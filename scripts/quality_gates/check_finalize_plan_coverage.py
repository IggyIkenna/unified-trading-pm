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

Second check (added 2026-07-30, same script — shares the frontmatter-loading infra):
a finalize plan (`depends_on` + `gate_on_depends: true`) sitting at `status: draft` is a
REDUNDANT double-gate, not a safety feature. `gate_on_depends` already machine-holds the
plan's tasks until its upstream is done (`_wire_gate_on_depends_prereqs` in
`regen_backlog_from_plan.py` covers both an already-active upstream via
`prereqs.completed_tasks` and a still-draft upstream via a derived
`gate-upstream-open:<stem>` condition read off the upstream file directly) — so stacking
`status: draft` on top requires a SEPARATE manual flip that nothing automates and nobody
reliably remembers. A 2026-07-30 corpus audit found 46 finalize plans stuck in draft this
way, most with their upstream already done and archived weeks earlier. Fix: author/ship
finalize plans `status: active` from the start (`ag-closeout-audit` SKILL.md corrected the
same day). This check ratchets that fix so it can't silently regress.

Third check — duplicate-gate detector (added 2026-08-11,
duplicate_finalize_plans_created_for_one_parent_2026_08_06.md):
two gated finalize plans for the SAME parent slug is a latent race — once the parent's
last todos clear, BOTH become dispatchable on the same tick and run the identical archival
procedure concurrently against one target. `_gated_slugs()` returns a `set[str]` (deduped
by construction), so it cannot surface a duplicate — a parent with >1 gate reads identically
to a parent with exactly 1. `_find_duplicate_gates()` returns the actual duplicates.
Two surfaces:
  - `--check-duplicate-gates`: corpus-wide report (hygiene sweep, non-zero = review-blocking).
  - `--only` mode: when a staged plan IS a finalize plan, verify none of its parent slugs
    already have a DIFFERENT gated finalize plan — the idempotent-creation guard (todo 1).

Exit-code semantics: 0 = at/below baseline (all checks); 1 = regression (any check);
2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml


def _pm_root_or_legacy(workspace_root):
    """PM checkout root resolved by CONTENT, not by directory NAME (F7, 2026-08-10).

    See scripts/quality_gates/_pm_root.py for why. Behaviour-preserving in a canonically
    named checkout; fixes resolution when running from a git worktree."""
    import pathlib as _pathlib
    import sys as _sys

    _d = str(_pathlib.Path(__file__).resolve().parent)
    if _d not in _sys.path:
        _sys.path.insert(0, _d)
    from _pm_root import pm_root_or_legacy as _impl

    return _impl(workspace_root)


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


def _is_finalize_companion_for(cov: Coverage, parent_slug: str) -> bool:
    """Is `cov` a FINALIZE COMPANION of `parent_slug` — as opposed to a work plan
    that merely sequences after it via `depends_on` + `gate_on_depends: true`?

    The companion naming contract is `<parent>_finalize` or `<parent>_finalize_<suffix>`
    (the incident pair differed only by a redundant date suffix:
    `..._finalize.md` vs `..._finalize_2026_07_31.md`). Distinguishing companions
    from work plans is what separates a genuine duplicate-gate RACE (two companions
    running the identical 6-step archival against one target) from a legitimate
    shared-prerequisite DAG (several distinct work plans gating on one parent — they
    do different work and must NOT be flagged as duplicates).
    """
    stem = cov.path.stem
    prefix = parent_slug + "_finalize"
    return stem == prefix or stem.startswith(prefix + "_")


def _find_duplicate_gates(all_plans: list[Coverage]) -> dict[str, list[Path]]:
    """Return parent slugs that have >1 FINALIZE COMPANION plan, mapped to the plan paths.

    A duplicate gate means two or more active plans BOTH declare
    `depends_on: [<parent>]` + `gate_on_depends: true` AND both look like finalize
    companions (`<parent>_finalize*`) — so when the parent's last todo clears, BOTH
    become dispatchable on the same tick and race the identical archival procedure
    concurrently against one target. Work plans that merely gate on the parent as a
    shared prerequisite are not counted (they do different work — see
    `_is_finalize_companion_for`).

    Distinct from `_gated_slugs()` which returns a `set[str]` (deduped by
    construction — a parent with >1 gate reads identically to exactly 1).
    """
    parent_to_finalizers: dict[str, list[Path]] = {}
    for cov in all_plans:
        if not _is_finalize_plan(cov.frontmatter):
            continue
        depends_on = cov.frontmatter.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        for dep in cast(list[object], depends_on):
            if isinstance(dep, str):
                slug = dep.strip()
                if _is_finalize_companion_for(cov, slug):
                    parent_to_finalizers.setdefault(slug, []).append(cov.path)
    return {k: v for k, v in parent_to_finalizers.items() if len(v) > 1}


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


