#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Installs git pre-push hook in all workspace repos.
# Run from WORKSPACE_ROOT.
# Usage: bash unified-trading-pm/scripts/workspace/install-hooks.sh [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PM_DIR="$WORKSPACE_ROOT/unified-trading-pm"
MANIFEST="$PM_DIR/workspace-manifest.json"
HOOK_SOURCE="$PM_DIR/scripts/hooks/pre-push"
DRY_RUN=false

for arg in "$@"; do
  if [ "$arg" = "--dry-run" ]; then DRY_RUN=true; fi
done

if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: workspace-manifest.json not found at $MANIFEST"
  exit 1
fi

if [ ! -f "$HOOK_SOURCE" ]; then
  echo "ERROR: pre-push hook source not found at $HOOK_SOURCE"
  exit 1
fi

echo "Installing pre-push hook in all workspace repos..."
REPOS=$(python3 -c "import json; m=json.load(open('$MANIFEST')); print('\n'.join(m.get('repositories', {}).keys()))")

INSTALLED=0
SKIPPED=0
while IFS= read -r repo; do
  [ -z "$repo" ] && continue
  REPO_DIR="$WORKSPACE_ROOT/$repo"
  GIT_DIR="$REPO_DIR/.git"

  if [ ! -d "$GIT_DIR" ]; then
    echo "  SKIP: $repo (no .git directory)"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  HOOK_DEST="$GIT_DIR/hooks/pre-push"
  if [ "$DRY_RUN" = true ]; then
    echo "  DRY-RUN: would install hook in $repo"
  else
    cp "$HOOK_SOURCE" "$HOOK_DEST"
    chmod +x "$HOOK_DEST"
    echo "  OK: $repo"
    INSTALLED=$((INSTALLED + 1))
  fi
done <<< "$REPOS"

echo ""
echo "Done. Installed: $INSTALLED, Skipped: $SKIPPED"
