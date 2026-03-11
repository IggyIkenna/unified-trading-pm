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
import json
import sys
import urllib.request
from pathlib import Path
from typing import cast

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_URL = "https://raw.githubusercontent.com/SchemaStore/schemastore/master/src/schemas/json/cloudbuild.json"


def load_schema() -> dict[str, object]:
    """Fetch Cloud Build JSON schema from SchemaStore."""
    with urllib.request.urlopen(SCHEMA_URL, timeout=10) as resp:  # type: ignore[arg-type]
        data: bytes = resp.read()  # type: ignore[union-attr]
        return json.loads(data.decode())  # type: ignore[no-any-return]


def load_yaml(path: Path) -> object:
    """Load YAML file. Uses PyYAML (workspace venv)."""
    import yaml

    with open(path) as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


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
        jsonschema.validate(instance=data, schema=schema)  # type: ignore[no-untyped-call]
        return True, None
    except jsonschema.ValidationError as e:  # type: ignore[no-untyped-call]
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
    args = parser.parse_args()

    arg_workspace: bool = cast(bool, args.workspace)
    arg_dir: str | None = cast("str | None", args.dir)
    arg_paths: list[str] = cast("list[str]", args.paths)
    arg_quiet: bool = cast(bool, args.quiet)

    schema: dict[str, object] = load_schema()

    files: list[Path] = []
    if arg_workspace:
        files = find_cloudbuild_files(WORKSPACE_ROOT)
    elif arg_dir:
        files = find_cloudbuild_files(Path(arg_dir).resolve())
    elif arg_paths:
        for p in arg_paths:
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
            if not arg_quiet:
                print(f"OK {rel}")
        else:
            print(f"FAIL {rel}: {err}", file=sys.stderr)
            failed += 1

    if failed:
        sys.exit(1)
    print(f"Validated {len(files)} file(s) OK")


if __name__ == "__main__":
    main()
