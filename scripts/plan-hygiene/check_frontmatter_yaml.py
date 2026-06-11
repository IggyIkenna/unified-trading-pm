#!/usr/bin/env python3
"""Strict YAML parse of plan/epic frontmatter — the machine-readability gate.

`check_frontmatter.sh` is grep-based (field-presence only): a frontmatter block whose
YAML is INVALID still passes it, while every real consumer (`yaml.safe_load` in the
deployment-api Epics tab, the orchestrator regen, fix_frontmatter.py) gets `{}` — so the
plan silently reads as parentless/blank everywhere that matters (incident 2026-06-11:
2 plans with unquoted `key: value`-shaped source strings showed as review-blocking
orphans on the Epics dashboard while the hygiene sweep stayed green).

Usage: check_frontmatter_yaml.py [file ...]   # no args → full corpus glob
Exit 0 = every frontmatter block parses to a YAML mapping. Exit 1 = violations.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

PM_DIR = Path(__file__).resolve().parents[2]
SKIP_NAMES = {"INDEX.md", "task_template.md", "README.md"}


def should_skip(name: str) -> bool:
    return (
        name in SKIP_NAMES
        or name.startswith("_")
        or name.endswith(".HANDOVER.md")
        or "SUPERSEDED" in name
    )


def check(path: Path) -> str | None:
    """Return an error string if the frontmatter block fails to parse as a mapping."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None  # jammed/absent frontmatter is check_frontmatter.sh's finding
    end = text.find("\n---", 3)
    if end == -1:
        return "unterminated frontmatter (no closing ---)"
    try:
        parsed: object = yaml.safe_load(text[3:end])
    except yaml.YAMLError as exc:
        first_line = str(exc).splitlines()[0]
        return f"frontmatter is not valid YAML ({first_line}) — quote any value containing ': '"
    if not isinstance(parsed, dict):
        return f"frontmatter parses to {type(parsed).__name__}, not a mapping"
    return None


def main(argv: list[str]) -> int:
    if argv:
        files = [Path(a) for a in argv if a.endswith(".md")]
    else:
        files = sorted(PM_DIR.glob("plans/active/*.md")) + sorted(PM_DIR.glob("plans/epics/*.md"))
    failures = 0
    for f in files:
        if not f.is_file() or should_skip(f.name):
            continue
        err = check(f)
        if err is not None:
            print(f"  {f.name}:\n    - {err}")
            failures += 1
    if failures:
        print(f"❌ check_frontmatter_yaml: {failures} file(s) with unparseable frontmatter")
        return 1
    print("✅ check_frontmatter_yaml: all frontmatter parses")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
