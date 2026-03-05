#!/usr/bin/env python3
"""Validate workspace-constraints.toml resolves without dependency conflicts.

Parses workspace-constraints.toml, writes a temp requirements.in, runs uv pip compile.
Exit: 0 = resolves, 1 = conflict or error.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

PM_ROOT = Path(__file__).resolve().parent.parent.parent
CONSTRAINTS_PATH = PM_ROOT / "workspace-constraints.toml"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()

    if not CONSTRAINTS_PATH.is_file():
        if not args.quiet:
            print(f"ERROR: {CONSTRAINTS_PATH} not found", file=sys.stderr)
        return 1

    with open(CONSTRAINTS_PATH, "rb") as f:
        data = tomllib.load(f)
    deps = data.get("dependencies", {})
    if not isinstance(deps, dict):
        if not args.quiet:
            print("ERROR: No [dependencies] in workspace-constraints.toml", file=sys.stderr)
        return 1

    specs = [str(v) for v in deps.values() if isinstance(v, str)]
    if not specs:
        if not args.quiet:
            print("ERROR: No dependency specs in workspace-constraints.toml", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        req_in = Path(tmp) / "requirements.in"
        req_in.write_text("\n".join(specs))
        r = subprocess.run(
            ["uv", "pip", "compile", str(req_in), "-o", str(Path(tmp) / "out.txt")],
            cwd=str(PM_ROOT),
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            if not args.quiet and r.stderr:
                print(r.stderr, file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
