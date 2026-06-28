---
doc_type: plan
title: Full-month MDPS+features benchmark on a Binance shard — time, memory, cost
summary:
  "Run MDPS+features over a full month of a most-liquid Binance shard and capture wall-time, peak+retained RSS, output
  bytes, object count, and estimated egress $ — current engine vs pure-Polars — to produce a per-shard cost model for
  the candle+feature artifact."
status: draft
nature: process
asset_group: [cefi]
stage: [data, features]
repos: [market-data-processing-service, features-service]
scope: [engineer, admin]
tags: [benchmark, cost, memory, rss, egress, polars, binance, full-month, smoke-test]
related:
  [
    ./mdps_features_reduced_artifact_tracker_2026_06_28.md,
    ./mdps_polars_engine_cost_sharpening_2026_06_28.md,
    ./honest_coverage_smoke_harness_2026_06_28.md,
    ../audit/results/mdps_engine_benchmark_findings_2026_05_28.md,
  ]
created: 2026-06-28
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-28
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on: [mdps_book_microstructure_precompute_columns_2026_06_28, honest_coverage_smoke_harness_2026_06_28]
source: [operator request 2026-06-28]
---

# Full-month MDPS+features benchmark on Binance

The capstone smoke + cost benchmark. Run the full candle+feature pipeline over a **full month of a most-liquid Binance
shard** and measure how long it takes, how much memory it needs, and what it costs — so we have a per-shard cost model
to multiply across the MVP universe (and a hard number on the Polars cost-sharpening before/after).

**Why Binance, not BITGET:** Binance is the most-liquid representative and the feature-MVP crypto spot default (Plan 3),
so the benchmark doubles as the universe smoke test. (BITGET was only ever a fallback because it had recent
processed_candles.)

**Execution model:** Sonnet to run the benchmark + collect metrics (script-and-verify). Opus for the analysis/cost-model
synthesis across the two engine variants.

**Prereqs:** Plan 1 (candle carries book columns — so we benchmark the real, complete artifact) + Plan 6 (coverage
harness — pick the RUNNABLE Binance shard, confirm a genuine full-month window).

## Metrics to capture (per run)

- Wall-time (total + per-day), via the audit canary shape (e2-standard-8, 32 GB, MAX_WORKERS pinned).
- **Peak RSS and retained RSS** after each day (the arena-leak signal from the 2026-05-28 audit).
- Output bytes + object count (candles + features).
- Estimated egress $ = output GB × the GCP-egress/AWS-ingress rate from
  `codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md`.

## Todos

- [ ] [DESIGN] P1. Pick the Binance shard (venue, instrument, data_types incl. book) + the full month, confirmed
      RUNNABLE by Plan 6's harness. Declare the benchmark matrix: {current engine, pure-Polars} × {MDPS only,
      MDPS+features}. — Gate: a named shard + month + a RUNNABLE classification from the harness recorded here.
- [ ] [IMPLEMENT] P1. Benchmark runner that executes each cell on real infra, capturing wall-time, peak+retained RSS
      (sampled), output bytes, object count; emits a structured results table. Reuse the 2026-05-28 canary harness
      pattern; do not hand-roll memory telemetry. — Gate: runner produces the results table for at least the
      current-engine cells on the real shard.
- [ ] [VERIFY] P1. Full-run both engine variants over the full month on real infra (Plan 8 supplies the Polars path; if
      Plan 8 hasn't landed, run current-engine now and add the Polars column when it does — note the deferral). — Gate:
      per CLAUDE.md full-execution — command + VM name + duration + the metrics table for each completed cell.
- [ ] [IMPLEMENT] P1. Build the **per-shard cost model**: $/shard-month and RSS/shard for the artifact, with the formula
      to extrapolate across the MVP universe (shard count × per-shard cost). — Gate: a cost-model table + total-universe
      estimate; egress $ cites the cost-analysis rate.
- [ ] [AGENT] P1. Commit the benchmark report + cost model (no `*_SUMMARY.md` doc — results live in this plan's Progress
      Log + a committed results artifact); quickmerge any benchmark-runner code `--agent --files`. — Gate: QG green on
      touched repos; report committed.

## Min-window correction (audited 2026-06-28)

A "full month" is NOT automatically the right window. Min window =
`max over feature families of (lookback_periods × coarsest_timeframe)`: a 200-period feature at 24h needs ~200 trading
days even on a 15s base. So the benchmark window is **read from Plan 6's required-window registry for the chosen Binance
shard**, not fixed at one month — if the heaviest feature family is 1m-only, a month is ample; if a 24h-200-period
family consumes it, the run must cover the longer window (or explicitly scope to the 1m families and SAY SO). The
benchmark report MUST state which feature families it exercised and at which window, so the cost/RSS numbers are
interpretable.

## Notes

- This is the evidence that justifies Plan 8 (cost-sharpening): the current-vs-Polars columns should reproduce the
  audited 3× wall / 5× peak RSS / 7.8× retention deltas on a real full month, not just the 9-instrument micro-benchmark.
- B3 KPI (data pipeline): declare target $/shard-month + peak RSS ceiling so "fast + cheap enough" is checkable, not a
  judgment call.
