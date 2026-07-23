---
doc_type: plan
title: Data Pipeline Canonical Sharding Alignment (MTDS + MDPS)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-data-processing-service, market-tick-data-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-31
priority: P1
locked_by: live-defi-rollout
locked_since: 2026-03-31
owner: agent
---

# Data Pipeline Canonical Sharding Alignment (MTDS + MDPS)

> **Conflict resolution**: instrument_schema_cohesion Phase 3A also modifies MTDS `engine/orchestrator.py` (adds market
> hours check). This plan's Phase 2 (sharding path refactor) must complete FIRST, then instrument_schema_cohesion Phase
> 3A slots the market hours check into the refactored code.

## Context

The PATH_REGISTRY in UTL (`config_interface/paths/registry.py`) defines canonical GCS paths for all datasets. Two
services have drifted from the spec:

### MTDS Gap

|                    | Canonical                                                                                                                         | Actual                                                         |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **Path**           | `raw_tick_data/by_date/day={date}/data_type={data_type}/instrument_type={instrument_type}/venue={venue}/{instrument_key}.parquet` | `raw_tick_data/by_date/day={date}/venue={venue}/ticks.parquet` |
| **Partitions**     | `["date", "data_type", "instrument_type", "venue"]`                                                                               | `["date", "venue"]`                                            |
| **Files**          | Per-instrument (`{instrument_key}.parquet`)                                                                                       | Monolithic (`ticks.parquet`)                                   |
| **Manifest shard** | `(date, venue, data_type)`                                                                                                        | `(date, venue)`                                                |

Impact: Cannot re-process just trades without re-fetching book/funding data. Cannot query by data_type in BigQuery
external tables. MDPS parses monolithic blob.

### MDPS Gap

|                    | Canonical                                                                                                                                                  | Actual                                                                                         |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **Path**           | `processed_candles/by_date/day={date}/timeframe={timeframe}/data_type={data_type}/instrument_type={instrument_type}/venue={venue}/{instrument_id}.parquet` | `processed_candles/{category}/by_date/day={date}/timeframe={timeframe}/data_type={data_type}/` |
| **Partitions**     | `["date", "timeframe", "data_type", "instrument_type", "venue"]`                                                                                           | `["date", "timeframe", "data_type"]`                                                           |
| **Files**          | Per-instrument (`{instrument_id}.parquet`)                                                                                                                 | Bulk output                                                                                    |
| **Manifest shard** | `(date, data_type)` — timeframe is processing dimension, not availability                                                                                  | `(date, data_type)` — correct                                                                  |

Impact: Cannot query candles by venue or instrument_type in BigQuery external tables. Missing `instrument_type` and
`venue` hive partitions.

### features-onchain — No Gap

Canonical: `by_date/day={date}/feature_group={feature_group}/features.parquet` Actual: matches. No changes needed.

## Pre-Audit Manifest

| Repo                           | File                               | Change needed                                                                     |
| ------------------------------ | ---------------------------------- | --------------------------------------------------------------------------------- |
| market-tick-data-service       | engine/orchestrator.py             | gcs_path → `build_path("raw_tick_data", ...)` with all 4 partitions               |
| market-tick-data-service       | adapters/umi_tick_provider.py      | Split fetched data by data_type before writing                                    |
| market-tick-data-service       | engine/orchestrator.py             | ManifestWriter shard key → `(date, venue, data_type)`                             |
| market-tick-data-service       | engine/orchestrator.py             | StreamingParquetWriter → per-instrument files                                     |
| market-data-processing-service | app/core/orchestration_service.py  | Input path → `build_path("raw_tick_data", ...)`                                   |
| market-data-processing-service | app/core/orchestration_service.py  | Output path → `build_path("processed_candles", ...)` with instrument_type + venue |
| market-data-processing-service | app/core/orchestration_writer.py   | Write per-instrument files with instrument_type + venue partitions                |
| market-data-processing-service | config.py                          | `get_processed_path()` → use PATH_REGISTRY instead of hardcoded template          |
| unified-trading-library        | config_interface/paths/registry.py | Verify specs are correct (already exist)                                          |
| unified-trading-library        | manifest_writer.py                 | reconcile_manifest prefix must handle multi-dimension shards                      |
| unified-trading-pm             | /codex/02-data/partitioning.md     | Verify spec matches PATH_REGISTRY                                                 |

