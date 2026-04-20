# Market-Tick-Data-Service (MTDS) — Coverage Matrix SSOT

**Status:** canonical — consumed by deployment-api data-status aggregator (MTDS branches), MTDS adapter audits, and
downstream coverage dashboards. Sibling doc to `sports-data-source-coverage-matrix.md`.

**Scope:** for every `(category, venue, data_type)` that MTDS writes to the availability manifest, defines (a) the
responsible adapter, (b) the expected `(venue, data_type, instrument_type)` shard set, (c) the coverage axis, (d)
whether `record_empty` is expected.

Cross-refs:

- `codex/02-data/availability-manifest-and-data-status.md` — §Layer 2 table + v5 honest-coverage schema + UAC
  denominator accessors.
- `codex/02-data/sports-data-source-coverage-matrix.md` — sibling (SPORTS instruments-service).
- `codex/02-data/per-category-bucket-layouts.md` — MTDS GCS path layouts per category.
- `codex/02-data/partitioning.md` — Hive partitioning (venue / date / data_type / instrument_type / chain / league_id).
- UAC: `unified_api_contracts.registry.venue_mapping.VenueMapping` — `all_cefi_venues`, `all_databento_venues`,
  `all_defi_venues`, `get_venue_start_date`, `is_venue_available_on_date`, `get_expected_trading_dates`.
- UAC: `unified_api_contracts.get_expected_data_types_for_venue(venue)` — per-venue expected data_types.
- UAC: `unified_api_contracts.get_venue_data_type_start_date(venue, data_type)` — per-(venue, data_type) start date.

## 1. Expected-venue counts per category (observed from UAC 2026-04-20)

These counts are live-derived from `VenueMapping` and are the authoritative denominator for data-status coverage %:

| Category       | Venues (expected) | Chain axis | Notes                                                                                                                                                                                             |
| -------------- | ----------------: | :--------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CEFI**       |       11 distinct |     no     | ASTER, BINANCE-SPOT, BINANCE-FUTURES, BYBIT, COINBASE-SPOT, DERIBIT, HYPERLIQUID, OKX-SPOT, OKX-FUTURES, OKX-SWAP, UPBIT                                                                          |
| **TRADFI**     |                 6 |     no     | CBOE, CME, FX, ICE, NASDAQ, NYSE                                                                                                                                                                  |
| **DEFI**       |                11 | per-chain  | AAVEV3-ETHEREUM, BALANCER-ETHEREUM, CURVE-ETHEREUM, ETHENA-ETHEREUM, ETHERFI-ETHEREUM, FLUID-ETHEREUM, LIDO-ETHEREUM, MORPHO-ETHEREUM, UNISWAPV2-ETHEREUM, UNISWAPV3-ETHEREUM, UNISWAPV4-ETHEREUM |
| **SPORTS**     |    ~23 bookmakers |     no     | PINNACLE, BETFAIR_EX, DRAFTKINGS, FANDUEL, CORAL, PADDYPOWER, WILLIAMHILL, BET365, UNIBET, MARATHONBET, … — enumerate via `get_expected_bookmakers()`                                             |
| **PREDICTION** |                 2 |     no     | POLYMARKET, KALSHI                                                                                                                                                                                |

**Known UAC gaps** (observed 2026-04-20 — flagged for fix in Phase 6b):

- COINBASE-SPOT, OKX-SPOT, OKX-FUTURES, OKX-SWAP currently return `[]` from `get_expected_data_types_for_venue()` —
  registry under-specified. Aggregator cannot compute expected shards until UAC is completed.
- PREDICTION venues return only `trades`; manifest SSOT §Layer 2 lists `prediction_trades`, `prediction_book_snapshot`,
  `prediction_market_metadata`. UAC needs to carry the specialised names.
- DEFI venues use `PROTOCOL-CHAIN` canonical names (`AAVEV3-ETHEREUM`). The chain axis is currently implicit in the
  venue name — separate `chain` shard column exists in the manifest for multi-chain protocols; canonical form for
  multi-chain expansion is `AAVEV3-ARBITRUM`, `AAVEV3-BASE`, etc. (not yet in registry — follow-up).
