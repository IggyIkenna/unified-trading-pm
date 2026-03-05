#!/usr/bin/env bash
# Audit all workspace repos for reset/reset --hard/reset to origin in reflog.
# Reports repos that may have had commits discarded. For manual review.
#
# Usage: bash audit-reflog-resets.sh [--limit N] [--reflog-depth N]
# Run from: workspace root or unified-trading-pm/scripts/repo-management/
#
# Output: Repos with reset entries, categorized by risk (--hard, to origin, no-op).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
MANIFEST="$PM_ROOT/workspace-manifest.json"

REFLOG_DEPTH=50
LIMIT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit) LIMIT="$2"; shift 2 ;;
    --reflog-depth) REFLOG_DEPTH="$2"; shift 2 ;;
    *) shift ;;
  esac
done

[[ ! -f "$MANIFEST" ]] && { echo "Missing $MANIFEST"; exit 1; }

REPOS=($(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null))
[[ -n "$LIMIT" ]] && REPOS=("${REPOS[@]:0:$LIMIT}")

echo "Audit reflog for resets: ${#REPOS[@]} repos (depth=$REFLOG_DEPTH)"
echo ""

high_risk=()
medium_risk=()
low_risk=()

for repo in "${REPOS[@]}"; do
  dir="$WORKSPACE_ROOT/$repo"
  [[ ! -d "$dir" ]] && continue
  [[ ! -d "$dir/.git" ]] && continue

  reflog=$(git -C "$dir" reflog -n "$REFLOG_DEPTH" 2>/dev/null) || true
  [[ -z "$reflog" ]] && continue

  if echo "$reflog" | grep -qE "reset.*--hard|reset: moving to origin/main|reset: moving to origin/"; then
    high_risk+=("$repo")
  elif echo "$reflog" | grep -q "reset: moving to origin"; then
    medium_risk+=("$repo")
  elif echo "$reflog" | grep -qi "reset"; then
    low_risk+=("$repo")
  fi
done

echo "=== HIGH RISK (reset --hard or reset to origin/main) ==="
if [[ ${#high_risk[@]} -eq 0 ]]; then
  echo "  (none)"
else
  for r in "${high_risk[@]}"; do
    echo "  $r"
    dir="$WORKSPACE_ROOT/$r"
    git -C "$dir" reflog -n "$REFLOG_DEPTH" 2>/dev/null | grep -E "reset.*--hard|reset: moving to origin" || true
    echo ""
  done
fi

echo ""
echo "=== MEDIUM RISK (reset to origin/*) ==="
if [[ ${#medium_risk[@]} -eq 0 ]]; then
  echo "  (none)"
else
  for r in "${medium_risk[@]}"; do
    echo "  $r"
  done
fi

echo ""
echo "=== LOW RISK (reset: moving to HEAD only — no-op) ==="
if [[ ${#low_risk[@]} -eq 0 ]]; then
  echo "  (none)"
else
  for r in "${low_risk[@]}"; do
    echo "  $r"
  done
fi

echo ""
echo "Summary: ${#high_risk[@]} high, ${#medium_risk[@]} medium, ${#low_risk[@]} low"
[[ ${#high_risk[@]} -gt 0 ]] && exit 1
exit 0
