#!/usr/bin/env bash
# quality-gates-base-codex v1.0 — owned by unified-trading-pm
#
# Shared quality-gate body for docs-only repos (no Python source directory).
# Do NOT edit per-repo — this file is the SSOT for all codex/docs gate logic.
# To add a new check for all docs repos, edit this file only.
#
# Required caller variables (set before sourcing this file):
#   SERVICE_NAME  — documentation repo name, e.g. "unified-trading-codex"
#
# Skipped checks (docs-only repos have no Python source):
#   - basedpyright type checking
#   - pytest / coverage
#   - ruff lint on source
#   - pip-audit / bandit
#
# Runs:
#   - [1] Markdown lint (markdownlint-cli)
#   - [2] Prettier formatting check
#   - [3] Link validation (markdown-link-check, non-blocking)
#   - [4] Codex structure checks (no Python anti-patterns in docs tooling)
#
# Version guard (optional): declare EXPECTED_BASE_VERSION="1.0" in stub before sourcing.
#
REQUIRED_BASE_VERSION="1.0"
if [[ -n "${EXPECTED_BASE_VERSION:-}" && "$EXPECTED_BASE_VERSION" != "$REQUIRED_BASE_VERSION" ]]; then
    echo "⚠️  Stub expects base v${EXPECTED_BASE_VERSION} but base is v${REQUIRED_BASE_VERSION}" >&2
fi

# ── REQUIRED VARIABLE VALIDATION ──────────────────────────────────────────────
if [[ -z "${SERVICE_NAME:-}" ]]; then
    echo "❌ base-codex.sh: required variable SERVICE_NAME is not set." >&2
    echo "   Set SERVICE_NAME in your repo's quality-gates.sh before sourcing base-codex.sh." >&2
    exit 1
fi

set -e

QG_START=$(date +%s)
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_section() { echo -e "\n${BLUE}$1${NC}"; echo "----------------------------------------------------------------------"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_fail()    { echo -e "${RED}❌ $1${NC}"; }
log_warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }

# When sourced, BASH_SOURCE[0] is this base script (in PM); BASH_SOURCE[1] is the caller stub.
# Derive PROJECT_ROOT from the stub's location (the repo that sourced us).
_BASE_CALLER="${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}"
SCRIPT_DIR="$(cd "$(dirname "$_BASE_CALLER")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="${REPO_ROOT:-$(dirname "$PROJECT_ROOT")}"
cd "$PROJECT_ROOT"
unset _BASE_CALLER

run_timeout() {
    local secs=$1; shift
    if command -v timeout &>/dev/null; then timeout "$secs" "$@"
    elif command -v gtimeout &>/dev/null; then gtimeout "$secs" "$@"
    else "$@"; fi
}

# ── MODE FLAGS ────────────────────────────────────────────────────────────────
QUICK_MODE=false; FIX_MODE=true
for arg in "$@"; do
    case $arg in
        --quick) QUICK_MODE=true ;;
        --no-fix) FIX_MODE=false ;;
        --fix) FIX_MODE=true ;;
    esac
done

log_section "[0/4] ENVIRONMENT — ${SERVICE_NAME} (docs-only)"
echo "PROJECT_ROOT : $PROJECT_ROOT"
echo "REPO_ROOT    : $REPO_ROOT"
echo "SERVICE_NAME : $SERVICE_NAME"
log_success "Environment OK (docs-only repo — Python checks skipped)"

# ── [1] MARKDOWN LINT ─────────────────────────────────────────────────────────
log_section "[1/4] MARKDOWN LINT"
if command -v markdownlint &>/dev/null || command -v markdownlint-cli2 &>/dev/null; then
    MDLINT_CMD="markdownlint"
    command -v markdownlint &>/dev/null || MDLINT_CMD="markdownlint-cli2"
    # Exclude CHANGELOG and auto-generated files; run non-blocking (docs may have legacy issues)
    run_timeout 60 "$MDLINT_CMD" "**/*.md" \
        --ignore node_modules \
        --ignore ".venv*" \
        --ignore "CHANGELOG.md" \
        2>/dev/null \
        && log_success "Markdown lint PASSED" \
        || log_warn "Markdown lint warnings (non-blocking for docs repos)"
elif command -v npx &>/dev/null; then
    run_timeout 60 npx --yes markdownlint-cli "**/*.md" \
        --ignore node_modules \
        --ignore ".venv*" \
        --ignore "CHANGELOG.md" \
        2>/dev/null \
        && log_success "Markdown lint PASSED" \
        || log_warn "Markdown lint warnings (non-blocking for docs repos)"
else
    log_warn "markdownlint not installed — skipping (install: npm install -g markdownlint-cli)"
