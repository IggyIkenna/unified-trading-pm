#!/usr/bin/env bash
# Epic: resource_watchdog_host_guardian_2026_08_05
# Lifecycle: permanent
# Delete-when: NA
# resource-watchdog.sh — cross-process resource guardian for the planning VM.
#
# Monitors CPU, RAM, and swap for every process in the orchestrator cgroup and kills
# non-allowlisted processes that exceed per-resource thresholds. Two pressure levels
# gated on cgroup memory: normal (10 GB per-process RSS limit) and high (4 GB).
#
# After killing, writes a marker file and POSTs to the orchestrator's internal API
# so the agent that spawned the process knows NOT to re-spawn it — offload to a spot VM.
#
# Config: env vars (set by systemd unit or config.yaml). See config.yaml for docs.
#   RW_POLL_INTERVAL_SEC        default 10
#   RW_CGROUP_MEMORY_MAX        default read from /sys/fs/cgroup (fallback 57982058496 = 54G)
#   RW_PRESSURE_HIGH_PCT        default 80
#   RW_RSS_LIMIT_NORMAL_GB      default 10
#   RW_RSS_LIMIT_HIGH_GB        default 4
#   RW_CPU_MAX_PCT              default 95   (% of one core)
#   RW_CPU_WINDOW_MIN           default 10
#   RW_SWAP_LIMIT_GB            default 4
#   RW_MIN_PROCESS_AGE_SEC      default 30
#   RW_MAX_KILLS_PER_MIN        default 1
#   RW_ORCHESTRATOR_URL         default http://localhost:8765
#   RW_MARKER_DIR               default /dev/shm/resource-watchdog/kills
#   RW_LOG_FILE                 default /var/log/resource-watchdog.log
#   RW_DRY_RUN                  default false
#   RW_ALLOWLIST                default "orchestrator uvicorn resource-watchdog pytest prek ruff basedpyright mypy npm vitest tsc"
#
# Usage:
#   ./resource-watchdog.sh [--dry-run] [--interval N] [--status]

set -euo pipefail

# ── Config (env vars with defaults) ───────────────────────────────────────────
POLL_INTERVAL="${RW_POLL_INTERVAL_SEC:-10}"

# Cgroup memory max: try to read from the live cgroup, fall back to 54 GB
CGROUP_MEMORY_PATH="${RW_CGROUP_MEMORY_PATH:-/sys/fs/cgroup/system.slice/orchestrator.service/memory.current}"
CGROUP_MAX_PATH="${RW_CGROUP_MAX_PATH:-/sys/fs/cgroup/system.slice/orchestrator.service/memory.max}"
if [[ -f "$CGROUP_MAX_PATH" ]] && [[ "$(cat "$CGROUP_MAX_PATH" 2>/dev/null)" != "max" ]]; then
    CGROUP_MEMORY_MAX="$(cat "$CGROUP_MAX_PATH")"
else
    CGROUP_MEMORY_MAX="${RW_CGROUP_MEMORY_MAX:-57982058496}"  # 54 GB
fi

PRESSURE_HIGH_PCT="${RW_PRESSURE_HIGH_PCT:-80}"
RSS_LIMIT_NORMAL_KB=$(( ${RW_RSS_LIMIT_NORMAL_GB:-10} * 1024 * 1024 ))
RSS_LIMIT_HIGH_KB=$(( ${RW_RSS_LIMIT_HIGH_GB:-4} * 1024 * 1024 ))
CPU_MAX_PCT="${RW_CPU_MAX_PCT:-95}"
CPU_WINDOW_MIN="${RW_CPU_WINDOW_MIN:-10}"
SWAP_LIMIT_KB=$(( ${RW_SWAP_LIMIT_GB:-4} * 1024 * 1024 ))
MIN_AGE_SEC="${RW_MIN_PROCESS_AGE_SEC:-30}"
MAX_KILLS_PER_MIN="${RW_MAX_KILLS_PER_MIN:-1}"
ORCHESTRATOR_URL="${RW_ORCHESTRATOR_URL:-http://localhost:8765}"
DEPLOYMENT_API_URL="${RW_DEPLOYMENT_API_URL:-}"
# deployment-api X-API-Key for the kill-event POST. Same GSM secret
# `deployment-api-api-key` deployment-api validates against. Resolved in this
# order: RW_DEPLOYMENT_API_KEY env (systemd override) → GSM `deployment-api-api-key`
# (runtime fetch — the orchestrator VM's SA holds secretmanager.secretAccessor,
# so no secret is ever written to the repo/service file). Empty → omit the
# header (deployment-api's own "omit if empty" convention), so the watchdog
# keeps working during rollout.
DEPLOYMENT_API_KEY="${RW_DEPLOYMENT_API_KEY:-}"
if [[ -z "${DEPLOYMENT_API_KEY:-}" && -n "${DEPLOYMENT_API_URL:-}" ]]; then
  DEPLOYMENT_API_KEY="$(
    timeout 10 gcloud secrets versions access latest --secret=deployment-api-api-key \
      --project=central-element-323112 2>/dev/null | tr -d '\n'
  )"
  if [[ -z "${DEPLOYMENT_API_KEY:-}" ]]; then
    echo "[resource-watchdog] WARN deployment-api key unset — kill-event POST will omit X-API-Key (auth will fail after enforcement flip)" >&2
  fi
