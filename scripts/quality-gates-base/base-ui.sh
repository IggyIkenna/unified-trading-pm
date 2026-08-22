#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
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
# Fail closed on a venv that drifted from uv.lock (see qg_assert_venv_fresh).
qg_assert_venv_fresh

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
STEP_TIMEOUT_BUILD=${STEP_TIMEOUT_BUILD:-900}  # bumped 2026-06-20: the unified-trading-system-ui Next.js production build (~302 routes) legitimately exceeds 240s/420s cold-cache — raise the ceiling rather than skip the build (CLAUDE.md "bump MAX_DURATION over suppressing the time check")
STEP_TIMEOUT_INSTALL=${STEP_TIMEOUT_INSTALL:-180}  # added 2026-07-31 (deployment_ui_coverage_floor_red_preexisting): the pnpm/yarn frozen-lockfile install-freshness guard below is a fast (~1-2s measured) no-op once node_modules matches the lockfile; generous headroom only matters on a cold local store

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

# ── SIGNAL TRAP: loud "killed" marker on a genuinely-CAUGHT kill signal ──
# Mirror of base-service.sh/base-library.sh's own signal trap (see base-service.sh for
# the full rationale) — shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md's
# silent-kill pattern is not tier-specific, so UI repos get the same fix. SIGKILL stays
# fundamentally UNCATCHABLE (no trap fires for it); this closes the CATCHABLE-signal
# slice only (SIGTERM/SIGINT/SIGHUP).
_qg_write_killed_marker() {
    local sig="$1" marker_dir marker
    marker_dir="${WORKSPACE_ROOT:-.}/.benchmarks/qg-governor"
    mkdir -p "$marker_dir" 2>/dev/null || true
    marker="${marker_dir}/killed.$$"
    {
        echo "killed_by_signal=${sig}"
        echo "pid=$$"
        echo "repo=${SERVICE_NAME:-unknown}"
        echo "killed_at_epoch=$(date +%s 2>/dev/null || echo 0)"
    } > "$marker" 2>/dev/null || true
    echo "❌ [quality-gates] received SIG${sig} — wrote kill marker (${marker}) before exit; a poller can now tell this apart from a still-running or a normal-exit run" >&2
}

# ── UI TRAP OVERRIDES (add _qg_kill_children to EXIT, handle INT/TERM/HUP) ──
# Overrides the default _qg_record_failure-only trap from qg-common.sh
trap '_qg_record_failure; _qg_kill_children' EXIT
trap '_qg_write_killed_marker INT; _qg_kill_children; exit 130' INT
trap '_qg_write_killed_marker TERM; _qg_kill_children; exit 130' TERM
trap '_qg_write_killed_marker HUP; _qg_kill_children; exit 130' HUP

# ── MODE ───────────────────────────────────────────────────────────────────
SKIP_LINT=false
SKIP_TESTS=false
SKIP_BUILD=false
SKIP_CODEX=false
FIX_MODE=false
IGNORE_TIMEOUT=${IGNORE_TIMEOUT:-false}
SKIP_VERSION_ALIGNMENT=false
UPDATE_CODEX_BASELINE=false
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
    --update-baseline) UPDATE_CODEX_BASELINE=true ;;
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

