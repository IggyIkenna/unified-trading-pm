#!/usr/bin/env bash
# quality-gates-base-library v1.0 — owned by unified-trading-pm
#
# Shared quality-gate body for Python library/interface repos.
# Do NOT edit per-repo — this file is the SSOT for all library gate logic.
# To add a new check for all libraries, edit this file only.
#
# Required caller variables (set before sourcing this file):
#   PACKAGE_NAME  — e.g. "unified-events-interface"
#   SOURCE_DIR    — e.g. "unified_events_interface"  (underscore form)
#   MIN_COVERAGE  — e.g. 99
#
# Optional caller variables:
#   PYTEST_WORKERS — parallel workers (default: 2)
#   LOCAL_DEPS     — array of sibling repo names to install locally
#   MAX_DURATION   — duration limit in seconds (default: 150)
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

QG_START=$(date +%s)
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_section() { :; }
log_success() { :; }
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
MAX_FUNCTION_LINES=${MAX_FUNCTION_LINES:-200}; MAX_CLASS_LINES=${MAX_CLASS_LINES:-900}; MAX_METHOD_LINES=${MAX_METHOD_LINES:-50}

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
# Prefer .venv-workspace when available (single Python for all repos)
WORKSPACE_VENV="${REPO_ROOT}/.venv-workspace"
if [ -z "${GITHUB_ACTIONS:-}" ] && [ -z "${CI:-}" ] && [ -z "${CLOUD_BUILD:-}" ]; then
    if [ -f "$WORKSPACE_VENV/bin/activate" ]; then
        source "$WORKSPACE_VENV/bin/activate"
    else
        command -v uv &>/dev/null || pip install uv --quiet
        uv lock 2>/dev/null || :
        [ ! -d ".venv" ] && uv venv .venv
        [ -f ".venv/bin/activate" ] && source .venv/bin/activate || :
        for lib in "${LOCAL_DEPS[@]+"${LOCAL_DEPS[@]}"}"; do
            [ -d "${REPO_ROOT}/$lib" ] && uv pip install -e "${REPO_ROOT}/$lib" --quiet 2>/dev/null || :
        done
        uv pip install -e . --quiet 2>/dev/null || :
    fi
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
        npx --yes prettier@3.6.2 --write --cache "**/*.{md,json,yaml,yml}" --ignore-path .gitignore >/dev/null 2>&1 \
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

# ── [3] TESTS (pytest, unit only — libraries have no integration tests by default) ──
if [ "$RUN_TESTS" = true ]; then
    log_section "[3/6] TESTS"
    $PYTHON_CMD -c "import pytest_timeout" 2>/dev/null || { log_fail "pytest-timeout required: uv pip install pytest-timeout"; exit 1; }
    $PYTHON_CMD -c "import xdist" 2>/dev/null || { log_fail "pytest-xdist required: uv pip install pytest-xdist"; exit 1; }
    COV="--cov=$SOURCE_DIR --cov-report=xml:coverage.xml --cov-fail-under=$MIN_COVERAGE"
    PARGS="-n ${PYTEST_WORKERS:-2} --timeout=60 -q -r a --tb=short --no-header"
    _pytest_out=$($PYTHON_CMD -m pytest tests/unit/ --disable-socket --allow-unix-socket $PARGS $COV 2>&1) \
        || { echo "$_pytest_out"; exit 1; }
    log_success "Tests PASSED"

    # No duplicate test files (test_*_extended.py, test_*_additional.py)
    DUP=$(find tests/ -name "test_*_extended.py" -o -name "test_*_additional.py" 2>/dev/null | head -5 || :)
    [[ -n "$DUP" ]] && { log_fail "Duplicate test files — expand existing files instead:"; echo "$DUP"; exit 1; }
    log_success "No duplicate test files"

    # @pytest.mark.skip (bare skip, not skipif) must have a reason comment on the preceding line
    # skipif always carries reason= inline so is excluded from this check
    SKIP_NO_REASON=$(rg "@pytest\.mark\.skip" --type py tests/ -B 1 2>/dev/null \
        | grep -v "# reason:\|# noqa\|^--\|skipif\|reason=" | grep "@pytest\.mark\.skip" || :)
    [[ -n "$SKIP_NO_REASON" ]] && { log_fail "pytest.mark.skip without reason comment — add '# reason: ...' above"; echo "$SKIP_NO_REASON" | head -3; exit 1; }
    log_success "All pytest.mark.skip have reason comments"
