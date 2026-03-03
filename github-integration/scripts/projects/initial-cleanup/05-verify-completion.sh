#!/bin/bash
# Verify Initial Cleanup Project Completion
#
# Checks status of all cleanup issues and generates completion report.
#
# Usage:
#   bash 05-verify-completion.sh

set -euo pipefail

ORG="IggyIkenna"

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
echo "Initial Cleanup Project - Status Report"
echo "========================================="
echo ""

TOTAL=0
OPEN=0
CLOSED=0
ERRORS=0

echo "| Repo | Issue | State | Labels | Violations |"
echo "|------|-------|-------|--------|------------|"

for repo in "${REPOS[@]}"; do
    TOTAL=$((TOTAL + 1))

    # Find cleanup issue
    ISSUE_DATA=$(gh issue list \
        --repo "$ORG/$repo" \
        --label "cleanup" \
        --json number,state,labels \
        --jq '.[0]' 2>/dev/null || echo "{}")

    ISSUE_NUMBER=$(echo "$ISSUE_DATA" | jq -r '.number // "N/A"')
    STATE=$(echo "$ISSUE_DATA" | jq -r '.state // "ERROR"')
    LABELS=$(echo "$ISSUE_DATA" | jq -r '.labels[].name // empty' | tr '\n' ',' | sed 's/,$//')

    # Check manifest for violation count
    MANIFEST_FILE="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/$repo/CODEX_VIOLATIONS_MANIFEST.md"
    if [ -f "$MANIFEST_FILE" ]; then
        VIOLATIONS=$(grep "Total violations:" "$MANIFEST_FILE" | grep -o "[0-9]*" || echo "?")
    else
        VIOLATIONS="?"
    fi

    # Count by state
    if [ "$STATE" = "OPEN" ]; then
        OPEN=$((OPEN + 1))
        echo "| $repo | #$ISSUE_NUMBER | 🟡 $STATE | $LABELS | $VIOLATIONS |"
    elif [ "$STATE" = "CLOSED" ]; then
        CLOSED=$((CLOSED + 1))
        echo "| $repo | #$ISSUE_NUMBER | ✅ $STATE | $LABELS | $VIOLATIONS |"
    else
        ERRORS=$((ERRORS + 1))
        echo "| $repo | #$ISSUE_NUMBER | ❌ $STATE | - | - |"
    fi
done

echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo "  Total repos: $TOTAL"
echo "  Open: $OPEN"
echo "  Closed: $CLOSED"
echo "  Errors: $ERRORS"
echo ""

if [ $OPEN -eq 0 ] && [ $ERRORS -eq 0 ]; then
    echo "🎉 PROJECT COMPLETE! All cleanup issues resolved."
    echo ""
    echo "Next steps:"
    echo "  - Archive completed project"
    echo "  - Start COD-SIZE refactoring (Project #6)"
else
    echo "📋 Next steps:"
    echo "  - Run batch fix for remaining $OPEN issues:"
    echo "    bash 04-run-batch-fix.sh --model auto --require-labels cleanup --state open"
    echo ""
    echo "  - Or run locally for specific repo (see AGENT_PROMPT.md)"
fi

echo ""
