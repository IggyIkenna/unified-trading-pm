# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_finalize_plan_coverage.py.

Covers the --only mode added for the prek plan-hygiene precommit hook
(ao_kpi_done_vs_detail_mismatch_2026_08_05 follow-up): the default (no --only)
path is a corpus-wide, baseline-ratchet check — too slow/foreign-blast-radius-risky
for a fast staged-files-only precommit hook (RULE-11, same reasoning as
check_frontmatter_schema.py's staged-files scoping,
foreign_dirty_frontmatter_blocks_every_agents_gate_2026_07_18). --only still scans
the whole corpus to resolve gating (which plans have finalize companions is
inherently corpus-wide knowledge) but only reports/fails on violations among the
given paths, so a pre-existing violation in an unrelated plan never blocks an
unrelated commit.
"""

from __future__ import annotations

from pathlib import Path

import check_finalize_plan_coverage as _checker  # type: ignore[import-not-found]
from check_finalize_plan_coverage import main  # type: ignore[import-not-found]


# 2026-08-10 (55a43797a4): content-based PM-root resolution (_pm_root.py) ignores the explicit
# --workspace-root, so main() would scan the REAL corpus instead of the fixture. Redirect
# _pm_root_or_legacy to the fixture PM root so these tests exercise the coverage logic against
# their synthetic tmp_path corpus. SSOT:
# plans/active/issues/pm_root_content_resolution_breaks_checker_unit_test_fixtures_2026_08_10.md
def _fixture_pm_root(root: Path) -> Path:
    return root / "unified-trading-pm"


_checker._pm_root_or_legacy = _fixture_pm_root  # type: ignore[attr-defined]


def _write_plan(path: Path, *, assigned_vm: str = "planning", todos: int = 3, extra_frontmatter: str = "") -> Path:
    """extra_frontmatter is raw, unindented YAML lines (e.g. "a: 1\\nb: 2") — kept
    separate from any textwrap.dedent() block, since dedent computes the common
    leading-whitespace prefix across ALL lines including interpolated ones, and an
    unindented interpolated line silently zeroes that prefix for the whole block."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---", "doc_type: plan", f"title: {path.stem}", "status: active", f"assigned_vm: {assigned_vm}"]
    if extra_frontmatter:
        lines.extend(extra_frontmatter.splitlines())
    lines.append("---")
    todo_lines = "\n".join(f"- [ ] [SCRIPT] P2. todo {i}" for i in range(todos))
    _ = path.write_text("\n".join(lines) + f"\n\n## Todos\n\n{todo_lines}\n", encoding="utf-8")
    return path


def _active_dir(tmp_path: Path) -> Path:
    d = tmp_path / "unified-trading-pm" / "plans" / "active"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── --only scoping ────────────────────────────────────────────────────────────


