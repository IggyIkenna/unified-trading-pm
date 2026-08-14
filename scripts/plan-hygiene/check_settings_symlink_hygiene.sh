#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# check_settings_symlink_hygiene.sh — fleet-wide guard for the two symptoms of
# claude_settings_symlink_writeback_drops_hooks_2026_08_11.md.
#
# link-claude-skills.sh's block (4.5) now REFUSES to rewrite a symlinked
# .claude/settings.local.json (the guard applied 2026-08-11), but that guard only
# covers that ONE writer. Any OTHER script/manual step that reintroduces a
# settings.local.json -> cursor-configs/settings.json symlink, or otherwise dirties
# the git-tracked team SSOT (cursor-configs/settings.json) in a clone, would silently
# reach the same failure: a mechanism that can delete a hook registration from the
# team file (hooks are the ONLY surviving guardrail under bypassPermissions — see the
# issue doc). This check catches BOTH symptoms across every clone on the host:
#
#   1. <root>/.claude/settings.local.json is a SYMLINK (must be a real per-clone file
#      — settings.local.json is personal, gitignored, and must never link to anything,
#      let alone the team SSOT).
#   2. <root>/unified-trading-pm/cursor-configs/settings.json is DIRTY (uncommitted
#      changes to the git-tracked team file in that clone, from any source).
#
# "Root" = the true workspace root (the dir containing .tabs/) AND every .tabs/<N>/
# slot dir — the same two shapes link-claude-skills.sh's own WORKSPACE_ROOT arg
# accepts (see its header + _is_true_workspace_root()).
#
# Soft check — exit 0 always (informational, matches check_claude_subagent_parity.sh's
# precedent for a fleet-wide non-per-plan tripwire); exit 1 only on script error.
# Usage: bash scripts/plan-hygiene/check_settings_symlink_hygiene.sh [--quiet]

set -uo pipefail
QUIET="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Climb from PM_DIR's parent until we find a dir containing .tabs/ — that's the true
# workspace root whether PM_DIR itself is the root clone (parent already has .tabs/)
# or a slot clone (.tabs/<N>/unified-trading-pm — one more level up has .tabs/).
find_workspace_root() {
  local d
  d="$(dirname "$PM_DIR")"
  while [[ "$d" != "/" ]]; do
    if [[ -d "$d/.tabs" ]]; then
      printf '%s\n' "$d"
      return 0
    fi
    d="$(dirname "$d")"
  done
  return 1
}

WORKSPACE_ROOT="$(find_workspace_root)" || {
  echo "check_settings_symlink_hygiene: could not locate workspace root (no .tabs/ found climbing from ${PM_DIR})" >&2
  exit 1
}

ROOTS=("$WORKSPACE_ROOT")
for _slot_dir in "$WORKSPACE_ROOT"/.tabs/*/; do
  [[ -d "$_slot_dir" ]] || continue
  _slot_id="$(basename "$_slot_dir")"
  [[ "$_slot_id" =~ ^[0-9]+$ ]] || continue
  ROOTS+=("${_slot_dir%/}")
done

SYMLINK_HITS=""
DIRTY_HITS=""
CHECKED=0

for _root in "${ROOTS[@]}"; do
  CHECKED=$(( CHECKED + 1 ))

  _local_settings="$_root/.claude/settings.local.json"
  if [[ -L "$_local_settings" ]]; then
    SYMLINK_HITS="${SYMLINK_HITS}  SYMLINK  ${_local_settings} -> $(readlink "$_local_settings")"$'\n'
  fi

  _pm_clone="$_root/unified-trading-pm"
  if [[ -d "$_pm_clone/.git" || -f "$_pm_clone/.git" ]]; then
    _porcelain="$(git -C "$_pm_clone" status --porcelain -- cursor-configs/settings.json 2>/dev/null || true)"
    if [[ -n "$_porcelain" ]]; then
      DIRTY_HITS="${DIRTY_HITS}  DIRTY    ${_pm_clone}/cursor-configs/settings.json (${_porcelain})"$'\n'
    fi
  fi
done

if [[ "$QUIET" != "--quiet" ]]; then
  echo "Settings symlink/dirty hygiene (${CHECKED} clone root(s) checked):"
  echo ""
fi

TOTAL_HITS=0
if [[ -n "$SYMLINK_HITS" ]]; then
  printf '%s' "$SYMLINK_HITS"
  TOTAL_HITS=$(( TOTAL_HITS + $(printf '%s' "$SYMLINK_HITS" | grep -c '^') ))
fi
if [[ -n "$DIRTY_HITS" ]]; then
  printf '%s' "$DIRTY_HITS"
  TOTAL_HITS=$(( TOTAL_HITS + $(printf '%s' "$DIRTY_HITS" | grep -c '^') ))
fi

if [[ "$TOTAL_HITS" -gt 0 ]]; then
  echo ""
  echo "⚠️  check_settings_symlink_hygiene: ${TOTAL_HITS} hit(s) — settings.local.json must be a real per-clone file, and cursor-configs/settings.json must stay clean (see plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md)"
else
  [[ "$QUIET" != "--quiet" ]] && echo "✅ check_settings_symlink_hygiene: no symlinked settings.local.json, no dirty cursor-configs/settings.json (${CHECKED} clone(s), soft check)"
fi

exit 0
