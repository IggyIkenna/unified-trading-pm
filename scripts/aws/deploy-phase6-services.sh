#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Phase 6 ECS Fargate + App Runner deployment script for DeFi-live services.
#
# SSOT: plans/active/aws_migration_defi_first_2026_05_07.md § Phase 6
#
# Services:
#   App Runner  — alerting-service, deployment-api, position-balance-monitor-service
#   ECS Fargate — execution-service, features-service, strategy-service, risk-and-exposure-service
#
# Usage:
#   bash deploy-phase6-services.sh [--dry-run] [--manifest-dir <path>] [--env staging|prod]
#
# Prerequisites:
#   - AWS CLI v2 with ecs:*, apprunner:*, ecr:*, iam:GetRole permissions
#   - deployment-service/configs/aws/ manifests (deployment-service@e7964c7+)
#   - ECS cluster uts-defi-prod already created (DONE 2026-05-21)
#   - ECR images built via CodeBuild (build IDs in plan § Phase 6 "IN PROGRESS")
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }
log_ok()      { echo -e "${GREEN}✅ $1${NC}"; }
log_skip()    { echo -e "${YELLOW}⏭  $1${NC}"; }
log_fail()    { echo -e "${RED}❌ $1${NC}"; }
log_info()    { echo -e "   $1"; }

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DRY_RUN=false
ENV="${DEPLOY_ENV:-prod}"
MANIFEST_DIR="${WS_ROOT}/deployment-service/configs/aws"
AWS_REGION="${AWS_REGION:-ap-northeast-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-427895769566}"
ECS_CLUSTER="uts-defi-prod"

# Build SHAs from Phase 6 IN-PROGRESS state (plan 2026-05-21)
# Override with ECR_TAG_<SERVICE_UPPER>=<tag> env vars if builds have newer tags
ALERTING_TAG="${ECR_TAG_ALERTING_SERVICE:-7c0a3ec6}"
EXECUTION_TAG="${ECR_TAG_EXECUTION_SERVICE:-51057f1f}"
FEATURES_TAG="${ECR_TAG_FEATURES_SERVICE:-bad0af28}"
STRATEGY_TAG="${ECR_TAG_STRATEGY_SERVICE:-988aeee8}"
RISK_TAG="${ECR_TAG_RISK_AND_EXPOSURE_SERVICE:-4861c3fa}"
PBM_TAG="${ECR_TAG_POSITION_BALANCE_MONITOR_SERVICE:-a7ec3263}"
DEPLOY_API_TAG="${ECR_TAG_DEPLOYMENT_API:-8ec6982c}"

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)       DRY_RUN=true; shift ;;
    --env)           ENV="${2:?--env requires staging or prod}"; shift 2 ;;
    --manifest-dir)  MANIFEST_DIR="${2:?--manifest-dir requires a path}"; shift 2 ;;
    *)               echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# ---------------------------------------------------------------------------
# Service definitions
# ---------------------------------------------------------------------------
declare -A SERVICE_TYPE=(
  [alerting-service]="apprunner"
  [deployment-api]="apprunner"
  [position-balance-monitor-service]="apprunner"
  [execution-service]="fargate"
  [features-service]="fargate"
  [strategy-service]="fargate"
  [risk-and-exposure-service]="fargate"
)

declare -A SERVICE_TAG=(
  [alerting-service]="${ALERTING_TAG}"
  [deployment-api]="${DEPLOY_API_TAG}"
  [position-balance-monitor-service]="${PBM_TAG}"
  [execution-service]="${EXECUTION_TAG}"
  [features-service]="${FEATURES_TAG}"
  [strategy-service]="${STRATEGY_TAG}"
  [risk-and-exposure-service]="${RISK_TAG}"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ecr_image_exists() {
  local svc="$1" tag="$2"
  aws ecr describe-images \
    --repository-name "${svc}" \
    --image-ids imageTag="${tag}" \
    --region "${AWS_REGION}" \
    --query 'imageDetails[0].imagePushedAt' \
    --output text 2>/dev/null | grep -qv "None"
}

run_cmd() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] $*"
  else
    "$@"
  fi
}

