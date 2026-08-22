#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# install-gcloud-sdk-path-symlinks.sh — make the real (non-snap) gcloud SDK binaries
# win PATH resolution in EVERY shell type, not just interactive login shells.
#
# Root cause (vm_tarball_upload_expired_wif_token_interactive_slot_2026_07_25.md):
# on a host with the snap-packaged gcloud pre-installed, `/snap/bin` is on PATH
# ahead of the real SDK, and `/snap/bin/gcloud` cannot even run in this sandbox
# (`snap-confine is packaged without necessary permissions ... cap_dac_override
# not found`). `~/.bashrc` already sources `google-cloud-sdk/path.bash.inc`, which
# PREPENDS the real SDK's bin dir — but that only fires in an INTERACTIVE login
# shell. Non-interactive tool invocations (an agent's sandboxed Bash tool, cron,
# `claude -p`, …) never source `.bashrc`, so they still resolve the broken snap
# `gcloud`/`gsutil` first. Same class of bug as the cron-PATH-excludes-~/.local/bin
# fix in install-prune-uv-cache-cron.sh (per-tab-worktrees.md § "Shared uv cache").
#
# Fix: symlink the working SDK binaries into ~/.local/bin, which is FIRST on PATH
# in every shell type observed on this host (interactive AND sandboxed/non-interactive)
# — no shell-startup file needs to run for it to take effect. Mirrors the
# already-present (hand-installed, undocumented) ~/.local/bin/docker-credential-gcloud
# symlink this script now formalises + extends to gcloud/gsutil.
#
# Idempotent: re-runs replace existing symlinks in place; a REAL (non-symlink) file
# already at the target path is left untouched (never clobber operator-installed
# content). Self-skips cleanly if no working SDK is found (e.g. a VM that installs
# gcloud via apt with no snap conflict — see bootstrap_vm.sh STEP 1.6) or the
# resolved `gcloud`/`gsutil` already both work.
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-gcloud-sdk-path-symlinks.sh
#   bash unified-trading-pm/scripts/dev/install-gcloud-sdk-path-symlinks.sh --uninstall
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "gcloud SDK PATH symlinks"

set -euo pipefail

UNINSTALL=0
[ "${1:-}" = "--uninstall" ] && UNINSTALL=1

LOCAL_BIN="${HOME}/.local/bin"
SDK_BIN="${GCLOUD_SDK_BIN_DIR:-${HOME}/google-cloud-sdk/bin}"
BINARIES=(gcloud gsutil bq docker-credential-gcloud)

mkdir -p "${LOCAL_BIN}"

if [ "${UNINSTALL}" -eq 1 ]; then
    for name in "${BINARIES[@]}"; do
        target="${LOCAL_BIN}/${name}"
        if [ -L "${target}" ] && [ "$(readlink "${target}")" = "${SDK_BIN}/${name}" ]; then
            rm -f "${target}"
            echo "[uninstalled] removed ${target}"
        fi
    done
    exit 0
fi

if [ ! -x "${SDK_BIN}/gcloud" ]; then
    echo "No working gcloud SDK at ${SDK_BIN} — nothing to symlink (this host may install gcloud via apt/snap with no conflict)." >&2
    exit 0
fi

linked=0
for name in "${BINARIES[@]}"; do
    src="${SDK_BIN}/${name}"
    [ -x "${src}" ] || continue
    dst="${LOCAL_BIN}/${name}"
    if [ -e "${dst}" ] && [ ! -L "${dst}" ]; then
        echo "[skip] ${dst} exists and is not a symlink — leaving it alone (operator-installed content)."
        continue
    fi
    if [ -L "${dst}" ] && [ "$(readlink "${dst}")" = "${src}" ]; then
        echo "[ok]   ${dst} already -> ${src}"
        continue
    fi
    ln -sf "${src}" "${dst}"
    echo "[linked] ${dst} -> ${src}"
    linked=1
done

if [ "${linked}" -eq 1 ] || [ -L "${LOCAL_BIN}/gcloud" ]; then
    echo "Verify: 'command -v gcloud' should resolve to ${LOCAL_BIN}/gcloud (or ${SDK_BIN}/gcloud) in a NEW/non-interactive shell too."
fi
