#!/usr/bin/env bash
# Coverage floor governance guard (add-coverage-floor-governance).
# Validates that MIN_COVERAGE meets the system-wide floor (70) OR has a signed-off exception.
# Usage: bash scripts/coverage-floor-guard.sh <service_qg_script> <pyproject_toml>
# Called from quality-gates base scripts after reading MIN_COVERAGE.
set -euo pipefail

SYSTEM_FLOOR=70
QG_SCRIPT="${1:-scripts/quality-gates.sh}"
PYPROJECT="${2:-pyproject.toml}"
EXCEPTION_FILE=".coverage-floor-exception.md"

# Read MIN_COVERAGE from repo QG stub.
# `cut -d'#' -f1` strips any inline comment (e.g. `MIN_COVERAGE=28  # ISS-031: restore...`) BEFORE the
# whitespace-strip — otherwise the comment glues onto the value (`28#ISS-031...`) and every integer
# comparison below errors with "integer expression expected", silently masking the floor check.
MIN_COVERAGE=$(grep -E '^MIN_COVERAGE=' "$QG_SCRIPT" 2>/dev/null | head -1 | cut -d'=' -f2 | cut -d'#' -f1 || echo "$SYSTEM_FLOOR")
MIN_COVERAGE="${MIN_COVERAGE//[[:space:]]/}"

# Read fail_under from pyproject.toml
FAIL_UNDER=$(grep -E 'fail_under\s*=' "$PYPROJECT" 2>/dev/null | grep -oE '[0-9]+' | head -1 || echo "$MIN_COVERAGE")

# Check for mismatch: warn if pyproject fail_under < MIN_COVERAGE (pyproject is the real pytest gate)
if [ -n "$FAIL_UNDER" ] && [ "$FAIL_UNDER" -lt "$MIN_COVERAGE" ]; then
    echo "⚠ COVERAGE MISMATCH: MIN_COVERAGE=$MIN_COVERAGE but pyproject.toml fail_under=$FAIL_UNDER" >&2
    echo "  pyproject.toml fail_under is the real gate — QG MIN_COVERAGE should match or be lower" >&2
fi

# Enforce system floor
if [ "$MIN_COVERAGE" -lt "$SYSTEM_FLOOR" ]; then
    if [ -f "$EXCEPTION_FILE" ]; then
        # Validate exception file format
        if grep -q "^Approved by:" "$EXCEPTION_FILE" && \
           grep -q "^Date:" "$EXCEPTION_FILE" && \
           grep -q "^Reason:" "$EXCEPTION_FILE"; then
            APPROVED_BY=$(grep "^Approved by:" "$EXCEPTION_FILE" | cut -d':' -f2- | xargs)
            DATE=$(grep "^Date:" "$EXCEPTION_FILE" | cut -d':' -f2- | xargs)
            echo "⚠ Coverage floor exception: MIN_COVERAGE=$MIN_COVERAGE (system floor=$SYSTEM_FLOOR)"
            echo "  Approved by: $APPROVED_BY on $DATE"
        else
            echo "❌ COVERAGE FLOOR VIOLATION: MIN_COVERAGE=$MIN_COVERAGE < system floor $SYSTEM_FLOOR" >&2
            echo "  Exception file $EXCEPTION_FILE missing required fields (Approved by, Date, Reason)" >&2
            exit 1
        fi
    else
        echo "❌ COVERAGE FLOOR VIOLATION: MIN_COVERAGE=$MIN_COVERAGE < system floor $SYSTEM_FLOOR" >&2
        echo "  To override: create $EXCEPTION_FILE with:" >&2
        echo "    Approved by: [human name]" >&2
        echo "    Date: $(date +%Y-%m-%d)" >&2
        echo "    Reason: [justification]" >&2
        exit 1
    fi
else
    echo "✓ Coverage floor: MIN_COVERAGE=$MIN_COVERAGE >= system floor $SYSTEM_FLOOR"
fi
