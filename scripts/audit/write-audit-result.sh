#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# write-audit-result.sh — Write a single repo audit result as JSON.
#
# Usage:
#   bash scripts/audit/write-audit-result.sh \
#     --repo unified-trading-library \
#     --date 2026-03-13 \
#     --grade PASS \
#     --pass-count 12 --fail-count 0 --warn-count 3 \
#     --sections '[{"id":"s01","title":"Governance","result":"PASS","details":"OK"}]'
#
# Output: writes plans/audit/results/{repo}_{date}.json
# Exits non-zero on missing required args.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$PM_ROOT/plans/audit/results"

# ── Parse args ───────────────────────────────────────────────────────────────
REPO="" DATE="" GRADE="" PASS_COUNT=0 FAIL_COUNT=0 WARN_COUNT=0 SECTIONS="[]"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)        REPO="$2";        shift 2 ;;
    --date)        DATE="$2";        shift 2 ;;
    --grade)       GRADE="$2";       shift 2 ;;
    --pass-count)  PASS_COUNT="$2";  shift 2 ;;
    --fail-count)  FAIL_COUNT="$2";  shift 2 ;;
    --warn-count)  WARN_COUNT="$2";  shift 2 ;;
    --sections)    SECTIONS="$2";    shift 2 ;;
    *) echo "ERROR: Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# ── Validate ─────────────────────────────────────────────────────────────────
if [[ -z "$REPO" || -z "$DATE" || -z "$GRADE" ]]; then
  echo "ERROR: --repo, --date, and --grade are required." >&2
  exit 1
fi

if [[ "$GRADE" != "PASS" && "$GRADE" != "FAIL" ]]; then
  echo "ERROR: --grade must be PASS or FAIL (got: $GRADE)." >&2
  exit 1
fi

# Validate date format YYYY-MM-DD
if ! [[ "$DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "ERROR: --date must be YYYY-MM-DD (got: $DATE)." >&2
  exit 1
fi

# Validate sections is valid JSON array
if ! echo "$SECTIONS" | python3 -c "import sys,json; json.load(sys.stdin)" >/dev/null 2>&1; then
  echo "ERROR: --sections must be valid JSON array." >&2
  exit 1
fi

# ── Write result ─────────────────────────────────────────────────────────────
mkdir -p "$RESULTS_DIR"
OUT_FILE="$RESULTS_DIR/${REPO}_${DATE}.json"

python3 -c "
import json, sys
result = {
    'repo': '$REPO',
    'date': '$DATE',
    'grade': '$GRADE',
    'pass_count': $PASS_COUNT,
    'fail_count': $FAIL_COUNT,
    'warn_count': $WARN_COUNT,
    'sections': json.loads('''$SECTIONS''')
}
with open('$OUT_FILE', 'w') as f:
    json.dump(result, f, indent=2)
    f.write('\n')
"

echo "Wrote: $OUT_FILE"
