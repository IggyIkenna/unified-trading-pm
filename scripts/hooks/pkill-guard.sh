#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# pkill-guard.sh — mechanical guard against host-wide `pkill`/`pgrep` process kills.
#
# Incident: plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md
# (recurrence #2). Every slot on a shared host invokes shared scripts (e.g.
# `bash scripts/quality-gates.sh --no-fix`) with IDENTICAL argv, so a bare
# `pkill -f "quality-gates.sh"` (or `pkill quality-gates.sh`) matches every slot's
# process, not just the caller's own. Recurrence #1's fix was a RULES.md prose
# addendum ("kill by exact PID/PGID, never a name pattern") — recurrence #2 proved
# prose alone does not prevent the mistake under time pressure, even when the
# offending worker had read the rule at boot minutes earlier. This file is the
# mechanical follow-up: a shell-level guard that REFUSES a `pkill`/`pgrep`
# invocation lacking a slot-specific discriminator, instead of silently executing
# host-wide.
#
# Sourced (not executed) — installed into ~/.bashrc / ~/.zshrc by
# scripts/dev/install-pkill-guard-shell-env.sh. Defines `pkill()`/`pgrep()` shell
# FUNCTIONS that shadow the real binaries for interactive/agent-driven shells.
# This is a footgun-guard, not a security boundary: `command pkill ...` or an
# absolute path (`/usr/bin/pkill ...`) both deliberately bypass it, same as any
# bash wrapper function. It does not (and cannot) intercept a non-shell caller
# (e.g. a Python `subprocess.run(["pkill", ...])`) — that class of caller never
# goes through a user shell function in the first place.
#
# ALLOWED (not blocked):
#   - Any invocation carrying an exact numeric target for -g/-G/-P/-s/-U/-u/-T
#     (process-group / parent / session / uid criteria) — e.g. `pkill -g 12345`.
#     This is the "exact PID/PGID you recorded at background-start time" case.
#   - `pkill`/`pgrep` with a pattern (bare or `-f`) that contains the CALLER's own
#     `.tabs/<N>/` absolute-path substring, derived from $PWD at call time — e.g.
#     `pkill -f ".tabs/5/.*quality-gates"` run from inside slot 5's worktree.
#     A cwd-scoped pattern cannot cross-match another slot's process (each slot's
#     cwd substring is unique), so this is safe host-wide fan-out protection.
#
# BLOCKED (refused with a one-line error + pointer to this doc):
#   - `pkill -f "quality-gates.sh"` / `pkill quality-gates.sh` / any bare
#     name/pattern lacking both a numeric exact-target AND the caller's own
#     `.tabs/<N>/` substring. This is exactly the recurrence #1 + #2 mistake.
#
# `kill <pid>` is intentionally NOT wrapped — it already takes an exact PID by
# construction and needs no guard.

# _pkill_guard_slot_token — the caller's own `.tabs/<N>/` substring, derived from
# $PWD. Empty if the caller isn't inside a slot worktree (e.g. a root-clone shell),
# in which case the cwd-scoped allowance simply never matches (bare patterns still
# must clear the numeric-target check).
_pkill_guard_slot_token() {
    printf '%s' "$PWD" | sed -nE 's#.*(/\.tabs/[0-9]+/).*#\1#p'
}

# _pkill_guard_has_numeric_target — true if any of -g/-G/-P/-s/-U/-u/-T is paired
# with a purely numeric (comma-separated list OK) value, either as a separate
# argument (`-g 12345`) or attached (`-g12345`).
_pkill_guard_has_numeric_target() {
    local args=("$@")
    local i n a val
    n=${#args[@]}
    for ((i = 0; i < n; i++)); do
        a="${args[$i]}"
        case "$a" in
            -g | -G | -P | -s | -U | -u | -T)
                val="${args[$((i + 1))]:-}"
                [[ "$val" =~ ^[0-9]+(,[0-9]+)*$ ]] && return 0
                ;;
            -g[0-9]* | -G[0-9]* | -P[0-9]* | -s[0-9]* | -U[0-9]* | -u[0-9]* | -T[0-9]*)
                val="${a:2}"
                [[ "$val" =~ ^[0-9]+(,[0-9]+)*$ ]] && return 0
                ;;
        esac
    done
    return 1
}