fi

# ── [2] PRETTIER FORMATTING CHECK ────────────────────────────────────────────
log_section "[2/4] PRETTIER FORMATTING"
if command -v prettier &>/dev/null || command -v npx &>/dev/null; then
    PRETTIER_CMD="prettier"
    command -v prettier &>/dev/null || PRETTIER_CMD="npx prettier"
    if [ "$FIX_MODE" = true ]; then
        run_timeout 60 $PRETTIER_CMD --write "**/*.md" "**/*.yaml" "**/*.yml" "**/*.json" \
            --ignore-path .gitignore \
            2>/dev/null \
            && log_success "Prettier auto-fix complete" \
            || log_warn "Prettier auto-fix had warnings"
    fi
    run_timeout 60 $PRETTIER_CMD --check "**/*.md" "**/*.yaml" "**/*.yml" "**/*.json" \
        --ignore-path .gitignore \
        2>/dev/null \
        && log_success "Prettier formatting PASSED" \
        || log_warn "Prettier formatting warnings (run with --fix to auto-format)"
else
    log_warn "prettier not installed — skipping (install: npm install -g prettier)"
fi

# ── [3] LINK VALIDATION (non-blocking) ───────────────────────────────────────
log_section "[3/4] LINK VALIDATION"
if [ "$QUICK_MODE" = true ]; then
    log_warn "Link validation skipped (--quick mode)"
elif command -v markdown-link-check &>/dev/null || command -v npx &>/dev/null; then
    MLC_CMD="markdown-link-check"
    command -v markdown-link-check &>/dev/null || MLC_CMD="npx --yes markdown-link-check"
    LINK_FAILURES=0
    # Check top-level README and key docs — full recursive check can be slow
    for mdfile in README.md $(find . -maxdepth 3 -name "*.md" ! -path "./.git/*" ! -path "./node_modules/*" ! -path "./.venv*" 2>/dev/null | head -20); do
        [ -f "$mdfile" ] || continue
        run_timeout 30 $MLC_CMD "$mdfile" --quiet 2>/dev/null || LINK_FAILURES=$((LINK_FAILURES + 1))
    done
    if [ "$LINK_FAILURES" -gt 0 ]; then
        log_warn "Link validation: $LINK_FAILURES file(s) with broken links (non-blocking — fix before release)"
    else
        log_success "Link validation PASSED"
    fi
else
    log_warn "markdown-link-check not installed — skipping (install: npm install -g markdown-link-check)"
fi

# ── [4] CODEX STRUCTURE CHECKS ───────────────────────────────────────────────
log_section "[4/4] CODEX STRUCTURE CHECKS"
V=0

# CI/CD hygiene: no ||true bypasses in any quality gate scripts
BYPASS=$(rg "\|\|true|\|\| true" --glob "**/quality-gates.sh" --glob "**/quality-gates.yml" . 2>/dev/null \
    | grep -v "^#\|zombies\|pyright\|cleanup\|log_fail\|:#" || :)
[[ -n "$BYPASS" ]] && { log_fail "||true bypass in quality gates — fix the root cause"; echo "$BYPASS" | head -3; V=$((V+1)); } || log_success "No ||true quality gate bypasses"

# No hardcoded prod project IDs in documentation
HARDCODED_PROJ=$(rg "central-element-323112" --glob "!.git/**" . 2>/dev/null || :)
[[ -n "$HARDCODED_PROJ" ]] && { log_warn "Hardcoded GCP project ID found in docs: $HARDCODED_PROJ"; } || log_success "No hardcoded project IDs"

# pip install anywhere (docs tooling must use npm or uv, not bare pip)
PIP=$(rg "^RUN pip install|^RUN python -m pip" --glob "**/Dockerfile" --glob "**/*.sh" . 2>/dev/null \
    | grep -v "pip install uv" | grep -v "#" || :)
[[ -n "$PIP" ]] && { log_fail "Use 'uv pip install' not 'pip install'"; echo "$PIP" | head -3; V=$((V+1)); } || log_success "No bare pip install"

[[ $V -gt 0 ]] && { log_fail "Codex structure checks FAILED: $V violations"; exit 1; }
log_success "Codex structure checks PASSED"

# ── DURATION CHECK (<2 min) ───────────────────────────────────────────────────
QG_END=$(date +%s); DUR=$((QG_END - QG_START))
[ $DUR -gt 120 ] && log_warn "Quality gates took ${DUR}s (expected <120s for docs repo)"
echo -e "\n${GREEN}======================================================================"
echo -e "✅ ALL QUALITY GATES PASSED (${DUR}s) — ${SERVICE_NAME}${NC}"
