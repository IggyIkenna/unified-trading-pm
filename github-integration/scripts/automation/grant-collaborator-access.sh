#!/usr/bin/env bash
#
# Grant Collaborator Access to All Repositories
#
# This script grants admin/write access to specified GitHub users across all repositories
# in the organization or workspace.
#
# Usage:
#   ./grant-collaborator-access.sh
#
# Required:
#   - GitHub CLI (gh) installed and authenticated
#   - Admin access to the repositories
#
# Security Note:
#   - Uses GitHub CLI authentication (no hardcoded tokens)
#   - Requires manual confirmation for safety
#

set -e

# Configuration
GITHUB_ORG="IggyIkenna" # Update if different
COLLABORATORS=("CosmicTrader" "datadodo")
PERMISSION_LEVEL="write" # Options: admin, write, read (write = push code, not settings)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "GitHub Repository Access Grant Script"
echo "=================================================="
echo ""
echo "This script will grant the following access:"
echo "  Users: ${COLLABORATORS[*]}"
echo "  Permission: $PERMISSION_LEVEL"
echo "  Organization: $GITHUB_ORG"
echo ""

# Check if gh CLI is installed
if ! command -v gh &>/dev/null; then
  echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
  echo "Install with: brew install gh"
  exit 1
fi

# Check if authenticated
if ! gh auth status &>/dev/null; then
  echo -e "${RED}Error: Not authenticated with GitHub CLI${NC}"
  echo "Run: gh auth login"
  exit 1
fi

# Get list of repositories
echo "Fetching repository list..."

# Get all repos from the organization (up to 100)
REPOS=$(gh repo list $GITHUB_ORG --limit 100 --json name --jq '.[].name' 2>/dev/null || echo "")

if [ -z "$REPOS" ]; then
  echo -e "${YELLOW}No organization repos found. Trying user repos...${NC}"
  # If org fails, try user repos
  REPOS=$(gh repo list --limit 100 --json name --jq '.[].name' 2>/dev/null || echo "")
fi

if [ -z "$REPOS" ]; then
  echo -e "${RED}Error: No repositories found${NC}"
  exit 1
fi

# Count repositories
REPO_COUNT=$(echo "$REPOS" | wc -l | tr -d ' ')
echo -e "${GREEN}Found $REPO_COUNT repositories${NC}"
echo ""

# Show repository list
echo "Repositories to update:"
echo "------------------------"
echo "$REPOS" | head -20
if [ $REPO_COUNT -gt 20 ]; then
  echo "... and $((REPO_COUNT - 20)) more"
fi
echo ""

# Confirm before proceeding
read -p "Do you want to grant $PERMISSION_LEVEL access to these $REPO_COUNT repos? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Operation cancelled"
  exit 0
fi

echo ""
echo "Processing repositories..."
echo ""

# Track statistics
SUCCESS_COUNT=0
FAIL_COUNT=0
FAILED_REPOS=()

# Process each repository
for REPO in $REPOS; do
  echo -n "Processing $GITHUB_ORG/$REPO..."

  # Process each collaborator
  ALL_SUCCESS=true
  for USER in "${COLLABORATORS[@]}"; do
    # Add collaborator with specified permission
    if gh api \
      --method PUT \
      "/repos/$GITHUB_ORG/$REPO/collaborators/$USER" \
      -f permission="$PERMISSION_LEVEL" \
      --silent 2>/dev/null; then
      # Success - continue
      :
    else
      # Try with just repo name if org/repo failed
      if gh api \
        --method PUT \
        "/repos/$(gh api user --jq .login)/$REPO/collaborators/$USER" \
        -f permission="$PERMISSION_LEVEL" \
        --silent 2>/dev/null; then
        # Success with user repo
        :
      else
        ALL_SUCCESS=false
        echo -e " ${RED}✗${NC} (Failed for $USER)"
        break
      fi
    fi
  done

  if $ALL_SUCCESS; then
    echo -e " ${GREEN}✓${NC}"
    ((SUCCESS_COUNT++))
  else
    ((FAIL_COUNT++))
    FAILED_REPOS+=("$REPO")
  fi
done

echo ""
echo "=================================================="
echo "Summary"
echo "=================================================="
echo -e "${GREEN}Successfully updated: $SUCCESS_COUNT repositories${NC}"

if [ $FAIL_COUNT -gt 0 ]; then
  echo -e "${RED}Failed: $FAIL_COUNT repositories${NC}"
  echo ""
  echo "Failed repositories:"
  for REPO in "${FAILED_REPOS[@]}"; do
    echo "  - $REPO"
  done
  echo ""
  echo "Common reasons for failure:"
  echo "  - Repository doesn't exist or was renamed"
  echo "  - Insufficient permissions (need admin access)"
  echo "  - User already has access through team membership"
fi

echo ""
echo "Collaborator access has been updated!"
echo ""
echo "Next steps:"
echo "1. Verify access at: https://github.com/$GITHUB_ORG?tab=repositories"
echo "2. Users should receive invitation emails"
echo "3. They need to accept the invitations to get access"

# Create a summary file
SUMMARY_FILE="collaborator-access-summary-$(date +%Y%m%d-%H%M%S).txt"
{
  echo "GitHub Collaborator Access Grant Summary"
  echo "Date: $(date)"
  echo "Organization: $GITHUB_ORG"
  echo "Users: ${COLLABORATORS[*]}"
  echo "Permission: $PERMISSION_LEVEL"
  echo ""
  echo "Successfully updated: $SUCCESS_COUNT repositories"
  echo "Failed: $FAIL_COUNT repositories"
  if [ $FAIL_COUNT -gt 0 ]; then
    echo ""
    echo "Failed repositories:"
    for REPO in "${FAILED_REPOS[@]}"; do
      echo "  - $REPO"
    done
  fi
} >"$SUMMARY_FILE"

echo ""
echo "Summary saved to: $SUMMARY_FILE"
