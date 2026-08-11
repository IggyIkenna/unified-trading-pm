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

Third mode (added 2026-08-11, issue duplicate_finalize_plans_created_for_one_parent todo 1):
finalize-plan CREATION is idempotent at the point of creation. Two gated finalize plans for the
SAME parent (differing only by a redundant date suffix) were both created 2026-07-31 against
`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31` — nothing refused the second
author because the remediation path had no create-time guard. `--assert-not-gated <parent-slug>`
re-derives the gate set over the CURRENT corpus and refuses (exit 1) if the parent already has a
`depends_on` + `gate_on_depends: true` finalize plan, regardless of that plan's filename shape.
The `--only` precommit mode applies the same refusal to a STAGED finalize plan whose parent is
already gated by a DIFFERENT plan in the corpus, so the two-agents race can never land even if
the author skipped the pre-flight guard.

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


def _gating_plans(all_plans: list[Coverage], parent_slug: str) -> list[Path]:
    """Existing finalize plans whose `depends_on` names `parent_slug`.

    The gate contract is the depends_on relationship, NOT the filename: two colliding finalize
    plans for one parent can differ only by a redundant date suffix (`<parent>_finalize.md` vs
    `<parent>_finalize_<date>.md`), so any guard keyed on the expected filename shape would miss
    the duplicate. Returns the gating plan paths so callers can name exactly what already covers
    the parent (issue duplicate_finalize_plans_created_for_one_parent).
    """
    out: list[Path] = []
    for cov in all_plans:
        if not _is_finalize_plan(cov.frontmatter):
            continue
        depends_on = cov.frontmatter.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        for dep in cast(list[object], depends_on):
            if isinstance(dep, str) and dep.strip() == parent_slug:
                out.append(cov.path)
                break
    return out


def _staged_duplicate_gates(all_plans: list[Coverage], only_resolved: set[Path]) -> list[tuple[Path, list[str]]]:
    """For each STAGED finalize plan, the parents that are ALREADY gated by a DIFFERENT finalize
    plan in the corpus (the staged file's own gate contribution excluded).

    A hit means creating this file would duplicate the gate for that parent — the exact
    two-agents race issue duplicate_finalize_plans_created_for_one_parent documents. Used by the
    `--only` prek precommit path so the refusal fires at the point of creation even when the
    author never ran the pre-flight `--assert-not-gated` guard.
    """
    out: list[tuple[Path, list[str]]] = []
    for cov in all_plans:
        if cov.path.resolve() not in only_resolved:
            continue
        if not _is_finalize_plan(cov.frontmatter):
            continue
        depends_on = cov.frontmatter.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        parents = [d.strip() for d in cast(list[object], depends_on) if isinstance(d, str) and d.strip()]
        if not parents:
            continue
        others = [c for c in all_plans if c.path != cov.path]
        already_gated = _gated_slugs(others)
        dupe_parents = [p for p in parents if p in already_gated]
        if dupe_parents:
            out.append((cov.path, dupe_parents))
    return out


def _find_violations(all_plans: list[Coverage]) -> list[Path]:
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


def _find_draft_gate_violations(all_plans: list[Coverage]) -> list[Path]:
    """A finalize plan (`depends_on` + `gate_on_depends: true`) sitting at `status:
    draft` is a redundant double-gate — `gate_on_depends` already machine-holds it.
    Scoped to `assigned_vm: planning` only: an `NA`-track plan is never ingested
    regardless of `status`, so its draft/active state isn't this bug.
    """
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


