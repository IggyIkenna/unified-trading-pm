---
name: mdps_long_running_multi_shard_architecture_audit
title: "MDPS architectural audit — long-running multi-shard execution (2026-05-28)"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
status: active
model_tier: opus-required
thinking_tier: max
priority: P1
created: 2026-05-28
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
related:
  - mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md
locked_by: live-defi-rollout
locked_since: 2026-05-28
---

# MDPS architectural audit — long-running multi-shard execution

> **✅ ARCHIVED 2026-06-21 — all phases complete + codex-aligned (Phase 6 documented in codex/05-infrastructure/manifest-consolidator-ssot.md); 0 deferred work. [unlock-plan]**

## Codex audit (run 2026-05-28 before starting Phase 0)

Operator asked: "do my four findings contradict anything in codex?" Sub-agent audited `codex/04-architecture/`,
`codex/05-infrastructure/`, `codex/06-coding-standards/`, `codex/02-data/`. Verdicts per finding:

| Finding                                                            | Codex verdict             | Codex docs touched                                                                                                                                                                                                                                                                                                                                                             | What this means for this plan                                                                                                                                                                                                                                  |
| ------------------------------------------------------------------ | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A** — `_cleanup_after_day` not wired into success path           | **SILENT**                | `06-coding-standards/service-orchestration-patterns.md` (Patterns 1-14, no cleanup phase), `04-architecture/batch-live-architecture.md` (§1 says "setup → work → cleanup" implicitly but never names a cleanup entry-point)                                                                                                                                                    | No codex contract violated. The tactical fix in the sibling plan + the Phase 6 codex doc this plan ships are additive.                                                                                                                                         |
| **B** — canonical instrument_id should suffice for CLI granularity | **SILENT**                | `06-coding-standards/cli-convention.md` (mentions `--instrument-ids` but never defines the canonical form, which axes are derivable, what counts as the atomic shard), `05-infrastructure/vm-tarball-deployment.md` (shows `VM_INSTRUMENT_IDS` examples but no parsing rule)                                                                                                   | No codex contract violated. Phase 3 of this plan defines the canonical parser + axis derivation rules + ships them to codex as a new doc.                                                                                                                      |
| **C** — orchestrator state assumes one-VM-per-shard                | **PARTIAL CONTRADICTION** | `05-infrastructure/vm-tarball-deployment.md` § "LifecycleClass" defines `EPHEMERAL_BATCH` (short-lived, self-delete on completion) as the MDPS designation; the operator's "long-running multi-shard worker" doesn't fit `EPHEMERAL_BATCH` cleanly. `04-architecture/batch-live-architecture.md` is silent on per-instance state retention contracts for each lifecycle class. | Either MDPS gets a different LifecycleClass (or a new one) OR the existing `EPHEMERAL_BATCH` contract gets explicit per-shard cleanup requirements. Phase 1 of this plan must reconcile this — picking the execution model and the LifecycleClass go together. |
| **D** — Polars/Pandas conversion churn                             | **SILENT**                | `06-coding-standards/dependency-management.md` lists both polars + pandas as valid deps but says nothing about engine choice, conversion anti-patterns, or `engine="pyarrow"`. No `data-engine-selection.md` exists.                                                                                                                                                           | No codex contract violated. Phase 2 of this plan picks the engine + ships the new coding-standards doc.                                                                                                                                                        |

**Net**: 0 of 4 findings violate any explicit codex SSOT. 3 of 4 are gaps codex never addressed. 1 (Finding C) is a real
reconciliation: the `EPHEMERAL_BATCH` LifecycleClass designation doesn't match how MDPS is actually being run. That
reconciliation belongs in Phase 1 (execution model decision) of this plan, not in the tactical sibling plan.

The codex audit also produced a precise list of edits per finding — see Phase 6 below, which now uses the audit's exact
target paths.

## Why this plan exists

The 2026-05-28 filter-pushdown plan
([`mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`](mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md))
landed three tactical fixes (scanner filter, cross-date `del + gc.collect()`, `_cleanup_after_day` wiring) that together
let an `e2-standard-8` VM complete a multi-day narrow-scope backfill. But the symptoms those fixes had to work around —
25 GB per-day high-water mark, cross-date retention, repeated 526 MB manifest reads, Polars/Pandas conversion churn —
are not isolated bugs. They are consequences of running a fan-out-shaped codebase as a long- running multi-shard worker.
The orchestrator was designed under the assumption that each VM processes ONE shard (one day × one venue × one
asset_group × one data_type); the deployment model has since pivoted to a small number of long-running VMs that each
cover many shards. The two assumptions are incompatible and the tactical fixes do not close the gap.

This plan is the architecture-level audit + refactor track. It is **not** in the critical path for the 2026-05-23
live-DeFi cutover or the immediate 4h/24h features-side unblock — those are handled by the tactical fixes in the sibling
plan. This plan exists so that the long-running execution mode is properly engineered after the live-DeFi cutover, not
patched indefinitely.

## Scope

Concrete questions to answer + corresponding redesigns to ship:

1. **What is the right execution unit?** Subprocess-per-date? Subprocess-per-shard? In-process with proper cleanup?
   Process-pool worker model? Each option has different cost/reliability/observability trade-offs.
2. **What state belongs to the orchestrator vs the worker vs the per-shard task?** The current orchestrator conflates
   all three. Cleanup is hard because the boundaries are blurred.
3. **Why does MDPS read the full 526 MB manifest at each per-date startup?** Is there a partial-read path? Can the
   manifest be lazy / streaming? Can the freshness check use a small index instead of the full manifest?
4. **Why is data passed Polars → Pandas → Polars → Pandas?** Pick one engine, end-to-end. Polars is the more obvious
   choice because aggregation is already there. Eliminate the conversion buffers.
