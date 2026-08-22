#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_slot_git_status_bare_root_dirty_alert.bats — unit tests for check_bare_root_dirty_for_slot(),
# the slot-0 alert path wired into slot-git-status-report.sh
# (/plans/active/issues/bare_root_repo_agent_writes_unenforced_2026_08_21.md P1). Before this, a
# DIRTY verdict on a bare root (slot-0) repo was passive telemetry -- reported via post_snapshot
# only, never paged, unlike the numbered-slot loop's FF-starvation/stash-pile watchdogs.
#
# HERMETIC: mirrors test_slot_git_status_auto_reconcile_wiring.bats's sourcing pattern -- the real
# script is sourced with an EMPTY --workspace so its main slot-walking loop is a no-op, then
# check_bare_root_dirty_for_slot is called directly against hand-built TSV rows (the same shape
# classify_repo emits), with post_starve_ping + resolve_token_for_slot stubbed so no real network
# call happens.
#
# Run: bats tests/test_slot_git_status_bare_root_dirty_alert.bats

REPORTER="unified-trading-pm/scripts/dev/slot-git-status-report.sh"

setup() {
    WS_ROOT="$(git rev-parse --show-toplevel)/.."
    cd "${WS_ROOT}" || cd ..
    REPORTER_ABS="$(cd "$(dirname "${REPORTER}")" && pwd)/$(basename "${REPORTER}")"
    EMPTY_WS="${BATS_TEST_TMPDIR}/empty_ws_$$_${RANDOM}"
    mkdir -p "${EMPTY_WS}/.tabs"

    PING_LOG="${BATS_TEST_TMPDIR}/pings.log"
    : > "${PING_LOG}"

    # One dirty row + one clean row, in the exact 14-field TSV shape classify_repo emits.
    DIRTY_ROW=$'some-repo\tlive-defi-rollout\tdirty\t2\t0\t0\tabc123\tlive-defi-rollout\t2026-08-21T00:00:00Z\t\tM foo.py|?? bar.py\t0\t\t'
    CLEAN_ROW=$'clean-repo\tlive-defi-rollout\tclean\t0\t0\t0\tdef456\tlive-defi-rollout\t\t\t\t0\t\t'
    # SAME repo name as DIRTY_ROW, transitioned to clean -- for the marker-clear test, which needs
    # the marker's (slot, repo) key to actually match the row that goes clean.
    SAME_REPO_NOW_CLEAN_ROW=$'some-repo\tlive-defi-rollout\tclean\t0\t0\t0\tabc123\tlive-defi-rollout\t\t\t\t0\t\t'
}

# $1 = rows_tsv to pass to check_bare_root_dirty_for_slot
# $2 = extra harness lines (e.g. a pre-seeded marker), optional
_run_check() {
    local rows="$1"
    local harness="${BATS_TEST_TMPDIR}/harness.sh"
    {
        echo "source '${REPORTER_ABS}' --workspace '${EMPTY_WS}' --quiet"
        echo "resolve_token_for_slot() { printf 'dummy-token'; return 0; }"
        echo "post_starve_ping() {"
        echo "  printf '%s\t%s\t%s\t%s\n' \"\$1\" \"\$2\" \"\$3\" \"\$5\" >> '${PING_LOG}'"
        echo "  return 0"
        echo "}"
        printf 'check_bare_root_dirty_for_slot 0 %q\n' "${rows}"
    } > "${harness}"
    bash "${harness}"
}

@test "dirty bare-root repo pages once, with the [bare-root-dirty] label and repo/sample content" {
    run _run_check "${DIRTY_ROW}"

    [ "$status" -eq 0 ]
    [ -s "${PING_LOG}" ]
    run cat "${PING_LOG}"
    [[ "$output" == *"some-repo"* ]]
    [[ "$output" == *"bare-root-dirty"* ]]
    [[ "$output" == *"BARE-ROOT DIRTY"* ]]
    [[ "$output" == *"bar.py"* ]]

    marker="${EMPTY_WS}/.tabs/.ff-starve-state/slot-0__some-repo.bare-root-dirty"
    [ -f "${marker}" ]
}

@test "second consecutive DIRTY tick does not re-page (dedup-per-episode marker)" {
    run _run_check "${DIRTY_ROW}"
    [ "$status" -eq 0 ]
    [ -s "${PING_LOG}" ]

    : > "${PING_LOG}"
    run _run_check "${DIRTY_ROW}"

    [ "$status" -eq 0 ]
    [ ! -s "${PING_LOG}" ]      # no second ping was posted for the still-open episode
}

@test "repo goes clean again -> marker cleared, next DIRTY episode re-pages" {
    run _run_check "${DIRTY_ROW}"
    [ "$status" -eq 0 ]
    marker="${EMPTY_WS}/.tabs/.ff-starve-state/slot-0__some-repo.bare-root-dirty"
    [ -f "${marker}" ]

    run _run_check "${SAME_REPO_NOW_CLEAN_ROW}"
    [ "$status" -eq 0 ]
    [ ! -f "${marker}" ]

    : > "${PING_LOG}"
    run _run_check "${DIRTY_ROW}"
    [ "$status" -eq 0 ]
    [ -s "${PING_LOG}" ]
}

@test "clean repo never pages" {
    run _run_check "${CLEAN_ROW}"

    [ "$status" -eq 0 ]
    [ ! -s "${PING_LOG}" ]
}

@test "BARE_ROOT_DIRTY_WATCHDOG=0 disables the alert entirely" {
    local harness="${BATS_TEST_TMPDIR}/harness_off.sh"
    {
        echo "source '${REPORTER_ABS}' --workspace '${EMPTY_WS}' --quiet"
        echo "BARE_ROOT_DIRTY_WATCHDOG=0"
        echo "resolve_token_for_slot() { printf 'dummy-token'; return 0; }"
        echo "post_starve_ping() {"
        echo "  printf '%s\t%s\t%s\n' \"\$1\" \"\$2\" \"\$3\" >> '${PING_LOG}'"
        echo "  return 0"
        echo "}"
        printf 'check_bare_root_dirty_for_slot 0 %q\n' "${DIRTY_ROW}"
    } > "${harness}"
    run bash "${harness}"

    [ "$status" -eq 0 ]
    [ ! -s "${PING_LOG}" ]
}

@test "slot-git-status-report.sh still has valid bash syntax after the bare-root-dirty wiring change" {
    run bash -n "${REPORTER_ABS}"
    [ "$status" -eq 0 ]
}