fi
VM_NAME="${RW_VM_NAME:-$(hostname 2>/dev/null || echo 'planning-vm')}"
MARKER_DIR="${RW_MARKER_DIR:-/dev/shm/resource-watchdog/kills}"
LOG_FILE="${RW_LOG_FILE:-/var/log/resource-watchdog.log}"
DRY_RUN="${RW_DRY_RUN:-false}"
ALLOWLIST="${RW_ALLOWLIST:-orchestrator uvicorn resource-watchdog pytest prek ruff basedpyright mypy npm vitest tsc}"

# State for CPU tracking across polls
declare -A CPU_PREV_UTIME CPU_PREV_STIME CPU_PREV_TIMESTAMP CPU_OVER_THRESHOLD_SINCE

# Rate-limit state
LAST_KILL_TIMESTAMP=0

# ── Logging ───────────────────────────────────────────────────────────────────
_rw_log() {
    local level="$1" msg="$2"
    local ts; ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u)"
    printf '[%s] [%s] %s\n' "$ts" "$level" "$msg" | tee -a "$LOG_FILE" >&2
}

_rw_log_info()  { _rw_log "INFO"  "$1"; }
_rw_log_warn()  { _rw_log "WARN"  "$1"; }
_rw_log_error() { _rw_log "ERROR" "$1"; }

# ── /proc helpers ─────────────────────────────────────────────────────────────

_rw_cgroup_memory_current() {
    cat "$CGROUP_MEMORY_PATH" 2>/dev/null || echo 0
}

_rw_pressure_level() {
    local current; current="$(_rw_cgroup_memory_current)"
    local threshold=$(( CGROUP_MEMORY_MAX * PRESSURE_HIGH_PCT / 100 ))
    if (( current >= threshold )); then echo "high"; else echo "normal"; fi
}

_rw_rss_limit_kb() {
    local level; level="$(_rw_pressure_level)"
    if [[ "$level" == "high" ]]; then echo "$RSS_LIMIT_HIGH_KB"; else echo "$RSS_LIMIT_NORMAL_KB"; fi
}

# Get all PIDs in the orchestrator cgroup (recursive)
_rw_cgroup_pids() {
    local cgroup_procs="${RW_CGROUP_PROCS_PATH:-/sys/fs/cgroup/system.slice/orchestrator.service/cgroup.procs}"
    cat "$cgroup_procs" 2>/dev/null || true
}

_rw_process_exists() {
    local pid="$1"
    [[ -d "/proc/$pid" ]]
}

_rw_process_rss_kb() {
    local pid="$1"
    awk '/^VmRSS:/{print $2; exit}' "/proc/$pid/status" 2>/dev/null || echo 0
}

_rw_process_swap_kb() {
    local pid="$1"
    awk '/^VmSwap:/{print $2; exit}' "/proc/$pid/status" 2>/dev/null || echo 0
}

