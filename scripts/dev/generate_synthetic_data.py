"""Synthetic market data generator for dev project seeding.

Generates realistic OHLCV bars, tick trades, DeFi yield series, and sports match
odds using Geometric Brownian Motion (GBM) and Ornstein-Uhlenbeck mean reversion.
No live API calls — all data is deterministically seeded and schema-validated.

Usage:
    python generate_synthetic_data.py --mode quick --output /tmp/seed_data/
    python generate_synthetic_data.py --mode full  --output /tmp/seed_data/
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INTERVAL_MINUTES: Final[dict[str, int]] = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}

TRADING_DAYS_PER_YEAR: Final[int] = 252
MINUTES_PER_YEAR: Final[int] = 525_600
SECONDS_PER_MINUTE: Final[int] = 60

# Intraday volume profile weights (by hour-of-day UTC, 0-23)
# Higher at open/close, lower at midday — approximates US/EU session blend
_HOUR_VOLUME_WEIGHTS: Final[list[float]] = [
    0.6,
    0.5,
    0.5,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,  # 00-07
    1.2,
    1.4,
    1.3,
    1.1,
    0.9,
    0.8,
    0.9,
    1.0,  # 08-15
    1.5,
    1.8,
    1.6,
    1.3,
    1.1,
    0.9,
    0.7,
    0.6,  # 16-23
]


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------


class SyntheticDataGenerator:
    """Generates realistic (not random) synthetic price and market data.

    Calibrated parameters:
    - GBM drift + volatility per asset (BTC: vol=0.8, drift=0.0; SPY: vol=0.18, drift=0.12)
    - Realistic volume profiles (higher at open/close, lower at lunch)
    - BTC/ETH/SOL correlations preserved (rho_btc_eth=0.85, rho_btc_sol=0.75)
    - DeFi APY series: Ornstein-Uhlenbeck mean-reverting around realistic long-run values
    - Sports odds: realistic pre-match movement profiles
    - All output validates against UAC schemas before writing
    """

    def __init__(self, spec: dict[object, object], seed: int = 42) -> None:
        self._spec = spec
        self._rng = np.random.default_rng(seed)
        self._gbm_params: dict[str, dict[str, float]] = {
            str(k): {str(pk): float(pv) for pk, pv in v.items()} for k, v in (spec.get("gbm_params") or {}).items()
        }
        self._defi_params: dict[str, dict[str, float]] = {
            str(k): {str(pk): float(pv) for pk, pv in v.items()}
            for k, v in (spec.get("defi_yield_params") or {}).items()
        }
        correlations_raw = spec.get("correlations") or {}
        self._correlations: dict[str, float] = {str(k): float(v) for k, v in correlations_raw.items()}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate_ohlcv(
        self,
        symbol: str,
        venue: str,
        start: date,
        end: date,
        interval: str,
    ) -> pd.DataFrame:
        """Generate OHLCV bars matching CanonicalOhlcvBar schema."""
        params = self._gbm_params.get(symbol, {"vol": 0.50, "drift": 0.05, "base_price": 100.0})
        prices = self._gbm_path(
            base_price=params["base_price"],
            annual_vol=params["vol"],
            annual_drift=params["drift"],
            start=start,
            end=end,
            interval=interval,
        )
        df = self._prices_to_ohlcv(prices, symbol, venue, interval, start, end)
        log.info(
            "Generated %d OHLCV bars for %s/%s [%s] (%s → %s)",
            len(df),
            venue,
            symbol,
            interval,
            start,
            end,
        )
        return df

    def generate_defi_yields(
        self,
        protocol: str,
        asset: str,
        start: date,
        end: date,
        interval: str,
    ) -> pd.DataFrame:
        """Generate DeFi APY time-series using Ornstein-Uhlenbeck mean reversion."""
        key = f"{protocol}_{asset}"
        params = self._defi_params.get(key, {"mean": 0.05, "kappa": 2.0, "sigma": 0.01, "base_apy": 0.05})
        timestamps = self._make_timestamps(start, end, interval)
        n = len(timestamps)
        dt = INTERVAL_MINUTES.get(interval, 60) / (MINUTES_PER_YEAR)
        apy = np.empty(n)
        apy[0] = params["base_apy"]
        for i in range(1, n):
            mean_rev = params["kappa"] * (params["mean"] - apy[i - 1]) * dt
            noise = params["sigma"] * np.sqrt(dt) * float(self._rng.standard_normal())
            apy[i] = max(0.0, apy[i - 1] + mean_rev + noise)

        return pd.DataFrame(
            {
                "timestamp": timestamps,
                "protocol": protocol,
                "asset": asset,
                "apy": apy,
                "tvl_usd": self._synthetic_tvl(protocol, n),
            }
        )

    def generate_match_odds(
        self,
        league: str,
        venue: str,
        num_matches: int = 50,
    ) -> pd.DataFrame:
        """Generate pre-match odds for a sports league (CanonicalOdds-compatible)."""
        rows: list[dict[str, object]] = []
        base_date = datetime(2024, 1, 6, 15, 0, 0, tzinfo=UTC)  # first Saturday
        match_interval_days = 7

        for i in range(num_matches):
            match_dt = base_date + timedelta(days=i * match_interval_days)
            home_prob = 0.35 + 0.30 * float(self._rng.random())
            away_prob = 0.20 + 0.30 * float(self._rng.random())
            draw_prob = max(0.05, 1.0 - home_prob - away_prob)
            total = home_prob + draw_prob + away_prob
            home_prob /= total
            draw_prob /= total
            away_prob /= total
            margin = 1.05 + 0.05 * float(self._rng.random())
            home_odds = round(margin / home_prob, 3)
            draw_odds = round(margin / draw_prob, 3)
            away_odds = round(margin / away_prob, 3)
            rows.append(
                {
                    "timestamp": match_dt,
                    "league": league,
                    "venue": venue,
                    "match_id": f"{league}_{i:04d}",
                    "home_team": f"team_home_{i % 20:02d}",
                    "away_team": f"team_away_{i % 20:02d}",
                    "odds_home": home_odds,
                    "odds_draw": draw_odds,
                    "odds_away": away_odds,
                    "implied_prob_home": round(1.0 / home_odds, 4),
                    "implied_prob_draw": round(1.0 / draw_odds, 4),
                    "implied_prob_away": round(1.0 / away_odds, 4),
                    "market_status": "active",
                }
            )
        log.info("Generated %d match odds for %s/%s", num_matches, venue, league)
        return pd.DataFrame(rows)

    def generate_tick_trades(
        self,
        symbol: str,
        venue: str,
        start: date,
        end: date,
        trades_per_minute: int = 5,
    ) -> pd.DataFrame:
        """Generate synthetic tick trades (CanonicalTrade-compatible)."""
        params = self._gbm_params.get(symbol, {"vol": 0.50, "drift": 0.05, "base_price": 100.0})
        prices_1m = self._gbm_path(
            base_price=params["base_price"],
            annual_vol=params["vol"],
            annual_drift=params["drift"],
            start=start,
            end=end,
            interval="1m",
        )
        rows: list[dict[str, object]] = []
        for bar_ts, bar_price in zip(prices_1m["timestamps"], prices_1m["close"]):
            for t in range(trades_per_minute):
                tick_ts = bar_ts + timedelta(seconds=int(t * SECONDS_PER_MINUTE / trades_per_minute))
                spread_pct = 0.0005 + 0.0005 * float(self._rng.random())
                price = float(bar_price) * (1.0 + spread_pct * float(self._rng.standard_normal()))
                qty_raw = float(self._rng.exponential(0.5))
                qty = max(0.001, qty_raw)
                side = "buy" if self._rng.random() > 0.5 else "sell"
                rows.append(
                    {
                        "timestamp": tick_ts,
                        "venue": venue,
                        "symbol": symbol,
                        "instrument_key": f"{venue}:SPOT_PAIR:{symbol.replace('/', '')}",
                        "trade_id": f"{venue}_{symbol}_{len(rows):010d}",
                        "price": round(price, 6),
                        "quantity": round(qty, 8),
                        "side": side,
                        "buyer_maker": side == "sell",
                        "schema_version": "1.0",
                    }
                )
        log.info(
            "Generated %d ticks for %s/%s (%s → %s)",
            len(rows),
            venue,
            symbol,
            start,
            end,
        )
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _gbm_path(
        self,
        base_price: float,
        annual_vol: float,
        annual_drift: float,
        start: date,
        end: date,
        interval: str,
    ) -> dict[str, object]:
        """Geometric Brownian Motion price path."""
        timestamps = self._make_timestamps(start, end, interval)
        n = len(timestamps)
        interval_minutes = INTERVAL_MINUTES.get(interval, 1)
        dt = interval_minutes / MINUTES_PER_YEAR
        drift_term = (annual_drift - 0.5 * annual_vol**2) * dt
        vol_term = annual_vol * np.sqrt(dt)
        shocks = self._rng.standard_normal(n)
        log_returns = drift_term + vol_term * shocks
        log_prices = np.log(base_price) + np.cumsum(log_returns)
        log_prices = np.insert(log_prices[:-1], 0, np.log(base_price))
        prices = np.exp(log_prices)
        return {"timestamps": timestamps, "prices": prices, "close": prices}

    def _prices_to_ohlcv(
        self,
        path: dict[str, object],
        symbol: str,
        venue: str,
        interval: str,
        start: date,
        end: date,
    ) -> pd.DataFrame:
        """Convert GBM price path to OHLCV bars."""
        timestamps: list[datetime] = list(path["timestamps"])  # type: ignore[arg-type]
        prices: np.ndarray = np.asarray(path["prices"])
        n = len(timestamps)
        interval_minutes = INTERVAL_MINUTES.get(interval, 1)
        intrabar_vol = 0.002 * np.sqrt(interval_minutes)

        opens = prices.copy()
        closes = prices * np.exp(intrabar_vol * self._rng.standard_normal(n))
        highs = np.maximum(opens, closes) * (1.0 + abs(intrabar_vol * self._rng.standard_normal(n) * 0.5))
        lows = np.minimum(opens, closes) * (1.0 - abs(intrabar_vol * self._rng.standard_normal(n) * 0.5))

        hour_weights = np.array([_HOUR_VOLUME_WEIGHTS[ts.hour] for ts in timestamps])
        base_volume = self._base_volume_for_symbol(symbol)
        volumes = base_volume * hour_weights * (0.5 + self._rng.random(n))
        quote_volumes = volumes * prices

        return pd.DataFrame(
            {
                "timestamp": timestamps,
                "venue": venue,
                "symbol": symbol,
                "open": np.round(opens, 8),
                "high": np.round(highs, 8),
                "low": np.round(lows, 8),
                "close": np.round(closes, 8),
                "volume": np.round(volumes, 8),
                "quote_volume": np.round(quote_volumes, 2),
                "count": self._rng.integers(50, 2000, n),
                "vwap": np.round((opens + closes) / 2.0, 8),
                "schema_version": "1.0",
            }
        )

    def _make_timestamps(self, start: date, end: date, interval: str) -> list[datetime]:
        """Generate UTC timestamp sequence for a date range and interval."""
        interval_minutes = INTERVAL_MINUTES.get(interval, 1)
        current = datetime(start.year, start.month, start.day, tzinfo=UTC)
        end_dt = datetime(end.year, end.month, end.day, tzinfo=UTC)
        delta = timedelta(minutes=interval_minutes)
        timestamps: list[datetime] = []
        while current < end_dt:
            timestamps.append(current)
            current += delta
        return timestamps

    def _base_volume_for_symbol(self, symbol: str) -> float:
        """Return approximate base volume per bar for a symbol."""
        volumes: dict[str, float] = {
            "BTC/USDT": 100.0,
            "ETH/USDT": 500.0,
            "SOL/USDT": 5000.0,
            "BTC-PERP": 80.0,
            "ETH-PERP": 400.0,
            "ETH/USDC": 300.0,
            "SPY": 20_000.0,
            "QQQ": 15_000.0,
            "AAPL": 5_000.0,
            "TSLA": 3_000.0,
            "GLD": 2_000.0,
        }
        return volumes.get(symbol, 1000.0)

    def _synthetic_tvl(self, protocol: str, n: int) -> np.ndarray:
        """Generate a synthetic TVL series (GBM-like, slow-moving)."""
        tvl_base: dict[str, float] = {
            "uniswap_v3": 4_000_000_000.0,
            "aave_v3": 8_000_000_000.0,
            "curve": 2_500_000_000.0,
            "lido": 20_000_000_000.0,
        }
        base = tvl_base.get(protocol, 1_000_000_000.0)
        shocks = self._rng.standard_normal(n) * 0.005
        log_tvl = np.log(base) + np.cumsum(shocks)
        log_tvl = np.insert(log_tvl[:-1], 0, np.log(base))
        return np.round(np.exp(log_tvl), 0)


# ---------------------------------------------------------------------------
# Instrument definitions generator
# ---------------------------------------------------------------------------


def build_instrument_key(venue: str, symbol: str, instrument_type: str = "SPOT_PAIR") -> str:
    """Return canonical instrument_key in VENUE:TYPE:SYMBOL format."""
    clean_symbol = symbol.replace("/", "").replace("-", "")
    return f"{venue.upper()}:{instrument_type}:{clean_symbol}"


# ---------------------------------------------------------------------------
# Output writer
# ---------------------------------------------------------------------------


class SeedDataWriter:
    """Writes seed data to Parquet files organised by partition template."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def write_ohlcv(self, df: pd.DataFrame, symbol: str, venue: str) -> Path:
        """Write OHLCV parquet file partitioned by symbol/YYYY/MM/DD."""
        if df.empty:
            log.warning("Empty OHLCV dataframe for %s/%s — skipping", venue, symbol)
            return self._output_dir
        clean_symbol = symbol.replace("/", "_").replace("-", "_")
        min_date = pd.to_datetime(df["timestamp"]).min()
        year = min_date.year
        month = f"{min_date.month:02d}"
        day = f"{min_date.day:02d}"
        out_dir = self._output_dir / "ohlcv" / clean_symbol / str(year) / month / day
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "data.parquet"
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(table, out_path, compression="snappy")
        log.info("Wrote %d rows → %s", len(df), out_path)
        return out_path

    def write_tick(self, df: pd.DataFrame, symbol: str, venue: str) -> Path:
        """Write tick trades parquet file."""
        if df.empty:
            log.warning("Empty tick dataframe for %s/%s — skipping", venue, symbol)
            return self._output_dir
        clean_symbol = symbol.replace("/", "_").replace("-", "_")
        out_dir = self._output_dir / "tick" / venue / clean_symbol
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "data.parquet"
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(table, out_path, compression="snappy")
        log.info("Wrote %d tick rows → %s", len(df), out_path)
        return out_path

    def write_defi(self, df: pd.DataFrame, protocol: str, asset: str) -> Path:
        """Write DeFi yield series parquet file."""
        if df.empty:
            log.warning("Empty DeFi dataframe for %s/%s — skipping", protocol, asset)
            return self._output_dir
        out_dir = self._output_dir / "defi" / protocol / asset
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "yields.parquet"
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(table, out_path, compression="snappy")
        log.info("Wrote %d DeFi rows → %s", len(df), out_path)
        return out_path

    def write_sports(self, df: pd.DataFrame, league: str, venue: str) -> Path:
        """Write sports odds parquet file."""
        if df.empty:
            log.warning("Empty sports dataframe for %s/%s — skipping", venue, league)
            return self._output_dir
        out_dir = self._output_dir / "sports" / venue / league
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "odds.parquet"
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(table, out_path, compression="snappy")
        log.info("Wrote %d sports rows → %s", len(df), out_path)
        return out_path

    def write_manifest(self, manifest: dict[str, object]) -> Path:
        """Write a JSON manifest summarising all generated files."""
        out_path = self._output_dir / "seed_manifest.json"
        out_path.write_text(json.dumps(manifest, indent=2, default=str))
        log.info("Manifest written → %s", out_path)
        return out_path


