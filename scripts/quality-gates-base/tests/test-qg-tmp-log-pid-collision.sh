#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for the shared-host QG capture-file filename collision
# (shared_host_tmp_tmpfs_full_2026_07_26.md todo 2).
#
# Bug: base-service.sh's ~28 STEP 5.x checker-output captures redirected to a
# FIXED, non-PID-unique path (`${TMPDIR:-/tmp}/<name>_qg.log`, no `mktemp`/`$$`
# suffix). Two slots' concurrent `quality-gates.sh` runs on the same shared host
# hitting the SAME STEP at the same time collide on the identical filename — one
# process's write races the other's read, producing a spurious gate failure (or a
# gate reading the WRONG process's output) with no real content issue.
#
# Fix: every capture path is now `${TMPDIR:-/tmp}/<name>_qg.log.$$` ($$ = the
# invoking shell's PID, unique per concurrent run by OS guarantee), stored once in
# a local variable and reused for both the write and every paired read-back
# (`grep`/`cat`), then removed after use.
#
# This test EXTRACTS the REAL STEP 5.93 (canonical-model-regression) block from
# base-service.sh (not a replica — same technique as
# test-ratchet-exit-code-aggregation.sh / test-quickmerge-blocked-contract.sh) and
# asserts:
#   (a) two concurrent invocations of the CURRENT (fixed) block never cross-read
#       each other's capture file content, even when one process's write
#       deliberately overlaps the other's read window.
#   (b) the SAME concurrency scenario against a hand-built stand-in of the OLD
#       (pre-fix, fixed-filename) shape DOES cross-read — proving the fix is not
#       just cosmetic, it closes a real, reproducible race.
#   (c) none of the ~28 known capture-file names in base-service.sh appear as a
#       bare (non-`.$$`-suffixed) redirect target anywhere in the file.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-tmp-log-pid-collision.sh
set -euo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$(( PASS + 1 )); }
fail() { echo "FAIL: $*"; FAIL=$(( FAIL + 1 )); }

BASE_SERVICE="$(cd "$(dirname "$0")/.." && pwd)/base-service.sh"
[ -f "$BASE_SERVICE" ] || { echo "FATAL: base-service.sh not found at $BASE_SERVICE"; exit 2; }

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/qg_tmp_log_collision_test.XXXXXX")"
trap 'rm -rf "$WORK_DIR"' EXIT

