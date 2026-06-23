#!/usr/bin/env bash
# Epic: infrastructure_master
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
#   3. If failures: append a notification entry to BOTH orchestrator inboxes
#      (ikenna_orchestrator/_agent_pings.md + harsh_orchestrator/_agent_pings.md)
#      and commit + push back to live-defi-rollout.
#   4. Exit 0 always (hard failures are surfaced via inbox notifications, not
#      Cloud Run job failure — avoids noisy PagerDuty alerts for plan hygiene).
#
# Container image: google/cloud-sdk:slim (bash + git + python3 preinstalled).
#
# Env vars (set by Cloud Run Job):
#   GH_PAT       — GitHub PAT secret (Secret Manager → GH_PAT).
#   PM_BRANCH    — branch to checkout + push to (default: live-defi-rollout).
#   PM_REPO_URL  — repo URL (default: https://github.com/IggyIkenna/unified-trading-pm.git).
#   GIT_AUTHOR_NAME / GIT_AUTHOR_EMAIL / GIT_COMMITTER_NAME / GIT_COMMITTER_EMAIL
#                — author identity for the auto-commit (set in the Job spec).

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

git config user.email "${GIT_COMMITTER_EMAIL:-hygiene-sweep-cron@odum-research.com}"
git config user.name  "${GIT_COMMITTER_NAME:-hygiene-sweep-cron}"

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

# Hard failures found — write notification to both orchestrator inboxes.
echo "── sweep FAILED — appending notifications to orchestrator inboxes"

NOTIFICATION="
## [hygiene-sweep-cron] ${TIMESTAMP_UTC} — HARD FAILURES DETECTED

\`run_hygiene_sweep.sh --ci\` exit code: ${SWEEP_RC}
Hard failures: ${HARD_COUNT}  |  Soft warnings: ${SOFT_COUNT}

Run locally to see details:
\`\`\`bash
cd \$(git rev-parse --show-toplevel)
bash scripts/plan-hygiene/run_hygiene_sweep.sh
\`\`\`

Auto-fix frontmatter:
\`\`\`bash
python3 scripts/plan-hygiene/fix_frontmatter.py
\`\`\`

This notification will reappear daily at 05:00 UTC until the sweep passes clean.
Clear by fixing violations and pushing to live-defi-rollout.
"

EXPECTED_PATHS=(
  "ikenna_orchestrator/_agent_pings.md"
  "harsh_orchestrator/_agent_pings.md"
)
for p in "${EXPECTED_PATHS[@]}"; do
  if [[ -f "$p" ]]; then
    echo "$NOTIFICATION" >> "$p"
    git add "$p"
  fi
done

if git diff --cached --quiet; then
  echo "── nothing staged — exit clean"
  echo "── done ${TIMESTAMP_UTC}"
  exit 0
fi

git commit -m "chore(hygiene-cron): hard failures detected ${TIMESTAMP_UTC} (hard=${HARD_COUNT}, soft=${SOFT_COUNT})

Auto-commit by Cloud Run Job uts-prod-plan-hygiene-sweep.
Cadence: daily at 05:00 UTC.
Sweep script: scripts/plan-hygiene/run_hygiene_sweep.sh.
Fix violations + push to live-defi-rollout to clear this notification.
"
echo "── pushing to ${PM_BRANCH}"
git push "$PM_REPO_URL_AUTH" "HEAD:${PM_BRANCH}" 2>&1 | sed "s|${GH_PAT}|***REDACTED***|g"
echo "── push complete"

echo "── done ${TIMESTAMP_UTC}"
exit 0
