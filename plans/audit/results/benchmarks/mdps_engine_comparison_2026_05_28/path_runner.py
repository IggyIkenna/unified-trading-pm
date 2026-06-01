"""Per-engine benchmark runner.

Invoked as `uv run python path_runner.py <path-id> <data-dir> <output-dir>`.
Runs ONE engine path across all instrument parquets in data-dir, writes
candles to output-dir, and emits a JSON result line to stdout.

Each engine path is run in its OWN subprocess (driven by run_all.py) so
cross-path arena retention can't pollute the measurement. Within one path,
we iterate all 9 instruments in the SAME Python process so cumulative
RSS-after-N-instruments tells us how much each engine's allocator retains
across iterations.

Paths under test:
  A: pure polars end-to-end (scan_parquet lazy → group_by → write_parquet)
  B: pandas + pyarrow dtype_backend end-to-end (pd.read_parquet engine=pyarrow
     → pandas groupby → pyarrow write_table)
  C: current MDPS shape (polars read eager → to_pandas → from_pandas →
     polars group_by → polars write — the actual production round-trip)
  D: polars eager read (no .to_pandas round-trip) — the minimum-rewrite
     pure-polars target

Timeframes per the MDPS canonical ladder:
  15s, 1m, 5m, 15m, 1h, 4h, 24h
"""

from __future__ import annotations

import gc
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

TIMEFRAMES_SEC = [15, 60, 300, 900, 3600, 14400, 86400]
TIMEFRAME_NAMES = ["15s", "1m", "5m", "15m", "1h", "4h", "24h"]
DAY_STR = "2026-04-15"
DAY_START_US = int(datetime.strptime(DAY_STR, "%Y-%m-%d")
                   .replace(tzinfo=timezone.utc).timestamp() * 1_000_000)
PRICE_COL = "price"
SIZE_COL = "amount"
TS_COL_NS = "local_timestamp"


def rss_mb() -> float:
    return psutil.Process().memory_info().rss / 1024 / 1024


# ---------------------------------------------------------------------------
# PATH A — pure polars (LazyFrame, scan_parquet, group_by, write_parquet)
# ---------------------------------------------------------------------------

