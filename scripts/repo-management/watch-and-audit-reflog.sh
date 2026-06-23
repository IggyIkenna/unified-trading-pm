#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Run fswatch on workspace .git/logs; trigger audit on changes.
# Event-based complement to the time-based launchd job.
#
# Location: unified-trading-pm/scripts/repo-management/watch-and-audit-reflog.sh
# Run: bash watch-and-audit-reflog.sh (or via launchd)
# Stop: Ctrl+C or launchctl unload the plist

set -euo pipefail

# Resolve workspace root from cwd (must run from workspace root)
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  exit 1
fi
AUDIT_SCRIPT="$WORKSPACE_ROOT/unified-trading-pm/scripts/repo-management/run-audit-reflog-with-alert.sh"

cd "$WORKSPACE_ROOT"

# Watch .git/logs (commits, resets, checkouts). -l 2 debounces.
exec /usr/local/bin/fswatch -o -r -l 2 -i '\.git/logs' . | while read -r _; do
  bash "$AUDIT_SCRIPT"
done
