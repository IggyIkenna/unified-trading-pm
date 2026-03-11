#!/usr/bin/env bash
# quality-gates-base-service v1.0 — owned by unified-trading-pm
#
# Shared quality-gate body for Python service repos.
# Do NOT edit per-repo — this file is the SSOT for all service gate logic.
# To add a new check for all services, edit this file only.
#
# Required caller variables (set before sourcing this file):
#   SERVICE_NAME      — e.g. "features-calendar-service"
#   SOURCE_DIR        — e.g. "features_calendar_service"
#   MIN_COVERAGE      — e.g. 70
#   RUN_INTEGRATION   — e.g. false
#   PYTEST_WORKERS    — e.g. ${PYTEST_WORKERS:-2}
#   LOCAL_DEPS        — e.g. ("unified-events-interface")
#
# Optional caller variables:
#   MAX_DURATION      — duration limit in seconds (default: 120); set to 300 for PM/codex
#
# Version guard (optional): declare EXPECTED_BASE_VERSION="1.0" in stub before sourcing.
#
REQUIRED_BASE_VERSION="1.0"
if [[ -n "${EXPECTED_BASE_VERSION:-}" && "$EXPECTED_BASE_VERSION" != "$REQUIRED_BASE_VERSION" ]]; then
    echo "⚠️  Stub expects base v${EXPECTED_BASE_VERSION} but base is v${REQUIRED_BASE_VERSION}" >&2
fi

# ── REQUIRED VARIABLE VALIDATION ──────────────────────────────────────────────
_qg_missing=()
[[ -z "${SERVICE_NAME:-}" ]]    && _qg_missing+=("SERVICE_NAME")
[[ -z "${SOURCE_DIR:-}" ]]      && _qg_missing+=("SOURCE_DIR")
[[ -z "${MIN_COVERAGE+x}" ]]    && _qg_missing+=("MIN_COVERAGE")
[[ -z "${RUN_INTEGRATION+x}" ]] && _qg_missing+=("RUN_INTEGRATION")
if [[ ${#_qg_missing[@]} -gt 0 ]]; then
    echo "❌ base-service.sh: required variables not set: ${_qg_missing[*]}" >&2
    echo "   Set these in your repo's quality-gates.sh before sourcing base-service.sh." >&2
    exit 1
fi
unset _qg_missing

# ── CI RUNTIME ENV VAR ENFORCEMENT (GitHub Actions only) ──────────────────────
if [[ "${CI:-}" == "true" ]]; then
    _ci_missing=()
    [[ "${CLOUD_MOCK_MODE:-}" != "true" ]] && _ci_missing+=("CLOUD_MOCK_MODE=true")
    [[ -z "${GCP_PROJECT_ID:-}" ]]         && _ci_missing+=("GCP_PROJECT_ID")
    [[ -z "${CLOUD_PROVIDER:-}" ]]         && _ci_missing+=("CLOUD_PROVIDER")
    if [[ ${#_ci_missing[@]} -gt 0 ]]; then
        echo "❌ base-service.sh: CI env vars not set: ${_ci_missing[*]}" >&2
        echo "   Add these to your workflow env: block." >&2
        exit 1
    fi
    unset _ci_missing
fi

set -e

QG_START=$(date +%s)
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_section() { echo -e "\n${BLUE}$1${NC}"; echo "----------------------------------------------------------------------"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_fail()    { echo -e "${RED}❌ $1${NC}"; }
log_warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }

# When sourced, BASH_SOURCE[0] is this base script (in PM); BASH_SOURCE[1] is the caller stub.
# We derive PROJECT_ROOT from the stub's location (the repo that sourced us).
_BASE_CALLER="${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}"
SCRIPT_DIR="$(cd "$(dirname "$_BASE_CALLER")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="${REPO_ROOT:-$(dirname "$PROJECT_ROOT")}"
cd "$PROJECT_ROOT"
unset _BASE_CALLER

# ── SIZE LIMITS (per coding standards) ────────────────────────────────────────
MAX_FILE_LINES=900; FILE_WARN_LINES=700
MAX_FUNCTION_LINES=200; MAX_CLASS_LINES=900; MAX_METHOD_LINES=50

# ── PORTABLE TIMEOUT ──────────────────────────────────────────────────────────
run_timeout() {
    local secs=$1; shift
    if command -v timeout &>/dev/null; then timeout "$secs" "$@"
    elif command -v gtimeout &>/dev/null; then gtimeout "$secs" "$@"
    elif command -v perl &>/dev/null; then perl -e 'alarm shift; exec @ARGV' -- "$secs" "$@"
    else "$@"; fi
}

# ── MODE ──────────────────────────────────────────────────────────────────────
FIX_MODE=true; QUICK_MODE=false; RUN_LINT=true; RUN_TESTS=true; SKIP_TYPECHECK=false; ACT_MODE=false
for arg in "$@"; do
    case $arg in
        --no-fix) FIX_MODE=false ;;   --quick) QUICK_MODE=true ;;
        --lint) RUN_TESTS=false ;;    --test) RUN_LINT=false ;;
        --skip-tests) RUN_TESTS=false ;;
        --fix) FIX_MODE=true ;;       --skip-typecheck) SKIP_TYPECHECK=true ;;
        --act) ACT_MODE=true ;;
    esac
done

# ── BOOTSTRAP (local only; CI has its own setup) ─────────────────────────────
if [ -z "${GITHUB_ACTIONS:-}" ] && [ -z "${CI:-}" ] && [ -z "${CLOUD_BUILD:-}" ]; then
    command -v uv &>/dev/null || pip install uv --quiet
    uv lock 2>/dev/null || :
    [ ! -d ".venv" ] && uv venv .venv
    [ -f ".venv/bin/activate" ] && source .venv/bin/activate || :
    for lib in "${LOCAL_DEPS[@]}"; do
        [ -d "${REPO_ROOT}/$lib" ] && uv pip install -e "${REPO_ROOT}/$lib" --quiet 2>/dev/null || :
    done
    uv pip install -e ".[dev]" --quiet 2>/dev/null || uv pip install -e . --quiet 2>/dev/null || :
fi
PYTHON_CMD=".venv/bin/python"; [ ! -f "$PYTHON_CMD" ] && PYTHON_CMD="python3"

# Git-aware: only check staged files when committing
STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | grep '\.py$' | tr '\n' ' ' || :)
SOURCE_DIRS="${STAGED:-$SOURCE_DIR/ tests/}"
[ -n "$STAGED" ] && log_warn "Git-aware mode: $(echo "$STAGED" | wc -w | tr -d ' ') staged files"

export CLOUD_MOCK_MODE="true"; export GCP_PROJECT_ID="test-project"

