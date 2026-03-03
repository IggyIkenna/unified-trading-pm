#!/usr/bin/env bash
# Add GitHub secret to a single repo or all existing repos
#
# This script uses GitHub CLI authentication (no hardcoded tokens)
# Run 'gh auth login' once to authenticate
#
# Usage:
#   bash add-secret-to-repo.sh <repo-name>    # Single repo
#   bash add-secret-to-repo.sh --all          # All existing repos
#

set -euo pipefail

# Configuration
SECRET_NAME="AUTOMATION_GITHUB_TOKEN"
ORG="IggyIkenna"

# Check if gh CLI is installed and authenticated
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Install with: brew install gh"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

# Get the secret value from environment or prompt
if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "Enter the GitHub token value to store as secret:"
    read -rs GITHUB_TOKEN
    echo ""
fi

# All potential service repos (some may not exist yet)
ALL_REPOS=(
    "market-data-processing-service"
    "instruments-service"
    "order-book-service"
    "ml-training-service"
    "portfolio-reporting-service"
    "portfolio-management-service"
    "orchestration-service"
    "notifications-service"
    "position-aggregation-service"
    "risk-management-service"
    "strategy-execution-service"
    "signal-generation-service"
    "trade-execution-service"
    "unified-trading-codex"
    "execution-services"
    "strategy-service"
    "unified-trading-library"
    "unified-config-interface"
    "unified-domain-client"
    "unified-events-interface"
    "unified-market-interface"
    "unified-feature-calculator-library"
    "execution-algo-library"
    "matching-engine-library"
)

add_secret_to_repo() {
    local repo=$1

    # Check if repo exists
    if ! gh repo view "$ORG/$repo" --json name -q .name &>/dev/null; then
        echo "   ⏭️  Repo does not exist yet"
        return 1
    fi

    # Check Actions status
    ACTIONS_STATUS=$(gh api "repos/$ORG/$repo/actions/permissions" --jq '.enabled' 2>/dev/null || echo "unknown")

    if [ "$ACTIONS_STATUS" = "false" ]; then
        echo "   🔧 Enabling Actions..."
        gh api -X PUT "repos/$ORG/$repo/actions/permissions" \
            -f enabled=true \
            -f allowed_actions=all 2>/dev/null || true
        sleep 1
    fi

    # Add the secret using gh CLI
    echo "$GITHUB_TOKEN" | gh secret set "$SECRET_NAME" -R "$ORG/$repo" --body - 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "   ✅ Secret added successfully"
        return 0
    else
        echo "   ❌ Failed to add secret"
        return 1
    fi
}

# Main logic
if [ "${1:-}" = "--all" ]; then
    echo "🔄 Adding secret to all existing repos..."
    SUCCESS=0
    FAILED=0
    SKIPPED=0

    for repo in "${ALL_REPOS[@]}"; do
        echo "📦 Processing $repo..."
        if add_secret_to_repo "$repo"; then
            ((SUCCESS++))
        else
            if gh repo view "$ORG/$repo" --json name -q .name &>/dev/null; then
                ((FAILED++))
            else
                ((SKIPPED++))
            fi
        fi
    done

    echo ""
    echo "📊 Summary:"
    echo "   ✅ Success: $SUCCESS"
    echo "   ❌ Failed: $FAILED"
    echo "   ⏭️  Skipped (don't exist): $SKIPPED"
elif [ -n "${1:-}" ]; then
    echo "📦 Adding secret to $1..."
    add_secret_to_repo "$1"
else
    echo "Usage:"
    echo "  bash $0 <repo-name>    # Add to single repo"
    echo "  bash $0 --all          # Add to all repos"
    exit 1
fi

echo ""
echo "🔒 Security Notes:"
echo "   - The secret is now stored securely in GitHub"
echo "   - Clear your shell history if you entered the token"
echo "   - Consider rotating tokens regularly"
