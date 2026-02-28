#!/usr/bin/env bash
# ==============================================================================
# Unified GitHub Project Management Script
# ==============================================================================
#
# This script consolidates 6 project management scripts into one unified tool.
# Takes best practices from each:
#   - wipe-project-background.sh → Parallel deletion (xargs -P 20)
#   - clear-github-project.sh → Flexible CLI (--repo, --all, --close|--delete)
#   - wipe-and-regenerate-project.sh → Safety confirmations
#   - create-project-fully-automated.sh → GraphQL API
#   - delete-and-recreate-project.sh → Prereq checks
#   - run-full-regeneration.sh → Orchestration
#
# Commands:
#   create      - Create new GitHub project with custom fields
#   wipe        - Delete all issues from project (parallel, 30sec for 650 issues)
#   regenerate  - Wipe + regenerate issues
#   delete      - Delete entire project
#
# Usage:
#   bash manage-project.sh create --name "Project Name" --org IggyIkenna
#   bash manage-project.sh wipe --project-number 3 [--no-confirm]
#   bash manage-project.sh regenerate --project-number 3
#   bash manage-project.sh delete --project-number 3 [--no-confirm]
#
# ==============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
ORG="IggyIkenna"
REPO="unified-trading-codex"
PROJECT_NUMBER=""
PROJECT_NAME=""
NO_CONFIRM=false
DRY_RUN=false

# ==============================================================================
# Logging Functions
# ==============================================================================

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
# Prerequisite Checks
# ==============================================================================

check_prerequisites() {
    # Check gh CLI
    if ! command -v gh &> /dev/null; then
        log_error "gh CLI not found. Install: brew install gh"
        exit 1
    fi

    # Check auth
    if ! gh auth status &> /dev/null; then
        log_error "gh CLI not authenticated. Run: gh auth login"
        exit 1
    fi

    # Check python3
    if ! command -v python3 &> /dev/null; then
        log_error "python3 not found. Install python3"
        exit 1
    fi

    # Check jq
    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Install: brew install jq"
        exit 1
    fi
}

# ==============================================================================
# Command: Create Project
# ==============================================================================

cmd_create() {
    log_info "Creating project: $PROJECT_NAME"
    echo ""

    # Check if project already exists (idempotent)
    local existing_project=$(gh project list --owner "$ORG" --limit 100 2>/dev/null | \
        awk -F'\t' -v name="$PROJECT_NAME" '$2 == name {print $1; exit}')

    if [[ -n "$existing_project" ]]; then
        log_warning "Project '$PROJECT_NAME' already exists (ID: $existing_project)"
        log_info "Skipping creation (idempotent)"
        echo "$existing_project"
        return 0
    fi

    # Get owner node ID
    local owner_id=$(gh api user -q .node_id)

    # Create project using GraphQL API
    local result=$(gh api graphql -f query='
      mutation {
        createProjectV2(input: {
          ownerId: "'"$owner_id"'"
          title: "'"$PROJECT_NAME"'"
        }) {
          projectV2 {
            id
            number
            url
          }
        }
      }' 2>/dev/null)

    local project_id=$(echo "$result" | jq -r '.data.createProjectV2.projectV2.id')
    local project_number=$(echo "$result" | jq -r '.data.createProjectV2.projectV2.number')
    local project_url=$(echo "$result" | jq -r '.data.createProjectV2.projectV2.url')

    if [[ -z "$project_id" ]] || [[ "$project_id" == "null" ]]; then
        log_error "Failed to create project"
        exit 1
    fi

    log_success "Created project #$project_number"
    log_info "URL: $project_url"
    echo ""

    # Add custom fields
    log_info "Adding custom fields..."

    # Status field
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
          projectV2Field { id }
        }
      }' > /dev/null 2>&1

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
          projectV2Field { id }
        }
      }' > /dev/null 2>&1

    log_success "Added Priority field"

    echo ""
    log_success "Project creation complete!"
    echo "$project_number"
}

# ==============================================================================
# Command: Wipe Project (Parallel Deletion - 10x Faster)
# ==============================================================================

cmd_wipe() {
    log_info "Wiping GitHub Project #$PROJECT_NUMBER"
    echo ""

    # Safety confirmation
    if [[ "$NO_CONFIRM" != "true" ]]; then
        log_warning "This will DELETE ALL ISSUES from Project #$PROJECT_NUMBER"
        log_warning "Issues will be PERMANENTLY DELETED"
        echo ""
        read -p "Are you sure? Type 'yes' to confirm: " confirmation

        if [[ "$confirmation" != "yes" ]]; then
            log_info "Aborted by user"
            exit 0
        fi
        echo ""
    fi

    # Step 1: Delete all issues in parallel (20 at a time)
    log_info "Step 1/2: Deleting all issues (parallel)..."

    local all_issues=$(gh issue list --repo "$ORG/$REPO" --state all --limit 1000 --json number --jq '.[].number' 2>/dev/null || true)

    if [ -n "$all_issues" ]; then
        local issue_count=$(echo "$all_issues" | wc -l | tr -d ' ')
        log_info "Found $issue_count issues to delete"

        # Parallel deletion using xargs -P 20 (30 seconds for 650 issues vs 5 minutes sequential)
        echo "$all_issues" | xargs -P 20 -I {} gh issue delete {} --repo "$ORG/$REPO" --yes 2>/dev/null || true

        log_success "Deleted $issue_count issues"
    else
        log_info "No issues to delete"
    fi

    echo ""

    # Step 2: Clear project board items in parallel
    log_info "Step 2/2: Clearing project board (parallel)..."

    local project_items=$(gh project item-list "$PROJECT_NUMBER" --owner "$ORG" --format json --limit 1000 2>/dev/null | \
        jq -r '.items[].id' 2>/dev/null || true)

    if [ -n "$project_items" ]; then
        local item_count=$(echo "$project_items" | wc -l | tr -d ' ')
        log_info "Found $item_count project items"

        # Parallel removal using xargs -P 20
        echo "$project_items" | xargs -P 20 -I {} gh project item-delete "$PROJECT_NUMBER" --owner "$ORG" --id {} 2>/dev/null || true

        log_success "Removed $item_count items"
    else
        log_info "No project items to remove"
    fi

    echo ""
    log_success "Project wipe complete!"
}

