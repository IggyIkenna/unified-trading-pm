#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1 self-hosted glue runners)
# Lifecycle: permanent
# Delete-when: glue moves to serverless (B2) or a managed runner (B3) and self-hosting is retired
#
# bootstrap-ci-host.sh — take a BARE Ubuntu box to CI-ready, then hand off to setup-glue-runners.sh.
#
# ┌─ WHY THIS EXISTS (read before editing) ────────────────────────────────────────────────────────┐
# │ The runner design deliberately REUSES planning-VM's existing toolchain and creds (operator      │
# │ 2026-07-16). That is the right call for cost, but it HIDES the dependency: if that VM dies and  │
# │ we must stand up a replacement CI host, nothing records what the box actually needs.            │
# │ `setup-glue-runners.sh preflight` only CHECKS — on a bare box it fails and leaves you stuck.    │
# │ This script is the failsafe: it ASSUMES NOTHING IS INSTALLED and provisions from scratch.       │
# └────────────────────────────────────────────────────────────────────────────────────────────────┘
#
# ┌─ OPERATOR DISCIPLINE — THE WHOLE POINT (operator 2026-07-16) ──────────────────────────────────┐
# │ UPDATE THIS SCRIPT AT EVERY DEPLOY STEP. Each time a real deploy reveals something missing or   │
# │ silently assumed-present, fold it back in HERE, immediately. A failsafe that drifts from truth  │
# │ is worse than none — it fails at the exact moment you're relying on it. This file converges on  │
# │ reality only if every discovery is written back.                                                │
# └────────────────────────────────────────────────────────────────────────────────────────────────┘
#
# STATUS (2026-07-16) — be precise about what is and isn't proven:
#   ✅ PROVEN: full run against a bare `ubuntu:24.04` container → all 10 tools resolve, EXIT=0.
#      That run EARNED its keep: it caught the `sudo` dependency (see install_base) which cloud
#      images mask. Reproduce:
#        docker run --rm -v "$PWD/bootstrap-ci-host.sh:/b.sh:ro" ubuntu:24.04 \
#          bash -c 'useradd -m -s /bin/bash ubuntu; bash /b.sh'
#   ✅ PROVEN (2026-08-22, real bare EC2 host via SSM, `i-0fbdb1f176c8ff14a`/`i-0641314cb67f66211`,
#      reproduced 2x): IMDS / EC2 instance role (AWS identity resolution — `aws sts get-caller-identity`
#      ambiently resolves the launch-time IAM instance profile, no env override needed) AND the full
#      non-interactive toolchain install (base/gh/gcloud/aws/uv/python3.13/node/claude-code) +
#      `verify()`, end to end, exit 0.
#   ❌ STILL NOT PROVEN — blocked by the SSM-channel-death gotcha above, not a container limitation:
#        · GCP ADC (interactive; STEP 2b's trim depends on runner-user ADC) — deliberately out of scope
#          for a throwaway host per the security-scoping note in
#          `/plans/active/ci_satellite_ao_dispatch_batch13_2026_08_13.md`'s own todo write-up
#        · systemd — so `setup-glue-runners.sh install` (units, slice, timer) is UNTESTED end-to-end
#        · actual runner registration against GitHub
#   Do not upgrade either of those two to "works" off the toolchain-install pass alone.
#
# TOOL INVENTORY — measured 2026-07-16 across the 38 MOVE workflows (occurrence counts):
#   gh 181 · jq 111 · python3 105 · uv 32 · aws 22 · gcloud 16 · pip 15 · npm 1
#   docker: NOT needed — its hits are a step *named* `docker-build` (which only dispatches to Cloud
#   Build) plus the Artifact Registry hostname in `gcloud artifacts docker images describe`.
#   Regenerate:
#     MOVE=$(bash classify-glue-workflows.sh | awk '$2=="MOVE"{print $1}')
#     for f in $MOVE; do rg -o --no-filename '\b(jq|yq|docker|node|npm|npx|python3|pip|uv|gh|gcloud|aws|prettier)\b' \
#       "../../.github/workflows/$f"; done | sort | uniq -c | sort -rn
#
#   sudo ./bootstrap-ci-host.sh            # provision everything, then verify
#   sudo ./bootstrap-ci-host.sh --check    # verify only (no install) — same as setup preflight
#
# After this succeeds:
#   1. authenticate:  gh auth login   (or seed a PAT)  +  gcloud auth application-default login
#   2. sudo GH_PAT=… ./setup-glue-runners.sh install
#
# GOTCHA (found 2026-08-22, live bare-EC2-host verification via SSM): clone this repo under a path
# RUNNER_USER can traverse (e.g. /home/ubuntu/...), never under /root — /root's default 700 perms
# block `sudo -u ${RUNNER_USER} uv ...` from even OPENING a relative uv.toml, surfacing as a
# confusing "Permission denied" on `uv python install`, not an obviously-CWD-related error.
#
# GOTCHA (found 2026-08-22, same session, UNRESOLVED): on a fresh bare host reached ONLY via SSM (no
# SSH), `setup-glue-runners.sh install` reliably killed the SSM command channel itself (document
# worker crashes with "ipc messaging received timeout signal") — reproduced 3x across t3.small,
# t3.medium, and t3.medium with CpuCredits=unlimited, ruling out both memory pressure and CPU-credit
# throttling. The SSM agent's own ping channel stayed Online throughout; only NEW send-command
# document-worker executions kept failing afterward, on that exact same instance, indefinitely. Prime
# suspect (not yet confirmed — the channel was lost before process-tree evidence could be captured):
# the runner's own `installdependencies.sh` apt step triggers `needrestart` to actually bounce
# `snap.amazon-ssm-agent.amazon-ssm-agent.service` (this script's own base-package apt step already
# shows needrestart FLAGGING that unit as "deferred" — install_repo_python/setup-glue-runners.sh may
# be what tips it from deferred to actually restarted), which severs the very channel running the
# command. If reproduced again: capture `journalctl -u snap.amazon-ssm-agent.amazon-ssm-agent.service
# --since -10min` and `needrestart -r a` output BEFORE the channel dies, and consider pre-satisfying
# every package `installdependencies.sh` would touch so its apt step becomes a no-op.
set -euo pipefail

