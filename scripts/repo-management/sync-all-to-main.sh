#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Sync all workspace repos to main via quickmerge (PR + auto-merge)
#
# Flow:
# 1. Ensure .gitignore has heavy-file exclusions (.coverage, .venv, node_modules, etc.)
# 2. git add -A (stage all local changes)
# 3. Fetch origin/main; if local is behind, merge. If merge conflicts → FAIL (abort, do not continue)
# 4. If local has commits ahead of origin: git reset --soft origin/main (convert to staged changes)
# 5. If there are changes: run quickmerge (creates PR, runs quality gates, enables auto-merge)
# 6. If quickmerge fails (quality gates, PR creation, or auto-merge): FAIL, report
#
# Repos are processed in dependency order (topologicalOrder from workspace-manifest.json SSOT)
# so dependencies are merged before dependents.
#
# Prerequisites: gh CLI authenticated; auto-merge enabled on repos.
# See: codex/08-workflows/ci-cd-flow.md
#
# Usage: bash sync-all-to-main.sh [--dry-run] [--limit N] [--repo NAME] [--filter PATTERN] [--dep-branch NAME]
#   --repo NAME       Sync only this repo (e.g. unified-api-contracts)
#   --filter PATTERN  Sync only repos matching glob (e.g. unified-*, *-service, execution-*)
#   --dep-branch NAME Pass to quickmerge when path deps have local changes (avoids DEPENDENCY CONFLICT)
# Run from: workspace root or unified-trading-pm/scripts/repo-management/

set -euo pipefail

# Resolve workspace root from cwd (must run from workspace root)
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  echo "  cd /path/to/unified-trading-system-repos"
  echo "  bash unified-trading-pm/scripts/repo-management/sync-all-to-main.sh"
  exit 1
fi
PM_ROOT="$WORKSPACE_ROOT/unified-trading-pm"
MANIFEST="$PM_ROOT/workspace-manifest.json"


GITIGNORE_BLOCK='
# Heavy/build artifacts (sync-all-to-main)
.coverage
.coverage.*
htmlcov/
.venv/
venv/
node_modules/
__pycache__/
.DS_Store
dist/
build/
.pytest_cache/
.ruff_cache/
'

DRY_RUN=false
LIMIT=""
REPO_FILTER=""
FILTER_PATTERN=""
DEP_BRANCH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --repo) REPO_FILTER="$2"; shift 2 ;;
    --filter) FILTER_PATTERN="$2"; shift 2 ;;
    --dep-branch) DEP_BRANCH="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# Build repo list in dependency order from manifest SSOT (topologicalOrder)
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
# Apply glob filter if set (e.g. unified-*, *-service)
if [[ -n "$FILTER_PATTERN" ]]; then
  FILTERED=()
  for r in "${REPOS[@]}"; do
    [[ "$r" == $FILTER_PATTERN ]] && FILTERED+=("$r")
  done
  REPOS=("${FILTERED[@]}")
fi
[[ -n "$LIMIT" ]] && REPOS=("${REPOS[@]:0:$LIMIT}")

echo "Sync to main: ${#REPOS[@]} repos (dependency order, quickmerge flow)"
[[ "$DRY_RUN" = true ]] && echo "DRY RUN"
[[ -n "$FILTER_PATTERN" ]] && echo "Filter: $FILTER_PATTERN"
[[ -n "$DEP_BRANCH" ]] && echo "Dep branch: $DEP_BRANCH (will pass to quickmerge)"
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

  (cd "$dir" && git checkout main 2>/dev/null) || true

  if [[ -f "$dir/.gitignore" ]]; then
    for pat in ".coverage" ".venv/" "node_modules/" "__pycache__/" ".DS_Store"; do
      grep -qF "$pat" "$dir/.gitignore" 2>/dev/null || echo "$pat" >> "$dir/.gitignore"
    done
  else
    echo -e "$GITIGNORE_BLOCK" >> "$dir/.gitignore"
  fi

  (cd "$dir" && git add -A 2>/dev/null) || true

  if ! (cd "$dir" && git rev-parse --verify main >/dev/null 2>&1); then
    echo "  (skip) $repo — no main branch"
    ((skip++))
    continue
  fi

  # Fetch and merge origin/main — if we are behind, pull. Conflict -> FAIL
  if ! (cd "$dir" && git fetch origin main 2>/dev/null); then
    FAILED_REPOS+=("$repo")
    FAILED_REASONS+=("fetch failed")
    echo "  FAIL $repo — fetch origin failed"
    ((fail++))
    continue
  fi

  if ! (cd "$dir" && git merge origin/main --no-edit 2>/dev/null); then
    (cd "$dir" && git merge --abort 2>/dev/null) || true
    FAILED_REPOS+=("$repo")
    FAILED_REASONS+=("merge conflict with origin/main")
    echo "  FAIL $repo — merge conflicts with origin/main; resolve manually first"
    ((fail++))
    continue
  fi

  # If we have commits ahead of origin, reset to staged changes so quickmerge can commit
  if (cd "$dir" && git rev-list origin/main..HEAD --quiet 2>/dev/null); then
    (cd "$dir" && git reset --soft origin/main 2>/dev/null) || true
  fi

  # Skip if nothing to commit
  if (cd "$dir" && [[ -z "$(git status --porcelain 2>/dev/null)" ]] ); then
    echo "  OK $repo (no changes)"
    ((ok++))
    continue
  fi

  # Run quickmerge
  QM_SCRIPT="$dir/scripts/quickmerge.sh"
  if [[ ! -f "$QM_SCRIPT" ]]; then
    QM_SCRIPT="$PM_ROOT/scripts/quickmerge.sh"
  fi
  if [[ ! -f "$QM_SCRIPT" ]]; then
    FAILED_REPOS+=("$repo")
    FAILED_REASONS+=("no quickmerge.sh")
    echo "  FAIL $repo — scripts/quickmerge.sh not found"
    ((fail++))
    continue
  fi

  QM_ARGS=("chore: sync local changes")
  [[ -n "$DEP_BRANCH" ]] && QM_ARGS+=("--dep-branch" "$DEP_BRANCH")
  QM_OUT=$(mktemp)
  if (cd "$dir" && bash "$QM_SCRIPT" "${QM_ARGS[@]}" > "$QM_OUT" 2>&1); then
    echo "  OK $repo"
    ((ok++))
  else
    FAILED_REPOS+=("$repo")
    FAILED_REASONS+=("quickmerge failed (quality gates or PR auto-merge)")
    echo "  FAIL $repo — quickmerge failed"
    echo "  Last 60 lines of quickmerge output:"
    tail -60 "$QM_OUT" | sed 's/^/    /'
    ((fail++))
  fi
  rm -f "$QM_OUT"
done

echo ""
echo "Done: $ok OK, $fail FAIL, $skip skipped"
if [[ $fail -gt 0 ]]; then
  echo "Failed repos:"
  for i in "${!FAILED_REPOS[@]}"; do
    echo "  - ${FAILED_REPOS[$i]}: ${FAILED_REASONS[$i]:-unknown}"
  done
  echo ""
  echo "Resolve: fix conflicts manually, or run quality gates locally, then re-run."
  exit 1
fi
exit 0
