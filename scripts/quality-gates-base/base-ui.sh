#!/usr/bin/env bash
# quality-gates-base-ui v2.0 — owned by unified-trading-pm
#
# Shared quality-gate body for TypeScript/React UI repos.
# Do NOT edit per-repo — this file is the SSOT for all UI gate logic.
# To add a new check for all UIs, edit this file only.
#
# No required caller variables — UI repos are self-describing via package.json.
#
# Optional caller variables:
#   MAX_DURATION     — duration limit in seconds (default: 180)
#   MIN_UI_COVERAGE  — coverage floor % (default: 70)
#   CODEX_COLOUR_EXCLUDE_GLOBS — extra --glob exclusions for the hardcoded-colour check
#                                e.g. CODEX_COLOUR_EXCLUDE_GLOBS=("!src/lib/theme-overrides.ts")
#
# Version guard (optional): declare EXPECTED_BASE_VERSION="2.0" in stub before sourcing.
#
# Flags:
#   (default)    — Full: env + typecheck + lint + tests + codex + build
#   --test       — Typecheck + tests only (SKIP lint, codex, build)
#   --lint       — Typecheck + lint only (skip tests, codex, build)
#   --quick      — Typecheck + lint only (skip tests, codex, build); alias for --lint in UI
#   --no-fix     — no-op for UI; kept for interface compatibility with Python gate callers
#
# 6-stage gate (matches base-service.sh structure):
#   [0/6] ENVIRONMENT   — Node ≥22, required scripts, eslint/vitest present
#   [1/6] TYPECHECK     — tsc --noEmit, zero errors
#   [2/6] LINT          — ESLint --max-warnings 0; optional --fix
#   [3/6] UNIT TESTS    — vitest, coverage floor, zero-test guard
#   [3.5/6] UI CODEX    — rg-based: no console.*, no hardcoded colours, no localhost URLs,
#                         no @ts-ignore in src/, chart-theme.ts required when recharts present
#   [4/6] BUILD         — npm run build
#   [5/6] CI CONFIG     — cloudbuild.yaml / buildspec.aws.yaml schema validation
#
REQUIRED_BASE_VERSION="2.0"
if [[ -n "${EXPECTED_BASE_VERSION:-}" && "$EXPECTED_BASE_VERSION" != "$REQUIRED_BASE_VERSION" ]]; then
    echo "⚠️  Stub expects base v${EXPECTED_BASE_VERSION} but base is v${REQUIRED_BASE_VERSION}" >&2
fi

set -euo pipefail

# ── SHARED FOUNDATION (colors, logging, run_timeout, REPO_ROOT, CI_STATUS) ──
source "${BASH_SOURCE[0]%/*}/qg-common.sh"

# ── UI-SPECIFIC LOG OVERRIDES (stderr for failures, extra indentation) ───────
log_fail()    { echo -e "${RED}  ❌ $*${NC}" >&2; }
log_warn()    { echo -e "${YELLOW}  ⚠️  $*${NC}"; }

# ── PORTABLE TIMEOUT (enhanced for UI — SIGKILL escalation + bash fallback) ──
# Overrides qg-common.sh run_timeout with harder kill semantics for node processes.
run_timeout() {
    local secs=$1; shift
    if command -v timeout &>/dev/null; then
        timeout --signal=KILL "$((secs + 5))" timeout "$secs" "$@"
    elif command -v gtimeout &>/dev/null; then
        gtimeout --signal=KILL "$((secs + 5))" gtimeout "$secs" "$@"
    elif command -v perl &>/dev/null; then
        # perl alarm sends SIGALRM which terminates the child
        perl -e 'alarm shift; exec @ARGV' -- "$secs" "$@"
    else
        # Last resort: background the command, wait with timeout, kill if needed
        "$@" &
        local pid=$!
        ( sleep "$secs"; kill -TERM "$pid" 2>/dev/null; sleep 3; kill -KILL "$pid" 2>/dev/null ) &
        local watchdog=$!
        wait "$pid" 2>/dev/null
        local rc=$?
        kill "$watchdog" 2>/dev/null; wait "$watchdog" 2>/dev/null
        return $rc
    fi
}

