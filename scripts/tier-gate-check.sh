#!/usr/bin/env bash
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

tier_str = repo_info.get("arch_tier", "")
if not tier_str or not tier_str.startswith("T"):
    print(f"INFO: {repo} has no arch_tier — skipping tier gate check")
    sys.exit(0)

try:
    tier_n = int(tier_str[1:])
except ValueError:
    sys.exit(0)

if tier_n == 0:
    print(f"✓ {repo} is T0 — no lower tier to check")
    sys.exit(0)

prerequisite_tier = f"T{tier_n - 1}"
blocked = []

for r, info in repos.items():
    if not isinstance(info, dict):
        continue
    if info.get("arch_tier") != prerequisite_tier:
        continue
    status = info.get("ci_status") or "UNKNOWN"
    if status not in ("PASSING", "passing"):
        blocked.append(f"  {r} ({prerequisite_tier}): ci_status={status}")

if blocked:
    print(f"❌ TIER GATE BLOCKED: Cannot work on {repo} ({tier_str}) — {len(blocked)} {prerequisite_tier} repos not green:")
    for b in blocked:
        print(b)
    sys.exit(1)

print(f"✓ Tier gate open: all {prerequisite_tier} prerequisites passing for {repo} ({tier_str})")
PYEOF
