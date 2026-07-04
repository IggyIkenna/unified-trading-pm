#!/usr/bin/env bash
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
# regenerate-plan-inventory.sh — prek hook: keep the auto-generated active-plan
# inventory table (embedded in plans/active/master_to_live_defi_2026_05_23.md)
# fresh at commit time and after pulls.
#
# Stages (wired in scripts/pre-commit-templates/docs.pre-commit-config.yaml):
#   pre-commit  (mode: --stage)   — regenerate + re-stage the master file if the
#                                   table changed, so the commit carries a fresh
#                                   table (same mutate+restage pattern as the
#                                   prettier-autostage hook).
#   post-merge / post-rewrite     — regenerate after `git pull` (merge or rebase)
#                                   so the local table reflects pulled-in plan
#                                   state; leaves the change in the working tree
#                                   (never auto-commits after a pull).
#
# IMPORTANT: reads the LOCAL WORKING TREE (plans/active/*.md on disk), not git
# objects — uncommitted plan edits ARE reflected in the regenerated table.
# PM-only: no-ops in any other repo the docs template rolls out to.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
[ "$(basename "$REPO_ROOT")" = "unified-trading-pm" ] || exit 0
REGEN="$REPO_ROOT/scripts/plans/regenerate_active_plan_inventory.py"
[ -f "$REGEN" ] || exit 0
MASTER="plans/active/master_to_live_defi_2026_05_23.md"

PY="$REPO_ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

"$PY" "$REGEN" >/dev/null

if ! git -C "$REPO_ROOT" diff --quiet -- "$MASTER"; then
  if [ "${1:-}" = "--stage" ]; then
    git -C "$REPO_ROOT" add -- "$MASTER"
    echo "plan-inventory: table refreshed + re-staged ($MASTER)"
  else
    echo "plan-inventory: table refreshed after pull — commit $MASTER when convenient"
  fi
else
  echo "plan-inventory: table already fresh"
fi
