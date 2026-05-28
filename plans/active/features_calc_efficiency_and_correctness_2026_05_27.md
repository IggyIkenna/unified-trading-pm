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
locked_by: live-defi-rollout
locked_since: 2026-05-27
related_plans:
  - plans/active/features_service_e2e_pipeline_test_2026_05_26.md
---

> **🛑 ROLLOUT-AGENT HOLD (2026-05-27):** harsh-side (operator-directed) is actively working this plan. **Do NOT
> auto-assign / auto-fix / push to LDR.** See `plans/active/_agent_pings.md`. Banner removed by harsh-side when
> released.

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
      row/11.8KB, 4h=6 rows/12.4KB, 1h=24/14.2KB, 15s=5760/350KB; 7× amplification = 7 `load_candles_with_buffer`
      calls; consolidation candidates (24h→yearly, 4h/1h→monthly) tagged `needs-design + blocked-on-migration-window`.
      Below is the original task spec (kept for provenance):
- [ ] [AUDIT] [P1] **1.0 (spec) Storage-layout audit (read GCS first; produce findings, DECIDE NOTHING).**
      Operator-directed: before any layout redesign, ground in how data is _actually_ processed + saved in
      `processed_candles/`. Deliverable is an audit doc
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
- [ ] [SPEC][P1] **1.1a (spec) Read-once-from-15s-base is pathological for high output TFs — measure + fix the base-TF
      choice.** Surfaced 2026-05-27 running delta_one momentum all-TF CEFI 05-03 (567e499d). The shipped 1.1 loads the
      **widest buffer across all output TFs in the 15s base**, then resamples up. But momentum/RSI at **24h** needs a
      deep lookback (tens– hundreds of bars) → loading e.g. 75 days of 15s ≈ 75 × 152 KB ≈ **11 MB/instrument**, vs
      reading MDPS's already- materialised 24h candles directly (~75 × 6.6 KB ≈ **0.5 MB**). MDPS persists ALL 7 TFs
      (confirmed in 1.0 audit), so the "7× fewer GETs" win holds only for shallow TFs close to the base; the
      deep-lookback high-TF leg got **heavier in bytes + compute** (run was still loading base candles back to March
      after >10 min). Fix direction: pick the base read per output-TF (or per TF-cluster) — read each output TF's
      pre-materialised candles directly for high TFs (cheap small objects), reserve in-memory resample for TFs near the
      base; OR read the lookback RANGE once per TF (overlaps 1.2). The GET-count metric alone is the wrong objective —
      optimise **bytes read + compute**, not just request count.
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
- [ ] [P2] **1.3 Batch the writes.** We emit thousands of tiny per-shard parquets; GCS small-object write latency
      dominates. Buffer + flush per partition-group (fewer, larger objects) — measure write-count + wall-clock. (Trades
      off against the per-instrument partition layout readers expect — design carefully; coordinate with the writegate.)
- [ ] [P2] **1.4 Feature dependency DAG — reuse intermediates in memory.** Compute in dependency order; pass derived
      features in-memory instead of write-then-reread. For colocated mtf/cross_instrument, read delta_one from memory,
      not GCS. (Requires a declared feature dependency graph — overlaps Phase 2's registry.)
- [ ] [P2] **1.5 Idempotent skip + column pruning + predicate pushdown.** Skip already-written partitions; read only the
      columns + date-range each calculator needs.
- [ ] [P3] **1.6 Parallelism tune.** I/O-bound → MAX_WORKERS≈16 across instruments × timeframes; measure RAM
      (85%→halve).
- [x] ✅ [P3][PERF] **1.7 De-fragment lagged-feature insertion** (`app/calculators/base.py:478`) — surfaced by Phase-2
      suites as a pandas `PerformanceWarning`: per-lag `features[lagged_name] = features[feature].shift(lag)` does N
      `frame.insert`s → highly-fragmented frame (slow compute, high RAM). Fix: build all lagged columns then
      `pd.concat(axis=1)` once. Compute-side (not I/O) but real for the wide ~964-col surface. — **DONE**
      features@ff00cae6: builds all lagged columns in list first, then concatenates once. Cleaner + faster for wide
      DataFrames.
- [x] ✅ [BUG][P0] **1.7b Regression from 1.7 — _add_lags concat created duplicate columns → 126 calculator tests RED on
      live-defi-rollout.** ff00cae6 replaced `lagged_features[lagged_name] = ...` (overwrite-on-collision) with
      `pd.concat([features, *lagged_columns], axis=1)` (append, never overwrite). When OHLCV passthrough (@44fc11d1)
      or any other path produces a column whose name collides with a lagged column, concat creates duplicate labels →
      `features_df[col]` returns a DataFrame (not Series) → `.std()` returns a Series → `if std > 0:` in
      `_check_extreme_outliers` raises `ValueError: truth value of a Series is ambiguous`. Found by full QG run
      2026-05-28. **FIXED** features@4c20160a: dedupe post-concat with `keep="last"` — restores pre-defrag overwrite
      semantics, preserves the perf win. Verified: 7 formerly-failing test files → 96 passed, 1 separate failure
      (1.7c below). basedpyright 0/0/0 + ruff clean.
- [ ] [TOOLING-BUG][P2] **1.7d `.cursor/scripts/check-import-patterns.py --fix` is unsafe — rewrites deep imports
      without verifying top-level re-export.** Discovered 2026-05-28: QG's import-pattern gate flagged 4 `from
      unified_trading_library.feature_service_base import (compose_instrument_ids, DependencyError, DependencyFailure,
      DependencyReport, DependencyStatus, ...)` in `delta_one/app/core/data_loader.py`, `onchain/app/core/dependency_checker.py`,
      `volatility/core/data_loader.py`, `volatility/core/dependency_checker.py` (all from Rollout-Agent commit
      06edd586). Running `--fix` rewrote to top-level `from unified_trading_library import (...)` — but those symbols
      are NOT re-exported at UTL top level → `ImportError: cannot import name 'compose_instrument_ids' from
      'unified_trading_library'` at module load → **237 tests RED** (volatility module + delta_one collection errors).
      Reverted (features@a4bec8ec restores deep imports). The check tool needs to either (a) verify the symbol exists
      at top level before suggesting/applying the rewrite, OR (b) allowlist `unified_trading_library.feature_service_base`
      as a legitimate submodule (alternative: add the missing re-exports to UTL `__init__.py`). Current state:
      features-service tests/lint/typecheck all GREEN but QG import-pattern gate still RED because the original deep
      imports remain (correctly) in place.
- [ ] [BUG][P1] **1.7c test_orchestration_flow MagicMock leak — `get_settings().base_timeframe` not mocked.** Surfaced
      after 1.7b fix unblocked the calculator pipeline. Phase-1 read-once work introduced `get_settings().base_timeframe`
      lookups; the e2e test in `tests/delta_one/e2e/test_end_to_end.py:60` mocks `get_settings()` but doesn't return a
      real string for `base_timeframe` → "Could not convert MagicMock... did not recognize Python value type when
      inferring an Arrow data type" → orchestration silently fails → `write_features_batch.called` is False. Fix: update
      the conftest / test fixture to return a real string from `mock_settings.base_timeframe`. Test-only; no runtime
      bug. Provenance: full QG run 2026-05-28.

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
- [ ] [P2] **2.6 Real-data distribution sanity** (beyond NaN): per-feature on real candles — flag all-zero, stuck
      values, absurd variance/outliers ("computes but wrong").
- [ ] [P3] **2.7 Cross-timeframe sanity**: a feature at 4h vs 1h relates within bounds; flags TF-label/wiring mistakes.

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
