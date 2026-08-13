#!/usr/bin/env bats
# test_slot_cron_ff_pull_dirty_gate.bats — unit tests for the dirty-gate
# count-integrity fix in slot-cron-ff-pull.sh's ff_one()
#   (ao_remediation_b_code_chain_2026_07_23.md items 3 + 5, mirrors item 1 + item 4;
#    git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md).
#
# HERMETIC: builds throwaway git repos under BATS_TEST_TMPDIR; never touches real
# worktrees in $WORKSPACE_ROOT, never acquires the real fleet cron's lock file, never
# runs the fleet-wide git-hook self-heal / doc-index regen at the bottom of the real
# script.
#
# slot-cron-ff-pull.sh has NO clean "point it at an empty workspace" off-switch like
# slot-git-status-report.sh: the very first top-level statements after the LAST
# function definition (prefetch_main_clones, ending line 712) immediately resolve cwd,
# call walk_slot on it with a REAL fetch, and `exit 0` — so a full `source` of the real
# file is unsafe (it would walk whatever directory the test happens to run from). We
# therefore source only lines 1-712 (every function def, none of the driver) into a
# fresh bash subprocess (via `run bash -c`), with SLOT_FF_PULL_LOCK_FILE and
# SLOT_FF_PULL_RESULT_FILE pointed at per-test tmp paths so the lock/result-file side
# effects stay hermetic, then call ff_one()/_write_ff_result() directly.
#
# Run: bats tests/test_slot_cron_ff_pull_dirty_gate.bats
# Run all: bats tests/

FF_CRON="unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh"
# Boundary is found by MARKER, never hardcoded. It WAS hardcoded (712); the script grew past
# 1000 lines and that cut landed mid-function, so the extracted prefix stopped parsing and all
# 6 tests here failed as though the dirty-gate logic were broken. A line number silently rots;
# a marker fails loudly if someone removes it.
FN_DEFS_MARKER="=== END OF FUNCTION DEFINITIONS"

setup() {
    WS_ROOT="$(git rev-parse --show-toplevel)/.."
    cd "${WS_ROOT}" || cd ..
    FF_CRON_ABS="$(cd "$(dirname "${FF_CRON}")" && pwd)/$(basename "${FF_CRON}")"
    FN_DEFS="${BATS_TEST_TMPDIR}/ff_cron_fn_defs_$$_${RANDOM}.sh"
    FN_DEFS_END_LINE="$(grep -n "${FN_DEFS_MARKER}" "${FF_CRON_ABS}" | head -1 | cut -d: -f1)"
    [ -n "${FN_DEFS_END_LINE}" ] || {
        echo "marker '${FN_DEFS_MARKER}' not found in ${FF_CRON_ABS} — restore it rather than" >&2
        echo "reverting to a hardcoded line number; see the comment at the marker." >&2
        return 1
    }
    sed -n "1,$((FN_DEFS_END_LINE - 1))p" "${FF_CRON_ABS}" > "${FN_DEFS}"
    LOCK_PATH="${BATS_TEST_TMPDIR}/lock_$$_${RANDOM}.lock"
    RESULT_PATH="${BATS_TEST_TMPDIR}/result_$$_${RANDOM}.json"
}

# Build a local clone + bare "origin" both on live-defi-rollout, local HEAD ==
# origin HEAD (clean + up to date) unless the caller dirties it afterward.
_make_synced_repo() {
    local root="${BATS_TEST_TMPDIR}/repo_$$_${RANDOM}"
    mkdir -p "${root}"
    git init -q --bare "${root}/remote.git"
    git init -q "${root}/local"
    (
        cd "${root}/local"
        git config user.email t@t.t
        git config user.name t
        git remote add origin ../remote.git
        printf 'v1\n' > tracked.txt
        git add -A && git commit -qm init
        git push -q origin HEAD:live-defi-rollout
        git fetch -q origin live-defi-rollout
    )
    echo "${root}/local"
}

# Call ff_one() (do_fetch=0 — no network, the fixture already has origin/live-defi-
# rollout cached) then _write_ff_result(), and print the resulting result-file JSON.
# The per-repo confirm-gate reads its own prior streak straight out of RESULT_PATH inside
# ff_one() itself now (repo_dirty_ticks, keyed by repo_key) — no separate pre-sweep global
# to seed here any more — so calling this twice against the SAME RESULT_PATH reproduces two
# consecutive cron ticks for the confirm-gate (item 5) purely via the file on disk.
_run_ff_one() {
    local repo="$1"
    SLOT_FF_PULL_LOCK_FILE="${LOCK_PATH}" SLOT_FF_PULL_RESULT_FILE="${RESULT_PATH}" \
        bash -c '
            SLOT_CRON_FF_PULL_LIB_ONLY=1 source "'"${FN_DEFS}"'" --quiet
            ff_one "'"${repo}"'" 0
            _write_ff_result
            cat "'"${RESULT_PATH}"'"
        '
}

