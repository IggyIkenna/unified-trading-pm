#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_slot_collision_detect_lsof_batching.bats — cursor-configs/hooks/lib/slot-collision-detect.sh
#
# Covers plans/active/issues/slot_collision_guard_bats_fails_open_under_host_load_2026_08_15.md
# todo 4: foreign_claude_pids() used to resolve each candidate pid's cwd with one `_cwd_of` call
# per pid, which falls back to spawning its own `lsof` subprocess whenever `/proc/<pid>/cwd` can't
# be read. Under host load that per-pid fork+exec cost is what pushed the detector past its 10s
# budget (measured load 48, then 164 — see the issue doc's "Mechanism" section). The fix:
# `_cwd_of_batch` resolves via /proc first (no subprocess) and batches everything /proc could not
# resolve into exactly ONE `lsof -p pid1,pid2,...` call, never one lsof call per leftover pid.
#
# Run: bats tests/test_slot_collision_detect_lsof_batching.bats

setup() {
    _SCD_PM_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    _SCD_LIB="${_SCD_PM_ROOT}/cursor-configs/hooks/lib/slot-collision-detect.sh"
    SCRATCH="${BATS_TEST_TMPDIR}/scratch"
    SLOT="${SCRATCH}/.tabs/77/unified-trading-pm"
    mkdir -p "${SLOT}"
    _PEER_PIDS=()
}

teardown() {
    local p
    for p in "${_PEER_PIDS[@]:-}"; do
        [ -n "${p}" ] && kill "${p}" 2>/dev/null || true
    done
}

# A counting `lsof` stub, first in PATH, that logs one line per invocation (with its full argv) to
# $LSOF_CALL_LOG and then execs the REAL lsof so the function under test still gets real output.
_install_counting_lsof_stub() {
    local real_lsof
    real_lsof="$(command -v lsof)"
    STUB_BIN="${BATS_TEST_TMPDIR}/stubbin"
    mkdir -p "${STUB_BIN}"
    LSOF_CALL_LOG="${BATS_TEST_TMPDIR}/lsof_calls.log"
    : >"${LSOF_CALL_LOG}"
    cat >"${STUB_BIN}/lsof" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >>"${LSOF_CALL_LOG}"
exec "${real_lsof}" "\$@"
EOF
    chmod +x "${STUB_BIN}/lsof"
    PATH="${STUB_BIN}:${PATH}"
}

@test "_cwd_of_batch resolves a live pid via /proc without ever spawning lsof" {
    # /proc is a Linux-only filesystem (2026-08-17) -- on macOS this test's own peer-wait loop
    # times out (nothing under /proc is ever readable) and _cwd_of_batch correctly falls back to
    # the lsof-batched path instead, which is the CORRECT cross-platform behavior, not a bug. This
    # test specifically validates the Linux-only /proc fast path, so it only applies where /proc
    # is real; the lsof-batched fallback path is covered cross-platform by the two neighbouring
    # tests below, which do not assume /proc succeeds.
    [ -r "/proc/$$/cwd" ] || skip "/proc/<pid>/cwd not readable on this host (non-Linux) -- /proc fast path N/A"
    source "${_SCD_LIB}"
    _install_counting_lsof_stub

    ( cd "${SLOT}" && exec -a claude-bats-fake-peer sleep 20 ) &
    _PEER_PIDS+=("$!")
    local peer="$!"
    # Wait until /proc genuinely reports the child's cwd (avoids a startup race).
    local deadline=$(( SECONDS + 5 ))
    while [ "${SECONDS}" -lt "${deadline}" ] && [ ! -r "/proc/${peer}/cwd" ]; do sleep 0.05; done

    run _cwd_of_batch "${peer}"
    [ "$status" -eq 0 ]
    [[ "$output" == "${peer} "* ]]
    [[ "$output" == *"${SLOT}"* ]]
    # The fast path resolved everything via /proc — lsof must not have run at all.
    [ ! -s "${LSOF_CALL_LOG}" ]
}

