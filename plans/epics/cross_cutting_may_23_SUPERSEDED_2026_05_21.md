---
doc_type: epic
title: cross-cutting-may-23-2026
summary:
  SUPERSEDED (2026-05-21) May-23 cross-cutting epic — its 5 deliverables (strategy catalogue, strategy IDs,
  clients+accounts, DART UI-replication of every live action, infrastructure/stability) are absorbed into
  client_isolation_and_governance_master + infrastructure_master + observability_master; kept as archaeology only, no
  new work here.
status: superseded
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [migration, governance, strategy, ui, infrastructure, consolidation]
related:
  [
    /plans/epics/client_isolation_and_governance_master.md,
    /plans/epics/infrastructure_master.md,
    /plans/epics/observability_master.md,
    ../active/master_to_live_defi_2026_05_23.md,
  ]
created: 2026-05-08
name: cross-cutting-may-23-2026
tier:
priority:
assigned_vm: vm-cross-cutting
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
plan_type: epic
owner: ikenna
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
deadline: 2026-05-23
---

# Epic — Cross-Cutting (May 23 2026) — SUPERSEDED 2026-05-21

> **⚠️ SUPERSEDED-BY 2026-05-21**: The everlasting workspace-wide scope (clients, strategy catalogue, UI replication,
> infrastructure, jurisdiction, share-class, UAC schema, hardcoded-value cleanup) is absorbed into the L4 epic
> [`client_isolation_and_governance_master.md`](client_isolation_and_governance_master.md) (extended scope) +
> [`infrastructure_master.md`](infrastructure_master.md) (infra-specific parts) +
> [`observability_master.md`](observability_master.md) (alerting + monitoring).
>
> This file is kept as **archaeology only** — DO NOT add new work here. New active plans declare the appropriate
> `parent_epic:` (typically `client_isolation_and_governance_master` for cross-cutting governance work). Full epic-flow
> SSOT: [`README.md`](README.md).

---

## Why this epic exists

Five cross-cutting concerns wrap around all 6 domain epics for May 23. None of them are domain-specific; all of them are
non-negotiable for cutover. Per operator direction 2026-05-08:

> "Cross-cutting concerns across all of them are things like clients, strategy IDs, strategy catalogue (even if we're
> not launching all the strategies, is a hard requirement for May 23 that we have all of the archetypes and all of the
> venue combinations and stuff done so that we know what the universe looks like)... a wrap around all of this is that
> the UI needs to be able to replicate everything that we're doing... Anything to do with infrastructure, stability,
> environments, deployment, maturity, live functionality, speed, that all needs to be cross-cutting concerns for 23rd of
> May anyway, because the system has to be perfect in terms of infrastructure. We can't take shortcuts on that side."

## The 5 cross-cutting deliverables

**MVP universe SSOT** (codified 2026-05-13):
[`/codex/09-strategy/mvp-universe-per-asset-group.md`](/codex/09-strategy/mvp-universe-per-asset-group.md). Defines the
2-tier scope model — data capture (broad) vs backtest scope (narrow per asset_group) — and Tier A vs Tier B archetype
classification. Binding constraint for backtest config-grid sizing in `compute_optimization_mock_data_2026_05_13.md`.

### 1. Strategy catalogue (HARD requirement)

Every archetype × every venue combination must be enumerated in the strategy catalogue, **even if not launching this
cycle**, so the universe is visible. Live archetypes for May 23 are a small subset; the full universe must be modeled so
onboarding new ones post-May-23 is config-only, not code-greenfield.

- [ ] Strategy catalogue lists all archetype families: carry (3 sub-types), price-arb (3 sub-types), ML prediction
      (per-asset-group), prediction-markets (4 sub-types), and any others.
- [ ] Per-archetype venue matrix populated: every (archetype, venue, instrument-type) combination known to be feasible
      is a row.
- [ ] Per-archetype configuration parameters declared (collateral, hedge ratios, position caps, kill-switch thresholds).
- [ ] Strategy catalogue UI reflects the full universe (filter by asset_group / archetype / venue / live-vs-backtest).

### 2. Strategy IDs

Stable, traceable, machine-readable strategy IDs for every archetype × venue combination. Used by:

- live trades (per-fill attribution)
- batch backtest result attribution
- batch-vs-live reconciliation
- alerting (which strategy fired the alert)
- DART manual-trade replication
- model registry (which model is bound to which strategy ID, for ML-driven archetypes)

- [ ] Strategy ID schema declared in UAC (canonical naming + versioning).
- [ ] Strategy ID registry populated for every catalogue row.
- [ ] Every code-path that creates a trade / fill / signal / model-inference uses strategy IDs, not free-form strings.

