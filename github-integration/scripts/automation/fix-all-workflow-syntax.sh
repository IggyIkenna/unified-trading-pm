#!/usr/bin/env bash
#
# Fix duplicate run: keys in quality-gates.yml workflows across all repos
#
# The issue: An empty "Install dependencies" step followed by orphaned run: keys
# This script removes the empty step and properly formats the remaining steps.
#
# Usage:
#   bash fix-all-workflow-syntax.sh           # Fix all repos
#   bash fix-all-workflow-syntax.sh --dry-run # Preview only

set -uo pipefail # Removed -e to continue on errors

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
      echo "Fixes duplicate run: keys in quality-gates.yml across all repos"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# List of repos with the issue
BROKEN_REPOS=(
  "execution-services"
  "features-calendar-service"
  "features-delta-one-service"
  "features-onchain-service"
  "features-volatility-service"
  "instruments-service"
  "market-data-processing-service"
  "sports-betting-service"
  "strategy-service"
  "unified-trading-library"
  "unified-trading-deployment-v2"
)

echo "🔧 Fixing workflow syntax across ${#BROKEN_REPOS[@]} repos"
echo "Dry run: $DRY_RUN"
echo ""

FIXED_COUNT=0
SKIPPED_COUNT=0

for repo in "${BROKEN_REPOS[@]}"; do
  WORKFLOW_FILE="$WORKSPACE_ROOT/$repo/.github/workflows/quality-gates.yml"

  if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "⚠️  $repo: No workflow file"
    ((SKIPPED_COUNT++))
    continue
  fi

  echo "🔧 Checking: $repo"

  # Use Python to fix the YAML properly
  if [ "$DRY_RUN" = false ]; then
    python3 - "$WORKFLOW_FILE" <<'PYTHON_EOF'
import sys
import re

workflow_file = sys.argv[1]

with open(workflow_file, 'r') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]

    # Check if this is the empty "Install dependencies" step
    if line.strip() == '- name: Install dependencies':
        # Look ahead to see if next line is blank or another step
        if i + 1 < len(lines) and (lines[i + 1].strip() == '' or lines[i + 1].strip().startswith('- name:')):
            # This is an empty step - skip it
            print(f"  Removing empty step at line {i + 1}")
            i += 1
            # Also skip following blank line if present
            if i < len(lines) and lines[i].strip() == '':
                i += 1
            continue

    # Check for orphaned run: at wrong indentation (should be under a step)
    if i > 0 and line.strip().startswith('run:') and not line.startswith('      '):
        # This is likely orphaned from the empty step
        # Check if previous step has a run: already
        prev_has_run = False
        for j in range(i - 1, max(0, i - 5), -1):
            if 'run:' in lines[j]:
                prev_has_run = True
                break
            if lines[j].strip().startswith('- name:'):
                break

        if prev_has_run:
            # Previous step already has run:, this is a duplicate - skip it
            print(f"  Removing duplicate run: at line {i + 1}")
            i += 1
            # Skip the multi-line run: block
            while i < len(lines) and (lines[i].startswith('        ') or lines[i].strip() == ''):
                i += 1
            continue

    fixed_lines.append(line)
    i += 1

with open(workflow_file, 'w') as f:
    f.writelines(fixed_lines)

print(f"  ✅ Fixed")
PYTHON_EOF

    # Commit the fix
    cd "$WORKSPACE_ROOT/$repo"

    if git diff --quiet .github/workflows/quality-gates.yml 2>/dev/null; then
      echo "  ℹ️  No changes needed"
      ((SKIPPED_COUNT++))
    else
      git add .github/workflows/quality-gates.yml
      if git commit -m "Fix workflow syntax: remove empty step and duplicate run: keys

GitHub Actions error:
- Empty 'Install dependencies' step (no run:)
- Duplicate run: key at wrong indentation

This was causing workflow validation failures.

Fixed by removing empty step and orphaned run: block." >/dev/null 2>&1; then
        echo "  ✅ Fixed and committed locally"
        ((FIXED_COUNT++))
      else
        echo "  ⚠️  Fixed but commit failed (check git config)"
        ((SKIPPED_COUNT++))
      fi
    fi
  else
    echo "  [DRY RUN] Would remove empty step and duplicate run: keys"
    ((FIXED_COUNT++))
  fi

  echo ""
done

echo "========================================================================"
echo "Summary"
echo "========================================================================"
echo "Fixed:   $FIXED_COUNT repos"
echo "Skipped: $SKIPPED_COUNT repos"
echo ""

if [ "$DRY_RUN" = false ] && [ $FIXED_COUNT -gt 0 ]; then
  echo "✅ All workflows fixed!"
  echo ""
  echo "Next steps:"
  echo "1. Review changes in each repo: git log -1 --stat"
  echo "2. Push all at once:"
  echo "   cd $WORKSPACE_ROOT/unified-trading-deployment-v2"
  echo "   bash git-quickmerge.sh 'Fix workflow syntax: remove duplicate run keys' --all"
  echo ""
  echo "Or push individually to test incrementally"
fi
