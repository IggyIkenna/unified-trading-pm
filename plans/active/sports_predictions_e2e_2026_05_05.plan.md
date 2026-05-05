---
name: sports-predictions-e2e
overview: |
  Drive sports predictions running end-to-end on the live pipeline: feature-service-sports producing
  honest non-NULL features → ML training (Model 2A walk-forward) → strategy-service paper trade
  (ArbitrageStrategy + MLSportsStrategy) → upcoming-fixtures-ui showing predictions. Folds
  sports_e2e_validation_2026_03_27 Phases 2/3/5 (MTDS Tier 2 validation, arb backtest, live pipeline)
  into a single coherent driver, gated on master roadmap Phase 6 deployment activation and the new
  features_sports_honest_coverage plan that's actively shipping.
type: mixed
epic: sports-predictions-e2e
status: in_progress
priority: P0
owner: Iggy
created: 2026-05-05
locked_by: live-defi-rollout
locked_since: 2026-05-05
supersedes: [sports_e2e_validation_2026_03_27.plan.md]
depends_on:
  - sports_roadmap_master_execution_2026_04_21.plan.md
  - utl_base_image_rebuild_and_workflow_unblock_2026_04_22.plan.md
  - features_sports_honest_coverage_2026_05_05.plan.md
  - sports_phantom_recon_and_failure_triage_2026_05_01.plan.md
  - sports_manifest_shard_migration_cleanup_2026_04_21.plan.md
  - canonical_team_mapping_propagation_2026_03_30.plan.md
completion_gates:
  code: C5
  deployment: D5
  business: B5
repo_gates:
  - repo: feature-service-sports
    code: C0
    deployment: D0
    business: B0
  - repo: ml-training
    code: C0
    deployment: D0
    business: B0
  - repo: strategy-service
    code: C0
    deployment: D0
    business: B0
  - repo: execution-service
    code: C0
    deployment: D0
    business: B0
  - repo: market-data-processing-service
    code: C0
    deployment: D0
    business: B0
  - repo: market-tick-data-service
    code: C0
    deployment: D0
    business: B0
  - repo: deployment-api
    code: C0
    deployment: D0
    business: B0
  - repo: deployment-ui
    code: C0
    deployment: D0
    business: B0
---

# Sports Predictions End-to-End

## Context

User reports sports raw-data coverage is at ~100% (or close enough for meaningful league-fixture predictions). The 26+
sports plans in `plans/active/` were cleaned up on 2026-05-05 — 13 superseded plans archived, leaving the focused active
set: backfill execution (apifootball_enrichment, non_apifootball_provider_backfill_launchers, sfi_chunk_parallel), data
integrity (sports_phantom_recon, sports_manifest_shard_migration, canonical_team_mapping_propagation), feature-pipeline
preparation (features_sports_pipeline_deployment, features_sports_upstream_coverage_gaps,
features_sports_honest_coverage), and operational deployment (sports_roadmap_master_execution Phase 6,
sports_scheduler_cron_activation, utl_base_image_rebuild_and_workflow_unblock).

What was missing: a single plan that drives sports predictions from raw data → features → ML → strategy → execution →
UI. This plan is that driver. It folds sports_e2e_validation_2026_03_27 Phases 2/3/5 (which were the closest thing to an
e2e plan but scoped only to MTDS arb validation), drops the 207M-credit Phase 4 backfill expansion (operator decision,
not on the predictions critical path with sports already at 100%), and adds explicit ML-training and UI-verification
gates.

The fold targets:

- **sports_e2e_validation_2026_03_27** (status active, 23 open todos, last updated 2026-04-25): Phases 2/3/5 fold here;
  Phase 4 (cost plan + Tier 1/2 expansion) deferred to operator. Plan archived in the same commit as this plan's first
  push.

This plan does **not** swallow:

- The honest-coverage backfill plan (features_sports_honest_coverage_2026_05_05) — that's the upstream ingest-gating
  plan launched today by the sibling agent; this plan is the downstream prediction driver. They are sequential, not
  duplicate.
- The master roadmap (sports_roadmap_master_execution_2026_04_21) — Phase 6 (deployment activation: Cloud Build trigger,
  sports-scheduler image, terraform apply, INJURIES VM verify) is a hard prerequisite but lives in the master plan.

## Dependency DAG

