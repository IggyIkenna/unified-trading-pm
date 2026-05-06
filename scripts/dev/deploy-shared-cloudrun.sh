#!/usr/bin/env bash
# deploy-shared-cloudrun.sh — Tier-3 shared Cloud Run deployment.
#
# Builds deployment-api (FastAPI + bundled deployment-ui SPA) via Cloud Build
# in asia-northeast1 and rolls a new revision of the shared Cloud Run service
# `uts-shared-deployment-api`. Co-located with the project's GCS buckets so
# data-status reads avoid cross-region latency.
#
# Tradeoffs vs `dev-tiers.sh --tier 2 --real`:
#   * Build+deploy ~5-10 min vs hot-reload, but data-status under 5s in-region
#     (vs minutes from a laptop hitting cross-region GCS).
#   * Shared instance — every dev pushing to `live-defi-rollout` lands on the
#     same URL. No per-user state.
#
# Usage:
#   bash unified-trading-pm/scripts/dev/deploy-shared-cloudrun.sh
#   bash unified-trading-pm/scripts/dev/deploy-shared-cloudrun.sh --build-only
#   bash unified-trading-pm/scripts/dev/deploy-shared-cloudrun.sh --no-build
#
# Env overrides:
#   GCP_PROJECT_ID  (default: central-element-323112)
#   REGION          (default: asia-northeast1)
#   SERVICE_NAME    (default: uts-shared-deployment-api)
#   BRANCH          (default: live-defi-rollout)

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-central-element-323112}"
REGION="${REGION:-asia-northeast1}"
SERVICE_NAME="${SERVICE_NAME:-uts-shared-deployment-api}"
IMAGE="asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-system/deployment-api:latest"
BRANCH="${BRANCH:-live-defi-rollout}"
SA="unified-trading-sa@${PROJECT_ID}.iam.gserviceaccount.com"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-$(cd "${SCRIPT_DIR}/../../.." && pwd)}"
DEPLOYMENT_API_DIR="${WORKSPACE_ROOT}/deployment-api"

DO_BUILD=true
DO_DEPLOY=true
case "${1:-}" in
  --build-only)  DO_DEPLOY=false ;;
  --deploy-only|--no-build) DO_BUILD=false ;;
  --rebuild|"")  ;;
  -h|--help)
    sed -n '1,/^set -euo/p' "$0" | sed 's/^# *//; /^!/d; /^$/d; q' >&2
    grep -E '^# (Usage|  bash|Env|  GCP_|  REGION|  SERVICE|  BRANCH)' "$0" | sed 's/^# *//' >&2
    exit 0
    ;;
  *) echo "Unknown arg: $1"; exit 1 ;;
esac

if [ ! -d "$DEPLOYMENT_API_DIR" ]; then
  echo "ERROR: deployment-api dir not found at $DEPLOYMENT_API_DIR" >&2
  echo "Set UNIFIED_TRADING_WORKSPACE_ROOT or run from workspace root." >&2
  exit 1
fi

echo "═══════════════════════════════════════════════════════════"
echo "  Tier-3 shared Cloud Run deploy"
echo "═══════════════════════════════════════════════════════════"
echo "  Project:  $PROJECT_ID"
echo "  Region:   $REGION (co-located with GCS buckets)"
echo "  Service:  $SERVICE_NAME"
echo "  Image:    $IMAGE"
echo "  Branch:   $BRANCH"
echo "  SA:       $SA"
echo

if $DO_BUILD; then
  echo "==> [1/2] Cloud Build — full QG + UI bundle + image push (~5-10 min)"
  cd "$DEPLOYMENT_API_DIR"

  # The cloudbuild.yaml fetch-ui step tries to git-clone deployment-ui from
  # GitHub — that fails inside Cloud Build because the cloud-builders/git
  # image has no GitHub auth (private repo → 404). The same step has an
  # explicit fast-path: "if ./ui/package.json exists, skip the clone".
  # We pre-bundle a tarball of deployment-ui (HEAD on the same branch) so
  # the fetch-ui step short-circuits.
  UI_SRC="${WORKSPACE_ROOT}/deployment-ui"
  if [ ! -d "$UI_SRC" ]; then
    echo "ERROR: deployment-ui sibling repo not found at $UI_SRC" >&2
    exit 1
  fi

  echo "==> Pre-bundling deployment-ui into ./ui/ (skips Cloud Build git-clone)"
  TEMP_UI="${DEPLOYMENT_API_DIR}/ui"
  if [ -e "$TEMP_UI" ] || [ -L "$TEMP_UI" ]; then rm -rf "$TEMP_UI"; fi
  # rsync exclude the heavy/local-only paths — node_modules (will be reinstalled
  # by the Dockerfile's npm ci), dist, .git, test caches.
  rsync -a \
    --exclude='node_modules' \
    --exclude='dist' \
    --exclude='.git' \
    --exclude='coverage' \
    --exclude='.turbo' \
    --exclude='.cache' \
    --exclude='playwright-report' \
    --exclude='test-results' \
    "$UI_SRC/" "$TEMP_UI/"
  echo "    bundled ui/ size: $(du -sh "$TEMP_UI" | cut -f1)"
  trap 'rm -rf "${DEPLOYMENT_API_DIR}/ui"' EXIT

  # Manual `gcloud builds submit` does not auto-populate SHORT_SHA / COMMIT_SHA
  # (those only come from Cloud Build triggers). The repo's cloudbuild.yaml
  # references both in the ``images:`` push list, so we synthesise them from
  # local git HEAD and override via --substitutions. The image SHA tag is
  # informational; :latest is what Cloud Run actually consumes.
  SHORT_SHA="$(git -C "$DEPLOYMENT_API_DIR" rev-parse --short HEAD)"
  COMMIT_SHA="$(git -C "$DEPLOYMENT_API_DIR" rev-parse HEAD)"

  gcloud builds submit . \
    --project="$PROJECT_ID" \
    --config=cloudbuild.yaml \
    --substitutions="_BRANCH=${BRANCH},SHORT_SHA=${SHORT_SHA}" \
    --region="$REGION"
  echo "==> Build complete. :latest now points at the new digest."
fi

if $DO_DEPLOY; then
  echo
  echo "==> [2/2] Cloud Run deploy — rolling new revision (~30s)"
  gcloud run deploy "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --image="$IMAGE" \
    --port=8080 \
    --memory=2Gi \
    --cpu=1 \
    --min-instances=1 \
    --max-instances=4 \
    --timeout=900 \
    --service-account="$SA" \
    --allow-unauthenticated \
    --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},CLOUD_PROVIDER=gcp,CLOUD_MOCK_MODE=false,DEPLOYMENT_ENV=prod,DISABLE_AUTH=true" \
    --quiet

  URL=$(gcloud run services describe "$SERVICE_NAME" \
    --project="$PROJECT_ID" --region="$REGION" \
    --format='value(status.url)')

  echo
  echo "═══════════════════════════════════════════════════════════"
  echo "  Tier-3 deployed"
  echo "═══════════════════════════════════════════════════════════"
  echo "  URL:    $URL"
  echo "  UI:     $URL/                       (Vite SPA bundled)"
  echo "  API:    $URL/api/health             (health check)"
  echo "  Stats:  $URL/api/data-status/turbo/stats"
  echo
  echo "  Data-status latency (in-region GCS reads): expect ~2-5s warm."
  echo "  Subsequent re-deploys: same URL, zero-downtime revision swap."
  echo
fi
