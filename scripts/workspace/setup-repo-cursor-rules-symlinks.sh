#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# setup-repo-cursor-rules-symlinks.sh — Replace per-repo .cursor/rules copies with symlinks
#
# P0 of CONTEXT_BLOAT_REMEDIATION: each repo's .cursor/rules points at unified-trading-pm/.cursor/rules.
# Edits in .cursor/rules/ directly modify PM's git-tracked files. No sync needed.
#
# Usage: bash unified-trading-pm/scripts/workspace/setup-repo-cursor-rules-symlinks.sh
# Run from workspace root (unified-trading-system-repos).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TARGET_ABS="$WORKSPACE_ROOT/unified-trading-pm/.cursor/rules"
# Relative from repo/.cursor/ to unified-trading-pm/.cursor/rules
TARGET_REL="../../unified-trading-pm/.cursor/rules"

REPOS=(
  batch-audit-ui
  unified-api-contracts
  features-sports-service
  unified-trading-ui-auth
  deployment-api
  deployment-service
  system-integration-tests
)

if [ ! -d "$TARGET_ABS" ]; then
  echo "[ERROR] Target not found: $TARGET_ABS"
  exit 1
fi

for repo in "${REPOS[@]}"; do
  REPO_DIR="$WORKSPACE_ROOT/$repo"
  RULES_PATH="$REPO_DIR/.cursor/rules"

  if [ ! -d "$REPO_DIR" ]; then
    echo "[SKIP] $repo: repo not found"
    continue
  fi

  if [ -L "$RULES_PATH" ]; then
    current="$(readlink "$RULES_PATH")"
    if [ "$current" = "$TARGET_REL" ]; then
      echo "[OK] $repo: already symlink"
      continue
    fi
    rm "$RULES_PATH"
    echo "[OK] $repo: removed incorrect symlink"
  fi

  if [ -d "$RULES_PATH" ] && [ ! -L "$RULES_PATH" ]; then
    echo "[MIGRATE] $repo: replacing real .cursor/rules with symlink"
    local_only=0
    for f in "$RULES_PATH"/*.mdc; do
      [ -f "$f" ] || continue
      fname="$(basename "$f")"
      if [ ! -f "$TARGET_ABS/$fname" ]; then
        cp "$f" "$TARGET_ABS/"
        echo "  [MOVED] $fname -> .cursor/rules/"
        ((local_only++)) || true
      fi
    done
    rm -rf "$RULES_PATH"
  fi

  if [ ! -e "$RULES_PATH" ]; then
    mkdir -p "$REPO_DIR/.cursor"
    ln -s "$TARGET_REL" "$RULES_PATH"
    echo "[OK] $repo: created symlink"
  fi
done

echo ""
echo "Done. Verifying:"
for repo in "${REPOS[@]}"; do
  p="$WORKSPACE_ROOT/$repo/.cursor/rules"
  if [ -L "$p" ]; then
    echo "  $repo: $(readlink "$p")"
  fi
done