# ---------------------------------------------------------------------------
# Step 1: Verify ECR images exist for all 7 services
# ---------------------------------------------------------------------------
log_section "Step 1 — Verify ECR images"
MISSING_IMAGES=()
for svc in "${!SERVICE_TAG[@]}"; do
  tag="${SERVICE_TAG[$svc]}"
  if ecr_image_exists "${svc}" "${tag}"; then
    log_ok "${svc}:${tag}"
  else
    log_fail "${svc}:${tag} — NOT FOUND in ECR"
    MISSING_IMAGES+=("${svc}:${tag}")
  fi
done

if [[ ${#MISSING_IMAGES[@]} -gt 0 ]]; then
  echo ""
  log_fail "Missing ECR images: ${MISSING_IMAGES[*]}"
  echo "Run: aws codebuild start-build --project-name <service> --region ${AWS_REGION}"
  echo "Check build status: aws codebuild list-builds-for-project --project-name <service>"
  if [[ "$DRY_RUN" != "true" ]]; then
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# Step 2: Deploy Fargate services
# ---------------------------------------------------------------------------
FARGATE_SERVICES=(execution-service features-service strategy-service risk-and-exposure-service)
log_section "Step 2 — ECS Fargate deployments (cluster: ${ECS_CLUSTER})"

for svc in "${FARGATE_SERVICES[@]}"; do
  tag="${SERVICE_TAG[$svc]}"
  image="${ECR_BASE}/${svc}:${tag}"
  manifest="${MANIFEST_DIR}/${svc}.yaml"

  log_info "Deploying ${svc} (${image})"

  if [[ ! -f "$manifest" ]]; then
    log_skip "Manifest not found: ${manifest} — skipping ${svc}"
    continue
  fi

  # Parse manifest for cpu/memory/role (yq or python fallback)
  if command -v yq &>/dev/null; then
    CPU=$(yq '.cpu' "$manifest")
    MEMORY=$(yq '.memory' "$manifest")
    TASK_ROLE_ARN=$(yq '.iam_role_arn' "$manifest")
    HEALTH_PATH=$(yq '.health_check.path // "/health"' "$manifest")
    PORT=$(yq '.port // 8000' "$manifest")
  elif command -v python3 &>/dev/null; then
    CPU=$(python3 -c "import sys,yaml; d=yaml.safe_load(open('$manifest')); print(d.get('cpu',512))")
    MEMORY=$(python3 -c "import sys,yaml; d=yaml.safe_load(open('$manifest')); print(d.get('memory',1024))")
    TASK_ROLE_ARN=$(python3 -c "import sys,yaml; d=yaml.safe_load(open('$manifest')); print(d.get('iam_role_arn',''))")
    HEALTH_PATH=$(python3 -c "import sys,yaml; d=yaml.safe_load(open('$manifest')); print(d.get('health_check',{}).get('path','/health'))")
    PORT=$(python3 -c "import sys,yaml; d=yaml.safe_load(open('$manifest')); print(d.get('port',8000))")
  else
    log_fail "Need yq or python3+pyyaml to parse manifests"; exit 1
  fi

  # Register task definition
  TASK_DEF_JSON=$(cat <<EOF
{
  "family": "uts-${svc}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "${CPU}",
  "memory": "${MEMORY}",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/uts-ecs-execution-role",
  "taskRoleArn": "${TASK_ROLE_ARN}",
  "containerDefinitions": [
    {
      "name": "${svc}",
      "image": "${image}",
      "portMappings": [{"containerPort": ${PORT}, "protocol": "tcp"}],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/uts/${svc}",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "${svc}"
        }
      },
      "environment": [
        {"name": "CLOUD_PROVIDER", "value": "aws"},
        {"name": "DEPLOYMENT_ENV", "value": "${ENV}"},
        {"name": "AWS_REGION", "value": "${AWS_REGION}"}
      ]
    }
  ]
}
EOF
)

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] aws ecs register-task-definition --region ${AWS_REGION} --cli-input-json <task-def for ${svc}>"
    TASK_DEF_ARN="arn:aws:ecs:${AWS_REGION}:${AWS_ACCOUNT_ID}:task-definition/uts-${svc}:DRY-RUN"
  else
    TASK_DEF_ARN=$(aws ecs register-task-definition \
      --region "${AWS_REGION}" \
      --cli-input-json "${TASK_DEF_JSON}" \
      --query 'taskDefinition.taskDefinitionArn' \
      --output text)
    log_info "Registered task def: ${TASK_DEF_ARN}"

    # Create CW log group if missing
    aws logs create-log-group --log-group-name "/uts/${svc}" --region "${AWS_REGION}" 2>/dev/null || true
  fi

  # Check if service already exists
  SVC_EXISTS=$(aws ecs describe-services \
    --cluster "${ECS_CLUSTER}" \
    --services "${svc}" \
    --region "${AWS_REGION}" \
    --query 'services[?status==`ACTIVE`].serviceName' \
    --output text 2>/dev/null || echo "")

  if [[ -n "$SVC_EXISTS" && "$SVC_EXISTS" != "None" ]]; then
    run_cmd aws ecs update-service \
      --cluster "${ECS_CLUSTER}" \
      --service "${svc}" \
      --task-definition "${TASK_DEF_ARN}" \
      --region "${AWS_REGION}" \
      --output text > /dev/null
    log_info "${svc}: service updated"
  else
    run_cmd aws ecs create-service \
      --cluster "${ECS_CLUSTER}" \
      --service-name "${svc}" \
      --task-definition "${TASK_DEF_ARN}" \
      --desired-count 1 \
      --launch-type FARGATE \
      --network-configuration 'awsvpcConfiguration={subnets=[],securityGroups=[],assignPublicIp=ENABLED}' \
      --region "${AWS_REGION}" \
      --output text > /dev/null
    log_info "${svc}: service created"
  fi
  log_ok "${svc} deployed"
