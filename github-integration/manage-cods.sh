#!/bin/bash
# Quick helper script for COD management operations

set -e

ORG="IggyIkenna"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) is not installed"
    echo "Install with: brew install gh"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    print_error "Not authenticated with GitHub"
    echo "Run: gh auth login"
    exit 1
fi

case "${1:-help}" in
    setup)
        print_header "Setting up COD project"
        echo ""
        echo "This will:"
        echo "  1. Create 'cod' label in all repos"
        echo "  2. Find and label existing COD issues"
        echo "  3. Create COD project"
        echo "  4. Add all CODs to project"
        echo ""
        read -p "Continue? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 "$SCRIPT_DIR/setup-cod-project.py" --org "$ORG" --apply
        else
            echo "Cancelled"
        fi
        ;;

    dry-run)
        print_header "COD project setup (dry run)"
        python3 "$SCRIPT_DIR/setup-cod-project.py" --org "$ORG" --dry-run
        ;;

    workflows)
        print_header "Setup project workflows & views"
        echo ""
        if [ -z "$2" ]; then
            print_error "Missing COD project number"
            echo "Usage: $0 workflows <project-number>"
            echo "Example: $0 workflows 3"
            exit 1
        fi
        echo "This will setup workflows and views for COD project #$2"
        echo ""
        echo "Note: Due to GitHub API limitations, this will show you"
        echo "      what manual steps are still required."
        echo ""
        read -p "Continue? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 "$SCRIPT_DIR/setup-cod-project-workflows.py" --org "$ORG" --cod-project-number "$2" --apply
        else
            echo "Cancelled"
        fi
        ;;

    create-all-projects)
        print_header "Create All Missing GitHub Projects"
        echo ""
        echo "This will create 15 missing projects:"
        echo "  - Bugs & Issues"
        echo "  - Execution Services"
        echo "  - Strategy Services"
        echo "  - Position Monitoring & Risk"
        echo "  - Market Data Pipeline"
        echo "  - Features Engineering"
        echo "  - ML Training Services"
        echo "  - ML Inference Services"
        echo "  - ML Deployment Analytics"
        echo "  - Settlement & Reconciliation"
        echo "  - Client Reporting"
        echo "  - Infrastructure & Tooling"
        echo "  - Execution Backtest & UI"
        echo "  - Strategy Backtest & UI"
        echo ""
        echo "Each project will be created with:"
        echo "  - Appropriate labels"
        echo "  - Manual setup guide for workflows & views"
        echo ""
        if [ "$2" = "--dry-run" ]; then
            python3 "$SCRIPT_DIR/create-all-projects.py" --org "$ORG" --dry-run
        else
            read -p "Continue? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                python3 "$SCRIPT_DIR/create-all-projects.py" --org "$ORG" --apply
            else
                echo "Cancelled"
            fi
        fi
        ;;

    list)
        print_header "Listing COD issues"
        echo ""
        gh issue list --search "label:cod" --limit 100 --json number,title,repository,state | \
            jq -r '.[] | "\(.repository.name)#\(.number): \(.title) [\(.state)]"'
        ;;

    count)
        print_header "COD issue counts by repository"
        echo ""

        # Get all repos
        repos=$(gh repo list "$ORG" --json name --limit 1000 | jq -r '.[].name')

        total=0
        for repo in $repos; do
            count=$(gh issue list --repo "$ORG/$repo" --label "cod" --limit 1000 --json number | jq 'length')
            if [ "$count" -gt 0 ]; then
                printf "%-40s %5d CODs\n" "$repo" "$count"
                total=$((total + count))
            fi
        done

        echo ""
        print_success "Total CODs across all repos: $total"
        ;;

    label)
        if [ -z "$2" ]; then
            print_error "Usage: $0 label <repo> <issue-number>"
            exit 1
        fi

        repo="$2"
        issue="$3"

        print_header "Adding 'cod' label to issue"
        gh issue edit "$issue" --repo "$ORG/$repo" --add-label "cod"
        print_success "Added 'cod' label to $repo#$issue"
        ;;

    unlabel)
        if [ -z "$2" ]; then
            print_error "Usage: $0 unlabel <repo> <issue-number>"
            exit 1
        fi

        repo="$2"
        issue="$3"

        print_header "Removing 'cod' label from issue"
        gh issue edit "$issue" --repo "$ORG/$repo" --remove-label "cod"
        print_success "Removed 'cod' label from $repo#$issue"
        ;;

    search)
        if [ -z "$2" ]; then
            print_error "Usage: $0 search <query>"
            exit 1
        fi

        query="$2"
        print_header "Searching COD issues: $query"
        echo ""
        gh issue list --search "label:cod $query" --limit 50 --json number,title,repository,url | \
            jq -r '.[] | "\(.repository.name)#\(.number): \(.title)\n  \(.url)\n"'
        ;;

    open)
        print_header "Opening COD project in browser"
        # This will need the project number - update after setup
        echo "COD project URL: https://github.com/orgs/$ORG/projects"
        echo ""
        print_warning "Update this script with the actual project number after setup"
        ;;

    stats)
        print_header "COD Statistics"
        echo ""

        total=$(gh issue list --search "label:cod" --limit 1000 --json number | jq 'length')
        open=$(gh issue list --search "label:cod state:open" --limit 1000 --json number | jq 'length')
        closed=$(gh issue list --search "label:cod state:closed" --limit 1000 --json number | jq 'length')

        echo "Total CODs:   $total"
        echo "Open CODs:    $open"
        echo "Closed CODs:  $closed"

        if [ "$total" -gt 0 ]; then
            closed_pct=$((closed * 100 / total))
            echo "Closed rate:  ${closed_pct}%"
        fi
        ;;

    bulk-close)
        print_warning "This will close COD issues matching a search query"
        echo ""

        if [ -z "$2" ]; then
            print_error "Usage: $0 bulk-close <search-query>"
            echo "Example: $0 bulk-close 'created:<2023-01-01'"
            exit 1
        fi

        query="$2"
        echo "Search query: label:cod $query"
        echo ""

        # Show matching issues
        gh issue list --search "label:cod $query" --limit 50 --json number,title,repository | \
            jq -r '.[] | "\(.repository.name)#\(.number): \(.title)"'

        echo ""
        read -p "Close these issues? (y/N) " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            gh issue list --search "label:cod $query" --limit 50 --json number,repository | \
                jq -r '.[] | "\(.repository.name) \(.number)"' | \
                while read repo issue; do
                    echo "Closing $repo#$issue..."
                    gh issue close "$issue" --repo "$ORG/$repo" --reason "not planned"
                done
            print_success "Closed matching CODs"
        else
            echo "Cancelled"
        fi
        ;;

    help|*)
        echo "COD Management Script"
        echo ""
        echo "Usage: $0 <command> [arguments]"
        echo ""
        echo "Commands:"
        echo "  setup                     - Run full COD project setup (interactive)"
        echo "  dry-run                   - Preview what setup would do (no changes)"
        echo "  workflows <number>        - Setup project workflows & views (after initial setup)"
        echo "  create-all-projects       - Create all 15 missing GitHub projects"
        echo "  list                      - List all COD issues (up to 100)"
        echo "  count                     - Count CODs by repository"
        echo "  stats                     - Show COD statistics (total, open, closed)"
        echo "  search <query>            - Search COD issues"
        echo "  label <repo> <issue>      - Add 'cod' label to an issue"
        echo "  unlabel <repo> <issue>    - Remove 'cod' label from an issue"
        echo "  bulk-close <query>        - Close multiple CODs matching query"
        echo "  open                      - Open COD project in browser"
        echo "  help                      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 setup                                 # Initial setup (creates project, labels issues)"
        echo "  $0 workflows 3                           # Setup workflows for project #3"
        echo "  $0 create-all-projects                   # Create all 15 projects (interactive)"
        echo "  $0 create-all-projects --dry-run         # Preview project creation"
        echo "  $0 count                                 # Count CODs per repo"
        echo "  $0 search 'authentication'               # Find auth-related CODs"
        echo "  $0 label execution-services 1234         # Label issue as COD"
        echo "  $0 bulk-close 'created:<2023-01-01'      # Close old CODs"
        echo ""
        ;;
esac
