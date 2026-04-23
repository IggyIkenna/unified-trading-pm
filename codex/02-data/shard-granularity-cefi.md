# CeFi shard granularity — instrument_type × quote_asset × margin_type (v6)

**Status:** active as of 2026-04-23 (manifest schema v6 shipped). **SSOT:**
`unified-trading-pm/plans/active/manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md`. **Related:**
[availability-manifest-and-data-status.md](./availability-manifest-and-data-status.md),
[partitioning.md](./partitioning.md).

## Problem v6 solves

Pre-v6 the CeFi chain-bundle shard key was `(venue, date, data_type, instrument_type, underlying)`. Example — DERIBIT
options chain: a single `BTC.parquet` file held BOTH:

- `BTC-29DEC25-100000-C` — coin-margined (inverse), USD-settled
- `BTC_USDC-29DEC25-100000-C` — USDC-margined (linear), USDC-settled

Row concatenation lost the disambiguation and broke downstream strategies that treat inverse and linear as separate
instruments.

## v6 shard key matrix

| instrument_type                           | data_type                                                        | Shard key                                                                   | Path shape                                                                                             |
| ----------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `PERPETUAL`                               | `trades`, `book_snapshot_5`, `derivative_ticker`, `liquidations` | `(venue, date, dt, instrument_id)`                                          | `.../instrument_type=perpetual/data_type=.../{instrument_id}.parquet`                                  |
| `SPOT_PAIR`                               | `trades`, `book_snapshot_5`                                      | `(venue, date, dt, instrument_id)`                                          | `.../instrument_type=spot_pair/data_type=.../{instrument_id}.parquet`                                  |
| `OPTION` → `options_chain`                | `trades`                                                         | `(venue, date, options_chain, underlying, quote_asset, margin_type)` bundle | `.../instrument_type=options_chain/data_type=trades/underlying={U}/quote={Q}/margin={M}/ticks.parquet` |
| `FUTURE` (multi-symbol) → `futures_chain` | `trades`                                                         | `(venue, date, futures_chain, underlying, quote_asset, margin_type)` bundle | `.../instrument_type=futures_chain/data_type=trades/underlying={U}/quote={Q}/margin={M}/ticks.parquet` |

COMBO rows (call spreads, iron condors, etc.) live INSIDE the parent chain bundle — they are distinguished by
`combo_type != ""` and populated `leg_weights` on the manifest row, not by a separate `instrument_type`.

## Manifest v6 columns (added over v5)

Four new string columns on `AvailabilityRecord`:

| Column        | Default | Example values                                                                   |
| ------------- | ------- | -------------------------------------------------------------------------------- |
| `quote_asset` | `""`    | `"USD"`, `"USDT"`, `"USDC"`, `"BTC"`, `"ETH"`, `"KRW"`                           |
| `margin_type` | `""`    | `"inverse"` (coin-margined), `"linear"` (stable-margined), `""` (spot / unknown) |
| `combo_type`  | `""`    | `"call_spread"`, `"iron_condor"`, `"butterfly"`, `"calendar_spread"`, `""`       |
| `leg_weights` | `""`    | JSON: `[{"instrument_id":"BTC-26DEC25-100000-C","qty":1}, ...]`                  |

Legacy v1–v5 parquets are read with all four columns backfilled to `""` — same compat pattern used for v4→v5
`capture_status` rollout.

## Venue-symbol parser matrix

`derive_settlement_dimensions(venue, symbol, instrument_type)` — canonical mapping in
[tardis_shared.py](../../../market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py)
— extracts `(quote_asset, margin_type)` per row.

| Venue                    | Symbol pattern                        | quote                    | margin      |
| ------------------------ | ------------------------------------- | ------------------------ | ----------- |
| DERIBIT                  | `BTC-*` / `ETH-*` (no `_` before `-`) | `USD`                    | `inverse`   |
| DERIBIT                  | `BTC_USDC-*`, `ETH_USDT-*`            | `USDC` / `USDT`          | `linear`    |
| BINANCE-FUTURES          | `*USDT`, `*USDC`                      | `USDT` / `USDC`          | `linear`    |
| BINANCE-FUTURES          | `*USD_PERP`, `*USD_{YYMMDD}`          | `USD`                    | `inverse`   |
| BYBIT                    | `*USDT`, `*USDC`, `*PERP`             | `USDT` / `USDC` / `USDC` | `linear`    |
| BYBIT                    | `*USD` (no T)                         | `USD`                    | `inverse`   |
| OKX-SWAP                 | `*-USDT-SWAP`, `*-USDC-SWAP`          | `USDT` / `USDC`          | `linear`    |
| OKX-SWAP                 | `*-USD-SWAP`                          | `USD`                    | `inverse`   |
| HYPERLIQUID / ASTER      | all perps                             | `USDC`                   | `linear`    |
| CME / CBOE               | `ESM26`, `VX-21JAN26-20-C`            | `USD`                    | `linear`    |
| COINBASE-SPOT / OKX-SPOT | `BTC-USD`, `BTC-USDT`                 | quote                    | `""` (spot) |
| BINANCE-SPOT             | `btcusdt` (lowercase concat)          | quote                    | `""` (spot) |
| UPBIT                    | `KRW-BTC` (quote-first)               | `KRW`                    | `""` (spot) |

Unknown venues or ambiguous symbols return `("", "")` — the shard falls back to the v5 path shape without the nested
`quote=`/`margin=` segments.

## Downstream implications

1. **Pre-flight skip logic.** Keys on `(venue, date, data_type)` as before; finer granularity flows in naturally as v6
   manifest rows accumulate. No change required in consumers that merely check "did this date get any data for this
   venue/data_type".

2. **Strategy / risk consumers.** Any strategy that holds DERIBIT BTC options previously fed from `BTC.parquet` now
   reads from one of two paths (`underlying=BTC/quote=USD/margin=inverse/...` or
   `underlying=BTC/quote=USDC/margin=linear/...`). Strategies that care about only one margin flavour get a cheaper
   read; strategies that span both must `UNION` the two paths. The manifest row carries `quote_asset` and `margin_type`
   so queries can filter by margin type cleanly.

3. **Legacy parquets.** Existing `BTC.parquet` DERIBIT bundles contain a mix of inverse and linear rows. The one-off
   migration script
   [`migrate_deribit_margin_split_v6.py`](../../../market-tick-data-service/market_tick_data_service/scripts/migrate_deribit_margin_split_v6.py)
   row-splits them into v6 paths. The legacy file is NOT deleted — only tagged for removal in a follow-up sweep once v6
   readers are validated (trivial rollback).

4. **`rebuild_cefi_manifest.py`** recognises all three layouts (v6 chain, legacy `underlying=` sub-path, Tardis
   canonical `{stem}.parquet`) — see `parse_hive_path`.

## Non-goals (for v6)

- Does NOT extend `build_instrument_id` with `quote_asset` / `margin_type` kwargs. Canonical IDs
  (`DERIBIT:OPTION:BTC:26DEC25:100000:C`) stay stable for backward compatibility of the catalogue. Disambiguation is
  load-bearing at the _shard path_ + _manifest row_ layer, not in the ID. (Follow-up: Phase 2c of the v6 plan —
  deferred.)
- Does NOT touch sports / prediction / DeFi manifests. v6 is additive for them — the four new columns are simply `""`.
