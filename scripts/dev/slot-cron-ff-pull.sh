#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# slot-cron-ff-pull.sh — safe fast-forward-only puller for slot worktrees.
#
# Designed for cron (default cadence: every 5 minutes). For every repo worktree
# under the current slot dir (or all slots with --all-slots) PLUS the main
# (non-tabbed) workspace, this script:
#
#   1. PHASE 1 (sequential pre-fetch): from each MAIN-workspace full clone,
#      fetches origin/<integration-branch>. This puts the latest objects in the
#      shared store ONCE per repo (~22 network fetches, not 13×22≈286).
#   2. PHASE 2 (parallel FF): fans out N workers (default 4). Each worker walks
#      its assigned slots and FF-only merges. Per-worktree refs are refreshed
#      cheaply: Path-B slot clones (own .git dir + --reference alternates) get a
#      LOCAL ref-copy from the main clone (objects already shared → no network);
#      legacy linked worktrees (.git FILE) share the main clone's refs directly.
#      Skips: dirty / ahead / diverged / detached.
#      NOTE (Path-B, 2026-06-08): slots are independent clones with their OWN
#      refs — PHASE-1 alone does NOT advance them, so PHASE 2 MUST refresh each
#      slot's origin/<branch> (the prior shared-ref assumption silently stranded
#      slots behind; fixed 2026-06-12 via _refresh_independent_clone_ref).
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
# Lock file at ${XDG_RUNTIME_DIR:-/tmp}/slot-cron-ff-pull.$(id -u).lock prevents overlapping cron
# runs (per-uid so a root run and an ubuntu run never collide on the same lock).
#
# Per-repo min-interval throttle (widen-pm-cron-cadence_2026_07_27, cron-repo-min-interval.txt,
# same directory/format as cron-branch-overrides.txt: "repo_name seconds" per line, # and blank
# lines ignored). This cron's whole job is keeping an otherwise-IDLE repo from going stale —
# a repo under constant active shipping (PM specifically) already gets that from its own commit
# traffic, so running the full FF-pull dance on it every single tick is pure extra git-state
# churn on an already-busy repo, not additional freshness. State is a per-clone-identity temp
# file (mirrors the dirty-streak gate's own repo_key convention below), so throttling one slot's
# clone never affects another slot's clone of the same repo name.
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md

set -euo pipefail

INTEGRATION_BRANCH="live-defi-rollout"
MODE="single-slot"
QUIET=0
DRY_RUN=0
PARALLEL_WORKERS="${SLOT_FF_PULL_WORKERS:-4}"
DO_PREFETCH=1
LOCK_FILE="${SLOT_FF_PULL_LOCK_FILE:-${XDG_RUNTIME_DIR:-/tmp}/slot-cron-ff-pull.$(id -u).lock}"
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

# Per-repo min-interval throttle config (widen-pm-cron-cadence_2026_07_27) — same
# directory/format/parsing shape as the branch-overrides file above, deliberately, so both
# configs stay discoverable together. "repo_name seconds" per line; a repo with no entry
# here has 0 = never throttled (today's default for everything except the operator-set entry).
MIN_INTERVAL_FILE="$(dirname "${BASH_SOURCE[0]}")/cron-repo-min-interval.txt"
MIN_INTERVAL_REPOS=()
MIN_INTERVAL_SECONDS=()
if [[ -f "${MIN_INTERVAL_FILE}" ]]; then
    while IFS= read -r line || [[ -n "${line}" ]]; do
        line="${line%%#*}"
        line="${line#"${line%%[![:space:]]*}"}"
        [[ -z "${line// }" ]] && continue
        repo=""; secs=""
        read -r repo secs <<< "${line}"
        if [[ -n "${repo}" && -n "${secs}" ]]; then
            MIN_INTERVAL_REPOS+=("${repo}")
            MIN_INTERVAL_SECONDS+=("${secs}")
        fi
    done < "${MIN_INTERVAL_FILE}"
fi

