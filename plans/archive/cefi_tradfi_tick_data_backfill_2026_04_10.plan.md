---
title: "CeFi + TradFi Tick Data Backfill"
status: active
created: 2026-04-10
locked_by: live-defi-rollout
locked_since: 2026-04-10
---

# CeFi + TradFi Tick Data Backfill

## 2026-05-05 manifest-truth correction

Manifest probe on 2026-05-05 against
`gs://market-data-tick-tradfi-central-element-323112/_index/availability_index.parquet` invalidates several
pre-2026-05-05 assumptions in this plan. The 2026-04-10 "CME 53d / 2020 only" snapshot in the table below is **stale** —
the row stays for history but is overridden by the truth here. Future agents: re-verify against the manifest path above
before acting.

| Instrument                                           | Reality (2026-05-05 manifest)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | --- | --- | --- | ---- | --------------------------------------------------------------------------------------------------------------------------------- |
| ES futures (CME) ohlcv_1m + trades                   | **2020-01-01 → 2026-05-04, 100% captured.** futures_chain 1,848 ohlcv_1m + 1,974 trades; options_chain 1,287 ohlcv_1m + 1 trades.                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| MES futures (CME) ohlcv_1m + trades                  | **2020-01-01 → 2026-05-04, 100% captured.** combo 1,691 ohlcv_1m + 1,741 trades; futures_chain 1,879 ohlcv_1m + 1,962 trades. No MES options.                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ES_OPT options_chain                                 | 2020 = 0, 2021 = 0, 2022 = 281, 2023 = unknown, 2024 = 208, 2025 = 8, 2026 = 95. **2020-2021 missing entirely; 2025 sparse.** Fill VM `tradfi-bf-es-opt-fill-20260505-123434` running asia-northeast1-c targeting this gap.                                                                                                                                                                                                                                                                                                                                                      |
| IBIT (NASDAQ trades)                                 | 31 rows, all `empty_confirmed`, July 2024 only. **0 usable rows ever — NASDAQ trades cold backfill never run.**                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ETHA (NASDAQ trades)                                 | 31 rows, all `empty_confirmed`, July 2024 only. **0 usable rows ever — NASDAQ trades cold backfill never run.**                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| VIX (Yahoo Finance ohlcv_15m)                        | 2,211 rows 2020-01-03 → 2026-04-29, **ALL `empty_confirmed`** in canonical manifest. `instrument_id` column blank. User reports manually uploading real VIX data 2-4 weeks ago — likely sitting under non-canonical path the manifest doesn't index. Status: needs adapter triage / manifest rebuild, NOT a fresh backfill. **CORRECTED by second-probe 2026-05-05 — see § 2026-05-05 second-probe correction below: the canonical VIX is captured under `venue=CBOE` (not Yahoo); the 2,211 Yahoo `empty_confirmed` rows are an abandoned adapter and not the canonical feed.** |
| Stale ETF rows (post-2026-05-05 MVP scope reduction) | NYSE rows for ETHE 27, GBTC 27, BITO 24, FBTC 18, ARKB 13, FETH 12 — all `empty_confirmed`, 2024-07. Cleanup pending; doesn't block.                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Tradfi disk path shape                               | Uses legacy `day-YYYY-MM-DD/` (dash) NOT canonical `raw_tick_data/by_date/day=YYYY-MM-DD/` (hive). No `rebuild_tradfi_manifest.py` exists; phantom audit never run for tradfi. Drift may be hiding rows.                                                                                                                                                                                                                                                                                                                                                                         |
| `launch-tradfi-backfill-vm.sh`                       | Confirmed exists at `deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh`, valid roots `ES                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | ES_OPT | MES | BTC | ETH | IBIT | ETHA`, singleton lock, `VM_SHUTDOWN_ON_COMPLETION=true`, ServiceBootstrap events. Earlier text claiming this is missing is wrong. |
| Databento VX futures                                 | Not supported. `databento_classifier.py:88` lists VIX only as INDEX. CFE/VX continuous symbology absent. Term-structure feed dead unless Databento adds it.                                                                                                                                                                                                                                                                                                                                                                                                                      |

## 2026-05-05 second-probe correction

