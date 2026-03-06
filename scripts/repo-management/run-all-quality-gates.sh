#!/usr/bin/env bash
# Run quality gates for all workspace repos in dependency order.
#
# Does NOT push. Precursor to quickmerge — validates lint, typecheck, unit tests
# across all repos before attempting sync/merge.
#
# Quality gates run with --no-fix (verify only, no auto-fix) for CI consistency.
# Act is not run (Act is in quickmerge, not quality-gates).
#
# Repos are processed in dependency order (topologicalOrder from workspace-manifest.json SSOT).
#
# Usage: bash run-all-quality-gates.sh [--dry-run] [--limit N] [--repo NAME]
#   --repo NAME   Run quality gates only for this repo
#
# Run from: workspace root
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh
#
# Or from PM repo:
#   bash scripts/repo-management/run-all-quality-gates.sh

set -euo pipefail

# Resolve workspace root from cwd (must run from workspace root)
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  echo "  cd /path/to/unified-trading-system-repos"
  echo "  bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh"
  exit 1
fi
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"

DRY_RUN=false
LIMIT=""
REPO_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --repo) REPO_FILTER="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# Build repo list in dependency order from manifest SSOT
if [[ -n "$REPO_FILTER" ]]; then
  REPOS=("$REPO_FILTER")
else
  ORDERED=($(jq -r '.topologicalOrder.levels[].repos[]' "$MANIFEST" 2>/dev/null))
  REPO_KEYS=($(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null))
  for r in "${REPO_KEYS[@]}"; do
    for o in "${ORDERED[@]}"; do [[ "$o" == "$r" ]] && break; done
    [[ "$o" != "$r" ]] && ORDERED+=("$r")
  done
  REPOS=("${ORDERED[@]}")
fi
[[ -n "$LIMIT" ]] && REPOS=("${REPOS[@]:0:$LIMIT}")

echo "Quality gates: ${#REPOS[@]} repos (dependency order)"
[[ "$DRY_RUN" = true ]] && echo "DRY RUN"
echo ""

ok=0
FAILED_REPOS=()
FAILED_REASONS=()
fail=0
skip=0

for repo in "${REPOS[@]}"; do
  dir="$WORKSPACE_ROOT/$repo"

  [[ ! -d "$dir" ]] || [[ ! -d "$dir/.git" ]] && continue

  if [[ "$DRY_RUN" = true ]]; then
    echo "  [dry] $repo"
    continue
  fi

  QG_SCRIPT="$dir/scripts/quality-gates.sh"
  if [[ ! -f "$QG_SCRIPT" ]]; then
    echo "  (skip) $repo — no scripts/quality-gates.sh"
    ((skip++))
    continue
  fi

  echo "----------------------------------------------------------------------"
  echo "  $repo"
  echo "----------------------------------------------------------------------"
  if (cd "$dir" && bash scripts/quality-gates.sh --no-fix 2>&1); then
    echo "  OK $repo"
    ((ok++))
  else
    FAILED_REPOS+=("$repo")
    FAILED_REASONS+=("quality gates failed")
    echo "  FAIL $repo"
    ((fail++))
  fi
  echo ""
done

echo "======================================================================"
echo "Done: $ok OK, $fail FAIL, $skip skipped"
if [[ $fail -gt 0 ]]; then
  echo ""
  echo "Failed repos:"
  for i in "${!FAILED_REPOS[@]}"; do
    echo "  - ${FAILED_REPOS[$i]}: ${FAILED_REASONS[$i]:-unknown}"
  done
  echo ""
  echo "Fix: cd <repo> && bash scripts/quality-gates.sh --no-fix"
  exit 1
fi
exit 0