RUNNER_USER="${RUNNER_USER:-ubuntu}"
# The version pyproject declares (requires-python >=3.13,<3.14) — NOT the distro's. The slot venv is
# built on this and IS the runner's python3, which is what lets movers drop actions/setup-python.
REPO_PY="${REPO_PY:-3.13}"
# Where this script lives — verify() reads the runner's PATH out of the sibling unit file so the two
# can never drift apart.
_BOOTSTRAP_HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_ONLY=false
[ "${1:-}" = "--check" ] && CHECK_ONLY=true

log() { printf '\033[36m[bootstrap]\033[0m %s\n' "$*"; }
warn() { printf '\033[33m[bootstrap] WARN:\033[0m %s\n' "$*" >&2; }
die() { printf '\033[31m[bootstrap] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

if [ "${CHECK_ONLY}" = false ]; then
  [ "$(id -u)" -eq 0 ] || die "must run as root (sudo) — it installs system packages"
fi

# ── 1. base OS packages ────────────────────────────────────────────────────────────────────────
# Two of these are the "assumed present" class this script exists to kill — both FOUND EMPIRICALLY by
# running this against a bare ubuntu:24.04 container (2026-07-16), not by reasoning:
#
#   sudo        — this script itself calls `sudo -u ${RUNNER_USER}` (uv install, verify). Ubuntu
#                 CLOUD images ship sudo, so the dependency is invisible on planning-VM and would
#                 have surfaced only on a minimal/hardened image, mid-incident. Container proved it:
#                 "line 127: sudo: command not found".
#   python3-venv — a SEPARATE package from python3 on Ubuntu. `command -v python3` reports present
#                 while `python3 -m venv` fails, and setup-glue-runners.sh builds the slot venv with
#                 exactly that. Silent until the slot build.
#
# libicu-dev is required by the Actions runner binary itself (installdependencies.sh).
# ripgrep found MISSING on a real bare-VM run (2026-08-03, ci_runner_fleet_split_and_vm_rightsizing
# canary): base-service.sh's own [0/6] ENVIRONMENT check hard-requires `rg` and fails every QG
# invocation immediately if absent — this is exactly the "assumed present" class this script exists
# to kill, just never hit until a real fresh VM ran quality-gates.sh for real.
install_base() {
  log "apt-get update + base packages"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq --no-install-recommends \
    sudo ca-certificates curl gnupg lsb-release \
    git jq python3 python3-venv python3-pip \
    libicu-dev ripgrep
  log "base packages OK"
}

# ── 2. gh (GitHub CLI) — 181 uses, the single biggest dep ───────────────────────────────────────
# NOTE (found 2026-07-26): `have gh && return` used to skip repo setup ENTIRELY whenever any gh
# binary pre-existed — on a box where gh came pre-installed from Ubuntu's own `noble` universe
# archive (not this script), that left the official cli.github.com apt source never configured,
# silently pinning gh at whatever Ubuntu ships (measured: 2.45.0, ~6 months stale) forever, since
# re-runs kept short-circuiting on the same check. `apt-cache policy gh` is the tell: a real
# official-repo install shows `500 https://cli.github.com/packages stable/main` as a candidate
# source; Ubuntu-only shows just the `noble`/`noble-updates` universe lines. This bit
# escalate-to-orchestrator.yml's `gh pr edit --add-label` step, which started hard-failing on a
# GraphQL "Projects (classic) deprecated" error that only reproduces on the old client.
install_gh() {
  if [ ! -f /etc/apt/sources.list.d/github-cli.list ]; then
    log "gh present but not from the official apt repo (or absent) — configuring cli.github.com"
    install -d -m 0755 /etc/apt/keyrings
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
    chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list
    apt-get update -qq
  fi
  apt-get install -y -qq gh
  log "gh: $(gh --version | head -1)"
}

# ── 3. gcloud — 16 uses (Firestore writes, Artifact Registry, Cloud Build dispatch) ─────────────
install_gcloud() {
  have gcloud && { log "gcloud present"; return; }
  log "installing google-cloud-cli from the official apt repo"
  install -d -m 0755 /etc/apt/keyrings
  curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | gpg --dearmor -o /etc/apt/keyrings/cloud.google.gpg
  echo "deb [signed-by=/etc/apt/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    > /etc/apt/sources.list.d/google-cloud-sdk.list
  apt-get update -qq
  apt-get install -y -qq google-cloud-cli
}

# ── 4. aws cli v2 — 22 uses ────────────────────────────────────────────────────────────────────
install_aws() {
  have aws && { log "aws present"; return; }
  log "installing awscli v2"
  local arch tmp
  case "$(uname -m)" in
    x86_64) arch=x86_64 ;;
    aarch64) arch=aarch64 ;;
    *) die "unsupported arch for awscli v2: $(uname -m)" ;;
  esac
  tmp="$(mktemp -d)"
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${arch}.zip" -o "${tmp}/awscliv2.zip"
  have unzip || apt-get install -y -qq unzip
  unzip -q "${tmp}/awscliv2.zip" -d "${tmp}"
  "${tmp}/aws/install" --update
  rm -rf "${tmp}"
}

