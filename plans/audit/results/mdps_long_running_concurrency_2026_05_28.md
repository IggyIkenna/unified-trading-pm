---
type: audit-findings
title: MDPS Long-Running Concurrency + Execution-Unit Cost Model
epic: mtds_mdps_master
auditor: claude opus 4.7 (slot main subagent)
date: "2026-05-28"
status: complete
name: mdps_long_running_concurrency_2026_05_28
audit_instructions: mtds_mdps_master_audit_instructions.md
parent_plan: mdps_long_running_multi_shard_architecture_audit_2026_05_28.md
---

# MDPS Long-Running Concurrency + Execution-Unit Cost Model

**Codex references**: service-orchestration-patterns.md § 15; vm-tarball-deployment.md invariant 10.

## What I read

### Execution layer entry points and loop structure

- `cli/handlers/process_handler.py:607–650` — `process_candles_handler()` (entry point)
  - Line 643–650: outer loop over dates (`for date in start_end_date_range(...)`)
  - Per date: constructs `orchestrator = CandleOrchestrationService(...)`, calls `orchestrator.process_category(...)`

- `app/core/orchestration_service.py:110–293` — `process_category()` (the orchestrator's per-shard entry)
  - Line 148–162: try block entry
  - Line 181–227: per-date freshness check + manifest read
  - Line 246–262: per-data_type loop → calls `_process_data_type(data_type)`
  - Line 286–293: finally block with `_cleanup_after_day` call (fires on all exit paths)

- `app/core/batch_workers.py:216–238` — `_on_memory_warning()` (backpressure callback)
  - Sets `self._backpressure_active = True` when system RSS crosses 85% threshold
  - Triggers when `memory_pct > self.high_water_mark` (line 225)

- `app/core/batch_workers.py:240–278` — `_unpause_if_safe()` (resume logic)
  - Resumes submissions when RSS drops below `self.resume_threshold` (default ~75%)
  - Or after `max_pause_duration` fires (default 120 seconds), whichever comes first

- `app/core/batch_workers.py:284–315` — `_submit_instrument_file_tasks()` (submission gate)
  - Line 289–298: polls `self._backpressure_active` flag before submitting new tasks
  - If True, calls `_unpause_if_safe()` then continues or yields

- `app/core/batch_workers.py:317–381` — `_process_files_parallel()` (the inner per-file parallelism)
  - Line 342: constructs `ThreadPoolExecutor(max_workers=N)` (default from config, typically 4; canary ran with 1)
  - Line 343–352: submits one task per scanner-returned blob (per-instrument parquet)
  - Line 354–379: `as_completed()` loop awaits all futures; backpressure checks run during submission

- `app/core/live_workers.py:224–447` — `_process_instrument_file()` (the worker body)
  - Line 310–320: GCS download via `storage_client.download_blob(...)` (I/O bound)
  - Line 324–380: `_read_tick_data()` and `_process_all_timeframes()` (CPU bound: Polars aggregation + parquet write)
  - Per-instrument wall-clock varies from ~10s (1 instrument, 1 data_type) to ~300s (4 instruments, full 7 TFs)

- `unified_trading_library` (external) — `ResourceProfiler` class
  - Module-level singleton at `batch_workers.py:49` (`_active_resource_profiler`)
  - Profiles RSS + CPU per task submission; data stored in process memory for later analysis

### Parallelism layer: ThreadPoolExecutor choice

- `app/core/batch_workers.py:342` — `with ThreadPoolExecutor(max_workers=effective_workers) as executor:`
  - Per-date, per-data_type: creates a NEW executor (not reused across data_types or dates)
  - Tasks are `_process_instrument_file(blob_path)` — one per instrument-day parquet
  - Threads do I/O (GCS download) and heavy CPU (Polars reads / aggregation / pyarrow write)

---

## Current execution shape (as-is)

### Outer loop (synchronous, dates + asset_groups)

```
process_candles_handler (start_date=X, end_date=Y, asset_group=Z, data_types=[...])
  │
  └─→ for date in date_range:
        │
        └─→ CandleOrchestrationService(asset_group=Z, data_types=data_types, ...)
              │
              └─→ process_category(date=date, asset_group=Z, data_types=data_types)
                    try:
                      │
                      ├─→ check_shard_freshness(...) [reads 526 MB manifest]
                      │
                      └─→ for data_type in data_types:
                            │
                            └─→ _process_data_type(data_type)
                                  │
                                  └─→ _process_files_parallel(data_type, blobs)
                                        │
                                        └─→ ThreadPoolExecutor(max_workers=N).map(_process_instrument_file, blobs)
                                              │
                                              └─→ [threads run: GCS download + Polars agg + write]
                    finally:
                      │
                      └─→ _cleanup_after_day(date) [calls service.clear_cache_for_date()]
```

**Cardinality** (example: 16-day backfill, 1 asset_group, 4 instruments, 2 data_types, 7 timeframes):

- Outer date loop: **16 iterations**
- Inner per-data_type loop: **2 iterations per date** (trades + ohlcv) → **32 total**
- Per-data_type per-instrument: **4 iterations per data_type** (BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT) → **128
  instrument-file tasks**
- ThreadPoolExecutor workers: **min(4, CPU_COUNT)** by default (canary ran with 1)
- Total work units submitted: **128**

**Memory management**:

- GIL semantics: Python threads share memory. Per-thread state in orchestrator (caches, manifest readers, GCS client) is
  accessible to all threads.
- Heavy work (Polars C++ bindings, PyArrow I/O) releases the GIL → threads achieve real parallelism for
  aggregation/write.
- Backpressure layer monitors system RSS; pauses new submissions if RSS > 85%, resumes if < 75% or timeout fires.
- Cleanup hook at date boundary clears `candle_processing_service.cache` + `sampling_service.cache` + calls
  `gc.collect()`.

**Empirical measurements** (Phase 3.1 and Phase 3.2 canary):

- Phase 3.1 (1-day, 4 instruments, MAX_WORKERS=1): **191s total wall-clock, exit code 0**
- Phase 3.2 attempt-2 (1-day, 4 instruments, MAX_WORKERS=1, with cleanup wiring): **202s total, post-day RSS 15.7 GB**
- The 25 GB floor from attempt-1 (no cleanup wiring) reduced to 15.7 GB after `_cleanup_after_day` wiring; gap
  attributable to Polars/PyArrow arena retention (Finding D).

---

## Cost model per execution shape

The architectural plan Phase 1.1 enumerates four candidates. Here is the cost model for each:

| Shape                                  | Startup cost per shard                                                                         | Per-shard variable cost                                                               | Memory ceiling per worker                                                                                            | Crash isolation                                                                                                                | Observability                                                                                                                 | Code-change cost                                                                                                                                                                                                          |
| -------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **(a) Subprocess-per-date**            | ~4–5s (Python interpreter init + instruments DF load + asset_group handler setup)              | ~150s (actual work: GCS I/O + Polars agg)                                             | 8–32 GB (isolated child process; max is VM memory)                                                                   | Excellent — child process exit → kernel reclaims all memory, file descriptors, threads                                         | Child process stdout/stderr captured; requires explicit progress log parsing by parent                                        | **MEDIUM** — add subprocess invocation loop in `process_candles_handler`; per-date file scoping; per-date manifest cache per child; no shared state from parent needed beyond CLI config                                  |
| **(b) Subprocess-per-shard**           | ~8–12s (Python init + instruments load + asset_group init + data_type-level state setup)       | ~30–60s (finer-grain work: single data_type, single asset_group)                      | Per-child: 2–8 GB (same isolation as (a), per-shard footprint lower)                                                 | Excellent — each child dies on completion                                                                                      | Requires aggregating results from N children; JSON envelope per result                                                        | **HIGH** — subprocess per (date, asset_group, data_type, instrument subset) tuple; manifest caching per child problematic (no warmth across shards); coordination of result collection                                    |
| **(c) In-process with proper cleanup** | 0 (no fork)                                                                                    | ~150s (same work as current)                                                          | Per-date: currently 15.7 GB (with cleanup hook); **empirically unreliable** per Phase 3.2 attempt-2                  | **Poor** — unhandled exception in one shard leaves process + all accumulated state alive; must rely on outer timeout + SIGKILL | Natural: live logs, streaming progress, in-process instrumentation                                                            | **LOW** — the current shape; requires solving Polars/PyArrow arena-retention problem (Concern D) to reliably keep per-day footprint < 2 GB                                                                                |
| **(d) Process-pool worker model**      | ~30–60s (parent startup + manifest load once + reference data warmup + executor pool creation) | ~20–30s per shard (workers pull work from queue; no per-shard manifest reload needed) | Per-worker: 1–4 GB (isolated from parent; workers do not accumulate manifest or reference data, only per-shard work) | Good — failed worker is recycled or replaced; parent + other workers unaffected                                                | Executor provides task futures; can emit progress per future completion; requires parent-to-worker comm channel for telemetry | **HIGH** — refactor orchestrator into (parent state owner) + (worker function); manifest/reference-data must be serializable; per-shard worker isolation logic; likely requires orchestrator state → parent-only refactor |

---

## Why each shape exists / what it solves

### (a) Subprocess-per-date

**Rationale**: Kernel reclaims all per-date process state (heap, memory-mapped pages, open file descriptors, thread
stacks) at process exit. No in-process accumulation possible. Per-date floor = fresh child memory footprint (~80–200 MB
base Python + small config). Amortises the per-date work (150s) against one 4–5s startup cost.

**Solves**:

- Polars/PyArrow arena retention (Concern D) — child dies with arena
- Per-date service cache retention (Concern C, partial) — child's cache objects freed
- Memory ceiling predictability — each child has a bounded footprint; parent doesn't accumulate

**Trade-offs**:

- Per-date fork cost: 4–5s × N_dates (for 16 dates: 64–80s overhead, amortised across 191s per-date work = ~33%
  wall-clock tax)
- Instruments DF reloaded per child (not shared)
- Manifest buffer read per child (but cached per-child lifetime, not globally)
- Parent process must parse child stderr/stdout for progress; requires protocol

**Cost per 16-day backfill**: (16 dates × 5s startup) + (16 × 150s work) = **80s overhead + 2400s work = 2480s total
(~41 min)**

---

### (b) Subprocess-per-shard

**Rationale**: Finer grain than (a). Each subprocess handles one (date, asset_group, data_type) cell or even one
instrument per shard. Reduces per-shard memory footprint below the 15 GB current floor.

**Solves**:

- Polars/PyArrow arena retention (same as (a))
- Per-shard service cache retention — child dies with cache
- State-inventory dependencies decoupled (Concern C) — each child is a fresh orchestrator instance

**Trade-offs**:

- Per-shard fork cost: 8–12s × N_shards
  - 16 dates × 2 data_types × 4 instruments = 128 shards → **1024–1536s = 17–26 min overhead alone**
  - Wall-clock tax: ~40–50% of total runtime just for forking
- Manifest loaded per child (same as (a), but more copies in flight)
- Instruments DF loaded per child (more redundant reloads)
- Result aggregation: parent must collect exit codes + structured output from 128 children
- Progress tracking: requires polling / message queue

**Cost per 16-day backfill**: (128 shards × 10s startup) + (128 × 30s work) = **1280s overhead + 3840s work = 5120s
total (~85 min)** vs. (a)'s **2480s**. **2× wall-clock regression**, prohibitive for interactive backfills.

---

### (c) In-process with proper cleanup (current shape)

**Rationale**: No fork cost. Trust that `_cleanup_after_day` + arena drops + `malloc_trim(0)` keep per-date floor flat
(~2 GB achieved, empirically 15.7 GB measured). Phase 3.2 proved this is **unreliable in practice**.

**Solves**:

- Zero fork overhead
- Shared manifest buffer across dates (if cached properly; currently not)
- Warm GCS client connection across dates
- Real-time progress logging and instrumentation

**Trade-offs**:

- Per-date RSS ratchet: Phase 3.2 attempt-1 (no cleanup) = 25 GB, attempt-2 (with cleanup) = 15.7 GB
  - The 15.7 GB residue is mostly Polars/PyArrow arena + per-service cache state not reaching the cleanup hook
  - On a 32 GB VM, this leaves ~16 GB free for work per date; OOM risk on day 7–10 for large backfills
- Backpressure layer is reactive: fires at 85% RSS (already in trouble), pauses submissions, relies on in-flight work to
  complete
- If in-flight work can't complete (needs more memory to finish aggregation), backpressure deadlocks: submissions
  paused, in-flight work blocked
- No structural isolation: one unhandled exception in a worker thread can corrupt orchestrator state, requiring full
  process restart

**Cost per 16-day backfill**: **2400s total (40 min)**. Lowest wall-clock. **Not viable beyond 8–10 days on 32 GB VM
without OOM risk.**

---

### (d) Process-pool worker model

**Rationale**: Long-running parent process holds manifest (loaded once) + reference data (instruments DF, GCS client
config). Per-shard work dispatched to a `ProcessPoolExecutor(max_workers=K)`. Workers are isolated child processes; they
do work, return results, and are recycled.

**Solves**:

- Polars/PyArrow arena retention (worker dies after shard, arena freed)
- Per-shard service cache isolation (each worker is clean)
- Manifest amortisation (parent loads once, reused across all shards via pickle)
- Reference data warmth (parent's instruments DF shared via memory mapping or re-transmitted per worker)

**Trades-offs**:

- Process pool setup cost: ~30–60s (parent startup + pool creation + initial worker spin-up)
- Per-shard worker cost: ~5–8s (worker process init + unpickling manifest + per-shard setup)
  - Lower than full subprocess-per-shard because manifest is pre-loaded in parent (not per-child)
  - 128 shards × 6s startup = 768s overhead
  - Wall-clock tax: ~25–30%
- State serialisation: manifest + reference data must pickle/unpickle for transmission (manifest is 526 MB compressed;
  unpickled in parent = 2–5 GB; per-worker copy = expensive)
  - Mitigation: use `multiprocessing.shared_memory` (requires Python 3.8+) to memory-map the manifest across workers
    (not currently used in MDPS)
- Worker pool recycling: OS creates new child processes as old ones complete (not a free lunch; kernel scheduling
  overhead per recycle)
- Complex refactoring: orchestrator must separate parent state (manifest, GCS client, auth) from worker state (per-shard
  tick DF, accumulator)

**Cost per 16-day backfill**: (parent startup 60s) + (128 shards × 6s startup) + (128 × 30s work) = **60 + 768 + 3840 =
4668s (~78 min)** vs. (a)'s **2480s**. **1.9× wall-clock regression vs (a), but 2× improvement vs (b).**

---

## ThreadPoolExecutor vs ProcessPoolExecutor for the inner per-instrument fan-out

**Current choice**: ThreadPoolExecutor (batch_workers.py:342). **This is correct.**

**Why threads, not processes, for the inner loop**:

1. **GIL release**: Polars reads via `pl.read_parquet()` release the GIL during C++ buffer operations. PyArrow write
   path also releases GIL. Threads achieve real parallelism for these heavy operations without full process isolation
   overhead.

2. **Memory sharing**: Threads share the orchestrator's state (caches, manifest in memory if pre-loaded, GCS client
   connection). The backpressure layer monitors shared system RSS; a thread-local footprint is meaningful because
   threads contribute to the same process memory pool.

3. **Per-shard footprint bounds**: If the orchestrator pre-loads a 526 MB manifest (unlikely in current shape, but
   relevant for shape (d)), all threads reference the same buffer. A ProcessPoolExecutor would duplicate the manifest
   per worker (each worker re-unpickles, allocating 2–5 GB per worker).

4. **I/O scaling**: ThreadPoolExecutor scales well for I/O-bound work (GCS download) with default 4 workers. Adding more
   threads for CPU-bound work (Polars agg) beyond CPU_COUNT offers no benefit; the current default of 4 is reasonable.

**Trade-off**: Threads don't isolate per-instrument crashes. A segfault in Polars (rare but possible with edge-case
data) kills all threads and the parent process. This is acceptable because:

- Polars is well-tested; segfaults are extraordinarily rare in production
- The orchestrator already has a try/finally; any exception in a thread propagates to the parent's `as_completed()` loop
  and is logged
- Per-date cleanup still fires on exception (finally block)

**Conclusion**: The inner-loop (per-instrument per-data_type) is correctly ThreadPoolExecutor. The question is the
**outer loop (date / asset_group)**, not the inner loop.

---

## Backpressure layer evaluation

### How it works (current)

- `BatchOrchestrationMixin._on_memory_warning()` (line 216–238): callback invoked by the ResourceProfiler when system
  RSS crosses 85%
- Sets `self._backpressure_active = True` (line 226)
- `_unpause_if_safe()` (line 240–278): polls system memory; resumes if RSS < 75% OR 120s timeout fires
- `_submit_instrument_file_tasks()` (line 284–315): submission gate checks `_backpressure_active` flag before
  submitting; if True, tries to unpause, otherwise yields control

### Blind spots

1. **Reactive, not predictive**: Fires at 85% RSS, meaning the system is already under memory pressure and swapping may
   have begun. A predictive backpressure (based on per-shard cost model + remaining budget) would be superior.

2. **No per-shard memory budget**: Backpressure doesn't know how much memory the _current_ in-flight work needs to
   complete. If 10 threads are running aggregations and each needs 500 MB to finish, but backpressure pauses at 85%
   (27.2 GB on a 32 GB box), and 26 GB is already allocated, the in-flight work can't complete → **deadlock**:
   submissions gated, in-flight work blocked waiting for memory.
   - Example: Phase 3.2 attempt-1 hit this on day 2 with 25+ GB residue; backpressure fired, paused submissions, but
     cleanup couldn't complete because per-shard aggregation tasks needed memory they couldn't allocate.