# ── EMULATOR REACHABILITY CHECK (warn-only; emulators optional in local dev) ──
check_emulator_reachability() {
    if [[ "${CLOUD_MOCK_MODE:-}" == "true" ]]; then
        if [[ -n "${PUBSUB_EMULATOR_HOST:-}" ]]; then
            local ps_host ps_port
            ps_host=$(echo "$PUBSUB_EMULATOR_HOST" | cut -d: -f1)
            ps_port=$(echo "$PUBSUB_EMULATOR_HOST" | cut -d: -f2)
            if nc -z "$ps_host" "$ps_port" 2>/dev/null; then
                log_success "EMULATOR CHECK: PUBSUB reachable ($PUBSUB_EMULATOR_HOST)"
            else
                log_warn "EMULATOR CHECK: PUBSUB not reachable ($PUBSUB_EMULATOR_HOST) — warning only; CI injects emulators via env"
            fi
        fi
        if [[ -n "${STORAGE_EMULATOR_HOST:-}" ]]; then
            local gcs_url gcs_host gcs_port
            gcs_url="${STORAGE_EMULATOR_HOST#http://}"
            gcs_url="${gcs_url#https://}"
            gcs_host=$(echo "$gcs_url" | cut -d: -f1)
            gcs_port=$(echo "$gcs_url" | cut -d: -f2)
            if nc -z "$gcs_host" "$gcs_port" 2>/dev/null; then
                log_success "EMULATOR CHECK: GCS (STORAGE) reachable ($STORAGE_EMULATOR_HOST)"
            else
                log_warn "EMULATOR CHECK: GCS (STORAGE) not reachable ($STORAGE_EMULATOR_HOST) — warning only; CI injects emulators via env"
            fi
        fi
        if [[ -n "${BIGQUERY_EMULATOR_HOST:-}" ]]; then
            local bq_host bq_port
            bq_host=$(echo "$BIGQUERY_EMULATOR_HOST" | cut -d: -f1)
            bq_port=$(echo "$BIGQUERY_EMULATOR_HOST" | cut -d: -f2)
            if nc -z "$bq_host" "$bq_port" 2>/dev/null; then
                log_success "EMULATOR CHECK: BIGQUERY reachable ($BIGQUERY_EMULATOR_HOST)"
            else
                log_warn "EMULATOR CHECK: BIGQUERY not reachable ($BIGQUERY_EMULATOR_HOST) — warning only; CI injects emulators via env"
            fi
        fi
    fi
}

# ── [0] ENVIRONMENT ────────────────────────────────────────────────────────────
log_section "[0/6] ENVIRONMENT"
ACTUAL_PY=$($PYTHON_CMD --version 2>&1 | awk '{print $2}' | cut -d'.' -f1,2)
[[ "$ACTUAL_PY" != "3.13" ]] && { log_fail "Python 3.13 required, found $ACTUAL_PY"; exit 1; }; log_success "Python $ACTUAL_PY"
command -v rg &>/dev/null || { log_fail "ripgrep required: brew install ripgrep"; exit 1; }; log_success "ripgrep OK"
[ -f "pyproject.toml" ] && grep -q '>=3.13,<3.14' pyproject.toml || { log_fail "pyproject.toml: requires-python = '>=3.13,<3.14'"; exit 1; }; log_success "pyproject.toml OK"
[[ ! -f "uv.lock" ]] && log_warn "uv.lock missing" || log_success "uv.lock present"
RUFF_CMD=".venv/bin/ruff"; command -v "$RUFF_CMD" &>/dev/null || RUFF_CMD="ruff"
RUFF_VER=$($RUFF_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo "0")
[[ "$RUFF_VER" != "0.15.0" ]] && log_warn "ruff 0.15.0 expected, found $RUFF_VER" || log_success "ruff $RUFF_VER"
BASEDPYRIGHT_CMD=".venv/bin/basedpyright"; [ ! -f "$BASEDPYRIGHT_CMD" ] && BASEDPYRIGHT_CMD="basedpyright"
BP_VER=$("$BASEDPYRIGHT_CMD" --version 2>/dev/null | head -1 | awk '{print $NF}' || echo "0")
[[ "$BP_VER" != "1.38.2" ]] && log_warn "basedpyright 1.38.2 expected, found $BP_VER" || log_success "basedpyright $BP_VER"

# ── [1] AUTO-FIX (prettier + ruff, 30s each) ──────────────────────────────────
# Prettier runs FIRST on non-Python files to prevent ruff/prettier conflict in pre-commit hooks.
# Without this, committing JSON/YAML/MD files causes "MM" status and hook stash conflicts.
# See: 06-coding-standards/quality-gates.md § Formatter Conflict Resolution
if [ "$RUN_LINT" = true ] && [ "$FIX_MODE" = true ]; then
    log_section "[1/6] AUTO-FIX"
    # Pre-format non-Python files with prettier to avoid pre-commit hook conflicts
    if command -v npx &>/dev/null; then
        npx --yes prettier@3.6.2 --write --cache "**/*.{md,json,yaml,yml}" --ignore-path .gitignore $([ -f .prettierignore ] && echo "--ignore-path .prettierignore") 2>/dev/null \
            && log_success "Prettier: non-Python files formatted" \
            || log_warn "Prettier not available or no files to format (skipping)"
    else
        log_warn "npx not available — skipping prettier pre-format (commit may require re-staging)"
    fi
    run_timeout 30 $RUFF_CMD format $SOURCE_DIRS || exit 1
    run_timeout 30 $RUFF_CMD check --fix $SOURCE_DIRS || exit 1
    log_success "Auto-fix complete"
fi

# ── [2] LINT (ruff, 30s) ──────────────────────────────────────────────────────
if [ "$RUN_LINT" = true ]; then
    log_section "[2/6] LINT"
    run_timeout 30 $RUFF_CMD check $SOURCE_DIRS && log_success "Lint PASSED" || { log_fail "Lint FAILED"; exit 1; }
fi