Re-probe on 2026-05-05 against `gs://market-data-tick-tradfi-central-element-323112/_index/availability_index.parquet`
plus direct GCS path probes overrides several first-probe assertions above. The first correction's "VIX needs adapter
triage" item is wrong; below is the verified ground truth.

| Topic                         | First-probe claim                                                | Second-probe verified ground truth (2026-05-05)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ----------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| VIX canonical capture         | "ALL `empty_confirmed`, needs adapter triage / manifest rebuild" | **WRONG.** VIX is fully captured at canonical path `gs://market-data-tick-tradfi-central-element-323112/raw_tick_data/by_date/day={D}/asset_group=tradfi/venue=CBOE/instrument_type=index/data_type=ohlcv_15m/VIX.parquet`. 696+ daily partitions on disk. Manifest has **1,602 rows `venue=CBOE, data_type=ohlcv_15m, capture_status=captured`** covering 2020-01-07 → 2026-05-05 (~250 trading days/year, all years complete). Sample-read 2026-05-04: 52 rows, OHLC populated 17.23-18.95, `instrument_key=CBOE:INDEX:VIX-USD`, `volume=0` (correct for index). The 2,211 `empty_confirmed` rows under `venue=YAHOO_FINANCE` (`ohlcv_24h`/`ohlcv_15m`) are a **separate abandoned adapter** — NOT the canonical VIX feed. NO FIX NEEDED.                                                      |
| ES_OPT 2020-2022 fill VM      | "Fill VM `tradfi-bf-es-opt-fill-20260505-123434` running"        | **Killed.** That VM had `VM_FORCE_WINDOW=true` + `VM_START_DATE=2023-01-01`, refetching already-captured 2023-2026 and missing the actual 2020-2022 gap. Relaunched as `tradfi-bf-es-opt-adhoc-adhoc-20260505-183009` in `asia-northeast1-c` with `--start-date 2020-01-01 --end-date 2022-12-31`, instruments `ES.OPT;EW.OPT;EW1-4.OPT;E1A-E5A.OPT;EOM.OPT`, data_types `ohlcv_1m`. STARTED event confirmed at `gs://central-element-323112-events/events/market-tick-data-service/2026-05-05/tradfi-bf-es-opt-adhoc-adhoc-20260505-183009/hour=17/+hour=18/`. Launcher hardcodes `VM_FORCE_WINDOW=true` (line 196) — narrowing the date window is the workaround until launcher accepts a configurable flag.                                                                                   |
| Legacy `category=tradfi` path | (not previously surfaced)                                        | **Holds significant uncatalogued option + equity data.** `day=2024-01-15/category=tradfi/venue=CME/data_type=options_chain/` has `*_migrated_20260419T131639Z.parquet` (e.g. `6AG4_*`, `E1AG4_C4800_*`); manifest's options*chain count for 2024 = 208 only, suggesting partial indexing. `day=2020-06-15/category=tradfi/venue=CME/instrument_type=future/data_type=trades/` has `E1AN0_C3090`, `E3AM0*\*`style option-strike parquets stored under`instrument_type=future` (path-misclassified — these are options not futures). Phantom-audit / manifest-rebuild port to tradfi (same drift class CeFi audited 2026-05-04) likely surfaces them without re-fetching.                                                                                                                          |
| NASDAQ S&P 500 constituents   | (first-probe focused on IBIT/ETHA only)                          | **Legacy path holds 79 constituent tickers.** `day-2026-01-03/data_type-ohlcv_1m/equities/NASDAQ/` has AAPL, ADBE, ADI, ADP, ADSK, AMAT, AMD, AMGN, AMZN, AVGO, BIIB, BKNG, CDNS, CDW, CEG, CHTR, CMCSA, COST, CPRT, CSCO, CSGP — top S&P 500 NASDAQ tech names. Canonical path `day=2026-05-04/asset_group=tradfi/venue=NASDAQ/instrument_type=equity/data_type=ohlcv_1m/` only has IBIT.parquet + ETHA.parquet — live captures are spot-ETF-only; individual constituents NOT being live-captured. Manifest NASDAQ: 2,156 captured rows 2023-04-15 → 2026-05-04 (mostly IBIT/ETHA + 79-instrument legacy snapshots), pre-2023 = 0. **Implication for S&P 500 ML: ES futures (proxy for SPX) is the canonical training input.** Individual constituents are nice-to-have; not blocking the MVP. |
| Yahoo Finance manifest noise  | "needs adapter triage"                                           | **Stale-not-blocker.** 2,211 `empty_confirmed` rows under venue=YAHOO_FINANCE for 2020-2026 — abandoned adapter, separate from canonical CBOE VIX. Cleanup is low-priority noise.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |

