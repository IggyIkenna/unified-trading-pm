#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
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
#   PYTEST_WORKERS         — explicit worker count override; default is max(1, cpu_count // 4)
#   PYTEST_TIMEOUT_SECONDS — per-test wall-clock timeout override; default 150
#   PYTEST_TIMEOUT_RETRIES — retries on timeout-only pytest failures (xdist-contention flake
#                            class; serial re-run); 0 disables; default 1
#   LOCAL_DEPS             — array of sibling repo names to install locally
#   MAX_DURATION           — duration limit in seconds (default: 300)
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
# TOTAL-INSTANCE gate (mirror of base-service.sh) — bounds ALL concurrent
# quality-gates.sh processes host-wide, not just the heavy phases below. See
# qg-host-governor.sh's header for the full rationale (scope gap found investigating
# plans/active/issues/review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md).
# Acquired for the WHOLE run; released from the EXIT trap below.
qg_governor_acquire_total_instance
export OMP_NUM_THREADS="${QG_THREAD_CAP:-2}" OPENBLAS_NUM_THREADS="${QG_THREAD_CAP:-2}" \
       MKL_NUM_THREADS="${QG_THREAD_CAP:-2}" NUMEXPR_NUM_THREADS="${QG_THREAD_CAP:-2}"
export RUFF_CACHE_DIR="${RUFF_CACHE_DIR:-${TMPDIR:-/tmp}/qg-ruff-cache}"
# Green sentinel content hash (see base-service.sh for the full rationale).
_qg_content_hash() {
    {
        git rev-parse HEAD 2>/dev/null || echo no-head
        git diff HEAD 2>/dev/null
        git ls-files --others --exclude-standard 2>/dev/null \
            | grep -vE '(^|/)(\.qg_content_sentinel|\.qg_last_passed_sha|\.qg_cache/|coverage\.xml|\.coverage|\.pytest_cache/|\.ruff_cache/|__pycache__/)' \
            | sort | while IFS= read -r _f; do [ -f "$_f" ] && sha256sum "$_f" 2>/dev/null; done
        sha256sum "${BASH_SOURCE[0]}" "${BASH_SOURCE[0]%/*}/qg-host-governor.sh" 2>/dev/null
        "${RUFF_CMD:-ruff}" --version 2>/dev/null
        "${BASEDPYRIGHT_CMD:-basedpyright}" --version 2>/dev/null
        "${PYTHON_CMD:-python3}" --version 2>/dev/null
        _qg_editable_sibling_hash                                        # workspace sibling deps (qg-common.sh)
        # gate-affecting config (qg_sentinel_environment_blind_2026_07_23.md item 2):
        # see base-service.sh for the full rationale — a byte-identical tree verified
        # under a different ENVIRONMENT/DEPLOYMENT_ENV is not the same verified surface.
        printf 'ENVIRONMENT=%s DEPLOYMENT_ENV=%s\n' "${ENVIRONMENT:-}" "${DEPLOYMENT_ENV:-}"
    } | sha256sum | awk '{print $1}'
}

# ── TRAP: release the host governor(s) + set ci_status=FAILING on non-zero exit ──
# Covers every exit path (the happy-path heavy-phase release near the bottom of this
# file only runs after TYPECHECK; a run that fails/aborts before that would otherwise
# leak a token/reservation until the next acquirer's sweep — mirror of base-service.sh's
# own trap fix). Idempotent: both release functions guard on their own held-state var.
_qg_exit_handler() {
    local rc=$?
    if command -v qg_governor_release >/dev/null 2>&1; then qg_governor_release 2>/dev/null || true; fi
    if command -v qg_governor_release_total_instance >/dev/null 2>&1; then qg_governor_release_total_instance 2>/dev/null || true; fi
    [ "$rc" -ne 0 ] && _qg_update_ci_status_failing 2>/dev/null || true
}
trap '_qg_exit_handler' EXIT

# ── SIGNAL TRAP: loud "killed" marker on a genuinely-CAUGHT kill signal ──
# Mirror of base-service.sh's own signal trap (see that file for the full rationale) —
# shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md's field evidence
# includes library-tier repos (unified-api-contracts) directly, so this needs the same
# fix, not just the service-tier base. SIGKILL stays fundamentally UNCATCHABLE (no trap
# fires for it); this closes the CATCHABLE-signal slice only (SIGTERM/SIGINT/SIGHUP).
_qg_signal_handler() {
    local sig="$1" marker_dir marker
    marker_dir="$(command -v _qg_ledger_dir >/dev/null 2>&1 && _qg_ledger_dir || echo "${WORKSPACE_ROOT:-.}/.benchmarks/qg-governor")"
    mkdir -p "$marker_dir" 2>/dev/null || true
    marker="${marker_dir}/killed.$$"
    {
        echo "killed_by_signal=${sig}"
        echo "pid=$$"
        echo "repo=${PACKAGE_NAME:-unknown}"
        echo "killed_at_epoch=$(date +%s 2>/dev/null || echo 0)"
    } > "$marker" 2>/dev/null || true
    echo "❌ [quality-gates] received SIG${sig} — wrote kill marker (${marker}) before exit; a poller can now tell this apart from a still-running or a normal-exit run" >&2
    exit 143
}
trap '_qg_signal_handler TERM' TERM
trap '_qg_signal_handler INT' INT
trap '_qg_signal_handler HUP' HUP

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
        --help|-h)
            # quickmerge_help_flag_misparsed_as_commit_message_2026_07_30: mirrors the guard
            # added to base-service.sh — --help/-h must be a pure, immediate, side-effect-free
            # no-op, never fall through to the unknown-flag arm below (or, before that arm
            # existed, be silently ignored and run the full gate with default settings).
            cat <<'QG_USAGE'
Usage: quality-gates.sh [FLAGS]   (library-repo gate body: base-library.sh)

Mode flags:
  --no-fix                  Don't auto-reformat the tree (DEFAULT — safe for agents/CI;
                             use for any run whose diff you intend to commit).
  --fix                     Opt into tree-wide auto-fix (ruff --fix / prettier --write).
                             Can dirty files outside your own change — use deliberately.
  --quick                   Faster iteration pass (skips version-alignment / merge-sentinel
                             write) — NOT a substitute for a full gate before shipping.
  --fast                    Change-scoped codex-grep tier (scans only files changed vs the
                             merge-base). Never writes the merge sentinel — the full gate
                             still runs at quickmerge/CI. Local iteration only.

Scope flags (skip one phase):
  --lint                    Lint-only (skips tests).
  --test                    Test-only (skips lint).
  --skip-tests               Skip the pytest phase.
  --skip-typecheck           Skip basedpyright.
  --skip-version-alignment    Skip the version-alignment check.

Other:
  --act                      Run under `act` (local GitHub Actions emulation).
  --help, -h                 Show this message and exit 0 (no gate phases run).

Env var:
  QG_SLICE=tests|typecheck|lint-codex   CI parallel-job slice selector used by the
                                         reusable workflow — not usually set by hand.

Unknown flags are a hard error (exit 1) — see quickmerge_help_flag_misparsed_as_commit_message_2026_07_30
for why: a silently-ignored unrecognized flag is how a fat-fingered run ends up executing the
full gate with unintended default settings instead of failing loud.
QG_USAGE
            exit 0
            ;;
        --no-fix) FIX_MODE=false ;;   --quick) QUICK_MODE=true ;;
        --lint) RUN_TESTS=false ;;    --test) RUN_LINT=false ;;
        --skip-tests) RUN_TESTS=false ;;
        --fix) FIX_MODE=true ;;       --skip-typecheck) SKIP_TYPECHECK=true ;;
        --act) ACT_MODE=true ;;
        --skip-version-alignment) SKIP_VERSION_ALIGNMENT=true ;;
        # --fast: change-scoped ITERATION tier — codex greps only changed source files (see the
        # CODEX_SCOPE_GLOBS block). Never writes the merge sentinel → commit still runs the FULL gate.
        --fast) QG_FAST=1; export QG_FAST ;;
        *)
            # quickmerge_help_flag_misparsed_as_commit_message_2026_07_30: previously any
            # unrecognized flag was silently ignored here (no catch-all arm at all). Hard
            # error instead, mirroring base-service.sh.
            echo "❌ quality-gates.sh: unknown flag: $arg" >&2
            echo "   Run 'bash scripts/quality-gates.sh --help' for the full flag list." >&2
            exit 1
            ;;
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
# _qg_slice_done <phase>: exit cleanly when the CURRENT slice's OWN phase just completed
# (arg = phase that finished). BUG FIX 2026-06-10: the arg-less version exited for
# tests|typecheck at the single post-TESTS call site, so QG_SLICE=typecheck exited
# BEFORE [4] TYPE CHECK ran (CI typecheck leg = silent no-op / false green).
_qg_slice_done() {
    if [ -n "$QG_SLICE" ] && [ "$QG_SLICE" = "${1:-}" ]; then
        echo -e "\n${GREEN:-}✅ QG_SLICE=${QG_SLICE} PASSED${NC:-}"
        exit 0
    fi
}

# ── QG_PROFILE forces a COMPLETE, no-skip run (mirror of base-service.sh) ─────
# Profiling must measure EVERY path, so the skip/quick bypass flags (--quick /
# --skip-tests / --skip-typecheck) are overridden and the green content-sentinel is
# disabled. The <MAX_DURATION> meta-gate is the one thing relaxed (the wall-time IS
# the measurement — a slow single-core profile run must not false-fail).
# FIX_MODE STAYS at its safe default (false / --no-fix) — see base-service.sh for the full
# rationale: AUTO-FIX's tree-wide reformat would dirty every profiled LIBRARY (UTL/UAC) just
# like it did the services. (Codified 2026-06-11.)
if [[ "${QG_PROFILE:-}" == "1" ]]; then
    QUICK_MODE=false; RUN_LINT=true; RUN_TESTS=true; SKIP_TYPECHECK=false
    _QG_RUN_CODEX=true
    export QG_SENTINEL_DISABLE=true
    IGNORE_TIMEOUT=true
    QG_SLICE=""   # profiling measures the whole gate — ignore any slice selector
