#!/usr/bin/env bash
# Epic: infrastructure_master (ci_satellite_ao_dispatch_batch1_2026_07_26)
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for the LDR->main fleet promoter's auto-merge ARM_FAILED tally fix
# (plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md [CI] P1 -- MTDS auto-merge-arm
# investigation, 2026-08-02; source: plans/archive/issues/
# ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md).
#
# Bug: all 3 `gh pr merge --auto` arm-call sites in process_repo()
# (scripts/cicd/ldr_to_main_fleet_promote.sh) called `_done PROMOTED` UNCONDITIONALLY after
# the arm attempt, regardless of whether the arm itself succeeded or failed -- so a repo
# whose auto-merge never actually got armed (needs a manual `gh pr merge`) was silently
# counted identically to a genuinely-armed one in the run's Promoted/Blocked/Conflicted
# tally + Slack summary. The close+reopen re-arm site was worse: it swallowed the arm
# call's exit code entirely (`2>/dev/null || true`), so a failure there wasn't even logged.
#
# Fix (2026-08-02): each of the 3 arm sites now branches on the arm call's own exit status
# -- `_done PROMOTED` only on a confirmed-armed success, `_done ARM_FAILED` (a new 4th
# terminal state, tallied separately and surfaced via a dedicated Slack notify job) on
# failure.
#
# Like test-ldr-promote-provenance-rearm-gate.sh, this EXTRACTS the REAL code (not a
# replica) and:
#   (a) structurally asserts all 3 arm-call sites branch (none unconditionally tallies
#       PROMOTED after the arm attempt), and that ARM_FAILED is wired through the
#       aggregation case statement + GITHUB_OUTPUT + job outputs + a Slack notify job;
#   (b) functionally runs the REAL aggregation/tally block (extracted verbatim) against a
#       synthetic RESULT_DIR, proving an ARM_FAILED repo lands in arm_failed_count and its
#       repo list, NOT in promoted_count.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-ldr-promote-arm-failed-tally.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PROMOTE_SCRIPT="$REPO_ROOT/scripts/cicd/ldr_to_main_fleet_promote.sh"
WORKFLOW_YML="$REPO_ROOT/.github/workflows/ldr-to-main-promote-fleet.yml"
[ -f "$PROMOTE_SCRIPT" ] || { echo "FATAL: ldr_to_main_fleet_promote.sh not found at $PROMOTE_SCRIPT"; exit 2; }
[ -f "$WORKFLOW_YML" ] || { echo "FATAL: ldr-to-main-promote-fleet.yml not found at $WORKFLOW_YML"; exit 2; }

echo "── Structural: all 3 arm-call sites branch on their own exit status ──"
ARM_SITES=$(grep -c -- '--auto --squash --delete-branch' "$PROMOTE_SCRIPT" || true)
if [ "${ARM_SITES:-0}" -eq 3 ]; then
  pass "structural: exactly 3 auto-merge arm-call sites found (creation + close-reopen re-arm + clean-state re-arm)"
else
  fail "structural: expected 3 arm-call sites, found ${ARM_SITES:-0}"
fi

PROMOTED_SITES=$(grep -c '_done PROMOTED$' "$PROMOTE_SCRIPT" || true)
ARM_FAILED_SITES=$(grep -c '_done ARM_FAILED$' "$PROMOTE_SCRIPT" || true)
if [ "${PROMOTED_SITES:-0}" -eq 3 ] && [ "${ARM_FAILED_SITES:-0}" -eq 3 ]; then
  pass "structural: 3 conditional _done PROMOTED sites + 3 matching _done ARM_FAILED sites (one if/else pair per arm site — none unconditional)"
else
  fail "structural: expected 3 PROMOTED + 3 ARM_FAILED conditional sites, found ${PROMOTED_SITES:-0} PROMOTED / ${ARM_FAILED_SITES:-0} ARM_FAILED"
fi

# Regression guard for the specific close+reopen swallow bug: that site must no longer
# discard the arm call's own exit code via `2>/dev/null || true`.
if grep -A4 'close+reopen re-arm' "$PROMOTE_SCRIPT" | grep -q '2>/dev/null || true'; then
  fail "regression: close+reopen re-arm site still swallows its exit code (2>/dev/null || true)"
else
  pass "regression: close+reopen re-arm site no longer swallows its exit code"
fi

echo "── Structural: ARM_FAILED is wired into aggregation + GITHUB_OUTPUT + job outputs + Slack ──"
if grep -q 'ARM_FAILED) ARM_FAILED=' "$PROMOTE_SCRIPT"; then
  pass "structural: aggregation case statement handles ARM_FAILED"
else
  fail "structural: aggregation case statement does not handle ARM_FAILED"
fi
if grep -q 'echo "arm_failed_count=\$ARM_FAILED_COUNT"' "$PROMOTE_SCRIPT"; then
  pass "structural: arm_failed_count is written to GITHUB_OUTPUT"
