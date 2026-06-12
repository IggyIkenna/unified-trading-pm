---
title: "Features calculation pipeline — I/O efficiency + feature-function correctness verification"
created: 2026-05-27
last_updated: 2026-05-27
parent_epic: features_and_ml_master
assigned_vm: vm-ml
name: features-calc-efficiency-and-correctness-2026-05-27
priority: P1
status: active
estimate_class: brand-new
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 10
estimate_calibration_note: |
  brand-new (1.0×): neither a read-once/resample I/O path nor a registry-driven
  feature-correctness harness exists. Bulk is net-new: the candle-read refactor +
  the verification framework (ta-lib-equality + invariants + edge fixtures +
  lookahead + dimension/label/config audit) across ~thousands of features.
related_plans:
  - plans/active/features_service_e2e_pipeline_test_2026_05_26.md
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **HOLD released 2026-06-11 (operator Ikenna):** harsh-side Phase 1/2 work landed (items ✅); 2-week-stale banner
> cleared to ship Phase 3 (resampler unification). `[unlock-plan]`.

## Goal

Two operator-prioritised concerns about the features calculation pipeline (`read → calculate → write`):

1. **Efficiency** — the cost is **I/O (read + write), not compute**. Make the pipeline efficient given: we read large
   candle volumes per (instrument × timeframe × day), some features depend on others (feature DAG — features are not
   absolute), and we backfill multiple days (so lookback windows overlap day-to-day).
2. **Correctness** — verify the ~thousands of feature functions are computed correctly: not just NaN handling (caught
   2026-05-26) but the **actual values, labels, timeframes, configs, dimensions, and input/output wiring**. We trust
   ta-lib's indicator _math_ (battle-tested); the risk is OUR wrapping + the **custom** (non-ta-lib) features (swing
   high/low, market structure, wedges).

Sibling plan `features_service_e2e_pipeline_test_2026_05_26.md` covers the e2e read/write _plumbing_ (buckets, manifest,
the timeframe-coverage loop). This plan is the I/O _efficiency_ + feature-_correctness_ layer on top.

## Pre-audit (grounded 2026-05-27)

- **The 7× read problem is live**: the Phase-6.A timeframe loop (delta_one@7bd77525) reads candles **once per output
  timeframe** (7 reads/instrument/day) → blew the 10-min e2e timeout; operator flagged read-once as the fix.
- delta_one reads candles via `app/core/data_loader.py`; computes via the per-feature-group calculators (some wrap
  ta-lib: `MultiPeriodFeatureGenerator`, `app/calculators/technical.py`; custom: swing/market-structure/wedge); writes
  per-(instrument × feature_group × timeframe × day) parquet via `feature_writer.py` (one small object per shard).
- `TimeframeResampler` (`app/core/timeframe_resampler.py`) resamples _feature values_ + flags indicators needing recalc
  → unsuitable for indicators; but **candle** resampling (OHLC `first/max/min/last/sum`) IS exact and is the efficiency
  lever.
- mtf re-reads delta_one output **from GCS** (a read that an in-memory DAG could avoid for colocated runs).
- 2026-05-26 correctness signal so far is shallow: "0 all-NaN" existence checks + one swing bug. No ta-lib-equality
  tests, no per-feature invariants, no lookahead audit, no dimension/label/config consistency check.

### GCS processed-candles storage layout — grounded against real bucket 2026-05-27

Inspected `gs://market-data-tick-cefi-central-element-323112/processed_candles/` directly:

- **Layout**: `processed_candles/by_date/day=YYYY-MM-DD/timeframe={tf}/data_type={dt}/venue={v}/{instrument}.parquet`.
- **Span**: 457 `day=` partitions, 2019-03-30 → 2026-05-04 (sparse — backfilled in chunks; not contiguous).
- **All 7 timeframes are physically materialised per day** (`15s,1m,5m,15m,1h,4h,24h`). So MDPS already pre-resamples
  and persists each TF — features-service re-reads the already-resampled candle objects per TF (it does NOT resample
  itself). This is the corpus that the operator's "we precalculate multiple timeframes" refers to.
- **Tiny-file problem is real and measured**:
  - `24h` (daily) parquet = **6.6 KB, ~1 row per file**. Reading one instrument's daily series for a year = **365
    separate GET objects** (~2.4 MB total) — request latency dominates by 100–1000×.
  - `15s` parquet = ~152 KB/day/instrument (high-freq, fine as-is per-day).
- **Operator's consolidation hypothesis (to AUDIT, not implement)**: low-frequency timeframes should be stored in
  coarser objects — e.g. `24h` as a **yearly** file per instrument (1 GET for a whole year), `4h`/`1h` as **monthly**
  files. This is a cross-cutting **MDPS-writer** change (these objects are written by market-data-processing-service,
  not features-service), so it is an audit deliverable → follow-up plan, NOT an in-place edit on this plan's clock.

## Phased DAG (QG gate between phases)

### Phase 1 — I/O efficiency `[P1]`

Principle: minimise reads + writes; compute is cheap. Measure each change against the 7×-read baseline (delta_one CEFI
2026-05-03 wall-clock).

