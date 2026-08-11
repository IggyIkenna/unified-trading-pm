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

Also covers the --assert-not-gated + --only duplicate-gate modes (2026-08-11,
duplicate_finalize_plans_created_for_one_parent todo 1): finalize-plan creation is
idempotent at the point of creation — refuse a new <parent>_finalize*.md when the
parent already has a gated finalize plan, keyed on the depends_on relationship
(_gating_plans), never the filename shape.
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


# ── --assert-not-gated (create-time idempotency guard, duplicate_finalize_plans_created_for_one_parent todo 1) ──


def test_assert_not_gated_refuses_when_parent_already_gated(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    _write_plan(active / "source_plan_2026_08_11.md")
    _write_plan(
        active / "source_plan_2026_08_11_finalize.md",
        extra_frontmatter="depends_on: [source_plan_2026_08_11]\ngate_on_depends: true",
    )

    rc = main(["--workspace-root", str(tmp_path), "--assert-not-gated", "source_plan_2026_08_11"])
    assert rc == 1


def test_assert_not_gated_refuses_on_date_suffixed_duplicate_filename(tmp_path: Path) -> None:
    """The two colliding finalize plans (2026-07-31 incident) differed only by a redundant
    date suffix — the guard must key on the depends_on relationship, not the expected
    filename shape."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_07_31.md")
    _write_plan(
        active / "parent_2026_07_31_finalize_2026_07_31.md",
        extra_frontmatter="depends_on: [parent_2026_07_31]\ngate_on_depends: true",
    )

    rc = main(["--workspace-root", str(tmp_path), "--assert-not-gated", "parent_2026_07_31"])
    assert rc == 1


def test_assert_not_gated_passes_when_parent_not_gated(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    _write_plan(active / "source_plan_2026_08_11.md")

    rc = main(["--workspace-root", str(tmp_path), "--assert-not-gated", "source_plan_2026_08_11"])
    assert rc == 0


# ── --only duplicate-gate refusal (prek precommit create-time guard) ─────────


def test_only_refuses_staged_duplicate_finalize_for_an_already_gated_parent(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    _write_plan(active / "source_plan_2026_08_11.md")
    _write_plan(
        active / "source_plan_2026_08_11_finalize.md",
        extra_frontmatter="depends_on: [source_plan_2026_08_11]\ngate_on_depends: true",
    )
    # A SECOND finalize plan for the same parent (different filename shape) is staged — the exact
    # two-agents race this guard exists to refuse.
    second = _write_plan(
        active / "source_plan_2026_08_11_finalize_2026_08_11.md",
        extra_frontmatter="depends_on: [source_plan_2026_08_11]\ngate_on_depends: true",
    )

    rc = main(["--workspace-root", str(tmp_path), "--only", str(second)])
    assert rc == 1


def test_only_passes_a_single_finalize_for_an_un_gated_parent(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    _write_plan(active / "source_plan_2026_08_11.md")
    finalize = _write_plan(
        active / "source_plan_2026_08_11_finalize.md",
        extra_frontmatter="depends_on: [source_plan_2026_08_11]\ngate_on_depends: true",
    )

    rc = main(["--workspace-root", str(tmp_path), "--only", str(finalize)])
    assert rc == 0


def test_only_ignores_an_unrelated_duplicate_pair_outside_scope(tmp_path: Path) -> None:
    """A pre-existing duplicate gate pair elsewhere in the corpus must NOT block a staged clean
    finalize plan for a different parent (RULE-11 blast-radius safety) — the corpus-wide at-rest
    detector is a separate check."""
    active = _active_dir(tmp_path)
    _write_plan(active / "source_a_2026_08_11.md")
    _write_plan(
        active / "source_a_2026_08_11_finalize.md",
        extra_frontmatter="depends_on: [source_a_2026_08_11]\ngate_on_depends: true",
    )
    _write_plan(
        active / "source_a_2026_08_11_finalize_2026_08_11.md",
        extra_frontmatter="depends_on: [source_a_2026_08_11]\ngate_on_depends: true",
    )
    _write_plan(active / "source_b_2026_08_11.md")
    clean = _write_plan(
        active / "source_b_2026_08_11_finalize.md",
        extra_frontmatter="depends_on: [source_b_2026_08_11]\ngate_on_depends: true",
    )

    rc = main(["--workspace-root", str(tmp_path), "--only", str(clean)])
    assert rc == 0


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