# ── 5. uv — 32 uses (the repo's Python toolchain) ───────────────────────────────────────────────
# Installed FOR the runner user, not root: the runners execute as ${RUNNER_USER} and resolve uv from
# that user's PATH. Installing as root would put it in /root/.local and be invisible to the runner —
# exactly the assumed-present class this script exists to kill.
install_uv() {
  if sudo -u "${RUNNER_USER}" bash -lc 'command -v uv' >/dev/null 2>&1; then
    log "uv present for ${RUNNER_USER}"; return
  fi
  log "installing uv for ${RUNNER_USER}"
  sudo -u "${RUNNER_USER}" bash -lc 'curl -LsSf https://astral.sh/uv/install.sh | sh' \
    || die "uv install failed for ${RUNNER_USER}"
}

# ── 5b. Python ${REPO_PY} — the version the REPO declares, not the one the distro ships ──────────
# THE POINT OF A LONG-LIVED VM IS THAT THE TOOLS ARE ALREADY HERE (operator 2026-07-16).
#
# pyproject declares requires-python >=3.13,<3.14; Ubuntu 24.04 ships 3.12.3 and has NO python3.13 in
# apt. Without this step the slot venv gets built on 3.12, which is precisely why 5 movers still
# carried `actions/setup-python` and re-downloaded a THIRD copy of Python on EVERY job — the
# ephemeral-hosted model rebuilt on hardware we already pay for 24/7, keeping only the downsides
# (wasted wall-clock, ~400MB per runner, and the shared-tool-cache race that took the pool down).
# "The box doesn't have that version" is a BOOTSTRAP gap. This is where it gets fixed.
#
# uv, not deadsnakes: 3.13 is not in noble's apt and a third-party PPA on the live orchestrator VM is
# not a trade worth making. uv is already the repo's Python toolchain and fetches the SAME
# python-build-standalone builds actions/setup-python does — so this is the same interpreter, just
# resident instead of re-downloaded per job.
install_repo_python() {
  if sudo -u "${RUNNER_USER}" bash -lc "uv python find ${REPO_PY}" >/dev/null 2>&1; then
    log "Python ${REPO_PY} already present for ${RUNNER_USER} (uv-managed)"; return
  fi
  log "installing Python ${REPO_PY} for ${RUNNER_USER} via uv (repo requires >=3.13,<3.14)"
  sudo -u "${RUNNER_USER}" bash -lc "uv python install ${REPO_PY}" \
    || die "uv python install ${REPO_PY} failed — the slot venv cannot satisfy requires-python without it"
}

