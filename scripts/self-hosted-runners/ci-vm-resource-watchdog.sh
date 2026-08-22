#!/usr/bin/env bash
# ci-vm-resource-watchdog.sh
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
#
# Standing 60-min resource-strain check for the dedicated CI/self-hosted-runner VM
# (ci-escalation-runner-vm-1). Reads the box's OWN resource-history-sampler JSONL log
# (already installed + running, ci_vm_exposure_remediation_2026_08_06.md todo 2 --
# this script adds no new instrumentation) for the last hour and pages #ci-failures
# ONLY on a genuine box-down risk signal.
#
# EXPLICIT DESIGN GOAL (operator directive, 2026-08-08): a temporary burst -- CPU/load/iowait
# pegged for a few minutes during a fleet-wide CI wave -- is EFFICIENT use of the box's
# capacity, not a problem, and must NOT page. Only escalate when something would risk
# genuinely bringing the box down: a real kernel OOM-kill, or SUSTAINED near-saturation
# (not a spike) that historically preceded one (this VM has 6 documented OOM kills on
# record -- Part 5 of ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md).
#
# Same dedup/recovery-bookend/dispatch_alert pattern as
# glue-runner-crash-loop-watchdog.sh (state-transition alerting, not "page every tick") --
# see that script's own comments for the rationale; not re-derived here.
set -euo pipefail

# ── Tunables (env-overridable, same convention as the crash-loop watchdog) ──────────────
WINDOW_SECONDS="${CI_VM_WATCHDOG_WINDOW_SECONDS:-3600}"          # look-back window (1h, matches the 60-min tick)
SWAP_CRITICAL_PCT="${CI_VM_WATCHDOG_SWAP_CRITICAL_PCT:-90}"      # swap_percent above this = no memory headroom left
LOAD_MULTIPLIER="${CI_VM_WATCHDOG_LOAD_MULTIPLIER:-4}"           # load_avg_1m above cpu_count * this = real oversubscription
IOWAIT_CRITICAL_PCT="${CI_VM_WATCHDOG_IOWAIT_CRITICAL_PCT:-50}"  # iowait_percent above this = genuinely disk-bound, not just busy
SUSTAINED_FRACTION="${CI_VM_WATCHDOG_SUSTAINED_FRACTION:-0.5}"   # fraction of the window that must be over threshold -- a brief spike is NOT sustained
RESOURCE_HISTORY_DIR="${CI_VM_WATCHDOG_RESOURCE_HISTORY_DIR:-/opt/glue-deploy/agent-orchestrator/data/state/resource_history}"
STATE_DIR="${CI_VM_WATCHDOG_STATE_DIR:-/home/ubuntu/.local/state/ci-vm-resource-watchdog}"
STATE_FILE="${STATE_DIR}/alerted-conditions"
GH_REPO="IggyIkenna/unified-trading-pm"
PM_ENV_FILE="/etc/github-glue-runner.env"

mkdir -p "$STATE_DIR"
touch "$STATE_FILE"

log() { echo "[ci-vm-resource-watchdog] $*"; }

THIS_INSTANCE_ID="$(curl -sf -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null \
  | xargs -I{} curl -sf -H "X-aws-ec2-metadata-token: {}" \
    "http://169.254.169.254/latest/meta-data/instance-id" 2>/dev/null || echo "unknown-host")"

# Same token-resolution path as glue-runner-crash-loop-watchdog.sh (this VM's own glue-runner
# alert-dispatch identity, already reused fleet-wide -- see that script's own comment for why
# no new credential is needed).
resolve_gh_token() {
  local secret="${GH_TOKEN_SECRET:-}" project="${GCP_PROJECT:-}" gcloud_cfg="${GLUE_GCLOUD_CONFIG:-}"
  if [ -z "$secret" ] && [ -r "$PM_ENV_FILE" ]; then
    secret="$(sed -n 's/^GH_TOKEN_SECRET=//p' "$PM_ENV_FILE" | head -1)"
    project="${project:-$(sed -n 's/^GCP_PROJECT=//p' "$PM_ENV_FILE" | head -1)}"
    gcloud_cfg="${gcloud_cfg:-$(sed -n 's/^GLUE_GCLOUD_CONFIG=//p' "$PM_ENV_FILE" | head -1)}"
  fi
  gcloud_cfg="${gcloud_cfg:-/opt/github-glue-runners/.gcloud}"
  CLOUDSDK_CONFIG="$gcloud_cfg" gcloud secrets versions access latest \
    --secret="$secret" --project="$project"
}

