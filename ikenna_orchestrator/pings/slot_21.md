# Slot 21 Pings

## [2026-06-24] BLOCKED-OPERATOR-DECISION — TradFi ES features pipeline architectural mismatch

**Plan**: `plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` P0 #2 + P0 #3
**Issue**: `plans/active/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md`

### What happened

Slot-21 was tasked with running `features-delta-one-service` for tradfi/ES. Three VM attempts all failed.
After launching the MDPS process VM `mdps-backfill-tradfi-20260624-065912` (to build the MDPS layer),
investigation of the build-continuous source code revealed the MDPS output is ARCHITECTURALLY INCOMPATIBLE
with the build-continuous pipeline. VM was killed to stop burning compute.

**Features-volatility-tradfi** is blocked by the same mismatch (slot-23 confirmed, same issue doc).

### Triple architectural mismatch (see full issue doc for code references)

1. **data_type path mismatch**: MDPS process writes `data_type=trades` in output path.
   Build-continuous reads `data_type=ohlcv_1m` (`DEFAULT_DATA_TYPES = ["ohlcv_1m"]`).
   → These paths never intersect. Zero files found.

2. **Filename format mismatch**: MDPS writes `ESH0.parquet` (bare Massive symbol).
   Build-continuous `contract_id_for_expiry()` generates `CME:FUTURE:ES-20200320` (Databento date format).
   Exact string match → all MDPS files skipped.

3. **ES absent from Databento**: ES (E-mini S&P 500) does NOT exist in `pipeline_mode=batch_databento/
   .../futures_chain/data_type=ohlcv_1m/` GCS path. Only MES (micro) is present. Build-continuous was
   designed for Databento ohlcv_1m data, but that data doesn't exist for ES.

   ES IS in Massive trades: `raw_tick_data/...pipeline_mode=batch_massive/.../futures_chain/data_type=trades/underlying=ES/ticks.parquet`

4. **Build-continuous → features-service read path mismatch**: Build-continuous writes to
   `instrument_type=continuous_future/venue=CME/underlying=ES/ticks.parquet`. Features-service
   `_build_blob_path("CME:FUTURES:ES")` builds `data_type=ohlcv_1m/venue=CME/CME:FUTURES:ES.parquet`.
   No `continuous_future` handling in features-service `_DERIVATIVE_DATA_TYPES`.

### Decision required

**Option A (RECOMMENDED — fast, ~1-2 days to unblock)**:
Add a `TradfiDirectDataLoader` in features-delta-one-service that reads the Massive raw chain bundle
directly from MTDS bucket, applies Panama-canal roll adjustment inline (reuse or extract `panama_core.py`
to UAC/UTL), and produces the same output feature parquets. Bypasses MDPS + build-continuous entirely
for ES. The `panama_core.py` logic (expiry calendar, roll schedule, back-adjustment math) exists in MDPS
and would need to be extracted to a shared lib (UTL or UAC), OR the computation done inline.

**Option B (architecturally complete — ~3-5 days)**:
Fix MDPS process step to: (a) translate `data_type=trades` → `data_type=ohlcv_1m` in output path
for Massive tradfi bundles, (b) use Databento date-format IDs `CME:FUTURE:ES-20200320` in filenames
(or change panama_core to use short symbols matching MDPS output).
Then fix features-service `_build_blob_path` to support `CME:CONTINUOUS_FUTURE:ES` (continuous_future type).
Then run MDPS process (1642 days) → build-continuous → features.

### Your `[ack]`

Please respond in this file or in the plan with one of:
- `[ack: option-a]` — proceed with Option A (direct MTDS read in features-service)
- `[ack: option-b]` — proceed with Option B (fix MDPS + build-continuous + features-service)
- `[ack: option-b-variant]` — proceed with cleaner B variant: change panama_core short symbols +
   translate data_type in MDPS + fix features-service `_build_blob_path`

Once acked, slot-21 will immediately start the fix.
