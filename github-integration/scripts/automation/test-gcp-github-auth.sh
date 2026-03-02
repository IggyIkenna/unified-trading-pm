#!/usr/bin/env bash
#
# Test GCP Secret Manager GitHub Authentication
#
# This script verifies that:
# 1. GCP Secret Manager is accessible
# 2. github-automation-token secret exists and can be fetched
# 3. gh CLI can authenticate with the token
# 4. Git operations would work (tests gh auth status)
#
# Usage:
#   bash test-gcp-github-auth.sh              # Full test (fetches + authenticates)
#   bash test-gcp-github-auth.sh --check-only # Check only (don't re-authenticate)
#   bash test-gcp-github-auth.sh --quick      # Skip authentication (just check secret exists)
#
# Exit codes:
#   0 = All tests passed
#   1 = GCP Secret Manager not accessible
#   2 = Secret not found or can't be fetched
#   3 = gh CLI authentication failed
#   4 = gh CLI not installed

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SECRET_NAME="${GITHUB_TOKEN_SECRET:-github-automation-token}"
GCP_PROJECT="${GCP_PROJECT:?GCP_PROJECT required}"
CHECK_ONLY=false
QUICK=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--check-only|--quick]"
            echo ""
            echo "Options:"
            echo "  --check-only  Check secret exists but don't re-authenticate"
            echo "  --quick       Only verify secret exists (fastest)"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔐 Testing GCP Secret Manager GitHub Authentication${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test 1: Check if gcloud is installed and configured
echo -e "${YELLOW}[1/5] Checking gcloud CLI...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not installed${NC}"
    echo "   Install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

GCLOUD_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "not-set")
if [ "$GCLOUD_ACCOUNT" = "not-set" ] || [ -z "$GCLOUD_ACCOUNT" ]; then
    echo -e "${RED}❌ gcloud not authenticated${NC}"
    echo "   Run: gcloud auth login"
    exit 1
fi

echo -e "${GREEN}✅ gcloud CLI configured${NC}"
echo -e "   Account: $GCLOUD_ACCOUNT"
echo -e "   Project: $GCP_PROJECT"
echo ""

# Test 2: Check if gh CLI is installed
echo -e "${YELLOW}[2/5] Checking gh CLI...${NC}"
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ gh CLI not installed${NC}"
    echo "   Install: brew install gh"
    exit 4
fi

GH_VERSION=$(gh --version | head -1)
echo -e "${GREEN}✅ gh CLI installed${NC}"
echo -e "   Version: $GH_VERSION"
echo ""

# Test 3: Fetch secret from Secret Manager
echo -e "${YELLOW}[3/5] Fetching GitHub token from Secret Manager...${NC}"
echo -e "   Secret: $SECRET_NAME"
echo -e "   Project: $GCP_PROJECT"

if ! GITHUB_TOKEN=$(gcloud secrets versions access latest \
    --secret="$SECRET_NAME" \
    --project="$GCP_PROJECT" 2>&1); then
    echo -e "${RED}❌ Failed to fetch secret${NC}"
    echo -e "${RED}   Error: $GITHUB_TOKEN${NC}"
    echo ""
    echo "Possible causes:"
    echo "  1. Secret doesn't exist: gcloud secrets list --project=$GCP_PROJECT"
    echo "  2. No permission: Check IAM role 'roles/secretmanager.secretAccessor'"
    echo "  3. Wrong project: Verify GCP_PROJECT environment variable"
    exit 2
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ Secret is empty${NC}"
    exit 2
fi

TOKEN_LENGTH=${#GITHUB_TOKEN}
TOKEN_PREFIX=$(echo "$GITHUB_TOKEN" | head -c 20)

echo -e "${GREEN}✅ Token fetched successfully${NC}"
echo -e "   Length: $TOKEN_LENGTH characters"
echo -e "   Prefix: ${TOKEN_PREFIX}..."
echo ""

# If quick mode, stop here
if [ "$QUICK" = true ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Quick check passed (secret accessible)${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 0
fi

# Test 4: Check current gh auth status
echo -e "${YELLOW}[4/5] Checking current gh auth status...${NC}"
if gh auth status &>/dev/null; then
    CURRENT_USER=$(gh api user --jq .login 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✅ Already authenticated to GitHub${NC}"
    echo -e "   User: $CURRENT_USER"

    if [ "$CHECK_ONLY" = true ]; then
        echo ""
        echo -e "${BLUE}ℹ️  Skipping re-authentication (--check-only)${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}✅ All checks passed (already authenticated)${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        exit 0
    fi
else
    echo -e "${YELLOW}⚠️  Not currently authenticated${NC}"
fi
echo ""

# Test 5: Authenticate with the token
echo -e "${YELLOW}[5/5] Authenticating gh CLI with token from Secret Manager...${NC}"

# Save current auth state (backup)
GH_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/gh"
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -d "$GH_CONFIG_DIR" ] && [ -f "$GH_CONFIG_DIR/hosts.yml" ]; then
    mkdir -p "$GH_CONFIG_DIR/backups"
    cp "$GH_CONFIG_DIR/hosts.yml" "$GH_CONFIG_DIR/backups/hosts.yml.$BACKUP_TIMESTAMP" 2>/dev/null || true
    echo -e "${BLUE}ℹ️  Backed up existing auth to: $GH_CONFIG_DIR/backups/hosts.yml.$BACKUP_TIMESTAMP${NC}"
fi

# Authenticate
if echo "$GITHUB_TOKEN" | gh auth login --with-token 2>&1; then
    echo -e "${GREEN}✅ Authentication successful${NC}"
else
    echo -e "${RED}❌ Authentication failed${NC}"
    exit 3
fi
echo ""

# Verify authentication
echo -e "${YELLOW}Verifying authentication...${NC}"
if gh auth status 2>&1; then
    AUTHENTICATED_USER=$(gh api user --jq .login 2>/dev/null || echo "unknown")
    echo ""
    echo -e "${GREEN}✅ Verified: authenticated as $AUTHENTICATED_USER${NC}"
else
    echo -e "${RED}❌ Verification failed${NC}"
    exit 3
fi

# Test GitHub API access
echo ""
echo -e "${YELLOW}Testing GitHub API access...${NC}"
if gh api user --jq '.login, .name' &>/dev/null; then
    USER_LOGIN=$(gh api user --jq .login)
    USER_NAME=$(gh api user --jq .name)
    echo -e "${GREEN}✅ GitHub API accessible${NC}"
    echo -e "   Login: $USER_LOGIN"
    echo -e "   Name: $USER_NAME"
else
    echo -e "${RED}❌ Cannot access GitHub API${NC}"
    echo "   Token may have insufficient permissions"
    exit 3
fi

# Success
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Summary:"
echo "  ✅ GCP Secret Manager accessible"
echo "  ✅ GitHub token retrieved ($TOKEN_LENGTH chars)"
echo "  ✅ gh CLI authenticated as $AUTHENTICATED_USER"
echo "  ✅ GitHub API accessible"
echo ""
echo "You can now run automation scripts that require GitHub authentication."
echo ""

exit 0
