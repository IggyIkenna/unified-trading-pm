#!/usr/bin/env bash
# Epic: infrastructure_master
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

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL BLOCKS PASSED"; else echo "FAILED BLOCKS: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
