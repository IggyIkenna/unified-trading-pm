#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# install-uv-cache-shell-env.sh — export the shared uv-cache convention into the
# operator's INTERACTIVE shells (bash/zsh), per host.
#
# Closes the B2 gap named in
# plans/archive/issues/slot_venv_duplication_disk_pressure_2026_06_29.md: QG runs
# (base-service.sh) and AO slot spawns (tmux_spawn.py) already derive
#   UV_CACHE_DIR=<workspace-root>/.uv-cache  +  UV_LINK_MODE=hardlink
# but a HAND-RUN `uv` in a plain shell falls back to uv's default (~/.cache/uv),
# which on split-filesystem hosts is cross-fs from the venvs it links into —
# hardlinks silently degrade to copies onto the wrong (often fuller) partition,
# and every host quietly grows a second cache.
#
# Idempotent: re-runs replace the managed block in place. Operator runs this ONCE
# per host (planning VM + each dev host) — mirrors install-prune-uv-cache-cron.sh.
# The exports respect a pre-set value (`${VAR:-...}`), same as base-service.sh, so
# all layers agree and a spawn env still wins.
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-uv-cache-shell-env.sh
#   bash unified-trading-pm/scripts/dev/install-uv-cache-shell-env.sh --uninstall
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Shared uv cache"

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
if [ ! -d "${WS_ROOT}/unified-trading-pm" ]; then
    echo "Derived workspace root '${WS_ROOT}' does not contain unified-trading-pm — aborting." >&2
    exit 1
fi

MARK_BEGIN="# >>> shared uv-cache convention (install-uv-cache-shell-env.sh) >>>"
MARK_END="# <<< shared uv-cache convention <<<"

# GNU sed edits in place with a bare `-i`; BSD/macOS sed requires an explicit
# (empty) backup suffix (`-i ''`). Passing the GNU form to BSD sed makes it read
# the sed script as the backup suffix and the filename as the program — it errors
# ("command i expects \ followed by text") and writes nothing, so a hand-run on a
# macOS dev host silently no-ops. Detect the flavor once (only GNU sed answers
# `--version`) and build the right in-place invocation. The `\|…\|` address form
# below is accepted by both seds, so only the `-i` arg differs.
if sed --version >/dev/null 2>&1; then
    _sed_inplace=(sed -i)
else
    _sed_inplace=(sed -i '')
fi

strip_block() { # $1 = rc file
    # Delete any existing managed block (between markers, inclusive).
    "${_sed_inplace[@]}" "\|^${MARK_BEGIN}\$|,\|^${MARK_END}\$|d" "$1"
}

install_block() { # $1 = rc file
    strip_block "$1"
    cat >> "$1" <<EOF
${MARK_BEGIN}
# Hand-run uv must hit the same per-host shared cache QG + AO spawns use
# (base-service.sh derivation); \${VAR:-...} so a pre-set spawn env still wins.
# INSIDE .tabs/ (tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09):
# a cache dir sibling of .tabs/ sits on a different mount boundary than
# .tabs/<N>/<repo>/.venv on this host — hardlink() returns EXDEV across it and
# uv silently falls back to a full copy per slot. All real work happens inside
# .tabs/<N>/ (Path-B topology), so the shared cache lives inside .tabs/ too.
export UV_CACHE_DIR="\${UV_CACHE_DIR:-${WS_ROOT}/.tabs/.uv-cache}"
export UV_LINK_MODE="\${UV_LINK_MODE:-hardlink}"
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
        echo "[installed] $rc → UV_CACHE_DIR=${WS_ROOT}/.tabs/.uv-cache UV_LINK_MODE=hardlink"
    fi
    changed=1
done

if [ "$changed" -eq 0 ]; then
    echo "No ~/.bashrc or ~/.zshrc found — nothing to do." >&2
    exit 1
fi

[ "$UNINSTALL" -eq 1 ] && exit 0
echo "Verify in a NEW login shell: 'uv cache dir' should print ${WS_ROOT}/.tabs/.uv-cache"
