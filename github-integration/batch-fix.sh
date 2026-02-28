#!/bin/bash
#
# Batch Fix Multiple GitHub Issues using Cursor Agent CLI
#
# Usage:
#   bash batch-fix.sh --model <model> --issues "<issue1> <issue2> <issue3>"
#   bash batch-fix.sh --model <model> --issues "[issue1,issue2,issue3]"
#
# Options:
#   --model <model>        Model to use for all issues (required)
#   --issues "<list>"      Space-separated or comma-separated list of issue numbers
#   --sequential           Run fixes sequentially instead of parallel (default: parallel)
#   --dry-run             Preview all prompts without executing
#   --max-parallel <n>    Maximum parallel fixes (default: 5)
#
# Examples:
#   bash batch-fix.sh --model sonnet-4 --issues "1234 1235 1236"
#   bash batch-fix.sh --model sonnet-4-thinking --issues "[1234,1235,1236]"
#   bash batch-fix.sh --model gpt-5 --issues "1234 1235" --sequential
#   bash batch-fix.sh --model sonnet-4 --issues "1234 1235 1236" --dry-run
#

set -euo pipefail

MODEL=""
ISSUES=""
SEQUENTIAL=false
DRY_RUN=false
MAX_PARALLEL=5
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --issues)
            ISSUES="$2"
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
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: bash batch-fix.sh --model <model> --issues \"<list>\" [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --model <model>        Model to use (gpt-5, sonnet-4, sonnet-4-thinking)"
            echo "  --issues \"<list>\"      Issue numbers (space or comma separated)"
            echo "  --sequential           Run fixes sequentially (default: parallel)"
            echo "  --dry-run             Preview prompts without executing"
            echo "  --max-parallel <n>    Max parallel fixes (default: 5)"
            echo ""
            echo "Examples:"
            echo "  bash batch-fix.sh --model sonnet-4 --issues \"1234 1235 1236\""
            echo "  bash batch-fix.sh --model sonnet-4-thinking --issues \"[1234,1235,1236]\""
            echo "  bash batch-fix.sh --model gpt-5 --issues \"1234 1235\" --dry-run"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$MODEL" ]; then
    echo "❌ Error: --model is required"
    echo ""
    echo "Available models:"
    echo "  - gpt-4o-mini           (FREE: 500/day, good for simple fixes)"
    echo "  - gpt-5                 (fast, general-purpose)"
    echo "  - sonnet-4              (high quality, coding-focused)"
    echo "  - sonnet-4-thinking     (best for complex logic)"
    echo ""
    echo "💡 Recommended for code standards violations: gpt-4o-mini (free)"
    echo ""
    echo "Usage: bash batch-fix.sh --model <model> --issues \"<list>\""
    exit 1
fi

if [ -z "$ISSUES" ]; then
    echo "❌ Error: --issues is required"
    echo ""
    echo "Usage: bash batch-fix.sh --model <model> --issues \"<list>\""
    echo ""
    echo "Examples:"
    echo "  --issues \"1234 1235 1236\""
    echo "  --issues \"[1234,1235,1236]\""
    exit 1
fi

# Clean up issues list (remove brackets, commas, convert to space-separated)
# Deduplicate so the same issue is never processed twice (e.g. from list-codex-issues-by-category all)
ISSUES=$(echo "$ISSUES" | tr -d '[],' | tr ',' ' ' | tr ' ' '\n' | grep -v '^$' | sort -n -u | tr '\n' ' ')

# Convert to array
read -ra ISSUE_ARRAY <<< "$ISSUES"

