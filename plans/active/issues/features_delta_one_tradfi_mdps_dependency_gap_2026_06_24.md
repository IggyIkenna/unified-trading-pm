---
doc_type: issue
title: "features-delta-one-tradfi: MDPS processed-candle dependency gap + architectural pipeline mismatch"
summary:
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service, market-data-processing-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-24
parent_epic:
priority: P0
source: [tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md]
assigned_vm:
resolved_by:
locked_by: live-defi-rollout
---

## What I found

Three VM runs of `features-delta-one-tradfi` all failed — the third bypassed the preflight dependency check
(`SKIP_DEPENDENCY_CHECK=1`) but still failed during computation with:

```
WARNING: No upstream MDPS data for CME:FUTURES:ES on 2024-12-30 (data_type=trades) — skipping date
ERROR: FAILED feature group: technical_indicators
... (all 34 feature groups fail similarly)
```

**Root cause 1 — MDPS processed-candle layer does not exist for tradfi:** The features-delta-one-service reads MDPS
(market-data-processing) candle data that is produced by aggregating raw MTDS tick data (typically `trades` data_type).
For CeFi (crypto), MTDS captures `trades` data → MDPS aggregates into OHLCV candles → features reads those candles. For
TradFi, MTDS captures `ohlcv_1s` and `ohlcv_1m` directly from Databento — there is NO `trades` data_type. Either:

- (a) The features-service needs a tradfi-specific read path that reads ohlcv_1s/1m directly, bypassing the MDPS
  trades→candle aggregation step, OR
- (b) An MDPS run is required to translate tradfi MTDS ohlcv data into the format features-service expects.

The MTDS manifest for tradfi has 8,997 captured rows for ES (2020-01-01 → 2026-06-22) with ohlcv_1s and ohlcv_1m
data_types. But features-service can't read these directly.

**Root cause 2 — dependency_checker.py: MTDS manifest stores `instrument_id=''` (blank) for CME futures:** In
`features_service/delta_one/app/core/dependency_checker.py`:

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

The `instrument_id` column is blank for all CME rows. This explains why the preflight lookback check always reports
0/2964 candles for `CME:FUTURES:ES`.

## features-volatility-tradfi: same MDPS gap CONFIRMED (slot-23, 2026-06-24)

`features_service/volatility/core/data_loader.py` line 51–55:

```python
# Processed-candle data_types the volatility features actually READ from MDPS.
_VOLATILITY_CANDLE_DATA_TYPES: tuple[str, ...] = ("futures_chain", "options_chain")
```

`VolatilityDataLoader` reads `futures_chain` + `options_chain` from the TRADFI market-data-tick bucket (same MDPS
processed-candle format). Neither data_type is captured in `market-data-tick-tradfi-prd-*` (only `ohlcv_1s`, `ohlcv_1m`,
`ohlcv_15m` exist there). **Every volatility feature group (futures_basis, futures_term_structure, options_iv,
options_term_structure) will fail with 0 rows just like delta-one.** The VM launch for volatility is blocked until the
MDPS gap is resolved.

## MDPS process VM killed — architectural mismatch diagnosed (slot-21, 2026-06-24)

The MDPS process VM `mdps-backfill-tradfi-20260624-065912` was running (launched 2026-06-24 ~06:49 UTC) but was killed
after architectural investigation confirmed it would NEVER produce output compatible with the downstream pipeline.
Three-layer format mismatch discovered:

### Mismatch 1 — data_type in output path

| Layer                   | data_type in path                    | Expected by next layer                                     |
| ----------------------- | ------------------------------------ | ---------------------------------------------------------- |
| Massive MTDS raw        | `data_type=trades`                   | —                                                          |
| MDPS process output     | `data_type=trades` (preserves input) | `data_type=ohlcv_1m` (build-continuous DEFAULT_DATA_TYPES) |
| Build-continuous output | `data_type=ohlcv_1m` (output)        | `data_type=ohlcv_1m` (features-service \_build_blob_path)  |

