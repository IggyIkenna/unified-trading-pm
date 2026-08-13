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

Third check (added 2026-08-13, same script — duplicate-finalize-plan race): two or more
LIVE finalize/archival plans (non-terminal status) gating the SAME parent would both become
dispatchable on one tick and race the identical archival ritual (a file move plus a
corpus-wide referrer fixup against one target). The 2026-07-31 collision — two
`<parent>_finalize*.md` plans differing only by a redundant date suffix, each authored by a
responder whose own "no companion gated finalize plan exists" justification was already
false when written — is the proof this can happen. `_gated_slugs()` dedupes by construction
(it returns a set), so it cannot surface the duplicate; this check groups live finalize
plans by each `depends_on` slug and flags parents gated by more than one. Keyed on the
`depends_on` relationship (the real contract), not filename shape. **Scoped to
finalize/archival plans (`finalize` in the slug), NOT every `depends_on + gate_on_depends:
true` plan** — phase-sequenced plans reuse that same signature for legitimate DAG edges
(`sports_taxonomy_p2/p3/p4` all gate on P1, `prediction_phase_c/d/e` all gate on AB), and
they do DIFFERENT work, so they don't race a sibling's archival; a parent gated by several
phase plans is normal sequencing, not a duplicate. The `--only` precommit path applies this
as a creation-time idempotency guard: it flags only a STAGED finalize plan whose parent is
already gated by another live finalize plan AND which did not already gate that parent at
HEAD — so a de-race edit (porting a todo into the survivor, or superseding the loser) is not
blocked by the very check that caught the duplicate.

Exit-code semantics: 0 = at/below baseline (all checks); 1 = regression (any check);
2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import re
import subprocess
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

# Plan statuses that are TERMINAL (mirrors check_terminal_status_archived.py's PLAN_TERMINAL).
# A superseded/cancelled/complete finalize plan can no longer dispatch, so it can't race a
# sibling's archival — and excluding it keeps the de-race commit itself (flipping the loser to
# `status: superseded`) from being blocked by this very duplicate check.
_PLAN_TERMINAL_STATUSES = frozenset({"complete", "superseded", "cancelled"})


@dataclass(frozen=True)
class Coverage:
    path: Path
    frontmatter: dict[str, object]


@dataclass(frozen=True)
class DuplicateGate:
    parent: str
    gating: tuple[Path, ...]


def _parse_frontmatter(text: str) -> dict[str, object] | None:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        loaded = cast(object, yaml.safe_load(m.group(1)))
    except yaml.YAMLError:
        return None
    if not isinstance(loaded, dict):
        return None
    return cast(dict[str, object], loaded)


def _load_plan(p: Path) -> Coverage | None:
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    fm = _parse_frontmatter(text)
    if fm is None:
        return None
    return Coverage(path=p, frontmatter=fm)


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


def _is_live_finalize_plan(fm: dict[str, object]) -> bool:
    """A finalize plan that can still dispatch (non-terminal status)."""
    return _is_finalize_plan(fm) and fm.get("status") not in _PLAN_TERMINAL_STATUSES


def _is_archival_finalize(cov: Coverage) -> bool:
    """A live finalize/ARCHIVAL plan — the class that races the identical archival ritual.

    `depends_on + gate_on_depends: true` is ALSO the signature of phase-sequenced plans
    (`sports_taxonomy_p4_backfill` gates on `sports_taxonomy_p2_migration`; `prediction_phase_e`
    gates on `prediction_phase_ab_residuals`). Those do DIFFERENT work and don't archive their
    parent, so they can't collide with a sibling archival. Only a plan whose slug carries the
    `finalize` convention actually reconciles-and-archives its `depends_on` parent.
    """
    return _is_live_finalize_plan(cov.frontmatter) and "finalize" in _slug(cov.path)


def _depends_on_slugs(fm: dict[str, object]) -> set[str]:
    depends_on = fm.get("depends_on")
    if not isinstance(depends_on, list):
        return set()
    return {d.strip() for d in cast(list[object], depends_on) if isinstance(d, str) and d.strip()}


def _gated_slugs(all_plans: list[Coverage]) -> set[str]:
    """Every plan-slug named in some OTHER plan's depends_on + gate_on_depends: true."""
    out: set[str] = set()
    for cov in all_plans:
        if not _is_finalize_plan(cov.frontmatter):
            continue
        out |= _depends_on_slugs(cov.frontmatter)
    return out


