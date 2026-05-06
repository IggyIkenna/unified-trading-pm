---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06 -->

> **POST-PLAN REALITY (2026-05-06)** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md)
> BEFORE making code or doc changes informed by this doc. This doc is partially stale: doesn't reflect the 4-pillar
> write-gate (row-count + NaN-ratio + schema + cluster-coverage), record_empty / record_failed typed reasons, per-VM
> shard isolation, or sports per-fixture sharding. The post-plan-reality doc lists the 10 cross-cutting principles
> codified in workspace `CLAUDE.md` (live=batch, no double SSOT, three-category empty-output decision, cluster
> validation mandatory, per-row write-time `available_at`, prediction lifecycle timing, temporary state must have named
> successor, per-VM shard isolation, etc.) plus the active plans where the canonical post-plan reality is being
> implemented (`writegate_honest_coverage_endtoend_2026_05_06.plan.md`,
> `predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`). If this doc and the active plans
> disagree, the plans win. If you find a contradiction the plans don't address, flag to user — don't decide
> unilaterally.

# Availability Manifest & Data Status — SSOT

> **This document is the single source of truth** for: what the availability manifest is, its schema, shard dimensions
> per service, how the data status page works, how availability % is calculated, and the integrity principles that make
> it trustworthy. All other docs, CLAUDE.md, cursor rules, and memory files cross-reference this document.

> **Reading this for chart debugging?** See also `chart-candle-delivery-flow.md` for the end-to-end flow from the
> price-chart widget through the manifest to the GCS parquets.

## What Is the Availability Manifest?

Every GCS data bucket has an `_index/availability_index.parquet` file. This parquet file is the **index of what data
exists** in that bucket. Each row represents one shard — a unit of data written atomically.

Services write to the manifest via `ManifestWriter` (UTL). The deployment-api reads it via `read_availability_index()`.
The deployment-ui renders it as the data status page.

### SSOT Locations

| Component                                     | Location                                                                                              |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Schema definition                             | `unified-trading-library/unified_trading_library/manifest_writer.py` — `AvailabilityRecord` dataclass |
| Writer                                        | `unified-trading-library/unified_trading_library/manifest_writer.py` — `ManifestWriter` class         |
| Reader                                        | `unified-trading-library/unified_trading_library/manifest_writer.py` — `read_availability_index()`    |
| Registry (start dates, expected venues, etc.) | `unified-api-contracts/unified_api_contracts/registry/`                                               |
| API that serves data status                   | `deployment-api/deployment_api/services/data_status_service.py`                                       |
| UI that renders data status                   | `deployment-ui/src/components/DataStatusTab.tsx`                                                      |

## Schema v6 (current)

The schema has evolved through three published revisions: v4 → v5 (honest-coverage Phase A, 2026-04-19) → v6
(quote_margin_combo plan, 2026-04-23). The current SSOT lives in
`unified-trading-library/unified_trading_library/manifest_writer.py` — `MANIFEST_SCHEMA_VERSION = 6` and the
`AvailabilityRecord` dataclass.

```python
MANIFEST_SCHEMA_VERSION = 6

@dataclass
class AvailabilityRecord:
    # ─────────────────────────────────────────────────────────────────────
    # Universal (always populated)
    # ─────────────────────────────────────────────────────────────────────
    date: str                       # YYYY-MM-DD — the date this shard covers
    venue: str                      # tradeable venue/protocol: BINANCE-SPOT, AAVE_V3, PINNACLE
    instrument_count: int           # number of rows/instruments in the shard
    service_name: str               # "instruments-service", "market-tick-data-service", etc.
    written_at: str                 # ISO timestamp — when this manifest entry was written
    schema_version: int = MANIFEST_SCHEMA_VERSION

    # ─────────────────────────────────────────────────────────────────────
    # Market data dimensions (populated by instruments-service, MTDS, MDPS)
    # ─────────────────────────────────────────────────────────────────────
    data_type: str = ""             # trades, book_snapshot_5, odds, swaps, liquidity, etc.
    timeframe: str = ""             # MDPS: 15s, 1m, 5m, 15m, 1h, 4h, 24h, T-24h..T-0
                                    # Features: 1m, 5m, 1h, T-24h..HT (sports horizons)
    league_id: str = ""             # SPORTS only: EPL, BUNDESLIGA, LA_LIGA, etc.
    chain: str = ""                 # DeFi only: ETHEREUM, ARBITRUM, BASE, SOLANA, etc.
    instrument_type: str = ""       # spot, perpetuals, equity, pool, lending, prediction_market
    underlying: str = ""            # Options/futures: BTC, ETH, ES, NQ — base for per-underlying shards

    # ─────────────────────────────────────────────────────────────────────
    # Feature/ML dimensions
    # ─────────────────────────────────────────────────────────────────────
    feature_group: str = ""         # Feature services: momentum, fixture_stats, macro_sentiment, etc.
    model_family: str = ""          # ML: pregame_xg, CEFI_BTC_swing-high_LIGHTGBM_1h_V1, etc.
    training_period: str = ""       # ML walk-forward: "2024-01" (month) or "2024" (season)

    # ─────────────────────────────────────────────────────────────────────
    # Downstream dimensions
    # ─────────────────────────────────────────────────────────────────────
    strategy_id: str = ""           # strategy, execution, PnL services
    client_id: str = ""             # risk-and-exposure service
    instruction_type: str = ""      # execution: TRADE, SWAP, LEND, BORROW, STAKE

    # ─────────────────────────────────────────────────────────────────────
    # Per-instrument identification (Phase 1.9 — zero-fill + canonical IDs)
    # ─────────────────────────────────────────────────────────────────────
    instrument_id: str = ""         # canonical instrument id (matches InstrumentRecord.instrument_key)
    expected: bool = True           # True = shard was expected on this date
    available: bool = True          # False only for zero-fill rows that have no data

    # ─────────────────────────────────────────────────────────────────────
    # v5 — honest-coverage Phase A (2026-04-19)
    # Distinguishes "tried + got nothing" from "tried + failed" from "didn't try".
    # ─────────────────────────────────────────────────────────────────────
    capture_status: str = "captured"    # one of: captured / empty_confirmed / attempted_failed
    error_reason: str = ""              # classified failure code for attempted_failed rows
    attempted_at: str = ""              # ISO-8601 UTC start-of-attempt; "" = legacy unknown

    # ─────────────────────────────────────────────────────────────────────
    # v6 — quote_margin_combo plan (2026-04-23)
    # Disambiguates DERIBIT inverse vs linear (BTC-PERPETUAL vs BTC_USDC-PERPETUAL)
    # on the same underlying, and carries multi-leg synthetic instrument metadata.
    # ─────────────────────────────────────────────────────────────────────
    quote_asset: str = ""           # "USD", "USDT", "USDC", "BTC", "ETH", "KRW"
    margin_type: str = ""           # "inverse" (coin-margined) | "linear" (stable-margined) | ""
    combo_type: str = ""            # "call_spread", "iron_condor", "butterfly", "" = non-combo
    leg_weights: str = ""           # JSON: [{"instrument_id": "...", "qty": 1|-1|...}]; "" = non-combo
```

