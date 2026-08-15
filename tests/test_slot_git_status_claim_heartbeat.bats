#!/usr/bin/env bats
# test_slot_git_status_claim_heartbeat.bats — unit tests for refresh_agent_claim_heartbeat()
# in slot-git-status-report.sh
#   (multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md candidate
#    fix 1: a live heartbeat on .agent-claim, unblocked by operator ruling 2026-08-08).
#
# HERMETIC: builds a throwaway .agent-claim JSON under BATS_TEST_TMPDIR; never touches a real
# slot's claim file. Mirrors tests/test_slot_git_status_dirty_count.bats's hermetic-source
# pattern: source the real script with --workspace pointed at an EMPTY .tabs/ dir + --quiet, so
# the main slot-walking loop is a no-op and never POSTs anything real, then call the function
# under test directly.
#
# INJECTABLE (pm_bats_tmux_fixture_leak_wedges_shared_host_2026_08_10.md P2 todo): the
# production script factors the tmux liveness check into its own
# `_claim_heartbeat_session_alive()` function specifically so a test can redefine it after
# sourcing. The common alive/dead cases below stub that function and never touch a real tmux
# server at all — no `tmux new-session`, nothing that can spin or leak under a loaded host.
# Only the "exact-match target" case below is a genuine integration test: it exists to prove
# tmux's own `-t "=<name>"` exact-match behaviour (the slot-1-vs-slot-10 prefix-collision guard
# tmux_spawn.exact_target() exists for), which a stub cannot exercise — it is tagged
# `integration,tmux` so it stays selectable/excludable via `bats --filter-tags` even though the
# fleet's current bats invocation runs the whole suite untagged.
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
    # DEDICATED tmux socket per test (pm_bats_tmux_fixture_leak_wedges_shared_host_2026_08_10):
    # these fixtures used to run on the user's DEFAULT socket, right alongside the real
    # orch-slot-* sessions, so a leaked fixture session was indistinguishable from live fleet
    # state and simply accumulated. 41 were found on the orchestrator VM on 2026-08-10 (oldest
    # 29h) helping fill its 8 GiB /tmp tmpfs to 100%, at which point tmux_spawn.spawn started
    # failing with [Errno 28] and EVERY escalation dispatch died and re-queued.
    # Exported, not passed as `tmux -L`: the script under test is invoked as a subprocess by
    # _heartbeat and inherits this, so both sides resolve the SAME socket without production
    # code needing a test-only socket flag.
    #
    # SHORT path, deliberately NOT nested under BATS_TEST_TMPDIR (which is the obvious choice and
    # is wrong): a unix socket path is capped at ~104 bytes by sockaddr_un.sun_path, and on macOS
    # BATS_TEST_TMPDIR is already ~90 (`/var/folders/<...>/bats-run-XXXXXX/test/N`) before tmux
    # appends its own `tmux-<uid>/default`. Nesting there fails every session with
    # "error connecting to ... (File name too long)". The dir holds one socket, is torn down
    # below, and any survivor is swept by tmpfs-disk-cleanup.timer.
    export TMUX_TMPDIR="${TMPDIR:-/tmp}/bth.$$.${RANDOM}"
    mkdir -p "${TMUX_TMPDIR}"
}

# Every fixture tmux call is timeout-bounded. On a loaded shared host the tmux server can stop
# responding and the client spins instead of returning — measured 2026-08-10 with 8 clients at
# 75-94% CPU each (~7 of the box's 10 cores), which is what made this suite able to wedge the
# whole host. A bounded call FAILS THE TEST rather than hanging the runner.
# `timeout` is GNU coreutils; macOS ships it only as `gtimeout` (same portability shape as
# _stat_mtime_epoch below), and a host with neither still runs, just unbounded.
_tmux() {
    if command -v timeout >/dev/null 2>&1; then
        timeout 10 tmux "$@"
    elif command -v gtimeout >/dev/null 2>&1; then
        gtimeout 10 tmux "$@"
    else
        tmux "$@"
    fi
}

teardown() {
    # BOTH session names, and in teardown rather than at the end of a test body. The
    # "-longer-suffix" session used to be killed on the LAST LINE of its own @test, so any
    # earlier assertion failure leaked it permanently — and every one of the 41 sessions found
    # leaked on the orchestrator VM was a `*-longer-suffix`. bats runs teardown unconditionally,
    # including after a failed assertion, which is the property that fixes this.
    _tmux kill-session -t "=${TMUX_SESSION}" 2>/dev/null || true
    _tmux kill-session -t "=${TMUX_SESSION}-longer-suffix" 2>/dev/null || true
    # Belt-and-braces: the socket is per-test, so killing the server releases every session on it
    # wholesale — a session name this teardown forgot cannot outlive the test.
    _tmux kill-server 2>/dev/null || true
    [ -n "${TMUX_TMPDIR:-}" ] && rm -rf "${TMUX_TMPDIR}" 2>/dev/null || true
}