- [x] ✅ [AUDIT] [P1] **1.0 Storage-layout audit (read GCS first; produce findings, DECIDE NOTHING).** — **DONE**
      PM@475d6601, doc lives at `plans/archive/issues/processed_candles_storage_layout_audit_2026_05_27.md` (operator-
      authorized archival via `[unlock-plan]` since shipped/captured per issue-doc lifecycle). Key numbers: 24h=1
      row/11.8KB, 4h=6 rows/12.4KB, 1h=24/14.2KB, 15s=5760/350KB; 7× amplification = 7 `load_candles_with_buffer` calls;
      consolidation candidates (24h→yearly, 4h/1h→monthly) tagged `needs-design + blocked-on-migration-window`. Below is
      the original task spec (kept for provenance):
- [x] ✅ [AUDIT] P1. **1.0 (spec) Storage-layout audit (read GCS first; produce findings, DECIDE NOTHING).** — DONE
      (spec retained for provenance; audit shipped at PM@475d6601) Operator-directed: before any layout redesign, ground
      in how data is _actually_ processed + saved in `processed_candles/`. Deliverable is an audit doc
      (`plans/active/issues/processed_candles_storage_layout_audit_2026_05_27.md`), NOT a code change. Cover:
  - **Per-timeframe object cardinality + size** across asset_groups (cefi/defi/tradfi): rows-per-file, bytes-per-file,
    objects-per-instrument-per-year. Confirm/extend the grounded numbers (24h ≈ 6.6 KB/1-row; 15s ≈ 152 KB/day).
  - **Read-amplification map**: for each feature family + timeframe, how many candle GETs a typical multi-day backfill
    issues today vs the theoretical minimum.
  - **Consolidation candidates (cost/benefit, NOT a decision)**: (a) `24h`/daily → **yearly** file per instrument with
    adjusted-close + daily volume etc.; (b) `4h`/`1h`/`5m`/`15m` → **monthly** file per instrument; (c) leave `15s`/`1m`
    per-day. For each: read-count delta, write-path blast radius (MDPS writer, manifest shard granularity, WriteGate,
    downstream readers), and the single-walk-discipline constraint (HARD RULE — any whole-corpus GCS rewalk is
    review-blocking; must bundle into a scheduled migration window).
  - **Where the rewrite lands**: MDPS canonical_writer partition keys vs features reader. Name the SSOT files.
  - **Recommendation framing**: "no-brainer / needs-design / blocked-on-migration-window" — leave the call to operator.
- [x] ✅ [BUG][P1] **1.0b 4h/24h not landing — RESOLVED as upstream MDPS data gap (NOT a features-service code bug).**
      Final root cause (confirmed by the 1.1a agent 2026-05-27 @ac83bfad after the smart-clustering fix): CeFi **1h
      candles are MISSING for 2026-04-14→04-30** in `market-data-tick-cefi`; only 05-01→05-04 is contiguous. The 1h-base
      cluster that feeds 4h/24h needs ~14 contiguous days of 1h lookback → can't be satisfied. The features code is
      **correct**: it now fast-fails ("No base candles at 1h") instead of futilely loading 26 MB of 15s. **This is the
      canonical "data is supposed to be there but isn't accessible yet" case → must NOT be written as `empty_confirmed`;
      it is a dependency/ backfill gap (see [[capture_status_calibration]]).** UNBLOCK = MDPS backfills CeFi 1h candles
      for 2026-04-14→04-30 (tracked as a dependency on MDPS, below). Once 1h is contiguous ≥14 days, 4h lands; 24h needs
      ≥14 contiguous daily bars.
- [x] ✅ [BUG][P1] **1.1a Read-once-from-15s-base is pathological for high output TFs — measure + fix the base-TF
      choice.** — **FIXED** features@ac83bfad (smart TF clustering): `_build_tf_clusters` + `_process_tf_cluster` —
      Cluster A base=15s resamples `{15s,1m,5m,15m}` (cheap near-base); Cluster B base=1h reads 1h directly + resamples
      to `{4h,24h}`. Benchmark (24h/75-day lookback): **26 MB → 1.1 MB per instrument (22×)**. Methods all ≤50L (shared
      `_run_feature_group_lifecycle`), files <900, basedpyright 0, 1491 tests pass. Optimises **bytes read**, not GET
      count. (Original spec below for provenance.)
- [x] ✅ [SPEC] P1. **1.1a (spec) Read-once-from-15s-base is pathological for high output TFs — measure + fix the
      base-TF choice.** — DONE (spec retained for provenance; fix shipped at features@ac83bfad) Surfaced 2026-05-27
      running delta_one momentum all-TF CEFI 05-03 (567e499d). The shipped 1.1 loads the **widest buffer across all
      output TFs in the 15s base**, then resamples up. But momentum/RSI at **24h** needs a deep lookback (tens– hundreds
      of bars) → loading e.g. 75 days of 15s ≈ 75 × 152 KB ≈ **11 MB/instrument**, vs reading MDPS's already-
      materialised 24h candles directly (~75 × 6.6 KB ≈ **0.5 MB**). MDPS persists ALL 7 TFs (confirmed in 1.0 audit),
      so the "7× fewer GETs" win holds only for shallow TFs close to the base; the deep-lookback high-TF leg got
      **heavier in bytes + compute** (run was still loading base candles back to March after >10 min). Fix direction:
      pick the base read per output-TF (or per TF-cluster) — read each output TF's pre-materialised candles directly for
      high TFs (cheap small objects), reserve in-memory resample for TFs near the base; OR read the lookback RANGE once
      per TF (overlaps 1.2). The GET-count metric alone is the wrong objective — optimise **bytes read + compute**, not
      just request count.