def _find_draft_gate_violations(active_dir: Path) -> list[Path]:
    """A finalize plan (`depends_on` + `gate_on_depends: true`) sitting at `status:
    draft` is a redundant double-gate — `gate_on_depends` already machine-holds it.
    Scoped to `assigned_vm: planning` only: an `NA`-track plan is never ingested
    regardless of `status`, so its draft/active state isn't this bug.
    """
    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    violations: list[Path] = []
    for cov in all_plans:
        fm = cov.frontmatter
        if fm.get("assigned_vm") != "planning":
            continue
        if not _is_finalize_plan(fm):
            continue
        if fm.get("status") == "draft":
            violations.append(cov.path)
    return violations


def _load_baseline_count(baseline_path: Path, key: str) -> int:
    if not baseline_path.exists():
        return 0
    try:
        loaded = cast(object, yaml.safe_load(baseline_path.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return 0
    if isinstance(loaded, dict):
        count: object = cast(dict[str, object], loaded).get(key)
        if isinstance(count, int):
            return count
    return 0


def _write_baseline(
    baseline_path: Path,
    violations: list[Path],
    draft_gate_violations: list[Path],
    workspace_root: Path,
) -> None:
    def _rels(paths: list[Path]) -> list[str]:
        out: list[str] = []
        for v in paths:
            try:
                out.append(str(v.relative_to(workspace_root)))
            except ValueError:
                out.append(str(v))
        return out

    payload: dict[str, object] = {
        "violation_count": len(violations),
        "draft_gate_violation_count": len(draft_gate_violations),
        "rule": "finalize-plan-coverage",
        "source": (
            "task_template.md §4 'Every AO-dispatched plan needs a gated finalize plan' (operator ruling 2026-07-24)"
        ),
        "baseline_files": _rels(violations),
        "draft_gate_baseline_files": _rels(draft_gate_violations),
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Finalize-plan-coverage check (every AO plan needs a gated finalize plan)."
    )
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[2].parent)
    parser.add_argument("--baseline-path", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--baseline-write", action="store_true")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-error output; exit code only.")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help=(
            "Blast-radius-safe precommit mode (RULE-11, mirrors check_frontmatter_schema.py's staged-files "
            "scoping): still scans the whole corpus to resolve WHICH plans are gated (that's inherently "
            "corpus-wide knowledge), but only reports/fails on violations among these specific paths — a "
            "pre-existing violation in an unrelated plan never blocks an unrelated commit. No baseline/ratchet "
            "comparison in this mode; any violation among --only paths fails immediately."
        ),
    )
    parser.add_argument(
        "--check-duplicate-gates",
        action="store_true",
        help=(
            "Corpus-wide duplicate-gate detector (duplicate_finalize_plans_created_for_one_parent_2026_08_06.md "
            "todo 2): report every parent slug named in the depends_on of >1 gate_on_depends: true plan. "
            "Non-zero count is review-blocking (absolute check, not a ratchet — there is no legitimate reason "
            "for a parent to have multiple gated finalize plans)."
        ),
    )
    return parser.parse_args(argv)


def _resolve_active_dir(workspace_root: Path) -> tuple[Path, int]:
    """Locate `plans/active` by content (F7, 2026-08-10) — see the long comment in
    the original `main()` body for the worktree-resolution rationale. Returns
    (active_dir, exit_code); exit_code is non-zero only on the hard failure path.
    """
    active_dir = (_pm_root_or_legacy(workspace_root)) / "plans" / "active"
    if active_dir.is_dir():
        return active_dir, 0
    fallback_dir = workspace_root / "plans" / "active"
    if fallback_dir.is_dir():
        return fallback_dir, 0
    self_located_dir = Path(__file__).resolve().parents[2] / "plans" / "active"
    if self_located_dir.is_dir():
        return self_located_dir, 0
    print(
        f"ERROR: plans/active not found at {active_dir}, {fallback_dir}, or {self_located_dir}",
        file=sys.stderr,
    )
    return active_dir, 2


