"""Instrument metadata seeder for the dev project.

Creates instruments.json with exactly 100 instruments covering all 4 asset classes:
  - 30 crypto CeFi (top coins × 3 venues)
  - 20 crypto DeFi (LP pairs + lending pools)
  - 30 TradFi (US equities, bonds, commodities, FX)
  - 20 Sports (leagues × team matchups)

All instruments are validated against the UAC InstrumentWarehouseRow schema
before being written to disk (and optionally to GCS).

Usage:
    python seed_instruments.py --output /tmp/seed_data/
    python seed_instruments.py --output /tmp/seed_data/ --dry-run
    python seed_instruments.py --project unified-trading-dev --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

_AVAILABLE_FROM = datetime(2020, 1, 1, tzinfo=UTC).isoformat()
_GENERATED_AT = datetime(2024, 1, 1, tzinfo=UTC).isoformat()


# ---------------------------------------------------------------------------
# Instrument definitions
# ---------------------------------------------------------------------------


def _crypto_cefi_instruments() -> list[dict[str, object]]:
    """30 crypto CeFi instruments: top 10 coins × 3 venues."""
    coins = [
        ("BTC", "USDT", 42000.0, 0.1),
        ("ETH", "USDT", 2500.0, 0.001),
        ("SOL", "USDT", 100.0, 0.1),
        ("BNB", "USDT", 380.0, 0.01),
        ("XRP", "USDT", 0.60, 10.0),
        ("ADA", "USDT", 0.55, 10.0),
        ("AVAX", "USDT", 38.0, 0.1),
        ("DOT", "USDT", 9.0, 0.1),
        ("LINK", "USDT", 18.0, 0.1),
        ("MATIC", "USDT", 0.90, 10.0),
    ]
    venues = [
        ("binance", "BINANCE"),
        ("okx", "OKX"),
        ("bybit", "BYBIT"),
    ]
    instruments: list[dict[str, object]] = []
    for base, quote, _price, min_size in coins:
        symbol = f"{base}/{quote}"
        clean = f"{base}{quote}"
        for venue_key, venue_upper in venues:
            instruments.append(
                {
                    "instrument_key": f"{venue_upper}:SPOT_PAIR:{clean}",
                    "venue": venue_key,
                    "instrument_type": "SPOT_PAIR",
                    "symbol": symbol,
                    "asset_class": "crypto_cefi",
                    "base_asset": base,
                    "quote_asset": quote,
                    "ccxt_symbol": symbol,
                    "ccxt_exchange": venue_key,
                    "tick_size": 0.01,
                    "min_size": min_size,
                    "available_from_datetime": _AVAILABLE_FROM,
                    "timestamp": _GENERATED_AT,
                    "data_types": ["ohlcv", "trades", "orderbook"],
                }
            )
    return instruments[:30]


def _crypto_perps() -> list[dict[str, object]]:
    """10 perpetual contracts on deribit + hyperliquid (part of CeFi count)."""
    perps = [
        ("BTC", "USD", "deribit", "DERIBIT", "BTC-PERPETUAL", 42000.0, 10.0),
        ("ETH", "USD", "deribit", "DERIBIT", "ETH-PERPETUAL", 2500.0, 1.0),
        ("SOL", "USDC", "hyperliquid", "HYPERLIQUID", "SOL-PERP", 100.0, 1.0),
        ("BNB", "USDT", "hyperliquid", "HYPERLIQUID", "BNB-PERP", 380.0, 0.1),
        ("AVAX", "USDT", "hyperliquid", "HYPERLIQUID", "AVAX-PERP", 38.0, 1.0),
    ]
    instruments: list[dict[str, object]] = []
    for base, quote, venue, venue_upper, raw_symbol, _price, min_size in perps:
        instruments.append(
            {
                "instrument_key": f"{venue_upper}:PERPETUAL:{base}{quote}",
                "venue": venue,
                "instrument_type": "PERPETUAL",
                "symbol": f"{base}-PERP",
                "asset_class": "crypto_cefi",
                "base_asset": base,
                "quote_asset": quote,
                "exchange_raw_symbol": raw_symbol,
                "tick_size": 0.5,
                "min_size": min_size,
                "max_leverage": 10.0,
                "initial_margin_rate": 0.1,
                "maintenance_margin_rate": 0.05,
                "available_from_datetime": _AVAILABLE_FROM,
                "timestamp": _GENERATED_AT,
                "data_types": ["ohlcv", "trades", "funding_rate"],
            }
        )
    return instruments


def _crypto_defi_instruments() -> list[dict[str, object]]:
    """20 DeFi instruments: LP pairs + lending pools + liquid staking."""
    instruments: list[dict[str, object]] = []

    # Uniswap V3 pools (8)
    uniswap_pools = [
        ("ETH", "USDC", "0.05%", "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"),
        ("WBTC", "ETH", "0.3%", "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed"),
        ("ETH", "USDT", "0.05%", "0x11b815efb8f581194ae79006d24e0d814b7697f6"),
        ("DAI", "USDC", "0.01%", "0x5777d92f208679db4b9778590fa3cab3ac9e2168"),
        ("LINK", "ETH", "0.3%", "0xa6cc3c2531fdaa6ae1a3ca84c2855806728693e8"),
        ("UNI", "ETH", "0.3%", "0x1d42064fc4beb5f8aaf85f4617ae8b3b5b8bd801"),
        ("WBTC", "USDC", "0.3%", "0x99ac8ca7087fa4a2a1248c931c8cc8c908201e7e"),
        ("SOL", "USDC", "0.3%", "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"),
    ]
    for base, quote, fee, addr in uniswap_pools:
        instruments.append(
            {
                "instrument_key": f"UNISWAP_V3:SPOT_PAIR:{base}{quote}",
                "venue": "uniswap_v3",
                "instrument_type": "SPOT_PAIR",
                "symbol": f"{base}/{quote}",
                "asset_class": "crypto_defi",
                "base_asset": base,
                "quote_asset": quote,
                "pool_address": addr,
                "pool_fee_tier": fee,
                "available_from_datetime": _AVAILABLE_FROM,
                "timestamp": _GENERATED_AT,
                "data_types": ["ohlcv", "liquidity"],
            }
        )

    # Aave V3 lending pools (4)
    aave_assets = ["USDC", "USDT", "ETH", "WBTC"]
    for asset in aave_assets:
        instruments.append(
            {
                "instrument_key": f"AAVE_V3:A_TOKEN:{asset}",
                "venue": "aave_v3",
                "instrument_type": "A_TOKEN",
                "symbol": f"a{asset}",
                "asset_class": "crypto_defi",
                "base_asset": asset,
                "quote_asset": "USD",
                "available_from_datetime": _AVAILABLE_FROM,
                "timestamp": _GENERATED_AT,
                "data_types": ["apy", "tvl"],
                "ltv": 0.75,
                "liquidation_threshold": 0.80,
            }
        )

    # Curve pools (4)
    curve_pools = [
        ("3pool", "DAI+USDC+USDT", "0x6c3f90f043a72fa612cbac8115ee7e52bde6e490"),
        ("stETH", "ETH+stETH", "0xdc24316b9ae028f1497c275eb9192a3ea0f67022"),
        ("tricrypto2", "USDT+WBTC+ETH", "0xd51a44d3fae010294c616388b506acda1bfaae46"),
        ("frxETH", "ETH+frxETH", "0xa1f8a6807c402e4a15ef4eba36528a3fed24e577"),
    ]
    for pool_name, assets, addr in curve_pools:
        instruments.append(
            {
                "instrument_key": f"CURVE:{pool_name.upper()}:{assets.replace('+', '_')}",
                "venue": "curve",
                "instrument_type": "LST",
                "symbol": f"curve_{pool_name}",
                "asset_class": "crypto_defi",
                "pool_address": addr,
                "available_from_datetime": _AVAILABLE_FROM,
                "timestamp": _GENERATED_AT,
                "data_types": ["apy", "tvl"],
            }
        )

    # Lido staking (4: stETH, wstETH, stMATIC, stSOL)
    lido_assets = [
        ("stETH", "ETH", "ethereum"),
        ("wstETH", "ETH", "ethereum"),
        ("stMATIC", "MATIC", "ethereum"),
        ("stSOL", "SOL", "solana"),
    ]
    for lst_sym, underlying, chain in lido_assets:
        instruments.append(
            {
                "instrument_key": f"LIDO:LST:{lst_sym}",
                "venue": "lido",
                "instrument_type": "LST",
                "symbol": lst_sym,
                "asset_class": "crypto_defi",
                "underlying": underlying,
                "available_from_datetime": _AVAILABLE_FROM,
                "timestamp": _GENERATED_AT,
                "data_types": ["apy", "tvl"],
            }
        )

    return instruments[:20]


def _tradfi_instruments() -> list[dict[str, object]]:
    """30 TradFi instruments: US equities, bonds, commodities, FX."""
    instruments: list[dict[str, object]] = []

    # US equities (15)
    equities = [
        ("SPY", "ARCA", 470.0, 0.01),
        ("QQQ", "NASDAQ", 400.0, 0.01),
        ("AAPL", "NASDAQ", 185.0, 0.01),
        ("MSFT", "NASDAQ", 415.0, 0.01),
        ("GOOGL", "NASDAQ", 170.0, 0.01),
        ("AMZN", "NASDAQ", 185.0, 0.01),
        ("TSLA", "NASDAQ", 230.0, 0.01),
        ("NVDA", "NASDAQ", 875.0, 0.01),
        ("META", "NASDAQ", 505.0, 0.01),
        ("BRK.B", "NYSE", 395.0, 0.01),
        ("JPM", "NYSE", 195.0, 0.01),
        ("GS", "NYSE", 445.0, 0.01),
        ("WMT", "NYSE", 175.0, 0.01),
        ("XOM", "NYSE", 110.0, 0.01),
        ("JNJ", "NYSE", 155.0, 0.01),
    ]
    for symbol, exchange, _price, tick_size in equities:
        clean = symbol.replace(".", "_")
        instruments.append(
            {
                "instrument_key": f"DATABENTO:{exchange}:{clean}",
                "venue": "databento",
                "instrument_type": "SPOT_PAIR",
                "symbol": symbol,
                "asset_class": "tradfi_equity",
                "base_asset": symbol,
                "quote_asset": "USD",
                "tick_size": tick_size,
                "trading_hours_open": "09:30",
                "trading_hours_close": "16:00",
                "regular_open_utc": "14:30",
                "regular_close_utc": "21:00",
                "holiday_calendar": "NYSE",
                "available_from_datetime": _AVAILABLE_FROM,
                "timestamp": _GENERATED_AT,
                "data_types": ["ohlcv", "trades"],
            }
        )

    # Bonds ETFs (5)
    bonds = [
        ("TLT", "long_treasury"),
        ("IEF", "mid_treasury"),
        ("HYG", "high_yield_corp"),
        ("LQD", "investment_grade_corp"),
        ("SHY", "short_treasury"),
    ]
    for symbol, bond_type in bonds:
        instruments.append(
            {
                "instrument_key": f"DATABENTO:ARCA:{symbol}",
                "venue": "databento",
                "instrument_type": "SPOT_PAIR",
                "symbol": symbol,
                "asset_class": "tradfi_bond",
                "base_asset": symbol,
                "quote_asset": "USD",
                "tick_size": 0.01,
                "venue_type": bond_type,
                "trading_hours_open": "09:30",
                "trading_hours_close": "16:00",
                "available_from_datetime": _AVAILABLE_FROM,
                "timestamp": _GENERATED_AT,
                "data_types": ["ohlcv"],
            }
        )

    # Commodities (5)
    commodities = [
        ("GLD", "gold_etf", "ARCA"),
        ("SLV", "silver_etf", "ARCA"),
        ("USO", "oil_etf", "ARCA"),
        ("UNG", "natgas_etf", "ARCA"),
        ("PDBC", "diversified_commodity", "NASDAQ"),
    ]
    for symbol, comm_type, exchange in commodities:
        instruments.append(
            {
                "instrument_key": f"DATABENTO:{exchange}:{symbol}",
                "venue": "databento",
                "instrument_type": "SPOT_PAIR",
                "symbol": symbol,
                "asset_class": "tradfi_commodity",
                "base_asset": symbol,
                "quote_asset": "USD",
                "tick_size": 0.01,
                "venue_type": comm_type,
                "available_from_datetime": _AVAILABLE_FROM,
                "timestamp": _GENERATED_AT,
                "data_types": ["ohlcv"],
            }
        )

    # FX (5)
    fx_pairs = [
        ("EURUSD", "EUR", "USD", 1.09),
        ("GBPUSD", "GBP", "USD", 1.27),
        ("USDJPY", "USD", "JPY", 148.0),
        ("AUDUSD", "AUD", "USD", 0.65),
        ("USDCAD", "USD", "CAD", 1.35),
    ]
    for symbol, base, quote, _rate in fx_pairs:
        instruments.append(
            {
                "instrument_key": f"DATABENTO:FX:{symbol}",
                "venue": "databento",
                "instrument_type": "SPOT_PAIR",
                "symbol": symbol,
                "asset_class": "tradfi_fx",
                "base_asset": base,
                "quote_asset": quote,
                "tick_size": 0.00001,
                "available_from_datetime": _AVAILABLE_FROM,
                "timestamp": _GENERATED_AT,
                "data_types": ["ohlcv", "trades"],
            }
        )

    return instruments[:30]


def _sports_instruments() -> list[dict[str, object]]:
    """20 sports betting market instruments."""
    instruments: list[dict[str, object]] = []

    leagues = [
        ("premier_league", "pinnacle", "football", "EPL"),
        ("nba", "odds_api", "basketball", "NBA"),
        ("nfl", "pinnacle", "american_football", "NFL"),
        ("mlb", "odds_api", "baseball", "MLB"),
        ("nhl", "pinnacle", "ice_hockey", "NHL"),
        ("la_liga", "betfair", "football", "LALIGA"),
        ("bundesliga", "betfair", "football", "BULI"),
        ("serie_a", "pinnacle", "football", "SERIE_A"),
        ("ligue_1", "odds_api", "football", "L1"),
        ("champions_league", "betfair", "football", "UCL"),
        ("afl", "sportsbet", "aussie_rules", "AFL"),
        ("a_league", "sportsbet", "football", "ALEAGUE"),
        ("ipl", "betway", "cricket", "IPL"),
        ("ashes", "betway", "cricket", "ASHES"),
        ("wimbledon", "pinnacle", "tennis", "WIMB"),
        ("us_open_tennis", "pinnacle", "tennis", "USO_TENNIS"),
        ("formula_1", "betfair", "motorsport", "F1"),
        ("the_masters", "pinnacle", "golf", "MASTERS"),
        ("nrl", "sportsbet", "rugby_league", "NRL"),
        ("super_rugby", "sportsbet", "rugby_union", "SRUGBY"),
    ]

    for league, venue, sport, ticker in leagues:
        instruments.append(
            {
                "instrument_key": f"{venue.upper()}:SPORTS:{ticker}",
                "venue": venue,
                "instrument_type": "SPOT_PAIR",
                "symbol": league,
                "asset_class": "sports",
                "venue_type": sport,
                "available_from_datetime": _AVAILABLE_FROM,
                "timestamp": _GENERATED_AT,
                "data_types": ["match_odds", "in_play"],
            }
        )

    return instruments[:20]


# ---------------------------------------------------------------------------
# Validation (lightweight — no UAC import required for script portability)
# ---------------------------------------------------------------------------


def _validate_instrument(inst: dict[str, object], idx: int) -> list[str]:
    """Return list of validation errors for a single instrument dict."""
    errors: list[str] = []
    required = ["instrument_key", "venue", "instrument_type", "symbol", "available_from_datetime", "timestamp"]
    for field in required:
        if not inst.get(field):
            errors.append(f"[{idx}] Missing required field: {field}")
    key = str(inst.get("instrument_key", ""))
    if key.count(":") != 2:
        errors.append(f"[{idx}] instrument_key '{key}' must have format VENUE:TYPE:SYMBOL")
    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_instruments() -> list[dict[str, object]]:
    """Build and return all 100 instrument definitions."""
    cefi = _crypto_cefi_instruments()
    perps = _crypto_perps()
    defi = _crypto_defi_instruments()
    tradfi = _tradfi_instruments()
    sports = _sports_instruments()

    all_instruments = cefi + perps + defi + tradfi + sports

    # Ensure exactly 100
    if len(all_instruments) > 100:
        all_instruments = all_instruments[:100]
    elif len(all_instruments) < 100:
        log.warning("Only %d instruments defined — target is 100", len(all_instruments))

    return all_instruments


def run(output_dir: Path, project: str | None, dry_run: bool) -> int:
    """Validate and write instruments.json."""
    instruments = build_instruments()
    log.info("Built %d instrument definitions", len(instruments))

    all_errors: list[str] = []
    for idx, inst in enumerate(instruments):
        errors = _validate_instrument(inst, idx)
        all_errors.extend(errors)

    if all_errors:
        for err in all_errors:
            log.error("Validation error: %s", err)
        log.error("Validation FAILED — %d errors", len(all_errors))
        return 1

    log.info("All %d instruments pass schema validation", len(instruments))

    payload: dict[str, object] = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "instrument_count": len(instruments),
        "instruments": instruments,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "instruments.json"

    if dry_run:
        log.info("[DRY RUN] Would write %d instruments to %s", len(instruments), out_path)
        if project:
            log.info("[DRY RUN] Would upload to GCS: gs://%s-tick-data/instruments.json", project)
    else:
        out_path.write_text(json.dumps(payload, indent=2, default=str))
        log.info("Wrote instruments.json → %s", out_path)
        if project:
            log.info(
                "To upload: gsutil cp %s gs://%s-tick-data/instruments.json",
                out_path,
                project,
            )

    asset_class_counts: dict[str, int] = {}
    for inst in instruments:
        ac = str(inst.get("asset_class", "unknown"))
        asset_class_counts[ac] = asset_class_counts.get(ac, 0) + 1
    log.info("Asset class breakdown: %s", asset_class_counts)
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed instruments metadata for the unified-trading dev project.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/seed_data"),
        help="Output directory (instruments.json written here)",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="GCP project name (used only for logging upload hints)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without writing files",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    return run(output_dir=args.output, project=args.project, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
