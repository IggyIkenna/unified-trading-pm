---
title:
  Manifest consolidator starves idle buckets — a per-VM shard written to an idle bucket never merges (incremental
  mtime-cutoff trap)
created: 2026-06-19
source:
  - unified-trading-library/unified_trading_library/manifest_consolidator.py (lines 355-373)
  - 2026-06-19 expected_unattempted materialisation run (cefi/tradfi shards never auto-merged)
locked_by: live-defi-rollout
parent_epic: mtds_mdps_master
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
priority: P2
status: active
---

# Consolidator idle-bucket incremental trap

## What I found

The manifest consolidator (`unified_trading_library/manifest_consolidator.py`) runs a `*/1` Cloud Run cron per bucket
and uses an **incremental** merge: it only re-merges per-VM shards whose `mtime > (canonical_mtime - skew)` (line 360).
When **no shard changed** since the last cycle it takes the no-op path (line 362): it calls
`_touch_canonical_mtime(bucket)` (advancing the canonical marker to NOW) **and** `_prune_consolidated_shards(...)`
(deleting shards older than the cutoff).

On an **idle bucket** (no incoming capture writes) this is a TRAP for any externally-written shard:

1. A producer (e.g. the expected-universe v2 enumerator) writes `_index/per_vm/<vm>.parquet` at time `T`.
2. If a capture write does NOT coincide within the same ~60 s window, the very next idle cycle (canonical_mtime already
   ≈ now) computes `cutoff ≈ now > T` → `changed_paths=[]` → **no-op**: it touches the canonical mtime forward and may
   **prune the un-merged shard as "settled"** — the shard's rows were NEVER incorporated.
3. The shard is then gone (or perpetually "older than cutoff") → its rows never reach the canonical `_index`.

**Observed live 2026-06-19**: the v2 enumerator wrote `expected_unattempted` per-VM shards for all 4 AGs.
`defi`/`sports` (which had concurrent capture writes → `n` grew every cycle) merged within 1 cycle. `cefi`/`tradfi`
(idle — no concurrent captures, `n` frozen) **never merged across ~10 min / 10 cycles**, even after re-writing the shard
with a fresh mtime. A manual `consolidate(bucket, force=True)` (which bypasses the incremental cutoff, line 248) merged
them immediately (cefi eu 0→482,114; tradfi eu 0→818,311; captured preserved). So the merge logic is correct; the
**incremental cutoff starves idle buckets of externally-written shards**.

## Why it matters

- **Data correctness ≥1 asset_group.** Any out-of-band writer to an idle bucket's per-VM shard (the v2 expected-universe
  enumerator, a rebuild script, a backfill that finished and went quiet) can have its rows silently dropped. The
  `expected_unattempted` 4th-state seed is exactly this pattern.
- The new `expected_universe_v2_scheduler.tf` (01:30 UTC daily, `--apply-write`) will hit this on any AG that is idle at
  01:30 — the shard will be written but never merged → the denominator silently fails to update. The recurring fix is
  not self-sustaining until this is addressed.
- The prune step makes it WORSE than a benign delay: the shard can be deleted before it ever merges.

## Recommended decision

Two options (operator pick):

1. **Fix the consolidator (preferred, at the UTL SSOT):** in the no-op branch (line 362), before pruning, detect a shard
   whose rows are NOT yet represented in the canonical (mtime newer than the canonical's LAST REAL WRITE marker — track
   a separate `last_full_write_mtime` distinct from the `_touch`ed freshness mtime) and force-merge it. I.e. do not let
   an idle `_touch` advance the cutoff past an un-merged shard. The fix must be OOM-safe (cefi had a 2099-shard SIGKILL
   incident) — keep the bounded incremental working set, only widen the "changed" predicate to "newer than last real
   write".
2. **Companion force-consolidate in the scheduler (workaround):** add a per-AG Cloud Run job to
   `expected_universe_v2_scheduler.tf` that runs `consolidate(bucket, force=True)` immediately AFTER the enumerator job
   (01:35 UTC), so idle AGs always get a full merge of the just-written seed shard. Cheap, isolated, no hot-path change
   — but leaves the underlying trap for every other out-of-band writer.

Until either lands, the materialisation must be force-consolidated manually after an enumerator apply-write on an idle
AG (the 2026-06-19 run did exactly this for cefi/tradfi).

## Provenance

Surfaced during the 2026-06-19 `expected_unattempted` 4th-state materialisation (master_data_canonicalisation §G1
G1.run-bounded). The enumerator + catalogue + per-VM shard path are correct; this is purely the consolidator's
idle-bucket incremental decision.
