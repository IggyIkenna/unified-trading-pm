#!/usr/bin/env bash
#
# Wipe GitHub Project (Background-Friendly)
#
# This script deletes all issues from the GitHub project board.
# Optimized for speed with parallel deletion.
#

set -euo pipefail

ORG="IggyIkenna"
REPO="unified-trading-codex"
PROJECT_NUMBER=1

echo "🗑️  Wiping GitHub Project #$PROJECT_NUMBER..."
echo ""

# Step 1: Delete all issues (open + closed) in parallel (20 at a time)
echo "Step 1/2: Deleting all issues..."
ALL_ISSUES=$(gh issue list --repo "$ORG/$REPO" --state all --limit 1000 --json number --jq '.[].number' 2>/dev/null || true)

if [ -n "$ALL_ISSUES" ]; then
    ISSUE_COUNT=$(echo "$ALL_ISSUES" | wc -l | tr -d ' ')
    echo "  Found $ISSUE_COUNT issues to delete"
    echo "$ALL_ISSUES" | xargs -P 20 -I {} gh issue delete {} --repo "$ORG/$REPO" --yes 2>/dev/null || true
    echo "  ✅ Deleted $ISSUE_COUNT issues"
else
    echo "  ✅ No issues to delete"
fi

# Step 2: Clear project board items in parallel
echo ""
echo "Step 2/2: Clearing project board..."
PROJECT_ITEMS=$(gh project item-list $PROJECT_NUMBER --owner "$ORG" --format json --limit 1000 2>/dev/null | jq -r '.items[].id' 2>/dev/null || true)

if [ -n "$PROJECT_ITEMS" ]; then
    ITEM_COUNT=$(echo "$PROJECT_ITEMS" | wc -l | tr -d ' ')
    echo "  Found $ITEM_COUNT project items"
    echo "$PROJECT_ITEMS" | xargs -P 20 -I {} gh project item-delete $PROJECT_NUMBER --owner "$ORG" --id {} 2>/dev/null || true
    echo "  ✅ Removed $ITEM_COUNT items"
else
    echo "  ✅ No project items to remove"
fi

echo ""
echo "✅ Project wipe complete!"
echo ""
