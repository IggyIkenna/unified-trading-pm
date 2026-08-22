#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# check-data-completeness.sh — Daily data completeness check wrapper.
#
# Delegates to the Python implementation at scripts/validation/check_data_completeness.py.
# Intended to be invoked by Cloud Scheduler daily at 08:00 UTC.
#
# Usage:
#   bash check-data-completeness.sh                  # auto-detect GCS or mock
#   bash check-data-completeness.sh --mock           # force mock mode (CI/dev)
#   bash check-data-completeness.sh --date 2026-03-09
#   bash check-data-completeness.sh --output /tmp/report.md
#
# Exit codes:
#   0 -- all sources passed coverage threshold
#   1 -- one or more sources failed coverage threshold
#   2 -- unexpected error (missing Python, missing script, etc.)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON_SCRIPT="${REPO_ROOT}/scripts/validation/check_data_completeness.py"
REPORTS_DIR="${REPO_ROOT}/reports"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log_info() {
    echo "[INFO]  $(date -u '+%Y-%m-%dT%H:%M:%SZ')  $*" >&2
}

log_error() {
    echo "[ERROR] $(date -u '+%Y-%m-%dT%H:%M:%SZ')  $*" >&2
}

die() {
    log_error "$*"
    exit 2
}

# ---------------------------------------------------------------------------
# Validate prerequisites
# ---------------------------------------------------------------------------

[[ -f "${PYTHON_SCRIPT}" ]] || die "Python script not found: ${PYTHON_SCRIPT}"

# Prefer workspace venv Python; fall back to system Python 3.
if [[ -x "${REPO_ROOT}/../.venv-workspace/bin/python" ]]; then
    PYTHON="${REPO_ROOT}/../.venv-workspace/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="$(command -v python3)"
else
    die "No suitable Python interpreter found."
fi

log_info "Python: ${PYTHON} ($(${PYTHON} --version 2>&1))"
log_info "Script: ${PYTHON_SCRIPT}"

# ---------------------------------------------------------------------------
# Resolve output path (default: reports/data_completeness_YYYY-MM-DD.md)
# ---------------------------------------------------------------------------

# Yesterday in UTC -- matches the check_data_completeness.py default.
if [[ "$(uname)" == "Darwin" ]]; then
    DATE_YESTERDAY="$(date -u -v-1d '+%Y-%m-%d')"
else
    DATE_YESTERDAY="$(date -u -d 'yesterday' '+%Y-%m-%d')"
fi

OUTPUT_DEFAULT="${REPORTS_DIR}/data_completeness_${DATE_YESTERDAY}.md"

# Parse args -- forward everything to the Python script but also track --output
# so we can create the parent directory before invoking it.
ARGS=()
OUTPUT_PATH="${OUTPUT_DEFAULT}"
DATE_ARG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output)
            OUTPUT_PATH="$2"
            ARGS+=("--output" "$2")
            shift 2
            ;;
        --date)
            DATE_ARG="$2"
            ARGS+=("--date" "$2")
            shift 2
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

# Derive the expected report filename when --date was supplied but not --output.
if [[ -n "${DATE_ARG}" && "${OUTPUT_PATH}" == "${OUTPUT_DEFAULT}" ]]; then
    OUTPUT_PATH="${REPORTS_DIR}/data_completeness_${DATE_ARG}.md"
    ARGS+=("--output" "${OUTPUT_PATH}")
elif [[ "${OUTPUT_PATH}" == "${OUTPUT_DEFAULT}" ]]; then
    ARGS+=("--output" "${OUTPUT_PATH}")
fi

mkdir -p "$(dirname "${OUTPUT_PATH}")"

# ---------------------------------------------------------------------------
# Run completeness check
# ---------------------------------------------------------------------------

log_info "Starting daily data completeness check (date=${DATE_ARG:-${DATE_YESTERDAY}})"
log_info "Report path: ${OUTPUT_PATH}"

set +e
"${PYTHON}" "${PYTHON_SCRIPT}" "${ARGS[@]}"
EXIT_CODE=$?
set -e

# ---------------------------------------------------------------------------
# Summarise result
# ---------------------------------------------------------------------------

if [[ ${EXIT_CODE} -eq 0 ]]; then
    log_info "Completeness check PASSED -- all sources above threshold."
elif [[ ${EXIT_CODE} -eq 1 ]]; then
    log_error "Completeness check FAILED -- one or more sources below coverage threshold."
    log_error "See report: ${OUTPUT_PATH}"
else
    die "Completeness check exited with unexpected code ${EXIT_CODE}."
fi

exit ${EXIT_CODE}
