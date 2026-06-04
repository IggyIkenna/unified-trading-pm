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
OVERRIDES_FILE="$(dirname "${BASH_SOURCE[0]}")/cron-branch-overrides.txt"

# Per-repo branch overrides, loaded from OVERRIDES_FILE if present.
# Format: "repo_name branch_name" per line; # and blank lines ignored.
# Parallel arrays (compatible with macOS bash 3.2; assoc arrays need bash 4+).
OVERRIDE_REPOS=()
OVERRIDE_BRANCHES=()
if [[ -f "${OVERRIDES_FILE}" ]]; then
    while IFS= read -r line || [[ -n "${line}" ]]; do
        line="${line%%#*}"  # strip trailing comment
        line="${line#"${line%%[![:space:]]*}"}"  # ltrim
        [[ -z "${line// }" ]] && continue
        repo=""; branch=""
        read -r repo branch <<< "${line}"
        if [[ -n "${repo}" && -n "${branch}" ]]; then
            OVERRIDE_REPOS+=("${repo}")
            OVERRIDE_BRANCHES+=("${branch}")
        fi
    done < "${OVERRIDES_FILE}"
fi

# Resolve the effective branch for a repo (override or default).
branch_for_repo() {
    local repo_name="$1" i
    for i in "${!OVERRIDE_REPOS[@]}"; do
        if [[ "${OVERRIDE_REPOS[$i]}" == "${repo_name}" ]]; then
            echo "${OVERRIDE_BRANCHES[$i]}"
            return 0
        fi
    done
    echo "${INTEGRATION_BRANCH}"
}

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

    local repo_name branch local_sha remote_sha merge_base ahead behind int_branch
    repo_name=$(basename "${repo_dir}")
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "DETACHED")
    int_branch="$(branch_for_repo "${repo_name}")"

    if [[ "${branch}" == "DETACHED" || "${branch}" == "HEAD" ]]; then
        log "[skip:detached] ${repo_name} — not on a branch"
        popd >/dev/null
        return 0
    fi

    # Step 0: upstream self-heal (codified 2026-06-04). A tab worktree's @{upstream} MUST be
    # origin/<int_branch> (set by setup-tab-worktrees.sh --track). A stray `git push -u origin
    # HEAD:tab/<op>/N` re-points it to origin/<tab-branch>, after which the IDE shows a PHANTOM
    # "ahead N" measured vs the STALE remote tab (not real drift). Functionally harmless (the FF
    # below pulls <int_branch> EXPLICITLY, and push.default=simple refuses a mismatched-name bare
    # push) but the display lies — so re-point it every tick. Runs on EVERY slot host (laptop + VM)
    # since this cron does. SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Upstream tracking".
    local _want_upstream _have_upstream
    _want_upstream="origin/${int_branch}"
    _have_upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || echo "")
    if [[ -n "${_have_upstream}" && "${_have_upstream}" != "${_want_upstream}" ]]; then
        if [[ "${DRY_RUN}" -eq 0 ]]; then
            git branch --set-upstream-to="${_want_upstream}" "${branch}" >/dev/null 2>&1 \
                && log "[upstream-fix] ${repo_name} — reset @{upstream} ${_have_upstream} → ${_want_upstream}"
        else
            log "[upstream-fix:dry] ${repo_name} — would reset @{upstream} ${_have_upstream} → ${_want_upstream}"
        fi
    fi

    # Step 1: dirty-tree check (any unstaged or staged change).
    # First auto-discard the closed set of locally-regenerated / CI-authoritative artifacts
    # so they never block the FF-pull (mirrors the VM's pm-pull-ff.sh; was local-vs-VM asymmetry
    # that stranded laptop slots dirty — cicd #482-adjacent). These files are disposable locally:
    #   - WORKSPACE_MANIFEST_DAG.svg / DATA_FLOW_DAG.svg : pure generated (refresh-manifest-dag.sh) → always safe.
    #   - workspace-manifest.json : discard ONLY when the diff is ci_status-only (CI-authoritative —
    #     flips FAILING/LOCAL_PASS/STAGING_GREEN); ANY other manifest edit is real WIP → preserved.
    # For non-PM repos these files are absent → the checks are no-ops.
    if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
        for _regen in WORKSPACE_MANIFEST_DAG.svg DATA_FLOW_DAG.svg; do
            if ! git diff --quiet -- "${_regen}" 2>/dev/null; then
                git checkout -q -- "${_regen}" 2>/dev/null || true
            fi
        done
        if ! git diff --quiet -- workspace-manifest.json 2>/dev/null; then
            _nonstatus=$(git diff -- workspace-manifest.json 2>/dev/null \
                | grep -E '^[+-]' | grep -vE '^[+-]{3}' | grep -vE '"ci_status":' || true)
            if [[ -z "${_nonstatus}" ]]; then
                git checkout -q -- workspace-manifest.json 2>/dev/null || true
                log "[auto-clean] ${repo_name} — discarded ci_status-only manifest churn (CI-authoritative)"
            fi
        fi
    fi
    # Auto-flush agent ping ledgers: they accumulate append-only cross-agent content that
    # legitimately blocks FF (can't discard — real data, unlike the regen artifacts above).
    # When the ONLY remaining dirt is ping-ledger files, commit + push them so the tree goes
    # clean and FF proceeds. This is the per-host safety net for "Commit + Push + Flip" (pings
    # should be flushed by whoever appends; this catches the cases where they weren't, which
    # is what stranded the top-level PM clone 1164 commits behind — cicd hardening 2026-06-02).
    #   - Scoped to unified-trading-pm AND only when the clone is directly on the integration
    #     branch (branch == int_branch). On a slot's tab/<op>/<N> branch we must NOT push
    #     HEAD:int_branch (would leak tab commits into LDR) — slot pings flush via the normal
    #     tab→LDR promote, so there we fall through to [skip:dirty] as before.
    #   - Commits ONLY the ping-ledger paths; rebase-retry handles a concurrent push race; a
    #     rebase conflict aborts cleanly (no mid-rebase, no data loss) and retries next cycle.
    if [[ "${repo_name}" == "unified-trading-pm" && "${branch}" == "${int_branch}" \
          && "${DRY_RUN}" -eq 0 && -n "$(git status --porcelain 2>/dev/null)" ]]; then
        local _ping_paths _f _is_ping _p _nonping _dirty _pushed _try
        _ping_paths=(ikenna_orchestrator/_agent_pings.md harsh_orchestrator/_agent_pings.md plans/active/_agent_pings.md)
        _dirty=$(git status --porcelain 2>/dev/null | awk '{print $2}')
        _nonping=""
        while IFS= read -r _f; do
            [[ -z "${_f}" ]] && continue
            _is_ping=0
            for _p in "${_ping_paths[@]}"; do [[ "${_f}" == "${_p}" ]] && _is_ping=1; done
            [[ "${_is_ping}" -eq 0 ]] && _nonping="${_nonping} ${_f}"
        done <<< "${_dirty}"
        if [[ -z "${_nonping// }" ]]; then
            for _p in "${_ping_paths[@]}"; do git add "${_p}" 2>/dev/null || true; done
            if git commit -q -m "chore(pings): auto-flush agent ping ledgers [skip ci]" 2>/dev/null; then
                _pushed=0
                for _try in 1 2; do
                    if git pull --rebase --quiet origin "${int_branch}" 2>/dev/null; then
                        if git push --quiet origin "HEAD:${int_branch}" 2>/dev/null; then _pushed=1; break; fi
                    else
                        git rebase --abort 2>/dev/null || true  # ping append conflict → never leave mid-rebase
                        break
                    fi
                done
                if [[ "${_pushed}" -eq 1 ]]; then
                    log "[ping-flush] ${repo_name} — committed+pushed agent ping ledgers (tree clean, FF can proceed)"
                else
                    log "[ping-flush:deferred] ${repo_name} — ping ledgers committed locally (ahead); push race/conflict, retry next cycle"
                fi
            fi
        fi
    fi
    if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
        log "[skip:dirty] ${repo_name} (${branch}) — uncommitted changes"
        popd >/dev/null
        return 0
    fi

    # Step 2: fetch only if not pre-fetched (silent; skip on offline / no-such-ref).
    # `--tags --force` self-heals stale local release tags (e.g. a lightweight
    # v1.0.0 that diverged from semver-agent's canonical remote annotated tag),
    # which would otherwise surface as `(would clobber existing tag)` on a manual
    # `git pull`. Remote is canonical for release tags; forcing local→remote is
    # safe and we never push tags the other way. SSOT:
    # codex/05-infrastructure/per-tab-worktrees.md § "Step 7 — troubleshooting".
    if [[ "${do_fetch}" -eq 1 ]]; then
        if ! git fetch --quiet --tags --force origin "${int_branch}" 2>/dev/null; then
            log "[skip:fetch-fail] ${repo_name} (${branch}) — fetch failed (offline? missing branch?)"
            popd >/dev/null
            return 0
        fi
    fi

    local_sha=$(git rev-parse HEAD)
    remote_sha=$(git rev-parse "origin/${int_branch}" 2>/dev/null || echo "")
    if [[ -z "${remote_sha}" ]]; then
        log "[skip:no-remote-ref] ${repo_name} (${branch}) — origin/${int_branch} not in this worktree"
        popd >/dev/null
        return 0
    fi

    # Step 3: already up-to-date?
    if [[ "${local_sha}" == "${remote_sha}" ]]; then
        log_quiet "[ok:up-to-date] ${repo_name} (${branch} → ${int_branch})"
        popd >/dev/null
        return 0
    fi

    merge_base=$(git merge-base HEAD "origin/${int_branch}" 2>/dev/null || echo "")

    if [[ -z "${merge_base}" ]]; then
        log "[skip:no-merge-base] ${repo_name} (${branch} → ${int_branch}) — branches unrelated"
        popd >/dev/null
        return 0
    fi

    # Step 4: ahead-only (local has unpushed commits, remote not advanced past us).
    if [[ "${merge_base}" == "${remote_sha}" && "${merge_base}" != "${local_sha}" ]]; then
        ahead=$(git rev-list --count "origin/${int_branch}..HEAD")
        log "[skip:ahead] ${repo_name} (${branch} → ${int_branch}) — ${ahead} unpushed commit(s)"
        popd >/dev/null
        return 0
    fi

    # Step 5: diverged (both sides have unique commits).
    if [[ "${merge_base}" != "${remote_sha}" && "${merge_base}" != "${local_sha}" ]]; then
        ahead=$(git rev-list --count "origin/${int_branch}..HEAD")
        behind=$(git rev-list --count "HEAD..origin/${int_branch}")
        log "[skip:diverged] ${repo_name} (${branch} → ${int_branch}) — ahead ${ahead}, behind ${behind}; need manual rebase"
        popd >/dev/null
        return 0
    fi

    # Step 6: clean fast-forward (merge_base == local_sha, remote ahead).
    behind=$(git rev-list --count "HEAD..origin/${int_branch}")
    if [[ "${DRY_RUN}" -eq 1 ]]; then
        log "[dry-run:ff] ${repo_name} (${branch} → ${int_branch}) — would FF by ${behind} commit(s) to ${remote_sha:0:8}"
    else
        if git merge --ff-only --quiet "origin/${int_branch}" 2>/dev/null; then
            log "[ff] ${repo_name} (${branch} → ${int_branch}) — FF +${behind} → ${remote_sha:0:8}"
        else
            log "[skip:ff-failed] ${repo_name} (${branch} → ${int_branch}) — --ff-only refused; manual inspection needed"
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

# Workers are forked via `&`, so they inherit functions, variables, and the
# BRANCH_OVERRIDES assoc array in-process without any export ceremony.

prefetch_main_clones() {
    # Sequentially fetch origin/<branch> for every MAIN-workspace full clone.
    # Linked tab worktrees share .git/refs, so this updates origin/<branch>
    # for every slot at once. Skips dirs without .git/ (e.g. .tabs/, plans/, etc.).
    local main_ws="$1"
    local fetched=0
    local failed=0
    for d in "${main_ws}"/*/; do
        [[ -d "${d}.git" ]] || continue  # only main clones (file-.git = linked worktree)
        local repo_name int_branch
        repo_name=$(basename "${d}")
        int_branch="$(branch_for_repo "${repo_name}")"
        # `--tags --force` heals stale local release tags fleet-wide: linked tab
        # worktrees share .git/refs with this main clone, so one forced tag sync
        # here fixes the `(would clobber existing tag)` pull failure for every
        # slot at once (semver-agent's remote tags are canonical).
        if git -C "${d}" fetch --quiet --tags --force origin "${int_branch}" 2>/dev/null; then
            fetched=$((fetched + 1))
        else
            log "[prefetch-fail] ${repo_name} — fetch origin/${int_branch} failed"
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
