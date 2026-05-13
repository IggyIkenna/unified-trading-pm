---
title: Compute-bound stage optimization via mock data — parallelize + big-machine the slow stages before cutover
type: plan
status: active
created: 2026-05-13
deadline: 2026-05-23
horizon: ~10-day pre-cutover sprint
companion_to: master_to_live_defi_2026_05_23.md (Group F items 17/18/20/21)
locked_by: live-defi-rollout
locked_since: 2026-05-13
priority: P1
parent_epic: strategy_and_dart_master_2026_05_07.md
mvp_universe_ssot: codex/09-strategy/mvp-universe-per-asset-group.md
spawned_from: operator direction 2026-05-13 — "instrument backfill may take 1-2 days, MTDS similar even when working; features + 3 sets of backtests (strategy combo / execution alpha / ML training) on top; have any plans optimised the non-I/O-blocked stuff?"
related_plans:
  - plans/active/mock_data_pipeline_benchmarking_2026_05_10.md
  - plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md
  - plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/defi_simulation_realism_2026_05_10.md
  - plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md
related_codex:
  - codex/06-coding-standards/performance-targets.md
  - codex/05-infrastructure/runtime-tiers-and-deployment.md
  - codex/05-infrastructure/vm-tarball-deployment.md
  - codex/04-architecture/batch-live-architecture.md
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: |
  Design class (instrumentation + parallelization wiring + big-machine SKU rollout); baseline 8 (per-stage analysis,
  parallel-batch wiring across 4-5 stages, SKU matrix experiments, dependency-order doc). × 0.6 = 4.8 calibrated.
  Heavy lift is in features-service + strategy backtest config-grid + execution-alpha measurement; ML training
  optimization is mostly upstream framework (lightgbm + torch dataloader) tuning.
---

# Compute-bound stage optimization via mock data

## Why this plan exists

The mock-data benchmarking plan ([`mock_data_pipeline_benchmarking_2026_05_10.md`](mock_data_pipeline_benchmarking_2026_05_10.md))
**measured** per-stage CPU / RSS / wall-clock on `c2-standard-{8,16,30}` + `c3-highcpu-44` shapes — Phases 0-7 shipped, VM-shape
matrix populated in `gs://central-element-323112-benchmark-reports/`. That work answered *"how slow is each stage?"*.

This plan answers the next question: ***"can we make the compute-bound stages much faster so cutover-window wall-clock
shrinks?"***

**Operator's framing 2026-05-13**: real-data backfills are wall-clock-bound (instruments-service 1-2 days, MTDS similar
even when working perfectly), and three downstream stages stack on top:

1. **Features-service compute** (per-asset_group × per-archetype × per-day × 730 days for 2-yr backfill)
2. **Strategy backtest config-grid** (Group F item 18 — flagged AUTHOR-MISSING in master plan)
3. **Execution-alpha measurement** (live-fills P&L − simulated-fills P&L, per archetype × per window)
4. **ML training + retraining cadence** (TradFi swing-prediction daily retrain; per-archetype ML models)

These stages are I/O-light + compute-heavy. They can be pre-tuned with synthetic data NOW (schemas stable per
`unified_api_contracts.canonical.domain.*`) without waiting for real backfills.

### Backtest window per asset_group (operator clarification 2026-05-13)

Walk-forward training validation loops require longer history for ML-heavy archetypes:

- **DeFi + Prediction**: 2-year backtest window (730 days). DeFi venues mostly <5yr old; Polymarket launched 2020.
- **CeFi + TradFi + Sports**: **5-year backtest window** (1825 days). Walk-forward ML validation requires multi-regime history. Worker counts ~2.5× larger than the prior 2-yr estimates.

Per `codex/09-strategy/mvp-universe-per-asset-group.md` § "Backtest config-grid sizing math" — total ~580K-1.3M
worker-runs at the 5-yr/2-yr mix. With 4× `c3-highcpu-176` concurrent shards: ~2 hours wall-clock per
archetype-bundle. Bigger-SKU strategy in Phase 5 is now critical (not optional).

