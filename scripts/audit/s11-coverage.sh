#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# §11 — Coverage Regression Prevention
# Checks: MIN_COVERAGE calibration, fail_under alignment, cov-fail-under wired.
# Usage: bash unified-trading-pm/scripts/audit/s11-coverage.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$WORKSPACE_ROOT"

echo "=== §11 Coverage Regression Prevention ==="

# Default (uncalibrated) MIN_COVERAGE=70 — should only appear in genuinely low-coverage repos
default_coverage=$(rg 'MIN_COVERAGE=70$' --glob '*/scripts/quality-gates.sh' \
  2>/dev/null | grep -v '# calibrated' || true)
if [ -z "$default_coverage" ]; then
  emit "§11" "MIN_COVERAGE calibrated (not default 70 for high-coverage repos)" "PASS" "none"
else
  count=$(echo "$default_coverage" | wc -l | tr -d ' ')
  emit "§11" "MIN_COVERAGE calibrated (not default 70 for high-coverage repos)" "WARN" \
    "$count repos at default 70 — verify each is actually at ~70% actual coverage"
fi

# check-coverage-alignment.py (fail_under ↔ MIN_COVERAGE match)
if [ -f "unified-trading-pm/scripts/check-coverage-alignment.py" ]; then
  if python3 unified-trading-pm/scripts/check-coverage-alignment.py > /tmp/cov-align.txt 2>&1; then
    emit "§11" "fail_under matches MIN_COVERAGE per repo" "PASS" "check-coverage-alignment.py passed"
  else
    issues=$(head -5 /tmp/cov-align.txt | tr '\n' '; ')
    emit "§11" "fail_under matches MIN_COVERAGE per repo" "WARN" "$issues"
  fi
else
  emit "§11" "fail_under matches MIN_COVERAGE per repo" "WARN" \
    "check-coverage-alignment.py not found — manual check required"
fi

# --cov-fail-under wired in base-service.sh
if grep -q 'cov-fail-under' unified-trading-pm/scripts/quality-gates-base/base-service.sh 2>/dev/null; then
  emit "§11" "--cov-fail-under wired in base-service.sh" "PASS" "none"
else
  emit "§11" "--cov-fail-under wired in base-service.sh" "FAIL" \
    "not found in base-service.sh — coverage floor not enforced at pytest level"
fi

audit_summary
