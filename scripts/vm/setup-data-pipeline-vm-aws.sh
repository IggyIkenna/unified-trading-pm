#!/usr/bin/env bash
#
# EC2 user-data startup script for AWS data pipeline VMs.
# AWS equivalent of deployment-service/scripts/vm/setup-data-pipeline-vm.sh.
#
# SSOT: codex/05-infrastructure/vm-tarball-deployment.md
#
# Invariants (mirrors GCS variant):
#   1. Python 3.13 via `uv python install 3.13` (NOT deadsnakes PPA).
#   2. C-extension deps (build-essential + python3.13-dev) installed before uv step.
#   3. Venv at /home/ikennaigboaka/venv (all nohup invocations use full venv path).
#   4. VM_TASK (from EC2 instance tags / user-data env) drives workload routing.
#   5. Streaming S3 log + EXIT_STATUS file mirrors GCS variant.
#   6. Self-terminate if VM_SHUTDOWN_ON_COMPLETION=true.
#
# Configuration (set via EC2 user-data environment or instance tags):
#   VM_TASK             Workload identifier: cefi-backfill|defi-backfill|tradfi-backfill|
#                       sports-forward-poll|canonical-migration|features-backfill|...
#   VM_SERVICE          Service CLI entry-point (e.g. market_tick_data_service)
#   VM_OPERATION        Service CLI --operation value (download|process|forward-poll)
#   VM_ASSET_GROUP      Service CLI --asset-group (CEFI|DEFI|TRADFI|SPORTS|PREDICTION)
#   VM_START_DATE       ISO date (e.g. 2022-01-01)
#   VM_END_DATE         ISO date (e.g. 2022-12-31)
#   VM_DATA_TYPES       Semicolon-separated data types (e.g. ohlcv_1m;trades)
#   VM_INSTRUMENT_IDS   Semicolon-separated instrument IDs
#   VM_MIGRATION_CMD    Verbatim command for canonical-migration task
#   VM_SHUTDOWN_ON_COMPLETION  true|false (default true — self-terminate after workload)
#   S3_DEPLOYMENT_BUCKET  S3 bucket for code tarballs (default: uts-prod-deployment-state)
#   AWS_REGION          AWS region (default: us-east-1)
#   CLOUD_PROVIDER      Must be "aws" for this script (enforced at top)
#
# Passed via EC2 launch template / user-data block as #!/usr/bin/env bash with
# export statements, OR injected via instance tags and read below.
#
set -euo pipefail
export CLOUD_PROVIDER=aws

LOG_FILE="/var/log/vm-startup.log"
exec >> "$LOG_FILE" 2>&1

echo "[startup] $(date -u +%Y-%m-%dT%H:%M:%SZ) — setup-data-pipeline-vm-aws.sh START"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
S3_DEPLOYMENT_BUCKET="${S3_DEPLOYMENT_BUCKET:-uts-prod-deployment-state}"
AWS_REGION="${AWS_REGION:-us-east-1}"
UBUNTU_USER="ikennaigboaka"
HOME_DIR="/home/${UBUNTU_USER}"
VENV_DIR="${HOME_DIR}/venv"
WORKSPACE_DIR="${HOME_DIR}/workspace"
LOG_DIR="${HOME_DIR}/logs"
VM_SHUTDOWN_ON_COMPLETION="${VM_SHUTDOWN_ON_COMPLETION:-true}"

# Read EC2 instance identity
INSTANCE_ID="$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/instance-id || echo unknown)"
echo "[startup] instance-id=${INSTANCE_ID}"

# Read VM_TASK from instance tags if not already set (EC2 user-data export or tag-based injection)
if [[ -z "${VM_TASK:-}" ]]; then
  VM_TASK="$(aws ec2 describe-tags \
    --filters "Name=resource-id,Values=${INSTANCE_ID}" "Name=key,Values=VM_TASK" \
    --region "${AWS_REGION}" \
    --query 'Tags[0].Value' --output text 2>/dev/null || echo '')"
fi

VM_TASK="${VM_TASK:-}"
VM_SERVICE="${VM_SERVICE:-}"
VM_OPERATION="${VM_OPERATION:-}"
VM_ASSET_GROUP="${VM_ASSET_GROUP:-}"
VM_START_DATE="${VM_START_DATE:-}"
VM_END_DATE="${VM_END_DATE:-}"
VM_DATA_TYPES="${VM_DATA_TYPES:-ohlcv_1m}"
VM_INSTRUMENT_IDS="${VM_INSTRUMENT_IDS:-}"
VM_MIGRATION_CMD="${VM_MIGRATION_CMD:-}"

