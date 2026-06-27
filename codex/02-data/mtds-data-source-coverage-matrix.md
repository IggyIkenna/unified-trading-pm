---
scope: [engineer, admin]
last_reviewed: 2026-05-17
---

# Market-Tick-Data-Service (MTDS) — Coverage Matrix SSOT

**Status:** canonical — consumed by deployment-api data-status aggregator (MTDS branches), MTDS adapter audits, and
downstream coverage dashboards. Sibling doc to `sports-data-source-coverage-matrix.md`.

**Scope:** for every `(category, venue, data_type)` that MTDS writes to the availability manifest, defines (a) the
responsible adapter, (b) the expected `(venue, data_type, instrument_type)` shard set, (c) the coverage axis, (d)
whether `record_empty` is expected.

Cross-refs:

- `codex/02-data/availability-manifest-and-data-status.md` — §Layer 2 table + v5 honest-coverage schema + UAC
  denominator accessors. **Also the canonical literal-values mirror for `SOURCE_COVERAGE_START` /
  `DATA_TYPE_COVERAGE_START`** (sports + `odds_api` source coverage starts) — this doc cross-links, never redeclares the
  dates.
- `codex/02-data/sports-data-source-coverage-matrix.md` — sibling (SPORTS instruments-service).
- `codex/02-data/per-asset-group-bucket-layouts.md` — MTDS GCS path layouts per asset_group.
- `codex/02-data/partitioning.md` — Hive partitioning (venue / date / data_type / instrument_type / chain / league_id).
- UAC: `unified_api_contracts.registry.venue_mapping.VenueMapping` — `all_cefi_venues`, `all_databento_venues`,
  `all_defi_venues`, `get_venue_start_date`, `is_venue_available_on_date`, `get_expected_trading_dates`.
- UAC: `unified_api_contracts.sports.SOURCE_COVERAGE_START` / `DATA_TYPE_COVERAGE_START` — runtime SSOT for sports +
  odds_api source-coverage-start dates; literal-values mirror in the availability-manifest doc above.
- UAC: `unified_api_contracts.get_expected_data_types_for_venue(venue)` — per-venue expected data_types.
- UAC: `unified_api_contracts.get_venue_data_type_start_date(venue, data_type)` — per-(venue, data_type) start date.

## 1. Expected-venue counts per category (observed from UAC 2026-04-20)

These counts are live-derived from `VenueMapping` and are the authoritative denominator for data-status coverage %:

| Category       |                      Venues (expected) | Chain axis | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| -------------- | -------------------------------------: | :--------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CEFI**       |                            17 distinct |     no     | ASTER, BINANCE-SPOT, BINANCE-FUTURES, BITFINEX-SPOT, BITFINEX-FUTURES, BITGET-SPOT, BITGET-FUTURES, BYBIT, COINBASE-SPOT, DERIBIT, HYPERLIQUID, KRAKEN-SPOT (no data yet — backfill pending), KRAKEN-FUTURES (no data yet), OKX-SPOT, OKX-FUTURES, OKX-SWAP, UPBIT                                                                                                                                                                                                                           |
| **TRADFI**     |                                      6 |     no     | CBOE, CME, FX, ICE, NASDAQ, NYSE                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **DEFI**       | 60 entries (flat + legacy VENUE-CHAIN) | per-chain  | Two naming eras coexist — see note below. Flat (current): UNISWAP_V3, AAVE_V3, COMPOUND_V3, MORPHO, FLUID, BALANCER, CURVE, LIDO, ETHERFI, ETHENA, ROCKETPOOL, STADER, ANKR, JITO etc. Legacy VENUE-CHAIN (411k rows migrated 2026-05-07): UNISWAP_V3-ETHEREUM, AAVE_V3-ETHEREUM, BALANCER-ETHEREUM, LIDO-ETHEREUM etc. Both sets registered in `expected_coverage._DEFI`. Ghost venues (UNISWAP_V3 no-underscore era-2) tracked: `issues/defi_coverage_capability_alignment_2026_05_22.md`. |
| **SPORTS**     |                         ~23 bookmakers |     no     | PINNACLE, BETFAIR_EX, DRAFTKINGS, FANDUEL, CORAL, PADDYPOWER, WILLIAMHILL, BET365, UNIBET, MARATHONBET, … — enumerate via `get_expected_bookmakers()`                                                                                                                                                                                                                                                                                                                                        |
| **PREDICTION** |                                      2 |     no     | POLYMARKET, KALSHI                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

