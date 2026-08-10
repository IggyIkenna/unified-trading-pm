#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1 self-hosted glue runners)
# Lifecycle: permanent
# Delete-when: glue moves to serverless (B2) or a managed runner (B3) and this host is retired
#
# setup-glue-runners.sh — install / manage the TWO glue runner pools on THIS host (the planning /
# orchestrator VM) to absorb unified-trading-pm's CI "glue" workflows.
#
# Runs ON the VM as a sudo-capable user. All glue workflows live in unified-trading-pm, so runners
# register to that ONE repo (a personal account has no org-level runners — repo-scoped is correct).
#
#   POOLS (see glue-runner-run.sh for the full rationale)
#     glue-N     JIT-ephemeral   labels self-hosted,glue          -> the ~37 low-frequency movers
#     writer-N   long-lived      labels self-hosted,glue-writer   -> ci-status-update (~13k/mo, ~3s)
#   The labels are DISJOINT on purpose: label matching is a subset test, so a writer carrying `glue`
#   would also match `runs-on: [self-hosted, glue]` and steal the movers' jobs.
#
#   THE SLOT (isolation scope = folder/venv/clone only; operator 2026-07-16)
#     ${RUNNER_BASE}/repo       runner-OWNED clone (never an AO slot clone) — pre-staged code for the
#                               writer so it does NO checkout; kept current by the refresh timer.
#     ${RUNNER_BASE}/venv       dedicated venv (google-cloud-firestore for STEP 2b) — not AO/system.
#     <runner>/toolcache        PER-RUNNER RUNNER_TOOL_CACHE (a sibling of _work, so the JIT wipe does
#                               not destroy it). NOT shared: actions/setup-python is delete-then-create
#                               and races across concurrent runners — see glue-runner-run.sh.
#   User stays `ubuntu` and reuses the VM's existing GCP/AWS/GitHub creds + toolchain, deliberately:
#   everything needing true clean-room isolation is GitHub-hosted and stays there.
#
#   THE ADMIN TOKEN — exactly ONE of these, and GH_TOKEN_SECRET is the one you want
#     GH_TOKEN_SECRET=<name>  PREFERRED. Names a GCP Secret Manager secret (on this VM: GH_PAT). Only
#                             the NAME lands in ${ENV_FILE}; the wrapper resolves the token per start
#                             via the VM's ADC, so no credential is ever written to disk.
#     GH_PAT=<token>          LEGACY. Writes the literal token into ${ENV_FILE} (0600 root). Only for
#                             a host with no ADC.
#
#   sudo GH_TOKEN_SECRET=GH_PAT ./setup-glue-runners.sh install  # download+verify, build slot, start pools
#   ./setup-glue-runners.sh status                               # systemd + slot freshness + live runners
#   ./setup-glue-runners.sh preflight                            # verify the VM has the tools the movers need
#   sudo ./setup-glue-runners.sh teardown                        # stop+remove everything
#   ./setup-glue-runners.sh prune                                # delete leftover OFFLINE EPHEMERAL runners
#
# Tunables (env): GLUE_COUNT (1) · WRITER_COUNT (3) · RUNNER_BASE (/opt/github-glue-runners) ·
#   OWNER (IggyIkenna) · REPO (unified-trading-pm) · RUNNER_VERSION · GCP_PROJECT (optional, pairs
#   with GH_TOKEN_SECRET) · GH_TOKEN_SECRET | GH_PAT (admin token — see above) · POOL_TAG (see below)
#
# POOL_TAG — run a SECOND (THIRD, ...) independent pool on this same host for a DIFFERENT repo,
# without touching PM's pool at all (qg_backfill... no — this is
# github_actions_operator_gated_followups_2026_07_17.md's "setup-glue-runners.sh cannot safely
# register a second repo's runner pool" P0 finding). Default empty ⇒ every path/name below is
# BYTE-IDENTICAL to before this existed (ENV_FILE/RUNNER_BASE/unit names all unchanged) — zero
# behavior change for PM. Set POOL_TAG=<slug> (e.g. `ao`) and this pool's ENV_FILE, RUNNER_BASE
# default, and all six systemd unit names get a `-<slug>` suffix, so a second `install` with a
# different POOL_TAG is ADDITIVE (new files/units) rather than overwriting PM's live pool — the
# exact clobber the P0 finding warned about (PM's glue-N/writer-N re-reading a rewritten shared
# ENV_FILE on their next JIT restart, minutes away).
set -euo pipefail

OWNER="${OWNER:-IggyIkenna}"
REPO="${REPO:-unified-trading-pm}"
# 13k/mo ≈ 18/hr at ~3s each is trivial for one writer; 3 is burst headroom (a fleet-wide event can
# fire ~24 repos at once). The ephemeral pool absorbs the ~37 low-frequency movers.
# GLUE_COUNT default lowered 5->1 (capacity-planning ruling, orchestrator_vm_disk_io_contention_
# runner_burst_2026_07_28.md): registering GLUE_COUNT=5 pools per repo across a same-time multi-repo
# bulk onboarding (23 repos at once, 2026-07-28) drove the shared host into sustained 66-93% iowait
# and starved the operator's own interactive AO slot-workers (D-state). The fix that actually cleared
# it (scaling every newly-onboarded pool down to 1 glue runner) is now the standing default, not a
# one-off mitigation — override explicitly (GLUE_COUNT=2) only for the two original high-traffic
# pools (unified-trading-pm, agent-orchestrator) that predate this ruling.
GLUE_COUNT="${GLUE_COUNT:-1}"
WRITER_COUNT="${WRITER_COUNT:-3}"
RUNNER_VERSION="${RUNNER_VERSION:-2.335.1}"
RUNNER_SHA256="${RUNNER_SHA256:-4ef2f25285f0ae4477f1fe1e346db76d2f3ebf03824e2ddd1973a2819bf6c8cf}" # linux-x64 2.335.1
RUNNER_USER="${RUNNER_USER:-ubuntu}"
UNIT_DIR="/etc/systemd/system"

