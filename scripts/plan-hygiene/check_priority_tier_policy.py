#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Soft check: flag active plans/issues whose declared `priority:` looks inconsistent with
`/codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md` (the 2026-07-28
operator-ruled tier policy).

Enforcement gap this closes (per the SSOT's own § 3): "No automated enforcement exists yet
... correct application depends on whoever authors/reprioritizes a plan actually reading this
doc." `regen_backlog_from_plan.py` dispatches strictly off a plan's literal `P<n>` tag and does
not know this policy at all.

First-pass heuristic (title/summary/tags keyword match — deliberately NOT a hard judgment call;
see the SSOT: "is this really backfill-critical" needs reading, not just regexing):

  A `status: active` plan (or `status: open` issue) whose `asset_group` is ENTIRELY within the
  two deprioritized tiers (`sports`, `tradfi` — no `cross-cutting`/`cefi`/`defi` mixed in) and
  whose `priority` is `P0` or `P1` is flagged UNLESS its title/summary/tags contain at least one
  backfill-completion-critical signal keyword (the SSOT's own carve-out: "data-completion /
  backfill / manifest-canonicalisation / closeout-critical ... the work that finishes the
  backfill and lets the paid vendor subscription be cancelled"). A flagged doc is a CANDIDATE for
  re-triage, not an automatic violation — a human (or `/plan-reconcile`) still reads it to confirm.

This is advisory (soft, warn-only) by design: a keyword miss/hit cannot itself decide whether a
plan is genuinely backfill-critical, only surface a doc worth a human glance. Exit code is 0
unless --strict is passed (matching this repo's other soft plan-hygiene checks, e.g.
check_parent_epic_alignment.py).

Usage:
    python3 scripts/plan-hygiene/check_priority_tier_policy.py [--quiet] [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import cast

PM_DIR = Path(__file__).resolve().parents[2]
PLANS_DIR = PM_DIR / "plans" / "active"
ISSUES_DIR = PLANS_DIR / "issues"

# The two deprioritized tiers per the SSOT (§1.2-1.3): sports/tradfi are lower strategic
# priority overall EXCEPT for the specific backfill-completion-critical carve-out below.
DEPRIORITIZED_TIERS = frozenset({"sports", "tradfi"})
# Tiers that, if present ALONGSIDE sports/tradfi on the same doc, take the doc out of scope for
# this heuristic entirely (a genuinely cross-cutting or higher-tier doc is not what this check
# is trying to catch — only a BARE sports/tradfi-tagged doc).
HIGHER_TIERS = frozenset({"cross-cutting", "cefi", "defi"})
ELEVATED_PRIORITIES = frozenset({"P0", "P1"})

# Backfill-completion-critical signal keywords — the SSOT's own carve-out language, plus the
# concrete artifacts that class of work actually touches (manifest capture_status states,
# canonical-path migration, vendor vs. paid-subscription framing). Deliberately broad/precision
# is NOT required here (false negatives just mean a flag isn't cleared; the whole check is
# advisory) — case-insensitive substring match.
BACKFILL_SIGNAL_KEYWORDS: tuple[str, ...] = (
    "backfill",
    "manifest",
    "canonical",
    "closeout",
    "coverage",
    "coverage gap",
    "data floor",
    "data-completion",
    "data completion",
    "attempted_failed",
    "empty_confirmed",
    "orphan",
    "reconcil",
    "consolidat",
    "vendor",
    "subscription",
    "cancel the",  # "...lets the paid vendor subscription be cancelled"
)

# Downstream/lower-priority signal keywords — the SSOT's own explicit "drops to P2/P3" examples
# (ML/strategy/UX work, plan-hygiene/AO-dispatch-batch satellites). Not required to flag (absence
# of a backfill signal alone is sufficient), but surfaced in the WARN line as extra context for
# whoever reads the flag, since a doc matching one of these is a stronger candidate.
DOWNSTREAM_SIGNAL_KEYWORDS: tuple[str, ...] = (
    "satellite",
    "ao_dispatch_batch",
    "ao-dispatch-batch",
    "plan-hygiene",
    "ml pipeline",
    "ml-service",
    "strategy-service",
    "ux",
    "frontend",
    "dashboard",
)


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract simple `key: value` frontmatter pairs (list-valued fields kept as their raw
    bracketed string — good enough for the substring/membership checks this script needs)."""
    fm: dict[str, str] = {}
    in_fm = False
    for i, line in enumerate(text.splitlines()):
        if line.strip() == "---":
            if not in_fm and i == 0:
                in_fm = True
                continue
            if in_fm:
                break
        if in_fm:
            m = re.match(r'^(\w[\w_-]*):\s*"?(.+?)"?\s*$', line)
            if m:
                fm[m.group(1)] = m.group(2)
    return fm


def _asset_groups(raw: str) -> set[str]:
    """Parse a frontmatter asset_group value (e.g. `[sports, tradfi]` or a bare `sports`)."""
    cleaned = raw.strip().strip("[]")
    return {g.strip().strip("'\"") for g in cleaned.split(",") if g.strip()}


def _has_any_keyword(haystack: str, keywords: tuple[str, ...]) -> list[str]:
    lower = haystack.lower()
    return [kw for kw in keywords if kw in lower]


def _iter_docs() -> list[Path]:
    docs = sorted(PLANS_DIR.glob("*.md"))
    if ISSUES_DIR.is_dir():
        docs += sorted(ISSUES_DIR.glob("*.md"))
    return docs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="Suppress OK output; only print flags + summary.")
    parser.add_argument(
        "--strict", action="store_true", help="Exit 1 if any doc is flagged (default: advisory, exit 0)."
    )
    args = parser.parse_args(argv)
    quiet = cast(bool, args.quiet)
    strict = cast(bool, args.strict)

    if not PLANS_DIR.is_dir():
        print(f"ERROR: plans/active not found at {PLANS_DIR}", file=sys.stderr)
        return 2

    checked = 0
    flagged: list[tuple[str, str, str]] = []  # (name, priority, asset_groups_str)

    for doc in _iter_docs():
        text = doc.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        status = fm.get("status", "").strip()  # noqa: qg-empty-fallback
        is_issue = doc.parent.name == "issues"
        live_status = "open" if is_issue else "active"
        if status != live_status:
            continue

        priority = fm.get("priority", "").strip()  # noqa: qg-empty-fallback
        raw_ag = fm.get("asset_group", "")  # noqa: qg-empty-fallback — field legitimately absent; `_asset_groups()` returns an empty set and the caller `continue`s
        groups = _asset_groups(raw_ag)
        if not groups:
            continue

        checked += 1

        if priority not in ELEVATED_PRIORITIES:
            continue
        if not groups.issubset(DEPRIORITIZED_TIERS):
            continue  # mixes in a higher tier, or is prediction/ao/ci/infrastructure/meta — out of scope
        if groups & HIGHER_TIERS:
            continue  # defensive; issubset above already excludes this, kept for clarity

        title = fm.get("title", "")  # noqa: qg-empty-fallback — field legitimately absent; empty title just contributes nothing to the keyword search below
        summary_start = text.find("summary:")
        # crude but sufficient: pull a chunk of body text around the frontmatter for keyword
        # matching (title + a slice of the raw frontmatter block covers summary/tags either way,
        # since both live inside the same '---' block this script already isolated conceptually).
        fm_block_end = text.find("\n---", 4) if text.startswith("---") else -1
        searchable = title + " " + (text[:fm_block_end] if fm_block_end != -1 else text[:2000])
        _ = summary_start  # kept only for readability of intent; searchable already covers it

        backfill_hits = _has_any_keyword(searchable, BACKFILL_SIGNAL_KEYWORDS)
        if backfill_hits:
            if not quiet:
                print(
                    f"OK    {doc.name}: priority={priority} asset_group={sorted(groups)} "
                    f"— backfill signal: {backfill_hits[:3]}"
                )
            continue

        downstream_hits = _has_any_keyword(searchable, DOWNSTREAM_SIGNAL_KEYWORDS)
        flagged.append((doc.name, priority, ",".join(sorted(groups))))
        extra = f" [downstream signal: {downstream_hits[:3]}]" if downstream_hits else ""
        print(
            f"WARN  {doc.name}: priority={priority} asset_group={sorted(groups)} — no backfill-completion-critical "
            f"signal in title/frontmatter; per plan-priority-tier-and-dispatch-ordering.md this tier normally drops "
            f"to P2/P3 unless it's the backfill-critical carve-out.{extra}"
        )

    if not quiet:
        print(
            f"\n{'WARN' if flagged else 'PASS'}  Checked {checked} active plan/issue docs (asset_group set) — "
            f"{len(flagged)} flagged for priority/tier-policy re-triage."
        )

    if strict and flagged:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
