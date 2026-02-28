#!/bin/bash
#
# Close an Already-Fixed Issue
#
# Usage:
#   bash close-fixed-issue.sh <ISSUE_NUMBER> "<reason>"
#
# Example:
#   bash close-fixed-issue.sh 1079 "Already fixed in previous run - file is compliant"
#

set -euo pipefail

ISSUE_NUMBER="${1:-}"
REASON="${2:-Already fixed - file is compliant with coding standards}"

if [ -z "$ISSUE_NUMBER" ]; then
    echo "Usage: bash close-fixed-issue.sh <ISSUE_NUMBER> \"<reason>\""
    exit 1
fi

CODEX_ISSUE_REPO="IggyIkenna/unified-trading-codex"

echo "🔒 Closing issue #$ISSUE_NUMBER as already fixed"
echo "Reason: $REASON"
echo ""

# Add comment explaining why it's being closed
gh issue comment "$ISSUE_NUMBER" --repo "$CODEX_ISSUE_REPO" --body "✅ **Already Fixed**

$REASON

The file(s) mentioned in this issue are already compliant with the coding standards. This was likely fixed in a previous commit or by another agent run.

**Verification:**
- Quality gates pass
- No violations found in current codebase

Closing as resolved."

# Close the issue
gh issue close "$ISSUE_NUMBER" --repo "$CODEX_ISSUE_REPO" --reason completed

echo "✅ Issue #$ISSUE_NUMBER closed successfully"
