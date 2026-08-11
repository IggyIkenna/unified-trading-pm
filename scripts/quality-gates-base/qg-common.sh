#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# qg-common.sh — Shared foundation for all quality-gate base scripts.
# Owned by unified-trading-pm. Do NOT edit per-repo.
#
# Provides:
#   - Color variables (RED, GREEN, YELLOW, BLUE, NC)
#   - Logging functions: log_section, log_success, log_fail, log_warn, log_ok
#   - QG_START timestamp
#   - REPO_ROOT / PROJECT_ROOT / SCRIPT_DIR detection (from BASH_SOURCE chain)
#   - _ci-status-updater.sh source + _qg_record_failure trap
#   - run_timeout() portable timeout wrapper
#
# Sourced by: base-service.sh, base-library.sh, base-ui.sh, base-codex.sh
# Must be sourced BEFORE version-alignment-gate.sh (which depends on REPO_ROOT).
#
# IMPORTANT: This file must NOT contain any repo-type-specific logic
# (no pytest, no npm, no ruff config, no mode parsing).

# ── TIMESTAMP ────────────────────────────────────────────────────────────────
QG_START=$(date +%s)

# ── TMPDIR (shared_host_tmp_tmpfs_exhaustion_2026_07_08) ──────────────────────
# `/tmp` on the orchestrator host is a small tmpfs shared by every slot; a single
# tmp_path-heavy pytest run can leave hundreds of MB behind, and several slots'
# concurrent QG runs exhaust it within minutes — spurious ENOSPC test failures
# (unrelated to the change under review) and, once, the Claude Code harness's own
# /tmp-backed Bash-tool output capture. Default every base-*.sh's TMPDIR (pytest's
# tmp_path, RUFF_CACHE_DIR, BASEDPYRIGHT_CACHE_DIR, qg-host-governor's token dir all
# key off it) to a writable, spacious mount unless the caller already set one — every
# consumer already does `${TMPDIR:-/tmp}`, so this is a single control point.
# NOTE: `/` (and `/var/tmp` under it) is mounted read-only on this host (`ro`,
# errors=remount-ro) — `$HOME` (under the separate `rw` /home mount, ~95G free) is the
# writable large-disk target, mirroring the existing QG_CACHE_ROOT convention below and
# the manual workaround recorded in the issue doc.
export TMPDIR="${TMPDIR:-${HOME}/.cache/qg-tmp}"
mkdir -p "$TMPDIR" 2>/dev/null || true

