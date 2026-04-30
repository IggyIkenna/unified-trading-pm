---
title: "Manifest range index — concrete v7 layout sample"
parent: manifest_scaling_range_index_2026_05.plan.md
status: illustrative
created: 2026-04-30
---

# Manifest range index — concrete v7 layout sample

Working illustration of what a row in the proposed v7 manifest looks
like vs. today's v6, end-to-end for the symbols and timeframes in
the chart's MVP set. **Not a spec yet** — meant to make the shape
tangible so we can sanity-check it before committing.

---

## Scenario

`market-data-tick-tradfi-{project}` bucket, 2026-04-30, after
~4 months of MDPS backfill (2026-01-02 → 2026-04-15) for:

- AAPL, MSFT, GOOGL on NASDAQ
- JPM on NYSE
- Across timeframes: 1m, 5m, 15m, 1h, 4h, 24h
- `data_type=ohlcv_1m` (TRADFI's only data_type today)

NASDAQ trading days in window: ~73. Bonus example: an MSFT option
chain that listed Mar 5 and expired Apr 17, capturing the dated
behaviour.

---

## v6 today — one row per shard

Today's `_index/availability_index.parquet` for this scenario:

- AAPL: 73 days × 6 timeframes × 1 data_type = **438 rows**
- MSFT: 438 rows
- GOOGL: 438 rows
- JPM: 438 rows (different `venue` value)
- TOTAL for 4 symbols: **1,752 rows**

Sample (4 of those 1,752):

| date | service_name | venue | instrument_id | timeframe | data_type | available | instrument_count | written_at |
|---|---|---|---|---|---|---|---|---|
| 2026-04-13 | market-data-processing-service | NASDAQ | AAPL | 1m | ohlcv_1m | True | 1 | 2026-04-30T16:08Z |
| 2026-04-14 | market-data-processing-service | NASDAQ | AAPL | 1m | ohlcv_1m | True | 1 | 2026-04-30T16:08Z |
| 2026-04-13 | market-data-processing-service | NASDAQ | AAPL | 5m | ohlcv_1m | True | 1 | 2026-04-30T16:08Z |
| 2026-04-13 | market-data-processing-service | NYSE | JPM | 1m | ohlcv_1m | True | 1 | 2026-04-30T16:08Z |

(And 1,748 more rows mostly identical except date / timeframe /
instrument_id / venue.)

Read pattern in chart route today:

```python
df = read_availability_index(bucket)            # downloads ~few-MB parquet (today)
                                                 # ~hundreds-of-MB at full scale
mdps = df[
    (df["service_name"] == "market-data-processing-service")
    & (df["data_type"] == "ohlcv_1m")
    & (df["timeframe"] == "1m")
    & (df["venue"] == "NASDAQ")
    & (df["instrument_id"] == "AAPL")
    & (df["available"] == True)
]
present_dates = set(mdps["date"].astype(str).tolist())
return [d for d in requested_window if d.isoformat() in present_dates]
```

Linear pandas filter over the whole DataFrame. O(N) per call.

---

## v7 proposed — one row per coverage range

Same scenario as v6, after the range-collapsing nightly compactor
runs:

- AAPL: 6 rows (one per timeframe), each spanning 2026-01-02 → 2026-04-15
- MSFT: 6 rows
- GOOGL: 6 rows
- JPM: 6 rows
- TOTAL for 4 symbols: **24 rows** (down from 1,752 = **73× shrink**)

Sample (all 6 rows for NASDAQ:AAPL):

| service_name | venue | instrument_id | timeframe | data_type | covered_from | covered_to | gap_dates | shard_count | bytes_total | last_compacted_at |
|---|---|---|---|---|---|---|---|---|---|---|
| market-data-processing-service | NASDAQ | AAPL | 1m   | ohlcv_1m | 2026-01-02 | 2026-04-15 | [] | 73 | 12.3 MB | 2026-04-30T03:00Z |
| market-data-processing-service | NASDAQ | AAPL | 5m   | ohlcv_1m | 2026-01-02 | 2026-04-15 | [] | 73 | 2.4 MB  | 2026-04-30T03:00Z |
| market-data-processing-service | NASDAQ | AAPL | 15m  | ohlcv_1m | 2026-01-02 | 2026-04-15 | [] | 73 | 800 KB  | 2026-04-30T03:00Z |
| market-data-processing-service | NASDAQ | AAPL | 1h   | ohlcv_1m | 2026-01-02 | 2026-04-15 | [] | 73 | 200 KB  | 2026-04-30T03:00Z |
| market-data-processing-service | NASDAQ | AAPL | 4h   | ohlcv_1m | 2026-01-02 | 2026-04-15 | [] | 73 | 50 KB   | 2026-04-30T03:00Z |
| market-data-processing-service | NASDAQ | AAPL | 24h  | ohlcv_1m | 2026-01-02 | 2026-04-15 | [] | 73 | 8 KB    | 2026-04-30T03:00Z |

Note: NASDAQ trading days in `[2026-01-02, 2026-04-15]` = 73 days.
Calendar days in the same range = 104. The 31 weekends + holidays
are not in `gap_dates` because they're not trading days for
`venue=NASDAQ` per `InstrumentRecord.holiday_calendar='XNYS'`.

Read pattern post-v7:

```python
df = read_availability_index(bucket)            # downloads few-MB parquet (now flat)
                                                 # tens-of-MB at full scale (vs hundreds for v6)
match = df[
    (df["service_name"] == "market-data-processing-service")
    & (df["venue"] == "NASDAQ")
    & (df["instrument_id"] == "AAPL")
    & (df["timeframe"] == "1m")
    & (df["data_type"] == "ohlcv_1m")
]
if match.empty:
    return []
row = match.iloc[0]                              # single row — O(1) hash lookup
covered = (row["covered_from"], row["covered_to"], set(row["gap_dates"]))
return [
    d for d in requested_window
    if covered[0] <= d <= covered[1] and d.isoformat() not in covered[2]
]
```

Two cardinal differences from v6:

1. The **filter resolves to a single row** (or zero), not N. Single-
   row pandas indexing is sub-microsecond; pandas filter over millions
   of rows is hundreds of milliseconds.
2. **Holidays / weekends never enter the picture.** They're not in
   `gap_dates` because they're not in the InstrumentRecord trading
   calendar. The chart never asks for them.

---

## What a real gap looks like

Suppose MDPS crashed processing 2026-03-12 (a Thursday) for AAPL 1m
specifically — the GCS parquet for that day was never written. v6
manifest has zero rows for that (date, venue, symbol, timeframe,
data_type) tuple, indistinguishable from "MDPS hasn't run yet."

v7 captures it precisely:

| service | venue | instrument_id | tf | dt | covered_from | covered_to | gap_dates | shard_count |
|---|---|---|---|---|---|---|---|---|
| mdps | NASDAQ | AAPL | 1m | ohlcv_1m | 2026-01-02 | 2026-04-15 | **[2026-03-12]** | 72 |

`shard_count` = 72 (one less than 73), `gap_dates` carries the
specific day that failed. A monitoring view filters for
`array_length(gap_dates) > 0` to find pipeline failures.

When the AAPL 2026-03-12 shard is later backfilled, the compactor
sees the new shard and removes 2026-03-12 from `gap_dates`. The
`covered_from`/`covered_to` boundaries don't move because they
already covered that date.

---

## What an option chain looks like

MSFT option `MSFT_240417C400` listed 2026-03-05, expired 2026-04-17,
trading on NASDAQ regular hours.

v6 today: ~30 daily rows × 6 timeframes = ~180 rows, each indistinguishable
from "more might come."

v7:

| service | venue | instrument_id | tf | dt | covered_from | covered_to | gap_dates | shard_count |
|---|---|---|---|---|---|---|---|---|
| mdps | NASDAQ | MSFT_240417C400 | 1m | trades | 2026-03-05 | 2026-04-17 | [] | 30 |

The bounds `[2026-03-05, 2026-04-17]` are the option's lifecycle.
Joined with `instruments-service.InstrumentRecord` for this option:
`available_from=2026-03-05`, `available_to=2026-04-17`. **Bounds match
the lifecycle exactly** — no further coverage possible. Coverage % =
100%. (For a still-listed instrument, `available_to` is null and the
manifest's `covered_to` lags it by ingest cadence — the gap there is
real, not "missing.")

---

## What `gap_dates` is bounded by

For continuously-traded stocks across multi-year windows, `gap_dates`
should stay small (a handful per year, mostly zero). It's a list, not
a separate row-per-gap. If gaps balloon past a threshold (e.g. >30
gap dates in a single row), it indicates pipeline trouble bigger than
what a single tuple should carry — escalate to ops via an alert, don't
let the row keep growing unbounded.

Alternative shape if gaps prove problematic in practice: split into
multiple range rows per tuple when gaps exceed a threshold, e.g.

| covered_from | covered_to | gap_dates |
|---|---|---|
| 2024-01-02 | 2024-06-30 | [] |
| 2024-07-15 | 2026-04-15 | [] |

(Ingest gap from 2024-07-01 to 2024-07-14 represented as the absence
of a connecting row, not as an explicit list. Same lookup logic — the
filter just returns multiple rows and the day-set check unions them.)
Defer this decision until we've measured what real gaps look like.

---

## Index size projection

Continuing the back-of-envelope from the parent plan:

| Surface | v6 row count | v7 row count | shrink |
|---|---|---|---|
| 4 symbols × 6 tf × 73 days (this scenario) | 1,752 | 24 | **73×** |
| 10K stocks × 6 tf × 5y | ~73M | ~60K | ~1,200× |
| 3K crypto perps × 7 tf × 4 dt × 5y | ~150M | ~84K | ~1,800× |
| Options chains (per-strike) | ~500M | ~few-K (per chain bundle) | ~100K× |

A few-MB parquet, fully readable in a single `download_bytes` call,
fully filterable as a hash lookup. No paging, no fanning out, no
per-symbol files.

---

## What stays the same

- Hive partition layout in GCS (`day=YYYY-MM-DD/timeframe=…/venue=…/{symbol}.parquet`)
  — unchanged.
- `processed_candles/` parquets themselves — untouched.
- Existing consumers that don't care about per-instrument granularity
  (e.g. data-status drilldown which keys on `(date, venue, data_type)`)
  — work unchanged after v7's `_backfill()` synthesises per-day rows
  from the range on read for transition window.
- UTL `read_availability_index(bucket)` API surface — unchanged. Only
  the row schema differs.

The migration is read-compatible (old code reading new manifest sees
backfilled per-day rows for transition window) and write-compatible
(old writers can keep emitting v6 rows; the nightly compactor folds
them into v7 rows on its next run).