# ── [3] TESTS (pytest, timeout, xdist, coverage) ──────────────────────────────
if [ "$RUN_TESTS" = true ]; then
    log_section "[3/6] TESTS"
    check_emulator_reachability
    $PYTHON_CMD -c "import pytest_timeout" 2>/dev/null || { log_fail "pytest-timeout required: uv pip install pytest-timeout"; exit 1; }
    $PYTHON_CMD -c "import xdist" 2>/dev/null || { log_fail "pytest-xdist required: uv pip install pytest-xdist"; exit 1; }
    COV="--cov=$SOURCE_DIR --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=$MIN_COVERAGE"
    PARGS="-n $PYTEST_WORKERS --timeout=60 -v --tb=short"
    if [ "$QUICK_MODE" = true ] || [ "$RUN_INTEGRATION" != "true" ]; then
        $PYTHON_CMD -m pytest tests/unit/ --disable-socket --allow-unix-socket $PARGS $COV || exit 1
    else
        $PYTHON_CMD -m pytest tests/unit/ tests/integration/ --disable-socket --allow-unix-socket $PARGS $COV || exit 1
    fi
    log_success "Tests PASSED"
    [ ! -f "tests/unit/test_event_logging.py" ] && { log_fail "Missing tests/unit/test_event_logging.py"; exit 1; }
    [ ! -f "tests/unit/test_config.py" ] && { log_fail "Missing tests/unit/test_config.py"; exit 1; }
    log_success "Required test files present"

    # No duplicate test files (test_*_extended.py, test_*_additional.py)
    DUP=$(find tests/ -name "test_*_extended.py" -o -name "test_*_additional.py" 2>/dev/null | head -5 || :)
    [[ -n "$DUP" ]] && { log_fail "Duplicate test files — expand existing files instead:"; echo "$DUP"; exit 1; }
    log_success "No duplicate test files"

    # @pytest.mark.skip must have a # reason: comment on the immediately preceding line
    SKIP_NO_REASON=$(python3 - <<'PYEOF' 2>/dev/null || :
import re
from pathlib import Path
violations = []
for f in sorted(Path("tests").rglob("*.py")):
    try:
        lines = f.read_text().splitlines()
    except Exception:
        continue
    for i, line in enumerate(lines):
        if re.search(r"@pytest\.mark\.skip", line):
            if "# noqa" in line:
                continue
            # skipif always carries reason= inline — not subject to this check
            if "skipif" in line:
                continue
            # reason= as argument inline satisfies the requirement
            if "reason=" in line:
                continue
            # # reason: comment on the same line satisfies the requirement
            if "# reason:" in line:
                continue
            prev = lines[i - 1].strip() if i > 0 else ""
            if "# noqa" in prev or prev.startswith("# reason:"):
                continue
            violations.append(f"{f}:{i+1}: {line.strip()}")
for v in violations:
    print(v)
PYEOF
)
    [[ -n "$SKIP_NO_REASON" ]] && { log_fail "pytest.mark.skip without reason comment — add '# reason: ...' above"; echo "$SKIP_NO_REASON" | head -3; exit 1; }
    log_success "All pytest.mark.skip have reason comments"
fi

# ── [3.5] IMPORT PATTERN STANDARDS ───────────────────────────────────────────
log_section "[3.5/6] IMPORT PATTERNS"
IP="${REPO_ROOT}/unified-trading-pm/scripts/validation/check-import-patterns.py"
[ ! -f "$IP" ] && IP="${REPO_ROOT}/unified-trading-pm/scripts/check-import-patterns.py"  # pre-move fallback
if [ -f "$IP" ]; then
    # Bypass: add --exclude flags for files whitelisted in QUALITY_GATE_BYPASS_AUDIT.md §1.2
    $PYTHON_CMD "$IP" --verbose 2>/dev/null && log_success "Import patterns PASSED" || { log_fail "Import patterns FAILED"; exit 1; }
else
    log_warn "check-import-patterns.py not found (unified-trading-pm/scripts/)"
fi

# ── [3.6] NO SERVICE-AS-PACKAGE DEPS (services only) ───────────────────────────
# Importing another service as a package is a violation; interaction is via messaging only (topology DAG SSOT).
NSD="${REPO_ROOT}/unified-trading-pm/scripts/check-no-service-deps.py"
if [ -f "$NSD" ]; then
    $PYTHON_CMD "$NSD" 2>/dev/null && log_success "No service-as-package deps" || { log_fail "Service must not depend on another service repo (use messaging per topology)"; exit 1; }
fi

# ── [4] TYPE CHECK (basedpyright, 120s, zombie cleanup) ──────────────────────
log_section "[4/6] TYPE CHECK"
if [ "$SKIP_TYPECHECK" != "true" ]; then
    cleanup_zombie_pyright() {
        ps -eo pid,etime,command 2>/dev/null | grep -E 'basedpyright.*index\.js' | grep -v grep | \
        while read -r pid etime _; do
            hours=0; echo "$etime" | grep -q '-' && hours=$(($(echo "$etime" | cut -d'-' -f1) * 24))
            [ "$(echo "$etime" | tr ':' '\n' | wc -l)" -eq 3 ] && hours=$(echo "$etime" | cut -d':' -f1)
            [ "${hours:-0}" -ge 2 ] && log_warn "Killing zombie basedpyright PID $pid" && kill -9 "$pid" 2>/dev/null || :
        done
    }
    cleanup_zombie_pyright
    [ ! -f "$BASEDPYRIGHT_CMD" ] && ! command -v basedpyright &>/dev/null && { log_fail "basedpyright required: uv pip install basedpyright==1.38.2"; exit 1; }
    # CRITICAL: always pass the source directory explicitly — never run basedpyright without a path
    # (basedpyright . analyzes the entire workspace and consumes gigabytes of RAM)
    if [ -z "$SOURCE_DIR" ] || [ "$SOURCE_DIR" = "REPLACE_ME" ]; then
        log_fail "SOURCE_DIR not set — cannot run basedpyright safely"; exit 1
    fi
    # ── BASELINE FILE GATE ────────────────────────────────────────────────────
    # Zero-baseline policy (2026-03-10): presence of .basedpyright-baseline.json is a hard block.
    # Delete the file and resolve all underlying type errors before re-running.
    if [ -f ".basedpyright-baseline.json" ]; then
        log_fail "TYPE CHECK: .basedpyright-baseline.json present — baseline suppression not allowed (zero-baseline policy); delete the file and fix all type errors"; exit 1
    fi
    export BASEDPYRIGHT_CACHE_DIR="${TMPDIR:-/tmp}/basedpyright-cache/${SERVICE_NAME:-$(basename "$PWD")}"
    mkdir -p "$BASEDPYRIGHT_CACHE_DIR"
    PYRIGHT_OUT=$(run_timeout "${PYRIGHT_TIMEOUT:-120}" "$BASEDPYRIGHT_CMD" "$SOURCE_DIR/" 2>&1); PYRIGHT_EXIT=$?
    if [ "$PYRIGHT_EXIT" -ne 0 ]; then echo "$PYRIGHT_OUT"; log_fail "Type check FAILED/timeout"; exit 1; fi
    WARN_COUNT=$(echo "$PYRIGHT_OUT" | grep -c " warning:" || :)
    if [ "${WARN_COUNT:-0}" -gt 0 ]; then
        echo "$PYRIGHT_OUT"
        log_fail "Type check FAILED — $WARN_COUNT warning(s) (zero-warning policy: promote all rules to error in [tool.basedpyright])"; exit 1
    fi
    log_success "Type check PASSED (0 errors, 0 warnings)"
fi
[ "$SKIP_TYPECHECK" = "true" ] && echo -e "${YELLOW}⚠️  Type check SKIPPED (--skip-typecheck flag)${NC}"

# ── [5] CODEX COMPLIANCE ──────────────────────────────────────────────────────
# All checks are blocking unless excluded via QUALITY_GATE_BYPASS_AUDIT.md.
# Add inline --glob exclusions below only for bypasses documented in that file.
log_section "[5/6] CODEX COMPLIANCE"
V=0