## Context

CeFi migration to hive-partitioned GCS (instrument_type= partition) is complete. Now need to backfill missing data
types, instrument types, and historical dates. Also TradFi CME/CBOE gaps.

All CeFi backfills use MTDS batch mode via Tardis. TradFi uses Databento (CME) and Barchart (CBOE).

### Current state (from manifest 2026-04-10)

| Venue           | instrument_type        | data_type            | Have                     | Gap                                                  |
| --------------- | ---------------------- | -------------------- | ------------------------ | ---------------------------------------------------- |
| DERIBIT         | perpetual/trades       | trades               | 470d (Apr 2024→Jul 2025) | Not needed (user scope: options + futures only)      |
| DERIBIT         | options_chain/\*       | ALL                  | 0                        | **Full range: 2019-03-30 → now (~2,220 days)**       |
| DERIBIT         | futures_chain/\*       | ALL                  | 0                        | **Full range: 2019-03-30 → now (~2,220 days)**       |
| BINANCE-FUTURES | perpetual/trades       | trades               | 470d (Apr 2024→Jul 2025) | **2019-11-17 → Apr 2024 + Jul 2025 → now (~1,870d)** |
| BINANCE-FUTURES | perpetual/liquidations | liquidations         | 0                        | **Full range: 2019-11-17 → now (~2,340d)**           |
| DERIBIT         | \*/liquidations        | liquidations         | 0                        | **Full range: 2019-03-30 → now (~2,220d per itype)** |
| CME             | future/\*              | trades,ohlcv_1m,tbbo | 53d (2020 only)          | **2021 → now (~1,500 trading days)**                 |
| CBOE            | index/ohlcv_15m        | ohlcv_15m            | 1,481d → Nov 2025        | **Nov 2025 → now (~150d)**                           |

### Tardis data type availability (from API)

**DERIBIT OPTIONS**: trades, options_chain, liquidations, book_snapshot_5, book_snapshot_25, incremental_book_L2,
quotes, book_ticker — since 2019-03-30 **DERIBIT FUTURES**: trades, derivative_ticker, liquidations, incremental_book_L2
— since 2019-03-30 **BINANCE-FUTURES PERPS**: trades, derivative_ticker, liquidations — since 2019-11-17

### Scope (user-specified)

