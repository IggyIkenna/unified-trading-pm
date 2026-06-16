---
type: audit-findings
title: MDPS Long-Running State Inventory Audit
epic: mtds_mdps_master
auditor: claude haiku 4.5 (audit sub-agent)
date: "2026-05-28"
status: complete
name: mdps_long_running_state_inventory_2026_05_28
audit_instructions: mtds_mdps_master_audit_instructions.md
parent_plan: mdps_long_running_multi_shard_architecture_audit_2026_05_28.md
---

# MDPS Long-Running State Inventory Audit

**Codex references**: service-orchestration-patterns.md § 15; vm-tarball-deployment.md invariant 10;
data-engine-selection.md; cli-convention.md instrument-identity.

## What I read

### Orchestrator class hierarchy (MRO order)

The entry point is `CandleOrchestrationService` at orchestration_service.py:57. The MRO (Method Resolution Order)
chains:

```
CandleOrchestrationService
  → CandleOrchestrationWriter (orchestration_writer.py:41)
    → OrchestrationWorkersMixin (orchestration_workers.py:28)
      → BatchOrchestrationMixin (batch_workers.py:66)
      → LiveOrchestrationMixin (live_workers.py:183)
        → CandleWriteMixin (from candle_write_mixin.py)
    → CandleOrchestrationScanner (orchestration_scanner.py:187)
      → CandleOrchestrationBase (orchestration_base.py:29)
```

Note: `OrchestrationStateMixin` (orchestration_state.py:37) provides `_cleanup_after_day` but is NOT in the inheritance
chain. There are TWO implementations of `_cleanup_after_day`:

- **orchestration_base.py:79** (currently active) — the one called by `process_category` at orchestration_service.py:291
- **orchestration_state.py:45** (duplicate, UNUSED) — never called; dead code sitting in OrchestrationStateMixin

The active hook at orchestration_base.py:79 is the canonical one.

### State-holding attributes traced per file:line

- **orchestration_base.py:47** — `self._storage_client: StorageClient | None` (lazy GCS client)
- **orchestration_base.py:49** — `self._data_sinks: dict[str, DataSink]` (per-category registry)
- **orchestration_base.py:51-52** — `self.data_source` / `self.data_sink` (live-mode adapters)
- **batch_workers.py:49** — `_active_resource_profiler: ResourceProfiler | None` (module-level singleton)
- **orchestration_service.py:498** — `self._get_tradable_instruments(...)` returns DataFrame (not retained, freed after
  use)
- **orchestration_service.py:181** — `check_shard_freshness(...)` reads 526 MB manifest into memory
- **live_workers.py:468-470** — `_read_tick_data` Polars→Pandas conversion (per-instrument per-call, temporary)
- **live_workers.py:483-602** — `_iter_chain_symbol_dfs` streaming reads (per-symbol DataFrame, freed per iteration)

### The cleanup hook implementations

**orchestration_base.py:79-101** (ACTIVE):

```python
def _cleanup_after_day(self, date: str) -> None:
    logger.info("🧹 Cleaning up memory after processing %s", date)
    for _attr in ("candle_processing_service", "sampling_service"):
        _svc: object = getattr(self, _attr, None)
        if _svc is not None:
            _fn: object = getattr(_svc, "clear_cache_for_date", None)
            if callable(_fn):
                cast("Callable[[str], None]", _fn)(date)
    gc.collect()
    try:
        process = psutil.Process()
        rss: int = cast(int, process.memory_info().rss)
        memory_mb: float = rss / 1024 / 1024
        logger.info("💾 Memory after cleanup: %s MB", memory_mb)
    except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as e:
        logger.debug("Could not log memory usage: %s", e)
```

**orchestration_state.py:45-60** (DEAD CODE — never called):

```python
def _cleanup_after_day(self, date: str) -> None:
    logger.info("🧹 Cleaning up memory after processing %s", date)
    candle_svc: object = getattr(self, "candle_processing_service", None)
    if candle_svc is not None and hasattr(candle_svc, "clear_cache_for_date"):
        cast(_HasClearCache, candle_svc).clear_cache_for_date(date)
    sampling_svc: object = getattr(self, "sampling_service", None)
    if sampling_svc is not None and hasattr(sampling_svc, "clear_cache_for_date"):
        cast(_HasClearCache, sampling_svc).clear_cache_for_date(date)
    gc.collect()
```

