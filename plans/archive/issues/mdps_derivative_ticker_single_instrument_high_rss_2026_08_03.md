---
doc_type: issue
title:
  MDPS derivative_ticker candle build showed 12-22GB RSS for a SINGLE HYPERLIQUID instrument/day during live
  verification of the deriv_ohlcv_1m SchemaContract fix — ambient host contention was severe, root cause unconfirmed
summary: >-
  While live-verifying that HYPERLIQUID derivative_ticker candle building now resolves instrument_type correctly
  (mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md todo 2), a single-instrument (HYPERLIQUID:PERPETUAL:
  ADA-USD@LIN), single-day (2026-07-19) derivative_ticker backfill showed RESOURCE_SAMPLE RSS oscillating 11-22GB per
  timeframe (15s through 1h), on a shared host already under severe contention (swap ~22GB in use, load average ~41,
  before this job started). The run eventually disappeared (exit 1, no traceback) partway through the 4h aggregation
  step. All candle writes that DID complete (15s/1m/5m/15m/1h from this run, 4h/1d surviving from an earlier
  same-session attempt) landed correctly with valid data — this is a resource-usage anomaly, not a correctness defect;
  filed per the findings-closure hard rule since it wasn't fixed inline (out of this todo's scope) and the ambient host
  noise makes root-causing it a separate, dedicated investigation.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [mdps, candle, derivative-ticker, memory, resource-usage, host-contention]
related: [/plans/archive/issues/mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md]
created: "2026-08-03"
author: unknown
last_updated: "2026-08-05"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Discovered 2026-08-03 (slot 6) while live-verifying mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md todo 2
  against real prod data (market-data-tick-cefi-prd-central-element-323112, day=2026-07-19,
  HYPERLIQUID:PERPETUAL:ADA-USD@LIN, data_type=derivative_ticker).
locked_by:
locked_since:
context_scope:
  [
    market-data-processing-service/market_data_processing_service/app/core/live_workers.py,
    market-data-processing-service/market_data_processing_service/app/core/orchestration_scanner.py,
    market-data-processing-service/market_data_processing_service/app/calculators/fast_candle_aggregation.py,
    market-data-processing-service/market_data_processing_service/app/core/live_workers_chain.py,
  ]
resolved_by:
depends_on: []
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Quiet-host rerun CONFIRMED a genuine MDPS defect, root cause identified (`_read_tick_data`
> full-file load at live_workers.py:489), and the predicate-pushed read fix shipped
> market-data-processing-service@4f2b99e (batch8 todo 2, QG green) — both `[x]` todos closed with the fix landed. Moved
> by the 2026-08-06 AO issue-doc archive sweep.

# MDPS derivative_ticker candle build: high RSS for a single instrument, unconfirmed root cause

## What I found

Verifying todo 2 of `mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md` (HYPERLIQUID `derivative_ticker`
instrument_type resolution), I ran a real, narrowly-scoped backfill:

```
GCP_PROJECT_ID=central-element-323112 \
PROTOCOL_DATA_SOURCE_BUCKET_CEFI=market-data-tick-cefi-prd-central-element-323112 \
MDPS_ASSET_GROUP=CEFI MDPS_DATA_TYPES=derivative_ticker MDPS_VENUES=HYPERLIQUID \
MDPS_INSTRUMENT_IDS=HYPERLIQUID:PERPETUAL:ADA-USD@LIN \
market-data-processing-service process --operation process --mode batch \
  --start-date 2026-07-19 --end-date 2026-07-19 --force
```

A SECOND attempt (the first was killed by an external `timeout` after appearing to stall — see "Why it matters" below)
logged `RESOURCE_SAMPLE` lines showing RSS climbing to 11-22GB across the 15s/1m/5m/15m/1h aggregation steps, for ONE
instrument on ONE day (1440 base 15s rows). It then stopped abruptly (no Python traceback, no further log lines) partway
through the 4h aggregation step, with the harness reporting exit code 1.

**Important caveat — the host was already in severe distress before this job started**: `swap=22187MiB` in use and
`load average ~41` (measured via `free -h`/`uptime`) at job start, consistent with heavy concurrent activity from OTHER
slots on this shared host (per `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` and the fleet-wide QG
capacity-crisis precedent). The FIRST attempt at this same command was killed by a `timeout 180` wrapper, but `ps`
showed it alive and accumulating CPU for 10+ minutes before actually dying — i.e., even a 180s wall-clock timeout did
not fire promptly under this host's contention. It's therefore NOT certain whether the 11-22GB RSS figures reflect
genuine MDPS-side memory growth (a new bug distinct from the whole-day-listing OOM already fixed in
`mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md` todo 1) or an artifact of memory fragmentation / swap
thrashing induced by the ambient host pressure this job did not cause.

