---
type: audit-findings
title: MDPS Long-Running Observability — Audit Findings
epic: observability_master
auditor: claude opus 4.7 (slot main subagent)
date: "2026-05-28"
status: complete
name: mdps_long_running_observability_2026_05_28
audit_instructions: mtds_mdps_master_audit_instructions.md
parent_plan: mdps_long_running_multi_shard_architecture_audit_2026_05_28.md
---

# MDPS Long-Running Observability — Audit Findings

## What I read

- `market-data-processing-service/app/core/batch_workers.py:216-278` — `_on_memory_warning`, `_unpause_if_safe`,
  `MEMORY_BACKPRESSURE_ENGAGED` / `MEMORY_BACKPRESSURE_RESOLVED` events
- `market-data-processing-service/app/core/orchestration_base.py:79-100` — `_cleanup_after_day` with RSS logging
- `market-data-processing-service/app/core/orchestration_state.py:45-60` — duplicate `_cleanup_after_day` implementation
- `market-data-processing-service/cli/handlers/process_handler.py:680+` — per-date loop iteration
- `unified-trading-library/unified_trading_library/lifecycle/resource_profiler.py:1-760` — ResourceProfiler sampling (5s
  default), `RESOURCE_PROFILER_SAMPLE` emit (30s default), memory warning tripwire (75%), critical tripwire (85%),
  debounce windows
- `unified-trading-library/unified_trading_library/events/__init__.py:337-366` — `log_event` signature + sink
  integration
- Codex:
  - `codex/03-observability/lifecycle-events.md` — mandatory 11-event batch sequence (STARTED → VALIDATION_COMPLETED →
    DATA_INGESTION_COMPLETED → PROCESSING_COMPLETED → PERSISTENCE_COMPLETED → STOPPED or FAILED)
  - `codex/03-observability/coordination-events.md` — service-to-service events (out of scope for batch MDPS)
  - `codex/03-observability/slos.md` — dashboard + alerting patterns

## What exists today

| Event / log signal                                | Source                                    | When it fires                                         | Structured fields                                                                              | Aggregated downstream? | Operator-visible                       |
| ------------------------------------------------- | ----------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------- | -------------------------------------- |
| `MEMORY_BACKPRESSURE_ENGAGED`                     | `batch_workers.py:227`                    | When system memory ≥ 85%                              | `system_memory_percent`, `process_rss_bytes`, `max_pause_sec`                                  | Yes (to event sink)    | Yes, in logs                           |
| `MEMORY_BACKPRESSURE_RESOLVED`                    | `batch_workers.py:248-271`                | When memory drops below 75% OR max_pause_sec exceeded | `reason`, `system_memory_percent`, `paused_for_sec`                                            | Yes (to event sink)    | Yes, in logs                           |
| `💾 Memory after cleanup: X MB`                   | `orchestration_base.py:98`                | After `_cleanup_after_day` completes                  | None (log-only)                                                                                | No                     | Yes, text log                          |
| `🧹 Cleaning up memory after processing <date>`   | `orchestration_base.py:81`                | Before `_cleanup_after_day` runs                      | None (log-only)                                                                                | No                     | Yes, text log                          |
| `📉 date-boundary GC for <date>: RSS X MB → Y MB` | `process_handler.py` (Phase 2.2 addition) | After GC at date boundary                             | None (log-only, implied: date, before_mb, after_mb)                                            | No                     | Yes, text log                          |
| `RESOURCE_PROFILER_SAMPLE`                        | `resource_profiler.py:621-629`            | Every 30 seconds                                      | Full `ResourceSample` (process RSS, VMS, threads, system memory %, disk usage per path, CPU %) | Yes (to event sink)    | Partially (at INFO level, high volume) |
| `PROCESS_MEMORY_WARNING`                          | `resource_profiler.py:658-676`            | When system memory ≥ 75% (warning threshold)          | Sample dict + `memory_warning_percent`, `critical_memory_percent`, in-flight summary           | Yes (to event sink)    | Yes, at WARNING level                  |

**Signal assessment**: Current telemetry is **heavy on reactive log emission, light on per-shard structure**. The
operator sees:

- System-level backpressure engage/disengage (no per-shard granularity)
- Post-cleanup RSS in **MB as a float string** (hard to parse, no shard/date context)
- GC reclaim as **implied deltas without per-shard attribution**
- 30-second resource samples covering the entire process (not aggregated per shard)

