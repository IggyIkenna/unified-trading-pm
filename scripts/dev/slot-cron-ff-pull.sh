#!/usr/bin/env bash
# slot-cron-ff-pull.sh — safe fast-forward-only puller for slot worktrees.
#
# Designed for cron (default cadence: every 15 minutes). For every repo worktree
# under the current slot dir (or all slots with --all-slots), this script:
#
#   1. Fetches origin/<integration-branch> (default: live-defi-rollout).
#   2. Skips the repo if working tree is DIRTY (any uncommitted change).
#   3. Skips the repo if local branch is AHEAD of remote (has unpushed commits —
#      i.e. the LOCAL tab branch has commits that aren't yet on `live-defi-rollout`).
#   4. Skips the repo if local + remote have DIVERGED (would need rebase/merge).
#   5. Otherwise (local strictly BEHIND remote): fast-forwards the local branch to
#      match origin/<integration-branch>. This is the only case where the script
#      mutates local state; FF-only never loses work.
#
# Never destructive. Never runs `merge --no-ff`, never `rebase`, never `reset --hard`.
# Exits 0 always (cron-safe). Per-repo status logged to stdout + the rotating log file.
#
# Usage:
#   slot-cron-ff-pull.sh                        # current slot, default branch
#   slot-cron-ff-pull.sh --all-slots            # every slot under .tabs/
#   slot-cron-ff-pull.sh --branch staging       # different integration branch
#   slot-cron-ff-pull.sh --quiet                # only print skips/FFs, not no-ops
#   slot-cron-ff-pull.sh --dry-run              # report what would FF; don't move refs
#
# Cron install (example, every 15 min):
#   crontab -e
#   */15 * * * * cd "${WORKSPACE_ROOT}/.tabs/1" && bash unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh --all-slots >> /tmp/slot-cron-ff-pull.log 2>&1
#
# Lock file at /tmp/slot-cron-ff-pull.lock prevents overlapping cron runs.
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md

set -euo pipefail

INTEGRATION_BRANCH="live-defi-rollout"
MODE="single-slot"
QUIET=0
DRY_RUN=0
LOCK_FILE="/tmp/slot-cron-ff-pull.lock"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --all-slots)    MODE="all-slots"; shift;;
        --branch)       INTEGRATION_BRANCH="$2"; shift 2;;
        --quiet)        QUIET=1; shift;;
        --dry-run)      DRY_RUN=1; shift;;
        -h|--help)
            sed -n '2,32p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0;;
        *)              echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

