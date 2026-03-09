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
    ln -s "../unified-trading-pm/cursor-configs" "$SYMLINK_PATH"
    echo "[OK] Recreated symlink: .cursor/workspace-configs -> cursor-configs"
  fi
elif [ -d "$SYMLINK_PATH" ]; then
  echo "[REPLACE] Removing .cursor/workspace-configs (canonical lives in cursor-configs)"
  rm -rf "$SYMLINK_PATH"
  ln -s "../unified-trading-pm/cursor-configs" "$SYMLINK_PATH"
  echo "[OK] Replaced with symlink: .cursor/workspace-configs -> cursor-configs"
else
  mkdir -p "$(dirname "$SYMLINK_PATH")"
  ln -s "../unified-trading-pm/cursor-configs" "$SYMLINK_PATH"
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
  else
    rm "$ROOT_WS"
    ln -s "$REL_TARGET" "$ROOT_WS"
    echo "[OK] Recreated symlink: unified-trading-system-repos.code-workspace -> $REL_TARGET"
  fi
elif [ -f "$ROOT_WS" ]; then
  rm -f "$ROOT_WS"
  ln -s "$REL_TARGET" "$ROOT_WS"
  echo "[OK] Replaced regular file with symlink: unified-trading-system-repos.code-workspace -> $REL_TARGET"
else
  ln -s "$REL_TARGET" "$ROOT_WS"
  echo "[OK] Created symlink: unified-trading-system-repos.code-workspace -> $REL_TARGET"
fi
ls -la "$ROOT_WS"

# 3. Symlink root .cursorignore -> unified-trading-pm/cursor-configs/cursorignore
CURSORIGNORE_SYMLINK="$WORKSPACE_ROOT/.cursorignore"
CURSORIGNORE_TARGET="unified-trading-pm/cursor-configs/cursorignore"
CURSORIGNORE_ABS="$WORKSPACE_ROOT/unified-trading-pm/cursor-configs/cursorignore"

if [ ! -f "$CURSORIGNORE_ABS" ]; then
  echo "[ERROR] Canonical cursorignore not found: $CURSORIGNORE_ABS"
  exit 1
fi

if [ -L "$CURSORIGNORE_SYMLINK" ]; then
  CURRENT="$(readlink "$CURSORIGNORE_SYMLINK")"
  if [ "$CURRENT" = "$CURSORIGNORE_TARGET" ]; then
    echo "[SKIP] Already configured: .cursorignore -> $CURSORIGNORE_TARGET"
  else
    rm "$CURSORIGNORE_SYMLINK"
    ln -s "$CURSORIGNORE_TARGET" "$CURSORIGNORE_SYMLINK"
    echo "[OK] Recreated symlink: .cursorignore -> $CURSORIGNORE_TARGET"
  fi
elif [ -f "$CURSORIGNORE_SYMLINK" ]; then
  rm "$CURSORIGNORE_SYMLINK"
  ln -s "$CURSORIGNORE_TARGET" "$CURSORIGNORE_SYMLINK"
  echo "[OK] Replaced regular file with symlink: .cursorignore -> $CURSORIGNORE_TARGET"
else
  ln -s "$CURSORIGNORE_TARGET" "$CURSORIGNORE_SYMLINK"
  echo "[OK] Created symlink: .cursorignore -> $CURSORIGNORE_TARGET"
fi

echo ""
echo "Open workspace: File > Open Workspace from File > .cursor/workspace-configs/unified-trading-system-repos.code-workspace"
echo "Or: unified-trading-system-repos.code-workspace (at root)"
