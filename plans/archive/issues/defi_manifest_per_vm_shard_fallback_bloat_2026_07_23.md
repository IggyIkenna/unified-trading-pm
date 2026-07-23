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
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer]
tags: [defi, manifest, per-vm-shards, oom, timeout, consolidator, shared-library, canonical-migration]
related:
  - /plans/archive/issues/lst_venue_registry_gap_and_cron_crash_loop_2026_07_22.md
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
resolved_by: unified-trading-library@c5cd6186, unified-trading-library@36bdbbae
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

# Resolution (2026-07-23, full investigation + fix)

Operator asked for the full investigation and fix. Traced the exact code path end to end
(`unified_trading_library/manifest_writer/_read_index.py`):

**The framework already has a designed-in safety net, and it's correctly configured for lst-rates.** `_read_slow_path`
loud-fails (`ManifestConsolidatorStaleError`) by default whenever the consolidated index is stale AND per-VM shards
exist -- the expensive merge is an explicit opt-in via `MANIFEST_ALLOW_STALE_FALLBACK=true`. Confirmed via `grep` across
every `deployment-service/terraform/gcp/*.tf` Cloud Run Job definition: this env var is **NOT set** for
`uts-prod-mtds-collect-lst-rates` (only the writer-side `MANIFEST_PER_VM_SHARDS=true` is). And that loud-fail, when it
does fire, is caught gracefully by `ManifestFreshnessCache._refresh_locked`'s own `except Exception` -- it logs, keeps
the previous (possibly empty) membership set, and continues; it does not crash the handler. So this specific
default-safe path was very likely NOT the direct cause of the two historical crashes either -- consistent with the
original doc's honest "unproven" framing.

