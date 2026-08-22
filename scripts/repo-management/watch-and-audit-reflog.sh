#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
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

# Resolve a native-arch fswatch explicitly — launchd's default PATH doesn't include
# Homebrew's bin dirs, and an Intel (x86_64) fswatch run under Rosetta on Apple
# Silicon segfaults on the recursive-watch syscalls this script needs (found live
# 2026-08-06: /usr/local/bin/fswatch crash-looped on every invocation). Prefer the
# native Apple Silicon path, fall back to Intel Homebrew / bare PATH lookup for
# other machines.
if [ -x /opt/homebrew/bin/fswatch ]; then
  FSWATCH_BIN=/opt/homebrew/bin/fswatch
elif [ -x /usr/local/bin/fswatch ]; then
  FSWATCH_BIN=/usr/local/bin/fswatch
else
  FSWATCH_BIN="$(command -v fswatch)"
fi

# Watch .git/logs (commits, resets, checkouts). -l 2 debounces.
exec "$FSWATCH_BIN" -o -r -l 2 -i '\.git/logs' . | while read -r _; do
  bash "$AUDIT_SCRIPT"
done