- `HYPERLIQUID` appears twice in `VenueMapping.all_cefi_venues` — dedup required at the aggregator (possibly two
  variants: CLOB vs centralised-futures). Confirm + dedup in UAC.

## 2. CEFI — per venue × data_type matrix

Expected leagues: N/A (no league axis). Expected dates: `VenueMapping.get_expected_trading_dates(venue, start, end)` —
crypto trades 24/7, so daily grid = all days in `[max(start, venue_start_date), end]`. Instrument_type axis: SPOT_PAIR,
PERPETUAL, FUTURE, OPTION (per-instrument shard for `derivative_ticker` / `options_chain` / `futures_chain`; per-venue
single shard for `trades` / `book_snapshot_5`).

| venue           | expected data_types (UAC)                                                                | adapter (live / batch)   |
| --------------- | ---------------------------------------------------------------------------------------- | ------------------------ |
| ASTER           | book_snapshot_5, derivative_ticker, liquidations, trades                                 | aster (REST + WS)        |
| BINANCE-SPOT    | book_snapshot_5, trades                                                                  | tardis / binance-spot    |
| BINANCE-FUTURES | book_snapshot_5, derivative_ticker, futures_chain, liquidations, trades                  | tardis / binance-futures |
| BYBIT           | book_snapshot_5, derivative_ticker, futures_chain, liquidations, trades                  | tardis / bybit           |
| COINBASE-SPOT   | **(UAC empty — FIX)** expected: book_snapshot_5, trades                                  | coinbase-spot            |
| DERIBIT         | book_snapshot_5, derivative_ticker, futures_chain, liquidations, options_chain, trades   | tardis / deribit         |
| HYPERLIQUID     | book_snapshot_5, derivative_ticker, liquidations, trades                                 | hyperliquid direct       |
| OKX-SPOT        | **(UAC empty — FIX)** expected: book_snapshot_5, trades                                  | tardis / okx-spot        |
| OKX-FUTURES     | **(UAC empty — FIX)** expected: book_snapshot_5, derivative_ticker, trades               | tardis / okx-futures     |
| OKX-SWAP        | **(UAC empty — FIX)** expected: book_snapshot_5, derivative_ticker, liquidations, trades | tardis / okx-swap        |
| UPBIT           | book_snapshot_5, trades                                                                  | tardis / upbit           |

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

Expected dates: `VenueMapping.get_expected_trading_dates(venue, start, end)` — **trading days only** (no weekends,
holidays excluded). Instrument*type axis: equity, futures_chain, options_chain, index. Tick-window rule: `tbbo` /
`trades` only expected inside tick windows (Databento cost management); outside tick windows only
`ohlcv*\*`is expected — see`codex/02-data/availability-manifest-and-data-status.md` §`is_in_tradfi_tick_window`.

| venue  | expected data_types    | notes                                                                                         |
| ------ | ---------------------- | --------------------------------------------------------------------------------------------- |
| CBOE   | ohlcv_15m              | Options index — limited subscription                                                          |
| CME    | ohlcv_1m, tbbo, trades | Full tick window + minute OHLCV; options_chain, futures_chain via instruments-service refresh |
| FX     | ohlcv_24h              | Daily only (cost envelope)                                                                    |
| ICE    | ohlcv_1m, tbbo, trades | Same cost model as CME                                                                        |
| NASDAQ | ohlcv_1m, tbbo, trades | Equity venue                                                                                  |
| NYSE   | ohlcv_1m, tbbo, trades | Equity venue                                                                                  |

### TRADFI coverage axes

| data_type   | Coverage axis                                         | Expected shards (per trading day)    | `record_empty` expected                                                           |
| ----------- | ----------------------------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------- |
| `trades`    | per-venue × per-instrument × daily (tick window only) | venues × active equities / contracts | Yes — outside tick window = `capture_status=empty_confirmed` (expected by design) |
| `tbbo`      | per-venue × per-instrument × daily (tick window only) | same as `trades`                     | Yes                                                                               |
| `ohlcv_1m`  | per-venue × per-instrument × daily                    | venues × active equities / contracts | Yes — halted instruments = empty_confirmed                                        |
| `ohlcv_15m` | per-venue × per-instrument × daily                    | CBOE × options index                 | Yes                                                                               |
| `ohlcv_24h` | per-venue × per-pair × daily                          | FX × G10 crosses                     | Yes                                                                               |

