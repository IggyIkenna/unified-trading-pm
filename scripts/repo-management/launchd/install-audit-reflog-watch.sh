#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Install launchd job for fswatch event-based audit trigger.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
PLIST_SRC="$SCRIPT_DIR/com.unified-trading.audit-reflog-watch.plist.example"
PLIST_DST="$HOME/Library/LaunchAgents/com.unified-trading.audit-reflog-watch.plist"
sed "s|WORKSPACE_ROOT_PLACEHOLDER|$WORKSPACE_ROOT|g" "$PLIST_SRC" > "$PLIST_DST"
echo "Installed $PLIST_DST"
echo "Load: launchctl load $PLIST_DST"
echo "Unload: launchctl unload $PLIST_DST"