_rw_process_age_sec() {
    local pid="$1"
    local now boot_sec start_ticks hz uptime_sec
    now="$(awk '{print $1}' /proc/uptime 2>/dev/null | cut -d. -f1)" || return 0
    start_ticks="$(awk '{print $22}' "/proc/$pid/stat" 2>/dev/null)" || return 0
    hz="$(getconf CLK_TCK 2>/dev/null || echo 100)"
    uptime_sec=$(( start_ticks / hz ))
    echo $(( now - uptime_sec ))
}

_rw_process_command() {
    local pid="$1"
    local cmd; cmd="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
    [[ -n "${cmd// }" ]] && echo "$cmd" || cat "/proc/$pid/comm" 2>/dev/null || echo "unknown"
}

_rw_process_cpu_pct() {
    # Returns CPU% of ONE core (utime+stime delta / wall delta * 100).
    # Values >100 mean the process is multi-threaded and using multiple cores.
    local pid="$1"
    local now; now="$(date +%s 2>/dev/null || echo 0)"
    local utime stime
    read -r utime stime < <(awk '{print $14, $15}' "/proc/$pid/stat" 2>/dev/null || echo "0 0")
    local prev_utime="${CPU_PREV_UTIME[$pid]:-0}"
    local prev_stime="${CPU_PREV_STIME[$pid]:-0}"
    local prev_ts="${CPU_PREV_TIMESTAMP[$pid]:-0}"

    CPU_PREV_UTIME[$pid]="$utime"
    CPU_PREV_STIME[$pid]="$stime"
    CPU_PREV_TIMESTAMP[$pid]="$now"

    local delta_ticks=$(( utime + stime - prev_utime - prev_stime ))
    local delta_sec=$(( now - prev_ts ))
    if (( delta_sec <= 0 || delta_ticks < 0 )); then echo 0; return 0; fi

    local hz; hz="$(getconf CLK_TCK 2>/dev/null || echo 100)"
    # CPU% of one core = (ticks/hz) / wall_sec * 100
    awk -v ticks="$delta_ticks" -v hz="$hz" -v sec="$delta_sec" \
        'BEGIN { printf "%.0f", (ticks / hz) / sec * 100 }'
}

_rw_process_is_allowlisted() {
    local pid="$1"
    local cmd; cmd="$(_rw_process_command "$pid")"
    local pattern
    for pattern in $ALLOWLIST; do
        if [[ "$cmd" == *"$pattern"* ]]; then
            return 0
        fi
    done
    return 1
}

# ── Slot detection ────────────────────────────────────────────────────────────

