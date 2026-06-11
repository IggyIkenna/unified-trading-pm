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
#   PYTEST_WORKERS    — explicit worker count override; default is 1 (memory-frugal)
#   LOCAL_DEPS        — e.g. ("unified-trading-library")
#
# Optional caller variables:
#   MAX_DURATION      — duration limit in seconds (default: 300); set to 600 for PM/codex
#   IGNORE_TIMEOUT    — set to "true" to skip duration check (useful when running parallel suites)
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

# ── SHARED FOUNDATION (colors, logging, run_timeout, REPO_ROOT, CI_STATUS) ──
source "${BASH_SOURCE[0]%/*}/qg-common.sh"
cd "$PROJECT_ROOT"

# ── QG RESOURCE GOVERNANCE ────────────────────────────────────────────────────
# Plan: quality_gates_resource_contention_speedup_2026_06_02.
# (1) Host concurrency governor — token bucket so at most K QG heavy-phases run
#     concurrently across ALL slots. Sourced here so qg_governor_acquire/release
#     bracket the heavy phases below.
source "${BASH_SOURCE[0]%/*}/qg-host-governor.sh"
# (2) Thread-pool caps — stop one repo's native BLAS/OMP pools (numpy/sklearn/
#     lightgbm/xgboost) from fanning out across every core under multi-slot load
#     (measured: ml-service spawned 100+ threads). With the governor's K-cap this
#     keeps the box from oversubscribing. Per-repo override: export QG_THREAD_CAP.
export OMP_NUM_THREADS="${QG_THREAD_CAP:-2}" OPENBLAS_NUM_THREADS="${QG_THREAD_CAP:-2}" \
       MKL_NUM_THREADS="${QG_THREAD_CAP:-2}" NUMEXPR_NUM_THREADS="${QG_THREAD_CAP:-2}"
# (3) Shared ruff cache across worktrees/slots — the default .ruff_cache lives in
#     each worktree and defeats cross-slot reuse; repoint to a host-shared dir.
export RUFF_CACHE_DIR="${RUFF_CACHE_DIR:-${TMPDIR:-/tmp}/qg-ruff-cache}"
# (4) Green sentinel (qg-repo-green-sentinel): a CONSERVATIVE content hash of the
#     working tree + gate-script + tool versions. When it is byte-identical to the
#     last FULL green run, the heavy phases (TESTS + TYPE CHECK) are skipped — that
#     content was already fully verified, incl. coverage. ANY change → different hash
#     → full run. Light phases (codex/production) still run so external-state drift is
#     caught. Robust: a malformed/empty hash NEVER triggers a skip. Escape:
#     QG_SENTINEL_DISABLE=true.  Separate file (.qg_content_sentinel) so quickmerge's
#     .qg_last_passed_sha (git HEAD) is untouched.
_qg_content_hash() {
    {
        git rev-parse HEAD 2>/dev/null || echo no-head
        git diff HEAD 2>/dev/null                                       # uncommitted tracked changes
        # untracked files — but EXCLUDE QG artifacts that change every run (else the
        # hash self-references and the sentinel can never hit).
        git ls-files --others --exclude-standard 2>/dev/null \
            | grep -vE '(^|/)(\.qg_content_sentinel|\.qg_last_passed_sha|\.qg_cache/|coverage\.xml|\.coverage|\.pytest_cache/|\.ruff_cache/|__pycache__/)' \
            | sort | while IFS= read -r _f; do
                [ -f "$_f" ] && sha256sum "$_f" 2>/dev/null
            done
        sha256sum "${BASH_SOURCE[0]}" "${BASH_SOURCE[0]%/*}/qg-host-governor.sh" 2>/dev/null  # gate logic
        "${RUFF_CMD:-ruff}" --version 2>/dev/null
        "${BASEDPYRIGHT_CMD:-basedpyright}" --version 2>/dev/null
        "${PYTHON_CMD:-python3}" --version 2>/dev/null                   # tool versions
    } | sha256sum | awk '{print $1}'
}

# ╔══ MEMORY GOVERNANCE [OOM MITIGATION — added 2026-05-15] ═══════════════════╗
# Cap heavy subprocesses (pytest, basedpyright) at QG_MEM_CAP. Prevents one
# runaway process from OOM-killing the whole machine.
#
# Incident 2026-05-15: single python process hit 79GB RSS (basedpyright/pytest),
# kernel oom-killer fired, took down VS Code + all worker agent sessions on
# 93 GB dev box.
#
# Linux: uses `systemd-run --user --scope -p MemoryMax=N -p MemorySwapMax=0`.
#        Process exceeding cap dies with exit 137 (SIGKILL by cgroup). Rest of
#        the box is unaffected. Requires bash 4+ and systemd user instance
#        (available out-of-the-box on Ubuntu/Debian/Fedora since systemd v226).
# macOS: NO equivalent cgroup memory cap without root. Falls through to
#        MEM_WRAP=() empty array — pytest/basedpyright run unwrapped. The
#        PYTEST_WORKERS=1 default below still applies. Warning printed once
#        per QG run when QG_MEM_CAP is non-zero on a non-systemd host.
#
# Per-user override (recommended — put in ~/.bashrc or ~/.zshrc):
#   export QG_MEM_CAP=15G    # 96GB workstation, can spare more for QG
#   export QG_MEM_CAP=8G     # 24GB laptop, leave room for other apps
#   export QG_MEM_CAP=0      # disable cap (also disables the macOS warning)
#
# Per-call override:
#   QG_MEM_CAP=20G bash scripts/quality-gates.sh
#
# ── TO REVERT (once OOM root cause is properly fixed elsewhere) ───────────────
# Option 1 (runtime, no code change):  export QG_MEM_CAP=0  in your shell.
# Option 2 (full code revert):         delete this whole block AND remove the
#   `"${MEM_WRAP[@]}"` prefix from the pytest + basedpyright call-sites below
#   (search for "MEM_WRAP" in this file — should find 3 prefixed call-sites).
# Option 2 partial revert is also safe: deleting just this block leaves the
# call-sites with `"${MEM_WRAP[@]}"` undefined — bash will error. Either drop
# this block AND the prefixes, or use Option 1.
#
# Full SSOT: codex/06-coding-standards/quality-gates-memory-governance.md
# ╚════════════════════════════════════════════════════════════════════════════╝
QG_MEM_CAP="${QG_MEM_CAP:-10G}"
MEM_WRAP=()
if [[ "$QG_MEM_CAP" != "0" ]]; then
    if command -v systemd-run >/dev/null 2>&1 \
        && systemd-run --user --scope -p MemoryMax=100M --quiet -- true >/dev/null 2>&1; then
        # MemorySwapMax=0 prevents thrashing into swap before hitting the cap —
        # without it the kernel swaps-out other processes to keep the runaway
        # alive, slowing the whole box before SIGKILL fires.
        MEM_WRAP=(systemd-run --user --scope -p MemoryMax="$QG_MEM_CAP" -p MemorySwapMax=0 --quiet --)
    elif [[ -z "${_QG_OOM_WARN_SHOWN:-}" ]]; then
        # macOS / non-systemd Linux / containers without --user manager.
        # Warn once per shell so the macOS teammate knows the cap is inactive.
        echo "⚠️  QG_MEM_CAP=$QG_MEM_CAP set but systemd-run unavailable on this host" >&2
        echo "    → running pytest + basedpyright without hard memory cap" >&2
        echo "    → on macOS / small-RAM hosts: keep parallel QGs to 2 slots max" >&2
        echo "    → silence this warning: export QG_MEM_CAP=0  in your shell rc" >&2
        export _QG_OOM_WARN_SHOWN=1
    fi
fi

# ── TRAP: set ci_status=FAILING on non-zero script exit ──────────────────────
_qg_exit_handler() { local rc=$?; [ "$rc" -ne 0 ] && _qg_update_ci_status_failing 2>/dev/null || true; }
trap '_qg_exit_handler' EXIT

# ── SIZE LIMITS (per coding standards) ────────────────────────────────────────
# Per-repo overrides: set MAX_FILE_LINES / MAX_FUNCTION_LINES / MAX_METHOD_LINES
# BEFORE sourcing this script (${VAR:-default} preserves pre-set values).
MAX_FILE_LINES=${MAX_FILE_LINES:-900}; FILE_WARN_LINES=${FILE_WARN_LINES:-700}
MAX_FUNCTION_LINES=${MAX_FUNCTION_LINES:-200}; MAX_CLASS_LINES=${MAX_CLASS_LINES:-900}; MAX_METHOD_LINES=${MAX_METHOD_LINES:-50}

# ── MODE ──────────────────────────────────────────────────────────────────────
# FIX_MODE DEFAULTS TO FALSE (2026-06-10): AUTO-FIX's tree-wide `prettier --write "**/*"`
# reformats files outside the caller's commit → a stray default-mode run leaves foreign
# reformats as worktree dirt + jams the FF-pull. Canonical agent path is already `--no-fix`;
# default it so a bare run can't churn. Per-commit formatting = scoped prettier-autostage hook;
# opt into a deliberate tree reformat with `--fix`. (QG_PROFILE branch below keeps fix-mode on.)
FIX_MODE=false; QUICK_MODE=false; RUN_LINT=true; RUN_TESTS=true; SKIP_TYPECHECK=false; ACT_MODE=false; IGNORE_TIMEOUT=${IGNORE_TIMEOUT:-false}; SKIP_VERSION_ALIGNMENT=false
for arg in "$@"; do
    case $arg in
        --no-fix) FIX_MODE=false ;;   --quick) QUICK_MODE=true ;;
        --lint) RUN_TESTS=false ;;    --test) RUN_LINT=false ;;
        --skip-tests) RUN_TESTS=false ;; --skip-lint) RUN_LINT=false ;;
        --fix) FIX_MODE=true ;;       --skip-typecheck) SKIP_TYPECHECK=true ;;
        --act) ACT_MODE=true ;;       --ignore-timeout) IGNORE_TIMEOUT=true ;;
        --skip-version-alignment) SKIP_VERSION_ALIGNMENT=true ;;
        --skip-codex) SKIP_CODEX_FLAG=true ;;
    esac
done

# ── QG_SLICE — CI parallel-jobs selector (latency reduction 2026-06-10) ───────
# The CI reusable workflow (python-quality-gates-v2.yml) fans the ONE monolithic
# ~12-min serial gate into PARALLEL jobs, each invoking this script with a slice:
#   QG_SLICE=tests       → ENVIRONMENT + [3] TESTS only        (the pytest cost; dominant)
#   QG_SLICE=typecheck   → ENVIRONMENT + [4] TYPE CHECK only   (basedpyright cost)
#   QG_SLICE=lint-codex  → ENVIRONMENT + [2] LINT + [3.5/3.6] + [5] CODEX (incl.
#                          pip-audit + bandit) + [5.5] WORKFLOW LINT + [5.6] SERVICE
#                          INFRA + the per-repo stub POST-GATES (falls through to stub)
# Wall-time becomes max(slice), not sum(slices). The three slices PARTITION the gate
# with ZERO overlap and ZERO lost coverage — every check the monolith ran runs in
# exactly one slice. UNSET (the default) = the full, untouched monolithic run, so
# every LOCAL invocation + every existing caller is behaviour-identical. The
# tests/typecheck slice jobs early-exit after their phase; lint-codex and the full
# run fall through to the stub's post-gates.
#
# WHY pip-audit is folded into lint-codex (not its own 4th slice): the entire [5]
# CODEX section accumulates a SHARED violation counter `V` (codex checks + size
# checks + pip-audit + bandit all `V=$((V+1))` into one ceiling check at section
# end). Splitting pip-audit out would fork that counter — high-risk surgery on the
# fleet's critical gate for ~3min of pip-audit that runs in PARALLEL with the 715s
# pytest slice anyway (it is NOT on the critical path). Tradeoff documented in
# plans/archive/2026_06/cicd_v2_latency_reduction_2026_06_10.md Progress Log.
#
# Sentinel safety: a sliced run is a PARTIAL run by definition, so it must NEVER
# write `.qg_last_passed_sha` / `.qg_content_sentinel` (QG_SLICE forces
# QG_SENTINEL_DISABLE + the sentinel-write block is additionally guarded on QG_SLICE
# being empty). The CI aggregation job reports the required context only when ALL
# slices pass.
QG_SLICE="${QG_SLICE:-}"
case "$QG_SLICE" in
    ""|tests|typecheck|lint-codex) : ;;
    *) echo "❌ invalid QG_SLICE='${QG_SLICE}' (allowed: tests|typecheck|lint-codex|unset)" >&2; exit 2 ;;
esac
# _QG_RUN_CODEX — run [3.5]/[3.6] + the [5] CODEX-compliance body + [5.5]/[5.6] +
# stub post-gates. Default (full run): true. tests/typecheck slices set it false.
_QG_RUN_CODEX=true
if [ -n "$QG_SLICE" ]; then
    # A slice is a partial run — never touch the sentinel (it certifies the FULL surface).
    export QG_SENTINEL_DISABLE=true
    case "$QG_SLICE" in
        tests)      RUN_LINT=false; RUN_TESTS=true;  SKIP_TYPECHECK=true;  _QG_RUN_CODEX=false ;;
        typecheck)  RUN_LINT=false; RUN_TESTS=false; SKIP_TYPECHECK=false; _QG_RUN_CODEX=false ;;
        lint-codex) RUN_LINT=true;  RUN_TESTS=false; SKIP_TYPECHECK=true;  _QG_RUN_CODEX=true  ;;
    esac
fi
# _qg_slice_done <phase>: a slice job exits cleanly when ITS OWN phase just completed
# (arg = the phase that finished: tests|typecheck). No-op for the full run (QG_SLICE
# empty), for lint-codex (it must fall through to run the post-gates), and for a slice
# whose phase hasn't run yet. BUG FIX 2026-06-10: the previous arg-less version exited
# for tests|typecheck at the single post-TESTS call site, so QG_SLICE=typecheck exited
# BEFORE [4] TYPE CHECK ever ran — CI's typecheck leg was a silent no-op (false green;
# see ci_local_qg_parity_2026_06_08.md "PM basedpyright count skew").
_qg_slice_done() {
    if [ -n "$QG_SLICE" ] && [ "$QG_SLICE" = "${1:-}" ]; then
        echo -e "\n${GREEN:-}✅ QG_SLICE=${QG_SLICE} PASSED${NC:-}"
        exit 0
    fi
}

# ── QG_PROFILE forces a COMPLETE, no-skip run ────────────────────────────────
# Profiling must measure EVERY path, so all bypass flags (--no-fix / --quick /
# --skip-tests / --skip-lint / --skip-typecheck / --skip-codex) are overridden and the
# green content-sentinel is disabled. The <MAX_DURATION> meta-gate is the one thing relaxed
# (the wall-time IS the measurement — a slow single-core profile run must not false-fail).
if [[ "${QG_PROFILE:-}" == "1" ]]; then
    FIX_MODE=true; QUICK_MODE=false; RUN_LINT=true; RUN_TESTS=true; SKIP_TYPECHECK=false
    unset SKIP_CODEX_FLAG
    export QG_SENTINEL_DISABLE=true
    IGNORE_TIMEOUT=true
    QG_SLICE=""   # profiling measures the whole gate — ignore any slice selector
fi

# ── VERSION ALIGNMENT GATE ────────────────────────────────────────────────────
_VA_GATE="${WORKSPACE_ROOT:-$(cd "$REPO_ROOT/.." && pwd)}/unified-trading-pm/scripts/quality-gates-base/version-alignment-gate.sh"
[[ -f "$_VA_GATE" ]] && source "$_VA_GATE" || echo "⚠️  version-alignment-gate.sh not found (skipping)"

# ── DEP-CONTENT SYNC GATE (2026-06-08) ───────────────────────────────────────
# Local QG builds against the WORKING-TREE copy of every editable dep (tool.uv.sources
# path=…,editable=true), so a dirty/LDR-divergent dep (same pinned version) is invisible
# to the version gates yet green locally / red at staging. This gate refuses an INVISIBLE
# dep: each transitive editable dep must be clean + == its origin/live-defi-rollout ref.
# WARN by default; set DEP_CONTENT_GATE_BLOCK=1 to hard-fail (rule-11: flip to default-block
# only once the whole fleet is proven clean — e.g. after the current multi-slot session).
# Human-only escape: --allow-dirty-deps (taints the sentinel → cannot satisfy a promotion).
_DEP_GATE="${WORKSPACE_ROOT:-$(cd "$REPO_ROOT/.." && pwd)}/unified-trading-pm/scripts/cicd/check_dep_content_sync.py"
if [ -z "${CI:-}" ] && [ -z "${GITHUB_ACTIONS:-}" ] && [[ -f "$_DEP_GATE" ]]; then
    if python3 "$_DEP_GATE" --repo "$REPO_ROOT" ${DEP_CONTENT_ALLOW_DIRTY:+--allow-dirty-deps}; then
        :
    else
        if [ "${DEP_CONTENT_GATE_BLOCK:-0}" = "1" ]; then
            log_fail "Dep-content gate: a transitive editable dep is dirty or ahead-of-LDR-unpushed (see above)"
            exit 1
        else
            log_warn "Dep-content gate WARN (set DEP_CONTENT_GATE_BLOCK=1 to enforce; --allow-dirty-deps to bypass)"
        fi
    fi
fi

# ── BOOTSTRAP (local only; CI has its own setup) ─────────────────────────────
if [ -z "${GITHUB_ACTIONS:-}" ] && [ -z "${CI:-}" ] && [ -z "${CLOUD_BUILD:-}" ]; then
    command -v uv &>/dev/null || pip install "uv==0.10.8" --quiet
    # uv.lock freshness — WARN-ONLY, never blocking (2026-06-09). Nothing installs FROM the lock
    # (every path is `uv pip install -e .`, no `uv sync`/`--frozen`/`--locked`), so the lock is a
    # RECORD, not an enforced pin: the real dependency contract is the pyproject RANGE, which `uv pip
    # install` enforces at install (an out-of-range MAJOR fails to resolve = the signal). Blocking here
    # only added churn on the cosmetic internal-editable `version =` snapshot. Do NOT mutate uv.lock here
    # either (it dirtied trees + jammed the FF-pull cron). SSOT:
    # plans/active/dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md § Phase 1.
    uv lock --check 2>/dev/null || echo "⚠️  uv.lock out of sync with pyproject.toml (non-blocking — lock is a record, not a pin; pyproject range is the contract). Run 'uv lock' to refresh the record."
    [ ! -d ".venv" ] && uv venv .venv
    [ -f ".venv/bin/activate" ] && source .venv/bin/activate || :
    # LOCAL_DEPS (e.g. unified-trading-library / unified-api-contracts) are SIBLING repos at the
    # WORKSPACE ROOT, not nested under this repo — resolve workspace-root-first (the Path-B slot +
    # flat-workspace layout), falling back to the nested path for any legacy layout. The old
    # `${REPO_ROOT}/$lib`-only check silently skipped the editable install (the dir is never nested
    # under the repo) → workspace libs unresolved → a basedpyright `Unknown`-type CASCADE → the LOCAL
    # typecheck count inflated vs CI's in-image env (which has these installed). This is the PM
    # local↔CI parity gap: PM declares no UTL/UAC project dep, so this loop is its ONLY install path.
    # SSOT: plans/active/ci_local_qg_parity_2026_06_08.md.
    _ws_root="${WORKSPACE_ROOT:-$(cd "${REPO_ROOT:-.}/.." && pwd)}"
    for lib in "${LOCAL_DEPS[@]}"; do
        for _libcand in "${_ws_root}/$lib" "${REPO_ROOT}/$lib"; do
            [ -d "$_libcand" ] && { uv pip install -e "$_libcand" --quiet 2>/dev/null || :; break; }
        done
    done
    uv pip install -e . --quiet 2>/dev/null || :
fi
PYTHON_CMD=".venv/bin/python"; [ ! -f "$PYTHON_CMD" ] && PYTHON_CMD="python3"

# Git-aware: only check staged files when committing
STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | grep '\.py$' | tr '\n' ' ' || :)
# Guard: only include tests/ if the directory exists (Docker images exclude it via .dockerignore)
_tests_lint_dir=""; [ -d "tests" ] && _tests_lint_dir="tests/"
SOURCE_DIRS="${STAGED:-$SOURCE_DIR/ $_tests_lint_dir}"
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
# Flat deps violation check (fix-quickmerge-dev-extras): optional-dependencies are banned (CLAUDE.md)
if grep -q 'optional-dependencies' pyproject.toml 2>/dev/null; then
    log_fail "FLAT DEPS VIOLATION: [project.optional-dependencies] found in pyproject.toml — use [project.dependencies] only (see CLAUDE.md)"
    exit 1
fi
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
    qg_prof start autofix
    # Pre-format non-Python files with prettier to avoid pre-commit hook conflicts
    if command -v npx &>/dev/null; then
        _BASE_IGNORE="${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/.prettierignore-base"
        _PRETTIER_IGNORES="--ignore-path .gitignore $([ -f .prettierignore ] && echo '--ignore-path .prettierignore') $([ -f "$_BASE_IGNORE" ] && echo "--ignore-path $_BASE_IGNORE")"
        npx --yes prettier@3.6.2 --write --cache "**/*.{md,json,yaml,yml}" ${_PRETTIER_IGNORES} >/dev/null 2>&1 \
            || log_warn "Prettier not available or no files to format (skipping)"
    else
        log_warn "npx not available — skipping prettier pre-format (commit may require re-staging)"
    fi
    run_timeout 30 $RUFF_CMD format $SOURCE_DIRS >/dev/null 2>&1 || :
    run_timeout 30 $RUFF_CMD check --fix $SOURCE_DIRS >/dev/null 2>&1 || :
    qg_prof end autofix
    log_ok "Auto-fix complete"
fi

# ── [2] LINT (ruff, 30s) ──────────────────────────────────────────────────────
if [ "$RUN_LINT" = true ]; then
    log_section "[2/6] LINT"
    qg_prof start lint
    _lint_out=$(run_timeout 30 $RUFF_CMD check $SOURCE_DIRS 2>&1) || { echo "$_lint_out"; log_fail "Lint FAILED"; exit 1; }
    qg_prof end lint
fi

# ── GREEN SENTINEL: skip heavy phases when content is byte-identical to last full green ──
_QG_SENTINEL_HIT=false
_QG_SENTINEL_FILE="${PROJECT_ROOT}/.qg_content_sentinel"   # per-repo (REPO_ROOT is the workspace root)
_QG_CONTENT_HASH=""
if [ "${QG_SENTINEL_DISABLE:-false}" != "true" ]; then
    _QG_CONTENT_HASH="$(_qg_content_hash)"
    # Only a well-formed 64-char hash that EXACTLY matches the stored sentinel triggers
    # a skip — a malformed/empty hash can never accidentally match.
    if [ "${#_QG_CONTENT_HASH}" -eq 64 ] && [ -f "$_QG_SENTINEL_FILE" ] \
       && [ "$(cat "$_QG_SENTINEL_FILE" 2>/dev/null)" = "$_QG_CONTENT_HASH" ]; then
        _QG_SENTINEL_HIT=true
        log_success "Green sentinel HIT — working tree byte-identical to last full green; skipping TESTS + TYPE CHECK (light checks still run)"
    fi