fi

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
    # Single canonical uv version pin: unified-trading-pm/scripts/workspace/resolve-canonical-versions.py
    # sed -E, not `grep -oP` (2026-08-09, quickmerge_setup_bootstrap_loop_blocks_commit_2026_08_09.md):
    # -P is a GNU/PCRE extension; the /usr/bin/grep a bare subprocess resolves to on macOS (BSD grep,
    # no PCRE) exits 2 on it, which this file's own `set -e` turns into a silent whole-script abort.
    # sed -E is POSIX-portable across BSD and GNU sed alike. See scripts/setup.sh's sibling fix for
    # the full incident writeup (same pattern, same root cause, copy-pasted into both files).
    _uv_pm_root="${WORKSPACE_ROOT:-$(cd "$REPO_ROOT/.." && pwd)}"
    _uv_pin="$(sed -nE 's/^UV_VERSION = "([^"]+)"/\1/p' "${_uv_pm_root}/unified-trading-pm/scripts/workspace/resolve-canonical-versions.py" 2>/dev/null)"
    command -v uv &>/dev/null || pip install "uv${_uv_pin:+==$_uv_pin}" --quiet
    # uv-version drift-guard — WARN-ONLY (mirrors base-service.sh; same rationale + SSOT).
    _uv_ver="$(uv --version 2>/dev/null | awk '{print $2}')"
    if [[ -n "$_uv_pin" && -n "$_uv_ver" && "$_uv_ver" != "$_uv_pin" ]]; then
        echo "⚠️  uv version drift: running $_uv_ver, workspace pin is $_uv_pin — re-lock output may not match CI. Realign: curl -LsSf https://astral.sh/uv/${_uv_pin}/install.sh | env UV_UNMANAGED_INSTALL=\$HOME/.local/bin sh"
    fi
    unset _uv_ver _uv_pin _uv_pm_root
    # uv.lock freshness — WARN-ONLY, never blocking (stays warn-only per 1.5b: making it blocking
    # treadmills on the semver CI-side `version =` bump). The lock IS now the install SSOT —
    # `uv sync --frozen` (below, 1.5b) installs the committed lock EXACTLY, byte-for-byte with CI — so a
    # stale lock is a real (warned) gap: regen with `uv lock` on any EXTERNAL-dep floor change in the
    # SAME commit (internal editable bumps exempt — the lock resolves the on-disk sibling). Do NOT mutate
    # uv.lock here (it dirtied trees + jammed the FF-pull cron). SSOT:
    # plans/active/cicd_consolidated_remaining_2026_06_24.md § Phase 1.5b.
    uv lock --check 2>/dev/null || echo "⚠️  uv.lock out of sync with pyproject.toml (non-blocking — lock is a record, not a pin; pyproject range is the contract). Run 'uv lock' to refresh the record."
    [ ! -d ".venv" ] && uv venv .venv
    [ -f ".venv/bin/activate" ] && source .venv/bin/activate || :
    # LOCAL_DEPS are SIBLING repos at the WORKSPACE ROOT (Path-B / flat layout), not nested under this
    # repo — resolve workspace-root-first, and install into THIS .venv EXPLICITLY (--python). `source
    # activate` alone does NOT reliably retarget `uv pip install` (uv can resolve to a pyenv/global env),
    # which silently skipped the editable install → workspace libs unresolved → basedpyright Unknown
    # cascade inflating the LOCAL typecheck count vs CI. SSOT: plans/active/ci_local_qg_parity_2026_06_08.md.
    _venv_py=".venv/bin/python"; [ -x "$_venv_py" ] || _venv_py="python3"
    _ws_root="${WORKSPACE_ROOT:-$(cd "${REPO_ROOT:-.}/.." && pwd)}"
    # CI-parity (1.5b frozen-lock): install root + EXTERNAL deps from the FROZEN lock — byte-for-byte
    # with CI's `uv sync --frozen`. --frozen NOT --locked (tolerates the semver CI-side `version =`
    # bump; --locked hard-fails on it). uv sync PRUNES packages absent from the lock, so the
    # editable-sibling loop runs AFTER it: a sibling used only for typecheck but NOT declared in
    # pyproject (hence absent from the lock) would otherwise be pruned right after install.
    # SSOT: plans/active/cicd_consolidated_remaining_2026_06_24.md § Phase 1.5b.
    UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --quiet \
        || log_warn "uv sync --frozen failed (lock stale/broken?) — QG runs against the existing .venv"
    for lib in ${LOCAL_DEPS[@]+"${LOCAL_DEPS[@]}"}; do
        for _libcand in "${_ws_root}/$lib" "${REPO_ROOT}/$lib"; do
            [ -d "$_libcand" ] && { uv pip install -e "$_libcand" --python "$_venv_py" --quiet \
                || log_warn "editable install failed for $lib — local typecheck may inflate via Unknown-type cascade"; break; }
        done
    done
fi
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
elif [ -f "$WORKSPACE_VENV/bin/python" ]; then
    PYTHON_CMD="$WORKSPACE_VENV/bin/python"
else
    PYTHON_CMD="python3"
fi

# ── Frozen-lock floor guardrail (1.5b) — every EXTERNAL dep's uv.lock pin must satisfy its pyproject
# range. QG installs via `uv sync --frozen`, so a stale lock (a floor bumped without `uv lock`) ships a
# below-floor pin verbatim (failure-mode-B). BLOCKS by default (fleet proven clean 2026-06-18);
# FROZEN_FLOOR_GATE_WARN=1 downgrades to warn. Deliberately NOT `uv lock --check` (treadmills on the
# cosmetic semver `version =` bump). Editable/internal sibling deps are skipped (resolved on-disk).
# SSOT: plans/active/cicd_consolidated_remaining_2026_06_24.md § 1.5b.
_FLOOR_GATE="${WORKSPACE_ROOT:-$(cd "$REPO_ROOT/.." && pwd)}/unified-trading-pm/scripts/quality_gates/check_lock_satisfies_pyproject.py"
if [[ -f "$_FLOOR_GATE" && -f "$REPO_ROOT/uv.lock" && -x "$REPO_ROOT/.venv/bin/python" ]]; then
    if "$REPO_ROOT/.venv/bin/python" "$_FLOOR_GATE" --repo "$REPO_ROOT"; then
        echo "✅ Frozen-lock floor gate: external uv.lock pins satisfy pyproject ranges"
    elif [ "${FROZEN_FLOOR_GATE_WARN:-0}" = "1" ]; then
        log_warn "Frozen-lock floor gate WARN (FROZEN_FLOOR_GATE_WARN=1; regenerate uv.lock to clear)"
    else
        log_fail "Frozen-lock floor gate: a uv.lock pin violates its pyproject range — run 'uv lock' (see above)"
        exit 1
    fi
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

# ── Change-scoped codex (fast/iterative tier — quality_gates_speed Phase 2; mirror of base-service.sh) ──
# QG_FAST=1 restricts the codex grep checks to the source .py files CHANGED vs the merge-base, passed
# to rg as INCLUDE-globs (which PRESERVE each check's own exclude-globs). Full tier (QG_FAST unset) →
# empty array → codex_rg is BYTE-IDENTICAL to rg. Fast tier never writes .qg_last_passed_sha, so a
# fast miss is re-checked at the merge boundary (quickmerge Pass-1 / CI run the FULL gate).
CODEX_SCOPE_GLOBS=()
if [[ -n "${QG_FAST:-}" ]]; then
    _qgf_base=$(git merge-base HEAD origin/live-defi-rollout 2>/dev/null || echo "")
    while IFS= read -r _qgf_f; do
        [ -n "$_qgf_f" ] && CODEX_SCOPE_GLOBS+=(--glob "$_qgf_f")
    done < <( { [ -n "$_qgf_base" ] && git diff --name-only --diff-filter=ACMR "$_qgf_base" -- '*.py'; \
                git diff --name-only --diff-filter=ACMR -- '*.py'; \
                git ls-files --others --exclude-standard -- '*.py'; } 2>/dev/null | sort -u )
    [ ${#CODEX_SCOPE_GLOBS[@]} -eq 0 ] && CODEX_SCOPE_GLOBS=(--glob '__qg_fast_no_changed_py__')
    log_warn "QG_FAST: codex scoped to $(( ${#CODEX_SCOPE_GLOBS[@]} / 2 )) changed .py file(s)"
fi
# codex_rg: codex grep checks call this instead of bare rg. Empty array → identical to rg.
codex_rg() { rg ${CODEX_SCOPE_GLOBS[@]+"${CODEX_SCOPE_GLOBS[@]}"} "$@"; }

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
    qg_prof start autofix
    # prettier@3.9.5 (not 3.6.2) — see base-service.sh's identical comment:
    # prettier_emphasis_mangling_corpus_corruption_2026_07_14 proved <3.9.5 corrupts markdown;
    # this tree-wide invocation was a second, un-updated pin of the proven-buggy version.
    if command -v npx &>/dev/null; then
        npx --yes prettier@3.9.5 --write --cache "**/*.{md,json,yaml,yml}" --ignore-path .gitignore --ignore-path .prettierignore >/dev/null 2>&1 \
            || log_warn "Prettier not available or no files to format (skipping)"
    else
        log_warn "npx not available — skipping prettier pre-format (commit may require re-staging)"
    fi
    run_timeout 30 $RUFF_CMD format $SOURCE_DIRS >/dev/null 2>&1 || :
    run_timeout 30 $RUFF_CMD check --fix $SOURCE_DIRS >/dev/null 2>&1 || :
    log_success "Auto-fix complete"
    qg_prof end autofix
fi

# ── [2] LINT (ruff, 30s) ──────────────────────────────────────────────────────
if [ "$RUN_LINT" = true ]; then
    log_section "[2/6] LINT"
    qg_prof start lint
    _lint_out=$(run_timeout 30 $RUFF_CMD check $SOURCE_DIRS 2>&1) || { echo "$_lint_out"; log_fail "Lint FAILED"; exit 1; }
    qg_prof end lint
fi

# ── AUTO DOCS-ONLY TIER (WS-L 2026-06-26 — content-derived, NOT a flag; mirror of base-service.sh) ──
# Pure-documentation changeset → skip the slow CODE gates (tests, typecheck) + codex code-body; ANY
# source/config file (.py/.ts/.json/.yaml/.toml/.sh/…) forces the full gate (no lazy bypass). Derived
# from the working tree, so the server v2 (committed PR, no uncommitted diff) always runs the full
# gate — the backstop. Engages only on an otherwise-full run; the sentinel still writes (complete for
# a doc-only changeset). Capture-and-test-empty avoids the fragile `grep -qv` combo.
_QG_DOCS_ONLY=false
if [ "${RUN_TESTS}" = true ] && [ "${RUN_LINT}" = true ] && [ "${SKIP_TYPECHECK}" != "true" ] \
   && [ "${QUICK_MODE}" != "true" ] && [ "${ACT_MODE}" != "true" ] && [ -z "${QG_SLICE:-}" ] && [ -z "${QG_FAST:-}" ]; then
    _qg_changed="$( { git diff HEAD --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null; \
                      git ls-files --others --exclude-standard 2>/dev/null; } | grep -vE '^[[:space:]]*$' | sort -u )"
    _qg_nondoc="$( printf '%s\n' "$_qg_changed" | grep -ivE '\.(md|mdc|rst|txt|svg|png|jpe?g|gif|ico)$' || true )"
    if [ -n "$_qg_changed" ] && [ -z "$_qg_nondoc" ]; then
        _QG_DOCS_ONLY=true
        RUN_TESTS=false; SKIP_TYPECHECK="true"; _QG_RUN_CODEX=false
        log_warn "DOCS-ONLY changeset ($(printf '%s\n' "$_qg_changed" | wc -l | tr -d ' ') file(s), all documentation) → skipping TESTS + TYPECHECK + codex code-body; lint/format + doc-validators still run. Any source/config change forces the full gate; the server v2 always runs the full gate."
    fi
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
    qg_prof start tests
    $PYTHON_CMD -c "import pytest_timeout" 2>/dev/null || { log_fail "pytest-timeout required: uv pip install pytest-timeout"; exit 1; }
    $PYTHON_CMD -c "import xdist" 2>/dev/null || { log_fail "pytest-xdist required: uv pip install pytest-xdist"; exit 1; }
    # TIER-A config-SSOT (2026-06-17): no --cov-fail-under — pytest-cov reads fail_under
    # from [tool.coverage.report] in pyproject.toml when the CLI flag is absent, so toml is
    # the single home for the coverage gate. Verified pre-flip: UTL/UAC toml fail_under ==
    # stub MIN_COVERAGE (80/80, 94/94). SSOT: quality_gates_speed_and_config_ssot_2026_06_09.md Phase 1.
    COV="--cov=$SOURCE_DIR --cov-report=xml:coverage.xml"
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
    # Wall-clock per-test timeout. Explicit PYTEST_TIMEOUT_SECONDS wins; default raised
    # 60→150 to absorb GH-Actions-xdist + shared-host scheduling variance without
    # meaningfully delaying detection of a genuinely hung test (2026-07-29:
    # pytest_timeout_60s_flaky_under_contention_2026_07_29.md — a 0.04s offline-only
    # test hit the 60s deadline under sibling-xdist-worker contention on hosted CI).
    PYTEST_TIMEOUT_SECONDS="${PYTEST_TIMEOUT_SECONDS:-150}"
    PARGS="-n ${_PYTEST_N} --timeout=${PYTEST_TIMEOUT_SECONDS} -q -r a --tb=short --no-header --durations=25"

    # ── Retry-once-on-timeout (xdist/scheduler-contention flake class) ──────────
    # A fixed wall-clock per-test budget under xdist `-n auto` / a contended host can
    # fire on a genuinely instant test (0.04-2s in isolation) that gets descheduled past
    # the budget by sibling workers or co-resident jobs — the 60→150s raise (2026-07-29)
    # reduced but did NOT close the class: at load avg 50+ even CPU-bound synchronous
    # tests were starved 15+ min, so no fixed budget can ever beat the contention. SSOT:
    # plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md.
    # Retry-once-on-timeout targets the MECHANISM, not the threshold: when EVERY failure
    # in a run is a pytest-timeout, re-run exactly those tests serially (minimal
    # contention). A genuine hang times out AGAIN on the retry and still fails the gate;
    # a scheduling-descheduled test passes clean. Disable: PYTEST_TIMEOUT_RETRIES=0.
    # Only retries when every failed/errored test is a timeout — a real failure fails
    # the gate outright (no masking of genuine failures).
    PYTEST_TIMEOUT_RETRIES="${PYTEST_TIMEOUT_RETRIES:-1}"
    _qg_pytest_timeout_retry() {
        local _out="$1"
        local _tids _nt _nf
        _tids=$(printf '%s\n' "$_out" | grep -E '^FAILED [^ ]+ - Failed: Timeout' | sed -E 's/^FAILED ([^ ]+) - .*/\1/' | tr '\n' ' ' || true)
        _nt=$(printf '%s' "$_tids" | wc -w | tr -d ' ')
        [ "${_nt:-0}" -gt 0 ] || return 1
        _nf=$(printf '%s\n' "$_out" | grep -cE '^(FAILED|ERROR) [^ ]+ - ' || true)
        [ "${_nf:-0}" = "$_nt" ] || return 1
        log_warn "pytest-timeout on ${_nt} test(s) — ALL failures are timeouts; serial re-run (retry-once-on-timeout for the xdist-contention flake class)"
        # shellcheck disable=SC2086  # intentional word-split: _tids is a space-separated nodeid list
        if $PYTHON_CMD -m pytest ${_tids} --allow-hosts=127.0.0.1,::1,localhost --allow-unix-socket --timeout=${PYTEST_TIMEOUT_SECONDS} -q -r a --tb=short --no-header 2>&1; then
            log_success "retry-on-timeout: the ${_nt} timed-out test(s) passed clean serially — scheduling contention, not a hang"
            return 0
        fi
        return 1
    }

    # Per-repo test root override. Default: tests/unit/. Set PYTEST_UNIT_DIR before sourcing this
    # script to add per-family unit test dirs (e.g. PYTEST_UNIT_DIR="tests/unit/ tests/events/unit/").
    PYTEST_UNIT_DIR="${PYTEST_UNIT_DIR:-tests/unit/}"

    _HAS_INTEGRATION=false
    [ -d "tests/integration" ] && \
        [ "$(find tests/integration -name 'test_*.py' 2>/dev/null | wc -l | tr -d ' ')" -gt 0 ] && \
        _HAS_INTEGRATION=true

    if [ "$_HAS_INTEGRATION" = true ]; then
        _pytest_out=$($PYTHON_CMD -m pytest ${PYTEST_UNIT_DIR} tests/integration/ --allow-hosts=127.0.0.1,::1,localhost --allow-unix-socket $PARGS $COV 2>&1) \
            || { if [ "${PYTEST_TIMEOUT_RETRIES:-1}" != "0" ] && _qg_pytest_timeout_retry "$_pytest_out"; then :; else echo "$_pytest_out"; exit 1; fi; }
    else
        _pytest_out=$($PYTHON_CMD -m pytest ${PYTEST_UNIT_DIR} --allow-hosts=127.0.0.1,::1,localhost --allow-unix-socket $PARGS $COV 2>&1) \
            || { if [ "${PYTEST_TIMEOUT_RETRIES:-1}" != "0" ] && _qg_pytest_timeout_retry "$_pytest_out"; then :; else echo "$_pytest_out"; exit 1; fi; }
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
    qg_prof end tests
fi
# QG_SLICE=tests finishes here (its one phase is the pytest run above).
_qg_slice_done tests

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
    # TMPDIR-aware (matches BASEDPYRIGHT_CACHE_DIR above, and the base-service.sh sibling fix) —
    # a hardcoded /tmp path here (and at every other checker-capture site below) made the capture
    # write fail with ENOSPC whenever a shared host's /tmp tmpfs was full, producing a false gate
    # failure indistinguishable from a real one (qg_hardcoded_tmp_paths_false_failures_on_full_tmpfs_2026_07_26.md).
    _bp_out="${TMPDIR:-/tmp}/bp_out.$$"
    qg_prof start typecheck
    run_timeout "${PYRIGHT_TIMEOUT:-120}" "$BASEDPYRIGHT_CMD" "$SOURCE_DIR/" > "$_bp_out" 2>&1 &
    BP_PID=$!
    wait $BP_PID || true
    PYRIGHT_EXIT=$?
    qg_prof end typecheck
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
qg_prof start codex
V=0

codex_rg "print\(" --type py --glob "!tests/**" --glob "!scripts/**" --glob "!**/testing/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "print() — use logger"; V=$(( V + 1 )); } || log_success "No print()"

# unified-config-interface: bootstrap exception — UCI IS the config layer, must read os.environ
# (QUALITY_GATE_BYPASS_AUDIT.md §2.4)
if [[ "$PACKAGE_NAME" != "unified-config-interface" ]]; then
    _osenv_extra_globs=()
    for _f in "${OS_ENVIRON_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_f" ]] && _osenv_extra_globs+=("--glob" "!${_f}"); done
    _OSENV=$(codex_rg "os\.getenv|os\.environ" --type py --glob "!tests/**" --glob "!**/testing/**" --glob "!scripts/**" "${_osenv_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
        | grep -v "# noqa:.*qg-os-environ\|# noqa: qg-os-environ\|# config-bootstrap:" || :)
    [[ -n "$_OSENV" ]] && { log_fail "os.getenv()/os.environ — use UnifiedCloudConfig for config, get_secret_client() for secrets"; echo "$_OSENV" | head -3; V=$(( V + 1 )); } || log_success "No os.getenv()/os.environ"
else
    log_success "os.getenv/bootstrap — UTL cloud_interface is config layer (bypass §2.4)"
fi

codex_rg 'os\.getenv\s*\([^)]+,\s*""\s*\)' --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "os.getenv empty fallback — fail fast"; V=$(( V + 1 )); } || log_success "No os.getenv empty fallback"

codex_rg "datetime\.now\(\)|datetime\.utcnow\(\)" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Naive datetime — use datetime.now(timezone.utc)"; V=$(( V + 1 )); } || log_success "No naive datetime"

codex_rg "except:" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Bare except — use specific exception"; V=$(( V + 1 )); } || log_success "No bare except"

for f in $(codex_rg "import requests" --type py --glob "!tests/**" --glob "!scripts/**" "$SOURCE_DIR/" -l 2>/dev/null || :); do
    # Skip if the import line has a noqa comment for this check
    codex_rg "import requests.*# noqa:.*qg-requests-in-async" "$f" >/dev/null 2>&1 && continue
    grep -q "async def" "$f" && { log_fail "requests in async: $f — use aiohttp"; V=$(( V + 1 )); break; }
done; [[ ${V} -eq $(( V )) ]] && log_success "No requests in async" 2>/dev/null || :

_asyncio_violation=""
for f in $(codex_rg "asyncio\.run\(" --type py --glob "!tests/**" --glob "!scripts/**" --glob "!**/testing/**" "$SOURCE_DIR/" -l 2>/dev/null || :); do
    # Only flag asyncio.run() deeply nested inside a loop body (>=8 spaces indentation)
    if codex_rg "^\s{8,}asyncio\.run\(" "$f" 2>/dev/null | grep -q .; then
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
    "${_inside_extra_args[@]}" 2>${TMPDIR:-/tmp}/_inside_imports_qg.err; then
    log_success "No imports inside functions"
else
    log_fail "Imports inside functions — move to top (AST-detected)"
    head -10 ${TMPDIR:-/tmp}/_inside_imports_qg.err 2>/dev/null
    V=$(( V + 1 ))
fi

# `!**/testing/**` mirrors the empty-fallback + inside-import checks: in-package test-support
# utilities (e.g. internal/testing/ seed validators) legitimately carry `pd.Series[Any]` that
# pandas-stubs forces and that basedpyright's reportUnknownVariableType requires be annotated.
ANY=$(codex_rg ": Any|-> Any|\[Any\]" --type py --glob "!tests/**" --glob "!**/testing/**" "$SOURCE_DIR/" 2>/dev/null | grep -v "type: ignore" || :)
[[ -n "$ANY" ]] && { log_fail "Any types (including dict[str, Any]) — use Pydantic models or specific types"; echo "$ANY" | head -3; V=$(( V + 1 )); } || log_success "No Any types"

_raw_json_extra_globs=()
for _excl in "${RAW_JSON_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _raw_json_extra_globs+=("--glob" "!${_excl}"); done
RAW_JSON=$(codex_rg 'response\.json\(\)|await response\.json\(\)' --type py --glob "!tests/**" "${_raw_json_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v 'model_validate\|cast(dict' \
    | grep -v "# noqa:.*qg-raw-json\|# noqa: qg-raw-json" || :)
[[ -n "$RAW_JSON" ]] && { log_fail "Raw response.json() — parse through Pydantic model_validate()"; echo "$RAW_JSON" | head -3; V=$(( V + 1 )); } || log_success "No raw response.json()"

_efb_extra_globs=()
for _excl in "${EMPTY_FALLBACK_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _efb_extra_globs+=("--glob" "!${_excl}"); done
# Empty-string fallback (`.get("key", "")`) is now STEP 5.101 below — a per-repo
# baseline-ratchet (check_no_empty_string_fallback.py), replacing the zero-tolerance
# inline check that used to live here. See
# plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md.

ED=$(codex_rg '\.get\s*\(\s*["\x27][^"\x27]+["\x27]\s*,\s*\{\}\s*\)' --type py --glob "!tests/**" --glob "!**/testing/**" "${_efb_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa:.*qg-empty-fallback\|# noqa: qg-empty-fallback" || :)
EL=$(codex_rg '\.get\s*\(\s*["\x27][^"\x27]+["\x27]\s*,\s*\[\]\s*\)' --type py --glob "!tests/**" --glob "!**/testing/**" "${_efb_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
    | grep -v "# noqa:.*qg-empty-fallback\|# noqa: qg-empty-fallback" || :)
[[ -n "$ED$EL" ]] && { log_fail "Empty dict/list fallback — fail fast"; V=$(( V + 1 )); } || log_success "No empty dict/list fallbacks"

codex_rg "central-element-323112" tests/ 2>/dev/null \
    && { log_fail "Hardcoded prod project ID in tests — use 'test-project'"; V=$(( V + 1 )); } || log_success "No hardcoded project ID in tests"

# GCP_PROJECT_ID_EXCLUDE_GLOBS: per-repo array of glob patterns (e.g. "!**/registry/foo.py")
GCP_LIB_EXTRA=()
for g in ${GCP_PROJECT_ID_EXCLUDE_GLOBS[@]+"${GCP_PROJECT_ID_EXCLUDE_GLOBS[@]}"}; do GCP_LIB_EXTRA+=(--glob "$g"); done
codex_rg "central-element-323112" --type py --glob "!tests/**" "${GCP_LIB_EXTRA[@]}" "$SOURCE_DIR/" 2>/dev/null \
    && { log_fail "Hardcoded project ID in production — use config"; V=$(( V + 1 )); } || log_success "No hardcoded project ID in production"

BAD_PROJECT=$(codex_rg "GOOGLE_CLOUD_PROJECT|GCP_PROJECT(?!_ID)" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$BAD_PROJECT" ]] && { log_fail "Use GCP_PROJECT_ID; banned: GOOGLE_CLOUD_PROJECT, GCP_PROJECT"; echo "$BAD_PROJECT" | head -3; V=$(( V + 1 )); } || log_success "Project ID uses GCP_PROJECT_ID"

# Domain clients live in unified_trading_library.domain (re-exported at the UTL top level) — there is NO
# separate unified_domain_client package anywhere in the workspace. RETARGETED 2026-07-30 (mirrors
# base-service.sh): the prior check demanded imports come FROM unified_domain_client and failed on the
# correct top-level form, directly contradicting the deep-import (DI) check below, which independently
# requires top-level and fails on a `.domain` submodule import — no import shape could pass both.
# FOLLOW-UP FIX 2026-07-30 (mirrors base-service.sh): added a second `(?!\.)` lookahead — the first
# retarget's module-name class still matched a RELATIVE import's leading dot (`from .instruments import
# X`), breaking UTL's own internal source. SSOT:
# plans/active/codex_violations_ratchet_to_five_2026_06_10.md.
UCS_DOMAIN=$(codex_rg 'from (?!unified_trading_library)(?!\.)[a-zA-Z0-9_.]+ import[^#]*?(InstrumentsDomainClient|ExecutionDomainClient|MarketCandleDataDomainClient|MarketTickDataDomainClient|create_instruments_client|create_execution_client|create_features_client|create_market_candle_data_client|create_market_tick_data_client)' \
    --pcre2 --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$UCS_DOMAIN" ]] && { log_fail "Domain clients must come from unified_trading_library (top-level or .domain), not a per-repo shim"; echo "$UCS_DOMAIN" | head -5; V=$(( V + 1 )); } || log_success "Domain clients imported from unified_trading_library"

DOMAIN_FROM_UCS=$(codex_rg 'from (?!unified_trading_library)(?!\.)[a-zA-Z0-9_.]+ import.*(market_category|DomainValidation|UnifiedCloudServicesConfig)' \
    --pcre2 --type py "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$DOMAIN_FROM_UCS" ]] && { log_fail "Library imports domain symbols from a non-unified_trading_library source — use unified_trading_library instead"; echo "$DOMAIN_FROM_UCS" | head -5; V=$(( V + 1 )); } || log_success "No stray domain imports outside unified_trading_library"

if codex_rg 'def setup_events|def setup_service' --type py "$SOURCE_DIR/" -q 2>/dev/null; then
    log_success "setup_service() check skipped (repo defines setup_events/setup_service)"
else
    SETUP_NO_SINK=$(codex_rg 'setup_(events|service)\s*\(' --type py \
        --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null | grep -v 'sink=' \
        | grep -v "def setup_events\|def setup_service" \
        | grep -vE ":[[:space:]]*#|:[[:space:]]+(\"\"\"|\x27\x27\x27)" || :)
    [[ -n "$SETUP_NO_SINK" ]] && { log_fail "setup_events()/setup_service() called without sink= in production code"; echo "$SETUP_NO_SINK" | head -5; V=$(( V + 1 )); } || log_success "setup_service() uses sink= in all production call sites"
fi

BAD_AUTH_SKIP=$(codex_rg 'pytest\.skip.*[Cc]redential|pytest\.skip.*GOOGLE_APPLICATION_CREDENTIALS|if not.*gcp_credentials.*pytest\.skip\|if not.*cred_file.*pytest\.skip' \
    --type py tests/ 2>/dev/null \
    | grep -v "_skip_integration_without_creds\|No GCP credentials.*skipping integration\|No GCP credentials.*skipping Secret Manager\|Could not create/access" \
    || :)
[[ -n "$BAD_AUTH_SKIP" ]] && { log_fail "Tests skip due to missing credential file — use google.auth.default() + @pytest.mark.integration instead"; echo "$BAD_AUTH_SKIP" | head -5; V=$(( V + 1 )); } || log_success "No credential-file skip patterns in tests"

[[ -f ".env.example" ]] && codex_rg "GOOGLE_APPLICATION_CREDENTIALS" .env.example 2>/dev/null \
    && { log_fail ".env.example contains GOOGLE_APPLICATION_CREDENTIALS — remove it (use ADC, not SA key files)"; V=$(( V + 1 )); } || log_success "No GOOGLE_APPLICATION_CREDENTIALS in .env.example"

_di_extra_globs=()
for _excl in "${DEEP_IMPORT_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _di_extra_globs+=("--glob" "!${_excl}"); done
DI=$(codex_rg 'from unified_[a-z_]+\.[a-zA-Z0-9_.]+\s+import' --type py --glob "!tests/**" --glob "!**/__init__.py" "${_di_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null \
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
CLOUD_SDK_VIOLATIONS=$(codex_rg "^from google\.cloud|^import boto3|^import botocore" \
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
    TIER_VIOLATIONS=$(codex_rg 'from unified_trading_library|from unified_domain_client' \
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
BACK_COMPAT=$(codex_rg "# MIGRATED|backward compat|backward-compat|Re-export.*backward|re-export.*compat" \
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
    DOMAIN_CONTRACTS_IN_LIB=$(codex_rg 'class \w+\(BaseModel\)' --type py \
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
    PROTOCOL_VIOLATIONS=$(codex_rg "CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
        --type py --glob '!.venv*' --glob '!**/.venv*/**' --glob '!tests' --glob '!**/cloud_config.py' -l . 2>/dev/null || :)
elif [[ "$PACKAGE_NAME" = "unified-api-contracts" ]]; then
    # UAC defines CloudTarget as the workspace SSOT enum (canonical/crosscutting/cloud_target.py)
    # and re-exports it from the top-level facade + canonical.crosscutting + canonical.domain.
    # The other protocol-specific symbols (gcs_bucket, bigquery_dataset, etc.) are still blocked.
    PROTOCOL_VIOLATIONS=$(codex_rg "upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
        --type py --glob '!.venv*' --glob '!**/.venv*/**' --glob '!tests' -l . 2>/dev/null || :)
elif [[ "$PACKAGE_NAME" = "unified-trading-library" ]]; then
    # UTL defines/deprecates these symbols — skip the origin and compat-layer files
    # domain_client/ sub-package (merged into UTL) uses these symbols legitimately
    PROTOCOL_VIOLATIONS=$(codex_rg "CloudTarget|upload_to_gcs_batch|StandardizedDomainCloudService" \
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
    PROTOCOL_VIOLATIONS=$(codex_rg "CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
        --type py --glob '!.venv*' --glob '!**/.venv*/**' --glob '!tests' -l . 2>/dev/null || :)
fi
[[ -n "$PROTOCOL_VIOLATIONS" ]] && {
    log_fail "STEP 5.11: Protocol-specific symbols found. Use get_data_sink() / get_event_bus() from UTL instead:"
    echo "$PROTOCOL_VIOLATIONS"
    V=$(( V + 1 ))
} || log_success "STEP 5.11: No protocol-specific symbols in library code"

# ============================================================
# STEP 5.13 — Schema canonical name collision (advisory)
# ============================================================
SCHEMA_COLLISION=$(codex_rg 'class\s+Canonical[A-Z]\w+\s*\(' \
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
    PIP=$(codex_rg "^RUN pip install|^RUN python -m pip" Dockerfile 2>/dev/null | grep -v "uv pip install" | grep -v "pip install uv" | grep -v "#" || :)
    [[ -n "$PIP" ]] && { log_fail "Use 'uv pip install' not 'pip install' in Dockerfile"; echo "$PIP" | head -3; V=$(( V + 1 )); } || log_success "No bare pip install in Dockerfile"
fi
PIP_SH=$(codex_rg " pip install " --glob "**/*.sh" --glob "!unified-trading-pm/**" . 2>/dev/null | grep -v "uv pip install" | grep -v "pip install uv" | grep -v "#" || :)
[[ -n "$PIP_SH" ]] && { log_fail "Use 'uv pip install' not 'pip install' in scripts"; echo "$PIP_SH" | head -3; V=$(( V + 1 )); } || log_success "No bare pip install in scripts"

_be_extra_globs=()
for _excl in "${BROAD_EXCEPT_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _be_extra_globs+=("--glob" "!${_excl}"); done
BE=$(codex_rg "except Exception:" --type py --glob "!tests/**" "${_be_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null || :)
# AST-filter out matches that only occur inside a string/comment (e.g. a generated-code
# template literal) — the raw regex above can't tell source code from a string containing
# similar text; this narrows to real ExceptHandler nodes before counting a violation.
[[ -n "$BE" ]] && BE=$(echo "$BE" | python3 "$(dirname "${BASH_SOURCE[0]}")/filter_broad_except_string_literals.py" 2>/dev/null || echo "$BE")
[[ -n "$BE" ]] && { log_warn "broad except Exception — document in QUALITY_GATE_BYPASS_AUDIT.md"; echo "$BE" | head -5; V=$(( V + 1 )); } || log_success "No broad except Exception"

SWALLOWED=$(codex_rg "except Exception:" --type py --glob "!tests/**" "${_be_extra_globs[@]}" "$SOURCE_DIR/" -A 2 2>/dev/null \
    | grep -E "^[[:space:]]+(pass|return None)$" || :)
[[ -n "$SWALLOWED" ]] && { log_fail "Swallowed errors — use @handle_api_errors or re-raise"; V=$(( V + 1 )); } || log_success "No swallowed errors"

# CI/CD hygiene: ||true bypasses in quality gate scripts
BYPASS=$(codex_rg "\|\|true|\|\| true" --glob "**/quality-gates.sh" --glob "**/quality-gates.yml" . 2>/dev/null \
    | grep -v "BYPASS —\|fix the root cause\|zombies\|pyright\|cleanup" || :)
[[ -n "$BYPASS" ]] && { log_fail "||true bypass in quality gates — fix the root cause"; echo "$BYPASS" | head -3; V=$(( V + 1 )); } || log_success "No ||true quality gate bypasses"

# File size (exclude build artifacts and test dirs — tests get warn-only treatment)
# Optional: SIZE_EXTRA_EXCLUDES array of extra ! -path patterns (set before sourcing)
qg_prof start size-checks
SVIOL=""; SWARN=""
_size_extra_args=()
for _excl in "${SIZE_EXTRA_EXCLUDES[@]:-}"; do [[ -n "$_excl" ]] && _size_extra_args+=("!" "-path" "$_excl"); done
# Batched size-checks (mirror of base-service.sh): ONE python pass per check instead of
# 1 wc/python PER source file — the per-file subprocess spawn was the size-check cost.
# Same find exclusions + thresholds + AST visitor verbatim → byte-identical violations;
# only the spawn count drops (O(files) → 3). Helps every QG context (local/CI/SIT).
# `|| true`: set-e-safety (a non-zero find — e.g. an rg `--glob` exclude find rejects, or a broken
# symlink — must not trip `set -e` and kill the gate; the original for-loop tolerated it). See
# base-service.sh size-checks for the full note.
_SIZE_FILES_FILE=$(find . -name "*.py" ! -path "./.venv/*" ! -path "./scripts/*" ! -path "./.git/*" ! -path "./.claude/*" ! -path "./build/*" ! -path "./unified-trading-pm/*" "${_size_extra_args[@]}" 2>/dev/null || true)
# File-size: non-test files FAIL (SVIOL), test files WARN (SWARN); line count == `wc -l` (count of '\n').
# The ./tests/ ./test/ split matches the original `[[ "$f" == ./tests/* ]]` root-anchored glob.
SVIOL=$(printf '%s\n' "$_SIZE_FILES_FILE" | $PYTHON_CMD -c "
import sys
mx=$MAX_FILE_LINES; out=[]
for p in (line.strip() for line in sys.stdin):
  if not p or p.startswith('./tests/') or p.startswith('./test/'): continue
  try:
    with open(p,'rb') as fp: n=fp.read().count(b'\n')
  except OSError: continue
  if n>mx: out.append(f'  {p}: {n} L')
print('\n'.join(out))
" 2>/dev/null || :)
SWARN=$(printf '%s\n' "$_SIZE_FILES_FILE" | $PYTHON_CMD -c "
import sys
mx=$MAX_FILE_LINES; out=[]
for p in (line.strip() for line in sys.stdin):
  if not p or not (p.startswith('./tests/') or p.startswith('./test/')): continue
  try:
    with open(p,'rb') as fp: n=fp.read().count(b'\n')
  except OSError: continue
  if n>mx: out.append(f'  {p}: {n} L')
print('\n'.join(out))
" 2>/dev/null || :)
[[ -n "$SVIOL" ]] && { log_fail "Files exceed $MAX_FILE_LINES lines:\n$SVIOL"; V=$(( V + 1 )); } || log_success "File size OK"
[[ -n "$SWARN" ]] && log_warn "Test files exceed limit:\n$SWARN"

# Function/class/method size (exclude build artifacts and test dirs — test methods can be long)
FSIZES=$(find . -name "*.py" ! -path "./.venv/*" ! -path "./scripts/*" ! -path "./.git/*" ! -path "./.claude/*" ! -path "./build/*" ! -path "./tests/*" ! -path "./test/*" ! -path "./unified-trading-pm/*" "${_size_extra_args[@]}" 2>/dev/null | $PYTHON_CMD -c "
import ast, sys
for p in (line.strip() for line in sys.stdin):
  if not p: continue
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
  except Exception: pass
" 2>/dev/null || :)
[[ -n "$FSIZES" ]] && { log_fail "Function/class/method size exceeded:\n$FSIZES"; V=$(( V + 1 )); } || log_success "Function/class/method size OK"
qg_prof end size-checks

# Security: pip-audit (prefer project venv to avoid workspace transitive vulns)
qg_prof start pip-audit
if $PYTHON_CMD -c "import pip_audit" 2>/dev/null; then
    # aiohttp cookie-CVE cluster CVE-2026-34993/47265/50269/54273-54280 — RESOLVED: execution-service (the last
    #   holdout) migrated to adapter-boundary mocks and bumped to aiohttp>=3.14.1 fleet-wide; the 11 ignore-vuln
    #   entries were dropped from QG_PIP_AUDIT_COMMON_IGNORES. See
    #   plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md.
    # CVE-2026-54283 / -54282 (starlette <1.3.1) — RESOLVED 2026-07-28: fastapi/starlette floor lifted to
    #   fastapi>=0.137.0/starlette>=1.3.1 fleet-wide. Ignore DROPPED. See
    #   plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md.
    # RE-AUDITED 2026-07-30 (mirrors base-service.sh): every entry currently in QG_PIP_AUDIT_COMMON_IGNORES was
    # re-verified against each repo's ACTUAL locked version — 4 entries confirmed fully moot and dropped with zero
    # repo changes; every remaining entry's real fix version + still-vulnerable repo list is documented at the
    # ignore list itself (qg-common.sh), the single SSOT — do NOT re-duplicate that detail here.
    _pa_extra="${PIP_AUDIT_EXTRA_ARGS:-} ${QG_PIP_AUDIT_COMMON_IGNORES}"
    # DEPS-CHANGE/CRON TRIGGER (plan quality_gates_speed_and_config_ssot_2026_06_09 Phase 3;
    # parity with base-service.sh): the OSV query runs only when the deps-hash (pyproject.toml
    # + uv.lock + ignore set + pip-audit version) changed, OR the cached clean result is older
    # than QG_PIP_AUDIT_MAX_AGE_HOURS (default 24h — cron-equivalent freshness bound for
    # newly-published advisories). ONLY a clean run is cached (.qg_cache/pip_audit_deps_hash).
    # Bypass: QG_NO_CACHE=1 forces the full OSV query.
    _pa_key=$({ cat pyproject.toml uv.lock 2>/dev/null || :; echo "$_pa_extra"; $PYTHON_CMD -m pip_audit --version 2>/dev/null || :; } | _qg_hash)
    if qg_cache_hit pip_audit_deps_hash "$_pa_key" "${QG_PIP_AUDIT_MAX_AGE_HOURS:-24}"; then
        log_success "pip-audit: cached (deps unchanged, age $(_qg_cache_age_hours pip_audit_deps_hash || echo '?')h)"
    else
        # Classify by WHAT pip-audit produced, not just the exit code (parity with base-service.sh):
        # a non-zero exit with NO vuln report = INFRA error (OSV unreachable / crash) → advisory, NOT
        # a gate fail. Previously any non-zero exit was reported as "vulnerabilities", so a network
        # blip reddened a green PR. A genuine finding still writes the json and still fails.
        _pa_rc=0
        $PYTHON_CMD -m pip_audit --format json $_pa_extra -o ${TMPDIR:-/tmp}/pip-audit-lib-output.json >/dev/null 2>&1 || _pa_rc=$?
        if [[ $_pa_rc -eq 0 ]]; then
            qg_cache_store pip_audit_deps_hash "$_pa_key"
        elif [[ -s ${TMPDIR:-/tmp}/pip-audit-lib-output.json ]] && $PYTHON_CMD -c "import json,sys; d=json.load(open('${TMPDIR:-/tmp}/pip-audit-lib-output.json')); sys.exit(0 if any(x.get('vulns') for x in d.get('dependencies',[])) else 1)" 2>/dev/null; then
            log_fail "pip-audit vulnerabilities"
            $PYTHON_CMD -c "
import json
try:
    data = json.load(open('${TMPDIR:-/tmp}/pip-audit-lib-output.json'))
    for d in data.get('dependencies', []):
        for v in d.get('vulns', []):
            print(f'  {d[\"name\"]} {d[\"version\"]}: {v[\"id\"]} — {v.get(\"description\",\"\")[:120]}')
except Exception as e:
    print(f'  (could not parse pip-audit output: {e})')
" 2>/dev/null || :
            V=$(( V + 1 ))
        else
            log_warn "pip-audit: infra error (rc=$_pa_rc, no vuln report — OSV unreachable?) — skipping vulnerability gate (advisory)"
        fi
    fi
elif command -v pip-audit &>/dev/null; then
    # Bare-PATH fallback (no venv pip_audit): rare path — uncached by design.
    _pa_rc=0; _pa_out=$(pip-audit 2>&1) || _pa_rc=$?
    if [[ $_pa_rc -eq 0 ]]; then
        :
    elif echo "$_pa_out" | grep -qiE 'known vulnerabilit'; then
        echo "$_pa_out"; log_fail "pip-audit vulnerabilities"; V=$(( V + 1 ))
    else
        log_warn "pip-audit: infra error (rc=$_pa_rc, no vuln report — OSV unreachable?) — advisory"
    fi
else
    log_fail "pip-audit required: uv pip install pip-audit"; V=$(( V + 1 ))
fi
qg_prof end pip-audit

# Security: bandit (use python -m bandit for venv reliability)
# CONTENT-HASH CACHE (plan quality_gates_speed_and_config_ssot_2026_06_09 Phase 3; parity
# with base-service.sh): key = source content (index blobs + worktree diff + untracked)
# under SOURCE_DIR + pyproject.toml + bandit version → .qg_cache/bandit_content_hash.
# ONLY a clean run is cached — issues always re-run + re-print. Bypass: QG_NO_CACHE=1.
qg_prof start bandit
if $PYTHON_CMD -c "import bandit" 2>/dev/null; then
    _bandit_key=$({ _qg_src_content_key "$SOURCE_DIR" pyproject.toml; $PYTHON_CMD -m bandit --version 2>/dev/null || :; } | _qg_hash)
    if qg_cache_hit bandit_content_hash "$_bandit_key"; then
        log_success "bandit: cached (source content unchanged)"
    else
        # -c pyproject.toml: honor [tool.bandit] (single config home). Audited safe 2026-06-17
        # (UTL/UAC carry no non-empty skips); bandit tolerates -c with no [tool.bandit] section.
        # Timeout 30 → 180 (2026-07-17): 30s was under the real cost on the larger libraries, and
        # the failure is SILENTLY MISLEADING — run_timeout kills bandit, the non-zero exit falls
        # into the `||` branch, and the gate prints "bandit issues" + V++ as though a SECURITY
        # finding was detected. Measured on UTL: a full scan takes ~52s (clean: Medium 0 / High 0,
        # exit 0), so any cache-miss run on a loaded host failed the repo for a nonexistent
        # vulnerability. Raising the ceiling only grants time — a genuinely hung bandit still gets
        # killed, just at a bound above the honest worst case.
        _bandit_out=$(run_timeout 180 $PYTHON_CMD -m bandit -c pyproject.toml -r "$SOURCE_DIR/" -ll 2>&1) \
            && qg_cache_store bandit_content_hash "$_bandit_key" \
            || { echo "$_bandit_out"; log_fail "bandit issues"; V=$(( V + 1 )); }
    fi
else
    log_fail "bandit required: uv pip install bandit"; V=$(( V + 1 ))
fi
qg_prof end bandit

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
  codex_rg 'from unified_api_contracts\.canonical\.' "$SOURCE_DIR/" --glob '!**/test_*' --glob '!**/conftest*' --type py 2>/dev/null && DEEP_UAC_IMPORTS=1 || :
  codex_rg 'from unified_api_contracts\.normalize_utils\.' "$SOURCE_DIR/" --type py 2>/dev/null && DEEP_UAC_IMPORTS=1 || :
  codex_rg 'from unified_api_contracts\.config\.' "$SOURCE_DIR/" --type py 2>/dev/null && DEEP_UAC_IMPORTS=1 || :
  codex_rg 'from unified_api_contracts\.shared\.' "$SOURCE_DIR/" --type py 2>/dev/null && DEEP_UAC_IMPORTS=1 || :
  codex_rg 'from unified_api_contracts\.schemas\.' "$SOURCE_DIR/" --type py 2>/dev/null && DEEP_UAC_IMPORTS=1 || :
  if [[ $DEEP_UAC_IMPORTS -eq 1 ]]; then
    log_fail "STEP 5.23: Deep UAC import detected. Use facade: from unified_api_contracts.{domain} import X"
    codex_rg 'from unified_api_contracts\.(canonical|normalize_utils|config|shared|schemas)\.' "$SOURCE_DIR/" --type py 2>/dev/null | head -10
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
  _TYPE_IGNORE_HITS=$(codex_rg -n '# type: ignore' "$SOURCE_DIR/" --type py --glob '!tests/**' --glob '!**/testing/**' 2>/dev/null || :)
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
qg_prof end codex

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
    if $PYTHON_CMD "$_CHAIN_INCLUSION_CHECKER" >${TMPDIR:-/tmp}/chain_set_inclusion_qg_lib.log 2>&1; then
        log_ok "STEP 5.72: UAC chain_env MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES ⊇ GAS_FEE_CHAIN_START_DATES"
    else
        log_fail "STEP 5.72: UAC chain_env inclusion invariant violated (DF-7). Output:"
        cat ${TMPDIR:-/tmp}/chain_set_inclusion_qg_lib.log
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
    if $PYTHON_CMD "$_UAC_INSTRUMENT_VALIDATOR_CHECKER" >${TMPDIR:-/tmp}/uac_instrument_validator_qg.log 2>&1; then
        log_ok "STEP 5.83: UAC InstrumentRecord hard-schema enforcement validator present (hard_schema Phase 1 guard)"
    else
        log_fail "STEP 5.83: UAC InstrumentRecord hard-schema enforcement MISSING or BROKEN:"
        cat ${TMPDIR:-/tmp}/uac_instrument_validator_qg.log
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
    if $PYTHON_CMD "$_UAC_SOURCE_CAPABILITY_CHECKER" "$WORKSPACE_ROOT" >${TMPDIR:-/tmp}/uac_source_capability_qg.log 2>&1; then
        log_ok "STEP 5.85: UAC SourceCapability structured metadata present on all venues"
    else
        log_fail "STEP 5.85: SourceCapability instances missing chain= or kind= kwargs:"
        cat ${TMPDIR:-/tmp}/uac_source_capability_qg.log
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
    if $PYTHON_CMD "$_UAC_CASSETTE_LINKAGE_CHECKER" >${TMPDIR:-/tmp}/uac_cassette_linkage_qg.log 2>&1; then
        log_ok "STEP 5.86: UAC cassette→prod-consumer linkage OK (no unallowlisted orphans)"
    else
        log_fail "STEP 5.86: Unallowlisted orphan cassette(s) found:"
        cat ${TMPDIR:-/tmp}/uac_cassette_linkage_qg.log
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
    if $PYTHON_CMD "$_UAC_PROD_URL_CHECKER" --warn-only >${TMPDIR:-/tmp}/uac_prod_url_coverage_qg.log 2>&1; then
        if grep -q "STEP 5.87.*WARN" ${TMPDIR:-/tmp}/uac_prod_url_coverage_qg.log 2>/dev/null; then
            log_warn "STEP 5.87: prod-URL→cassette coverage gap (run scripts/check_prod_url_cassette_coverage.py for full list)"
        else
            log_ok "STEP 5.87: All prod URL hosts have cassette coverage or are allowlisted"
        fi
    else
        log_warn "STEP 5.87: prod_url_has_cassette checker error:"
        cat ${TMPDIR:-/tmp}/uac_prod_url_coverage_qg.log
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
            --workspace-root "$REPO_ROOT" --scope "$_BE_REPO" "${_BE_SRC_ARG[@]}" >${TMPDIR:-/tmp}/bar_edge_open_ingestion_qg.log 2>&1; then
        log_ok "STEP 5.92: No NEW open-edge (left) bar ingestion (closed candles stamped on the right/close edge)"
    else
        log_fail "STEP 5.92: NEW open-edge (left) bar ingestion site (not baselined). Use the vendor close field or compute_bar_close_boundary(open_ts, timeframe) → t_close:"
        cat ${TMPDIR:-/tmp}/bar_edge_open_ingestion_qg.log
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
            --workspace-root "$REPO_ROOT" --scope "$_CM_REPO" "${_CM_SRC_ARG[@]}" >${TMPDIR:-/tmp}/canonical_model_regressions_qg.log 2>&1; then
        log_ok "STEP 5.93: No NEW coarse pipeline_mode / exact-coarse reader / Era-A chain-write regressions"
    else
        log_fail "STEP 5.93: NEW canonical-model regression (not baselined). Use source-aware batch_<source> / prefix-match readers / Era-B data_type=trades for chains:"
        cat ${TMPDIR:-/tmp}/canonical_model_regressions_qg.log
        exit 1
    fi
fi

# ── STEP 5.94: try/except-ImportError fallback-import ratchet ─────────────────
# Library-repo parity with base-service.sh STEP 5.94 (no-empty-fallbacks.mdc §
# "No try/except ImportError Fallbacks" — applies to ALL tiers, no exception).
# Baseline-ratchet: no_fallback_imports_baseline.yaml. Per-line opt-out:
# `# noqa: fallback-import` + a one-line reason.
# SSOT: harden_grepable_rules_into_ci_gates_2026_06_02.md Phase 3.
_NOFB_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_no_fallback_imports.py"
if [ -f "$_NOFB_CHECKER" ]; then
    _FB_REPO=$(basename "$PROJECT_ROOT")
    if "${PYTHON_CMD:-python3}" "$_NOFB_CHECKER" \
            --workspace-root "$REPO_ROOT" --scope "$_FB_REPO" >${TMPDIR:-/tmp}/no_fallback_imports_qg.log 2>&1; then
        log_ok "STEP 5.94: No NEW try/except-ImportError fallback-import shims (baseline-ratchet, no-empty-fallbacks)"
    else
        log_fail "STEP 5.94: NEW try/except-ImportError fallback-import shim (not baselined). Import directly + declare the dep in pyproject, or add '# noqa: fallback-import' with a one-line reason:"
        cat ${TMPDIR:-/tmp}/no_fallback_imports_qg.log
        exit 1
    fi
fi

# ── STEP 5.95: ruff DTZ (UTC-datetime) + TID251 (cloud-SDK) count ratchet ─────
# Library-repo parity with base-service.sh STEP 5.95. CLAUDE.md "UTC datetimes
# always" (pinned DTZ001-007/011/012/901) + "Cloud-agnostic I/O" (TID251 bans
# google.cloud/boto3; UTL cloud_interface/ wrapper internals exempt by path).
# Baseline-ratchet: ruff_rule_ratchet_baseline.yaml. Config SSOT:
# scripts/pyproject-templates/canonical-tool-sections.toml.
# SSOT: harden_grepable_rules_into_ci_gates_2026_06_02.md Phase 3.
_RUFFRR_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_ruff_rule_ratchet.py"
if [ -f "$_RUFFRR_CHECKER" ]; then
    _RR_REPO=$(basename "$PROJECT_ROOT")
    if "${PYTHON_CMD:-python3}" "$_RUFFRR_CHECKER" \
            --workspace-root "$REPO_ROOT" --scope "$_RR_REPO" >${TMPDIR:-/tmp}/ruff_rule_ratchet_qg.log 2>&1; then
        log_ok "STEP 5.95: No NEW naive-datetime (DTZ) / direct cloud-SDK (TID251) sites (baseline-ratchet)"
    else
        log_fail "STEP 5.95: NEW naive-datetime (DTZ) / direct cloud-SDK (TID251) site (not baselined). Use datetime.now(timezone.utc) / get_storage_client()/get_secret_client(), or a ruff '# noqa: <code>' with a one-line reason:"
        cat ${TMPDIR:-/tmp}/ruff_rule_ratchet_qg.log
        exit 1
    fi
fi

# ── STEP 5.96: blank asset_group at record_captured callsites ratchet ─────────
# Library-repo parity gate. `asset_group=""` / `asset_group=''` is banned —
# blank asset_group produces silent cross-asset manifest confusion. Shrinking
# ratchet: no_blank_asset_group_baseline.yaml. Per-line opt-out:
# `# noqa: blank-asset-group  <reason>` with a one-line reason on the flagged line.
# SSOT: data_completion_to_100_all_ag_2026_06_21.md task 042.
_BAG_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_no_blank_asset_group.py"
if [ -f "$_BAG_CHECKER" ]; then
    _BAG_REPO=$(basename "$PROJECT_ROOT")
    if "${PYTHON_CMD:-python3}" "$_BAG_CHECKER" \
            --workspace-root "$REPO_ROOT" --scope "$_BAG_REPO" >${TMPDIR:-/tmp}/no_blank_asset_group_qg.log 2>&1; then
        log_success "STEP 5.96: No NEW blank asset_group at record_captured callsites (baseline-ratchet)"
    else
        log_fail "STEP 5.96: NEW blank asset_group callsite — use a non-blank asset_group or add '# noqa: blank-asset-group  <reason>' on the same line:"
        cat ${TMPDIR:-/tmp}/no_blank_asset_group_qg.log
        exit 1
    fi
fi

# ── STEP 5.101: .get("key", "") empty-string-fallback ratchet ─────────────────
# Library-repo parity with base-service.sh STEP 5.101. "Empty string fallback —
# fail fast": a dict `.get("key", "")` call silently swaps a genuinely-missing/
# error-worthy field for an empty string instead of failing loud. Baseline-
# ratchet: no_empty_string_fallback_baseline.yaml. Per-line opt-out (already
# used at ~250 sites fleet-wide): `# noqa: qg-empty-fallback` + a one-line reason.
# SSOT: plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md.
_ESF_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_no_empty_string_fallback.py"
if [ -f "$_ESF_CHECKER" ]; then
    _ESF_REPO=$(basename "$PROJECT_ROOT")
    if "${PYTHON_CMD:-python3}" "$_ESF_CHECKER" \
            --workspace-root "$REPO_ROOT" --scope "$_ESF_REPO" >${TMPDIR:-/tmp}/no_empty_string_fallback_qg.log 2>&1; then
        log_ok "STEP 5.101: No NEW .get(\"key\", \"\") empty-string-fallback sites (baseline-ratchet)"
    else
        log_fail "STEP 5.101: NEW .get(\"key\", \"\") empty-string-fallback site (not baselined). Rewrite to fail fast (raise, or return None and let the caller decide), or add '# noqa: qg-empty-fallback' with a one-line reason:"
        cat ${TMPDIR:-/tmp}/no_empty_string_fallback_qg.log
        exit 1
    fi
fi

# ── STEP 5.102: every pytest.xfail / unconditional @pytest.mark.skip must cite a tracked slug ─
# Library-repo parity with base-service.sh STEP 5.107. Standing rule (operator
# finding 2026-08-08, "tests weakened rather than fixed" sweep): an xfail with a
# good reason and no remediation todo is indistinguishable, six months later,
# from coverage that was never written. SHRINKING ratchet:
# xfail_skip_tracked_baseline.yaml (43 entries at bootstrap).
_XST_CHECKER="${REPO_ROOT}/unified-trading-pm/scripts/quality_gates/check_xfail_skip_tracked.py"
if [ -f "$_XST_CHECKER" ]; then
    _XST_REPO=$(basename "$PROJECT_ROOT")
    if "${PYTHON_CMD:-python3}" "$_XST_CHECKER" \
            --workspace-root "$REPO_ROOT" --scope "$_XST_REPO" >${TMPDIR:-/tmp}/xfail_skip_tracked_qg.log 2>&1; then
        if grep -q '^\[WARN\]' ${TMPDIR:-/tmp}/xfail_skip_tracked_qg.log 2>/dev/null; then
            log_warn "STEP 5.102: $(grep -c '^\[WARN\]' ${TMPDIR:-/tmp}/xfail_skip_tracked_qg.log) baselined untracked xfail/skip marker(s) (pending_removal — must cite a tracked slug or be fixed); 0 new"
        else
            log_ok "STEP 5.102: No NEW untracked xfail/skip markers (every xfail/skip cites a tracked plan/issue slug)"
        fi
    else
        log_fail "STEP 5.102: NEW untracked xfail/skip marker — every pytest.xfail / unconditional @pytest.mark.skip reason must cite a tracked plan/issue slug (xfail_skip_tracked_baseline.yaml is a SHRINKING ratchet, never grow it):"
        cat ${TMPDIR:-/tmp}/xfail_skip_tracked_qg.log
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
    _ACT_LOG="$(mktemp ${TMPDIR:-/tmp}/act-output.XXXXXX)"
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

# ── STEP 5.97 — DeFi contract-address citation ratchet (library repos) ───────
# Ported from base-service.sh so the gate ALSO runs for LIBRARY repos — critically
# unified-api-contracts, whose registry/ is the checker's PRIMARY documented target
# (the defi_address_citation_baseline.yaml seed of 138 was UAC's). base-library.sh
# never ran it before, so UAC's baseline was UNENFORCED — a new uncited on-chain
# address could land silently. Per-repo SHRINKING count ratchet; per-line citation
# `# DERIVED <YYYY-MM-DD> from <chain> <source>` or exemption `# QG-allow: defi-citation`.
# Non-UAC libraries have no registry/ → checker scans repo → 0 → no-op pass.
# SSOT: defi_onchain_derivable_values_and_date_drift_2026_06_20.md Phase 5.
_DC_WS="${WORKSPACE_ROOT:-$(cd "$PROJECT_ROOT/.." && pwd)}"
_DEFI_CITE_CHECKER="${_DC_WS}/unified-trading-pm/scripts/quality_gates/check_defi_address_citations.py"
if [ -f "$_DEFI_CITE_CHECKER" ]; then
    _DC_REPO=$(basename "$PROJECT_ROOT")
    if $PYTHON_CMD "$_DEFI_CITE_CHECKER" --workspace-root "$_DC_WS" --scope "$_DC_REPO" >${TMPDIR:-/tmp}/defi_address_citations_qg.log 2>&1; then
        if grep -q '^\[WARN\]' ${TMPDIR:-/tmp}/defi_address_citations_qg.log 2>/dev/null; then
            log_warn "STEP 5.97: $(grep -c '^\[WARN\]' ${TMPDIR:-/tmp}/defi_address_citations_qg.log) baselined uncited DeFi address(es); 0 new (ratchet down when citations are back-filled)"
        else
            log_success "STEP 5.97: No new uncited DeFi contract addresses (citation ratchet)"
        fi
    else
        log_fail "STEP 5.97: NEW uncited Ethereum contract address (not in defi_address_citation_baseline.yaml). Add \`# DERIVED <YYYY-MM-DD> from <chain> <source>\` on the same line, or \`# QG-allow: defi-citation — <reason>\` for factory-deployed pool addresses:"
        cat ${TMPDIR:-/tmp}/defi_address_citations_qg.log
        log_fail "         Baseline: unified-trading-pm/scripts/quality_gates/defi_address_citation_baseline.yaml (NEVER raise a count)"
        exit 1
    fi
else
    log_success "STEP 5.97: skipped (checker not yet provisioned in this repo's PM checkout)"
fi

# ── DURATION CHECK ───────────────────────────────────────────────────────────
# IGNORE_TIMEOUT honoured (mirror of base-service.sh): QG_PROFILE=1 sets it so a slow
# single-core profile run cannot false-fail the meta-gate; unset → unchanged behaviour.
MAX_DURATION=${MAX_DURATION:-300}
QG_END=$(date +%s); DUR=$((QG_END - QG_START))
# Governor queue-wait excluded from billable time — mirror of base-service.sh
# (qg_host_governor_severe_contention_2026_07_13.md). 0 when ungoverned/uncontended.
DUR_WALL_BILLABLE=$(( DUR - ${QG_GOVERNOR_WAIT_SECONDS:-0} ))

# ── BILLABLE TIME IS CPU-SECONDS, NOT WALL (2026-08-10) ──────────────────────
# Wall clock measures how busy the HOST was, not how much work this gate did. Subtracting the
# governor's explicit queue-wait does not fix that: time spent DESCHEDULED while peers saturate
# the CPU is still counted as work. Measured on a dev laptop the same PM gate reported 602s
# "work" under 11 concurrent quickmerges against a 600s cap -- a 0.3% overshoot that was pure
# contention, surfaced to the agent as a content failure, and whose retry cost another full
# gate and made the next run likelier to trip. That is the livelock shape this whole gate
# family exists to avoid.
#
# CPU-seconds are invariant under contention: a gate that burns 370 CPU-seconds burns 370
# whether it runs alone or against eleven peers -- only the wall time moves. This also makes
# the codex's "organically outgrows the budget ON A QUIET HOST" test (quality-gates.md
# "Bump MAX_DURATION ...") MEASURABLE rather than a human judgement about how busy the box was:
# real growth still trips the cap, load no longer does.
#
# `times`'s second line is cumulative user+sys for children this shell has waited for. It MUST
# be captured by REDIRECTION -- inside `$(...)` the builtin runs in a SUBSHELL with its own
# accounting and reports 0m0.000s, i.e. a zero-second budget that can never trip. Verified both
# ways before adopting (0.787s via redirect vs 0.000s via command substitution).
_qg_cpu_file="${TMPDIR:-/tmp}/qg-cpu-$$"
times > "$_qg_cpu_file" 2>/dev/null || true
DUR_CPU=$(awk 'NR==2 { t=0; for (i=1;i<=NF;i++) { split($i,p,"m"); sub(/s$/,"",p[2]); t += p[1]*60 + p[2] } printf "%d", t }' "$_qg_cpu_file" 2>/dev/null)
rm -f "$_qg_cpu_file"
# Fall back to the wall figure if CPU accounting is unavailable or implausible: a silent 0 would
# disable the cap entirely, which is worse than the contention false-positive it replaces.
if [ -n "${DUR_CPU:-}" ] && [ "${DUR_CPU:-0}" -gt 0 ] 2>/dev/null; then
  DUR_BILLABLE=$DUR_CPU; _qg_dur_basis="CPU"
else
  DUR_BILLABLE=$DUR_WALL_BILLABLE; _qg_dur_basis="wall(CPU unavailable)"
fi
# The wall clock is kept ONLY as a hang detector, deliberately loose -- a gate stuck on a lock
# or a dead network call burns no CPU and would otherwise never trip anything.
MAX_WALL=${MAX_WALL:-$(( MAX_DURATION * 4 ))}
[ "${IGNORE_TIMEOUT:-false}" != "true" ] && [ $DUR_BILLABLE -gt $MAX_DURATION ] && { log_fail "Quality gates must complete in <${MAX_DURATION}s (${DUR_BILLABLE}s ${_qg_dur_basis} work; ${DUR}s wall incl. ${QG_GOVERNOR_WAIT_SECONDS:-0}s governor queue-wait)"; exit 1; }
[ "${IGNORE_TIMEOUT:-false}" != "true" ] && [ $DUR -gt $MAX_WALL ] && { log_fail "Quality gates wall-clock ceiling ${MAX_WALL}s exceeded (${DUR}s wall, only ${DUR_BILLABLE}s ${_qg_dur_basis} work) -- suspected HANG, not load"; exit 1; }
echo -e "\n${GREEN}======================================================================"
echo -e "✅ ALL QUALITY GATES PASSED (${DUR}s)${NC}"
# ── QG SENTINEL (SHA fingerprint for quickmerge --agent fast-path) — mirror of
# base-service.sh. Library repos were MISSING this write (only the content sentinel
# below), so `quickmerge --agent` always saw .qg_last_passed_sha "missing" and hard-refused
# every LIBRARY repo fleet-wide. H5: do NOT refresh on a content-sentinel HIT (a HIT skipped
# the tests/typecheck phases; refreshing would let quickmerge ship without re-running tests).
# Written to PROJECT_ROOT (the gated repo root — where quickmerge --agent reads it), same dir
# as the content sentinel below. Guarded identically to that write (full green: tests ran, not quick).
# SENTINEL CONTRACT (HARD, 2026-06-10): QG_FAST (the future change-scoped fast tier) is excluded
# like QG_SLICE — partial-surface runs must NEVER write this file (mirror of base-service.sh).
# SENTINEL CONTRACT (parity with base-service.sh, WS-L #1014): write ONLY on a COMPLETE green run.
# A partial-surface run (--skip-typecheck / --test=skip-lint / --act / --quick / a QG_SLICE / QG_FAST)
# must NEVER write the sentinel, or quickmerge --agent would fast-green + ship a tree the full gate
# never verified. (Was missing SKIP_TYPECHECK/RUN_LINT/ACT_MODE → --skip-typecheck wrote it anyway.)
if { { [ "${QUICK_MODE:-false}" = false ] && [ "${RUN_TESTS:-false}" = true ] && [ "${RUN_LINT:-false}" = true ] && [ "${SKIP_TYPECHECK:-false}" != true ] && [ "${ACT_MODE:-false}" != true ] && [ -z "${QG_SLICE:-}" ] && [ -z "${QG_FAST:-}" ]; } || [ "${_QG_DOCS_ONLY:-false}" = true ]; } && [ "${_QG_SENTINEL_HIT:-false}" != true ]; then
    git rev-parse HEAD > "${PROJECT_ROOT}/.qg_last_passed_sha" 2>/dev/null \
        && echo "Sentinel written: .qg_last_passed_sha=$(cat "${PROJECT_ROOT}/.qg_last_passed_sha")" \
        || echo "Warning: could not write .qg_last_passed_sha (non-git dir?)"
    # Configuration binding (qg_sentinel_environment_blind_2026_07_23.md item 2) — mirror
    # of base-service.sh: append (not overwrite) the resolved ENVIRONMENT/DEPLOYMENT_ENV so
    # quickmerge's sentinel check can refuse a config mismatch. `head -1` (every SHA reader)
    # is unaffected; an old bare-SHA sentinel still parses correctly.
    { printf 'ENVIRONMENT=%s\n' "${ENVIRONMENT:-}"; printf 'DEPLOYMENT_ENV=%s\n' "${DEPLOYMENT_ENV:-}"; } \
        >> "${PROJECT_ROOT}/.qg_last_passed_sha" 2>/dev/null || true
fi
# Green content sentinel (qg-repo-green-sentinel): record on a full green so an
# unchanged tree skips the heavy phases next run. See base-service.sh for rationale.
if [ "${#_QG_CONTENT_HASH}" -eq 64 ] && { { [ "${QUICK_MODE:-false}" = false ] && [ "${RUN_TESTS:-false}" = true ] && [ "${RUN_LINT:-false}" = true ] && [ "${SKIP_TYPECHECK:-false}" != true ] && [ "${ACT_MODE:-false}" != true ] && [ -z "${QG_SLICE:-}" ] && [ -z "${QG_FAST:-}" ]; } || [ "${_QG_DOCS_ONLY:-false}" = true ]; }; then
    echo "$_QG_CONTENT_HASH" > "${PROJECT_ROOT}/.qg_content_sentinel" 2>/dev/null \
        && echo "Green sentinel written: .qg_content_sentinel (unchanged tree → fast green next run)" || true
fi
