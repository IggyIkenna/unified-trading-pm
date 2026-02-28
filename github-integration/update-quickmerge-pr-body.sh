#!/bin/bash
# Update all quickmerge.sh scripts to include issue references in PR body

set -e

WORKSPACE_ROOT="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"

SERVICES=(
    "instruments-service"
    "execution-services"
    "market-data-processing-service"
    "market-tick-data-handler"
    "features-volatility-service"
    "features-delta-one-service"
    "unified-trading-deployment-v2"
    "features-calendar-service"
    "features-onchain-service"
    "unified-trading-services"
    "ml-inference-service"
    "ml-training-service"
    "strategy-service"
)

echo "🔧 Updating quickmerge.sh scripts to include issue refs in PR body..."
echo ""

for service in "${SERVICES[@]}"; do
    SCRIPT_PATH="$WORKSPACE_ROOT/$service/scripts/quickmerge.sh"

    if [ ! -f "$SCRIPT_PATH" ]; then
        echo "⏭️  Skipping $service (no quickmerge.sh)"
        continue
    fi

    # Check if already updated
    if grep -q "ISSUE_REFS=" "$SCRIPT_PATH"; then
        echo "✅ $service (already updated)"
        continue
    fi

    # Create backup
    cp "$SCRIPT_PATH" "$SCRIPT_PATH.bak"

    # Use Python for safer multiline replacement
    python3 - "$SCRIPT_PATH" << 'PYEOF'
import sys
script_path = sys.argv[1]

with open(script_path, 'r') as f:
    content = f.read()

# Find and replace the PR creation section
old_pattern = '''# Create PR with auto-merge
PR_URL=$(gh pr create \\
    --title "$COMMIT_MSG" \\
    --body "Automated PR. Will auto-merge once quality gates pass." \\
    --base main \\
    --head "$BRANCH" 2>/dev/null)'''

new_pattern = '''# Create PR with auto-merge
# Extract issue references from commit message for PR body
ISSUE_REFS=$(echo "$COMMIT_MSG" | grep -o -E "(Fixes|Closes|Resolves) [^#]*#[0-9]+" || echo "")
PR_BODY="Automated PR. Will auto-merge once quality gates pass.

$ISSUE_REFS"

PR_URL=$(gh pr create \\
    --title "$COMMIT_MSG" \\
    --body "$PR_BODY" \\
    --base main \\
    --head "$BRANCH" 2>/dev/null)'''

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    with open(script_path, 'w') as f:
        f.write(content)
    print(f"✅ Updated")
else:
    print(f"⚠️  Pattern not found - manual check needed")
    sys.exit(1)
PYEOF

    if [ $? -eq 0 ]; then
        echo "✅ $service"
        rm "$SCRIPT_PATH.bak"
    else
        echo "❌ $service (failed - restored backup)"
        mv "$SCRIPT_PATH.bak" "$SCRIPT_PATH"
    fi
done

echo ""
echo "✅ All quickmerge scripts updated!"