_rw_detect_slot() {
    # Walk /proc/[pid]/cwd up the parent chain looking for .tabs/N/
    local pid="$1"
    local current="$pid"
    local max_depth=10 depth=0 cwd

    while (( depth < max_depth )); do
        cwd="$(readlink "/proc/$current/cwd" 2>/dev/null || true)"
        if [[ "$cwd" =~ \.tabs/([0-9]+) ]]; then
            echo "${BASH_REMATCH[1]}"
            return 0
        fi
        # Walk up to parent
        current="$(awk '/^PPid:/{print $2; exit}' "/proc/$current/status" 2>/dev/null || echo 0)"
        if (( current <= 1 )); then break; fi
        depth=$(( depth + 1 ))
    done

    # Fallback: try the PID's own cwd even if not .tabs (might be a child that chdir'd)
    cwd="$(readlink "/proc/$pid/cwd" 2>/dev/null || true)"
    if [[ "$cwd" =~ \.tabs/([0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
        return 0
    fi

    echo "unknown"
    return 1
}

# ── Kill + notification ───────────────────────────────────────────────────────

_rw_write_marker() {
    local pid="$1" slot="$2" reason="$3" rss_kb="$4" limit_kb="$5" cmd="$6"
    mkdir -p "$MARKER_DIR" 2>/dev/null || return 1
    local marker="${MARKER_DIR}/${pid}.json"
    local rss_mb=$(( rss_kb / 1024 ))
    local limit_mb=$(( limit_kb / 1024 ))
    local pressure; pressure="$(_rw_pressure_level)"
    cat > "$marker" <<EOF
{
  "pid": ${pid},
  "slot_id": "${slot}",
  "command": "$(echo "$cmd" | sed 's/"/\\"/g')",
  "rss_mb": ${rss_mb},
  "limit_mb": ${limit_mb},
  "pressure_level": "${pressure}",
  "reason": "${reason}",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u)",
  "killed_by": "resource-watchdog",
  "message": "Process killed by resource watchdog. Do not re-spawn on planning VM. Offload this workload to a spot VM."
}
EOF
    _rw_log_info "marker written: $marker (pid=$pid slot=$slot reason=$reason rss_mb=$rss_mb limit_mb=$limit_mb)"
}

_rw_notify_orchestrator() {
    local pid="$1" slot="$2" reason="$3" rss_kb="$4" limit_kb="$5" cmd="$6"
    local rss_mb=$(( rss_kb / 1024 ))
    local limit_mb=$(( limit_kb / 1024 ))
    local pressure; pressure="$(_rw_pressure_level)"

    local payload; payload="$(cat <<EOF
{
  "pid": ${pid},
  "slot_id": "${slot}",
  "command": "$(echo "$cmd" | sed 's/"/\\"/g')",
  "rss_mb": ${rss_mb},
  "limit_mb": ${limit_mb},
  "pressure_level": "${pressure}",
  "reason": "${reason}",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u)"
}
EOF
)"
    # Fire-and-forget — don't block the watchdog loop on API calls
    curl -s -X POST "${ORCHESTRATOR_URL}/api/resource-watchdog/kill" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        --connect-timeout 3 --max-time 5 \
        >/dev/null 2>&1 || _rw_log_warn "orchestrator API unreachable for kill notification (pid=$pid slot=$slot)"
    _rw_log_info "orchestrator notified: pid=$pid slot=$slot reason=$reason"
}

_rw_notify_deployment_api() {
    local pid="$1" slot="$2" reason="$3" rss_kb="$4" limit_kb="$5" cmd="$6" killed="$7"

    # Skip silently if no deployment-api URL is configured (opt-in).
    if [[ -z "${DEPLOYMENT_API_URL:-}" ]]; then
        return 0
    fi

    local rss_mb=$(( rss_kb / 1024 ))
    local limit_mb=$(( limit_kb / 1024 ))
    local pressure; pressure="$(_rw_pressure_level)"

    local payload; payload="$(cat <<EOF
{
  "vm_name": "${VM_NAME}",
  "pid": ${pid},
  "slot_id": "${slot}",
  "command": "$(echo "$cmd" | sed 's/"/\\"/g')",
  "rss_mb": ${rss_mb},
  "limit_mb": ${limit_mb},
  "pressure_level": "${pressure}",
  "reason": "${reason}",
  "killed": ${killed}
}
EOF
)"
    # Fire-and-forget — don't block the watchdog loop on API calls
    local -a curl_args=( -s -X POST "${DEPLOYMENT_API_URL}/api/fleet/watchdog/kill-events" )
    curl_args+=( -H "Content-Type: application/json" )
    if [[ -n "${DEPLOYMENT_API_KEY:-}" ]]; then
        curl_args+=( -H "X-API-Key: ${DEPLOYMENT_API_KEY}" )
    fi
    curl_args+=( -d "$payload" --connect-timeout 3 --max-time 5 )
    curl "${curl_args[@]}" >/dev/null 2>&1 || _rw_log_warn "deployment-api unreachable for kill notification (pid=$pid slot=$slot)"
    _rw_log_info "deployment-api notified: pid=$pid slot=$slot reason=$reason killed=${killed}"
}

_rw_snapshot_process() {
    local pid="$1" reason="$2"
    local snap_dir; snap_dir="$(dirname "$LOG_FILE")/snapshots"
    mkdir -p "$snap_dir" 2>/dev/null || return 0
    local snap="${snap_dir}/kill_${pid}_$(date -u +"%Y%m%dT%H%M%SZ" 2>/dev/null || date +%s).txt"
    {
        echo "=== Kill snapshot: pid=$pid reason=$reason ==="
        echo "Timestamp: $(date -u -Iseconds 2>/dev/null || date)"
        echo
        echo "=== /proc/$pid/status ==="
        cat "/proc/$pid/status" 2>/dev/null || echo "(unavailable)"
        echo
        echo "=== /proc/$pid/cmdline ==="
        _rw_process_command "$pid"
        echo
        echo "=== Process tree (pstree -p $pid) ==="
        pstree -p "$pid" 2>/dev/null || ps --ppid "$pid" -o pid,comm 2>/dev/null || echo "(unavailable)"
        echo
        echo "=== Cgroup memory stat ==="
        cat /sys/fs/cgroup/system.slice/orchestrator.service/memory.stat 2>/dev/null | head -10 || echo "(unavailable)"
        echo
        echo "=== /proc/$pid/smaps (head 200 lines) ==="
        head -200 "/proc/$pid/smaps" 2>/dev/null || echo "(unavailable)"
    } > "$snap" 2>/dev/null
    _rw_log_info "snapshot saved: $snap"
}

