#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Unit tests for QG_GOVERNOR_WAIT_SECONDS (qg-host-governor.sh) — the fix for
# qg_host_governor_severe_contention_2026_07_13.md's second finding: a
# quality-gates.sh run that queues under host contention must not fail its own
# MAX_DURATION wall-clock check purely for having queued. qg_governor_acquire()
# now accumulates the seconds actually spent WAITING (not holding) the token
# into QG_GOVERNOR_WAIT_SECONDS, so base-service.sh/base-library.sh can subtract
# it from billable duration.
#
# Uses a real flock(1) token dir under a temp QG_GOVERNOR_DIR — never the live
# host's shared /tmp/qg-host-governor dir.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-governor-wait-time.sh
set -uo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
FAILS=0
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# shellcheck source=/dev/null
source "$GOV"

# ── (a) uncontended acquire -> QG_GOVERNOR_WAIT_SECONDS stays 0 ─────────────
(
    unset _QG_GOV_FD QG_GOVERNOR_WAIT_SECONDS
    export QG_GOVERNOR_DIR="$TMP/uncontended"
    export QG_HOST_CONCURRENCY=1
    qg_governor_acquire
    rc=0
    if [[ "${QG_GOVERNOR_WAIT_SECONDS:-0}" -ne 0 ]]; then
        echo "FAIL: uncontended acquire recorded wait=${QG_GOVERNOR_WAIT_SECONDS} (expected 0)"
        rc=1
    else
        echo "PASS: uncontended acquire recorded wait=0"
    fi
    qg_governor_release
    exit "$rc"
) || FAILS=$((FAILS + 1))

# ── (b) contended acquire -> QG_GOVERNOR_WAIT_SECONDS > 0, and matches the run ──
(
    unset _QG_GOV_FD QG_GOVERNOR_WAIT_SECONDS
    dir="$TMP/contended"
    export QG_GOVERNOR_DIR="$dir"
    export QG_HOST_CONCURRENCY=1
    mkdir -p "$dir"

    # Hold the ONE token in a background subshell for ~3s so the foreground
    # qg_governor_acquire (2s poll interval) is forced to queue at least once.
    (
        exec 250>"$dir/slot.1"
        flock 250
        sleep 3
    ) &
    holder_pid=$!
    sleep 0.5   # let the holder actually acquire before we start polling

    start=$(date +%s)
    qg_governor_acquire
    elapsed=$(( $(date +%s) - start ))
    wait "$holder_pid" 2>/dev/null

    rc=0
    if [[ "${QG_GOVERNOR_WAIT_SECONDS:-0}" -le 0 ]]; then
        echo "FAIL: contended acquire recorded wait=${QG_GOVERNOR_WAIT_SECONDS:-0} (expected >0)"
        rc=1
    else
        echo "PASS: contended acquire recorded wait=${QG_GOVERNOR_WAIT_SECONDS}s (elapsed ${elapsed}s)"
    fi
    # The recorded wait must not wildly exceed the real elapsed time (sanity bound,
    # generous for CI jitter — the poll granularity is 2s).
    if [[ "${QG_GOVERNOR_WAIT_SECONDS:-0}" -gt $(( elapsed + 2 )) ]]; then
        echo "FAIL: recorded wait (${QG_GOVERNOR_WAIT_SECONDS}s) exceeds real elapsed (${elapsed}s) beyond poll jitter"
        rc=1
    fi
    qg_governor_release
    exit "$rc"
) || FAILS=$((FAILS + 1))

# ── (c) idempotent re-acquire (already holding) never adds wait ─────────────
(
    unset _QG_GOV_FD QG_GOVERNOR_WAIT_SECONDS
    export QG_GOVERNOR_DIR="$TMP/idempotent"
    export QG_HOST_CONCURRENCY=1
    qg_governor_acquire
    first_wait="${QG_GOVERNOR_WAIT_SECONDS:-0}"
    qg_governor_acquire   # idempotent no-op (already holding _QG_GOV_FD)
    rc=0
    if [[ "${QG_GOVERNOR_WAIT_SECONDS:-0}" -ne "$first_wait" ]]; then
        echo "FAIL: idempotent re-acquire changed wait ${first_wait} -> ${QG_GOVERNOR_WAIT_SECONDS}"
        rc=1
    else
        echo "PASS: idempotent re-acquire left wait unchanged (${first_wait}s)"
    fi
    qg_governor_release
    exit "$rc"
) || FAILS=$((FAILS + 1))

# ── (d) QG_GOVERNOR_DISABLE=true -> no-op, wait stays unset/0 ───────────────
(
    unset _QG_GOV_FD QG_GOVERNOR_WAIT_SECONDS
    export QG_GOVERNOR_DISABLE=true
    export QG_GOVERNOR_DIR="$TMP/disabled"
    qg_governor_acquire
    rc=0
    if [[ "${QG_GOVERNOR_WAIT_SECONDS:-0}" -ne 0 ]]; then
        echo "FAIL: disabled governor recorded wait=${QG_GOVERNOR_WAIT_SECONDS} (expected 0)"
        rc=1
    else
        echo "PASS: disabled governor recorded wait=0"
    fi
    exit "$rc"
) || FAILS=$((FAILS + 1))

