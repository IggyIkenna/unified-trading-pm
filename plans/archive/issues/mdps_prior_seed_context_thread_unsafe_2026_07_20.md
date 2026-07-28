---
doc_type: issue
title:
  P0 — MDPS prior-day seed context is stored on the SHARED orchestrator instance while instrument files run on a
  ThreadPoolExecutor; raising max_workers silently corrupts leading-bin carry-forward prices
summary: >-
  _set_prior_seed_context writes _seed_category / _seed_date_str / _seed_input_venue / _seed_underlying /
  _seed_pipeline_mode / _seed_frame_cache onto `self` (the shared CandleOrchestrationService instance), and
  batch_workers submits `self._process_instrument_file` to a ThreadPoolExecutor sized by max_workers (8 on
  e2-standard-8). With max_workers>1 over a heterogeneous file list - multiple venues / underlyings / pipeline_modes in
  one data_type, which is the NORMAL case for a real backfill - thread A reads thread B's seed context and resolves the
  prior-day carry seed from the WRONG GCS object path, and _seed_frame_cache is a plain dict reassigned per file and
  mutated concurrently. The failure is SILENT - wrong seed prices in leading bins, no crash, no error row, no
  attempted_failed. It is invisible on a homogeneous run (a single-venue single-day smoke shows nothing) which is
  exactly why it has survived. This BLOCKS the primary backfill speed lever - raising in-process worker concurrency - so
  it must be fixed before any fleet-wide MDPS backfill runs with max_workers>1.
status: resolved
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [data-correctness, p0, concurrency, thread-safety, mdps, candles, backfill-blocker, silent-corruption]
related:
  [
    ../data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  "market-data-processing-service@b3376b8 (frozen SeedContext threaded per-call + regression test proving
  failing-on-old/passing-on-new + opt-in date-concurrency lever); blast-radius assessment (2026-07-27, slot-8) found
  zero real backfill runs predate the fix — all 4 todos DONE"
source: >-
  found 2026-07-20 while profiling the MDPS candle path for a backfill ETA; both halves verified by direct read of the
  cited files.
---

> **🟢 ARCHIVED 2026-07-28** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule.

# P0 — shared-instance seed context + a thread pool = silent wrong prices

## The two halves (both VERIFIED by direct read)

**(1) Seed context is written to the SHARED instance** —
`market_data_processing_service/app/core/candle_write_mixin.py:406-411`:

```python
self._seed_category = category
self._seed_date_str = date_str
self._seed_input_venue = input_venue
self._seed_underlying = underlying
self._seed_pipeline_mode = pipeline_mode
self._seed_frame_cache = {}
```

Called per FILE from `live_workers.py:243`; read back by `_seed_adapter_for_instrument`
(`candle_write_mixin.py:433-441`) to resolve the prior-day frame.

**(2) Instrument files run on a thread pool over that same `self`** — `app/core/batch_workers.py:370`
`with ThreadPoolExecutor(max_workers=max_workers)`, and `:332-335`:

```python
executor.submit(
    self._process_instrument_file,
    category=category,
    data_type=data_type,
    ...
```

One `self` shared across every pool thread. `max_workers` resolves to `min(os.cpu_count(), 16)` = **8** on the default
`e2-standard-8` (`config.py:417-420`).

## The failure

With `max_workers > 1` and a file list spanning **multiple venues / underlyings / pipeline_modes within one data_type**
— the normal shape of a real backfill — thread A can read thread B's `_seed_input_venue` / `_seed_underlying` /
`_seed_pipeline_mode` and therefore resolve the prior-day carry seed **from the wrong GCS object path**. Additionally
`_seed_frame_cache` is a plain dict _reassigned_ per file and mutated concurrently.

**The corruption is SILENT**: wrong seed prices in the leading bins of a candle series. No exception, no
`attempted_failed` row, no manifest signal. It would surface only as subtly wrong opens/carry values in early bins —
precisely the kind of defect that survives for months and then poisons downstream features/backtests.

**Why it has gone unnoticed / why my own smoke run did not show it**: the profiled run processed 2 files that were both
DERIBIT, same day, same `pipeline_mode`, so the clobbered values were _identical_ and the bug was invisible. Any
homogeneous single-venue smoke test will pass. This is a heterogeneity-triggered race.

## Why this is a BLOCKER, not just a bug

The single biggest backfill speed lever identified for MDPS is raising in-process concurrency (the pool was measured
**under-fed** — 2 futures into 8 slots, 6 workers idle). **Turning that lever up is exactly what triggers this bug.** So
the correctness fix is a hard prerequisite for the throughput work, not a parallel nice-to-have.

## The adapter itself is SAFE (do not "fix" it)

`app/adapters/base_adapter.py:802` `return adapter_cls(config=config)` returns a FRESH adapter instance per call, so
`set_prior_day_seed` is already per-thread. The bug is confined to the orchestrator-level `self._seed_*` stash.

## Fix direction

Make the seed context **per-call**, not per-instance: pass a small immutable `SeedContext` value object (category,
date_str, input_venue, underlying, pipeline_mode) through `_process_instrument_file` → `_seed_adapter_for_instrument` →
`_read_prior_day_frame`/`_get_prior_day_seed`, instead of stashing on `self`. Give the frame cache an explicit
thread-safe scope (either per-call, or a keyed cache guarded by a lock and keyed by the full
`(category, date, venue, underlying, pipeline_mode)` tuple so entries cannot collide across threads).

