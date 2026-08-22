#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate that workspace constraints resolve without dependency conflicts.

1. Optionally regenerate workspace-constraints.toml from pyproject.toml (resolve-canonical-versions)
2. Run uv pip compile to verify no transitive conflicts
3. Optionally regenerate canonical-dependency-manifest.json

Usage:
    python validate-dependency-conflicts.py              # validate existing constraints
    python validate-dependency-conflicts.py --regenerate # regenerate constraints first
    python validate-dependency-conflicts.py --quiet

Exit: 0 = resolves, 1 = conflict or error.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", str(PM_ROOT.parent)))
RESOLVE_SCRIPT = PM_ROOT / "scripts" / "workspace" / "resolve-canonical-versions.py"
VALIDATE_SCRIPT = PM_ROOT / "scripts" / "workspace" / "validate-workspace-constraints.py"
GENERATE_CANONICAL = PM_ROOT / "scripts" / "manifest" / "generate_canonical_dependency_manifest.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regenerate", action="store_true", help="Run resolve-canonical-versions first")
    parser.add_argument("--quiet", "-q", action="store_true")
    parser.add_argument("--no-cache", action="store_true", help="Bypass validation cache, always run uv pip compile")
    args = parser.parse_args()
    regenerate: bool = cast(bool, args.regenerate)
    quiet: bool = cast(bool, args.quiet)
    no_cache: bool = cast(bool, args.no_cache)

    if regenerate:
        if not RESOLVE_SCRIPT.is_file():
            print(f"ERROR: {RESOLVE_SCRIPT} not found", file=sys.stderr)
            return 1
        r = subprocess.run(
            [sys.executable, str(RESOLVE_SCRIPT)], cwd=str(WORKSPACE_ROOT), capture_output=not quiet, text=True
        )
        if r.returncode != 0:
            if not quiet and r.stderr:
                print(r.stderr, file=sys.stderr)
            return 1

    if not VALIDATE_SCRIPT.is_file():
        print(f"ERROR: {VALIDATE_SCRIPT} not found", file=sys.stderr)
        return 1
    r = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT)] + (["-q"] if quiet else []) + (["--no-cache"] if no_cache else []),
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print("ERROR: Workspace constraints do not resolve. Dependency conflict detected.", file=sys.stderr)
        if r.stdout:
            print(r.stdout, file=sys.stderr, end="" if r.stdout.endswith("\n") else "\n")
        if r.stderr:
            print(r.stderr, file=sys.stderr, end="" if r.stderr.endswith("\n") else "\n")
        return 1

    if not quiet:
        print("OK: Workspace constraints resolve without conflicts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
