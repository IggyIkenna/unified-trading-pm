---
doc_type: issue
title:
  "MDPS `reprocess_sports_odds.py --full` OOM-killed at ~24/571 days — repeated full-schema manifest reload under a
  long-running ThreadPoolExecutor"
summary: >-
  Relaunching MDPS shard4's `odds_horizon_bucket` reprocess in `full` mode (per
  `mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`'s P2 todo) OOM-killed (exit_code=137, SIGKILL) on an
  e2-standard-8 (32GB) VM after only ~24/571 days, RSS reaching ~31.7GB. Root cause: `full` mode's manifest pre-flight
  (`writer.lookup()`, only exercised when NOT `--force`) calls `read_availability_index()` with no `columns=`/`filters=`
  — the full ~30-column, whole-sports-manifest (240MB compressed) schema — and the in-process cache
  (`_INDEX_CACHE_TTL=60s`, `unified_trading_library/manifest_writer/_state.py`) expires and reloads every 60s regardless
  of run duration. Under 16 concurrent `ThreadPoolExecutor` workers over a multi-hour run, multiple full-schema copies
  can be alive simultaneously across cache-refresh cycles, accumulating RSS until OOM. This exact code path (`full`
  mode's manifest pre-flight) was NEVER previously exercised at this data scale — the original 4-shard sweep used
  `force` mode throughout, which skips the pre-flight lookup entirely (see `reprocess_sports_odds.py`'s `if not force
  and not dry_run:` guard around Pre-flight 2) — so this is a newly-discovered gap, not a regression.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, unified-trading-library]
scope: [engineer]
tags: [mdps, oom, manifest-cache, full-mode, reprocess, memory, vm]
related: [/plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md]
created: 2026-08-03
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
source:
  "worker, slot 5, executing mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md's P2 shard4 full-mode retry
  todo — VM OOM-killed at ~24/571 days"
resolved_by:
locked_by:
context_scope:
  [
    market-data-processing-service/scripts/reprocess_sports_odds.py,
    unified-trading-library/unified_trading_library/manifest_writer/_writer_io.py,
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    unified-trading-library/unified_trading_library/manifest_writer/_state.py,
  ]
drift_direction: advance-code
depends_on: []
---

# MDPS full-mode reprocess OOM — manifest-cache reload under a long-running worker pool

## What I found

Launched `bash scripts/vm/launch-mdps-sports-bucket-vm.sh 2025-01-01 2026-07-25 full` (e2-standard-8, SPOT,
`--workers 16`) per the parent doc's P2 todo. `run.log` shows steady per-day pre-flight skips
(`Manifest pre-flight: prior status=captured for <date> — skipping`) interleaved with repeated
`MANIFEST_LOAD_SIZE_BYTES` events (`bytes_compressed=251711327`, ~240MB) roughly every 10-20s — far more frequent than
the 571-day run should need if the cache were holding. At `[24/571]` (~3.5 minutes in), the serial console shows:

```
[  327.528302] Out of memory: Killed process 8765 (python) total-vm:39776308kB, anon-rss:31673032kB, ...
```

`vm-exec` recorded `command exited rc=137`; the deployment record was archived `status=failed, exit_code=137`. VM
self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true`.

**Root cause chain**:

1. `reprocess_sports_odds.py`'s Pre-flight 2 (`writer.lookup(row_key=_coarse_row_key(date_str))`,
   `scripts/reprocess_sports_odds.py:893-900`) runs only `if not force and not dry_run` — i.e. **only in `full` mode**,
   never in `force` mode (which the original 4-shard sweep used exclusively — this is why this bug was never hit
   before).
2. `ManifestWriter.lookup()` (`unified_trading_library/manifest_writer/_writer_io.py:196`) calls
   `_mw.read_availability_index(self.catalogue_bucket)` with **no `columns=`/`filters=`** — deliberately, per its own
   comment ("not meaningfully slim-projectable... the union is effectively the full schema") — i.e. every lookup call is
   a full-schema, whole-manifest read.
3. `read_availability_index()`'s full-schema path caches the resulting DataFrame in-process for `_INDEX_CACHE_TTL=60s`
   (`unified_trading_library/manifest_writer/_state.py:63`). A cache HIT returns the same object (cheap); a cache MISS
   re-downloads + re-decodes the full ~240MB-compressed manifest.
4. `reprocess_sports_odds.py` runs a single `ManifestWriter` instance shared across a 16-worker `ThreadPoolExecutor` for
   the WHOLE run (`scripts/reprocess_sports_odds.py:1075-1079` construction, `:1108` pool) — a run intended to process
   571 days will, by design, run for many multiples of the 60s TTL. Every ~60s the cache expires and the NEXT lookup
   call reloads a fresh full-schema DataFrame; if any OTHER thread is still mid-processing (holding a reference to the
   OLD cached object, e.g. via `matching = df[mask]` intermediate) when the reload happens, both copies are briefly
   resident. Repeated over enough 60s cycles under 16-way concurrency, RSS accumulates until the kernel OOM-kills the
   process — confirmed empirically (31.7GB RSS reached in ~5.5 minutes / ~5 cache-refresh cycles on a 32GB machine).

This is a genuine gap in the `_INDEX_CACHE_TTL=60s` design: the docstring frames the cache as protecting against
re-download "on every date check in backfill VMs" but a 60s TTL only helps within a single burst of activity shorter
than 60s — any real multi-hour reprocess run will still re-pay the full-schema reload cost repeatedly, and with
concurrent workers, can pile up enough simultaneous copies to OOM a standard-memory VM.

## Why it matters

Any future `full`-mode (non-`--force`) reprocess of ANY asset_group at comparable manifest size/run-duration is at risk
of the same OOM — this is not sports-specific or reprocess_sports_odds.py-specific; the shared `ManifestWriter.lookup()`
path is used by every service that does manifest pre-flight checks in `full` mode. Directly blocks this doc's own parent
task (`mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`'s P2 todo) from completing on the default
machine type.

## Recommended decision

Two independently-shippable angles (do NOT bundle):

1. **Immediate unblock (this task)**: relaunch shard4's retry on a higher-memory machine type (e.g. `e2-highmem-8`,
   64GB) and/or reduced `--workers` to bound concurrent stale-copy accumulation. This does not fix the underlying design
   gap, just avoids tripping it for this one run.
2. **Root-cause fix (separate, broader scope)**: either (a) raise `_INDEX_CACHE_TTL` for long-running batch jobs
   specifically (a per-call override, not a global bump — full-schema data can go stale for online services that need
   near-real-time freshness), or (b) have long-running reprocess scripts load the manifest ONCE up front and pass an
   explicit snapshot into `lookup()`-equivalent calls instead of relying on the shared TTL cache, or (c) make the cache
   genuinely bound total concurrent memory (e.g. a single-flight/lock around reload so only one fresh copy is ever
   built, immediately dropping the old reference). This needs design input on which approach fits `ManifestWriter`'s
   existing contract — flagged as its own todo below rather than solved here.

## Second occurrence (2026-08-03T10:11Z) — confirms this is NOT a fixed-peak, machine-size-fixable OOM

Relaunched on `e2-highmem-8` (64GB) with `--workers 8` (down from the original 16). **OOM-killed again**
(exit_code=137), this time at ~21/571 days (vs ~24/571 on the smaller machine) — further progress before the crash, but
still crashed. This rules out "just needs a bigger machine": the failure point scaled only slightly with 2x the RAM and
half the workers, which is consistent with a **thundering-herd** pattern rather than one fixed-size leak:

- `read_availability_index()`'s own docstring states the full-schema sports index decodes to **~6.5GB** in memory (not
  just the 240MB compressed size).