# Per-step timeouts (seconds). Override in caller stub if needed.
STEP_TIMEOUT_TYPECHECK=${STEP_TIMEOUT_TYPECHECK:-60}
STEP_TIMEOUT_LINT=${STEP_TIMEOUT_LINT:-60}
STEP_TIMEOUT_TEST=${STEP_TIMEOUT_TEST:-120}
STEP_TIMEOUT_BUILD=${STEP_TIMEOUT_BUILD:-90}

# ── PROCESS CLEANUP (prevent zombie node processes) ──────────────────────────
# When 14 UIs run in parallel and the parent (Cursor/shell) dies, orphaned
# node/tsc/vitest/esbuild processes accumulate. This kills the entire process
# tree rooted at this script on any exit — normal, error, or signal.
# pkill -P only kills direct children. Node spawns npm→node→vitest→workers,
# so we recurse to catch the full tree.
_qg_kill_tree() {
    local pid=$1
    local children
    children=$(pgrep -P "$pid" 2>/dev/null) || true
    for child in $children; do
        _qg_kill_tree "$child"
    done
    kill -TERM "$pid" 2>/dev/null || true
}
_qg_kill_children() {
    # Walk descendants but never kill $$. _qg_kill_tree $$ would SIGTERM self at
    # the end → INT/TERM/HUP trap → exit 130 even on success, silently aborting
    # set -e callers like quickmerge.sh after Phase 1.
    local children
    children=$(pgrep -P $$ 2>/dev/null) || true
    for child in $children; do
        _qg_kill_tree "$child"
    done
    sleep 0.3
    # Force-kill any survivors (node can ignore SIGTERM during I/O)
    local stragglers
    stragglers=$(pgrep -P $$ 2>/dev/null) || true
    for pid in $stragglers; do
        kill -KILL "$pid" 2>/dev/null || true
    done
}

# ── UI TRAP OVERRIDES (add _qg_kill_children to EXIT, handle INT/TERM/HUP) ──
# Overrides the default _qg_record_failure-only trap from qg-common.sh
trap '_qg_record_failure; _qg_kill_children' EXIT
trap '_qg_kill_children; exit 130' INT TERM HUP

# ── MODE ───────────────────────────────────────────────────────────────────
SKIP_LINT=false
SKIP_TESTS=false
SKIP_BUILD=false
SKIP_CODEX=false
FIX_MODE=false
IGNORE_TIMEOUT=${IGNORE_TIMEOUT:-false}
SKIP_VERSION_ALIGNMENT=false
for arg in "$@"; do
  case "$arg" in
    --test)           SKIP_LINT=true;  SKIP_BUILD=true; SKIP_CODEX=true ;;
    --lint)           SKIP_TESTS=true; SKIP_BUILD=true; SKIP_CODEX=true ;;
    --quick)          SKIP_TESTS=true; SKIP_BUILD=true; SKIP_CODEX=true ;;
    --skip-lint)      SKIP_LINT=true ;;
    --fix)            FIX_MODE=true ;;
    --no-fix)         FIX_MODE=false ;;
    --ignore-timeout) IGNORE_TIMEOUT=true ;;
    --skip-version-alignment) SKIP_VERSION_ALIGNMENT=true ;;
  esac
done

# ── SERVICE_NAME (required by version-alignment-gate.sh) ─────────────────────
# UI repos don't have PACKAGE_NAME — derive from the git directory name.
SERVICE_NAME="${SERVICE_NAME:-$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || basename "$PROJECT_ROOT")}"

# ── VERSION ALIGNMENT GATE ────────────────────────────────────────────────────
if [ "$SKIP_VERSION_ALIGNMENT" = false ]; then
  _VA_GATE="${WORKSPACE_ROOT:-$(cd "$REPO_ROOT/.." && pwd)}/unified-trading-pm/scripts/quality-gates-base/version-alignment-gate.sh"
  [[ -f "$_VA_GATE" ]] && source "$_VA_GATE" || echo "⚠️  version-alignment-gate.sh not found (skipping)"
fi