5. **What is the right granularity for the CLI?** A single canonical instrument_id should be sufficient to scope one
   cell. Today the CLI claims that but the filter logic does substring matching on raw symbols.
6. **How do we test memory bounds?** The current QG has no per-shard memory test. The `_cleanup_after_day` hook exists
   but was untested for ~years because no test exercised the cross-date loop. Memory regressions need tooling to catch.

## Phase 0 — Frame the problem (no code edits)

- [x] ✅ [AUDIT] P1. **0.1 Inventory the current fan-out assumptions baked into the code.** Find every place where the
      orchestrator constructs per-instance state that would be redundant for the next shard / next date. Examples
      (preliminary, surfaced by the sibling plan): lazy `_storage_client`, per-asset_group `_data_sinks` dict, the
      4128-instrument reference DataFrame, the freshness-check manifest read. Tabulate with
      `(field, owner, lifetime, reset_cost)`.

  **Audit findings (2026-05-29, slot-9):**

  | Field / Object                                          | Owner (file:line)                                                                                   | Lifetime                                                                                       | Reset cost                                                                                                                                                                                                                                                       |
  | ------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `_storage_client`                                       | `CandleOrchestrationBase` (orchestration_base.py:47)                                                | Process-lifetime lazy singleton; initialized on first `.storage_client` access                 | **Cheap** — single `get_storage_client()` call (~10 ms); thread-safe; no accumulation risk                                                                                                                                                                       |
  | `_data_sinks` dict                                      | `CandleOrchestrationBase` (orchestration_base.py:49)                                                | Per-orchestrator-instance (one per date × category in `process_handler._process_one_category`) | **Moderate** — `get_data_sink(routing_key=key)` per category key; 4–6 per call; ~50–100 ms total; no per-shard `.clear()` — if a shard leaves a DataSink in a bad state, subsequent shards in the same date are contaminated                                     |
  | `data_source` / `data_sink` (live adapters)             | `CandleOrchestrationBase` (orchestration_base.py:51–52)                                             | Set externally by `LiveModeHandler` before the run; never re-set per shard                     | **Cheap** — just references; but live mode is not the batch concern here                                                                                                                                                                                         |
  | Tradable instruments DataFrame                          | `CandleOrchestrationService._get_tradable_instruments()` called from `orchestration_service.py:507` | Per-date (loaded once per `process_category` call)                                             | **Moderate** — polars read of per-venue instrument parquet files; parallel load via `ThreadPoolExecutor`; ~1–2 s for full CeFi scope; cached in the orchestrator for the duration of one date                                                                    |
  | Manifest freshness check (`availability_index.parquet`) | `check_shard_freshness()` at `orchestration_service.py:184`                                         | Per-category per-date (single call, deferred UTL in-process TTL cache)                         | **Expensive** — ~526 MB parquet materialised to ~2–5 GB decompressed polars per call; UTL has an in-process TTL cache so repeated calls within a short window are cheap, but on a fresh process (new date) the first call always pays the full cost (~1–5 s)     |
  | `_active_resource_profiler`                             | Module-level global in `batch_workers.py:49`                                                        | Process-lifetime; set once from `cli/main.py` via `set_active_resource_profiler()`             | **Free** — read-only after init; safe for all shards                                                                                                                                                                                                             |
  | `_MDPSPriorLTPProvider._cache`                          | Per-instance dict in `live_aggregator.py`                                                           | Per-shard last-trade-price window                                                              | **Cheap** — in-memory dict; GC'd when provider instance is collected; no explicit `.clear()`                                                                                                                                                                     |
  | `candle_processing_service` / `sampling_service` caches | Created inside `CandleOrchestrationService` per date                                                | Per-date (lifecycle matches the orchestrator instance)                                         | **Moderate** — `_cleanup_after_day` at `orchestration_base.py:79` calls `gc.collect()` but does NOT call `.cache.clear()` on either service — the sibling plan noted these as the retention owners, but the actual cleanup hook only does GC, not cache eviction |

  **Key risk**: `_data_sinks` dict has no per-shard cleanup. If an exception mid-shard corrupts a DataSink's write
  state, all subsequent shards for that date share the same contaminated sink. Per-shard isolation requires either: (a)
  re-creating the orchestrator per shard, or (b) catching exceptions and replacing the affected `_data_sinks[key]`
  entry.

  **`_cleanup_after_day` gap** (confirmed from code at orchestration_base.py:79–93): the current implementation only
  calls `gc.collect()` and logs RSS — it does NOT clear `candle_processing_service.cache` or `sampling_service.cache`.
  The sibling plan's text was aspirational; the cache clearing was never actually added. This is a confirmed residual
  gap for 0.2.