**MDPS writes `data_type=trades` in the output `processed_candles/` path. Build-continuous reads `data_type=ohlcv_1m`.
These do not match** — build-continuous would find zero files.

### Mismatch 2 — per-contract filename format

| Layer                        | Filename format              | Expected by next layer                              |
| ---------------------------- | ---------------------------- | --------------------------------------------------- |
| MDPS process (old)           | `ESH0.parquet` (bare symbol) | `CME:FUTURE:ES-20200320.parquet` (build-continuous) |
| MDPS process (new canonical) | `CME:FUTURES:ESH0.parquet`   | `CME:FUTURE:ES-20200320.parquet` (build-continuous) |

**build-continuous engine** (`panama_core.contract_id_for_expiry`) returns IDs in Databento date format
`CME:FUTURE:ES-20200320`. `_load_per_contract_candles_for_day` does exact filename matching:

```python
contract_id = leaf.rsplit(".parquet", 1)[0]  # e.g. "ESH0" from "ESH0.parquet"
if contract_id not in contract_ids:           # contract_ids = {"CME:FUTURE:ES-20200320", ...}
    continue                                   # ESH0 never matches → all files skipped
```

Neither `ESH0` (old format) nor `CME:FUTURES:ESH0` (canonical format) matches `CME:FUTURE:ES-20200320`.

### Mismatch 3 — ES does NOT exist in Databento ohlcv_1m raw data

The Databento GLBX dataset raw MTDS data for `futures_chain/data_type=ohlcv_1m/` includes MES, NQ, GC, CL, etc. **but
NOT ES (E-mini S&P 500)**. Verified in GCS:

- `raw_tick_data/.../pipeline_mode=batch_databento/.../futures_chain/data_type=ohlcv_1m/underlying=MES/` ✓
- `raw_tick_data/.../pipeline_mode=batch_databento/.../futures_chain/data_type=ohlcv_1m/underlying=ES/` ✗

Even if MDPS were rewritten to produce the right format from Databento ohlcv_1m data, there is NO ES data to process
from Databento.

### Mismatch 4 — build-continuous output vs features-service read path

Build-continuous writes to:

```
processed_candles/.../instrument_type=continuous_future/venue=CME/underlying=ES/ticks.parquet
```

Features-service `_build_blob_path("CME:FUTURES:ES", data_type="ohlcv_1m")` builds:

```
processed_candles/.../data_type=ohlcv_1m/venue=CME/CME:FUTURES:ES.parquet
```

These are completely different paths. Features-service has no `continuous_future` handling in `_build_blob_path` —
`_DERIVATIVE_DATA_TYPES = {"options_chain", "futures_chain"}` does NOT include `continuous_future`. No
`CME:CONTINUOUS_FUTURE:ES` or similar instrument_id handling found.

## Why it matters

- **Blocks**: All TradFi features-delta-one runs AND features-volatility-tradfi until resolved.
- **Blocks**: S&P ML training + backtest (no feature parquets = no training).
- **Blocks the MDPS path entirely**: The MDPS process → build-continuous → features pipeline has never worked for ES
  tradfi and cannot work in its current form. Fix A/B/C shipped in features-service (features-service@259569d9) make
  features fallback to `data_type=ohlcv_1m` but that still reads from `processed_candles/` MDPS layer which doesn't have
  the right data.
- **MDPS process VM killed** (`mdps-backfill-tradfi-20260624-065912`) to stop burning compute.

## Data that DOES exist

Massive ES trades chain bundle IS captured in MTDS:

```
raw_tick_data/by_date/day=2024-01-02/pipeline_mode=batch_massive/asset_group=tradfi/venue=CME/
  instrument_type=futures_chain/data_type=trades/underlying=ES/ticks.parquet
```

This is the actual ES OHLCV data (from Massive) stored as a trades chain bundle. 920 days of processed_candles from the
prior 2026-05-12 MDPS run exist but in incompatible old format (`ESH0.parquet`).

## Recommended decision — OPERATOR DECISION REQUIRED

