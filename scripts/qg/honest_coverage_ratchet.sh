#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# QG: honest-coverage-ratchet
# Fail QG if any (data_type) coverage ratio regressed by >0.5pp vs yesterday's snapshot.
# Snapshots stored at: gs://<bucket>/_index/snapshots/honest_coverage/<date>.json
#
# Usage: bash scripts/qg/honest_coverage_ratchet.sh <service_name> <bucket_name> [asset_group]
# Returns: 0 (pass), 1 (regression), 2 (no prior snapshot — first run, pass)
#
# In local dev (CLOUD_MOCK_MODE=true), skips with exit 0.
# In CI, requires GCS access via ADC.
#
# owner: slot-2  cadence: per-service QG (post-manifest write)  verifier: quality-gates.sh
# last_executed: 2026-05-20

set -euo pipefail

SERVICE_NAME="${1:-}"
BUCKET_NAME="${2:-}"
ASSET_GROUP="${3:-}"

if [[ -z "$SERVICE_NAME" || -z "$BUCKET_NAME" ]]; then
    echo "Usage: $0 <service_name> <bucket_name> [asset_group]" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RATCHET_PY="${SCRIPT_DIR}/honest_coverage_ratchet.py"

# In local mock mode, skip the ratchet (no real GCS data)
if [[ "${CLOUD_MOCK_MODE:-false}" == "true" ]]; then
    echo "SKIP (CLOUD_MOCK_MODE=true): honest-coverage-ratchet skipped in local dev mode."
    exit 0
fi

EXTRA_ARGS=()
[[ -n "$ASSET_GROUP" ]] && EXTRA_ARGS+=("--asset-group" "$ASSET_GROUP")

# Use workspace venv if available, otherwise fall through to PATH python3
PYTHON="${WORKSPACE_ROOT:+${WORKSPACE_ROOT}/.venv-workspace/bin/python3}"
PYTHON="${PYTHON:-python3}"
[[ -x "$PYTHON" ]] || PYTHON="python3"

set +e
"$PYTHON" "$RATCHET_PY" \
    --bucket "$BUCKET_NAME" \
    --service "$SERVICE_NAME" \
    --skip-on-no-gcs \
    "${EXTRA_ARGS[@]}"
RC=$?
set -e

if [[ $RC -eq 2 ]]; then
    echo "INFO: first run for $SERVICE_NAME — baseline snapshot saved, no regression check."
    exit 0
fi
exit $RC