# ── [0/6] ENVIRONMENT ──────────────────────────────────────────────────────
log_section "[0/6] ENVIRONMENT"
if [ ! -f "package.json" ]; then
  log_fail "No package.json found — run from repo root"; exit 1
fi

# Node version ≥ 22 — the UI stack (jsdom@29 / vite@8 / vitest@4) has ESM-only
# transitive deps (@exodus/bytes, @csstools/css-calc) the vitest forks pool can only
# require() on Node's stable require(esm) (Node ≥22; Node 20 crashes ERR_REQUIRE_ESM).
# CI runs Node 22. Fail loud here so a Node<22 host gets a clear message instead of a
# cryptic worker crash. SSOT: plans/active/issues/deployment_ui_test_env_esm_breakage_2026_06_16.md.
NODE_VER=$(node --version 2>/dev/null | grep -oE '[0-9]+' | head -1 || echo "0")
if [ "${NODE_VER:-0}" -lt 22 ]; then
  log_fail "Node ≥22 required for the UI stack (jsdom@29 ESM deps), found $(node --version 2>/dev/null || echo 'none') — install Node 22 (see .nvmrc); CI uses 22"
  exit 1
fi
log_success "Node $(node --version)"

# Required scripts
for _script in typecheck lint build; do
  if ! node -e "const s=require('./package.json').scripts||{}; process.exit('${_script}' in s ? 0 : 1)" 2>/dev/null; then
    log_fail "package.json missing required script: \"${_script}\""
    exit 1
  fi
done
log_success "Required scripts present (typecheck, lint, build)"

# Test script (warn if missing — library repos may not have one yet)
if ! node -e "const s=require('./package.json').scripts||{}; process.exit('test' in s ? 0 : 1)" 2>/dev/null; then
  log_warn "package.json has no \"test\" script — unit tests will be skipped"
fi

# ESLint version (informational)
ESLINT_VER=$(npx eslint --version 2>/dev/null || echo "not found")
log_success "ESLint ${ESLINT_VER}"

# vitest (warn if missing — older repos may not have it yet)
if node_modules/.bin/vitest --version >/dev/null 2>&1; then
  VITEST_VER=$(node_modules/.bin/vitest --version 2>/dev/null || echo "?")
  log_success "vitest ${VITEST_VER}"
else
  log_warn "vitest not found in node_modules — run npm install; unit tests will be skipped"
fi

# ── [1/6] TYPE CHECK ────────────────────────────────────────────────────────
log_section "[1/6] TYPE CHECK"
if _out=$(run_timeout "$STEP_TIMEOUT_TYPECHECK" npm run typecheck 2>&1); then
  log_success "TypeScript type check passed"
else
  echo "$_out"
  log_fail "TypeScript type check FAILED (timeout=${STEP_TIMEOUT_TYPECHECK}s)"; exit 1
fi

# ── [2/6] LINT ──────────────────────────────────────────────────────────────
if [ "$SKIP_LINT" = false ]; then
  log_section "[2/6] LINT"
  if [ "$FIX_MODE" = true ]; then
    run_timeout "$STEP_TIMEOUT_LINT" npm run lint -- --fix >/dev/null 2>&1 || true
  fi
  # Target src/ directly — avoids traversing node_modules, dist, coverage, etc.
  # Falls back to npm run lint if src/ doesn't exist (non-standard layout).
  if [ -d "src" ]; then
    if _out=$(run_timeout "$STEP_TIMEOUT_LINT" npx eslint src/ --ext .ts,.tsx 2>&1); then
      log_success "ESLint passed"
    else
      echo "$_out"
      log_fail "ESLint FAILED (timeout=${STEP_TIMEOUT_LINT}s)"; exit 1
    fi
  else
    if _out=$(run_timeout "$STEP_TIMEOUT_LINT" npm run lint 2>&1); then
      log_success "ESLint passed"
    else
      echo "$_out"
      log_fail "ESLint FAILED (timeout=${STEP_TIMEOUT_LINT}s)"; exit 1
    fi
  fi
else
  log_section "[2/6] LINT — skipped (--test / --lint / --quick)"
fi