_rw_kill_process() {
    local pid="$1"
    # SIGTERM first — gives the process a chance to clean up
    kill -TERM "$pid" 2>/dev/null || return 1
    local waited=0
    while (( waited < 5 )); do
        if ! _rw_process_exists "$pid"; then
            _rw_log_info "pid=$pid exited cleanly after SIGTERM (${waited}s)"
            return 0
        fi
        sleep 1
        waited=$(( waited + 1 ))
    done
    # Escalate to SIGKILL
    kill -9 "$pid" 2>/dev/null || true
    local sigkill_waited=0
    while (( sigkill_waited < 5 )); do
        if ! _rw_process_exists "$pid"; then
            _rw_log_info "pid=$pid killed (SIGKILL effective after ${sigkill_waited}s)"
            return 0
        fi
        sleep 1
        sigkill_waited=$(( sigkill_waited + 1 ))
    done
    if _rw_process_exists "$pid"; then
        _rw_log_error "FAILED to kill pid=$pid — process still alive after SIGKILL+${sigkill_waited}s (may be in D-state / uninterruptible sleep)"
        return 1
    fi
    return 0
}

_rw_rate_limit_check() {
    local now; now="$(date +%s)"
    local elapsed=$(( now - LAST_KILL_TIMESTAMP ))
    if (( elapsed < 60 / MAX_KILLS_PER_MIN )); then
        return 1  # rate-limited
    fi
    return 0
}

_rw_rate_limit_record() {
    LAST_KILL_TIMESTAMP="$(date +%s)"
}

# ── Main enforcement logic ────────────────────────────────────────────────────

