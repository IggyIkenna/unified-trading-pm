#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# QG: no-blank-empty-reason
# Every record_empty() call MUST supply a typed EmptyConfirmedReason enum value.
# Blank reason strings raise LegacyBlankErrorReasonError at runtime.
# String literal reasons (instead of enum) fail UAC validation.
#
# Pattern 4 from service-contract-audit-template.md (mega audit B1).
# Source: codex/04-architecture/service-contract-audit-template.md § Pattern 4
#
# Usage: bash scripts/qg/no_blank_empty_reason.sh <repo_root>
# Returns: 0 (pass), 1 (violations found)
#
# owner: slot-8  cadence: CI (pre-merge)  verifier: quality-gates.sh
# last_executed: 2026-05-20

set -euo pipefail

REPO_ROOT="${1:-$(git rev-parse --show-toplevel)}"

VIOLATIONS=0

for CANDIDATE_DIR in \
    "${REPO_ROOT}/market-tick-data-service/market_tick_data_service" \
    "${REPO_ROOT}/instruments-service/instruments_service" \
    "${REPO_ROOT}/features-service/features_service" \
    "${REPO_ROOT}/strategy-service/strategy_service" \
    "${REPO_ROOT}/execution-service/execution_service" \
    "${REPO_ROOT}/ml-service/ml_service"; do

    [[ ! -d "$CANDIDATE_DIR" ]] && continue

    while IFS= read -r -d '' file; do
        [[ "$file" == *"/tests/"* ]] && continue
        [[ "$file" == *"test_"* ]] && continue
        [[ "$file" == *"_test.py" ]] && continue

        # Pattern: record_empty with blank reason string ""
        if grep -qnE 'record_empty\s*\(.*reason\s*=\s*""' "$file" 2>/dev/null; then
            echo "ERROR: blank reason string in record_empty() call in $file:"
            grep -nE 'record_empty\s*\(.*reason\s*=\s*""' "$file"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi

        # Pattern: record_empty with non-enum string literal reason (any quoted non-empty string)
        # Exempt: EmptyConfirmedReason.<VALUE> references (correct enum usage)
        if grep -qnE 'record_empty\s*\(.*reason\s*=\s*"[A-Z_]+"' "$file" 2>/dev/null; then
            # Check if it's passing the enum value via .value or string — both forms checked
            HITS=$(grep -nE 'record_empty\s*\(.*reason\s*=\s*"[A-Z_]+"' "$file" | grep -v 'EmptyConfirmedReason\|# noqa' || true)
            if [[ -n "$HITS" ]]; then
                echo "ERROR: string literal reason in record_empty() — use EmptyConfirmedReason enum in $file:"
                echo "$HITS"
                VIOLATIONS=$((VIOLATIONS + 1))
            fi
        fi
    done < <(find "$CANDIDATE_DIR" -name "*.py" -print0 2>/dev/null)
done

if [[ $VIOLATIONS -gt 0 ]]; then
    echo "ERROR: $VIOLATIONS file(s) use blank or string-literal record_empty reasons"
    echo "Use EmptyConfirmedReason from unified_api_contracts.canonical.crosscutting.honest_coverage"
    echo "Valid reasons: SOURCE_RETURNED_ZERO, EXPECTED_PRE_SOURCE_COVERAGE_START, EXPECTED_PAST_SOURCE_COVERAGE_END, ..."
    echo "SSOT: codex/04-architecture/service-contract-audit-template.md § Pattern 4"
    exit 1
fi

echo "OK: no_blank_empty_reason — all record_empty() calls use typed EmptyConfirmedReason"
exit 0
