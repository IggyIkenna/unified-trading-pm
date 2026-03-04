#!/usr/bin/env bash
#
# Add parallel testing (-n auto) to all repos that have pytest-xdist
#
# This adds -n auto to pytest commands in quality-gates.yml for repos
# that have pytest-xdist installed but aren't using parallel testing yet.
#
# Expected benefit: 40-60% faster CI runs (GitHub Actions runners have 2 cores)
#
# Usage:
#   bash add-parallel-testing.sh           # Add -n auto to all applicable repos
#   bash add-parallel-testing.sh --dry-run # Preview changes only

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h | --help)
      echo "Usage: $0 [--dry-run]"
      echo ""
      echo "Adds -n auto to pytest commands for parallel testing"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Repos that have pytest-xdist but are NOT using -n auto
REPOS_TO_UPDATE=(
  "features-calendar-service"
  "features-delta-one-service"
  "features-onchain-service"
  "instruments-service"
  "market-tick-data-handler"
  "ml-training-service"
  "sports-betting-service"
  "strategy-service"
)

echo "🚀 Adding parallel testing (-n auto) to ${#REPOS_TO_UPDATE[@]} repos"
echo "Dry run: $DRY_RUN"
echo ""

UPDATED_COUNT=0
SKIPPED_COUNT=0

for repo in "${REPOS_TO_UPDATE[@]}"; do
  WORKFLOW_FILE="$WORKSPACE_ROOT/$repo/.github/workflows/quality-gates.yml"

  if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "⚠️  $repo: No workflow file"
    ((SKIPPED_COUNT++))
    continue
  fi

  # Check if already has -n auto
  if grep -q "\-n auto" "$WORKFLOW_FILE"; then
    echo "✅ $repo: Already using -n auto"
    ((SKIPPED_COUNT++))
    continue
  fi

  echo "🔧 $repo: Adding -n auto..."

  if [ "$DRY_RUN" = false ]; then
    # Add -n auto to all pytest commands
    # Pattern: pytest tests/{unit,integration,e2e}/ ... --timeout=XX
    # Add: -n auto after the timeout

    sed -i.bak -E \
      's/(pytest tests\/(unit|integration|e2e)\/.* --timeout=[0-9]+)( \\)?$/\1 -n auto\3/' \
      "$WORKFLOW_FILE"

    # Also handle cases without line continuation (no backslash at end)
    sed -i.bak2 -E \
      's/(pytest tests\/(unit|integration|e2e)\/.* --timeout=[0-9]+)$/\1 -n auto/' \
      "$WORKFLOW_FILE"

    # Remove backup files
    rm -f "$WORKFLOW_FILE.bak" "$WORKFLOW_FILE.bak2"

    # Verify changes were made
    if grep -q "\-n auto" "$WORKFLOW_FILE"; then
      echo "  ✅ Added -n auto"

      # Show what changed
      echo "  📝 Changes:"
      grep -n "\-n auto" "$WORKFLOW_FILE" | head -5 | sed 's/^/     /'

      ((UPDATED_COUNT++))
    else
      echo "  ⚠️  No changes made (pattern might not match)"
      ((SKIPPED_COUNT++))
    fi
  else
    echo "  [DRY RUN] Would add -n auto to pytest commands"
    ((UPDATED_COUNT++))
  fi

  echo ""
done

echo "========================================================================"
echo "Summary"
echo "========================================================================"
echo "Updated: $UPDATED_COUNT repos"
echo "Skipped: $SKIPPED_COUNT repos"
echo ""

if [ "$DRY_RUN" = false ] && [ $UPDATED_COUNT -gt 0 ]; then
  echo "✅ Parallel testing enabled!"
  echo ""
  echo "Next steps:"
  echo "1. Review changes: git diff .github/workflows/quality-gates.yml (in each repo)"
  echo "2. Commit changes:"
  echo "   for repo in ${REPOS_TO_UPDATE[*]}; do"
  echo "     cd $WORKSPACE_ROOT/\$repo"
  echo "     git add .github/workflows/quality-gates.yml"
  echo "     git commit -m 'Enable parallel testing with pytest-xdist -n auto'"
  echo "   done"
  echo "3. Push all at once:"
  echo "   cd $WORKSPACE_ROOT/unified-trading-deployment-v2"
  echo "   bash git-quickmerge.sh 'Enable parallel testing (-n auto)' --all"
  echo ""
  echo "Expected benefit: 40-60% faster CI runs"
fi
