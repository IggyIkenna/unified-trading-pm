# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_pytest_unit_dir_coverage.py.

Covers the three PYTEST_UNIT_DIR resolution shapes (literal / self-discovering
/ unset-default), the coverage predicate, and two "done when" bars:
- the original MTDS bug shape from
  `plans/active/issues/mtds_ungated_test_families_2026_07_17.md` todo 5: a new
  `tests/<family>/unit/` dir the repo's PYTEST_UNIT_DIR doesn't reach.
- the v2 fix's own reason for existing: a co-located `scripts/<name>/test_*.py`
  dir (the exact shape PM's own `scripts/plan-hygiene/` shipped — 24 tests
  across 4 files, fixed in `4a4716151f` — that v1's `tests/<family>/unit/`-only
  scan structurally could not have caught, because it never looked outside
  `tests/`).
`main()` must flag both shapes once they're over baseline.
"""

from __future__ import annotations

from pathlib import Path

from check_pytest_unit_dir_coverage import (  # type: ignore[import-not-found]
    BASE_DEFAULT_ENTRY,
    Baseline,
    find_test_containing_dirs,
    is_pytest_unit_dir_repo,
    load_baseline,
    main,
    resolve_effective_entries,
    ungated_test_dirs,
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


# ── find_test_containing_dirs ───────────────────────────────────────────────


def test_find_test_containing_dirs_finds_family_unit_shape(tmp_path: Path) -> None:
    """The original MTDS shape: tests/<family>/unit/ with a test file inside."""
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_a.py").write_text("def test_a(): pass\n")
    (tmp_path / "tests" / "market_interface" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "market_interface" / "unit" / "test_b.py").write_text("def test_b(): pass\n")
    (tmp_path / "tests" / "market_interface" / "adapters").mkdir(parents=True)  # no test_*.py -> not counted

    assert find_test_containing_dirs(tmp_path) == ["tests/market_interface/unit", "tests/unit"]


def test_find_test_containing_dirs_finds_colocated_scripts_shape(tmp_path: Path) -> None:
    """The v1-blind-spot shape: co-located test_*.py directly under scripts/<name>/, NOT
    nested under tests/ at all — the real unified-trading-pm scripts/plan-hygiene/ bug."""
    (tmp_path / "scripts" / "plan-hygiene").mkdir(parents=True)
    (tmp_path / "scripts" / "plan-hygiene" / "test_check_na_corpus_ratchet.py").write_text("def test_x(): pass\n")

    assert find_test_containing_dirs(tmp_path) == ["scripts/plan-hygiene"]


def test_find_test_containing_dirs_prunes_venv_and_hidden_dirs(tmp_path: Path) -> None:
    """A vendored .venv test suite (pytest's own tests, hypothesis, etc.) or an agent
    worktree checkout under a hidden dir must never inflate the observed count."""
    (tmp_path / ".venv" / "lib" / "site-packages" / "pytest" / "tests").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "site-packages" / "pytest" / "tests" / "test_vendored.py").write_text("x\n")
    (tmp_path / ".claude" / "worktrees" / "agent-1" / "tests").mkdir(parents=True)
    (tmp_path / ".claude" / "worktrees" / "agent-1" / "tests" / "test_worktree.py").write_text("x\n")
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_real.py").write_text("def test_real(): pass\n")

    assert find_test_containing_dirs(tmp_path) == ["tests/unit"]


def test_find_test_containing_dirs_no_test_files(tmp_path: Path) -> None:
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    assert find_test_containing_dirs(tmp_path) == []


def test_find_test_containing_dirs_excludes_non_unit_tiers(tmp_path: Path) -> None:
    """tests/integration/, tests/e2e/, tests/smoke/ etc. are a deliberately separate
    tier with their own collection mechanism (e.g. system-integration-tests' Layer 3a/3b
    @pytest.mark.smoke / @pytest.mark.full_e2e) — not this checker's bug class. Measured
    2026-08-15: an unscoped scan flagged ~60 such dirs across the real fleet as false
    positives before this exclusion was added."""
    for tier in ("integration", "e2e", "smoke", "perf", "regression", "backtest"):
        d = tmp_path / "tests" / tier
        d.mkdir(parents=True)
        (d / "test_x.py").write_text("def test_x(): pass\n")
    (tmp_path / "tests" / "defi" / "swap").mkdir(parents=True)  # feature name, not a tier
    (tmp_path / "tests" / "defi" / "test_swap.py").write_text("def test_swap(): pass\n")

    assert find_test_containing_dirs(tmp_path) == ["tests/defi"]


def test_find_test_containing_dirs_excludes_codex_docs_root(tmp_path: Path) -> None:
    """codex/06-coding-standards/test-templates/test_event_logging.py is a CANONICAL
    TEMPLATE meant to be copied into a service's tests/unit/, never collected in place —
    confirmed via its own leading comment on the real file."""
    template_dir = tmp_path / "codex" / "06-coding-standards" / "test-templates"
    template_dir.mkdir(parents=True)
    (template_dir / "test_event_logging.py").write_text("# CANONICAL TEMPLATE\n")

    assert find_test_containing_dirs(tmp_path) == []


# ── ungated_test_dirs / _covers ─────────────────────────────────────────────


def test_ungated_test_dirs_flags_dir_with_zero_overlap() -> None:
    test_dirs = ["tests/trade_execution/unit", "tests/sports_execution/unit"]
    entries = ("tests/unit/", "tests/trade_execution/unit/")
    assert ungated_test_dirs(test_dirs, entries) == ["tests/sports_execution/unit"]


def test_ungated_test_dirs_prefix_entry_covers_whole_dir() -> None:
    test_dirs = ["tests/risk/unit", "tests/pnl/unit"]
    assert ungated_test_dirs(test_dirs, ("tests/",)) == []


def test_ungated_test_dirs_colocated_scripts_dir_covered_by_its_own_entry() -> None:
    """The scripts/plan-hygiene/ fix shape: naming the dir directly covers it."""
    assert ungated_test_dirs(["scripts/plan-hygiene"], ("tests/unit/", "scripts/plan-hygiene/")) == []


def test_ungated_test_dirs_colocated_scripts_dir_uncovered_without_its_entry() -> None:
    """Reproduces the actual bug: scripts/plan-hygiene/ ships tests but PYTEST_UNIT_DIR
    only lists the OTHER co-located scripts/ dirs — the exact pre-4a4716151f state."""
    test_dirs = ["scripts/plan-hygiene", "scripts/quality_gates"]
    entries = ("tests/unit/", "scripts/quality_gates/", "scripts/cicd/", "scripts/docs/")
    assert ungated_test_dirs(test_dirs, entries) == ["scripts/plan-hygiene"]


def test_ungated_test_dirs_file_scoped_entry_still_counts_as_covered() -> None:
    """A single-file PYTEST_UNIT_DIR entry inside the test dir is coarse partial
    coverage, not a full ungating — out of scope for this checker (a distinct debt
    class from the MTDS zero-collection bug)."""
    test_dirs = ["tests/defi_execution/unit"]
    entries = ("tests/defi_execution/unit/test_defi_lateral_loader.py",)
    assert ungated_test_dirs(test_dirs, entries) == []


def test_ungated_test_dirs_self_discovering_none_is_always_empty() -> None:
    assert ungated_test_dirs(["tests/anything/unit"], None) == []


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


# ── main(): synthetic new-uncollected-dir cases (the "done when" proof) ────


def _write_fleet_repo(
    workspace_root: Path,
    name: str,
    pytest_unit_dir: str,
    test_dirs: list[str],
) -> None:
    repo_root = workspace_root / name
    (repo_root / ".git").mkdir(parents=True)
    (repo_root / "scripts").mkdir(parents=True)
    (repo_root / "scripts" / "quality-gates.sh").write_text(
        f'source "${{WORKSPACE_ROOT}}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"\n'
        f'PYTEST_UNIT_DIR="{pytest_unit_dir}"\n',
        encoding="utf-8",
    )
    for test_dir in test_dirs:
        (repo_root / test_dir).mkdir(parents=True)
        (repo_root / test_dir / "test_placeholder.py").write_text("def test_x(): pass\n", encoding="utf-8")


def test_main_flags_synthetic_new_ungated_family(tmp_path: Path) -> None:
    """Reproduces the exact MTDS bug shape: a repo grows a NEW
    `tests/<family>/unit/` dir that PYTEST_UNIT_DIR doesn't reach. With an
    empty (zero) baseline, main() must exit 1 and name the ungated dir."""
    _write_fleet_repo(
        tmp_path,
        "synthetic-repo",
        pytest_unit_dir="tests/unit/",
        test_dirs=["tests/unit", "tests/new_family/unit"],
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


def test_main_flags_synthetic_new_ungated_colocated_scripts_dir(tmp_path: Path) -> None:
    """Reproduces the ACTUAL unified-trading-pm bug: a repo grows a NEW co-located
    scripts/<name>/test_*.py dir PYTEST_UNIT_DIR doesn't reach — v1's tests/<family>/unit/-
    only scan could never have flagged this shape (it never looked outside tests/)."""
    _write_fleet_repo(
        tmp_path,
        "synthetic-repo-scripts",
        pytest_unit_dir="tests/unit/ scripts/quality_gates/",
        test_dirs=["tests/unit", "scripts/quality_gates", "scripts/plan-hygiene"],
    )
    baseline_file = tmp_path / "baseline.yaml"
    write_baseline({}, Baseline(), path=baseline_file)

    exit_code = main(
        [
            "--workspace-root",
            str(tmp_path),
            "--scope",
            "synthetic-repo-scripts",
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
        test_dirs=["tests/unit", "tests/new_family/unit"],
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
        test_dirs=["tests/unit", "tests/legacy_family/unit"],
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