**UAC gaps — resolved 2026-04-20 in Phase 6b:**

- COINBASE-SPOT, OKX-SPOT, OKX-FUTURES, OKX-SWAP now have explicit suffixed entries in `VENUE_DATA_TYPE_CAPABILITIES`.
  The bare `OKX` / `COINBASE` keys are retained for execution-context and client-config callers that don't split by
  market; MTDS uses the suffixed forms.
- `HYPERLIQUID` deduplicated in `VenueMapping.all_cefi_venues` — now returns a sorted
  `set(tardis_to_venue.values()) | set(all_cefi_onchain_clob_venues)` (11 unique venues, was 12 with duplicate).

**Remaining design notes (not bugs):**

- PREDICTION venues declare only `trades` by design. Legacy `prediction_trades` name retired 2026-04-19 for
  cross-category alignment. `book_snapshot_5` was intentionally removed at the same time — neither the Polymarket CLOB
  adapter nor the Kalshi adapter captures book snapshots, and declaring them phantom-inflated the MTDS PREDICTION
  completion denominator (35k expected vs ~5.7k observable). Re-add when + if either adapter grows a book-snapshot
  collection path. `prediction_market_metadata` lives in the `instrument_availability` index (not `market_tick_data`)
  because the instruments parquet IS the metadata.
- **DEFI venue naming — two eras coexist in manifest** (2026-05-22): Era 1/3 (current handlers): `protocol.upper()` +
  chain as separate field → e.g. `venue="UNISWAP_V3" chain="ETHEREUM"`. Era 2 (post-migration 2026-05-07): 411k rows
  with embedded chain → `venue="UNISWAP_V3-ETHEREUM" chain=""`. Both registered in `expected_coverage._DEFI`. Ghost
  era-2 no-underscore rows (UNISWAP_V3, AAVE_V3 without chain suffix) require phantom reconciler; tracked in
  `plans/active/issues/defi_coverage_capability_alignment_2026_05_22.md` Bug 3.
- **DEFI handler naming inconsistency** (Bug 2 OPEN): `evm_defi_handler` writes `AAVE_V3` (underscore);
  `flash_loan_events_handler` and `position_data_handler` hardcode `AAVE_V3` (no underscore). Both in manifest as
  separate venues. Fix: normalise all to `AAVE_V3`. Tracked in issue doc above.
- DEFI multi-chain legacy entries (`AAVE_V3-ARBITRUM`, `AAVE_V3-BASE`, etc.) now in `expected_coverage._DEFI` (flat
  variants for current handlers + VENUE-CHAIN variants for 411k migrated rows).

## 2. CEFI — per venue × data_type matrix

Expected leagues: N/A (no league axis). Expected dates: `VenueMapping.get_expected_trading_dates(venue, start, end)` —
crypto trades 24/7, so daily grid = all days in `[max(start, venue_start_date), end]`. Instrument_type axis: SPOT_PAIR,
PERPETUAL, FUTURE, OPTION (per-instrument shard for `derivative_ticker` / `options_chain` / `futures_chain`; per-venue
single shard for `trades` / `book_snapshot_5`).

| venue           | expected data_types (UAC)                                                              | adapter (live / batch)   |
| --------------- | -------------------------------------------------------------------------------------- | ------------------------ |
| ASTER           | book_snapshot_5, derivative_ticker, liquidations, trades                               | aster (REST + WS)        |
| BINANCE-SPOT    | book_snapshot_5, trades                                                                | tardis / binance-spot    |
| BINANCE-FUTURES | book_snapshot_5, derivative_ticker, futures_chain, liquidations, trades                | tardis / binance-futures |
| BYBIT           | book_snapshot_5, derivative_ticker, futures_chain, liquidations, trades                | tardis / bybit           |
| COINBASE-SPOT   | book_snapshot_5, trades                                                                | coinbase-spot            |
| DERIBIT         | book_snapshot_5, derivative_ticker, futures_chain, liquidations, options_chain, trades | tardis / deribit         |
| HYPERLIQUID     | book_snapshot_5, derivative_ticker, liquidations, trades                               | hyperliquid direct       |
| OKX-SPOT        | book_snapshot_5, trades                                                                | tardis / okx-spot        |
| OKX-FUTURES     | book_snapshot_5, derivative_ticker, trades                                             | tardis / okx-futures     |
| OKX-SWAP        | book_snapshot_5, derivative_ticker, liquidations, trades                               | tardis / okx-swap        |
| UPBIT           | book_snapshot_5, trades                                                                | tardis / upbit           |

