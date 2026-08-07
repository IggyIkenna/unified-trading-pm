---
doc_type: issue
title: >-
  `ManifestWriter.add()`/`write()`/`_drain()` have NO internal thread-safety — a shared writer across a
  `ThreadPoolExecutor` races, duplicating staged rows exponentially until OOM (dead `self._write_lock`)
summary: >-
  The `dex_swaps` legacy data_type fold VM (`backfill-defi-legacy-datatype-fold-20260806-072135`) OOM-killed
  (exit_code=137) at 1200/27549 shards after ~55 clean minutes. Root cause: `ManifestWriter.add()` does an unprotected
  `self._records.append()` + check-then-act auto-flush (`if len(self._records) >= batch_size: self.write()`), and
  `write()`/`flush()`/`close()` all funnel through `_drain()`, which reads + clears a module-level pending buffer with
  no lock serializing concurrent callers on the SAME instance. The fold script shares ONE `ManifestWriter` across 24
  `ThreadPoolExecutor` workers (a documented, common pattern in this codebase — see
  `migrate_legacy_gas_fees_venue_2026_07_30.py` and others). `ManifestWriter.__init__` already declares
  `self._write_lock = threading.Lock()` with a comment stating its exact intended purpose ("protects against
  multi-thread writers within one process trampling each other's shard") — but it is NEVER acquired anywhere in
  `add()`/`write()`/`flush()`/`close()`/`_drain()` (confirmed via `grep -n "_write_lock"` across
  `unified_trading_library/manifest_writer/*.py`: only the declaration and a docstring comment reference it). This is a
  SIBLING bug to `mdps_full_mode_reprocess_manifest_cache_oom_2026_08_03.md` (resolved) — same class (ManifestWriter +
  concurrent threads → OOM), different mechanism (that one was `lookup()`'s unfiltered full-schema cache reload; this
  one is `add()`'s unprotected `self._records` mutation + per-VM-shard staging race) — filed separately because the fix
  and blast radius are distinct.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer]
tags: [manifest-writer, thread-safety, concurrency, oom, race-condition, vm, defi]
related:
  [
    /plans/archive/issues/mdps_full_mode_reprocess_manifest_cache_oom_2026_08_03.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
  ]
created: "2026-08-06"
author: unknown
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
source: >-
  Interactive session 2026-08-06, discovered while relaunching the dex_swaps legacy data_type fold VM (part of the DeFi
  distinct-values zero-non-canonical dispatch) — the VM crashed OOM and the log's per-flush "new" row count (123k ->
  246k -> 492k -> 985k -> 1.97M, roughly doubling each cycle) was the tell.
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    unified-trading-library/unified_trading_library/manifest_writer/_writer.py,
    unified-trading-library/unified_trading_library/manifest_writer/_writer_io.py,
    unified-trading-library/unified_trading_library/manifest_writer/_writer_ingest.py,
    unified-trading-library/unified_trading_library/manifest_writer/_state.py,
    market-tick-data-service/scripts/fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py,
    /plans/archive/issues/mdps_full_mode_reprocess_manifest_cache_oom_2026_08_03.md,
  ]
---

# `ManifestWriter` shared-across-threads race — dead `self._write_lock` (2026-08-06)

## What happened

`backfill-defi-legacy-datatype-fold-20260806-072135` (SPOT, e2-standard-4, `--only dex_swaps --workers 24`) ran cleanly
for ~55 minutes, logging steady `progress: N/27549 shards done` checkpoints every ~6-12 minutes with `missing_source=0`
throughout. The per-VM-shard flush log (`ManifestWriter: per-VM shard updated (%d total entries, %d new, ...)`) shows
`total entries` climbing smoothly (~500/flush) from the earliest logged flush through **123,229 total entries** — then
the **"new" count for that single flush jumps to 245,955**, then successive flushes show **492,411 → 985,322 →
1,973,150** ("new" roughly doubling every ~1-2 minutes) while `total entries` barely moves (123,229 → 126,238 over the
same window). The process was SIGKILL'd (`rc=137`) ~4 minutes after the anomaly started;
`VM_SHUTDOWN_ON_COMPLETION=true` self-deleted the VM.

