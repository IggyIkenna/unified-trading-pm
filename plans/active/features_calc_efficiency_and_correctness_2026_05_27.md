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
> auto-assign / auto-fix / push to LDR.** See `plans/active/_agent_pings.md`. Banner removed by harsh-side when released.

## Goal

Two operator-prioritised concerns about the features calculation pipeline (`read → calculate → write`):

1. **Efficiency** — the cost is **I/O (read + write), not compute**. Make the pipeline efficient given: we read large
   candle volumes per (instrument × timeframe × day), some features depend on others (feature DAG — features are not
   absolute), and we backfill multiple days (so lookback windows overlap day-to-day).
2. **Correctness** — verify the ~thousands of feature functions are computed correctly: not just NaN handling (caught
   2026-05-26) but the **actual values, labels, timeframes, configs, dimensions, and input/output wiring**. We trust
   ta-lib's indicator *math* (battle-tested); the risk is OUR wrapping + the **custom** (non-ta-lib) features (swing
   high/low, market structure, wedges).

Sibling plan `features_service_e2e_pipeline_test_2026_05_26.md` covers the e2e read/write *plumbing* (buckets, manifest,
the timeframe-coverage loop). This plan is the I/O *efficiency* + feature-*correctness* layer on top.

## Pre-audit (grounded 2026-05-27)

- **The 7× read problem is live**: the Phase-6.A timeframe loop (delta_one@7bd77525) reads candles **once per output
  timeframe** (7 reads/instrument/day) → blew the 10-min e2e timeout; operator flagged read-once as the fix.
- delta_one reads candles via `app/core/data_loader.py`; computes via the per-feature-group calculators (some wrap
  ta-lib: `MultiPeriodFeatureGenerator`, `app/calculators/technical.py`; custom: swing/market-structure/wedge); writes
  per-(instrument × feature_group × timeframe × day) parquet via `feature_writer.py` (one small object per shard).
- `TimeframeResampler` (`app/core/timeframe_resampler.py`) resamples *feature values* + flags indicators needing recalc
  → unsuitable for indicators; but **candle** resampling (OHLC `first/max/min/last/sum`) IS exact and is the efficiency
  lever.
- mtf re-reads delta_one output **from GCS** (a read that an in-memory DAG could avoid for colocated runs).
- 2026-05-26 correctness signal so far is shallow: "0 all-NaN" existence checks + one swing bug. No ta-lib-equality
  tests, no per-feature invariants, no lookahead audit, no dimension/label/config consistency check.

## Phased DAG (QG gate between phases)

### Phase 1 — I/O efficiency `[P1]`

Principle: minimise reads + writes; compute is cheap. Measure each change against the 7×-read baseline (delta_one CEFI
2026-05-03 wall-clock).

- [ ] [P1] **1.1 Read base candles once → resample candles in-memory to all output timeframes.** Replace the per-TF
  candle re-read in the Phase-6.A loop with: read 15s/1m for the lookback window once, OHLC-resample to
  {5m,15m,1h,4h,24h} in memory (exact aggregation), compute features per TF. Target: 7 reads → 1. (`data_loader.py` +
  the `_process_feature_group` loop + a candle-resampler — NOT `resample_features`.)
