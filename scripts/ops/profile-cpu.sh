#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# profile-cpu.sh — CPU profiling for a running service or a benchmark run
#
# Usage:
#   ./profile-cpu.sh <service-name> [--duration <seconds>]
#
# Examples:
#   ./profile-cpu.sh execution-service
#   ./profile-cpu.sh execution-service --duration 120
#   ./profile-cpu.sh strategy-service --duration 60
#
# Behaviour:
#   1. If `py-spy` is available: attaches to a running PID and generates an SVG flamegraph.
#   2. Otherwise: runs the service's benchmark scripts under cProfile via subprocess
#      and generates a pstats text report + dot/svg call graph (if gprof2dot is available).
#
# Output files (written to ./profile_output/):
#   <service>_cpu_<timestamp>.svg          (py-spy flamegraph — if py-spy available)
#   <service>_cpu_<timestamp>.cprofile     (cProfile binary dump)
#   <service>_cpu_<timestamp>_stats.txt    (pstats top-50 functions)
#   <service>_cpu_<timestamp>_callgraph.svg (gprof2dot call graph — if gprof2dot available)
#
# Target:
#   Order submission hot path <= 50% of wall time at p95 load (reference from performance-targets.md).

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
OUTPUT_PREFIX="${OUTPUT_DIR}/${SERVICE}_cpu_${TIMESTAMP}"

mkdir -p "${OUTPUT_DIR}"

echo "=== CPU Profiling: ${SERVICE} ==="
echo "Duration: ${DURATION}s"
echo "Output:   ${OUTPUT_PREFIX}.*"
echo ""

# ---------------------------------------------------------------------------
# Python interpreter
# ---------------------------------------------------------------------------
VENV_PYTHON="${SERVICE_DIR}/.venv/bin/python"
if [ ! -f "${VENV_PYTHON}" ]; then
    VENV_PYTHON="$(command -v python3 || command -v python || echo "")"
fi

if [ -z "${VENV_PYTHON}" ]; then
    echo "ERROR: no Python interpreter found. Activate a venv first." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# py-spy path: attach to a running PID and record an SVG flamegraph
# ---------------------------------------------------------------------------
PYSPY_BIN=""
if command -v py-spy >/dev/null 2>&1; then
    PYSPY_BIN="py-spy"
elif "${VENV_PYTHON}" -m py_spy --version >/dev/null 2>&1; then
    PYSPY_BIN="${VENV_PYTHON} -m py_spy"
fi

if [ -n "${PYSPY_BIN}" ]; then
    SERVICE_PID=""
    if command -v pgrep >/dev/null 2>&1; then
        SERVICE_PID="$(pgrep -f "${SERVICE}" | head -1 || echo "")"
    fi

    if [ -n "${SERVICE_PID}" ]; then
        FLAMEGRAPH_SVG="${OUTPUT_PREFIX}.svg"
        echo "py-spy recording PID ${SERVICE_PID} for ${DURATION}s..."
        # shellcheck disable=SC2086
        ${PYSPY_BIN} record \
            --pid "${SERVICE_PID}" \
            --output "${FLAMEGRAPH_SVG}" \
            --duration "${DURATION}" \
            --rate 100 \
            --format speedscope \
            2>&1 || true
        echo "Flamegraph (speedscope): ${FLAMEGRAPH_SVG}"
        echo "View at: https://www.speedscope.app (drag-drop the file)"
    else
        echo "No running PID found for '${SERVICE}' — falling back to cProfile benchmark run."
    fi
fi

# ---------------------------------------------------------------------------
# cProfile path: run benchmark suite under cProfile
# ---------------------------------------------------------------------------
echo "Running benchmark suite under cProfile..."
CPROFILE_OUT="${OUTPUT_PREFIX}.cprofile"
STATS_OUT="${OUTPUT_PREFIX}_stats.txt"

BENCH_SCRIPT="${SERVICE_DIR}/benchmarks/test_e2e_latency.py"
if [ ! -f "${BENCH_SCRIPT}" ]; then
    BENCH_SCRIPT="$(find "${SERVICE_DIR}/benchmarks" -name "test_*.py" 2>/dev/null | head -1 || echo "")"
fi

if [ -z "${BENCH_SCRIPT}" ]; then
    echo "WARNING: no benchmark script found in ${SERVICE_DIR}/benchmarks/ — skipping cProfile run."
else
    "${VENV_PYTHON}" -m cProfile \
        -o "${CPROFILE_OUT}" \
        -m pytest "${BENCH_SCRIPT}" \
        -x -q --no-header \
        2>&1 || true

    if [ -f "${CPROFILE_OUT}" ]; then
        echo "Generating pstats report..."
        "${VENV_PYTHON}" - <<EOF 2>&1 | tee "${STATS_OUT}"
import pstats
import sys

try:
    stats = pstats.Stats("${CPROFILE_OUT}", stream=sys.stdout)
    stats.sort_stats("cumulative")
    print("=== Top 50 functions by cumulative time ===")
    stats.print_stats(50)
    print("\n=== Top 20 callers of hot functions ===")
    stats.print_callers(20)
except Exception as e:
    print(f"ERROR reading cProfile output: {e}")
    sys.exit(1)
EOF
        echo "cProfile stats: ${STATS_OUT}"

        # Generate call graph SVG if gprof2dot + dot are available
        if command -v gprof2dot >/dev/null 2>&1 && command -v dot >/dev/null 2>&1; then
            CALLGRAPH_SVG="${OUTPUT_PREFIX}_callgraph.svg"
            gprof2dot --format=pstats "${CPROFILE_OUT}" \
                | dot -Tsvg -o "${CALLGRAPH_SVG}" \
                2>&1 || true
            echo "Call graph SVG: ${CALLGRAPH_SVG}"
        else
            echo "Tip: install gprof2dot + graphviz for call graph SVG:"
            echo "  uv pip install gprof2dot && brew install graphviz"
        fi
    fi
fi

echo ""
echo "=== CPU profiling complete: ${OUTPUT_DIR} ==="
