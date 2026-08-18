#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
"""Soft check: every active, non-superseded epic under plans/epics/*.md should have a
published HTML ledger at plans/epics/html/<slug>.html (SSOT:
/codex/11-project-management/epic-html-report-format.md "Storage + publish convention"),
and that report should not be STALE relative to the epic doc's own `last_updated`
frontmatter (report generated before the epic's last real content change).

Part of /plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md Phase 5
(the QG-hardening phase for the new epic taxonomy + HTML-artifact convention). Phase 4 of
the SAME plan (a concurrent agent, not this one) builds the actual HTML-generation path --
this script only checks presence + freshness, it never generates a report itself.

Embedded generation-timestamp comment format (this script's own choice, made 2026-08-18
BEFORE Phase 4 landed -- the two phases ran concurrently and could not coordinate live, so
reconcile this against whatever Phase 4 actually emitted and update the regex below if it
diverged):

    <!-- generated: 2026-08-18T14:00:00Z -->

i.e. a single HTML comment near the top of the file, literal key `generated:`, an ISO-8601
UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`). Only the DATE portion is used for the freshness
comparison -- the epic doc's own `last_updated` frontmatter is date-only, so comparing at
finer-than-a-day granularity would be false precision.

Reuses scripts/docs/docspec.py's `parse_frontmatter()` (the same YAML-backed parser the
corpus-wide docspec frontmatter gate uses), the same dynamic-load pattern
check_frontmatter_schema.py already uses, rather than a second hand-rolled regex parser --
epic `last_updated` values in this corpus carry a mix of plain dates, quoted-string dates,
and trailing `# inline comment` annotations (confirmed by sampling plans/epics/*.md before
writing this script) that a real YAML parser normalizes for free.

Soft-launch, warn-only (mirrors check_parent_epic_alignment.py's contract exactly): as of
2026-08-18 this corpus has ZERO plans/epics/html/*.html artifacts yet, so a hard-fail-by-
default launch would immediately red every epic in the corpus. Every finding is a WARN;
--strict is required to turn a run with findings into a real (exit 1) failure.

Exit 0  -- always, unless --strict AND at least one warning fired.
Exit 1  -- --strict was passed and at least one epic is missing its report or stale.

Usage:
    python3 scripts/plan-hygiene/check_epic_html_freshness.py [--quiet] [--strict]
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import cast

PM_DIR = Path(__file__).resolve().parents[2]
EPICS_DIR = PM_DIR / "plans" / "epics"
HTML_DIR = EPICS_DIR / "html"

# See module docstring for why this exact literal shape was chosen.
GENERATED_COMMENT_RE = re.compile(r"<!--\s*generated:\s*(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}:\d{2}Z?\s*-->")


def _load_docspec():
    spec = importlib.util.spec_from_file_location("docspec", PM_DIR / "scripts" / "docs" / "docspec.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/docs/docspec.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["docspec"] = mod
    spec.loader.exec_module(mod)
    return mod


def _coerce_last_updated(raw: object) -> date | None:
    """Normalize docspec.parse_frontmatter()'s `last_updated` value to a plain date.

    YAML parses an unquoted `YYYY-MM-DD` scalar as a real `datetime.date` already (and
    strips any trailing `# comment` for free); a quoted value (`"2026-08-17"`) comes back
    as `str` instead, so both shapes are handled. An empty/missing value (confirmed present
    in this corpus, e.g. mtds_mdps_master.md's blank `last_updated:`) returns None rather
    than raising -- freshness simply can't be checked for that epic.
    """
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            return None
        try:
            return date.fromisoformat(stripped)
        except ValueError:
            return None
    return None


def _parse_generated_timestamp(html_text: str) -> date | None:
    # "near the top" per the codex spec (epic-html-report-format.md) -- bound the scan so a
    # large report never forces a full-file regex pass.
    match = GENERATED_COMMENT_RE.search(html_text[:4096])
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--quiet", action="store_true", help="Suppress OK output")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any warning fired")
    args = parser.parse_args(argv)
    quiet = cast(bool, args.quiet)
    strict = cast(bool, args.strict)

    if not EPICS_DIR.exists():
        print(f"ERROR: epics dir not found at {EPICS_DIR}", file=sys.stderr)
        return 1

    docspec = _load_docspec()

    warn_count = 0
    checked_count = 0

    for epic_path in sorted(EPICS_DIR.glob("*.md")):
        name = epic_path.name
        if name == "README.md":
            continue

        text = epic_path.read_text(encoding="utf-8")
        fm, _body = docspec.parse_frontmatter(text)
        fm = fm if isinstance(fm, dict) else {}

        if fm.get("status") == "superseded":
            continue

        slug = epic_path.stem
        checked_count += 1
        html_path = HTML_DIR / f"{slug}.html"

        if not html_path.exists():
            warn_count += 1
            print(f"WARN  {slug}: no HTML report at plans/epics/html/{slug}.html")
            continue

        html_text = html_path.read_text(encoding="utf-8")
        generated = _parse_generated_timestamp(html_text)
        if generated is None:
            warn_count += 1
            print(
                f"WARN  {slug}: plans/epics/html/{slug}.html has no parseable "
                f"<!-- generated: YYYY-MM-DDTHH:MM:SSZ --> comment near the top"
            )
            continue

        last_updated = _coerce_last_updated(fm.get("last_updated"))
        if last_updated is None:
            if not quiet:
                print(
                    f"OK    {slug}: report exists (epic's last_updated is empty/unparseable -- freshness not checked)"
                )
            continue

        if generated < last_updated:
            warn_count += 1
            print(
                f"WARN  {slug}: stale — epic changed since last report "
                f"(report generated {generated.isoformat()}, epic last_updated {last_updated.isoformat()})"
            )
        elif not quiet:
            print(
                f"OK    {slug}: report fresh (generated {generated.isoformat()} >= "
                f"last_updated {last_updated.isoformat()})"
            )

    if not quiet:
        print(f"\n{'WARN' if warn_count else 'PASS'}  Checked {checked_count} epics — {warn_count} warning(s).")

    if strict and warn_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
