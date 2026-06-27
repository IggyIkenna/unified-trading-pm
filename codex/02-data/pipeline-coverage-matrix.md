---
scope: [engineer]
last_reviewed: 2026-05-17
---

# Pipeline Coverage Matrix — instruments-service · MTDS · MDPS

**Purpose:** single-page reference for "what does each service capture / produce, per (asset_group, venue, data_type)"
across the three pipeline layers. Use this when scoping backfills, debugging missing shards, or reasoning about
end-to-end coverage.

**Last audited:** 2026-05-06 (parallel agent audit of source + GCS reality check) **Project:** `central-element-323112`
**Related SSOTs:**

- `codex/02-data/availability-manifest-and-data-status.md` — manifest schema + capture_status
- `codex/02-data/per-asset-group-bucket-layouts.md` — bucket naming
- `codex/02-data/mtds-data-source-coverage-matrix.md` — MTDS-specific deeper dive
- `codex/02-data/sports-data-source-coverage-matrix.md` — sports-specific deeper dive
- `market-tick-data-service/market_tick_data_service/raw_tick_hive.py` — hive key SSOT
- `unified_api_contracts.canonical.domain.sports.league_data` — `SOURCE_COVERAGE_START`

> **Refresh protocol:** when an adapter is added/removed, a venue capability flips, or hive-key drift is resolved,
> update the relevant section here AND the per-service deep-dive doc. This document is a navigational matrix, not a
> duplicate SSOT — link out to source files for anything that needs version tracking.

---

## 0. Bucket Topology (ground truth from GCS, 2026-05-06)

> **SSOT pointer**: per-asset-group bucket patterns + path templates + hive-key vocabulary (canonical `asset_group=` vs
> legacy `category=` + tradfi non-Hive shape) + per-asset-group migration status live in
> [`per-asset-group-bucket-layouts.md`](./per-asset-group-bucket-layouts.md). This doc focuses on the per-service
> coverage matrix (which service writes which `(asset_group, data_type, day)` tuple) and the manifest index files +
> consolidator topology below — for "what does the path look like on disk for asset_group X" consult the
> per-asset-group-bucket-layouts SSOT.

### Manifest index files (per bucket)

Every bucket carries an index sub-tree at `_index/`. The split-write pattern (Phase 1: per-VM shards; Phase 2:
consolidator merge) avoids the 429 thundering herd on the canonical blob. Path constants are SSOT in
[`unified-trading-library/unified_trading_library/manifest_consolidator.py`](../../../unified-trading-library/unified_trading_library/manifest_consolidator.py).

| Path                                 | Producer                                                 | Purpose                                                                                                                                       |
| ------------------------------------ | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `_index/availability_index.parquet`  | consolidator (single writer)                             | **Canonical merged manifest** — one row per shard. All readers (deployment-api, instruments-service skip-if-exists, phantom audit) read this. |
| `_index/per_vm/{instance}.parquet`   | `ManifestWriter._write_per_vm_shard` (one per writer VM) | Per-VM append-only shard. Avoids CAS contention on the canonical blob — each VM writes its own file with no cross-VM locking.                 |
| `_index/per_vm/_legacy_seed.parquet` | consolidator on first run                                | One-time copy of the historical canonical blob, so legacy rows survive the merge. Idempotent — subsequent runs skip if present.               |
| `_index/consolidator.lock`           | consolidator (TTL = 90 s)                                | Cooperative lock so two scheduled cycles don't fight. Lock TTL exceeds the cycle period (60 s) by design — stale locks self-expire.           |

**Consolidator deployment shape:**

- Cloud Run Job `manifest-consolidator` (one per bucket / asset-group).
- Cron: `*/1 * * * *` (one cycle per minute). Reader fallback staleness is 120 s, so a one-cycle skip stays correct.
- CLI: `python -m unified_trading_library.manifest_consolidator --bucket {bucket}`.
- Per cycle emits `MANIFEST_CONSOLIDATED` (success) or `MANIFEST_CONSOLIDATION_FAILED` (failure).
- Dedup on merge: last-attempted-write wins per shard primary key.

**Read path:** `read_availability_index()` reads the canonical blob first; falls back to merging per-VM shards on the
fly if the canonical is older than 120 s (rare — only when the consolidator is down). Missing v5/v6 columns from older
parquets are backfilled with their defaults; **no migration needed for reads**.

