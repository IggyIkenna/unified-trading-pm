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
assigned_vm: NA
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

- [x] [INVESTIGATE] P0. Root-cause exactly which executor/library is torn down before the manifest module's atexit
      handler runs (candidates: `asyncio`'s default executor, `gcsfs`'s internal thread pool, `google-cloud-storage`
      client transport threads) and confirm whether Python's `atexit` LIFO ordering can be controlled (e.g. registering
      the manifest flush handler EARLIER so it runs LATER, i.e. before dependent executors register their own shutdown)
      or whether the fix must be structural. (repo: unified-trading-library) ✅ — 2026-07-09 (slot-9). **This is NOT a
      LIFO/registration-order race at all — it's a deterministic two-phase CPython shutdown sequence, and reordering
      registrations CANNOT fix it.** `concurrent.futures.thread` registers its `_python_exit` cleanup via the PRIVATE
      `threading._register_atexit()` API, not the public `atexit.register()` — a distinct callback list CPython drains
      in `threading._shutdown()`. Empirically confirmed on the exact production interpreter
      (`cpython-3.13.13-linux-x86_64-gnu`, both service venvs): registering an `atexit.register()` callback BEFORE a
      `threading._register_atexit()` callback still fires the threading one FIRST — `threading._register_atexit`
      callbacks unconditionally precede ALL `atexit.register()` callbacks, regardless of registration order (this is the
      documented bpo-39812 change: "used _instead of_ atexit.register() ... for compatibility with subinterpreters").
      Once `_python_exit()` runs, it sets the MODULE-GLOBAL `concurrent.futures.thread._shutdown` flag — not a
      per-instance flag — so from that point on, ANY `ThreadPoolExecutor.submit()` call anywhere in the process, on ANY
      executor (even a brand-new one), raises exactly
      `RuntimeError: cannot schedule new futures after     interpreter shutdown` (the specific wording confirms the
      module-global check, not the per-instance `"...after shutdown"` variant). **`concurrent.futures.thread` is
      essentially guaranteed to already be imported (and thus its `_python_exit` registered) in every process that
      imports `unified_trading_library`**: package `unified_trading_library/__init__.py:617` does
      `from .core.run_async import run_async_from_sync`, and `unified_trading_library/core/run_async.py:11,18` does
      `from concurrent.futures import ThreadPoolExecutor` + eagerly constructs a module-level
      `_executor = ThreadPoolExecutor(max_workers=4, ...)` at import time — so simply `import unified_trading_library`
      (transitively, via `import unified_trading_library.manifest_writer`) is enough, no explicit executor use required
      by the calling script. **Exhaustively grepped the actual write path** (`ManifestWriter.close()` →
      `_write_to_gcs()` → `get_storage_client()` → `google.cloud.storage.Client` / `google.auth` / `requests` /
      `urllib3`) for any `ThreadPoolExecutor`/`run_in_executor`/`asyncio.to_thread` call — found NONE; none of those
      libraries touch a Python-level thread-pool executor in this call chain (ruling out `gcsfs` — not used here at all,
      `get_storage_client()` wraps the official synchronous `google-cloud-storage` client — and ruling out
      `google-auth`'s `TimeoutGuard`, which is a wall-clock check, not a thread). So the write path itself is not the
      permanent source of a `.submit()` call; the concrete trip in the 2026-07-08/09 incident was most likely a
      transient/in-flight executor use elsewhere in the same process at the moment atexit fired (e.g. an aiohttp
      `ThreadedResolver`-driven DNS lookup still winding down;
      `instruments_service/reference_data/adapters/sports/adapters/base.py:184` wires
      `aiohttp.TCPConnector(resolver=aiohttp.resolver.ThreadedResolver())`, whose `resolve()` calls `loop.getaddrinfo()`
      → `loop.run_in_executor(None, socket.getaddrinfo, ...)`, i.e. asyncio's own lazily-created default executor)
      rather than a deterministic line in the manifest writer. **Practical upshot — same conclusion either way**: the
      atexit-registered `flush_all_pending_buckets()` can NEVER be trusted as a safety net for an asyncio-based script,
      because (a) `concurrent.futures.thread`'s shutdown is guaranteed to run first the instant
      `unified_trading_library` is imported, and (b) whether any GIVEN run actually trips a live `.submit()` call at
      that exact moment is incidental/nondeterministic, not something a fix inside the write path alone can close. **Fix
      must be structural** (confirms option (a) in the sibling [CODE] todo below) — an explicit
      pre-`asyncio.run()`-return drain is the only reliable mechanism; reordering imports/registrations cannot help.
      Reproduction commands + evidence: see Progress Log entry below.
- [x] [CODE] P0. Make the guaranteed drain actually guaranteed for asyncio scripts — either (a) provide + document a
      public "call this before your asyncio.run() returns" helper (formalizing the workaround applied here) that every
      asyncio-based one-off/backfill script is expected to call explicitly, since atexit cannot be trusted post-hoc, or
      (b) fix the executor-teardown race so plain atexit is reliable again. Add a regression test that simulates an
      asyncio script exiting fast with pending per-VM records and asserts the shard is written. (repo:
      unified-trading-library) ✅ — unified-trading-library@baeeff9e (slot-8). Went with option (a), per item #1's
      finding that the race is structural (not fixable by reordering atexit registrations):
      `flush_all_pending_buckets()`'s docstring now documents the explicit-call contract and it's exported from the
      top-level `unified_trading_library` package (was previously reachable only via the `manifest_writer` submodule).
      Also added a `MANIFEST_ATEXIT_DRAIN_INCOMPLETE` structured event (emitted from `_write_to_gcs`'s existing
      except-block, gated on `process_final=True`) so a guaranteed-drain failure is machine-detectable instead of only
      the pre-existing `logger.warning` line — this closes the "why it matters #2" silent-loss gap even for scripts that
      still rely on bare atexit. Two regression tests in `tests/unit/test_manifest_writer_atexit_asyncio_drain.py`: (1)
      calling `flush_all_pending_buckets()` from inside a still-running `asyncio.run()` coroutine persists a debounced
      per-VM shard remainder correctly; (2) a simulated upload failure (the exact production `RuntimeError` text) during
      the guaranteed drain now emits the new event with accurate row counts. Full `quality-gates.sh` green.
- [x] [SCRIPT] P1. Audit other asyncio-based one-off/backfill scripts under `instruments-service/scripts/backfill/` (and
      sibling repos) for the same reliance-on-bare-atexit pattern; apply the same explicit-pre-exit-drain workaround to
      any that matter for an active plan's gate, pending the real fix above. (repo: instruments-service) ✅ —
      instruments-service@a745898 (slot-11). See Progress Log entry below for the audit methodology + findings.
- [x] [SCRIPT] P2. Add a QG check that greps for `asyncio.run(` in a script alongside `MANIFEST_PER_VM_SHARDS` env usage
      and requires an explicit `flush_all_pending_buckets()` call in the same file, to catch new instances of this
      anti-pattern going forward. (repo: unified-trading-pm) ✅ — 2026-07-09 (slot-13). Added
      `scripts/quality_gates/check_asyncio_manifest_explicit_drain.py` (QG STEP 5.103 — 5.102 was claimed concurrently
      by the sibling manifest_early_return_missing_write_loss checker; wired into
      `scripts/quality-gates-base/base-service.sh` so every repo's own gate run scans itself) — flags any `.py` file
      containing both `asyncio.run(` and `MANIFEST_PER_VM_SHARDS` but no `flush_all_pending_buckets(` call. Per-repo
      SHRINKING baseline ratchet (`asyncio_manifest_explicit_drain_baseline.yaml`); item #3's audit (instruments-
      service@a745898, concurrent with this task) fixed 2 of the original 3 known offenders, leaving 1
      (`scripts/recover_fixtures_from_truthset.py`) — baseline seeded at 1, matching the live re-scan; per-file opt-out
      `# noqa: qg-asyncio-manifest-drain`. `unified-trading-pm@0452119bb` (checker + tests: `d863e01d6`; wiring:
      `0452119bb`); 10 unit tests pass; full `quality-gates.sh --no-fix` green (STEP 5.103 ✅).

## Progress Log

### 2026-07-09 ~03:0x UTC — slot-9: item #1 (INVESTIGATE) — root cause is a deterministic two-phase shutdown, not a LIFO race

**Task**: `manifest_atexit_drain_races_asyncio_shutdown-001` (item #1).

**Method**: static analysis of the write call chain (`ManifestWriter.close()` → `_write_to_gcs()` in
`unified_trading_library/manifest_writer/_writer_io.py`) across `unified-trading-library`, `google-cloud-storage`,
`google-auth`, `requests`/`urllib3` (all in the real service venv, Python 3.13.13) to find every
`ThreadPoolExecutor`/`run_in_executor`/`asyncio.to_thread` call site, plus a direct empirical reproduction of CPython's
atexit ordering on the exact interpreter build used in production (`cpython-3.13.13-linux-x86_64-gnu`).

**Key reproduction** (run standalone, no GCS credentials needed):

```python
import atexit, threading
def atexit_marker(): print("FIRED: atexit.register callback")
def threading_marker(): print("FIRED: threading._register_atexit callback")
atexit.register(atexit_marker)          # registered FIRST
threading._register_atexit(threading_marker)  # registered SECOND
# exiting now — LIFO would predict atexit_marker fires first (it was registered
# first, so LIFO/atexit's own "last-in-first-out" would place its "later"
# registrant, threading_marker, ahead of it -- but threading._register_atexit
# is a SEPARATE list entirely, drained by threading._shutdown() at a fixed,
# always-earlier point in interpreter finalization):
```

Output: `FIRED: threading._register_atexit callback` always prints before `FIRED: atexit.register callback`, regardless
of which was registered first — confirmed on both this host's `/usr/lib/python3.12` and the actual production venv's
`cpython-3.13.13-linux-x86_64-gnu`.

**Root cause** (see the checked-off todo above for the full writeup): `concurrent.futures.thread` registers its
worker-thread-joining cleanup (`_python_exit`, which sets the MODULE-GLOBAL `_shutdown=True`) via the private
`threading._register_atexit()` API specifically BECAUSE (per its own source comment, bpo-39812) it must run before
regular `atexit.register()`-registered functions, not after. `unified_trading_library/__init__.py:617` →
`core/run_async.py:11,18` guarantees `concurrent.futures.thread` is imported (and `_python_exit` registered) the moment
`unified_trading_library` itself is imported — no explicit executor use required by the calling script. So by the time
`flush_all_pending_buckets()` (registered via plain `atexit.register()`) runs, `_python_exit()` has ALWAYS already
fired, and any live `ThreadPoolExecutor.submit()` call anywhere in the process from that point on raises
`RuntimeError: cannot schedule new futures after interpreter shutdown` — matching the exact wording slot-2 observed (the
module-global check's message, distinct from the per-instance `"...after shutdown"` variant).

**Did not find** an explicit thread-pool call inside the manifest write path itself (`get_storage_client()` →
`google.cloud.storage.Client` → `blob.upload_from_string`, or `google.auth`'s `TimeoutGuard`, which is a wall-clock
check, not a thread) — ruling out `gcsfs` (not used; `get_storage_client()` wraps the official sync client) and ruling
out the GCS/auth transport layers as a _permanent_ trigger. Strongest candidate for the actual trip observed by slot-2:
`instruments_service/reference_data/adapters/sports/adapters/base.py:184`'s
`aiohttp.TCPConnector(resolver=aiohttp.resolver.ThreadedResolver())` — `ThreadedResolver.resolve()` calls
`loop.getaddrinfo()` → `loop.run_in_executor(None, ...)`, i.e. asyncio's own lazily-created default executor, which
could still have in-flight work at the exact moment the atexit-registered flush ran.

**Conclusion for the sibling [CODE] todo**: the LIFO-ordering angle is a dead end — it cannot be "fixed" by
re-registering the manifest flush earlier/later, because `threading._register_atexit` and `atexit.register` are two
separate lists with a fixed relative order, not one LIFO stack. The only reliable fix is structural: an explicit
pre-`asyncio.run()`-return drain (formalizing slot-2's workaround) for every asyncio-based script, since the
atexit-based "guarantee" is provably unreliable for any process that imports `unified_trading_library` (i.e., all of
them). No code shipped this session — this was an INVESTIGATE-only todo; the next todo ([CODE] P0) should implement the
explicit-drain helper.

### 2026-07-09 ~01:22 UTC — slot-2: diagnosed, worked around in one-off script, verified end-to-end

Found while re-testing the sibling missing-`.write()` fix — the fix alone wasn't sufficient because of this second,
independent bug. Added an explicit `flush_all_pending_buckets()` call to `understat_eu_residual_closer_2026_07_08.py`'s
`main()` (shipped in the same commit as the sibling fix, `instruments-service@920b303`) as a scoped workaround; re-ran
end-to-end and confirmed via a fresh-process read + forced consolidation that all 4,125 buffered rows persisted
correctly. Filed this doc since the underlying `unified_trading_library` race is unfixed and cross-cutting — out of
scope for this task (understat item #4 checkbox) to fix at the library level.

### 2026-07-09 ~02:xx UTC — slot-11: item #3 (SCRIPT audit) — 3 more scripts fixed, 1 checked-and-skipped

**Task**: `manifest_atexit_drain_races_asyncio_shutdown-003` (item #3, [SCRIPT] P1).

**Method**: `grep -rl MANIFEST_PER_VM_SHARDS instruments-service/scripts` → 52 hits, then narrowed to `asyncio.run(`
callers only (4 hits: the already-fixed `understat_eu_residual_closer_2026_07_08.py` + 3 unfixed). Cross-checked
`sibling repos` per the todo's wording — grepped `MANIFEST_PER_VM_SHARDS` across every other repo in the workspace
(`deployment-api`, `deployment-service`, `features-service`, `market-data-processing-service`,
`market-tick-data-service`, `unified-trading-library`, `unified-api-contracts`); none of their hits call `asyncio.run(`
— the bare-atexit-reliance pattern is confined to `instruments-service` one-off scripts.

**Fixed** (`instruments-service@a745898`):

- `scripts/backfill/understat_bulk_backfill.py` — async `main()` had no explicit drain before its final log line; added
  `_mw.flush_all_pending_buckets()` right before `=== ... COMPLETE ===`, matching the sibling closer script's pattern
  exactly. Actively gates `plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md` (status: active).
- `scripts/backfill_understat_xg_epl_2025_2026_06_29.py` — different shape: sync `main()` calls
  `asyncio.run(_run_backfill(...))`, so the drain has to run **inside** the `_run_backfill` coroutine (before it
  returns), not after `asyncio.run()` in the outer sync `main()` — the loop (and any executors it owns) is already torn
  down by the time `asyncio.run()` hands control back. Added the `_mw` import + explicit flush at the end of
  `_run_backfill()`. Its issue doc (`sports_data_capture_gap_2026_06_29.md`) has all 4 todos checked but no final
  re-verify confirming the XG backfill's result stuck — applied the fix defensively since the cost is zero and the
  script could still be re-run.
- `scripts/recover_fixtures_from_truthset.py` — **different bug shape, same root cause.** This script already calls an
  explicit `manifest.flush()` before returning (looks like it already had the "explicit drain" pattern) — but
  `ManifestWriter.flush()` docstring is explicit that it does **NOT** force the per-VM shard rewrite, only the
  module-buffer/legacy-CAS write; the per-VM shard's "true finality" is deliberately left to `close()`/atexit
  (`process_final=True`). So this script's existing `.flush()` call gave a false sense of safety — it was still exposed
  to the exact atexit race for the per-VM shard specifically. Swapped `manifest.flush()` → `manifest.close()` so the
  guaranteed drain runs explicitly, in-loop. **This script is NOT dead despite its own `Delete-when` marker and parent
  plan (`sports_fixtures_truthset_recovery_2026_05_06.md`) being archived** — it's actively referenced as a
  still-to-be-re-run recovery tool in the plan (now archived, superseded by
  `sports_consolidated_closeout_2026_07_19.md`)
  `plans/archive/2026_07/sports_p2_history_apifootball_2015_to_present_2026_06_27.md` (line ~487: "generate a fresh
  truthset ... → run `recover_fixtures_from_truthset.py --flip-empty-attempts`"). Worth flagging: don't trust a script's
  own `Lifecycle`/`Delete-when` header as proof of deadness — grep for its filename across `plans/active/` before
  assuming it's safe to skip or delete.

**Checked, not fixed** — `scripts/recover_fixtures_from_truthset.py`'s own sibling from the same Phase-1/Phase-2
recovery effort has no other asyncio-based counterparts; no other candidate scripts were found once the `asyncio.run(`
filter was applied, so no further scripts in this repo needed the workaround.

Shipped: `instruments-service@a745898` (QG green, quickmerge --agent). This todo does not fix the underlying
`unified_trading_library` race (that's [CODE] P0, still open) — it's the scoped mitigation across every currently-live
asyncio one-off script, same as the sibling closer-script fix.
