#!/bin/bash
# Initial Cleanup Project: Run Batch Fix with Filtering
#
# Enhanced wrapper for run-cleanup-batch-fix.sh with label/state filtering.
# Filters cleanup issues by labels and state before running batch automation.
#
# Usage:
#   bash 04-run-batch-fix.sh \
#     --model auto \
#     --exclude-labels "blocked,wip" \
#     --require-labels "cleanup" \
#     --state "open" \
#     --max-parallel 4

set -euo pipefail

# Cleanup issues
CLEANUP_ISSUES=(
  "execution-services:147"
  "strategy-service:23"
  "instruments-service:58"
  "unified-trading-library:48"
  "market-data-processing-service:46"
  "ml-training-service:38"
  "ml-inference-service:28"
  "features-delta-one-service:34"
  "features-volatility-service:25"
  "features-calendar-service:37"
  "features-onchain-service:27"
  "market-tick-data-handler:51"
  "unified-trading-deployment-v2:126"
)

MODEL=""
MAX_PARALLEL=5
DRY_RUN=false
FILTER_REPOS=""
EXCLUDE_LABELS=""
REQUIRE_LABELS=""
STATE_FILTER="open"

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
    --exclude-labels)
      EXCLUDE_LABELS="$2"
      shift 2
      ;;
    --require-labels)
      REQUIRE_LABELS="$2"
      shift 2
      ;;
    --state)
      STATE_FILTER="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo ""
      echo "Usage: $0 --model <model> [options]"
      echo ""
      echo "Options:"
      echo "  --model <model>             Model to use (required)"
      echo "  --max-parallel <n>          Max parallel agents (default: 5)"
      echo "  --repos <repo1,repo2>       Filter by repos"
      echo "  --exclude-labels <l1,l2>    Skip issues with these labels"
      echo "  --require-labels <l1,l2>    Only process issues with these labels"
      echo "  --state <open|closed|all>   Filter by issue state (default: open)"
      echo "  --dry-run                   Show what would be processed"
      exit 1
      ;;
  esac
done

if [ -z "$MODEL" ]; then
  echo "❌ Error: --model is required"
  exit 1
fi

# Normalize state filter to uppercase
STATE_FILTER=$(echo "$STATE_FILTER" | tr '[:lower:]' '[:upper:]')

echo "🔍 Filtering issues..."
echo "  State: $STATE_FILTER"
[ -n "$REQUIRE_LABELS" ] && echo "  Require labels: $REQUIRE_LABELS"
[ -n "$EXCLUDE_LABELS" ] && echo "  Exclude labels: $EXCLUDE_LABELS"
[ -n "$FILTER_REPOS" ] && echo "  Repos: $FILTER_REPOS"
echo ""

FILTERED_ISSUES=""

for repo_issue in "${CLEANUP_ISSUES[@]}"; do
  repo_name="${repo_issue%%:*}"
  issue_number="${repo_issue##*:}"

  # Filter by repos
  if [ -n "$FILTER_REPOS" ]; then
    if [[ ",$FILTER_REPOS," != *",$repo_name,"* ]]; then
      continue
    fi
  fi

  # Get issue metadata
  state=$(gh issue view "$issue_number" --repo "IggyIkenna/$repo_name" --json state --jq '.state' 2>/dev/null || echo "ERROR")
  labels=$(gh issue view "$issue_number" --repo "IggyIkenna/$repo_name" --json labels --jq '.labels[].name' 2>/dev/null | tr '\n' ',' | sed 's/,$//' || echo "")

  # Filter by state
  if [ "$STATE_FILTER" != "ALL" ]; then
    if [ "$state" != "$STATE_FILTER" ]; then
      echo "  ⏭️  $repo_name #$issue_number - Skipped (state: $state)"
      continue
    fi
  fi

  # Filter by required labels
  if [ -n "$REQUIRE_LABELS" ]; then
    IFS=',' read -ra REQUIRED <<<"$REQUIRE_LABELS"
    has_required=false
    for req_label in "${REQUIRED[@]}"; do
      req_label_trimmed=$(echo "$req_label" | xargs) # Trim whitespace
      if [[ ",$labels," == *",$req_label_trimmed,"* ]]; then
        has_required=true
        break
      fi
    done
    if [ "$has_required" = false ]; then
      echo "  ⏭️  $repo_name #$issue_number - Skipped (missing required labels)"
      continue
    fi
  fi

  # Filter by excluded labels
  if [ -n "$EXCLUDE_LABELS" ]; then
    IFS=',' read -ra EXCLUDED <<<"$EXCLUDE_LABELS"
    is_excluded=false
    for excl_label in "${EXCLUDED[@]}"; do
      excl_label_trimmed=$(echo "$excl_label" | xargs) # Trim whitespace
      if [[ ",$labels," == *",$excl_label_trimmed,"* ]]; then
        echo "  🔒 $repo_name #$issue_number - Skipped (has '$excl_label_trimmed' label)"
        is_excluded=true
        break
      fi
    done
    if [ "$is_excluded" = true ]; then
      continue
    fi
  fi

  echo "  ✅ $repo_name #$issue_number - Will process (labels: $labels)"
  FILTERED_ISSUES="$FILTERED_ISSUES $repo_issue"
done

if [ -z "$FILTERED_ISSUES" ]; then
  echo ""
  echo "❌ No issues match the filters"
  exit 1
fi

echo ""
ISSUE_COUNT=$(echo "$FILTERED_ISSUES" | wc -w | tr -d ' ')
echo "📋 Issues to process: $ISSUE_COUNT"
echo "$FILTERED_ISSUES" | tr ' ' '\n' | sed 's/^/  - /'
echo ""

if [ "$DRY_RUN" = true ]; then
  echo "🔍 DRY RUN - Would call run-cleanup-batch-fix.sh with:"
  echo "  --model $MODEL"
  echo "  --issues \"$FILTERED_ISSUES\""
  echo "  --max-parallel $MAX_PARALLEL"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # Call the actual batch-fix script (in automation directory)
  exec bash "$SCRIPT_DIR/../../automation/run-cleanup-batch-fix.sh" \
    --model "$MODEL" \
    --issues "$FILTERED_ISSUES" \
    --max-parallel "$MAX_PARALLEL"
fi