**Write path (every adapter):**

| Outcome                         | Method                                                                      | When                                                 |
| ------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------- |
| Real rows on disk               | `record_captured(row_key=…, instrument_count=N, attempted_at=…)`            | adapter wrote N>0 rows to canonical path             |
| Source returned 200 + zero rows | `record_empty(row_key=…, attempted_at=…)`                                   | legitimate gap (paused league, post-genesis)         |
| Adapter raised                  | `record_failed(row_key=…, error=classify_venue_error(exc), attempted_at=…)` | error_reason classified; auto-retried by next VM run |

### Manifest schema (v9 — current in code; data migration in progress)

> **[DELTA 2026-06-01]** **Current state:** `MANIFEST_SCHEMA_VERSION = 9` in `manifest_writer.py` (code constant rolled
> 2026-05-30). Data-side migration is in progress as per-AG L3 walk riders; target is 100% of production rows at v9.
> **Target architecture:** 100% of production rows at v9 with all new v9 columns populated.

`MANIFEST_SCHEMA_VERSION = 9` in
[`manifest_writer.py`](../../../unified-trading-library/unified_trading_library/manifest_writer.py). Evolution: v4 → v5
(honest-coverage Phase A, 2026-04-19) → v6 (quote_margin_combo plan, 2026-04-23) → v7 (sports `fixture_id` +
ML/strategy/execution `job_id`, UTL@`ed658e9b`) → v8 (`pipeline_mode` + `service_emission_state` +
`last_emission_decision_at` + `expected_window_completeness_fraction` (renamed from `_pct` per UAC@`76f950a`
2026-05-11)) → v9 (`source` universal provider tag, UTL@`c7bfa427` 2026-05-30; data migration via per-AG L3 walk riders
per `plans/active/pipeline_mode_partition_migration_2026_06_01.md`). See
[`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md) for the full SSOT — this is a
brief recap.

`AvailabilityRecord` columns (defaults `""` unless noted):

| Group                                   | Columns                                                                                                                                                                                        | Notes                                                                                                                                         |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Universal (always set)                  | `date`, `venue`, `instrument_count`, `service_name`, `written_at`, `schema_version`                                                                                                            | every row                                                                                                                                     |
| Market data                             | `data_type`, `timeframe`, `league_id`, `chain`, `instrument_type`, `underlying`                                                                                                                | populated by instruments-service / MTDS / MDPS                                                                                                |
| Feature/ML                              | `feature_group`, `model_family`, `training_period`                                                                                                                                             | feature & ml services                                                                                                                         |
| Downstream                              | `strategy_id`, `client_id`, `instruction_type`                                                                                                                                                 | strategy / risk / execution                                                                                                                   |
| Per-instrument (Phase 1.9)              | `instrument_id`, `expected: bool=True`, `available: bool=True`                                                                                                                                 | zero-fill rows set `available=False`                                                                                                          |
| **v5** (honest-coverage, 2026-04-19)    | `capture_status` (`captured` / `empty_confirmed` / `attempted_failed`), `error_reason`, `attempted_at`                                                                                         | distinguishes empty-vs-failed-vs-missing                                                                                                      |
| **v6** (quote_margin_combo, 2026-04-23) | `quote_asset` (USD/USDT/USDC/BTC/ETH/KRW), `margin_type` (`inverse` / `linear` / `""`), `combo_type` (`call_spread`, `iron_condor`, etc.), `leg_weights` (JSON of `[{instrument_id, qty}, …]`) | required on DERIBIT chain shards to disambiguate `BTC-PERPETUAL` (inverse) vs `BTC_USDC-PERPETUAL` (linear); carries multi-leg combo metadata |

**Column rules (must follow):**

- Services write **only** the columns relevant to their shard dimensions; the rest stay `""`.
- **Never overload `venue`** with non-venue data.
- DeFi `venue` = protocol only (`AAVE_V3`); chain goes in `chain`.
- Sports MTDS `venue` = individual bookmaker (`PINNACLE`, `BETFAIR_EX`), NOT `ODDS_API`.
- **No `data_source` column.** Track what the data IS (transfers, injuries, odds), not where it came from. Provider swap
  = same manifest.
- `underlying` vs `instrument_id`: chain bundles (`options_chain`/`futures_chain`) populate `underlying` (BTC, ETH) and
  leave `instrument_id` empty; per-symbol shards do the inverse.
- `quote_asset` + `margin_type` are **required** on DERIBIT v6 chain shards so
  `(date, venue, instrument_type, data_type, underlying, quote_asset, margin_type)` is unambiguous.

**Four states a shard can be in (v5/v6 encoding):**

| State                     | Row?   | `capture_status`   | `instrument_count` |
| ------------------------- | ------ | ------------------ | ------------------ |
| Ingested                  | yes    | `captured`         | > 0                |
| Expected-empty            | yes    | `empty_confirmed`  | 0                  |
| Attempted-failed          | yes    | `attempted_failed` | 0                  |
| Missing (never attempted) | no row | —                  | —                  |

Phantom audit (`reconcile_phantom_manifest_rows_all.py`) is the inverse: scans canonical GCS paths, flips `captured`
rows whose parquet is missing on disk to `attempted_failed`.

---

## 1. instruments-service — Reference Discovery

instruments-service writes `instrument_type` (not market data_types). Source:
`instruments-service/instruments_service/adapters/{cefi,defi,tradfi,sports}/`. Manifest:
`instruments-store-{ag}/_index/availability_index.parquet`.

### CEFI

| venue                                                                                           | instrument_types                            | adapter                                  |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------- | ---------------------------------------- |
| BINANCE-SPOT, COINBASE, BITFINEX-SPOT, BITGET-SPOT, KRAKEN-SPOT, OKX-SPOT, UPBIT                | SPOT_PAIR                                   | `adapters/cefi/tardis.py`                |
| BINANCE-FUTURES, BITFINEX-FUTURES, BITGET-FUTURES, KRAKEN-FUTURES, OKX-SWAP, OKX-FUTURES, BYBIT | PERPETUAL, FUTURE (BYBIT also SPOT)         | tardis                                   |
| DERIBIT                                                                                         | SPOT_PAIR, PERPETUAL, FUTURE, OPTION, COMBO | tardis + `cefi/deribit_combo_adapter.py` |
| HYPERLIQUID, ASTER                                                                              | PERPETUAL only (options/futures rejected)   | `cefi/hyperliquid.py`, `cefi/aster.py`   |
| PACIFICA-SOLANA, EXTENDED-STARKNET, LIGHTER-ZKSYNC                                              | PERPETUAL                                   | CCXT fallback                            |
| GMX, DRIFT                                                                                      | PERPETUAL (+SPOT for DRIFT)                 | defi adapter chain                       |

CeFi options underlyings filtered to BTC/ETH only (`CEFI_OPTIONS_UNDERLYINGS`).

### DEFI

| protocol                                               | chains                                      | inst_type      | mtds_ops                                                                 |
| ------------------------------------------------------ | ------------------------------------------- | -------------- | ------------------------------------------------------------------------ |
| AAVE_V3                                                | ETH, ARB, OPT, POLY, AVAX, BASE, BSC, LINEA | LENDING        | lending_indices, liquidations, risk_params, gas_fees                     |
| SPARK                                                  | ETH                                         | LENDING        | lending_indices, liquidations, risk_params, gas_fees                     |
| COMPOUND_V3                                            | ETH, ARB, BASE, OPT                         | LENDING        | lending_indices, liquidations, gas_fees                                  |
| MORPHO                                                 | ETH, BASE                                   | LENDING        | liquidations, gas_fees (no lending_indices — uses `blue-api.morpho.org`) |
| FLUID                                                  | ETH                                         | LENDING        | lending_indices, liquidations, gas_fees                                  |
| UNISWAP_V2 / V3 / V4                                   | V2:ETH; V3:ETH/ARB/BASE/OPT/POLY; V4:ETH    | POOL           | dex_pools, dex_swaps, gas_fees                                           |
| BALANCER                                               | ETH, ARB, POLY, OPT, AVAX, BASE             | POOL           | dex_pools, dex_swaps, gas_fees                                           |
| CURVE                                                  | ETH, OPT, AVAX                              | POOL           | dex_pools, dex_swaps, gas_fees                                           |
| PANCAKESWAP_V3, SUSHISWAP_V3, AERODROME_V3, CAMELOT_V3 | per-chain                                   | POOL           | dex_pools, dex_swaps, gas_fees                                           |
| GMX                                                    | ARB, AVAX                                   | POOL           | dex_pools, dex_swaps, perp_funding, liquidations, gas_fees               |
| LIDO, ETHERFI, ETHENA                                  | ETH                                         | YIELD_BEARING  | lst_rates, oracle_prices, rewards, gas_fees                              |
| EIGENLAYER                                             | ETH                                         | SPOT_ASSET     | rewards, oracle_prices, gas_fees                                         |
| DRIFT                                                  | SOLANA                                      | PERPETUAL+SPOT | perp_funding, oracle_prices                                              |
| KAMINO, RAYDIUM, ORCA                                  | SOLANA                                      | POOL           | dex_pools, dex_swaps                                                     |
| MARINADE, JITO                                         | SOLANA                                      | STAKING        | lst_rates, oracle_prices                                                 |

**Orphan adapters** (present, not in `PROTOCOL_CAPABILITIES`, not wired into orchestrator): `benqi.py`, `euler_v2.py`,
`ethfi.py`, `radiant.py`, `venus.py`. Either dead or planned future venues.

### TRADFI

| venue        | instrument_types              | adapter                                                                        |
| ------------ | ----------------------------- | ------------------------------------------------------------------------------ |
| CME          | FUTURE, OPTION, FX SPOT, BOND | `tradfi/databento.py`                                                          |
| NASDAQ, NYSE | EQUITY, ETF, INDEX            | databento                                                                      |
| ICE          | INDEX (DXY)                   | **Yahoo Finance** (NOT databento; IFUS/IFEU out of subscription, UAC@5480f5d5) |
| CBOE         | INDEX (VIX cash)              | Barchart CSV → Yahoo (VX FUTURES = Databento XCBF.PITCH)                       |
| FX           | SPOT_PAIR (KRW/USD)           | `tradfi/tradfi_live.py` (Yahoo)                                                |
| KRX          | INDEX (KOSPI/KOSPI200)        | **Yahoo Finance** (`^KS11`/`^KS200`; genesis 2019-01-02; UAC@5480f5d5)         |

### SPORTS

> **Coverage-start values**: see
> [`availability-manifest-and-data-status.md` § Source coverage start dates (canonical)](./availability-manifest-and-data-status.md#source-coverage-start-dates-canonical--source_coverage_start-ssot)
> (UAC `unified_api_contracts.sports.SOURCE_COVERAGE_START` + `DATA_TYPE_COVERAGE_START` runtime SSOT). Sources covered:
> `api_football`, `footystats`, `understat`, `transfermarkt`, `soccer_football_info`, `open_meteo`.
> Per-`(source, data_type)` overrides for SFI_PROGRESSIVE_STATS and api_football per-fixture data_types live in the same
> canonical table.

### PREDICTION

| venue      | inst_type                                            | data_type                           | coverage_start                               |
| ---------- | ---------------------------------------------------- | ----------------------------------- | -------------------------------------------- |
| POLYMARKET | PREDICTION_MARKET (sub-typed crypto/sports/EPL/etc.) | trades (canonical, post-2026-04-19) | per-market: BTC 2025-03-13 → GOLD 2025-12-09 |
| KALSHI     | PREDICTION_MARKET                                    | trades                              | 2024-06-01                                   |

---

## 2. MTDS — Raw Market Data

### CEFI

| venue                                                    | trades               | book_snapshot_5   | derivative_ticker        | liquidations        | options_chain | futures_chain |
| -------------------------------------------------------- | -------------------- | ----------------- | ------------------------ | ------------------- | ------------- | ------------- |
| BINANCE-SPOT                                             | yes                  | yes               | –                        | –                   | –             | –             |
| BINANCE-FUTURES                                          | yes                  | yes               | yes                      | yes                 | –             | yes           |
| BYBIT                                                    | yes                  | yes               | yes                      | yes                 | –             | yes           |
| OKX-SPOT                                                 | yes                  | yes               | –                        | –                   | –             | –             |
| OKX-FUTURES/SWAP                                         | yes                  | yes               | yes                      | yes                 | –             | –             |
| DERIBIT                                                  | yes                  | yes               | yes                      | yes                 | yes           | yes           |
| COINBASE, UPBIT, BITFINEX-SPOT, BITGET-SPOT, KRAKEN-SPOT | yes                  | yes               | –                        | –                   | –             | –             |
| BITFINEX-FUTURES, BITGET-FUTURES, KRAKEN-FUTURES         | yes                  | yes               | yes                      | yes                 | –             | –             |
| HYPERLIQUID                                              | yes (S3 ≥2025-03-22) | yes (≥2023-04-15) | yes                      | – (no feed)         | –             | –             |
| ASTER                                                    | yes                  | –                 | yes                      | – (broken endpoint) | –             | –             |
| GMX, DRIFT                                               | –                    | –                 | – (perp_funding instead) | –                   | –             | –             |
| LIGHTER-ZKSYNC, PACIFICA-SOLANA, EXTENDED-STARKNET       | **live-only** ¹      | –                 | – (perp_funding)         | –                   | –             | –             |

Adapters: `market_interface/adapters/{binance,bybit,okx,deribit,coinbase}.py`,
`cefi/tardis_incremental_book_adapter.py`, `onchain_perps/{hyperliquid,aster}_adapter.py`.

**Asymmetries:** `options_chain` is Deribit-only. `liquidations` absent from all spot venues + HYPERLIQUID + ASTER.
`derivative_ticker` perp-only. ¹ `trades` for LIGHTER-ZKSYNC / PACIFICA-SOLANA / EXTENDED-STARKNET is **live-only, no
historical tape** — upstream adapters lack an archival endpoint; strategies needing per-trade history must use
`ohlcv_1m` bars or forward-poll history built post-launch (LIGHTER ≥2026-04-17, PACIFICA ≥2025-06-01, EXTENDED
BLOCKED-OPERATOR-DECISION). See `plans/active/defi_master.md` item 2.P3.

### DEFI (data_types by category)

| category       | data_types                                                                        | venues                                                                              |
| -------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| DEX            | dex_swaps, dex_pools                                                              | UNISWAP V2/V3/V4, CURVE, BALANCER, ORCA, RAYDIUM (per chains in §1)                 |
| Lending        | lending_indices, oracle_prices, rewards, risk_params                              | AAVE_V3, COMPOUND_V3, MORPHO, FLUID, KAMINO                                         |
| Lending events | liquidation_events, flash_loan_events, position_data                              | AAVE_V3-{ETH,ARB,POLY}, MORPHO-ETH, UNISWAP_V3-ETH                                  |
| LST/Yield      | lst_rates, oracle_prices, staking_yields                                          | LIDO, ETHERFI, ETHENA, JITO                                                         |
| Perp DEX       | perp_funding (+ liquidations, oracle_prices for GMX)                              | HYPERLIQUID, ASTER, GMX-ARB, GMX-AVAX                                               |
| Gas            | gas_fees                                                                          | ALCHEMY-{ETH, OPT, BSC, POLY, BASE, ARB, AVAX, LINEA, FANTOM, CELO, MANTLE, AURORA} |
| Vault          | vault_share_price                                                                 | ETHEREUM (Yearn V3, sUSDe, Morpho MetaMorpho, Pendle)                               |
| Phase-1 events | token_transfers, bridge_events, governance_events, eigenlayer_rewards, mev_events | ALCHEMY, ACROSS, STARGATE, COMPOUND, AAVE, UNISWAP, EIGENLAYER, FLASHBOTS           |

### TRADFI

| venue        | data_types             | start      | source                                                                |
| ------------ | ---------------------- | ---------- | --------------------------------------------------------------------- |
| NASDAQ, NYSE | trades, ohlcv_1m, tbbo | 2023-04-15 | Databento                                                             |
| CME          | trades, ohlcv_1m, tbbo | 2020-01-01 | Databento                                                             |
| ICE          | (DXY only)             | 2020-01-01 | **Yahoo Finance** (NOT Databento — IFUS/IFEU out of subscription)     |
| CBOE         | ohlcv_15m              | 2020-06-01 | Barchart CSV→2025-11, Yahoo after (VX futures = Databento XCBF.PITCH) |
| FX           | ohlcv_24h              | 2020-01-01 | Yahoo                                                                 |
| KRX          | index_daily            | 2019-01-02 | **Yahoo Finance** (`^KS11`/`^KS200`)                                  |

MBP-1 quotes dropped 2026-04-30; tbbo supersedes.

### SPORTS

> **Coverage-start values**: see
> [`availability-manifest-and-data-status.md` § Source coverage start dates (canonical)](./availability-manifest-and-data-status.md#source-coverage-start-dates-canonical--source_coverage_start-ssot)
> for `ODDS_API` / `mdps_odds_horizon_bucket` (SSOT for the literal date).

| source                                             | mtds raw data_type              | coverage_start                |
| -------------------------------------------------- | ------------------------------- | ----------------------------- |
| ODDS_API                                           | odds                            | per canonical SOURCE_COVERAGE |
| PINNACLE / BETFAIR / DRAFTKINGS / FANDUEL / BET365 | odds (via ODDS_API aggregation) | 2024-01-01 (per-bookmaker)    |

### PREDICTION

| venue      | data_types | start      |
| ---------- | ---------- | ---------- |
| POLYMARKET | trades     | 2024-06-01 |
| KALSHI     | trades     | 2024-06-01 |

`book_snapshot_5` retired 2026-04-19 (was inflating completion_pct).

---

## 3. MDPS — Processed Output

Output path:

```
{mtds_bucket}/processed_candles/by_date/day=YYYY-MM-DD/timeframe={tf}/data_type={dt}/venue={v}/{instrument_id}.parquet
```

(sports uses `processed/by_date/...` instead of `processed_candles/`).

Standard timeframes: `15s, 1m, 5m, 15m, 1h, 4h, 24h`. Sports horizon-bucket timeframes:
`T-24h, T-12h, T-6h, T-4h, T-2h, T-1h, T-10m, T-0`.

### Input → Processor Map

| MTDS input                     | MDPS adapter                           | Output features                                                                                                       | Asset groups                        |
| ------------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| `trades`                       | `cefi/trades_adapter.py`               | OHLCV + buy/sell volume + VWAP + HFT (delay percentiles, tick momentum, trade size p10/50/90/99, whale, volume clock) | cefi, prediction (inherits), tradfi |
| `book_snapshot_5`              | `{cefi,defi}/book_snapshot_adapter.py` | OHLCV=NaN; spread_bps, mid_price, depth, imbalance, weighted_mid_5lvl, effective_spread_5lvl, OBI, micro vol          | cefi, defi                          |
| `derivative_ticker`            | `cefi/derivative_adapter.py`           | funding_rate, open_interest, mark_price, index_price (LOCF)                                                           | cefi                                |
| `liquidations`                 | `cefi/liquidations_adapter.py`         | per-interval buy/sell volume, count, cascade detection                                                                | cefi                                |
| `options_chain`                | `cefi/options_chain_adapter.py`        | mark_iv/bid_iv/ask_iv, greeks (delta/gamma/vega/theta), strike, expiry, OI, **staleness_seconds**                     | cefi (Deribit)                      |
| `futures_chain`                | `cefi/futures_chain_adapter.py`        | last/index/mark, basis, basis_pct, annualized_basis (hardcoded 30d), OI                                               | cefi                                |
| `dex_swaps`                    | `defi/swap_adapter.py`                 | OHLCV from amount0/amount1/amountUSD                                                                                  | defi                                |
| `liquidity`                    | `defi/liquidity_adapter.py`            | tvl_usd, reserves, token prices, V3 in-range liquidity, tick, fees                                                    | defi                                |
| `market_state`                 | `defi/market_state_adapter.py`         | total_supply/borrow, liquidity, fee, utilization                                                                      | defi                                |
| `fx_rates`                     | `defi/fx_rate_adapter.py`              | ETH/BTC/SOL USD spot at candle close (synthesized from CeFi spot)                                                     | defi                                |
| `ohlcv_1m / 15m / 24h`         | `tradfi/ohlcv_passthrough.py`          | full-day grid passthrough; market_state / is_halted / is_auction                                                      | tradfi                              |
| `tbbo`                         | `tradfi/tbbo_adapter.py`               | spread_bps, mid_price, market state flags                                                                             | tradfi                              |
| `odds` → `odds_snapshot`       | `sports/odds_snapshot_adapter.py`      | LOCF home/away/draw odds + implied probs + overround                                                                  | sports                              |
| `odds` → `odds_movement`       | `sports/odds_movement_adapter.py`      | OHLC of home_odds line movement + count                                                                               | sports                              |
| `odds` → `odds_horizon_bucket` | `sports/bucket_assignment_adapter.py`  | 8 horizon buckets; long→wide for h2h/spreads/totals/btts; staleness caps; causality filter                            | sports                              |

---

## 4. Gaps & Asymmetries

### MTDS captures, MDPS does NOT process (pass-through to features-onchain)

| data_type                                                                                                                                                                                      | scope      | status                                                               |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | -------------------------------------------------------------------- |
| `lending_indices`, `oracle_prices`, `utilization`, `rewards`, `risk_params`, `gas_fees`, `lst_rates`, `tvl`                                                                                    | defi       | intentional pass-through (per `defi/__init__.py` docstring)          |
| `perp_funding`                                                                                                                                                                                 | cefi/defi  | listed in scanner set, **no registered MDPS adapter** — possible gap |
| `prediction_book_snapshot`, `prediction_market_metadata`                                                                                                                                       | prediction | retired 2026-04-19 (won't appear)                                    |
| `liquidation_events`, `flash_loan_events`, `staking_yields`, `token_transfers`, `bridge_events`, `governance_events`, `eigenlayer_rewards`, `mev_events`, `position_data`, `vault_share_price` | defi       | pass-through                                                         |

### MDPS produces, MTDS source not obvious

- `fx_rates` — synthesized from CeFi spot trades; no MTDS `fx_rates` stream
- `odds_snapshot`, `odds_movement`, `odds_horizon_bucket` — all from one MTDS `odds` input

### Disk drift / data quality concerns

1. **sports + prediction:** 100% on disk uses legacy `category=` hive key. No migration done; readers rely on regex
   fallback (`(?:category|asset_group)=`).
2. **tradfi:** uses `day-` (dash) and `data_type-` (dash) — non-Hive; no `asset_group=` partition; instrument_type
   before venue. Schema is an outlier vs. cefi/defi.
3. **Stray flat parquets** at `market-data-tick-cefi/raw_tick_data/by_date/*.parquet` (no `day=`, written 2026-05-04) —
   likely mis-routed test writes worth reconciling.
4. **Sports has dual sub-trees per day** — `venue=ODDS_API/...` and `data_source=ODDS_API/venue=BETFAIR_EX_EU/...`
   coexist.
5. **2026-05-05 placeholder-row class:** Caused by reader/data_type drift (`dex_swaps` vs legacy `swaps`;
   `{instrument_id}.parquet` vs legacy `ticks.parquet`). Mitigated via `_data_type_requires_partition` gating in
   `orchestration_scanner.py`. `ticks.parquet` is now write-side only (chain bundles).
6. **futures_chain basis annualization** uses hardcoded 30-day to-expiry assumption — known approximation, not a
   per-contract calc.

### Cross-venue holes worth flagging

- `options_chain` exists only for DERIBIT. CME options exist at instruments-service level (databento) but no MTDS
  options_chain.
- `liquidations` missing from HYPERLIQUID (no feed) and ASTER (broken endpoint) — perp data without liquidation
  telemetry.
- `perp_funding` has no MDPS processor despite being scanned — either add one or drop from scanner set.
- Orphan instruments-service DeFi adapters (`benqi`, `euler_v2`, `radiant`, `venus`) imply planned-but-not-shipped
  venues.

---

## 5. Open follow-ups (non-exhaustive)

- [ ] Decide on `perp_funding` MDPS adapter (build or remove from scanner)
- [ ] Migrate sports + prediction off `category=` hive key (or formally bless it as canonical — document either way)
- [ ] Reconcile stray flat parquets in `market-data-tick-cefi/raw_tick_data/by_date/`
- [ ] Re-Hive tradfi paths (`day-` → `day=`, add `asset_group=`) or document the divergence as intentional
- [ ] Wire orphan DeFi adapters or delete them
- [ ] Replace hardcoded 30-day basis annualization in futures_chain adapter with per-contract expiry
