---
doc_type: plan
title: Harsh's daily work-split — 2026-05-08 (15 days to live-DeFi)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    deployment-api,
    deployment-service,
    deployment-ui,
    execution-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
type: coordination-doc
deadline: 2026-05-23 (live DeFi)
horizon: 1-day cycle (rolls forward EOD)
companion_to: plans/active/work_split_2026_05_08_ikenna.md
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

## Deferred work — migrated to:

**None** — successor: not applicable. Verified 2026-07-21 (batch-5 archived-plan discipline triage): a disposable
single-day coordination snapshot (`type: coordination-doc`, `horizon: 1-day cycle`) whose own text says to archive it
EOD and draft the next day's tracker — exactly what happened (a chain of dated successors through at least 2026-05-22,
all similarly archived). Every named plan-of-record it points at (features-repo consolidation, mtds_databento streaming,
hard_schema_enforcement, api_football flattening, cme_polymarket_arb, gcs_migration) is archived complete. Nothing here
is untracked.

# Harsh's daily work-split — 2026-05-08

> **Companion**: [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md). Cross-side handshakes appear in
> both plans (mirror-image entries). The other side's plan is read-only for you.
>
> **Methodology**: see [`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) §"Daily Work-Split Process" for the
> full spec — split principle, working models, universal mechanics. This doc is today's specific load-balancing; the
> spec is the durable rules.

## Why this split exists today

- **15 days to live-DeFi cutover** (2026-05-23). Master plan
  [`master_to_live_defi_2026_05_23`](master_to_live_defi_2026_05_23.md) Group F + G are the gating ladder. Harsh-side
  absorbs the implement-from-spec / mechanical / parallel-safe / single-repo-edits / test-execution / launch-verify work
  that doesn't require cross-cutting design judgment.
- **Yesterday's Harsh orchestration ledger finished** with 12 spawned tabs ✅ DONE (Tabs 3-14): deployment-api Phase 2
  endpoints, deploy-missing Phase 1 tarball-refresh, lending-indices Bug 1+2+3 fixes (Tab 5), defi-988 audit,
  mtds-databento path-streaming Phase 1, audit_followups, lending-indices VM relaunch validation, predictions Phase 1
  ingestion, launcher consolidation 10 of 30, ml-features-phase2a (deferred per Tab 12 Q1), deploy-missing IAM proposal
  draft, defi-fork1-prep audit (13 of 17 UAC drift pairs flagged). Only Tab 2 (cefi-babysit) still IN FLIGHT — sweeps
  continuing, drain ETA tomorrow.
- **Carryover into today**: cefi VM drain monitor, cross-asset manifest rescan post-drain, TradFi MDPS post-drain
  cluster validation, sports per-source reconciler hook + features_sports_reconcile_available_at hook, defi_988 13,632
  actionable rows targeted backfill, predictions Phase 2+3 (after Tab 12 Q1 deferred), deployment-ui lifecycle tabs,
  ml/features parquet column-pruning + 8-service LookaheadBiasError wires (per resolved Tab 12 Q1 decision: absorbed
  into features_repo_consolidation), launcher consolidation remaining 20 of 30, hard_schema enforcement Phase 1-5,
  mtds_databento path-streaming Phases 2-4, mtds_per_instrument_download_api Phase 1.5,
  api_football_minimal_flattening_removal, cme_polymarket_arb, data_status_comprehensive_test_coverage.
- **Ping ledger (overnight)**: empty after rebase. `ml-features-phase2a-tab` Q1 ESCALATED-TO-OPERATOR was resolved this
  morning (operator picked option (b) — defer to features_repo_consolidation absorption). Beef-up sub-agent BLOCKED ping
  resolved via fast-forward rebase.

## May-23 epic context (read first)

The 2026-05-08 plans-restructure landed the **epic layer** at [`plans/epics/`](../epics/) above the granular masters
(per [`plans_workspace_organization_2026_05_08.md`](plans_workspace_organization_2026_05_08.md) +
[`plans/epics/README.md`](../epics/README.md)). 7 epics own the May-23 cutover targets:

| Epic                                                                                  | May-23 scope                              | Side ownership                       |
| ------------------------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------ |
| [`live_defi_rollout_may_23_2026`](../archive/live_defi_rollout_may_23_2026.epic.md)   | LIVE on real wallet — 3 carry archetypes  | Ikenna lead; Harsh implements pieces |
| [`cefi_ml_may_23_2026`](../archive/cefi_ml_may_23_2026.epic.md)                       | LIVE on real capital — continuous ML CeFi | **Joint** (Harsh Tab 2 + Ikenna)     |
| [`sp_prediction_may_23_2026`](../archive/sp_prediction_may_23_2026.epic.md)           | BATCH ML only                             | **Harsh lead** (Tab 2 + 5)           |
| [`price_arbitrage_may_23_2026`](../archive/price_arbitrage_may_23_2026.epic.md)       | BACKTEST only                             | **Harsh lead** (Tab 5)               |
| [`sports_ml_may_23_2026`](../archive/sports_ml_may_23_2026.epic.md)                   | BACKTEST only                             | **Harsh lead** (Tab 1 + 5)           |
| [`prediction_markets_may_23_2026`](../archive/prediction_markets_may_23_2026.epic.md) | BACKTEST only                             | **Harsh lead** (Tab 1 + 5)           |
| [`cross_cutting_may_23_2026`](../epics/cross_cutting_may_23_2026.epic.md)             | Workspace-wide                            | Both sides every tab                 |

Harsh-side absorbs the implement-from-spec / mechanical / parallel-safe / single-repo / test-execution work for ALL 7
epics; Ikenna-side owns the cross-cutting design + governance. The 4 BATCH/BACKTEST epics (sp_prediction +
price_arbitrage + sports_ml + prediction_markets) are predominantly Harsh-side because they need full backtest pipeline
runs + integration test matrices rather than judgment calls. Per [`plans/epics/README.md`](../epics/README.md): epics
are **read-mostly** + don't duplicate sub-plans; this split assigns sub-plan tactical work, not epic-level deliverables.

## Working model

**Model A — fixed thematic 6-tab clustering**, but with a pre-baked option to switch to Model B (1 main + dynamic
spawned tabs) mid-cycle if more items emerge from incoming pings or audit findings. Yesterday Harsh ran Model B (12
spawned tabs by EOD); today Model A is the starting shape because the carryover items cluster cleanly into 6 themes
(instruments-live + lifecycle, features-repo consolidation, deployment-UI lifecycle, per-asset_group VM ops, mechanical
refactor cluster, cross-cutting build). If Harsh prefers Model B's flexibility, treat the 6 tabs below as the day's
initial scope and spawn additional tabs as work clarifies — same universal mechanics either way.

> **CI gate reminder (workspace-wide).** Per CLAUDE.md § "CI Verification After Every Push": pushes to
> `live-defi-rollout` do **NOT** trigger remote CI. With ~6 parallel tab agents + many sub-agents pushing all day, the
> ONLY quality gate is each shippable unit's local `bash scripts/quality-gates.sh` (Pass 1) before push. There is no
> remote safety net catching platform-specific failures on this branch. Confirm push landed on origin
> (`git rev-list --left-right --count HEAD...origin/live-defi-rollout` returns `0 0`) per shippable unit.

## Coverage guarantee — 6 tabs absorb today's Harsh-side scope

| Source                                                                      | Item                                                                                                                                         | Tab |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | --- |
| `instruments_live_master_2026_05_08`                                        | Phase A-E live activation across all 5 asset_groups (Cloud Scheduler + audit jobs + UI tab integration)                                      | 1   |
| `predictions_master_2026_05_07`                                             | Phase 2 lifecycle gating MTDS Polymarket/Kalshi adapter + UMI tick provider data_type rename                                                 | 1   |
| `predictions_master_2026_05_07`                                             | Phase 3 reader / feature / strategy consumer migration to canonical_question_group                                                           | 1   |
| `instruments_and_market_tick_data_completion_2026_05_01`                    | Per-asset_group instrument lifecycle floor handling + catalog-aware writer-guard                                                             | 1   |
| `features_repo_consolidation_2026_05_08`                                    | Phase 0-3 (deadline 2026-05-13): pre-audit + scaffold consolidated repo + sub-package extraction + import-rewrite                            | 2   |
| `features_repo_consolidation_2026_05_08`                                    | Phase 4-7: per-source consumer migration + feature_family UAC column + deprecation banners + delete-source-repos commit                      | 2   |
| `ml_and_features_master_2026_05_07`                                         | Phase 2A + 2B 8-service `assert_no_lookahead_for_feature_group` wires (resolved Tab 12 Q1: absorb into features_repo_consolidation)          | 2   |
| `ml_and_features_master_2026_05_07`                                         | Phase 3 parquet column-pruning quick-win (1-3 day pure-win, self-contained)                                                                  | 2   |
| `deployment_ui_lifecycle_tabs_2026_05_08`                                   | Phase A UAC SSOT for lifecycle column + Phase B UI re-shape (4 tab refactors)                                                                | 3   |
| `deployment_ui_lifecycle_tabs_2026_05_08`                                   | Phase C cloud-toggle + Phase D auth flow + Phase E env-resolution                                                                            | 3   |
| `deploy_missing_auto_launch_2026_05_07`                                     | Phase 1 tarball-refresh follow-on + Phase 2 auto-launch endpoint (after Ikenna Tab 5 ships IAM decision)                                     | 3   |
| `cefi_master_2026_05_07`                                                    | Day-3 OPS babysit of remaining cefi VMs + drain reporting; TradFi MDPS post-drain ES.OPT 11-cluster validation                               | 4   |
| `manifest_migration_master_2026_05_07`                                      | Stage 4 cross-asset manifest rescan post-CeFi drain (mechanical operation; Ikenna Tab 3 designs the schema flip)                             | 4   |
| `sports_master_2026_05_07`                                                  | Per-source reconciler hook + features_sports_reconcile_available_at hook into per-source backfill VM exit-step                               | 4   |
| `defi_master_2026_05_07` + `issues/defi_988_missing_dates_audit_2026_05_08` | Targeted backfill of 13,632 actionable rows from Tab 6 audit (top-5 priority list)                                                           | 4   |
| `launcher_scripts_consolidation_into_deployment_service_2026_05_07`         | Migrate remaining 20 of 30 ad-hoc launchers into deployment-service/scripts/vm/                                                              | 5   |
| `data_status_comprehensive_test_coverage_2026_05_07`                        | All 30 todos: 5 test categories × 6 repos                                                                                                    | 5   |
| `mtds_databento_path_streaming_2026_05_07`                                  | Phases 2-4 (chunked streaming + memory profiler + smoke fixtures)                                                                            | 5   |
| `mtds_per_instrument_download_api_2026_04_24`                               | Phase 1.5 chain axis (audit named CRITICAL-PATH)                                                                                             | 5   |
| `hard_schema_enforcement_2026_05_08`                                        | Phases 1-5 mechanical migration scripts per asset_group                                                                                      | 5   |
| `api_football_minimal_flattening_removal_2026_05_07`                        | All 16 todos (UAC normalize.py:377-381 fix + re-fetch VM + manifest flip)                                                                    | 5   |
| `cme_polymarket_arb_2026_05_08`                                             | All 6 phases (config + CLOB / CME tick wiring + execution route + DART)                                                                      | 5   |
| `cross_cutting_may_23_deliverables_2026_05_08`                              | Strategy ID refactor sweep across execution / strategy / ml-inference / pnl-attr / batch-live-recon / PBM / alerting (consume Ikenna T6 UAC) | 6   |
| `cross_cutting_may_23_deliverables_2026_05_08`                              | Strategy catalogue rows populated from Ikenna T6 schema (full archetype × venue × instrument-type matrix)                                    | 6   |
| `cross_cutting_may_23_deliverables_2026_05_08`                              | Client-account-strategy tagging propagation through every live trade + batch backtest result                                                 | 6   |
| `cross_cutting_may_23_deliverables_2026_05_08`                              | DART manual-trade UI implementation (5 surfaces: DeFi swap/lend/stake, CeFi orders, ML training trigger, sports bet, prediction-market)      | 6   |
| `cross_cutting_may_23_deliverables_2026_05_08`                              | Strategy catalogue UI (filter by asset_group / archetype / venue / live-vs-backtest)                                                         | 6   |

**27 items / 6 tabs / 0 dropped.**

## AI-day estimate (per tab, summed across the cycle)

| Tab                        | Theme                                                                         | Items                                                                                                                              | AI-days |
| -------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------- |
| 1                          | Instruments-live + lifecycle ingestion                                        | 5 asset_group activations + Predictions Phase 2+3 + instrument-completion catalog work                                             | ~10     |
| 2                          | Features-repo consolidation + ml/features wiring                              | 8 phases features-repo + Phase 2A/B + Phase 3 column-pruning                                                                       | ~10     |
| 3                          | Deployment-UI lifecycle tabs + deploy_missing                                 | 5 phases UI + deploy_missing Phase 1 + Phase 2                                                                                     | ~10     |
| 4                          | Per-asset_group VM ops + reconcilers + targeted backfill                      | cefi drain + TradFi cluster validation + cross-asset rescan + sports reconciler + defi_988                                         | ~8      |
| 5                          | Mechanical refactors + audit cluster (the dragon)                             | 6 plans: launcher consolidation + data-status tests + databento + per-instrument + hard_schema + api_football + cme_polymarket     | ~12     |
| 6                          | Cross-cutting build (catalogue rows + ID refactor + client tagging + DART UI) | Consume Ikenna T6 UAC SSOTs; ID refactor sweep + catalogue row population + client tagging + 5 DART manual surfaces + catalogue UI | ~12     |
| **Total Harsh-side cycle** |                                                                               | **~62**                                                                                                                            |

6 parallel agents × ~10 days solo = ~62 ai-days. Above the CLAUDE.md "25-50 AI-days per side" target but within "err on
beefier scope" guidance — Tab 6 was added 2026-05-08 mid-cycle to close the cross_cutting epic gap (deliverables #1-#4
not assigned to Tabs 1-5 per the audit). Tab 6 is gated on Ikenna T6 UAC SSOT ships; mechanical scaffolding (refactor
callsite identification) can run in parallel.

---

## TAB 1 — Instruments-live + lifecycle ingestion

**Identity**: you own the May-23 instruments-live activation thread. 5 asset_groups need lifecycle ingestion +
catalog-aware capture. Per CLAUDE.md "Prediction market lifecycle timing" rule, predictions specifically requires
per-market_id lifecycle timestamps (`market_created_at`, `resolution_time`, `settlement_time`). High-leverage tab
because Phase 1 ingestion shipped 2026-05-07 (instruments-service@98bb167, MTDS@b904785) but Phase 2+3 (adapter
migration + reader/feature/strategy consumers) was deferred.

**Plan-of-record**: [`instruments_live_master_2026_05_08.md`](../epics/instruments_live_master_2026_05_08.md)

- [`predictions_master_2026_05_07.md`](../epics/predictions_master_2026_05_07.md) Phase 2+3 +
  [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) Phase 3.D.5
  Wave 3 (catalog-aware writer-guard; archived parent
  [`instruments_and_market_tick_data_completion_2026_05_01.md`](../archive/instruments_and_market_tick_data_completion_2026_05_01.md)).

**Scope (4 items, P0-P1)**:

- [ ] [SCRIPT] P0. **`instruments_live_master` Phase A-E** — 5 asset_group live activations: Phase A (cefi Cloud
      Scheduler + audit job + UI tab); Phase B (defi); Phase C (tradfi); Phase D (sports); Phase E (predictions). Each
      phase: Cloud Scheduler cron config + audit job that reconciles per-asset_group catalog vs manifest at midnight +
      deployment-UI tab integration to surface live status. ~5 AI-days (1 per phase).
- [ ] [SCRIPT] P0. **Predictions Phase 2 — MTDS Polymarket/Kalshi lifecycle gating + UMI tick provider data_type
      rename** — per [`predictions_master_2026_05_07.md`](../epics/predictions_master_2026_05_07.md) Phase 2 deferred
      from Tab 10 yesterday. Per CLAUDE.md "Prediction market lifecycle timing": MTDS CLOB capture must respect
      lifecycle bounds (NO ticks before `market_created_at`, NO new ticks after `settlement_time`). Rename
      `umi_tick_provider.py:225` + `orchestrator.py:1990-1995` `data_type` → `prediction_canonical_question_group`.
      Per-market_id manifest rows + cluster-coverage gate. ~2 AI-days.
- [ ] [SCRIPT] P0. **Predictions Phase 3 — reader/feature/strategy consumer migration** — every reader of Polymarket /
      Kalshi data migrates to the new shard atom keyed on
      `(asset_group=prediction, venue, data_type,     canonical_question_group, day)`. Features-prediction +
      strategy-service archetype consumers wired. ~2 AI-days.
- [ ] [SCRIPT] P1. **`instruments_and_market_tick_data_completion` per-asset_group catalog-aware writer-guard** —
      writegate Phase 3.D.5 Wave 3 deferred from 2026-05-07. Adds `instrument_catalog` reference at MTDS adapter
      construction so blank-zero-source-response gets routed to (D) zero-activity bars when the catalog says alive AND
      market hours. ~1 AI-day.

**Repos owned (collision boundary)**: instruments-service (full ownership for catalog + lifecycle ingestion; no
overlap), MTDS (Polymarket + Kalshi adapters + UMI tick provider; collides with Ikenna Tab 1 only on different files —
Ikenna touches DeFi adapters), deployment-ui (instruments-live tab integration; collides with Tab 3 here on UI re-shape
— see cross-tab handshake), Cloud Scheduler config files in deployment-service.

**Read-first**:

- CLAUDE.md sections: "Prediction market lifecycle timing", "Per-asset-group shard-key matrix", "Honest absence vs fake
  placeholders", "Four-category empty-output decision", "Cluster validation MANDATORY at record_captured"
- [`plans/epics/instruments_live_master_2026_05_08.md`](../epics/instruments_live_master_2026_05_08.md)
- [`plans/epics/predictions_master_2026_05_07.md`](../epics/predictions_master_2026_05_07.md) Phase 2+3
- [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md)
  Phase 3.D.5 Wave 3 (catalog-aware writer-guard work; archived parent
  [`instruments_and_market_tick_data_completion_2026_05_01.md`](../archive/instruments_and_market_tick_data_completion_2026_05_01.md))
- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
- [`/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`](/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md)

**Sub-agent fan-out**:

- Phase A-E: 5 parallel sub-agents (one per asset_group). Each independent. Send all 5 in ONE message.
- Predictions Phase 2: 3 parallel sub-agents — (a) Polymarket adapter lifecycle gating; (b) Kalshi adapter lifecycle
  gating; (c) UMI tick provider rename + manifest writer change.
- Predictions Phase 3: 3 parallel sub-agents per consumer (features-prediction calculator + strategy-service archetype +
  reader fallback).

**Sub-agent isolation table** (paste rows verbatim into each Task prompt's "files OFF-LIMITS" section):

| Sub-agent ID      | Files owned (only edit these)                                                                                                                                 | Files OFF-LIMITS                                                                                                                                                                                |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| sa1.PhaseA-cefi   | `deployment-service/scripts/cloud-scheduler/cefi_audit_job.py` + `cloud-scheduler-cefi.yaml`; deployment-ui cefi tab content fragment                         | All other asset_group audit jobs / scheduler configs / UI tab fragments                                                                                                                         |
| sa1.PhaseB-defi   | `deployment-service/scripts/cloud-scheduler/defi_audit_job.py` + `cloud-scheduler-defi.yaml`; deployment-ui defi tab content fragment                         | All other asset_group audit jobs / scheduler configs / UI tab fragments                                                                                                                         |
| sa1.PhaseC-tradfi | `deployment-service/scripts/cloud-scheduler/tradfi_audit_job.py` + `cloud-scheduler-tradfi.yaml`; deployment-ui tradfi tab content fragment                   | All other asset_group audit jobs / scheduler configs / UI tab fragments                                                                                                                         |
| sa1.PhaseD-sports | `deployment-service/scripts/cloud-scheduler/sports_audit_job.py` + `cloud-scheduler-sports.yaml`; deployment-ui sports tab content fragment                   | All other asset_group audit jobs / scheduler configs / UI tab fragments                                                                                                                         |
| sa1.PhaseE-pred   | `deployment-service/scripts/cloud-scheduler/prediction_audit_job.py` + `cloud-scheduler-prediction.yaml`; deployment-ui prediction tab content fragment       | All other asset_group audit jobs / scheduler configs / UI tab fragments                                                                                                                         |
| sa1.PredP2-poly   | `market-tick-data-service/market_tick_data_service/adapters/polymarket_*.py` + lifecycle gating tests                                                         | Kalshi adapter, UMI tick provider, MDPS readers                                                                                                                                                 |
| sa1.PredP2-kalshi | `market-tick-data-service/market_tick_data_service/adapters/kalshi_*.py` + lifecycle gating tests                                                             | Polymarket adapter, UMI tick provider, MDPS readers                                                                                                                                             |
| sa1.PredP2-umi    | `market-tick-data-service/market_tick_data_service/adapters/umi_tick_provider.py:225` + `orchestrator.py:1990-1995` rename; manifest writer row_key migration | Polymarket / Kalshi adapter bodies                                                                                                                                                              |
| sa1.PredP3-feat   | `features-onchain-service` prediction calculator + tests                                                                                                      | strategy-service archetype consumers, MDPS reader fallback                                                                                                                                      |
| sa1.PredP3-strat  | strategy-service prediction archetype consumers + tests                                                                                                       | features-onchain calculator, MDPS reader fallback                                                                                                                                               |
| sa1.PredP3-read   | MDPS reader fallback for prediction shard atom + tests                                                                                                        | features calculator, strategy archetype consumers                                                                                                                                               |
| sa1.WriterGuard   | `market-tick-data-service/market_tick_data_service/adapters/base_adapter.py` catalog-aware route (writer-guard hook only); per-adapter wire-in tests          | MDPS `base_adapter.py` (Ikenna T2 + Harsh T2 own different layers there); features-\* repos (Harsh T2 features-consolidation owns); UAC `chain_env.py` `PROTOCOL_LAUNCH_DATES` (Ikenna T1 owns) |

**Collision risk**:

- MTDS adapters: Ikenna Tab 1 owns DeFi adapters (lending-indices, vault-share-price, lst-rates). You own Polymarket +
  Kalshi. Different files. Pre-commit `git diff --cached --name-only` verifies.
- deployment-ui: Tab 3 here owns the UI re-shape (lifecycle-tabs); you own the instruments-live tab content. **Hard sync
  gate**: Tab 3 lands the lifecycle-tabs UAC SSOT first; you wire instruments-live content on top.

**Done definition**:

1. ✅ Phase A-E shipped: 5 asset_groups have Cloud Scheduler audit jobs running + UI tab surfaces alive.
2. ✅ Predictions Phase 2 + Phase 3 shipped: lifecycle gating active in MTDS, every reader/feature/strategy consumer
   migrated to canonical_question_group axis.
3. ✅ Catalog-aware writer-guard active in MTDS adapter base class; blank-zero-source response correctly routed to (D)
   zero-activity bars when catalog says alive.

---

## TAB 2 — Features-repo consolidation + ml/features wiring

**Identity**: you own the 8 repos → 1 features-service consolidation. Deadline 2026-05-13 (5 days). Pre-req for Ikenna
Tab 2's live-pipeline Phase 4-7 wiring. Tab 12 yesterday's deferred Phase 2A wires absorb into Phase 4-7 of THIS plan
per resolved Tab 12 Q1.

**Plan-of-record**: [`features_repo_consolidation_2026_05_08.md`](features_repo_consolidation_2026_05_08.md)

- [`ml_and_features_master_2026_05_07.md`](../epics/ml_and_features_master_2026_05_07.md) Phase 2A/2B + Phase 3.

**Scope (4 items, P0)**:

- [ ] [SCRIPT] P0. **Features-repo consolidation Phases 0-3** — Phase 0 pre-audit (every consumer of every features-\*
      repo enumerated); Phase 1 scaffold consolidated repo `features-service` with sub-package layout; Phase 2
      sub-package extraction (features-onchain → features_service.onchain etc.); Phase 3 import-rewrite sweep across 8
      source repos + every downstream consumer. ~3 AI-days.
- [ ] [SCRIPT] P0. **Features-repo consolidation Phases 4-7** — Phase 4 per-source consumer migration; Phase 5
      `feature_family` UAC column add (replaces N feature_groups with 1 column + value); Phase 6 deprecation banners +
      delete-source-repos commit (8 repos archived); Phase 7 codex SSOT updates per Post-Plan-Phase Codex Audit HARD
      RULE. ~3 AI-days.
- [ ] [SCRIPT] P0. **ml_and_features_master Phase 2A + 2B 8-service `assert_no_lookahead_for_feature_group` wires** —
      absorbs Tab 12 yesterday's deferred work. Wire UTL helper into 8 services at compute entry; strict-mode raise;
      per-service unit test asserting raise on stale input. Lands as sub-step of Phase 4 per resolved Tab 12 Q1
      (operator picked option (b) — defer-into-consolidation). ~2 AI-days.
- [ ] [SCRIPT] P0. **ml_and_features_master Phase 3 parquet column-pruning quick-win** — self-contained 1-3 day pure-win
      for ml-training-service. Memory + speed win on training reads. ~2 AI-days.
- [ ] [LIVE-ML+SCRIPT] P0. **CeFi ML live-pipeline integration test + ML serving plumbing** — per
      [`cefi_ml_may_23_2026.epic.md`](../archive/cefi_ml_may_23_2026.epic.md). Joint with Ikenna Tab 2 design
      (model_registry SSOT + hot-reload pattern). Harsh-side ships: (a) features-service ML inference handler consuming
      the registry; (b) end-to-end integration test (live tick → live feature → live model inference → live strategy
      decision → live execution → fill → P&L attribution) for one continuous-ML archetype across OKX + Binance + Bybit;
      (c) live + batch backtest fidelity proof (2-year config grid → live config baseline per epic success criterion);
      (d) per-trade model_version + model_artefact_uri tagging in execution events. ~4 AI-days.
- [ ] [LIVE-ML+SCRIPT] P0. **sp_prediction full backtest pipeline run** — per
      [`sp_prediction_may_23_2026.epic.md`](../archive/sp_prediction_may_23_2026.epic.md). 2-year batch backtest of CME
      S&P swing high/low ML model (SP + BTC + calendar features). Pre-req: Tab 4 TradFi MDPS post-drain validation
      green. Output: full backtest report with P&L attribution per archetype + per-feature SHAP attribution. ~2 AI-days.

**Repos owned (collision boundary)**: features-onchain-service + features-sports-service + 6 other features-\* repos
(all source repos for the consolidation; Tab 5 owns mechanical sweeps elsewhere — different repos), new
`features-service` repo (target of consolidation), MDPS `base_adapter.py` if features-cefi/tradfi compute lives there
(collides with Ikenna Tab 2 live-pipeline wiring — different layers; pre-commit name-only verifies), ml-training-service
(Phase 3 column-pruning).

**Read-first**:

- CLAUDE.md sections: "ARCHITECTURE 2026-05-08 — Live pipeline" (features consolidation is the 3-5 day pre-req per the
  architecture decision), "Plans must capture full codebase impact upfront", "Post-Plan-Phase Codex Audit HARD RULE",
  "Shard-granularity SSOT" ([UAC] vs [UTL] vs [per-service] layer discipline)
- [`plans/active/features_repo_consolidation_2026_05_08.md`](features_repo_consolidation_2026_05_08.md)
- [`plans/epics/ml_and_features_master_2026_05_07.md`](../epics/ml_and_features_master_2026_05_07.md) Phase 2A
  - 2B + 3
- [`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md`](live_pipeline_mtds_mdps_features_2026_05_08.md)
  (Ikenna Tab 2's plan — read for Phase 4-7 dependency surface)

**Sub-agent fan-out**:

- Phases 0-3: 4 parallel sub-agents — (a) Phase 0 pre-audit (every import enumeration); (b) Phase 1 scaffold; (c) Phase
  2 sub-package extraction; (d) Phase 3 import-rewrite. Master integrates between phases.
- Phases 4-7: 5 parallel sub-agents per source repo migration + 1 codex SSOT updater + 1 deprecation-banner sweeper.
- Phase 2A/2B 8-service wires: 8 parallel sub-agents (one per service). Send all 8 in ONE message.
- Phase 3 column-pruning: 1 sub-agent profiles current parquet read, identifies droppable columns, applies pruning.

**Phase ordering (HARD SEQUENCE)**: Phase 0 (audit, read-only) → Phase 1 (scaffold target repo) → Phase 2 (extract
sub-packages, no consumer changes yet) → Phase 3 (import-rewrite sweep across consumers) → Phase 4 (per-source consumer
migration) → Phase 5 (`feature_family` UAC column add) → Phase 6 (deprecation banners + delete-source-repos) → Phase 7
(codex SSOT updates). Phase 4-7 sub-agents do NOT spawn until Phase 1-3 land. Phase 2A/2B 8-service wires fan out IN
PARALLEL with Phase 4-7 (independent surface) but only AFTER Phase 3 import-rewrite completes (8 services need the new
import paths to compile). Phase 3 column-pruning is independent and can fan out from day-1.

**Sub-agent isolation table** (paste rows verbatim into each Task prompt's "files OFF-LIMITS" section):

| Sub-agent ID           | Files owned (only edit these)                                                                                                      | Files OFF-LIMITS                                                                                                              |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| sa2.P0-audit           | Phase 0 audit body in `features_repo_consolidation_2026_05_08.md` only (no code edits)                                             | All code surfaces (Phase 0 is read-only)                                                                                      |
| sa2.P1-scaffold        | NEW `features-service/` repo skeleton (`pyproject.toml`, `src/features_service/__init__.py`, `tests/`)                             | All 8 source features-\* repos; consumer repos                                                                                |
| sa2.P2-extract-onchain | `features-onchain-service/*` → `features-service/src/features_service/onchain/*` move + tests                                      | Other 7 source features-\* repos; consumer repos                                                                              |
| sa2.P2-extract-sports  | `features-sports-service/*` → `features-service/src/features_service/sports/*` move + tests                                        | Other 7 source features-\* repos; consumer repos                                                                              |
| sa2.P2-extract-vol     | `features-volatility-service/*` → `features-service/src/features_service/volatility/*` move + tests                                | Other 7 source features-\* repos; consumer repos                                                                              |
| sa2.P2-extract-cross   | `features-cross-instrument-service/*` → `features-service/src/features_service/cross_instrument/*` move + tests                    | Other 7 source features-\* repos; consumer repos                                                                              |
| sa2.P2-extract-other   | Remaining 4 features-\* source repos (commodity, calendar, delta-one, multi-timeframe) → `features-service/*` move + tests         | The 4 already-extracted source repos; consumer repos                                                                          |
| sa2.P3-rewrite         | Import-rewrite sweep across ~20 downstream consumer repos (mechanical `from features_X import` → `from features_service.X import`) | features-service/ source dirs; UAC; UTL                                                                                       |
| sa2.P4-perSource×N     | Per-source consumer migration (one sub-agent per source) — touches ONLY its source's calculator-call sites                         | Other sources' migration sites; new repo source                                                                               |
| sa2.P5-uac-col         | UAC `feature_family` column add: `unified_api_contracts/canonical/feature/family.py` + tests                                       | Other UAC dirs (Ikenna T1 PROTOCOL_LAUNCH_DATES, Ikenna T6 strategy/, client/; Harsh T5 mechanical adds — all separate files) |
| sa2.P6-deprec          | Deprecation banners on 8 source repos' `README.md` + final commit citing migration sha                                             | features-service/ source; consumer repos                                                                                      |
| sa2.P7-codex           | `/codex/04-architecture/features-service-consolidation.md` (NEW); update 5 existing codex docs per Post-Plan-Phase Audit           | Plan body; code repos                                                                                                         |
| sa2.PhaseAB×8          | Each of 8 services' compute-entry adds `assert_no_lookahead_for_feature_group` — ONE sub-agent per service                         | Other 7 services; UTL helper itself (already shipped); MDPS `base_adapter.py` live-pipeline layer (Ikenna T2)                 |
| sa2.ColPrune           | `ml-training-service` parquet-read profiler + column-pruning patch + memory measurement                                            | features-service repos; UAC; UTL                                                                                              |
| sa2.MLLive             | `features-service/src/features_service/ml_inference/handler.py` + integration test wiring (joint with Ikenna T2 design)            | Strategy-service archetype consumers; execution-service; alerting-service                                                     |
| sa2.spP-bt             | sp_prediction backtest pipeline runner script + report output dir                                                                  | Strategy-service archetype source; UAC; features-service                                                                      |

**Collision risk**:

- MDPS `base_adapter.py`: Ikenna Tab 2 wires live-pipeline; you wire ml-features-phase2a-style lookahead-bias check.
  Different layers, methods. Per-commit pre-commit check + `git add -p` for any shared file.
- 8 features-\* source repos: yours; no other tab touches.
- New `features-service` repo: yours; new repo, no collision.

**Done definition**:

1. ✅ `features-service` repo scaffolded + 8 source repos' content migrated as sub-packages + import-rewrite swept
   across every consumer.
2. ✅ All 8 services compute calls wired with `assert_no_lookahead_for_feature_group` strict-mode + unit tests.
3. ✅ Column-pruning quick-win shipped + ml-training memory profile shows expected reduction.
4. ✅ 8 source repos archived with deprecation banner + final commit citing the migration sha.

---

## TAB 3 — Deployment-UI lifecycle tabs + deploy_missing

**Identity**: you own the deployment-UI re-shape thread. Auth + cloud-toggle + env-resolution + 4 lifecycle tab
refactors. Pre-req for Ikenna Tab 5 audit-log integration (auth re-shape ships first; audit-log wraps it).

**Plan-of-record**: [`deployment_ui_lifecycle_tabs_2026_05_08.md`](deployment_ui_lifecycle_tabs_2026_05_08.md)

- [`deploy_missing_auto_launch_2026_05_07.md`](deploy_missing_auto_launch_2026_05_07.md) Phase 1+2.

**Scope (3 items, P0)**:

- [ ] [SCRIPT] P0. **Deployment-UI lifecycle tabs Phases A+B** — Phase A UAC SSOT for lifecycle column (per the plan
      body's UAC schema design); Phase B UI re-shape (4 tab refactors: data-status, deployment-flow, operator-actions,
      alerts). ~3 AI-days.
- [ ] [SCRIPT] P0. **Deployment-UI lifecycle tabs Phases C+D+E** — Phase C cloud-toggle (UI reads `CLOUD_PROVIDER` env +
      per-cloud bucket lookups); Phase D auth flow (Firebase emulator → Cloud Run production parity); Phase E
      env-resolution (UI dev tier 0/1/2 startup script alignment per CLAUDE.md "Local Development"). ~3 AI-days.
- [ ] [SCRIPT] P0. **Deploy_missing Phase 1 + Phase 2** — Phase 1 = tarball-refresh follow-on (Tab 4 yesterday shipped
      the foundation at deployment-service@a620e1f + deployment-api@faac20a). Phase 2 = auto-launch endpoint that wraps
      `_TASK_TO_LAUNCHER` + `subprocess.run` flow, **gated on Ikenna Tab 5's IAM operator decision shipping first**.
      Phase 3+ = post-cutover. ~4 AI-days.

**Repos owned (collision boundary)**: deployment-ui (full ownership), deployment-api `auth_middleware.py` + new launch
endpoint (collides with Ikenna Tab 5 audit-log integration — sequence: auth re-shape ships first),
unified-config-interface (env-resolution), Firebase config files. **Hands off** instruments-live tab content to Tab 1.

**Read-first**:

- CLAUDE.md sections: "Local Development" (full body for tier 0/1/2 + Firebase emulator + dev-start / dev-tiers
  scripts), "Workflow Templates", "Deploy_missing UI" (in DeFi Execution Architecture context)
- [`plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md`](deployment_ui_lifecycle_tabs_2026_05_08.md)
- [`plans/active/deploy_missing_auto_launch_2026_05_07.md`](deploy_missing_auto_launch_2026_05_07.md)
- [`/codex/14-customer-journeys/authentication/firebase-local.md`](/codex/14-customer-journeys/authentication/firebase-local.md)
- [`/codex/05-infrastructure/runtime-tiers-and-deployment.md`](/codex/05-infrastructure/runtime-tiers-and-deployment.md)

**Sub-agent fan-out**:

- Phase A+B: 5 parallel sub-agents — (a) UAC SSOT lifecycle column; (b) data-status tab refactor; (c) deployment-flow
  tab refactor; (d) operator-actions tab refactor; (e) alerts tab refactor.
- Phase C+D+E: 3 parallel sub-agents (one per phase). Cloud-toggle + auth + env-resolution are independent.
- Deploy_missing Phase 2: blocked until Ikenna Tab 5 ships IAM. While blocked, prep test scaffold + integration test
  fixtures + auto-launch endpoint draft (no IAM-decision-dependent code yet).

**Collision risk**:

- deployment-ui: yours alone. Tab 1 only adds an instruments-live tab content fragment AFTER your Phase A+B.
- deployment-api `auth_middleware.py`: Tab 5 here owns deploy_missing route definitions. Ikenna Tab 5 owns audit-log
  integration. Sequence enforced by cross-side handshake: you ship auth re-shape, Ikenna wraps with audit-log.
- Firebase config: yours.

**Done definition**:

1. ✅ Phases A-E shipped + every UI tab refactored + cloud-toggle works + auth flow Firebase-emulator-to-prod parity
   verified.
2. ✅ Deploy_missing Phase 1 follow-on shipped + Phase 2 auto-launch endpoint shipped (post-IAM decision).
3. ✅ Plan flips per shippable unit + codex updates per Post-Plan-Phase Codex Audit HARD RULE.

---

## TAB 4 — Per-asset_group VM ops + reconcilers + targeted backfill

**Identity**: you own the day-2/3 OPS thread. Cefi VM drain monitoring + post-drain reconcilers across all 5
asset_groups + targeted defi_988 backfill. Mechanical run-script-and-verify work.

**Plan-of-record**: [`cefi_master_2026_05_07.md`](../epics/cefi_master_2026_05_07.md) (cefi drain) +
[`tradfi_master_2026_05_07.md`](../epics/tradfi_master_2026_05_07.md) (TradFi MDPS post-drain) +
[`manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md) Stage 4 (rescan)

- [`sports_master_2026_05_07.md`](../epics/sports_master_2026_05_07.md) (per-source reconciler hook) +
  [`../archive/issues/defi_988_missing_dates_audit_2026_05_08.md`](../archive/issues/defi_988_missing_dates_audit_2026_05_08.md).

**Scope (4 items, P0-P1)**:

- [ ] [OPS] P0. **CeFi VM drain final monitoring + sweep** — Tab 2 (cefi-babysit) yesterday continued, ETA today EOD.
      Per CLAUDE.md "No fire-and-forget VM launches": event-progression checks (`STARTED` → `PROCESSING` → `STOPPED`),
      sample-checked spot-shard via per-VM manifest at T+30min after each VM hits STOPPED. Drain report to operator +
      Ikenna Tab 5 (master plan refresh) before EOD. ~1 AI-day.
- [ ] [SCRIPT] P0. **TradFi MDPS post-drain ES.OPT 11-cluster validation rerun** — 5 mdps-tradfi-2021/22/23/24/25 VMs
      running per [`tradfi_master`](../epics/tradfi_master_2026_05_07.md). After drain, rerun cluster-coverage gate on
      TradFi MDPS shards; flag any partial bundles via the existing `MissingClusterValidationError` guard; fix in place
      if any flag. ~1 AI-day.
- [ ] [SCRIPT] P0. **Cross-asset manifest rescan post-CeFi drain (Stage 4 of manifest_migration_master)** — Ownership
      split (codified 2026-05-08 audit): **Ikenna T3 sa3.Rescan-launcher writes the rescan launcher script** (in
      `instruments-service/scripts/` or `deployment-service/scripts/vm/`); **Harsh T4 operates it** on a same-region GCE
      VM. Sequence: (1) Ikenna T3 ships launcher + announces RESOLVED in
      [`manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md)
      `## Open     questions`; (2) Tab 4 here pulls + runs `--dry-run` per asset_group
      (`reconcile_phantom_manifest_rows_all.py --asset-group {cefi|defi|tradfi|prediction|sports} --dry-run` per
      CLAUDE.md "Manifest phantom audit"); (3) operator reviews CSV; (4) Tab 4 runs `--apply-write`; (5) Ikenna T3
      handles edge cases / triage file. Banner-add to 5+ active plans on launch + banner-remove on completion. ~1.5
      AI-days.
- [ ] [SCRIPT] P1. **Sports per-source reconciler hook + features_sports_reconcile_available_at hook into per-source
      backfill VM exit-step** — sports_master Tab 3B Phase per
      [`sports_master_2026_05_07.md`](../epics/sports_master_2026_05_07.md). Hook fires after each per-source backfill
      VM completes; flips manifest captured → attempted_failed[error="MISSING_AVAILABLE_AT"] on parquets with absent or
      100% null available_at column. ~1 AI-day.
- [ ] [SCRIPT] P0. **defi_988 13,632 actionable rows targeted backfill** — Tab 6 yesterday's audit (PM@fc52188 →
      [`../archive/issues/defi_988_missing_dates_audit_2026_05_08.md`](../archive/issues/defi_988_missing_dates_audit_2026_05_08.md))
      identified the top-5 priority list. Launch targeted backfill VMs per (chain, protocol, data_type) tuple. Per
      CLAUDE.md "Singleton-locked launchers" + "VM Naming Convention" + "No fire-and-forget VM launches". Use
      rescan-aware skip per CLAUDE.md "Manifest concurrency principle" so concurrent VMs don't re-do work. ~2 AI-days.

**Repos owned (collision boundary)**: deployment-service `scripts/vm/` (you LAUNCH; Tab 5 here MIGRATES launchers —
different files, different ops); instruments-service `scripts/reconcile_phantom_manifest_rows_all.py` (you run; Ikenna
Tab 3 designs the rescan flip schema), per-VM manifest shards on GCS (you read), features-sports-service
`scripts/features_sports_reconcile_available_at.py` (you wire-into-VM-exit-step). **Hands off** lending-indices adapter
code edits to Ikenna Tab 1.

**Read-first**:

- CLAUDE.md sections: "VM tarball deployment", "VM Naming Convention", "Singleton-locked launchers", "No fire-and-forget
  VM launches", "Manifest concurrency principle", "Manifest phantom audit", "Per-VM shard isolation"
- [`plans/epics/cefi_master_2026_05_07.md`](../epics/cefi_master_2026_05_07.md)
- [`plans/epics/tradfi_master_2026_05_07.md`](../epics/tradfi_master_2026_05_07.md)
- [`plans/epics/manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md) Stage 4
- [`plans/epics/sports_master_2026_05_07.md`](../epics/sports_master_2026_05_07.md) Tab 3B
- [`plans/archive/issues/defi_988_missing_dates_audit_2026_05_08.md`](../archive/issues/defi_988_missing_dates_audit_2026_05_08.md)

**Sub-agent fan-out**:

- CeFi drain monitoring: 1 monitoring sub-agent tails events bucket + flags stalls every 10-15 min. Master reports to
  operator at EOD + Tab 5.
- Cross-asset rescan: 5 parallel sub-agents (one per asset_group). Each runs scan-only + reports CSV; master decides
  apply-write per asset_group based on operator review.
- defi_988 backfill: per top-5 priority list, 5 parallel sub-agents launching VMs (each launches its own VM with proper
  VM_NAME prefix + watchdog-registered prefix + per-VM-shard isolation).

**Collision risk**:

- deployment-service `scripts/vm/`: Tab 5 here MIGRATES launcher files (creates new files in `scripts/vm/`, adds
  prefixes to `VM_PREFIX_TO_BUCKET`). You only RUN existing launchers. Coordinate via cross-tab handshake: Tab 5 ships
  any new prefix BEFORE you launch a VM with that prefix.
- per-VM manifest shards: yours alone for the rescan; Ikenna Tab 3's expected_universe v2 also writes shards but to
  different row_keys.

**Done definition**:

1. ✅ All cefi VMs drained + report to operator with per-VM manifest spot-check sample.
2. ✅ TradFi MDPS post-drain cluster-coverage validation green or partial-bundle fixes shipped.
3. ✅ Cross-asset rescan: per-VM shards from all 5 asset_groups merged into canonical manifest; triage file populated
   for any disagreements (Ikenna Tab 3 handles).
4. ✅ Sports reconciler hook wired into VM exit-step + first per-source VM cycle through validates the wire.
5. ✅ defi_988 top-5 priority backfill VMs launched + STARTED + per-VM progress events flowing.

**Full-execution criterion** (per PLAN_FORMAT.md § 8 + "Plans Run To Actual Completion" HARD RULE):

- ✅ **CeFi VM drain ran-to-completion on real infra**.
  - **What ran**: `gcloud compute instances list --filter='name~cefi-' --zones=asia-northeast1-c` shows zero RUNNING
    cefi-{venue}-{flavor}-{ts} VMs at end-of-cycle; per-VM event stream emits STOPPED with non-empty progress.
  - **Verification**: `gcloud storage ls gs://${PID}-events/events/mtds/$(date +%Y-%m-%d)/cefi-*/` shows STARTED +
    INSTRUMENT_PROCESSED progress + STOPPED for each drained VM. Sample 3 random VMs: open the latest JSONL, assert
    `event in ("STOPPED","FAILED")` with non-empty `metadata.details`.
- ✅ **TradFi MDPS cluster validation ran on real production manifest**.
  - **What ran**: post-drain
    `python -m market_data_processing_service.scripts.run_cluster_validation --asset-group tradfi --start 2024-01-01 --end 2025-12-31`
    against `gs://central-element-323112-availability-manifest/`.
  - **Verification**: report shows zero `MissingClusterValidationError` violations across ES.OPT 11-cluster + futures
    chains; partial-bundle fixes (if any) shipped via separate commit referenced in the report.
- ✅ **Cross-asset rescan `--apply-flips` ran against canonical manifest**.
  - **What ran**:
    `python -m market_data_processing_service.scripts.rescan_cross_asset --apply-flips --csv-out /tmp/rescan_2026_05_08.csv`
    after operator dry-run review.
  - **Verification**: post-rescan `_index/availability_index.parquet` row count matches pre-rescan + flip count; sample
    probe of 5 random row_keys confirms typed reasons (no blanks); CSV diff archived.
- ✅ **defi_988 top-5 backfill VMs ran-to-completion on real infra (or partial coverage with named successor for the
  rest)**.
  - **What ran**: `bash deployment-service/scripts/vm/launch-defi-{venue}-{flavor}-vm.sh` × 5, monitored via event
    stream until each emits STOPPED with `rows_captured > 0`.
  - **Verification**: per-VM events directory contains STARTED + at least N progress events / hour + STOPPED; sample
    probe of one parquet per VM confirms non-empty rows + correct schema.

**Handoff exception(s)**:

- Sports reconciler hook validation: **DEFERRED-WITH-NAMED-VERIFICATION-RECIPE 2026-05-09**. Audit confirmed the
  reconciler script exists (`features-sports-service/scripts/features_sports_reconcile_available_at.py`) but is NOT YET
  wired into any VM launcher — none of the sports launchers under
  `deployment-service/scripts/vm/launch-{features-sports,sfi,footystats,sports-*}-*.sh` invoke it as exit-step.
  **Successor scope**: extend a sports VM launcher's `BACKFILL_CMD` (or extend `setup-data-pipeline-vm.sh` post-backfill
  branch) to invoke the reconciler before VM auto-shutdown. Verification recipe per
  `features_sports_reconcile_available_at.py` docstring: scan-only first (CSV report to `$TMPDIR`), then operator
  reviews + lifts `--apply-flips` cap. Tracked as a follow-up; either folded into a new `sports_master_2026_05_07` Phase
  5 todo OR a new `sports_reconciler_hook_wiring_<date>.md` plan filed as named successor before next sports VM cycle.

