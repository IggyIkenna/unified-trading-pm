#!/usr/bin/env bash
#
# Temporarily disable branch protection for direct pushes
#
# Usage:
#   bash disable-branch-protection.sh [--all | repo1 repo2 ...]
#
# Prerequisites:
#   - GitHub CLI authenticated: gh auth login
#   - PAT with 'admin:org' or 'repo' (admin) scope
#   - If you get 403, update your PAT at: https://github.com/settings/tokens
#
# Examples:
#   bash disable-branch-protection.sh --all                    # All repos
#   bash disable-branch-protection.sh unified-trading-library   # Single repo
#

set -euo pipefail

ORG="IggyIkenna"
BRANCH="main"

# All repos with branch protection
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
  "unified-trading-library"
  "unified-trading-deployment-v2"
)

# Parse arguments
if [ $# -eq 0 ]; then
  echo "❌ Error: Specify --all or list of repos"
  echo ""
  echo "Usage: $0 [--all | repo1 repo2 ...]"
  exit 1
fi

if [ "$1" = "--all" ]; then
  REPOS=("${ALL_REPOS[@]}")
else
  REPOS=("$@")
fi

echo "🔓 Disabling branch protection for ${#REPOS[@]} repo(s)..."
echo ""

# Check gh auth status
if ! gh auth status &>/dev/null; then
  echo "❌ Error: GitHub CLI not authenticated"
  echo ""
  echo "Run: gh auth login"
  exit 1
fi

SUCCESS_COUNT=0
SKIP_COUNT=0
ERROR_COUNT=0

# Save protection configs to restore later
BACKUP_DIR="/tmp/branch-protection-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

for repo in "${REPOS[@]}"; do
  echo "🔧 $repo..."

  # Check if repo exists
  if ! gh repo view "$ORG/$repo" &>/dev/null; then
    echo "  ⚠️  Repo not found"
    ((SKIP_COUNT++))
    continue
  fi

  # Backup current protection settings (only writable fields for restore)
  if FULL_CONFIG=$(gh api "repos/$ORG/$repo/branches/$BRANCH/protection" 2>/dev/null); then
    # Transform GET response to PUT-compatible format
    echo "$FULL_CONFIG" | jq '{
            required_status_checks: (
                if .required_status_checks then {
                    strict: .required_status_checks.strict,
                    contexts: .required_status_checks.contexts
                } else null end
            ),
            enforce_admins: .enforce_admins.enabled,
            required_pull_request_reviews: (
                if .required_pull_request_reviews then {
                    dismiss_stale_reviews: .required_pull_request_reviews.dismiss_stale_reviews,
                    require_code_owner_reviews: .required_pull_request_reviews.require_code_owner_reviews,
                    required_approving_review_count: .required_pull_request_reviews.required_approving_review_count
                } else null end
            ),
            restrictions: (
                if .restrictions then {
                    users: .restrictions.users,
                    teams: .restrictions.teams,
                    apps: .restrictions.apps
                } else null end
            ),
            required_linear_history: .required_linear_history.enabled,
            allow_force_pushes: .allow_force_pushes.enabled,
            allow_deletions: .allow_deletions.enabled,
            block_creations: .block_creations.enabled,
            required_conversation_resolution: .required_conversation_resolution.enabled,
            lock_branch: .lock_branch.enabled,
            allow_fork_syncing: .allow_fork_syncing.enabled
        }' >"$BACKUP_DIR/$repo.json"
    echo "  💾 Backed up protection config"
  else
    echo "  ℹ️  No protection or already disabled"
  fi

  # Try to disable protection
  if gh api -X DELETE "repos/$ORG/$repo/branches/$BRANCH/protection" 2>/dev/null; then
    echo "  ✅ Disabled"
    ((SUCCESS_COUNT++))
  else
    ERROR=$(gh api -X DELETE "repos/$ORG/$repo/branches/$BRANCH/protection" 2>&1 || true)

    if echo "$ERROR" | grep -q "403"; then
      echo "  ❌ 403 Forbidden - PAT needs admin scope"
      echo "     Update at: https://github.com/settings/tokens"
      echo "     Required: 'repo' scope (full control)"
      ((ERROR_COUNT++))
    elif echo "$ERROR" | grep -q "404"; then
      echo "  ℹ️  Already disabled or no protection"
      ((SKIP_COUNT++))
    else
      echo "  ❌ Failed: $ERROR"
      ((ERROR_COUNT++))
    fi
  fi

  echo ""
done

echo "========================================================================"
echo "Summary"
echo "========================================================================"
echo "✅ Disabled:  $SUCCESS_COUNT"
echo "⏭️  Skipped:   $SKIP_COUNT"
echo "❌ Errors:    $ERROR_COUNT"
echo ""

if [ $SUCCESS_COUNT -gt 0 ]; then
  echo "📁 Protection configs backed up to: $BACKUP_DIR"
  echo ""
  echo "To restore later, run:"
  echo "  bash enable-branch-protection.sh --restore $BACKUP_DIR"
  echo ""
fi

if [ $ERROR_COUNT -gt 0 ]; then
  echo "⚠️  Some repos failed - check PAT permissions"
  echo ""
  echo "If you get 403 errors:"
  echo "1. Go to: https://github.com/settings/tokens"
  echo "2. Find your token (or create new fine-grained token)"
  echo "3. Add 'Administration' permission (read/write)"
  echo "4. Or for classic token: Enable 'repo' (full control)"
  echo ""
  exit 1
fi