POOL_TAG="${POOL_TAG:-}"
_TAG_SUFFIX="${POOL_TAG:+-${POOL_TAG}}"
RUNNER_BASE="${RUNNER_BASE:-/opt/github-glue-runners${_TAG_SUFFIX}}"
ENV_FILE="${ENV_FILE:-/etc/github-glue-runner${_TAG_SUFFIX}.env}"
# Every systemd unit name this script installs/enables/tears down — ALL derived from ONE prefix per
# base name, so a POOL_TAG can never make two of these agree by accident (the exact bug class this
# fix exists to close: names/paths computed independently, one updated and one forgotten).
RUNNER_UNIT_PREFIX="github-glue-runner${_TAG_SUFFIX}"
SLOT_REFRESH_PREFIX="github-glue-slot-refresh${_TAG_SUFFIX}"
TOKEN_REFRESH_PREFIX="github-glue-token-refresh${_TAG_SUFFIX}"
SLICE_NAME="${RUNNER_UNIT_PREFIX}.slice"
TEMPLATE_UNIT="${RUNNER_UNIT_PREFIX}@.service"
SLOT_REFRESH_SERVICE="${SLOT_REFRESH_PREFIX}.service"
SLOT_REFRESH_TIMER="${SLOT_REFRESH_PREFIX}.timer"
TOKEN_REFRESH_SERVICE="${TOKEN_REFRESH_PREFIX}.service"
TOKEN_REFRESH_TIMER="${TOKEN_REFRESH_PREFIX}.timer"
# The runtime (tmpfs) dir name happens to share the runner-unit prefix — same "github-glue-runner"
# root the token cache has always lived under, just pool-tagged like everything else.
RUNTIME_DIR_NAME="${RUNNER_UNIT_PREFIX}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARBALL="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${TARBALL}"
SLOT_REPO="${RUNNER_BASE}/repo"
SLOT_VENV="${RUNNER_BASE}/venv"
# Must satisfy pyproject's requires-python (>=3.13,<3.14). The slot venv IS the runner's python3
# (first on the unit PATH), which is what lets the movers drop actions/setup-python entirely.
SLOT_PY="${SLOT_PY:-3.13}"
# SSOT for what the slot venv provides (and which workflow needs each). Pre-installed so no mover
# downloads at job time — the whole point of a long-lived VM.
SLOT_REQS="${SLOT_REQS:-${HERE}/slot-venv-requirements.txt}"