# ── 6. node/npm — exactly 1 use in the MOVE set ────────────────────────────────────────────────
# Advisory: only one mover references npm. Installed for completeness so the failsafe host is a true
# superset; if this ever becomes the only reason to carry the nodejs package, drop it and mark that
# one workflow KEEP instead.
install_node() {
  have npm && { log "npm present"; return; }
  log "installing nodejs/npm (1 mover references it)"
  apt-get install -y -qq nodejs npm || warn "nodejs/npm install failed — only 1 mover needs it; continuing"
}

# ── 6b. claude-code CLI — rules-alignment-agent runs `npm install -g @anthropic-ai/claude-code` ──
# Pre-installed for the same reason as Python: a long-lived VM that re-downloads its toolchain per
# job is a hosted runner with extra steps (operator 2026-07-16). An `npm install -g` on every run
# also MUTATES a shared host — the same class as the `sudo apt-get` we guarded in
# workspace-quickmerge-validation, and it can fail on a transient registry blip for a workflow that
# has nothing to do with npm.
#
# NOTE (measured on planning-VM 2026-07-16): this box ALREADY carries two claude installs at
# different versions — npm-global /usr/bin/claude 2.1.145 and ubuntu's ~/.local/bin/claude 2.1.202.
# The runner PATH puts ~/.local/bin FIRST, so a job gets 2.1.202. That drift predates this epic and
# is left alone deliberately: the AO depends on its own copy, and unifying them is not this plan's
# call to make. Recorded so the next person is not surprised by `claude --version` disagreeing with
# `npm ls -g`.
install_claude_code() {
  if sudo -u "${RUNNER_USER}" bash -lc 'command -v claude' >/dev/null 2>&1; then
    log "claude-code present for ${RUNNER_USER} ($(sudo -u "${RUNNER_USER}" bash -lc 'claude --version' 2>/dev/null | head -1))"
    return
  fi
  have npm || { warn "npm absent — skipping claude-code (1 mover needs it)"; return; }
  log "installing @anthropic-ai/claude-code globally (1 mover: rules-alignment-agent)"
  npm install -g @anthropic-ai/claude-code \
    || warn "claude-code install failed — only rules-alignment-agent needs it; continuing"
}

