#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# enable_slack_alerts.sh — SSM script to enable AGENT_ORCHESTRATOR_SLACK_WEBHOOK for one
# or more systemd units on a VM.
#
# notifications/slack.py reads AGENT_ORCHESTRATOR_SLACK_WEBHOOK at import and no-ops
# when unset — so a unit's Slack alerts are silently suppressed until this is set
# (orchestrator_master.md P1; and, for the two audit-cron oneshots,
# audit_cron_slack_alerting_and_15min_cadence_2026_07_25.md — .env.local does NOT
# carry this var on the live VM, only this drop-in does, confirmed 2026-07-25 when the
# oneshots' own EnvironmentFile=.env.local line resolved to nothing). This fetches the
# webhook URL from Secret Manager and wires it into EACH named unit's systemd env via a
# per-unit drop-in (mirroring how `orchestrator.service.d/slack-alerts.conf` already
# does it), then daemon-reloads. The webhook is a SECRET — never echoed; every drop-in
# is mode 600.
#
# Usage (run via AWS SSM SendCommand / gcloud compute ssh on each target VM):
#   bash scripts/orchestrator/enable_slack_alerts.sh                    # defaults to: orchestrator
#   bash scripts/orchestrator/enable_slack_alerts.sh orchestrator audit-stale-gate-references audit-false-done
#
# Secret resolution order (first hit wins), on whichever cloud the VM is on:
#   1. AGENT_ORCHESTRATOR_SLACK_WEBHOOK   (dedicated orchestrator webhook)
#   2. alerting-slack-webhook-url         (shared alerting-service / "hives" webhook)
# Override the secret id with SLACK_WEBHOOK_SECRET_ID env.
#
# Safe to re-run — idempotent (each drop-in overwritten; `orchestrator` restart harmless,
# the audit-cron oneshots are NOT force-restarted — see the loop below for why).
set -euo pipefail

UNITS=("$@")
[[ ${#UNITS[@]} -eq 0 ]] && UNITS=("orchestrator")

PROJECT_ID="${GCP_PROJECT_ID:-central-element-323112}"

echo "=== enable_slack_alerts.sh ==="
echo "VM: $(hostname)"
echo "units: ${UNITS[*]}"

# Candidate secret ids (verified live 2026-06-01): AWS SM uses the `unified-trading/`
# prefix; GCP SM uses the bare name. Both clouds carry the dedicated
# AGENT_ORCHESTRATOR_SLACK_WEBHOOK + the shared uts-live-alerts-slack-webhook.
_AWS_SIDS=("unified-trading/AGENT_ORCHESTRATOR_SLACK_WEBHOOK" "unified-trading/uts-live-alerts-slack-webhook")
_GCP_SIDS=("AGENT_ORCHESTRATOR_SLACK_WEBHOOK" "alerting-uts-live-alerts-slack-webhook")
if [[ -n "${SLACK_WEBHOOK_SECRET_ID:-}" ]]; then
  _AWS_SIDS=("${SLACK_WEBHOOK_SECRET_ID}" "${_AWS_SIDS[@]}")
  _GCP_SIDS=("${SLACK_WEBHOOK_SECRET_ID}" "${_GCP_SIDS[@]}")
fi

_fetch_aws() { aws secretsmanager get-secret-value --secret-id "$1" --query SecretString --output text 2>/dev/null || true; }
_fetch_gcp() { gcloud secrets versions access latest --secret="$1" --project="$PROJECT_ID" 2>/dev/null || true; }

WEBHOOK=""
if command -v aws >/dev/null 2>&1; then
  for SID in "${_AWS_SIDS[@]}"; do
    WEBHOOK="$(_fetch_aws "$SID")"; [[ "$WEBHOOK" == "None" ]] && WEBHOOK=""
    if [[ -n "$WEBHOOK" ]]; then echo "Resolved webhook from AWS SM: $SID (redacted)"; break; fi
  done
fi
if [[ -z "$WEBHOOK" ]] && command -v gcloud >/dev/null 2>&1; then
  for SID in "${_GCP_SIDS[@]}"; do
    WEBHOOK="$(_fetch_gcp "$SID")"; [[ "$WEBHOOK" == "None" ]] && WEBHOOK=""
    if [[ -n "$WEBHOOK" ]]; then echo "Resolved webhook from GCP SM: $SID (redacted)"; break; fi
  done
fi

if [[ -z "$WEBHOOK" ]]; then
  echo "ERROR: no Slack webhook secret found (AWS: ${_AWS_SIDS[*]} ; GCP: ${_GCP_SIDS[*]})." >&2
  echo "       Create one, e.g.:  printf '%s' 'https://hooks.slack.com/services/...' | gcloud secrets create AGENT_ORCHESTRATOR_SLACK_WEBHOOK --data-file=- --project=$PROJECT_ID" >&2
  exit 1
fi

# Basic sanity (don't echo the value): must look like an https Slack webhook.
case "$WEBHOOK" in
  https://hooks.slack.com/*) : ;;
  https://*) echo "WARN: webhook is https but not hooks.slack.com — proceeding anyway" ;;
  *) echo "ERROR: resolved webhook is not an https URL — refusing to write" >&2; exit 1 ;;
esac

for UNIT in "${UNITS[@]}"; do
  DROPIN_DIR="/etc/systemd/system/${UNIT}.service.d"
  DROPIN_FILE="$DROPIN_DIR/slack-alerts.conf"
  mkdir -p "$DROPIN_DIR"
  umask 077
  cat > "$DROPIN_FILE" <<EOF
[Service]
Environment=AGENT_ORCHESTRATOR_SLACK_WEBHOOK=$WEBHOOK
EOF
  chmod 600 "$DROPIN_FILE"
  umask 022
  echo "Wrote $DROPIN_FILE (mode 600, value redacted)"
done

systemctl daemon-reload

# orchestrator is the only long-running Type=simple unit this script ever targets — its
# already-running process needs a restart to pick up the new env. audit-stale-gate-
# references / audit-false-done are Type=oneshot (no persistent process to restart);
# daemon-reload alone is enough for their NEXT systemd-timer-triggered tick to inherit
# the drop-in, so they are deliberately NOT force-restarted here (a restart on a oneshot
# just re-runs it early — harmless, but unnecessary).
for UNIT in "${UNITS[@]}"; do
  if [[ "$UNIT" == "orchestrator" ]]; then
    systemctl restart orchestrator
    echo "orchestrator restarted"
  fi
done

# Verify the env is present WITHOUT printing the secret.
for UNIT in "${UNITS[@]}"; do
  if systemctl show "$UNIT" --property=Environment | grep -q 'AGENT_ORCHESTRATOR_SLACK_WEBHOOK='; then
    echo "✅ AGENT_ORCHESTRATOR_SLACK_WEBHOOK is set for ${UNIT} — Slack alerts ENABLED"
  else
    echo "⚠️  env not visible via systemctl show for ${UNIT} — check /etc/systemd/system/${UNIT}.service.d/slack-alerts.conf"
  fi
done
echo "=== done ==="