### Column Rules

- Services write ONLY the columns relevant to their shard dimensions. All others default to `""`.
- **Never overload `venue`** with non-venue data. Use the proper column.
- **`venue` for DeFi** = protocol name only (AAVE_V3, not AAVEV3-ETHEREUM). Chain goes in `chain` column.
- **`venue` for SPORTS (MTDS)** = individual bookmaker (PINNACLE, BETFAIR_EX, DRAFTKINGS), not "ODDS_API".
- **No `data_source` column.** Track what the data IS (transfers, injuries, odds), not where it came from
  (Transfermarkt, API Football, Tardis). If you swap providers, the manifest stays the same.
- **`capture_status` is canonical** for shard state — `captured` (real data on disk), `empty_confirmed` (source returned
  200 + zero rows; counts in denominator only), `attempted_failed` (exception during fetch; classified via
  `error_reason`).
- **`underlying` vs `instrument_id`** for derivatives: bundled chain shards (options_chain / futures_chain) populate
  `underlying` with the base asset (BTC, ETH) and leave `instrument_id` empty. Per-symbol shards populate
  `instrument_id` and leave `underlying` empty.
- **`quote_asset` + `margin_type`** are required for DERIBIT v6 chain shards (and any future inverse/linear-split venue)
  so the (date, venue, instrument_type, data_type, underlying) primary key extends to (..., quote_asset, margin_type)
  without colliding inverse/linear bundles. Leave both empty for non-derivative or single-margin venues.

### Backward Compatibility

`read_availability_index()` handles older index versions transparently — missing v5/v6 columns are backfilled with their
defaults (`captured` for capture*status, `""` for the rest). No migration needed for reads. Writes produce v6 entries
that coexist with older entries until re-scanned by a `rebuild*\*\_manifest.py` pass.

## Per-Service Shard Dimension Matrix

Each service writes a specific subset of columns. "—" means the column is always `""` for that service.

### Layer 1: instruments-service (reference data)

| Category   | venue                                                                                                          | chain                                                                                          | data_type | instrument_type                                               | league_id                         |
| ---------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------- | --------------------------------- |
| CEFI       | BINANCE-SPOT, BINANCE-FUTURES, BYBIT, OKX, DERIBIT, COINBASE, ASTER, HYPERLIQUID, UPBIT                        | —                                                                                              | —         | SPOT_PAIR, PERPETUAL, FUTURE, OPTION                          | —                                 |
| TRADFI     | CME, NASDAQ, NYSE, ICE, CBOE, FX                                                                               | —                                                                                              | —         | EQUITY, FUTURE, OPTION, INDEX, COMMODITY, CURRENCY, BOND, ETF | —                                 |
| DEFI       | AAVE_V3, UNISWAP_V3, UNISWAP_V4, CURVE, BALANCER, COMPOUND_V3, MORPHO, LIDO, DRIFT, KAMINO, ... (30 protocols) | ETHEREUM, ARBITRUM, BASE, OPTIMISM, POLYGON, BSC, AVALANCHE, LINEA, SOLANA, HYPERLIQUID, ASTER | —         | POOL, LENDING, LST, YIELD_BEARING, STAKING                    | —                                 |
| SPORTS     | —                                                                                                              | —                                                                                              | —         | EXCHANGE_ODDS, FIXED_ODDS                                     | league_id (EPL, BUNDESLIGA, etc.) |
| PREDICTION | POLYMARKET, KALSHI                                                                                             | —                                                                                              | —         | PREDICTION_MARKET                                             | —                                 |