- `ManifestWriterIoMixin.lookup()` has **no single-flight/lock guard** around a cache-miss reload — every thread that
  calls `lookup()` in the same instant the 60s TTL expires independently triggers its OWN full ~6.5GB decode.
- Worst case at `--workers N` concurrent threads hitting a cache-expiry boundary together: **N × 6.5GB** simultaneous
  resident copies, on top of base process/pandas overhead. At `N=16` this is up to ~104GB (trivially OOMs any reasonable
  machine); at `N=8` up to ~52GB (explains surviving longer on a 64GB machine before an unlucky coincidence of
  concurrent expiries pushed it over).
- This means naively scaling `MACHINE_TYPE` up is not a viable mitigation path in general — it only buys a probabilistic
  delay, not a bound. The only mitigation that changes the WORST-CASE bound (not just the observed odds of hitting it)
  is reducing `--workers` low enough that `N × 6.5GB` fits comfortably (e.g. `--workers 2` → ~13GB worst case, safe even
  on a standard machine) — genuinely fixing this requires the single-flight/snapshot fix in item 2's P3 todo below.

## Third occurrence (2026-08-03T10:19Z) — thundering-herd hypothesis REFUTED; escalating to P1

Relaunched a THIRD time on the default `e2-standard-8` (32GB) with `--workers 2` — the minimum-concurrency mitigation
the thundering-herd analysis above predicted would be safe (worst case `2 × 6.5GB ≈ 13GB`, well under 32GB).
**OOM-killed again** (exit_code=137), this time at only **~18/571 days, ~3 minutes wall-clock** — WORSE relative timing
than either prior attempt, not better.

