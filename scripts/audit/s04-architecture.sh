#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# §4 — Architecture (+ §12 Cloud-Agnostic, which overlaps)
# Checks: cross-service imports, cloud SDK confinement, GCS/boto3 refs, PubSub abstraction.
# Usage: bash unified-trading-pm/scripts/audit/s04-architecture.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$WORKSPACE_ROOT"

echo "=== §4 Architecture + §12 Cloud-Agnostic ==="

# Cross-service T4 imports (services importing sibling services directly)
cross_svc=$(rg \
  'from (execution_service|strategy_service|risk_and_exposure_service|alerting_service|pnl_attribution_service|instruments_service|market_tick_data_service|market_data_processing_service)' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' --glob '!**/test_*' \
  -n 2>/dev/null || true)
pass_if_empty "§4" "no cross-service T4 Python imports" "$cross_svc"

# Direct deployment_service import from other services
dep_svc_import=$(rg 'from deployment_service|import deployment_service' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!deployment-service/**' \
  --glob '!**/tests/**' \
  -n 2>/dev/null || true)
pass_if_empty "§4" "no direct deployment_service imports from other services" "$dep_svc_import"

# google.cloud imports outside UCI + deployment-service
google_cloud=$(rg 'from google\.cloud|import google\.cloud' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!unified-cloud-interface/**' \
  --glob '!deployment-service/**' \
  -n 2>/dev/null || true)
pass_if_empty "§4/§12" "google.cloud confined to UCI + deployment-service" "$google_cloud"

# boto3 imports outside UCI + deployment-service
boto3_hits=$(rg 'import boto3|from boto3' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!unified-cloud-interface/**' \
  --glob '!deployment-service/**' \
  -n 2>/dev/null || true)
pass_if_empty "§4/§12" "boto3 confined to UCI + deployment-service" "$boto3_hits"

# GCS bucket construction outside UCI
gcs_refs=$(rg 'gcs_bucket|gs://' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!unified-cloud-interface/**' \
  -n 2>/dev/null || true)
pass_if_empty "§4/§12" "GCS bucket refs confined to UCI" "$gcs_refs"

# BigQuery outside UCI
bq_refs=$(rg 'bigquery_dataset|BigQueryClient|from google\.cloud import bigquery' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!unified-cloud-interface/**' \
  --glob '!deployment-service/**' \
  -n 2>/dev/null || true)
pass_if_empty "§4/§12" "BigQuery refs confined to UCI" "$bq_refs"

# Direct google-cloud-pubsub (should use get_pubsub_client() from UCI)
direct_pubsub=$(rg 'from google\.cloud import pubsub|google\.cloud\.pubsub' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!unified-cloud-interface/**' \
  -n 2>/dev/null || true)
pass_if_empty "§4/§12" "no direct google-cloud-pubsub (use UCI get_pubsub_client)" "$direct_pubsub"

audit_summary
