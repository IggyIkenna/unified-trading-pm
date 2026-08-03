#!/usr/bin/env bash
# Epic: infrastructure_master (ci_satellite_ao_dispatch_batch1_2026_07_26)
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for the PM-standalone LDR->main promoter's auto-merge ARM_FAILED tally fix
# (plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md [CI] P1 -- "Mirror the batch1-036
# auto-merge-arm-failure fix to the sibling standalone ldr-to-main-promote.yml", 2026-08-03).
#
# Bug: `.github/workflows/ldr-to-main-promote.yml` (the PM-only standalone promoter -- distinct
# from the fleet bot at ldr-to-main-promote-fleet.yml, which was already fixed by
# unified-trading-pm@4bf65b67c) had the IDENTICAL silent-swallow defect at its own 4
# `gh pr merge --auto` arm-call sites: each either discarded the call's exit status entirely
# (`2>/dev/null || true`) or only echoed a WARN without tallying anywhere a human/Slack would
# see it. Review agt-39a53d confirmed this failing LIVE (gh run view 30774619258: "WARN:
# auto-merge unavailable", PR #2061 left open/UNSTABLE, zero alert).
#
# Fix (2026-08-03): each of the 4 sites (new-PR arm, routine per-tick re-arm, close+reopen
# recovery re-arm, post-dirty-reconcile re-arm) now branches on the arm call's own exit status,
# tallying an `arm_failed` step/job output (wired through GITHUB_OUTPUT at every exit point) and
# firing a dedicated `notify-arm-failed` Slack job -- mirroring the fleet bot's ARM_FAILED
# terminal-state design (this workflow is single-repo/per-tick, so a boolean flag is the
# equivalent of the fleet's per-repo tally: ARM_FAILED tracks the outcome of the LAST arm
# attempt made this run, since a later successful re-arm supersedes an earlier failure).
#
# Like test-ldr-promote-arm-failed-tally.sh, this:
#   (a) structurally asserts all 4 arm-call sites branch (none unconditionally swallows), and
#       that arm_failed is wired through step output + job output + a Slack notify job;
#   (b) functionally EXTRACTS one real arm-site if/else block verbatim from the shipped
#       workflow file and evals it against a stubbed `gh`, proving a failing arm call sets
#       ARM_FAILED=true and a succeeding one sets ARM_FAILED=false -- not a hand-written replica.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-ldr-promote-standalone-arm-failed-tally.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
WORKFLOW_YML="$REPO_ROOT/.github/workflows/ldr-to-main-promote.yml"
[ -f "$WORKFLOW_YML" ] || { echo "FATAL: ldr-to-main-promote.yml not found at $WORKFLOW_YML"; exit 2; }

echo "── Structural: exactly 4 auto-merge arm-call sites, all conditional ──"
ARM_CALL_SITES=$(grep -c -- '--auto --merge --delete-branch' "$WORKFLOW_YML" || true)
if [ "${ARM_CALL_SITES:-0}" -eq 4 ]; then
  pass "structural: exactly 4 arm-call sites found (new-PR / routine re-arm / close+reopen re-arm / post-dirty-reconcile re-arm)"
else
  fail "structural: expected 4 arm-call sites, found ${ARM_CALL_SITES:-0}"
fi

# Regression guard: none of the 4 sites may unconditionally swallow the arm call's exit code
# via a bare `2>/dev/null || true` / `|| echo ...` immediately after it (the pre-fix shape).
UNCONDITIONAL_SWALLOWS=$(grep -c -- '--auto --merge --delete-branch --repo "\$OWNER/\$REPO" 2>/dev/null || true$' "$WORKFLOW_YML" || true)
if [ "${UNCONDITIONAL_SWALLOWS:-0}" -eq 0 ]; then
  pass "regression: no arm-call site unconditionally swallows its exit code (2>/dev/null || true) anymore"
else
  fail "regression: ${UNCONDITIONAL_SWALLOWS:-0} arm-call site(s) still swallow their exit code unconditionally"
fi

