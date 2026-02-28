#!/usr/bin/env bash
#
# Cleanup Leftover Workspace Pools
#
# Removes temporary workspace directories from interrupted batch-fix runs.
# Safe to run anytime - only removes pools older than a threshold.
#
# Usage:
#   bash cleanup-workspaces.sh           # Clean pools >60 min old
#   bash cleanup-workspaces.sh --all     # Clean all (including recent)
#   bash cleanup-workspaces.sh --dry-run # Show what would be removed

set -euo pipefail

# Configuration
MIN_AGE_MINUTES=60  # Default: only clean pools older than 60 minutes
FORCE_ALL=false
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            MIN_AGE_MINUTES=0
            FORCE_ALL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--all] [--dry-run]"
            echo ""
            echo "Options:"
            echo "  --all      Remove all workspace pools (including recent ones)"
            echo "  --dry-run  Show what would be removed without actually removing"
            echo ""
            echo "Default: Only removes pools older than $MIN_AGE_MINUTES minutes"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Detect temp directory (macOS uses /var/folders, Linux uses /tmp)
TEMP_DIR="${TMPDIR:-/tmp}"
TEMP_DIR="${TEMP_DIR%/}"  # Remove trailing slash

echo "🔍 Searching for leftover workspace pools..."
echo "   Temp directory: $TEMP_DIR"
if [ "$FORCE_ALL" = true ]; then
    echo "   Age threshold: All (--all flag)"
else
    echo "   Age threshold: >$MIN_AGE_MINUTES minutes"
fi
echo ""

# Find workspace pools
if [ "$FORCE_ALL" = true ]; then
    # Find all, regardless of age
    POOLS=$(find "$TEMP_DIR" -maxdepth 1 -name "batch-fix-pool-*" -type d 2>/dev/null || true)
else
    # Find only old ones
    POOLS=$(find "$TEMP_DIR" -maxdepth 1 -name "batch-fix-pool-*" -type d -mmin +$MIN_AGE_MINUTES 2>/dev/null || true)
fi

if [ -z "$POOLS" ]; then
    echo "✨ No leftover workspace pools found"
    exit 0
fi

# Count and show details
POOL_COUNT=$(echo "$POOLS" | wc -l | tr -d ' ')
TOTAL_SIZE=0

echo "Found $POOL_COUNT workspace pool(s):"
echo ""

echo "$POOLS" | while read -r pool; do
    if [ -z "$pool" ] || [ ! -d "$pool" ]; then
        continue
    fi

    # Get size and age
    size_kb=$(du -sk "$pool" 2>/dev/null | awk '{print $1}')
    size_mb=$((size_kb / 1024))
    size_gb=$(awk "BEGIN {printf \"%.1f\", $size_kb / 1024 / 1024}")

    age_seconds=$(( $(date +%s) - $(stat -f %m "$pool" 2>/dev/null || echo 0) ))
    age_minutes=$((age_seconds / 60))
    age_hours=$((age_minutes / 60))

    if [ $age_hours -gt 0 ]; then
        age_display="${age_hours}h ${$((age_minutes % 60))}m"
    else
        age_display="${age_minutes}m"
    fi

    if [ $size_mb -gt 1000 ]; then
        size_display="${size_gb}GB"
    else
        size_display="${size_mb}MB"
    fi

    echo "  📦 $(basename "$pool")"
    echo "     Path: $pool"
    echo "     Size: $size_display"
    echo "     Age:  $age_display ago"
    echo ""
done

# Confirm removal
if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN: Would remove $POOL_COUNT workspace pool(s)"
    exit 0
fi

if [ "$FORCE_ALL" = true ]; then
    echo "⚠️  WARNING: About to remove ALL workspace pools (including recent ones)"
    echo "   This may interrupt running batch-fix processes!"
    echo ""
    read -p "   Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi
fi

# Remove pools
echo "🗑️  Removing workspace pools..."
echo ""

REMOVED=0
FAILED=0

echo "$POOLS" | while read -r pool; do
    if [ -z "$pool" ] || [ ! -d "$pool" ]; then
        continue
    fi

    echo "  Removing: $(basename "$pool")..."
    if rm -rf "$pool" 2>/dev/null; then
        echo "    ✅ Removed"
        REMOVED=$((REMOVED + 1))
    else
        echo "    ❌ Failed (may be in use)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Cleanup complete"
echo "   Removed: $POOL_COUNT workspace pool(s)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
