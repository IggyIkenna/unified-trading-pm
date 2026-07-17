---
doc_type: issue
title:
  Consolidator silently reaps unmerged per-VM shards when an out-of-band index write strips the content-write marker
summary:
  An out-of-band rewrite of _index/availability_index.parquet that does not preserve the custom metadata destroys
  consolidator_content_write_at. _get_content_write_mtime then falls back to blob.updated — the out-of-band write's OWN
  mtime — which advances the prune cutoff PAST pending per-VM shards. The next consolidator run deletes those shards
  without merging them and reports success=True / exit(0) / rows_in=0. Fired for real on 2026-07-17 and destroyed 7,185
  sports manifest rows (recovered in-band from a pre-merge download). Affects EVERY asset_group, not just sports.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, consolidator, data-correctness, silent-data-loss, per-vm-shards, gcs]
related:
  [
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ../../../codex/02-data/availability-manifest-and-data-status.md,
    ../../../codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    sports legacy bucket cutover Phase 6 / T6.1 execution 2026-07-17,
    consolidator exec uts-prod-manifest-consolidator-instruments-sports-4rfp4,
  ]
---

# Consolidator silently reaps unmerged per-VM shards after an out-of-band index write

> **Severity: P0 / silent data loss.** The failure mode is a **successful-looking run**: `success=True`, `exit(0)`,
> `rows_in=0`, shards gone. Nothing alerts. It is caught only by someone who counted the rows BEFORE and AFTER.

## What happened (measured, 2026-07-17)

Executing T6.1 of the sports legacy bucket cutover — merging two pending per-VM shards into the canonical instruments
index — the first consolidator run (`uts-prod-manifest-consolidator-instruments-sports-4rfp4`, 01:34:31Z) logged:

```
manifest-consolidator bucket=instruments-store-sports-prd-central-element-323112
  success=True shards=3 rows_in=0 rows_out=0 dedup_dropped=0 pruned_shards=2 latency_ms=9449.3 error=-
ManifestConsolidator: pruned 2 consolidated per-VM shard(s)
  (cutoff=2026-07-16T18:45:21.846000+00:00, 2 eligible)
```

Both pending shards (`cutover-move-20260716.parquet` 7,183 rows; `or9-recover-20260716.parquet` 2 rows) were **deleted
without being merged**. The index was byte-identical afterwards (5,342,265 rows, delta 0). GCS retained **no**
noncurrent versions (`gcloud storage ls -a` on `_index/per_vm/` → only `_legacy_seed.parquet`). **7,185 manifest rows
describing 92,722+ real moved objects were destroyed by a run that reported success.**

Recovery was possible ONLY because the executing agent had downloaded both shards minutes earlier to measure the
expected deltas. Had it trusted the plan's expected numbers instead of deriving its own, the loss would have been
permanent and silent.

## Root cause

`unified_trading_library/manifest_consolidator.py`:

1. **`_prune_consolidated_shards` (`:1751-1782`)** deletes a shard iff `mtime <= cutoff`, where
   `cutoff = content_write_marker − _INCREMENTAL_SKEW_SECONDS (5s)`. Its stated invariant:

   > the marker carries the last real merge's SHARD-LISTING start time … so mtime `<= cutoff` proves the shard was
   > visible to that merge's listing — either merged as "changed" or already settled from an earlier cycle. Its data is
   > therefore provably in the canonical and the shard is redundant.

   This is sound — **but only if the marker was written by an actual merge.**

2. **`_get_content_write_mtime` (`:1617-1666`)** resolves the marker with a fallback chain:

   ```
   consolidator_content_write_at  →  consolidator_run_at  →  blob.updated
   ```

   documented as safe:

   > The fallback is SAFE: it can only make the cutoff OLDER (or equal), never newer, so it over-includes shards
   > (re-merge) rather than under-includes (silent drop) — fail toward correctness.

3. **That safety argument does not hold.** It assumes `blob.updated` is a proxy for "when a merge last wrote content" —
   true for a legacy canonical never touched by anything else. But **any out-of-band writer** that rewrites
   `_index/availability_index.parquet` without preserving custom metadata does two things at once:
   - **strips** `consolidator_content_write_at` (custom metadata is not carried by a plain rewrite), and
   - **bumps** `blob.updated` to now.

   The fallback then reads the out-of-band write's OWN mtime as if it were a merge's shard-listing time. The cutoff
   jumps **forward**, past shards no merge ever saw ⇒ **silent drop** — precisely the outcome the docstring claims is
   impossible. It fails toward DATA LOSS, not correctness.

### Forensic proof of the strip

Backups made by the cutover (`gcloud storage cp` preserves custom metadata) bracket the event:

