#!/bin/bash
#
# Create GitHub Project for Unified Libraries Refactor
#
# Creates a new GitHub Project with appropriate fields for tracking
# the Unified Libraries Refactor epic (51 subtasks across 5 repos).
#
# Usage:
#   bash 01-create-project.sh --org IggyIkenna
#
# Requires:
#   - gh CLI authenticated with project scope
#
# Python 3.13+ / Bash 5+
#

set -euo pipefail

# Defaults
ORG="${ORG:-IggyIkenna}"
PROJECT_NAME="Unified Libraries Refactor"
PROJECT_DESCRIPTION="Split unified-trading-library into focused libraries (events, config, market, order) with backward compatibility"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --org)
            ORG="$2"
            shift 2
            ;;
        --name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: bash 01-create-project.sh [--org <org>] [--name <project-name>]"
            echo ""
            echo "Options:"
            echo "  --org   GitHub organization/user (default: IggyIkenna)"
            echo "  --name  Project name (default: Unified Libraries Refactor)"
            echo ""
            echo "Example:"
            echo "  bash 01-create-project.sh --org IggyIkenna"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "GitHub Project Creation"
echo "========================================="
echo ""
echo "Project: $PROJECT_NAME"
echo "Owner: $ORG"
echo ""

# Step 1: Check if project already exists
echo "Step 1: Checking if project exists..."

EXISTING_PROJECT=$(gh api graphql -f query='
query {
  user(login: "'"$ORG"'") {
    projectsV2(first: 100) {
      nodes {
        number
        title
      }
    }
  }
}' --jq '.data.user.projectsV2.nodes[] | select(.title == "'"$PROJECT_NAME"'") | .number' 2>/dev/null || echo "")

if [ -n "$EXISTING_PROJECT" ]; then
    echo "✅ Project already exists: #$EXISTING_PROJECT"
    echo "   URL: https://github.com/users/$ORG/projects/$EXISTING_PROJECT"
    echo ""
    echo "Skipping creation. Use this project number for subsequent steps."
    echo ""
    echo "Project Number: $EXISTING_PROJECT"
    exit 0
fi

# Step 2: Create project
echo "Step 2: Creating project..."

OWNER_ID=$(gh api user --jq .node_id)

PROJECT_DATA=$(gh api graphql -f query='
mutation {
  createProjectV2(input: {
    ownerId: "'"$OWNER_ID"'"
    title: "'"$PROJECT_NAME"'"
  }) {
    projectV2 {
      id
      number
      title
      url
    }
  }
}' --jq '.data.createProjectV2.projectV2')

PROJECT_ID=$(echo "$PROJECT_DATA" | jq -r '.id')
PROJECT_NUMBER=$(echo "$PROJECT_DATA" | jq -r '.number')
PROJECT_URL=$(echo "$PROJECT_DATA" | jq -r '.url')

echo "✅ Project created: #$PROJECT_NUMBER"
echo "   URL: $PROJECT_URL"
echo ""

# Step 3: Add custom fields
echo "Step 3: Adding custom fields..."

# Add Priority field (single select)
gh api graphql -f query='
mutation {
  createProjectV2Field(input: {
    projectId: "'"$PROJECT_ID"'"
    dataType: SINGLE_SELECT
    name: "Priority"
    singleSelectOptions: [
      {name: "P0-critical", color: RED, description: "Blocking, must fix immediately"}
      {name: "P1-high", color: YELLOW, description: "Important, fix soon"}
      {name: "P2-medium", color: BLUE, description: "Normal priority"}
      {name: "P3-low", color: GRAY, description: "Low priority, nice to have"}
    ]
  }) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        id
        name
      }
    }
  }
}' > /dev/null 2>&1 || echo "⚠️  Priority field may already exist"

# Add Type field (single select)
gh api graphql -f query='
mutation {
  createProjectV2Field(input: {
    projectId: "'"$PROJECT_ID"'"
    dataType: SINGLE_SELECT
    name: "Type"
    singleSelectOptions: [
      {name: "epic", color: PINK, description: "Large feature or initiative"}
      {name: "task", color: BLUE, description: "Standard work item"}
      {name: "subtask", color: GRAY, description: "Part of a larger task"}
    ]
  }) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        id
        name
      }
    }
  }
}' > /dev/null 2>&1 || echo "⚠️  Type field may already exist"

# Add Estimated Hours field (number)
gh api graphql -f query='
mutation {
  createProjectV2Field(input: {
    projectId: "'"$PROJECT_ID"'"
    dataType: NUMBER
    name: "Estimated Hours"
  }) {
    projectV2Field {
      ... on ProjectV2Field {
        id
        name
      }
    }
  }
}' > /dev/null 2>&1 || echo "⚠️  Estimated Hours field may already exist"

echo "✅ Custom fields added"
echo ""

# Summary
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Project: #$PROJECT_NUMBER - $PROJECT_NAME"
echo "URL: $PROJECT_URL"
echo ""
echo "Custom fields:"
echo "  - Priority: P0-critical, P1-high, P2-medium, P3-low"
echo "  - Type: epic, task, subtask"
echo "  - Estimated Hours: number"
echo ""
echo "Next Steps:"
echo "  1. Create repos (Stage 2):"
echo "     bash 02-create-repos.sh --org $ORG"
echo ""
echo "  2. Create issues (Stage 3):"
echo "     python 02-create-issues.py --org $ORG --project $PROJECT_NUMBER --apply"
echo ""
echo "  3. Configure workflows (Stage 5):"
echo "     bash 04-copy-workflows.sh --from 5 --to $PROJECT_NUMBER"
echo ""
echo "========================================="
echo ""
echo "Project Number: $PROJECT_NUMBER"