min_interval_for_repo() {
    local repo_name="$1" i
    for i in "${!MIN_INTERVAL_REPOS[@]}"; do
        if [[ "${MIN_INTERVAL_REPOS[$i]}" == "${repo_name}" ]]; then
            echo "${MIN_INTERVAL_SECONDS[$i]}"
            return 0
        fi
    done
    echo "0"
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
#
# SLOT_CRON_FF_PULL_LIB_ONLY=1 skips the lock entirely, for tests that SOURCE this file to unit-
# test its helpers. Every function the tests need is defined below this point, so any usable
# prefix necessarily includes this block — and at source time the lock is normally already held
# by the real */5 cron, so sourcing hit `exit 0` before defining anything. That made two unit
# tests fail depending on whether a cron tick happened to be in flight: green on a quiet machine,
# red on a busy one, and never pointing at the lock as the reason.
#
# This does NOT weaken the guard for real runs: lib-only mode is opt-in via an env var that
# nothing but the test harness sets, and it skips only the lock, never any logic under test.
if [[ "${SLOT_CRON_FF_PULL_LIB_ONLY:-0}" != "1" ]]; then
    exec 9>"${LOCK_FILE}"
    if ! flock -n 9 2>/dev/null; then
        log_quiet "another instance is holding ${LOCK_FILE}; exiting."
        exit 0
    fi
fi

# Cron-liveness result file (fleet_git_health_orchestrator_2026_06_10.md Phase 3).
# Each sweep records its worst per-repo outcome + run timestamp here; the per-slot
# reporter (slot-git-status-report.sh) reads it and attests ff_pull_last_run /
# ff_pull_last_result on its POST so the orchestrator can flag a dead FF-pull cron
# (ff_cron_stale) as a first-class fleet state. Host-global (one FF-pull cron per
# host covers every slot). Tokens collect to a temp file (single-line appends are
# atomic across the parallel workers); aggregated worst-of at sweep end.
FF_RESULT_FILE="${SLOT_FF_PULL_RESULT_FILE:-${TMPDIR:-/tmp}/slot-cron-ff-pull.result.json}"
FF_TOKENS_FILE="$(mktemp -t ffpulltokens.XXXXXX 2>/dev/null || echo "${TMPDIR:-/tmp}/ffpulltokens.$$")"
# Per-repo dirty/clean observations for THIS sweep (cross_repo_dirty_gate_contamination
# fix, below) — a SEPARATE file from FF_TOKENS_FILE (which stays the host/sweep-wide
# outcome list, unchanged) because the per-repo confirm-gate needs to know which SPECIFIC
# repo produced which observation, not just the sweep's worst-of.
FF_REPO_TICKS_FILE="$(mktemp -t ffpullrepoticks.XXXXXX 2>/dev/null || echo "${TMPDIR:-/tmp}/ffpullrepoticks.$$")"
trap 'rm -f "${FF_TOKENS_FILE}" "${FF_REPO_TICKS_FILE}" 2>/dev/null || true' EXIT
# Consecutive-dirty alert (plan L1603): emit [WARN:dirty-streak-N] when every repo
# in the sweep has been [skip:dirty] for ≥ this many consecutive cron ticks.
FF_DIRTY_STREAK_THRESHOLD="${FF_DIRTY_STREAK_THRESHOLD:-3}"

# Record one per-repo outcome token: ok | skip:dirty | conflict | fail.
_ff_record() { printf '%s\n' "$1" >> "${FF_TOKENS_FILE}" 2>/dev/null || true; }

# Record THIS repo's own dirty/clean observation for the current tick, keyed by repo_key
# (see ff_one() — the repo's own resolved absolute path, so two DIFFERENT repos sharing the
# same basename across different slots/clones — e.g. every slot's "unified-trading-pm" —
# never collide). "dirty" = tracked dirt seen this tick (whether confirmed or not yet);
# "clean" = dirty-checked this tick and had none. A repo that never reaches the dirty check
# this tick (e.g. [skip:detached]) records nothing and simply carries its prior streak
# forward unchanged at merge time (_write_ff_result).
_record_repo_dirty_state() { printf '%s\t%s\n' "$1" "$2" >> "${FF_REPO_TICKS_FILE}" 2>/dev/null || true; }

# Single-source-of-truth dirt filter (ao_remediation_b_code_chain_2026_07_23.md item 3;
# mirrors slot-git-status-report.sh's classify_repo() fix, item 1). This cron computes
# dirt with the exact same `git status --porcelain` pattern as the reporter, so it is
# equally exposed to whatever phantom mechanism can inject a stray blank byte into the
# capture even on a genuinely clean tree — the reporter's bug was trusting a count
# independent of what a line-by-line pass actually kept; the parallel risk here is
# trusting raw byte-non-emptiness (`[[ -n "$capture" ]]`) instead of whether the capture
# contains any REAL (non-blank) line. Never gate on the raw capture directly — always
# filter first and gate on that, so a phantom blank byte can never trip [skip:dirty] and
# starve FF-pull. Pure (no I/O, no globals) — echoes only the kept non-blank lines.
_filter_nonblank_porcelain() {
    local raw="$1" line
    while IFS= read -r line; do
        [[ -z "${line}" ]] && continue
        printf '%s\n' "${line}"
    done <<< "${raw}"
}

# Read the sweep/host-wide aggregate dirty_consecutive_ticks field out of a result-file
# JSON (0 if the file is absent/unparseable). This is a COARSE, ACROSS-ALL-REPOS signal —
# consumed by slot-git-status-report.sh, which forwards it to agent-orchestrator's
# git_health.py as an independent cross-check against that server's OWN per-repo
# not_clean_since streak (ao_remediation_b_code_chain_2026_07_23.md item 4; deliberately
# NOT a per-repo counter for that consumer — see the plan's 2026-07-24 Progress Log entry).
# _write_ff_result below still maintains this field exactly as before. It is NOT what
# ff_one()'s own confirm-gate reads any more — see _read_repo_dirty_ticks for that.
_read_dirty_consecutive_ticks() {
    local f="$1"
    if [[ -s "${f}" ]]; then
        python3 -c "
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    print(int(d.get('dirty_consecutive_ticks', 0)))
except Exception:
    print(0)
" "${f}" 2>/dev/null || echo 0
    else
        echo 0
    fi
}

# Read ONE repo's OWN dirty_consecutive_ticks out of the result-file JSON's per-repo map
# (0 if the file/repo/field is absent or unparseable). This is the per-repo counterpart of
# _read_dirty_consecutive_ticks's host-wide aggregate above: ff_one()'s confirm-gate reads
# THIS, keyed by the repo's own resolved path (repo_key in ff_one()), so one repo's already-
# confirmed dirty streak can never be misread as another, unrelated repo's streak (the
# cross-repo FF-pull starvation bug: a --all-slots sweep walks every repo on the host in ONE
# pass, so a single shared/aggregate counter meant repo X's confirmed skip:dirty silently
# confirmed repo Y's genuinely-first dirty tick too, reintroducing the exact starvation class
# the confirm-gate (item 5) was built to prevent). FF_RESULT_FILE is read-only for the
# duration of a sweep (only _write_ff_result, run once at sweep end, mutates it), so this is
# safe to call per-repo, including from parallel forked --all-slots workers.
_read_repo_dirty_ticks() {
    local f="$1" repo_key="$2"
    if [[ -s "${f}" ]]; then
        python3 -c "
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    print(int(d.get('repo_dirty_ticks', {}).get(sys.argv[2], 0)))
except Exception:
    print(0)
" "${f}" "${repo_key}" 2>/dev/null || echo 0
    else
        echo 0
    fi
}

# Aggregate the run's worst outcome + write the result file atomically (tmp+mv).
# Worst-of precedence: conflict > fail > skip:dirty > dirty:unconfirmed > ok (an empty
# run = ok, the cron ran and had nothing stuck).
_write_ff_result() {
    local worst="ok" now tmp prev_ticks new_ticks
    if [[ -s "${FF_TOKENS_FILE}" ]]; then
        if grep -q '^conflict$' "${FF_TOKENS_FILE}" 2>/dev/null; then
            worst="conflict"
        elif grep -q '^fail$' "${FF_TOKENS_FILE}" 2>/dev/null; then
            worst="fail"
        elif grep -q '^skip:dirty$' "${FF_TOKENS_FILE}" 2>/dev/null; then
            worst="skip:dirty"
        elif grep -q '^dirty:unconfirmed$' "${FF_TOKENS_FILE}" 2>/dev/null; then
            worst="dirty:unconfirmed"
        fi
    fi
    # Consecutive-dirty-tick counter (plan L1603) — the host/sweep-wide AGGREGATE, kept
    # bit-for-bit as before (see _read_dirty_consecutive_ticks's comment: this feeds the
    # reporter's cross-check + the [WARN] streak line, not ff_one()'s own gate any more).
    # Read the previous count, increment when this sweep saw ANY dirt (confirmed skip:dirty
    # OR a not-yet-confirmed single tick — both need the streak to climb so a second
    # consecutive tick can confirm, ao_remediation_b_code_chain_2026_07_23.md item 5), reset
    # otherwise. Emit a visible [WARN] line when the streak reaches the threshold so
    # operators / log monitors see the stale-WIP signal.
    prev_ticks="$(_read_dirty_consecutive_ticks "${FF_RESULT_FILE}")"
    if [[ "${worst}" == "skip:dirty" || "${worst}" == "dirty:unconfirmed" ]]; then
        new_ticks=$(( prev_ticks + 1 ))
        if [[ "${worst}" == "skip:dirty" && "${new_ticks}" -ge "${FF_DIRTY_STREAK_THRESHOLD}" ]]; then
            log "[WARN:dirty-streak-${new_ticks}] ff-pull has skipped ${new_ticks} consecutive tick(s) (skip:dirty) — uncommitted WIP is blocking integration-branch updates. Investigate: git -C <repo> status && git diff --stat"
        fi
    else
        new_ticks=0
    fi
    now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    tmp="$(mktemp -t ffpullresult.XXXXXX 2>/dev/null || echo "${FF_RESULT_FILE}.tmp.$$")"
    # Per-repo confirm-gate streak (cross-repo starvation fix, above): merge THIS sweep's
    # per-repo dirty/clean observations (FF_REPO_TICKS_FILE) into the PRIOR per-repo map, so
    # a repo never even dirty-checked this tick (e.g. [skip:detached]) keeps its last-known
    # streak untouched, a repo observed dirty this tick increments its OWN counter, and a
    # repo observed clean resets its OWN counter — all independent of every OTHER repo in
    # the sweep. Done in python3 (already a hard dependency here) rather than reinventing a
    # JSON merge in bash. Falls back to the plain (no per-repo map) JSON on any python3
    # failure so a bug here can never jam the cron (mirrors every other `|| true` in this
    # file).
    if ! python3 -c "
import json, sys

result_path, repo_ticks_path, now, worst, new_ticks, out_path = sys.argv[1:7]
try:
    prev = json.load(open(result_path))
except Exception:
    prev = {}
repo_map = dict(prev.get('repo_dirty_ticks', {}))
try:
    with open(repo_ticks_path) as fh:
        lines = fh.read().splitlines()
except Exception:
    lines = []
for line in lines:
    if '\t' not in line:
        continue
    repo, state = line.split('\t', 1)
    if state == 'dirty':
        repo_map[repo] = int(repo_map.get(repo, 0)) + 1
    else:
        repo_map[repo] = 0
out = {
    'ff_pull_last_run': now,
    'ff_pull_last_result': worst,
    'dirty_consecutive_ticks': int(new_ticks),
    'repo_dirty_ticks': repo_map,
}
# Compact separators (no space after ':'/',') to byte-match the hand-rolled printf format
# this replaces — consumers (this file's own tests, slot-git-status-report.sh) substring-
# match on e.g. '\"ff_pull_last_result\":\"ok\"', which json.dump's default spaced
# separators would silently break.
with open(out_path, 'w') as fh:
    json.dump(out, fh, separators=(',', ':'))
" "${FF_RESULT_FILE}" "${FF_REPO_TICKS_FILE}" "${now}" "${worst}" "${new_ticks}" "${tmp}" 2>/dev/null; then
        printf '{"ff_pull_last_run":"%s","ff_pull_last_result":"%s","dirty_consecutive_ticks":%d}\n' \
            "${now}" "${worst}" "${new_ticks}" > "${tmp}"
    fi
    mv -f "${tmp}" "${FF_RESULT_FILE}" 2>/dev/null || true
}

# Lightweight lockfile-drift heads-up (deployment_ui_coverage_floor_red_preexisting_2026_07_31
# follow-up). A package-manager migration or lockfile bump (e.g. the 2026-07-29 npm→pnpm +
# jsdom→happy-dom switch that produced the false coverage-floor red) can silently desync a
# long-lived slot clone's `node_modules` — nothing else in this cron ever looks at JS
# lockfiles. This is deliberately NOT another install call: base-ui.sh's `[0/6] ENVIRONMENT`
# step already self-heals `node_modules` on every real `quality-gates.sh` run (shipped
# unified-trading-pm@01ff2a3f5), so re-running `pnpm/yarn/npm install` here on a 5-min cron
# fanning out across every slot would just add repeated network/latency cost for zero
# additional correctness. Instead: hash the highest-precedence lockfile present (pnpm > yarn
# > npm, matching base-ui.sh's own precedence) and compare against this clone's own
# last-seen hash (persisted per-repo, same keying convention as the min-interval throttle
# state above — repo_key is this clone's resolved path, so two slots' clones of the same
# repo NAME never share state). A change since last tick logs one WARN so the drift is
# visible in the cron log the moment it lands, not discovered days later via a confusing
# coverage/test failure. No hash on record yet (first tick ever, or state file lost) seeds
# it silently — never warns on a clone's very first observation. Pure local file reads, no
# network, no I/O beyond one small state file — safe to call unconditionally, every tick,
# regardless of this repo's git/dirty/throttle outcome this tick.
_check_lockfile_drift() {
    local repo_name="$1" repo_key="$2" lock="" pkg_mgr=""
    if [[ -f "pnpm-lock.yaml" ]]; then
        lock="pnpm-lock.yaml"; pkg_mgr="pnpm"
    elif [[ -f "yarn.lock" ]]; then
        lock="yarn.lock"; pkg_mgr="yarn"
    elif [[ -f "package-lock.json" ]]; then
        lock="package-lock.json"; pkg_mgr="npm"
    else
        return 0  # not a JS repo (or no lockfile yet) — nothing to track
    fi
    local hash state_file prev_hash
    hash=$(shasum -a 256 "${lock}" 2>/dev/null | cut -d' ' -f1)
    [[ -n "${hash}" ]] || return 0
    state_file="${TMPDIR:-/tmp}/slot-cron-ff-pull.lockhash.$(printf '%s' "${repo_key}" | shasum -a 256 2>/dev/null | cut -d' ' -f1)"
    prev_hash=$(cat "${state_file}" 2>/dev/null || echo "")
    if [[ -n "${prev_hash}" && "${prev_hash}" != "${hash}" ]]; then
        log "[WARN:lockfile-drift] ${repo_name} — ${lock} changed since last tick — node_modules may now be stale (base-ui.sh self-heals at QG time; run '${pkg_mgr} install' now to pre-warm this clone)"
    fi
    printf '%s' "${hash}" > "${state_file}" 2>/dev/null || true
}

_refresh_independent_clone_ref() {
    # Path-B fix (2026-06-12): advance an independent slot clone's
    # refs/remotes/origin/<branch> from its --reference (main-workspace) clone, whose ref was
    # freshly updated by PHASE-1 prefetch. The clone shares the reference's object store via
    # objects/info/alternates, so this is a LOCAL ref copy — NO network. Must be called from
    # inside the clone (cwd == clone root). Returns non-zero when no usable reference is found
    # (caller then falls back to a direct network fetch).
    local int_branch="$1" ref_objects ref_gitdir
    ref_objects=$(head -n1 ".git/objects/info/alternates" 2>/dev/null)
    [[ -n "${ref_objects}" && -d "${ref_objects}" ]] || return 1
    ref_gitdir="$(dirname "${ref_objects}")"   # .../<repo>/.git/objects → .../<repo>/.git
    [[ -d "${ref_gitdir}" ]] || return 1
    git fetch --quiet --tags --force "${ref_gitdir}" \
        "+refs/remotes/origin/${int_branch}:refs/remotes/origin/${int_branch}" 2>/dev/null
}

# ── venv currency ─────────────────────────────────────────────────────────────
# This cron keeps CODE current and, until 2026-08-11, nothing kept the ENVIRONMENT
# current with it. A FF that moves `uv.lock` leaves the venv behind silently and
# forever, which is how 162 of 216 local slot venvs and 135 of 194 on the
# orchestrator VM ended up drifted from their lockfiles
# (/plans/active/issues/fleet_venv_drift_after_pull_no_resync_2026_08_11.md). The
# damaging case is not version skew but an API boundary: agent-orchestrator sat on
# fastapi 0.136.3 against a lock pinning 0.140.7, so UTL's `iter_route_contexts`
# import raised and the ENTIRE pytest suite stopped collecting.
#
# Deliberately narrow: it re-syncs ONLY when the FF actually changed that repo's
# uv.lock, so an ordinary no-op tick costs one `git diff --quiet` and nothing else.
_resync_venv_if_lock_moved() {
    local repo_name="$1" prev_sha="$2"
    [[ "${SLOT_CRON_SKIP_VENV_RESYNC:-0}" == "1" ]] && return 0
    [[ -f uv.lock && -x .venv/bin/python ]] || return 0
    command -v uv >/dev/null 2>&1 || return 0
    # Unchanged lock -> nothing to do. This is the common case and stays free.
    git diff --quiet "${prev_sha}" HEAD -- uv.lock 2>/dev/null && return 0
    # Never rewrite site-packages under a peer mid-run — same rule the manual sweep
    # followed. A skipped repo is picked up on a later tick, when it is idle.
    if pgrep -af 'pytest|quality-gates|basedpyright' 2>/dev/null | grep -qF "${PWD}"; then
        log "[venv-skip] ${repo_name} — uv.lock moved but a test/gate is running here; resync deferred to a later tick"
        return 0
    fi
    local _to=""
    command -v timeout >/dev/null 2>&1 && _to="timeout 600"
    if ${_to} uv sync --frozen >/dev/null 2>&1; then
        log "[venv-resync] ${repo_name} — uv.lock moved; venv re-synced"
    else
        log "[venv-resync-failed] ${repo_name} — uv.lock moved but 'uv sync' failed; run it manually"
    fi
}

ff_one() {
    local repo_dir="$1"
    local do_fetch="${2:-1}"
    pushd "${repo_dir}" >/dev/null

    local repo_name repo_key branch local_sha remote_sha merge_base ahead behind int_branch
    repo_name=$(basename "${repo_dir}")
    # Per-repo identity for the dirty-streak confirm-gate (repo_name/basename alone is NOT
    # enough — every slot's PM clone is named "unified-trading-pm", every slot's clone of
    # any other repo shares that repo's name too, so basename would re-collapse the
    # per-repo counters back into a per-repo-NAME one, silently reintroducing the same
    # class of cross-clone contamination this fix removes for cross-REPO contamination).
    # The resolved cwd (post-pushd) is a stable, unique identity for THIS physical clone.
    repo_key="$(pwd)"
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "DETACHED")
    int_branch="$(branch_for_repo "${repo_name}")"

    # Lockfile-drift heads-up — runs unconditionally, every tick, regardless of this repo's
    # git/dirty/throttle outcome below (pure local file reads, no network; see the function's
    # own comment for the full rationale).
    _check_lockfile_drift "${repo_name}" "${repo_key}"

    # Min-interval throttle (widen-pm-cron-cadence_2026_07_27): skip this repo entirely,
    # before any other per-repo work, if it was processed more recently than its configured
    # min-interval (cron-repo-min-interval.txt). Keyed by repo_key (the resolved clone path,
    # same identity the dirty-streak gate below already uses) so two slots' clones of the
    # same repo NAME never share throttle state.
    local _min_iv _state_file _last_run _now _elapsed
    _min_iv="$(min_interval_for_repo "${repo_name}")"
    if [[ "${_min_iv}" -gt 0 ]]; then
        _state_file="${TMPDIR:-/tmp}/slot-cron-ff-pull.last-run.$(printf '%s' "${repo_key}" | shasum -a 256 2>/dev/null | cut -d' ' -f1)"
        _now=$(date +%s)
        _last_run=$(cat "${_state_file}" 2>/dev/null || echo 0)
        _elapsed=$(( _now - _last_run ))
        if [[ "${_elapsed}" -lt "${_min_iv}" ]]; then
            log_quiet "[skip:min-interval] ${repo_name} — last processed ${_elapsed}s ago, need ${_min_iv}s"
            popd >/dev/null
            return 0
        fi
        printf '%s' "${_now}" > "${_state_file}" 2>/dev/null || true
    fi

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
        # coverage*.xml : generated pytest artifacts (gitignored fleet-wide via the python
        # template, but discard any that predate the gitignore rollout so they never block FF).
        git clean -fq -- 'coverage*.xml' 2>/dev/null || true
        for _cov in $(git ls-files -m -- 'coverage*.xml' 2>/dev/null); do
            git checkout -q -- "${_cov}" 2>/dev/null || true
        done
        # uv.lock : internal editable-dep "version =" drift is REGEN churn — every repo pins its
        # siblings as editable path sources (source = { editable = "../sibling" }) and `uv sync`
        # (quality-gates / setup) rewrites each sibling's `version = "X"` field to the sibling's
        # CURRENT pyproject version on every run. The HARD RULE (CLAUDE.md / SUB_AGENT_MANDATORY_RULES)
        # is that this internal-version drift must NEVER be committed — the committed lock is canonical
        # and editable installs ignore the version field. Left dirty it [skip:dirty]s the clone → it
        # falls behind the integration branch (the #1 fleet-wide "commits not flowing" cause, esp. for
        # system-integration-tests which pins ALL siblings). Restore ONLY when the diff is PURELY
        # internal "version =" drift — a genuine lock edit (new/removed external package, floor bump,
        # changed wheel/sdist hash) leaves non-version lines → preserved, so in-flight work survives.
        if git ls-files --error-unmatch uv.lock >/dev/null 2>&1 && ! git diff --quiet -- uv.lock 2>/dev/null; then
            _uvnonver=$(git diff -- uv.lock 2>/dev/null \
                | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' \
                | sed -E 's/^[+-][[:space:]]*//' | grep -vcE '^version = "[^"]*"$' || true)
            if [[ "${_uvnonver}" == "0" ]]; then
                git checkout -q -- uv.lock 2>/dev/null || true
                log "[auto-clean] ${repo_name} — discarded uv.lock internal-version drift (editable-dep regen churn)"
            fi
        fi
        # plan_health_digest.md / plan_skeleton.md : the orchestrator plan-health agent writes these
        # untracked digests into the PM EXECUTOR clone root. Untracked files show in `git status
        # --porcelain` → trigger [skip:dirty] below → the clone falls behind → the PlanRegenLoop +
        # plan-health agent that read plans/active/ FROM this clone are starved (incident 2026-06-10:
        # vm-planning PM clone 545 commits behind → empty backlog, no CI-failure/plan-health work).
        # They are pure generated output (regenerated each run) → safe to clean so the FF proceeds.
        # Absent in non-PM repos → no-op. (Should also be gitignored; this is the per-tick safety net.)
        git clean -fq -- plan_health_digest.md plan_skeleton.md 2>/dev/null || true
        if ! git diff --quiet -- workspace-manifest.json 2>/dev/null; then
            _nonstatus=$(git diff -- workspace-manifest.json 2>/dev/null \
                | grep -E '^[+-]' | grep -vE '^[+-]{3}' | grep -vE '"ci_status":' || true)
            if [[ -z "${_nonstatus}" ]]; then
                git checkout -q -- workspace-manifest.json 2>/dev/null || true
                log "[auto-clean] ${repo_name} — discarded ci_status-only manifest churn (CI-authoritative)"
            fi
        fi
        # Cron self-pull artifact heal (2026-07-14): the crontab self-pull snippet
        # (cron-self-pull-lib.sh) asserts the origin/<int_branch> version of its managed cron
        # files into the main PM clone's WORKING TREE each tick without moving HEAD. On a behind
        # clone the file then differs from HEAD → [skip:dirty] below → the clone can never FF →
        # HEAD never catches up → the file stays dirty FOREVER (self-inflicted starvation;
        # root-PM incident 2026-07-14: 1138 commits behind with the self-pull as sole tracked
        # dirt). These files are documented LDR-authoritative (install-slot-cron-ff-pull.sh:
        # local edits to them are overwritten every tick BY DESIGN), so a working copy
        # byte-identical to origin/<int_branch> carries zero local information — restore it to
        # HEAD (index + worktree; the old checkout-based data self-pull also STAGED its write)
        # so the FF below proceeds and brings HEAD, and the file, forward to that same content.
        local _managed
        for _managed in scripts/dev/slot-cron-ff-pull.sh scripts/dev/cron-branch-overrides.txt \
            scripts/verify-slot-host-symmetry.sh scripts/dev/slot-git-status-report.sh; do
            git ls-files --error-unmatch "${_managed}" >/dev/null 2>&1 || continue
            [[ -n "$(git status --porcelain -- "${_managed}" 2>/dev/null)" ]] || continue
            if git show "origin/${int_branch}:${_managed}" 2>/dev/null | cmp -s - "${_managed}" 2>/dev/null; then
                git checkout -q HEAD -- "${_managed}" 2>/dev/null || true
                log "[auto-clean] ${repo_name} — restored ${_managed} to HEAD (cron self-pull artifact; content already on origin/${int_branch})"
            fi
        done
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
    # Dirt gate. TRACKED dirt (modified/staged/renamed/deleted) blocks the FF — that is real
    # WIP and we never clobber it. UNTRACKED-ONLY dirt does NOT (2026-07-16).
    #
    # WHY (this check has frozen a production clone THREE times):
    #   - 2026-06-10 — plan_health_digest.md/plan_skeleton.md (untracked agent output) froze the
    #     vm-planning PM clone 545 commits behind → empty backlog, no plan-health work.
    #   - 2026-07-14 — the cron self-pull artifacts froze root-PM 1138 commits behind.
    #   - 2026-07-16 — main-agent-checkpoint.md (untracked, written BY DESIGN on RECYCLE per
    #     context_lifecycle.py) froze the CENTRAL orchestrator VM's SERVICE clone at 23 commits
    #     behind for 2 days. Every AO fix shipped in that window was on LDR and NOT running.
    # Each was "fixed" by allowlisting one more filename to the auto-clean above. That cannot
    # scale: an allowlist can only ever name files someone already got burned by. The freeze is
    # also SELF-SUSTAINING — a clone that cannot FF never stops being dirty, so one stray file
    # costs FOREVER, not one tick.
    #
    # An untracked file is not a reason to refuse: an FF only moves TRACKED content. In the one
    # case where an untracked file genuinely collides (the incoming commit ADDS that same path),
    # `git merge --ff-only` refuses on its own with "untracked working tree files would be
    # overwritten" — recorded by the [skip:ff-failed]/conflict branch below. Git is the authority
    # on whether the file actually blocks; pre-emptively guessing "dirty ⇒ skip" is what turned a
    # harmless stray file into a permanent outage. Verified empirically 2026-07-16: untracked-only
    # → FF succeeds and the file survives; tracked dirt → still skips; real collision → git refuses.
    #
    # dirty_consecutive_ticks confirm-gate (ao_remediation_b_code_chain_2026_07_23.md
    # item 5, mirrors item 4's server-side git_health.py gate): a SINGLE tick of tracked
    # dirt must not itself skip the FF — whatever produced it (reporter phantom, a
    # transient race, or genuine WIP), one observation is not yet distinguishable from a
    # one-tick phantom. The streak is tracked PER REPO (keyed by repo_key, this clone's own
    # resolved path) — NOT as a single sweep-wide/host-wide aggregate. A --all-slots sweep
    # walks every repo on the host in ONE pass, so a shared aggregate meant repo A's own
    # confirmed dirty streak silently confirmed repo B's genuinely-first dirty tick too,
    # reintroducing the exact cross-repo FF-pull starvation class this confirm-gate exists
    # to prevent (found in a post-hoc audit of this fix — the aggregate is still exactly
    # right for _read_dirty_consecutive_ticks's OTHER consumer, the reporter cross-check;
    # see that function's comment). _read_repo_dirty_ticks reads THIS repo's own prior
    # count; >=1 there means a PRIOR tick already saw THIS repo dirty (confirming, not
    # originating) — only then does the skip actually fire. On the unconfirmed (first)
    # tick the FF is allowed to proceed — git's own --ff-only refuses if the dirty file
    # genuinely collides with the incoming diff (same reasoning as the untracked-dirt case
    # below), so this never clobbers real WIP; it only stops treating one stray tick as
    # gospel. _record_repo_dirty_state persists this tick's dirty/clean observation for
    # THIS repo so the NEXT sweep's read sees it (merged into the result file by
    # _write_ff_result at sweep end, never written mid-sweep — see that function).
    # COLLISION-DEFERRAL (2026-08-10 fleet-drift RCA). Confirmed tracked dirt no longer
    # returns here. It sets _dirt_confirmed and FALLS THROUGH to Step 5.5, where
    # origin/<int_branch> is resolved and the incoming changed-file set is knowable, so the
    # skip is gated on an ACTUAL collision (dirty ∩ incoming) rather than on the mere
    # presence of tracked dirt.
    #
    # WHY: "any tracked dirt ⇒ skip" is the same over-broad guess the untracked-dirt comment
    # below was written to kill, and it caused an identical outage one class down. Measured
    # 2026-08-10: one stale `.github/workflows/semver-agent.yml` (a never-committed rollout
    # artifact, superseded upstream by the unified-trading-ci thin-caller dedup) sat in 15
    # slot-2 repos. No incoming commit touched that path, so no FF was ever at risk — yet
    # every repo was skipped on every 5-minute tick for THREE DAYS, reaching 206 / 113 / 109
    # commits behind. Self-sustaining for the reason documented above: a clone that cannot
    # FF never stops being dirty.
    #
    # Worse, it was INVISIBLE. ff-starvation-detect.sh only pages on `collision AND
    # (behind>=N OR age>H)`, so non-colliding tracked dirt starved the clone while the
    # watchdog stayed silent BY CONSTRUCTION — actor and detector disagreed on the skip
    # rule. Aligning the actor to the detector's (git-accurate) collision model closes the
    # gap from both ends; the detector's new cause-agnostic behind-backstop covers whatever
    # neither model anticipates.
    #
    # Safety is unchanged and doubly held: we skip on a real collision, AND `git merge
    # --ff-only` independently refuses if a dirty tracked file would be clobbered
    # ([skip:ff-failed]). Git stays the authority; we stop pre-emptively guessing.
    local _dirt_confirmed=0
    _tracked_dirt="$(_filter_nonblank_porcelain "$(git status --porcelain --untracked-files=no 2>/dev/null)")"
    if [[ -n "${_tracked_dirt}" ]]; then
        local _prev_repo_dirty_ticks
        _prev_repo_dirty_ticks="$(_read_repo_dirty_ticks "${FF_RESULT_FILE}" "${repo_key}")"
        if [[ "${_prev_repo_dirty_ticks:-0}" -ge 1 ]]; then
            _dirt_confirmed=1
            _record_repo_dirty_state "${repo_key}" "dirty"
            # fall through — Step 5.5 decides on collision, not on dirt alone.
        else
            log "[dirty:unconfirmed] ${repo_name} (${branch}) — uncommitted changes on a single tick; not yet confirmed, FF proceeds this tick"
            _ff_record "dirty:unconfirmed"
            _record_repo_dirty_state "${repo_key}" "dirty"
            # fall through — do NOT return; the FF attempt below proceeds.
        fi
    else
        _record_repo_dirty_state "${repo_key}" "clean"
    fi
    if [[ -z "${_tracked_dirt}" ]] && [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
        # Untracked-only (no tracked dirt at all, so the dirty:unconfirmed branch above
        # never fired for this repo this tick): proceed. Logged (not silent) so scratch
        # accumulation stays visible and the following FF is attributable if git DOES
        # refuse on a collision.
        log "[untracked-ok] ${repo_name} (${branch}) — untracked-only dirt; FF proceeds (git rejects a real collision)"
    fi

    # Step 2: fetch only if not pre-fetched (silent; skip on offline / no-such-ref).
    # `--tags --force` self-heals stale local release tags (e.g. a lightweight
    # v1.0.0 that diverged from semver-agent's canonical remote annotated tag),
    # which would otherwise surface as `(would clobber existing tag)` on a manual
    # `git pull`. Remote is canonical for release tags; forcing local→remote is
    # safe and we never push tags the other way. SSOT:
    # codex/05-infrastructure/per-tab-worktrees.md § "Step 7 — troubleshooting".
    # Independent Path-B clones (.git is a DIRECTORY) have their OWN refs. PHASE-1 prefetch only
    # updated the MAIN-workspace clones' refs, so with do_fetch=0 such a slot would compare HEAD
    # against a STALE local origin/<branch> and silently fall behind (the prefetch shared-ref
    # assumption holds ONLY for legacy linked worktrees, whose .git is a FILE). Refresh the ref:
    # local propagation from the --reference clone (objects already shared → no network), with a
    # direct network fetch as fallback. SSOT: codex/05-infrastructure/per-tab-worktrees.md.
    if [[ "${do_fetch}" -eq 1 ]]; then
        if ! git fetch --quiet --tags --force origin "${int_branch}" 2>/dev/null; then
            log "[skip:fetch-fail] ${repo_name} (${branch}) — fetch failed (offline? missing branch?)"
            _ff_record "fail"
            popd >/dev/null
            return 0
        fi
    elif [[ -d ".git" && -f ".git/objects/info/alternates" ]]; then
        _refresh_independent_clone_ref "${int_branch}" \
            || git fetch --quiet --tags --force origin "${int_branch}" 2>/dev/null || true
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
        _ff_record "ok"
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
        # Auto-adopt ONLY the "tab-mirror GHA rebased origin/tab onto LDR" signature:
        # every ahead-commit is already patch-id-present in LDR (`git cherry` marks the
        # already-applied ones '-', genuinely-new ones '+'), AND the tree is clean. Then a
        # rebase just drops the dups and FFs local to LDR — non-destructive, and it never
        # rewrites genuine in-flight work or touches dirty WIP. Any other divergence
        # (real new local commits, or a dirty tree) stays [skip:diverged] for the agent /
        # manual `git rebase origin/<int_branch>` recovery. See tab-mirror-to-ldr.yml §4.
        genuine_ahead=$(git cherry "origin/${int_branch}" HEAD 2>/dev/null | grep -c '^+' || true)
        dirty=$(git status --porcelain 2>/dev/null | head -c1)
        if [[ "${genuine_ahead}" -eq 0 && -z "${dirty}" ]]; then
            if [[ "${DRY_RUN}" -eq 1 ]]; then
                log "[dry-run:adopt-rebase] ${repo_name} (${branch}) — ${ahead} ahead all mirrored to ${int_branch}; would rebase-adopt to ${remote_sha:0:8}"
            elif git rebase "origin/${int_branch}" >/dev/null 2>&1; then
                log "[adopt-rebase] ${repo_name} (${branch}) — dropped ${ahead} mirrored dup(s); now == ${int_branch} ${remote_sha:0:8}"
                _ff_record "ok"
            else
                git rebase --abort >/dev/null 2>&1 || true
                log "[skip:adopt-failed] ${repo_name} (${branch}) — rebase aborted unexpectedly; manual inspection"
                _ff_record "conflict"
            fi
        else
            log "[skip:diverged] ${repo_name} (${branch} → ${int_branch}) — ahead ${ahead} (${genuine_ahead} genuine), behind ${behind}${dirty:+, dirty tree}; manual/mirror will handle"
            _ff_record "conflict"
        fi
        popd >/dev/null
        return 0
    fi

    # Step 5.5 — confirmed-tracked-dirt COLLISION gate (deferred from the dirt gate above,
    # where origin/<int_branch> was not yet resolved). Skip ONLY if a dirty tracked path is
    # actually in the incoming diff; otherwise the FF cannot touch it, so proceed. Mirrors
    # ff-starvation-detect.sh's `collision = dirty ∩ incoming` definition so the actor and
    # the detector cannot silently drift apart again (they did — see the RCA comment above).
    behind=$(git rev-list --count "HEAD..origin/${int_branch}")
    if [[ "${_dirt_confirmed}" -eq 1 ]]; then
        local _incoming _dirty_paths _colliding
        _incoming="$(git diff --name-only "HEAD..origin/${int_branch}" 2>/dev/null || echo "")"
        # Porcelain v1: "XY PATH", or "R  old -> new" for renames (take the destination).
        _dirty_paths="$(printf '%s\n' "${_tracked_dirt}" | while IFS= read -r _l; do
            [[ -z "${_l}" ]] && continue
            _p="${_l:3}"; _p="${_p##* -> }"; _p="${_p%\"}"; _p="${_p#\"}"
            printf '%s\n' "${_p}"
        done)"
        _colliding="$(printf '%s\n' "${_dirty_paths}" \
            | grep -Fxf <(printf '%s\n' "${_incoming}") 2>/dev/null || true)"
        if [[ -n "${_colliding}" ]]; then
            log "[skip:dirty-collision] ${repo_name} (${branch} → ${int_branch}) — behind ${behind}; dirty tracked file(s) collide with incoming: $(printf '%s' "${_colliding}" | tr '\n' ' ')"
            _ff_record "skip:dirty"
            popd >/dev/null
            return 0
        fi
        log "[dirty-nocollide] ${repo_name} (${branch} → ${int_branch}) — behind ${behind}; tracked dirt present but NOT in the incoming diff; FF proceeds (git rejects a real collision)"
    fi

    # Step 6: clean fast-forward (merge_base == local_sha, remote ahead).
    if [[ "${DRY_RUN}" -eq 1 ]]; then
        log "[dry-run:ff] ${repo_name} (${branch} → ${int_branch}) — would FF by ${behind} commit(s) to ${remote_sha:0:8}"
    else
        if git merge --ff-only --quiet "origin/${int_branch}" 2>/dev/null; then
            log "[ff] ${repo_name} (${branch} → ${int_branch}) — FF +${behind} → ${remote_sha:0:8}"
            _ff_record "ok"
            _resync_venv_if_lock_moved "${repo_name}" "${local_sha}"
        else
            log "[skip:ff-failed] ${repo_name} (${branch} → ${int_branch}) — --ff-only refused; manual inspection needed"
            _ff_record "conflict"
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
    # This populates the SHARED object store (each Path-B slot clone references it
    # via objects/info/alternates) so PHASE-2's per-slot ref refresh is object-local
    # (no network). NOTE: this does NOT advance the independent slot clones' refs —
    # PHASE 2 does that per-slot (_refresh_independent_clone_ref). For legacy linked
    # worktrees (.git FILE) the refs are genuinely shared, so this alone sufficed.
    # Skips dirs without .git/ (e.g. .tabs/, plans/, etc.).
    local main_ws="$1"
    local fetched=0
    local failed=0
    for d in "${main_ws}"/*/; do
        [[ -d "${d}.git" ]] || continue  # only main clones (file-.git = linked worktree)
        local repo_name int_branch
        repo_name=$(basename "${d}")
        int_branch="$(branch_for_repo "${repo_name}")"
        # Reference-clone prune protection (2026-07-13). This very fetch adds loose objects to
        # the base every tick — exactly what pushes it past git's auto-gc threshold. The base
        # backs N slot `git clone --reference` clones (shared object store via
        # objects/info/alternates), and default auto-gc prunes objects unreachable from the
        # BASE's refs with no knowledge of slot refs → a slot's stale ref/reflog is left
        # pointing at a deleted object and its `git fsck` FAILS ("invalid sha1 pointer" /
        # "invalid reflog entry"). gc.pruneExpire=never keeps auto-gc's repack but never
        # DELETES objects. Asserted here because this cron runs every 5 min on EVERY slot host
        # and self-pulls its own code, so the fix reaches the whole fleet with no manual
        # deploy. SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Reference-clone prune hazard".
        git -C "${d}" config gc.pruneExpire never 2>/dev/null || true
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

# === END OF FUNCTION DEFINITIONS — tests source everything ABOVE this marker ===
# tests/test_slot_cron_ff_pull_dirty_gate.bats extracts the prefix of this file to unit-test the
# helpers without running the script. It used to do that with a hardcoded FN_DEFS_END_LINE=712.
# The file grew to >1000 lines, so that cut landed MID-FUNCTION: the extracted prefix stopped
# parsing, `source` failed, and all 6 tests in that file failed with errors that read as though
# the dirty-gate logic itself was broken. Keep this a MARKER, never a line number — and keep it
# immediately after the last function definition, before any top-level execution.

# Resolve starting slot dir.
cwd="$(pwd)"
if [[ -f .git || -d .git ]]; then
    # Inside a per-repo worktree → climb to slot dir.
    cwd="$(cd .. && pwd)"
fi

if [[ "${MODE}" == "single-slot" ]]; then
    walk_slot "${cwd}" 1
    _write_ff_result
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

# Aggregate the parallel workers' per-repo outcome tokens into the host-global
# cron-liveness result file the reporter reads (fleet_git_health Phase 3).
_write_ff_result

# --- L0 doc-index regen (W4, agent_operating_framework_master) — piggyback the FF sweep ---
# After the sweep pulls in new commits (possibly new frontmatter), refresh the grep-native L0 map
# in EVERY PM clone on this host: the main-workspace PM (whose script copy cron runs) PLUS each
# .tabs/<N>/unified-trading-pm slot clone. DOC_INDEX.generated.md is per-clone, gitignored,
# consumer-side local. The sweep's per-repo dirty/ahead skips apply to the PULL only — a dirty PM
# still gets its index refreshed here (the regen only READS docs + writes the ignored file; it can
# never dirty the tree / jam the FF). PM-only by construction (paths end in /unified-trading-pm);
# other repos don't carry the generator. `--stale-check` rewrites only on content change. Each run
# guarded + `timeout`-bounded so a bug can never hang or fail the cron (|| true). Cost: ~1.4s per
# clone, sequential, at sweep end — acceptable for a 5-min cron.
# Workspace root derivation must be invocation-agnostic: the script may run from the
# main-workspace PM (cron) OR a slot clone (.tabs/<N>/unified-trading-pm) — strip any
# /.tabs/<N>/ suffix to land on the workspace root either way.
_pm_home="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ "${_pm_home}" == */.tabs/* ]]; then
    _ws_root="${_pm_home%%/.tabs/*}"
else
    _ws_root="$(dirname "${_pm_home}")"
fi
for _pm_clone in "${_ws_root}/unified-trading-pm" "${_ws_root}"/.tabs/*/unified-trading-pm; do
    [[ -d "${_pm_clone}" && -f "${_pm_clone}/scripts/docs/gen_doc_index.py" ]] || continue
    _idx_py="${_pm_clone}/.venv/bin/python"
    [[ -x "${_idx_py}" ]] || _idx_py="python3"
    timeout 60 "${_idx_py}" "${_pm_clone}/scripts/docs/gen_doc_index.py" --stale-check >/dev/null 2>&1 || true
done

# --- Git-hook self-heal, ALL repos × ALL clones (2026-07-06) ---
# Found: 384/400 clones (25 repos × 16 clones, every one carrying a .pre-commit-config.yaml) had
# NO prek pre-commit hook — setup-tab-worktrees.sh only ever installed the pre-push guard, so
# commit-time gates (gitleaks, slot·host commit-identity, staged-plans schema in PM, ruff,
# prettier, conventional-commit) silently never ran fleet-wide; 24 main-ws clones also lacked the
# pre-push strict-quickmerge guard, and 10 clones carried a stale absolute core.hooksPath from the
# pre-/active migration that disabled ALL hooks. Heal every tick: missing pre-commit →
# `prek install` (writes pre-commit + commit-msg ONLY — pre-push stays the strict-quickmerge
# guard, prek must NEVER manage it); missing pre-push → copy the guard from the workspace PM.
# core.hooksPath is cleared ONLY when provably dead (target dir gone) — a live custom hooksPath is
# deliberate and left alone. Idempotent, guarded, || true — can never jam the cron.
# Fix 2026-07-07: two bugs found auditing this block on a host where it had been a total no-op
# since 2026-07-06 (prek missing at ~/.local/bin, so -x "${_prek_bin}" was false every tick with
# zero logging either way — installed via `uv tool install prek` to resolve that half). The other
# half is IN this block: (1) `-f "${_clone}/.git/hooks/pre-commit"` treated ANY pre-existing file —
# e.g. a hand-written unrelated hook predating this feature — as "already installed", permanently
# skipping prek for that clone (verified prek actually migrates a foreign hook fine: moves it to
# `pre-commit.legacy` and chains it, exit 0 — the block just never tried). Now detects prek's own
# marker instead of blind existence, so a foreign hook gets migrated exactly once. (2) the literal
# `${_clone}/.git/hooks/...` path is wrong for a linked worktree (`.git` is a FILE there; the real
# shared hooks dir lives under the main clone) — every tick "saw" no hook and re-ran `prek install`
# harmlessly but pointlessly. Resolved via `git rev-parse --path-format=absolute --git-path hooks`,
# which returns the correct dir for a normal clone, a Path-B --reference clone, AND a linked worktree.
# Fix 2026-07-08: the 2026-07-07 "install prek at ~/.local/bin" half did NOT hold on every host —
# on a host where prek lives ONLY in the workspace venv (.venv-workspace/bin, not ~/.local/bin) the
# resolver `command -v prek || ~/.local/bin/prek` again resolved to a NON-EXISTENT path under cron's
# minimal PATH, so -x was false and the whole block no-op'd fleet-wide (audited: 288/300 clones
# missing the prek pre-commit). Two hardenings: (a) probe EVERY known prek location (PATH,
# ~/.local/bin, workspace .venv-workspace/bin, PM .venv/bin) and LOG LOUDLY when none is usable — this
# failure can never again be silent; (b) SKIP husky-managed repos (core.hooksPath under .husky): prek
# does NOT refuse with hooksPath set — it OVERWRITES husky's .husky/_/ shims with its own pre-commit +
# commit-msg, wrong for the JS UI repos, which gate commits via husky/lint-staged, not prek.
_prek_bin=""
for _cand in \
    "$(command -v prek 2>/dev/null || true)" \
    "${HOME}/.local/bin/prek" \
    "${_ws_root}/.venv-workspace/bin/prek" \
    "${_ws_root}/unified-trading-pm/.venv/bin/prek"; do
    if [[ -n "${_cand}" && -x "${_cand}" ]]; then _prek_bin="${_cand}"; break; fi
done
if [[ -z "${_prek_bin}" ]]; then
    log "[hook-heal:WARN] prek not found (PATH / ~/.local/bin / .venv-workspace/bin / PM .venv/bin) — pre-commit hooks NOT installed this tick; install with 'uv tool install prek'"
fi
# The ONE canonical pre-push source (strict-quickmerge + dep-alignment, chained). Must match
# install-hooks.sh's HOOK_SOURCE and setup-tab-worktrees.sh — three installers previously raced over
# this same destination with two different sources, and the loser (dep-align-only) won in all 25
# clones, so nothing was enforced off staging (2026-07-17).
_pp_guard="${_ws_root}/unified-trading-pm/scripts/hooks/pre-push"
for _clone in "${_ws_root}"/*/ "${_ws_root}"/.tabs/*/*/; do
    _clone="${_clone%/}"
    [[ -e "${_clone}/.git" && -f "${_clone}/.pre-commit-config.yaml" ]] || continue
    _hooks_dir="$(git -C "${_clone}" rev-parse --path-format=absolute --git-path hooks 2>/dev/null)" || continue
    [[ -n "${_hooks_dir}" ]] || continue
    # Husky-managed repos (JS UI: deployment-ui, unified-trading-system-ui) resolve their hooks dir
    # UNDER .husky/ via core.hooksPath. prek would clobber husky's .husky/_/ shims (it does NOT
    # refuse with hooksPath set), so pre-commit stays entirely husky's — skip prek AND the
    # .git/hooks-style pre-push copy (copying into ${_hooks_dir} would overwrite husky's own
    # internal dispatcher shim, not a real hook). The strict-quickmerge guard for these two repos
    # instead lives at a COMMITTED, version-controlled file — <repo>/.husky/pre-push, a thin
    # delegate to this same canonical scripts/hooks/pre-push (mirrors .husky/pre-commit's prek
    # delegation) — so it ships via normal commits, not a per-tick content-heal. This branch only
    # RECOGNISES that install (warn loudly if the delegate is missing) instead of silently skipping
    # every husky repo with zero signal — that exact blind spot is how both UI repos carried NO
    # provenance guard at all for months (issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md).
    case "${_hooks_dir}" in
        */.husky/*)
            _husky_pp="${_hooks_dir%/_}/pre-push"
            if [[ ! -f "${_husky_pp}" ]]; then
                log "[hook-heal:WARN] ${_clone}: husky-managed repo has NO .husky/pre-push strict-quickmerge delegate — provenance guard missing (see issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md)"
            fi
            continue
            ;;
    esac
    _pc_hook="${_hooks_dir}/pre-commit"
    _pp_hook="${_hooks_dir}/pre-push"
    if [[ -x "${_prek_bin}" ]] && { [[ ! -f "${_pc_hook}" ]] || ! grep -q 'generated by prek' "${_pc_hook}" 2>/dev/null; }; then
        if ! (cd "${_clone}" && timeout 30 "${_prek_bin}" install >/dev/null 2>&1); then
            _hp="$(git -C "${_clone}" config --local core.hooksPath 2>/dev/null || true)"
            if [[ -n "${_hp}" && ! -d "${_hp}" ]]; then
                git -C "${_clone}" config --unset-all --local core.hooksPath 2>/dev/null || true
                (cd "${_clone}" && timeout 30 "${_prek_bin}" install >/dev/null 2>&1) || true
            fi
        fi
    fi
    # CONTENT-gated, not existence-gated. The old `! -f "${_pp_hook}"` test could NEVER fire: a
    # pre-push file always already existed (install-hooks.sh copies one into every clone), so this
    # "self-heal" spent months re-affirming a hook that enforced nothing off staging. Re-copy
    # whenever the installed hook lacks the strict guard, so every clone converges within one 5-min
    # sweep instead of only at clone time — main-workspace clones were never covered by
    # setup-tab-worktrees.sh at all, and that is where all 33 bypassed commits came from.
    # IDENTITY-gated (2026-07-18), not marker-gated. A `grep -q check_strict_quickmerge` test only
    # asks "does SOME strict hook exist" — so it re-heals a MISSING hook but never refreshes a STALE
    # one. Measured the same day: adding the frontmatter guard [2] left .tabs/*/unified-trading-pm
    # pinned on the previous 2-guard hook, because that hook still matched the marker. Comparing
    # against the canonical source instead makes EVERY future hook change propagate within one sweep,
    # with no marker to remember to update.
    if [[ -f "${_pp_guard}" ]] && ! cmp -s "${_pp_guard}" "${_pp_hook}" 2>/dev/null; then
        cp "${_pp_guard}" "${_pp_hook}" 2>/dev/null \
            && chmod +x "${_pp_hook}" || true
    fi
done

# Heartbeat: write ONE line every run, even in --quiet on a fully-idle no-op sweep, so the
# log mtime always refreshes while the cron is alive. verify-slot-host-symmetry.sh check 3
# ("FF-pull log fresh <10m") reads only the mtime — without this, a quiet idle window (LDR
# not advancing + all worktrees clean) writes nothing and the check false-fails despite a
# healthy cron. `log` (not log_quiet) makes check 3 test cron LIVENESS, not "had work to do".
log "=== sweep complete ==="
