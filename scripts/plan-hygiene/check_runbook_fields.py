#!/usr/bin/env python3
"""Check that every incident runbook has the 4 required governance fields.

Required frontmatter: owner, cadence, verifier, last_executed.
Scans codex/15-runbooks/incidents/*.md (excludes README.md and game_day_protocol.md).

Usage: python3 scripts/plan-hygiene/check_runbook_fields.py [--quiet] [file ...]
Exit 0 = clean. Exit 1 = violations found.

Optional explicit file list (staged mode — mirrors check_frontmatter.sh): when
files are passed, check ONLY those (the prek hook's STAGED runbooks) so a
commit is never blocked by a pre-existing violation in a runbook it does not
touch. Files outside codex/15-runbooks/incidents/ (or excluded names) are
silently ignored. No files given -> full-corpus scan (cron / CI, unchanged).
"""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_FIELDS = ("owner", "cadence", "verifier", "last_executed")
EXCLUDED = {"README.md", "game_day_protocol.md"}

_quiet = "--quiet" in sys.argv

PM_DIR = Path(__file__).resolve().parents[2]
RUNBOOK_DIR = PM_DIR / "codex" / "15-runbooks" / "incidents"

_file_args = [a for a in sys.argv[1:] if a != "--quiet"]
if _file_args:
    scan_files: list[Path] = []
    for raw in _file_args:
        f = Path(raw) if Path(raw).is_absolute() else PM_DIR / raw
        if not f.is_file():
            continue
        if f.resolve().parent != RUNBOOK_DIR.resolve():
            continue
        scan_files.append(f)
    scan_files.sort()
else:
    scan_files = sorted(RUNBOOK_DIR.glob("*.md"))

failures: list[str] = []

for runbook in scan_files:
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
    count = len([f for f in scan_files if f.name not in EXCLUDED])
    print(f"✅ All {count} checked runbook(s) have required governance fields (owner/cadence/verifier/last_executed)")
sys.exit(0)
