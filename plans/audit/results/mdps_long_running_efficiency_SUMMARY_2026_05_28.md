---
type: audit-findings-summary
title: MDPS long-running efficiency audit — synthesis
epic: mtds_mdps_master
auditor: claude opus 4.7 (slot main)
date: "2026-05-28"
status: complete
name: mdps_long_running_efficiency_SUMMARY_2026_05_28
audit_instructions: mtds_mdps_master_audit_instructions.md
parent_plan: mdps_long_running_multi_shard_architecture_audit_2026_05_28.md
---

# MDPS long-running efficiency audit — synthesis

Operator-readable rollup of the 7 findings docs landed 2026-05-28. Each section names the doc, the one-line headline,
and the one-line recommended action. Read this first; deep-dive into the individual docs when you need file:line
evidence.

## Empirical anchor

Phase 3.2 canary retry (e2-standard-8, 32 GB, MAX_WORKERS=1, 4 instruments × 2 venues × trades × all 7 timeframes):

| Run                                        | Day 1 outcome | Post-day-1 RSS                       | Day 2 outcome                         |
| ------------------------------------------ | ------------- | ------------------------------------ | ------------------------------------- |
| Attempt 1 (no `_cleanup_after_day` wiring) | 28/28 outputs | **25.1 GB**                          | Hung on transition; OOM ~38 min later |
| Attempt 2 (cleanup wired at MDPS@dcd7416)  | 28/28 outputs | **15.7 GB** (9.4 GB reclaimed, ~38%) | Same silent pattern; manually stopped |

The cleanup hook is the right shape and pulls ~9 GB. The remaining ~15 GB residue is in places Python-level cleanup
cannot reach — primarily Polars/PyArrow arenas + the orchestrator's structural state choices.

## The 7 findings (one row each)

| #   | Doc                                                                  | Headline                                                                                                                                                                                                                                                                 | Recommended action                                                                                                                                                                                                                         |
| --- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | [`state_inventory`](mdps_long_running_state_inventory_2026_05_28.md) | 12-row state-inventory table; cleanup hook fires on every exit path (✓); ~15 GB residue most likely lives in Polars/PyArrow arenas that `gc.collect()` cannot reach.                                                                                                     | **Immediate**: short list of attrs to add to `_cleanup_after_day`'s reach. **Architectural**: subprocess-per-date or process-pool.                                                                                                         |
| 2   | [`engine_mixing`](mdps_long_running_engine_mixing_2026_05_28.md)     | `_read_tick_data` allocates 4 independent buffers per instrument via Polars→Pandas→Polars chain; arenas never reclaim. **Likely majority owner of the 15.7 GB floor.**                                                                                                   | **Immediate**: pure-Polars `_read_tick_data` prototype (3-line scope). **Architectural**: workspace-wide single-engine discipline per the new codex doc.                                                                                   |
| 3   | [`cli_granularity`](mdps_long_running_cli_granularity_2026_05_28.md) | Canonical instrument_id `VENUE:INSTRUMENT_TYPE:SYMBOL` returns **zero blobs** today — substring matcher mismatches blob paths' `=` separator. Silent failure contradicts the codex contract.                                                                             | **Immediate**: 2-line parser replacement at `_collect_matching_parquet_blobs`. **Architectural**: workspace-wide canonical parser + UAC `VENUES_BY_ASSET_GROUP` reverse lookup.                                                            |
| 4   | [`manifest_io`](mdps_long_running_manifest_io_2026_05_28.md)         | Orchestrator double-reads the **526 MB** `availability_index.parquet` per shard (primary + per-timeframe re-check). 32–80 GB of allocate-then-free churn per 16-day backfill.                                                                                            | **Immediate**: reuse the manifest DataFrame from the first check at `orchestration_service.py:166-211`. **Architectural**: read-once-at-VM-start + per-shard incremental check; DuckDB-style memory-bounded read for very large manifests. |
| 5   | [`concurrency`](mdps_long_running_concurrency_2026_05_28.md)         | Cost-model table for the 4 candidate execution shapes (subprocess-per-date / subprocess-per-shard / in-process / process-pool). Current in-process shape empirically unreliable beyond ~1-2 days on 32 GB; subprocess-per-date is the lowest-risk pivot.                 | **Architectural**: feeds directly into the architectural plan's Phase 1.1 decision. No immediate change.                                                                                                                                   |
| 6   | [`observability`](mdps_long_running_observability_2026_05_28.md)     | Existing memory telemetry is reactive (`MEMORY_BACKPRESSURE_ENGAGED` at 85%, already-in-trouble signal). Missing per-shard structured events would have predicted the Phase 3.2 day-2 OOM ~5 minutes before it happened.                                                 | **Immediate**: 6 structured event proposals (`SHARD_STARTED`, `SHARD_COMPLETED`, `MANIFEST_LOAD_BYTES`, etc.); ~1h of code. **Architectural**: SLO dashboard + per-shard memory regression test in QG.                                     |
| 7   | [`axes_e_g_h`](mdps_long_running_axes_e_g_h_2026_05_28.md)           | (E) Pre-count log misleads operators ("Listed 18" vs "Listed 4"); 2-line fix. (G) `_iter_chain_symbol_dfs` is the architecturally-correct streaming pattern other code paths should emulate. (H) All 21 adapters are stateless — adapter caches are NOT the 25 GB owner. | **Immediate** (E): pass `instrument_ids=` to pre-count. **Architectural** (G): use streaming pattern as model for bundle reader. (H) closes the adapter hypothesis.                                                                        |