---

## TAB 5 — Mechanical refactors + audit cluster (the dragon)

**Identity**: you own 6 plans of mechanical / parallel-safe / scoped refactor work. Tab 5 is the heaviest tab by plan
count but the cleanest by collision risk (each plan touches a different surface). Ideal for fan-out across 6
sub-agents + master integration.

**Plans-of-record**:
[`launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`](launcher_scripts_consolidation_into_deployment_service_2026_05_07.md)

- [`data_status_comprehensive_test_coverage_2026_05_07.md`](data_status_comprehensive_test_coverage_2026_05_07.md)
- [`mtds_databento_path_streaming_2026_05_07.md`](mtds_databento_path_streaming_2026_05_07.md)
- [`mtds_per_instrument_download_api_2026_04_24.md`](mtds_per_instrument_download_api_2026_04_24.md)
- [`hard_schema_enforcement_2026_05_08.md`](hard_schema_enforcement_2026_05_08.md)
- [`api_football_minimal_flattening_removal_2026_05_07.md`](api_football_minimal_flattening_removal_2026_05_07.md)
- [`cme_polymarket_arb_2026_05_08.md`](cme_polymarket_arb_2026_05_08.md).

**Scope (7 items, P0-P1)**:

- [ ] [SCRIPT] P0. **Launcher consolidation: remaining 20 of 30 ad-hoc launchers** — Tab 11 yesterday migrated 10;
      finish the rest. Per CLAUDE.md "VM launcher script SSOT": every launcher under
      `deployment-service/scripts/vm/launch-{asset_group}-{flavor}-vm.sh` + `VM_PREFIX_TO_BUCKET` registry +
      `_SERVICE_LAUNCHER_SCRIPTS` registration if Deploy-Missing UI reachable + relaunch watchdog after each prefix add.
      ~2 AI-days.
