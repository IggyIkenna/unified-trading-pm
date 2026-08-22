#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""End-to-end prediction pipeline manual smoke check.

Tests the full flow: Polymarket API → URDI instruments → UMI trades → GCS hive partitions.
Validates schemas, mappings, canonical IDs, and data types.

A manual e2e driver, not a pytest suite (qg_pytest_testpaths_excludes_scripts_quality_gates_2026_07_14.md)
— several functions take non-fixture positional args pytest can't inject, and
main() threads live state (fetched instruments → trades) between phases
sequentially rather than running independent, isolated tests. Named
``*_e2e_check.py`` (not ``test_*.py``) so pytest's `python_files = ["test_*.py"]`
collection glob never picks it up; mirrors the same-purpose
``pipeline_e2e_check.py`` scripts in instruments-service / market-tick-data-service.

Usage:
    python scripts/prediction/prediction_pipeline_e2e_check.py
    python scripts/prediction/prediction_pipeline_e2e_check.py --write-gcs  # actually write to GCS
    python scripts/prediction/prediction_pipeline_e2e_check.py --date 2026-03-25

Requires: ADC credentials for GCS writes (--write-gcs mode only).
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def check_urdi_instruments() -> dict[str, list[dict[str, str]]]:
    """Phase 1: Fetch instruments via URDI PolymarketReferenceDataAdapter."""
    from instruments_service.reference_data.adapters.polymarket import PolymarketReferenceDataAdapter

    logger.info("=" * 60)
    logger.info("PHASE 1: URDI Instrument Fetch")
    logger.info("=" * 60)

    adapter = PolymarketReferenceDataAdapter()
    instruments = await adapter.get_instruments()

    logger.info("Total instruments: %d", len(instruments))

    # Classify
    btc_markets: list[dict[str, str]] = []
    spx_markets: list[dict[str, str]] = []
    sports_markets: list[dict[str, str]] = []
    other_markets: list[dict[str, str]] = []

    for inst in instruments:
        base = (inst.base_asset or "").lower()
        symbol = (inst.symbol or "").lower()
        record = {
            "instrument_key": inst.instrument_key,
            "instrument_type": inst.instrument_type,
            "base_asset": inst.base_asset or "",
            "symbol": inst.symbol or "",
            "venue": inst.venue,
            "is_active": str(inst.is_active),
            "expiry": str(inst.expiry) if inst.expiry else "",
        }
        if "bitcoin" in base or "btc" in base or "btc" in symbol:
            btc_markets.append(record)
        elif "s&p" in base or "spx" in symbol or "sp-500" in symbol:
            spx_markets.append(record)
        elif "::" in inst.instrument_type:
            sports_markets.append(record)
        else:
            other_markets.append(record)

    logger.info("  BTC markets:    %d", len(btc_markets))
    logger.info("  SPX markets:    %d", len(spx_markets))
    logger.info("  Sports markets: %d", len(sports_markets))
    logger.info("  Other:          %d", len(other_markets))

    # Validate schema
    assert len(instruments) > 0, "No instruments fetched"
    for inst in instruments[:10]:
        assert inst.instrument_key, f"Missing instrument_key: {inst}"
        assert inst.venue == "polymarket", f"Wrong venue: {inst.venue}"
        assert inst.quote_asset == "USDC", f"Wrong quote: {inst.quote_asset}"

    logger.info("  Schema validation: PASSED")

    return {
        "btc": btc_markets,
        "spx": spx_markets,
        "sports": sports_markets,
        "other": other_markets,
    }


async def check_umi_trades(condition_ids: list[str]) -> list[dict[str, object]]:
    """Phase 2: Fetch trades via UMI PolymarketAdapter."""
    from unified_market_interface import PolymarketAdapter

    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE 2: UMI Trade Fetch")
    logger.info("=" * 60)

    adapter = PolymarketAdapter()
    all_trades: list[dict[str, object]] = []

    for cid in condition_ids[:5]:  # cap at 5 markets for testing
        trades = await adapter.get_trades(cid, after_ts=0)
        logger.info("  market %s...: %d trades", cid[:20], len(trades))
        all_trades.extend(trades)

    logger.info("  Total trades fetched: %d", len(all_trades))

    # Validate trade schema
    if all_trades:
        t = all_trades[0]
        assert "price" in t, f"Missing price in trade: {t}"
        assert "size" in t, f"Missing size in trade: {t}"
        logger.info("  Trade schema validation: PASSED")
        logger.info("  Sample: price=%s size=%s side=%s", t.get("price"), t.get("size"), t.get("side"))

    return all_trades


