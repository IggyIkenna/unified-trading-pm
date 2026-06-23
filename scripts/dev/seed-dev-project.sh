#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# RETIRED 2026-03-13 — Referenced unified-trading-dev as a separate GCP project (never created).
# Synthetic data seeding is superseded by VCR cassette playback (CI) and real batch data (dev).
# Dev infra provisioning: cd deployment-service/terraform/gcp && terraform apply -var="environment=dev"
# See: deployment-service/docs/dev-environment.md
# VCR cassettes: unified-api-contracts/docs/MOCKS_AND_VCR.md
#
# seed-dev-project.sh — Seed the unified-trading GCP dev project with synthetic data.
#
# Usage:
#   seed-dev-project.sh [--quick|--full] [--dry-run]
#
# Requires:
#   - Python 3.13 with numpy, pandas, pyarrow, pyyaml (workspace venv)
#   - gsutil (only for real GCS upload; skipped in --dry-run)
#   - GOOGLE_APPLICATION_CREDENTIALS pointing to unified-trading-dev SA key (for real upload)
#
# Zero live API calls — all data is synthetic.
# Completes in <5 minutes (--quick) or <30 minutes (--full).

set -euo pipefail

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

MODE="quick"
DRY_RUN=""

for arg in "$@"; do
    case "$arg" in
        --quick) MODE="quick" ;;
        --full)  MODE="full"  ;;
        --dry-run) DRY_RUN="--dry-run" ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Usage: $0 [--quick|--full] [--dry-run]" >&2
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEED_DATA_DIR="/tmp/seed_data"
SEED_FEATURES_DIR="/tmp/seed_features"
SEED_MODELS_DIR="/tmp/seed_models"
GCS_PROJECT="${GCS_PROJECT:-unified-trading-dev}"
GCS_TICK_BUCKET="gs://${GCS_PROJECT}-tick-data"
MODEL_VERSION="1"

# Prefer workspace venv Python if available, fall back to system Python
if [[ -f "${SCRIPT_DIR}/../../../.venv-workspace/bin/python" ]]; then
    PYTHON="${SCRIPT_DIR}/../../../.venv-workspace/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    PYTHON="python"
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

step() {
    echo ""
    echo "==> $1"
    echo "    $(date '+%H:%M:%S')"
}

warn() {
    echo "WARNING: $1" >&2
}

die() {
    echo "ERROR: $1" >&2
    exit 1
}

check_python_deps() {
    local missing=()
    for pkg in numpy pandas pyarrow yaml; do
        if ! "$PYTHON" -c "import $pkg" 2>/dev/null; then
            missing+=("$pkg")
        fi
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        die "Missing Python packages: ${missing[*]}. Run: uv pip install numpy pandas pyarrow pyyaml"
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

echo "======================================================="
echo " unified-trading dev project seeder"
echo " mode=${MODE}  dry_run=${DRY_RUN:-false}  project=${GCS_PROJECT}"
echo "======================================================="

START_TS=$(date +%s)

step "Checking Python dependencies"
check_python_deps
echo "    Python: $("$PYTHON" --version)"

step "Generating synthetic data (mode=${MODE})"
"$PYTHON" -m unified_internal_contracts.testing.synthetic \
    --mode "${MODE}" \
    --output "${SEED_DATA_DIR}"

step "Seeding instruments metadata"
"$PYTHON" -m unified_internal_contracts.testing.seed_instruments \
    --output "${SEED_DATA_DIR}" \
    --project "${GCS_PROJECT}" \
    ${DRY_RUN}

step "Validating generated data against UAC schemas"
"$PYTHON" -m unified_internal_contracts.testing.seed_validator \
    "${SEED_DATA_DIR}" \
    --strict \
    --json-report "${SEED_DATA_DIR}/validation_report.json" \
|| die "Schema validation failed — check ${SEED_DATA_DIR}/validation_report.json for details"

step "Pre-computing feature data"
"$PYTHON" -m unified_internal_contracts.testing.seed_features \
    --mode "${MODE}" \
    --input "${SEED_DATA_DIR}" \
    --output "${SEED_FEATURES_DIR}" \
    --project "${GCS_PROJECT}" \
    ${DRY_RUN}

step "Seeding ML model artifacts"
"$PYTHON" -m unified_internal_contracts.testing.seed_ml_artifacts \
    --output "${SEED_MODELS_DIR}" \
    --version "${MODEL_VERSION}" \
    --project "${GCS_PROJECT}" \
    ${DRY_RUN}

# ---------------------------------------------------------------------------
# GCS upload (skipped in dry-run or if gsutil not available)
# ---------------------------------------------------------------------------

if [[ -n "${DRY_RUN}" ]]; then
    step "GCS upload SKIPPED (--dry-run)"
    echo "    Would upload to: ${GCS_TICK_BUCKET}/"
    echo "    Tick data:  ${SEED_DATA_DIR}/tick/"
    echo "    Features:   ${SEED_FEATURES_DIR}/"
    echo "    Models:     gs://${GCS_PROJECT}-models/v${MODEL_VERSION}/"
elif ! command -v gsutil &>/dev/null; then
    warn "gsutil not found — skipping GCS upload. Install Google Cloud SDK to enable upload."
elif [[ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
    warn "GOOGLE_APPLICATION_CREDENTIALS not set — skipping GCS upload."
    warn "Set this to your dev project SA key JSON to enable real GCS upload."
else
    step "Uploading tick data to GCS"
    gsutil -m cp -r "${SEED_DATA_DIR}/tick/" "${GCS_TICK_BUCKET}/"

    step "Uploading OHLCV data to GCS"
    gsutil -m cp -r "${SEED_DATA_DIR}/ohlcv/" "${GCS_TICK_BUCKET}/ohlcv/"

    step "Uploading instruments metadata to GCS"
    gsutil cp "${SEED_DATA_DIR}/instruments.json" "${GCS_TICK_BUCKET}/instruments.json"

    step "Uploading feature data to GCS"
    gsutil -m cp -r "${SEED_FEATURES_DIR}/" "gs://${GCS_PROJECT}-features/seed/"

    step "Uploading ML model artifacts to GCS"
    gsutil -m cp -r "${SEED_MODELS_DIR}/v${MODEL_VERSION}/" \
        "gs://${GCS_PROJECT}-models/v${MODEL_VERSION}/"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

END_TS=$(date +%s)
ELAPSED=$((END_TS - START_TS))

echo ""
echo "======================================================="
echo " Seeding complete"
echo " Elapsed: ${ELAPSED}s"
echo " Local data:     ${SEED_DATA_DIR}/"
echo " Local features: ${SEED_FEATURES_DIR}/"
echo " Local models:   ${SEED_MODELS_DIR}/"
if [[ -f "${SEED_DATA_DIR}/validation_report.json" ]]; then
    echo " Validation:     ${SEED_DATA_DIR}/validation_report.json"
fi
echo "======================================================="
