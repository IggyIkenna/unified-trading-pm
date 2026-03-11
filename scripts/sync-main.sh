#!/usr/bin/env bash
# sync-main — Admin force-sync all repos to main (preserve-local by default).
#
# Runs admin-force-sync-all-to-main.sh with --admin-confirm and default message.
# Default: stage, commit, push; stay on current branch (--preserve-local).
#
# Usage:
#   sync-main
#   sync-main --message "chore: custom message"
#   sync-main --switch-to-main   # old behavior: switch to main after push
#   sync-main --dry-run
#
# Run from workspace root. Add to .zshrc:
#   sync-main() { cd "${WORKSPACE_ROOT:-$HOME/Code/unified-trading-system-repos}" && bash unified-trading-pm/scripts/sync-main.sh "$@"; }

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Resolve workspace root
if [ -f "$PM_ROOT/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
else
  WORKSPACE_ROOT="$(cd "$PM_ROOT/../.." && pwd)"
fi

cd "$WORKSPACE_ROOT"
exec bash "$PM_ROOT/scripts/repo-management/admin-force-sync-all-to-main.sh" \
  --admin-confirm \
  --message "chore: admin force sync" \
  "$@"
