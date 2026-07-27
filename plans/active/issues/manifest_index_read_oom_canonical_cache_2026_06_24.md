---
doc_type: issue
title: Manifest _index read OOMs multi-day batch backfills — un-evicted _CANONICAL_CACHE + slow per-VM fan-in merge
summary:
  DeFi MTDS batch backfills (`--mode batch` over a multi-day range) OOM-die (exit_code=137 / SIGKILL) on `e2-standard-4`
  (16GB) — confirmed across EVERY data_type (collect-dex-pools/dex-swaps/lending...
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [manifest, defi, backfill, spot-vm, data-pipeline, performance, single-walk]
related: []
created: 2026-06-24
parent_epic: manifest_master
priority: P2
source:
  [
    plans/active/defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md,
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    unified-trading-library/unified_trading_library/manifest_writer/_state.py,
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

## What I found

DeFi MTDS batch backfills (`--mode batch` over a multi-day range) OOM-die (exit_code=137 / SIGKILL) on `e2-standard-4`
(16GB) — confirmed across EVERY data_type (collect-dex-pools/dex-swaps/lending-indices/ liquidations/perp-funding). The
day-1 captures land, then the process is Killed when starting day-2: memory grows per-date across the BatchPayload
day-loop and is never released.

ROOT CAUSE (code-confirmed):

- Every per-pool `record_captured` (and the per-date preflight + `ManifestFreshnessCache.bulk_load`) calls
  `read_availability_index(bucket)`. When the consolidated canonical index reads STALE, it takes the slow fallback
  `_read_and_merge_per_vm_shards` (`manifest_writer/_read_index.py:429-481`) → `pd.concat(frames)` + `drop_duplicates` +
  `sort_values` (`_writer_io._merge_dataframes`), holding 4-5 simultaneous copies of the full merged index. The code
  itself documents this (`_read_index.py:286-287`): _"per-VM recovery merge can be 12+GB pandas heap on large buckets
  (cefi: 1700+ shards → SIGKILL at startup)."_
- The merged result is cached in process-global `_CANONICAL_CACHE` (`_state.py:111`), and `_invalidate_index_cache`
  (`_state.py:165-166`) **intentionally NEVER evicts it** (a deliberate warm-cache optimisation added for the 2026-05-07
  sports per-date incident — avoids a ~27s canonical re-read per date).
- The DeFi consolidated `_index` is **82MB parquet / ~7M rows × wide v9 schema** → a few GB in pandas; pinned in
  `_CANONICAL_CACHE` for the whole run + per-day transient merge copies layered on top → RSS climbs to OOM. Shared
  manifest-read path ⇒ ALL data_types OOM identically (not handler-specific).

## Why it matters

It blocks every multi-day DeFi (and potentially cefi/tradfi/sports as their indices grow) batch backfill on the default
e2-standard-4. The DeFi capture-to-100% backfill is unblocked OPERATIONALLY by running on e2-highmem-8 (64GB) — the
82MB-index peak fits with headroom — but the default machine + the un-evicted cache is a latent fleet-wide OOM for any
large-index asset_group.

## Recommended decision

Memory-bound the manifest-index cache WITHOUT losing the sports warm-cache optimisation:

- **Option A (lowest-risk)**: in `_invalidate_index_cache` (`_state.py:142-166`), cap `_CANONICAL_CACHE` to the single
  current bucket and `del` the prior bucket's DataFrame on bucket-change — keeps the warm window for the active bucket,
  frees the pinned copy when the process moves on. (For a single-asset-group backfill VM this is a no-op on the warm
  path but bounds the worst case.)
- **Option B (durable)**: make the per-VM fan-in merge (`_read_and_merge_per_vm_shards`) stream/iteratively reduce
  frames (concat in chunks, free as you go) instead of holding all frames + a 4-5× concat spike, so the slow path itself
  never needs 12+GB.
- **Option C (config mitigation, already applied)**: DeFi launchers set `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` so
  the fast path (consolidated + own self-shard only) is taken — but once the slow path fires the un-evicted cache pins
  the result regardless, so A/B is the durable fix.

Cross-cutting (touches the LIVE cefi/sports/tradfi manifest path) → validate carefully; NOT blocking the DeFi backfill
(highmem unblocks it). Owner: a UTL/manifest slot. parent epic: manifest_master (corrected 2026-07-12 per operator
ruling, finding 134 — frontmatter was right; charter match: manifest machinery → manifest_master; was written as
"mtds_mdps_master" — that was the error, not the frontmatter).