### 3. Clients + Accounts

Client and account configuration must be wired for live capital allocation across all live archetypes (DeFi rollout +
CeFi ML).

- [ ] Client model in UAC stable; account-per-venue mapping wired.
- [ ] Capital allocation matrix per (client, archetype, venue) declared and respected at execution time.
- [ ] Client-account-strategy tagging propagated through every live trade + batch backtest result.

### 4. UI replication of every live action (DART manual-trade lane)

Every live trade / model training / DeFi swap / CeFi order / sports bet that the system can do automatically must also
be replicable as a **manual operator action through the UI**. This is the operator's safety valve — if the automated
side has a bug, the manual side ships the trade.

- [ ] DART manual-trade UI supports every live archetype (DeFi rollout carry archetypes + CeFi ML archetype).
- [ ] DART exposes manual ML training trigger (pause-resume model retraining for any in-flight ML archetype).
- [ ] DART exposes manual DeFi swap / lend / borrow / stake actions for the carry-staked-basis archetype.
- [ ] DART exposes manual CeFi order placement across the 4 live CeFi venues.
- [ ] DART exposes manual sports bet placement (for sports backtest exec validation, not live).

### 5. Infrastructure / stability / environments / deployment maturity / live functionality / speed

The system has to be **perfect** at the infrastructure layer for May 23 cutover. Any shortcuts here jeopardise the live
trading goal directly.

- [ ] **Deployment maturity**: every service deployable via deployment-UI without SSH; tarball + image deploy modes both
      work; AWS↔GCP parity for at least one carry archetype's full stack.
- [ ] **Environments**: staging / SIT / production environments isolated; promotion path canonical (quickmerge → main →
      staging → SIT → prod).
- [ ] **Live functionality**: every live-mode service (PBM, R&E, P&L attribution, alerting, batch-vs-live recon) shipped
      and code-complete, not scaffold.
- [ ] **Live observability**: VM event streaming complete; deployment-UI tails logs/events without SSH; per-instrument
      progress events emitted; silent-success-with-zero-output detectable from event stream alone.
- [ ] **Speed**: in-region slicer fast-path for data-status + drilldown; deployment-stack restart < 30s; dev tier 0
      boots < 60s.
- [ ] **Stability**: zombie watchdog covering every VM prefix; manifest concurrency protocol respected by every backfill
      script; per-VM shard isolation everywhere there's multi-worker.
