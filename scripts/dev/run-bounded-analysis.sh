#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# run-bounded-analysis.sh — memory-cap wrapper for ad-hoc one-off analysis scripts.
#
# Why: QG_MEM_CAP (quality-gates-memory-governance.md) only wraps pytest/basedpyright
# inside quality-gates.sh — it does NOT protect an agent-authored ad-hoc scratchpad
# script run directly (e.g. `python3 my_script.py &`). The heavy-I/O HARD RULE
# (vm-launcher-runbook.md) governs GCS BANDWIDTH from the operator's own laptop only and
# explicitly exempts the shared planning-vm/AO-orchestrator VM — it says nothing about
# COMPUTE/MEMORY. Neither rule stopped the 2026-07-27 incident: an ad-hoc
# candle-coverage-gap analysis script loaded a whole corpus into memory directly on the
# shared planning-vm, grew to 15.8GB RSS over 21 minutes, and degraded the orchestrator's
# own poll/API loop for every slot on the host (host hit 24/30GB used, load avg 50)
# before it was SIGTERM-killed as a protective action.
#
# This wrapper closes that gap for the ad-hoc-script case: it reuses the exact
# systemd-run cgroup mechanism quality-gates-memory-governance.md already uses for QG,
# generalized to ANY command. A process that exceeds the cap dies with exit 137 (SIGKILL
# by cgroup) instead of taking the shared host down with it.
#
# This is a SAFETY NET, not a substitute for the right fix: prefer a bounded/streamed
# read (DuckDB, chunked pandas, a manifest-driven partial read — see
# manifest-consolidator-ssot.md for the DuckDB-over-pandas precedent) over loading a
# whole corpus into memory at all. If the analysis is genuinely corpus-scale and
# long-running, dispatch it to a dedicated one-off VM instead of running it here — see
# vm-launcher-runbook.md's "Heavy I/O" rule and the heavy-compute-on-shared-host section
# directly below it.
#
# Usage:
#   bash scripts/dev/run-bounded-analysis.sh -- python3 my_ad_hoc_script.py --foo bar
#   ANALYSIS_MEM_CAP=8G bash scripts/dev/run-bounded-analysis.sh -- python3 script.py
#   bash scripts/dev/run-bounded-analysis.sh --mem-cap 2G -- python3 script.py
#
# Default cap (4G) is deliberately smaller than QG_MEM_CAP's 10G default — an ad-hoc
# scratchpad script has no business needing more than a few GB; if it does, that's
# itself a signal it should be a bounded/streamed read or a dedicated VM, not a bigger
# cap.
#
# Hosts without a working systemd --user instance (confirmed 2026-07-27: `systemd-run`
# reports available but the scope launch itself silently fails on some hosts) fall back to
# an RSS-poll cap: the command runs in its own session (`setsid`), and a background monitor
# polls its real resident memory every few seconds, SIGKILLing the whole process group the
# first time RSS exceeds the cap. RSS is read via /proc/<pid>/status (Linux) when available,
# else via `ps -o rss=` (macOS/BSD — no /proc there at all, confirmed 2026-08-12: the ORIGINAL
# /proc-only fallback silently degraded to fully-unwrapped/advisory-only on every macOS host,
# meaning this wrapper enforced NOTHING on the operator's own laptop — exactly the host class
# a concurrent multi-tab session most needs it on. `ps -o rss=` needs no elevated permissions
# and works identically on macOS and Linux, so it is also used as the Linux fallback if /proc
# is ever unreadable for some reason.
#
# This used to be a per-process RLIMIT_AS hard cap via `ulimit -v` instead — REMOVED
# 2026-08-03 (/plans/archive/2026_08/read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md Todo 2):
# RLIMIT_AS caps virtual address space, not physical residency, and pyarrow/grpc-heavy
# workloads routinely reserve large virtual-address arenas (mmap pools, arena allocators)
# well beyond what they actually touch — confirmed live, an 8G `ulimit -v` cap spuriously
# failed a ~4.2MB allocation (`ArrowMemoryError: malloc of size 4423744 failed`) on a process
# whose real peak RSS need was ~11.8GiB, i.e. the fallback failed BELOW the intended cap on
# exactly the class of workload this wrapper exists to protect. RSS-poll measures the thing
# the cap is actually meant to bound. Only genuine non-Linux hosts (macOS, or any host
# missing `/proc` or `setsid`) fall all the way through to the advisory-only warning.
#
# SSOT: codex/05-infrastructure/vm-launcher-runbook.md § heavy-compute-on-shared-host,
# codex/06-coding-standards/quality-gates-memory-governance.md (the cgroup mechanism this
# reuses for the primary path).
set -euo pipefail