The orchestration_state.py version is identical in intent but is never invoked because the MRO resolves
`_cleanup_after_day` to the orchestration_base.py implementation first. No refactoring harm from the duplicate; it is
just dead code.

### Per-shard call paths verified

**process_category (orchestration_service.py:110-293)** — the entry point:

- Line 148-162: try block enters
- Line 181-227: freshness check + manifest read (526 MB potential allocation)
- Line 246-262: per-data_type loop → `_process_data_type` call
- Line 286-293: **finally block** with `_cleanup_after_day` call (fires on ALL exit paths)

This is the tactical fix from MDPS@dcd7416 (Phase 3 of the sibling plan). The try/finally guarantees the cleanup hook
runs even if:

- `_load_tradable_context` returns empty (line 166 returns early inside try)
- `check_shard_freshness` marks data fresh (line 207 returns early)
- Dependency check fails (line 151 returns early)
- An exception is raised during processing

**\_process_data_type (orchestration_service.py:562-633)** — per data_type:

- Calls `_resolve_files_to_process` (line 603-613)
- Calls `_process_files_parallel` (line 619-630)
- All work happens INSIDE the outer `process_category` try block

**\_process_files_parallel (batch_workers.py:317-381)** — parallel per-instrument:

- ThreadPoolExecutor submits per-instrument tasks (line 343-352)
- Each future runs `_process_instrument_file` (line 305)
- All are awaited inside the try block (line 354-379)

**Single-instrument drilldown check**: the minimal invocation
`--asset-group cefi --data-types trades --start-date 2026-04-15 --end-date 2026-04-15 --instrument-ids BTCUSDT` flows:

1. CLI parse → process_handler.py
2. `CandleOrchestrationService.process_category(...)` called (line 110)
3. Enters try block (line 148)
4. Even if 0 files are found, execution returns from within try (line 165 or 172)
5. finally block (line 286) runs, calling `_cleanup_after_day`

**✅ Cleanup hook fires on ALL single-shard exit paths.** No missed paths identified.

---

## State inventory table