log()      { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
log_quiet(){ [[ "${QUIET}" -eq 0 ]] && log "$@" || true; }

# Acquire lock (skip silently if another instance is running).
exec 9>"${LOCK_FILE}"
if ! flock -n 9 2>/dev/null; then
    log_quiet "another instance is holding ${LOCK_FILE}; exiting."
    exit 0
fi

ff_one() {
    local repo_dir="$1"
    pushd "${repo_dir}" >/dev/null

    local repo_name branch local_sha remote_sha merge_base ahead behind
    repo_name=$(basename "${repo_dir}")
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "DETACHED")

    if [[ "${branch}" == "DETACHED" ]]; then
        log "[skip:detached] ${repo_name} — not on a branch"
        popd >/dev/null
        return 0
    fi

    # Step 1: dirty-tree check (any unstaged or staged change).
    if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
        log "[skip:dirty] ${repo_name} (${branch}) — uncommitted changes"
        popd >/dev/null
        return 0
    fi

    # Step 2: fetch (silent; skip on offline / no-such-ref).
    if ! git fetch --quiet origin "${INTEGRATION_BRANCH}" 2>/dev/null; then
        log "[skip:fetch-fail] ${repo_name} (${branch}) — fetch failed (offline? missing branch?)"
        popd >/dev/null
        return 0
    fi

    local_sha=$(git rev-parse HEAD)
    remote_sha=$(git rev-parse "origin/${INTEGRATION_BRANCH}")

    # Step 3: already up-to-date?
    if [[ "${local_sha}" == "${remote_sha}" ]]; then
        log_quiet "[ok:up-to-date] ${repo_name} (${branch})"
        popd >/dev/null
        return 0
    fi

    merge_base=$(git merge-base HEAD "origin/${INTEGRATION_BRANCH}" 2>/dev/null || echo "")

    if [[ -z "${merge_base}" ]]; then
        log "[skip:no-merge-base] ${repo_name} (${branch}) — branches unrelated"
        popd >/dev/null
        return 0
    fi

    # Step 4: ahead-only (local has unpushed commits, remote not advanced past us).
    if [[ "${merge_base}" == "${remote_sha}" && "${merge_base}" != "${local_sha}" ]]; then
        ahead=$(git rev-list --count "origin/${INTEGRATION_BRANCH}..HEAD")
        log "[skip:ahead] ${repo_name} (${branch}) — ${ahead} unpushed commit(s)"
        popd >/dev/null
        return 0
    fi

    # Step 5: diverged (both sides have unique commits).
    if [[ "${merge_base}" != "${remote_sha}" && "${merge_base}" != "${local_sha}" ]]; then
        ahead=$(git rev-list --count "origin/${INTEGRATION_BRANCH}..HEAD")
        behind=$(git rev-list --count "HEAD..origin/${INTEGRATION_BRANCH}")
        log "[skip:diverged] ${repo_name} (${branch}) — ahead ${ahead}, behind ${behind}; need manual rebase"
        popd >/dev/null
        return 0
    fi

    # Step 6: clean fast-forward (merge_base == local_sha, remote ahead).
    behind=$(git rev-list --count "HEAD..origin/${INTEGRATION_BRANCH}")
    if [[ "${DRY_RUN}" -eq 1 ]]; then
        log "[dry-run:ff] ${repo_name} (${branch}) — would FF by ${behind} commit(s) to ${remote_sha:0:8}"
    else
        if git merge --ff-only --quiet "origin/${INTEGRATION_BRANCH}" 2>/dev/null; then
            log "[ff] ${repo_name} (${branch}) — FF +${behind} → ${remote_sha:0:8}"
        else
            log "[skip:ff-failed] ${repo_name} (${branch}) — --ff-only refused; manual inspection needed"
        fi
    fi
    popd >/dev/null
    return 0
}

walk_slot() {
    # Walk every repo worktree under one slot dir.
    local slot_dir="$1"
    local count=0
    for d in "${slot_dir}"/*/; do
        [[ -d "${d}" ]] || continue
        # Repo if .git is dir or file (worktree).
        [[ -d "${d}.git" || -f "${d}.git" ]] || continue
        ff_one "${d}" || true
        count=$((count + 1))
    done
    log_quiet "slot ${slot_dir}: walked ${count} repo(s)"
}

# Resolve starting slot dir.
cwd="$(pwd)"
if [[ -f .git || -d .git ]]; then
    # Inside a per-repo worktree → climb to slot dir.
    cwd="$(cd .. && pwd)"
fi

if [[ "${MODE}" == "single-slot" ]]; then
    walk_slot "${cwd}"
else
    # --all-slots: cwd should be the .tabs/ parent OR any .tabs/N dir.
    # Find the .tabs/ root.
    tabs_root="${cwd}"
    while [[ "$(basename "${tabs_root}")" != ".tabs" && "${tabs_root}" != "/" ]]; do
        tabs_root="$(dirname "${tabs_root}")"
    done
    if [[ "${tabs_root}" == "/" ]]; then
        log "[err] --all-slots: not inside a .tabs/ tree (cwd=${cwd})"
        exit 0
    fi
    for slot in "${tabs_root}"/*/; do
        [[ -d "${slot}" ]] || continue
        log_quiet "=== slot $(basename "${slot}") ==="
        walk_slot "${slot}"
    done
fi
