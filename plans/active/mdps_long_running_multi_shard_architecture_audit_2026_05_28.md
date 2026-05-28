---
name: mdps_long_running_multi_shard_architecture_audit
title: "MDPS architectural audit — long-running multi-shard execution (2026-05-28)"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
status: active
priority: P1
created: 2026-05-28
author: harsh (claude opus 4.7) — slot main, captured operator direction
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
related:
  - mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md
locked_by: live-defi-rollout
locked_since: 2026-05-28
---

# MDPS architectural audit — long-running multi-shard execution

## Why this plan exists

The 2026-05-28 filter-pushdown plan
([`mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`](mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md))
landed three tactical fixes (scanner filter, cross-date `del + gc.collect()`, `_cleanup_after_day` wiring) that
together let an `e2-standard-8` VM complete a multi-day narrow-scope backfill. But the symptoms those fixes had to
work around — 25 GB per-day high-water mark, cross-date retention, repeated 526 MB manifest reads, Polars/Pandas
conversion churn — are not isolated bugs. They are consequences of running a fan-out-shaped codebase as a long-
running multi-shard worker. The orchestrator was designed under the assumption that each VM processes ONE shard
(one day × one venue × one asset_group × one data_type); the deployment model has since pivoted to a small number
of long-running VMs that each cover many shards. The two assumptions are incompatible and the tactical fixes do
not close the gap.

This plan is the architecture-level audit + refactor track. It is **not** in the critical path for the
2026-05-23 live-DeFi cutover or the immediate 4h/24h features-side unblock — those are handled by the tactical
fixes in the sibling plan. This plan exists so that the long-running execution mode is properly engineered after
the live-DeFi cutover, not patched indefinitely.

## Scope

Concrete questions to answer + corresponding redesigns to ship:

1. **What is the right execution unit?** Subprocess-per-date? Subprocess-per-shard? In-process with proper
   cleanup? Process-pool worker model? Each option has different cost/reliability/observability trade-offs.
2. **What state belongs to the orchestrator vs the worker vs the per-shard task?** The current orchestrator
   conflates all three. Cleanup is hard because the boundaries are blurred.
3. **Why does MDPS read the full 526 MB manifest at each per-date startup?** Is there a partial-read path? Can the
   manifest be lazy / streaming? Can the freshness check use a small index instead of the full manifest?
4. **Why is data passed Polars → Pandas → Polars → Pandas?** Pick one engine, end-to-end. Polars is the more
   obvious choice because aggregation is already there. Eliminate the conversion buffers.
5. **What is the right granularity for the CLI?** A single canonical instrument_id should be sufficient to scope
   one cell. Today the CLI claims that but the filter logic does substring matching on raw symbols.
6. **How do we test memory bounds?** The current QG has no per-shard memory test. The `_cleanup_after_day` hook
   exists but was untested for ~years because no test exercised the cross-date loop. Memory regressions need
   tooling to catch.

## Phase 0 — Frame the problem (no code edits)

- [ ] [AUDIT][P1] **0.1 Inventory the current fan-out assumptions baked into the code.** Find every place where
  the orchestrator constructs per-instance state that would be redundant for the next shard / next date. Examples
  (preliminary, surfaced by the sibling plan): lazy `_storage_client`, per-asset_group `_data_sinks` dict, the
  4128-instrument reference DataFrame, the freshness-check manifest read. Tabulate with `(field, owner, lifetime,
  reset_cost)`.
- [ ] [AUDIT][P1] **0.2 Inventory caches and their cleanup paths.** Beyond the `candle_processing_service` /
  `sampling_service` caches that `_cleanup_after_day` knows about — what other module-level or singleton state
  exists? `unified_trading_library` data sinks, the `ResourceProfiler`, event sinks, polars/pyarrow arenas.
  Where is each cache's `clear()` / `dispose()` method, and is anything calling it?
- [ ] [AUDIT][P1] **0.3 Document the cost model**. What does one VM-hour cost? What does N parallel small VMs
  cost vs one long-running VM for the same work? This frames whether "subprocess-per-date" inside one VM is
  meaningfully cheaper than 16 × 1-day VMs, and whether subprocess-per-shard is cost-feasible.
