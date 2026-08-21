#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
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

  # RETIRED 2026-06-07 — ALWAYS-PASS NO-OP. The fleet no longer uses the pay-per-call Claude API:
  # every agent escalates to an agent-orchestrator VM worker running on Claude Code session auth
  # (setup-tokens), so the raw-API billing/health probed by `claude-api-health-monitor.yml` (now
  # DELETED) is irrelevant — and gating on it FALSE-DAMMED the agentic-CI layer during credit
  # outages (the documented cascade-dammer). The real "out of capacity" signal is
  # agent-orchestrator's per-account `account_status`, which fires `notify_all_accounts_unusable`
  # to #agent-orchestrator-alerts only when ALL Claude Code accounts go unusable. This shim keeps
  # the workflows that still `source` it working; remove the call sites at leisure. SSOT:
  # cicd_contract_hardening_2026_06_01 § billing-alert retirement.
  echo "[claude-health-precheck] RETIRED no-op — Claude API unused (AO account-health is the SSOT); proceeding."
  return 0
}
