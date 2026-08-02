# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_pytest_unit_dir_coverage.py.

Covers the three PYTEST_UNIT_DIR resolution shapes (literal / self-discovering
/ unset-default), the coverage predicate, and — the "done when" bar from
`plans/active/issues/mtds_ungated_test_families_2026_07_17.md` todo 5 — a
synthetic fixture repo reproducing the exact MTDS bug shape: a new
`tests/<family>/unit/` dir the repo's PYTEST_UNIT_DIR doesn't reach, which
`main()` must flag once it's over baseline.
"""

from __future__ import annotations

from pathlib import Path

from check_pytest_unit_dir_coverage import (  # type: ignore[import-not-found]
    BASE_DEFAULT_ENTRY,
    Baseline,
    find_family_unit_dirs,
    is_pytest_unit_dir_repo,
    load_baseline,
    main,
    resolve_effective_entries,
    ungated_families,
    write_baseline,
)

# ── resolve_effective_entries ───────────────────────────────────────────────


def test_literal_assignment_is_parsed() -> None:
    text = 'PYTEST_UNIT_DIR="tests/unit/ tests/market_interface/unit/ tests/cli/"\n'
    assert resolve_effective_entries(text) == ("tests/unit/", "tests/market_interface/unit/", "tests/cli/")


def test_later_literal_assignment_wins_bash_order() -> None:
    """Matches the real fleet shape: every PYTEST_UNIT_DIR= assignment in the
    corpus is line-anchored (optionally indented inside a conditional block),
    never appended after a `&&` on the same line."""
    text = (
        'PYTEST_UNIT_DIR="tests/unit/"\n'
        'if [ -n "$WIDEN" ]; then\n'
        '    PYTEST_UNIT_DIR="tests/unit/ tests/foo/unit/"\n'
        "fi\n"
    )
    assert resolve_effective_entries(text) == ("tests/unit/", "tests/foo/unit/")


def test_self_discovering_returns_none() -> None:
    text = (
        "_UNIT_DIRS=\"$(find tests -maxdepth 2 -type d -name 'unit' 2>/dev/null | sort | tr '\\n' ' ')\"\n"
        'PYTEST_UNIT_DIR="$_UNIT_DIRS"\n'
    )
    assert resolve_effective_entries(text) is None


def test_no_assignment_falls_back_to_base_default() -> None:
    assert resolve_effective_entries("# nothing here\n") == (BASE_DEFAULT_ENTRY,)


# ── is_pytest_unit_dir_repo ──────────────────────────────────────────────────


def test_repo_sourcing_base_service_is_in_scope() -> None:
    assert is_pytest_unit_dir_repo(
        'source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"\n'
    )


def test_repo_not_sourcing_base_scripts_is_out_of_scope() -> None:
    assert not is_pytest_unit_dir_repo("npm run lint && npm test\n")


# ── find_family_unit_dirs ───────────────────────────────────────────────────


def test_find_family_unit_dirs_ignores_top_level_tests_unit(tmp_path: Path) -> None:
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "market_interface" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "market_interface" / "adapters").mkdir(parents=True)

    assert find_family_unit_dirs(tmp_path) == ["tests/market_interface/unit"]


def test_find_family_unit_dirs_no_tests_dir(tmp_path: Path) -> None:
    assert find_family_unit_dirs(tmp_path) == []


# ── ungated_families / _covers ──────────────────────────────────────────────


def test_ungated_families_flags_family_with_zero_overlap() -> None:
    families = ["tests/trade_execution/unit", "tests/sports_execution/unit"]
    entries = ("tests/unit/", "tests/trade_execution/unit/")
    assert ungated_families(families, entries) == ["tests/sports_execution/unit"]


def test_ungated_families_prefix_entry_covers_whole_family() -> None:
    families = ["tests/risk/unit", "tests/pnl/unit"]
    assert ungated_families(families, ("tests/",)) == []


def test_ungated_families_file_scoped_entry_still_counts_as_covered() -> None:
    """A single-file PYTEST_UNIT_DIR entry inside the family dir is coarse
    partial coverage, not a full-family ungating — out of scope for this
    checker (a distinct debt class from the MTDS zero-collection bug)."""
    families = ["tests/defi_execution/unit"]
    entries = ("tests/defi_execution/unit/test_defi_lateral_loader.py",)
    assert ungated_families(families, entries) == []


def test_ungated_families_self_discovering_none_is_always_empty() -> None:
    assert ungated_families(["tests/anything/unit"], None) == []


# ── Baseline round-trip ──────────────────────────────────────────────────────


def test_baseline_round_trip(tmp_path: Path) -> None:
    baseline_file = tmp_path / "baseline.yaml"
    write_baseline({"demo-repo": 1}, Baseline(), path=baseline_file)

    loaded = load_baseline(baseline_file)

    assert loaded.allowed("demo-repo") == 1
    assert loaded.allowed("unscanned-repo") == 0


def test_baseline_write_never_raises_and_preserves_unscanned_repos(tmp_path: Path) -> None:
    baseline_file = tmp_path / "baseline.yaml"
    existing = Baseline(counts={"repo-a": 5, "repo-b": 2})
    write_baseline({"repo-a": 7}, existing, path=baseline_file)  # observed HIGHER than baseline

    loaded = load_baseline(baseline_file)

    assert loaded.allowed("repo-a") == 5  # clamped DOWN, never raised
    assert loaded.allowed("repo-b") == 2  # unobserved this run — carried forward verbatim


# ── main(): synthetic new-uncollected-dir case (the "done when" proof) ─────


def _write_fleet_repo(
    workspace_root: Path,
    name: str,
    pytest_unit_dir: str,
    family_dirs: list[str],
) -> None:
    repo_root = workspace_root / name
    (repo_root / ".git").mkdir(parents=True)
    (repo_root / "scripts").mkdir(parents=True)
    (repo_root / "scripts" / "quality-gates.sh").write_text(
        f'source "${{WORKSPACE_ROOT}}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"\n'
        f'PYTEST_UNIT_DIR="{pytest_unit_dir}"\n',
        encoding="utf-8",
    )
    for family_dir in family_dirs:
        (repo_root / family_dir).mkdir(parents=True)
        (repo_root / family_dir / "test_placeholder.py").write_text("def test_x(): pass\n", encoding="utf-8")


def test_main_flags_synthetic_new_ungated_family(tmp_path: Path) -> None:
    """Reproduces the exact MTDS bug shape: a repo grows a NEW
    `tests/<family>/unit/` dir that PYTEST_UNIT_DIR doesn't reach. With an
    empty (zero) baseline, main() must exit 1 and name the ungated family."""
    _write_fleet_repo(
        tmp_path,
        "synthetic-repo",
        pytest_unit_dir="tests/unit/",
        family_dirs=["tests/unit", "tests/new_family/unit"],
    )
    baseline_file = tmp_path / "baseline.yaml"
    write_baseline({}, Baseline(), path=baseline_file)  # seed empty (0 tolerated everywhere)

    exit_code = main(
        [
            "--workspace-root",
            str(tmp_path),
            "--scope",
            "synthetic-repo",
            "--baseline-file",
            str(baseline_file),
        ]
    )

    assert exit_code == 1


def test_main_passes_when_family_is_gated(tmp_path: Path) -> None:
    _write_fleet_repo(
        tmp_path,
        "synthetic-repo-gated",
        pytest_unit_dir="tests/unit/ tests/new_family/unit/",
        family_dirs=["tests/unit", "tests/new_family/unit"],
    )
    baseline_file = tmp_path / "baseline.yaml"
    write_baseline({}, Baseline(), path=baseline_file)

    exit_code = main(
        [
            "--workspace-root",
            str(tmp_path),
            "--scope",
            "synthetic-repo-gated",
            "--baseline-file",
            str(baseline_file),
        ]
    )

    assert exit_code == 0


def test_main_tolerates_pre_existing_debt_at_baseline(tmp_path: Path) -> None:
    """Shrinking-ratchet contract: a repo's ALREADY-baselined ungated count
    does not fail the gate (todo 12's explicit "do not fail red on existing
    fleet debt this todo doesn't fix")."""
    _write_fleet_repo(
        tmp_path,
        "synthetic-repo-debt",
        pytest_unit_dir="tests/unit/",
        family_dirs=["tests/unit", "tests/legacy_family/unit"],
    )
    baseline_file = tmp_path / "baseline.yaml"
    write_baseline({"synthetic-repo-debt": 1}, Baseline(), path=baseline_file)

    exit_code = main(
        [
            "--workspace-root",
            str(tmp_path),
            "--scope",
            "synthetic-repo-debt",
            "--baseline-file",
            str(baseline_file),
        ]
    )

    assert exit_code == 0


def test_main_skips_non_pytest_unit_dir_repo(tmp_path: Path) -> None:
    repo_root = tmp_path / "ui-repo"
    (repo_root / ".git").mkdir(parents=True)
    (repo_root / "scripts").mkdir(parents=True)
    (repo_root / "scripts" / "quality-gates.sh").write_text("npm run lint && npm test\n", encoding="utf-8")
    (repo_root / "tests" / "some_family" / "unit").mkdir(parents=True)

    exit_code = main(["--workspace-root", str(tmp_path), "--scope", "ui-repo"])

    assert exit_code == 0