_rw_enforce_process() {
    local pid="$1"
    local rss_kb swap_kb cpu_pct age cmd

    # Quick pre-checks
    rss_kb="$(_rw_process_rss_kb "$pid")"
    age="$(_rw_process_age_sec "$pid")"

    # Skip young processes (startup spikes)
    if (( age < MIN_AGE_SEC )); then
        return 0
    fi

    # Skip allowlisted processes
    if _rw_process_is_allowlisted "$pid"; then
        return 0
    fi

    cmd="$(_rw_process_command "$pid")"
    swap_kb="$(_rw_process_swap_kb "$pid")"
    cpu_pct="$(_rw_process_cpu_pct "$pid")"

    local limit_kb reason
    reason=""

    # Check RSS
    limit_kb="$(_rw_rss_limit_kb)"
    if (( rss_kb > limit_kb )); then
        reason="rss:${rss_kb}kB > ${limit_kb}kB"
    fi

    # Check swap
    if [[ -z "$reason" ]] && (( swap_kb > SWAP_LIMIT_KB )); then
        reason="swap:${swap_kb}kB > ${SWAP_LIMIT_KB}kB"
        limit_kb="$SWAP_LIMIT_KB"
    fi

    # Check sustained CPU
    if [[ -z "$reason" ]] && (( cpu_pct > CPU_MAX_PCT )); then
        local since="${CPU_OVER_THRESHOLD_SINCE[$pid]:-0}"
        local now; now="$(date +%s)"
        if (( since == 0 )); then
            CPU_OVER_THRESHOLD_SINCE[$pid]="$now"
        elif (( now - since >= CPU_WINDOW_MIN * 60 )); then
            reason="cpu:${cpu_pct}% > ${CPU_MAX_PCT}% for ${CPU_WINDOW_MIN}+ min"
            limit_kb=0  # not RSS-based
        fi
    else
        # Reset CPU tracking if below threshold
        CPU_OVER_THRESHOLD_SINCE[$pid]=0
    fi

    # No violation — process is fine
    if [[ -z "$reason" ]]; then
        return 0
    fi

    # ── Violation: kill the process ──
    local slot; slot="$(_rw_detect_slot "$pid")"
    local rss_mb=$(( rss_kb / 1024 ))
    local limit_mb=$(( limit_kb / 1024 ))

    _rw_log_warn "VIOLATION: pid=$pid slot=$slot cmd='$cmd' $reason"

    # Rate-limit
    if ! _rw_rate_limit_check; then
        _rw_log_warn "rate-limited: skipping kill for pid=$pid (last kill < $(( 60 / MAX_KILLS_PER_MIN ))s ago)"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        _rw_log_info "DRY-RUN: would kill pid=$pid slot=$slot ($reason)"
        _rw_rate_limit_record
        # Notify deployment-api even in dry-run mode so the integration is testable
        # without an actual kill (killed=false).
        _rw_notify_deployment_api "$pid" "$slot" "$reason" "$rss_kb" "${limit_kb:-0}" "$cmd" "false"
        return 0
    fi

    # Pre-kill: snapshot + marker
    _rw_snapshot_process "$pid" "$reason"
    _rw_write_marker "$pid" "$slot" "$reason" "$rss_kb" "${limit_kb:-0}" "$cmd"

    # Kill
    if _rw_kill_process "$pid"; then
        _RW_KILL_COUNT=$(( ${_RW_KILL_COUNT:-0} + 1 ))
        _rw_rate_limit_record
        # Notify orchestrator (fire-and-forget)
        _rw_notify_orchestrator "$pid" "$slot" "$reason" "$rss_kb" "${limit_kb:-0}" "$cmd"
        # Notify deployment-api (fire-and-forget — additive, dual-write)
        _rw_notify_deployment_api "$pid" "$slot" "$reason" "$rss_kb" "${limit_kb:-0}" "$cmd" "true"
        _rw_log_info "KILL #${_RW_KILL_COUNT}: pid=$pid slot=$slot ($reason)"
    fi

    # Clean up CPU tracking for dead process
    unset "CPU_PREV_UTIME[$pid]" 2>/dev/null || true
    unset "CPU_PREV_STIME[$pid]" 2>/dev/null || true
    unset "CPU_PREV_TIMESTAMP[$pid]" 2>/dev/null || true
    unset "CPU_OVER_THRESHOLD_SINCE[$pid]" 2>/dev/null || true
}

# ── Status / introspection ────────────────────────────────────────────────────

_rw_status_json_path() {
    echo "${RW_STATUS_FILE:-/dev/shm/resource-watchdog/status.json}"
}

_rw_probe_qg_governor() {
    # Probe the QG host governor's token-concurrency state so the AO UI can show
    # "2/4 tokens held" at a glance. Best-effort: -1 means "governor unreachable."
    # Try the configured path, then the standard VM workspace path.
    local gov_script=""
    if [[ -n "${RW_QG_GOVERNOR_SCRIPT:-}" ]] && [[ -x "$RW_QG_GOVERNOR_SCRIPT" ]]; then
        gov_script="$RW_QG_GOVERNOR_SCRIPT"
    elif [[ -x "/home/ubuntu/unified-trading-system-repos/unified-trading-pm/scripts/quality-gates-base/qg-host-governor.sh" ]]; then
        gov_script="/home/ubuntu/unified-trading-system-repos/unified-trading-pm/scripts/quality-gates-base/qg-host-governor.sh"
    elif [[ -x "/active/unified-trading-system-repos/unified-trading-pm/scripts/quality-gates-base/qg-host-governor.sh" ]]; then
        gov_script="/active/unified-trading-system-repos/unified-trading-pm/scripts/quality-gates-base/qg-host-governor.sh"
    fi
    _RW_QG_TOKENS_HELD=-1
    _RW_QG_TOKENS_MAX=-1
    if [[ -z "$gov_script" ]]; then return 0; fi
    local status_output; status_output="$("$gov_script" --status 2>/dev/null || true)"
    # Parse "tokens held now: X/Y" when there ARE active reservations
    if [[ "$status_output" =~ tokens\ held\ now:\ ([0-9]+)/([0-9]+) ]]; then
        _RW_QG_TOKENS_HELD="${BASH_REMATCH[1]}"
        _RW_QG_TOKENS_MAX="${BASH_REMATCH[2]}"
    elif [[ "$status_output" =~ K=([0-9]+) ]]; then
        # Governor running but no tokens held (dir empty/absent) → 0/K
        _RW_QG_TOKENS_HELD=0
        _RW_QG_TOKENS_MAX="${BASH_REMATCH[1]}"
    fi
}