- [ ] **CI infrastructure**: workspace-wide QG sweep clean (operator's 2026-05-07 → 2026-05-09 cleanup pass); semver
      agents healthy; force-sync drift checks clean.

## Sub-plans this epic consumes

| Path                                                                                                                                                         | Role                                                                                                                                                                                                                          | Status            |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| [`active/cross_cutting_may_23_deliverables_2026_05_08`](../active/cross_cutting_may_23_deliverables_2026_05_08.md)                                           | **Critical-path child plan** — May-23 critical-path slice covering deliverables #1-#4 (catalogue + IDs + clients + DART). Owners: Ikenna Tab 6 (design) + Harsh Tab 6 (build). Added 2026-05-08 mid-cycle to close audit gap. | Active            |
| [`infrastructure_master`](./infrastructure_master.md)                                                                                                        | Infrastructure umbrella (deployment, observability, AWS, runtime parity)                                                                                                                                                      | Active            |
| [`manifest_migration_SUPERSEDED_2026_05_21`](./manifest_migration_SUPERSEDED_2026_05_21.md)                                                                  | Manifest schema v6 + migration coordination                                                                                                                                                                                   | Active            |
| [`active/writegate_honest_coverage_endtoend_2026_05_06`](../active/writegate_honest_coverage_endtoend_2026_05_06.md)                                         | Write-gate / honest-coverage umbrella                                                                                                                                                                                         | Active            |
| [`active/available_at_lookahead_bias_completion_2026_05_08`](../active/available_at_lookahead_bias_completion_2026_05_08.md)                                 | `available_at` end-to-end chain coordinator (MDPS bar boundary + per-asset-group adapter stamping + `FEATURE_REQUIRED_INPUTS` expansion + Tab 12 deferral tracker + QG static check + e2e test)                               | Active            |
| [`active/aws_migration_defi_first_2026_05_07`](../active/aws_migration_defi_first_2026_05_07.md)                                                             | AWS↔GCP parity (DeFi-first scope, generalises post-May-23)                                                                                                                                                                    | Active            |
| [`archive/deployment_api_work_stream_a_2026_05_07.plan.md`](../archive/deployment_api_work_stream_a_2026_05_07.plan.md)                                      | deployment-api work stream A — shipped; archived. Residual deployment-api scope rolls up under [`infrastructure_master`](./infrastructure_master.md).                                                                         | ✓ Done (archived) |
| [`active/deployment_ui_lifecycle_tabs_2026_05_08`](../active/deployment_ui_lifecycle_tabs_2026_05_08.md)                                                     | deployment-UI lifecycle tabs (live observability)                                                                                                                                                                             | Active            |
| [`active/deploy_missing_auto_launch_2026_05_07`](../active/deploy_missing_auto_launch_2026_05_07.md)                                                         | Deploy-Missing UI auto-launch                                                                                                                                                                                                 | Active            |
| [`active/launcher_scripts_consolidation_into_deployment_service_2026_05_07`](../active/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md) | Launcher script SSOT consolidation                                                                                                                                                                                            | Active            |
| [`active/data_status_comprehensive_test_coverage_2026_05_07`](../active/data_status_comprehensive_test_coverage_2026_05_07.md)                               | Data-status test coverage                                                                                                                                                                                                     | Active            |
| [`active/data_status_drilldown_shard_atom_alignment_2026_05_07`](../active/data_status_drilldown_shard_atom_alignment_2026_05_07.md)                         | Data-status drilldown shard-atom alignment                                                                                                                                                                                    | Active            |
| [`strategy_and_dart_master_SUPERSEDED_2026_05_21`](./strategy_and_dart_master_SUPERSEDED_2026_05_21.md)                                                      | Strategy v2 + DART manual-trade lane (covers UI replication deliverable)                                                                                                                                                      | Active            |
| [`archive/audit_followups_2026_05_07.plan.md`](../archive/audit_followups_2026_05_07.plan.md)                                                                | Audit follow-ups across services — shipped; archived. Live follow-ups (if any) tracked in [`plans/active/issues/`](../active/issues/).                                                                                        | ✓ Done (archived) |
| [`active/hard_schema_enforcement_2026_05_08`](../active/hard_schema_enforcement_2026_05_08.md)                                                               | Hard schema enforcement (deployment maturity)                                                                                                                                                                                 | Active            |
| [`active/mtds_databento_path_streaming_2026_05_07`](../active/mtds_databento_path_streaming_2026_05_07.md)                                                   | MTDS streaming + speed                                                                                                                                                                                                        | Active            |
| [`active/mdps_streaming_and_backpressure_2026_05_07`](../active/mdps_streaming_and_backpressure_2026_05_07.md)                                               | MDPS streaming + speed                                                                                                                                                                                                        | Active            |
| [`active/mtds_per_instrument_download_api_2026_04_24`](../active/mtds_per_instrument_download_api_2026_04_24.md)                                             | MTDS per-instrument download API                                                                                                                                                                                              | Active            |
| [`archive/instruments_and_market_tick_data_completion_2026_05_01.plan.md`](../archive/instruments_and_market_tick_data_completion_2026_05_01.plan.md)        | Instruments + MTDS completion — shipped; archived. Live activation continues under [`instruments_live_master`](./instruments_master.md).                                                                                      | ✓ Done (archived) |
| [`archive/ml_pipeline_ui_integration_2026_04_16.plan.md`](../archive/ml_pipeline_ui_integration_2026_04_16.plan.md)                                          | ML pipeline UI integration (DART → ML training trigger) — shipped; archived. DART manual-trade lane continues under [`strategy_and_dart_master`](./strategy_and_dart_master_SUPERSEDED_2026_05_21.md).                        | ✓ Done (archived) |
| [`active/deployment_and_qg_strategy_implementation_2026_05_13`](../active/deployment_and_qg_strategy_implementation_2026_05_13.md)                           | Deployment + QG strategy implementation — workspace-wide QG ratchet closure and deployment maturity gates                                                                                                                     | Active            |
| [`active/batch_live_symmetry_2026_05_10`](../active/batch_live_symmetry_2026_05_10.md)                                                                       | Batch = live symmetry enforcement — pipeline mode propagation + schema parity audit across all asset_groups                                                                                                                   | Active            |
| [`active/disaster_recovery_circuit_breakers_2026_05_10`](../active/disaster_recovery_circuit_breakers_2026_05_10.md)                                         | Disaster recovery + circuit breakers — kill-switch arming + automated DR runbooks for May-23 live cutover                                                                                                                     | Active            |
| [`active/governance_qg_automation_gaps_post_cutover_2026_05_12`](../active/governance_qg_automation_gaps_post_cutover_2026_05_12.md)                         | Governance + QG automation gaps (post-cutover) — CI ratchet + semver-agent health + force-sync discipline post-May-23                                                                                                         | Active            |
| [`active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12`](../active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md)           | Codex doc currency + consolidation (post-cutover) — SSOT drift remediation and codex consolidation wave post-May-23                                                                                                           | Active            |
| [`active/basefc_validation_flip_2026_05_10`](../active/basefc_validation_flip_2026_05_10.md)                                                                 | BasePyright / basefc validation flip — workspace-wide basedpyright strict-mode ratchet enforcement                                                                                                                            | Active            |
| [`active/dart_manual_trade_ux_refactor_2026_05_13`](../active/dart_manual_trade_ux_refactor_2026_05_13.md)                                                   | DART manual-trade UX refactor — operator manual-trade gate UI for all live archetypes (Group G deliverable)                                                                                                                   | Active            |
| [`active/risk_simulations_limits_alerting_2026_05_10`](../active/risk_simulations_limits_alerting_2026_05_10.md)                                             | Risk simulations + limits + alerting — position-level risk limits + kill-switch thresholds + alerting rules for live trading                                                                                                  | Active            |
| [`active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12`](../active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md)                   | Alerting runbook + operator UX (post-cutover) — on-call runbooks + alert routing + operator notification surface post-May-23                                                                                                  | Active            |

## Cross-epic handshakes

- **Provides to:** Every other epic depends on this one. Strategy catalogue + strategy IDs + clients are referenced by
  every live or backtest archetype. UI replication is the operator's safety valve for every live archetype.
  Infrastructure is the substrate everything else runs on.

## Open questions

- [x] ✓ **Strategy catalogue completeness — RESOLVED 2026-05-08.** **Archetype-level completeness for May 23**, with
      venue / instrument-type drill-down lookups deferred to post-cutover. The v2 catalogue
      (`internal/architecture_v2/enums.py` 9-family / 53-archetype + `archetype_capability.py`
      `ARCHETYPE_CAPABILITY_REGISTRY`) already covers every archetype currently traded or backtested. Only May-23 live
      archetypes need fully-seeded `ArchetypeConfig` (CARRY_STAKED_BASIS Solana + Ethereum; CARRY_BASIS_PERP × 6 perp
      venues; ML_DIRECTIONAL_CONTINUOUS × 3 venues OKX/Binance/Bybit). Backtest-only archetypes consume catalogue rows
      by `(archetype, asset_group)` lookup via `is_archetype_live(archetype, asset_group)` helper. Full cross-product
      enumeration tracked as post-cutover sweep. See `plans/archive/operator_decisions_2026_05_08.plan.md`.
- [x] ✓ **DART manual-trade lane scope — RESOLVED 2026-05-08.** **Operator-only manual** (Ikenna + Harsh) for May 23.
      Third-party broker-style DART (external operators executing on behalf of clients) DEFERRED post-cutover. The
      May-23 deliverable is the 7-day live cefi_ml + DeFi run on a single client; no external operators in scope.
      6-persona Playwright matrix per `strategy_and_dart_master:Phase 2.2` covers operator-only personas (DESK / DEV /
      ADMIN / EXEC / RISK / OPS).
- [x] ✓ **AWS parity scope at this layer — RESOLVED 2026-05-08.** **DeFi-only by May 23 per master plan Q&A 4 default**,
      with full-workspace AWS coverage post-cutover. By May 23: (a) DeFi-relevant data migrated to AWS S3; (b)
      data-status working on AWS for DeFi asset_group; (c) DeFi backfill on AWS with `--force` proves batch deployment
      side; (d) DeFi backtest examples runnable on AWS; (e) DeFi live trading deployment + monitoring on AWS so the team
      can switch any DeFi deployment between AWS-live / AWS-batch / GCP-live / GCP-batch. Sports / predictions / TradFi
      / CeFi data + compute remain GCP-only this cycle.

## See also

- [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) — May-23 cutover master
- [`/codex/04-architecture/cloud-agnostic-migration.md`](/codex/04-architecture/cloud-agnostic-migration.md)
- [`/codex/05-infrastructure/launcher-script-ssot.md`](/codex/05-infrastructure/launcher-script-ssot.md)
- [`/codex/09-strategy/strategy-summary.md`](/codex/09-strategy/strategy-summary.md) — 9-family / 53-archetype catalogue
  (per 2026-05-08 codex drift-correction; pre-2026-05-08 doc said 8/18 — that was the 2026-04-17 baseline before the
  Phase 9 expansion). UAC `internal/architecture_v2/enums.StrategyArchetype` is the SSOT.
- [`/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md`](/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md)
- [`/codex/09-strategy/operational/onboarding-checklist.md`](/codex/09-strategy/operational/onboarding-checklist.md)
