---
doc_type: issue
title:
  P0 — compute_completeness_fraction builds a FULL-CORPUS python dict to serve a ONE-ELEMENT lookup, 3x per instrument,
  unmemoized; projects to ~75-100s/call on cefi-prd and likely OOM on the 1.58 GB defi-prd index
summary: >-
  Found while measuring why MDPS candle derivation takes 25.9s per instrument-day. The manifest-flush hypothesis was
  REFUTED by measurement (the per-VM write is already debounced at 50 entries/5.0s and costs ~0.02s and ~47 KB for a
  whole run). The real cost is a READ amplification - canonical_writer's per-timeframe _publish_emission_check calls
  compute_completeness_fraction, which calls _build_capture_status_map(index) - a pure-python loop over EVERY row of the
  whole manifest corpus x 25 row-key columns - to answer a lookup whose upstream_window is literally a 1-element list.
  It runs 3x per instrument (ohlcv_1m/1h/1d are policy-gated from trades), has no memoization, and each manifest flush
  calls _invalidate_index_cache so the next check re-merges. Measured scaling is super-linear - 22,719 rows 0.11s;
  1,454,016 rows 13.14s (9.04 us/row). Measured PROD index sizes - cefi 159.1 MB, defi 1,579.3 MB, tradfi 77.4 MB,
  sports 46.1 MB - versus the 0.44 MB TEST index all the timing work was done against. So the measured 25.9s/instrument
  is a best case on a 3,614x-smaller index than defi prod. Fix is read-path only - filter to the candidate rows before
  building the map, memoize, and thread the already-existing manifest_index= kwarg - so durability, honest-absence
  semantics and the on-disk layout are all untouched.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [unified-trading-library, market-data-processing-service]
