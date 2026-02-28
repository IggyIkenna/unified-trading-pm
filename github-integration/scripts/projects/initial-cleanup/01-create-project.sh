#!/bin/bash
# Create "Initial Cleanup" GitHub Project (Project #5)
#
# Creates a GitHub Project to track initial cleanup issues across all service repos.
# Project tracks fixing of all codex violations (print, os.getenv, datetime, bare except, imports, etc.)
#
# Usage:
#   bash 01-create-project.sh

set -euo pipefail

ORG="IggyIkenna"
PROJECT_NAME="Initial Cleanup"

echo "========================================="
echo "Creating Project: $PROJECT_NAME"
echo "========================================="
echo ""

# Check if project exists
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
    PROJECT_NUMBER=$EXISTING_PROJECT
else
    # Create project
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
          }
        }
      }' --jq '.data.createProjectV2.projectV2')

    PROJECT_NUMBER=$(echo "$PROJECT_DATA" | jq -r '.number')
    echo "✅ Project created: #$PROJECT_NUMBER"
fi

echo ""
echo "========================================="
echo "Project Setup Complete"
echo "========================================="
echo ""
echo "Project Number: $PROJECT_NUMBER"
echo "Project URL: https://github.com/users/$ORG/projects/$PROJECT_NUMBER"
echo ""
echo "Next Steps:"
echo "  1. Run: bash 02-create-issues.sh"
echo "  2. Run: bash 03-link-issues-to-project.sh"
echo "  3. Configure workflows: https://github.com/users/$ORG/projects/$PROJECT_NUMBER/settings/workflows"
echo "  4. Run batch fix: bash 04-run-batch-fix.sh --model auto --require-labels cleanup --state open"
echo ""