# ── [2.5/6] ORPHAN-ROUTE AUDIT ───────────────────────────────────────────────
# Blocks new orphan pages — Next.js app/ routes that are not reachable from any
# declared navigation surface. Opts in per-repo: requires both
# `scripts/orphan-audit.ts` and `scripts/.orphan-audit-baseline.json` to exist.
# Skip with SKIP_ORPHAN_AUDIT=1 (human-only escape hatch) or in --test mode.
# SSOT: unified-trading-pm/codex/06-coding-standards/orphan-audit.md.
if [ "$SKIP_LINT" = false ] && [ "${SKIP_ORPHAN_AUDIT:-0}" != "1" ] && \
   [ -f "scripts/orphan-audit.ts" ] && [ -f "scripts/.orphan-audit-baseline.json" ]; then
  log_section "[2.5/6] ORPHAN-ROUTE AUDIT"
  if _out=$(run_timeout 60 npx --yes tsx scripts/orphan-audit.ts --blocking 2>&1); then
    echo "$_out" | tail -5
    log_success "Orphan-route audit passed (no new orphans vs baseline)"
  else
    echo "$_out"
    log_fail "Orphan-route audit FAILED — new unreachable page(s) introduced"
    exit 1
  fi
elif [ -f "scripts/orphan-audit.ts" ] && [ ! -f "scripts/.orphan-audit-baseline.json" ]; then
  log_warn "orphan-audit.ts found but no baseline — advisory-only (run: npm run orphan-audit:write-baseline)"
fi

# ── [2.6] ENVIRONMENT MODE INVARIANTS ───────────────────────────────────────
# Static structural checks enforcing the three-axis environment/auth/data philosophy.
# Requires: tests/e2e/environment-mode-invariants.spec.ts (no server needed).
# SSOT: unified-trading-pm/codex/08-workflows/environment-mode-philosophy.md
if [ -f "tests/e2e/environment-mode-invariants.spec.ts" ]; then
  log_section "[2.6] ENVIRONMENT MODE INVARIANTS"
  if _out=$(run_timeout 60 npx playwright test tests/e2e/environment-mode-invariants.spec.ts \
      --config playwright.invariants.config.ts --project=chromium --reporter=dot 2>&1); then
    log_ok "Environment mode invariants passed"
  else
    echo "$_out"
    log_fail "Environment mode invariants FAILED — see output above"
    GATE_FAILURES=$((GATE_FAILURES + 1))
  fi
fi

# ── [3/6] UNIT TESTS + COVERAGE ─────────────────────────────────────────────
# Runs only when package.json has a "test" script that is NOT playwright-only.
# After tests: enforces MIN_UI_COVERAGE floor (default 70) by reading
# coverage/coverage-summary.json — belt-and-suspenders alongside vitest thresholds.
# Zero-test guard: hard fail if 0 tests ran (prevents silent pass on broken glob patterns).
MIN_UI_COVERAGE=${MIN_UI_COVERAGE:-70}
if [ "$SKIP_TESTS" = false ]; then
  log_section "[3/6] UNIT TESTS + COVERAGE"
  if node -e "const s=require('./package.json').scripts||{}; process.exit(('test' in s && !s.test.includes('playwright')) ? 0 : 1)" 2>/dev/null; then
    if _out=$(run_timeout "$STEP_TIMEOUT_TEST" env CI=true npm test -- --run --coverage 2>&1); then
      # ── Zero-test guard ──────────────────────────────────────────────────
      _TESTS_RAN=$(echo "$_out" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1 || echo "0")
      if [ "${_TESTS_RAN:-0}" -eq 0 ]; then
        echo "$_out"
        log_fail "ZERO TESTS RAN — QG cannot pass with no test execution"
        log_fail "Check vitest.config.ts 'include' pattern matches your test files"
        exit 1
      fi
      log_success "${_TESTS_RAN} tests passed"
      # ── Coverage floor check ─────────────────────────────────────────────
      SUMMARY="coverage/coverage-summary.json"
      if [ -f "$SUMMARY" ]; then
        LINES_PCT=$(node -e "const d=require('./${SUMMARY}'); console.log(d.total&&d.total.lines?d.total.lines.pct:0)" 2>/dev/null || echo "0")
        LINES_INT=${LINES_PCT%.*}
        if [ "${LINES_INT:-0}" -lt "$MIN_UI_COVERAGE" ]; then
          echo "$_out"
          log_fail "Coverage floor FAILED: ${LINES_PCT}% lines < ${MIN_UI_COVERAGE}% required"
          log_fail "Add tests or lower MIN_UI_COVERAGE — do NOT just skip this check"
          exit 1
        fi
        log_success "Coverage: ${LINES_PCT}% lines ≥ ${MIN_UI_COVERAGE}%"
      else
        echo "$_out"
        log_fail "coverage/coverage-summary.json not found — ensure vitest.config.ts has reporter: ['json-summary']"
        exit 1
      fi
    else
      echo "$_out"
      log_fail "Unit tests FAILED"; exit 1
    fi
  else
    log_warn "No unit test script found — skipping coverage (only e2e/playwright detected)"
  fi
