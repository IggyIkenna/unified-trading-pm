#!/usr/bin/env bash
#
# Re-enable branch protection after direct pushes
#
# Usage:
#   bash enable-branch-protection.sh [--all | --restore <backup-dir> | repo1 repo2 ...]
#
# Examples:
#   bash enable-branch-protection.sh --restore /tmp/branch-protection-backup-20260214-120000
#   bash enable-branch-protection.sh --all
#   bash enable-branch-protection.sh unified-trading-services
#

set -euo pipefail

ORG="IggyIkenna"
BRANCH="main"
RESTORE_DIR=""

# All repos
ALL_REPOS=(
    "execution-services"
    "features-calendar-service"
    "features-delta-one-service"
    "features-onchain-service"
    "features-volatility-service"
    "instruments-service"
    "market-data-processing-service"
    "market-tick-data-handler"
    "ml-inference-service"
    "ml-training-service"
    "sports-betting-service"
    "strategy-service"
    "unified-trading-services"
    "unified-trading-deployment-v2"
)

# Default protection config (if no backup)
DEFAULT_PROTECTION='{
  "required_status_checks": {
    "strict": true,
    "contexts": ["quality-gates"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}'

# Parse arguments
if [ $# -eq 0 ]; then
    echo "❌ Error: Specify --all, --restore <dir>, or list of repos"
    echo ""
    echo "Usage: $0 [--all | --restore <dir> | repo1 repo2 ...]"
    exit 1
fi

if [ "$1" = "--restore" ]; then
    RESTORE_DIR="$2"
    if [ ! -d "$RESTORE_DIR" ]; then
        echo "❌ Error: Backup directory not found: $RESTORE_DIR"
        exit 1
    fi
    # Get repos from backup files
    REPOS=()
    for backup_file in "$RESTORE_DIR"/*.json; do
        repo=$(basename "$backup_file" .json)
        REPOS+=("$repo")
    done
    echo "📁 Restoring from backup: $RESTORE_DIR"
elif [ "$1" = "--all" ]; then
    REPOS=("${ALL_REPOS[@]}")
else
    REPOS=("$@")
fi

echo "🔒 Enabling branch protection for ${#REPOS[@]} repo(s)..."
echo ""

SUCCESS_COUNT=0
ERROR_COUNT=0

for repo in "${REPOS[@]}"; do
    echo "🔧 $repo..."

    # Check if repo exists
    if ! gh repo view "$ORG/$repo" &>/dev/null; then
        echo "  ⚠️  Repo not found"
        ((ERROR_COUNT++))
        continue
    fi

    # Determine config to use
    if [ -n "$RESTORE_DIR" ] && [ -f "$RESTORE_DIR/$repo.json" ]; then
        CONFIG="@$RESTORE_DIR/$repo.json"
        echo "  📄 Using backed up config"
    else
        CONFIG="$DEFAULT_PROTECTION"
        echo "  📄 Using default config"
    fi

    # Enable protection
    if [ "${CONFIG:0:1}" = "@" ]; then
        # Config from file
        if gh api -X PUT "repos/$ORG/$repo/branches/$BRANCH/protection" \
            --input "${CONFIG:1}" &>/dev/null; then
            echo "  ✅ Enabled"
            ((SUCCESS_COUNT++))
        else
            ERROR=$(gh api -X PUT "repos/$ORG/$repo/branches/$BRANCH/protection" \
                --input "${CONFIG:1}" 2>&1 || true)
            echo "  ❌ Failed: $ERROR"
            ((ERROR_COUNT++))
        fi
    else
        # Config from string
        if echo "$CONFIG" | gh api -X PUT "repos/$ORG/$repo/branches/$BRANCH/protection" \
            --input - &>/dev/null; then
            echo "  ✅ Enabled"
            ((SUCCESS_COUNT++))
        else
            ERROR=$(echo "$CONFIG" | gh api -X PUT "repos/$ORG/$repo/branches/$BRANCH/protection" \
                --input - 2>&1 || true)
            echo "  ❌ Failed: $ERROR"
            ((ERROR_COUNT++))
        fi
    fi

    echo ""
done

echo "========================================================================"
echo "Summary"
echo "========================================================================"
echo "✅ Enabled:   $SUCCESS_COUNT"
echo "❌ Errors:    $ERROR_COUNT"
echo ""

if [ $ERROR_COUNT -gt 0 ]; then
    echo "⚠️  Some repos failed - check PAT permissions"
    exit 1
fi
