#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# List all human (user:) principals on the project's IAM policy and highlight
# ones matching datadodo / Data Dodo or Harsh. Use to find emails for granting
# Secret Manager access.
#
# Usage:
#   bash unified-trading-pm/scripts/list-gcp-iam-emails.sh
#   PROJECT_ID=central-element-323112 bash unified-trading-pm/scripts/list-gcp-iam-emails.sh
#
# Requires: gcloud installed and authenticated.

set -e

PROJECT_ID="${PROJECT_ID:-central-element-323112}"
KEYWORDS=("dodo" "datadodo" "harsh" "femi" "amoo")

echo "Fetching IAM policy for project: $PROJECT_ID"
echo ""

if ! command -v gcloud &>/dev/null; then
  echo "Error: gcloud CLI not found. Install from https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Get IAM policy and extract user: emails (Python for reliable JSON parsing)
USER_EMAILS=$(gcloud projects get-iam-policy "$PROJECT_ID" --format=json 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
except Exception as e:
    sys.exit(1)
emails = set()
for binding in data.get('bindings', []):
    for m in binding.get('members', []):
        if m.startswith('user:'):
            emails.add(m.replace('user:', ''))
for e in sorted(emails):
    print(e)
" 2>/dev/null)

if [[ -z "$USER_EMAILS" ]]; then
  echo "No user principals found in IAM policy (or Python parse failed)."
  echo "Run: gcloud projects get-iam-policy $PROJECT_ID --format=json to inspect."
  exit 1
fi

echo "All user principals (emails) on project $PROJECT_ID:"
echo "----------------------------------------"
echo "$USER_EMAILS"
echo ""

echo "Likely matches for datadodo / Data Dodo or Harsh:"
echo "----------------------------------------"
FOUND=""
while IFS= read -r email; do
  lower=$(echo "$email" | tr '[:upper:]' '[:lower:]')
  for kw in "${KEYWORDS[@]}"; do
    if [[ "$lower" == *"$kw"* ]]; then
      echo "  -> $email"
      FOUND=1
      break
    fi
  done
done <<<"$USER_EMAILS"

if [[ -z "$FOUND" ]]; then
  echo "  (none matched keywords: ${KEYWORDS[*]})"
  echo "  Check the full list above for the correct emails."
fi
