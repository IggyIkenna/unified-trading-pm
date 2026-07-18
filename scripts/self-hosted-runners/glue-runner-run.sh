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

# ── Token with Administration:write on the repo (JIT config / registration token) ───────────────────
# Resolution order: env (EnvironmentFile) -> tmpfs cache -> Secret Manager (cold-start only).
#
# WHY THE CACHE EXISTS (operator 2026-07-17, after a MEASURED 14,561-error crash-loop in 24h):
# this wrapper re-execs after EVERY job (the glue pool is JIT-ephemeral) and again on every systemd
# restart. Calling Secret Manager here put a network dependency on the hot path of the thing that
# retries every ~6s — a self-amplifying loop: fetch fails -> die -> restart -> fetch. The refresher
# timer (github-glue-token-refresh.timer) now does ONE fetch per 5 min into tmpfs and, crucially,
# KEEPS THE LAST GOOD TOKEN on failure, so a GSM blip degrades to a slightly stale (still valid —
# GH_PAT never expires) credential instead of taking the whole pool offline.
: "${GH_TOKEN_FILE:=/run/github-glue-runner/gh_token}"
if [ -z "${GH_TOKEN:-}" ] && [ -s "${GH_TOKEN_FILE}" ]; then
  GH_TOKEN="$(cat "${GH_TOKEN_FILE}")"
  # A stale cache is a WARNING, not an error: the token is still valid, but a cache older than a few
  # intervals means the refresher is dead and a rotation would not propagate. Say so; do not die.
  token_age=$(( $(date +%s) - $(stat -c %Y "${GH_TOKEN_FILE}") ))
  if [ "${token_age}" -gt 1800 ]; then
    echo "WARN: ${GH_TOKEN_FILE} is ${token_age}s old (>30min) — is github-glue-token-refresh.timer running?" >&2
  fi
fi

# Cold start only: the cache is tmpfs, so it is empty until the timer's OnBootSec fires. Deliberately
# NO `2>/dev/null || true` here — that swallow is precisely what turned a readable permission error
# into a bare "GH_TOKEN must be set", and cost ~16h of a silently bleeding pool on 2026-07-17.
if [ -z "${GH_TOKEN:-}" ] && [ -n "${GH_TOKEN_SECRET:-}" ]; then
  echo "token cache ${GH_TOKEN_FILE} absent/empty — falling back to a direct Secret Manager read" >&2
  # CLOUDSDK_CONFIG as a COMMAND PREFIX — same isolation as refresh-gh-token.sh, same reason: a job
  # step running google-github-actions/auth poisons the shared ~/.config/gcloud with a WIF credential
  # whose issuer only exists inside a job (2026-07-18, 2.5h outage). Never export it and never put it
  # in the EnvironmentFile — that env reaches `exec ./run.sh` and every job step below.
  GH_TOKEN="$(CLOUDSDK_CONFIG="${GLUE_GCLOUD_CONFIG:-/opt/github-glue-runners/.gcloud}" \
    gcloud secrets versions access latest --secret="${GH_TOKEN_SECRET}" \
    ${GCP_PROJECT:+--project="${GCP_PROJECT}"})" || {
    echo "FATAL: Secret Manager read of '${GH_TOKEN_SECRET}' failed (see the gcloud error above)." >&2
    echo "       project=${GCP_PROJECT:-<unset — gcloud default>} user=$(id -un)" >&2
    exit 1
  }
fi
: "${GH_TOKEN:?GH_TOKEN (Administration:write on ${OWNER}/${REPO}) must be set via EnvironmentFile, ${GH_TOKEN_FILE}, or GH_TOKEN_SECRET}"

RUNNER_DIR="${RUNNER_BASE}/${INSTANCE}"
HOST="$(hostname -s)"
RUNNER_NAME="${POOL}-${HOST}-${IDX}"
API="https://api.github.com/repos/${OWNER}/${REPO}"
cd "${RUNNER_DIR}"

