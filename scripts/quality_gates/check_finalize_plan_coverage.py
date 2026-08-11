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

Exit-code semantics: 0 = at/below baseline (both checks); 1 = regression (either check);
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


def _find_duplicate_gates(active_dir: Path) -> list[tuple[str, list[Path]]]:
    """Find parent slugs named in depends_on of >1 gate_on_depends: true plan.

    Returns a list of (parent_slug, [finalize_plan_path, ...]) for duplicates only,
    sorted by parent_slug for deterministic output.  Keyed on the depends_on
    relationship — the filename shape is irrelevant, same as the real incident's
    two collision files differed only by a redundant date suffix.
    """
    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    slug_to_paths: dict[str, list[Path]] = {}
    for cov in all_plans:
        if not _is_finalize_plan(cov.frontmatter):
            continue
        depends_on = cov.frontmatter.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        for dep in cast(list[object], depends_on):
            if isinstance(dep, str):
                dep_slug = dep.strip()
                if dep_slug not in slug_to_paths:
                    slug_to_paths[dep_slug] = []
                slug_to_paths[dep_slug].append(cov.path)
    result = [(slug, paths) for slug, paths in slug_to_paths.items() if len(paths) > 1]
    result.sort(key=lambda x: x[0])
    return result


def _parent_already_gated(parent_slug: str, active_dir: Path) -> tuple[bool, list[Path]]:
    """Check whether *parent_slug* already has at least one gated finalize plan.

    Returns ``(True, [paths of gating plans])`` if already gated, ``(False, [])``
    if not.  Keyed on the ``depends_on`` relationship — not filename shape — so a
    guard calling this before writing a new ``<parent>_finalize*.md`` catches the
    exact collision class the 2026-07-31 duplicate-finalize-plan incident produced.
    """
    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    gated = _gated_slugs(all_plans)
    if parent_slug not in gated:
        return (False, [])
    existing: list[Path] = []
    for cov in all_plans:
        if not _is_finalize_plan(cov.frontmatter):
            continue
        depends_on = cov.frontmatter.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        for dep in cast(list[object], depends_on):
            if isinstance(dep, str) and dep.strip() == parent_slug:
                existing.append(cov.path)
                break
    return (True, existing)


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
    duplicate_gate_violations: int = 0,
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
        "duplicate_gate_violation_count": duplicate_gate_violations,
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
        "--check-parent-gated",
        type=str,
        default=None,
        help=(
            "Check if a parent slug already has a gated finalize plan (idempotency guard). "
            "Exits 0 if safe to create, 1 if already gated."
        ),
    )
    parser.add_argument(
        "--duplicate-gate-only",
        action="store_true",
        help="Run only the duplicate-gate detector (parent with >1 gated finalize plan).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output; exit code only.",
    )
    return parser.parse_args(argv)


def _run_check_parent_gated(
    parent_slug: str,
    active_dir: Path,
    workspace_root: Path,
    quiet: bool,
) -> int:
    """``--check-parent-gated`` mode: idempotency guard for finalize-plan creation.

    Returns 0 if *parent_slug* is safe to gate (no existing finalize plan), 1 if
    already gated (creation would be a duplicate).
    """
    already_gated, existing = _parent_already_gated(parent_slug, active_dir)
    if already_gated:
        rel_paths: list[str] = []
        for p in existing:
            try:
                rel_paths.append(str(p.relative_to(workspace_root)))
            except ValueError:
                rel_paths.append(str(p))
        print(
            f"REFUSED: parent '{parent_slug}' already has {len(existing)} gated finalize plan(s):",
            file=sys.stderr,
        )
        for rp in rel_paths:
            print(f"  - {rp}", file=sys.stderr)
        return 1
    if not quiet:
        print(f"OK: parent '{parent_slug}' is not yet gated — safe to create a finalize plan.")
    return 0


def _run_duplicate_gate_only(
    active_dir: Path,
    workspace_root: Path,
    baseline_path: Path,
    baseline_write: bool,
    strict: bool,
    only: list[str] | None,
    quiet: bool,
) -> int:
    """``--duplicate-gate-only`` mode: corpus-wide duplicate-gate detector.

    Finds parent slugs named in ``depends_on`` of more than one
    ``gate_on_depends: true`` plan and compares against a shrinking-ratchet
    baseline.  Returns 0 at/below baseline, 1 on regression.
    """
    duplicates = _find_duplicate_gates(active_dir)

    if only is not None:
        only_resolved = {Path(o).resolve() for o in only}
        duplicates = [(slug, [p for p in paths if p.resolve() in only_resolved]) for slug, paths in duplicates]
        duplicates = [(slug, paths) for slug, paths in duplicates if paths]

    if not quiet:
        print(f"Scanned plans/active/ for parent slugs with >1 gated finalize plan — {len(duplicates)} duplicate(s).")
        if duplicates:
            print("\nParent slugs with duplicate gated finalize plans:")
            for slug, paths in duplicates:
                print(f"  - '{slug}':")
                for p in paths:
                    try:
                        print(f"      {p.relative_to(workspace_root)}")
                    except ValueError:
                        print(f"      {p}")

    if baseline_write:
        _write_baseline(
            baseline_path,
            violations=[],
            draft_gate_violations=[],
            workspace_root=workspace_root,
            duplicate_gate_violations=len(duplicates),
        )
        if not quiet:
            print(f"✅ Wrote baseline ({len(duplicates)} duplicate-gate violations) to {baseline_path}")
        return 0

    if strict:
        if duplicates:
            if not quiet:
                print(f"\n❌ STRICT: {len(duplicates)} duplicate-gate violation(s).")
            return 1
        if not quiet:
            print("\n✅ STRICT: no duplicate-gate violations.")
        return 0

    baseline = _load_baseline_count(baseline_path, "duplicate_gate_violation_count")
    if len(duplicates) > baseline:
        if not quiet:
            print(
                f"\n❌ Regression: {len(duplicates)} > baseline {baseline}. A parent now has >1 gated"
                " finalize plan — de-race before merging (port unique todos to the survivor, supersede"
                " the duplicate)."
            )
        return 1
    elif len(duplicates) < baseline:
        if not quiet:
            print(f"\n⚠️  Improvement: {len(duplicates)} < baseline {baseline}. Re-baseline to codify.")

    if not quiet:
        print(f"\n✅ At baseline ({baseline} duplicate-gate).")
    return 0