This refutes the thundering-herd/concurrent-reload theory as the (sole) cause: `--workers 2` gives essentially no room
for a multi-thread pile-up, yet the process still exhausted 32GB in ~3 minutes. Re-reading the cache implementation
(`_read_index.py:606-636`): `_INDEX_CACHE[bucket]` is a **single dict entry per bucket, overwritten** on every reload
(`_INDEX_CACHE[bucket] = (now, _backfill(...))`) — not an accumulating collection — so a naive "cache dict grows
forever" explanation doesn't fit the code either. The reload cadence observed in this run's `run.log`
(`MANIFEST_LOAD_SIZE_BYTES` events at 10:17:02 and again at ~10:18:11, ~69s apart) is consistent with the documented 60s
TTL, not a runaway reload storm.

**Conclusion: the true root cause is NOT fully isolated yet.** Candidates that remain open, roughly in order of
suspicion:

1. A genuine reference leak keeping the "overwritten" old `_INDEX_CACHE` entry alive somewhere else in the call chain
   (e.g. a still-referencing local variable in `lookup()`'s `df`/`matching` intermediates that outlives the call via a
   closure, an exception traceback, or a `ThreadPoolExecutor` future retaining its call-frame).
2. Something in `reprocess_sports_odds.py`'s OWN per-date processing (`reprocess_date()` / the sports-odds adapter
   fetch/decode path) that is unrelated to the manifest cache entirely and just happens to correlate with the same
   symptom — this pass did not rule this out, since all 3 attempts used the SAME reprocess script + SAME data range.
3. GC-generational delay: CPython's refcounting frees most objects immediately, but reference cycles (e.g. pandas
   internals with circular refs) only get collected on a generational GC pass, which may not fire often enough under
   this workload's allocation pattern to keep pace with ~6.5GB-per-cycle churn.

**Do not attempt a 4th VM-launch-and-guess cycle.** Three attempts (workers=16/e2-standard-8, workers=8/ e2-highmem-8,
workers=2/e2-standard-8) have now all OOM'd, burning real SPOT-VM cost each time without new diagnostic signal beyond
"still crashes." The next step needs actual memory profiling (`tracemalloc` / `objgraph`/heap snapshot at intervals),
not another blind resource-scaling guess — see the P1 todo below.

## Todos

