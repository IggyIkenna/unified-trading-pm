#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Corpus-wide duplicate-gated-finalize-plan detector (hygiene sweep).

Todo 2, duplicate_finalize_plans_created_for_one_parent_2026_08_06.md: flag any
parent slug named in the `depends_on` of MORE THAN ONE `gate_on_depends: true`
plan. Todo 1 (shipped 2026-08-15, unified-trading-pm@5255d0cbea) added a
CREATION-TIME guard to check_finalize_plan_coverage.py's `--only` precommit path,
which refuses a NEW/staged finalize plan that would collide with an existing gate
-- but nothing catches a duplicate already AT REST in the corpus (introduced before
that guard existed, or by a commit path the precommit hook doesn't cover). This is
that standing detector: it re-scans the whole `plans/active/` corpus every sweep
and reports the count the same way the orphan count is reported elsewhere in this
sweep (0 = clean; a non-zero count is review-blocking) -- see
/codex/12-agent-workflow/plan-completion-and-archival-discipline.md.

Deliberately self-contained rather than importing check_finalize_plan_coverage.py's
`_gated_by()` across the scripts/quality_gates <-> scripts/plan-hygiene directory
boundary: the loading logic is ~15 lines and duplicating it here avoids a fragile
runtime sys.path splice for what is otherwise a completely standalone check (every
other checker in this directory is self-contained the same way).

A live corpus-wide run at authoring time (2026-08-15) found 6 PRE-EXISTING
duplicate-gated parents using a filename-blind match (any `depends_on` +
`gate_on_depends: true` plan counted as a "finalize plan"). Todo 3's sweep
(2026-08-16) read all 6 flagged plans' actual titles/content and found EVERY ONE
was a false positive: a sanctioned SPLIT child (CLAUDE.md: "partial parallelism
isn't expressible in one plan -> SPLIT (gated step in Plan B via depends_on +
gate_on_depends: true)") -- a legitimate downstream phase plan that can't start
before its parent lands, not a competitor for the parent's archival slot. Example:
prediction_phase_ab_residuals_2026_07_24 was "gated by 3 finalize plans" that were
actually Phase C (data-status UI), Phase D (smoke-test/backfill) and Phase E
(football arb live) -- three substantively distinct plans, none of them archival
attempts. `_gated_by()` now additionally requires the gating plan's OWN filename to
follow the corpus's established `<parent-slug>_finalize[...]` naming convention
(every genuine finalize plan in this corpus is named that way) before it counts
toward a parent's duplicate-finalize tally -- see that function's docstring. This
closed all 6 false positives (0 duplicate-gated parents on re-scan) without
changing detection of a genuine collision (the reconstructed 2026-07-31 incident
shape is still caught -- see the test suite). Still a SHRINKING-RATCHET baseline
check, same shape as check_reference_paths.py / check_archive_candidates.sh in
this directory, not an absolute zero-tolerance gate -- kept that way since a
future genuine collision could plausibly still slip past the naming heuristic (a
mis-named finalize plan). Baseline lives in duplicate_gated_finalize_plans_baseline.yaml,
re-baselined to 0 as of todo 3.

Usage:
  python3 scripts/plan-hygiene/check_duplicate_gated_finalize_plans.py [--quiet] [--workspace-root <path>]
      [--baseline-path <path>] [--baseline-write] [--strict]
Exit 1 on a regression (current count > baseline, in default/--quiet mode) or any
hit at all (--strict); 0 otherwise; 2 on arg/IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


@dataclass(frozen=True)
class _Coverage:
    path: Path
    frontmatter: dict[str, object]


def _load_plan(p: Path) -> _Coverage | None:
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
    return _Coverage(path=p, frontmatter=cast(dict[str, object], loaded))


def _is_finalize_plan(fm: dict[str, object]) -> bool:
    depends_on = fm.get("depends_on")
    gate = fm.get("gate_on_depends")
    has_deps = isinstance(depends_on, list) and len(cast(list[object], depends_on)) > 0
    return bool(has_deps and gate is True)


def _gated_by(all_plans: list[_Coverage]) -> dict[str, list[Path]]:
    """Every gated parent slug -> the finalize plan path(s) whose depends_on names it
    AND whose own filename follows the corpus's established `<parent-slug>_finalize[...]`
    naming convention (every genuine finalize plan in this corpus is named that way --
    confirmed by inspection at todo-3 sweep time, duplicate_finalize_plans_created_for_
    one_parent_2026_08_06.md). That second condition matters: `depends_on` +
    `gate_on_depends: true` alone (todo 1/2's `_is_finalize_plan`) is ALSO the exact
    shape of a sanctioned SPLIT child (CLAUDE.md: "partial parallelism isn't expressible
    in one plan -> SPLIT (gated step in Plan B via depends_on + gate_on_depends: true)")
    -- a legitimate downstream phase plan that simply can't start before its parent
    lands, not a competitor for the parent's archival slot. Filename-blind matching over-
    flagged all 6 corpus hits as false positives at todo-3 sweep time (verified by
    reading each flagged plan's actual title/summary: e.g. prediction Phase C/D/E are
    three substantively distinct plans, not duplicate archival attempts, for
    prediction_phase_ab_residuals_2026_07_24) -- see that doc's 2026-08-16 Progress Log
    entry for the full per-parent evidence.
    """
    out: dict[str, list[Path]] = {}
    for cov in all_plans:
        if not _is_finalize_plan(cov.frontmatter):
            continue
        depends_on = cov.frontmatter.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        stem = cov.path.stem
        for dep in cast(list[object], depends_on):
            if isinstance(dep, str):
                slug = dep.strip()
                if stem == f"{slug}_finalize" or stem.startswith(f"{slug}_finalize_"):
                    out.setdefault(slug, []).append(cov.path)
    return out


def _resolve_active_dir(workspace_root: Path) -> Path | None:
    """Same three-candidate resolution as check_finalize_plan_coverage.py's main()
    (sibling-checkout layout, workspace_root-is-checkout-root layout, then a
    self-located fallback based on this file's own position -- see that module's
    main() for the per-tab-worktree rationale)."""
    candidates = [
        workspace_root / "unified-trading-pm" / "plans" / "active",
        workspace_root / "plans" / "active",
        Path(__file__).resolve().parents[2] / "plans" / "active",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


DEFAULT_BASELINE_PATH = Path(__file__).parent / "duplicate_gated_finalize_plans_baseline.yaml"


def _load_baseline_count(baseline_path: Path) -> int:
    if not baseline_path.exists():
        return 0
    try:
        loaded = cast(object, yaml.safe_load(baseline_path.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return 0
    if isinstance(loaded, dict):
        count: object = cast(dict[str, object], loaded).get("violation_count")
        if isinstance(count, int):
            return count
    return 0


def _write_baseline(baseline_path: Path, duplicates: list[tuple[str, list[Path]]], workspace_root: Path) -> None:
    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(workspace_root))
        except ValueError:
            return str(p)

    payload: dict[str, object] = {
        "violation_count": len(duplicates),
        "rule": "duplicate-gated-finalize-plans",
        "source": "duplicate_finalize_plans_created_for_one_parent_2026_08_06.md todo 2",
        "baseline_parents": {slug: [_rel(p) for p in paths] for slug, paths in duplicates},
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Corpus-wide duplicate-gated-finalize-plan detector.")
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[2].parent)
    parser.add_argument("--baseline-path", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--baseline-write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)
    quiet: bool = cast(bool, ns.quiet)

    active_dir = _resolve_active_dir(workspace_root)
    if active_dir is None:
        print(f"ERROR: plans/active not found under {workspace_root}", file=sys.stderr)
        return 2

    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    duplicates = sorted((slug, paths) for slug, paths in _gated_by(all_plans).items() if len(paths) >= 2)

    if not quiet:
        print(f"Duplicate-gated-finalize-plan count: {len(duplicates)} (0 = clean).")
        for slug, paths in duplicates:
            rels = ", ".join(str(p) for p in paths)
            print(f"  - parent '{slug}' gated by {len(paths)} finalize plans: {rels}")

    if baseline_write:
        _write_baseline(baseline_path, duplicates, workspace_root)
        if not quiet:
            print(f"✅ Wrote baseline ({len(duplicates)} duplicate-gated parent(s)) to {baseline_path}")
        return 0

    if strict:
        if duplicates:
            print(f"\n❌ STRICT: {len(duplicates)} duplicate-gated parent(s).")
            return 1
        if not quiet:
            print("✅ check_duplicate_gated_finalize_plans: clean.")
        return 0

    baseline = _load_baseline_count(baseline_path)
    if len(duplicates) > baseline:
        print(
            f"\n❌ Regression: {len(duplicates)} > baseline {baseline}. A NEW parent is now gated by >1 "
            "finalize plan -- port the loser's unique todos into the survivor, then supersede it "
            "(port-then-supersede procedure: duplicate_finalize_plans_created_for_one_parent_2026_08_06.md's "
            "2026-08-06 Progress Log entry)."
        )
        return 1
    if len(duplicates) < baseline and not quiet:
        print(f"\n⚠️  Improvement: {len(duplicates)} < baseline {baseline}. Re-baseline to codify.")

    if not quiet:
        print(f"\n✅ At baseline ({baseline} duplicate-gated parent(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
