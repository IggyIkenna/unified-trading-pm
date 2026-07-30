#!/usr/bin/env bats
# test_qg_mem_wrap_typecheck_retry.bats — unit tests for the [4] TYPE CHECK MEM_WRAP
#   TOCTOU-retry fix in scripts/quality-gates-base/base-service.sh.
#
# SSOT: plans/active/issues/qg_mem_wrap_systemd_bus_unavailable_2026_07_26.md
#
# The retry logic (_qg_run_basedpyright_attempt() + the MEM_WRAP-failure detector that
# follows it) is REPLICATED here rather than sourcing the 4000-line base-service.sh
# directly (which requires a full repo checkout, SOURCE_DIR, SERVICE_NAME, and dozens of
# other QG-only globals to even parse past its own preflight) — same tradeoff
# test_quickmerge_dep_tier_gate.bats already documents for quickmerge.sh's STAGE 1.7.
# To catch the replica drifting from the real script, the "sync guard" tests below grep
# base-service.sh for the exact literal markers this replica depends on; keep both in
# sync when editing either.
#
# HERMETIC: uses only tmpdir + a fake systemd-run/basedpyright on PATH — no real git ops,
# no network, no real basedpyright invocation.
# Run: bats tests/test_qg_mem_wrap_typecheck_retry.bats
# Run all bats: bats tests/

_BASE_SERVICE_SH="$(dirname "$BATS_TEST_DIRNAME")/scripts/quality-gates-base/base-service.sh"

# ── replica of run_timeout (qg-common.sh) — only the GNU-timeout branch is needed here ──
run_timeout() {
    local secs=$1; shift
    if command -v timeout &>/dev/null; then timeout "$secs" "$@"
    else "$@"; fi
}

# ── replica of base-service.sh [4] TYPE CHECK's retry logic ─────────────────────────────
_qg_run_basedpyright_attempt() {
    run_timeout "${PYRIGHT_TIMEOUT:-120}" "$@" "$BASEDPYRIGHT_CMD" "$SOURCE_DIR/" > "$_bp_out" 2>&1 &
    BP_PID=$!
    PYRIGHT_EXIT=0; wait $BP_PID || PYRIGHT_EXIT=$?
    PYRIGHT_OUT=$(cat "$_bp_out" 2>/dev/null); rm -f "$_bp_out"
    ERROR_COUNT=$(echo "$PYRIGHT_OUT" | grep -c " error:" || :)
    WARN_COUNT=$(echo "$PYRIGHT_OUT" | grep -c " warning:" || :)
}

_qg_typecheck_with_retry() {
    _bp_out="${BATS_TEST_TMPDIR}/bp_out.$$"
    _qg_run_basedpyright_attempt "${MEM_WRAP[@]}"
    if [ "${PYRIGHT_EXIT}" -ne 0 ] && [ "${ERROR_COUNT:-0}" -eq 0 ] && [ "${WARN_COUNT:-0}" -eq 0 ] \
        && [ "${#MEM_WRAP[@]}" -gt 0 ] \
        && { [ -z "$PYRIGHT_OUT" ] || echo "$PYRIGHT_OUT" | grep -q "Failed to connect to bus"; }; then
        MEM_WRAP_RETRY_FIRED=1
        _qg_run_basedpyright_attempt
    fi
}

# ── fixtures ──────────────────────────────────────────────────────────────────────────

setup() {
    FAKE_BIN="${BATS_TEST_TMPDIR}/fakebin"
    mkdir -p "$FAKE_BIN"
    export SYSTEMD_RUN_CALLS="${BATS_TEST_TMPDIR}/systemd_run_calls"
    export BASEDPYRIGHT_CALLS="${BATS_TEST_TMPDIR}/basedpyright_calls"
    : > "$SYSTEMD_RUN_CALLS"
    : > "$BASEDPYRIGHT_CALLS"

    # Fake systemd-run: FAKE_SYSTEMD_RUN_MODE=bus_down simulates the D-Bus TOCTOU race
    # (dies before ever exec'ing the wrapped command); =working simulates a healthy
    # systemd-run that execs through to whatever follows "--".
    cat > "${FAKE_BIN}/systemd-run" <<'SH'
#!/usr/bin/env bash
echo x >> "$SYSTEMD_RUN_CALLS"
if [ "${FAKE_SYSTEMD_RUN_MODE:-bus_down}" = "bus_down" ]; then
    echo "Failed to connect to bus: No medium found" >&2
    exit 1
fi
while [ "$#" -gt 0 ]; do
    arg="$1"; shift
    [ "$arg" = "--" ] && break
done
exec "$@"
SH
    chmod +x "${FAKE_BIN}/systemd-run"

    # Fake basedpyright: FAKE_BP_MODE selects success | errors | hang_empty.
    BASEDPYRIGHT_CMD="${FAKE_BIN}/basedpyright"
    cat > "$BASEDPYRIGHT_CMD" <<'SH'
#!/usr/bin/env bash
echo x >> "$BASEDPYRIGHT_CALLS"
case "${FAKE_BP_MODE:-success}" in
    success)    echo "0 errors, 0 warnings"; exit 0 ;;
    errors)     echo "src/foo.py:1:1 - error: bad type"; exit 1 ;;
    hang_empty) exit 1 ;;
