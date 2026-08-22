#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for base-service.sh's BATS_HARD_FAIL opt-in
# (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md, todo G).
#
# `.bats` shell-test failures were WARN-only for every repo sharing base-service.sh (a
# genuine regression could ship silently). PM's own suite re-measured 0 failures 2026-08-12
# (was 60 -- both root causes fixed, not left ratcheted), so PM opts in via
# `BATS_HARD_FAIL=1` in its own quality-gates.sh. This test proves the opt-in actually
# changes the exit code, and that every OTHER repo (opt-in unset) keeps today's unchanged
# WARN-only behaviour -- a shared file serving every service repo must never regress that
# default silently.
#
# Extracts the exact bats-invocation block (between the `_BATS_FILES=()` line and the
# "=== END OF BATS SHELL TESTS BLOCK ===" marker) with log_ok/log_warn/log_fail/log_section
# and `bats` itself stubbed, so this never actually runs the real (slow, 600+ test) suite.

setup() {
    REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    BASE_SERVICE="${REPO_ROOT}/scripts/quality-gates-base/base-service.sh"
    START_MARKER='_BATS_FILES=()'
    END_MARKER='=== END OF BATS SHELL TESTS BLOCK ==='

    WORK="${BATS_TEST_TMPDIR}/work"
    mkdir -p "${WORK}/tests"
    touch "${WORK}/tests/dummy.bats" # so _BATS_FILES is non-empty

    START_LINE="$(grep -n "${START_MARKER}" "${BASE_SERVICE}" | head -1 | cut -d: -f1)"
    END_LINE="$(grep -n "${END_MARKER}" "${BASE_SERVICE}" | head -1 | cut -d: -f1)"
    [ -n "${START_LINE}" ] && [ -n "${END_LINE}" ] || {
        echo "marker(s) not found in ${BASE_SERVICE} — restore them rather than reverting to" >&2
        echo "hardcoded line numbers." >&2
        return 1
    }

    SNIPPET="${BATS_TEST_TMPDIR}/bats_block.sh"
    sed -n "${START_LINE},$((END_LINE - 1))p" "${BASE_SERVICE}" >"${SNIPPET}"
}

# Runs the extracted block in a fresh bash subprocess with everything it calls stubbed.
# $1 = "pass" or "fail" (what the stubbed `bats` invocation reports).
_run_block() {
    local bats_outcome="$1"
    (
        cd "${WORK}" || exit 1
        bash -c '
            set -e
            log_section() { :; }
            log_ok()      { echo "LOG_OK: $*"; }
            log_warn()    { echo "LOG_WARN: $*"; }
            log_fail()    { echo "LOG_FAIL: $*"; }
            command() {
                case "$1 $2" in
                    "-v bats") return 0 ;;
                    "-v parallel") return 1 ;;
                    *) builtin command "$@" ;;
                esac
            }
            bats() { [ "'"${bats_outcome}"'" = "pass" ] && return 0 || return 1; }
            source "'"${SNIPPET}"'"
            echo "REACHED_END"
        '
    )
}

@test "bats passes: exits 0 regardless of BATS_HARD_FAIL" {
    run _run_block pass
    [ "$status" -eq 0 ]
    [[ "$output" == *"LOG_OK: BATS tests PASSED"* ]]
    [[ "$output" == *"REACHED_END"* ]]
}

@test "bats fails, BATS_HARD_FAIL unset: warns, exits 0 (today's unchanged default for every other repo)" {
    unset BATS_HARD_FAIL
    run _run_block fail
    [ "$status" -eq 0 ]
    [[ "$output" == *"LOG_WARN: BATS:"* ]]
    [[ "$output" == *"REACHED_END"* ]]
}

@test "bats fails, BATS_HARD_FAIL=1: hard-fails, does NOT reach past the block" {
    export BATS_HARD_FAIL=1
    run _run_block fail
    unset BATS_HARD_FAIL
    [ "$status" -eq 1 ]
    [[ "$output" == *"LOG_FAIL: BATS:"* ]]
    [[ "$output" != *"REACHED_END"* ]]
}

@test "bats fails, BATS_HARD_FAIL=0 explicitly: still warn-only (only the literal string \"1\" opts in)" {
    export BATS_HARD_FAIL=0
    run _run_block fail
    unset BATS_HARD_FAIL
    [ "$status" -eq 0 ]
    [[ "$output" == *"LOG_WARN: BATS:"* ]]
}

@test "PM's own quality-gates.sh sets BATS_HARD_FAIL=1" {
    run grep -q '^BATS_HARD_FAIL=1$' "${REPO_ROOT}/scripts/quality-gates.sh"
    [ "$status" -eq 0 ]
}