echo "[startup] VM_TASK=${VM_TASK} VM_SERVICE=${VM_SERVICE} VM_OPERATION=${VM_OPERATION}"
echo "[startup] VM_ASSET_GROUP=${VM_ASSET_GROUP} VM_START_DATE=${VM_START_DATE} VM_END_DATE=${VM_END_DATE}"

# ---------------------------------------------------------------------------
# S3 log / EXIT_STATUS helpers (mirrors vm-exec-with-gcs-tee.sh behaviour)
# ---------------------------------------------------------------------------
S3_LOG_PREFIX="${S3_DEPLOYMENT_BUCKET}/vm-logs/${INSTANCE_ID}"

_upload_log() {
  aws s3 cp "${LOG_DIR}/backfill.log" "s3://${S3_LOG_PREFIX}/run.log" \
    --region "${AWS_REGION}" --quiet 2>/dev/null || true
}

_write_exit_status() {
  local rc=$1
  echo "[vm-exec] command exited rc=${rc}" > /tmp/EXIT_STATUS
  aws s3 cp /tmp/EXIT_STATUS "s3://${S3_LOG_PREFIX}/EXIT_STATUS" \
    --region "${AWS_REGION}" --quiet 2>/dev/null || true
}

_self_terminate() {
  if [[ "${VM_SHUTDOWN_ON_COMPLETION}" == "true" ]]; then
    echo "[startup] VM_SHUTDOWN_ON_COMPLETION=true — terminating instance ${INSTANCE_ID}"
    aws ec2 terminate-instances --instance-ids "${INSTANCE_ID}" --region "${AWS_REGION}" || true
  fi
}

# ---------------------------------------------------------------------------
# System packages
# ---------------------------------------------------------------------------
echo "[startup] Installing system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq build-essential python3.13-dev curl git unzip

# ---------------------------------------------------------------------------
# uv + Python 3.13
# ---------------------------------------------------------------------------
echo "[startup] Installing uv..."
if ! command -v uv &>/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "[startup] Installing Python 3.13 via uv..."
uv python install 3.13

# ---------------------------------------------------------------------------
# User + workspace setup
# ---------------------------------------------------------------------------
id "${UBUNTU_USER}" &>/dev/null || useradd -m -s /bin/bash "${UBUNTU_USER}"
mkdir -p "${WORKSPACE_DIR}" "${LOG_DIR}"
chown -R "${UBUNTU_USER}:${UBUNTU_USER}" "${HOME_DIR}"

# ---------------------------------------------------------------------------
# Download code tarballs from S3
# ---------------------------------------------------------------------------
echo "[startup] Downloading CORE code tarballs from s3://${S3_DEPLOYMENT_BUCKET}/code/"

CORE_TARBALLS=(
  "unified-api-contracts-code.tar.gz"
  "unified-trading-library-code.tar.gz"
  "mtds-code.tar.gz"
  "deployment-service-code.tar.gz"
)

_download_tarball() {
  local name="$1"
  local dest="${WORKSPACE_DIR}/${name}"
  echo "[startup] Downloading ${name}..."
  aws s3 cp "s3://${S3_DEPLOYMENT_BUCKET}/code/${name}" "${dest}" \
    --region "${AWS_REGION}" || {
    echo "[startup] WARNING: ${name} not found in S3 — skipping"
    return 0
  }
  echo "[startup] Extracting ${name}..."
  tar xzf "${dest}" -C "${WORKSPACE_DIR}" --strip-components=0
  rm -f "${dest}"
}

for tarball in "${CORE_TARBALLS[@]}"; do
  _download_tarball "${tarball}"
done

# Download service-specific tarball if VM_SERVICE is set
if [[ -n "${VM_SERVICE}" ]]; then
  SERVICE_TARBALL="${VM_SERVICE}-code.tar.gz"
  _download_tarball "${SERVICE_TARBALL}"
fi

chown -R "${UBUNTU_USER}:${UBUNTU_USER}" "${WORKSPACE_DIR}"

