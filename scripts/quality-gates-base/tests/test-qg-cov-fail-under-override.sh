#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Self-test for base-service.sh's COV_FAIL_UNDER_OVERRIDE opt-in hook
# (test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md, MDPS promotion).
#
# base-service.sh is a 3700+-line CLI script (not sourceable in isolation) — this
# REPLICATES the exact COV-building conditional from its "[3] TESTS" section and
# asserts it resolves correctly across the QUICK_MODE / override-set matrix,
# mirroring test-qg-governor-slice-gating.sh's replica-matcher convention.
#
# Real end-to-end verification (not just this replica) was also run manually against
# market-data-processing-service: a narrowed PYTEST_UNIT_DIR without the override
# genuinely fails coverage (15.05% < fail_under=85), and passes with the override set
# — see test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md Progress Log.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-cov-fail-under-override.sh
set -euo pipefail

FAILS=0

# Replica of base-service.sh's COV-building conditional:
#   if [ "$QUICK_MODE" = true ]; then
#       COV=""
#   else
#       COV="--cov=$SOURCE_DIR --cov-report=xml:coverage.xml"
#       if [ -n "${COV_FAIL_UNDER_OVERRIDE:-}" ]; then
#           COV="$COV --cov-fail-under=${COV_FAIL_UNDER_OVERRIDE}"
#       fi
#   fi
build_cov() {
    local quick_mode="$1" override="$2" source_dir="market_data_processing_service"
    local cov
    if [ "$quick_mode" = true ]; then
        cov=""
    else
        cov="--cov=$source_dir --cov-report=xml:coverage.xml"
        if [ -n "$override" ]; then
            cov="$cov --cov-fail-under=${override}"
        fi
    fi
    echo "$cov"
}

assert_case() {
    local label="$1" quick_mode="$2" override="$3" expected="$4"
    local actual
    actual="$(build_cov "$quick_mode" "$override")"
    if [ "$actual" = "$expected" ]; then
        echo "PASS: $label -> COV=[$actual]"
    else
        echo "FAIL: $label -> expected COV=[$expected], got COV=[$actual]"
        FAILS=$((FAILS + 1))
    fi
}

# ── Default full-suite run (no override set, the ~24-other-repo case) — UNCHANGED ──
assert_case "full run, no override" false "" \
    "--cov=market_data_processing_service --cov-report=xml:coverage.xml"

# ── QUICK_MODE — coverage is skipped entirely regardless of override (unchanged) ──
assert_case "QUICK_MODE, no override" true "" ""
assert_case "QUICK_MODE, override set (still ignored — quick mode wins)" true "0" ""

# ── Narrowed run (MDPS test-impact gate fired) — floor explicitly relaxed ──
assert_case "narrowed run, override=0" false "0" \
    "--cov=market_data_processing_service --cov-report=xml:coverage.xml --cov-fail-under=0"

# ── Override can be set to any explicit floor, not just 0 (e.g. a future narrower ask) ──
assert_case "narrowed run, override=50" false "50" \
    "--cov=market_data_processing_service --cov-report=xml:coverage.xml --cov-fail-under=50"

echo "────────────────────────────────────────"
if [ "$FAILS" -eq 0 ]; then echo "ALL CASES PASSED"; else echo "FAILED CASES: $FAILS"; fi
[ "$FAILS" -eq 0 ]
