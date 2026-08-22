#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Create Cloud Build feature-branch triggers for all repos.
# Run from workspace root. Requires gcloud auth and Cloud Build API.
#
# Usage: bash unified-trading-pm/scripts/create-cloud-build-feature-triggers.sh
#
# Creates triggers with branch pattern ^feat/.* for each repo.
# Idempotent: skips if trigger already exists.

set -euo pipefail

REGION="${REGION:-asia-northeast1}"
REPO_BASE="projects/$(gcloud config get-value project 2>/dev/null)/locations/${REGION}/connections/iggyikenna-github/repositories"

REPOS="deployment-service deployment-api features-multi-timeframe-service ml-training-ui execution-service market-tick-data-service unified-reference-data-interface unified-api-contracts unified-market-interface unified-config-interface unified-trading-library deployment-dashboard unified-cloud-interface features-calendar-service market-data-processing-service strategy-service features-volatility-service features-onchain-service features-delta-one-service ml-training-service ml-inference-service instruments-service position-balance-monitor-service unified-trading-library"

for name in $REPOS; do
  repo="${REPO_BASE}/${name}"
  [ "$name" = "deployment-dashboard" ] && repo="${REPO_BASE}/unified-trading-deployment-v2"
  trigger_name="${name}-feature-build"
  if gcloud builds triggers describe "$trigger_name" --region="$REGION" &>/dev/null; then
    echo "SKIP $trigger_name"
  else
    gcloud builds triggers create github --name="$trigger_name" --repository="$repo" --branch-pattern="^feat/.*" --build-config="cloudbuild.yaml" --description="Build $name on feat/*" --region="$REGION" 2>&1 | tail -1
  fi
done
echo "Done."
