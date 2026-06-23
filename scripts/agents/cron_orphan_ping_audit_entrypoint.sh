#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# cron_orphan_ping_audit_entrypoint.sh — Cloud Run Job entrypoint for the
# every-4h orphan-ping audit cron.
#
# Plan-of-record:
#   CLAUDE.md HARD RULE "Every Active Ping Must Reference A Plan Item"
#   (codified 2026-05-20 round 5; cadence tightened round 6).
#
# Cron stack:
#   - Local (Ikenna's machine): `0 */4 * * *` via crontab.
#   - Cloud (Cloud Scheduler asia-northeast1): `15 2,6,10,14,18,22 * * *`
#     — offset by 2h so the two passes don't collide. Job name:
#     `uts-prod-orphan-ping-audit`.
#
# What this entrypoint does:
#   1. Clone unified-trading-pm from GitHub (live-defi-rollout branch) using
#      a GitHub PAT loaded from Secret Manager as $GH_PAT.
#   2. Run `scripts/agents/audit_ping_orphans.sh` — the script appends
#      orphan-notification entries to the orchestrator inboxes if orphans
#      are detected.
#   3. If git working tree is dirty after the run (i.e. orphan notifications
#      were appended), `git add` the modified ping ledgers, commit + push
#      back to live-defi-rollout so both operators' tab worktrees see the
#      notifications on next `git fetch`.
#   4. Exit 0 always (orphan detection is informational, not a Cloud Run
#      failure — operator inboxes carry the signal).
#
# Container image: google/cloud-sdk:slim (bash + git + gcloud preinstalled).
#
# Env vars (set by Cloud Run Job):
#   GH_PAT                          — GitHub PAT secret (Secret Manager → GH_PAT).
#   AGENT_ORCHESTRATOR_SLACK_WEBHOOK — optional; if set, posts a Slack alert to
#                                      #agent-orchestrator-alerts when orphans are found.
#                                      Wire via `gcloud run jobs update --update-secrets`.
#   PM_BRANCH    — branch to checkout + push to (default: live-defi-rollout).
#   PM_REPO_URL  — repo URL (default: https://github.com/IggyIkenna/unified-trading-pm.git).
#   GIT_AUTHOR_NAME / GIT_AUTHOR_EMAIL / GIT_COMMITTER_NAME / GIT_COMMITTER_EMAIL
#                — author identity for the auto-commit (set in the Job spec).

set -uo pipefail

