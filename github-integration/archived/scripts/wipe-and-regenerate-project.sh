#!/bin/bash
# ==============================================================================
# Wipe and Regenerate GitHub Project
# ==============================================================================
#
# This script:
# 1. Deletes all issues from existing project (with confirmation)
# 2. Regenerates everything with new service-level Epic structure
#
# Usage:
#   bash wipe-and-regenerate-project.sh
#
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORG="IggyIkenna"
REPO="unified-trading-codex"
PROJECT_NUMBER=1  # "Codex Delta Wave 1 - Unified Board"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
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
# Step 1: Confirm Wipe
# ==============================================================================

log_warning "This will DELETE ALL ISSUES from Project #${PROJECT_NUMBER} in ${ORG}/${REPO}"
log_warning "Current issues will be PERMANENTLY DELETED"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirmation

if [[ "$confirmation" != "yes" ]]; then
    log_info "Aborted by user"
    exit 0
fi

echo ""
log_info "Proceeding with wipe and regeneration..."
echo ""

# ==============================================================================
# Step 2: Close All Existing Issues (PARALLEL)
# ==============================================================================

log_info "Closing all open issues in ${ORG}/${REPO}..."

# Get all open issue numbers
open_issues=$(gh issue list --repo "${ORG}/${REPO}" --limit 1000 --json number --jq '.[].number')

if [[ -z "$open_issues" ]]; then
    log_info "No open issues found"
else
    issue_count=$(echo "$open_issues" | wc -l | tr -d ' ')
    log_info "Found ${issue_count} open issues"
    log_info "Closing in parallel (20 at a time)..."

    # Parallel close using xargs (20 parallel jobs)
    echo "$open_issues" | xargs -P 20 -I {} sh -c '
        gh issue close {} --repo "'"${ORG}/${REPO}"'" --comment "Closed during project regeneration" 2>/dev/null && echo "✓ Closed #{}" || echo "✗ Failed #{}"
    '

    log_success "Closed ${issue_count} issues"
fi

echo ""

# ==============================================================================
# Step 3: Clear Project Board (PARALLEL)
# ==============================================================================

log_info "Clearing project board #${PROJECT_NUMBER}..."

# Get all project items
project_items=$(gh project item-list ${PROJECT_NUMBER} --owner ${ORG} --limit 1000 --format json 2>/dev/null | \
    python3 -c "import sys, json; items = json.load(sys.stdin)['items']; print(' '.join([item['id'] for item in items]))" || echo "")

if [[ -z "$project_items" ]]; then
    log_info "No project items found"
else
    item_count=$(echo "$project_items" | wc -w | tr -d ' ')
    log_info "Found ${item_count} project items"
    log_info "Removing in parallel (20 at a time)..."

    # Parallel delete using xargs (20 parallel jobs)
    echo "$project_items" | tr ' ' '\n' | xargs -P 20 -I {} sh -c '
        gh project item-delete --owner "'"${ORG}"'" --id "{}" 2>/dev/null && echo "✓ Removed {}" || echo "✗ Failed {}"
    '

    log_success "Removed ${item_count} project items"
fi

echo ""

# ==============================================================================
# Step 4: Regenerate with New Structure
# ==============================================================================

log_info "Regenerating project with service-level Epics..."
echo ""

# Run create-service-epics.py
python3 "${SCRIPT_DIR}/create-service-epics.py" --all-services

echo ""
log_success "Project regeneration complete!"
echo ""

# ==============================================================================
# Step 5: Summary
# ==============================================================================

echo "===================================================================="
echo "Summary"
echo "===================================================================="
log_success "Old issues closed and removed from project"
log_success "New service-level Epics created"
echo ""
log_info "View project: https://github.com/users/${ORG}/projects/${PROJECT_NUMBER}"
log_info "View issues: https://github.com/${ORG}/${REPO}/issues"
echo ""
echo "Structure:"
echo "  - One Epic per Service"
echo "  - Tasks grouped by: Batch Mode, Live Mode, Testing, Observability"
echo "  - Subtasks for atomic work units"
echo "  - Rich labels: mode/batch, mode/live, domain/sports, type/ui, etc."
echo ""
echo "===================================================================="
