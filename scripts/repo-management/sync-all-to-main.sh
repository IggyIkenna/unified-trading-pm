#!/usr/bin/env bash
# Sync all workspace repos to main: commit local changes, merge origin/main, push
#
# 1. Ensures .gitignore has heavy-file exclusions (.coverage, .venv, node_modules, etc.)
# 2. git add -A (stages all local changes, respects .gitignore)
# 3. git commit if there are staged changes
# 4. git fetch origin main && git merge origin/main — keep non-conflicting remote changes
# 5. If merge conflicts: abort, log error, FAIL (do not push)
# 6. git push origin main
#
# Safe to run periodically in background (e.g. cron, launchd).
#
# Usage: bash sync-all-to-main.sh [--dry-run] [--limit N]
# Run from: workspace root or unified-trading-pm/scripts/repo-management/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
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

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --limit) LIMIT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

REPOS=($(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null))
[[ -n "$LIMIT" ]] && REPOS=("${REPOS[@]:0:$LIMIT}")

echo "Sync to main: ${#REPOS[@]} repos"
[[ "$DRY_RUN" = true ]] && echo "DRY RUN"
echo ""

ok=0
fail=0
skip=0

for repo in "${REPOS[@]}"; do
  dir="$WORKSPACE_ROOT/$repo"

  [[ "$repo" = "execution-visualizer-ui" ]] && dir="$WORKSPACE_ROOT/execution-analytics-ui"
  [[ ! -d "$dir" ]] && echo "  (skip) $repo — not in workspace" && ((skip++)) && continue
  [[ ! -d "$dir/.git" ]] && echo "  (skip) $repo — not a git repo" && ((skip++)) && continue

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

  (cd "$dir" && git add -A 2>/dev/null || true)
  (cd "$dir" && [[ -n "$(git status --porcelain 2>/dev/null)" ]] && git commit --no-verify -m "chore: sync local changes" 2>/dev/null) || true
  if ! (cd "$dir" && git rev-parse --verify main >/dev/null 2>&1); then
    echo "  (skip) $repo — no main branch"
    ((skip++))
    continue
  fi
  # Fetch and merge origin/main — keep non-conflicting remote changes
  if ! (cd "$dir" && git fetch origin main 2>/dev/null); then
    echo "  FAIL $repo — fetch origin failed"
    ((fail++))
    continue
  fi
  if ! (cd "$dir" && git merge origin/main --no-edit 2>/dev/null); then
    (cd "$dir" && git merge --abort 2>/dev/null) || true
    echo "  FAIL $repo — merge conflicts with origin/main; pull and resolve manually first"
    ((fail++))
    continue
  fi
  if (cd "$dir" && git push origin main 2>/dev/null); then
    echo "  OK $repo"
    ((ok++))
  else
    echo "  FAIL $repo — push failed"
    ((fail++))
  fi
done

echo ""
echo "Done: $ok OK, $fail FAIL, $skip skipped"
[[ $fail -gt 0 ]] && exit 1
exit 0
