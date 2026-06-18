#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# qg-host-governor.sh — host-level concurrency governor for quality-gates.sh.
#
# Plan: plans/active/quality_gates_resource_contention_speedup_2026_06_02.md (todo: qg-governor)
#
# WHY (the core fix)
#   The dev host runs 8 slots × 2 operator sides of parallel agents. When several slots'
#   quality-gates.sh hit the heavy phases (pytest/basedpyright) AT ONCE the box oversubscribes:
#   CPU steal climbs, it swaps, EVERY concurrent run slows. Measured ceilings that make this
#   acute: unified-trading-library peaks at 5.27 GB and execution/features at ~1.9 GB per run.
#   This governor caps how many QG runs may be in their heavy phase concurrently across ALL
#   slots — converting an N-way thrash into orderly queueing. No added parallelism; p95 drops.
#
# MECHANISM
#   Token bucket of K tokens implemented as K flock(1) lockfiles in a host-shared dir. A run
#   acquires one token (blocking until one frees), holds it for the heavy phase, releases it.
#   K defaults to max(2, floor(physical_cores / 4)) — overridable via QG_HOST_CONCURRENCY.
#   The acquiring process tree is de-prioritised (nice + ionice) so a held QG never starves
#   interactive work.
#
# USAGE
#   A) Sourced (from base-service.sh, around the heavy phases):
#        source "<this file>"
#        qg_governor_acquire        # blocks until a host token is free; holds it
#        ... pytest / basedpyright ...
#        qg_governor_release        # frees the token (also auto-freed on process exit)
#
#   B) Wrapper CLI (wrap any command under one token):
#        bash qg-host-governor.sh -- <command> [args...]
#
#   C) Introspection:
#        bash qg-host-governor.sh --status   # K, dir, currently-held tokens
#
# ENV
#   QG_HOST_CONCURRENCY   override K (max concurrent heavy QG phases host-wide)
#   QG_GOVERNOR_DIR       token dir (default ${TMPDIR:-/tmp}/qg-host-governor)
#   QG_GOVERNOR_DISABLE   set to "true" to make acquire/release no-ops (CI / single-run)
#   QG_GOVERNOR_NICE      nice increment applied to the QG tree (default 10)
#
# Safe to source repeatedly; functions are idempotent. No effect on correctness — purely
# a scheduling throttle, so a missing flock(1) degrades gracefully to "no governor".

# ── default K = max(2, floor(physical_cores / 4)) ────────────────────────────
# Floor RAISED 1 → 2 (operator 2026-06-05): the host must be able to run 2 full QGs
# at once, not just 1. RAM-safe by the documented sizing rule (per-VM RAM ≥ peak-RSS
# × K): the UTL ceiling 5.27 GB × 2 = ~10.6 GB still fits a 16 GB worker; service
# repos (~1.9 GB) are trivial. On the macOS operator host lscpu+nproc are both absent
# → cores degrades to 4 → floor(4/4)=1 → the min-2 floor lifts it to exactly 2 (the
# desired Mac cap); bigger boxes keep their higher floor(cores/4) (24-core → 6).
_qg_governor_default_k() {
    local cores
    # physical cores if lscpu is available, else logical (nproc), else 4
    cores="$(lscpu -p=core 2>/dev/null | grep -vc '^#')"
    [[ "${cores:-0}" -ge 1 ]] || cores="$(nproc 2>/dev/null || echo 4)"
    local k=$(( cores / 4 ))
    (( k >= 2 )) || k=2
    echo "$k"
}

_qg_governor_k() { echo "${QG_HOST_CONCURRENCY:-$(_qg_governor_default_k)}"; }
_qg_governor_dir() { echo "${QG_GOVERNOR_DIR:-${TMPDIR:-/tmp}/qg-host-governor}"; }

# Base file-descriptor for the token locks. The original used bash >=4.1's
# `exec {fd}>` auto-FD form, which is unparseable on bash 3.2 (the macOS
# operator host) → the governor silently went INACTIVE there, so concurrent
# QG runs on a Mac dev host were never throttled (host thrash / OOM, exit 144).
# Explicit numeric FDs opened via `eval "exec $fd>..."` work on bash 3.2 AND
# bash >=4.1, so the governor is now active on every host. High base (200) to
# avoid colliding with FDs quality-gates.sh holds. A token uses base+i (i=1..K).
_QG_GOV_FD_BASE=200
# Temp FD for the non-blocking probe in --status (must not overlap base+1..base+K).
_QG_GOV_PROBE_FD=199

