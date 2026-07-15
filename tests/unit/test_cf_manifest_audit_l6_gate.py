"""Unit tests for the L6-legacy-only gate in plans/audit/results/cf_manifest_audit_2026_06_01.py.

The gate was REDEFINED 2026-07-15 (operator ruling) to real-data-only: it counts legacy captured
cells with backing data (per-cell MAX instrument_count > 0) that are absent from canonical, and
reports ic=0 phantom cells separately instead of failing on them.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

import pandas as pd
import pytest


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "plans" / "audit" / "results" / "cf_manifest_audit_2026_06_01.py"
    spec = importlib.util.spec_from_file_location("cf_manifest_audit_2026_06_01", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


def _idx(rows: list[tuple[str, str, str, float]], status: str = "captured") -> pd.DataFrame:
    """Build a minimal availability-index frame: (date, venue, data_type, instrument_count)."""
    return pd.DataFrame(
        {
            "date": [r[0] for r in rows],
            "venue": [r[1] for r in rows],
            "data_type": [r[2] for r in rows],
            "instrument_count": [r[3] for r in rows],
            "capture_status": [status] * len(rows),
        }
    )


class TestSplitBackedCells:
    def test_splits_real_from_phantom_cells(self) -> None:
        df = _idx(
            [
                ("2018-01-01", "API_FOOTBALL", "MATCHES", 5.0),
                ("2018-01-02", "API_FOOTBALL", "INJURIES", 0.0),
            ]
        )
        real, phantom = MOD._split_backed_cells(df)
        assert real == {("2018-01-01", "API_FOOTBALL", "MATCHES")}
        assert phantom == {("2018-01-02", "API_FOOTBALL", "INJURIES")}

    def test_cell_is_real_when_any_row_has_backing_data(self) -> None:
        """Per-cell MAX, not per-row: a cell fanning out to many per-league populations is REAL
        if a single one is populated (Gotcha-#2 — a per-row/first-row test misclassifies it)."""
        df = _idx(
            [
                ("2018-01-01", "API_FOOTBALL", "MATCHES", 0.0),
                ("2018-01-01", "API_FOOTBALL", "MATCHES", 0.0),
                ("2018-01-01", "API_FOOTBALL", "MATCHES", 12.0),
            ]
        )
        real, phantom = MOD._split_backed_cells(df)
        assert real == {("2018-01-01", "API_FOOTBALL", "MATCHES")}
        assert phantom == set()

    def test_cell_is_phantom_only_when_every_row_is_zero(self) -> None:
        df = _idx([("2018-01-01", "API_FOOTBALL", "INJURIES", 0.0)] * 3)
        real, phantom = MOD._split_backed_cells(df)
        assert real == set()
        assert phantom == {("2018-01-01", "API_FOOTBALL", "INJURIES")}

    def test_null_instrument_count_is_not_real_data_evidence(self) -> None:
        df = _idx([("2018-01-01", "API_FOOTBALL", "WEATHER", float("nan"))])
        real, phantom = MOD._split_backed_cells(df)
        assert real == set()
        assert phantom == {("2018-01-01", "API_FOOTBALL", "WEATHER")}

    def test_non_captured_rows_are_ignored(self) -> None:
        df = _idx([("2018-01-01", "API_FOOTBALL", "MATCHES", 9.0)], status="empty_confirmed")
        real, phantom = MOD._split_backed_cells(df)
        assert real == set()
        assert phantom == set()

    def test_missing_instrument_count_column_treats_all_cells_as_real(self) -> None:
        """Conservative fallback: without the column the split is impossible, so the gate may read
        RED — it must never under-report data loss by assuming cells are phantoms."""
        df = _idx([("2018-01-01", "API_FOOTBALL", "MATCHES", 5.0)]).drop(columns=["instrument_count"])
        real, phantom = MOD._split_backed_cells(df)
        assert real == {("2018-01-01", "API_FOOTBALL", "MATCHES")}
        assert phantom == set()


class TestL6GateCriterion:
    """The gate's decision logic: real-stranded → RED; phantom-only stranded → GREEN + reported."""

    @staticmethod
    def _gate(legacy: pd.DataFrame, canon: pd.DataFrame) -> tuple[int, int]:
        cc = MOD._cells(canon)
        real, phantom = MOD._split_backed_cells(legacy)
        return len(real - cc), len(phantom - cc)

    def test_phantom_only_residual_is_green_and_reported_separately(self) -> None:
        """The E8 data-state: every stranded legacy cell is an ic=0 phantom → gate GREEN, but the
        phantoms stay VISIBLE on their own line rather than being silently dropped."""
        legacy = _idx(
            [
                ("2018-01-01", "API_FOOTBALL", "MATCHES", 5.0),
                ("2018-01-02", "API_FOOTBALL", "INJURIES", 0.0),
            ]
        )
        canon = _idx([("2018-01-01", "API_FOOTBALL", "MATCHES", 5.0)])
        legacy_only, phantom_residual = self._gate(legacy, canon)
        assert legacy_only == 0
        assert phantom_residual == 1

    def test_stranded_real_data_is_red(self) -> None:
        legacy = _idx([("2018-01-01", "API_FOOTBALL", "MATCHES", 5.0)])
        canon = _idx([("2020-06-06", "API_FOOTBALL", "MATCHES", 5.0)])
        legacy_only, phantom_residual = self._gate(legacy, canon)
        assert legacy_only == 1
        assert phantom_residual == 0

    def test_full_overlap_is_green_with_no_residual(self) -> None:
        rows = [("2018-01-01", "API_FOOTBALL", "MATCHES", 5.0)]
        legacy_only, phantom_residual = self._gate(_idx(rows), _idx(rows))
        assert legacy_only == 0
        assert phantom_residual == 0

    def test_phantom_present_in_canonical_is_not_residual(self) -> None:
        """A phantom the canonical also carries is not stranded — it is not reported."""
        rows = [("2018-01-02", "API_FOOTBALL", "INJURIES", 0.0)]
        legacy_only, phantom_residual = self._gate(_idx(rows), _idx(rows))
        assert legacy_only == 0
        assert phantom_residual == 0

    @pytest.mark.parametrize("ic", [1.0, 0.5, 100.0])
    def test_any_positive_instrument_count_counts_as_real(self, ic: float) -> None:
        legacy = _idx([("2018-01-01", "API_FOOTBALL", "MATCHES", ic)])
        canon = _idx([("2099-01-01", "OTHER", "OTHER", 1.0)])
        legacy_only, _ = self._gate(legacy, canon)
        assert legacy_only == 1