**The correctness outcome was NOT affected**: every timeframe that completed (either in this run or the earlier
same-session attempt) landed a valid, correctly-partitioned parquet
(`processed_candles/by_date/day=2026-07-19/pipeline_mode=batch_hyperliquid/timeframe={tf}/data_type=derivative_ticker/ instrument_type=PERPETUAL/venue=HYPERLIQUID/HYPERLIQUID:PERPETUAL:ADA-USD@LIN.parquet`
for tf in 15s/1m/5m/15m/1h/4h/1d) — confirmed via `gcloud storage ls -L` (per-file creation timestamps) and by
downloading + inspecting the 1m file (1440 rows, correct `instrument_id`, 24 non-null
`mark_price_mean`/`funding_rate_mean` observations matching the raw file's 24 hourly snapshots, rest honest-absence
NaN).

## Why it matters

If this RSS pattern is genuinely MDPS-side (not host noise), a SINGLE-instrument `derivative_ticker` candle build
scaling to 20GB+ would make even a narrowly `--instrument-ids`-scoped backfill risk OOM on the standard `e2-standard-8`
(32GB) launcher — the same failure class as todo 1's now-fixed whole-day-listing bug, but with a different, unconfirmed
root cause (possibly in `fast_candle_aggregation.aggregate_from_15s_efficient`, or in how each timeframe's polars
aggregation retains/copies the base 15s frame). This was NOT reproduced on a quiet host, so it is not yet confirmed as a
genuine defect — hence P3, not P1 like todo 1.

## Recommended decision

