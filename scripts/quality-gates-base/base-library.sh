#!/usr/bin/env bash
# quality-gates-base-library v1.0 — owned by unified-trading-pm
#
# Shared quality-gate body for Python library/interface repos.
# Do NOT edit per-repo — this file is the SSOT for all library gate logic.
# To add a new check for all libraries, edit this file only.
#
# Required caller variables (set before sourcing this file):
#   PACKAGE_NAME  — e.g. "unified-trading-library"
#   SOURCE_DIR    — e.g. "unified_trading_library.events"  (underscore form)
#   MIN_COVERAGE  — e.g. 99
#
# Optional caller variables:
#   PYTEST_WORKERS — explicit worker count override; default is max(1, cpu_count // 4)
#   LOCAL_DEPS     — array of sibling repo names to install locally
#   MAX_DURATION   — duration limit in seconds (default: 300)
#
# Version guard (optional): declare EXPECTED_BASE_VERSION="1.0" in stub before sourcing.
#
REQUIRED_BASE_VERSION="1.0"
if [[ -n "${EXPECTED_BASE_VERSION:-}" && "$EXPECTED_BASE_VERSION" != "$REQUIRED_BASE_VERSION" ]]; then
    echo "⚠️  Stub expects base v${EXPECTED_BASE_VERSION} but base is v${REQUIRED_BASE_VERSION}" >&2
fi

# ── REQUIRED VARIABLE VALIDATION ──────────────────────────────────────────────
_qg_missing=()
[[ -z "${PACKAGE_NAME:-}" ]]  && _qg_missing+=("PACKAGE_NAME")
[[ -z "${SOURCE_DIR:-}" ]]    && _qg_missing+=("SOURCE_DIR")
[[ -z "${MIN_COVERAGE+x}" ]]  && _qg_missing+=("MIN_COVERAGE")
if [[ ${#_qg_missing[@]} -gt 0 ]]; then
    echo "❌ base-library.sh: required variables not set: ${_qg_missing[*]}" >&2
    echo "   Set these in your repo's quality-gates.sh before sourcing base-library.sh." >&2
    exit 1
fi
unset _qg_missing

set -e

# ── SHARED FOUNDATION (colors, logging, run_timeout, REPO_ROOT, CI_STATUS) ──
source "${BASH_SOURCE[0]%/*}/qg-common.sh"
cd "$PROJECT_ROOT"

# ── QG RESOURCE GOVERNANCE (mirror of base-service.sh) ────────────────────────
# Plan: quality_gates_resource_contention_speedup_2026_06_02. base-library.sh covers
# UAC + unified-trading-library (the 5.27 GB peak-RSS ceiling) — so the governor +
# thread caps matter MOST here. SSOT: codex/06-coding-standards/quality-gates.md
# § "Resource governance under multi-slot load".
source "${BASH_SOURCE[0]%/*}/qg-host-governor.sh"
export OMP_NUM_THREADS="${QG_THREAD_CAP:-2}" OPENBLAS_NUM_THREADS="${QG_THREAD_CAP:-2}" \
       MKL_NUM_THREADS="${QG_THREAD_CAP:-2}" NUMEXPR_NUM_THREADS="${QG_THREAD_CAP:-2}"
export RUFF_CACHE_DIR="${RUFF_CACHE_DIR:-${TMPDIR:-/tmp}/qg-ruff-cache}"
# Green sentinel content hash (see base-service.sh for the full rationale).
_qg_content_hash() {
    {
        git rev-parse HEAD 2>/dev/null || echo no-head
        git diff HEAD 2>/dev/null
        git ls-files --others --exclude-standard 2>/dev/null \
            | grep -vE '(^|/)(\.qg_content_sentinel|\.qg_last_passed_sha|coverage\.xml|\.coverage|\.pytest_cache/|\.ruff_cache/|__pycache__/)' \
            | sort | while IFS= read -r _f; do [ -f "$_f" ] && sha256sum "$_f" 2>/dev/null; done
        sha256sum "${BASH_SOURCE[0]}" "${BASH_SOURCE[0]%/*}/qg-host-governor.sh" 2>/dev/null
        "${RUFF_CMD:-ruff}" --version 2>/dev/null
        "${BASEDPYRIGHT_CMD:-basedpyright}" --version 2>/dev/null
        "${PYTHON_CMD:-python3}" --version 2>/dev/null
    } | sha256sum | awk '{print $1}'
}

# ── TRAP: set ci_status=FAILING on non-zero script exit ──────────────────────
_qg_exit_handler() { local rc=$?; [ "$rc" -ne 0 ] && _qg_update_ci_status_failing 2>/dev/null || true; }
trap '_qg_exit_handler' EXIT

# ── SIZE LIMITS (per coding standards) ────────────────────────────────────────
MAX_FILE_LINES=900; FILE_WARN_LINES=700
MAX_FUNCTION_LINES=${MAX_FUNCTION_LINES:-200}; MAX_CLASS_LINES=${MAX_CLASS_LINES:-900}; MAX_METHOD_LINES=${MAX_METHOD_LINES:-50}

# ── MODE ──────────────────────────────────────────────────────────────────────
# FIX_MODE DEFAULTS TO FALSE (2026-06-10): AUTO-FIX runs a TREE-WIDE `prettier --write "**/*"`
# (the [1] AUTO-FIX block), which reformats files OUTSIDE the caller's commit — a stray
# default-mode run (cron / forgotten flag) then leaves foreign reformats as worktree dirt,
# jamming the FF-pull. The canonical agent path is already `--no-fix`; making it the DEFAULT
# closes the foot-gun so a bare run can't churn the tree. Per-commit formatting is handled by
# the SCOPED prettier-autostage pre-commit hook; opt into a deliberate tree reformat with `--fix`.
FIX_MODE=false; QUICK_MODE=false; RUN_LINT=true; RUN_TESTS=true; SKIP_TYPECHECK=false; ACT_MODE=false; SKIP_VERSION_ALIGNMENT=false
for arg in "$@"; do
    case $arg in
        --no-fix) FIX_MODE=false ;;   --quick) QUICK_MODE=true ;;
        --lint) RUN_TESTS=false ;;    --test) RUN_LINT=false ;;
        --skip-tests) RUN_TESTS=false ;;
        --fix) FIX_MODE=true ;;       --skip-typecheck) SKIP_TYPECHECK=true ;;
        --act) ACT_MODE=true ;;
        --skip-version-alignment) SKIP_VERSION_ALIGNMENT=true ;;
    esac
done

# ── QG_SLICE — CI parallel-jobs selector (latency reduction 2026-06-10) ───────
# Mirrors base-service.sh. The CI reusable workflow fans the monolithic gate into
# PARALLEL jobs, each invoking this script with a slice:
#   QG_SLICE=tests       → ENVIRONMENT + [3] TESTS only        (pytest cost; dominant)
#   QG_SLICE=typecheck   → ENVIRONMENT + [4] TYPE CHECK only   (basedpyright cost)
#   QG_SLICE=lint-codex  → ENVIRONMENT + [2] LINT + [3.5] + [5] CODEX (incl. pip-audit
#                          + bandit) + [5.6] DEAD CODE + post-gates (falls through)
# UNSET (default) = the full, untouched monolithic run — behaviour-identical for
# every LOCAL invocation + existing caller. The three slices PARTITION the gate with
# ZERO overlap and ZERO lost coverage. pip-audit folds into lint-codex (shared [5] `V`
# counter; not on the critical path — see base-service.sh comment + the plan).
# A slice is a PARTIAL run → never writes the sentinel (QG_SENTINEL_DISABLE forced +
# the sentinel-write guard checks QG_SLICE empty).
QG_SLICE="${QG_SLICE:-}"
case "$QG_SLICE" in
    ""|tests|typecheck|lint-codex) : ;;
    *) echo "❌ invalid QG_SLICE='${QG_SLICE}' (allowed: tests|typecheck|lint-codex|unset)" >&2; exit 2 ;;
esac
_QG_RUN_CODEX=true
if [ -n "$QG_SLICE" ]; then
    export QG_SENTINEL_DISABLE=true
    case "$QG_SLICE" in
        tests)      RUN_LINT=false; RUN_TESTS=true;  SKIP_TYPECHECK=true;  _QG_RUN_CODEX=false ;;
        typecheck)  RUN_LINT=false; RUN_TESTS=false; SKIP_TYPECHECK=false; _QG_RUN_CODEX=false ;;
        lint-codex) RUN_LINT=true;  RUN_TESTS=false; SKIP_TYPECHECK=true;  _QG_RUN_CODEX=true  ;;
    esac
fi
_qg_slice_done() {
    case "$QG_SLICE" in
        tests|typecheck)
            echo -e "\n${GREEN:-}✅ QG_SLICE=${QG_SLICE} PASSED${NC:-}"
            exit 0 ;;
    esac
}

# ── VERSION ALIGNMENT GATE ────────────────────────────────────────────────────
_VA_GATE="${WORKSPACE_ROOT:-$(cd "$REPO_ROOT/.." && pwd)}/unified-trading-pm/scripts/quality-gates-base/version-alignment-gate.sh"
[[ -f "$_VA_GATE" ]] && source "$_VA_GATE" || echo "⚠️  version-alignment-gate.sh not found (skipping)"