def _run_assert_not_gated(active_dir: Path, parent_slug: str) -> int:
    """Create-time idempotency guard (issue duplicate_finalize_plans_created_for_one_parent,
    todo 1). Re-derives the gate set over the CURRENT corpus via `_gating_plans()` — keyed on
    the depends_on relationship, never the filename shape — and refuses (exit 1) if
    `parent_slug` already has a gated finalize plan. Run BEFORE authoring a new
    `<parent>_finalize*.md`; exit 0 = safe to create.
    """
    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    gating = _gating_plans(all_plans, parent_slug)
    if gating:
        print(
            f"❌ REFUSE: parent slug '{parent_slug}' already has a gated finalize plan "
            "(depends_on + gate_on_depends: true) — creating another <parent>_finalize*.md "
            "would duplicate the gate:"
        )
        for g in gating:
            print(f"  - {g}")
        print(
            "  Reconcile instead: fold any remaining work into the existing finalize plan "
            "(append its todos), or de-race with the port-then-supersede procedure — never "
            "create a competing finalize plan."
        )
        return 1
    print(f"✅ safe-to-create: '{parent_slug}' has no gated finalize plan in the current corpus.")
    return 0


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
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--assert-not-gated",
        metavar="PARENT_SLUG",
        default=None,
        help=(
            "Create-time idempotency guard (issue duplicate_finalize_plans_created_for_one_parent "
            "todo 1): exit 1 (REFUSE) if PARENT_SLUG already has a gated finalize plan "
            "(depends_on + gate_on_depends: true) in the current corpus — regardless of the "
            "gating plan's filename shape. Run BEFORE authoring a new <parent>_finalize*.md. "
            "Exit 0 = safe to create."
        ),
    )
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
    return parser.parse_args(argv)


def _run_only_mode(
    all_plans: list[Coverage],
    violations: list[Path],
    draft_gate_violations: list[Path],
    only: list[str],
) -> int:
    """Blast-radius-safe precommit mode (RULE-11, mirrors check_frontmatter_schema.py's staged-files
    scoping): resolve each given path (relative-to-cwd or absolute both work — argparse hands us
    whatever the caller typed) and keep just the violations that ARE one of them. The corpus scan
    ran in full in main() (gating is inherently corpus-wide); only the reported/failed set narrows,
    so a pre-existing violation in an unrelated plan never blocks an unrelated commit.

    Extends the coverage check with the create-time duplicate-gate refusal (issue
    duplicate_finalize_plans_created_for_one_parent todo 1): a STAGED finalize plan whose parent is
    already gated by a DIFFERENT finalize plan in the corpus would duplicate the gate — refuse it
    here so the two-agents race (each author's file staged on its own commit, the earlier one
    already in the corpus) can never land even if the author skipped --assert-not-gated.
    """
    only_resolved = {Path(o).resolve() for o in only}
    violations = [v for v in violations if v.resolve() in only_resolved]
    draft_gate_violations = [v for v in draft_gate_violations if v.resolve() in only_resolved]
    duplicate_gates = _staged_duplicate_gates(all_plans, only_resolved)
    if not violations and not draft_gate_violations and not duplicate_gates:
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
    if duplicate_gates:
        print(
            "❌ Staged finalize plan(s) whose parent already has a gated finalize plan (a second"
            " <parent>_finalize*.md duplicates the gate — reconcile into the existing plan, or"
            " port-then-supersede it, never create a competing one):"
        )
        for path, parents in duplicate_gates:
            print(f"  - {path} — parent already gated: {', '.join(parents)}")
    return 1


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
                print(
                    f"ERROR: plans/active not found at {active_dir}, {fallback_dir}, or {self_located_dir}",
                    file=sys.stderr,
                )
                return 2

    # Create-time idempotency guard (issue duplicate_finalize_plans_created_for_one_parent, todo 1):
    # `--assert-not-gated <parent>` refuses (exit 1) to create a new <parent>_finalize*.md when the
    # parent already has a gated finalize plan in the CURRENT corpus — keyed on the depends_on
    # relationship via `_gating_plans()`, never the filename shape.
    if ns.assert_not_gated is not None:
        return _run_assert_not_gated(active_dir, ns.assert_not_gated)

    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    violations = _find_violations(all_plans)
    draft_gate_violations = _find_draft_gate_violations(all_plans)

    if only is not None:
        return _run_only_mode(all_plans, violations, draft_gate_violations, only)

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