else
  fail "structural: arm_failed_count is NOT written to GITHUB_OUTPUT"
fi
if grep -q 'arm_failed_count: \${{ steps.promote.outputs.arm_failed_count }}' "$WORKFLOW_YML"; then
  pass "structural: job outputs.arm_failed_count is wired from the step output"
else
  fail "structural: job outputs.arm_failed_count is NOT wired from the step output"
fi
if grep -q '^  notify-arm-failed:' "$WORKFLOW_YML" && grep -q 'arm_failed_count != .0.' "$WORKFLOW_YML"; then
  pass "structural: a dedicated Slack notify job exists, gated on arm_failed_count"
else
  fail "structural: no dedicated Slack notify job gated on arm_failed_count"
fi

echo "── Functional: extracted aggregation block correctly separates ARM_FAILED from PROMOTED ──"
# Extract the REAL barrier/aggregate block verbatim (between the barrier comment and the
# GITHUB_OUTPUT write) and run it against a synthetic RESULT_DIR — proves the actual
# shipped case statement + output-write, not a hand-written replica of it.
AGG=$(awk '
  /^# ── Barrier: replay logs in topo order \+ aggregate/ { c = 1 }
  c { print }
  /^\} >> "\$GITHUB_OUTPUT"$/ { if (c) exit }
' "$PROMOTE_SCRIPT")
[ -n "$AGG" ] || { echo "FATAL: could not extract the aggregation block"; exit 2; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

run_aggregation() {
  local result_dir="$1" log_dir="$2" repos="$3" out_file="$4"
  (
    RESULT_DIR="$result_dir"; LOG_DIR="$log_dir"; REPOS="$repos"; GITHUB_OUTPUT="$out_file"
    eval "$AGG"
  )
}

echo "── Case 1: one of each terminal state — ARM_FAILED must not inflate promoted_count ──"
RESULT_DIR="$WORK/results1"; LOG_DIR="$WORK/logs1"
mkdir -p "$RESULT_DIR" "$LOG_DIR"
echo "PROMOTED"   > "$RESULT_DIR/repo-a"
echo "ARM_FAILED" > "$RESULT_DIR/repo-b"
echo "BLOCKED"    > "$RESULT_DIR/repo-c"
echo "CONFLICTED" > "$RESULT_DIR/repo-d"
: > "$LOG_DIR/repo-a.log"; : > "$LOG_DIR/repo-b.log"; : > "$LOG_DIR/repo-c.log"; : > "$LOG_DIR/repo-d.log"
OUT1="$WORK/gh_output1.txt"; : > "$OUT1"
run_aggregation "$RESULT_DIR" "$LOG_DIR" $'repo-a\nrepo-b\nrepo-c\nrepo-d' "$OUT1"

if grep -qx 'promoted_count=1' "$OUT1" && grep -qx 'arm_failed_count=1' "$OUT1" \
   && grep -qx 'blocked_count=1' "$OUT1" && grep -qx 'conflicted_count=1' "$OUT1" \
   && grep -q '^promoted= *repo-a$' "$OUT1" && grep -q '^arm_failed= *repo-b$' "$OUT1"; then
  pass "functional: PROMOTED/ARM_FAILED/BLOCKED/CONFLICTED tallied into 4 distinct counts — repo-b (ARM_FAILED) does NOT inflate promoted_count"
else
  fail "functional: case1 aggregation output did not match expected tally"; cat "$OUT1"
fi

echo "── Case 2 (THE regression this closes): if ARM_FAILED were mis-tallied as PROMOTED, this would show promoted_count=2 ──"
# Sanity-check the discriminating power of case 1: an all-PROMOTED run (i.e. the pre-fix
# behavior for what is really repo-a + repo-b) WOULD show promoted_count=2 — confirming the
# assertion above is actually exercising the ARM_FAILED-vs-PROMOTED distinction, not a
# vacuously-true count.
RESULT_DIR2="$WORK/results2"; LOG_DIR2="$WORK/logs2"
mkdir -p "$RESULT_DIR2" "$LOG_DIR2"
echo "PROMOTED" > "$RESULT_DIR2/repo-a"
echo "PROMOTED" > "$RESULT_DIR2/repo-b"
: > "$LOG_DIR2/repo-a.log"; : > "$LOG_DIR2/repo-b.log"
OUT2="$WORK/gh_output2.txt"; : > "$OUT2"
run_aggregation "$RESULT_DIR2" "$LOG_DIR2" $'repo-a\nrepo-b' "$OUT2"
if grep -qx 'promoted_count=2' "$OUT2"; then
  pass "sanity: the same extracted block DOES report promoted_count=2 when both repos are genuinely PROMOTED (confirms case1 isn't vacuous)"
else
  fail "sanity: expected promoted_count=2 for two genuinely-PROMOTED repos"; cat "$OUT2"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
