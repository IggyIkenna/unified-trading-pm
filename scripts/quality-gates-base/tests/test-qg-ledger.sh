#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Unit tests for the Phase-3 reservation ledger in qg-host-governor.sh
# (plans/active/qg_host_adaptive_resource_governor_2026_07_14.md).
#
# QG_LEDGER_DIR points the ledger at a throwaway dir — never the real host ledger.
# Covers: empty sum, add live, sum of multiple, dead-PID sweep (crash-safety),
# remove, and physical pruning of the dead row (not just the sum).
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-ledger.sh
set -uo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
QG_LEDGER_DIR="$(mktemp -d)"
export QG_LEDGER_DIR
SLEEP1=""
SLEEP2=""
trap 'rm -rf "$QG_LEDGER_DIR"; kill "$SLEEP1" "$SLEEP2" 2>/dev/null || true' EXIT
FAILS=0
eq() {
    if [[ "$2" == "$3" ]]; then
        echo "PASS: $1 ($3)"
    else
        echo "FAIL: $1 — expected '$2' got '$3'"
        FAILS=$((FAILS + 1))
    fi
}

# shellcheck source=/dev/null
source "$GOV"

# (1) empty ledger sums to 0
eq "empty reserved_mb" 0 "$(_qg_ledger_reserved_mb)"

# (2) one live reservation
sleep 300 &
SLEEP1=$!
_qg_ledger_add "$SLEEP1" unified-trading-library 5500 111
eq "one live reservation" 5500 "$(_qg_ledger_reserved_mb)"

# (3) a second live reservation sums
sleep 300 &
SLEEP2=$!
_qg_ledger_add "$SLEEP2" instruments-service 3600 222
eq "two live reservations" 9100 "$(_qg_ledger_reserved_mb)"

# (4) a DEAD pid's reservation is swept out of the sum (crash-safety)
_qg_ledger_add 2999999 ghost-repo 1000 333
eq "dead-pid reservation swept from sum" 9100 "$(_qg_ledger_reserved_mb)"

# (5) removing a pid drops its reservation
_qg_ledger_remove "$SLEEP1"
eq "after remove SLEEP1" 3600 "$(_qg_ledger_reserved_mb)"

# (6) the dead row was PHYSICALLY pruned, not just excluded from the sum
if grep -q "ghost-repo" "$(_qg_ledger_file)"; then
    echo "FAIL: dead row still present in ledger file"
    FAILS=$((FAILS + 1))
else
    echo "PASS: dead row physically pruned from ledger file"
fi

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
