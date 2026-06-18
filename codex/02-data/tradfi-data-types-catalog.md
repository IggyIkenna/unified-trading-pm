---
scope: [engineer, admin]
status: canonical
last_reviewed: 2026-05-24
---

# TradFi Data Types Catalog

> SSOT for all MTDS TradFi data type definitions, sources, shard keys, and implementation status. Last updated:
> 2026-05-24.

## Overview

MTDS collects TradFi market data in 9 distinct data types across market data, reference data, and macro domains. Each
data type maps to one MTDS CLI operation (`--operation collect-<type>`), one or more venues, and a canonical GCS path
under the TradFi tick-data bucket.

`trades` and `tbbo` are **DEFERRED to post-cutover** — OHLCV-only MVP per operator direction 2026-05-15 (see
`plans/active/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md`). `mbp_10` is also deferred (L2 order book). All three are
suppressed at the orchestrator level via `TRADFI_TICK_DATA_WINDOWS = []` in UAC
`unified_api_contracts/registry/market_data_categories.py`.

The instrument_type axis for TradFi has four values: `equity`, `futures_chain`, `options_chain`, `index`.

### GCS Path Convention

**Canonical** (per CLAUDE.md § "Asset-group vocabulary"; `asset_group=` hive key per
`market_tick_data_service/raw_tick_hive.RAW_TICK_ASSET_GROUP_HIVE_KEY`):

```
{resolved-tradfi-tick-bucket}/raw_tick_data/by_date/day={date}/asset_group=tradfi/
  venue={VENUE}/instrument_type={type}/data_type={data_type}/ticks.parquet
```

Bucket name is resolved via
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud=..., kind="market-data-tick", asset_group="tradfi", env=...)`
per CLAUDE.md § "Bucket-name SSOT" — never inline `gs://...` / `s3://...` (QG STEP 5.69 ratchet enforces).

Expected dates use trading days only: `VenueMapping.get_expected_trading_dates(venue, start, end)` — weekends and
exchange-specific holidays are excluded.

### Instrument Type Mapping

| instrument_type  | Data types                                   |
| ---------------- | -------------------------------------------- |
| `equity`         | ohlcv_1m, trades (deferred), tbbo (deferred) |
| `futures_chain`  | ohlcv_1m, trades (deferred), tbbo (deferred) |
| `options_chain`  | ohlcv_15m (CBOE index only)                  |
| `index`          | ohlcv_24h (FX G10), macro_result             |
| (reference data) | corporate_action_confirmed, earnings_result  |

---

## Data Type Catalog

### 1. ohlcv_1m

