#!/usr/bin/env python3
"""
Sync labels from label-schema.yaml into a GitHub repo.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml


def _run_gh(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        check=check,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync labels from YAML schema.")
    parser.add_argument("--repo", required=True, help="Target repo OWNER/REPO.")
    parser.add_argument(
        "--schema-path",
        default=None,
        help="Path to label-schema.yaml (defaults to sibling file).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only.")
    args = parser.parse_args()

    if yaml is None:
        print("ERROR: PyYAML required. Install with `pip install pyyaml`", file=sys.stderr)
        return 1

    schema = Path(args.schema_path) if args.schema_path else Path(__file__).resolve().parent / "label-schema.yaml"
    if not schema.exists():
        print(f"ERROR: schema file not found: {schema}", file=sys.stderr)
        return 1

    data = yaml.safe_load(schema.read_text(encoding="utf-8")) or {}
    labels = data.get("labels", [])
    if not isinstance(labels, list):
        print("ERROR: schema labels must be a list", file=sys.stderr)
        return 1

    created = 0
    failed = 0
    for item in labels:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        desc = str(item.get("description", "")).strip()
        color = str(item.get("color", "")).strip().lstrip("#")
        if not name or not color:
            continue
        if args.dry_run:
            print(f"[DRY-RUN] would upsert label: {name}")
            created += 1
            continue
        proc = _run_gh(
            [
                "label",
                "create",
                name,
                "--repo",
                args.repo,
                "--description",
                desc,
                "--color",
                color,
                "--force",
            ],
            check=False,
        )
        if proc.returncode == 0:
            created += 1
        else:
            failed += 1
            print(f"WARN failed label {name}: {proc.stderr.strip()}", file=sys.stderr)

    print(f"Done: {created} upserted, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
