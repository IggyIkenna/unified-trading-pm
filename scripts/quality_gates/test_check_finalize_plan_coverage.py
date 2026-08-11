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


# ── --check-already-gated pre-create idempotency guard ─────────────────────────


def test_check_already_gated_true_when_finalize_plan_exists(tmp_path: Path) -> None:
    """A parent that already has a <parent>_finalize*.md gating on it returns exit 1."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_plan_2026_08_11.md")
    _write_plan(
        active / "parent_plan_2026_08_11_finalize.md",
        extra_frontmatter="depends_on: [parent_plan_2026_08_11]\ngate_on_depends: true",
    )
    rc = main(["--workspace-root", str(tmp_path), "--check-already-gated", "parent_plan_2026_08_11"])
    assert rc == 1


def test_check_already_gated_false_when_no_finalize_plan(tmp_path: Path) -> None:
    """A parent with no finalize companion returns exit 0 (safe to create one)."""
    active = _active_dir(tmp_path)
    _write_plan(active / "orphan_plan_2026_08_11.md")
    rc = main(["--workspace-root", str(tmp_path), "--check-already-gated", "orphan_plan_2026_08_11"])
    assert rc == 0


# ── _find_duplicate_gates — refined (finalize-shaped companions only) ──────────


def test_duplicate_gate_ignores_legitimate_fan_out(tmp_path: Path) -> None:
    """Multiple downstream plans gating on the same prerequisite (but none of their
    stems match <parent>_finalize*) is NOT a duplicate gate — it's legitimate fan-out.
    All plans use assigned_vm:NA so the coverage check (which only flags planning) is silent."""
    active = _active_dir(tmp_path)
    _write_plan(active / "shared_prereq_2026_08_11.md", assigned_vm="NA")
    _write_plan(
        active / "phase_a_2026_08_11.md",
        assigned_vm="NA",
        extra_frontmatter="depends_on: [shared_prereq_2026_08_11]\ngate_on_depends: true",
    )
    _write_plan(
        active / "phase_b_2026_08_11.md",
        assigned_vm="NA",
        extra_frontmatter="depends_on: [shared_prereq_2026_08_11]\ngate_on_depends: true",
    )
    rc = main(["--workspace-root", str(tmp_path)])
    assert rc == 0


def test_duplicate_gate_detects_two_finalize_companions(tmp_path: Path) -> None:
    """Two plans whose stems BOTH start with <parent>_finalize is the exact pattern
    from the 2026-07-31 incident — MUST be flagged.  assigned_vm:NA so only the
    duplicate-gate check fires, not the coverage check."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_11.md", assigned_vm="NA")
    _write_plan(
        active / "parent_2026_08_11_finalize.md",
        assigned_vm="NA",
        extra_frontmatter="depends_on: [parent_2026_08_11]\ngate_on_depends: true",
    )
    _write_plan(
        active / "parent_2026_08_11_finalize_2026_08_11.md",
        assigned_vm="NA",
        extra_frontmatter="depends_on: [parent_2026_08_11]\ngate_on_depends: true",
    )
    rc = main(["--workspace-root", str(tmp_path)])
    assert rc == 1


def test_duplicate_gate_ignores_one_finalize_plus_one_downstream(tmp_path: Path) -> None:
    """One real finalize companion and one downstream dependent (whose stem does NOT
    start with <parent>_finalize) is the healthy case — not a duplicate."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_11.md", assigned_vm="NA")
    _write_plan(
        active / "parent_2026_08_11_finalize.md",
        assigned_vm="NA",
        extra_frontmatter="depends_on: [parent_2026_08_11]\ngate_on_depends: true",
    )
    _write_plan(
        active / "parent_2026_08_11_phase_c.md",
        assigned_vm="NA",
        extra_frontmatter="depends_on: [parent_2026_08_11]\ngate_on_depends: true",
    )
    rc = main(["--workspace-root", str(tmp_path)])
    assert rc == 0


# ── --quiet flag ──────────────────────────────────────────────────────────────


def test_quiet_flag_exits_zero_on_clean_no_baseline(tmp_path: Path) -> None:
    """--quiet suppresses output and returns 0 on a clean corpus (no baseline file)."""
    _active_dir(tmp_path)  # empty corpus, baseline file absent → all baselines default to 0
    rc = main(["--workspace-root", str(tmp_path), "--quiet"])
    assert rc == 0