def _find_duplicate_gates(all_plans: list[Coverage]) -> list[DuplicateGate]:
    """Parents gated by MORE THAN ONE live (non-terminal) finalize plan.

    `_gated_slugs` dedupes by construction (it returns a set), so it can't surface the
    2026-07-31 collision — two `<parent>_finalize*.md` plans differing only by a redundant
    date suffix, both `depends_on` + `gate_on_depends: true`. This groups live ARCHIVAL
    finalize plans (see `_is_archival_finalize`) by each `depends_on` slug and reports
    parents with >1 distinct gating plan.
    """
    by_parent: dict[str, list[Path]] = {}
    for cov in all_plans:
        if not _is_archival_finalize(cov):
            continue
        for dep in _depends_on_slugs(cov.frontmatter):
            by_parent.setdefault(dep, []).append(cov.path)
    out: list[DuplicateGate] = []
    for parent in sorted(by_parent):
        gating = sorted(set(by_parent[parent]))
        if len(gating) > 1:
            out.append(DuplicateGate(parent=parent, gating=tuple(gating)))
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


def _head_text(pm_root: Path, path: Path) -> str | None:
    """`git show HEAD:<relpath>` content, or None if not committed yet (a brand-new
    staged file) or the path lies outside the PM root."""
    try:
        rel = path.resolve().relative_to(pm_root).as_posix()
    except ValueError:
        return None
    proc = subprocess.run(
        ["git", "-C", str(pm_root), "show", f"HEAD:{rel}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def _duplicate_gates_in_scope(
    duplicate_gates: list[DuplicateGate],
    only_resolved: set[Path],
    pm_root: Path,
) -> list[DuplicateGate]:
    """Duplicate gates THIS commit introduces — creation-time idempotency guard.

    A duplicate gate is in scope iff at least one of its gating paths is staged AND that
    staged path did NOT already gate its parent at HEAD. This refuses the creation of a
    SECOND finalize plan for an already-gated parent without blocking a de-race edit
    (porting a todo into the survivor, or superseding the loser — both touch an existing
    plan that already gated the parent, so neither is "new").
    """
    in_scope: list[DuplicateGate] = []
    for dg in duplicate_gates:
        newly: list[Path] = []
        for p in dg.gating:
            if p.resolve() not in only_resolved:
                continue
            head = _head_text(pm_root, p)
            fm = _parse_frontmatter(head) if head is not None else None
            head_cov = Coverage(path=p, frontmatter=fm) if fm is not None else None
            if head_cov is None or not _is_archival_finalize(head_cov) or dg.parent not in _depends_on_slugs(fm):
                newly.append(p)
        if newly:
            in_scope.append(dg)
    return in_scope


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
    duplicate_gates: list[DuplicateGate],
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
        "duplicate_gate_count": len(duplicate_gates),
        "duplicate_gate_parents": [dg.parent for dg in duplicate_gates],
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
        "--duplicate-gates",
        action="store_true",
        help=(
            "Run ONLY the duplicate-gate detector (corpus-wide) and exit 0/1 on the "
            "duplicate_gate_count baseline ratchet — the shape the hygiene sweep's hard-check "
            "runner expects (reports a duplicate-gated-parent count, 0 = clean)."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the human-readable report; exit code only (used by the sweep runner).",
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


def _run_duplicate_gates_only(duplicate_gates: list[DuplicateGate], baseline_path: Path, quiet: bool) -> int:
    """The hygiene sweep's hard-check shape: exit 0/1 on the duplicate_gate_count ratchet."""
    baseline = _load_baseline_count(baseline_path, "duplicate_gate_count")
    if not quiet:
        print(
            f"Scanned plans/active/ for parents gated by >1 live finalize plan — "
            f"{len(duplicate_gates)} duplicate-gated parent(s)."
        )
        for dg in duplicate_gates:
            print(f"  - parent '{dg.parent}' gated by: " + ", ".join(str(p) for p in dg.gating))
    if len(duplicate_gates) > baseline:
        if not quiet:
            print(
                f"\n❌ Regression: {len(duplicate_gates)} > baseline {baseline} duplicate-gated parent(s)."
                " De-race: port any todo unique to the loser into the survivor, then set"
                " superseded_by/supersedes + a dated banner (see"
                " plans/active/issues/duplicate_finalize_plans_created_for_one_parent_2026_08_06.md)."
            )
        return 1
    if not quiet:
        print(f"\n✅ At baseline ({baseline} duplicate-gated parent(s)).")
    return 0


def _run_only(
    violations: list[Path],
    draft_gate_violations: list[Path],
    duplicate_gates: list[DuplicateGate],
    only: list[str],
    pm_root: Path,
) -> int:
    # --only: resolve each given path the same way (relative-to-cwd or absolute both work,
    # since argparse hands us whatever the caller typed) and keep just the violations that
    # ARE one of them — the corpus scan above still ran in full (gating is inherently
    # corpus-wide), only the reported/failed set narrows. A plan outside --only that's
    # ALSO in violation is silently not-our-problem here, same as check_frontmatter_schema.py's
    # staged-files scoping (foreign_dirty_frontmatter_blocks_every_agents_gate_2026_07_18).
    only_resolved = {Path(o).resolve() for o in only}
    violations = [v for v in violations if v.resolve() in only_resolved]
    draft_gate_violations = [v for v in draft_gate_violations if v.resolve() in only_resolved]
    dup_in_scope = _duplicate_gates_in_scope(duplicate_gates, only_resolved, pm_root)
    if not violations and not draft_gate_violations and not dup_in_scope:
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
    if dup_in_scope:
        print(
            "❌ Duplicate finalize gate(s) introduced by this commit (a parent already gated by a live"
            " finalize plan — see task_template.md §4):"
        )
        for dg in dup_in_scope:
            print(f"  - parent '{dg.parent}' gated by: " + ", ".join(str(p) for p in dg.gating))
    return 1


def _run_corpus(
    violations: list[Path],
    draft_gate_violations: list[Path],
    duplicate_gates: list[DuplicateGate],
    baseline_path: Path,
    workspace_root: Path,
    baseline_write: bool,
    strict: bool,
) -> int:
    print(
        f"Scanned plans/active/ for assigned_vm: planning plans lacking a gated finalize plan — "
        f"{len(violations)} violation(s)."
    )
    print(
        f"Scanned plans/active/ for finalize plans redundantly stuck at status: draft — "
        f"{len(draft_gate_violations)} violation(s)."
    )
    print(
        f"Scanned plans/active/ for parents gated by >1 live finalize plan — "
        f"{len(duplicate_gates)} duplicate-gated parent(s)."
    )

    if baseline_write:
        _write_baseline(baseline_path, violations, draft_gate_violations, duplicate_gates, workspace_root)
        print(
            f"✅ Wrote baseline ({len(violations)} coverage / {len(draft_gate_violations)} draft-gate / "
            f"{len(duplicate_gates)} duplicate-gate violations) to {baseline_path}"
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
            "\nParents gated by >1 live finalize plan (de-race: port any todo unique to the loser into the"
            " survivor, then set superseded_by/supersedes + a dated banner — see"
            " plans/active/issues/duplicate_finalize_plans_created_for_one_parent_2026_08_06.md):"
        )
        for dg in duplicate_gates:
            print(f"  - parent '{dg.parent}' gated by: " + ", ".join(str(p) for p in dg.gating))

    if strict:
        if violations or draft_gate_violations or duplicate_gates:
            print(
                f"\n❌ STRICT: {len(violations)} coverage + {len(draft_gate_violations)} draft-gate + "
                f"{len(duplicate_gates)} duplicate-gate violation(s)."
            )
            return 1
        return 0

    baseline = _load_baseline_count(baseline_path, "violation_count")
    draft_gate_baseline = _load_baseline_count(baseline_path, "draft_gate_violation_count")
    duplicate_gate_baseline = _load_baseline_count(baseline_path, "duplicate_gate_count")
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

    if len(duplicate_gates) > duplicate_gate_baseline:
        print(
            f"\n❌ Regression: {len(duplicate_gates)} > baseline {duplicate_gate_baseline} duplicate-gated parent(s)."
            " A second live finalize plan was authored for an already-gated parent — de-race before merging"
            " (see plans/active/issues/duplicate_finalize_plans_created_for_one_parent_2026_08_06.md)."
        )
        regressed = True
    elif len(duplicate_gates) < duplicate_gate_baseline:
        print(f"\n⚠️  Improvement: {len(duplicate_gates)} < baseline {duplicate_gate_baseline}. Re-baseline to codify.")

    if regressed:
        return 1
    print(
        f"\n✅ At baseline ({baseline} coverage / {draft_gate_baseline} draft-gate / "
        f"{duplicate_gate_baseline} duplicate-gate)."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)
    only: list[str] | None = cast("list[str] | None", ns.only)
    duplicate_gates_only: bool = cast(bool, ns.duplicate_gates)
    quiet: bool = cast(bool, ns.quiet)

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
    pm_root = _pm_root_or_legacy(workspace_root)
    active_dir = pm_root / "plans" / "active"
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

    all_plans = [c for p in active_dir.glob("*.md") if (c := _load_plan(p)) is not None]
    violations = _find_violations(all_plans)
    draft_gate_violations = _find_draft_gate_violations(all_plans)
    duplicate_gates = _find_duplicate_gates(all_plans)

    if duplicate_gates_only:
        return _run_duplicate_gates_only(duplicate_gates, baseline_path, quiet)
    if only is not None:
        return _run_only(violations, draft_gate_violations, duplicate_gates, only, pm_root)
    return _run_corpus(
        violations,
        draft_gate_violations,
        duplicate_gates,
        baseline_path,
        workspace_root,
        baseline_write,
        strict,
    )


if __name__ == "__main__":
    sys.exit(main())