log() { printf '\033[36m[glue-runners]\033[0m %s\n' "$*"; }
warn() { printf '\033[33m[glue-runners] WARN:\033[0m %s\n' "$*" >&2; }
die() { printf '\033[31m[glue-runners] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# Read a Secret Manager secret AS ${RUNNER_USER} whenever we are root — the ONE way this script
# touches Secret Manager, so the rule below cannot be applied in some paths and forgotten in others.
#
# LOAD-BEARING, and it cuts BOTH ways (both halves measured on planning-VM 2026-07-16):
#   • install runs under sudo but the WRAPPER runs as ${RUNNER_USER}. Probing as root would prove
#     nothing about the account that actually resolves this secret on every runner start.
#   • root on this box has NO ADC at all, so resolving as root simply FAILS — which is exactly how
#     `status` came back "no admin token resolvable" while the runners were resolving it fine.
# Either way the answer is the same: ask the account that owns the ADC.
secret_access() {
  local secret="$1" project="${2:-}"
  if [ "$(id -u)" -eq 0 ]; then
    sudo -u "${RUNNER_USER}" gcloud secrets versions access latest --secret="${secret}" \
      ${project:+--project="${project}"} 2>/dev/null || true
  else
    gcloud secrets versions access latest --secret="${secret}" \
      ${project:+--project="${project}"} 2>/dev/null || true
  fi
}

# HTTP status of the registration-token POST — the honest probe for Administration:write, because it
# is exactly the call the wrapper makes. The minted token expires in 1h and we discard it, so this is
# free. No -f: we want the code, not a curl failure.
probe_admin_write() {
  curl -sS -o /dev/null -w '%{http_code}' -X POST \
    -H "Authorization: Bearer ${1}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/${OWNER}/${REPO}/actions/runners/registration-token" 2>/dev/null || true
}

# Best-effort admin token for the API-touching subcommands (status/prune), mirroring the wrapper's
# precedence: explicit env > whatever install recorded in ${ENV_FILE} > nothing. Prints empty rather
# than dying so `status` degrades to "no live listing" instead of failing outright.
#
# ${ENV_FILE} is 0600 root, so the file paths here only fire under sudo — that is intended, not a bug:
# reading it is a privileged act.
resolve_admin_token() {
  if [ -n "${GH_PAT:-}" ]; then printf '%s' "${GH_PAT}"; return 0; fi
  if [ -n "${GH_TOKEN:-}" ]; then printf '%s' "${GH_TOKEN}"; return 0; fi

  local secret="${GH_TOKEN_SECRET:-}" project="${GCP_PROJECT:-}" literal=""
  if [ -r "${ENV_FILE}" ]; then
    [ -n "${secret}" ] || secret="$(sed -n 's/^GH_TOKEN_SECRET=//p' "${ENV_FILE}" | head -1)"
    [ -n "${project}" ] || project="$(sed -n 's/^GCP_PROJECT=//p' "${ENV_FILE}" | head -1)"
    literal="$(sed -n 's/^GH_TOKEN=//p' "${ENV_FILE}" | head -1)"
  fi
  # A legacy (GH_PAT-path) install put the literal token in the file; the secret path did not.
  if [ -z "${secret}" ] && [ -n "${literal}" ]; then printf '%s' "${literal}"; return 0; fi
  if [ -n "${secret}" ]; then
    secret_access "${secret}" "${project}"
  fi
}

# All instance names, e.g. "glue-1 glue-2 ... writer-1 ...". The instance name IS <pool>-<index>;
# glue-runner-run.sh forks on the pool prefix.
all_instances() {
  local i
  for i in $(seq 1 "${GLUE_COUNT}"); do echo "glue-${i}"; done
  for i in $(seq 1 "${WRITER_COUNT}"); do echo "writer-${i}"; done
}

# The runner's PATH, read from the unit file so there is exactly ONE source of truth. Parsing it
# (rather than duplicating the string here) means preflight can never green-light a PATH the runner
# will not actually have.
#
# The checked-in template's PATH is PM's literal /opt/github-glue-runners — under a non-empty
# POOL_TAG that is NOT what the installed unit will actually contain (render_unit substitutes it to
# ${RUNNER_BASE}), so this applies the SAME substitution here. Without it, preflight for a second
# pool silently probes PM's already-built venv (python3/uv both "resolve" via PM's path) instead of
# reporting the truth: this pool's venv does not exist until install builds it.
runner_path() {
  local p
  p="$(sed -n 's/^Environment=PATH=//p' "${HERE}/github-glue-runner@.service" | head -1)"
  [ -n "${p}" ] || die "no 'Environment=PATH=' in ${HERE}/github-glue-runner@.service — refusing to guess the runner's PATH"
  printf '%s' "${p}" | sed "s#/opt/github-glue-runners#${RUNNER_BASE}#g"
}

# Run a command EXACTLY as a job step will: as ${RUNNER_USER}, on the unit's PATH, with the env
# SCRUBBED (`env -i`) so no inherited PATH can leak in and fake a pass.
run_as_runner() {
  local rp="$1" cmd="$2"
  if [ "$(id -u)" -eq 0 ]; then
    sudo -u "${RUNNER_USER}" env -i PATH="${rp}" HOME="/home/${RUNNER_USER}" bash -c "${cmd}" 2>/dev/null
  else
    env -i PATH="${rp}" HOME="${HOME:-/home/${RUNNER_USER}}" bash -c "${cmd}" 2>/dev/null
  fi
}

probe_tool() { run_as_runner "$1" "command -v $2"; }

# The MOVE set's tool inventory (measured 2026-07-16): gh 181 · jq 111 · python3 105 · uv 32 · aws 22
# · gcloud 16 · pip 15 · npm 1. docker is NOT needed (its hits are a step *name* that dispatches to
# Cloud Build, plus the Artifact Registry hostname in `gcloud artifacts docker images describe`).
# Hosted ubuntu-latest ships all of this; this VM is the one that has to be checked.
#
# WHY THIS PROBES THE UNIT'S PATH AND NOT THE CALLER'S (learned the hard way, 2026-07-16): the first
# version of this checked `command -v` in whatever shell invoked it. Run from an interactive/login
# shell it reported uv ✓ — while the runner, which systemd starts WITHOUT ~/.profile, could not see
# uv at all. A preflight that passes in a shell the runner never uses is worse than no preflight: it
# is a confident green on a box that will fail 32 of the 38 movers.
cmd_preflight() {
  local missing=0 t rp resolved
  rp="$(runner_path)"
  log "toolchain parity vs ubuntu-latest, resolved as ${RUNNER_USER} on the RUNNER's PATH:"
  printf '  PATH=%s\n' "${rp}"
  for t in gh jq python3 uv aws gcloud git; do
    resolved="$(probe_tool "${rp}" "${t}")"
    if [ -n "${resolved}" ]; then
      printf '  \033[32m✓\033[0m %-8s %s\n' "${t}" "${resolved}"
    else
      printf '  \033[31m✗\033[0m %-8s MISSING on the runner PATH\n' "${t}"; missing=$((missing + 1))
    fi
  done

  # pip is 15 uses across 12 movers and is the subtlest failure on this host (MEASURED 2026-07-16):
  # Ubuntu 24.04's system python has NO pip AND ships /usr/lib/python3.12/EXTERNALLY-MANAGED, so the
  # 8 movers running `python3 -m pip install "google-cloud-firestore>=2,<3"` fail twice over. Hosted
  # ubuntu-latest has neither restriction. The slot venv, FIRST on the unit PATH, is what makes those
  # movers work unmodified — its python has pip and is not externally-managed.
  #
  # This check is PHASE-AWARE on purpose: install BUILDS that venv, so demanding pip before install
  # would block install for a reason install itself fixes. Before install the honest question is
  # "can a venv be built here" (that is the real precondition — python3-venv is a separate package
  # and its absence is invisible until the slot build); after install it is "does pip actually
  # resolve on the runner's PATH".
  if [ -x "${SLOT_VENV}/bin/python" ]; then
    # The version is a CONTRACT, not a detail: this python3 IS what the movers run, and the repo
    # declares requires-python >=3.13,<3.14. A 3.12 here is exactly the state that forced every
    # mover to carry actions/setup-python and re-download Python per job.
    resolved="$(run_as_runner "${rp}" 'python3 --version 2>&1')"
    if run_as_runner "${rp}" 'python3 -c "import sys; sys.exit(0 if (3,13) <= sys.version_info[:2] < (3,14) else 1)" && echo ok' | grep -q ok; then
      printf '  \033[32m✓\033[0m %-8s %s (satisfies requires-python >=3.13,<3.14)\n' "py-ver" "${resolved}"
    else
      printf '  \033[31m✗\033[0m %-8s %s does NOT satisfy requires-python >=3.13,<3.14\n' "py-ver" "${resolved}"
      printf '           the slot venv IS the runner python3 — rebuild it: setup-glue-runners.sh install\n'
      missing=$((missing + 1))
    fi
    resolved="$(run_as_runner "${rp}" 'python3 -m pip --version 2>&1 | head -1')"
    case "${resolved}" in
      *"No module named pip"*)
        printf '  \033[31m✗\033[0m %-8s slot venv exists but python3 has NO pip — 12 movers need it\n' "pip"
        missing=$((missing + 1)) ;;
      *) printf '  \033[32m✓\033[0m %-8s %s\n' "pip" "${resolved}" ;;
    esac
  else
    # The probe dir is created INSIDE the runner shell, not out here: preflight may run as root, and
    # a root-owned `mktemp -d` (0700) would make the venv fail with EACCES for ${RUNNER_USER} — a
    # false NEGATIVE that looks exactly like a missing python3-venv. Same class of bug as probing on
    # the wrong PATH, just pointing the other way.
    # shellcheck disable=SC2016  # single quotes are REQUIRED: $d must expand in the runner's shell,
    # not in this one — the temp dir has to be created by ${RUNNER_USER} for the probe to be honest.
    if run_as_runner "${rp}" \
         'd="$(mktemp -d)"; python3 -m venv "$d/v" >/dev/null 2>&1 && echo ok; rm -rf "$d"' \
       | grep -q ok; then
      printf '  \033[32m✓\033[0m %-8s (slot venv not built yet — install will create it and supply pip)\n' "pip"
    else
      printf '  \033[31m✗\033[0m %-8s python3 -m venv FAILS for %s — run bootstrap-ci-host.sh\n' "pip" "${RUNNER_USER}"
      printf '           without it install dies at the slot venv, and 12 movers lose pip\n'
      missing=$((missing + 1))
    fi
  fi

  # npm has exactly ONE use in the MOVE set — advisory, not fatal.
  resolved="$(probe_tool "${rp}" npm)"
  if [ -n "${resolved}" ]; then
    printf '  \033[32m✓\033[0m %-8s %s\n' npm "${resolved}"
  else
    warn "npm missing — 1 MOVE workflow references it; check before flipping that one"
  fi

  [ "${missing}" -eq 0 ] || die "${missing} required tool(s) missing on the RUNNER's PATH — fix by adding them to bootstrap-ci-host.sh and re-running it, NOT by hand-installing (a hand-fix leaves the failsafe lying)"
  log "preflight OK — every tool resolves in the environment the runner will actually have"
}

