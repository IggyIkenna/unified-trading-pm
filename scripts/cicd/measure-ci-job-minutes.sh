#!/usr/bin/env bash
# Epic: ci_master
# Lifecycle: RECURRING — this answer has a DATE on it; re-run, never cite an old number.
# Delete-when: the CI-VM sizing/cost question in
#   /plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md
#   is closed AND the fleet's runner topology has stopped changing.
#
# ── WHY THIS EXISTS ───────────────────────────────────────────────────────────
# Sizing/keeping the self-hosted CI VM is a cost decision, and the only honest
# input is "how many job-minutes does the fleet actually consume". GitHub's
# billing REST API (`/users/{u}/settings/billing/actions`) is NOT usable here:
# the org is a User account and a normal PAT gets 403 (verified 2026-08-06).
# So we measure from run/job timestamps instead, which needs no billing scope.
#
# ── WHAT IT MEASURES (and what it does NOT) ───────────────────────────────────
#   * VOLUME, in job-minutes, per repo, over a window.
#   * NOT cost. Jobs on self-hosted runners are billed $0. Jobs in PUBLIC repos
#     are billed $0 too (GitHub Actions is free + UNLIMITED on standard hosted
#     runners for public repos). Only PRIVATE + GitHub-hosted actually costs
#     money (~$0.008/min Linux 2-core). Interpret accordingly — a big number
#     here on a public or self-hosted repo is a CAPACITY signal, not a bill.
#
# ── TRAPS HIT BUILDING THIS (do not re-learn these) ───────────────────────────
#  1. GitHub bills each JOB rounded UP to the whole minute — not the run, and
#     not the sum-then-round. A repo with many short jobs (matrix legs) costs
#     far more than its wall-clock suggests. We replicate per-job ceil() here.
#  2. `gh run list --limit N` defaults small; the window filter must be applied
#     AFTER a large enough --limit or you silently truncate a busy repo.
#  3. Jobs still running have completed_at=null -> the date arithmetic yields
#     garbage. They are filtered out, so an in-flight window UNDER-reports.
#  4. Sequential `gh api` per run is slow (minutes for a busy repo). Run this
#     backgrounded, or narrow the window. Do NOT foreground it in an agent turn
#     -- it will hit the 2-minute Bash timeout (learned the hard way).
#  5. Numbers measured BEFORE 2026-08-06 are inflated by the `actions/cache`
#     uv-cache step, which cost 335-894s/job on self-hosted before it was gated
#     off (unified-trading-pm@9b39f6a05). Do not compare across that boundary.
#
# Usage:  bash scripts/cicd/measure-ci-job-minutes.sh [ISO8601_SINCE] [repo ...]
# e.g.    bash scripts/cicd/measure-ci-job-minutes.sh 2026-08-05T07:00:00Z
set -uo pipefail

SINCE="${1:-$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)}"
shift 2>/dev/null || true
OWNER="${GH_OWNER:-IggyIkenna}"

if [ "$#" -gt 0 ]; then
    REPOS=("$@")
else
    # Default: the repos that can actually cost money or capacity -- private ones.
    REPOS=(agent-orchestrator e2e-testing execution-service features-service
           market-tick-data-service ml-service strategy-service)
fi

command -v gh >/dev/null || { echo "gh CLI required" >&2; exit 1; }

printf '%-32s %7s %7s %10s %10s\n' "repo" "runs" "jobs" "min/window" "vis"
TOTAL=0
for R in "${REPOS[@]}"; do
    VIS=$(gh api "repos/${OWNER}/${R}" --jq '.visibility' 2>/dev/null || echo "?")
    IDS=$(gh run list --repo "${OWNER}/${R}" --limit 200 --json databaseId,createdAt \
            --jq "[.[]|select(.createdAt>\"${SINCE}\")]|.[].databaseId" 2>/dev/null)
    NR=$(printf '%s' "$IDS" | grep -c . || true)
    NJ=0; MIN=0
    for ID in $IDS; do
        # completed_at=null (in-flight) is filtered -> an open window under-reports.
        DUR=$(gh api "repos/${OWNER}/${R}/actions/runs/${ID}/jobs" \
              --jq '.jobs[]|select(.completed_at!=null)|((.completed_at|fromdate)-(.started_at|fromdate))' 2>/dev/null)
        for S in $DUR; do
            NJ=$((NJ + 1))
            M=$(( (${S%.*} + 59) / 60 ))   # GitHub bills per JOB, rounded UP
            [ "$M" -lt 1 ] && M=1
            MIN=$((MIN + M))
        done
    done
    printf '%-32s %7s %7s %10s %10s\n' "$R" "$NR" "$NJ" "$MIN" "$VIS"
    TOTAL=$((TOTAL + MIN))
done
echo "----"
echo "TOTAL job-minutes in window since ${SINCE}: ${TOTAL}"
echo "NOTE: volume, not cost. public repos = free+unlimited; self-hosted = \$0."
