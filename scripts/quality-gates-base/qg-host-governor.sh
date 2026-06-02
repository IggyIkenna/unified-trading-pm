#!/usr/bin/env bash
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
#   K defaults to max(1, floor(physical_cores / 4)) — overridable via QG_HOST_CONCURRENCY.
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

# ── default K = max(1, floor(physical_cores / 4)) ────────────────────────────
_qg_governor_default_k() {
    local cores
    # physical cores if lscpu is available, else logical (nproc), else 4
    cores="$(lscpu -p=core 2>/dev/null | grep -vc '^#')"
    [[ "${cores:-0}" -ge 1 ]] || cores="$(nproc 2>/dev/null || echo 4)"
    local k=$(( cores / 4 ))
    (( k >= 1 )) || k=1
    echo "$k"
}

_qg_governor_k() { echo "${QG_HOST_CONCURRENCY:-$(_qg_governor_default_k)}"; }
_qg_governor_dir() { echo "${QG_GOVERNOR_DIR:-${TMPDIR:-/tmp}/qg-host-governor}"; }

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
    # bash <4.1 lacks the `exec {fd}>` auto-fd syntax used below (macOS ships bash 3.2). Without
    # this guard that `exec` is parsed as a command, terminates quality-gates.sh BEFORE [3] TESTS,
    # and the .qg_last_passed_sha sentinel is never written → quickmerge can't promote from a Mac.
    # Degrade to ungoverned, same as a missing flock.
    { [[ "${BASH_VERSINFO[0]:-0}" -gt 4 ]] || { [[ "${BASH_VERSINFO[0]:-0}" -eq 4 ]] && [[ "${BASH_VERSINFO[1]:-0}" -ge 1 ]]; }; } \
        || { echo "[qg-governor] bash ${BASH_VERSION} <4.1 lacks {fd}> — running ungoverned" >&2; return 0; }
    [[ -n "${_QG_GOV_FD:-}" ]] && return 0   # already holding a token (idempotent)

    local k dir fd
    k="$(_qg_governor_k)"; dir="$(_qg_governor_dir)"
    mkdir -p "$dir" 2>/dev/null || { echo "[qg-governor] cannot create $dir — ungoverned" >&2; return 0; }

    local waited=0
    while true; do
        local i
        for (( i=1; i<=k; i++ )); do
            exec {fd}>"$dir/slot.$i" 2>/dev/null || continue
            if flock -n "$fd"; then
                _QG_GOV_FD=$fd
                _qg_governor_deprioritise
                [[ "$waited" -gt 0 ]] && echo "[qg-governor] token $i/$k acquired after ${waited}s wait" >&2
                return 0
            fi
            exec {fd}>&-   # slot busy — close and try next
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
    exec {_QG_GOV_FD}>&- 2>/dev/null || true
    _QG_GOV_FD=""
}

_qg_governor_status() {
    local k dir; k="$(_qg_governor_k)"; dir="$(_qg_governor_dir)"
    echo "qg-host-governor: K=${k}  dir=${dir}  flock=$(command -v flock >/dev/null 2>&1 && echo yes || echo MISSING)"
    # bash <4.1 lacks `exec {tfd}>` used by the token probe below — report inactive rather
    # than emit bogus held-counts (the probe's exec fails → every slot mis-counts as held).
    { [[ "${BASH_VERSINFO[0]:-0}" -gt 4 ]] || { [[ "${BASH_VERSINFO[0]:-0}" -eq 4 ]] && [[ "${BASH_VERSINFO[1]:-0}" -ge 1 ]]; }; } \
        || { echo "  (bash ${BASH_VERSION} <4.1 — governor inactive; token accounting unavailable)"; return 0; }
    if [[ -d "$dir" ]]; then
        local held=0 i
        for (( i=1; i<=k; i++ )); do
            [[ -e "$dir/slot.$i" ]] || continue
            # a slot is held iff a non-blocking flock fails
            if ! ( exec {tfd}>"$dir/slot.$i" && flock -n "$tfd" ) 2>/dev/null; then
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