## Root cause

1. `ManifestWriter.add()` (`_writer_ingest.py:357`) does `self._records.append(record)` with **no lock**, then
   (`:412-413`) `if self._batch_size > 0 and len(self._records) >= self._batch_size: self.write()` — a classic
   check-then-act race when called concurrently.
2. `write()` (`_writer_io.py:295`) itself further mutates `self._records` unprotected
   (`_add_to_write_buffer(...); self._records = []`) before calling `_drain()`.
3. `_drain()` (`_writer_io.py:357`, the shared tail for `write()`/`flush()`/`close()`) reads a **module-level** pending
   buffer (`_get_pending_records(bucket)`), calls `_mark_flushed(bucket)`, and writes — with no lock around the
   read-then-mark sequence **for this instance**. Two threads concurrently reaching `_drain()` on the SAME
   `ManifestWriter` can each read overlapping/duplicate snapshots of pending records before either marks them flushed,
   double-staging the same rows into the per-VM-shard pending buffer
   (`_per_vm_add_pending`/`_per_vm_drain_pending`/`_per_vm_shard_lock` in `_state.py`) — that layer's own locking is
   correct in isolation, but it faithfully persists whatever it's handed, including duplicates from the layer above.
4. `ManifestWriter.__init__` (`_writer.py:189-192`) declares exactly the lock that would prevent this:
   ```python
   # Same-process write-path lock — protects against multi-thread writers within one process trampling each other's shard.
   self._write_lock = threading.Lock()
   ```
   `grep -rn "_write_lock" unified_trading_library/manifest_writer/*.py` returns only this declaration + a docstring
   mention in `_state.py:650,668` (itself noting the lock "never [serialized cross-instance writers]" — an
   acknowledgment of a _different_, already-addressed gap via `_PER_VM_SHARD_LOCKS`, not this one). **`self._write_lock`
   is never `.acquire()`'d or used in a `with` block anywhere in the class.**

This is the exact scenario the lock's own comment describes, just never wired up.

## Verification

Isolated reproduction (not the full fold script — direct `ManifestWriter.add()` stress test, 24 threads × 50 calls each
= 1200 genuinely-distinct rows, run against a disposable per-VM shard path, cleaned up after): confirms the class IS
vulnerable to this pattern in principle, and confirms a caller-side lock around every `add()` call (see Immediate
mitigation below) eliminates it — 1200/1200 rows landed, zero duplication, with the caller-side lock in place.

## Impact / who else is exposed

Any script that shares ONE `ManifestWriter` instance across a `ThreadPoolExecutor` (a common, documented pattern in this
codebase — `migrate_legacy_gas_fees_venue_2026_07_30.py`, `fold_legacy_composite_venue_objects_2026_07_31.py`, and
others follow the same shape) is exposed to this race whenever concurrent `add()` calls cross a `batch_size` threshold
or a per-VM debounce window closely enough to interleave. It is timing-dependent — this run went ~55 clean minutes (~74
flushes, ~123K registrations) before the bad interleaving hit, so absence of symptoms in a short/small run is not proof
of safety.

## Immediate mitigation (shipped, script-level only)

`market-tick-data-service@94e625c7` — `fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py` now serializes its
`recorder.add(...)` call site with a `threading.Lock()` held by the caller. This only serializes the (cheap) manifest
registration call, not the per-shard GCS download/write work, so it preserves virtually all of the 24-way I/O
parallelism. This is a workaround for ONE script, not a fix for the shared library — every other script with the same
sharing pattern remains exposed until the library itself is fixed.

## Recommended decision

