#!/usr/bin/env bash
# claude-api-health-precheck.sh — Check Claude API health before invoking agent workflows.
#
# Checks the last run of claude-api-health-monitor.yml via GH API.
# If the last health check failed (conclusion != success), fast-fails with Telegram alert.
#
# Usage:
#   source scripts/agents/claude-api-health-precheck.sh
#   check_claude_api_health  # exits 1 if unhealthy
#
# Requires env vars:
#   GH_TOKEN             — GitHub PAT for API access
#   GH_ORG               — GitHub org (default: IggyIkenna)
#
# Optional env vars:
#   TELEGRAM_BOT_TOKEN   — For alert on failure
#   TELEGRAM_CHAT_ID     — Target chat
#   CALLING_WORKFLOW      — Name of the calling workflow (for alert context)
#   SKIP_HEALTH_CHECK    — Set to "true" to bypass (emergency override)

set -euo pipefail

check_claude_api_health() {
  local org="${GH_ORG:-IggyIkenna}"
  local calling_workflow="${CALLING_WORKFLOW:-unknown}"

  # Emergency override
  if [ "${SKIP_HEALTH_CHECK:-false}" = "true" ]; then
    echo "[claude-health-precheck] SKIP_HEALTH_CHECK=true — bypassing health check"
    return 0
  fi

  if [ -z "${GH_TOKEN:-}" ]; then
    echo "[claude-health-precheck] GH_TOKEN not set — skipping health check (cannot query API)"
    return 0
  fi

  echo "[claude-health-precheck] Checking last claude-api-health-monitor.yml run..."

  # Query the last completed run of claude-api-health-monitor.yml
  local last_run
  last_run=$(gh run list \
    --repo "${org}/unified-trading-pm" \
    --workflow "claude-api-health-monitor.yml" \
    --limit 1 \
    --json conclusion,status,createdAt \
    --jq '.[0]' 2>/dev/null || echo "")

  if [ -z "$last_run" ] || [ "$last_run" = "null" ]; then
    echo "[claude-health-precheck] No health monitor runs found — proceeding (monitor may not be deployed yet)"
    return 0
  fi

  local conclusion
  conclusion=$(echo "$last_run" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('conclusion') or 'unknown')" 2>/dev/null || echo "unknown")
  local status
  status=$(echo "$last_run" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status') or 'unknown')" 2>/dev/null || echo "unknown")
  local created_at
  created_at=$(echo "$last_run" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('createdAt') or 'unknown')" 2>/dev/null || echo "unknown")

  echo "[claude-health-precheck] Last health check: status=$status conclusion=$conclusion created=$created_at"

  # If the health check is still running, check the one before it
  if [ "$status" != "completed" ]; then
    echo "[claude-health-precheck] Last run still in progress — checking previous run"
    local prev_run
    prev_run=$(gh run list \
      --repo "${org}/unified-trading-pm" \
      --workflow "claude-api-health-monitor.yml" \
      --limit 2 \
      --json conclusion,status \
      --jq '.[1]' 2>/dev/null || echo "")
    if [ -n "$prev_run" ] && [ "$prev_run" != "null" ]; then
      conclusion=$(echo "$prev_run" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('conclusion') or 'unknown')" 2>/dev/null || echo "unknown")
    else
      echo "[claude-health-precheck] No previous completed run — proceeding optimistically"
      return 0
    fi
  fi

  if [ "$conclusion" = "success" ]; then
    echo "[claude-health-precheck] Claude API healthy (last check: $created_at) — proceeding"
    return 0
  fi

  # Health check failed — send Telegram alert and fail
  echo "[claude-health-precheck] FAIL: Claude API health check conclusion=$conclusion"
  echo "[claude-health-precheck] Aborting $calling_workflow to avoid wasting API credits on a degraded API"

  if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
    local text="⚠️ *Claude API Unhealthy — Agent Skipped*%0AWorkflow: \`${calling_workflow}\`%0ALast health check: \`${conclusion}\` at ${created_at}%0ASkipping agent invocation until API recovers.%0AOverride: set SKIP_HEALTH_CHECK=true"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d "chat_id=${TELEGRAM_CHAT_ID}" \
      -d "text=${text}" \
      -d "parse_mode=Markdown" > /dev/null 2>&1 || true
  fi

  return 1
}