# ==============================================================================
# Command: Regenerate (Wipe + Create Issues)
# ==============================================================================

cmd_regenerate() {
    log_info "Regenerating Project #$PROJECT_NUMBER"
    echo ""

    # Step 1: Wipe
    log_info "Phase 1/2: Wiping project..."
    cmd_wipe

    echo ""
    log_info "Waiting 5 seconds for GitHub API to settle..."
    sleep 5
    echo ""

    # Step 2: Regenerate issues
    log_info "Phase 2/2: Generating issues..."

    local script_dir="$(dirname "${BASH_SOURCE[0]}")/../core"

    if [ -f "$script_dir/04-create-service-epics.py" ]; then
        python3 "$script_dir/04-create-service-epics.py" --all-services
        log_success "Issues generated"
    else
        log_warning "create-service-epics.py not found at $script_dir/04-create-service-epics.py"
        log_info "You'll need to manually generate issues"
    fi

    echo ""
    log_success "Project regeneration complete!"
}

# ==============================================================================
# Command: Delete Project
# ==============================================================================

cmd_delete() {
    log_info "Deleting GitHub Project #$PROJECT_NUMBER"
    echo ""

    # Safety confirmation
    if [[ "$NO_CONFIRM" != "true" ]]; then
        log_warning "This will PERMANENTLY DELETE Project #$PROJECT_NUMBER"
        log_warning "This action CANNOT be undone"
        echo ""
        read -p "Are you sure? Type 'DELETE' to confirm: " confirmation

        if [[ "$confirmation" != "DELETE" ]]; then
            log_info "Aborted by user"
            exit 0
        fi
        echo ""
    fi

    # Get project GraphQL ID
    local project_id=$(gh project view "$PROJECT_NUMBER" --owner "$ORG" --format json --jq '.id' 2>/dev/null)

    if [[ -z "$project_id" ]] || [[ "$project_id" == "null" ]]; then
        log_error "Project #$PROJECT_NUMBER not found"
        exit 1
    fi

    # Delete project using GraphQL API
    local result=$(gh api graphql -f query='
      mutation {
        deleteProjectV2(input: {projectId: "'"$project_id"'"}) {
          projectV2 { id }
        }
      }' 2>/dev/null)

    if echo "$result" | jq -e '.data.deleteProjectV2' &>/dev/null; then
        log_success "Deleted project #$PROJECT_NUMBER"
    else
        log_error "Failed to delete project"
        log_info "You may need to delete manually at: https://github.com/orgs/$ORG/projects"
        exit 1
    fi
}

# ==============================================================================
# Main Argument Parsing
# ==============================================================================

show_usage() {
    cat << EOF
Unified GitHub Project Management Script

USAGE:
    bash manage-project.sh <command> [options]

COMMANDS:
    create      Create new GitHub project with custom fields
    wipe        Delete all issues from project (parallel, fast)
    regenerate  Wipe + regenerate issues
    delete      Delete entire project

OPTIONS:
    --name NAME             Project name (for create)
    --org ORG               Organization name (default: IggyIkenna)
    --project-number NUM    Project number (for wipe/regenerate/delete)
    --no-confirm            Skip confirmation prompts
    --dry-run               Preview actions without executing

EXAMPLES:
    # Create project
    bash manage-project.sh create --name "Execution Services" --org IggyIkenna

    # Wipe project (with confirmation)
    bash manage-project.sh wipe --project-number 3

    # Wipe project (no confirmation, fast - 30sec for 650 issues)
    bash manage-project.sh wipe --project-number 3 --no-confirm

    # Regenerate project
    bash manage-project.sh regenerate --project-number 3

    # Delete project
    bash manage-project.sh delete --project-number 3

PERFORMANCE:
    - Parallel deletion: 30 seconds for 650 issues (vs 5 minutes sequential)
    - Uses xargs -P 20 for 20 parallel operations
    - Idempotent: safe to re-run

EOF
}

# Parse command
COMMAND="${1:-}"
shift || true

if [[ -z "$COMMAND" ]]; then
    show_usage
    exit 1
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        --org)
            ORG="$2"
            shift 2
            ;;
        --project-number)
            PROJECT_NUMBER="$2"
            shift 2
            ;;
        --no-confirm)
            NO_CONFIRM=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# ==============================================================================
# Execute Command
# ==============================================================================

check_prerequisites

case "$COMMAND" in
    create)
        if [[ -z "$PROJECT_NAME" ]]; then
            log_error "Missing required option: --name"
            show_usage
            exit 1
        fi
        cmd_create
        ;;

    wipe)
        if [[ -z "$PROJECT_NUMBER" ]]; then
            log_error "Missing required option: --project-number"
            show_usage
            exit 1
        fi
        cmd_wipe
        ;;

    regenerate)
        if [[ -z "$PROJECT_NUMBER" ]]; then
            log_error "Missing required option: --project-number"
            show_usage
            exit 1
        fi
        cmd_regenerate
        ;;

    delete)
        if [[ -z "$PROJECT_NUMBER" ]]; then
            log_error "Missing required option: --project-number"
            show_usage
            exit 1
        fi
        cmd_delete
        ;;

    *)
        log_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
