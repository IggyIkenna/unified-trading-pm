#!/usr/bin/env bash
# glue-runner-crash-loop-watchdog.sh
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Periodically checks every github-glue-runner* systemd unit on THIS host for a crash-loop
# (SubState=auto-restart with a high NRestarts) and pages #ci-failures via a repository_dispatch
# to unified-trading-pm's ci-health.yml `glue-runner-alert` job -- the one alert path that stays
# reachable even when every self-hosted runner on this box is itself dead, because that job runs
# on ubuntu-latest (GitHub-hosted), not here.
#
# WHY THIS EXISTS: found 2026-07-28 -- every glue-runner pool crash-looped for ~3.5h
# (GCP_PROJECT missing from runtime env files, see
# plans/active/issues/glue_runner_gcp_project_missing_fleet_outage_2026_07_28.md) before a
# routine fleet CI sweep caught it by accident. No alerting existed for "the runner PROCESS
# itself is dead" -- only for CI job outcomes, which obviously never fire if the runner never
# came up to run anything in the first place.
#
# WEDGED-RUNNER DETECTION (2026-08-05, added alongside crash-loop): found live
# (market-tick-data-service, i-042a6332509482556) a `glue-*` unit that was neither crashing NOR
# progressing -- a single hung job (a deadlocked pytest run) kept its Runner.Worker alive for
# 21+ hours, holding ~5.6GB RSS. `Restart=always` never fired (the process never EXITED, it just
# hung), so the crash-loop check above is structurally blind to this failure mode. Worse,
# GitHub's own side had already stopped tracking the run (zero registered runners, job stuck
# `queued`) -- there was no live channel left for GitHub's own job-level `timeout-minutes` to
# reach, so nothing was ever going to kill it. Every subsequent commit for that repo queued
# forever with zero chance of pickup, silently, until this was caught by a live manual
# investigation. `is_wedged()` below catches this class going forward: a `@glue-N` instance
# (JIT-ephemeral, one job per process by design -- see github-glue-runner@.service's own
# comment) that has been `active` continuously for longer than any legitimate single job could
# take. Deliberately excludes `@writer-N` instances (long-lived by design, e.g. ci-status-update
# -- a long ActiveEnterTimestamp there is normal, not a symptom).
#
# State-transition dedup (not "page every tick while true"): tracks which units are CURRENTLY
# alerted in a local state file; only pages on a NEW crash-loop/wedge detection and on RECOVERY,
# matching the workspace's own standing-condition alerting convention. The two conditions share
# one state file with disjoint key prefixes (bare unit name = crash-loop, `wedged::`-prefixed =
# wedged) so either can independently alert/recover on the same unit without clobbering the
# other's tracking.
#
# Credential reuse: dispatches AS unified-trading-pm's own existing glue-runner identity
# (GH_TOKEN_SECRET from /etc/github-glue-runner.env, read via its own isolated CLOUDSDK_CONFIG)
# -- no new credential to provision or leak; same secret PM's own runner pool already uses.
set -euo pipefail

RESTART_THRESHOLD="${GLUE_WATCHDOG_RESTART_THRESHOLD:-5}"
# 180min: comfortably above quality-gates-v2's own job-level `timeout-minutes: 135` (the longest
# any legitimate qg-slices job should ever run) plus real margin for JIT-registration/queueing
# delay before a job starts. The market-tick-data-service zombie this was built for ran 21+
# hours -- anything past 135min is already firmly in "something is wrong" territory, 180min just
# keeps a comfortable buffer against false-positiving a genuinely-slow-but-healthy run.
WEDGED_THRESHOLD_SEC="${GLUE_WATCHDOG_WEDGED_THRESHOLD_SEC:-10800}"
# Resolved live, never hardcoded: the alert messages below used to hard-code
# i-0c9b283b31d6b5ca7 (the OLD shared VM, pre-runner-fleet-split) -- a stale reference that
# would point an operator at a now-decommissioned box after any future host migration too.
# IMDSv2 (this host's own instance-id) is always correct for wherever the script is actually
# running.
THIS_INSTANCE_ID="$(curl -sf -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null \
  | xargs -I{} curl -sf -H "X-aws-ec2-metadata-token: {}" \
    "http://169.254.169.254/latest/meta-data/instance-id" 2>/dev/null || echo "unknown-host")"
# /var/lib is root-owned; /opt/github-glue-runners itself is ALSO root:root (only specific
# pre-created subdirs like .gcloud are ubuntu-owned) -- verified live, not assumed, after the
# first attempt at each hit Permission denied. The unit runs User=ubuntu, so state has to live
# under ubuntu's own home instead.
STATE_DIR="${GLUE_WATCHDOG_STATE_DIR:-/home/ubuntu/.local/state/glue-runner-watchdog}"
STATE_FILE="${STATE_DIR}/alerted-units"
GH_REPO="IggyIkenna/unified-trading-pm"
PM_ENV_FILE="/etc/github-glue-runner.env"

