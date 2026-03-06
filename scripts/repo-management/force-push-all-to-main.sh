#!/usr/bin/env bash
# Force-push local main to origin/main for all workspace repos
#
# WARNING: Overwrites remote main with local state. Branch protection MUST be disabled.
#
# Usage:
#   bash force-push-all-to-main.sh                    # All repos
#   bash force-push-all-to-main.sh --dry-run          # Show what would run, no pushes
#   bash force-push-all-to-main.sh --limit 2          # First 2 repos only (for testing)
#   bash force-push-all-to-main.sh --repos "repo1 repo2"  # Specific repos only
#
# Requires: workspace-manifest.json, git, gh (optional for auth)
# Run from: unified-trading-pm/scripts/repo-management/ or workspace root

set -euo pipefail

# Resolve workspace root from cwd (must run from workspace root)
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  echo "  cd /path/to/unified-trading-system-repos"
  echo "  bash <script>"
  exit 1
fi
PM_ROOT="$WORKSPACE_ROOT/unified-trading-pm"
MANIFEST="$PM_ROOT/workspace-manifest.json"

DRY_RUN=false
LIMIT=""
REPOS_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    --repos)
      REPOS_FILTER="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing $MANIFEST"
  exit 1
fi

if [[ -n "$REPOS_FILTER" ]]; then
  REPOS=($REPOS_FILTER)
else
  REPOS=($(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null))
fi

if [[ -n "$LIMIT" ]]; then
  REPOS=("${REPOS[@]:0:$LIMIT}")
fi

echo "Force-push to main: ${#REPOS[@]} repos"
[[ "$DRY_RUN" = true ]] && echo "DRY RUN — no pushes will be made"
echo ""

failed=0
for repo in "${REPOS[@]}"; do
  dir="$WORKSPACE_ROOT/$repo"
  if [[ ! -d "$dir" ]]; then
    echo "  (skip) $repo — not in workspace"
    continue
  fi
  if [[ ! -d "$dir/.git" ]]; then
    echo "  (skip) $repo — not a git repo"
    continue
  fi

  # Ensure we're on main before force-push
  (cd "$dir" && git checkout main 2>/dev/null) || true

  if [[ "$DRY_RUN" = true ]]; then
    echo "  [dry] $repo"
    continue
  fi

  echo -n "  $repo ... "
  if (cd "$dir" && git push --force origin main 2>&1); then
    echo "OK"
  else
    echo "FAIL"
    ((failed++)) || true
  fi
done

echo ""
[[ $failed -gt 0 ]] && echo "Failed: $failed" && exit 1
echo "Done."
exit 0