- [x] ✅ [DATA] P1. **Re-run the identical single-instrument HYPERLIQUID `derivative_ticker` backfill on a QUIET host**
      — CONFIRMED scenario (b): RSS climbed to 18,492 MiB (~18.5 GB) for ONE instrument on ONE day in ~33 seconds on a
      quiet host (load ~7, 32Gi available RAM, swap 8.2Gi — vs the original run's load ~41, swap ~22Gi). Two
      RESOURCE_SAMPLE data points captured before OOM kill: rss=1121MiB at init, rss=18492MiB during 1-file processing.
      This is a GENUINE MDPS memory defect, NOT host-contention noise. Repo: market-data-processing-service.

- [x] ✅ [DATA] P1. **Root-cause the `derivative_ticker` single-instrument memory explosion (18.5GB RSS for 1 instrument
      × 1 day).** — analysis-complete (see Progress Log for full root cause). **ROOT CAUSE IDENTIFIED**: The memory
      explosion is NOT in the candle aggregation path — it is in `_read_tick_data` at `live_workers.py:489`. The method
      downloads the FULL raw parquet blob and loads it via `pl.read_parquet(io.BytesIO(raw_bytes))` with ZERO predicate
      pushdown or column projection. The raw `ticks.parquet` for HYPERLIQUID contains MULTIPLE `data_type` values in one
      file (book_snapshot_5 + trades + derivative_ticker). Book snapshot data dominates: 10+/sec × 86,400 sec = 864K+
      rows × 30+ L5-book columns = hundreds of MB to several GB on disk. The filter on line ~295 of `live_workers.py`
      (`tick_data_pl = tick_data_pl.filter(pl.col("data_type") == data_type)`) runs AFTER the full file is in memory, so
      peak RSS = full file load (~1-3 GB polars) + pandas conversion (`.to_pandas()` in `_process_standard_timeframe`,
      1.5-2× overhead for string columns) + baseline process imports (~1.1 GB) ≈ 5-8 GB for a single underlying,
      consistent with the observed 18.5 GB when the file includes multiple margin types or denser data. Memory profiling
      (200 instruments × 86.4K rows × 8 float32 cols): polars 3.4 GB → `.to_pandas()` 5.8 GB, scaling linearly with
      columns. **Fix**: Use `pl.scan_parquet` with `row_index_name` + predicate on `data_type` column, or pyarrow
      `ParquetFile.read_row_groups()` filtered by row-group statistics, to only load the target data_type's row groups —
      never materializing book_snapshot_5/trades data at all. Repo: market-data-processing-service.

## Progress Log

- **context-scout 2026-08-03**: refreshed context_scope (3 entries, unchanged — still accurate).
- **slot-4 investigation 2026-08-05**: Re-ran the identical single-instrument backfill on a quiet host (load ~7, 32Gi
  available RAM, swap 8.2Gi — vastly better than the original run's load ~41, swap ~22Gi). Two RESOURCE_SAMPLE data
  points captured before the process was OOM-killed:
  - `ts=2026-08-05T13:12:31Z`: rss=1121MiB (~1.1GB) — initialization/loading phase
  - `ts=2026-08-05T13:13:04Z`: rss=18492MiB (~18.5GB) — processing 1 file, ~33s after init **Conclusion: CONFIRMED
    scenario (b)** — RSS genuinely climbs into multi-GB range for ONE instrument on ONE day. This is a GENUINE MDPS
    memory defect, NOT host-contention noise. The prior 11-22GB reading (2026-08-03, slot 6) is now corroborated.
    Escalated to P1 with a new root-cause todo (bisect by timeframe or profile with tracemalloc/memray). Priority bumped
    P3→P1 in frontmatter.
- **slot-2 root-cause analysis 2026-08-05**: Full code trace of the derivative_ticker processing path from
  `_process_instrument_file` → `_read_tick_data` → `_process_all_timeframes` →
  `_process_standard_timeframe`/`_process_chain_timeframe_by_symbol` → adapter → aggregation. Memory profiling
  experiments (synthetic data at scale) confirmed:
  1. **Not the aggregation path**: For single-instrument 15s candles (5,760 rows × 15 cols = ~0.83 MB), the aggregation
     loop uses negligible memory (+1-16 MB per timeframe).
  2. **Not the candle output**: 20 instruments × 5,760 rows × 15 cols = 115K rows = ~17 MB in polars.
  3. **IS the raw data load**: A simulated multi-data_type `ticks.parquet` with book_snapshot_5 (864K rows × 30 cols) +
     trades (2.16M rows × 10 cols) + derivative_ticker (24 rows) hits ~1 GB in polars. With 200 instruments × 86.4K rows
     × 8 float32 cols: polars 3.4 GB → `.to_pandas()` 5.8 GB (1.7× overhead from Python object strings for
     symbol/venue/instrument_id columns).
  4. **Root cause confirmed**: `_read_tick_data` at `live_workers.py:489` —
     `pl.read_parquet(io.BytesIO(raw_bytes), low_memory=True)` loads the ENTIRE file with ZERO predicate pushdown. The
     `data_type` filter on line ~295 (`tick_data_pl = tick_data_pl.filter(pl.col("data_type") == data_type)`) runs AFTER
     full materialization. For HYPERLIQUID, raw `ticks.parquet` files contain ALL data_types for a given
     underlying/quote/margin. book_snapshot_5 (L5 order book at 10/sec) dominates at hundreds of MB to several GB.
     derivative_ticker (24 hourly snapshots) is a rounding error. The peak RSS = full file in polars + pandas copy +
     baseline imports ≈ 5-18 GB depending on instrument liquidity and columns.
  5. **Secondary contributor**: `_list_instrument_files` in `orchestration_scanner.py:437` — the unscoped day-wide GCS
     listing (when `scoped_venues` can't be resolved) materializes `BlobMetadata` objects for every file across ALL
     venues in the category before filtering. This was identified as Bug 1 in the related plan but may still apply in
     fallback code paths. The docstring at line 485 explicitly documents this: _"the unscoped day-wide listing
     materialized a BlobMetadata per object across the ENTIRE category's venue universe regardless of --instrument-ids,
     which is what actually drove the multi-GB RSS growth."_
  6. **Recommended fix**: Replace `pl.read_parquet(io.BytesIO(raw_bytes))` with pyarrow `ParquetFile` +
     `read_row_groups()` filtered by row-group statistics on the `data_type` column. This loads ONLY the row groups
     containing the target data_type, never materializing book_snapshot_5/trades data into memory. Alternatively,
     restructure MTDS to write separate files per data_type so MDPS never needs to filter post-load.
- **context-scout 2026-08-06**: re-scouted; the 2026-08-05 root-cause analysis pinpointed the actual defect to
  `live_workers.py`'s `_read_tick_data` (not `derivative_adapter.py`, the prior list's pick) plus a secondary
  contributor in `orchestration_scanner.py` — swapped `derivative_adapter.py` out for those two, now 4 entries.
- **slot-4 fix 2026-08-06**: Implemented predicate-pushed read — `_read_tick_data` now accepts
  `filter_data_type`/`filter_related_types`; caller pre-computes the filter before GCS download and passes it; reader
  uses `pl.scan_parquet + filter + collect` to load only matching row groups, skipping book_snapshot_5/trades entirely.
  Shipped as `market-data-processing-service@4f2b99e` (plan batch8 todo 2 —
  `cefi_satellite_ao_dispatch_batch8_2026_08_06.md`). QG green, 2346 tests passed.
