#!/usr/bin/env bash
# regen-catalogue.sh — Regenerate the strategy catalogue artefacts on GCS.
#
# Runs the three UAC enumeration scripts and uploads to
# gs://strategy-store-cefi-central-element-323112/catalogue/{file}.
#
# Usage:
#   bash unified-trading-pm/scripts/dev/regen-catalogue.sh           # all three
#   bash unified-trading-pm/scripts/dev/regen-catalogue.sh --stub    # skip slow parquet read
#
# Flags:
#   --stub        Use the stub instruments resolver (venue-only) instead of
#                 the slow real parquet read. Useful for fast local iteration.
#   --skip-upload Print to stdout instead of uploading to GCS.
#
# Outputs (on success):
#   gs://strategy-store-cefi-central-element-323112/catalogue/envelope.md
#   gs://strategy-store-cefi-central-element-323112/catalogue/envelope.json
#   gs://strategy-store-cefi-central-element-323112/catalogue/strategy_instruments.json
#   gs://strategy-store-cefi-central-element-323112/catalogue/availability.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
UAC_DIR="${WORKSPACE_ROOT}/unified-api-contracts"
VENV_BIN="${WORKSPACE_ROOT}/.venv-workspace/bin"

USE_STUB=false
SKIP_UPLOAD=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stub) USE_STUB=true; shift ;;
    --skip-upload) SKIP_UPLOAD=true; shift ;;
    *) echo "Unknown flag: $1"; exit 2 ;;
  esac
done

if [[ ! -x "${VENV_BIN}/python" ]]; then
  echo "ERROR: workspace venv missing at ${VENV_BIN}/python"
  echo "Run: python -m venv ${WORKSPACE_ROOT}/.venv-workspace"
  exit 1
fi

cd "${UAC_DIR}"

UPLOAD_FLAG="--upload"
if "${SKIP_UPLOAD}"; then
  UPLOAD_FLAG=""
fi

echo "==> Envelope (markdown + JSON)"
"${VENV_BIN}/python" scripts/enumerate_envelope.py ${UPLOAD_FLAG}

echo ""
echo "==> Availability"
"${VENV_BIN}/python" scripts/enumerate_availability.py ${UPLOAD_FLAG}

echo ""
INSTR_FLAG=""
if ! "${USE_STUB}"; then
  INSTR_FLAG="--with-real-instruments"
  echo "==> Strategy instruments (REAL parquet read — slower, ~5 min)"
else
  echo "==> Strategy instruments (stub: venue-only)"
fi
"${VENV_BIN}/python" scripts/enumerate_strategy_instruments.py ${INSTR_FLAG} ${UPLOAD_FLAG}

echo ""
echo "Catalogue regeneration complete."