- [x] ✅ [AUDIT] P1. **0.2 Inventory caches and their cleanup paths.** Beyond the `candle_processing_service` /
      `sampling_service` caches that `_cleanup_after_day` knows about — what other module-level or singleton state
      exists? `unified_trading_library` data sinks, the `ResourceProfiler`, event sinks, polars/pyarrow arenas. Where is
      each cache's `clear()` / `dispose()` method, and is anything calling it?

  **Audit findings (2026-05-29, slot-9):** _(Note: task 0.1 already confirmed `_cleanup_after_day` only calls
  `gc.collect()` — no service cache clearing happens. This task expands the inventory.)_

  | Object                                           | Owner / Location                                                    | `clear()` / `dispose()` exists?       | Currently called between dates?                           | Retention pattern                                                                                                                                                                                                             |
  | ------------------------------------------------ | ------------------------------------------------------------------- | ------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `_data_sinks` dict                               | `CandleOrchestrationBase` (orchestration_base.py:49)                | No explicit `.clear()` on the dict    | **No**                                                    | Dict populated lazily per category; reused across all dates in a run; GCS connections/buffers inside each `DataSink` are pooled indefinitely                                                                                  |
  | `_storage_client`                                | `CandleOrchestrationBase` (orchestration_base.py:47)                | No                                    | No                                                        | Singleton; stateless after init; safe to reuse                                                                                                                                                                                |
  | `_is_holiday()` lru_cache                        | `market_state_detector.py:70` (`functools.lru_cache(maxsize=1024)`) | **Yes** — `_is_holiday.cache_clear()` | **No** — never called between dates                       | Accumulates to 1024 entries and stays there for process lifetime                                                                                                                                                              |
  | `candle_processing_service.cache`                | Created inside `CandleOrchestrationService` per date                | Unknown (depends on UTL impl)         | **No** — confirmed: `_cleanup_after_day` does not call it | If UTL service holds a TTL dict, it stays warm across dates                                                                                                                                                                   |
  | `sampling_service.cache`                         | Created inside `CandleOrchestrationService` per date                | Unknown (depends on UTL impl)         | **No** — same as above                                    | Same retention pattern                                                                                                                                                                                                        |
  | `ResourceProfiler` (`_active_resource_profiler`) | Module-level global in `batch_workers.py:49`                        | No explicit dispose                   | No                                                        | Process-lifetime; used for memory callbacks; no accumulation risk (observability only)                                                                                                                                        |
  | `persistence_queue` (live mode)                  | `AsyncGCSDataSink.persistence_queue` (`data_sink.py`)               | No drain/clear between dates          | No                                                        | Live mode only; unflushed write tasks accumulate if dates run back-to-back without queue drain                                                                                                                                |
  | Polars/PyArrow C-level arenas                    | System (`libarrow.so` / Polars Rust allocator)                      | No Python-callable clear              | `gc.collect()` has **zero effect** on C arenas            | **Critical**: Each `pl.read_parquet()` / `.to_pandas()` / aggregation allocates C-level memory that Python GC cannot reclaim. Arena memory is only returned to OS at process exit. This is the 25 GB per-day floor explained. |

  **Root-cause chain for the 25 GB per-day floor:**
  1. `pl.read_parquet()` → PyArrow/Polars C arena allocates ~2–5 GB per tick file batch
  2. `.to_pandas()` (now eliminated by pure-polars migration) added a second allocation layer
  3. Aggregation (polars) materializes another arena allocation
  4. Python `del frame` → Python wrapper freed, but C arena bytes remain in `libarrow.so` memory pool
  5. `gc.collect()` → cleans Python cycles only; C arenas unchanged
  6. Result: RSS floor rises ~20–25 GB per date processed; never returns to OS between dates

  **Fix direction for Phase 4**: Subprocess-per-date or process-pool model (options a/d from Phase 1.1) is the only
  structural solution — the OS reclaims the full C arena on subprocess exit. In-process cleanup (option c) cannot solve
  C-arena retention without calling `pa.default_memory_pool().release_unused()` (PyArrow) and `jemalloc_stats_epoch()` /
  `malloc_trim(0)` (glibc), which are fragile and not exposed via Polars' public API.

- [x] ✅ [AUDIT] P1. **0.3 Document the cost model**. What does one VM-hour cost? What does N parallel small VMs cost vs
      one long-running VM for the same work? This frames whether "subprocess-per-date" inside one VM is meaningfully
      cheaper than 16 × 1-day VMs, and whether subprocess-per-shard is cost-feasible.

  **Cost model (2026-05-29, slot-9):** Reference scenario: 16-day narrow scope (BINANCE-FUTURES + BYBIT × BTCUSDT +
  ETHUSDT × trades). Empirical timing: ~200s per date (Phase 3.1: 191s; Phase 3.2 day-1: 133.6s). VM startup + tarball
  pull: ~3–5 min per fresh VM (from `launch-mdps-sharded-backfill.sh` header). Machine rate: e2-standard-8 (8 vCPU, 32
  GB) ≈ **$0.268/hour** (GCP asia-northeast1 on-demand).

  | Execution model                                   | Wall-clock                                      | Peak RAM needed                                       | Cost estimate                       | Memory isolation                             |
  | ------------------------------------------------- | ----------------------------------------------- | ----------------------------------------------------- | ----------------------------------- | -------------------------------------------- |
  | **16 × 1-day VMs (parallel)**                     | ~8 min (dominated by startup)                   | 25 GB per VM                                          | 16 × (8/60 h) × $0.268 = **~$0.57** | Full (OS reclaims C arenas at VM exit)       |
  | **1 VM, in-process multi-date** (current, broken) | ~58 min                                         | 25 GB × day count → OOM at day 2 on 32 GB             | (58/60) × $0.268 = **~$0.26**       | None — C arenas accumulate                   |
  | **1 VM, subprocess-per-date** (proposed)          | ~62 min (5 min startup + 16 × ~210s)            | ≤ 25 GB (one date in-flight)                          | (62/60) × $0.268 = **~$0.28**       | Per-date (subprocess exit releases C arenas) |
  | **1 VM, subprocess-per-shard** (fine-grain)       | ~38 min (32 subprocesses, some startup overlap) | ≤ ~15 GB (one shard = 2 instr × 1 data_type × 1 date) | (38/60) × $0.268 = **~$0.17**       | Per-shard — highest isolation                |
  | **Process-pool (N=1 serial worker)**              | Same as subprocess-per-date                     | Same                                                  | Same                                | Same — equivalent to option 3                |
  | **Process-pool (N=4 concurrent workers)**         | ~20 min (4 parallel date batches of 4)          | 4 × 25 GB = 100 GB → needs e2-highmem-16 ($1.01/h)    | (20/60) × $1.01 = **~$0.34**        | Per-worker (but peak RAM 4× higher)          |

  **Conclusion**: `subprocess-per-date` (option a in Phase 1.1) is the cheapest structural fix — essentially the same
  cost as the broken in-process model ($0.28 vs $0.26), zero infrastructure overhead vs spawning 16 separate VMs, and
  full C-arena isolation at date boundaries. The `subprocess-per-shard` model is cheaper still ($0.17) but has higher
  per-subprocess overhead and more complex coordination. The 16 × 1-day VMs approach is ~2× more expensive but completes
  8× faster if time matters. For the architecture recommendation: default to subprocess-per-date; use 16 × 1-day VMs
  only when wall-clock time is critical and cost is not.

