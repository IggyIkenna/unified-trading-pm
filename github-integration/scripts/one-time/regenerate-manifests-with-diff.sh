#!/usr/bin/env bash
#
# Regenerate CODEX_VIOLATIONS_MANIFEST.md for all repos and show diff
#
# Usage:
#   bash regenerate-manifests-with-diff.sh [--repos "repo1,repo2"]
#
# This helps answer: "Did the agent actually fix violations?"
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
WORKSPACE_ROOT="$(cd "$CODEX_ROOT/.." && pwd)"

# All service repos
ALL_REPOS=(
    "execution-services"
    "strategy-service"
    "instruments-service"
    "unified-trading-services"
    "market-data-processing-service"
    "ml-training-service"
    "ml-inference-service"
    "features-delta-one-service"
    "features-volatility-service"
    "features-calendar-service"
    "features-onchain-service"
    "market-tick-data-handler"
    "unified-trading-deployment-v2"
)

# Parse arguments
FILTER_REPOS=""
if [ "${1:-}" = "--repos" ]; then
    FILTER_REPOS="$2"
    shift 2
fi

# Determine which repos to process
if [ -n "$FILTER_REPOS" ]; then
    IFS=',' read -ra REPOS <<< "$FILTER_REPOS"
else
    REPOS=("${ALL_REPOS[@]}")
fi

echo "════════════════════════════════════════════════════════════════════════"
echo "Regenerating Codex Violation Manifests"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "Repos: ${REPOS[*]}"
echo ""

# Step 1: Save current manifests (if they exist) for comparison
BACKUP_DIR="/tmp/codex-manifest-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📁 Step 1: Backing up current manifests..."
for repo in "${REPOS[@]}"; do
    manifest="$WORKSPACE_ROOT/$repo/CODEX_VIOLATIONS_MANIFEST.md"
    if [ -f "$manifest" ]; then
        cp "$manifest" "$BACKUP_DIR/${repo}_MANIFEST.md"
        echo "  ✓ $repo"
    fi
done
echo ""

# Step 2: Regenerate manifests
echo "🔄 Step 2: Regenerating manifests (running diff-checker on each repo)..."
echo ""

cd "$SCRIPT_DIR"
python3 generate-codex-violation-manifests.py

echo ""

# Step 3: Compare before/after
echo "📊 Step 3: Comparing violations (before → after)..."
echo ""
echo "Repository                               Before    After     Change"
echo "────────────────────────────────────────────────────────────────────────"

TOTAL_BEFORE=0
TOTAL_AFTER=0

for repo in "${REPOS[@]}"; do
    manifest="$WORKSPACE_ROOT/$repo/CODEX_VIOLATIONS_MANIFEST.md"
    backup="$BACKUP_DIR/${repo}_MANIFEST.md"

    # Count violations in new manifest
    if [ -f "$manifest" ]; then
        AFTER=$(grep -c "^#### [0-9]" "$manifest" 2>/dev/null || echo "0")
        # Alternative: extract from "**Total Violations**:" line
        if [ "$AFTER" = "0" ]; then
            AFTER=$(grep "^\*\*Total Violations\*\*:" "$manifest" 2>/dev/null | grep -oE '[0-9]+' || echo "0")
        fi
    else
        AFTER="N/A"
    fi

    # Count violations in old manifest
    if [ -f "$backup" ]; then
        BEFORE=$(grep -c "^#### [0-9]" "$backup" 2>/dev/null || echo "0")
        if [ "$BEFORE" = "0" ]; then
            BEFORE=$(grep "^\*\*Total Violations\*\*:" "$backup" 2>/dev/null | grep -oE '[0-9]+' || echo "0")
        fi
    else
        BEFORE="N/A"
    fi

    # Calculate change
    if [ "$BEFORE" != "N/A" ] && [ "$AFTER" != "N/A" ]; then
        CHANGE=$((AFTER - BEFORE))
        if [ "$CHANGE" -lt 0 ]; then
            CHANGE_STR="✅ $CHANGE"  # Improvement
        elif [ "$CHANGE" -gt 0 ]; then
            CHANGE_STR="⚠️  +$CHANGE"  # Regression
        else
            CHANGE_STR="   -"  # No change
        fi

        TOTAL_BEFORE=$((TOTAL_BEFORE + BEFORE))
        TOTAL_AFTER=$((TOTAL_AFTER + AFTER))
    else
        CHANGE_STR="   NEW"
    fi

    printf "%-40s %8s  %8s  %10s\n" "$repo" "$BEFORE" "$AFTER" "$CHANGE_STR"
done

echo "────────────────────────────────────────────────────────────────────────"
TOTAL_CHANGE=$((TOTAL_AFTER - TOTAL_BEFORE))
if [ "$TOTAL_CHANGE" -lt 0 ]; then
    TOTAL_CHANGE_STR="✅ $TOTAL_CHANGE (improved!)"
elif [ "$TOTAL_CHANGE" -gt 0 ]; then
    TOTAL_CHANGE_STR="⚠️  +$TOTAL_CHANGE (regression)"
else
    TOTAL_CHANGE_STR="   - (no change)"
fi
printf "%-40s %8s  %8s  %s\n" "TOTAL" "$TOTAL_BEFORE" "$TOTAL_AFTER" "$TOTAL_CHANGE_STR"
echo ""

# Step 4: Show which repos are now clean
echo "✨ Step 4: Clean repos (0 violations)..."
for repo in "${REPOS[@]}"; do
    manifest="$WORKSPACE_ROOT/$repo/CODEX_VIOLATIONS_MANIFEST.md"
    if [ -f "$manifest" ] && grep -q "No violations found" "$manifest" 2>/dev/null; then
        echo "  ✅ $repo"
    fi
done
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "✅ DONE"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "📁 Old manifests backed up to: $BACKUP_DIR"
echo "📁 New manifests saved to: <repo>/CODEX_VIOLATIONS_MANIFEST.md"
echo ""
echo "To see detailed diff for a specific repo:"
echo "  diff $BACKUP_DIR/<repo>_MANIFEST.md <repo>/CODEX_VIOLATIONS_MANIFEST.md"
echo ""
