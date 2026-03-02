#!/usr/bin/env bash
# sync-rules-pull.sh — Pull Cursor rules from the team repo into your local .cursor/rules/
#
# Usage:
#   ./sync-rules-pull.sh [--dry-run] [--force]
#
# What it does:
#   Copies unified-trading-pm/cursor-rules/ → <workspace-root>/.cursor/rules/
#   Also restores .cursorrules and *.code-workspace from cursor-configs/
#
# Run 'git pull' on unified-trading-pm first to get the latest changes from the team.
# Use --dry-run to preview what would change before applying.
# Use --force to skip the confirmation prompt.
#
# Does NOT delete local rules that are absent from the repo (safer).
# If you want to remove a rule, delete it manually from .cursor/rules/ too.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"

# shellcheck source=../_workspace-lib.sh
source "$SCRIPT_DIR/../_workspace-lib.sh"

# ── Parse args ────────────────────────────────────────────────────────────────
DRY_RUN=false
FORCE=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --force)   FORCE=true;   shift ;;
        *)         shift ;;
    esac
done

# ── Validate workspace ────────────────────────────────────────────────────────
echo ""
validate_workspace_structure || exit 1
echo ""

# ── Paths ─────────────────────────────────────────────────────────────────────
CURSOR_RULES_SRC="$PM_ROOT/cursor-rules"
CURSOR_RULES_DST="$WORKSPACE_ROOT/.cursor/rules"
CURSOR_CONFIGS_SRC="$PM_ROOT/cursor-configs"

# ── Dry run ───────────────────────────────────────────────────────────────────
if [ "$DRY_RUN" = true ]; then
    echo "${YELLOW}[DRY RUN] Would sync:${NC}"
    echo "  $CURSOR_RULES_SRC → $CURSOR_RULES_DST"
    echo ""
    echo "Rule counts:"
    echo "  Repo (source): $(count_rules_repo)"
    echo "  Local (dest):  $(count_rules_local)"
    echo ""
    local_only=$(rules_only_local)
    repo_only=$(rules_only_repo)
    if [ -n "$local_only" ]; then
        echo "${YELLOW}Rules only in your local (would NOT be deleted):${NC}"
        echo "$local_only" | sed 's/^/  - /'
    fi
    if [ -n "$repo_only" ]; then
        echo "${CYAN}Rules only in repo (would be added to local):${NC}"
        echo "$repo_only" | sed 's/^/  + /'
    fi
    echo ""
    echo "Content diff (repo vs local):"
    diff -rq "$CURSOR_RULES_SRC" "$CURSOR_RULES_DST" 2>/dev/null || true
    exit 0
fi

# ── Confirmation ──────────────────────────────────────────────────────────────
if [ "$FORCE" != true ]; then
    echo "${YELLOW}This will overwrite matching rules in: $CURSOR_RULES_DST${NC}"
    echo "(Rules only in your local are preserved — they are not deleted.)"
    echo ""
    echo "  Repo rules:  $(count_rules_repo)"
    echo "  Local rules: $(count_rules_local)"
    echo "  Last sync:   $(get_last_sync)"
    echo ""
    repo_only=$(rules_only_repo)
    if [ -n "$repo_only" ]; then
        echo "${CYAN}New rules to be added:${NC}"
        echo "$repo_only" | sed 's/^/  + /'
        echo ""
    fi
    read -r -p "Continue? [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY]) ;;
        *) echo "Aborted."; exit 0 ;;
    esac
fi

# ── Copy rules ────────────────────────────────────────────────────────────────
mkdir -p "$CURSOR_RULES_DST"

RULE_COUNT=0
for f in "$CURSOR_RULES_SRC"/*.mdc; do
    [ -f "$f" ] || continue
    cp -f "$f" "$CURSOR_RULES_DST/"
    ((RULE_COUNT++)) || true
done

# Restore .cursorrules
if [ -f "$CURSOR_CONFIGS_SRC/cursorrules" ]; then
    cp -f "$CURSOR_CONFIGS_SRC/cursorrules" "$WORKSPACE_ROOT/.cursorrules"
    echo "${GREEN}✓${NC} Restored .cursorrules"
fi

# Restore *.code-workspace files
mkdir -p "$WORKSPACE_ROOT/.cursor/workspace-configs"
if [ -d "$CURSOR_CONFIGS_SRC" ]; then
    for f in "$CURSOR_CONFIGS_SRC"/*.code-workspace; do
        [ -f "$f" ] || continue
        cp -f "$f" "$WORKSPACE_ROOT/.cursor/workspace-configs/"
    done
fi

update_last_sync

echo ""
echo "${GREEN}${BOLD}✓ Pulled $RULE_COUNT rules → $CURSOR_RULES_DST${NC}"
echo ""
echo "Restart Cursor (or reload window) for new rules to take effect."
