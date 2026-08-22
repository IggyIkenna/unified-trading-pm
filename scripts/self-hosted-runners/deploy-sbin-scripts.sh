#!/usr/bin/env bash
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
#
# deploy-sbin-scripts.sh — sync the host-deployed monitoring/cleanup scripts from the
# already-refreshed slot mirror (${RUNNER_BASE}/repo) into their live /usr/local/sbin/
# execution path, so a repo fix actually reaches the running host instead of requiring a
# one-off manual SSM copy.
#
# WHY THIS EXISTS: found 2026-08-06 while fixing glue-runner-crash-loop-watchdog.sh's
# false-positive crash-loop bug -- the live host copy at /usr/local/sbin/ had a DIFFERENT
# hash than either repo-tracked mirror on the same host, missing an earlier 2026-08-05 fix,
# because NOTHING deployed this class of script automatically; every prior fix needed a
# manual SSM copy that evidently didn't happen consistently. See this repo's
# plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md, final P3 todo.
# The same gap applies to every OTHER script this host runs straight out of /usr/local/sbin/
# via a systemd unit's `ExecStart=` (docker-disk-cleanup.sh, tmpfs-disk-cleanup.sh,
# ci-vm-resource-watchdog.sh) -- same file layout, same silent-drift failure mode -- so this
# syncs the whole small set rather than re-solving the identical problem once per script.
#
# PRIVILEGE BOUNDARY: this runs as ROOT, unlike refresh-slot-repo.sh (deliberately
# unprivileged -- ${RUNNER_BASE}/repo is ubuntu-owned). /usr/local/sbin is root:root 0755 and
# none of these are things the runner user should be able to silently rewrite, so the write
# step is isolated to this dedicated script/unit rather than folded into the slot refresh.
#
# This script only READS ${RUNNER_BASE}/repo -- it never fetches/pulls anything itself.
# github-glue-slot-refresh.timer keeps that mirror current every 10 min; a partial or dirty
# mirror is refresh-slot-repo.sh's problem to fail loudly on (it refuses to force a merge),
# not this script's to guess around.
set -euo pipefail

: "${RUNNER_BASE:=/opt/github-glue-runners}"
: "${SLOT_REPO:=${RUNNER_BASE}/repo}"
SCRIPT_DIR_REL="scripts/self-hosted-runners"
TARGET_DIR="/usr/local/sbin"

# One entry per script that a systemd unit `ExecStart=`'s straight out of /usr/local/sbin/ --
# keep this list in sync with that set:
#   grep -l '^ExecStart=/usr/local/sbin/' scripts/self-hosted-runners/*.service
DEPLOY_SCRIPTS=(
  glue-runner-crash-loop-watchdog.sh
  docker-disk-cleanup.sh
  tmpfs-disk-cleanup.sh
  prune-shared-bare-repo-worktrees.sh
  ci-vm-resource-watchdog.sh
)

log() { printf '[deploy-sbin] %s\n' "$*"; }

[ -d "${SLOT_REPO}/.git" ] || { echo "[deploy-sbin] no clone at ${SLOT_REPO} — run setup-glue-runners.sh install" >&2; exit 1; }
[ "$(id -u)" = "0" ] || { echo "[deploy-sbin] must run as root (writes ${TARGET_DIR})" >&2; exit 1; }

changed=0
for name in "${DEPLOY_SCRIPTS[@]}"; do
  src="${SLOT_REPO}/${SCRIPT_DIR_REL}/${name}"
  dst="${TARGET_DIR}/${name}"
  if [ ! -f "${src}" ]; then
    echo "[deploy-sbin] WARN: ${src} not found in mirror — skipping ${name}" >&2
    continue
  fi
  if [ -f "${dst}" ] && cmp -s "${src}" "${dst}"; then
    continue
  fi
  install -m 0755 -o root -g root "${src}" "${dst}"
  changed=$((changed + 1))
  log "deployed ${name} (mirror -> ${dst})"
done

if [ "${changed}" -eq 0 ]; then
  log "already current — 0/${#DEPLOY_SCRIPTS[@]} script(s) changed"
else
  log "synced ${changed}/${#DEPLOY_SCRIPTS[@]} script(s)"
fi
