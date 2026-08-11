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

Fourth check (added 2026-08-11, duplicate_finalize_plans_created_for_one_parent_2026_08_06.md):
a parent slug named in the `depends_on` of MORE THAN ONE active `gate_on_depends: true`
plan is a duplicate finalize gate — two gated plans racing the identical archival ritual
against one target. This is a shrinking-ratchet check (baseline: unique parents with >1
gater), kept separate from `--guard-finalize`'s create-time go/no-go.

Exit-code semantics: 0 = at/below baseline (all checks) OR safe-to-create (--guard-finalize);
1 = regression (any check) OR parent already gated (--guard-finalize); 2 = arg/IO error.
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


def _find_duplicate_gate_violations(active_dir: Path) -> dict[str, list[Path]]:
    """Find parent slugs named in the `depends_on` of MORE THAN ONE `gate_on_depends: true`
    plan — a duplicate finalize gate where two gated plans would race the identical
    archival ritual against one target. Returns a dict mapping parent_slug -> list of
    finalize-plan paths gating on it, only for parents with >1 gater.

    Scoped to `assigned_vm: planning` + `status: active` gating plans only: a superseded
    or draft finalize plan does not actually gate dispatch, and an NA-track plan is never
    ingested regardless of its frontmatter.
    """
    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]

    # Map parent_slug -> list of finalize-plan paths that gate on it
    parent_to_finalizers: dict[str, list[Path]] = {}
    for cov in all_plans:
        fm = cov.frontmatter
        if fm.get("assigned_vm") != "planning":
            continue
        if fm.get("status") != "active":
            continue
        if not _is_finalize_plan(fm):
            continue
        depends_on = fm.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        for dep in cast(list[object], depends_on):
            if isinstance(dep, str):
                parent = dep.strip()
                parent_to_finalizers.setdefault(parent, []).append(cov.path)

    return {k: v for k, v in parent_to_finalizers.items() if len(v) > 1}


def finalize_plan_collisions(parent_slug: str, active_dir: Path) -> list[Path]:
    """Existing finalize plans already gating on `parent_slug` — non-empty means authoring
    ANOTHER `<parent>_finalize*.md` would create a duplicate gate racing the identical
    archival ritual against one target. This is the `--guard-finalize` create-time check
    (duplicate_finalize_plans_created_for_one_parent_2026_08_06.md todo 1).

    Re-derives the same `depends_on` relationship `_gated_slugs()` reads, but per-parent and
    returning the specific gating plan paths for a useful refusal message. Keyed on the
    relationship, NEVER on filename shape — the live colliding pair
    (`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md` /
    `..._finalize_2026_07_31.md`) differed only by a redundant `_2026_07_31` suffix, so any
    guard keyed on the expected filename would have missed it.
    """
    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
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
    duplicate_gate_violations: dict[str, list[Path]],
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

    def _dup_rels(d: dict[str, list[Path]]) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for parent, finalizers in d.items():
            rels: list[str] = []
            for f in sorted(finalizers):
                try:
                    rels.append(str(f.relative_to(workspace_root)))
                except ValueError:
                    rels.append(str(f))
            out[parent] = rels
        return out

    payload: dict[str, object] = {
        "violation_count": len(violations),
        "draft_gate_violation_count": len(draft_gate_violations),
        "duplicate_gate_violation_count": len(duplicate_gate_violations),
        "rule": "finalize-plan-coverage",
        "source": (
            "task_template.md §4 'Every AO-dispatched plan needs a gated finalize plan' (operator ruling 2026-07-24)"
        ),
        "baseline_files": _rels(violations),
        "draft_gate_baseline_files": _rels(draft_gate_violations),
        "duplicate_gate_baseline_files": _dup_rels(duplicate_gate_violations),
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
        "--guard-finalize",
        metavar="PARENT_SLUG",
        default=None,
        help=(
            "CREATE-TIME idempotency guard (duplicate_finalize_plans_created_for_one_parent"
            "_2026_08_06.md todo 1): re-derives gating over the CURRENT corpus and refuses"
            " (exit 1) if PARENT_SLUG is already the `depends_on` target of an existing finalize"
            " plan — run BEFORE authoring a new <parent>_finalize*.md. Keyed on the depends_on"
            " relationship, never filename shape (the colliding pair differed only by a _date suffix)."
        ),
    )
    return parser.parse_args(argv)


