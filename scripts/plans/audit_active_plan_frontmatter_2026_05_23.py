#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: oneoff
# Delete-when: after prod-run + orphan-sweep=0
"""Audit active-plan frontmatter for canonical conformity.

Required fields (per epic-foundation model):
  name (or title), parent_epic, assigned_vm, priority, status,
  estimate_class, estimate_baseline_ai_days, estimate_calibrated_ai_days

Optional but expected:
  created, last_updated, parent, locked_by, locked_since
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED = [
    ("name", "title"),  # either acceptable
    ("parent_epic",),
    ("assigned_vm",),
    ("priority",),
    ("status",),
    ("estimate_class",),
    ("estimate_baseline_ai_days",),
    ("estimate_calibrated_ai_days",),
]

SKIP_FILES = {"INDEX.md", "_agent_pings.md", "task_template.md"}


def extract_frontmatter(path: Path) -> dict[str, str] | None:
    text = path.read_text()
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    block = text[4:end].strip()
    fields: dict[str, str] = {}
    current_key: str | None = None
    for line in block.splitlines():
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:(.*)$", line)
        if m and not line.startswith(" "):
            current_key = m.group(1)
            value = m.group(2).strip()
            fields[current_key] = value
        # nested or list continuation — ignore for audit
    return fields


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    active_dir = root / "plans" / "active"
    plans = sorted(p for p in active_dir.glob("*.md") if p.name not in SKIP_FILES)

    full_conformant: list[Path] = []
    partial: dict[Path, list[str]] = {}
    no_frontmatter: list[Path] = []

    for path in plans:
        fm = extract_frontmatter(path)
        if fm is None:
            no_frontmatter.append(path)
            continue
        missing: list[str] = []
        for field_group in REQUIRED:
            if not any(f in fm for f in field_group):
                missing.append("/".join(field_group))
        if missing:
            partial[path] = missing
        else:
            full_conformant.append(path)

    print("=== Active plan frontmatter audit ===")
    print(f"Total plans scanned:    {len(plans)}")
    print(f"Fully conformant:       {len(full_conformant)}")
    print(f"Partial frontmatter:    {len(partial)}")
    print(f"No frontmatter at all:  {len(no_frontmatter)}")
    print()

    if no_frontmatter:
        print(f"--- NO FRONTMATTER ({len(no_frontmatter)}) ---")
        for p in no_frontmatter:
            print(f"  {p.name}")
        print()

    if partial:
        # Group by missing-field signature for sweep planning
        sigs: dict[tuple[str, ...], list[Path]] = {}
        for p, miss in partial.items():
            key = tuple(sorted(miss))
            sigs.setdefault(key, []).append(p)
        print(f"--- PARTIAL ({len(partial)}) — grouped by missing-field signature ---")
        for sig, files in sorted(sigs.items(), key=lambda kv: -len(kv[1])):
            print(f"\n  Missing: {', '.join(sig)}  ({len(files)} plans)")
            for p in files[:5]:
                print(f"    - {p.name}")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
