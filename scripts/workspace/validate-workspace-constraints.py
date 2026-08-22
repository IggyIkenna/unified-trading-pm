#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate workspace-constraints.toml resolves without dependency conflicts.

Parses workspace-constraints.toml, writes a temp requirements.in, runs uv pip compile.
Caches result by hash of constraints file — skips uv pip compile when unchanged.
Exit: 0 = resolves, 1 = conflict or error.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import cast

PM_ROOT = Path(__file__).resolve().parent.parent.parent
CONSTRAINTS_PATH = PM_ROOT / "workspace-constraints.toml"
CACHE_DIR = PM_ROOT / ".cache" / "workspace-constraints-validation"

# Packages that CANNOT be co-resolved with the rest of the workspace constraints
# in a single flat `uv pip compile`. Each entry is a PyPI-metadata conflict that
# is correctly resolved per-repo via `[tool.uv] override-dependencies`, not by
# editing the workspace floor.
#
# `betfairlightweight`: declares transitive `requests<2.33.0` on PyPI for every
# release we'd use (CVE-2026-25645 floors workspace `requests` at >=2.33.0).
# execution-service is the sole consumer; it pins requests via per-repo override.
# See `.cursor/rules/dependencies/requests-betfairlightweight-workspace-resolution.mdc`.
EXCLUDE_FROM_GLOBAL_COMPILE: frozenset[str] = frozenset({"betfairlightweight"})


def _constraints_hash() -> str:
    content = CONSTRAINTS_PATH.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


def _read_cache() -> int | None:
    """Return cached exit code (0 or 1) if cache hit, else None."""
    if not CACHE_DIR.is_dir():
        return None
    h = _constraints_hash()
    ok_file = CACHE_DIR / f"{h}.ok"
    err_file = CACHE_DIR / f"{h}.err"
    if ok_file.is_file():
        return 0
    if err_file.is_file():
        return 1
    return None


def _write_cache(exit_code: int) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    h = _constraints_hash()
    for f in CACHE_DIR.glob(f"{h}.*"):
        f.unlink()
    (CACHE_DIR / f"{h}.ok" if exit_code == 0 else CACHE_DIR / f"{h}.err").touch()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache, always run uv pip compile")

    class Args(argparse.Namespace):
        quiet: bool = False
        no_cache: bool = False

    args = parser.parse_args(namespace=Args())
    quiet: bool = args.quiet
    no_cache: bool = args.no_cache

    if not CONSTRAINTS_PATH.is_file():
        if not quiet:
            print(f"ERROR: {CONSTRAINTS_PATH} not found", file=sys.stderr)
        return 1

    if not no_cache:
        cached = _read_cache()
        if cached is not None:
            if not quiet:
                if cached == 0:
                    print("OK: Workspace constraints resolve (cached).", file=sys.stderr)
                else:
                    print(
                        "FAIL: Workspace constraints did not resolve (cached failure). "
                        "Re-run with --no-cache to print the full uv pip compile error.",
                        file=sys.stderr,
                    )
            return cached

    with open(CONSTRAINTS_PATH, "rb") as f:
        data = cast(dict[str, object], tomllib.load(f))
    if "dependencies" not in data:
        if not quiet:
            print("ERROR: [dependencies] required in workspace-constraints.toml", file=sys.stderr)
        return 1
    deps_raw = data["dependencies"]
    if not isinstance(deps_raw, dict):
        if not quiet:
            print("ERROR: No [dependencies] in workspace-constraints.toml", file=sys.stderr)
        return 1
    deps: dict[str, object] = deps_raw

    specs = [str(v) for k, v in deps.items() if isinstance(v, str) and k not in EXCLUDE_FROM_GLOBAL_COMPILE]
    if not specs:
        if not quiet:
            print("ERROR: No dependency specs in workspace-constraints.toml", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        req_in = Path(tmp) / "requirements.in"
        req_in.write_text(chr(10).join(specs))
        r = subprocess.run(
            ["uv", "pip", "compile", str(req_in), "-o", str(Path(tmp) / "out.txt")],
            cwd=str(PM_ROOT),
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            if not quiet:
                if r.stdout:
                    print(r.stdout, file=sys.stderr, end="" if r.stdout.endswith("\n") else "\n")
                if r.stderr:
                    print(r.stderr, file=sys.stderr, end="" if r.stderr.endswith("\n") else "\n")
            _write_cache(1)
            return 1
    _write_cache(0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
