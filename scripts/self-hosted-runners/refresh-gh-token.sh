#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction / self-hosted glue runners)
# Lifecycle: permanent
# Delete-when: the glue runners stop needing a repo-admin token (i.e. never, while self-hosted).
#
# refresh-gh-token.sh — cache the runner-registration PAT in tmpfs, refreshed on a timer, so the
#                       runner wrapper NEVER calls Secret Manager on the hot path.
#
# ┌─ WHY (operator 2026-07-17, after the 14,561-error crash-loop) ────────────────────────────────────┐
# │ The wrapper used to fetch GH_PAT from Secret Manager on EVERY exec. The glue pool is JIT-ephemeral │
# │ — a runner re-execs after every single job, and systemd re-execs it again on any failure — so one  │
# │ gcloud call per job became a gcloud call every ~6s per unit under a crash-loop. MEASURED 2026-07-17:│
# │ 14,561 failed token fetches in 24h across 5 units.                                                 │
# │                                                                                                     │
# │ Worse, it was a SELF-AMPLIFYING loop: fetch fails -> wrapper dies -> systemd restarts in 5s ->      │
# │ fetch again. The dependency was on the hot path of the thing that retries fastest.                  │
# │                                                                                                     │
# │ Now: this unit fetches ONCE every 5 minutes into tmpfs; the wrapper does a local read. Secret       │
# │ Manager calls drop from O(jobs + crashes) to a flat 288/day, and a transient GSM/network blip can   │
# │ no longer take the pool down — see KEEP-THE-OLD-TOKEN below, which is the whole point.              │
# └─────────────────────────────────────────────────────────────────────────────────────────────────────┘
#
# ┌─ WHY tmpfs (/run) AND NOT /etc ─────────────────────────────────────────────────────────────────────┐
# │ The operator asked for the token "locally on disk". This puts it in /run, which is tmpfs: it is a   │
# │ local file for every practical purpose (open/read, no network) but lives in RAM only — so the PAT   │
# │ never lands on the EBS volume, never enters a snapshot/AMI, and is gone on reboot. That keeps most  │
# │ of the original "no PAT at rest" property while giving up none of the efficiency. Mode 0600, owned  │
# │ by the runner user, inside a 0700 RuntimeDirectory.                                                  │
# └─────────────────────────────────────────────────────────────────────────────────────────────────────┘
set -uo pipefail

: "${GH_TOKEN_SECRET:=GH_PAT}"
: "${GCP_PROJECT:=central-element-323112}"
: "${GH_TOKEN_FILE:=/run/github-glue-runner/gh_token}"
# Launcher-PRIVATE gcloud config (2026-07-18). The comment below already argues that the token path
# must not depend on "a per-user gcloud config that nothing tests and any `gcloud config set` can
# silently change" — that reasoning was applied to the PROJECT but not to the CREDENTIAL, which is
# the half that actually broke. Self-hosted runners do not reset HOME between jobs, so a job step
# running google-github-actions/auth writes into the shared ~/.config/gcloud and makes its WIF
# external_account credential ACTIVE for every later process. That credential mints its subject
# token from actions-run-service, which exists only INSIDE a job, so afterwards every fetch here
# fails with 404 "job request not found" — 1377 restarts and a 2.5h fleet-wide CI outage.
: "${GLUE_GCLOUD_CONFIG:=/opt/github-glue-runners/.gcloud}"

TOKEN_DIR="$(dirname "${GH_TOKEN_FILE}")"
mkdir -p "${TOKEN_DIR}" && chmod 700 "${TOKEN_DIR}"

# NOTE: no `2>/dev/null || true` here, deliberately. The bug this whole file exists to fix was
# `gcloud ... 2>/dev/null || true` in the wrapper: it swallowed the real error and handed back an
# empty string, so a permission/quota/network fault was rendered as "token unset". Capture stderr and
# REPORT it. (Third instance of this exact swallow-the-error bug in this epic — see the plan.)
err_file="$(mktemp)"; trap 'rm -f "${err_file}"' EXIT
# --project is passed EXPLICITLY: relying on gcloud's default project means the token path depends on
# a per-user gcloud config that nothing tests and any `gcloud config set` can silently change.
# CLOUDSDK_CONFIG is a COMMAND PREFIX, never exported and never put in the systemd EnvironmentFile:
# that env reaches `exec ./run.sh` and therefore every job step (measured on a live Runner.Listener
# 2026-07-18), so exporting it would invite jobs to write their credentials into this private config
# — the opposite of the isolation intended here.
token="$(CLOUDSDK_CONFIG="${GLUE_GCLOUD_CONFIG}" gcloud secrets versions access latest \
  --secret="${GH_TOKEN_SECRET}" --project="${GCP_PROJECT}" 2>"${err_file}")"
rc=$?

# ── KEEP-THE-OLD-TOKEN: a failed refresh must NEVER destroy a working one ───────────────────────────
# This is the resilience property, and the reason the incident of 2026-07-17 cannot recur in this
# shape: an existing cached token stays valid (GH_PAT is fine-grained and never expires), so a GSM
# blip degrades to "slightly stale token" instead of "entire pool cannot register". Fail LOUD (non-zero
# + journal) so the timer's failure is visible, but leave the good file alone.
if [ ${rc} -ne 0 ] || [ -z "${token}" ]; then
  echo "ERROR: could not read ${GH_TOKEN_SECRET} from Secret Manager (project=${GCP_PROJECT}, rc=${rc})" >&2
  sed 's/^/  gcloud: /' "${err_file}" >&2
  if [ -s "${GH_TOKEN_FILE}" ]; then
    age=$(( $(date +%s) - $(stat -c %Y "${GH_TOKEN_FILE}") ))
    echo "KEEPING the existing cached token (age ${age}s) — runners stay up. NOT overwriting it." >&2
  else
    echo "No cached token exists yet — runners CANNOT register until this succeeds." >&2
  fi
  exit 1
fi

# Shape check before publishing: a PAT that isn't a PAT (an HTML error page, a truncated read) would
# otherwise be written and then fail 401 on every runner, which looks like a GitHub outage, not a
# fetch bug. Cheap to check here; expensive to diagnose there.
case "${token}" in
  ghp_* | github_pat_* | gho_* | ghs_*) ;;
  *) echo "ERROR: value from ${GH_TOKEN_SECRET} is not a GitHub token (len=${#token}) — refusing to publish." >&2
     exit 1 ;;
esac

# Atomic publish: write-then-rename, so a reader never sees a half-written token. A plain `>` would
# truncate the file first, giving every runner starting in that window an empty token.
tmp="$(mktemp "${TOKEN_DIR}/.gh_token.XXXXXX")"
printf '%s' "${token}" > "${tmp}"
chmod 600 "${tmp}"
mv -f "${tmp}" "${GH_TOKEN_FILE}"

echo "refreshed ${GH_TOKEN_FILE} from ${GH_TOKEN_SECRET} (${#token} chars)"