def _run_duplicate_gate_check(active_dir: Path, workspace_root: Path, quiet: bool) -> int:
    """Corpus-wide duplicate-gate detector (`--check-duplicate-gates`): a parent
    with >1 finalize companion is a latent race — both become dispatchable on the
    same tick and run the identical archival against one target."""
    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    dup_gates = _find_duplicate_gates(all_plans)
    if not dup_gates:
        if not quiet:
            print("✅ No duplicate finalize gates (every gated parent has exactly one finalize plan).")
        return 0
    if not quiet:
        print(f"❌ {len(dup_gates)} parent slug(s) with >1 gated finalize plan — duplicate-gate race:")
        for parent, finalizers in sorted(dup_gates.items()):
            print(f"  - {parent}:")
            for f in finalizers:
                try:
                    rel = f.relative_to(workspace_root)
                except ValueError:
                    rel = f
                print(f"      {rel}")
    return 1


def _find_only_duplicate_gate_violations(active_dir: Path, only_resolved: set[Path]) -> list[Path]:
    """Idempotent-creation guard (todo 1 of duplicate_finalize_plans_created_for_one_parent_2026_08_06.md):
    a staged finalize plan must not create a duplicate companion for a parent that already has a
    DIFFERENT finalize companion. Key on the `depends_on` relationship — but only count existing
    FINALIZE COMPANIONS (`<parent>_finalize*`), never work plans that merely gate on the parent as
    a shared prerequisite (those do different work and don't race the archival). The two colliding
    files in the incident differed only by a redundant date suffix, so a guard keyed on the EXACT
    expected filename would have missed it — the `_is_finalize_companion_for` prefix match catches
    both shapes.
    """
    if not only_resolved:
        return []
    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    # Build parent→finalizer mapping from the corpus ON DISK (not including the staged
    # plan, which hasn't been committed yet).
    parent_to_finalizers: dict[str, list[Path]] = {}
    for cov in all_plans:
        if not _is_finalize_plan(cov.frontmatter):
            continue
        depends_on = cov.frontmatter.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        for dep in cast(list[object], depends_on):
            if isinstance(dep, str):
                slug = dep.strip()
                if _is_finalize_companion_for(cov, slug):
                    parent_to_finalizers.setdefault(slug, []).append(cov.path)
    duplicate_gate_violations: list[Path] = []
    for o in only_resolved:
        staged = _load_plan(o)
        if staged is None or not _is_finalize_plan(staged.frontmatter):
            continue
        depends_on = staged.frontmatter.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        for dep in cast(list[object], depends_on):
            if not isinstance(dep, str):
                continue
            parent = dep.strip()
            # Exclude the staged plan ITSELF — it may already be on disk
            # (test fixture) or not yet committed (real pre-commit scenario).
            existing = [p for p in parent_to_finalizers.get(parent, []) if p.resolve() != o.resolve()]
            if existing:
                duplicate_gate_violations.append(o)
                break
    return duplicate_gate_violations


