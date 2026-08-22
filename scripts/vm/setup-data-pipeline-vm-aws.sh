#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# setup-data-pipeline-vm-aws.sh — EC2 user-data startup script for data pipeline VMs.
#
# AWS equivalent of deployment-service/scripts/vm/setup-data-pipeline-vm.sh (GCE variant).
# Staged here (unified-trading-pm/scripts/vm/) pending deployment-service clone; cp to
# deployment-service/scripts/vm/ when available and upload to:
#   s3://uts-prod-deployment-state/vm/setup-data-pipeline-vm-aws.sh
#
# ── Launcher usage ─────────────────────────────────────────────────────────────────────────
# EC2 launchers pass a minimal user-data script that fetches + execs this from S3:
#
#   #!/usr/bin/env bash
#   aws s3 cp s3://uts-prod-deployment-state/vm/setup-data-pipeline-vm-aws.sh /tmp/setup.sh
#   bash /tmp/setup.sh
#
# GCE equivalent:
#   --metadata startup-script-url=gs://deployment-scripts-{project}/vm/setup-data-pipeline-vm.sh
#
# ── VM metadata ────────────────────────────────────────────────────────────────────────────
# All VM_* keys are passed as EC2 instance tags by the launcher (read via IMDSv2).
# GCE equivalent: --metadata KEY=VALUE (read from GCE metadata server).
#
# Required tags:
#   VM_TASK                 Workload router key (same values as GCE variant):
#                             cefi-backfill | defi-backfill | tradfi-backfill
#                             mdps-backfill | mtds-forward-poll | features-backfill
#                             canonical-migration | sports-manifest-rescan
#                             manifest-consolidator-poll
#   VM_SERVICE              Service sub-package (e.g. "market_tick_data_service")
#   VM_OPERATION            Service CLI --operation value (e.g. "download")
#   VM_ASSET_GROUP          Uppercase canonical (CEFI|TRADFI|DEFI|SPORTS|PREDICTION)
#   VM_START_DATE           ISO date (e.g. 2022-01-01)
#   VM_END_DATE             ISO date (e.g. 2022-01-31)
#   VM_DATA_TYPES           Semicolon-separated (e.g. "ohlcv_1m;trades")
#   VM_INSTRUMENT_IDS       Semicolon-separated instrument IDs (optional)
#   VM_MIGRATION_CMD        Verbatim Python command for canonical-migration / sports-manifest-rescan
#   VM_SHUTDOWN_ON_COMPLETION  "true" → self-terminate after workload exits (default: true)
#   MANIFEST_PER_VM_SHARDS  "true" → per-VM shard isolation (mandatory for manifest writers)
#
# ── Invariants (per codex/05-infrastructure/vm-tarball-deployment.md) ──────────────────────
#   - Python 3.13 via uv (NOT deadsnakes PPA — stale as of 2026-05-21)
#   - Venv at /home/ubuntu/venv
#   - Tarballs: s3://uts-prod-deployment-state/code/{repo}-code.tar.gz
#   - Logs: s3://uts-prod-deployment-state/vm-logs/{VM_NAME}/run.log (30s upload cadence)
#   - EXIT_STATUS: s3://uts-prod-deployment-state/vm-logs/{VM_NAME}/EXIT_STATUS
#   - Self-terminate via aws ec2 terminate-instances on VM_SHUTDOWN_ON_COMPLETION=true
#   - Region: ap-northeast-1 (mirrors GCE asia-northeast1)
#   - Core tarballs always fetched: unified-api-contracts, unified-trading-library,
#     market-tick-data-service (mtds-code), deployment-service
#   - Per-VM shard isolation: MANIFEST_PER_VM_SHARDS=true + VM_NAME in env
#
# ── AWS S3 bucket SSOT ─────────────────────────────────────────────────────────────────────
#   GCE code bucket:  gs://deployment-scripts-central-element-323112/code/
#   AWS code bucket:  s3://uts-prod-deployment-state/code/
#   GCE vm bucket:    gs://deployment-scripts-central-element-323112/vm/
#   AWS vm bucket:    s3://uts-prod-deployment-state/vm/
#   GCE log bucket:   gs://deployment-scripts-central-element-323112/vm-logs/
#   AWS log bucket:   s3://uts-prod-deployment-state/vm-logs/
set -euo pipefail

# ── Constants ──────────────────────────────────────────────────────────────────────────────
AWS_REGION="ap-northeast-1"
DEPLOYMENT_BUCKET="uts-prod-deployment-state"
VENV_DIR="/home/ubuntu/venv"
WORKSPACE_DIR="/home/ubuntu/workspace"
LOG_DIR="/home/ubuntu/logs"
PYTHON_VERSION="3.13"
LOG_UPLOAD_INTERVAL_SEC=30
HEARTBEAT_INTERVAL_SEC=60
STALL_TIMEOUT_SEC=600

