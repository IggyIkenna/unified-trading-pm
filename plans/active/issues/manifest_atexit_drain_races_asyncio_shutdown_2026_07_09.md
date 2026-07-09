---
doc_type: issue
title:
  ManifestWriter's atexit "guaranteed" per-VM drain races the asyncio event loop's own executor teardown — silently
  drops buffered writes on fast-exit asyncio scripts
summary:
  "After fixing the missing-.write() bug in understat/weather/footystats (sibling issue doc
  manifest_early_return_missing_write_loss_2026_07_09.md), re-ran the understat EU residual closer script and observed a
  NEW failure at process exit: `ManifestWriter write failed: cannot schedule new futures after interpreter shutdown`.
  The atexit-registered flush_all_pending_buckets() handler — documented as the GUARANTEED drain for fast-exit processes
  — races the asyncio event loop's own executor shutdown and silently fails (a WARNING log line, not a raised
  exception), meaning any asyncio-based script relying solely on the atexit guarantee can lose its final, un-debounced
  batch of manifest writes with no visible error in its own success reporting."
status: open
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library]
scope: [engineer, admin]
tags: [manifest, atexit, asyncio, data-correctness, silent-write-loss, race-condition]
related:
  [
    plans/active/issues/manifest_early_return_missing_write_loss_2026_07_09.md,
    plans/active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md,
    plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md,
  ]
created: 2026-07-09
parent_epic: sports_master
priority: P0
source: [plans/active/issues/manifest_early_return_missing_write_loss_2026_07_09.md]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-09
---

## What I found

After fixing the missing-`.write()` bug (sibling issue doc), re-ran `understat_eu_residual_closer_2026_07_08.py` (v4)
against prod GCS with `MANIFEST_PER_VM_SHARDS=true`. The MAIN pass processed all 413 dates in ~2 seconds (all resolved
via the cheap off-season-guard short-circuit, no network calls) and logged exactly ONE
`ManifestWriter: per-VM shard updated (5 total entries, 5 new, process_final=False)` line — for the FIRST date only. The
remaining ~408 dates' worth of `.write()` calls (now correctly issued, per the sibling fix) were buffered into the
module-level pending buffer but never triggered another live shard rewrite, because the module-buffer time-throttle
(`_should_flush_to_gcs`) hadn't elapsed again within the ~2-second run.

At process exit, the script logged:

```
WARNING ManifestWriter write failed: cannot schedule new futures after interpreter shutdown
```

No shard matching the run's `VM_NAME` (`understat-eu-residual-closer-20260709-v4-fixed`) ever appeared in
`_index/per_vm/`. The script's own final self-check (`blank_reason_eu_dates()`, called immediately after) still reported
all 413 dates remaining — i.e. genuinely NONE of the ~4,125 buffered rows persisted, not a read-side staleness artifact.

**Root cause**: `flush_all_pending_buckets()` (`unified_trading_library/manifest_writer/_state.py:704`) is registered as
the `atexit` handler specifically to catch fast-exit processes that finish inside `_WRITE_FLUSH_INTERVAL` (its own
docstring: "an MDPS catch-up VM that finishes a 28-day window in 8 minutes... leaves all manifest records in the
in-memory buffer when the interpreter exits"). But `atexit` handlers run during CPython interpreter shutdown, by which
point objects like `asyncio`'s default `ThreadPoolExecutor` (used for `run_in_executor` calls the GCS client library or
`gcsfs` may make internally) can already be in the process of shutting down — `concurrent.futures` raises
`RuntimeError: cannot schedule new futures after interpreter shutdown` if a `.submit()`/executor call happens after that
point. The manifest write path apparently dispatches its actual GCS upload (or some part of its drain) through such an
executor, and by the time `atexit` fires for the manifest module, the executor may already be torn down — depending on
Python's LIFO atexit-handler ordering and exactly which library registered its shutdown hook first. This makes the
"guaranteed" drain NOT actually guaranteed for `asyncio.run(main())`-style scripts — exactly the class of script this
whole repo's backfill/closer scripts are written as.

