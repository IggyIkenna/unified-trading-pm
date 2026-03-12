#!/bin/bash
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
baseline_count=$(find . -maxdepth 3 -name '.basedpyright-baseline.json' \
  ! -path './.venv*' ! -path './.venv-workspace*' \
  ! -path '*/site-packages/*' \
  2>/dev/null | wc -l | tr -d ' ')
if [ "$baseline_count" -eq 0 ]; then
  emit "§8" "no .basedpyright-baseline.json files" "PASS" "none"
else
  # Check each has a corresponding QUALITY_GATE_BYPASS_AUDIT.md entry
  undocumented=0
  while IFS= read -r baseline; do
    repo_dir="$(dirname "$baseline")"
    if [ ! -f "$repo_dir/QUALITY_GATE_BYPASS_AUDIT.md" ]; then
      undocumented=$((undocumented+1))
    fi
  done < <(find . -maxdepth 3 -name '.basedpyright-baseline.json' \
    ! -path './.venv*' ! -path './.venv-workspace*' 2>/dev/null)
  if [ "$undocumented" -gt 0 ]; then
    emit "§8" "basedpyright baselines all documented" "FAIL" \
      "$undocumented of $baseline_count baselines missing QUALITY_GATE_BYPASS_AUDIT.md"
  else
    emit "§8" "basedpyright baselines all documented" "WARN" \
      "$baseline_count baselines exist but all documented (target: 0 baselines)"
  fi
fi

# try/except ImportError fallbacks in production (no-empty-fallbacks rule)
import_fallbacks=$(rg 'except ImportError' --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' --glob '!**/test_*' \
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
hardcoded_proj=$(rg 'central-element-323112|[a-z]+-[a-z]+-[0-9]{9}' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' \
  -n 2>/dev/null || true)
pass_if_empty "§8" "no hardcoded GCP project IDs in prod source" "$hardcoded_proj"

audit_summary