# ── 7. verify ──────────────────────────────────────────────────────────────────────────────────
verify() {
  local missing=0 t
  log "verifying toolchain parity vs ubuntu-latest:"
  for t in git jq python3 gh gcloud aws curl rg; do
    if have "${t}"; then printf '  \033[32m✓\033[0m %-10s %s\n' "${t}" "$(command -v "${t}")"
    else printf '  \033[31m✗\033[0m %-10s MISSING\n' "${t}"; missing=$((missing + 1)); fi
  done
  # python3 -m venv is the one that bites: python3 can be present while venv is not.
  #
  # MEASURED 2026-07-16 on planning-VM: `python3 -m venv --help` SUCCEEDS on a box where creating a
  # venv FAILS with "ensurepip is not available" — --help never touches ensurepip. The old --help
  # probe therefore reported venv ✓ on a host where setup-glue-runners.sh install would die at the
  # slot-venv step. Only building a real (throwaway) venv proves it.
  local _venv_probe; _venv_probe="$(mktemp -d)"
  if python3 -m venv "${_venv_probe}/v" >/dev/null 2>&1; then
    printf '  \033[32m✓\033[0m %-10s (python3 -m venv creates a real venv)\n' "venv"
  else
    printf '  \033[31m✗\033[0m %-10s BROKEN — install python3-venv (a passing --help means nothing)\n' "venv"
    missing=$((missing + 1))
  fi
  rm -rf "${_venv_probe}"

  # uv + the rest resolve from the RUNNER's PATH — which is NOT root's and NOT a login shell's.
  #
  # MEASURED 2026-07-16: the old probe was `sudo -u ubuntu bash -lc 'command -v uv'`. The -l makes it
  # a LOGIN shell, which sources ~/.profile and finds ~/.local/bin/uv — so it reported ✓ while the
  # runner (systemd, no ~/.profile) could not see uv at all. GitHub Actions `run:` steps are
  # non-login shells, so the unit's PATH is the only environment that counts. Read it from the unit
  # file to keep ONE source of truth, and scrub the env (`env -i`) so nothing inherited can fake it.
  local _unit="${_BOOTSTRAP_HERE}/github-glue-runner@.service" _rp=""
  [ -f "${_unit}" ] && _rp="$(sed -n 's/^Environment=PATH=//p' "${_unit}" | head -1)"
  if [ -z "${_rp}" ]; then
    warn "cannot read Environment=PATH from ${_unit} — falling back to systemd's default PATH for the uv probe"
    _rp="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/snap/bin"
  fi
  if sudo -u "${RUNNER_USER}" env -i PATH="${_rp}" HOME="/home/${RUNNER_USER}" \
       bash -c 'command -v uv' >/dev/null 2>&1; then
    printf '  \033[32m✓\033[0m %-10s (as %s, on the RUNNER PATH)\n' "uv" "${RUNNER_USER}"
  else
    printf '  \033[31m✗\033[0m %-10s not on the RUNNER PATH for %s — 32 movers invoke uv\n' "uv" "${RUNNER_USER}"
    missing=$((missing + 1))
  fi

  # The REPO's python must be RESIDENT on the box. If it is not, the slot venv falls back to the
  # distro's 3.12, every mover is forced to carry actions/setup-python, and the long-lived VM buys
  # us nothing over a hosted one. This check is the difference between those two worlds.
  if sudo -u "${RUNNER_USER}" bash -lc "uv python find ${REPO_PY}" >/dev/null 2>&1; then
    printf '  \033[32m✓\033[0m %-10s %s resident (uv-managed) — movers need no setup-python\n' "python${REPO_PY}" "$(sudo -u "${RUNNER_USER}" bash -lc "uv python find ${REPO_PY}" 2>/dev/null)"
  else
    printf '  \033[31m✗\033[0m %-10s MISSING — repo requires >=3.13,<3.14; distro ships %s\n' "python${REPO_PY}" "$(python3 --version 2>&1)"
    missing=$((missing + 1))
  fi

  if have npm; then printf '  \033[32m✓\033[0m %-10s %s\n' "npm" "$(command -v npm)"
  else warn "npm missing — 1 MOVE workflow references it"; fi
  # Advisory, not fatal: exactly one mover needs it, and a bare box is legitimately without it until
  # install_claude_code runs.
  if sudo -u "${RUNNER_USER}" bash -lc 'command -v claude' >/dev/null 2>&1; then
    printf '  \033[32m✓\033[0m %-10s %s (as %s)\n' "claude" "$(sudo -u "${RUNNER_USER}" bash -lc 'claude --version' 2>/dev/null | head -1)" "${RUNNER_USER}"
  else
    warn "claude-code missing for ${RUNNER_USER} — rules-alignment-agent would npm-install it per run"
  fi
  [ "${missing}" -eq 0 ] || die "${missing} required tool(s) missing"
  log "toolchain OK"

  # Creds are NOT provisioned here — they are interactive/instance-specific. Report, don't fail:
  # a bare box legitimately reaches this point unauthenticated.
  log "credential state (provision these BEFORE setup-glue-runners.sh install):"
  if sudo -u "${RUNNER_USER}" gh auth status >/dev/null 2>&1; then
    printf '  \033[32m✓\033[0m gh authenticated (as %s)\n' "${RUNNER_USER}"
  else warn "gh NOT authenticated for ${RUNNER_USER} — run: gh auth login  (needed for the slot clone)"; fi
  if sudo -u "${RUNNER_USER}" gcloud auth application-default print-access-token >/dev/null 2>&1; then
    printf '  \033[32m✓\033[0m GCP ADC present (as %s)\n' "${RUNNER_USER}"
  else warn "GCP ADC missing for ${RUNNER_USER} — run: gcloud auth application-default login  (STEP 2b drops the auth step and relies on this)"; fi
  if aws sts get-caller-identity >/dev/null 2>&1; then
    printf '  \033[32m✓\033[0m AWS identity resolves\n'
  else warn "AWS identity does not resolve — instance role or credentials needed"; fi
}

if [ "${CHECK_ONLY}" = true ]; then
  verify
  exit 0
fi

install_base
install_gh
install_gcloud
install_aws
install_uv
install_repo_python
install_node
install_claude_code
verify

cat <<'NEXT'

[bootstrap] Host is provisioned. NEXT STEPS (not automated — they need secrets/interaction):
  1. sudo -u ubuntu gh auth login                              # slot clone + runner registration
  2. sudo -u ubuntu gcloud auth application-default login      # STEP 2b relies on runner-user ADC
  3. sudo GH_TOKEN_SECRET=GH_PAT ./setup-glue-runners.sh install   # register both pools (no PAT on disk)
  4. ./setup-glue-runners.sh status                            # both pools Online, slot clone fresh

If ANY of the above revealed a missing tool or assumption, ADD IT TO THIS SCRIPT NOW — that is the
only thing that keeps this failsafe true.
NEXT