```
sports_phantom_recon ─┐
                      │
canonical_team_mapping┤
                      ├─→  apifootball_enrichment + non_apifootball_launchers + sfi_chunk_parallel
                      │       │
                      │       ▼ (raw data lands)
sports_manifest_shard ┤
                      │       ▼
                      ├──────→ features_sports_honest_coverage  (NaN-aware feature compute)
                      │       │
                      ▼       ▼
        master_roadmap_phase_6 + utl_base_image_rebuild
                      │       │
                      ▼       ▼
        ┌──────────────────────────────────────────────┐
        │  THIS PLAN: sports_predictions_e2e            │
        │                                               │
        │  Group D → Group E → Group F → Group H → Group I  │
        │  (FSS validate → ML train → strategy paper → │
        │   e2e schema gates → live pipeline)           │
        └──────────────────────────────────────────────┘
                      │
                      ▼
        upcoming-fixtures-ui shows predictions (B5)
```

Phases run sequentially because each gates the next on schema/data-quality acceptance. Within each phase, todos marked
PARALLEL run concurrently.

## Group D — FSS validation against honest coverage

Goal: feature-service-sports produces non-NULL features for the trained universe at the volume + quality the strategy
needs.

Folded from sports_e2e_validation Phase 2 (MTDS Tier 2 1-week validation) plus FSS-specific gates.

- [ ] [SCRIPT] P0. Run MTDS Tier 2 (57 buckets) for 1 recent week — all leagues. Verify output to
      `gs://market-data-tick-sports-{pid}/raw_tick_data/by_date/day=*/`. Reference: codex §12 register.
- [ ] [ANALYSIS] P0. Verify bm_time freshness: ≥18 bookmakers within ±60s at T-10m, T-30m, T-60m, T-120m. Acceptance
      gate before strategy backtest.
- [ ] [ANALYSIS] P0. Arb scan: cross-bookmaker arb opportunities (bm_time ±60s, implied prob > 100%). Quantify count +
      average size.
- [ ] [ANALYSIS] P0. Arb decay by horizon: T-4h vs T-2h vs T-30m vs T-10m. Drives Group F window selection.
- [ ] [ANALYSIS] P0. Arb by league: identify most/least efficient markets. Drives Group F universe filter.
- [ ] [SCRIPT] P1. Run MDPS cleaning pass — filter by bm_time freshness, add buckets per codex §12.
- [ ] [SCRIPT] P1. Run FSS on cleaned data — verify odds features (velocity, CLV, steam) populate at >95% non-NULL for
      in-coverage windows.
- [ ] [SCRIPT] P1. Verify feature matrix is ML-ready (one row per fixture, all features as columns, no NaN where
      coverage says captured).
- [ ] [GATE] P0. Block Group E until FSS produces ≥95% non-NULL features for the trained universe (per
      features_sports_honest_coverage acceptance).

## Group E — ML training validation (Model 2A walk-forward)

Goal: Model 2A walk-forward acceptance metrics ≥ thresholds against fresh features.

- [ ] [SCRIPT] P0. Run ml-training Model 2A walk-forward against the Group-D-validated feature matrix.
- [ ] [ANALYSIS] P0. Acceptance metrics — log-loss, calibration, AUC for win/draw/loss; threshold per consolidated plan
      §Group E (now archived but referenced).
- [ ] [SCRIPT] P0. Training-config sanity check: feature columns match FSS schema, label leakage absent, walk-forward
      windows aligned with fixture dates.
- [ ] [ANALYSIS] P1. Persist model + metrics to ml-models registry; tag model_family=`sports_arb_v1`,
      training_period=`<window>`.
- [ ] [GATE] P0. Block Group F until walk-forward AUC ≥ 0.55 and calibration error ≤ 5% (re-tune if not).

## Group F — Strategy/execution paper trade

Goal: ArbitrageStrategy + MLSportsStrategy in execution-service paper mode produce signals + simulated fills against
live odds.

Folded from sports_e2e_validation Phase 3 (arb_calculator + spread_calculator + strategy-service arb backtest).

- [ ] [CODE] P0. Implement (or verify shipped) `arb_calculator` in FSS: cross-bookmaker arb %, eligible pairs, duration.
      SSOT: codex/14-playbooks/sports/arb-detection.md.
- [ ] [CODE] P0. Implement (or verify shipped) `spread_calculator` in FSS: sharp-soft spread, vig, max-min.
- [ ] [SCRIPT] P0. Run strategy-service arb backtest on Group D's 1-week dataset. Use execution-service "always fill"
      mode for strategy-alpha P&L (per CLAUDE.md "Batch = Live").
- [ ] [SCRIPT] P0. Run strategy-service Model 2A backtest on the same 1-week dataset. Reference UAC signal contract.
- [ ] [SCRIPT] P0. Run execution-service matching-engine pass on the same dataset to compute execution alpha (real-fill
      simulation with slippage/commission/latency).
