#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_slot_git_status_root_dirty_watchdog.bats — unit tests for check_dirty_root_repo()
# in slot-git-status-report.sh, the slot-0 (bare root checkout) dirty/untracked-files
# alert added to close
# plans/active/issues/bare_root_repo_agent_writes_unenforced_2026_08_21.md: a DIRTY
# verdict for a bare ${WORKSPACE_PATH}/<repo>/ checkout was previously passive
# telemetry only (post_snapshot to the dashboard, no page) -- this watchdog pages the
# same dedup-per-episode way check_starvation_for_slot/check_stash_pile_for_slot
# already do.
#
# HERMETIC: mirrors test_slot_git_status_auto_reconcile_wiring.bats's harness pattern
# -- resolve_token_for_slot and post_starve_ping are both stubbed inline in the
# sourced harness script, so no real curl call is ever made and no live orchestrator
# state (even a colocated one on :8765) is ever touched. check_dirty_root_repo is a
# pure leaf function (repo_name + a pre-built TSV row in, no filesystem repo-existence
# check of its own -- that already happened in the caller loop before it's invoked),
# so unlike the starvation/stash-pile wiring tests this needs no throwaway git repo on
# disk, just a hand-built row string.
#
# Run: bats tests/test_slot_git_status_root_dirty_watchdog.bats

REPORTER="unified-trading-pm/scripts/dev/slot-git-status-report.sh"

setup() {
    WS_ROOT="$(git rev-parse --show-toplevel)/.."
    cd "${WS_ROOT}" || cd ..
    REPORTER_ABS="$(cd "$(dirname "${REPORTER}")" && pwd)/$(basename "${REPORTER}")"
    EMPTY_WS="${BATS_TEST_TMPDIR}/empty_ws_$$_${RANDOM}"
    mkdir -p "${EMPTY_WS}/.tabs"

    PING_LOG="${BATS_TEST_TMPDIR}/pings.log"
    : > "${PING_LOG}"

    MARKER_DIR="${EMPTY_WS}/.tabs/.ff-starve-state"
    MARKER="${MARKER_DIR}/slot-0__some-repo.root-dirty-warn"
}

# TSV row builder matching classify_repo()'s 14-field order (see its own field-order
# comment above classify_repo() in the reporter script).
# $1=state $2=dirty_files $3=dirty_sample
_row() {
    printf 'some-repo\tlive-defi-rollout\t%s\t%s\t0\t0\tabc123\tlive-defi-rollout\t\t\t%s\t0\t\t' \
        "$1" "$2" "$3"
}

# $1 = TSV row  $2 = ROOT_DIRTY_WATCHDOG value ("1" default if empty)
# Deliberately NOT --quiet: check_dirty_root_repo's dedup-skip line uses log_quiet
# (mirrors check_starvation_for_slot's [starve-dup] / check_stash_pile_for_slot's
# [stash-warn-dup] convention exactly), which --quiet would suppress -- the dedup
# test below needs to observe it. Still fully hermetic: EMPTY_WS has zero repos, so
# the sourced script's own main loop only ever emits harmless [skip:empty] noise.
_run_check() {
    local row="$1" toggle="${2:-1}"
    local harness="${BATS_TEST_TMPDIR}/harness.sh"
    {
        echo "source '${REPORTER_ABS}' --workspace '${EMPTY_WS}'"
        echo "ROOT_DIRTY_WATCHDOG=${toggle}"
        echo "resolve_token_for_slot() { printf 'dummy-token'; return 0; }"
        echo "post_starve_ping() {"
        echo "  printf '%s\t%s\t%s\n' \"\$1\" \"\$2\" \"\$3\" >> '${PING_LOG}'"
        echo "  return 0"
        echo "}"
        printf "check_dirty_root_repo 'some-repo' %q\n" "${row}"
    } > "${harness}"
    bash "${harness}"
}

@test "slot-git-status-report.sh still has valid bash syntax after the root-dirty-watchdog change" {
    run bash -n "${REPORTER_ABS}"
    [ "$status" -eq 0 ]
}

@test "dirty row, no prior marker -> pages once, marker created" {
    run _run_check "$(_row dirty 2 'M  foo.py|?? bar.py')"
    [ "$status" -eq 0 ]
    [ -s "${PING_LOG}" ]
    [ -f "${MARKER}" ]
}

@test "dirty row payload names the repo, the file count, and the issue doc" {
    run _run_check "$(_row dirty 2 'M  foo.py|?? bar.py')"
    [ "$status" -eq 0 ]
    run cat "${PING_LOG}"
    [[ "$output" == *"BARE ROOT REPO DIRTY"* ]]
    [[ "$output" == *"some-repo"* ]]
    [[ "$output" == *"2 uncommitted"* ]]
    [[ "$output" == *"bare_root_repo_agent_writes_unenforced_2026_08_21.md"* ]]
}

@test "dirty row, marker already present -> dedup, no second ping" {
    mkdir -p "${MARKER_DIR}"
    : > "${MARKER}"
    run _run_check "$(_row dirty 1 'M  foo.py')"
    [ "$status" -eq 0 ]
    [[ "$output" == *"[root-dirty-dup]"* ]]
    [ ! -s "${PING_LOG}" ]
}

@test "clean row, prior marker present -> marker cleared, no ping" {
    mkdir -p "${MARKER_DIR}"
    : > "${MARKER}"
    run _run_check "$(_row clean 0 '')"
    [ "$status" -eq 0 ]
    [ ! -s "${PING_LOG}" ]
    [ ! -f "${MARKER}" ]
}

@test "ROOT_DIRTY_WATCHDOG=0 -> never pages even on a dirty row" {
    run _run_check "$(_row dirty 3 'M  x|M  y|?? z')" "0"
    [ "$status" -eq 0 ]
    [ ! -s "${PING_LOG}" ]
    [ ! -f "${MARKER}" ]
}
