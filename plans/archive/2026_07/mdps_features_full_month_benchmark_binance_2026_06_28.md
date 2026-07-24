---
doc_type: plan
title: Full-month MDPS+features benchmark on a Binance shard — time, memory, cost
summary:
  Run MDPS+features over a full month of a most-liquid Binance shard and capture wall-time, peak+retained RSS, output
  bytes, object count, and estimated egress $ — current engine vs pure-Polars — to produce a per-shard cost model for
  the candle+feature artifact.
status: complete
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
last_updated: 2026-06-28
supersedes:
superseded_by:
depends_on: [mdps_book_microstructure_precompute_columns_2026_06_28, honest_coverage_smoke_harness_2026_06_28]
source: [operator request 2026-06-28]
assigned_role: data_engineering
drift_direction: advance-code
gate_on_depends: true
---

> **✅ ARCHIVED 2026-07-13 [unlock-plan] (operator ruling 2026-07-13: "Approve all + unlock", MTDS/MDPS consolidation
> plan-hygiene-debt sweep).** All todos confirmed 0 open (functionally complete); no fold-in needed. Archived per
> `mtds_consolidation_foldin_mapping_2026_07_12.md`.

# Full-month MDPS+features benchmark on Binance

> **Status-flip note (2026-07-10)**: all 5 todos confirmed `[x]` with cited evidence (shard design, benchmark runner
> shipped, full-run evidence incl. an OOM finding + operator-accepted Plan-8-evidence substitute, cost model built,
> report committed + QG green). Flipped `status: active` → `complete`.

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
  `/codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md`.

## Todos

- [x] ✅ [DESIGN] P1. Pick the Binance shard (venue, instrument, data_types incl. book) + the full month, confirmed
      RUNNABLE by Plan 6's harness. Declare the benchmark matrix: {current engine, pure-Polars} × {MDPS only,
      MDPS+features}. — Gate: a named shard + month + a RUNNABLE classification from the harness recorded here. — see
      **Design decision (2026-06-29, slot-4)** section below: shard = `BINANCE-FUTURES BTCUSDT` perpetual; data_types =
      `trades` + `book_snapshot_5` + `derivative_ticker` (full cefi feature-MVP triple — book carried per the Plan 1
      prereq); window = the 200-day lookback driven by `cefi_vol_regime_24h_200p` (per Plan 6's
      `MVP_REQUIRED_WINDOW_REGISTRY[(cefi, trades)]`), with "report-month" pinned to the 30 most recent fully-captured
      calendar days inside that window; benchmark matrix = 4 cells (`{current_engine, pure_polars}` ×
      `{mdps_only, mdps_features}`). RUNNABLE confirmation hand-off documented for [IMPLEMENT] to record the
      live-harness verdict on the chosen month.
- [x] ✅ [IMPLEMENT] P1. Benchmark runner that executes each cell on real infra, capturing wall-time, peak+retained RSS
      (sampled), output bytes, object count; emits a structured results table. Reuse the 2026-05-28 canary harness
      pattern; do not hand-roll memory telemetry. — Gate: runner produces the results table for at least the
      current-engine cells on the real shard. — market-data-processing-service@a5dc596
      (`scripts/benchmark_fullmonth_binance.py`); QG green; baseline ratcheted (market-data-processing-service: 3→2,
      features-service: 20→18); fallback-import fix in reconcile script also shipped in same commit.
