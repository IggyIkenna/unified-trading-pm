#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# QG: no-inline-coverage-formula
# Detects re-implementations of compute_honest_coverage() outside the canonical
# UAC honest_coverage.py file. Any caller that derives numerator/denominator
# directly from capture_status columns MUST use compute_honest_coverage() instead.
#
# Looks for patterns that suggest a bespoke coverage formula:
#   - Variables/expressions matching "coverage_ratio", "coverage_pct", "_coverage"
#     assigned via arithmetic that touches "captured" or "denominator"
#   - Direct "captured / total" arithmetic in coverage context
#
# False-positive suppression: exempt the canonical SSOT files and test files.
#
# Usage: bash scripts/qg/no_inline_coverage_formula.sh <workspace_root>
# Returns: 0 (pass), 1 (violations found)
#
# owner: slot-2  cadence: CI (pre-merge)  verifier: quality-gates.sh
# last_executed: 2026-05-20

set -euo pipefail

WORKSPACE_ROOT="${1:-$(git rev-parse --show-toplevel)}"

# Canonical files exempt from the linter (they ARE the SSOT)
EXEMPT_PATTERNS=(
    "honest_coverage.py"
    "manifest_writer.py"
    "manifest_completeness.py"
    "test_"
)

VIOLATIONS=0

# Pattern 1: inline coverage_ratio / coverage_pct / _pct assignment via arithmetic
#   e.g.  coverage_ratio = captured / total
#         coverage_pct = captured_count / (captured_count + failed_count)
PATTERN1='(coverage_ratio|coverage_pct|_coverage)\s*=\s*.*[0-9a-z_]\s*/\s*'

# Pattern 2: direct captured + empty_confirmed arithmetic in numerator assignment
#   e.g.  numerator = captured + empty_confirmed
PATTERN2='(numerator|denominator)\s*=\s*.*(captured|empty_confirmed|attempted_failed)'

for pattern in "$PATTERN1" "$PATTERN2"; do
    while IFS= read -r match_line; do
        [[ -z "$match_line" ]] && continue
        file_path="${match_line%%:*}"

        # Check exemptions
        skip=false
        for exempt in "${EXEMPT_PATTERNS[@]}"; do
            if [[ "$file_path" == *"$exempt"* ]]; then
                skip=true
                break
            fi
        done
        $skip && continue

        # Only flag Python service files (not scripts, not migrations)
        if [[ "$file_path" == *"_service/"* || "$file_path" == *"-api/"* ]]; then
            echo "INLINE-COVERAGE-FORMULA: $match_line"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done < <(
        grep -rn --include="*.py" -E "$pattern" "$WORKSPACE_ROOT" \
            --glob '!.venv*' --glob '!build' --glob '!node_modules' 2>/dev/null || true
    )
done

if [[ $VIOLATIONS -gt 0 ]]; then
    echo ""
    echo "ERROR: $VIOLATIONS inline coverage formula re-implementation(s) detected."
    echo "Replace with: from unified_api_contracts import compute_honest_coverage, CaptureStatusCounts"
    echo "See: codex/02-data/availability-manifest-and-data-status.md § Coverage formula"
    exit 1
fi

echo "OK: no inline coverage formula re-implementations detected."
exit 0
