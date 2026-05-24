#!/usr/bin/env python3
"""Check that every incident runbook has the 4 required governance fields.

Required frontmatter: owner, cadence, verifier, last_executed.
Scans codex/15-runbooks/incidents/*.md (excludes README.md and game_day_protocol.md).

Usage: python3 scripts/plan-hygiene/check_runbook_fields.py [--quiet]
Exit 0 = clean. Exit 1 = violations found.
"""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_FIELDS = ("owner", "cadence", "verifier", "last_executed")
EXCLUDED = {"README.md", "game_day_protocol.md"}

_quiet = "--quiet" in sys.argv

PM_DIR = Path(__file__).resolve().parents[2]
RUNBOOK_DIR = PM_DIR / "codex" / "15-runbooks" / "incidents"

failures: list[str] = []

for runbook in sorted(RUNBOOK_DIR.glob("*.md")):
    if runbook.name in EXCLUDED:
        continue
    lines = runbook.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        failures.append(f"{runbook.name}: missing frontmatter (first line is not '---')")
        continue
    fm_lines: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        fm_lines.append(line)
    fm_text = "\n".join(fm_lines)
    for field in REQUIRED_FIELDS:
        if not any(ln.startswith(f"{field}:") for ln in fm_lines):
            failures.append(f"{runbook.name}: missing required field '{field}'")

if failures:
    if not _quiet:
        print(f"❌ Runbook governance violations ({len(failures)}):")
        for f in failures:
            print(f"  {f}")
    sys.exit(1)

if not _quiet:
    count = len(list(RUNBOOK_DIR.glob("*.md"))) - len(EXCLUDED)
    print(f"✅ All {count} runbooks have required governance fields (owner/cadence/verifier/last_executed)")
sys.exit(0)
