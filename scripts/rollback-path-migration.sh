#!/usr/bin/env bash
# Auto-generated rollback script
# Created: Mon Mar  2 05:19:48 GMT 2026
# Reverts: /Users/ikennaigboaka/Documents/Documents - Mac/repos → /Users/ikennaigboaka/Documents/Documents/repos

set -euo pipefail

echo "Rolling back path migration..."
echo "  From: /Users/ikennaigboaka/Documents/Documents - Mac/repos"
echo "  To:   /Users/ikennaigboaka/Documents/Documents/repos"
echo ""

read -r -p "Continue? [y/N]: " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled"
    exit 0
fi

# Run migration in reverse
bash "$(dirname "$0")/migrate-all-paths.sh" "/Users/ikennaigboaka/Documents/Documents - Mac/repos" "/Users/ikennaigboaka/Documents/Documents/repos"

echo "Rollback complete!"
echo "Update your shell config to use: export UNIFIED_TRADING_WORKSPACE_ROOT=\"/Users/ikennaigboaka/Documents/Documents/repos\""