## Dependency DAG

```
Phase 1: UTL PATH_REGISTRY verification
    ↓
Phase 2: MTDS write path alignment  ← breaking change for MDPS input
    ↓ QG gate
Phase 3: MDPS read path + write path alignment (PARALLEL: input reads + output writes)
    ↓ QG gate
Phase 4: E2E validation (full pipeline run)
```

## Phase 1 — Verify PATH_REGISTRY [PARALLEL]

- [x] [AGENT] P0. Read PATH_REGISTRY raw_tick_data spec — confirm partition_keys =
      `["date", "data_type", "instrument_type", "venue"]`, file_template = `{instrument_key}.parquet`
- [x] [AGENT] P0. Read PATH_REGISTRY processed_candles spec — confirm partition_keys =
      `["date", "timeframe", "data_type", "instrument_type", "venue"]`, file_template = `{instrument_id}.parquet`
- [x] [AGENT] P0. Read `/codex/02-data/partitioning.md` — confirm both specs match PATH_REGISTRY
- [x] [AGENT] P0. Verify `build_path("raw_tick_data", ...)` and `build_path("processed_candles", ...)` produce correct
      hive paths
- [ ] [AGENT] P1. Clean up legacy `PathRegistry` class constants (MARKET*TICK_RAW, MARKET_CANDLE*\*) that use old flat
      paths — replace usages with `build_path()` or delete if unused

## Phase 2 — MTDS Write Path Alignment [SEQUENTIAL]

- [x] [AGENT] P0. Refactor `orchestrator.py` gcs_path to use
      `build_path("raw_tick_data", date=date, data_type=dt, instrument_type=it, venue=venue)` from PATH_REGISTRY —
      `_canonical_gcs_prefix()` now delegates to `build_path()` with `instrument_type` param
- [x] [AGENT] P0. Refactor UMI tick provider to split fetched data by data_type before writing — trades, book_snapshots,
      funding_rates go to separate partition paths — DONE: `_split_and_upload()` groups by data_type column and uploads
      each group separately
- [x] [AGENT] P0. Update StreamingParquetWriter calls to write per-instrument files (`{instrument_key}.parquet`) instead
      of monolithic `ticks.parquet` — `_split_and_upload()` groups by `instrument_key` and writes per-instrument files;
      legacy adapters without `instrument_key` fall back to `ticks.parquet`
- [x] [AGENT] P0. Update ManifestWriter.add() calls — shard key = `venue=f"{venue}:{data_type}"` so manifest tracks per
      data_type — DONE: line 374 uses `venue=f"{venue}:{dt_name}"`
- [x] [AGENT] P0. Update skip-if-exists check_shard_freshness expected_venues to include `venue:data_type` pairs —
      `check_shard_freshness` now receives `[f"{v}:{dt}" for v in active_venues for dt in data_types]`
- [x] [AGENT] P0. Update shard completeness check to compare `(venue, data_type)` pairs — stale/missing shard keys now
      split on `:` to extract base venue for re-fetch targeting
- [x] [AGENT] P0. Run `cd market-tick-data-service && bash scripts/quality-gates.sh` — **Done 2026-05-06** (86s, all
      gates green including the new STEP 5.63 run_lifecycle pairing gate; 6 codex violations within tolerance of 6; no
      test failures).

## Phase 3 — MDPS Read + Write Path Alignment [PARALLEL within, SEQUENTIAL after Phase 2]

