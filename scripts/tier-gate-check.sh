#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Tier gate enforcement: verify all repos at tier N-1 are passing before working on tier N.
# Usage: bash scripts/tier-gate-check.sh <repo_name> [--manifest path/to/workspace-manifest.json]
# Exit 0 = gate open, Exit 1 = blocked (some T(N-1) repo is not passing).
set -euo pipefail

REPO="${1:-}"
MANIFEST="workspace-manifest.json"

for arg in "$@"; do
    if [[ "$arg" == "--manifest" ]]; then
        MANIFEST_NEXT=true
    elif [[ "${MANIFEST_NEXT:-false}" == "true" ]]; then
        MANIFEST="$arg"
        MANIFEST_NEXT=false
    fi
done

if [ -z "$REPO" ]; then
    echo "Usage: bash scripts/tier-gate-check.sh <repo_name>" >&2
    exit 1
fi

if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: $MANIFEST not found" >&2
    exit 1
fi

python3 - "$REPO" "$MANIFEST" << 'PYEOF'
import json, sys

repo = sys.argv[1]
manifest_path = sys.argv[2]

with open(manifest_path) as f:
    manifest = json.load(f)

repos = manifest.get("repositories", {})

if repo not in repos:
    print(f"WARNING: {repo} not in manifest — skipping tier gate check")
    sys.exit(0)

repo_info = repos[repo]
if not isinstance(repo_info, dict):
    sys.exit(0)

# Read integer tier field (new SSOT); fall back to arch_tier for migration period
tier_n = repo_info.get("tier")
if tier_n is None:
    print(f"INFO: {repo} has no tier — skipping tier gate check")
    sys.exit(0)

if not isinstance(tier_n, int):
    print(f"INFO: {repo} tier={tier_n} is not an integer — skipping tier gate check")
    sys.exit(0)

# --- Check 1: All T(N-1) repos must be passing before working on T(N) ---
if tier_n == 0:
    print(f"OK: {repo} is T0 — no lower tier to check")
else:
    prerequisite_tier = tier_n - 1
    blocked = []

    for r, info in repos.items():
        if not isinstance(info, dict):
            continue
        r_tier = info.get("tier")
        if r_tier != prerequisite_tier:
            continue
        status = info.get("ci_status") or "UNKNOWN"
        if status not in ("PASSING", "passing"):
            blocked.append(f"  {r} (T{prerequisite_tier}): ci_status={status}")

    if blocked:
        print(f"TIER GATE BLOCKED: Cannot work on {repo} (T{tier_n}) — {len(blocked)} T{prerequisite_tier} repos not green:")
        for b in blocked:
            print(b)
        sys.exit(1)

    print(f"OK: Tier gate open: all T{prerequisite_tier} prerequisites passing for {repo} (T{tier_n})")

# --- Check 2: Every dependency D must have tier <= N ---
dep_violations = []
deps = repo_info.get("dependencies", [])
for dep in deps:
    dep_name = dep.get("name") if isinstance(dep, dict) else dep
    if not dep_name or dep_name not in repos:
        continue
    dep_info = repos[dep_name]
    if not isinstance(dep_info, dict):
        continue
    dep_tier = dep_info.get("tier")
    if dep_tier is None:
        continue  # skip repos with no tier (infrastructure, test)
    if not isinstance(dep_tier, int):
        continue
    if dep_tier > tier_n:
        dep_violations.append(f"  {dep_name} (T{dep_tier}) > {repo} (T{tier_n})")

if dep_violations:
    print(f"TIER DEP VIOLATION: {repo} (T{tier_n}) depends on higher-tier repos:")
    for v in dep_violations:
        print(v)
    sys.exit(1)

print(f"OK: All dependencies of {repo} (T{tier_n}) have tier <= {tier_n}")
PYEOF
