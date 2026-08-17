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