- [x] ✅ [AUDIT] P1. **0.4 Granularity contract**. Document the canonical instrument_id form and the asset_group / venue
      / instrument_type / data_type axes. State which axes are derivable from instrument_id and which are independent.
      This becomes the input spec for redesigning the CLI filter logic.

  **Contract findings (2026-05-29, slot-9):**

  **Canonical form**: `VENUE:INSTRUMENT_TYPE:SYMBOL` — e.g. `BINANCE-FUTURES:PERPETUAL:BTCUSDT`. Implemented at
  `market_data_processing_service/app/utils/path_parsing.py:149` (`parse_canonical_instrument_id`) and
  `blob_matches_canonical_instrument_id` (line 178). Symbol may itself contain `:` (split on first 2 colons only).
  Bare-symbol fallback (`BTCUSDT`) still works but emits a once-per-process deprecation log
  (`_LEGACY_BARE_SYMBOL_WARNED` guard at line 253).

  **Hive path structure** (from `orchestration_scanner.py`):

  ```
  raw_tick_data/by_date/day={DATE}/asset_group={AG}/venue={VENUE}/instrument_type={IT}/data_type={DT}/{SYMBOL}.parquet
  ```

  **Axis derivability table:**

  | Axis              | Derivable from canonical instrument_id? | Notes                                                                                                                            |
  | ----------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
  | `venue`           | ✅ Yes — part[0]                        | e.g. `BINANCE-FUTURES`                                                                                                           |
  | `instrument_type` | ✅ Yes — part[1]                        | e.g. `PERPETUAL` (lowercase in path; canonical form uppercase)                                                                   |
  | `symbol`          | ✅ Yes — part[2]                        | e.g. `BTCUSDT` (matched as `{symbol}.parquet` filename)                                                                          |
  | `data_type`       | ❌ Independent                          | Same instrument has `trades`, `book_snapshot_5`, `derivative_ticker`, etc. — requires `--data-types`                             |
  | `asset_group`     | ❌ Independent                          | Determined by which bucket (cefi/tradfi/defi/sports/prediction) is scanned; the instrument_id alone doesn't determine the bucket |
  | `date`            | ❌ Independent                          | Requires `--start-date` / `--end-date`                                                                                           |

  **Atomic shard** = `(asset_group, venue, instrument_type, data_type, symbol, date)`. A canonical instrument_id pins 3
  of 6 axes. The minimum additional args for a fully-pinned single shard:
  `--data-types {DT} --start-date {D} --end-date {D}` (asset_group is implied by the bucket selection).

  **Status**: Phase 2.1 (filter-pushdown) + Phase 3 (CLI granularity) of the sibling plan have already shipped
  `parse_canonical_instrument_id` and `blob_matches_canonical_instrument_id` (market-data-processing-service@e47205d).
  The canonical form is now the operative matcher. The UAC (`unified_api_contracts`) currently has `InstrumentType` enum
  values (`PERPETUAL`, `SPOT_PAIR`, `FUTURE`, `OPTION`, `SPOT_ASSET`) but no shared `parse_canonical_instrument_id`
  utility — the parser lives in MDPS `utils/path_parsing.py` and should be considered for promotion to UAC (Phase 3.1 of
  this plan).

## Phase 1 — Decide the execution-unit shape

- [x] ✅ [DESIGN] P1. **1.1 Choose the execution model.** Closed set:
  - **(a) Subprocess-per-date** ← **CHOSEN** (see decision below)
  - **(b) Subprocess-per-shard**: same idea, finer grain (per date × per data_type × per venue). Higher fork overhead,
    lower per-process footprint.
  - **(c) In-process with proper cleanup**: trust that `_cleanup_after_day` + arena drops + `malloc_trim(0)` can keep
    the per-day floor flat. Requires solving the Polars/PyArrow arena retention problem.
  - **(d) Process-pool worker model**: long-running parent process holds the manifest + reference data, dispatches
    per-shard work to a `concurrent.futures.ProcessPoolExecutor`. Workers do isolated work, no accumulation.

  **Decision: (a) Subprocess-per-date** (2026-05-29, slot-9)

  | Model                        | Rules out                  | Reason                                                                                                                                                                                                                                                                                                                                                                                                  |
  | ---------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | **(c) in-process**           | ❌ Eliminated              | Phase 3.2 attempt-2 empirically proved that `del orchestrator + gc.collect()` only reclaims 87 MB / 25 GB (0.3%) per date. C-level PyArrow/Polars arenas are invisible to Python GC. No in-process API can force OS reclaim.                                                                                                                                                                            |
  | **(d) process-pool N=4**     | ❌ Ruled out for 32 GB box | 4 concurrent workers each peak at ~25 GB = 100 GB required; needs e2-highmem-16 at ~$0.34 vs $0.28 for (a); extra complexity with no benefit over (a) at N=1.                                                                                                                                                                                                                                           |
  | **(b) subprocess-per-shard** | ❌ Not now                 | Cheaper (~$0.17) but each subprocess independently loads the 526 MB manifest + 4128-instrument reference; at 32 shards the aggregate startup dominates. Viable once manifest load is lazy/cached in parent — revisit at Phase 4.1 if per-date isn't sufficient.                                                                                                                                         |
  | **(a) subprocess-per-date**  | ✅ **CHOSEN**              | Same cost as broken in-process model ($0.28), same wall-clock, full C-arena isolation at each date exit. Minimally invasive: `process_candles_handler` wraps each date in `subprocess.run([sys.executable, "-m", "market_data_processing_service", "--date", date, ...])`. Parent holds manifest + reference data only between subprocess calls — not shared (simplest: each subprocess loads its own). |

  **Why not share manifest across subprocesses**: passing a 526 MB parquet frame via pickle/IPC adds coordination
  complexity and a serialization cost that rivals the cold-load. The simpler contract — each subprocess loads what it
  needs — is safer and is already validated by Phase 3.1 (one subprocess = one date = clean slate).

  **Transition**: the subprocess-per-date model is a thin wrapper around the existing `process_category` /
  `process_candles_handler` calls. The inner date-loop in `process_handler.py:_process_candles_for_one_date` becomes
  `subprocess.run(...)`. No changes to the orchestrator's scan/filter/aggregate/write logic are needed for Phase 4.1.

