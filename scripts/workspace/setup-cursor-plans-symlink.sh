#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TARGET_DIR="$WORKSPACE_ROOT/unified-trading-pm/plans/cursor-plans"
SYMLINK_PATH="$WORKSPACE_ROOT/.cursor/plans"

# Always ensure target directory exists
mkdir -p "$TARGET_DIR"
echo "[OK] Target directory ready: $TARGET_DIR"

if [ -L "$SYMLINK_PATH" ]; then
  # It's a symlink - check if it points to the right place
  CURRENT_TARGET="$(readlink "$SYMLINK_PATH")"
  CANONICAL_TARGET="$(cd "$WORKSPACE_ROOT" && cd "$(dirname "$SYMLINK_PATH")" && cd "$CURRENT_TARGET" 2>/dev/null && pwd)" || true
  if [ "$CANONICAL_TARGET" = "$TARGET_DIR" ] || [ "$CURRENT_TARGET" = "$TARGET_DIR" ]; then
    echo "[SKIP] Already configured: .cursor/plans -> $TARGET_DIR"
    echo ""
    echo "Verification:"
    ls -la "$SYMLINK_PATH"
    echo ""
    echo "Plan files:"
    ls -la "$TARGET_DIR"/*.md 2>/dev/null || echo "(none)"
    exit 0
  fi
  rm "$SYMLINK_PATH"
  echo "[OK] Removed incorrect symlink, recreating..."
fi

if [ -d "$SYMLINK_PATH" ]; then
  # It's a regular directory (not a symlink)
  if [ -n "$(find "$SYMLINK_PATH" -maxdepth 1 -name "*.md" 2>/dev/null | head -1)" ]; then
    echo "[MOVE] Moving .md files to target..."
    for f in "$SYMLINK_PATH"/*.md; do
      [ -e "$f" ] && mv "$f" "$TARGET_DIR/"
    done
  fi
  # Move any remaining files
  if [ -n "$(find "$SYMLINK_PATH" -maxdepth 1 -mindepth 1 2>/dev/null | head -1)" ]; then
    echo "[MOVE] Moving remaining files to target..."
    for f in "$SYMLINK_PATH"/*; do
      [ -e "$f" ] && mv "$f" "$TARGET_DIR/"
    done
  fi
  rmdir "$SYMLINK_PATH" || {
    echo "[ERROR] Could not remove directory - may have unexpected contents"
    exit 1
  }
  echo "[OK] Removed old directory"
fi

# Ensure .cursor exists
if [ ! -d "$WORKSPACE_ROOT/.cursor" ]; then
  mkdir -p "$WORKSPACE_ROOT/.cursor"
  echo "[OK] Created .cursor directory"
fi

# Create symlink
ln -s "../unified-trading-pm/plans/cursor-plans" "$SYMLINK_PATH"
echo "[OK] Created symlink: .cursor/plans -> ../unified-trading-pm/plans/cursor-plans"

# Ensure cursor-plans and active in repo symlink to .cursor/plans (so Cursor can execute)
PM_PLANS="$WORKSPACE_ROOT/unified-trading-pm/plans"
for name in cursor-plans active; do
  p="$PM_PLANS/$name"
  if [ -L "$p" ]; then
    t=$(readlink "$p")
    if [ "$t" != "../../.cursor/plans" ]; then
      rm "$p" && ln -s ../../.cursor/plans "$p" && echo "[OK] $name -> ../../.cursor/plans"
    fi
  elif [ -d "$p" ] && [ "$name" = "cursor-plans" ]; then
    echo "[OK] cursor-plans is real directory (canonical)"
  elif [ ! -e "$p" ]; then
    ln -s ../../.cursor/plans "$p" && echo "[OK] Created $name -> ../../.cursor/plans"
  fi
done

# Verify
echo ""
echo "Verification:"
ls -la "$SYMLINK_PATH"
echo ""
echo "Plan files:"
ls -la "$TARGET_DIR"/*.md 2>/dev/null || echo "(none)"
