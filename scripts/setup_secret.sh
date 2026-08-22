#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Create or add a new version of a secret in GCP Secret Manager.
# Use from workspace root or PM repo. Requires gcloud CLI and auth.
#
# Usage:
#   bash unified-trading-pm/scripts/setup_secret.sh -p PROJECT_ID -n SECRET_NAME -v "secret_value"
#   echo -n "secret_value" | bash unified-trading-pm/scripts/setup_secret.sh -p PROJECT_ID -n SECRET_NAME
#   bash unified-trading-pm/scripts/setup_secret.sh -p PROJECT_ID -n betfair-api-key -v "YOUR_BETFAIR_APP_KEY"
#
# Options:
#   -p, --project-id PROJECT_ID   GCP project ID (required)
#   -n, --secret-name NAME        Secret name in Secret Manager (required), e.g. betfair-api-key
#   -v, --value "VALUE"           Secret value (optional; otherwise read from stdin)
#   -f, --from-file PATH          Read secret value from file (optional)
#   -h, --help                    Show this help

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_usage() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  -p, --project-id PROJECT_ID   GCP project ID (required)"
  echo "  -n, --secret-name NAME        Secret name (required), e.g. betfair-api-key"
  echo "  -v, --value \"VALUE\"           Secret value (optional; else stdin)"
  echo "  -f, --from-file PATH          Read value from file (optional)"
  echo "  -h, --help                    Show this help"
  echo ""
  echo "Examples:"
  echo "  $0 -p my-project -n betfair-api-key -v \"YOUR_BETFAIR_APP_KEY\""
  echo "  echo -n 'key' | $0 -p my-project -n tardis-api-key"
}

PROJECT_ID=""
SECRET_NAME=""
SECRET_VALUE=""
FROM_FILE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    -p | --project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    -n | --secret-name)
      SECRET_NAME="$2"
      shift 2
      ;;
    -v | --value)
      SECRET_VALUE="$2"
      shift 2
      ;;
    -f | --from-file)
      FROM_FILE="$2"
      shift 2
      ;;
    -h | --help)
      show_usage
      exit 0
      ;;
    *)
      print_error "Unknown option: $1"
      show_usage
      exit 1
      ;;
  esac
done

if [[ -z "$PROJECT_ID" ]]; then
  print_error "Project ID required. Use -p or --project-id"
  show_usage
  exit 1
fi
if [[ -z "$SECRET_NAME" ]]; then
  print_error "Secret name required. Use -n or --secret-name"
  show_usage
  exit 1
fi

if [[ -n "$FROM_FILE" ]]; then
  if [[ ! -r "$FROM_FILE" ]]; then
    print_error "File not readable: $FROM_FILE"
    exit 1
  fi
  SECRET_VALUE=$(<"$FROM_FILE")
elif [[ -z "$SECRET_VALUE" ]]; then
  if [[ -t 0 ]]; then
    print_error "No value provided. Use -v, -f, or pipe value on stdin."
    show_usage
    exit 1
  fi
  SECRET_VALUE=$(cat)
fi

if [[ -z "$SECRET_VALUE" ]]; then
  print_error "Secret value is empty."
  exit 1
fi

if ! command -v gcloud &>/dev/null; then
  print_error "gcloud CLI not installed. See https://cloud.google.com/sdk/docs/install"
  exit 1
fi

if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
  print_error "No active gcloud auth. Run: gcloud auth login"
  exit 1
fi

print_status "Project: $PROJECT_ID | Secret: $SECRET_NAME"
gcloud config set project "$PROJECT_ID"
print_status "Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
  print_warning "Secret '$SECRET_NAME' already exists. Adding new version."
else
  print_status "Creating secret: $SECRET_NAME"
  echo -n | gcloud secrets create "$SECRET_NAME" --data-file=- --project="$PROJECT_ID" --replication-policy=automatic
fi

print_status "Adding secret version..."
echo -n "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" --data-file=- --project="$PROJECT_ID"

CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null || true)
if [[ -n "$CURRENT_ACCOUNT" ]]; then
  print_status "Granting access to current user: $CURRENT_ACCOUNT"
  gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
    --member="user:$CURRENT_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project="$PROJECT_ID"
fi

RETRIEVED=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID")
if [[ "$RETRIEVED" == "$SECRET_VALUE" ]]; then
  print_status "Secret setup successful."
  echo ""
  echo "Verify: gcloud secrets versions access latest --secret=$SECRET_NAME --project=$PROJECT_ID"
  echo "For Cloud Run / batch SA: gcloud secrets add-iam-policy-binding $SECRET_NAME \\"
  echo "  --member='serviceAccount:YOUR_SA@$PROJECT_ID.iam.gserviceaccount.com' \\"
  echo "  --role='roles/secretmanager.secretAccessor' --project=$PROJECT_ID"
else
  print_error "Retrieval test failed."
  exit 1
fi
