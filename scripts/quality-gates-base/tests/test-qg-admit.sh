#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Unit tests for the Phase-3b dual-gate admission DECISION logic in
# qg-host-governor.sh (plans/active/qg_host_adaptive_resource_governor_2026_07_14.md).
#
# _qg_admit_check is pure (all inputs explicit), so every branch is asserted here:
# ADMIT / WAIT_RAM_RESERVATION / WAIT_RAM_LIVE / WAIT_CPU / SOLO_ADMIT / SOLO_WAIT,
# boundary cases, and the plan's 6×UTL worked example. Also _qg_repo_peak_mb on a
# fixture baseline (max(local,vm); unmeasured → conservative default).
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-admit.sh
set -uo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAILS=0

# shellcheck source=/dev/null
source "$GOV"

# check_decision <label> <exp_token> <exp_rc> <this reserved running budget avail floor slots>
check_decision() {
    local label="$1" exp_tok="$2" exp_rc="$3"; shift 3
    local tok rc
    tok="$(_qg_admit_check "$@")"; rc=$?
    if [[ "$tok" == "$exp_tok" && "$rc" == "$exp_rc" ]]; then
        echo "PASS: $label ($tok rc=$rc)"
    else
        echo "FAIL: $label — expected $exp_tok/rc$exp_rc got $tok/rc$rc"
        FAILS=$((FAILS + 1))
    fi
}
eq() {
    if [[ "$2" == "$3" ]]; then echo "PASS: $1 ($3)"; else echo "FAIL: $1 — expected '$2' got '$3'"; FAILS=$((FAILS + 1)); fi
}

# ── _qg_admit_check — every branch (args: this reserved running budget avail floor slots) ──
check_decision "plain admit"            ADMIT                0  2000  5000 2 43000 30000 6000 6
check_decision "RAM reservation bound"  WAIT_RAM_RESERVATION 1  5500 40000 1 43000 30000 6000 6
check_decision "RAM live backstop"      WAIT_RAM_LIVE        1  5500  1000 1 43000  8000 6000 6
check_decision "CPU slots full"         WAIT_CPU             1  1000  1000 6 43000 30000 6000 6
check_decision "oversize solo admit"    SOLO_ADMIT           0 12000     0 0 11000 13000 2000 4
check_decision "oversize solo wait"     SOLO_WAIT            1 12000  5000 1 11000 13000 2000 4
# Plan worked example — the 4th UTL is blocked by the LIVE clause once avail has fallen:
check_decision "6xUTL 4th blocked live" WAIT_RAM_LIVE        1  5500 16500 3 43000  9000 6000 6
# Boundaries (>, not >=): reservation exactly at budget admits; live exactly at floor admits:
check_decision "reservation == budget"  ADMIT                0  3000 40000 0 43000 30000 6000 6
check_decision "live == this+floor"     ADMIT                0  5500     0 0 43000 11500 6000 6
check_decision "cpu == slots"           ADMIT                0  1000  1000 5 43000 30000 6000 6
# Host-pressure valve (8th arg min_avail): refuse ANY admit when avail < min_avail (host >80% used).
check_decision "host >80% used, tiny run blocked" WAIT_HOST_PRESSURE 1  1000 1000 1 43000  8000 6000 6 12200
check_decision "host <80% used, min_avail set, admits" ADMIT        0  1000 1000 1 43000 30000 6000 6 12200
check_decision "min_avail=0 disables the valve"        ADMIT        0  1000 1000 1 43000  5000 2000 6 0

# ── _qg_repo_mem_cap — 1.2 × baseline, floored at 2048M (needs the fixture baseline below) ──
if command -v python3 >/dev/null 2>&1; then
    export QG_BASELINE_PATH="$TMP/baseline.json"
    cat > "$QG_BASELINE_PATH" <<'EOF'
{ "utl": {"vm": {"peak_rss_mb": 5500}}, "tiny": {"vm": {"peak_rss_mb": 630}} }
EOF
    eq "mem_cap 1.2×5500"        6600M "$(_qg_repo_mem_cap utl)"
    eq "mem_cap floor 2048M"     2048M "$(_qg_repo_mem_cap tiny)"
    eq "mem_cap unmeasured 1.2×5500" 6600M "$(_qg_repo_mem_cap no-such-repo)"
    unset QG_BASELINE_PATH
fi

# ── _qg_repo_peak_mb on a fixture baseline (needs python3; skip peak tests if absent) ──
if command -v python3 >/dev/null 2>&1; then
    export QG_BASELINE_PATH="$TMP/baseline.json"
    cat > "$QG_BASELINE_PATH" <<'EOF'
{
  "instruments-service": {"local": {"peak_rss_mb": 1297}, "vm": {"peak_rss_mb": 3657}},
  "greeks-service":      {"vm": {"peak_rss_mb": 630}},
  "only-local":          {"local": {"peak_rss_mb": 900}}
}
EOF
    eq "peak max(local,vm)"      3657 "$(_qg_repo_peak_mb instruments-service)"
    eq "peak vm-only"            630  "$(_qg_repo_peak_mb greeks-service)"
    eq "peak local-only"         900  "$(_qg_repo_peak_mb only-local)"
    eq "peak unmeasured default" 5500 "$(_qg_repo_peak_mb no-such-repo)"
    eq "peak unmeasured override" 4096 "$(QG_UNMEASURED_PEAK_MB=4096 _qg_repo_peak_mb no-such-repo)"
else
    echo "SKIP: _qg_repo_peak_mb tests (python3 absent)"
fi

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
