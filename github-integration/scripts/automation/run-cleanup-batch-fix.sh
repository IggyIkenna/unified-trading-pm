#!/usr/bin/env bash
#
# Wrapper for batch-fix-v2.sh that handles cleanup issues in service repos
#
# Usage:
#   bash run-cleanup-batch-fix.sh --model <model> [OPTIONS]
#
# Options:
#   --model <model>        AI model to use (required)
#   --max-parallel <n>     Max parallel workers (default: 5)
#   --repos <list>         Comma-separated repo names to filter (e.g., "unified-trading-services,market-tick-data-handler")
#   --issues "<list>"      Custom issues (overrides default cleanup issues)
#   --dry-run             Preview what would be done
#
# Examples:
#   # All cleanup issues
#   bash run-cleanup-batch-fix.sh --model auto --max-parallel 5
#
#   # Just unified-trading-services
#   bash run-cleanup-batch-fix.sh --model auto --repos unified-trading-services
#
#   # Custom issues
#   bash run-cleanup-batch-fix.sh --model auto --issues "unified-trading-services:48 market-tick-data-handler:51"
#

set -euo pipefail

# Note: Bash 3.x compatible - associative arrays removed
# Always pass --issues parameter to this script (via wrapper)

MODEL=""
MAX_PARALLEL=5  # Default: 5 (with file locking wrapper, higher parallelism is safe)
DRY_RUN=false
FILTER_REPOS=""  # Optional: comma-separated list of repos to filter

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
        --issues)
            # Pass through custom issues (overrides default cleanup issues)
            CUSTOM_ISSUES="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -z "$MODEL" ]; then
    echo "❌ Error: --model is required"
    exit 1
fi

# If custom issues provided, use them directly
if [ -n "${CUSTOM_ISSUES:-}" ]; then
    ISSUE_LIST="$CUSTOM_ISSUES"
    echo "🔄 Running with custom issues..."
else
    echo "❌ Error: --issues parameter is required (associative arrays removed for Bash 3.x compatibility)"
    echo "   Use the wrapper script: scripts/projects/initial-cleanup/04-run-batch-fix.sh"
    exit 1
fi

echo ""
echo "Model: $MODEL"
echo "Max parallel: $MAX_PARALLEL"
echo "Dry run: $DRY_RUN"
if [ -n "$FILTER_REPOS" ]; then
    echo "Filter repos: $FILTER_REPOS"
fi
echo ""

echo "Issues to process:"
for mapped in $ISSUE_LIST; do
    echo "  - $mapped"
done
echo ""

# Call batch-fix-v2.sh with mapped issues
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN: Would call batch-fix-v2.sh with:"
    echo "  --model $MODEL"
    echo "  --issues \"$ISSUE_LIST\""
    echo "  --max-parallel $MAX_PARALLEL"
else
    # Use explicit bash path or fall back to current bash
    BASH_BIN="${BASH:-/opt/homebrew/bin/bash}"
    if ! command -v "$BASH_BIN" &>/dev/null; then
        BASH_BIN="$(command -v bash)"
    fi

    exec "$BASH_BIN" "$SCRIPT_DIR/batch-fix-v2.sh" \
        --model "$MODEL" \
        --issues "$ISSUE_LIST" \
        --max-parallel "$MAX_PARALLEL"
fi
