#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction / digest ratchet)
# Lifecycle: permanent
# Delete-when: digest-drift-sweep.yml is fixed AND has run correctly for a few cycles — at that point
#              the workflow's own log is the answer and this stops earning its keep.
#
# simulate-digest-drift-sweep.sh — answer "what would digest-drift-sweep DO if we fixed it?"
#                                  WITHOUT dispatching anything. Read-only.
#
# ┌─ WHY THIS EXISTS ──────────────────────────────────────────────────────────────────────────────┐
# │ digest-drift-sweep.yml has never worked: it passes secrets.GITHUB_TOKEN, which is scoped to PM  │
# │ only, so every cross-repo Dockerfile read 404s and is misreported as "Dockerfile not found".    │
# │ SSOT: plans/active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md       │
# │                                                                                                  │
# │ Fixing it is NOT a one-liner — the first correct run dispatches to every stale repo at once      │
# │ (measured 2026-07-17: 15 of 16), each producing a commit + a CI run. The operator asked to see   │
# │ the blast radius BEFORE the fix. That is this script. Re-run it whenever the decision comes back │
# │ up: the answer CHANGES over time (UTL :latest moves on every release, and repos drift), so a     │
# │ number measured last week is not the number you will get today.                                  │
# └────────────────────────────────────────────────────────────────────────────────────────────────┘
#
# It mirrors digest-drift-sweep.yml's `Sweep stale repos` step (:123-184) EXACTLY — same IMAGE_REPOS
# list and order, same live-defi-rollout→main fallback, same `^ARG BASE_IMAGE_DIGEST=sha256:<64hex>`
# extraction, same staleness rule (PINNED != CURRENT and FORCE_ALL != true). ONE difference, and it is
# the point: it NEVER POSTs /dispatches. If you edit the workflow's logic, edit this to match or it
# stops being a simulation and becomes a guess.
#
# NOTE ON THE TOKEN: this uses a cross-repo-scoped PAT (via load-gh-token.sh) — i.e. it runs the
# sweep as the FIXED workflow would. That asymmetry IS the bug being simulated.
#
#   source scripts/workspace/load-gh-token.sh
#   bash scripts/propagation/simulate-digest-drift-sweep.sh
#   CURRENT_DIGEST=sha256:... bash scripts/propagation/simulate-digest-drift-sweep.sh   # skip gcloud
set -uo pipefail

OWNER="${OWNER:-IggyIkenna}"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
[ -n "$TOKEN" ] || { echo "no token — run: source scripts/workspace/load-gh-token.sh" >&2; exit 1; }

# Keep in sync with digest-drift-sweep.yml:87-104.
IMAGE_REPOS=(
  agent-orchestrator alerting-service batch-live-reconciliation-service client-reporting-api
  deployment-api deployment-service execution-service features-service
  fund-administration-service greeks-service instruments-service market-data-processing-service
  market-tick-data-service ml-service strategy-service trading-agent-service
)

CURRENT_DIGEST="${CURRENT_DIGEST:-}"
if [ -z "$CURRENT_DIGEST" ]; then
  PROJECT_ID="${GCP_PROJECT_ID:-central-element-323112}"
  IMAGE="asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest"
  CURRENT_DIGEST=$(gcloud artifacts docker images describe "$IMAGE" --format='value(image_summary.digest)' 2>/dev/null || echo "")
fi
if ! echo "$CURRENT_DIGEST" | grep -qE '^sha256:[0-9a-f]{64}$'; then
  echo "FATAL: could not resolve UTL :latest digest (got: '${CURRENT_DIGEST}')" >&2
  echo "       need gcloud ADC, or pass CURRENT_DIGEST=sha256:... explicitly." >&2
  exit 1
fi
echo "Current UTL :latest = ${CURRENT_DIGEST}"
echo

TMP="$(mktemp)"; trap 'rm -f "${TMP}"' EXIT
DISPATCHED=0; FRESH=0; NOARG=0
printf '%-34s %-14s %s\n' REPO VERDICT DETAIL
for REPO in "${IMAGE_REPOS[@]}"; do
  CONTENT=""; SRC=""
  for BRANCH in live-defi-rollout main; do
    code=$(curl -s -o "${TMP}" -w '%{http_code}' \
      -H "Authorization: Bearer ${TOKEN}" -H "Accept: application/vnd.github.raw+json" \
      "https://api.github.com/repos/${OWNER}/${REPO}/contents/Dockerfile?ref=${BRANCH}")
    if [ "${code}" = "200" ]; then CONTENT=$(cat "${TMP}"); SRC="${BRANCH}"; break; fi
  done

  if [ -z "${CONTENT}" ]; then
    printf '%-34s %-14s %s\n' "${REPO}" "NO-DOCKERFILE" "(genuinely absent on LDR+main)"
    NOARG=$((NOARG + 1)); continue
  fi
  PINNED=$(echo "${CONTENT}" | grep -oE '^ARG BASE_IMAGE_DIGEST=sha256:[0-9a-f]{64}' | grep -oE 'sha256:[0-9a-f]{64}' || echo "")
  if [ -z "${PINNED}" ]; then
    printf '%-34s %-14s %s\n' "${REPO}" "NO-ARG" "(Dockerfile on ${SRC}, no digest pin)"
    NOARG=$((NOARG + 1)); continue
  fi
  if [ "${PINNED}" = "${CURRENT_DIGEST}" ]; then
    printf '%-34s %-14s %s\n' "${REPO}" "fresh" "${PINNED:0:19}… (${SRC})"
    FRESH=$((FRESH + 1)); continue
  fi
  printf '%-34s %-14s %s\n' "${REPO}" "WOULD-DISPATCH" "${PINNED:0:19}… -> ${CURRENT_DIGEST:0:19}… (${SRC})"
  DISPATCHED=$((DISPATCHED + 1))
done

echo
echo "=== IF THE TOKEN WERE FIXED, THE FIRST RUN WOULD ==="
echo "  Dispatch dependency-update to : ${DISPATCHED} repo(s)  <- each = 1 commit to that repo's LDR + 1 CI run"
echo "  Leave alone (already fresh)   : ${FRESH}"
echo "  Skip (no Dockerfile / no ARG) : ${NOARG}"
echo
echo "  Today, with the PM-scoped GITHUB_TOKEN, the real workflow reports: Dispatched 0 / fresh 0 / no-ARG 16."
echo "  A non-zero 'Dispatch' count here with 0 in the real run IS the bug."