fi

# ── [3.5] IMPORT PATTERN STANDARDS ───────────────────────────────────────────
log_section "[3.5/6] IMPORT PATTERNS"
IP="${REPO_ROOT}/unified-trading-pm/scripts/validation/check-import-patterns.py"
[ ! -f "$IP" ] && IP="${REPO_ROOT}/unified-trading-pm/scripts/check-import-patterns.py"  # pre-move fallback
[ ! -f "$IP" ] && IP="${REPO_ROOT}/.cursor/scripts/check-import-patterns.py"
if [ -f "$IP" ]; then
    # Scope import check to SOURCE_DIR only — tests are allowed to deep-import from their own
    # package (they test internal components). External consumers are linted at a higher level.
    IP_TARGET="${SOURCE_DIR:-.}"
    _ip_out=$($PYTHON_CMD "$IP" "$IP_TARGET" 2>/dev/null) || { echo "$_ip_out"; log_fail "Import patterns FAILED"; exit 1; }
else
    log_warn "check-import-patterns.py not found (unified-trading-pm/scripts/)"
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
    PYRIGHT_OUT=$(run_timeout 120 "$BASEDPYRIGHT_CMD" "$SOURCE_DIR/" 2>&1); PYRIGHT_EXIT=$?
    if [ "$PYRIGHT_EXIT" -ne 0 ]; then echo "$PYRIGHT_OUT"; log_fail "Type check FAILED/timeout"; exit 1; fi
    WARN_COUNT=$(echo "$PYRIGHT_OUT" | grep -c " warning:" || :)
    if [ "${WARN_COUNT:-0}" -gt 0 ]; then
        echo "$PYRIGHT_OUT"
        log_fail "Type check FAILED — $WARN_COUNT warning(s) (zero-warning policy: promote all rules to error in [tool.basedpyright])"; exit 1
    fi
    log_success "Type check PASSED (0 errors, 0 warnings)"
fi
[ "$SKIP_TYPECHECK" = "true" ] && echo -e "${YELLOW}⚠️  Type check SKIPPED (--skip-typecheck flag)${NC}"

# ── [5] CODEX COMPLIANCE (library variant) ────────────────────────────────────
# Same checks as service variant with library-specific exceptions noted inline.
log_section "[5/6] CODEX COMPLIANCE"
V=0

rg "print\(" --type py --glob "!tests/**" --glob "!scripts/**" "$SOURCE_DIR/" 2>/dev/null \
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
    grep -q "async def" "$f" && { log_fail "requests in async: $f — use aiohttp"; V=$(( V + 1 )); break; }
done; [[ ${V} -eq $(( V )) ]] && log_success "No requests in async" 2>/dev/null || :

for f in $(rg "asyncio\.run\(" --type py --glob "!tests/**" --glob "!scripts/**" --glob "!**/testing/**" "$SOURCE_DIR/" -l 2>/dev/null || :); do
    grep -qE "^[[:space:]]*(for |while )" "$f" && { log_fail "asyncio.run() in loop: $f — use asyncio.gather()"; V=$(( V + 1 )); break; }
done

_SELF_PKG=$(echo "$SOURCE_DIR" | tr '/' '_')
_inside_extra_globs=()
for _excl in "${INSIDE_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _inside_extra_globs+=("--glob" "!${_excl}"); done
INSIDE=$(rg "^[[:space:]]+import |^[[:space:]]+from .* import" --type py --glob "!tests/**" --glob "!**/__init__.py" \
    "${_inside_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa: qg-inside-import\|# noqa:.*qg-inside-import" \
    | grep -v "from ${_SELF_PKG}\.\|from ${_SELF_PKG} " || :)
[[ -n "$INSIDE" ]] && { log_fail "Imports inside functions — move to top"; echo "$INSIDE" | head -3; V=$(( V + 1 )); } || log_success "No imports inside functions"