# ── AUTO DOCS-ONLY TIER (WS-L 2026-06-26 — content-derived, NOT a flag; mirror of base-service.sh) ──
# Pure-documentation changeset → skip the slow gates (tests, build, codex); ANY source/config file
# (.ts/.tsx/.js/.css/.json/.yaml/…) forces the full gate (no lazy bypass). Derived from the working
# tree, so the server v2 (committed PR, no uncommitted diff) always runs the full gate — the backstop.
# Engages only on an otherwise-full run; lint/format still runs; the sentinel still writes. Capture-
# and-test-empty avoids the fragile `grep -qv` combo.
_QG_DOCS_ONLY=false
if [ "${SKIP_TESTS}" = false ] && [ "${SKIP_BUILD}" = false ] && [ "${SKIP_CODEX}" = false ] && [ "${SKIP_LINT}" = false ]; then
    _qg_changed="$( { git diff HEAD --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null; \
                      git ls-files --others --exclude-standard 2>/dev/null; } | grep -vE '^[[:space:]]*$' | sort -u || true )"
    _qg_nondoc="$( printf '%s\n' "$_qg_changed" | grep -ivE '\.(md|mdc|rst|txt|svg|png|jpe?g|gif|ico)$' || true )"
    if [ -n "$_qg_changed" ] && [ -z "$_qg_nondoc" ]; then
        _QG_DOCS_ONLY=true
        SKIP_TESTS=true; SKIP_BUILD=true; SKIP_CODEX=true
        log_warn "DOCS-ONLY changeset ($(printf '%s\n' "$_qg_changed" | wc -l | tr -d ' ') file(s), all documentation) → skipping TESTS + BUILD + CODEX; lint/format still runs. Any source/config change forces the full gate; the server v2 always runs the full gate."
    fi
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

# ── PACKAGE-MANAGER INSTALL FRESHNESS (early guard) ──────────────────────────
# Hardens the vitest-presence check below against a stale/incomplete install that
# survives it: a lockfile/package-manager migration (e.g. npm->pnpm, de5b7af) or a
# new dependency (e.g. happy-dom, ee269ec) can land in a pre-existing clone whose
# node_modules/.bin/vitest still exists from BEFORE the change — every DOM test then
# errors at setup and coverage silently collapses toward 0%, with no attribution to
# the real cause (root-caused in
# plans/active/issues/deployment_ui_coverage_floor_red_preexisting_2026_07_31.md).
# Detect the package manager from its lockfile (same precedence as scripts/setup.sh:
# pnpm > yarn > npm) and verify node_modules actually matches it:
#   - pnpm/yarn: their own --frozen-lockfile install IS the authoritative sync check
#     and self-heals a stale install; measured ~1-2s no-op once already in sync
#     (matches what CI's "Install dependencies" step already runs on every push).
#   - npm: no fast frozen mode exists (`npm ci` always wipes node_modules — too slow
#     to run unconditionally on every QG invocation), so compare npm's own
#     installed-state marker (node_modules/.package-lock.json, an exact copy npm
#     writes after every successful install) against the committed lockfile instead.
PKG_MGR=""; PKG_LOCK=""
if [ -f "pnpm-lock.yaml" ]; then
  PKG_MGR="pnpm"; PKG_LOCK="pnpm-lock.yaml"
elif [ -f "yarn.lock" ]; then
  PKG_MGR="yarn"; PKG_LOCK="yarn.lock"
elif [ -f "package-lock.json" ]; then
  PKG_MGR="npm"; PKG_LOCK="package-lock.json"
fi

if [ -z "$PKG_MGR" ]; then
  log_warn "No pnpm-lock.yaml/yarn.lock/package-lock.json found — skipping install-freshness guard"
elif ! command -v "$PKG_MGR" &>/dev/null; then
  log_fail "$PKG_LOCK present but '$PKG_MGR' not on PATH — install: npm install -g $PKG_MGR"; exit 1
elif [ "$PKG_MGR" = "npm" ]; then
  if [ -f "node_modules/.package-lock.json" ] && cmp -s "package-lock.json" "node_modules/.package-lock.json"; then
    log_success "node_modules in sync with package-lock.json (npm)"
  else
    log_fail "node_modules is stale/incomplete vs package-lock.json — run 'npm install' locally to fix"; exit 1
  fi
else
  if _out=$(run_timeout "$STEP_TIMEOUT_INSTALL" "$PKG_MGR" install --frozen-lockfile 2>&1); then
    log_success "node_modules in sync with $PKG_LOCK ($PKG_MGR)"
  else
    echo "$_out"
    log_fail "'$PKG_MGR install --frozen-lockfile' FAILED — node_modules is stale/incomplete vs $PKG_LOCK, or $PKG_LOCK is out of sync with package.json. Run '$PKG_MGR install' locally to fix (commit the updated $PKG_LOCK if it changes)."
    exit 1
  fi