**The REAL, confirmed gap: the recovery-merge path (whenever it IS exercised -- opt-in via
`MANIFEST_ALLOW_STALE_FALLBACK`, or via test-VM runs which `setup-data-pipeline-vm.sh` deliberately sets it for) never
threaded `filters=` through at all.** The consolidated fast-path already bounds peak memory via row-group predicate
pushdown (`mtds_backfill_vm_startup_oom_rc137_2026_07_14`: ~14.86 GiB -> ~5 MB for a single-day filter on the real
27.4M-row DeFi index) -- but `_read_and_merge_per_vm_shards` had no `filters` parameter at all, so ANY caller that does
hit this path (any handler using `ManifestFreshnessCache`'s date-bounded `filters=`, on ANY bucket, if the opt-in is
ever set) decodes the FULL, unfiltered row set of every per-VM shard. The code's own comments already flagged this exact
gap as known ("filters aren't threaded through the per-VM-shard-merge recovery path... a separate, already-flagged
large-heap risk") but nobody had closed it.

**Fixed**: threaded `filters=` through the whole chain -- `_read_and_merge_per_vm_shards` -> `_read_slow_path` ->
`_wait_for_in_flight_cycle_then_reread` and `_read_availability_index_slim`'s recovery branch -- reusing the exact same
row-group-skip mechanism already proven safe on the consolidated path. Purely additive (new optional parameter, default
`None`); verified no existing caller passes positional args that would collide with the new parameter (checked every
call site of all 3 functions across `unified-trading-library` and every downstream repo that references them). Added
`test_reader_recovery_merge_with_filters_narrows_per_vm_shard_rows` (seeds a per-VM shard with two different dates,
asserts a date-range filter excludes the non-matching row even on this recovery path) alongside the existing
`test_reader_recovery_merge_when_opted_out_and_consolidated_stale` family. QG-green, shipped
`unified-trading-library@c5cd6186`.

**The risk this closes is bigger and more urgent than it looked a few hours ago.** Re-checked the DeFi manifest's
`_index/per_vm/` directory while finishing this fix: the original migration shard grew again (173.8MB -> 176.6MB) AND
**7 new sibling shards appeared in the same ~15-minute window**
(`canonical-migration-defi-rebuild-20260723-{073604,073738,074640,075224,075807,075900,080250}.parquet`, 1.7MB-73.4MB
each) -- the migration effort has scaled out to a small VM fleet, all writing into the same shared per-VM directory.
Total per-VM shard size right now is ~386MB across 10 files, up from ~114MB this morning. Every one of those shards is
still live, in-progress WIP belonging to `defi_consolidated_closeout_2026_07_18.md` -- NOT touched, NOT deleted. This
growth trend is exactly why the fix matters even though it wasn't provably the cause of the two original incidents: the
fallback path is now materially MORE expensive than it was when this issue was first filed, for every DeFi handler that
might ever exercise it.

**Not done, deliberately left for the dedicated review the original doc recommended**: a size/row cap with a
warn-and-sample fallback (belt-and-suspenders on top of the filters fix, for callers with an unbounded query), and
whether the consolidator should fold+archive large per-VM shards more proactively. The `filters=` fix addresses the
specific, confirmed gap for date-bounded callers (`ManifestFreshnessCache`, the common case); a caller with NO date
bound would still pay the full cost if it ever hits this path — that residual case is still open.

# Resolution, round 2 (2026-07-23 -- operator asked to do the two remaining items in full)

**Size/row cap for callers with no date bound -- shipped.** `_read_and_merge_per_vm_shards` now accepts an optional
`max_total_bytes`. When set, shards are listed with their real size (`BlobMetadata.size`, free from the same
`list_blobs` call -- no extra network round-trip), sorted smallest-first, and read until the NEXT shard would exceed
budget; the caller's own shard and the legacy seed are ALWAYS kept regardless of size (mirrors `_read_self_shard`'s "a
writer always sees its own writes" guarantee, and the seed's permanent-bootstrap status), and at least one shard is
always kept overall so a lone giant shard with a tiny budget doesn't collapse the read to nothing. Anything skipped past
the budget is logged (WARNING) and emitted as a new `MANIFEST_PER_VM_MERGE_SHARDS_SKIPPED` event -- never silently
dropped. Default 200MiB (headroom under the 2Gi Cloud Run ceiling most DeFi collect jobs run under, at a 3-5x pandas
decode multiplier), overridable via `MANIFEST_PER_VM_MERGE_MAX_BYTES`. Wired into `_read_slow_path` ONLY when the caller
has no `filters=` (a filtered caller already gets the row-group-pushdown protection from the earlier fix);
`merge_canonical_with_outstanding_shards`'s read-before-write-back and `_maintenance.py`'s reconciler call
`_read_and_merge_per_vm_shards` directly and never pass this budget, so their completeness guarantee is unaffected. 7
new tests (pure unit tests for the budget-trimming logic itself, plus an end-to-end test with a real
`BlobMetadata`-backed stub proving a shard over budget contributes zero rows to the merged result). One real bug caught
and fixed during testing: the initial "always keep at least one" exemption logic incorrectly checked for a non-exempt
entry already present, which let the self-shard/legacy-seed exemptions accidentally starve the budget check entirely
whenever either was present -- fixed to the correct invariant (never skip if doing so would leave the kept set
completely empty, full stop). Shipped `unified-trading-library@36bdbbae`, QG-green.

**Consolidator proactive fold+archive -- investigated, no code change warranted.** Read
`manifest_consolidator.py::_prune_consolidated_shards` in full: it already deletes a per-VM shard as soon as it can
PROVE the shard's rows are durably in the canonical (mtime `<= cutoff`, where cutoff is the last merge's own
listing-start marker) -- and explicitly, by design, refuses to prune any shard whose mtime is still advancing
(`if mtime > cutoff: continue  # not yet settled -- keep`), because deleting an actively-written shard risks losing rows
never merged. This is correct and already as proactive as it safely can be. The growth observed earlier (one migration
shard becoming several, ~114MB -> ~386MB) is an INHERENT, TEMPORARY property of currently-running migration VMs
continuously appending to their own shard files, not a consolidator gap -- each VM's shard becomes prune-eligible on the
next cycle after that VM stops writing. No fix needed or made here; forcing the consolidator to prune an
actively-written shard would be actively unsafe.

**Also checked, per a separate operator ask**: scanned every production bucket's `_index/per_vm/` directory (execution,
features x5, instruments x5, market-data x5, ml-store, strategy x2 -- 20 buckets) for shards older than 1 hour (a looser
threshold than the consolidator's own staleness budget). Zero found anywhere -- no stuck/regressed shards across the
estate right now; everything present is either actively being written or the permanent legacy seed.

**Status: resolved, both remaining items closed.**
