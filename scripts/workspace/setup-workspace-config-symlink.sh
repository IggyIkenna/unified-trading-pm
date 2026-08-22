#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
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

# Write the root workspace file as a REGULAR file with ROOT-RELATIVE folder paths — NOT a symlink.
# A symlink to the cursor-configs copy (whose folder paths are "../../<repo>", correct only when opened
# from cursor-configs/) breaks when VS Code/Cursor opens it via the root symlink: it resolves "../../"
# relative to the symlink's real target dir, so the folders map ABOVE the workspace root and Source
# Control reports "no folders containing Git repositories". A regular file with root-relative paths works
# however it is opened. SSOT: plans/active/issues/uv_pin_fleet_drift_2026_06_22.md (REL_TARGET retained
# for the canonical path reference: $REL_TARGET).
[ -L "$ROOT_WS" ] && rm -f "$ROOT_WS"   # drop any legacy symlink
sed -e 's#"path": "\.\./\.\./"#"path": "."#g' \
    -e 's#"path": "\.\./\.\./#"path": "#g' \
    "$TARGET_DIR/unified-trading-system-repos.code-workspace" > "$ROOT_WS"
echo "[OK] Wrote regular root workspace file (root-relative paths): unified-trading-system-repos.code-workspace"
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
