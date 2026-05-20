#!/usr/bin/env bash
# slot-cron-ff-pull.sh — safe fast-forward-only puller for slot worktrees.
#
# Designed for cron (default cadence: every 5 minutes). For every repo worktree
# under the current slot dir (or all slots with --all-slots) PLUS the main
# (non-tabbed) workspace, this script:
#
#   1. PHASE 1 (sequential pre-fetch): from each MAIN-workspace full clone,
#      fetches origin/<integration-branch>. Linked worktrees (tabs) share refs,
#      so one fetch updates origin/<branch> for every slot that references that
#      repo. Cuts a 13-slot × 22-repo sweep from ~286 fetches to ~22.
#   2. PHASE 2 (parallel FF): fans out N workers (default 4). Each worker walks
#      its assigned slots and does FF-only merges using the pre-fetched refs
#      (no network). Per-worktree skips: dirty / ahead / diverged / detached.
#   3. Otherwise (local strictly BEHIND remote): fast-forwards the local branch
#      to match origin/<integration-branch>. This is the only case where the
#      script mutates local state; FF-only never loses work.
#
# Never destructive. Never runs `merge --no-ff`, never `rebase`, never `reset --hard`.
# Exits 0 always (cron-safe). Per-repo status logged to stdout + the rotating log file.
#
# Usage:
#   slot-cron-ff-pull.sh                        # current slot, default branch
#   slot-cron-ff-pull.sh --all-slots            # every slot under .tabs/ + main worktree
#   slot-cron-ff-pull.sh --branch staging       # different integration branch
#   slot-cron-ff-pull.sh --quiet                # only print skips/FFs, not no-ops
#   slot-cron-ff-pull.sh --dry-run              # report what would FF; don't move refs
#   slot-cron-ff-pull.sh --workers 8            # parallel workers (default 4)
#   slot-cron-ff-pull.sh --no-prefetch          # skip phase 1 (per-repo fetch in phase 2)
#
# Cron install (every 5 min):
#   */5 * * * * cd ${WORKSPACE_ROOT}/.tabs/1 && bash unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh --all-slots --quiet >> /tmp/slot-cron-ff-pull.log 2>&1
#
# Lock file at /tmp/slot-cron-ff-pull.lock prevents overlapping cron runs.
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md

set -euo pipefail

INTEGRATION_BRANCH="live-defi-rollout"
MODE="single-slot"
QUIET=0
DRY_RUN=0
PARALLEL_WORKERS="${SLOT_FF_PULL_WORKERS:-4}"
DO_PREFETCH=1
LOCK_FILE="/tmp/slot-cron-ff-pull.lock"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --all-slots)    MODE="all-slots"; shift;;
        --branch)       INTEGRATION_BRANCH="$2"; shift 2;;
        --quiet)        QUIET=1; shift;;
        --dry-run)      DRY_RUN=1; shift;;
        --workers)      PARALLEL_WORKERS="$2"; shift 2;;
        --no-prefetch)  DO_PREFETCH=0; shift;;
        -h|--help)
            sed -n '2,35p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
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
    local do_fetch="${2:-1}"
    pushd "${repo_dir}" >/dev/null

    local repo_name branch local_sha remote_sha merge_base ahead behind
    repo_name=$(basename "${repo_dir}")
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "DETACHED")

    if [[ "${branch}" == "DETACHED" || "${branch}" == "HEAD" ]]; then
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

    # Step 2: fetch only if not pre-fetched (silent; skip on offline / no-such-ref).
    if [[ "${do_fetch}" -eq 1 ]]; then
        if ! git fetch --quiet origin "${INTEGRATION_BRANCH}" 2>/dev/null; then
            log "[skip:fetch-fail] ${repo_name} (${branch}) — fetch failed (offline? missing branch?)"
            popd >/dev/null
            return 0
        fi
    fi

    local_sha=$(git rev-parse HEAD)
    remote_sha=$(git rev-parse "origin/${INTEGRATION_BRANCH}" 2>/dev/null || echo "")
    if [[ -z "${remote_sha}" ]]; then
        log "[skip:no-remote-ref] ${repo_name} (${branch}) — origin/${INTEGRATION_BRANCH} not in this worktree"
        popd >/dev/null
        return 0
    fi

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
    # Arg $2 (optional): 0 = skip per-repo fetch (use pre-fetched refs), 1 = fetch.
    local slot_dir="$1"
    local do_fetch="${2:-1}"
    local count=0
    for d in "${slot_dir}"/*/; do
        [[ -d "${d}" ]] || continue
        [[ -d "${d}.git" || -f "${d}.git" ]] || continue
        ff_one "${d}" "${do_fetch}" || true
        count=$((count + 1))
    done
    log_quiet "slot $(basename "${slot_dir}"): walked ${count} repo(s)"
}

# Export functions + vars for parallel worker subshells (& inherits these).
export -f ff_one walk_slot log log_quiet
export INTEGRATION_BRANCH QUIET DRY_RUN

prefetch_main_clones() {
    # Sequentially fetch origin/<branch> for every MAIN-workspace full clone.
    # Linked tab worktrees share .git/refs, so this updates origin/<branch>
    # for every slot at once. Skips dirs without .git/ (e.g. .tabs/, plans/, etc.).
    local main_ws="$1"
    local fetched=0
    local failed=0
    for d in "${main_ws}"/*/; do
        [[ -d "${d}.git" ]] || continue  # only main clones (file-.git = linked worktree)
        local repo_name
        repo_name=$(basename "${d}")
        if git -C "${d}" fetch --quiet origin "${INTEGRATION_BRANCH}" 2>/dev/null; then
            fetched=$((fetched + 1))
        else
            log "[prefetch-fail] ${repo_name} — fetch origin/${INTEGRATION_BRANCH} failed"
            failed=$((failed + 1))
        fi
    done
    log_quiet "prefetch: ${fetched} fetched, ${failed} failed"
}

