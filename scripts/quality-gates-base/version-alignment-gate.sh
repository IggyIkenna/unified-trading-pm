#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# version-alignment-gate.sh — Shared version alignment check for all QG base scripts.
# Sourced by base-service.sh, base-library.sh, base-ui.sh, and infra-quality-gates.yml.
#
# Checks (local only — skipped in CI):
#   1. Branch commit drift: are you behind origin/<current-branch>?  → BLOCK (genuine stale checkout)
#   2. Self version drift: is your repo's version behind LDR?        → BLOCK only if also behind your
#   3. Dependency version drift: are deps' versions behind LDR?          branch; else WARN (nothing to fix).
#
# Compares against live-defi-rollout (LDR), not main. The main→LDR backmerge skips [skip ci]
# version-bump commits, so main's versions perpetually lead LDR — comparing vs main would WARN on
# every PM-on-LDR commit even when the agent is fully current. LDR is the integration source of truth
# for local dev; Phase-2 (version-out-of-source) retires this gate entirely. (WS-C P2 option-b)
#
# BLOCKS on a stale checkout (Check 1). Override: --skip-version-alignment (human-only, agents MUST NOT use).
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
    # True until Check 1 proves we're BEHIND our branch. When we're current with our branch, a
    # "version behind main" (Check 2-3) is purely the pending main→LDR backmerge (not a stale
    # checkout) → WARN, not BLOCK. (WS-L 2026-06-26: kills the recurring backmerge-lag false-block.)
    local _branch_current=true

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
            _branch_current=false
        fi
    fi

    # 2-3. Version drift: self + dependencies vs remote PM manifest on LDR.
    # Compare against live-defi-rollout (LDR) rather than main: the main→LDR backmerge
    # skips [skip ci] version-bump commits, so LDR's version surface perpetually lags main.
    # That lag is not the agent's to fix; comparing vs LDR gives a drift-free signal for
    # genuine stale-checkout detection. WS-L Phase-2 (version-out-of-source) retires this
    # gate entirely; this change is the cheap interim fix per option (b). (item: WS-C P2)
    (cd "$_pm_dir" && git fetch origin live-defi-rollout --quiet 2>/dev/null) || :
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
    result = subprocess.run(['git', '-C', str(pm_dir), 'show', 'origin/live-defi-rollout:workspace-manifest.json'],
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
        if [ "$_branch_current" = true ]; then
            # Current with our branch (Check 1 clean) ⇒ a local-version-behind-main is purely the
            # pending main→LDR backmerge, NOT a stale checkout — and nothing the agent can fix (the
            # backmerge bot reconciles it). WARN, don't block. The genuine stale-checkout case
            # (behind your branch) is the hard BLOCK in Check 1; quickmerge's dep-tier gate (STAGE
            # 1.6/1.7) is the precise dep-order guard. (WS-L 2026-06-26 backmerge-lag friction fix.)
            echo ""
            echo -e "${YELLOW}⚠️  VERSION ALIGNMENT (non-blocking): local manifest version trails LDR — you are current with origin/${_branch:-your branch}. Nothing to fix.${NC}"
            echo "$_ver_drift" | tail -n +2
        else
            echo ""
            echo -e "${RED}━━━ VERSION ALIGNMENT: Version Drift Detected ━━━${NC}"
            echo "$_ver_drift" | tail -n +2
            echo ""
            echo "  Your local checkout is STALE (behind your branch). Pull first:"
            echo "    cd unified-trading-pm && git pull origin main"
            echo "  Then: bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix"
            echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            _va_block=true
        fi
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
