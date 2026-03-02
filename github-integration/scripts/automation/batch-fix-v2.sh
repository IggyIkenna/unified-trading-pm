#!/usr/bin/env bash
#
# Batch Fix with Smart Workspace Pooling
#
# Resource-Aware Strategy:
#   - Pre-calculates optimal clones per service based on:
#     * Number of workers (MAX_PARALLEL)
#     * Number of services with issues
#     * Distribution of issues per service
#   - Pre-provisions workspace pool (clones repos upfront)
#   - Assigns issues to isolated workspaces
#   - Processes in parallel with no conflicts
#
# Usage:
#   bash batch-fix-v2.sh --model <model> --issues "<issue1> <issue2> <issue3>"
#
# Options:
#   --model <model>        Model to use for all issues (required)
#   --issues "<list>"      Space-separated or comma-separated list of issue numbers
#   --sequential           Disable pooling, run all sequentially
#   --dry-run             Preview workspace allocation
#   --max-parallel <n>    Maximum parallel workers (default: 5)
#   --keep-workspaces     Don't cleanup workspace pool after completion
#
# Examples:
#   # 23 issues across 14 services, 5 workers
#   bash batch-fix-v2.sh --model gpt-4o-mini --issues "589 588 587..." --max-parallel 5
#
#   # Preview workspace allocation
#   bash batch-fix-v2.sh --model sonnet-4 --issues "..." --dry-run
#

set -euo pipefail

# Check bash version (need 4+ for associative arrays)
if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    echo "❌ Error: This script requires Bash 4.0 or higher"
    echo "   Current version: $BASH_VERSION"
    echo ""
    echo "macOS ships with Bash 3.2. Please install a newer version:"
    echo ""
    echo "  brew install bash"
    echo ""
    echo "Then run this script with the new bash:"
    echo ""
    echo "  /opt/homebrew/bin/bash $0 $@"
    echo ""
    echo "Or add to your PATH: export PATH=\"/opt/homebrew/bin:\$PATH\""
    exit 1
fi

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
MODEL=""
ISSUE_LIST=""
SEQUENTIAL=false
DRY_RUN=false
MAX_PARALLEL=5
KEEP_WORKSPACES=false
VERBOSE=false
ORG="IggyIkenna"
CODEX_ISSUE_REPO="IggyIkenna/unified-trading-codex"

# Auto-detect workspace root (parent of unified-trading-codex)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${WORKSPACE_ROOT:-}" ]; then
    # We're in unified-trading-codex/11-project-management/.../automation
    # Go up 5 levels to get workspace root
    WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
    echo "📂 Auto-detected workspace: $WORKSPACE_ROOT"
fi

# Save original workspace for fallback merges (in case quickmerge fails to create PR)
ORIGINAL_WORKSPACE_ROOT="$WORKSPACE_ROOT"

# Validate workspace has required repos
if [ ! -d "$WORKSPACE_ROOT/unified-trading-codex" ]; then
    echo "❌ Error: unified-trading-codex not found in $WORKSPACE_ROOT"
    echo "   Clone it with: gh repo clone IggyIkenna/unified-trading-codex"
    exit 1
fi