**Workaround applied (not a fix)**: added an explicit `_mw.flush_all_pending_buckets()` call at the end of
`understat_eu_residual_closer_2026_07_08.py`'s `main()` coroutine — i.e. called EXPLICITLY while the event loop (and any
executors it depends on) is still fully alive, before `asyncio.run()` returns and interpreter shutdown begins. Verified
this works: re-ran (v5) and got
`ManifestWriter: per-VM shard updated (4130 total entries, 4125 new, process_final=True)` +
`EXPLICIT PRE-EXIT DRAIN: {'instruments-store-sports-prd-...': 4125}`, followed by the script's own final check
correctly reporting 0 remaining — independently re-verified in a fresh process + after forced consolidation.

This workaround is scoped to ONE one-off script. It does NOT fix the underlying race in `unified_trading_library` itself
— any OTHER asyncio-based backfill/closer/one-off script that relies solely on the atexit guarantee (which is the
documented, expected way to get the "fast-exit" safety net) is still exposed to the same silent loss.

## Why it matters

1. **Silently defeats the exact guarantee the atexit handler exists to provide.** The docstring explicitly calls out
   fast-exit processes (an 8-minute VM run) as the target scenario this handler protects — but a fast-exit _asyncio_
   process is precisely where the race is most likely to fire (short total runtime, event-loop-owned executors present,
   interpreter shutdown following almost immediately after the coroutine returns).
2. **No raised exception, no non-zero exit code** — just a `WARNING` log line easy to miss in a busy backfill log, and a
   "COMPLETE" success message from the calling script that is unaware anything was lost. This is exactly the kind of
   silent-placeholder-adjacent failure mode this codebase's honest-absence discipline is designed to prevent, just one
   layer lower (in the write-buffering infra itself, not the business-logic callsite).
3. **Cross-cutting**: any asset_group's asyncio-based backfill/closer script using `MANIFEST_PER_VM_SHARDS=true` and
   relying on the atexit drain (rather than an explicit in-loop flush) is exposed — not sports-specific.

## Recommended decision

- [ ] [INVESTIGATE] P0. Root-cause exactly which executor/library is torn down before the manifest module's atexit
      handler runs (candidates: `asyncio`'s default executor, `gcsfs`'s internal thread pool, `google-cloud-storage`
      client transport threads) and confirm whether Python's `atexit` LIFO ordering can be controlled (e.g. registering
      the manifest flush handler EARLIER so it runs LATER, i.e. before dependent executors register their own shutdown)
      or whether the fix must be structural. (repo: unified-trading-library)
- [ ] [CODE] P0. Make the guaranteed drain actually guaranteed for asyncio scripts — either (a) provide + document a
      public "call this before your asyncio.run() returns" helper (formalizing the workaround applied here) that every
      asyncio-based one-off/backfill script is expected to call explicitly, since atexit cannot be trusted post-hoc, or
      (b) fix the executor-teardown race so plain atexit is reliable again. Add a regression test that simulates an
      asyncio script exiting fast with pending per-VM records and asserts the shard is written. (repo:
      unified-trading-library)
- [ ] [SCRIPT] P1. Audit other asyncio-based one-off/backfill scripts under `instruments-service/scripts/backfill/` (and
      sibling repos) for the same reliance-on-bare-atexit pattern; apply the same explicit-pre-exit-drain workaround to
      any that matter for an active plan's gate, pending the real fix above. (repo: instruments-service)
- [ ] [SCRIPT] P2. Add a QG check that greps for `asyncio.run(` in a script alongside `MANIFEST_PER_VM_SHARDS` env usage
      and requires an explicit `flush_all_pending_buckets()` call in the same file, to catch new instances of this
      anti-pattern going forward. (repo: unified-trading-pm)

## Progress Log

### 2026-07-09 ~01:22 UTC — slot-2: diagnosed, worked around in one-off script, verified end-to-end

Found while re-testing the sibling missing-`.write()` fix — the fix alone wasn't sufficient because of this second,
independent bug. Added an explicit `flush_all_pending_buckets()` call to `understat_eu_residual_closer_2026_07_08.py`'s
`main()` (shipped in the same commit as the sibling fix, `instruments-service@920b303`) as a scoped workaround; re-ran
end-to-end and confirmed via a fresh-process read + forced consolidation that all 4,125 buffered rows persisted
correctly. Filed this doc since the underlying `unified_trading_library` race is unfixed and cross-cutting — out of
scope for this task (understat item #4 checkbox) to fix at the library level.