mkdir -p "$STATE_DIR"
touch "$STATE_FILE"

log() { echo "[glue-runner-watchdog] $*"; }

# Resolve a GH token the same way glue-runner-run.sh does for this exact repo. GH_TOKEN_SECRET/
# GCP_PROJECT/GLUE_GCLOUD_CONFIG come from the environment, NOT a direct read of PM_ENV_FILE --
# that file is 0600 root:root (same as every per-repo one), unreadable by this unit's own
# User=ubuntu. The systemd unit's `EnvironmentFile=` directive is what actually reads it (at
# root, before the privilege drop) and injects these as env vars; a bare sed-parse here silently
# failed on every tick (2026-08-05 finding -- see the .service file's own comment). Falls back
# to parsing PM_ENV_FILE directly only for a manual/local run outside systemd, where no
# EnvironmentFile injection happens and the invoking user presumably already has read access.
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

# <unit-name> is crash-looping if systemd is actively retrying it past the threshold.
is_crash_looping() {
  local unit="$1" substate restarts
  substate="$(systemctl show "$unit" -p SubState --value 2>/dev/null || echo "")"
  restarts="$(systemctl show "$unit" -p NRestarts --value 2>/dev/null || echo "0")"
  [ "$substate" = "auto-restart" ] && [ "${restarts:-0}" -ge "$RESTART_THRESHOLD" ]
}

# Seconds since <unit-name>'s current invocation started. Empty/unparseable timestamp -> 0
# (never false-positives a wedge on a systemd read hiccup).
unit_active_seconds() {
  local unit="$1" ts epoch now
  ts="$(systemctl show "$unit" -p ActiveEnterTimestamp --value 2>/dev/null || echo "")"
  [ -z "$ts" ] && { echo 0; return; }
  epoch="$(date -d "$ts" +%s 2>/dev/null || echo 0)"
  [ "${epoch:-0}" -eq 0 ] && { echo 0; return; }
  now="$(date +%s)"
  echo $(( now - epoch ))
}

# <unit-name> is wedged if it's a JIT-ephemeral glue-* instance (never writer-*, those are
# long-lived by design) that's been continuously active well past any legitimate single job.
is_wedged() {
  local unit="$1" active_state
  case "$unit" in
    *@glue-*) : ;;      # JIT-ephemeral pool -- eligible
    *) return 1 ;;      # writer-* or anything else -- long-lived by design, never wedged
  esac
  active_state="$(systemctl show "$unit" -p ActiveState --value 2>/dev/null || echo "")"
  [ "$active_state" = "active" ] || return 1   # crash-looping units are "activating", not "active"
  [ "$(unit_active_seconds "$unit")" -ge "$WEDGED_THRESHOLD_SEC" ]
}

was_alerted()  { grep -qxF "$1" "$STATE_FILE" 2>/dev/null; }
mark_alerted() { echo "$1" >> "$STATE_FILE"; }
clear_alerted() {
  grep -vxF "$1" "$STATE_FILE" > "${STATE_FILE}.tmp" 2>/dev/null || true
  mv "${STATE_FILE}.tmp" "$STATE_FILE"
}

# Fire a repository_dispatch carrying the alert; best-effort (never fails the watchdog tick).
dispatch_alert() {
  local message="$1" severity="$2" dedup_key="$3" recovery="$4" token
  token="$(resolve_gh_token)" || { log "FATAL: could not resolve GH token, skipping dispatch for ${dedup_key}"; return 0; }
  jq -n \
    --arg message "$message" \
    --arg severity "$severity" \
    --arg dedup_key "$dedup_key" \
    --argjson recovery "$recovery" \
    '{event_type: "glue-runner-health", client_payload: {message: $message, severity: $severity, dedup_key: $dedup_key, cooldown_min: 30, recovery: $recovery}}' \
  | GH_TOKEN="$token" gh api "repos/${GH_REPO}/dispatches" --input - 2>&1 | sed 's/^/[glue-runner-watchdog] /' || true
}

mapfile -t units < <(systemctl list-units --type=service --all --no-legend 2>/dev/null \
  | grep glue | grep -v token-refresh | grep -v slot-refresh | awk '{print $1}')

currently_crashlooping=()
for unit in "${units[@]}"; do
  if is_crash_looping "$unit"; then
    currently_crashlooping+=("$unit")
  fi
done

