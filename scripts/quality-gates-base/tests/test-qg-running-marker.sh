#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for the running-PID marker in base-service.sh (_QG_RUNNING_MARKER),
# added by plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md
# (P2, "optional hardening"): a worker that needs to self-kill its OWN stuck
# quality-gates.sh run should have an exact, cwd-scoped PID handle instead of ever
# reaching for a name-based `pkill -f quality-gates.sh` (host-wide, not slot-scoped —
# the exact incident that issue doc exists to prevent).
#
# WHY a byte-identical inline copy, not `source base-service.sh`: base-service.sh is a
# top-to-bottom script (running the full gate as a side effect of being sourced), so
# actually sourcing it here would run ruff/pytest/basedpyright etc. Mirrors the existing
# convention in test-trap-release.sh: install a byte-identical copy of the block under
# test in a fresh subprocess and assert on its observable effects (the marker file).
#
# Covers:
#   1. Marker is written on start, with correct pid=/repo=/cwd= fields
#   2. Marker is removed by the exit handler on a PASS exit
#   3. Marker is removed by the exit handler on a FAIL exit (every exit path, not just happy path)
#   4. Marker filename is scoped by PID (two concurrent "runs" get two distinct markers,
#      each in its own process — the mechanism a worker actually greps/kills by)
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-running-marker.sh
set -uo pipefail

LTMP="$(mktemp -d)"
trap 'rm -rf "$LTMP"' EXIT
FAILS=0
LEDGER_DIR="$LTMP/.benchmarks/qg-governor"

# run_scenario <outcome: pass|fail> <service_name> <extra_sleep_seconds>
# Runs the marker-write + exit-handler block (byte-identical to base-service.sh) in a
# fresh process so PIDs are real and distinct. Writes the child PID to stdout.
run_scenario() {
    OUTCOME="$1" SVC="$2" SLEEP_S="${3:-0}" LEDGER_DIR="$LEDGER_DIR" \
    bash -c '
        set -uo pipefail
        SERVICE_NAME="$SVC"
        PROJECT_ROOT="/fake/repo/$SVC"
        _qg_ledger_dir() { echo "$LEDGER_DIR"; }

        # ── byte-identical to base-service.sh: exit-handler marker cleanup ──
        _qg_exit_handler() {
            local rc=$?
            [ -n "${_QG_RUNNING_MARKER:-}" ] && rm -f "$_QG_RUNNING_MARKER" 2>/dev/null || true
            return 0
        }
        trap "_qg_exit_handler" EXIT

        # ── byte-identical to base-service.sh: running-PID marker write ──
        _QG_RUNNING_MARKER_DIR="$(command -v _qg_ledger_dir >/dev/null 2>&1 && _qg_ledger_dir || echo "${WORKSPACE_ROOT:-.}/.benchmarks/qg-governor")"
        mkdir -p "$_QG_RUNNING_MARKER_DIR" 2>/dev/null || true
        _QG_RUNNING_MARKER="${_QG_RUNNING_MARKER_DIR}/running.$$"
        {
            echo "pid=$$"
            echo "repo=${SERVICE_NAME:-unknown}"
            echo "cwd=${PROJECT_ROOT:-$(pwd)}"
            echo "started_at_epoch=$(date +%s 2>/dev/null || echo 0)"
        } > "$_QG_RUNNING_MARKER" 2>/dev/null || true

        echo "$$"
        [ "$SLEEP_S" -gt 0 ] 2>/dev/null && sleep "$SLEEP_S"
        [ "$OUTCOME" = fail ] && exit 1
        exit 0
    ' 2>/dev/null
}

eq() { if [[ "$2" == "$3" ]]; then echo "PASS: $1"; else echo "FAIL: $1 — expected '$2' got '$3'"; FAILS=$((FAILS+1)); fi; }

# 1+2. PASS exit: marker existed mid-run with correct fields, then removed on exit.
# (Assert content via a slept scenario captured mid-run, then a fast one to check cleanup.)
bash -c '
    LEDGER_DIR="'"$LEDGER_DIR"'"
    _qg_ledger_dir() { echo "$LEDGER_DIR"; }
    SERVICE_NAME="svc-slow"
    PROJECT_ROOT="/fake/repo/svc-slow"
    _qg_exit_handler() { local rc=$?; [ -n "${_QG_RUNNING_MARKER:-}" ] && rm -f "$_QG_RUNNING_MARKER" 2>/dev/null || true; return 0; }
    trap "_qg_exit_handler" EXIT
    _QG_RUNNING_MARKER_DIR="$(_qg_ledger_dir)"
    mkdir -p "$_QG_RUNNING_MARKER_DIR" 2>/dev/null || true
    _QG_RUNNING_MARKER="${_QG_RUNNING_MARKER_DIR}/running.$$"
    { echo "pid=$$"; echo "repo=${SERVICE_NAME}"; echo "cwd=${PROJECT_ROOT}"; echo "started_at_epoch=$(date +%s)"; } > "$_QG_RUNNING_MARKER"
    echo "$$" > "'"$LTMP"'/slow_pid"
    sleep 2