# ── BOOTSTRAP (local only; CI has its own setup) ─────────────────────────────
# QG MUST audit/test the repo's OWN .venv, NOT the shared .venv-workspace (2026-06-09 fix).
# The workspace venv carries tooling/agent deps (anthropic/uv/curl-cffi/pillow/twisted/…) that
# are NOT this repo's runtime deps, so activating it made pip-audit audit the WRONG env →
# spurious vuln fails for CODEX_MAX_VIOLATIONS=0 repos (the pip-audit V++ tipped them over).
# Always build + use the repo .venv (venv-split rule; mirrors base-service.sh). Test tooling
# (pytest/basedpyright/ruff/pip-audit/bandit) is in [project.dependencies] (flat deps), so
# `uv pip install -e .` yields a COMPLETE .venv — no missing-tooling regression. CI has no
# .venv-workspace so this only corrects LOCAL runs (CI already builds the repo .venv).
WORKSPACE_VENV="${REPO_ROOT}/.venv-workspace"
if [ -z "${GITHUB_ACTIONS:-}" ] && [ -z "${CI:-}" ] && [ -z "${CLOUD_BUILD:-}" ]; then
    unset VIRTUAL_ENV   # never inherit an activated workspace venv from the parent shell
    command -v uv &>/dev/null || pip install "uv==0.10.8" --quiet
    # uv.lock freshness — WARN-ONLY, never blocking (2026-06-09). Nothing installs FROM the lock
    # (every path is `uv pip install -e .`, no `uv sync`/`--frozen`/`--locked`), so the lock is a
    # RECORD, not an enforced pin: the real dependency contract is the pyproject RANGE, which `uv pip
    # install` enforces at install (an out-of-range MAJOR fails to resolve = the signal). Blocking here
    # only added churn on the cosmetic internal-editable `version =` snapshot. Do NOT mutate uv.lock
    # here either (it dirtied trees + jammed the FF-pull cron). SSOT:
    # plans/active/dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md § Phase 1.
    uv lock --check 2>/dev/null || echo "⚠️  uv.lock out of sync with pyproject.toml (non-blocking — lock is a record, not a pin; pyproject range is the contract). Run 'uv lock' to refresh the record."
    [ ! -d ".venv" ] && uv venv .venv
    [ -f ".venv/bin/activate" ] && source .venv/bin/activate || :
    for lib in ${LOCAL_DEPS[@]+"${LOCAL_DEPS[@]}"}; do
        [ -d "${REPO_ROOT}/$lib" ] && uv pip install -e "${REPO_ROOT}/$lib" --quiet 2>/dev/null || :
    done
    uv pip install -e . --quiet 2>/dev/null || :
fi
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
elif [ -f "$WORKSPACE_VENV/bin/python" ]; then
    PYTHON_CMD="$WORKSPACE_VENV/bin/python"
else
    PYTHON_CMD="python3"
fi

# Prefer workspace venv ruff when available (align with PYTHON_CMD)
if [ -f "$WORKSPACE_VENV/bin/ruff" ]; then
    RUFF_CMD="$WORKSPACE_VENV/bin/ruff"
elif [ -f ".venv/bin/ruff" ]; then
    RUFF_CMD=".venv/bin/ruff"
else
    RUFF_CMD="ruff"
fi

# BASEDPYRIGHT: always resolve from per-repo .venv — NEVER workspace venv
# (workspace venv has extra packages that mask missing dep declarations → CI would fail)
BASEDPYRIGHT_CMD=".venv/bin/basedpyright"; [ ! -f "$BASEDPYRIGHT_CMD" ] && BASEDPYRIGHT_CMD="basedpyright"

STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | grep '\.py$' | tr '\n' ' ' || :)
SOURCE_DIRS="${STAGED:-$SOURCE_DIR/ tests/}"
[ -n "$STAGED" ] && log_warn "Git-aware mode: $(echo "$STAGED" | wc -w | tr -d ' ') staged files"

export CLOUD_MOCK_MODE="true"; export GCP_PROJECT_ID="test-project"

# ── [0] ENVIRONMENT ────────────────────────────────────────────────────────────
log_section "[0/6] ENVIRONMENT"
ACTUAL_PY=$($PYTHON_CMD --version 2>&1 | awk '{print $2}' | cut -d'.' -f1,2)
[[ "$ACTUAL_PY" != "3.13" ]] && { log_fail "Python 3.13 required, found $ACTUAL_PY"; exit 1; }; log_success "Python $ACTUAL_PY"
command -v rg &>/dev/null || { log_fail "ripgrep required: brew install ripgrep"; exit 1; }; log_success "ripgrep OK"
[ -f "pyproject.toml" ] && grep -q '>=3.13,<3.14' pyproject.toml || { log_fail "pyproject.toml: requires-python = '>=3.13,<3.14'"; exit 1; }; log_success "pyproject.toml OK"
[[ ! -f "uv.lock" ]] && log_warn "uv.lock missing" || log_success "uv.lock present"
RUFF_VER=$($RUFF_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo "0")
[[ "$RUFF_VER" != "0.15.0" ]] && log_warn "ruff 0.15.0 expected, found $RUFF_VER" || log_success "ruff $RUFF_VER"
BP_VER=$("$BASEDPYRIGHT_CMD" --version 2>/dev/null | head -1 | awk '{print $NF}' || echo "0")
[[ "$BP_VER" != "1.38.2" ]] && log_warn "basedpyright 1.38.2 expected, found $BP_VER" || log_success "basedpyright $BP_VER"

# ── [1] AUTO-FIX (prettier + ruff, 30s each) ──────────────────────────────────
# Prettier runs FIRST on non-Python files to prevent ruff/prettier conflict in pre-commit hooks.
# Without this, committing JSON/YAML/MD files causes "MM" status and hook stash conflicts.
# See: 06-coding-standards/quality-gates.md § Formatter Conflict Resolution
if [ "$RUN_LINT" = true ] && [ "$FIX_MODE" = true ]; then
    log_section "[1/6] AUTO-FIX"
    if command -v npx &>/dev/null; then
        npx --yes prettier@3.6.2 --write --cache "**/*.{md,json,yaml,yml}" --ignore-path .gitignore --ignore-path .prettierignore >/dev/null 2>&1 \
            || log_warn "Prettier not available or no files to format (skipping)"
    else
        log_warn "npx not available — skipping prettier pre-format (commit may require re-staging)"
    fi
    run_timeout 30 $RUFF_CMD format $SOURCE_DIRS >/dev/null 2>&1 || :
    run_timeout 30 $RUFF_CMD check --fix $SOURCE_DIRS >/dev/null 2>&1 || :
    log_success "Auto-fix complete"
fi

# ── [2] LINT (ruff, 30s) ──────────────────────────────────────────────────────
if [ "$RUN_LINT" = true ]; then
    log_section "[2/6] LINT"
    _lint_out=$(run_timeout 30 $RUFF_CMD check $SOURCE_DIRS 2>&1) || { echo "$_lint_out"; log_fail "Lint FAILED"; exit 1; }
fi

# ── GREEN SENTINEL + GOVERNOR (mirror of base-service.sh) ──
_QG_SENTINEL_HIT=false
_QG_SENTINEL_FILE="${PROJECT_ROOT}/.qg_content_sentinel"
_QG_CONTENT_HASH=""
if [ "${QG_SENTINEL_DISABLE:-false}" != "true" ]; then
    _QG_CONTENT_HASH="$(_qg_content_hash)"
    if [ "${#_QG_CONTENT_HASH}" -eq 64 ] && [ -f "$_QG_SENTINEL_FILE" ] \
       && [ "$(cat "$_QG_SENTINEL_FILE" 2>/dev/null)" = "$_QG_CONTENT_HASH" ]; then
        _QG_SENTINEL_HIT=true
        log_success "Green sentinel HIT — tree byte-identical to last full green; skipping TESTS + TYPE CHECK"
    fi
fi
[ "$_QG_SENTINEL_HIT" = true ] || qg_governor_acquire

