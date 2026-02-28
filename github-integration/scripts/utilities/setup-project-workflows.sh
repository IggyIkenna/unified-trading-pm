#!/bin/bash
#
# Setup Project Workflows - Manual Instructions Generator
#
# GitHub's API doesn't support creating project workflows programmatically.
# This script generates the exact manual steps needed.
#
# Usage:
#   bash setup-project-workflows.sh --project-number 5 --org IggyIkenna
#

set -euo pipefail

# Defaults
ORG="${ORG:-IggyIkenna}"
PROJECT_NUMBER=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-number)
            PROJECT_NUMBER="$2"
            shift 2
            ;;
        --org)
            ORG="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: bash setup-project-workflows.sh --project-number <number> [--org <org>]"
            echo ""
            echo "Options:"
            echo "  --project-number  GitHub project number (required)"
            echo "  --org             GitHub organization/user (default: IggyIkenna)"
            echo ""
            echo "Example:"
            echo "  bash setup-project-workflows.sh --project-number 5 --org IggyIkenna"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate
if [ -z "$PROJECT_NUMBER" ]; then
    echo "Error: --project-number is required"
    exit 1
fi

# Get project details
echo "Fetching project details..."
PROJECT_TITLE=$(gh project view "$PROJECT_NUMBER" --owner "$ORG" --format json --jq '.title' 2>/dev/null || echo "Unknown")

echo ""
echo "========================================="
echo "Project Workflow Setup Instructions"
echo "========================================="
echo ""
echo "Project: #$PROJECT_NUMBER - $PROJECT_TITLE"
echo "Owner: $ORG"
echo ""
echo "⚠️  IMPORTANT: GitHub's GraphQL API doesn't support creating workflows"
echo "    You MUST configure these MANUALLY for automation to work"
echo ""

# Step 1: Navigate to workflows
echo "========================================="
echo "Step 1: Open Project Workflows Settings"
echo "========================================="
echo ""
echo "URL: https://github.com/users/$ORG/projects/$PROJECT_NUMBER/settings/workflows"
echo ""
echo "Or manually:"
echo "  1. Go to: https://github.com/users/$ORG/projects/$PROJECT_NUMBER"
echo "  2. Click: '...' (more options) → Settings"
echo "  3. Click: 'Workflows' in left sidebar"
echo ""
echo "Press Enter when ready..."
read -r

# Step 2: Workflow 1 - Auto-add issues
echo ""
echo "========================================="
echo "Step 2: Create 'Auto-add issues' Workflow"
echo "========================================="
echo ""
echo "This workflow automatically adds labeled issues to the project."
echo ""
echo "Click: 'Create workflow' button"
echo ""
echo "Configuration:"
echo "  Name: Auto-add issues with cleanup label"
echo ""
echo "  Trigger:"
echo "    Event: Item added to repository"
echo "    Filters: Label = 'cleanup'"
echo ""
echo "  Action:"
echo "    Action type: Add to project"
echo "    Project: #$PROJECT_NUMBER ($PROJECT_TITLE)"
echo ""
echo "Then click: 'Save workflow'"
echo ""
echo "✓ Result: New issues with 'cleanup' label auto-add to project"
echo ""
echo "Press Enter when done..."
read -r

# Step 3: Workflow 2 - Auto-close on PR merge
echo ""
echo "========================================="
echo "Step 3: Create 'Auto-close on PR' Workflow"
echo "========================================="
echo ""
echo "This workflow automatically closes issues when linked PRs merge."
echo ""
echo "Click: 'Create workflow' button"
echo ""
echo "Configuration:"
echo "  Name: Auto-close on PR merge"
echo ""
echo "  Trigger:"
echo "    Event: Pull request merged"
echo "    Filters: Pull request closes issue"
echo ""
echo "  Action:"
echo "    Action type: Set status"
echo "    Status: Done"
echo ""
echo "Then click: 'Save workflow'"
echo ""
echo "✓ Result: Issues auto-close when PRs merge with 'Closes #issue' in body"
echo ""
echo "Press Enter when done..."
read -r

# Step 4: Workflow 3 - Auto-archive (optional)
echo ""
echo "========================================="
echo "Step 4: Create 'Auto-archive' Workflow (Optional)"
echo "========================================="
echo ""
echo "This workflow archives completed items after 30 days."
echo ""
echo "Click: 'Create workflow' button"
echo ""
echo "Configuration:"
echo "  Name: Auto-archive completed items"
echo ""
echo "  Trigger:"
echo "    Event: Item status changed"
echo "    Filters: Status = 'Done'"
echo "    Wait: 30 days"
echo ""
echo "  Action:"
echo "    Action type: Archive item"
echo ""
echo "Then click: 'Save workflow'"
echo ""
echo "✓ Result: Items auto-archive 30 days after completion"
echo ""
echo "Press Enter when done (or Ctrl+C to skip)..."
read -r

# Verification
echo ""
echo "========================================="
echo "Verification"
echo "========================================="
echo ""
echo "To verify workflows are working:"
echo ""
echo "1. Create a test issue:"
echo "   gh issue create \\"
echo "     --repo $ORG/unified-trading-codex \\"
echo "     --title \"[TEST] Workflow verification\" \\"
echo "     --body \"Testing auto-add workflow\" \\"
echo "     --label cleanup"
echo ""
echo "2. Check if it appears in project:"
echo "   gh project view $PROJECT_NUMBER --owner $ORG"
echo ""
echo "3. Create PR that closes the test issue:"
echo "   - In PR body: 'Closes #<issue-number>'"
echo "   - Merge PR"
echo "   - Check if issue moves to 'Done' status"
echo ""
echo "4. If working correctly, close test issue:"
echo "   gh issue close <issue-number> --repo $ORG/unified-trading-codex"
echo ""

# Summary
echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo ""
echo "✅ Workflows configured for project #$PROJECT_NUMBER"
echo ""
echo "Configured workflows:"
echo "  1. ✓ Auto-add issues (label: cleanup)"
echo "  2. ✓ Auto-close on PR merge"
echo "  3. ✓ Auto-archive (optional)"
echo ""
echo "Project URL:"
echo "  https://github.com/users/$ORG/projects/$PROJECT_NUMBER"
echo ""
echo "Workflows URL:"
echo "  https://github.com/users/$ORG/projects/$PROJECT_NUMBER/settings/workflows"
echo ""
echo "========================================="
echo ""
echo "🎉 Workflow setup complete!"
echo ""
echo "Your project will now:"
echo "  - Auto-add issues with 'cleanup' label"
echo "  - Auto-close issues when PRs merge"
echo "  - Auto-archive items after 30 days (if enabled)"
echo ""
echo "Ready to run batch-fix-v2.sh!"
echo "========================================="
