#!/usr/bin/env bash
# setup-workspace-config-symlink.sh — Symlink .cursor/workspace-configs to PM cursor-configs
# Canonical workspace configs live in unified-trading-pm/cursor-configs/. All paths use
# ${workspaceFolder} for portability. Root workspace file symlinks to the canonical.
#
# Usage: bash unified-trading-pm/scripts/workspace/setup-workspace-config-symlink.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TARGET_DIR="$WORKSPACE_ROOT/unified-trading-pm/cursor-configs"
SYMLINK_PATH="$WORKSPACE_ROOT/.cursor/workspace-configs"
ROOT_WS="$WORKSPACE_ROOT/unified-trading-system-repos.code-workspace"
REL_TARGET=".cursor/workspace-configs/unified-trading-system-repos.code-workspace"

# 1. Symlink .cursor/workspace-configs -> unified-trading-pm/cursor-configs
if [ -L "$SYMLINK_PATH" ]; then
  CURRENT="$(readlink "$SYMLINK_PATH")"
  RESOLVED="$(cd "$WORKSPACE_ROOT" && cd "$(dirname "$SYMLINK_PATH")" && cd "$CURRENT" 2>/dev/null && pwd)" || true
  if [ "$RESOLVED" = "$TARGET_DIR" ]; then
    echo "[SKIP] Already configured: .cursor/workspace-configs -> cursor-configs"
  else
    rm "$SYMLINK_PATH"
    ln -s "$TARGET_DIR" "$SYMLINK_PATH"
    echo "[OK] Recreated symlink: .cursor/workspace-configs -> cursor-configs"
  fi
elif [ -d "$SYMLINK_PATH" ]; then
  echo "[REPLACE] Removing .cursor/workspace-configs (canonical lives in cursor-configs)"
  rm -rf "$SYMLINK_PATH"
  ln -s "$TARGET_DIR" "$SYMLINK_PATH"
  echo "[OK] Replaced with symlink: .cursor/workspace-configs -> cursor-configs"
else
  mkdir -p "$(dirname "$SYMLINK_PATH")"
  ln -s "$TARGET_DIR" "$SYMLINK_PATH"
  echo "[OK] Created symlink: .cursor/workspace-configs -> cursor-configs"
fi

# 2. Symlink root workspace file -> .cursor/workspace-configs/unified-trading-system-repos.code-workspace
if [ ! -f "$TARGET_DIR/unified-trading-system-repos.code-workspace" ]; then
  echo "[ERROR] Canonical workspace not found: $TARGET_DIR/unified-trading-system-repos.code-workspace"
  exit 1
fi

if [ -L "$ROOT_WS" ]; then
  CURRENT="$(readlink "$ROOT_WS")"
  if [ "$CURRENT" = "$REL_TARGET" ]; then
    echo "[SKIP] Root symlink already correct: unified-trading-system-repos.code-workspace -> $REL_TARGET"
    ls -la "$ROOT_WS"
    exit 0
  fi
  rm "$ROOT_WS"
  echo "[OK] Removed incorrect symlink, recreating..."
fi

if [ -f "$ROOT_WS" ] && [ ! -L "$ROOT_WS" ]; then
  rm -f "$ROOT_WS"
fi

ln -s "$REL_TARGET" "$ROOT_WS"
echo "[OK] Symlink created: unified-trading-system-repos.code-workspace -> $REL_TARGET"
ls -la "$ROOT_WS"
echo ""
echo "Open workspace: File > Open Workspace from File > .cursor/workspace-configs/unified-trading-system-repos.code-workspace"
echo "Or: unified-trading-system-repos.code-workspace (at root)"
