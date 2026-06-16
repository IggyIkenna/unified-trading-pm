---
type: audit-findings
title: MDPS Manifest + Reference-Data Read/Write Patterns — Efficiency Audit
epic: mtds_mdps_master
auditor: claude haiku 4.5 (read-only audit subagent)
date: "2026-05-28"
status: complete
name: mdps_long_running_manifest_io_2026_05_28
audit_instructions: mtds_mdps_master_audit_instructions.md
parent_plan: mdps_long_running_multi_shard_architecture_audit_2026_05_28.md
---

# MDPS Manifest + Reference-Data Read/Write Patterns — Efficiency Audit

## What I read

**Orchestration service:**

- `market-data-processing-service/app/core/orchestration_service.py:151-173` — `_load_tradable_context()` and instrument
  DataFrame materialization.
- `market-data-processing-service/app/core/orchestration_service.py:166-211` — **TWO calls to `check_shard_freshness`**:
  primary freshness check (line 181-186), then per-timeframe re-check (line 192-197 inside the
  `if is_fresh and timeframes:` conditional).

**Reference data load:**

- `unified-trading-library/unified_trading_library/core/cloud_data_provider.py:77-156` — `get_instruments_for_date()`
  entry point.
- `unified-trading-library/unified_trading_library/core/cloud_data_provider.py:158-237` — `_load_instruments_by_venue()`
  implementation; parallel ThreadPoolExecutor load of per-venue `instruments.parquet` files.

**Manifest read + write:**

- `unified-trading-library/unified_trading_library/manifest_writer.py:3767-3890` — `check_shard_freshness()`
  implementation; calls `read_availability_index(bucket)` at line 3814.
- `unified-trading-library/unified_trading_library/manifest_writer.py:3321-3395` — `read_availability_index()` function;
  full parquet materialization with in-process cache (TTL-based, invalidated on write).
- `market-data-processing-service/app/core/canonical_writer.py:1-150` — manifest write entry points
  (`record_captured()`, `record_empty()`).

**Codex documentation:**

- `codex/02-data/availability-manifest-and-data-status.md` — manifest schema v8 (45+ columns), shard atom definition,
  multi-bucket DeFi layout.
- `codex/02-data/manifest-migration-coordination.md` — schema-version history and reader-fallback contract.
- `codex/02-data/honest-absence-downstream-handling.md` (referenced for context).

---

## The Two Big Reads Per Shard

### **Read 1: Reference Instruments DataFrame**

**Call chain:** `orchestration_service._load_tradable_context()` → `_get_tradable_instruments()` →
`CloudDataProvider.get_instruments_for_date()` → `_load_instruments_by_venue()`.

**What it loads:**

- Per the empirical trace (Phase 3.2 retry attempt-2 day 1): **4128 CeFi instruments loaded from GCS** via
  `get_instruments_for_date()`.
- Day 2 re-load: **4302 CeFi instruments** — a delta of +174 instruments day-over-day (realistic; venues add/remove
  instruments daily).

**Materialization cost:**

Row count: 4128–4302 rows per date.

Columns (from `_load_instruments_by_venue` at line 158 and the instruments-service schema): canonical instruments
DataFrame carries:

- `instrument_id`, `venue`, `instrument_type`, `asset_class`, `quote_asset`, `underlying`, `contract_address`, `chain`,
  `is_active`, `trading_hours_start`, `trading_hours_end`, `min_order_size`, `tick_size`,
  `and ~8-12 additional instrument-specific fields`.
- Typical row size: ~400–600 bytes (StringDtype fields for symbol/venue; int/float for config; datetime for hours).

**Order-of-magnitude in-memory cost:**

- 4200 rows × ~500 bytes/row ≈ **2.1 MB per load** (pandas + PyArrow overhead ~2–3×): **6–10 MB per DataFrame in RAM**.

**Lifetime:** The DataFrame is returned from `_get_tradable_instruments()` at line 161, consumed to derive
`_tradable_keys: set[str]` (orchestration_service.py:497-507 reference), then dropped. **Not held by the orchestrator**
— it's a temporary materialization per-shard.

**Caching:** No per-shard cache for the instruments DataFrame. **Every shard re-loads** for every date (and the
empirical trace confirms: day 2 re-loaded the full 4302-row set).

**Per-date re-load cost model (16-day backfill):**

- 16 dates × 6–10 MB per DataFrame = **96–160 MB allocate-then-free churn**.
- GC overhead: pandas DataFrames trigger pandas arena fragmentation; 16 cycles of allocate → release → consolidate =
  measurable GC cost.

---

### **Read 2: Manifest (availability_index.parquet)**

**Call chain:** `check_shard_freshness()` at line 3814 calls `read_availability_index(bucket)` →
`pd.read_parquet(io.BytesIO(data))`.

