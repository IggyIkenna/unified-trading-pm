---
doc_type: issue
title:
  ManifestWriter per-VM shard flush cost scales with existing shard size, defeating the debounce once a shard passes ~1M
  rows
summary:
  A backfill VM's per-VM manifest shard write path does a full read-merge-reserialize-upload of the WHOLE shard on every
  debounced flush (O(existing-size), not O(new-rows)); once a shard passes ~1M rows the flush itself takes longer than
  the debounce interval, so the debounce is defeated and the VM stalls making near-zero forward progress while still
  looking healthy (high CPU, no errors, regular heartbeats).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer]
tags: [manifest-writer, performance, backfill, scalability, per-vm-shard]
related: [defi_dex_pool_symbol_fix_backfill_purge_2026_07_25]
created: 2026-07-28
author: unknown
parent_epic: security_and_cross_cutting_master
priority: P2
assigned_vm: NA
resolved_by:
locked_by:
context_scope:
  [
    unified-trading-library/unified_trading_library/manifest_writer/_writer_io.py,
    unified-trading-library/unified_trading_library/manifest_writer/_state.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py,
    /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
source:
  [
    "found while working todo 4 of /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md (the
    curve/sushiswap/velodrome_v2/trader_joe_v2 dex_pool_state re-backfill)",
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# ManifestWriter per-VM shard flush cost scales with existing shard size

## What I found

Backfill VM `mtds-dex-pools-symbolfix-batch1` (4th relaunch of todo 4's backfill, on-demand,
`--start 2025-04-02 --end 2026-07-27 --protocols curve,sushiswap,trader_joe_v2`) stalled for 35+ minutes after
completing only its FIRST day (2025-04-02) of a ~480-day remaining range. Directly verified (not inferred from logs
alone) via `pandas.read_parquet` on the actual
`gs://market-data-tick-defi-prd-central-element-323112/_index/per_vm/mtds-dex-pools-symbolfix-batch1.parquet` shard:
total row count stayed at EXACTLY `1196916` across the entire stall window, while the run.log repeated
`ManifestWriter: per-VM shard updated (1196916 total entries, 1 new, process_final=False)` every ~12 seconds.
`strace -c` on the live PID showed 83% of syscall time in `futex` (thread/GC contention), CPU pinned 100-130%, RSS
1.7-3.8GB, no errors, no new day-processing log lines.

**Root cause** (`unified_trading_library/manifest_writer/_writer_io.py:694-783`,
`_write_per_vm_shard`/`_flush_per_vm_pending`): the per-VM shard write path stages new rows into a module-level pending
buffer and is supposed to debounce the expensive full-shard rewrite to at most once per `manifest_per_vm_flush_entries`
(50) OR `manifest_per_vm_flush_interval_sec` (5.0), whichever first (`_state.py:246-280`). But the rewrite itself
(`_flush_per_vm_pending`, lines 757-773) does a full **read-merge-reserialize-upload of the ENTIRE existing per-VM
shard** on every flush — an O(existing shard size) operation, not O(new rows). Once a per-VM shard accumulates past
roughly 1M rows (this one had inherited ~1.2M rows from 3 prior preempted incarnations of the SAME `VM_NAME`, per the
parent plan's own Progress Log), a single flush round-trip takes longer than the 5-second debounce interval. That means
the debounce can never actually accumulate a batch — every flush ends up draining only ~1 pending row (matching the
observed `1 new` in every log line), paying the full O(N) cost for essentially one row at a time.

This DeFi dex_pools handler makes it much worse than typical manifest writers because it emits a per-pool "empty"
manifest marker for every catalogue pool a day's subgraph query returned no data for
(`market_tick_data_service/cli/handlers/_dex_swaps_queries.py:241-254`, `_dex_pools_subgraph.py:799-815`) — up to ~384
pools for curve/ETHEREUM and ~294 for trader_joe_v2/AVALANCHE in a single day, each going through
`DefiManifestRecorder.record_empty` → `ManifestWriter.add()` individually. `DefiManifestRecorder` intentionally sets
`batch_size=1` (`market_tick_data_service/cli/handlers/_defi_manifest.py:129-134`, documented as matching "the
orchestrator's at-least-one-complete-shard persistence discipline under mid-run SIGKILL") so every single
`record_empty`/`record_captured` call is an independent `write()` attempt into the debounced per-VM path.

**Verified NOT the cause**: no deadlock, no infinite retry loop, no missing timeout on the subgraph fetch itself (that
path already has a 300s per-shard ceiling). The stall is a genuine architectural cost-scaling bug in the manifest-writer
flush path, confirmed via direct read of the parquet shard (not just log inference) plus `strace`/`ss` process
inspection on the live VM.

## Why it matters

Any sufficiently long-running backfill VM that reuses a `VM_NAME` across preemption-recoveries (the documented, intended
recovery pattern per `/codex/05-infrastructure/vm-launcher-runbook.md`) will eventually accumulate a large per-VM shard
and hit this same wall — this is not unique to DeFi dex_pools, though DeFi's per-pool empty-marker density made it
surface fast (~1.2M rows reached well before the 480-day range this todo needs was even half done). Left unfixed, any
backfill touching a similarly dense per-pool/per-day manifest grain will silently stall for the same reason, burning
on-demand/SPOT compute for near-zero throughput while LOOKING alive (healthy CPU, no errors, regular heartbeats) —
exactly the "logged + heartbeated healthily while making zero real progress" failure class the workspace's async-wait
discipline warns about.

## What I did (mitigation, not a fix)

Killed the stalled VM and relaunched the remaining range under a FRESH `VM_NAME` (`mtds-dex-pools-symbolfix-batch1c`),
so its own per-VM shard starts empty rather than inheriting the 1.2M-row backlog. This is a normal, safe pattern (per-VM
shards are plural by design, consolidated centrally later) and unblocks the immediate todo, but it is NOT a fix — this
new VM's own shard will eventually grow large again over its ~480-day range and could hit the same wall partway through,
just delayed rather than avoided. Todo 4 in the parent plan tracks watching this relaunch to completion.

## Recommended decision

The actual fix belongs in shared `unified-trading-library` code (`manifest_writer/_writer_io.py`), not DeFi-specific
code, since the debounce mechanism itself is what's defeated at scale. Candidate directions (the todos below name the
investigation + design work, not a pre-committed implementation, since this is a shared-infra performance change needing
its own review):

- [ ] [BACKEND] P2. Investigate an append-only "delta shard" pattern for the per-VM manifest write path
      (`unified_trading_library/manifest_writer/_writer_io.py`) — write new rows to a small, cheap delta file per flush
      instead of rewriting the whole shard, with periodic (or close()-time) compaction into the canonical per-VM
      parquet. Must preserve the existing SIGKILL-durability guarantee (no entry lost on a hard kill) and not regress
      the small-shard case. (repo: unified-trading-library)
- [ ] [BACKEND] P3. **(reworded 2026-08-19, `/plan-reconcile security_and_cross_cutting_master` Phase 1 — line-1
      completeness fix; content unchanged, action moved to line 1, dated annotation moved after)** As a cheaper
      interim alternative to the P2 delta-shard todo above, investigate making the per-VM flush debounce
      entries-threshold dominant over the interval-threshold once the existing shard exceeds some size (e.g. skip
      the 5s time-based trigger and require a real entry-count batch once the shard is large), so large shards get
      bigger, less-frequent batches instead of constant small ones. Note this trades durability under SIGKILL for
      throughput — needs an explicit call on whether that tradeoff is acceptable, not a default flip.
      **round5-cross-cutting-audit 2026-08-08 note**: durability-vs-throughput defaults to preserving durability per
      CLAUDE.md's "data pipeline correctness is the heartbeat" HARD RULE + the P2 todo above already requiring the
      SIGKILL-durability guarantee; pursue P2 first, leave this tradeoff unimplemented absent an explicit ask.
      (repo: unified-trading-library)
- [ ] [SCRIPT] P3. Once either fix above ships, verify against a synthetic large per-VM shard (~1M+ rows) that flush
      latency no longer scales linearly with existing shard size, and add a regression test guarding it. (repo:
      unified-trading-library)

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the doc states its todos 'name the investigation + design work,
  not a pre-committed implementation, since this is a shared-infra performance change needing its own review', and the
  P3 alternative needs an explicit durability-vs-throughput tradeoff call.

- **na-eligibility-audit 2026-08-03 (cross-cutting tranche)**: KEEP-NA, valid — reaffirmed, unchanged. Today's edit that
  put this doc back in incremental scope was a cosmetic `context_scope`/reference-path-repointing commit, not a content
  change to the 3 open todos; the 2026-07-30 rationale (shared-infra concurrency-critical performance design work,
  needing its own review) still holds.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — reviewed against current doc content, list still
  accurate (unchanged).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-03 (unchanged): all 3 open todos are
  shared-infra concurrency-critical performance-design investigation/tradeoff work, not pre-committed implementation.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- reaffirms 2026-08-06 (unchanged): all
  3 open todos are shared-infra concurrency-critical performance-design investigation/tradeoff work (the P3 alternative
  explicitly needs an explicit durability-vs-throughput call per its own round5-cross-cutting-audit 2026-08-08
  annotation), not pre-committed implementation.

- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-17** [body-hash:552ffed4150d81ba]: KEEP-NA, valid -- Reaffirmed KEEP-NA 4x (2026-07-30, 08-03, 08-06, 08-08 round7 RECLASSIFY sweep) -- survived an explicit RECLASSIFY sweep. The fix belongs in shared unified-trading-library manifest-writer code (used by every backfill VM fleet-wide) with an explicit SIGKILL-durability-preservation constraint; the P3 alternative explicitly trades durability for throughput and 'needs an explicit call on whether that tradeoff is acceptable, not a default flip'; the verification todo is sequenced after either fix ships.
- **context-scout 2026-08-17**: refreshed context_scope (5 entries), unchanged.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — 3 open todos — shared-infra (unified-trading-library manifest-writer) performance-design investigation/tradeoff work with an explicit SIGKILL-durability-preservation constraint; reaffirmed KEEP-NA 5x.
- **context-scout 2026-08-20**: refreshed context_scope (5 entries).
