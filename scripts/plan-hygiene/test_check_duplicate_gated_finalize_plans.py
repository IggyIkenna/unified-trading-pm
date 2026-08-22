# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_duplicate_gated_finalize_plans.py (todo 2,
duplicate_finalize_plans_created_for_one_parent_2026_08_06.md).

Every test passes an explicit --baseline-path pointing at a non-existent file
under tmp_path so it never reads this repo's own real
duplicate_gated_finalize_plans_baseline.yaml (which carries a non-zero count as
of 2026-08-15 -- see that module's docstring) -- an isolated baseline=0 keeps
these assertions deterministic regardless of what the live corpus's baseline
currently says.
"""

from __future__ import annotations

from pathlib import Path

from check_duplicate_gated_finalize_plans import main


def _write_plan(path: Path, *, assigned_vm: str = "planning", todos: int = 3, extra_frontmatter: str = "") -> Path:
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


def _run(tmp_path: Path) -> int:
    return main(
        [
            "--workspace-root",
            str(tmp_path),
            "--baseline-path",
            str(tmp_path / "no_such_baseline.yaml"),
            "--quiet",
        ]
    )


def test_clean_corpus_passes(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    _write_plan(active / "source_plan_2026_08_15.md")
    _write_plan(
        active / "source_plan_2026_08_15_finalize.md",
        extra_frontmatter="depends_on: [source_plan_2026_08_15]\ngate_on_depends: true",
    )

    assert _run(tmp_path) == 0


def test_empty_corpus_passes(tmp_path: Path) -> None:
    _active_dir(tmp_path)

    assert _run(tmp_path) == 0


def test_fails_on_the_2026_07_31_collision_shape(tmp_path: Path) -> None:
    """Reconstructs the actual live incident this whole issue doc tracks: two
    finalize plans, filenames differing only by a redundant date suffix, both
    depends_on the same parent -- caught here even though NEITHER side of the
    pair is newly staged (this is the at-rest sweep, not the --only precommit
    guard, which only fires when one side is in the staged set)."""
    active = _active_dir(tmp_path)
    _write_plan(active / "live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md")
    _write_plan(
        active / "live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md",
        extra_frontmatter=(
            "depends_on: [live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31]\ngate_on_depends: true"
        ),
    )
    _write_plan(
        active / "live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize_2026_07_31.md",
        extra_frontmatter=(
            "depends_on: [live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31]\ngate_on_depends: true"
        ),
    )

    assert _run(tmp_path) == 1


def test_single_gated_parent_is_not_a_duplicate(tmp_path: Path) -> None:
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_15.md")
    _write_plan(
        active / "parent_2026_08_15_finalize.md",
        extra_frontmatter="depends_on: [parent_2026_08_15]\ngate_on_depends: true",
    )
    _write_plan(active / "unrelated_2026_08_15.md", assigned_vm="NA")

    assert _run(tmp_path) == 0


def test_sanctioned_split_children_are_not_flagged_as_duplicate_finalize_plans(tmp_path: Path) -> None:
    """A parent gated by ONE genuine finalize plan plus TWO sanctioned SPLIT children
    (CLAUDE.md: "partial parallelism isn't expressible in one plan -> SPLIT (gated step
    in Plan B via depends_on + gate_on_depends: true)") must NOT read as 3 duplicate
    finalize plans -- the SPLIT children's filenames don't follow the `<parent>_finalize`
    convention, so they aren't competing for the parent's archival slot at all. This is
    the exact false-positive class todo 3's corpus sweep found in all 6 pre-fix baseline
    hits (duplicate_finalize_plans_created_for_one_parent_2026_08_06.md, 2026-08-16
    Progress Log)."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_15.md")
    _write_plan(
        active / "parent_2026_08_15_finalize.md",
        extra_frontmatter="depends_on: [parent_2026_08_15]\ngate_on_depends: true",
    )
    _write_plan(
        active / "parent_phase_c_2026_08_15.md",
        extra_frontmatter="depends_on: [parent_2026_08_15]\ngate_on_depends: true",
    )
    _write_plan(
        active / "parent_phase_d_2026_08_15.md",
        extra_frontmatter="depends_on: [parent_2026_08_15]\ngate_on_depends: true",
    )

    assert _run(tmp_path) == 0


def test_strict_mode_fails_on_any_duplicate_regardless_of_baseline(tmp_path: Path) -> None:
    """--strict ignores the baseline entirely -- used by anything that wants a
    zero-tolerance answer (e.g. todo 3's one-time sweep) rather than the ratchet
    the standing hygiene-sweep wiring uses."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_15.md")
    _write_plan(
        active / "parent_2026_08_15_finalize_a.md",
        extra_frontmatter="depends_on: [parent_2026_08_15]\ngate_on_depends: true",
    )
    _write_plan(
        active / "parent_2026_08_15_finalize_b.md",
        extra_frontmatter="depends_on: [parent_2026_08_15]\ngate_on_depends: true",
    )

    rc = main(["--workspace-root", str(tmp_path), "--strict", "--quiet"])
    assert rc == 1


def test_baseline_write_then_rerun_is_clean(tmp_path: Path) -> None:
    """A corpus at N duplicates, baselined at N, reads as clean on the next run --
    the shrinking-ratchet mechanics every other checker in this directory uses."""
    active = _active_dir(tmp_path)
    _write_plan(active / "parent_2026_08_15.md")
    _write_plan(
        active / "parent_2026_08_15_finalize_a.md",
        extra_frontmatter="depends_on: [parent_2026_08_15]\ngate_on_depends: true",
    )
    _write_plan(
        active / "parent_2026_08_15_finalize_b.md",
        extra_frontmatter="depends_on: [parent_2026_08_15]\ngate_on_depends: true",
    )
    baseline_path = tmp_path / "baseline.yaml"

    rc_write = main(
        ["--workspace-root", str(tmp_path), "--baseline-path", str(baseline_path), "--baseline-write", "--quiet"]
    )
    assert rc_write == 0

    rc_rerun = main(["--workspace-root", str(tmp_path), "--baseline-path", str(baseline_path), "--quiet"])
    assert rc_rerun == 0