# ── [3] TESTS (pytest — unit always, integration when tests/integration/ exists) ──
if [ "$RUN_TESTS" = true ] && [ "$_QG_SENTINEL_HIT" != true ]; then
    log_section "[3/6] TESTS"
    $PYTHON_CMD -c "import pytest_timeout" 2>/dev/null || { log_fail "pytest-timeout required: uv pip install pytest-timeout"; exit 1; }
    $PYTHON_CMD -c "import xdist" 2>/dev/null || { log_fail "pytest-xdist required: uv pip install pytest-xdist"; exit 1; }
    COV="--cov=$SOURCE_DIR --cov-report=xml:coverage.xml --cov-fail-under=$MIN_COVERAGE"
    # 25% of logical CPUs, minimum 1. Works on Linux, macOS (Intel + Apple Silicon), ARM.
    # PYTEST_WORKERS env var overrides when set (e.g. CI throttling or debugging).
    _DEFAULT_WORKERS=$($PYTHON_CMD -c "import multiprocessing; print(max(1, multiprocessing.cpu_count()//4))" 2>/dev/null || echo 1)
    # Memory-frugal default (was $_DEFAULT_WORKERS = cpu_count//4 → oversubscription on
    # a shared host; UTL peaks 5.27 GB). Per-repo opt-in: export PYTEST_WORKERS=N.
    # ── PYTEST PARALLELISM (latency reduction 2026-06-10) — mirror of base-service.sh ──
    # In CI each quality-gates-v2 leg runs ALONE on its own runner (no shared-host OOM
    # risk), so xdist `-n auto` cuts the dominant pytest leg ~2-4×. LOCAL stays 1 (the
    # OOM-safe value). Explicit PYTEST_WORKERS wins; else CI → auto, local → 1.
    if [ -n "${PYTEST_WORKERS:-}" ]; then
        _PYTEST_N="${PYTEST_WORKERS}"
    elif [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${CI:-}" ]; then
        _PYTEST_N="auto"
    else
        _PYTEST_N="1"
    fi
    PARGS="-n ${_PYTEST_N} --timeout=60 -q -r a --tb=short --no-header"

    # Per-repo test root override. Default: tests/unit/. Set PYTEST_UNIT_DIR before sourcing this
    # script to add per-family unit test dirs (e.g. PYTEST_UNIT_DIR="tests/unit/ tests/events/unit/").
    PYTEST_UNIT_DIR="${PYTEST_UNIT_DIR:-tests/unit/}"

    _HAS_INTEGRATION=false
    [ -d "tests/integration" ] && \
        [ "$(find tests/integration -name 'test_*.py' 2>/dev/null | wc -l | tr -d ' ')" -gt 0 ] && \
        _HAS_INTEGRATION=true

    if [ "$_HAS_INTEGRATION" = true ]; then
        _pytest_out=$($PYTHON_CMD -m pytest ${PYTEST_UNIT_DIR} tests/integration/ --allow-hosts=127.0.0.1,::1,localhost --allow-unix-socket $PARGS $COV 2>&1) \
            || { echo "$_pytest_out"; exit 1; }
    else
        _pytest_out=$($PYTHON_CMD -m pytest ${PYTEST_UNIT_DIR} --allow-hosts=127.0.0.1,::1,localhost --allow-unix-socket $PARGS $COV 2>&1) \
            || { echo "$_pytest_out"; exit 1; }
    fi
    log_success "Tests PASSED"

    # PM integration test — verifies repo integrates with PM scripts (quality-gates, setup, manifest)
    PM_INT_TEST="${REPO_ROOT}/unified-trading-pm/tests/integration/test_pm_scripts_integration.py"
    if [ -f "$PM_INT_TEST" ] && [ -d "${REPO_ROOT}/unified-trading-pm" ]; then
        if ! PROJECT_ROOT="$PROJECT_ROOT" $PYTHON_CMD -m pytest "$PM_INT_TEST" -v -m integration --tb=line -q 2>/dev/null; then
            log_fail "PM integration test failed — repo must integrate with PM scripts"
            exit 1
        fi
        log_success "PM integration test PASSED"
    fi


    # No duplicate test files (test_*_extended.py, test_*_additional.py)
    DUP=$(find tests/ -name "test_*_extended.py" -o -name "test_*_additional.py" 2>/dev/null | head -5 || :)
    [[ -n "$DUP" ]] && { log_fail "Duplicate test files — expand existing files instead:"; echo "$DUP"; exit 1; }
    log_success "No duplicate test files"


    # Integration test coverage for library deps — only checked when tests/integration/ exists.
    _INT_DEP_CHECK="${REPO_ROOT}/unified-trading-pm/scripts/validation/check-integration-dep-coverage.py"
    if [ -f "$_INT_DEP_CHECK" ] && [ "${_HAS_INTEGRATION}" = true ]; then
        if ! $PYTHON_CMD "$_INT_DEP_CHECK" --repo "$PACKAGE_NAME" --project-root "$PROJECT_ROOT" --manifest "${REPO_ROOT}/unified-trading-pm/workspace-manifest.json" 2>/dev/null; then
            log_fail "Integration test coverage missing for library deps — add tests in tests/integration/ that import each library. Bypass: QUALITY_GATE_BYPASS_AUDIT.md"
            exit 1
        fi
        log_success "Integration dep coverage OK"
    fi
    # @pytest.mark.skip (bare skip, not skipif) must have a reason comment on the preceding line
    # skipif always carries reason= inline so is excluded from this check
    SKIP_NO_REASON=$(rg "@pytest\.mark\.skip" --type py tests/ -B 1 2>/dev/null \
        | grep -v "# reason:\|# noqa\|^--\|skipif\|reason=" | grep "@pytest\.mark\.skip" || :)
    [[ -n "$SKIP_NO_REASON" ]] && { log_fail "pytest.mark.skip without reason comment — add '# reason: ...' above"; echo "$SKIP_NO_REASON" | head -3; exit 1; }
    log_success "All pytest.mark.skip have reason comments"
fi
# QG_SLICE=tests finishes here (its one phase is the pytest run above).
_qg_slice_done

# ── [3.5] IMPORT PATTERN STANDARDS ───────────────────────────────────────────
# Codex-adjacent static check → lint-codex slice (typecheck slice skips via _QG_RUN_CODEX).
if [ "${_QG_RUN_CODEX}" = true ]; then
log_section "[3.5/6] IMPORT PATTERNS"
IP="${REPO_ROOT}/unified-trading-pm/scripts/validation/check-import-patterns.py"
[ ! -f "$IP" ] && IP="${REPO_ROOT}/unified-trading-pm/scripts/check-import-patterns.py"  # pre-move fallback
[ ! -f "$IP" ] && IP="${REPO_ROOT}/.cursor/scripts/check-import-patterns.py"
if [[ "${SKIP_IMPORT_PATTERNS:-false}" == "true" ]]; then
    log_success "Import patterns: skipped (SKIP_IMPORT_PATTERNS=true)"
elif [ -f "$IP" ]; then
    # Scope import check to SOURCE_DIR only — tests are allowed to deep-import from their own
    # package (they test internal components). External consumers are linted at a higher level.
    IP_TARGET="${SOURCE_DIR:-.}"
    _ip_out=$($PYTHON_CMD "$IP" "$IP_TARGET" 2>/dev/null) || { echo "$_ip_out"; log_fail "Import patterns FAILED"; exit 1; }
else
    log_warn "check-import-patterns.py not found (unified-trading-pm/scripts/)"
fi
fi  # _QG_RUN_CODEX (import-patterns)

# ── [4] TYPE CHECK (basedpyright, 120s, zombie cleanup) ──────────────────────
log_section "[4/6] TYPE CHECK"
if [ "$SKIP_TYPECHECK" != "true" ] && [ "${_QG_SENTINEL_HIT:-false}" != true ]; then
    cleanup_zombie_pyright() {
        _killed=0
        while read -r pid etime _; do
            mins=0
            if echo "$etime" | grep -q '-'; then
                d=$(echo "$etime" | cut -d'-' -f1); rest=$(echo "$etime" | cut -d'-' -f2)
                h=$(echo "$rest" | cut -d':' -f1); m=$(echo "$rest" | cut -d':' -f2)
                mins=$((d * 24 * 60 + h * 60 + m))
            elif [ "$(echo "$etime" | tr ':' '\n' | wc -l)" -eq 3 ]; then
                h=$(echo "$etime" | cut -d':' -f1); m=$(echo "$etime" | cut -d':' -f2)
                mins=$((h * 60 + m))
            elif [ "$(echo "$etime" | tr ':' '\n' | wc -l)" -eq 2 ]; then
                m=$(echo "$etime" | cut -d':' -f1); mins=${m:-0}
            else
                mins=0
            fi
            if [ "${mins:-0}" -ge 30 ]; then
                log_warn "Killing zombie basedpyright PID $pid"
                kill -9 "$pid" 2>/dev/null || :
                _killed=$((_killed + 1))
            fi
        done < <(ps -eo pid,etime,command 2>/dev/null | grep -E 'basedpyright.*index\.js' | grep -v grep) || :
        [ "${_killed:-0}" -eq 0 ] && log_success "No zombie basedpyright processes to kill" || :
    }
    cleanup_zombie_pyright
    [ ! -f "$BASEDPYRIGHT_CMD" ] && ! command -v basedpyright &>/dev/null && { log_fail "basedpyright required: uv pip install basedpyright==1.38.2"; exit 1; }
    if [ -z "$SOURCE_DIR" ] || [ "$SOURCE_DIR" = "REPLACE_ME" ]; then
        log_fail "SOURCE_DIR not set — cannot run basedpyright safely"; exit 1
    fi
    # ── BASELINE FILE GATE ────────────────────────────────────────────────────
    # Zero-baseline policy (2026-03-10): presence of .basedpyright-baseline.json is a hard block.
    # Delete the file and resolve all underlying type errors before re-running.
    if [ -f ".basedpyright-baseline.json" ]; then
        log_fail "TYPE CHECK: .basedpyright-baseline.json present — baseline suppression not allowed (zero-baseline policy); delete the file and fix all type errors"; exit 1
    fi
    export BASEDPYRIGHT_CACHE_DIR="${TMPDIR:-/tmp}/basedpyright-cache/${PACKAGE_NAME:-$(basename "$PWD")}"
    mkdir -p "$BASEDPYRIGHT_CACHE_DIR"
    BP_PID=""
    trap '''[[ -n "$BP_PID" ]] && kill -9 $BP_PID 2>/dev/null''' INT TERM
    _bp_out="/tmp/bp_out.$$"
    run_timeout "${PYRIGHT_TIMEOUT:-120}" "$BASEDPYRIGHT_CMD" "$SOURCE_DIR/" > "$_bp_out" 2>&1 &
    BP_PID=$!
    wait $BP_PID || true
    PYRIGHT_EXIT=$?
    trap - INT TERM
    PYRIGHT_OUT=$(cat "$_bp_out" 2>/dev/null); rm -f "$_bp_out"
    if [ "$PYRIGHT_EXIT" -ne 0 ]; then echo "$PYRIGHT_OUT"; log_fail "Type check FAILED/timeout"; exit 1; fi
    WARN_COUNT=$(echo "$PYRIGHT_OUT" | grep -c " warning:" || :)
    if [ "${WARN_COUNT:-0}" -gt 0 ]; then
        echo "$PYRIGHT_OUT"
        log_fail "Type check FAILED — $WARN_COUNT warning(s) (zero-warning policy: promote all rules to error in [tool.basedpyright])"; exit 1
    fi
    log_success "Type check PASSED (0 errors, 0 warnings)"
fi
[ "$SKIP_TYPECHECK" = "true" ] && echo -e "${YELLOW}⚠️  Type check SKIPPED (--skip-typecheck flag)${NC}"

# ── HOST CONCURRENCY GOVERNOR: release after the heavy phases (no-op on sentinel hit) ──
[ "${_QG_SENTINEL_HIT:-false}" = true ] || qg_governor_release

# QG_SLICE=typecheck finishes here (basedpyright was its only phase). Everything from
# [5] onward (codex + pip-audit + bandit + dead-code + post-gates) is the lint-codex
# slice + the full run — both reach here, so [5] needs no extra slice guard.
if [ "$QG_SLICE" = typecheck ]; then
    echo -e "\n${GREEN:-}✅ QG_SLICE=typecheck PASSED${NC:-}"
    exit 0
fi

# ── [5] CODEX COMPLIANCE (library variant) ────────────────────────────────────
# Same checks as service variant with library-specific exceptions noted inline.
log_section "[5/6] CODEX COMPLIANCE"
V=0

rg "print\(" --type py --glob "!tests/**" --glob "!scripts/**" --glob "!**/testing/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "print() — use logger"; V=$(( V + 1 )); } || log_success "No print()"

# unified-config-interface: bootstrap exception — UCI IS the config layer, must read os.environ
# (QUALITY_GATE_BYPASS_AUDIT.md §2.4)
if [[ "$PACKAGE_NAME" != "unified-config-interface" ]]; then
    _osenv_extra_globs=()
    for _f in "${OS_ENVIRON_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_f" ]] && _osenv_extra_globs+=("--glob" "!${_f}"); done
    _OSENV=$(rg "os\.getenv|os\.environ" --type py --glob "!tests/**" --glob "!**/testing/**" --glob "!scripts/**" "${_osenv_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
        | grep -v "# noqa:.*qg-os-environ\|# noqa: qg-os-environ\|# config-bootstrap:" || :)
    [[ -n "$_OSENV" ]] && { log_fail "os.getenv()/os.environ — use UnifiedCloudConfig for config, get_secret_client() for secrets"; echo "$_OSENV" | head -3; V=$(( V + 1 )); } || log_success "No os.getenv()/os.environ"
else
    log_success "os.getenv/bootstrap — UCI is config layer (bypass §2.4)"
fi

rg 'os\.getenv\s*\([^)]+,\s*""\s*\)' --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "os.getenv empty fallback — fail fast"; V=$(( V + 1 )); } || log_success "No os.getenv empty fallback"

rg "datetime\.now\(\)|datetime\.utcnow\(\)" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Naive datetime — use datetime.now(timezone.utc)"; V=$(( V + 1 )); } || log_success "No naive datetime"

rg "except:" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Bare except — use specific exception"; V=$(( V + 1 )); } || log_success "No bare except"

