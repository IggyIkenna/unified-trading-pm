#!/bin/bash
# ==============================================================================
# Fully Automated GitHub Project Creation
# ==============================================================================
#
# Creates GitHub Project with ALL settings configured via API.
# No manual steps required.
#
# Usage:
#   bash create-project-fully-automated.sh
#
# ==============================================================================

set -euo pipefail

# Load config
source "$(dirname "${BASH_SOURCE[0]}")/.github-config"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }

# ==============================================================================
# Create Project
# ==============================================================================

create_project() {
    log_info "Creating project: $PROJECT_NAME"

    # Create project (returns project ID)
    PROJECT_ID=$(gh api graphql -f query='
      mutation {
        createProjectV2(input: {
          ownerId: "'$(gh api user -q .node_id)'"
          title: "'"$PROJECT_NAME"'"
        }) {
          projectV2 {
            id
            number
            url
          }
        }
      }' --jq '.data.createProjectV2.projectV2.id')

    PROJECT_NUMBER=$(gh api graphql -f query='
      mutation {
        createProjectV2(input: {
          ownerId: "'$(gh api user -q .node_id)'"
          title: "'"$PROJECT_NAME"'"
        }) {
          projectV2 {
            number
          }
        }
      }' --jq '.data.createProjectV2.projectV2.number')

    log_success "Created project #$PROJECT_NUMBER (ID: $PROJECT_ID)"
    echo "$PROJECT_ID" > /tmp/uts_project_id.txt
    echo "$PROJECT_NUMBER" > /tmp/uts_project_number.txt
}

# ==============================================================================
# Add Custom Fields
# ==============================================================================

add_custom_fields() {
    log_info "Adding custom fields"

    local project_id=$(cat /tmp/uts_project_id.txt)

    # Status field (Single Select)
    gh api graphql -f query='
      mutation {
        createProjectV2Field(input: {
          projectId: "'"$project_id"'"
          dataType: SINGLE_SELECT
          name: "Status"
          singleSelectOptions: [
            {name: "Open", color: GRAY}
            {name: "Planned", color: BLUE}
            {name: "Implementing", color: YELLOW}
            {name: "Testing", color: ORANGE}
            {name: "Review", color: PURPLE}
            {name: "Completed", color: GREEN}
          ]
        }) {
          projectV2Field {
            id
          }
        }
      }' > /dev/null

    log_success "Added Status field"

    # Priority field
    gh api graphql -f query='
      mutation {
        createProjectV2Field(input: {
          projectId: "'"$project_id"'"
          dataType: SINGLE_SELECT
          name: "Priority"
          singleSelectOptions: [
            {name: "P0-critical", color: RED}
            {name: "P1-high", color: ORANGE}
            {name: "P2-medium", color: YELLOW}
            {name: "P3-low", color: GREEN}
          ]
        }) {
          projectV2Field {
            id
          }
        }
      }' > /dev/null

    log_success "Added Priority field"

    # Service field
    gh api graphql -f query='
      mutation {
        createProjectV2Field(input: {
          projectId: "'"$project_id"'"
          dataType: SINGLE_SELECT
          name: "Service"
          singleSelectOptions: [
            {name: "instruments-service"}
            {name: "market-data-processing-service"}
            {name: "strategy-service"}
            {name: "execution-services"}
          ]
        }) {
          projectV2Field {
            id
          }
        }
      }' > /dev/null

    log_success "Added Service field"

    # Milestone field
    gh api graphql -f query='
      mutation {
        createProjectV2Field(input: {
          projectId: "'"$project_id"'"
          dataType: SINGLE_SELECT
          name: "Milestone"
          singleSelectOptions: [
            {name: "TechReadiness"}
            {name: "Batch85"}
            {name: "Live90"}
            {name: "Commercialization"}
          ]
        }) {
          projectV2Field {
            id
          }
        }
      }' > /dev/null

    log_success "Added Milestone field"

    # Estimated Hours field (Number)
    gh api graphql -f query='
      mutation {
        createProjectV2Field(input: {
          projectId: "'"$project_id"'"
          dataType: NUMBER
          name: "Estimated Hours"
        }) {
          projectV2Field {
            id
          }
        }
      }' > /dev/null

    log_success "Added Estimated Hours field"
}

# ==============================================================================
# Main
# ==============================================================================

main() {
    echo "===================================================================="
    echo "Fully Automated Project Creation"
    echo "===================================================================="
    echo "Organization: $GITHUB_ORG"
    echo "Project: $PROJECT_NAME"
    echo ""

    create_project
    add_custom_fields

    local project_number=$(cat /tmp/uts_project_number.txt)

    log_success "Project created successfully!"
    echo ""
    echo "Project URL: https://github.com/orgs/$GITHUB_ORG/projects/$project_number"
    echo ""
}

main
