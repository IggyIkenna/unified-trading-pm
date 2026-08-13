#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Self-test for run-bounded-analysis.sh's memory-cap enforcement, especially the
# macOS/BSD fallback path (no systemd, no /proc, no setsid) — codified 2026-08-12 after
# confirming the ORIGINAL script silently enforced NOTHING on any macOS host (setsid
# doesn't exist there at all, so the RSS-poll fallback's own launch line failed outright
# and every run fell through to "fully UNWRAPPED, advisory only" without saying so loudly
# enough to notice). This test exists so that regression is impossible to miss: it asserts
# a real over-cap allocation is actually killed, not just that the script exits 0.
#
# Run: bash unified-trading-pm/scripts/dev/test-run-bounded-analysis.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$SCRIPT_DIR/run-bounded-analysis.sh"
FAILS=0

pass() { echo "PASS: $1"; }
fail() {
    echo "FAIL: $1"
    FAILS=$((FAILS + 1))
}

# --- Test 1: an over-cap allocation is actually killed (exit 137 = SIGKILL) -------------
out="$(ANALYSIS_MEM_CAP=50M ANALYSIS_POLL_INTERVAL_S=1 bash "$TARGET" -- python3 -c "
import time
data = bytearray(200 * 1024 * 1024)
time.sleep(5)
print('SHOULD_NOT_PRINT')
" 2>&1)"
rc=$?
if [[ "$rc" -eq 137 ]] && [[ "$out" != *SHOULD_NOT_PRINT* ]]; then
    pass "over-cap allocation killed (exit 137, never reached its own completion print)"
else
    fail "over-cap allocation NOT killed as expected (rc=$rc, output: $out)"
fi

# --- Test 2: a real enforcement mechanism actually engaged (not silently advisory-only) -
if [[ "$out" == *"RSS-poll cap"* ]]; then
    pass "RSS-poll cap mechanism reported as active (not silently advisory-only)"
elif [[ "$out" == *"cgroup mem cap active"* ]]; then
    pass "cgroup mem cap mechanism reported as active"
else
    fail "no real enforcement mechanism reported active — this is the exact silent-degrade regression this test guards against: $out"
fi

# --- Test 3: an under-cap run completes normally, unwrapped correctness preserved -------
out2="$(ANALYSIS_MEM_CAP=200M bash "$TARGET" -- python3 -c "
data = bytearray(20 * 1024 * 1024)
print('COMPLETED_OK', len(data))
" 2>&1)"
rc2=$?
if [[ "$rc2" -eq 0 ]] && [[ "$out2" == *"COMPLETED_OK 20971520"* ]]; then
    pass "under-cap allocation completes normally (exit 0, real output preserved)"
else
    fail "under-cap allocation did not complete normally (rc=$rc2, output: $out2)"
fi

# --- Test 4: macOS-class host (no /proc) uses the `ps`-based RSS reader, not /proc ------
if [[ ! -d /proc ]]; then
    if [[ "$out" == *"source: ps"* ]]; then
        pass "no /proc on this host and RSS source correctly reports 'ps', not /proc"
    else
        fail "no /proc on this host but RSS source didn't report 'ps' — regression: $out"
    fi
else
    echo "SKIP: /proc present on this host (Linux) — the ps-fallback-selection assertion only applies on macOS/BSD"
fi

echo ""
if [[ "$FAILS" -eq 0 ]]; then
    echo "ALL PASSED"
    exit 0
else
    echo "$FAILS test(s) FAILED"
    exit 1
fi
