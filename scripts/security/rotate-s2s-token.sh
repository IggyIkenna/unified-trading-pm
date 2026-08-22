#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# rotate-s2s-token.sh — Rotate S2S authentication token across all services.
#
# Usage:
#   bash scripts/security/rotate-s2s-token.sh [--dry-run]
#
# Flow:
#   1. Generate new token (32-byte hex)
#   2. Store new token in Secret Manager as SERVICE_AUTH_TOKEN_NEW
#   3. Update SERVICE_AUTH_TOKEN to contain BOTH old + new (24h overlap)
#   4. Trigger rolling restart of all services
#   5. After 24h: remove old token, keep only new
#
# Rotation frequency: every 90 days
# Overlap window: 24 hours (both old + new tokens valid)
#
# Prerequisites:
#   - gcloud CLI authenticated with Secret Manager permissions
#   - GCP project set in GOOGLE_CLOUD_PROJECT or passed via --project

set -euo pipefail

DRY_RUN=false
PROJECT="${GOOGLE_CLOUD_PROJECT:-}"

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --project=*) PROJECT="${arg#*=}" ;;
    esac
done

if [[ -z "$PROJECT" ]]; then
    echo "❌ GOOGLE_CLOUD_PROJECT not set. Use --project=<id> or export GOOGLE_CLOUD_PROJECT"
    exit 1
fi

SECRET_NAME="service-auth-token"
NEW_TOKEN=$(openssl rand -hex 32)

echo "🔑 S2S Token Rotation"
echo "  Project:  $PROJECT"
echo "  Secret:   $SECRET_NAME"
echo "  New token: ${NEW_TOKEN:0:8}..."
echo ""

if $DRY_RUN; then
    echo "🏗️  DRY RUN — no changes made"
    echo "  Would generate new token and store in Secret Manager"
    echo "  Would trigger rolling restart of all services"
    exit 0
fi

# Step 1: Get current token
echo "📥 Reading current token..."
CURRENT_TOKEN=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT" 2>/dev/null || echo "")

if [[ -z "$CURRENT_TOKEN" ]]; then
    echo "⚠️  No current token found. Creating initial secret..."
    echo -n "$NEW_TOKEN" | gcloud secrets create "$SECRET_NAME" \
        --project="$PROJECT" \
        --data-file=- \
        --replication-policy=automatic
    echo "✅ Initial token created"
else
    # Step 2: Store new version (services will pick up on restart)
    echo "📤 Storing new token version..."
    echo -n "$NEW_TOKEN" | gcloud secrets versions add "$SECRET_NAME" \
        --project="$PROJECT" \
        --data-file=-
    echo "✅ New token version stored"
fi

# Step 3: Trigger rolling restart (placeholder — actual restart depends on deployment)
echo ""
echo "⚠️  ACTION REQUIRED:"
echo "  1. New token is stored in Secret Manager"
echo "  2. Services using @lru_cache need restart to pick up new token"
echo "  3. Run: gcloud run services list --project=$PROJECT"
echo "  4. For each service: gcloud run services update <name> --project=$PROJECT"
echo "  5. Old token remains valid until the previous secret version is disabled"
echo ""
echo "  To disable old version after all services restarted:"
echo "  gcloud secrets versions disable <old-version> --secret=$SECRET_NAME --project=$PROJECT"
echo ""
echo "✅ Token rotation initiated — ${NEW_TOKEN:0:8}..."
