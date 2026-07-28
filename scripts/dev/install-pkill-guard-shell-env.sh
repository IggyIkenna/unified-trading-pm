#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# install-pkill-guard-shell-env.sh — deploy the mechanical pkill safety guard
# (scripts/hooks/pkill-guard-lib.sh) into every interactive/tool shell on this host.
#
# WHY (recurrence #2, 2026-07-28): a prose-only RULES.md addendum from the FIRST
# cross-slot `pkill -f "quality-gates.sh"` incident was already live and read at boot,
# and the identical mistake still happened again the same day, on a different slot.
# See plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md's
# "Recurrence #2" section + its P1 todo: enforcement has to be mechanical, not more
# documentation. This installer is that mechanism.
#
# Idempotent: re-runs replace the managed block in place. Run ONCE per host that runs
# agent-orchestrator slot workers (mirrors install-qg-governor-shell-env.sh /
# install-uv-cache-shell-env.sh's managed-block convention exactly).
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-pkill-guard-shell-env.sh
#   bash unified-trading-pm/scripts/dev/install-pkill-guard-shell-env.sh --uninstall
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Multi-agent safety"
# Issue doc: plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md

set -euo pipefail

if [ "${EUID:-$(id -u)}" -eq 0 ] && [ "${ALLOW_ROOT_INSTALL:-0}" != "1" ]; then
    echo "Refusing to run as root (EUID=0) — this edits the OPERATOR's own shell rc." >&2
    echo "Run as the login user (on the planning VM: sudo -u ubuntu -i bash $0)." >&2
    exit 1
fi

UNINSTALL=0
[ "${1:-}" = "--uninstall" ] && UNINSTALL=1

# Workspace root = the directory holding all repo clones (parent of unified-trading-pm).
_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(cd "${_script_dir}/../../.." && pwd)"
GUARD_LIB="${WS_ROOT}/unified-trading-pm/scripts/hooks/pkill-guard-lib.sh"
if [ ! -d "${WS_ROOT}/unified-trading-pm" ]; then
    echo "Derived workspace root '${WS_ROOT}' does not contain unified-trading-pm — aborting." >&2
    exit 1
fi
if [ "$UNINSTALL" -eq 0 ] && [ ! -f "$GUARD_LIB" ]; then
    echo "Guard lib not found at '${GUARD_LIB}' — aborting." >&2
    exit 1
fi

MARK_BEGIN="# >>> pkill cross-slot-kill guard (install-pkill-guard-shell-env.sh) >>>"
MARK_END="# <<< pkill cross-slot-kill guard <<<"

# GNU sed edits in place with a bare `-i`; BSD/macOS sed requires an explicit
# (empty) backup suffix. Mirrors install-qg-governor-shell-env.sh's detection.
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
    cat >> "$1" <<EOF
${MARK_BEGIN}
# Defines a pkill() shell function that refuses a bare, unscoped pkill pattern (the
# exact footgun that killed a sibling slot's live quality-gates.sh run TWICE on
# 2026-07-28) and passes legitimate PID/PGID- or worktree-scoped kills straight
# through. SSOT lives in the sourced lib, not here, so this block never drifts.
if [ -f "${GUARD_LIB}" ]; then
    # shellcheck source=/dev/null
    . "${GUARD_LIB}"
fi
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
        echo "[installed] $rc → pkill() guard sourced from ${GUARD_LIB}"
    fi
    changed=1
done

if [ "$changed" -eq 0 ]; then
    echo "No ~/.bashrc or ~/.zshrc found — nothing to do." >&2
    exit 1
fi

[ "$UNINSTALL" -eq 1 ] && exit 0
echo "Verify in a NEW shell: 'type pkill' should show 'pkill is a function'"
