#!/usr/bin/env bash
# Epic: instruments_master
# Lifecycle: permanent
# Delete-when: NA
# QG: no-blank-instruments-data-type
# Non-sports record_captured() calls in writers.py MUST stamp data_type='instruments'.
# data_type="" was the regression (2026-06-29..2026-07-06) that made 260 cefi/defi/tradfi
# shards appear absent to downstream consumers filtering by data_type='instruments'.
#
# Regression SSOT: plans/active/issues/is_cefi_manifest_blank_data_type_since_2026_06_29_2026_07_06.md
# Writer SSOT: codex/02-data/availability-manifest-and-data-status.md
#
# Usage: bash scripts/qg/no_blank_instruments_data_type.sh <workspace_root>
# Returns: 0 (pass), 1 (violation found)
#
# owner: slot-11  cadence: CI (pre-merge)  verifier: instruments-service/scripts/quality-gates.sh
# last_executed: 2026-07-06

set -euo pipefail

WORKSPACE_ROOT="${1:-$(cd "$(git rev-parse --show-toplevel)/.." && pwd)}"

WRITERS_FILE="${WORKSPACE_ROOT}/instruments-service/instruments_service/engine/orchestrator/writers.py"

if [[ ! -f "$WRITERS_FILE" ]]; then
    echo "SKIP: writers.py not found at ${WRITERS_FILE}"
    exit 0
fi

# Detect data_type="" as a keyword argument — negative lookbehind excludes variable
# assignment prefixes like manifest_data_type (preceded by underscore).
# Sports record_captured paths are exempt: they pass data_type=manifest_data_type
# (a variable), which does not match this literal-string pattern.
VIOLATIONS=$(grep -nP '(?<![_a-zA-Z])data_type\s*=\s*""' "$WRITERS_FILE" || true)

if [[ -n "$VIOLATIONS" ]]; then
    echo "ERROR: blank data_type=\"\" in writers.py — non-sports IS record_captured must stamp data_type='instruments':"
    echo "$VIOLATIONS"
    echo "Fix: change data_type=\"\" to data_type=\"instruments\" for cefi/tradfi/defi paths."
    echo "Regression SSOT: plans/active/issues/is_cefi_manifest_blank_data_type_since_2026_06_29_2026_07_06.md"
    exit 1
fi

echo "OK: no_blank_instruments_data_type — writers.py non-sports record_captured stamps data_type='instruments'"
exit 0
