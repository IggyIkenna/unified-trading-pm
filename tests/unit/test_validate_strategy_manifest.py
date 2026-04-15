"""Unit tests for scripts/validation/validate-strategy-manifest.py.

Tests cover:
  - JSON structure validation (valid, invalid, missing keys)
  - Duplicate strategy_id detection
  - Required field validation
  - Maturity sub-structure validation
  - Class path existence checks
  - Instrument matrix generation
  - Maturity consistency checks
  - Orphan strategy detection
  - End-to-end main() with real manifest
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

# ── Load the script as a module ──────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validation" / "validate-strategy-manifest.py"


def _load_validator():
    """Load validate-strategy-manifest.py as a module."""
    spec = importlib.util.spec_from_file_location("validate_strategy_manifest", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_validator()


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_strategy(
    strategy_id: str = "TEST_STRATEGY_1",
    display_name: str = "Test Strategy",
    category: str = "CEFI",
    domain: str = "cefi",
    asset_classes: list[str] | None = None,
    venues: list[str] | None = None,
    class_path: str = "strategy_service.engine.strategies.test.TestStrategy",
    maturity: dict[str, object] | None = None,
) -> dict[str, object]:
    """Create a minimal valid strategy entry."""
    if asset_classes is None:
        asset_classes = ["PERPETUAL"]
    if venues is None:
        venues = ["BINANCE-FUTURES"]
    if maturity is None:
        maturity = {
            "code": {
                "status": "C1",
                "class_exists": True,
                "unit_tests": False,
                "qg_pass": False,
                "merged": False,
            },
            "deployment": {
                "status": "D0",
                "batch_analytics": False,
                "mock_smoke": False,
                "batch_live_recon": False,
            },
            "business": {
                "status": "B0",
                "backtest_profitable": False,
                "live_1d_match": False,
                "live_1w_match": False,
                "strategy_deck": False,
            },
        }
    return {
        "strategy_id": strategy_id,
        "display_name": display_name,
        "category": category,
        "domain": domain,
        "asset_classes": asset_classes,
        "venues": venues,
        "class_path": class_path,
        "maturity": maturity,
    }


# ── Tests: validate_json_structure ───────────────────────────────────────────


class TestValidateJsonStructure:
    def test_valid_manifest(self, tmp_path: Path) -> None:
        manifest = tmp_path / "strategy-manifest.json"
        manifest.write_text(json.dumps({"strategies": [_make_strategy()]}))
        data, errors = MOD.validate_json_structure(manifest)
        assert not errors
        assert data is not None
        assert "strategies" in data

    def test_missing_file(self, tmp_path: Path) -> None:
        manifest = tmp_path / "nonexistent.json"
        data, errors = MOD.validate_json_structure(manifest)
        assert data is None
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_invalid_json(self, tmp_path: Path) -> None:
        manifest = tmp_path / "bad.json"
        manifest.write_text("{invalid json,,}")
        data, errors = MOD.validate_json_structure(manifest)
        assert data is None
        assert len(errors) == 1
        assert "Invalid JSON" in errors[0]

    def test_missing_strategies_key(self, tmp_path: Path) -> None:
        manifest = tmp_path / "no-strategies.json"
        manifest.write_text(json.dumps({"version": "1.0"}))
        data, errors = MOD.validate_json_structure(manifest)
        assert data is None
        assert any("strategies" in e for e in errors)

    def test_strategies_not_array(self, tmp_path: Path) -> None:
        manifest = tmp_path / "bad-type.json"
        manifest.write_text(json.dumps({"strategies": "not-a-list"}))
        data, errors = MOD.validate_json_structure(manifest)
        assert data is None
        assert any("array" in e for e in errors)

    def test_top_level_not_object(self, tmp_path: Path) -> None:
        manifest = tmp_path / "array.json"
        manifest.write_text(json.dumps([1, 2, 3]))
        data, errors = MOD.validate_json_structure(manifest)
        assert data is None
        assert any("object" in e for e in errors)


# ── Tests: validate_no_duplicate_ids ─────────────────────────────────────────


class TestValidateNoDuplicateIds:
    def test_no_duplicates(self) -> None:
        strategies = [
            _make_strategy(strategy_id="A"),
            _make_strategy(strategy_id="B"),
            _make_strategy(strategy_id="C"),
        ]
        errors = MOD.validate_no_duplicate_ids(strategies)
        assert not errors

    def test_with_duplicates(self) -> None:
        strategies = [
            _make_strategy(strategy_id="A"),
            _make_strategy(strategy_id="B"),
            _make_strategy(strategy_id="A"),
        ]
        errors = MOD.validate_no_duplicate_ids(strategies)
        assert len(errors) == 1
        assert "Duplicate" in errors[0]
        assert "'A'" in errors[0]

    def test_multiple_duplicates(self) -> None:
        strategies = [
            _make_strategy(strategy_id="A"),
            _make_strategy(strategy_id="A"),
            _make_strategy(strategy_id="B"),
            _make_strategy(strategy_id="B"),
        ]
        errors = MOD.validate_no_duplicate_ids(strategies)
        assert len(errors) == 2

    def test_empty_list(self) -> None:
        errors = MOD.validate_no_duplicate_ids([])
        assert not errors


# ── Tests: validate_required_fields ──────────────────────────────────────────


class TestValidateRequiredFields:
    def test_all_fields_present(self) -> None:
        errors = MOD.validate_required_fields([_make_strategy()])
        assert not errors

    def test_missing_field(self) -> None:
        strat = _make_strategy()
        del strat["display_name"]
        errors = MOD.validate_required_fields([strat])
        assert len(errors) == 1
        assert "display_name" in errors[0]

    def test_invalid_category(self) -> None:
        strat = _make_strategy(category="INVALID_CAT")
        errors = MOD.validate_required_fields([strat])
        assert len(errors) == 1
        assert "unknown category" in errors[0]

    def test_invalid_domain(self) -> None:
        strat = _make_strategy(domain="invalid_domain")
        errors = MOD.validate_required_fields([strat])
        assert len(errors) == 1
        assert "unknown domain" in errors[0]

    def test_asset_classes_not_list(self) -> None:
        strat = _make_strategy()
        strat["asset_classes"] = "PERPETUAL"
        errors = MOD.validate_required_fields([strat])
        assert any("list" in e for e in errors)

    def test_venues_not_list(self) -> None:
        strat = _make_strategy()
        strat["venues"] = "BINANCE"
        errors = MOD.validate_required_fields([strat])
        assert any("list" in e for e in errors)

    def test_maturity_missing_code(self) -> None:
        strat = _make_strategy(
            maturity={
                "deployment": {
                    "status": "D0",
                    "batch_analytics": False,
                    "mock_smoke": False,
                    "batch_live_recon": False,
                },
                "business": {
                    "status": "B0",
                    "backtest_profitable": False,
                    "live_1d_match": False,
                    "live_1w_match": False,
                    "strategy_deck": False,
                },
            }
        )
        errors = MOD.validate_required_fields([strat])
        assert any("code" in e for e in errors)

    def test_maturity_code_missing_field(self) -> None:
        strat = _make_strategy(
            maturity={
                "code": {"status": "C0", "class_exists": False},
                "deployment": {
                    "status": "D0",
                    "batch_analytics": False,
                    "mock_smoke": False,
                    "batch_live_recon": False,
                },
                "business": {
                    "status": "B0",
                    "backtest_profitable": False,
                    "live_1d_match": False,
                    "live_1w_match": False,
                    "strategy_deck": False,
                },
            }
        )
        errors = MOD.validate_required_fields([strat])
        assert any("maturity.code missing fields" in e for e in errors)

    def test_valid_categories_accepted(self) -> None:
        for cat, dom in [
            ("CEFI", "cefi"),
            ("TRADFI", "tradfi"),
            ("DEFI", "defi"),
            ("SPORTS", "sports"),
            ("QUANT", "quant"),
            ("OPTIONS", "options"),
        ]:
            errors = MOD.validate_required_fields([_make_strategy(category=cat, domain=dom)])
            assert not errors, f"Category {cat} / domain {dom} should be valid"


# ── Tests: validate_class_paths ──────────────────────────────────────────────


class TestValidateClassPaths:
    def test_skips_when_class_exists_false(self) -> None:
        strat = _make_strategy(
            maturity={
                "code": {
                    "status": "C0",
                    "class_exists": False,
                    "unit_tests": False,
                    "qg_pass": False,
                    "merged": False,
                },
                "deployment": {
                    "status": "D0",
                    "batch_analytics": False,
                    "mock_smoke": False,
                    "batch_live_recon": False,
                },
                "business": {
                    "status": "B0",
                    "backtest_profitable": False,
                    "live_1d_match": False,
                    "live_1w_match": False,
                    "strategy_deck": False,
                },
            }
        )
        errors, warnings = MOD.validate_class_paths([strat])
        assert not errors

    def test_warns_when_strategy_service_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", Path("/nonexistent/path"))
        strat = _make_strategy()
        errors, warnings = MOD.validate_class_paths([strat])
        assert not errors
        assert any("strategy-service not found" in w for w in warnings)

    def test_errors_when_module_file_missing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", tmp_path)
        monkeypatch.setattr(MOD, "WORKSPACE_ROOT", tmp_path.parent)
        strat = _make_strategy(class_path="strategy_service.engine.strategies.nonexistent.NoStrategy")
        errors, warnings = MOD.validate_class_paths([strat])
        assert len(errors) == 1
        assert "class_exists=true but module file not found" in errors[0]

    def test_passes_when_module_file_exists(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", tmp_path)
        monkeypatch.setattr(MOD, "WORKSPACE_ROOT", tmp_path.parent)
        # Create the module file
        module_dir = tmp_path / "strategy_service" / "engine" / "strategies"
        module_dir.mkdir(parents=True)
        (module_dir / "test_strat.py").write_text("class TestStrategy: pass")
        strat = _make_strategy(class_path="strategy_service.engine.strategies.test_strat.TestStrategy")
        errors, warnings = MOD.validate_class_paths([strat])
        assert not errors


# ── Tests: generate_instrument_matrix ────────────────────────────────────────


class TestGenerateInstrumentMatrix:
    def test_basic_matrix(self) -> None:
        strat = _make_strategy(
            venues=["BINANCE-FUTURES", "BYBIT"],
            asset_classes=["PERPETUAL", "SPOT"],
        )
        rows, warnings = MOD.generate_instrument_matrix([strat])
        assert len(rows) == 4  # 2 venues x 2 asset classes
        assert not warnings

    def test_empty_venues_warns(self) -> None:
        strat = _make_strategy(venues=[])
        rows, warnings = MOD.generate_instrument_matrix([strat])
        assert any("no venues" in w for w in warnings)

    def test_empty_asset_classes_warns(self) -> None:
        strat = _make_strategy(asset_classes=[])
        rows, warnings = MOD.generate_instrument_matrix([strat])
        assert any("no asset_classes" in w for w in warnings)

    def test_venues_only_no_asset_classes(self) -> None:
        strat = _make_strategy(venues=["BINANCE"], asset_classes=[])
        rows, warnings = MOD.generate_instrument_matrix([strat])
        # Should produce rows with "(none)" for asset class
        assert len(rows) == 1
        assert rows[0][2] == "(none)"

    def test_empty_strategies(self) -> None:
        rows, warnings = MOD.generate_instrument_matrix([])
        assert not rows
        assert not warnings


# ── Tests: validate_maturity_consistency ──────────────────────────────────────


class TestValidateMaturityConsistency:
    def test_consistent_c0(self) -> None:
        strat = _make_strategy(
            maturity={
                "code": {
                    "status": "C0",
                    "class_exists": False,
                    "unit_tests": False,
                    "qg_pass": False,
                    "merged": False,
                },
                "deployment": {
                    "status": "D0",
                    "batch_analytics": False,
                    "mock_smoke": False,
                    "batch_live_recon": False,
                },
                "business": {
                    "status": "B0",
                    "backtest_profitable": False,
                    "live_1d_match": False,
                    "live_1w_match": False,
                    "strategy_deck": False,
                },
            }
        )
        warnings = MOD.validate_maturity_consistency([strat])
        assert not warnings

    def test_consistent_c4(self) -> None:
        strat = _make_strategy(
            maturity={
                "code": {
                    "status": "C4",
                    "class_exists": True,
                    "unit_tests": True,
                    "qg_pass": True,
                    "merged": True,
                },
                "deployment": {
                    "status": "D0",
                    "batch_analytics": False,
                    "mock_smoke": False,
                    "batch_live_recon": False,
                },
                "business": {
                    "status": "B0",
                    "backtest_profitable": False,
                    "live_1d_match": False,
                    "live_1w_match": False,
                    "strategy_deck": False,
                },
            }
        )
        warnings = MOD.validate_maturity_consistency([strat])
        assert not warnings

    def test_inconsistent_c1_with_tests(self) -> None:
        strat = _make_strategy(
            maturity={
                "code": {
                    "status": "C1",
                    "class_exists": True,
                    "unit_tests": True,  # inconsistent: C1 should not have tests
                    "qg_pass": False,
                    "merged": False,
                },
                "deployment": {
                    "status": "D0",
                    "batch_analytics": False,
                    "mock_smoke": False,
                    "batch_live_recon": False,
                },
                "business": {
                    "status": "B0",
                    "backtest_profitable": False,
                    "live_1d_match": False,
                    "live_1w_match": False,
                    "strategy_deck": False,
                },
            }
        )
        warnings = MOD.validate_maturity_consistency([strat])
        assert len(warnings) >= 1
        assert any("unit_tests" in w for w in warnings)

    def test_inconsistent_c0_with_class_exists(self) -> None:
        strat = _make_strategy(
            maturity={
                "code": {
                    "status": "C0",
                    "class_exists": True,  # inconsistent: C0 should have nothing
                    "unit_tests": False,
                    "qg_pass": False,
                    "merged": False,
                },
                "deployment": {
                    "status": "D0",
                    "batch_analytics": False,
                    "mock_smoke": False,
                    "batch_live_recon": False,
                },
                "business": {
                    "status": "B0",
                    "backtest_profitable": False,
                    "live_1d_match": False,
                    "live_1w_match": False,
                    "strategy_deck": False,
                },
            }
        )
        warnings = MOD.validate_maturity_consistency([strat])
        assert len(warnings) >= 1
        assert any("class_exists" in w for w in warnings)


# ── Tests: find_orphan_strategies ────────────────────────────────────────────


class TestFindOrphanStrategies:
    def test_no_orphans_when_dir_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", Path("/nonexistent"))
        warnings = MOD.find_orphan_strategies([_make_strategy()])
        assert not warnings

    def test_detects_orphan_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", tmp_path)
        strategies_dir = tmp_path / "strategy_service" / "engine" / "strategies"
        strategies_dir.mkdir(parents=True)
        (strategies_dir / "orphan_strategy.py").write_text("class Orphan: pass")
        # Manifest has no strategy pointing to orphan_strategy
        strat = _make_strategy(class_path="strategy_service.engine.strategies.known.KnownStrategy")
        warnings = MOD.find_orphan_strategies([strat])
        assert len(warnings) == 1
        assert "orphan_strategy" in warnings[0]

    def test_skips_base_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", tmp_path)
        strategies_dir = tmp_path / "strategy_service" / "engine" / "strategies"
        strategies_dir.mkdir(parents=True)
        # These should be skipped
        (strategies_dir / "__init__.py").write_text("")
        (strategies_dir / "base_strategy.py").write_text("")
        (strategies_dir / "sports_base.py").write_text("")
        (strategies_dir / "defi_base.py").write_text("")
        warnings = MOD.find_orphan_strategies([])
        assert not warnings

    def test_no_orphan_when_matched(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", tmp_path)
        strategies_dir = tmp_path / "strategy_service" / "engine" / "strategies"
        strategies_dir.mkdir(parents=True)
        (strategies_dir / "my_strategy.py").write_text("class MyStrategy: pass")
        strat = _make_strategy(class_path="strategy_service.engine.strategies.my_strategy.MyStrategy")
        warnings = MOD.find_orphan_strategies([strat])
        assert not warnings


# ── Tests: _class_path_to_module_file ────────────────────────────────────────


class TestClassPathToModuleFile:
    def test_simple_path(self) -> None:
        result = MOD._class_path_to_module_file("strategy_service.engine.strategies.cefi_momentum.CeFiMomentumStrategy")
        expected = MOD.STRATEGY_SERVICE_ROOT / "strategy_service/engine/strategies/cefi_momentum.py"
        assert result == expected

    def test_nested_path(self) -> None:
        result = MOD._class_path_to_module_file(
            "strategy_service.engine.strategies.sports.kelly.KellyCriterionStrategy"
        )
        expected = MOD.STRATEGY_SERVICE_ROOT / "strategy_service/engine/strategies/sports/kelly.py"
        assert result == expected


# ── Tests: main() with real manifest ─────────────────────────────────────────


class TestMainWithRealManifest:
    """Integration-style test using the actual strategy-manifest.json."""

    def test_real_manifest_exists(self) -> None:
        assert MOD.MANIFEST_PATH.exists(), "strategy-manifest.json must exist in PM repo"

    def test_real_manifest_is_valid_json(self) -> None:
        data, errors = MOD.validate_json_structure(MOD.MANIFEST_PATH)
        assert not errors, f"Real manifest has JSON errors: {errors}"
        assert data is not None

    def test_real_manifest_no_duplicate_ids(self) -> None:
        data, _ = MOD.validate_json_structure(MOD.MANIFEST_PATH)
        assert data is not None
        errors = MOD.validate_no_duplicate_ids(data["strategies"])
        assert not errors, f"Real manifest has duplicate IDs: {errors}"

    def test_real_manifest_required_fields(self) -> None:
        data, _ = MOD.validate_json_structure(MOD.MANIFEST_PATH)
        assert data is not None
        errors = MOD.validate_required_fields(data["strategies"])
        assert not errors, f"Real manifest missing required fields: {errors}"

    def test_real_manifest_has_strategies(self) -> None:
        data, _ = MOD.validate_json_structure(MOD.MANIFEST_PATH)
        assert data is not None
        assert len(data["strategies"]) > 0, "Real manifest must have at least one strategy"

    def test_real_manifest_instrument_matrix_not_empty(self) -> None:
        data, _ = MOD.validate_json_structure(MOD.MANIFEST_PATH)
        assert data is not None
        rows, _ = MOD.generate_instrument_matrix(data["strategies"])
        assert len(rows) > 0, "Real manifest must produce non-empty instrument matrix"


# ── Tests: main() with synthetic data ─────────────────────────────────────


class TestMainFunction:
    """Test the main() function end-to-end with synthetic manifest data."""

    def test_main_with_valid_manifest(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 0 when manifest is fully valid."""
        manifest = tmp_path / "strategy-manifest.json"
        manifest.write_text(json.dumps({"strategies": [_make_strategy()]}))
        monkeypatch.setattr(MOD, "MANIFEST_PATH", manifest)
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", Path("/nonexistent"))
        result = MOD.main()
        assert result == 0

    def test_main_with_missing_manifest(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 1 when manifest file is missing."""
        manifest = tmp_path / "nonexistent.json"
        monkeypatch.setattr(MOD, "MANIFEST_PATH", manifest)
        result = MOD.main()
        assert result == 1

    def test_main_with_invalid_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 1 when manifest contains invalid JSON."""
        manifest = tmp_path / "bad.json"
        manifest.write_text("{bad json,,}")
        monkeypatch.setattr(MOD, "MANIFEST_PATH", manifest)
        result = MOD.main()
        assert result == 1

    def test_main_with_duplicate_ids(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 1 when strategies have duplicate IDs."""
        manifest = tmp_path / "strategy-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "strategies": [
                        _make_strategy(strategy_id="DUP"),
                        _make_strategy(strategy_id="DUP"),
                    ]
                }
            )
        )
        monkeypatch.setattr(MOD, "MANIFEST_PATH", manifest)
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", Path("/nonexistent"))
        result = MOD.main()
        assert result == 1

    def test_main_with_missing_fields(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 1 when required fields are missing."""
        strat = _make_strategy()
        del strat["display_name"]
        manifest = tmp_path / "strategy-manifest.json"
        manifest.write_text(json.dumps({"strategies": [strat]}))
        monkeypatch.setattr(MOD, "MANIFEST_PATH", manifest)
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", Path("/nonexistent"))
        result = MOD.main()
        assert result == 1

    def test_main_reports_maturity_warnings(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() reports warnings for maturity inconsistencies but still returns 0."""
        strat = _make_strategy(
            maturity={
                "code": {
                    "status": "C0",
                    "class_exists": True,  # inconsistent with C0
                    "unit_tests": False,
                    "qg_pass": False,
                    "merged": False,
                },
                "deployment": {
                    "status": "D0",
                    "batch_analytics": False,
                    "mock_smoke": False,
                    "batch_live_recon": False,
                },
                "business": {
                    "status": "B0",
                    "backtest_profitable": False,
                    "live_1d_match": False,
                    "live_1w_match": False,
                    "strategy_deck": False,
                },
            }
        )
        manifest = tmp_path / "strategy-manifest.json"
        manifest.write_text(json.dumps({"strategies": [strat]}))
        monkeypatch.setattr(MOD, "MANIFEST_PATH", manifest)
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", Path("/nonexistent"))
        # Warnings don't cause failure
        result = MOD.main()
        assert result == 0

    def test_main_with_class_path_errors(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 1 when class_exists=true but file is missing."""
        strat = _make_strategy(class_path="strategy_service.engine.strategies.nonexistent.NoStrategy")
        manifest = tmp_path / "strategy-manifest.json"
        manifest.write_text(json.dumps({"strategies": [strat]}))
        monkeypatch.setattr(MOD, "MANIFEST_PATH", manifest)
        monkeypatch.setattr(MOD, "STRATEGY_SERVICE_ROOT", tmp_path / "strategy-service")
        (tmp_path / "strategy-service").mkdir()
        monkeypatch.setattr(MOD, "WORKSPACE_ROOT", tmp_path)
        result = MOD.main()
        assert result == 1

    def test_main_maturity_not_object(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Maturity as a non-dict triggers an error."""
        strat = _make_strategy()
        strat["maturity"] = "invalid"
        errors = MOD.validate_required_fields([strat])
        assert any("must be an object" in e for e in errors)

    def test_main_maturity_sub_key_not_object(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Maturity sub-key as a non-dict triggers an error."""
        strat = _make_strategy(
            maturity={
                "code": "not_a_dict",
                "deployment": {
                    "status": "D0",
                    "batch_analytics": False,
                    "mock_smoke": False,
                    "batch_live_recon": False,
                },
                "business": {
                    "status": "B0",
                    "backtest_profitable": False,
                    "live_1d_match": False,
                    "live_1w_match": False,
                    "strategy_deck": False,
                },
            }
        )
        errors = MOD.validate_required_fields([strat])
        assert any("must be an object" in e for e in errors)