done

# ---------------------------------------------------------------------------
# Step 3: Deploy App Runner services
# ---------------------------------------------------------------------------
APPRUNNER_SERVICES=(alerting-service deployment-api position-balance-monitor-service)
log_section "Step 3 — App Runner deployments"

for svc in "${APPRUNNER_SERVICES[@]}"; do
  tag="${SERVICE_TAG[$svc]}"
  image="${ECR_BASE}/${svc}:${tag}"
  manifest="${MANIFEST_DIR}/${svc}.yaml"

  log_info "Deploying ${svc} (${image})"

  if [[ ! -f "$manifest" ]]; then
    log_skip "Manifest not found: ${manifest} — skipping ${svc}"
    continue
  fi

  if command -v yq &>/dev/null; then
    PORT=$(yq '.port // 8000' "$manifest")
    CPU=$(yq '.cpu // "1 vCPU"' "$manifest")
    MEMORY=$(yq '.memory // "2 GB"' "$manifest")
  else
    PORT=8000; CPU="1 vCPU"; MEMORY="2 GB"
  fi

  # Check if App Runner service already exists
  EXISTING_ARN=$(aws apprunner list-services \
    --region "${AWS_REGION}" \
    --query "ServiceSummaryList[?ServiceName=='uts-${svc}'].ServiceArn | [0]" \
    --output text 2>/dev/null || echo "")

  AR_CONFIG=$(cat <<EOF
{
  "ServiceName": "uts-${svc}",
  "SourceConfiguration": {
    "ImageRepository": {
      "ImageIdentifier": "${image}",
      "ImageConfiguration": {
        "Port": "${PORT}",
        "RuntimeEnvironmentVariables": {
          "CLOUD_PROVIDER": "aws",
          "DEPLOYMENT_ENV": "${ENV}",
          "AWS_REGION": "${AWS_REGION}"
        }
      },
      "ImageRepositoryType": "ECR"
    },
    "AutoDeploymentsEnabled": false
  },
  "InstanceConfiguration": {
    "Cpu": "${CPU}",
    "Memory": "${MEMORY}"
  }
}
EOF
)

  if [[ -n "$EXISTING_ARN" && "$EXISTING_ARN" != "None" ]]; then
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "[DRY-RUN] aws apprunner update-service --region ${AWS_REGION} --service-arn <arn> --source-configuration <...>"
    else
      aws apprunner update-service \
        --region "${AWS_REGION}" \
        --service-arn "${EXISTING_ARN}" \
        --source-configuration "{\"ImageRepository\":{\"ImageIdentifier\":\"${image}\",\"ImageConfiguration\":{\"Port\":\"${PORT}\"},\"ImageRepositoryType\":\"ECR\"}}" \
        --output text > /dev/null
      log_info "${svc}: App Runner service updated"
    fi
  else
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "[DRY-RUN] aws apprunner create-service --region ${AWS_REGION} --cli-input-json <config for ${svc}>"
    else
      APP_RUNNER_ARN=$(aws apprunner create-service \
        --region "${AWS_REGION}" \
        --cli-input-json "${AR_CONFIG}" \
        --query 'Service.ServiceArn' \
        --output text)
      log_info "${svc}: App Runner service created: ${APP_RUNNER_ARN}"
    fi
  fi
  log_ok "${svc} deployed"
