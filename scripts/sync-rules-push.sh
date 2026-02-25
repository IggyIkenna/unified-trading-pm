#!/usr/bin/env bash
# sync-rules-push.sh — Push local .cursor/rules/ into the team repo
#
# Usage:
#   ./sync-rules-push.sh [--dry-run] [--commit "message"]
#
# NOTE: You rarely need to call this directly.
# unified-trading-pm/scripts/quickmerge.sh runs this automatically as Stage 0.
# Only use this standalone if you want to sync without committing.
#
# What it does:
#   Copies <workspace-root>/.cursor/rules/ → unified-trading-pm/cursor-rules/
#   Also syncs .cursorrules → cursor-configs/cursorrules
#   Also syncs *.code-workspace files → cursor-configs/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"

# shellcheck source=./_workspace-lib.sh
source "$SCRIPT_DIR/_workspace-lib.sh"

# ── Parse args ────────────────────────────────────────────────────────────────
DRY_RUN=false
COMMIT_MSG=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)  DRY_RUN=true; shift ;;
        --commit)   COMMIT_MSG="${2:-}"; shift 2 ;;
        *)          shift ;;
    esac
done

# ── Validate workspace ────────────────────────────────────────────────────────
echo ""
validate_workspace_structure || exit 1
echo ""

# ── Paths ─────────────────────────────────────────────────────────────────────
CURSOR_RULES_SRC="$WORKSPACE_ROOT/.cursor/rules"
CURSOR_RULES_DST="$PM_ROOT/cursor-rules"
CURSOR_CONFIGS_DST="$PM_ROOT/cursor-configs"

# ── Dry run ───────────────────────────────────────────────────────────────────
if [ "$DRY_RUN" = true ]; then
    echo "${YELLOW}[DRY RUN] Would sync:${NC}"
    echo "  $CURSOR_RULES_SRC → $CURSOR_RULES_DST"
    echo ""
    echo "Rules to copy:"
    find "$CURSOR_RULES_SRC" -maxdepth 1 -name "*.mdc" -print0 2>/dev/null | \
        xargs -0 -I{} basename {} | sort | sed 's/^/  - /'
    exit 0
fi

# ── Copy rules ────────────────────────────────────────────────────────────────
mkdir -p "$CURSOR_RULES_DST"
mkdir -p "$CURSOR_CONFIGS_DST"

RULE_COUNT=0
for f in "$CURSOR_RULES_SRC"/*.mdc; do
    [ -f "$f" ] || continue
    cp -f "$f" "$CURSOR_RULES_DST/"
    ((RULE_COUNT++)) || true
done

# Sync .cursorrules
if [ -f "$WORKSPACE_ROOT/.cursorrules" ]; then
    cp -f "$WORKSPACE_ROOT/.cursorrules" "$CURSOR_CONFIGS_DST/cursorrules"
fi

# Sync *.code-workspace
WORKSPACE_CONFIGS_SRC="$WORKSPACE_ROOT/.cursor/workspace-configs"
if [ -d "$WORKSPACE_CONFIGS_SRC" ]; then
    for f in "$WORKSPACE_CONFIGS_SRC"/*.code-workspace; do
        [ -f "$f" ] || continue
        cp -f "$f" "$CURSOR_CONFIGS_DST/"
    done
fi
# Also root-level .code-workspace files
find "$WORKSPACE_ROOT" -maxdepth 1 -name "*.code-workspace" \
    -exec cp -f {} "$CURSOR_CONFIGS_DST/" \; 2>/dev/null || true

update_last_sync

echo "${GREEN}✓ Synced $RULE_COUNT rules → $CURSOR_RULES_DST${NC}"

# Show what changed
echo ""
echo "${CYAN}Changes staged for commit:${NC}"
cd "$PM_ROOT"
git diff --stat cursor-rules/ cursor-configs/ .last-sync 2>/dev/null || true

# Commit if requested (standalone use only — quickmerge does its own commit)
if [ -n "$COMMIT_MSG" ]; then
    echo ""
    git add cursor-rules/ cursor-configs/ .last-sync 2>/dev/null || true
    git commit -m "$COMMIT_MSG" 2>/dev/null || echo "${YELLOW}Nothing new to commit.${NC}"
fi