def _run_only_mode(
    active_dir: Path,
    only: list[str],
    violations: list[Path],
    draft_gate_violations: list[Path],
) -> int:
    """--only (staged-files) mode: report/fail on violations among the given paths
    only — the corpus scan already ran in full (gating is inherently corpus-wide),
    only the reported/failed set narrows. A plan outside --only that's ALSO in
    violation is silently not-our-problem here, same as check_frontmatter_schema.py's
    staged-files scoping (foreign_dirty_frontmatter_blocks_every_agents_gate_2026_07_18).
    """
    only_resolved = {Path(o).resolve() for o in only}
    violations = [v for v in violations if v.resolve() in only_resolved]
    draft_gate_violations = [v for v in draft_gate_violations if v.resolve() in only_resolved]
    duplicate_gate_violations = _find_only_duplicate_gate_violations(active_dir, only_resolved)

    if not violations and not draft_gate_violations and not duplicate_gate_violations:
        print("✅ finalize-plan-coverage (--only): clean.")
        return 0
    if violations:
        print(
            "❌ Plan(s) missing a gated finalize plan (add depends_on: [<this-slug>] + gate_on_depends: true"
            " to a new/existing companion plan — see task_template.md §4):"
        )
        for v in violations:
            print(f"  - {v}")
    if draft_gate_violations:
        print(
            "❌ Finalize plan(s) redundantly stuck at status: draft (gate_on_depends already holds them —"
            " flip to status: active, see task_template.md §4):"
        )
        for v in draft_gate_violations:
            print(f"  - {v}")
    if duplicate_gate_violations:
        print(
            "❌ Staged finalize plan(s) would create a duplicate gate — parent already has a gated"
            " finalize plan (key on depends_on, not filename; the existing plan may have a different"
            " filename shape — port any unique todos into the survivor, then supersede the duplicate):"
        )
        for v in duplicate_gate_violations:
            print(f"  - {v}")
    return 1


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)
    only: list[str] | None = cast("list[str] | None", ns.only)
    check_duplicate_gates: bool = cast(bool, ns.check_duplicate_gates)
    quiet: bool = cast(bool, ns.quiet)

    active_dir, rc = _resolve_active_dir(workspace_root)
    if rc != 0:
        return rc

    violations = _find_violations(active_dir)
    draft_gate_violations = _find_draft_gate_violations(active_dir)

    # ── --check-duplicate-gates: corpus-wide duplicate-gate detector ──
    if check_duplicate_gates:
        return _run_duplicate_gate_check(active_dir, workspace_root, quiet)

    if only is not None:
        return _run_only_mode(active_dir, only, violations, draft_gate_violations)

    print(
        f"Scanned plans/active/ for assigned_vm: planning plans lacking a gated finalize plan — "
        f"{len(violations)} violation(s)."
    )
    print(
        f"Scanned plans/active/ for finalize plans redundantly stuck at status: draft — "
        f"{len(draft_gate_violations)} violation(s)."
    )

    if baseline_write:
        _write_baseline(baseline_path, violations, draft_gate_violations, workspace_root)
        print(
            f"✅ Wrote baseline ({len(violations)} coverage / {len(draft_gate_violations)} draft-gate "
            f"violations) to {baseline_path}"
        )
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

    if draft_gate_violations:
        print(
            "\nFinalize plans redundantly stuck at status: draft (gate_on_depends already holds them —"
            " flip to status: active, see task_template.md §4 / ag-closeout-audit SKILL.md 2026-07-30 fix):"
        )
        for v in draft_gate_violations[:20]:
            try:
                rel = v.relative_to(workspace_root)
            except ValueError:
                rel = v
            print(f"  - {rel}")
        if len(draft_gate_violations) > 20:
            print(f"  ... + {len(draft_gate_violations) - 20} more")

    if strict:
        if violations or draft_gate_violations:
            print(f"\n❌ STRICT: {len(violations)} coverage + {len(draft_gate_violations)} draft-gate violation(s).")
            return 1
        return 0

    baseline = _load_baseline_count(baseline_path, "violation_count")
    draft_gate_baseline = _load_baseline_count(baseline_path, "draft_gate_violation_count")
    regressed = False
    if len(violations) > baseline:
        print(
            f"\n❌ Regression: {len(violations)} > baseline {baseline}. New AO plan(s) shipped without a gated"
            " finalize plan — author one before merging (task_template.md §4)."
        )
        regressed = True
    elif len(violations) < baseline:
        print(f"\n⚠️  Improvement: {len(violations)} < baseline {baseline}. Re-baseline to codify.")

    if len(draft_gate_violations) > draft_gate_baseline:
        print(
            f"\n❌ Regression: {len(draft_gate_violations)} > baseline {draft_gate_baseline}. A finalize plan shipped"
            " (or reverted to) status: draft — flip to active, gate_on_depends already holds it."
        )
        regressed = True
    elif len(draft_gate_violations) < draft_gate_baseline:
        print(
            f"\n⚠️  Improvement: {len(draft_gate_violations)} < baseline {draft_gate_baseline}. Re-baseline to codify."
        )

    if regressed:
        return 1
    print(f"\n✅ At baseline ({baseline} coverage / {draft_gate_baseline} draft-gate).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