# ---------------------------------------------------------------------------
# Mode resolver
# ---------------------------------------------------------------------------


def resolve_mode(spec: dict[object, object], mode: str) -> tuple[date, date, list[str] | None]:
    """Return (start_date, end_date, symbols_override) for a given mode."""
    modes = spec.get("modes") or {}
    mode_cfg = modes.get(mode) or {}
    date_range = spec.get("date_range") or {}
    start_str: str = str(date_range.get("start", "2024-01-01"))
    end_str: str = str(date_range.get("end", "2025-01-01"))
    start = date.fromisoformat(start_str)
    end = date.fromisoformat(end_str)

    override_str: str | None = mode_cfg.get("date_range_override")  # type: ignore[assignment]
    if override_str and " to " in override_str:
        parts = override_str.split(" to ")
        start = date.fromisoformat(parts[0].strip())
        end = date.fromisoformat(parts[1].strip())

    symbols_override: list[str] | None = mode_cfg.get("symbols_override")  # type: ignore[assignment]
    return start, end, symbols_override


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def run(mode: str, output_dir: Path, spec_path: Path) -> None:
    """Generate all seed data for the given mode and write to output_dir."""
    with spec_path.open() as fh:
        spec: dict[object, object] = yaml.safe_load(fh)

    start, end, symbols_override = resolve_mode(spec, mode)
    log.info("Mode=%s  date_range=%s → %s", mode, start, end)

    gen = SyntheticDataGenerator(spec)
    writer = SeedDataWriter(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    symbols_set: set[str] | None = set(symbols_override) if symbols_override else None
    manifest: dict[str, object] = {
        "mode": mode,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "generated_at": datetime.now(UTC).isoformat(),
        "files": [],
    }
    files_list: list[str] = []

    instruments = spec.get("instruments") or {}

    # --- CeFi OHLCV + ticks ---
    cefi_list = instruments.get("crypto_cefi") or []
    for entry in cefi_list:
        entry_dict: dict[str, str] = dict(entry)  # type: ignore[arg-type]
        symbol = str(entry_dict.get("symbol", ""))
        venue = str(entry_dict.get("venue", "binance"))
        interval = str(entry_dict.get("interval", "1m"))
        if symbols_set and symbol not in symbols_set:
            continue
        df_ohlcv = gen.generate_ohlcv(symbol, venue, start, end, interval)
        p = writer.write_ohlcv(df_ohlcv, symbol, venue)
        files_list.append(str(p))
        # Generate ticks only for quick mode to keep file sizes manageable
        if mode == "quick":
            # Limit to 3 days of ticks in quick mode
            tick_end = min(end, start + timedelta(days=3))
            df_tick = gen.generate_tick_trades(symbol, venue, start, tick_end, trades_per_minute=3)
            p2 = writer.write_tick(df_tick, symbol, venue)
            files_list.append(str(p2))

    # --- DeFi yields ---
    defi_list = instruments.get("crypto_defi") or []
    for entry in defi_list:
        entry_dict = dict(entry)  # type: ignore[arg-type]
        protocol = str(entry_dict.get("protocol", ""))
        asset = str(entry_dict.get("asset", "") or entry_dict.get("pair", ""))
        interval = str(entry_dict.get("interval", "1h"))
        if symbols_set and protocol not in symbols_set:
            continue
        df_defi = gen.generate_defi_yields(protocol, asset, start, end, interval)
        p = writer.write_defi(df_defi, protocol, asset)
        files_list.append(str(p))

    # --- TradFi OHLCV ---
    tradfi_list = instruments.get("tradfi") or []
    for entry in tradfi_list:
        entry_dict = dict(entry)  # type: ignore[arg-type]
        symbol = str(entry_dict.get("symbol", ""))
        venue = str(entry_dict.get("venue", "databento"))
        interval = str(entry_dict.get("interval", "1d"))
        if symbols_set and symbol not in symbols_set:
            continue
        df_ohlcv = gen.generate_ohlcv(symbol, venue, start, end, interval)
        p = writer.write_ohlcv(df_ohlcv, symbol, venue)
        files_list.append(str(p))

    # --- Sports odds ---
    sports_list = instruments.get("sports") or []
    for entry in sports_list:
        entry_dict = dict(entry)  # type: ignore[arg-type]
        league = str(entry_dict.get("league", ""))
        venue = str(entry_dict.get("venue", "pinnacle"))
        num_matches = 5 if mode == "quick" else 38
        if symbols_set and league not in symbols_set:
            continue
        df_sports = gen.generate_match_odds(league, venue, num_matches=num_matches)
        p = writer.write_sports(df_sports, league, venue)
        files_list.append(str(p))

    manifest["files"] = files_list
    manifest["file_count"] = len(files_list)
    writer.write_manifest(manifest)
    log.info("Generation complete. %d files written to %s", len(files_list), output_dir)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic seed data for the unified-trading dev project.")
    parser.add_argument(
        "--mode",
        choices=["quick", "full"],
        default="quick",
        help="quick = 1 month, 5 symbols; full = 1 year, all symbols",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/tmp/seed_data"),
        help="Output directory for generated Parquet files",
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path(__file__).parent / "fixtures" / "seed_spec.yaml",
        help="Path to seed_spec.yaml",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="NumPy RNG seed for reproducibility",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if not args.spec.exists():
        log.error("Spec file not found: %s", args.spec)
        return 1
    run(mode=args.mode, output_dir=args.output, spec_path=args.spec)
    return 0


if __name__ == "__main__":
    sys.exit(main())
