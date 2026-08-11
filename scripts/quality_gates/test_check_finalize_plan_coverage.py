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

Also covers the duplicate-gate detector (--check-duplicate-gates) and the
idempotent-creation guard in --only mode (todos 1+2 of
duplicate_finalize_plans_created_for_one_parent_2026_08_06.md). A "finalize
companion" of a parent is a plan named `<parent>_finalize*` that declares
`depends_on: [<parent>]` + `gate_on_depends: true` — work plans that merely gate on
a parent as a shared prerequisite are NOT companions and must not be flagged.
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


def _finalize(active: Path, parent_slug: str, suffix: str = "") -> Path:
    """Write a finalize COMPANION for `parent_slug` following the `<parent>_finalize*`
    naming contract, and return its path."""
    name = f"{parent_slug}_finalize{suffix}.md"
    return _write_plan(
        active / name,
        extra_frontmatter=f"depends_on: [{parent_slug}]\ngate_on_depends: true",
    )


def _work_plan_gating(active: Path, name: str, parent_slug: str) -> Path:
    """Write a WORK plan (not a finalize companion — name does not follow
    `<parent>_finalize*`) that gates on `parent_slug` as a shared prerequisite."""
    return _write_plan(
        active / name,
        extra_frontmatter=f"depends_on: [{parent_slug}]\ngate_on_depends: true",
    )


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
    _finalize(active, "source_plan_2026_08_05")

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


# ── --check-duplicate-gates ───────────────────────────────────────────────────


def test_check_duplicate_gates_clean_when_no_duplicates(tmp_path: Path) -> None:
    """A corpus where every parent has at most one finalize companion passes."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_a_2026_08_11.md")
    _finalize(active, "parent_a_2026_08_11")
    _write_plan(active / "parent_b_2026_08_11.md")
    _finalize(active, "parent_b_2026_08_11")

    rc = main(["--workspace-root", str(tmp_path), "--check-duplicate-gates"])
    assert rc == 0


def test_check_duplicate_gates_finds_duplicate(tmp_path: Path) -> None:
    """A parent with TWO finalize companions is flagged (the incident shape —
    `..._finalize.md` vs `..._finalize_<date>.md` differ only by a redundant suffix)."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_11.md")
    _finalize(active, "parent_2026_08_11")
    _finalize(active, "parent_2026_08_11", "_2026_08_11")

    rc = main(["--workspace-root", str(tmp_path), "--check-duplicate-gates"])
    assert rc == 1


def test_check_duplicate_gates_finds_multiple_duplicates(tmp_path: Path) -> None:
    """Multiple parents each with >1 finalize companion are all flagged."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_a_2026_08_11.md")
    _finalize(active, "parent_a_2026_08_11")
    _finalize(active, "parent_a_2026_08_11", "_b")
    _write_plan(active / "parent_b_2026_08_11.md")
    _finalize(active, "parent_b_2026_08_11")
    _finalize(active, "parent_b_2026_08_11", "_c")

    rc = main(["--workspace-root", str(tmp_path), "--check-duplicate-gates"])
    assert rc == 1


def test_check_duplicate_gates_quiet_suppresses_output(tmp_path: Path, capsys) -> None:
    """--quiet mode produces no stdout on a clean corpus."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_11.md")
    _finalize(active, "parent_2026_08_11")

    rc = main(["--workspace-root", str(tmp_path), "--check-duplicate-gates", "--quiet"])
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_check_duplicate_gates_ignores_shared_prereq_dag(tmp_path: Path) -> None:
    """A parent gated by TWO distinct WORK plans (neither named `<parent>_finalize*`)
    is a legitimate shared-prerequisite DAG, NOT a duplicate gate — must pass."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_11.md")
    _work_plan_gating(active, "phase_c_data_status_ui_2026_08_11.md", "parent_2026_08_11")
    _work_plan_gating(active, "phase_e_arb_live_2026_08_11.md", "parent_2026_08_11")

    rc = main(["--workspace-root", str(tmp_path), "--check-duplicate-gates"])
    assert rc == 0


def test_check_duplicate_gates_mixed_one_companion_one_work_plan(tmp_path: Path) -> None:
    """A parent with ONE finalize companion PLUS a distinct work plan gating on it is
    exactly one companion — not a duplicate — must pass."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_11.md")
    _finalize(active, "parent_2026_08_11")
    _work_plan_gating(active, "registry_coverage_2026_08_11.md", "parent_2026_08_11")

    rc = main(["--workspace-root", str(tmp_path), "--check-duplicate-gates"])
    assert rc == 0


# ── Idempotent-creation guard in --only mode ──────────────────────────────────


def test_only_blocks_duplicate_finalize_plan_for_already_gated_parent(tmp_path: Path) -> None:
    """A staged finalize companion whose parent ALREADY has a DIFFERENT finalize
    companion is flagged as a duplicate-gate violation."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_11.md")
    _finalize(active, "parent_2026_08_11", "_existing")  # the surviving companion
    second = _finalize(active, "parent_2026_08_11", "_duplicate")  # staged for commit

    rc = main(["--workspace-root", str(tmp_path), "--only", str(second)])
    assert rc == 1


def test_only_allows_first_finalize_plan_for_parent(tmp_path: Path) -> None:
    """The FIRST finalize companion for a parent passes — no duplicate exists yet."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_11.md")
    first = _finalize(active, "parent_2026_08_11")

    rc = main(["--workspace-root", str(tmp_path), "--only", str(first)])
    assert rc == 0


def test_only_allows_multiple_work_plans_gating_on_different_parents(tmp_path: Path) -> None:
    """Two finalize companions for DIFFERENT parents are both fine."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_a_2026_08_11.md")
    _write_plan(active / "parent_b_2026_08_11.md")
    fa = _finalize(active, "parent_a_2026_08_11")
    fb = _finalize(active, "parent_b_2026_08_11")

    rc = main(["--workspace-root", str(tmp_path), "--only", str(fa), str(fb)])
    assert rc == 0


def test_only_allows_a_work_plan_gating_on_a_parent(tmp_path: Path) -> None:
    """A staged WORK plan (not companion-named) that gates on a parent is fine even
    when the parent has no finalize companion — it is not a duplicate-gate attempt."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_11.md")
    work = _work_plan_gating(active, "phase_c_work_2026_08_11.md", "parent_2026_08_11")

    rc = main(["--workspace-root", str(tmp_path), "--only", str(work)])
    assert rc == 0