## The Phase 3.2 retry signal — what we saw vs what we needed

**Log excerpt from 2026-04-15 canary (the failing run)**:

```
13:29:42 Listed 18 files (pre-count)
13:30:30 Listed 4 files (processing scanner)
13:30:31 Processing candles for 2026-04-15
...
13:33:04 ✅ trades complete: 4/4 succeeded in 154.6s
13:33:04 🏁 cefi processing complete: 4/4 succeeded, 0 errors in 202.6s
13:33:04 🧹 Cleaning up memory after processing 2026-04-15
13:33:05 💾 Memory after cleanup: 15692.3515625 MB
13:33:05 📉 date-boundary GC for 2026-04-15: RSS 15692 MB → 15692 MB (freed 0 MB)
13:33:05 Processing candles for 2026-04-16
[VM silent for ~18 min as of 19:21 IST — then OOM kill]
```

**What this tells us**:

- 4 instruments × 1 day processed in 202.6 seconds
- Peak RSS around 15.7 GB
- **Post-cleanup RSS remains 15.7 GB** (no reclaim) — signal that `_cleanup_after_day` is not reaching the allocator
  holding the data
- Candles reading started at 13:33:05 for 2026-04-16
- **No per-shard boundary markers** (when did instrument 1 finish? when did instrument 2 peak?)

**What the operator NEEDED to predict OOM at T+5min before it happened**:

1. **Per-shard completion event with peak RSS**: "Shard X (2026-04-15, cefi, instrument-1) completed in 50s, peak RSS
   4.2 GB, final RSS 3.1 GB (73% retention)"
   - **Why**: operator can trend per-shard costs; if trend shows 4.2 GB × 90 shards = 378 GB projected, OOM is
     guaranteed before T+0min
2. **Date-boundary reclaim ratio**: "Date 2026-04-15 cleanup: RSS 15.7 GB → 15.7 GB = 0% freed (expected >60%)"
   - **Why**: 0% freed is a screaming signal; the hook isn't reaching the right allocators
3. **Per-shard memory components**: "Shard manifest: 526 MB compressed (decompressed ~2.1 GB), wall-clock 12s;
   instruments DataFrame 1.8 GB, wall-clock 18s"
   - **Why**: operator can isolate whether the 25 GB floor is manifest re-reads, instrument caching, or polars arena
     retention

**What we couldn't distinguish**:

- Is the 18 min silence "slow work" or "deadlocked in backpressure waiting for memory to drop"?
  - **Signal needed**: `BACKPRESSURE_DEADLOCK_RISK` when paused > N seconds AND no shard submissions completed in that
    window
- Which data structure owns the 25 GB per-day?
  - **Signal needed**: breakdown of manifest bytes, instruments bytes, candle cache bytes per shard

## Recommended structured events

### 1. `SHARD_STARTED`

- **Fires at**: `orchestration_base.py` / `process_handler.py`, at shard entry (before
  asset_group/date/data_type/instrument is opened)
- **Structured fields**:
  - `asset_group` (str: cefi/defi/tradfi)
  - `date` (str: YYYY-MM-DD)
  - `data_type` (str: trades/ohlcv/options_chain)
  - `venue` (str, optional)
  - `instrument_id` (str, optional: VENUE:TYPE:SYMBOL)
  - `expected_blob_count` (int: number of source files to process)
  - `rss_mb_before` (float: process RSS in MB at shard start)
- **Why**: operators can track shard entry + baseline memory state; prerequisite for per-shard peak calculation

### 2. `SHARD_COMPLETED`