fi

# vitest (warn if missing — older repos may not have it yet)
if node_modules/.bin/vitest --version >/dev/null 2>&1; then
  VITEST_VER=$(node_modules/.bin/vitest --version 2>/dev/null || echo "?")
  log_success "vitest ${VITEST_VER}"
else
  log_warn "vitest not found in node_modules — run ${PKG_MGR:-npm} install; unit tests will be skipped"
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
#
# Source root resolution — src/-rooted repos search src/; Next.js App-Router repos
# (app/ directory, no src/ at all) search app/ + components/ + lib/, whichever exist.
# Without this, App-Router repos silently skipped this ENTIRE block forever (found
# 2026-07-21: unified-trading-system-ui had run quality-gates.sh with `[3.5/6]`
# never once firing, accumulating real console.log/any-type violations the whole
# time — see ui_codex_gate_blind_to_app_router_layout_2026_07_21.md). All exclude
# globs below use a leading `**/` so they match regardless of which root matched.
_CODEX_ROOTS=()
if [ -d "src" ]; then
  _CODEX_ROOTS=("src")
elif [ -d "app" ]; then
  for _d in app components lib; do
    [ -d "$_d" ] && _CODEX_ROOTS+=("$_d")
  done
fi

if [ "$SKIP_CODEX" = false ] && [ "${#_CODEX_ROOTS[@]}" -gt 0 ]; then
  log_section "[3.5/6] UI CODEX CHECKS"
  _CODEX_V=0

  # ── Per-category baseline ratchet (2026-07-21) ──────────────────────────────
  # A repo whose codex-violation backlog is measured far larger than believed
  # (unified_trading_system_ui_codex_violations_far_exceed_estimate_2026_07_21.md:
  # 1082 colour hits/100 files, 30 localhost hits, 84 console.* hits/49 files —
  # 10-80x the original manual-audit estimate) cannot go green in one pass, and
  # zero-tolerance blocks the WHOLE repo's pipeline for every future commit
  # regardless of what it touches. A CODEX_*_EXCLUDE_GLOBS bypass was considered
  # and rejected (operator decision) — it blinds whole categories so a genuinely
  # NEW violation in the excluded tree ships silently, a gate-coverage
  # regression. Instead: a per-repo, per-category SHRINKING baseline, identical
  # mechanism to base-service.sh's ruff_rule_ratchet_baseline.yaml /
  # no_empty_string_fallback_baseline.yaml — fails only on count ABOVE baseline
  # (net-new violations); count below baseline warns to ratchet down (never
  # raise a baseline to mask a regression). Baseline file is OPTIONAL — a repo
  # with none (e.g. deployment-ui) keeps today's zero-tolerance behavior
  # (baseline defaults to 0 per category), so this is purely additive.
  _CODEX_BASELINE_FILE="codex_ui_violation_baseline.json"
  _codex_baseline_for() {
    # $1 = category key (console|colour|localhost). Prints the baseline count (0 if absent).
    if [ -f "$_CODEX_BASELINE_FILE" ] && command -v jq >/dev/null 2>&1; then
      jq -r --arg k "$1" '.[$k] // 0' "$_CODEX_BASELINE_FILE" 2>/dev/null || echo 0
    else
      echo 0
    fi
  }
  _codex_ratchet_check() {
    # $1=category key  $2=human label  $3=hits (newline-separated, may be empty)
    local key="$1" label="$2" hits="$3" count baseline
    if [ -n "$hits" ]; then
      count=$(printf '%s\n' "$hits" | grep -c .)
    else
      count=0
    fi
    baseline=$(_codex_baseline_for "$key")
    if [ "$count" -gt "$baseline" ]; then
      log_fail "$label: $count > baseline $baseline (NEW violation(s) — fix them, or if the baseline itself is stale run --update-baseline after confirming no regression):"
      # `|| true`: a large $hits piped through `head -5` can SIGPIPE the producer once head
      # exits early (exit 141) — under this script's `set -euo pipefail` that would abort the
      # WHOLE quality-gates run right here, before ever reaching the final exit-1 (or, under
      # --update-baseline, before the baseline file is even written). Display-only; never let
      # it affect control flow.
      { printf '%s\n' "$hits" | head -5; } || true
      _CODEX_V=$((_CODEX_V + 1))
    elif [ "$count" -lt "$baseline" ]; then
      log_warn "$label: $count below baseline $baseline — ratchet $_CODEX_BASELINE_FILE DOWN (re-run --update-baseline)"
    else
      log_success "$label: $count (at baseline, no new violations)"
    fi
  }

  # ── console.* in production code ───────────────────────────────────────────
  # Bypass: add entries to CODEX_CONSOLE_EXCLUDE_GLOBS before sourcing (e.g. "!**/lib/logger.ts")
  _CONSOLE_EXTRA=()
  for g in "${CODEX_CONSOLE_EXCLUDE_GLOBS[@]+"${CODEX_CONSOLE_EXCLUDE_GLOBS[@]}"}"; do
    _CONSOLE_EXTRA+=(--glob "$g")
  done
  _CONSOLE_HITS=$(rg "console\.(log|warn|error|debug|info)" "${_CODEX_ROOTS[@]}" \
    --glob "!**/*.test.*" --glob "!**/setupTests.*" \
    "${_CONSOLE_EXTRA[@]+"${_CONSOLE_EXTRA[@]}"}" 2>/dev/null || true)
  _codex_ratchet_check "console" "console.* in production code" "$_CONSOLE_HITS"

  # ── Hardcoded hex colours / rgb() ──────────────────────────────────────────
  # Bypass: add entries to CODEX_COLOUR_EXCLUDE_GLOBS (e.g. "!**/lib/brand-colours.ts")
  _COLOUR_EXTRA=()
  for g in "${CODEX_COLOUR_EXCLUDE_GLOBS[@]+"${CODEX_COLOUR_EXCLUDE_GLOBS[@]}"}"; do
    _COLOUR_EXTRA+=(--glob "$g")
  done
  _COLOUR_HITS=$(rg '#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|rgb\(|rgba\(' "${_CODEX_ROOTS[@]}" \
    --glob "!**/*.test.*" --glob "!**/chart-theme.*" \
    --glob "!**/globals.css" --glob "!**/*.css" \
    "${_COLOUR_EXTRA[@]+"${_COLOUR_EXTRA[@]}"}" 2>/dev/null || true)
  _codex_ratchet_check "colour" "Hardcoded colour values (use CSS vars / Tailwind classes)" "$_COLOUR_HITS"

  # ── Hardcoded localhost URLs ────────────────────────────────────────────────
  # Bypass: add entries to CODEX_LOCALHOST_EXCLUDE_GLOBS (e.g. "!**/lib/dev-utils.ts")
  _LOCALHOST_EXTRA=()
  for g in "${CODEX_LOCALHOST_EXCLUDE_GLOBS[@]+"${CODEX_LOCALHOST_EXCLUDE_GLOBS[@]}"}"; do
    _LOCALHOST_EXTRA+=(--glob "$g")
  done
  _LOCALHOST_HITS=$(rg 'http://localhost:[0-9]+' "${_CODEX_ROOTS[@]}" \
    --glob "!**/*.test.*" --glob "!**/mock-api.*" --glob "!**/mock/**" \
    "${_LOCALHOST_EXTRA[@]+"${_LOCALHOST_EXTRA[@]}"}" 2>/dev/null || true)
  _codex_ratchet_check "localhost" "Hardcoded localhost URL (use import.meta.env.VITE_* instead)" "$_LOCALHOST_HITS"

  if [ "$UPDATE_CODEX_BASELINE" = true ]; then
    if command -v jq >/dev/null 2>&1; then
      _CONSOLE_N=$([ -n "$_CONSOLE_HITS" ] && printf '%s\n' "$_CONSOLE_HITS" | grep -c . || echo 0)
      _COLOUR_N=$([ -n "$_COLOUR_HITS" ] && printf '%s\n' "$_COLOUR_HITS" | grep -c . || echo 0)
      _LOCALHOST_N=$([ -n "$_LOCALHOST_HITS" ] && printf '%s\n' "$_LOCALHOST_HITS" | grep -c . || echo 0)
      jq -n --argjson console "$_CONSOLE_N" --argjson colour "$_COLOUR_N" --argjson localhost "$_LOCALHOST_N" \
        '{console: $console, colour: $colour, localhost: $localhost}' >"$_CODEX_BASELINE_FILE"
      log_success "Wrote $_CODEX_BASELINE_FILE (console=$_CONSOLE_N colour=$_COLOUR_N localhost=$_LOCALHOST_N)"
    else
      log_fail "--update-baseline requires jq, not found on PATH"
      _CODEX_V=$((_CODEX_V + 1))
    fi
  fi

  # ── @ts-ignore / @ts-expect-error ──────────────────────────────────────────
  _TS_IGNORE_HITS=$(rg '@ts-ignore|@ts-expect-error' "${_CODEX_ROOTS[@]}" \
    --glob "!**/*.test.*" 2>/dev/null || true)
  if [ -n "$_TS_IGNORE_HITS" ]; then
    log_fail "@ts-ignore in production code — fix the type error instead of suppressing it:"
    echo "$_TS_IGNORE_HITS" | head -5
    _CODEX_V=$((_CODEX_V + 1))
  else
    log_success "No @ts-ignore in production code"
  fi

  # ── chart-theme.ts required when recharts is a dependency ──────────────────
  # src/-rooted repos nest lib/ under src/; App-Router repos have lib/ as its own top-level
  # root (a sibling of app/, not nested under it) — `${_CODEX_ROOTS[0]}/lib/...` was always
  # "app/lib/chart-theme.ts" on App-Router repos, which can never exist. Same blind-spot class
  # as the rg-based checks above (ui_codex_gate_blind_to_app_router_layout_2026_07_21.md).
  if [ -d "src" ]; then
    _CHART_THEME_PATH="src/lib/chart-theme.ts"
  else
    _CHART_THEME_PATH="lib/chart-theme.ts"
  fi
  if node -e "const p=require('./package.json'); process.exit(p.dependencies?.recharts ? 0 : 1)" 2>/dev/null; then
    if [ ! -f "$_CHART_THEME_PATH" ]; then
      log_fail "recharts in dependencies but $_CHART_THEME_PATH missing"
      log_fail "Create $_CHART_THEME_PATH with CHART_COLORS, TOOLTIP_STYLE, GRID_STYLE, AXIS_STYLE using CSS vars"
      _CODEX_V=$((_CODEX_V + 1))
    else
      log_success "chart-theme.ts present (recharts dependency)"
    fi
  fi

  # ── No duplicate test files ─────────────────────────────────────────────────
  _DUP=$(find "${_CODEX_ROOTS[@]}" tests/ -name "*_extended.test.*" -o -name "*_additional.test.*" 2>/dev/null || true)
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
  log_section "[3.5/6] UI CODEX CHECKS — skipped (--test / --lint / --quick or no src/ or app/)"