- [ ] [TEST] P0. **data_status_comprehensive_test_coverage all 30 todos** — 5 test categories × 6 repos. Per
      [`data_status_comprehensive_test_coverage_2026_05_07.md`](data_status_comprehensive_test_coverage_2026_05_07.md).
      Each test category has explicit assertion shape per the plan body. ~3 AI-days.
- [ ] [SCRIPT] P1. **mtds_databento path-streaming Phases 2-4** — Phase 2 memory profiler verification on heavy day;
      Phase 3 chunked streaming for `get_async_range`; Phase 4 deployment-VM smoke + memory-bound assertion. Per
      [`mtds_databento_path_streaming_2026_05_07.md`](mtds_databento_path_streaming_2026_05_07.md). ~1.5 AI-days.
- [ ] [SCRIPT] P0. **mtds_per_instrument_download_api Phase 1.5 chain axis** — audit named CRITICAL-PATH per
      [`mtds_per_instrument_download_api_2026_04_24.md`](mtds_per_instrument_download_api_2026_04_24.md). Adds chain
      axis to the per-instrument download API; needed for DeFi instrument download support. ~1 AI-day.
- [ ] [SCRIPT] P0. **hard_schema_enforcement Phases 1-5 mechanical migration scripts per asset_group** — per
      [`hard_schema_enforcement_2026_05_08.md`](hard_schema_enforcement_2026_05_08.md). Each asset*group gets a one-time
      migration script in instruments-service `scripts/migrate*<asset_group>\_to_hard_schema.py`
      (precedent:`migrate_local_sfi_to_canonical.py`). Per CLAUDE.md "Manifest migration, NOT fallback". ~2.5 AI-days.