# ── IMDSv2 token (required for EC2 instance tag reads) ────────────────────────────────────
IMDS_TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" || true)
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $IMDS_TOKEN" \
  "http://169.254.169.254/latest/meta-data/instance-id")

_get_tag() {
  local key="$1"
  local default="${2:-}"
  local val
  val=$(curl -s -H "X-aws-ec2-metadata-token: $IMDS_TOKEN" \
    "http://169.254.169.254/latest/meta-data/tags/instance/${key}" 2>/dev/null || true)
  echo "${val:-$default}"
}

# Read all VM_* metadata from instance tags
VM_TASK=$(_get_tag "VM_TASK" "")
VM_SERVICE=$(_get_tag "VM_SERVICE" "")
VM_OPERATION=$(_get_tag "VM_OPERATION" "")
VM_ASSET_GROUP=$(_get_tag "VM_ASSET_GROUP" "")
VM_START_DATE=$(_get_tag "VM_START_DATE" "")
VM_END_DATE=$(_get_tag "VM_END_DATE" "")
VM_DATA_TYPES=$(_get_tag "VM_DATA_TYPES" "")
VM_INSTRUMENT_IDS=$(_get_tag "VM_INSTRUMENT_IDS" "")
VM_MIGRATION_CMD=$(_get_tag "VM_MIGRATION_CMD" "")
VM_BACKFILL_CMD=$(_get_tag "VM_BACKFILL_CMD" "")
VM_SHUTDOWN_ON_COMPLETION=$(_get_tag "VM_SHUTDOWN_ON_COMPLETION" "true")
VM_NAME=$(_get_tag "VM_NAME" "$INSTANCE_ID")
MANIFEST_PER_VM_SHARDS=$(_get_tag "MANIFEST_PER_VM_SHARDS" "true")

# Export for child processes (mirrors GCE metadata env injection)
export VM_TASK VM_SERVICE VM_OPERATION VM_ASSET_GROUP VM_START_DATE VM_END_DATE
export VM_DATA_TYPES VM_INSTRUMENT_IDS VM_MIGRATION_CMD VM_BACKFILL_CMD
export VM_NAME MANIFEST_PER_VM_SHARDS INSTANCE_ID AWS_REGION DEPLOYMENT_BUCKET

# ── Logging helpers ───────────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR"
MAIN_LOG="${LOG_DIR}/backfill.log"
S3_LOG_PREFIX="s3://${DEPLOYMENT_BUCKET}/vm-logs/${VM_NAME}"

_log() { echo "[setup] $(date -u +%FT%T) $*" | tee -a "$MAIN_LOG"; }
_err() { echo "[setup][ERROR] $(date -u +%FT%T) $*" | tee -a "$MAIN_LOG" >&2; }

_upload_log_once() {
  aws s3 cp "$MAIN_LOG" "${S3_LOG_PREFIX}/run.log" \
    --region "$AWS_REGION" --quiet 2>/dev/null || true
}

_background_log_upload() {
  while true; do
    _upload_log_once
    sleep "$LOG_UPLOAD_INTERVAL_SEC"
  done
}

_write_exit_status() {
  local rc="$1"
  echo "[vm-exec] command exited rc=${rc}" > /tmp/EXIT_STATUS
  aws s3 cp /tmp/EXIT_STATUS "${S3_LOG_PREFIX}/EXIT_STATUS" \
    --region "$AWS_REGION" --quiet 2>/dev/null || true
  _upload_log_once
}

_self_terminate() {
  if [[ "$VM_SHUTDOWN_ON_COMPLETION" == "true" ]]; then
    _log "VM_SHUTDOWN_ON_COMPLETION=true — terminating instance $INSTANCE_ID"
    aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION" \
      2>/dev/null || true
  fi
}

# Start background log upload daemon
_background_log_upload &
LOG_UPLOAD_PID=$!
trap 'kill $LOG_UPLOAD_PID 2>/dev/null || true; _upload_log_once; _self_terminate' EXIT

_log "=== EC2 data-pipeline setup starting ==="
_log "instance_id=${INSTANCE_ID} vm_name=${VM_NAME} vm_task=${VM_TASK}"
_log "asset_group=${VM_ASSET_GROUP} operation=${VM_OPERATION}"

# ── System packages ───────────────────────────────────────────────────────────────────────
_log "Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
  build-essential python3.13-dev libssl-dev libffi-dev \
  curl unzip git jq awscli 2>&1 | tee -a "$MAIN_LOG"

