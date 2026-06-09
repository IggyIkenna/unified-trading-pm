#!/usr/bin/env bash
# version-alignment-gate.sh — Shared version alignment check for all QG base scripts.
# Sourced by base-service.sh, base-library.sh, base-ui.sh, and infra-quality-gates.yml.
#
# Checks (local only — skipped in CI):
#   1. Branch commit drift: are you behind origin/<current-branch>?
#   2. Self version drift: is your repo's version behind staging/main?
#   3. Dependency version drift: are your deps' versions behind staging/main?
#
# BLOCKS by default. Override: --skip-version-alignment (human-only, agents MUST NOT use).
#
# Required variables (set by caller before sourcing):
#   SERVICE_NAME — repo name (e.g. instruments-service)
#   REPO_ROOT    — absolute path to the repo root
#
# Optional variables:
#   WORKSPACE_ROOT — workspace root (default: $REPO_ROOT/..)
#   SKIP_VERSION_ALIGNMENT — set to "true" to skip (parsed from --skip-version-alignment)

_run_version_alignment_gate() {
    local RED='\033[0;31m'
    local YELLOW='\033[0;33m'
    local NC='\033[0m'

    # Skip in CI — CI uses manifest directly, no local drift concerns
    if [[ -n "${GITHUB_ACTIONS:-}" || -n "${CI:-}" || -n "${CLOUD_BUILD:-}" ]]; then
        return 0
    fi

    if [[ "${SKIP_VERSION_ALIGNMENT:-false}" = "true" ]]; then
        echo -e "${YELLOW}⚠️  Version alignment SKIPPED (--skip-version-alignment)${NC}"
        return 0
    fi

    local _ws="${WORKSPACE_ROOT:-$(cd "$REPO_ROOT/.." && pwd)}"
    local _pm_manifest="$_ws/unified-trading-pm/workspace-manifest.json"
    local _pm_dir="$_ws/unified-trading-pm"
    local _va_block=false

    [[ ! -f "$_pm_manifest" || ! -d "$_pm_dir/.git" ]] && return 0

    # 1. Branch commit drift: am I behind on my current branch?
    local _branch
    _branch=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || :)
    if [ -n "$_branch" ]; then
        git -C "$REPO_ROOT" fetch origin "$_branch" --quiet 2>/dev/null || :
        local _behind
        _behind=$(git -C "$REPO_ROOT" rev-list HEAD..origin/"$_branch" --count 2>/dev/null || echo "0")
        if [ "$_behind" -gt 0 ] 2>/dev/null; then
            echo ""
            echo -e "${RED}━━━ VERSION ALIGNMENT: Branch Commit Drift ━━━${NC}"
            echo "  You are $_behind commit(s) behind origin/$_branch on ${SERVICE_NAME:-${PACKAGE_NAME:-unknown}}"
            echo "  Someone pushed to your branch. Pull first:"
            echo "    cd ${SERVICE_NAME:-${PACKAGE_NAME:-unknown}} && git pull origin $_branch"
            echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            _va_block=true
        fi
    fi

    # 2-3. Version drift: self + dependencies vs remote PM manifest
    (cd "$_pm_dir" && git fetch origin main --quiet 2>/dev/null) || :
    local _ver_drift
    _ver_drift=$(python3 -c "
import json, sys, subprocess
from pathlib import Path
pm_dir = Path('$_pm_dir')
repo = '${SERVICE_NAME:-${PACKAGE_NAME:-}}'
with open('$_pm_manifest') as f:
    local = json.load(f)
local_versions = local.get('versions', {})
repos_data = local.get('repositories', {})

# Self + dependencies
check_repos = [repo]
deps = [d.get('name', d) if isinstance(d, dict) else d for d in repos_data.get(repo, {}).get('dependencies', [])]
check_repos.extend(deps)

try:
    result = subprocess.run(['git', '-C', str(pm_dir), 'show', 'origin/main:workspace-manifest.json'],
                            capture_output=True, text=True, timeout=10)
    if result.returncode != 0: sys.exit(0)
    remote = json.loads(result.stdout)
except Exception: sys.exit(0)

remote_versions = remote.get('versions', {})
drifted = []

def pv(v):
    try:
        parts = [int(x) for x in str(v).split('.')[:3]]
        return tuple(parts + [0] * (3 - len(parts)))
    except Exception:
        return None

for r in check_repos:
    local_v = local_versions.get(r, '')
    main_v = remote_versions.get(r, '')
    label = '(self)' if r == repo else '(dependency)'
    # Compare LIKE-FOR-LIKE: local main-line 'versions' vs remote main-line
    # 'versions' (origin/main). Do NOT compare local 'versions' against remote
    # 'staging_versions' — staging legitimately LEADS main during every in-flight
    # LDR->staging->main promotion, so a cross-line compare false-blocked EVERY
    # dependent repo's local QG for the whole promotion window (e.g. uac 0.2.1 on
    # staging while 0.2.0 on main blocked all uac-dependent repos). Being behind
    # staging-but-current-with-main is normal: you build against main-line releases
    # / editable local path-source checkouts. The real signal we still catch: local
    # main-version behind the RELEASED main version => your local PM checkout is
    # stale, pull it. Only flag BEHIND; AHEAD is fine (quickmerge Stage 1.6 invariant).
    if main_v:
        pl, pm = pv(local_v), pv(main_v)
        if pl is not None and pm is not None and pl < pm:
            drifted.append(f'  {r} {label}: local={local_v} main={main_v}')

if drifted:
    print('DRIFT')
    for d in drifted: print(d)
" 2>/dev/null || :)

    if [ -n "$_ver_drift" ] && echo "$_ver_drift" | head -1 | grep -q "DRIFT"; then
        echo ""
        echo -e "${RED}━━━ VERSION ALIGNMENT: Version Drift Detected ━━━${NC}"
        echo "$_ver_drift" | tail -n +2
        echo ""
        echo "  Your local version is BEHIND the remote staging/main version."
        echo "  Fix: cd unified-trading-pm && git pull origin main"
        echo "  Then: bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        _va_block=true
    fi

    if [ "$_va_block" = true ]; then
        echo ""
        echo -e "${RED}❌ BLOCKED: Version alignment failed. Fix the drift above, then re-run.${NC}"
        echo "  Override: --skip-version-alignment (human-only — agents MUST NOT use this flag)"
        exit 1
    fi
}

# Run the check
_run_version_alignment_gate
