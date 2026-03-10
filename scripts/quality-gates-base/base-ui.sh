#!/usr/bin/env bash
# quality-gates-base-ui v1.0 — owned by unified-trading-pm
#
# Shared quality-gate body for TypeScript/React UI repos.
# Do NOT edit per-repo — this file is the SSOT for all UI gate logic.
# To add a new check for all UIs, edit this file only.
#
# No required caller variables — UI repos are self-describing via package.json.
#
# Optional caller variables:
#   MAX_DURATION  — duration limit in seconds (default: 180)
#
# Version guard (optional): declare EXPECTED_BASE_VERSION="1.0" in stub before sourcing.
#
# Flags:
#   (default)    — Full: typecheck + lint + tests + build
#   --test       — Typecheck + tests only (SKIP lint + build)
#   --lint       — Typecheck + lint only (skip tests + build)
#   --quick      — Typecheck + lint only (skip tests + build); alias for --lint in UI
#   --no-fix     — no-op for UI; kept for interface compatibility with Python gate callers
#
REQUIRED_BASE_VERSION="1.0"
if [[ -n "${EXPECTED_BASE_VERSION:-}" && "$EXPECTED_BASE_VERSION" != "$REQUIRED_BASE_VERSION" ]]; then
    echo "⚠️  Stub expects base v${EXPECTED_BASE_VERSION} but base is v${REQUIRED_BASE_VERSION}" >&2
fi

set -euo pipefail

QG_START=$(date +%s)

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log_success() { echo -e "${GREEN}  ✅ $*${NC}"; }
log_fail()    { echo -e "${RED}  ❌ $*${NC}" >&2; }
log_warn()    { echo -e "${YELLOW}  ⚠️  $*${NC}"; }
log_section() { echo -e "\n${GREEN}── $* ──${NC}"; }

# ── MODE ───────────────────────────────────────────────────────────────────
SKIP_LINT=false
SKIP_TESTS=false
SKIP_BUILD=false
for arg in "$@"; do
  case "$arg" in
    --test)   SKIP_LINT=true;  SKIP_BUILD=true ;;   # tests + typecheck only
    --lint)   SKIP_TESTS=true; SKIP_BUILD=true ;;   # lint + typecheck only
    --quick)  SKIP_TESTS=true; SKIP_BUILD=true ;;   # alias for --lint in UI
    --no-fix) ;;  # no-op; kept for interface compatibility
  esac
done

echo "======================================================================"
echo "  UI Quality Gates — $(basename "$(pwd)")"
echo "======================================================================"

# ── [1] TYPE CHECK ─────────────────────────────────────────────────────────
log_section "[1/4] TYPE CHECK"
if [ ! -f "package.json" ]; then
  log_fail "No package.json found"; exit 1
fi
if npm run typecheck 2>&1; then
  log_success "TypeScript type check passed"
else
  log_fail "TypeScript type check FAILED"; exit 1
fi

# ── [2] LINT ───────────────────────────────────────────────────────────────
if [ "$SKIP_LINT" = false ]; then
  log_section "[2/4] LINT"
  if npm run lint 2>&1; then
    log_success "ESLint passed"
  else
    log_fail "ESLint FAILED"; exit 1
  fi
else
  log_section "[2/4] LINT — skipped (--test)"
fi

# ── [3] UNIT TESTS + COVERAGE ──────────────────────────────────────────────
# Runs only when package.json has a "test" script that is NOT playwright-only
# (vitest/jest produce coverage; playwright e2e does not).
if [ "$SKIP_TESTS" = false ]; then
  log_section "[3/4] UNIT TESTS + COVERAGE"
  if node -e "const s=require('./package.json').scripts||{}; process.exit(('test' in s && !s.test.includes('playwright')) ? 0 : 1)" 2>/dev/null; then
    if npm test -- --coverage --reporter=verbose 2>&1; then
      log_success "Unit tests + coverage passed"
    else
      log_fail "Unit tests FAILED"; exit 1
    fi
  else
    log_warn "No unit test script found — skipping coverage (only e2e/playwright detected)"
  fi
else
  log_section "[3/4] UNIT TESTS — skipped (--lint / --quick)"
fi

# ── [4] BUILD ──────────────────────────────────────────────────────────────
if [ "$SKIP_BUILD" = false ]; then
  log_section "[4/4] BUILD"
  if npm run build 2>&1; then
    log_success "Build passed"
  else
    log_fail "Build FAILED"; exit 1
  fi
else
  log_section "[4/4] BUILD — skipped (--lint / --test / --quick)"
fi

# ── [5] BUILD CONFIG VALIDATION ─────────────────────────────────────────────
# Validate cloudbuild.yaml and buildspec.aws.yaml when present (same as base-service STEP 5.17)
PM_ROOT="${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null && cd .. && pwd)}/unified-trading-pm"
run_timeout() { timeout "${1:-30}" "${@:2}" 2>/dev/null || true; }
if [ -f "cloudbuild.yaml" ]; then
  VALIDATOR="${PM_ROOT}/scripts/validation/validate-cloudbuild.py"
  if [ -f "$VALIDATOR" ]; then
    if run_timeout 30 python3 "$VALIDATOR" cloudbuild.yaml 2>/dev/null; then
      log_success "cloudbuild.yaml schema OK"
    else
      log_fail "cloudbuild.yaml schema validation failed"; exit 1
    fi
  fi
fi
if [ -f "buildspec.aws.yaml" ]; then
  VALIDATOR="${PM_ROOT}/scripts/validation/validate-buildspec.py"
  if [ -f "$VALIDATOR" ]; then
    if run_timeout 30 python3 "$VALIDATOR" buildspec.aws.yaml 2>/dev/null; then
      log_success "buildspec.aws.yaml schema OK"
    else
      log_fail "buildspec.aws.yaml schema validation failed"; exit 1
    fi
  fi
fi

# ── DURATION ───────────────────────────────────────────────────────────────
MAX_DURATION=${MAX_DURATION:-180}
QG_END=$(date +%s); DUR=$((QG_END - QG_START))
[ $DUR -gt $MAX_DURATION ] && { log_fail "Quality gates must complete in <${MAX_DURATION}s (took ${DUR}s)"; exit 1; }

echo -e "\n${GREEN}======================================================================"
echo -e "✅ ALL UI QUALITY GATES PASSED (${DUR}s)${NC}"
echo "======================================================================"