| Field               | Value                                                                                                         |
| ------------------- | ------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-ohlcv-1m` (tradfi_ohlcv_handler)                                                                     |
| **Sources**         | Databento (market data provider)                                                                              |
| **Shard key**       | venue × instrument_id × date                                                                                  |
| **Instrument type** | `equity`, `futures_chain`                                                                                     |
| **Status**          | Production (Databento floor 2023-04-15 for NASDAQ/NYSE; backdated to 2019-01-01 for CME/ICE per operator ask) |
| **Schema fields**   | symbol, ts_event, venue, open, high, low, close, volume                                                       |
| **Venues**          | NASDAQ, NYSE, CME, ICE                                                                                        |
| **Requires**        | `databento-api-key` (Secret Manager)                                                                          |

Pre-aggregated 1-minute OHLCV bars. One row per (symbol, minute) per trading day. Databento delivers bars directly — no
tick aggregation on our side. CME and ICE are backdated to 2019-01-01 per operator full-period ask; NASDAQ and NYSE
floor at 2023-04-15 (Databento subscription start date).

> **OHLCV fetch = 1m AND 1s (operator 2026-06-18 subscription cutover).** Both `ohlcv-1m` and `ohlcv-1s` are L0/free
> (16-year included history). We fetch BOTH (1m completes the existing corpus; 1s is the finer-grained add) and
> aggregate the coarser bars (`ohlcv_15m` / `ohlcv_24h`) downstream — so `ohlcv-1h` / `ohlcv-1d` are NOT fetched (they
> raise via `assert_schema_allowed`). SSOT: `codex/02-data/tradfi-databento-sourcing-ssot.md` +
> `registry/databento_subscription_allowlist.py`.

---

### 1b. ohlcv_1s

| Field               | Value                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| **CLI operation**   | `collect-ohlcv-1s` (tradfi_ohlcv_handler)                                                              |
| **Sources**         | Databento (market data provider)                                                                       |
| **Shard key**       | venue × instrument_id × date                                                                           |
| **Instrument type** | `equity`, `futures_chain`                                                                              |
| **Status**          | Production (operator 2026-06-18 cutover — additive alongside `ohlcv_1m`; L0/free 16y included history) |
| **Schema fields**   | symbol, ts_event, venue, open, high, low, close, volume                                                |
| **Venues**          | NASDAQ, NYSE, CME, CFE (VX futures)                                                                    |
| **Requires**        | `databento-api-key` (Secret Manager)                                                                   |

Pre-aggregated 1-second OHLCV bars — the finer-grained OHLCV granularity added in the 2026-06-18 subscription cutover.
Databento delivers bars directly (Schema `OHLCV_1S`). Both 1s and 1m are L0/free (16y); 15m/24h are aggregated
downstream from the 1m base. Off-allowlist OHLCV schemas (`ohlcv-1h` / `ohlcv-1d`) raise via `assert_schema_allowed`
(derived, never fetched).

---

### 2. ohlcv_15m

| Field               | Value                                                   |
| ------------------- | ------------------------------------------------------- |
| **CLI operation**   | `collect-ohlcv-15m` (tradfi_ohlcv_handler)              |
| **Sources**         | Databento                                               |
| **Shard key**       | venue × instrument_id × date                            |
| **Instrument type** | `options_chain`, `index`                                |
| **Status**          | Production (CBOE limited subscription)                  |
| **Schema fields**   | symbol, ts_event, venue, open, high, low, close, volume |
| **Venues**          | CBOE                                                    |
| **Requires**        | `databento-api-key` (Secret Manager)                    |

Pre-aggregated 15-minute OHLCV bars. Used for CBOE options index instruments (VIX-family). One row per (symbol,
15-minute interval) per trading day. CBOE subscription is limited — universe is restricted to the options index
instruments provisioned under the current subscription tier.

---

### 3. ohlcv_24h

| Field               | Value                                                                                                                                                                |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-ohlcv-24h` (tradfi_ohlcv_handler)                                                                                                                           |
| **Sources**         | FRED (Federal Reserve Economic Data), Yahoo Finance via `yfinance`, Barchart preload for VIX 15m                                                                     |
| **Shard key**       | venue × pair × date                                                                                                                                                  |
| **Instrument type** | `index`                                                                                                                                                              |
| **Status**          | Production (FX: daily-only per cost envelope; VIX: Barchart preload + Yahoo rolling 60d + honest gap per UAC `registry/data_source_continuity.py`)                   |
| **Schema fields**   | symbol, ts_event, venue, open, high, low, close, volume                                                                                                              |
| **Venues**          | FX (G10 crosses: EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD, USD/CHF, NZD/USD, EUR/GBP, EUR/JPY, USD/MXN), BARCHART (VIX), YAHOO_FINANCE (VIX rolling 60d fallback) |

Daily-resolution OHLCV. FX covers G10 currency pairs at daily granularity — tick data is not collected for FX (cost
envelope constraint). VIX uses Barchart preload for the historical series combined with Yahoo Finance rolling 60d
window; honest gap handling is enforced via UAC `registry/data_source_continuity.py` constants — gaps are
`empty_confirmed[reason=EXPECTED_SOURCE_GAP]`, not silently dropped.

---