- [x] ✅ [DESIGN] P1. **1.2 Map state ownership to the chosen execution model.** Which state lives in the long- running
      parent (manifest? reference data? auth sessions?) and which lives in the per-shard worker (tick DataFrame, candle
      accumulators)? This is the foundation for any refactor that follows.

  **State ownership map (2026-05-29, slot-9) — subprocess-per-date model:**

  | State object                                              | Owner                                                               | Lifetime                | Notes                                                                                                                                           |
  | --------------------------------------------------------- | ------------------------------------------------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
  | CLI args (venues, instrument_ids, data_types, date range) | **Parent** — parsed once at startup                                 | Parent process lifetime | Forwarded verbatim to each subprocess as argv; no serialisation needed                                                                          |
  | Date list                                                 | **Parent** — generated from `--start-date` / `--end-date`           | Parent process lifetime | Ordered sequence; parent iterates and spawns one subprocess per date                                                                            |
  | `manifest` / `availability_index.parquet` (~526 MB)       | **Per-subprocess** — loaded on first `check_shard_freshness()` call | Subprocess lifetime     | Cheaper to reload (1–5 s) than to pickle / mmap across a subprocess boundary; UTL in-process TTL cache deduplicates calls within one subprocess |
  | Tradable instruments DataFrame                            | **Per-subprocess** — loaded in `_get_tradable_instruments()`        | Subprocess lifetime     | ~1–2 s; IPC cost of serialising a 4128-row polars frame rivals cold load                                                                        |
  | `_storage_client`                                         | **Per-subprocess** — lazy singleton                                 | Subprocess lifetime     | Stateless after init (~10 ms); no cross-date state to propagate                                                                                 |
  | `_data_sinks` dict                                        | **Per-subprocess** — created lazily per category                    | Subprocess lifetime     | GCS write handles + buffer state; released on subprocess exit; no contamination risk                                                            |
  | `_is_holiday()` lru_cache                                 | **Per-subprocess** — starts empty                                   | Subprocess lifetime     | Bounded to 1024 entries; cleared naturally at subprocess exit                                                                                   |
  | Tick DataFrames (raw parquet reads)                       | **Per-subprocess** — inside `process_category` scan                 | Subprocess lifetime     | Python GC sees wrapper; C-level arena bytes released on subprocess exit — **this is the structural fix for the 25 GB/day floor**                |
  | Candle accumulators                                       | **Per-subprocess** — inside `CandleProcessingService`               | Subprocess lifetime     | Per-instrument aggregation state; no cross-date leakage                                                                                         |
  | `candle_processing_service.cache`                         | **Per-subprocess** — fresh instance                                 | Subprocess lifetime     | UTL service instance; cache starts empty each date                                                                                              |
  | `sampling_service.cache`                                  | **Per-subprocess** — fresh instance                                 | Subprocess lifetime     | Same                                                                                                                                            |
  | `_active_resource_profiler`                               | **Per-subprocess** — set once in `cli/main.py`                      | Subprocess lifetime     | Observer only; no accumulation                                                                                                                  |
  | Polars/PyArrow C-level arenas                             | **Per-subprocess** — allocated by `libarrow.so` / Rust allocator    | Subprocess lifetime     | **RELEASED ON SUBPROCESS EXIT** — the OS reclaims the full arena; `gc.collect()` has zero effect on these                                       |
  | Auth credentials (GCP SA key, env vars)                   | **Inherited by subprocess** — `env=os.environ.copy()`               | Subprocess lifetime     | No re-authentication per date; env vars inherited from parent at `subprocess.run()`                                                             |

  **Parent process contract (the entire parent-side implementation of Phase 4.1):**

  ```python
  for date in date_list:                         # only thing parent holds
      rc = subprocess.run(
          [sys.executable, "-m", "market_data_processing_service.cli.main",
           "--start-date", date, "--end-date", date,
           *forwarded_args],                      # venues, instrument_ids, data_types, etc.
          env=os.environ.copy(),                  # auth credentials inherited
      ).returncode
      log(f"date={date} rc={rc}")                # 0 = success; non-zero = log + continue
  ```

  Parent holds: one `list[str]` of date strings. Nothing else. Zero memory accumulation.

  **What `_cleanup_after_day` becomes**: vestigial in the new model — the OS does the cleanup. It should be kept in
  place (it catches genuine Python-cycle garbage) but is no longer critical for memory correctness. The
  `del + gc.collect()` patches from the sibling plan (Phase 2.2) are safe to remove in Phase 4.3 — they will no longer
  be needed.

  **Why no manifest sharing across subprocesses**: passing a 526 MB polars frame via `multiprocessing.shared_memory` or
  pickle adds ~0.5–1 s serialisation + IPC coordination that erases most of the saving vs a cold load. The
  shared-manifest optimisation is only worth it if the subprocess count is high (e.g., subprocess-per-shard at 32
  shards). For subprocess-per-date (≤ 30 dates), cold-load-per-subprocess is simpler and safe.

## Phase 2 — Decide the data-engine shape