_rw_write_status_file() {
    # Write a lightweight status JSON snapshot for the orchestrator to read.
    # Called once per poll tick so the AO UI always has fresh data.
    local status_file; status_file="$(_rw_status_json_path)"
    local status_dir; status_dir="$(dirname "$status_file")"
    mkdir -p "$status_dir" 2>/dev/null || return 0

    local pressure cgroup_mem rss_limit_kb rss_limit_gb cgroup_max_gb cgroup_mem_gb
    pressure="$(_rw_pressure_level)"
    cgroup_mem="$(_rw_cgroup_memory_current)"
    rss_limit_kb="$(_rw_rss_limit_kb)"
    rss_limit_gb=$(( rss_limit_kb / 1024 / 1024 ))
    cgroup_max_gb=$(( CGROUP_MEMORY_MAX / 1024 / 1024 / 1024 ))
    cgroup_mem_gb=$(( cgroup_mem / 1024 / 1024 / 1024 ))

    local last_kill_iso="null"
    if (( LAST_KILL_TIMESTAMP > 0 )); then
        last_kill_iso="\"$(date -d "@$LAST_KILL_TIMESTAMP" -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "unknown")\""
    fi

    local uptime_sec; uptime_sec="$(awk '{print int($1)}' /proc/uptime 2>/dev/null || echo 0)"

    cat > "$status_file" <<STATUS_EOF
{
  "pressure_level": "${pressure}",
  "cgroup_mem_gb": ${cgroup_mem_gb},
  "cgroup_max_gb": ${cgroup_max_gb},
  "rss_limit_gb": ${rss_limit_gb},
  "dry_run": ${DRY_RUN},
  "poll_interval_sec": ${POLL_INTERVAL},
  "allowlist": "$(echo "$ALLOWLIST" | sed 's/"/\\"/g')",
  "kill_count": ${_RW_KILL_COUNT:-0},
  "last_kill_iso": ${last_kill_iso},
  "uptime_seconds": ${uptime_sec},
  "orchestrator_url": "${ORCHESTRATOR_URL}",
  "marker_dir": "${MARKER_DIR}",
  "qg_tokens_held": ${_RW_QG_TOKENS_HELD:--1},
  "qg_tokens_max": ${_RW_QG_TOKENS_MAX:--1}
}
STATUS_EOF
}

_rw_status() {
    local pressure cgroup_mem rss_limit
    pressure="$(_rw_pressure_level)"
    cgroup_mem="$(_rw_cgroup_memory_current)"
    rss_limit="$(_rw_rss_limit_kb)"
    printf 'resource-watchdog status:\n'
    printf '  pressure_level:    %s\n' "$pressure"
    printf '  cgroup_memory:     %d GB\n' "$(( cgroup_mem / 1024 / 1024 / 1024 ))"
    printf '  cgroup_max:        %d GB\n' "$(( CGROUP_MEMORY_MAX / 1024 / 1024 / 1024 ))"
    printf '  rss_limit:         %d GB\n' "$(( rss_limit / 1024 / 1024 ))"
    printf '  dry_run:           %s\n' "$DRY_RUN"
    printf '  poll_interval:     %ds\n' "$POLL_INTERVAL"
    printf '  allowlist:         %s\n' "$ALLOWLIST"
    printf '  orchestrator_url:  %s\n' "$ORCHESTRATOR_URL"
    printf '  marker_dir:        %s\n' "$MARKER_DIR"
    printf '  log_file:          %s\n' "$LOG_FILE"
    printf '  kill_count:        %d (since start)\n' "${_RW_KILL_COUNT:-0}"
    printf '  last_kill:         %s\n' "$( (( LAST_KILL_TIMESTAMP > 0 )) && date -d "@$LAST_KILL_TIMESTAMP" -Iseconds 2>/dev/null || echo "never")"
}

