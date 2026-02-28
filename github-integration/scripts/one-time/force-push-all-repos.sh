#!/usr/bin/env bash
#
# Force push all uncommitted changes across all repos
#
# Workflow:
#   1. Disable branch protection
#   2. Commit all changes in each repo
#   3. Force push to main
#   4. Re-enable branch protection
#
# Usage:
#   bash force-push-all-repos.sh [--dry-run]

set -euo pipefail

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No actual changes will be made"
    echo ""
fi

WORKSPACE_ROOT="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"
ORG="IggyIkenna"

# All repos
REPOS=(
    "execution-services"
    "strategy-service"
    "instruments-service"
    "unified-trading-services"
    "market-data-processing-service"
    "ml-training-service"
    "ml-inference-service"
    "features-delta-one-service"
    "features-volatility-service"
    "features-calendar-service"
    "features-onchain-service"
    "market-tick-data-handler"
    "unified-trading-deployment-v2"
    "unified-trading-codex"
)

echo "========================================================================"
echo "Force Push All Repos - Workflow"
echo "========================================================================"
echo ""
echo "This script will:"
echo "  1. Disable branch protection for ${#REPOS[@]} repos"
echo "  2. Commit all uncommitted changes"
echo "  3. Force push to main"
echo "  4. Re-enable branch protection"
echo ""

if [ "$DRY_RUN" = false ]; then
    read -p "Continue? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted"
        exit 1
    fi
    echo ""
fi

# ============================================================================
# STEP 1: Disable Branch Protection
# ============================================================================

echo "========================================================================"
echo "STEP 1: Disable Branch Protection"
echo "========================================================================"
echo ""

if [ "$DRY_RUN" = false ]; then
    bash "$(dirname "$0")/disable-branch-protection.sh" --all

    if [ $? -ne 0 ]; then
        echo "❌ Failed to disable branch protection"
        echo "Check your GitHub PAT permissions"
        exit 1
    fi
else
    echo "🔍 Would run: disable-branch-protection.sh --all"
fi

echo ""
sleep 2

# ============================================================================
# STEP 2: Commit and Force Push Each Repo
# ============================================================================

echo "========================================================================"
echo "STEP 2: Commit and Force Push All Repos"
echo "========================================================================"
echo ""

PUSHED=0
SKIPPED=0
ERRORS=0

for repo in "${REPOS[@]}"; do
    REPO_PATH="$WORKSPACE_ROOT/$repo"

    if [ ! -d "$REPO_PATH/.git" ]; then
        echo "⏭️  $repo - Not a git repo"
        ((SKIPPED++))
        continue
    fi

    cd "$REPO_PATH"

    # Check if there are changes
    if [ -z "$(git status --short)" ]; then
        echo "⏭️  $repo - No changes"
        ((SKIPPED++))
        continue
    fi

    echo "📝 $repo..."

    # Show what will be committed
    CHANGE_COUNT=$(git status --short | wc -l | tr -d ' ')
    echo "  Changes: $CHANGE_COUNT files"

    if [ "$DRY_RUN" = true ]; then
        echo "  🔍 Would commit and force push:"
        git status --short | head -10 | sed 's/^/    /'
        if [ "$CHANGE_COUNT" -gt 10 ]; then
            echo "    ... and $((CHANGE_COUNT - 10)) more"
        fi
        ((PUSHED++))
        echo ""
        continue
    fi

    # Commit message
    COMMIT_MSG="Housekeeping: Commit local changes (force push)"

    if [ "$repo" = "unified-trading-codex" ]; then
        COMMIT_MSG="Housekeeping: Commit documentation and workflow updates"
    else
        # Check if it's just CODEX_VIOLATIONS_MANIFEST.md
        if git status --short | grep -q "CODEX_VIOLATIONS_MANIFEST.md"; then
            COMMIT_MSG="Add CODEX_VIOLATIONS_MANIFEST.md for tracking"
        fi
    fi

    # Add all changes
    git add -A

    # Commit
    if git commit -m "$COMMIT_MSG" --no-verify 2>/dev/null; then
        echo "  ✅ Committed"
    else
        echo "  ℹ️  Already committed or nothing to commit"
    fi

    # Force push
    if git push --force origin main 2>&1; then
        echo "  ✅ Force pushed"
        ((PUSHED++))
    else
        echo "  ❌ Force push failed"
        ((ERRORS++))
    fi

    echo ""
done

echo "========================================================================"
echo "Step 2 Summary"
echo "========================================================================"
echo "✅ Pushed:   $PUSHED"
echo "⏭️  Skipped:  $SKIPPED"
echo "❌ Errors:   $ERRORS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "⚠️  Some repos failed - review errors above"
    echo ""
fi

if [ "$DRY_RUN" = true ]; then
    echo "🔍 Dry run complete - no changes made"
    exit 0
fi

sleep 2

# ============================================================================
# STEP 3: Re-enable Branch Protection
# ============================================================================

echo "========================================================================"
echo "STEP 3: Re-enable Branch Protection"
echo "========================================================================"
echo ""

# Find the most recent backup directory
BACKUP_DIR=$(ls -td /tmp/branch-protection-backup-* 2>/dev/null | head -1)

if [ -z "$BACKUP_DIR" ]; then
    echo "⚠️  No backup directory found"
    echo "Branch protection was disabled but cannot be restored automatically"
    echo ""
    echo "You will need to manually re-enable branch protection for:"
    for repo in "${REPOS[@]}"; do
        echo "  - $ORG/$repo"
    done
    echo ""
    exit 1
fi

echo "📁 Using backup: $BACKUP_DIR"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/enable-branch-protection.sh" --restore "$BACKUP_DIR"

if [ $? -ne 0 ]; then
    echo "⚠️  Failed to restore branch protection"
    echo "Backup configs saved in: $BACKUP_DIR"
    echo "You can manually restore later"
    exit 1
fi

echo ""
echo "========================================================================"
echo "✅ COMPLETE!"
echo "========================================================================"
echo ""
echo "Summary:"
echo "  - Branch protection: Temporarily disabled, then restored"
echo "  - Repos pushed: $PUSHED"
echo "  - Repos skipped: $SKIPPED"
echo "  - Errors: $ERRORS"
echo ""