- [ ] [SCRIPT] P0. **api_football_minimal_flattening_removal all 16 todos** — UAC normalize.py:377-381 fix + re-fetch
      VM + manifest flip per
      [`api_football_minimal_flattening_removal_2026_05_07.md`](api_football_minimal_flattening_removal_2026_05_07.md).
      Per CLAUDE.md "Manifest migration, NOT fallback" — write a migration script + remove the flattening fallback. ~1
      AI-day.
- [ ] [SCRIPT] P1. **cme_polymarket_arb 6 phases** — config + CLOB / CME tick wiring + execution route + DART per
      [`cme_polymarket_arb_2026_05_08.md`](cme_polymarket_arb_2026_05_08.md). New archetype RFC-based; reference plan
      for similar arch wiring. ~2 AI-days.
- [ ] [BACKTEST+SCRIPT] P0. **prediction_markets full backtest pipeline run** — per
      [`prediction_markets_may_23_2026.epic.md`](../archive/prediction_markets_may_23_2026.epic.md). Polymarket +
      Kalshi + Opinion Trade + CME event futures arb full backtest. Pre-req: Tab 1 Predictions Phase 2+3 complete
      (lifecycle ingestion + canonical_question_group migration). Output: full backtest report. ~2 AI-days.
- [ ] [BACKTEST+SCRIPT] P0. **sports_ml full backtest pipeline run** — per
      [`sports_ml_may_23_2026.epic.md`](../archive/sports_ml_may_23_2026.epic.md). Sports ML prediction (odds + features
      → strategy → execution, all backtest). Pre-req: Tab 5 api_football_minimal_flattening_removal + Tab 4 sports
      per-source reconciler hook. Output: full backtest report per league tier. ~2 AI-days.
