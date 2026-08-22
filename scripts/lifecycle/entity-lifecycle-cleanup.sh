#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# entity-lifecycle-cleanup.sh — Manifest reconciliation after entity add/remove.
#
# Wraps instruments-service/scripts/reconcile_manifest_after_entity_change.py
# for a single entity across one or all asset_groups in dry-run mode (default)
# or real write mode.
#
# Outputs audit CSVs to:
#   unified-trading-pm/audits/entity_lifecycle/by_date/day=YYYY-MM-DD/*.csv
#
# Usage:
#   bash scripts/lifecycle/entity-lifecycle-cleanup.sh \
#       --mode remove \
#       --entity-type venue \
#       --entity-key OLD_VENUE \
#       [--asset-group cefi|defi|tradfi|sports|prediction]  # default: all
#       [--no-dry-run]
#       [--cloud gcp|aws]                                   # default: gcp
#
# Example (dry-run across all asset_groups):
#   bash scripts/lifecycle/entity-lifecycle-cleanup.sh \
#       --mode remove --entity-type venue --entity-key REMOVED_VENUE
#
# Attach all CSV output paths to your PR description per the entity-lifecycle
# HARD RULE (infrastructure_master.md "Manifest cleanup HARD RULE" section).
#
# NOTE: --mode add is BLOCKED-ON writegate Phase 3.D.5 Wave 3 v2 enumerator.
#       The underlying Python script will raise NotImplementedError until that
#       dependency ships.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
IS_REPO="${WORKSPACE_ROOT}/../.tabs/7/instruments-service"

if [[ ! -d "${IS_REPO}" ]]; then
    # Fallback: try relative to workspace root peer directory.
    IS_REPO="${WORKSPACE_ROOT%/unified-trading-pm}/instruments-service"
fi

if [[ ! -f "${IS_REPO}/scripts/reconcile_manifest_after_entity_change.py" ]]; then
    echo "ERROR: Cannot find reconcile_manifest_after_entity_change.py" >&2
    echo "       Expected at: ${IS_REPO}/scripts/reconcile_manifest_after_entity_change.py" >&2
    exit 1
fi

PYTHON="${IS_REPO}/.venv/bin/python"
if [[ ! -x "${PYTHON}" ]]; then
    echo "ERROR: instruments-service .venv not found at ${PYTHON}" >&2
    echo "       Run: cd ${IS_REPO} && uv venv .venv && uv pip install -e ." >&2
    exit 1
fi

# Parse args.
MODE=""
ENTITY_TYPE=""
ENTITY_KEY=""
ASSET_GROUP_FILTER=""
DRY_RUN_FLAG="--dry-run"
CLOUD="gcp"
OUTPUT_CSV_ARG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)          MODE="$2";             shift 2 ;;
        --entity-type)   ENTITY_TYPE="$2";      shift 2 ;;
        --entity-key)    ENTITY_KEY="$2";        shift 2 ;;
        --asset-group)   ASSET_GROUP_FILTER="$2"; shift 2 ;;
        --no-dry-run)    DRY_RUN_FLAG="--no-dry-run"; shift ;;
        --dry-run)       DRY_RUN_FLAG="--dry-run"; shift ;;
        --cloud)         CLOUD="$2";             shift 2 ;;
        --output-csv)    OUTPUT_CSV_ARG="--output-csv $2"; shift 2 ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "${MODE}" || -z "${ENTITY_TYPE}" || -z "${ENTITY_KEY}" ]]; then
    echo "Usage: $0 --mode remove|add --entity-type <col> --entity-key <val> [opts]" >&2
    exit 1
fi

ALL_ASSET_GROUPS=("cefi" "defi" "tradfi" "sports" "prediction")
if [[ -n "${ASSET_GROUP_FILTER}" ]]; then
    TARGET_GROUPS=("${ASSET_GROUP_FILTER}")
else
    TARGET_GROUPS=("${ALL_ASSET_GROUPS[@]}")
fi

echo "=== entity-lifecycle-cleanup ==="
echo "  mode:        ${MODE}"
echo "  entity-type: ${ENTITY_TYPE}"
echo "  entity-key:  ${ENTITY_KEY}"
echo "  asset-groups: ${TARGET_GROUPS[*]}"
echo "  dry-run:     ${DRY_RUN_FLAG}"
echo "  cloud:       ${CLOUD}"
echo ""

FAILED=()
CSV_PATHS=()

for AG in "${TARGET_GROUPS[@]}"; do
    echo "--- ${AG} ---"
    # Capture the output to extract CSV path from log.
    LOG_FILE="$(mktemp)"
    set +e
    "${PYTHON}" \
        "${IS_REPO}/scripts/reconcile_manifest_after_entity_change.py" \
        --mode "${MODE}" \
        --asset-group "${AG}" \
        --entity-type "${ENTITY_TYPE}" \
        --entity-key "${ENTITY_KEY}" \
        "${DRY_RUN_FLAG}" \
        --cloud "${CLOUD}" \
        ${OUTPUT_CSV_ARG} \
        2>&1 | tee "${LOG_FILE}"
    EXIT_CODE=$?
    set -e

    if [[ ${EXIT_CODE} -ne 0 ]]; then
        FAILED+=("${AG}")
        echo "  [FAILED] ${AG} exited ${EXIT_CODE}" >&2
    else
        CSV_LINE="$(grep -o 'Audit CSV: .*' "${LOG_FILE}" | head -1 || true)"
        if [[ -n "${CSV_LINE}" ]]; then
            CSV_PATH="${CSV_LINE#Audit CSV: }"
            CSV_PATHS+=("${CSV_PATH}")
        fi
    fi
    rm -f "${LOG_FILE}"
    echo ""
done

echo "=== Summary ==="
if [[ ${#CSV_PATHS[@]} -gt 0 ]]; then
    echo "Audit CSVs written:"
    for P in "${CSV_PATHS[@]}"; do
        echo "  ${P}"
    done
    echo ""
    echo "ATTACH these CSV paths to your PR description (entity-lifecycle HARD RULE)."
    echo "Or include [entity-skip-cleanup] + operator reason in the commit body."
fi

if [[ ${#FAILED[@]} -gt 0 ]]; then
    echo "FAILED asset_groups: ${FAILED[*]}" >&2
    exit 1
fi

echo "Done."
