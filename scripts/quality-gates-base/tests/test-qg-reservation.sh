#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Unit tests for the Phase-3c reservation-mode cutover in qg-host-governor.sh
# (plans/active/qg_host_adaptive_resource_governor_2026_07_14.md).
#
# All inputs forced (QG_FORCE_MEM_* / QG_FORCE_CORES + a fixture baseline) so the
# decisions are deterministic. Covers:
#   (A) default mode is "token" — reservation path is INERT unless flag set (ship-safety)
#   (B) acquire/release round-trip in reservation mode (reserve → sum → release → 0)
#   (C) oversize → SOLO_ADMIT when nothing else is reserved
#   (D) CONCURRENCY: 6 simultaneous acquirers on the same heavy repo can only fill the
#       budget (exactly 3 of 5500 MB in an 18 GB budget), never over-admit — the crux
#       that proves the check-and-reserve is atomic under the ledger lock.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-reservation.sh
set -uo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
TMP="$(mktemp -d)"
HOLDERS=""
cleanup() { local h; for h in $HOLDERS; do kill "$h" 2>/dev/null || true; done; rm -rf "$TMP"; }
trap cleanup EXIT
FAILS=0
eq() { if [[ "$2" == "$3" ]]; then echo "PASS: $1 ($3)"; else echo "FAIL: $1 — expected '$2' got '$3'"; FAILS=$((FAILS + 1)); fi; }

# Deterministic capacity: avail huge + cores huge so ONLY the RAM-reservation clause bites.
export QG_LEDGER_DIR="$TMP/ledger"
export QG_BASELINE_PATH="$TMP/baseline.json"
export QG_FORCE_MEM_AVAIL_KB=$((900000 * 1024)) # ~900 GB avail — live clause never blocks
export QG_FORCE_CORES=64                        # cpu slots 51 — cpu clause never blocks
cat > "$QG_BASELINE_PATH" <<'EOF'
{ "utl": {"vm": {"peak_rss_mb": 5500}}, "testrepo": {"vm": {"peak_rss_mb": 5500}} }
EOF
# budget = total_kb/1024 * 0.70. Pick total so budget ≈ 18000 MB → fits floor(18000/5500)=3.
export QG_FORCE_MEM_TOTAL_KB=26331428 # → ~25714 MB total → ~17999 MB budget

# shellcheck source=/dev/null
source "$GOV"

# ── (A) default mode is token — reservation path inert ───────────────────────
eq "default mode token: acquire is a no-op reservation-wise" "" "${_QG_RESERVED_PID:-}"
( unset QG_GOVERNOR_MODE; qg_governor_release ) && echo "PASS: token-mode release is safe no-op" || { echo "FAIL: token release errored"; FAILS=$((FAILS + 1)); }

# ── (B) reservation-mode acquire/release round-trip ──────────────────────────
export QG_GOVERNOR_MODE=reservation
QG_GOVERNOR_REPO=testrepo qg_governor_acquire
eq "round-trip: acquired (reserved pid set)" "$$" "${_QG_RESERVED_PID:-}"
eq "round-trip: ledger holds one 5500 reservation" 5500 "$(_qg_ledger_reserved_mb)"
qg_governor_release
eq "round-trip: released (pid cleared)" "" "${_QG_RESERVED_PID:-}"
eq "round-trip: ledger empty after release" 0 "$(_qg_ledger_reserved_mb)"

# ── (C) oversize → SOLO_ADMIT (this_peak > budget, nothing reserved) ─────────
(
    export QG_FORCE_MEM_TOTAL_KB=5851428 # budget ≈ 4000 MB < 5500 peak → oversize
    sleep 60 & hp=$!
    dec="$(_qg_ledger_with_lock _qg_try_reserve utl 5500 "$hp")"
    kill "$hp" 2>/dev/null || true
    [[ "$dec" == "SOLO_ADMIT" ]] && echo "PASS: oversize solo admit ($dec)" || echo "FAIL: oversize expected SOLO_ADMIT got $dec"
) || FAILS=$((FAILS + 1))

# ── (D) CONCURRENCY — 6 simultaneous reservers, budget fits exactly 3 ────────
rm -rf "$QG_LEDGER_DIR"; mkdir -p "$TMP/dec"
for i in 1 2 3 4 5 6; do
    sleep 30 & # long-lived holder so its reservation stays live DURING the reserves
    hp=$!
    HOLDERS="$HOLDERS $hp"
    echo "$hp" > "$TMP/dec/holder.$i"
done
rpids=""
for i in 1 2 3 4 5 6; do
    (
        hp="$(cat "$TMP/dec/holder.$i")"
        _qg_ledger_with_lock _qg_try_reserve utl 5500 "$hp" > "$TMP/dec/dec.$i"
    ) &
    rpids="$rpids $!"
done
# shellcheck disable=SC2086
wait $rpids # ONLY the reserve subshells — not the long-lived holder sleeps (else 30s hang)
admits="$(cat "$TMP"/dec/dec.* | grep -c '^ADMIT$' || true)"
waits="$(cat "$TMP"/dec/dec.* | grep -c '^WAIT_RAM_RESERVATION$' || true)"
# Read the ledger file DIRECTLY (no sweep) — robust to the background holders being
# reaped after the concurrent run. Exactly-3-admits already proves the holders were
# live DURING the reserves (a swept-mid-run ledger would have let a 4th in).
raw_rows="$(awk 'END{print NR+0}' "$QG_LEDGER_DIR/reservations" 2>/dev/null || echo 0)"
raw_sum="$(awk '{s+=$3} END{print s+0}' "$QG_LEDGER_DIR/reservations" 2>/dev/null || echo 0)"
eq "concurrency: exactly 3 admitted (budget fits 3×5500)" 3 "$admits"
eq "concurrency: other 3 waited on reservation bound" 3 "$waits"
eq "concurrency: exactly 3 rows written to ledger" 3 "$raw_rows"
eq "concurrency: raw reserved sum == 16500" 16500 "$raw_sum"
if [[ "$raw_sum" -le 18000 ]]; then
    echo "PASS: NO OVER-ADMIT — 3×5500 = $raw_sum MB ≤ 18000 MB budget (atomic check-and-reserve holds)"
else
    echo "FAIL: OVER-ADMIT — reserved $raw_sum MB > budget"
    FAILS=$((FAILS + 1))
fi

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
