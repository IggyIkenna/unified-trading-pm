---
name: predictions-master
slug: predictions_master_2026_05_07
date: 2026-05-07
owner: claude-code
status: active
priority: P1
phase: pending_approval
domain: prediction
asset_group: prediction
type: umbrella
locked_by: live-defi-rollout
locked_since: 2026-05-07
folds_in:
  - predictions_canonical_question_group_polymarket_migration_2026_05_06
  - sports_predictions_e2e_2026_05_05 # predictions ML half (sports half goes to sports_master)
  - market_tick_data_to_100pct_2026_05_05 # predictions slice
related_plans:
  - master_to_live_defi_2026_05_23
  - writegate_honest_coverage_endtoend_2026_05_06
---

# Predictions Master — asset_group umbrella

## Scope

Single source of truth for **prediction asset_group** work. Per master plan asset-group readiness ladder, predictions is
**features-pipeline-running (no ML this cycle)** by 2026-05-23.

Covers:

- **Canonical question group taxonomy + classifier**: Polymarket / Kalshi raw market_ids → canonical groups
  (`BTC_UP_DOWN_HOURLY` (24/day), `BTC_UP_DOWN_DAILY` (1/day), `SPX_UP_DOWN_DAILY`, `ELECTION_PRESIDENT_2028`, etc.).
  Like options-chain bundling.
- **Polymarket / Kalshi market lifecycle**: `market_created_at` / `resolution_time` / `settlement_time` per market_id.
  MTDS CLOB capture respects bounds (no ticks before created or after settled).
- **`asset_group=prediction` shard atom migration**: from legacy `category=prediction_market` / `data_type=<base_asset>`
  to canonical
  `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)`.
- **Per-market lifecycle gating in feature compute**: `LookaheadBiasError` extension — features at time T see only
  market_ids where `market_created_at ≤ T`.
- **Predictions ML half of `sports_predictions_e2e`**: ml-training Model 2A walk-forward + arb_calculator + Group E/F ML
  gates. Sports half (288M ODDS_API row migration + MDPS bucketing + FSS) lives in `sports_master`.

## Current state (2026-05-07)

- **predictions_canonical_question_group_polymarket_migration**: 14/37 = 38% done. Phase 0 audit + classifier shape
  documented; Phase 1 lifecycle ingestion writer + Phase 2 reader/feature/strategy migration NOT yet shipped.
- **UAC `PREDICTION_GROUPS`**: empty registry (`{}`) per CLAUDE.md "Temporary state"; canonical-question-group registry
  seeding pending Phase 1.
- **MTDS POLYMARKET adapter**: writes `data_type=<base_asset>` legacy shape; needs migration to
  `data_type=prediction_canonical_question_group` per CLAUDE.md "Prediction market lifecycle timing" rule.
- **288M ODDS_API legacy row migration**: scoped per `sports_predictions_e2e`; sports half tracked in `sports_master`.

## Critical path

| Workstream                                                                       | Status                          | Source                                                      |
| -------------------------------------------------------------------------------- | ------------------------------- | ----------------------------------------------------------- | ----------- | ---- |
| Canonical question group taxonomy + classifier                                   | Phase 0 audit done              | `predictions_canonical_question_group_polymarket_migration` |
| Lifecycle ingestion (created_at / resolution / settlement per market_id)         | NOT started                     | same                                                        |
| Polymarket adapter migration (data_type rename)                                  | NOT started                     | same                                                        |
| Kalshi adapter migration                                                         | NOT started                     | same                                                        |
| Reader-side migration (callsites: `data_type=BTC                                 | ETH                             | ...` → canonical_question_group)                            | NOT started | same |
| Per-market lifecycle gating in features compute (`LookaheadBiasError` extension) | NOT started                     | same                                                        |
| Strategy-service prediction archetypes — canonical_group config                  | NOT started                     | same                                                        |
| Manifest reflip + parquet migration scripts                                      | scoped                          | same                                                        |
| ML training Model 2A walk-forward (predictions half)                             | gated on sports half completion | `sports_predictions_e2e`                                    |
| arb_calculator in FSS                                                            | scoped                          | `sports_predictions_e2e`                                    |
| Predictions MTDS slice to ≥99%                                                   | partial                         | `market_tick_data_to_100pct` (predictions slice)            |

## Consolidated todos (P0 only)

### Canonical-question-group taxonomy + lifecycle ingestion

- [ ] [AUDIT] P0. Classifier stability hash design — pending; audit-3 documented existing classifier shape but hash
      design not finalized.
- [ ] [SCRIPT] P0. Lifecycle ingestion in instruments-service: capture `market_created_at`, `resolution_time`,
      `settlement_time` per conditionId / Kalshi ticker.
- [ ] [SCRIPT] P0. New writer path in `engine/orchestrator.py` for prediction with canonical_group + lifecycle.
- [ ] [SCRIPT] P0. `_extract_prediction_shard` / `_compute_prediction_shards` (orchestrator.py:2497–2524) call
      classifier; emit
      `(asset_group=prediction, venue, data_type=prediction_canonical_question_group,     canonical_question_group, market_id, day)`
      shard atom.
