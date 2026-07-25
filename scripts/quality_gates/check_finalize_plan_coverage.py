#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Every AO-dispatched (`assigned_vm: planning`) plan needs a gated finalize plan.

Operator ruling 2026-07-24 (task_template.md §4): a batch/source AO plan that ships
its own todos but never gets a companion `depends_on: [<slug>] + gate_on_depends: true`
finalize plan leaves two things stuck forever: source-doc checkboxes never get
reconciled (for extraction-style batch plans), and the plan itself never goes through
the archival ritual. This check finds `assigned_vm: planning` plans with NO other
active plan gating on them, per the pattern shipped for
`sports_closeout_batch1_ao_ready_2026_07_24.md` / `sports_closeout_batch1_finalize_2026_07_24.md`
and `sports_satellite_ao_dispatch_batch2_2026_07_24.md` /
`sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`.

Exemptions (not violations):
  - The plan IS ITSELF a finalize plan (has its own `depends_on` + `gate_on_depends: true`)
    — no infinite regress.
  - The plan has exactly 1 open todo — trivial enough to fold archival into that todo's
    own done-when, per task_template.md's explicit single-todo carve-out.
  - `assigned_vm` is NOT `planning` (LOCAL/NA plans are untouched by AO dispatch, so this
    rule doesn't apply — archival there is a human call, not a machine-gate concern).

Exit-code semantics: 0 = at/below baseline; 1 = regression; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

DEFAULT_BASELINE_PATH = Path(__file__).parent / "finalize_plan_coverage_baseline.yaml"

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_TODO_RE = re.compile(r"^-\s+\[[ x]\]\s+\[\w+\]\s+P\d\.", re.MULTILINE)


@dataclass(frozen=True)
class Coverage:
    path: Path
    frontmatter: dict[str, object]


def _load_plan(p: Path) -> Coverage | None:
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
    return Coverage(path=p, frontmatter=cast(dict[str, object], loaded))


def _slug(p: Path) -> str:
    return p.stem


def _todo_count(p: Path) -> int:
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    return len(_TODO_RE.findall(text))


def _is_finalize_plan(fm: dict[str, object]) -> bool:
    depends_on = fm.get("depends_on")
    gate = fm.get("gate_on_depends")
    has_deps = isinstance(depends_on, list) and len(cast(list[object], depends_on)) > 0
    return bool(has_deps and gate is True)


def _gated_slugs(all_plans: list[Coverage]) -> set[str]:
    """Every plan-slug named in some OTHER plan's depends_on + gate_on_depends: true."""
    out: set[str] = set()
    for cov in all_plans:
        if not _is_finalize_plan(cov.frontmatter):
            continue
        depends_on = cov.frontmatter.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        for dep in cast(list[object], depends_on):
            if isinstance(dep, str):
                out.add(dep.strip())
    return out


def _find_violations(active_dir: Path) -> list[Path]:
    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    gated = _gated_slugs(all_plans)

    violations: list[Path] = []
    for cov in all_plans:
        fm = cov.frontmatter
        if fm.get("assigned_vm") != "planning":
            continue
        if _is_finalize_plan(fm):
            continue  # a finalize plan doesn't need its own finalize plan
        if _todo_count(cov.path) <= 1:
            continue  # single-todo carve-out
        if _slug(cov.path) in gated:
            continue  # some other plan already gates on this one
        violations.append(cov.path)
    return violations


def _load_baseline(baseline_path: Path) -> int:
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


def _write_baseline(baseline_path: Path, violations: list[Path], workspace_root: Path) -> None:
    rels: list[str] = []
    for v in violations:
        try:
            rels.append(str(v.relative_to(workspace_root)))
        except ValueError:
            rels.append(str(v))
    payload: dict[str, object] = {
        "violation_count": len(violations),
        "rule": "finalize-plan-coverage",
        "source": (
            "task_template.md §4 'Every AO-dispatched plan needs a gated finalize plan' (operator ruling 2026-07-24)"
        ),
        "baseline_files": rels,
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Finalize-plan-coverage check (every AO plan needs a gated finalize plan)."
    )
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[2].parent)
    parser.add_argument("--baseline-path", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--baseline-write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)

    active_dir = workspace_root / "unified-trading-pm" / "plans" / "active"
    if not active_dir.is_dir():
        print(f"ERROR: plans/active not found at {active_dir}", file=sys.stderr)
        return 2

    violations = _find_violations(active_dir)
    print(
        f"Scanned plans/active/ for assigned_vm: planning plans lacking a gated finalize plan — "
        f"{len(violations)} violation(s)."
    )

    if baseline_write:
        _write_baseline(baseline_path, violations, workspace_root)
        print(f"✅ Wrote baseline ({len(violations)} violations) to {baseline_path}")
        return 0

    if violations:
        print(
            "\nPlans missing a gated finalize plan (add depends_on: [<this-slug>] + gate_on_depends: true"
            " to a new/existing companion plan — see task_template.md §4):"
        )
        for v in violations[:20]:
            try:
                rel = v.relative_to(workspace_root)
            except ValueError:
                rel = v
            print(f"  - {rel}")
        if len(violations) > 20:
            print(f"  ... + {len(violations) - 20} more")

    if strict:
        if violations:
            print(f"\n❌ STRICT: {len(violations)} violation(s).")
            return 1
        return 0

    baseline = _load_baseline(baseline_path)
    if len(violations) > baseline:
        print(
            f"\n❌ Regression: {len(violations)} > baseline {baseline}. New AO plan(s) shipped without a gated"
            " finalize plan — author one before merging (task_template.md §4)."
        )
        return 1
    if len(violations) < baseline:
        print(f"\n⚠️  Improvement: {len(violations)} < baseline {baseline}. Re-baseline to codify.")
        return 0
    print(f"\n✅ At baseline ({baseline}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
