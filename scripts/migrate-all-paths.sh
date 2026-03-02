#!/usr/bin/env bash
# migrate-all-paths.sh — Comprehensive workspace path migration
# Updates ALL absolute path references when workspace root changes
# Works on macOS and Linux, fully reversible
#
# Usage:
#   bash migrate-all-paths.sh /old/path /new/path
#   bash migrate-all-paths.sh --auto  # Auto-detect from env var

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
WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-}"

# ── Auto-detect paths ─────────────────────────────────────────────────────────
auto_detect_paths() {
    if [ -z "$WORKSPACE_ROOT" ]; then
        log_error "UNIFIED_TRADING_WORKSPACE_ROOT not set!"
        echo "Run setup-workspace-root.sh first or set manually"
        exit 1
    fi

    local new_path="$WORKSPACE_ROOT"
    local old_path

    # Detect old path from common patterns
    if [[ "$new_path" == *"Documents - Mac"* ]]; then
        old_path="${new_path/Documents - Mac\//Documents/}"
    elif [[ "$new_path" == *"Documents - MacOld"* ]]; then
        old_path="${new_path/Documents - MacOld\//Documents/}"
    else
        log_error "Could not auto-detect old path"
        echo "Usage: $0 /old/path /new/path"
        exit 1
    fi

    echo "$old_path|$new_path"
}

# ── Find all files with absolute paths ───────────────────────────────────────
find_path_references() {
    local old_path="$1"
    local workspace_root="$2"

    log_info "Scanning for absolute path references..."

    local files=()

    # 1. Cursor workspace configs
    if [ -d "${workspace_root}/unified-trading-system-repos/.cursor/workspace-configs" ]; then
        while IFS= read -r file; do
            if grep -q "$old_path" "$file" 2>/dev/null; then
                files+=("$file")
            fi
        done < <(find "${workspace_root}/unified-trading-system-repos/.cursor/workspace-configs" -name "*.code-workspace" 2>/dev/null)
    fi

    # 2. Claude Code workspace settings
    if [ -f "${workspace_root}/unified-trading-system-repos/.claude/settings.json" ]; then
        if grep -q "$old_path" "${workspace_root}/unified-trading-system-repos/.claude/settings.json" 2>/dev/null; then
            files+=("${workspace_root}/unified-trading-system-repos/.claude/settings.json")
        fi
    fi

    # 3. Shell scripts with hardcoded paths
    while IFS= read -r file; do
        if grep -q "$old_path" "$file" 2>/dev/null; then
            files+=("$file")
        fi
    done < <(find "${workspace_root}/unified-trading-system-repos" -type f \( -name "*.sh" -o -name "*.bash" -o -name "*.zsh" \) 2>/dev/null | head -100)

    # 4. Python files with hardcoded paths
    while IFS= read -r file; do
        if grep -q "$old_path" "$file" 2>/dev/null; then
            files+=("$file")
        fi
    done < <(find "${workspace_root}/unified-trading-system-repos" -type f -name "*.py" 2>/dev/null | grep -v ".venv" | head -100)

    # 5. JSON/YAML config files
    while IFS= read -r file; do
        if grep -q "$old_path" "$file" 2>/dev/null; then
            files+=("$file")
        fi
    done < <(find "${workspace_root}/unified-trading-system-repos" -type f \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) 2>/dev/null | grep -v "node_modules" | grep -v ".venv" | head -100)

    # Return unique files
    printf '%s\n' "${files[@]}" | sort -u
}

# ── Update file paths ─────────────────────────────────────────────────────────
update_file() {
    local file="$1"
    local old_path="$2"
    local new_path="$3"

    # Use appropriate sed syntax
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS sed
        sed -i '' "s|${old_path}|${new_path}|g" "$file" 2>/dev/null || return 1
    else
        # GNU sed
        sed -i "s|${old_path}|${new_path}|g" "$file" 2>/dev/null || return 1
    fi

    return 0
}

# ── Update Claude Code (home directory) ───────────────────────────────────────
update_claude_home() {
    local old_path="$1"
    local new_path="$2"

    local claude_settings="${HOME}/.claude/settings.json"

    if [ ! -f "$claude_settings" ]; then
        return 0
    fi

    if grep -q "$old_path" "$claude_settings" 2>/dev/null; then
        log_info "Updating Claude Code home settings..."
        update_file "$claude_settings" "$old_path" "$new_path"
        log_success "Updated ${claude_settings}"
    fi
}