- [ ] [TEST] P0. instruments-service unit + integration tests for lifecycle ingestion + classifier integration.

### Adapter migration (MTDS — Polymarket + Kalshi)

- [ ] [SCRIPT] P0. Polymarket adapter (`polymarket_adapter.py:454–602`): read lifecycle from instruments-service; reject
      ticks outside `[market_created_at, settlement_time]` window per CLAUDE.md "Prediction market lifecycle timing"
      rule.
- [ ] [SCRIPT] P0. Kalshi adapter (`kalshi_adapter.py:242–269`): same migration.
- [ ] [SCRIPT] P0. `umi_tick_provider.py:225`: replace `category="prediction_market"` with `asset_group="prediction"` +
      `data_type="prediction_canonical_question_group"`.
- [ ] [SCRIPT] P0. Replace POLYMARKET writer (`orchestrator.py:1990–1995`): old `data_type = <base_asset>` → new
      `data_type = prediction_canonical_question_group`.
- [ ] [TEST] P0. MTDS unit tests: lifecycle gating (pre-created tick rejected, post-settled tick rejected); cluster
      validation per `(canonical_question_group, day)`.

### Reader / feature / strategy migration

- [ ] [SCRIPT] P0. Reader migration: every callsite with `data_type=BTC|ETH|...` →
      `data_type=prediction_canonical_question_group` + filter on `canonical_question_group`.
- [ ] [SCRIPT] P0. Per-market lifecycle gating in feature compute: `LookaheadBiasError` extension — feature at time T
      consumes only market_ids where `market_created_at ≤ T`.
- [ ] [SCRIPT] P0. Strategy-service prediction archetypes: archetype configs reference `canonical_question_group`
      directly (not base_asset).
- [ ] [TEST] P0. End-to-end smoke: 1 canonical_group (`BTC_UP_DOWN_HOURLY`) × 1 day; run feature compute + verify.

### Manifest + parquet migration

**Cross-plan coordination**: Polymarket parquet rewrite + manifest reflip is **Stage 3** of the workspace-wide manifest
migration. See [`manifest_migration_master_2026_05_07.plan.md`](./manifest_migration_master_2026_05_07.plan.md) for
sequencing DAG, VM impact, and operator gates. Key constraints: PAUSE `mtds-prediction-*` VMs during rewrite window;
resume ONLY after MTDS Polymarket adapter migration ships (so resumed VMs write `canonical_question_group` shape, not
legacy per-base_asset). Migration must run AFTER writegate Phase 2.A placeholder-method deletions complete.

- [ ] [SCRIPT] P0. New script `mtds_migrate_polymarket_per_base_asset_to_canonical_group.py` (in scripts/).
- [ ] [SCRIPT] P0. Manifest reflip script `mtds_reflip_polymarket_per_base_asset.py` per
      `unified_trading_library.run_lifecycle` pattern.
- [ ] [SCRIPT] P0. Old parquet deletion — only AFTER (a) new parquets verified by hand-inspection (sample 10 random
      groups × random days), (b) downstream features compute clean, (c) operator approval.
- [ ] [SCRIPT] P0. Backfill any missing canonical_groups — markets in `conditionid_universe.csv` that classifier maps to
      a group not yet in `PREDICTION_GROUPS` registry.
- [ ] [SCRIPT] P0. Confirm `migrate_polymarket_canonical.py` (MTDS) ran for all targets; afterwards delete legacy
      `category=prediction` fallback reader in MTDS (no compat shim per workspace rule).
- [ ] [SCRIPT] P0. Every reconciler wraps work in `unified_trading_library.run_lifecycle.run_lifecycle(...)`.
- [ ] [SCRIPT] P0. Each reconciler supports `--max-flips-per-run=10000` halt safety; operator confirms first 10k flips.
- [ ] [SCRIPT] P0. CSV audit at `gs://{pid}-reconciler-audit/{run_id}/`.

### Data-status panel — Predictions asset_group drill-down

- [ ] [SCRIPT] P0. Predictions asset_group panel — drill-down shape: `(venue, canonical_question_group, day)`.

### Predictions ML half (`sports_predictions_e2e`)

- [ ] [SCRIPT] P0. Run ml-training Model 2A walk-forward against the Group-D-validated feature matrix (gated on sports
      half completion in `sports_master`).
- [ ] [ANALYSIS] P0. Acceptance metrics — log-loss, calibration, AUC for win/draw/loss; threshold per consolidated plan
      bar.
- [ ] [SCRIPT] P0. Training-config sanity check: feature columns match FSS schema, label leakage absent, walk-forward
      window correct.
- [ ] [GATE] P0. Block Group F until walk-forward AUC ≥ 0.55 and calibration error ≤ 5%.
- [ ] [CODE] P0. Implement (or verify shipped) `arb_calculator` in FSS: cross-bookmaker arb %, eligible pairs, duration.
- [ ] [ANALYSIS] P1. Persist model + metrics to ml-models registry; tag `model_family=sports_arb_v1`.

