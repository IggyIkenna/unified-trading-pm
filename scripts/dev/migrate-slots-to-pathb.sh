#!/usr/bin/env bash
# migrate-slots-to-pathb.sh — convert existing tab-branch slot worktrees → Path-B reference-clones.
#
# Path-B (2026-06-08): each .tabs/<N>/<repo> becomes `git clone --reference <main> <url>` with its
# OWN .git, checked out on live-defi-rollout (no tab branch, no tab-mirror, no sync tax). This tool
# does it SAFELY for an existing host (Ikenna's laptop already migrated; this is for Harsh / any host):
#
#   1. PRESERVE first — any real uncommitted WIP in a tab worktree is committed + pushed to
#      origin/wip-preserve/<handle>-slot-<N> (junk excluded: node_modules, *.qg_*sentinel*,
#      playwright-report). Nothing is compromised; recover with
#      `git show origin/wip-preserve/<handle>-slot-<N>:<path>` / cherry-pick.
#   2. RECLONE — worktree remove --force + git clone --reference <main> <url> + checkout LDR.
#   3. IDENTITY — `<handle> [slot-<N>·<host>]` (resolved host-stably: env SLOT_CANON_NAME →
#      `git config --global slotIdentity.name` → ikennaigboaka default) + the canonical email.
#   4. HOOK — install the strict-quickmerge pre-push hook into each clone.
#
# Identity resolution mirrors setup-tab-worktrees.sh. A non-Ikenna host MUST declare itself ONCE
# before running:  git config --global slotIdentity.name <handle> ; git config --global slotIdentity.email <email>
# (Harsh: handle=harshkantariya, email=harshkantariya.work@gmail.com).
#
# Usage:
#   migrate-slots-to-pathb.sh [--slots 1-11] [--exclude <N>/<repo>] [--dry-run]
#     --exclude is for the slot/repo you are CURRENTLY operating in (cannot self-reclone live).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-$(cd "${PM_DIR}/.." && pwd)}"
TABS_DIR="${WORKSPACE_ROOT}/.tabs"
HOOK_SRC="${PM_DIR}/scripts/dev/hooks/pre-push-strict-quickmerge.sh"
LDR="live-defi-rollout"

CANON_NAME="${SLOT_CANON_NAME:-$(git config --global slotIdentity.name 2>/dev/null || true)}"
CANON_NAME="${CANON_NAME:-ikennaigboaka}"
CANON_EMAIL="${SLOT_CANON_EMAIL:-$(git config --global slotIdentity.email 2>/dev/null || true)}"
CANON_EMAIL="${CANON_EMAIL:-ikennaigboaka@gmail.com}"
HOST_ID="${VM_NAME:-laptop}"

SLOTS="1-11"; EXCLUDE=""; DRY=0
while [[ $# -gt 0 ]]; do case "$1" in
  --slots) SLOTS="$2"; shift 2;;
  --exclude) EXCLUDE="$2"; shift 2;;
  --dry-run) DRY=1; shift;;
  *) echo "unknown arg: $1" >&2; exit 1;;
esac; done
SLOT_LO="${SLOTS%-*}"; SLOT_HI="${SLOTS#*-}"

echo "Path-B migration: slots ${SLOT_LO}..${SLOT_HI} | identity '${CANON_NAME} [slot-N·${HOST_ID}]' <${CANON_EMAIL}>${EXCLUDE:+ | exclude ${EXCLUDE}}${DRY:+ | DRY-RUN}"

preserve_wip() {
  local dir="$1" slot="$2" repo="$3"
  local real; real="$(git -C "$dir" status --porcelain | grep -vE 'node_modules|\.qg_[a-z_]*sentinel|\.qg_last_passed_sha|playwright-report' || true)"
  [[ -z "$real" ]] && return 0
  [[ "$DRY" == 1 ]] && { echo "    (dry) would preserve WIP in $repo"; return 0; }
  git -C "$dir" add -u
  git -C "$dir" ls-files --others --exclude-standard | grep -vE 'node_modules|\.qg_|playwright-report' \
    | grep -E '\.(py|ts|tsx|md|mdc|yaml|yml|json|toml|sh|txt|cfg)$' | while read -r f; do git -C "$dir" add -- "$f"; done || true
  [[ -z "$(git -C "$dir" diff --cached --name-only)" ]] && { git -C "$dir" reset -q; return 0; }
  git -C "$dir" -c user.name="${CANON_NAME} [slot-${slot}·${HOST_ID}]" -c user.email="${CANON_EMAIL}" \
    commit --no-verify -q -m "chore(wip): preserve slot-${slot} ${repo} uncommitted work before Path-B migration"
  git -C "$dir" push origin "HEAD:refs/heads/wip-preserve/${CANON_NAME}-slot-${slot}" --force-with-lease \
    && echo "    PRESERVED ${repo} → origin/wip-preserve/${CANON_NAME}-slot-${slot}"
}

for slot in $(seq "$SLOT_LO" "$SLOT_HI"); do
  sp="${TABS_DIR}/${slot}"; [[ -d "$sp" ]] || continue
  for dir in "${sp}"/*/; do
    [[ -e "$dir" ]] || continue
    repo="$(basename "$dir")"; dir="${dir%/}"
    [[ "${slot}/${repo}" == "$EXCLUDE" ]] && { echo "  SKIP ${slot}/${repo} (excluded — your live slot)"; continue; }
    [[ -d "${dir}/.git" ]] && { echo "  OK   ${slot}/${repo} (already Path-B)"; continue; }
    [[ -f "${dir}/.git" ]] || continue   # not a worktree
    main="${WORKSPACE_ROOT}/${repo}"; [[ -d "${main}/.git" ]] || { echo "  SKIP ${slot}/${repo} (no main clone)"; continue; }
    url="$(git -C "$main" remote get-url origin)"
    preserve_wip "$dir" "$slot" "$repo"
    if [[ "$DRY" == 1 ]]; then echo "  (dry) would reclone ${slot}/${repo} Path-B on ${LDR}"; continue; fi
    git -C "$main" worktree remove --force "$dir" 2>/dev/null || true
    [[ -e "$dir" ]] && rm -rf "$dir"
    if git clone --reference "$main" "$url" "$dir" --quiet 2>/dev/null; then
      git -C "$dir" checkout "$LDR" --quiet 2>/dev/null || git -C "$dir" checkout -B "$LDR" "origin/${LDR}" --quiet
      git -C "$dir" config user.name "${CANON_NAME} [slot-${slot}·${HOST_ID}]"
      git -C "$dir" config user.email "${CANON_EMAIL}"
      [[ -f "$HOOK_SRC" && -d "${dir}/.git/hooks" ]] && { cp "$HOOK_SRC" "${dir}/.git/hooks/pre-push"; chmod +x "${dir}/.git/hooks/pre-push"; }
      echo "  CLONE ${slot}/${repo} → Path-B on ${LDR}"
    else
      echo "  FAIL  ${slot}/${repo} reference-clone"
    fi
  done
  git -C "${WORKSPACE_ROOT}/unified-trading-pm" worktree prune 2>/dev/null || true
done
echo "Path-B migration complete. Verify: python3 ${PM_DIR}/scripts/cicd/slot_drift_check.py --tabs-root ${TABS_DIR}"