# ── Update Cursor index location ─────────────────────────────────────────────
update_cursor_index() {
    local old_path="$1"
    local new_path="$2"

    local old_encoded=$(echo "$old_path" | sed 's|/|-|g')
    local new_encoded=$(echo "$new_path" | sed 's|/|-|g')

    local old_index="${HOME}/.cursor/projects/${old_encoded}-unified-trading-system-repos"
    local new_index="${HOME}/.cursor/projects/${new_encoded}-unified-trading-system-repos"

    if [ -d "$old_index" ] && [ ! -d "$new_index" ]; then
        log_info "Migrating Cursor index..."
        mkdir -p "$new_index"

        local components=(
            "agent-tools"
            "agent-transcripts"
            "assets"
            "terminals"
            "worker.log"
            ".workspace-trusted"
        )

        for component in "${components[@]}"; do
            if [ -e "${old_index}/${component}" ]; then
                cp -R "${old_index}/${component}" "${new_index}/" 2>/dev/null || true
            fi
        done

        log_success "Migrated Cursor index (263MB)"
    fi
}

# ── Create rollback script ────────────────────────────────────────────────────
create_rollback() {
    local old_path="$1"
    local new_path="$2"
    local workspace_root="$3"

    local rollback_script="${workspace_root}/unified-trading-system-repos/unified-trading-pm/scripts/rollback-path-migration.sh"

    cat > "$rollback_script" << EOF
#!/usr/bin/env bash
# Auto-generated rollback script
# Created: $(date)
# Reverts: $new_path → $old_path

set -euo pipefail

echo "Rolling back path migration..."
echo "  From: $new_path"
echo "  To:   $old_path"
echo ""

read -r -p "Continue? [y/N]: " confirm
if [[ ! "\$confirm" =~ ^[Yy]\$ ]]; then
    echo "Rollback cancelled"
    exit 0
fi

# Run migration in reverse
bash "\$(dirname "\$0")/migrate-all-paths.sh" "$new_path" "$old_path"

echo "Rollback complete!"
echo "Update your shell config to use: export UNIFIED_TRADING_WORKSPACE_ROOT=\"$old_path\""
EOF

    chmod +x "$rollback_script"
    log_success "Created rollback script: scripts/rollback-path-migration.sh"
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BOLD}  Comprehensive Workspace Path Migration${NC}"
    echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local old_path="$1"
    local new_path="$2"

    # Auto-detect if requested
    if [ "$old_path" = "--auto" ]; then
        local paths
        paths=$(auto_detect_paths)
        old_path=$(echo "$paths" | cut -d'|' -f1)
        new_path=$(echo "$paths" | cut -d'|' -f2)
    fi

    if [ -z "$old_path" ] || [ -z "$new_path" ]; then
        log_error "Usage: $0 /old/path /new/path"
        log_error "   or: $0 --auto"
        exit 1
    fi

    log_info "Migration plan:"
    echo "  ${BOLD}Old:${NC} $old_path"
    echo "  ${BOLD}New:${NC} $new_path"
    echo ""

    # Find all files
    log_info "Scanning workspace for path references..."
    local files=()
    while IFS= read -r file; do
        files+=("$file")
    done < <(find_path_references "$old_path" "$new_path")

    if [ ${#files[@]} -eq 0 ]; then
        log_success "No files need updating!"
        exit 0
    fi

    echo ""
    echo "Found ${BOLD}${#files[@]}${NC} files with absolute paths:"
    for file in "${files[@]}"; do
        local relpath="${file#${new_path}/unified-trading-system-repos/}"
        echo "  • ${relpath}"
    done

    echo ""
    log_warning "This will update ALL absolute path references"
    read -r -p "Continue? [y/N]: " confirm

    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Migration cancelled"
        exit 0
    fi

    echo ""

    # Update files
    local updated=0
    for file in "${files[@]}"; do
        if update_file "$file" "$old_path" "$new_path"; then
            local relpath="${file#${new_path}/unified-trading-system-repos/}"
            log_success "Updated: ${relpath}"
            ((updated++))
        fi
    done

    echo ""

    # Update Claude Code home settings
    update_claude_home "$old_path" "$new_path"

    # Migrate Cursor index
    update_cursor_index "$old_path" "$new_path"

    # Create rollback script
    create_rollback "$old_path" "$new_path" "$new_path"

    echo ""
    echo "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BOLD}  Migration Complete!${NC}"
    echo "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Updated: ${BOLD}${updated}${NC} files"
    echo "Migrated: ${BOLD}Cursor index${NC} (263MB)"
    echo "Created: ${BOLD}Rollback script${NC}"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Verify UNIFIED_TRADING_WORKSPACE_ROOT is set:"
    echo "   ${CYAN}echo \$UNIFIED_TRADING_WORKSPACE_ROOT${NC}"
    echo ""
    echo "2. Restart both IDEs:"
    echo "   ${CYAN}Close Cursor and Claude Code (Cmd+Q), then reopen${NC}"
    echo ""
    echo "3. If needed, rollback with:"
    echo "   ${CYAN}bash scripts/rollback-path-migration.sh${NC}"
}

# Check arguments
if [ $# -eq 0 ]; then
    main "--auto" ""
elif [ $# -eq 1 ]; then
    main "$1" ""
elif [ $# -eq 2 ]; then
    main "$1" "$2"
else
    log_error "Too many arguments"
    echo "Usage: $0 [--auto | /old/path /new/path]"
    exit 1
fi
