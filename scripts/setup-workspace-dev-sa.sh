#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Create (or use existing) a service account for local workspace dev with access to
# all Secret Manager secrets. Key file is stored at workspace root — never committed.
# Rotate the key when people leave; no need to change IAM for individual users.
#
# Usage:
#   bash unified-trading-pm/scripts/setup-workspace-dev-sa.sh
#   PROJECT_ID=central-element-323112 bash unified-trading-pm/scripts/setup-workspace-dev-sa.sh
#
# Steps: 1) Create SA if missing  2) Grant secretAccessor  3) Create key → workspace root
#        Run test at the end to verify secret access.

set -e

PROJECT_ID="${PROJECT_ID:-central-element-323112}"
# Use existing SA (e.g. batch-processing-sa) or leave empty to create workspace-dev
SA_NAME="${WORKSPACE_SA_NAME:-workspace-dev}"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
# Key file at workspace root (parent of unified-trading-pm)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/../.." && pwd)"
KEY_FILE="${WORKSPACE_ROOT}/workspace-dev-sa-key.json"

echo "Project: $PROJECT_ID"
echo "Service account: $SA_EMAIL"
echo "Key file (do not commit): $KEY_FILE"
echo ""

if ! command -v gcloud &>/dev/null; then
  echo "Error: gcloud CLI not found."
  exit 1
fi

gcloud config set project "$PROJECT_ID"

# Create SA if it doesn't exist (skip if using existing SA and it exists)
if ! gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
  echo "Creating service account: $SA_NAME"
  gcloud iam service-accounts create "$SA_NAME" \
    --display-name="Workspace dev (secrets access, key at workspace root)"
else
  echo "Service account already exists: $SA_EMAIL"
fi
# To use an existing SA instead: WORKSPACE_SA_NAME=batch-processing-sa bash scripts/setup-workspace-dev-sa.sh

# Grant access to all secrets in the project
echo "Granting roles/secretmanager.secretAccessor to $SA_EMAIL on project..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None \
  --quiet

# Create key if file doesn't exist
if [[ -f "$KEY_FILE" ]]; then
  echo "Key file already exists: $KEY_FILE"
  echo "To rotate: delete it, then re-run this script to create a new key."
else
  echo "Creating new key and saving to: $KEY_FILE"
  gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL"
  echo "Key created. Ensure this path is in .gitignore (e.g. workspace-dev-sa-key.json)."
fi

echo ""
echo "--- Test secret access ---"
export GOOGLE_APPLICATION_CREDENTIALS="$KEY_FILE"
if gcloud secrets versions access latest --secret=betfair-api-key --project="$PROJECT_ID" &>/dev/null; then
  echo "OK: Service account can read betfair-api-key."
else
  echo "Test read (betfair-api-key) failed or secret missing. Check key and IAM."
fi
echo ""
echo "To use in local dev:"
echo "  export GOOGLE_APPLICATION_CREDENTIALS=\"$KEY_FILE\""
echo "  # Then run your app or: gcloud secrets versions access latest --secret=SECRET_NAME --project=$PROJECT_ID"
