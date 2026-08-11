#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Catch parents with >1 gated finalize plan — the duplicate-gate bug class.

`check_finalize_plan_coverage.py::_gated_slugs()` is a ``set[str]`` — it dedupes by
construction, so it correctly answers "is this parent gated?" but cannot surface when
TWO different finalize plans both gate on the same parent.  That is this script's job:
flag any parent slug named in the ``depends_on`` of MORE THAN ONE
``gate_on_depends: true`` plan.

The bug class was discovered 2026-08-06 when two finalize plans were created the same
day for the same parent, each justified by "no companion gated finalize plan exists"
— both would have gone dispatchable on the same tick and raced the identical 6-step
archival.  See: `plans/active/issues/duplicate_finalize_plans_created_for_one_parent_2026_08_06.md`.

SHRINKING ratchet (same shape as check_terminal_status_archived.py /
check_reference_paths.py): NOT zero-tolerance from day 1.  A live count EXCEEDING the
baseline means a NEW duplicate appeared, which IS mechanically wrong.  Fix by
de-racing per the issue doc's procedure: port any unique todos from the loser into the
survivor FIRST, then set ``superseded_by``/``supersedes`` + a dated banner.

Usage:
  python3 scripts/plan-hygiene/check_duplicate_finalize_gates.py [--quiet]
  python3 scripts/plan-hygiene/check_duplicate_finalize_gates.py --update-baseline
Exit 0 if the duplicate count is <= baseline.  NEVER hand-raise a baseline entry.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

BASELINE_PATH = Path(__file__).resolve().parent / "duplicate_finalize_gates_baseline.yaml"


@dataclass(frozen=True)
class Coverage:
    path: Path
    frontmatter: dict[str, object]


def _load_plan(p: Path) -> Coverage | None:
    import re

    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    m = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL).match(text)
    if not m:
        return None
    try:
        loaded = cast(object, yaml.safe_load(m.group(1)))
    except yaml.YAMLError:
        return None
    if not isinstance(loaded, dict):
        return None
    return Coverage(path=p, frontmatter=cast(dict[str, object], loaded))


def _is_finalize_plan(fm: dict[str, object]) -> bool:
    depends_on = fm.get("depends_on")
    gate = fm.get("gate_on_depends")
    has_deps = isinstance(depends_on, list) and len(cast(list[object], depends_on)) > 0
    return bool(has_deps and gate is True)


def _find_duplicate_gates(all_plans: list[Coverage]) -> dict[str, list[Path]]:
    """Parents with MORE THAN ONE gated finalize plan."""
    parent_to_finalizers: dict[str, list[Path]] = {}
    for cov in all_plans:
        if not _is_finalize_plan(cov.frontmatter):
            continue
        depends_on = cov.frontmatter.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        for dep in cast(list[object], depends_on):
            if isinstance(dep, str):
                parent = dep.strip()
                parent_to_finalizers.setdefault(parent, []).append(cov.path)
    return {p: fps for p, fps in parent_to_finalizers.items() if len(fps) > 1}


def _load_baseline_count() -> int:
    if not BASELINE_PATH.exists():
        return 0
    try:
        loaded = cast(object, yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return 0
    if isinstance(loaded, dict):
        cnt: object = cast(dict[str, object], loaded).get("duplicate_parent_count")
        if isinstance(cnt, int):
            return cnt
    return 0


def _write_baseline(count: int, duplicates: dict[str, list[Path]], workspace_root: Path) -> None:
    def _rels(paths: list[Path]) -> list[str]:
        out: list[str] = []
        for v in paths:
            try:
                out.append(str(v.relative_to(workspace_root)))
            except ValueError:
                out.append(str(v))
        return out

    detail = {parent: _rels(paths) for parent, paths in duplicates.items()}
    payload: dict[str, object] = {
        "duplicate_parent_count": count,
        "rule": "duplicate-finalize-gates",
        "source": ("plans/active/issues/duplicate_finalize_plans_created_for_one_parent_2026_08_06.md"),
        "detail": detail,
    }
    BASELINE_PATH.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _pm_root_or_legacy(workspace_root: Path) -> Path:
    import pathlib as _pathlib

    _d = str(_pathlib.Path(__file__).resolve().parents[1] / "quality_gates")
    if _d not in sys.path:
        sys.path.insert(0, _d)
    from _pm_root import pm_root_or_legacy as _impl

    return _impl(workspace_root)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Duplicate-finalize-gate check (>1 gated finalize plan for same parent)."
    )
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[2].parent)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    quiet: bool = cast(bool, ns.quiet)

    active_dir = (_pm_root_or_legacy(workspace_root)) / "plans" / "active"
    if not active_dir.is_dir():
        fallback_dir = workspace_root / "plans" / "active"
        if fallback_dir.is_dir():
            active_dir = fallback_dir
        else:
            self_located_dir = Path(__file__).resolve().parents[2] / "plans" / "active"
            if self_located_dir.is_dir():
                active_dir = self_located_dir
            else:
                if not quiet:
                    print(
                        f"ERROR: plans/active not found at {active_dir}, {fallback_dir}, or {self_located_dir}",
                        file=sys.stderr,
                    )
                return 2

    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    duplicates = _find_duplicate_gates(all_plans)
    dup_count = len(duplicates)

    if ns.update_baseline:
        _write_baseline(dup_count, duplicates, workspace_root)
        if not quiet:
            print(f"✅ Wrote baseline ({dup_count} duplicate-gate parent(s)) to {BASELINE_PATH}")
            if duplicates:
                for parent, paths in sorted(duplicates.items()):
                    print(f"  parent='{parent}' → {len(paths)} finalize plans:")
                    for fp in paths:
                        try:
                            rel = fp.relative_to(workspace_root)
                        except ValueError:
                            rel = fp
                        print(f"      - {rel}")
        return 0

    baseline = _load_baseline_count()

    if dup_count > baseline:
        if not quiet:
            print(
                f"❌ DUPLICATE GATE REGRESSION: {dup_count} > baseline {baseline}. "
                f"{dup_count} parent(s) have >1 gated finalize plan — de-race per "
                f"plans/active/issues/duplicate_finalize_plans_created_for_one_parent_2026_08_06.md:"
            )
            for parent, paths in sorted(duplicates.items()):
                print(f"  parent='{parent}' → {len(paths)} finalize plans:")
                for fp in paths:
                    try:
                        rel = fp.relative_to(workspace_root)
                    except ValueError:
                        rel = fp
                    print(f"      - {rel}")
        return 1

    if not quiet:
        if dup_count == 0:
            print("✅ No duplicate finalize gates (0 parents with >1 gated finalize plan).")
        else:
            print(f"✅ At baseline ({dup_count} duplicate-gate parent(s), baseline {baseline}).")
            for parent, paths in sorted(duplicates.items()):
                print(f"  parent='{parent}' → {len(paths)} finalize plans:")
                for fp in paths:
                    try:
                        rel = fp.relative_to(workspace_root)
                    except ValueError:
                        rel = fp
                    print(f"      - {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