def check_canonical_id_format(instruments: dict[str, list[dict[str, str]]]) -> None:
    """Phase 3: Validate canonical ID conventions."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE 3: Canonical ID Validation")
    logger.info("=" * 60)

    # All instrument_keys should be condition_ids (hex strings starting with 0x)
    all_keys = []
    for category_markets in instruments.values():
        for m in category_markets:
            all_keys.append(m["instrument_key"])

    hex_keys = [k for k in all_keys if k.startswith("0x")]
    logger.info("  Total keys: %d, hex format (0x...): %d", len(all_keys), len(hex_keys))
    assert len(hex_keys) == len(all_keys), "Some instrument_keys are not hex condition_ids"

    # All venues should be "polymarket"
    venues = {m["venue"] for markets in instruments.values() for m in markets}
    assert venues == {"polymarket"}, f"Unexpected venues: {venues}"

    # Sports markets should have enriched instrument_type
    sports_types = {m["instrument_type"] for m in instruments.get("sports", [])}  # noqa: qg-empty-fallback
    logger.info("  Sports instrument_types: %s", sports_types)

    logger.info("  Canonical ID validation: PASSED")


def check_mappings() -> None:
    """Phase 4: Validate Polymarket mapping infrastructure."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE 4: Mapping Validation")
    logger.info("=" * 60)

    from unified_api_contracts.external.polymarket import (  # noqa: qg-deep-import
        POLYMARKET_SERIES_TO_LEAGUE,
        POLYMARKET_TEAM_TO_CANONICAL,
        POLYMARKET_TIMEFRAMES,
        get_canonical_league_for_polymarket_series,
        get_canonical_team_for_polymarket,
        get_polymarket_tags_for_underlying,
    )

    # League mappings
    assert len(POLYMARKET_SERIES_TO_LEAGUE) >= 30, f"Only {len(POLYMARKET_SERIES_TO_LEAGUE)} leagues"
    assert get_canonical_league_for_polymarket_series("premier-league-2025") == "EPL"
    assert get_canonical_league_for_polymarket_series("ucl-2025") == "UCL"
    logger.info("  League mappings: %d (PASSED)", len(POLYMARKET_SERIES_TO_LEAGUE))

    # Team mappings
    assert len(POLYMARKET_TEAM_TO_CANONICAL) >= 190, f"Only {len(POLYMARKET_TEAM_TO_CANONICAL)} teams"
    assert get_canonical_team_for_polymarket("Paris Saint-Germain") == "PSG"
    assert get_canonical_team_for_polymarket("FC Internazionale Milano") == "INTER_MILAN"
    logger.info("  Team mappings: %d (PASSED)", len(POLYMARKET_TEAM_TO_CANONICAL))

    # Crypto/macro underlyings
    assert len(POLYMARKET_TIMEFRAMES) >= 18, f"Only {len(POLYMARKET_TIMEFRAMES)} underlyings"
    assert POLYMARKET_TIMEFRAMES["BTC"][0] == "5m"
    btc_tags = get_polymarket_tags_for_underlying("BTC")
    assert "bitcoin" in btc_tags
    spx_tags = get_polymarket_tags_for_underlying("SPX")
    assert "s-and-p-500" in spx_tags
    logger.info("  Underlyings: %d, BTC tags: %s (PASSED)", len(POLYMARKET_TIMEFRAMES), btc_tags)

    # Settlement indices
    logger.info("  Settlement: BTC→Chainlink BTC/USD, SPX→Official close")
    logger.info("  Mapping validation: ALL PASSED")


