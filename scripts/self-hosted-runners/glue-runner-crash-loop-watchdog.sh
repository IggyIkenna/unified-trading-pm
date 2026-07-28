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
# State-transition dedup (not "page every tick while true"): tracks which units are CURRENTLY
# alerted in a local state file; only pages on a NEW crash-loop detection and on RECOVERY,
# matching the workspace's own standing-condition alerting convention.
#
# Credential reuse: dispatches AS unified-trading-pm's own existing glue-runner identity
# (GH_TOKEN_SECRET from /etc/github-glue-runner.env, read via its own isolated CLOUDSDK_CONFIG)
# -- no new credential to provision or leak; same secret PM's own runner pool already uses.
set -euo pipefail

RESTART_THRESHOLD="${GLUE_WATCHDOG_RESTART_THRESHOLD:-5}"
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

# Resolve a GH token the same way glue-runner-run.sh does for this exact repo: read
# GH_TOKEN_SECRET/GCP_PROJECT/GLUE_GCLOUD_CONFIG from PM's own env file, fetch from Secret
# Manager via the isolated per-pool gcloud config. Never logs the token itself.
resolve_gh_token() {
  local secret project gcloud_cfg
  secret="$(sed -n 's/^GH_TOKEN_SECRET=//p' "$PM_ENV_FILE" | head -1)"
  project="$(sed -n 's/^GCP_PROJECT=//p' "$PM_ENV_FILE" | head -1)"
  gcloud_cfg="$(sed -n 's/^GLUE_GCLOUD_CONFIG=//p' "$PM_ENV_FILE" | head -1)"
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
      "\`${unit}\` is crash-looping on \`i-0c9b283b31d6b5ca7\` (\`NRestarts=${restarts}\`, state \`activating (auto-restart)\`) -- the runner process is DOWN, not just slow." \
      "CRITICAL" \
      "glue-runner-crash-loop:${unit}" \
      "false"
    mark_alerted "$unit"
  fi
done

# RECOVERY: previously alerted, now healthy -- one bookend post, then clear the state.
if [ -s "$STATE_FILE" ]; then
  while IFS= read -r unit; do
    [ -z "$unit" ] && continue
    still_looping=false
    for u in "${currently_crashlooping[@]:-}"; do
      [ "$u" = "$unit" ] && still_looping=true && break
    done
    if [ "$still_looping" = false ]; then
      log "RECOVERED: ${unit} -- posting bookend"
      dispatch_alert \
        "\`${unit}\` recovered -- no longer crash-looping on \`i-0c9b283b31d6b5ca7\`." \
        "INFO" \
        "glue-runner-crash-loop:${unit}" \
        "true"
      clear_alerted "$unit"
    fi
  done < "$STATE_FILE"
fi

if [ "${#currently_crashlooping[@]}" -eq 0 ]; then
  log "OK -- 0/${#units[@]} glue-runner units crash-looping"
else
  log "ALERT -- ${#currently_crashlooping[@]}/${#units[@]} glue-runner units crash-looping: ${currently_crashlooping[*]}"
fi