**Strategic value**: optimization shortens cutover-window critical-path wall-clock + de-risks "live trading day 1 hits a
slow code path and times out". Mock-data approach means **we don't gate this work on real-backfill completion** — full
parallel track to the data-pipeline workstream.

## Bottleneck profile (from benchmarking plan outputs)

Per the benchmark plan's Phase 5/6 outputs (synthetic 1-day window, row_count_scale=0.1, on `c3-highcpu-44`):

| Stage | Wall-clock | CPU% | Threading | Scale-up signal |
|---|---:|---:|---|---|
| `mtds_read` | 6.91s | 36% | 1.5 cores | **I/O-bound** — parallel batching helps |
| `mdps_compute` | (TBD per-archetype) | (TBD) | (TBD) | **compute-bound** — Phase 3.D wire-in pending |
| `features_compute` | (TBD per-archetype) | (TBD) | (TBD) | **compute-bound** — Phase 3.D wire-in pending |
| `strategy` | 5.55s | **196%** | 2 cores | **CPU-bound parallel** — bigger machine helps |
| `ml_inference` | (TBD per-archetype) | (TBD) | (TBD) | **compute-bound** — Phase 3.D wire-in pending |
| `matching_engine` | (TBD per-archetype) | (TBD) | (TBD) | execution-service scope; varies per matcher class |

Production scale = ~730× the synthetic window (2-yr backfill) × per-archetype × per-config-grid-cell.
Rough back-of-envelope: 730 days × 5.55s strategy × ~20 config-grid cells = ~22 hours per archetype, serial.

**With per-day parallelization** (730-way fan-out on c3-highcpu-176 or m3-ultramem-160): wall-clock drops to ~minutes.

## Scope + non-goals

### In scope (must ship by 2026-05-23)

1. **Per-stage parallelization patterns** identified + wired for MDPS / features / strategy / ml-inference / execution alpha / ML training.
2. **Big-machine SKU matrix** extended beyond `c3-highcpu-44` to: `c3-highcpu-88` / `c3-highcpu-176` / `m3-megamem-128` / `m3-ultramem-160` (where appropriate per stage memory profile).
3. **Per-day fan-out wrapper** for backtest config-grid runs (730-day backfill window across 20-30 config cells).
4. **Execution-alpha measurement at scale** — paired-run harness (live-mode fills + simulated-mode fills, identical seeds, diff = alpha).
5. **ML training parallel-config-grid** — hyperparameter sweeps in parallel using mock training data.
6. **Dependency-ordering doc** for orchestrator: which stages can run while real backfill is happening vs which must follow.
7. **Performance targets** committed in `codex/06-coding-standards/performance-targets.md` (CREATE — currently referenced as missing in benchmarking plan).

### Non-goals (post-cutover or out-of-scope)

- Code-level micro-optimizations beyond what stage-level parallelization gives us (Cython rewrites, GPU kernels, etc.).
- Optimizing live-mode pipeline (already covered by `live_pipeline_mtds_mdps_features` Phase 5+).
- Real-data validation runs (those happen post-backfill; this plan ships the harness + tuning, not the verified runs).
- Optimizing reference-data ingestion (instruments-service is mostly API-bound, not compute-bound).

## Phased execution DAG

### Phase 0 — Pre-audit + stage-bottleneck classification (Day 1, ~0.5 cal-AI-days)

- [ ] [SCRIPT] P0. Read benchmark Phase 5/6 output parquets from `gs://central-element-323112-benchmark-reports/` and produce per-stage `compute_bound_vs_io_bound` classification. For each stage: (a) CPU% headroom, (b) RSS at p95, (c) read/write bytes ratio, (d) thread count observed, (e) per-core scalability prediction. Output: `codex/06-coding-standards/performance-targets.md` (NEW) § Per-stage bottleneck table.
- [ ] [SCRIPT] P0. Identify the **3 slowest stages** (by total cutover-window contribution = wall-clock × call-count × scale-factor). These are the optimization priorities.

### Phase 1 — Per-day fan-out wrapper for backtest config-grid (Days 2-3, ~1.5 cal-AI-days)