ANY=$(rg ": Any|-> Any|\[Any\]" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null | grep -v "type: ignore" || :)
[[ -n "$ANY" ]] && { log_fail "Any types (including dict[str, Any]) — use Pydantic models or specific types"; echo "$ANY" | head -3; V=$(( V + 1 )); } || log_success "No Any types"

_raw_json_extra_globs=()
for _excl in "${RAW_JSON_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _raw_json_extra_globs+=("--glob" "!${_excl}"); done
RAW_JSON=$(rg 'response\.json\(\)|await response\.json\(\)' --type py --glob "!tests/**" "${_raw_json_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v 'model_validate\|cast(dict' \
    | grep -v "# noqa:.*qg-raw-json\|# noqa: qg-raw-json" || :)
[[ -n "$RAW_JSON" ]] && { log_fail "Raw response.json() — parse through Pydantic model_validate()"; echo "$RAW_JSON" | head -3; V=$(( V + 1 )); } || log_success "No raw response.json()"

_efb_extra_globs=()
for _excl in "${EMPTY_FALLBACK_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _efb_extra_globs+=("--glob" "!${_excl}"); done
ES=$(rg '\.get\(["\x27][\w_]+["\x27]\s*,\s*["\x27]["\x27]\)' --type py --glob "!tests/**" "${_efb_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa:.*qg-empty-fallback\|# noqa: qg-empty-fallback" || :)
[[ -n "$ES" ]] && { log_fail "Empty string fallback — fail fast"; echo "$ES" | head -3; V=$(( V + 1 )); } || log_success "No empty string fallbacks"

ED=$(rg '\.get\s*\(\s*["\x27][^"\x27]+["\x27]\s*,\s*\{\}\s*\)' --type py --glob "!tests/**" "${_efb_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa:.*qg-empty-fallback\|# noqa: qg-empty-fallback" || :)
EL=$(rg '\.get\s*\(\s*["\x27][^"\x27]+["\x27]\s*,\s*\[\]\s*\)' --type py --glob "!tests/**" "${_efb_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa:.*qg-empty-fallback\|# noqa: qg-empty-fallback" || :)
[[ -n "$ED$EL" ]] && { log_fail "Empty dict/list fallback — fail fast"; V=$(( V + 1 )); } || log_success "No empty dict/list fallbacks"

rg "central-element-323112" tests/ 2>/dev/null \
    && { log_fail "Hardcoded prod project ID in tests — use 'test-project'"; V=$(( V + 1 )); } || log_success "No hardcoded project ID in tests"

rg "central-element-323112" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
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
    | grep -v "# noqa:.*qg-deep-import\|# noqa: qg-deep-import" || :)
[[ -n "$DI" ]] && { log_fail "Deep unified lib imports — use top-level"; echo "$DI" | head -3; V=$(( V + 1 )); } || log_success "No deep imports"

EL_OLD=$(rg "from unified_trading_library[. ].*(log_event|setup_events|setup_cloud_logging|observability)" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "from ${_SELF_PKG}\." || :)
[[ -n "$EL_OLD" ]] && { log_fail "Old event logging import — use 'from unified_events_interface import ...'"; echo "$EL_OLD" | head -3; V=$(( V + 1 )); } || log_success "Event logging imports from unified_events_interface"

