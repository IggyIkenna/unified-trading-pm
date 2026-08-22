#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# aggregate-audit-summary.sh — Aggregate all audit results for a given date.
#
# Usage:
#   bash scripts/audit/aggregate-audit-summary.sh --date 2026-03-13
#
# Output: prints summary JSON to stdout, writes plans/audit/results/summary_{date}.json
#
# Summary format:
# {
#   "date": "2026-03-13",
#   "total_repos": 12,
#   "pass_count": 10,
#   "fail_count": 2,
#   "warn_total": 5,
#   "overall_grade": "FAIL",
#   "failed_repos": ["repo-a", "repo-b"],
#   "repos": [ ...individual results... ]
# }

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$PM_ROOT/plans/audit/results"

# ── Parse args ───────────────────────────────────────────────────────────────
DATE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --date) DATE="$2"; shift 2 ;;
    *) echo "ERROR: Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$DATE" ]]; then
  echo "ERROR: --date is required." >&2
  exit 1
fi

# ── Find result files ───────────────────────────────────────────────────────
RESULT_FILES=()
for f in "$RESULTS_DIR"/*_"${DATE}".json; do
  # Skip the summary file itself and non-existent glob
  [[ "$(basename "$f")" == summary_* ]] && continue
  [[ -f "$f" ]] && RESULT_FILES+=("$f")
done

if [[ ${#RESULT_FILES[@]} -eq 0 ]]; then
  echo "ERROR: No results found for date $DATE in $RESULTS_DIR" >&2
  exit 1
fi

# ── Aggregate ────────────────────────────────────────────────────────────────
OUT_FILE="$RESULTS_DIR/summary_${DATE}.json"

python3 -c "
import json, sys, glob, os

date = '$DATE'
results_dir = '$RESULTS_DIR'
out_file = '$OUT_FILE'

files = [f for f in sorted(glob.glob(os.path.join(results_dir, f'*_{date}.json')))
         if not os.path.basename(f).startswith('summary_')]

if not files:
    print('No result files found', file=sys.stderr)
    sys.exit(1)

repos = []
for f in files:
    with open(f) as fh:
        repos.append(json.load(fh))

total = len(repos)
passes = sum(1 for r in repos if r['grade'] == 'PASS')
fails = sum(1 for r in repos if r['grade'] == 'FAIL')
warn_total = sum(r.get('warn_count', 0) for r in repos)
failed_repos = [r['repo'] for r in repos if r['grade'] == 'FAIL']
overall = 'FAIL' if fails > 0 else 'PASS'

summary = {
    'date': date,
    'total_repos': total,
    'pass_count': passes,
    'fail_count': fails,
    'warn_total': warn_total,
    'overall_grade': overall,
    'failed_repos': failed_repos,
    'repos': repos
}

with open(out_file, 'w') as f:
    json.dump(summary, f, indent=2)
    f.write('\n')

# Also print to stdout
print(json.dumps(summary, indent=2))
"

echo "" >&2
echo "Summary written to: $OUT_FILE" >&2
