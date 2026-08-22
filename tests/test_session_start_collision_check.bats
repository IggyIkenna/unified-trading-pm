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
    # Unique per-test session name (pm_bats_tmux_fixture_leak_wedges_shared_host_2026_08_10 recurrence):
    # the old hardcoded "ssc-test-session" name collided across concurrent bats runs (parallel -j jobs,
    # or multiple slots on the shared host running this same suite at once) all sharing the user's
    # DEFAULT tmux socket -- one run's teardown could kill a DIFFERENT run's just-created session of the
    # same name, or its `has-session` check could race a peer's kill-session, producing exactly the
    # observed "not ok ... [[ \"$output\" == *\"agent-claim\"* ]] failed" (the hook found no live session
    # to warn about because a peer run had already torn it down).
    SSC_TMUX_SESSION="ssc-test-session-$$-${RANDOM}"
    # DEDICATED tmux socket per test, exported so the hook subprocess spawned by _run_hook resolves the
    # SAME socket -- mirrors tests/test_slot_git_status_claim_heartbeat.bats's fix for the identical bug
    # class. SHORT path, deliberately NOT nested under BATS_TEST_TMPDIR: a unix socket path is capped at
    # ~104 bytes by sockaddr_un.sun_path, and BATS_TEST_TMPDIR can already be close to that on its own.
    export TMUX_TMPDIR="${TMPDIR:-/tmp}/ssct.$$.${RANDOM}"
    mkdir -p "${TMUX_TMPDIR}"
}

# Every fixture tmux call is timeout-bounded -- on a loaded shared host the tmux server can stop
# responding and the client spins instead of returning (measured 2026-08-10, see the issue doc cited
# above). A bounded call FAILS THE TEST rather than hanging the runner.
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
    local p
    for p in "${_SSC_PEER_PIDS[@]:-}"; do
        [ -n "${p}" ] && kill "${p}" 2>/dev/null || true
    done
    _tmux kill-session -t "=${SSC_TMUX_SESSION:-ssc-test-session}" 2>/dev/null || true
    # Belt-and-braces: the socket is per-test, so killing the server releases every session on it
    # wholesale -- a session name this teardown forgot cannot outlive the test or leak onto the shared
    # default socket.
    _tmux kill-server 2>/dev/null || true
    [ -n "${TMUX_TMPDIR:-}" ] && rm -rf "${TMUX_TMPDIR}" 2>/dev/null || true
}

# Spawns a background process whose argv0 contains "claude" (so `pgrep -f
# claude` matches it) with its cwd set to $1. Appends its pid to
# _SSC_PEER_PIDS for teardown.
_spawn_fake_peer() {
    local cwd="$1"
    ( cd "${cwd}" && exec -a claude-bats-fake-peer sleep 20 ) &
    local pid="$!"
    _SSC_PEER_PIDS+=("${pid}")
    # Poll until the detector's OWN cwd resolution (lsof on macOS -- no /proc) actually reports
    # this peer as foreign-in-slot, instead of a fixed sleep. Under real host contention
    # (`pgrep -f claude` matching dozens+ real processes, one `lsof -p` call per match) that
    # resolution can take far longer than 0.3s, or fail outright for a given PID on a given
    # pass -- the detector is deliberately fail-open on failure, so a fixed-sleep test races the
    # same timing variance the production hook is exposed to and intermittently asserts against
    # a peer that isn't lsof-visible yet (see slot-collision-detect.sh's foreign_claude_pids).
    # Bounded at 5s; falls through to let the assertion fail with a clear signal rather than hang.
    local detect_lib="${_SSC_PM_ROOT}/cursor-configs/hooks/lib/slot-collision-detect.sh"
    local waited=0
    while [ "${waited}" -lt 50 ]; do
        if bash "${detect_lib}" foreign-pids "${cwd}" 2>/dev/null | grep -qx "${pid}"; then
            return 0
        fi
        sleep 0.1
        waited=$((waited + 1))
    done
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
    _tmux new-session -d -s "${SSC_TMUX_SESSION}" 2>/dev/null || skip "could not start a tmux session in this environment"
    printf '{"tmux_session":"%s","operator":"test","role":"worker"}' "${SSC_TMUX_SESSION}" \
        >"${SCRATCH}/.tabs/77/.agent-claim"
    run _run_hook "${SLOT}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"agent-claim"* ]]
    [[ "$output" == *"${SSC_TMUX_SESSION}"* ]]
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
        # `command -v pgrep` resolves to scripts/hooks/pkill-guard-bin/pgrep -- a WRAPPER that
        # `source`s ../pkill-guard.sh relative to its own location. Symlinked into ${fakebin} that
        # relative source has nothing to find, so the link would be a wrapper that fails outright
        # rather than the tool this fixture means to provide. Take the first PATH match that is NOT
        # a guard wrapper, mirroring slot-collision-detect.sh's own _real_pgrep resolution.
        p=""
        while read -r _p_cand; do
            case "${_p_cand}" in */pkill-guard-bin/*) continue ;; esac
            p="${_p_cand}"
            break
        done < <(type -aP "${tool}" 2>/dev/null)
        [ -n "${p}" ] || continue
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
