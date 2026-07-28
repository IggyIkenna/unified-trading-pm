#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction)
# Lifecycle: permanent
# Delete-when: the notify-slack fan-out is gone (options-doc A3/A4/A5 land) AND nobody needs a
#              before/after billed-minutes number any more
#
# measure-billed-notify-cost.sh — count the ACTUAL BILLED notify-slack job executions over a window.
#
# ┌─ WHY THIS IS IN THE REPO ──────────────────────────────────────────────────────────────────────┐
# │ This produced the notify-slack spend numbers that the CI-cost plan's KEEP-D / A3 / A4 / A5      │
# │ decisions rest on, and the plan still has an OPEN todo that needs it again:                     │
# │   "After 3-5 days, re-measure PM's billed minutes; confirm the moved workflows bill ~$0"        │
# │ (/plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md). Without this script that todo is │
# │ unverifiable and the whole project's success metric is an assertion. It lived in a scratchpad   │
# │ until 2026-07-16.                                                                               │
# └────────────────────────────────────────────────────────────────────────────────────────────────┘
#
# ┌─ THE MEASUREMENT IS SUBTLE — it took THREE attempts to get right. Read before "simplifying". ──┐
# │ 1. Counting notify-ish jobs per run          -> WRONG. SKIPPED jobs are not billed, so this     │
# │                                                 over-counts every dedup-suppressed alert.       │
# │ 2. Counting non-skipped notify jobs          -> closer, but a throttled API call returned empty │
# │                                                 and was silently counted as 0 -> UNDER-counts.  │
# │ 3. (this) count jobs named "*/send-notification" with conclusion != skipped, WITH retry.        │
# │                                                                                                  │
# │ The naming detail is load-bearing: the notify-slack reusable's job is `send-notification`, and  │
# │ it appears in a caller's run ONLY when it actually ran. A caller whose notify was skipped shows │
# │ a bare `notify` job instead. That distinction is the difference between billed and not.         │
# │                                                                                                  │
# │ WHY ONLY THE DEDUP-CAPABLE CALLERS: dedup suppresses the Slack POST but the job still RUNS and  │
# │ BILLS — so those are the only callers where billed > posted. Every non-dedup caller always       │
# │ posts, so its billed count == its post count, which the Slack ledger already gives us.          │
# └────────────────────────────────────────────────────────────────────────────────────────────────┘
#
# Billing model: GitHub bills hosted minutes with a 1-MINUTE MINIMUM PER JOB. A notify job runs for
# ~5s and bills 60s. That is the whole reason this fan-out is expensive enough to measure.
#
#   ./measure-billed-notify-cost.sh                 # last 30 days
#   DAYS=7 ./measure-billed-notify-cost.sh          # last 7 days
#   LEDGER_POSTS=117 ./measure-billed-notify-cost.sh  # feed the Slack-ledger post count for a total
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../.." && pwd)"
cd "${REPO_ROOT}" || { echo "cannot cd to ${REPO_ROOT}" >&2; exit 1; }

DAYS="${DAYS:-30}"
REPO="${REPO:-IggyIkenna/unified-trading-pm}"
# Slack-ledger POST count for the same window. Non-dedup callers' billed == their posts, so this is
# the only way to reach a fleet total. Leave empty to report the dedup-only number.
LEDGER_POSTS="${LEDGER_POSTS:-}"
MINUTE_RATE_USD="${MINUTE_RATE_USD:-0.006}" # ubuntu-latest, per billed minute (1-min minimum/job)
export REPO

# shellcheck disable=SC1091
source scripts/workspace/load-gh-token.sh >/dev/null 2>&1 || true
command -v gh >/dev/null 2>&1 || { echo "gh not found" >&2; exit 1; }

SINCE="$(date -u -d "${DAYS} days ago" +%Y-%m-%d)"

# The ONLY callers where billed can exceed posted (dedup fires the job, then suppresses the post).
# Regenerate: grep -l 'dedup_key:' .github/workflows/*.yml
DEDUP_CALLERS="${DEDUP_CALLERS:-cloud-build-failure-watcher ci-health sit-debounce-trigger branch-health fix-approval-timeout escalate-to-orchestrator cascade-qg-ordering ruleset-drift-alert major-bump-issue-handler semver-agent request-major-bump}"

# Retry, because a throttled API call returns EMPTY and would be silently counted as 0 — an
# under-count that looks exactly like a real result. That was attempt #2's bug.
billed_run() {
  local id="$1" out="" i
  for i in 1 2 3; do
    out="$(gh api "/repos/${REPO}/actions/runs/${id}/jobs" \
      --jq '[.jobs[] | select(.name|test("send-notification")) | select(.conclusion!="skipped")] | length' 2>/dev/null)"
    [ -n "${out}" ] && { echo "${out}"; return 0; }
    sleep $((i * 2))
  done
  echo "  WARN: run ${id} unreadable after 3 tries — counted 0 (UNDER-count)" >&2
  echo 0
}
export -f billed_run

printf 'Billed notify-slack job executions — last %s days (since %s), repo %s\n\n' "${DAYS}" "${SINCE}" "${REPO}"
grand=0
TMP="$(mktemp)"; trap 'rm -f "${TMP}"' EXIT
for w in ${DEDUP_CALLERS}; do
  ids="$(gh api --paginate "/repos/${REPO}/actions/workflows/${w}.yml/runs?created=>${SINCE}&per_page=100" \
    --jq '.workflow_runs[].id' 2>/dev/null)"
  if [ -z "${ids}" ]; then printf '%5d  %s (0 runs)\n' 0 "${w}" >> "${TMP}"; continue; fi
  b="$(echo "${ids}" | xargs -P 5 -I{} bash -c 'billed_run "$@"' _ {} 2>/dev/null | awk '{s+=$1} END{print s+0}')"
  printf '%5d  %s\n' "${b}" "${w}" >> "${TMP}"
  grand=$((grand + b))
done
sort -rn "${TMP}"
echo "----"
printf 'DEDUP_BILLED_%sD=%s\n' "${DAYS}" "${grand}"
if [ -n "${LEDGER_POSTS}" ]; then
  # billed_total = non-dedup posts + dedup billed = (LEDGER_POSTS - dedup_posts) + grand.
  # dedup_posts >= 0, so LEDGER_POSTS + grand is an UPPER BOUND — state it as such, never as exact.
  total=$((LEDGER_POSTS + grand))
  printf 'LEDGER_POSTS_%sD=%s  (== billed for every NON-dedup caller)\n' "${DAYS}" "${LEDGER_POSTS}"
  printf 'BILLED_TOTAL_UPPER_BOUND=%s   COST_UPPER_USD=%.2f  (1-min minimum/job @ $%s)\n' \
    "${total}" "$(echo "${total} * ${MINUTE_RATE_USD}" | bc -l)" "${MINUTE_RATE_USD}"
else
  printf '(set LEDGER_POSTS=<slack-ledger posts for the window> for a fleet total + $ figure)\n'
fi