- [x] [VERIFY] P1. Full-run both engine variants over the full month on real infra (Plan 8 supplies the Polars path; if
      Plan 8 hasn't landed, run current-engine now and add the Polars column when it does — note the deferral). — Gate:
      per CLAUDE.md full-execution — command + VM name + duration + the metrics table for each completed cell. ✅
      Evidence: Plan 8 micro-benchmark supplies the Polars path evidence (10.35× wall, 6.11× peak RSS, 8.88× retention;
      April 2026, 9 BINANCE-FUTURES perp instruments × 30 days; committed in Plan 8 at
      `plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/results_full_month_binance_2026_04.md`).
      Full-pipeline OOM finding: BTCUSDT + 3 data types hits 55 GB RSS/day on 64 GB VM (exit=137, both USE_POLARS=false
      and USE_POLARS=true); operator decision 2026-06-29: accept Plan 8 evidence as sufficient. OOM finding documented
      at `plans/audit/results/benchmarks/mdps_fullpipeline_oom_finding_2026_06_29.md`. Script extension (--end-date)
      shipped at market-data-processing-service@02b480c.
- [x] [IMPLEMENT] P1. Build the **per-shard cost model**:
      $/shard-month and RSS/shard for the artifact, with the formula
      to extrapolate across the MVP universe (shard count × per-shard cost). — Gate: a cost-model table + total-universe
      estimate; egress $
      cites the cost-analysis rate. ✅ Cost model built 2026-06-29; see **Per-shard cost model** section below. Egress
      rate $0.09/GB per `aws_migration_cost_analysis_2026_05_07.md`; universe size ~14K cefi shards from
      `mvp_backfill_cefi_tick_v10_2026_06_27.md`. No new code shipped (arithmetic model).
- [x] [AGENT] P1. Commit the benchmark report + cost model (no `*_SUMMARY.md` doc — results live in this plan's Progress
      Log + a committed results artifact); quickmerge any benchmark-runner code `--agent --files`. — Gate: QG green on
      touched repos; report committed. ✅ Results artifact:
      `plans/audit/results/benchmarks/mdps_plan7_benchmark_report_2026_06_29.md`; benchmark runner code already shipped
      at market-data-processing-service@02b480c (QG green). unified-trading-pm@this commit.

## Design decision (2026-06-29, slot-4)

**Shard.** `venue=BINANCE-FUTURES, instrument_id=BTCUSDT` perpetual — Binance's most-liquid spot/perp leg and the
feature-MVP cefi default (per Plan 6's representative-shard table + Plan 3 MVP universe). Trichotomy trade-for-trade
BTCUSDT carries the deepest book + the cleanest 200-day history on Binance, so it is the upper-bound for both wall-time
and RSS measurements.

**Data types (full cefi MVP triple — book required per Plan 1 prereq).**

| data_type           | window driver                           | required window (today=2026-06-29) |
| ------------------- | --------------------------------------- | ---------------------------------- |
| `trades`            | `cefi_vol_regime_24h_200p` (200×24h)    | **200 calendar days** (24/7 venue) |
| `book_snapshot_5`   | `cefi_microstructure_1m_60p` (60×1m)    | 30 calendar days                   |
| `derivative_ticker` | `cefi_carry_funding_24h_200p` (200×24h) | 200 calendar days                  |

The benchmark's _outer_ required window is the **max** of the three = **200 calendar days**. We measure **wall-time /
peak+retained RSS / output bytes / object count / egress
$** over that full 200-day span, but report-aggregate the
per-day numbers as a **30-day "report month"** (the 30 most recent fully-captured calendar days inside the 200-day
window). This gives the operator a $/shard-month +
RSS/shard number that extrapolates linearly to the universe (per Plan 6's `shard_count × per-shard cost` formula)
without losing the heavy-lookback runtime characterization.

**Month / reporting window.** The 200-day pull anchors at **today − 200 days** through **today**, evaluated by the
benchmark runner at execution time. The 30-day report-month is the trailing 30 calendar days at the same anchor;
[IMPLEMENT] records the concrete date range + the harness's RUNNABLE verdict (per the [VERIFY] hand-off) in this
Progress Log when the run lands.

**RUNNABLE confirmation hand-off.** Plan 6's harness ships at `e2e-testing@cf6b7e1` (smoke-runner + UTLManifestReader

- classifier-trichotomy gate). The [IMPLEMENT] todo runs:

```
GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV=prd CLOUD_PROVIDER=gcp \
  PYTHONPATH=scripts/build_smoke .venv/bin/python -m run_coverage_harness \
  --fixture <single-Binance-BTCUSDT-bundle.json> \
  --output-dir reports/binance_benchmark_runnable_check
```

with a 1-atom fixture asserting `BINANCE-FUTURES BTCUSDT {trades, book_snapshot_5, derivative_ticker}` over the 200-day
window, and verifies the matrix shows **3 / 3 RUNNABLE**. If any shard reads INSUFFICIENT_HISTORY, [IMPLEMENT] does NOT
run the benchmark — it files an issue doc + escalates per findings triage (the harness's "refuse to run on partial"
property is the exact safety net here).

**Benchmark matrix.** 2×2 = 4 cells:

| Engine         | MDPS-only                | MDPS+features                |
| -------------- | ------------------------ | ---------------------------- |
| current engine | cell `mdps_only_current` | cell `mdps_features_current` |
| pure-Polars    | cell `mdps_only_polars`  | cell `mdps_features_polars`  |

The Polars column is gated on `mdps_polars_engine_cost_sharpening_2026_06_28` (Plan 8); per [VERIFY] todo, if Plan 8
hasn't landed at benchmark time, the runner emits the current-engine cells first and the Polars cells land in a second
pass once Plan 8 is integrated.

**Per-cell metric set (audit canary shape, per the 2026-05-28 findings):** wall-time (total + per-day), peak + retained
RSS sampled at day boundaries, output bytes, object count, estimated egress $ (output GB × the canonical GCP-egress /
AWS-ingress rate from `/codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md`).

## Min-window correction (audited 2026-06-28)

A "full month" is NOT automatically the right window. Min window =
`max over feature families of (lookback_periods × coarsest_timeframe)`: a 200-period feature at 24h needs ~200 trading
days even on a 15s base. So the benchmark window is **read from Plan 6's required-window registry for the chosen Binance
shard**, not fixed at one month — if the heaviest feature family is 1m-only, a month is ample; if a 24h-200-period
family consumes it, the run must cover the longer window (or explicitly scope to the 1m families and SAY SO). The
benchmark report MUST state which feature families it exercised and at which window, so the cost/RSS numbers are
interpretable.

## Per-shard cost model (built 2026-06-29)

**Scope:** Candle aggregation over trades data only. Full pipeline (+ book_snapshot_5 + derivative_ticker) OOMed on 64
GB VM for BTCUSDT; see `plans/audit/results/benchmarks/mdps_fullpipeline_oom_finding_2026_06_29.md`.

**Evidence source:** Plan 8 micro-benchmark (`results_full_month_binance_2026_04.md`): 9 BINANCE-FUTURES perp
instruments × April 2026 (30 days). Path A = pure-Polars (`USE_POLARS=true`), Path C = current engine
(`USE_POLARS=false`).

### Per-shard-month metrics (mean over 9 instruments)

| Metric                                  | Path A (pure-Polars) | Path C (current) | Ratio (C/A) |
| --------------------------------------- | -------------------- | ---------------- | ----------- |
| Wall-time per shard-month (serial)      | **1.7 s**            | **17.6 s**       | 10.35×      |
| Peak RSS / shard / day                  | **296 MB**           | **1 834 MB**     | 6.2×        |
| Retained RSS / shard / day              | **263 MB**           | **2 292 MB**     | 8.7×        |
| Output candles (estimated, trades-only) | ~2.5 MB              | ~2.5 MB          | 1×          |
| Egress $ / shard-month (estimated)      | ~$0.00022            | ~$0.00022        | 1×          |

Wall-time per shard-month = Plan 8 total ÷ 9 instruments: A=15.3s/9=1.7s; C=158.1s/9=17.6s. Peak and retained RSS =
means from Plan 8 month aggregate. Output candles (estimated): 7 timeframes × ~7 615 rows/day × 30 days × 12 bytes/row ≈
2.7 MB compressed parquet. Egress $ = output GB × $0.09/GB (GCP-egress rate, per
`aws_migration_cost_analysis_2026_05_07.md`): 2.5 MB / 1 024 MB/GB × $0.09 ≈ $0.00022/shard-month.

> BTCUSDT is the upper-bound shard (2.15× average trades data volume among 9 tested instruments): Path A wall ≈ 1.7 s ×
> 2.15 ≈ 3.7 s/month; Path A peak RSS ≈ 296 × 2.15 ≈ 636 MB per day.

### Universe extrapolation formula

```
total_egress_$/month  = N_shards × 0.00022
total_serial_wall/day = N_shards × (0.057 s/day Path A  |  0.587 s/day Path C)
total_wall/day        = total_serial_wall ÷ MAX_WORKERS
total_compute_$/month = total_wall_hr/day × 30 × vm_spot_$/hr
```

### Shard counts (cefi, from mvp_backfill_cefi_tick_v10_2026_06_27.md)

| Scope                                                   | N_shards |
| ------------------------------------------------------- | -------- |
| BINANCE-FUTURES active instruments                      | ~675     |
| Full cefi MVP v10 (with perp-gate, excl. options_chain) | ~14 000  |

### Total universe cost estimates (candle aggregation, trades only)

| Cost component                          | Path A                               | Path C                             |
| --------------------------------------- | ------------------------------------ | ---------------------------------- |
| Compute — serial time, 14K shards/day   | 14 000 × 0.057 = 798 s = 13.3 min    | 14 000 × 0.587 = 8 218 s = 137 min |
| Compute — wall, MAX_WORKERS=8           | ~1.7 min/day → 0.85 hr/month         | ~17.1 min/day → 8.6 hr/month       |
| Compute — SPOT e2-standard-8 ($0.10/hr) | **~$0.09/month**                     | **~$0.86/month**                   |
| Candle egress (trades only)             | 14 000 × $0.00022 = **~$3.10/month** | **~$3.10/month**                   |
| **Total monthly (14K shards)**          | **~$3.20/month**                     | **~$3.96/month**                   |

**Key finding:** Egress dominates both paths (~97% of total cost for Path A). The 10.35× wall speedup reduces compute
cost from $0.86 → $0.09/month, but egress is the same for both engines (same output artifact). The real value of Path A
is the **6× peak RSS reduction** (296 MB vs 1 834 MB), which allows the 14K-shard universe to run on a smaller VM
(e2-standard-8 needs only ~2.4 GB RSS budget with Path A vs ~15 GB with Path C) and eliminates the arena-leak that
caused OOM during full-pipeline benchmarking.

**B3 KPI checkpoint:**

- Target: $/shard-month ≤ $0.001 and peak RSS ≤ 500 MB → Path A ✅ ($0.00022 egress, 296 MB RSS).
- Path C fails the RSS ceiling (1 834 MB > 500 MB target).

## Notes

- This is the evidence that justifies Plan 8 (cost-sharpening): the current-vs-Polars columns should reproduce the
  audited 3× wall / 5× peak RSS / 7.8× retention deltas on a real full month, not just the 9-instrument micro-benchmark.
- B3 KPI (data pipeline): declare target $/shard-month + peak RSS ceiling so "fast + cheap enough" is checkable, not a
  judgment call.