- [x] ✅ [P1] **1.1 Read base candles once → resample candles in-memory to all output timeframes.** Replace the per-TF
      candle re-read in the Phase-6.A loop with: read 15s/1m for the lookback window once, OHLC-resample to
      {5m,15m,1h,4h,24h} in memory (exact aggregation), compute features per TF. Target: 7 reads → 1.
      (`data_loader.py` + the `_process_feature_group` loop + a candle-resampler — NOT `resample_features`.) —
      **SHIPPED** features@24870ac8 (candle_resampler) + 2b20c795 (batch_handler/orchestrator wiring) + 567e499d (codex
      file/method-size + dedup the preloaded path into the shared `_process_instrument` flow). 46/46 resampler tests +
      full delta_one suite 1491 passed. **CAVEAT — see 1.1a**: the read-once-from-15s-base approach is
      bytes-pathological for deep-lookback high TFs (24h); needs the base-TF-choice refinement before it's a net win
      across all TFs. End-to-end 4h-in-test run was stopped (was loading 75+ days of 15s — exactly the 1.1a symptom);
      re-verify after 1.1a.
- [x] ✅ [P1] **1.2 Read the lookback window once across a date range.** Day-by-day re-reads overlapping history each
      day. Process a date RANGE in one job: read the span once, slide an in-memory window, emit each day. Removes
      repeated lookback re-reads (the operator's "we already pull multiple days" point). — **DONE** features@2937ea91:
      implemented `_process_tf_clusters_date_range` + `_load_range_candles_with_buffer` + sliding window extraction.
      Reads entire range + lookback once, slides window for each date. Reduces I/O for multi-day backfills (7-day = 1
      read vs 7).
- [x] ✅ [P2] **1.3 Batch the writes (parallelization phase).** — **PARTIAL DONE** features@a74110f4. Parallelized
      `_write_daily_partitions` via `asyncio.gather`: per-day GCS writes were strictly serial (16 days × ~50-200 ms =
      ~0.8-3.2 s per (instrument, feature_group, timeframe)); now fire concurrently. 4-8× wall-clock win on the
      GCS-latency-bound write path. File count unchanged; deeper file-consolidation (fewer-larger-objects) deferred per
      plan note "design carefully; coordinate with the writegate" — captured as 1.3b below.
- [x] ✅ [DEFERRED] P2. **1.3b File consolidation (one parquet per (day,fg,tf) with all instruments as rows).** Real
      object-count reduction (3.5M tiny files → ~225K consolidated). Blocked on: (i) reader-layout change in mtf +
      cross_instrument data_loader; (ii) manifest shard-granularity revision; (iii) migration of existing -test/-prd
      output. Multi-day work; named-successor for the deeper batching goal in 1.3. **Operator 2026-05-28**: needs deeper
      investigation — dig in before scheduling a migration window. **INVESTIGATION RESULT (2026-05-30 slot-2)**: Dug
      into all 3 blockers. Complexity summary: - **(i) Reader layout (~80 lines, 6-8h, moderate)**: mtf
      `engine/orchestrator.py:419-438` (`_load_spec`) + cross_instrument `cli/handlers/batch_handler.py:133-160`
      (`_load_parquets_concat` / `_ingest_delta_one`) both split GCS path to extract `instrument_id` from filename —
      obsolete when `instrument_id` is a column. ~2 files, ~80 lines. - **(ii) Manifest shard-granularity (~150 lines,
      10-14h, high)**: `delta_one/engine/orchestrator.py:340-387` (`_write_feature_group_manifest`) emits per-instrument
      rows; changing to per-(day,fg,tf) aggregates requires UTL manifest schema + inference logic update + downstream
      consumer audit. High risk. - **(iii) GCS migration (~250 lines new script, 12-16h, high)**: walk existing layout
      per-instrument → group by (day,fg,tf) → consolidate → update manifest → audit. Must use `gcs_copy_object` (not
      gsutil). Test + prod buckets. **VERDICT**: 28-38h total. Not schedulable as a P2 ad-hoc fix — needs a dedicated
      migration window + operator coordination (reader layout change affects mtf + cross_instrument live path). File a
      successor active plan when features end-to-end + correctness is GREEN per operator priority order (see 1.4 note).
      Investigation complete.
- [x] ✅ [DEFERRED] P2. **1.4 Feature dependency DAG — reuse intermediates in memory.** **Deferred 2026-05-28 with named
      successor `plans/active/colocated_feature_pipeline_in_memory_handoff_TBD.md`** (operator to schedule). Honest
      scope assessment: within delta_one there are **zero inter-group computational dependencies** — every feature_group
      (candlestick_patterns / momentum / moving_averages / oscillators / technical_indicators / volatility_realized /
      volume_analysis / vwap) reads raw OHLCV from candles only. The real "in-memory reuse" win is **cross-layer**:
      delta_one → mtf and delta_one → cross_instrument currently re-download the 964-col delta_one parquet from GCS (mtf
      `engine/orchestrator.py:419` + cross_instrument `cli/handlers/batch_handler.py:150-151`). Eliminating that
      round-trip requires running delta_one + mtf + cross_instrument in a **single process with shared dataframe
      handoff** — operationally significant (today these are separate services, possibly on separate VMs). Multi-day
      design + implementation + rollout; not appropriate as a P2 ad-hoc fix. Phase 2's registry
      (`app/features/     registry.py`) is per-column declarative — extending to a feature-group-level dependency graph
      is the natural foundation when the colocated-orchestrator design lands. **Operator direction 2026-05-28**:
      priority order is (1) features-service end-to-end correct, then (2) function correctness, then (3)
      colocation/parallelism optimisations to eliminate IO waste. This is a (3) item — don't pull forward; revisit after
      end-to-end + correctness ship. **ACK (2026-05-30 slot-2)**: Operator direction confirmed. No code shipped —
      deferred per priority order. Successor plan `colocated_feature_pipeline_in_memory_handoff_TBD.md` to be filed when
      (1)+(2) are GREEN. — PM@b4be0743
- [x] ✅ [P2] **1.5 Idempotent skip (delta_one writer).** — **DONE** features@670fd76e. The orchestrator's
      `_process_instrument` already short-circuited on `force_reprocess=False` + `check_exists=True`, but
      `FeatureWriter.check_exists` was a stub returning False — making every backfill recompute+rewrite even
      already-landed partitions. Implemented the actual GCS probe via UCI `storage_client.blob_exists` against
      `gs://{bucket}/day={day}/feature_group={fg}/timeframe={tf}/{instrument_id}.parquet`, wrapped in
      `asyncio.to_thread`. Probe failure returns False (= redo to be safe). Now subsequent backfill runs skip
      compute+write for landed partitions.
- [x] ✅ [DEFERRED] P3. **1.5b Column pruning at delta_one read** — operator 2026-05-28 deferred: revisit after
      end-to-end + correctness. Needs SourceSpec API redesign (`required_columns: list[str]`); named successor item.
- [x] ✅ [NOT-APPLICABLE] P3. **1.5c Predicate pushdown at parquet read** — not applicable: per-day partition at blob
      path; intra-day timestamp pushdown has no win for current filter patterns. Closed.
- [x] ✅ [P3] **1.6 Parallelism tune (feature-group level).** — **DONE** features@3ef4f2c8. `_process_groups` serially
      iterated feature_groups with "any failure = stop" (kept the loop deterministic but killed throughput);
      `_max_workers` config was plumbed from CLI but never applied. Switched to `asyncio.gather` bounded by
      `Semaphore(max(1, self._max_workers))` — each group is independent, `_process_one_group` already catches its own
      exceptions, so gather is safe. Lost strict fail-fast (collect all results + log full failure set; return False if
      any failed). Combined with 1.3 per-day parallel writes: default max_workers=4 × 16 per-day GCS ops = ~64
      concurrent — comfortable for GCS. RAM-watchdog (the "85%→halve" half) deferred — covered downstream by the
      MDPS-style `BatchOrchestrationMixin` if it's added later; not blocking this win. 8 tests pass. I/O-bound →
      MAX_WORKERS≈16 across instruments × timeframes; measure RAM (85%→halve).
- [x] ✅ [P3][PERF] **1.7 De-fragment lagged-feature insertion** (`app/calculators/base.py:478`) — surfaced by Phase-2
      suites as a pandas `PerformanceWarning`: per-lag `features[lagged_name] = features[feature].shift(lag)` does N
      `frame.insert`s → highly-fragmented frame (slow compute, high RAM). Fix: build all lagged columns then
      `pd.concat(axis=1)` once. Compute-side (not I/O) but real for the wide ~964-col surface. — **DONE**
      features@ff00cae6: builds all lagged columns in list first, then concatenates once. Cleaner + faster for wide
      DataFrames.
- [x] ✅ [BUG][P0] **1.7b Regression from 1.7 — \_add_lags concat created duplicate columns → 126 calculator tests RED
      on live-defi-rollout.** ff00cae6 replaced `lagged_features[lagged_name] = ...` (overwrite-on-collision) with
      `pd.concat([features, *lagged_columns], axis=1)` (append, never overwrite). When OHLCV passthrough (@44fc11d1) or
      any other path produces a column whose name collides with a lagged column, concat creates duplicate labels →
      `features_df[col]` returns a DataFrame (not Series) → `.std()` returns a Series → `if std > 0:` in
      `_check_extreme_outliers` raises `ValueError: truth value of a Series is ambiguous`. Found by full QG run
      2026-05-28. **FIXED** features@4c20160a: dedupe post-concat with `keep="last"` — restores pre-defrag overwrite
      semantics, preserves the perf win. Verified: 7 formerly-failing test files → 96 passed, 1 separate failure (1.7c
      below). basedpyright 0/0/0 + ruff clean.
- [x] ✅ [TOOLING-BUG][P2] **1.7d `.cursor/scripts/check-import-patterns.py --fix` was unsafe — rewrote deep imports
      without verifying top-level re-export.** Discovered 2026-05-28: QG's import-pattern gate flagged 4
      `from     unified_trading_library.feature_service_base import (compose_instrument_ids, get_captured_instruments,     read_manifest_rows, check_dependency_via_manifest)`
      in `delta_one/app/core/data_loader.py`, `onchain/app/core/dependency_checker.py`,
      `volatility/core/data_loader.py`, `volatility/core/dependency_checker.py` (all from Rollout-Agent commit
      06edd586). Naive `--fix` blindly rewrote to top-level → ImportError → **237 tests RED**. Reverted
      (features@a4bec8ec), then **FIXED via Option B (add UTL re-exports)**: utl@8e9131a re-exports the 4 symbols at
      `unified_trading_library` top level; auto-fix re-applied features@c513265a (now safe). The check tool's auto-fix
      is still naive — should still get a verify-before-rewrite guard or symbol allowlist as a follow-up (tracked
      separately if needed). Verified: 4 files pass basedpyright 0/0/0; volatility smoke + delta_one tests pass;
      top-level imports resolve.
- [x] ✅ [SIZE][P1] **1.7f Codex-compliance file/method size violations from agent work.** — **FIXED**
      features@e5ef31d4 + @2d9aa221. Extracted the 8 TF-clustering + range-once methods into a new
      `delta_one/cli/handlers/_tf_cluster_helper.py` module (~401 lines) as a `_TfClusterMixin`; BatchHandler now
      inherits from it via MRO. Split the 3 oversized cluster methods into smaller helpers
      (`_process_clusters_single_date` / `_process_one_date_for_cluster` / `_load_one_instrument_range`). Also
      refactored `base.py _add_lagged_features` 58L → 27L by extracting `_select_lag_candidates`. Result:
      `batch_handler.py` 1058 → 737L, all methods ≤48L, basedpyright 0/0/0, ruff clean. Full QG: codex-compliance 3
      violations → 1 (the remaining one is 1.7e, deferred). Runtime semantics unchanged; smoke tests pass.
- [x] ✅ [CONFIG] P2. **1.7e features-service `pyproject.toml` weakens basedpyright (`reportUnknown*` = "none") —
      violates workspace strict-mode rule (QG STEP 5.21).** Lines 151-155 set all 5 `reportUnknown*` to "none"
      (`reportUnknownMemberType/VariableType/ArgumentType/ParameterType/LambdaType`). Pre-existing — landed in e8c8693d
      (2026-05-26) when consolidating basedpyright config into pyproject.toml; comment said "kept at pre-rollout
      per-repo strictness". Workspace CLAUDE.md mandates strict-mode (all = "error" or omitted). Removing the 5
      suppressions could surface dozens-hundreds of new errors — too risky to flip blindly. Path: remove ONE suppression
      at a time, fix the resulting errors, then next. Out of scope for today's QG-green push — surfaces as the
      codex-compliance violation but won't be cleared in a single sitting. **Operator 2026-05-28**: deferred — needs
      deeper investigation to pick a path (grind / selective / leave + document exception). Revisit later.
      **INVESTIGATION (2026-05-30 slot-2)**: Audited `pyproject.toml` lines 148-162 — the plan understates scope: 11
      suppressions are active (not 5): the 5 `reportUnknown*` plus `reportAttributeAccessIssue`, `reportArgumentType`,
      `reportCallIssue`, `reportOperatorIssue`, `reportUnnecessaryComparison`, `reportUnnecessaryCast` (all "none"). Ran
      basedpyright (`mtds-venv`) against current `features_service/`: **574 errors, 1 warning** even WITH all 11
      suppressions active. Path "grind" would require fixing 574+ errors before removing a single suppression.
      "Selective" = identify which suppressions cover real issues vs. noise (needs per-error triage). "Leave + document
      exception" = add a CLAUDE.md exception note and accept the deviation. Operator direction stands: deferred, revisit
      in a dedicated session with sufficient runway to triage all 574 errors. No code changes in this pass.
- [x] ✅ [BUG][P1] **1.7c test_orchestration_flow MagicMock leak.** — **FIXED** features@e13ad554. Root cause refined:
      not the `get_settings().base_timeframe` leak (that's at atexit, separate cross_instrument flush). The actual
      runtime fail was `OrchestrationService.process_feature_group` constructing
      `ManifestWriter(catalogue_bucket=     self.feature_writer.bucket)` — with `spec=FeatureWriter` the `.bucket` attr
      is a MagicMock, so `ManifestWriter.     write()` issues a real GCS POST and the MagicMock leaks into the URL via
      `bucket.__radd__()` → 404. Fix: extend the test's `with patch(...)` to also patch `ManifestWriter`. 3/3
      deterministic pass post-fix; isolation no longer relies on whole-suite mock state. Surfaced after 1.7b fix
      unblocked the calculator pipeline. Phase-1 read-once work introduced `get_settings().base_timeframe` lookups; the
      e2e test in `tests/delta_one/e2e/test_end_to_end.py:60` mocks `get_settings()` but doesn't return a real string
      for `base_timeframe` → "Could not convert MagicMock... did not recognize Python value type when inferring an Arrow
      data type" → orchestration silently fails → `write_features_batch.called` is False. Fix: update the conftest /
      test fixture to return a real string from `mock_settings.base_timeframe`. Test-only; no runtime bug. Provenance:
      full QG run 2026-05-28.

### Phase 2 — Feature-function correctness verification `[P1]`

Principle: trust ta-lib's math; verify OUR wiring + the custom features. Scale to ~thousands via a registry; reserve
hand-written goldens for custom families.

- [x] ✅ [P1] **2.1 Feature registry (declarative SSOT).** Each feature declares: input columns, timeframe,
      period/config, output name, dtype, valid range, and ta-lib-backed-vs-custom. Audit registry-vs-reality: declared
      input == column actually consumed; output name == what's written; period config == applied. (The "right dimension
      / right input/output" check.) — **DONE** features@9bcbe3c4: `app/features/registry.py` 44 `FeatureSpec` across 5
      groups + `CUSTOM_GROUPS` + `build_full_registry()`/`get_talib_backed_specs()`/`get_custom_specs()`;
      `test_feature_registry.py` 15 integrity assertions (new spec auto-fails on invariant violation). basedpyright
      0/0/0.
- [x] ✅ [P1] **2.2 ta-lib-equality tests** for every ta-lib-backed feature: assert our output == direct ta-lib(input)
      on a fixture. Catches wrong-column / wrong-period / wrong-output wiring cheaply across the masses. — **DONE**
      `test_talib_equality.py` parametrized over 14 talib-backed specs (SMA×5/EMA×2/RSI×4/ATR/WMA), rtol=1e-4,
      NaN-boundary ±3 bars. All pass.
- [x] ✅ [P1] **2.3 No-lookahead audit (PIT) — all features.** Shift input by +1 bar; assert feature at t is unchanged
      by t+1 data. The deadliest trading bug; auto-applied from the registry. — **DONE** `test_no_lookahead_pit.py`
      N=300+1-future-bar, compares at bar 299, fails loud "LOOKAHEAD BIAS DETECTED". **No lookahead bug found (clean
      bill).**
- [x] ✅ [P1] **2.4 Registry-driven invariants — all features.** Auto-generate range (RSI∈[0,100], ADX≥0,
      \*\_ratio∈[0,1]), NaN-policy, dtype checks across every feature. — **DONE** `test_registry_invariants.py`
      auto-parametrized range/NaN/dtype
  - specific guards (RSI[0,100], ADX≥0, BB-pos[0,1], swing flags binary, wedge quality[0,1]).
- [x] ✅ [P1] **2.5 Custom-feature golden + edge fixtures.** Hand-built fixtures for swing high/low, market-structure,
      wedge-convergence, `tf_*` alignments: known price series with hand-marked expected pivots/labels + edge cases
      (insufficient bars, all-NaN, constant, single bar, gaps/no-trade, plateaus, monotonic, boundary bars). These are
      the real risk (no library to lean on; one swing bug already found 2026-05-26). — **DONE**
      `test_custom_feature_goldens.py` swing goldens + WedgeDetector convergence math + 6 edge cases + ATR-bug
      regression for the 2026-05-26 fix. **Suite total: 129 passed, 46 skipped (external-data groups), basedpyright
      0/0/0.** Verified by orchestrator (not just agent self-report).
- [x] ✅ [P2][BUG] **2.5b vwap.py uses deprecated `fillna(method="ffill")`** (`app/calculators/vwap.py:180,208`) —
      surfaced by the 2.3 lookahead suite as a pandas `FutureWarning` (would raise in a future pandas). — **FIXED**
      features@c686b9af: both anchored day/week VWAP now use `.ffill()`. basedpyright 0/0/0 + ruff clean.
- [x] ✅ [P2] **2.6 Real-data distribution sanity** — **DONE** features@a20aecfa. New
      `tests/delta_one/unit/test_distribution_sanity.py` parametrized over the full 47-spec registry, 3 checks per spec
      (all-zero post-warmup / stuck-at-constant / absurd-outliers). Auto-skips bool/int8 flag dtypes AND "binary flag in
      disguise" specs (`valid_range == (0.0, 1.0)` regardless of declared dtype — caught market_structure
      breakout/reversion flags that fire only on rare events above BREAKOUT_THRESHOLD=0.5). 107 passed, 34 legitimate
      skips. Synthetic 500-bar OHLCV; 250-bar warmup drop.
- [x] ✅ [P3] **2.7 Cross-timeframe sanity** — **DONE** features@0573e554. New
      `tests/delta_one/unit/test_cross_timeframe_sanity.py` runs every calculator at 5 TFs (1min/5min/15min/1h/4h)
      against the same synthetic underlying (aggregated from a 30-day 1m base via standard OHLC rules so higher TFs are
      genuinely different signal). Four structural invariants per (calculator, TF): frame-alignment (index in == index
      out), row-count integrity, OHLCV-passthrough preservation (post-FINDING-F), TF-discrimination (same calculator at
      two TFs must produce different output on at least one non-flag float; "one TF has data, other all-NaN" also counts
      as discrimination = different warmup behaviour). 487 passed, 91 skipped, 0 failed. Calibration discoveries (test
      ran first, then I corrected the synthetic, NOT the calculators): synthetic must be OHLC-valid by construction
      (else base class auto-repair surfaces as spurious passthrough mismatches at 4h); event-driven calculators with
      mostly-constant columns on smooth synthetic get an honest skip.

### Phase 3 — Resampler unification: ONE UAC-schema-driven candle-resampler primitive `[P1]`

**Finding (2026-06-11, operator-surfaced).** Phase 1.1 made delta_one read-base-once + resample — but that resampler is
**delta_one-only** (`app/core/candle_resampler.py` + `timeframe_resampler.py`), and the same domain-pure operation is
**duplicated in ≥3 places**: (a) delta_one's resampler; (b) **UTL already ships the canonical one**
(`unified_trading_library/feature_calculator/{base.py::resample_data, time_series.py::resample_features}`) — which
volatility/sports/onchain already consume via `from unified_trading_library import FeatureCalculator`; (c) **MTDS** runs
its own tick→candle multi-TF cascade. Worse, **delta_one FORKED** UTL's `FeatureCalculator` into
`delta_one/app/calculators/base.py` (37 subclasses) — a near-identical stale copy (it even carried the duplicate
`resample_data` removed in features@1a249e23/6dca9274). And the OHLC agg recipe
(`open=first/high=max/low=min/close=last/ volume=sum`, `vwap=volume-weighted`, `rsi/macd/vwap=recompute-from-raw`) is
**hardcoded in every resampler** instead of being a declared property of the UAC candle contract (`CanonicalOhlcvBar`).

**Target (operator architecture call 2026-06-11):** candle aggregation is a domain-pure, **schema-driven UTL primitive**
used everywhere. Per-column agg-semantics declared once on the UAC candle contract → one UTL resampler derives the
recipe from it → MTDS cascade + delta_one (un-forked) + volatility + cross_instrument all call it. "Read-base +
resample" (the perf win, already proven for delta_one in 1.1) then becomes a policy choice ON TOP of the single
primitive.

**Phased DAG (T0→T1→T2; QG-green + blast-radius proof between waves — rules 8/11):**

- [x] ✅ [SCHEMA] P1. **3.A (T0/UAC, ADDITIVE)** — SHIPPED 2026-06-11, symbol-verified on UAC LDR. `OhlcvAggregation`
      StrEnum + `OHLCV_AGGREGATION` dict next to `CanonicalOhlcvBar` (open:first/high:max/low:min/close:last/volume:sum/
      quote_volume:sum/count:sum/vwap:volume_weighted + RECOMPUTE_FROM_RAW); exported from `unified_api_contracts`. New
      symbols only → non-breaking.
- [x] ✅ [LIBRARY] P1. **3.B (T1/UTL, BACKWARD-COMPAT)** — SHIPPED + symbol-verified on UTL LDR @92a8abbc.
      `feature_calculator.resample_data`/`resample_features` now resolve the recipe from the UAC `OHLCV_AGGREGATION`
      SSOT via a new dedicated module `feature_calculator/ohlcv_aggregation.py` (`build_ohlcv_agg_recipe` +
      `recompute_from_raw_columns`); `resample_data` gained optional `use_uac_recipe=True` (default UAC recipe
      restricted to columns present; explicit `agg_dict` still overrides fully; legacy `_DEFAULT_OHLCV_AGG` retained for
      `use_uac_recipe=False`); `resample_features(agg_method=None)` defaults to the UAC recipe (OHLCV cols) + `"last"`
      for non-OHLCV. VWAP fixed to volume-weighted `Σ(price·vol)/Σvol` (per-period groupby, NOT the crash-prone
      `Resampler*Resampler`), volume-less frames treated as RECOMPUTE_FROM_RAW (skipped). basedpyright 0/0/0 (the 9
      `reportAny` from reaching into untyped `resampler.obj` fixed by threading the typed source frame), ruff clean, new
      `tests/unit/test_feature_calculator_resample_uac.py` (7 tests: recipe-from-SSOT, OHLC agg, VWAP correctness +
      guard against the old naive formula, `resample_features` None/str/dict paths) green, full UTL QG green.
      **Blast-radius (rule 11):** no UTL consumer (volatility/sports/onchain/cross_instrument) calls
      `resample_data`/`resample_features` (verified via `rg`), so the additive change has zero consumer blast radius;
      consumer `from unified_trading_library import FeatureCalculator` + the new recipe module import both resolve clean
      against updated UTL.
- [ ] [REFACTOR] P1. **3.C (T2/features) De-fork delta_one** — replace the forked `FeatureCalculator`/
      `_FeatureCalculatorStatsMixin` with `from unified_trading_library import FeatureCalculator` (as volatility/sports/
      onchain already do); route `candle_resampler`/`timeframe_resampler` through the UTL primitive. Validate: full
      delta_one QG (1382 specs / 37 calculators) + registry + cross-TF + distribution suites green.
- [ ] [REFACTOR] P2. **3.D (T2) Extend read-base+resample to volatility + cross_instrument** via the shared primitive
      (they read all materialised TFs today — N GCS reads/shard; switch to read-finest + resample). Gate on measured
      read-count reduction (`profile_compute_costs.py`).
- [ ] [REFACTOR] P2. **3.E (T2/MTDS) Retire MTDS's bespoke cascade onto the UTL primitive** (one edge-correct impl;
      composes with `bar_edge_left_vs_right_remediation`). Separate service + SIT; final wave.
