---
title: "Manifest schema v6 — quote_asset, margin_type, combo_type, leg_weights"
status: active
created: 2026-04-23
locked_by: live-defi-rollout
locked_since: 2026-04-23
---

# Manifest schema v6 — quote / margin / combo dimensions

## Context

Fleet relaunch 2026-04-22 revealed a latent schema gap: DERIBIT lists BOTH
**inverse** (coin-margined) and **linear** (USDC-margined) derivatives on
the same underlying. Example:

- `BTC-PERPETUAL` — BTC-margined perp (inverse)
- `BTC_USDC-PERPETUAL` — USDC-margined perp (linear)
- `BTC-29DEC25-100000-C` — BTC-margined call option
- `BTC_USDC-29DEC25-100000-C` — USDC-margined call option

Current v5 shard key for OPTION / FUTURE bundles is
``(venue, date, data_type, instrument_type, underlying)`` — **inverse and
linear on the same underlying COLLIDE into the same parquet**
(`BTC.parquet` under `instrument_type=option/data_type=options_chain`).
Rows from both margin types get concatenated together, losing
disambiguation information and breaking any downstream strategy that
treats them as separate instruments.

Additionally: **COMBO instruments** (call spreads, iron condors,
butterflies, calendar spreads) flow through Tardis as single-row
instruments with synthetic symbols like
`BTC-29DEC25-100000-C|BTC-29DEC25-110000-C` (or platform-specific combo
tickers). Currently they fold into `options_chain` / `futures_chain`
bundles with no leg metadata, making it impossible to reconstruct the
strategy or evaluate risk per-leg without re-parsing the symbol on every
read.

## Schema v6 additions

Four new string columns on `AvailabilityRecord` + `build_instrument_id`:

| Column | Type | Purpose | Example values |
|---|---|---|---|
| `quote_asset` | str (default `""`) | Settlement / quote currency — disambiguates inverse vs linear derivatives and spot quote asset | `"USD"`, `"USDT"`, `"USDC"`, `"BTC"`, `"ETH"`, `"KRW"` |
| `margin_type` | str (default `""`) | Coin-margined (inverse) vs stable-margined (linear) derivative | `"inverse"` (BTC/ETH-margin), `"linear"` (USDC/USDT/USD-margin), `""` (spot / unknown) |
| `combo_type` | str (default `""`) | Multi-leg synthetic instrument classification | `"call_spread"`, `"put_spread"`, `"iron_condor"`, `"butterfly"`, `"calendar_spread"`, `"strangle"`, `"straddle"`, `""` (non-combo) |
| `leg_weights` | str (default `""`) | JSON-serialised legs + signed quantities for COMBO rows | `[{"instrument_id":"BTC-26DEC25-100000-C","qty":1},{"instrument_id":"BTC-26DEC25-110000-C","qty":-1}]` |

Legacy rows with `quote_asset=""`, `margin_type=""`, `combo_type=""`,
`leg_weights=""` are valid — the read path coerces missing columns to
`""` when reading v1-v5 parquets (same pattern as v4→v5 capture_status
backfill).

## Revised shard key + GCS path

| instrument_type | data_type | Shard key | Example path |
|---|---|---|---|
| PERPETUAL | trades, book_snapshot_5, derivative_ticker, liquidations | `(venue, date, dt, instrument_id)` | `.../instrument_type=perpetual/data_type=trades/BTC-PERPETUAL.parquet` (inverse) or `BTC_USDC-PERPETUAL.parquet` (linear) — disambiguated via the instrument_id itself |
| SPOT_PAIR | trades, book_snapshot_5 | `(venue, date, dt, instrument_id)` | `.../instrument_type=spot_pair/data_type=trades/BTC-USDT.parquet` |
| OPTION | options_chain | `(venue, date, options_chain, option, underlying, quote_asset, margin_type)` bundle | `.../instrument_type=option/data_type=options_chain/underlying=BTC/quote=USD/margin=inverse/ticks.parquet` |
| FUTURE (ALWAYS multi-symbol) | futures_chain | `(venue, date, futures_chain, future, underlying, quote_asset, margin_type)` bundle | `.../instrument_type=future/data_type=futures_chain/underlying=ES/quote=USD/margin=linear/ticks.parquet` |