**Option A (Recommended — fast, unblocks ES features within 1-2 days)**: Add a direct raw MTDS read path in
features-delta-one-service that bypasses MDPS entirely. When `asset_group=tradfi`, instead of reading from
`processed_candles/`, read directly from the Massive raw chain bundle:

```
raw_tick_data/.../pipeline_mode=batch_massive/.../instrument_type=futures_chain/data_type=trades/underlying=ES/ticks.parquet
```

Then apply Panama-canal roll adjustment inline in features-service (reuse `panama_core.py` or a shared UTL/UAC helper).
This is architecturally sound: the batch=live rule is maintained, the roll adjustment is already implemented in
panama_core.py, and features-service gets real historical ES data.

**Implications of Option A**:

- Adds a `TradfiDirectDataLoader` in features-service that reads from MTDS raw bucket
- Requires importing/calling `apply_panama_canal_backadjust` — but MDPS is a service, not a library, so panama_core.py
  logic must be extracted to UAC or UTL (or duplicated — not recommended)
- Alternatively: make build-continuous run FIRST as a pre-step to features, but fix the format mismatches (see Option B)

**Option B (Correct long-term — fixes the architecture, ~3-5 days)**:

1. Fix MDPS process step: translate `data_type=trades` → `data_type=ohlcv_1m` in output path when processing Massive
   trades chain bundles for TradFi
2. Fix MDPS process step: use `CME:FUTURE:ES-20200320` Databento date-format IDs (not bare symbols) in output filenames,
   OR fix panama_core to use short-symbol IDs that match what MDPS actually writes
3. Run MDPS process VM for ES trades (1642 days) — with fix, would write correct `data_type=ohlcv_1m` +
   `CME:FUTURE:ES-20200320.parquet` files
4. Run build-continuous → produces `instrument_type=continuous_future/underlying=ES/ticks.parquet`
5. Fix features-service `_build_blob_path` to support `CME:CONTINUOUS_FUTURE:ES` as instrument_id (adding
   `continuous_future` to `_DERIVATIVE_DATA_TYPES`) so it reads the build-continuous output

**Scope**: Option B requires coordinated changes to MDPS (process step data_type translation + filename format) +
features-service (`_build_blob_path` continuous_future handling). panama_core.py's `contract_id_for_expiry` date-format
vs MDPS's short-symbol filenames is the core incompatibility.

**Cleaner Option B variant**: Change panama_core's `contract_id_for_expiry` to return short symbols (`ESH24` style =
root + month_letter + year2) that match what MDPS actually writes after canonicalization, AND fix the `data_type`
translation in MDPS. This avoids changing filename formats.

## VMs attempted

| VM                                        | Exit   | Notes                                                                                             |
| ----------------------------------------- | ------ | ------------------------------------------------------------------------------------------------- |
| features-delta-one-tradfi-20260624-055637 | rc=1   | `--instruments ES` rejected: "Malformed instrument_id"                                            |
| features-delta-one-tradfi-20260624-061207 | rc=1   | `CME:FUTURES:ES: 0/2964 candles` (blank inst_id bug)                                              |
| features-delta-one-tradfi-20260624-061841 | rc=1   | Passed preflight (`SKIP_DEPENDENCY_CHECK=1`) but all feature groups fail: "No upstream MDPS data" |
| mdps-backfill-tradfi-20260624-065912      | KILLED | MDPS process VM killed 2026-06-24 (incompatible output format)                                    |

## Links

- Parent plan: `plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`
- dependency_checker.py: `features-service/features_service/delta_one/app/core/dependency_checker.py:628-656`
- MTDS tradfi manifest: `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`
- Build-continuous engine:
  `market-data-processing-service/market_data_processing_service/engine/build_continuous_engine.py`
- panama_core contract_id: `market_data_processing_service/engine/panama_core.py:101-103`
- MDPS output path helpers: `market_data_processing_service/app/core/output_path_helpers.py`
- MDPS output uses data_type as-is: `candle_write_mixin.py:233`
