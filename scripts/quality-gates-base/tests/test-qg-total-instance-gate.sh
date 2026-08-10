#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Unit tests for the TOTAL-INSTANCE gate (qg_governor_acquire_total_instance /
# qg_governor_release_total_instance) added to qg-host-governor.sh, 2026-08-09 —
# closes the scope gap found investigating
# plans/active/issues/review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md:
# the existing qg_governor_acquire only ever bracketed TESTS+TYPECHECK, so a host
# could carry far more live quality-gates.sh PROCESSES (12-19 observed) than the
# heavy-phase K ever capped (<=6 live) — BOOTSTRAP/LINT/CODEX-COMPLIANCE ran fully
# ungated. This gate bounds TOTAL concurrent script instances host-wide.
#
# Covers:
#   (A) default cap = floor(physical cores × 0.75), floored at 6 (tightened 2026-08-10,
#       plans/active/issues/ldr_qg_v2_ci_host_contention_false_wall_2026_08_03.md todo 4
#       — was a flat `cores` with no headroom discount)
#   (B) QG_TOTAL_GOVERNOR_DISABLE makes acquire/release safe no-ops
#   (C) acquire/release round-trip in the CURRENT process (token freed after release)
#   (D) CONCURRENCY: cap=2 — two background holders fill both slots; a third
#       acquirer blocks until one holder releases, then succeeds
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-total-instance-gate.sh
set -uo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
TMP="$(mktemp -d)"
HOLDERS=""
cleanup() { local h; for h in $HOLDERS; do kill "$h" 2>/dev/null || true; done; rm -rf "$TMP"; }
trap cleanup EXIT
FAILS=0
eq() { if [[ "$2" == "$3" ]]; then echo "PASS: $1 ($3)"; else echo "FAIL: $1 — expected '$2' got '$3'"; FAILS=$((FAILS + 1)); fi; }

export QG_TOTAL_GOVERNOR_DIR="$TMP/total-gate"

# ── (A) default cap sizing ────────────────────────────────────────────────────
(
    export QG_FORCE_CORES=8
    # shellcheck source=/dev/null
    source "$GOV"
    # Tightened 2026-08-10 (ldr_qg_v2_ci_host_contention_false_wall_2026_08_03.md
    # todo 4): floor(8 × 0.75) = 6, down from the old flat-`cores` value of 8.
    eq "default cap == floor(cores x 0.75) (8 cores -> 6)" 6 "$(_qg_total_k)"
)
(
    export QG_FORCE_CORES=16
    # shellcheck source=/dev/null
    source "$GOV"
    # floor(16 x 0.75) = 12 > the floor=6, so the multiplier (not the floor) binds here
    # — proves the formula actually scales down for bigger hosts, not just clamps to 6.
    eq "default cap == floor(cores x 0.75) (16 cores -> 12)" 12 "$(_qg_total_k)"
)
(
    export QG_FORCE_CORES=2
    # shellcheck source=/dev/null
    source "$GOV"
    # Floor raised 4 -> 6 (operator ruling 2026-08-09, see _qg_total_default_cap's own
    # comment in qg-host-governor.sh) — this assertion was left stale by that change;
    # fixed in passing while touching this test file for the repo-bucketing regression
    # (qg_governor_repo_bucketing_falls_back_to_slot_number_2026_08_09.md), unrelated bug.
    # floor(2 x 0.75)=1 < 6, so the floor still binds and is unchanged by today's tightening.
    eq "default cap floored at 6 (cores=2)" 6 "$(_qg_total_k)"
)
(
    export QG_TOTAL_INSTANCE_CAP=3 QG_FORCE_CORES=8
    # shellcheck source=/dev/null
    source "$GOV"
    eq "explicit QG_TOTAL_INSTANCE_CAP override" 3 "$(_qg_total_k)"
)

# shellcheck source=/dev/null
source "$GOV"

# ── (B) disable flag — safe no-op ─────────────────────────────────────────────
(
    export QG_TOTAL_GOVERNOR_DISABLE=true
    unset _QG_TOTAL_FD
    qg_governor_acquire_total_instance
    eq "disabled: acquire does not set _QG_TOTAL_FD" "" "${_QG_TOTAL_FD:-}"
    qg_governor_release_total_instance
) || FAILS=$((FAILS + 1))

# ── (C) acquire/release round-trip in THIS process ────────────────────────────
export QG_TOTAL_INSTANCE_CAP=2
unset _QG_TOTAL_FD
qg_governor_acquire_total_instance
if [[ -n "${_QG_TOTAL_FD:-}" ]]; then echo "PASS: round-trip acquired (_QG_TOTAL_FD set)"; else
    echo "FAIL: round-trip acquire did not set _QG_TOTAL_FD"; FAILS=$((FAILS + 1))
