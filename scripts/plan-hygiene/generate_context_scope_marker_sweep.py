#!/usr/bin/env python3
r"""Corpus-wide sweep: compare each in-scope doc's most recent context-scout Progress Log
marker's claimed `context_scope` entry count against the live frontmatter list length.

Why this exists: the daily Phase-0 STALE check (generate_context_scope_inventory.py) only
compares the marker's DATE against the doc's last-touched date -- it cannot see a doc whose
most recent context-scout marker claims N entries while the live frontmatter list holds
fewer. That exact shape (a later context-scout batch edits the `context_scope` list without
updating the prior run's marker) was confirmed 4x in one 13-doc sample on 2026-08-06
(plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md)
and is plausibly wider: such a doc reads UP_TO_DATE while silently omitting exactly the
citations a worker most needs. This script is the corpus-wide sweep that finds every doc
in that state, regardless of Phase-0 verdict.

Method (per in-scope doc -- same population + parser as the inventory script, loaded from
it rather than re-derived, so the two tools can never disagree on what a doc or a marker
is):
  1. Parse frontmatter + body via scripts/docs/docspec.py (PyYAML), exactly like the
     inventory script.
  2. Find every `context-scout YYYY-MM-DD` Progress Log marker (the inventory script's
     MARKER_RE) and take the LATEST one by date (last occurrence on ties).
  3. Within that marker's own Progress Log bullet (bounded window -- the next bullet /
     header / fence), parse the claimed entry count with the issue's prescribed regex
     `\((\d+) entries?\)`.
  4. Compare against len(context_scope) in the live frontmatter. Any mismatch is reported
     -- a claim with NO parenthetical count (e.g. "trimmed from 9 to 6 entries") cannot be
     compared mechanically and is listed separately, never silently dropped.

Phase-0 verdict (UP_TO_DATE/STALE/NEVER_SCOUTED) is joined onto each row via the sibling
module's `_last_touched`, so the report shows whether mismatches hide under UP_TO_DATE.

# Epic: agent_operating_framework_master
# Lifecycle: standing audit tool (daily Phase-0 companion)
# Delete-when: never (superseded by a COUNT_MISMATCH verdict in Phase 0 -- issue todo 3)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]

# Claimed-count regex per the issue's spec: "(5 entries)" / "(1 entry)".
COUNT_RE = re.compile(r"\((\d+)\s+entries?\)")
# Marker bullet window bounds: a marker bullet ends at the next Progress Log bullet,
# section header, fenced block, blockquote, or horizontal rule -- plus a hard char cap
# so a pathological bullet can never balloon the scan.
_WINDOW_END_PATTERNS = ("\n- ", "\n## ", "\n```", "\n---", "\n> ")
_MAX_MARKER_WINDOW_CHARS = 2000
_BULLET_LOOKBACK = 300


def _load_sibling_inventory():
    """Load generate_context_scope_inventory.py as a module (same importlib pattern the
    plan-hygiene scripts use for scripts/docs/docspec.py) and reuse its corpus iterator,
    in-scope filter, marker regex, and last-touched logic -- the sweep must stay in
    lockstep with Phase 0's definition of every one of those."""
    inv_path = PM / "scripts" / "plan-hygiene" / "generate_context_scope_inventory.py"
    spec = importlib.util.spec_from_file_location("gen_context_scope_inventory", inv_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {inv_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


inv = _load_sibling_inventory()


@dataclass
class SweepRecord:
    path: str
    doc_type: str
    status: str
    verdict: str
    marker_date: str | None
    latest_claimed: int | None  # count claim on the LATEST marker, if it carries one
    actual: int | None
    last_claim_date: str | None  # date of the newest marker that carries a count claim
    last_claimed: int | None  # that older marker's claim (reference only, not a verdict)
    latest_marker_snippet: str | None  # first ~160 chars of the latest marker's bullet


def _marker_bullet_slice(body: str, marker_pos: int) -> str:
    """The Progress Log bullet containing the marker at `marker_pos`: from the `- ` line
    start walking back (bounded), forward to the next bullet/header/fence (bounded)."""
    start = body.rfind("\n- ", max(0, marker_pos - _BULLET_LOOKBACK), marker_pos)
    if start == -1:
        start = body.rfind("\n-", max(0, marker_pos - _BULLET_LOOKBACK), marker_pos)
    if start == -1:
        start = body.rfind("\n", 0, marker_pos) + 1
    end = len(body)
    for pat in _WINDOW_END_PATTERNS:
        idx = body.find(pat, marker_pos, min(len(body), marker_pos + _MAX_MARKER_WINDOW_CHARS))
        if idx != -1 and idx < end:
            end = idx
    return body[start:end]


def _claimed_count(body: str, marker_pos: int) -> tuple[int | None, str]:
    """(claimed count, bullet snippet) for the marker at marker_pos, or (None, ...) when
    its bullet carries no `(N entries)` parenthetical claim."""
    bullet = _marker_bullet_slice(body, marker_pos)
    m = COUNT_RE.search(bullet)
    return (int(m.group(1)) if m else None), bullet[:160].strip()


def _sweep_doc(path: Path) -> SweepRecord:
    rel = path.relative_to(PM).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        fm, body = inv.ds.parse_frontmatter(text)
    except yaml.YAMLError:
        fm, body = None, ""
    if fm is None:
        return SweepRecord(rel, "?", "?", "UNPARSEABLE", None, None, None, None, None, None)

    doc_type = fm.get("doc_type")
    status = fm.get("status")
    context_scope = fm.get("context_scope") or []
    if isinstance(context_scope, str):
        context_scope = [context_scope]
    actual = len(context_scope)

    # Same marker set Phase 0 sees -- the sweep must not invent markers Phase 0 ignores.
    markers = [(m.group(1), m.start()) for m in inv.MARKER_RE.finditer(body)]
    if not markers:
        return SweepRecord(rel, doc_type, status, "NEVER_SCOUTED", None, None, actual, None, None, None)

    latest_date = max(date for date, _ in markers)
    latest_pos = max(pos for date, pos in markers if date == latest_date)
    latest_claimed, latest_snippet = _claimed_count(body, latest_pos)

    # Reference claim: the newest marker that carries a parenthetical count.
    last_claim_date: str | None = None
    last_claimed: int | None = None
    for date, pos in sorted(markers, key=lambda m: (m[0], m[1])):
        claimed, _ = _claimed_count(body, pos)
        if claimed is not None:
            last_claim_date, last_claimed = date, claimed

    marker_for_verdict = inv._latest_marker(body)
    last_touched = inv._last_touched(fm, path, marker_for_verdict)
    if marker_for_verdict is not None and last_touched is not None and marker_for_verdict >= last_touched:
        verdict = "UP_TO_DATE"
    else:
        verdict = "STALE"

    return SweepRecord(
        rel,
        doc_type,
        status,
        verdict,
        latest_date,
        latest_claimed,
        actual,
        last_claim_date,
        last_claimed,
        latest_snippet,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of the summary report")
    args = parser.parse_args(argv)

    records = [_sweep_doc(path) for path in inv._iter_docs()]

    mismatches = [r for r in records if r.latest_claimed is not None and r.latest_claimed != r.actual]
    no_claim = [r for r in records if r.marker_date is not None and r.latest_claimed is None]
    with_marker = [r for r in records if r.marker_date is not None]

    if args.json:
        print(json.dumps([r.__dict__ for r in records], indent=1))
        return 0

    print(f"Total in-scope plan/issue docs: {len(records)}")
    print(f"  with context-scout marker:   {len(with_marker)}")
    print(f"  latest marker carries a count claim: {len(with_marker) - len(no_claim)}")
    print(f"  latest marker lacks a count claim (informational): {len(no_claim)}")
    print(f"  MISMATCH (claimed != actual): {len(mismatches)}")
    print()
    print("MISMATCHED DOCS (claimed != live frontmatter count):")
    for r in sorted(mismatches, key=lambda r: r.path):
        print(f"  - {r.path}")
        print(
            f"      verdict={r.verdict} marker={r.marker_date} claimed={r.latest_claimed} "
            f"actual={r.actual} (last count-bearing marker: {r.last_claim_date} claimed {r.last_claimed})"
        )
    print()
    print("LATEST MARKER WITHOUT A COUNT CLAIM (cannot compare mechanically; manual glance):")
    for r in sorted(no_claim, key=lambda r: r.path):
        ref = (
            f", last count-bearing marker {r.last_claim_date} claimed {r.last_claimed}"
            if r.last_claimed is not None
            else ""
        )
        snippet = f"\n      marker: {r.latest_marker_snippet}..." if r.latest_marker_snippet else ""
        print(f"  - {r.path} (verdict={r.verdict}, marker={r.marker_date}, actual={r.actual}{ref}){snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