# NEW crash-loops: page once, mark alerted.
for unit in "${currently_crashlooping[@]}"; do
  if ! was_alerted "$unit"; then
    restarts="$(systemctl show "$unit" -p NRestarts --value 2>/dev/null || echo "?")"
    log "NEW crash-loop: ${unit} (NRestarts=${restarts}) -- paging"
    dispatch_alert \
      "\`${unit}\` is crash-looping on \`${THIS_INSTANCE_ID}\` (\`NRestarts=${restarts}\`, state \`activating (auto-restart)\`) -- the runner process is DOWN, not just slow." \
      "CRITICAL" \
      "glue-runner-crash-loop:${unit}" \
      "false"
    mark_alerted "$unit"
  fi
done

# RECOVERY: previously alerted, now healthy -- one bookend post, then clear the state.
# Skips `wedged::`-prefixed lines -- those belong to the wedged-detection block below, which
# owns its own recovery pass over the same shared state file.
if [ -s "$STATE_FILE" ]; then
  while IFS= read -r unit; do
    [ -z "$unit" ] && continue
    case "$unit" in wedged::*) continue ;; esac
    still_looping=false
    for u in "${currently_crashlooping[@]:-}"; do
      [ "$u" = "$unit" ] && still_looping=true && break
    done
    if [ "$still_looping" = false ]; then
      log "RECOVERED: ${unit} -- posting bookend"
      dispatch_alert \
        "\`${unit}\` recovered -- no longer crash-looping on \`${THIS_INSTANCE_ID}\`." \
        "INFO" \
        "glue-runner-crash-loop:${unit}" \
        "true"
      clear_alerted "$unit"
    fi
  done < "$STATE_FILE"
fi

# ── Wedged-runner check (2026-08-05) ──────────────────────────────────────────
currently_wedged=()
for unit in "${units[@]}"; do
  if is_wedged "$unit"; then
    currently_wedged+=("$unit")
  fi
done

# NEW wedges: page once, mark alerted.
for unit in "${currently_wedged[@]}"; do
  key="wedged::${unit}"
  if ! was_alerted "$key"; then
    active_sec="$(unit_active_seconds "$unit")"
    active_hr="$(awk -v s="$active_sec" 'BEGIN{printf "%.1f", s/3600}')"
    mem_mb="$(awk -v b="$(systemctl show "$unit" -p MemoryCurrent --value 2>/dev/null || echo 0)" 'BEGIN{printf "%.0f", (b+0)/1024/1024}')"
    log "NEW wedge: ${unit} (active ${active_hr}h, ${mem_mb}MB) -- paging"
    dispatch_alert \
      "\`${unit}\` on \`${THIS_INSTANCE_ID}\` has been continuously active for **${active_hr}h** (>${WEDGED_THRESHOLD_SEC}s threshold, ${mem_mb}MB resident) -- a JIT glue-runner should cycle every job. This is very likely a hung job holding the process alive (Restart=always never fires because it never exits) rather than a slow one. \`systemctl restart ${unit}\` re-registers a fresh JIT token; check GitHub's own runner list for this repo first (\`gh api repos/<owner>/<repo>/actions/runners\`) -- an empty list confirms GitHub has already abandoned tracking this run and nothing else will unstick it." \
      "CRITICAL" \
      "$key" \
      "false"
    mark_alerted "$key"
  fi
done

# RECOVERY: previously alerted as wedged, now either restarted (fresh ActiveEnterTimestamp) or
# gone -- one bookend post, then clear the state.
if [ -s "$STATE_FILE" ]; then
  while IFS= read -r key; do
    [ -z "$key" ] && continue
    case "$key" in
      wedged::*) unit="${key#wedged::}" ;;
      *) continue ;;
    esac
    still_wedged=false
    for u in "${currently_wedged[@]:-}"; do
      [ "$u" = "$unit" ] && still_wedged=true && break
    done
    if [ "$still_wedged" = false ]; then
      log "RECOVERED (wedge): ${unit} -- posting bookend"
      dispatch_alert \
        "\`${unit}\` recovered -- no longer wedged on \`${THIS_INSTANCE_ID}\`." \
        "INFO" \
        "$key" \
        "true"
      clear_alerted "$key"
    fi
  done < "$STATE_FILE"
fi

if [ "${#currently_crashlooping[@]}" -eq 0 ]; then
  log "OK -- 0/${#units[@]} glue-runner units crash-looping"
else
  log "ALERT -- ${#currently_crashlooping[@]}/${#units[@]} glue-runner units crash-looping: ${currently_crashlooping[*]}"
fi

if [ "${#currently_wedged[@]}" -eq 0 ]; then
  log "OK -- 0/${#units[@]} glue-runner units wedged"
else
  log "ALERT -- ${#currently_wedged[@]}/${#units[@]} glue-runner units wedged: ${currently_wedged[*]}"
fi
