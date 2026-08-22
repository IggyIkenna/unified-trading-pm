#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Validate Cursor plan format for *.plan.md files.

Required YAML frontmatter:
  - name: str
  - overview: str
  - todos: list of {id, content, status}
  - isProject: bool

Fails (exit 1) if any plan file does not match. Used by quality-gates.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _find_plans_dir(repo_root: Path) -> Path:
    """Resolve plans dir: repo/plans/cursor-plans (canonical in repo)."""
    candidates = [
        repo_root / "unified-trading-pm" / "plans" / "cursor-plans",
        repo_root / "plans" / "cursor-plans",
    ]
    for p in candidates:
        if p.is_dir():
            return p
    return candidates[0]


def _parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """Extract YAML frontmatter. Returns (parsed_dict, rest) or (None, content)."""
    if not content.strip().startswith("---"):
        return None, content
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return None, content
    yaml_block, rest = match.group(1), match.group(2)
    data: dict = {}
    for line in yaml_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key == "todos":
                data[key] = "present" if "id:" in yaml_block and "content:" in yaml_block else None
            else:
                data[key] = val
    return data, rest


def validate_plan(path: Path) -> list[str]:
    """Validate a single plan file. Returns list of error messages."""
    errs: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return [f"{path}: cannot read: {e}"]

    data, _ = _parse_frontmatter(text)
    if data is None:
        errs.append(f"{path}: missing or invalid YAML frontmatter (must start with ---)")
        return errs

    if not data.get("name"):
        errs.append(f"{path}: frontmatter must have 'name:'")
    if not data.get("overview"):
        errs.append(f"{path}: frontmatter must have 'overview:'")
    if not data.get("todos"):
        errs.append(f"{path}: frontmatter must have 'todos:' with id/content/status items")
    if "isProject" not in data:
        errs.append(f"{path}: frontmatter must have 'isProject:' (true or false)")

    if "todos:" not in text or "- id:" not in text:
        errs.append(f"{path}: todos must be a list of {{id, content, status}} objects")

    return errs


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    plans_dir = _find_plans_dir(repo_root)

    if not plans_dir.is_dir():
        print(f"ERROR: plans dir not found: {plans_dir}", file=sys.stderr)
        return 1

    plan_files = list(plans_dir.glob("*.plan.md"))
    if not plan_files:
        print("OK: no *.plan.md files to validate")
        return 0

    all_errs: list[str] = []
    for p in sorted(plan_files):
        all_errs.extend(validate_plan(p))

    if all_errs:
        print("ERROR: Cursor plan format validation failed:", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        print(
            "\nRequired frontmatter: name, overview, todos (list of {id, content, status}), isProject",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {len(plan_files)} plan(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