scope: [engineer, admin]
tags: [data-correctness, p0, performance, manifest, mdps, backfill-blocker, oom-risk]
related:
  [../data_pipeline_check_mdps_features_2026_07_20.md, mdps_derivative_ticker_candle_schema_violation_2026_07_20.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
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
source: >-
  measured 2026-07-20 while profiling the MDPS candle path for a backfill ETA; prod index sizes verified independently
  by direct `gcloud storage ls -l`.
---

# P0 — a full-corpus map build to answer a one-element lookup

> **The hypothesis this replaces was WRONG, and that matters.** I originally suspected the per-shard manifest flush
> (`_flush_manifest_with_backoff`) was doing an O(n²) read-modify-write. **Measurement refuted it.** Recording that
> plainly so nobody re-litigates the flush.

## What was REFUTED (do not re-open)

`ManifestWriter.flush()` deliberately does **not** force the per-VM rewrite — it debounces (`_writer_io.py:291` →
`_state.py:706 _per_vm_should_write`, default **50 entries OR 5.0s**); only `close()`/atexit pass `process_final=True`.
Shipped 2026-06-21 (`utl@6b6d53bd`, "coalesce per-call final into the debounce — fleet-wide 429 fix"). The live log line
`(8 total entries, 7 new)` **proves the debounce worked**: 7 rows coalesced into ONE rewrite.

Measured against the actual shard the profiled run produced:

| measured                         | value                     |
| -------------------------------- | ------------------------- |
| the run's per-VM shard           | **14 rows, 23,438 bytes** |
| `to_parquet(14 rows)`            | **0.010 s**               |
| rewrites for the whole 51.9s run | **~2**                    |
| total bytes rewritten, whole run | **~47 KB**                |

⇒ the manifest **write** is ~0.02 s of a 51.9 s run. "Batch the flush" was already shipped; per-shard-object / WAL /
async-flush designs would optimise **0.02 s** while adding durability-relevant moving parts. **Rejected on evidence.**

## The REAL cost — read amplification

`canonical_writer.py:416` fires `_publish_emission_check` **per timeframe**. `_resolve_policy_output_data_type`
(`canonical_writer_stamping.py:409-435`) returns non-`None` for `ohlcv_1m`, `ohlcv_1h`, `ohlcv_1d` derived from `trades`
— **3 of 7 timeframes**. That path (`emission_publisher.py:366`, unconditional, no short-circuit) →
`compute_completeness_fraction` → `_build_capture_status_map(index)` (`manifest_completeness.py:157-185`): a
**pure-Python loop over every row of the entire manifest corpus × 25 `_ROW_KEY_COLUMNS`** (`_rows.py:93-168`).

The lookup it serves is **one element** — `_build_ohlcv_1m_upstream_window` returns `return [{...}]`
(`canonical_writer_stamping.py:541`).

> It materialises a hash map of the **entire corpus** to perform **one dictionary lookup**, with **no memoization**,
> **3× per instrument**. And `_flush_per_vm_pending` ends with `_invalidate_index_cache(bucket)` (`_writer_io.py:724`),
> so each flush forces the next check to re-merge (`_read_index.py:566`).

### Measured scaling (super-linear — dict/heap pressure)

| rows      | build time  | µs/row |
| --------- | ----------- | ------ |
| 22,719    | 0.11 s      | 4.68   |
| 90,876    | 0.40 s      | 4.39   |
| 363,504   | 2.45 s      | 6.74   |
| 1,454,016 | **13.14 s** | 9.04   |

Also measured on the real 22,719-row test index: `_merge_shard_frames([canonical, 14-row shard])` = **0.441 s**;
`read_parquet(458 KB)` = 0.027 s.

### Measured PROD index sizes (verified by direct `gcloud storage ls -l`, 2026-07-20)

| bucket                               | index size     | vs the TEST index | projected rows | projected build/call    |
| ------------------------------------ | -------------- | ----------------- | -------------- | ----------------------- |
| **defi-prd**                         | **1,579.3 MB** | **3,614×**        | ~82 M          | ~15 min, **OOM likely** |
| cefi-prd                             | 159.1 MB       | 364×              | ~8.3 M         | **~75–100 s**           |
| tradfi-prd                           | 77.4 MB        | 177×              | ~4.0 M         | ~40 s                   |
| sports-prd                           | 46.1 MB        | 106×              | ~2.4 M         | ~22 s                   |
| **test** (all timings measured here) | **0.44 MB**    | 1×                | 22,719         | 0.11 s                  |

**⚠️ ETA CONSEQUENCE:** the 25.9 s/instrument-day figure used for backfill planning was measured against the **0.44 MB
test** index. On cefi-prd the same code path projects to **~75–100 s per policy-gated timeframe ≈ 4–5 minutes per
instrument**. **Any ETA built on the test-bucket number is optimistic by ~10×** until this is fixed or the projection is
disproved. (Row counts are INFERRED from bytes assuming constant compression; the sizes themselves are MEASURED.)

## Secondary P0 (standalone)

**The defi-prd availability index is 1.58 GB.** Any consumer calling `read_availability_index` on defi without a
column/filter projection is one cache-miss from an OOM — independent of this issue. (`_read_index.py` documents a ~14.86
GiB unfiltered peak on the DeFi index and the slim/filter path as the mitigation.)

## Fix — read-path only, zero durability change

| #      | change                                                                                                                                                                                                                                                                                                                                                                                                     | effect |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| **F1** | In `compute_completeness_fraction` (`manifest_completeness.py:253`), coerce the (typically 1-element) `upstream_window` to key tuples FIRST, vector-filter the DataFrame to the candidate rows (`date` + `data_type` + `instrument_id` are the selective dims), and build the map from that **slice only**. O(corpus×25) → O(window + slice). Keep `_build_capture_status_map` for existing callers/tests. |
| **F2** | Memoize the projected map by index identity (`id(index)` + `len(index)`) in a small bounded dict.                                                                                                                                                                                                                                                                                                          |
| **F3** | MDPS `_publish_emission_check` should read the index **once per instrument-day** and thread it via the **already-existing** `manifest_index=` kwarg (`emission_publisher.py:280`, `manifest_completeness.py:227`) instead of letting all 3 timeframes trigger a read.                                                                                                                                      |

**On-disk layout unchanged.** No migration, no back-compat shim, no new objects, no consolidator change, no
`_index/per_vm/` contract change. **Crash-loss bound identical to today** (≤1 debounce window, drained by
`close()`/atexit with `_emit_atexit_drain_incomplete` on failure). Because the change is on a **read** path,
`record_captured`/`record_empty`/`record_failed`/`record_expected_unattempted`, the honest-absence rules, per-VM
isolation, consolidator merge/dedup, stale-blob liveness and the `captured`-outranks tie-break are **all untouched**.

## Todos

- [ ] 1. [DATA] P0. **VERIFY the prod projection before sizing the win** — is `_publish_emission_check` actually firing
      on prod MDPS backfills (are they ~4–5 min/instrument on cefi), or does a policy/short-circuit disable it in prod?
      The projection is INFERRED from a measured curve + measured sizes, not observed on a prod VM.
- [x] 2. ✅ [SCRIPT] P0. F1+F2 SHIPPED utl@80d2497e (16.7x, value-equivalent, proven). Implement F1 (filtered lookup) +
      F2 (memoize) in `unified-trading-library/…/manifest_completeness.py`.
- [x] 3. ✅ [SCRIPT] P1. F3 shipped mdps@b4db0af as a SAFE optional pass-through (forced snapshot REJECTED — MDPS
      ohlcv_1m self-mutates the shard the ohlcv_1h/24h window reads). Implement F3 in MDPS
      `canonical_writer_stamping.py::_publish_emission_check` (thread `manifest_index=`).
- [x] 4. ✅ [SCRIPT] P1. Tests shipped (equivalence 4-state+sentinel+dup+absent; perf-guard 1.45M<0.5s; memo). Tests:
      (a) equivalence vs `_build_capture_status_map` across all 4 `capture_status` states incl. the
      `_DEDUP_NULL_SENTINEL` NULL≡`""` collapse; (b) perf guard — 1.4 M-row synthetic index,
      `compute_completeness_fraction` < 0.5 s (today: **13.14 s measured**); (c) memoization — 1 build for 3 calls.
- [ ] 5. [DATA] P0. **The 1.58 GB defi-prd index is its own P0** — audit every `read_availability_index` caller on defi
      for a missing column/filter projection (OOM risk), and consider whether the index needs compaction/partitioning.
- [ ] 6. [DOC] P2. Record in codex that the per-VM manifest flush is ALREADY debounced (50 entries/5.0s, `utl@6b6d53bd`)
    so the "flush is O(n²)" hypothesis is not re-derived by the next reader.
</content>

## 2026-07-20 — F1+F2 SHIPPED (16.7x, value-equivalent); F3 premise DISPROVEN

**Shipped:** `unified-trading-library@80d2497e` (F1 filter-then-build + F2 memoize) +
`market-data-processing-service@b4db0af` (F3 safe optional pass-through). **Measured 3.528s -> 0.211s at 1.45M rows
(16.7x, <0.5s)**, value-equivalent to the full-corpus reference across all 4 capture states + the NULL-equals-empty
sentinel + dup last-write-wins + absent key; memo 1 build / 3 calls. Both QGs green. The full speedup applies
AUTOMATICALLY to the existing `_publish_emission_check -> publish_with_manifest_lookup -> compute_completeness_fraction`
path with ZERO MDPS behavior change — no risky snapshot needed.

**F3 SPEC PREMISE WAS FALSE (data-correctness finding).** Todo 3 said "the emission check is a read of UPSTREAM raw-tick
capture state, which the candle write does not change, so a per-instrument snapshot is safe." That is WRONG:
`mdps_data_type_key("trades","1m") == "ohlcv_1m"`, so MDPS's OWN ohlcv_1m candle write emits the exact
`data_type=ohlcv_1m,timeframe=1m` manifest shard that `_build_ohlcv_1m_upstream_window` (for ohlcv_1h/ohlcv_24h) reads.
A per-instrument snapshot taken BEFORE the ohlcv_1m write would give the later ohlcv_1h/24h checks a staler view ->
different completeness fraction -> different emission verdict. So F3 was implemented as an honored optional pass-through
defaulting to None (read-fresh), NOT a forced snapshot. Todo 3 is CLOSED as "pass-through only; forced snapshot rejected
on correctness grounds."