fi

# ── HOST CONCURRENCY GOVERNOR: acquire before the heavy phases (TESTS + TYPECHECK) ──
# Blocks until <=K QG heavy-phases run host-wide (K=max(2, floor(cores/4))); released after
# TYPE CHECK. The OS auto-frees the flock on any early exit between here and release.
# No-op when QG_GOVERNOR_DISABLE=true or flock(1) is absent. Skipped on a sentinel hit
# (no heavy phase to govern).
[ "$_QG_SENTINEL_HIT" = true ] || qg_governor_acquire

# ── [3] TESTS (pytest, timeout, xdist, coverage) ──────────────────────────────
if [ "$RUN_TESTS" = true ] && [ "$_QG_SENTINEL_HIT" != true ]; then
    log_section "[3/6] TESTS"
    qg_prof start tests
    # Coverage floor governance (add-coverage-floor-governance)
    # Use PROJECT_ROOT (set by qg-common.sh from the caller stub's location) so we read
    # the CALLING repo's quality-gates.sh, not base-service.sh's own parent directory.
    # Bug fix: the old dirname/${BASH_SOURCE[0]}/../../ path resolved to unified-trading-pm's
    # own scripts/quality-gates.sh (MIN_COVERAGE=0) instead of the service repo's stub.
    _REPO_QG_SCRIPT="${PROJECT_ROOT}/scripts/quality-gates.sh"
    if [ -f "$_REPO_QG_SCRIPT" ] && [ -f "pyproject.toml" ]; then
        bash "$(cd "$(git rev-parse --show-toplevel)/../unified-trading-pm" 2>/dev/null && pwd)/scripts/coverage-floor-guard.sh" \
            "$_REPO_QG_SCRIPT" "pyproject.toml" 2>&1 || true
    fi
    check_emulator_reachability
    $PYTHON_CMD -c "import pytest_timeout" 2>/dev/null || { log_fail "pytest-timeout required: uv pip install pytest-timeout"; exit 1; }
    $PYTHON_CMD -c "import xdist" 2>/dev/null || { log_fail "pytest-xdist required: uv pip install pytest-xdist"; exit 1; }
    # Coverage off the hot path (qg-coverage-off-hotpath): per-line instrumentation
    # is a large CPU/RAM cost. Iterative/--quick runs skip it; the coverage floor is
    # still ENFORCED on the full gate run (quickmerge Pass 1) — merge gate unchanged.
    if [ "$QUICK_MODE" = true ]; then
        COV=""
    else
        COV="--cov=$SOURCE_DIR --cov-report=xml:coverage.xml --cov-fail-under=$MIN_COVERAGE"
    fi
    # ╔══ [OOM MITIGATION — added 2026-05-15] ═════════════════════════════════╗
    # OLD (pre-2026-05-15): xdist used 25% of logical CPUs by default. With 8
    # slots × ~4 workers × 2-4GB each peak the 93GB dev box hit OOM.
    #     _DEFAULT_WORKERS=$($PYTHON_CMD -c "import multiprocessing; print(max(1, multiprocessing.cpu_count()//4))" 2>/dev/null || echo 1)
    #     PARGS="-n ${PYTEST_WORKERS:-$_DEFAULT_WORKERS} --timeout=${PYTEST_TIMEOUT:-60} -q -r a --tb=short --no-header"
    # NEW (post-OOM): default 1 worker. Per-repo opt-in: set PYTEST_WORKERS=N
    # in the repo's scripts/quality-gates.sh BEFORE `source base-service.sh`.
    # TO REVERT: comment NEW line below, uncomment OLD pair above.
    # SSOT: codex/06-coding-standards/quality-gates-memory-governance.md
    # ╚════════════════════════════════════════════════════════════════════════╝
    # ── PYTEST PARALLELISM (latency reduction 2026-06-10) ────────────────────
    # The OOM mitigation above (default 1 worker) targets the SHARED 93 GB dev box
    # running ~8 slots concurrently — its risk is many slots × many workers. In CI
    # each quality-gates-v2 leg runs ALONE on its OWN GitHub runner (no shared host,
    # no slot contention), so xdist `-n auto` (= core count, 2-4 on ubuntu-latest)
    # is safe + cuts the dominant pytest leg ~2-4×. forks isolation is preserved
    # (xdist spawns worker SUBPROCESSES; --block-network-equivalent allow-hosts kept
    # below). LOCAL default stays 1 (the OOM-safe value) unless PYTEST_WORKERS is set.
    # Override precedence: explicit PYTEST_WORKERS (per-repo / per-call) wins; else CI
    # → auto, local → 1.
    if [ -n "${PYTEST_WORKERS:-}" ]; then
        _PYTEST_N="${PYTEST_WORKERS}"
    elif [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${CI:-}" ]; then
        _PYTEST_N="auto"
    else
        _PYTEST_N="1"
    fi
    PARGS="-n ${_PYTEST_N} --timeout=${PYTEST_TIMEOUT:-60} -q -r a --tb=short --no-header"
    # Per-repo test root override. Default: tests/unit/. Set PYTEST_UNIT_DIR before sourcing this
    # script to point at a different layout (e.g. PYTEST_UNIT_DIR="tests/" for per-family layouts).
    PYTEST_UNIT_DIR="${PYTEST_UNIT_DIR:-tests/unit/}"
    # RUN_INTEGRATION=true: include tests/integration/ when the directory exists.
    # Repos without tests/integration/ run unit tests only — no failure, no skip.
    # Integration tests are library contract tests (no real GCS/network calls).
    # Real-infra tests use @pytest.mark.live and require IS_TEST_RUN=true.
    _HAS_INTEGRATION=false
    [ -d "tests/integration" ] && \
        [ "$(find tests/integration -name 'test_*.py' 2>/dev/null | wc -l | tr -d ' ')" -gt 0 ] && \
        _HAS_INTEGRATION=true

    # Stream pytest output to a temp file instead of capturing it into a bash
    # variable. Large stderr (failing hypothesis traces, leaked blobs) can blow
    # bash's allocator (xrealloc: cannot allocate … bytes) when stuffed into RAM.
    _pytest_log="$(mktemp "${TMPDIR:-/tmp}/qg-pytest-out.XXXXXX")" || exit 1
    trap 'rm -f "${_pytest_log:-}"' EXIT INT HUP TERM

    # [OOM MITIGATION 2026-05-15] `"${MEM_WRAP[@]}"` prefix puts pytest in a
    # cgroup with hard memory cap on Linux (no-op + empty array on macOS).
    # OLD invocation (pre-2026-05-15) had no MEM_WRAP prefix:
    #     if ! $PYTHON_CMD -m pytest ${PYTEST_UNIT_DIR} ... ; then
    # TO REVERT: drop the `"${MEM_WRAP[@]}"` prefix from both branches below.
    if [ "$QUICK_MODE" = true ] || [ "$RUN_INTEGRATION" != "true" ] || [ "$_HAS_INTEGRATION" = false ]; then
        if ! "${MEM_WRAP[@]}" $PYTHON_CMD -m pytest ${PYTEST_UNIT_DIR} --allow-hosts=127.0.0.1,::1,localhost --allow-unix-socket $PARGS $COV >>"$_pytest_log" 2>&1; then
            cat "$_pytest_log"
            exit 1
        fi
        # Remind: when RUN_INTEGRATION=true but no integration tests exist yet, nudge author.
        if [ "$RUN_INTEGRATION" = "true" ] && [ "$_HAS_INTEGRATION" = false ] && [ "$QUICK_MODE" != true ]; then
            log_warn "RUN_INTEGRATION=true but no tests/integration/test_*.py found — add library contract tests"
        fi
    else
        if ! "${MEM_WRAP[@]}" $PYTHON_CMD -m pytest ${PYTEST_UNIT_DIR} tests/integration/ --allow-hosts=127.0.0.1,::1,localhost --allow-unix-socket $PARGS $COV >>"$_pytest_log" 2>&1; then
            cat "$_pytest_log"
            exit 1
        fi
    fi
    log_ok "Tests PASSED"

    # PM integration test — verifies repo integrates with PM scripts (quality-gates, setup, manifest)
    PM_INT_TEST="${REPO_ROOT}/unified-trading-pm/tests/integration/test_pm_scripts_integration.py"
    if [ -f "$PM_INT_TEST" ] && [ -d "${REPO_ROOT}/unified-trading-pm" ]; then
        if ! PROJECT_ROOT="$PROJECT_ROOT" $PYTHON_CMD -m pytest "$PM_INT_TEST" -v -m integration --tb=line -q 2>/dev/null; then
            log_fail "PM integration test failed — repo must integrate with PM scripts"
            exit 1
        fi
        log_ok "PM integration test PASSED"
    fi


    # Zero-test silent pass guard (fix-zero-test-silent-pass): QG must not pass with no tests executed
    _TESTS_RAN=$(grep -oE '[0-9]+ passed' "$_pytest_log" | grep -oE '[0-9]+' | head -1 || echo "0")
    _SKIPPED=$(grep -oE '[0-9]+ skipped' "$_pytest_log" | grep -oE '[0-9]+' | head -1 || echo "0")
    rm -f "$_pytest_log"
    trap - EXIT INT HUP TERM
    if [ "${_TESTS_RAN:-0}" -eq 0 ]; then
        log_fail "ZERO TESTS RAN — QG cannot pass with no test execution (zero-test-silent-pass guard)"
        exit 1
    fi
    if [ "${_TESTS_RAN:-0}" -gt 0 ] && [ "${_SKIPPED:-0}" -gt 0 ]; then
        _SKIP_RATE=$(( _SKIPPED * 100 / (_TESTS_RAN + _SKIPPED) ))
        [ "$_SKIP_RATE" -ge 90 ] && { log_warn "High skip rate: ${_SKIP_RATE}% of tests skipped (${_SKIPPED} skipped, ${_TESTS_RAN} ran)"; }
    fi

    [ ! -f "tests/unit/test_event_logging.py" ] && { log_fail "Missing tests/unit/test_event_logging.py"; exit 1; }
    [ ! -f "tests/unit/test_config.py" ] && { log_fail "Missing tests/unit/test_config.py"; exit 1; }
    log_ok "Required test files present"

    # No duplicate test files (test_*_extended.py, test_*_additional.py)
    DUP=$(find tests/ -name "test_*_extended.py" -o -name "test_*_additional.py" 2>/dev/null | head -5 || :)
    [[ -n "$DUP" ]] && { log_fail "Duplicate test files — expand existing files instead:"; echo "$DUP"; exit 1; }
    log_ok "No duplicate test files"

    # Integration test coverage for library deps (plan: integration_tests_codex_compliance)
    # Only enforced when RUN_INTEGRATION=true AND tests/integration/ exists with test files.
    _INT_DEP_CHECK="${REPO_ROOT}/unified-trading-pm/scripts/validation/check-integration-dep-coverage.py"
    if [ -f "$_INT_DEP_CHECK" ] && [ "${RUN_INTEGRATION}" = "true" ] && [ "${_HAS_INTEGRATION}" = true ]; then
        if ! $PYTHON_CMD "$_INT_DEP_CHECK" --repo "$SERVICE_NAME" --project-root "$PROJECT_ROOT" --manifest "${REPO_ROOT}/unified-trading-pm/workspace-manifest.json" 2>/dev/null; then
            log_fail "Integration test coverage missing for library deps — add tests in tests/integration/ that import each library. Bypass: QUALITY_GATE_BYPASS_AUDIT.md"
            exit 1
        fi
        log_ok "Integration dep coverage OK"
    fi
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
    log_ok "All pytest.mark.skip have reason comments"
    qg_prof end tests
fi
# QG_SLICE=tests finishes here (its one phase is the pytest run above).
_qg_slice_done tests

# ── [3.5] IMPORT PATTERN STANDARDS ───────────────────────────────────────────
# [3.5]+[3.6] are codex-adjacent static checks → part of the lint-codex slice
# (skipped by the tests/typecheck/pip-audit slices via _QG_RUN_CODEX).
if [ "${_QG_RUN_CODEX}" = true ]; then
log_section "[3.5/6] IMPORT PATTERNS"
IP="${REPO_ROOT}/unified-trading-pm/scripts/validation/check-import-patterns.py"
[ ! -f "$IP" ] && IP="${REPO_ROOT}/unified-trading-pm/scripts/check-import-patterns.py"  # pre-move fallback
if [[ "${SKIP_IMPORT_PATTERNS:-false}" == "true" ]]; then
    log_ok "Import patterns: skipped (SKIP_IMPORT_PATTERNS=true)"
elif [ -f "$IP" ]; then
    # Bypass: add --exclude flags for files whitelisted in QUALITY_GATE_BYPASS_AUDIT.md §1.2
    $PYTHON_CMD "$IP" --quiet 2>/dev/null && log_ok "Import patterns PASSED" || { log_fail "Import patterns FAILED"; exit 1; }
else
    log_warn "check-import-patterns.py not found (unified-trading-pm/scripts/)"
fi

# ── [3.6] NO SERVICE-AS-PACKAGE DEPS (services only) ───────────────────────────
# Importing another service as a package is a violation; interaction is via messaging only (topology DAG SSOT).
# Path lives under scripts/validation/ (the prior scripts/check-no-service-deps.py path never existed →
# the gate silently no-op'd fleet-wide). stderr is surfaced (not /dev/null'd) so the offending dep prints.
NSD="${REPO_ROOT}/unified-trading-pm/scripts/validation/check-no-service-deps.py"
if [ -f "$NSD" ]; then
    if $PYTHON_CMD "$NSD"; then
        log_success "No service-as-package deps"
    else
        log_fail "Service must not depend on another service repo (use messaging per topology)"
        exit 1
    fi
fi
fi  # _QG_RUN_CODEX (import-patterns + service-deps)

# ── [4] TYPE CHECK (basedpyright, 120s, zombie cleanup) ──────────────────────
log_section "[4/6] TYPE CHECK"
if [ "$SKIP_TYPECHECK" != "true" ] && [ "${_QG_SENTINEL_HIT:-false}" != true ]; then
    cleanup_zombie_pyright() {
        # || : on every line + after done: CI uses set -eo pipefail; grep exits 1 when no processes
        # found, which would kill the script before basedpyright even starts without these guards.
        _killed=0
        while read -r pid etime _; do
            # Parse ps etime [[DD-]hh:]mm:ss -> total minutes (kill if >= 30 min stale)
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
        [ "${_killed:-0}" -eq 0 ] && log_ok "No zombie basedpyright processes to kill" || :
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
    # Trap: kill only OUR basedpyright on Ctrl+C (avoids killing parallel QG runs in other repos)
    BP_PID=""
    trap '''[[ -n "$BP_PID" ]] && kill -9 $BP_PID 2>/dev/null''' INT TERM
    _bp_out="/tmp/bp_out.$$"
    # [OOM MITIGATION 2026-05-15] MEM_WRAP wraps basedpyright in cgroup mem cap (Linux only).
    # OLD: run_timeout "${PYRIGHT_TIMEOUT:-120}" "$BASEDPYRIGHT_CMD" "$SOURCE_DIR/" > "$_bp_out" 2>&1 &
    # TO REVERT: drop the `"${MEM_WRAP[@]}"` prefix below.
    qg_prof start typecheck
    run_timeout "${PYRIGHT_TIMEOUT:-120}" "${MEM_WRAP[@]}" "$BASEDPYRIGHT_CMD" "$SOURCE_DIR/" > "$_bp_out" 2>&1 &
    BP_PID=$!
    PYRIGHT_EXIT=0; wait $BP_PID || PYRIGHT_EXIT=$?  # 2026-05-26: fix || true bug that swallowed exit code
    qg_prof end typecheck
    trap - INT TERM
    PYRIGHT_OUT=$(cat "$_bp_out" 2>/dev/null); rm -f "$_bp_out"
    ERROR_COUNT=$(echo "$PYRIGHT_OUT" | grep -c " error:" || :)
    WARN_COUNT=$(echo "$PYRIGHT_OUT" | grep -c " warning:" || :)
    if [ "${PYRIGHT_EXIT}" -ne 0 ] && [ "${ERROR_COUNT:-0}" -eq 0 ] && [ "${WARN_COUNT:-0}" -eq 0 ]; then
        echo "$PYRIGHT_OUT"; log_fail "Type check FAILED/timeout (exit=${PYRIGHT_EXIT})"; exit 1
    fi
    if [ "${WARN_COUNT:-0}" -gt 0 ]; then
        echo "$PYRIGHT_OUT"
        log_fail "Type check FAILED — $WARN_COUNT warning(s) (zero-warning policy: promote all rules to error in [tool.basedpyright])"; exit 1
    fi
    _max_bp_errors="${BASEDPYRIGHT_MAX_ERRORS:-}"
    if [ -n "$_max_bp_errors" ]; then
        if [ "${ERROR_COUNT:-0}" -gt "${_max_bp_errors}" ]; then
            echo "$PYRIGHT_OUT"
            log_fail "Type check FAILED — ${ERROR_COUNT} error(s) > BASEDPYRIGHT_MAX_ERRORS=${_max_bp_errors} (ratchet down to fix errors)"; exit 1
        elif [ "${ERROR_COUNT:-0}" -gt 0 ]; then
            log_warn "Type check: ${ERROR_COUNT}/${_max_bp_errors} errors within ceiling — ratchet BASEDPYRIGHT_MAX_ERRORS down as errors are fixed"
        else
            log_ok "Type check PASSED (0 errors, 0 warnings)"
        fi
    elif [ "${ERROR_COUNT:-0}" -gt 0 ]; then
        log_warn "Type check: ${ERROR_COUNT} basedpyright error(s) — set BASEDPYRIGHT_MAX_ERRORS in quality-gates.sh to enforce error ceiling"
    else
        log_ok "Type check PASSED (0 errors, 0 warnings)"
    fi
    # Baseline growth guard (add-baseline-growth-ci-guard): basedpyright baseline files can only shrink
    if git diff --name-only 2>/dev/null | grep -q '.basedpyright-baseline.json'; then
        _BASELINE_ADDS=$(git diff .basedpyright-baseline.json 2>/dev/null | grep '^+' | grep -v '^+++' | wc -l | tr -d ' ')
        if [ "${_BASELINE_ADDS:-0}" -gt 0 ]; then
            log_fail "BASELINE GROWTH: ${_BASELINE_ADDS} new suppressions added to .basedpyright-baseline.json — fix the type errors instead"
            exit 1
        fi
    fi
fi
[ "$SKIP_TYPECHECK" = "true" ] && echo -e "${YELLOW}⚠️  Type check SKIPPED (--skip-typecheck flag)${NC}"

# ── HOST CONCURRENCY GOVERNOR: release the token — heavy phases (TESTS + TYPECHECK)
# are done; the lighter codex/validator phases run ungoverned. (OS auto-frees on exit.)
# No-op when a sentinel hit meant we never acquired.
[ "${_QG_SENTINEL_HIT:-false}" = true ] || qg_governor_release

# QG_SLICE=typecheck finishes here (basedpyright [4] was its only phase).
_qg_slice_done typecheck

# QG_SLICE=tests and QG_SLICE=typecheck have already exited above (TESTS / TYPE CHECK
# are their only phases). Everything from [5] onward (codex + pip-audit + bandit +
# [5.5]/[5.6] + the stub post-gates) is the lint-codex slice and the full run — both
# reach here, so [5] needs no extra slice guard (the early-exits did the partition).

# ── [5] CODEX COMPLIANCE ──────────────────────────────────────────────────────
# All checks are blocking unless excluded via QUALITY_GATE_BYPASS_AUDIT.md.
# Add inline --glob exclusions below only for bypasses documented in that file.
log_section "[5/6] CODEX COMPLIANCE"
qg_prof start codex
V=0

# PRINT_EXCLUDE_GLOBS: per-repo array of --glob exclusions (e.g. Rich console.print, bash template strings)
# Excluded: console.print (Rich library), python3 -c "...print..." (bash heredoc templates), pprint;
#           CLI entry-points (**/cli/main.py, **/cli/_shim.py, **/__main__.py) — argparse --version/--help/dispatcher
#           output to stdout is correct CLI behaviour, not an event (per Harsh slot-2 Q1.1, 2026-05-11; CLI handlers
#           under cli/handlers/ are NOT excluded — they must still use log_event()).
_print_hits=$(rg "print\(" --type py --glob "!tests/**" --glob "!scripts/**" --glob "!**/cli/main.py" --glob "!**/cli/_shim.py" --glob "!**/__main__.py" "${PRINT_EXCLUDE_GLOBS[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v 'console\.print\|pprint\|python3 -c\|".*print.*"\|# noqa: qg-print' || :)
[[ -n "$_print_hits" ]] && { echo "$_print_hits"; log_fail "print() — use log_event() from UEI"; V=$(( V + 1 )); } || log_success "No print()"

# OS_ENV_EXCLUDE_GLOBS: per-repo array of --glob exclusions (e.g. bootstrap_config.py, env_substitutor.py)
# Lines annotated with "# config-bootstrap:" are the documented approved exception for pre-UCC init (LOG_LEVEL, PORT).
# __main__.py is excluded because Cloud Run bootstrap reads PORT before UCC is available.
# Exclude: config-bootstrap: annotated lines, comments (lines starting with #), docstrings
_os_env_hits=$(rg "os\.getenv|os\.environ" --type py --glob "!tests/**" --glob "!scripts/**" --glob "!**/config.py" --glob "!**/__main__.py" "${OS_ENV_EXCLUDE_GLOBS[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v 'config-bootstrap:' | grep -v '^\s*#' | grep -v '# noqa: qg-os-env' || :)
if [[ -n "$_os_env_hits" ]]; then
    echo "$_os_env_hits"
    log_fail "os.getenv()/os.environ — use UnifiedCloudConfig for config, get_secret_client() for secrets"
    V=$(( V + 1 ))
else
    log_success "No os.getenv()/os.environ"
fi

rg 'os\.getenv\s*\([^)]+,\s*""\s*\)' --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "os.getenv empty fallback — fail fast"; V=$(( V + 1 )); } || log_success "No os.getenv empty fallback"


# Env canon: when os.getenv is used, keys must be from unified_internal_contracts.EnvVars
if [[ -n "${WORKSPACE_ROOT:-}" && -f "${WORKSPACE_ROOT}/unified-trading-pm/scripts/validation/check_env_canon.py" ]]; then
    python3 "${WORKSPACE_ROOT}/unified-trading-pm/scripts/validation/check_env_canon.py" "$(pwd)" 2>/dev/null \
        && log_success "Env canon: keys from EnvVars" \
        || { log_fail "Env canon: os.getenv keys must be from unified_internal_contracts.EnvVars"; V=$(( V + 1 )); }
fi
# Manifest import alignment: dependencies[] must match actual Python imports
# MANIFEST_ALIGNMENT_SKIP: set true in test-harness repos where SOURCE_DIR=tests (alignment scanner excludes tests/)
if [[ "${MANIFEST_ALIGNMENT_SKIP:-false}" == "true" ]]; then
    log_success "Manifest import alignment: skipped (MANIFEST_ALIGNMENT_SKIP=true)"
elif [[ -n "${WORKSPACE_ROOT:-}" && -f "${WORKSPACE_ROOT}/unified-trading-pm/scripts/validation/check_manifest_import_alignment.py" ]]; then
    python3 "${WORKSPACE_ROOT}/unified-trading-pm/scripts/validation/check_manifest_import_alignment.py" --repo "$(pwd)" --workspace-root "${WORKSPACE_ROOT}" \
        && log_success "Manifest import alignment: OK" \
        || { log_fail "Manifest import alignment: declare deps you import, import deps you declare"; V=$(( V + 1 )); }
else
    # LOUD skip (parity, 2026-06-10): CI runs without a workspace → this check silently never ran
    # there, masking local-vs-CI divergence (ci_local_qg_parity P2). Warn so the gap is visible.
    log_warn "Manifest import alignment: SKIPPED — no WORKSPACE_ROOT/PM checkout (CI without workspace); local runs DO check this"
fi

rg "datetime\.now\(\)|datetime\.utcnow\(\)" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Naive datetime — use datetime.now(timezone.utc)"; V=$(( V + 1 )); } || log_success "No naive datetime"

rg "except:" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Bare except — use specific exception"; V=$(( V + 1 )); } || log_success "No bare except"


# Bypass: add --glob exclusions for files in QUALITY_GATE_BYPASS_AUDIT.md §1.1
for f in $(rg "import requests" --type py --glob "!tests/**" --glob "!scripts/**" "$SOURCE_DIR/" -l 2>/dev/null || :); do
    # Skip if the import line has a noqa comment for this check
    rg "import requests.*# noqa:.*qg-requests-in-async" "$f" >/dev/null 2>&1 && continue
    grep -q "async def" "$f" && { log_fail "requests in async: $f — use aiohttp"; V=$(( V + 1 )); break; }
done; [[ ${V} -eq $(( V )) ]] && log_success "No requests in async" 2>/dev/null || :

# ASYNCIO_RUN_EXCLUDE_GLOBS: optional array set in quality-gates.sh to exclude
# known-false-positive files (asyncio.run() as entry-point in file that also has loops).
# Document each exclusion in QUALITY_GATE_BYPASS_AUDIT.md §1.1.
# Example: ASYNCIO_RUN_EXCLUDE_GLOBS=("!**/cli/batch_fetch.py")
ASYNCIO_EXTRA_GLOBS=()
for g in ${ASYNCIO_RUN_EXCLUDE_GLOBS[@]+"${ASYNCIO_RUN_EXCLUDE_GLOBS[@]}"}; do
    ASYNCIO_EXTRA_GLOBS+=(--glob "$g")
done
_asyncio_violation=""
for f in $(rg "asyncio\.run\(" --type py --glob "!tests/**" --glob "!scripts/**" ${ASYNCIO_EXTRA_GLOBS[@]+"${ASYNCIO_EXTRA_GLOBS[@]}"} "$SOURCE_DIR/" -l 2>/dev/null || :); do
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
# IMPORT_INSIDE_EXCLUDE_GLOBS: per-repo array of glob patterns (e.g. "!**/smoke-test-dev.py").
_AST_CHECKER="$(cd "$(dirname "${BASH_SOURCE[0]}")/../quality_gates" && pwd)/check_imports_inside_functions.py"
IMPORT_INSIDE_EXTRA_ARGS=()
for g in ${IMPORT_INSIDE_EXCLUDE_GLOBS[@]+"${IMPORT_INSIDE_EXCLUDE_GLOBS[@]}"}; do
    IMPORT_INSIDE_EXTRA_ARGS+=(--exclude-glob "$g")
done
if python3 "$_AST_CHECKER" --source-dir "$SOURCE_DIR" "${IMPORT_INSIDE_EXTRA_ARGS[@]}" 2>/tmp/_inside_imports_qg.err; then
    log_success "No imports inside functions"
else
    log_fail "Imports inside functions — move to top (AST-detected)"
    head -10 /tmp/_inside_imports_qg.err 2>/dev/null
    V=$(( V + 1 ))
fi

ANY=$(rg ": Any|-> Any|\[Any\]" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null | grep -v "type: ignore" || :)
[[ -n "$ANY" ]] && { log_fail "Any types (including dict[str, Any]) — use Pydantic models or specific types"; echo "$ANY" | head -3; V=$(( V + 1 )); } || log_success "No Any types"

# Untyped API responses — response.json() must go through model_validate(), not raw dict access.
# Honour `# noqa: qg-raw-json` per-line opt-out (matches base-library.sh) for explicit
# protocol-layer / dynamic-schema cases where Pydantic validation is intentionally deferred.
RAW_JSON=$(rg 'response\.json\(\)|await response\.json\(\)' --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v 'model_validate\|cast(dict' \
    | grep -v "# noqa:.*qg-raw-json\|# noqa: qg-raw-json" || :)
[[ -n "$RAW_JSON" ]] && { log_fail "Raw response.json() — parse through Pydantic model_validate()"; echo "$RAW_JSON" | head -3; V=$(( V + 1 )); } || log_success "No raw response.json()"

EMPTY_STR_EXTRA=()
for g in ${EMPTY_STR_EXCLUDE_GLOBS[@]+"${EMPTY_STR_EXCLUDE_GLOBS[@]}"}; do EMPTY_STR_EXTRA+=(--glob "$g"); done
EMPTY_STR=$(rg '\.get\(["\x27][\w_]+["\x27]\s*,\s*["\x27]["\x27]\)' --type py --glob "!tests/**" "${EMPTY_STR_EXTRA[@]}" "$SOURCE_DIR/" 2>/dev/null | grep -v '# noqa: qg-empty-fallback' || :)
[[ -n "$EMPTY_STR" ]] && { log_fail "Empty string fallback — fail fast"; V=$(( V + 1 )); } || log_success "No empty string fallbacks"

ED_EL_EXTRA=()
for g in ${EMPTY_DICT_LIST_EXCLUDE_GLOBS[@]+"${EMPTY_DICT_LIST_EXCLUDE_GLOBS[@]}"}; do ED_EL_EXTRA+=(--glob "$g"); done
ED=$(rg '\.get\s*\(\s*["\x27][^"\x27]+["\x27]\s*,\s*\{\}\s*\)' --type py --glob "!tests/**" "${ED_EL_EXTRA[@]}" "$SOURCE_DIR/" 2>/dev/null | grep -v '# noqa: qg-empty-fallback' || :)
EL=$(rg '\.get\s*\(\s*["\x27][^"\x27]+["\x27]\s*,\s*\[\]\s*\)' --type py --glob "!tests/**" "${ED_EL_EXTRA[@]}" "$SOURCE_DIR/" 2>/dev/null | grep -v '# noqa: qg-empty-fallback' || :)
[[ -n "$ED$EL" ]] && { log_fail "Empty dict/list fallback — fail fast"; V=$(( V + 1 )); } || log_success "No empty dict/list fallbacks"

rg "central-element-[0-9]+" tests/ 2>/dev/null \
    && { log_fail "Hardcoded prod project ID in tests — use 'test-project'"; V=$(( V + 1 )); } || log_success "No hardcoded project ID in tests"

HP_EXTRA=()
for g in ${HARDCODED_PROJECT_EXCLUDE_GLOBS[@]+"${HARDCODED_PROJECT_EXCLUDE_GLOBS[@]}"}; do HP_EXTRA+=(--glob "$g"); done
rg "central-element-[0-9]+" --type py --glob "!tests/**" "${HP_EXTRA[@]}" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Hardcoded project ID in production — use config.gcp_project_id"; V=$(( V + 1 )); } || log_success "No hardcoded project ID in production"

# GCP_PROJECT_ID is legacy — only GCP_PROJECT_ID is canonical
# GCP_PROJECT_ID_EXCLUDE_GLOBS: per-repo array of glob patterns (e.g. "!**/rollout-*.py")
GCP_EXTRA=()
for g in ${GCP_PROJECT_ID_EXCLUDE_GLOBS[@]+"${GCP_PROJECT_ID_EXCLUDE_GLOBS[@]}"}; do GCP_EXTRA+=(--glob "$g"); done
# Exclude: docstrings (triple-quoted), comments, and noqa-annotated lines
_gcp_id_hits=$(rg "GCP_PROJECT_ID" --type py --glob "!tests/**" --glob "!**/config.py" "${GCP_EXTRA[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v '^\s*#\|^\s*"""\|# noqa: qg-gcp-project-id\|"""$' || :)
[[ -n "$_gcp_id_hits" ]] && { echo "$_gcp_id_hits"; log_fail "Use GCP_PROJECT_ID not GCP_PROJECT_ID (except config.py backward compat)"; V=$(( V + 1 )); } || log_success "No GCP_PROJECT_ID usage"

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

# Schema provenance: local BaseModel/TypedDict/dataclass should import from UAC or UIC
# SCHEMA_PROVENANCE_SKIP: set true for devops/PM repos where local BaseModel in checker scripts is expected
REPO_ROOT_SVC="${REPO_ROOT:-$(dirname "$PROJECT_ROOT")}"
if [[ "${SCHEMA_PROVENANCE_SKIP:-false}" == "true" ]]; then
    log_success "Schema provenance: skipped (SCHEMA_PROVENANCE_SKIP=true)"
elif [[ -f "$REPO_ROOT_SVC/unified-trading-pm/scripts/validation/check_schema_provenance.py" ]]; then
    if python3 "$REPO_ROOT_SVC/unified-trading-pm/scripts/validation/check_schema_provenance.py" --repo "$SERVICE_NAME" --workspace-root "$REPO_ROOT_SVC" 2>/dev/null; then
        log_success "Schema provenance OK (schemas from UAC/UIC)"
    else
        log_fail "Schema provenance: local BaseModel/TypedDict/dataclass found (should import from UAC or UIC)"
        python3 "$REPO_ROOT_SVC/unified-trading-pm/scripts/validation/check_schema_provenance.py" --repo "$SERVICE_NAME" --workspace-root "$REPO_ROOT_SVC" 2>/dev/null | head -5 || true
        V=$(( V + 1 ))
    fi
fi

# setup_events/setup_service uses sink= in production
# Skip if this repo defines setup_events (e.g. unified-trading-library)
if rg 'def setup_events|def setup_service' --type py "$SOURCE_DIR/" -q 2>/dev/null; then
    log_success "setup_service() check skipped (repo defines setup_events/setup_service)"
else
    SETUP_EXTRA=()
    for g in ${SETUP_NO_SINK_EXCLUDE_GLOBS[@]+"${SETUP_NO_SINK_EXCLUDE_GLOBS[@]}"}; do SETUP_EXTRA+=(--glob "$g"); done
    SETUP_NO_SINK=$(rg 'setup_(events|service)\s*\(' --type py \
        --glob "!tests/**" "$SOURCE_DIR/" "${SETUP_EXTRA[@]}" 2>/dev/null | grep -v 'sink=' \
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

DI_EXTRA=()
for g in ${DEEP_IMPORT_EXCLUDE_GLOBS[@]+"${DEEP_IMPORT_EXCLUDE_GLOBS[@]}"}; do DI_EXTRA+=(--glob "$g"); done
# Allow `unified_api_contracts.internal` — sanctioned facade per CLAUDE.md "Citadel Import Rules":
# "schemas → unified-api-contracts (external + internal via `unified_api_contracts.internal`)".
# `.internal` is a facade, not a `canonical.*`/`normalize_utils.*` deep path.
# Q1.3 fix per features_service_qg_cleanup_2026_05_11.md (operator decision (a) shipped 2026-05-11).
# Also allow the sanctioned ONE-LEVEL `.{domain}` facade form per CLAUDE.md "Citadel Import Rules": services use
# `from unified_api_contracts import X` OR `from unified_api_contracts.{domain} import X` (sports/market/execution/
# alerting/registry/...). Only the deep-INTERNAL namespaces stay flagged — `canonical`/`normalize_utils`/`config`/
# `shared`/`schemas`/`external` (these are UAC-internal / deleted dirs — always accessed deeper, so they keep the
# trailing dot and the negative lookahead does not whitelist them). NB `registry` IS a sanctioned one-level facade
# (`registry/__init__.py` re-exports `CHAIN_RPC_TEMPLATES`/`resolve_rpc_url`/capability declarations; execution-service
# imports `from unified_api_contracts.registry import CHAIN_RPC_TEMPLATES`) — so `from unified_api_contracts.registry
# import X` passes, while two-level `from unified_api_contracts.registry.chain_env import X` stays flagged (the
# `[a-z_]+ import` clause only matches a single segment before ` import`). STEP 5.23 (uac-import-surface-enforcement)
# is the precise enforcement for the internal namespaces. Q4 + Q4b fix per features_service_qg_cleanup_2026_05_11.md.
# PORTABILITY (ci_local_qg_parity 2026-06-10): the negative-lookahead filter MUST run under
# ripgrep's bundled PCRE2 (`rg --pcre2`), NOT `grep -P`. macOS `/usr/bin/grep` (BSD) does NOT
# support `-P` → `grep -vP` exits 2 + emits nothing → with `|| :` the whole DI collapses to ""
# → this check FALSE-PASSES on every macOS slot ("No deep imports") while CI (Linux GNU grep)
# correctly flags. That single +1 divergence is what made deployment-api local-green / CI-red
# (V=23 vs 24). `rg --pcre2` is byte-identical local↔CI. NEVER reintroduce `grep -P` in the gate.
DI=$(rg 'from unified_[a-z_]+\.[a-zA-Z0-9_.]+\s+import' --type py --glob "!tests/**" --glob "!**/__init__.py" \
    "${DI_EXTRA[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa" \
    | grep -v 'from unified_api_contracts\.internal' \
    | rg --pcre2 -v 'from unified_api_contracts\.(?!canonical|normalize_utils|config|shared|schemas|external)[a-z_]+ import' || :)
[[ -n "$DI" ]] && { log_fail "Deep unified lib imports — use top-level"; echo "$DI" | head -3; V=$(( V + 1 )); } || log_success "No deep imports"

# Old event logging pattern — flag obsolete cloud logging helpers only.
# log_event/setup_events: from unified_trading_library import log_event is correct (UEI merged into UTL;
#   check-import-patterns.py enforces top-level top-level import; from unified_trading_library.events also accepted).
# setup_cloud_logging/observability: old non-standard helpers — flag these.
EL_OLD=$(rg "from unified_trading_library[. ].*(setup_cloud_logging|observability)" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$EL_OLD" ]] && { log_fail "Old event logging import — use 'from unified_trading_library import log_event'"; echo "$EL_OLD" | head -3; V=$(( V + 1 )); } || log_success "Event logging imports OK"

# ============================================================
# STEP 5.5 — No direct cloud SDK imports (must route through UCLI/UCS)
# ============================================================
_csdk_extra=()
for g in ${CLOUD_SDK_EXCLUDE_GLOBS[@]+"${CLOUD_SDK_EXCLUDE_GLOBS[@]}"}; do _csdk_extra+=(--glob "$g"); done
DIRECT_CLOUD=$(rg 'from google\.cloud import|^import boto3\b|^from boto3 import|^from botocore import' \
    --type py "${_csdk_extra[@]}" "${SOURCE_DIR}/" 2>/dev/null | grep -v __pycache__ | grep -v '\.venv' | grep -v '# noqa: cloud-sdk-direct' || :)
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

BE_EXTRA_GLOBS=()
for g in ${BE_EXCLUDE_GLOBS[@]+"${BE_EXCLUDE_GLOBS[@]}"}; do
    BE_EXTRA_GLOBS+=(--glob "!$g")
done
BE=$(rg "except Exception:" --type py --glob "!tests/**" ${BE_EXTRA_GLOBS[@]+"${BE_EXTRA_GLOBS[@]}"} "$SOURCE_DIR/" 2>/dev/null || :)
# Bypass: add --glob exclusions for files in QUALITY_GATE_BYPASS_AUDIT.md §1.1
[[ -n "$BE" ]] && { log_warn "broad except Exception — document in QUALITY_GATE_BYPASS_AUDIT.md"; echo "$BE" | head -5; V=$(( V + 1 )); } || log_success "No broad except Exception"

# Swallowed errors — except that silently passes/returns None
SWALLOWED=$(rg "except Exception:" --type py --glob "!tests/**" "$SOURCE_DIR/" -A 2 2>/dev/null \
    | grep -E "^[[:space:]]+(pass|return None)$" || :)
[[ -n "$SWALLOWED" ]] && { log_fail "Swallowed errors — use @handle_api_errors or re-raise"; V=$(( V + 1 )); } || log_success "No swallowed errors"

# File size — tests excluded (test files are often long due to fixtures/assertions)
# FUNCTION_SIZE_EXTRA_EXCLUDES also applies here for consistency (same variable, same dirs to skip)
qg_prof start size-checks
SVIOL=""
for f in $(find . -name "*.py" ! -path "./.venv/*" ! -path "./scripts/*" ! -path "./.git/*" ! -path "./build/*" ! -path "./.venv-workspace/*" ! -path "*/site-packages/*" ! -path "./tests/*" "${FUNCTION_SIZE_EXTRA_EXCLUDES[@]}" 2>/dev/null); do
    lines=$(wc -l < "$f" 2>/dev/null || echo 0)
    [[ "$lines" -gt $MAX_FILE_LINES ]] && SVIOL="${SVIOL}\n  $f: $lines L"
done
[[ -n "$SVIOL" ]] && { log_fail "Files exceed $MAX_FILE_LINES lines:$SVIOL"; V=$(( V + 1 )); } || log_success "File size OK"

# Function/class/method size — tests excluded (test functions are often long)
# FUNCTION_SIZE_EXTRA_EXCLUDES: optional array of extra ! -path args set in quality-gates.sh
# e.g. FUNCTION_SIZE_EXTRA_EXCLUDES=("! -path ./features_service/*" "! -path ./examples/*")
FSIZES=""
for f in $(find . -name "*.py" ! -path "./.venv/*" ! -path "./scripts/*" ! -path "./.git/*" ! -path "./build/*" ! -path "./.venv-workspace/*" ! -path "*/site-packages/*" ! -path "./tests/*" "${FUNCTION_SIZE_EXTRA_EXCLUDES[@]}" 2>/dev/null); do
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
qg_prof end size-checks

# Security: pip-audit (BLOCKING — OSV vulnerability database check)
# Use venv pip-audit to skip internal/editable packages that are not on PyPI.
qg_prof start pip-audit
_PIPAUDIT="${PYTHON_CMD%python*}pip-audit"
if [ ! -x "$_PIPAUDIT" ]; then _PIPAUDIT="pip-audit"; fi
if command -v "$_PIPAUDIT" &>/dev/null; then
    # CVE-2026-4539: no-fix-version (workspace-global, reviewed 2026-05-20)
    # CVE-2026-45409: idna 3.11 — follow-up to CVE-2024-3651; no patched release as of 2026-05-22
    # CVE-2026-3219: pip 26.0.1 concatenated tar+ZIP handling; fix: upgrade pip >= 26.1
    # CVE-2026-6357: pip < 26.1 self-update check; fix: upgrade pip >= 26.1
    # CVE-2026-34993: aiohttp <=3.13.5 CookieJar.load() RCE on UNTRUSTED cookie input. fix_versions=[3.14.0],
    #   BUT aiohttp 3.14.0 removed aiohttp.streams.AsyncStreamReaderMixin → breaks vcrpy 8.1.1 (latest release)
    #   fleet-wide (vcr/stubs/aiohttp_stubs.py MockStream) → 64 VCR cassette tests AttributeError. These services
    #   use aiohttp as an HTTP CLIENT and never call CookieJar.load() on untrusted files → exploit surface nil.
    #   SUCCESSOR (remove this ignore): bump aiohttp>=3.14 + vcrpy once vcrpy ships an aiohttp-3.14-compatible release
    #   (or an aiohttp 3.13.x backport fix lands). Tracked: plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md.
    #   Non-vcrpy repos (features-service, deployment-api) already run aiohttp 3.14.0 (CVEs actually patched there).
    # CVE-2026-47265: aiohttp <=3.13.5 — cookies set via the `cookies=` param are re-sent after a cross-origin
    #   redirect. fix_versions=[3.14.0] (same vcrpy block as CVE-2026-34993). aiohttp 3.13.5 keeps accumulating
    #   cookie CVEs fixed only in 3.14.0; this ignore set grows until the vcrpy-unblock lets the fleet reach 3.14.0.
    # PYSEC-2026-196: pip 26.1.1 — console_scripts/gui_scripts treated as paths without sanitizing the resolved
    #   absolute path. The fleet stays on the vulnerable pip line because the next pip release is incompatible with
    #   the pinned vcrpy (operator-accepted 2026-06-05). Exploit surface nil — the fleet never pip-installs untrusted
    #   packages at runtime. SUCCESSOR (remove this ignore): the same vcrpy-unblock that lets aiohttp reach 3.14.0.
    _pa_extra="${PIP_AUDIT_EXTRA_ARGS:-} --ignore-vuln CVE-2026-4539 --ignore-vuln CVE-2026-45409 --ignore-vuln CVE-2026-3219 --ignore-vuln CVE-2026-6357 --ignore-vuln CVE-2026-34993 --ignore-vuln CVE-2026-47265 --ignore-vuln PYSEC-2026-196"
    # DEPS-CHANGE/CRON TRIGGER (plan quality_gates_speed_and_config_ssot_2026_06_09 Phase 3):
    # the OSV query is a fixed ~30-40s network tax whose verdict only changes when the
    # dependency inputs change OR new advisories publish. Key = pyproject.toml + uv.lock
    # contents + the ignore set + pip-audit version, cached at .qg_cache/pip_audit_deps_hash.
    # Unchanged key AND younger than QG_PIP_AUDIT_MAX_AGE_HOURS (default 24h — the
    # cron-equivalent freshness bound for newly-published advisories) → skip the query.
    # ONLY a clean (rc=0) audit is cached; vulnerabilities/timeouts always re-run. The
    # internal-advisories check below stays OUTSIDE the cache (its input is a PM yaml,
    # not this repo's deps). Bypass: QG_NO_CACHE=1 forces the full OSV query.
    _pa_key=$({ cat pyproject.toml uv.lock 2>/dev/null || :; echo "$_pa_extra"; "$_PIPAUDIT" --version 2>/dev/null || :; } | _qg_hash)
    if qg_cache_hit pip_audit_deps_hash "$_pa_key" "${QG_PIP_AUDIT_MAX_AGE_HOURS:-24}"; then
        log_success "pip-audit: cached (deps unchanged, age $(_qg_cache_age_hours pip_audit_deps_hash || echo '?')h)"
    else
        # run_timeout 180: OSV API can stall indefinitely in Cloud Build (no connection-level timeout
        # in pip-audit itself). Exit 124 = timeout → warn-only; image still passes (advisory gate).
        _pa_rc=0
        run_timeout 180 "$_PIPAUDIT" --format json --skip-editable $_pa_extra -o /tmp/pip-audit-output.json 2>/dev/null || _pa_rc=$?
        if [[ $_pa_rc -eq 0 ]]; then
            log_success "pip-audit clean"
            qg_cache_store pip_audit_deps_hash "$_pa_key"
        elif [[ $_pa_rc -eq 124 ]]; then
            log_warn "pip-audit: OSV query timed out after 180s (Cloud Build network) — skipping vulnerability gate (advisory)"
        else
            log_fail "pip-audit vulnerabilities found"
            python3 -c "
import json, sys
try:
    data = json.load(open('/tmp/pip-audit-output.json'))
    deps = [d for d in data.get('dependencies', []) if d.get('vulns')]
    for d in deps:
        for v in d['vulns']:
            print(f'  {d[\"name\"]} {d[\"version\"]}: {v[\"id\"]} — {v.get(\"description\",\"\")[:120]}')
except Exception as e:
    print(f'  (could not parse pip-audit output: {e})')
" 2>/dev/null || :
            V=$(( V + 1 ))
        fi
        # Store SBOM audit trail in GCS (non-blocking — upload failure does not fail the build).
        # Inside the cache-miss branch: on a cache hit /tmp holds another repo's stale output.
        SERVICE_NAME="$SERVICE_NAME" python3 "$REPO_ROOT/unified-trading-pm/scripts/sbom-store.py" \
            /tmp/pip-audit-output.json 2>/dev/null || :
    fi
    # Internal advisory check (BLOCKING — checks unified-trading-pm/security/internal-advisories.yaml)
    if [[ -f "$REPO_ROOT/unified-trading-pm/scripts/validation/check-internal-advisories.sh" ]]; then
        bash "$REPO_ROOT/unified-trading-pm/scripts/validation/check-internal-advisories.sh" \
            && log_success "internal advisory check clean" \
            || { log_fail "internal advisory violation — see unified-trading-pm/security/internal-advisories.yaml"; V=$(( V + 1 )); }
    else
        log_warn "check-internal-advisories.sh not found at ${REPO_ROOT}/unified-trading-pm/scripts/validation/ — skipping internal advisory check"
    fi
else
    log_fail "pip-audit required: uv pip install pip-audit"; V=$(( V + 1 ))
fi
qg_prof end pip-audit

# Security: bandit
# BANDIT_EXTRA_ARGS: optional per-repo override (e.g. BANDIT_EXTRA_ARGS="-c pyproject.toml")
# CONTENT-HASH CACHE (plan quality_gates_speed_and_config_ssot_2026_06_09 Phase 3):
# bandit's verdict is a pure function of scanned source content + tool version + config.
# Key = _qg_src_content_key over SOURCE_DIR + pyproject.toml (covers [tool.bandit] when
# `-c pyproject.toml` is passed) + `bandit --version` + BANDIT_EXTRA_ARGS, cached at
# .qg_cache/bandit_content_hash. ONLY a clean run is cached — issues always re-print.
# Bypass: QG_NO_CACHE=1 forces a full scan.
qg_prof start bandit
if command -v bandit &>/dev/null; then
    _bandit_key=$({ _qg_src_content_key "$SOURCE_DIR" pyproject.toml; bandit --version 2>/dev/null || :; echo "${BANDIT_EXTRA_ARGS:-}"; } | _qg_hash)
    if qg_cache_hit bandit_content_hash "$_bandit_key"; then
        log_success "bandit: cached (source content unchanged)"
    else
        _bandit_out=$(run_timeout 30 bandit -r "$SOURCE_DIR/" -ll ${BANDIT_EXTRA_ARGS:-} 2>&1) \
            && qg_cache_store bandit_content_hash "$_bandit_key" \
            || { echo "$_bandit_out"; log_fail "bandit issues"; V=$(( V + 1 )); }
    fi
else
    log_fail "bandit required: uv pip install bandit"; V=$(( V + 1 ))
fi
qg_prof end bandit


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
_csdk_step_extra=()
for g in ${CLOUD_SDK_EXCLUDE_GLOBS[@]+"${CLOUD_SDK_EXCLUDE_GLOBS[@]}"}; do _csdk_step_extra+=(--glob "$g"); done
CLOUD_SDK_VIOLATIONS=$(rg "^from google\.cloud|^import boto3|^import botocore" \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!tests' \
    --glob '!scripts' \
    --glob '!unified_cloud_interface/providers/**' \
    "${_csdk_step_extra[@]}" \
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
# HARDCODED_PROTO_EXCLUDE_GLOBS: per-repo array of --glob exclusions.
# Use when a file legitimately calls UCI/UTL APIs that use gcs_bucket as a field name
# (e.g. ManifestWriter.write(gcs_bucket=...) — NOT a raw GCS SDK call).
# Document exceptions in QUALITY_GATE_BYPASS_AUDIT.md.
# Example (per-repo quality-gates.sh):
#   HARDCODED_PROTO_EXCLUDE_GLOBS=("--glob=!**/adapters/catalogue_adapter.py")
PROTOCOL_VIOLATIONS=$(rg "CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!tests' --glob '!scripts/**' \
    "${HARDCODED_PROTO_EXCLUDE_GLOBS[@]}" \
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
    # Skip deploy advisory if cloudbuild declares deploy-via-dispatch (e.g. central deployment-service)
    if ! grep -qE '# deploy-via-dispatch|# deploys-via-dispatch' cloudbuild.yaml 2>/dev/null; then
        rg "id:\s*[\"']?(deploy|notify-deployment)|gcloud run deploy" cloudbuild.yaml 2>/dev/null \
            | grep -qE 'deploy|notify-deployment' || {
            log_warn "STEP 5.17: cloudbuild.yaml has no deploy/notify-deployment step (advisory — some services deploy via dispatch)"; }
    fi
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

# ============================================================
# STEP 5.19 — cloudbuild.yaml unescaped-substitution validation
# Cloud Build substitution-scans EVERY step string (args/script/env), bash
# comments included; an unescaped $WORD that is neither a builtin nor a
# _-prefixed user substitution makes GCB SILENTLY reject the whole config
# (no build record, no GitHub check, no Slack). Shell vars / command
# substitutions inside cloudbuild bash blocks need $$ ($$VAR, $$(cmd)).
# Issue: plans/active/issues/cloudbuild_silent_failures_no_alerting_no_validation_2026_06_10.md (Gap 3)
# ============================================================
if [ -f "cloudbuild.yaml" ]; then
    _CB_SUBST_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_cloudbuild_substitutions.py"
    if [ -f "$_CB_SUBST_CHECKER" ]; then
        if run_timeout 30 "$PYTHON_CMD" "$_CB_SUBST_CHECKER" cloudbuild.yaml >/tmp/cloudbuild_subst_qg.log 2>&1; then
            log_success "STEP 5.19: cloudbuild.yaml substitutions OK (no unescaped \$VAR / \$( — \$\$-escape honored)"
        else
            log_fail "STEP 5.19: cloudbuild.yaml has unescaped substitution(s) — Cloud Build will SILENTLY reject this config (file:step-id:varname):"
            cat /tmp/cloudbuild_subst_qg.log
            log_fail "         Remedy: shell vars in cloudbuild bash blocks need \$\$; even COMMENT lines are scanned by the validator"
            V=$(( V + 1 ))
        fi
    else
        log_success "STEP 5.19: skipped (cloudbuild substitution checker not provisioned in this PM checkout)"
    fi
else
    log_success "STEP 5.19: no cloudbuild.yaml (skipped)"
fi

# ============================================================
if [ -d ".github/workflows" ]; then
    WT_VALIDATOR="${REPO_ROOT}/unified-trading-pm/scripts/validation/check-workflow-tokens.py"
    if [ -f "$WT_VALIDATOR" ]; then
        if run_timeout 15 "$PYTHON_CMD" "$WT_VALIDATOR" --dir .github/workflows 2>/dev/null; then
            log_success "STEP 5.18: No cross-repo GITHUB_TOKEN violations"
        else
            log_fail "STEP 5.18: Cross-repo checkout/artifact uses GITHUB_TOKEN — must use GH_PAT"
            V=$(( V + 1 ))
        fi
    fi
else
    log_success "STEP 5.18: no .github/workflows dir (skipped)"
fi

# ============================================================
# STEP 5.23 — UAC import surface enforcement
# Only facade imports allowed: from unified_api_contracts.{domain} import X
# Deep imports into canonical/, normalize_utils/, config/, shared/, schemas/ are blocked.
# Exempt repos: UAC itself, UIC, SIT (auto-detected by SERVICE_NAME or UAC_CANONICAL_EXEMPT=true).
# ============================================================
_UAC_EXEMPT="${UAC_CANONICAL_EXEMPT:-false}"
[[ "${SERVICE_NAME:-}" == "system-integration-tests" ]] && _UAC_EXEMPT=true
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

# ============================================================
# STEP 5.30 — No hardcoded market categories (Pattern A)
# Services must import MarketCategory from UIC or derive from UAC VENUE_CATEGORY_MAP.
# Catches: CATEGORIES = ["CEFI", "TRADFI", "DEFI"] and similar hardcoded lists.
# ============================================================
HARDCODED_CATEGORIES=$(rg '\[.*"CEFI".*"TRADFI".*\]|\[.*"TRADFI".*"CEFI".*\]|categories\s*=\s*\[.*"CEFI"|CATEGORIES\s*=\s*\[' \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!**/tests/**' --glob '!**/scripts/**' \
    "$SOURCE_DIR/" 2>/dev/null \
    | grep -v '# CORRECT-LOCAL' \
    | grep -v 'MarketCategory' \
    | grep -v 'VENUE_CATEGORY_MAP' \
    | grep -v 'default=' \
    | grep -v 'Field(' \
    || :)
if [ -n "$HARDCODED_CATEGORIES" ]; then
    log_fail "STEP 5.30: Hardcoded market categories found — import MarketCategory from unified_internal_contracts:"
    echo "$HARDCODED_CATEGORIES" | head -5
    V=$(( V + 1 ))
else
    log_success "STEP 5.30: No hardcoded market categories"
fi

# ============================================================
# STEP 5.31 — No hardcoded bucket name f-string templates (Pattern B)
# Bucket names must come from config fields, not inline f-strings.
# Catches: f"features-*-{category}-{project}" and similar patterns.
# ============================================================
HARDCODED_BUCKETS=$(rg 'f"(features-|instruments-|ml-)[a-z-]+-\{' \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!**/tests/**' --glob '!**/scripts/**' \
    "$SOURCE_DIR/" 2>/dev/null \
    | grep -v '# CORRECT-LOCAL' \
    | grep -v '_template' \
    | grep -v 'Field(' \
    | grep -v 'default=' \
    || :)
if [ -n "$HARDCODED_BUCKETS" ]; then
    log_fail "STEP 5.31: Hardcoded bucket name templates found — move to config fields:"
    echo "$HARDCODED_BUCKETS" | head -5
    V=$(( V + 1 ))
else
    log_success "STEP 5.31: No hardcoded bucket name templates"
fi

# ============================================================
# STEP 5.32 — No duplicate enum definitions that exist in UAC/UIC (Pattern H)
# Services must not redefine enums that exist in shared contracts.
# Known enums: BetSide, MarketCategory, Timeframe, RuntimeMode, CloudProvider.
# ============================================================
DUPLICATE_ENUMS=$(rg 'class\s+(BetSide|MarketCategory|Timeframe|RuntimeMode|CloudProvider|DataMode|PhaseMode)\s*\(' \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!**/tests/**' \
    "$SOURCE_DIR/" 2>/dev/null \
    | grep -v '# CORRECT-LOCAL' \
    || :)
if [ -n "$DUPLICATE_ENUMS" ]; then
    log_fail "STEP 5.32: Duplicate enum definitions (already in UAC/UIC) — import instead of redefining:"
    echo "$DUPLICATE_ENUMS" | head -5
    V=$(( V + 1 ))
else
    log_success "STEP 5.32: No duplicate shared enum definitions"
fi

# ============================================================
# STEP 5.33 — No hardcoded TIMEFRAME_TO_SECONDS mappings (Pattern E)
# Must import from unified_internal_contracts, not define locally.
# ============================================================
LOCAL_TIMEFRAME_MAP=$(rg 'TIMEFRAME.*(TO_SECONDS|SECONDS)\s*[:=]\s*\{' \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!**/tests/**' --glob '!**/scripts/**' \
    "$SOURCE_DIR/" 2>/dev/null \
    | grep -v '# CORRECT-LOCAL' \
    | grep -v 'from unified' \
    || :)
if [ -n "$LOCAL_TIMEFRAME_MAP" ]; then
    log_fail "STEP 5.33: Local TIMEFRAME_TO_SECONDS mapping found — import from unified_internal_contracts:"
    echo "$LOCAL_TIMEFRAME_MAP" | head -5
    V=$(( V + 1 ))
else
    log_success "STEP 5.33: No local TIMEFRAME_TO_SECONDS definitions"
fi

# ============================================================
# STEP 5.34 — No brittle getattr for config fields (Pattern F)
# Config access must use typed attributes, not getattr with fallback defaults.
# All services remediated 2026-03-24 — this is now an ERROR.
# ============================================================
BRITTLE_GETATTR=$(rg 'getattr\s*\(\s*service_config\s*,' \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!**/tests/**' \
    "$SOURCE_DIR/" 2>/dev/null \
    | grep -v '# CORRECT-LOCAL' \
    || :)
if [ -n "$BRITTLE_GETATTR" ]; then
    log_fail "STEP 5.34: Brittle getattr(service_config, ...) found — use typed config class access:"
    echo "$BRITTLE_GETATTR" | head -5
    V=$(( V + 1 ))
else
    log_success "STEP 5.34: No brittle getattr config patterns"
fi

# ============================================================
# STEP 5.35 — No duplicate API URL constants (Pattern: DeFi/macro URLs)
# External API URLs must come from unified-features-interface, not local hardcoding.
# ============================================================
HARDCODED_URLS=$(rg '"https://api\.(llama\.fi|coingecko\.com|alternative\.me|stlouisfed\.org)' \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!**/tests/**' --glob '!**/scripts/**' \
    "$SOURCE_DIR/" 2>/dev/null \
    | grep -v '# CORRECT-LOCAL' \
    | grep -v 'Field(' \
    | grep -v 'default=' \
    || :)
if [ -n "$HARDCODED_URLS" ]; then
    log_fail "STEP 5.35: Hardcoded external API URLs found — import from unified_features_interface:"
    echo "$HARDCODED_URLS" | head -5
    V=$(( V + 1 ))
else
    log_success "STEP 5.35: No hardcoded external API URLs"
fi

# ============================================================
# STEP 5.36 — Config singleton: no bare Settings() outside get_settings()
# Components must use get_settings() singleton, not construct fresh Settings().
# ============================================================
BARE_SETTINGS=$(rg 'Settings\(\)' \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!**/tests/**' --glob '!**/scripts/**' \
    --glob '!**/config.py' \
    --glob '!**/conftest.py' \
    "$SOURCE_DIR/" 2>/dev/null \
    | grep -v 'get_settings' \
    | grep -v '# CORRECT-LOCAL' \
    | grep -v '_settings = ' \
    || :)
if [ -n "$BARE_SETTINGS" ]; then
    log_fail "STEP 5.36: Bare Settings() construction found outside config.py — use get_settings() singleton:"
    echo "$BARE_SETTINGS" | head -5
    V=$(( V + 1 ))
else
    log_success "STEP 5.36: No bare Settings() outside config module"
fi

# ============================================================
# STEP 5.37 — No inline HF / LTV / margin thresholds (P1.0e — workspace audit 2026-05-01)
# Margin thresholds belong in UAC LIQUIDATION_PARAMS_REGISTRY. Inlining
# them in service code is what produced the 1.5/1.3/1.1 vs 1.2 vs 1.2
# Aave HF threshold drift incident -- three services disagreeing on the
# same protocol's liquidation band. Allowed in tests + opt-out lines.
# ============================================================
INLINE_THRESHOLDS=$(rg 'Decimal\("(1\.05|1\.10?|1\.15|1\.20?|1\.30?|1\.50?)"\)|liquidation_threshold\s*=|maintenance_margin_pct\s*=|maintenance_margin\s*=\s*Decimal' \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!**/tests/**' --glob '!**/scripts/**' \
    "$SOURCE_DIR/" 2>/dev/null \
    | grep -v '# CORRECT-LOCAL' \
    | grep -v 'noqa: qg-inline-threshold' \
    || :)
if [ -n "$INLINE_THRESHOLDS" ]; then
    log_fail "STEP 5.37: Inline HF/LTV/margin thresholds found — use UAC LIQUIDATION_PARAMS_REGISTRY (see workspace audit C2/C4/C1):"
    echo "$INLINE_THRESHOLDS" | head -5
    V=$(( V + 1 ))
else
    log_success "STEP 5.37: No inline HF/LTV/margin thresholds (UAC LIQUIDATION_PARAMS_REGISTRY)"
fi

# ============================================================
# STEP 5.38 — No local domain Event/Snapshot/Alert/Trigger/Fill BaseModel
# (P1.0e — workspace audit 2026-05-01). Inter-service event schemas live
# in unified_api_contracts.internal.inter_service_events. Local definitions
# fragment the wire-format contract. Allowed only with # CORRECT-LOCAL on
# the line above (extends the existing convention used elsewhere).
# ============================================================
LOCAL_EVENT_MODELS=$(rg '^class \w*(Event|Snapshot|Alert|Trigger|Fill)\(BaseModel\):' \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!**/tests/**' --glob '!**/scripts/**' \
    -B 1 \
    "$SOURCE_DIR/" 2>/dev/null \
    | grep -B0 -A0 '^class' \
    | grep -v '# CORRECT-LOCAL' \
    || :)
if [ -n "$LOCAL_EVENT_MODELS" ]; then
    log_fail "STEP 5.38: Local Event/Snapshot/Alert/Trigger/Fill BaseModel found — import from unified_api_contracts.internal:"
    echo "$LOCAL_EVENT_MODELS" | head -5
    V=$(( V + 1 ))
else
    log_success "STEP 5.38: No local domain event models (use UAC inter_service_events)"
fi

qg_prof end codex

# STEP 5.24 — No `# type: ignore` (OPT-IN: ENFORCE_NO_TYPE_IGNORE=true in repo quality-gates.sh).
# `# type: ignore` is a BLANKET suppress-all — basedpyright ignores the bracketed codes and
# hides EVERY error on the line, masking future bugs. Use precise `# pyright: ignore[reportX]`.
# Banned workspace-wide (CLAUDE.md "No # type: ignore"); enforced per-repo once converted so it
# does not break un-converted fleet repos. Scope mirrors basedpyright (excludes tests/ + **/testing/**).
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
elif [[ $V -gt 0 ]]; then
    log_warn "Codex compliance: $V violations (within tolerance of $_max_v)"
else
    log_ok "Codex compliance PASSED"
fi

# ── [5.5a] WORKFLOW EXPRESSION GUARD (always-on, version-proof) ───────────────
# Incident 2026-06-04: an empty `${{ }}` expression inside a run-block COMMENT in
# cloud-build-router.yml reached main and broke the workflow's PARSE — GitHub
# rejected it with "workflow file issue", 0 jobs, so defer-on-freeze never ran.
# The actionlint block below was ALSO silently skipped for unified-trading-pm (its
# `[ -d $REPO_ROOT/.github/workflows ]` guard is false in the CI reusable-workflow
# context — no [5.5/6] line in PM's v2 log), so nothing caught it. This standalone
# guard is the targeted, fleet-safe fix: robust dir-detection + a regex for the
# exact parse-breaking class. It does NOT run full actionlint (which surfaces many
# pre-existing best-practice nits fleet-wide), only the always-invalid empty-expr.
# GitHub evaluates ${{ }} everywhere incl. run-block comments; to show a literal
# `${{` escape it (e.g. `$\{\{`), never write a bare `${{ }}`.
_WF_DIR_GUARD=""
for _cand in "${REPO_ROOT:-}/.github/workflows" "$(git rev-parse --show-toplevel 2>/dev/null)/.github/workflows" "${PROJECT_ROOT:-}/.github/workflows" "./.github/workflows"; do
    [ -d "$_cand" ] && { _WF_DIR_GUARD="$_cand"; break; }
done
if [ -n "$_WF_DIR_GUARD" ]; then
    if grep -rnE '\$\{\{[[:space:]]*\}\}' "$_WF_DIR_GUARD" 2>/dev/null; then
        log_fail "Workflow: empty \${{ }} expression(s) above — GitHub rejects these at parse time (0 jobs). Reword/escape."
        exit 1
    fi
fi

# ── [5.5] WORKFLOW LINT (actionlint) ──────────────────────────────────────────
# Dir-detection broadened to git-toplevel (mirrors [5.5a]) — the original
# `[ -d ${REPO_ROOT}/.github/workflows ]` guard was silently false in the v2
# reusable-workflow context (REPO_ROOT mis-resolves), so full actionlint never ran
# for PM. Resolve the workflows dir robustly so the gate actually fires.
_WF_LINT_DIR=""
for _cand in "${REPO_ROOT:-}/.github/workflows" "$(git rev-parse --show-toplevel 2>/dev/null)/.github/workflows" "${PROJECT_ROOT:-}/.github/workflows" "./.github/workflows"; do
    [ -d "$_cand" ] && { _WF_LINT_DIR="$_cand"; break; }
done
if [ -n "$_WF_LINT_DIR" ]; then
    log_section "[5.5/6] WORKFLOW LINT (actionlint)"
    if command -v actionlint &>/dev/null; then
        # CONTENT-HASH CACHE (plan quality_gates_speed_and_config_ssot_2026_06_09 Phase 3):
        # key = .github/workflows/*.yml file names + contents (plain cat, NOT git blobs —
        # _WF_LINT_DIR may resolve outside the repo's pathspec in the CI reusable-workflow
        # context) + actionlint version + SHELLCHECK_OPTS, cached at
        # .qg_cache/actionlint_content_hash. ONLY a 0-findings run is cached — findings
        # always re-print. Bypass: QG_NO_CACHE=1 forces a full lint.
        _al_key=$({
            while IFS= read -r -d '' _wf; do printf '%s\n' "$_wf"; cat "$_wf" 2>/dev/null || :; done \
                < <(find "$_WF_LINT_DIR" -name "*.yml" -type f -print0 2>/dev/null | LC_ALL=C sort -z)
            actionlint --version 2>/dev/null || :
            echo "${SHELLCHECK_OPTS:-}"
        } | _qg_hash)
        if qg_cache_hit actionlint_content_hash "$_al_key"; then
            log_success "Workflow lint: cached (workflows unchanged)"
        else
        WORKFLOW_ERRORS=0
        # actionlint's OWN rules (undefined outputs, untrusted github.event.* in run:,
        # the empty-${{ }} parse-breaking class, bad expressions) stay STRICT — those are
        # the real workflow-correctness errors this gate exists to catch. But its EMBEDDED
        # shellcheck defaults to reporting info/style nits (SC2086 word-splitting=info,
        # SC2129 redirect-style=style) in inline `run:` scripts — failing the QG fleet-wide
        # on shellcheck STYLE is scope-creep beyond the gate's intent and was a regression
        # of the [5.5] re-enable (deployment-service + others v2-red on pure style nits).
        # Raise embedded-shellcheck to warning+ so genuine shell bugs still fail but
        # info/style suggestions don't. (SHELLCHECK_OPTS is read by actionlint's shellcheck.)
        export SHELLCHECK_OPTS="--severity=warning${SHELLCHECK_OPTS:+ $SHELLCHECK_OPTS}"
        while IFS= read -r -d '' wf; do
            actionlint "$wf" 2>&1 || WORKFLOW_ERRORS=$(( WORKFLOW_ERRORS + 1 ))
        done < <(find "$_WF_LINT_DIR" -name "*.yml" -print0 2>/dev/null)
        # NON-FATAL (warn, not fail) — transitional, codified 2026-06-07. Hard-failing the
        # WHOLE FLEET on broad actionlint findings was a rule-11(a) violation: the canonical
        # fixed templates (e.g. major-bump-issue-handler env-var indirection) are on LDR but
        # NOT yet on every repo's main/staging, so a PR into any main fails [5.5] on the
        # un-propagated template — a gate the fleet does not yet pass. Findings still print
        # (visible + fixable); the empty-${{ }} PARSE-BREAK class stays a HARD fail in [5.5a]
        # below (separate, always-on, 0-false-positive). RE-HARDEN this to `exit 1` once the
        # fixed workflow templates have propagated to all repos' main+staging (the LDR→main
        # drain) and the fleet provably passes. SSOT: codex/08-workflows/ci-cd-flow.md +
        # cursor-configs/AUTONOMOUS_AGENT_RULES.md Rule 11.
        if [ $WORKFLOW_ERRORS -gt 0 ]; then
            log_warn "Workflow lint: $WORKFLOW_ERRORS file(s) with actionlint findings (NON-FATAL transitional — see [5.5a] for the hard parse-break guard; re-harden after templates propagate to all mains)"
        else
            qg_cache_store actionlint_content_hash "$_al_key"
        fi
        log_ok "Workflow lint checked (broad actionlint = warn; parse-break = hard in [5.5a])"
        fi
    else
        log_warn "actionlint not found — skipping workflow lint (install: brew install actionlint)"
    fi

    # Cross-repo checkout must use GH_PAT, not GITHUB_TOKEN (GITHUB_TOKEN is repo-scoped only)
    _TOKEN_CHECKER="${WORKSPACE_ROOT}/unified-trading-pm/scripts/validation/check-workflow-tokens.py"
    if [ -f "$_TOKEN_CHECKER" ]; then
        if ! $PYTHON_CMD "$_TOKEN_CHECKER" --dir "$_WF_LINT_DIR" 2>&1; then
            log_fail "Workflow: cross-repo checkout uses secrets.GITHUB_TOKEN — must use secrets.GH_PAT"
            exit 1
        fi
        log_success "Workflow: GH_PAT used for cross-repo checkouts"
    fi

    # Bash-guard checks: secrets.TELEGRAM_CHAT_ID (→ vars.) and $(&&) without || true
    _BASH_GUARD_CHECKER="${WORKSPACE_ROOT}/unified-trading-pm/scripts/validation/check-workflow-bash-guards.py"
    if [ -f "$_BASH_GUARD_CHECKER" ]; then
        if ! $PYTHON_CMD "$_BASH_GUARD_CHECKER" --dir "$_WF_LINT_DIR" 2>&1; then
            log_fail "Workflow bash-guard violations found — see output above"
            exit 1
        fi
        log_success "Workflow bash guards OK"
    fi
fi

# ── [5.6] SERVICE INFRASTRUCTURE CHECKS ──────────────────────────────────────

# unified-trading-pm (scripts-only) and similar repos set SKIP_SERVICE_LIFECYCLE_STEPS=true — not HTTP services.
if [ "${SKIP_SERVICE_LIFECYCLE_STEPS:-false}" = "true" ]; then
    log_success "STEP 5.61: skipped (SKIP_SERVICE_LIFECYCLE_STEPS — not a deployable service)"
    log_success "STEP 5.62: skipped (SKIP_SERVICE_LIFECYCLE_STEPS — not a deployable service)"
else
    # 5.6.1 — ServiceBootstrap / fastapi_uei_lifespan usage (replaces lifecycle event grep)
    # STARTED/STOPPED/FAILED lifecycle events are emitted by UTL ServiceBootstrap.run() for CLI
    # services, or by fastapi_uei_lifespan for HTTP services. Either satisfies this check.
    _HAS_BOOTSTRAP=$(rg 'ServiceBootstrap\(' --type py --glob '!.venv*' --glob '!**/tests/**' "$SOURCE_DIR/" -q 2>/dev/null && echo "yes" || echo "no")
    _HAS_HTTP_LIFECYCLE=$(rg 'fastapi_uei_lifespan\(' --type py --glob '!.venv*' --glob '!**/tests/**' "$SOURCE_DIR/" -q 2>/dev/null && echo "yes" || echo "no")
    if [ "$_HAS_BOOTSTRAP" = "yes" ] || [ "$_HAS_HTTP_LIFECYCLE" = "yes" ]; then
        log_success "STEP 5.61: ServiceBootstrap/fastapi_uei_lifespan used (lifecycle events handled by UTL)"
    else
        log_fail "STEP 5.61: ServiceBootstrap not found — services MUST use ServiceBootstrap from UTL for lifecycle events"
        V=$(( V + 1 ))
    fi

    # 5.6.2 — Health API (FastAPI make_health_router with data_freshness)
    # Every service must expose /health and /readiness via UTL make_health_router.
    _HAS_HEALTH=$(rg 'make_health_router' --type py --glob '!.venv*' --glob '!**/tests/**' "$SOURCE_DIR/" -q 2>/dev/null && echo "yes" || echo "no")
    if [ "$_HAS_HEALTH" = "yes" ]; then
        log_success "STEP 5.62: Health API present (make_health_router)"
    else
        log_fail "STEP 5.62: No health API — add api/main.py with make_health_router (see market-tick-data-service/api/main.py)"
        V=$(( V + 1 ))
    fi
fi

# 5.6.3 — run_lifecycle pairing for setup_events() entry-points
# Every script / entry-point that calls setup_events() MUST emit a paired
# RUN_STARTED + RUN_COMPLETED|RUN_FAILED via either:
#   * run_lifecycle(...)        (preferred — auto-correlated by run_id)
#   * ServiceBootstrap(...)     (services — UTL handles lifecycle internally)
#   * ad-hoc log_event _RUN_STARTED + _RUN_(COMPLETED|FAILED) pair (legacy)
# The UTL helper definition itself + repos that define setup_events are skipped.
_LIFECYCLE_EXTRA_GLOBS=()
for g in ${LIFECYCLE_EXCLUDE_GLOBS[@]+"${LIFECYCLE_EXCLUDE_GLOBS[@]}"}; do
    _LIFECYCLE_EXTRA_GLOBS+=(--glob "$g")
done
_LIFECYCLE_FILES=$(rg -l 'setup_events\(' --type py \
    --glob '!.venv*' \
    --glob '!**/tests/**' \
    --glob '!**/run_lifecycle.py' \
    --glob '!**/events/__init__.py' \
    ${_LIFECYCLE_EXTRA_GLOBS[@]+"${_LIFECYCLE_EXTRA_GLOBS[@]}"} \
    "$SOURCE_DIR/" 2>/dev/null || :)
_LIFECYCLE_VIOLATIONS=""
for _f in $_LIFECYCLE_FILES; do
    # Skip files that define setup_events themselves (the UTL helper).
    if grep -q 'def setup_events' "$_f" 2>/dev/null; then continue; fi
    # Pass: ServiceBootstrap wraps lifecycle for services.
    if grep -q 'ServiceBootstrap(' "$_f" 2>/dev/null; then continue; fi
    # Pass: run_lifecycle context manager.
    if grep -q 'run_lifecycle(' "$_f" 2>/dev/null; then continue; fi
    # Legacy pass: explicit *_RUN_STARTED + *_RUN_(COMPLETED|FAILED) pair.
    if grep -qE '_RUN_STARTED' "$_f" 2>/dev/null && grep -qE '_RUN_(COMPLETED|FAILED)' "$_f" 2>/dev/null; then
        continue
    fi
    _LIFECYCLE_VIOLATIONS="${_LIFECYCLE_VIOLATIONS}${_f}"$'\n'
done
if [ -n "$_LIFECYCLE_VIOLATIONS" ]; then
    log_fail "STEP 5.63: setup_events() entry-points missing run_lifecycle/ServiceBootstrap pairing — wrap main() in 'with run_lifecycle(service_name=...) as run:' (from unified_trading_library):"
    printf "  %s\n" $_LIFECYCLE_VIOLATIONS
    V=$(( V + 1 ))
else
    log_success "STEP 5.63: All setup_events() entry-points paired with run_lifecycle / ServiceBootstrap / explicit RUN events"
fi

# STEP 5.64 — Preflight short-circuits MUST emit PREFLIGHT_SKIPPED
#
# Reference incident 2026-05-07: features-onchain-defi-backfill VM emitted
# only STARTED -> VALIDATION_COMPLETED -> STOPPED in 9 seconds with NO
# PROCESSING events. The VM's _preflight_guard fired (skip-if-exists,
# dependency-check-fail, or date-out-of-range — operator could not tell
# which from the event stream alone). PREFLIGHT_SKIPPED with a structured
# PreflightSkipReason resolves silent skips so dashboards can distinguish
# (a) skip-if-exists from (b) dep-fail from (c) date-out-of-range from
# (d) calendar-non-trading-day from (e) concurrent-VM-owns-shard.
#
# Detection: any service source containing one of the canonical preflight
# patterns (`_preflight_guard`, `should_skip_date`, `_check_dependencies`,
# `check_shard_freshness` directly invoked outside ManifestWriter) MUST
# also import / call `emit_preflight_skip` (UTL helper) at every short-
# circuit return site. The check is grep-based; refinements (per-return-
# branch coverage) live in a follow-up if needed.
if [ -n "${SOURCE_DIR:-}" ] && [ -d "$SOURCE_DIR" ]; then
    _PREFLIGHT_PATTERN_FILES=$(rg -l --type py \
        -e '_preflight_guard|should_skip_date|_check_dependencies|check_shard_freshness' \
        --glob '!tests/**' --glob '!scripts/**' \
        "$SOURCE_DIR/" 2>/dev/null || true)
    if [ -n "$_PREFLIGHT_PATTERN_FILES" ]; then
        # Service has at least one preflight-guard pattern. Confirm the
        # service ALSO emits PREFLIGHT_SKIPPED somewhere.
        _EMIT_FILES=$(rg -l --type py \
            -e 'emit_preflight_skip\(|PREFLIGHT_SKIPPED' \
            --glob '!tests/**' --glob '!scripts/**' \
            "$SOURCE_DIR/" 2>/dev/null || true)
        if [ -z "$_EMIT_FILES" ]; then
            log_fail "STEP 5.64: Service has preflight-guard patterns but no emit_preflight_skip / PREFLIGHT_SKIPPED — silent skips will be invisible in the event stream. Files with preflight patterns:"
            printf "  %s\n" $_PREFLIGHT_PATTERN_FILES
            log_fail "         Fix: import emit_preflight_skip from unified_trading_library + PreflightSkipReason from unified_api_contracts.internal; emit at every preflight return-True / dependency-raise / skip-date branch. SSOT: features-onchain-service/cli/handlers/batch_handler.py:_preflight_guard (commit reference 2026-05-07)."
            V=$(( V + 1 ))
        else
            log_success "STEP 5.64: Preflight short-circuits emit PREFLIGHT_SKIPPED (silent-skip visibility per UTL emit_preflight_skip)"
        fi
    else
        log_success "STEP 5.64: skipped (no preflight-guard patterns in this service)"
    fi
else
    log_success "STEP 5.64: skipped (SOURCE_DIR not set or not a directory)"
fi

# STEP 5.65 — Removed-symbol AST-walk (Citadel-Grade Planning § 6 EXTENDED)
#
# Enforces CLAUDE.md "Citadel-Grade Planning Standards § 6 Downstream
# Consumer Updates (extended 2026-05-08 to cover non-library refactors)":
# every workspace consumer must update its imports/usages when a public
# symbol is REMOVED or RENAMED by a refactor.
#
# The check runs `unified-trading-pm/scripts/quality_gates/check_removed_symbols.py`
# against the calling repo's source tree. Manifest entries with
# `status: removed` fail CI; `status: pending_removal` entries surface
# as warnings (informational, non-blocking) until their successor
# migration plan ships.
#
# Reference incident: 2026-05-01 → 2026-05-08 silent rot of
# `e2e-testing/scripts/defi/colocated_engine.py` (broken import of
# strategy-service's removed `get_strategy_factories`). Caught at
# runtime 7 days later by an operator running the harness manually;
# this AST-walk would have caught it on the next PR in <1 minute.
#
# Adding a new entry to the manifest: see the file header in
# `unified-trading-pm/scripts/quality_gates/removed_symbols_manifest.yaml`
# — required keys, status enum, when-to-add discipline.
_REMOVED_SYMBOLS_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_removed_symbols.py"
qg_prof start removed-symbols
if [ -f "$_REMOVED_SYMBOLS_CHECKER" ]; then
    # Run scoped to the calling repo so per-repo QG only sees its own
    # consumers; the workspace-wide sweep is run separately (e.g. via
    # the CI cron, or `python <checker>` from workspace root).
    # FIX 2026-06-09: REPO_ROOT IS the workspace root (qg-common sets it to PROJECT_ROOT/..),
    # so the old basename/dirname-of-REPO_ROOT scanned the ENTIRE workspace (incl. every .tabs
    # slot clone) on every repo's gate → ~286s single-threaded. Match STEP 5.67's correct wiring:
    # scope = this repo (PROJECT_ROOT), workspace-root = REPO_ROOT. The cross-repo workspace-wide
    # sweep runs separately (cron/CI) — see quality_gates_speed_and_config_ssot_2026_06_09.md.
    _REPO_REL_TO_WORKSPACE=$(basename "$PROJECT_ROOT")
    _WORKSPACE_ROOT="$REPO_ROOT"
    if python "$_REMOVED_SYMBOLS_CHECKER" \
            --workspace-root "$_WORKSPACE_ROOT" \
            --scope "$_REPO_REL_TO_WORKSPACE" \
            --workers 1 >/tmp/removed_symbols_qg.log 2>&1; then
        log_success "STEP 5.65: No references to removed symbols (Citadel § 6 EXTENDED)"
    else
        log_fail "STEP 5.65: Repo references symbols listed as 'removed' in unified-trading-pm/scripts/quality_gates/removed_symbols_manifest.yaml. Update consumers per the documented successor:"
        cat /tmp/removed_symbols_qg.log
        log_fail "         Manifest: unified-trading-pm/scripts/quality_gates/removed_symbols_manifest.yaml"
        log_fail "         Recheck: python unified-trading-pm/scripts/quality_gates/check_removed_symbols.py --scope $_REPO_REL_TO_WORKSPACE"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.65: skipped (checker not yet provisioned in this repo's PM checkout)"
fi
qg_prof end removed-symbols

# STEP 5.67 — Banned NaN-placeholder / bypass-record_captured method AST-walk
#
# (5.66 is reserved for the planned launcher-script multi-process-isolation
# AST-walk per CLAUDE.md "Per-VM shard isolation for concurrent backfills".)
#
# Enforces CLAUDE.md "Honest absence vs fake placeholders" + "No double SSOT in
# data-saving methodology" + "Four-category empty-output decision": the
# `_create_empty_output()`-style placeholder methods (which emit NaN-OHLC
# placeholder bars that LOOK populated and pass the manifest as `captured`) are
# BANNED from `base_adapter` and any equivalent base class; so is a direct
# `*.upload_bytes(...)` candle write that bypasses `record_captured` (the MDPS
# legacy `orchestration_writer._write_candles` path Track D P0-2 flagged — ZERO
# manifest record + ZERO 4-pillar write-gate on every candle MDPS writes today).
#
# The check runs `check_banned_placeholder_methods.py` against the calling repo's
# source tree (scripts/ + tests/ excluded). It is a SHRINKING ratchet: occurrences
# listed in `banned_placeholder_methods_baseline.yaml` (status: pending_removal —
# the writegate-Phase-2.A backlog) surface as WARNINGS (exit-clean); any NEW
# occurrence not in the baseline fails CI. Remove a baseline entry the moment its
# successor deletes the occurrence; never ADD a new one.
#
# Reference incidents: 2026-05-05 MDPS 1440-NaN-bar (placeholder bars persisted for
# years before hand-inspection caught them); Track D audit 2026-05-11 P0-2
# (`tradfi/ohlcv_passthrough.py:266 _create_full_day_empty_output` still live; the
# `record_captured`/write-gate path dead on MDPS's live path by MRO).
_BANNED_PLACEHOLDER_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_banned_placeholder_methods.py"
if [ -f "$_BANNED_PLACEHOLDER_CHECKER" ]; then
    # Scope = THIS repo's directory name; workspace-root = dir CONTAINING the repo
    # dirs. `REPO_ROOT` is set by qg-common.sh:48 to `dirname(PROJECT_ROOT)` —
    # it IS the workspace-root (contains the repo dirs), NOT one of them. Old
    # wiring (`basename`/`dirname REPO_ROOT`) silently scanned wrong tree +
    # computed mis-rooted relative paths breaking baseline match. Reference:
    # plans/active/issues/qg_runner_worktree_foot_guns_2026_05_12.md.
    _BPM_REPO=$(basename "$PROJECT_ROOT")
    _BPM_WS="$REPO_ROOT"
    _BPM_SRC_ARG=()
    [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ] && _BPM_SRC_ARG=(--source-dir "$SOURCE_DIR")
    if $PYTHON_CMD "$_BANNED_PLACEHOLDER_CHECKER" \
            --workspace-root "$_BPM_WS" --scope "$_BPM_REPO" "${_BPM_SRC_ARG[@]}" >/tmp/banned_placeholder_qg.log 2>&1; then
        # exit 0 — either no occurrences, or only baselined (pending_removal) ones.
        if grep -q '^\[WARN\]' /tmp/banned_placeholder_qg.log 2>/dev/null; then
            log_warn "STEP 5.67: $(grep -c '^\[WARN\]' /tmp/banned_placeholder_qg.log) baselined NaN-placeholder occurrence(s) (pending_removal — writegate Phase 2.A backlog); 0 new"
        else
            log_success "STEP 5.67: No banned NaN-placeholder / bypass-record_captured methods"
        fi
    else
        log_fail "STEP 5.67: NEW banned NaN-placeholder / bypass-record_captured pattern (not in unified-trading-pm/scripts/quality_gates/banned_placeholder_methods_baseline.yaml). Delete it — emit record_empty(reason=...) / record_captured() instead (CLAUDE.md 'Honest absence vs fake placeholders'):"
        cat /tmp/banned_placeholder_qg.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_banned_placeholder_methods.py --workspace-root $_BPM_WS --scope $_BPM_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.67: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# STEP 5.69 — inline f"gs://..." / f"s3://..." cloud-URI formatter ratchet
#
# (5.68 is reserved by `available_at_lookahead_bias_completion_2026_05_08.md`
# for the feature-compute lookahead-callsite check — not yet implemented.)
#
# Enforces CLAUDE.md "Bucket-name SSOT (b+)": every bucket lookup goes through
# `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)`
# (or `resolve_bucket_uri(...)` for a full URI) — never an inline f-string that
# builds a `gs://` / `s3://` URI by hand. Scattering inline `f"gs://{bucket}/..."`
# formatters across services is how the workspace ended up with the bucket-name
# triple-drift the `bucket_name_ssot_canonicalisation_2026_05_10.md` plan exists
# to collapse (yaml SSOT vs per-family config.py template vs UTL resolver vs
# deployment-api's own internal templates — pre-audit manifest "Layer 1-5").
#
# The check runs `check_inline_bucket_uri.py` against the calling repo's source
# (scripts/ + tests/ excluded). It is a SHRINKING per-repo COUNT ratchet:
# `inline_bucket_uri_baseline.yaml` records the CURRENTLY-KNOWN count of inline
# `f"gs://...`/`f"s3://...` formatters (those WITHOUT a `# noqa: gs-uri` marker —
# the "grandfathered, intentional" exemption) per repo. A repo whose live count
# EXCEEDS its baseline fails CI (a NEW inline formatter landed — route it through
# `resolve_bucket_uri()` or mark it `# noqa: gs-uri` with a one-line reason). A
# repo BELOW its baseline → WARNING (ratchet the baseline DOWN: re-run
# `--update-baseline`). Repos not in the baseline default to count=0 (zero tolerance).
#
# v1 is grep-based (the formatter is always a single-line f-string in practice);
# v2 hardening = an AST-walk distinguishing `f"gs://{x}/..."` from a
# `resolve_bucket_uri(...)` call + ignoring docstrings/comments (same shape as
# STEP 5.65's AST-walk). v1 ships first. SSOT: bucket_name_ssot_canonicalisation_2026_05_10.md
# Done-def #5 + § "QG STEP 5.6X design".
_INLINE_URI_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_inline_bucket_uri.py"
if [ -f "$_INLINE_URI_CHECKER" ]; then
    # Slot-worktree-aware: scope=this-repo's-dir; workspace-root=REPO_ROOT (which
    # IS the workspace root per qg-common.sh:48). Reference:
    # plans/active/issues/qg_runner_worktree_foot_guns_2026_05_12.md.
    _IU_REPO=$(basename "$PROJECT_ROOT")
    _IU_WS="$REPO_ROOT"
    _IU_SRC_ARG=()
    [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ] && _IU_SRC_ARG=(--source-dir "$SOURCE_DIR")
    if $PYTHON_CMD "$_INLINE_URI_CHECKER" \
            --workspace-root "$_IU_WS" --scope "$_IU_REPO" "${_IU_SRC_ARG[@]}" >/tmp/inline_bucket_uri_qg.log 2>&1; then
        if grep -q '^\[WARN\]' /tmp/inline_bucket_uri_qg.log 2>/dev/null; then
            log_warn "STEP 5.69: $(grep -c '^\[WARN\]' /tmp/inline_bucket_uri_qg.log) repo(s) BELOW the inline-URI baseline — ratchet inline_bucket_uri_baseline.yaml DOWN (re-run --update-baseline)"
        else
            log_success "STEP 5.69: No new inline gs://|s3:// f-string URI formatters (baseline-ratchet, bucket-name SSOT (b+))"
        fi
    else
        log_fail "STEP 5.69: NEW inline f\"gs://...\" / f\"s3://...\" cloud-URI formatter(s) above the per-repo baseline. Route through unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_uri(...) / resolve_bucket_name(...), or add '# noqa: gs-uri' with a one-line reason (CLAUDE.md 'Bucket-name SSOT (b+)'):"
        cat /tmp/inline_bucket_uri_qg.log
        log_fail "         Baseline: unified-trading-pm/scripts/quality_gates/inline_bucket_uri_baseline.yaml (NEVER raise a count)"
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_inline_bucket_uri.py --workspace-root $_IU_WS --scope $_IU_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.69: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# STEP 5.92 — Ban legacy `category=` kwarg at ManifestWriter writes (v9 canonical)
#
# The UTL ManifestWriter asset-group write param was renamed `category` →
# `asset_group` (2026-06-02; sports_/defi_manifest_canonicalisation cross-AG
# dead-bucket root). v9 post-migration canonical vocabulary is `asset_group`
# everywhere — never `category`, not even as a fallback (operator 2026-06-02).
# AST-walk, zero-tolerance (the workspace-wide rename removed every occurrence).
# (5.71-5.91 are in use elsewhere in this file — these two ratchets take 5.92/5.93.)
_NOCAT_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_no_category_kwarg_at_manifest_write.py"
if [ -f "$_NOCAT_CHECKER" ]; then
    _NC_REPO=$(basename "$PROJECT_ROOT")
    _NC_WS="$REPO_ROOT"
    _NC_SRC_ARG=()
    [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ] && _NC_SRC_ARG=(--source-dir "$SOURCE_DIR")
    if $PYTHON_CMD "$_NOCAT_CHECKER" \
            --workspace-root "$_NC_WS" --scope "$_NC_REPO" "${_NC_SRC_ARG[@]}" >/tmp/no_category_kwarg_qg.log 2>&1; then
        log_success "STEP 5.92: No legacy category= kwarg at ManifestWriter writes (asset_group= is v9 canonical)"
    else
        log_fail "STEP 5.92: Legacy category= kwarg(s) at ManifestWriter writes — rename to asset_group= (UTL contract, v9 canonical):"
        cat /tmp/no_category_kwarg_qg.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_no_category_kwarg_at_manifest_write.py --workspace-root $_NC_WS --scope $_NC_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.92: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# STEP 5.93 — Ban explicit project_id= on asset-group bucket builders (no-env bypass)
#
# Passing project_id to get_bucket_name()/get_write_bucket_name() bypasses the
# cloud-providers.yaml SSOT and returns the legacy no-env bucket shape (e.g.
# instruments-store-sports-{pid}), which is DELETED at each asset_group's
# legacy-bucket decommission. Canonical: drop project_id (delegates to the yaml
# SSOT → env-tiered -prd-) or use resolve_bucket_name(...). AST-walk, scoped to
# string-literal asset-group domains; scripts/tests/migration trees + the
# bucket-naming SSOT modules are exempt. Zero-tolerance.
_NOPID_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_no_explicit_project_id_bucket.py"
if [ -f "$_NOPID_CHECKER" ]; then
    _NP_REPO=$(basename "$PROJECT_ROOT")
    _NP_WS="$REPO_ROOT"
    _NP_SRC_ARG=()
    [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ] && _NP_SRC_ARG=(--source-dir "$SOURCE_DIR")
    if $PYTHON_CMD "$_NOPID_CHECKER" \
            --workspace-root "$_NP_WS" --scope "$_NP_REPO" "${_NP_SRC_ARG[@]}" >/tmp/no_explicit_project_id_bucket_qg.log 2>&1; then
        log_success "STEP 5.93: No explicit project_id on asset-group bucket builders (delegates to yaml SSOT → -prd- canonical)"
    else
        log_fail "STEP 5.93: Explicit project_id on asset-group bucket builder(s) → legacy no-env bucket. Drop project_id or use resolve_bucket_name(...):"
        cat /tmp/no_explicit_project_id_bucket_qg.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_no_explicit_project_id_bucket.py --workspace-root $_NP_WS --scope $_NP_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.93: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# STEP 5.94 — try/except-ImportError fallback-import ratchet (no-empty-fallbacks)
#
# Enforces .cursor/rules/standards/no-empty-fallbacks.mdc § "No try/except
# ImportError Fallbacks" as CI (harden_grepable_rules_into_ci_gates_2026_06_02.md
# Phase 3): never wrap imports in try/except (ImportError|ModuleNotFoundError) —
# or an imports-only try with a broad except — to provide a fallback; fail LOUD
# at import time. AST-based (docstrings/comments never trigger). Per-repo
# SHRINKING count ratchet: no_fallback_imports_baseline.yaml grandfathers the
# audited pre-existing set (2026-06-10: 75 sites fleet-wide); a NEW shim fails.
# Per-line opt-out: `# noqa: fallback-import` on the try: line + a reason.
_NOFB_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_no_fallback_imports.py"
if [ -f "$_NOFB_CHECKER" ]; then
    _FB_REPO=$(basename "$PROJECT_ROOT")
    _FB_WS="$REPO_ROOT"
    if $PYTHON_CMD "$_NOFB_CHECKER" \
            --workspace-root "$_FB_WS" --scope "$_FB_REPO" >/tmp/no_fallback_imports_qg.log 2>&1; then
        if grep -q '^\[WARN\]' /tmp/no_fallback_imports_qg.log 2>/dev/null; then
            log_warn "STEP 5.94: below the fallback-import baseline — ratchet no_fallback_imports_baseline.yaml DOWN (re-run --update-baseline)"
        else
            log_success "STEP 5.94: No new try/except-ImportError fallback-import shims (baseline-ratchet, no-empty-fallbacks)"
        fi
    else
        log_fail "STEP 5.94: NEW try/except-ImportError fallback-import shim(s) above the per-repo baseline. Import directly + declare the dep in pyproject, or add '# noqa: fallback-import' with a one-line reason (no-empty-fallbacks.mdc):"
        cat /tmp/no_fallback_imports_qg.log
        log_fail "         Baseline: unified-trading-pm/scripts/quality_gates/no_fallback_imports_baseline.yaml (NEVER raise a count)"
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_no_fallback_imports.py --workspace-root $_FB_WS --scope $_FB_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.94: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# STEP 5.95 — ruff DTZ (UTC-datetime ban) + TID251 (cloud-SDK ban) count ratchet
#
# Hardens CLAUDE.md "UTC datetimes always" (`datetime.now(timezone.utc)`, never
# naive now()/utcnow()/today()/zone-less strptime — pinned DTZ001-007/011/012/901)
# and "Cloud-agnostic I/O" (get_storage_client()/get_secret_client(), never
# `from google.cloud import …` / `import boto3` — TID251 banned-api) into CI
# (harden_grepable_rules_into_ci_gates_2026_06_02.md Phase 3). The canonical
# [tool.ruff] template (scripts/pyproject-templates/canonical-tool-sections.toml)
# carries the rules as config SSOT; this step enforces them TODAY as a per-repo
# SHRINKING count ratchet (ruff_rule_ratchet_baseline.yaml; 2026-06-10 seed:
# 180 dtz + 211 tid251 fleet-wide; tests/ excluded; UTL cloud_interface/ exempt
# for tid251). Per-line opt-out: ruff `# noqa: DTZ00x|TID251` + a reason.
_RUFFRR_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_ruff_rule_ratchet.py"
if [ -f "$_RUFFRR_CHECKER" ]; then
    _RR_REPO=$(basename "$PROJECT_ROOT")
    _RR_WS="$REPO_ROOT"
    if $PYTHON_CMD "$_RUFFRR_CHECKER" \
            --workspace-root "$_RR_WS" --scope "$_RR_REPO" >/tmp/ruff_rule_ratchet_qg.log 2>&1; then
        if grep -q '^\[WARN\]' /tmp/ruff_rule_ratchet_qg.log 2>/dev/null; then
            log_warn "STEP 5.95: below the DTZ/TID251 baseline — ratchet ruff_rule_ratchet_baseline.yaml DOWN (re-run --update-baseline)"
        else
            log_success "STEP 5.95: No new naive-datetime (DTZ) / direct cloud-SDK (TID251) sites (baseline-ratchet)"
        fi
    else
        log_fail "STEP 5.95: NEW naive-datetime (DTZ) / direct cloud-SDK (TID251) site(s) above the per-repo baseline. Use datetime.now(timezone.utc) / get_storage_client()/get_secret_client(), or add a ruff '# noqa: <code>' with a one-line reason:"
        cat /tmp/ruff_rule_ratchet_qg.log
        log_fail "         Baseline: unified-trading-pm/scripts/quality_gates/ruff_rule_ratchet_baseline.yaml (NEVER raise a count)"
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_ruff_rule_ratchet.py --workspace-root $_RR_WS --scope $_RR_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.95: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# STEP 5.70 — Explicit pipeline_mode= kwarg at every ManifestWriter.record_* call
#
# (5.6x is exhausted — 5.65/5.67/5.69 in use, 5.66/5.68 reserved above — so this
# manifest-data-correctness ratchet takes 5.70.)
#
# Enforces manifest_schema_final_gate_2026_05_09 Phase 4 "explicit-or-fail"
# contract: every `record_captured()` / `record_empty()` / `record_failed()` /
# `record_expected_unattempted()` (and the legacy `ManifestWriter.add()` path)
# call MUST pass an explicit `pipeline_mode=PipelineMode.<source>` kwarg matching
# the UAC SOURCE_PRIORITY top entry for that (asset_group, data_type). Implicit /
# inherited `pipeline_mode` is exactly how the availability manifest ended up
# unable to say WHICH source served a given (asset_group, data_type) — the v8
# schema makes `pipeline_mode` a first-class manifest column, and this ratchet
# keeps it explicit at the write boundary forever (no `**kwargs` swallowing, no
# orchestrator-inherited default).
#
# The check runs `check_pipeline_mode_explicit_at_record_calls.py` against the
# calling repo's source tree (scripts/ + tests/ excluded — same exclusion shape
# as STEP 5.67). It is a SHRINKING ratchet: occurrences listed in
# `pipeline_mode_explicit_baseline.yaml` (status: pending_phase_4_mtds /
# pending_phase_4_features — the Phase 4 sweep backlog) surface as WARNINGS
# (exit-clean); any NEW occurrence not in the baseline fails CI. Delete a baseline
# entry the moment its successor sweep ships the explicit kwarg; never ADD one.
# Rare legitimate N/A (e.g. a base-class method that re-forwards `**kwargs`) gets
# the inline marker `# QG-allow: pipeline-mode-not-applicable`.
#
# SSOT: manifest_schema_final_gate_2026_05_09.md Phase 4.GREP-VERIFY +
# Phase 4.DEFAULT-REMOVAL; CLAUDE.md "Live = batch (CRITICAL)" (only legitimate
# batch/live diff is which SOURCE serves a given (asset_group, data_type)).
_PIPELINE_MODE_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py"
if [ -f "$_PIPELINE_MODE_CHECKER" ]; then
    # Slot-worktree-aware: scope=this-repo's-dir; workspace-root=REPO_ROOT (which
    # IS the workspace root per qg-common.sh:48). Reference:
    # plans/active/issues/qg_runner_worktree_foot_guns_2026_05_12.md.
    _PM_REPO=$(basename "$PROJECT_ROOT")
    _PM_WS="$REPO_ROOT"
    _PM_SRC_ARG=()
    [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ] && _PM_SRC_ARG=(--source-dir "$SOURCE_DIR")
    if $PYTHON_CMD "$_PIPELINE_MODE_CHECKER" \
            --workspace-root "$_PM_WS" --scope "$_PM_REPO" "${_PM_SRC_ARG[@]}" >/tmp/pipeline_mode_explicit_qg.log 2>&1; then
        # exit 0 — either no occurrences, or only baselined (pending Phase 4 sweep) ones.
        if grep -q '^\[WARN\]' /tmp/pipeline_mode_explicit_qg.log 2>/dev/null; then
            log_warn "STEP 5.70: $(grep -c '^\[WARN\]' /tmp/pipeline_mode_explicit_qg.log) baselined record_*() call(s) missing explicit pipeline_mode= (pending Phase 4 sweep); 0 new"
        else
            log_success "STEP 5.70: Every ManifestWriter.record_*() call passes explicit pipeline_mode= kwarg"
        fi
    else
        log_fail "STEP 5.70: NEW ManifestWriter.record_*() call missing explicit pipeline_mode= kwarg (not in unified-trading-pm/scripts/quality_gates/pipeline_mode_explicit_baseline.yaml). Pass pipeline_mode=PipelineMode.<source> per UAC SOURCE_PRIORITY top entry, or add inline '# QG-allow: pipeline-mode-not-applicable' (manifest_schema_final_gate Phase 4 explicit-or-fail contract):"
        cat /tmp/pipeline_mode_explicit_qg.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py --workspace-root $_PM_WS --scope $_PM_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.70: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# STEP 5.71 — Emission-policy paired-callsite enforcement (writegate slice c Phase 6.9)
#
# For every service repo whose output data_types appear in UAC SERVICE_OUTPUT_POLICIES,
# asserts that every record_captured() callsite ALSO has a paired publish_with_policy() /
# publish_with_manifest_lookup() call within the same function body.
#
# Catches drift where a service-team adds a new derived-output adapter and wires
# record_captured() but forgets to wire the companion emission-policy helper.
#
# Escape hatch: add '# QG-allow: emission-policy-not-applicable' on the record_captured()
# line to mark input-data captures (not derived-output boundaries).
#
# Baseline ratchet: emission_policy_paired_callsites_baseline.yaml (starts empty — Phase
# 6.3-6.8 wired all callsites; only SHRINKS as remaining services migrate).
#
# Plan: writegate_honest_coverage_endtoend_2026_05_06.md Phase 6.9.
# SSOT: CLAUDE.md "Service-output emission policy (writegate slice b/c)".
_EMISSION_POLICY_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_emission_policy_paired_callsites.py"
if [ -f "$_EMISSION_POLICY_CHECKER" ]; then
    _EP_REPO=$(basename "$PROJECT_ROOT")
    _EP_WS="$REPO_ROOT"
    _EP_BASELINE="${REPO_ROOT}/unified-trading-pm/baselines/emission_policy_paired_callsites_baseline.yaml"
    _EP_BASELINE_ARG=()
    [ -f "$_EP_BASELINE" ] && _EP_BASELINE_ARG=(--baseline "$_EP_BASELINE")
    if $PYTHON_CMD "$_EMISSION_POLICY_CHECKER" \
            --workspace-root "$_EP_WS" --scope "$_EP_REPO" "${_EP_BASELINE_ARG[@]}" >/tmp/emission_policy_paired_qg.log 2>&1; then
        # exit 0 — either no violations, or only baselined ones.
        if grep -q '^\[STEP 5.71\] OK' /tmp/emission_policy_paired_qg.log 2>/dev/null; then
            _ep_baselined_count=$(grep -c '^\[WARN\]' /tmp/emission_policy_paired_qg.log 2>/dev/null || echo 0)
            if [ "$_ep_baselined_count" -gt 0 ]; then
                log_warn "STEP 5.71: ${_ep_baselined_count} baselined record_captured() callsite(s) missing publish_with_policy() (grandfathered pending Phase 6.3-6.8 rollout); 0 new"
            else
                log_success "STEP 5.71: All record_captured() callsites in scope have paired emission-policy calls (writegate Phase 6.9)"
            fi
        fi
    else
        log_fail "STEP 5.71: NEW record_captured() callsite(s) without paired publish_with_policy() / publish_with_manifest_lookup(). Wire the emission-policy helper or add '# QG-allow: emission-policy-not-applicable' on each input-data record_captured() line:"
        cat /tmp/emission_policy_paired_qg.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_emission_policy_paired_callsites.py --workspace-root $_EP_WS --scope $_EP_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.71: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# ── STEP 5.72: chain-set inclusion invariant on UAC chain_env ─────────────────
#
# Enforces MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES ⊇ GAS_FEE_CHAIN_START_DATES
# (via chain_id reverse-lookup) on the UAC chain_env registries. Drift between
# these three dicts produces silent zero-shard coverage in the honest-coverage
# panel — reference DF-7 in cross_asset_group_catalogue_audit_2026_05_10.md.
#
# Closes the Phase 1F-extend `check_chain_set_inclusion.py QG ratchet`
# carry-forward (cross_asset Phase 6A).
_CHAIN_INCLUSION_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_chain_set_inclusion.py"
if [ -f "$_CHAIN_INCLUSION_CHECKER" ]; then
    if $PYTHON_CMD "$_CHAIN_INCLUSION_CHECKER" >/tmp/chain_set_inclusion_qg.log 2>&1; then
        log_success "STEP 5.72: UAC chain_env MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES ⊇ GAS_FEE_CHAIN_START_DATES"
    else
        log_fail "STEP 5.72: UAC chain_env inclusion invariant violated (DF-7). Output:"
        cat /tmp/chain_set_inclusion_qg.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_chain_set_inclusion.py"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.72: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# ── STEP 5.73: ManifestWriter.add() with bundled data_type literal — banned ──
#
# ManifestWriter.add() raises ValueError for any bundled data_type (options_chain,
# futures_chain, prediction_canonical_question_group, sports_fixture_bundle) since
# wave2_polymarket_record_captured_from_counts_2026_05_09 Phase 4. This step bans
# literal-string bundled data_type arguments at the call-site level.
#
# Note: only literal-string "data_type=..." kwargs are detectable by static grep.
# Runtime-resolved data_type assignments (data_type=variable) pass through — they
# would fail at test/runtime when the ValueError fires.
#
# Plan: wave2_polymarket_record_captured_from_counts_2026_05_09 Phase 4 item 2.
if [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ]; then
    _BUNDLED_TYPES_PATTERN='data_type\s*=\s*["\x27](options_chain|futures_chain|prediction_canonical_question_group|sports_fixture_bundle)["\x27]'
    if grep -rn --include="*.py" -E "$_BUNDLED_TYPES_PATTERN" "${SOURCE_DIR}" | grep -v "^Binary" | grep -v "BUNDLED_DATA_TYPES" | grep -q "\.add("; then
        # A literal bundled data_type arg was passed to an .add() call.
        log_fail "STEP 5.73: ManifestWriter.add() called with literal bundled data_type. Use record_captured_from_counts() instead (wave2_polymarket plan Phase 4). Offending lines:"
        grep -rn --include="*.py" -E "$_BUNDLED_TYPES_PATTERN" "${SOURCE_DIR}" | grep -v "BUNDLED_DATA_TYPES" | grep "\.add("
        V=$(( V + 1 ))
    else
        log_success "STEP 5.73: No ManifestWriter.add() calls with literal bundled data_type"
    fi
else
    log_success "STEP 5.73: skipped (SOURCE_DIR not set or not a directory)"
fi

# ── STEP 5.74: MDPS bar-boundary truncation-bypass static check ───────────────
#
# Asserts MDPS source does NOT use inline timestamp-truncation bypasses
# (pd.Timestamp.floor / round / .replace(minute=0, ...) / polars dt.truncate).
# These bypass the canonical compute_bar_close_boundary() SSOT.
#
# Plan: available_at_lookahead_bias_completion_2026_05_08 Phase 0.7 Item 3.
# Pairs with MDPS@3836363 (Phase 0.7 Item 2: write-gate runtime enforcement).
#
# Per-line opt-out: `# noqa: bar-boundary-truncation`.
_BAR_BOUNDARY_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_mdps_bar_boundary_compliance.py"
if [ -f "$_BAR_BOUNDARY_CHECKER" ] && [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ]; then
    # Scope to MDPS / market-data-processing-service only (MDPS-specific contract)
    if [[ "$REPO" == "market-data-processing-service" ]] || [[ "$REPO" == "mdps" ]]; then
        if python3 "$_BAR_BOUNDARY_CHECKER" --source-dir "${SOURCE_DIR}"; then
            log_success "STEP 5.74: No bar-boundary truncation bypasses found"
        else
            log_fail "STEP 5.74: MDPS bar-boundary truncation bypass(es) found — use compute_bar_close_boundary() helper"
            V=$(( V + 1 ))
        fi
    else
        log_success "STEP 5.74: skipped (non-MDPS repo)"
    fi
else
    log_success "STEP 5.74: skipped (checker or SOURCE_DIR not provisioned)"
fi

# ── STEP 5.75: L1 — DataType enum mode-agnosticism ───────────────────────────
#
# batch=live architecture: DataType enum values must be mode-agnostic.
# No LIVE_/BATCH_ prefixed member names are permitted in any DataType enum
# class (e.g. LIVE_PRICE, BATCH_OHLCV are banned; PRICE, OHLCV are correct).
# Mode-specific behaviour is driven by RuntimeMode / the pipeline mode flag,
# NOT by separate per-mode DataType variants.
#
# Detection: grep for LIVE_/BATCH_ prefixed identifier assignments inside
# files that declare 'class DataType'. Pre-audit 2026-05-10 confirmed
# 0 violations workspace-wide; DAY-1 ENABLE.
#
# Opt-out line: # noqa: L1-mode-prefix (requires team-lead approval).
# Plan: batch_live_symmetry_2026_05_10.md Tab 3 L1.
if [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ]; then
    _L1_DT_FILES=$(rg -l --type py "^class DataType\b" "${SOURCE_DIR}/" 2>/dev/null || true)
    if [ -n "$_L1_DT_FILES" ]; then
        _L1_HITS=$(echo "$_L1_DT_FILES" | xargs rg -n "^\s+(LIVE_|BATCH_)[A-Z][A-Z0-9_]*\s*=" 2>/dev/null \
            | grep -v "# noqa: L1-mode-prefix" || true)
        if [ -n "$_L1_HITS" ]; then
            log_fail "STEP 5.75: LIVE_/BATCH_ prefixed DataType enum members found — DataType values must be mode-agnostic (batch_live_symmetry L1). Rename to mode-agnostic name; drive mode via RuntimeMode flag."
            printf "  %s\n" "$_L1_HITS"
            V=$(( V + 1 ))
        else
            log_success "STEP 5.75: DataType enum members are mode-agnostic (no LIVE_/BATCH_ prefixes)"
        fi
    else
        log_success "STEP 5.75: skipped (no DataType class in this service)"
    fi
else
    log_success "STEP 5.75: skipped (SOURCE_DIR not set or not a directory)"
fi

# ── STEP 5.76: L5 — No service-level DataType enum redeclarations ─────────────
#
# DataType enum lives exclusively in unified-api-contracts (UAC).
# No service or library is permitted to declare 'class DataType' locally.
# Services must import: from unified_api_contracts import DataType.
#
# UAC itself is exempt (canonical owner). Detection: grep for
# '^class DataType' in service Python source dirs.
# Pre-audit 2026-05-10 confirmed 0 violations workspace-wide; DAY-1 ENABLE.
#
# Plan: batch_live_symmetry_2026_05_10.md Tab 3 L5.
if [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ]; then
    if [[ "${REPO:-}" == "unified-api-contracts" ]]; then
        log_success "STEP 5.76: skipped (UAC is the canonical DataType owner)"
    else
        _L5_HITS=$(rg -n --type py "^class DataType\b" "${SOURCE_DIR}/" 2>/dev/null || true)
        if [ -n "$_L5_HITS" ]; then
            log_fail "STEP 5.76: Service-level DataType class declaration found — import from unified_api_contracts instead, never redeclare (batch_live_symmetry L5)."
            printf "  %s\n" "$_L5_HITS"
            V=$(( V + 1 ))
        else
            log_success "STEP 5.76: No service-level DataType redeclarations"
        fi
    fi
else
    log_success "STEP 5.76: skipped (SOURCE_DIR not set or not a directory)"
fi

# ── STEP 5.77: L2 — No mode comparisons outside CLI seam ─────────────────────
#
# Mode routing (batch vs live) must happen ONLY at the CLI entry point.
# Comparing mode strings deeper in the engine = separate code paths = L2 violation.
#
# Violation pattern: `mode == "batch"` / `mode == "live"` anywhere in non-CLI
# Python source. CLI files (matching *cli*.py / *main.py) are exempt — that IS
# the allowed seam. Lines annotated `# noqa: L2-mode-seam` are baselined known
# exceptions pending a design call.
#
# Known baselined exceptions as of 2026-05-14:
#   instruments-service/engine/orchestrator.py:1653,2072 — DeFi batch caching +
#   pre-genesis early-exit; design call pending per batch_live_symmetry Q3.
#
# Plan: batch_live_symmetry_2026_05_10.md Tab 3 L2.
if [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ]; then
    _L2_HITS=$(rg -n --type py \
        --glob '!**/cli/**' \
        --glob '!**/cli*.py' \
        --glob '!**/main.py' \
        -e '\bmode\s*==\s*"batch"' \
        -e '\bmode\s*==\s*"live"' \
        -e "\bmode\s*==\s*'batch'" \
        -e "\bmode\s*==\s*'live'" \
        "${SOURCE_DIR}/" 2>/dev/null \
        | grep -v '# noqa: L2-mode-seam' \
        || true)
    if [ -n "$_L2_HITS" ]; then
        log_fail "STEP 5.77: mode == \"batch\"/\"live\" comparison found outside CLI seam — mode routing must happen ONLY at the CLI entry point (batch_live_symmetry L2). Annotate with '# noqa: L2-mode-seam' ONLY for known exceptions with a design-call pending."
        printf "  %s\n" "$_L2_HITS"
        V=$(( V + 1 ))
    else
        log_success "STEP 5.77: No L2 mode comparisons outside CLI seam"
    fi
else
    log_success "STEP 5.77: skipped (SOURCE_DIR not set or not a directory)"
fi

# ── STEP 5.78: L3 — RuntimeMode declared once (UAC internal/modes.py) ─────────
#
# RuntimeMode is a T0 canonical type (unified-api-contracts, no dependencies).
# All other repos MUST re-export from UAC, never redeclare locally.
#
# Violation pattern: 'class RuntimeMode' outside unified-api-contracts.
# UAC is self-exempt (canonical owner). UTL is fixed (ebed394): re-exports
# from UAC. UI unified-internal-contracts deliberate copy pattern is DEFERRED
# (see batch_live_symmetry_2026_05_10.md Tab 3 L3).
#
# UAC QG skip: UAC is the canonical owner.
# UI QG skip: unified-trading-system-ui is a deliberate copy (deferred L3 fix).
# UTL QG: UTL now re-exports from UAC — this STEP confirms no regression.
#
# Plan: batch_live_symmetry_2026_05_10.md Tab 3 L3.
if [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ]; then
    if [[ "${REPO:-}" == "unified-api-contracts" ]] || [[ "${REPO:-}" == "unified-trading-system-ui" ]]; then
        log_success "STEP 5.78: skipped (${REPO} is exempt — canonical owner or deliberate-copy pattern)"
    else
        _L3_HITS=$(rg -n --type py "^class RuntimeMode\b" "${SOURCE_DIR}/" 2>/dev/null || true)
        if [ -n "$_L3_HITS" ]; then
            log_fail "STEP 5.78: Service-level RuntimeMode class declaration found — import from unified_api_contracts.internal.modes instead (batch_live_symmetry L3). Only UAC internal/modes.py may declare RuntimeMode."
            printf "  %s\n" "$_L3_HITS"
            V=$(( V + 1 ))
        else
            log_success "STEP 5.78: No local RuntimeMode redeclarations (re-exports UAC canonical)"
        fi
    fi
else
    log_success "STEP 5.78: skipped (SOURCE_DIR not set or not a directory)"
fi

# ── STEP 5.79: dockerfile-base-pin — production Dockerfiles must use @sha256:digest ─
#
# Every production-bound Dockerfile base image MUST be pinned to a digest
# (`@sha256:<hex>`) rather than a mutable `:tag` (including `:latest`).
# Tag-pinned images silently drift when the upstream image is re-tagged —
# the container you tested is NOT what runs in production after any registry update.
#
# Exemptions: `FROM scratch` (no registry image), `--platform` flag is stripped
# before checking, multi-stage alias re-references (`FROM build-stage AS ...`
# within the same file) are exempt.
#
# ARG-interpolated FROMs (NARROWED 2026-06-10 — closes the blanket `${` skip,
# plan dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md Phase 6):
#   - CONVERTED Dockerfile (carries a checked-in `ARG BASE_IMAGE_DIGEST=sha256:<hex>`
#     default) → enforce STRICTLY: every `${`-interpolated registry FROM must consume
#     the digest — `@${BASE_IMAGE_DIGEST}` inline (or a literal `@sha256:`), or be a
#     pure `${VAR}` reference whose `ARG VAR=` default embeds the digest
#     (instruments-service `${BASE_IMAGE}` shape).
#   - UNCONVERTED Dockerfile (still `:latest` + `${PROJECT_ID}`) → keep the legacy
#     skip but log_warn "ratchet pending rollout" — conversion is monotonic, no fleet
#     redness before add-dockerfile-digest-arg.py lands repo-by-repo.
#
# Date-gated ratchet: WARN before 2026-05-15, FAIL (exit 1) from 2026-05-15.
# Remediation: pin base images per Phase 5 (deployment_and_qg_strategy_implementation_2026_05_13.md)
# + convert via unified-trading-pm/scripts/propagation/add-dockerfile-digest-arg.py.
_RATCHET_579="2026-05-15"
_TODAY_579=$(date +%Y-%m-%d)
_DF_VIOLATIONS_579=()
while IFS= read -r -d '' _df_579; do
    _stage_aliases_579=()
    while IFS= read -r _line_579; do
        [[ "$_line_579" =~ ^[[:space:]]*FROM[[:space:]] ]] || continue
        _img_579=$(echo "$_line_579" | sed 's/^[[:space:]]*FROM[[:space:]]*//' | sed 's/[[:space:]]*--platform=[^[:space:]]*//' | awk '{print $1}')
        [[ "$_img_579" == "scratch" ]] && continue
        # Register multi-stage aliases (FROM x AS alias → alias is a local ref, not a registry image)
        # Anchor to end-of-line ($) so " as" prefix in registry hostnames (e.g. asia-northeast1-docker)
        # doesn't produce spurious matches with case-insensitive -i flag.
        _alias_579=$(echo "$_line_579" | grep -oi ' AS [a-z0-9_-]*$' | awk '{print $NF}' || true)
        [[ -n "$_alias_579" ]] && _stage_aliases_579+=("$_alias_579")
        # Skip if image is a known local stage alias
        _is_alias_579=0
        for _a_579 in "${_stage_aliases_579[@]:-}"; do
            [[ "$_img_579" == "$_a_579" ]] && _is_alias_579=1 && break
        done
        [[ "$_is_alias_579" -eq 1 ]] && continue
        # ARG-interpolated image (${...}): narrowed ratchet (2026-06-10) — strict for
        # converted Dockerfiles (ARG BASE_IMAGE_DIGEST=sha256: default present), legacy
        # skip + pending-rollout warn for unconverted ones (monotonic conversion).
        if [[ "$_img_579" == *'${'* ]]; then
            if grep -qE '^[[:space:]]*ARG[[:space:]]+BASE_IMAGE_DIGEST=sha256:[0-9a-f]{64}[[:space:]]*$' "$_df_579"; then
                _digest_ok_579=0
                if [[ "$_img_579" == *'@${BASE_IMAGE_DIGEST}'* ]] || [[ "$_img_579" == *"@sha256:"* ]]; then
                    # FROM consumes the digest inline.
                    _digest_ok_579=1
                else
                    # Pure ${VAR} reference (e.g. FROM ${BASE_IMAGE}) — accept when the
                    # ARG VAR= default embeds the digest (instruments-service shape).
                    _ref_re_579='^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$'
                    if [[ "$_img_579" =~ $_ref_re_579 ]]; then
                        _ref_579="${BASH_REMATCH[1]}"
                        if grep -E "^[[:space:]]*ARG[[:space:]]+${_ref_579}=" "$_df_579" \
                            | grep -qF '@${BASE_IMAGE_DIGEST}'; then
                            _digest_ok_579=1
                        fi
                    fi
                fi
                [[ "$_digest_ok_579" -eq 1 ]] || _DF_VIOLATIONS_579+=("$_df_579: $_line_579")
            else
                # HARD-FAIL (flipped 2026-06-10 — the final FROM-digest ratchet): the legacy
                # warn-only path is closed. Gate was operator-ratified to flip ONLY after a
                # REAL cloud build proved the @digest path end-to-end: proof = mtds build
                # fc2d4b07 SUCCESS through FROM @${BASE_IMAGE_DIGEST} with the digest-aware
                # pre-pull; all 16 consumer Dockerfiles converted (16/16 on LDR). Convert a
                # new/regressed Dockerfile via scripts/propagation/add-dockerfile-digest-arg.py.
                _DF_VIOLATIONS_579+=("$_df_579 (registry FROM without ARG BASE_IMAGE_DIGEST pin): $_line_579")
            fi
            continue
        fi
        [[ "$_img_579" == *"@sha256:"* ]] || _DF_VIOLATIONS_579+=("$_df_579: $_line_579")
    done < "$_df_579"
done < <(find . \( -name "Dockerfile" -o -name "Dockerfile.*" \) \
    -not -path "./.venv*/*" -not -path "./build/*" \
    -not -path "./node_modules/*" -not -path "./.git/*" \
    -print0 2>/dev/null)
if [ ${#_DF_VIOLATIONS_579[@]} -gt 0 ]; then
    if [[ "$_TODAY_579" < "$_RATCHET_579" ]]; then
        log_warn "STEP 5.79 [PENDING-RATCHET ${_RATCHET_579}]: dockerfile-base-pin — Dockerfiles using :tag instead of @sha256:digest (fails from ${_RATCHET_579}; remediate via Phase 5):"
        printf "    %s\n" "${_DF_VIOLATIONS_579[@]}"
    else
        log_fail "STEP 5.79: dockerfile-base-pin — production Dockerfile uses :tag instead of @sha256:digest (pin via Phase 5, deployment_and_qg_strategy_implementation_2026_05_13.md):"
        printf "    %s\n" "${_DF_VIOLATIONS_579[@]}"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.79: dockerfile-base-pin — all Dockerfiles use @sha256: digest pinning (or no Dockerfiles present)"
fi

# ── STEP 5.80: tarball-manifest-present — tarball uploads must write sibling manifest.json ─
#
# Every tarball upload by create-code-tarballs.sh MUST write a sibling
# `<repo>@<commit-sha>.manifest.json` containing repo, commit_sha, pyproject_version,
# git_status_clean, created_at, created_by. Without this manifest the VM boot-time
# commit-sha assertion has no source to compare against.
#
# Scope: deployment-service only (owns create-code-tarballs.sh). All other repos: skip.
#
# Date-gated ratchet: WARN before 2026-05-15, FAIL from 2026-05-15.
# Remediation: update create-code-tarballs.sh per Phase 3 (deployment_and_qg_strategy_implementation_2026_05_13.md).
_RATCHET_580="2026-05-15"
_TODAY_580=$(date +%Y-%m-%d)
_TARBALL_SH_580="scripts/vm/create-code-tarballs.sh"
if [ "${REPO:-}" = "deployment-service" ]; then
    if [ -f "$_TARBALL_SH_580" ]; then
        if grep -q "manifest\.json" "$_TARBALL_SH_580" 2>/dev/null; then
            log_success "STEP 5.80: tarball-manifest-present — create-code-tarballs.sh writes sibling manifest.json"
        else
            if [[ "$_TODAY_580" < "$_RATCHET_580" ]]; then
                log_warn "STEP 5.80 [PENDING-RATCHET ${_RATCHET_580}]: tarball-manifest-present — create-code-tarballs.sh does not write sibling manifest.json (fails from ${_RATCHET_580}; remediate via Phase 3)"
            else
                log_fail "STEP 5.80: tarball-manifest-present — create-code-tarballs.sh missing sibling manifest.json write. Add per Phase 3 (deployment_and_qg_strategy_implementation_2026_05_13.md)."
                V=$(( V + 1 ))
            fi
        fi
    else
        log_success "STEP 5.80: tarball-manifest-present — skipped (create-code-tarballs.sh not found in deployment-service)"
    fi
else
    log_success "STEP 5.80: tarball-manifest-present — skipped (${REPO:-unknown}: not deployment-service)"
fi

# ── STEP 5.81: tarball-env-block — deployment-api must gate staging/prod tarball uploads ─
#
# deployment-api MUST reject tarball-deploy requests for staging/prod environments
# unless an explicit override flag is present. Without this gate, an operator can
# accidentally promote an untested tarball straight to production.
#
# Check: deployment-api Python source must reference DEPLOYMENT_ENV check alongside
# tarball-related code, or carry an explicit env-tier override guard.
#
# Scope: deployment-api only. All other repos: skip.
#
# Date-gated ratchet: WARN before 2026-05-17, FAIL from 2026-05-17.
# Remediation: wire env-tier override guard per Phase 1 (deployment_and_qg_strategy_implementation_2026_05_13.md).
_RATCHET_581="2026-05-17"
_TODAY_581=$(date +%Y-%m-%d)
if [ "${REPO:-}" = "deployment-api" ] && [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ]; then
    _HAS_TARBALL_581=$(grep -rl "tarball\|TARBALL\|TarballDeploy\|tarball_deploy" "${SOURCE_DIR}/" --include="*.py" 2>/dev/null || true)
    if [ -n "$_HAS_TARBALL_581" ]; then
        _HAS_ENV_BLOCK_581=$(grep -rl "DEPLOYMENT_ENV\|deployment_env\|staging_override\|prod_override\|allow_tarball\|tarball_override\|env_tier_check" "${SOURCE_DIR}/" --include="*.py" 2>/dev/null || true)
        if [ -n "$_HAS_ENV_BLOCK_581" ]; then
            log_success "STEP 5.81: tarball-env-block — deployment-api has env-tier guard for staging/prod tarball uploads"
        else
            if [[ "$_TODAY_581" < "$_RATCHET_581" ]]; then
                log_warn "STEP 5.81 [PENDING-RATCHET ${_RATCHET_581}]: tarball-env-block — deployment-api has tarball code but no env-tier block for staging/prod (fails from ${_RATCHET_581}; remediate via Phase 1)"
            else
                log_fail "STEP 5.81: tarball-env-block — deployment-api allows tarball uploads without staging/prod env-tier guard. Wire DEPLOYMENT_ENV check per Phase 1 (deployment_and_qg_strategy_implementation_2026_05_13.md)."
                V=$(( V + 1 ))
            fi
        fi
    else
        log_success "STEP 5.81: tarball-env-block — skipped (no tarball-related code found in deployment-api source)"
    fi
else
    log_success "STEP 5.81: tarball-env-block — skipped (${REPO:-unknown}: not deployment-api or SOURCE_DIR absent)"
fi

# ── STEP 5.82: image-build-on-staging-merge — staging merges must trigger cloud-build ─
#
# Every merge to the staging branch MUST trigger a cloud-build image build so
# the image exists in Artifact Registry before the staging deploy runs. Without this,
# staging deploys use a stale image from the previous cycle — silently wrong.
#
# Check: if .github/workflows/ contains a staging-branch push trigger, a corresponding
# cloud-build / gcloud builds invocation must also be present in the same workflow dir.
#
# Date-gated ratchet: WARN before 2026-05-17, FAIL from 2026-05-17.
# Remediation: wire cloud-build trigger on staging push per Phase 5 (deployment_and_qg_strategy_implementation_2026_05_13.md).
_RATCHET_582="2026-05-17"
_TODAY_582=$(date +%Y-%m-%d)
if [ -d ".github/workflows" ]; then
    _HAS_STAGING_582=$(grep -rl "staging" .github/workflows/ 2>/dev/null || true)
    _HAS_BUILD_582=$(grep -rl "cloudbuild\|cloud-build\|gcloud builds\|google-github-actions/deploy-cloudrun\|buildTrigger" .github/workflows/ 2>/dev/null || true)
    if [ -n "$_HAS_STAGING_582" ] && [ -z "$_HAS_BUILD_582" ]; then
        if [[ "$_TODAY_582" < "$_RATCHET_582" ]]; then
            log_warn "STEP 5.82 [PENDING-RATCHET ${_RATCHET_582}]: image-build-on-staging-merge — staging workflow present but no cloud-build trigger found (fails from ${_RATCHET_582}; remediate via Phase 5)"
        else
            log_fail "STEP 5.82: image-build-on-staging-merge — staging branch workflow does not trigger cloud-build. Wire image-build trigger per Phase 5 (deployment_and_qg_strategy_implementation_2026_05_13.md)."
            V=$(( V + 1 ))
        fi
    else
        log_success "STEP 5.82: image-build-on-staging-merge — OK (cloud-build trigger present or no staging workflow)"
    fi
else
    log_success "STEP 5.82: image-build-on-staging-merge — skipped (no .github/workflows/)"
fi

# ── STEP 5.83: UAC hard-required field validation regression guard ─────────────
#
# Two-part check (hard_schema_enforcement_2026_05_08.md Phase 5):
#
# (a) UAC regression guard: asserts that validate_instrument_records() + the
#     3 closed-set per-rule landmarks are still present in
#     unified_api_contracts/internal/reference/instrument_validation.py.
#     Guards against silent removal of the hard-required enforcement logic
#     shipped in uac@37d1ddb.  Phase 1 nullable→required field flips are still
#     pending; this check ensures the RUNTIME validator is not regressed before
#     those static flips land.
#
# (b) Bundled-shard key kwargs: every literal
#     record_captured(data_type="<bundled_type>", …) call in SOURCE_DIR MUST
#     include the required shard-key kwarg:
#       options_chain                       → options_chain=
#       futures_chain                       → chain=
#       prediction_canonical_question_group → canonical_question_group=
#       sports_fixture_bundle               → fixture_id=
#     Complements UTL MalformedRowKeyError (UTL@0caa08e3) with STATIC coverage.
#     Inline opt-out: # QG-allow: shard-key-not-applicable
#
# Note: 5.66 is reserved (launcher-script multi-process-isolation), 5.68 is
# reserved (available_at lookahead callsite check) — so this manifest-
# correctness ratchet lands at 5.83 (after 5.82 image-build-on-staging-merge).
# SSOT: plans/active/hard_schema_enforcement_2026_05_08.md Phase 5.
_UAC_HARD_FIELD_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_uac_hard_required_fields.py"
if [ -f "$_UAC_HARD_FIELD_CHECKER" ]; then
    _UHF_REPO=$(basename "$PROJECT_ROOT")
    _UHF_WS="$REPO_ROOT"
    _UHF_SRC_ARG=()
    [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ] && _UHF_SRC_ARG=(--source-dir "$SOURCE_DIR")
    if $PYTHON_CMD "$_UAC_HARD_FIELD_CHECKER" \
            --workspace-root "$_UHF_WS" --scope "$_UHF_REPO" "${_UHF_SRC_ARG[@]}" >/tmp/uac_hard_required_fields_qg.log 2>&1; then
        if grep -q '^\[FAIL\]' /tmp/uac_hard_required_fields_qg.log 2>/dev/null; then
            log_fail "STEP 5.83: UAC hard-required field regression or bundled-shard key kwarg missing:"
            cat /tmp/uac_hard_required_fields_qg.log
            log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_uac_hard_required_fields.py --workspace-root $_UHF_WS --scope $_UHF_REPO"
            V=$(( V + 1 ))
        else
            log_success "STEP 5.83: UAC hard-required field validation landmarks present + bundled-shard key kwargs OK"
        fi
    else
        log_fail "STEP 5.83: UAC hard-required field check FAILED (validation regression or bundled-shard key kwarg missing):"
        cat /tmp/uac_hard_required_fields_qg.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_uac_hard_required_fields.py --workspace-root $_UHF_WS --scope $_UHF_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.83: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# ── STEP 5.84: no-inline-coverage-formula — detect bespoke coverage ratio calcs ─
#
# Any re-implementation of compute_honest_coverage() numerator/denominator in
# service source (not in honest_coverage.py itself) fails this gate.
# SSOT: plans/active/honest_coverage_formula_consolidation_2026_05_19.md Phase 6.
# Script: unified-trading-pm/scripts/qg/no_inline_coverage_formula.sh
_INLINE_COVERAGE_LINTER="${REPO_ROOT}/unified-trading-pm/scripts/qg/no_inline_coverage_formula.sh"
if [ -f "$_INLINE_COVERAGE_LINTER" ] && [ -n "${SOURCE_DIR:-}" ]; then
    if bash "$_INLINE_COVERAGE_LINTER" "$REPO_ROOT" 2>/tmp/inline_coverage_qg.log; then
        log_success "STEP 5.84: no-inline-coverage-formula — no bespoke coverage formula re-implementations"
    else
        log_fail "STEP 5.84: no-inline-coverage-formula — bespoke coverage formula detected (use compute_honest_coverage() from UAC):"
        cat /tmp/inline_coverage_qg.log
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.84: no-inline-coverage-formula — skipped (script absent or SOURCE_DIR not set)"
fi

# ── STEP 5.85: no inline string literal pipeline_mode values in service source ─
#
# Inline string literals like pipeline_mode="batch_tardis" in record_*() call-sites
# bypass the PipelineMode enum type-check and can silently produce stale / typo'd
# values. All service-code pipeline_mode= kwargs MUST use PipelineMode.<MEMBER>
# or a call to resolve_pipeline_mode() — not a raw string literal.
#
# Test files are excluded (readers + test helpers legitimately filter by string).
#
# The matched quote MUST be followed by a VALUE char ([A-Za-z0-9_{]) so this only
# flags genuine value ASSIGNMENTS (pipeline_mode="batch_tardis" /
# pipeline_mode="{pm}") — NOT path-segment string CONSTANTS where pipeline_mode=
# is the tail of a quoted GCS path key and the matched quote is the CLOSING quote
# (e.g. `"/pipeline_mode=" in rel`, `f"day=x/pipeline_mode="`, `"pipeline_mode="
# not in obj`). Those are legitimate partition-path membership checks in the
# canonicalisation migrators (slots 2-6) + audit tools — there is no PipelineMode
# enum that helps match a substring, so flagging them was a pure false-positive
# that red-blocked every MTDS QG fleet-wide once the migrators landed (2026-06-08;
# verified 0 genuine value-literal violations in any service source, only a UAC
# docstring example caught identically before+after). Narrowing un-catches nothing
# real (a real `pipeline_mode="<value>"` still has a value char after the quote).
#
# Escape hatch: add '# QG-allow: pipeline-mode-string-literal' on the line.
#
# Plan: pipeline_mode_implementation_2026_05_28.md Phase 2.3.
# SSOT: resolve_pipeline_mode() in unified_trading_library.pipeline_mode_resolver.
if [ -n "${SOURCE_DIR:-}" ] && [ -d "$SOURCE_DIR" ]; then
    _PM_STR_HITS=$(grep -rn 'pipeline_mode\s*=\s*["'"'"'][A-Za-z0-9_{]' "$SOURCE_DIR" \
        --include="*.py" --exclude-dir=tests --exclude='test_*.py' --exclude='*_test.py' \
        | grep -v '# QG-allow: pipeline-mode-string-literal' || true)
    if [ -n "$_PM_STR_HITS" ]; then
        log_fail "STEP 5.85: no-inline-pipeline-mode-string-literal — raw string literal pipeline_mode= value in service source. Use PipelineMode.<MEMBER> or resolve_pipeline_mode():"
        echo "$_PM_STR_HITS"
        V=$(( V + 1 ))
    else
        log_success "STEP 5.85: no-inline-pipeline-mode-string-literal — no raw string pipeline_mode values in service source"
    fi
else
    log_success "STEP 5.85: no-inline-pipeline-mode-string-literal — skipped (SOURCE_DIR not set)"
fi

# ── STEP 5.86: fleet-wide SOURCE_RETURNED_ZERO routing ratchet (A10c-fleet) ────
#
# Generalises the DeFi-MTDS-only A10c check (scripts/qg/no_unrouted_source_returned_zero.sh,
# zero-tolerance, DeFi handlers only) to EVERY service / asset_group: a "source succeeded,
# zero rows" shard MUST route through the generic UTL ManifestWriter.record_zero_rows(...)
# (plan §A10b) — which sends a genuinely-empty shard to empty_confirmed but a shard the per-AG
# expected-universe oracle (UAC was_instrument_alive / a sports fixture lookup) says SHOULD have
# had data to attempted_failed — instead of a raw record_empty(reason=SOURCE_RETURNED_ZERO) that
# masks the fetch failure as honest absence.
#
# Baselined GRIND-DOWN ratchet (model: STEP 5.70 + check_adapter_contract_regression.py): every
# pre-migration unrouted callsite is in unrouted_source_returned_zero_baseline.yaml → it WARNs
# (exit-clean) until its AG-slot migrates it; a NEW unrouted callsite (or a non-baselined file
# with one) FAILS. As each AG migrates, re-run with --regenerate-baseline to LOCK the lower count.
# A genuinely-typed-reason callsite where record_zero_rows does not apply (service-output /
# computed output / pipeline-mode-not-applicable) gets an inline '# QG-allow: <reason>' marker.
#
# SSOT: defi_manifest_canonicalisation_2026_06_01.md §A10c-fleet
#       (+ each AG's *_manifest_canonicalisation_2026_06_01.md migration todo).
_SRZ_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_unrouted_source_returned_zero.py"
if [ -f "$_SRZ_CHECKER" ]; then
    # Slot-worktree-aware: scope=this repo's dir; workspace-root=REPO_ROOT (== workspace root per
    # qg-common.sh). Same shape as STEP 5.70.
    _SRZ_REPO=$(basename "$PROJECT_ROOT")
    if $PYTHON_CMD "$_SRZ_CHECKER" \
            --workspace-root "$REPO_ROOT" --scope "$_SRZ_REPO" >/tmp/unrouted_srz_qg.log 2>&1; then
        if grep -q '^\[WARN\]' /tmp/unrouted_srz_qg.log 2>/dev/null; then
            log_warn "STEP 5.86: $(grep -c '^\[WARN\]' /tmp/unrouted_srz_qg.log) baselined unrouted SOURCE_RETURNED_ZERO callsite(s) pending A10c-fleet migration; 0 new"
        else
            log_success "STEP 5.86: every zero-rows shard routes through record_zero_rows (or carries # QG-allow:)"
        fi
    else
        log_fail "STEP 5.86: NEW unrouted record_empty(SOURCE_RETURNED_ZERO) callsite — route via ManifestWriter.record_zero_rows(was_expected=<oracle>, ...) or add inline '# QG-allow: <reason>' (A10c-fleet):"
        cat /tmp/unrouted_srz_qg.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_unrouted_source_returned_zero.py --workspace-root $REPO_ROOT --scope $_SRZ_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.86: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# ── STEP 5.89: record_empty/record_expected_empty reason closed-set ───────────
#
# Every ``record_empty(reason=...)`` / ``record_expected_empty(reason=...)`` call
# that passes a literal string ``reason=`` kwarg must use a value from
# ``unified_api_contracts.canonical.crosscutting.honest_coverage.EMPTY_CONFIRMED_REASONS``.
#
# UTL's ManifestWriter already raises UnknownEmptyConfirmedReasonError at runtime,
# but this static check catches the error before tests run with precise file:line.
#
# Attribute-access forms (EmptyConfirmedReason.X, SomeEnum.X.value) pass through —
# they are validated by the type system. Only literal strings are checked.
#
# Exemptions: manifest_writer.py (UTL definition site), test_*.py (negative tests),
# per-line ``# QG-allow: record-empty-reason``.
#
# SSOT: writegate_honest_coverage_endtoend_2026_05_06.md Phase 2.E.1 / STEP 5.89.
_RECORD_EMPTY_REASON_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_record_empty_reason_closed_set.py"
if [ -f "$_RECORD_EMPTY_REASON_CHECKER" ]; then
    _RER_REPO=$(basename "$PROJECT_ROOT")
    _RER_WS="$REPO_ROOT"
    _RER_SRC_ARG=()
    [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ] && _RER_SRC_ARG=(--source-dir "$SOURCE_DIR")
    if $PYTHON_CMD "$_RECORD_EMPTY_REASON_CHECKER" \
            --workspace-root "$_RER_WS" --scope "$_RER_REPO" "${_RER_SRC_ARG[@]}" >/tmp/record_empty_reason_qg.log 2>&1; then
        log_success "STEP 5.89: All record_empty/record_expected_empty literal reasons are in EMPTY_CONFIRMED_REASONS"
    else
        log_fail "STEP 5.89: record_empty/record_expected_empty called with unknown/blank literal reason. Use EmptyConfirmedReason enum member or a known string from EMPTY_CONFIRMED_REASONS (writegate Phase 2.E.1):"
        cat /tmp/record_empty_reason_qg.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_record_empty_reason_closed_set.py --workspace-root $_RER_WS --scope $_RER_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.89: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# ── STEP 5.90: GET /data-status endpoint must use canonical coverage helper ───
#
# Every Python file that defines a GET /data-status route MUST import
# compute_coverage_for_bucket (UTL) or compute_honest_coverage (UAC).
# Inline re-implementations of the manifest read or the coverage formula are
# review-blocking per codex/06-coding-standards/data-status-endpoint-contract.md.
#
# SSOT: honest_coverage_formula_consolidation_2026_05_19.md Phase 1 P1 / STEP 5.90.
_DS_CANONICAL_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_data_status_endpoint_canonical.sh"
if [ -f "$_DS_CANONICAL_CHECKER" ] && [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ]; then
    if bash "$_DS_CANONICAL_CHECKER" "$SOURCE_DIR" >/tmp/data_status_canonical_qg.log 2>&1; then
        log_success "STEP 5.90: GET /data-status endpoint uses compute_coverage_for_bucket or compute_honest_coverage"
    else
        log_fail "STEP 5.90: GET /data-status route file does not use canonical coverage helper (see codex/06-coding-standards/data-status-endpoint-contract.md):"
        cat /tmp/data_status_canonical_qg.log
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.90: skipped (checker absent or SOURCE_DIR not set)"
fi

# ── STEP 5.91: entity-registry CI gate ───────────────────────────────────────
#
# Any commit that adds/removes values from entity-registry constants
# (DATA_TYPES_BY_ASSET_GROUP / VENUES_BY_ASSET_GROUP / PROTOCOL_LAUNCH_DATES /
# LST_TOKEN_GENESIS / PREDICTION_GROUPS / *_LAUNCH_DATES / *_GENESIS_DATES)
# MUST include a CSV path under unified-trading-pm/audits/entity_lifecycle/
# in the commit body OR an [entity-skip-cleanup] tag with operator reason.
#
# SSOT: plans/epics/infrastructure_master.md "Manifest cleanup HARD RULE" section.
# Script: scripts/lifecycle/entity-lifecycle-cleanup.sh
_ENTITY_REGISTRY_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_entity_registry_cleanup.py"
if [ -f "$_ENTITY_REGISTRY_CHECKER" ] && [ -n "${REPO_ROOT:-}" ] && [ -d "${REPO_ROOT}" ]; then
    if python3 "$_ENTITY_REGISTRY_CHECKER" "$REPO_ROOT" >/tmp/entity_registry_qg.log 2>&1; then
        cat /tmp/entity_registry_qg.log
        log_success "STEP 5.91: Entity-registry cleanup evidence check passed"
    else
        log_fail "STEP 5.91: Entity-registry change without cleanup evidence — see instructions:"
        cat /tmp/entity_registry_qg.log
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.91: skipped (checker absent or REPO_ROOT not set)"
fi

# ── STEP 5.92: bar-edge open-edge (left) ingestion detector ───────────────────
#
# A CLOSED OHLCV candle MUST be timestamped on its RIGHT (close) edge. Stamping
# the vendor bar-START (open/left) edge is look-ahead → leakage, and the MDPS
# bar-boundary gate (STEP 5.74) does NOT catch a uniform one-interval left shift
# (it stays grid-aligned). This AST gate flags an ingestion/adapter function
# that consumes a vendor bar-START field (periodStartUnix / openTimestamp / a
# candle-fn "t" key) WITHOUT a close conversion (compute_bar_close_boundary /
# vendor close field). SHRINKING ratchet: `bar_edge_open_ingestion_baseline.yaml`
# entries are WARNINGS (exit-clean); a NEW open-edge site fails CI. Escape:
# `# noqa: bar-boundary-open-edge`.
#
# SSOT: bar_edge_left_vs_right_remediation_2026_06_08.md Phase 0 +
# audit_criteria_automation_2026_06_08.md Tier-2.
_BAR_EDGE_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_bar_edge_open_ingestion.py"
if [ -f "$_BAR_EDGE_CHECKER" ]; then
    _BE_REPO=$(basename "$PROJECT_ROOT")
    _BE_WS="$REPO_ROOT"
    _BE_SRC_ARG=()
    [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ] && _BE_SRC_ARG=(--source-dir "$SOURCE_DIR")
    if $PYTHON_CMD "$_BAR_EDGE_CHECKER" \
            --workspace-root "$_BE_WS" --scope "$_BE_REPO" "${_BE_SRC_ARG[@]}" >/tmp/bar_edge_open_ingestion_qg.log 2>&1; then
        if grep -q '^\[WARN\]' /tmp/bar_edge_open_ingestion_qg.log 2>/dev/null; then
            log_warn "STEP 5.92: $(grep -c '^\[WARN\]' /tmp/bar_edge_open_ingestion_qg.log) baselined latent open-edge ingestion site(s); 0 new"
        else
            log_success "STEP 5.92: No open-edge (left) bar ingestion — closed candles stamped on the right/close edge"
        fi
    else
        log_fail "STEP 5.92: NEW open-edge (left) bar ingestion site (not in unified-trading-pm/scripts/quality_gates/bar_edge_open_ingestion_baseline.yaml). Use the vendor close field or compute_bar_close_boundary(open_ts, timeframe) → t_close (bar_edge_left_vs_right_remediation_2026_06_08.md):"
        cat /tmp/bar_edge_open_ingestion_qg.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_bar_edge_open_ingestion.py --workspace-root $_BE_WS --scope $_BE_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.92: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# ── STEP 5.93: canonical data-model regression detector ───────────────────────
#
# AST gate for two recurring canonicalisation regressions: (a) coarse
# `pipeline_mode = "batch"/"live"` stamps (canonical is source-aware
# `batch_<source>`); (b) exact-coarse reader path probes `pipeline_mode=batch/`
# (readers MUST prefix-match `batch_*`). (There is deliberately NO
# data_type=options_chain check — that literal is a legitimate Era-B snapshot
# data_type, name-collided with the instrument_type; Era-A is a runtime
# _LEGAL_DATA_TYPES concern.) Docstrings + the blank-sentinel `pipeline_mode=""`
# are excluded. SHRINKING ratchet:
# `canonical_model_regressions_baseline.yaml` entries are WARNINGS; a NEW one
# fails CI. Escape: `# QG-allow: canonical-model-regression`.
#
# SSOT: audit_criteria_automation_2026_06_08.md Tier-2 +
# master_data_canonicalisation_migration_catalogue_2026_06_07.md (the C-PATH /
# pipeline_mode source-aware + Era-B model).
_CANON_MODEL_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_canonical_model_regressions.py"
if [ -f "$_CANON_MODEL_CHECKER" ]; then
    _CM_REPO=$(basename "$PROJECT_ROOT")
    _CM_WS="$REPO_ROOT"
    _CM_SRC_ARG=()
    [ -n "${SOURCE_DIR:-}" ] && [ -d "${SOURCE_DIR}" ] && _CM_SRC_ARG=(--source-dir "$SOURCE_DIR")
    if $PYTHON_CMD "$_CANON_MODEL_CHECKER" \
            --workspace-root "$_CM_WS" --scope "$_CM_REPO" "${_CM_SRC_ARG[@]}" >/tmp/canonical_model_regressions_qg.log 2>&1; then
        if grep -q '^\[WARN\]' /tmp/canonical_model_regressions_qg.log 2>/dev/null; then
            log_warn "STEP 5.93: $(grep -c '^\[WARN\]' /tmp/canonical_model_regressions_qg.log) baselined canonical-model occurrence(s); 0 new"
        else
            log_success "STEP 5.93: No coarse pipeline_mode / exact-coarse reader / Era-A chain-write regressions"
        fi
    else
        log_fail "STEP 5.93: NEW canonical-model regression (not in unified-trading-pm/scripts/quality_gates/canonical_model_regressions_baseline.yaml). Use source-aware batch_<source> / prefix-match readers / Era-B data_type=trades for chains:"
        cat /tmp/canonical_model_regressions_qg.log
        log_fail "         Recheck: $PYTHON_CMD unified-trading-pm/scripts/quality_gates/check_canonical_model_regressions.py --workspace-root $_CM_WS --scope $_CM_REPO"
        V=$(( V + 1 ))
    fi
else
    log_success "STEP 5.93: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# ── [6] PRODUCTION READINESS (informational) ──────────────────────────────────
log_section "[6/6] PRODUCTION READINESS VALIDATORS"
# SSOT: unified-trading-pm/codex/scripts (not a separate unified-trading-codex clone)
VSCRIPT="${REPO_ROOT}/unified-trading-pm/codex/scripts/run-all-validators.sh"
if [ -f "$VSCRIPT" ]; then
    if ! "$VSCRIPT" --asset-group all --failed-only; then
        log_fail "Production readiness validators FAILED — fix unified-trading-pm/workspace-manifest.json and plans/active/*.md (run: python3 unified-trading-pm/scripts/run_validators.py --scope all)"
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
    if act -j quality-gates -W .github/workflows/quality-gates.yml --container-architecture linux/amd64 ${ACT_SECRETS_ARG} 2>&1 | tee "$_ACT_LOG"; then
        log_ok "Act simulation PASSED"
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
MAX_DURATION=${MAX_DURATION:-300}
QG_END=$(date +%s); DUR=$((QG_END - QG_START))

# ── 2× RESOURCE-DRIFT GUARD (qg-perrepo-baseline) ─────────────────────────────
# WARN (never fail) when this run's wall-clock exceeds 2× the committed per-repo
# baseline — an early signal of a resource regression during code-freeze. Keyed by
# repo folder name in qg_resource_baseline.json (local side). Fully defensive.
_QG_BASELINE="${REPO_ROOT}/unified-trading-pm/scripts/dev/qg_resource_baseline.json"
if [ -f "$_QG_BASELINE" ] && command -v python3 >/dev/null 2>&1; then
    _qg_repo_key="$(basename "$PROJECT_ROOT")"
    _base_wall="$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get(sys.argv[2],{}).get('local',{}).get('wall_s',0))" "$_QG_BASELINE" "$_qg_repo_key" 2>/dev/null || echo 0)"
    if awk "BEGIN{exit !(${_base_wall:-0}>0 && ${DUR:-0} > 2*${_base_wall:-0})}" 2>/dev/null; then
        log_warn "Resource drift: wall ${DUR}s > 2× baseline ${_base_wall}s for ${_qg_repo_key} (qg_resource_baseline.json) — investigate before merge"
    fi
fi

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

echo -e "\n${GREEN}======================================================================"
echo -e "✅ ALL QUALITY GATES PASSED (${DUR}s)${NC}"

# ── QG SENTINEL (SHA fingerprint for quickmerge --agent fast-path) ────────────
# Only written on a COMPLETE run (no skip flags). Partial runs (--skip-tests,
# --skip-lint, --quick, --lint-only, --skip-codex) must NOT write the sentinel
# because they do not verify the full gate surface.
#
# SENTINEL CONTRACT (HARD, operator-ratified 2026-06-10): `.qg_last_passed_sha` means
# "a COMPLETE green gate ran on this HEAD" — it is what `quickmerge --agent` ships on.
# ANY partial-surface mode must be excluded here: QG_SLICE (CI parallel slices) and the
# future change-scoped fast tier (QG_FAST — quality_gates_speed Phase 2). The fast tier
# gets its OWN `.qg_fast_sentinel` + an explicit quickmerge policy; it must NEVER write
# this file, or partial gates silently dissolve the commit-quality boundary.
if [[ "${RUN_TESTS}" == "true" ]] && \
   [[ "${RUN_LINT}" == "true" ]] && \
   [[ "${QUICK_MODE}" == "false" ]] && \
   [[ "${ACT_MODE}" == "false" ]] && \
   [[ -z "${QG_SLICE:-}" ]] && \
   [[ -z "${QG_FAST:-}" ]] && \
   [[ -z "${SKIP_CODEX_FLAG:-}" ]]; then
    # Write to PROJECT_ROOT (the gated repo's root — same dir the content sentinel below
    # uses), NOT REPO_ROOT: qg-common.sh resolves REPO_ROOT to PROJECT_ROOT/.. (the WORKSPACE
    # parent), so writing there put .qg_last_passed_sha one level above the repo where
    # `quickmerge --agent` reads it (CWD = repo root) → the agent fast-path always saw it
    # "missing" and hard-refused, fleet-wide.
    #
    # H5: do NOT refresh the SHA sentinel on a content-sentinel HIT — a HIT skipped the
    # tests/typecheck phases (the content hash omits cross-repo dep state), so refreshing
    # `.qg_last_passed_sha = HEAD` would let `quickmerge --agent` ship a repo whose deps
    # changed underneath without actually re-running its tests. On a HIT, keep the prior
    # full-run SHA sentinel: if HEAD is unchanged it still certifies a real test pass; if
    # HEAD moved (e.g. a sentinel/coverage-only commit), the SHA mismatch correctly forces
    # a full QG at quickmerge time. The content sentinel below is unaffected (it IS the HIT).
    if [ "${_QG_SENTINEL_HIT:-false}" != true ]; then
        git rev-parse HEAD > "${PROJECT_ROOT}/.qg_last_passed_sha" 2>/dev/null && \
            echo "Sentinel written: .qg_last_passed_sha=$(cat "${PROJECT_ROOT}/.qg_last_passed_sha")" || \
            echo "Warning: could not write .qg_last_passed_sha (non-git dir?)"
    else
        echo "SHA sentinel NOT refreshed (content-sentinel HIT → tests skipped; prior full-run SHA sentinel retained)."
    fi
    # Green content sentinel (qg-repo-green-sentinel): record the content hash so an
    # unchanged tree skips the heavy phases next run. Only here — a COMPLETE green run
    # (this block) — so the sentinel always represents a coverage-inclusive pass.
    if [ "${#_QG_CONTENT_HASH}" -eq 64 ]; then
        echo "$_QG_CONTENT_HASH" > "${PROJECT_ROOT}/.qg_content_sentinel" 2>/dev/null \
            && echo "Green sentinel written: .qg_content_sentinel (unchanged tree → fast green next run)" || true
    fi
else
    echo "Sentinel NOT written — partial run detected (skip flags active). Run full quality-gates.sh to enable quickmerge --agent fast-path."
fi
