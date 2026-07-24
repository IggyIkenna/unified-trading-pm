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
# function definition (prefetch_main_clones, ending line 598) immediately resolve cwd,
# call walk_slot on it with a REAL fetch, and `exit 0` — so a full `source` of the real
# file is unsafe (it would walk whatever directory the test happens to run from). We
# therefore source only lines 1-598 (every function def, none of the driver) into a
# fresh bash subprocess (via `run bash -c`), with SLOT_FF_PULL_LOCK_FILE and
# SLOT_FF_PULL_RESULT_FILE pointed at per-test tmp paths so the lock/result-file side
# effects stay hermetic, then call ff_one()/_write_ff_result() directly.
#
# Run: bats tests/test_slot_cron_ff_pull_dirty_gate.bats
# Run all: bats tests/

FF_CRON="unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh"
FN_DEFS_END_LINE=598

setup() {
    WS_ROOT="$(git rev-parse --show-toplevel)/.."
    cd "${WS_ROOT}" || cd ..
    FF_CRON_ABS="$(cd "$(dirname "${FF_CRON}")" && pwd)/$(basename "${FF_CRON}")"
    FN_DEFS="${BATS_TEST_TMPDIR}/ff_cron_fn_defs_$$_${RANDOM}.sh"
    sed -n "1,${FN_DEFS_END_LINE}p" "${FF_CRON_ABS}" > "${FN_DEFS}"
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
# PREV_DIRTY_CONSECUTIVE_TICKS is computed from RESULT_PATH first, mirroring the real
# driver's pre-sweep read (bottom of the real script, not part of the sourced FN_DEFS
# function-only block) — so calling this twice against the SAME RESULT_PATH reproduces
# two consecutive cron ticks for the confirm-gate (item 5).
_run_ff_one() {
    local repo="$1"
    SLOT_FF_PULL_LOCK_FILE="${LOCK_PATH}" SLOT_FF_PULL_RESULT_FILE="${RESULT_PATH}" \
        bash -c '
            source "'"${FN_DEFS}"'" --quiet
            PREV_DIRTY_CONSECUTIVE_TICKS="$(_read_dirty_consecutive_ticks "'"${RESULT_PATH}"'")"
            ff_one "'"${repo}"'" 0
            _write_ff_result
            cat "'"${RESULT_PATH}"'"
        '
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
        source "'"${FN_DEFS}"'" --quiet
        out="$(_filter_nonblank_porcelain "$(printf "\n")")"
        printf "[%s]" "$out"
    '
    [ "$status" -eq 0 ]
    [ "$output" = "[]" ]
}

@test "_filter_nonblank_porcelain: real porcelain line -> kept verbatim" {
    run bash -c '
        source "'"${FN_DEFS}"'" --quiet
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
    repo="$(_make_synced_repo)"
    printf 'v2\n' > "${repo}/tracked.txt"
    run _run_ff_one "${repo}"          # tick 1: unconfirmed
    [ "$status" -eq 0 ]
    [[ "$output" != *'"ff_pull_last_result":"skip:dirty"'* ]]
    run _run_ff_one "${repo}"          # tick 2: PREV_DIRTY_CONSECUTIVE_TICKS now >= 1 -> confirmed
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