fi
qg_governor_release_total_instance
eq "round-trip: released (_QG_TOTAL_FD cleared)" "" "${_QG_TOTAL_FD:-}"

# ── (D) CONCURRENCY: cap=2, two long-lived holders, a third blocks then succeeds ─
rm -rf "$QG_TOTAL_GOVERNOR_DIR"
DONE_DIR="$TMP/done"; mkdir -p "$DONE_DIR"
# Holders are backgrounded DIRECTLY at top level (never inside a `$(...)` command
# substitution) so their PID is a real, waitable child of THIS script process —
# `$(fn_that_backgrounds &)` would instead reparent the child to the subshell's
# parent once the substitution's subshell exits, making it un-waitable and, worse,
# leaving it as a co-holder of the substitution's capture pipe (which then blocks
# `$(...)` from returning until that orphaned child itself exits). hold_secs is
# generous (8s) — this host runs under real, sometimes-severe multi-slot contention
# (the exact incident this gate exists for), so the poll-for-acquired loop below can
# itself eat a couple seconds; too short a hold window races the "still blocked"
# assertion against the holders self-releasing before the check runs.
QG_TOTAL_GOVERNOR_DIR="$QG_TOTAL_GOVERNOR_DIR" QG_TOTAL_INSTANCE_CAP=2 GOV="$GOV" \
DONE_DIR="$DONE_DIR" id=1 hold_secs=8 \
bash -c '
    # shellcheck source=/dev/null
    source "$GOV"
    qg_governor_acquire_total_instance
    : > "$DONE_DIR/acquired.$id"
    sleep "$hold_secs"
    qg_governor_release_total_instance
    : > "$DONE_DIR/released.$id"
' > "$DONE_DIR.log.1" 2>&1 &
h1=$!
QG_TOTAL_GOVERNOR_DIR="$QG_TOTAL_GOVERNOR_DIR" QG_TOTAL_INSTANCE_CAP=2 GOV="$GOV" \
DONE_DIR="$DONE_DIR" id=2 hold_secs=8 \
bash -c '
    # shellcheck source=/dev/null
    source "$GOV"
    qg_governor_acquire_total_instance
    : > "$DONE_DIR/acquired.$id"
    sleep "$hold_secs"
    qg_governor_release_total_instance
    : > "$DONE_DIR/released.$id"
' > "$DONE_DIR.log.2" 2>&1 &
h2=$!
HOLDERS="$h1 $h2"
# wait for both to actually acquire (bounded poll, not a blind sleep)
waited=0
while [[ ! -f "$DONE_DIR/acquired.1" || ! -f "$DONE_DIR/acquired.2" ]]; do
    sleep 0.2; waited=$((waited + 1))
    [[ "$waited" -gt 50 ]] && break   # ~10s ceiling
done
eq "concurrency: holder 1 acquired" "true" "$([[ -f "$DONE_DIR/acquired.1" ]] && echo true || echo false)"
eq "concurrency: holder 2 acquired" "true" "$([[ -f "$DONE_DIR/acquired.2" ]] && echo true || echo false)"

# both slots full — a third acquirer in THIS process must NOT get a token immediately
unset _QG_TOTAL_FD
(
    timeout 2 bash -c '
        export QG_TOTAL_GOVERNOR_DIR="'"$QG_TOTAL_GOVERNOR_DIR"'" QG_TOTAL_INSTANCE_CAP=2
        # shellcheck source=/dev/null
        source "'"$GOV"'"
        qg_governor_acquire_total_instance
    ' 2>/dev/null
)
rc=$?
if [[ "$rc" -eq 124 ]]; then
    echo "PASS: concurrency — third acquirer blocked while both slots held (timed out as expected)"
else
    echo "FAIL: concurrency — third acquirer did NOT block (rc=$rc, expected timeout 124)"; FAILS=$((FAILS + 1))
fi

# after both holders release (they self-release at ~6s), a fresh acquire must succeed promptly
wait "$h1" "$h2" 2>/dev/null
HOLDERS=""
eq "concurrency: holder 1 released" "true" "$([[ -f "$DONE_DIR/released.1" ]] && echo true || echo false)"
eq "concurrency: holder 2 released" "true" "$([[ -f "$DONE_DIR/released.2" ]] && echo true || echo false)"
(
    timeout 5 bash -c '
        export QG_TOTAL_GOVERNOR_DIR="'"$QG_TOTAL_GOVERNOR_DIR"'" QG_TOTAL_INSTANCE_CAP=2
        # shellcheck source=/dev/null
        source "'"$GOV"'"
        qg_governor_acquire_total_instance
    ' 2>/dev/null
)
rc=$?
eq "concurrency: post-release acquire succeeds promptly" 0 "$rc"

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
