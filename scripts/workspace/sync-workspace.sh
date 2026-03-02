#!/usr/bin/env bash
# sync-workspace.sh - Full workspace sync (pull latest rules + workspace configs)
# Usage: ./sync-workspace.sh [--push | --pull] [--dry-run]
#
# Default (no flags): shows current diff between local .cursor/rules/ and repo cursor-rules/
# --pull: runs sync-rules-pull.sh (updates your local rules from repo)
# --push: runs sync-rules-push.sh (pushes your local rules to repo)
# --dry-run: preview only, no changes

set -euo pipefail

# Resolve paths (must come before sourcing _workspace-lib.sh which uses PM_ROOT/WORKSPACE_ROOT)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"

# Source shared workspace library (provides colors, path helpers, rule diff functions)
source "$SCRIPT_DIR/../_workspace-lib.sh"

# Additional color not in _workspace-lib.sh
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
    CYAN=$(tput setaf 6)
else
    CYAN=""
fi
export CYAN

CURSOR_RULES_LOCAL="$WORKSPACE_ROOT/.cursor/rules"
CURSOR_RULES_REPO="$PM_ROOT/cursor-rules"

# Parse args
MODE="diff"
DRY_RUN=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --pull) MODE="pull"; shift ;;
        --push) MODE="push"; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) shift ;;
    esac
done

# Validate unified-trading-pm exists
if [ ! -d "$PM_ROOT" ]; then
    echo -e "${RED}Error: unified-trading-pm not found at $PM_ROOT${NC}" >&2
    exit 1
fi

# Delegate to push/pull scripts
if [ "$MODE" = "push" ]; then
    DRY_ARGS=""
    [ "$DRY_RUN" = true ] && DRY_ARGS="--dry-run"
    "$SCRIPT_DIR/sync-rules-push.sh" $DRY_ARGS
elif [ "$MODE" = "pull" ]; then
    DRY_ARGS=""
    [ "$DRY_RUN" = true ] && DRY_ARGS="--dry-run"
    "$SCRIPT_DIR/sync-rules-pull.sh" $DRY_ARGS
fi

# After push/pull, fall through to show status (same as default mode)

# Default: show diff

echo -e "${BOLD}Workspace sync status${NC}"
echo "====================="
echo ""

# Rule counts (from _workspace-lib.sh)
LOCAL_COUNT=$(count_rules_local)
REPO_COUNT=$(count_rules_repo)

echo -e "${CYAN}Rule counts:${NC}"
echo "  Local .cursor/rules/:    $LOCAL_COUNT"
echo "  Repo cursor-rules/:      $REPO_COUNT"
echo ""

# Last sync (from _workspace-lib.sh)
echo -e "${CYAN}Last sync:${NC} $(get_last_sync)"
echo ""

# Rules only in local (not yet pushed) — uses rules_only_local() from _workspace-lib.sh
echo -e "${CYAN}Rules only in local (not yet pushed):${NC}"
ONLY_LOCAL=$(rules_only_local 2>/dev/null || true)
if [ -n "$ONLY_LOCAL" ]; then
    echo "$ONLY_LOCAL" | sed 's/^/  - /'
else
    echo "  (none)"
fi
echo ""

# Rules only in repo (not yet pulled) — uses rules_only_repo() from _workspace-lib.sh
echo -e "${CYAN}Rules only in repo (not yet pulled):${NC}"
ONLY_REPO=$(rules_only_repo 2>/dev/null || true)
if [ -n "$ONLY_REPO" ]; then
    echo "$ONLY_REPO" | sed 's/^/  - /'
else
    echo "  (none)"
fi
echo ""

# Diff summary (files that differ)
echo -e "${CYAN}Files that differ (local vs repo):${NC}"
if [ -d "$CURSOR_RULES_LOCAL" ] && [ -d "$CURSOR_RULES_REPO" ]; then
    DIFF_FILES=$(diff -rq "$CURSOR_RULES_LOCAL" "$CURSOR_RULES_REPO" 2>/dev/null | grep -E "differ|Only in" || true)
    if [ -n "$DIFF_FILES" ]; then
        echo "$DIFF_FILES" | sed 's/^/  /'
    else
        echo "  (in sync)"
    fi
else
    echo "  (cannot compare)"
fi
echo ""
echo "Use --pull to update local from repo, --push to push local to repo."
echo "Use --dry-run with --pull or --push to preview."
