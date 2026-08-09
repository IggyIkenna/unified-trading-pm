# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_codex_doc_freshness.py.

Focus: the per-file baseline-diffing fix
(codex_doc_freshness_regression_ambient_staleness_drift_2026_08_09.md) — a doc
already known-violating at baseline time drifting further stale must NOT count
as a new regression, and the baseline file must store WORKSPACE-RELATIVE paths
(not absolute per-slot-worktree paths) so a snapshot written by one slot is
diffable by any other.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_codex_doc_freshness import (
    BaselineSnapshot,
    FreshnessViolation,
    _check_doc,
    _load_baseline,
    _new_violations,
    _relative_path,
    _write_baseline,
)


def _violation(rel_path: str, workspace_root: Path, reason: str = "stale") -> FreshnessViolation:
    return FreshnessViolation(workspace_root / rel_path, reason)


def test_relative_path_strips_workspace_root(tmp_path: Path) -> None:
    p = tmp_path / "unified-trading-pm" / "codex" / "02-data" / "x.md"
    assert _relative_path(p, tmp_path) == "unified-trading-pm/codex/02-data/x.md"


def test_relative_path_falls_back_to_absolute_outside_root(tmp_path: Path) -> None:
    other = Path("/some/unrelated/path.md")
    assert _relative_path(other, tmp_path) == str(other)


def test_write_then_load_baseline_round_trips_relative_paths(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.yaml"
    violations = [_violation("unified-trading-pm/codex/02-data/a.md", tmp_path)]
    _write_baseline(baseline_path, violations, tmp_path)

    loaded = _load_baseline(baseline_path)
    assert loaded.count == 1
    assert loaded.known_paths == frozenset({"unified-trading-pm/codex/02-data/a.md"})


def test_write_baseline_never_stores_absolute_paths(tmp_path: Path) -> None:
    """Direct regression test for the slot-10 incident: an absolute per-slot
    prefix (e.g. .tabs/4/) must never land in the shared baseline file."""
    baseline_path = tmp_path / "baseline.yaml"
    violations = [_violation("unified-trading-pm/codex/04-architecture/b.md", tmp_path)]
    _write_baseline(baseline_path, violations, tmp_path)

    raw = baseline_path.read_text(encoding="utf-8")
    assert str(tmp_path) not in raw
    assert ".tabs" not in raw


def test_load_baseline_missing_file_is_empty_snapshot(tmp_path: Path) -> None:
    loaded = _load_baseline(tmp_path / "does-not-exist.yaml")
    assert loaded.count == 0
    assert loaded.known_paths == frozenset()


def test_load_baseline_ignores_malformed_entries(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.yaml"
    baseline_path.write_text(
        "violation_count: 2\n"
        "baseline_files:\n"
        "  - path: unified-trading-pm/codex/a.md\n"
        "    reason: stale\n"
        "  - not-a-dict-marker\n",
        encoding="utf-8",
    )
    loaded = _load_baseline(baseline_path)
    assert loaded.count == 2
    assert loaded.known_paths == frozenset({"unified-trading-pm/codex/a.md"})


def test_new_violations_excludes_already_known_paths(tmp_path: Path) -> None:
    """The core ambient-drift fix: a doc already in the baseline snapshot
    getting older (still stale, or now MORE stale) is not a new regression."""
    known = _violation("unified-trading-pm/codex/02-data/already_stale.md", tmp_path)
    baseline = BaselineSnapshot(1, frozenset({_relative_path(known.path, tmp_path)}))

    result = _new_violations([known], baseline, tmp_path)

    assert result == []


def test_new_violations_flags_paths_absent_from_baseline(tmp_path: Path) -> None:
    known = _violation("unified-trading-pm/codex/02-data/already_stale.md", tmp_path)
    fresh_regression = _violation("unified-trading-pm/codex/05-infrastructure/newly_stale.md", tmp_path)
    baseline = BaselineSnapshot(1, frozenset({_relative_path(known.path, tmp_path)}))

    result = _new_violations([known, fresh_regression], baseline, tmp_path)

    assert result == [fresh_regression]


def test_new_violations_empty_baseline_flags_every_violation(tmp_path: Path) -> None:
    v = _violation("unified-trading-pm/codex/02-data/a.md", tmp_path)
    baseline = BaselineSnapshot(0, frozenset())

    assert _new_violations([v], baseline, tmp_path) == [v]


def test_new_violations_no_violations_is_always_clean(tmp_path: Path) -> None:
    baseline = BaselineSnapshot(3, frozenset({"unified-trading-pm/codex/x.md"}))
    assert _new_violations([], baseline, tmp_path) == []


# ---------------------------------------------------------------------------
# _check_doc — unchanged behaviour sanity checks (not the focus of this fix,
# but cheap to lock in given the file's already open for review).
# ---------------------------------------------------------------------------


def test_check_doc_missing_frontmatter(tmp_path: Path) -> None:
    p = tmp_path / "no_fm.md"
    p.write_text("# just a heading, no frontmatter\n", encoding="utf-8")
    v = _check_doc(p, 90, datetime.date(2026, 8, 9))
    assert v is not None
    assert v.reason == "no-frontmatter"


def test_check_doc_missing_last_reviewed_field(tmp_path: Path) -> None:
    p = tmp_path / "no_field.md"
    p.write_text("---\ndoc_type: codex-ssot\n---\nbody\n", encoding="utf-8")
    v = _check_doc(p, 90, datetime.date(2026, 8, 9))
    assert v is not None
    assert v.reason == "no-last_reviewed-field"


def test_check_doc_stale(tmp_path: Path) -> None:
    p = tmp_path / "stale.md"
    p.write_text("---\nlast_reviewed: 2026-01-01\n---\nbody\n", encoding="utf-8")
    v = _check_doc(p, 90, datetime.date(2026, 8, 9))
    assert v is not None
    assert v.reason == "stale"


def test_check_doc_fresh_is_clean(tmp_path: Path) -> None:
    p = tmp_path / "fresh.md"
    p.write_text("---\nlast_reviewed: 2026-08-01\n---\nbody\n", encoding="utf-8")
    assert _check_doc(p, 90, datetime.date(2026, 8, 9)) is None


def test_check_doc_future_dated_is_clean_not_an_error(tmp_path: Path) -> None:
    """Staggered-review convention (see module docstring): a future
    last_reviewed is intentional, never flagged."""
    p = tmp_path / "future.md"
    p.write_text("---\nlast_reviewed: 2026-10-20\n---\nbody\n", encoding="utf-8")
    assert _check_doc(p, 90, datetime.date(2026, 8, 9)) is None