# Portable mtime-as-epoch-seconds (2026-08-09: `stat -c %Y` is GNU-only and fails with
# "illegal option -- c" on macOS BSD stat -- the production script under test here
# (slot-git-status-report.sh) already has this exact fallback as stat_mtime_epoch(); this
# test-local copy mirrors it rather than sourcing the reporter script for just this helper).
#
# 2026-08-13: an `||`-chained `stat -f %m ... || stat -c %Y ...` (as below, formerly) is NOT
# equivalent to the production script's `uname`-based branch on Linux -- GNU coreutils'
# `-f` means "report FILESYSTEM info", not "custom format" (that's BSD-only; GNU's format
# flag is `-c`). `stat -f %m FILE` on GNU therefore treats `%m` and FILE as two separate
# file OPERANDS, fails on the nonexistent `%m` operand (nonzero exit -> the `||` fallback
# DOES fire) but has already written filesystem-info output for the real operand to stdout
# first -- command substitution captures both commands' stdout across the whole `||` chain,
# so the captured value was contaminated multi-line garbage on Linux, not a clean integer.
# `[ "${after}" -gt "${before}" ]` then failed with "integer expression expected" (status 2,
# not a real mtime-comparison failure) -- 100% deterministic on every GitHub Actions run
# (Linux) while always passing on a macOS dev machine, found live 2026-08-13 contributing to
# a 12+ hour block of every PM promote-PR QG slice. Mirror the production script's actual
# `uname`-gated branch instead of an exit-code-only `||` chain.
_stat_mtime_epoch() {
    if [[ "$(uname -s)" == "Darwin" ]]; then
        stat -f %m "$1" 2>/dev/null || true
    else
        stat -c %Y "$1" 2>/dev/null || true
    fi
}

_write_claim() {
    local session="$1"
    cat > "${SLOT_DIR}.agent-claim" <<EOF
{"agent_id": "slot99-worker-test", "slot_id": 99, "role": "worker", "model": "sonnet",
 "operator": "test", "tmux_session": "${session}", "spawned_at": "2026-01-01T00:00:00Z",
 "expires_at": "2026-01-01T01:00:00Z"}
EOF
}

# stub_mode: "alive" | "dead" | "" (real tmux, only the exact-match integration test uses this).
# Each invocation is a fresh `bash -c` subshell (mirrors the real per-tick reporter run), so the
# stub redefinition has to be injected into that same subshell string, after the source and
# before the call under test.
_heartbeat() {
    local stub_mode="${1:-}" stub_def=""
    case "${stub_mode}" in
        alive) stub_def='_claim_heartbeat_session_alive() { return 0; }' ;;
        dead) stub_def='_claim_heartbeat_session_alive() { return 1; }' ;;
        *) stub_def="" ;;
    esac
    bash -c '
        source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --quiet
        '"${stub_def}"'
        refresh_agent_claim_heartbeat 99 "'"${SLOT_DIR}"'"
    '
}

@test "no .agent-claim file -> no-op, exits 0" {
    run _heartbeat
    [ "$status" -eq 0 ]
}

@test "claim present, tmux session alive -> mtime advances" {
    # Stubbed liveness — no real tmux server spawned (this is the injectable path the
    # pm_bats_tmux_fixture_leak_wedges_shared_host_2026_08_10.md P2 todo asked for).
    _write_claim "${TMUX_SESSION}"
    # Force an old mtime so a later touch is unambiguously detectable.
    touch -t 202001010000 "${SLOT_DIR}.agent-claim"
    before=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")

    run _heartbeat "alive"
    [ "$status" -eq 0 ]
    [[ "$output" == *"[claim-heartbeat]"* ]]
    after=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")
    [ "${after}" -gt "${before}" ]
}

@test "claim present, tmux session dead -> mtime untouched" {
    # Stubbed liveness — no real tmux server spawned.
    _write_claim "no-such-session-${RANDOM}"
    touch -t 202001010000 "${SLOT_DIR}.agent-claim"
    before=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")

    run _heartbeat "dead"
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

# bats test_tags=integration,tmux
@test "exact-match target: a live SUFFIX-colliding session name does not falsely heartbeat" {
    # slot-1-vs-slot-10 style guard: a claim naming session "orch-slot-1" must not be
    # satisfied by a live session actually named "orch-slot-10" (bare -t prefix-matches;
    # exact_target()'s "=" form must not).
    LONG_SESSION="${TMUX_SESSION}-longer-suffix"
    _tmux new-session -d -s "${LONG_SESSION}" 2>/dev/null
    _write_claim "${TMUX_SESSION}"
    touch -t 202001010000 "${SLOT_DIR}.agent-claim"
    before=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")

    run _heartbeat
    [ "$status" -eq 0 ]
    [[ "$output" == *"[claim-heartbeat:stale]"* ]]
    after=$(_stat_mtime_epoch "${SLOT_DIR}.agent-claim")
    [ "${after}" -eq "${before}" ]
    # NOTE: no kill here — teardown() owns it now. An in-body kill is skipped whenever an
    # assertion above fails, which is exactly how this session leaked 41 times on the AO VM.
}
