#!/usr/bin/env bash
# Add Cloud Build triggers for deployment-api and deployment-service.
#
# Prerequisites:
#   - GCP_PROJECT_ID set (or central-element-323112)
#   - gcloud authenticated
#   - Cloud Build GitHub connection (iggyikenna-github) with repo access
#
# Usage:
#   GCP_PROJECT_ID=your-project bash unified-trading-pm/scripts/setup-cloud-build-triggers-new-repos.sh

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-central-element-323112}"
REGION="${GCP_REGION:-asia-northeast1}"
CONNECTION="${CB_CONNECTION:-iggyikenna-github}"
GITHUB_OWNER="${GITHUB_OWNER:-IggyIkenna}"

NEW_REPOS=(deployment-api deployment-service)

repo_uri() { echo "https://github.com/${GITHUB_OWNER}/${1}.git"; }
repo_resource() { echo "projects/${PROJECT_ID}/locations/${REGION}/connections/${CONNECTION}/repositories/${1}"; }

add_repo_if_missing() {
  local repo="$1"
  if gcloud builds repositories describe "$repo" --connection="$CONNECTION" --region="$REGION" --project="$PROJECT_ID" 2>/dev/null; then
    echo "✓ Repository $repo already in connection"
    return 0
  fi
  echo "Adding repository $repo..."
  gcloud builds repositories create "$repo" \
    --remote-uri="$(repo_uri "$repo")" \
    --connection="$CONNECTION" \
    --region="$REGION" \
    --project="$PROJECT_ID" || { echo "⚠ $repo: Add via GCP Console > Cloud Build > Repositories"; return 1; }
}

create_trigger_if_missing() {
  local repo="$1"
  local trigger_name="${repo}-build"
  local repo_res
  repo_res=$(repo_resource "$repo")
  if gcloud builds triggers describe "$trigger_name" --region="$REGION" --project="$PROJECT_ID" 2>/dev/null; then
    echo "✓ Trigger $trigger_name already exists"
    return 0
  fi
  if ! gcloud builds repositories describe "$repo" --connection="$CONNECTION" --region="$REGION" --project="$PROJECT_ID" 2>/dev/null; then
    echo "⚠ Skipping trigger $trigger_name (repo not in connection)"
    return 1
  fi
  echo "Creating trigger $trigger_name..."
  gcloud builds triggers create github \
    --name="$trigger_name" \
    --repository="$repo_res" \
    --branch-pattern="^main$" \
    --build-config="cloudbuild.yaml" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --description="Build ${repo} on main push"
}

echo "=== Cloud Build triggers for deployment-api, deployment-service ==="
echo "Project: $PROJECT_ID | Region: $REGION | Connection: $CONNECTION"
echo ""

for repo in "${NEW_REPOS[@]}"; do
  add_repo_if_missing "$repo" || true
done
echo ""
for repo in "${NEW_REPOS[@]}"; do
  create_trigger_if_missing "$repo" || true
done
echo ""
echo "=== Done ==="
gcloud builds triggers list --region="$REGION" --project="$PROJECT_ID" --filter="name:deployment" --format="table(name,description)"
