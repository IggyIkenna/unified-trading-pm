#!/bin/bash
#
# Copy Project Workflows from Template (Project #3)
#
# GitHub API Limitation: Cannot CREATE workflows via API
# This script shows which workflows exist on template project #3
# and provides EXACT instructions to replicate them on new project
#
# Usage:
#   bash copy-project-workflows.sh --from 3 --to 5
#

set -euo pipefail

# Defaults
FROM_PROJECT=""
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
    -h | --help)
      echo "Usage: bash copy-project-workflows.sh --from <template-number> --to <new-number>"
      echo ""
      echo "Options:"
      echo "  --from  Template project number (e.g., 3 for COD project)"
      echo "  --to    New project number to configure"
      echo "  --org   GitHub user/org (default: IggyIkenna)"
      echo ""
      echo "Example:"
      echo "  bash copy-project-workflows.sh --from 3 --to 5"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate
if [ -z "$FROM_PROJECT" ] || [ -z "$TO_PROJECT" ]; then
  echo "Error: --from and --to are required"
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

# Step 1: Fetch workflows from template project
echo "Step 1: Fetching workflows from template project #$FROM_PROJECT..."
echo ""

WORKFLOWS=$(gh api graphql -f query='
query {
  user(login: "'"$ORG"'") {
    projectV2(number: '"$FROM_PROJECT"') {
      id
      title
      workflows(first: 20) {
        nodes {
          id
          name
          enabled
          number
        }
      }
    }
  }
}')

# Extract workflow details
PROJECT_TITLE=$(echo "$WORKFLOWS" | jq -r '.data.user.projectV2.title')
WORKFLOW_COUNT=$(echo "$WORKFLOWS" | jq '.data.user.projectV2.workflows.nodes | length')

echo "Template: $PROJECT_TITLE (#$FROM_PROJECT)"
echo "Workflows found: $WORKFLOW_COUNT"
echo ""

if [ "$WORKFLOW_COUNT" -eq 0 ]; then
  echo "⚠️  No workflows found on template project"
  echo "   Either project #$FROM_PROJECT doesn't exist or has no workflows"
  exit 1
fi

# Display workflows
echo "Workflows to replicate:"
echo ""
echo "$WORKFLOWS" | jq -r '.data.user.projectV2.workflows.nodes[] | "  [\(.number)] \(.name) (enabled: \(.enabled))"'
echo ""

# Step 2: Get target project info
echo "Step 2: Checking target project #$TO_PROJECT..."
echo ""

TARGET_INFO=$(gh api graphql -f query='
query {
  user(login: "'"$ORG"'") {
    projectV2(number: '"$TO_PROJECT"') {
      id
      title
      workflows(first: 20) {
        nodes {
          name
        }
      }
    }
  }
}')

TARGET_TITLE=$(echo "$TARGET_INFO" | jq -r '.data.user.projectV2.title')
TARGET_WORKFLOW_COUNT=$(echo "$TARGET_INFO" | jq '.data.user.projectV2.workflows.nodes | length')

echo "Target: $TARGET_TITLE (#$TO_PROJECT)"
echo "Existing workflows: $TARGET_WORKFLOW_COUNT"
echo ""

# Step 3: Generate configuration instructions
echo "========================================="
echo "Step 3: Workflow Configuration Instructions"
echo "========================================="
echo ""
echo "⚠️  GitHub GraphQL API doesn't support creating workflows programmatically"
echo "    You MUST configure these manually via the web UI"
echo ""
echo "URL: https://github.com/users/$ORG/projects/$TO_PROJECT/settings/workflows"
echo ""
echo "Press Enter to see detailed instructions for each workflow..."
read -r

# Parse and display each workflow with instructions
echo ""
echo "========================================="
echo "Workflows to Configure"
echo "========================================="
echo ""

# Map workflow names to configuration instructions
echo "$WORKFLOWS" | jq -r '.data.user.projectV2.workflows.nodes[] | .name' | while read -r workflow_name; do
  echo "────────────────────────────────────────"
  echo "Workflow: $workflow_name"
  echo "────────────────────────────────────────"
  echo ""

  case "$workflow_name" in
    "Auto-add to project")
      echo "Type: Built-in workflow"
      echo ""
      echo "Configuration:"
      echo "  1. Click: 'Create workflow' → 'Auto-add to project'"
      echo "  2. Set filter:"
      echo "     - Label: 'cleanup' (or 'cod' for COD project)"
      echo "  3. Action: Add to this project"
      echo "  4. Click: 'Save workflow'"
      echo ""
      echo "Result: Issues with 'cleanup' label auto-add to project"
      ;;
    "Auto-add sub-issues to project")
      echo "Type: Built-in workflow"
      echo ""
      echo "Configuration:"
      echo "  1. Click: 'Create workflow' → 'Auto-add to project'"
      echo "  2. Set filter:"
      echo "     - Issue type: Sub-issue"
      echo "  3. Action: Add to this project"
      echo "  4. Click: 'Save workflow'"
      echo ""
      echo "Result: Sub-issues auto-add to project"
      ;;
    "Item closed")
      echo "Type: Built-in workflow"
      echo ""
      echo "Configuration:"
      echo "  1. Click: 'Create workflow' → 'Auto-archive items'"
      echo "  2. Set trigger:"
      echo "     - When: Item closed"
      echo "  3. Action: Set status to 'Done'"
      echo "  4. Click: 'Save workflow'"
      echo ""
      echo "Result: Closed issues move to 'Done' status"
      ;;
    "Pull request merged")
      echo "Type: Built-in workflow"
      echo ""
      echo "Configuration:"
      echo "  1. Click: 'Create workflow' → 'Auto-close items'"
      echo "  2. Set trigger:"
      echo "     - When: Pull request merged"
      echo "     - Filter: Pull request closes issue"
      echo "  3. Action: Close linked issues"
      echo "  4. Click: 'Save workflow'"
      echo ""
      echo "Result: Issues auto-close when PRs merge"
      echo ""
      echo "⭐ CRITICAL: This workflow enables auto-close on PR merge!"
      ;;
    "Auto-close issue")
      echo "Type: Built-in workflow"
      echo ""
      echo "Configuration:"
      echo "  1. Click: 'Create workflow' → 'Auto-close items'"
      echo "  2. Set trigger:"
      echo "     - When: Pull request merged"
      echo "     - Filter: Pull request closes linked item"
      echo "  3. Action: Close item"
      echo "  4. Click: 'Save workflow'"
      echo ""
      echo "Result: Project items close when PRs merge"
      ;;
    "Auto-archive items")
      echo "Type: Built-in workflow"
      echo ""
      echo "Configuration:"
      echo "  1. Click: 'Create workflow' → 'Auto-archive items'"
      echo "  2. Set trigger:"
      echo "     - When: Item status = 'Done'"
      echo "     - Wait: 30 days"
      echo "  3. Action: Archive item"
      echo "  4. Click: 'Save workflow'"
      echo ""
      echo "Result: Completed items archive after 30 days"
      ;;
    "Item added to project")
      echo "Type: Built-in workflow"
      echo ""
      echo "Configuration:"
      echo "  1. Click: 'Create workflow' → 'Set status'"
      echo "  2. Set trigger:"
      echo "     - When: Item added to project"
      echo "  3. Action: Set status to 'Todo'"
      echo "  4. Click: 'Save workflow'"
      echo ""
      echo "Result: New items default to 'Todo' status"
      ;;
    "Pull request linked to issue")
      echo "Type: Built-in workflow"
      echo ""
      echo "Configuration:"
      echo "  1. Click: 'Create workflow' → 'Set status'"
      echo "  2. Set trigger:"
      echo "     - When: Pull request linked to issue"
      echo "  3. Action: Set status to 'In Progress'"
      echo "  4. Click: 'Save workflow'"
      echo ""
      echo "Result: Issues move to 'In Progress' when PR linked"
      ;;
    *)
      echo "Type: Custom workflow"
      echo ""
      echo "⚠️  Unknown workflow: $workflow_name"
      echo "    Check template project #$FROM_PROJECT for configuration"
      ;;
  esac

  echo ""
  echo "Press Enter for next workflow..."
  read -r
done

# Summary
echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo ""
echo "Template Project: #$FROM_PROJECT ($PROJECT_TITLE)"
echo "  Workflows: $WORKFLOW_COUNT configured"
echo ""
echo "Target Project: #$TO_PROJECT ($TARGET_TITLE)"
echo "  Current workflows: $TARGET_WORKFLOW_COUNT"
echo "  To configure: $WORKFLOW_COUNT workflows"
echo ""
echo "Critical Workflows:"
echo "  ⭐ Pull request merged → Close linked issues"
echo "  ⭐ Auto-add to project (label: cleanup)"
echo ""
echo "Configuration URL:"
echo "  https://github.com/users/$ORG/projects/$TO_PROJECT/settings/workflows"
echo ""
echo "========================================="
echo ""
echo "✅ Instructions complete!"
echo ""
echo "After configuring workflows, run:"
echo "  bash scripts/automation/batch-fix-v2.sh \\"
echo "    --model gemini-3-flash \\"
echo "    --issues \"...\" \\"
echo "    --max-parallel 7"
echo ""
echo "========================================="