# ── Python 3.13 via uv ────────────────────────────────────────────────────────────────────
_log "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh 2>&1 | tee -a "$MAIN_LOG"
export PATH="/root/.cargo/bin:/home/ubuntu/.local/bin:$PATH"

_log "Installing Python ${PYTHON_VERSION} via uv..."
uv python install "$PYTHON_VERSION" 2>&1 | tee -a "$MAIN_LOG"

# ── Download core tarballs from S3 ───────────────────────────────────────────────────────
_log "Downloading core tarballs from s3://${DEPLOYMENT_BUCKET}/code/"
mkdir -p "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"

_fetch_tarball() {
  local repo="$1"
  local tarball="${repo}-code.tar.gz"
  _log "Fetching ${tarball}..."
  aws s3 cp "s3://${DEPLOYMENT_BUCKET}/code/${tarball}" "/tmp/${tarball}" \
    --region "$AWS_REGION" 2>&1 | tee -a "$MAIN_LOG"
  tar -xzf "/tmp/${tarball}" -C "$WORKSPACE_DIR" 2>&1 | tee -a "$MAIN_LOG"
  rm -f "/tmp/${tarball}"
}

# Core tarballs — always fetched (mirrors GCE: UAC + UTL + MTDS + deployment-service)
_fetch_tarball "unified-api-contracts"
_fetch_tarball "unified-trading-library"
_fetch_tarball "mtds-code"          # market-tick-data-service
_fetch_tarball "deployment-service"

# Service-specific tarballs based on VM_SERVICE
_fetch_service_tarball() {
  local service="$1"
  if [[ -n "$service" ]]; then
    _fetch_tarball "$service" 2>/dev/null || _log "WARN: tarball not found for service=$service (optional)"
  fi
}

case "${VM_TASK:-}" in
  cefi-backfill)       _fetch_service_tarball "instruments-service" ;;
  defi-backfill)       _fetch_service_tarball "instruments-service" ;;
  tradfi-backfill)     _fetch_service_tarball "instruments-service" ;;
  mdps-backfill)       _fetch_service_tarball "mdps-service" ;;
  features-backfill)   _fetch_service_tarball "features-service" ;;
  canonical-migration) : ;;  # Uses deployment-service migration scripts
  sports-manifest-rescan) _fetch_service_tarball "instruments-service" ;;
  manifest-consolidator-poll) : ;;  # Core tarballs only
  *)
    _log "WARN: unknown VM_TASK=${VM_TASK}; fetching VM_SERVICE tarball if set"
    _fetch_service_tarball "$VM_SERVICE"
    ;;
esac

# ── Create venv + install ──────────────────────────────────────────────────────────────────
_log "Creating venv at ${VENV_DIR}..."
uv venv --python "$PYTHON_VERSION" "$VENV_DIR" 2>&1 | tee -a "$MAIN_LOG"
export VIRTUAL_ENV="$VENV_DIR"
export PATH="${VENV_DIR}/bin:$PATH"

_log "Installing packages into venv..."
uv pip install --no-deps \
  -e "${WORKSPACE_DIR}/unified-api-contracts" \
  -e "${WORKSPACE_DIR}/unified-trading-library" \
  2>&1 | tee -a "$MAIN_LOG"

# Install market-tick-data-service (aliased as mtds-code)
if [[ -d "${WORKSPACE_DIR}/market-tick-data-service" ]]; then
  uv pip install --no-deps -e "${WORKSPACE_DIR}/market-tick-data-service" 2>&1 | tee -a "$MAIN_LOG"
fi

# Install service-specific package if present
if [[ -n "$VM_SERVICE" ]] && [[ -d "${WORKSPACE_DIR}/${VM_SERVICE/-/_}" ]]; then
  uv pip install --no-deps -e "${WORKSPACE_DIR}/${VM_SERVICE/-/_}" 2>&1 | tee -a "$MAIN_LOG"
fi

# ── Stall watchdog (mirrors GCE vm-exec-with-gcs-tee.sh STALL_TIMEOUT_SEC logic) ─────────
_launch_with_tee() {
  local cmd=("$@")
  local rc=0

  _log "Launching: ${cmd[*]}"

  # Stall watchdog: kills workload if log mtime doesn't advance within STALL_TIMEOUT_SEC
  (
    while true; do
      sleep "$STALL_TIMEOUT_SEC"
      if [[ -f "$MAIN_LOG" ]]; then
        age=$(( $(date +%s) - $(stat -c %Y "$MAIN_LOG") ))
        if (( age >= STALL_TIMEOUT_SEC )); then
          _err "STALL DETECTED: log mtime ${age}s ago — killing workload"
          pkill -f "${cmd[0]}" 2>/dev/null || true
          break
        fi
      fi
    done
  ) &
  WATCHDOG_PID=$!

  "${cmd[@]}" 2>&1 | tee -a "$MAIN_LOG" || rc=$?

  kill "$WATCHDOG_PID" 2>/dev/null || true
  _write_exit_status "$rc"
  return "$rc"
}

