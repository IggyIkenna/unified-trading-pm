#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# cron_hygiene_sweep_entrypoint.sh — Cloud Run Job entrypoint for the
# daily plan hygiene sweep cron (0 5 * * * UTC).
#
# Plan-of-record:
#   CLAUDE.md § "Plan Hygiene — Frontmatter, Line Caps, Archive Candidates"
#   codex/11-project-management/plan-hygiene.md
#   deployment-service/terraform/gcp/hygiene_sweep_scheduler.tf
#
# What this entrypoint does:
#   1. Clone unified-trading-pm from GitHub (live-defi-rollout branch) using
#      a GitHub PAT loaded from Secret Manager as $GH_PAT.
#   2. Run `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` — exits 1 if
#      any HARD check fails (todo regression or frontmatter violations).
#   3. If failures: post a Slack alert to #agent-orchestrator-alerts (webhook
#      from Secret Manager) — details stay in the Cloud Run job logs.
#      The pre-2026-07-04 behaviour (append to the _agent_pings.md orchestrator
#      inboxes + auto-commit) is RETIRED — the ping-ledger channel is dead
#      (agent comms = agent-orchestrator HTTP server; nobody reads the ledgers).
#   4. Exit 0 always (hard failures are surfaced via Slack, not Cloud Run job
#      failure — avoids noisy PagerDuty alerts for plan hygiene).
#
# Container image: google/cloud-sdk:slim (bash + git + python3 preinstalled).
#
# Env vars (set by Cloud Run Job):
#   GH_PAT       — GitHub PAT secret (Secret Manager → GH_PAT).
#   PM_BRANCH    — branch to checkout (default: live-defi-rollout).
#   PM_REPO_URL  — repo URL (default: https://github.com/IggyIkenna/unified-trading-pm.git).
#   AGENT_ORCHESTRATOR_SLACK_WEBHOOK — Slack webhook for failure alerts
#                (Secret Manager → AGENT_ORCHESTRATOR_SLACK_WEBHOOK).

set -uo pipefail

PM_BRANCH="${PM_BRANCH:-live-defi-rollout}"
PM_REPO_URL_PUBLIC="${PM_REPO_URL:-https://github.com/IggyIkenna/unified-trading-pm.git}"
WORKDIR="${WORKDIR:-/tmp/unified-trading-pm}"
TIMESTAMP_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "── cron-plan-hygiene-sweep entrypoint ${TIMESTAMP_UTC} ──"

if [[ -z "${GH_PAT:-}" ]]; then
  echo "FATAL: GH_PAT env var not set. Wire the Secret Manager secret into the Cloud Run Job spec." >&2
  exit 2
fi

PM_REPO_URL_AUTH="$(echo "$PM_REPO_URL_PUBLIC" | sed "s|https://|https://x-access-token:${GH_PAT}@|")"

rm -rf "$WORKDIR"
echo "── cloning ${PM_REPO_URL_PUBLIC} @ ${PM_BRANCH} into ${WORKDIR}"
git clone --depth=10 --branch="$PM_BRANCH" "$PM_REPO_URL_AUTH" "$WORKDIR" 2>&1 | sed "s|${GH_PAT}|***REDACTED***|g"
if [[ ! -d "$WORKDIR/.git" ]]; then
  echo "FATAL: clone failed" >&2
  exit 3
fi

cd "$WORKDIR"

# Run the hygiene sweep in --ci mode. Capture full output for the notification.
# Do NOT abort on failure — we want to write the notification regardless.
_SWEEP_LOG="$(mktemp)"
set +e
bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci 2>&1 | tee "$_SWEEP_LOG"
SWEEP_RC="${PIPESTATUS[0]}"
set -e

# Extract hard/soft counts from summary line "Hard failures: N  |  Soft warnings: M"
HARD_COUNT="$(grep -o 'Hard failures: [0-9]*' "$_SWEEP_LOG" | grep -o '[0-9]*' || echo "?")"
SOFT_COUNT="$(grep -o 'Soft warnings: [0-9]*' "$_SWEEP_LOG" | grep -o '[0-9]*' || echo "?")"
rm -f "$_SWEEP_LOG"
echo "── sweep exit code: ${SWEEP_RC} (hard=${HARD_COUNT}, soft=${SOFT_COUNT})"

if [[ "$SWEEP_RC" -eq 0 ]]; then
  echo "── sweep PASSED — no notifications needed"
  echo "── done ${TIMESTAMP_UTC}"
  exit 0
fi

# Hard failures found — alert via Slack; full details live in the Cloud Run
# job logs above. (Ping-ledger inbox appends retired 2026-07-04 — nobody reads
# the _agent_pings.md files; agent comms = agent-orchestrator HTTP server.)
echo "── sweep FAILED (hard=${HARD_COUNT}, soft=${SOFT_COUNT}) — posting Slack alert"

SLACK_WEBHOOK="${AGENT_ORCHESTRATOR_SLACK_WEBHOOK:-}"
if [[ -n "$SLACK_WEBHOOK" ]]; then
  PAYLOAD='{"text":":broom: *Plan-hygiene sweep FAILED* — hard failures: '"${HARD_COUNT}"', soft warnings: '"${SOFT_COUNT}"'.\nFix: `bash scripts/plan-hygiene/run_hygiene_sweep.sh` locally in unified-trading-pm, then push to live-defi-rollout.\n_Details: Cloud Run job `uts-prod-plan-hygiene-sweep` logs @ '"${TIMESTAMP_UTC}"'_"}'
  curl -s -o /dev/null -w "slack http %{http_code}\n" -X POST \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "$SLACK_WEBHOOK" || echo "WARNING: Slack notify failed (non-fatal)" >&2
else
  echo "── AGENT_ORCHESTRATOR_SLACK_WEBHOOK not set — alert visible in job logs only"
fi

echo "── done ${TIMESTAMP_UTC}"
exit 0
