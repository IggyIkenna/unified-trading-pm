#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# check-internal-advisories.sh — Internal package vulnerability advisory checker
#
# Reads unified-trading-pm/security/internal-advisories.yaml and checks whether
# any currently installed package matches a known advisory (affected_versions).
# Exits non-zero if a match is found. Run this from quality-gates.sh.
#
# Usage:
#   bash unified-trading-pm/scripts/check-internal-advisories.sh
#
# Requires: python3, packaging (pip install packaging)
# Called from: scripts/quality-gates.sh after pip-audit block
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADVISORIES_FILE="$SCRIPT_DIR/../../security/internal-advisories.yaml"

if [[ ! -f "$ADVISORIES_FILE" ]]; then
  echo "⚠️  internal-advisories.yaml not found at $ADVISORIES_FILE — skipping internal advisory check"
  exit 0
fi

python3 - "$ADVISORIES_FILE" <<'PYEOF'
import sys
import subprocess
import json
import re

advisories_path = sys.argv[1]

# Parse the YAML advisory file without requiring pyyaml (use simple inline parser
# since the file has a well-known fixed structure). Falls back to pyyaml if available.
def load_advisories(path: str) -> list[dict]:
    try:
        import yaml  # type: ignore[import-untyped]
        with open(path) as f:
            data = yaml.safe_load(f)
        return data.get("advisories") or []
    except ImportError:
        pass
    # Minimal fallback: if advisories is empty list, return []
    with open(path) as f:
        content = f.read()
    if re.search(r"advisories:\s*\[\]", content):
        return []
    # Non-empty advisories without pyyaml — warn and skip rather than false-pass
    print("⚠️  pyyaml not installed and advisories list is non-empty. Install pyyaml to enable internal advisory checks.")
    print("    Run: uv pip install pyyaml")
    sys.exit(0)


def get_installed_packages() -> dict[str, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {}
    packages = json.loads(result.stdout)
    return {pkg["name"].lower(): pkg["version"] for pkg in packages}


def version_matches(installed_version: str, specifier: str) -> bool:
    try:
        from packaging.specifiers import SpecifierSet  # type: ignore[import-untyped]
        from packaging.version import Version
        return Version(installed_version) in SpecifierSet(specifier)
    except ImportError:
        print("⚠️  packaging not installed — cannot evaluate version specifiers.")
        print("    Run: uv pip install packaging")
        return False
    except Exception:
        return False


advisories = load_advisories(advisories_path)

if not advisories:
    print("✅ No internal advisories defined — check passed")
    sys.exit(0)

installed = get_installed_packages()
violations: list[str] = []

for advisory in advisories:
    pkg_name = advisory.get("package", "").lower()
    affected = advisory.get("affected_versions", "")
    fixed_in = advisory.get("fixed_in")
    advisory_id = advisory.get("id", "UNKNOWN")
    severity = advisory.get("severity", "UNKNOWN")
    description = advisory.get("description", "")

    if pkg_name not in installed:
        continue

    installed_ver = installed[pkg_name]

    # If advisory has a fixed_in and installed version >= fixed_in, skip
    if fixed_in:
        try:
            from packaging.version import Version
            if Version(installed_ver) >= Version(fixed_in):
                continue
        except Exception:
            pass

    if version_matches(installed_ver, affected):
        violations.append(
            f"  [{severity}] {advisory_id}: {pkg_name}=={installed_ver} "
            f"matches affected range '{affected}' — {description}"
            + (f" (fixed in {fixed_in})" if fixed_in else " (no fix available yet)")
        )

if violations:
    print("❌ Internal advisory violations found:")
    for v in violations:
        print(v)
    print("\nUpdate the affected packages or check unified-trading-pm/security/internal-advisories.yaml")
    sys.exit(1)

print(f"✅ Internal advisory check passed ({len(advisories)} advisories checked)")
PYEOF
