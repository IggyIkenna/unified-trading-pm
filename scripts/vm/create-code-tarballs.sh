#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Create code tarballs and upload to GCS or S3 for VM tarball deployments.
#
# SSOT: codex/05-infrastructure/vm-tarball-deployment.md
#
# Cloud flag (NEW in this revision — --cloud aws support):
#   --cloud gcp  Upload to gs://deployment-scripts-{PROJECT}/code/<repo>-code.tar.gz (default)
#   --cloud aws  Upload to s3://uts-prod-deployment-state/code/<repo>-code.tar.gz
#
# Usage:
#   bash create-code-tarballs.sh [--cloud gcp|aws] [--dry-run]
#   bash create-code-tarballs.sh [--cloud gcp|aws] --all
#   bash create-code-tarballs.sh [--cloud gcp|aws] --asset-group CEFI|DEFI|TRADFI|SPORTS|PREDICTION
#   bash create-code-tarballs.sh [--cloud gcp|aws] --ml-training
#   bash create-code-tarballs.sh [--cloud gcp|aws] --include <repo> [--include <repo> ...]
#
# Scope flags (mutually compatible, additive):
#   (none)              CORE only — UAC / UTL / MTDS / deployment-service
#   --all               CORE + all service repos
#   --asset-group AG    CORE + that asset-group's pipeline repos
#   --ml-training       CORE + ml-service + features-* consumers
#   --include <repo>    CORE + the named repo (repeatable)
#
# Exclusions: .git, .venv*, node_modules, __pycache__, coverage, .terraform,
#             *.pyc, *.pyo, dist, build, .eggs, *.egg-info
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }
log_ok()      { echo -e "${GREEN}✅ $1${NC}"; }
log_skip()    { echo -e "${YELLOW}⏭  $1${NC}"; }
log_fail()    { echo -e "${RED}❌ $1${NC}"; }

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
CLOUD="${CLOUD_PROVIDER:-gcp}"
DRY_RUN=false
SCOPE_ALL=false
SCOPE_ML=false
ASSET_GROUP=""
EXTRA_REPOS=()

# GCS config (used when --cloud gcp)
PROJECT="${CLOUD_PROJECT:-central-element-323112}"
GCS_CODE_BUCKET="deployment-scripts-${PROJECT}"
GCS_CODE_PREFIX="code"
GCS_VM_PREFIX="vm"

# S3 config (used when --cloud aws)
S3_BUCKET="${S3_DEPLOYMENT_BUCKET:-uts-prod-deployment-state}"
S3_CODE_PREFIX="code"
AWS_REGION="${AWS_REGION:-us-east-1}"

# ---------------------------------------------------------------------------
# Category-to-repo mappings (mirrors deployment-service create-code-tarballs.sh)
# ---------------------------------------------------------------------------
CEFI_REPOS=(instruments-service market-tick-data-service)
DEFI_REPOS=(instruments-service market-tick-data-service)
TRADFI_REPOS=(instruments-service market-tick-data-service)
SPORTS_REPOS=(instruments-service market-tick-data-service)
PREDICTION_REPOS=(market-tick-data-service)
ML_REPOS=(ml-service features-service)

# CORE repos — always included
CORE_REPOS=(
  "unified-api-contracts"
  "unified-trading-library"
  "market-tick-data-service"  # alias: mtds-code.tar.gz
  "deployment-service"
)

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cloud)
      CLOUD="${2:?--cloud requires gcp or aws}"; shift 2 ;;
    --dry-run)
      DRY_RUN=true; shift ;;
    --all)
      SCOPE_ALL=true; shift ;;
    --ml-training)
      SCOPE_ML=true; shift ;;
    --asset-group)
      ASSET_GROUP="${2:?--asset-group requires a value}"; shift 2 ;;
    --include)
      EXTRA_REPOS+=("${2:?--include requires a repo name}"); shift 2 ;;
    *)
      echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

CLOUD="${CLOUD,,}"  # lowercase
if [[ "$CLOUD" != "gcp" && "$CLOUD" != "aws" ]]; then
  echo "ERROR: --cloud must be 'gcp' or 'aws', got '${CLOUD}'" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Collect repos to tarball
# ---------------------------------------------------------------------------
declare -A SEEN_REPOS
REPOS_TO_TAR=()

add_repo() {
  local repo="$1"
  if [[ -z "${SEEN_REPOS[$repo]+x}" ]]; then
    SEEN_REPOS[$repo]=1
    REPOS_TO_TAR+=("$repo")
  fi
}

# CORE always
for r in "${CORE_REPOS[@]}"; do add_repo "$r"; done

if [[ "$SCOPE_ALL" == "true" ]]; then
  for cat in CEFI_REPOS DEFI_REPOS TRADFI_REPOS SPORTS_REPOS PREDICTION_REPOS ML_REPOS; do
    eval "repos=(\"\${${cat}[@]}\")"
    for r in "${repos[@]}"; do add_repo "$r"; done
  done
fi

if [[ -n "$ASSET_GROUP" ]]; then
  AG_UPPER="${ASSET_GROUP^^}"
  AG_VAR="${AG_UPPER}_REPOS"
  if [[ -z "${!AG_VAR+x}" ]]; then
    echo "ERROR: Unknown --asset-group '${ASSET_GROUP}'. Valid: CEFI DEFI TRADFI SPORTS PREDICTION" >&2
    exit 1
  fi
  eval "ag_repos=(\"\${${AG_VAR}[@]}\")"
  for r in "${ag_repos[@]}"; do add_repo "$r"; done
