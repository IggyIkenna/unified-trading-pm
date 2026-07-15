#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1 self-hosted glue runners)
# Lifecycle: permanent
# Delete-when: glue moves to serverless (B2) or a managed runner (B3) and this host is retired
#
# setup-glue-runners.sh — install / manage N ephemeral GitHub Actions runners on THIS host
# (the planning / orchestrator VM) to absorb unified-trading-pm's CI "glue" workflows.
#
# Runs ON the VM as a sudo-capable user. All glue workflows live in unified-trading-pm, so runners
# register to that ONE repo. Runners are ephemeral (JIT config) and capped by github-glue-runner.slice
# so a CI burst can never starve the orchestrator.
#
#   sudo GH_PAT=<admin-pat> ./setup-glue-runners.sh install      # download+verify, install, start N
#   ./setup-glue-runners.sh status                               # systemd + live runner list
#   sudo ./setup-glue-runners.sh teardown                        # stop+remove everything
#   ./setup-glue-runners.sh prune                                # delete leftover OFFLINE glue-* runners
#
# Tunables (env): RUNNER_COUNT (default 8) · RUNNER_BASE (/opt/github-glue-runners) ·
#   OWNER (IggyIkenna) · REPO (unified-trading-pm) · RUNNER_VERSION · GH_PAT (admin token, install only)
set -euo pipefail

OWNER="${OWNER:-IggyIkenna}"
REPO="${REPO:-unified-trading-pm}"
RUNNER_COUNT="${RUNNER_COUNT:-8}"
RUNNER_BASE="${RUNNER_BASE:-/opt/github-glue-runners}"
RUNNER_VERSION="${RUNNER_VERSION:-2.335.1}"
RUNNER_SHA256="${RUNNER_SHA256:-4ef2f25285f0ae4477f1fe1e346db76d2f3ebf03824e2ddd1973a2819bf6c8cf}" # linux-x64 2.335.1
RUNNER_USER="${RUNNER_USER:-ubuntu}"
ENV_FILE="/etc/github-glue-runner.env"
UNIT_DIR="/etc/systemd/system"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARBALL="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${TARBALL}"