# ── Extract the REAL, current STEP 5.93 block (from the `if [ -f ` guard through
#    its matching top-level `fi`) — same awk-extraction technique as the sibling
#    ratchet/quickmerge tests, so this test fails loudly if the shape ever moves.
#    Anchored to the `if` line (NOT the preceding `_CANON_MODEL_CHECKER=` assignment
#    above it) so the harness's own injected fake-checker path isn't immediately
#    clobbered by the block's real assignment when it runs.
FIXED_BLOCK=$(awk '
    /^if \[ -f "\$_CANON_MODEL_CHECKER" \]; then$/{start=1}
    start{print}
    start && /^fi$/{exit}
' "$BASE_SERVICE")
[ -n "$FIXED_BLOCK" ] || { echo "FATAL: could not extract STEP 5.93 block from base-service.sh"; exit 2; }
echo "$FIXED_BLOCK" | grep -q '\.\$\$"' \
    || { echo "FATAL: extracted block has no PID-suffixed capture var — extraction anchor is stale"; exit 2; }

# Minimal stubs for the log_* helpers the block calls (normally from qg-common.sh).
STUBS='log_fail() { echo "FAIL_MARK: $*"; }; log_success() { :; }; log_warn() { :; }'

# A fake "checker" that always exits 1 (so the interesting cat-the-capture-file
# read-back path runs) after writing an invocation-identifiable line and then
# sleeping — this deliberately widens the write/read window so a second
# concurrent invocation's write can land WHILE the first is still asleep, exactly
# the real shared-host timing this bug class hits (STEP N's redirect finishes,
# then a sibling process's STEP N redirect lands, THEN the first process reads
# back — the read sees the sibling's content instead of its own).
cat > "$WORK_DIR/fake_checker.sh" <<'EOF'
#!/usr/bin/env bash
echo "REGRESSION_FROM_${MARKER}"
sleep "${SLEEP_S:-0}"
exit 1
EOF
chmod +x "$WORK_DIR/fake_checker.sh"

run_invocation() {
    # $1=marker  $2=sleep_after_write_s  $3=out_file  $4=block (fixed or old-shape)
    local marker="$1" sleep_s="$2" out_file="$3" block="$4"
    bash -c "
        set -u
        ${STUBS}
        REPO_ROOT='$WORK_DIR'
        PROJECT_ROOT='$WORK_DIR/proj'
        SOURCE_DIR=''
        PYTHON_CMD='env MARKER=$marker SLEEP_S=$sleep_s bash'
        _CANON_MODEL_CHECKER='$WORK_DIR/fake_checker.sh'
        V=0
        ${block}
    " >"$out_file" 2>&1
}

# ── (a) CURRENT (fixed) block: PID-suffixed paths must not cross-read ──────────
# Process A writes, then sleeps 0.4s BEFORE its own read-back; Process B (no
# sleep) runs fully — including ITS OWN write+read — inside that window.
run_invocation "A" "0.4" "$WORK_DIR/fixed_a.out" "$FIXED_BLOCK" &
PID_A=$!
sleep 0.1
run_invocation "B" "0" "$WORK_DIR/fixed_b.out" "$FIXED_BLOCK" &
PID_B=$!
wait "$PID_A" "$PID_B" 2>/dev/null || true

a_ok=0; b_ok=0
grep -q 'REGRESSION_FROM_A' "$WORK_DIR/fixed_a.out" && ! grep -q 'REGRESSION_FROM_B' "$WORK_DIR/fixed_a.out" && a_ok=1
grep -q 'REGRESSION_FROM_B' "$WORK_DIR/fixed_b.out" && ! grep -q 'REGRESSION_FROM_A' "$WORK_DIR/fixed_b.out" && b_ok=1
if [ "$a_ok" -eq 1 ] && [ "$b_ok" -eq 1 ]; then
    pass "(a) current PID-suffixed block: two concurrent invocations each read back only their OWN capture"
else
    fail "(a) current block cross-read under concurrency (a_ok=$a_ok b_ok=$b_ok) — see $WORK_DIR/fixed_{a,b}.out"
fi

# ── (b) OLD (pre-fix) shape: hand-built stand-in of the fixed-filename pattern ──
# Same structure as the real block MINUS the PID suffix (exactly what every one
# of the ~28 sites looked like before this fix) — must demonstrably collide under
# the identical timing, proving (a) isn't a coincidence of the test harness.
OLD_BLOCK='
_CANON_MODEL_CHECKER="'"$WORK_DIR"'/fake_checker.sh"
if [ -f "$_CANON_MODEL_CHECKER" ]; then
    if $PYTHON_CMD "$_CANON_MODEL_CHECKER" >${TMPDIR:-/tmp}/canonical_model_regressions_qg.log 2>&1; then
        log_success "STEP 5.93: clean"
    else
        log_fail "STEP 5.93: NEW canonical-model regression:"
        cat ${TMPDIR:-/tmp}/canonical_model_regressions_qg.log
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.93: skipped"
fi
'
export TMPDIR="$WORK_DIR"
run_invocation "A" "0.4" "$WORK_DIR/old_a.out" "$OLD_BLOCK" &
PID_A=$!
sleep 0.1
run_invocation "B" "0" "$WORK_DIR/old_b.out" "$OLD_BLOCK" &
PID_B=$!
wait "$PID_A" "$PID_B" 2>/dev/null || true

if grep -q 'REGRESSION_FROM_B' "$WORK_DIR/old_a.out"; then
    pass "(b) OLD fixed-filename shape DOES cross-read under the identical timing (proves the fix is load-bearing, not cosmetic)"
else
    fail "(b) OLD-shape repro didn't reproduce a collision — the negative control failed, (a) above is not conclusive on its own; see $WORK_DIR/old_{a,b}.out"
fi

# ── (c) corpus sweep: no bare (non-.$$) literal redirect target remains ────────
# Two-step: first find FULL LINES containing the literal capture-path shape, then
# drop the ones that are a `_LOG="...".$$"` variable DEFINITION (the sanctioned
# shape) — filtering the matched substring alone (grep -o output) would never see
# the `_LOG="` prefix that lives earlier on the same line.
BARE_HITS=$(grep -nE '\$\{TMPDIR:-/tmp\}/[A-Za-z0-9_.]+_qg\.(log|err)\b' "$BASE_SERVICE" | grep -v '_LOG="\|_ERR_LOG="' || true)
if [ -z "$BARE_HITS" ]; then
    pass "(c) every _qg.log/_qg.err capture path in base-service.sh is confined to a PID-suffixed variable definition"
else
    fail "(c) bare (non-variable, non-PID-suffixed) capture path(s) remain: $BARE_HITS"
fi

echo
echo "── qg tmp-log PID-collision: $PASS passed, $FAIL failed ──"
[ "$FAIL" -eq 0 ]
