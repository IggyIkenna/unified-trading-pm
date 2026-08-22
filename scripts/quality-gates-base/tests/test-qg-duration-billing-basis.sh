#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for how `base-service.sh` decides the BILLABLE duration it checks against
# MAX_DURATION. This block has now shipped two defects in a single day (2026-08-10), which is why
# it gets a test rather than another comment:
#
#   1. `times` captured via `$(...)` reports 0m0.000s — the builtin runs in a subshell with its
#      own accounting — so the budget silently became zero and could never trip. Fixed by
#      capturing through REDIRECTION.
#   2. Billing CPU-seconds OUTRIGHT. CPU is contention-invariant, which is what the block was
#      introduced for, but `bats -j N` accrues up to N CPU-seconds per WALL second. PM's suite is
#      ~617s CPU / ~115-200s wall at -j 5..8, so a pure-CPU basis made the 600s cap UNPASSABLE on
#      a quiet host — it charged the gate N× for being parallelised. Fixed to min(CPU, wall-net).
#
# The invariant worth protecting, and the one both bugs broke: **the billed figure may only ever
# be LOWER than wall-net, never higher.** A duration basis that can EXCEED wall-clock invents
# failures that the wall-clock it replaced would not have produced.
#
# Runs the REAL block extracted from the live file (like test-sit-fleet-green-auto-retrigger.sh
# does for its workflow function) — a replica here would drift from the code that actually ships.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-duration-billing-basis.sh
set -uo pipefail

BASE="$(cd "$(dirname "$0")/.." && pwd)/base-service.sh"
PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() {
  echo "FAIL: $*"
  FAIL=$((FAIL + 1))
}

[ -f "$BASE" ] || {
  echo "FAIL: base-service.sh not found at $BASE"
  exit 1
}

# ── (a) structural: the min() comparison must be PRESENT, and the naked assignment ABSENT ──────
BLOCK="$(sed -n '/^if \[ -n "\${DUR_CPU:-}" \]/,/^fi$/p' "$BASE")"
[ -n "$BLOCK" ] || {
  echo "FAIL: could not extract the DUR_CPU billing block (did the guard line change?)"
  exit 1
}

if printf '%s' "$BLOCK" | grep -q 'DUR_CPU" -lt "\$DUR_BILLABLE'; then
  pass "billing block compares CPU against wall-net (min semantics present)"
else
  fail "billing block no longer takes the MINIMUM — a pure-CPU basis re-breaks parallel suites"
fi

# The exact shape of defect 2: an unconditional overwrite with no comparison guarding it.
if printf '%s' "$BLOCK" | grep -qE '^\s*DUR_BILLABLE=\$DUR_CPU;.*$' &&
  ! printf '%s' "$BLOCK" | grep -q '\-lt'; then
  fail "DUR_BILLABLE is assigned from CPU unconditionally (defect 2 reintroduced)"
else
  pass "no unconditional CPU assignment"
fi

# ── (b) functional: run the REAL extracted block against known inputs ───────────────────────────
_billed() { # <cpu> <wall_net> -> billed seconds, via the live code
  local DUR_CPU="$1" DUR_BILLABLE="$2" _qg_dur_basis=""
  eval "$BLOCK"
  printf '%s' "$DUR_BILLABLE"
}

_basis() { # <cpu> <wall_net> -> the basis label the live code chose
  local DUR_CPU="$1" DUR_BILLABLE="$2" _qg_dur_basis=""
  eval "$BLOCK"
  printf '%s' "$_qg_dur_basis"
}

# Descheduled: gate starved by peer load. CPU is the honest figure — this is the whole point of
# the block (measured: PM reported 602s then 611s of "work" against a 600s cap under 11 concurrent
# quickmerges, pure contention surfaced to the agent as a content failure).
got="$(_billed 370 900)"
[ "$got" = "370" ] && pass "starved gate bills CPU (370s), not the 900s wall" ||
  fail "starved gate billed '$got', expected 370"

# Parallel: the 2026-08-10 regression. bats -j 5 burns far more CPU than wall; billing CPU here
# would fail a cap the gate comfortably passes.
got="$(_billed 617 200)"
[ "$got" = "200" ] && pass "parallel gate bills wall-net (200s), not the 617s of CPU" ||
  fail "parallel gate billed '$got', expected 200 — CPU basis punishes parallelism"

# THE invariant, asserted directly across a spread rather than trusting the two cases above.
for pair in "617 776" "370 900" "200 210" "600 601" "50 50" "1 1" "900 100"; do
  set -- $pair
  b="$(_billed "$1" "$2")"
  if [ "$b" -gt "$2" ]; then
    fail "billed ${b}s EXCEEDS wall-net ${2}s (cpu=$1) — invents a failure wall-clock would not"
  fi
done
[ "$FAIL" -eq 0 ] && pass "billed figure never exceeds wall-net across 7 cpu/wall combinations"

# CPU accounting unavailable (defect 1's failure mode): must fall back to wall, NOT to a zero
# budget that disables the cap entirely.
got="$(_billed 0 450)"
[ "$got" = "450" ] && pass "CPU=0 (accounting unavailable) falls back to wall-net, cap stays live" ||
  fail "CPU=0 billed '$got', expected the 450s wall fallback — a 0 budget can never trip"
got="$(_basis 0 450)"
case "$got" in
*"CPU unavailable"*) pass "CPU=0 labels its basis honestly ($got)" ;;
*) fail "CPU=0 basis was '$got' — must say CPU accounting was unavailable" ;;
esac

echo
echo "── $PASS passed, $FAIL failed ──"
[ "$FAIL" -eq 0 ]