- [ ] [ANALYSIS] P1. Determine optimal X-hours window for arb (cost vs opportunity, from Group D arb-decay analysis).
- [ ] [GATE] P0. Block Group H until paper-trade strategy alpha is ≥ 0 over the 1-week dataset and execution alpha gap
      is documented.

## Group H — End-to-end schema + freshness gates

Goal: schema and freshness alignment from FSS → ML → strategy → execution → UI.

- [ ] [TEST] P0. Schema parity test: schema-out FSS == schema-in ML == schema-in strategy. Add to UAC
      `tests/test_cassette_schema_parity.py` style (per CLAUDE.md).
- [ ] [TEST] P0. Data freshness check: end-to-end latency budget (Pub/Sub event → strategy signal published) within
      target (define target as P95 ≤ 30s for forward-poll, ≤ 5min for batch).
- [ ] [TEST] P0. Predictions appear in upcoming-fixtures-ui via deployment-api `/sports/predictions/upcoming` (or
      current canonical route).
- [ ] [ANALYSIS] P1. Per-league prediction-volume health check: at least N predictions per league per fixture day for
      the trained universe.

## Group I — Live pipeline activation

Goal: forward-poll path produces predictions into UI without manual VM intervention.

Folded from sports_e2e_validation Phase 5 (MTDS/MDPS/FSS/strategy live mode).

- [ ] [CODE] P1. MTDS live mode: capture odds per fixture schedule (Pub/Sub trigger). Verify against
      sports_scheduler_cron_activation.
- [ ] [CODE] P1. MDPS live mode: clean + bucket in real-time on Pub/Sub.
- [ ] [CODE] P1. FSS live mode: compute features per fixture ~60min pre-KO.
- [ ] [CODE] P2. Strategy live mode: arb detection + signal generation; emit to execution-service paper-fill queue.
- [ ] [GATE] P0. Final gate (B5): live-pipeline runs unattended for 1 fixture-day and produces predictions in UI for
      every league in the trained universe within latency budget.

## Out of scope

- **Cost-driven backfill expansion** — sports_e2e_validation Phase 4 (Tier 1 + Tier 2 = 207M Odds API credits) is
  operator/budget decision; not predictions critical-path now that coverage is reportedly at 100%. Re-open as a separate
  plan if Group D shows undercoverage gaps.
- **Live (non-paper) sports execution** — Group F caps at execution-service paper mode. Live execution gated on operator
  sign-off.
- **New ML models beyond Model 2A** — model R&D after baseline.
- **SFI parallel-backfill polish** — sfi_chunk_parallel_backfill_2026_04_22 stays a separate plan (backfill-speed scope,
  not predictions critical path).
- **Transfermarkt/SFI team-mapping cache** — shipped 2026-04-25; archived alongside this plan.

## Critical files / SSOTs

- `unified-trading-pm/codex/02-data/sports-scheduling-and-sharding.md §12` — current sports register
- `unified-trading-pm/codex/14-playbooks/sports/` — playbooks for arb-detection, ML training, strategy patterns
- `unified-api-contracts/canonical/domain/sports/` — SPORTS data-type schemas
- `feature-service-sports/feature_service_sports/calculators/` — FSS calculator implementations
- `ml-training/ml_training/configs/` — Model 2A training config
- `strategy-service/strategy_service/strategies/` — ArbitrageStrategy + MLSportsStrategy
- `execution-service/execution_service/matching_engine/` — historical fill simulator

## Verification

- After Group D: `feature-service-sports` data-status shows ≥95% non-NULL features for the trained universe over 1-week
  window.
- After Group E: ml-training Model 2A walk-forward report (committed) shows AUC ≥ 0.55 + calibration ≤ 5%.
- After Group F: strategy-service backtest report shows positive strategy-alpha + documented execution-alpha gap on
  1-week paper-trade dataset.
- After Group H: schema-parity tests in CI, end-to-end freshness check passing, deployment-ui sports widgets show
  predictions.
- After Group I: 1 fixture-day live run with no manual VM intervention; predictions in UI for every league in the
  trained universe.

## Notes for executing agents

- **Batch = Live invariant** — strategy must exercise the full service mesh in batch mode (CLAUDE.md). Do not build
  standalone backtest engines that settle inline; use execution-service "always fill" mode for strategy alpha and
  matching-engine for execution alpha.
- **No `os.getenv()` / no fallback imports** — service mesh standard.
- **All schemas in UAC** — never re-declare in service source.
- **Tarball refresh** — after any code change touching FSS / ml-training / strategy-service / execution-service, refresh
  tarballs via `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS` before next live run.