> **Removed venues:** OddsJam, PredictIt, Betdaq, and Smarkets have been deleted from all repos (UAC, MTDS,
> execution-service, instruments-service, consumer repos, and UI repos). No manifest rows exist or should be expected
> for these venues. Do not add expected-shard entries for them in UAC registry functions.

> **Hyperliquid and Aster instrument-type guard:** Both venues support perpetuals only. Any attempt to fetch
> `instrument_type=OPTION` or `instrument_type=FUTURE` from these venues raises
> `UnsupportedCapabilityError(venue=..., capability="options")` in the MTDS `BaseOnchainPerpAdapter`.
> instruments-service must apply the same guard at reference-data fetch time. Consequently, **no OPTION or FUTURE
> manifest rows should ever exist for HYPERLIQUID or ASTER** — the data status page treats any such row as a pipeline
> misconfiguration.

### Layer 2: market-tick-data-service (raw market data)

| Category   | venue                                                                                           | chain                                 | data_type                                                                                                                | instrument_type                                | league_id |
| ---------- | ----------------------------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------- | --------- |
| CEFI       | BINANCE-SPOT, BYBIT, DERIBIT, OKX, COINBASE, ...                                                | —                                     | trades, book_snapshot_5, derivative_ticker, liquidations, options_chain, futures_chain                                   | spot, perpetuals, futures_chain, options_chain | —         |
| CEFI \*    | HYPERLIQUID, ASTER                                                                              | —                                     | trades, book_snapshot_5, derivative_ticker, liquidations, perp_funding                                                   | **perpetuals only** — see guard note below     | —         |
| TRADFI     | CME, NASDAQ, NYSE, ICE, CBOE                                                                    | —                                     | trades, ohlcv_1m, ohlcv_15m, ohlcv_24h, tbbo                                                                             | equity, futures_chain, options_chain, index    | —         |
| DEFI       | AAVE_V3, UNISWAP_V3, CURVE, DRIFT, ...                                                          | ETHEREUM, ARBITRUM, BASE, SOLANA, ... | swaps, liquidity, rate_indices, oracle_prices, utilization, rewards, risk_params, gas_fees, lst_rates, perp_funding, tvl | pool, lending, lst                             | —         |
| SPORTS     | PINNACLE, BETFAIR_EX, DRAFTKINGS, FANDUEL, CORAL, PADDYPOWER, WILLIAMHILL, ... (~21 bookmakers) | —                                     | odds                                                                                                                     | —                                              | league_id |
| PREDICTION | POLYMARKET, KALSHI                                                                              | —                                     | prediction_trades, prediction_book_snapshot, prediction_market_metadata                                                  | prediction_market                              | —         |

> **\* Hyperliquid / Aster perpetuals-only guard:** `BaseOnchainPerpAdapter` raises
> `UnsupportedCapabilityError(venue=..., capability="options")` when `instrument_type` is OPTION or FUTURE. The
> instruments-service reference-data adapter applies the same guard. The UAC registry functions
> `get_expected_instrument_types_for_venue()` and `get_expected_data_types_for_venue()` return only
> perpetuals-compatible types for these venues — so the expected-shard denominator is never inflated with option/futures
> rows.

### Layer 2.5: market-data-processing-service (bucketed data)

| Category | venue        | chain  | data_type                                                  | instrument_type                                | timeframe                                        | league_id |
| -------- | ------------ | ------ | ---------------------------------------------------------- | ---------------------------------------------- | ------------------------------------------------ | --------- |
| CEFI     | same as MTDS | —      | trades, ohlcv, book_snapshot_5                             | spot, perpetuals, futures_chain, options_chain | 15s, 1m, 5m, 15m, 1h, 4h, 24h                    | —         |
| TRADFI   | same as MTDS | —      | trades, option_chain, futures_chain, rate_indices          | equity, futures_chain, options_chain           | 15s, 1m, 5m, 15m, 1h, 4h, 24h                    | —         |
| DEFI     | protocols    | chains | swaps, liquidity, rate_indices, oracle_prices, utilization | pool, lending, lst                             | 15s, 1m, 5m, 15m, 1h, 4h, 24h                    | —         |
| SPORTS   | bookmakers   | —      | odds_horizon_bucket                                        | —                                              | T-24h, T-12h, T-6h, T-4h, T-2h, T-1h, T-10m, T-0 | league_id |

#### Combo Shard Key (Phase 4 forward-reference)

Bundle-level combo chains will be tracked at a dedicated shard key. The manifest row for a combo chain shard uses:

| Column            | Value                            |
| ----------------- | -------------------------------- |
| `venue`           | underlying venue (e.g. DERIBIT)  |
| `data_type`       | `COMBO_CHAIN`                    |
| `instrument_type` | `COMBO`                          |
| `chain`           | `""` (CeFi) or chain name (DeFi) |
| `league_id`       | `""` (not applicable)            |

The shard granularity is `venue × underlying × date × data_type=COMBO_CHAIN`, analogous to how `options_chain` shards
are keyed at `venue × underlying × date × data_type=options_chain`. Expected-shard denominator for combo chains comes
from UAC `get_expected_data_types_for_venue(venue)` — the registry must include `COMBO_CHAIN` for venues that support
combo instruments. This section is a forward-reference; implementation is tracked in Phase 4 of the relevant plan.

