#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Provision AWS SNS topics + SQS queues for the Unified Trading System messaging bus.
#
# Creates 5 trading-event topics (SNS) each with a paired SQS queue subscriber,
# matching the GCP Pub/Sub topics documented in the cloud-agnostic audit §7.
#
# GCP topic → AWS equivalent:
#   risk_alerts_circuit_breaker_triggers  → uts-risk-alerts-circuit-breaker-triggers
#   balance_discrepancy_alerts            → uts-balance-discrepancy-alerts
#   order_rejection_spikes                → uts-order-rejection-spikes
#   circuit_breaker_commands              → uts-circuit-breaker-commands
#   service_stop_restart_triggers         → uts-service-stop-restart-triggers
#
# Policy: SNS+SQS for all trading-event and command topics.  EventBridge only
# for cross-account deployment-orchestration (not provisioned here).
#
# Usage:
#   bash scripts/aws/setup-messaging.sh [--dry-run]
#
# Prerequisites:
#   - AWS CLI configured with credentials that have SNS + SQS create permissions.
#   - AWS_REGION env var set (defaults to us-east-1 if absent).
#
# Idempotent: SNS CreateTopic and SQS CreateQueue are no-ops when the resource
# already exists.
#
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }
log_ok()      { echo -e "${GREEN}✅ $1${NC}"; }
log_skip()    { echo -e "${YELLOW}⏭  $1${NC}"; }
log_fail()    { echo -e "${RED}❌ $1${NC}"; }

# 5 trading-event / command topics — all use SNS+SQS (at-least-once, no cross-account routing needed)
TOPICS=(
  "uts-risk-alerts-circuit-breaker-triggers"
  "uts-balance-discrepancy-alerts"
  "uts-order-rejection-spikes"
  "uts-circuit-breaker-commands"
  "uts-service-stop-restart-triggers"
)

run_cmd() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] $*"
    return 0
  fi
  "$@"
}

log_section "AWS messaging setup — region=${REGION} dry_run=${DRY_RUN}"

# Resolve AWS account ID (needed to construct ARNs for queue policy)
if [[ "$DRY_RUN" == "true" ]]; then
  ACCOUNT_ID="123456789012"
else
  ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
fi
echo "Account ID: ${ACCOUNT_ID}"

ERRORS=0

for TOPIC in "${TOPICS[@]}"; do
  QUEUE_NAME="${TOPIC}-queue"
  log_section "Topic: ${TOPIC}"

  # 1. Create SNS topic (idempotent)
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] aws sns create-topic --name ${TOPIC} --region ${REGION}"
    TOPIC_ARN="arn:aws:sns:${REGION}:${ACCOUNT_ID}:${TOPIC}"
  else
    TOPIC_ARN="$(aws sns create-topic --name "${TOPIC}" --region "${REGION}" --query TopicArn --output text)"
    if [[ -z "$TOPIC_ARN" ]]; then
      log_fail "Failed to create SNS topic ${TOPIC}"
      ERRORS=$((ERRORS + 1))
      continue
    fi
  fi
  log_ok "SNS topic: ${TOPIC_ARN}"

  # 2. Create SQS queue (idempotent)
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] aws sqs create-queue --queue-name ${QUEUE_NAME} --region ${REGION}"
    QUEUE_URL="https://sqs.${REGION}.amazonaws.com/${ACCOUNT_ID}/${QUEUE_NAME}"
  else
    QUEUE_URL="$(aws sqs create-queue --queue-name "${QUEUE_NAME}" --region "${REGION}" --query QueueUrl --output text)"
    if [[ -z "$QUEUE_URL" ]]; then
      log_fail "Failed to create SQS queue ${QUEUE_NAME}"
      ERRORS=$((ERRORS + 1))
      continue
    fi
  fi
  QUEUE_ARN="arn:aws:sqs:${REGION}:${ACCOUNT_ID}:${QUEUE_NAME}"
  log_ok "SQS queue: ${QUEUE_URL}"

  # 3. Set SQS queue policy to allow SNS to publish
  QUEUE_POLICY="$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSNSPublish",
      "Effect": "Allow",
      "Principal": { "Service": "sns.amazonaws.com" },
      "Action": "sqs:SendMessage",
      "Resource": "${QUEUE_ARN}",
      "Condition": { "ArnEquals": { "aws:SourceArn": "${TOPIC_ARN}" } }
    }
  ]
}
EOF
)"

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] aws sqs set-queue-attributes --queue-url ${QUEUE_URL} --attributes Policy=<json> --region ${REGION}"
  else
    aws sqs set-queue-attributes \
      --queue-url "${QUEUE_URL}" \
      --attributes "Policy=$(echo "$QUEUE_POLICY" | tr -d '\n')" \
      --region "${REGION}"
  fi
  log_ok "Queue policy set (allows SNS publish from ${TOPIC_ARN})"

  # 4. Subscribe SQS queue to SNS topic (idempotent — SNS deduplicates by endpoint ARN)
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] aws sns subscribe --topic-arn ${TOPIC_ARN} --protocol sqs --notification-endpoint ${QUEUE_ARN} --region ${REGION}"
  else
    aws sns subscribe \
      --topic-arn "${TOPIC_ARN}" \
      --protocol sqs \
      --notification-endpoint "${QUEUE_ARN}" \
      --region "${REGION}" \
      --output text > /dev/null
  fi
  log_ok "SQS queue subscribed to SNS topic"

done

log_section "Summary"
if [[ "$ERRORS" -gt 0 ]]; then
  log_fail "Completed with ${ERRORS} error(s) — see above"
  exit 1
fi

if [[ "$DRY_RUN" == "true" ]]; then
  log_skip "DRY-RUN complete — no resources created. Re-run without --dry-run to apply."
else
  log_ok "All ${#TOPICS[@]} SNS topics + SQS queues provisioned in region ${REGION}"
fi