cmd_install() {
  [ "$(id -u)" -eq 0 ] || die "install must run as root (sudo) — it writes /etc and /opt"

  # --- admin token: EXACTLY ONE source ---------------------------------------------------------
  # Both set is an error rather than a precedence rule: they can disagree, and silently preferring
  # one would mean the token you THINK is registering runners isn't the one that is.
  local n=0
  if [ -n "${GH_TOKEN_SECRET:-}" ]; then n=$((n + 1)); fi
  if [ -n "${GH_PAT:-}" ]; then n=$((n + 1)); fi
  case "${n}" in
    0) die "set exactly one of GH_TOKEN_SECRET=<secret-name> (preferred — no PAT on disk; on this VM: GH_TOKEN_SECRET=GH_PAT) or GH_PAT=<token> (legacy)" ;;
    1) ;;
    *) die "GH_TOKEN_SECRET and GH_PAT are both set — pick one (they can disagree, and the wrapper would use GH_TOKEN_SECRET)" ;;
  esac

  local admin_tok=""
  if [ -n "${GH_TOKEN_SECRET:-}" ]; then
    log "resolving admin token as ${RUNNER_USER} from Secret Manager: ${GH_TOKEN_SECRET}${GCP_PROJECT:+ (project ${GCP_PROJECT})}"
    admin_tok="$(secret_access "${GH_TOKEN_SECRET}" "${GCP_PROJECT:-}")"
    [ -n "${admin_tok}" ] || die "cannot read secret '${GH_TOKEN_SECRET}' as ${RUNNER_USER}. gcloud ADC is per-user and the runners run as ${RUNNER_USER}, so it must work for THAT user (root's ADC is irrelevant). Check: sudo -u ${RUNNER_USER} gcloud secrets versions access latest --secret=${GH_TOKEN_SECRET}"
  else
    admin_tok="${GH_PAT}"
    warn "GH_PAT path — the literal token WILL be written to ${ENV_FILE} (0600 root). Prefer GH_TOKEN_SECRET on any host with ADC."
  fi

  # Fail here (one HTTP call) rather than at first start (8 crash-looping units + an opaque journal).
  local code
  code="$(probe_admin_write "${admin_tok}")"
  [ "${code}" = "201" ] || die "token lacks Administration:write on ${OWNER}/${REPO} — registration-token probe returned HTTP ${code}, want 201"
  log "token OK — Administration:write on ${OWNER}/${REPO} (probe 201)"
  unset admin_tok

  install -d -m 0755 "${RUNNER_BASE}"

  # 1) download + verify the pinned runner tarball ONCE
  local cache="${RUNNER_BASE}/${TARBALL}"
  if [ ! -f "${cache}" ]; then
    log "downloading ${URL}"
    curl -fsSL -o "${cache}" "${URL}"
  fi
  echo "${RUNNER_SHA256}  ${cache}" | sha256sum -c - || die "checksum mismatch for ${TARBALL}"
  log "checksum OK (${RUNNER_VERSION})"

  # 2) one runner dir per instance across BOTH pools (each needs its own _work/_diag)
  local inst dir first=""
  for inst in $(all_instances); do
    dir="${RUNNER_BASE}/${inst}"
    if [ ! -x "${dir}/run.sh" ]; then
      log "extracting runner -> ${dir}"
      install -d -m 0755 "${dir}"
      tar -xzf "${cache}" -C "${dir}"
    fi
    chown -R "${RUNNER_USER}:${RUNNER_USER}" "${dir}"
    [ -z "${first}" ] && first="${dir}"
  done
  # install OS deps once (uses any extracted copy)
  "${first}/bin/installdependencies.sh" >/dev/null 2>&1 || die "installdependencies.sh failed"

  # 3) the slot: shared tool cache + dedicated venv + runner-OWNED clone
  #
  # ${RUNNER_BASE} itself stays ROOT-owned so a runner cannot drop files at the top level; the runner
  # user owns only the subdirs it must write into. Pre-create all three: both `python3 -m venv` and
  # `git clone` CREATE their target directory, which needs write permission on the PARENT.
  # MEASURED failure 2026-07-16 when the parent was root-owned 0755 and only the target was chowned:
  #   Error: [Errno 13] Permission denied: '/opt/github-glue-runners/venv'
  # venv and git clone both accept an existing EMPTY dir, so pre-creating is the tight fix (rather
  # than handing the runner user ownership of ${RUNNER_BASE}).
  install -d -m 0755 -o "${RUNNER_USER}" -g "${RUNNER_USER}" "${SLOT_VENV}" "${SLOT_REPO}"
  # qg-host-governor.sh's shared reservation-ledger dir used to live under
  # /opt/.qg-governor-glue-shared (pre-created here, same root-owned-parent problem as above)
  # — REMOVED 2026-08-10 (ldr_qg_v2_ci_host_contention_false_wall_2026_08_03.md todo 2): every
  # interactive agent-orchestrator slot's shell runs sandboxed to /home+/tmp ReadWritePaths
  # (systemd ProtectSystem-style, confirmed live via /proc/self/mountinfo — /opt is genuinely
  # unreachable from that side), so the ledger root moved to
  # ${RUNNER_USER}'s own home (unified_trading_system_repos sibling — see
  # scripts/quality-gates-base/qg-host-governor.sh's _QG_HOST_SHARED_LEDGER_ROOT_DEFAULT),
  # which both this runner user and every interactive slot can already write to with zero new
  # provisioning. No pre-create needed here anymore — _qg_ledger_with_lock mkdir -p's it lazily.
  # PER-RUNNER tool cache (see glue-runner-run.sh for the measured race that killed the shared one).
  for inst in $(all_instances); do
    install -d -m 0755 -o "${RUNNER_USER}" -g "${RUNNER_USER}" "${RUNNER_BASE}/${inst}/toolcache"
  done

  # THE SLOT VENV IS THE RUNNER'S `python3` — it is FIRST on the unit PATH. So it must satisfy the
  # REPO's requires-python, not whatever the distro happens to ship.
  #
  # WHY THIS IS BUILT ON uv's 3.13 AND NOT `python3 -m venv` (operator 2026-07-16, and the sharpest
  # correction of this whole deploy): the system python3 here is 3.12.3 while pyproject declares
  # >=3.13,<3.14. Building the venv on the distro python is exactly WHY 5 movers still needed
  # actions/setup-python — every job downloaded a THIRD copy of Python onto a box that ALREADY had
  # the right one (uv keeps 3.13 under ~/.local/share/uv/python; the AO uses it). That is the
  # ephemeral-hosted model rebuilt on hardware we already pay for 24/7 — it keeps only the
  # downsides, and it is what made the shared tool cache race in the first place.
  #
  # uv, not apt/deadsnakes: 3.13 is NOT in noble's apt, and adding a third-party PPA to the live
  # orchestrator VM is not a trade worth making. uv is already the repo's Python toolchain (32 movers
  # invoke it) and fetches the SAME python-build-standalone builds actions/setup-python uses.
  # `--seed` is LOAD-BEARING: a bare `uv venv` has NO pip, and 8 movers run `python3 -m pip install`.
  local rp; rp="$(runner_path)"
  if ! "${SLOT_VENV}/bin/python" -c 'import sys; sys.exit(0 if (3,13) <= sys.version_info[:2] < (3,14) else 1)' 2>/dev/null; then
    log "building the slot venv on Python ${SLOT_PY} (repo requires >=3.13,<3.14) -> ${SLOT_VENV}"
    run_as_runner "${rp}" "uv python install ${SLOT_PY}" >/dev/null 2>&1 || true
    rm -rf "${SLOT_VENV:?}"/* "${SLOT_VENV:?}"/.[!.]* 2>/dev/null || true
    run_as_runner "${rp}" "uv venv --python ${SLOT_PY} --seed '${SLOT_VENV}'" >/dev/null 2>&1 \
      || die "uv venv --python ${SLOT_PY} --seed failed. Is uv on the runner PATH and can it fetch ${SLOT_PY}? Check: sudo -u ${RUNNER_USER} uv python install ${SLOT_PY}"
  fi
  local slot_py_ver
  slot_py_ver="$("${SLOT_VENV}/bin/python" --version 2>&1)"
  "${SLOT_VENV}/bin/python" -c 'import sys; sys.exit(0 if (3,13) <= sys.version_info[:2] < (3,14) else 1)' \
    || die "slot venv is ${slot_py_ver} — the repo requires >=3.13,<3.14 and this venv IS the runner's python3"
  log "slot venv OK — ${slot_py_ver} (satisfies requires-python; movers need no actions/setup-python)"

  # Pre-install EVERY dep the movers would otherwise install per-job (operator 2026-07-16: "so that we
  # are not doing similar install or download on the long-living vm and take the benefit of the vm
  # properly and fully"). The list — and WHICH workflow needs each — is the SSOT next door; keeping it
  # in a file rather than inline means the workflows and the venv can be diffed against one thing.
  # This is STEP 2b generalised: firestore alone made ci-status-update's per-run pip a no-op; the rest
  # do the same for the other movers.
  log "installing slot venv deps <- ${SLOT_REQS##*/}"
  [ -f "${SLOT_REQS}" ] || die "missing ${SLOT_REQS} — it is the SSOT for what the slot venv provides"
  sudo -u "${RUNNER_USER}" "${SLOT_VENV}/bin/pip" install --quiet --upgrade -r "${SLOT_REQS}" \
    || die "slot venv dep install failed (see ${SLOT_REQS})"
  local n_deps
  n_deps="$(grep -cvE '^\s*(#|$)' "${SLOT_REQS}")"
  log "slot venv provides ${n_deps} declared dep(s) — movers must NOT install these at runtime"

  # Clone via `gh` so we use the VM's EXISTING GitHub creds (operator decision) rather than embedding
  # a PAT in the remote URL, which would persist the token in .git/config.
  if [ ! -d "${SLOT_REPO}/.git" ]; then
    log "cloning ${OWNER}/${REPO} -> ${SLOT_REPO} (runner-owned; NEVER an AO slot clone)"
    sudo -u "${RUNNER_USER}" gh repo clone "${OWNER}/${REPO}" "${SLOT_REPO}" -- --depth 1 \
      || die "gh repo clone failed — check that 'gh auth status' is green for ${RUNNER_USER}"
  fi
  chown -R "${RUNNER_USER}:${RUNNER_USER}" "${SLOT_REPO}" "${SLOT_VENV}"

  # Seed the freshness stamp. Honest by construction: the clone was JUST made current, so install
  # time is genuinely when it was last fresh. Two reasons this is not merely cosmetic:
  #   • the refresh timer runs as ${RUNNER_USER} and rewrites this file, but CREATING a new file in
  #     the root-owned ${RUNNER_BASE} is denied — MEASURED 2026-07-16, the first tick failed with
  #     "refresh-slot-repo.sh: line 38: .../repo.refreshed-at: Permission denied". Pre-creating it
  #     owned by the runner user works because rewriting an EXISTING file needs write on the FILE.
  #   • without it, `status` reports the refresher broken for the first 10 minutes after install.
  date -u +%s > "${RUNNER_BASE}/repo.refreshed-at"
  chown "${RUNNER_USER}:${RUNNER_USER}" "${RUNNER_BASE}/repo.refreshed-at"
  chmod 0644 "${RUNNER_BASE}/repo.refreshed-at"

  # 3b) launcher-PRIVATE gcloud config dir (2026-07-18)
  # The token path must not read the runner user's shared ~/.config/gcloud. Self-hosted runners do
  # not reset HOME between jobs, so a job step running google-github-actions/auth writes a WIF
  # external_account credential there and makes it ACTIVE for every later process; its subject token
  # comes from actions-run-service and exists only INSIDE a job, so afterwards every Secret Manager
  # read fails 404 "job request not found" (2026-07-18: 1377 restarts, 2.5h fleet-wide CI outage).
  # refresh-gh-token.sh and glue-runner-run.sh point CLOUDSDK_CONFIG here as a COMMAND PREFIX.
  #
  install -d -o "${RUNNER_USER}" -g "${RUNNER_USER}" -m 0700 "${RUNNER_BASE}/.gcloud"

  # Seed it with the MACHINE identity: Workload Identity Federation from this host's AWS instance
  # role. No key on disk — the cred-config holds only the pool/provider audience, the IMDS URLs and
  # the impersonation target, and the subject token is minted from IMDSv2 at call time. It therefore
  # works OUTSIDE a job, which is the whole point (the credential that broke on 2026-07-18 was a
  # GitHub-OIDC WIF cred whose issuer only exists INSIDE a job).
  #
  # Provisioned 2026-07-18: pool aws-glue-runners / provider ec2-instance-role, locked by attribute
  # condition to arn:aws:sts::427895769566:assumed-role/uts-orchestrator-epic-role; the SA holds
  # roles/secretmanager.secretAccessor on the GH_PAT secret ONLY (not project-wide).
  #
  # Without this block a re-provisioned host came up with an EMPTY private config and no identity —
  # the token path then fails loudly but the host is dead on arrival. Idempotent: regenerates the
  # cred-config only when absent, and re-activation is a no-op.
  : "${GLUE_WIF_FILE:=${RUNNER_BASE}/glue-runner-wif.json}"
  : "${GLUE_WIF_PROVIDER:=projects/1060025368044/locations/global/workloadIdentityPools/aws-glue-runners/providers/ec2-instance-role}"
  : "${GLUE_WIF_SA:=glue-runner-gh-pat@central-element-323112.iam.gserviceaccount.com}"
  # Pre-create the file (empty, runner-owned) before gcloud tries to write it — CREATING a new file
  # in the root-owned ${RUNNER_BASE} (0755 root:root, see step 3 above) is denied for ${RUNNER_USER};
  # rewriting an EXISTING file only needs write on the FILE, not the parent dir. Same fix already
  # applied to repo.refreshed-at above; this exact ordering bug was latent here too until the
  # agent-orchestrator canary install (2026-07-27) hit it on genuinely FRESH ${RUNNER_BASE} — PM's own
  # ${GLUE_WIF_FILE} predates this code path and was never re-verified against a clean install.
  if [ ! -s "${GLUE_WIF_FILE}" ]; then
    [ -e "${GLUE_WIF_FILE}" ] || install -o "${RUNNER_USER}" -g "${RUNNER_USER}" -m 0600 /dev/null "${GLUE_WIF_FILE}"
    sudo -u "${RUNNER_USER}" gcloud iam workload-identity-pools create-cred-config \
      "${GLUE_WIF_PROVIDER}" \
      --service-account="${GLUE_WIF_SA}" \
      --aws --enable-imdsv2 \
      --output-file="${GLUE_WIF_FILE}" ||
      echo "WARN: could not generate ${GLUE_WIF_FILE} — the token path will fail loudly until it exists" >&2
  fi
  if [ -s "${GLUE_WIF_FILE}" ]; then
    chown "${RUNNER_USER}:${RUNNER_USER}" "${GLUE_WIF_FILE}"
    chmod 0600 "${GLUE_WIF_FILE}"
    sudo -u "${RUNNER_USER}" env CLOUDSDK_CONFIG="${RUNNER_BASE}/.gcloud" \
      gcloud auth login --cred-file="${GLUE_WIF_FILE}" >/dev/null 2>&1 ||
      echo "WARN: gcloud auth login --cred-file failed for ${GLUE_WIF_FILE}" >&2
    # Verify by LENGTH only — never echo a secret into provisioning logs.
    if sudo -u "${RUNNER_USER}" env CLOUDSDK_CONFIG="${RUNNER_BASE}/.gcloud" \
      gcloud secrets versions access latest --secret="${GH_TOKEN_SECRET:-GH_PAT}" \
      --project="${GCP_PROJECT:-central-element-323112}" >/dev/null 2>&1; then
      echo "  machine identity OK: $(sudo -u "${RUNNER_USER}" env CLOUDSDK_CONFIG="${RUNNER_BASE}/.gcloud" gcloud config list --format='value(core.account)' 2>/dev/null)"
    else
      echo "WARN: private gcloud config cannot read ${GH_TOKEN_SECRET:-GH_PAT} — runners will fail loudly at registration" >&2
    fi
  fi

  # 4) helper scripts
  install -m 0755 -o "${RUNNER_USER}" -g "${RUNNER_USER}" "${HERE}/glue-runner-run.sh"   "${RUNNER_BASE}/glue-runner-run.sh"
  install -m 0755 -o "${RUNNER_USER}" -g "${RUNNER_USER}" "${HERE}/job-cleanup.sh"       "${RUNNER_BASE}/job-cleanup.sh"
  install -m 0755 -o "${RUNNER_USER}" -g "${RUNNER_USER}" "${HERE}/refresh-slot-repo.sh" "${RUNNER_BASE}/refresh-slot-repo.sh"
  # Consumed by python-quality-gates-v2.yml's qg-slices checkout step (repo-clone I/O
  # reduction, ci_pipeline_speed_and_cost_redesign_2026_08_05.md) — hardlink-copies the
  # slot's own mirror (this same RUNNER_BASE/repo, refreshed by refresh-slot-repo.sh above)
  # instead of a cold network clone. A caller whose runner doesn't have this file (not yet
  # rolled out here, or a pool provisioned before this line existed) safely falls back to a
  # plain clone, so this install is additive, never load-bearing for existing pools.
  install -m 0755 -o "${RUNNER_USER}" -g "${RUNNER_USER}" "${HERE}/fast-checkout.sh"     "${RUNNER_BASE}/fast-checkout.sh"

  # 5) env file (0600, root). On the SECRET path GH_TOKEN is deliberately ABSENT: the wrapper resolves
  # it per start via ADC, so this file holds a secret NAME and leaks nothing if it is copied, backed
  # up, or read out of a snapshot. Only the legacy path writes a real credential here.
  umask 077
  if [ -n "${GH_TOKEN_SECRET:-}" ]; then
    printf 'GH_TOKEN_SECRET=%s\n' "${GH_TOKEN_SECRET}" > "${ENV_FILE}"
    # ALWAYS write GCP_PROJECT (same central-element-323112 fallback as the install-time self-test
    # at line ~464 and the template default at line ~511) -- never conditional on the operator having
    # passed it explicitly. Found 2026-07-28: the install-time verification call already applies this
    # fallback and so always passes, but the runtime env file previously did NOT get GCP_PROJECT
    # unless explicitly set, silently falling back to the isolated per-pool .gcloud config's own
    # bootstrapped default project -- which `gcloud auth login --cred-file=...` does not reliably set.
    # Result: every pool installed via the documented `GH_TOKEN_SECRET=GH_PAT ./setup-glue-runners.sh
    # install` (no GCP_PROJECT) passed its own install-time check yet crash-looped at runtime with
    # "Failed to find attribute [project]" on every GH_PAT fetch -- a ~3.5h fleet-wide outage across
    # 23 repos before this was found and fixed live via SSM, then fixed here for future installs.
    printf 'GCP_PROJECT=%s\n' "${GCP_PROJECT:-central-element-323112}" >> "${ENV_FILE}"
  else
    printf 'GH_TOKEN=%s\n' "${GH_PAT}" > "${ENV_FILE}"
  fi
  printf 'OWNER=%s\nREPO=%s\nRUNNER_BASE=%s\n' "${OWNER}" "${REPO}" "${RUNNER_BASE}" >> "${ENV_FILE}"
  # GH_TOKEN_FILE/GLUE_GCLOUD_CONFIG: glue-runner-run.sh's OWN defaults point at PM's shared
  # /opt/github-glue-runners paths (see its `${VAR:=...}` fallbacks) — a second pool MUST override
  # both explicitly here or it would silently read PM's token cache / gcloud identity instead of its
  # own. github-glue-runner@.service has no other path to these two (only EnvironmentFile=${ENV_FILE}
  # reaches it), so this is the ONE place they are set for that unit.
  printf 'GH_TOKEN_FILE=/run/%s/gh_token\nGLUE_GCLOUD_CONFIG=%s/.gcloud\n' "${RUNTIME_DIR_NAME}" "${RUNNER_BASE}" >> "${ENV_FILE}"
  chmod 0600 "${ENV_FILE}"
  log "wrote ${ENV_FILE} (0600) — $([ -n "${GH_TOKEN_SECRET:-}" ] && echo 'secret NAME only, no credential on disk' || echo 'contains a literal PAT')"

  # 6) systemd slice + template unit + slot-refresh timer — RENDERED (sed-substituted), not a byte
  # copy: the checked-in templates hardcode PM's paths/names, and POOL_TAG needs those swapped for a
  # second pool's own RUNNER_BASE/ENV_FILE/SLICE_NAME/runtime-dir. With POOL_TAG empty every
  # substitution is a same-value no-op, so PM's installed units are BYTE-IDENTICAL to before this
  # existed — verified via `diff` against a pre-change install, see the plan's evidence entry.
  render_unit() {
    sed \
      -e "s#/opt/github-glue-runners#${RUNNER_BASE}#g" \
      -e "s#/etc/github-glue-runner\\.env#${ENV_FILE}#g" \
      -e "s#github-glue-runner\\.slice#${SLICE_NAME}#g" \
      -e "s#/run/github-glue-runner/#/run/${RUNTIME_DIR_NAME}/#g" \
      -e "s#RuntimeDirectory=github-glue-runner\$#RuntimeDirectory=${RUNTIME_DIR_NAME}#" \
      -e "s#Before=github-glue-runner@\\.service#Before=${TEMPLATE_UNIT}#" \
      -e "s#Unit=github-glue-slot-refresh\\.service#Unit=${SLOT_REFRESH_SERVICE}#" \
      -e "s#Environment=GH_TOKEN_SECRET=GH_PAT#Environment=GH_TOKEN_SECRET=${GH_TOKEN_SECRET:-GH_PAT}#" \
      -e "s#Environment=GCP_PROJECT=central-element-323112#Environment=GCP_PROJECT=${GCP_PROJECT:-central-element-323112}#" \
      -e "s#IggyIkenna/unified-trading-pm#${OWNER}/${REPO}#g" \
      "$1"
  }
  render_unit "${HERE}/github-glue-runner.slice"          > "${UNIT_DIR}/${SLICE_NAME}"
  render_unit "${HERE}/github-glue-runner@.service"       > "${UNIT_DIR}/${TEMPLATE_UNIT}"
  render_unit "${HERE}/github-glue-slot-refresh.service"  > "${UNIT_DIR}/${SLOT_REFRESH_SERVICE}"
  render_unit "${HERE}/github-glue-slot-refresh.timer"    > "${UNIT_DIR}/${SLOT_REFRESH_TIMER}"
  chmod 0644 "${UNIT_DIR}/${SLICE_NAME}" "${UNIT_DIR}/${TEMPLATE_UNIT}" "${UNIT_DIR}/${SLOT_REFRESH_SERVICE}" "${UNIT_DIR}/${SLOT_REFRESH_TIMER}"
  # Token cache refresher — keeps Secret Manager OFF the runner hot path (see refresh-gh-token.sh).
  install -m 0755 "${HERE}/refresh-gh-token.sh"               "${RUNNER_BASE}/refresh-gh-token.sh"
  render_unit "${HERE}/github-glue-token-refresh.service" > "${UNIT_DIR}/${TOKEN_REFRESH_SERVICE}"
  render_unit "${HERE}/github-glue-token-refresh.timer"   > "${UNIT_DIR}/${TOKEN_REFRESH_TIMER}"
  chmod 0644 "${UNIT_DIR}/${TOKEN_REFRESH_SERVICE}" "${UNIT_DIR}/${TOKEN_REFRESH_TIMER}"
  unset -f render_unit
  systemctl daemon-reload

  # 7) enable + start both pools, then the refresh timer
  for inst in $(all_instances); do
    systemctl enable --now "${RUNNER_UNIT_PREFIX}@${inst}.service"
  done
  systemctl enable --now "${SLOT_REFRESH_TIMER}"
  systemctl enable --now "${TOKEN_REFRESH_TIMER}"
  # Seed the cache synchronously: /run is tmpfs, so it is empty right now, and every runner started
  # below would otherwise cold-start against Secret Manager — the exact hot-path call we removed.
  systemctl start "${TOKEN_REFRESH_SERVICE}" || {
    echo "WARN: token refresh failed at install; runners will fall back to a direct Secret Manager read" >&2
  }
  log "started ${GLUE_COUNT} ephemeral (glue-*) + ${WRITER_COUNT} long-lived (writer-*) — verify with: $0 status"
}