def _resolve_active_dir(workspace_root: Path) -> Path | None:
    """Resolve ``plans/active/`` under the PM checkout, with three fallback strategies.

    Returns the resolved directory, or ``None`` when every strategy fails (caller
    prints the error and exits 2).
    """
    active_dir = (_pm_root_or_legacy(workspace_root)) / "plans" / "active"
    if active_dir.is_dir():
        return active_dir
    fallback_dir = workspace_root / "plans" / "active"
    if fallback_dir.is_dir():
        return fallback_dir
    self_located_dir = Path(__file__).resolve().parents[2] / "plans" / "active"
    if self_located_dir.is_dir():
        return self_located_dir
    return None


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)
    only: list[str] | None = cast("list[str] | None", ns.only)

    # The normal (sibling-checkout) workspace layout is `<workspace_root>/unified-trading-pm/plans/active`
    # (all existing tests construct exactly this shape) — preserved as the first candidate below. An
    # isolated per-agent worktree (`git worktree add` under `<pm-checkout>/.claude/worktrees/agent-*`,
    # per /codex/05-infrastructure/per-tab-worktrees.md) breaks that assumption two ways at once: the
    # checkout's own directory is NOT named `unified-trading-pm`, AND run_hygiene_sweep.sh's
    # `--workspace-root "$(dirname "$PM_DIR")"` passes the checkout's PARENT (one hop too far — neither
    # `<parent>/unified-trading-pm/plans/active` nor `<parent>/plans/active` exists; the real
    # `plans/active` lives directly under `$PM_DIR` itself, i.e. two hops up from THIS script's own
    # location). This used to hard-fail with a bare "ERROR: plans/active not found" instead of ever
    # running the actual check — a false gate-block unrelated to any real violation (found 2026-08-08
    # while committing a plan-only change from exactly this worktree shape). Self-locate as the last
    # resort: this script always physically lives at `<pm-checkout>/scripts/quality_gates/<this file>`,
    # so `parents[2]` (quality_gates -> scripts -> checkout root, three hops up) is always the real
    # checkout root regardless of what `--workspace-root` was given or what the checkout directory
    # happens to be named.
    active_dir = _resolve_active_dir(workspace_root)
    if active_dir is None:
        print(
            f"ERROR: plans/active not found — tried _pm_root_or_legacy({workspace_root}), "
            f"{workspace_root / 'plans' / 'active'}, and self-locate from {__file__}",
            file=sys.stderr,
        )
        return 2

    # ── --check-parent-gated: idempotency guard for finalize-plan creation (todo 1) ──
    if ns.check_parent_gated is not None:
        return _run_check_parent_gated(ns.check_parent_gated, active_dir, workspace_root, ns.quiet)

    # ── --duplicate-gate-only: corpus-wide duplicate-gate detector (todo 2) ──
    if ns.duplicate_gate_only:
        return _run_duplicate_gate_only(
            active_dir,
            workspace_root,
            baseline_path,
            baseline_write,
            strict,
            only,
            ns.quiet,
        )

    violations = _find_violations(active_dir)
    draft_gate_violations = _find_draft_gate_violations(active_dir)

    if only is not None:
        # --only: resolve each given path the same way (relative-to-cwd or absolute both work,
        # since argparse hands us whatever the caller typed) and keep just the violations that
        # ARE one of them — the corpus scan above still ran in full (gating is inherently
        # corpus-wide), only the reported/failed set narrows. A plan outside --only that's
        # ALSO in violation is silently not-our-problem here, same as check_frontmatter_schema.py's
        # staged-files scoping (foreign_dirty_frontmatter_blocks_every_agents_gate_2026_07_18).
        only_resolved = {Path(o).resolve() for o in only}
        violations = [v for v in violations if v.resolve() in only_resolved]
        draft_gate_violations = [v for v in draft_gate_violations if v.resolve() in only_resolved]
        if not violations and not draft_gate_violations:
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
        return 1

    print(
        f"Scanned plans/active/ for assigned_vm: planning plans lacking a gated finalize plan — "
        f"{len(violations)} violation(s)."
    )
    print(
        f"Scanned plans/active/ for finalize plans redundantly stuck at status: draft — "
        f"{len(draft_gate_violations)} violation(s)."
    )

    if baseline_write:
        dup_count = len(_find_duplicate_gates(active_dir))
        _write_baseline(baseline_path, violations, draft_gate_violations, workspace_root, dup_count)
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
