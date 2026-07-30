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
# RE-AUDITED 2026-07-30 (slot-21): every entry below was re-verified against the REAL current version
# in each of the 23 Python repos' uv.lock (not the version noted when the ignore was first added) via
# direct `pip-audit -r` queries against each observed version, cross-referenced with OSV alias data.
# Four entries this pass confirmed fully MOOT (the fleet's current versions were never in the affected
# range, or long past it) and were DROPPED with zero repo changes needed: PYSEC-2024-277 (joblib
# <=1.4.2, disputed — fleet is 1.5.3 everywhere), PYSEC-2025-183 (pyjwt <=2.10.1, disputed — fleet is
# 2.13.0 everywhere), PYSEC-2026-161 (starlette, fixed 1.0.1 — fleet's OLDEST is 1.1.0), GHSA-rpj2-4hq8-938g
# (vcrpy <8.2.1 — fleet is 8.2.1 everywhere, incl. ibkr-gateway-infra, the repo this was re-added for
# 2026-06-24). CVE-2026-45409 was confirmed an EXACT alias of PYSEC-2026-215 (same GHSA-65pc-fj4g-8rjx) —
# collapsed to one entry. Every remaining entry below is a REAL, currently-exploitable-per-repo gap (the
# ignore is doing real work, not masking nothing) with the actual fix version + the actual list of
# still-vulnerable repos measured this pass — see cve_affected_pinned_deps_remediation_2026_06_18.md for
# the full audit + per-repo bump tracking.
#
# PYSEC-2026-3447: setuptools <83.0.0 (TRANSITIVE build/packaging tool, not a runtime dep). Exploit
#   surface nil: setuptools runs only at image/build time to install first-party packages, never at
#   runtime on untrusted input. Fix: setuptools>=83.0.0. Still vulnerable (2026-07-30): 17 of 22 repos —
#   only e2e-testing/instruments-service/market-tick-data-service/system-integration-tests/
#   unified-trading-library are on 83.0.0. SUCCESSOR: bump the remaining 17 + drop this ignore.
# CVE-2026-3219 / CVE-2026-6357 / PYSEC-2026-196: pip <26.1.2 (TRANSITIVE — pip's own dependency-resolver
#   tar/zip handling + self-update check + console_scripts path sanitization). Fix: pip>=26.1.2. The
#   "blocked by the pinned vcrpy" note from 2026-06-05 is STALE — vcrpy is 8.2.1 fleet-wide now (see
#   GHSA-rpj2 above). Still vulnerable (2026-07-30): agent-orchestrator (26.1.1), greeks-service
#   (26.1.1), batch-live-reconciliation-service (26.0.1) — 3 of 22 repos; everyone else already resolved
#   to >=26.1.2 organically. SUCCESSOR: bump those 3 + drop these 3 ignores.
# GHSA-6v7p-g79w-8964: msgpack <1.2.1 (TRANSITIVE) — Unpacker re-used after an unpack error can SEGV.
#   Exploit surface nil: we never feed untrusted msgpack to an Unpacker and reuse it post-error. Fix:
#   msgpack>=1.2.1. Still vulnerable (2026-07-30): agent-orchestrator, strategy-service (2 of 22 repos).
#   SUCCESSOR: bump those 2 + drop this ignore.
# GHSA-4xgf-cpjx-pc3j: pydantic-settings <2.14.2 (TRANSITIVE) — NestedSecretsSettingsSource reads secret
#   VALUES from configured secrets_dir files. Exploit surface nil: secrets_dir is always a trusted
#   Secret-Manager mount, never untrusted input. Fix: pydantic-settings>=2.14.2. Still vulnerable
#   (2026-07-30): 16 of 21 repos carrying this dep (only e2e-testing/ml-service/system-integration-tests/
#   unified-trading-api are already >=2.14.2) — the BIGGEST remaining gap by repo count. SUCCESSOR: bump
#   the remaining 16 + drop this ignore.
# CVE-2026-54911 (= PYSEC-2026-2294): ujson <5.13.0 (TRANSITIVE) — dumps(reject_bytes=False) edge case
#   on bytes encoding. Exploit surface nil: we never serialize untrusted bytes with reject_bytes=False.
#   Fix: ujson>=5.13.0. Still vulnerable (2026-07-30): strategy-service only (1 of 4 repos carrying this
#   dep). SUCCESSOR: bump strategy-service + drop this ignore.
# CVE-2026-4539 (= PYSEC-2026-2987): pygments <2.20.0 (TRANSITIVE, NOT "workspace-global" as a prior
#   note claimed — that was a stale mischaracterization; a real fix has shipped since the 2026-05-20
#   review) — ReDoS in the archetype.py GUID lexer. Exploit surface nil: we never lex untrusted source
#   with pygments at runtime (it's a dev/doc-rendering dependency). Fix: pygments>=2.20.0. Still
#   vulnerable (2026-07-30): ibkr-gateway-infra, market-tick-data-service, unified-api-contracts,
#   unified-trading-library (4 of 22 repos). SUCCESSOR: bump those 4 + drop this ignore.
# PYSEC-2026-215 (alias CVE-2026-45409, GHSA-65pc-fj4g-8rjx): idna <3.15 (TRANSITIVE) — crafted input to
#   idna.encode(). Exploit surface nil: we parse only controlled/first-party hostnames. Fix: idna>=3.15
#   (NOT 3.18 as a prior note claimed — re-verified via direct pip-audit query: 3.15/3.16/3.18 all clean,
#   3.11/3.13 both flag this). Still vulnerable (2026-07-30): 13 of 22 repos. SUCCESSOR: bump the
#   remaining 13 + drop this ignore.
QG_PIP_AUDIT_COMMON_IGNORES="--ignore-vuln CVE-2026-4539 --ignore-vuln PYSEC-2026-215 --ignore-vuln CVE-2026-3219 --ignore-vuln CVE-2026-6357 --ignore-vuln GHSA-6v7p-g79w-8964 --ignore-vuln GHSA-4xgf-cpjx-pc3j --ignore-vuln CVE-2026-54911 --ignore-vuln PYSEC-2026-196 --ignore-vuln PYSEC-2026-3447"

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