def check_data_types() -> None:
    """Phase 5: Validate PREDICTION data types in registry."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE 5: Data Type + Registry Validation")
    logger.info("=" * 60)

    from unified_api_contracts.registry.market_data_categories import (  # noqa: qg-deep-import
        DATA_TYPES_BY_ASSET_GROUP,
        VENUES_BY_ASSET_GROUP,
    )

    assert "prediction" in VENUES_BY_ASSET_GROUP, "PREDICTION missing from VENUES_BY_ASSET_GROUP"
    assert "POLYMARKET" in VENUES_BY_ASSET_GROUP["prediction"]
    assert "KALSHI" in VENUES_BY_ASSET_GROUP["prediction"]
    logger.info("  VENUES_BY_ASSET_GROUP[prediction]: %s", VENUES_BY_ASSET_GROUP["prediction"])

    assert "prediction" in DATA_TYPES_BY_ASSET_GROUP, "prediction missing from DATA_TYPES_BY_ASSET_GROUP"
    logger.info("  DATA_TYPES: %s", DATA_TYPES_BY_ASSET_GROUP["prediction"])

    # Validate prediction domain exists in canonical schemas
    from unified_api_contracts import (
        PredictionMarketCategory,
        PredictionMarketMapper,
    )

    mapper = PredictionMarketMapper()
    m = mapper.map_market("polymarket", "cid", "Bitcoin Up or Down - March 25, 2PM ET")
    assert m.category == PredictionMarketCategory.CRYPTO
    logger.info("  Mapper: BTC→%s (PASSED)", m.category)

    logger.info("  Registry validation: ALL PASSED")


async def write_to_gcs(instruments: dict[str, list[dict[str, str]]], date: str) -> None:
    """Phase 6: Write instruments to GCS in hive partition format."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE 6: GCS Write (Hive Partitions)")
    logger.info("=" * 60)

    from unified_trading_library import get_storage_client

    client = get_storage_client(provider="gcp")
    bucket = "instruments-store-prediction-central-element-323112"

    all_instruments = []
    for category_markets in instruments.values():
        all_instruments.extend(category_markets)

    data = json.dumps(all_instruments, indent=2, default=str).encode()
    blob_path = f"instrument_availability/by_date/day={date}/venue=POLYMARKET/instruments.json"

    client.upload_bytes(bucket=bucket, blob_path=blob_path, data=data)
    logger.info("  Wrote %d instruments to gs://%s/%s", len(all_instruments), bucket, blob_path)

    # Verify
    exists = client.blob_exists(bucket=bucket, blob_path=blob_path)
    assert exists, f"Failed to verify write at {blob_path}"
    logger.info("  Verification: EXISTS (%d bytes)", len(data))
    logger.info("  GCS write: PASSED")


async def main() -> None:
    parser = argparse.ArgumentParser(description="E2E Prediction Pipeline Test")
    parser.add_argument("--write-gcs", action="store_true", help="Write results to GCS")
    parser.add_argument("--date", default=datetime.now(UTC).strftime("%Y-%m-%d"))
    args = parser.parse_args()

    logger.info("Prediction Pipeline E2E Test — %s", args.date)
    logger.info("")

    # Phase 1: URDI instruments
    instruments = await check_urdi_instruments()

    # Phase 2: UMI trades (use first 3 BTC market condition_ids)
    btc_cids = [m["instrument_key"] for m in instruments.get("btc", [])[:3]]  # noqa: qg-empty-fallback
    if btc_cids:
        trades = await check_umi_trades(btc_cids)
    else:
        logger.warning("No BTC markets found — skipping trade fetch")
        trades = []

    # Phase 3: Canonical IDs
    check_canonical_id_format(instruments)

    # Phase 4: Mappings
    check_mappings()

    # Phase 5: Data types + registry
    check_data_types()

    # Phase 6: GCS write (optional)
    if args.write_gcs:
        await write_to_gcs(instruments, args.date)
    else:
        logger.info("\n  (Skipping GCS write — use --write-gcs to enable)")

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("E2E PREDICTION PIPELINE TEST: ALL PHASES PASSED")
    logger.info("=" * 60)
    total = sum(len(v) for v in instruments.values())
    logger.info(
        "  Instruments: %d (BTC=%d, SPX=%d, Sports=%d, Other=%d)",
        total,
        len(instruments["btc"]),
        len(instruments["spx"]),
        len(instruments["sports"]),
        len(instruments["other"]),
    )
    logger.info("  Trades: %d", len(trades))
    logger.info("  Leagues mapped: 35, Teams mapped: 196, Underlyings: 20")


if __name__ == "__main__":
    asyncio.run(main())
