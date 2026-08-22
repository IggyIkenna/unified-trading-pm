#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# install-qg-governor-shell-env.sh — make the operator's INTERACTIVE shells (bash/zsh)
# + spawned worker panes actually see the QG_GOVERNOR_MODE / QG_HOST_CONCURRENCY that
# bootstrap_vm.sh already writes into agent-orchestrator/.env.local.
#
# Gap closed (found 2026-07-20, ao_fleet_infra_hardening_2026_07_20.md todo 7): unlike
# UV_CACHE_DIR (which base-service.sh derives fresh every run), qg-host-governor.sh /
# base-service.sh read QG_GOVERNOR_MODE / QG_HOST_CONCURRENCY straight from the ambient
# env with no file-read fallback (`${QG_GOVERNOR_MODE:-token}`) — .env.local having the
# right value written by bootstrap_vm.sh is necessary but NOT sufficient; nothing SOURCES
# it into a worker's tmux pane or an operator's hand-run terminal. Measured on the central
# VM: `qg-host-governor.sh --status` reported MODE=token K=2 while .env.local ALREADY
# contained QG_GOVERNOR_MODE=reservation + QG_HOST_CONCURRENCY=6 (operator had set these
# correctly) — sourcing .env.local by hand flipped it to MODE=reservation immediately,
# confirming the value was always correct, only unreachable.
#
# Fix: a managed ~/.bashrc/~/.zshrc block that reads the CURRENT value straight out of
# agent-orchestrator/.env.local at shell-start (not a hardcoded literal here — that would
# recreate the exact "two places, one concept" bug this plan exists to kill). `${VAR:-...}`
# so a pre-set spawn env still wins, mirroring install-uv-cache-shell-env.sh's convention.
#
# Idempotent: re-runs replace the managed block in place. Run ONCE per host that runs a
# backend/workers (planning VM primarily; any dev host that hand-runs QG benefits too).
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-qg-governor-shell-env.sh
#   bash unified-trading-pm/scripts/dev/install-qg-governor-shell-env.sh --uninstall
#
# Codex SSOT: codex/06-coding-standards/quality-gates.md
# Plan: plans/active/ao_fleet_infra_hardening_2026_07_20.md (todo 7)

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
AO_ENV_LOCAL="${WS_ROOT}/agent-orchestrator/.env.local"
GOVERNOR_SCRIPT="${WS_ROOT}/unified-trading-pm/scripts/quality-gates-base/qg-host-governor.sh"
if [ ! -d "${WS_ROOT}/unified-trading-pm" ]; then
    echo "Derived workspace root '${WS_ROOT}' does not contain unified-trading-pm — aborting." >&2
    exit 1
fi

MARK_BEGIN="# >>> QG governor env passthrough (install-qg-governor-shell-env.sh) >>>"
MARK_END="# <<< QG governor env passthrough <<<"

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
    cat >> "$1" <<EOF
${MARK_BEGIN}
# qg-host-governor.sh / base-service.sh read these straight from the ambient env
# with no file-read fallback -- pull the CURRENT value out of the single SSOT
# (agent-orchestrator/.env.local, written by bootstrap_vm.sh) rather than a
# literal here, so this self-heals if that file's value ever changes.
# \${VAR:-...} so a pre-set spawn env still wins.
_ao_env_local="${AO_ENV_LOCAL}"
if [ -f "\${_ao_env_local}" ]; then
    export QG_GOVERNOR_MODE="\${QG_GOVERNOR_MODE:-\$(sed -n 's/^QG_GOVERNOR_MODE=//p' "\${_ao_env_local}" | tail -1)}"
    export QG_HOST_CONCURRENCY="\${QG_HOST_CONCURRENCY:-\$(sed -n 's/^QG_HOST_CONCURRENCY=//p' "\${_ao_env_local}" | tail -1)}"
fi
unset _ao_env_local
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
        echo "[installed] $rc → QG_GOVERNOR_MODE/QG_HOST_CONCURRENCY sourced from ${AO_ENV_LOCAL}"
    fi
    changed=1
done

if [ "$changed" -eq 0 ]; then
    echo "No ~/.bashrc or ~/.zshrc found — nothing to do." >&2
    exit 1
fi

[ "$UNINSTALL" -eq 1 ] && exit 0
echo "Verify in a NEW login shell: 'bash ${GOVERNOR_SCRIPT} --status' should show MODE=reservation"