- [ ] [AUDIT][P1] **0.4 Granularity contract**. Document the canonical instrument_id form and the asset_group /
  venue / instrument_type / data_type axes. State which axes are derivable from instrument_id and which are
  independent. This becomes the input spec for redesigning the CLI filter logic.

## Phase 1 — Decide the execution-unit shape

- [ ] [DESIGN][P1] **1.1 Choose the execution model.** Closed set:
  - **(a) Subprocess-per-date**: `process_candles_handler` invokes `subprocess.run([sys.executable, "-m", ...])`
    per date. Kernel reclaims the address space at exit; no in-process accumulation possible.
  - **(b) Subprocess-per-shard**: same idea, finer grain (per date × per data_type × per venue). Higher fork
    overhead, lower per-process footprint.
  - **(c) In-process with proper cleanup**: trust that `_cleanup_after_day` + arena drops + `malloc_trim(0)` can
    keep the per-day floor flat. Requires solving the Polars/PyArrow arena retention problem.
  - **(d) Process-pool worker model**: long-running parent process holds the manifest + reference data, dispatches
    per-shard work to a `concurrent.futures.ProcessPoolExecutor`. Workers do isolated work, no accumulation.
  Pick one. Document trade-offs explicitly. Sibling-plan empirical data: Phase 3.2 attempt-2 proved (c) is
  unreliable on a 32 GB box even with cleanup-hook wiring; that drives the case for (a) / (b) / (d).
- [ ] [DESIGN][P1] **1.2 Map state ownership to the chosen execution model.** Which state lives in the long-
  running parent (manifest? reference data? auth sessions?) and which lives in the per-shard worker (tick
  DataFrame, candle accumulators)? This is the foundation for any refactor that follows.

## Phase 2 — Decide the data-engine shape

- [ ] [DESIGN][P1] **2.1 Pick the data engine.** Closed set:
  - **(a) Pure Polars end-to-end**: read raw via polars, aggregate via polars (already partially in place), write
    via polars. Pandas eliminated.
  - **(b) Pure Pandas with pyarrow engine**: `pd.read_parquet(engine="pyarrow")`. Eliminates polars but loses
    polars' faster aggregation path.
  - **(c) Pyarrow-table end-to-end**: lowest-level, most explicit memory control, fewer high-level conveniences.
  Pick one. The expectation per operator direction is (a). Document why.
- [ ] [DESIGN][P1] **2.2 Audit every parquet read/write callsite in MDPS.** Tabulate `(file:line, engine, why)`.
  Any mixed-engine boundary is a candidate conversion buffer that the refactor must eliminate.
- [ ] [DESIGN][P1] **2.3 Measure the per-instrument peak memory for the chosen engine.** Run one instrument-day
  through the chosen engine, take a tracemalloc snapshot at peak. Compare against the current mixed-engine peak.
  The bar: per-instrument peak ≤ 2 GB for a typical CeFi perp trades day. (Numbers from the canary suggest the
  current mixed-engine peak is ~7-8 GB per instrument-day; the bar should be a real improvement, not parity.)

## Phase 3 — Fix the CLI granularity (closes Finding B from the sibling plan)

- [ ] [DESIGN][P1] **3.1 Define the canonical instrument_id parser.** A canonical id is
  `VENUE:INSTRUMENT_TYPE:SYMBOL`. Given a list of canonical ids, the scanner can derive the venue set + the
  instrument_type set + the symbol set, and filter blob paths on each axis independently. Document the parser
  spec in UAC (it likely belongs there as a shared utility; check `unified_api_contracts.canonical.*` for an
  existing parser before adding one).
- [ ] [P1] **3.2 Replace the substring filter in `_collect_matching_parquet_blobs`** with a structured check
  derived from the parsed canonical id. Each blob path is matched on (venue, instrument_type, symbol) extracted
  from the path, against the per-axis derived sets. Bare-symbol matching (`BTCUSDT`) stays supported as a
  fallback for legacy / convenience use cases but emits a deprecation log.
- [ ] [P1] **3.3 Update the regression tests** in `test_orchestration_scanner.py`. Add cases for canonical
  matching (`["BINANCE-FUTURES:PERPETUAL:BTCUSDT"]` → exactly the BINANCE-FUTURES perpetual BTCUSDT blob, even if
  a BYBIT perpetual BTCUSDT exists in the same scope) and the bare-symbol fallback (with the deprecation log
  assertion).