### CEFI coverage axes

| data_type           | Coverage axis                      | Expected shards (per day)                                                    | `record_empty` expected                                                     |
| ------------------- | ---------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `trades`            | per-venue × per-instrument × daily | venues_with_support × instruments_per_venue (MVP set ~ top N pairs from UAC) | Yes — zero-trade day on an inactive perp = `capture_status=empty_confirmed` |
| `book_snapshot_5`   | per-venue × per-instrument × daily | same as `trades`                                                             | Yes                                                                         |
| `derivative_ticker` | per-venue × per-perp × daily       | perp venues × perp instruments                                               | Yes                                                                         |
| `liquidations`      | per-venue × daily                  | perp venues × 1 shard/day                                                    | Yes — quiet day with no liquidations = empty_confirmed                      |
| `futures_chain`     | per-venue × per-root × daily       | futures venues × root contracts (e.g. BTC/ETH quarterlies)                   | Yes                                                                         |
| `options_chain`     | per-venue × per-underlying × daily | options venues × underlyings × expiries × strikes (expanded at write-time)   | Yes                                                                         |

## 3. TRADFI — per venue × data_type matrix

**OHLCV-only MVP (operator direction 2026-05-15)** — see `plans/active/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md`.
`trades` + `tbbo` (L1/L2 tick data) moved to post-cutover; only `ohlcv_1m` (cheap pre-aggregated bars) collected in MVP.
`TRADFI_TICK_DATA_WINDOWS = []` in UAC (`unified_api_contracts/registry/market_data_categories.py`) —
`is_in_tradfi_tick_window()` returns False for every date, suppressing every tbbo/trades fetch attempt in MTDS
orchestrator.py:3014. Historical windows preserved in `_DEFERRED_TRADFI_TICK_DATA_WINDOWS` (list-shape, mirrors the
TRADFI_TICK_DATA_WINDOWS shape) and `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` (dict-shape, mirrors
VENUE_DATA_TYPE_COVERAGE_WINDOWS — preserves the CME tbbo + CME mbp_10 reference windows). Both restored by post-cutover
plan (`tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md`).

Expected dates: `VenueMapping.get_expected_trading_dates(venue, start, end)` — **trading days only** (no weekends,
holidays excluded). Instrument_type axis: equity, futures_chain, options_chain, index.

| venue  | expected data_types | notes                                                                                                                   |
| ------ | ------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| CBOE   | ohlcv_15m           | Options index — limited subscription                                                                                    |
| CME    | ohlcv_1m            | Databento GLBX.MDP3; genesis floor **2020-01-01**; options_chain + futures_chain via instruments-service                |
| FX     | ohlcv_24h           | Daily only (cost envelope); floor 2020-01-01                                                                            |
| ICE    | (DXY only)          | **Yahoo Finance DXY, NOT Databento** (IFUS/IFEU out of subscription, UAC@5480f5d5). ICE Brent/Gasoil = subscription ask |
| NASDAQ | ohlcv_1m            | Equity venue (Databento floor 2023-04-15)                                                                               |
| NYSE   | ohlcv_1m            | Equity venue (Databento floor 2023-04-15)                                                                               |

### TRADFI coverage axes

