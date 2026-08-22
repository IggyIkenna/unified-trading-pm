#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Validate workspace-manifest.json structure and semver format.
# Usage: bash scripts/validate-manifest-json.sh [path/to/workspace-manifest.json]
# Exit 0 = valid, Exit 1 = invalid (prints error to stderr).
set -euo pipefail

MANIFEST="${1:-workspace-manifest.json}"

python3 - "$MANIFEST" << 'PYEOF'
import json, re, sys

path = sys.argv[1] if len(sys.argv) > 1 else "workspace-manifest.json"

try:
    with open(path) as f:
        d = json.load(f)
except json.JSONDecodeError as e:
    print(f"FATAL: {path} is not valid JSON: {e}", file=sys.stderr)
    sys.exit(1)
except OSError as e:
    print(f"FATAL: cannot open {path}: {e}", file=sys.stderr)
    sys.exit(1)

required = ["versions", "repositories", "staging_status", "staging_versions"]
missing = [k for k in required if k not in d]
if missing:
    print(f"FATAL: manifest missing required keys: {missing}", file=sys.stderr)
    sys.exit(1)

semver = re.compile(r"^\d+\.\d+\.\d+$")
for repo, ver in d.get("versions", {}).items():
    if repo.startswith("_"):
        continue
    if not semver.match(str(ver)):
        print(f"FATAL: versions['{repo}'] = {ver!r} is not valid semver", file=sys.stderr)
        sys.exit(1)

for repo, ver in d.get("staging_versions", {}).items():
    if repo.startswith("_"):
        continue
    if not semver.match(str(ver)):
        print(f"FATAL: staging_versions['{repo}'] = {ver!r} is not valid semver", file=sys.stderr)
        sys.exit(1)

print(f"Manifest valid: {len(d.get('versions', {}))} stable versions, {len(d.get('repositories', {}))} repos")
PYEOF
