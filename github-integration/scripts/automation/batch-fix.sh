#!/bin/bash
#
# Batch Fix Multiple GitHub Issues using Cursor Agent CLI
#
# Smart Parallelization:
#   - Automatically groups issues by service
#   - Processes each service SEQUENTIALLY (avoids git conflicts)
#   - Processes services in PARALLEL (faster overall)
#
# Usage:
#   bash batch-fix.sh --model <model> --issues "<issue1> <issue2> <issue3>"
#   bash batch-fix.sh --model <model> --issues "[issue1,issue2,issue3]"
#
# Options:
#   --model <model>        Model to use for all issues (required)
#   --issues "<list>"      Space-separated or comma-separated list of issue numbers
#   --sequential           Disable smart grouping, run all sequentially
#   --dry-run             Preview all prompts without executing
#   --max-parallel <n>    Maximum parallel services (default: 5)
#
# Examples:
#   # 8 issues across 3 services → processes 3 services in parallel
#   bash batch-fix.sh --model gpt-4o-mini --issues "589 588 587 586 537 401 402 403"
#
#   # Sequential mode (no parallelization)
#   bash batch-fix.sh --model sonnet-4 --issues "1234 1235 1236" --sequential
#
#   # Dry-run to preview grouping
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
    --verbose | -v)
      VERBOSE=true
      shift
      ;;
    -h | --help)
      echo "Usage: bash batch-fix.sh --model <model> --issues \"<list>\" [OPTIONS]"
      echo ""
      echo "Smart Parallelization:"
      echo "  - Groups issues by service (extracts from issue title)"
      echo "  - Sequential within same service (avoids git conflicts)"
      echo "  - Parallel across different services (faster overall)"
      echo ""
      echo "Options:"
      echo "  --model <model>        Model to use (gpt-5, sonnet-4, sonnet-4-thinking)"
      echo "  --issues \"<list>\"      Issue numbers (space or comma separated)"
      echo "  --sequential           Disable grouping, run all sequentially"
      echo "  --dry-run             Preview prompts without executing"
      echo "  --max-parallel <n>    Max parallel services (default: 5)"
      echo ""
      echo "Examples:"
      echo "  # 8 issues, 3 services → 3 services run in parallel"
      echo "  bash batch-fix.sh --model gpt-4o-mini --issues \"589 588 587 586 537 401 402 403\""
      echo ""
      echo "  # Sequential mode"
      echo "  bash batch-fix.sh --model sonnet-4 --issues \"1234 1235 1236\" --sequential"
      echo ""
      echo "  # Dry-run to preview grouping"
      echo "  bash batch-fix.sh --model sonnet-4 --issues \"1234 1235\" --dry-run"
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
read -ra ISSUE_ARRAY <<<"$ISSUES"