> **CORRECTION 2026-05-13**: `strategy-service/scripts/run_2yr_config_grid_backtest.py` ALREADY EXISTS (886 lines).
> Master plan flag "AUTHOR-MISSING" is stale. Phase 1 scope is **VERIFY + EXTEND** the existing script with the
> Tier A archetypes per `codex/09-strategy/mvp-universe-per-asset-group.md` (the 6 Tier A archetype families:
> ml-continuous, ml-settled, arbitrage-funding-rate, arbitrage-sports-book, arbitrage-event-markets, defi-carry-family).

- [ ] [SCRIPT] P0. **VERIFY** `strategy-service/scripts/run_2yr_config_grid_backtest.py` actually covers all 6 Tier A archetype families + uses `target_universe/catalog.py` as the rollout-instance SSOT + uses UAC `StrategyArchetype` enum for archetype iteration. If gaps found, **EXTEND** rather than rewrite.
- [ ] [SCRIPT] P0. Add `--max-parallel` CLI flag (default = SKU's CPU count); writer-side use UTL `ParallelPerSymbolRunner` pattern with shard-level isolation (CLAUDE.md HARD RULE).
- [ ] [SCRIPT] P0. Wire results aggregation: per-(config_cell, date_chunk) summary → cross-chunk P&L roll-up → master config-grid CSV. Mock-data smoke run = end-to-end exit on synthetic 30-day window in <5 min on c3-highcpu-44.

### Phase 2 — Features-service parallel batching (Days 3-5, ~1 cal-AI-day)

- [ ] [SCRIPT] P0. For each features-service family (delta_one, onchain, volatility, calendar, cross_instrument, commodity, sports), profile compute cost per `feature_group × per-day × per-instrument`. Identify which family is most expensive (likely onchain or volatility based on DAG depth).
- [ ] [SCRIPT] P0. Add `--worker-count` CLI flag to consolidated features-service CLI. Wire shard-level batch-parallel calculator runs. Verify on synthetic data: `--worker-count 88` on c3-highcpu-88 gives near-linear speedup vs serial.
- [ ] [SCRIPT] P1. Identify any feature_group whose `required_inputs` DAG forces serial computation; flag for post-cutover refactor (not blocking May-23 — those stages just run on the smallest SKU that fits memory).

### Phase 3 — Execution-alpha measurement at scale (Days 5-7, ~1 cal-AI-day)

- [ ] [SCRIPT] P0. Author `execution-service/scripts/run_execution_alpha_measurement.py`. Per-(archetype, date_window): runs the matching-engine in BOTH `always_fill` (alpha-zero benchmark) AND `realistic_fills` (per-matcher class) modes with identical input order book + identical seeds. Output = per-archetype P&L delta = execution alpha.
- [ ] [SCRIPT] P0. Parallel-shard wrapper: 730 days × 2 archetypes × 2 fill-modes = 2920 worker runs. Fits on `c3-highcpu-176` with 16-day chunks → 183 chunks per shape, all parallel.
- [ ] [SCRIPT] P0. Mock-data smoke: synthetic 5-day window per archetype, both fill modes, verify diff > 0 + within expected magnitude.

### Phase 4 — ML training + retraining parallel config-grid (Days 6-8, ~1 cal-AI-day)

- [ ] [SCRIPT] P0. Confirm ml-training-service has a `--hyperparam-grid-file` CLI flag. If not, add it (per-archetype) — accepts a JSON list of hyperparameter dicts, runs each in parallel.
- [ ] [SCRIPT] P0. Mock training data harness: use synthetic features-output parquets from Phase 2 to drive ml-training without real backfill. Verify training completes + writes `model.pkl` + `model_card.json` end-to-end.
- [ ] [SCRIPT] P1. Identify the per-stage time spent in (a) dataloader vs (b) GPU/CPU compute vs (c) checkpoint write. If dataloader >40% → wire `num_workers` properly; if checkpoint >20% → defer to background thread.

### Phase 5 — Big-machine SKU matrix extension (Days 7-9, ~0.5 cal-AI-day)

- [ ] [SCRIPT] P0. Extend benchmark harness shape list from current `{c2-standard-8, c2-standard-16, c2-standard-30, c3-highcpu-44}` to add `c3-highcpu-88` / `c3-highcpu-176` / `m3-megamem-128` / `m3-ultramem-160`. Per-stage decision: which SKU gives best `cal-AI-day-per-$` for the cutover-window run.
- [ ] [SCRIPT] P0. Run the extended matrix on the 3 slowest stages identified in Phase 0. Output: `codex/05-infrastructure/runtime-tiers-and-deployment.md` § "Per-stage SKU recommendation matrix" UPDATE with cutover-window-sized recommendations.
- [ ] [SCRIPT] P1. Spot-instance / preemptible-VM viability check: for the longest-running shapes, would preemptible save ≥40% cost? If yes, design checkpoint-restart for those stages (post-cutover wire-in).

### Phase 6 — Orchestrator dependency-ordering doc (PULLED FORWARD 2026-05-13, ~0.5 cal-AI-day)

- [x] [SCRIPT] P0. **SHIPPED 2026-05-13** — `codex/08-workflows/cutover-window-dependency-order.md` authored with full 2026-05-13→05-23 checkpoint timeline, serial data-pipeline track vs parallel code-and-tests track distinction, per-asset_group backtest window (5yr CeFi/TradFi/Sports, 2yr DeFi/Prediction), per-Tier-A archetype sizing (operator estimate ~0.5 day per backtest/strategy/ML optimization with concurrent loops), and slot-scheduling guidance for slot 1 main per-day allocation. Cross-references master plan + per-asset-group epics.
- [ ] [SCRIPT] P0. Cross-reference from master plan Group F items 17/18/20/21 + `code_freeze_migrate_backfill_sequencing` Phase 2/3 cutover-window section. (Master plan banner already references via MVP SSOT row 2026-05-13; broader F17/18/20/21 row references to dependency-order doc pending.)

### Phase 7 — Performance-targets codex SSOT (Day 9-10, ~0.3 cal-AI-day)

- [ ] [SCRIPT] P0. Author `codex/06-coding-standards/performance-targets.md`. Per-stage acceptable wall-clock targets at production scale (2-yr backfill on production SKU). These become CI assertion gates (post-cutover hardening).

## Mock-data sufficiency caveat

This plan's optimization work is valid IFF the schemas are stable. Per CLAUDE.md "writegate" + UAC discipline:
- UAC canonical schemas are the SSOT for all column shapes.
- Mock data uses UAC `unified_api_contracts.canonical.domain.<asset_group>.<data_type>` Pydantic models to generate synthetic columns matching production exactly.
- If the writegate plan ships a column rename / additional-column / type-change AFTER Phase 0-2 here, the mock harness MUST regenerate. Risk-monitor: `unified-api-contracts/` commits affecting `canonical/domain/` between today and 2026-05-23.

**Schema freeze checkpoint**: by 2026-05-15 freeze gate (per master plan), UAC schemas are LOCKED. Optimization runs from 2026-05-15 → 2026-05-21 land against stable schemas. Real backfill drains 2026-05-15 → 2026-05-19 (per `code_freeze_migrate_backfill_sequencing` Phase 2-3). **Optimization + real backfill run in parallel** — that's the whole point.

## Dependency order — what orchestrator should know

```
TIMELINE (calendar-day rough estimate):

Day 0 (today, 2026-05-13)
  ├─ Phase 0 audit (depends on benchmark plan outputs in GCS — already there)
  └─ Phase 1 backtest 730-day fan-out wrapper draft

Days 2-5 (2026-05-15 freeze gate window)
  ├─ Phase 1-4 in parallel — all mock-data; no real-backfill dependency
  │
  └─ REAL BACKFILL ALSO RUNNING (separate workstream):
     instruments-service backfill → MTDS backfill → drains 2026-05-15 → 2026-05-19

Days 5-8 (2026-05-18 → 2026-05-21)
  ├─ Phase 5 big-SKU matrix runs (parallel with real backfill)
  ├─ Phase 6 dependency-order doc + Phase 7 performance-targets
  └─ FIRST REAL-DATA CUTOVER-WINDOW DRESS REHEARSAL: real backfill outputs
     feed optimized pipeline. THIS IS THE CRITICAL TEST.

Days 8-10 (2026-05-22 → 2026-05-23)
  └─ Cutover. Pipeline runs end-to-end with optimized stages.
```

**Critical insight for orchestrator**: stages 1-7 can be scheduled on slots **TODAY** without waiting for backfill. The benchmark harness is already shipped. Mock data generators exist. SKU choices are configurable.

## Done definition

**Full-execution criterion**:
- ✅ `strategy-service/scripts/run_2yr_config_grid_backtest.py` exists + runs on mock data end-to-end (Phase 1).
  - **What ran**: synthetic 30-day × 20 config cells × 2 archetypes on `c3-highcpu-44`.
  - **Verification**: exit 0, output `gs://central-element-323112-benchmark-reports/strategy_backtest_2yr/<date>/grid_summary.parquet` (NEW path).
- ✅ Features-service `--worker-count` flag accepts + scales near-linear on mock data (Phase 2).
- ✅ `execution-service/scripts/run_execution_alpha_measurement.py` exists + per-archetype P&L delta non-zero on mock data (Phase 3).
- ✅ ml-training `--hyperparam-grid-file` works on synthetic features (Phase 4).
- ✅ Extended SKU matrix profile parquets in `gs://central-element-323112-benchmark-reports/sku_matrix_v2/` (Phase 5).
- ✅ `codex/08-workflows/cutover-window-dependency-order.md` shipped + cross-referenced from master plan (Phase 6).
- ✅ `codex/06-coding-standards/performance-targets.md` shipped (Phase 7).

**Operator authority + ADC**: all SKU provisioning + VM launches use GCP `central-element-323112` ADC (per CLAUDE.md "Plans Run To Actual Completion" — operator does NOT need to approve VM launches).

## Risk + mitigation

| Risk | Mitigation |
|---|---|
| Schema drift between mock harness + production after 2026-05-15 | Schema freeze gate; QG STEP enforces UAC `canonical/domain/` no-edit window 2026-05-15→2026-05-23 |
| Big-machine SKUs not available in `asia-northeast1-c` quota | Verify quota via `gcloud compute regions describe` Phase 0; if needed switch zone within asia-northeast1 |
| Optimization breaks correctness | All Phase 1-4 outputs cross-check against benchmark Phase 5/6 single-shape outputs (already shipped); diff > 0 → bug, not speedup |
| Execution alpha measurement diverges from real fills | Mock validation only; real verification = cutover-window dress rehearsal Day 7-8 |
| ML training data leak (mock features bleed into mock labels) | Mock generator uses RNG seed-isolation between feature-gen and label-gen; verified via leakage assertion test |

## Cross-plan handshakes

- **mock_data_pipeline_benchmarking_2026_05_10** — Phase 3.D bespoke reader wire-in still pending; this plan does NOT block on Phase 3.D since we run the prod-pipeline subprocess mode with `--synthetic-input-uri` flag once Phase 4 wires it.
- **live_pipeline_mtds_mdps_features_2026_05_08** — live-mode optimizations are out-of-scope here; only batch/backtest mode.
- **code_freeze_migrate_backfill_sequencing_2026_05_10** — Phase 2 cutover-window timeline is the binding constraint; this plan's optimization output FEEDS that plan's wall-clock budget.
- **defi_simulation_realism_2026_05_10** + **simulation_scenarios_topology_price_shocks_2026_05_09** — scenarios drive backtest config-grid cells; integration via `--scenario-overlay-uri` flag.

## Owner

Suggested: features-service maintainer slot (Phases 1+2) + execution-service maintainer slot (Phase 3) + ml-training maintainer slot (Phase 4) + benchmark harness owner (Phase 5) + slot 1 main (Phases 6+7 codex SSOTs) — 4 implementer slots + 1 PM slot, all distributable across existing density-push cycles.
