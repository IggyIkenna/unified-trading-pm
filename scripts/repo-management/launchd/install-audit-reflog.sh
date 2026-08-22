#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Install launchd job for weekly audit-reflog-resets.
# Run from: workspace root. Uses (cd to script dir) to find workspace root.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
PLIST_SRC="$SCRIPT_DIR/com.unified-trading.audit-reflog.plist.example"
PLIST_DST="$HOME/Library/LaunchAgents/com.unified-trading.audit-reflog.plist"
sed "s|WORKSPACE_ROOT_PLACEHOLDER|$WORKSPACE_ROOT|g" "$PLIST_SRC" > "$PLIST_DST"
echo "Installed $PLIST_DST"
echo "Load with: launchctl load $PLIST_DST"
