#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# supervised-resume.sh — self-restarting supervisor loop for a resumable, CAS-idempotent
# background command on this workspace's shared slot hosts.
#
# Why: this workspace's shared slot hosts have twice-confirmed, distinct ways of silently
# killing a long-running background process with zero traceback ("exit code 144" / clean
# stop) — a fixed ~1-3 min session/cgroup-boundary reap of nohup/setsid-detached
# processes, and a genuine host resource-exhaustion kill (load 22-325, swap 52-100%) that
# can catch even a harness-tracked run_in_background job after an hour or more. Every prior
# sighting was handled by an agent manually noticing the kill and hand-relaunching — this
# script is the standing fix so a kill is auto-recovered without a fresh agent turn having
# to notice and relaunch by hand.
#
# Contract (both required for this wrapper to be safe to use):
#   1. <command...> MUST be idempotent/resumable via its own checkpoint mechanism (e.g. a
#      --resume-log/--checkpoint path) — this script relaunches the IDENTICAL command line
#      unchanged on every retry, so the command itself is what must pick up where it left off.
#   2. That checkpoint file MUST live on the repo worktree's real disk, never /tmp — this
#      workspace's shared hosts often mount a small (~2GB) tmpfs at /tmp that another slot's
#      own usage can fill, corrupting a mid-write checkpoint (a real OSError/traceback, a
#      DIFFERENT failure mode from the clean kill this script exists to recover).
#
# Run THIS SCRIPT ITSELF directly under the harness's own tracked run_in_background (never
# nohup/disown/setsid-wrap it) — that is what makes each individual attempt survive past the
# ~1-3 min nohup-detachment kill window before this loop's own retry logic ever needs to
# fire. See async-wait-and-poll-discipline.md item 6 for the full incident lineage.
#
# Usage:
#   bash scripts/dev/supervised-resume.sh [options] -- <command> [args...]
#
# Options:
#   --max-retries N          Max relaunches after the first attempt (default: 10).
#   --retry-delay-seconds N  Base delay between a failed attempt and the next relaunch,
#                            in seconds (default: 15).
#   --contention-backoff-seconds N
#                            Extra wait applied on top of the base delay when the host looks
#                            severely contended at retry time (swap-used% > 80, matching the
#                            doc's own load-100+/swap>80%-back-off guidance) — default: 120.
#
# On any non-zero exit of <command...>, relaunches the identical command line, up to
# --max-retries times, applying a longer back-off when the host is under severe memory
# pressure (swap recovers faster and more directly than the lagging 5/15-min load average,
# per the SSOT). Prints an explicit terminal verdict line on every exit path
# (SUPERVISED-RESUME: SUCCESS / SUPERVISED-RESUME: FAILED-RETRIES-EXHAUSTED) — per the
# Watcher Coverage HARD RULE, this script never exits silently.
#
# SSOT: codex/12-agent-workflow/async-wait-and-poll-discipline.md item 6,
# plans/archive/issues/footystats_migration_bg_workers_killed_externally_2026_07_28.md.
set -euo pipefail

MAX_RETRIES=10
RETRY_DELAY_SECONDS=15
CONTENTION_BACKOFF_SECONDS=120

while [[ $# -gt 0 ]]; do
    case "$1" in
    --max-retries)
        MAX_RETRIES="$2"
        shift 2
        ;;
    --retry-delay-seconds)
        RETRY_DELAY_SECONDS="$2"
        shift 2
        ;;
    --contention-backoff-seconds)
        CONTENTION_BACKOFF_SECONDS="$2"
        shift 2
        ;;
    --)
        shift
        break
        ;;
    *)
        echo "supervised-resume.sh: unrecognized option before '--': $1" >&2
        exit 2
        ;;
    esac
done

if [[ $# -eq 0 ]]; then
    echo "Usage: supervised-resume.sh [options] -- <command> [args...]" >&2
    exit 2
fi

# Swap-used% is the fast-recovering signal the SSOT prefers over the lagging 5/15-min load
# average. Prints nothing (caller skips the backoff) if /proc/meminfo is unavailable
# (non-Linux host) rather than failing the whole loop over a diagnostic-only read.
_swap_used_pct() {
    local total used
    if [[ ! -r /proc/meminfo ]]; then
        return 1
    fi
    total=$(awk '/^SwapTotal:/ {print $2}' /proc/meminfo)
    used=$(awk '/^SwapFree:/ {print $2}' /proc/meminfo)
    if [[ -z "$total" || "$total" -eq 0 ]]; then
        echo 0
        return 0
    fi
    # $used here is actually SwapFree; compute used = total - free.
    local free="$used"
    echo $(((total - free) * 100 / total))
}

attempt=0
while true; do
    attempt=$((attempt + 1))
    echo "[supervised-resume attempt $attempt/$((MAX_RETRIES + 1)) $(date -u +%H:%M:%SZ)] launching: $*"

    # Capture the real exit code with -e suspended: under `if "$@"; then`, bash's compound
    # exit status is 0 whenever no branch's condition matched (not the failed command's own
    # code) — `rc=$?` read after such an `if/fi` is silently always 0. Disabling -e around a
    # direct invocation is the only way to both let the command fail without killing this
    # script AND read its real exit code.
    set +e
    "$@"
    rc=$?
    set -e

    if [[ $rc -eq 0 ]]; then
        echo "SUPERVISED-RESUME: SUCCESS — attempt $attempt exited 0"
        exit 0
    fi

    if [[ $attempt -gt $MAX_RETRIES ]]; then
        echo "SUPERVISED-RESUME: FAILED-RETRIES-EXHAUSTED — attempt $attempt exited $rc, $MAX_RETRIES retries used"
        exit "$rc"
    fi

    delay="$RETRY_DELAY_SECONDS"
    swap_pct="$(_swap_used_pct || echo "")"
    if [[ -n "$swap_pct" && "$swap_pct" -gt 80 ]]; then
        echo "[supervised-resume] swap ${swap_pct}% used — severe contention, adding ${CONTENTION_BACKOFF_SECONDS}s backoff before retry"
        delay=$((delay + CONTENTION_BACKOFF_SECONDS))
    fi

    echo "[supervised-resume] attempt $attempt exited $rc — retrying in ${delay}s"
    sleep "$delay"
done
