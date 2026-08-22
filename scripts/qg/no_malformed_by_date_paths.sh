#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# QG: no-malformed-by-date-paths
# GCS paths containing ``raw_tick_data/by_date/`` MUST use the canonical Hive
# ``key=value`` form: ``raw_tick_data/by_date/day=YYYY-MM-DD/``.
# The legacy ``key-value`` form (``day-YYYY-MM-DD``) breaks BigQuery external
# tables and pyarrow hive-partitioned reads.
#
# Canonical pattern:  raw_tick_data/by_date/day=YYYY-MM-DD/
# Malformed pattern:  raw_tick_data/by_date/day-YYYY-MM-DD/
#
# Exclusions (files that legitimately reference the legacy regex to FIX it):
#   - scripts/_migrate_tradfi_hyphen_rewriter.py  (the migration rewriter)
#   - scripts/migrate_tradfi_to_v9_canonical.py   (calls the rewriter)
#   - Any other scripts/ directory migration file that explicitly parses the
#     legacy form to rewrite it (all such files live under …/scripts/).
#
# Usage: bash scripts/qg/no_malformed_by_date_paths.sh <workspace_root>
# Returns: 0 (pass), 1 (violations found)
#
# owner: slot-7  cadence: CI (pre-merge)  verifier: quality-gates.sh
# last_executed: 2026-06-02

set -euo pipefail

WORKSPACE_ROOT="${1:-$(git rev-parse --show-toplevel)}"

MTDS_ROOT="${WORKSPACE_ROOT}/market-tick-data-service"
SOURCE_DIR="${MTDS_ROOT}/market_tick_data_service"

if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "SKIP: MTDS source directory not found: $SOURCE_DIR"
    exit 0
fi

VIOLATIONS=0

# ------------------------------------------------------------------
# Pattern: string literals or docstrings that embed the malformed
# ``day-YYYY-MM-DD`` hyphen segment after ``raw_tick_data/by_date/``.
#
# We scan for the literal substring ``by_date/day-`` followed by a
# digit (to match actual path constructions, not prose like
# "by_date/day-of-week"). Migration scripts that define/match the
# legacy regex to rewrite it are excluded.
# ------------------------------------------------------------------

_RAW_HITS=$(grep -rn "by_date/day-[0-9]" \
    "${SOURCE_DIR}" \
    --include="*.py" \
    --exclude-dir="__pycache__" \
    --exclude-dir=".venv" \
    --exclude-dir=".venv-workspace" \
    --exclude-dir="build" \
    --exclude-dir="dist" \
    --exclude-dir="node_modules" \
    2>/dev/null || true)

# Exclude the migration scripts that legitimately reference the legacy
# pattern in order to rewrite it (all live under …/scripts/).
_FILTERED_HITS=$(echo "$_RAW_HITS" \
    | grep -v "scripts/_migrate_tradfi_hyphen_rewriter\.py" \
    | grep -v "scripts/migrate_tradfi_to_v9_canonical\.py" \
    | grep -v "/scripts/migrate_" \
    | grep -v "/scripts/_migrate_" \
    | grep -v '^\s*$' \
    || true)

if [[ -n "$_FILTERED_HITS" ]]; then
    echo "ERROR: Malformed GCS paths found (use day=YYYY-MM-DD, not day-YYYY-MM-DD):"
    echo "$_FILTERED_HITS"
    echo ""
    echo "Canonical form:  raw_tick_data/by_date/day=YYYY-MM-DD/"
    echo "Malformed form:  raw_tick_data/by_date/day-YYYY-MM-DD/  (breaks Hive + BQ)"
    echo "SSOT: market_tick_data_service/scripts/_migrate_tradfi_hyphen_rewriter.py"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# ------------------------------------------------------------------
# Pattern 2: f-string or concatenation that builds a by_date/ path
# using a variable interpolation of the hyphen form ``day-{`` (e.g.
# f"raw_tick_data/by_date/day-{date}/"). This catches runtime paths
# that aren't literal strings.
# ------------------------------------------------------------------

_RAW_HITS2=$(grep -rn 'by_date/day-{' \
    "${SOURCE_DIR}" \
    --include="*.py" \
    --exclude-dir="__pycache__" \
    --exclude-dir=".venv" \
    --exclude-dir=".venv-workspace" \
    --exclude-dir="build" \
    --exclude-dir="dist" \
    --exclude-dir="node_modules" \
    2>/dev/null || true)

_FILTERED_HITS2=$(echo "$_RAW_HITS2" \
    | grep -v "scripts/_migrate_tradfi_hyphen_rewriter\.py" \
    | grep -v "scripts/migrate_tradfi_to_v9_canonical\.py" \
    | grep -v "/scripts/migrate_" \
    | grep -v "/scripts/_migrate_" \
    | grep -v '^\s*$' \
    || true)

if [[ -n "$_FILTERED_HITS2" ]]; then
    echo "ERROR: Malformed f-string/concat GCS path construction (use day=, not day-):"
    echo "$_FILTERED_HITS2"
    echo ""
    echo "Canonical form:  f\"raw_tick_data/by_date/day={date}/\""
    echo "Malformed form:  f\"raw_tick_data/by_date/day-{date}/\"  (breaks Hive + BQ)"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
if [[ $VIOLATIONS -gt 0 ]]; then
    echo ""
    echo "ERROR: $VIOLATIONS malformed-by_date-path violation group(s) in MTDS source."
    exit 1
fi

echo "OK: no_malformed_by_date_paths — all by_date/ GCS paths use canonical day=YYYY-MM-DD form"
exit 0