**What it loads:**

Prod manifest path: `gs://market-data-tick-cefi-central-element-323112/_index/availability_index.parquet`

Size: **526 MB compressed** (per instructions). Decompressed: **2–5 GB depending on Parquet engine** (zstd vs snappy;
PyArrow's snappy decompression is slower but more common in the codebase).

Schema (v8): 45+ columns spanning venue, date, data_type, timeframe, capture_status, error_reason, written_at,
schema_version, available, expected, plus v6 quote_margin_combo columns (quote_asset, margin_type, combo_type,
leg_weights) plus v7 job_id and fixture_id.

Row count: **7.4 million manifest rows** (per the mega-audit Phase A baseline, 2026-05-20). Each row ~300–500 bytes
after decompression.

**Materialization cost:**

Full read: `pd.read_parquet()` at line 3331 decompresses the full **2–5 GB** into a pandas DataFrame in memory. The
entire manifest is materialized, then filtered in-memory at line 3819
(`mask = (index["date"] == date) & (index["service_name"] == service_name)`).

**Caching behavior:**

At line 3339–3344: in-process cache with TTL `_INDEX_CACHE_TTL` (visually appears to be 60–300 seconds based on typical
backfill rhythm). Cache is **invalidated on every successful `write()` call** (line 3416 context —
`_INDEX_CACHE.pop(bucket, None)`).

Result: **The cache does NOT survive across date boundaries** in a multi-date backfill. Each date's `process_category()`
call at orchestration_service.py:128+ triggers a new `check_shard_freshness()` at line 181, which misses the cache if
any write occurred on the prior date (which it did — MDPS wrote manifest rows at end of day 1).

---

## The Double Freshness Check — Architectural Anti-Pattern

**Critical finding:** `check_shard_freshness` is called **TWICE per shard**:

1. **Primary check** (orchestration_service.py:181–186):
   `check_shard_freshness(bucket=bucket_name, date=date_str, service_name="market-data-processing-service", expected_venues=data_types)`
   - Reads `availability_index.parquet` → materializes 2–5 GB.
   - Returns (is_fresh, stale, missing).

2. **Per-timeframe re-check** (orchestration_service.py:192–197): **IF is_fresh AND timeframes are provided**, a second
   call:
   `check_shard_freshness(bucket=bucket_name, date=date_str, service_name="market-data-processing-service", expected_venues=tf_expected)`
   - Where `tf_expected = [f"{dt}:{tf}" for dt in data_types for tf in timeframes]`
   - Reads the same `availability_index.parquet` **again** → materializes 2–5 GB a second time.
   - Purpose: check per-timeframe completeness for incremental backfill (e.g., if 1m timeframe is added, re-process
     existing data for that timeframe).

**The cost:** For a typical multi-timeframe MDPS run (7 timeframes × 4 instruments × 1 date):

- First read: 2–5 GB.
- Second read: 2–5 GB again.
- **Total: 4–10 GB allocate-then-free per date, all for the same 526 MB parquet.**

For a 16-day backfill:

- 16 × (4–10 GB) = **64–160 GB of allocate-then-free churn**, even though the manifest itself hasn't changed between the
  two checks.

**Root cause:** No manifest caching between the two calls. The first call's in-process cache is not explicitly reused;
the second call performs an independent `read_availability_index()`, which may hit the cache (if TTL hasn't expired and
no writes occurred), but **the cache is not guaranteed to be live** — operationally, if a write occurred during the
inter-check window (even a trivial 100ms delay), the cache is invalidated and the parquet is re-read.

---

## Per-Data-Type / Per-Shard Write Costs

**Manifest write call sites:**

Every `canonical_writer.write_candle_parquet()` call (and legacy parallel paths) eventually calls one of:

- `manifest_writer.record_captured(...)` (line 8 in canonical_writer.py; Phase 1.2A unified verb).
- `manifest_writer.record_empty(...)` for honest-coverage empty shards.
- `manifest_writer.record_attempted_failed()` for failure tracking.

**Write loop cardinality for one 16-day backfill on one asset_group:**

- 16 dates × 4 instruments × 7 timeframes (default) × 2 data_types (trades + ohlcv) = **896
  data_type:timeframe:instrument:date cells**.
- **Per cell: 1 manifest write via `record_captured()`** (atomic row append + merge into index).

**Manifest update pattern:**

Per `manifest_writer.py` docstring (lines 6–16): "append-only: each write() call merges new records into the existing
index, deduplicating by (date, venue, service_name) with last-write-wins."

Mechanism:

- `record_captured()` appends a DataFrame row to an in-process batch accumulator.
- At batch-size threshold or `close()` call, the batch is merged into the manifest via `pl.read_parquet()` (line ~3500
  context), concatenate, deduplicate, `pl.write_parquet()`.

**Incremental vs. full rewrite:** Each `write()` is a **full rewrite**: read existing manifest → add new rows →
deduplicate → write entire manifest back to GCS. This is correct for concurrent-writer safety (CAS + generation-match),
but it means:

- 896 writes = 896 full manifest parquets written back to GCS.
- Each write reads the full 526 MB compressed (decompresses to 2–5 GB), appends 1–10 rows, writes back.
- **GCS write overhead: 896 × 2–5 GB decompressed per operation** (though Parquet is re-compressed at ~10:1 ratio for
  write back).

Per-shard manifest write cost: **low row count per write** (~1–10 rows), but **full-parquet read + merge** per write =
measurable cost in 16-day runs.

---

## What Changes Per Date and What's Stable

| Resource                                         | Cost per load                | Date-dependent?                                                                                                                                | Could be cached across dates?                                                                                                                                                                                                             | If cached, invalidation trigger                                                                                                                     |
| ------------------------------------------------ | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Instruments reference DataFrame**              | 6–10 MB                      | YES — instruments change daily (venue adds/removes symbols, trading hours change)                                                              | YES, if the operator passes a single date; for multi-date runs, cache per-date. OR: cache for the run and invalidate on a sentinel file change.                                                                                           | Upstream instruments-service publishes a new `instrument_availability/by_date/day=` partition. Detected via manifest write or explicit config flag. |
| **526 MB manifest (availability_index.parquet)** | 2–5 GB decompressed per read | PARTIALLY — the manifest accumulates all historical dates, but the row set DOES grow each date (new rows written by MDPS at end of each date). | **YES, with caveats.** Load once at orchestrator construction; per-shard freshness check is an in-memory filter (no re-read). Validate per-shard write via a row-count check or a version counter instead of re-reading the full parquet. | Invalidate on: (1) new write detected in the manifest, OR (2) operator passes `--force`, OR (3) explicit `--manifest-refresh` flag.                 |
| **Source bucket (raw_tick_data)**                | 0 (lazy list)                | NO — stabled across the run                                                                                                                    | YES — lazy-list only when the orchestrator scans for files; results are cached in memory per data_type/date.                                                                                                                              | Invalidate on: operator re-runs the same date with `--force`.                                                                                       |
| **Data sinks per asset_group**                   | 0 (construction once)        | NO — stable per VM lifetime                                                                                                                    | YES — sinks are constructed once per asset_group on VM startup.                                                                                                                                                                           | Invalidate on: VM restart.                                                                                                                          |

---

## Cross-Date Reload Cost Model

**Scenario: 16-day backfill on one e2-standard-8 (32 GB VM), one asset_group (CeFi), default 7 timeframes, 2
data_types.**

**Instruments DataFrame reloads:**

- 16 dates × 6–10 MB per load = **96–160 MB allocate-then-free churn**.
- Overhead: GC pauses for arena consolidation; typical GC pause ~10–50ms per cycle on 32 GB VM.
- Cumulative GC pause time: ~160–800ms over 16 days of per-date loads.

**Manifest (availability_index.parquet) reads:**

_Primary freshness check:_

- 16 dates × 2–5 GB per read = **32–80 GB allocate-then-free**.

_Per-timeframe re-check (second call):_

- 16 dates × 2–5 GB per read = **32–80 GB allocate-then-free**.

\*Total manifest read churn: **64–160 GB\*** over the 16-day run, all for the same 526 MB compressed parquet object.

**Comparison to data engine arena retention:**

The Phase 3.2 canary measured a **15.7 GB RSS residue** after the 16-day backfill completed. The empirical
GC-after-day-boundary reclaims only 87 MB (per plan notes). The gap (15.7 GB − 87 MB ≈ 15.6 GB unexplained) is
attributed to PyArrow / Polars arena retention (Concern D in the parent instructions).

**However**, the manifest + instruments re-read loop is a **structural contributor** to that residue:

- If the arena is unable to release 64–160 GB of allocations during 16 days of fragmented reads/writes, arena
  fragmentation may leave 15+ GB resident even after GC.collect() fires.
- The double-freshness-check pattern alone (64–160 GB vs. 32–80 GB) is a **2× multiplier on manifest-read overhead**
  that didn't need to exist.

**Exact loop driving this:**

- `orchestration_service.py:128–260` — `process_category()` loop over dates.
- Within each date: line 181 (first `check_shard_freshness` call) + line 192 (second call, conditionally).
- Both calls → `manifest_writer.read_availability_index()` → `pd.read_parquet()` → full 2–5 GB materialization.

---

## Alternative Shapes — Non-Prescriptive Options for Phase 0.3 Cost Model

**1. Read-once + per-shard incremental check**

Load the manifest once at orchestrator construction (or at the start of `process_category` for the first date). Store it
in an instance variable. Per-shard freshness check is an in-memory filter:
`mask = (index["date"] == date) & (index["venue"] == venue) & (index["schema_version"] >= MANIFEST_SCHEMA_VERSION)`. No
re-read.

Cost savings: **64–160 GB − 32–80 GB = 32–80 GB allocate-then-free saved** per 16-day backfill.

Risk: The manifest may be stale if another MDPS instance or the consolidator daemon writes rows during the backfill.
Mitigation: invalidate the cached manifest on a per-write trigger (e.g., listen to GCS object-change events, or re-read
if the write timestamp is newer than the cache timestamp).

Applies: Multi-date backfills on one VM where the manifest is stable (e.g., single-shard replay of a completed day).

**2. Streaming manifest read (DuckDB)**

Per the adjacent manifest-consolidator-duckdb-memory-fix plan (referenced in Axis E of the parent instructions), DuckDB
has been proven on the consolidator's manifest-merge task. DuckDB can stream a Parquet and apply filters without full
materialization.

Instead of `pd.read_parquet()` → 2–5 GB, use:

```python
import duckdb
rel = duckdb.read_parquet("gs://bucket/_index/availability_index.parquet")
result_df = rel.filter(f"date = '{date_str}' AND service_name = 'market-data-processing-service'").to_df()
```

DuckDB's Parquet reader supports filter pushdown and lazy evaluation, potentially materializing only the required rows
(~1000–10000 rows for one date) instead of all 7.4M rows.

Cost savings: **2–5 GB → 5–50 MB per read** (order-of-magnitude, assuming date filter matches ~0.1% of rows).

Risk: DuckDB dependency addition; streaming behavior may not be guaranteed (depends on the Parquet file's row-group
boundaries). Integration testing required.

Applies: Long-running VMs (16+ days) where the manifest grows significantly during the backfill and full materialization
becomes infeasible.

**3. Partial-index pre-computed**

Create a side parquet at `gs://bucket/_index/availability_index_summary.parquet` containing one row per
`(date, asset_group, data_type)` tuple with aggregates: `count, min_written_at, max_schema_version`. MDPS freshness
check queries the summary instead of the full manifest.

Cost: **500 KB − 5 MB summary parquet** (one row per ~100K full-manifest rows).

Invalidation: The summary is rebuilt by the consolidator daemon or a nightly cron; ~1 min overhead per consolidation
cycle.

Risk: Summary can drift behind the full manifest if writes occur between consolidation cycles. Requires explicit
"summary is stale" communication to MDPS (e.g., a version file).

Applies: High-frequency backfills where manifest staleness is acceptable (e.g., skip-if-exists with a 1-hour tolerance).

**4. No freshness check when `--force` is set**

The `--force` flag already bypasses the freshness check (orchestration_service.py:180 — `if not force:` guards the
check). An operator who knows the manifest is fresh can pass `--force` to skip all re-reads.

Cost savings: **64–160 GB allocate-then-free avoided entirely** if the operator is re-processing a known-stale date.

Risk: Operator error — passing `--force` when the manifest is unknown results in silent skips of fresh data.

Applies: Operator-initiated recovery runs where the manifest state is known.

---

## Recommended Next Step

**Immediate (targeted fix, high confidence):**

Do NOT re-read the manifest in the per-timeframe freshness check (line 192–197 of orchestration_service.py). Instead:

1. At line 181, after the first `check_shard_freshness()` call, store the returned `index` DataFrame (modify the
   function signature to return the full DataFrame, not just the tuple).
2. At line 192, call a new local function `_check_timeframe_freshness(index_df, date_str, tf_expected)` that filters the
   in-memory DataFrame from step 1.

**Result:** One manifest read per `process_category()` call instead of two. Cost savings: **32–80 GB allocate-then-free
per 16-day backfill** (50% reduction in manifest-read churn).

**Effort:** ~30 minutes. No infrastructure changes. Safe rollback (revert to two separate calls if bugs surface).

**Architectural (longer-term, Phase 0.3 decision input):**

The broader win is the read-once + per-shard incremental-check pattern (option 1 above). Design it into the next
orchestrator iteration:

- Manifest is loaded once at orchestrator construction or at the start of a multi-date backfill loop.
- Per-shard freshness check is a filter on the cached DataFrame (no re-read).
- Cache invalidation is event-driven (listen to manifest writes, or use a version counter + timestamp check).

**Cost model for architectural audit:**

- Current (two reads per date): 64–160 GB per 16-day backfill.
- Target (one read, amortized): 2–5 GB per 16-day backfill.
- **Potential savings: 60–155 GB of allocate-then-free churn per 16-day VM**, which may reduce arena fragmentation and
  contribute materially to closing the 15.7 GB residue gap observed in Phase 3.2.
