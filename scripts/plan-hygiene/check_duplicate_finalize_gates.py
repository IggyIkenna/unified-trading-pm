#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
"""Detect duplicate finalize-plan gates — a parent slug named in the `depends_on` of MORE THAN
ONE `gate_on_depends: true` plan WHERE at least two of those plans are themselves identifiable
as finalize plans (slug contains ``finalize`` — the established naming convention).

Context (2026-08-06,
plans/active/issues/duplicate_finalize_plans_created_for_one_parent_2026_08_06.md):
Two gated finalize plans were created for the SAME parent on the same day, each justified by
"no companion gated finalize plan exists" — nothing made the finalize-plan remediation path
idempotent. The two colliding files differ only by a redundant `_2026_07_31` suffix, so any
guard keyed on the exact expected filename would miss this; the real contract is the `depends_on`
relationship.

This check is the corpus-wide backstop: it surfaces the collision at rest. A non-zero count is
review-blocking (same severity as the orphan count).

Scope is narrowed to finalize-identifiable plans only (slug contains ``finalize``) — without
this filter, legitimate sibling-phase DAG edges (e.g. phases C/D/E all depending on phases
A+B being done via ``gate_on_depends: true``) would false-positive as duplicate gates. Those
are genuine prerequisite chains, not competing finalize plans for the same parent. A
2026-08-11 first-run corpus sweep confirmed 5 raw >1-gate cases, all 5 were legitimate sibling
dependencies with zero finalize-plan duplicates among them — the original incident's pair was
genuinely a one-off.

HARD failure (exit 1): any parent slug appears in >1 ``gate_on_depends: true`` plan's
``depends_on`` AND at least two of those plans are finalize-identifiable. This is an ABSOLUTE
check, not a ratchet — a duplicate finalize gate is unconditionally wrong.

Usage:
    python3 scripts/plan-hygiene/check_duplicate_finalize_gates.py [--quiet] [--pm-root <path>]
    python3 scripts/plan-hygiene/check_duplicate_finalize_gates.py --only <path> [<path> ...]

``--only <paths>``: still scans the full corpus to resolve gating (inherently corpus-wide
knowledge), but only reports violations involving a parent slug named in a staged file's own
`depends_on` — blast-radius-safe for precommit (a pre-existing duplicate entirely among
unstaged files never blocks this commit).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


@dataclass(frozen=True)
class PlanMeta:
    path: Path
    frontmatter: dict[str, object]


def _load_plan(p: Path) -> PlanMeta | None:
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        loaded = cast(object, yaml.safe_load(m.group(1)))
    except yaml.YAMLError:
        return None
    if not isinstance(loaded, dict):
        return None
    return PlanMeta(path=p, frontmatter=cast(dict[str, object], loaded))


def _is_finalize_plan(fm: dict[str, object]) -> bool:
    depends_on = fm.get("depends_on")
    gate = fm.get("gate_on_depends")
    has_deps = isinstance(depends_on, list) and len(cast(list[object], depends_on)) > 0
    return bool(has_deps and gate is True)


def _depends_on_slugs(fm: dict[str, object]) -> list[str]:
    """Return the slugs this plan's depends_on names (only if gate_on_depends: true)."""
    if not _is_finalize_plan(fm):
        return []
    depends_on = fm.get("depends_on")
    if not isinstance(depends_on, list):
        return []
    out: list[str] = []
    for dep in cast(list[object], depends_on):
        if isinstance(dep, str):
            out.append(dep.strip())
    return out


def _is_finalize_identifiable(pm: PlanMeta) -> bool:
    """A plan is finalize-identifiable if its slug contains 'finalize'.

    This is a naming-convention heuristic, not a content check — it deliberately does NOT
    inspect title/summary/todos. The convention is established (every finalize plan in the
    corpus is named ``<parent>_finalize[_<date>].md``), and a content-based check would
    be fragile in the other direction (a non-finalize plan whose title happens to mention
    "finalize" in passing).
    """
    return "finalize" in pm.path.stem.lower()


def _find_duplicates(active_dir: Path, issues_dir: Path) -> dict[str, list[Path]]:
    """Return {parent_slug: [gating_plan_path, ...]} for slugs with >1 gating plan
    where at least two of the gating plans are finalize-identifiable.

    Without the finalize-identifiable filter, legitimate sibling-phase DAG edges
    (e.g. phases C/D/E all depending on phases A+B via gate_on_depends: true) would
    false-positive. Only flag when the collision is between plans that both look like
    they are THE finalize plan for the same parent.
    """
    all_plans: list[PlanMeta] = []
    for d in (active_dir, issues_dir):
        if d.is_dir():
            for p in d.glob("*.md"):
                if (pm := _load_plan(p)) is not None:
                    all_plans.append(pm)

    # Build parent_slug -> list of gating-plan paths that gate on it
    parent_to_gates: dict[str, list[Path]] = {}
    for pm in all_plans:
        for slug in _depends_on_slugs(pm.frontmatter):
            parent_to_gates.setdefault(slug, []).append(pm.path)

    # Only flag when >1 gating plan AND at least 2 are finalize-identifiable
    result: dict[str, list[Path]] = {}
    for slug, paths in parent_to_gates.items():
        if len(paths) <= 1:
            continue
        finalize_count = sum(1 for p in paths if "finalize" in p.stem.lower())
        if finalize_count >= 2:
            result[slug] = paths
    return result


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect duplicate finalize-plan gates (parent slug in >1 gate_on_depends: true plan)."
    )
    parser.add_argument("--pm-root", type=Path, default=None)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help=(
            "Blast-radius-safe precommit mode: still scans the full corpus to resolve gating, "
            "but only reports duplicates where at least one of the gating plans is among these "
            "paths. A pre-existing duplicate entirely among unstaged files never blocks this commit."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    pm_root = cast("Path | None", ns.pm_root)
    quiet: bool = cast(bool, ns.quiet)
    only: list[str] | None = cast("list[str] | None", ns.only)

    if pm_root is None:
        pm_root = Path(__file__).resolve().parents[2]
    else:
        pm_root = pm_root.resolve()

    active_dir = pm_root / "plans" / "active"
    issues_dir = pm_root / "plans" / "active" / "issues"

    if not active_dir.is_dir():
        print(f"ERROR: plans/active not found at {active_dir}", file=sys.stderr)
        return 2

    duplicates = _find_duplicates(active_dir, issues_dir)

    if only is not None:
        only_resolved = {Path(o).resolve() for o in only}
        # Keep only duplicates where at least one gating plan is in --only
        filtered: dict[str, list[Path]] = {}
        for slug, paths in duplicates.items():
            if any(p.resolve() in only_resolved for p in paths):
                filtered[slug] = paths
        duplicates = filtered

    if not duplicates:
        if not quiet:
            print("✅ No duplicate finalize-plan gates (each parent slug has ≤1 gated finalize plan).")
        return 0

    print(
        f"❌ Duplicate finalize-plan gate(s) found — {len(duplicates)} parent slug(s) gated by >1 plan:"
    )
    for slug, paths in sorted(duplicates.items()):
        print(f"  - '{slug}' is gated by {len(paths)} finalize plans:")
        for p in sorted(paths):
            try:
                rel = p.relative_to(pm_root)
            except ValueError:
                rel = p
            print(f"      {rel}")

    print(
        "\nDe-race using the procedure in"
        " plans/active/issues/duplicate_finalize_plans_created_for_one_parent_2026_08_06.md:"
        " port any todo unique to the loser into the survivor FIRST, then set"
        " superseded_by/supersedes + a dated banner on the loser."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