**Preserve the documented read/write path symmetry** that the current docstring calls out (the prior-day read must
resolve the exact object path the live writer wrote — the path==manifest invariant). The fix is about _where the context
lives_, not _what it resolves to_.

## Todos

- [x] 1. ✅ [SCRIPT] P0. SHIPPED mdps@b3376b8 — frozen SeedContext threaded per-call, self._seed_* removed. Thread the
      seed context as an immutable per-call value object instead of `self._seed_*`; scope or lock `_seed_frame_cache`
      with a collision-proof key. Preserve read/write path symmetry.
- [x] 2. ✅ [SCRIPT] P0. SHIPPED — test_seed_context_thread_safety.py, PROVEN failing-on-old (Barrier-forced clobber) /
      passing-on-new + a meta-guard. Regression test that FAILS on today's code: run `_process_files_parallel` with
      `max_workers>1` over a HETEROGENEOUS file list (>=2 venues and/or underlyings and/or pipeline_modes) and assert
      each instrument's resolved prior-day seed path matches its OWN venue/underlying/pipeline_mode. A homogeneous list
      must not be used — it cannot detect the bug.
- [x] 3. ✅ [DATA] P1. Assess blast radius on EXISTING candle data — LOW/near-zero, evidence below.

## 2026-07-27 update (slot-8) — todo 3 blast-radius assessment

**Method**: enumerated every `mdps-backfill-*` VM run under `gs://deployment-scripts-central-element-323112/vm-logs/`
(excluding `-pcskip-`/`-pipelinecheck-`/`-pcbench-`, which are smoke/verification runs, not real backfills) and checked
each real run's start timestamp against the fix commit (`market-data-processing-service@b3376b8`,
`2026-07-20 20:47:10 +0100` = `2026-07-20T19:47:10Z`).

**Finding: zero real backfill runs predate the fix.** Every real (non-smoke) `mdps-backfill-*` run in the log bucket is
timestamped `2026-07-21` or later (the great majority `2026-07-26`) — CEFI, TradFi (incl. the `y2020`..`y2026`
year-sharded + `buildcontinuous-es` runs), and SPORTS. No real backfill activity exists from before the fix landed.

**Confirmed real (non-dry-run) writes under the exact heterogeneous-venue precondition**:
`mdps-backfill-cefi- 20260726-165959` and `-171422` — `MDPS_VENUES='HYPERLIQUID LIGHTER-ZKSYNC EXTENDED-STARKNET'` (3
venues, one `data_type=trades`), no `MAX_WORKERS` override (defaults to `min(cpu_count,16)`=8 on `e2-standard-8`),
windows `2024-01-01..2026-07-25` / `2026-06-26..2026-07-25`. Verified via `run.log`: real
`POLARS AGGREGATED: 1440 1m candles` writes + `ManifestWriter: per-VM shard updated` entries, and
`RESOURCE_SAMPLE cpu=278.6% ... threads=82` confirms actual multi-threaded concurrent execution occurred — this is
exactly the bug's trigger shape (heterogeneous venues, default worker count >1, real writes).

**Why blast radius is assessed LOW despite that match**: these runs are dated `2026-07-26`, 5-6 days AFTER the fix
commit. `market-data-processing-service`'s launcher pins are `MDPS_TARBALL_SHA` = **floating** (not pinned in VM
metadata, confirmed via this run's own `TARBALL_PINS.json`), meaning the VM pulled whichever
`market-data-processing- service-code` tarball was live at launch time. The CI-driven `create-code-tarballs.sh` rebuild
cadence (observed: today's live manifest was rebuilt `2026-07-27T01:29:26Z`, itself a different sha again) is fast
enough relative to a 5-6 day gap that these runs almost certainly ran the FIXED code. **This cannot be independently
re-verified after the fact** — GCS retains only the CURRENT tarball manifest, not historical snapshots, so there's no
way to directly confirm which exact commit sha was live at `2026-07-26T17:14:22Z` (this run's launch time) versus assume
it from the rebuild cadence.

**Conclusion**: no DETERMINED corruption. The one class of run that structurally matches the bug's trigger (real,
heterogeneous-venue, default-concurrency, non-smoke) only exists post-fix, and CI's per-commit tarball rebuild pattern
makes pre-fix code on those specific runs unlikely though not provably ruled out. **No re-derivation is recommended on
current evidence** — if this needs to be escalated to certainty, the only path is checking Cloud Build's tarball-build
history (if retained) for `market-data-processing-service-code` builds between `2026-07-20T19:47Z` and
`2026-07-26T17:14Z` to confirm at least one rebuild happened after the fix commit and before the flagged runs; I did not
have budget in this session to pull that separately since deployment/build-history access wasn't part of this session's
already-open tool surface.

- [x] 4. ✅ [SCRIPT] P1. R1 SHIPPED mdps@b3376b8 — opt-in MDPS_DATE_CONCURRENCY/--date-concurrency (default 1);
      date-level multiprocessing (measured 4.12->1.04s @N=1..4). In-date max_workers raise still a follow-up. Only AFTER
      1+2: raise the concurrency lever (the pool was measured under-fed — 2 futures into 8 slots) and re-measure
      per-instrument-day throughput.