cmd_status() {
  log "systemd units:"
  systemctl --no-pager --type=service list-units "${RUNNER_UNIT_PREFIX}@*" || true
  echo
  log "slot-refresh timer:"
  systemctl --no-pager list-timers "${SLOT_REFRESH_PREFIX}*" "${TOKEN_REFRESH_PREFIX}*" || true
  local stamp="${RUNNER_BASE}/repo.refreshed-at" stamp_val=""
  [ -f "${stamp}" ] && stamp_val="$(tr -dc '0-9' < "${stamp}")"
  # Guard the arithmetic: an empty/garbage stamp would make $(( now - "" )) a fatal syntax error
  # under `set -e` and take the whole status report down over a cosmetic field.
  if [ -n "${stamp_val}" ]; then
    local age=$(( $(date -u +%s) - stamp_val ))
    printf '  slot clone last refreshed %ss ago' "${age}"
    [ "${age}" -gt 1800 ] && printf ' \033[31m(STALE — refresher broken?)\033[0m'
    printf '\n'
  elif [ -f "${stamp}" ]; then
    warn "${stamp} is empty/corrupt — treat the slot clone as UNVERIFIED"
  else
    warn "no ${stamp} — the slot clone has never been refreshed"
  fi
  echo
  log "slice resource state:"
  systemctl --no-pager show "${SLICE_NAME}" -p CPUQuotaPerSecUSec -p MemoryMax -p MemoryCurrent 2>/dev/null || true
  echo
  local tok
  tok="$(resolve_admin_token)"
  if [ -n "${tok}" ]; then
    log "live runners registered to ${OWNER}/${REPO}:"
    curl -fsS -H "Authorization: Bearer ${tok}" -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/${OWNER}/${REPO}/actions/runners" \
      | python3 -c "
import sys, json
runners = json.load(sys.stdin).get('runners', [])
if not runners:
    print(' (none)')
for r in runners:
    labels = ','.join(l['name'] for l in r.get('labels', []))
    print(' %-28s %-8s busy=%-5s labels=%s' % (r['name'], r['status'], r['busy'], labels))
"
  else
    log "(no admin token resolvable — set GH_TOKEN_SECRET/GH_PAT, or run under sudo so ${ENV_FILE} is readable, to also list live runners)"
  fi
}

