#!/usr/bin/env python3
"""Validate AWS CodeBuild buildspec YAML files.

Uses jsonschema + PyYAML (no extra deps). Schema: minimal embedded schema per AWS docs
(version 0.1/0.2, phases, env, artifacts, etc.). No SchemaStore schema exists for buildspec.

Usage:
    python3 validate-buildspec.py buildspec.aws.yaml
    python3 validate-buildspec.py --dir ./some-repo
    python3 validate-buildspec.py --workspace  # all buildspec*.aws.yaml in workspace
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import sys
from pathlib import Path
from typing import cast

# Directory names EXCLUDED from the recursive walk (never descended into). Build/cache/
# dependency trees hold no buildspec yaml — descending every repo's .venv across the
# workspace is pure walk-waste. Excluded ≠ pruned/removed: dirs stay on disk, the walk
# just doesn't enter them. (node_modules was already filtered post-hoc; now skipped at
# the walk level alongside the rest.)
EXCLUDE_DIR_NAMES: frozenset[str] = frozenset(
    {".venv", ".venv-workspace", "venv", "build", "dist", "node_modules", "__pycache__", ".git"}
)

try:
    import yaml
except ImportError:
    yaml = None

try:
    import jsonschema  # type: ignore[import-untyped]
except ImportError:
    jsonschema = None

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]

# Minimal AWS CodeBuild buildspec schema (no official SchemaStore schema)
# https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html
BUILDSPEC_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["version"],
    "properties": {
        "version": {"oneOf": [{"type": "string", "enum": ["0.1", "0.2"]}, {"type": "number", "enum": [0.1, 0.2]}]},
        "run-as": {"type": "string"},
        "env": {
            "type": "object",
            "properties": {
                "shell": {"type": "string"},
                "variables": {"type": "object"},
                "parameter-store": {"type": "object"},
                "exported-variables": {"type": "array", "items": {"type": "string"}},
                "secrets-manager": {"type": "object"},
                "git-credential-helper": {"type": "string", "enum": ["no", "yes"]},
            },
            "additionalProperties": True,
        },
        "phases": {
            "type": "object",
            "properties": {
                "install": {"type": "object"},
                "pre_build": {"type": "object"},
                "build": {"type": "object"},
                "post_build": {"type": "object"},
            },
            "additionalProperties": True,
        },
        "artifacts": {"type": "object"},
        "cache": {"type": "object"},
        "reports": {"type": "object"},
        "proxy": {"type": "object"},
        "batch": {"type": "object"},
    },
    "additionalProperties": True,
}


class _ParsedArgs(argparse.Namespace):
    paths: list[str]
    dir: str | None
    workspace: bool
    quiet: bool


def load_yaml(path: Path) -> object:
    if yaml is None:
        raise ImportError("yaml module not available")

    with open(path) as f:
        return cast(object, yaml.safe_load(f))


def validate_file(path: Path, schema: dict[str, object]) -> tuple[bool, str | None]:
    if jsonschema is None:
        raise ImportError("jsonschema module not available")

    try:
        data = load_yaml(path)
    except Exception as e:
        return False, f"YAML parse error: {e}"
    if data is None:
        return False, "Empty file"
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, None
    except jsonschema.ValidationError as e:
        return False, str(e)


def find_buildspec_files(root: Path) -> list[Path]:
    """Find buildspec yaml under root, skipping EXCLUDE_DIR_NAMES trees.

    Single os.walk replaces two ``root.rglob`` passes (each of which descended every .venv
    across the workspace). The per-file match conditions are unchanged, so the result set is
    identical — only the dependency/build trees are no longer enumerated.
    """
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
        for name in filenames:
            p = Path(dirpath) / name
            if "node_modules" in str(p):
                continue
            if fnmatch.fnmatch(name, "buildspec*.yaml"):
                if "aws" in name.lower() or name == "buildspec.yaml":
                    found.append(p)
            elif fnmatch.fnmatch(name, "buildspec*.yml"):
                found.append(p)
    return sorted(set(found))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate AWS CodeBuild buildspec YAML")
    parser.add_argument("paths", nargs="*", help="Files or dirs to validate")
    parser.add_argument("--dir", help="Validate all buildspec*.aws.yaml in directory")
    parser.add_argument("--workspace", action="store_true", help="Validate all in workspace")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only print failures")
    args = parser.parse_args(namespace=_ParsedArgs())

    files: list[Path] = []
    if args.workspace:
        files = find_buildspec_files(WORKSPACE_ROOT)
    elif args.dir:
        files = find_buildspec_files(Path(args.dir).resolve())
    elif args.paths:
        for p in args.paths:
            path = Path(p).resolve()
            if path.is_dir():
                files.extend(find_buildspec_files(path))
            elif path.is_file():
                files.append(path)
            else:
                print(f"Not found: {path}", file=sys.stderr)
                sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    if not files:
        print("No buildspec*.aws.yaml / buildspec*.yml files found.")
        sys.exit(0)

    failed = 0
    for path in files:
        ok, err = validate_file(path, BUILDSPEC_SCHEMA)
        try:
            rel = path.relative_to(WORKSPACE_ROOT)
        except ValueError:
            rel = path
        if ok:
            if not args.quiet:
                print(f"OK {rel}")
        else:
            print(f"FAIL {rel}: {err}", file=sys.stderr)
            failed += 1

    if failed:
        sys.exit(1)
    print(f"Validated {len(files)} file(s) OK")


if __name__ == "__main__":
    main()
