#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Route 53 DNS routing setup for unified-trading-system-ui on AWS.
#
# ARCHITECTURE: weighted A-record routing between GCP Cloud Run and AWS ALB.
# During DeFi cutover, shift weight from GCP (100) → AWS (100) to move all
# production traffic to the Fargate deployment in ap-northeast-1.
#
# Usage (initial setup — both endpoints active, all traffic to GCP):
#   bash setup-dns-routing.sh \
#     --domain odum-research.com \
#     --alb-dns <alb-dns-name>.ap-northeast-1.elb.amazonaws.com \
#     --alb-hz <alb-hosted-zone-id> \
#     --gcp-ip <current-cloud-run-global-lb-ip> \
#     --mode setup
#
# Usage (cutover — shift all traffic to AWS):
#   bash setup-dns-routing.sh \
#     --domain odum-research.com \
#     --alb-dns <alb-dns-name>.ap-northeast-1.elb.amazonaws.com \
#     --alb-hz <alb-hosted-zone-id> \
#     --mode cutover
#
# Usage (rollback — shift all traffic back to GCP):
#   bash setup-dns-routing.sh \
#     --domain odum-research.com \
#     --gcp-ip <current-cloud-run-global-lb-ip> \
#     --mode rollback
#
# IMPORTANT: After setup, you must update the domain registrar (Squarespace /
# Google Domains / Namecheap) to use the Route 53 NS records that this script
# prints. Until NS records propagate (~48h), Squarespace / existing registrar
# DNS remains authoritative.
#
# Data-locality rationale: odum-research.com currently points to Cloud Run
# (europe-west4 / us-central1 / asia-northeast1). For DeFi cutover, all
# trading traffic must co-locate with DeFi data on ap-northeast-1. Weighted
# routing allows gradual traffic shift with instant rollback capability.
#
set -euo pipefail

DOMAIN=""
ALB_DNS=""
ALB_HZ=""
GCP_IP=""
MODE="setup"
AWS_REGION="${AWS_REGION:-ap-northeast-1}"

usage() {
  grep "^# Usage" "$0" | sed 's/^# //'
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --domain)    DOMAIN="$2";  shift 2 ;;
    --alb-dns)   ALB_DNS="$2"; shift 2 ;;
    --alb-hz)    ALB_HZ="$2";  shift 2 ;;
    --gcp-ip)    GCP_IP="$2";  shift 2 ;;
    --mode)      MODE="$2";    shift 2 ;;
    *) echo "Unknown arg: $1"; usage ;;
  esac
done

[[ -n "$DOMAIN" ]] || { echo "ERROR: --domain required"; usage; }

echo "=== Route 53 DNS routing for $DOMAIN ==="
echo "  Mode:   $MODE"
echo "  Region: $AWS_REGION"

# ── Step 1: Ensure hosted zone exists ────────────────────────────────────────

ZONE_ID=$(aws route53 list-hosted-zones-by-name \
  --dns-name "$DOMAIN." \
  --query "HostedZones[?Name=='${DOMAIN}.'].Id" \
  --output text 2>/dev/null | head -1 | sed 's|/hostedzone/||')

if [[ -z "$ZONE_ID" ]]; then
  echo "Creating Route 53 hosted zone for $DOMAIN..."
  ZONE_ID=$(aws route53 create-hosted-zone \
    --name "$DOMAIN" \
    --caller-reference "uts-$(date +%s)" \
    --query 'HostedZone.Id' \
    --output text | sed 's|/hostedzone/||')
  echo "  Created zone: $ZONE_ID"
  echo ""
  echo "⚠️  ACTION REQUIRED: Update domain registrar NS records to:"
  aws route53 get-hosted-zone --id "$ZONE_ID" \
    --query 'DelegationSet.NameServers' --output text
  echo "(NS propagation takes up to 48h)"
else
  echo "  Found existing zone: $ZONE_ID"
fi

# ── Helper: upsert a Route53 record set ──────────────────────────────────────

upsert_record() {
  local name="$1" type="$2" value="$3" weight="$4" set_id="$5"
  # value is either an IP (A record) or an ALB alias JSON
  local record_value_json
  if [[ "$type" == "ALIAS" ]]; then
    # ALB alias — value="<alb-dns>|<alb-hz>"
    local alb_dns_name="${value%%|*}"
    local alb_hz_id="${value##*|}"
    record_value_json=$(cat <<EOF
{
  "AliasTarget": {
    "HostedZoneId": "$alb_hz_id",
    "DNSName": "$alb_dns_name",
    "EvaluateTargetHealth": true
  }
}
EOF
)
  else
    record_value_json=$(cat <<EOF
{
  "TTL": 60,
  "ResourceRecords": [{"Value": "$value"}]
}
EOF
)
  fi

  aws route53 change-resource-record-sets \
    --hosted-zone-id "$ZONE_ID" \
    --change-batch "$(cat <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "$name",
      "Type": "A",
      "SetIdentifier": "$set_id",
      "Weight": $weight,
      $record_value_json
    }
  }]
}
EOF
)" \
    --output text > /dev/null
  echo "  Upserted $name weight=$weight set-id=$set_id"
}

# ── Step 2: Configure weighted routing ───────────────────────────────────────

WWW="www.${DOMAIN}"

case "$MODE" in
  setup)
    [[ -n "$ALB_DNS" && -n "$ALB_HZ" && -n "$GCP_IP" ]] || {
      echo "ERROR: --alb-dns, --alb-hz, and --gcp-ip required for setup mode"
      exit 1
    }
    echo "Setting up weighted routing: GCP weight=100, AWS weight=0..."
    upsert_record "$WWW" "A"     "$GCP_IP"             100 "gcp-cloud-run"
    upsert_record "$WWW" "ALIAS" "${ALB_DNS}|${ALB_HZ}" 0  "aws-fargate"
    echo "  Traffic currently: 100% GCP, 0% AWS (gradual shift via 'cutover' mode)"
    ;;

  cutover)
    [[ -n "$ALB_DNS" && -n "$ALB_HZ" ]] || {
      echo "ERROR: --alb-dns and --alb-hz required for cutover mode"
      exit 1
    }
    echo "Cutting over to AWS: GCP weight=0, AWS weight=100..."
    # If GCP record exists, set weight=0 (keeps rollback available without deletion)
    if [[ -n "$GCP_IP" ]]; then
      upsert_record "$WWW" "A"     "$GCP_IP"             0   "gcp-cloud-run"
    fi
    upsert_record "$WWW" "ALIAS" "${ALB_DNS}|${ALB_HZ}" 100 "aws-fargate"
    echo "  Traffic now: 0% GCP, 100% AWS"
    echo "  Verify: dig $WWW +short"
    ;;

  rollback)
    [[ -n "$GCP_IP" ]] || {
      echo "ERROR: --gcp-ip required for rollback mode"
      exit 1
    }
    echo "Rolling back to GCP: GCP weight=100, AWS weight=0..."
    upsert_record "$WWW" "A"     "$GCP_IP" 100 "gcp-cloud-run"
    if [[ -n "$ALB_DNS" && -n "$ALB_HZ" ]]; then
      upsert_record "$WWW" "ALIAS" "${ALB_DNS}|${ALB_HZ}" 0 "aws-fargate"
    fi
    echo "  Traffic now: 100% GCP, 0% AWS"
    ;;

  *)
    echo "ERROR: --mode must be setup|cutover|rollback"
    exit 1
    ;;
esac

echo ""
echo "=== Route 53 DNS routing $MODE complete ==="
echo "DNS propagation TTL: 60s (next dig result should reflect change within 1 min)"