# _pkill_guard_extract_pattern — best-effort extraction of the trailing name/-f
# pattern argument: the last token that isn't a recognized option or an option's
# consumed value. Not a full pkill(1) arg parser (this is a footgun-guard, not a
# CLI reimplementation) — good enough to find the pattern in the common invocation
# shapes this guard exists to catch.
_pkill_guard_extract_pattern() {
    local args=("$@")
    local i n a last skip_next
    n=${#args[@]}
    last=""
    skip_next=0
    for ((i = 0; i < n; i++)); do
        a="${args[$i]}"
        if [ "$skip_next" -eq 1 ]; then
            skip_next=0
            continue
        fi
        case "$a" in
            -g | -G | -P | -s | -U | -u | -T | -n | -o)
                skip_next=1
                continue
                ;;
            -*)
                continue
                ;;
            *)
                last="$a"
                ;;
        esac
    done
    printf '%s' "$last"
}

# _pkill_guard_check — the actual gate. Returns 0 (allow) or 1 (refuse, with a
# one-line explanation on stderr). $1 = the command name being wrapped
# ("pkill"/"pgrep"), the rest = its original argv.
_pkill_guard_check() {
    local cmd="$1"
    shift
    if _pkill_guard_has_numeric_target "$@"; then
        return 0
    fi
    local pattern token
    pattern="$(_pkill_guard_extract_pattern "$@")"
    token="$(_pkill_guard_slot_token)"
    if [ -n "$token" ] && [[ "$pattern" == *"$token"* ]]; then
        return 0
    fi
    {
        echo "REFUSED: '${cmd} $*' lacks a slot-specific discriminator."
        echo "  Every slot on this host invokes shared scripts with IDENTICAL argv --"
        echo "  a bare name/pattern match (no numeric -g/-G/-P/-s/-U/-u/-T target, no"
        echo "  '${token:-.tabs/<N>/}' cwd substring in the pattern) is host-wide, not"
        echo "  slot-scoped, and can kill a DIFFERENT slot's live process."
        echo "  Fix: kill the exact PID/PGID you recorded at background-start time"
        echo "  (e.g. \`kill \$MY_PID\`), or scope the pattern to your own worktree"
        echo "  (e.g. \`${cmd} -f \"${token:-.tabs/<N>/}.*quality-gates\"\`)."
        echo "  See plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md"
        echo "  (deliberate bypass: \`command ${cmd} ...\` or an absolute path)."
    } >&2
    return 1
}

pkill() {
    _pkill_guard_check "pkill" "$@" || return 1
    command pkill "$@"
}

pgrep() {
    _pkill_guard_check "pgrep" "$@" || return 1
    command pgrep "$@"
}

# export -f (recurrence #3, pkill_broad_pattern_vite_cross_slot_kill_recurrence3_2026_08_14.md):
# a non-exported shell function only lives in the shell process that defined it. The
# tmux_spawn.py worker-spawn path sources this file then immediately `exec`s into the
# `claude` binary -- a non-shell process -- which discards any non-exported function
# outright, and every later Bash-tool child (`bash -c '...'`, the actual vector all three
# pkill recurrences hit) is a FRESH bash process that never re-sources this file at all.
# `export -f` bakes each function into the process environment as a BASH_FUNC_*
# variable, which bash auto-imports into a real shell function on startup for ANY child
# process -- interactive or `bash -c`, login or not -- with no rc-file sourcing required.
# Confirmed empirically: without this export, `type pkill` in a live worker's Bash-tool
# shell resolved straight to /usr/bin/pkill despite the guard_export sourcing having run
# in its ancestor shell moments earlier.
export -f _pkill_guard_slot_token
export -f _pkill_guard_has_numeric_target
export -f _pkill_guard_extract_pattern
export -f _pkill_guard_check
export -f pkill
export -f pgrep
