---
title: "features-delta-one-tradfi: MDPS processed-candle dependency gap + dependency_checker instrument_id key mismatch"
created: 2026-06-24
source:
  - tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

Three VM runs of `features-delta-one-tradfi` all failed — the third bypassed the preflight dependency check
(`SKIP_DEPENDENCY_CHECK=1`) but still failed during computation with:

```
WARNING: No upstream MDPS data for CME:FUTURES:ES on 2024-12-30 (data_type=trades) — skipping date
ERROR: Failed processing technical_indicators for date 2025-01-01 00:00:00+00:00
ERROR: FAILED feature group: technical_indicators
... (all 34 feature groups fail similarly)
```

**Root cause 1 — MDPS processed-candle layer does not exist for tradfi:**
The features-delta-one-service reads MDPS (market-data-processing) candle data that is produced by aggregating
raw MTDS tick data (typically `trades` data_type). For CeFi (crypto), MTDS captures `trades` data → MDPS
aggregates into OHLCV candles → features reads those candles. For TradFi, MTDS captures `ohlcv_1s` and
`ohlcv_1m` directly from Databento — there is NO `trades` data_type. Either:
- (a) The features-service needs a tradfi-specific read path that reads ohlcv_1s/1m directly, bypassing
  the MDPS trades→candle aggregation step, OR
- (b) An MDPS run is required to translate tradfi MTDS ohlcv data into the format features-service expects.

The MTDS manifest for tradfi has 8,997 captured rows for ES (2020-01-01 → 2026-06-22) with ohlcv_1s and
ohlcv_1m data_types. But features-service can't read these directly.

**Root cause 2 — dependency_checker.py: MTDS manifest stores `instrument_id=''` (blank) for CME futures:**
In `features_service/delta_one/app/core/dependency_checker.py`:
- `_build_captured_index` (line 594) stores manifest rows as `(rec["venue"], rec["instrument_id"])` keys.
- `_count_candles_for_lookback` (line 645) looks up `captured_index.get(("CME", "ES"), set())`.
- BUT the MTDS manifest stores `instrument_id=''` (empty string) for all CME futures rows.
- So the stored key is `("CME", "")` but the lookup is `("CME", "ES")` → always 0 candles.

Verified by sampling `market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`:
```
venue instrument_id data_type  capture_status  date
CME                ohlcv_1s    captured        2020-12-23
CME                ohlcv_1s    captured        2025-12-15
```
The `instrument_id` column is blank for all CME rows. This explains why the preflight lookback check
always reports 0/2964 candles for `CME:FUTURES:ES`.

## features-volatility-tradfi: same MDPS gap CONFIRMED (slot-23, 2026-06-24)

`features_service/volatility/core/data_loader.py` line 51–55:
```python
# Processed-candle data_types the volatility features actually READ from MDPS.
_VOLATILITY_CANDLE_DATA_TYPES: tuple[str, ...] = ("futures_chain", "options_chain")
```
`VolatilityDataLoader` reads `futures_chain` + `options_chain` from the TRADFI market-data-tick bucket
(same MDPS processed-candle format). Neither data_type is captured in `market-data-tick-tradfi-prd-*`
(only `ohlcv_1s`, `ohlcv_1m`, `ohlcv_15m` exist there). **Every volatility feature group
(futures_basis, futures_term_structure, options_iv, options_term_structure) will fail with 0 rows
just like delta-one.** The VM launch for volatility is blocked until the MDPS gap is resolved.

## Why it matters

- **Blocks**: All TradFi features-delta-one runs AND features-volatility-tradfi until resolved.
- **Blocks**: S&P ML training + backtest (no feature parquets = no training).
- **Scope**: The dependency_checker blank-instrument_id bug affects ALL tradfi instruments (ES, NQ, YM, etc),
  not just ES. Every tradfi features run will silently fail lookback validation.

## Recommended decision

**P0 investigation (operator decision needed on approach):**
Option A: Add a tradfi-specific OHLCV read path in features-delta-one-service that reads ohlcv_1s/1m
  directly from MTDS bucket without an MDPS intermediate step. This requires mapping feature-service data
  consumption to MTDS's ohlcv data_types instead of MDPS's trade-aggregated candles.
Option B: Run an MDPS aggregation pass for tradfi that converts ohlcv_1s → multi-timeframe candles in the
  format features-service expects. This is more architecturally consistent but adds a pipeline step.

**P1 fix (clear, fix it):**
The `dependency_checker.py` blank instrument_id bug. Fix `_count_candles_for_lookback` to handle the case
where the manifest stores blank instrument_ids for a venue — fall back to checking if ANY captured row for
that venue+date exists (date-level check when per-instrument is unavailable), or fix MTDS to write the
instrument_id into its manifest rows for tradfi.

## VMs attempted

| VM | Exit | Notes |
|----|------|-------|
| features-delta-one-tradfi-20260624-055637 | rc=1 | `--instruments ES` rejected: "Malformed instrument_id" |
| features-delta-one-tradfi-20260624-061207 | rc=1 | `CME:FUTURES:ES: 0/2964 candles` (blank inst_id bug) |
| features-delta-one-tradfi-20260624-061841 | rc=1 | Passed preflight (`SKIP_DEPENDENCY_CHECK=1`) but all feature groups fail: "No upstream MDPS data" |

## Links

- Parent plan: `plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` (line 54)
- dependency_checker.py: `features-service/features_service/delta_one/app/core/dependency_checker.py:628-656`
- MTDS tradfi manifest: `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`