# ============================================================
# STEP 5.5 — No direct cloud SDK imports
# Libraries: exclude providers/ and cache.py (UCI-specific paths)
# ============================================================
CLOUD_SDK_VIOLATIONS=$(rg "^from google\.cloud|^import boto3|^import botocore" \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!tests' \
    --glob '!*/providers/**' \
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
    --type py --glob "!tests/**" --glob "!.venv*" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$BACK_COMPAT" ]] && {
    log_fail "Backward-compat pattern found — eliminate re-export stubs, aliases, and compat shims"
    log_fail "See: cursor-rules/core/no-backward-compat-shims.mdc"
    echo "$BACK_COMPAT" | head -5
    V=$(( V + 1 ))
} || log_success "No backward-compat stubs"

# ============================================================
# STEP 5.9 — Schema placement (advisory for libraries)
# ============================================================
DOMAIN_CONTRACTS_IN_LIB=$(rg 'class \w+\(BaseModel\)' --type py \
    --glob "!tests/**" --glob "!**/__init__.py" \
    "$SOURCE_DIR/" 2>/dev/null | grep -v '#.*CORRECT-LOCAL' || :)
[[ -n "$DOMAIN_CONTRACTS_IN_LIB" ]] && {
    log_warn "Pydantic BaseModel subclasses found in library source — external API schemas belong in UAC; internal domain contracts in UIC"
    log_warn "See: unified-trading-pm/plans/active/SCHEMA_CONTRACTS_AUDIT.md"
    echo "$DOMAIN_CONTRACTS_IN_LIB" | head -5
} || log_success "No misplaced domain BaseModel contracts in library"

# ============================================================
# STEP 5.11 — Block protocol-specific symbols
# unified-config-interface cloud_config.py: field names are schema — documented bypass §2.6
# unified-trading-library: defines/deprecates these symbols — excluded as origin repo §2.6
# ============================================================
if [[ "$PACKAGE_NAME" = "unified-config-interface" ]]; then
    PROTOCOL_VIOLATIONS=$(rg "CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
        --type py --glob '!.venv*' --glob '!**/.venv*/**' --glob '!tests' --glob '!**/cloud_config.py' -l . 2>/dev/null || :)
elif [[ "$PACKAGE_NAME" = "unified-trading-library" ]]; then
    # UTL defines/deprecates these symbols — skip the origin and compat-layer files
    PROTOCOL_VIOLATIONS=$(rg "CloudTarget|upload_to_gcs_batch|StandardizedDomainCloudService" \
        --type py --glob '!.venv*' --glob '!**/.venv*/**' --glob '!tests' \
        --glob '!**/domain/standardized_service.py' --glob '!**/__init__.py' \
        --glob '!**/core/cloud_config.py' --glob '!**/core/cloud_data_provider.py' \
        --glob '!**/domain/data_completion.py' \
        -l . 2>/dev/null \
        | grep -v "# noqa:.*qg-protocol-symbol\|# noqa: qg-protocol-symbol" || :)
elif [[ "$PACKAGE_NAME" = "unified-domain-client" ]]; then
    # UDC defines its own StandardizedDomainCloudService (domain wrapper, not a protocol violation)
    # and CloudTarget (local config dataclass, not UTL's deprecated GCS-specific CloudTarget).
    # All client files and sports/ are legitimate consumers of UDC's own class — excluded.
    PROTOCOL_VIOLATIONS=$(rg "CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
        --type py --glob '!.venv*' --glob '!**/.venv*/**' --glob '!tests' \
        --glob '!**/standardized_service.py' --glob '!**/cloud_target.py' \
        --glob '!**/factories.py' --glob '!**/__init__.py' \
        --glob '!**/cloud_data_provider.py' --glob '!**/clients/**' \
        --glob '!**/sports/**' \
        -l . 2>/dev/null || :)
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
[[ -n "$BE" ]] && { log_warn "broad except Exception — document in QUALITY_GATE_BYPASS_AUDIT.md"; V=$(( V + 1 )); } || log_success "No broad except Exception"

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
    [[ "$lines" -gt $FILE_WARN_LINES && "$lines" -le $MAX_FILE_LINES ]] && SWARN="${SWARN}\n  $f: $lines L"
done
[[ -n "$SVIOL" ]] && { log_fail "Files exceed $MAX_FILE_LINES lines:$SVIOL"; V=$(( V + 1 )); } || log_success "File size OK"
[[ -n "$SWARN" ]] && log_warn "Approaching limit:$SWARN"

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
    _pa_out=$($PYTHON_CMD -m pip_audit 2>&1) || { echo "$_pa_out"; log_fail "pip-audit vulnerabilities"; V=$(( V + 1 )); }
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

# ── DURATION CHECK ───────────────────────────────────────────────────────────
MAX_DURATION=${MAX_DURATION:-150}
QG_END=$(date +%s); DUR=$((QG_END - QG_START))
[ $DUR -gt $MAX_DURATION ] && { log_fail "Quality gates must complete in <${MAX_DURATION}s (took ${DUR}s)"; exit 1; }
echo -e "\n${GREEN}======================================================================"
echo -e "✅ ALL QUALITY GATES PASSED (${DUR}s)${NC}"