- [ ] [P1] **3.4 Update the launcher pass-through documentation** in `launch-mdps-backfill-vm.sh` to recommend
  canonical form. The bare-symbol form should be tagged as legacy.

## Phase 4 — Implement the chosen execution + engine model

Once Phase 1 and Phase 2 land their `[DESIGN][P1]` items, this phase is the actual refactor. Sub-items are
intentionally TBD here — they depend on which execution model and which engine are chosen. Land the design
decisions first; don't start implementation against an unconfirmed shape.

- [ ] [P1] **4.1 Refactor execution model** per the Phase 1 decision.
- [ ] [P1] **4.2 Refactor data engine** per the Phase 2 decision.
- [ ] [P1] **4.3 Replace the tactical `del + gc.collect()` patches** from the sibling plan with the structural
  cleanup the refactor enables. The sibling plan's Phase 2.2 fix should be **deleted** at this point — keeping
  it would mask any retention regressions the new architecture introduces.
- [ ] [P1] **4.4 Wire memory bounds into QG.** A per-shard memory regression test that runs a representative
  scope and asserts peak RSS < threshold. This is what should have caught the 25 GB per-day floor at code-review
  time. Threshold = whatever the Phase 2.3 measurement establishes for the chosen engine.

## Phase 5 — Observability

- [ ] [P2] **5.1** Emit `MEMORY_HIGH_WATER_MARK` events at each shard boundary (per-date, per-data_type,
  per-instrument) — currently the only memory signal is the existing `MEMORY_BACKPRESSURE_ENGAGED` warning,
  which only fires when we're already in trouble.
- [ ] [P2] **5.2** Per-shard wall-clock timing emitted as a `SHARD_COMPLETED` event with structured fields,
  so the per-shard cost model in Phase 0.3 can be validated against real production data.
- [ ] [P2] **5.3** The 526 MB manifest read should emit a `MANIFEST_LOAD_SIZE_BYTES` event so future regressions
  ("the manifest is now 1.2 GB") are caught before they OOM a small box.

## Phase 6 — Codex updates

- [ ] [P2] **6.1** Update or replace
  [`codex/04-architecture/batch-live-architecture.md`](../../codex/04-architecture/batch-live-architecture.md)
  to reflect the chosen execution model.
- [ ] [P2] **6.2** If the data-engine decision in Phase 2 lands at "pure Polars", add a codex coding-standard
  doc to enforce it across the workspace (other batch services have the same Polars/Pandas mixing pattern; this
  rule generalises).
- [ ] [P2] **6.3** Document the canonical instrument_id parser spec from Phase 3.1 in
  `codex/02-data/` (alongside the existing schema-placement guidance).

## Out of scope

- The 4h/24h features-side unblock (covered by the sibling plan + the 16-day backfill it ships).
- The `e2-highmem-8` mitigation for the TradFi bundle reader (separate concern; not architectural).
- Live-mode pipeline changes (this is a batch-side architectural audit; live mode shares the engine but the
  multi-shard concern is batch-specific).

## Success criteria

- Per-shard memory test in QG with a concrete RSS threshold that's a real improvement over the current 25 GB
  per-day floor.
- A canonical instrument_id alone is sufficient to scope one cell at the CLI surface, with regression coverage.
- One long-running VM processes a 16-day narrow-scope backfill with monotonically-flat RSS (no per-date
  ratchet).
- No `del + gc.collect()` patches remain in `process_handler.py` — they've been replaced by structural cleanup.

## Reference incidents that motivate this plan

- 2026-05-28 narrow-scope smoke OOM (intra-day) — fixed by sibling plan Phase 2.1
- 2026-05-28 Phase 3.2 day-2 OOM (cross-date) — sibling plan Phase 2.2 was tactically sufficient (with
  `_cleanup_after_day` wiring); structurally still leaves a 25 GB per-day floor that this plan addresses.
- 2026-05-06 / 2026-05-07 TradFi `ticks.parquet` 4000-symbol bundle OOMs — separate per-file Polars memory
  issue, lives in `launch-mdps-sharded-backfill.sh` mitigation; touched by Phase 2 (data-engine) here.
