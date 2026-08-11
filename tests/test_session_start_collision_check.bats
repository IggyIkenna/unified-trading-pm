#!/usr/bin/env bats
# test_session_start_collision_check.bats — tests for
# cursor-configs/hooks/session-start-collision-check.sh.
#
# Covers the 2026-08-11 portability fix: signal 2 (the live-process cwd
# scan) previously used ONLY /proc/<pid>/cwd + /proc/<pid>/status, which do
# not exist on macOS at all — so on Darwin (the host the real incident this
# hook exists to catch was measured on) it was a silent structural no-op,
# never actually detecting a peer process. The fix adds an `lsof`/`ps`
# fallback so the SAME signal fires on macOS too. These tests simulate a
# "peer session" with a real background process (argv0 renamed to contain
# "claude" so `pgrep -f claude` matches it, and its cwd pointed at a fake
# slot dir), which is the only way to exercise this hook's actual detection
# logic rather than just its arg-parsing.
#
# Never touches a real .tabs/<N> slot or a real .agent-claim.
#
# Run: bats tests/test_session_start_collision_check.bats

setup() {
    _SSC_PM_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    HOOK="${_SSC_PM_ROOT}/cursor-configs/hooks/session-start-collision-check.sh"
    SCRATCH="${BATS_TEST_TMPDIR}/scratch"
    SLOT="${SCRATCH}/.tabs/77/unified-trading-pm"
    mkdir -p "${SLOT}"
    _SSC_PEER_PIDS=()
}

teardown() {
    local p
    for p in "${_SSC_PEER_PIDS[@]:-}"; do
        [ -n "${p}" ] && kill "${p}" 2>/dev/null || true
    done
    tmux kill-session -t ssc-test-session 2>/dev/null || true
}

# Spawns a background process whose argv0 contains "claude" (so `pgrep -f
# claude` matches it) with its cwd set to $1. Appends its pid to
# _SSC_PEER_PIDS for teardown.
_spawn_fake_peer() {
    local cwd="$1"
    ( cd "${cwd}" && exec -a claude-bats-fake-peer sleep 20 ) &
    _SSC_PEER_PIDS+=("$!")
    # Give the process a moment to actually be scheduled + cwd resolvable.
    sleep 0.3
}

_run_hook() {
    local cwd_json="$1"
    printf '{"cwd": "%s"}' "${cwd_json}" | bash "${HOOK}"
}

# ── syntax + no-op paths ──────────────────────────────────────────────────

@test "session-start-collision-check.sh has valid bash syntax" {
    run bash -n "$HOOK"
    [ "$status" -eq 0 ]
}

@test "exits quietly (no output, exit 0) for a cwd outside any .tabs/<N>" {
    run _run_hook "${SCRATCH}/not-a-slot"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "exits quietly when inside a real .tabs/<N> with no peer and no claim file" {
    run _run_hook "${SLOT}"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "never exits non-zero even when it warns (WARN-only contract)" {
    _spawn_fake_peer "${SLOT}"
    run _run_hook "${SLOT}"
    [ "$status" -eq 0 ]
}

# ── signal 2: live cwd scan (the portability fix) ─────────────────────────

@test "detects a live foreign process whose cwd is INSIDE the slot dir" {
    _spawn_fake_peer "${SLOT}"
    run _run_hook "${SLOT}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"SLOT COLLISION WARNING"* ]]
    [[ "$output" == *"live process"* ]]
}

@test "does NOT warn about a live claude-named process whose cwd is a DIFFERENT slot" {
    local other_slot="${SCRATCH}/.tabs/88/unified-trading-pm"
    mkdir -p "${other_slot}"
    _spawn_fake_peer "${other_slot}"
    run _run_hook "${SLOT}"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "warning names the slot dir and points at the per-tab-worktrees model" {
    _spawn_fake_peer "${SLOT}"
    run _run_hook "${SLOT}"
    [[ "$output" == *"${SCRATCH}/.tabs/77"* ]]
    [[ "$output" == *"WARNING ONLY"* ]]
}

# ── signal 1: .agent-claim liveness ────────────────────────────────────────

@test "a claim file with a DEAD tmux session produces no warning from signal 1" {
    command -v jq >/dev/null 2>&1 || skip "jq not installed"
    printf '{"tmux_session":"ssc-test-does-not-exist","operator":"test","role":"worker"}' \
        >"${SCRATCH}/.tabs/77/.agent-claim"
    run _run_hook "${SLOT}"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "a claim file with a LIVE matching tmux session warns via signal 1" {
    command -v jq >/dev/null 2>&1 || skip "jq not installed"
    command -v tmux >/dev/null 2>&1 || skip "tmux not installed"
    tmux new-session -d -s ssc-test-session 2>/dev/null || skip "could not start a tmux session in this environment"
    printf '{"tmux_session":"ssc-test-session","operator":"test","role":"worker"}' \
        >"${SCRATCH}/.tabs/77/.agent-claim"
    run _run_hook "${SLOT}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"agent-claim"* ]]
    [[ "$output" == *"ssc-test-session"* ]]
}

# ── graceful degradation ───────────────────────────────────────────────────

@test "falls back to plain-text output when jq is unavailable (curated PATH, no jq)" {
    _spawn_fake_peer "${SLOT}"
    # Build a minimal PATH containing everything the hook needs EXCEPT jq —
    # excluding jq's own directory wholesale (rather than filtering it out
    # of $PATH) would also drop any co-located tool (tmux lives next to jq
    # in /usr/local/bin on this host), breaking the very signals under test.
    local fakebin tool p
    fakebin="${BATS_TEST_TMPDIR}/fakebin"
    mkdir -p "${fakebin}"
    for tool in pgrep lsof ps awk readlink tmux cat tr; do
        p="$(command -v "${tool}" 2>/dev/null)" || continue
        ln -sf "${p}" "${fakebin}/${tool}"
    done
    # Without jq the hook can't parse the stdin JSON payload at all (by
    # design — that parse itself is jq-gated), so it falls back to
    # $CLAUDE_PROJECT_DIR / $PWD for START_CWD rather than the JSON cwd.
    run env PATH="${fakebin}" CLAUDE_PROJECT_DIR="${SLOT}" "$(command -v bash)" "${HOOK}" </dev/null
    [ "$status" -eq 0 ]
    [[ "$output" == *"SLOT COLLISION WARNING"* ]]
    # No jq on PATH -> plain text, not the hookSpecificOutput JSON envelope.
    [[ "$output" != *"hookSpecificOutput"* ]]
}
