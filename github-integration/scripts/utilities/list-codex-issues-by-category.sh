#!/bin/bash
#
# List open GitHub issues in unified-trading-codex by codex compliance category.
# Excludes COD-SIZE (file >1500 lines) by default.
#
# Usage:
#   bash list-codex-issues-by-category.sh <category>
#   bash list-codex-issues-by-category.sh all
#   bash list-codex-issues-by-category.sh all --include-size
#
# Categories (match quality-gates codex checks):
#   print       → COD-PRINT   (print() use logger)
#   getenv      → COD-GETENV  (os.getenv use config)
#   datetime    → COD-UTC     (datetime.now use UTC)
#   bare        → COD-BARE    (bare except)
#   requests    → COD-REQUESTS
#   timesleep   → COD-TIMESLEEP (time.sleep in async)
#   asyncio     → COD-ASYNCRUN (asyncio.run in loop)
#   import      → COD-IMPORT  (import inside function)
#   size        → COD-SIZE    (files >1500 lines)
#   all         → All COD-* except COD-SIZE (unless --include-size)
#
# Output: Space-separated issue numbers (for use with batch-fix.sh)
#
# Examples:
#   bash list-codex-issues-by-category.sh print
#   bash list-codex-issues-by-category.sh getenv
#   ISSUES=$(bash list-codex-issues-by-category.sh all)
#   bash batch-fix.sh --model gpt-4o-mini --issues "$ISSUES"
#

set -euo pipefail

REPO="${REPO:-IggyIkenna/unified-trading-codex}"
CATEGORY="${1:-}"
INCLUDE_SIZE=false

for arg in "$@"; do
  case "$arg" in
    --include-size) INCLUDE_SIZE=true ;;
  esac
done

# Map category to GitHub search term (title contains this)
get_search_term() {
  case "$1" in
    print) echo "COD-PRINT" ;;
    getenv) echo "COD-GETENV" ;;
    datetime | utc) echo "COD-UTC" ;;
    bare) echo "COD-BARE" ;;
    requests) echo "COD-REQUESTS" ;;
    timesleep) echo "COD-TIMESLEEP" ;;
    asyncio) echo "COD-ASYNCRUN" ;;
    import) echo "COD-IMPORT" ;;
    size) echo "COD-SIZE" ;;
    *) echo "" ;;
  esac
}

# List issue numbers for a search term
list_issues() {
  local term=$1
  gh issue list --repo "$REPO" --state open --search "$term" --limit 500 \
    --json number -q '.[].number' 2>/dev/null | sort -n | tr '\n' ' '
}

if [ -z "$CATEGORY" ]; then
  echo "Usage: $0 <category> [--include-size]" >&2
  echo "" >&2
  echo "Categories: print | getenv | datetime | bare | requests | timesleep | asyncio | import | size | all" >&2
  echo "  all  = all COD-* issues except COD-SIZE (use --include-size to include size)" >&2
  echo "  size = COD-SIZE issues only (files >1500 lines; requires file splitting)" >&2
  exit 1
fi

if [ "$CATEGORY" = "all" ]; then
  # All COD-* categories except SIZE (unless --include-size)
  TERMS="COD-PRINT COD-GETENV COD-UTC COD-BARE COD-REQUESTS COD-TIMESLEEP COD-ASYNCRUN COD-IMPORT"
  if [ "$INCLUDE_SIZE" = true ]; then
    TERMS="$TERMS COD-SIZE"
  fi
  ALL=""
  for term in $TERMS; do
    NEXT=$(list_issues "$term")
    if [ -n "$NEXT" ]; then
      ALL="$ALL $NEXT"
    fi
  done
  # Dedupe and sort (issues might match multiple searches in theory; in practice no)
  echo "$ALL" | tr ' ' '\n' | sort -n -u | tr '\n' ' '
  exit 0
fi

TERM=$(get_search_term "$CATEGORY")
if [ -z "$TERM" ]; then
  echo "Unknown category: $CATEGORY" >&2
  echo "Use: print | getenv | datetime | bare | requests | timesleep | asyncio | import | size | all" >&2
  exit 1
fi

list_issues "$TERM"