fi

if [[ "$SCOPE_ML" == "true" ]]; then
  for r in "${ML_REPOS[@]}"; do add_repo "$r"; done
fi

for r in "${EXTRA_REPOS[@]}"; do add_repo "$r"; done

# ---------------------------------------------------------------------------
# Tar exclusion args
# ---------------------------------------------------------------------------
TAR_EXCLUDES=(
  --exclude=".git"
  --exclude=".venv"
  --exclude=".venv*"
  --exclude="node_modules"
  --exclude="__pycache__"
  --exclude="*.pyc"
  --exclude="*.pyo"
  --exclude="coverage"
  --exclude=".coverage"
  --exclude=".terraform"
  --exclude="dist"
  --exclude="build"
  --exclude=".eggs"
  --exclude="*.egg-info"
)

# ---------------------------------------------------------------------------
# Upload helpers
# ---------------------------------------------------------------------------
upload_gcs() {
  local src="$1"
  local dst="$2"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] gsutil cp ${src} ${dst}"
  else
    gsutil cp "${src}" "${dst}"
  fi
}

upload_s3() {
  local src="$1"
  local dst="$2"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] aws s3 cp ${src} ${dst} --region ${AWS_REGION}"
  else
    aws s3 cp "${src}" "${dst}" --region "${AWS_REGION}"
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

log_section "create-code-tarballs — cloud=${CLOUD} dry_run=${DRY_RUN} repos=${#REPOS_TO_TAR[@]}"
echo "Repos: ${REPOS_TO_TAR[*]}"
if [[ "$CLOUD" == "gcp" ]]; then
  echo "Destination: gs://${GCS_CODE_BUCKET}/${GCS_CODE_PREFIX}/<repo>-code.tar.gz"
else
  echo "Destination: s3://${S3_BUCKET}/${S3_CODE_PREFIX}/<repo>-code.tar.gz"
fi

ERRORS=0

for REPO in "${REPOS_TO_TAR[@]}"; do
  REPO_DIR="${WS_ROOT}/${REPO}"
  if [[ ! -d "$REPO_DIR" ]]; then
    log_skip "Skipping ${REPO} — directory not found at ${REPO_DIR}"
    continue
  fi

  # market-tick-data-service ships as mtds-code.tar.gz for historical compat
  if [[ "$REPO" == "market-tick-data-service" ]]; then
    TARBALL_NAME="mtds-code.tar.gz"
  else
    TARBALL_NAME="${REPO}-code.tar.gz"
  fi

  TARBALL_PATH="${TMP_DIR}/${TARBALL_NAME}"

  echo -n "  Tarring ${REPO}... "
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] tar czf ${TARBALL_PATH} -C ${WS_ROOT} ${REPO} <exclusions>"
  else
    tar czf "${TARBALL_PATH}" -C "${WS_ROOT}" "${TAR_EXCLUDES[@]}" "${REPO}" 2>/dev/null
    BYTES="$(wc -c < "$TARBALL_PATH")"
    echo "${BYTES} bytes → ${TARBALL_NAME}"
  fi

  if [[ "$CLOUD" == "gcp" ]]; then
    DEST="gs://${GCS_CODE_BUCKET}/${GCS_CODE_PREFIX}/${TARBALL_NAME}"
    upload_gcs "${TARBALL_PATH}" "${DEST}" || { log_fail "Upload failed: ${TARBALL_NAME}"; ERRORS=$((ERRORS+1)); continue; }
  else
    DEST="s3://${S3_BUCKET}/${S3_CODE_PREFIX}/${TARBALL_NAME}"
    upload_s3 "${TARBALL_PATH}" "${DEST}" || { log_fail "Upload failed: ${TARBALL_NAME}"; ERRORS=$((ERRORS+1)); continue; }
  fi
  log_ok "Uploaded ${TARBALL_NAME}"
done

# For GCS: also re-upload setup-data-pipeline-vm.sh so launchers fetch the latest boot script
if [[ "$CLOUD" == "gcp" ]]; then
  SETUP_SCRIPT="${WS_ROOT}/deployment-service/scripts/vm/setup-data-pipeline-vm.sh"
  if [[ -f "$SETUP_SCRIPT" ]]; then
    log_section "Re-uploading setup-data-pipeline-vm.sh"
    DEST="gs://${GCS_CODE_BUCKET}/${GCS_VM_PREFIX}/setup-data-pipeline-vm.sh"
    upload_gcs "${SETUP_SCRIPT}" "${DEST}" || { log_fail "Failed to upload setup script"; ERRORS=$((ERRORS+1)); }
    log_ok "setup-data-pipeline-vm.sh uploaded"
  else
    log_skip "setup-data-pipeline-vm.sh not found — skipping re-upload"
  fi
fi

log_section "Summary"
if [[ "$ERRORS" -gt 0 ]]; then
  log_fail "Completed with ${ERRORS} error(s) — see above"
  exit 1
fi
if [[ "$DRY_RUN" == "true" ]]; then
  log_skip "DRY-RUN complete — no uploads performed. Re-run without --dry-run to apply."
else
  log_ok "All ${#REPOS_TO_TAR[@]} tarballs uploaded to ${CLOUD^^}"
fi
