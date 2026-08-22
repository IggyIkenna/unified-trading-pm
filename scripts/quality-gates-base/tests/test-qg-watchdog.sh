#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Unit tests for the Phase-4 runtime abort-monitor (watchdog) in qg-host-governor.sh —
# closes plans/active/qg_host_adaptive_resource_governor_2026_07_14.md's open P0
# ("runtime ABORT of an already-running >80% job STILL PENDING") and
# plans/active/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md.
#
# All inputs forced (QG_FORCE_MEM_* + fast poll interval) so decisions are deterministic
# and the suite runs in a few seconds. Covers:
#   (A) token mode: watchdog never starts (reservation-only feature — inert by default)
#   (B) healthy host: watchdog started, target survives (no SIGTERM, no marker)
#   (C) sustained pressure: watchdog fires after N consecutive hits — target receives
#       SIGTERM, a loud marker file is written, watchdog self-exits
#   (D) release stops a still-running (not-yet-fired) watchdog — no orphaned poll loop
#
# Assertions run inside `( )` subshells (backgrounded targets/watchdogs need process
# isolation) — subshell variable mutations don't propagate to the parent, so failures
# are recorded to a shared FAILFILE (file writes DO cross the subshell boundary) rather
# than an in-memory counter.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-watchdog.sh
set -uo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
FAILFILE="$TMP/fails.log"
: > "$FAILFILE"
eq() { if [[ "$2" == "$3" ]]; then echo "PASS: $1 ($3)"; else echo "FAIL: $1 — expected '$2' got '$3'"; echo "$1" >> "$FAILFILE"; fi; }

export QG_LEDGER_DIR="$TMP/ledger"
export QG_BASELINE_PATH="$TMP/baseline.json"
cat > "$QG_BASELINE_PATH" <<'EOF'
{ "testrepo": {"vm": {"peak_rss_mb": 5500}} }
EOF
# Fast, deterministic watchdog cadence for the whole suite.
export QG_WATCHDOG_INTERVAL_SECONDS=1
export QG_WATCHDOG_CONSECUTIVE_HITS=2

# shellcheck source=/dev/null
source "$GOV"

# ── (A) token mode — watchdog never starts ────────────────────────────────────
(
    unset QG_GOVERNOR_MODE
    _qg_watchdog_start testrepo
    eq "token mode: watchdog does not start" "" "${_QG_WATCHDOG_PID:-}"
)

# ── (B) healthy host — watchdog runs, target survives, no marker ─────────────
(
    export QG_GOVERNOR_MODE=reservation
    export QG_FORCE_MEM_TOTAL_KB=$((32 * 1024 * 1024))   # 32 GB
    export QG_FORCE_MEM_AVAIL_KB=$((28 * 1024 * 1024))   # 28 GB avail — well under 80% used
    sleep 30 & target=$!
    _qg_watchdog_loop "$target" testrepo &
    wpid=$!
    sleep 3.5   # >3 poll cycles at 1s — should never trip
    still_alive=false
    kill -0 "$target" 2>/dev/null && still_alive=true
    marker_exists=false
    [[ -f "$QG_LEDGER_DIR/aborted.$target" ]] && marker_exists=true
    kill "$target" "$wpid" 2>/dev/null || true
    eq "healthy host: target survives" "true" "$still_alive"
    eq "healthy host: no marker written" "false" "$marker_exists"
)

# ── (C) sustained pressure — watchdog fires: SIGTERM + loud marker ───────────
(
    export QG_GOVERNOR_MODE=reservation
    export QG_FORCE_MEM_TOTAL_KB=$((32 * 1024 * 1024))   # 32 GB
    export QG_FORCE_MEM_AVAIL_KB=$((3 * 1024 * 1024))    # 3 GB avail — >90% used, well over 80%
    # Target: a subshell that traps SIGTERM (mirrors base-service.sh's EXIT-trap release
    # path) and otherwise sleeps — proves the signal is catchable/loud, unlike SIGKILL.
    (
        trap 'echo terminated > "'"$TMP"'/target_terminated"; exit 143' TERM
        sleep 30
    ) &
    target=$!
    _qg_watchdog_loop "$target" testrepo &
    wpid=$!
    # 2 consecutive hits at 1s interval → fires within ~3s; give it margin.
    for _ in 1 2 3 4 5 6 7 8; do
        [[ -f "$TMP/target_terminated" ]] && break
        sleep 1
    done
    terminated=false
    [[ -f "$TMP/target_terminated" ]] && terminated=true
    marker_exists=false
    [[ -f "$QG_LEDGER_DIR/aborted.$target" ]] && marker_exists=true
    marker_has_reason=false
    [[ "$marker_exists" == "true" ]] && grep -q "^reason=host_ram_pressure" "$QG_LEDGER_DIR/aborted.$target" && marker_has_reason=true
    kill "$target" "$wpid" 2>/dev/null || true
    eq "sustained pressure: target received catchable SIGTERM (trap ran)" "true" "$terminated"
    eq "sustained pressure: loud marker file written" "true" "$marker_exists"
    eq "sustained pressure: marker carries a reason" "true" "$marker_has_reason"
)

# ── (D) release stops a still-running watchdog (no orphan) ───────────────────
(
    export QG_GOVERNOR_MODE=reservation
    export QG_FORCE_MEM_TOTAL_KB=$((32 * 1024 * 1024))
    export QG_FORCE_MEM_AVAIL_KB=$((28 * 1024 * 1024))   # healthy — watchdog would run forever
    unset _QG_RESERVED_PID _QG_WATCHDOG_PID
    _qg_watchdog_start testrepo
    wpid="${_QG_WATCHDOG_PID:-}"
    running=false
    [[ -n "$wpid" ]] && kill -0 "$wpid" 2>/dev/null && running=true
    qg_governor_release
    sleep 0.3
    still_running=false
    [[ -n "$wpid" ]] && kill -0 "$wpid" 2>/dev/null && still_running=true
    eq "release: watchdog was running before release" "true" "$running"
    eq "release: watchdog reaped after release" "false" "$still_running"
    eq "release: _QG_WATCHDOG_PID cleared" "" "${_QG_WATCHDOG_PID:-}"
)

echo "────────────────────────────────────────"
FAILS=$(wc -l < "$FAILFILE" | tr -d ' ')
if [[ "$FAILS" -eq 0 ]]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
