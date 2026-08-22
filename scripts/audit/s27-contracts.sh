#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# §27 — Contract Completeness & Adoption Verification
# Runs: check_uic_adoption.py, check_uac_adoption.py, check_utl_adoption.py
# Usage: bash unified-trading-pm/scripts/audit/s27-contracts.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$WORKSPACE_ROOT"

echo "=== §27 Contract Adoption ==="

_TMP=$(mktemp -d)
trap 'rm -rf "$_TMP"' EXIT

run_checker_bg() {
  local section="$1" criterion="$2" script="$3" key="$4"
  local out="$_TMP/${key}.out" rc="$_TMP/${key}.rc"
  (
    if [ ! -f "$script" ]; then
      echo "WARN|checker not found: $script" > "$out"
    elif python3 "$script" > "$_TMP/${key}.log" 2>&1; then
      echo "PASS|$(tail -1 "$_TMP/${key}.log")" > "$out"
    else
      issues=$(grep -i 'fail\|error\|missing\|orphan' "$_TMP/${key}.log" | head -3 | tr '\n' '; ')
      echo "WARN|${issues:-see log}" > "$out"
    fi
  ) &
}

# Launch all 3 checkers in parallel
run_checker_bg "§27" "UIC adoption (check_uic_adoption.py)" \
  "system-integration-tests/tests/adoption/check_uic_adoption.py" "uic"
run_checker_bg "§27" "UAC adoption (check_uac_adoption.py)" \
  "system-integration-tests/tests/adoption/check_uac_adoption.py" "uac"
run_checker_bg "§27" "UTL adoption (check_utl_adoption.py)" \
  "system-integration-tests/tests/adoption/check_utl_adoption.py" "utl"

# Wait for all 3 to complete, then emit in canonical order
wait
for pair in "uic|UIC adoption (check_uic_adoption.py)" \
            "uac|UAC adoption (check_uac_adoption.py)" \
            "utl|UTL adoption (check_utl_adoption.py)"; do
  key="${pair%%|*}"; criterion="${pair##*|}"
  out="$_TMP/${key}.out"
  if [ -f "$out" ]; then
    IFS='|' read -r status evidence < "$out"
    emit "§27" "$criterion" "$status" "$evidence"
  else
    emit "§27" "$criterion" "WARN" "checker did not complete"
  fi
done

# VCR cassette counts per interface repo (§10 overlap)
echo ""
echo "  VCR cassette counts per interface repo:"
for repo in unified-market-interface unified-reference-data-interface \
            unified-cloud-interface execution-service \
            position-balance-monitor-service; do
  count=$(find "$repo" -name '*.yaml' -path '*/mocks/*' 2>/dev/null | wc -l | tr -d ' ')
  if [ "$count" -eq 0 ]; then
    emit "§27" "VCR cassettes: $repo" "FAIL" "0 cassettes"
  else
    emit "§27" "VCR cassettes: $repo" "PASS" "$count cassettes"
  fi
done

audit_summary
