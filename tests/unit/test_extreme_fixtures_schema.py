"""Validate all extreme fixture files load and conform to the expected schema.

Each fixture must have:
- scenario: str (non-empty)
- description: str (non-empty)
- data: list (non-empty)
- expected_behavior: dict (non-empty)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures" / "extreme"

# All expected fixture files
EXPECTED_FIXTURES = [
    "extreme_market_crash.json",
    "extreme_flash_crash.json",
    "extreme_high_volume.json",
    "extreme_missing_data.json",
    "extreme_stale_data.json",
    "extreme_zero_liquidity.json",
]

REQUIRED_TOP_LEVEL_KEYS = {"scenario", "description", "data", "expected_behavior"}


def _load_fixture(filename: str) -> dict[str, object]:
    """Load a fixture JSON file and return parsed dict."""
    path = FIXTURES_DIR / filename
    assert path.exists(), f"Fixture file not found: {path}"
    with path.open() as f:
        parsed: dict[str, object] = json.load(f)
    return parsed


class TestExtremeFixturesExist:
    """Verify all expected fixture files exist on disk."""

    def test_fixtures_directory_exists(self) -> None:
        assert FIXTURES_DIR.is_dir(), f"Fixtures directory not found: {FIXTURES_DIR}"

    @pytest.mark.parametrize("filename", EXPECTED_FIXTURES)
    def test_fixture_file_exists(self, filename: str) -> None:
        path = FIXTURES_DIR / filename
        assert path.exists(), f"Missing fixture: {path}"
        assert path.stat().st_size > 0, f"Empty fixture file: {path}"


class TestExtremeFixturesSchema:
    """Verify all fixture files conform to the required schema."""

    @pytest.mark.parametrize("filename", EXPECTED_FIXTURES)
    def test_fixture_has_required_keys(self, filename: str) -> None:
        data = _load_fixture(filename)
        missing = REQUIRED_TOP_LEVEL_KEYS - set(data.keys())
        assert not missing, f"{filename} missing keys: {missing}"

    @pytest.mark.parametrize("filename", EXPECTED_FIXTURES)
    def test_scenario_is_nonempty_string(self, filename: str) -> None:
        data = _load_fixture(filename)
        scenario = data["scenario"]
        assert isinstance(scenario, str), f"{filename}: scenario must be str, got {type(scenario)}"
        assert len(scenario) > 0, f"{filename}: scenario must not be empty"

    @pytest.mark.parametrize("filename", EXPECTED_FIXTURES)
    def test_description_is_nonempty_string(self, filename: str) -> None:
        data = _load_fixture(filename)
        description = data["description"]
        assert isinstance(description, str), (
            f"{filename}: description must be str, got {type(description)}"
        )
        assert len(description) > 0, f"{filename}: description must not be empty"

    @pytest.mark.parametrize("filename", EXPECTED_FIXTURES)
    def test_data_is_nonempty_list(self, filename: str) -> None:
        data = _load_fixture(filename)
        data_list = data["data"]
        assert isinstance(data_list, list), f"{filename}: data must be list, got {type(data_list)}"
        assert len(data_list) > 0, f"{filename}: data list must not be empty"

    @pytest.mark.parametrize("filename", EXPECTED_FIXTURES)
    def test_expected_behavior_is_nonempty_dict(self, filename: str) -> None:
        data = _load_fixture(filename)
        expected = data["expected_behavior"]
        assert isinstance(expected, dict), (
            f"{filename}: expected_behavior must be dict, got {type(expected)}"
        )
        assert len(expected) > 0, f"{filename}: expected_behavior must not be empty"

    @pytest.mark.parametrize("filename", EXPECTED_FIXTURES)
    def test_data_items_are_dicts_or_null(self, filename: str) -> None:
        """Each entry in data must be a dict or null (for missing_data scenario)."""
        data = _load_fixture(filename)
        data_list = data["data"]
        assert isinstance(data_list, list)
        for idx, item in enumerate(data_list):
            assert item is None or isinstance(item, dict), (
                f"{filename}: data[{idx}] must be dict or null, got {type(item)}"
            )


class TestExtremeFixturesContent:
    """Content-level validation for specific fixture scenarios."""

    def test_market_crash_price_decline(self) -> None:
        data = _load_fixture("extreme_market_crash.json")
        ticks = [t for t in data["data"] if isinstance(t, dict)]
        first_price = ticks[0]["price"]
        last_price = ticks[-1]["price"]
        assert isinstance(first_price, float)
        assert isinstance(last_price, float)
        decline_pct = (first_price - last_price) / first_price * 100
        assert decline_pct >= 29.0, f"Expected ~30% decline, got {decline_pct:.1f}%"

    def test_flash_crash_drop_and_recovery(self) -> None:
        data = _load_fixture("extreme_flash_crash.json")
        ticks = [t for t in data["data"] if isinstance(t, dict)]
        prices = [t["price"] for t in ticks]
        assert isinstance(prices[0], float)
        start = prices[0]
        min_price = min(prices)
        end = prices[-1]
        assert isinstance(min_price, float)
        assert isinstance(end, float)
        drop_pct = (start - min_price) / start * 100
        assert drop_pct >= 89.0, f"Expected ~90% drop, got {drop_pct:.1f}%"
        recovery_from_bottom = (end - min_price) / min_price * 100
        assert recovery_from_bottom > 500, f"Expected substantial recovery, got {recovery_from_bottom:.0f}%"

    def test_high_volume_has_orders(self) -> None:
        data = _load_fixture("extreme_high_volume.json")
        orders = [o for o in data["data"] if isinstance(o, dict)]
        assert len(orders) >= 20, "Expected at least 20 representative orders"
        for order in orders:
            assert "order_id" in order
            assert "side" in order
            assert order["side"] in ("buy", "sell")

    def test_missing_data_has_nulls(self) -> None:
        data = _load_fixture("extreme_missing_data.json")
        assert isinstance(data["data"], list)
        null_count = sum(1 for item in data["data"] if item is None)
        assert null_count >= 5, f"Expected at least 5 null entries, got {null_count}"

    def test_stale_data_all_old(self) -> None:
        data = _load_fixture("extreme_stale_data.json")
        expected = data["expected_behavior"]
        assert isinstance(expected, dict)
        ref_now = expected["reference_now_ms"]
        assert isinstance(ref_now, int)
        ticks = [t for t in data["data"] if isinstance(t, dict)]
        for tick in ticks:
            ts = tick["timestamp_ms"]
            assert isinstance(ts, int)
            age_seconds = (ref_now - ts) / 1000
            assert age_seconds >= 3060, f"Data point not stale enough: age={age_seconds}s"

    def test_zero_liquidity_has_empty_book_states(self) -> None:
        data = _load_fixture("extreme_zero_liquidity.json")
        snapshots = [s for s in data["data"] if isinstance(s, dict)]
        states = [s["state"] for s in snapshots]
        assert "both_empty" in states, "Must include a completely empty orderbook state"
        assert "asks_depleted" in states, "Must include an asks-depleted state"
        assert "bids_depleted" in states, "Must include a bids-depleted state"
        # Verify the both_empty state actually has empty books
        both_empty = [s for s in snapshots if s["state"] == "both_empty"][0]
        assert both_empty["bids"] == []
        assert both_empty["asks"] == []