DEFAULT_MEM_CAP="4G"
MEM_CAP="${ANALYSIS_MEM_CAP:-$DEFAULT_MEM_CAP}"

# Convert a systemd-run-style size (e.g. "4G", "512M", "2048K", or a bare byte count) into
# whole kilobytes for `ulimit -v` (which always takes KB). Prints nothing (empty stdout) on
# an unrecognized format so the caller can skip the ulimit fallback rather than mis-cap.
_mem_cap_to_kb() {
    local val="$1" num unit
    if [[ "$val" =~ ^([0-9]+)([KMGT]?)$ ]]; then
        num="${BASH_REMATCH[1]}"
        unit="${BASH_REMATCH[2]}"
        case "$unit" in
            K) echo "$num" ;;
            M) echo $(( num * 1024 )) ;;
            G) echo $(( num * 1024 * 1024 )) ;;
            T) echo $(( num * 1024 * 1024 * 1024 )) ;;
            "") echo $(( (num + 1023) / 1024 )) ;; # bare bytes -> KB, round up
        esac
    fi
}

if [[ "${1:-}" == "--mem-cap" ]]; then
    if [[ $# -lt 2 ]]; then
        echo "run-bounded-analysis: --mem-cap requires a value (e.g. --mem-cap 2G)" >&2
        exit 2
    fi
    MEM_CAP="$2"
    shift 2
fi

if [[ "${1:-}" == "--" ]]; then
    shift
fi

if [[ $# -eq 0 ]]; then
    echo "Usage: run-bounded-analysis.sh [--mem-cap SIZE] -- <command> [args...]" >&2
    echo "  (SIZE understands systemd-run's MemoryMax syntax, e.g. 4G, 512M, 0 to disable)" >&2
    exit 2
fi

# RSS-poll fallback: launches "$@" in its own process group, polls its real RSS every
# ANALYSIS_POLL_INTERVAL_S seconds (default 2), and SIGKILLs the whole group the first time
# RSS exceeds the cap. Runs when systemd-run/cgroups aren't available — see the header
# comment for why this replaced the old RLIMIT_AS/ulimit -v fallback (it's virtual-address-
# space accounting, not physical residency, and fails spuriously on pyarrow/grpc-heavy
# workloads well below the intended cap).
#
# Process-group isolation prefers `setsid` (Linux, util-linux) when available, falling back
# to bash job control (`set -m`) only when it isn't (macOS/BSD — confirmed 2026-08-12: `setsid`
# has no macOS equivalent, so a setsid-only launch failed outright there and this whole
# fallback silently never engaged, leaving the wrapper enforcing NOTHING on the operator's own
# laptop). Both give the launched job its own new process group with PID==PGID, so
# `kill -- -$cmd_pid` below kills the whole group either way. `setsid` is preferred where it
# exists (2026-08-15,
# `run_bounded_analysis_rss_poll_numpy_rec_breakage_2026_08_15.md`): enabling job control
# (`set -m`) mid-script is the ONE thing this fallback changes relative to an unwrapped run —
# it flips how bash manages the launched job (job-control notifications, pgrp/session
# reassociation semantics) — and was identified as the most plausible source of a confirmed
# live regression (`ModuleNotFoundError: No module named 'numpy.rec'` deep inside a
# `pandas.DataFrame.groupby()` call, reproducible only when the identical script ran through
# this fallback, never when run directly). `setsid` gets the same PID==PGID process-group
# property via a syscall instead of bash job-control state, so it avoids that class of
# side effect entirely on the host class (Linux) where the regression was confirmed.
_read_rss_kb() {
    local pid="$1"
    if [[ -r "/proc/$pid/status" ]]; then
        awk '/^VmRSS:/{print $2}' "/proc/$pid/status" 2>/dev/null
    else
        # macOS/BSD (no /proc): `ps -o rss=` reports RSS in KB directly, portable, no
        # elevated permissions needed. Also the fallback if /proc is present but unreadable.
        ps -o rss= -p "$pid" 2>/dev/null | tr -d ' '
    fi
}

_run_with_rss_poll_cap() {
    local mem_cap_kb="$1"
    shift
    local poll_interval="${ANALYSIS_POLL_INTERVAL_S:-2}"

    if command -v setsid >/dev/null 2>&1; then
        setsid "$@" &
        local cmd_pid=$!
    else
        set -m
        "$@" &
        local cmd_pid=$!
        set +m
    fi

    (
        while kill -0 "$cmd_pid" 2>/dev/null; do
            sleep "$poll_interval"
            local rss_kb
            rss_kb="$(_read_rss_kb "$cmd_pid")"
            if [[ -n "$rss_kb" ]] && (( rss_kb > mem_cap_kb )); then
                echo "🛑 [run-bounded-analysis] RSS ${rss_kb}K exceeded cap ${mem_cap_kb}K — killing process group ${cmd_pid}" >&2
                kill -KILL -- "-${cmd_pid}" 2>/dev/null || true
                break
            fi
        done
    ) &
    local monitor_pid=$!

    set +e
    wait "$cmd_pid"
    local exit_code=$?
    set -e
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true
    return "$exit_code"
}

MEM_WRAP=()
USE_RSS_POLL=0
if [[ "$MEM_CAP" != "0" ]]; then
    if command -v systemd-run >/dev/null 2>&1 \
        && systemd-run --user --scope -p MemoryMax=100M --quiet -- true >/dev/null 2>&1; then
        # MemorySwapMax=0: without it the kernel swaps other processes out to keep the
        # runaway alive, slowing the whole shared host before the cap actually fires —
        # same rationale as QG_MEM_CAP (quality-gates-memory-governance.md).
        MEM_WRAP=(systemd-run --user --scope -p MemoryMax="$MEM_CAP" -p MemorySwapMax=0 --quiet --)
        echo "[run-bounded-analysis] cgroup mem cap active: MemoryMax=${MEM_CAP} MemorySwapMax=0" >&2
    else
        if [[ "$(uname -s)" == "Darwin" ]]; then
            echo "⚠️  [run-bounded-analysis] systemd-run unavailable on this host (macOS — no systemd at all)" >&2
        else
            echo "⚠️  [run-bounded-analysis] systemd-run unavailable on this host (no systemd --user instance enabled)" >&2
        fi
        MEM_CAP_KB="$(_mem_cap_to_kb "$MEM_CAP")"
        if [[ -n "$MEM_CAP_KB" ]] && { [[ -r /proc/self/status ]] || command -v ps >/dev/null 2>&1; }; then
            USE_RSS_POLL=1
            RSS_SOURCE="/proc"; [[ -r /proc/self/status ]] || RSS_SOURCE="ps"
            echo "    → falling back to an RSS-poll cap (source: ${RSS_SOURCE}): ~${MEM_CAP} (${MEM_CAP_KB}K), polled every ${ANALYSIS_POLL_INTERVAL_S:-2}s" >&2
        else
            # Neither /proc nor `ps` can report RSS — genuinely no enforcement mechanism
            # available (should be rare; `ps` is near-universal on Unix-likes).
            echo "    → RSS-poll fallback unavailable on this host too (needs /proc or ps) — running fully UNWRAPPED, advisory only" >&2
            echo "    → keep the analysis genuinely bounded (streamed/chunked read) rather than relying on a cap" >&2
        fi
    fi
fi

if [[ "$USE_RSS_POLL" == "1" ]]; then
    _run_with_rss_poll_cap "$MEM_CAP_KB" "$@"
    exit $?
fi

exec "${MEM_WRAP[@]}" "$@"
