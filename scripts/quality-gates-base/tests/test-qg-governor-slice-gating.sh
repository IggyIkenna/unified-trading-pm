#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Self-test for base-service.sh's governor-acquire gating condition
# (qg_host_governor_severe_contention_2026_07_13.md todo 3).
#
# base-service.sh is a 3700+-line CLI script (not sourceable in isolation like
# qg-host-governor.sh) — this REPLICATES the exact acquire-gating boolean from
# base-service.sh's "HOST CONCURRENCY GOVERNOR: acquire" section and asserts it
# resolves correctly across the QG_SLICE / sentinel-hit / DOCS-ONLY / skip-flag
# matrix, mirroring tests/test-step-5-63-run-lifecycle.sh's replica-matcher
# convention.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-governor-slice-gating.sh
set -euo pipefail

FAILS=0

# Replica of base-service.sh's acquire condition:
#   if [ "$_QG_SENTINEL_HIT" != true ] && { [ "$RUN_TESTS" = true ] || [ "$SKIP_TYPECHECK" != "true" ]; }; then
#       qg_governor_acquire
#   fi
needs_governor() {
    local sentinel_hit="$1" run_tests="$2" skip_typecheck="$3"
    if [ "$sentinel_hit" != true ] && { [ "$run_tests" = true ] || [ "$skip_typecheck" != "true" ]; }; then
        echo true
    else
        echo false
    fi
}

assert_case() {
    local label="$1" sentinel_hit="$2" run_tests="$3" skip_typecheck="$4" expected="$5"
    local actual
    actual="$(needs_governor "$sentinel_hit" "$run_tests" "$skip_typecheck")"
    if [ "$actual" = "$expected" ]; then
        echo "PASS: $label -> needs_governor=$actual"
    else
        echo "FAIL: $label -> expected needs_governor=$expected, got $actual"
        FAILS=$((FAILS + 1))
    fi
}

# ── Full run (QG_SLICE unset): RUN_TESTS=true, SKIP_TYPECHECK=false -> governed ──
assert_case "full run (unset QG_SLICE)" false true false true

# ── QG_SLICE=tests: RUN_TESTS=true, SKIP_TYPECHECK=true -> still governed (TESTS is heavy) ──
assert_case "QG_SLICE=tests" false true true true

# ── QG_SLICE=typecheck: RUN_TESTS=false, SKIP_TYPECHECK=false -> governed (TYPECHECK is heavy) ──
assert_case "QG_SLICE=typecheck" false false false true

# ── QG_SLICE=lint-codex: RUN_TESTS=false, SKIP_TYPECHECK=true -> NOT governed (the bug this fixes) ──
assert_case "QG_SLICE=lint-codex" false false true false

# ── DOCS-ONLY short-circuit (RUN_TESTS=false, SKIP_TYPECHECK=true, any QG_SLICE) -> NOT governed ──
assert_case "DOCS-ONLY changeset" false false true false

# ── --skip-tests + --skip-typecheck together -> NOT governed (nothing heavy runs) ──
assert_case "--skip-tests --skip-typecheck" false false true false

# ── --skip-tests only (SKIP_TYPECHECK still false) -> still governed (TYPECHECK still runs) ──
assert_case "--skip-tests only" false false false true

# ── Green sentinel hit overrides everything -> never governed regardless of RUN_TESTS/SKIP_TYPECHECK ──
assert_case "sentinel hit, would-be full run" true true false false

echo "────────────────────────────────────────"
if [ "$FAILS" -eq 0 ]; then echo "ALL CASES PASSED"; else echo "FAILED CASES: $FAILS"; fi
[ "$FAILS" -eq 0 ]
