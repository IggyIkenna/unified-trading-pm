"""Unit tests for scripts/manifest/generate-strategy-instrument-matrix.py.

Tests cover:
- Instrument format validation (canonical VENUE:TYPE:PAYLOAD[@CHAIN])
- Instrument vs venue cross-reference validation
- Instrument vs asset_group cross-reference validation
- Instrument-to-strategy map building
- Conflict detection (same instrument, different categories)
- Matrix generation
- Integration with real strategy-manifest.json
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

# ── Load the script as a module ──────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "manifest" / "generate-strategy-instrument-matrix.py"


def _load_module():
    """Load generate-strategy-instrument-matrix.py as a module."""
    spec = importlib.util.spec_from_file_location("generate_strategy_instrument_matrix", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_strategy(
    strategy_id: str = "TEST_STRAT",
    category: str = "CEFI",
    venues: list[str] | None = None,
    asset_groupes: list[str] | None = None,
    instruments: list[str] | None = None,
) -> dict[str, object]:
    if venues is None:
        venues = ["BINANCE-FUTURES"]
    if asset_groupes is None:
        asset_groupes = ["PERPETUAL"]
    if instruments is None:
        instruments = ["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"]
    return {
        "strategy_id": strategy_id,
        "category": category,
        "venues": venues,
        "asset_groupes": asset_groupes,
        "instruments": instruments,
        "live_capable": True,
        "batch_capable": True,
    }


# ── Tests: validate_instrument_format ────────────────────────────────────────


class TestInstrumentFormat:
    def test_valid_formats(self) -> None:
        assert MOD.validate_instrument_format("BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN") is True
        assert MOD.validate_instrument_format("AAVEV3_ETHEREUM:A_TOKEN:AUSDT@ETHEREUM") is True
        assert MOD.validate_instrument_format("DERIBIT:OPTION:BTC-28MAR26-80000-C") is True
        assert MOD.validate_instrument_format("IBKR:EQUITY:SPY") is True

    def test_invalid_formats(self) -> None:
        assert MOD.validate_instrument_format("") is False
        assert MOD.validate_instrument_format("just-a-string") is False
        assert MOD.validate_instrument_format("VENUE:") is False
        assert MOD.validate_instrument_format(":TYPE:PAYLOAD") is False


# ── Tests: extract_instrument_venue / extract_instrument_type ────────────────


class TestInstrumentParsing:
    def test_extract_venue(self) -> None:
        assert MOD.extract_instrument_venue("BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN") == "BINANCE-FUTURES"
        assert MOD.extract_instrument_venue("AAVEV3_ETHEREUM:A_TOKEN:AUSDT") == "AAVEV3_ETHEREUM"

    def test_extract_type(self) -> None:
        assert MOD.extract_instrument_type("BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN") == "PERPETUAL"
        assert MOD.extract_instrument_type("IBKR:EQUITY:SPY") == "EQUITY"

    def test_extract_from_empty(self) -> None:
        assert MOD.extract_instrument_venue("") == ""
        assert MOD.extract_instrument_type("") == ""


# ── Tests: validate_instruments_vs_venues ────────────────────────────────────


class TestInstrumentsVsVenues:
    def test_valid_instrument_venue(self) -> None:
        strat = _make_strategy(
            venues=["BINANCE-FUTURES"],
            instruments=["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"],
        )
        errors = MOD.validate_instruments_vs_venues(strat)
        assert not errors

    def test_instrument_venue_not_in_venues(self) -> None:
        strat = _make_strategy(
            venues=["BYBIT"],
            instruments=["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"],
        )
        errors = MOD.validate_instruments_vs_venues(strat)
        assert len(errors) == 1
        assert "BINANCE-FUTURES" in errors[0]
        assert "BYBIT" in errors[0]

    def test_no_instruments_no_errors(self) -> None:
        strat = _make_strategy(instruments=[])
        errors = MOD.validate_instruments_vs_venues(strat)
        assert not errors

    def test_multiple_venues_all_valid(self) -> None:
        strat = _make_strategy(
            venues=["BINANCE-FUTURES", "BYBIT"],
            instruments=[
                "BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN",
                "BYBIT:PERPETUAL:ETH-USDT@LIN",
            ],
        )
        errors = MOD.validate_instruments_vs_venues(strat)
        assert not errors


# ── Tests: validate_instruments_vs_asset_groupes ─────────────────────────────


class TestInstrumentsVsAssetClasses:
    def test_valid_instrument_type(self) -> None:
        strat = _make_strategy(
            asset_groupes=["PERPETUAL"],
            instruments=["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"],
        )
        errors = MOD.validate_instruments_vs_asset_groupes(strat)
        assert not errors

    def test_instrument_type_not_in_asset_groupes(self) -> None:
        strat = _make_strategy(
            asset_groupes=["SPOT"],
            instruments=["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"],
        )
        errors = MOD.validate_instruments_vs_asset_groupes(strat)
        assert len(errors) == 1
        assert "PERPETUAL" in errors[0]


# ── Tests: validate_instrument_id_formats ────────────────────────────────────


class TestInstrumentIdFormats:
    def test_valid_ids(self) -> None:
        strat = _make_strategy(
            instruments=[
                "BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN",
                "DERIBIT:OPTION:BTC-28MAR26-80000-C",
            ],
        )
        errors = MOD.validate_instrument_id_formats(strat)
        assert not errors

    def test_invalid_id(self) -> None:
        strat = _make_strategy(instruments=["bad-format"])
        errors = MOD.validate_instrument_id_formats(strat)
        assert len(errors) == 1
        assert "canonical format" in errors[0]


# ── Tests: build_instrument_to_strategies_map ────────────────────────────────


class TestInstrumentToStrategiesMap:
    def test_single_strategy_single_instrument(self) -> None:
        strategies = [_make_strategy()]
        result = MOD.build_instrument_to_strategies_map(strategies)
        assert "BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN" in result
        assert result["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"] == ["TEST_STRAT"]

    def test_shared_instrument(self) -> None:
        strategies = [
            _make_strategy(
                strategy_id="A",
                instruments=["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"],
            ),
            _make_strategy(
                strategy_id="B",
                instruments=["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"],
            ),
        ]
        result = MOD.build_instrument_to_strategies_map(strategies)
        assert len(result["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"]) == 2

    def test_no_instruments(self) -> None:
        strategies = [_make_strategy(instruments=[])]
        result = MOD.build_instrument_to_strategies_map(strategies)
        assert result == {}


# ── Tests: detect_instrument_conflicts ───────────────────────────────────────


class TestInstrumentConflicts:
    def test_no_conflict_same_category(self) -> None:
        instrument_map = {"BTC-PERP": ["A", "B"]}
        strategies_by_id = {
            "A": {"strategy_id": "A", "category": "CEFI"},
            "B": {"strategy_id": "B", "category": "CEFI"},
        }
        warnings = MOD.detect_instrument_conflicts(instrument_map, strategies_by_id)
        assert not warnings

    def test_conflict_different_categories(self) -> None:
        instrument_map = {"BTC-PERP": ["A", "B"]}
        strategies_by_id = {
            "A": {"strategy_id": "A", "category": "CEFI"},
            "B": {"strategy_id": "B", "category": "DEFI"},
        }
        warnings = MOD.detect_instrument_conflicts(instrument_map, strategies_by_id)
        assert len(warnings) == 1
        assert "CEFI" in warnings[0]
        assert "DEFI" in warnings[0]

    def test_single_strategy_per_instrument_no_conflict(self) -> None:
        instrument_map = {"BTC-PERP": ["A"], "ETH-PERP": ["B"]}
        strategies_by_id = {
            "A": {"strategy_id": "A", "category": "CEFI"},
            "B": {"strategy_id": "B", "category": "DEFI"},
        }
        warnings = MOD.detect_instrument_conflicts(instrument_map, strategies_by_id)
        assert not warnings


# ── Tests: build_matrix ──────────────────────────────────────────────────────


class TestBuildMatrix:
    def test_basic_matrix(self) -> None:
        strategies = [_make_strategy()]
        rows = MOD.build_matrix(strategies)
        assert len(rows) == 1
        assert rows[0]["strategy_id"] == "TEST_STRAT"
        assert rows[0]["category"] == "CEFI"

    def test_matrix_preserves_instruments(self) -> None:
        strategies = [
            _make_strategy(
                instruments=[
                    "BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN",
                    "BYBIT:PERPETUAL:ETH-USDT@LIN",
                ]
            )
        ]
        rows = MOD.build_matrix(strategies)
        assert len(rows[0]["instruments"]) == 2

    def test_empty_strategies(self) -> None:
        rows = MOD.build_matrix([])
        assert rows == []


# ── Tests: Integration with real manifest ────────────────────────────────────


class TestRealManifest:
    MANIFEST_PATH = REPO_ROOT / "strategy-manifest.json"

    def test_real_manifest_exists(self) -> None:
        assert self.MANIFEST_PATH.exists(), "strategy-manifest.json must exist"

    def test_real_manifest_has_instruments(self) -> None:
        with open(self.MANIFEST_PATH) as f:
            data = json.load(f)
        strategies = data["strategies"]
        # At least some strategies should have instruments
        with_instruments = [
            s
            for s in strategies
            if s.get("instruments") and isinstance(s["instruments"], list) and len(s["instruments"]) > 0
        ]
        assert len(with_instruments) > 0, "At least one strategy must have instruments"

    def test_real_manifest_instrument_formats_valid(self) -> None:
        with open(self.MANIFEST_PATH) as f:
            data = json.load(f)
        strategies = data["strategies"]
        all_errors: list[str] = []
        for strat in strategies:
            all_errors.extend(MOD.validate_instrument_id_formats(strat))
        assert not all_errors, f"Instrument format errors: {all_errors}"

    def test_real_manifest_instruments_match_venues(self) -> None:
        with open(self.MANIFEST_PATH) as f:
            data = json.load(f)
        strategies = data["strategies"]
        all_errors: list[str] = []
        for strat in strategies:
            all_errors.extend(MOD.validate_instruments_vs_venues(strat))
        assert not all_errors, f"Instrument/venue mismatch errors: {all_errors}"

    def test_real_manifest_matrix_not_empty(self) -> None:
        with open(self.MANIFEST_PATH) as f:
            data = json.load(f)
        strategies = data["strategies"]
        rows = MOD.build_matrix(strategies)
        assert len(rows) > 0

    def test_real_manifest_instrument_map(self) -> None:
        with open(self.MANIFEST_PATH) as f:
            data = json.load(f)
        strategies = data["strategies"]
        instrument_map = MOD.build_instrument_to_strategies_map(strategies)
        assert len(instrument_map) > 0, "Should have at least one instrument mapped"


# ── Tests: load_manifest ─────────────────────────────────────────────────


class TestLoadManifest:
    def test_loads_valid_manifest(self, tmp_path: Path) -> None:
        manifest = tmp_path / "strategy-manifest.json"
        manifest.write_text(json.dumps({"strategies": [_make_strategy()]}))
        data = MOD.load_manifest(manifest)
        assert "strategies" in data

    def test_exits_when_manifest_missing(self, tmp_path: Path) -> None:
        import pytest

        with pytest.raises(SystemExit):
            MOD.load_manifest(tmp_path / "nonexistent.json")


# ── Tests: print_matrix_table ─────────────────────────────────────────────


class TestPrintMatrixTable:
    def test_prints_without_error(self, capsys: object) -> None:
        rows: list[dict[str, str | list[str]]] = [
            {
                "strategy_id": "TEST_STRAT",
                "category": "CEFI",
                "venues": ["BINANCE-FUTURES"],
                "asset_groupes": ["PERPETUAL"],
                "instruments": ["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"],
                "live_capable": "True",
                "batch_capable": "True",
            }
        ]
        # Should not raise
        MOD.print_matrix_table(rows)

    def test_truncates_long_strings(self, capsys: object) -> None:
        rows: list[dict[str, str | list[str]]] = [
            {
                "strategy_id": "TEST_STRAT",
                "category": "CEFI",
                "venues": ["VENUE_" + str(i) for i in range(20)],
                "asset_groupes": ["PERPETUAL"],
                "instruments": ["VENUE_" + str(i) + ":PERPETUAL:BTC-USDT@LIN" for i in range(20)],
                "live_capable": "True",
                "batch_capable": "True",
            }
        ]
        MOD.print_matrix_table(rows)

    def test_empty_instruments(self, capsys: object) -> None:
        rows: list[dict[str, str | list[str]]] = [
            {
                "strategy_id": "TEST_STRAT",
                "category": "CEFI",
                "venues": [],
                "asset_groupes": [],
                "instruments": [],
                "live_capable": "False",
                "batch_capable": "False",
            }
        ]
        MOD.print_matrix_table(rows)


# ── Tests: main() ────────────────────────────────────────────────────────


class TestMainFunction:
    def test_main_with_valid_manifest(self, tmp_path: Path) -> None:
        manifest = tmp_path / "strategy-manifest.json"
        manifest.write_text(json.dumps({"strategies": [_make_strategy()]}))
        with patch.object(sys, "argv", ["prog", "--manifest", str(manifest)]):
            result = MOD.main()
        assert result == 0

    def test_main_json_output(self, tmp_path: Path) -> None:
        manifest = tmp_path / "strategy-manifest.json"
        manifest.write_text(json.dumps({"strategies": [_make_strategy()]}))
        with patch.object(sys, "argv", ["prog", "--json", "--manifest", str(manifest)]):
            result = MOD.main()
        assert result == 0

    def test_main_category_filter(self, tmp_path: Path) -> None:
        manifest = tmp_path / "strategy-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "strategies": [
                        _make_strategy(strategy_id="CEFI_1", category="CEFI"),
                        _make_strategy(strategy_id="DEFI_1", category="DEFI"),
                    ]
                }
            )
        )
        with patch.object(sys, "argv", ["prog", "--category", "CEFI", "--manifest", str(manifest)]):
            result = MOD.main()
        assert result == 0

    def test_main_category_filter_no_match(self, tmp_path: Path) -> None:
        manifest = tmp_path / "strategy-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "strategies": [
                        _make_strategy(strategy_id="CEFI_1", category="CEFI"),
                    ]
                }
            )
        )
        with patch.object(sys, "argv", ["prog", "--category", "SPORTS", "--manifest", str(manifest)]):
            result = MOD.main()
        assert result == 1  # No strategies found

    def test_main_with_instrument_errors(self, tmp_path: Path) -> None:
        manifest = tmp_path / "strategy-manifest.json"
        strat = _make_strategy(instruments=["bad-format"])
        manifest.write_text(json.dumps({"strategies": [strat]}))
        with patch.object(sys, "argv", ["prog", "--manifest", str(manifest)]):
            result = MOD.main()
        assert result == 1

    def test_main_with_warnings(self, tmp_path: Path) -> None:
        manifest = tmp_path / "strategy-manifest.json"
        strat_a = _make_strategy(
            strategy_id="A",
            category="CEFI",
            instruments=["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"],
        )
        strat_b = _make_strategy(
            strategy_id="B",
            category="DEFI",
            instruments=["BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"],
        )
        manifest.write_text(json.dumps({"strategies": [strat_a, strat_b]}))
        with patch.object(sys, "argv", ["prog", "--manifest", str(manifest)]):
            result = MOD.main()
        # Warnings don't cause failure
        assert result == 0