- [ ] [BACKTEST+SCRIPT] P0. **price_arbitrage full backtest pipeline run** — per
      [`price_arbitrage_may_23_2026.epic.md`](../archive/price_arbitrage_may_23_2026.epic.md). CME futures
      same-day-expiry arb + ETF↔future arb (TradFi). Pre-req: Tab 4 TradFi MDPS post-drain ES.OPT 11-cluster validation
      green. Output: full backtest report per arb pair. ~2 AI-days. (NOTE: cme_polymarket_arb above is a DIFFERENT
      archetype — same-day-expiry CME arb here is the broader TradFi cohort.)

**Repos owned (collision boundary)**: deployment-service `scripts/vm/` + `vm_zombie_watchdog.py` (you create files; Tab
4 launches existing files — coordinate via handshake), all 7 plan-target repos (each plan touches distinct surface).
**Hands off** anything cross-cutting (UAC schema design, UTL helper design) to Ikenna side.

**Read-first**:

- CLAUDE.md sections: "VM launcher script SSOT", "VM Naming Convention", "Singleton-locked launchers", "Manifest
  migration, NOT fallback", "Per-asset-group shard-key matrix"
- All 7 plan-of-records (above; substantial reading — fan out to sub-agents per plan)

**Sub-agent fan-out**:

- 7 parallel sub-agents (one per plan). Each gets a self-contained task with full done-definition. Send all 7 in ONE
  message at boot.
- Within each sub-agent's task, further sub-fan-out as plan dictates (e.g. data_status_test 5 test categories × 6 repos
  = 30 sub-sub-agents in one message; launcher consolidation 20 launchers = 20 sub-sub-agents).

**Sub-agent isolation table** — TAB 5 IS THE HIGHEST COLLISION-RISK TAB this cycle. Paste the relevant row verbatim into
each Task prompt; pre-commit `git diff --cached --name-only` MUST match the "Files owned" cell exactly. Every cell here
is a contract.

| Sub-agent ID        | Files owned (only edit these)                                                                                                                                                                                                                            | Files OFF-LIMITS                                                                                                                                                                                                         |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| sa5.LaunchCons      | `deployment-service/scripts/vm/launch-*.sh` NEW files (20 migrations); `deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` dict additions; `deployment-api/services/deploy_missing.py` `_SERVICE_LAUNCHER_SCRIPTS` registry adds | Existing launchers Tab 4 invokes (DO NOT delete originals until Tab 4 confirms cutover); Ikenna T1 launchers (DeFi Pyth Hermes etc.); MDPS / MTDS adapters                                                               |
| sa5.DSTests         | `data-status/tests/**` NEW; `deployment-api/tests/data_status/**` NEW; `deployment-ui/src/__tests__/data-status/**` NEW; sister test dirs in 3 other repos per `data_status_comprehensive_test_coverage` plan                                            | All non-test source files; Tab 3 deployment-ui live components (only edit `__tests__/` siblings); Ikenna T5 audit-log code                                                                                               |
| sa5.MTDS-pathstream | `market-tick-data-service/market_tick_data_service/adapters/databento_adapter.py` chunked-streaming methods + `tests/adapters/test_databento_path_streaming.py` + memory profiler script                                                                 | MTDS `umi_tick_provider.py` (sa5.MTDS-perInstr owns); MTDS prediction adapters (Tab 1 owns); MTDS DeFi adapters (Ikenna T1 owns); UAC                                                                                    |
| sa5.MTDS-perInstr   | `market-tick-data-service/market_tick_data_service/api/per_instrument_download.py` chain axis add + `tests/api/test_per_instrument_chain_axis.py`                                                                                                        | MTDS adapters (sa5.MTDS-pathstream + Tab 1 + Ikenna T1 own different ones); UAC; UTL                                                                                                                                     |
| sa5.HardSchema      | `instruments-service/scripts/migrate_<asset_group>_to_hard_schema.py` NEW (5 migration scripts, one per asset_group); UAC `canonical/manifest/schema_v6.py` column adds (NOT `chain_env.py`)                                                             | UAC `canonical/crosscutting/chain_env.py` (Ikenna T1 owns `PROTOCOL_LAUNCH_DATES`); UAC `canonical/strategy/` + `canonical/client/` (Ikenna T6 owns); existing manifest reader fallback paths                            |
| sa5.APIFootball     | UAC `external/api_football/normalize.py:377-381` + tests; sports re-fetch VM launcher; sports manifest flip migration script                                                                                                                             | Other UAC paths; sports backfill VMs Tab 4 launches (sa5 ships re-fetch launcher; Tab 4 may also launch sports VMs — coordinate via plan-of-record); features-sports-service                                             |
| sa5.CMEPolyArb      | UAC `canonical/strategy/cme_polymarket_arb_archetype.py` NEW + tests; strategy-service archetype config; execution-service route entry + DART persona test                                                                                               | UAC `canonical/strategy/catalogue.py` + `ids.py` (Ikenna T6 owns the catalogue + ID schema; sa5.CMEPolyArb consumes after Ikenna T6 RESOLVED); other archetype configs                                                   |
| sa5.PredMkts-bt     | prediction_markets backtest pipeline runner script + report output dir                                                                                                                                                                                   | Strategy-service archetype source; UAC; features-service; MTDS prediction adapters (depends on Tab 1 P2+P3 — wait for Tab 1 RESOLVED before running)                                                                     |
| sa5.SportsML-bt     | sports_ml backtest pipeline runner script + report output dir                                                                                                                                                                                            | Strategy-service archetype source; UAC; features-sports-service (Harsh T2 features-consolidation owns); api_football_minimal_flattening (sa5.APIFootball must finish first); Tab 4 sports reconciler (must finish first) |
| sa5.PriceArb-bt     | price_arbitrage backtest pipeline runner script + report output dir                                                                                                                                                                                      | Strategy-service archetype source; UAC; MDPS TradFi shards (Tab 4 ES.OPT 11-cluster validation must finish first)                                                                                                        |

