#!/usr/bin/env bash
# Epic: infrastructure_master
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
# an RSS poll-and-kill loop (background `/proc/<pid>/status` VmRSS poll, `kill -KILL` on
# breach) rather than a `ulimit -v` (RLIMIT_AS) hard cap. RLIMIT_AS was tried first
# (2026-07-27) and DROPPED (2026-08-01,
# plans/active/issues/read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md):
# RLIMIT_AS caps virtual address space, not resident memory, and pyarrow/grpc reserve large
# virtual ranges (arena allocators, mmap pools) that count against `ulimit -v` even when not
# physically resident — confirmed spurious failure (`ArrowMemoryError: malloc of size
# 4423744 failed` under an 8G cap on a ~4.2MB allocation) on exactly the pyarrow-heavy
# workload class this wrapper exists to protect. RSS polling was independently improvised
# ad hoc in that same incident (5s interval, caught a 1.67GB→15.5GB-in-5s spike before host
# impact) and is now the standing fallback mechanism. Only genuine non-Linux hosts (macOS,
# where `/proc` doesn't exist) fall all the way through to the advisory-only warning.
#
# SSOT: codex/05-infrastructure/vm-launcher-runbook.md § heavy-compute-on-shared-host,
# codex/06-coding-standards/quality-gates-memory-governance.md (the mechanism this reuses).
set -euo pipefail

DEFAULT_MEM_CAP="4G"
MEM_CAP="${ANALYSIS_MEM_CAP:-$DEFAULT_MEM_CAP}"
# How often (seconds) the RSS-poll fallback samples /proc/<pid>/status. Tighter than the
# 5s interval improvised in the 2026-08-01 incident (that interval still caught the spike
# before host impact, but only because an operator was watching an ad-hoc safety net; the
# unattended default here polls faster to reduce the overshoot window).
DEFAULT_MEM_POLL_INTERVAL="2"
MEM_POLL_INTERVAL="${ANALYSIS_MEM_POLL_INTERVAL:-$DEFAULT_MEM_POLL_INTERVAL}"

# Convert a systemd-run-style size (e.g. "4G", "512M", "2048K", or a bare byte count) into
# whole kilobytes (used both for the cgroup path's own bookkeeping and the RSS-poll cap).
# Prints nothing (empty stdout) on an unrecognized format so the caller can skip the
# fallback rather than mis-cap.
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

# Sum VmRSS (KB) across a PID and all of its live descendants (a pyarrow/grpc workload can
# fan out worker processes that individually stay small while the tree's total is what
# actually threatens the host). Prints 0 for a PID whose /proc entry is already gone
# (process exited between the caller's liveness check and this read) rather than erroring.
_sum_tree_rss_kb() {
    local root_pid="$1" total=0 pid child
    local -a queue=("$root_pid")
    local i=0
    while [[ $i -lt ${#queue[@]} ]]; do
        pid="${queue[$i]}"
        i=$((i + 1))
        if [[ -r "/proc/$pid/status" ]]; then
            local rss
            rss="$(awk '/^VmRSS:/{print $2}' "/proc/$pid/status" 2>/dev/null)"
            [[ -n "$rss" ]] && total=$((total + rss))
        fi
        while IFS= read -r child; do
            [[ -n "$child" ]] && queue+=("$child")
        done < <(pgrep -P "$pid" 2>/dev/null)
    done
    echo "$total"
}

# Background poll-and-kill loop: samples the process tree's summed RSS every
# MEM_POLL_INTERVAL seconds and SIGKILLs the whole tree the first time it exceeds cap_kb.
# This is the RSS-based fallback used when systemd-run/cgroups are unavailable — it
# replaced a `ulimit -v` (RLIMIT_AS) cap, which spuriously fails pyarrow-heavy workloads
# well below the intended cap (virtual address space != resident memory; see the header
# comment). Runs as a detached background job; the caller kills it once the monitored
# command exits on its own.
_rss_poll_kill_loop() {
    local watch_pid="$1" cap_kb="$2" interval="$3"
    while kill -0 "$watch_pid" 2>/dev/null; do
        sleep "$interval"
        kill -0 "$watch_pid" 2>/dev/null || break
        local rss_kb
        rss_kb="$(_sum_tree_rss_kb "$watch_pid")"
        if [[ "$rss_kb" -gt "$cap_kb" ]]; then
            echo "⚠️  [run-bounded-analysis] RSS ${rss_kb}KB exceeded cap ${cap_kb}KB — killing process tree (PID $watch_pid)" >&2
            kill -KILL "$watch_pid" 2>/dev/null || :
            pkill -KILL -P "$watch_pid" 2>/dev/null || :
            break
        fi
    done
}

MEM_WRAP=()
RSS_POLL_CAP_KB=""
if [[ "$MEM_CAP" != "0" ]]; then
    if command -v systemd-run >/dev/null 2>&1 \
        && systemd-run --user --scope -p MemoryMax=100M --quiet -- true >/dev/null 2>&1; then
        # MemorySwapMax=0: without it the kernel swaps other processes out to keep the
        # runaway alive, slowing the whole shared host before the cap actually fires —
        # same rationale as QG_MEM_CAP (quality-gates-memory-governance.md).
        MEM_WRAP=(systemd-run --user --scope -p MemoryMax="$MEM_CAP" -p MemorySwapMax=0 --quiet --)
        echo "[run-bounded-analysis] cgroup mem cap active: MemoryMax=${MEM_CAP} MemorySwapMax=0" >&2
    else
        echo "⚠️  [run-bounded-analysis] systemd-run unavailable on this host (macOS / no user systemd instance)" >&2
        MEM_CAP_KB="$(_mem_cap_to_kb "$MEM_CAP")"
        if [[ -n "$MEM_CAP_KB" ]] && [[ -d /proc/self ]]; then
            # RSS-poll fallback: enforced by a background monitor reading
            # /proc/<pid>/status, not the kernel — a fast-growing allocation can overshoot
            # the cap between polls (bounded by MEM_POLL_INTERVAL), unlike a true kernel
            # limit. That tradeoff is deliberate: `ulimit -v` (RLIMIT_AS) WAS a true kernel
            # limit and it spuriously killed legitimate pyarrow reads well under cap, which
            # is worse than a slightly-delayed-but-accurate kill. See header comment.
            RSS_POLL_CAP_KB="$MEM_CAP_KB"
            echo "    → falling back to an RSS-poll cap: ~${MEM_CAP} (${MEM_CAP_KB}K), sampled every ${MEM_POLL_INTERVAL}s" >&2
        else
            # /proc doesn't exist on this host (e.g. macOS) — no enforcement mechanism is
            # available at all.
            echo "    → /proc unavailable on this host too — running fully UNWRAPPED, advisory only" >&2
            echo "    → keep the analysis genuinely bounded (streamed/chunked read) rather than relying on a cap" >&2
        fi
    fi
fi

if [[ -n "$RSS_POLL_CAP_KB" ]]; then
    # Can't `exec` here — the poller needs to keep running alongside the monitored command,
    # so this process stays alive as the shepherd instead of being replaced by "$@".
    "$@" &
    CMD_PID=$!
    _rss_poll_kill_loop "$CMD_PID" "$RSS_POLL_CAP_KB" "$MEM_POLL_INTERVAL" &
    POLL_PID=$!
    set +e
    wait "$CMD_PID"
    CMD_STATUS=$?
    set -e
    kill "$POLL_PID" 2>/dev/null || :
    wait "$POLL_PID" 2>/dev/null || :
    exit "$CMD_STATUS"
fi

exec "${MEM_WRAP[@]}" "$@"