# De-prioritise the current process tree so a held token never starves interactive work.
_qg_governor_deprioritise() {
    local inc="${QG_GOVERNOR_NICE:-10}"
    renice -n "$inc" -p "$$" >/dev/null 2>&1 || true
    ionice -c2 -n7 -p "$$" >/dev/null 2>&1 || true
}

# Acquire one host token (blocks until free). Holds an flock'd fd for the run's lifetime.
qg_governor_acquire() {
    [[ "${QG_GOVERNOR_DISABLE:-}" == "true" ]] && return 0
    command -v flock >/dev/null 2>&1 || { echo "[qg-governor] flock(1) absent — running ungoverned" >&2; return 0; }
    [[ -n "${_QG_GOV_FD:-}" ]] && return 0   # already holding a token (idempotent)

    local k dir fd
    k="$(_qg_governor_k)"; dir="$(_qg_governor_dir)"
    mkdir -p "$dir" 2>/dev/null || { echo "[qg-governor] cannot create $dir — ungoverned" >&2; return 0; }

    local waited=0
    while true; do
        local i
        for (( i=1; i<=k; i++ )); do
            fd=$(( _QG_GOV_FD_BASE + i ))
            # Explicit numeric FD opened via eval — parses on bash 3.2 (the macOS operator
            # host) AND bash >=4.1. The previous `exec {fd}>` auto-FD form is bash >=4.1-only,
            # so the governor silently went INACTIVE on a Mac → 8-slot QG thrash / OOM (exit 144).
            # On ANY failure we `continue` (try next slot) or fall through ungoverned, so a
            # botched FD never terminates quality-gates.sh before the sentinel is written.
            eval "exec ${fd}>\"\$dir/slot.\$i\"" 2>/dev/null || continue
            if flock -n "$fd"; then
                _QG_GOV_FD=$fd
                _qg_governor_deprioritise
                [[ "$waited" -gt 0 ]] && echo "[qg-governor] token $i/$k acquired after ${waited}s wait" >&2
                return 0
            fi
            eval "exec ${fd}>&-"   # slot busy — close and try next
        done
        sleep 2; waited=$(( waited + 2 ))
        # narrate every ~30s so a long queue is visible, not silent
        (( waited % 30 == 0 )) && echo "[qg-governor] all ${k} tokens busy — queued ${waited}s" >&2
    done
}

# Release the held token (also released automatically when the process exits).
qg_governor_release() {
    [[ -n "${_QG_GOV_FD:-}" ]] || return 0
    flock -u "$_QG_GOV_FD" 2>/dev/null || true
    eval "exec ${_QG_GOV_FD}>&-" 2>/dev/null || true   # explicit FD (bash 3.2-compatible)
    _QG_GOV_FD=""
}

_qg_governor_status() {
    local k dir; k="$(_qg_governor_k)"; dir="$(_qg_governor_dir)"
    echo "qg-host-governor: K=${k}  dir=${dir}  flock=$(command -v flock >/dev/null 2>&1 && echo yes || echo MISSING)"
    if [[ -d "$dir" ]]; then
        local held=0 i tfd="$_QG_GOV_PROBE_FD"
        for (( i=1; i<=k; i++ )); do
            [[ -e "$dir/slot.$i" ]] || continue
            # a slot is held iff a non-blocking flock fails. Explicit numeric probe FD via
            # eval (bash 3.2-compatible) in a SUBSHELL so the open/lock never leaks into the
            # caller's FD table or holds the lock past the probe.
            if ! ( eval "exec ${tfd}>\"\$dir/slot.\$i\"" && flock -n "$tfd" ) 2>/dev/null; then
                held=$(( held + 1 ))
            fi
        done
        echo "  tokens held now: ${held}/${k}"
    fi
}

# ── CLI entrypoint (only when executed directly, not when sourced) ───────────
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        --status) _qg_governor_status ;;
        --)
            shift
            [[ $# -ge 1 ]] || { echo "usage: qg-host-governor.sh -- <command> [args...]" >&2; exit 2; }
            qg_governor_acquire
            trap qg_governor_release EXIT
            "$@"; rc=$?
            qg_governor_release
            exit "$rc"
            ;;
        *) echo "usage: qg-host-governor.sh [--status | -- <command...>]" >&2; exit 2 ;;
    esac
fi
