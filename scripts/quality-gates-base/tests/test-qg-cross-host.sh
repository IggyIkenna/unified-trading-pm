#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Phase-6 cross-host verification for the reservation governor
# (plans/active/qg_host_adaptive_resource_governor_2026_07_14.md): assert that admission
# adapts to host size with NO per-host tuning, matching the plan's cross-host table.
#
# Method: for each simulated host (QG_FORCE_MEM_TOTAL_KB / QG_FORCE_CORES), reserve the
# heaviest repo (UTL, 5465 MB) repeatedly against an isolated ledger with MemAvailable
# forced = MemTotal (so the live-availability clause + 80 % valve never bind and the test
# isolates the reservation-sum bound × the CPU-slot gate — the two host-size-driven gates).
# Admitted count = min(floor(0.70×MemTotal / 5465), floor(cores×0.80)). Holders are REAL
# background sleeps (fake PIDs would be pruned by the dead-PID sweep every acquire runs).
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-cross-host.sh
set -uo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
TMP="$(mktemp -d)"
ALL_HOLDERS=""
cleanup() { local h; for h in $ALL_HOLDERS; do kill "$h" 2>/dev/null || true; done; rm -rf "$TMP"; }
trap cleanup EXIT
FAILS=0

export QG_GOVERNOR_MODE=reservation
export QG_UNMEASURED_PEAK_MB=5465     # every reserve uses the UTL peak
export SERVICE_NAME=utl
# shellcheck source=/dev/null
source "$GOV"

# admits_for <mem_total_kb> <cores> — reserve UTL until the gate flips; echo the admit count.
admits_for() {
    local mt="$1" cores="$2" admits=0 decision hp holders=""
    local ws="$TMP/h_${mt}_${cores}/.tabs/1"; mkdir -p "$ws"
    export WORKSPACE_ROOT="$ws"
    export QG_FORCE_MEM_TOTAL_KB="$mt" QG_FORCE_MEM_AVAIL_KB="$mt" QG_FORCE_CORES="$cores"
    for _ in $(seq 1 40); do
        sleep 120 </dev/null >/dev/null 2>&1 &   # real live holder; detached stdio so $() can't hang
        hp=$!; holders="$holders $hp"; ALL_HOLDERS="$ALL_HOLDERS $hp"
        decision="$(_qg_ledger_with_lock _qg_try_reserve utl 5465 "$hp")"
        case "$decision" in ADMIT|SOLO_ADMIT) admits=$((admits + 1)) ;; *) break ;; esac
    done
    for hp in $holders; do kill "$hp" 2>/dev/null || true; done
    echo "$admits"
}

chk() {  # <label> <expected> <mem_total_kb> <cores>
    local got; got="$(admits_for "$3" "$4")"
    if [ "$got" = "$2" ]; then echo "PASS: $1 (admitted $got)"; else echo "FAIL: $1 — expected $2 got $got"; FAILS=$((FAILS + 1)); fi
}

if ! command -v flock >/dev/null 2>&1; then echo "SKIP: flock(1) absent"; exit 0; fi

#    label                                          exp  mem_total_kb  cores
chk "16 GB / 4-core → RAM-bound (~2 heavy)"           2   16777216      4
chk "24 GB / 4-core → ~3"                             3   25165824      4
chk "61 GB / 8-core → CPU-bound (6 = floor(8×0.8))"   6   63963136      8
chk "96 GB / 16-core → 12"                           12  100663296      16
chk "128 GB / 16-core → CPU-bound (RAM never binds)" 12  134217728      16

echo "────────────────────────────────────────"
if [ "$FAILS" -eq 0 ]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[ "$FAILS" -eq 0 ]