def path_a_pure_polars(parquet_path: Path, out_dir: Path) -> dict:
    import polars as pl
    t0 = time.perf_counter()
    peak_rss = rss_mb()

    base = pl.scan_parquet(parquet_path).with_columns(
        ((pl.col(TS_COL_NS) // 1000) - DAY_START_US).alias("ts_us")
    )

    for tf_name, tf_sec in zip(TIMEFRAME_NAMES, TIMEFRAMES_SEC):
        interval_us = tf_sec * 1_000_000
        n_candles = 86400 // tf_sec
        candles = (
            base
            .with_columns((pl.col("ts_us") // interval_us).alias("interval_idx"))
            .filter((pl.col("interval_idx") >= 0)
                    & (pl.col("interval_idx") < n_candles))
            .group_by("interval_idx")
            .agg([
                pl.col(PRICE_COL).first().alias("open"),
                pl.col(PRICE_COL).max().alias("high"),
                pl.col(PRICE_COL).min().alias("low"),
                pl.col(PRICE_COL).last().alias("close"),
                pl.col(SIZE_COL).sum().alias("volume"),
            ])
            .sort("interval_idx")
            .collect()
        )
        out_path = out_dir / f"{parquet_path.stem}_{tf_name}.parquet"
        candles.write_parquet(out_path)
        peak_rss = max(peak_rss, rss_mb())
        del candles
    return {
        "wall_clock_s": time.perf_counter() - t0,
        "peak_rss_mb": peak_rss,
    }


# ---------------------------------------------------------------------------
# PATH B — pandas + pyarrow dtype_backend end-to-end
# ---------------------------------------------------------------------------

def path_b_pandas_pyarrow(parquet_path: Path, out_dir: Path) -> dict:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    t0 = time.perf_counter()
    peak_rss = rss_mb()

    df = pd.read_parquet(parquet_path, engine="pyarrow", dtype_backend="pyarrow")
    # Convert ns → us then subtract day start
    ts_us = (df[TS_COL_NS] // 1000) - DAY_START_US
    peak_rss = max(peak_rss, rss_mb())

    for tf_name, tf_sec in zip(TIMEFRAME_NAMES, TIMEFRAMES_SEC):
        interval_us = tf_sec * 1_000_000
        n_candles = 86400 // tf_sec
        interval_idx = ts_us // interval_us
        mask = (interval_idx >= 0) & (interval_idx < n_candles)
        sub = df.loc[mask].assign(_idx=interval_idx[mask])
        agg = sub.groupby("_idx", as_index=False).agg(
            open=(PRICE_COL, "first"),
            high=(PRICE_COL, "max"),
            low=(PRICE_COL, "min"),
            close=(PRICE_COL, "last"),
            volume=(SIZE_COL, "sum"),
        ).sort_values("_idx")
        out_path = out_dir / f"{parquet_path.stem}_{tf_name}.parquet"
        pq.write_table(pa.Table.from_pandas(agg, preserve_index=False),
                       str(out_path))
        peak_rss = max(peak_rss, rss_mb())
        del sub, agg
    del df, ts_us
    return {
        "wall_clock_s": time.perf_counter() - t0,
        "peak_rss_mb": peak_rss,
    }


# ---------------------------------------------------------------------------
# PATH C — current MDPS shape (polars read eager → to_pandas → from_pandas →
#                              polars group_by → polars write)
# ---------------------------------------------------------------------------

def path_c_current_mdps(parquet_path: Path, out_dir: Path) -> dict:
    import io
    import polars as pl

    t0 = time.perf_counter()
    peak_rss = rss_mb()

    # Replicate _read_tick_data exactly
    raw_bytes = parquet_path.read_bytes()
    pl_df = pl.read_parquet(io.BytesIO(raw_bytes), low_memory=True)
    pd_df = pl_df.to_pandas()
    del pl_df, raw_bytes
    peak_rss = max(peak_rss, rss_mb())

    # Now back to polars for aggregation (as _process_all_timeframes does)
    pl_df2 = pl.from_pandas(pd_df)
    del pd_df
    peak_rss = max(peak_rss, rss_mb())

    base = pl_df2.with_columns(
        ((pl.col(TS_COL_NS) // 1000) - DAY_START_US).alias("ts_us")
    )

    for tf_name, tf_sec in zip(TIMEFRAME_NAMES, TIMEFRAMES_SEC):
        interval_us = tf_sec * 1_000_000
        n_candles = 86400 // tf_sec
        candles = (
            base
            .with_columns((pl.col("ts_us") // interval_us).alias("interval_idx"))
            .filter((pl.col("interval_idx") >= 0)
                    & (pl.col("interval_idx") < n_candles))
            .group_by("interval_idx")
            .agg([
                pl.col(PRICE_COL).first().alias("open"),
                pl.col(PRICE_COL).max().alias("high"),
                pl.col(PRICE_COL).min().alias("low"),
                pl.col(PRICE_COL).last().alias("close"),
                pl.col(SIZE_COL).sum().alias("volume"),
            ])
            .sort("interval_idx")
        )
        # Mimic the second to_pandas round trip if writer needs pandas
        pd_candles = candles.to_pandas()
        out_path = out_dir / f"{parquet_path.stem}_{tf_name}.parquet"
        pd_candles.to_parquet(out_path, engine="pyarrow")
        peak_rss = max(peak_rss, rss_mb())
        del candles, pd_candles
    del pl_df2, base
    return {
        "wall_clock_s": time.perf_counter() - t0,
        "peak_rss_mb": peak_rss,
    }


# ---------------------------------------------------------------------------
# PATH D — polars eager read (no to_pandas round trip; minimum-rewrite target)
# ---------------------------------------------------------------------------

def path_d_polars_eager(parquet_path: Path, out_dir: Path) -> dict:
    import polars as pl

    t0 = time.perf_counter()
    peak_rss = rss_mb()

    df = pl.read_parquet(parquet_path, low_memory=True)
    peak_rss = max(peak_rss, rss_mb())

    base = df.with_columns(
        ((pl.col(TS_COL_NS) // 1000) - DAY_START_US).alias("ts_us")
    )

    for tf_name, tf_sec in zip(TIMEFRAME_NAMES, TIMEFRAMES_SEC):
        interval_us = tf_sec * 1_000_000
        n_candles = 86400 // tf_sec
        candles = (
            base
            .with_columns((pl.col("ts_us") // interval_us).alias("interval_idx"))
            .filter((pl.col("interval_idx") >= 0)
                    & (pl.col("interval_idx") < n_candles))
            .group_by("interval_idx")
            .agg([
                pl.col(PRICE_COL).first().alias("open"),
                pl.col(PRICE_COL).max().alias("high"),
                pl.col(PRICE_COL).min().alias("low"),
                pl.col(PRICE_COL).last().alias("close"),
                pl.col(SIZE_COL).sum().alias("volume"),
            ])
            .sort("interval_idx")
        )
        out_path = out_dir / f"{parquet_path.stem}_{tf_name}.parquet"
        candles.write_parquet(out_path)
        peak_rss = max(peak_rss, rss_mb())
        del candles
    del df, base
    return {
        "wall_clock_s": time.perf_counter() - t0,
        "peak_rss_mb": peak_rss,
    }


PATHS = {
    "A": ("pure_polars_lazy", path_a_pure_polars),
    "B": ("pandas_pyarrow", path_b_pandas_pyarrow),
    "C": ("current_mdps_mixed", path_c_current_mdps),
    "D": ("polars_eager", path_d_polars_eager),
}


def main():
    path_id = sys.argv[1]
    data_dir = Path(sys.argv[2])
    out_dir = Path(sys.argv[3])
    out_dir.mkdir(parents=True, exist_ok=True)

    if path_id not in PATHS:
        print(f"unknown path {path_id}", file=sys.stderr)
        sys.exit(2)
    label, fn = PATHS[path_id]

    parquets = sorted(data_dir.glob("*.parquet"))
    if not parquets:
        print("no parquets found", file=sys.stderr)
        sys.exit(2)

    # Pre-warm: do one read to load shared libs etc. so the first
    # measurement isn't polluted by import cost.
    warmup_dir = out_dir / "_warmup"
    warmup_dir.mkdir(parents=True, exist_ok=True)
    _ = fn(parquets[0], warmup_dir)
    gc.collect()
    rss_after_warmup = rss_mb()

    results = []
    cumulative_rss_after_each = []
    overall_t0 = time.perf_counter()

    for p in parquets:
        r = fn(p, out_dir)
        gc.collect()
        rss_after = rss_mb()
        cumulative_rss_after_each.append(rss_after)
        results.append({
            "file": p.name,
            "file_size_mb": p.stat().st_size / 1024 / 1024,
            "wall_clock_s": r["wall_clock_s"],
            "peak_rss_mb": r["peak_rss_mb"],
            "rss_after_mb": rss_after,
        })

    total_wall = time.perf_counter() - overall_t0
    final_rss = rss_mb()

    print(json.dumps({
        "path_id": path_id,
        "label": label,
        "polars": __import__("polars").__version__,
        "pandas": __import__("pandas").__version__,
        "pyarrow": __import__("pyarrow").__version__,
        "python": sys.version.split()[0],
        "pid": os.getpid(),
        "rss_after_warmup_mb": rss_after_warmup,
        "rss_final_mb": final_rss,
        "rss_retention_mb": final_rss - rss_after_warmup,
        "total_wall_s": total_wall,
        "n_instruments": len(parquets),
        "per_instrument": results,
        "cumulative_rss_after_each_mb": cumulative_rss_after_each,
    }))


if __name__ == "__main__":
    main()
