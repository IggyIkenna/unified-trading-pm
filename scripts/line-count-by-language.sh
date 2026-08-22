#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Count lines of code by language; exclude venv/node_modules; split test vs non-test.
# Requires: cloc (brew install cloc)
# Usage: from workspace root, run:
#   bash unified-trading-pm/scripts/line-count-by-language.sh
# Or: cd unified-trading-pm && bash scripts/line-count-by-language.sh
# (script will cd to workspace root automatically if UNIFIED_TRADING_WORKSPACE_ROOT is set)

set -e

# Resolve workspace root
if [[ -n "${UNIFIED_TRADING_WORKSPACE_ROOT}" ]]; then
  ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT}"
else
  # Assume we're in unified-trading-pm or workspace root
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ "$(basename "$(dirname "$SCRIPT_DIR")")" == "unified-trading-pm" ]]; then
    ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  else
    ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
  fi
fi
cd "$ROOT"

EXCLUDE_DIRS=".venv,.venv-workspace,node_modules,build,dist,__pycache__,.git,.ruff_cache,.mypy_cache,*.egg-info,htmlcov,.coverage"

if ! command -v cloc &>/dev/null; then
  echo "cloc is required. Install with: brew install cloc"
  exit 1
fi

echo "Workspace root: $ROOT"
echo "Excluded dirs: $EXCLUDE_DIRS"
echo ""

# --- Full codebase by language ---
echo "========== Full codebase (by language) =========="
cloc . --exclude-dir="$EXCLUDE_DIRS" --quiet
echo ""

# --- Test-only files ---
TEST_LIST="$(mktemp)"
FULL_LIST="$(mktemp)"
NON_TEST_LIST="$(mktemp)"
trap 'rm -f "$TEST_LIST" "$FULL_LIST" "$NON_TEST_LIST"' EXIT

find . -type f \
  \( -path '*/.venv*' -o -path '*/.venv-workspace*' -o -path '*/node_modules*' \
  -o -path '*/.git*' -o -path '*/build*' -o -path '*/dist*' \
  -o -path '*/__pycache__*' -o -path '*/htmlcov*' \) -prune -o \
  \( -name 'test_*.py' -o -name '*_test.py' -o -path '*/tests/*' \
  -o -path '*/__tests__/*' -o -name '*.test.ts' -o -name '*.spec.ts' \
  -o -name '*.test.tsx' -o -name '*.spec.tsx' \
  -o -name 'test_*.sh' -o -name '*_test.sh' -o -path '*/test/*' \) \
  -print 2>/dev/null | sed 's|^\./||' >"$TEST_LIST"

TEST_COUNT=$(grep -c . "$TEST_LIST" 2>/dev/null || true)
if [[ "$TEST_COUNT" -gt 0 ]]; then
  echo "========== Test files only ($TEST_COUNT files) =========="
  cloc --list-file="$TEST_LIST" --quiet
  echo ""
fi

# --- Non-test files (all minus test patterns) ---
find . -type f \
  \( -path '*/.venv*' -o -path '*/.venv-workspace*' -o -path '*/node_modules*' \
  -o -path '*/.git*' -o -path '*/build*' -o -path '*/dist*' \
  -o -path '*/__pycache__*' -o -path '*/htmlcov*' -o -path '*/.ruff_cache*' \) -prune -o \
  \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' \
  -o -name '*.sh' -o -name '*.bash' \) -print 2>/dev/null | sed 's|^\./||' | sort -u >"$FULL_LIST"

comm -23 <(sort -u "$FULL_LIST") <(sort -u "$TEST_LIST") >"$NON_TEST_LIST" 2>/dev/null || true

NON_TEST_COUNT=$(grep -c . "$NON_TEST_LIST" 2>/dev/null || true)
if [[ "$NON_TEST_COUNT" -gt 0 ]]; then
  echo "========== Non-test (source) files only ($NON_TEST_COUNT files) =========="
  cloc --list-file="$NON_TEST_LIST" --quiet
fi

echo ""
echo "Test patterns used: test_*.py, *_test.py, tests/, __tests__/, *.test.ts, *.spec.ts, test_*.sh, *_test.sh"