# Multi-repo variant: runs ff_one() for EVERY repo passed, all within ONE simulated sweep
# (mirrors --all-slots: walk_slot() calls ff_one() once per repo, then ONE
# _write_ff_result() fires after every repo in the sweep has been walked), then dumps the
# result-file JSON. Needed to reproduce/verify the cross-repo dirty-gate bug, which only
# manifests when more than one repo shares a single sweep — a sweep containing exactly one
# repo (as _run_ff_one models) can never exercise cross-repo contamination.
_run_ff_multi() {
    SLOT_FF_PULL_LOCK_FILE="${LOCK_PATH}" SLOT_FF_PULL_RESULT_FILE="${RESULT_PATH}" \
        bash -c '
            SLOT_CRON_FF_PULL_LIB_ONLY=1 source "'"${FN_DEFS}"'" --quiet
            for repo in "$@"; do
                ff_one "${repo}" 0
            done
            _write_ff_result
            cat "'"${RESULT_PATH}"'"
        ' _ "$@"
}

# Push a NEW commit to the bare "origin" that also touches tracked.txt, then fetch it into
# the repo's own origin/live-defi-rollout ref WITHOUT touching local HEAD -- simulates a
# concurrent push landing between two cron ticks (real Phase-1 prefetch behaviour), so the
# repo is left both diverged AND colliding on the same path its own local dirt touches.
_push_colliding_commit_to_origin() {
    local repo="$1" bare
    # `origin` is set to a RELATIVE path ("../remote.git", see _make_synced_repo) -- resolve
    # it to absolute before cloning from an unrelated tmp cwd, or the clone 404s (status 128).
    bare="$(cd "${repo}" && git rev-parse --show-toplevel)/../remote.git"
    bare="$(cd "${bare}" && pwd)"
    (
        local tmp
        tmp="$(mktemp -d)"
        # -b live-defi-rollout: the bare repo's HEAD symref defaults to "master" (never
        # created -- _make_synced_repo only ever pushes "live-defi-rollout"), so a plain
        # `git clone` checks out nothing and a commit here would build on an unrelated
        # history, rejected by the push below as non-fast-forward.
        git clone -q -b live-defi-rollout "${bare}" "${tmp}/writer" 2>/dev/null
        cd "${tmp}/writer" || exit 1
        git config user.email w@w.w
        git config user.name w
        printf 'v3-from-origin\n' >tracked.txt
        git add -A && git commit -qm "origin advances tracked.txt"
        git push -q origin HEAD:live-defi-rollout
    )
    git -C "${repo}" fetch -q origin live-defi-rollout
}

@test "slot-cron-ff-pull.sh has valid bash syntax" {
    run bash -n "$FF_CRON_ABS"
    [ "$status" -eq 0 ]
}

@test "_filter_nonblank_porcelain: blank-only capture -> empty (structural, cause-agnostic)" {
    # Regression guard for the exact phantom fingerprint this item mirrors: a raw
    # capture that is byte-non-empty (a stray blank/whitespace line) must never read
    # as real dirt once filtered.
    run bash -c '
        SLOT_CRON_FF_PULL_LIB_ONLY=1 source "'"${FN_DEFS}"'" --quiet
        out="$(_filter_nonblank_porcelain "$(printf "\n")")"
        printf "[%s]" "$out"
    '
    [ "$status" -eq 0 ]
    [ "$output" = "[]" ]
}

@test "_filter_nonblank_porcelain: real porcelain line -> kept verbatim" {
    run bash -c '
        SLOT_CRON_FF_PULL_LIB_ONLY=1 source "'"${FN_DEFS}"'" --quiet
        _filter_nonblank_porcelain "$(printf "M  tracked.txt")"
    '
    [ "$status" -eq 0 ]
    [[ "$output" == *"tracked.txt"* ]]
}

@test "clean + up-to-date tree -> ff_pull_last_result != skip:dirty" {
    repo="$(_make_synced_repo)"
    run _run_ff_one "${repo}"
    [ "$status" -eq 0 ]
    [[ "$output" != *'"ff_pull_last_result":"skip:dirty"'* ]]
    [[ "$output" == *'"ff_pull_last_result":"ok"'* ]]
}

@test "item 5: single-tick dirty (tracked modification) -> NOT skip:dirty yet (unconfirmed)" {
    # ao_remediation_b_code_chain_2026_07_23.md item 5 Gate: a single-tick dirty
    # observation must not itself cause an FF-pull skip, whatever produced it.
    repo="$(_make_synced_repo)"
    printf 'v2\n' > "${repo}/tracked.txt"
    run _run_ff_one "${repo}"
    [ "$status" -eq 0 ]
    [[ "$output" != *'"ff_pull_last_result":"skip:dirty"'* ]]
    [[ "$output" == *'"ff_pull_last_result":"dirty:unconfirmed"'* ]]
    [[ "$output" == *'"dirty_consecutive_ticks":1'* ]]
}

