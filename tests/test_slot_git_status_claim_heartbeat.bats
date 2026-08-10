#!/usr/bin/env bats
# test_slot_git_status_claim_heartbeat.bats — unit tests for refresh_agent_claim_heartbeat()
# in slot-git-status-report.sh
#   (multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md candidate
#    fix 1: a live heartbeat on .agent-claim, unblocked by operator ruling 2026-08-08).
#
# HERMETIC: builds a throwaway .agent-claim JSON under BATS_TEST_TMPDIR; never touches a real
# slot's claim file. Uses REAL, short-lived tmux sessions (killed in teardown) rather than
# mocking `tmux has-session`, so the exact-match `-t "=<name>"` target behaviour (the
# slot-1-vs-slot-10 prefix-collision guard tmux_spawn.exact_target() exists for) is exercised
# for real, not assumed. Mirrors tests/test_slot_git_status_dirty_count.bats's hermetic-source
# pattern: source the real script with --workspace pointed at an EMPTY .tabs/ dir + --quiet, so
# the main slot-walking loop is a no-op and never POSTs anything real, then call the function
# under test directly.
#
# Run: bats tests/test_slot_git_status_claim_heartbeat.bats
# Run all: bats tests/

REPORTER="unified-trading-pm/scripts/dev/slot-git-status-report.sh"

setup() {
    WS_ROOT="$(git rev-parse --show-toplevel)/.."
    cd "${WS_ROOT}" || cd ..
    REPORTER_ABS="$(cd "$(dirname "${REPORTER}")" && pwd)/$(basename "${REPORTER}")"
    EMPTY_WS="${BATS_TEST_TMPDIR}/empty_ws_$$_${RANDOM}"
    mkdir -p "${EMPTY_WS}/.tabs"
    SLOT_DIR="${BATS_TEST_TMPDIR}/slot_$$_${RANDOM}/"
    mkdir -p "${SLOT_DIR}"
    # Unique per-test session name so parallel bats runs never collide with each other
    # or with a real orch-slot-* session on the host.
    TMUX_SESSION="bats-claim-hb-test-$$-${RANDOM}"
}

teardown() {
    tmux kill-session -t "=${TMUX_SESSION}" 2>/dev/null || true
}

# Portable mtime-as-epoch-seconds (2026-08-09: `stat -c %Y` is GNU-only and fails with
# "illegal option -- c" on macOS BSD stat -- the production script under test here
# (slot-git-status-report.sh) already has this exact fallback as stat_mtime_epoch(); this
# test-local copy mirrors it rather than sourcing the reporter script for just this helper).
_stat_mtime_epoch() {
    stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null || true
}

_write_claim() {
    local session="$1"
    cat > "${SLOT_DIR}.agent-claim" <<EOF
{"agent_id": "slot99-worker-test", "slot_id": 99, "role": "worker", "model": "sonnet",
 "operator": "test", "tmux_session": "${session}", "spawned_at": "2026-01-01T00:00:00Z",
 "expires_at": "2026-01-01T01:00:00Z"}
EOF
}

_heartbeat() {
    bash -c '
        source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --quiet
        refresh_agent_claim_heartbeat 99 "'"${SLOT_DIR}"'"
    '
}

@test "no .agent-claim file -> no-op, exits 0" {
    run _heartbeat
    [ "$status" -eq 0 ]
}

@test "claim present, tmux session alive -> mtime advances" {
    tmux new-session -d -s "${TMUX_SESSION}" 2>/dev/null
    _write_claim "${TMUX_SESSION}"
    # Force an old mtime so a later touch is unambiguously detectable.
    touch -t 202001010000 "${SLOT_DIR}.agent-claim"
    before=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")

    run _heartbeat
    [ "$status" -eq 0 ]
    [[ "$output" == *"[claim-heartbeat]"* ]]
    after=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")
    [ "${after}" -gt "${before}" ]
}

@test "claim present, tmux session dead -> mtime untouched" {
    _write_claim "no-such-session-${RANDOM}"
    touch -t 202001010000 "${SLOT_DIR}.agent-claim"
    before=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")

    run _heartbeat
    [ "$status" -eq 0 ]
    [[ "$output" == *"[claim-heartbeat:stale]"* ]]
    after=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")
    [ "${after}" -eq "${before}" ]
}

@test "claim present, malformed JSON -> no-op, no crash" {
    printf 'not json at all' > "${SLOT_DIR}.agent-claim"
    touch -t 202001010000 "${SLOT_DIR}.agent-claim"
    before=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")

    run _heartbeat
    [ "$status" -eq 0 ]
    after=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")
    [ "${after}" -eq "${before}" ]
}

@test "exact-match target: a live SUFFIX-colliding session name does not falsely heartbeat" {
    # slot-1-vs-slot-10 style guard: a claim naming session "orch-slot-1" must not be
    # satisfied by a live session actually named "orch-slot-10" (bare -t prefix-matches;
    # exact_target()'s "=" form must not).
    LONG_SESSION="${TMUX_SESSION}-longer-suffix"
    tmux new-session -d -s "${LONG_SESSION}" 2>/dev/null
    _write_claim "${TMUX_SESSION}"
    touch -t 202001010000 "${SLOT_DIR}.agent-claim"
    before=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")

    run _heartbeat
    [ "$status" -eq 0 ]
    [[ "$output" == *"[claim-heartbeat:stale]"* ]]
    after=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")
    [ "${after}" -eq "${before}" ]

    tmux kill-session -t "=${LONG_SESSION}" 2>/dev/null || true
}