- [x] ✅ [INFRA] P1. **DONE 2026-08-03 — root-caused + fixed (candidate 1, the manifest-cache path, confirmed).** Wrote
      a local tracemalloc/RSS reproduction
      (`market-data-processing-service/scripts/profile_reprocess_sports_odds_memory_2026_08_03.py`, bounded to 20G via
      `run-bounded-analysis.sh` — since deleted per its own `Delete-when:` marker now that the fix has shipped) with two
      isolated arms: Arm A repeated `ManifestWriter.lookup()`'s exact Pre-flight-2 call with
      `_INDEX_CACHE_TTL`/`_CANONICAL_CACHE_TTL` patched down to 2s (so many reload cycles fit in a short run); Arm B ran
      the real `reprocess_date(..., dry_run=True)` (skips the manifest lookup + write entirely) over real dates to
      isolate candidate 2. Arm A's iteration 0 alone measured ~12.4GB RSS for ONE `lookup()` call (`malloc_trim(0)`
      recovered only ~54MB — ruling OUT arena/allocator retention, i.e. this was genuinely referenced, not just
      unreturned-to-OS); iteration 1 (the next 60s-equivalent reload cycle) OOM'd outright with
      `numpy._core._exceptions._ArrayMemoryError: Unable to allocate 3.36 GiB for an array with shape (38, 11853040)` —
      direct proof the sports manifest is ~11.85M rows / 38 columns and `lookup()`'s bare, unfiltered
      `read_availability_index(bucket)` decodes the FULL schema on every cache-miss cycle, process-global regardless of
      `--workers` (explaining why worker-count scaling never helped in any of the 3 VM attempts). **Fix**
      (unified-trading-library@4dc12dbe, was landed as 2 local commits then rebased+pushed by quickmerge):
      `ManifestWriter.lookup()` now derives `filters=[("date", "==", key["date"])]` from the row_key (every row_key
      already requires a non-empty `date` — `_coerce_row_key` raises otherwise, so this fires on every real call) and
      threads it into `read_availability_index(bucket, filters=...)`. Extended the row-group-pushdown mechanism (already
      proven on the slim/`columns=` path, `mtds_backfill_vm_startup_oom_rc137_2026_07_14`: ~14.86 GiB → ~5 MB for a
      single-day filter) to the full-schema (`columns=None`) path too via a new `_read_availability_index_full_filtered`
      — `lookup()`'s own reasoning against `columns=` narrowing (needs ~25 of ~30 columns for the returned
      `ManifestRow`) only rules out column pruning, not row pruning; the two are orthogonal. Bypasses
      `_INDEX_CACHE`/`_CANONICAL_CACHE` when filtered (mirrors the slim path's own cache-bypass). Added 6 regression
      tests (`tests/unit/test_manifest_full_read_date_filter.py`): full V8 schema still returned (not narrowed), filter
      correctly isolates the matching date only (no cross-date leak), filtered reads bypass both caches, an unfiltered
      bare call is completely unaffected (back-compat), and `lookup()` actually derives + passes the filter end-to-end.
      unified-trading-library's full `quality-gates.sh` passed both before and after (149s / 205s). Repos:
      unified-trading-library@4dc12dbe.
- [x] ✅ [INFRA] P2. **DONE 2026-08-03 (slot-9) — fix confirmed, ran clean to completion, zero OOM.** Found
      `mdps-sports-bucket-20260803-134154` (e2-standard-8, SPOT, `--workers 16` — same original params, the P1 fix
      applies regardless of worker count) already launched (13:41:54Z) with `unified-trading-library@4dc12dbe` in place;
      monitored it end-to-end rather than duplicate the launch. Completed cleanly in 1591s (2.8s/date) — **no OOM at any
      point**, sailing well past the ~18-24/571-day mark where all 3 pre-fix attempts crashed. Final tally: 571 total,
      48 success, 0 empty, 19 attempted_failed, 500 skipped (already captured/empty_confirmed, correct `full`-mode
      resume behavior), 4 `LOSS_GUARD_BLOCKED`. `rc=1` is EXPECTED (same as pre-fix runs) — the script exits non-zero
      whenever residual failures remain, unrelated to the OOM bug this fix targets. Confirms the root cause (unfiltered
      full-schema manifest decode in `ManifestWriter.lookup()`) was correctly isolated and fixed. Full
      manifest-verification + residual-date accounting is tracked in the sibling parent doc
      (`mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`'s P2 todo, its own action item) rather than
      duplicated here. Repo: market-data-processing-service, deployment-service — no new code, verification only.