### 4. tbbo

| Field               | Value                                                                                                                                                                                                                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-tbbo` (tradfi_tbbo_handler) — DEFERRED                                                                                                                                                                                                                                              |
| **Sources**         | Databento (L1 tick data)                                                                                                                                                                                                                                                                     |
| **Shard key**       | venue × instrument_id × date                                                                                                                                                                                                                                                                 |
| **Instrument type** | `equity`, `futures_chain`                                                                                                                                                                                                                                                                    |
| **Status**          | **DEFERRED** — post-cutover (`tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md`). `TRADFI_TICK_DATA_WINDOWS = []` in UAC suppresses all fetch attempts. `is_in_tradfi_tick_window()` returns False for every date. Historical windows preserved in `_DEFERRED_TRADFI_TICK_DATA_WINDOWS`. |
| **Schema fields**   | symbol, ts_event, venue, bid_px, ask_px, bid_sz, ask_sz                                                                                                                                                                                                                                      |
| **Venues**          | CME (post-cutover), NASDAQ (post-cutover), NYSE (post-cutover)                                                                                                                                                                                                                               |
| **Requires**        | `databento-api-key` (Secret Manager)                                                                                                                                                                                                                                                         |

Top-of-book best bid/offer tick data (L1). One row per quote update. Deferred to post-cutover — OHLCV-only MVP per
operator direction 2026-05-15. Suppression is at the MTDS orchestrator level; the handler scaffold exists but is never
invoked while `TRADFI_TICK_DATA_WINDOWS = []`.

---

### 5. trades

| Field               | Value                                                                                                     |
| ------------------- | --------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-trades` (tradfi_trades_handler) — DEFERRED                                                       |
| **Sources**         | Databento (L1 tick data)                                                                                  |
| **Shard key**       | venue × instrument_id × date                                                                              |
| **Instrument type** | `equity`, `futures_chain`, `options_chain`                                                                |
| **Status**          | **DEFERRED** — same suppression as `tbbo`. `TRADFI_TICK_DATA_WINDOWS = []` in UAC suppresses all fetches. |
| **Schema fields**   | symbol, ts_event, venue, price, size, side, trade_id                                                      |
| **Venues**          | NASDAQ (post-cutover), NYSE (post-cutover), CME (post-cutover)                                            |
| **Requires**        | `databento-api-key` (Secret Manager)                                                                      |

Tick-by-tick trade executions. One row per executed trade. Deferred to post-cutover — operationally, existing manifest
rows for `trades` (if any) are re-classified by the Phase 5 phantom-reconcile pass before restoration.

---

### 6. mbp_10

| Field               | Value                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-mbp-10` (tradfi_mbp_handler) — DEFERRED                                                               |
| **Sources**         | Databento (L2/MBP data)                                                                                        |
| **Shard key**       | venue × instrument_id × date                                                                                   |
| **Instrument type** | `equity`, `futures_chain`                                                                                      |
| **Status**          | **DEFERRED** — post-cutover. Historical CME windows preserved in `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS`. |
| **Schema fields**   | symbol, ts_event, venue, bid_px_00..09, ask_px_00..09, bid_sz_00..09, ask_sz_00..09 (10 levels each side)      |
| **Venues**          | CME (post-cutover)                                                                                             |
| **Requires**        | `databento-api-key` (Secret Manager)                                                                           |

10-level market-by-price order book (L2). Full depth-of-book snapshot at each update — 20 bid columns + 20 ask columns
(price + size per level). The schema expands to 40 price/size columns at write time. Deferred to post-cutover;
historical CME reference windows are preserved in `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` (dict-shape mirroring
`VENUE_DATA_TYPE_COVERAGE_WINDOWS`) for restoration when the post-cutover plan executes.

---

### 7. corporate_action_confirmed

| Field               | Value                                                                                                                      |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-corporate-actions` (corporate_action_handler)                                                                     |
| **Sources**         | Polygon.io corporate actions API (`api.polygon.io/v3/reference/dividends`, `/splits`)                                      |
| **Shard key**       | venue × date (one shard per exchange per day)                                                                              |
| **Instrument type** | `equity`                                                                                                                   |
| **Status**          | Production (reference data; daily batch)                                                                                   |
| **Schema fields**   | symbol, ts_event, venue, action_type, ex_date, record_date, pay_date, ratio, from_factor, to_factor, cash_amount, currency |
| **Venues**          | NASDAQ, NYSE, ICE                                                                                                          |
| **Requires**        | `polygon-api-key` (Secret Manager)                                                                                         |

