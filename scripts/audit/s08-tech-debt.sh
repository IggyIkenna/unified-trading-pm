#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# §8 — Technical Debt
# Checks: type:ignore count, basedpyright baselines, except ImportError, noqa in prod.
# Usage: bash unified-trading-pm/scripts/audit/s08-tech-debt.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$WORKSPACE_ROOT"

echo "=== §8 Technical Debt ==="

# type: ignore count (target <10; each must be in QUALITY_GATE_BYPASS_AUDIT.md)
type_ignore_count=$(rg '# type: ignore' --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  2>/dev/null | wc -l | tr -d ' ')
if [ "$type_ignore_count" -eq 0 ]; then
  emit "§8" "# type: ignore count (target: 0)" "PASS" "none"
elif [ "$type_ignore_count" -le 10 ]; then
  emit "§8" "# type: ignore count (target: 0, max: 10)" "WARN" \
    "$type_ignore_count occurrences — each must be in QUALITY_GATE_BYPASS_AUDIT.md"
else
  emit "§8" "# type: ignore count (target: 0, max: 10)" "FAIL" \
    "$type_ignore_count occurrences (>10 threshold)"
fi

# .basedpyright-baseline.json files (each needs BYPASS_AUDIT.md entry)
# maxdepth 2 = workspace_root/<repo>/.basedpyright-baseline.json — fast
baseline_files=$(rg --files --glob '.basedpyright-baseline.json' \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --max-depth 3 2>/dev/null || true)
baseline_count=$(echo "$baseline_files" | grep -c '.' 2>/dev/null || echo 0)
if [ "$baseline_count" -eq 0 ] || [ -z "$baseline_files" ]; then
  emit "§8" "no .basedpyright-baseline.json files" "PASS" "none"
else
  undocumented=0
  while IFS= read -r baseline; do
    [ -z "$baseline" ] && continue
    repo_dir="$(dirname "$baseline")"
    [ ! -f "$repo_dir/QUALITY_GATE_BYPASS_AUDIT.md" ] && undocumented=$((undocumented+1))
  done <<< "$baseline_files"
  if [ "$undocumented" -gt 0 ]; then
    emit "§8" "basedpyright baselines all documented" "FAIL" \
      "$undocumented of $baseline_count baselines missing QUALITY_GATE_BYPASS_AUDIT.md"
  else
    emit "§8" "basedpyright baselines all documented" "WARN" \
      "$baseline_count baselines exist but all documented (target: 0)"
  fi
fi

# try/except ImportError fallbacks in production (no-empty-fallbacks rule)
# Match the actual Python construct: "except ImportError" not preceded by # (i.e. not a comment)
import_fallbacks=$(rg '^\s+except ImportError' --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' --glob '!**/test_*' \
  --glob '!**/archive/**' \
  -n 2>/dev/null || true)
pass_if_empty "§8" "no try/except ImportError fallbacks in prod" "$import_fallbacks"

# noqa suppressions in production source
noqa_count=$(rg '# noqa' --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' \
  2>/dev/null | wc -l | tr -d ' ')
if [ "$noqa_count" -eq 0 ]; then
  emit "§8" "no # noqa in prod source" "PASS" "none"
else
  emit "§8" "no # noqa in prod source" "FAIL" \
    "$noqa_count occurrences — use ruff config instead: rg '# noqa' --type py --glob '!.venv*' -n"
fi

# Hardcoded project IDs (not 'test-project')
hardcoded_proj=$(rg 'central-element-[0-9]+|[a-z]+-[a-z]+-[0-9]{9}' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' \
  --glob '!**/archive/**' \
  -n 2>/dev/null || true)
pass_if_empty "§8" "no hardcoded GCP project IDs in prod source" "$hardcoded_proj"

audit_summary