def _handle_only_mode(
    only: list[str],
    violations: list[Path],
    draft_gate_violations: list[Path],
    duplicate_gates: dict[str, list[Path]],
) -> int:
    """Blast-radius-safe --only reporting: corpus scanned in full, but only staged-file
    violations fail. Returns 0 when clean, 1 when any staged file is in violation."""
    only_resolved = {Path(o).resolve() for o in only}
    scoped_violations = [v for v in violations if v.resolve() in only_resolved]
    scoped_draft = [v for v in draft_gate_violations if v.resolve() in only_resolved]
    all_dup_paths: set[Path] = set()
    for _df in duplicate_gates.values():
        all_dup_paths.update(_df)
    dup_only = sorted(p for p in all_dup_paths if p.resolve() in only_resolved)

    if not scoped_violations and not scoped_draft and not dup_only:
        print("✅ finalize-plan-coverage (--only): clean.")
        return 0

    if scoped_violations:
        print(
            "❌ Plan(s) missing a gated finalize plan (add depends_on: [<this-slug>]"
            " + gate_on_depends: true to a new/existing companion plan — see"
            " task_template.md §4):"
        )
        for v in scoped_violations:
            print(f"  - {v}")
    if scoped_draft:
        print(
            "❌ Finalize plan(s) redundantly stuck at status: draft (gate_on_depends"
            " already holds them — flip to status: active, see task_template.md §4):"
        )
        for v in scoped_draft:
            print(f"  - {v}")
    if dup_only:
        print(
            "❌ Duplicate finalize-plan gate(s) — a parent has >1 active"
            " gate_on_depends: true plan, which would race the identical archival"
            " ritual against one target. De-race: port any todo unique to the loser"
            " into the survivor, then supersede the loser (see"
            " plan-completion-and-archival-discipline.md §1):"
        )
        for parent, finalizers in sorted(duplicate_gates.items()):
            staged = [f for f in finalizers if f.resolve() in only_resolved]
            if not staged:
                continue
            print(f"  Parent: {parent}")
            for f in sorted(finalizers):
                marker = " ← STAGED" if f.resolve() in only_resolved else ""
                print(f"    - {f}{marker}")
    return 1