Confirmed corporate actions — stock splits, reverse splits, cash dividends, spin-offs. `action_type` is a closed set:
`split`, `dividend`, `spinoff`. `ex_date` is the ex-dividend / ex-split date (the day the action takes effect on price).
Days with no corporate actions are recorded as `empty_confirmed[reason=SOURCE_RETURNED_ZERO]`. Used by execution-service
for price adjustment and by instruments-service for continuous contract construction.

---

### 8. earnings_result

| Field               | Value                                                                                                                                                    |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-earnings` (earnings_result_handler)                                                                                                             |
| **Sources**         | Polygon.io earnings API (`api.polygon.io/vX/reference/financials`)                                                                                       |
| **Shard key**       | venue × date (one shard per exchange per reporting date)                                                                                                 |
| **Instrument type** | `equity`                                                                                                                                                 |
| **Status**          | Production (reference data; daily batch — events fire on reporting dates)                                                                                |
| **Schema fields**   | symbol, ts_event, venue, period, eps_actual, eps_estimate, eps_surprise, revenue_actual, revenue_estimate, revenue_surprise, fiscal_quarter, fiscal_year |
| **Venues**          | NASDAQ, NYSE                                                                                                                                             |
| **Requires**        | `polygon-api-key` (Secret Manager)                                                                                                                       |

Quarterly earnings results. One row per company per earnings release. `eps_surprise` = actual − estimate (raw delta);
`revenue_surprise` = same. Non-reporting days (the vast majority of trading days) are recorded as
`empty_confirmed[reason=SOURCE_RETURNED_ZERO]`. Used by features-service for earnings-event momentum signals and by
execution-service for pre-trade risk checks around earnings windows.

---

### 9. macro_result

| Field               | Value                                                                                                                            |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-macro` (macro_result_handler)                                                                                           |
| **Sources**         | FRED REST API (`fred.stlouisfed.org/docs/api/fred/`); series IDs registered in UAC `registry/capability_declarations/_tradfi.py` |
| **Shard key**       | venue (`FRED`) × date (release date)                                                                                             |
| **Instrument type** | `index`                                                                                                                          |
| **Status**          | Production (reference data; daily batch — events fire on FRED release calendar)                                                  |
| **Schema fields**   | symbol, ts_event, venue, series_id, value, period, revision_flag                                                                 |
| **Venues**          | FRED                                                                                                                             |
| **Requires**        | `fred-api-key` (Secret Manager) or public FRED API (rate-limited)                                                                |

Macro data releases — CPI, PCE, NFP, Fed Funds rate decisions, GDP, PMI. One row per FRED series per release date.
`revision_flag=True` for data revisions to prior periods. `symbol` = FRED series ID (e.g., `CPIAUCSL`, `UNRATE`,
`FEDFUNDS`). Non-release days are recorded as `empty_confirmed[reason=SOURCE_RETURNED_ZERO]`. Used by features-service
for macro-regime signals and by strategy-service for rate-sensitivity modelling. The full series ID registry is in UAC
`registry/capability_declarations/_tradfi.py` — add new series there, not inline in the handler.

---

## Venue Coverage Matrix