ISSUE_COUNT=${#ISSUE_ARRAY[@]}

echo "🤖 Batch Fix GitHub Issues"
echo "========================================================================"
echo "Model: $MODEL"
echo "Issues: ${ISSUE_ARRAY[*]}"
echo "Count:  $ISSUE_COUNT (deduplicated)"
echo "Mode: $([ "$SEQUENTIAL" = true ] && echo "Sequential" || echo "Parallel (max $MAX_PARALLEL)")"
echo "Dry Run: $([ "$DRY_RUN" = true ] && echo "Yes" || echo "No")"
echo "========================================================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Dry run - show all prompts
if [ "$DRY_RUN" = true ]; then
    echo "📄 Dry Run Mode - Previewing all prompts"
    echo ""

    for ISSUE in "${ISSUE_ARRAY[@]}"; do
        echo "────────────────────────────────────────────────────────────────────────"
        echo "Issue #$ISSUE"
        echo "────────────────────────────────────────────────────────────────────────"
        if [ "$VERBOSE" = true ]; then
            bash "$SCRIPT_DIR/auto-fix-issue.sh" "$ISSUE" --model "$MODEL" --verbose --dry-run
        else
            bash "$SCRIPT_DIR/auto-fix-issue.sh" "$ISSUE" --model "$MODEL" --dry-run
        fi
        echo ""
    done

    echo "✅ Dry run complete for $ISSUE_COUNT issues"
    echo ""
    echo "To execute, remove --dry-run flag:"
    echo "  bash batch-fix.sh --model $MODEL --issues \"${ISSUE_ARRAY[*]}\""
    exit 0
fi

# Execute fixes
echo "🚀 Starting batch fix..."
echo ""

# Track results
SUCCESS_COUNT=0
FAILED_ISSUES=()

if [ "$SEQUENTIAL" = true ]; then
    # Sequential execution
    echo "Running fixes sequentially..."
    echo ""

    for ISSUE in "${ISSUE_ARRAY[@]}"; do
        echo "────────────────────────────────────────────────────────────────────────"
        echo "▶️  Fixing issue #$ISSUE ($(($SUCCESS_COUNT + ${#FAILED_ISSUES[@]} + 1))/$ISSUE_COUNT)"
        echo "────────────────────────────────────────────────────────────────────────"

        if [ "$VERBOSE" = true ]; then
            VERBOSE_FLAG="--verbose"
        else
            VERBOSE_FLAG=""
        fi

        if bash "$SCRIPT_DIR/auto-fix-issue.sh" "$ISSUE" --model "$MODEL" $VERBOSE_FLAG; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            echo "✅ Issue #$ISSUE fixed successfully"
        else
            FAILED_ISSUES+=("$ISSUE")
            echo "❌ Issue #$ISSUE failed"
        fi
        echo ""
    done
else
    # Parallel execution with limit
    echo "Running fixes in parallel (max $MAX_PARALLEL concurrent)..."
    echo ""

    # Function to run fix and track result
    run_fix() {
        local ISSUE=$1
        local RESULT_FILE=$2

        if [ "$VERBOSE" = true ]; then
            VERBOSE_FLAG="--verbose"
        else
            VERBOSE_FLAG=""
        fi

        if bash "$SCRIPT_DIR/auto-fix-issue.sh" "$ISSUE" --model "$MODEL" $VERBOSE_FLAG; then
            echo "SUCCESS:$ISSUE" >> "$RESULT_FILE"
        else
            echo "FAILED:$ISSUE" >> "$RESULT_FILE"
        fi
    }

    # Create temp file for results
    RESULT_FILE=$(mktemp)

    # Run fixes with parallelism limit (bash 3.2 compatible)
    RUNNING=0
    PIDS=()

    for ISSUE in "${ISSUE_ARRAY[@]}"; do
        echo "▶️  Starting fix for issue #$ISSUE..."

        # Run in background
        run_fix "$ISSUE" "$RESULT_FILE" &
        PIDS+=($!)

        RUNNING=$((RUNNING + 1))

        # Wait if we hit max parallel (bash 3.2 compatible)
        if [ $RUNNING -ge $MAX_PARALLEL ]; then
            # Wait for any job to finish
            wait "${PIDS[0]}"
            # Remove first PID from array
            PIDS=("${PIDS[@]:1}")
            RUNNING=$((RUNNING - 1))
        fi
    done

    # Wait for all remaining jobs
    echo ""
    echo "⏳ Waiting for all fixes to complete..."
    for pid in "${PIDS[@]}"; do
        wait "$pid" 2>/dev/null || true
    done

    # Parse results (safely handle empty or missing file)
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
fi

# Summary
echo ""
echo "========================================================================"
echo "📊 Batch Fix Summary"
echo "========================================================================"
echo "Total Issues:     $ISSUE_COUNT"
echo "✅ Successful:    $SUCCESS_COUNT"
echo "❌ Failed:        ${#FAILED_ISSUES[@]}"
echo ""

if [ ${#FAILED_ISSUES[@]} -gt 0 ]; then
    echo "Failed Issues:"
    for ISSUE in "${FAILED_ISSUES[@]}"; do
        echo "  - #$ISSUE"
    done
    echo ""
    echo "To retry failed issues:"
    echo "  bash batch-fix.sh --model $MODEL --issues \"${FAILED_ISSUES[*]}\""
    echo ""
fi

echo "Next Steps:"
echo "1. Verify PRs created: gh pr list --repo IggyIkenna/<service-repo>"
echo "2. Monitor CI/CD: Check GitHub Actions for quality gates"
echo "3. Check issue status: gh issue list --repo IggyIkenna/unified-trading-codex"
echo "========================================================================"

# Exit with error if any failed
if [ ${#FAILED_ISSUES[@]} -gt 0 ]; then
    exit 1
fi

exit 0