**Within-sub-agent fan-outs** (sub-sub-agents must each get their own row in their parent sub-agent's Task prompt):

- sa5.LaunchCons spawns 20 sub-sub-agents (one per launcher migration). Each owns ONE NEW `launch-X-vm.sh` file + ONE
  `VM_PREFIX_TO_BUCKET` dict-entry add. After every batch of ≤5 prefix adds, master sa5.LaunchCons relaunches the
  watchdog VM (CLAUDE.md "VM Naming Convention" rule).
- sa5.DSTests spawns up to 30 sub-sub-agents (5 test categories × 6 repos). Each owns ONE test file in ONE repo;
  sub-sub-agents within the same repo must NOT touch the same `conftest.py` or shared fixture file simultaneously —
  sequence by category within each repo.
- Other sa5.\* may sub-fan-out per-asset_group or per-leg as their parent plan dictates; same isolation discipline: one
  file per sub-sub-agent, every prompt cites the parent's "Files owned" subset.

**Collision risk**:

- deployment-service `scripts/vm/`: Tab 4 LAUNCHES existing scripts; you CREATE new ones + register prefixes.
  Coordinate: ship any new prefix in `VM_PREFIX_TO_BUCKET` BEFORE Tab 4 launches a VM with that prefix.
- UAC: Ikenna Tab 1 (`PROTOCOL_LAUNCH_DATES` flips); you (`api_football_minimal_flattening_removal` UAC change +
  `cme_polymarket_arb` UAC enums + `hard_schema_enforcement` UAC schema columns). Different lines + different files;
  pre-commit `git diff --cached --name-only` MUST match exactly your subset.
- MTDS: Ikenna Tab 1 (DeFi adapters); you (mtds_databento path-streaming + mtds_per_instrument_download_api). Different
  files.

**Done definition**:

1. ✅ 20 launchers migrated; watchdog relaunched; each new prefix Deploy-Missing-UI-reachable.
2. ✅ All 30 data_status tests shipped + green across 6 repos.
3. ✅ mtds_databento Phases 2-4 + memory profiler shows bounded peak.
4. ✅ mtds_per_instrument_download_api Phase 1.5 chain axis shipped + DeFi download integration test green.
5. ✅ hard_schema_enforcement migration scripts per asset_group + reader fallback removed.
6. ✅ api_football_minimal_flattening_removal: 16 todos shipped + sports backfill VM cycles correctly through the new
   shape.
7. ✅ cme_polymarket_arb 6 phases shipped + DART persona test green.

---

## TAB 6 — Cross-cutting build (catalogue rows + ID refactor + client tagging + DART UI)

**Identity**: you own the implementation side of cross_cutting epic deliverables #1-#4. Audit 2026-05-08 found these
were unassigned across Tabs 1-5; this tab is the operator's mid-cycle add to close the gap before May-23. Pure
implement-from-spec work — Ikenna T6 ships UAC SSOTs + DART codex spec, you consume + ship the consumer wiring + UI.

**Plan-of-record**: [`cross_cutting_may_23_deliverables_2026_05_08.md`](cross_cutting_may_23_deliverables_2026_05_08.md)
(shared with Ikenna Tab 6) +
[`plans/epics/cross_cutting_may_23_2026.epic.md`](../epics/cross_cutting_may_23_2026.epic.md) (parent epic).

**Scope (5 items, P0-P1)**:

- [ ] [SCRIPT] P0. **Strategy ID refactor sweep** — every code-path that creates a trade / fill / signal /
      model-inference uses strategy IDs (not free-form strings). Mechanical sweep across **execution-service** (order
      submission + fill ingestion), **strategy-service** (signal generation), **ml-inference-service** (inference
      output), **pnl-attribution-service** (per-fill attribution), **batch-live-reconciliation-service** (per-trade
      diff), **position-balance-monitor** (position tag), **alerting-service** (rule-fired strategy ID), and
      **deployment-api** (deploy_missing strategy filter). Pre-Ikenna-T6 phase: identify every callsite via
      grep+ast-walk into a checklist; post-Ikenna-T6: apply `derive_strategy_id(catalogue_row)` at each site. ~3
      AI-days.
- [ ] [SCRIPT] P0. **Strategy catalogue row population** from Ikenna T6's UAC schema — enumerate every
      `(archetype, venue, instrument_type)` combination known to be feasible (full universe, including
      not-launching-this-cycle archetypes). Source: existing
      [`/codex/09-strategy/strategy-summary.md`](/codex/09-strategy/strategy-summary.md) 8-family / 18-archetype
      baseline + new archetypes from May-23 epics (3 carry sub-types, 3 price-arb sub-types, per-asset-group ML, 4
      prediction-market sub-types). Output: populated catalogue rows in UAC + per-archetype config defaults (collateral,
      hedge ratio, position cap, kill-switch thresholds). ~3 AI-days.
- [ ] [SCRIPT] P0. **Client-account-strategy tagging propagation** through every live trade + batch backtest result.
      Hooks into the strategy ID refactor sweep above — every trade also carries
      `(client_id, account_id,     strategy_id)` tuple. Capital allocation matrix from Ikenna T6 enforced at
      execution-service entry (reject if computed position would breach allocation). ~2 AI-days.
- [ ] [BUILD] P0. **DART manual-trade UI — 5 surfaces** per Ikenna T6's codex spec
      ([`/codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md`](/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md)
      or extension): (a) DeFi swap / lend / borrow / stake actions per chain × protocol for `carry_staked_basis`; (b)
      CeFi order placement (limit / market / stop) across Bybit / Deribit / Binance / OKX; (c) ML training trigger
      (pause / resume / retrain) per ML archetype; (d) sports bet placement for backtest exec validation; (e)
      prediction-market trade for backtest. Implementation lands in unified-trading-system-ui or deployment-ui per
      Ikenna T6's route assignment. ~3 AI-days.
- [ ] [BUILD] P1. **Strategy catalogue UI** — filter by asset_group / archetype / venue / live-vs-backtest. Reflects the
      full universe (catalogue rows shipped above). Route per Ikenna T6's scope decision. ~2 AI-days.

**Repos owned (collision boundary)**: execution-service (refactor sweep), strategy-service (signal generation +
catalogue consumer), ml-inference-service (inference tagging), pnl-attribution-service + batch-live-reconciliation-
service (attribution wiring), alerting-service (strategy_id in rule output — collides with Ikenna T5 alerting Phase 2-9;
coordinate via cross-tab "Tab 5 alerting takes precedence on rule structure; Tab 6 lays in strategy_id field"),
unified-trading-system-ui + deployment-ui (DART surfaces + catalogue UI; collides with Harsh T3 deployment-ui-
lifecycle-tabs on shared route shell — different page routes, no overlap).

**Read first**:

- [`cross_cutting_may_23_deliverables_2026_05_08.md`](cross_cutting_may_23_deliverables_2026_05_08.md) — shared
  plan-of-record (Ikenna T6 writes UAC schema spec into `## Open questions` resolved blocks; you read + consume)
- [`plans/epics/cross_cutting_may_23_2026.epic.md`](../epics/cross_cutting_may_23_2026.epic.md) — 5-deliverable scope
- Ikenna T6 ship-block in `cross_cutting_may_23_deliverables_2026_05_08.md` `## Open questions` (wait for green before
  consuming)
- [`/codex/09-strategy/strategy-summary.md`](/codex/09-strategy/strategy-summary.md) — existing catalogue baseline (your
  enumeration source)

**Sub-agent fan-out**:

- 1 main agent: orchestration + ID refactor sweep design
- 4 parallel sub-agents per repo cluster: (a) execution + strategy + ml-inference (signal/fill path); (b) pnl-attr +
  batch-live-recon + PBM (attribution path); (c) catalogue rows + UI implementation; (d) DART manual-trade UI 5 surfaces
  (the heaviest sub-task — sub-fan-out further per surface possible).

**Sub-agent isolation table** (paste rows verbatim into each Task prompt's "files OFF-LIMITS" section):

| Sub-agent ID         | Files owned (only edit these)                                                                                                                                                                                | Files OFF-LIMITS                                                                                                                                        |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| sa6.IDsweep-signal   | `execution-service/**/order_submission.py` + `**/fill_ingestion.py` strategy_id callsites; `strategy-service/**/signal_generation.py` strategy_id; `ml-inference-service/**/inference_output.py` strategy_id | UAC `canonical/strategy/` (Ikenna T6 owns); pnl-attr / batch-live-recon / PBM (sa6.IDsweep-attr owns); alerting-service rule structure (Ikenna T5 owns) |
| sa6.IDsweep-attr     | `pnl-attribution-service/**/per_fill_attribution.py` + `batch-live-reconciliation-service/**/per_trade_diff.py` + `position-balance-monitor-service/**/position_tag.py` strategy_id callsites                | execution / strategy / ml-inference signal-fill path (sa6.IDsweep-signal owns); UAC; alerting-service                                                   |
| sa6.IDsweep-alerting | `alerting-service` rule output `strategy_id` field add (only after Ikenna T5 ships the rule shell)                                                                                                           | alerting-service rule structure / publish hook / KillSwitchBus (Ikenna T5 owns); UAC                                                                    |
| sa6.IDsweep-deploy   | `deployment-api/**/deploy_missing.py` strategy_id filter param + UI surface                                                                                                                                  | deployment-api auth_middleware (Tab 3 owns); deployment-api launch endpoint (Tab 3 owns); deployment-ui live tabs (Tab 3 owns)                          |
| sa6.Catalogue-rows   | UAC `canonical/strategy/catalogue.py` row population (consumes Ikenna T6 schema after RESOLVED) + `tests/test_catalogue_rows.py`                                                                             | UAC `canonical/strategy/catalogue.py` schema/dataclass (Ikenna T6 owns); UAC `canonical/strategy/ids.py`; UAC `canonical/client/`                       |
| sa6.ClientTag        | execution-service entry-point allocation enforcement (`(client_id, account_id, strategy_id)` tuple propagation + reject-if-breach); per-fill / per-trade tagging in attribution + reconciliation services    | UAC `canonical/client/` schema (Ikenna T6 owns); strategy-service signal generation surface (sa6.IDsweep-signal owns)                                   |
| sa6.DART-defi        | unified-trading-system-ui DART DeFi swap/lend/borrow/stake surfaces per chain × protocol + Playwright smoke                                                                                                  | DART CeFi / ML / sports / prediction surfaces (other sa6.DART-\* own them); deployment-ui (Tab 3 owns)                                                  |
| sa6.DART-cefi        | unified-trading-system-ui DART CeFi order placement (limit / market / stop) across Bybit / Deribit / Binance / OKX + Playwright smoke                                                                        | Other DART surfaces; deployment-ui                                                                                                                      |
| sa6.DART-ml          | unified-trading-system-ui DART ML training trigger (pause / resume / retrain) per ML archetype + Playwright smoke                                                                                            | Other DART surfaces; deployment-ui; ml-training-service ML control endpoints (just call them, do not edit them)                                         |
| sa6.DART-sports      | unified-trading-system-ui DART sports bet placement for backtest exec validation + Playwright smoke                                                                                                          | Other DART surfaces; deployment-ui                                                                                                                      |
| sa6.DART-pred        | unified-trading-system-ui DART prediction-market trade for backtest + Playwright smoke                                                                                                                       | Other DART surfaces; deployment-ui                                                                                                                      |
| sa6.CatalogueUI      | unified-trading-system-ui (or deployment-ui per Ikenna T6 route assignment) catalogue UI page (filter by asset_group / archetype / venue / live-vs-backtest) + tests                                         | DART manual-trade surfaces; deployment-ui lifecycle tabs (Tab 3 owns)                                                                                   |

**Done-definition**:

- [ ] Strategy ID refactor sweep complete: every callsite uses derived ID; QG passes
- [ ] Catalogue rows populated: every (archetype, venue, instrument_type) combo from cross_cutting epic deliverable #1
      is a row
- [ ] Client tagging propagates: live trade + batch backtest result both carry `(client_id, account_id, strategy_id)`
- [ ] 5 DART manual-trade surfaces ship + Playwright smoke for each (per CLAUDE.md "UI replication" deliverable #4)
- [ ] Catalogue UI ships at the route Ikenna T6 assigned
- [ ] DONE block appended to plan-of-record citing every code commit sha

**Collision risk**: Strategy ID refactor touches MANY repos. Use `git add -p` per repo. Coordinate with all other Harsh
tabs on shared touch points (e.g. Tab 1 instruments-service catalog, Tab 2 features-repo consolidation). Pre-commit
`git diff --cached --name-only` MUST show only your files per CLAUDE.md mandatory pre-commit check.

## Cross-tab handshakes (within Harsh side)

Hard sync gates between tabs.

- [ ] **Tab 3 (deployment-UI Phase A UAC SSOT) → Tab 1 (instruments-live UI tab content)**: lifecycle column SSOT lands
      first; Tab 1 wires content on top.
- [ ] **Tab 5 (launcher consolidation new prefix) → Tab 4 (VM launches)**: any new prefix in `VM_PREFIX_TO_BUCKET` ships
      first; Tab 4 launches with that prefix afterwards.
- [ ] **Tab 2 (features-repo consolidation Phase 4) → Tab 4 (sports reconciler hook)**:
      features_sports_reconcile_available_at lives in features-sports-service today; will move to features-service after
      consolidation. **Mitigation**: Tab 4 wires hook against current path; Tab 2 updates the import path during Phase 4
      sweep.
- [ ] **Tab 4 (cefi drain done) → Tab 5 (data_status tests rerun)**: data_status integration tests assume drain
      complete. Sequence: drain → rerun.
- [ ] **Tab 1 (instruments-live Phase E predictions) → Tab 1 (Predictions Phase 2+3)**: same tab, sequential.

## Cross-side handshakes (Harsh ↔ Ikenna)

Mirror-image entries appear in [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md).

- [ ] **Harsh Tab 1 (instruments-live + lifecycle ingestion) → Ikenna Tab 1 (lending-indices Bug 3 fix)**: Bug 3 =
      instruments-store-defi 2022 metadata floor. Harsh's instruments-live Phase D (defi instrument lifecycle
      activation) + catalog-aware writer-guard land the catalog-aware floor. Ikenna's Bug 3 fix reads the new catalog.
      Hard sync: Harsh Phase D + writer-guard ship first.
- [ ] **Harsh Tab 2 (features_repo_consolidation Phase 1-4) → Ikenna Tab 2 (live-pipeline Phase 4-7)**: Live-pipeline
      Phase 4-7 wires the consolidated features repo. **Hard ordering**: features_repo_consolidation Phase 1-4 must land
      before live-pipeline Phase 4-7. Harsh announces feat repo consolidation Phase 4 ship in plan-of-record
      `## Open questions`; Ikenna pulls + starts Phase 4-7 wiring.
- [ ] **Harsh Tab 2 (ml-features-phase2a wires) → Ikenna Tab 2 (live-pipeline Phase 11 ServiceEmissionPolicy slice b)**:
      Slice b couples to assert_no_lookahead_for_feature_group; ml-features-phase2a wires it into 8 services.
      Coordinate: Harsh ships per-service wires; Ikenna reads the wires + extends ServiceEmissionPolicy state to reflect
      lookahead-bias-checked status.
- [ ] **MDPS `base_adapter.py` 3-way collision — HARD SEQUENCE (codified 2026-05-08 audit)**: three sub-agents touch
      this file across two operators. To prevent the documented foot-gun pattern (PM@961980db / @611b9501 / @34075d84)
      where parallel `git add` / reset wipes staged hunks, enforce: 1. **Harsh T2 features-consolidation Phase 1-4 ships
      FIRST** — extracts features-cefi/tradfi compute paths into `features-service/`, replacing existing MDPS
      `base_adapter.py` calls. Master sa2.P3-rewrite is the only writer in this window. 2. **Ikenna T2 sa2.P4-cefi
      (live-pipeline) wires SECOND** — adds pipeline_mode partition + replay subsystem hooks to MDPS `base_adapter.py`
      AFTER Harsh T2 has finished its rewrite sweep + pushed. 3. **Harsh T2 sa2.PhaseAB×8 (lookahead-bias) wires THIRD**
      — adds `assert_no_lookahead_for_feature_group` calls at compute entry, on top of the live-pipeline-wired version.
      Each step waits for the previous step's RESOLVED block in
      [`features_repo_consolidation_2026_05_08.md`](features_repo_consolidation_2026_05_08.md) /
      [`live_pipeline_mtds_mdps_features_2026_05_08.md`](live_pipeline_mtds_mdps_features_2026_05_08.md)
      `## Open     questions`. **No surgical `git add -p` in parallel** — sequence enforced via plan-of-record
      signaling.
- [ ] **Harsh Tab 3 (deployment-ui-lifecycle-tabs auth re-shape) → Ikenna Tab 5 (deploy_missing audit-log
      integration)**: audit-log integration wraps the auth re-shape. Hard ordering: Harsh ships auth re-shape Phase D;
      Ikenna ships audit-log on top.
- [ ] **Harsh Tab 4 (per-asset_group VM ops + reconcilers) → Ikenna Tab 3 (cross-asset rescan design + LAUNCHER)**:
      Ownership clarified — **Ikenna T3 sa3.Rescan-launcher writes the rescan launcher script** (in
      `instruments-service/scripts/` or `deployment-service/scripts/vm/`); **Harsh T4 operates it** on a same-region GCE
      VM. Sequence: Ikenna T3 ships design + launcher + announces RESOLVED in
      [`manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md) `## Open questions`
      → Harsh T4 runs `--dry-run` per asset_group → operator reviews CSV → Harsh T4 runs `--apply-write` → Ikenna T3
      handles edge-case triage file.
- [ ] **UAC editor priority queue (codified 2026-05-08 audit)**: Up to 4+ sub-agents could touch UAC simultaneously
      (Harsh T2 sa2.P5-uac-col `feature_family` column; Harsh T5 sa5.HardSchema schema_v6 column adds, sa5.APIFootball
      `external/api_football/normalize.py`, sa5.CMEPolyArb `canonical/strategy/cme_polymarket_arb_archetype.py`; Ikenna
      T1 already-shipped `chain_env.py` `PROTOCOL_LAUNCH_DATES`; Ikenna T6 NEW `canonical/strategy/catalogue.py` +
      `ids.py` + `canonical/client/model.py`). The conditional-push rule catches collisions at push time but earlier
      serialization is cheaper. **Priority queue (top → bottom; each waits for previous to RESOLVED in
      cross_cutting_may_23_deliverables_2026_05_08.md `## Open questions`)**: 1. Ikenna T6 NEW dirs
      (`canonical/strategy/catalogue.py`, `ids.py`, `canonical/client/model.py`) — brand-new files, zero overlap risk;
      ships first. 2. Ikenna T1 `chain_env.py` flips — already shipped UAC@6c873e4; remaining drift fixes in same
      window. 3. Harsh T2 sa2.P5-uac-col `feature_family` column in `canonical/feature/family.py` (NEW dir). 4. Harsh T5
      sa5.HardSchema `canonical/manifest/schema_v6.py` column adds. 5. Harsh T5 sa5.APIFootball
      `external/api_football/normalize.py:377-381`. 6. Harsh T5 sa5.CMEPolyArb
      `canonical/strategy/cme_polymarket_arb_archetype.py` — same DIR as Ikenna T6 (#1) but DIFFERENT FILE; serialize
      after Ikenna T6 ships catalogue + ids files so the dir state is stable. Each editor pre-commit-checks
      `git diff --cached --name-only` matches their assigned file subset exactly.
- [ ] **Ikenna Tab 6 (UAC strategy SSOTs + DART scope) → Harsh Tab 6 (consumer wiring + DART UI)**: cross_cutting epic
      deliverables #1-#4. **Hard ordering**: Ikenna T6 ships UAC catalogue + ID + client schemas + DART codex spec
      first; Harsh T6 consumes after. **Mitigation**: Harsh T6 can scaffold the strategy ID refactor sweep (identify
      every callsite that needs an ID without modifying yet) in parallel with Ikenna T6 schema design. Ikenna T6
      announces `## Open questions` resolved per-deliverable; Harsh T6 reads then ships.

## Collision-risk callouts (file-level)

- **deployment-service `scripts/vm/` directory**: Tab 4 (launches existing) + Tab 5 (creates new) share the dir.
  Different files. Pre-commit `git diff --cached --name-only` verifies. Tab 5 ships any new prefix in
  `VM_PREFIX_TO_BUCKET` BEFORE Tab 4 launches with that prefix; Tab 5 relaunches the watchdog VM after every batch of
  prefix adds (CLAUDE.md "VM Naming Convention").
- **MDPS `base_adapter.py`** (3-way collision — see HARD SEQUENCE in Cross-side handshakes above): Harsh T2
  features-consolidation rewrite FIRST → Ikenna T2 sa2.P4-cefi live-pipeline wiring SECOND → Harsh T2 sa2.PhaseAB×8
  lookahead-bias wires THIRD. Sequence enforced via plan-of-record signaling, NOT parallel `git add -p`.
- **UAC** (4+ editor priority queue — see HARD QUEUE in Cross-side handshakes above): Ikenna T6 NEW dirs first → Ikenna
  T1 drift fixes → Harsh T2 `feature_family` column → Harsh T5 schema/normalize/archetype adds in order. Each editor
  pre-commit-checks `git diff --cached --name-only` matches assigned subset exactly.
- **deployment-api `auth_middleware.py` + new launch endpoint**: Tab 3 (auth re-shape + new launch endpoint) + Ikenna
  Tab 5 (audit-log on top). Sequence enforced.
- **8 features-\* source repos**: Tab 2 (consolidation source repos). Tab 4 wires hook into features-sports exit-step
  (one of the 8). Coordinate during Phase 4 import-path migration.
- **`live-defi-rollout` push race**: per CLAUDE.md conditional push rule. Pre-commit `git status` +
  `git diff --cached --stat` (no path arg) MANDATORY before EVERY commit. Use `git add -p` / `git add <specific-file>`
  only. Branch does NOT trigger remote CI — every shippable unit's local `bash scripts/quality-gates.sh` Pass 1 is the
  ONLY quality gate (per top-of-file CI gate reminder).

## Daily sync points

- **EOD T+0** (today, midnight UTC): Tabs 1-6 each report done-definition status to operator via plan-of-record
  `## Open questions` resolved + DONE block. CeFi drain reports done.
- **Tomorrow's daily reset**: 1 main-orchestrator-or-operator runs the daily reset per CLAUDE.md (fetch summary + Q&A
  sweep + draft tomorrow's split). Carryover items roll forward.
- **2026-05-13 features-repo consolidation deadline**: Tab 2 must land Phase 0-7 by then (5 days from today). Pre-req
  for Ikenna Tab 2's live-pipeline Phase 4-7.
- **2026-05-15 GCS migration deadline**: Ikenna Tab 3 deadline; Harsh Tab 4 supports the rescan.
- **2026-05-23 live-DeFi cutover**: master plan Group F+G must all be ✅. Tab 4 reports per-asset_group readiness;
  Ikenna Tab 5 aggregates.

## Defer post-cutover (BOTH must NOT touch)

(Same list as Ikenna's split — see [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md) §"Defer
post-cutover".)

## Spawn prompts (paste-ready per tab)

> Use these when opening a fresh Claude Code tab + telling it _"work on Tab N"_.

### Tab 1 spawn prompt

```text
You are Tab 1 — a sub-agent spawned by Harsh's main orchestrator agent (a separate Claude
Code session on the SAME PC, sharing the SAME .git/ + working tree as you).

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — workspace rules + § "Daily Work-Split Process".
  2. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — sub-agent inheritance.
  3. plans/active/work_split_2026_05_08_harsh.md § "TAB 1 — Instruments-live + lifecycle ingestion".
  4. plans/epics/instruments_live_master_2026_05_08.md (primary plan-of-record).
  5. plans/epics/predictions_master_2026_05_07.md Phase 2+3.

Your agent-tag: instruments-live-tab. Your tab number: 1.

ORCHESTRATION RULES per CLAUDE.md § "Daily Work-Split Process" universal mechanics —
shared working tree, conditional push, plan-doc Q&A flow, plan-flip in same logical unit
as code, Findings Triage Discipline.

YOUR TASK: ship Phase A-E + Predictions Phase 2+3 + catalog-aware writer-guard. See
work_split_2026_05_08_harsh.md § "TAB 1" for full done-definition.

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE-2026-05-08 block at bottom of each
plan-of-record.
```

### Tab 2 spawn prompt

```text
You are Tab 2 — a sub-agent spawned by Harsh's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "ARCHITECTURE 2026-05-08 — Live pipeline"
     (in the "Plans must capture full codebase impact upfront" rule context),
     § "Shard-granularity SSOT" ([UAC] vs [UTL] vs [per-service] discipline),
     § "Post-Plan-Phase Codex Audit HARD RULE".
  2. plans/active/work_split_2026_05_08_harsh.md § "TAB 2 — Features-repo consolidation".
  3. plans/active/features_repo_consolidation_2026_05_08.md (primary).
  4. plans/epics/ml_and_features_master_2026_05_07.md Phase 2A/2B + Phase 3.

Your agent-tag: features-consolidation-tab. Your tab number: 2.

YOUR TASK: ship features-repo consolidation Phase 0-7 + 8-service lookahead-bias wires
+ parquet column-pruning. See work_split_2026_05_08_harsh.md § "TAB 2".

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of each plan-of-record.
```

### Tab 3 spawn prompt

```text
You are Tab 3 — a sub-agent spawned by Harsh's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "Local Development",
     § "Workflow Templates", § "Plan Locking".
  2. plans/active/work_split_2026_05_08_harsh.md § "TAB 3 — Deployment-UI lifecycle tabs".
  3. plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md (primary).
  4. plans/active/deploy_missing_auto_launch_2026_05_07.md Phase 1+2.

Your agent-tag: deployment-ui-tab. Your tab number: 3.

YOUR TASK: ship Deployment-UI lifecycle tabs Phase A-E + deploy_missing Phase 1+2 (Phase
2 gated on Ikenna Tab 5 IAM decision shipping first). See work_split_2026_05_08_harsh.md
§ "TAB 3".

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of each plan-of-record.
```

### Tab 4 spawn prompt

```text
You are Tab 4 — a sub-agent spawned by Harsh's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "VM tarball deployment",
     § "VM Naming Convention", § "Singleton-locked launchers", § "No fire-and-forget VM
     launches", § "Manifest concurrency principle", § "Manifest phantom audit".
  2. plans/active/work_split_2026_05_08_harsh.md § "TAB 4 — Per-asset_group VM ops".
  3. plans/epics/cefi_master_2026_05_07.md (cefi drain).
  4. plans/epics/tradfi_master_2026_05_07.md (TradFi MDPS post-drain).
  5. plans/epics/manifest_migration_master_2026_05_07.md Stage 4 (rescan).
  6. plans/epics/sports_master_2026_05_07.md (per-source reconciler hook).
  7. plans/archive/issues/defi_988_missing_dates_audit_2026_05_08.md (top-5 priority list).

Your agent-tag: vm-ops-tab. Your tab number: 4.

YOUR TASK: ship cefi drain monitoring + TradFi cluster validation + cross-asset rescan
operation + sports reconciler hook + defi_988 targeted backfill. See
work_split_2026_05_08_harsh.md § "TAB 4".

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of each plan-of-record.
```

### Tab 5 spawn prompt

```text
You are Tab 5 — a sub-agent spawned by Harsh's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "VM launcher script SSOT",
     § "VM Naming Convention", § "Manifest migration, NOT fallback",
     § "Per-asset-group shard-key matrix".
  2. plans/active/work_split_2026_05_08_harsh.md § "TAB 5 — Mechanical refactors + audit cluster"
     including the Sub-agent isolation table (paste rows verbatim into each Task prompt).
  3. All 7 plan-of-records in TAB 5 scope (launcher consolidation + data-status tests +
     databento + per-instrument + hard_schema + api_football + cme_polymarket).

Your agent-tag: mechanical-refactor-tab. Your tab number: 5.

CRITICAL HANDSHAKES (do not violate):
  • VM_PREFIX_TO_BUCKET dict in deployment-service/scripts/vm/vm_zombie_watchdog.py MUST be
    extended BEFORE Harsh Tab 4 launches a VM with any new prefix you ship — coordinate via
    plan-of-record `## Open questions` ping when each new prefix is registered.
  • After EVERY new prefix add (or batch of adds), RELAUNCH the watchdog VM per CLAUDE.md
    § "VM Naming Convention" — running watchdog only fetches the Python at boot. Skipping
    relaunch silently zombies the new prefix (precedent: 2026-05-05 5-prefix incident).
  • UAC edits (api_football_minimal_flattening_removal + cme_polymarket_arb +
    hard_schema_enforcement) MUST follow the UAC editor priority queue declared in
    cross-side handshakes — Ikenna T6 ships canonical/strategy/ + canonical/client/ NEW
    dirs first, then Ikenna T1 finishes drift fixes, THEN Tab 5 mechanical adds. Wait for
    the green-flag in shared plan-of-record `## Open questions` before staging any UAC hunk.
  • Watchdog MUST be in VM_PREFIX_TO_BUCKET BEFORE the launcher consolidation commit lands;
    register-and-relaunch ride together as one shippable unit per launcher.

YOUR TASK: ship 7 plans of mechanical / parallel-safe / scoped refactor work. Fan out
7 parallel sub-agents (one per plan) at boot via a SINGLE message with 7 Task blocks.
See work_split_2026_05_08_harsh.md § "TAB 5" + the Sub-agent isolation table for the
file-ownership boundaries each sub-agent must respect.

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of each plan-of-record.
```

### Tab 6 spawn prompt

```text
You are Tab 6 — a sub-agent spawned by Harsh's main orchestrator agent (a separate Claude
Code session on the SAME PC, sharing the SAME .git/ + working tree as you).

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — full body (workspace standards). Esp.
     § "Daily Work-Split Process" + § "Two teammates × multiple parallel agents — don't
     edit unfamiliar files" + § "Sub-Agents & Autonomous Agents: Full Rules Required".
  2. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (symlink to CLAUDE.md;
     same content — sub-agent framing applies to you).
  3. plans/active/work_split_2026_05_08_harsh.md § "TAB 6 — Cross-cutting build" including
     the Sub-agent isolation table (paste rows verbatim into each Task prompt).
  4. plans/active/cross_cutting_may_23_deliverables_2026_05_08.md (shared plan-of-record
     with Ikenna Tab 6 — read `## Open questions` for Ikenna T6's UAC SSOT spec ship-blocks
     before consuming).
  5. plans/epics/cross_cutting_may_23_2026.epic.md — 5-deliverable scope (parent epic).
  6. /codex/09-strategy/strategy-summary.md — existing 8-family / 18-archetype catalogue
     baseline (your enumeration source).

Your agent-tag: cross-cutting-build-tab. Your tab number: 6.

ORCHESTRATION RULES (per CLAUDE.md § "Daily Work-Split Process" universal mechanics):
  1. Shared working tree — no `git pull` needed between tabs; pre-commit check
     (git status + git diff --cached --stat NO PATH ARG) mandatory before EVERY commit.
     Use `git add -p` for shared files; never `git add -A` / `git add <whole-shared-file>`.
  2. Plan-doc Q&A flow — write blockers into cross_cutting_may_23_deliverables_2026_05_08.md
     `## Open questions` (status 🟡 BLOCKED), append ping in plans/active/_agent_pings.md,
     continue with what you CAN do.
  3. Conditional push — per shippable unit: commit locally, fetch + check incoming, zero
     incoming → push, any incoming → flag + escalate.
  4. Plan-flip in same logical unit as code — checkbox flip + <repo>@<sha> evidence stamped
     in body, NOT batched at session end.
  5. Findings Triage Discipline (HARD RULE) — case-1-to-5 routing per CLAUDE.md.

CRITICAL HANDSHAKES (HARD ORDERING — do not violate):
  • Ikenna T6 → Harsh T6: Ikenna T6 ships UAC `canonical/strategy/catalogue.py` +
    `canonical/strategy/ids.py` + `canonical/client/model.py` + DART codex spec FIRST.
    Wait for the per-deliverable RESOLVED block in
    cross_cutting_may_23_deliverables_2026_05_08.md `## Open questions` before consuming.
  • While waiting on Ikenna T6: scaffold the strategy-ID refactor sweep (identify every
    callsite that needs `derive_strategy_id(catalogue_row)` — grep + AST walk into a
    checklist). DO NOT modify yet — only audit + capture in the plan body.
  • alerting-service `strategy_id` field landing: Ikenna T5 owns alerting Phase 2-9 rule
    structure; Tab 6 lays in `strategy_id` on top after Ikenna T5 ships the rule shell.
  • UI surfaces: Tab 3 here owns deployment-UI lifecycle re-shape; you own DART manual-trade
    UI + catalogue UI on different routes. Per-commit `git diff --cached --name-only`
    MUST show only your route directories.

YOUR TASK: ship the 5 items in TAB 6 (strategy ID refactor sweep + catalogue row population
+ client tagging propagation + 5 DART manual-trade surfaces + catalogue UI). Fan out per
the Sub-agent isolation table for TAB 6 in the work-split plan. See
work_split_2026_05_08_harsh.md § "TAB 6" for full done-definition + file-ownership table.

REPORT-BACK: per shippable unit, code commit + plan-flip commit, conditional push.
Final: append a "DONE-2026-05-08" block at the bottom of
cross_cutting_may_23_deliverables_2026_05_08.md body listing every code + plan-flip commit
sha. Then go quiet — don't pick up new work autonomously.
```

## Discipline reminders (every tab, every commit)

(Same as [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md) §"Discipline reminders" — see there for
the full list. Per CLAUDE.md § "Daily Work-Split Process" universal mechanics.)

## Done definition (whole layout)

When all 6 tabs hit their per-tab done-definition, today's Harsh split is complete. EOD: archive this plan to
`plans/archive/work_split_2026_05_08_harsh.md` + draft tomorrow's `work_split_2026_05_09_harsh.md` per the daily reset
protocol.

## Cross-references

- Companion: [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md) — Ikenna's mirror plan.
- Methodology spec: [`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) §"Daily Work-Split Process".
- Yesterday's archived split:
  [`plans/archive/work_split_2026_05_07_harsh_5tab_layout.md`](../archive/work_split_2026_05_07_harsh_5tab_layout.md).
- Master plan: [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) — the durable readiness model.
