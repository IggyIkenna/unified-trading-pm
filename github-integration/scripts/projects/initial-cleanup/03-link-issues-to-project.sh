#!/bin/bash
# Link Initial Cleanup Issues to Project #5
#
# Finds all cleanup issues and adds them to the Initial Cleanup project.
#
# Usage:
#   bash 03-link-issues-to-project.sh [--project-number N]

set -euo pipefail

ORG="IggyIkenna"
PROJECT_NUMBER="${1:-5}"  # Default: Project #5

REPOS=(
    "execution-services"
    "strategy-service"
    "instruments-service"
    "unified-trading-library"
    "market-data-processing-service"
    "ml-training-service"
    "ml-inference-service"
    "features-delta-one-service"
    "features-volatility-service"
    "features-calendar-service"
    "features-onchain-service"
    "market-tick-data-handler"
    "unified-trading-deployment-v2"
)

echo "========================================="
echo "Linking Issues to Project #$PROJECT_NUMBER"
echo "========================================="
echo ""

LINKED=0
ALREADY_LINKED=0

for repo in "${REPOS[@]}"; do
    echo "🔗 $repo..."

    # Find cleanup issue
    ISSUE_NUMBER=$(gh issue list \
        --repo "$ORG/$repo" \
        --label "cleanup" \
        --json number \
        --jq '.[0].number' 2>/dev/null || echo "")

    if [ -z "$ISSUE_NUMBER" ] || [ "$ISSUE_NUMBER" = "null" ]; then
        echo "  ⚠️  No cleanup issue found"
        continue
    fi

    # Add to project
    if gh project item-add "$PROJECT_NUMBER" --owner "$ORG" --url "https://github.com/$ORG/$repo/issues/$ISSUE_NUMBER" 2>/dev/null; then
        echo "  ✅ Linked #$ISSUE_NUMBER"
        LINKED=$((LINKED + 1))
    else
        echo "  ℹ️  Already linked #$ISSUE_NUMBER"
        ALREADY_LINKED=$((ALREADY_LINKED + 1))
    fi

    sleep 0.3
done

echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo "  Newly linked: $LINKED"
echo "  Already linked: $ALREADY_LINKED"
echo ""
echo "View project: https://github.com/users/$ORG/projects/$PROJECT_NUMBER"
echo ""
echo "Next: bash 04-run-batch-fix.sh --model auto --require-labels cleanup --state open"
echo ""