# ---------------------------------------------------------------------------
# Create virtualenv + install deps
# ---------------------------------------------------------------------------
echo "[startup] Creating venv at ${VENV_DIR}..."
sudo -u "${UBUNTU_USER}" bash -c "
  export PATH=\"\$HOME/.local/bin:\$PATH\"
  uv venv --python 3.13 \"${VENV_DIR}\"
  source \"${VENV_DIR}/bin/activate\"

  # Install CORE packages in order
  for pkg_dir in unified-api-contracts unified-trading-library market-tick-data-service deployment-service; do
    pkg_path=\"${WORKSPACE_DIR}/\${pkg_dir}\"
    if [[ -f \"\${pkg_path}/pyproject.toml\" ]] || [[ -f \"\${pkg_path}/setup.py\" ]]; then
      uv pip install -e \"\${pkg_path}\" --quiet
    fi
  done

  # Install service package if present
  if [[ -n '${VM_SERVICE}' ]]; then
    svc_dir=\"${WORKSPACE_DIR}/${VM_SERVICE}\"
    if [[ -f \"\${svc_dir}/pyproject.toml\" ]] || [[ -f \"\${svc_dir}/setup.py\" ]]; then
      uv pip install -e \"\${svc_dir}\" --quiet
    fi
  fi
"

# ---------------------------------------------------------------------------
# Route to workload CLI via VM_TASK
# ---------------------------------------------------------------------------
TASK_LOG="${LOG_DIR}/backfill.log"
WORKLOAD_RC=0

_run_workload() {
  local cmd="$*"
  echo "[startup] Running workload: ${cmd}"
  # shellcheck disable=SC2086
  sudo -u "${UBUNTU_USER}" bash -c "
    source \"${VENV_DIR}/bin/activate\"
    export CLOUD_PROVIDER=aws
    export AWS_DEFAULT_REGION=${AWS_REGION}
    ${cmd}
  " >> "${TASK_LOG}" 2>&1 || WORKLOAD_RC=$?
}

case "${VM_TASK}" in
  cefi-backfill|defi-backfill|tradfi-backfill|sports-backfill)
    AG="${VM_ASSET_GROUP:-${VM_TASK%%-backfill}}"
    AG_UPPER="${AG^^}"
    _run_workload "python -m ${VM_SERVICE:-market_tick_data_service} \\
      --operation ${VM_OPERATION:-download} \\
      --asset-group ${AG_UPPER} \\
      ${VM_START_DATE:+--start-date ${VM_START_DATE}} \\
      ${VM_END_DATE:+--end-date ${VM_END_DATE}} \\
      ${VM_DATA_TYPES:+--data-types ${VM_DATA_TYPES}} \\
      ${VM_INSTRUMENT_IDS:+--instrument-ids ${VM_INSTRUMENT_IDS}}"
    ;;

  sports-forward-poll|cefi-forward-poll|defi-forward-poll)
    AG="${VM_ASSET_GROUP:-${VM_TASK%%-forward-poll}}"
    AG_UPPER="${AG^^}"
    _run_workload "python -m ${VM_SERVICE:-market_tick_data_service} \\
      --operation forward-poll \\
      --asset-group ${AG_UPPER} \\
      ${VM_DATA_TYPES:+--data-types ${VM_DATA_TYPES}} \\
      ${VM_INSTRUMENT_IDS:+--instrument-ids ${VM_INSTRUMENT_IDS}}"
    ;;

  features-backfill)
    _run_workload "python -m ${VM_SERVICE:-features_service} \\
      --operation ${VM_OPERATION:-backfill} \\
      --asset-group ${VM_ASSET_GROUP:-DEFI} \\
      ${VM_START_DATE:+--start-date ${VM_START_DATE}} \\
      ${VM_END_DATE:+--end-date ${VM_END_DATE}}"
    ;;

  canonical-migration)
    if [[ -z "${VM_MIGRATION_CMD}" ]]; then
      echo "[startup] ERROR: canonical-migration requires VM_MIGRATION_CMD" >&2
      WORKLOAD_RC=1
    else
      _run_workload "${VM_MIGRATION_CMD}"
    fi
    ;;

  *)
    if [[ -n "${VM_MIGRATION_CMD}" ]]; then
      _run_workload "${VM_MIGRATION_CMD}"
    else
      echo "[startup] ERROR: Unknown VM_TASK='${VM_TASK}' and no VM_MIGRATION_CMD set" >&2
      WORKLOAD_RC=1
    fi
    ;;
esac

# ---------------------------------------------------------------------------
# Upload final log + EXIT_STATUS + self-terminate
# ---------------------------------------------------------------------------
_upload_log
_write_exit_status "${WORKLOAD_RC}"

echo "[startup] $(date -u +%Y-%m-%dT%H:%M:%SZ) — setup-data-pipeline-vm-aws.sh DONE rc=${WORKLOAD_RC}"

_self_terminate

exit "${WORKLOAD_RC}"
