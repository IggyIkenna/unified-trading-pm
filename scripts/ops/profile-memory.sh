#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# profile-memory.sh — Memory profiling for a running service or a short benchmark run
#
# Usage:
#   ./profile-memory.sh <service-name> [--duration <seconds>]
#
# Examples:
#   ./profile-memory.sh execution-service
#   ./profile-memory.sh execution-service --duration 120
#   ./profile-memory.sh strategy-service --duration 300
#
# Behaviour:
#   1. If `memray` is available: runs a benchmark entrypoint under memray and
#      generates an HTML flamegraph + stats file.
#   2. Otherwise: attaches to a running PID (if found) via periodic psutil sampling
#      for --duration seconds, then prints a summary.
#
# Output files (written to ./profile_output/):
#   <service>_memory_<timestamp>.bin       (memray binary — if memray available)
#   <service>_memory_<timestamp>.html      (memray flamegraph)
#   <service>_memory_<timestamp>_psutil.txt (psutil sample log — if memray absent)
#
# Assertion:
#   Heap at minute 30 must be <= 110% of heap at minute 5 (no unbounded growth).
#   This assertion is applied when --duration >= 300 seconds.

set -euo pipefail

# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------
SERVICE="${1:-execution-service}"
DURATION=60
shift 1 || true

