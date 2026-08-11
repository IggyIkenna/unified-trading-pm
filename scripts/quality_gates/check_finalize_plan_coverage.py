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


def _find_duplicate_gates(active_dir: Path) -> dict[str, list[Path]]:
    """Find parent slugs with MORE THAN ONE finalize-companion plan gating on them.

    Returns a dict mapping parent_slug -> list of gating plans whose stem starts with
    ``<parent_slug>_finalize``, filtered to parents with >1 such companion.  A parent
    with a single ``<parent>_finalize*`` companion is the normal, healthy case — it
    does NOT appear in the result.

    Refined from a literal "any parent named in >1 depends_on" scan after a corpus
    audit (2026-08-11) found 5 parents gated by multiple NON-finalize plans —
    downstream phase/dependent plans legitimately listing a shared prerequisite (e.g.
    the sports-taxonomy P2/P3/fixture plans all gating on P1, the prediction phase
    C/D/E plans all gating on AB-residuals).  Those are fan-out prerequisites, NOT
    duplicate finalize companions; flagging them would make this check review-blocking
    on a healthy corpus with no legitimate fix, and would block a legitimate precommit
    that stages a new dependent plan.  The duplicate-finalize class this exists to
    catch is the 2026-07-31 incident pair: two files whose stems both start with
    ``<parent>_finalize`` (`..._finalize.md` + `..._finalize_2026_07_31.md`, differing
    only by a redundant date suffix) — both match the prefix filter below, while a
    mere downstream dependent does not.
    """
    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    parent_to_finalizers: dict[str, list[Path]] = {}
    for cov in all_plans:
        if not _is_finalize_plan(cov.frontmatter):
            continue
        depends_on = cov.frontmatter.get("depends_on")
        if not isinstance(depends_on, list):
            continue
        for dep in cast(list[object], depends_on):
            if not isinstance(dep, str):
                continue
            slug = dep.strip()
            # Only count this plan as a finalize COMPANION for *slug* if its own stem
            # names slug as its finalize target (`<slug>_finalize*`).  A downstream
            # dependent that merely lists *slug* as a prerequisite is not a companion.
            if not cov.path.stem.startswith(slug + "_finalize"):
                continue
            parent_to_finalizers.setdefault(slug, []).append(cov.path)
    return {slug: paths for slug, paths in parent_to_finalizers.items() if len(paths) > 1}


