#!/bin/bash
#
# Filter Service-Specific Issues
#
# Takes a list of issue numbers and filters out non-service issues
# (Epic, Task, Subtask hierarchy issues)
#
# Usage:
#   bash filter-service-issues.sh "589 588 587 586 537"
#

ISSUES="$1"

if [ -z "$ISSUES" ]; then
    echo "Usage: bash filter-service-issues.sh \"<issue numbers>\""
    exit 1
fi

# Convert to array
read -ra ISSUE_ARRAY <<< "$ISSUES"

SERVICE_ISSUES=()

for ISSUE in "${ISSUE_ARRAY[@]}"; do
    # Fetch issue title
    TITLE=$(gh issue view "$ISSUE" --repo IggyIkenna/unified-trading-codex --json title -q '.title' 2>/dev/null)

    if [ -z "$TITLE" ]; then
        echo "⚠️  Issue #$ISSUE not found, skipping" >&2
        continue
    fi

    # Check if it's a hierarchy issue
    if [[ "$TITLE" =~ ^\[(Subtask|Task|Epic)\] ]]; then
        echo "⚠️  Skipping hierarchy issue #$ISSUE: $TITLE" >&2
        continue
    fi

    # Check if it has a service name
    if [[ "$TITLE" =~ ^\[[a-z-]+\] ]]; then
        SERVICE_ISSUES+=("$ISSUE")
    else
        echo "⚠️  Skipping non-service issue #$ISSUE: $TITLE" >&2
    fi
done

# Output filtered list
echo "${SERVICE_ISSUES[*]}"
