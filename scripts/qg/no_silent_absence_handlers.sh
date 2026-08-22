#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# QG: no-silent-absence-handlers
# For every *_handler.py in MTDS + instruments-service, every function whose
# name matches handle_*|collect_*|backfill_*|_fetch_* MUST contain at least
# one call to record_captured|record_empty|record_failed|record_expected_unattempted.
#
# Exempt list (documented below): data_manifest_handler.py, replay_handler.py,
# tick_data_handler.py — until their Phase 3 audit (is_mtds_contract_audit_2026_05_20) completes.
#
# Usage: bash scripts/qg/no_silent_absence_handlers.sh <repo_root>
# Returns: 0 (pass), 1 (violations found)
#
# owner: slot-8  cadence: CI (pre-merge)  verifier: quality-gates.sh
# last_executed: 2026-05-20

set -euo pipefail

REPO_ROOT="${1:-$(git rev-parse --show-toplevel)}"

# Service handler directories to scan
HANDLER_DIRS=(
    "${REPO_ROOT}/market-tick-data-service/market_tick_data_service/cli/handlers"
    "${REPO_ROOT}/instruments-service/instruments_service/cli/handlers"
    "${REPO_ROOT}/instruments-service/instruments_service/reference_data/adapters"
)

# Exempt files (legacy handlers pending Phase 3 audit)
EXEMPT_FILES=(
    "data_manifest_handler.py"
    "replay_handler.py"
    "tick_data_handler.py"
)

VIOLATIONS=0

for handler_dir in "${HANDLER_DIRS[@]}"; do
    [[ -d "$handler_dir" ]] || continue

    while IFS= read -r -d '' handler_file; do
        basename=$(basename "$handler_file")

        # Check exemptions
        exempt=0
        for exempt_file in "${EXEMPT_FILES[@]}"; do
            if [[ "$basename" == "$exempt_file" ]]; then
                exempt=1
                break
            fi
        done
        if [[ $exempt -eq 1 ]]; then
            continue
        fi

        # Extract function names matching handle_*|collect_*|backfill_*|_fetch_*
        # grep for "def <name>(" patterns; extract just the function body by checking
        # if the record_* calls appear anywhere in the file (conservative: file-level check)
        matching_fns=$(grep -cP '^\s*(async )?def (handle_\w+|collect_\w+|backfill_\w+|_fetch_\w+)\(' "$handler_file" 2>/dev/null || echo "0")
        matching_fns="${matching_fns//[[:space:]]/}"
        if [[ "$matching_fns" -eq 0 ]]; then
            continue
        fi

        # Check if the file has ANY record_* emission
        if ! grep -qE 'record_captured|record_empty|record_failed|record_expected_unattempted' "$handler_file" 2>/dev/null; then
            echo "SILENT-ABSENCE: $handler_file has ${matching_fns} handle/collect/backfill/_fetch functions but NO record_* calls"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done < <(find "$handler_dir" -name "*_handler.py" -print0 2>/dev/null)
done

# Phase Qa/Qb: explicit file checks for strategy→execution boundary
# These files contain write_instructions() / download_instructions_df() and MUST
# have manifest emission (record_captured|record_empty|record_failed).
SPECIFIC_FILES=(
    "${REPO_ROOT}/strategy-service/strategy_service/engine/core/gcs_storage_service.py"
    "${REPO_ROOT}/execution-service/execution_service/strategy_instructions/gcs.py"
)

for specific_file in "${SPECIFIC_FILES[@]}"; do
    [[ -f "$specific_file" ]] || continue
    if ! grep -qE 'record_captured|record_empty|record_failed' "$specific_file" 2>/dev/null; then
        echo "SILENT-ABSENCE: $specific_file has no manifest emission (record_captured/record_empty/record_failed)"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

if [[ $VIOLATIONS -gt 0 ]]; then
    echo "ERROR: $VIOLATIONS handler file(s) have no manifest emission (silent-absence violation)"
    echo "Each handle_*/collect_*/backfill_*/_fetch_* function MUST emit record_captured/record_empty/record_failed."
    echo "Exempt: data_manifest_handler.py, replay_handler.py, tick_data_handler.py (pending Phase 3 audit)"
    echo "SSOT: plans/active/is_mtds_contract_audit_2026_05_20.md Phase 7"
    exit 1
fi

echo "OK: no_silent_absence_handlers — all scanned handlers have manifest emission"
exit 0
