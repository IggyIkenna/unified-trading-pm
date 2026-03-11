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
import sys
from pathlib import Path

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


def load_yaml(path: Path) -> object:
    import yaml

    with open(path) as f:
        return yaml.safe_load(f)


def validate_file(path: Path, schema: dict) -> tuple[bool, str | None]:
    import jsonschema

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
    found: list[Path] = []
    for p in root.rglob("buildspec*.yaml"):
        if "node_modules" in str(p):
            continue
        if "aws" in p.name.lower() or p.name == "buildspec.yaml":
            found.append(p)
    for p in root.rglob("buildspec*.yml"):
        if "node_modules" in str(p):
            continue
        found.append(p)
    return sorted(set(found))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate AWS CodeBuild buildspec YAML")
    parser.add_argument("paths", nargs="*", help="Files or dirs to validate")
    parser.add_argument("--dir", help="Validate all buildspec*.aws.yaml in directory")
    parser.add_argument("--workspace", action="store_true", help="Validate all in workspace")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only print failures")
    args = parser.parse_args()

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