| venue   | MVP data_types                              | status     | notes                                                                               |
| ------- | ------------------------------------------- | ---------- | ----------------------------------------------------------------------------------- |
| CBOE    | ohlcv_15m                                   | Production | Options index only (limited Databento subscription)                                 |
| CME     | ohlcv_1m                                    | Production | Backdated to 2019-01-01; tbbo + mbp_10 post-cutover                                 |
| FX      | ohlcv_24h                                   | Production | Daily only (cost envelope); G10 crosses via FRED + Yahoo Finance                    |
| ICE     | ohlcv_1m                                    | Production | Backdated to 2019-01-01                                                             |
| NASDAQ  | ohlcv_1m                                    | Production | Equity venue; Databento floor 2023-04-15; trades post-cutover                       |
| NYSE    | ohlcv_1m                                    | Production | Equity venue; Databento floor 2023-04-15; trades post-cutover                       |
| FRED    | macro_result                                | Production | All FRED series IDs registered in UAC `registry/capability_declarations/_tradfi.py` |
| POLYGON | corporate_action_confirmed, earnings_result | Production | Reference data APIs; `polygon-api-key` required                                     |

---

## Coverage Axes

| data_type                    | Coverage axis                            | Expected shards (per trading day)    | `record_empty` expected                                        |
| ---------------------------- | ---------------------------------------- | ------------------------------------ | -------------------------------------------------------------- |
| `ohlcv_1m`                   | per-venue × per-instrument × daily       | venues × active equities / contracts | Yes — halted instruments = `empty_confirmed`                   |
| `ohlcv_15m`                  | per-venue × per-instrument × daily       | CBOE × options index instruments     | Yes                                                            |
| `ohlcv_24h`                  | per-venue × per-pair × daily             | FX × G10 crosses                     | Yes                                                            |
| `tbbo`                       | DEFERRED — post-cutover                  | n/a (suppressed via empty windows)   | n/a — fetch suppressed entirely                                |
| `trades`                     | DEFERRED — post-cutover                  | n/a (suppressed via empty windows)   | n/a — existing rows re-classified by Phase 5 phantom-reconcile |
| `mbp_10`                     | DEFERRED — post-cutover                  | n/a (suppressed via empty windows)   | n/a — historical CME windows preserved in deferred constant    |
| `corporate_action_confirmed` | per-venue × daily (events-only)          | venues × action dates                | Yes — no-action days = `empty_confirmed`                       |
| `earnings_result`            | per-venue × daily (events-only)          | venues × reporting dates             | Yes — no-reporting days = `empty_confirmed`                    |
| `macro_result`               | per-venue (`FRED`) × daily (events-only) | series × FRED release calendar       | Yes — non-release days = `empty_confirmed`                     |

---

## Implementation Notes

### API Key Requirements

| Secret Manager key  | Data types                                                                             |
| ------------------- | -------------------------------------------------------------------------------------- |
| `databento-api-key` | ohlcv_1m, ohlcv_15m, tbbo (deferred), trades (deferred), mbp_10 (deferred)             |
| `polygon-api-key`   | corporate_action_confirmed, earnings_result                                            |
| `fred-api-key`      | macro_result (public FRED API available but rate-limited; Secret Manager key for prod) |

### Deferred Tick Data — How Suppression Works

`TRADFI_TICK_DATA_WINDOWS = []` in UAC `registry/market_data_categories.py`. The MTDS orchestrator calls
`is_in_tradfi_tick_window(venue, data_type, date)` before dispatching any `tbbo`, `trades`, or `mbp_10` fetch; this
function returns `False` for every date while the list is empty, so no fetch is attempted and no manifest row is
written.

Historical reference windows are preserved in two constants:

- `_DEFERRED_TRADFI_TICK_DATA_WINDOWS` — list-shape, mirrors the original `TRADFI_TICK_DATA_WINDOWS` entries before
  deferral.
- `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` — dict-shape, preserves the CME `tbbo` and CME `mbp_10` reference
  coverage windows from `VENUE_DATA_TYPE_COVERAGE_WINDOWS`.