cmd_teardown() {
  [ "$(id -u)" -eq 0 ] || die "teardown must run as root (sudo)"
  local inst
  for inst in $(all_instances); do
    systemctl disable --now "${RUNNER_UNIT_PREFIX}@${inst}.service" 2>/dev/null || true
  done
  systemctl disable --now "${SLOT_REFRESH_TIMER}" 2>/dev/null || true
  systemctl disable --now "${TOKEN_REFRESH_TIMER}" 2>/dev/null || true
  rm -f "${UNIT_DIR}/${TEMPLATE_UNIT}" "${UNIT_DIR}/${SLICE_NAME}" \
        "${UNIT_DIR}/${SLOT_REFRESH_SERVICE}" "${UNIT_DIR}/${SLOT_REFRESH_TIMER}" \
        "${UNIT_DIR}/${TOKEN_REFRESH_SERVICE}" "${UNIT_DIR}/${TOKEN_REFRESH_TIMER}"
  systemctl daemon-reload
  cmd_prune || true
  log "systemd units removed. Runner dirs + slot + ${ENV_FILE} left in place; rm -rf ${RUNNER_BASE} ${ENV_FILE} to fully purge."
}

# Delete OFFLINE EPHEMERAL runner registrations left by a crashed wrapper (a healthy ephemeral runner
# deregisters itself on normal exit).
#
# EPHEMERAL ONLY — this MUST NOT touch writer-*. A JIT runner is only ever OFFLINE if it crashed, but
# a LONG-LIVED writer is legitimately offline across every reboot/redeploy; pruning on `offline` would
# deregister the writer pool out from under a rebooting VM. The name prefix is the guard: ephemeral
# runners are `glue-<host>-<idx>`, writers are `writer-<host>-<idx>`.
cmd_prune() {
  local tok
  tok="$(resolve_admin_token)"
  [ -n "${tok}" ] || die "prune needs an admin token — set GH_TOKEN_SECRET/GH_PAT, or run under sudo so ${ENV_FILE} is readable"
  curl -fsS -H "Authorization: Bearer ${tok}" -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${OWNER}/${REPO}/actions/runners?per_page=100" \
    | python3 -c "
import sys, json
# 'glue-' prefix is the guard that excludes the long-lived 'writer-<host>-<idx>' pool.
for r in json.load(sys.stdin).get('runners', []):
    if r['name'].startswith('glue-') and r['status'] == 'offline':
        print(r['id'])
" \
    | while read -r id; do
        [ -n "${id}" ] || continue
        curl -fsS -X DELETE -H "Authorization: Bearer ${tok}" -H "Accept: application/vnd.github+json" \
          "https://api.github.com/repos/${OWNER}/${REPO}/actions/runners/${id}" && log "pruned offline ephemeral runner ${id}"
      done
}