# ── VM_TASK routing (mirrors setup-data-pipeline-vm.sh branching) ─────────────────────────
_log "Routing VM_TASK=${VM_TASK}..."

# Build CLI args common to most service invocations
_build_cli_args() {
  local args=()
  [[ -n "$VM_OPERATION" ]] && args+=("--operation" "$VM_OPERATION")
  [[ -n "$VM_ASSET_GROUP" ]] && args+=("--asset-group" "$(echo "$VM_ASSET_GROUP" | tr '[:upper:]' '[:lower:]')")
  [[ -n "$VM_START_DATE" ]] && args+=("--start-date" "$VM_START_DATE")
  [[ -n "$VM_END_DATE" ]] && args+=("--end-date" "$VM_END_DATE")
  [[ -n "$VM_DATA_TYPES" ]] && args+=("--data-types" "${VM_DATA_TYPES//;/ }")
  [[ -n "$VM_INSTRUMENT_IDS" ]] && args+=("--instrument-ids" "${VM_INSTRUMENT_IDS//;/ }")
  echo "${args[@]}"
}

RC=0
case "${VM_TASK:-}" in
  cefi-backfill|defi-backfill|tradfi-backfill)
    read -ra CLI_ARGS <<< "$(_build_cli_args)"
    _launch_with_tee "${VENV_DIR}/bin/python" -m instruments_service "${CLI_ARGS[@]}" || RC=$?
    ;;

  mdps-backfill)
    read -ra CLI_ARGS <<< "$(_build_cli_args)"
    _launch_with_tee "${VENV_DIR}/bin/python" -m mdps_service "${CLI_ARGS[@]}" || RC=$?
    ;;

  mtds-forward-poll)
    read -ra CLI_ARGS <<< "$(_build_cli_args)"
    _launch_with_tee "${VENV_DIR}/bin/python" \
      -m market_tick_data_service --mode live "${CLI_ARGS[@]}" || RC=$?
    ;;

  features-backfill)
    if [[ -n "$VM_BACKFILL_CMD" ]]; then
      # Verbatim command mode (e.g. from launch-ml-vm.sh)
      cd "${WORKSPACE_DIR}"
      _launch_with_tee bash -c "$VM_BACKFILL_CMD" || RC=$?
    else
      read -ra CLI_ARGS <<< "$(_build_cli_args)"
      _launch_with_tee "${VENV_DIR}/bin/python" -m features_service "${CLI_ARGS[@]}" || RC=$?
    fi
    ;;

  canonical-migration)
    if [[ -z "$VM_MIGRATION_CMD" ]]; then
      _err "VM_MIGRATION_CMD required for canonical-migration task"
      RC=1
    else
      cd "${WORKSPACE_DIR}/deployment-service"
      _launch_with_tee bash -c "$VM_MIGRATION_CMD" || RC=$?
    fi
    ;;

  sports-manifest-rescan)
    if [[ -z "$VM_MIGRATION_CMD" ]]; then
      _err "VM_MIGRATION_CMD required for sports-manifest-rescan task"
      RC=1
    else
      cd "${WORKSPACE_DIR}/instruments-service"
      _launch_with_tee bash -c "$VM_MIGRATION_CMD" || RC=$?
    fi
    ;;

  manifest-consolidator-poll)
    POLL_INTERVAL=60
    BUCKETS=$(echo "${VM_DATA_TYPES:-cefi:defi:tradfi:sports:prediction}" | tr ':' ' ')
    PROJECT_SUFFIX="${AWS_REGION}"  # AWS: bucket suffix is region vs GCE project-id
    _log "Starting manifest consolidator poll (interval=${POLL_INTERVAL}s, buckets=${BUCKETS})"
    while true; do
      for bucket_short in $BUCKETS; do
        bucket="instruments-store-${bucket_short}-427895769566"
        _launch_with_tee "${VENV_DIR}/bin/python" \
          -m unified_trading_library.manifest_consolidator \
          --bucket "$bucket" --once 2>&1 | tee -a "$MAIN_LOG" || true
      done
      sleep "$POLL_INTERVAL"
    done
    ;;

  *)
    _err "Unknown VM_TASK=${VM_TASK} — no routing match"
    RC=1
    ;;
esac

_log "=== Workload exited rc=${RC} ==="
exit "$RC"
