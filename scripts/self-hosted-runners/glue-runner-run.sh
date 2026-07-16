#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1 self-hosted glue runners)
# Lifecycle: permanent
# Delete-when: glue moves to serverless (B2) or a managed runner (B3) and this host is retired
#
# glue-runner-run.sh — the per-runner ExecStart wrapper (one instance per systemd template unit).
#
# TWO POOLS, two lifecycles. The systemd instance name IS the pool + index ("glue-3", "writer-1"):
#
#   glue-N    JIT-EPHEMERAL. Runs ONE job then exits; systemd restarts us to re-register. No
#             long-lived .credentials on disk, fresh identity per job, auto-deregistration.
#             Labels: self-hosted,glue          <- the ~37 low-frequency movers land here.
#
#   writer-N  LONG-LIVED (non-ephemeral). Registers ONCE via config.sh + a registration token, then
#             run.sh loops and serves many jobs in ONE process. For the high-frequency writer
#             (ci-status-update, ~13k/mo at ~2-5s a job) where JIT re-registration overhead
#             (generate-jitconfig + config + connect ≈ seconds) would DOMINATE the job itself.
#             Labels: self-hosted,glue-writer   <- NOTE: deliberately does NOT carry `glue`.
#
# WHY THE LABELS MUST BE DISJOINT (subtle, load-bearing): runner label matching is a SUBSET test. A
# writer labelled `self-hosted,glue,writer` would still satisfy `runs-on: [self-hosted, glue]`, so the
# low-frequency movers would get scheduled onto the long-lived pool and defeat the split. The writer
# pool therefore omits `glue` entirely, and ci-status-update.yml targets [self-hosted, glue-writer].
#
# WHY NOT "long-lived JIT": a JIT config is single-use BY CONSTRUCTION — the runner auto-deregisters
# after one job. There is no flag to make it persist. Hence the genuine fork below.
#
# Invoked as: glue-runner-run.sh <pool>-<index>   (the systemd %i)
set -euo pipefail

INSTANCE="${1:?usage: glue-runner-run.sh <pool>-<index>  (e.g. glue-3 | writer-1)}"
POOL="${INSTANCE%-*}"
IDX="${INSTANCE##*-}"
case "${POOL}" in
  glue | writer) ;;
  *) echo "unknown pool '${POOL}' (expected glue|writer) from instance '${INSTANCE}'" >&2; exit 2 ;;
esac

: "${OWNER:=IggyIkenna}"
: "${REPO:=unified-trading-pm}"
: "${RUNNER_BASE:=/opt/github-glue-runners}"

# Token with Administration:write on the repo (JIT config / registration token). Prefer the env
# (systemd EnvironmentFile); optionally fetch from GCP Secret Manager at runtime so no PAT sits on
# disk. Set GH_TOKEN_SECRET (+ have gcloud ADC on the VM) to use the Secret-Manager path.
if [ -z "${GH_TOKEN:-}" ] && [ -n "${GH_TOKEN_SECRET:-}" ]; then
  GH_TOKEN="$(gcloud secrets versions access latest --secret="${GH_TOKEN_SECRET}" \
    ${GCP_PROJECT:+--project="${GCP_PROJECT}"} 2>/dev/null || true)"
fi
: "${GH_TOKEN:?GH_TOKEN (Administration:write on ${OWNER}/${REPO}) must be set via EnvironmentFile or GH_TOKEN_SECRET}"

RUNNER_DIR="${RUNNER_BASE}/${INSTANCE}"
HOST="$(hostname -s)"
RUNNER_NAME="${POOL}-${HOST}-${IDX}"
API="https://api.github.com/repos/${OWNER}/${REPO}"
cd "${RUNNER_DIR}"

# The post-job cleanup hook needs to know which runner dir to wipe; the runner propagates its env to
# hooks, so export it here rather than re-deriving it from RUNNER_WORKSPACE (fragile).
export GLUE_RUNNER_DIR="${RUNNER_DIR}"

# Shared tool cache across ALL runner dirs (both pools). actions/setup-python resolves against this;
# on a hosted image it is pre-seeded, on self-hosted a MISS means it downloads+builds a Python for
# that job. Sharing one dir means only the FIRST job pays; every later job across every runner hits
# cache. (5 movers use actions/setup-python@v6.)
export RUNNER_TOOL_CACHE="${RUNNER_BASE}/toolcache"

# JSON via python3, not jq — python3 is guaranteed on the box, jq is not (verify-at-deploy item).
json_get() { python3 -c "import sys, json; print(json.load(sys.stdin)['$1'])"; }

if [ "${POOL}" = "glue" ]; then
  # ---- JIT-EPHEMERAL ------------------------------------------------------------------------
  # One job per process. Safe to wipe here precisely BECAUSE this runs once per job.
  rm -rf _work/* _diag/*.log 2>/dev/null || true

  LABELS_JSON='["self-hosted","glue"]'
  JIT="$(curl -fsS -X POST \
    -H "Authorization: Bearer ${GH_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "${API}/actions/runners/generate-jitconfig" \
    -d "{\"name\":\"${RUNNER_NAME}\",\"runner_group_id\":1,\"labels\":${LABELS_JSON},\"work_folder\":\"_work\"}" \
    | json_get encoded_jit_config)"

  # Run exactly one job, then exit 0 → systemd restarts us and we re-register.
  exec ./run.sh --jitconfig "${JIT}"
fi

# ---- LONG-LIVED (writer) --------------------------------------------------------------------
# Register ONCE. `.runner` is the marker config.sh writes; if it exists we are already registered and
# must NOT re-run config.sh (it would fail/prompt). On restart we just reconnect.
#
# NOTE: unlike the JIT pool this DOES persist .credentials on disk — the accepted trade for killing
# per-job re-registration overhead on a ~3s job. Feeds the security-codex todo.
if [ ! -f .runner ]; then
  REG_TOKEN="$(curl -fsS -X POST \
    -H "Authorization: Bearer ${GH_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "${API}/actions/runners/registration-token" | json_get token)"

  ./config.sh --unattended --replace \
    --url "https://github.com/${OWNER}/${REPO}" \
    --token "${REG_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --labels "self-hosted,glue-writer" \
    --work "_work"
fi

# Per-job cleanup is the runner's own post-job hook — NOT a wipe up here. This process serves many
# jobs, so anything above this line runs once per BOOT, not once per job.
export ACTIONS_RUNNER_HOOK_JOB_COMPLETED="${RUNNER_BASE}/job-cleanup.sh"

# Serve jobs until stopped (no --once): the whole point of this pool.
exec ./run.sh
