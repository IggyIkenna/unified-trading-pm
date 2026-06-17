#!/usr/bin/env bash
# Regression test for the QG hard-gate exit-code aggregation.
#
# Bug (qg_base_service_ratchet_exit_code_2026_06_11.md): $V is the violation
# counter but it was CHECKED ONLY at the codex-compliance verdict. Every STEP
# below it (the 5.7x/5.9x ratchets — fallback-imports 5.94, DTZ/TID251 5.95, …)
# still did `V=$(( V + 1 ))` on failure, but $V was never re-evaluated → a red
# ratchet step fell through to "ALL QUALITY GATES PASSED" and wrote the sentinel
# (a hollow green gate). Fix: snapshot $V right after the codex verdict
# (_V_PRE_RATCHET), then a final HARD-GATE AGGREGATION VERDICT fails the run if
# any later step incremented it, placed BEFORE the ci_status write + the sentinel.
#
# This test extracts the ACTUAL fix code from base-service.sh (not a replica) and
# asserts:
#   (a) a planted post-snapshot V increment → the verdict exits 1
#   (b) no post-snapshot increment → the verdict falls through (exit 0)
#   (c) the verdict is positioned BEFORE the sentinel + ci_status writes (so a
#       failure suppresses both)
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-ratchet-exit-code-aggregation.sh
set -euo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$(( PASS + 1 )); }
fail() { echo "FAIL: $*"; FAIL=$(( FAIL + 1 )); }

BASE_SERVICE="$(cd "$(dirname "$0")/.." && pwd)/base-service.sh"
[ -f "$BASE_SERVICE" ] || { echo "FATAL: base-service.sh not found at $BASE_SERVICE"; exit 2; }

# Extract the real verdict block (from the _RATCHET_FAILS= line through its closing `fi`).
VERDICT_BLOCK=$(awk '/^_RATCHET_FAILS=\$\(\( V - _V_PRE_RATCHET \)\)/{c=1} c{print} c&&/^fi$/{exit}' "$BASE_SERVICE")
[ -n "$VERDICT_BLOCK" ] || { echo "FATAL: could not extract HARD-GATE AGGREGATION VERDICT block from base-service.sh"; exit 2; }

# Minimal stubs for the log_* helpers the block calls (normally from qg-common.sh).
STUBS='log_fail() { echo "FAIL_MARK: $*"; }; log_success() { :; }; log_ok() { :; }; log_warn() { :; }'

# ── (a) planted post-snapshot failure must exit 1 ─────────────────────────────
set +e
out_a=$(bash -c "
    set -u
    ${STUBS}
    V=0
    _V_PRE_RATCHET=\$V         # snapshot (as base-service.sh does right after the codex verdict)
    V=\$(( V + 1 ))            # a ratchet step (e.g. STEP 5.94) fails after the snapshot
    ${VERDICT_BLOCK}
    echo 'REACHED_SENTINEL'    # stands in for the success banner + sentinel write
" 2>&1)
rc_a=$?
set -e
if [ "$rc_a" -ne 0 ] && ! grep -q 'REACHED_SENTINEL' <<<"$out_a" && grep -q 'FAIL_MARK' <<<"$out_a"; then
    pass "(a) planted post-snapshot failure → exit $rc_a, did NOT reach sentinel, emitted failure"
else
    fail "(a) planted failure not gated (rc=$rc_a, out=$out_a)"
fi

# ── (b) clean run (no post-snapshot increment) must fall through (exit 0) ──────
set +e
out_b=$(bash -c "
    set -u
    ${STUBS}
    V=2                        # codex-tolerated soft violations (e.g. CODEX_MAX_VIOLATIONS)
    _V_PRE_RATCHET=\$V         # snapshot: V==_V_PRE_RATCHET → no hard-gate failure
    ${VERDICT_BLOCK}
    echo 'REACHED_SENTINEL'
" 2>&1)
rc_b=$?
set -e
if [ "$rc_b" -eq 0 ] && grep -q 'REACHED_SENTINEL' <<<"$out_b"; then
    pass "(b) no post-snapshot increment → exit 0, reached sentinel (codex tolerance preserved)"
else
    fail "(b) clean run wrongly gated (rc=$rc_b, out=$out_b)"
fi

# ── (c) the verdict must sit BEFORE the ci_status write + the sentinel write ───
# Fixed-string greps (the verdict line contains `$((` which BRE would mis-parse);
# `|| true` so a no-match never trips `set -e` before the assertion runs.
verdict_ln=$(grep -nF '_RATCHET_FAILS=$(( V - _V_PRE_RATCHET ))' "$BASE_SERVICE" | head -1 | cut -d: -f1 || true)
cistatus_ln=$(grep -nF '_qg_update_ci_status_pass' "$BASE_SERVICE" | head -1 | cut -d: -f1 || true)
sentinel_ln=$(grep -nF 'git rev-parse HEAD > "${PROJECT_ROOT}/.qg_last_passed_sha"' "$BASE_SERVICE" | head -1 | cut -d: -f1 || true)
snapshot_ln=$(grep -nF '_V_PRE_RATCHET=$V' "$BASE_SERVICE" | head -1 | cut -d: -f1 || true)
if [ -n "$snapshot_ln" ] && [ -n "$verdict_ln" ] && [ -n "$cistatus_ln" ] && [ -n "$sentinel_ln" ] \
   && [ "$snapshot_ln" -lt "$verdict_ln" ] \
   && [ "$verdict_ln" -lt "$cistatus_ln" ] \
   && [ "$verdict_ln" -lt "$sentinel_ln" ]; then
    pass "(c) ordering: snapshot($snapshot_ln) < verdict($verdict_ln) < ci_status($cistatus_ln) & sentinel($sentinel_ln)"
else
    fail "(c) verdict mis-positioned (snapshot=$snapshot_ln verdict=$verdict_ln ci_status=$cistatus_ln sentinel=$sentinel_ln)"
fi

echo
echo "── ratchet exit-code aggregation: $PASS passed, $FAIL failed ──"
[ "$FAIL" -eq 0 ]