| data_type   | Coverage axis                                              | Expected shards (per trading day)    | `record_empty` expected                                                                   |
| ----------- | ---------------------------------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------- |
| `trades`    | DEFERRED-post-cutover (was: per-venue × per-instr × daily) | n/a (suppressed via empty windows)   | n/a — fetch suppressed entirely; existing rows re-classified by Phase 5 phantom-reconcile |
| `tbbo`      | DEFERRED-post-cutover (was: per-venue × per-instr × daily) | n/a (suppressed via empty windows)   | n/a — same as `trades`                                                                    |
| `ohlcv_1m`  | per-venue × per-instrument × daily                         | venues × active equities / contracts | Yes — halted instruments = empty_confirmed                                                |
| `ohlcv_15m` | per-venue × per-instrument × daily                         | CBOE × options index                 | Yes                                                                                       |
| `ohlcv_24h` | per-venue × per-pair × daily                               | FX × G10 crosses                     | Yes                                                                                       |

## 4. DEFI — per venue × data_type matrix (venue = `PROTOCOL-CHAIN`)

Expected dates: daily grid from `get_venue_start_date(venue)` (each protocol-chain has its own deployment date).
Instrument_type axis: POOL (DEX), LENDING (Aave/Morpho/Compound/Fluid), LST (Lido/Ether.fi/Ethena).

| venue               | expected data_types                                  | instrument_type category |
| ------------------- | ---------------------------------------------------- | ------------------------ |
| AAVE_V3-ETHEREUM    | lending_indices, oracle_prices, rewards, risk_params | LENDING                  |
| BALANCER-ETHEREUM   | dex_pools, dex_swaps                                 | POOL                     |
| CURVE-ETHEREUM      | dex_pools, dex_swaps                                 | POOL                     |
| ETHENA-ETHEREUM     | lst_rates, oracle_prices                             | LST                      |
| ETHERFI-ETHEREUM    | lst_rates, oracle_prices                             | LST                      |
| FLUID-ETHEREUM      | lending_indices, oracle_prices                       | LENDING                  |
| LIDO-ETHEREUM       | lst_rates, oracle_prices                             | LST                      |
| MORPHO-ETHEREUM     | lending_indices, oracle_prices                       | LENDING                  |
| UNISWAP_V2-ETHEREUM | dex_pools, dex_swaps                                 | POOL                     |
| UNISWAP_V3-ETHEREUM | dex_pools, dex_swaps                                 | POOL                     |
| UNISWAP_V4-ETHEREUM | dex_pools, dex_swaps                                 | POOL                     |

### DEFI coverage axes

| data_type         | Coverage axis                              | Expected shards (per day)                  | `record_empty` expected                                |
| ----------------- | ------------------------------------------ | ------------------------------------------ | ------------------------------------------------------ |
| `dex_swaps`       | per-venue × per-pool × per-chain × daily   | venues (DEX) × active pools (TVL-gated)    | Yes — dead pools with no swaps = empty_confirmed       |
| `dex_pools`       | per-venue × per-pool × per-chain × daily   | same, snapshot of pool metadata            | Yes                                                    |
| `lending_indices` | per-venue × per-market × per-chain × daily | lending protocols × reserves               | Yes                                                    |
| `oracle_prices`   | per-venue × per-asset × per-chain × daily  | price-feed providers × assets              | Yes                                                    |
| `lst_rates`       | per-venue × per-token × per-chain × daily  | LST providers × tokens (stETH, eETH, USDe) | Yes                                                    |
| `rewards`         | per-venue × per-market × per-chain × daily | Aave rewards tracking                      | Yes — markets without active rewards = empty_confirmed |
| `risk_params`     | per-venue × per-market × per-chain × daily | lending protocols × reserves               | Yes — immutable params period = empty_confirmed        |

**Multi-chain expansion (future):** each protocol that deploys on Arbitrum / Base / Optimism / Polygon / BSC / Avalanche
/ Linea / Solana will register as `PROTOCOL-<CHAIN>` in UAC. Aggregator groups by (chain, venue) → data_types.

## 5. SPORTS (MTDS — odds from bookmakers)

Expected bookmakers: `get_expected_bookmakers()` — ~23 bookmakers with per-bookmaker start dates.

