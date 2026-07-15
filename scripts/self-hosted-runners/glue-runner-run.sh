#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1 self-hosted glue runners)
# Lifecycle: permanent
# Delete-when: glue moves to serverless (B2) or a managed runner (B3) and this host is retired
#
# glue-runner-run.sh — the per-runner ExecStart wrapper (one instance per systemd template unit).
#
# Runs ONE ephemeral GitHub Actions job then exits; systemd (Restart=always) restarts us for the
# next. Ephemeral + just-in-time (JIT) config means: no long-lived .credentials on disk, a fresh
# runner identity per job, and auto-deregistration after each job — the clean, low-footprint pattern
# for a trusted PRIVATE repo. All glue workflows live in unified-trading-pm, so we register to that
# ONE repo (a personal account has no org-level runners — repo-scoped is correct here).
#
# Invoked as: glue-runner-run.sh <instance-id>   (the systemd %i)
set -euo pipefail

INSTANCE="${1:?usage: glue-runner-run.sh <instance-id>}"
: "${OWNER:=IggyIkenna}"
: "${REPO:=unified-trading-pm}"
: "${RUNNER_BASE:=/opt/github-glue-runners}"
: "${RUNNER_LABELS:=self-hosted,glue}"

# Token with Administration:write on the repo (needed to generate a JIT config). Prefer the env
# (systemd EnvironmentFile); optionally fetch from GCP Secret Manager at runtime so no PAT sits on
# disk. Set GH_TOKEN_SECRET (+ have gcloud ADC on the VM) to use the Secret-Manager path.
if [ -z "${GH_TOKEN:-}" ] && [ -n "${GH_TOKEN_SECRET:-}" ]; then
  GH_TOKEN="$(gcloud secrets versions access latest --secret="${GH_TOKEN_SECRET}" \
    ${GCP_PROJECT:+--project="${GCP_PROJECT}"} 2>/dev/null || true)"
fi
: "${GH_TOKEN:?GH_TOKEN (Administration:write on ${OWNER}/${REPO}) must be set via EnvironmentFile or GH_TOKEN_SECRET}"

RUNNER_DIR="${RUNNER_BASE}/glue-${INSTANCE}"
HOST="$(hostname -s)"
RUNNER_NAME="glue-${HOST}-${INSTANCE}"
cd "${RUNNER_DIR}"

# Keep disk bounded — wipe the previous ephemeral job's checkout + diag before re-registering.
rm -rf _work/* _diag/*.log 2>/dev/null || true

# labels JSON array from the comma list
LABELS_JSON="$(printf '%s' "${RUNNER_LABELS}" | python3 -c 'import sys,json;print(json.dumps(sys.stdin.read().strip().split(",")))')"

# Single-use JIT config (the runner auto-removes its registration after one job).
JIT="$(curl -fsS -X POST \
  -H "Authorization: Bearer ${GH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${OWNER}/${REPO}/actions/runners/generate-jitconfig" \
  -d "{\"name\":\"${RUNNER_NAME}\",\"runner_group_id\":1,\"labels\":${LABELS_JSON},\"work_folder\":\"_work\"}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["encoded_jit_config"])')"

# Run exactly one job, then exit 0 → systemd restarts us and we re-register.
exec ./run.sh --jitconfig "${JIT}"