' &
BGPID=$!
# Poll for the child's real PID (echoed to file) instead of a fixed sleep.
for _ in 1 2 3 4 5 6 7 8 9 10; do
    [[ -f "$LTMP/slow_pid" ]] && break
    sleep 0.2
done
SLOW_PID="$(cat "$LTMP/slow_pid" 2>/dev/null || echo "")"
MARKER="$LEDGER_DIR/running.$SLOW_PID"

marker_exists_midrun=false
[[ -n "$SLOW_PID" && -f "$MARKER" ]] && marker_exists_midrun=true
eq "1. marker exists while process is running" "true" "$marker_exists_midrun"

if [[ "$marker_exists_midrun" == "true" ]]; then
    got_pid="$(grep '^pid=' "$MARKER" | cut -d= -f2)"
    got_repo="$(grep '^repo=' "$MARKER" | cut -d= -f2)"
    got_cwd="$(grep '^cwd=' "$MARKER" | cut -d= -f2)"
    eq "1b. marker pid= matches the real PID" "$SLOW_PID" "$got_pid"
    eq "1c. marker repo= matches SERVICE_NAME" "svc-slow" "$got_repo"
    eq "1d. marker cwd= matches PROJECT_ROOT" "/fake/repo/svc-slow" "$got_cwd"
fi

wait "$BGPID" 2>/dev/null
marker_exists_after_exit=false
[[ -f "$MARKER" ]] && marker_exists_after_exit=true
eq "2. marker removed by exit handler after PASS exit" "false" "$marker_exists_after_exit"

# 3. FAIL exit also cleans up the marker (every exit path, not just happy path).
FAIL_PID=$(run_scenario fail svc-fail 0)
FAIL_MARKER="$LEDGER_DIR/running.$FAIL_PID"
fail_marker_gone=false
[[ ! -f "$FAIL_MARKER" ]] && fail_marker_gone=true
eq "3. marker removed by exit handler after FAIL exit" "true" "$fail_marker_gone"

# 4. Two concurrent "runs" get two distinct PID-scoped markers (never colliding).
(
    LEDGER_DIR="$LEDGER_DIR" SERVICE_NAME="svc-a" PROJECT_ROOT="/fake/repo/svc-a" \
    bash -c '
        _qg_ledger_dir() { echo "$LEDGER_DIR"; }
        _QG_RUNNING_MARKER_DIR="$(_qg_ledger_dir)"; mkdir -p "$_QG_RUNNING_MARKER_DIR"
        _QG_RUNNING_MARKER="${_QG_RUNNING_MARKER_DIR}/running.$$"
        { echo "pid=$$"; echo "repo=svc-a"; } > "$_QG_RUNNING_MARKER"
        echo "$$" > "'"$LTMP"'/a_pid"
        sleep 1.5
    ' &
)
(
    LEDGER_DIR="$LEDGER_DIR" SERVICE_NAME="svc-b" PROJECT_ROOT="/fake/repo/svc-b" \
    bash -c '
        _qg_ledger_dir() { echo "$LEDGER_DIR"; }
        _QG_RUNNING_MARKER_DIR="$(_qg_ledger_dir)"; mkdir -p "$_QG_RUNNING_MARKER_DIR"
        _QG_RUNNING_MARKER="${_QG_RUNNING_MARKER_DIR}/running.$$"
        { echo "pid=$$"; echo "repo=svc-b"; } > "$_QG_RUNNING_MARKER"
        echo "$$" > "'"$LTMP"'/b_pid"
        sleep 1.5
    ' &
)
for _ in 1 2 3 4 5 6 7 8 9 10; do
    [[ -f "$LTMP/a_pid" && -f "$LTMP/b_pid" ]] && break
    sleep 0.2
done
A_PID="$(cat "$LTMP/a_pid" 2>/dev/null || echo "")"
B_PID="$(cat "$LTMP/b_pid" 2>/dev/null || echo "")"
distinct_and_present=false
if [[ -n "$A_PID" && -n "$B_PID" && "$A_PID" != "$B_PID" \
      && -f "$LEDGER_DIR/running.$A_PID" && -f "$LEDGER_DIR/running.$B_PID" ]]; then
    distinct_and_present=true
fi
eq "4. two concurrent runs get distinct PID-scoped markers" "true" "$distinct_and_present"
wait 2>/dev/null

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
