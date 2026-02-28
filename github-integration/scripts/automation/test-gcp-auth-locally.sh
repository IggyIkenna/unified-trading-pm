#!/usr/bin/env bash
# Test GCP Secret Manager authentication locally (same as VM would use)

set -euo pipefail

echo "🔐 Testing GCP Secret Manager authentication locally..."
echo ""

# Fetch token from Secret Manager (same as VM does)
echo "📥 Fetching token from GCP Secret Manager..."
GITHUB_TOKEN=$(gcloud secrets versions access latest \
  --secret=github-automation-token \
  --project=central-element-323112)

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Failed to fetch token"
    exit 1
fi

echo "✅ Token fetched successfully (${#GITHUB_TOKEN} characters)"
echo ""

# Authenticate gh CLI with the token
echo "🔧 Authenticating gh CLI..."
echo "$GITHUB_TOKEN" | gh auth login --with-token

# Verify authentication
echo ""
echo "🧪 Testing authentication..."
if gh auth status; then
    echo ""
    echo "✅ Successfully authenticated using GCP Secret Manager!"
    echo ""
    echo "Now you can run automation scripts:"
    echo "  bash run-cleanup-batch-fix.sh --model auto --max-parallel 7"
else
    echo "❌ Authentication failed"
    exit 1
fi