@test "item 5: two consecutive dirty ticks on the same repo -> confirmed, second tick == skip:dirty" {
    # Confirmed dirt alone no longer skips (COLLISION-DEFERRAL, 2026-08-10 fleet-drift RCA,
    # see slot-cron-ff-pull.sh's own comment at "Step 5.5") -- the skip additionally requires
    # the confirmed-dirty tracked path to actually collide with the incoming diff, so this
    # fixture must ALSO diverge origin with a competing change to the same file, or the
    # confirmed-second-tick can never reach [skip:dirty] (it stops earlier, at
    # already-up-to-date, since nothing pushed anything new).
    repo="$(_make_synced_repo)"
    printf 'v2\n' > "${repo}/tracked.txt"
    run _run_ff_one "${repo}"          # tick 1: unconfirmed
    [ "$status" -eq 0 ]
    [[ "$output" != *'"ff_pull_last_result":"skip:dirty"'* ]]
    _push_colliding_commit_to_origin "${repo}"
    run _run_ff_one "${repo}"          # tick 2: streak >= 1 (confirmed) AND a real collision -> skip
    [ "$status" -eq 0 ]
    [[ "$output" == *'"ff_pull_last_result":"skip:dirty"'* ]]
    [[ "$output" == *'"dirty_consecutive_ticks":2'* ]]
}

@test "item 5: a clean tick after an unconfirmed dirty tick resets the streak" {
    repo="$(_make_synced_repo)"
    printf 'v2\n' > "${repo}/tracked.txt"
    run _run_ff_one "${repo}"          # tick 1: unconfirmed dirty, ticks -> 1
    [ "$status" -eq 0 ]
    [[ "$output" == *'"dirty_consecutive_ticks":1'* ]]
    git -C "${repo}" checkout -q -- tracked.txt   # back to clean + up-to-date
    run _run_ff_one "${repo}"          # tick 2: clean -> resets, never reaches confirmed
    [ "$status" -eq 0 ]
    [[ "$output" != *'"ff_pull_last_result":"skip:dirty"'* ]]
    [[ "$output" == *'"dirty_consecutive_ticks":0'* ]]
}

@test "cross-repo isolation: repo Y's first-ever dirty tick is NOT confirmed by repo X's already-confirmed streak" {
    # Reproduces the cross-repo FF-pull starvation bug: the confirm-gate used to read a
    # SINGLE sweep-wide/host-wide PREV_DIRTY_CONSECUTIVE_TICKS value shared by every repo
    # walked in a sweep, so once repo X's OWN streak confirmed (skip:dirty), that confirmed
    # state silently applied to every OTHER repo in the same (or the very next) sweep too --
    # repo Y's genuinely-first-ever dirty tick would incorrectly confirm-skip instead of
    # getting the one-tick grace (dirty:unconfirmed) it is entitled to on its own.
    repoX="$(_make_synced_repo)"
    repoY="$(_make_synced_repo)"

    # Tick 1 (sweep 1): only repo X is dirty -> unconfirmed (repo X's own first tick).
    printf 'v2\n' > "${repoX}/tracked.txt"
    run _run_ff_multi "${repoX}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"[dirty:unconfirmed]"* ]]
    [[ "$output" != *"[skip:dirty]"* ]]

    # Tick 2 (sweep 2, same result file -> state carries forward): repo X is dirty AGAIN
    # (its own second consecutive tick -> correctly confirms) AND, in the SAME sweep, repo Y
    # -- a different, previously-clean repo -- becomes dirty for the very first time ever.
    # repo X also needs a genuine collision to reach [skip:dirty] under the collision-gated
    # design (see the sibling "two consecutive dirty ticks" test's comment) -- repo Y does
    # NOT get this treatment, since its own tick must stay unconfirmed regardless.
    _push_colliding_commit_to_origin "${repoX}"
    printf 'v2\n' > "${repoY}/tracked.txt"
    run _run_ff_multi "${repoX}" "${repoY}"
    [ "$status" -eq 0 ]
    # repo X: correctly confirmed on its own second consecutive dirty tick, with a real
    # collision -- checked via the result-file JSON (authoritative), not the log line, since
    # the collision-gated path logs "[skip:dirty-collision]" rather than plain "[skip:dirty]".
    [[ "$output" == *'"ff_pull_last_result":"skip:dirty"'* ]]
    # repo Y: must get its OWN one-tick grace (dirty:unconfirmed) on this, its first dirty
    # tick -- independent of repo X's already-confirmed state in the SAME sweep. The bug
    # instead fires [skip:dirty] for repo Y here too (no [dirty:unconfirmed] line at all),
    # because the confirm-gate can't tell repo Y's history apart from repo X's.
    [[ "$output" == *"[dirty:unconfirmed]"* ]]
}
