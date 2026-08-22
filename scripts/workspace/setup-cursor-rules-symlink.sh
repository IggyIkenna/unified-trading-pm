#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# setup-cursor-rules-symlink.sh — Point .cursor/rules/ at unified-trading-pm/.cursor/rules/
#
# After this, edits in .cursor/rules/ directly modify the PM repo's git-tracked files.
# No sync scripts needed — changes are committed with quickmerge like any other file.
#
# Usage: bash unified-trading-pm/scripts/workspace/setup-cursor-rules-symlink.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TARGET_DIR="$WORKSPACE_ROOT/unified-trading-pm/.cursor/rules"
SYMLINK_PATH="$WORKSPACE_ROOT/.cursor/rules"

# Ensure target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "[ERROR] Target directory not found: $TARGET_DIR"
    echo "  Is unified-trading-pm cloned?"
    exit 1
fi
echo "[OK] Target directory ready: $TARGET_DIR"

# If it's already a correct symlink, nothing to do
if [ -L "$SYMLINK_PATH" ]; then
    CURRENT_TARGET="$(readlink "$SYMLINK_PATH")"
    CANONICAL_TARGET="$(cd "$WORKSPACE_ROOT" && cd "$(dirname "$SYMLINK_PATH")" && cd "$CURRENT_TARGET" 2>/dev/null && pwd)" || true
    if [ "$CANONICAL_TARGET" = "$TARGET_DIR" ] || [ "$CURRENT_TARGET" = "$TARGET_DIR" ]; then
        echo "[SKIP] Already configured: .cursor/rules -> $TARGET_DIR"
        echo ""
        echo "Verification:"
        ls -la "$SYMLINK_PATH"
        echo ""
        RULE_COUNT=$(find "$TARGET_DIR" -maxdepth 1 -name "*.mdc" 2>/dev/null | wc -l | tr -d ' ')
        echo "Rule files: $RULE_COUNT .mdc files"
        exit 0
    fi
    rm "$SYMLINK_PATH"
    echo "[OK] Removed incorrect symlink, recreating..."
fi

# If it's a regular directory (old copy-based setup), migrate any local-only rules
if [ -d "$SYMLINK_PATH" ] && [ ! -L "$SYMLINK_PATH" ]; then
    echo "[MIGRATE] Found existing .cursor/rules/ directory (old copy-based setup)"

    # Copy any .mdc files that exist locally but not in the target
    local_only=0
    for f in "$SYMLINK_PATH"/*.mdc; do
        [ -f "$f" ] || continue
        fname="$(basename "$f")"
        if [ ! -f "$TARGET_DIR/$fname" ]; then
            cp "$f" "$TARGET_DIR/"
            echo "  [MOVED] $fname -> .cursor/rules/ (was local-only)"
            ((local_only++)) || true
        fi
    done
    if [ "$local_only" -gt 0 ]; then
        echo "  Migrated $local_only local-only rule(s) into .cursor/rules/"
    fi

    rm -rf "$SYMLINK_PATH"
    echo "[OK] Removed old directory"
fi

# Ensure .cursor exists
mkdir -p "$WORKSPACE_ROOT/.cursor"

# Create symlink
ln -s "../unified-trading-pm/.cursor/rules" "$SYMLINK_PATH"
echo "[OK] Created symlink: .cursor/rules -> ../unified-trading-pm/.cursor/rules"

# Verify
echo ""
echo "Verification:"
ls -la "$SYMLINK_PATH"
echo ""
RULE_COUNT=$(find "$TARGET_DIR" -maxdepth 1 -name "*.mdc" 2>/dev/null | wc -l | tr -d ' ')
echo "Rule files: $RULE_COUNT .mdc files"
