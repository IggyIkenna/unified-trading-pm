#!/usr/bin/env bash
# QG STEP 5.90: every GET /data-status route file MUST import the canonical helper.
#
# Finds Python files in SOURCE_DIR that define a GET /data-status endpoint and
# checks that they import compute_coverage_for_bucket or compute_honest_coverage.
# Files that only define an internal helper (no router.get route) are not checked.
#
# Exemption: a /data-status endpoint that returns NON-coverage payload (access
# rules, key/credential status, static metadata — not a manifest-coverage read)
# declares the marker `# QG-allow: data-status-no-coverage` with a one-line reason
# (on or next to the route decorator). The coverage formula does not apply to such
# endpoints, and forcing it would fabricate a meaningless ratio (a banned pattern).
#
# Usage: check_data_status_endpoint_canonical.sh <source_dir>
# Exit 0 = all clean.  Exit 1 = violation(s) found.
#
# SSOT: codex/06-coding-standards/data-status-endpoint-contract.md
#       honest_coverage_formula_consolidation_2026_05_19.md Phase 1 P1 / STEP 5.90

set -euo pipefail

SOURCE_DIR="${1:-}"
if [[ -z "$SOURCE_DIR" || ! -d "$SOURCE_DIR" ]]; then
    echo "SKIP: SOURCE_DIR not set or not a directory — no data-status endpoint files to check"
    exit 0
fi

# Inline escape hatch for a non-coverage data-status endpoint (file-scoped — this
# check matches at file granularity). Carries a one-line reason at the call site.
ALLOW_MARKER='# QG-allow: data-status-no-coverage'

VIOLATIONS=()

# Find every .py file that contains a data-status GET route declaration.
while IFS= read -r -d '' FILE; do
    # Does this file define a GET /data-status route?
    if ! grep -qE '@(router|app)\.get\(.*["'"'"']/?.*data-status' "$FILE" 2>/dev/null; then
        continue
    fi
    # Explicitly exempted non-coverage data-status endpoint (access rules / metadata)?
    if grep -qF "$ALLOW_MARKER" "$FILE" 2>/dev/null; then
        continue
    fi
    # Does it import either canonical helper?
    if ! grep -qE 'compute_coverage_for_bucket|compute_honest_coverage' "$FILE" 2>/dev/null; then
        VIOLATIONS+=("$FILE")
    fi
done < <(find "$SOURCE_DIR" -name '*.py' -print0)

if [[ ${#VIOLATIONS[@]} -eq 0 ]]; then
    echo "OK: all GET /data-status route files use compute_coverage_for_bucket or compute_honest_coverage"
    exit 0
fi

echo "FAIL: GET /data-status route file(s) do not import the canonical coverage helper."
echo "      Import compute_coverage_for_bucket (UTL) or compute_honest_coverage (UAC)."
echo "      See codex/06-coding-standards/data-status-endpoint-contract.md"
for F in "${VIOLATIONS[@]}"; do
    echo "  violation: $F"
done
exit 1