### Layer 3: Feature Services

| Service                   | feature_group                                                                        | timeframe                           | chain                   | league_id |
| ------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------- | ----------------------- | --------- |
| features-delta-one        | technical_indicators, momentum, volatility_realized, microstructure, moving_averages | 1m, 5m, 1h                          | —                       | —         |
| features-volatility       | options_iv, options_term_structure, futures_basis, futures_term_structure            | 1m                                  | —                       | —         |
| features-onchain          | macro_sentiment, lending_rates, lst_yields, onchain_perps                            | timeframe                           | ETHEREUM, ARBITRUM, ... | —         |
| features-sports           | fixture_stats, injuries, lineups, player_stats, standings, ... (14 groups)           | T-24h, T-12h, T-6h, T-1h, T-10m, HT | —                       | league_id |
| features-calendar         | time_features, economic_events                                                       | —                                   | —                       | —         |
| features-multi-timeframe  | per enabled group                                                                    | 1m, 5m, 1h, 4h, 1d                  | —                       | —         |
| features-cross-instrument | regime_detection, cross_venue_spreads, realized_implied_vol, cross_asset_correlation | 1h                                  | —                       | —         |
| features-commodity        | commodity names (WTI_CRUDE_OIL, etc.)                                                | —                                   | —                       | —         |

**Sports feature horizons note:** Not all features are available at all horizons:

- T-24h: historical stats, early odds, predictive lineup (based on prior fixtures + known injuries)
- T-6h: odds velocity between T-24h and T-6h now known
- T-1h: actual lineup confirmed (UEFA/FA announce 60-75 min before kickoff)
- T-10m: sharp money peaks, final odds movement, late CLV
- HT: first-half live stats, in-play odds, current score

### Layer 4: ML Services

| Service                        | model_family                                                    | training_period                                                              |
| ------------------------------ | --------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| ml-training (CEFI/TRADFI/DEFI) | {CATEGORY}\_{SYMBOL}\_{target}\_{algo}\_{timeframe}\_V{version} | Walk-forward month: "2024-01", "2024-02", ...                                |
| ml-training (SPORTS)           | pregame_xg, pregame_clv, ht_xg, ht_clv, meta (5 families)       | Walk-forward season: "2019", "2020", ..., "2024" (expanding window, 5 folds) |
| ml-inference                   | Same model_family references                                    | — (daily predictions)                                                        |

**Sports ML:** ONE global model per family (league is a categorical feature, NOT separate models per league). 7
horizon-specific models across 5 families. Seasonal expanding window walk-forward. Quarterly retrain.

### Layer 5-8: Downstream Services

| Layer | Service                   | strategy_id | venue                                      | client_id | instruction_type                 |
| ----- | ------------------------- | ----------- | ------------------------------------------ | --------- | -------------------------------- |
| L5    | strategy-service          | strategy_id | —                                          | —         | —                                |
| L6    | execution-service         | strategy_id | execution venue (BINANCE-FUTURES, BETFAIR) | —         | TRADE, SWAP, LEND, BORROW, STAKE |
| L7    | risk-and-exposure-service | —           | —                                          | client_id | —                                |
| L8    | pnl-attribution-service   | strategy_id | —                                          | —         | —                                |

Position-balance-monitor is DB-backed (PostgreSQL), not GCS. It does not write to the manifest — it is monitored via
health checks, not data status.

## Data Status Page Tree Hierarchy

The deployment-ui renders a hierarchical tree per service × category. The tree structure is determined by which manifest
columns are populated.

| Service + Category      | Tree                                                     |
| ----------------------- | -------------------------------------------------------- |
| instruments CEFI/TRADFI | venue → dates                                            |
| instruments DEFI        | chain → protocol(venue) → dates                          |
| instruments SPORTS      | league → dates (fixture count)                           |
| instruments PREDICTION  | venue → dates                                            |
| MTDS CEFI/TRADFI        | venue → instrument_type → data_type → dates              |
| MTDS DEFI               | chain → protocol(venue) → data_type → dates              |
| MTDS SPORTS             | league → bookmaker(venue) → dates                        |
| MTDS PREDICTION         | venue → data_type → dates                                |
| MDPS CEFI/TRADFI        | venue → instrument_type → data_type → timeframe → dates  |
| MDPS DEFI               | chain → protocol(venue) → data_type → timeframe → dates  |
| MDPS SPORTS             | league → timeframe(horizon) → dates                      |
| Features (all)          | feature_group → [timeframe →] [chain →] [league →] dates |
| ML training             | model_family → training_period → dates                   |
| ML inference            | model_family → dates                                     |
| Strategy                | strategy → dates                                         |
| Execution               | strategy → venue → instruction_type → dates              |
| Risk                    | client → dates                                           |
| PnL                     | strategy → dates                                         |

**DeFi grouping toggle:** The UI provides a dropdown to switch between chain→protocol and protocol→chain grouping.

## Availability % Calculation

```
availability_pct = found_shards / expected_shards × 100
```

### Expected Shards (Denominator)

The denominator comes from **UAC only**. Never hardcoded in services.