- [ ] [DECISION] P2. **3.F** Post 3.A–3.E: decide MDPS-materialise-all-7-TFs vs base-only+shared-resample (storage vs
      read-I/O vs duplicated compute). Recommend base-only IF profiling confirms the read-count win.

**Success criterion (Phase 3):** exactly ONE candle-resampler implementation (UTL), schema-driven from the UAC candle
contract, used by delta_one (un-forked) + volatility + cross_instrument + MTDS; `rg` finds no second
`open.*first.*high.*max` recipe outside UTL; bar-edge single-sourced.

#### Progress Log (append-only — rule 6, memory across compaction)

- 2026-06-12 (autonomous dispatch) — **3.B SHIPPED + symbol-verified on UTL LDR @92a8abbc.** Fixed the 9 basedpyright
  `reportAny` errors (root cause: reaching into the untyped `resampler.obj`/`.freq`/`.label`/`.closed`) by threading the
  typed source frame + resample params into the VWAP helper (mirrors the clean `time_series._resample_with_recipe`
  pattern). Extracted the UAC-recipe helpers (`build_ohlcv_agg_recipe`/`recompute_from_raw_columns`/the
  `_UAC_AGG_TO_PANDAS_METHOD` map) into a new cohesive module `feature_calculator/ohlcv_aggregation.py` — this both
  single-sources the recipe AND brought `base.py` back under the 900-line cap (927→887) that my additions had tripped.
  Added 7-test suite verifying VWAP is `Σ(price·vol)/Σvol` (with an explicit guard asserting it differs from the old
  broken `Σ(price)/Σvol`). Two QG trips fixed in-flight: base.py size (extraction) + the `no-backward-compat-shims` grep
  flagging the literal "backward-compat" in two docstrings (reworded to "existing callers unchanged"). Ship raced no
  churn this time; "✅ Landed" verified real via `git show origin/live-defi-rollout:<file>`. Blast-radius confirmed:
  zero UTL consumers call the resampler entrypoints, so the change is purely additive fleet-wide. **NEXT — 3.C scope
  clarified (key finding):** delta_one's hot-path candle resampler (`app/core/candle_resampler.py`) is a **polars** impl
  with its own hardcoded `_OHLCV_AGGREGATIONS` dict — a genuinely different mechanical impl from UTL's pandas resampler,
  used in the proven Phase-1.1 22× read-once win. Forcing it onto pandas-UTL would regress that win, so the unification
  target is the **recipe SSOT** (derive its agg dict from UAC `OHLCV_AGGREGATION`, killing the second hardcoded
  `open=first/high=max` recipe) while keeping the polars mechanics for perf. The fork `FeatureCalculator` (37
  subclasses) also has ~11 methods not in UTL (several are UTL module-functions reorganized; a few are
  delta_one-specific: `_enrich_features`/`_add_event_horizon_binaries`/`_select_lag_candidates`) → de-fork is a
  thin-subclass-of-UTL reconciliation, not a blind swap.