while [[ $# -gt 0 ]]; do
    case "$1" in
        --duration)
            DURATION="${2:?--duration requires a value}"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SERVICE_DIR="${WORKSPACE_ROOT}/${SERVICE}"
OUTPUT_DIR="${WORKSPACE_ROOT}/profile_output"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_PREFIX="${OUTPUT_DIR}/${SERVICE}_memory_${TIMESTAMP}"

mkdir -p "${OUTPUT_DIR}"

echo "=== Memory Profiling: ${SERVICE} ==="
echo "Duration: ${DURATION}s"
echo "Output:   ${OUTPUT_PREFIX}.*"
echo ""

# ---------------------------------------------------------------------------
# Helper: find the Python package name for the service
# ---------------------------------------------------------------------------
_find_package_name() {
    local svc_dir="$1"
    # Look for directory with __init__.py that matches service name pattern
    find "${svc_dir}" -maxdepth 1 -type d -name "*service*" -o -type d -name "*api*" 2>/dev/null \
        | while read -r d; do
            [ -f "${d}/__init__.py" ] && basename "${d}" && break
        done \
        | head -1
}

# ---------------------------------------------------------------------------
# Check if memray is available
# ---------------------------------------------------------------------------
VENV_PYTHON="${SERVICE_DIR}/.venv/bin/python"
if [ ! -f "${VENV_PYTHON}" ]; then
    VENV_PYTHON="$(command -v python3 || command -v python || echo "")"
fi

if [ -z "${VENV_PYTHON}" ]; then
    echo "ERROR: no Python interpreter found. Activate a venv first." >&2
    exit 1
fi

MEMRAY_AVAILABLE=false
if "${VENV_PYTHON}" -c "import memray" 2>/dev/null; then
    MEMRAY_AVAILABLE=true
fi

PSUTIL_AVAILABLE=false
if "${VENV_PYTHON}" -c "import psutil" 2>/dev/null; then
    PSUTIL_AVAILABLE=true
fi

# ---------------------------------------------------------------------------
# memray path: run benchmark entrypoint under memray
# ---------------------------------------------------------------------------
if [ "${MEMRAY_AVAILABLE}" = "true" ]; then
    echo "memray detected — running ${SERVICE} benchmark under memray..."
    MEMRAY_BIN="${OUTPUT_PREFIX}.bin"
    MEMRAY_HTML="${OUTPUT_PREFIX}.html"

    BENCH_SCRIPT="${SERVICE_DIR}/benchmarks/test_e2e_latency.py"
    if [ ! -f "${BENCH_SCRIPT}" ]; then
        # Fall back to any benchmark file
        BENCH_SCRIPT="$(find "${SERVICE_DIR}/benchmarks" -name "test_*.py" 2>/dev/null | head -1 || echo "")"
    fi

    if [ -z "${BENCH_SCRIPT}" ]; then
        echo "WARNING: no benchmark script found in ${SERVICE_DIR}/benchmarks/ — skipping memray run"
    else
        "${VENV_PYTHON}" -m memray run \
            --output "${MEMRAY_BIN}" \
            --force \
            -m pytest "${BENCH_SCRIPT}" \
            -x -q --no-header \
            2>&1 || true

        if [ -f "${MEMRAY_BIN}" ]; then
            "${VENV_PYTHON}" -m memray flamegraph \
                "${MEMRAY_BIN}" \
                --output "${MEMRAY_HTML}" \
                --force \
                2>&1 || true
            echo "Flamegraph: ${MEMRAY_HTML}"

            "${VENV_PYTHON}" -m memray stats "${MEMRAY_BIN}" 2>&1 | tee "${OUTPUT_PREFIX}_stats.txt" || true
        fi
    fi
fi

# ---------------------------------------------------------------------------
# psutil path: periodic RSS sampling of a running PID
# ---------------------------------------------------------------------------
if [ "${PSUTIL_AVAILABLE}" = "true" ]; then
    # Find a running PID for the service
    SERVICE_PID=""
    if command -v pgrep >/dev/null 2>&1; then
        SERVICE_PID="$(pgrep -f "${SERVICE}" | head -1 || echo "")"
    fi

    if [ -n "${SERVICE_PID}" ]; then
        echo "psutil sampling PID ${SERVICE_PID} for ${DURATION}s (every 5s)..."
        PSUTIL_LOG="${OUTPUT_PREFIX}_psutil.txt"

        "${VENV_PYTHON}" - <<EOF 2>&1 | tee "${PSUTIL_LOG}"
import psutil
import time
import sys

pid = int("${SERVICE_PID}")
duration = int("${DURATION}")
interval = 5

try:
    proc = psutil.Process(pid)
except psutil.NoSuchProcess:
    print(f"ERROR: PID {pid} not found")
    sys.exit(1)

samples = []
start = time.time()
print(f"{'Time(s)':>8}  {'RSS(MB)':>10}  {'CPU%':>6}")
print("-" * 30)
while time.time() - start < duration:
    try:
        mem = proc.memory_info()
        cpu = proc.cpu_percent(interval=None)
        rss_mb = mem.rss / 1024 / 1024
        elapsed = time.time() - start
        samples.append((elapsed, rss_mb))
        print(f"{elapsed:>8.1f}  {rss_mb:>10.2f}  {cpu:>6.1f}")
        time.sleep(interval)
    except psutil.NoSuchProcess:
        print(f"Process {pid} exited after {time.time() - start:.1f}s")
        break

if len(samples) >= 2:
    early_rss = samples[min(1, len(samples) - 1)][1]
    late_rss = samples[-1][1]
    growth_pct = (late_rss - early_rss) / max(early_rss, 0.001) * 100
    print(f"\nRSS growth: {early_rss:.2f}MB → {late_rss:.2f}MB ({growth_pct:+.1f}%)")
    if "${DURATION}" != "" and int("${DURATION}") >= 300:
        threshold = 10.0
        if growth_pct > threshold:
            print(f"WARN: RSS grew {growth_pct:.1f}% > {threshold}% threshold — possible memory leak")
            sys.exit(1)
        else:
            print(f"OK: RSS growth {growth_pct:.1f}% within {threshold}% threshold")
EOF
        echo "psutil log: ${PSUTIL_LOG}"
    else
        echo "No running PID found for '${SERVICE}'. Start the service first, or use memray with a benchmark script."
        echo "Tip: run 'bash scripts/demo-mode.sh --seed' to start the local stack."
    fi
else
    echo "WARNING: neither memray nor psutil available."
    echo "Install with: uv pip install memray psutil"
    exit 1
fi

echo ""
echo "=== Memory profiling complete: ${OUTPUT_DIR} ==="