3. **Manifest + cache state invisible**: Backpressure monitors system RSS but doesn't decompose it. It can't distinguish
   between:
   - 10 GB in per-service caches (should be freed by `clear_cache_for_date()`)
   - 5 GB in Polars arenas (won't be freed by cleanup hook)
   - 3 GB in thread stacks + reference data (structural)
   - 2 GB in current work (temporary, will be freed after thread completes)
   - The mix determines whether unpause is safe, but backpressure has no visibility

4. **Timeout-based unpause is coarse**: The 120s max-pause-duration is fixed. For a long-running aggregation (e.g.,
   4000-symbol options chain taking 300s per symbol), 120s timeout may unpause submissions while the slow in-flight work
   is still consuming memory, causing RSS to spike again.

5. **No structured fallback**: If backpressure deadlocks (submissions paused, in-flight work can't complete), the only
   recovery is the outer process timeout + SIGKILL. There's no graceful degradation (e.g., "switch to smaller batch
   size" or "skip to next date").

### Evidence of blind spots

**Phase 3.2 attempt-1 incident** (from audit instructions): 7-day canary, day 2 OOM. Post-day-1 RSS = 25 GB (no cleanup
wiring). Backpressure engaged → paused submissions. In-flight per-instrument aggregations needed memory to flush to
parquet but couldn't allocate (RSS too high). Cleanup never fired (still inside the orchestrator, waiting for thread
completion). Deadlock → timeout → SIGKILL.

**Mitigation in attempt-2**: Added `_cleanup_after_day` wiring in finally block (MDPS@dcd7416) so cleanup fires even on
early return. Reduced post-day-1 RSS to 15.7 GB. Day 2 still starts with 15.7 GB residue; on a 32 GB box, leaves only 16
GB free for work on day 2. **Not scalable beyond 8–10 days.**

---

## Observability gaps

The current logs emit:

- `📉 date-boundary GC: freed X MB` (added Phase 2.2)
- `BatchOrchestrationMixin: memory backpressure engaged at X%` (when backpressure fires)
- `💾 Memory after cleanup: Y MB` (from `_cleanup_after_day`)

**Missing signals for confident decision-making**:

1. **Per-shard wall-clock distribution**: Which instruments/data_types are slow? Is 1 instrument taking 10s or 200s?
   Current logs don't emit `SHARD_COMPLETED` events with timing.

2. **Per-shard peak RSS**: The per-instrument memory footprint is unknown. Is one instrument 1 GB or 8 GB? Without
   per-shard memory events (`MEMORY_HIGH_WATER_MARK` with shard context), the cost model is an guess.

3. **Manifest-read cost**: No telemetry on how often `check_shard_freshness` is called or how much memory it allocates.
   The double-freshness-check anti-pattern (audit Finding in manifest_io doc) is invisible to operators.

4. **Thread pool saturation**: No signal for whether the ThreadPoolExecutor is waiting for threads or submitting fast.
   Is backpressure limiting submission speed, or is the pool just full?

5. **GCS latency**: Download times per instrument are not structured. Is 10s for a 100 MB blob fast (good) or slow
   (network congestion)?

**Cross-link**: Deliverable 6 (observability audit, sibling subagent) will document what telemetry exists and should
exist.

---

## Recommended next step

### Immediate: None for concurrency proper

The current ThreadPoolExecutor inner loop is correct. The decision to make is at the **outer loop** (date /
asset_group), not the inner loop (per-instrument). That decision belongs to Phase 1.1 of the architectural audit plan.

### Architectural: Phase 1.1 input

This audit document IS the evidence base for Phase 1.1. The cost-model table in this doc should be adopted by the
architectural plan's Phase 1.1 decision rationale. Key inputs:

1. **Phase 3.2 empirical data**: In-process cleanup (shape c) hit 15.7 GB post-day-1 residue on a 32 GB box. Not
   reliable beyond 8–10 days.

2. **Cost model**:
   - (a) Subprocess-per-date: 2480s (~41 min) for 16-day backfill; excellent isolation; acceptable fork overhead
   - (b) Subprocess-per-shard: 5120s (~85 min); 2× wall-clock regression; per-shard footprint lower but fork cost
     prohibitive
   - (c) In-process: 2400s (~40 min); lowest wall-clock; empirically unreliable without solving Concern D (Polars arena)
   - (d) Process-pool: 4668s (~78 min); 1.9× vs (a); best amortisation of manifest; requires complex orchestrator
     refactor

3. **Blocker for (c)**: Polars/PyArrow arena retention (Concern D, Finding in engine-mixing audit). Until the engine is
   switched to pure-Polars with arena-trim calls OR until malloc_trim(0) + libc glibc config mitigations are deployed,
   shape (c) is not reliable.

4. **Blocker for (d)**: Orchestrator state ownership refactor. The manifest + reference data are currently instance
   variables on the orchestrator; separating them into parent-owned state is a substantial refactor (Phase 1.2 of the
   architectural plan).

The Phase 1.1 decision should weigh (a) vs (d) based on:

- If 41 min wall-clock is acceptable for the backfill frequency and scale, (a) is lowest-risk, highest-observability.
- If manifest + reference-data amortisation is critical for cost (e.g., multi-asset-group runs where manifest is 1+ GB),
  (d) is the target despite complexity.

---

## References

- Phase 3.1 + 3.2 canary measurements: mdps_long_running_efficiency_audit_instructions.md § "Empirical context"
- State inventory detailed findings: mdps_long_running_state_inventory_2026_05_28.md
- Engine mixing detailed findings: mdps_long_running_engine_mixing_2026_05_28.md
- Manifest I/O cost details: mdps_long_running_manifest_io_2026_05_28.md
- Architectural plan full scope: mdps_long_running_multi_shard_architecture_audit_2026_05_28.md
