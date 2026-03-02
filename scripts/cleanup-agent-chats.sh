#!/usr/bin/env bash
# cleanup-agent-chats.sh — Remove old Cursor agent chat transcripts
# Deletes all .jsonl files older than 24 hours from ~/.cursor/projects
# Run periodically to save disk space (typically saves 20-50MB)
#
# Usage:
#   bash cleanup-agent-chats.sh           # Delete files >24h old
#   bash cleanup-agent-chats.sh --dry-run # Show what would be deleted

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
    GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); CYAN=$(tput setaf 6)
    BOLD=$(tput bold); NC=$(tput sgr0)
else
    GREEN=""; YELLOW=""; CYAN=""; BOLD=""; NC=""
fi

# ── Configuration ─────────────────────────────────────────────────────────────
CURSOR_PROJECTS_DIR="${HOME}/.cursor/projects"
AGE_HOURS=24  # Delete files older than this

# ── Parse arguments ───────────────────────────────────────────────────────────
DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
fi

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BOLD}  Cursor Agent Chat Cleanup${NC}"
    echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ ! -d "$CURSOR_PROJECTS_DIR" ]; then
        echo "${YELLOW}⚠${NC} Cursor projects directory not found: $CURSOR_PROJECTS_DIR"
        exit 0
    fi
    
    echo "🔍 Scanning for agent chat transcripts older than ${AGE_HOURS} hours..."
    echo ""
    
    # Count and size before deletion
    local old_files
    old_files=$(find "$CURSOR_PROJECTS_DIR" -name "*.jsonl" -type f -mtime +1 2>/dev/null || true)
    local old_count=0
    if [ -n "$old_files" ]; then
        old_count=$(echo "$old_files" | wc -l | tr -d ' ')
    fi
    
    if [ "$old_count" -eq 0 ]; then
        echo "${GREEN}✅${NC} No old chat files to delete"
        echo ""
        
        # Show current size
        if command -v du >/dev/null 2>&1; then
            local current_size
            current_size=$(du -sh "$CURSOR_PROJECTS_DIR" 2>/dev/null | awk '{print $1}')
            echo "📊 Cursor projects folder: ${BOLD}${current_size}${NC}"
        fi
        exit 0
    fi
    
    # Calculate size
    local old_size
    if command -v du >/dev/null 2>&1; then
        old_size=$(echo "$old_files" | xargs du -ch 2>/dev/null | tail -1 | awk '{print $1}')
    else
        old_size="unknown"
    fi
    
    echo "Found: ${BOLD}${old_count}${NC} files totaling ${BOLD}${old_size}${NC}"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        echo "${YELLOW}⚠${NC} DRY RUN - would delete:"
        echo ""
        echo "$old_files" | head -10
        if [ "$old_count" -gt 10 ]; then
            echo "... and $((old_count - 10)) more files"
        fi
        echo ""
        echo "Run without --dry-run to actually delete"
        exit 0
    fi
    
    # Delete files
    echo "🗑️  Deleting old chat transcripts..."
    find "$CURSOR_PROJECTS_DIR" -name "*.jsonl" -type f -mtime +1 -delete 2>/dev/null || true
    
    # Show results
    echo "${GREEN}✅${NC} Cleanup complete!"
    echo ""
    echo "Deleted: ${BOLD}${old_count}${NC} files (${BOLD}${old_size}${NC})"
    
    if command -v du >/dev/null 2>&1; then
        local remaining_size
        remaining_size=$(du -sh "$CURSOR_PROJECTS_DIR" 2>/dev/null | awk '{print $1}')
        echo "📊 Cursor projects folder now: ${BOLD}${remaining_size}${NC}"
    fi
    
    echo ""
    echo "💡 ${BOLD}Tip:${NC} Add to cron to run daily at 3 AM:"
    echo "   ${CYAN}crontab -e${NC}"
    echo "   ${CYAN}0 3 * * * $(realpath "$0")${NC}"
}

main "$@"
