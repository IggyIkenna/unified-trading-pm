#!/usr/bin/env python3
"""Validate workspace-constraints.toml resolves without dependency conflicts.

Runs uv pip compile with workspace constraints to verify all external packages
and their transitive dependencies resolve together. Fails if pandas->numpy,
or any other transitive chain, conflicts with the constrained versions.

SSOT: unified-trading-pm/workspace-constraints.toml (last valid external deps).
Run after resolve-canonical-versions.py or when bumping constraints.

Usage:
    python validate-workspace-constraints.py
    python validate-workspace-constraints.py --python-version 3.13

Exit: 0 = resolves; 1 = conflict or error.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-reuse-def]

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent.parent
CONSTRAINTS_PATH = PM_ROOT / "workspace-constraints.toml"

# Internal/workspace packages - not on PyPI, skip for resolution
INTERNAL_PREFIXES = ("unified-", "unified_")


def load_constraints() -> dict[str, str]:
    """Load [dependencies] from workspace-constraints.toml."""
    if not CONSTRAINTS_PATH.is_file():
        return {}
    with open(CONSTRAINTS_PATH, "rb") as f:
        data: dict[str, Any] = cast(dict[str, Any], tomllib.load(f))
    deps = data.get("dependencies")
    if not isinstance(deps, dict):
        return {}
    return {k: str(v) for k, v in deps.items()}


def is_external_pyproject_spec(spec: str) -> bool:
    """True if spec is a PyPI package with version constraints."""
    base = re.sub(r"\[.*?\]", "", spec).strip().lower()
    if any(base.startswith(p) for p in INTERNAL_PREFIXES):
        return False
    # Bare package name (no >=, <, ==) = path dep or unversioned, skip
    if not re.search(r"[<>=~!]", spec):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate workspace-constraints.toml resolves without conflicts")
    parser.add_argument(
        "--python-version",
        default="3.13",
        help="Python version for resolution (default: 3.13)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress success message",
    )
    args = parser.parse_args()

    if not CONSTRAINTS_PATH.is_file():
        print(f"ERROR: {CONSTRAINTS_PATH} not found", file=sys.stderr)
        return 1

    constraints = load_constraints()
    external: dict[str, str] = {}
    for key, spec in constraints.items():
        if is_external_pyproject_spec(spec):
            external[key] = spec

    if not external:
        print("ERROR: No external PyPI packages in workspace-constraints.toml", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        constraints_txt = tmp / "constraints.txt"
        requirements_in = tmp / "requirements.in"

        # constraints.txt: one spec per line (uv format)
        constraints_txt.write_text(
            "\n".join(sorted(external.values(), key=lambda s: s.lower())) + "\n",
            encoding="utf-8",
        )

        # requirements.in: package names only (constraints restrict versions)
        def pkg_from_spec(s: str) -> str:
            m = re.match(r"^([a-zA-Z0-9_-]+(?:\[[^\]]*\])?)\s*([<>=~!].*)?$", s)
            return m.group(1) if m else s.split("[")[0]

        pkgs = sorted({pkg_from_spec(s) for s in external.values()})
        requirements_in.write_text("\n".join(pkgs) + "\n", encoding="utf-8")

        cmd = [
            "uv",
            "pip",
            "compile",
            str(requirements_in),
            "-c",
            str(constraints_txt),
            "--python-version",
            args.python_version,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=WORKSPACE_ROOT,
        )

        if result.returncode != 0:
            print("ERROR: Workspace constraints do not resolve. Dependency conflict detected.", file=sys.stderr)
            print(file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            if result.stdout:
                print("--- stdout ---", file=sys.stderr)
                print(result.stdout, file=sys.stderr)
            return 1

        if not args.quiet:
            print(f"OK: {len(external)} external packages resolve without conflicts (Python {args.python_version})")
        return 0


if __name__ == "__main__":
    sys.exit(main())