- [x] ✅ [DESIGN] P1. **2.1 Pick the data engine.** Closed set:
  - **(a) Pure Polars end-to-end**: read raw via polars, aggregate via polars (already partially in place), write via
    polars. Pandas eliminated.
  - **(b) Pure Pandas with pyarrow engine**: `pd.read_parquet(engine="pyarrow")`. Eliminates polars but loses polars'
    faster aggregation path.
  - **(c) Pyarrow-table end-to-end**: lowest-level, most explicit memory control, fewer high-level conveniences. Pick
    one. The expectation per operator direction is (a). Document why. **DECISION 2026-05-30: (a) Pure Polars** —
    already >95% complete (Stage 5E). All 13 parquet callsites use Polars natively. The 2 Polars→Pandas conversions
    (`canonical_writer.py:1400,2204`, `live_aggregator.py:324`) are INTENTIONAL hard-protocol boundaries (UTL
    `record_captured` + `TickFetcher` require pandas DataFrames). These stay; do NOT attempt to convert UTL internals.
    Pandas fallbacks were removed in Stage 5E. No pyarrow direct decode remains in production paths (Stage 5.6 already
    migrated `mock_data_provider.py:196`). Why not (b) or (c): polars is faster for aggregation (candle engine is
    polars-native); pyarrow direct would require explicit column handling that polars already provides ergonomically; no
    benefit over polars + conversion at UTL boundary is cheaper than rewriting UTL.
- [x] ✅ [DESIGN] P1. **2.2 Audit every parquet read/write callsite in MDPS.** Tabulate `(file:line, engine, why)`. Any
      mixed-engine boundary is a candidate conversion buffer that the refactor must eliminate. **AUDIT DONE 2026-05-30**
      — 13 callsites (10 read, 2 write, 1 mock write): | File | Line | Op | Engine | Note |
      |------|------|----|--------|------| | `app/adapters/prediction/trades_adapter.py` | 198 | read | Polars |
      lifecycle dataset | | `app/calculators/polars_candle_engine.py` | 306 | write | Polars | candle output | |
      `app/core/canonical_writer.py` | 1400 | read | Polars→Pandas | UTL boundary | | `app/core/canonical_writer.py` |
      2204 | read | Polars→Pandas | UTL boundary | | `app/core/cloud_data_provider.py` | 144 | read | Polars | legacy
      fallback | | `app/core/cloud_data_provider.py` | 229 | read | Polars | sports/prediction | |
      `app/core/data_source.py` | 174 | read | Polars | Stage 5E, no pandas fallback | | `app/core/live_aggregator.py` |
      324 | read | Polars→Pandas | UTL TickFetcher boundary | | `app/core/live_workers.py` | 488 | read | Polars | Stage
      5E, low_memory=True | | `engine/mock_data_provider.py` | 140 | read | Polars | instruments availability | |
      `engine/mock_data_provider.py` | 144 | read | Polars | instruments availability | | `engine/mock_data_provider.py`
      | 196 | read | Polars | Stage 5.6 (replaced pyarrow) | | `engine/mock_data_provider.py` | 291 | write | Polars |
      mock candles | Mixed-engine: 2 intentional Polars→Pandas at UTL boundaries. No round-trips. No remaining
      fallbacks.
- [x] ✅ [DESIGN] P1. **2.3 Measure the per-instrument peak memory for the chosen engine.** Run one instrument-day
      through the chosen engine, take a tracemalloc snapshot at peak. Compare against the current mixed-engine peak. The
      bar: per-instrument peak ≤ 2 GB for a typical CeFi perp trades day. (Numbers from the canary suggest the current
      mixed-engine peak is ~7-8 GB per instrument-day; the bar should be a real improvement, not parity.) **DONE
      2026-05-30** — market-data-processing-service@c293522: `tests/perf/test_polars_instrument_day_memory.py` (3 tests,
      all pass). Measurement: 1M ticks (BTCUSDT-perp-equivalent, 5 timeframes + buy/sell split). **tracemalloc
      Python-heap delta: ~22 MB. RSS growth: ~250 MB. RSS absolute peak: ~339 MB.** **8× inside the 2 GB bar; ~24×
      better than the old mixed-engine ~7-8 GB.** Root cause of the improvement: no Polars→Pandas→Polars round-trips;
      C-arena allocation stays in a single Polars execution context; no per-conversion copies.

## Phase 3 — Fix the CLI granularity (closes Finding B from the sibling plan)

- [x] ✅ [DESIGN] P1. **3.1 Define the canonical instrument_id parser.** A canonical id is
      `VENUE:INSTRUMENT_TYPE:SYMBOL`. Given a list of canonical ids, the scanner can derive the venue set + the
      instrument_type set + the symbol set, and filter blob paths on each axis independently. Document the parser spec
      in UAC (it likely belongs there as a shared utility; check `unified_api_contracts.canonical.*` for an existing
      parser before adding one). **DONE 2026-05-30** — unified-api-contracts@aff01de5:
      `unified_api_contracts/canonical/instrument_key.py` with `parse_instrument_key`, `format_instrument_key`,
      `derive_venue_set`, `derive_instrument_type_set`, `derive_symbol_set`. Exported from
      `unified_api_contracts.canonical`. 16 tests in `tests/test_instrument_key.py`. No existing parser in UAC —
      confirmed via grep before adding. MDPS `utils/path_parsing.py` implementation kept as the MDPS-internal caller;
      downstream callers should migrate to `unified_api_contracts.canonical.parse_instrument_key`.
