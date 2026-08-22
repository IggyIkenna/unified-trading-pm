#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# install-pkill-guard-shell-env.sh — install the pkill/pgrep cross-slot-kill guard
# (scripts/hooks/pkill-guard.sh) into the operator's INTERACTIVE shells (bash/zsh).
#
# Closes plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md's
# recurrence-#2 P1 todo: a RULES.md prose addendum alone did not prevent a second
# same-day occurrence of a bare `pkill -f "quality-gates.sh"` killing a DIFFERENT
# slot's live QG run. This installs a shell-function guard (mirrors
# install-uv-cache-shell-env.sh / install-qg-governor-shell-env.sh's managed-block
# convention) that refuses a `pkill`/`pgrep` invocation lacking a slot-specific
# discriminator (an exact numeric PID/PGID target, or the caller's own
# `.tabs/<N>/` cwd substring in the pattern) instead of letting it execute
# host-wide.
#
# Idempotent: re-runs replace the managed block in place. Run ONCE per shared host
# (the central planning VM + any multi-slot dev host); a single-slot laptop
# benefits too since it's zero-cost when there's nothing else to cross-match.
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-pkill-guard-shell-env.sh
#   bash unified-trading-pm/scripts/dev/install-pkill-guard-shell-env.sh --uninstall
#
# Codex SSOT: plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md
# Plan: unified-trading-pm/agents/RULES.md § 1 "Your worktree"

set -euo pipefail

if [ "${EUID:-$(id -u)}" -eq 0 ] && [ "${ALLOW_ROOT_INSTALL:-0}" != "1" ]; then
    echo "Refusing to run as root (EUID=0) — this edits the OPERATOR's own shell rc." >&2
    echo "Run as the login user (on the planning VM: sudo -u ubuntu -i bash $0)." >&2
    exit 1
fi

UNINSTALL=0
[ "${1:-}" = "--uninstall" ] && UNINSTALL=1

# Workspace root = the directory holding all repo clones (parent of unified-trading-pm).
# Slot-aware: this installer commonly runs from WITHIN a per-slot clone
# (.tabs/<N>/unified-trading-pm/scripts/dev/...), and the guard-lib path this
# script installs must stay valid for EVERY shell on the host, not just the slot
# that happened to run the installer — so strip a `.tabs/<N>/<repo>` suffix first
# and resolve to the true host root; only fall back to the plain "3 levels up"
# derivation (mirrors install-uv-cache-shell-env.sh) when not slot-nested.
_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${_script_dir}" =~ ^(.*)/\.tabs/[0-9]+/[^/]+(/.*)?$ ]]; then
    WS_ROOT="${BASH_REMATCH[1]}"
else
    WS_ROOT="$(cd "${_script_dir}/../../.." && pwd)"
fi
GUARD_LIB="${WS_ROOT}/unified-trading-pm/scripts/hooks/pkill-guard.sh"
if [ ! -f "${GUARD_LIB}" ]; then
    echo "Derived guard-lib path '${GUARD_LIB}' does not exist — aborting." >&2
    echo "(derived workspace root: ${WS_ROOT})" >&2
    exit 1
fi

MARK_BEGIN="# >>> pkill/pgrep cross-slot-kill guard (install-pkill-guard-shell-env.sh) >>>"
MARK_END="# <<< pkill/pgrep cross-slot-kill guard <<<"

# GNU sed edits in place with a bare `-i`; BSD/macOS sed requires an explicit
# (empty) backup suffix. Mirrors install-uv-cache-shell-env.sh's detection.
if sed --version >/dev/null 2>&1; then
    _sed_inplace=(sed -i)
else
    _sed_inplace=(sed -i '')
fi

strip_block() { # $1 = rc file
    "${_sed_inplace[@]}" "\|^${MARK_BEGIN}\$|,\|^${MARK_END}\$|d" "$1"
}

install_block() { # $1 = rc file
    strip_block "$1"
    cat >>"$1" <<EOF
${MARK_BEGIN}
# Guards against the cross-slot pkill/pgrep footgun (recurrence #2, 2026-07-28):
# see plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md.
# \${VAR:-...} not applicable here (functions, not an env var) — re-source is
# idempotent (redefining a function is a no-op replace, not an error).
_pkill_guard_lib="${GUARD_LIB}"
if [ -f "\${_pkill_guard_lib}" ]; then
    # shellcheck source=/dev/null
    . "\${_pkill_guard_lib}"
fi
unset _pkill_guard_lib
${MARK_END}
EOF
}

changed=0
for rc in "${HOME}/.bashrc" "${HOME}/.zshrc"; do
    # Only touch rc files that already exist — don't invent a shell the host doesn't use.
    [ -f "$rc" ] || continue
    if [ "$UNINSTALL" -eq 1 ]; then
        strip_block "$rc"
        echo "[uninstalled] managed block removed from $rc"
    else
        install_block "$rc"
        echo "[installed] $rc → pkill()/pgrep() guarded via ${GUARD_LIB}"
    fi
    changed=1
done

if [ "$changed" -eq 0 ]; then
    echo "No ~/.bashrc or ~/.zshrc found — nothing to do." >&2
    exit 1
fi

[ "$UNINSTALL" -eq 1 ] && exit 0
echo "Verify in a NEW shell: 'pkill -f quality-gates.sh' should be REFUSED (no numeric target, no .tabs/<N>/ substring in pattern)."
echo "and 'pkill -f \"\$PWD-scoped-pattern\"' (containing your own .tabs/<N>/ substring) should still work."
