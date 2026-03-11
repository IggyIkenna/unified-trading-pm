#!/usr/bin/env bash
# setup-cursor-rules-symlink.sh — No-op. Rules now live in unified-trading-pm/.cursor/rules/
#
# Cursor reads unified-trading-pm/.cursor/rules/ directly when the workspace is open.
# No symlinks are needed. This script is kept for backward compatibility only.
#
# Usage: bash unified-trading-pm/scripts/workspace/setup-cursor-rules-symlink.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RULES_DIR="$WORKSPACE_ROOT/unified-trading-pm/.cursor/rules"

if [ -d "$RULES_DIR" ]; then
    RULE_COUNT=$(find "$RULES_DIR" -name "*.mdc" | wc -l | tr -d ' ')
    echo "[OK] Rules live in: $RULES_DIR"
    echo "     $RULE_COUNT .mdc files — no symlink setup needed."
else
    echo "[ERROR] Rules directory not found: $RULES_DIR"
    echo "  Is unified-trading-pm cloned?"
    exit 1
fi
