#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Rotate the alerting-service Telegram bot token in both GCP and AWS Secret Manager.
#
# Run AFTER completing @BotFather token rotation:
#   1. /revoke the old token in @BotFather
#   2. /newbot (or use the same bot — re-generate token via /mybots → API Token → Revoke)
#   3. Run this script with the new token value
#
# Usage:
#   bash scripts/rotate_telegram_token.sh -t "NEW_BOT_TOKEN"
#   echo -n "NEW_BOT_TOKEN" | bash scripts/rotate_telegram_token.sh
#
# Target secrets (both clouds):
#   GCP: projects/central-element-323112/secrets/alerting-telegram-bot-token
#   AWS: ap-northeast-1 / alerting-telegram-bot-token (account 427895769566)

set -euo pipefail

GCP_PROJECT="central-element-323112"
AWS_REGION="ap-northeast-1"
SECRET_NAME="alerting-telegram-bot-token"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
die()     { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

NEW_TOKEN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--token) NEW_TOKEN="$2"; shift 2 ;;
        -h|--help)
            sed -n '1,15p' "$0"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

if [[ -z "$NEW_TOKEN" ]]; then
    if [[ -t 0 ]]; then
        die "No token provided. Use -t TOKEN or pipe on stdin."
    fi
    NEW_TOKEN=$(cat)
fi

[[ -z "$NEW_TOKEN" ]] && die "Token value is empty."
[[ "$NEW_TOKEN" == *":"* ]] || die "Token looks malformed — expected format: <bot_id>:<hash>"

info "Rotating $SECRET_NAME in GCP + AWS"
echo ""

# ── GCP ──────────────────────────────────────────────────────────────────────
info "GCP: adding new version to projects/$GCP_PROJECT/secrets/$SECRET_NAME"
if ! command -v gcloud &>/dev/null; then
    die "gcloud CLI not found. Install from https://cloud.google.com/sdk/docs/install"
fi
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q .; then
    die "No active gcloud auth. Run: gcloud auth login"
fi

echo -n "$NEW_TOKEN" | gcloud secrets versions add "$SECRET_NAME" \
    --project="$GCP_PROJECT" \
    --data-file=- 2>&1

GCP_RETRIEVED=$(gcloud secrets versions access latest \
    --secret="$SECRET_NAME" \
    --project="$GCP_PROJECT" 2>/dev/null)
if [[ "$GCP_RETRIEVED" == "$NEW_TOKEN" ]]; then
    info "GCP ✅  latest version verified"
else
    die "GCP retrieval check failed — stored value does not match"
fi

# ── AWS ──────────────────────────────────────────────────────────────────────
echo ""
info "AWS: updating $SECRET_NAME in $AWS_REGION"
if ! command -v aws &>/dev/null; then
    die "aws CLI not found. Install from https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
fi
if ! aws sts get-caller-identity --region "$AWS_REGION" &>/dev/null; then
    die "No active AWS auth for region $AWS_REGION. Run: aws configure"
fi

aws secretsmanager put-secret-value \
    --region "$AWS_REGION" \
    --secret-id "$SECRET_NAME" \
    --secret-string "$NEW_TOKEN" \
    --output text \
    --query 'VersionId' 2>&1 | xargs -I{} echo "AWS version: {}"

AWS_RETRIEVED=$(aws secretsmanager get-secret-value \
    --region "$AWS_REGION" \
    --secret-id "$SECRET_NAME" \
    --query 'SecretString' \
    --output text 2>/dev/null)
if [[ "$AWS_RETRIEVED" == "$NEW_TOKEN" ]]; then
    info "AWS ✅  latest version verified"
else
    die "AWS retrieval check failed — stored value does not match"
fi

echo ""
info "Both clouds updated. Next steps:"
echo "  1. Verify alerting-service can send a smoke alert:"
echo "     TELEGRAM_BOT_TOKEN='$NEW_TOKEN' python -c \\"
echo "       \"from alerting_service.notifiers.telegram import send_telegram; import asyncio; asyncio.run(send_telegram('rotation smoke OK'))\""
echo "  2. Flip the checkbox in plans/active/alerting_service_live_rules_2026_05_07.md Phase 4 item"
echo "  3. Push the plan flip: git add plans/active/alerting_service_live_rules_2026_05_07.md && git commit -m 'docs(plans): flip Phase 4 token-rotation item' && git push origin HEAD:live-defi-rollout"
