---
doc_type: issue
title: >-
  DeFi manifest's `_index/per_vm/` fallback-merge path is exposed to unbounded growth from OTHER processes' large per-VM
  shards -- a live, currently-growing 173.8MB canonical-migration shard bloats every handler's fallback read
summary: >-
  Investigated while root-causing a rare late-stage OOM/timeout on `uts-prod-mtds-collect-lst-rates` (see
  `lst_venue_registry_gap_and_cron_crash_loop_2026_07_22.md`). Read `unified-trading-library`'s
  `manifest_writer/_read_index.py::_read_and_merge_per_vm_shards` -- triggered whenever a handler's manifest
  freshness-check finds the consolidated index blob >120s stale (`_read_consolidated_if_fresh`'s threshold); it lists +
  pandas-reads + merges EVERY parquet under `_index/per_vm/` for the bucket. As of this check the DeFi manifest bucket's
  `_index/per_vm/` holds `canonical-migration-defi-rebuild-20260722-194751.parquet`, which grew from 113.6MB to 173.8MB
  within 12 hours and was still being actively written at check time -- this is a real, live, worsening cost paid by
  EVERY DeFi handler that happens to hit the fallback path, not something specific to `lst_rates_handler.py`. Checked
  the manifest consolidator's own health (`uts-prod-manifest-consolidator-market-data-defi`) -- it is currently running
  reliably (~60s cadence, mostly succeeding), so this is not "the consolidator is broken"; it's that the
  per-VM-shard-merge fallback itself has no size guard, so ANY large stray/in-progress shard in that shared directory
  (this migration's shard today; some other process's tomorrow) makes every handler's occasional fallback read
  proportionally more expensive. NOT confirmed to be the exact cause of the specific historical
  `uts-prod-mtds-collect-lst-rates` OOM (2026-07-21, execution `xrhf8`) or timeout (2026-07-22, execution `4f99t`) --
  this specific 173.8MB shard did not exist yet at either of those timestamps, so the mechanism is real and current but
  not retroactively provable for those two incidents specifically. Filed as a standalone cross-cutting issue (not folded
  into the LST doc) because the fix, if any, lives in a shared library (`unified-trading-library`) used by every DeFi
  handler, and because the migration shard itself belongs to the `defi_consolidated_closeout_2026_07_18.md` effort, not
  this thread -- NOT touched, NOT deleted (live, in-progress WIP belonging to a different process).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer]
tags: [defi, manifest, per-vm-shards, oom, timeout, consolidator, shared-library, canonical-migration]
related:
  - lst_venue_registry_gap_and_cron_crash_loop_2026_07_22.md
  - plans/active/defi_consolidated_closeout_2026_07_18.md
created: "2026-07-23"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source: [self-investigation-2026-07-23]
---

# What I found

- `_read_and_merge_per_vm_shards` (`unified_trading_library/manifest_writer/_read_index.py`) has no size/row-count
  guard: it lists every blob under `_index/per_vm/` for a bucket and reads + pandas-concats all of them whenever the
  consolidated index is judged stale (>120s, `_read_consolidated_if_fresh`'s threshold).
- The DeFi manifest bucket's per-VM directory currently holds a shard from an unrelated, actively-running process
  (`canonical-migration-defi-rebuild-20260722-194751.parquet`) that grew 113.6MB -> 173.8MB in under 12 hours and was
  still being written at check time (`updated: 2026-07-23T06:24:33Z`).
- The manifest consolidator itself (`uts-prod-manifest-consolidator-market-data-defi`) is healthy right now -- executing
  roughly every 60s, mostly succeeding -- so the risk isn't "the consolidator never runs"; it's that ANY large shard
  sitting in the shared per-VM directory (this one today, a different one tomorrow) makes the occasional fallback read
  proportionally slower/heavier for every handler that hits it, with no circuit-breaker.
- `uts-prod-mtds-collect-lst-rates`'s two recent failures (`xrhf8` 2026-07-21 OOM, `4f99t` 2026-07-22 timeout) both
  showed the RSS spike (535MiB -> 1493MiB in ~30s) and the crash happening LATE in the run, consistent with this
  mechanism being a plausible contributor -- but the specific 173.8MB shard did not exist at either timestamp, so I
  cannot claim it explains those two incidents specifically. The mechanism is real and current; its role in those two
  past incidents is unproven.

# What I did NOT do

Did not modify `_read_and_merge_per_vm_shards` or add a size guard -- this function is shared across every DeFi handler
(and potentially other asset groups) that reads this manifest; a wrong bound here risks silently dropping real per-VM
data for some other consumer. Did not touch or delete the migration shard -- it is live, in-progress WIP owned by a
different, currently-running process (`defi_consolidated_closeout_2026_07_18.md`'s canonical-migration effort), not
something to interrupt.

# Suggested next step

A dedicated unit (not squeezed into an LST-scoped session) should: (1) decide whether the per-VM-merge needs a size/row
cap with a WARN-and-sample fallback instead of an unbounded read, (2) confirm whether the consolidator should
proactively fold+archive very large per-VM shards sooner rather than leaving them for the next scheduled cycle, and (3)
re-check whether `canonical-migration-defi-rebuild-20260722-194751.parquet` has been folded away once that migration
completes -- if it has, this specific instance of the risk resolves itself even without a code change, though the
underlying unbounded-fallback exposure remains for the next large shard.
