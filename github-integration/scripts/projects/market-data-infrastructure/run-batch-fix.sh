#!/usr/bin/env bash
#
# Batch execution wrapper for Market Data Infrastructure subtasks
#
# Processes subtasks from the epic in parallel using batch-fix-v2.sh.
# Reads issue numbers from issue-manifest.json (created by 02-create-issues.py).
#
# Usage:
#   bash run-batch-fix.sh --model <model> [OPTIONS]
#
# Options:
#   --model <model>        AI model to use (required)
#   --max-parallel <n>     Max parallel workers (default: 3)
#   --repos <list>         Comma-separated repo names to filter (e.g., "unified-events-interface,unified-config-interface")
#   --phase <0-4>          Filter by phase (0=infra, 1=events, 2=config, 3=market, 4=order)
#   --priority <P0-P3>     Filter by priority (P0-critical, P1-high, P2-medium, P3-low)
#   --issues "<list>"      Custom issues (overrides manifest)
#   --issue-manifest <file> Path to issue manifest (default: issue-manifest.json)
#   --dry-run             Preview what would be done
#
# Examples:
#   # All subtasks from manifest
#   bash run-batch-fix.sh --model auto --max-parallel 3
#
#   # Just Phase 1 (events interface)
#   bash run-batch-fix.sh --model auto --phase 1 --max-parallel 5
#
#   # Just unified-events-interface repo
#   bash run-batch-fix.sh --model auto --repos unified-events-interface
#
#   # P0-critical tasks only
#   bash run-batch-fix.sh --model auto --priority P0-critical --max-parallel 5
#
#   # Custom issues
#   bash run-batch-fix.sh --model auto --issues "unified-events-interface:1 unified-events-interface:2"
#

set -euo pipefail

# Check bash version
if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    echo "❌ Error: This script requires Bash 4.0 or higher"
    exit 1
fi

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
MODEL=""
MAX_PARALLEL=3  # Conservative default for library creation tasks
DRY_RUN=false
FILTER_REPOS=""
FILTER_PHASE=""
FILTER_PRIORITY=""
CUSTOM_ISSUES=""
ISSUE_MANIFEST="$SCRIPT_DIR/issue-manifest.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --max-parallel)
            MAX_PARALLEL="$2"
            shift 2
            ;;
        --repos)
            FILTER_REPOS="$2"
            shift 2
            ;;
        --phase)
            FILTER_PHASE="$2"
            shift 2
            ;;
        --priority)
            FILTER_PRIORITY="$2"
            shift 2
            ;;
        --issues)
            CUSTOM_ISSUES="$2"
            shift 2
            ;;
        --issue-manifest)
            ISSUE_MANIFEST="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            head -n 30 "$0" | grep "^#" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate
if [ -z "$MODEL" ]; then
    echo "❌ Error: --model is required"
    exit 1
fi

echo "========================================="
echo "Market Data Infrastructure - Batch Execution"
echo "========================================="
echo ""
echo "Model: $MODEL"
echo "Max parallel: $MAX_PARALLEL"
echo "Dry run: $DRY_RUN"
if [ -n "$FILTER_REPOS" ]; then
    echo "Filter repos: $FILTER_REPOS"
fi
if [ -n "$FILTER_PHASE" ]; then
    echo "Filter phase: $FILTER_PHASE"
fi
if [ -n "$FILTER_PRIORITY" ]; then
    echo "Filter priority: $FILTER_PRIORITY"
fi
echo ""

# If custom issues provided, use them directly
if [ -n "$CUSTOM_ISSUES" ]; then
    ISSUE_LIST="$CUSTOM_ISSUES"
    echo "🔄 Running with custom issues:"
    for mapped in $ISSUE_LIST; do
        echo "  - $mapped"
    done
    echo ""
