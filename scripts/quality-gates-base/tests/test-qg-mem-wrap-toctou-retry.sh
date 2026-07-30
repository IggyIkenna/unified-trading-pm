#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Smoke tests for qg_mem_wrap_systemd_bus_unavailable_2026_07_26.md's fix: base-service.sh's [4]
# TYPE CHECK step retries basedpyright ONCE unwrapped when the wrapped (MEM_WRAP) invocation looks
# like a systemd-run/D-Bus launch failure (empty output, nonzero exit) rather than a genuine
# basedpyright timeout/error.
#
# Extracts the live [4] TYPE CHECK block from base-service.sh (same sed-line-range technique as
# test-qg-mem-cap.sh) and exercises it against a fake `basedpyright` binary whose behavior is
# controlled via a state file, so the FIRST invocation (simulating the MEM_WRAP-wrapped call
# TOCTOU-racing a transient D-Bus outage) can fail with empty output while a SECOND invocation
# (simulating the unwrapped retry) succeeds — proving the retry path recovers and reports the real
# result, and does not fire at all for a genuine type-check failure/timeout.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-mem-wrap-toctou-retry.sh
set -uo pipefail

PASS=0
FAIL=0
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

HERE="$(cd "$(dirname "$0")/.." && pwd)"
BASE_SERVICE="$HERE/base-service.sh"

# The live [4] TYPE CHECK block, from the first basedpyright invocation through the
# "Type check FAILED/timeout" exit (excludes the zero-baseline/warning-policy tail below it,
# which this fix doesn't touch). Anchored on stable, unlikely-to-drift markers rather than a
# hardcoded line range, so a future unrelated edit above this block doesn't silently desync the test.
TYPE_CHECK_BLOCK=$(sed -n '/^    _bp_out="\${TMPDIR:-\/tmp}\/bp_out\.\$\$"$/,/log_fail "Type check FAILED\/timeout/p' "$BASE_SERVICE")
if [ -z "$TYPE_CHECK_BLOCK" ]; then
    echo "FATAL: could not extract the [4] TYPE CHECK block from $BASE_SERVICE — anchors drifted?" >&2
    exit 2
fi

# Fake `basedpyright` driven by a counter file: 1st call (simulating the MEM_WRAP-wrapped
# invocation racing a D-Bus outage) emits nothing and exits 1; 2nd call (the unwrapped retry)
# succeeds with clean output.
make_fake_basedpyright_toctou() {
    local bin="$1/basedpyright"
    local counter="$1/calls"
    printf '0' > "$counter"
    cat > "$bin" << FAKE
#!/bin/bash
n=\$(cat "$counter")
n=\$((n + 1))
echo "\$n" > "$counter"
if [ "\$n" -eq 1 ]; then
    exit 1
fi
echo "0 errors, 0 warnings"
exit 0
FAKE
    chmod +x "$bin"
    echo "$bin"
}

# Fake `basedpyright` that ALWAYS fails with a real (non-empty) type-error output — must NOT
# trigger a retry (ERROR_COUNT > 0, so the MEM_WRAP-launch-failure shape doesn't match).
make_fake_basedpyright_real_error() {
    local bin="$1/basedpyright"
    cat > "$bin" << 'FAKE'
#!/bin/bash
echo "foo.py:1:1 - error: real type error"
exit 1
FAKE
    chmod +x "$bin"
    echo "$bin"
}

run_block() {
    local basedpyright_cmd="$1" mem_wrap_len="$2"
    (
        cd "$WORKDIR" || exit 2
        # shellcheck source=/dev/null
        source "$HERE/qg-common.sh" 2>/dev/null || true
        log_warn() { echo "WARN: $1"; }
        log_success() { echo "SUCCESS: $1"; }
        log_fail() { echo "FAIL_LOG: $1"; }
        BASEDPYRIGHT_CMD="$basedpyright_cmd"
        SOURCE_DIR="."
        SERVICE_NAME="test"
        PYRIGHT_TIMEOUT=10
        if [ "$mem_wrap_len" -gt 0 ]; then
            MEM_WRAP=(env)  # a no-op wrapper standing in for systemd-run in this harness
        else
            MEM_WRAP=()
        fi
        eval "$TYPE_CHECK_BLOCK"
        echo "FINAL_EXIT=${PYRIGHT_EXIT}"
        echo "FINAL_ERRORS=${ERROR_COUNT}"
    )
}

# ── Test (a): MEM_WRAP-launch-failure shape (empty 1st output) → retry recovers ──────────────
FAKE_DIR_A=$(mktemp -d)
BP_A=$(make_fake_basedpyright_toctou "$FAKE_DIR_A")
OUT_A=$(run_block "$BP_A" 1 2>&1)
if echo "$OUT_A" | grep -q "retrying ONCE unwrapped" && echo "$OUT_A" | grep -q "unwrapped retry recovered" && echo "$OUT_A" | grep -q "FINAL_EXIT=0"; then
    pass "(a) MEM_WRAP TOCTOU shape: detected, retried unwrapped, recovered (exit=0)"
else
    fail "(a) MEM_WRAP TOCTOU shape: expected detect+retry+recover, got:
$OUT_A"
fi
rm -rf "$FAKE_DIR_A"

# ── Test (b): genuine type error (non-empty error output) → no retry, exits 1 as before ──────
FAKE_DIR_B=$(mktemp -d)
BP_B=$(make_fake_basedpyright_real_error "$FAKE_DIR_B")
OUT_B=$(run_block "$BP_B" 1 2>&1)
if ! echo "$OUT_B" | grep -q "retrying ONCE unwrapped"; then
    pass "(b) genuine type error: retry path did NOT fire (ERROR_COUNT>0 correctly excludes it)"
else
    fail "(b) genuine type error: retry path incorrectly fired for a real error:
$OUT_B"
fi

# ── Test (c): MEM_WRAP empty (no wrapper active) → retry path never considered ────────────────
FAKE_DIR_C=$(mktemp -d)
BP_C=$(make_fake_basedpyright_toctou "$FAKE_DIR_C")
OUT_C=$(run_block "$BP_C" 0 2>&1)
if ! echo "$OUT_C" | grep -q "retrying ONCE unwrapped"; then
    pass "(c) MEM_WRAP empty: retry path never considered (no wrapper to race against)"
else
    fail "(c) MEM_WRAP empty: retry path incorrectly fired with no MEM_WRAP active:
$OUT_C"
fi
rm -rf "$FAKE_DIR_C"

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "MEM_WRAP TOCTOU-retry smoke tests: ALL ${PASS} PASSED"
    exit 0
else
    echo "MEM_WRAP TOCTOU-retry smoke tests: ${PASS} passed, ${FAIL} FAILED"
    exit 1
fi
