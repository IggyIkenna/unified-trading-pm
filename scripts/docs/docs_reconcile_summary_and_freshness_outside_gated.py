#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Two report-only checks for the `/docs-reconcile` skill's Phase 1 items 2 and 4
(`cursor-configs/skills/docs-reconcile/SKILL.md`):

1. **Summary quality** (`--files`): flags missing/placeholder/very-short `summary:` frontmatter
   values via `docspec.parse_frontmatter` — the SAME trusted parser `check_frontmatter_schema.py`
   uses. A naive `grep '^summary:'` false-positives on any doc using YAML's `>-` folded block-
   scalar style (the value is on subsequent indented lines, not the `summary:` line itself) —
   this script doesn't have that blind spot. Pass specific paths to scope the check (e.g. to
   "docs touched since the last clean run", matching this skill's own established recency-
   scoping precedent for the more expensive hunters); omit `--files` to check the full live
   corpus (codex/ + plans/active/ + agents/), matching the corpus-wide sweep historical
   docs-reconcile runs have repeatedly done by hand.

2. **Freshness distribution OUTSIDE the 4 cutover-critical gated dirs** (always corpus-wide):
   `check_codex_doc_freshness.py` only gates `02-data/04-architecture/05-infrastructure/
   11-project-management`. Every prior docs-reconcile run that wanted the OUTSIDE-gated-dirs
   distribution (report-only per the skill's own charter — widening the gate is an operator
   call) recomputed it by hand from scratch each time. This makes that recomputation a one-line
   re-run instead.

Usage:
  python3 scripts/docs/docs_reconcile_summary_and_freshness_outside_gated.py [--files PATH ...]
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import docspec
import yaml

GATED_DIRS = ("02-data", "04-architecture", "05-infrastructure", "11-project-management")


def _pm_root() -> Path:
    return Path(__file__).resolve().parents[2]


def check_summaries(pm_root: Path, docspec, files: list[Path]) -> int:
    print("=== Summary-quality check (proper parser, not line-scoped grep) ===")
    bad = 0
    for p in files:
        if not p.exists() or p.suffix != ".md":
            print(f"  SKIP (not .md or absent): {p}")
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        try:
            fm, _ = docspec.parse_frontmatter(text)
        except yaml.YAMLError as e:
            print(f"  PARSE-ERROR: {p} :: {str(e).splitlines()[0]}")
            continue
        if not fm:
            print(f"  NO-FRONTMATTER: {p}")
            continue
        summary = fm.get("summary")
        rel = p.relative_to(pm_root) if p.is_absolute() else p
        if summary is None:
            print(f"  MISSING summary: {rel}")
            bad += 1
            continue
        summary = str(summary).strip()
        length = len(summary)
        placeholder = summary.lower() in {"tbd", "todo", "see body", "n/a", ""}
        flag = length < 40 or placeholder
        if flag:
            bad += 1
            print(f"  [{length} chars] <== FLAG {rel} :: {summary[:100]!r}")
    print(f"Total flagged: {bad} / {len(files)}")
    return bad


def check_freshness_outside_gated(pm_root: Path, docspec) -> None:
    print()
    print("=== Freshness distribution OUTSIDE the 4 gated dirs (report-only) ===")
    today = datetime.now(UTC).date()
    total = missing = fresh = stale = future = 0
    oldest: tuple[str, int] | None = None
    for md_path in sorted((pm_root / "codex").rglob("*.md")):
        rel = str(md_path.relative_to(pm_root / "codex"))
        top_dir = rel.split("/")[0]
        if top_dir in GATED_DIRS:
            continue
        text = md_path.read_text(encoding="utf-8", errors="replace")
        try:
            fm, _ = docspec.parse_frontmatter(text)
        except yaml.YAMLError:
            continue
        if not fm:
            continue
        total += 1
        lr = fm.get("last_reviewed")
        if not lr:
            missing += 1
            continue
        try:
            lr_date = datetime.strptime(str(lr), "%Y-%m-%d").date()
        except ValueError:
            missing += 1
            continue
        age = (today - lr_date).days
        if age < 0:
            future += 1
        elif age > 90:
            stale += 1
            if oldest is None or age > oldest[1]:
                oldest = (f"codex/{rel}", age)
        else:
            fresh += 1

    print(f"non-gated codex docs: {total}")
    print(f"missing last_reviewed: {missing}")
    print(f"fresh (<=90d): {fresh}")
    print(f"stale (>90d): {stale}")
    print(f"future-stamped: {future}")
    if oldest:
        print(f"oldest stale: {oldest[0]} ({oldest[1]}d)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="paths to summary-check; omit for the full live corpus (codex/ + plans/active/ + agents/)",
    )
    ap.add_argument("--pm-root", type=Path, default=None)
    ap.add_argument("--skip-summaries", action="store_true", help="only run the freshness-distribution report")
    args = ap.parse_args(argv)

    pm_root = args.pm_root or _pm_root()

    if not args.skip_summaries:
        if args.files:
            files = [(pm_root / f) if not Path(f).is_absolute() else Path(f) for f in args.files]
        else:
            files = (
                sorted((pm_root / "codex").rglob("*.md"))
                + sorted((pm_root / "plans" / "active").glob("*.md"))
                + sorted((pm_root / "agents").glob("*.md"))
            )
        check_summaries(pm_root, docspec, files)

    check_freshness_outside_gated(pm_root, docspec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