fi

# ── [4/6] BUILD ──────────────────────────────────────────────────────────────
# One automatic retry on the TIMEOUT class only (rc 124/137 from run_timeout's
# GNU-timeout wrapping): a cold-cache build legitimately trips the budget once
# and passes on a warm retry (ui_build_warm_cache_2026_06_17.md), while a
# genuine hang still fails twice. A non-timeout build failure (real compile/
# lint-in-build error) is NOT retried — that would just burn the budget twice
# on a failure a retry can never fix.
if [ "$SKIP_BUILD" = false ]; then
  log_section "[4/6] BUILD"
  if _out=$(run_timeout "$STEP_TIMEOUT_BUILD" npm run build 2>&1); then
    log_success "Build passed"
  else
    _build_rc=$?
    if [ "$_build_rc" -eq 124 ] || [ "$_build_rc" -eq 137 ]; then
      log_warn "Build TIMED OUT (rc=${_build_rc}, timeout=${STEP_TIMEOUT_BUILD}s) — retrying once (cold-cache class)"
      if _out=$(run_timeout "$STEP_TIMEOUT_BUILD" npm run build 2>&1); then
        log_success "Build passed on retry (cold-cache trip self-recovered)"
      else
        echo "$_out"
        log_fail "Build FAILED again on retry (timeout=${STEP_TIMEOUT_BUILD}s) — genuine hang, not cold-cache"; exit 1
      fi
    else
      echo "$_out"
      log_fail "Build FAILED (rc=${_build_rc}, timeout=${STEP_TIMEOUT_BUILD}s)"; exit 1
    fi
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