| Dimension                 | UAC function                                                 | What it returns                                  |
| ------------------------- | ------------------------------------------------------------ | ------------------------------------------------ |
| Venue start date          | `VenueMapping.get_venue_start_date(venue)`                   | When a venue's data begins                       |
| Chain start date (DeFi)   | `get_venue_chain_start_date(venue, chain)`                   | When a protocol deployed on a chain              |
| Data type start date      | `get_venue_data_type_start_date(venue, data_type)`           | When a specific data type became available       |
| Expected trading dates    | `VenueMapping.get_expected_trading_dates(venue, start, end)` | Trading days only (excludes weekends for TradFi) |
| Fixture calendar (SPORTS) | `get_league_fixture_calendar(league_id, start, end)`         | Dates with actual fixtures                       |
| Expected data types       | `get_expected_data_types_for_venue(venue)`                   | Which data types a venue should produce          |
| Expected instrument types | `get_expected_instrument_types_for_venue(venue)`             | Which instrument types a venue should produce    |
| Expected bookmakers       | `get_expected_bookmakers()`                                  | Audited bookmakers with start dates              |
| Expected feature groups   | `get_expected_feature_groups_for_service(service)`           | Feature groups per service                       |
| Expected timeframes       | `get_expected_timeframes_for_service(service, category)`     | Timeframes per service+category                  |

### Sparseness

Not all shards are expected every day:

- **Sports fixtures:** A day with no fixtures in a league is NOT a missing shard. Denominator = fixture calendar.
- **TradFi weekends:** Saturday/Sunday are not trading days. Denominator = trading calendar.
- **Transfer windows:** Transfer data arrives on seasonal cadence, not daily.
- **Chain start dates:** AAVE_V3 on LINEA started much later than on ETHEREUM. Per-chain start dates.
- **New venues/bookmakers:** A bookmaker added in 2025-06 has no expected data before that date.

### Data Freshness

The `written_at` column records when each manifest entry was written. This enables:

- **Point-in-time queries:** "What data existed as of 2026-04-10 08:00 UTC?" — filter by `written_at <= timestamp`.
  Critical for reproducible backtests.
- **Staleness detection:** Shard exists but `written_at` is old — may indicate stale data.
- **Monitoring:** "What was written in the last 24h?" — freshness dashboard.

The data status page supports an `as_of_timestamp` parameter for point-in-time views.

### Expected-Empty vs Missing Shards (Phase 1.9)

The v6 schema carries enough columns to encode the four distinct states a shard can be in on a given day. The
`capture_status` column (added in v5, honest-coverage Phase A) is the canonical source — `expected` / `available` /
`instrument_count` are kept for backward compat but `capture_status` is what the data-status UI + phantom audit read
first.

| State                | Manifest row? | `capture_status`   | `instrument_count` | Meaning                                                                                                                                                                                               |
| -------------------- | ------------- | ------------------ | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ingested**         | yes           | `captured`         | `> 0`              | Real parquet on disk at the canonical path. Counts toward numerator.                                                                                                                                  |
| **Expected-empty**   | yes           | `empty_confirmed`  | `= 0`              | Source returned 200 + zero rows on this date (paused league, dated future not yet trading, lending market with no activity). Counts in denominator only.                                              |
| **Attempted-failed** | yes           | `attempted_failed` | `0`                | Adapter raised an exception classified via `error_reason`. Counts in denominator + triggers alerts. The orchestrator's `_should_skip_shard` does NOT skip these — they auto-retry on the next VM run. |
| **Missing**          | no row        | —                  | —                  | Never attempted — pipeline gap. Counts in denominator; triggers alerts. The phantom audit flips manifest rows whose `captured` claim has no matching parquet on disk to `attempted_failed`.           |

Before Phase 1.9 + Phase A we could not distinguish empty-vs-failed-vs-missing — any day without a manifest entry looked
identical whether the source was silent or the pipeline had never run. `write_with_zero_fill`