else
  log_section "[3/6] UNIT TESTS — skipped (--lint / --quick)"
fi

# ── [3.5/6] UI CODEX CHECKS ──────────────────────────────────────────────────
# rg-based pattern checks — equivalent of base-service.sh [5/6] codex compliance.
# All checks are blocking. Add per-repo exclusions using the CODEX_*_EXCLUDE_GLOBS arrays
# (set in quality-gates.sh before sourcing this script) and document in QUALITY_GATE_BYPASS_AUDIT.md.
if [ "$SKIP_CODEX" = false ] && [ -d "src" ]; then
  log_section "[3.5/6] UI CODEX CHECKS"
  _CODEX_V=0

  # ── console.* in production code ───────────────────────────────────────────
  # Bypass: add entries to CODEX_CONSOLE_EXCLUDE_GLOBS before sourcing (e.g. "!src/lib/logger.ts")
  _CONSOLE_EXTRA=()
  for g in "${CODEX_CONSOLE_EXCLUDE_GLOBS[@]+"${CODEX_CONSOLE_EXCLUDE_GLOBS[@]}"}"; do
    _CONSOLE_EXTRA+=(--glob "$g")
  done
  _CONSOLE_HITS=$(rg "console\.(log|warn|error|debug|info)" src/ \
    --glob "!src/**/*.test.*" --glob "!src/setupTests.*" \
    "${_CONSOLE_EXTRA[@]+"${_CONSOLE_EXTRA[@]}"}" 2>/dev/null || true)
  if [ -n "$_CONSOLE_HITS" ]; then
    log_fail "console.* in production code — remove or replace with structured logging:"
    echo "$_CONSOLE_HITS" | head -5
    _CODEX_V=$((_CODEX_V + 1))
  else
    log_success "No console.* in production code"
  fi

  # ── Hardcoded hex colours / rgb() ──────────────────────────────────────────
  # Bypass: add entries to CODEX_COLOUR_EXCLUDE_GLOBS (e.g. "!src/lib/brand-colours.ts")
  _COLOUR_EXTRA=()
  for g in "${CODEX_COLOUR_EXCLUDE_GLOBS[@]+"${CODEX_COLOUR_EXCLUDE_GLOBS[@]}"}"; do
    _COLOUR_EXTRA+=(--glob "$g")
  done
  _COLOUR_HITS=$(rg '#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|rgb\(|rgba\(' src/ \
    --glob "!src/**/*.test.*" --glob "!src/lib/chart-theme.*" \
    --glob "!src/globals.css" --glob "!src/**/*.css" \
    "${_COLOUR_EXTRA[@]+"${_COLOUR_EXTRA[@]}"}" 2>/dev/null || true)
  if [ -n "$_COLOUR_HITS" ]; then
    log_fail "Hardcoded colour values — use CSS vars (--color-*) or Tailwind classes:"
    echo "$_COLOUR_HITS" | head -5
    _CODEX_V=$((_CODEX_V + 1))
  else
    log_success "No hardcoded colours"
  fi

  # ── Hardcoded localhost URLs ────────────────────────────────────────────────
  # Bypass: add entries to CODEX_LOCALHOST_EXCLUDE_GLOBS (e.g. "!src/lib/dev-utils.ts")
  _LOCALHOST_EXTRA=()
  for g in "${CODEX_LOCALHOST_EXCLUDE_GLOBS[@]+"${CODEX_LOCALHOST_EXCLUDE_GLOBS[@]}"}"; do
    _LOCALHOST_EXTRA+=(--glob "$g")
  done
  _LOCALHOST_HITS=$(rg 'http://localhost:[0-9]+' src/ \
    --glob "!src/**/*.test.*" --glob "!src/lib/mock-api.*" --glob "!src/mock/**" \
    "${_LOCALHOST_EXTRA[@]+"${_LOCALHOST_EXTRA[@]}"}" 2>/dev/null || true)
  if [ -n "$_LOCALHOST_HITS" ]; then
    log_fail "Hardcoded localhost URL — use import.meta.env.VITE_* instead:"
    echo "$_LOCALHOST_HITS" | head -5
    _CODEX_V=$((_CODEX_V + 1))
  else
    log_success "No hardcoded localhost URLs"
  fi

  # ── @ts-ignore / @ts-expect-error in src/ ──────────────────────────────────
  _TS_IGNORE_HITS=$(rg '@ts-ignore|@ts-expect-error' src/ \
    --glob "!src/**/*.test.*" 2>/dev/null || true)
  if [ -n "$_TS_IGNORE_HITS" ]; then
    log_fail "@ts-ignore in production code — fix the type error instead of suppressing it:"
    echo "$_TS_IGNORE_HITS" | head -5
    _CODEX_V=$((_CODEX_V + 1))
  else
    log_success "No @ts-ignore in production code"
  fi

  # ── chart-theme.ts required when recharts is a dependency ──────────────────
  if node -e "const p=require('./package.json'); process.exit(p.dependencies?.recharts ? 0 : 1)" 2>/dev/null; then
    if [ ! -f "src/lib/chart-theme.ts" ]; then
      log_fail "recharts in dependencies but src/lib/chart-theme.ts missing"
      log_fail "Create src/lib/chart-theme.ts with CHART_COLORS, TOOLTIP_STYLE, GRID_STYLE, AXIS_STYLE using CSS vars"
      _CODEX_V=$((_CODEX_V + 1))
    else
      log_success "chart-theme.ts present (recharts dependency)"
    fi
  fi

  # ── No duplicate test files ─────────────────────────────────────────────────
  _DUP=$(find src/ tests/ -name "*_extended.test.*" -o -name "*_additional.test.*" 2>/dev/null || true)
  if [ -n "$_DUP" ]; then
    log_fail "Duplicate test files found — expand existing test files instead:"
    echo "$_DUP"
    _CODEX_V=$((_CODEX_V + 1))
  else
    log_success "No duplicate test files"
  fi

  [ "$_CODEX_V" -gt 0 ] && { log_fail "UI codex checks FAILED ($_CODEX_V violation(s))"; exit 1; }
  log_success "UI codex checks passed"