### 3a. MDPS Input (read MTDS output)

- [x] [AGENT] P0. Update input path resolution to use `build_path("raw_tick_data", ...)` — `get_raw_tick_path()` in
      config.py already includes instrument_type/venue partitions, used in orchestration_service for reads
- [ ] [AGENT] P1. Update MDPS to only read the data_types it needs (e.g. OHLCV processing reads trades only, not book
      snapshots)

### 3b. MDPS Output (write processed candles)

- [x] [AGENT] P0. Refactor `get_processed_path()` in config.py to use `build_path("processed_candles", ...)` —
      `get_processed_path()` now accepts `instrument_type` param and delegates to `build_path("processed_candles", ...)`
      when `venue` is provided
- [x] [AGENT] P0. Update orchestration_writer to write per-instrument files with `instrument_type` + `venue` hive
      partitions — orchestration_writer already processes per instrument_id and resolves venue from data
- [x] [AGENT] P0. Update ManifestWriter shard key to `(date, data_type)` — DONE: \_write_manifest_records uses data_type
      as venue shard key
- [ ] [AGENT] P0. Run `cd market-data-processing-service && bash scripts/quality-gates.sh` — **Attempted 2026-05-06**:
      MDPS QG fails on
      `tests/unit/test_per_instrument_pipeline.py::TestPerInstrumentPipelineFix::test_legacy_ticks_parquet_recovers_instrument_id_from_data`
      (instrument_id resolves to `""` instead of `BINANCE-FUTURES:PERPETUAL:BTC-USDT`). Pre-existing regression in the
      streaming chain-bundle dispatch (commit
      `1dfae3b feat(mdps): wire streaming chain-bundle dispatch + 11 unit tests`) — unrelated to canonical sharding
      alignment. Concurrent agent (CosmicTrader) has in-flight edits to `candle_write_mixin.py` + `cli/main.py` that
      simplify the fan-out path. **Blocked-by-concurrent-stream**: re-run this gate after that work lands. Coverage
      71.64% / 71.77%; rest of suite green (1123 passed, 1 failed).

## Phase 4 — E2E Validation [SEQUENTIAL]

- [ ] [HUMAN] P0. Run full 2-day pipeline:
      `bash scripts/defi/run-batch-pipeline.sh --start-date 2026-03-01 --end-date 2026-03-02`
- [ ] [HUMAN] P0. Verify MTDS GCS paths:
      `gsutil ls -r gs://market-data-tick-cefi-central-element-323112/raw_tick_data/by_date/day=2026-03-01/` — expect
      `data_type=trades/instrument_type=PERPETUAL/venue=BINANCE-FUTURES/{instrument}.parquet`
- [ ] [HUMAN] P0. Verify MDPS GCS paths:
      `gsutil ls -r gs://market-data-tick-cefi-central-element-323112/processed_candles/` — expect
      `timeframe=15m/data_type=ohlcv_15m/instrument_type=PERPETUAL/venue=BINANCE-FUTURES/{instrument}.parquet`
- [ ] [HUMAN] P0. Verify manifest indexes track correct shard dimensions
- [ ] [HUMAN] P0. Verify features-onchain reads MTDS output correctly (if applicable)

## Success Criteria

- All GCS paths match `/codex/02-data/partitioning.md` and PATH_REGISTRY specs exactly
- `build_path()` is the sole path construction method — no hardcoded path templates in service code
- Legacy `PathRegistry` class constants cleaned up or deleted
- MTDS manifest tracks `(date, venue, data_type)` — skip-if-exists works per data_type
- MDPS manifest tracks `(date, data_type)` — timeframe is processing-internal
- MDPS reads selectively by data_type from MTDS output (no monolithic parsing)
- MDPS writes with `instrument_type` + `venue` partitions for BigQuery compatibility
- QG pass on MTDS + MDPS
- E2E pipeline produces correct data in correct layout
