#!/usr/bin/env bash
# setup-workspace-config-symlink.sh — Point root workspace file at your resolved config
# The file you open at repo root is a symlink to .cursor/workspace-configs/... (with your path
# injected). Templates in git use __WORKSPACE_ROOT__; inject-workspace-paths.sh writes your path
# into .cursor/workspace-configs/ so no one's path gets committed.
#
# Usage: bash unified-trading-pm/scripts/setup-workspace-config-symlink.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RESOLVED_FILE="$REPO_ROOT/.cursor/workspace-configs/unified-trading-system-repos.code-workspace"
SYMLINK_PATH="$REPO_ROOT/unified-trading-system-repos.code-workspace"
REL_TARGET=".cursor/workspace-configs/unified-trading-system-repos.code-workspace"
PM_CONFIGS="$REPO_ROOT/unified-trading-pm/cursor-configs"

# Ensure resolved file exists: copy template from PM then inject local path
mkdir -p "$REPO_ROOT/.cursor/workspace-configs"
if [ -f "$PM_CONFIGS/unified-trading-system-repos.code-workspace" ]; then
    cp -f "$PM_CONFIGS/unified-trading-system-repos.code-workspace" "$RESOLVED_FILE"
    PARENT_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
    bash "$SCRIPT_DIR/inject-workspace-paths.sh" "${UNIFIED_TRADING_WORKSPACE_ROOT:-$PARENT_ROOT}"
fi

if [ ! -f "$RESOLVED_FILE" ]; then
    echo "Error: Resolved file not found: $RESOLVED_FILE (run sync-rules-pull or setup-workspace-root first?)"
    exit 1
fi

if [ -L "$SYMLINK_PATH" ]; then
    CURRENT="$(readlink "$SYMLINK_PATH")"
    if [ "$CURRENT" = "$REL_TARGET" ]; then
        echo "[OK] Symlink already correct: unified-trading-system-repos.code-workspace -> $REL_TARGET"
        ls -la "$SYMLINK_PATH"
        exit 0
    fi
    rm "$SYMLINK_PATH"
    echo "[OK] Removed incorrect symlink, recreating..."
fi

if [ -f "$SYMLINK_PATH" ] && [ ! -L "$SYMLINK_PATH" ]; then
    rm -f "$SYMLINK_PATH"
fi

ln -s "$REL_TARGET" "$SYMLINK_PATH"
echo "[OK] Symlink created: unified-trading-system-repos.code-workspace -> $REL_TARGET"
ls -la "$SYMLINK_PATH"