ARM_TRUE_SITES=$(grep -c 'ARM_FAILED="true"' "$WORKFLOW_YML" || true)
if [ "${ARM_TRUE_SITES:-0}" -eq 4 ]; then
  pass "structural: all 4 sites set ARM_FAILED=\"true\" on their own failure branch"
else
  fail "structural: expected 4 sites setting ARM_FAILED=\"true\", found ${ARM_TRUE_SITES:-0}"
fi

echo "── Structural: arm_failed is wired into GITHUB_OUTPUT + job outputs + Slack ──"
ARM_OUTPUT_WRITES=$(grep -c 'echo "arm_failed=\$ARM_FAILED"' "$WORKFLOW_YML" || true)
if [ "${ARM_OUTPUT_WRITES:-0}" -ge 9 ]; then
  pass "structural: arm_failed is written to GITHUB_OUTPUT at every exit point (${ARM_OUTPUT_WRITES} sites)"
else
  fail "structural: arm_failed GITHUB_OUTPUT write is missing at one or more exit points (found ${ARM_OUTPUT_WRITES:-0}, expected >=9)"
fi
if grep -q 'arm_failed: ${{ steps.promote.outputs.arm_failed }}' "$WORKFLOW_YML"; then
  pass "structural: job outputs.arm_failed is wired from the step output"
else
  fail "structural: job outputs.arm_failed is NOT wired from the step output"
fi
if grep -q '^  notify-arm-failed:' "$WORKFLOW_YML" && grep -q "needs.promote-ldr-to-main.outputs.arm_failed == 'true'" "$WORKFLOW_YML"; then
  pass "structural: a dedicated Slack notify job exists, gated on arm_failed == 'true'"
else
  fail "structural: no dedicated Slack notify job gated on arm_failed"
fi

echo "── Functional: extracted real arm-site if/else block correctly branches on exit status ──"
# Extract the routine per-tick re-arm site (the simplest self-contained if/then/else/fi block,
# depending only on PR_NUM/GH_PAT_FOR_ARM/OWNER/REPO -- no PR_URL/reconcile state needed)
# verbatim from the shipped workflow, between its unique lead-in comment and its closing `fi`.
SNIPPET=$(awk '
  /this routine per-tick re-arm attempt used to/ { c = 1; next }
  c && /^          if GH_TOKEN=/ { p = 1 }
  p { print }
  p && /^          fi$/ { exit }
' "$WORKFLOW_YML")
[ -n "$SNIPPET" ] || { echo "FATAL: could not extract the routine re-arm if/else block"; exit 2; }
if ! printf '%s\n' "$SNIPPET" | grep -q 'ARM_FAILED="false"'; then
  echo "FATAL: extracted snippet missing expected success branch -- extraction markers drifted"
  printf '%s\n' "$SNIPPET"
  exit 2
fi

run_snippet() {
  local gh_exit="$1"
  (
    PR_NUM="1234"; OWNER="IggyIkenna"; REPO="unified-trading-pm"; GH_PAT_FOR_ARM="dummy-token"
    ARM_FAILED="unset"
    # shellcheck disable=SC2317  # invoked indirectly via the extracted snippet's `gh pr merge` call
    gh() { return "$gh_exit"; }
    eval "$SNIPPET" >/dev/null 2>&1
    echo "$ARM_FAILED"
  )
}

RESULT_SUCCESS=$(run_snippet 0)
if [ "$RESULT_SUCCESS" = "false" ]; then
  pass "functional: a succeeding arm call (gh exit 0) sets ARM_FAILED=false"
else
  fail "functional: expected ARM_FAILED=false on a succeeding arm call, got '$RESULT_SUCCESS'"
fi

RESULT_FAILURE=$(run_snippet 1)
if [ "$RESULT_FAILURE" = "true" ]; then
  pass "functional: a failing arm call (gh exit 1) sets ARM_FAILED=true, not silently swallowed"
else
  fail "functional: expected ARM_FAILED=true on a failing arm call, got '$RESULT_FAILURE'"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
