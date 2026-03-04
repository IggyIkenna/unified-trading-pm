#!/bin/bash
# ==============================================================================
# Delete and Recreate GitHub Project - Fresh Start
# ==============================================================================
#
# This script:
#   1. Deletes the existing GitHub Project
#   2. Recreates it with proper structure
#   3. Syncs with local codebase as source of truth
#
# Usage:
#   bash delete-and-recreate-project.sh
#
# ==============================================================================

set -euo pipefail

# Config
ORG="IggyIkenna"
PROJECT_NAME="Unified Trading System"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
  echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[⚠]${NC} $1"
}

# ==============================================================================
# Step 1: Check Prerequisites
# ==============================================================================

check_prerequisites() {
  log_info "Step 1: Checking prerequisites"

  # Check gh CLI
  if ! command -v gh &>/dev/null; then
    log_error "gh CLI not found. Install: brew install gh"
    exit 1
  fi
  log_success "gh CLI installed"

  # Check auth
  if ! gh auth status &>/dev/null; then
    log_error "gh CLI not authenticated. Run: gh auth login"
    exit 1
  fi
  log_success "gh CLI authenticated"

  # Check if project exists
  local project_list=$(gh project list --owner "$ORG" --format json 2>/dev/null || echo "[]")
  local project_count=$(echo "$project_list" | jq -r '. | length')

  if [[ "$project_count" -gt 0 ]]; then
    log_warning "Found $project_count existing project(s)"
    echo "$project_list" | jq -r '.[] | "  - \(.title) (ID: \(.number))"'
  else
    log_info "No existing projects found"
  fi

  echo ""
}

# ==============================================================================
# Step 2: Delete Existing Project
# ==============================================================================

delete_existing_project() {
  log_info "Step 2: Finding and deleting existing project"

  # List all projects
  local projects=$(gh project list --owner "$ORG" --format json 2>/dev/null || echo "[]")

  # Find project by name (case-insensitive partial match)
  local project_id=$(echo "$projects" | jq -r '.[] | select(.title | test("unified.*trading"; "i")) | .number' | head -1)

  if [[ -z "$project_id" ]]; then
    log_info "No matching project found to delete"
    return 0
  fi

  log_warning "Found project to delete: ID $project_id"
  echo -e "${YELLOW}Are you sure you want to DELETE this project? (yes/no)${NC}"
  read -r confirm

  if [[ "$confirm" != "yes" ]]; then
    log_info "Skipping deletion"
    return 0
  fi

  # Delete project
  if gh project delete "$project_id" --owner "$ORG" --yes &>/dev/null; then
    log_success "Deleted project #$project_id"
  else
    log_error "Failed to delete project. You may need to do this manually in GitHub UI."
    log_info "Go to: https://github.com/orgs/$ORG/projects"
    exit 1
  fi

  echo ""
}

# ==============================================================================
# Step 3: Create New Project
# ==============================================================================

create_new_project() {
  log_info "Step 3: Creating new project"

  # Create project
  local project_url=$(gh project create --owner "$ORG" --title "$PROJECT_NAME" --format json 2>/dev/null | jq -r '.url')

  if [[ -z "$project_url" ]]; then
    log_error "Failed to create project"
    exit 1
  fi

  log_success "Created project: $project_url"

  # Extract project number from URL
  local project_number=$(echo "$project_url" | grep -oE '[0-9]+$')
  echo "$project_number" >/tmp/uts_project_number.txt

  echo ""
}

# ==============================================================================
# Step 4: Configure Project Fields
# ==============================================================================

configure_project_fields() {
  log_info "Step 4: Configuring project fields"

  local project_number=$(cat /tmp/uts_project_number.txt)

  log_warning "NOTE: Custom fields must be added manually in GitHub UI"
  log_info "Go to: https://github.com/orgs/$ORG/projects/$project_number/settings/fields"
  log_info ""
  log_info "Add these fields:"
  echo "  1. Status (Single select): Open, Planned, Implementing, Testing, Review, Completed"
  echo "  2. Priority (Single select): P0-critical, P1-high, P2-medium, P3-low"
  echo "  3. Service (Single select): instruments-service, market-data-processing-service, etc."
  echo "  4. Milestone (Single select): TechReadiness, Batch85, Live90, Commercialization"
  echo "  5. Estimated Hours (Number)"
  echo "  6. Regeneration Count (Number)"
  echo ""

  echo -e "${YELLOW}Press Enter when you've added the custom fields...${NC}"
  read -r

  log_success "Project fields configured"
  echo ""
}

# ==============================================================================
# Step 5: Create Project Views
# ==============================================================================

create_project_views() {
  log_info "Step 5: Creating project views"

  local project_number=$(cat /tmp/uts_project_number.txt)

  log_info "Default views to create:"
  echo "  1. By Status (kanban)"
  echo "  2. By Service (table)"
  echo "  3. By Priority (table)"
  echo "  4. By Milestone (roadmap)"
  echo ""

  log_warning "NOTE: Views must be created manually in GitHub UI"
  log_info "Go to: https://github.com/orgs/$ORG/projects/$project_number"
  log_info "Click 'New view' to create each view"
  echo ""

  echo -e "${YELLOW}Press Enter when you've created the views...${NC}"
  read -r

  log_success "Project views created"
  echo ""
}

# ==============================================================================
# Main
# ==============================================================================

main() {
  echo "===================================================================="
  echo "Delete and Recreate GitHub Project"
  echo "===================================================================="
  echo ""
  echo "Organization: $ORG"
  echo "Project Name: $PROJECT_NAME"
  echo ""

  check_prerequisites
  delete_existing_project
  create_new_project
  configure_project_fields
  create_project_views

  log_success "Project setup complete!"
  echo ""
  echo "===================================================================="
  echo "Next Steps"
  echo "===================================================================="
  echo "1. Sync issues from codebase:"
  echo "   bash sync-from-codebase.sh --repo IggyIkenna/instruments-service"
  echo ""
  echo "2. Mark completed work:"
  echo "   bash mark-completed.sh --repo IggyIkenna/instruments-service --status batch-working"
  echo ""
  echo "3. View project:"
  local project_number=$(cat /tmp/uts_project_number.txt)
  echo "   https://github.com/orgs/$ORG/projects/$project_number"
  echo ""
}

main