- **DERIBIT**: options_chain + futures_chain instrument types only (coin-margined, that's where the volume is)
- **BINANCE-FUTURES**: USDT perps only, trades + liquidations
- **CME**: ES futures — as long as possible (Databento)
- **CBOE VIX**: fill gap to present (Barchart) — used as a feature

## Backfill Scope (dates × venue × instrument_type × data_type)

### Phase 1: DERIBIT Options + Futures (Tardis) — PARALLEL

**1a. DERIBIT options_chain**

- Dates: 2019-03-30 → 2026-04-10 (~2,220 days)
- instrument_type: options_chain
- data_types: trades, options_chain (greeks/IVs), liquidations
- Shards: ~6,660

**1b. DERIBIT futures_chain**

- Dates: 2019-03-30 → 2026-04-10 (~2,220 days)
- instrument_type: futures_chain
- data_types: trades, derivative_ticker, liquidations
- Shards: ~6,660

**Phase 1 total: ~13,320 shards**

### Phase 2: BINANCE-FUTURES Perps (Tardis) — PARALLEL with Phase 1

**2a. BINANCE-FUTURES perpetual/trades backfill**

- Dates: 2019-11-17 → 2024-04-04 (pre-existing gap) + 2025-07-19 → 2026-04-10 (post-migration gap)
- instrument_type: perpetual
- data_types: trades
- Shards: ~1,870

**2b. BINANCE-FUTURES perpetual/liquidations**

- Dates: 2019-11-17 → 2026-04-10 (~2,340 days)
- instrument_type: perpetual
- data_types: liquidations
- Shards: ~2,340

**Phase 2 total: ~4,210 shards**

### Phase 3: TradFi (Databento + Barchart) — SEQUENTIAL (different data providers)

**3a. CME ES futures**

- Dates: 2021-01-01 → 2026-04-10 (~1,350 trading days)
- instrument_type: future
- data_types: trades, ohlcv_1m, tbbo
- Shards: ~4,050
- Provider: Databento (GLBX.MDP3)

**3b. CBOE VIX**

- Dates: 2025-11-13 → 2026-04-10 (~150 days)
- instrument_type: index
- data_types: ohlcv_15m
- Shards: ~150
- Provider: Barchart

**Phase 3 total: ~4,200 shards**

### Grand total: ~21,730 shards

## Execution Plan

```
Phase 1+2 (CeFi/Tardis)    Phase 3 (TradFi)
  ┌─────────┐               ┌─────────┐
  │ VM: DERIBIT opts │       │ VM: CME  │
  │ (1a)             │       │ (3a)     │
  └─────────┘               └─────────┘
  ┌─────────┐               ┌─────────┐
  │ VM: DERIBIT futs │       │ VM: CBOE │
  │ (1b)             │       │ (3b)     │
  └─────────┘               └─────────┘
  ┌─────────┐
  │ VM: BINANCE perps│
  │ (2a+2b)          │
  └─────────┘
  All PARALLEL
```

## Todos

### Phase 1+2: CeFi Backfill (Tardis)

- [ ] [AGENT] P0. Verify MTDS orchestrator handles all target data_types (options_chain, derivative_ticker,
      liquidations) with correct instrument_type partitioning for DERIBIT and BINANCE-FUTURES
- [ ] [AGENT] P0. Verify instruments-service has historical DERIBIT options/futures and BINANCE-FUTURES perps for the
      full date range (instruments must exist for MTDS to download)
- [ ] [SCRIPT] P0. Create VM launch script for DERIBIT options backfill (instrument_type=options_chain,
      data_types=trades,options_chain,liquidations, dates=2019-03-30→2026-04-10)
- [ ] [SCRIPT] P0. Create VM launch script for DERIBIT futures backfill (instrument_type=futures_chain,
      data_types=trades,derivative_ticker,liquidations, dates=2019-03-30→2026-04-10)
- [ ] [SCRIPT] P0. Create VM launch script for BINANCE-FUTURES perps backfill (instrument_type=perpetual,
      data_types=trades,liquidations, dates=2019-11-17→2026-04-10, skip existing trades Apr 2024→Jul 2025)
- [ ] [SCRIPT] P1. Launch all 3 CeFi VMs in parallel
- [ ] [SCRIPT] P1. Monitor VM progress via GCS logs
- [ ] [SCRIPT] P2. Verify manifest entries appear in deployment-ui data status tab

### Phase 3: TradFi Backfill

- [ ] [AGENT] P0. Verify MTDS orchestrator handles CME via Databento and CBOE via Barchart for the target data_types
- [x] [SCRIPT] P0. Create VM launch script for CME ES futures backfill (trades, ohlcv_1m, tbbo,
      dates=2021-01-01→2026-04-10) (verified captured 2020-01-01 → 2026-05-04 by manifest probe 2026-05-05 against
      `gs://market-data-tick-tradfi-central-element-323112/_index/availability_index.parquet`; futures_chain 1,848
      ohlcv_1m + 1,974 trades. Launcher `deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh` exists, valid roots
      `ES|ES_OPT|MES|BTC|ETH|IBIT|ETHA`)
- [x] [SCRIPT] P0. Create VM launch script for MES futures backfill (verified captured 2020-01-01 → 2026-05-04 by
      manifest probe 2026-05-05 — combo 1,691 ohlcv_1m + 1,741 trades; futures_chain 1,879 ohlcv_1m + 1,962 trades; no
      MES options exist)
- [ ] [SCRIPT] P0. Create VM launch script for CBOE VIX backfill (ohlcv_15m, dates=2025-11-13→2026-04-10)
- [ ] [SCRIPT] P1. Launch TradFi VMs
- [ ] [SCRIPT] P2. Verify manifest entries

### TradFi gaps surfaced by 2026-05-05 manifest probe

- [ ] [SCRIPT] P0. Run ES_OPT 2020-2022 fill VM `tradfi-bf-es-opt-adhoc-adhoc-20260505-183009` to completion in
      `asia-northeast1-c` (`--start-date 2020-01-01 --end-date 2022-12-31`, instruments
      `ES.OPT;EW.OPT;EW1-4.OPT;E1A-E5A.OPT;EOM.OPT`, data_types `ohlcv_1m`). STARTED event partitions confirmed at
      `gs://central-element-323112-events/events/market-tick-data-service/2026-05-05/tradfi-bf-es-opt-adhoc-adhoc-20260505-183009/hour=17/+hour=18/`
      (probe 2026-05-05). Replaces prior wasteful `tradfi-bf-es-opt-fill-20260505-123434` (killed this session — that VM
      had `VM_FORCE_WINDOW=true` + `VM_START_DATE=2023-01-01`, refetching already-captured 2023-2026 and missing the
      actual 2020-2022 gap). Confirm `capture_status=captured` for filled windows post-run.
- [ ] [AGENT] P0. IBIT NASDAQ trades cold backfill — 31 rows all `empty_confirmed` from July 2024 only. Run via
      `launch-tradfi-backfill-vm.sh ROOT=IBIT` once adapter path is confirmed. Same for ETHA (also all
      `empty_confirmed`, 31 July-2024 rows).
- [x] [AGENT] P0. VIX manifest rebuild / adapter triage — VIX confirmed captured at canonical CBOE path 2020-2026 by
      second-probe 2026-05-05 against
      `gs://market-data-tick-tradfi-central-element-323112/_index/availability_index.parquet` and direct GCS path probes
      against
      `raw_tick_data/by_date/day={D}/asset_group=tradfi/venue=CBOE/instrument_type=index/data_type=ohlcv_15m/VIX.parquet`.
      1,602 manifest rows `venue=CBOE, data_type=ohlcv_15m, capture_status=captured` covering 2020-01-07 → 2026-05-05;
      sample-read 2026-05-04 confirmed real OHLC values 17.23-18.95 with `instrument_key=CBOE:INDEX:VIX-USD`. The 2,211
      Yahoo `empty_confirmed` rows are a separate abandoned adapter (cleanup low-priority) — NOT the canonical VIX feed.
      `e2e-testing/scripts/common/backfill_vix_yahoo.py` (committed 2026-04-11) writes to the legacy
      `category=tradfi/venue=CBOE/...` path and is superseded by canonical writes.
- [ ] [AGENT] P0. Port phantom audit + manifest-rebuild scripts to tradfi. Tradfi disk path uses legacy
      `day-YYYY-MM-DD/` (dash) instead of canonical `raw_tick_data/by_date/day=YYYY-MM-DD/` (hive). No
      `rebuild_tradfi_manifest.py` exists; phantom audit never run for tradfi. Drift may be hiding captured rows under
      non-indexed paths. Pattern: instruments-service `reconcile_phantom_manifest_rows_all.py` (cefi/defi) + MTDS
      `rebuild_cefi_manifest.py` / `rebuild_defi_manifest.py`.
- [ ] [AGENT] P2. Cleanup stale ETF rows in tradfi manifest post-2026-05-05 MVP scope reduction: NYSE ETHE 27, GBTC 27,
      BITO 24, FBTC 18, ARKB 13, FETH 12 — all `empty_confirmed` 2024-07. Doesn't block; just noise.
- [ ] [AGENT] P0. Port phantom-audit + manifest-rebuild scripts to tradfi (second-probe 2026-05-05 finding). Legacy
      `category=tradfi` paths hold uncatalogued option data
      (`day=2024-01-15/category=tradfi/venue=CME/data_type=options_chain/` has `*_migrated_20260419T131639Z.parquet`
      files; manifest options*chain count for 2024 = 208 only) AND path-misclassified options under
      `instrument_type=future` (`day=2020-06-15/.../venue=CME/instrument_type=future/data_type=trades/` has
      `E1AN0_C3090`,
      `E3AM0*\*`strike     parquets — these are options stored under future) AND 79 NASDAQ S&P 500 constituent equities under legacy    `day-2026-01-03/data_type-ohlcv_1m/equities/NASDAQ/`(AAPL, ADBE, ADI, ADP, AVGO, BIIB, BKNG, COST, CSCO, etc.)     that the canonical NASDAQ path doesn't index (live captures are spot-ETF-only IBIT/ETHA). Same drift class CeFi     audited 2026-05-04. Pattern: instruments-service`reconcile_phantom_manifest_rows_all.py`(cefi/defi) +     MTDS`rebuild_cefi_manifest.py`/`rebuild_defi_manifest.py`.
- [x] [AGENT] P1. Make `VM_FORCE_WINDOW` configurable in `deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh` —
      **SHIPPED 2026-05-05** in prior session. `FORCE_WINDOW=true` default + `--no-force-window` arg-parser flag +
      usage-string update; replaces hardcoded `VM_FORCE_WINDOW=true` at the previous line 196. Comment block points at
      `sp500_ml_readiness_master_2026_05_05.plan.md`.
- [ ] [AGENT] P2. Yahoo Finance manifest cleanup (low-priority noise removal) — 2,211 `empty_confirmed` rows under
      `venue=YAHOO_FINANCE` (`ohlcv_24h`/`ohlcv_15m`) for 2020-2026 are an abandoned adapter, separate from canonical
      CBOE VIX (which is fully captured). Drop these rows from the manifest so deployment-UI data-status doesn't render
      false-empty rows. Not blocking.

### Validation

- [ ] [SCRIPT] P2. Run rebuild_mtds_manifest.py for CEFI and TRADFI to reconcile
- [ ] [SCRIPT] P2. Spot-check: download 3 random days of DERIBIT options, verify options_chain data has greeks/IVs
- [ ] [SCRIPT] P2. Spot-check: download 1 day of CME ES futures, verify trades data

## Success Criteria

- All shards downloaded with 0 errors
- Manifest entries for all (date, venue, instrument_type/data_type) combos
- deployment-ui data status tab shows full coverage
- DERIBIT options_chain instrument_type has trades + options_chain + liquidations for 2019→now
- DERIBIT futures_chain instrument_type has trades + derivative_ticker + liquidations for 2019→now
- BINANCE-FUTURES perpetual has trades for full 2019→now + liquidations for full range
- CME future has trades + ohlcv_1m + tbbo for 2021→now
- CBOE VIX has ohlcv_15m gap filled to present

## Phase: Fix-stack Smoke (2026-04-22)

### Why

Prior 95-VM launch (2026-04-19) saw 55 heavy VMs hit `rc=137` SIGKILL during parquet encoding — OOM on `e2-standard-4`
(16 GB) and recurring on `e2-highmem-4` (32 GB) because per-date `writer_manifest.write()` lost in-memory manifest rows
on SIGKILL. Three fixes landed since (on origin/live-defi-rollout):

- **Fix #1** MTDS `ab91a2c` — `ManifestWriter(..., batch_size=1)` in `engine/orchestrator.py:1243` so every shard
  `.add()` auto-flushes to the UTL module-level buffer. End-of-date `.flush()` backstop.
- **Fix #3** MTDS `ab91a2c` — pyarrow streaming decompress in `_decompress_and_parse_csv_legacy` (gzip.GzipFile +
  `pacsv.open_csv` + `split_blocks=True, self_destruct=True`). Benchmarked 1050→498 MB peak RSS on BYBIT BTCUSDT
  2024-01-02 (2.1× reduction).