done

# ---------------------------------------------------------------------------
# Step 4: Wait for Fargate services stable + smoke /health
# ---------------------------------------------------------------------------
log_section "Step 4 — Wait for services stable + smoke /health"

if [[ "$DRY_RUN" == "true" ]]; then
  log_skip "DRY-RUN: skipping wait + smoke"
else
  echo "Waiting for ECS services to reach steady state (timeout: 10 min)..."
  aws ecs wait services-stable \
    --cluster "${ECS_CLUSTER}" \
    --services "${FARGATE_SERVICES[@]}" \
    --region "${AWS_REGION}" \
    --cli-read-timeout 600 || log_fail "Fargate services did not stabilize in 10 min — check ECS console"

  # Smoke /health via ECS exec or ALB endpoint
  for svc in "${FARGATE_SERVICES[@]}"; do
    TASK_ARN=$(aws ecs list-tasks \
      --cluster "${ECS_CLUSTER}" \
      --service-name "${svc}" \
      --region "${AWS_REGION}" \
      --query 'taskArns[0]' \
      --output text 2>/dev/null || echo "")

    if [[ -n "$TASK_ARN" && "$TASK_ARN" != "None" ]]; then
      TASK_IP=$(aws ecs describe-tasks \
        --cluster "${ECS_CLUSTER}" \
        --tasks "${TASK_ARN}" \
        --region "${AWS_REGION}" \
        --query 'tasks[0].attachments[0].details[?name==`privateIPv4Address`].value | [0]' \
        --output text 2>/dev/null || echo "")

      if [[ -n "$TASK_IP" && "$TASK_IP" != "None" ]]; then
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://${TASK_IP}:8000/health" --connect-timeout 5 || echo "000")
        if [[ "$HTTP_STATUS" == "200" ]]; then
          log_ok "${svc} /health → ${HTTP_STATUS}"
        else
          log_fail "${svc} /health → ${HTTP_STATUS} (IP: ${TASK_IP})"
        fi
      else
        log_skip "${svc}: could not resolve task IP — check VPC/subnet config"
      fi
    else
      log_skip "${svc}: no running tasks found"
    fi
  done

  # App Runner: wait for RUNNING status
  for svc in "${APPRUNNER_SERVICES[@]}"; do
    AR_STATUS=$(aws apprunner describe-service \
      --region "${AWS_REGION}" \
      --service-arn "$(aws apprunner list-services \
        --region "${AWS_REGION}" \
        --query "ServiceSummaryList[?ServiceName=='uts-${svc}'].ServiceArn | [0]" \
        --output text 2>/dev/null)" \
      --query 'Service.Status' \
      --output text 2>/dev/null || echo "UNKNOWN")

    if [[ "$AR_STATUS" == "RUNNING" ]]; then
      AR_URL=$(aws apprunner describe-service \
        --region "${AWS_REGION}" \
        --service-arn "$(aws apprunner list-services \
          --region "${AWS_REGION}" \
          --query "ServiceSummaryList[?ServiceName=='uts-${svc}'].ServiceArn | [0]" \
          --output text)" \
        --query 'Service.ServiceUrl' \
        --output text 2>/dev/null || echo "")

      HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${AR_URL}/health" --connect-timeout 10 || echo "000")
      if [[ "$HTTP_STATUS" == "200" ]]; then
        log_ok "${svc} /health → ${HTTP_STATUS} (${AR_URL})"
      else
        log_fail "${svc} /health → ${HTTP_STATUS} (${AR_URL})"
      fi
    else
      log_fail "${svc} App Runner status: ${AR_STATUS}"
    fi
  done
fi

log_section "Summary"
log_ok "Phase 6 deployment script complete (dry_run=${DRY_RUN})"
echo ""
echo "Next steps:"
echo "  1. Run without --dry-run to apply deployments"
echo "  2. Monitor: aws ecs describe-services --cluster ${ECS_CLUSTER} --region ${AWS_REGION}"
echo "  3. Logs: aws logs tail /uts/<service> --follow --region ${AWS_REGION}"
