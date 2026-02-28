#!/bin/bash
#
# Copy Project Workflows - Post-Trade and Execution
#
# Wrapper around utilities/copy-project-workflows.sh with updated label filter
# for POST-TRADE-AND-EXECUTION instead of "cleanup".
#
# GitHub API Limitation: Cannot CREATE workflows via API
# This script shows which workflows exist on template project (e.g., #5)
# and provides EXACT instructions to replicate them on new project.
#
# Usage:
#   bash 04-copy-workflows.sh --from 5 --to 6
#

set -euo pipefail

# Defaults
FROM_PROJECT="${FROM_PROJECT:-5}"
TO_PROJECT=""
ORG="IggyIkenna"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --from)
            FROM_PROJECT="$2"
            shift 2
            ;;
        --to)
            TO_PROJECT="$2"
            shift 2
            ;;
        --org)
            ORG="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: bash 04-copy-workflows.sh --from <template-number> --to <new-number>"
            echo ""
            echo "Options:"
            echo "  --from  Template project number (default: 5 for Initial Cleanup)"
            echo "  --to    New project number to configure (required)"
            echo "  --org   GitHub user/org (default: IggyIkenna)"
            echo ""
            echo "Example:"
            echo "  bash 04-copy-workflows.sh --from 5 --to 6"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate
if [ -z "$TO_PROJECT" ]; then
    echo "Error: --to is required"
    exit 1
fi

echo "========================================="
echo "Copy Project Workflows"
echo "========================================="
echo ""
echo "Template Project: #$FROM_PROJECT"
echo "Target Project:   #$TO_PROJECT"
echo "Owner:            $ORG"
echo ""
echo "⚠️  IMPORTANT NOTE:"
echo "    This project uses label 'POST-TRADE-AND-EXECUTION' instead of 'cleanup'"
echo "    Update the auto-add workflow accordingly!"
echo ""

# Call the base copy-project-workflows script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_SCRIPT="$SCRIPT_DIR/../../utilities/copy-project-workflows.sh"

if [ ! -f "$BASE_SCRIPT" ]; then
    echo "❌ Base script not found: $BASE_SCRIPT"
    echo "   Expected: unified-trading-codex/11-project-management/github-integration/scripts/utilities/copy-project-workflows.sh"
    exit 1
fi

# Run base script
bash "$BASE_SCRIPT" --from "$FROM_PROJECT" --to "$TO_PROJECT" --org "$ORG"

# Additional instructions specific to Post-Trade and Execution
echo ""
echo "========================================="
echo "Post-Trade and Execution Specific"
echo "========================================="
echo ""
echo "⭐ CRITICAL: Update Label Filter"
echo ""
echo "When configuring 'Auto-add to project' workflow:"
echo "  - Change label filter from 'cleanup' to 'POST-TRADE-AND-EXECUTION'"
echo "  - This ensures new issues with the project label auto-add to the board"
echo ""
echo "Configuration:"
echo "  1. Go to: https://github.com/users/$ORG/projects/$TO_PROJECT/settings/workflows"
echo "  2. Create workflow: 'Auto-add to project'"
echo "  3. Trigger: Item added to repository"
echo "  4. Filters: Label = 'POST-TRADE-AND-EXECUTION'"
echo "  5. Action: Add to this project"
echo ""
echo "Other workflows (from template #$FROM_PROJECT):"
echo "  - Auto-add sub-issues"
echo "  - Item closed → Set status to 'Done'"
echo "  - Pull request merged → Close linked issues ⭐"
echo "  - Auto-close issue"
echo "  - Auto-archive items (30 days)"
echo "  - Item added → Set status to 'Todo'"
echo "  - PR linked → Set status to 'In Progress'"
echo ""
echo "========================================="
echo ""
echo "After configuring workflows, verify setup:"
echo "  bash 05-verify-setup.sh --project $TO_PROJECT"
echo ""
echo "========================================="