## What the cumulative evidence says about the 15 GB residue

Cross-referencing the 7 docs:

- Adapter-side caches: **NOT the owner** (H confirmed all 21 stateless).
- Orchestrator instance state (`_data_sinks`, `_storage_client`, instruments DataFrame): partially owns it; the
  state-inventory's table flags 4 specific attributes as candidates for cleanup-hook extension.
- Per-shard double manifest read: contributes ~32-80 GB of cumulative allocate-then-free churn over a 16-day run — much
  of which IS reclaimed (the manifest decompress is local and short-lived), but the high-water mark IS proportional to
  per-call decompression.
- **Polars/PyArrow arena retention** (Finding 2): the structural finding. Arenas are not visible to Python's GC. Even
  after `del`, the underlying arrow buffer stays in the arena. `pyarrow.default_memory_pool().release_unused()` is the
  only Python-level release primitive, and MDPS does not call it. This is the most likely majority owner.
- 4128-instrument reference DataFrame: small in absolute terms (~10-100 MB) but exercises pandas allocator each date.
  Cumulative impact unclear; verify with tracemalloc.

## Recommended sequence for the architectural audit's Phase 1

Driven by what these 7 docs surfaced:

1. **Phase 1.1 execution-model decision**: subprocess-per-date is the operationally cheapest fix for the arena problem.
   Doc 5 lays out the cost-model evidence; doc 2 makes the case for why arena reclaim cannot be solved at the Python
   layer.
2. **Phase 2.1 data-engine decision**: pure Polars. Doc 2 makes the case empirically; doc 7 axis G provides the
   reference implementation (`_iter_chain_symbol_dfs`).
3. **Phase 3.1 CLI parser fix**: doc 3 gives the 2-line replacement + the cross-service surface that needs the same fix.
4. **Phase 0.3 cost model input**: doc 4 gives the manifest-read cost per shard; doc 5 gives the per-shape startup cost.
5. **Phase 5 observability**: doc 6 gives the 6 structured-event proposals + SLO + dashboard recipe.

## Cross-codex alignment

All 7 findings are consistent with the four codex docs landed 2026-05-28:

- [`codex/06-coding-standards/service-orchestration-patterns.md`](../../codex/06-coding-standards/service-orchestration-patterns.md)
  § 15 — referenced by findings 1, 7.
- [`codex/06-coding-standards/cli-convention.md`](../../codex/06-coding-standards/cli-convention.md) "Instrument
  Identity" — finding 3 is the implementation-side audit of this contract.
- [`codex/05-infrastructure/vm-tarball-deployment.md`](../../codex/05-infrastructure/vm-tarball-deployment.md) invariant
  #10 — referenced by finding 5.
- [`codex/06-coding-standards/data-engine-selection.md`](../../codex/06-coding-standards/data-engine-selection.md) —
  finding 2 is the implementation-side audit.

No codex contradictions surfaced — these are gap-fills + first audits against newly-codified rules.

## What this audit does NOT cover

- Live-mode pipeline changes. This is a batch-side audit.
- The TradFi `ticks.parquet` 4000-symbol bundle OOM. Mitigation already documented in `launch-mdps-sharded-backfill.sh`;
  the architectural audit's Phase 2 (data engine) will subsume.
- Cost/billing details. The execution-model trade-offs in doc 5 are in wall-clock + memory + reliability terms, not
  dollars.
- The 14-day backfill run currently in flight elsewhere — that ships the features-side unblock without depending on
  Phase 3 of the sibling tactical plan, per operator direction.
