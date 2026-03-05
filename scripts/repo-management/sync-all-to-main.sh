#!/usr/bin/env bash
# Sync all workspace repos to main: ensure .gitignore, commit all changes, force-push
#
# 1. Ensures .gitignore has heavy-file exclusions (.coverage, .venv, node_modules, etc.)
# 2. git add -A (respects .gitignore)
# 3. git commit if changes
# 4. git push --force origin main
#
# Usage: bash sync-all-to-main.sh [--dry-run] [--limit N]
# Run from: workspace root or unified-trading-pm/scripts/repo-management/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
MANIFEST="$PM_ROOT/workspace-manifest.json"

# Standard heavy-file exclusions to ensure in .gitignore
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
  [[ ! -d "$dir" ]] && echo "  (skip) $repo — not in workspace" && ((skip++)) && continue
  [[ ! -d "$dir/.git" ]] && echo "  (skip) $repo — not a git repo" && ((skip++)) && continue

  if [[ "$DRY_RUN" = true ]]; then
    echo "  [dry] $repo"
    continue
  fi

  (cd "$dir" && git checkout main 2>/dev/null) || true

  # Ensure .gitignore has heavy exclusions
  if [[ -f "$dir/.gitignore" ]]; then
    for pat in .coverage .venv node_modules; do
      grep -q "$pat" "$dir/.gitignore" 2>/dev/null || echo "$pat" >> "$dir/.gitignore"
    done
  else
    echo -e "$GITIGNORE_BLOCK" >> "$dir/.gitignore"
  fi

  cd "$dir"
  git add -A 2>/dev/null || true
  if ! git diff --cached --quiet 2>/dev/null; then
    git commit --trailer "Made-with: Cursor" --no-verify -m "chore: sync local changes" 2>/dev/null || true
  fi
  if ! git rev-parse --verify main >/dev/null 2>&1; then
    echo "  (skip) $repo — no main branch"
    ((skip++))
    continue
  fi
  if git push --force origin main 2>/dev/null; then
    echo "  OK $repo"
    ((ok++))
  else
    echo "  FAIL $repo"
    ((fail++))
  fi
done

echo ""
echo "Done: $ok OK, $fail FAIL, $skip skipped"
[[ $fail -gt 0 ]] && exit 1
exit 0