- **Fix #5** UTL `881d9ec0` + MTDS `b888eff` — ResourceProfiler 75% RSS warning fires `flush_all_live_writers()` via
  `_LIVE_WRITERS: set[weakref.ref]` + `MANIFEST_EMERGENCY_FLUSH` event before the 85% CRITICAL tripwire.

Smoke must validate the full stack on a real VM at the target machine type (`e2-standard-2`, 8 GB) before relaunching
the 95-VM fleet.

### Smoke VM

```
name            cefi-smoke-fixstack-20260422
zone            asia-northeast1-c
machine-type    e2-standard-2  (8 GB RAM — the fleet target)
venue           BINANCE-FUTURES
date range      2024-01-02 → 2024-01-02  (single day)
instruments     BTCUSDT;ETHUSDT  (2 symbols, vs 9 in full fleet)
data_types      trades;book_snapshot_5  (heavy profile)
VM_TASK         cefi-backfill
```

### Execution

- [x] [SCRIPT] P0. Kill zombies from prior session (5 VMs, 2026-04-20 exited, still RUNNING)
- [x] [SCRIPT] P0. Verify Fix #1/#3/#5 commits on origin/live-defi-rollout + tarballs ≤24h old
- [x] [SCRIPT] P0. Launch `cefi-smoke-fixstack-20260422` VM at e2-standard-2
- [x] [AGENT] P0. Tail `gs://deployment-scripts-central-element-323112/vm-logs/cefi-smoke-fixstack-20260422/run.log`
      until `rc=0` or `rc=137` — initial smoke OOM'd (rc=137). P2.B fix required.