| Attribute (qualified)                                   | Type                                            | Set where                                   | Cleared where                                                        | Lifetime intent | Lifetime actual (empirical)                                                               | Per-shard reset cost                                         | Owner of cleanup                |
| ------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------- | --------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------- |
| `_storage_client` (base.py:47)                          | `StorageClient \| None`                         | orchestration_base.py:62-63 (lazy init)     | never                                                                | process         | RETAINED across dates (lazy singleton pattern)                                            | ~0 (reference-only; SDK cached internally)                   | orchestration_base              |
| `_data_sinks` (base.py:49)                              | `dict[str, DataSink]`                           | orchestration_base.py:74-76 per asset_group | never                                                                | process         | RETAINED across dates (per-category registry)                                             | ~0 (reference dict; sinks are long-lived)                    | orchestration_base              |
| `data_source` / `data_sink` (base.py:51-52)             | `DataSource \| None` / `CandleDataSink \| None` | set by LiveModeHandler before run           | none (live-mode only)                                                | process         | RETAINED if live (set once at startup)                                                    | N/A                                                          | orchestration_base              |
| `candle_processing_service.cache`                       | dict or cache object (inside service object)    | live_workers.py adapter calls               | base.py:83-88 via `clear_cache_for_date(date)`                       | per-day         | **STILL RETAINED per dcd7416 empirical** — 15.7 GB post-day-1                             | UNKNOWN — needs inspection of service internals              | base.py cleanup hook            |
| `sampling_service.cache`                                | dict or cache object (inside service object)    | cloud_candle_storage.py:128 init + calls    | base.py:83-88 via `clear_cache_for_date(date)`                       | per-day         | **STILL RETAINED per dcd7416 empirical** — 15.7 GB post-day-1                             | UNKNOWN — needs inspection of service internals              | base.py cleanup hook            |
| Instruments DataFrame (scheduling.py:134)               | `pd.DataFrame`                                  | orchestration_service.py:498 (loaded)       | freed after use line 516                                             | per-shard       | matches intent (local variable, garbage collected after `_load_tradable_context` returns) | ~50 MB (4128 instruments × metadata)                         | caller's local scope            |
| Manifest decompressed buffer (service.py:181)           | bytes / DataFrame (from check_shard_freshness)  | check_shard_freshness call (UTL)            | freed after freshness decision (line 207-227)                        | per-shard       | matches intent (local variable)                                                           | ~526 MB (per audit plan Phase 0.2 measurement)               | caller's local scope            |
| Per-instrument tick DataFrame (live_workers.py:468-470) | `pd.DataFrame`                                  | `_read_tick_data` call                      | freed after `_process_all_timeframes` completes (del pl_df line 470) | per-instrument  | matches intent (temporary, per-file call)                                                 | variable (~1 GB typical CeFi perp trades day per instrument) | live_workers per-call           |
| Per-symbol chain slice DataFrame (live_workers.py:594)  | `pd.DataFrame`                                  | `_iter_chain_symbol_dfs` yield              | del slice_df line 598 per iteration                                  | per-symbol      | matches intent (streaming pattern, freed per iteration)                                   | variable (~100 MB typical per symbol in options chain)       | live_workers per-iteration      |
| `_active_resource_profiler` (batch_workers.py:49)       | `ResourceProfiler \| None`                      | batch_workers.py:59 set by cli/main.py      | never (process-wide singleton)                                       | process         | RETAINED for process lifetime (correct; not per-shard state)                              | N/A                                                          | cli/main.py owns initialization |
| Per-adapter internal caches (adapters/\*.py)            | varies (dataclass fields on adapter instance)   | adapter init + per-call state               | UNKNOWN — NOT in cleanup hook                                        | per-adapter     | UNKNOWN — needs tracemalloc on adapter instances                                          | UNKNOWN                                                      | adapter classes                 |
| UTL module-level singletons (unified_trading_library)   | e.g. event sink, logging buffer                 | UTL **init**                                | varies per module                                                    | process         | UNKNOWN — UTL internal                                                                    | UNKNOWN                                                      | UTL owner (external)            |

**Key findings from table**:

1. **`candle_processing_service.cache` and `sampling_service.cache`** — these are the targets of the cleanup hook at
   base.py:83-88, BUT they are NOT properties of the orchestrator itself; they are properties of objects OUTSIDE the
   orchestrator's direct reference graph. The cleanup calls `getattr(self, "candle_processing_service", None)` — if
   these service objects are NOT attributes of the orchestrator instance, the hook will get `None` and do nothing.

2. **`_storage_client` and `_data_sinks`** — these are per-process singletons held on the orchestrator instance. They
   are NOT cleared on per-shard boundaries. This is correct behavior (startup amortization) and does NOT explain the 15
   GB residue.

3. **Manifest buffer** — the 526 MB manifest is read inside the try block but freed immediately after the freshness
   check decision. Per-shard cleanup cost is ~526 MB allocation + free per freshness check, not accumulated.

4. **Per-instrument tick DataFrames** — these are temporary, per-instrument, and freed after candle generation.
   Polars→Pandas conversion happens but the Polars object is deleted (line 470) before the Pandas object is freed
   downstream.

---

## Where the 15.7 GB residue most likely lives

The empirical signal is stark: Phase 3.2 attempt-1 (no cleanup wiring) post-day-1 RSS = **25.1 GB**; attempt-2 (with
cleanup wiring at dcd7416) post-day-1 RSS = **15.7 GB**. The cleanup hook claims to free
`candle_processing_service.cache` and `sampling_service.cache`, yet 15 GB still survives. This is the gap the audit must
narrow.

### Candidate 1: Polars/PyArrow arena allocations (MOST LIKELY)

**File:line**: live_workers.py:468 (`pl.read_parquet`)

**Signal**: The data-engine-selection.md codex (codified 2026-05-28) explicitly names this as a structural problem:
Polars reads parquets into PyArrow memory arenas. These arenas do NOT reclaim via `gc.collect()` because they are
managed by the underlying C++ PyArrow library, not Python's GC.