was_alerted()  { grep -qxF "$1" "$STATE_FILE" 2>/dev/null; }
mark_alerted() { echo "$1" >> "$STATE_FILE"; }
clear_alerted() {
  grep -vxF "$1" "$STATE_FILE" > "${STATE_FILE}.tmp" 2>/dev/null || true
  mv "${STATE_FILE}.tmp" "$STATE_FILE"
}

# Same contract as glue-runner-crash-loop-watchdog.sh's dispatch_alert(): returns 0 ONLY on a
# confirmed-sent dispatch; callers gate mark_alerted/clear_alerted on this.
dispatch_alert() {
  local message="$1" severity="$2" dedup_key="$3" recovery="$4" token
  token="$(resolve_gh_token)" || { log "FATAL: could not resolve GH token, skipping dispatch for ${dedup_key} -- will retry next tick"; return 1; }
  jq -n \
    --arg message "$message" \
    --arg severity "$severity" \
    --arg dedup_key "$dedup_key" \
    --argjson recovery "$recovery" \
    '{event_type: "ci-vm-resource-alert", client_payload: {message: $message, severity: $severity, dedup_key: $dedup_key, cooldown_min: 30, recovery: $recovery}}' \
  | GH_TOKEN="$token" gh api "repos/${GH_REPO}/dispatches" --input - 2>&1 | sed 's/^/[ci-vm-resource-watchdog] /'
}

# ── Load the window's samples ────────────────────────────────────────────────────────────
# Reads today's file plus yesterday's (only its samples inside the window survive the
# epoch-cutoff filter below) so a tick shortly after midnight UTC still sees a full window
# instead of silently truncating at the day boundary.
now_epoch="$(date -u +%s)"
cutoff_epoch=$(( now_epoch - WINDOW_SECONDS ))
today_file="${RESOURCE_HISTORY_DIR}/$(date -u +%F).jsonl"
yesterday_file="${RESOURCE_HISTORY_DIR}/$(date -u -d '1 day ago' +%F 2>/dev/null || date -u -v-1d +%F).jsonl"

samples_json="$(
  { [ -f "$yesterday_file" ] && cat "$yesterday_file"; [ -f "$today_file" ] && cat "$today_file"; } 2>/dev/null \
    | python3 -c "
import sys, json
cutoff = ${cutoff_epoch}
rows = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        row = json.loads(line)
        ts = row.get('ts', '')
        # ts is ISO-8601 UTC (resource_history.py's own format); fromisoformat handles the
        # 'Z'-less offset-naive form this sampler writes.
        from datetime import datetime, timezone
        epoch = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp()
        if epoch >= cutoff:
            rows.append(row)
    except (json.JSONDecodeError, ValueError, KeyError):
        continue
print(json.dumps(rows))
"
)"

n_samples="$(echo "$samples_json" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")"

if [ "$n_samples" -eq 0 ]; then
  log "WARN -- 0 samples in the last ${WINDOW_SECONDS}s window (sampler down, or fresh boot) -- nothing to check this tick"
  exit 0
fi

# ── Compute the verdict in one python pass (max/p95 for the summary log, sustained-fraction
# checks for the actual escalation decision) ─────────────────────────────────────────────
verdict_json="$(echo "$samples_json" | python3 -c "
import sys, json

rows = json.load(sys.stdin)
n = len(rows)

def vals(key):
    return [r[key] for r in rows if r.get(key) is not None]

def stat(key):
    v = vals(key)
    if not v:
        return {'max': None, 'p95': None}
    v_sorted = sorted(v)
    p95_idx = min(len(v_sorted) - 1, int(len(v_sorted) * 0.95))
    return {'max': round(max(v), 1), 'p95': round(v_sorted[p95_idx], 1)}

def sustained_fraction_over(key, threshold):
    v = vals(key)
    if not v:
        return 0.0
    return sum(1 for x in v if x > threshold) / len(v)