for f in $(rg "import requests" --type py --glob "!tests/**" --glob "!scripts/**" "$SOURCE_DIR/" -l 2>/dev/null || :); do
    # Skip if the import line has a noqa comment for this check
    rg "import requests.*# noqa:.*qg-requests-in-async" "$f" >/dev/null 2>&1 && continue
    grep -q "async def" "$f" && { log_fail "requests in async: $f — use aiohttp"; V=$(( V + 1 )); break; }
done; [[ ${V} -eq $(( V )) ]] && log_success "No requests in async" 2>/dev/null || :

_asyncio_violation=""
for f in $(rg "asyncio\.run\(" --type py --glob "!tests/**" --glob "!scripts/**" --glob "!**/testing/**" "$SOURCE_DIR/" -l 2>/dev/null || :); do
    # Only flag asyncio.run() deeply nested inside a loop body (>=8 spaces indentation)
    if rg "^\s{8,}asyncio\.run\(" "$f" 2>/dev/null | grep -q .; then
        _asyncio_violation="$f"
        break
    fi
done
if [[ -n "$_asyncio_violation" ]]; then
    log_fail "asyncio.run() in loop: $_asyncio_violation — use asyncio.gather()"
    V=$(( V + 1 ))
else
    log_success "No asyncio.run() in loop"
fi

# Imports inside functions — AST-based check (operator decision (a) 2026-05-11).
# Replaces the prior regex check (which false-positived on docstring usage examples
# containing `from foo import bar`). The AST walker only flags actual nested-function
# Import / ImportFrom nodes; docstrings, comments, and string literals are inert.
# Honours `# noqa: imports-inside-functions` and the legacy `# noqa: qg-inside-import` marker.
# Self-package imports (circular-import workarounds) auto-skipped via --self-pkg.
_SELF_PKG=$(echo "$SOURCE_DIR" | tr '/' '_')
_AST_CHECKER="$(cd "$(dirname "${BASH_SOURCE[0]}")/../quality_gates" && pwd)/check_imports_inside_functions.py"
_inside_extra_args=()
for _excl in "${INSIDE_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _inside_extra_args+=("--exclude-glob" "$_excl"); done
if python3 "$_AST_CHECKER" --source-dir "$SOURCE_DIR" --self-pkg "$_SELF_PKG" \
    "${_inside_extra_args[@]}" 2>/tmp/_inside_imports_qg.err; then
    log_success "No imports inside functions"
else
    log_fail "Imports inside functions — move to top (AST-detected)"
    head -10 /tmp/_inside_imports_qg.err 2>/dev/null
    V=$(( V + 1 ))
fi

# `!**/testing/**` mirrors the empty-fallback + inside-import checks: in-package test-support
# utilities (e.g. internal/testing/ seed validators) legitimately carry `pd.Series[Any]` that
# pandas-stubs forces and that basedpyright's reportUnknownVariableType requires be annotated.
ANY=$(rg ": Any|-> Any|\[Any\]" --type py --glob "!tests/**" --glob "!**/testing/**" "$SOURCE_DIR/" 2>/dev/null | grep -v "type: ignore" || :)
[[ -n "$ANY" ]] && { log_fail "Any types (including dict[str, Any]) — use Pydantic models or specific types"; echo "$ANY" | head -3; V=$(( V + 1 )); } || log_success "No Any types"

