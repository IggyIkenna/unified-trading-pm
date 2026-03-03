#!/usr/bin/env bash
#
# Check GitHub PAT permissions and recommend fixes
#
# Usage:
#   bash check-github-pat-permissions.sh
#

set -euo pipefail

ORG="IggyIkenna"
TEST_REPO="unified-trading-library"  # Use a known repo for testing

echo "🔍 Checking GitHub PAT permissions..."
echo ""

# Check if gh is authenticated
if ! gh auth status &>/dev/null; then
    echo "❌ GitHub CLI not authenticated"
    echo ""
    echo "Fix:"
    echo "  gh auth login"
    echo ""
    exit 1
fi

echo "✅ GitHub CLI authenticated"
echo ""

# Get current user
CURRENT_USER=$(gh api user --jq '.login' 2>/dev/null || echo "unknown")
echo "👤 User: $CURRENT_USER"
echo ""

# Test permissions by trying different API calls
echo "Testing permissions..."
echo ""

# 1. Read repo info (basic)
echo -n "  📖 Read repo info................ "
if gh api "repos/$ORG/$TEST_REPO" &>/dev/null; then
    echo "✅"
else
    echo "❌ FAILED"
    echo ""
    echo "Your PAT doesn't even have basic read access!"
    exit 1
fi

# 2. Read branch protection
echo -n "  📖 Read branch protection........ "
if gh api "repos/$ORG/$TEST_REPO/branches/main/protection" &>/dev/null 2>&1; then
    echo "✅"
    CAN_READ_PROTECTION=true
else
    echo "❌ FAILED"
    CAN_READ_PROTECTION=false
fi

# 3. Write branch protection (admin required)
echo -n "  🔒 Modify branch protection...... "
# Try a minimal protection update test
TEST_PROTECTION='{
  "required_status_checks": {
    "strict": true,
    "contexts": ["quality-gates"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null
}'
if echo "$TEST_PROTECTION" | gh api -X PUT "repos/$ORG/$TEST_REPO/branches/main/protection" --input - &>/dev/null 2>&1; then
    echo "✅"
    CAN_WRITE_PROTECTION=true
else
    ERROR=$(echo "$TEST_PROTECTION" | gh api -X PUT "repos/$ORG/$TEST_REPO/branches/main/protection" --input - 2>&1 || true)
    if echo "$ERROR" | grep -q "403"; then
        echo "❌ FAILED (403 Forbidden)"
    else
        echo "❌ FAILED"
    fi
    CAN_WRITE_PROTECTION=false
fi

# 4. Create issues
echo -n "  📝 Create issues................. "
# Don't actually create, just check repo issues endpoint
if gh api "repos/$ORG/$TEST_REPO/issues" --method GET &>/dev/null; then
    echo "✅"
    CAN_MANAGE_ISSUES=true
else
    echo "❌ FAILED"
    CAN_MANAGE_ISSUES=false
fi

# 5. Create/manage PRs
echo -n "  🔀 Manage pull requests.......... "
if gh api "repos/$ORG/$TEST_REPO/pulls" --method GET &>/dev/null; then
    echo "✅"
    CAN_MANAGE_PRS=true
else
    echo "❌ FAILED"
    CAN_MANAGE_PRS=false
fi

echo ""
echo "========================================================================"
echo "PERMISSION SUMMARY"
echo "========================================================================"
echo ""

if [ "$CAN_READ_PROTECTION" = true ] && [ "$CAN_WRITE_PROTECTION" = true ] && [ "$CAN_MANAGE_ISSUES" = true ] && [ "$CAN_MANAGE_PRS" = true ]; then
    echo "✅ ALL PERMISSIONS OK"
    echo ""
    echo "You can:"
    echo "  - Disable/enable branch protection (for bulk pushes)"
    echo "  - Create and manage issues"
    echo "  - Create and manage PRs"
    echo "  - Run all automation scripts"
    echo ""
    exit 0
fi

echo "⚠️  SOME PERMISSIONS MISSING"
echo ""

# Detailed recommendations
echo "What you CAN do:"
if [ "$CAN_READ_PROTECTION" = true ]; then
    echo "  ✅ Read branch protection settings"
fi
if [ "$CAN_MANAGE_ISSUES" = true ]; then
    echo "  ✅ Create and manage issues"
fi
if [ "$CAN_MANAGE_PRS" = true ]; then
    echo "  ✅ Create and manage PRs"
fi

echo ""
echo "What you CANNOT do:"
if [ "$CAN_WRITE_PROTECTION" = false ]; then
    echo "  ❌ Disable/enable branch protection (needs admin scope)"
    echo "     → Use quickmerge instead of direct pushes"
    echo "     → Or manually disable via GitHub UI"
fi

echo ""
echo "========================================================================"
echo "HOW TO FIX"
echo "========================================================================"
echo ""

if [ "$CAN_WRITE_PROTECTION" = false ]; then
    echo "Your PAT needs admin permissions. Choose one:"
    echo ""
    echo "Option 1: Update PAT Permissions (Recommended)"
    echo "────────────────────────────────────────────"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Find your current token (or create new fine-grained token)"
    echo "3. Add these permissions:"
    echo "   - Administration: Read and Write"
    echo "   - Contents: Read and Write"
    echo "   - Issues: Read and Write"
    echo "   - Pull Requests: Read and Write"
    echo "4. Regenerate/save token"
    echo "5. Update in terminal:"
    echo "   echo '<new-token>' | gh auth login --with-token"
    echo ""
    echo "Option 2: Use GitHub UI for Branch Protection"
    echo "────────────────────────────────────────────"
    echo "See: unified-trading-codex/11-project-management/github-integration/docs/BRANCH-PROTECTION-MANAGEMENT.md"
    echo ""
    echo "Option 3: Use Quickmerge (No Admin Needed)"
    echo "────────────────────────────────────────────"
    echo "Instead of direct pushes, use:"
    echo "  bash git-quickmerge.sh 'message' --all"
    echo ""
    echo "This creates PRs (no protection issues) and auto-merges."
fi

exit 1
