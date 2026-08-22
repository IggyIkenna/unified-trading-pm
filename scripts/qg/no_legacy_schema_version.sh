#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# QG: no-legacy-schema-version
# Service source code MUST NOT hardcode schema_version values < 8 in writer paths.
# Manifest index schema_version must be 8 workspace-wide (v8 migration complete).
#
# Pattern 3 from service-contract-audit-template.md (mega audit B1).
# Source: codex/04-architecture/service-contract-audit-template.md § Pattern 3
#
# Usage: bash scripts/qg/no_legacy_schema_version.sh <repo_root>
# Returns: 0 (pass), 1 (violations found)
#
# owner: slot-8  cadence: CI (pre-merge)  verifier: quality-gates.sh
# last_executed: 2026-05-20

set -euo pipefail

REPO_ROOT="${1:-$(git rev-parse --show-toplevel)}"

VIOLATIONS=0

# Scan all service repos for schema_version literals < 8 in non-test Python files.
# Exempt: test files (they may use any schema_version for fixture data),
#         comments (## schema_version=4 in docs),
#         migration scripts (they set old values intentionally during migration).
for CANDIDATE_DIR in \
    "${REPO_ROOT}/market-tick-data-service/market_tick_data_service" \
    "${REPO_ROOT}/instruments-service/instruments_service" \
    "${REPO_ROOT}/unified-trading-library/unified_trading_library" \
    "${REPO_ROOT}/features-service/features_service" \
    "${REPO_ROOT}/strategy-service/strategy_service" \
    "${REPO_ROOT}/execution-service/execution_service"; do

    [[ ! -d "$CANDIDATE_DIR" ]] && continue

    while IFS= read -r -d '' file; do
        # Skip test files and migration scripts (they may legitimately reference old versions)
        [[ "$file" == *"/tests/"* ]] && continue
        [[ "$file" == *"test_"* ]] && continue
        [[ "$file" == *"_test.py" ]] && continue
        [[ "$file" == *"migrate_"* ]] && continue
        [[ "$file" == *"migration_"* ]] && continue

        if grep -qnE 'schema_version\s*=\s*[1-7][^0-9]' "$file" 2>/dev/null; then
            echo "ERROR: legacy schema_version (< 8) in $file:"
            grep -nE 'schema_version\s*=\s*[1-7][^0-9]' "$file" | grep -v '^\s*#'
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done < <(find "$CANDIDATE_DIR" -name "*.py" -print0 2>/dev/null)
done

if [[ $VIOLATIONS -gt 0 ]]; then
    echo "ERROR: $VIOLATIONS file(s) hardcode schema_version < 8"
    echo "All manifest writers must emit schema_version=8."
    echo "Migration guide: plans/audit/is_mtds_contract_audit_2026_05_20.md Phase 4"
    echo "SSOT: codex/04-architecture/service-contract-audit-template.md § Pattern 3"
    exit 1
fi

echo "OK: no_legacy_schema_version — no schema_version < 8 in service source"
exit 0