# ── [5.97] DeFi CONTRACT-ADDRESS CITATION (.py parity) ───────────────────────
# UI repos are TS, but can carry .py schema-mirror files (e.g. internal-contracts
# protocol_sdks.py) that hold on-chain contract addresses. base-service.sh +
# base-library.sh run STEP 5.97 on those; this closes the last ungated surface so
# a UI repo's .py addresses are cited too, and any NEW .py address is caught. Uses
# the SAME Python checker (skips gracefully if python+yaml or the PM checkout is
# absent). SSOT: defi_onchain_derivable_values_and_date_drift_2026_06_20.md Phase 5.
log_section "[5.97] DeFi ADDRESS-CITATION (.py)"
_DC_WS="${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null && cd .. && pwd)}"
_DC_CHECKER="${_DC_WS}/unified-trading-pm/scripts/quality_gates/check_defi_address_citations.py"
_DC_PY=""
for _c in "${_DC_WS}/.venv-workspace/bin/python" "$(command -v python3 2>/dev/null)"; do
    [ -n "$_c" ] && [ -x "$_c" ] && "$_c" -c 'import yaml' >/dev/null 2>&1 && { _DC_PY="$_c"; break; }
done
if [ -f "$_DC_CHECKER" ] && [ -n "$_DC_PY" ]; then
    _DC_REPO="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo "$PROJECT_ROOT")")"
    if "$_DC_PY" "$_DC_CHECKER" --workspace-root "$_DC_WS" --scope "$_DC_REPO" >/tmp/defi_ui_cite.log 2>&1; then
        if grep -q '^\[WARN\]' /tmp/defi_ui_cite.log 2>/dev/null; then
            log_warn "DeFi .py citation: $(grep -c '^\[WARN\]' /tmp/defi_ui_cite.log) baselined uncited address(es); 0 new"
        else
            log_success "DeFi .py address-citation gate passed (no new uncited .py contract addresses)"
        fi
    else
        log_fail "DeFi .py address-citation gate: NEW uncited Ethereum address in a .py file — add '# DERIVED <YYYY-MM-DD> from <chain> <source>' on the same line, or '# QG-allow: defi-citation — <reason>' for factory-deployed pools:"
        cat /tmp/defi_ui_cite.log
        exit 1
    fi
