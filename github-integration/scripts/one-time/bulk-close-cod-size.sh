#!/bin/bash
#
# Bulk DELETE COD-SIZE issues for files between 400-1500 lines
# (these are now invalid - threshold changed from 400 to 1500)
#
# Issues for files >1500 lines are kept open (still violations)
#
# Usage:
#   bash bulk-close-cod-size.sh [--dry-run]
#

set -euo pipefail

REPO="${REPO:-IggyIkenna/unified-trading-codex}"
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
  esac
done

echo "Fetching all open COD-SIZE issues from $REPO..."

# Get all open issues with "COD-SIZE" in the title
ALL_ISSUES=$(gh issue list --repo "$REPO" --state open --search "COD-SIZE in:title" \
  --limit 500 --json number,title -q '.[] | "\(.number)|\(.title)"' 2>/dev/null)

if [ -z "$ALL_ISSUES" ]; then
  echo "No COD-SIZE issues found."
  exit 0
fi

# Parse issues and filter for 400 < lines <= 1500
ISSUES_TO_CLOSE=()
ISSUES_TO_KEEP=()

while IFS='|' read -r issue_num title; do
  # Extract line count from title format: "File >400 lines in {path} ({N} lines)"
  if [[ "$title" =~ \(([0-9]+)\ lines\) ]]; then
    line_count="${BASH_REMATCH[1]}"

    if [ "$line_count" -gt 1500 ]; then
      # Keep issues for files >1500 lines (still violations)
      ISSUES_TO_KEEP+=("$issue_num:$line_count")
    elif [ "$line_count" -gt 400 ]; then
      # Close issues for files 400-1500 lines (now acceptable)
      ISSUES_TO_CLOSE+=("$issue_num:$line_count")
    fi
  fi
done <<<"$ALL_ISSUES"

DELETE_COUNT=${#ISSUES_TO_CLOSE[@]}
KEEP_COUNT=${#ISSUES_TO_KEEP[@]}

echo ""
echo "Analysis:"
echo "  Issues to DELETE (400-1500 lines): $DELETE_COUNT"
echo "  Issues to keep open (>1500 lines): $KEEP_COUNT"
echo ""

if [ "$DRY_RUN" = true ]; then
  if [ $DELETE_COUNT -gt 0 ]; then
    echo "DRY RUN: Would DELETE the following issues (400-1500 lines, now invalid):"
    for item in "${ISSUES_TO_CLOSE[@]}"; do
      IFS=':' read -r issue_num line_count <<<"$item"
      TITLE=$(gh issue view "$issue_num" --repo "$REPO" --json title -q '.title' 2>/dev/null || echo "Unknown")
      echo "  #$issue_num ($line_count lines): $TITLE"
    done
  fi
  echo ""
  if [ $KEEP_COUNT -gt 0 ]; then
    echo "DRY RUN: Would keep open the following issues (>1500 lines):"
    for item in "${ISSUES_TO_KEEP[@]}"; do
      IFS=':' read -r issue_num line_count <<<"$item"
      TITLE=$(gh issue view "$issue_num" --repo "$REPO" --json title -q '.title' 2>/dev/null || echo "Unknown")
      echo "  #$issue_num ($line_count lines): $TITLE"
    done
  fi
  echo ""
  echo "Run without --dry-run to actually DELETE the 400-1500 line issues."
  exit 0
fi

if [ $DELETE_COUNT -eq 0 ]; then
  echo "No issues to delete (all COD-SIZE issues are >1500 lines)."
  exit 0
fi

echo "Issues to DELETE ($DELETE_COUNT):"
for item in "${ISSUES_TO_CLOSE[@]}"; do
  IFS=':' read -r issue_num line_count <<<"$item"
  echo "  #$issue_num ($line_count lines)"
done

echo ""
echo "⚠️  WARNING: This will PERMANENTLY DELETE these issues (not just close them)."
echo "   They are invalid because the threshold changed from 400 to 1500 lines."
echo ""
read -p "DELETE $DELETE_COUNT issues? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Cancelled."
  exit 0
fi

echo ""
echo "Deleting issues..."
DELETED=0
FAILED=0

for item in "${ISSUES_TO_CLOSE[@]}"; do
  IFS=':' read -r issue_num line_count <<<"$item"
  echo -n "Deleting #$issue_num ($line_count lines)... "
  # Note: gh issue delete requires confirmation, use --yes flag
  if gh issue delete "$issue_num" --repo "$REPO" --yes 2>/dev/null; then
    echo "✓"
    ((DELETED++))
  else
    echo "✗ (failed)"
    ((FAILED++))
  fi
done

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "  Deleted: $DELETED (400-1500 lines, now invalid)"
echo "  Failed: $FAILED"
echo "  Kept open: $KEEP_COUNT (>1500 lines, still violations)"
echo ""
if [ $KEEP_COUNT -gt 0 ]; then
  echo "Remaining open issues (>1500 lines):"
  for item in "${ISSUES_TO_KEEP[@]}"; do
    IFS=':' read -r issue_num line_count <<<"$item"
    echo "  #$issue_num ($line_count lines)"
  done
  echo ""
  echo "These files still need refactoring. To batch fix:"
  echo "  cd $(dirname "$0")"
  echo "  ISSUES=\$(bash list-codex-issues-by-category.sh size)"
  echo "  bash batch-fix.sh --model auto --issues \"\$ISSUES\" --max-parallel 4"
fi