# ── COLORS ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ── LOGGING ──────────────────────────────────────────────────────────────────
log_section() { echo -e "\n${BLUE}── $1 ──${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_fail()    { echo -e "${RED}❌ $1${NC}"; }
log_warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_ok()      { :; }

# ── PROJECT / REPO ROOT DETECTION ────────────────────────────────────────────
# When a base-*.sh sources this file, the BASH_SOURCE stack is:
#   [0] = qg-common.sh  [1] = base-*.sh  [2] = caller stub (repo's quality-gates.sh)
# We derive PROJECT_ROOT by walking UP from the caller stub's directory to the
# nearest pyproject.toml (the repo boundary marker). This is more robust than
# `dirname dirname` because it:
#   - handles non-standard repo layouts (scripts/ nested deeper than 1 level)
#   - never jumps to a sibling worktree's root under .tabs/<N>/ per-tab layout
#   - resolves correctly under symlinked invocations
# If no caller stub (direct invocation), fall back to this file's own location.
_QG_CALLER="${BASH_SOURCE[2]:-${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}}"
QG_SCRIPT_DIR="$(cd "$(dirname "$_QG_CALLER")" && pwd)"
_qg_walk_up_to_pyproject() {
    local d="$1"
    while [[ "$d" != "/" && -n "$d" ]]; do
        # `.git` is the universal repo-boundary marker (every repo has one, Python or
        # not); `pyproject.toml` alone under-detects UI/Node repos, which have neither —
        # the walk would then continue PAST the repo root and match a workspace-level
        # pyproject.toml several directories up (e.g. the bare workspace root's own
        # `.venv-workspace` config), misresolving PROJECT_ROOT to the wrong clone
        # entirely under the per-tab worktree layout. Checked together (not `.git` alone)
        # so existing Python repos keep matching at the same directory as before.
        [[ -f "$d/pyproject.toml" || -e "$d/.git" ]] && { echo "$d"; return 0; }
        d="$(dirname "$d")"
    done
    return 1
}
QG_PROJECT_ROOT="$(_qg_walk_up_to_pyproject "$QG_SCRIPT_DIR")" \
    || QG_PROJECT_ROOT="$(dirname "$QG_SCRIPT_DIR")"
unset -f _qg_walk_up_to_pyproject

# Export as the canonical names used by all base scripts
SCRIPT_DIR="${SCRIPT_DIR:-$QG_SCRIPT_DIR}"
PROJECT_ROOT="${PROJECT_ROOT:-$QG_PROJECT_ROOT}"
REPO_ROOT="${REPO_ROOT:-$(cd "$PROJECT_ROOT/.." 2>/dev/null && pwd)}"

# ── ENVIRONMENT RESOLUTION (single source of truth shared with quickmerge.sh) ──
# qg_sentinel_environment_blind_2026_07_23.md item 5: a standalone `quality-gates.sh`
# run and a quickmerge run must resolve the SAME ENVIRONMENT for the same branch
# context, or the two silently diverge (quickmerge forces development off any
# non-main branch; a standalone run previously left ENVIRONMENT unset and every
# downstream resolver, e.g. UTL's bucket_naming.py, defaulted to prod). qg-environment.sh
# is sourced from BOTH this file and quickmerge.sh so there is exactly one
# branch-conditional check to keep correct, not two copies that can drift apart again.
source "${BASH_SOURCE[0]%/*}/qg-environment.sh"
qg_resolve_environment "$PROJECT_ROOT"

# ── WORKTREE-IDENTITY GUARD (fail loud, never silently gate the wrong clone) ──
# Confirmed root cause (qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md):
# PROJECT_ROOT/REPO_ROOT/WORKSPACE_ROOT all use `${VAR:-fresh-derivation}` patterns that TRUST an
# inherited env value verbatim once one is set — a stale/persistent export (old shell profile,
# leftover tmux env) silently redirects every downstream `${WORKSPACE_ROOT}/<repo>/...` gate path
# at the WRONG clone (often the shared bare per-repo MAIN clone) instead of the worktree actually
# under test, even though SAME-repo-name checks (the SERVICE_NAME banner below) can't catch this —
# MAIN and the worktree share the same basename, only the toplevel path differs. This guard
# compares PROJECT_ROOT against the ACTUAL git toplevel for the invoking cwd and hard-fails on a
# mismatch, rather than silently proceeding to gate a different tree than the one requested.
if [[ -z "${QG_SKIP_WORKTREE_IDENTITY_GUARD:-}" ]]; then
    _qg_actual_toplevel="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    _qg_mismatch=""
    if [[ -n "$_qg_actual_toplevel" && "$PROJECT_ROOT" != "$_qg_actual_toplevel" ]]; then
        _qg_mismatch="PROJECT_ROOT='$PROJECT_ROOT' but the actual git worktree at cwd resolves to '$_qg_actual_toplevel'"
    elif [[ -n "$_qg_actual_toplevel" && -n "${WORKSPACE_ROOT:-}" ]]; then
        # WORKSPACE_ROOT is set by each repo's OWN quality-gates.sh (not derived here) and feeds
        # every `${WORKSPACE_ROOT}/<repo>/...` gate path in base-service.sh — check it separately
        # since PROJECT_ROOT can be correct while WORKSPACE_ROOT alone is stale/polluted.
        _qg_expected_ws_root="$(cd "$_qg_actual_toplevel/.." 2>/dev/null && pwd)"
        if [[ -n "$_qg_expected_ws_root" && "$WORKSPACE_ROOT" != "$_qg_expected_ws_root" ]]; then
            _qg_mismatch="WORKSPACE_ROOT='$WORKSPACE_ROOT' but the actual worktree's parent is '$_qg_expected_ws_root'"
        fi
        unset _qg_expected_ws_root
    fi
    if [[ -n "$_qg_mismatch" ]]; then
        echo "❌ [quality-gates] WORKTREE-IDENTITY MISMATCH: $_qg_mismatch." >&2
        echo "   An inherited env var (PROJECT_ROOT/REPO_ROOT/WORKSPACE_ROOT) is pointing this QG run" >&2
        echo "   at a DIFFERENT clone than the one being gated — unset it (check your shell" >&2
        echo "   profile/tmux env) and re-run." >&2
        echo "   SSOT: unified-trading-pm/plans/active/issues/qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md" >&2
        exit 1
    fi
    unset _qg_actual_toplevel _qg_mismatch
fi

# Banner — names the resolved repo so the operator can spot wrong-resolution at a glance.
# Critical under per-tab worktrees (.tabs/<N>/<repo>/) where sibling-worktree confusion
# was the root cause of slot_worktree_qg_repo_root_resolution_2026_05_11.
if [[ -z "${QG_BANNER_SUPPRESS:-}" ]]; then
    _qg_project_basename="$(basename "$PROJECT_ROOT")"
    if [[ -n "${SERVICE_NAME:-}" && "${SERVICE_NAME}" != "${_qg_project_basename}" ]]; then
        echo -e "\033[1;33m⚠️  [quality-gates] SERVICE_NAME='${SERVICE_NAME}' but PROJECT_ROOT='${PROJECT_ROOT}' (basename='${_qg_project_basename}') — possible sibling-worktree confusion\033[0m" >&2
    else
        echo -e "\033[0;34m[quality-gates] ${SERVICE_NAME:-${_qg_project_basename}} @ ${PROJECT_ROOT}\033[0m" >&2
    fi
    unset _qg_project_basename
fi
unset _QG_CALLER QG_SCRIPT_DIR QG_PROJECT_ROOT

# ── FLEET-WIDE PIP-AUDIT IGNORE LIST (single control point; item 252) ────────
# Add to base-service.sh _pa_extra / base-library.sh _pa_extra via ${QG_PIP_AUDIT_COMMON_IGNORES}.
# NEVER duplicate this list inline in a base script — update HERE ONLY.
#
# RESOLVED 2026-07-30 (slot-21): the list is now EMPTY. A full re-audit re-verified all 14 prior entries
# against each of the 23 Python repos' REAL current uv.lock version (direct `pip-audit -r` queries, not
# assumptions) — 4 were already fully moot (fleet never in the affected range: PYSEC-2024-277 joblib,
# PYSEC-2025-183 pyjwt, PYSEC-2026-161 starlette, GHSA-rpj2-4hq8-938g vcrpy), 1 was a duplicate alias
# (CVE-2026-45409 == PYSEC-2026-215), and the remaining 9 (PYSEC-2026-3447 setuptools, CVE-2026-3219/
# CVE-2026-6357/PYSEC-2026-196 pip, GHSA-6v7p-g79w-8964 msgpack, GHSA-4xgf-cpjx-pc3j pydantic-settings,
# CVE-2026-54911 ujson, CVE-2026-4539 pygments, PYSEC-2026-215 idna) were REAL gaps — every repo below
# the fix version was bumped (`uv lock --upgrade-package <name>`) and QG-validated before shipping.
# Fleet-wide re-verify confirmed 100% clean (every repo, every package, at/above fix version) before
# these ignores were dropped. Also found + fixed one gap no prior ignore covered at all:
# ibkr-gateway-infra was on fastapi 0.136.1/starlette 1.1.0 (missed by the 2026-07-28 fleet bump, which
# only touched repos declaring fastapi directly). Full audit + every shipped sha:
# cve_affected_pinned_deps_remediation_2026_06_18.md.
QG_PIP_AUDIT_COMMON_IGNORES=""

# ── QG PROFILER (opt-in; inactive unless QG_PROFILE=1) ────────────────────────
# No-op by default — zero behaviour change for normal runs across all repos. When
# QG_PROFILE=1, qg_prof appends one JSONL marker per phase/check boundary to
# $QG_PROFILE_FILE; an external profiler (scripts/quality_gates/profile_qg_resources.py)
# pairs start/end markers + samples RSS to produce a per-span wall+RAM JSON report.
# Output lives under .qg_profile/ (gitignored) so it never churns the worktree.
if [[ "${QG_PROFILE:-}" == "1" ]]; then
    QG_PROFILE_FILE="${QG_PROFILE_FILE:-${PROJECT_ROOT}/.qg_profile/markers.jsonl}"
    mkdir -p "$(dirname "$QG_PROFILE_FILE")" 2>/dev/null || true
    : > "$QG_PROFILE_FILE" 2>/dev/null || true
    # ${EPOCHREALTIME} (bash 5+) = portable sub-second; `date +%s.%N` emits a literal
    # "N" on BSD/macOS date (malformed JSONL). bash 3.2 (stock macOS) falls back to
    # whole seconds — valid JSON either way. (local↔CI parity, 2026-07-02)
    qg_prof() { printf '{"ts":%s,"event":"%s","name":"%s"}\n' "${EPOCHREALTIME:-$(date +%s)}" "${1:-}" "${2:-}" >> "$QG_PROFILE_FILE" 2>/dev/null || true; }
else
    qg_prof() { :; }
fi

# ── CI_STATUS HANDLER (shared, locked) ───────────────────────────────────────
# SSOT: _ci-status-updater.sh — unified name resolution + fcntl locking for all base scripts.
source "$(dirname "${BASH_SOURCE[0]}")/_ci-status-updater.sh"

_qg_record_failure() {
    local exit_code=$?
    [[ $exit_code -eq 0 ]] && return 0
    [[ "${GITHUB_ACTIONS:-}" == "true" ]] && return $exit_code
    _qg_update_ci_status_failing
    return $exit_code
}
# Default trap — base scripts may override (e.g. base-ui.sh adds _qg_kill_children)
trap _qg_record_failure EXIT

# ── PORTABLE TIMEOUT ─────────────────────────────────────────────────────────
# Wraps a command with a wall-clock timeout. Tries GNU timeout, gtimeout (macOS
# via coreutils), perl alarm, then bare execution as last resort.
run_timeout() {
    local secs=$1; shift
    if command -v timeout &>/dev/null; then timeout "$secs" "$@"
    elif command -v gtimeout &>/dev/null; then gtimeout "$secs" "$@"
    elif command -v perl &>/dev/null; then perl -e 'alarm shift; exec @ARGV' -- "$secs" "$@"
    else "$@"; fi
}

# ── QG STEP-RESULT CACHE (out-of-repo, ~/.cache/qg/<repo>/) ──────────────────
# Content-keyed skip cache for FIXED-COST gate steps (pip-audit / bandit /
# actionlint). Plan: plans/active/quality_gates_speed_and_config_ssot_2026_06_09.md
# Phase 3 (per-step cost reduction). Contract:
#   - Cache lives OUTSIDE the repo: ${QG_CACHE_ROOT:-$HOME/.cache/qg}/<repo-name>/.
#     MOVED out of ${PROJECT_ROOT}/.qg_cache 2026-06-10 same-day: an in-repo untracked
#     dir made EVERY post-QG tree dirty until the fleet gitignore rollout, which tripped
#     quickmerge's dirty-DEPS pre-flight for every CONSUMER of that repo (live incident:
#     deployment-api's ship blocked on deployment-service's .qg_cache). Out-of-repo =
#     no dirt, no gitignore rollout dependency, pre-flight clean by construction.
#     CI safety unchanged: the dir does not exist on a fresh CI runner → first run is
#     always a full run (correct by construction).
#   - A step stores its key ONLY after a CLEAN (green) run — failures / timeouts are
#     never cached, so a red step always re-runs.
#   - Bypass: QG_NO_CACHE=1 forces full runs (qg_cache_hit always reports miss).
if command -v sha256sum &>/dev/null; then
    _qg_hash() { sha256sum 2>/dev/null | awk '{print $1}'; }
else
    _qg_hash() { shasum -a 256 2>/dev/null | awk '{print $1}'; }   # stock macOS
fi
_QG_CACHE_DIR="${QG_CACHE_ROOT:-${HOME}/.cache/qg}/$(basename "${PROJECT_ROOT}")"

# Content key for a set of repo paths. Content-accurate (not mtime-based):
#   tracked-clean   → index blob hashes (`git ls-files -s`)
#   tracked-dirty   → worktree diff content (`git diff`)
#   untracked       → file names + contents (rare in the QG flow, but covered)
# `|| :` on every producer: CI runs under `set -eo pipefail`.
_qg_src_content_key() {
    {
        git ls-files -s -- "$@" 2>/dev/null || :
        git diff -- "$@" 2>/dev/null || :
        git ls-files -o --exclude-standard -- "$@" 2>/dev/null | LC_ALL=C sort \
            | while IFS= read -r _f; do printf '%s:' "$_f"; cat "$_f" 2>/dev/null || :; done
    } | _qg_hash
}

# ── EDITABLE-SIBLING CONTENT (green-sentinel gap fix, 2026-07-13 incident) ────
# A test can depend on a WORKSPACE SIBLING's live source via `uv pip install -e
# ../sibling` (setup.sh STEP 7/8b re-pins every sibling dep as editable) without
# THIS repo's own tree changing at all. Incident: unified-api-contracts's
# KNOWN_VENUE_TOKENS regressed under unified-trading-pm's
# test_capability_verdict_matrix.py while PM's own tree was untouched — the
# green content-sentinel (`_qg_content_hash`, below/base-service.sh /
# base-library.sh) only ever hashed THIS repo's tree, so it reported a false
# green and masked the regression (plans/active/issues/
# pm_qg_red_f47_venue_token_regression_2026_07_13.md). Fold each editable
# sibling's git state into the sentinel too, so a sibling regression invalidates
# it. Scope: committed HEAD + uncommitted TRACKED diff per sibling — untracked
# sibling files are out of scope (siblings are edited one-at-a-time per the
# /boot-per-shippable-unit discipline; the committed-change case this incident
# hit is the one that matters). Best-effort by design (matches the sentinel's
# own "malformed/empty hash never triggers a skip" contract): no venv, no
# editable installs, or a malformed direct_url.json all silently contribute
# nothing rather than failing the hash.
_qg_editable_sibling_hash() {
    local _site_pkgs
    _site_pkgs=$(find "${PROJECT_ROOT}/.venv/lib" -mindepth 1 -maxdepth 1 -name 'python3.*' 2>/dev/null | head -1)
    [ -n "$_site_pkgs" ] || return 0
    _site_pkgs="${_site_pkgs}/site-packages"
    [ -d "$_site_pkgs" ] || return 0
    local _durl _sib_path
    for _durl in "$_site_pkgs"/*.dist-info/direct_url.json; do
        [ -f "$_durl" ] || continue
        # Editable + file:// (local path) only — a PyPI/Artifact-Registry install has no
        # local sibling tree to drift, and direct_url.json's own format is stable pip/uv
        # output (not attacker-controlled), so this grep/sed match is sufficient — no jq
        # dependency added to a script every repo sources.
        grep -q '"editable"[[:space:]]*:[[:space:]]*true' "$_durl" 2>/dev/null || continue
        _sib_path=$(grep -oE '"url"[[:space:]]*:[[:space:]]*"file://[^"]+"' "$_durl" 2>/dev/null \
            | sed -E 's/.*"file:\/\/([^"]+)".*/\1/')
        [ -n "$_sib_path" ] && [ -d "${_sib_path}/.git" ] || continue
        git -C "$_sib_path" rev-parse HEAD 2>/dev/null
        git -C "$_sib_path" diff HEAD 2>/dev/null
    done
}

_qg_cache_age_hours() {  # $1=cache name → prints integer age in hours; rc 1 if absent
    local _f="${_QG_CACHE_DIR}/$1" _mt
    [ -f "$_f" ] || return 1
    # GNU (Linux) first, BSD (macOS) fallback. `stat -f %m` on GNU coreutils is `--file-system` + an
    # invalid format → exits 0 emitting a filesystem dump (NOT the mtime), so a BSD-first order never
    # reaches the GNU form on Linux and feeds garbage to the arithmetic below (syntax error). Mirror
    # the correct order already used in verify-slot-host-symmetry.sh.
    _mt=$(stat -c %Y "$_f" 2>/dev/null || stat -f %m "$_f" 2>/dev/null) || return 1
    echo $(( ( $(date +%s) - _mt ) / 3600 ))
}

qg_cache_hit() {  # $1=name $2=key [$3=max_age_hours] → rc 0 = HIT (safe to skip step)
    [ "${QG_NO_CACHE:-0}" = "1" ] && return 1
    local _f="${_QG_CACHE_DIR}/$1"
    [ -f "$_f" ] || return 1
    [ -n "$2" ] || return 1                                  # malformed key never hits
    [ "$(cat "$_f" 2>/dev/null)" = "$2" ] || return 1
    if [ -n "${3:-}" ]; then
        local _age
        _age=$(_qg_cache_age_hours "$1") || return 1
        [ "$_age" -lt "$3" ] || return 1                     # stale → re-run (cron bound)
    fi
    return 0
}

qg_cache_store() {  # $1=name $2=key — call ONLY after a clean/green step run
    mkdir -p "$_QG_CACHE_DIR" 2>/dev/null || return 0
    printf '%s' "$2" > "${_QG_CACHE_DIR}/$1" 2>/dev/null || :
}

# ── venv freshness ────────────────────────────────────────────────────────────
# Fail closed when .venv EXISTS but has drifted from uv.lock. This is the same
# reasoning as each base's "no usable .venv/bin/python" abort, one step further
# along: gating against the WRONG dependency set is as meaningless as gating
# against the wrong interpreter, but it is far harder to notice.
#
# Measured 2026-08-11 (fleet_venv_drift_after_pull_no_resync_2026_08_11.md):
# agent-orchestrator carried fastapi 0.136.3 against a pyproject requiring
# >=0.137.0 (lock pinned 0.140.7), so `from fastapi.routing import
# iter_route_contexts` — reached via UTL from tests/conftest.py — raised
# ImportError and the ENTIRE pytest suite failed to COLLECT. The gate ran every
# other check around it and reported one failed pytest step, which reads as a code
# defect rather than an environment one. A sweep the same day found 162/216 local
# slot venvs and 135/194 on the orchestrator VM drifted, because
# slot-cron-ff-pull.sh keeps CODE current and nothing re-syncs the environment
# after a pull moves uv.lock.
#
# DEFINED HERE, CALLED BY THE BASES — never invoked at source time: quickmerge.sh
# also sources this file for helpers, and in isolated-worktree mode its .venv is a
# symlink into a cache that may be unprovisioned. Aborting there would break
# shipping, which is not what this check is for.
#
# `-f uv.lock` is load-bearing, not defensive: with no lockfile the command fails
# with "Unable to find lockfile" — a MISSING LOCK, not a stale env — which would
# abort every lockless repo (measured: unified-trading-system-ui, a TS repo
# carrying a pyproject.toml but no uv.lock).
# NOTE: PROJECT_ROOT, never REPO_ROOT — in this codebase REPO_ROOT is the WORKSPACE dir
# ($PROJECT_ROOT/..), so an earlier version of this function looked for
# <workspace>/uv.lock, never found one, and silently returned 0 for every repo. A check
# that no-ops is worse than no check: it reports green and looks installed.
qg_assert_venv_fresh() {
    [ "${QG_ALLOW_STALE_VENV:-0}" = "1" ] && return 0
    [ -f "${PROJECT_ROOT:-.}/uv.lock" ] || return 0
    [ -x "${PROJECT_ROOT:-.}/.venv/bin/python" ] || return 0
    command -v uv >/dev/null 2>&1 || return 0
    # Read-only: --check never writes the env and --frozen never touches the lock.
    # ~50ms on an in-sync tree, so this costs nothing in the common case.
    (cd "${PROJECT_ROOT:-.}" && uv sync --frozen --check >/dev/null 2>&1) && return 0

    # WARN-ONLY BY DEFAULT (downgraded 2026-08-11, same day it shipped, on measurement).
    # Blocking here is not yet safe fleet-wide: unified-trading-pm re-drifts its OWN venv
    # across a gate run — verified by a controlled sync -> clean -> gate(exit 0) -> STALE
    # cycle — so a blocking check would stop PM from ever gating green. Mechanism: `uv sync`
    # regenerates uv.lock with editable-dep version churn, slot-cron-ff-pull.sh's [auto-clean]
    # reverts that with `git checkout -- uv.lock` (uv.lock content unchanged in git but its
    # mtime moves), and the venv is then consistent with the DISCARDED lock rather than the
    # committed one. Measured blast radius: 2 of 215 local venvs re-drift within an hour, both
    # unified-trading-pm.
    #
    # The signal is still worth printing everywhere — this is the class that let
    # agent-orchestrator sit on fastapi 0.136.3 against a lock pinning 0.140.7 with the whole
    # suite unable to collect. agent-orchestrator's own gate keeps a BLOCKING copy
    # (agent-orchestrator@f9a61ebf62) because it was verified there and does not self-drift.
    # Flip this to blocking fleet-wide with QG_ENFORCE_FRESH_VENV=1 once the PM lock-churn
    # cycle is fixed.
    echo "⚠ WARN — .venv is STALE against uv.lock in ${PROJECT_ROOT:-$PWD} (run 'uv sync')." >&2
    echo "   Non-blocking: a stale venv can stop the suite COLLECTING, so treat a red pytest here" >&2
    echo "   as possibly environmental. Set QG_ENFORCE_FRESH_VENV=1 to make this abort." >&2
    if [ "${QG_ENFORCE_FRESH_VENV:-0}" = "1" ]; then
        echo "❌ quality gate ABORTED — QG_ENFORCE_FRESH_VENV=1 and .venv is stale." >&2
        exit 1
    fi
    return 0
}