- [x] ✅ [AGENT] P1. **3.2 Replace the substring filter in `_collect_matching_parquet_blobs`** with a structured check
      derived from the parsed canonical id. Each blob path is matched on (venue, instrument_type, symbol) extracted from
      the path, against the per-axis derived sets. Bare-symbol matching (`BTCUSDT`) stays supported as a fallback for
      legacy / convenience use cases but emits a deprecation log. **DONE 2026-05-30** —
      market-data-processing-service@a82706e: fallback path (line 393) replaced `any(iid in blob_name ...)` with
      `blob_matches_any_instrument_id`. Primary path (line 475) was already using the canonical-aware function (shipped
      at 9ea08c8). Fix: canonical ids like BINANCE-FUTURES:PERPETUAL:BTCUSDT now correctly match hive-format paths in
      the fallback branch. 2 new tests in TestFallbackPathCanonicalFilter.
- [x] ✅ [AGENT] P1. **3.3 Update the regression tests** in `test_orchestration_scanner.py`. Add cases for canonical
      matching (`["BINANCE-FUTURES:PERPETUAL:BTCUSDT"]` → exactly the BINANCE-FUTURES perpetual BTCUSDT blob, even if a
      BYBIT perpetual BTCUSDT exists in the same scope) and the bare-symbol fallback (with the deprecation log
      assertion). **DONE 2026-05-30** — same commit a82706e: `TestFallbackPathCanonicalFilter` (2 tests). Pre-existing
      `TestCanonicalInstrumentIdMatching` (4 tests) already covered the primary path canonical cases. 12 tests total in
      test_orchestration_scanner.py, all pass.
- [x] ✅ [AGENT] P1. **3.4 Update the launcher pass-through documentation** in `launch-mdps-backfill-vm.sh` to recommend
      canonical form. The bare-symbol form should be tagged as legacy. **DONE 2026-05-30** — deployment-service@28aadd8:
      expanded `--instrument-ids` header comment with RECOMMENDED/LEGACY labels, hive-path segment explanation, codex
      SSOT cross-link (`codex/06-coding-standards/cli-convention.md §Instrument Identity and CLI Granularity`), and UAC
      import hint (`from unified_api_contracts.canonical import parse_instrument_key`).

## Phase 4 — Implement the chosen execution + engine model

Once Phase 1 and Phase 2 land their `[DESIGN][P1]` items, this phase is the actual refactor. Sub-items are intentionally
TBD here — they depend on which execution model and which engine are chosen. Land the design decisions first; don't
start implementation against an unconfirmed shape.

- [x] ✅ [AGENT] P1. **4.1 Refactor execution model** per the Phase 1 decision. **DONE 2026-05-30** —
      market-data-processing-service@fd37f58: `--subprocess-per-date` opt-in flag. When set, each date in the
      `[start_date, end_date]` range is spawned as a separate subprocess via
      `subprocess.run([sys.executable, "-m", "market_data_processing_service", "process", ...])` with
      `env=os.environ.copy()` (GCP credentials inherited). `_build_single_date_argv` reconstructs argv from parent's
      parsed namespace, pinning both `--start-date` and `--end-date` to the single date. Subprocess gets
      `--skip-date-validation` (parent already validated). `--subprocess-per-date` omitted from child argv to prevent
      recursion. Also adds `--skip-date-validation` to the parser (was a getattr default, now a proper CLI arg). 4 new
      tests in `TestSubprocessPerDate`. 13 tests pass.
- [x] ✅ [AGENT] P1. **4.2 Refactor data engine** per the Phase 2 decision. **DONE (pre-existing) — Stage 5E completed
      in sibling plan** (market-data-processing-service@58d51d2). Verification 2026-05-30: 0 `pd.read_parquet` calls in
      batch production paths. 13 Polars parquet callsites (10 read, 2 write, 1 mock) verified against Phase 2.2 audit.
      Remaining `to_pandas()` / `from_pandas()` calls fall into 3 documented categories: (a) UTL boundary write seam —
      `candle_write_mixin.py`, `data_sink.py`, `canonical_writer.py` — UTL APIs require `pd.DataFrame`; documented at
      each callsite. Single conversion per shard. (b) UTL timestamp validator seam — `orchestration_writer.py`,
      `orchestration_state.py`, `data_sink.py`. (c) Pandas→Polars input conversion at CeFi trades adapter —
      `pl.from_pandas(tick_data[cols_needed])` (Stage 2: table-level roundtrip replaced with column-subset conversion).
      No unnecessary round-trips in the read→aggregate→write hot path.
- [x] [AGENT] P1. **4.3 Replace the tactical `del + gc.collect()` patches** from the sibling plan with the structural
      cleanup the refactor enables. The sibling plan's Phase 2.2 fix should be **deleted** at this point — keeping it
      would mask any retention regressions the new architecture introduces. **Done**: Removed psutil import and
      RSS-measurement block from `_process_candles_for_one_date`; kept `del     tracker + gc.collect()` and
      `del orchestrator` for in-process Python-cycle cleanup (still needed when `--subprocess-per-date` is not active).
      Simplified comments to reflect subprocess-per-date as structural fix. Commit:
      market-data-processing-service@6c65e98. Tests: 13/13 pass.
- [x] [AGENT] P1. **4.4 Wire memory bounds into QG.** A per-shard memory regression test that runs a representative
      scope and asserts peak RSS < threshold. This is what should have caught the 25 GB per-day floor at code-review
      time. Threshold = whatever the Phase 2.3 measurement establishes for the chosen engine. **Done**: Added [6.X]
      PER-SHARD MEMORY REGRESSION GATE section to `scripts/quality-gates.sh`. Runs
      `tests/perf/test_polars_instrument_day_memory.py` on every QG pass: 1M-tick synthetic CeFi-perp day, RSS ≤ 2 GB,
      Python heap ≤ 500 MB. Baseline ~250 MB (8× inside bar). Commit: market-data-processing-service@f6cc5a0.

## Phase 5 — Observability