def test_only_fails_on_a_violating_plan_in_scope(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    violating = _write_plan(active / "source_plan_2026_08_05.md")

    rc = main(["--workspace-root", str(tmp_path), "--only", str(violating)])
    assert rc == 1


def test_only_ignores_an_unrelated_violation_outside_scope(tmp_path: Path) -> None:
    """The corpus has a real violation (source_plan), but --only names a DIFFERENT,
    clean plan — this must pass, mirroring RULE-11 blast-radius safety."""
    active = _active_dir(tmp_path)
    _write_plan(active / "source_plan_2026_08_05.md")  # violates, but not in --only
    clean = _write_plan(
        active / "clean_plan_2026_08_05.md",
        extra_frontmatter="depends_on: [source_plan_2026_08_05]\ngate_on_depends: true",
    )

    rc = main(["--workspace-root", str(tmp_path), "--only", str(clean)])
    assert rc == 0


def test_only_passes_when_the_scoped_plan_has_a_finalize_companion(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    source = _write_plan(active / "source_plan_2026_08_05.md")
    _write_plan(
        active / "source_plan_2026_08_05_finalize.md",
        extra_frontmatter="depends_on: [source_plan_2026_08_05]\ngate_on_depends: true",
    )

    rc = main(["--workspace-root", str(tmp_path), "--only", str(source)])
    assert rc == 0


def test_only_passes_for_a_local_na_plan_not_dispatched(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    local = _write_plan(active / "local_plan_2026_08_05.md", assigned_vm="NA")

    rc = main(["--workspace-root", str(tmp_path), "--only", str(local)])
    assert rc == 0


def test_only_with_multiple_paths_reports_every_violation_among_them(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    v1 = _write_plan(active / "a_2026_08_05.md")
    v2 = _write_plan(active / "b_2026_08_05.md")

    rc = main(["--workspace-root", str(tmp_path), "--only", str(v1), str(v2)])
    assert rc == 1


# ── default (no --only) mode stays corpus-wide + baseline-ratchet ────────────


def test_default_mode_ignores_only_and_uses_the_baseline(tmp_path: Path) -> None:
    """Without --only, behavior is unchanged: a fresh corpus with zero violations and
    no baseline file passes (baseline defaults to 0, matching 0 found)."""
    _active_dir(tmp_path)  # empty corpus

    rc = main(["--workspace-root", str(tmp_path)])
    assert rc == 0


def test_default_mode_regresses_on_a_new_uncovered_plan(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    _write_plan(active / "source_plan_2026_08_05.md")

    rc = main(["--workspace-root", str(tmp_path)])
    assert rc == 1


# ── duplicate-gated finalize plans (duplicate_finalize_plans_created_for_one_parent_2026_08_06) ──


def _write_finalize_plan(path: Path, parent_slug: str) -> Path:
    return _write_plan(path, extra_frontmatter=f"depends_on: [{parent_slug}]\ngate_on_depends: true")


def _empty_baseline_path(tmp_path: Path) -> str:
    """A path that does not exist -> _load_baseline_count defaults every key to 0. Without
    this, these tests would silently pick up the REAL shipped finalize_plan_coverage_baseline.yaml
    (DEFAULT_BASELINE_PATH), whose duplicate_violation_count reflects live corpus debt — not 0 —
    and a small fixture corpus would read as at-or-below that debt instead of exercising the
    intended fresh-baseline regression path."""
    return str(tmp_path / "no_such_baseline.yaml")


def test_default_mode_fails_when_a_parent_is_gated_by_two_finalize_plans(tmp_path: Path) -> None:
    """Reproduces the 2026-07-31 collision: two finalize plans, same parent, same day."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_07_31.md")
    _write_finalize_plan(active / "parent_2026_07_31_finalize.md", "parent_2026_07_31")
    _write_finalize_plan(active / "parent_finalize_2026_07_31.md", "parent_2026_07_31")

    rc = main(["--workspace-root", str(tmp_path), "--baseline-path", _empty_baseline_path(tmp_path)])
    assert rc == 1


def test_default_mode_passes_when_each_parent_has_exactly_one_finalize_plan(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_07_31.md")
    _write_finalize_plan(active / "parent_2026_07_31_finalize.md", "parent_2026_07_31")

    rc = main(["--workspace-root", str(tmp_path), "--baseline-path", _empty_baseline_path(tmp_path)])
    assert rc == 0


def test_duplicates_only_isolates_the_check_from_coverage_and_draft_gate_debt(tmp_path: Path) -> None:
    """--duplicates-only must not re-fail on pre-existing coverage/draft-gate baseline
    debt that the OTHER two (separately-ratcheted) checks already own."""
    active = _active_dir(tmp_path)
    _write_plan(active / "uncovered_2026_08_05.md")  # a real coverage violation, ignored here

    rc = main(
        ["--workspace-root", str(tmp_path), "--duplicates-only", "--baseline-path", _empty_baseline_path(tmp_path)]
    )
    assert rc == 0


def test_duplicates_only_fails_on_a_duplicate(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_07_31.md")
    _write_finalize_plan(active / "parent_2026_07_31_finalize.md", "parent_2026_07_31")
    _write_finalize_plan(active / "parent_finalize_2026_07_31.md", "parent_2026_07_31")

    rc = main(
        ["--workspace-root", str(tmp_path), "--duplicates-only", "--baseline-path", _empty_baseline_path(tmp_path)]
    )
    assert rc == 1


def test_duplicates_only_passes_when_count_is_at_or_below_baseline(tmp_path: Path) -> None:
    """The ratchet property itself: a duplicate count AT the baseline is not a regression —
    only exceeding it is (pre-existing debt is tracked, not re-blocked on every commit)."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_07_31.md")
    _write_finalize_plan(active / "parent_2026_07_31_finalize.md", "parent_2026_07_31")
    _write_finalize_plan(active / "parent_finalize_2026_07_31.md", "parent_2026_07_31")
    baseline_path = tmp_path / "baseline.yaml"
    baseline_path.write_text("duplicate_violation_count: 1\n", encoding="utf-8")

    rc = main(["--workspace-root", str(tmp_path), "--duplicates-only", "--baseline-path", str(baseline_path)])
    assert rc == 0


def test_only_catches_a_newly_committed_finalize_plan_that_duplicates_an_existing_gate(tmp_path: Path) -> None:
    """Todo 1's create-time guard: the SECOND finalize plan is the one being committed
    (named in --only); the first already exists on disk from an earlier commit."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_07_31.md")
    _write_finalize_plan(active / "parent_2026_07_31_finalize.md", "parent_2026_07_31")
    new_finalize = _write_finalize_plan(active / "parent_finalize_2026_07_31.md", "parent_2026_07_31")

    rc = main(["--workspace-root", str(tmp_path), "--only", str(new_finalize)])
    assert rc == 1


def test_only_ignores_a_preexisting_duplicate_when_neither_gating_plan_is_in_scope(tmp_path: Path) -> None:
    """RULE-11 blast-radius safety extends to duplicates too: a pre-existing duplicate
    pair sitting at rest must not block an unrelated commit."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_07_31.md")
    _write_finalize_plan(active / "parent_2026_07_31_finalize.md", "parent_2026_07_31")
    _write_finalize_plan(active / "parent_finalize_2026_07_31.md", "parent_2026_07_31")
    unrelated = _write_plan(active / "unrelated_2026_08_05.md", todos=1)  # single-todo carve-out

    rc = main(["--workspace-root", str(tmp_path), "--only", str(unrelated)])
    assert rc == 0
