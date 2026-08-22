#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# §2 — Code Quality
# Checks: QG stub size, os.getenv in prod, pyrightconfig test exclusion, basedpyright mode, file size.
# Usage: bash unified-trading-pm/scripts/audit/s02-code-quality.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$WORKSPACE_ROOT"

echo "=== §2 Code Quality ==="

# QG stub size (>50 lines = violation — must delegate to base script)
stub_violations=$(wc -l */scripts/quality-gates.sh 2>/dev/null \
  | awk '$1 > 50 && $2 != "total" {print $2, "("$1"L)"}')
pass_if_empty "§2" "QG stub size ≤50L per repo" "$stub_violations"

# os.getenv in production source (excluding bootstrap exceptions)
getenv_hits=$(rg 'os\.getenv' --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' --glob '!**/test_*' \
  --glob '!**/factory.py' --glob '!**/bootstrap_config.py' \
  --glob '!**/constants.py' \
  --glob '!**/archive/**' \
  -n 2>/dev/null || true)
pass_if_empty "§2" "no os.getenv in prod source (excl bootstrap)" "$getenv_hits"

# pyright vs basedpyright in pyproject.toml
pyright_wrong=$(rg '"pyright"' --glob '*/pyproject.toml' \
  --glob '!.venv*' 2>/dev/null || true)
pass_if_empty "§2" "all repos use basedpyright not pyright" "$pyright_wrong"

# basedpyright strict mode present
non_strict=$(rg -L 'basedpyright' --glob '*/pyproject.toml' \
  --glob '!.venv*' --glob '!unified-trading-pm/**' 2>/dev/null \
  | grep 'pyproject.toml' || true)
# This is a heuristic: check that pyproject.toml files reference strict/reportAny
reportany_missing=$(rg -L 'reportAny' --glob '*/pyproject.toml' \
  --glob '!.venv*' --glob '!unified-trading-pm/**' \
  --glob '!*ui*/**' 2>/dev/null | head -5 || true)
if [ -z "$reportany_missing" ]; then
  emit "§2" "basedpyright reportAny: error in pyproject.toml" "PASS" "none"
else
  count=$(echo "$reportany_missing" | wc -l | tr -d ' ')
  emit "§2" "basedpyright reportAny: error in pyproject.toml" "WARN" \
    "$count repos may be missing reportAny — first: $(echo "$reportany_missing" | head -1)"
fi

# File size >900 lines — delegate to existing checker (fast, per-repo)
large_files=$(bash "$(dirname "${BASH_SOURCE[0]}")/../validation/check-codsize-violations.sh" \
  --threshold 900 2>/dev/null | grep ' lines: ' | head -10 || true)
if [ -z "$large_files" ]; then
  emit "§2" "no source files >900L" "PASS" "none"
else
  count=$(echo "$large_files" | wc -l | tr -d ' ')
  emit "§2" "no source files >900L" "WARN" \
    "$count files — first: $(echo "$large_files" | head -1)"
fi

audit_summary