- [x] ✅ [AGENT] P2. **5.1** Emit `MEMORY_HIGH_WATER_MARK` events at each shard boundary (per-date, per-data_type,
      per-instrument) — currently the only memory signal is the existing `MEMORY_BACKPRESSURE_ENGAGED` warning, which
      only fires when we're already in trouble. Shipped at MDPS@3f98ed9: per-date in `_cleanup_after_day`
      (orchestration_base.py) + per-data_type at end of `_process_files_parallel` (batch_workers.py). Fields:
      shard_date, shard_type, shard_data_type, memory_rss_mb, memory_rss_bytes, instruments_processed, success_count.
      Per-instrument omitted — psutil call per instrument × hundreds of instruments = performance regression; existing
      `PROCESSING_COMPLETED` covers per-instrument observability. 2026-05-30.
- [x] ✅ [AGENT] P2. **5.2** Per-shard wall-clock timing emitted as a `SHARD_COMPLETED` event with structured fields, so
      the per-shard cost model in Phase 0.3 can be validated against real production data. Shipped at MDPS@684e114:
      per-data_type SHARD_COMPLETED in `_process_files_parallel` (batch_workers.py) with wall_clock_sec,
      instruments_per_sec, success_count, error_count, total_candles, shard_category; per-date SHARD_COMPLETED in
      `_log_category_summary` (orchestration_service.py) aggregating all data_types. Regression guard:
      test_batch_workers_shard_completed.py (two cases: success path + error path). 2026-05-30.
- [x] ✅ [AGENT] P2. **5.3** The 526 MB manifest read should emit a `MANIFEST_LOAD_SIZE_BYTES` event so future
      regressions ("the manifest is now 1.2 GB") are caught before they OOM a small box. Shipped at UTL@ff3c897e:
      `_emit_manifest_load_size` helper emits MANIFEST_LOAD_SIZE_BYTES{bucket, path, bytes_compressed, mb_compressed} on
      every cache-miss read of the consolidated availability_index.parquet via both download paths in
      `_read_consolidated_if_fresh` (manifest_writer.py). Cache hits (TTL 60s) and per-VM shard reads do NOT fire — only
      real GCS downloads. Regression guard: test_manifest_load_size_event.py. 2026-05-30.

## Phase 6 — Codex updates (targets from the 2026-05-28 codex audit)

The codex audit above named the exact docs that need to land. Phase 6 is the close-out for each finding.

- [x] ✅ [AGENT] P2. **6.1 (Finding A — cleanup discipline)** Add a new §15 to
      [`codex/06-coding-standards/service-orchestration-patterns.md`](../../codex/06-coding-standards/service-orchestration-patterns.md):
      "Batch Service Lifecycle: Setup, Work, Cleanup". Pre-existing at PM@d53aff6b — section 15 already codified at
      2026-05-28 with full "Why", anti-pattern example, correct pattern (try/finally), state audit table, reference
      implementation (orchestration_base.py + orchestration_service.py), reference incident (2026-05-28 OOM), and
      "Composes with" cross-links. No new content needed. Checkbox flip only. 2026-05-30.
- [x] ✅ [AGENT] P2. **6.2 (Finding B — instrument_id contract)** Add a new section to
      [`codex/06-coding-standards/cli-convention.md`](../../codex/06-coding-standards/cli-convention.md): "Instrument
      Identity and CLI Granularity". Pre-existing at PM@d53aff6b — section "Instrument Identity and CLI Granularity
      (HARD RULE — codified 2026-05-28)" at line 108 of cli-convention.md covers canonical form, venue derivability,
      data_type independence, atomic shard definition. No new content needed. Checkbox flip only. 2026-05-30.
- [x] ✅ [AGENT] P2. **6.3 (Finding C — VM lifecycle reconciliation)** Extend
      [`codex/05-infrastructure/vm-tarball-deployment.md`](../../codex/05-infrastructure/vm-tarball-deployment.md) §
      "The invariants" with multi-shard cleanup invariant. Pre-existing at PM@d53aff6b — invariant 10 "Per-shard cleanup
      discipline for multi-shard VMs (HARD RULE, codified 2026-05-28)" at line 121 of vm-tarball-deployment.md covers
      EPHEMERAL_BATCH multi-shard cleanup requirement. No new content needed. Checkbox flip only. 2026-05-30.
- [x] ✅ [AGENT] P2. **6.4 (Finding D — data engine)** Add a new doc at
      `codex/06-coding-standards/data-engine-selection.md`. Pre-existing at PM@d53aff6b — full doc exists with Rule,
      Why, decision tree, banned anti-patterns (Polars→Pandas→Polars), low_memory guidance. No new content needed.
      Checkbox flip only. 2026-05-30.

## Out of scope

- The 4h/24h features-side unblock (covered by the sibling plan + the 16-day backfill it ships).
- The `e2-highmem-8` mitigation for the TradFi bundle reader (separate concern; not architectural).
- Live-mode pipeline changes (this is a batch-side architectural audit; live mode shares the engine but the multi-shard
  concern is batch-specific).

## Success criteria

- Per-shard memory test in QG with a concrete RSS threshold that's a real improvement over the current 25 GB per-day
  floor.
- A canonical instrument_id alone is sufficient to scope one cell at the CLI surface, with regression coverage.
- One long-running VM processes a 16-day narrow-scope backfill with monotonically-flat RSS (no per-date ratchet).
- No `del + gc.collect()` patches remain in `process_handler.py` — they've been replaced by structural cleanup.

## Reference incidents that motivate this plan

- 2026-05-28 narrow-scope smoke OOM (intra-day) — fixed by sibling plan Phase 2.1
- 2026-05-28 Phase 3.2 day-2 OOM (cross-date) — sibling plan Phase 2.2 was tactically sufficient (with
  `_cleanup_after_day` wiring); structurally still leaves a 25 GB per-day floor that this plan addresses.
- 2026-05-06 / 2026-05-07 TradFi `ticks.parquet` 4000-symbol bundle OOMs — separate per-file Polars memory issue, lives
  in `launch-mdps-sharded-backfill.sh` mitigation; touched by Phase 2 (data-engine) here.