# ── Main loop ─────────────────────────────────────────────────────────────────

_rw_main_loop() {
    _rw_log_info "resource-watchdog starting (dry_run=$DRY_RUN interval=${POLL_INTERVAL}s pressure_high_pct=${PRESSURE_HIGH_PCT}%)"
    _rw_log_info "limits: rss_normal=${RSS_LIMIT_NORMAL_KB}KB rss_high=${RSS_LIMIT_HIGH_KB}KB cpu=${CPU_MAX_PCT}%/${CPU_WINDOW_MIN}min swap=${SWAP_LIMIT_KB}KB"
    _rw_log_info "cgroup: max=${CGROUP_MEMORY_MAX} path=${CGROUP_MEMORY_PATH}"

    local tick=0
    while true; do
        tick=$(( tick + 1 ))
        local level; level="$(_rw_pressure_level)"
        local cgroup_mem; cgroup_mem="$(_rw_cgroup_memory_current)"
        local cgroup_gb=$(( cgroup_mem / 1024 / 1024 / 1024 ))

        if (( tick % 6 == 1 )); then  # Log pressure ~once per minute
            _rw_log_info "tick=$tick pressure=$level cgroup_mem=${cgroup_gb}GB"
        fi

        local pids; pids="$(_rw_cgroup_pids)"
        local checked=0 violations=0

        for pid in $pids; do
            # Skip self
            [[ "$pid" == "$$" ]] && continue
            checked=$(( checked + 1 ))
            _rw_enforce_process "$pid" || true
        done

        # Clean up stale CPU tracking entries for dead processes
        local stale=()
        for tracked_pid in "${!CPU_PREV_UTIME[@]}"; do
            if ! _rw_process_exists "$tracked_pid"; then
                stale+=("$tracked_pid")
            fi
        done
        for spid in "${stale[@]}"; do
            unset "CPU_PREV_UTIME[$spid]" "CPU_PREV_STIME[$spid]" "CPU_PREV_TIMESTAMP[$spid]" "CPU_OVER_THRESHOLD_SINCE[$spid]" 2>/dev/null || true
        done

        # Probe QG governor token state + write status snapshot for AO UI
        _rw_probe_qg_governor
        _rw_write_status_file

        sleep "$POLL_INTERVAL"
    done
}

_rw_run_one_cycle() {
    # Run one full enforcement check across all cgroup processes.
    local pids; pids="$(_rw_cgroup_pids)"
    local checked=0
    for pid in $pids; do
        [[ "$pid" == "$$" ]] && continue
        checked=$(( checked + 1 ))
        _rw_enforce_process "$pid" || true
    done
    _rw_log_info "oneshot cycle complete: checked=${checked} processes"
}

# ── Signal handler ────────────────────────────────────────────────────────────

_rw_cleanup() {
    _rw_log_info "resource-watchdog shutting down"
    exit 0
}
trap _rw_cleanup SIGTERM SIGINT

# ── CLI entrypoint ────────────────────────────────────────────────────────────

_usage() {
    cat >&2 <<'EOF'
Usage: resource-watchdog.sh [--dry-run] [--interval N] [--status] [--oneshot]

  --dry-run      Log violations but don't kill anything.
  --interval N   Poll interval in seconds (default 10).
  --status       Print status and exit (does not start daemon).
  --oneshot      Run one check cycle and exit (for cron / testing).
  --help         This message.

Config is via env vars; see config.yaml for full documentation.
EOF
    exit 2
}

_main() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)   DRY_RUN="true"; shift ;;
            --interval)  POLL_INTERVAL="$2"; shift 2 ;;
            --status)    _rw_status; exit 0 ;;
            --oneshot)   _rw_run_one_cycle; _rw_status; exit 0 ;;
            --help)      _usage ;;
            *)           echo "Unknown flag: $1" >&2; _usage ;;
        esac
    done

    # Ensure log file is writable
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    mkdir -p "$MARKER_DIR" 2>/dev/null || true

    _rw_main_loop
}

_main "$@"
