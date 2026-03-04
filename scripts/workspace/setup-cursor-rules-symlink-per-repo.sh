#!/usr/bin/env bash
# setup-cursor-rules-symlink-per-repo.sh — Point each repo's .cursor/rules at unified-trading-pm/cursor-rules
#
# When a background agent opens a SINGLE repo (not the full workspace), it needs cursor rules.
# This creates repo/.cursor/rules -> ../unified-trading-pm/cursor-rules for every repo.
# Requires repos to be siblings of unified-trading-pm (workspace layout).
#
# Run AFTER setup-cursor-rules-symlink.sh (workspace root). Safe to re-run.
#
# Usage: bash unified-trading-pm/scripts/workspace/setup-cursor-rules-symlink-per-repo.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PM_DIR="$WORKSPACE_ROOT/unified-trading-pm"
TARGET_REL="../../unified-trading-pm/cursor-rules"

if [ ! -d "$PM_DIR/cursor-rules" ]; then
    echo "[ERROR] unified-trading-pm/cursor-rules not found"
    exit 1
fi

# Repos from workspace-manifest.json (exclude unified-trading-pm)
REPOS=()
if [ -f "$PM_DIR/workspace-manifest.json" ]; then
    REPOS=($(python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
for r in sorted(d.get('repositories', {}).keys()):
    if r != 'unified-trading-pm':
        print(r)
" "$PM_DIR/workspace-manifest.json" 2>/dev/null || true))
fi

# Fallback if python fails
[ ${#REPOS[@]} -eq 0 ] && REPOS=(unified-trading-codex instruments-service unified-api-contracts)

echo "[OK] Creating .cursor/rules symlinks in ${#REPOS[@]} repos..."
CREATED=0
SKIPPED=0

for repo in "${REPOS[@]}"; do
    REPO_DIR="$WORKSPACE_ROOT/$repo"
    RULES_LINK="$REPO_DIR/.cursor/rules"

    if [ ! -d "$REPO_DIR" ]; then
        continue
    fi

    mkdir -p "$REPO_DIR/.cursor"

    if [ -L "$RULES_LINK" ]; then
        current="$(readlink "$RULES_LINK")"
        if [ "$current" = "$TARGET_REL" ] || [ "$current" = "../../unified-trading-pm/cursor-rules" ]; then
            ((SKIPPED++)) || true
            continue
        fi
        rm "$RULES_LINK"
    fi

    if [ -d "$RULES_LINK" ] && [ ! -L "$RULES_LINK" ]; then
        rm -rf "$RULES_LINK"
    fi

    ln -sf "$TARGET_REL" "$RULES_LINK"
    echo "  [OK] $repo/.cursor/rules -> $TARGET_REL"
    ((CREATED++)) || true
done

echo ""
echo "Done: $CREATED created, $SKIPPED already correct"
