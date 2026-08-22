#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# sync-main — Admin force-sync all repos to main (preserve-local by default).
#
# Runs admin-force-sync-all-to-main.sh with --admin-confirm and default message.
# Default: stage, commit, push; stay on current branch (--preserve-local).
#
# Usage:
#   sync-main
#   sync-main --message "chore: custom message"
#   sync-main --switch-to-main      # switch to main after push (old behavior)
#   sync-main --feat-branch         # push to active_feature_branch from workspace-manifest.json
#   sync-main --stag-branch         # push to staging branch
#   sync-main --switch-only         # local branch switch only — no commit, no push (stays on main)
#   sync-main --feat-branch --switch-only  # switch all repos to active feature branch, no push
#   sync-main --stag-branch --switch-only  # switch all repos to staging, no push
#   sync-main --dry-run
#
# All other flags (--limit, --repo, --filter, --repos, --skip-protection,
# --no-commit, --max-workers) are passed straight through.
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

# --message conflicts with --switch-only; omit it when --switch-only is present
_has_switch_only=false
for _a in "$@"; do [[ "$_a" == "--switch-only" ]] && _has_switch_only=true; done
_msg_args=()
[[ "$_has_switch_only" == "false" ]] && _msg_args=(--message "chore: admin force sync")

exec bash "$PM_ROOT/scripts/repo-management/admin-force-sync-all-to-main.sh" \
  --admin-confirm \
  "${_msg_args[@]+"${_msg_args[@]}"}" \
  "$@"