_raw_json_extra_globs=()
for _excl in "${RAW_JSON_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _raw_json_extra_globs+=("--glob" "!${_excl}"); done
RAW_JSON=$(rg 'response\.json\(\)|await response\.json\(\)' --type py --glob "!tests/**" "${_raw_json_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v 'model_validate\|cast(dict' \
    | grep -v "# noqa:.*qg-raw-json\|# noqa: qg-raw-json" || :)
[[ -n "$RAW_JSON" ]] && { log_fail "Raw response.json() — parse through Pydantic model_validate()"; echo "$RAW_JSON" | head -3; V=$(( V + 1 )); } || log_success "No raw response.json()"

_efb_extra_globs=()
for _excl in "${EMPTY_FALLBACK_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _efb_extra_globs+=("--glob" "!${_excl}"); done
ES=$(rg '\.get\(["\x27][\w_]+["\x27]\s*,\s*["\x27]["\x27]\)' --type py --glob "!tests/**" --glob "!**/testing/**" "${_efb_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa:.*qg-empty-fallback\|# noqa: qg-empty-fallback" || :)
[[ -n "$ES" ]] && { log_fail "Empty string fallback — fail fast"; echo "$ES" | head -3; V=$(( V + 1 )); } || log_success "No empty string fallbacks"

ED=$(rg '\.get\s*\(\s*["\x27][^"\x27]+["\x27]\s*,\s*\{\}\s*\)' --type py --glob "!tests/**" --glob "!**/testing/**" "${_efb_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa:.*qg-empty-fallback\|# noqa: qg-empty-fallback" || :)
EL=$(rg '\.get\s*\(\s*["\x27][^"\x27]+["\x27]\s*,\s*\[\]\s*\)' --type py --glob "!tests/**" --glob "!**/testing/**" "${_efb_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa:.*qg-empty-fallback\|# noqa: qg-empty-fallback" || :)
[[ -n "$ED$EL" ]] && { log_fail "Empty dict/list fallback — fail fast"; V=$(( V + 1 )); } || log_success "No empty dict/list fallbacks"

rg "central-element-323112" tests/ 2>/dev/null \
    && { log_fail "Hardcoded prod project ID in tests — use 'test-project'"; V=$(( V + 1 )); } || log_success "No hardcoded project ID in tests"

# GCP_PROJECT_ID_EXCLUDE_GLOBS: per-repo array of glob patterns (e.g. "!**/registry/foo.py")
GCP_LIB_EXTRA=()
for g in ${GCP_PROJECT_ID_EXCLUDE_GLOBS[@]+"${GCP_PROJECT_ID_EXCLUDE_GLOBS[@]}"}; do GCP_LIB_EXTRA+=(--glob "$g"); done
rg "central-element-323112" --type py --glob "!tests/**" "${GCP_LIB_EXTRA[@]}" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Hardcoded project ID in production — use config"; V=$(( V + 1 )); } || log_success "No hardcoded project ID in production"

BAD_PROJECT=$(rg "GOOGLE_CLOUD_PROJECT|GCP_PROJECT(?!_ID)" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$BAD_PROJECT" ]] && { log_fail "Use GCP_PROJECT_ID; banned: GOOGLE_CLOUD_PROJECT, GCP_PROJECT"; echo "$BAD_PROJECT" | head -3; V=$(( V + 1 )); } || log_success "Project ID uses GCP_PROJECT_ID"

UCS_DOMAIN=$(rg 'from unified_trading_library import[^#]*?(InstrumentsDomainClient|ExecutionDomainClient|MarketCandleDataDomainClient|MarketTickDataDomainClient|create_instruments_client|create_execution_client|create_features_client|create_market_candle_data_client|create_market_tick_data_client)' \
    --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$UCS_DOMAIN" ]] && { log_fail "Domain clients must come from unified_domain_client, not unified_trading_library"; echo "$UCS_DOMAIN" | head -5; V=$(( V + 1 )); } || log_success "Domain clients imported from unified_domain_client"

DOMAIN_FROM_UCS=$(rg 'from unified_trading_library import.*(market_category|DomainValidation|UnifiedCloudServicesConfig)' \
    --type py "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$DOMAIN_FROM_UCS" ]] && { log_fail "Library imports domain symbols from UCS — use unified_domain_client instead"; echo "$DOMAIN_FROM_UCS" | head -5; V=$(( V + 1 )); } || log_success "No domain imports from UCS"

if rg 'def setup_events|def setup_service' --type py "$SOURCE_DIR/" -q 2>/dev/null; then
    log_success "setup_service() check skipped (repo defines setup_events/setup_service)"
else
    SETUP_NO_SINK=$(rg 'setup_(events|service)\s*\(' --type py \
        --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null | grep -v 'sink=' \
        | grep -v "def setup_events\|def setup_service" \
        | grep -vE ":[[:space:]]*#|:[[:space:]]+(\"\"\"|\x27\x27\x27)" || :)
    [[ -n "$SETUP_NO_SINK" ]] && { log_fail "setup_events()/setup_service() called without sink= in production code"; echo "$SETUP_NO_SINK" | head -5; V=$(( V + 1 )); } || log_success "setup_service() uses sink= in all production call sites"
fi

BAD_AUTH_SKIP=$(rg 'pytest\.skip.*[Cc]redential|pytest\.skip.*GOOGLE_APPLICATION_CREDENTIALS|if not.*gcp_credentials.*pytest\.skip\|if not.*cred_file.*pytest\.skip' \
    --type py tests/ 2>/dev/null \
    | grep -v "_skip_integration_without_creds\|No GCP credentials.*skipping integration\|No GCP credentials.*skipping Secret Manager\|Could not create/access" \
    || :)
[[ -n "$BAD_AUTH_SKIP" ]] && { log_fail "Tests skip due to missing credential file — use google.auth.default() + @pytest.mark.integration instead"; echo "$BAD_AUTH_SKIP" | head -5; V=$(( V + 1 )); } || log_success "No credential-file skip patterns in tests"

[[ -f ".env.example" ]] && rg "GOOGLE_APPLICATION_CREDENTIALS" .env.example 2>/dev/null \
    && { log_fail ".env.example contains GOOGLE_APPLICATION_CREDENTIALS — remove it (use ADC, not SA key files)"; V=$(( V + 1 )); } || log_success "No GOOGLE_APPLICATION_CREDENTIALS in .env.example"

_di_extra_globs=()
for _excl in "${DEEP_IMPORT_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _di_extra_globs+=("--glob" "!${_excl}"); done
DI=$(rg 'from unified_[a-z_]+\.[a-zA-Z0-9_.]+\s+import' --type py --glob "!tests/**" --glob "!**/__init__.py" "${_di_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "from ${_SELF_PKG}\." \
    | grep -v "from unified_api_contracts\.internal" \
    | grep -v "from unified_api_contracts\.testing" \
    | grep -v "# noqa:.*qg-deep-import\|# noqa: qg-deep-import" || :)
[[ -n "$DI" ]] && { log_fail "Deep unified lib imports — use top-level"; echo "$DI" | head -3; V=$(( V + 1 )); } || log_success "No deep imports"

# Post-consolidation: unified_trading_library.events merged INTO unified_trading_library.
# 'from unified_trading_library import log_event' IS the canonical import path.
# Only flag imports from truly obsolete packages (none currently exist).
EL_OLD=""
[[ -n "$EL_OLD" ]] && { log_fail "Old event logging import — use 'from unified_trading_library import ...'"; echo "$EL_OLD" | head -3; V=$(( V + 1 )); } || log_success "Event logging imports OK"

# ============================================================
# STEP 5.5 — No direct cloud SDK imports
# Libraries: exclude providers/ and cache.py (UCI-specific paths)
# ============================================================
CLOUD_SDK_VIOLATIONS=$(rg "^from google\.cloud|^import boto3|^import botocore" \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!tests' \
    --glob '!**/providers/**' \
    --glob '!*/cache.py' \
    --glob '!typings/**' --glob '!*/typings/**' \
    -l . 2>/dev/null || :)
[[ -n "$CLOUD_SDK_VIOLATIONS" ]] && {
    log_fail "STEP 5.5: Direct cloud SDK imports found. Use unified_cloud_interface instead:"
    echo "$CLOUD_SDK_VIOLATIONS"
    V=$(( V + 1 ))
} || log_success "STEP 5.5: No direct cloud SDK imports"

# ============================================================
# STEP 5.6 — Architecture Tier Compliance
# ============================================================
REPO_ARCH_TIER="${REPO_ARCH_TIER:-library}"
if [[ "$REPO_ARCH_TIER" == "0" ]]; then
    TIER_VIOLATIONS=$(rg 'from unified_trading_library|from unified_domain_client' \
        --type py "${SOURCE_DIR}/" 2>/dev/null | grep -v __pycache__ || :)
    [[ -n "$TIER_VIOLATIONS" ]] && {
        log_fail "Tier 0 violation: imports from Tier 1+ library:"
        echo "$TIER_VIOLATIONS" | head -5
        V=$(( V + 1 ))
    } || log_success "Tier 0 compliance: no Tier 1+ imports"
else
    log_success "Tier compliance skipped (REPO_ARCH_TIER=$REPO_ARCH_TIER)"
fi

# ============================================================
# STEP 5.8 — No backward-compatibility re-export stubs
# ============================================================
BACK_COMPAT=$(rg "# MIGRATED|backward compat|backward-compat|Re-export.*backward|re-export.*compat" \
    --type py --glob "!tests/**" --glob "!.venv*" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa:.*qg-backward-compat\|# noqa: qg-backward-compat" || :)
[[ -n "$BACK_COMPAT" ]] && {
    log_fail "Backward-compat pattern found — eliminate re-export stubs, aliases, and compat shims"
    log_fail "See: cursor-rules/core/no-backward-compat-shims.mdc"
    echo "$BACK_COMPAT" | head -5
    V=$(( V + 1 ))
} || log_success "No backward-compat stubs"

# ============================================================
# STEP 5.9 — Schema placement (advisory for libraries)
# ============================================================
# UAC and UIC are the schema repos — skip; they own external API and internal domain schemas
if [[ "$PACKAGE_NAME" != "unified-api-contracts" ]]; then
    DOMAIN_CONTRACTS_IN_LIB=$(rg 'class \w+\(BaseModel\)' --type py \
        --glob "!tests/**" --glob "!**/__init__.py" \
        "$SOURCE_DIR/" 2>/dev/null | grep -v '#.*CORRECT-LOCAL' || :)
    [[ -n "$DOMAIN_CONTRACTS_IN_LIB" ]] && {
        log_warn "Pydantic BaseModel subclasses found in library source — external API schemas belong in UAC; internal domain contracts in UIC"
        log_warn "See: unified-trading-pm/plans/active/SCHEMA_CONTRACTS_AUDIT.md"
        echo "$DOMAIN_CONTRACTS_IN_LIB" | head -5
    } || log_success "No misplaced domain BaseModel contracts in library"
else
    log_success "Schema repos (UAC/UIC) — skip BaseModel check"
fi

# ============================================================
# STEP 5.10 — Schema organization (UAC/UIC) and provenance (other repos)
# ============================================================
REPO_ROOT_FOR_SCHEMA="${REPO_ROOT:-$(dirname "$PROJECT_ROOT")}"
if [[ "$PACKAGE_NAME" = "unified-api-contracts" ]]; then
    if [[ -x "$PROJECT_ROOT/scripts/check_schema_organization.py" ]] || command -v python3 &>/dev/null; then
        if WORKSPACE_ROOT="$REPO_ROOT_FOR_SCHEMA" python3 "$PROJECT_ROOT/scripts/check_schema_organization.py" 2>/dev/null; then
            log_success "UAC schema organization OK"
        else
            log_warn "UAC schema organization: schemas in schemas/ not used in normalize/external/tests (should be in UIC)"
            WORKSPACE_ROOT="$REPO_ROOT_FOR_SCHEMA" python3 "$PROJECT_ROOT/scripts/check_schema_organization.py" 2>/dev/null || true
        fi
    fi
elif [[ -f "$REPO_ROOT_FOR_SCHEMA/unified-trading-pm/scripts/validation/check_schema_provenance.py" ]]; then
    if python3 "$REPO_ROOT_FOR_SCHEMA/unified-trading-pm/scripts/validation/check_schema_provenance.py" --repo "$PACKAGE_NAME" --workspace-root "$REPO_ROOT_FOR_SCHEMA" 2>/dev/null; then
        log_success "Schema provenance OK (schemas from UAC/UIC)"
    else
        log_warn "Schema provenance: local BaseModel/TypedDict/dataclass found (should import from UAC or UIC)"
        python3 "$REPO_ROOT_FOR_SCHEMA/unified-trading-pm/scripts/validation/check_schema_provenance.py" --repo "$PACKAGE_NAME" --workspace-root "$REPO_ROOT_FOR_SCHEMA" 2>/dev/null | head -10 || true
    fi
fi

# ============================================================
# STEP 5.11 — Block protocol-specific symbols
# unified-config-interface cloud_config.py: field names are schema — documented bypass §2.6
# unified-api-contracts: defines CloudTarget enum + facade re-exports as workspace SSOT
# unified-trading-library: defines/deprecates these symbols — excluded as origin repo §2.6
# ============================================================
if [[ "$PACKAGE_NAME" = "unified-config-interface" ]]; then
    PROTOCOL_VIOLATIONS=$(rg "CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
        --type py --glob '!.venv*' --glob '!**/.venv*/**' --glob '!tests' --glob '!**/cloud_config.py' -l . 2>/dev/null || :)
elif [[ "$PACKAGE_NAME" = "unified-api-contracts" ]]; then
    # UAC defines CloudTarget as the workspace SSOT enum (canonical/crosscutting/cloud_target.py)
    # and re-exports it from the top-level facade + canonical.crosscutting + canonical.domain.
    # The other protocol-specific symbols (gcs_bucket, bigquery_dataset, etc.) are still blocked.
    PROTOCOL_VIOLATIONS=$(rg "upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
        --type py --glob '!.venv*' --glob '!**/.venv*/**' --glob '!tests' -l . 2>/dev/null || :)
elif [[ "$PACKAGE_NAME" = "unified-trading-library" ]]; then
    # UTL defines/deprecates these symbols — skip the origin and compat-layer files
    # domain_client/ sub-package (merged into UTL) uses these symbols legitimately
    PROTOCOL_VIOLATIONS=$(rg "CloudTarget|upload_to_gcs_batch|StandardizedDomainCloudService" \
        --type py --glob '!.venv*' --glob '!**/.venv*/**' --glob '!tests' \
        --glob '!**/domain/standardized_service.py' --glob '!**/__init__.py' \
        --glob '!**/core/cloud_config.py' --glob '!**/core/cloud_data_provider.py' \
        --glob '!**/domain/data_completion.py' \
        --glob '!**/domain_client/cloud_target.py' --glob '!**/domain_client/factories.py' \
        --glob '!**/domain_client/cloud_data_provider.py' --glob '!**/domain_client/clients/**' \
        --glob '!**/domain_client/sports/**' --glob '!**/domain_client/standardized_service.py' \
        -l . 2>/dev/null \
        | grep -v "# noqa:.*qg-protocol-symbol\|# noqa: qg-protocol-symbol" || :)
else
    PROTOCOL_VIOLATIONS=$(rg "CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
        --type py --glob '!.venv*' --glob '!**/.venv*/**' --glob '!tests' -l . 2>/dev/null || :)
fi
[[ -n "$PROTOCOL_VIOLATIONS" ]] && {
    log_fail "STEP 5.11: Protocol-specific symbols found. Use get_data_sink() / get_event_bus() from UCI instead:"
    echo "$PROTOCOL_VIOLATIONS"
    V=$(( V + 1 ))
} || log_success "STEP 5.11: No protocol-specific symbols in library code"

# ============================================================
# STEP 5.13 — Schema canonical name collision (advisory)
# ============================================================
SCHEMA_COLLISION=$(rg 'class\s+Canonical[A-Z]\w+\s*\(' \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!tests' \
    "$SOURCE_DIR/" 2>/dev/null | grep -v 'unified_api_contracts\|unified_internal_contracts' || :)
[ -n "$SCHEMA_COLLISION" ] && {
    log_warn "STEP 5.13: Canonical* BaseModel subclass in library source — potential name collision with UAC/UIC canonical:"
    log_warn "See: cursor-rules/core/schema-governance-index.mdc (Rule 5)"
    echo "$SCHEMA_COLLISION" | head -5
}

# ============================================================
# STEP 5.21 — basedpyright zero-warning policy
# ============================================================
if [ -f "pyproject.toml" ]; then
    BP_VIOLATIONS=()
    # Only check the top-level [tool.basedpyright] section — not per-file [[overrides]]
    _BP_TOPLEVEL=$(awk '/^\[tool\.basedpyright\]/{p=1} /^\[\[tool\.basedpyright\.overrides\]\]/{p=0} p' pyproject.toml 2>/dev/null || :)
    for rule in reportAny reportUnknownVariableType reportUnknownParameterType reportUnknownMemberType reportUnknownArgumentType reportUnknownLambdaType; do
        if echo "$_BP_TOPLEVEL" | grep -qE "^\s*${rule}\s*=\s*[\"'](warning|none)[\"']" 2>/dev/null; then
            BP_VIOLATIONS+=("$rule is set to warning/none — must be \"error\" or omitted")
        fi
    done
    if [ "${#BP_VIOLATIONS[@]}" -gt 0 ]; then
        for v in "${BP_VIOLATIONS[@]}"; do log_fail "STEP 5.21: $v"; done
        V=$(( V + 1 ))
    else
        log_success "STEP 5.21: basedpyright Any/Unknown rules OK"
    fi
fi

# ============================================================
# STEP 5.22 — basedpyright baseline suppression audit
# Zero-baseline policy (enforced as ERROR 2026-03-10):
#   • Present (any state)  → FAIL: baseline suppression not allowed; delete the file
#   • Not present          → PASS (clean)
# ============================================================
if [ -f ".basedpyright-baseline.json" ]; then
    log_fail "STEP 5.22: .basedpyright-baseline.json present — baseline suppression not allowed (zero-baseline policy)"; V=$(( V + 1 ))
else
    log_success "STEP 5.22: no basedpyright baseline (clean)"
fi

# Conditional pip check (only if Dockerfile or shell scripts exist)
if [ -f "Dockerfile" ]; then
    PIP=$(rg "^RUN pip install|^RUN python -m pip" Dockerfile 2>/dev/null | grep -v "uv pip install" | grep -v "pip install uv" | grep -v "#" || :)
    [[ -n "$PIP" ]] && { log_fail "Use 'uv pip install' not 'pip install' in Dockerfile"; echo "$PIP" | head -3; V=$(( V + 1 )); } || log_success "No bare pip install in Dockerfile"
fi
PIP_SH=$(rg " pip install " --glob "**/*.sh" --glob "!unified-trading-pm/**" . 2>/dev/null | grep -v "uv pip install" | grep -v "pip install uv" | grep -v "#" || :)
[[ -n "$PIP_SH" ]] && { log_fail "Use 'uv pip install' not 'pip install' in scripts"; echo "$PIP_SH" | head -3; V=$(( V + 1 )); } || log_success "No bare pip install in scripts"

_be_extra_globs=()
for _excl in "${BROAD_EXCEPT_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _be_extra_globs+=("--glob" "!${_excl}"); done
BE=$(rg "except Exception:" --type py --glob "!tests/**" "${_be_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$BE" ]] && { log_warn "broad except Exception — document in QUALITY_GATE_BYPASS_AUDIT.md"; echo "$BE" | head -5; V=$(( V + 1 )); } || log_success "No broad except Exception"

SWALLOWED=$(rg "except Exception:" --type py --glob "!tests/**" "${_be_extra_globs[@]}" "$SOURCE_DIR/" -A 2 2>/dev/null \
    | grep -E "^[[:space:]]+(pass|return None)$" || :)
[[ -n "$SWALLOWED" ]] && { log_fail "Swallowed errors — use @handle_api_errors or re-raise"; V=$(( V + 1 )); } || log_success "No swallowed errors"

# CI/CD hygiene: ||true bypasses in quality gate scripts
BYPASS=$(rg "\|\|true|\|\| true" --glob "**/quality-gates.sh" --glob "**/quality-gates.yml" . 2>/dev/null \
    | grep -v "BYPASS —\|fix the root cause\|zombies\|pyright\|cleanup" || :)
[[ -n "$BYPASS" ]] && { log_fail "||true bypass in quality gates — fix the root cause"; echo "$BYPASS" | head -3; V=$(( V + 1 )); } || log_success "No ||true quality gate bypasses"

# File size (exclude build artifacts and test dirs — tests get warn-only treatment)
# Optional: SIZE_EXTRA_EXCLUDES array of extra ! -path patterns (set before sourcing)
SVIOL=""; SWARN=""
_size_extra_args=()
for _excl in "${SIZE_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _size_extra_args+=("!" "-path" "$_excl"); done
for f in $(find . -name "*.py" ! -path "./.venv/*" ! -path "./scripts/*" ! -path "./.git/*" ! -path "./build/*" ! -path "./unified-trading-pm/*" "${_size_extra_args[@]}" 2>/dev/null); do
    lines=$(wc -l < "$f" 2>/dev/null || echo 0)
    if [[ "$f" == ./tests/* || "$f" == ./test/* ]]; then
        # Test files: warn-only for file size (test suites naturally grow large)
        [[ "$lines" -gt $MAX_FILE_LINES ]] && SWARN="${SWARN}\n  $f: $lines L"
    else
        [[ "$lines" -gt $MAX_FILE_LINES ]] && SVIOL="${SVIOL}\n  $f: $lines L"
    fi
done
[[ -n "$SVIOL" ]] && { log_fail "Files exceed $MAX_FILE_LINES lines:$SVIOL"; V=$(( V + 1 )); } || log_success "File size OK"
[[ -n "$SWARN" ]] && log_warn "Test files exceed limit:$SWARN"

# Function/class/method size (exclude build artifacts and test dirs — test methods can be long)
FSIZES=""
for f in $(find . -name "*.py" ! -path "./.venv/*" ! -path "./scripts/*" ! -path "./.git/*" ! -path "./build/*" ! -path "./tests/*" ! -path "./test/*" ! -path "./unified-trading-pm/*" "${_size_extra_args[@]}" 2>/dev/null); do
    out=$($PYTHON_CMD -c "
import ast, sys
p=sys.argv[1]
try:
  with open(p,'r',encoding='utf-8') as fp: tree=ast.parse(fp.read())
  def v(n,par=None):
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
      l=(n.end_lineno or n.lineno)-n.lineno+1
      if isinstance(par,ast.ClassDef): l>$MAX_METHOD_LINES and print(f'  {p}:{n.lineno}:{par.name}.{n.name}(): {l}L')
      elif l>$MAX_FUNCTION_LINES: print(f'  {p}:{n.lineno}:{n.name}(): {l}L')
    elif isinstance(n,ast.ClassDef):
      l=(n.end_lineno or n.lineno)-n.lineno+1
      l>$MAX_CLASS_LINES and print(f'  {p}:{n.lineno}:{n.name}: {l}L')
    for c in ast.iter_child_nodes(n): v(c,n if isinstance(n,ast.ClassDef) else par)
  v(tree)
except: pass
" "$f" 2>/dev/null || :)
    [[ -n "$out" ]] && FSIZES="${FSIZES}\n${out}"
done
[[ -n "$FSIZES" ]] && { log_fail "Function/class/method size exceeded:$FSIZES"; V=$(( V + 1 )); } || log_success "Function/class/method size OK"

# Security: pip-audit (prefer project venv to avoid workspace transitive vulns)
if $PYTHON_CMD -c "import pip_audit" 2>/dev/null; then
    # CVE-2026-4539: pygments 2.19.2 (latest, no fix version) — transitive via pytest+rich
    # CVE-2026-45409: idna 3.14 follow-up to CVE-2024-3651; fix: upgrade to idna>=3.15
    # CVE-2026-34993: aiohttp <=3.13.5 CookieJar.load() RCE on UNTRUSTED input. fix_versions=[3.14.0] BUT 3.14.0
    #   removed aiohttp.streams.AsyncStreamReaderMixin → breaks vcrpy 8.1.1 (latest) MockStream fleet-wide (64 VCR
    #   AttributeError). These libs use aiohttp as a client and never CookieJar.load() untrusted files → surface nil.
    #   SUCCESSOR: bump aiohttp>=3.14 + vcrpy when vcrpy ships aiohttp-3.14 compat. Tracked:
    #   plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md.
    # CVE-2026-47265: aiohttp <=3.13.5 cookies re-sent after cross-origin redirect; fix_versions=[3.14.0] (same
    #   vcrpy block). The aiohttp-3.13.5 CVE set grows until the fleet can reach 3.14.0 (vcrpy-unblock).
    _pa_extra="${PIP_AUDIT_EXTRA_ARGS:-} --ignore-vuln CVE-2026-4539 --ignore-vuln CVE-2026-45409 --ignore-vuln CVE-2026-34993 --ignore-vuln CVE-2026-47265"
    _pa_out=$($PYTHON_CMD -m pip_audit $_pa_extra 2>&1) || { echo "$_pa_out"; log_fail "pip-audit vulnerabilities"; V=$(( V + 1 )); }
elif command -v pip-audit &>/dev/null; then
    _pa_out=$(pip-audit 2>&1) || { echo "$_pa_out"; log_fail "pip-audit vulnerabilities"; V=$(( V + 1 )); }
else
    log_fail "pip-audit required: uv pip install pip-audit"; V=$(( V + 1 ))
fi

# Security: bandit (use python -m bandit for venv reliability)
if $PYTHON_CMD -c "import bandit" 2>/dev/null; then
    _bandit_out=$(run_timeout 30 $PYTHON_CMD -m bandit -r "$SOURCE_DIR/" -ll 2>&1) \
        || { echo "$_bandit_out"; log_fail "bandit issues"; V=$(( V + 1 )); }
else
    log_fail "bandit required: uv pip install bandit"; V=$(( V + 1 ))
fi

# ============================================================
# STEP 5.23 — UAC import surface enforcement
# Only facade imports allowed: from unified_api_contracts.{domain} import X
# Deep imports into canonical/, normalize_utils/, config/, shared/, schemas/ are blocked.
# Exempt repos: UAC itself, UIC, SIT (auto-detected by PACKAGE_NAME or UAC_CANONICAL_EXEMPT=true).
# ============================================================
_UAC_EXEMPT="${UAC_CANONICAL_EXEMPT:-false}"
[[ "${PACKAGE_NAME:-}" == "unified-api-contracts" ]] && _UAC_EXEMPT=true
if [[ "$_UAC_EXEMPT" != "true" ]]; then
  DEEP_UAC_IMPORTS=0
  rg 'from unified_api_contracts\.canonical\.' "$SOURCE_DIR/" --glob '!**/test_*' --glob '!**/conftest*' --type py 2>/dev/null && DEEP_UAC_IMPORTS=1 || :
  rg 'from unified_api_contracts\.normalize_utils\.' "$SOURCE_DIR/" --type py 2>/dev/null && DEEP_UAC_IMPORTS=1 || :
  rg 'from unified_api_contracts\.config\.' "$SOURCE_DIR/" --type py 2>/dev/null && DEEP_UAC_IMPORTS=1 || :
  rg 'from unified_api_contracts\.shared\.' "$SOURCE_DIR/" --type py 2>/dev/null && DEEP_UAC_IMPORTS=1 || :
  rg 'from unified_api_contracts\.schemas\.' "$SOURCE_DIR/" --type py 2>/dev/null && DEEP_UAC_IMPORTS=1 || :
  if [[ $DEEP_UAC_IMPORTS -eq 1 ]]; then
    log_fail "STEP 5.23: Deep UAC import detected. Use facade: from unified_api_contracts.{domain} import X"
    rg 'from unified_api_contracts\.(canonical|normalize_utils|config|shared|schemas)\.' "$SOURCE_DIR/" --type py 2>/dev/null | head -10
    V=$(( V + 1 ))
  else
    log_success "STEP 5.23: UAC import surface clean"
  fi
else
  log_success "STEP 5.23: UAC import surface (exempt repo)"
fi

# STEP 5.24 — No `# type: ignore` (OPT-IN: ENFORCE_NO_TYPE_IGNORE=true in repo quality-gates.sh).
# `# type: ignore` is a BLANKET suppress-all — basedpyright ignores the bracketed codes and
# hides EVERY error on the line (proven), so it masks future bugs. Use precise
# `# pyright: ignore[reportX]` (suppresses only the named rule). Banned workspace-wide
# (CLAUDE.md "No # type: ignore"); enforced per-repo once converted so it does not break
# un-converted fleet repos. Scope mirrors basedpyright (excludes tests/ + **/testing/**).
if [[ "${ENFORCE_NO_TYPE_IGNORE:-false}" == "true" ]]; then
  _TYPE_IGNORE_HITS=$(rg -n '# type: ignore' "$SOURCE_DIR/" --type py --glob '!tests/**' --glob '!**/testing/**' 2>/dev/null || :)
  if [[ -n "$_TYPE_IGNORE_HITS" ]]; then
    log_fail "STEP 5.24: # type: ignore is banned (blanket suppress-all) — use precise # pyright: ignore[reportX]"
    echo "$_TYPE_IGNORE_HITS" | head -10
    V=$(( V + 1 ))
  else
    log_success "STEP 5.24: No # type: ignore (precise # pyright: ignore[rule] only)"
  fi
fi

# CODEX_MAX_VIOLATIONS: repos with pre-existing violations can set a ceiling.
# The goal is to ratchet this down to 0 over time.
_max_v=${CODEX_MAX_VIOLATIONS:-0}
if [[ $V -gt $_max_v ]]; then
    log_fail "Codex compliance FAILED: $V violations (max allowed: $_max_v)"
    exit 1
fi
log_success "Codex compliance PASSED"

# ── [5.6] DEAD CODE DETECTION (vulture — warn/fail thresholds) ───────────────
# vulture detects unused functions, classes, and variables.
# Repos may opt out of specific symbols by adding a .vulture-whitelist.py file
# (list each unused-but-intentional name as an attribute access, e.g. _.my_hook).
if command -v vulture &>/dev/null; then
    log_section "[5.6/6] DEAD CODE DETECTION (vulture)"
    _VULTURE_WHITELIST=""
    [ -f ".vulture-whitelist.py" ] && _VULTURE_WHITELIST=".vulture-whitelist.py"
    _DEAD_CODE=$(run_timeout 60 vulture "$SOURCE_DIR" ${_VULTURE_WHITELIST} \
        --min-confidence 80 2>/dev/null | wc -l | tr -d ' ')
    if [ "${_DEAD_CODE:-0}" -gt 100 ]; then
        log_fail "Dead code FAILED: vulture found ${_DEAD_CODE} unused items (threshold: 100) — remove dead code or add to .vulture-whitelist.py"
        exit 1
    elif [ "${_DEAD_CODE:-0}" -gt 20 ]; then
        log_warn "Dead code WARN: vulture found ${_DEAD_CODE} unused items (review recommended; threshold: 20)"
    else
        log_ok "Dead code check PASSED (${_DEAD_CODE} items)"
    fi
else
    log_warn "vulture not found — skipping dead-code check (install: uv pip install vulture)"
fi

# ── STEP 5.72: chain-set inclusion invariant on UAC chain_env ─────────────────
# Mirrors base-service.sh STEP 5.72. Enforces
# MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES ⊇ GAS_FEE_CHAIN_START_DATES on the
# UAC chain_env registries. Closes cross_asset_group_catalogue_audit Phase
# 1F-extend (DF-7).
_CHAIN_INCLUSION_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_chain_set_inclusion.py"
if [ -f "$_CHAIN_INCLUSION_CHECKER" ]; then
    if $PYTHON_CMD "$_CHAIN_INCLUSION_CHECKER" >/tmp/chain_set_inclusion_qg_lib.log 2>&1; then
        log_ok "STEP 5.72: UAC chain_env MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES ⊇ GAS_FEE_CHAIN_START_DATES"
    else
        log_fail "STEP 5.72: UAC chain_env inclusion invariant violated (DF-7). Output:"
        cat /tmp/chain_set_inclusion_qg_lib.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_chain_set_inclusion.py"
        exit 1
    fi
fi

# ── STEP 5.83: UAC InstrumentRecord hard-schema enforcement guard ─────────────
# Verifies InstrumentRecord._enforce_per_asset_group_required_fields() model_validator
# + CEFI_PAIR_INSTRUMENT_TYPES / DEFI_ONCHAIN_INSTRUMENT_TYPES frozensets exist in
# unified_api_contracts/internal/reference/instrument.py.
# Guards hard_schema_enforcement_2026_05_08 Phase 1 regression (model_validator
# enforces non-empty required fields per asset_group: CeFi base/quote, DeFi pool
# address, EVENT_CONTRACT expiry). Only runs for UAC (UAC_CANONICAL_EXEMPT=true).
_UAC_INSTRUMENT_VALIDATOR_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_uac_instrument_record_validator.py"
if [ "${UAC_CANONICAL_EXEMPT:-false}" = "true" ] && [ -f "$_UAC_INSTRUMENT_VALIDATOR_CHECKER" ]; then
    if $PYTHON_CMD "$_UAC_INSTRUMENT_VALIDATOR_CHECKER" >/tmp/uac_instrument_validator_qg.log 2>&1; then
        log_ok "STEP 5.83: UAC InstrumentRecord hard-schema enforcement validator present (hard_schema Phase 1 guard)"
    else
        log_fail "STEP 5.83: UAC InstrumentRecord hard-schema enforcement MISSING or BROKEN:"
        cat /tmp/uac_instrument_validator_qg.log
        log_fail "         Fix: restore _enforce_per_asset_group_required_fields() in InstrumentRecord"
        exit 1
    fi
fi

# ── STEP 5.85: UAC SourceCapability structured venue metadata guard ────────────
# Verifies every SourceCapability(...) instance in capability_declarations/_*.py
# has explicit chain= and kind= kwargs (even if set to None). Guards regression
# where new venue declarations omit the Phase 2 metadata fields.
# Only runs for UAC (UAC_CANONICAL_EXEMPT=true).
_UAC_SOURCE_CAPABILITY_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_uac_source_capability_metadata.py"
if [ "${UAC_CANONICAL_EXEMPT:-false}" = "true" ] && [ -f "$_UAC_SOURCE_CAPABILITY_CHECKER" ]; then
    if $PYTHON_CMD "$_UAC_SOURCE_CAPABILITY_CHECKER" "$WORKSPACE_ROOT" >/tmp/uac_source_capability_qg.log 2>&1; then
        log_ok "STEP 5.85: UAC SourceCapability structured metadata present on all venues"
    else
        log_fail "STEP 5.85: SourceCapability instances missing chain= or kind= kwargs:"
        cat /tmp/uac_source_capability_qg.log
        log_fail "         Fix: add chain=... kind=... to each SourceCapability() call"
        exit 1
    fi
fi

# ── STEP 5.86: UAC cassette → prod-consumer linkage (orphan checker) ─────────
# Fails QG if any cassette in external/<venue>/mocks/ has no production consumer
# (import, pydantic class reference, or URL host match in a service repo).
# Allowlist: tests/cassette_orphan_allowlist.yaml (documented exceptions).
# Only runs for UAC (UAC_CANONICAL_EXEMPT=true).
# SSOT: plans/active/canary_coverage_qg_enforcement_2026_05_20.md Phase 2
_UAC_CASSETTE_LINKAGE_CHECKER="${PROJECT_ROOT}/scripts/check_cassette_prod_consumer_linkage.py"
if [ "${UAC_CANONICAL_EXEMPT:-false}" = "true" ] && [ -f "$_UAC_CASSETTE_LINKAGE_CHECKER" ]; then
    if $PYTHON_CMD "$_UAC_CASSETTE_LINKAGE_CHECKER" >/tmp/uac_cassette_linkage_qg.log 2>&1; then
        log_ok "STEP 5.86: UAC cassette→prod-consumer linkage OK (no unallowlisted orphans)"
    else
        log_fail "STEP 5.86: Unallowlisted orphan cassette(s) found:"
        cat /tmp/uac_cassette_linkage_qg.log
        exit 1
    fi
fi

# ── STEP 5.87: UAC prod-URL → cassette coverage (warn-only, tracks gap) ──────
# Warns if a production HTTP/WS host in service repos has no UAC cassette.
# Run in --warn-only mode: surfaces gaps without blocking QG.
# Fix: add cassette OR add host to scripts/quality-gates-allowlists/prod-url-no-cassette.txt
# Switch to strict mode (remove --warn-only) once coverage reaches ~80%.
# SSOT: plans/active/canary_coverage_qg_enforcement_2026_05_20.md Phase 2
_UAC_PROD_URL_CHECKER="${PROJECT_ROOT}/scripts/check_prod_url_cassette_coverage.py"
if [ "${UAC_CANONICAL_EXEMPT:-false}" = "true" ] && [ -f "$_UAC_PROD_URL_CHECKER" ]; then
    if $PYTHON_CMD "$_UAC_PROD_URL_CHECKER" --warn-only >/tmp/uac_prod_url_coverage_qg.log 2>&1; then
        if grep -q "STEP 5.87.*WARN" /tmp/uac_prod_url_coverage_qg.log 2>/dev/null; then
            log_warn "STEP 5.87: prod-URL→cassette coverage gap (run scripts/check_prod_url_cassette_coverage.py for full list)"
        else
            log_ok "STEP 5.87: All prod URL hosts have cassette coverage or are allowlisted"
        fi
    else
        log_warn "STEP 5.87: prod_url_has_cassette checker error:"
        cat /tmp/uac_prod_url_coverage_qg.log
    fi
fi

# ── STEP 5.88: No _create_empty_output / _handle_empty_tick_data re-introduction ─
# Grep-based regression guard: catches the banned NaN-placeholder pattern
# (_create_empty_output, _handle_empty_tick_data) being re-introduced into
# library source. Services have the full AST-walk via base-service.sh STEP 5.67;
# this step adds a fast grep-level guard so library repos (UTL, UAC, etc.)
# can't silently grow the pattern either.
if [ -d "$SOURCE_DIR/" ]; then
    _placeholder_hits=$(grep -r --include="*.py" \
        -E '_create_empty_output|_handle_empty_tick_data' \
        "$SOURCE_DIR/" \
        --exclude-dir=".venv" --exclude-dir="__pycache__" 2>/dev/null || true)
    if [ -n "$_placeholder_hits" ]; then
        log_fail "STEP 5.88: Banned NaN-placeholder method detected in ${SOURCE_DIR}/. Delete it — emit record_empty(reason=...) / record_captured() instead:"
        echo "$_placeholder_hits"
        log_fail "         (CLAUDE.md 'Honest absence vs fake placeholders' + writegate Phase 2.A contract)"
        exit 1
    else
        log_ok "STEP 5.88: No banned NaN-placeholder methods (_create_empty_output / _handle_empty_tick_data)"
    fi
fi

# ── STEP 5.92: bar-edge open-edge (left) ingestion detector ───────────────────
# Library-repo parity with base-service.sh STEP 5.92. A closed OHLCV candle must
# be stamped on its RIGHT/close edge; a vendor bar-START (open/left) field stamped
# without a close conversion is look-ahead leakage. Baseline-ratchet.
# SSOT: bar_edge_left_vs_right_remediation_2026_06_08.md Phase 0.
_BAR_EDGE_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_bar_edge_open_ingestion.py"
if [ -f "$_BAR_EDGE_CHECKER" ]; then
    _BE_REPO=$(basename "$PROJECT_ROOT")
    _BE_SRC_ARG=()
    [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ] && _BE_SRC_ARG=(--source-dir "$SOURCE_DIR")
    if "${PYTHON_CMD:-python3}" "$_BAR_EDGE_CHECKER" \
            --workspace-root "$REPO_ROOT" --scope "$_BE_REPO" "${_BE_SRC_ARG[@]}" >/tmp/bar_edge_open_ingestion_qg.log 2>&1; then
        log_ok "STEP 5.92: No NEW open-edge (left) bar ingestion (closed candles stamped on the right/close edge)"
    else
        log_fail "STEP 5.92: NEW open-edge (left) bar ingestion site (not baselined). Use the vendor close field or compute_bar_close_boundary(open_ts, timeframe) → t_close:"
        cat /tmp/bar_edge_open_ingestion_qg.log
        exit 1
    fi
fi

# ── STEP 5.93: canonical data-model regression detector ───────────────────────
# Library-repo parity with base-service.sh STEP 5.93 (coarse pipeline_mode /
# exact-coarse reader probe). Baseline-ratchet. (No data_type=options_chain
# check — it's a legitimate Era-B snapshot data_type, name-collided with the
# instrument_type; Era-A is a runtime _LEGAL_DATA_TYPES concern.)
# SSOT: audit_criteria_automation_2026_06_08.md Tier-2.
_CANON_MODEL_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_canonical_model_regressions.py"
if [ -f "$_CANON_MODEL_CHECKER" ]; then
    _CM_REPO=$(basename "$PROJECT_ROOT")
    _CM_SRC_ARG=()
    [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ] && _CM_SRC_ARG=(--source-dir "$SOURCE_DIR")
    if "${PYTHON_CMD:-python3}" "$_CANON_MODEL_CHECKER" \
            --workspace-root "$REPO_ROOT" --scope "$_CM_REPO" "${_CM_SRC_ARG[@]}" >/tmp/canonical_model_regressions_qg.log 2>&1; then
        log_ok "STEP 5.93: No NEW coarse pipeline_mode / exact-coarse reader / Era-A chain-write regressions"
    else
        log_fail "STEP 5.93: NEW canonical-model regression (not baselined). Use source-aware batch_<source> / prefix-match readers / Era-B data_type=trades for chains:"
        cat /tmp/canonical_model_regressions_qg.log
        exit 1
    fi
fi

# ── [6] PRODUCTION READINESS (informational) ──────────────────────────────────
log_section "[6/6] PRODUCTION READINESS VALIDATORS"
VSCRIPT="${REPO_ROOT}/unified-trading-pm/codex/scripts/run-all-validators.sh"
if [ -f "$VSCRIPT" ]; then
    if ! "$VSCRIPT" --asset-group all --failed-only; then
        log_fail "Production readiness validators FAILED — fix workspace-manifest.json / plans (run: python3 unified-trading-pm/scripts/run_validators.py --scope all)"
        exit 1
    fi
    log_ok "Production readiness validators PASSED"
else
    log_fail "Production readiness validators missing — expected ${VSCRIPT}"
    exit 1
fi

# ── [ACT] GITHUB ACTIONS SIMULATION (opt-in via --act) ───────────────────────
if [ "$ACT_MODE" = true ]; then
    log_section "[ACT] GitHub Actions Simulation"
    if ! command -v act &>/dev/null; then
        OS="$(uname -s)"
        if [ "$OS" = "Darwin" ] && command -v brew &>/dev/null; then
            brew install act
        elif [ "$OS" = "Linux" ]; then
            INSTALL_DIR="${HOME}/.local/bin"
            mkdir -p "$INSTALL_DIR"
            curl -fsSL https://raw.githubusercontent.com/nektos/act/master/install.sh | bash -s -- -b "$INSTALL_DIR"
            export PATH="$INSTALL_DIR:$PATH"
        else
            log_fail "act not found — install: https://github.com/nektos/act"; exit 1
        fi
    fi
    ACT_SECRETS_ARG=""
    for _sp in "${ACT_SECRETS_FILE:-}" "${REPO_ROOT}/.act-secrets" "${HOME}/.secrets"; do
        [ -n "$_sp" ] && [ -f "$_sp" ] && { ACT_SECRETS_ARG="--secret-file $_sp"; break; }
    done
    _ACT_LOG="$(mktemp /tmp/act-output.XXXXXX)"
    if act -j quality-gates --container-architecture linux/amd64 ${ACT_SECRETS_ARG} 2>&1 | tee "$_ACT_LOG"; then
        log_success "Act simulation PASSED"
    else
        log_fail "Act simulation FAILED — full act output:"
        cat "$_ACT_LOG" >&2
        [ -z "$ACT_SECRETS_ARG" ] && log_warn "No .act-secrets found at ${REPO_ROOT}/.act-secrets or ~/.secrets — GH_PAT may be missing"
        log_warn "Fix: bash unified-trading-pm/scripts/workspace/generate-act-secrets.sh"
        rm -f "$_ACT_LOG"
        exit 1
    fi
    rm -f "$_ACT_LOG"
fi


# ── RECORD LOCAL PASS (ci_status=LOCAL_PASS when not in CI) ──────────────────
if ! _qg_update_ci_status_pass; then
    log_fail "Failed to update ci_status (LOCAL_PASS) in workspace-manifest.json"
    exit 1
fi
# DAG SVGs are GITIGNORED generated artifacts (item H, 2026-06-03): regenerate them on every local
# QG run so the codex/04-architecture symlinks stay fresh — gitignored output → zero worktree churn.
# The former MANIFEST_STATE_WRITER gate (single-writer-cron era, when these were tracked) is removed;
# ci_status gating is unaffected (it lives in _qg_update_ci_status_pass above).
if [[ "${GITHUB_ACTIONS:-}" != "true" ]]; then
    _MANIFEST="${REPO_ROOT}/unified-trading-pm/workspace-manifest.json"
    if [[ -f "$_MANIFEST" ]] && command -v python3 &>/dev/null; then
        _DAG_SCRIPT="${REPO_ROOT}/unified-trading-pm/scripts/manifest/generate_workspace_dag.py"
        if [[ -f "$_DAG_SCRIPT" ]]; then
            if ! python3 "$_DAG_SCRIPT"; then
                log_fail "Failed to regenerate WORKSPACE_MANIFEST_DAG.svg"
                exit 1
            fi
        fi
        _DATA_FLOW_SCRIPT="${REPO_ROOT}/unified-trading-pm/scripts/manifest/generate_data_flow_dag.py"
        if [[ -f "$_DATA_FLOW_SCRIPT" ]]; then
            if ! python3 "$_DATA_FLOW_SCRIPT"; then
                log_fail "Failed to regenerate DATA_FLOW_DAG.svg"
                exit 1
            fi
        fi
    fi
fi

# ── DURATION CHECK ───────────────────────────────────────────────────────────
MAX_DURATION=${MAX_DURATION:-300}
QG_END=$(date +%s); DUR=$((QG_END - QG_START))
[ $DUR -gt $MAX_DURATION ] && { log_fail "Quality gates must complete in <${MAX_DURATION}s (took ${DUR}s)"; exit 1; }
echo -e "\n${GREEN}======================================================================"
echo -e "✅ ALL QUALITY GATES PASSED (${DUR}s)${NC}"
# ── QG SENTINEL (SHA fingerprint for quickmerge --agent fast-path) — mirror of
# base-service.sh. Library repos were MISSING this write (only the content sentinel
# below), so `quickmerge --agent` always saw .qg_last_passed_sha "missing" and hard-refused
# every LIBRARY repo fleet-wide. H5: do NOT refresh on a content-sentinel HIT (a HIT skipped
# the tests/typecheck phases; refreshing would let quickmerge ship without re-running tests).
# Written to PROJECT_ROOT (the gated repo root — where quickmerge --agent reads it), same dir
# as the content sentinel below. Guarded identically to that write (full green: tests ran, not quick).
if [ "${QUICK_MODE:-false}" = false ] && [ "${RUN_TESTS:-false}" = true ] && [ -z "${QG_SLICE:-}" ] && [ "${_QG_SENTINEL_HIT:-false}" != true ]; then
    git rev-parse HEAD > "${PROJECT_ROOT}/.qg_last_passed_sha" 2>/dev/null \
        && echo "Sentinel written: .qg_last_passed_sha=$(cat "${PROJECT_ROOT}/.qg_last_passed_sha")" \
        || echo "Warning: could not write .qg_last_passed_sha (non-git dir?)"
fi
# Green content sentinel (qg-repo-green-sentinel): record on a full green so an
# unchanged tree skips the heavy phases next run. See base-service.sh for rationale.
if [ "${#_QG_CONTENT_HASH}" -eq 64 ] && [ "${QUICK_MODE:-false}" = false ] && [ "${RUN_TESTS:-false}" = true ] && [ -z "${QG_SLICE:-}" ]; then
    echo "$_QG_CONTENT_HASH" > "${PROJECT_ROOT}/.qg_content_sentinel" 2>/dev/null \
        && echo "Green sentinel written: .qg_content_sentinel (unchanged tree → fast green next run)" || true
fi