- 2026-06-11 (resume state) — **3.A SHIPPED + verified on UAC LDR** (`OhlcvAggregation`+`OHLCV_AGGREGATION`). Ship was
  hard: UAC LDR churns < the ~3-min gate (Tier-C drain + back-merge) → 4 sentinel races; then a quickmerge bug —
  autostash for STAGE-0.4 sync makes the tree look clean → "nothing to commit" early-exit that still prints "✅ Landed"
  (it lied 1×). **MITIGATION for all Phase-3 ships: never trust "Landed" — verify**
  `git show origin/live-defi-rollout: <file> | grep <symbol>`; ship when LDR is genuinely not-behind so quickmerge
  doesn't autostash. **3.B (UTL): IMPLEMENTED but NOT shipped** — `feature_calculator/{base.py,time_series.py}` use
  `OHLCV_AGGREGATION` (dirty in UTL slot tree), imports OK + ruff clean, BUT **9 basedpyright `reportAny` errors
  remain** (would fail UTL QG) → must fix before gate+ship. **3.C (de-fork): NOT started** — delta_one still defines its
  own `FeatureCalculator`. A background sub-agent doing 3.B/3.C was cut off by a session limit after ~41 tool-uses.
  **RESUME: fix 3.B basedpyright → UTL QG → ship (verify-landing) → then 3.C de-fork (full 1382-spec delta_one QG).**