else
  log_section "[3.5/6] UI CODEX CHECKS — skipped (--test / --lint / --quick or no src/)"
fi

# ── [4/6] BUILD ──────────────────────────────────────────────────────────────
if [ "$SKIP_BUILD" = false ]; then
  log_section "[4/6] BUILD"
  if _out=$(run_timeout "$STEP_TIMEOUT_BUILD" npm run build 2>&1); then
    log_success "Build passed"
  else
    echo "$_out"
    log_fail "Build FAILED (timeout=${STEP_TIMEOUT_BUILD}s)"; exit 1
  fi
else
  log_section "[4/6] BUILD — skipped (--lint / --test / --quick)"
fi

# ── [5/6] BUILD CONFIG VALIDATION ────────────────────────────────────────────
# Validate cloudbuild.yaml and buildspec.aws.yaml when present (same as base-service STEP 5.17)
PM_ROOT="${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null && cd .. && pwd)}/unified-trading-pm"
if [ -f "cloudbuild.yaml" ]; then
  VALIDATOR="${PM_ROOT}/scripts/validation/validate-cloudbuild.py"
  if [ -f "$VALIDATOR" ]; then
    if _out=$(run_timeout 30 python3 "$VALIDATOR" cloudbuild.yaml 2>&1); then
      log_success "cloudbuild.yaml schema OK"
    else
      echo "$_out"
      log_fail "cloudbuild.yaml schema validation failed"; exit 1
    fi
  fi