Two independently-shippable angles (do NOT bundle — mirrors the sibling doc's own framing):

1. **Per-script mitigation** (done for the fold script above): wrap the shared writer's `add()` call site in a
   caller-side lock. Cheap, safe, but must be repeated by hand in every script with this sharing pattern — an easy thing
   to forget on the next one.
2. **Root-cause fix (library-level, broader scope)**: wire up the already-declared `self._write_lock` around the
   critical sections in `add()`/`write()`/`close()`/`_drain()` so `ManifestWriter` is actually safe to share across
   threads, matching what its own comment already promises. Needs `threading.Lock()` → `threading.RLock()` (since
   `write()`/`close()` each do their own pre-`_drain()` mutation before calling into `_drain()`, which would deadlock
   under a plain `Lock` if both callers and `_drain()` itself acquire it) and care around the exact lock scope so it
   doesn't reintroduce the `_PER_VM_SHARD_LOCKS` cross-instance problem `_state.py`'s comment already solved separately.
   This is the fix that removes the footgun for every future caller instead of relying on each script remembering to
   protect itself.

## Todos

- [x] ✅ [DIAG] P2. Audit other `ThreadPoolExecutor`-sharing-one-`ManifestWriter` scripts
      (`migrate_legacy_gas_fees_venue_2026_07_30.py`, `fold_legacy_composite_venue_objects_2026_07_31.py`, and any
      others found via `grep -rl "ManifestWriter(" --include=*.py | xargs grep -l ThreadPoolExecutor`) for the same
      unprotected-shared-writer pattern; apply the same caller-side lock mitigation to each until item 2 below lands.
      **Extracted into `defi_satellite_ao_dispatch_batch10_2026_08_06.md` — SHIPPED 2026-08-07 (slot-9): 12 scripts
      audited, 0 needed mitigation (all confirmed safe — see batch10 plan's inline evidence for per-script reasons).**
- [x] ✅ [INFRA] P1. Wire up `self._write_lock` (converted to `RLock`) around `add()`/`write()`/`close()`/`_drain()`'s
      critical sections in `unified_trading_library/manifest_writer/`, add a regression test that reproduces this race
      (N threads × M distinct `add()` calls on one shared instance, assert row count == N×M with no duplication —
      mirrors this doc's own verification), run full `quality-gates.sh`. Once landed, the per-script caller-side locks
      (item 1 + the fold script's own) become redundant but harmless (a caller-side lock plus an internal `RLock` do not
      deadlock or conflict) — safe to remove opportunistically, not urgent to. **Shipped:
      `unified-trading-library@85bd0354` (batch10 Todo 1, slot-9 earlier session). Regression test: 10 threads × 50
      calls → 500 rows, no duplication.**

## Progress Log

- **interactive session 2026-08-06**: filed after root-causing + fixing (script-level) the dex_swaps fold VM crash;
  cross-referenced the sibling resolved doc (`mdps_full_mode_reprocess_manifest_cache_oom_2026_08_03.md`) for precedent
  and naming. Not yet triaged into the library-level fix (item 2) — flagged, not executed, given the scope (touches a
  widely-shared library method set) warrants its own dedicated pass rather than a rushed edit under this session's
  immediate VM-relaunch pressure.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA-STALE (already-duplicated) — both open checkboxes are
  extracted near-verbatim into `defi_satellite_ao_dispatch_batch10_2026_08_06.md:81-93` (explicit `Source:` citations
  there), still `status: draft` pending operator approval. Per the conflict-check protocol, NOT reclassified — flipping
  `assigned_vm` here would open a second, redundant dispatch path for the identical fix the moment batch10 activates.
  Citations added inline on both checkboxes above. Recommend a future audit re-check batch10's approval status; if it
  lapses without landing this content, re-run this doc through RECLASSIFY instead of leaving it stale-duplicated
  indefinitely. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-07**: populated/refreshed context_scope (6 entries).
- **slot-9 2026-08-07** (batch10 DIAG P2): Full grep audit of market-tick-data-service scripts for
  ThreadPoolExecutor+ManifestWriter sharing — 12 scripts checked (11 grep matches + 1 named script without TPE). All
  confirmed safe, 0 needed caller-side lock mitigation (library fix @85bd0354 also already in). Both todos closed — this
  issue is FULLY RESOLVED.