esac
SH
    chmod +x "$BASEDPYRIGHT_CMD"

    MEM_WRAP_RETRY_FIRED=0
    PYRIGHT_TIMEOUT=5
    SOURCE_DIR="${BATS_TEST_TMPDIR}"
    PATH="${FAKE_BIN}:${PATH}"
    export FAKE_SYSTEMD_RUN_MODE=bus_down
    export FAKE_BP_MODE=success
}

# ── syntax ────────────────────────────────────────────────────────────────────────────

@test "base-service.sh has valid bash syntax" {
    run bash -n "$_BASE_SERVICE_SH"
    [ "$status" -eq 0 ]
}

# ── sync guard: the real script still contains the markers this replica assumes ─────────

@test "sync guard: _qg_run_basedpyright_attempt is defined in base-service.sh" {
    run grep -cF '_qg_run_basedpyright_attempt() {' "$_BASE_SERVICE_SH"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}

@test "sync guard: MEM_WRAP TOCTOU retry detects a D-Bus connection failure" {
    run grep -cF 'Failed to connect to bus' "$_BASE_SERVICE_SH"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}

@test "sync guard: retry log line distinguishes MEM_WRAP failure from a timeout" {
    run grep -cF 'MEM_WRAP launch failed, retried unwrapped' "$_BASE_SERVICE_SH"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}

@test "sync guard: retry only fires when MEM_WRAP is non-empty" {
    run grep -cF '${#MEM_WRAP[@]}' "$_BASE_SERVICE_SH"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}

# ── behavior: MEM_WRAP TOCTOU recovery ───────────────────────────────────────────────────

@test "D-Bus down on first (wrapped) attempt recovers via unwrapped retry" {
    export FAKE_SYSTEMD_RUN_MODE=bus_down
    export FAKE_BP_MODE=success
    MEM_WRAP=(systemd-run --user --scope -p MemoryMax=10G -p MemorySwapMax=0 --quiet --)

    _qg_typecheck_with_retry

    [ "$PYRIGHT_EXIT" -eq 0 ]
    [ "$ERROR_COUNT" -eq 0 ]
    [ "$WARN_COUNT" -eq 0 ]
    [ "$MEM_WRAP_RETRY_FIRED" -eq 1 ]
    [ "$(wc -l < "$SYSTEMD_RUN_CALLS")" -eq 1 ]
    [ "$(wc -l < "$BASEDPYRIGHT_CALLS")" -eq 1 ]
}

@test "unwrapped host (MEM_WRAP empty) does not retry on a real empty failure" {
    export FAKE_BP_MODE=hang_empty
    MEM_WRAP=()

    _qg_typecheck_with_retry

    [ "$PYRIGHT_EXIT" -ne 0 ]
    [ "$ERROR_COUNT" -eq 0 ]
    [ "$WARN_COUNT" -eq 0 ]
    [ "$MEM_WRAP_RETRY_FIRED" -eq 0 ]
    [ "$(wc -l < "$SYSTEMD_RUN_CALLS")" -eq 0 ]
    [ "$(wc -l < "$BASEDPYRIGHT_CALLS")" -eq 1 ]
}

@test "genuine basedpyright errors (not a MEM_WRAP failure) are reported, not retried" {
    export FAKE_SYSTEMD_RUN_MODE=working
    export FAKE_BP_MODE=errors
    MEM_WRAP=(systemd-run --user --scope -p MemoryMax=10G -p MemorySwapMax=0 --quiet --)

    _qg_typecheck_with_retry

    [ "$PYRIGHT_EXIT" -ne 0 ]
    [ "$ERROR_COUNT" -eq 1 ]
    [ "$MEM_WRAP_RETRY_FIRED" -eq 0 ]
    [ "$(wc -l < "$SYSTEMD_RUN_CALLS")" -eq 1 ]
    [ "$(wc -l < "$BASEDPYRIGHT_CALLS")" -eq 1 ]
}

@test "still fails after the unwrapped retry stops at exactly one retry (no infinite loop)" {
    export FAKE_SYSTEMD_RUN_MODE=bus_down
    export FAKE_BP_MODE=hang_empty
    MEM_WRAP=(systemd-run --user --scope -p MemoryMax=10G -p MemorySwapMax=0 --quiet --)

    _qg_typecheck_with_retry

    [ "$PYRIGHT_EXIT" -ne 0 ]
    [ "$ERROR_COUNT" -eq 0 ]
    [ "$WARN_COUNT" -eq 0 ]
    [ "$MEM_WRAP_RETRY_FIRED" -eq 1 ]
    [ "$(wc -l < "$SYSTEMD_RUN_CALLS")" -eq 1 ]
    [ "$(wc -l < "$BASEDPYRIGHT_CALLS")" -eq 1 ]
}
