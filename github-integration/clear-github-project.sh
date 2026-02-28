#!/bin/bash
# ==============================================================================
# Clear GitHub Project - Fresh Start Script
# ==============================================================================
#
# This script helps you clear all issues from repos for a fresh start.
# Use with caution - this will close/delete issues!
#
# Usage:
#   bash clear-github-project.sh [--repo REPO] [--all] [--close|--delete]
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
ACTION="close"  # close or delete
DRY_RUN=false

# ==============================================================================
# Helper Functions
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
# Clear Issues from a Repo
# ==============================================================================

clear_repo_issues() {
    local repo=$1
    local action=$2
    local dry_run=$3

    log_info "Processing repo: $repo"

    # Get all open issues
    local issues=$(gh issue list --repo "$repo" --json number --limit 1000 --jq '.[].number')

    if [[ -z "$issues" ]]; then
        log_info "No open issues found in $repo"
        return 0
    fi

    local count=$(echo "$issues" | wc -l | xargs)
    log_warning "Found $count open issues in $repo"

    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY-RUN: Would $action these issues:"
        echo "$issues" | head -10
        if [[ $count -gt 10 ]]; then
            log_info "... and $((count - 10)) more"
        fi
        return 0
    fi

    # Ask for confirmation
    echo -e "${YELLOW}Are you sure you want to $action $count issues in $repo? (yes/no)${NC}"
    read -r confirm

    if [[ "$confirm" != "yes" ]]; then
        log_info "Skipping $repo"
        return 0
    fi

    # Process each issue
    local processed=0
    while IFS= read -r issue_num; do
        if [[ "$action" == "close" ]]; then
            if gh issue close "$issue_num" --repo "$repo" --comment "🧹 Clearing for fresh start" &>/dev/null; then
                ((processed++))
                echo -ne "\r  Closed: $processed/$count"
            fi
        elif [[ "$action" == "delete" ]]; then
            if gh issue delete "$issue_num" --repo "$repo" --yes &>/dev/null; then
                ((processed++))
                echo -ne "\r  Deleted: $processed/$count"
            fi
        fi
    done <<< "$issues"

    echo ""  # New line after progress
    log_success "Processed $processed issues in $repo"
}

# ==============================================================================
# Clear Project Board
# ==============================================================================

clear_project_board() {
    local org=$1
    local project_number=$2

    log_info "Clearing project board: $org project #$project_number"
    log_warning "NOTE: Project board items are auto-synced with issues."
    log_info "Once you clear issues, the project board will be empty."
    log_info "You can keep the project structure (columns, views) intact."
}

# ==============================================================================
# Interactive Mode
# ==============================================================================