if [ ! -d "$WORKSPACE_ROOT/unified-trading-services" ]; then
    echo "⚠️  Warning: unified-trading-services not found in $WORKSPACE_ROOT"
    echo "   Tests may fail. Clone it with: gh repo clone IggyIkenna/unified-trading-services"
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --issues)
            ISSUE_LIST="$2"
            shift 2
            ;;
        --sequential)
            SEQUENTIAL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --max-parallel)
            MAX_PARALLEL="$2"
            shift 2
            ;;
        --keep-workspaces)
            KEEP_WORKSPACES=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: bash batch-fix-v2.sh --model <model> --issues \"<list>\" [OPTIONS]"
            echo ""
            echo "Smart Workspace Pooling:"
            echo "  - Pre-calculates optimal clones per service"
            echo "  - Based on workers, services, and issue distribution"
            echo "  - Pre-provisions workspace pool (isolated clones)"
            echo "  - Parallel processing with zero git conflicts"
            echo ""
            echo "Options:"
            echo "  --model <model>        Model to use (gpt-5, sonnet-4, sonnet-4-thinking)"
            echo "  --issues \"<list>\"      Issue numbers (space or comma separated)"
            echo "  --sequential           Disable pooling, run all sequentially"
            echo "  --dry-run             Preview workspace allocation"
            echo "  --max-parallel <n>    Max parallel workers (default: 5)"
            echo "  --keep-workspaces     Don't cleanup workspace pool"
            echo ""
            echo "Examples:"
            echo "  # Smart pooling with 5 workers"
            echo "  bash batch-fix-v2.sh --model gpt-4o-mini --issues \"589 588 587\" --max-parallel 5"
            echo ""
            echo "  # Preview allocation"
            echo "  bash batch-fix-v2.sh --model sonnet-4 --issues \"589 588\" --dry-run"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$MODEL" ] || [ -z "$ISSUE_LIST" ]; then
    echo "Error: --model and --issues are required"
    echo ""
    echo "Usage: bash batch-fix-v2.sh --model <model> --issues \"<list>\""
    echo "Run with -h or --help for more information"
    exit 1
fi

# Parse issue list (handle both space and comma separated)
ISSUE_LIST=$(echo "$ISSUE_LIST" | tr ',' ' ' | tr -s ' ')
read -r -a ISSUE_ARRAY <<< "$ISSUE_LIST"