**COMBO rows live inside the parent bundle** (options_chain or
futures_chain) and are distinguished by `combo_type != ""` + populated
`leg_weights`. They share the bundle shard path.

## Phases (execution DAG)

```
Phase 1 (SEQUENTIAL — foundation)
└─ UTL: AvailabilityRecord + ManifestWriter v6 schema
    └─ Phase 2 (PARALLEL after Phase 1 lands)
        ├─ UAC: build_instrument_id(venue, itype, base, quote_asset=, margin_type=)
        ├─ MTDS: Tardis symbol parser (deribit BTC/BTC_USDC disambiguation)
        ├─ MTDS: finalise_and_write_cefi_shards refactor (memory + v6 path)
        └─ UTL: ResourceProfiler burst-aware sampling (5s → 1s + sync flush on 70%)
            └─ Phase 3 (SEQUENTIAL)
                ├─ MTDS: pre-flight lookup v6 key
                ├─ MTDS: rebuild_cefi_manifest v6-aware (parse margin from path when possible)
                └─ deployment-service: Fleet Monitor zombie detection fix (grep last 10 lines)
                    └─ Phase 4 (SEQUENTIAL)
                        ├─ QG: UAC + UTL + MTDS
                        ├─ Tarball refresh (--all)
                        ├─ Launch legacy migration VMs (read BTC.parquet → split by margin → write new paths)
                        └─ Launch fleet on new schema
                            └─ Phase 5 (POST-FLEET)
                                ├─ Codex doc: shard-granularity-cefi.md with v6 dimensions
                                ├─ Rebuild manifest from GCS (catch orphan parquets)
                                └─ deployment-ui: surface new dims in data-status
```

## Pre-audit manifest

### UTL — `unified_trading_library/manifest_writer.py`

| Line | Current | Change |
|---|---|---|
| 56 | `MANIFEST_SCHEMA_VERSION = 5` | → `6` |
| ~90 | `AvailabilityRecord` dataclass | Add `quote_asset`, `margin_type`, `combo_type`, `leg_weights: str = ""` |
| 389-470 | `.add()` signature | Accept new kwargs, default `""`, thread into `AvailabilityRecord` |
| 476-507 | `.record_empty()` / `.record_failed()` | Same kwarg plumbing |
| 1112+ | `read_availability_index` `_V4_COLUMNS` list | Rename to `_V5_COLUMNS`, add v6 columns; read path backfills missing cols to `""` |

### UAC — `unified_api_contracts/registry/instrument_id.py` (or similar)

Location TBD — grep for `def build_instrument_id`. Signature extension:

```python
def build_instrument_id(
    venue: str,
    instrument_type: InstrumentType,
    base: str,
    *,
    quote_asset: str = "",
    margin_type: str = "",  # "inverse" | "linear" | ""
    expiry_date: date | None = None,
    strike: Decimal | None = None,
    option_right: Literal["C", "P"] | None = None,
) -> str:
    """Canonical instrument_id including settlement dimension.

    Examples:
        PERPETUAL: DERIBIT:PERPETUAL:BTC:USD:inverse:PERPETUAL
                   DERIBIT:PERPETUAL:BTC:USDC:linear:PERPETUAL
        OPTION:    DERIBIT:OPTION:BTC:USD:inverse:26DEC25:100000:C
                   DERIBIT:OPTION:BTC:USDC:linear:26DEC25:100000:C
        Legacy (quote="" + margin=""): DERIBIT:OPTION:BTC:26DEC25:100000:C
    """
```

### MTDS — `market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py`

`derive_row_instrument_id` needs to parse DERIBIT / BINANCE-FUTURES /
BYBIT / OKX-SWAP symbol conventions for quote + margin:

| Venue | Symbol pattern | quote_asset | margin_type |
|---|---|---|---|
| DERIBIT | `BTC-*` or `ETH-*` (no underscore before dash) | `"USD"` (Deribit inverse settles USD) | `"inverse"` |
| DERIBIT | `BTC_USDC-*`, `BTC_USDT-*`, `ETH_USDC-*`, `ETH_USDT-*` | `"USDC"` / `"USDT"` | `"linear"` |
| BINANCE-FUTURES | `*USDT` (uppercase) | `"USDT"` | `"linear"` |
| BINANCE-FUTURES | `*USDC` | `"USDC"` | `"linear"` |
| BINANCE-FUTURES | `*USD_PERP` (coin-margined) | `"USD"` | `"inverse"` |
| BYBIT | `*USDT` linear perps | `"USDT"` | `"linear"` |
| BYBIT | `*USD` inverse perps | `"USD"` | `"inverse"` |
| OKX-SWAP | `*-USDT-SWAP` | `"USDT"` | `"linear"` |
| OKX-SWAP | `*-USD-SWAP` | `"USD"` | `"inverse"` |
| HYPERLIQUID | all perps | `"USDC"` | `"linear"` |
| CME-FUTURES | `ESM26` etc. | `"USD"` | `"linear"` |
| CBOE-VIX-FUTURES | `VXM26` etc. | `"USD"` | `"linear"` |
| COINBASE-SPOT | `BTC-USD`, `BTC-USDT` | `"USD"` / `"USDT"` | `""` (spot) |
| UPBIT | `KRW-BTC` etc. | `"KRW"` | `""` (spot) |
| BINANCE-SPOT | `btcusdt` | `"USDT"` | `""` (spot) |
| OKX-SPOT | `BTC-USDT` | `"USDT"` | `""` (spot) |

### MTDS — `market_tick_data_service/market_interface/adapters/tradfi/tardis_adapter.py`

`finalise_and_write_cefi_shards` refactor (three things in one):

1. **Memory: eliminate DataFrame bridge**
   - Remove `df = df.copy()` at line 834 — mutate in-place (caller drops after return)
   - For per-symbol shards (PERPETUAL / SPOT_PAIR): skip `.to_dict("records")` —
     `instrument_id` is scalar (one per shard), compute once, vectorized assign
     on the DataFrame, pass DataFrame directly to `StreamingParquetWriter`
   - For per-underlying bundles (OPTION / FUTURE): vectorize `derive_row_instrument_id`
     using pandas column operations; only fall back to per-row dict for rows missing
     required schema fields

2. **v6 shard key**
   - Thread `quote_asset` + `margin_type` into the group key for derivative shards
   - Update GCS path construction to include `quote=` and `margin=` segments
   - Emit manifest rows with v6 columns populated

3. **Chunked parquet writes**
   - `StreamingParquetWriter.write_chunk(df, chunk_size=100_000)` — bound peak RSS
     during parquet serialization

### MTDS — `market_tick_data_service/scripts/rebuild_cefi_manifest.py`

Extend path parser to extract `quote=` / `margin=` when present (new
layout). For legacy paths (`underlying=BTC/ticks.parquet` with no
`quote=` segment), emit rows with `quote_asset=""`, `margin_type=""`
— these rows get cleaned up by the legacy migration script.

### MTDS — new `scripts/migrate_deribit_margin_split_v6.py`

One-off migration for legacy DERIBIT `BTC.parquet` / `ETH.parquet` files:

1. List all `day=*/category=cefi/venue=DERIBIT/instrument_type=option/data_type=options_chain/{BTC,ETH}.parquet` and corresponding `futures_chain` paths
2. For each parquet:
   - Read row-level symbols
   - Split into `margin_type=inverse` (no `_USDC`/`_USDT` suffix) vs `margin_type=linear` subsets
   - Write split results to new paths `.../underlying=BTC/quote=USD/margin=inverse/ticks.parquet` and `.../underlying=BTC/quote=USDC/margin=linear/ticks.parquet`
   - Emit v6 manifest rows for the split shards
   - Delete the legacy unsplit parquet + legacy manifest row (replaced)
