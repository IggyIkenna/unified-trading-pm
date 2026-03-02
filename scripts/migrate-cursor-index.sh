#!/usr/bin/env bash
# migrate-cursor-index.sh — Copy Cursor codebase index from old path to new
# Saves 30+ minutes of re-indexing when workspace path changes
#
# Usage:
#   bash migrate-cursor-index.sh

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
    RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
    CYAN=$(tput setaf 6); BOLD=$(tput bold); NC=$(tput sgr0)
else
    RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; NC=""
fi

log_info() { echo "${CYAN}ℹ${NC} $*"; }
log_success() { echo "${GREEN}✅${NC} $*"; }
log_warning() { echo "${YELLOW}⚠${NC} $*"; }
log_error() { echo "${RED}✗${NC} $*" >&2; }

# ── Configuration ─────────────────────────────────────────────────────────────
CURSOR_PROJECTS="${HOME}/.cursor/projects"
OLD_PATH="Users-${USER}-Documents-repos-unified-trading-system-repos"
NEW_PATH="Users-${USER}-Documents-Documents-Mac-repos-unified-trading-system-repos"

# ── Check Cursor is closed ────────────────────────────────────────────────────
check_cursor_closed() {
    if pgrep -x "Cursor" > /dev/null 2>&1; then
        log_error "Cursor is still running!"
        echo ""
        echo "Please close Cursor completely (Cmd+Q) before running this script."
        echo "This prevents index corruption during the copy."
        exit 1
    fi
    log_success "Cursor is closed"
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BOLD}  Cursor Index Migration${NC}"
    echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check Cursor is closed
    check_cursor_closed
    echo ""
    
    # Check source exists
    local old_index="${CURSOR_PROJECTS}/${OLD_PATH}"
    local new_index="${CURSOR_PROJECTS}/${NEW_PATH}"
    
    if [ ! -d "$old_index" ]; then
        log_error "Old index not found: ${old_index}"
        log_error "Nothing to migrate!"
        exit 1
    fi
    
    local old_size=$(du -sh "$old_index" | awk '{print $1}')
    log_info "Found old index: ${BOLD}${old_size}${NC}"
    echo ""
    
    # Check destination
    if [ ! -d "$new_index" ]; then
        log_error "New index directory doesn't exist yet"
        log_error "Open workspace in Cursor once first, then run this script"
        exit 1
    fi
    
    local new_size=$(du -sh "$new_index" | awk '{print $1}')
    log_info "Current new index: ${BOLD}${new_size}${NC}"
    echo ""
    
    # Confirm
    log_warning "This will copy ${old_size} of index data"
    log_warning "It will save ~30+ minutes of re-indexing"
    echo ""
    read -r -p "Continue? [y/N]: " confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Migration cancelled"
        exit 0
    fi
    
    echo ""
    log_info "Copying index files..."
    
    # Copy key index files (skip some that should regenerate)
    local files_to_copy=(
        "agent-tools"
        "agent-transcripts" 
        "assets"
        "terminals"
        "worker.log"
        ".workspace-trusted"
    )
    
    local copied=0
    for file in "${files_to_copy[@]}"; do
        if [ -e "${old_index}/${file}" ]; then
            cp -R "${old_index}/${file}" "${new_index}/" 2>/dev/null || true
            if [ -e "${new_index}/${file}" ]; then
                log_success "Copied: ${file}"
                ((copied++))
            fi
        fi
    done
    
    echo ""
    log_success "Copied ${copied} index components"
    
    # Show new size
    local final_size=$(du -sh "$new_index" | awk '{print $1}')
    echo ""
    echo "Index sizes:"
    echo "  Old: ${BOLD}${old_size}${NC}"
    echo "  New: ${BOLD}${final_size}${NC}"
    
    echo ""
    echo "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BOLD}  Migration Complete!${NC}"
    echo "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Open Cursor"
    echo "2. Open your workspace"
    echo "3. Check ${CYAN}Indexing & Docs${NC} settings"
    echo "4. Index should complete much faster (or already be done!)"
    echo ""
    
    log_info "If indexing still takes long, it may need to verify paths"
    log_info "But it's much faster than indexing from scratch!"
}

main "$@"
