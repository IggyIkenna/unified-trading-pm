#!/usr/bin/env bash
# enable_slack_alerts.sh — SSM script to enable AGENT_ORCHESTRATOR_SLACK_WEBHOOK on one VM.
#
# notifications/slack.py reads AGENT_ORCHESTRATOR_SLACK_WEBHOOK at import and no-ops
# when unset — so the orchestrator's Slack alerts (slot blocked / stale / failed,
# git-staleness ahead>0||diverged, autospawn flap, watchdog kill, account rotation,
# setup-token expiry, …) are silently suppressed fleet-wide until this is set
# (orchestrator_master.md P1). This fetches the webhook URL from Secret Manager and
# wires it into the orchestrator's systemd env via a drop-in, then restarts so the
# Slack path goes live. The webhook is a SECRET — never echoed; drop-in is mode 600.
#
# Usage (run via AWS SSM SendCommand / gcloud compute ssh on each target VM):
#   bash scripts/orchestrator/enable_slack_alerts.sh
#
# Secret resolution order (first hit wins), on whichever cloud the VM is on:
#   1. AGENT_ORCHESTRATOR_SLACK_WEBHOOK   (dedicated orchestrator webhook)
#   2. alerting-slack-webhook-url         (shared alerting-service / "hives" webhook)
# Override the secret id with SLACK_WEBHOOK_SECRET_ID env.
#
# Safe to re-run — idempotent (drop-in overwritten, restart harmless).
set -euo pipefail

DROPIN_DIR="/etc/systemd/system/orchestrator.service.d"
DROPIN_FILE="$DROPIN_DIR/slack-alerts.conf"
PROJECT_ID="${GCP_PROJECT_ID:-central-element-323112}"

echo "=== enable_slack_alerts.sh ==="
echo "VM: $(hostname)"

_fetch_secret() {
  local sid="$1" val=""
  # Try AWS SM then GCP SM — whichever this VM can reach.
  if command -v aws >/dev/null 2>&1; then
    val="$(aws secretsmanager get-secret-value --secret-id "$sid" --query SecretString --output text 2>/dev/null || echo "")"
  fi
  if [[ -z "$val" || "$val" == "None" ]] && command -v gcloud >/dev/null 2>&1; then
    val="$(gcloud secrets versions access latest --secret="$sid" --project="$PROJECT_ID" 2>/dev/null || echo "")"
  fi
  [[ "$val" == "None" ]] && val=""
  printf '%s' "$val"
}

WEBHOOK=""
for SID in "${SLACK_WEBHOOK_SECRET_ID:-AGENT_ORCHESTRATOR_SLACK_WEBHOOK}" alerting-slack-webhook-url; do
  WEBHOOK="$(_fetch_secret "$SID")"
  if [[ -n "$WEBHOOK" ]]; then
    echo "Resolved webhook from Secret Manager secret: $SID (value redacted)"
    break
  fi
done

if [[ -z "$WEBHOOK" ]]; then
  echo "ERROR: no Slack webhook secret found (tried AGENT_ORCHESTRATOR_SLACK_WEBHOOK + alerting-slack-webhook-url)." >&2
  echo "       Create one, e.g.:  printf '%s' 'https://hooks.slack.com/services/...' | gcloud secrets create AGENT_ORCHESTRATOR_SLACK_WEBHOOK --data-file=- --project=$PROJECT_ID" >&2
  exit 1
fi

# Basic sanity (don't echo the value): must look like an https Slack webhook.
case "$WEBHOOK" in
  https://hooks.slack.com/*) : ;;
  https://*) echo "WARN: webhook is https but not hooks.slack.com — proceeding anyway" ;;
  *) echo "ERROR: resolved webhook is not an https URL — refusing to write" >&2; exit 1 ;;
esac

mkdir -p "$DROPIN_DIR"
umask 077
cat > "$DROPIN_FILE" <<EOF
[Service]
Environment=AGENT_ORCHESTRATOR_SLACK_WEBHOOK=$WEBHOOK
EOF
chmod 600 "$DROPIN_FILE"
umask 022
echo "Wrote $DROPIN_FILE (mode 600, value redacted)"

systemctl daemon-reload
systemctl restart orchestrator
echo "orchestrator restarted"

# Verify the env is present WITHOUT printing the secret.
if systemctl show orchestrator --property=Environment | grep -q 'AGENT_ORCHESTRATOR_SLACK_WEBHOOK='; then
  echo "✅ AGENT_ORCHESTRATOR_SLACK_WEBHOOK is set in the orchestrator env — Slack alerts ENABLED"
else
  echo "⚠️  env not visible via systemctl show — check $DROPIN_FILE"
fi
echo "=== done ==="