ISSUE_COUNT=${#ISSUE_ARRAY[@]}

echo "🤖 Batch Fix GitHub Issues"
echo "========================================================================"
echo "Model: $MODEL"
echo "Issues: ${ISSUE_ARRAY[*]}"
echo "Count:  $ISSUE_COUNT (deduplicated)"
echo "Mode: $([ "$SEQUENTIAL" = true ] && echo "Sequential (all issues)" || echo "Parallel by service (max $MAX_PARALLEL services)")"
echo "Dry Run: $([ "$DRY_RUN" = true ] && echo "Yes" || echo "No")"
echo ""
echo "Smart Parallelization:"
echo "  - Groups issues by service (avoids git conflicts within service)"
echo "  - Sequential fixes within same service"
echo "  - Parallel fixes across different services"
echo "========================================================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Dry run - show grouping and execution plan
if [ "$DRY_RUN" = true ]; then
  echo "📄 Dry Run Mode - Execution Plan Preview"
  echo ""

  if [ "$SEQUENTIAL" = true ]; then
    echo "Mode: Sequential (all issues processed one-by-one)"
    echo ""
    for ISSUE in "${ISSUE_ARRAY[@]}"; do
      echo "  ▶️  Issue #$ISSUE"
    done
  else
    # Show service grouping
    echo "Mode: Parallel by service (max $MAX_PARALLEL concurrent services)"
    echo ""
    echo "📋 Grouping issues by service..."

    declare -A SERVICE_ISSUES
    CODEX_ISSUE_REPO="IggyIkenna/unified-trading-codex"

    for ISSUE in "${ISSUE_ARRAY[@]}"; do
      ISSUE_TITLE=$(gh issue view "$ISSUE" --repo "$CODEX_ISSUE_REPO" --json title --jq '.title' 2>/dev/null || echo "")

      if [ -z "$ISSUE_TITLE" ]; then
        echo "⚠️  Could not fetch issue #$ISSUE"
        continue
      fi

      SERVICE_NAME=$(echo "$ISSUE_TITLE" | grep -o '\[.*\]' | tr -d '[]' | head -1)

      if [ -z "$SERVICE_NAME" ]; then
        echo "⚠️  Could not extract service from issue #$ISSUE: $ISSUE_TITLE"
        continue
      fi

      if [ -z "${SERVICE_ISSUES[$SERVICE_NAME]:-}" ]; then
        SERVICE_ISSUES[$SERVICE_NAME]="$ISSUE"
      else
        SERVICE_ISSUES[$SERVICE_NAME]="${SERVICE_ISSUES[$SERVICE_NAME]} $ISSUE"
      fi
    done

    echo ""
    echo "📦 Service Groups (${#SERVICE_ISSUES[@]} services will run in parallel):"
    echo ""
    for service in "${!SERVICE_ISSUES[@]}"; do
      issue_list=(${SERVICE_ISSUES[$service]})
      echo "  [$service] → ${#issue_list[@]} issues (sequential): ${SERVICE_ISSUES[$service]}"
    done
    echo ""
    echo "Execution Strategy:"
    echo "  ✓ Services run in parallel (max $MAX_PARALLEL)"
    echo "  ✓ Issues within each service run sequentially"
    echo "  ✓ No git conflicts (isolated by service)"
  fi

  echo ""
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
  # Parallel execution - group by service to avoid git conflicts
  echo "Running fixes in parallel (grouped by service to avoid conflicts)..."
  echo ""

  # Step 1: Group issues by service
  declare -A SERVICE_ISSUES
  CODEX_ISSUE_REPO="IggyIkenna/unified-trading-codex"

  echo "📋 Grouping issues by service..."
  for ISSUE in "${ISSUE_ARRAY[@]}"; do
    # Fetch issue title to extract service name
    ISSUE_TITLE=$(gh issue view "$ISSUE" --repo "$CODEX_ISSUE_REPO" --json title --jq '.title' 2>/dev/null || echo "")

    if [ -z "$ISSUE_TITLE" ]; then
      echo "⚠️  Could not fetch issue #$ISSUE, skipping"
      FAILED_ISSUES+=("$ISSUE")
      continue
    fi

    # Extract service name from title (format: [service-name] ...)
    SERVICE_NAME=$(echo "$ISSUE_TITLE" | grep -o '\[.*\]' | tr -d '[]' | head -1)

    if [ -z "$SERVICE_NAME" ]; then
      echo "⚠️  Could not extract service from issue #$ISSUE: $ISSUE_TITLE"
      FAILED_ISSUES+=("$ISSUE")
      continue
    fi

    # Add to service group
    if [ -z "${SERVICE_ISSUES[$SERVICE_NAME]:-}" ]; then
      SERVICE_ISSUES[$SERVICE_NAME]="$ISSUE"
    else
      SERVICE_ISSUES[$SERVICE_NAME]="${SERVICE_ISSUES[$SERVICE_NAME]} $ISSUE"
    fi
  done

  # Display grouping
  echo ""
  echo "📦 Issue Grouping:"
  for service in "${!SERVICE_ISSUES[@]}"; do
    issue_list=(${SERVICE_ISSUES[$service]})
    echo "  $service: ${#issue_list[@]} issues (${SERVICE_ISSUES[$service]})"
  done
  echo ""

  # Step 2: Process each service in parallel, issues within service sequentially
  echo "🚀 Processing services in parallel (max $MAX_PARALLEL services)..."
  echo ""

  # Function to process all issues for a service
  process_service() {
    local service=$1
    local issues=$2
    local result_file=$3

    echo "[${service}] Starting service processing..."

    # Process issues sequentially for this service (avoid git conflicts)
    for issue in $issues; do
      echo "[${service}] 🔧 Fixing issue #$issue..."

      if [ "$VERBOSE" = true ]; then
        VERBOSE_FLAG="--verbose"
      else
        VERBOSE_FLAG=""
      fi

      if bash "$SCRIPT_DIR/auto-fix-issue.sh" "$issue" --model "$MODEL" $VERBOSE_FLAG; then
        echo "SUCCESS:$issue" >>"$result_file"
        echo "[${service}] ✅ Issue #$issue fixed"
      else
        echo "FAILED:$issue" >>"$result_file"
        echo "[${service}] ❌ Issue #$issue failed"
      fi
    done

    echo "[${service}] ✅ Service processing complete"
  }

  export -f process_service
  export SCRIPT_DIR MODEL VERBOSE

  # Create temp file for results
  RESULT_FILE=$(mktemp)

  # Process services in parallel
  PIDS=()
  RUNNING=0

  for service in "${!SERVICE_ISSUES[@]}"; do
    issues="${SERVICE_ISSUES[$service]}"

    echo "▶️  Starting service: $service"

    # Run service processing in background
    process_service "$service" "$issues" "$RESULT_FILE" &
    PIDS+=($!)

    RUNNING=$((RUNNING + 1))

    # Wait if we hit max parallel services
    if [ $RUNNING -ge $MAX_PARALLEL ]; then
      # Wait for any job to finish
      wait "${PIDS[0]}"
      # Remove first PID from array
      PIDS=("${PIDS[@]:1}")
      RUNNING=$((RUNNING - 1))
    fi
  done

  # Wait for all remaining services
  echo ""
  echo "⏳ Waiting for all services to complete..."
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
    done <"$RESULT_FILE"
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