@test "_cwd_of_batch resolves N unreadable pids with exactly ONE lsof call, not N" {
    source "${_SCD_LIB}"
    _install_counting_lsof_stub

    # Pids that do not correspond to any real process: /proc/<pid>/cwd is unreadable for every one
    # of them, so all three land in the batched-lsof leftover path deterministically (no permission
    # trickery needed — a nonexistent pid fails the same readability check a permission-denied pid
    # would). What lsof reports about them is irrelevant to this test; call COUNT is the assertion.
    run _cwd_of_batch 999999991 999999992 999999993
    [ "$status" -eq 0 ]

    [ -s "${LSOF_CALL_LOG}" ]
    [ "$(wc -l <"${LSOF_CALL_LOG}")" -eq 1 ]
    run cat "${LSOF_CALL_LOG}"
    [[ "$output" == *"999999991,999999992,999999993"* ]]
}

@test "_cwd_of_batch with zero leftover pids never invokes lsof" {
    # Same /proc-only-on-Linux caveat as the test above -- this asserts the /proc fast path
    # resolved the CALLING process's own (always-live) pid with zero lsof calls, which is only
    # possible where /proc exists.
    [ -r "/proc/$$/cwd" ] || skip "/proc/<pid>/cwd not readable on this host (non-Linux) -- /proc fast path N/A"
    source "${_SCD_LIB}"
    _install_counting_lsof_stub

    run _cwd_of_batch "$$"
    [ "$status" -eq 0 ]
    [ ! -s "${LSOF_CALL_LOG}" ]
}

@test "foreign_claude_pids still finds a live peer through the batched path" {
    source "${_SCD_LIB}"

    ( cd "${SLOT}" && exec -a claude-bats-fake-peer sleep 20 ) &
    _PEER_PIDS+=("$!")
    local peer="$!"
    local deadline=$(( SECONDS + 10 ))
    local found=""
    while [ "${SECONDS}" -lt "${deadline}" ]; do
        found="$(foreign_claude_pids "${SLOT}")"
        [ -n "${found}" ] && break
        sleep 0.1
    done

    [[ "${found}" == *"${peer}"* ]]
}

# ── the pkill-guard PATH shim must not blind the detector ──────────────────
#
# unified-trading-pm@8df3df58a1 (2026-08-21) put scripts/hooks/pkill-guard-bin/ FIRST on PATH,
# shimming `pgrep` as well as `pkill` and REFUSING (exit 1, message on stderr, nothing on stdout)
# any invocation without a slot-specific discriminator. foreign_claude_pids' sweep is deliberately
# host-wide -- a peer occupying THIS slot is by construction outside our own process tree -- so the
# shim refused it on every invocation, `2>/dev/null` swallowed the refusal, and the detector
# reported "no collision" everywhere the shim was installed. Measured on slot 33, 2026-08-22.
#
# This test pins the fix INDEPENDENTLY of whether the real guard happens to be on PATH: it installs
# its own refusing shim, so it exercises the regression on a bare CI runner too (where the real
# guard dir is absent and the four tests that first caught this would otherwise pass vacuously).
@test "a refusing pgrep guard shim first on PATH does not blind foreign_claude_pids" {
    source "${_SCD_LIB}"

    local guard="${BATS_TEST_TMPDIR}/pkill-guard-bin"
    mkdir -p "${guard}"
    cat >"${guard}/pgrep" <<'EOF'
#!/usr/bin/env bash
echo "REFUSED: 'pgrep $*' lacks a slot-specific discriminator." >&2
exit 1
EOF
    chmod +x "${guard}/pgrep"
    PATH="${guard}:${PATH}"

    # Sanity: the shim really is what a bare `pgrep` now resolves to. (`run` merges stderr into
    # $output, so the refusal message lands there -- what matters is that no PIDs came back.)
    run pgrep -f claude
    [ "$status" -eq 1 ]
    [[ "$output" == *"REFUSED"* ]]

    ( cd "${SLOT}" && exec -a claude-bats-fake-peer sleep 20 ) &
    _PEER_PIDS+=("$!")
    local peer="$!"
    local deadline=$((SECONDS + 10))
    local found=""
    while [ "${SECONDS}" -lt "${deadline}" ]; do
        found="$(foreign_claude_pids "${SLOT}")"
        [ -n "${found}" ] && break
        sleep 0.1
    done

    [[ "${found}" == *"${peer}"* ]]
}