- `capture_status` together close that gap. The phantom audit
  (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` — multi-asset-group; the older
  `reconcile_phantom_manifest_rows.py` is sports-only) is the inverse process: scans canonical GCS paths, compares vs
  `captured` rows, flips drift to `attempted_failed`.

### Phantom audit — re-runnable recipe

**Script SSOT:** `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` (multi-asset-group; the older
`reconcile_phantom_manifest_rows.py` is sports-only and being phased out).

**Five drift axes the audit handles** (each one historically caused a wave of false-positive phantoms):

1. **Hive-vocab drift** — `category=` (legacy) vs `asset_group=` (post-2026-04 rename) coexist on disk; both probed.
2. **`instrument_type` casing** — manifest holds `PERPETUAL` / `perpetual` interchangeably; disk only has lowercase.
   Membership check is case-insensitive.
3. **Empty `instrument_type`** — schema-4 manifest rows omit the segment; audit accepts any disk `instrument_type`.
4. **Path-prefix drift** — Tardis/DeFi adapter writes via `build_*_partition_path` historically lived at top-level
   `day=*/...` while orchestrator-direct writes used `raw_tick_data/by_date/day=*/...`. UAC `77abd56` + MTDS `2a479ef`
   unified writes to the canonical prefix going forward; the rekeyer
   `instruments-service/scripts/migrate_rogue_root_to_raw_tick_data.py` relocates pre-existing rogue data. Audit probes
   both shapes as a safety net.
5. **Chain-bundle equivalence** — manifest `instrument_type=option` / `future` (row-level) vs disk `options_chain` /
   `futures_chain` (writer bundles them per `tardis_shared.finalise_rows_and_path`); audit accepts either form.

**Plus**: schema-v4 vestigial empty-data_type rows are filtered out of audit scope (informational pre-v5 markers, not
real shards).

**How to re-run** (must run on a same-region GCE VM — cross-region listing is 18× slower):

```bash
# 1. Spin up an e2-standard-4 VM in asia-northeast1-c (same region as the bucket)
gcloud compute instances create cefi-phantom-audit-$(date +%Y%m%d-%H%M) \
    --project=central-element-323112 --zone=asia-northeast1-c \
    --machine-type=e2-standard-4 \
    --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud \
    --boot-disk-size=50GB --scopes=cloud-platform

# 2. SSH in and bootstrap (project requires Python 3.13 — Ubuntu 24.04 ships 3.12)
gcloud compute ssh cefi-phantom-audit-$(date +%Y%m%d-%H%M) --zone=asia-northeast1-c --tunnel-through-iap --command='
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -qq && sudo apt-get install -qqy python3.13 python3.13-venv python3.13-dev
mkdir -p /tmp/repos && cd /tmp/repos
gsutil -q cp gs://deployment-scripts-central-element-323112/code/instruments-service-code.tar.gz .
tar xzf instruments-service-code.tar.gz -C instruments-service
cd instruments-service
python3.13 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet pandas pyarrow google-cloud-storage requests   # minimal deps; no UAC needed
.venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run --workers 64
'

# 3. After verifying the phantom count is reasonable, drop --dry-run to actually flip
#    rows to attempted_failed.  The script is idempotent — re-running on a clean
#    manifest is a no-op.
```

**Always **start with `--dry-run`. Compare phantom count vs prior run; investigate distribution by venue/data_type
before flipping.

**Connection-pool warning**: the script bumps the GCS HTTP pool to `2 × workers` (default 10 silently truncates
`list_blobs()` results under high concurrency — this caused 9,757 false-positive phantoms in the 2026-05-04 audit before
the fix landed).

**Asset-group cross-cuts**: the script supports `cefi`, `defi`, `tradfi`, `prediction`, `sports` via `--asset-group`.
DeFi has additional drift axes (legacy `venue=PROTOCOL-CHAIN/` overload, no-asset-group hive segment); prediction has
the 9-segment Polymarket layout. Both are encoded in `ASSET_GROUP_CONFIG.prefix_tpls`.

**History benchmark**: 2026-05-04 cefi audit reduced phantom count from 130,897 (false-positive baseline pre-fixes) →
354 real (99.7% reduction). Real phantoms were flipped to `attempted_failed` so backfill VMs auto-retry.

### Audit-script gotchas — adapter-specific path duality

Per-adapter quirks future audits MUST handle to avoid false-positive flips destroying real data:

- **Polymarket dual-schema** —
  `instruments-service/instruments_service/reference_data/adapters/prediction/polymarket.py` writes parquets at TWO path
  shapes depending on the adapter code path:
  1. **Question-format** (legacy): the file_stem is the human-readable question text
     (`will-bitcoin-cross-100k-by-end-of-2024.parquet`).
  2. **Canonical-ID format** (current): the file_stem is the Polymarket condition_id hex. Both are valid; the audit
     script must probe BOTH layouts before flagging a manifest row as phantom. Reference incident (plan
     `instruments_to_100pct_eod_2026_05_04.plan.md` lines 2540, 2659, 2692): a Phase-1 audit pass that only knew about
     the question-format would have destroyed 401 legitimate canonical-ID rows. Word-boundary keyword matchers in audit
     scripts must also handle this — `arch*` was over-aggressive across the question-format text and flagged 388
     legitimate market records before being narrowed (commit `b336834` word-boundary fix + `d7bd17f` hybrid
     long-form/short-ticker matcher). Always probe + assert on a sample BEFORE running `--apply`.
- **Sports per-league subpartition fallback** — `entity={F}/league={L}/{F}.parquet` first, bare `entity={F}/{F}.parquet`
  fallback (per `unified_api_contracts.sports.candidate_parquet_paths`). Same SSOT, two on-disk shapes; the canonical
  helper returns the ordered probe list.
- **PLAYER_VALUES per-day-per-season layout** — Transfermarkt team values land in ONE bulk parquet per (date, season) at
  `entity=player_values/season={S}/player_values.parquet`, NOT at the per-league-subpartition path. The `season` segment
  is a real partition dimension because near transfer windows old + new season values legitimately co-exist for the same
  day. Layout token: `SportsPathLayout.PER_DAY_PER_SEASON`. League filtering happens INTRA-FILE on the
  `canonical_league` column. **Reference incident 2026-05-05**: pre-fix UAC had
  `SPORTS_DATA_TYPE_TO_FOLDER["PLAYER_VALUES"] = "transfermarkt_teams"` with `PER_DAY_PER_LEAGUE` — never matched the
  writer; audit false-flagged every captured row as phantom; a band-aid script (`write_player_values_placeholders.py`,
  deleted 2026-05-05) wrote 906 zero-row placeholders to mask the drift. Aligned via UAC `gcs_paths.py` change +
  manifest rebuild (8,937 legacy denorm rows → 15,002 honest captured rows derived from disk truth at
  `entity=player_values/season=*/`). Lock test:
  `unified-api-contracts/tests/unit/sports/test_gcs_paths_player_values.py`. The `candidate_parquet_paths` helper probes
  a 3-year season window when no explicit `season` is passed (covers transfer-window overlap).
- **DeFi venue-overload + chain-bundle** — already encoded in `reconcile_phantom_manifest_rows_all.py` 5-axis drift
  handling (path-prefix, chain-bundle equivalence, hive-vocab, instrument_type casing, schema-v4 empty).

When adding a new adapter, document any path duality here BEFORE merging the writer — silent dual-schemas are the
canonical phantom-audit blast radius.

### Mechanism: `ManifestWriter.write_with_zero_fill`

Location: `unified-trading-library/unified_trading_library/manifest_writer.py:329`.

```python
zero_filled = writer.write_with_zero_fill(
    actual_records,                # list[AvailabilityRecord] — rows produced this run
    expected_catalogue=catalogue,  # Iterable[InstrumentRecord] — from instruments-service
    ref_date=date(2026, 4, 17),
    category="cefi",
    venue="BINANCE_FUTURES",
    instrument_type="perpetual",
    chain=None,
    data_type="trades",
)
```

Flow:

1. Delegates to UAC `get_instruments_available_on(ref_date, catalogue, ...)` to compute which catalogue members were
   in-window on `ref_date` under the given scope filters.
2. Any expected instrument (matched by `InstrumentRecord.instrument_key` ↔ `AvailabilityRecord.instrument_id`) that is
   NOT in `actual_records` gets a zero-fill row appended with `instrument_count=0`, `expected=True`, `available=False`.
3. Actual records override — a real ingestion with `instrument_count==0` stays as the caller wrote it; no zero-fill is
   appended for that id.

The `instruments-service` catalogue (see `instruments-service/docs/instrument-catalogue.md`) is the canonical source for
`expected_catalogue`. MTDS, features-\*, and ML services load it via UTL and feed it into their per-shard
`write_with_zero_fill` call.

## Integrity Principles

### 1. Atomic Shard Failure

If ANY item in a shard fails, the ENTIRE shard must fail. `ManifestWriter.add()` is only called after the complete shard
write succeeds. No partial writes, ever.

**Why:** A human looking at the data status page must trust that "shard present = shard complete". Partially written
shards create false confidence.

**Enforcement:** Services validate all items in a shard before writing any. If 1 of 100 instruments in a venue×date
shard fails, write 0 and mark the shard as failed.

### 2. Schema Validation Before Write

`ParquetSchemaEnforcer` runs before every GCS write. Checks: no NaN values, correct column types, required columns
present. Schema failure = shard failure = no write = shows as missing on data status page.

**Why:** Millions of parquet files. No human can inspect them all. Schema validation + atomic shards = confidence
without manual inspection.

### 3. Single SSOT for Registry — UAC Only

What venues exist, what chains exist, what data types exist, what feature groups exist, when each became available — ALL
of this comes from UAC. No service has hardcoded lists. No service tries to get data before a venue's start date.

**Why:** If 5 services have 5 different ideas of when AAVE_V3 on BASE became available, some will try to fetch data that
doesn't exist, and the data status page will show false negatives.

## DeFi Protocol × Chain Coverage

30 protocols × 11 chains = 57 venue combos. Key coverage:

| Chain       | Protocol Count | Examples                                                                                       |
| ----------- | -------------- | ---------------------------------------------------------------------------------------------- |
| ETHEREUM    | 16             | AAVE_V3, UNISWAP_V3, UNISWAP_V4, CURVE, BALANCER, COMPOUND_V3, MORPHO, LIDO, ETHERFI, ...      |
| BASE        | 8              | AAVE_V3, UNISWAP_V3, BALANCER, AERODROME_V3, COMPOUND_V3, MORPHO, PANCAKESWAP_V3, SUSHISWAP_V3 |
| ARBITRUM    | 7              | AAVE_V3, UNISWAP_V3, BALANCER, COMPOUND_V3, CAMELOT_V3, SUSHISWAP, GMX                         |
| AVALANCHE   | 6              | AAVE_V3, BALANCER, CURVE, SUSHISWAP_V3, TRADER_JOE_V2, GMX                                     |
| OPTIMISM    | 6              | AAVE_V3, UNISWAP_V3, BALANCER, COMPOUND_V3, CURVE, VELODROME_V2                                |
| SOLANA      | 6              | DRIFT, KAMINO, RAYDIUM, ORCA, MARINADE, JITO                                                   |
| POLYGON     | 3              | AAVE_V3, UNISWAP_V3, BALANCER                                                                  |
| BSC         | 2              | AAVE_V3, PANCAKESWAP_V3                                                                        |
| LINEA       | 1              | AAVE_V3                                                                                        |
| HYPERLIQUID | 1              | HYPERLIQUID                                                                                    |
| ASTER       | 1              | ASTER                                                                                          |

Top multi-chain protocols: AAVE_V3 (8 chains), BALANCER (6), UNISWAP_V3 (5).

## Sports Bookmaker Venues (~21 Audited)

These are the actual pricing venues for sports odds. "ODDS_API" is the data aggregator, NOT a venue.

**Removed bookmakers:** Smarkets, Betdaq, and OddsJam have been removed from all repos. No manifest rows exist for these
venues and they must not appear in UAC registry functions or expected-shard calculations.

| Bookmaker    | Accuracy            | Execution?                        |
| ------------ | ------------------- | --------------------------------- |
| PINNACLE     | 99% exact           | No (API restricted)               |
| BETFAIR_EX   | Exchange            | **Yes** (current execution venue) |
| FANDUEL      | 100% exact          | No                                |
| CORAL        | 100% exact          | No                                |
| PADDYPOWER   | 100% exact          | No                                |
| WILLIAMHILL  | Audited             | No                                |
| LADBROKES    | Audited             | No                                |
| DRAFTKINGS   | 86% exact           | No                                |
| BETRIVERS    | 92% exact           | No                                |
| BETONLINEAG  | Audited clean       | No                                |
| CASUMO       | 96% exact           | No                                |
| VIRGINBET    | 97% exact           | No                                |
| BETVICTOR    | Audited             | No                                |
| UNIBET       | 66% exact           | No                                |
| SKYBET       | Audited             | No                                |
| BET888SPORT  | Audited             | No                                |
| LIVESCOREBET | Audited             | No                                |
| MATCHBOOK    | Exchange, consensus | Yes (adapter exists)              |
| BETFAIR_SB   | Sportsbook variant  | No                                |
| UNIBET_UK    | Audited             | No                                |

## Migration history

### v3 → v4 (Phase 1 — venue/chain/instrument_type/league_id columns)

- **No data re-downloads.** All data already exists in GCS. The manifest is just an index.
- **GCS paths do NOT need to change.** The manifest is an abstraction layer over GCS paths. Old data stays at old paths
  (e.g., `venue=ODDS_API/league=EPL/`). New manifest entries normalize to v4 columns (venue=PINNACLE, league_id=EPL).
  The deployment-api reads the manifest, not GCS paths. GCS path changes are optional future optimization, not a
  migration requirement.
- **Backward compat in reader:** `read_availability_index()` backfills missing v4 columns with `""`.
- **v4 writes coexist with v3 entries** until re-scanned.
- **Re-scan existing data:** Run `rebuild_*_manifest.py` scripts per service. Scans existing GCS paths, extracts new
  columns from path structure (instrument_type from hive path, chain from folder names), writes v4 index.
- **Dedup on write:** v4 entries supersede v3 entries for the same shard.

### v4 → v5 (honest-coverage Phase A, 2026-04-19)

- Adds `capture_status` (`captured` / `empty_confirmed` / `attempted_failed`), `error_reason`, `attempted_at`.
- Adapters MUST distinguish empty-vs-failed: `record_empty(row_key=...)` for legitimately-zero-rows,
  `record_failed(row_key=..., error=classify_venue_error(exc))` for exceptions.
- Reader backfills missing columns: `capture_status="captured"` (preserves old semantics where presence of a row implied
  success), `error_reason=""`, `attempted_at=""`.

### v5 → v6 (quote_margin_combo plan, 2026-04-23)

- Adds `quote_asset`, `margin_type`, `combo_type`, `leg_weights`.
- The v5 primary key `(date, venue, instrument_type, data_type, underlying)` collided DERIBIT inverse and linear bundles
  into the same parquet (BTC-PERPETUAL vs BTC_USDC-PERPETUAL on the same underlying = BTC). v6 extends the key to
  `(..., quote_asset, margin_type)` so the bundles stay separate.
- Reader backfills `quote_asset=""`, `margin_type=""`, `combo_type=""`, `leg_weights=""` for v4/v5 rows.

## Per-VM shard layout (Phase 1, manifest_429_per_vm_sharding plan)

When `UnifiedCloudConfig.manifest_per_vm_shards` is True (env var `MANIFEST_PER_VM_SHARDS=true`), or when a writer is
constructed with `ManifestWriter(per_vm_shards=True, ...)` — the explicit kwarg added 2026-05-03 — `ManifestWriter`
writes to `_index/per_vm/{instance}.parquet` instead of CAS-writing the canonical `_index/availability_index.parquet`.
The `manifest_consolidator` daemon (Cloud Scheduler `*/1 * * * *`) merges per-VM shards into the canonical view; readers
fall back to a live shard-merge when the canonical blob is older than `MANIFEST_CONSOLIDATED_STALENESS_SEC` (default
120s).

**When to use:**

- Backfill VM fleets with 10+ writers per bucket (eliminates 429 thundering-herd on the canonical CAS path).
- One-off `rebuild_*_manifest.py` scripts: pass `per_vm_shards=True` to skip CAS contention with concurrent rebuilds /
  the consolidator daemon. Without this, OCC `generation_match` retries can re-merge stale views and drop most of the
  rebuild's output (observed 2026-05-02 on DeFi: 80k mid-run rows compacted to 12k canonical).
- Local multi-process rebuilds where every process inherits the same `HOSTNAME` — set a unique `VM_NAME` per chunk
  worker so they each get their own per-VM shard (not a shared one).

**Force-merge after a rebuild:**

```bash
python -m unified_trading_library.manifest_consolidator --bucket market-data-tick-{ag}-{pid}
```

Idempotent + safe to run concurrently with the scheduled cycle.