else
    log_success "DeFi .py address-citation gate: skipped (checker or python+yaml unavailable on this host)"
fi

# ── [5.108] CLOUDBUILD TEMPLATE DRIFT (this repo vs its shared template) ─────
# UI parity for base-service.sh STEP 5.108. The same checker unified-trading-pm's
# own gate runs fleet-wide, re-run here scoped to THIS repo so drift fails in the
# repo that INTRODUCED it rather than on the next unrelated PM commit on someone
# else's machine (measured twice in two days — see the step comment in
# base-service.sh and
# /plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md).
# Same baseline, same never-raise semantics — only the detection POINT moves.
# UI repos have no guaranteed .venv (deployment-ui has none), so this probes for
# a python with yaml exactly like the .py address-citation step above and skips
# gracefully rather than failing a gate for a missing interpreter.
log_section "[5.108] CLOUDBUILD TEMPLATE DRIFT"
_CBD_WS="${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null && cd .. && pwd)}"
_CBD_CHECKER="${_CBD_WS}/unified-trading-pm/scripts/quality_gates/check_cloudbuild_template_drift.py"
_CBD_PY=""
for _c in "${_CBD_WS}/.venv-workspace/bin/python" "$(command -v python3 2>/dev/null)"; do
    [ -n "$_c" ] && [ -x "$_c" ] && "$_c" -c 'import yaml' >/dev/null 2>&1 && { _CBD_PY="$_c"; break; }
