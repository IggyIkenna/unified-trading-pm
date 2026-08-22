#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# regen-catalogue.sh — Regenerate strategy + instrument catalogue artefacts on GCS.
#
# Runs the UAC enumeration scripts (strategy envelope + availability +
# instruments) AND the new instrument catalogue generator (catalogue plan
# P1.3, 2026-04-29) and uploads to
# gs://strategy-store-cefi-central-element-323112/catalogue/.
#
# Usage:
#   bash unified-trading-pm/scripts/dev/regen-catalogue.sh                 # all
#   bash unified-trading-pm/scripts/dev/regen-catalogue.sh --stub          # fast
#   bash unified-trading-pm/scripts/dev/regen-catalogue.sh --skip-instrument  # skip new catalogue
#
# Flags:
#   --stub             Use the stub instruments resolver (venue-only) instead
#                      of the slow real parquet read. Useful for fast local
#                      iteration.
#   --skip-upload      Print to stdout / write locally instead of uploading.
#   --skip-instrument  Skip the new instrument-catalogue generator (only run
#                      the legacy strategy regen). Defaults to running both.
#
# Outputs (on success):
#   gs://strategy-store-cefi-central-element-323112/catalogue/
#       envelope.md
#       envelope.json
#       strategy_instruments.json
#       availability.json
#       instrument/instrument-catalogue.json   (NEW — catalogue plan P1.3)
#       instrument/instrument-catalogue.md     (NEW)
#       instrument/shard-dynamics.json         (NEW)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
UAC_DIR="${WORKSPACE_ROOT}/unified-api-contracts"
VENV_BIN="${WORKSPACE_ROOT}/.venv-workspace/bin"

USE_STUB=false
SKIP_UPLOAD=false
SKIP_INSTRUMENT=false
PROJECT_ID="${PROJECT_ID:-central-element-323112}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stub) USE_STUB=true; shift ;;
    --skip-upload) SKIP_UPLOAD=true; shift ;;
    --skip-instrument) SKIP_INSTRUMENT=true; shift ;;
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

if ! "${SKIP_INSTRUMENT}"; then
  echo ""
  echo "==> Instrument catalogue (NEW: catalogue plan P1.3 — joins manifest with shard-dynamics SSOT)"
  INSTR_OUT_DIR="$(mktemp -d -t instrument-catalogue.XXXXXX)"
  GEN_FLAGS=("--project-id" "${PROJECT_ID}" "--output-dir" "${INSTR_OUT_DIR}")
  if "${SKIP_UPLOAD}"; then
    GEN_FLAGS+=("--dry-run")
  fi
  "${VENV_BIN}/python" scripts/generate_instrument_catalogue.py "${GEN_FLAGS[@]}"
  echo "Local artefacts written to: ${INSTR_OUT_DIR}"
fi

echo ""
echo "Catalogue regeneration complete."