- [x] [AGENT] P0. Capture ResourceProfiler peak-RSS sample from log — P2.B smoke `cefi-smoke-p2b-20260423-153352` exited
      rc=0 on e2-standard-2; no 75% RSS warning fired; 0.0 MB dual-write eliminated.
- [x] [AGENT] P0. Inspect `gs://market-data-tick-cefi-central-element-323112/_index/availability_index.parquet` for
      2026-04-18 BINANCE-FUTURES + BINANCE-SPOT + BYBIT rows — `capture_status` populated ✅
- [x] [AGENT] P0. Record smoke result summary: `cefi-smoke-p2b-20260423-153352` rc=0 (2026-04-23); 251451 manifest
      entries; 10M+ rows canonical; P2.B dual-write + small_frames accumulation eliminated (MTDS 1364211). Smoke gate
      passed; fleet relaunch unblocked.

### Success Criteria (Smoke)

1. VM exits `rc=0` (not SIGKILL, not CMD_PID stall from watchdog)
2. Log contains ≥2 `"Manifest updated"` lines (one per symbol-day — per-shard flush firing, not just per-date)
3. Log contains per-shard counters `rows_in>0 rows_out>0 events_emitted>0`
4. Manifest parquet has 2024-01-02 rows with `venue=BINANCE-FUTURES` +
   `capture_status IN (captured, empty_confirmed, attempted_failed)` (at least one `captured`)