## 4. DEFI — per venue × data_type matrix (venue = `PROTOCOL-CHAIN`)

Expected dates: daily grid from `get_venue_start_date(venue)` (each protocol-chain has its own deployment date).
Instrument_type axis: POOL (DEX), LENDING (Aave/Morpho/Compound/Fluid), LST (Lido/Ether.fi/Ethena).

| venue              | expected data_types                                  | instrument_type category |
| ------------------ | ---------------------------------------------------- | ------------------------ |
| AAVEV3-ETHEREUM    | lending_indices, oracle_prices, rewards, risk_params | LENDING                  |
| BALANCER-ETHEREUM  | dex_pools, dex_swaps                                 | POOL                     |
| CURVE-ETHEREUM     | dex_pools, dex_swaps                                 | POOL                     |
| ETHENA-ETHEREUM    | lst_rates, oracle_prices                             | LST                      |
| ETHERFI-ETHEREUM   | lst_rates, oracle_prices                             | LST                      |
| FLUID-ETHEREUM     | lending_indices, oracle_prices                       | LENDING                  |
| LIDO-ETHEREUM      | lst_rates, oracle_prices                             | LST                      |
| MORPHO-ETHEREUM    | lending_indices, oracle_prices                       | LENDING                  |
| UNISWAPV2-ETHEREUM | dex_pools, dex_swaps                                 | POOL                     |
| UNISWAPV3-ETHEREUM | dex_pools, dex_swaps                                 | POOL                     |
| UNISWAPV4-ETHEREUM | dex_pools, dex_swaps                                 | POOL                     |

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

For each `(category, venue, data_type)` the data-status aggregator computes:

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
        # DeFi adds chain axis; SPORTS adds (league, bookmaker, fixture_date).
        # Base honest-coverage:
        found_pairs = distinct (venue, dt, date) with capture_status in {captured, empty_confirmed}
        ratio = len(found_pairs) / max(1, len(expected_dates))
```

No multipliers. No cross-venue row-count comparisons. `capture_status="empty_confirmed"` counts toward `found_shards`
per v5 SSOT.

## 8. Open questions / follow-ups

- **UAC gaps** listed in §1. Phase 6b fills these; aggregator should fail loud (not silent zero) if
  `get_expected_data_types_for_venue(v)` returns `[]` for a venue in `all_*_venues()`.
- **HYPERLIQUID duplicate** in `all_cefi_venues` — decide whether to merge both entries or carry CLOB vs non-CLOB as
  distinct venues (check `is_cefi_onchain_clob_venue` method already present on VenueMapping).
- **DEFI multi-chain expansion** — canonical `PROTOCOL-CHAIN` venue naming needs
  Arbitrum/Base/Optimism/Polygon/BSC/Avalanche/Linea/Solana entries. Currently only `-ETHEREUM` set; adapters that
  already write to Arbitrum etc. are likely registering manifest rows under `chain` axis but not declared as separate
  venues.
- **Instrument-level expected** — `trades` / `book_snapshot_5` are per-instrument shards. UAC helper
  `get_expected_instrument_types_for_venue(venue)` returns instrument*types but not specific instruments. Instrument
  enumeration comes from instruments-service output — aggregator reads `instruments_store*\*` buckets for the
  current-day active instrument list. Honest per-instrument coverage is a Phase 6c+ stretch goal; base per-venue ×
  per-data_type × per-day is the MVP.

## 9. Changelog

- **2026-04-20** — Initial SSOT. Authored as Phase 6a of the SPORTS data-status overhaul — applies the same
  honest-coverage discipline (no FIXTURES-rowcount-as-denominator) to MTDS across CEFI / TRADFI / DEFI / SPORTS /
  PREDICTION. Matrix supersedes any implicit per-category coverage rules previously scattered in MTDS adapters.