### Predictions MTDS slice (`market_tick_data_to_100pct` — predictions)

- [ ] [AGENT] P1. Per-(canonical_question_group, day) completion %: HOURLY = 24 expected/day, DAILY = 1, ELECTION = 1
      over months/years.

### Audit findings 2026-05-07 — folded from session wrapper

**Source**: `plans/ai/session_2026_05_07_data_status_audit_findings.plan.md` row C.12. Operator inspected the
deployment-ui prediction panel + saw POLYMARKET tagged "out of scope" (badge driven by UAC
`VENUE_DATA_TYPE_CAPABILITIES` declaring `data_type=prediction_canonical_question_group` while MTDS still writes legacy
per-base-asset shape `BTC` / `ETH` / `SPX`). Per user direction 2026-05-07: NOT actually out of scope — small Polymarket
dataset means full migration is feasible in one VM run.

#### C.12 — POLYMARKET "out of scope" badge resolution + synthetic OTHER bucket

The Phase 1 critical-path todos above already cover the canonical-question-group classifier + lifecycle ingestion +
adapter migration. The two items below close the loop on the deployment-ui panel surface specifically:

- [ ] [SCRIPT] P0. **Synthetic `OTHER` canonical-question-group bucket** — the classifier MUST map every Polymarket
      `conditionId` (and Kalshi ticker) to SOME canonical group. Markets that don't fit the curated registry
      (`BTC_UP_DOWN_HOURLY`, `BTC_UP_DOWN_DAILY`, `SPX_UP_DOWN_DAILY`, `ELECTION_PRESIDENT_2028`, etc.) get mapped to
      `OTHER`. Rationale per user direction 2026-05-07: small Polymarket dataset means we can audit `OTHER` membership
      after each backfill VM run and promote frequently-seen patterns to first-class groups. Treating `OTHER` as a known
      catch-all bucket is honest absence; treating those markets as "out of scope" hides them from the panel and from
      the classifier audit loop.
  - [ ] UAC `PREDICTION_GROUPS` registry seeding (Phase 1 critical-path item) MUST include `OTHER` as a special-case
        entry from day one. Cluster validation for `OTHER` is per-day count > 0 (any markets fall through), not a target
        count.
  - [ ] Classifier emits an `INFO`-level event `OTHER_BUCKET_MEMBER_ADDED` whenever it routes a `conditionId` to
        `OTHER`. Operator periodically queries the event stream to find candidate groups for promotion.
  - [ ] Data-status panel renders `OTHER` as a normal canonical-question-group bucket (not "out of scope"). Hover
        tooltip: "Markets not yet mapped to a curated canonical question group — review event stream + promote recurring
        patterns to first-class groups."
- [ ] [VERIFY] P0. Phase 1 timeline check against 2026-05-23 master deadline: 14/37 done (38%) as of 2026-05-07. The 14
      remaining P0 items in Phase 1 + Phase 2 + Phase 3 (lifecycle ingestion + classifier + adapter migration + parquet
      rewrite + manifest reflip) need to ship in ~16 days. Per user direction: small dataset means migration is
      feasible. Block Phase 5 baseline + ratchet until POLYMARKET no longer renders "out of scope" in deployment-ui.
- [ ] [VERIFY] P0. After Phase 1 ships: re-walk deployment-ui prediction panel; POLYMARKET drill-down renders as
      `(venue=POLYMARKET, data_type=prediction_canonical_question_group, canonical_question_group, market_id, day)` per
      CLAUDE.md per-asset-group shard-key matrix. No "out of scope" badge. `OTHER` bucket visible alongside curated
      groups.

## Anti-patterns + workspace-rule cross-references

- **Prediction market lifecycle timing** (CLAUDE.md): NO ticks before `market_created_at`, NO ticks after
  `settlement_time`. MTDS adapters MUST gate on lifecycle bounds.
- **Cluster validation per `(canonical_question_group, day)`**: HOURLY → 24 clusters expected; DAILY → 1; ELECTION → 1
  over its window. Cluster gate at `record_captured` per CLAUDE.md "Cluster validation MANDATORY".
- **Temporary state**: UAC `PREDICTION_GROUPS = {}` empty registry until taxonomy seeded — CLAUDE.md "Temporary state"
  rule applies; this plan IS the named successor.

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.plan.md`](./master_to_live_defi_2026_05_23.plan.md).
- Sibling asset_group umbrellas: `cefi_master_2026_05_07`, `defi_master_2026_05_07`, `tradfi_master_2026_05_07`,
  `sports_master_2026_05_07`.
- Sports half of e2e: `sports_master_2026_05_07.plan.md` (288M ODDS_API row migration + MDPS bucketing + FSS).

## Folded plans (archived 2026-05-07)

- `predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md` — full migration spec; P0 todos lifted
  above.
- `sports_predictions_e2e_2026_05_05.plan.md` (predictions half) — ML training + arb_calculator + Group E/F gates;
  sports half went to `sports_master`.
- `market_tick_data_to_100pct_2026_05_05.plan.md` (predictions slice) — full plan archived after split per asset_group.