# PRINT_EXCLUDE_GLOBS: per-repo array of --glob exclusions (e.g. Rich console.print, bash template strings)
rg "print\(" --type py --glob "!tests/**" --glob "!scripts/**" "${PRINT_EXCLUDE_GLOBS[@]}" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "print() — use log_event() from UEI"; V=$(( V + 1 )); } || log_success "No print()"

# OS_ENV_EXCLUDE_GLOBS: per-repo array of --glob exclusions (e.g. bootstrap_config.py, env_substitutor.py)
rg "os\.getenv|os\.environ" --type py --glob "!tests/**" --glob "!scripts/**" --glob "!**/config.py" "${OS_ENV_EXCLUDE_GLOBS[@]}" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "os.getenv()/os.environ — use UnifiedCloudConfig for config, get_secret_client() for secrets"; V=$(( V + 1 )); } || log_success "No os.getenv()/os.environ"

rg 'os\.getenv\s*\([^)]+,\s*""\s*\)' --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "os.getenv empty fallback — fail fast"; V=$(( V + 1 )); } || log_success "No os.getenv empty fallback"

rg "datetime\.now\(\)|datetime\.utcnow\(\)" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Naive datetime — use datetime.now(timezone.utc)"; V=$(( V + 1 )); } || log_success "No naive datetime"

rg "except:" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Bare except — use specific exception"; V=$(( V + 1 )); } || log_success "No bare except"


# Bypass: add --glob exclusions for files in QUALITY_GATE_BYPASS_AUDIT.md §1.1
for f in $(rg "import requests" --type py --glob "!tests/**" --glob "!scripts/**" "$SOURCE_DIR/" -l 2>/dev/null || :); do
    grep -q "async def" "$f" && { log_fail "requests in async: $f — use aiohttp"; V=$(( V + 1 )); break; }
done; [[ ${V} -eq $(( V )) ]] && log_success "No requests in async" 2>/dev/null || :

# ASYNCIO_RUN_EXCLUDE_GLOBS: optional array set in quality-gates.sh to exclude
# known-false-positive files (asyncio.run() as entry-point in file that also has loops).
# Document each exclusion in QUALITY_GATE_BYPASS_AUDIT.md §1.1.
# Example: ASYNCIO_RUN_EXCLUDE_GLOBS=("!**/cli/batch_fetch.py")
ASYNCIO_EXTRA_GLOBS=()
for g in "${ASYNCIO_RUN_EXCLUDE_GLOBS[@]+"${ASYNCIO_RUN_EXCLUDE_GLOBS[@]}"}"; do
    ASYNCIO_EXTRA_GLOBS+=(--glob "$g")
done
for f in $(rg "asyncio\.run\(" --type py --glob "!tests/**" --glob "!scripts/**" "${ASYNCIO_EXTRA_GLOBS[@]+"${ASYNCIO_EXTRA_GLOBS[@]}"}" "$SOURCE_DIR/" -l 2>/dev/null || :); do
    grep -q "for \|while " "$f" && { log_fail "asyncio.run() in loop: $f — use asyncio.gather()"; V=$(( V + 1 )); break; }
done

# IMPORT_INSIDE_EXCLUDE_GLOBS: per-repo array of --glob exclusions (e.g. TYPE_CHECKING files)
INSIDE=$(rg "^[[:space:]]+import |^[[:space:]]+from .* import" --type py --glob "!tests/**" --glob "!**/__init__.py" \
    "${IMPORT_INSIDE_EXCLUDE_GLOBS[@]}" "$SOURCE_DIR/" 2>/dev/null || :)
# Bypass: add --glob exclusions for files in QUALITY_GATE_BYPASS_AUDIT.md §1.2
[[ -n "$INSIDE" ]] && { log_fail "Imports inside functions — move to top"; echo "$INSIDE" | head -3; V=$(( V + 1 )); } || log_success "No imports inside functions"

ANY=$(rg ": Any|-> Any|\[Any\]" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null | grep -v "type: ignore" || :)
[[ -n "$ANY" ]] && { log_fail "Any types (including dict[str, Any]) — use Pydantic models or specific types"; echo "$ANY" | head -3; V=$(( V + 1 )); } || log_success "No Any types"

# Untyped API responses — response.json() must go through model_validate(), not raw dict access
RAW_JSON=$(rg 'response\.json\(\)|await response\.json\(\)' --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v 'model_validate\|cast(dict' || :)
[[ -n "$RAW_JSON" ]] && { log_fail "Raw response.json() — parse through Pydantic model_validate()"; echo "$RAW_JSON" | head -3; V=$(( V + 1 )); } || log_success "No raw response.json()"

rg '\.get\(["\x27][\w_]+["\x27]\s*,\s*["\x27]["\x27]\)' --type py --glob "!tests/**" "${EMPTY_STR_EXCLUDE_GLOBS[@]}" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Empty string fallback — fail fast"; V=$(( V + 1 )); } || log_success "No empty string fallbacks"

