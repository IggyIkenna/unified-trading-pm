#!/usr/bin/env bash
# Epic: resource_watchdog_host_guardian_2026_08_05
# Lifecycle: permanent
# Delete-when: NA
# install-resource-watchdog-retention.sh -- install/update local-retention
# config for the resource-watchdog's log + kill snapshots (logrotate +
# tmpfiles.d). Standalone from bootstrap_vm.sh's Step 4.8 (which only runs at
# fresh VM provisioning) so this can be applied to an already-running VM, or
# re-applied after editing either source file, without a full bootstrap.
#
# Usage:
#   sudo bash scripts/infra/resource-watchdog/install-resource-watchdog-retention.sh
#   sudo bash scripts/infra/resource-watchdog/install-resource-watchdog-retention.sh --dry-run
#
# Requires root (sudo) to write /etc/logrotate.d/ and /etc/tmpfiles.d/ -- run
# on the orchestrator VM itself, not from a dev checkout.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SSOT_LOGROTATE="${SCRIPT_DIR}/resource-watchdog.logrotate"
SSOT_TMPFILES="${SCRIPT_DIR}/resource-watchdog-snapshots.tmpfiles.conf"
DEST_LOGROTATE="/etc/logrotate.d/resource-watchdog"
DEST_TMPFILES="/etc/tmpfiles.d/resource-watchdog-snapshots.conf"

DRY_RUN=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help)
            sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "ERROR: unknown arg: $1" >&2; exit 2 ;;
    esac
done

for f in "${SSOT_LOGROTATE}" "${SSOT_TMPFILES}"; do
    if [[ ! -f "${f}" ]]; then
        echo "ERROR: source file not found: ${f}" >&2
        exit 1
    fi
done

if [[ "${DRY_RUN}" == "true" ]]; then
    echo "# === dry-run: ${DEST_LOGROTATE} ==="
    cat "${SSOT_LOGROTATE}"
    echo ""
    echo "# === dry-run: ${DEST_TMPFILES} ==="
    cat "${SSOT_TMPFILES}"
    exit 0
fi

install_file() {
    local src="$1" dest="$2" mode="$3"
    if [[ -f "${dest}" ]] && diff -q "${src}" "${dest}" > /dev/null 2>&1; then
        echo "[install] ${dest} already current"
        return 0
    fi
    if [[ -f "${dest}" ]]; then
        echo "[install] diff vs installed ${dest}:"
        sudo diff "${dest}" "${src}" || true
    fi
    sudo cp "${src}" "${dest}"
    sudo chmod "${mode}" "${dest}"
    sudo chown root:root "${dest}"
    echo "[install] installed ${dest}"
}

install_file "${SSOT_LOGROTATE}" "${DEST_LOGROTATE}" 0644
install_file "${SSOT_TMPFILES}" "${DEST_TMPFILES}" 0644

echo "[install] applying tmpfiles.d rule immediately (age-cleanup, not creation)..."
sudo systemd-tmpfiles --clean "${DEST_TMPFILES}"

echo "[install] validating logrotate config..."
sudo logrotate -d "${DEST_LOGROTATE}" 2>&1 | tail -5

echo "[install] DONE. logrotate runs on the system's existing daily cadence (logrotate.timer/cron);"
echo "          no restart of resource-watchdog.service needed -- _rw_log() reopens the log path per line."