PM_BRANCH="${PM_BRANCH:-live-defi-rollout}"
PM_REPO_URL_PUBLIC="${PM_REPO_URL:-https://github.com/IggyIkenna/unified-trading-pm.git}"
WORKDIR="${WORKDIR:-/tmp/unified-trading-pm}"
TIMESTAMP_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Optional Slack webhook — if AGENT_ORCHESTRATOR_SLACK_WEBHOOK is set (wired via
# Cloud Run Job --update-secrets), posts a real-time alert to #agent-orchestrator-alerts
# when orphans are detected. Complements the git-commit notification so operators
# don't need to run git fetch to see the signal.
SLACK_WEBHOOK="${AGENT_ORCHESTRATOR_SLACK_WEBHOOK:-}"

_slack_notify_orphans() {
  local count="$1"
  [[ -z "$SLACK_WEBHOOK" ]] && return 0
  local payload
  payload='{"text":":warning: *'"${count}"' orphan ping(s) detected* — pings in `_agent_pings.md` have no plan reference.\nRun `git pull` on your tab worktree to see details, or check orchestrator inboxes.\n_Cron: uts-prod-orphan-ping-audit @ '"${TIMESTAMP_UTC}"'_"}'
  curl -s -o /dev/null -w "%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "$SLACK_WEBHOOK" || echo "WARNING: Slack notify failed (non-fatal)" >&2
}

echo "── cron-orphan-ping-audit entrypoint ${TIMESTAMP_UTC} ──"

if [[ -z "${GH_PAT:-}" ]]; then
  echo "FATAL: GH_PAT env var not set. Wire the Secret Manager secret into the Cloud Run Job spec." >&2
  exit 2
fi

# Construct authenticated URL (token in URL is acceptable for ephemeral
# Cloud Run Job env — never logged, container destroyed at exit).
PM_REPO_URL_AUTH="$(echo "$PM_REPO_URL_PUBLIC" | sed "s|https://|https://x-access-token:${GH_PAT}@|")"

rm -rf "$WORKDIR"
echo "── cloning ${PM_REPO_URL_PUBLIC} @ ${PM_BRANCH} into ${WORKDIR}"
git clone --depth=10 --branch="$PM_BRANCH" "$PM_REPO_URL_AUTH" "$WORKDIR" 2>&1 | sed "s|${GH_PAT}|***REDACTED***|g"
if [[ ! -d "$WORKDIR/.git" ]]; then
  echo "FATAL: clone failed" >&2
  exit 3
fi

cd "$WORKDIR"

# Configure git identity (Cloud Run Job runs as service account, no global
# git config baked into the slim image).
git config user.email "${GIT_COMMITTER_EMAIL:-orphan-ping-cron@odum-research.com}"
git config user.name  "${GIT_COMMITTER_NAME:-orphan-ping-cron}"

# Run the audit. It exits 1 if orphans found (script appends notifications
# to the ping ledgers). We capture output + exit code but do NOT abort —
# we still want to commit + push the notifications.
# Write to temp file so we get both real-time Cloud Run logs AND the output
# to extract the orphan count from.
_AUDIT_LOG="$(mktemp)"
set +e
bash scripts/agents/audit_ping_orphans.sh 2>&1 | tee "$_AUDIT_LOG"
AUDIT_RC="${PIPESTATUS[0]}"
set -e

# Extract orphan count from audit output line "── total orphans: N"
ORPHAN_COUNT="$(grep -o 'total orphans: [0-9]*' "$_AUDIT_LOG" | grep -o '[0-9]*' || echo "?")"
rm -f "$_AUDIT_LOG"
echo "── audit exit code: ${AUDIT_RC} (orphans: ${ORPHAN_COUNT})"

if ! git diff --quiet; then
  echo "── orphan notifications appended — committing + pushing"
  # Only stage the ping ledger files the audit script writes to. Anything
  # else dirty would be a bug — log it loudly.
  EXPECTED_PATHS=(
    "ikenna_orchestrator/_agent_pings.md"
    "harsh_orchestrator/_agent_pings.md"
  )
  for p in "${EXPECTED_PATHS[@]}"; do
    if [[ -f "$p" ]]; then
      git add "$p"
    fi
  done

  UNSTAGED_DIRTY="$(git diff --name-only | grep -vE '^(ikenna_orchestrator|harsh_orchestrator)/_agent_pings\.md$' || true)"
  if [[ -n "$UNSTAGED_DIRTY" ]]; then
    echo "WARNING: unexpected dirty files (will NOT commit these):"
    echo "$UNSTAGED_DIRTY"
  fi

  if git diff --cached --quiet; then
    echo "── nothing staged — exit clean"
    exit 0
  fi

  git commit -m "chore(orphan-ping-cron): notify ${TIMESTAMP_UTC} (audit rc=${AUDIT_RC})

Auto-commit by Cloud Run Job uts-prod-orphan-ping-audit.
Cadence: every 4h offset by 2h from local cron.
Audit script: scripts/agents/audit_ping_orphans.sh.
"
  echo "── pushing to ${PM_BRANCH}"
  git push "$PM_REPO_URL_AUTH" "HEAD:${PM_BRANCH}" 2>&1 | sed "s|${GH_PAT}|***REDACTED***|g"
  echo "── push complete"
  _slack_notify_orphans "${ORPHAN_COUNT}"
else
  echo "── no orphans → no commit needed"
fi

echo "── done ${TIMESTAMP_UTC}"
exit 0
