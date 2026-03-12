#!/bin/bash
# §27 — Contract Completeness & Adoption Verification
# Runs: check_uic_adoption.py, check_uac_adoption.py, check_utl_adoption.py
# Usage: bash unified-trading-pm/scripts/audit/s27-contracts.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$WORKSPACE_ROOT"

echo "=== §27 Contract Adoption ==="

run_checker() {
  local section="$1" criterion="$2" script="$3"
  if [ ! -f "$script" ]; then
    emit "$section" "$criterion" "WARN" "checker not found: $script"
    return
  fi
  if python3 "$script" > /tmp/contract-check.txt 2>&1; then
    emit "$section" "$criterion" "PASS" "$(tail -1 /tmp/contract-check.txt)"
  else
    issues=$(grep -i 'fail\|error\|missing\|orphan' /tmp/contract-check.txt | head -3 | tr '\n' '; ')
    emit "$section" "$criterion" "WARN" "${issues:-see /tmp/contract-check.txt}"
  fi
}

run_checker "§27" "UIC adoption (check_uic_adoption.py)" \
  "system-integration-tests/tests/adoption/check_uic_adoption.py"

run_checker "§27" "UAC adoption (check_uac_adoption.py)" \
  "system-integration-tests/tests/adoption/check_uac_adoption.py"

run_checker "§27" "UTL adoption (check_utl_adoption.py)" \
  "system-integration-tests/tests/adoption/check_utl_adoption.py"

# VCR cassette counts per interface repo (§10 overlap)
echo ""
echo "  VCR cassette counts per interface repo:"
for repo in unified-market-interface unified-trade-execution-interface \
            unified-reference-data-interface unified-position-interface \
            unified-sports-execution-interface unified-defi-execution-interface \
            unified-cloud-interface; do
  count=$(find "$repo" -name '*.yaml' -path '*/mocks/*' 2>/dev/null | wc -l | tr -d ' ')
  if [ "$count" -eq 0 ]; then
    emit "§27" "VCR cassettes: $repo" "FAIL" "0 cassettes"
  else
    emit "§27" "VCR cassettes: $repo" "PASS" "$count cassettes"
  fi
done

audit_summary