Both are restored by `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` when L1/L2 collection resumes post-cutover.

### NEEDS_CANDLE_PROCESSING

Indicates whether MTDS passes a data type through the MDPS candle-processing pipeline before writing to GCS.

| data_type                    | NEEDS_CANDLE_PROCESSING | Notes                                                  |
| ---------------------------- | ----------------------- | ------------------------------------------------------ |
| `ohlcv_1m`                   | True                    | Bars sent through MDPS candle pipeline                 |
| `ohlcv_15m`                  | True                    | Bars sent through MDPS candle pipeline                 |
| `ohlcv_24h`                  | True                    | Bars sent through MDPS candle pipeline                 |
| `tbbo`                       | True (when undeferred)  | L1 ticks require candle aggregation at consumption     |
| `trades`                     | True (when undeferred)  | L1 ticks require candle aggregation at consumption     |
| `mbp_10`                     | False                   | L2 order book — bypass / pass-through; no candle step  |
| `corporate_action_confirmed` | False                   | Reference data — bypass / pass-through; no candle step |
| `earnings_result`            | False                   | Reference data — bypass / pass-through; no candle step |
| `macro_result`               | False                   | Reference data — bypass / pass-through; no candle step |

### VIX — Barchart + Yahoo Finance Layered Coverage

VIX is collected as `ohlcv_24h` with a two-source layered strategy per UAC `registry/data_source_continuity.py`:

1. **Barchart preload** — covers the full historical series back to VIX inception. Requires Barchart API subscription
   (`barchart-api-key` in Secret Manager). This is the primary source.
2. **Yahoo Finance rolling 60d** (`yfinance`) — no API key required; covers the rolling 60-day window as a fallback and
   continuity layer when Barchart is unavailable.
3. **Honest gap** — any date not covered by either source is recorded as `empty_confirmed[reason=EXPECTED_SOURCE_GAP]`.
   The UAC `registry/data_source_continuity.py` constants define the known gap windows explicitly; the handler consults
   `is_in_known_gap(series="VIX", date=date)` before deciding the absence reason.

### Shard-Level Failure Isolation

All TradFi handlers follow the MTDS shard-level isolation pattern: exceptions are caught per-venue / per-instrument
loop, recorded via the appropriate manifest recorder (`record_failed()`), and the loop continues. No bare `raise` inside
per-shard iteration. SSOT: `codex/04-architecture/shard-level-failure-isolation.md`.

### Availability Manifest

All handlers use the TradFi manifest recorder to write honest-coverage entries:

- `record_captured(venue, data_type, instrument_type, row_count, attempted_at)` — rows written
- `record_empty(venue, data_type, attempted_at, reason=<EmptyConfirmedReason>)` — zero rows, legitimate absence
- `record_failed(venue, data_type, error, attempted_at)` — exception caught

`reason` on `record_empty` is mandatory. For events-only data types (`corporate_action_confirmed`, `earnings_result`,
`macro_result`), use `reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO` for non-event days.

---

## Related Documents

- `codex/02-data/mtds-data-source-coverage-matrix.md` — full MTDS source coverage matrix (§3 TRADFI)
- `codex/02-data/per-asset-group-bucket-layouts.md` — GCS bucket layout per asset_group
- `codex/02-data/defi-data-types-catalog.md` — sibling catalog for DeFi data types
- `codex/02-data/availability-manifest-and-data-status.md` — manifest v5+ schema + honest-coverage semantics
- `codex/02-data/honest-absence-downstream-handling.md` — per-reason consumer policy table
- UAC: `unified_api_contracts.registry.capability_declarations._tradfi` — registered series IDs + venue capabilities
- UAC: `unified_api_contracts.registry.market_data_categories` — `TRADFI_TICK_DATA_WINDOWS` + deferred constants
- Plan: `plans/active/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md` — OHLCV-only MVP backfill plan
- Plan: `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` — tick data restoration post-cutover