interactive_mode() {
    echo "===================================================================="
    echo "GitHub Project Clear - Interactive Mode"
    echo "===================================================================="
    echo ""

    # Step 1: Choose repos
    log_info "Step 1: Which repos do you want to clear?"
    echo ""
    echo "Available options:"
    echo "  1. All pipeline services (17 repos)"
    echo "  2. All platform services (5 repos)"
    echo "  3. All UI services (10 repos)"
    echo "  4. Specific repo(s)"
    echo "  5. All repos (32 total)"
    echo ""
    echo -n "Enter choice (1-5): "
    read -r choice

    local repos=()
    case $choice in
        1)
            repos=(
                "instruments-service"
                "corporate-actions"
                "features-calendar-service"
                "market-tick-data-handler"
                "market-data-processing-service"
                "features-delta-one-service"
                "features-volatility-service"
                "features-onchain-service"
                "features-sports-service"
                "ml-training-service"
                "ml-inference-service"
                "strategy-service"
                "execution-services"
                "reconciliation-service"
                "pnl-attribution-service"
                "position-balance-monitor-service"
                "exposure-monitor-service"
            )
            ;;
        2)
            repos=(
                "unified-trading-services"
                "unified-trading-deployment-v2"
                "unified-trading-codex"
            )
            ;;
        3)
            repos=(
                "live-health-monitor-ui"
                "batch-audit-ui"
                "logs-dashboard-ui"
                "ml-deployment-ui"
                "backtest-ui"
                "trading-analytics-ui"
                "settlement-ui"
                "client-reporting-ui"
                "strategy-onboarding-ui"
            )
            ;;
        4)
            echo -n "Enter repo name(s) (space-separated): "
            read -r repo_input
            IFS=' ' read -ra repos <<< "$repo_input"
            ;;
        5)
            log_warning "This will clear ALL 32 repos!"
            repos=(
                "instruments-service" "corporate-actions" "features-calendar-service"
                "market-tick-data-handler" "market-data-processing-service"
                "features-delta-one-service" "features-volatility-service"
                "features-onchain-service" "features-sports-service"
                "ml-training-service" "ml-inference-service"
                "strategy-service" "execution-services"
                "reconciliation-service" "pnl-attribution-service"
                "position-balance-monitor-service" "exposure-monitor-service"
                "unified-trading-services" "unified-trading-deployment-v2"
                "unified-trading-codex"
                "live-health-monitor-ui" "batch-audit-ui" "logs-dashboard-ui"
                "ml-deployment-ui" "backtest-ui" "trading-analytics-ui"
                "settlement-ui" "client-reporting-ui" "strategy-onboarding-ui"
            )
            ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac

    # Step 2: Choose action
    echo ""
    log_info "Step 2: How do you want to clear issues?"
    echo ""
    echo "Options:"
    echo "  1. Close issues (keeps issue history, can reopen)"
    echo "  2. Delete issues (permanent, cannot undo)"
    echo ""
    echo -n "Enter choice (1-2): "
    read -r action_choice

    case $action_choice in
        1) ACTION="close" ;;
        2) ACTION="delete" ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac

    # Step 3: Get org name
    echo ""
    log_info "Step 3: What is your GitHub organization name?"
    echo -n "Enter org name: "
    read -r org

    # Step 4: Dry-run or real?
    echo ""
    log_info "Step 4: Dry-run first?"
    echo ""
    echo "Options:"
    echo "  1. Dry-run (preview only)"
    echo "  2. Real run (will $ACTION issues)"
    echo ""
    echo -n "Enter choice (1-2): "
    read -r dry_choice

    case $dry_choice in
        1) DRY_RUN=true ;;
        2) DRY_RUN=false ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac

    # Step 5: Execute
    echo ""
    echo "===================================================================="
    echo "Summary"
    echo "===================================================================="
    echo "Repos to clear: ${#repos[@]}"
    echo "Action: $ACTION"
    echo "Dry-run: $DRY_RUN"
    echo ""

    if [[ "$DRY_RUN" == "false" ]]; then
        log_warning "This will $ACTION issues in ${#repos[@]} repos!"
        echo -n "Type 'CONFIRM' to proceed: "
        read -r final_confirm

        if [[ "$final_confirm" != "CONFIRM" ]]; then
            log_info "Cancelled"
            exit 0
        fi
    fi

    # Process repos
    for repo in "${repos[@]}"; do
        clear_repo_issues "$org/$repo" "$ACTION" "$DRY_RUN"
        echo ""
    done

    log_success "Done! Cleared ${#repos[@]} repos."
}

# ==============================================================================
# Main
# ==============================================================================

main() {
    # Check for gh CLI
    if ! command -v gh &> /dev/null; then
        log_error "gh CLI not found. Install: brew install gh"
        exit 1
    fi

    # Check auth
    if ! gh auth status &> /dev/null; then
        log_error "gh CLI not authenticated. Run: gh auth login"
        exit 1
    fi

    # Parse args
    if [[ $# -eq 0 ]]; then
        interactive_mode
    else
        # TODO: Add CLI arg support
        log_error "CLI args not yet implemented. Run without args for interactive mode."
        exit 1
    fi
}

main "$@"
