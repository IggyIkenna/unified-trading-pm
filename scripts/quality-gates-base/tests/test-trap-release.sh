#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for the exit-trap governor release in base-service.sh
# (_qg_exit_handler), added by
# plans/active/qg_host_adaptive_resource_governor_2026_07_14.md.
#
# WHY: the happy-path qg_governor_release runs only after [4] TYPECHECK. A run that
# FAILS or is aborted between qg_governor_acquire and that point never reaches it and
# would leak a reservation-ledger entry (correctness is fine — every admission decision
# sweeps dead PIDs first — but the ledger stays dirty until the next acquirer's sweep).
# Releasing from the EXIT trap covers every exit path. This test proves:
#   1. OLD handler (no trap release) + reservation-mode FAIL exit  → entry LEAKS   (the bug)
#   2. NEW handler (trap release)  + reservation-mode FAIL exit    → ledger CLEAN  (the fix)
#   3. NEW handler + happy-path release already called + trap fires → no double-free, CLEAN
#   4. NEW handler + never acquired (sentinel path)                → trap release is a no-op
#   5. NEW handler + TOKEN mode FAIL exit                          → no error, no ledger entry
#   6. exit code is PRESERVED across the trap (fail→1, pass→0): `return 0` must be inert
#
# Each scenario runs as its OWN bash process (acquire keys the ledger on $$, so distinct
# PIDs are required); the parent then greps the RAW ledger for that now-dead PID (a
# sweeping accessor would reap a leak and mask it).
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-trap-release.sh
set -uo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
LTMP="$(mktemp -d)"
trap 'rm -rf "$LTMP"' EXIT
FAILS=0
PIDFILE="$LTMP/childpid"

# run_scenario <mode> <outcome: fail|pass|sentinel> <handler: old|new>
# Runs the scenario in a fresh process. Echoes nothing; writes the child PID to $PIDFILE
# and returns the child's exit code (so the caller can assert exit-code preservation).
run_scenario() {
    MODE="$1" OUTCOME="$2" HANDLER="$3" LTMP="$LTMP" GOV="$GOV" PIDFILE="$PIDFILE" \
    bash -c '
        set -uo pipefail
        export QG_GOVERNOR_MODE="$MODE"
        export WORKSPACE_ROOT="$LTMP/.tabs/1"          # shared root strips /.tabs/* → $LTMP
        export SERVICE_NAME="traptest-repo"
        export QG_UNMEASURED_PEAK_MB=500               # trivial peak → always admits
        export QG_FORCE_MEM_TOTAL_KB=67108864          # 64 GB
        export QG_FORCE_MEM_AVAIL_KB=62914560          # 60 GB
        export QG_FORCE_CORES=16
        mkdir -p "$WORKSPACE_ROOT"
        echo "$$" > "$PIDFILE"
        _qg_update_ci_status_failing() { :; }          # base-service stub (not under test here)
        # shellcheck source=/dev/null
        source "$GOV"
        # Install the handler variant under test — byte-identical to base-service.sh.
        if [ "$HANDLER" = new ]; then
            _qg_exit_handler() {
                local rc=$?
                if command -v qg_governor_release >/dev/null 2>&1; then qg_governor_release 2>/dev/null || true; fi
                [ "$rc" -ne 0 ] && _qg_update_ci_status_failing 2>/dev/null || true
                return 0
            }
        else
            _qg_exit_handler() { local rc=$?; [ "$rc" -ne 0 ] && _qg_update_ci_status_failing 2>/dev/null || true; }
        fi
        trap "_qg_exit_handler" EXIT
        [ "$OUTCOME" = sentinel ] || qg_governor_acquire     # sentinel path never acquires
        [ "$OUTCOME" = pass ] && qg_governor_release         # happy-path release, THEN trap also fires
        case "$OUTCOME" in fail) exit 1 ;; *) exit 0 ;; esac
    ' >/dev/null 2>&1
    return $?
}

# ledger_has_pid <pid> — true if the RAW ledger still lists this (now-dead) pid
ledger_has_pid() {
    local led="$LTMP/.benchmarks/qg-governor/reservations"
    [[ -f "$led" ]] && grep -q "^${1} " "$led"
}

assert_leaked()  { if ledger_has_pid "$(cat "$PIDFILE")"; then echo "PASS: $1 (entry present as expected)"; else echo "FAIL: $1 — expected a leaked entry, ledger was clean"; FAILS=$((FAILS+1)); fi; }
assert_clean()   { if ledger_has_pid "$(cat "$PIDFILE")"; then echo "FAIL: $1 — LEAKED entry $(cat "$PIDFILE") still in ledger"; FAILS=$((FAILS+1)); else echo "PASS: $1 (ledger clean)"; fi; }
assert_rc()      { if [ "$2" = "$3" ]; then echo "PASS: $1 (exit rc=$3)"; else echo "FAIL: $1 — expected rc$2 got rc$3"; FAILS=$((FAILS+1)); fi; }

if ! command -v flock >/dev/null 2>&1; then echo "SKIP: flock(1) absent — governor runs ungoverned on this host"; exit 0; fi

# 1. OLD handler, reservation FAIL → demonstrates the leak the fix targets
run_scenario reservation fail old; rc=$?
assert_leaked "1. OLD handler + reservation FAIL leaks a ledger entry"
assert_rc     "1b. OLD handler preserves fail exit code" 1 "$rc"

# 2. NEW handler, reservation FAIL → the fix: ledger clean
run_scenario reservation fail new; rc=$?
assert_clean "2. NEW handler + reservation FAIL releases via trap"
assert_rc    "2b. NEW handler preserves fail exit code (return 0 inert)" 1 "$rc"

# 3. NEW handler, reservation PASS → happy-path release + trap release = idempotent, no error
run_scenario reservation pass new; rc=$?
assert_clean "3. NEW handler + reservation PASS (double release is safe)"
assert_rc    "3b. NEW handler preserves pass exit code" 0 "$rc"

# 4. NEW handler, never acquired (sentinel) → trap release is a guarded no-op
run_scenario reservation sentinel new; rc=$?
assert_clean "4. NEW handler + never-acquired is a no-op (no phantom entry)"
assert_rc    "4b. sentinel path exits 0" 0 "$rc"

# 5. NEW handler, TOKEN mode FAIL → no ledger involvement, no error, exit code intact
run_scenario token fail new; rc=$?
assert_clean "5. NEW handler + TOKEN mode leaves no ledger entry"
assert_rc    "5b. TOKEN mode preserves fail exit code" 1 "$rc"

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