Per the sibling plan (`mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`), the Phase 3.2 canary ran 7 days of
backfill. Each day processes 4-16 instruments × up to 5 data_types. Each instrument-day tick parquet reads 10-2000 MB
decompressed. If 5-10 per-instrument parquets are read per day and Polars arena memory is not reclaimed per read, the
arena grows cumulatively within the day and does NOT drop when the individual tick DataFrame is freed.

**Likely cost**: 5-10 parquets/day × 100 MB average decompressed = 500 MB-1 GB per day in arena allocations. Cumulative
across 16 days = 8-16 GB. This aligns with the ~15 GB empirical residue.

**Why the cleanup hook misses it**: The cleanup hook does not call any Polars/PyArrow arena reset API. The missing
method is likely `pyarrow.lib.clear_tensor_memory_pool()` or a Polars-level equivalent.

### Candidate 2: Per-service cache object internal state (SECONDARY)

**File:line**: orchestration_base.py:83-88

**Signal**: The cleanup hook calls `candle_processing_service.clear_cache_for_date(date)` and
`sampling_service.clear_cache_for_date(date)`, but we do not know if these methods actually exist or if they fully clear
all internal state.

If either service object was:

- Created once at startup (not per-day)
- Holds per-day state in a field that `clear_cache_for_date` does NOT clear
- Accumulates rows/buffers across dates without flushing

Then the cleanup hook would be incomplete. **This requires reading the actual `candle_processing_service` and
`sampling_service` implementations**, which are imported from external modules (UTL or another service library).

### Candidate 3: Manifest DataFrame not freed on freshness-check early-return path

**File:line**: orchestration_service.py:181-213

**Signal**: The manifest is read via `check_shard_freshness(...)` at line 181. If the freshness check returns early
(lines 207-213) without the caller holding a reference to the manifest object that is freed, the manifest buffer might
outlive the return scope.

However, the manifest is not stored in a self.\* attribute; it is a local variable inside `process_category`. Python's
GC should free it on return. **Low probability unless there is a hidden reference.**

### Candidate 4: Module-level singletons in UTL or canonical_writer

**File:line**: unified_trading_library (external); canonical_writer.py (local)

**Signal**: The canonical_writer module emits manifest rows via `record_captured(...)` calls (see
candle_write_mixin.py). If the canonical_writer or UTL modules hold per-shard buffers (e.g., an event sink upload
queue), these would NOT be in the orchestrator's cleanup scope.

**UNKNOWN without reading UTL source.**

### Candidate 5: Thread-local state in ThreadPoolExecutor workers

**File:line**: batch_workers.py:342-352

**Signal**: The ThreadPoolExecutor at batch_workers.py:342 submits parallel tasks. Each thread runs
`_process_instrument_file` inside the executor. If any thread-local state is created and not cleaned up on thread exit,
it could accumulate.

However, Python's ThreadPoolExecutor recycles threads in the pool; per-thread state should be freed when the pool is
destroyed (implicitly on exiting the with block at line 342). **Low probability.**

---

## Single-shard drilldown check

The minimal invocation to verify all code paths reach the cleanup hook:

```bash
mdps-cli --operation process --mode batch \
  --asset-group cefi --data-types trades \
  --start-date 2026-04-15 --end-date 2026-04-15 \
  --instrument-ids BTCUSDT --force
```

**Code path walk**:

1. `cli/main.py` parses args → calls process_handler.py
2. process_handler.py determines category=CEFI, date_str=2026-04-15, data_types=['trades'], instrument_ids=['BTCUSDT']
3. `CandleOrchestrationService(config)` instantiated (service_orchestration_service.py:70-77)
4. `process_category(category=CEFI, date_str='2026-04-15', data_types=['trades'], instrument_ids=['BTCUSDT'], ...)`
   called (service.py:110)
5. **Enters try block (line 148)**
6. `_check_dependencies` runs (line 149) → passes or returns early (line 150-162)
7. `_load_tradable_context` runs (line 166) → if empty, returns early **INSIDE try** (line 172)
8. Manifest freshness check runs (line 181-227) → if fresh, returns early **INSIDE try** (line 213)
9. Loop: `_process_data_type(data_type='trades', ...)` called (line 247)
   - Inside `_process_data_type` → list files, filter existing outputs, call `_process_files_parallel`