cpu_count = next((r.get('cpu_count') for r in rows if r.get('cpu_count')), 1)
swap_frac = sustained_fraction_over('swap_percent', ${SWAP_CRITICAL_PCT})
load_threshold = cpu_count * ${LOAD_MULTIPLIER}
load_frac = sustained_fraction_over('load_avg_1m', load_threshold)
iowait_stat = stat('iowait_percent')
iowait_max = iowait_stat['max'] or 0

out = {
    'n_samples': n,
    'cpu_count': cpu_count,
    'cpu_percent': stat('cpu_percent'),
    'load_avg_1m': stat('load_avg_1m'),
    'ram_percent': stat('ram_percent'),
    'swap_percent': stat('swap_percent'),
    'disk_percent': stat('disk_percent'),
    'iowait_percent': iowait_stat,
    'swap_sustained_fraction': round(swap_frac, 2),
    'load_sustained_fraction': round(load_frac, 2),
    'sustained_swap_risk': swap_frac >= ${SUSTAINED_FRACTION},
    'sustained_load_iowait_risk': load_frac >= ${SUSTAINED_FRACTION} and iowait_max >= ${IOWAIT_CRITICAL_PCT},
}
print(json.dumps(out))
"
)"

log "window=${WINDOW_SECONDS}s samples=${n_samples} summary=${verdict_json}"

# Real kernel OOM-kill in the window -- the single most unambiguous "this nearly (or did)
# bring the box down" signal, independent of the sampler's own percentage-based heuristics.
oom_hits="$(journalctl -k --since "-${WINDOW_SECONDS} seconds" 2>/dev/null | grep -ic "out of memory\|invoked oom-killer" || true)"

sustained_swap_risk="$(echo "$verdict_json" | python3 -c "import sys,json; print('true' if json.load(sys.stdin)['sustained_swap_risk'] else 'false')")"
sustained_load_iowait_risk="$(echo "$verdict_json" | python3 -c "import sys,json; print('true' if json.load(sys.stdin)['sustained_load_iowait_risk'] else 'false')")"

risk=false
risk_reason=""
if [ "${oom_hits:-0}" -gt 0 ]; then
  risk=true
  risk_reason="a real kernel OOM-kill fired in the last ${WINDOW_SECONDS}s (${oom_hits} match(es) in dmesg/journalctl -k)"
elif [ "$sustained_swap_risk" = "true" ]; then
  risk=true
  risk_reason="swap_percent stayed above ${SWAP_CRITICAL_PCT}% for >= $(echo "$SUSTAINED_FRACTION * 100" | bc)% of the window -- sustained memory exhaustion, not a brief spike"
elif [ "$sustained_load_iowait_risk" = "true" ]; then
  risk=true
  risk_reason="load_avg_1m stayed above cpu_count*${LOAD_MULTIPLIER} AND iowait_percent peaked >= ${IOWAIT_CRITICAL_PCT}% for a sustained stretch -- genuine CPU+IO starvation, not a tolerated burst"
fi

if [ "$risk" = "true" ]; then
  key="ci-vm-resource-risk"
  if ! was_alerted "$key"; then
    log "NEW risk: ${risk_reason} -- paging"
    if dispatch_alert \
      "CI VM (\`${THIS_INSTANCE_ID}\`) resource strain looks like genuine box-down risk, not a tolerated burst: ${risk_reason}. Last-hour summary: ${verdict_json}" \
      "CRITICAL" \
      "$key" \
      "false"; then
      mark_alerted "$key"
    fi
  else
    log "ongoing risk (already alerted, suppressing repeat): ${risk_reason}"
  fi
else
  if was_alerted "ci-vm-resource-risk"; then
    log "RECOVERED -- posting bookend"
    if dispatch_alert \
      "CI VM (\`${THIS_INSTANCE_ID}\`) resource strain recovered -- back within the tolerated-burst envelope." \
      "INFO" \
      "ci-vm-resource-risk" \
      "true"; then
      clear_alerted "ci-vm-resource-risk"
    fi
  else
    log "OK -- no box-down risk signal this tick (bursts are expected and fine)"
  fi
fi