3. Date-sharded for parallel VM execution (5-10 VMs)

### UTL — `unified_trading_library/lifecycle/resource_profiler.py`

Two changes:

1. **Burst-aware sampling**: add optional `burst_sample_sec` param (default
   `1.0`) that fires a tighter-interval sample when RSS jumps >N% between
   emits. Current 5s default masks sub-5s allocation spikes.
2. **Synchronous memory ceiling**: add `on_memory_critical_sync` callback
   fired at 70% RSS that BLOCKS the caller: pauses the io-loop via
   `asyncio.Event`, flushes in-progress `StreamingParquetWriter`, calls
   `flush_all_live_writers()`, forces `gc.collect()`, then resumes. Prevents
   the burst-OOM pattern we saw on 45 heavy VMs.

### deployment-service — Fleet Monitor

Rewrite the zombie check:

```bash
# OLD (broken — misses rc= when heartbeat daemon appends DEPLOYMENT_COMPLETED after)
tail=$(gsutil cat ".../run.log" | tail -1)
echo "$tail" | grep -qE "rc=[0-9]+"

# NEW
tail=$(gsutil cat ".../run.log" | tail -10)
echo "$tail" | grep -qE "rc=[0-9]+"
```

## Success criteria

### Phase 1-3 gates

- [ ] UTL QG green + schema v6 round-trip test (v5 parquet read → v6 write → v5 read still works)
- [ ] UAC QG green + `build_instrument_id` v6 unit tests (all venue patterns)
- [ ] MTDS QG green + existing tests pass + new Deribit symbol parsing test
- [ ] Local smoke: one DERIBIT light VM processes 2024-01-02 successfully, emits v6 manifest rows with populated `quote_asset` + `margin_type`

### Phase 4 gate — legacy migration

- [ ] Legacy migration script produces correct splits on 3 sample DERIBIT dates
- [ ] 5-10 migration VMs launched, complete within ~4hr
- [ ] Post-migration: zero DERIBIT rows with `quote_asset="" AND margin_type=""` + `instrument_type in (option, future)`

### Phase 5 gate — fleet relaunch

- [ ] Fleet launches on `e2-standard-2` (or `e2-highmem-2` fallback)
- [ ] Fleet Monitor correctly flags zombies (tested by killing a VM manually)
- [ ] ResourceProfiler emits burst samples AND fires memory-critical callback under stress test
- [ ] No rc=137 OOMs in first hour of fleet runtime
- [ ] Manifest growth shows correct v6 column population

### Phase 6 gate — downstream

- [ ] Codex doc `shard-granularity-cefi.md` published
- [ ] deployment-api data-status API includes new dims in response
- [ ] deployment-ui heatmap filterable by `quote_asset` / `margin_type`

## Estimated effort

| Phase | Duration |
|---|---|
| Phase 1 UTL v6 schema | 30-45 min |
| Phase 2 parallel (UAC + MTDS + UTL profiler) | 1.5-2 hr |
| Phase 3 sequential (pre-flight + rebuild + monitor) | 45 min |
| Phase 4 QG + migration launch | 1 hr + migration wall-clock ~4 hr |
| Phase 5 codex + UI | 45 min |
| **Total focused work** | **5-7 hr** + ~4hr migration wall-clock |

## Non-goals

- Not migrating TradFi (CME/CBOE) bundles — those are all USD-margined, no inverse variant
- Not introducing a separate `combo` instrument_type (COMBO is a tag on option/future)
- Not changing the hive layout for PERPETUAL/SPOT_PAIR (already per-symbol, instrument_id disambiguates)
- Not touching sports / prediction / defi manifests — v6 is additive (they'll ignore new columns)
