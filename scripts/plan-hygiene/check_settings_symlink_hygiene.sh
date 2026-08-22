#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Guards against the failure class in
# plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md: a stray
# .claude/settings.local.json SYMLINK (into the git-tracked cursor-configs/settings.json) lets any
# writer that heals settings.local.json follow the link and silently strip hooks from the team SSOT.
# link-claude-skills.sh's own heal step now refuses to write through such a symlink (2026-08-11), but
# this check is the fleet-wide backstop for any OTHER writer reaching the same file, or a symlink
# recreated by an older bootstrap path that was never fixed.
#
# Scans every clone under WORKSPACE_ROOT (the root clone itself + every .tabs/<N>/) for:
#   (a) cursor-configs/settings.json dirty in that clone's unified-trading-pm git tree — the team
#       SSOT should only ever change via a real commit, never an uncommitted local mutation.
#   (b) .claude/settings.local.json being a SYMLINK (should always be a real per-clone file, or
#       absent — never a link to anything).
# Absolute check (no ratchet/baseline): zero violations is the only correct state, unlike the
# corpus-content ratchets elsewhere in this sweep — this can never carry legitimate "pre-existing
# debt".
# Fail-open when WORKSPACE_ROOT / the .tabs layout doesn't exist (e.g. a CI runner, which has no
# per-tab-worktree filesystem shape at all) — nothing to check there.
# Usage: bash scripts/plan-hygiene/check_settings_symlink_hygiene.sh [--quiet]

set -uo pipefail
QUIET=0
for a in "$@"; do
  case "$a" in
    --quiet) QUIET=1 ;;
  esac
done

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$HOME/unified-trading-system-repos}"

if [ ! -d "$WORKSPACE_ROOT" ]; then
  [ "$QUIET" -eq 0 ] && echo "✅ check_settings_symlink_hygiene: WORKSPACE_ROOT ($WORKSPACE_ROOT) not present — nothing to check (e.g. CI runner)."
  exit 0
fi

CLONES=("$WORKSPACE_ROOT")
if [ -d "$WORKSPACE_ROOT/.tabs" ]; then
  while IFS= read -r d; do
    CLONES+=("$d")
  done < <(find "$WORKSPACE_ROOT/.tabs" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort -V)
fi

DIRTY_SETTINGS=()
SYMLINK_LOCAL=()

for clone in "${CLONES[@]}"; do
  pm_repo="$clone/unified-trading-pm"
  if [ -d "$pm_repo/.git" ] && [ -f "$pm_repo/cursor-configs/settings.json" ]; then
    if [ -n "$(git -C "$pm_repo" status --porcelain -- cursor-configs/settings.json 2>/dev/null)" ]; then
      DIRTY_SETTINGS+=("$clone")
    fi
  fi
  local_settings="$clone/.claude/settings.local.json"
  if [ -L "$local_settings" ]; then
    SYMLINK_LOCAL+=("$clone -> $(readlink "$local_settings")")
  fi
done

RC=0
if [ "${#DIRTY_SETTINGS[@]}" -gt 0 ]; then
  RC=1
  echo "❌ cursor-configs/settings.json dirty (uncommitted local mutation) in ${#DIRTY_SETTINGS[@]} clone(s):"
  printf '     %s\n' "${DIRTY_SETTINGS[@]}"
  echo "     Restore via: git -C <clone>/unified-trading-pm checkout -- cursor-configs/settings.json"
fi
if [ "${#SYMLINK_LOCAL[@]}" -gt 0 ]; then
  RC=1
  echo "❌ .claude/settings.local.json is a SYMLINK (must be a real per-clone file, never a link) in ${#SYMLINK_LOCAL[@]} clone(s):"
  printf '     %s\n' "${SYMLINK_LOCAL[@]}"
  echo "     Remove the symlink (rm <clone>/.claude/settings.local.json) — it will be recreated as a real file."
fi

if [ "$RC" -eq 0 ]; then
  [ "$QUIET" -eq 0 ] && echo "✅ check_settings_symlink_hygiene: ${#CLONES[@]} clone(s) checked — cursor-configs/settings.json clean everywhere, no settings.local.json symlinks."
fi

exit "$RC"