cmd_help() {
  cat <<EOF
usage: $0 {install|status|preflight|teardown|prune}

  install    download+verify the pinned runner, build the slot, register both pools, start systemd.
             Needs root AND exactly one admin-token source (see below).
  status     systemd units + slot freshness + slice resources + live runners from the API.
  preflight  check this host has the toolchain the MOVE set invokes. Run BEFORE install.
  teardown   stop + remove units, prune leftover ephemeral registrations. Keeps ${RUNNER_BASE}.
  prune      delete OFFLINE *ephemeral* (glue-*) registrations. Never touches writer-*.

admin token — exactly ONE of:
  GH_TOKEN_SECRET=<name>   PREFERRED. GCP Secret Manager secret name (this VM: GH_TOKEN_SECRET=GH_PAT).
                           Only the NAME is stored; the wrapper resolves the token per start via the
                           ADC of ${RUNNER_USER}, so no credential is written to disk. Pair with
                           GCP_PROJECT=<proj> if the secret is not in the VM's default project.
  GH_PAT=<token>           LEGACY. Writes the literal token into ${ENV_FILE} (0600 root). Only for a
                           host with no ADC.
Either way the token needs Administration:write on ${OWNER}/${REPO}; install probes it up front.

pools:  ${GLUE_COUNT}× glue-N (JIT-ephemeral, labels self-hosted,glue)
        ${WRITER_COUNT}× writer-N (long-lived, labels self-hosted,glue-writer — DISJOINT on purpose)

examples:
  ./setup-glue-runners.sh preflight
  sudo GH_TOKEN_SECRET=GH_PAT ./setup-glue-runners.sh install
  ./setup-glue-runners.sh status
EOF
}

case "${1:-status}" in
  install)   cmd_install ;;
  status)    cmd_status ;;
  preflight) cmd_preflight ;;
  teardown)  cmd_teardown ;;
  prune)     cmd_prune ;;
  -h | --help | help) cmd_help ;;
  *) cmd_help >&2; die "unknown subcommand '${1}'" ;;
esac
