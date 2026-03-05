#!/usr/bin/env bash
# Run fswatch on workspace .git/logs; trigger audit on changes.
# Event-based complement to the time-based launchd job.
#
# Location: unified-trading-pm/scripts/repo-management/watch-and-audit-reflog.sh
# Run: bash watch-and-audit-reflog.sh (or via launchd)
# Stop: Ctrl+C or launchctl unload the plist

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
AUDIT_SCRIPT="$SCRIPT_DIR/run-audit-reflog-with-alert.sh"

cd "$WORKSPACE_ROOT"

# Watch .git/logs (commits, resets, checkouts). -l 2 debounces.
exec /usr/local/bin/fswatch -o -r -l 2 -i '\.git/logs' . | while read -r _; do
  bash "$AUDIT_SCRIPT"
done
