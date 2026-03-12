#!/usr/bin/env python3
"""Validate Cloud Build YAML files against the SchemaStore cloudbuild.json schema.

Uses jsonschema + PyYAML (no extra deps). Schema: SchemaStore cloudbuild.json.
Can validate a single file, a directory, or all cloudbuild*.yaml in workspace.

Usage:
    python3 validate-cloudbuild.py cloudbuild.yaml
    python3 validate-cloudbuild.py --dir ./some-repo
    python3 validate-cloudbuild.py --workspace  # all cloudbuild*.yaml in workspace
"""

from __future__ import annotations

import argparse
import http.client
import json
import sys
import urllib.request
from pathlib import Path
from typing import cast

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_URL = "https://raw.githubusercontent.com/SchemaStore/schemastore/master/src/schemas/json/cloudbuild.json"


class _ParsedArgs(argparse.Namespace):
    paths: list[str]
    dir: str | None
    workspace: bool
    quiet: bool


def load_schema() -> dict[str, object]:
    """Fetch Cloud Build JSON schema from SchemaStore."""
    response: http.client.HTTPResponse = cast(http.client.HTTPResponse, urllib.request.urlopen(SCHEMA_URL, timeout=10))  # nosec B310 — hardcoded SchemaStore https URL
    try:
        raw: bytes = response.read()
    finally:
        response.close()
    return cast(dict[str, object], json.loads(raw.decode()))


def load_yaml(path: Path) -> object:
    """Load YAML file. Uses PyYAML (workspace venv)."""
    import yaml

    with open(path) as f:
        return cast(object, yaml.safe_load(f))


def validate_file(path: Path, schema: dict[str, object]) -> tuple[bool, str | None]:
    """Validate a single Cloud Build YAML file. Returns (ok, error_msg)."""
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


def find_cloudbuild_files(root: Path) -> list[Path]:
    """Find all cloudbuild*.yaml files under root."""
    return sorted(root.rglob("cloudbuild*.yaml"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Cloud Build YAML against SchemaStore schema")
    parser.add_argument("paths", nargs="*", help="Files or dirs to validate")
    parser.add_argument("--dir", help="Validate all cloudbuild*.yaml in directory")
    parser.add_argument("--workspace", action="store_true", help="Validate all cloudbuild*.yaml in workspace")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only print failures")
    args = parser.parse_args(namespace=_ParsedArgs())

    schema = load_schema()

    files: list[Path] = []
    if args.workspace:
        files = find_cloudbuild_files(WORKSPACE_ROOT)
    elif args.dir:
        files = find_cloudbuild_files(Path(args.dir).resolve())
    elif args.paths:
        for p in args.paths:
            path = Path(p).resolve()
            if path.is_dir():
                files.extend(find_cloudbuild_files(path))
            elif path.is_file():
                files.append(path)
            else:
                print(f"Not found: {path}", file=sys.stderr)
                sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    if not files:
        print("No cloudbuild*.yaml files found.")
        sys.exit(0)

    failed = 0
    for path in files:
        ok, err = validate_file(path, schema)
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
