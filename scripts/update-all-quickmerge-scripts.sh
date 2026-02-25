#!/bin/bash
# Update all quickmerge scripts to include Cursor Team Kit enforcement
# This script adds enforcement prompts for /deslop, /run-smoke-tests, and ci-watcher

set -e

WORKSPACE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC2034
ENFORCEMENT_SCRIPT="$WORKSPACE_ROOT/.cursor/scripts/cursor-team-kit-enforcement.sh"

echo "Cursor Team Kit: Bulk Update for Quickmerge Scripts"
echo "======================================================"
echo ""
echo "This will update all quickmerge scripts to include enforcement prompts."
echo "Backups will be created as quickmerge.sh.bak"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Find all quickmerge.sh scripts
QUICKMERGE_SCRIPTS=$(find "$WORKSPACE_ROOT" -maxdepth 3 -name "quickmerge.sh" -path "*/scripts/*" | grep -v "\.cursor")

UPDATED_COUNT=0
SKIPPED_COUNT=0

for script in $QUICKMERGE_SCRIPTS; do
    REPO_PATH=$(dirname "$(dirname "$script")")
    REPO_NAME=$(basename "$REPO_PATH")
    
    echo "Processing: $REPO_NAME"
    
    # Check if already integrated
    if grep -q "cursor-team-kit-enforcement.sh" "$script"; then
        echo "  ✓ Already integrated - skipping"
        ((SKIPPED_COUNT++))
        continue
    fi
    
    # Create backup
    cp "$script" "$script.bak"
    echo "  → Backup created: quickmerge.sh.bak"
    
    # Create temporary file for modifications
    TEMP_FILE=$(mktemp)
    
    # Add sourcing after 'set -e'
    awk '
        /^set -e$/ && !added {
            print
            print ""
            print "# Source Cursor Team Kit enforcement prompts (optional but recommended)"
            print "WORKSPACE_ROOT=\"$(cd \"$(dirname \"$0\")/../..\" && pwd)\""
            print "if [ -f \"$WORKSPACE_ROOT/.cursor/scripts/cursor-team-kit-enforcement.sh\" ]; then"
            print "    source \"$WORKSPACE_ROOT/.cursor/scripts/cursor-team-kit-enforcement.sh\""
            print "    CURSOR_TEAM_KIT_ENABLED=1"
            print "else"
            print "    CURSOR_TEAM_KIT_ENABLED=0"
            print "fi"
            added = 1
            next
        }
        { print }
    ' "$script" > "$TEMP_FILE"
    
    mv "$TEMP_FILE" "$script"
    
    # Add deslop prompt after changes check
    TEMP_FILE=$(mktemp)
    awk '
        /^# Check for changes$/ {
            in_block = 1
        }
        in_block && /^fi$/ && !added_deslop {
            print
            print ""
            print "# Cursor Team Kit: Prompt for deslop (code cleanup)"
            print "if [ \"$CURSOR_TEAM_KIT_ENABLED\" = 1 ]; then"
            print "    prompt_deslop \"$REPO_NAME\""
            print "fi"
            added_deslop = 1
            in_block = 0
            next
        }
        { print }
    ' "$script" > "$TEMP_FILE"
    
    mv "$TEMP_FILE" "$script"
    
    # Add smoke tests prompt after quality gates
    TEMP_FILE=$(mktemp)
    awk '
        /Quality gates PASSED - Proceeding with merge/ {
            print
            getline
            print
            print ""
            print "# Cursor Team Kit: Prompt for smoke tests (UI repos only)"
            print "if [ \"$CURSOR_TEAM_KIT_ENABLED\" = 1 ]; then"
            print "    prompt_smoke_tests \"$REPO_NAME\""
            print "fi"
            next
        }
        { print }
    ' "$script" > "$TEMP_FILE"
    
    mv "$TEMP_FILE" "$script"
    
    # Add ci-watcher prompt after PR creation
    TEMP_FILE=$(mktemp)
    awk '
        /To sync with main later: git checkout main/ {
            print
            print ""
            print "# Cursor Team Kit: Show ci-watcher instructions"
            print "if [ \"$CURSOR_TEAM_KIT_ENABLED\" = 1 ]; then"
            print "    show_ci_watcher_prompt \"$REPO_NAME\" \"$PR_NUM\" \"$PR_URL\""
            print "fi"
            next
        }
        { print }
    ' "$script" > "$TEMP_FILE"
    
    mv "$TEMP_FILE" "$script"
    
    # Make executable
    chmod +x "$script"
    
    echo "  ✅ Updated successfully"
    ((UPDATED_COUNT++))
done

echo ""
echo "======================================================"
echo "Summary:"
echo "  Updated: $UPDATED_COUNT repos"
echo "  Skipped: $SKIPPED_COUNT repos (already integrated)"
echo ""
echo "Backups created as quickmerge.sh.bak in each repo."
echo "Test with: bash scripts/quickmerge.sh \"test commit\""
echo ""
echo "To revert a repo:"
echo "  mv scripts/quickmerge.sh.bak scripts/quickmerge.sh"