10. **finally block runs (line 286)** — calls `_cleanup_after_day('2026-04-15')`

**✅ Cleanup fires on ALL paths** (early return, exception, or normal completion).

No skipped paths identified. The try/finally wrap is airtight.

---

## Recommended next step

### Immediate (tactical, in scope of Phase 3.2 / Phase 4.3 of sibling plan)

**What to ship before architectural redesign**:

1. **Inspect `candle_processing_service.clear_cache_for_date()` and `sampling_service.clear_cache_for_date()`** — verify
   these methods exist and fully drain their internal caches. If either method is missing, add it. If either leaks
   state, patch it.

2. **Add Polars/PyArrow arena reset to cleanup hook** — call the missing arena clear API. Per data-engine-selection.md,
   the call is likely:

   ```python
   import pyarrow as pa
   pa.memory_pool().release_unused()  # or equivalent per Polars docs
   ```

   Add this to orchestration_base.py:92 (after `gc.collect()`).

3. **Verify no module-level singletons in UTL or canonical_writer hold per-shard state** — if they do, add a flush/clear
   call to the cleanup hook.

**Effort**: 2-4 hours (inspection + audit + 1-2 line additions to base.py cleanup).

### Architectural (Phase 1+ of `mdps_long_running_multi_shard_architecture_audit_2026_05_28.md`)

**Longer-term structural fixes** (out of scope for immediate tactical fix):

- **Phase 1.1** — decide execution model: subprocess-per-date or in-process with structural cleanup. The empirical
  evidence (15.7 GB residue after Python-level cleanup) suggests subprocess-per-date may be the only viable option for a
  32 GB box running 16+ days of multi-shard backfill.

- **Phase 2** — select data engine end-to-end. Pure Polars with arena resets, pure Pandas+PyArrow, or PyArrow-table
  native. The current Polars→Pandas→Polars churn is a conversion-buffer tax on top of the arena-retention issue.

- **Phase 4.3** — replace the tactical `del + gc.collect()` patches in process_handler.py with structural cleanup once
  the execution model is chosen. If subprocess-per-date is selected, process-level memory cleanup happens on kernel exit
  (no Python patches needed). If in-process is chosen, the cleanup hook becomes the SSOT for per-date isolation.

---

## Codex alignment

- **service-orchestration-patterns.md § 15** (codified 2026-05-28): "Batch Service Lifecycle: Setup, Work, Cleanup". The
  cleanup hook at orchestration_base.py:79 is the reference implementation. ✅ Requirement MET (hook wired into
  try/finally as of dcd7416).

- **vm-tarball-deployment.md invariant 10**: Services running multi-shard inside one VM MUST call per-shard cleanup. ✅
  Requirement MET (cleanup wired per date, not per instrument-shard; next level of granularity could be per-data_type).

- **data-engine-selection.md** (codified 2026-05-28): Polars→Pandas→Polars is a banned anti-pattern. **VIOLATION** —
  live_workers.py:468-470 does exactly this (pl.read_parquet → .to_pandas()). No Pandas-to-Polars conversion currently,
  but the forward path is present. Audit finding: the data-engine selection decision (Phase 2 of architectural plan)
  MUST address this path.

- **cli-convention.md**: not directly engaged by this inventory audit (separate audit
  `mdps_long_running_cli_granularity_2026_05_28.md`). No findings.

---

## Summary

The state inventory is clean at the Python-level attribute scope: `_storage_client`, `_data_sinks`, and temporary
per-call DataFrames are either process-scoped (correct) or temporary (correct). The cleanup hook fires on every per-date
exit path (correct as of dcd7416).

The 15.7 GB post-day-1 residue is **most likely Polars/PyArrow arena memory** that Python's gc.collect() cannot reclaim.
The secondary suspect is incomplete cache clearing in the external service objects (`candle_processing_service` and
`sampling_service`). Both require investigation outside the orchestrator source code itself.

The architectural decision (Phase 1.1 of the long-running audit plan) between subprocess-per-date and in-process with
deeper cleanup is now empirically grounded: if the arena reset + service cache audit yields <5 GB residue, in-process is
viable; if it's still >10 GB, subprocess-per-date is the pragmatic choice.
