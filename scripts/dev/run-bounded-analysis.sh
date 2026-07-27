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
# macOS / non-systemd hosts: no cgroup equivalent without root — this degrades to an
# advisory warning only (same graceful-degrade posture as QG_MEM_CAP on macOS).
#
# SSOT: codex/05-infrastructure/vm-launcher-runbook.md § heavy-compute-on-shared-host,
# codex/06-coding-standards/quality-gates-memory-governance.md (the mechanism this reuses).
set -euo pipefail

DEFAULT_MEM_CAP="4G"
MEM_CAP="${ANALYSIS_MEM_CAP:-$DEFAULT_MEM_CAP}"

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

MEM_WRAP=()
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
        echo "    → running UNWRAPPED — no cgroup enforcement, this is advisory only here" >&2
        echo "    → keep the analysis genuinely bounded (streamed/chunked read) rather than relying on a cap" >&2
    fi
fi

exec "${MEM_WRAP[@]}" "$@"