# Remove duplicates and sort
ISSUE_ARRAY=($(printf '%s\n' "${ISSUE_ARRAY[@]}" | sort -u))
ISSUE_COUNT=${#ISSUE_ARRAY[@]}

# ============================================================================
# PRE-FLIGHT CHECK: Fetch GitHub token from Secret Manager and configure git
# ============================================================================
echo "🔐 Pre-flight: Setting up GitHub authentication from Secret Manager..."

# Configuration
SECRET_NAME="${GITHUB_TOKEN_SECRET:-github-automation-token}"
GCP_PROJECT="${GCP_PROJECT:?GCP_PROJECT required}"
GITHUB_TOKEN=""

# Try to fetch GitHub PAT from Secret Manager
if command -v gcloud &>/dev/null; then
    echo "   📥 Fetching GitHub PAT from Secret Manager..."

    if GITHUB_TOKEN=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$GCP_PROJECT" 2>/dev/null); then
        echo "   ✅ GitHub PAT fetched successfully"

        # Configure git globally to use this token for GitHub HTTPS operations
        echo "   🔧 Configuring git credential helper..."
        git config --global credential.helper ""  # Clear existing helpers
        git config --global credential.helper "store"

        # Store the credential (this creates ~/.git-credentials)
        mkdir -p "$HOME"
        echo "https://oauth2:${GITHUB_TOKEN}@github.com" > "$HOME/.git-credentials"
        chmod 600 "$HOME/.git-credentials"

        # Also authenticate gh CLI with the token (for gh commands)
        if command -v gh &>/dev/null; then
            if echo "$GITHUB_TOKEN" | gh auth login --with-token 2>/dev/null; then
                echo "   ✅ gh CLI authenticated with Secret Manager token"
            else
                echo "   ⚠️  gh CLI auth failed (non-critical, git will still work)"
            fi
        fi

        echo "   ✅ Git configured to use Secret Manager token"
        echo "   ℹ️  All git operations will use this token automatically"
    else
        echo "   ⚠️  Could not fetch GitHub PAT from Secret Manager"
        echo "   📌 Secret: $SECRET_NAME (project: $GCP_PROJECT)"
        echo "   💡 Falling back to local authentication..."

        # Fallback: Check local gh CLI auth
        if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
            echo "   ✅ Using local gh CLI authentication"
            gh auth setup-git  # Configure git to use gh for auth
        else
            echo "   ❌ ERROR: No GitHub authentication available!"
            echo ""
            echo "   To fix, either:"
            echo "   1. Set up GCP: gcloud auth login"
            echo "   2. Set up gh CLI: gh auth login"
            echo ""
            exit 1
        fi
    fi
else
    echo "   ⚠️  gcloud not installed, checking local authentication..."

    # Fallback: Check local gh CLI auth
    if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
        echo "   ✅ Using local gh CLI authentication"
        gh auth setup-git  # Configure git to use gh for auth
    else
        echo "   ❌ ERROR: No GitHub authentication available!"
        echo ""
        echo "   To fix, either:"
        echo "   1. Install & authenticate gcloud: https://cloud.google.com/sdk/docs/install"
        echo "   2. Authenticate gh CLI: gh auth login"
        echo ""
        exit 1
    fi
fi
echo ""

# Display header
echo "🤖 Batch Fix with Smart Workspace Pooling"
echo "========================================================================"
echo "Model: $MODEL"
echo "Issues: ${ISSUE_ARRAY[*]}"
echo "Count:  $ISSUE_COUNT (deduplicated)"
echo "Workers: $MAX_PARALLEL"
echo "Mode: $([ "$SEQUENTIAL" = true ] && echo "Sequential" || echo "Smart Pooling")"
echo "Dry Run: $([ "$DRY_RUN" = true ] && echo "Yes" || echo "No")"
echo "========================================================================"
echo ""

# Step 1: Group issues by service
echo "📋 Step 1: Grouping issues by service..."
declare -A SERVICE_ISSUES
declare -A SERVICE_ISSUE_COUNTS

for ISSUE in "${ISSUE_ARRAY[@]}"; do
    # Check if issue is in format "repo:number" (for cleanup issues in service repos)
    if [[ "$ISSUE" == *":"* ]]; then
        # Split repo:number format
        ISSUE_REPO="${ISSUE%%:*}"
        ISSUE_NUMBER="${ISSUE##*:}"
        ISSUE_TITLE=$(gh issue view "$ISSUE_NUMBER" --repo "$ORG/$ISSUE_REPO" --json title --jq '.title' 2>/dev/null || echo "")
        SERVICE_NAME="$ISSUE_REPO"
    else
        # Standard format - fetch from codex repo
        ISSUE_NUMBER="$ISSUE"
        ISSUE_TITLE=$(gh issue view "$ISSUE" --repo "$CODEX_ISSUE_REPO" --json title --jq '.title' 2>/dev/null || echo "")
        SERVICE_NAME=$(echo "$ISSUE_TITLE" | grep -o '\[.*\]' | tr -d '[]' | head -1)
    fi

    if [ -z "$ISSUE_TITLE" ]; then
        echo "⚠️  Could not fetch issue #$ISSUE"
        continue
    fi

    if [ -z "$SERVICE_NAME" ]; then
        echo "⚠️  Could not extract service from issue $ISSUE: $ISSUE_TITLE"
        continue
    fi

    # Store the full issue identifier (repo:number or just number)
    if [ -z "${SERVICE_ISSUES[$SERVICE_NAME]:-}" ]; then
        SERVICE_ISSUES[$SERVICE_NAME]="$ISSUE"
        SERVICE_ISSUE_COUNTS[$SERVICE_NAME]=1
    else
        SERVICE_ISSUES[$SERVICE_NAME]="${SERVICE_ISSUES[$SERVICE_NAME]} $ISSUE"
        SERVICE_ISSUE_COUNTS[$SERVICE_NAME]=$((SERVICE_ISSUE_COUNTS[$SERVICE_NAME] + 1))
    fi
done

NUM_SERVICES=${#SERVICE_ISSUES[@]}

echo ""
echo "Service Grouping:"
for service in "${!SERVICE_ISSUES[@]}"; do
    count=${SERVICE_ISSUE_COUNTS[$service]}
    echo "  [$service] → $count issues: ${SERVICE_ISSUES[$service]}"
done
echo ""
echo "Summary: $ISSUE_COUNT issues across $NUM_SERVICES services"
echo ""

# Step 2: Calculate optimal clones per service
echo "📊 Step 2: Calculating optimal workspace allocation..."
echo ""

declare -A SERVICE_CLONE_COUNTS

if [ "$NUM_SERVICES" -eq 0 ]; then
    echo "Error: No valid service issues found"
    exit 1
fi

if [ "$MAX_PARALLEL" -le "$NUM_SERVICES" ]; then
    # Case 1: More services than workers → 1 clone per service (reuse workers)
    echo "Strategy: workers ($MAX_PARALLEL) <= services ($NUM_SERVICES)"
    echo "  → 1 clone per service (workers will be reused)"
    echo ""

    for service in "${!SERVICE_ISSUES[@]}"; do
        SERVICE_CLONE_COUNTS[$service]=1
    done
else
    # Case 2: More workers than services → provision multiple clones for busy services
    echo "Strategy: workers ($MAX_PARALLEL) > services ($NUM_SERVICES)"
    echo "  → Multiple clones for services with many issues"
    echo ""

    # Calculate clones per service based on issue distribution
    for service in "${!SERVICE_ISSUES[@]}"; do
        issue_count=${SERVICE_ISSUE_COUNTS[$service]}

        # Optimal clones = min(issue_count, ceil(workers / services))
        workers_per_service=$(( (MAX_PARALLEL + NUM_SERVICES - 1) / NUM_SERVICES ))
        optimal_clones=$((issue_count < workers_per_service ? issue_count : workers_per_service))

        SERVICE_CLONE_COUNTS[$service]=$optimal_clones
    done
fi

# Display allocation
echo "Workspace Allocation:"
TOTAL_CLONES=0
for service in "${!SERVICE_CLONE_COUNTS[@]}"; do
    clone_count=${SERVICE_CLONE_COUNTS[$service]}
    issue_count=${SERVICE_ISSUE_COUNTS[$service]}
    TOTAL_CLONES=$((TOTAL_CLONES + clone_count))
    echo "  [$service] → $clone_count clones for $issue_count issues"
done
echo ""
echo "Total workspace clones: $TOTAL_CLONES"
echo ""

# Dry-run mode - show allocation and exit
if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY-RUN MODE: Workspace allocation preview complete"
    echo ""
    echo "Next steps (when executed):"
    echo "  1. Provision $TOTAL_CLONES workspace clones"
    echo "  2. Assign issues to clones round-robin"
    echo "  3. Process $MAX_PARALLEL workers in parallel"
    echo "  4. Cleanup workspace pool (unless --keep-workspaces)"
    echo ""
    echo "✅ Dry-run complete. Remove --dry-run to execute."
    exit 0
fi

# Step 3: Provision workspace pool
echo "🏗️  Step 3: Provisioning workspace pool ($TOTAL_CLONES clones)..."
echo ""

# Clean up old workspace pools from interrupted previous runs
# (older than 1 hour, to avoid deleting actively running processes)
# Use TMPDIR which resolves to the correct temp dir on macOS (/var/folders) and Linux (/tmp)
TEMP_DIR="${TMPDIR:-/tmp}"
TEMP_DIR="${TEMP_DIR%/}"  # Remove trailing slash if present

# Find old pools (only in the parent directory, not recursively)
OLD_POOLS=$(find "$(dirname "$TEMP_DIR")/$(basename "$TEMP_DIR")" -maxdepth 1 -name "batch-fix-pool-*" -type d -mmin +60 2>/dev/null || true)

if [ -n "$OLD_POOLS" ]; then
    echo "🧹 Cleaning up old workspace pools from interrupted runs (>60 min old)..."
    echo "$OLD_POOLS" | while read -r old_pool; do
        if [ -n "$old_pool" ] && [ -d "$old_pool" ]; then
            echo "  Removing: $old_pool"
            rm -rf "$old_pool" 2>/dev/null || true
        fi
    done
    echo ""
fi

WORKSPACE_POOL_DIR=$(mktemp -d -t batch-fix-pool-XXXXXX)
echo "Workspace pool: $WORKSPACE_POOL_DIR"
echo ""

declare -A CLONE_PATHS

for service in "${!SERVICE_CLONE_COUNTS[@]}"; do
    clone_count=${SERVICE_CLONE_COUNTS[$service]}

    echo "Cloning $service ($clone_count copies)..."

    for ((i=1; i<=clone_count; i++)); do
        clone_id="${service}_clone_${i}"
        clone_workspace="${WORKSPACE_POOL_DIR}/${clone_id}"

        # Create workspace directory structure
        mkdir -p "$clone_workspace"

        # Clone service repo
        source_service_repo="${WORKSPACE_ROOT}/${service}"
        if [ ! -d "$source_service_repo" ]; then
            echo "  ⚠️  Source repo not found: $source_service_repo"
            continue
        fi

        git clone --quiet "$source_service_repo" "$clone_workspace/$service" 2>&1 | grep -v "^Cloning" || true

        # Fix git remote to point to GitHub instead of local filesystem
        if [ -d "$clone_workspace/$service" ]; then
            cd "$clone_workspace/$service"

            # Use SSH if available, otherwise HTTPS (auth is handled globally)
            if [ -f ~/.ssh/id_rsa ] || [ -f ~/.ssh/id_ed25519 ]; then
                # SSH keys available - use SSH
                git remote set-url origin "git@github.com:$ORG/${service}.git"
                echo "  🔑 Using SSH authentication"
            else
                # Use HTTPS (auth configured globally in pre-flight check)
                git remote set-url origin "https://github.com/$ORG/${service}.git"
                echo "  🔑 Using HTTPS authentication (Secret Manager token)"
            fi

            cd - > /dev/null
        fi

        # Clone unified-trading-codex (needed for @ references in agent prompts)
        source_codex_repo="${WORKSPACE_ROOT}/unified-trading-codex"
        if [ -d "$source_codex_repo" ]; then
            # Remove existing directory if present (from interrupted previous run)
            rm -rf "$clone_workspace/unified-trading-codex" 2>/dev/null || true
            git clone --quiet "$source_codex_repo" "$clone_workspace/unified-trading-codex" 2>&1 | grep -v "^Cloning" || true
        fi

        # Clone unified-trading-services (needed for tests and dependencies)
        source_ucs_repo="${WORKSPACE_ROOT}/unified-trading-services"
        if [ -d "$source_ucs_repo" ]; then
            # Remove existing directory if present (from interrupted previous run)
            rm -rf "$clone_workspace/unified-trading-services" 2>/dev/null || true
            git clone --quiet "$source_ucs_repo" "$clone_workspace/unified-trading-services" 2>&1 | grep -v "^Cloning" || true
        fi

        if [ -d "$clone_workspace/$service" ]; then
            CLONE_PATHS[$clone_id]="$clone_workspace"
            echo "  ✓ $clone_id → $clone_workspace"
        else
            echo "  ✗ Failed to clone $clone_id"
        fi
    done
done

echo ""
echo "✅ Workspace pool ready: ${#CLONE_PATHS[@]} clones provisioned"
echo ""

# Step 4: Assign issues to clones (round-robin per service)
echo "🎯 Step 4: Assigning issues to workspace clones..."
echo ""

declare -A CLONE_ISSUES

for service in "${!SERVICE_ISSUES[@]}"; do
    issues=(${SERVICE_ISSUES[$service]})
    clone_count=${SERVICE_CLONE_COUNTS[$service]}

    for ((i=0; i<${#issues[@]}; i++)); do
        issue=${issues[$i]}
        clone_index=$(( (i % clone_count) + 1 ))
        clone_id="${service}_clone_${clone_index}"

        if [ -z "${CLONE_ISSUES[$clone_id]:-}" ]; then
            CLONE_ISSUES[$clone_id]="$issue"
        else
            CLONE_ISSUES[$clone_id]="${CLONE_ISSUES[$clone_id]} $issue"
        fi
    done
done

echo "Issue Assignment:"
for clone_id in "${!CLONE_ISSUES[@]}"; do
    issues="${CLONE_ISSUES[$clone_id]}"
    issue_array=($issues)
    echo "  $clone_id → ${#issue_array[@]} issues: $issues"
done
echo ""

# Step 5: Process issues in parallel using workspace pool
echo "🚀 Step 5: Processing issues in parallel (max $MAX_PARALLEL workers)..."
echo ""

# Function to process issues in a workspace clone
process_clone() {
    local clone_id=$1
    local issues=$2
    local clone_path=$3
    local result_file=$4

    echo "[$clone_id] Starting ($clone_path)"

    cd "$clone_path" || return 1

    for issue in $issues; do
        echo "[$clone_id] 🔧 Fixing issue #$issue..."

        # Parse repo name from issue (format: "repo:number")
        local repo_name="${issue%%:*}"
        local issue_num="${issue##*:}"

        # Call auto-fix-issue.sh with workspace override
        local agent_exit_code=0
        if WORKSPACE_ROOT="$clone_path" bash "$SCRIPT_DIR/auto-fix-issue.sh" "$issue" --model "$MODEL"; then
            agent_exit_code=0
            echo "SUCCESS:$issue" >> "$result_file"
            echo "[$clone_id] ✅ Issue #$issue fixed"
        else
            agent_exit_code=$?
            echo "FAILED:$issue" >> "$result_file"
            echo "[$clone_id] ❌ Issue #$issue failed"
        fi

        # SAFETY: Copy changes back to original workspace (fallback if quickmerge failed)
        # This prevents losing work if PR creation fails
        local service_dir="$clone_path/$repo_name"
        if [ -d "$service_dir/.git" ]; then
            cd "$service_dir" || continue

            # Check if agent made any changes
            if ! git diff --quiet HEAD || [ -n "$(git ls-files --others --exclude-standard)" ]; then
                echo "[$clone_id] 💾 Fallback: Copying changes to original workspace..."

                # Get original workspace path (parent of unified-trading-codex)
                local original_service="$ORIGINAL_WORKSPACE_ROOT/$repo_name"

                if [ -d "$original_service/.git" ]; then
                    # Create a fallback branch in original workspace
                    local fallback_branch="fallback/agent-fix-${issue_num}-$(date +%Y%m%d-%H%M%S)"

                    cd "$original_service" || continue

                    # Stash any uncommitted work in original
                    local had_changes=false
                    if ! git diff --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
                        git stash push -m "Pre-agent-fallback-merge" &>/dev/null
                        had_changes=true
                    fi

                    # Create fallback branch from main
                    git checkout main &>/dev/null 2>&1 || true
                    git checkout -b "$fallback_branch" &>/dev/null 2>&1

                    # Cherry-pick or copy changes from clone
                    cd "$service_dir" || continue
                    local clone_commit=$(git rev-parse HEAD 2>/dev/null)

                    cd "$original_service" || continue

                    # Try to fetch and cherry-pick from remote (if PR was created)
                    local pr_merged=false
                    if git fetch origin &>/dev/null 2>&1; then
                        # Check if there's a recent commit with this issue number
                        if git log origin/main --oneline -20 | grep -q "#${issue_num}"; then
                            echo "[$clone_id]    ✅ PR already merged to main, skipping fallback"
                            git checkout main &>/dev/null 2>&1
                            git pull origin main &>/dev/null 2>&1
                            pr_merged=true
                        fi
                    fi

                    if [ "$pr_merged" = false ]; then
                        # PR not merged, copy files manually
                        echo "[$clone_id]    📋 Copying changed files..."

                        # Get list of changed files from clone
                        cd "$service_dir" || continue
                        local changed_files=$(git diff --name-only HEAD~ HEAD 2>/dev/null || git ls-files --others --exclude-standard)

                        if [ -n "$changed_files" ]; then
                            # Copy each changed file
                            while IFS= read -r file; do
                                if [ -f "$file" ]; then
                                    local dest_file="$original_service/$file"
                                    mkdir -p "$(dirname "$dest_file")"
                                    cp "$file" "$dest_file"
                                fi
                            done <<< "$changed_files"

                            cd "$original_service" || continue
                            git add -A
                            git commit -m "Fallback: Agent fixes for #${issue_num} (PR creation failed)

Changes copied from temp workspace after successful agent run.
Original quickmerge failed to create PR, preserving work locally.

Re-push these changes when quickmerge is fixed." &>/dev/null 2>&1

                            echo "[$clone_id]    ✅ Changes saved to branch: $fallback_branch"
                            echo "[$clone_id]    📂 Location: $original_service"
                        fi
                    fi

                    # Restore original state
                    git checkout main &>/dev/null 2>&1 || true
                    if [ "$had_changes" = true ]; then
                        git stash pop &>/dev/null 2>&1 || true
                    fi
                else
                    echo "[$clone_id]    ⚠️  Original service directory not a git repo: $original_service"
                fi
            else
                echo "[$clone_id] ℹ️  No changes to copy (agent made no modifications)"
            fi

            cd "$clone_path" || return 1
        fi
    done

    echo "[$clone_id] ✅ Complete"
}

export -f process_clone
export SCRIPT_DIR MODEL ORIGINAL_WORKSPACE_ROOT

RESULT_FILE=$(mktemp)
PIDS=()
RUNNING=0

for clone_id in "${!CLONE_ISSUES[@]}"; do
    issues="${CLONE_ISSUES[$clone_id]}"
    clone_path="${CLONE_PATHS[$clone_id]}"

    if [ -z "$clone_path" ]; then
        echo "⚠️  No clone path for $clone_id, skipping"
        continue
    fi

    echo "▶️  Starting: $clone_id"

    # Run in background
    process_clone "$clone_id" "$issues" "$clone_path" "$RESULT_FILE" &
    PIDS+=($!)

    RUNNING=$((RUNNING + 1))

    # Wait if we hit max parallel
    if [ $RUNNING -ge $MAX_PARALLEL ]; then
        wait "${PIDS[0]}"
        PIDS=("${PIDS[@]:1}")
        RUNNING=$((RUNNING - 1))
    fi
done

# Wait for all remaining
echo ""
echo "⏳ Waiting for all workers to complete..."
for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
done

# Parse results
SUCCESS_COUNT=0
FAILED_ISSUES=()

if [ -f "$RESULT_FILE" ] && [ -s "$RESULT_FILE" ]; then
    while IFS=: read -r STATUS ISSUE; do
        [ -z "${STATUS:-}" ] && continue
        if [ "$STATUS" = "SUCCESS" ]; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            FAILED_ISSUES+=("$ISSUE")
        fi
    done < "$RESULT_FILE"
fi
rm -f "$RESULT_FILE"

# Cleanup workspace pool
if [ "$KEEP_WORKSPACES" = true ]; then
    echo ""
    echo "⚠️  Workspace pool preserved: $WORKSPACE_POOL_DIR"
else
    echo ""
    echo "🧹 Cleaning up workspace pool..."
    rm -rf "$WORKSPACE_POOL_DIR"
fi

# Final summary
echo ""
echo "========================================================================"
echo "Batch Fix Summary"
echo "========================================================================"
echo "Total Issues: $ISSUE_COUNT"
echo "Successful:   $SUCCESS_COUNT"
echo "Failed:       ${#FAILED_ISSUES[@]}"

if [ ${#FAILED_ISSUES[@]} -gt 0 ]; then
    echo ""
    echo "Failed Issues: ${FAILED_ISSUES[*]}"
fi

echo "========================================================================"
echo ""

if [ ${#FAILED_ISSUES[@]} -eq 0 ]; then
    echo "✅ All issues fixed successfully!"
    exit 0
else
    echo "⚠️  Some issues failed. See output above for details."
    exit 1
fi