| data_type | Coverage axis                                 | Expected shards (per day)                                                       | `record_empty` expected                                                                     |
| --------- | --------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `odds`    | per-league × per-bookmaker × per-fixture-date | league × bookmaker × fixture_calendar(league) — only dates with fixtures in UAC | Yes — bookmaker went dark for a match = `attempted_failed` (don't use empty_confirmed here) |

Because SPORTS MTDS is per-league × per-bookmaker × per-fixture-date, the aggregator needs `get_league_fixture_calendar`
(already consumed by instruments-service aggregator) crossed with `get_expected_bookmakers()`.

## 6. PREDICTION — per venue × data_type matrix

| venue      | expected data_types (UAC)                                                                                               | expected data_types (manifest SSOT)                                     |
| ---------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| POLYMARKET | `trades` **(UAC incomplete — should also list prediction_book_snapshot, prediction_market_metadata per manifest SSOT)** | prediction_trades, prediction_book_snapshot, prediction_market_metadata |
| KALSHI     | `trades` **(UAC incomplete)**                                                                                           | prediction_trades, prediction_book_snapshot, prediction_market_metadata |

### PREDICTION coverage axes

| data_type                    | Coverage axis                                | Expected shards (per day)                     | `record_empty` expected                                       |
| ---------------------------- | -------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------- |
| `prediction_trades`          | per-venue × per-conditionId × daily          | venue × active conditions (event-driven)      | Yes — conditions with zero trades on a date = empty_confirmed |
| `prediction_book_snapshot`   | per-venue × per-conditionId × daily          | same                                          | Yes                                                           |
| `prediction_market_metadata` | per-venue × per-conditionId × daily snapshot | same (one metadata row per condition per day) | Yes                                                           |

**Sparseness rule:** PREDICTION is `event_driven` coverage semantics
(`COVERAGE_SEMANTICS["PREDICTION"] = "event_driven"`) — shards-weighted capture_coverage_pct vastly understates real
coverage because the denominator assumes every (conditionId × day) combo should trade. Aggregator uses
`attempt_coverage_pct` for the displayed %.

## 7. Aggregator algorithm (v5 honest-coverage) — MTDS

Two tiers depending on whether the data*type is per-instrument or venue-level. UAC
`is_per_instrument_shard_data_type(dt)` is the discriminator — returns True for `trades` / `book_snapshot_5` /
`derivative_ticker` / `options_chain` / `futures_chain` / `dex_swaps` / `dex_pools` / `lending_indices` /
`oracle_prices` / `lst_rates` / `rewards` / `risk_params` / `prediction_trades` / `prediction_book_snapshot` /
`prediction_market_metadata`. Everything else (`liquidations`, `ohlcv*\*`, `tbbo`, `gas_fees`, `perp_funding`, `odds`)
is venue-level.

```python
# From UAC + this SSOT
expected_venues = _MTDS_VENUES_BY_CATEGORY[category]            # from §1
expected_data_types = get_expected_data_types_for_venue(venue)  # UAC per-venue
for venue in expected_venues:
    for dt in expected_data_types:
        venue_start = vm.get_venue_start_date(venue)
        dt_start = get_venue_data_type_start_date(venue, dt) or venue_start
        effective_start = max(start_date, dt_start)
        if category == "TRADFI":
            expected_dates = vm.get_expected_trading_dates(venue, effective_start, end_date)
            if dt in ("trades","tbbo"):
                expected_dates = [d for d in expected_dates if is_in_tradfi_tick_window(d)]
        else:
            expected_dates = daily_grid(effective_start, end_date)
        # Tier-3 per-instrument (Phase 8C/8D): for per-instrument shards the
        # denominator is |expected_instruments| × |expected_dates| and the
        # numerator is distinct (instrument_id, date) pairs with
        # capture_status in {captured, empty_confirmed}. Instrument list
        # comes from UAC seed or a runtime provider; capped per Phase 8E
        # (--per-instrument-sentinel-cap flag; MVP=50/Expanded=200/Full=10000).
        if is_per_instrument_shard_data_type(dt):
            instruments = get_expected_instruments_for_venue(
                venue, dt, as_of_date=effective_start, cap=sentinel_cap
            )
            expected_shards = len(instruments) * len(expected_dates)
            found_shards = distinct (instrument_id, date) for (venue, dt) in manifest
            # Legacy fallback: if all matching rows have empty instrument_id
            # (pre-Phase-8C writes), degrade to Tier-2 per-(venue, dt, date)
            # denominator and surface legacy_row_count so the UI can render
            # a migration-in-progress badge.
        else:
            # Tier-2 venue-level (Phase 6d): denominator = |expected_dates|.
            found_shards = distinct (venue, dt, date) with capture_status in {captured, empty_confirmed}
        # DeFi adds chain axis; SPORTS adds (league, bookmaker, fixture_date)
        # via Phase 7 Tier-2 orchestrator fan-out.
        ratio = found_shards / max(1, expected_shards)
```

No multipliers. No cross-venue row-count comparisons. `capture_status="empty_confirmed"` counts toward `found_shards`
per v5 SSOT. Instrument universe capped per Phase 8E rollout — see `codex/02-data/per-instrument-sentinel-rollout.md`
for the 3-tier progression (MVP=50 → Expanded=200 → Full=10000) and observability gates.

## 8. Open questions / follow-ups

- ✅ **UAC gaps** (Phase 6b) — resolved: COINBASE-SPOT / OKX-SPOT / OKX-FUTURES / OKX-SWAP entries added; HYPERLIQUID
  duplicate in `all_cefi_venues` deduped.
- ✅ **DEFI multi-chain expansion** (Phase 7 #4) — 58 canonical PROTOCOL-CHAIN venues registered across 11 chains
  (ETHEREUM / ARBITRUM / BASE / OPTIMISM / POLYGON / AVALANCHE / BSC / LINEA / SCROLL / ZKSYNC / SOLANA).
  `VENUE_DATA_TYPE_CAPABILITIES` filled for every new venue. **2026-05-07 closeout:** UTL
  `ManifestWriter._coerce_row_key` + `.add()` canonicalise legacy underscore venues (`AAVE_V3 → AAVE_V3`,
  `UNISWAP_V3 → UNISWAP_V3`, …) at write time via UAC `LEGACY_DEFI_VENUE_ALIASES`; the manifest migration
  (`market_tick_data_service/scripts/migrate_mtds_defi_legacy_venue_underscore.py`) rewrote 411,620 historical rows.
  Read-time venue fallback in deployment-api removed (commit 64d2be9). Hyphenated DEFI data_types
  (`lending-indices → lending_indices`) still normalised at read-time via `_canonicalise_defi_data_types` — paired
  data_type migration is the natural follow-up. Lifted DEFI coverage from 4% to ~50% with 48/63 venues lighting up
  honestly.
- ✅ **DeFi CLI handler ManifestWriter wiring** (Phase 7 #2) — `_defi_manifest.DefiManifestRecorder` helper plus 11
  handler wires (dex_pools / dex_swaps / lending_indices / oracle_prices / lst_rates / liquidations / gas_fee /
  perp_funding / evm_defi / solana_defi / eigenlayer_rewards). Live DeFi captures now emit honest v5 manifest rows
  (captured / empty / failed-with-classification) directly, not only via rebuild scripts.
- ✅ **SPORTS per-bookmaker × per-league Tier-2 sentinel** (Phase 7 #3) — orchestrator emits
  `(bookmaker, league_id, fixture_date)` sentinel rows for the league-partitioned ODDS_API path. Size-capped to ~12
  bookmakers × 33 PREDICTION leagues × in-season fixture dates per day (~396/day vs 4M naive fan-out).
- ✅ **Instrument-level expected** (Phase 8) — shipped. Per-instrument shard data*types (`trades` / `book_snapshot_5` /
  `derivative_ticker` / `options_chain` / `futures_chain` / `dex_swaps` / `dex_pools` / `lending_indices` /
  `oracle_prices` / `lst_rates` / `rewards` / `risk_params` / `prediction*\*`) now use a `|expected_instruments| ×
  |expected_dates|`Tier-3 denominator. UAC accessor`get_expected_instruments_for_venue(venue, data_type,
  cap=N)`returns the expected instrument list. MVP seed tables now cover CEFI/TRADFI spot/perp/options **and** DEFI + PREDICTION (Wave 8G). MTDS orchestrator emits Tier-3 sentinels per`(venue,
  data_type, instrument_id,
  date)`; deployment-api aggregator reads those and computes honest coverage. Size-capped via `--per-instrument-sentinel-cap`CLI flag — see`codex/02-data/per-instrument-sentinel-rollout.md`
  for the 3-tier progression.
- ✅ **Phase 8G DeFi + PREDICTION seeds** (2026-04-20) — MVP seed tables populated in UAC
  `registry/defi_prediction_instrument_seeds.py`: top-20 UniswapV3-Ethereum pools (by TVL from live
  `dex-pools-central-element-323112`), top-10 AaveV3-Ethereum reserves (`USDC`, `USDT`, `DAI`, `WETH`, `WBTC`, `AAVE`,
  `LINK`, `USDe`, `wstETH`, `weETH` from live `lending-indices-central-element-323112`), per-protocol LST tokens (LIDO →
  `stETH`/`wstETH`, ETHERFI → `eETH`/`weETH`, ETHENA → `USDe`/`sUSDe` from live `lst-rates-central-element-323112`), and
  top-10 Polymarket BTC conditionIds (from live `instruments-store-prediction-central-element-323112`). KALSHI seed
  intentionally empty — no bucket observed. `get_expected_instruments_for_venue` now returns non-empty lists for these
  DEFI + PREDICTION paths; Phase 8 Tier-3 denominator lifts honestly (completion % drops as expected — denominator up,
  numerator unchanged).
- ⏳ **HYPERLIQUID with chain=''** in perp-funding bucket — routing inconsistency; currently lands outside the
  `(venue=HYPERLIQUID, chain=HYPERLIQUID)` canonical form. Cosmetic but worth investigation when the perp adapter is
  next touched.

## 9. Changelog

- **2026-04-20** — Initial SSOT. Authored as Phase 6a of the SPORTS data-status overhaul — applies the same
  honest-coverage discipline (no FIXTURES-rowcount-as-denominator) to MTDS across CEFI / TRADFI / DEFI / SPORTS /
  PREDICTION. Matrix supersedes any implicit per-category coverage rules previously scattered in MTDS adapters.
- **2026-04-21** — Phase 7 closeout. DEFI multi-chain expansion (58 canonical venues), DeFi handler MW wiring (11
  handlers), SPORTS per-bookmaker × per-league Tier-2 sentinel, and hyphen→underscore data_type canonicalisation in the
  aggregator all landed. Live DEFI honest coverage moved 4% → 50%. Follow-ups narrowed to per-instrument sentinels
  (Phase 8) and VM FIXTURES backfill (operator work — script
  `instruments-service/scripts/rescan_sports_fixtures_canonical.py`).
- **2026-04-21** — Phase 8 closeout. Tier-3 per-instrument sentinel fan-out shipped across MTDS orchestrator (commit
  `2947dd2`) + deployment-api aggregator (`c059e6f`); UAC `get_expected_instruments_for_venue` +
  `is_per_instrument_shard_data_type` accessors landed (`74e278c`); `--per-instrument-sentinel-cap` CLI flag wired with
  3-tier rollout doc at `codex/02-data/per-instrument-sentinel-rollout.md` (MTDS `629e414c` + PM `4cc0ce7a`).
  Per-instrument denominator replaces the per-(venue, data*type, date) shard axis for 15 per-instrument data_types;
  venue-level data_types (liquidations, ohlcv*\*, tbbo, gas_fees, perp_funding, odds) stay on Tier-2. Remaining
  follow-ups: Wave 8G DeFi + PREDICTION seed tables, and VM FIXTURES backfill.
- **2026-04-20** — Wave 8G closeout. DEFI + PREDICTION MVP seed tables landed in UAC
  `registry/defi_prediction_instrument_seeds.py` (new module — top-20 UNIv3-ETH pools, top-10 AaveV3-ETH reserves,
  per-protocol LST tokens for LIDO/ETHERFI/ETHENA, top-10 Polymarket BTC conditionIds). Values sourced from live
  `central-element-323112` buckets (`dex-pools`, `lending-indices`, `lst-rates`, `instruments-store-prediction`). KALSHI
  seed left empty — no live bucket observed. 15 new Wave 8G tests added to `tests/unit/test_mtds_venue_coverage.py`.
  Last ⏳ follow-up in § 8 flipped to ✅.