def _check_baseline_regression(
    violations: list[Path],
    draft_gate_violations: list[Path],
    duplicate_gates: dict[str, list[Path]],
    baseline_path: Path,
) -> int:
    """Compare current violation counts against baseline. Returns 1 on regression, 0 otherwise."""
    baseline = _load_baseline_count(baseline_path, "violation_count")
    draft_gate_baseline = _load_baseline_count(baseline_path, "draft_gate_violation_count")
    dup_gate_baseline = _load_baseline_count(baseline_path, "duplicate_gate_violation_count")
    regressed = False

    if len(violations) > baseline:
        print(
            f"\n❌ Regression: {len(violations)} > baseline {baseline}. New AO plan(s)"
            " shipped without a gated finalize plan — author one before merging"
            " (task_template.md §4)."
        )
        regressed = True
    elif len(violations) < baseline:
        print(f"\n⚠️  Improvement: {len(violations)} < baseline {baseline}. Re-baseline to codify.")

    if len(draft_gate_violations) > draft_gate_baseline:
        print(
            f"\n❌ Regression: {len(draft_gate_violations)} > baseline {draft_gate_baseline}."
            " A finalize plan shipped (or reverted to) status: draft — flip to active,"
            " gate_on_depends already holds it."
        )
        regressed = True
    elif len(draft_gate_violations) < draft_gate_baseline:
        print(
            f"\n⚠️  Improvement: {len(draft_gate_violations)} < baseline {draft_gate_baseline}. Re-baseline to codify."
        )

    if len(duplicate_gates) > dup_gate_baseline:
        print(
            f"\n❌ Regression: {len(duplicate_gates)} > baseline {dup_gate_baseline}."
            " A new finalize plan was authored against a parent that already has an"
            " active gated finalize plan — this is the exact duplicate-gate race the"
            " create-time --guard-finalize check exists to prevent. De-race: port unique"
            " todos into the survivor, supersede the loser"
            " (plan-completion-and-archival-discipline.md §1)."
        )
        regressed = True
    elif len(duplicate_gates) < dup_gate_baseline:
        print(f"\n⚠️  Improvement: {len(duplicate_gates)} < baseline {dup_gate_baseline}. Re-baseline to codify.")

    if regressed:
        return 1
    print(
        f"\n✅ At baseline ({baseline} coverage / {draft_gate_baseline} draft-gate /"
        f" {dup_gate_baseline} duplicate-gate)."
    )
    return 0


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

    guard_finalize: str | None = cast("str | None", ns.guard_finalize)
    if guard_finalize is not None:
        collisions = finalize_plan_collisions(guard_finalize, active_dir)
        if collisions:
            print(f"❌ '{guard_finalize}' is already gated by {len(collisions)} existing finalize plan(s):")
            for c in collisions:
                print(f"  - {c}")
            print(
                "Refusing to author ANOTHER <parent>_finalize*.md — two gated plans would race"
                " the identical archival ritual against one target. Reuse/extend an existing"
                " gating plan, or supersede the loser first (plan-completion-and-archival"
                "-discipline.md §1)."
            )
            return 1
        print(f"✅ '{guard_finalize}' is not yet gated — safe to author a new finalize plan.")
        return 0

    violations = _find_violations(active_dir)
    draft_gate_violations = _find_draft_gate_violations(active_dir)
    duplicate_gates = _find_duplicate_gate_violations(active_dir)

    if only is not None:
        return _handle_only_mode(only, violations, draft_gate_violations, duplicate_gates)

    print(
        f"Scanned plans/active/ for assigned_vm: planning plans lacking a gated finalize plan — "
        f"{len(violations)} violation(s)."
    )
    print(
        f"Scanned plans/active/ for finalize plans redundantly stuck at status: draft — "
        f"{len(draft_gate_violations)} violation(s)."
    )
    print(
        f"Scanned plans/active/ for parents with duplicate finalize-plan gates (>1 active gate_on_depends: true"
        f" plan) — {len(duplicate_gates)} violation(s)."
    )

    if baseline_write:
        _write_baseline(baseline_path, violations, draft_gate_violations, duplicate_gates, workspace_root)
        print(
            f"✅ Wrote baseline ({len(violations)} coverage / {len(draft_gate_violations)} draft-gate /"
            f" {len(duplicate_gates)} duplicate-gate violations) to {baseline_path}"
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

    if duplicate_gates:
        print(
            "\nParents with duplicate finalize-plan gates (>1 active gate_on_depends: true plan —"
            " de-race: port unique todos into survivor, supersede loser, see"
            " plan-completion-and-archival-discipline.md §1):"
        )
        for parent, finalizers in sorted(duplicate_gates.items()):
            print(f"  Parent: {parent}")
            for f in sorted(finalizers):
                try:
                    rel = f.relative_to(workspace_root)
                except ValueError:
                    rel = f
                print(f"    - {rel}")

    if strict:
        if violations or draft_gate_violations or duplicate_gates:
            print(
                f"\n❌ STRICT: {len(violations)} coverage + {len(draft_gate_violations)} draft-gate +"
                f" {len(duplicate_gates)} duplicate-gate violation(s)."
            )
            return 1
        return 0

    return _check_baseline_regression(violations, draft_gate_violations, duplicate_gates, baseline_path)


if __name__ == "__main__":
    sys.exit(main())