else
    # Read issues from manifest
    if [ ! -f "$ISSUE_MANIFEST" ]; then
        echo "❌ Error: Issue manifest not found: $ISSUE_MANIFEST"
        echo ""
        echo "Run Stage 3 first:"
        echo "  cd $SCRIPT_DIR"
        echo "  python 02-create-issues.py --org IggyIkenna --epic-file ../../epic-breakdowns/epic-market-data-infrastructure.md --apply"
        exit 1
    fi

    echo "📋 Reading issues from manifest: $ISSUE_MANIFEST"
    echo ""

    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        echo "❌ Error: jq is required for parsing issue manifest"
        echo "   Install: brew install jq"
        exit 1
    fi

    # Build issue list from manifest with filtering
    ISSUE_LIST=""
    REPOS=$(jq -r 'keys[]' "$ISSUE_MANIFEST")

    for repo in $REPOS; do
        # Filter by repo name if specified
        if [ -n "$FILTER_REPOS" ]; then
            if [[ ",$FILTER_REPOS," != *",$repo,"* ]]; then
                continue
            fi
        fi

        # Get number of issues for this repo
        ISSUE_COUNT=$(jq -r ".[\"$repo\"] | length" "$ISSUE_MANIFEST")

        # Process each issue
        for i in $(seq 0 $((ISSUE_COUNT - 1))); do
            ISSUE_NUMBER=$(jq -r ".[\"$repo\"][$i].number" "$ISSUE_MANIFEST")
            ISSUE_TITLE=$(jq -r ".[\"$repo\"][$i].title" "$ISSUE_MANIFEST")
            SUBTASK_ID=$(jq -r ".[\"$repo\"][$i].subtask_id" "$ISSUE_MANIFEST")

            # Skip if no issue number
            if [ "$ISSUE_NUMBER" == "null" ] || [ -z "$ISSUE_NUMBER" ]; then
                continue
            fi

            # Filter by phase (from subtask ID)
            if [ -n "$FILTER_PHASE" ]; then
                TASK_PHASE=$(echo "$SUBTASK_ID" | cut -d'.' -f1 | sed 's/Subtask //g')
                if [ "$TASK_PHASE" != "$FILTER_PHASE" ]; then
                    continue
                fi
            fi

            # Filter by priority (from issue title - TODO: improve with labels)
            if [ -n "$FILTER_PRIORITY" ]; then
                if [[ "$ISSUE_TITLE" != *"$FILTER_PRIORITY"* ]]; then
                    continue
                fi
            fi

            # Add to issue list
            ISSUE_LIST="$ISSUE_LIST $repo:$ISSUE_NUMBER"
        done
    done

    if [ -z "$ISSUE_LIST" ]; then
        echo "❌ Error: No issues found matching filters"
        echo ""
        echo "Check filters:"
        echo "  - Repos: $FILTER_REPOS"
        echo "  - Phase: $FILTER_PHASE"
        echo "  - Priority: $FILTER_PRIORITY"
        exit 1
    fi

    echo "Issues to process:"
    for mapped in $ISSUE_LIST; do
        repo="${mapped%%:*}"
        issue="${mapped##*:}"
        subtask=$(jq -r ".[\"$repo\"][] | select(.number == \"$issue\") | .subtask_id" "$ISSUE_MANIFEST" 2>/dev/null || echo "")
        echo "  - $mapped ($subtask)"
    done
    echo ""
    echo "Total issues: $(echo $ISSUE_LIST | wc -w | tr -d ' ')"
    echo ""
fi

# Call batch-fix-v2.sh with mapped issues
if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN: Would call batch-fix-v2.sh with:"
    echo "  --model $MODEL"
    echo "  --issues \"$ISSUE_LIST\""
    echo "  --max-parallel $MAX_PARALLEL"
    echo ""
    echo "Command:"
    echo "  bash ../../automation/batch-fix-v2.sh \\"
    echo "    --model \"$MODEL\" \\"
    echo "    --issues \"$ISSUE_LIST\" \\"
    echo "    --max-parallel $MAX_PARALLEL"
else
    # Use explicit bash path or fall back to current bash
    BASH_BIN="${BASH:-/opt/homebrew/bin/bash}"
    if ! command -v "$BASH_BIN" &>/dev/null; then
        BASH_BIN="$(command -v bash)"
    fi

    echo "🚀 Starting batch execution..."
    echo ""

    exec "$BASH_BIN" "$SCRIPT_DIR/../../automation/batch-fix-v2.sh" \
        --model "$MODEL" \
        --issues "$ISSUE_LIST" \
        --max-parallel "$MAX_PARALLEL"
fi
