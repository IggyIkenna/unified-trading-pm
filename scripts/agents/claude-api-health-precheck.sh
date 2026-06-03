#!/usr/bin/env bash
# claude-api-health-precheck.sh — Check Claude API health before invoking agent workflows.
#
# Checks the last run of claude-api-health-monitor.yml via GH API.
# If the last health check failed (conclusion != success), fast-fails with Slack alert.
#
# Usage:
#   source scripts/agents/claude-api-health-precheck.sh
#   check_claude_api_health  # exits 1 if unhealthy
#
# Requires env vars:
#   GH_TOKEN               — GitHub PAT for API access
#   GH_ORG                 — GitHub org (default: IggyIkenna)
#
# Optional env vars:
#   SLACK_CI_WEBHOOK_URL   — For alert on failure (Slack #ci-failures incoming webhook)
#   CALLING_WORKFLOW        — Name of the calling workflow (for alert context)
#   SKIP_HEALTH_CHECK      — Set to "true" to bypass (emergency override)

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

  # Health check failed — send Slack alert (#ci-failures) and fail
  echo "[claude-health-precheck] FAIL: Claude API health check conclusion=$conclusion"
  echo "[claude-health-precheck] Aborting $calling_workflow to avoid wasting API credits on a degraded API"

  local webhook="${SLACK_CI_WEBHOOK_URL:-}"
  if [ -n "$webhook" ] && [ "${webhook#https://}" != "$webhook" ]; then
    local text="Claude API Unhealthy — Agent Skipped\nWorkflow: ${calling_workflow}\nLast health check: ${conclusion} at ${created_at}\nSkipping agent invocation until API recovers.\nOverride: set SKIP_HEALTH_CHECK=true"
    curl -s -o /dev/null -X POST "$webhook" \
      -H 'Content-Type: application/json' \
      --data "$(python3 -c "import json,sys; print(json.dumps({'text': sys.argv[1]}))" "$text")" || true
  fi

  return 1
}
