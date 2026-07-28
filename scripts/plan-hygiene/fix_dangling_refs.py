#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Resolve dangling /plans/... and /codex/... references to their current corpus
location, when the basename resolves UNAMBIGUOUSLY to exactly one real file
elsewhere (mirrors fix_reference_paths.py's related: field resolution safety rule
— ambiguous or unresolvable left untouched, never guessed).

Why this exists: `check_reference_paths.py`'s existence-ratchet counts referrers
whose /plans/.../codex/... path doesn't resolve to a real file — the single
biggest source is a plan/codex doc getting archived (git mv plans/active/X.md ->
plans/archive/<yyyy_mm>/X.md) without every OTHER doc that cites the old path
being updated. CLAUDE.md's plan-archival ritual names this exact step
("update every referrer's path corpus-wide") but it was a checked-in gap until
2026-07-23, so a large pre-existing backlog accumulated (~940 dangling refs at
the 2026-07-23 baseline seed) and keeps growing every time a doc is archived
without the corpus-wide grep-and-fix. This tool automates the SAFE subset of
that fix (basename resolves to exactly one file) — re-run it whenever the
existence count creeps toward its ratchet baseline in
reference_paths_baseline.yaml; the answer changes every time something new gets
archived, so this is NOT a one-off script.

Usage:
  python3 scripts/plan-hygiene/fix_dangling_refs.py [--dry-run]

After a real (non-dry-run) pass, re-run
`python3 scripts/plan-hygiene/check_reference_paths.py --quiet --update-baseline`
to lower the ratchet baseline by the number of violations actually fixed —
never hand-raise it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PM_DIR = Path(__file__).resolve().parents[2]
GOOD_REF_RE = re.compile(r"/(?:plans|codex)/[A-Za-z0-9_./-]+\.md")

TARGET_GLOBS = ["plans/**/*.md", "codex/**/*.md", "cursor-configs/**/*.md"]


def target_files() -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for pattern in TARGET_GLOBS:
        for p in PM_DIR.glob(pattern):
            if p in seen or not p.is_file():
                continue
            seen.add(p)
            files.append(p)
    return files


def build_index() -> dict[str, list[str]]:
    """basename -> [/plans/... or /codex/... path, ...] for every real .md file."""
    index: dict[str, list[str]] = {}
    for top in ("plans", "codex"):
        base = PM_DIR / top
        if not base.exists():
            continue
        for p in base.rglob("*.md"):
            rel = "/" + p.relative_to(PM_DIR).as_posix()
            index.setdefault(p.name, []).append(rel)
    return index


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    index = build_index()
    files = target_files()
    fixed = 0
    fixed_files = 0
    unresolved: list[str] = []
    skipped_ambiguous: list[str] = []

    for p in files:
        text = p.read_text(encoding="utf-8")
        refs = set(GOOD_REF_RE.findall(text))
        replacements: dict[str, str] = {}
        for ref in refs:
            if (PM_DIR / ref.lstrip("/")).is_file():
                continue  # already resolves fine
            basename = ref.rsplit("/", 1)[-1]
            matches = [m for m in index.get(basename, []) if m != ref]
            if len(matches) == 1:
                replacements[ref] = matches[0]
            elif len(matches) == 0:
                unresolved.append(f"{p.relative_to(PM_DIR)}: {ref} — no match anywhere")
            else:
                skipped_ambiguous.append(f"{p.relative_to(PM_DIR)}: {ref} — AMBIGUOUS {matches}")

        if not replacements:
            continue

        new_text = text
        file_fixed = 0
        for old, new in replacements.items():
            file_fixed += new_text.count(old)
            new_text = new_text.replace(old, new)

        if new_text != text:
            fixed_files += 1
            fixed += file_fixed
            if not dry_run:
                p.write_text(new_text, encoding="utf-8")
            print(f"FIXED {p.relative_to(PM_DIR)}: {replacements} ({file_fixed} occurrence(s))")

    print(f"\nFiles changed: {fixed_files}")
    print(f"Occurrences fixed: {fixed}")
    print(
        f"Unresolved (no match anywhere — needs a human to find the new home, or the doc is genuinely gone): {len(unresolved)}"
    )
    print(f"Skipped (ambiguous — multiple same-named files, needs a human pick): {len(skipped_ambiguous)}")
    if dry_run:
        print("(--dry-run: no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