ED=$(rg '\.get\s*\(\s*["\x27][^"\x27]+["\x27]\s*,\s*\{\}\s*\)' --type py --glob "!tests/**" "${EMPTY_DICT_LIST_EXCLUDE_GLOBS[@]}" "$SOURCE_DIR/" 2>/dev/null || :)
EL=$(rg '\.get\s*\(\s*["\x27][^"\x27]+["\x27]\s*,\s*\[\]\s*\)' --type py --glob "!tests/**" "${EMPTY_DICT_LIST_EXCLUDE_GLOBS[@]}" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$ED$EL" ]] && { log_fail "Empty dict/list fallback — fail fast"; V=$(( V + 1 )); } || log_success "No empty dict/list fallbacks"

rg "central-element-323112" tests/ 2>/dev/null \
    && { log_fail "Hardcoded prod project ID in tests — use 'test-project'"; V=$(( V + 1 )); } || log_success "No hardcoded project ID in tests"

rg "central-element-323112" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Hardcoded project ID in production — use config.gcp_project_id"; V=$(( V + 1 )); } || log_success "No hardcoded project ID in production"

# GCP_PROJECT_ID is legacy — only GCP_PROJECT_ID is canonical
# GCP_PROJECT_ID_EXCLUDE_GLOBS: per-repo array of --glob exclusions for legitimate GCP_PROJECT_ID usage
rg "GCP_PROJECT_ID" --type py --glob "!tests/**" --glob "!**/config.py" "${GCP_PROJECT_ID_EXCLUDE_GLOBS[@]}" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Use GCP_PROJECT_ID not GCP_PROJECT_ID (except config.py backward compat)"; V=$(( V + 1 )); } || log_success "No GCP_PROJECT_ID usage"

# GCP auth: tests must use google.auth.default() — never pytest.skip for missing credential file
# Acceptable: pytest.skip inside _skip_integration_without_creds autouse fixture (integration marker pattern)
# Domain clients must come from unified_domain_client, not unified_trading_library
# Services should import: InstrumentsDomainClient, ExecutionDomainClient, create_*_client from UDS
UCS_DOMAIN=$(rg 'from unified_trading_library import[^#]*?(InstrumentsDomainClient|ExecutionDomainClient|MarketCandleDataDomainClient|MarketTickDataDomainClient|create_instruments_client|create_execution_client|create_features_client|create_market_candle_data_client|create_market_tick_data_client)' \
    --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$UCS_DOMAIN" ]] && { log_fail "Domain clients must come from unified_domain_client, not unified_trading_library"; echo "$UCS_DOMAIN" | head -5; V=$(( V + 1 )); } || log_success "Domain clients imported from unified_domain_client"

# No domain imports from UCS (use # noqa: domain-ucs if UDC migration is pending)
DOMAIN_FROM_UCS=$(rg 'from unified_trading_library import.*(market_category|DomainValidation|UnifiedCloudServicesConfig)' \
    --type py "$SOURCE_DIR/" 2>/dev/null | grep -v '# noqa' || :)
[[ -n "$DOMAIN_FROM_UCS" ]] && { log_fail "Service imports domain symbols from UCS — use unified_domain_client instead"; echo "$DOMAIN_FROM_UCS" | head -5; V=$(( V + 1 )); } || log_success "No domain imports from UCS"

# setup_events/setup_service uses sink= in production
# Skip if this repo defines setup_events (e.g. unified-events-interface)
if rg 'def setup_events|def setup_service' --type py "$SOURCE_DIR/" -q 2>/dev/null; then
    log_success "setup_service() check skipped (repo defines setup_events/setup_service)"
else
    SETUP_NO_SINK=$(rg 'setup_(events|service)\s*\(' --type py \
        --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null | grep -v 'sink=' \
        | grep -v "def setup_events\|def setup_service" || :)
    [[ -n "$SETUP_NO_SINK" ]] && { log_fail "setup_events()/setup_service() called without sink= in production code"; echo "$SETUP_NO_SINK" | head -5; V=$(( V + 1 )); } || log_success "setup_service() uses sink= in all production call sites"
fi

BAD_AUTH_SKIP=$(rg 'pytest\.skip.*[Cc]redential|pytest\.skip.*GOOGLE_APPLICATION_CREDENTIALS|if not.*gcp_credentials.*pytest\.skip\|if not.*cred_file.*pytest\.skip' \
    --type py tests/ 2>/dev/null \
    | grep -v "_skip_integration_without_creds\|No GCP credentials.*skipping integration\|No GCP credentials.*skipping Secret Manager\|Could not create/access" \
    || :)
[[ -n "$BAD_AUTH_SKIP" ]] && { log_fail "Tests skip due to missing credential file — use google.auth.default() + @pytest.mark.integration instead"; echo "$BAD_AUTH_SKIP" | head -5; V=$(( V + 1 )); } || log_success "No credential-file skip patterns in tests"

# GOOGLE_APPLICATION_CREDENTIALS must not appear in .env.example (we use ADC / GH token / Cloud SA)
[[ -f ".env.example" ]] && rg "GOOGLE_APPLICATION_CREDENTIALS" .env.example 2>/dev/null \
    && { log_fail ".env.example contains GOOGLE_APPLICATION_CREDENTIALS — remove it (use ADC, not SA key files)"; V=$(( V + 1 )); } || log_success "No GOOGLE_APPLICATION_CREDENTIALS in .env.example"

DI=$(rg 'from unified_[a-z_]+\.[a-zA-Z0-9_.]+\s+import' --type py --glob "!tests/**" --glob "!**/__init__.py" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa" || :)
[[ -n "$DI" ]] && { log_fail "Deep unified lib imports — use top-level"; echo "$DI" | head -3; V=$(( V + 1 )); } || log_success "No deep imports"

# Old event logging pattern — must use unified_events_interface directly
EL_OLD=$(rg "from unified_trading_library[. ].*(log_event|setup_events|setup_cloud_logging|observability)" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$EL_OLD" ]] && { log_fail "Old event logging import — use 'from unified_events_interface import ...'"; echo "$EL_OLD" | head -3; V=$(( V + 1 )); } || log_success "Event logging imports from unified_events_interface"

# ============================================================
# STEP 5.5 — No direct cloud SDK imports (must route through UCLI/UCS)
# ============================================================
DIRECT_CLOUD=$(rg 'from google\.cloud import|^import boto3\b|^from boto3 import|^from botocore import' \
    --type py "${SOURCE_DIR}/" 2>/dev/null | grep -v __pycache__ | grep -v '\.venv' | grep -v '# noqa: cloud-sdk-direct' || :)
[[ -n "$DIRECT_CLOUD" ]] && {
    log_fail "Direct cloud SDK imports found (route through unified-cloud-interface instead):"
    echo "$DIRECT_CLOUD" | head -5
    V=$(( V + 1 ))
} || log_success "No direct cloud SDK imports"

# ============================================================
# STEP 5.6 — Architecture Tier Compliance
# ============================================================
REPO_ARCH_TIER="${REPO_ARCH_TIER:-service}"
if [[ "$REPO_ARCH_TIER" == "0" ]]; then
    TIER_VIOLATIONS=$(rg 'from unified_trading_library|from unified_domain_client|from unified_trading_library' \
        --type py "${SOURCE_DIR}/" 2>/dev/null | grep -v __pycache__ || :)
    [[ -n "$TIER_VIOLATIONS" ]] && {
        log_fail "Tier 0 violation: imports from Tier 1+ library:"
        echo "$TIER_VIOLATIONS" | head -5
        V=$(( V + 1 ))
    } || log_success "Tier 0 compliance: no Tier 1+ imports"
elif [[ "$REPO_ARCH_TIER" == "2" ]]; then
    TIER_VIOLATIONS=$(rg 'from unified_trading_library|from unified_trading_library' \
        --type py "${SOURCE_DIR}/" 2>/dev/null | grep -v __pycache__ || :)
    [[ -n "$TIER_VIOLATIONS" ]] && {
        log_fail "Tier 2 violation: imports from Tier 1 (unified-trading-library/unified-trading-library):"
        echo "$TIER_VIOLATIONS" | head -5
        V=$(( V + 1 ))
    } || log_success "Tier 2 compliance: no Tier 1 imports"
else
    log_success "Tier compliance skipped (REPO_ARCH_TIER=$REPO_ARCH_TIER)"
fi

# pip install anywhere other than bootstrap (must use uv pip install)
PIP=$(rg "^RUN pip install|^RUN python -m pip" --glob "**/Dockerfile" --glob "**/*.sh" . 2>/dev/null \
    | grep -v "uv pip install" | grep -v "pip install uv" | grep -v "#" || :)
[[ -n "$PIP" ]] && { log_fail "Use 'uv pip install' not 'pip install'"; echo "$PIP" | head -3; V=$(( V + 1 )); } || log_success "No bare pip install"

BE=$(rg "except Exception:" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null || :)
# Bypass: add --glob exclusions for files in QUALITY_GATE_BYPASS_AUDIT.md §1.1
[[ -n "$BE" ]] && { log_warn "broad except Exception — document in QUALITY_GATE_BYPASS_AUDIT.md"; V=$(( V + 1 )); } || log_success "No broad except Exception"

# Swallowed errors — except that silently passes/returns None
SWALLOWED=$(rg "except Exception:" --type py --glob "!tests/**" "$SOURCE_DIR/" -A 2 2>/dev/null \
    | grep -E "^[[:space:]]+(pass|return None)$" || :)
[[ -n "$SWALLOWED" ]] && { log_fail "Swallowed errors — use @handle_api_errors or re-raise"; V=$(( V + 1 )); } || log_success "No swallowed errors"

# File size
# FUNCTION_SIZE_EXTRA_EXCLUDES also applies here for consistency (same variable, same dirs to skip)
SVIOL=""; SWARN=""
for f in $(find . -name "*.py" ! -path "./.venv/*" ! -path "./scripts/*" ! -path "./.git/*" ! -path "./build/*" ! -path "./.venv-workspace/*" ! -path "*/site-packages/*" "${FUNCTION_SIZE_EXTRA_EXCLUDES[@]}" 2>/dev/null); do
    lines=$(wc -l < "$f" 2>/dev/null || echo 0)
    [[ "$lines" -gt $MAX_FILE_LINES ]] && SVIOL="${SVIOL}\n  $f: $lines L"
    [[ "$lines" -gt $FILE_WARN_LINES && "$lines" -le $MAX_FILE_LINES ]] && SWARN="${SWARN}\n  $f: $lines L"
done
[[ -n "$SVIOL" ]] && { log_fail "Files exceed $MAX_FILE_LINES lines:$SVIOL"; V=$(( V + 1 )); } || log_success "File size OK"
[[ -n "$SWARN" ]] && log_warn "Approaching limit:$SWARN"

# Function/class/method size
# FUNCTION_SIZE_EXTRA_EXCLUDES: optional array of extra ! -path args set in quality-gates.sh
# e.g. FUNCTION_SIZE_EXTRA_EXCLUDES=("! -path ./features_service/*" "! -path ./examples/*")
FSIZES=""
for f in $(find . -name "*.py" ! -path "./.venv/*" ! -path "./scripts/*" ! -path "./.git/*" ! -path "./build/*" ! -path "./.venv-workspace/*" ! -path "*/site-packages/*" "${FUNCTION_SIZE_EXTRA_EXCLUDES[@]}" 2>/dev/null); do
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

# Security: pip-audit (BLOCKING — OSV vulnerability database check)
if command -v pip-audit &>/dev/null; then
    pip-audit --format json -o /tmp/pip-audit-output.json 2>/dev/null \
        && log_success "pip-audit clean" \
        || { log_fail "pip-audit vulnerabilities found"; V=$(( V + 1 )); }
    # Store SBOM audit trail in GCS (non-blocking — upload failure does not fail the build)
    SERVICE_NAME="$SERVICE_NAME" python3 "$REPO_ROOT/unified-trading-pm/scripts/sbom-store.py" \
        /tmp/pip-audit-output.json 2>/dev/null || :
    # Internal advisory check (BLOCKING — checks unified-trading-pm/security/internal-advisories.yaml)
    if [[ -f "$REPO_ROOT/unified-trading-pm/scripts/check-internal-advisories.sh" ]]; then
        bash "$REPO_ROOT/unified-trading-pm/scripts/check-internal-advisories.sh" \
            && log_success "internal advisory check clean" \
            || { log_fail "internal advisory violation — see unified-trading-pm/security/internal-advisories.yaml"; V=$(( V + 1 )); }
    else
        log_warn "check-internal-advisories.sh not found at REPO_ROOT=$REPO_ROOT — skipping internal advisory check"
    fi
else
    log_fail "pip-audit required: uv pip install pip-audit"; V=$(( V + 1 ))
fi

# Security: bandit
# BANDIT_EXTRA_ARGS: optional per-repo override (e.g. BANDIT_EXTRA_ARGS="-c pyproject.toml")
if command -v bandit &>/dev/null; then
    run_timeout 30 bandit -r "$SOURCE_DIR/" -ll ${BANDIT_EXTRA_ARGS:-} 2>/dev/null && log_success "bandit clean" || { log_fail "bandit issues"; V=$(( V + 1 )); }
else
    log_fail "bandit required: uv pip install bandit"; V=$(( V + 1 ))
fi

# Cloud Build validator
if [ -f "cloudbuild.yaml" ] && command -v gcloud &>/dev/null; then
    if git diff --name-only HEAD 2>/dev/null | grep -q "cloudbuild.yaml"; then
        gcloud meta validate-yaml cloudbuild.yaml 2>/dev/null && log_success "cloudbuild.yaml valid" || log_warn "cloudbuild.yaml validation failed"
    fi
fi

# CI/CD hygiene: ||true bypasses in quality gate scripts
BYPASS=$(rg "\|\|true|\|\| true" --glob "**/quality-gates.sh" --glob "**/quality-gates.yml" . 2>/dev/null \
    | grep -v "^#\|zombies\|pyright\|cleanup" || :)
[[ -n "$BYPASS" ]] && { log_fail "||true bypass in quality gates — fix the root cause"; echo "$BYPASS" | head -3; V=$(( V + 1 )); } || log_success "No ||true quality gate bypasses"

# ============================================================
# STEP 5.7 — No real cloud API calls in unit tests
# ============================================================
UNIT_CLOUD_CALLS=$(rg 'get_storage_client\(\)|get_secret_client\(\)|get_queue_client\(\)' \
    --type py tests/unit/ 2>/dev/null | grep -v '\.mock\.' | grep -v 'MagicMock' | grep -v 'patch' || :)
[[ -n "$UNIT_CLOUD_CALLS" ]] && {
    log_fail "Unit tests call real cloud APIs — use MagicMock(spec=StorageClient) instead"
    echo "$UNIT_CLOUD_CALLS" | head -5
    V=$(( V + 1 ))
} || log_success "Unit tests appear cloud-agnostic"

# ============================================================
# STEP 5.8 — No backward-compatibility re-export stubs
# RULE: When moving a schema, update all consumers and delete the old file.
# Never leave a shim that re-exports from the new location.
# CODEX: cursor-rules/core/no-backward-compat-shims.mdc
# ============================================================
BACK_COMPAT=$(rg "# MIGRATED|backward compat|backward-compat|Re-export.*backward|re-export.*compat" \
    --type py --glob "!tests/**" --glob "!.venv*" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$BACK_COMPAT" ]] && {
    log_fail "Backward-compat pattern found — eliminate re-export stubs, aliases, and compat shims"
    log_fail "See: cursor-rules/core/no-backward-compat-shims.mdc"
    echo "$BACK_COMPAT" | head -5
    V=$(( V + 1 ))
} || log_success "No backward-compat stubs"

# ============================================================
# STEP 5.9 — Schema placement compliance
# Domain data contracts (BaseModel/TypedDict/dataclass) must live in UIC domain/<service>/
# SchemaDefinition/ColumnSchema (parquet infra) may stay in schemas/output_schemas.py
# CODEX: 02-data/contracts-scope-and-layout.md, 02-data/schema-governance.md
# ============================================================
# Detect Pydantic BaseModel subclasses in service source outside of output_schemas.py
# (output_schemas.py is allowed to contain SchemaDefinition/ColumnSchema infra objects only)
DOMAIN_CONTRACTS_IN_SERVICE=$(rg 'class \w+\(BaseModel\)' --type py \
    --glob "!tests/**" --glob "!**/output_schemas.py" --glob "!**/__init__.py" \
    "$SOURCE_DIR/" 2>/dev/null | grep -v '#.*CORRECT-LOCAL' || :)
[[ -n "$DOMAIN_CONTRACTS_IN_SERVICE" ]] && {
    log_fail "Pydantic BaseModel subclasses found in service source — domain data contracts must live in UIC domain/<service-name>/"
    log_fail "See: unified-trading-pm/plans/active/SCHEMA_CONTRACTS_AUDIT.md Section 3b"
    echo "$DOMAIN_CONTRACTS_IN_SERVICE" | head -5
    V=$(( V + 1 ))
} || log_success "No domain BaseModel contracts in service source"

# Detect TypedDict domain contracts in service source
# Exempt: underscore-prefix classes (e.g. class _Foo(TypedDict)) — private implementation types
# Exempt: lines with # CORRECT-LOCAL comment — explicitly marked as local-only, non-shared types
TYPEDDICT_IN_SERVICE=$(rg 'class \w+\(TypedDict\)' --type py \
    --glob "!tests/**" --glob "!**/output_schemas.py" \
    "$SOURCE_DIR/" 2>/dev/null \
    | grep -v '#.*CORRECT-LOCAL' \
    | grep -v 'class _[A-Z]' \
    || :)
[[ -n "$TYPEDDICT_IN_SERVICE" ]] && {
    log_fail "TypedDict contracts found in service source — belong in UIC domain/<service-name>/"
    log_fail "  Exception: underscore-prefix classes (private) or lines with # CORRECT-LOCAL are exempt"
    echo "$TYPEDDICT_IN_SERVICE" | head -3
    V=$(( V + 1 ))
} || log_success "No TypedDict domain contracts in service source"

# ============================================================
# STEP 5.10 — Block direct cloud SDK imports outside UCI providers
# ============================================================
CLOUD_SDK_VIOLATIONS=$(rg "^from google\.cloud|^import boto3|^import botocore" \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!tests' \
    --glob '!unified_cloud_interface/providers/**' \
    -l . 2>/dev/null || :)
if [ -n "$CLOUD_SDK_VIOLATIONS" ]; then
    log_fail "STEP 5.10: Direct cloud SDK imports found. Use unified_cloud_interface instead:"
    echo "$CLOUD_SDK_VIOLATIONS"
    V=$(( V + 1 ))
else
    log_success "STEP 5.10: No direct cloud SDK imports"
fi

# ============================================================
# STEP 5.11 — Block protocol-specific symbols in service code
# ============================================================
PROTOCOL_VIOLATIONS=$(rg "CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!tests' --glob '!scripts/**' \
    -l . 2>/dev/null || :)
if [ -n "$PROTOCOL_VIOLATIONS" ]; then
    log_fail "STEP 5.11: Protocol-specific symbols found. Use get_data_sink() / get_event_bus() from UCI instead:"
    echo "$PROTOCOL_VIOLATIONS"
    V=$(( V + 1 ))
else
    log_success "STEP 5.11: No protocol-specific symbols in service code"
fi

# ============================================================
# STEP 5.12 — Services must not hardcode cloud protocol names
# ============================================================
echo "=== STEP 5.12: No hardcoded protocol names in service source ==="
HARDCODED_PROTO=$(rg \
  'gcs_bucket\s*=|bigquery_dataset\s*=|upload_to_gcs|CloudTarget\b|StandardizedDomainCloudService\b' \
  --type py \
  --glob '!.venv*' \
  --glob '!**/.venv*/**' \
  --glob '!tests/**' \
  --glob '!scripts/**' \
  "${HARDCODED_PROTO_EXCLUDE_GLOBS[@]}" \
  -l "$SOURCE_DIR" 2>/dev/null || :)
if [ -n "$HARDCODED_PROTO" ]; then
    log_fail "STEP 5.12: Hardcoded protocol/cloud names in service source (use get_data_sink/get_event_bus):"
    echo "$HARDCODED_PROTO"
    V=$(( V + 1 ))
else
    log_success "STEP 5.12: No hardcoded protocol names"
fi

# ============================================================
# STEP 5.12b — §12 No hardcoded gs:// or s3:// URIs outside unified-cloud-interface
# ============================================================
echo "=== STEP 5.12b: No hardcoded gs:// or s3:// URIs outside UCI ==="
GCS_URI_VIOLATIONS=$(rg '"gs://|"s3://' \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!**/tests/**' --glob '!**/scripts/**' \
    --glob '!**/unified-cloud-interface/**' \
    -l "$SOURCE_DIR" 2>/dev/null \
    | xargs -I{} grep -l '"gs://\|"s3://' {} 2>/dev/null \
    | xargs grep -n '"gs://\|"s3://' 2>/dev/null \
    | grep -v '# noqa: gs-uri' \
    || :)
if [ -n "$GCS_URI_VIOLATIONS" ]; then
    log_fail "STEP 5.12b: Hardcoded cloud URIs found (use UCI StorageClient — download_bytes/upload_bytes/list_blobs):"
    echo "$GCS_URI_VIOLATIONS" | head -10
    V=$(( V + 1 ))
else
    log_success "STEP 5.12b: No hardcoded gs:// or s3:// URIs outside UCI"
fi

# STEP 5.13 — Schema placement advisory (cross-repo contract check)
# =====================================================================
echo "=== STEP 5.13: Schema placement advisory (cross-repo contract check) ==="
SCHEMA_DUPES=$(rg \
  'class\s+Canonical[A-Z]\w+\s*\(.*BaseModel' \
  --type py \
  --glob '!.venv*' \
  --glob '!tests/**' \
  --glob '!scripts/**' \
  "${SOURCE_DIR:-./}/" \
  2>/dev/null || :)
if [ -n "$SCHEMA_DUPES" ]; then
    log_warn "STEP 5.13: Pydantic classes matching 'Canonical*' pattern found in service source — verify these are NOT redefining UAC/UIC canonicals (canonical name collision causes type drift):"
    echo "$SCHEMA_DUPES" | head -10
    echo "(See: unified-trading-codex/02-data/schema-governance.md and cursor rule core/schema-governance-index.mdc)"
    # NOTE: Advisory only (log_warn, not log_fail). Some services may legitimately extend canonicals.
    # Manually verify: should import from unified_api_contracts or unified_internal_contracts instead.
else
    log_success "STEP 5.13: No canonical name collisions detected in service source"
fi

# STEP 5.21 — basedpyright config: all Any/Unknown rules must be "error" not "warning"
# Zero-warning policy requires rules to be errors so they block the QG at the config level too.
echo "=== STEP 5.21: basedpyright zero-warning policy (reportAny/reportUnknown* = \"error\") ==="
if [ -f "pyproject.toml" ]; then
    BP_VIOLATIONS=()
    for rule in reportAny reportUnknownVariableType reportUnknownParameterType reportUnknownMemberType reportUnknownArgumentType reportUnknownLambdaType; do
        if grep -qE "^\s*${rule}\s*=\s*[\"'](warning|none)[\"']" pyproject.toml 2>/dev/null; then
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

# STEP 5.22 — basedpyright baseline suppression audit
# .basedpyright-baseline.json silently hides errors from CI.
# Zero-baseline policy (enforced as ERROR 2026-03-10):
#   • Present (any state)  → FAIL: baseline suppression not allowed; delete the file
#   • Not present          → PASS (clean)
# Documentation in QUALITY_GATE_BYPASS_AUDIT.md does NOT exempt baseline suppression.
echo "=== STEP 5.22: basedpyright baseline suppression ==="
if [ -f ".basedpyright-baseline.json" ]; then
    log_fail "STEP 5.22: .basedpyright-baseline.json present — baseline suppression not allowed (zero-baseline policy)"; V=$(( V + 1 ))
else
    log_success "STEP 5.22: no basedpyright baseline (clean)"
fi

# ============================================================
# STEP 5.17 — cloudbuild.yaml structural compliance
# Verifies required CI steps are present when cloudbuild.yaml exists.
# If cloudbuild.yaml is absent (repo uses buildspec.aws.yaml or GitHub Actions),
# this check is skipped — absence of the file is not a violation.
# Required step patterns (any one match per category is sufficient):
#   test step   : quality-gates  OR  run-tests  OR  test-in-image
#   vuln scan   : vulnerability-scan  OR  scan-check  OR  trivy
#   push        : "push"  (step id containing push)
#   deploy      : deploy  OR  gcloud run deploy
# ============================================================
echo "=== STEP 5.17: cloudbuild.yaml structural compliance ==="
if [ -f "cloudbuild.yaml" ]; then
    CB_FAIL=0
    # Schema validation (SchemaStore + jsonschema) — portable, no gcloud required
    VALIDATOR="${REPO_ROOT}/unified-trading-pm/scripts/validation/validate-cloudbuild.py"
    if [ -f "$VALIDATOR" ]; then
        run_timeout 30 "$PYTHON_CMD" "$VALIDATOR" cloudbuild.yaml 2>/dev/null || {
            log_fail "STEP 5.17: cloudbuild.yaml schema validation failed"; CB_FAIL=1; V=$(( V + 1 )); }
    fi
    rg "id:\s*[\"']?(quality-gates|run-tests|test-in-image)" cloudbuild.yaml 2>/dev/null \
        | grep -qE 'quality-gates|run-tests|test-in-image' || {
        log_fail "STEP 5.17: cloudbuild.yaml missing test step (quality-gates / run-tests / test-in-image)"; CB_FAIL=1; V=$(( V + 1 )); }
    rg "id:\s*[\"']?(vulnerability-scan|scan-check|trivy)" cloudbuild.yaml 2>/dev/null \
        | grep -qE 'vulnerability-scan|scan-check|trivy' || {
        log_fail "STEP 5.17: cloudbuild.yaml missing vulnerability scan step (vulnerability-scan / scan-check / trivy)"; CB_FAIL=1; V=$(( V + 1 )); }
    rg "id:\s*[\"']?push" cloudbuild.yaml 2>/dev/null \
        | grep -q 'push' || \
        rg '"push"' cloudbuild.yaml 2>/dev/null | grep -q 'push' || {
        log_fail "STEP 5.17: cloudbuild.yaml missing push step"; CB_FAIL=1; V=$(( V + 1 )); }
    rg "id:\s*[\"']?(deploy|notify-deployment)|gcloud run deploy" cloudbuild.yaml 2>/dev/null \
        | grep -qE 'deploy|notify-deployment' || {
        log_warn "STEP 5.17: cloudbuild.yaml has no deploy/notify-deployment step (advisory — some services deploy via dispatch)"; }
    [ "$CB_FAIL" -eq 0 ] && log_success "STEP 5.17: cloudbuild.yaml structure OK"
elif [ -f "buildspec.aws.yaml" ]; then
    VALIDATOR="${REPO_ROOT}/unified-trading-pm/scripts/validation/validate-buildspec.py"
    if [ -f "$VALIDATOR" ]; then
        if run_timeout 30 "$PYTHON_CMD" "$VALIDATOR" buildspec.aws.yaml 2>/dev/null; then
            log_success "STEP 5.17: buildspec.aws.yaml schema OK"
        else
            log_fail "STEP 5.17: buildspec.aws.yaml schema validation failed"; V=$(( V + 1 ));
        fi
    else
        log_success "STEP 5.17: buildspec.aws.yaml present (validator not available)"
    fi
else
    log_success "STEP 5.17: no cloudbuild.yaml (buildspec.aws.yaml or GitHub Actions — skipped)"
fi

[[ $V -gt 0 ]] && { log_fail "Codex compliance FAILED: $V violations"; exit 1; }
log_success "Codex compliance PASSED"

# ── [6] PRODUCTION READINESS (informational) ──────────────────────────────────
log_section "[6/6] PRODUCTION READINESS VALIDATORS"
VSCRIPT="${REPO_ROOT}/unified-trading-codex/scripts/run-all-validators.sh"
[ -f "$VSCRIPT" ] && "$VSCRIPT" --category all --failed-only 2>/dev/null || log_warn "Validators not available (optional)"

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
    if act -j quality-gates --container-architecture linux/amd64 ${ACT_SECRETS_ARG}; then
        log_success "Act simulation PASSED"
    else
        log_fail "Act simulation FAILED — act needs GH_PAT to clone sibling repos"
        [ -z "$ACT_SECRETS_ARG" ] && log_warn "No .act-secrets found at ${REPO_ROOT}/.act-secrets or ~/.secrets"
        log_warn "Fix: bash unified-trading-pm/scripts/workspace/generate-act-secrets.sh"
        exit 1
    fi
fi

# ── DURATION CHECK ───────────────────────────────────────────────────────────
MAX_DURATION=${MAX_DURATION:-120}
QG_END=$(date +%s); DUR=$((QG_END - QG_START))
[ $DUR -gt $MAX_DURATION ] && { log_fail "Quality gates must complete in <${MAX_DURATION}s (took ${DUR}s)"; exit 1; }
echo -e "\n${GREEN}======================================================================"
echo -e "✅ ALL QUALITY GATES PASSED (${DUR}s)${NC}"
