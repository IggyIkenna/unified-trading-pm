#!/usr/bin/env bash
# Epic: infrastructure_master (ci_satellite_ao_dispatch_batch15_2026_08_16)
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for the LDR->main fleet promoter's per-repo fan-out stagger
# (plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md [INFRA] P2 — "Stagger
# ldr-to-main-promote-fleet.yml's per-repo fan-out rather than firing all repos
# simultaneously on each tick").
#
# Bug/gap: the bounded-parallel driver at the bottom of
# scripts/cicd/ldr_to_main_fleet_promote.sh backgrounded `process_repo "$REPO"` for every
# repo in $REPOS back-to-back with ZERO delay between launches — only throttled once
# MAXJOBS (6) were already in flight via the `wait -n` barrier. That let the first MAXJOBS
# repos' subshells all hit their earliest gh api calls / the SIT_DISPATCH_LOCK mkdir race
# within the same instant (the shape behind the 2026-08-06 "3 full-workspace-sit dispatches
# within ~10s" stampede documented inline above the driver).
#
# Fix (2026-08-17): a small STAGGER_SECONDS delay (env-overridable via
# LDR_MAIN_PROMOTE_STAGGER_SECONDS, default 3) runs after each background launch, before the
# MAXJOBS throttle check — so successive repo launches are spread out in real time instead of
# firing as fast as the shell can fork.
#
# Like its sibling tests in this directory, this EXTRACTS the REAL driver loop (not a
# replica) and:
#   (a) structurally asserts the driver declares a STAGGER_SECONDS var wired to an
#       overridable env default, and calls `sleep "$STAGGER_SECONDS"` between the background
#       launch and the MAXJOBS wait;
#   (b) functionally runs the REAL driver loop (extracted verbatim, with a stub
#       `process_repo` that just timestamps its own start) against a synthetic $REPOS list,
#       proving successive launches are measurably spaced apart by >= STAGGER_SECONDS, and
#       that STAGGER_SECONDS=0 reproduces the old zero-delay behavior (no regression risk for
#       local/CI testing that wants the fast path).
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-ldr-promote-fanout-stagger.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PROMOTE_SCRIPT="$REPO_ROOT/scripts/cicd/ldr_to_main_fleet_promote.sh"
[ -f "$PROMOTE_SCRIPT" ] || { echo "FATAL: ldr_to_main_fleet_promote.sh not found at $PROMOTE_SCRIPT"; exit 2; }

echo "── Structural: driver declares an overridable STAGGER_SECONDS and sleeps on it ──"
if grep -q 'STAGGER_SECONDS="\${LDR_MAIN_PROMOTE_STAGGER_SECONDS:-3}"' "$PROMOTE_SCRIPT"; then
  pass "structural: STAGGER_SECONDS is env-overridable (LDR_MAIN_PROMOTE_STAGGER_SECONDS), default 3"
else
  fail "structural: expected STAGGER_SECONDS=\"\${LDR_MAIN_PROMOTE_STAGGER_SECONDS:-3}\" declaration not found"
fi

if grep -q 'sleep "\$STAGGER_SECONDS"' "$PROMOTE_SCRIPT"; then
  pass "structural: driver loop calls sleep \"\$STAGGER_SECONDS\""
else
  fail "structural: expected a sleep \"\$STAGGER_SECONDS\" call in the driver loop"
fi

# The sleep must sit BETWEEN the background launch and the MAXJOBS wait -n barrier — a sleep
# placed anywhere else (e.g. after the barrier) would stagger job COMPLETION, not job START.
DRIVER_BLOCK=$(sed -n '/# ── Bounded-parallel driver/,/^wait 2>\/dev\/null || true$/p' "$PROMOTE_SCRIPT")
if printf '%s\n' "$DRIVER_BLOCK" | grep -qE 'process_repo "\$REPO".*&$' \
   && printf '%s\n' "$DRIVER_BLOCK" | grep -A1 'process_repo "\$REPO"' | grep -q 'sleep "\$STAGGER_SECONDS"'; then
  pass "structural: sleep immediately follows the background launch (staggers START, not completion)"
else
  fail "structural: sleep is not positioned immediately after the background launch"
fi

echo ""
echo "── Functional: successive launches are measurably spaced by >= STAGGER_SECONDS ──"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

run_driver() {
  # Extract the real driver loop verbatim and eval it against a stub process_repo that just
  # records its own launch time (epoch millis) — proves the REAL loop's timing behavior, not
  # a hand-written replica of it.
  local repos="$1" stagger="$2"
  local timestamps_file="$WORK_DIR/timestamps_$stagger"
  : > "$timestamps_file"

  # shellcheck disable=SC2317  # invoked indirectly via the extracted driver block below
  process_repo() {
    date +%s%3N >> "$timestamps_file"
  }

  RESULT_DIR="$WORK_DIR/results_$stagger"; LOG_DIR="$WORK_DIR/logs_$stagger"
  mkdir -p "$RESULT_DIR" "$LOG_DIR"
  MAXJOBS=6
  STAGGER_SECONDS="$stagger"
  REPOS="$repos"

  eval "$(sed -n '/# ── Bounded-parallel driver/,/^wait 2>\/dev\/null || true$/p' "$PROMOTE_SCRIPT")"
  printf '%s' "$timestamps_file"
}

FAKE_REPOS=$'repo-a\nrepo-b\nrepo-c\nrepo-d'

TS_FILE_1=$(run_driver "$FAKE_REPOS" 1)
LINES=$(wc -l < "$TS_FILE_1")
if [ "$LINES" -eq 4 ]; then
  pass "functional: all 4 stub process_repo launches recorded (stagger=1s)"
else
  fail "functional: expected 4 launch timestamps, got $LINES"
fi

# Compute min gap between consecutive sorted timestamps (ms). With STAGGER_SECONDS=1 every
# gap should be >= ~900ms (allowing scheduling jitter below the full 1000ms).
MIN_GAP=$(sort -n "$TS_FILE_1" | awk 'NR>1{d=$1-prev; if (min=="" || d<min) min=d} {prev=$1} END{print min+0}')
if [ "${MIN_GAP:-0}" -ge 900 ]; then
  pass "functional: min inter-launch gap ${MIN_GAP}ms >= ~900ms with STAGGER_SECONDS=1 (measurably staggered)"
else
  fail "functional: min inter-launch gap ${MIN_GAP}ms is below the expected ~1000ms stagger"
fi

# STAGGER_SECONDS=0 must reproduce the old fast/zero-delay behavior (no regression for
# local/CI callers that opt out via LDR_MAIN_PROMOTE_STAGGER_SECONDS=0).
START_MS=$(date +%s%3N)
TS_FILE_0=$(run_driver "$FAKE_REPOS" 0)
END_MS=$(date +%s%3N)
ELAPSED=$((END_MS - START_MS))
LINES_0=$(wc -l < "$TS_FILE_0")
if [ "$LINES_0" -eq 4 ] && [ "$ELAPSED" -lt 900 ]; then
  pass "functional: STAGGER_SECONDS=0 completes all 4 launches in ${ELAPSED}ms (< 900ms — no forced delay)"
else
  fail "functional: STAGGER_SECONDS=0 took ${ELAPSED}ms / recorded $LINES_0 launches — expected near-instant completion (opt-out path)"
fi

echo ""
echo "── Summary: $PASS passed, $FAIL failed ──"
[ "$FAIL" -eq 0 ]
