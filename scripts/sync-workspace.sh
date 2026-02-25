#!/usr/bin/env bash
# sync-workspace.sh - Full workspace sync (pull latest rules + workspace configs)
# Usage: ./sync-workspace.sh [--push | --pull] [--dry-run]
#
# Default (no flags): shows current diff between local .cursor/rules/ and repo cursor-rules/
# --pull: runs sync-rules-pull.sh (updates your local rules from repo)
# --push: runs sync-rules-push.sh (pushes your local rules to repo)
# --dry-run: preview only, no changes

set -euo pipefail

# Colors (with fallback)
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    CYAN=$(tput setaf 6)
    BOLD=$(tput bold)
    NC=$(tput sgr0)
else
    RED=""
    GREEN=""
    YELLOW=""
    CYAN=""
    BOLD=""
    NC=""
fi

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"

CURSOR_RULES_LOCAL="$WORKSPACE_ROOT/.cursor/rules"
CURSOR_RULES_REPO="$PM_ROOT/cursor-rules"
LAST_SYNC_FILE="$PM_ROOT/.last-sync"

# .last-sync format: ISO8601 timestamp, one per line (e.g. 2026-02-25T12:00:00Z)
# Used by sync-rules-push.sh and sync-rules-pull.sh to track last sync time.

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

# Rule counts
LOCAL_COUNT=0
REPO_COUNT=0
[ -d "$CURSOR_RULES_LOCAL" ] && LOCAL_COUNT=$(find "$CURSOR_RULES_LOCAL" -maxdepth 1 -type f -name "*.mdc" 2>/dev/null | wc -l | tr -d ' ')
[ -d "$CURSOR_RULES_REPO" ] && REPO_COUNT=$(find "$CURSOR_RULES_REPO" -maxdepth 1 -type f -name "*.mdc" 2>/dev/null | wc -l | tr -d ' ')

echo -e "${CYAN}Rule counts:${NC}"
echo "  Local .cursor/rules/:    $LOCAL_COUNT"
echo "  Repo cursor-rules/:      $REPO_COUNT"
echo ""

# Last sync
if [ -f "$LAST_SYNC_FILE" ]; then
    LAST_SYNC=$(head -c 80 "$LAST_SYNC_FILE" 2>/dev/null || echo "")
    echo -e "${CYAN}Last sync:${NC} $LAST_SYNC"
else
    echo -e "${CYAN}Last sync:${NC} (never)"
fi
echo ""

# Rules only in local (not yet pushed)
echo -e "${CYAN}Rules only in local (not yet pushed):${NC}"
if [ -d "$CURSOR_RULES_LOCAL" ] && [ -d "$CURSOR_RULES_REPO" ]; then
    ONLY_LOCAL=$(comm -23 \
        <(find "$CURSOR_RULES_LOCAL" -maxdepth 1 -type f -name "*.mdc" -exec basename {} \; 2>/dev/null | sort -u) \
        <(find "$CURSOR_RULES_REPO" -maxdepth 1 -type f -name "*.mdc" -exec basename {} \; 2>/dev/null | sort -u) \
        2>/dev/null || true)
    if [ -n "$ONLY_LOCAL" ]; then
        echo "$ONLY_LOCAL" | sed 's/^/  - /'
    else
        echo "  (none)"
    fi
else
    echo "  (cannot compare)"
fi
echo ""

# Rules only in repo (not yet pulled)
echo -e "${CYAN}Rules only in repo (not yet pulled):${NC}"
if [ -d "$CURSOR_RULES_LOCAL" ] && [ -d "$CURSOR_RULES_REPO" ]; then
    ONLY_REPO=$(comm -13 \
        <(find "$CURSOR_RULES_LOCAL" -maxdepth 1 -type f -name "*.mdc" -exec basename {} \; 2>/dev/null | sort -u) \
        <(find "$CURSOR_RULES_REPO" -maxdepth 1 -type f -name "*.mdc" -exec basename {} \; 2>/dev/null | sort -u) \
        2>/dev/null || true)
    if [ -n "$ONLY_REPO" ]; then
        echo "$ONLY_REPO" | sed 's/^/  - /'
    else
        echo "  (none)"
    fi
else
    echo "  (cannot compare)"
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