fi
if [ -f "buildspec.aws.yaml" ]; then
  VALIDATOR="${PM_ROOT}/scripts/validation/validate-buildspec.py"
  if [ -f "$VALIDATOR" ]; then
    if _out=$(run_timeout 30 python3 "$VALIDATOR" buildspec.aws.yaml 2>&1); then
      log_success "buildspec.aws.yaml schema OK"
    else
      echo "$_out"
      log_fail "buildspec.aws.yaml schema validation failed"; exit 1
    fi
  fi
fi

# ── DURATION ───────────────────────────────────────────────────────────────
MAX_DURATION=${MAX_DURATION:-180}
QG_END=$(date +%s); DUR=$((QG_END - QG_START))
if [ "$IGNORE_TIMEOUT" != "true" ] && [ $DUR -gt $MAX_DURATION ]; then
    log_fail "Quality gates must complete in <${MAX_DURATION}s (took ${DUR}s)"
    exit 1
fi


# ── RECORD LOCAL PASS (ci_status=LOCAL_PASS when not in CI) ──────────────────
if ! _qg_update_ci_status_pass; then
    log_fail "Failed to update ci_status (LOCAL_PASS) in workspace-manifest.json"
    exit 1
fi
# DAG SVGs are GITIGNORED generated artifacts (item H, 2026-06-03): regenerate them on every local
# QG run so the codex/04-architecture symlinks stay fresh — gitignored output → zero worktree churn.
# The former MANIFEST_STATE_WRITER gate (single-writer-cron era, when these were tracked) is removed;
# ci_status gating is unaffected.
if [[ "${GITHUB_ACTIONS:-}" != "true" ]] && [[ -n "${WORKSPACE_ROOT:-}" ]]; then
    _MANIFEST="${WORKSPACE_ROOT}/unified-trading-pm/workspace-manifest.json"
    if [[ -f "$_MANIFEST" ]] && command -v python3 &>/dev/null; then
        _DAG_SCRIPT="${WORKSPACE_ROOT}/unified-trading-pm/scripts/manifest/generate_workspace_dag.py"
        if [[ -f "$_DAG_SCRIPT" ]]; then
            if ! python3 "$_DAG_SCRIPT"; then
                log_fail "Failed to regenerate WORKSPACE_MANIFEST_DAG.svg"
                exit 1
            fi
        fi
        _DATA_FLOW_SCRIPT="${WORKSPACE_ROOT}/unified-trading-pm/scripts/manifest/generate_data_flow_dag.py"
        if [[ -f "$_DATA_FLOW_SCRIPT" ]]; then
            if ! python3 "$_DATA_FLOW_SCRIPT"; then
                log_fail "Failed to regenerate DATA_FLOW_DAG.svg"
                exit 1
            fi
        fi
    fi
fi

# SHA sentinel for quickmerge Pass-2 (parity fix 2026-06-10): base-service.sh writes
# .qg_last_passed_sha on every COMPLETE green run, but base-ui.sh never did — so
# `quickmerge --agent` in UI repos ALWAYS hard-refused with "Pass 1 not run (SHA mismatch)"
# even straight after a green gate. Write it here, the single complete-green exit point.
_UI_REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
git rev-parse HEAD > "${_UI_REPO_ROOT}/.qg_last_passed_sha" 2>/dev/null \
    && echo "Sentinel written: .qg_last_passed_sha=$(cat "${_UI_REPO_ROOT}/.qg_last_passed_sha")" \
    || echo "Warning: could not write .qg_last_passed_sha (non-git dir?)"

echo -e "\n${GREEN}======================================================================"
echo -e "✅ ALL UI QUALITY GATES PASSED (${DUR}s) — base-ui.sh v2.0${NC}"
echo "======================================================================"