# Resolve starting slot dir.
cwd="$(pwd)"
if [[ -f .git || -d .git ]]; then
    # Inside a per-repo worktree → climb to slot dir.
    cwd="$(cd .. && pwd)"
fi

if [[ "${MODE}" == "single-slot" ]]; then
    walk_slot "${cwd}" 1
    exit 0
fi

# --all-slots: find the .tabs/ root.
tabs_root="${cwd}"
while [[ "$(basename "${tabs_root}")" != ".tabs" && "${tabs_root}" != "/" ]]; do
    tabs_root="$(dirname "${tabs_root}")"
done
if [[ "${tabs_root}" == "/" ]]; then
    log "[err] --all-slots: not inside a .tabs/ tree (cwd=${cwd})"
    exit 0
fi
main_workspace="$(dirname "${tabs_root}")"

# PHASE 1: sequential pre-fetch (one fetch per unique repo, via main clones).
do_fetch_in_walk=1
if [[ "${DO_PREFETCH}" -eq 1 ]]; then
    log_quiet "=== phase 1: pre-fetch (sequential, main workspace clones) ==="
    prefetch_main_clones "${main_workspace}"
    do_fetch_in_walk=0
fi

# PHASE 2: collect slots (tabs + main workspace).
slots=()
for slot in "${tabs_root}"/*/; do
    [[ -d "${slot}" ]] || continue
    slots+=("${slot}")
done
slots+=("${main_workspace}")

log_quiet "=== phase 2: parallel FF (${PARALLEL_WORKERS} workers, ${#slots[@]} slots) ==="

# Round-robin assign slots to workers; each worker walks its slots sequentially.
declare -a worker_slots
for i in "${!slots[@]}"; do
    w=$(( i % PARALLEL_WORKERS ))
    worker_slots[$w]+="${slots[$i]}|"
done

pids=()
for w in $(seq 0 $((PARALLEL_WORKERS - 1))); do
    assigned="${worker_slots[$w]:-}"
    [[ -n "${assigned}" ]] || continue
    (
        IFS='|' read -r -a my_slots <<< "${assigned}"
        for slot in "${my_slots[@]}"; do
            [[ -n "${slot}" ]] || continue
            walk_slot "${slot}" "${do_fetch_in_walk}"
        done
    ) &
    pids+=("$!")
done

for pid in "${pids[@]}"; do
    wait "${pid}" || true
done

log_quiet "=== sweep complete ==="
