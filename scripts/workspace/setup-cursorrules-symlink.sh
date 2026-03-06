#!/usr/bin/env bash
# setup-cursorrules-symlink.sh — Create .cursorrules symlink at workspace root
#
# Workspace root rules are tracked in unified-trading-pm. This script creates
# a symlink so the root .cursorrules points to the PM template.
#
# Usage:
#   bash unified-trading-pm/scripts/workspace/setup-cursorrules-symlink.sh
#   (run from workspace root or any subdirectory)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPOS_DIR="$(cd "$PM_DIR/.." && pwd)"
CURSORRULES="${REPOS_DIR}/.cursorrules"
TARGET="unified-trading-pm/templates/workspace-root.cursorrules"
TARGET_ABS="${REPOS_DIR}/${TARGET}"

if [ ! -f "$TARGET_ABS" ]; then
  echo "Error: Template not found: $TARGET_ABS" >&2
  exit 1
fi

if [ -L "$CURSORRULES" ] && [ "$(readlink "$CURSORRULES")" = "$TARGET" ]; then
  echo "✓ .cursorrules symlink already correct"
  exit 0
fi

if [ -e "$CURSORRULES" ] && [ ! -L "$CURSORRULES" ]; then
  echo "Backing up existing .cursorrules to .cursorrules.bak"
  mv "$CURSORRULES" "${CURSORRULES}.bak"
fi

ln -sf "$TARGET" "$CURSORRULES"
echo "✓ Created .cursorrules → $TARGET"