log() { printf '\033[36m[glue-runners]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[glue-runners] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

cmd_install() {
  [ "$(id -u)" -eq 0 ] || die "install must run as root (sudo) — it writes /etc and /opt"
  [ -n "${GH_PAT:-}" ] || die "GH_PAT (Administration:write on ${OWNER}/${REPO}) required for install"

  log "installing runner deps (libicu etc.)"
  install -d -m 0755 "${RUNNER_BASE}"

  # 1) download + verify the pinned runner tarball ONCE
  local cache="${RUNNER_BASE}/${TARBALL}"
  if [ ! -f "${cache}" ]; then
    log "downloading ${URL}"
    curl -fsSL -o "${cache}" "${URL}"
  fi
  echo "${RUNNER_SHA256}  ${cache}" | sha256sum -c - || die "checksum mismatch for ${TARBALL}"
  log "checksum OK (${RUNNER_VERSION})"

  # 2) N per-instance runner dirs (each needs its own _work/_diag)
  local i dir
  for i in $(seq 1 "${RUNNER_COUNT}"); do
    dir="${RUNNER_BASE}/glue-${i}"
    if [ ! -x "${dir}/run.sh" ]; then
      log "extracting runner -> ${dir}"
      install -d -m 0755 "${dir}"
      tar -xzf "${cache}" -C "${dir}"
    fi
    chown -R "${RUNNER_USER}:${RUNNER_USER}" "${dir}"
  done
  # install OS deps once (uses any extracted copy)
  "${RUNNER_BASE}/glue-1/bin/installdependencies.sh" >/dev/null 2>&1 || die "installdependencies.sh failed"

  # 3) the ExecStart wrapper
  install -m 0755 -o "${RUNNER_USER}" -g "${RUNNER_USER}" "${HERE}/glue-runner-run.sh" "${RUNNER_BASE}/glue-runner-run.sh"

  # 4) token env file (0600, root) — token never enters git or a world-readable path
  umask 077
  printf 'GH_TOKEN=%s\nOWNER=%s\nREPO=%s\nRUNNER_BASE=%s\n' "${GH_PAT}" "${OWNER}" "${REPO}" "${RUNNER_BASE}" > "${ENV_FILE}"
  chmod 0600 "${ENV_FILE}"
  log "wrote ${ENV_FILE} (0600)"

  # 5) systemd slice + template unit
  install -m 0644 "${HERE}/github-glue-runner.slice" "${UNIT_DIR}/github-glue-runner.slice"
  install -m 0644 "${HERE}/github-glue-runner@.service" "${UNIT_DIR}/github-glue-runner@.service"
  systemctl daemon-reload

  # 6) enable + start N runners
  for i in $(seq 1 "${RUNNER_COUNT}"); do
    systemctl enable --now "github-glue-runner@${i}.service"
  done
  log "started ${RUNNER_COUNT} runners — verify with: $0 status"
}

cmd_status() {
  log "systemd units:"
  systemctl --no-pager --type=service list-units 'github-glue-runner@*' || true
  echo
  log "slice resource state:"
  systemctl --no-pager show github-glue-runner.slice -p CPUQuotaPerSecUSec -p MemoryMax -p MemoryCurrent 2>/dev/null || true
  echo
  if [ -n "${GH_PAT:-${GH_TOKEN:-}}" ]; then
    log "live runners registered to ${OWNER}/${REPO}:"
    curl -fsS -H "Authorization: Bearer ${GH_PAT:-${GH_TOKEN}}" -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/${OWNER}/${REPO}/actions/runners" \
      | python3 -c 'import sys,json;d=json.load(sys.stdin);[print(f" {r[\"name\"]:28s} {r[\"status\"]:8s} busy={r[\"busy\"]}") for r in d.get("runners",[])] or print(" (none)")'
  else
    log "(set GH_PAT to also list live runners via the API)"
  fi
}

cmd_teardown() {
  [ "$(id -u)" -eq 0 ] || die "teardown must run as root (sudo)"
  local i
  for i in $(seq 1 "${RUNNER_COUNT}"); do
    systemctl disable --now "github-glue-runner@${i}.service" 2>/dev/null || true
  done
  rm -f "${UNIT_DIR}/github-glue-runner@.service" "${UNIT_DIR}/github-glue-runner.slice"
  systemctl daemon-reload
  cmd_prune || true
  log "systemd units removed. Runner dirs + ${ENV_FILE} left in place; rm -rf ${RUNNER_BASE} ${ENV_FILE} to fully purge."
}

# Delete OFFLINE glue-* runner registrations left by a crashed wrapper (ephemeral cleans up on normal exit).
cmd_prune() {
  local tok="${GH_PAT:-${GH_TOKEN:-}}"
  [ -n "${tok}" ] || die "prune needs GH_PAT/GH_TOKEN (Administration:write)"
  curl -fsS -H "Authorization: Bearer ${tok}" -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${OWNER}/${REPO}/actions/runners?per_page=100" \
    | python3 -c 'import sys,json;print("\n".join(str(r["id"]) for r in json.load(sys.stdin).get("runners",[]) if r["name"].startswith("glue-") and r["status"]=="offline"))' \
    | while read -r id; do
        [ -n "${id}" ] || continue
        curl -fsS -X DELETE -H "Authorization: Bearer ${tok}" -H "Accept: application/vnd.github+json" \
          "https://api.github.com/repos/${OWNER}/${REPO}/actions/runners/${id}" && log "pruned offline runner ${id}"
      done
}

case "${1:-status}" in
  install)  cmd_install ;;
  status)   cmd_status ;;
  teardown) cmd_teardown ;;
  prune)    cmd_prune ;;
  *) die "usage: $0 {install|status|teardown|prune}" ;;
esac