# The post-job cleanup hook needs to know which runner dir to wipe; the runner propagates its env to
# hooks, so export it here rather than re-deriving it from RUNNER_WORKSPACE (fragile).
export GLUE_RUNNER_DIR="${RUNNER_DIR}"

# PER-RUNNER tool cache — NOT shared across runners. actions/setup-python resolves against this; on a
# hosted image it is pre-seeded, on self-hosted a MISS means it downloads a Python for that job.
#
# THIS WAS SHARED (${RUNNER_BASE}/toolcache) AND IT RACED — MEASURED 2026-07-16, batch-2 flip:
# three setup-python jobs landed within 7s of each other on different runners, all writing the same
# cache dir. actions/setup-python is DELETE-THEN-CREATE, not concurrency-safe:
#   15:03:02 ruleset-drift-alert     setup-python -> success
#   15:03:07 readiness-verifier      setup-python -> FAILURE
#   15:03:09 reconcile-release-tags  setup-python -> success
# readiness-verifier was mid-"Copy Python binaries" when reconcile-release-tags hit its own
# "Deleting Python 3.13.14 (x64)" and removed the directory under it:
#   cp: cannot create symbolic link '.../toolcache/Python/3.13.14/x64/lib/libpython3.13.so':
#       No such file or directory
# The shared cache saved ~10s per job and bought an intermittent, load-dependent CI failure — a
# flaky-test generator across the 5 movers that use setup-python. Not a trade worth making.
#
# Per-runner it is: each runner pays the download ONCE (~10s, first job only) and hits cache after.
# NOTE the placement — a SIBLING of _work, never inside it: the JIT wrapper wipes _work every cycle,
# so a cache under _work would be destroyed after every single job and re-downloaded every time.
export RUNNER_TOOL_CACHE="${RUNNER_DIR}/toolcache"

# JSON via python3, not jq — python3 is guaranteed on the box, jq is not (verify-at-deploy item).
json_get() { python3 -c "import sys, json; print(json.load(sys.stdin)['$1'])"; }