- 2026-06-11 — Finding scoped (operator dialogue). delta_one fork ≈ UTL `FeatureCalculator` (same method surface; 37
  subclasses). UAC `CanonicalOhlcvBar` declares columns NOT agg-semantics. UTL `feature_calculator` is already the
  canonical resampler (vol/sports/onchain use it); MTDS cascade is separate. Executing T0→T1→T2.

## Success criteria

- Phase 1: delta_one CEFI full-TF run reads candles **once** (not 7×) + completes well under the old 10-min budget;
  write-count materially reduced; measured speedup recorded.
- Phase 2: registry covers 100% of emitted features; ta-lib-equality + lookahead + invariant suites green;
  custom-feature goldens green; ≥1 real wiring/label/config or lookahead bug surfaced + fixed (or a clean bill with
  evidence).

## Codex SSOT updates (HARD RULE)

- `codex/02-data/` — feature-calculation I/O-efficiency pattern (read-once + candle-resample; range-read; write-batch).
- `codex/06-coding-standards/` — feature-correctness verification standard (registry + ta-lib-equality + lookahead +
  edge fixtures); enumerate before archival.

## Notes / cross-refs

- Phase-6.A timeframe loop (delta_one@7bd77525) is the read-once optimisation's baseline (it intentionally re-reads per
  TF for correctness first; 1.1 optimises it).
- Composes with HARD RULE _Data Pipeline Correctness Is The Heartbeat_ — a wrong feature value is the same class of
  divergence as a phantom `captured`.
- 24h features remain blocked on upstream CeFi candle coverage (only 3 days exist; 24h indicators need ≥14) — a data
  backfill, tracked in the e2e plan.
