#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# check-slot-commit-identity.sh — per-host audit (and --fix) of slot·host commit identity.
#
# For the MAIN workspace repos + every `.tabs/<N>/<repo>` clone on THIS host, verify the
# effective `git config user.name` / `user.email` match the expected
# `<canon> [<label>·<host>]` identity — sharing the EXACT derivation the fail-closed
# pre-commit hook enforces (scripts/hooks/slot-identity-lib.sh; single SSOT, no duplicated
# sed). Exit non-zero on any drift so cron/CI can gate on it.
#
#   bash scripts/dev/check-slot-commit-identity.sh              # report drift, exit 1 if any
#   bash scripts/dev/check-slot-commit-identity.sh --fix        # stamp the expected identity
#   bash scripts/dev/check-slot-commit-identity.sh --slot 16    # audit ONE slot's clones only
#   bash scripts/dev/check-slot-commit-identity.sh --fix --slot 16   # (setup-tab-worktrees final step)
#
# --fix stamps worktree-aware: `git config extensions.worktreeConfig true` +
# `git config --worktree user.*` (plain `git config` fallback for full clones) — the same
# write the hook self-heals with, so checker and hook can never fight.
#
# Runnable on the planning VM, the human-planning VM, and operator laptops
# (ao_task_lifecycle plan Phase D, 2026-07-09).
# SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Commit attribution".
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "${PM_ROOT}/.." && pwd)}"
# Running from a SLOT's PM clone (…/.tabs/<N>/unified-trading-pm) must still audit
# the TRUE workspace root — ascend out of the .tabs/<N>/ layer when detected.
case "$WORKSPACE_ROOT" in
  */.tabs/[0-9]*) WORKSPACE_ROOT="$(cd "${WORKSPACE_ROOT}/../.." && pwd)" ;;
esac

# shellcheck source=scripts/hooks/slot-identity-lib.sh
. "${PM_ROOT}/scripts/hooks/slot-identity-lib.sh"

FIX=0
ONLY_SLOT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --fix) FIX=1 ;;
    --slot)
      shift
      ONLY_SLOT="${1:-}"
      ;;
    *)
      echo "unknown arg: $1 (usage: [--fix] [--slot N])" >&2
      exit 2
      ;;
  esac
  shift
done

drift=0
checked=0
fixed=0

check_repo() {
  local repo_dir="$1"
  # A SYMLINKED repo dir is not a real clone — stamping through it hits the SYMLINK
  # TARGET's config (live incident 2026-07-09: slot-10 carried symlinks to the main
  # workspace's PM/UAC/UTL clones, so the slot-10 stamp landed in the ROOT clones'
  # configs). Report + skip; the repair is re-provisioning the slot with real
  # Path-B clones (setup-tab-worktrees.sh --add-slot N after removing the links).
  if [ -L "${repo_dir}" ]; then
    echo "SKIP   ${repo_dir} (symlinked repo dir → $(readlink "${repo_dir}") — not a real slot clone; re-provision)"
    return 0
  fi
  [ -e "${repo_dir}/.git" ] || return 0
  checked=$((checked + 1))

  slot_identity_resolve "$repo_dir"
  local exp_name="$SLOT_ID_EXPECTED_NAME"
  local exp_email="$SLOT_ID_CANON_EMAIL"

  local cur_name cur_email
  cur_name="$(git -C "$repo_dir" config user.name 2>/dev/null || echo '')"
  cur_email="$(git -C "$repo_dir" config user.email 2>/dev/null || echo '')"

  if [ "$cur_name" = "$exp_name" ] && [ "$cur_email" = "$exp_email" ]; then
    return 0
  fi

  if [ "$FIX" = 1 ]; then
    git -C "$repo_dir" config extensions.worktreeConfig true 2>/dev/null || true
    git -C "$repo_dir" config --worktree user.name "$exp_name" 2>/dev/null \
      || git -C "$repo_dir" config user.name "$exp_name"
    git -C "$repo_dir" config --worktree user.email "$exp_email" 2>/dev/null \
      || git -C "$repo_dir" config user.email "$exp_email"
    fixed=$((fixed + 1))
    echo "FIXED  ${repo_dir}"
    echo "       was: '${cur_name} <${cur_email}>'"
    echo "       now: '${exp_name} <${exp_email}>'"
  else
    drift=$((drift + 1))
    echo "DRIFT  ${repo_dir}"
    echo "       have: '${cur_name} <${cur_email}>'"
    echo "       want: '${exp_name} <${exp_email}>'"
  fi
}

if [ -n "$ONLY_SLOT" ]; then
  # Single-slot mode (setup-tab-worktrees final step; idempotent re-run covers a
  # partial slot — repos added later to an existing slot dir get stamped too).
  for repo_dir in "${WORKSPACE_ROOT}/.tabs/${ONLY_SLOT}"/*/; do
    check_repo "${repo_dir%/}"
  done
else
  # Main workspace repos (label resolves to "main").
  for repo_dir in "${WORKSPACE_ROOT}"/*/; do
    check_repo "${repo_dir%/}"
  done

  # Per-slot clones: .tabs/<N>/<repo> (label resolves to "slot-N").
  if [ -d "${WORKSPACE_ROOT}/.tabs" ]; then
    for slot_dir in "${WORKSPACE_ROOT}"/.tabs/*/; do
      for repo_dir in "${slot_dir}"*/; do
        check_repo "${repo_dir%/}"
      done
    done
  fi
fi

echo ""
echo "checked=${checked} drift=${drift} fixed=${fixed} host=${SLOT_ID_HOST:-?} canon=${SLOT_ID_CANON_NAME:-?}"
if [ "$FIX" = 0 ] && [ "$drift" -gt 0 ]; then
  echo "❌ ${drift} repo(s) carry a wrong commit identity — run with --fix to stamp."
  exit 1
fi
echo "✅ slot·host commit identity consistent on this host."