done
if [ -f "$_CBD_CHECKER" ] && [ -n "$_CBD_PY" ]; then
    _CBD_REPO="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo "$PROJECT_ROOT")")"
    _CBD_LOG="${TMPDIR:-/tmp}/cloudbuild_template_drift_ui.log.$$"
    if "$_CBD_PY" "$_CBD_CHECKER" --workspace-root "$_CBD_WS" --repo "$_CBD_REPO" >"$_CBD_LOG" 2>&1; then
        if grep -q '^\[WARN\]' "$_CBD_LOG" 2>/dev/null; then
            log_warn "cloudbuild drift is BELOW baseline — ratchet cloudbuild_template_drift_baseline.yaml DOWN (re-run --update-baseline)"
        else
            log_success "cloudbuild.yaml carries no undrained content vs its shared template (at baseline)"
        fi
    else
        log_fail "cloudbuild drift: this repo's cloudbuild.yaml carries content its shared template does NOT. Forward-port it into unified-trading-pm/configs/cloudbuild-*-template.yaml — the baseline is SHRINK-ONLY, so --update-baseline will refuse to raise it:"
        cat "$_CBD_LOG"
        rm -f "$_CBD_LOG" 2>/dev/null
        exit 1
    fi
    rm -f "$_CBD_LOG" 2>/dev/null
else
    log_success "cloudbuild drift gate: skipped (checker or python+yaml unavailable on this host)"
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
# SENTINEL CONTRACT (WS-L #1014): write ONLY on a COMPLETE run. This exit point is reached even by
# partial runs (--lint / --test / --quick set SKIP_TESTS/SKIP_BUILD/SKIP_CODEX/SKIP_LINT), so it was
# UNGUARDED → a partial UI gate wrote a ship-ready sentinel → quickmerge --agent fast-greened a tree
# the full gate never verified. Guard it: tests + build + codex + lint must all have run.
if { [ "${SKIP_TESTS:-false}" = false ] && [ "${SKIP_BUILD:-false}" = false ] && [ "${SKIP_CODEX:-false}" = false ] && [ "${SKIP_LINT:-false}" = false ]; } || [ "${_QG_DOCS_ONLY:-false}" = true ]; then
    _UI_REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
    git rev-parse HEAD > "${_UI_REPO_ROOT}/.qg_last_passed_sha" 2>/dev/null \
        && echo "Sentinel written: .qg_last_passed_sha=$(cat "${_UI_REPO_ROOT}/.qg_last_passed_sha")" \
        || echo "Warning: could not write .qg_last_passed_sha (non-git dir?)"
    # Configuration binding (qg_sentinel_environment_blind_2026_07_23.md item 2) — mirror
    # of base-service.sh: append (not overwrite) the resolved ENVIRONMENT/DEPLOYMENT_ENV so
    # quickmerge's sentinel check can refuse a config mismatch. `head -1` (every SHA reader)
    # is unaffected; an old bare-SHA sentinel still parses correctly.
    { printf 'ENVIRONMENT=%s\n' "${ENVIRONMENT:-}"; printf 'DEPLOYMENT_ENV=%s\n' "${DEPLOYMENT_ENV:-}"; } \
        >> "${_UI_REPO_ROOT}/.qg_last_passed_sha" 2>/dev/null || true
else
    echo "Sentinel NOT written — partial UI run (skip flags active). Run full quality-gates.sh to enable quickmerge --agent fast-path."
fi

echo -e "\n${GREEN}======================================================================"
echo -e "✅ ALL UI QUALITY GATES PASSED (${DUR}s) — base-ui.sh v2.0${NC}"
echo "======================================================================"
