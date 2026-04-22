---
title: "CeFi + TradFi Tick Data Backfill"
status: active
created: 2026-04-10
locked_by: live-defi-rollout
locked_since: 2026-04-10
---

# CeFi + TradFi Tick Data Backfill

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
- [ ] [SCRIPT] P0. Create VM launch script for CME ES futures backfill (trades, ohlcv_1m, tbbo,
      dates=2021-01-01→2026-04-10)
- [ ] [SCRIPT] P0. Create VM launch script for CBOE VIX backfill (ohlcv_15m, dates=2025-11-13→2026-04-10)
- [ ] [SCRIPT] P1. Launch TradFi VMs
- [ ] [SCRIPT] P2. Verify manifest entries

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

Prior 95-VM launch (2026-04-19) saw 55 heavy VMs hit `rc=137` SIGKILL during
parquet encoding — OOM on `e2-standard-4` (16 GB) and recurring on `e2-highmem-4`
(32 GB) because per-date `writer_manifest.write()` lost in-memory manifest rows
on SIGKILL. Three fixes landed since (on origin/live-defi-rollout):

- **Fix #1** MTDS `ab91a2c` — `ManifestWriter(..., batch_size=1)` in
  `engine/orchestrator.py:1243` so every shard `.add()` auto-flushes to the UTL
  module-level buffer. End-of-date `.flush()` backstop.
- **Fix #3** MTDS `ab91a2c` — pyarrow streaming decompress in
  `_decompress_and_parse_csv_legacy` (gzip.GzipFile + `pacsv.open_csv` +
  `split_blocks=True, self_destruct=True`). Benchmarked 1050→498 MB peak RSS on
  BYBIT BTCUSDT 2024-01-02 (2.1× reduction).
- **Fix #5** UTL `881d9ec0` + MTDS `b888eff` — ResourceProfiler 75% RSS warning
  fires `flush_all_live_writers()` via `_LIVE_WRITERS: set[weakref.ref]` +
  `MANIFEST_EMERGENCY_FLUSH` event before the 85% CRITICAL tripwire.

Smoke must validate the full stack on a real VM at the target machine type
(`e2-standard-2`, 8 GB) before relaunching the 95-VM fleet.

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
- [ ] [AGENT] P0. Tail `gs://deployment-scripts-central-element-323112/vm-logs/cefi-smoke-fixstack-20260422/run.log` until `rc=0` or `rc=137`
- [ ] [AGENT] P0. Capture ResourceProfiler peak-RSS sample from log (target ≤1 GB on Linux glibc)
- [ ] [AGENT] P0. Inspect `gs://market-data-tick-cefi-central-element-323112/_index/availability_index.parquet` for 2024-01-02 BINANCE-FUTURES rows with `capture_status` populated
- [ ] [AGENT] P0. Record smoke result summary in this plan

### Success Criteria (Smoke)

1. VM exits `rc=0` (not SIGKILL, not CMD_PID stall from watchdog)
2. Log contains ≥2 `"Manifest updated"` lines (one per symbol-day — per-shard flush firing, not just per-date)
3. Log contains per-shard counters `rows_in>0 rows_out>0 events_emitted>0`
4. Manifest parquet has 2024-01-02 rows with `venue=BINANCE-FUTURES` + `capture_status IN (captured, empty_confirmed, attempted_failed)` (at least one `captured`)
5. Peak RSS ≤ 1 GB on Linux glibc (macOS benchmark was 498 MB)
6. If 75% warning fires: `MANIFEST_EMERGENCY_FLUSH` event emits with `flushed_rows_per_bucket` populated

### Gate

**Only proceed to the 95-VM full relaunch (next section) after ALL 6 smoke criteria pass.** If any fail, fix before scaling.

## Phase: Fleet Relaunch at e2-standard-2 (pending smoke)

### Why

Post-smoke, `launch-cefi-sharded-backfill.sh:160` heavy-profile machine type must be downgraded from `e2-highmem-4` → `e2-standard-2`. Target: CeFi MTDS coverage 33.54% → 90%+ (bounded by Tardis sub-license coverage, not memory). TradFi similar.

### Execution

- [ ] [SCRIPT] P0. Edit `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh:160` — heavy profile e2-highmem-4 → e2-standard-2
- [ ] [SCRIPT] P0. `/opt/homebrew/bin/bash deployment-service/scripts/vm/create-code-tarballs.sh --category CEFI` (tarball refresh)
- [ ] [SCRIPT] P0. `DRY_RUN=1 bash scripts/vm/launch-cefi-sharded-backfill.sh` — confirm metadata
- [ ] [SCRIPT] P0. Full launch (~95 VMs)
- [ ] [AGENT] P0. Monitor via `gcloud compute instances list`; reap zombies with `xargs -P 20` parallel delete pattern
- [ ] [AGENT] P0. Post-drain: `/api/data-status/turbo?service=market-tick-data-service&force=true` → CEFI completion_pct should climb 33.54% → 90%+
- [ ] [AGENT] P0. Record final capture_status distribution + rc count (rc=0 vs rc=137 vs other)