- **Fires at**: `orchestration_base.py` / `process_handler.py`, after shard write + cleanup, before moving to next shard
- **Structured fields**:
  - `asset_group`, `date`, `data_type`, `venue`, `instrument_id` (match SHARD_STARTED)
  - `candle_count` (int: rows written)
  - `wall_clock_s` (float: elapsed time from start to completion)
  - `rss_mb_peak` (float: peak RSS observed during shard)
  - `rss_mb_after_cleanup` (float: RSS after shard's `_cleanup_after_day`)
  - `cleanup_freed_mb` (float: `rss_mb_peak - rss_mb_after_cleanup`)
  - `retention_rate_pct` (float: 100 \* `rss_mb_after_cleanup / rss_mb_peak`)
- **Why**: operators get per-shard cost model in production; can aggregate to daily floor estimate

### 3. `MANIFEST_LOAD_BYTES`

- **Fires at**: Inside the manifest read path (when parquet is decompressed)
- **Structured fields**:
  - `asset_group`, `date`, `data_type` (optional)
  - `bucket` (str: GCS bucket path prefix)
  - `compressed_size_mb` (float: on-disk size)
  - `decompressed_size_mb_est` (float: in-memory size after read)
  - `wall_clock_s` (float: read + parse wall clock)
- **Why**: per-shard can determine if manifest re-reads dominate the 25 GB floor

### 4. `INSTRUMENTS_LOAD_ROWS`

- **Fires at**: When instruments reference data is loaded (inside candle_processing_service or sampling_service
  initialization)
- **Structured fields**:
  - `asset_group`, `date`
  - `row_count` (int: number of rows in instruments DataFrame)
  - `rss_mb_delta` (float: delta in process RSS from before-load to after-load)
  - `wall_clock_s` (float: load time)
- **Why**: operator can measure if instruments caching is the bottleneck

### 5. `DATE_BOUNDARY_GC` (promote current log to structured event)

- **Fires at**: `orchestration_base.py:79-100`, after `_cleanup_after_day` and GC runs
- **Structured fields**:
  - `date` (str: YYYY-MM-DD)
  - `rss_before_mb` (float)
  - `rss_after_mb` (float)
  - `freed_mb` (float: `rss_before_mb - rss_after_mb`)
  - `reclaim_ratio_pct` (float: 100 \* `freed_mb / rss_before_mb`)
- **Why**: date-level aggregation of shard-level reclaim rates; 0% signals broken cleanup hook

### 6. `BACKPRESSURE_DEADLOCK_RISK` (proactive tripwire)

- **Fires at**: `batch_workers.py:_unpause_if_safe` or a new check in the main loop
- **Fires when**: backpressure has been paused for > `deadlock_risk_window_s` (e.g., 30s) **AND** no shard submissions
  completed in that window
- **Structured fields**:
  - `paused_for_s` (float: how long backpressure has been on)
  - `system_memory_percent` (float: current memory %)
  - `last_shard_submission_ago_s` (float: seconds since last shard entered processing)
  - `in_flight_shards` (int: how many shards currently being processed)
- **Why**: distinguishes "memory genuinely exhausted and paused correctly" from "stuck waiting forever"

## SLO suggestions

| SLO                         | Definition                                                                             | Threshold   | Where it's needed | Measured from                                                           |
| --------------------------- | -------------------------------------------------------------------------------------- | ----------- | ----------------- | ----------------------------------------------------------------------- |
| Per-shard peak RSS limit    | Peak RSS for any single shard ≤ 28 GB on e2-standard-8 (32 GB total, 4 GB OS reserved) | 28 GB       | MDPS backfill VMs | `SHARD_COMPLETED.rss_mb_peak` per shard; alert if any > threshold       |
| Per-shard reclaim ratio     | Cleanup-freed memory / peak memory ≥ 60% for each shard                                | 60%         | MDPS backfill VMs | `SHARD_COMPLETED.retention_rate_pct` per shard; alert if < 60%          |
| Date-level reclaim ratio    | GC reclaim ratio at date boundary ≥ 50%                                                | 50%         | MDPS backfill VMs | `DATE_BOUNDARY_GC.reclaim_ratio_pct` aggregated per date                |
| Median per-shard wall-clock | Median processing wall-clock across all shards in a day ≤ 5 min                        | 5 min       | MDPS backfill VMs | `SHARD_COMPLETED.wall_clock_s` p50 per date                             |
| Backpressure stability      | Time spent in backpressure ≤ 10% of total run wall-clock                               | 10%         | MDPS backfill VMs | Sum of `MEMORY_BACKPRESSURE_RESOLVED.paused_for_sec` / total_wall_clock |
| Deadlock risk SLI           | `BACKPRESSURE_DEADLOCK_RISK` incidents = 0 per run                                     | 0 incidents | MDPS backfill VMs | Count of `BACKPRESSURE_DEADLOCK_RISK` events per run                    |

## Dashboard recommendation

A single operator-facing pane during a long-running backfill VM should surface:

1. **Shard Progress Timeline** (1 panel)
   - Horizontal bar chart: each shard (asset_group + date + instrument) shows wall-clock span, colored by peak-RSS
     (green <10GB, yellow 10-20GB, red >20GB)
   - Allows operator to spot outliers (e.g., one shard at 25GB while others at 5GB indicates data-type-specific bloat)

2. **Per-Date RSS Trajectory** (1 panel)
   - Line chart: X-axis = date, Y-axis = RSS in GB; three lines: (peak RSS, post-cleanup RSS, trend extrapolation to end
     of backfill)
   - Allows operator to see "is the cleanup hook reclaiming memory or are we drifting up 25 GB per day?"

3. **Backpressure Health** (1 panel)
   - Gauge: `% time spent in backpressure` (ideally 0-5%; 20%+ is a warning sign)
   - Gauge: `seconds since last deadlock risk event` (ideally >300; <30 is critical)
   - Text: "Last pause: X seconds ago at system_memory Y%"

4. **Memory Component Attribution** (1 panel)
   - Stacked area chart or pie: breakdown of bytes spent on (manifest, instruments DataFrame, candle cache, other)
   - Allows operator to identify which component to tackle in architectural phase

5. **GC Reclaim Ratio** (1 panel)
   - Line chart: X-axis = date, Y-axis = reclaim ratio %; trend line (target >60%)
   - Red zone if < 50%; operator can see if a particular date's cleanup is broken

6. **Alerts Pane** (1 panel)
   - Bulleted list of active SLO breaches (e.g., "Shard 2026-04-16 peak RSS 29.5 GB > 28 GB SLO"; "2026-04-15 reclaim
     ratio 0% < 50% threshold")

## QG / regression-test recommendation

**Prerequisite**: A canary VM in CI that runs a small (7 days, 1 asset_group, 1 data_type, 4 instruments) MDPS backfill
against a snapshot of prod GCS data.

**Test 1: Per-shard peak RSS assertion**

- Collect all `SHARD_COMPLETED` events from the canary run
- Assert: `max([e.rss_mb_peak for e in events]) < 10_000` (10 GB on canary hardware)
- Assert: `p95([e.rss_mb_peak for e in events]) < 8_000` (p95 < 8 GB)
- Regression: any code merge that increases max-peak-RSS by >1 GB fails the QG

**Test 2: Date-boundary reclaim ratio assertion**

- Collect all `DATE_BOUNDARY_GC` events
- Assert: `min([e.reclaim_ratio_pct for e in events]) > 40` (every date reclaims >40%)
- Assert: `mean([e.reclaim_ratio_pct for e in events]) > 60` (mean >60%)
- Regression: any code that reduces mean reclaim ratio by >5 percentage points fails

**Test 3: Static analysis — Polars/Pandas mixing**

- Grep MDPS source for `.to_pandas()` + `.from_pandas()` callsites that occur in the same file or adjacent modules
- Fail if: any module imports both polars AND pandas and calls both `.to_pandas()` and read-after-convert operations
  (per codex data-engine-selection rule)
- Reference: `codex/06-coding-standards/data-engine-selection.md`

## Recommended next step

**Immediate (1 hour, no architecture change needed)**:

- Add `SHARD_STARTED` and `SHARD_COMPLETED` events to `orchestration_base.py` before/after per-shard processing
- Add `DATE_BOUNDARY_GC` structured event (upgrade existing log to `log_event`)
- Add `rss_mb_peak` tracking: maintain a high-water mark per shard via `psutil.Process().memory_info().rss` in a
  per-shard variable
- **Why**: These three events alone would have predicted the Phase 3.2 OOM at T+5min: when shard 1 reports peak 4.2 GB
  and shard 2 reports 4.1 GB, operator extrapolates 4.15 GB avg × 100 shards = 415 GB ceiling, triggering preemptive
  alert

**Architectural (Phase 5, addresses root cause)**:

- Instrument `_cleanup_after_day` to emit which caches it cleared + how many bytes each freed: `CLEANUP_CACHE_CLEARED`
  with `(cache_name, bytes_freed_mb)`
- Instrument manifest read path to emit `MANIFEST_LOAD_BYTES`
- Implement per-shard memory component tracking (manifest bytes, instruments bytes, candle-cache bytes) in a telemetry
  accumulator, emitted at shard completion
- Build the 6-panel dashboard in deployment-ui to let operators watch per-shard trajectories in real-time
- Wire the canary regression test into QG post-gates
- Evaluate subprocess-per-shard vs single-process vs process-pool using per-shard memory + wall-clock data as the cost
  model

The structured events are the **enabling layer** for the architectural decision phase: without per-shard granularity in
events, the Phase 1.1 (subprocess-per-shard decision) cannot be made on data.