def parent_already_gated(parent_slug: str, active_dir: Path) -> bool:
    """Check whether *parent_slug* is already gated by an existing finalize plan.

    Re-derives ``_gated_slugs()`` over the CURRENT corpus — the caller does not need
    to pre-load or cache anything.  Keyed on the ``depends_on`` relationship (not
    filename shape), so it catches a near-duplicate filename that a naive stem-
    based guard would miss.

    Returns True if a finalize plan already exists for *parent_slug*, False otherwise.
    Intended as a pre-create idempotency guard: call this BEFORE writing a new
    ``<parent>_finalize*.md`` and refuse if it returns True.
    """
    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    gated = _gated_slugs(all_plans)
    return parent_slug.strip() in gated


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
    duplicate_gates: dict[str, list[Path]],
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

    # Flatten duplicate-gate finalizer paths for the baseline file
    dup_flat: list[str] = []
    for _slug, fps in duplicate_gates.items():
        dup_flat.extend(_rels(fps))

    payload: dict[str, object] = {
        "violation_count": len(violations),
        "draft_gate_violation_count": len(draft_gate_violations),
        "duplicate_gate_parent_count": len(duplicate_gates),
        "rule": "finalize-plan-coverage",
        "source": (
            "task_template.md §4 'Every AO-dispatched plan needs a gated finalize plan' (operator ruling 2026-07-24)"
        ),
        "baseline_files": _rels(violations),
        "draft_gate_baseline_files": _rels(draft_gate_violations),
        "duplicate_gate_baseline_files": dup_flat,
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
    parser.add_argument("--quiet", action="store_true", help="Suppress output; rely on exit code only.")
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
        "--check-already-gated",
        type=str,
        default=None,
        metavar="PARENT_SLUG",
        help=(
            "Pre-create idempotency guard: exit 0 if PARENT_SLUG does NOT already have a gated finalize "
            "plan (safe to create one), exit 1 if it DOES (refuse — a finalize plan already exists). "
            "Keyed on the depends_on relationship, not filename shape.  Intended to be called BEFORE "
            "writing a new <parent>_finalize*.md."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)
    quiet: bool = cast(bool, getattr(ns, "quiet", False))
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

    # --check-already-gated: pre-create idempotency guard (todo 1).  Exit 0 = safe to create;
    # exit 1 = parent already gated — refuse.  Runs BEFORE the full sweep so a simple
    # pre-create check doesn't pay for the full corpus scan.
    check_already_gated: str | None = getattr(ns, "check_already_gated", None)
    if check_already_gated is not None:
        if parent_already_gated(check_already_gated, active_dir):
            print(f"❌ Parent slug '{check_already_gated}' is already gated by an existing finalize plan.")
            return 1
        print(f"✅ Parent slug '{check_already_gated}' is NOT gated — safe to create a finalize plan.")
        return 0

    violations = _find_violations(active_dir)
    draft_gate_violations = _find_draft_gate_violations(active_dir)
    duplicate_gates = _find_duplicate_gates(active_dir)

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
        # For duplicate gates: a parent is flagged only if at least ONE of its finalize-plan
        # paths is in the staged set — a pre-existing duplicate among unstaged files never
        # blocks an unrelated commit.
        staged_duplicate_gates: dict[str, list[Path]] = {}
        for parent_slug, finalizer_paths in duplicate_gates.items():
            staged = [fp for fp in finalizer_paths if fp.resolve() in only_resolved]
            if staged:
                staged_duplicate_gates[parent_slug] = staged
        if not violations and not draft_gate_violations and not staged_duplicate_gates:
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
        if staged_duplicate_gates:
            print(
                "❌ Duplicate-gate violation(s) — parent slug(s) gated by MORE THAN ONE finalize plan"
                " (de-race: port unique todos to the survivor, set superseded_by/supersedes, archive the"
                " loser — see /plans/active/issues/"
                "duplicate_finalize_plans_created_for_one_parent_2026_08_06.md):"
            )
            for parent_slug, fp_list in staged_duplicate_gates.items():
                print(f"  - '{parent_slug}' gated by {len(fp_list)} finalize plans:")
                for fp in fp_list:
                    print(f"      {fp}")
        return 1

    if not quiet:
        print(
            f"Scanned plans/active/ for assigned_vm: planning plans lacking a gated finalize plan — "
            f"{len(violations)} violation(s)."
        )
        print(
            f"Scanned plans/active/ for finalize plans redundantly stuck at status: draft — "
            f"{len(draft_gate_violations)} violation(s)."
        )
        print(
            f"Scanned plans/active/ for duplicate-gate violations (parent slug with >1 finalize plan) — "
            f"{len(duplicate_gates)} parent(s)."
        )

    if baseline_write:
        _write_baseline(baseline_path, violations, draft_gate_violations, duplicate_gates, workspace_root)
        if not quiet:
            print(
                f"✅ Wrote baseline ({len(violations)} coverage / {len(draft_gate_violations)} draft-gate / "
                f"{len(duplicate_gates)} duplicate-gate violations) to {baseline_path}"
            )
        return 0

    if violations and not quiet:
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

    if draft_gate_violations and not quiet:
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

    if duplicate_gates and not quiet:
        print(
            "\nDuplicate-gate violation(s) — parent slug(s) gated by MORE THAN ONE finalize plan"
            " (de-race: port unique todos to the survivor, set superseded_by/supersedes, archive the"
            " loser — see /plans/active/issues/"
            "duplicate_finalize_plans_created_for_one_parent_2026_08_06.md):"
        )
        for parent_slug, fp_list in sorted(duplicate_gates.items()):
            print(f"  - '{parent_slug}' gated by {len(fp_list)} finalize plans:")
            for fp in fp_list:
                try:
                    rel = fp.relative_to(workspace_root)
                except ValueError:
                    rel = fp
                print(f"      {rel}")

    if strict:
        if violations or draft_gate_violations or duplicate_gates:
            if not quiet:
                print(
                    f"\n❌ STRICT: {len(violations)} coverage + {len(draft_gate_violations)} draft-gate + "
                    f"{len(duplicate_gates)} duplicate-gate violation(s)."
                )
            return 1
        return 0

    baseline = _load_baseline_count(baseline_path, "violation_count")
    draft_gate_baseline = _load_baseline_count(baseline_path, "draft_gate_violation_count")
    dup_gate_baseline = _load_baseline_count(baseline_path, "duplicate_gate_parent_count")
    regressed = False
    if len(violations) > baseline:
        if not quiet:
            print(
                f"\n❌ Regression: {len(violations)} > baseline {baseline}. New AO plan(s) shipped without a gated"
                " finalize plan — author one before merging (task_template.md §4)."
            )
        regressed = True
    elif len(violations) < baseline:
        if not quiet:
            print(f"\n⚠️  Improvement: {len(violations)} < baseline {baseline}. Re-baseline to codify.")

    if len(draft_gate_violations) > draft_gate_baseline:
        if not quiet:
            print(
                f"\n❌ Regression: {len(draft_gate_violations)} > baseline {draft_gate_baseline}. A finalize plan shipped"
                " (or reverted to) status: draft — flip to active, gate_on_depends already holds it."
            )
        regressed = True
    elif len(draft_gate_violations) < draft_gate_baseline:
        if not quiet:
            print(
                f"\n⚠️  Improvement: {len(draft_gate_violations)} < baseline {draft_gate_baseline}. Re-baseline to codify."
            )

    if len(duplicate_gates) > dup_gate_baseline:
        if not quiet:
            print(
                f"\n❌ Regression: {len(duplicate_gates)} > baseline {dup_gate_baseline}. A new duplicate-gate pair"
                " shipped — de-race before merging (see duplicate_finalize_plans_created_for_one_parent_2026_08_06.md)."
            )
        regressed = True
    elif len(duplicate_gates) < dup_gate_baseline:
        if not quiet:
            print(
                f"\n⚠️  Improvement: {len(duplicate_gates)} < baseline {dup_gate_baseline}. Re-baseline to codify."
            )

    if regressed:
        return 1
    if not quiet:
        print(
            f"\n✅ At baseline ({baseline} coverage / {draft_gate_baseline} draft-gate / "
            f"{dup_gate_baseline} duplicate-gate)."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