# ── (e) _qg_governor_check_wait_timeout: no-op below the threshold ──────────
(
    export QG_LEDGER_DIR="$TMP/timeout-below"
    rc=0
    if ( _qg_governor_check_wait_timeout "test-repo" 5 "unit-test" ); then
        echo "PASS: below-threshold wait did not exit"
    else
        echo "FAIL: below-threshold wait exited (rc=$?), expected a no-op return"
        rc=1
    fi
    exit "$rc"
) || FAILS=$((FAILS + 1))

# ── (f) _qg_governor_check_wait_timeout: fires at/above the threshold — exit 75,
#        marker file written with the expected fields ───────────────────────
(
    dir="$TMP/timeout-above"
    export QG_LEDGER_DIR="$dir"
    export QG_GOVERNOR_MAX_WAIT_SECONDS=10
    ( _qg_governor_check_wait_timeout "test-repo" 10 "unit-test" )
    rc=$?
    ok=1
    if [[ "$rc" -ne 75 ]]; then
        echo "FAIL: at-threshold wait exited rc=${rc} (expected 75)"
        ok=0
    fi
    marker="$(find "$dir" -maxdepth 1 -name 'timeout.*' -type f 2>/dev/null | head -1)"
    if [[ -z "$marker" ]]; then
        echo "FAIL: no timeout marker file written under ${dir}"
        ok=0
    elif ! grep -q '^gate=unit-test$' "$marker" || ! grep -q '^repo=test-repo$' "$marker" \
         || ! grep -q '^waited_seconds=10$' "$marker" || ! grep -q '^max_wait_seconds=10$' "$marker"; then
        echo "FAIL: timeout marker missing expected fields: $(cat "$marker" 2>/dev/null)"
        ok=0
    fi
    if [[ "$ok" -eq 1 ]]; then
        echo "PASS: at-threshold wait exited 75 with a correctly-populated marker"
        exit 0
    fi
    exit 1
) || FAILS=$((FAILS + 1))

# ── (g) QG_GOVERNOR_WAIT_TIMEOUT_DISABLE=true -> never exits, however long ──
(
    export QG_LEDGER_DIR="$TMP/timeout-disabled"
    export QG_GOVERNOR_MAX_WAIT_SECONDS=1
    export QG_GOVERNOR_WAIT_TIMEOUT_DISABLE=true
    rc=0
    if ( _qg_governor_check_wait_timeout "test-repo" 999999 "unit-test" ); then
        echo "PASS: QG_GOVERNOR_WAIT_TIMEOUT_DISABLE=true suppressed a huge wait"
    else
        echo "FAIL: disabled wait-timeout still exited (rc=$?)"
        rc=1
    fi
    exit "$rc"
) || FAILS=$((FAILS + 1))
unset QG_GOVERNOR_WAIT_TIMEOUT_DISABLE QG_GOVERNOR_MAX_WAIT_SECONDS

# ── (h) end-to-end: qg_governor_acquire_total_instance actually exits 75 when
#        genuinely contended past a tiny configured max-wait (real flock contention,
#        not a mocked function call). _qg_repo_instance_dir() derives its path from
#        _qg_repo_name() (git-remote-derived), NOT from QG_GOVERNOR_REPO — that env
#        var is a different mechanism, read only by the reservation-mode gate — so
#        the holder's lock file must be planted at the SAME real resolved path this
#        test process's own repo checkout produces, not a hand-picked name.
(
    dir="$TMP/e2e-timeout"
    export QG_TOTAL_GOVERNOR_DIR="$dir/global"
    export QG_TOTAL_INSTANCE_CAP=1
    export QG_REPO_INSTANCE_CAP=1
    export QG_GOVERNOR_MAX_WAIT_SECONDS=2
    repo_dir="$(_qg_repo_instance_dir)"
    mkdir -p "$repo_dir" "$dir/global"

    # Hold the one repo slot for longer than the 2s max-wait so the foreground
    # acquire is forced to time out rather than ever admit.
    (
        exec 351>"${repo_dir}/slot.1"
        flock 351
        sleep 6
    ) &
    holder_pid=$!
    sleep 0.5

    out="$(bash -c '
        source "'"$GOV"'"
        qg_governor_acquire_total_instance
        echo "UNEXPECTED: admitted"
    ' 2>&1)"
    rc=$?
    wait "$holder_pid" 2>/dev/null

    rc_ok=0; msg_ok=0
    [[ "$rc" -eq 75 ]] && rc_ok=1
    [[ "$out" == *"KILLED(timeout)"* ]] && msg_ok=1
    if [[ "$rc_ok" -eq 1 && "$msg_ok" -eq 1 ]]; then
        echo "PASS: real total-instance contention past QG_GOVERNOR_MAX_WAIT_SECONDS exits 75 with a KILLED(timeout) message"
        exit 0
    fi
    echo "FAIL: rc=${rc} (want 75), message match=${msg_ok}. Output: ${out}"
    exit 1
) || FAILS=$((FAILS + 1))
unset QG_TOTAL_GOVERNOR_DIR QG_TOTAL_INSTANCE_CAP QG_REPO_INSTANCE_CAP QG_GOVERNOR_MAX_WAIT_SECONDS

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL BLOCKS PASSED"; else echo "FAILED BLOCKS: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
