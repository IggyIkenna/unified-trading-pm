#!/bin/bash
#
# Master workflow for updating COD-SIZE threshold from 400 to 1500 lines
#
# This script:
#   1. Closes COD-SIZE issues for files 400-1500 lines (now acceptable)
#   2. Keeps issues for files >1500 lines open (still violations)
#
# No need to rerun diff checker - existing >1500 line issues remain valid
#
# Usage:
#   bash update-cod-size-threshold.sh [--dry-run]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
    esac
done

echo "=========================================="
echo "COD-SIZE Threshold Update Workflow"
echo "From: 400 lines → To: 1500 lines"
echo "=========================================="
echo ""
echo "Strategy:"
echo "  1. Run diff checker to create issues for current >1500 line files"
echo "  2. DELETE issues for files 400-1500 lines (now invalid)"
echo "  3. Keep issues for files >1500 lines (still need fixing)"
echo ""

# Step 1: Run diff checker first (to catch files like instruments-service 2431-line file)
echo "Step 1: Run diff checker to create issues for current violations"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN: Would run:"
    echo "  cd $SCRIPT_DIR"
    echo "  python run-diff-checker.py --repo IggyIkenna/unified-trading-codex"
    echo ""
    echo "This ensures all current files >1500 lines have GitHub issues in the codex repo."
    echo "Then would run bulk-close-cod-size.sh to delete 400-1500 line issues."
    echo ""
    bash "$SCRIPT_DIR/bulk-close-cod-size.sh" --dry-run
    exit 0
fi

read -p "Run diff checker to create issues for current files >1500 lines? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$SCRIPT_DIR"
    # Target unified-trading-codex repo (where COD issues live)
    python run-diff-checker.py --repo IggyIkenna/unified-trading-codex

    if [ $? -ne 0 ]; then
        echo "❌ Diff checker failed."
        exit 1
    fi

    echo ""
    echo "✓ Diff checker complete"
    echo ""
else
    echo "⚠️  Skipped diff checker. Existing issues may be incomplete."
    echo ""
fi

# Step 2: Run the bulk delete script (it filters by line count)
echo "Step 2: Delete issues for files 400-1500 lines (now invalid)"
echo ""

bash "$SCRIPT_DIR/bulk-close-cod-size.sh"

if [ $? -ne 0 ]; then
    echo "❌ Failed to process issues."
    exit 1
fi

echo ""
echo "=========================================="
echo "Workflow Complete"
echo "=========================================="
echo ""
echo "The threshold has been updated to 1500 lines."
echo "Files between 400-1500 lines are now acceptable."
echo ""
echo "If there are remaining open COD-SIZE issues (>1500 lines),"
echo "you can batch fix them with:"
echo ""
echo "  cd $SCRIPT_DIR"
echo "  ISSUES=\$(bash list-codex-issues-by-category.sh size)"
echo "  bash batch-fix.sh --model auto --issues \"\$ISSUES\" --max-parallel 4"