| object                                              | as of                                   | `consolidator_content_write_at` |
| --------------------------------------------------- | --------------------------------------- | ------------------------------- |
| `availability_index.20260716-080453.precutover.bak` | 08:05Z (pre-purge)                      | `2026-07-16T06:36:46Z` (real)   |
| `availability_index.20260717-012712.pre_t6_1.bak`   | 01:27Z (post-purge, post-18:45 rewrite) | **`metadata: None`**            |

The T3.1 purge (13:09Z) and the 18:45:26Z byte-equivalent rewrite each rewrote the index out-of-band; the marker did not
survive. Fallback → `blob.updated` = 18:45:26.846Z → cutoff = **18:45:21.846Z** (exactly the logged value) → both shards
(12:46:09Z, 17:30:42Z) eligible → reaped.

**The poisoning agent was the "frozen-generation witness" itself** (`generation=1784227526828259`, the 18:45:26Z
rewrite). It was recorded as proof the index was quiet and unchanged — and it was, at the ROW layer. At the METADATA
layer it had armed a shard reaper.

## Blast radius

**Not sports-specific.** `_get_content_write_mtime` / `_prune_consolidated_shards` are asset-group-agnostic UTL code
used by every `uts-prod-manifest-consolidator-*` job. The trap arms whenever BOTH hold:

1. something rewrites a bucket's `_index/availability_index.parquet` out-of-band (a purge, a repair one-off, a manual
   `cp`/restore, a backfill patch script — the workspace has many), **and**
2. a per-VM shard written BEFORE that rewrite is still unmerged when the consolidator next runs.

Condition (2) is most likely exactly when (1) happens, because out-of-band index surgery is normally done with the
consolidators PAUSED — which is precisely when shards pile up unmerged. **The freeze/repair/resume runbook shape makes
this MORE likely, not less.**

Sports MDT was spared only by luck of ordering: its canonical still held a genuine marker (`2026-07-15T22:51:06Z`) and
was never rewritten out-of-band, so its shard (07-16 12:54:13Z) sat NEWER than the cutoff.

## Recommended fix (not yet implemented — this issue doc is the deliverable)

Ordered by strength; (1) is the minimum.

1. **Never prune on a fallback marker.** If `consolidator_content_write_at` (and `consolidator_run_at`) are absent,
   `_get_content_write_mtime` should signal "unknown" for PRUNE purposes and `_prune_consolidated_shards` must **prune
   nothing** — keep every shard, let the next real merge stamp the marker and prune on a later cycle. Pruning is an
   optimisation; merging is the contract. Never trade a durability invariant for a cleanup. (The `blob.updated` fallback
   may still be acceptable for _changed-shard detection_, which fails toward re-merge, not toward drop.)
2. **Make the prune positively-proven, not inferred.** Prune a shard only when its rows are demonstrably in the
   canonical — e.g. stamp each merged shard's generation/mtime into the canonical's metadata (a "merged through" set),
   and prune only members of that set. mtime-vs-cutoff is a proxy that any out-of-band write can falsify.
3. **Make out-of-band index writes preserve the marker.** Any tool rewriting `availability_index.parquet` must carry the
   existing custom metadata forward (or re-stamp it). This is necessary but NOT sufficient — it relies on every future
   one-off remembering, which is the class of assumption that produced this incident.
4. **Loud-fail the tell.** `rows_in=0 … pruned_shards=N>0` is contradictory: shards existed and were listed, yet nothing
   was read from them, and they were deleted anyway. That combination should log an ERROR / alert, never `success=True`.

## Repro

1. Bucket with a canonical index + ≥1 unmerged shard under `_index/per_vm/`.
2. Rewrite `_index/availability_index.parquet` out-of-band without preserving custom metadata (any plain `cp`/write),
   ensuring the rewrite's mtime is NEWER than the shard's.
3. Run the consolidator.
4. Observe: `rows_in=0 rows_out=0 pruned_shards=N`, `success=True`, `exit(0)`; the shard is gone; its rows never landed.

## Verification / recovery recipe (if this already fired somewhere)

- Detect: consolidator log line with `rows_in=0` and `pruned_shards>0`; or an index whose row count did not move across
  a run that pruned shards.
- Check for a stripped marker: read the canonical blob's `.metadata` — `None`/missing on a bucket that has been
  consolidating is the tell.
- Recover: restore the shard (from a pre-event copy — GCS versioning did NOT retain it in the observed case) into
  `_index/per_vm/` so its mtime is NEWER than the canonical's `updated`, then run the consolidator immediately (with the
  writer schedulers paused, so nothing re-advances the cutoff). Verify `rows_in > 0` and re-read the index BY CONTENT.
- **Never** re-upload a shard while its bucket's canonical is still being rewritten out-of-band — the race re-arms.

## Provenance

Found and recovered during `plans/active/sports_legacy_bucket_cutover_2026_07_16.md` T6.1 (2026-07-17). Full measured
narrative, before/after tables and evidence paths: that plan's Progress Log, entry **"✅ T6.1 MERGE COMPLETE"**.