5. Peak RSS ≤ 1 GB on Linux glibc (macOS benchmark was 498 MB)
6. If 75% warning fires: `MANIFEST_EMERGENCY_FLUSH` event emits with `flushed_rows_per_bucket` populated

### Gate

**Only proceed to the 95-VM full relaunch (next section) after ALL 6 smoke criteria pass.** If any fail, fix before
scaling.

## Phase: Fleet Relaunch at e2-standard-2 (pending smoke)

### Why

Post-smoke, `launch-cefi-sharded-backfill.sh:160` heavy-profile machine type must be downgraded from `e2-highmem-4` →
`e2-standard-2`. Target: CeFi MTDS coverage 33.54% → 90%+ (bounded by Tardis sub-license coverage, not memory). TradFi
similar.

### Execution

- [x] [SCRIPT] P0. Edit `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh:160` — heavy profile e2-highmem-4
      → e2-standard-2 (already done: both heavy+light set to e2-standard-2 per P2.B comment in script)
- [x] [SCRIPT] P0. `/opt/homebrew/bin/bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group CEFI`
      (tarball refreshed 2026-04-23T13:47:33Z — covers MTDS 1364211 P2.B fix)
- [x] [SCRIPT] P0. `DRY_RUN=1 bash scripts/vm/launch-cefi-sharded-backfill.sh` — confirmed 95 VMs, metadata correct
- [x] [SCRIPT] P0. Full launch (~95 VMs) — launched 2026-04-23 ~14:43 UTC; 95/95 RUNNING confirmed
- [ ] [AGENT] P0. Monitor via `gcloud compute instances list`; reap zombies with `xargs -P 20` parallel delete pattern
- [ ] [AGENT] P0. Post-drain: `/api/data-status/turbo?service=market-tick-data-service&force=true` → CEFI completion_pct
      should climb 33.54% → 90%+
- [ ] [AGENT] P0. Record final capture_status distribution + rc count (rc=0 vs rc=137 vs other)