- [ ] [P1] **1.2 Read the lookback window once across a date range.** Day-by-day re-reads overlapping history each day.
  Process a date RANGE in one job: read the span once, slide an in-memory window, emit each day. Removes repeated
  lookback re-reads (the operator's "we already pull multiple days" point).
- [ ] [P2] **1.3 Batch the writes.** We emit thousands of tiny per-shard parquets; GCS small-object write latency
  dominates. Buffer + flush per partition-group (fewer, larger objects) — measure write-count + wall-clock. (Trades off
  against the per-instrument partition layout readers expect — design carefully; coordinate with the writegate.)
- [ ] [P2] **1.4 Feature dependency DAG — reuse intermediates in memory.** Compute in dependency order; pass derived
  features in-memory instead of write-then-reread. For colocated mtf/cross_instrument, read delta_one from memory, not
  GCS. (Requires a declared feature dependency graph — overlaps Phase 2's registry.)
- [ ] [P2] **1.5 Idempotent skip + column pruning + predicate pushdown.** Skip already-written partitions; read only the
  columns + date-range each calculator needs.
- [ ] [P3] **1.6 Parallelism tune.** I/O-bound → MAX_WORKERS≈16 across instruments × timeframes; measure RAM (85%→halve).

### Phase 2 — Feature-function correctness verification `[P1]`

Principle: trust ta-lib's math; verify OUR wiring + the custom features. Scale to ~thousands via a registry; reserve
hand-written goldens for custom families.

- [ ] [P1] **2.1 Feature registry (declarative SSOT).** Each feature declares: input columns, timeframe, period/config,
  output name, dtype, valid range, and ta-lib-backed-vs-custom. Audit registry-vs-reality: declared input == column
  actually consumed; output name == what's written; period config == applied. (The "right dimension / right
  input/output" check.)
- [ ] [P1] **2.2 ta-lib-equality tests** for every ta-lib-backed feature: assert our output == direct ta-lib(input) on a
  fixture. Catches wrong-column / wrong-period / wrong-output wiring cheaply across the masses.
- [ ] [P1] **2.3 No-lookahead audit (PIT) — all features.** Shift input by +1 bar; assert feature at t is unchanged by
  t+1 data. The deadliest trading bug; auto-applied from the registry.
- [ ] [P1] **2.4 Registry-driven invariants — all features.** Auto-generate range (RSI∈[0,100], ADX≥0, *_ratio∈[0,1]),
  NaN-policy, dtype checks across every feature.
- [ ] [P1] **2.5 Custom-feature golden + edge fixtures.** Hand-built fixtures for swing high/low, market-structure,
  wedge-convergence, `tf_*` alignments: known price series with hand-marked expected pivots/labels + edge cases
  (insufficient bars, all-NaN, constant, single bar, gaps/no-trade, plateaus, monotonic, boundary bars). These are the
  real risk (no library to lean on; one swing bug already found 2026-05-26).
- [ ] [P2] **2.6 Real-data distribution sanity** (beyond NaN): per-feature on real candles — flag all-zero, stuck
  values, absurd variance/outliers ("computes but wrong").
- [ ] [P3] **2.7 Cross-timeframe sanity**: a feature at 4h vs 1h relates within bounds; flags TF-label/wiring mistakes.

## Success criteria

- Phase 1: delta_one CEFI full-TF run reads candles **once** (not 7×) + completes well under the old 10-min budget;
  write-count materially reduced; measured speedup recorded.
- Phase 2: registry covers 100% of emitted features; ta-lib-equality + lookahead + invariant suites green; custom-feature
  goldens green; ≥1 real wiring/label/config or lookahead bug surfaced + fixed (or a clean bill with evidence).

## Codex SSOT updates (HARD RULE)

- `codex/02-data/` — feature-calculation I/O-efficiency pattern (read-once + candle-resample; range-read; write-batch).
- `codex/06-coding-standards/` — feature-correctness verification standard (registry + ta-lib-equality + lookahead +
  edge fixtures); enumerate before archival.

## Notes / cross-refs

- Phase-6.A timeframe loop (delta_one@7bd77525) is the read-once optimisation's baseline (it intentionally re-reads
  per TF for correctness first; 1.1 optimises it).
- Composes with HARD RULE _Data Pipeline Correctness Is The Heartbeat_ — a wrong feature value is the same class of
  divergence as a phantom `captured`.
- 24h features remain blocked on upstream CeFi candle coverage (only 3 days exist; 24h indicators need ≥14) — a data
  backfill, tracked in the e2e plan.