if [ "${POOL}" = "glue" ]; then
  # ---- JIT-EPHEMERAL ------------------------------------------------------------------------
  # One job per process. Safe to wipe here precisely BECAUSE this runs once per job.
  rm -rf _work/* _diag/*.log 2>/dev/null || true

  # SELF-HEAL a stale registration holding OUR name, or we cannot start at all.
  #
  # A JIT runner auto-deregisters on a CLEAN exit (job done → process exits). But SIGTERM — i.e.
  # `systemctl restart/stop`, a redeploy, or a reboot — kills it mid-"Listening for Jobs", and the
  # registration survives as OFFLINE, still holding this runner's deterministic name. The next start
  # then asks for a JIT config for a name that exists and gets:
  #     HTTP 409  {"message":"Already exists - A runner with the name ... already exists."}
  # `curl -fsS` treats 409 as failure and prints NOTHING, so json_get received "" and died with
  #     json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
  # — a crash loop whose traceback names JSON and never mentions the actual cause. MEASURED
  # 2026-07-16: one `systemctl restart` of the pool took all 5 glue runners down permanently; the
  # writers were unaffected (they register once via config.sh and never re-register).
  #
  # Only OFFLINE registrations are deleted. An ONLINE one with our name means another process is
  # genuinely serving as this runner — deleting that would yank a live runner out from under a
  # running job, so we fail loudly instead. (Same guard as setup-glue-runners.sh `prune`.)
  STALE="$(curl -fsS -H "Authorization: Bearer ${GH_TOKEN}" -H "Accept: application/vnd.github+json" \
    "${API}/actions/runners?per_page=100" 2>/dev/null \
    | python3 -c "
import sys, json
try:
    runners = json.load(sys.stdin).get('runners', [])
except Exception:
    sys.exit(0)
for r in runners:
    if r['name'] == '${RUNNER_NAME}':
        print('%s %s' % (r['id'], r['status']))
        break
" || true)"
  if [ -n "${STALE}" ]; then
    STALE_ID="${STALE%% *}"; STALE_STATUS="${STALE##* }"
    # An ONLINE registration under OUR name, at the moment WE are starting, is our own predecessor's
    # GHOST: GitHub takes ~30-60s to mark a SIGTERM'd runner offline, and systemd has already fully
    # stopped that process before starting us. So WAIT for it rather than either (a) deleting a
    # possibly-live registration or (b) hard-failing.
    #
    # MEASURED 2026-07-16: the first version exit-3'd here with "Another process is serving as this
    # runner" — which is FALSE and would mislead whoever reads the journal. It did self-recover via
    # Restart=always once GitHub caught up, but only after ~30-40s of the pool crash-looping every
    # 5s. Waiting turns that into one clean start, and keeps the real protection: we never delete a
    # registration that is still genuinely serving.
    if [ "${STALE_STATUS}" != "offline" ]; then
      echo "[glue-runner] ${RUNNER_NAME} still registered as ${STALE_STATUS} (id=${STALE_ID}) — our SIGTERM'd predecessor's ghost; waiting for GitHub to mark it offline"
      for _ in $(seq 1 30); do   # ~90s: comfortably past GitHub's ~30-60s offline detection
        sleep 3
        STALE_STATUS="$(curl -fsS -H "Authorization: Bearer ${GH_TOKEN}" -H "Accept: application/vnd.github+json" \
          "${API}/actions/runners/${STALE_ID}" 2>/dev/null \
          | python3 -c "import sys,json;
try: print(json.load(sys.stdin)['status'])
except Exception: print('gone')" 2>/dev/null || echo gone)"
        [ "${STALE_STATUS}" = "offline" ] || [ "${STALE_STATUS}" = "gone" ] && break
      done
    fi
    if [ "${STALE_STATUS}" = "gone" ]; then
      echo "[glue-runner] registration ${STALE_ID} disappeared on its own (clean deregister) — nothing to do"
    elif [ "${STALE_STATUS}" = "offline" ]; then
      echo "[glue-runner] deleting stale OFFLINE registration ${RUNNER_NAME} (id=${STALE_ID}) — left by a SIGTERM'd predecessor"
      curl -fsS -X DELETE -H "Authorization: Bearer ${GH_TOKEN}" -H "Accept: application/vnd.github+json" \
        "${API}/actions/runners/${STALE_ID}" || true
    else
      # Still not offline after ~90s: this is NOT the normal ghost. Something else genuinely holds
      # our name. Fail loudly rather than yank it — systemd will retry.
      echo "[glue-runner] FATAL: ${RUNNER_NAME} is STILL ${STALE_STATUS} (id=${STALE_ID}) after ~90s." >&2
      echo "[glue-runner] That is not a restart ghost — something else is serving as this runner. Refusing to delete it." >&2
      exit 3
    fi
  fi

  LABELS_JSON='["self-hosted","glue"]'
  # Capture the body AND the status: a bare `curl -f | json_get` turns every API error into an
  # opaque JSONDecodeError. We want the API's own message in the journal.
  JIT_BODY="$(curl -sS -X POST \
    -H "Authorization: Bearer ${GH_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "${API}/actions/runners/generate-jitconfig" \
    -d "{\"name\":\"${RUNNER_NAME}\",\"runner_group_id\":1,\"labels\":${LABELS_JSON},\"work_folder\":\"_work\"}" \
    -w '\n%{http_code}' 2>/dev/null)"
  JIT_CODE="${JIT_BODY##*$'\n'}"
  JIT_JSON="${JIT_BODY%$'\n'*}"
  if [ "${JIT_CODE}" != "201" ]; then
    echo "[glue-runner] FATAL: generate-jitconfig for ${RUNNER_NAME} returned HTTP ${JIT_CODE}, want 201" >&2
    echo "[glue-runner] API said: ${JIT_JSON}" >&2
    exit 4
  fi
  JIT="$(printf '%s' "${JIT_JSON}" | json_get encoded_jit_config)"

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
