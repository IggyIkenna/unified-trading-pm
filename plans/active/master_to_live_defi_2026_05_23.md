---
plan_type: meta
asset_group: cross-cutting
owner: ikenna
created: 2026-05-06
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-06
name: master-to-live-defi-2026-05-23
overview:
  Master rollup plan from now (2026-05-06) to live DeFi trading on a real wallet by 2026-05-23. Three deliverables in
  one doc - (1) master plan tracking surface that orchestrates the ~175 active sub-plans without duplicating them, (2)
  audit cross-referencing existing codex SSOTs and flagging plan/doc/code drift, (3) Q&A surface for decisions that
  cascade through everything else. The headline goal is two DeFi archetypes trading live on a real wallet for greater
  than or equal to seven continuous days - carry_staked_basis (ultimate priority - recursive LST staking with CeFi/DeFi
  perp short hedge) and leveraged_funding_arb (cross-venue funding spread). Both hedge on a six-venue perp universe
  spanning CeFi (Bybit, Deribit, Binance, OKX) and DeFi perp DEXs (Hyperliquid, Aster). Concurrent goal is full AWS plus
  GCP cloud parity by May 23 - DeFi-relevant data migrated to AWS, batch backfill plus backtest plus ML plus live
  trading all runnable on AWS, seamless switch between AWS-live, AWS-batch, GCP-live, GCP-batch. TradFi, Sports,
  Prediction stage to ML pipeline running on representative sample but not live this cycle. The plan never duplicates
  sub-plans - it references and orchestrates them. Doc-touchpoint map is bi-directional (read before working, update
  after changing) and a plan-doc-code drift audit table flags pre-existing drift that must be resolved before agents
  start writing code in the affected area.
---

# May-23 Cutover Master — Live DeFi Trading by 2026-05-23

## Epics index (May-23 cutover, restructured 2026-05-08)

This plan is the **umbrella of epics**. Per operator direction 2026-05-08, six same-domain epics were folded into their
master plans (less indirection); only `cross_cutting` remains as a standalone epic. Each May-23 deliverable now lives in
its master plan's `## May-23 deliverable` section.

| May-23 deliverable                      | Lives in master § "May-23 deliverable"                                                                                   | Scope                | Live/Batch | Archived epic (archaeology)                                                                           |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------- | ---------- | ----------------------------------------------------------------------------------------------------- |
| Live DeFi rollout (carry archetypes)    | [`defi_master`](./defi_master_2026_05_07.md#may-23-deliverable-folded-from-live_defi_rollout_may_23_2026epic-2026-05-08) | LIVE on real wallet  | Live       | [`archive/live_defi_rollout_may_23_2026.epic.md`](../archive/live_defi_rollout_may_23_2026.epic.md)   |
| CeFi ML                                 | [`cefi_master`](../epics/cefi_master_2026_05_07.md)                                                                      | LIVE on real capital | Live       | [`archive/cefi_ml_may_23_2026.epic.md`](../archive/cefi_ml_may_23_2026.epic.md)                       |
| S&P prediction (CME)                    | [`tradfi_master`](../epics/tradfi_master_2026_05_07.md) (deliverable A)                                                  | BATCH ML only        | Batch      | [`archive/sp_prediction_may_23_2026.epic.md`](../archive/sp_prediction_may_23_2026.epic.md)           |
| Price arbitrage (CME futures + ETFs)    | [`tradfi_master`](../epics/tradfi_master_2026_05_07.md) (deliverable B)                                                  | BACKTEST only        | Batch      | [`archive/price_arbitrage_may_23_2026.epic.md`](../archive/price_arbitrage_may_23_2026.epic.md)       |
| Sports ML                               | [`sports_master`](../epics/sports_master_2026_05_07.md)                                                                  | BACKTEST only        | Batch      | [`archive/sports_ml_may_23_2026.epic.md`](../archive/sports_ml_may_23_2026.epic.md)                   |
| Prediction markets                      | [`predictions_master`](../epics/predictions_master_2026_05_07.md)                                                        | BACKTEST only        | Batch      | [`archive/prediction_markets_may_23_2026.epic.md`](../archive/prediction_markets_may_23_2026.epic.md) |
| Cross-cutting (catalogue / IDs / infra) | [`epics/cross_cutting_may_23_2026.epic.md`](../epics/cross_cutting_may_23_2026.epic.md)                                  | Workspace-wide       | Both       | (still active — workspace-wide concerns spanning all domains; explicitly NOT folded)                  |

Read [`plans/epics/README.md`](../epics/README.md) for the layer model + lifecycle. Each master plan enumerates its
sub-plans; this master plan retains the cross-master readiness checklist + audit + Q&A below.

**Migration note (2026-05-08).** The 9 domain umbrella masters (`cefi_master`, `tradfi_master`, `sports_master`,
`predictions_master`, `ml_and_features_master`, `strategy_and_dart_master`, `infrastructure_master`,
`manifest_migration_master`, `instruments_live_master`) were moved from `plans/active/` to `plans/epics/` — references
throughout the workspace updated in the same commit. `defi_master_2026_05_07` stays in `plans/active/` per operator
direction (mid-flight + parallel-agent sensitivity).

---

## What this plan is — three deliverables in one doc

1. **Master plan (product).** The single rollup tracking surface from now to live DeFi trading on 2026-05-23. Sub-plans
   in `unified-trading-pm/plans/active/` remain authoritative for tactical work; this plan never duplicates them, only
   references and orchestrates.
2. **Audit (process).** Cross-references to existing codex SSOTs and the ~175 active sub-plans. Surfaces overlaps,
   staleness, and conflicts so agents don't re-litigate decisions.
3. **Q&A (decision-gating).** Surfaces unresolved questions in one place so the human (Ikenna / Harsh) can answer once
   and agents stop guessing.

**This plan does not execute anything.** It writes itself, references real artefacts, and once approved is promoted to a
workspace location (see _Tracking surface_ below) where agents pick it up.

---

## Why this exists, what success looks like

**Headline goal.** **Two DeFi archetypes** trade live on a real wallet for ≥7 continuous days by 2026-05-23 (17 days
from today, 2026-05-06):

1. **`carry_staked_basis`** — _ultimate priority_ — recursive LST staking + CeFi/DeFi perp short hedge. Locked plan:
   `carry_staked_basis_structure_axis_2026_05_04`.
2. **`leveraged_funding_arb`** — cross-venue funding-rate spread trade. Lead plan: `defi_master_2026_05_07` (umbrella
   that folds in `defi_pipeline_extension_2026_05_01`, `leveraged_leg_controller_2026_05_01`, and
   `defi_e2e_pipeline_2026_04_30` per the 2026-05-07 consolidation; historical detail preserved in `plans/archive/`).

Both archetypes hedge on a 6-venue perp universe spanning CeFi (Bybit, Deribit, Binance, OKX) and DeFi perp DEXs
(Hyperliquid, Aster) — **all six must be live**. TradFi / Sports / Prediction stay batch-only this cycle — but their ML
readiness ladders progress in parallel so the _next_ archetypes after DeFi launch quickly.

**Cloud-parity goal (concurrent with live trading goal).** Full AWS↔GCP parity by May 23: DeFi-relevant data migrated
to AWS (with prior cost analysis), data status working on AWS, batch backfill with `--force` working on AWS, backtests /
ML / strategy examples runnable on AWS, **and** a live trading deployment + monitoring instance running on AWS — so the
team can seamlessly switch any deployment between AWS-live / AWS-batch / GCP-live / GCP-batch. _Not every byte gets
migrated_ (waste of API quota when GCS already has it) — only what's needed for the DeFi proof.

**Authority split.**

- _Codex_ (`unified-trading-pm/codex/`) = target architecture. Mostly defined.
- _Sub-plans_ (`unified-trading-pm/plans/active/`, ~175) = current bug-fix / refactor / migration backlog.
- _This plan_ = readiness rollup + audit + Q&A + new work streams not yet plan-covered.

---

## Audit — existing SSOTs this plan augments (does NOT recreate)

The codex already has SSOTs covering most of what was raised in the brief. Cross-reference table:

| Concern raised                                 | Existing codex SSOT                                                                                                                      | Plan action                                                                                  |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Service readiness checklist                    | `codex/10-audit/REPO_READINESS_CHECKLIST.yaml` + per-service `codex/10-audit/repos/<service>.yaml` + `_checklist-template-enhanced.yaml` | **Augment** with 7 groups / 23 items below; populate per-service yamls for tier-1            |
| Cloud-agnostic build / runtime                 | `codex/04-architecture/cloud-agnostic-migration.md`                                                                                      | Augment with build-lineage gap (work-stream D below)                                         |
| Custody / treasury (Copper)                    | `codex/04-architecture/copper-custody-integration.md`, `custody-providers.md`, `wallet-hierarchy-and-capital-flow.md`                    | Verify CEFFU coverage (Binance institutional custody) — likely a gap                         |
| Batch=live equivalence                         | `codex/04-architecture/batch-live-pipeline.md`, `batch-live-symmetry.md`, `backtest-groups.md`                                           | Verify backtest-fidelity rules per asset_group (real gas, real market impact, real matching) |
| Alerting                                       | `codex/04-architecture/alerting-batch-live.md`                                                                                           | Verify live-mode rule coverage; wire to alerting-service                                     |
| Auto-recovery / kill switches                  | `codex/04-architecture/autonomous-recovery-matrix.md`                                                                                    | Verify per-archetype kill-switch coverage                                                    |
| P&L attribution                                | `codex/09-strategy/cross-cutting/pnl-attribution.md`                                                                                     | Verify wired into batch-vs-live recon                                                        |
| Operational modes (manual / paper / automated) | `codex/09-strategy/cross-cutting/operational-modes-matrix.md`                                                                            | Add DART manual-trade lane (work-stream C below)                                             |
| Strategy onboarding                            | `codex/09-strategy/cross-cutting/onboarding-checklist.md`                                                                                | Verify end-to-end flow for `carry_staked_basis`                                              |
| Lifecycle events / observability               | `codex/03-observability/lifecycle-events.md`, `coordination-events.md`                                                                   | Verify GCS event-streaming endpoint exists for deployment-api                                |
| Deployment topology                            | `codex/04-architecture/deployment-topology-diagrams.md`, `RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg`                                           | Verify all tier-1 services represented                                                       |
| Shard granularity                              | `codex/02-data/availability-manifest-and-data-status.md`                                                                                 | Already canonical post-2026-05-06 multi-axis correction                                      |
| Strategy archetypes                            | `codex/09-strategy/strategy-summary.md` (8 families / 18 archetypes)                                                                     | `carry_staked_basis` is the lead candidate                                                   |

**Audit conclusion:** ~85% of target architecture has codex coverage. The 5 codex gaps to fill are listed in _Codex SSOT
gaps_ below — they are smaller than they first appear because the foundational docs already exist.

---

## SSOT touchpoint map — bi-directional (read before working · update after changing)

**Principle.** _Docs are the intent._ Codex SSOTs are always **ahead of the code** and **in line with the plans**. The
order of operations is **doc → plan → code**, never code-then-doc-when-someone-remembers. Drift between any pair
(doc/plan/code) is the failure mode this plan is designed to prevent.

The map below is bi-directional:

- **Before working on X** — read the listed SSOTs first. They define the intent. If the intent is unclear or stale,
  update the doc _first_, then write/change code.
- **After changing X** — update the same SSOTs (and the matching plan) so the doc stays the source of truth. Drift
  between code and SSOT is a CI / review failure, not a follow-up.

Rule of thumb: if it lives in `CLAUDE.md`, update there too.

| If you change…                                                                          | Update these SSOTs                                                                                                                                                                                                                                                                                                                                                                                             |
| --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Manifest schema** (column, shard axis, validator, write-gate)                         | `codex/02-data/availability-manifest-and-data-status.md` · `codex/02-data/shard-granularity-cefi.md` · `codex/02-data/sports-scheduling-and-sharding.md` · `codex/02-data/prediction-schema-paths.md` · `codex/02-data/per-category-bucket-layouts.md` · `unified-trading-library/unified_trading_library/manifest_writer.py` (SSOT) · `CLAUDE.md` "Availability manifest" + "Shard-granularity SSOT" sections |
| **Batch/live equivalence rule**                                                         | `codex/04-architecture/batch-live-pipeline.md` · `batch-live-symmetry.md` · `backtest-groups.md` · `CLAUDE.md` "Batch = Live" + "Live = batch" sections                                                                                                                                                                                                                                                        |
| **Cloud-agnostic VM / build path**                                                      | `codex/04-architecture/cloud-agnostic-migration.md` · `codex/05-infrastructure/vm-tarball-deployment.md` · `codex/05-infrastructure/cloud-agnostic-build-lineage.md` (new — work-stream F) · `deployment-service/scripts/vm/` launchers · `deployment-api/deployment_api/routes/_code_builds_aws.py` · `CLAUDE.md` "VM tarball deployment" + "VM Naming Convention" sections                                   |
| **Strategy archetype config**                                                           | `codex/09-strategy/strategy-summary.md` · `codex/09-strategy/architecture-v2/` · `codex/09-strategy/cross-cutting/onboarding-checklist.md` · the archetype-specific sub-plan in `plans/active/` · `CLAUDE.md` if cross-cutting                                                                                                                                                                                 |
| **Custody / treasury wiring** (Copper, CEFFU)                                           | `codex/04-architecture/custody-providers.md` (single SSOT — Copper + CEFFU + LocalKey + Mock) · `wallet-hierarchy-and-capital-flow.md` · `unified-config-interface/testnet_contracts.py` PROTOCOL_SCHEMAS                                                                                                                                                                                                       |
| **Live observability** (events, alerts, kill switches, auto-recovery)                   | `codex/03-observability/lifecycle-events.md` · `coordination-events.md` · `codex/04-architecture/alerting-batch-live.md` · `autonomous-recovery-matrix.md` · `codex/05-infrastructure/live-deployment-monitoring.md` (new — work-stream B) · `unified-api-contracts/.../internal/events.py` (`LifecycleEventType`) · `CLAUDE.md` "no fire-and-forget VM launches" section                                      |
| **P&L attribution / batch-vs-live reconciliation**                                      | `codex/09-strategy/cross-cutting/pnl-attribution.md` · `batch-live-reconciliation-service` plan (work-stream E) · pnl-attribution-service plan (work-stream E)                                                                                                                                                                                                                                                 |
| **Service readiness** (per-service)                                                     | `codex/10-audit/repos/<service>.yaml` · `codex/10-audit/REPO_READINESS_CHECKLIST.yaml` · this master plan's matrix                                                                                                                                                                                                                                                                                             |
| **Operational modes** (manual / paper / automated, DART terminal)                       | `codex/09-strategy/cross-cutting/operational-modes-matrix.md` · `codex/04-architecture/research-service-and-dart-integration.md` (new — work-stream C)                                                                                                                                                                                                                                                         |
| **ML experiment lifecycle**                                                             | `codex/04-architecture/ml-experiment-lifecycle.md` (new — work-stream F) · `codex/02-data/data-lineage-MTDS-features-ml.md` · `ml_pipeline_revolution_2026_04_11` plan                                                                                                                                                                                                                                         |
| **Hot-reload semantics**                                                                | `codex/06-coding-standards/config-reloader-pattern.md` · `codex/04-architecture/live-strategy-config-hot-reload.md` (new — work-stream F) · `CLAUDE.md` "Service Infrastructure Requirements"                                                                                                                                                                                                                  |
| **Service infrastructure requirements** (ServiceBootstrap, health API, typed reloaders) | `codex/06-coding-standards/service-structure-standards.md` · `base-service.sh` STEP 5.x in PM · `CLAUDE.md` "Service Infrastructure Requirements (QG-Enforced)"                                                                                                                                                                                                                                                |
| **Asset-group vocabulary**                                                              | `CLAUDE.md` "Asset-group vocabulary" section · `unified_api_contracts.canonical.crosscutting.market_data_categories` · `venue_axis_asset_group_vocabulary_2026_04_25` plan                                                                                                                                                                                                                                     |
| **Lookahead bias / available_at semantics**                                             | `unified_api_contracts.canonical.crosscutting.availability_semantics` · `unified-trading-library/.../availability_stamping.py` · `codex/02-data/availability-manifest-and-data-status.md` § available_at · `codex/POST_PLAN_REALITY_2026_05_06.md` Principle 5 · `CLAUDE.md` "available_at is per-row" section                                                                                                 |

**Agent rule.** Before merging any change in scope of one of the rows above:

1. The agent's PR description must list the docs read at the start (the "doc-first" check).
2. The commit must touch **all** the listed SSOTs in the relevant row, or explicitly state in the PR description why a
   given SSOT is unaffected.
3. Cross-reference: the corresponding sub-plan in `plans/active/` must agree with the doc — if they disagree, update the
   plan first.

Drift between any of (codex doc, sub-plan, code) is a review-blocking failure.

---

## Plan ↔ Doc ↔ Code drift audit

This is the deliverable that ties the audit to action. For each high-leverage change area, flag whether the codex SSOT,
the corresponding sub-plan, and the code agree. **Items marked ⚠ are pre-existing drift to resolve as part of this
plan, before agents start writing code in the affected area.**

| Area                                                            | Codex SSOT                                                                                                                                  | Sub-plans                                                                                                                                                                                                                         | Drift status                                                                                              | Resolve via                                                                                                                                                               |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Manifest schema (v6)                                            | `02-data/availability-manifest-and-data-status.md` (current)                                                                                | `manifest_schema_v6_quote_margin_combo_2026_04_23`, `availability_manifest_v4_and_data_status_2026_04_13`                                                                                                                         | ⚠ Confirmed — `availability_manifest_v4_…` is the only stale active plan; self-tagged superseded         | Archive the v4 plan via work-stream G; doc already canonical v6 with v4/v5 hive-key fallback                                                                              |
| Shard granularity propagation                                   | `02-data/availability-manifest-and-data-status.md` (multi-axis correction post-2026-05-06)                                                  | `shard_granularity_ssot_propagation_2026_05_06.HANDOVER`, `writegate_honest_coverage_endtoend_2026_05_06`, `data_status_multi_axis_shard_propagation_2026_05_06`                                                                  | ⚠ Confirmed — `writegate_…` declared umbrella; other two are children but not yet `parent:`-tagged       | Re-tag children with `parent: writegate_honest_coverage_endtoend_2026_05_06` (work-stream G); surface only umbrella                                                       |
| Cloud-agnostic VM/build                                         | `04-architecture/cloud-agnostic-migration.md`                                                                                               | (no active plan — work-stream D is the new one)                                                                                                                                                                                   | ⚠ Doc partially describes target; VM launchers GCP-only in code                                          | Add VM-launcher parity appendix to the doc; new plan for AWS launchers                                                                                                    |
| Live-mode services (PBM, R&E, P&L attr, alerting, B-vs-L recon) | Mostly covered by `04-architecture/alerting-batch-live.md`, `autonomous-recovery-matrix.md`, `09-strategy/cross-cutting/pnl-attribution.md` | ✓ REVISED — PBM/R&E/P&L attr in `defi_master_2026_05_07` Fork 1 (folds `defi_e2e_pipeline_2026_04_30` per Stage 7 consolidation); B-vs-L recon in `consolidated_operational_validation_2026_04_15`; only **alerting** has no plan | ⚠ Only alerting genuinely missing a plan                                                                 | Open `alerting-service-live-rules_2026_05_07.plan.md`; extend the 4 existing plans with explicit live-mode todos (work-stream E REVISED)                                  |
| Custody (Copper + CEFFU)                                        | `04-architecture/custody-providers.md` (single SSOT — Copper + CEFFU + LocalKey + Mock), `wallet-hierarchy-and-capital-flow.md`             | (no active plan; CEFFU section is STUB inside custody-providers.md)                                                                                                                                                              | ⚠ CEFFU section unwritten in custody-providers.md (PENDING subsections)                                 | Populate CEFFU subsections inside `custody-providers.md` + plan as part of work-stream F + E                                                                              |
| Strategy v2 finalization                                        | `09-strategy/strategy-summary.md`, `architecture-v2/`                                                                                       | `strategy_architecture_v2_finalization_2026_04_19`, `strategy_architecture_v2_phase3_11_handoff_2026_04_17`                                                                                                                       | ⚠ Confirmed — finalization is live; handoff is historical (Phase 2 done)                                 | Mark handoff `parent_of: finalization`; verify residuals; archive once absorbed (work-stream G)                                                                           |
| DART / research-service                                         | `09-strategy/cross-cutting/operational-modes-matrix.md` (operational modes)                                                                 | `dart_ui_strategy_filtering_and_onboarding_2026_04_24` (self-tagged superseded), `dart_ux_cockpit_refactor_2026_04_29` (active superset)                                                                                          | ⚠ research-service has 0 repo, only PNG mockups; manual-trade lane not in codex                          | Archive DART UI plan; add `04-architecture/research-service-and-dart-integration.md`; extend operational-modes-matrix                                                     |
| ML experiment lifecycle                                         | `02-data/data-lineage-MTDS-features-ml.md` (partial)                                                                                        | `ml_pipeline_revolution_2026_04_11` (self-tagged superseded), `consolidated_ml_advanced_pipeline_2026_04_15` (active), `sp500_ml_readiness_master_2026_05_05`                                                                     | ⚠ No dedicated SSOT for ML job_id lifecycle; `ml_pipeline_revolution` should archive                     | Archive `ml_pipeline_revolution_2026_04_11` + `domain_agnostic_ml_framework_2026_04_11` (work-stream G); add `04-architecture/ml-experiment-lifecycle.md` (work-stream F) |
| Live observability / log streaming                              | `03-observability/lifecycle-events.md`, `coordination-events.md`                                                                            | (no active plan for GCS event-tail endpoint)                                                                                                                                                                                      | ⚠ Doc defines events; deployment-api endpoint doesn't exist                                              | Build endpoint as part of work-stream A; doc stays current                                                                                                                |
| **NEW (audit-discovered):** Plan frontmatter discipline         | `plans/PLAN_FORMAT.md`                                                                                                                      | n/a (workspace-wide systemic gap)                                                                                                                                                                                                 | ⚠ 95% missing `last_updated`, 96% missing `asset_group`, 21% missing `locked_by`, 5 plans no frontmatter | Workspace-wide one-shot backfill script (work-stream G)                                                                                                                   |
| **NEW (audit-discovered):** Service-overlap concentration       | n/a (master-plan tracking concern)                                                                                                          | 35 plans on instruments-service; 16 each on deployment-service / strategy-service / deployment-api; 12+ on UTS-UI / execution-service / deployment-ui                                                                             | ⚠ Real overlap risk; consolidation candidate post-cutover                                                | Post-May-23 cleanup; not blocking. Document on master plan; address in next cycle                                                                                         |

**Audit guideline going forward.** Whenever an agent touches a row in this table, the PR includes a one-line "drift
status: resolved / unchanged / new-drift" note in the description. New drift = a new row gets added here.

---

## Audit — sub-plan conflicts, overlaps, stale references (VERIFIED 2026-05-06)

Two parallel agents (mechanical frontmatter + topic-map sweep ; content-overlap pass) audited the **148 active
sub-plans** on 2026-05-06. **Headline corrections to the earlier suspicion list:** 3 of the 5 "NO-PLAN" live-mode
services are actually already in scope of `defi_master_2026_05_07` Fork 1 (folds `defi_e2e_pipeline_2026_04_30` per
Stage 7 consolidation) — only **alerting** genuinely needs a new dedicated plan. **18 self-tagged superseded plans**
should be archived. Frontmatter discipline is systemically broken (95% missing `last_updated`, 96% missing
`asset_group`, 21% missing `locked_by`) — needs a one-shot backfill script.

### Plan clusters → surface ONE per cluster on the master plan

| Cluster                          | Lead / umbrella plan                                                                                                                         | Children (reference, not duplicate)                                                                                                                                                                                                                                                                         | Action                                                                                                                          |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **DeFi end-to-end pipeline**     | `defi_master_2026_05_07` (umbrella post-2026-05-07 Stage 7 consolidation)                                                                    | `defi_e2e_pipeline_2026_04_30` · `defi_pipeline_extension_2026_05_01` · `leveraged_leg_controller_2026_05_01` · `carry_staked_basis_structure_axis_2026_05_04` (all archived 2026-05-07) · `consolidated_defi_data_pipeline_2026_04_15` (residuals) · `defi_data_types_completeness_2026_04_24` (residuals) | Surface only the lead on master plan; track children as sub-bullets. Archive `defi_full_coverage_expansion_2026_04_09`.         |
| **Write-gate / honest-coverage** | `writegate_honest_coverage_endtoend_2026_05_06` (umbrella; declares `supersedes_phases:` on shard-granularity Tier 1 #1 + Tier 2 raw-tables) | `shard_granularity_ssot_propagation_2026_05_06.HANDOVER` · `data_status_multi_axis_shard_propagation_2026_05_06` · `feature_dag_uac_ssot_and_features_coverage_2026_05_06` · `predictions_canonical_question_group_polymarket_migration_2026_05_06`                                                         | Re-tag children with `role: child` / `parent: writegate_…`; surface only the umbrella.                                          |
| **Sports phantom recovery**      | `sports_fixtures_truthset_recovery_2026_05_06` (active executor; declares `supersedes_phases:` on phantom-recovery relaunch + audit-flip)    | `sports_phantom_fixtures_recovery_2026_05_06` · `sports_phantom_recon_and_failure_triage_2026_05_01` (diagnostic context)                                                                                                                                                                                   | Surface only truthset; the others are background.                                                                               |
| **Strategy v2 finalization**     | `strategy_architecture_v2_finalization_2026_04_19` (live, supersedes `strategy_architecture_v2_2026_04_17`)                                  | `strategy_architecture_v2_phase3_11_handoff_2026_04_17` (historical, Phase 2 done)                                                                                                                                                                                                                          | Surface only finalization; mark handoff `parent_of: finalization`.                                                              |
| **DART terminal / cockpit**      | `dart_ux_cockpit_refactor_2026_04_29` (active superset; supersedes codex `14-playbooks/dart/dart-terminal-vs-research.md`)                   | `dart_terminal_research_split_2026_04_28` (mechanics shipped)                                                                                                                                                                                                                                               | Archive terminal-research-split.                                                                                                |
| **Marketing site**               | `marketing_site_three_route_consolidation_2026_04_26`                                                                                        | `marketing_homepage_old_hero_migration_2026_04_22` (homepage scope within route-consolidation) · `dart_ui_strategy_filtering_and_onboarding_2026_04_24` (self-tagged superseded)                                                                                                                            | Archive DART UI plan; reference homepage as scope-of route-consolidation.                                                       |
| **Sports roadmap**               | `sports_roadmap_master_execution_2026_04_21` (10-plan parallel-execution master)                                                             | 4 explicit children (apifootball_enrichment_historical_backfill · non_apifootball_provider_backfill_launchers · features_sports_pipeline_deployment · sports_scheduler_cron_activation, all 2026-04-21)                                                                                                     | Surface master only; reconcile overlap with `sports_predictions_e2e_2026_05_05` + `features_sports_honest_coverage_2026_05_05`. |
| **Playbook SSOT**                | `playbook_ssot_stage_3_infra_spec_2026_04_19`                                                                                                | `_stage_2_doc_rewrite_2026_04_19` · `_stage_1_rules_2026_04_19` (correctly modeled with `depends_on` / `blocks`)                                                                                                                                                                                            | Surface as one playbook-SSOT cluster.                                                                                           |
| **Asset-group vocabulary**       | `venue_axis_asset_group_vocabulary_2026_04_25` (parent)                                                                                      | `shard_dimension_naming_asset_group_ssot_2026_04_25` (declares "complements")                                                                                                                                                                                                                               | **Merge** or formal child link.                                                                                                 |

### Self-tagged superseded plans (18) — archive with `[unlock-plan]`

All have `superseded_by:` declared in frontmatter but still sit in `active/`:

`client_config_and_defi_risk_2026_04_01` · `cross_domain_alpha_execution_intelligence_2026_04_11` ·
`strategy_lifecycle_visibility_ui_2026_04_11` · `ui_walkthrough_and_e2e_alignment_2026_04_01` ·
`dart_ui_strategy_filtering_and_onboarding_2026_04_24` · `ml_pipeline_revolution_2026_04_11` ·
`domain_agnostic_ml_framework_2026_04_11` · `defi_instrument_pipeline_and_rewards_2026_04_01` ·
`mev_protection_and_execution_enhancements_2026_04_01` · `manual_trade_booking_reconciliation_2026_03_22` ·
`unified_pipeline_scheduling_and_triggers_2026_04_15` · `remove_data_types_field_2026_04_10` ·
`polymarket_prediction_pipeline_2026_03_25` · `smoke_dep_chain_tactical_fixes_2026_04_20` ·
`instruments_service_template_refactor_8e653acc` · `availability_manifest_v4_and_data_status_2026_04_13` (manifest now
v6) · `defi_pipeline_extension_followups_2026_05_03` (`status: complete`) ·
`dashboard_services_grid_collapse_2026_04_21` (88% done, awaiting unlock).

### Other stale / drift findings

- **`signal_leasing_broadcast_architecture_2026_04_20`** — 8 phases all complete
  (`reconciliation_status: shipped_substantive`), awaiting human `[unlock-plan]`.
- **`venue_availability_ssot_2026_03_25`** — 88% done; either archive or extract 3 polish items into a small follow-up.
- **`hybrid_sampler_5s_resolution_2026_03_30`** — `orphan_candidate: true`, stalled since pivot to manifest+rescan. Move
  to ICEBOX.
- **`mempool_feed_integration_2026_06_01`** — `status: paused`, future-dated. Remove from `active/`-as-current.
- **Dangling `superseded_by` references:** `polymarket_prediction_pipeline_2026_03_25` points at
  `consolidated_sports_prediction_pipeline_2026_04_15` which isn't in `active/` (likely archived) — update to point at
  `predictions_canonical_question_group_polymarket_migration_2026_05_06`. `defi_strategies_phase2_2026_03_29`
  `depends_on:` `defi-instrument-pipeline-and-rewards` (itself superseded → transitively dangling).
- **Removed-providers references** (Elysium / Bloxroute / Arkham / Pyth / Infura) appear in technical scope of
  `consolidated_defi_data_pipeline_2026_04_15`, `mev_protection_and_execution_enhancements_2026_04_01`,
  `mempool_feed_integration_2026_06_01` — scrub or archive.

### Frontmatter discipline (systemic)

| Issue                                           | Count |
| ----------------------------------------------- | ----: |
| Plans with NO frontmatter at all                |     5 |
| Plans missing `locked_by`                       |    31 |
| Plans missing `name` field                      |    11 |
| Plans missing `last_updated` (95%)              |   140 |
| `superseded_by` set but plan still in `active/` |    18 |
| Filename ↔ `name` field mismatch               |     1 |
| YAML errors                                     |     2 |

**Action:** workspace-wide one-shot backfill script — populate `last_updated` from `git log` mtime, infer `asset_group`
from filename + body, populate `locked_by: live-defi-rollout` for any that are mid-flight. **Work-stream G below.**

### Service-overlap concentration (>5 active plans = consolidation candidate)

| Service                   | Active plans touching it |
| ------------------------- | -----------------------: |
| instruments-service       |                **35** ⚠ |
| deployment-service        |                    16 ⚠ |
| strategy-service          |                    16 ⚠ |
| deployment-api            |                    16 ⚠ |
| unified-trading-system-ui |                    12 ⚠ |
| execution-service         |                    12 ⚠ |
| deployment-ui             |                    12 ⚠ |
| market-tick-data-service  |                    10 ⚠ |

Eight services with >5 active plans = real overlap risk. The `instruments-service` 35-plan count is the clearest
consolidation target post-cutover.

---

## Q&A — resolved (✓) and outstanding (?)

1. ✓ **Lead DeFi archetypes — both `carry_staked_basis` (ultimate priority) AND `leveraged_funding_arb` (cross-venue
   funding spread) by May 23.** Recursive LST staking is part of the carry_staked_basis archetype. Linked plans:
   `carry_staked_basis_structure_axis_2026_05_04` and `defi_master_2026_05_07` (umbrella that folds in
   `defi_pipeline_extension_2026_05_01` + `leveraged_leg_controller_2026_05_01` + `defi_e2e_pipeline_2026_04_30` per the
   2026-05-07 consolidation).
2. ✓ **CeFi/DeFi perp venue scope — six venues live: Bybit, Deribit, Binance, OKX, Hyperliquid, Aster.** Hyperliquid +
   Aster are DeFi perp DEXs but live alongside the CeFi venues. CEFFU manual handoff acceptable for Binance flows on
   May 23.
3. ✓ **Custody scope — Copper wired for DeFi side; CEFFU manual for Binance side acceptable.** Codex SSOT exists for
   Copper; CEFFU doc is a gap (work-stream F).
4. ✓ **AWS proof scope — full cloud-parity proof:** (a) cost analysis of GCS data → estimate AWS migration cost; (b)
   migrate only DeFi-relevant data (not full corpus); (c) data-status working on AWS; (d) backfill on AWS with `--force`
   (proves batch deployment side); (e) backtest examples runnable on AWS; (f) ML strategy examples runnable on AWS; (g)
   **live trading deployment + monitoring on AWS** so the team can seamlessly switch any deployment between AWS-live /
   AWS-batch / GCP-live / GCP-batch. Reduces, but does not eliminate, the May 23 risk surface — see _Risk register_
   below.
5. ✓ **Manual-trade gating duration — RESOLVED 2026-05-08.** Default confirmed: **3 days manual → 7 days automated**,
   with kill-switch monitoring throughout. Day 1-3 = DART operator manually executes every trade signal generated by
   strategy-service (one-click confirm, no auto-fire); Day 4-10 = automation enabled, kill-switch + DART pause/override
   armed throughout; ≥7 continuous days automated = May-23 acceptance criterion. Applies to both DeFi archetypes
   (`carry_staked_basis` + `leveraged_funding_arb`) and to CeFi-ML (`ML_DIRECTIONAL_CONTINUOUS`) per Q&A 7. Stagger by
   ≥1 day across archetypes to isolate kill-switch tests. `strategy_and_dart_master:Phase 2.2` Playwright matrix is the
   acceptance gate. See `plans/active/operator_decisions_2026_05_08.md` for the full pickup record.
6. ✓ **research-service repo decision — RESOLVED 2026-05-08.** **Fold into deployment-api** for May 23 scope. Scope is
   contained: operator research views consume existing deployment-api / data-status / coverage endpoints; no new domain
   contracts; no new persistence layer. Re-evaluate post-cutover only if scope grows beyond a `/research/*` route group
   on deployment-api. No new repo, no new Cloud Run service, no new IAM surface this cycle.
7. ✓ **ML ladder targets per asset group by May 23 — RESOLVED 2026-05-08.** Per asset_group:
   - **Prediction**: features-only running batch end-to-end. NO live deployment.
   - **Sports**: ML pipeline RUNNING on representative sample. NO live deployment. Backtest-only deliverable.
   - **TradFi**: ML pipeline RUNNING on representative sample (S&P swing-prediction trains end-to-end on 2-year
     history). NO live deployment. Backtest-only.
   - **CeFi → DEPLOYED IN PRODUCTION on real capital ≥7 days.** Archetype: `ML_DIRECTIONAL_CONTINUOUS` (continuous
     directional prediction signal). Venues: OKX + Binance + Bybit (3 venues, deepest liquidity, lowest unit cost).
     Retraining cadence: **daily** (overnight retrain via ml-training; ml-inference hot-reload on next day open).
     Capital scale: **starting allocation $10k notional per venue ($30k total)**, Kelly-fraction sized per archetype
     `ArchetypeConfig.position_cap_usd`; ramp 2× per week absent kill-switch trips, capped at $250k notional total by
     post-cutover review. `ArchetypeConfig.kill_switch_drawdown_pct=5` and `kill_switch_position_breach_pct=20` applied;
     `kill_switch_scope=ARCHETYPE` so a CeFi-ML trip does NOT halt DeFi (and vice versa).
   - **DeFi**: rules-based (no ML this cycle). `carry_staked_basis` + `leveraged_funding_arb` deployed live ≥7 days per
     Q&A 1 + Q&A 5.

   Implication: `mlr-p4-strategy-calibrated-signals` + `mlr-p4-cost-aware-strategy` + live model registry / hot-reload /
   per-trade `model_version` tagging are P0 May-23-blockers (was P1 under "running" default). `ml_and_features_master`
   Phase 4D becomes hard-floor live-trading prerequisite, not just sports/predictions enablement.

8. ? **Plan location.** Default: PM `plans/active/master_to_live_defi_2026_05_23.plan.md` (sub-plan) **and**
   `codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md` (audit / SSOT companion), with the audit doc cross-linked
   from `CLAUDE.md` so it's loaded into agent context every session.
9. ✓ **Pyth oracle ban — REVERSED 2026-05-06 for Solana-only scope.** `carry_staked_basis` LST yields (jitoSOL / mSOL /
   bSOL) need on-chain Solana prices; Chainlink covers EVM only (Arb / Base / Polygon); no viable Switchboard wiring in
   workspace. Pyth via Hermes (HTTPS pull, batch) + PythNet (Solana RPC, live). Other chains continue Chainlink.
   CLAUDE.md "Removed providers" updated; `consolidated_defi_data_pipeline_2026_04_15` `mtds-s3-5-pyth-oracle` todo
   unblocked.
10. ✓ **MDPS vs MTDS in data-status — separate services, separate rows (current architecture).** Each has its own
    `SHARD_AXIS_MATRIX` entry, own bucket, own manifest; no double-representation. UI rollup ("raw ticks 99% / processed
    candles 95%" under one asset_group view) is a deployment-UI enhancement deferred to post-cutover work-stream
    B-adjacent.
11. ✓ **Cluster validation wiring (writegate Phase 1A Amendment F) — REVISED 2026-05-06 after MTDS re-read: ALREADY
    SHIPPED for ES.OPT.** `engine/orchestrator.py:2126-2193` already gates `writer_manifest.add()` for ES.OPT bundles
    via the hardcoded `venue_name == "CME-OPTIONS"` branch using `get_active_es_options_clusters_for_date_from_snapshot`
    - `ManifestWriter.check_cluster_coverage_from_counts`. The "wrap with `if data_type in BUNDLED_DATA_TYPES:`" framing
      is the **generalisation** to non-CME-OPTIONS bundles (futures_chain / prediction_canonical_question_group /
      sports_fixture_bundle), which is deferred until those bundle adapters exist. Phase 2.B for ES.OPT is **DONE**;
      Phase 2.B generalisation kicks in when a 2nd bundle data_type ships.
12. ✓ **`ES_OPTIONS_CLUSTERS` rename — REVISED 2026-05-06 after re-read: NO RENAME NEEDED.** Earlier proposal to make it
    generic `OPTIONS_CLUSTERS_BY_ROOT` was a misread of the architecture. The 11-cluster ES taxonomy is genuinely
    ES-specific — driven by CME futures symbology regex which differs from Deribit BTC options (`BTC-30JUN24-50000-C`),
    Solana DEX options, etc. Each future root needs its own extractor + cluster taxonomy
    - active-calendar logic. Current symbol naming (`ES_OPTIONS_CLUSTERS`, `extract_es_options_cluster`,
      `get_active_es_options_clusters_for_date`) is correctly scoped. When a 2nd root ships, the pattern is **sibling
      symbols** (`DERIBIT_BTC_OPTIONS_CLUSTERS` + `extract_deribit_btc_options_cluster`) plus a per-(data_type, root)
      lookup, NOT a rename of the existing symbols.
13. ✓ **VIX 15m source layering — `cefi_tradfi_tick_data_backfill_2026_04_10` Phase 3b OBSOLETE.** Plan A's Barchart VM
    for `2025-11-13 → today` would clobber Yahoo-served rows. CLAUDE.md "VIX 15m source layering" SSOT + MTDS `4a2747a`
    are canonical: Barchart preload ends 2025-11-12; post-cutoff is Yahoo Finance rolling 60-day window;
    `2025-11-13 → today−60d` is the honest gap (`empty_confirmed`). Phase 3b dropped.
14. ✓ **Sports `data_available_at` → `available_at` rename + on-disk migration.** UTL `assert_available_at_present` +
    every other service uses canonical `available_at`. Sports adapters + `InstrumentsWriteGate.DEFAULT_AS_OF_COLUMNS`
    rename to `available_at` + one-time GCS column rename in existing sports parquets (per "manifest migration not
    fallback" rule). Required before writegate Phase 2.C / `LookaheadBiasError` strict-mode flip — otherwise sports
    pipeline hard-fails on every record_captured call. **Dedicated plan shipped 2026-05-07**:
    [`plans/active/sports_data_available_at_rename_2026_05_07.plan.md`](../archive/sports_data_available_at_rename_2026_05_07.plan.md).
    Pre-audit complete (35+ callsites enumerated across UAC / UTL / instruments-service / features-sports). 4-phase DAG:
    Phase 0 audit (shipped) → Phase 1 migration script (next concrete agent task) → Phase 2 operator-runs-migration
    (same-region GCE VM, paused FWD/BACKFILL VMs) → Phase 3 atomic 4-repo source rename → Phase 4 writegate Phase 2.C
    unblock + verify.
15. ✓ **`_create_full_day_empty_output` delete (writegate Phase 2.A) — Option A: audit consumers, delete iff safe.**
    Empty/closed days use `record_empty(capture_status=empty_confirmed)` per existing SSOT — placeholder rows are
    double-SSOT. Downstream services NaN-handle their own way (forward-fill, masking, ML missing-data tolerance).
    **Codex follow-up doc**: "empty upstream means no expectation of data downstream; manifest `empty_confirmed` is the
    SSOT, NOT placeholder rows. Holidays + market hours via `venue_trading_calendar`; unexpected empties handled
    per-service in pre-flight." Block writegate Phase 2.A on grep audit of features-volatility / features-cross-
    instrument for `market_state == "CLOSED"` consumers; refactor any to read manifest `capture_status` instead. **A2
    audit shipped 2026-05-07** (commit `7d8ce330` codex doc; writegate plan re-categorisation): codex SSOT
    `codex/02-data/honest-absence-downstream-handling.md` codifies the principle. Audit ruling:
    `_create_full_day_empty_output` in `tradfi/ohlcv_passthrough.py:266` re-categorised from `?` to **A (honest
    absence)**; sibling banned method `_create_closed_market_candle` in `orchestration_writer.py:65`
    (1-row-per-non-trading-day variant) added to same delete scope. Two consumers (`features-volatility-service` +
    `features-delta-one-service` `_filter_market_state`) have legitimate intra-day filter purpose (`pre_market` /
    `post_market` / `closed` minutes from `_apply_market_state` on real trading days) — those filters STAY;
    placeholder-row drop role disappears once delete-and-replace ships. Consumer refactor: add manifest pre-flight gate
    (skip `empty_confirmed` days at parquet-load time). Code change folded into writegate Phase 2.A scope (already
    covers 37 `_create_empty_output` callsites + 3-write-path consolidation); A2 deliverable is the audit ruling that
    resolves the writegate plan's open `?` entry, not a separate commit.
16. ✓ **Sports `fixture_id` shard atom (writegate HANDOVER vs multi-axis plan) — multi-axis plan wins; `fixture_id` is
    NOT a shard atom.** `(league_id, day)` already bounds fixtures; per-fixture detail comes from parquet at drill-down
    time. HANDOVER per-asset-group matrix updated; features-sports audit reframes to `(feature_group, league_id, day)`.

---

## Risk register (post-Q&A scope expansion)

The answers expanded scope materially. Risks to flag explicitly so they're not silently signed off:

| Risk                                                    | Likelihood                             | Impact                                                                                          | Mitigation                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 6 perp venues live by May 23 (was 2)                    | High                                   | Slips one or more archetypes                                                                    | Sequence: Bybit + Hyperliquid first (Week 2 W1), Deribit + Binance + OKX + Aster fast-follow (Week 2 W2). Carry_staked_basis only strictly needs 1 perp venue; leveraged funding arb wants ≥3 for cross-venue spreads.                                                                                                                                                            |
| 2 archetypes live by May 23 (was 1)                     | High                                   | Slips leveraged_funding_arb                                                                     | Carry_staked_basis stays the cutover gate; leveraged_funding_arb can flip from manual-DART to automated within the 7-day window if Week 3 is tight.                                                                                                                                                                                                                               |
| Full AWS cloud parity by May 23                         | High                                   | Slips AWS or DeFi cutover                                                                       | AWS data migration + batch backfill + data-status earliest (Week 1 W2 → Week 2 W1). AWS live trading proof is "single archetype on smaller capital" — does not need full archetype scale.                                                                                                                                                                                         |
| 5 NO-PLAN live-mode services to write + ship            | Medium                                 | Live trading without circuit breakers / live alerting / batch-vs-live recon = unsafe to flip    | RESOLVED post-2026-05-06 audit: only `alerting-service` is genuinely NO-PLAN; PBM / R&E / pnl-attribution extend `defi_master_2026_05_07` Fork 1 (folds `defi_e2e_pipeline_2026_04_30` per Stage 7 consolidation); B-vs-L recon extends `consolidated_operational_validation_2026_04_15` (work-stream E REVISED).                                                                 |
| CEFFU integration unwritten                             | Low                                    | Forces all-manual Binance flows                                                                 | Manual is acceptable per Q&A 3; codify in plan + add CEFFU codex doc.                                                                                                                                                                                                                                                                                                             |
| DART manual-trade lane is new code on the critical path | Medium                                 | Slips Group G on tier-1 strategy / execution                                                    | Build on the strategy-evaluations + VmDeployments tracker patterns already in UTS-UI / deployment-ui — **no greenfield UI**.                                                                                                                                                                                                                                                      |
| Pyth ban left Solana on-chain prices unimplemented      | Medium                                 | Blocks LST yield tracking for jitoSOL / mSOL / bSOL — direct dependency of `carry_staked_basis` | RESOLVED 2026-05-06: Pyth unbanned for Solana-only scope (Q&A 9). Chainlink continues for EVM. Wire Hermes + PythNet via existing `oracle_prices_handler.py`.                                                                                                                                                                                                                     |
| `check_shard_freshness` ignores `capture_status`        | **RESOLVED 2026-05-06 (UTL@ba83a6f1)** | n/a — fix shipped                                                                               | UTL `check_shard_freshness` extended with `retry_failed: bool = True` param (default-on); `ATTEMPTED_FAILED` rows now treated as stale. DELETE workaround in `sports_fixtures_truthset_recovery` is now optional; `phantom_recon_and_failure_triage` Phase 1 flip-to-attempted_failed works as designed. 8 unit tests in `tests/unit/test_check_shard_freshness_retry_failed.py`. |

---

## Asset-group readiness ladder (critical-path orientation)

Per user direction: stage each asset_group up to a specific layer by May 23. DeFi must reach "live trading"; the others
stage to a parallel-but-deeper level so post-DeFi archetype launches are quick.

| Asset group    | May 23 target depth                                     | Live perp venues             | Notes                                                                                            |
| -------------- | ------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------ |
| **DeFi**       | **Live trading on real wallet (rules-based, no ML)**    | Hyperliquid, Aster           | 2 archetypes (carry_staked_basis lead + leveraged_funding_arb); LST + lending + perp-DEX legs    |
| **CeFi**       | **Live trading (perp hedge leg) + ML pipeline running** | Bybit, Deribit, Binance, OKX | Hedge for DeFi archetypes today; CeFi-only archetypes (e.g. funding-arb-CeFi-only) ready post-23 |
| **TradFi**     | **ML pipeline running on representative sample**        | n/a (no live)                | Backfill ~99%; ML training on rep sample; no live trading this cycle                             |
| **Sports**     | **ML pipeline running on representative sample**        | n/a (no live)                | Honest-coverage + phantom recovery close-outs land first                                         |
| **Prediction** | **Features pipeline running (no ML this cycle)**        | n/a (no live)                | Polymarket canonical-question-group migration is the gate                                        |

---

## Per-service readiness checklist — 7 groups / 23 items

Status legend: `✓` done · `◐` in flight · `✗` not started · `n/a` not applicable

### Group A — Code health (always-on)

1. **QG pass** — `bash scripts/quality-gates.sh` two-pass clean (full + quickmerge)
2. **Quickmerge** — branch landed `live-defi-rollout` → main via SIT
3. **Semver agent** — `feat:` / `fix:` / `feat!:` triggers version bump

### Group B — Data correctness (always-on)

> **2026-05-07:** writegate Phase 3.D.4 expected-universe `--apply-write` COMPLETE across all 5 asset_groups +
> CONSOLIDATOR MERGE LANDED (deployment-service@dcc5c87 / @38b7a58 + instruments-service@8e404c8 / @d1c9928 / @a936a28
>
> - UAC@ac218dc; PM@79e47874 + PM@341bb285). 1,455,901 rows written + merged into canonical 18:07-18:14 UTC (TradFi
>   35,033 + Sports 13,176 + CeFi 119,152 real impl + Prediction 2,280 real impl + DeFi 1,286,260). Consolidator P0
>   (`ArrowTypeError` on `instrument_count`) was briefly blocking tradfi / defi / prediction; resolved at PM@341bb285
>   (script-side root cause + 4 in-place shard fixes). Rollup-vs-drilldown denominator gap closure now observable on all
>   5 asset_groups; operator spot-check pending. Detail in
>   [`writegate_honest_coverage_endtoend_2026_05_06.plan.md`](writegate_honest_coverage_endtoend_2026_05_06.md) § Phase
>   3.D.4.

4. **Smoke test** — representative `(asset_group, data_type, day)` triples produce valid parquet end-to-end
5. **Manifest hookup + cluster validation** — `ManifestWriter.record_{captured,empty,failed}` with
   `expected_root_clusters` + `cluster_extractor` for bundled types (codex
   `02-data/availability-manifest-and-data-status.md`, UTL `61a142b0`)
6. **Upstream validation** — `DependencyError(fail_fast=True)` at boundary; honest absence categories A/B/C; no silent
   placeholder rows (CLAUDE.md "honest absence vs fake placeholders")
7. **UAC/UTL abstraction** — domain types in UAC, runtime utilities in UTL, only service-specific config inline
8. **Schema validation** — parquet schema matches UAC contract per `record_captured` (4-pillar write-gate item 3)

### Group C — Runtime parity (always-on)

9. **Hot reload** — `start_domain_config_reloaders` typed; `ApiKeyReloader` for Secret Manager creds (codex
   `06-coding-standards/config-reloader-pattern.md`)
10. **Batch = live** — same code path; only fill source differs (codex `04-architecture/batch-live-pipeline.md`,
    `batch-live-symmetry.md`)
11. **AWS + GCP parity** — both VM launch paths green; `CLOUD_PROVIDER` toggle works end-to-end (codex
    `04-architecture/cloud-agnostic-migration.md`)

### Group D — Coverage & shard (always-on, data-producing services)

12. **Data status accurate** — deployment-UI rollup matches on-disk truth-set; canonical shard axis per asset-group
13. **Shard granularity correct** — matches codex `02-data/availability-manifest-and-data-status.md` per-asset-group
    matrix
14. **Full-window backfill** — ≥2 years of representative history captured (per CLAUDE.md "honest absence" + codex
    `02-data/per-category-bucket-layouts.md`); n/a for runtime-only services

### Group E — Operability (always-on)

15. **UTS-UI summary** — service surfaces visible in unified-trading-system-ui where relevant (`/ops/admin/...` route
    exists or is in scope)
16. **Deployment-UI launch + GCS log streaming** — backfill / restart / forward-poll launchable from UI without SSH; VM
    event logs pooled to `gs://{pid}-events/`; tail works without SSH

### Group F — Trading prerequisites (live-only services)

> **🟢 LIVE-PIPELINE ACTIVATION 2026-05-08** — Three new plans landed 2026-05-08 cover the live-mode portion of Group F
> items 21 (Reconciliation suite) + 22 (Trading guardrails) for MTDS / MDPS / features-service:
> [`live_pipeline_mtds_mdps_features_2026_05_08`](./live_pipeline_mtds_mdps_features_2026_05_08.md) (main activation,
> 10d), [`features_repo_consolidation_2026_05_08`](./features_repo_consolidation_2026_05_08.md) (pre-req, merges 8
> features-\* repos into one features-service, 3-5d), and
> [`gcs_migration_bundle_pipeline_mode_2026_05_08`](./gcs_migration_bundle_pipeline_mode_2026_05_08.md) (bundled
> overnight GCS migration: pipeline_mode partition + category=→asset_group= rekey + drift cleanup). Codex entry:
> [`codex/05-infrastructure/live-pipeline-architecture.md`](../../codex/05-infrastructure/live-pipeline-architecture.md).
> Sequencing: features-repo Phase 7 + gcs-bundle Phase 9 BLOCK live-pipeline Phase 3+5 respectively.

17. **Backtest fidelity** — real gas, real market impact, realistic matching engine for AMM pools / perpetuals / spots /
    transfers / atomic transfers / flash loans; cost+yield to smallest precision (codex
    `04-architecture/backtest-groups.md`, `batch-live-symmetry.md`). **Deep audit 2026-05-07**: shipped matching engine
    has 5 matcher classes (L0 Sports TOB, L1 TradFi, L2 CeFi, AMM, ALPHA_ZERO benchmark fills) at
    `execution-service/execution_service/matching_engine/`. "Transfers" + "atomic transfers" are NOT separate matcher
    classes — they're swap/settlement modes within the AMM matcher. Either fold transfers into the AMM matcher's scope
    statement (current shipped reality) or open a follow-up to add a Transfers matcher (low-likelihood given DeFi
    transfers are atomic-by-default on-chain). Recommend folding into AMM matcher scope.
18. **2-year batch backtest run** — completed across config grid; P&L variance per archetype configuration captured so
    the live-trading config is informed, not guessed. **Deep audit 2026-05-07**: no dedicated 2-year batch backtest
    runner script found. `strategy-service/scripts/` has `trace_carry_staked_basis.py` + `trace_all_carry_archetypes.py`
    (May 5+7) — tracing/simulation, not config-grid sweep. P0 follow-up: author
    `strategy-service/scripts/run_2yr_config_grid_backtest.py` for `carry_staked_basis` + `leveraged_funding_arb`
    archetypes; emit P&L variance distribution per archetype config dimension.
19. **Treasury / custody integration** — Copper for DeFi side; CEFFU for Binance institutional flow; cross-wallet
    transfer paths verified. Single SSOT: `codex/04-architecture/custody-providers.md` (folded 2026-05-08, replaces the
    former per-provider docs). **Deep audit 2026-05-07 / merged 2026-05-08**: Copper section is full; CEFFU section is
    STUB with PENDING subsections. P0 follow-up tracked under work-stream F (populate CEFFU subsections inside
    `codex/04-architecture/custody-providers.md`).
20. **Live testnet replicates prod** — Tenderly fork / forked-mainnet for DeFi; Binance testnet / Bybit testnet for
    CeFi; same config code path, no faked data. **Deep audit 2026-05-07**: no testnet-specific branch paths or env
    toggles found in execution-service yet. Per-venue testnet wiring pending — verify each connector's testnet endpoint
    list before live cutover. Tenderly fork fixtures shipped per `execution-service/tests/integration/conftest.py` (per
    `CLAUDE.md` "DeFi integration tests" rule) — DeFi side has the testbed, CeFi side has not been validated end-to-end.
21. **Reconciliation suite** — batch-vs-live reconciliation working (codex
    `09-strategy/cross-cutting/pnl-attribution.md` + `batch-live-reconciliation-service`); P&L attribution decomposed
    per source; per-trade reconciliation. **Deep audit 2026-05-07**: pnl-attribution-service ships `--mode batch` CLI
    (verified at `pnl-attribution-service/pnl_attribution_service/__main__.py:288` + `cli/parser.py`). However,
    `batch-live-reconciliation-service` A column = ✗ in the matrix below (service scaffolded but NOT code-complete).
    Phase 2.E.3 of writegate plan + this Group F item depend on the service being shipped. P0 follow-up: ship the
    minimum-viable reconciliation surface (per-archetype P&L diff, per-trade fill comparison) before May-23 cutover.
22. **Trading guardrails** — circuit breakers configured per archetype; kill switches wired (codex
    `04-architecture/autonomous-recovery-matrix.md`); alerting-service rules cover live data-freshness + P&L deviation +
    position breaches (codex `04-architecture/alerting-batch-live.md`); auto-recovery for known transient failure
    classes. **Tab 5 (Agent 5) cycle 2026-05-08 progress** (refresh from 2026-05-07 baseline): Phase 2 service migration
    SHIPPED (alerting-service@`b025e83` consumes UAC `LIVE_ALERT_RULES`); Phase 3 envelope `code: AlertCode` field
    SHIPPED (UAC@`2636815` Option A) + 3-service consumer migration (execution-service@`624c36a8` yield_recon +
    funding_recon, position-balance-monitor@`d206ab3` reconciliation_engine + fee_recon, risk-and-exposure@`915f0de`
    RiskMonitor); Phase 6 15 per-AlertCode operator runbooks SHIPPED (PM@`45b854d5`+`6fad278e`+`db99a3ef`+`b40d405a`+
    `ac40983b`); Phase 5 DART Active Alerts panel + per-alert detail modal + severity widget + Playwright ack-flow
    SHIPPED (unified-trading-system-ui@`e9559565`); Phase 2 KillSwitchBus publisher hook + per-event scope
    (GLOBAL/VENUE/ARCHETYPE) SHIPPED (UAC@`3793310`+`2541a47` field; alerting-service@`8eda37c` hook + 5 integration
    tests); CeFi ML lifecycle alert codes SHIPPED (UAC@`6c4784f` — 6 ML codes + 5 ML thresholds + 6 ML rules). Group F
    item 22 column flipped ✗ → ◐. **Pending**: Phase 4 paging-target Secret Manager wiring (operator-driven); Phase 7
    quietness baseline 48h staging dry-run (operator-driven); Phase 8 live rehearsal (operator-driven); Phase 9 go-live
    on 2026-05-23 (operator-driven). features-onchain emission sites for `DEFI_HEALTH_FACTOR_CRITICAL` /
    `DEFI_AAVE_UTILIZATION_SPIKE` / `DEFI_FUNDING_RATE_FLIP` / `DEFI_FEATURE_STALE` / `DEFI_WEETH_DEPEG` deferred per
    Sub-B finding (calculators not yet wired; defi_master Fork 1 territory).

#### Folded operational-validation todos (from `consolidated_operational_validation_2026_04_15`)

These 11 todos were folded in 2026-05-07 from `consolidated_operational_validation_2026_04_15` (now archived). They
extend items 17–22 with concrete operational-validation work — pipeline scheduling completeness, per-cluster E2E
batch-vs-live reconciliation, and final infra QG sweeps — that gates `master Group F` closure.

**Pipeline scheduling remaining code** (extends items 21–22 — live-trading scheduler + trigger backend):

- [ ] [AGENT] P1. `ups-p2-run-tag-mtds-calendar`: Wire `--run-tag` into MTDS GCS output path + features-calendar-service
      (PARTIALLY*DONE — CLI flag exists at MTDS `cli/main.py:288`; needs threading into GCS output path templates +
      features-calendar adoption). Not on May-23 critical path. *(folded from
      consolidated*operational_validation_2026_04_15)*
- [ ] [AGENT] P1. `ups-p4-sports-trigger-backend-dispatch`: Sports trigger scheduler cloud backend dispatch
      (PARTIALLY*DONE — local subprocess works, cloud placeholder). Confirmed at deployment-service
      `deployment_service/sports_trigger_periodic.py` + `sports_trigger_scheduler.py` + `sports_trigger_state.py`;
      cloud-dispatch shim is the named gap. *(folded from consolidated*operational_validation_2026_04_15)*

**E2E cluster tests** (extends item 21 — batch-vs-live reconciliation per cluster):

- [ ] [HUMAN+AGENT] P0. `ups-p8-e2e-cefi`: E2E test — CEFI cluster (T+1, live 1h, reconciliation). BLOCKED-ON
      `cefi_master_2026_05_07` + writegate Tier 2C cefi adapters (shipped at MDPS@b9f9328); cefi cluster YAML exists at
      deployment-service `configs/clusters/cefi.yaml`. _(folded from consolidated_operational_validation_2026_04_15)_
- [ ] [HUMAN+AGENT] P0. `ups-p8-e2e-sports`: E2E test — SPORTS cluster (T+1, trigger scheduler, feature validation).
      BLOCKED-ON `sports_master_2026_05_07`; writegate Tier 2A sports adapters shipped at MDPS@5b52d0b; trigger
      scheduler shipped at deployment-service `sports_trigger_*` (cloud-dispatch placeholder per `ups-p4` above).
      _(folded from consolidated_operational_validation_2026_04_15)_
- [ ] [HUMAN+AGENT] P0. `ups-p8-e2e-defi`: E2E test — DEFI cluster (T+1 single day). BLOCKED-ON `defi_master_2026_05_07`
      (umbrella for all DEFI work). _(folded from consolidated_operational_validation_2026_04_15)_
- [ ] [HUMAN+AGENT] P0. `ups-p8-e2e-tradfi`: E2E test — TRADFI cluster (T+1 single day, needs `DATABENTO_API_KEY`).
      BLOCKED-ON `tradfi_master_2026_05_07`; writegate Tier 2E tradfi adapters shipped at MDPS@e9520a0;
      `DATABENTO_API_KEY` presence is the human-side credential gate. _(folded from
      consolidated_operational_validation_2026_04_15)_
- [ ] [HUMAN+AGENT] P0. `ups-p8-e2e-prediction`: E2E test — PREDICTION cluster (T+1 single day). BLOCKED-ON
      `predictions_master_2026_05_07` (canonical*question_group migration in flight). *(folded from
      consolidated*operational_validation_2026_04_15)*
- [ ] [HUMAN+AGENT] P0. `ups-p8-e2e-full`: E2E test — FULL cluster (all categories for 1 date). BLOCKED-ON the 5
      preceding per-cluster e2e tests. _(folded from consolidated_operational_validation_2026_04_15)_

**Infrastructure cleanup** (extends item 22 — final QG sweep before live cutover):

- [ ] [HUMAN] P1. `rdt-p4-gcs-cleanup`: Run instruments-service backfill to regenerate parquet without `data_types`
      column. instruments-service production code grep for `data_types` returns 0 hits; references remain only in legacy
      ETL scripts (`scripts/aggregate_legacy_es_opt_trades.py`) and test code. Remaining work is GCS cleanup of legacy
      parquets that still carry the column — operator-driven backfill rerun. _(folded from
      consolidated_operational_validation_2026_04_15)_
- [ ] [AGENT] P1. `rdt-p4-workspace-qg`: Run `quality-gates.sh` on all 5 affected repos. Depends on the GCS cleanup
      above to validate the column removal. _(folded from consolidated_operational_validation_2026_04_15)_
- [ ] [AGENT] P1. `mtb-p6e-final-qg-sweep`: Full QG sweep across all 6 affected repos. Final QG gate; depends on every
      preceding "qg" item plus the cluster e2e tests being passable on a representative day's data. _(folded from
      consolidated_operational_validation_2026_04_15)_

### Group G — Operator UX (live-only)

23. **DART manual-trade gate** — DART terminal in UTS-UI visualizes the strategy archetype end-to-end; operator first
    puts trades on manually → backend executes through the same path as automation → monitor for the gate window → flip
    switch to automation (codex `09-strategy/cross-cutting/operational-modes-matrix.md`)

> Per-service yamls in `codex/10-audit/repos/<service>.yaml` get extended to track items 4–23. Items 1–3 already in the
> existing repo readiness yaml are inherited.

---

## Service readiness matrix — current snapshot

Tier-1 services — every item must be ✓ by May 23. Group-level rollup (full 23-item detail in per-service yamls).

| Service                           | A·Code | B·Data | C·Runtime | D·Coverage | E·Ops | F·Trading | G·UX | Linked plans                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| --------------------------------- | ------ | ------ | --------- | ---------- | ----- | --------- | ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| instruments-service               | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | instruments_and_market_tick_data_completion_2026_05_01 (instruments_service_orchestrator_reliability_fixes_2026_04_21 archived 2026-05-06)                                                                                                                                                                                                                                                                                                                                                      |
| market-tick-data-service          | ✓      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | cefi_master_2026_05_07 / defi_master_2026_05_07 / tradfi_master_2026_05_07 / sports_master_2026_05_07 / predictions_master_2026_05_07 (per-asset_group MTDS slices folded from `market_tick_data_to_100pct_2026_05_05`), instruments_and_market_tick_data_completion_2026_05_01                                                                                                                                                                                                                 |
| market-data-processing-service    | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | instruments_and_market_tick_data_completion_2026_05_01 (data_pipeline_completion_2026_04_18 archived 2026-05-06; same epic, newer audit, strict superset)                                                                                                                                                                                                                                                                                                                                       |
| features-onchain-service          | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | defi_master_2026_05_07 (folds in `consolidated_defi_data_pipeline_2026_04_15` + `defi_e2e_pipeline_2026_04_30`)                                                                                                                                                                                                                                                                                                                                                                                 |
| features-volatility-service       | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | ml_and_features_master_2026_05_07 (folds in `feature_dag_uac_ssot_and_features_coverage_2026_05_06`)                                                                                                                                                                                                                                                                                                                                                                                            |
| features-cross-instrument-service | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | ml_and_features_master_2026_05_07 (folds in `features_consolidation_and_drilldown_2026_05_06`)                                                                                                                                                                                                                                                                                                                                                                                                  |
| ml-training-service               | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | ml_and_features_master_2026_05_07 (folds in `consolidated_ml_advanced_pipeline_2026_04_15` + `ml_training_feature_read_perf_2026_05_06`; `ml_pipeline_revolution_2026_04_11` archived 2026-05-06)                                                                                                                                                                                                                                                                                               |
| ml-inference-service              | ◐      | ◐      | ◐         | n/a        | ◐     | n/a       | n/a  | ml_and_features_master_2026_05_07 (folds in `consolidated_ml_advanced_pipeline_2026_04_15`)                                                                                                                                                                                                                                                                                                                                                                                                     |
| strategy-service                  | ◐      | ◐      | ◐         | n/a        | ◐     | ✗         | ✗    | strategy_and_dart_master_2026_05_07 (folds in `strategy_architecture_v2_finalization_2026_04_19`), defi_master_2026_05_07 Fork 1 (lead archetype; `carry_staked_basis_structure_axis_2026_05_04` archived 2026-05-07)                                                                                                                                                                                                                                                                           |
| execution-service                 | ◐      | ◐      | ◐         | n/a        | ◐     | ✗         | ✗    | defi_master_2026_05_07 (folds in `defi_phase3_infrastructure_2026_03_30` + `leveraged_leg_controller_2026_05_01`)                                                                                                                                                                                                                                                                                                                                                                               |
| position-balance-monitor-service  | ◐      | ◐      | ◐         | n/a        | ◐     | ◐         | n/a  | defi_master_2026_05_07 Fork 1 (folds in `defi_e2e_pipeline_2026_04_30`; PBMS dual projection / fill attributor / child-venue attribution)                                                                                                                                                                                                                                                                                                                                                       |
| risk-and-exposure-service         | ◐      | ◐      | ◐         | n/a        | ◐     | ◐         | n/a  | defi_master_2026_05_07 Fork 1 (folds in `defi_e2e_pipeline_2026_04_30`; R&E intent subscriber — extend with explicit live-wiring todo)                                                                                                                                                                                                                                                                                                                                                          |
| pnl-attribution-service           | ◐      | ◐      | ◐         | n/a        | ◐     | ◐         | n/a  | defi_master_2026_05_07 Fork 1 (folds in `defi_e2e_pipeline_2026_04_30`; compute --mode batch CLI; extend with live-mode wiring todo)                                                                                                                                                                                                                                                                                                                                                            |
| alerting-service                  | ◐      | n/a    | ◐         | n/a        | ◐     | ◐         | n/a  | alerting_service_live_rules_2026_05_07 (Phase 1 UAC AlertCode taxonomy UAC@`d00326d`; Phase 2 service migration alerting-service@`b025e83`; Phase 3 envelope `code: AlertCode` field UAC@`2636815` + 3-service consumer migration; Phase 5 DART unified-trading-system-ui@`e9559565`; Phase 6 15 per-code runbooks PM@`45b854d5`+`6fad278e`+`db99a3ef`+`b40d405a`+`ac40983b`; Phase 2 KillSwitchBus publisher hook UAC@`3793310`+`2541a47` + alerting-service@`8eda37c`; Phase 4/7/8/9 pending) |
| batch-live-reconciliation-service | ✗      | n/a    | ◐         | n/a        | ◐     | ◐         | n/a  | master_to_live_defi_2026_05_23 Group F (folded from `consolidated_operational_validation_2026_04_15` 2026-05-07; cluster e2e + final QG sweep extend items 17-22 inline)                                                                                                                                                                                                                                                                                                                        |
| deployment-api                    | ✓      | n/a    | ◐         | n/a        | ◐     | n/a       | n/a  | deployment_api_work_stream_a_2026_05_07 (Phase 1 UAC types shipped UAC@`a70b3f6`; Phase 2 endpoints + Phase 3 QG pending)                                                                                                                                                                                                                                                                                                                                                                       |
| deployment-service                | ✓      | n/a    | ◐         | n/a        | ◐     | n/a       | n/a  | infrastructure_master_2026_05_07 (folds in `deployment_service_build_infrastructure_repair_2026_04_22`)                                                                                                                                                                                                                                                                                                                                                                                         |
| deployment-ui                     | ✓      | n/a    | n/a       | n/a        | n/a   | n/a       | n/a  | infrastructure_master_2026_05_07 (data-status work; `data_status_offline_rollup_2026_05_06` + `data_status_ui_fixes_2026_05_06` deferred to plans/ai/)                                                                                                                                                                                                                                                                                                                                          |
| unified-trading-system-ui         | ✓      | n/a    | n/a       | n/a        | n/a   | n/a       | n/a  | strategy_and_dart_master_2026_05_07 (folds in `consolidated_strategy_and_ui_2026_04_15` + `dart_ui_strategy_filtering_and_onboarding_2026_04_24`)                                                                                                                                                                                                                                                                                                                                               |

> **Action:** Cell values seeded from session memory + sub-plan inventory + 2026-05-06 plan-vs-plan audit, refreshed
> 2026-05-07 (Agent 5 Item 3) post-umbrella consolidation. Verify via per-service yamls in `codex/10-audit/repos/`
> before relying. Refresh notes: (a) ml-training / ml-inference / features-volatility / features-cross-instrument now
> point at `ml_and_features_master_2026_05_07` (folded 2026-05-07 from 4 archived source plans); (b) strategy-service /
> unified-trading-system-ui now point at `strategy_and_dart_master_2026_05_07` (folded 2026-05-07 from 3 archived source
> plans); (c) execution-service / PBMS / R&E / pnl-attribution all consolidate under `defi_master_2026_05_07` Fork 1
> (folded `defi_phase3_infrastructure` + `leveraged_leg_controller` + `defi_e2e_pipeline`); (d) alerting-service
> NO-LONGER-NO-PLAN — `alerting_service_live_rules_2026_05_07` shipped, Phase 1 UAC AlertCode taxonomy landed 2026-05-07
> (UAC@`d00326d` per PM@`7624ab21`); (e) batch-live-reconciliation folded inline as Group F extension on 2026-05-07 (no
> longer points at archived `consolidated_operational_validation`); (f) deployment-api now points at
> `deployment_api_work_stream_a_2026_05_07` (Phase 1 UAC types shipped UAC@`a70b3f6`).

> **Deep-audit follow-ups 2026-05-07** — column status caveats discovered during the deep audit but NOT yet flipped in
> the matrix above pending verification (file under work-stream G next housekeeping pass): (i) **alerting-service F
> column ✗**: F column rule says "live trading prereq for alerting-service" — A column flipped ✗ → ◐ on UAC AlertCode
> ship, but F column remains ✗ correctly because rules-engine consumer wiring has not landed
> (`grep AlertCode alerting-service/` returns 0 hits as of 2026-05-07 evening). Stays ✗ until alerting Phase 2 lands.
> (ii) **strategy-service + execution-service F columns ✗**: matching engine (5 matchers) shipped + carry_staked_basis
> tracing scripts present, but live-trading wiring pending (Phase 1.9 fold-in residuals + Phase 4D consumption). Could
> argue ◐ partial, but the conservative ✗ reflects "live trade has not yet executed" — keep ✗ until first paper-trade
> smoke completes (Agent 4 Day 5 item). (iii) **batch-live-reconciliation-service A column ✗**: no service code shipped
> yet — folded item-21 extends Group F inline, but the actual reconciliation surface (`pnl-attribution-service` +
> `batch-live-reconciliation-service`) needs a minimum-viable shipment before May-23. Stays ✗ correctly.

### Tier 2 — backfill catch-up + ML readiness ladder (NOT live by May 23)

`features-sports-service` (→ ML), `features-calendar-service` (TradFi → ML), `features-delta-one-service` (TradFi → ML),
`features-commodity-service` (TradFi → ML), `features-multi-timeframe-service` (cross-asset multi-timeframe aggregation;
deep audit 2026-05-07 found this repo previously unlisted). Group A–E required by May 23; Group F/G n/a until next
archetype lands.

### Tier 3 — post-launch enablement (after May 23)

`client-reporting-api`, `fund-administration-service`, `trading-agent-service`. Out of cutover scope.

---

## New work streams (not yet covered by sub-plans)

### A · deployment-api → standalone orchestration receiver

Today exposes `/api/data-status`, `/api/deployments/{service}/deploy`, `/api/cloud-builds/*`, `/api/vm-deployments`, SSE
`/stream/deploy-events`. Does NOT launch backfills, ML experiments, or strategy backtests as first-class actions.

- [ ] [API] `POST /api/backfill/launch` — `(service, asset_group, venue, data_type, start, end, force)` → fires
      per-asset-group launcher in `deployment-service/scripts/vm/`
- [ ] [API] `POST /api/ml/experiment/launch` — accepts experiment manifest, spins ml-training VM with experiment job_id
- [ ] [API] `POST /api/strategy/backtest/launch` — `(strategy_id, window, archetype_config)` → spins strategy-service
      backtest
- [ ] [API] `POST /api/execution/backtest/launch` — execution-alpha measurement on historical fills
- [ ] [API] `GET /api/vm/events/{vm_name}?since=<ts>` — streams GCS event logs from `gs://{pid}-events/`
- [ ] [API] `GET /api/builds/history` — tarball + Docker-image lineage (branch, commit, build trigger, deployer, target
      service, asset_group, target cloud)
- [ ] [API] AuthN via Firebase token forwarded from UTS-UI / Deployment-UI
- Reference: existing `deployment_api/routes/_code_builds_aws.py` for dual-cloud pattern

### B · Live Deployment UI tab

A new tab/section monitoring **live** trading services. Today deployment-ui is batch-job + data-status console; live
monitoring not covered.

- [ ] [UI] `/ops/live-deployments` route in deployment-ui
- [ ] [UI] Live-services panel — running services in live mode, last STARTED, last DATA_BROADCAST, staleness in seconds
- [ ] [UI] Live alert pane consuming alerting-service feed
- [ ] [UI] Per-service live log tail (deployment-api `/api/vm/events`)
- [ ] [DOC] Codex SSOT at `codex/05-infrastructure/live-deployment-monitoring.md` (currently missing)

### C · UTS-UI ↔ DART terminal — research, backtest, **manual-trade**

Today UTS-UI has strategy-catalogue / strategy-evaluations / strategy-lifecycle-editor. Missing: ML-experiment,
strategy-backtest, execution-backtest launch surfaces, and **the DART manual-trade lane** (visualize the DeFi archetype,
place trades manually through the same backend as automation, monitor before flipping to auto).

- [ ] [DECIDE] research-service repo vs fold into deployment-api (default: fold-in)
- [ ] [UI] `/research/ml-experiments`, `/research/strategy-backtests`, `/research/execution-backtests` tabs
- [ ] [UI] **DART terminal — DeFi archetype visualization + manual trade entry**
  - [ ] Render archetype state (positions, funding, LST yields, hedge basis) in real-time
  - [ ] Manual trade entry → goes through execution-service same path as automation (NOT a side door)
  - [ ] Operator-monitored window before automation flip
  - [ ] Automation toggle gated by checklist Group F + G complete
- [ ] [API] All tabs wired to deployment-api (work-stream A)
- [ ] [UI] Borrow VmDeployments.tsx tracker pattern from deployment-ui
- [ ] [DOC] Codex SSOT at `codex/04-architecture/research-service-and-dart-integration.md`
- [ ] [DOC] Extend `codex/09-strategy/cross-cutting/operational-modes-matrix.md` with the DART manual-trade lane

### D · Cloud-agnostic full-parity proof (data + batch + ML + live + monitoring on AWS)

Per Q&A 4, the AWS proof is **full parity**, not a minimal 2-VM proof. Order of operations matters because data
migration is gated by cost.

**D.1 — Data migration to AWS (sized to DeFi only, NOT full corpus)**

- [ ] [SCRIPT] Cost analysis: GCS storage + egress for DeFi-relevant data → AWS S3 storage + ingress estimate; report in
      `unified-trading-pm/docs/aws-migration-cost-2026-05.md`
- [ ] [SCRIPT] Selective copy of DeFi-relevant manifests + parquet (instruments / MTDS / MDPS / features-onchain) to S3,
      preserving hive layout. **Skip TradFi / Sports / Prediction data — wasteful re-fetch.**
- [ ] [API] Update deployment-api data-status endpoints to be cloud-agnostic — read from GCS or S3 based on
      `CLOUD_PROVIDER`

**D.2 — Batch deployment side proof (AWS)**

- [ ] [SCRIPT] AWS EC2 launcher equivalents alongside `gcloud` launchers — minimum: instruments / MTDS /
      features-onchain in AWS mode
- [ ] [SCRIPT] Run a backfill on AWS with `--force` for a small DeFi window — proves the deployment-side batch path
      works on AWS, not just dataset migration
- [ ] [SCRIPT] Cloud Build dual-provider trigger taking deps tarball + code-from-GitHub (CodeBuild already partial via
      `_code_builds_aws.py`)

**D.3 — Backtest + ML on AWS**

- [ ] [SCRIPT] Run a strategy backtest example on AWS via deployment-api `/api/strategy/backtest/launch` (work-stream A)
      — proves end-to-end batch surface
- [ ] [SCRIPT] Run an ML training example on AWS via deployment-api `/api/ml/experiment/launch` — proves ML side
- [ ] [SCRIPT] Run an execution backtest example on AWS — proves execution-side batch

**D.4 — Live deployment + monitoring on AWS**

- [ ] [SCRIPT] One live archetype instance running on AWS (carry_staked_basis on smaller capital) — proves live trading
      works on AWS-as-deployment-target
- [ ] [UI] Live Deployment UI tab (work-stream B) reads from both GCS and S3 event streams, surfaces both live
      deployments
- [ ] [SCRIPT] Seamless-switch test: pause GCP-live archetype, resume on AWS-live, verify position state preserved via
      custody / position-balance-monitor

**D.5 — Build lineage tab**

- [ ] [API] `/api/builds/history` (work-stream A) returns combined GCP + AWS records
- [ ] [UI] Build-history tab in deployment-ui — branch / commit / image tag / target cloud / deployer / triggered-by
      (tarball vs Claude build vs CI)

**D.6 — Codex updates**

- [ ] [DOC] Augment `codex/04-architecture/cloud-agnostic-migration.md` with VM-launcher parity appendix + the
      data-migration cost-gate principle
- [ ] [DOC] Codex SSOT at `codex/05-infrastructure/cloud-agnostic-build-lineage.md`
- [ ] [DOC] Codex SSOT at `codex/04-architecture/seamless-cloud-switch.md` — preserved-state semantics when migrating a
      live deployment between clouds

### E · Live-mode services (REVISED post-2026-05-06 audit — 1 new plan, 4 extensions)

The plan-vs-plan audit found 4 of 5 services already covered by existing plans. Only **alerting** is a genuine new-plan
gap.

- [x] [PLAN] Open `alerting-service-live-rules_2026_05_07.plan.md` — the only genuine NO-PLAN gap. Lock to
      `live-defi-rollout`. References checklist Groups F + G. (verified 2026-05-07:
      plans/active/alerting_service_live_rules_2026_05_07.plan.md exists)
- [ ] [EXTEND] `defi_master_2026_05_07` Fork 1 (folds `defi_e2e_pipeline_2026_04_30`) — add explicit todos for
      **position-balance-monitor live-mode wiring** (PBMS Pub/Sub + GCS contract; dual projection + fill attributor +
      child-venue attribution already shipped per plan body).
- [ ] [EXTEND] `defi_master_2026_05_07` Fork 1 (folds `defi_e2e_pipeline_2026_04_30`) — add explicit **risk-and-exposure
      intent-subscriber live-wiring todo** (currently flagged as one of 5 wiring holes blocking live closure).
- [ ] [EXTEND] `defi_master_2026_05_07` Fork 1 (folds `defi_e2e_pipeline_2026_04_30`) — add explicit **pnl-attribution
      `--operation compute --mode live` todo** alongside the existing batch CLI.
- [x] [EXTEND] `consolidated_operational_validation_2026_04_15` — add explicit **batch-live-reconciliation live-cutover
      items**. **DONE 2026-05-07**: source plan archived; its 11 unchecked todos (incl. batch-vs-live cluster E2E)
      folded into master Group F — see "Folded operational-validation todos" subsection above.
      `manual_trade_booking_reconciliation_2026_03_22` was already archived 2026-05-06 (Stage 1 plan-hygiene sweep); its
      successor surface is now master Group F (live-trading prereqs).

### F · Codex SSOT gaps to fill alongside the work

- [ ] [DOC] `codex/05-infrastructure/live-deployment-monitoring.md` (work-stream B)
- [ ] [DOC] `codex/04-architecture/research-service-and-dart-integration.md` (work-stream C)
- [ ] [DOC] `codex/05-infrastructure/cloud-agnostic-build-lineage.md` (work-stream D)
- [ ] [DOC] `codex/04-architecture/ml-experiment-lifecycle.md` — ML job_id manifest separate from data manifest
- [ ] [DOC] `codex/04-architecture/live-strategy-config-hot-reload.md` — strategy config hot-reload end-to-end for live
      mode
- [x] [DOC] CEFFU integration content folded into single custody SSOT
      [`codex/04-architecture/custody-providers.md § 2.4 CeffuCustodyProvider — PLANNED`](../../codex/04-architecture/custody-providers.md).
      **STUB shipped 2026-05-07 (Agent 5 deep-audit follow-up)** as standalone `ceffu-custody-integration.md`; **folded
      into `custody-providers.md` 2026-05-08 (codex_refactor Phase D.4)** so the protocol + every provider + coverage
      matrix + mode matrix all live in one file. Subsections marked **PENDING** with content owners listed (Binance
      institutional wiring → defi_master Fork 1 hedging-leg). 5 open questions filed for content authors in the CEFFU
      subsection.

#### Deep-audit P0 follow-ups (2026-05-07, surfaced by Agent 5 deep-audit on Items 17-22)

These 5 follow-ups were uncovered by 3 parallel Explore sub-agents auditing Group F+G + the 2 new umbrellas. Each gates
a Group F item; ownership routes to the named agent/tab.

- [ ] [AGENT] P0. **Author 2-year config-grid backtest runner** at
      `strategy-service/scripts/run_2yr_config_grid_backtest.py` for `carry_staked_basis` + `leveraged_funding_arb`
      archetypes; emit P&L variance distribution per archetype config dimension (lookback / leverage / hedge-ratio /
      rebalance-freq). Gates Group F item 18 ("2-year batch backtest run"). Owner: Agent 4 (DeFi launch + paper-trade
      smoke). Existing scripts (`trace_carry_staked_basis.py`, `trace_all_carry_archetypes.py`) are tracing/simulation,
      not config-grid sweeps — confirm reusability or write fresh.
- [ ] [AGENT] P0. **Ship batch-live-reconciliation-service minimum-viable scaffold** with per-archetype P&L diff
      endpoint + per-trade fill comparison. Currently A column ✗ in the matrix (service scaffolded but NOT
      code-complete). Gates Group F item 21 ("Reconciliation suite — batch-vs-live reconciliation working"). Owner:
      Agent 4 (DeFi launch + paper-trade smoke) — this is the producer side that paper-trade smoke validates.
      `pnl-attribution-service` already ships `--mode batch` CLI; `--mode live` wiring + reconciliation surface is the
      gap.
- [ ] [AGENT] P0. **Wire alerting-service rules engine to consume UAC AlertCode taxonomy** —
      `grep "AlertCode" alerting-service/` returns 0 hits as of 2026-05-07 evening despite UAC@`d00326d` shipping the
      taxonomy. Existing rules (`data_freshness_rules.py`, `defi_rules.py`, `margin_rules.py`) need to be wired to the
      closed-set `AlertCode` enum. Gates Group F item 22 ("Trading guardrails — alerting-service rules cover live
      data-freshness + P&L deviation + position breaches"). Owner: Agent 1 (alerting Phase 2). Already part of
      [`alerting_service_live_rules_2026_05_07`](alerting_service_live_rules_2026_05_07.md) Phase 2 scope; this todo is
      the cross-tab visibility marker.
- [ ] [AGENT] P0. **Phase 1A.3 sports vocabulary decision** (operator decision, ~30min) — pick (a) mapping table / (b)
      tuple-typed required_inputs / (c) namespaced names. Currently deferred. Gates features-sports-service consumer
      migration (Phase 2A of ml_and_features_master) which in turn gates the `assert_no_lookahead_for_feature_group`
      helper from silently no-oping on sports calculators. Owner: operator + Agent 2 (writegate / consumer-migration).
      Already filed in [`ml_and_features_master_2026_05_07`](../epics/ml_and_features_master_2026_05_07.md) Phase 1A.3;
      this todo is the cross-tab visibility marker against May-23 critical path.
- [ ] [AGENT] P1. **Validate per-venue testnet endpoints for CeFi connectors** (Binance / Bybit / Deribit / OKX). Gates
      Group F item 20 ("Live testnet replicates prod"). Tenderly fork fixtures shipped on the DeFi side per
      `execution-service/tests/integration/conftest.py`; CeFi side has not been validated end-to-end. Owner: Agent 4
      (DeFi launch tab covers cross-venue execution). Verify each connector points at the correct testnet endpoint +
      runs through a smoke order via testnet credentials.

### G · Plan hygiene sweep (Day 1 quick-win, surfaced by 2026-05-06 audit)

Mechanical cleanups that shrink `active/` from ~148 to ~130 plans and unblock the master plan from referencing
self-superseded artefacts.

**Archive Stage 1 — 17 self-tagged superseded plans (DONE 2026-05-06, commit forthcoming):**

- [x] [SCRIPT] `client_config_and_defi_risk_2026_04_01` → archive
- [x] [SCRIPT] `cross_domain_alpha_execution_intelligence_2026_04_11` → archive
- [x] [SCRIPT] `strategy_lifecycle_visibility_ui_2026_04_11` → archive
- [x] [SCRIPT] `ui_walkthrough_and_e2e_alignment_2026_04_01` → archive
- [x] [SCRIPT] `dart_ui_strategy_filtering_and_onboarding_2026_04_24` → archive
- [x] [SCRIPT] `ml_pipeline_revolution_2026_04_11` → archive
- [x] [SCRIPT] `domain_agnostic_ml_framework_2026_04_11` → archive
- [x] [SCRIPT] `defi_instrument_pipeline_and_rewards_2026_04_01` → archive
- [x] [SCRIPT] `mev_protection_and_execution_enhancements_2026_04_01` → archive
- [x] [SCRIPT] `manual_trade_booking_reconciliation_2026_03_22` → archive
- [x] [SCRIPT] `unified_pipeline_scheduling_and_triggers_2026_04_15` → archive
- [x] [SCRIPT] `remove_data_types_field_2026_04_10` → archive
- [x] [SCRIPT] `polymarket_prediction_pipeline_2026_03_25` → archive (still has dangling `superseded_by:` to
      non-existent `consolidated_sports_prediction_pipeline_2026_04_15`; fix in follow-up)
- [x] [SCRIPT] `smoke_dep_chain_tactical_fixes_2026_04_20` → archive
- [x] [SCRIPT] `instruments_service_template_refactor_8e653acc` → archive
- [x] [SCRIPT] `availability_manifest_v4_and_data_status_2026_04_13` → archive (manifest now v6)
- [x] [SCRIPT] `defi_pipeline_extension_followups_2026_05_03` → archive (`status: complete`)
- [ ] [SCRIPT] `dashboard_services_grid_collapse_2026_04_21` → archive **once final 3 todos land** (deferred — plan
      explicitly says "Ready for [unlock-plan] + archive once final 3 todos land")

**Active count: 148 → 131 after Stage 1.**

**Convert to ICEBOX / paused (3):**

- [ ] [SCRIPT] `hybrid_sampler_5s_resolution_2026_03_30` → ICEBOX (`orphan_candidate: true`)
- [ ] [SCRIPT] `mempool_feed_integration_2026_06_01` → remove from `active/` (paused, future-dated)
- [ ] [SCRIPT] `signal_leasing_broadcast_architecture_2026_04_20` → archive on next `[unlock-plan]` pass (8 phases done)

**Frontmatter backfill (one-shot script):**

- [ ] [SCRIPT] Workspace-wide script to populate missing `last_updated` from `git log` mtime (re-derive count at script
      time; original 2026-05-06 audit said 140 plans, post-Stage-7 batch consolidation the surface is now
      `~28 active/` + `~66 ai/` + `~437 archive/` (re-derived 2026-05-08 by audit-followups Tab 8) — most missing
      `last_updated` rows are in `archive/` and `ai/`)
- [ ] [SCRIPT] Same script populates `asset_group` inferred from filename + body (re-derive count at script time;
      original 2026-05-06 audit said 142 plans across active+ai+archive)
- [ ] [SCRIPT] Same script populates `locked_by: live-defi-rollout` for plans missing it (re-derive count at script
      time; original 2026-05-06 audit said 31 plans active-only; verify each is actually mid-flight first; otherwise
      leave unset)
- [ ] [SCRIPT] Add YAML frontmatter to 5 plans that have none (`_sports_phantom_fixtures_recovery_handover_2026_05_06`,
      `dashboard_services_grid_collapse_2026_04_21`, `defi-strategy-ui-verification`, `tiered_help_chatbot_2026_03_22`,
      `universe_ssot_fix_2026_04_20`)
- [ ] [SCRIPT] Fix the 1 filename↔name mismatch (`path_to_100m_finalization_2026_04_20`)
- [ ] [SCRIPT] Fix the 2 YAML errors

**Re-tag children of cluster umbrellas:**

- [ ] [SCRIPT] Add `parent: writegate_honest_coverage_endtoend_2026_05_06` to the 4 child plans
- [x] [SCRIPT] Add `parent: defi_e2e_pipeline_2026_04_30` to defi_pipeline_extension / leveraged_leg_controller /
      carry_staked_basis where appropriate
      `[AUDIT 2026-05-07: STALE — defi_e2e_pipeline_2026_04_30, defi_pipeline_extension_2026_05_01, leveraged_leg_controller_2026_05_01, carry_staked_basis_structure_axis_2026_05_04 all archived 2026-05-07 Stage 7 consolidation; defi_master_2026_05_07 is the umbrella. parent: tagging no longer applicable.]`
- [ ] [SCRIPT] Add `parent: sports_fixtures_truthset_recovery_2026_05_06` to phantom-recovery + recon plans
- [ ] [SCRIPT] Merge or formal child-link `shard_dimension_naming_asset_group_ssot_2026_04_25` under
      `venue_axis_asset_group_vocabulary_2026_04_25`

---

## Recent shipments + open successor plans (2026-05-07 session)

**Shipped this session** — backfill throughput unblock + observability uplift:

- **MTDS Tardis adapter parallelization** — UTL@`50ad40ef` `ParallelPerSymbolRunner` (387 LOC + 12 tests) +
  UTL@`c5da8abe` + UTL@`3a204c03` (multi-callback `ResourceProfiler` + 11 tests) + MTDS@`28db65a` (Tardis adapter swap
  spot/perp + futures-chain) + MTDS@`452f105` (`_ACTIVE_RESOURCE_PROFILER` accessor wiring + 3 tests). Per-symbol
  fan-out went sequential → 16-way concurrent with shard-level failure isolation, RSS pause-not-cancel on 75% memory
  warning, and an in-flight byte budget gate. Atomicity preserved via existing staged-temp + atomic-rename +
  close-time-upload chain (verified across `tardis_stream_processor.py:172-244`, `streaming_writer.py:315-377`,
  `streaming_shard_finalizer.py:241-269`). Observed post-bounce: previously-slow heavy futures shards
  (cefi-bitfinex-futures-2025-heavy, cefi-kraken-futures-2025-heavy, etc.) drained to `STOPPED` clean in 5-11 minutes vs
  hours-to-days yesterday.
- **MDPS launcher tradfi-aware defaults** — deployment-service@`02ee6d6` auto-applies `MACHINE_TYPE=e2-highmem-8` +
  `--max-workers=2` for tradfi MDPS launches (band-aid for OOM signature seen on `mdps-tradfi-2025` 2026-05-07).
- **Tier3 cefi heavy default bumped** — deployment-service@`69071db` `e2-highmem-2` → `e2-highmem-4` (4 vCPU clears the
  CPU-saturation bottleneck post-parallelization; cost delta trivial because VMs now finish in 5-11 min).
- **BITGET coverage_start declared** — UAC@`c354d07` `date(2024, 11, 8)` per Tardis `availableSince` probe. Tardis
  bitget-futures has 0 data pre-2024-11-08 across all 910 perps; Bitget native covers 2019-07-10 forward but only via
  OHLC endpoints (no per-trade ticks). Pre-cutoff manifest rows now classified `EXPECTED_PRE_SOURCE_COVERAGE_START` via
  Tier 3D.1 reconciler.
- **7 verified plan checkbox flips** across 5 active plans — PM@`88d2abc4` (incident #4 of foot-gun rule: bundled into
  parallel-agent's commit; docs-only, content correct).

**Successor plans for partial implementations (per CLAUDE.md "Temporary state must have a named successor plan" rule):**

- [`mdps_streaming_and_backpressure_2026_05_07`](./mdps_streaming_and_backpressure_2026_05_07.md) (PM@`c0ccc8ad`) —
  covers DEFERRED Units 1+3 from this session: incremental flush in `_streaming_write_per_tf` (via UTL
  `canonical_writer` `open_candle_writer` / `close_candle_writer` lifecycle so shard atomicity is preserved across
  N-symbol batches) + MDPS-side ResourceProfiler `on_memory_warning` admission control on the ThreadPoolExecutor.
  Band-aid (deployment-service@`02ee6d6` launcher) shipped this session; architectural fix retires it. Optional Phase 3:
  replace `_read_tick_data` eager full-load with `pyarrow.parquet.ParquetFile.iter_batches()` row-group streaming
  (consumer audit: `_process_standard_timeframe`, `_extract_instrument_info`, `_validate_*` all need iterator
  adaptation).
- [`mtds_databento_path_streaming_2026_05_07`](./mtds_databento_path_streaming_2026_05_07.md) (PM@`c0ccc8ad`) — covers
  Databento adapter improvements identified during the parallelization audit: pass `path=<tempfile>` to
  `client.timeseries.get_range(...)` at `databento_adapter.py:509-517` + iterate `to_df(count=N)` chunks (eliminates
  full-DBN BytesIO + full-DataFrame materialisation peak). Phase 2: parallelise outer `(data_type, dataset)` loop via
  `asyncio.gather` (bounded by existing `Semaphore(100)`). Phase 3 (gated on 2nd consumer): UTL `streaming_dbn_writer`
  helper bridging Databento `path=<tmp>` mode into `StreamingParquetWriter.write_chunk`. Different antipattern than
  Tardis (Databento bundles up to 2000 symbols per call, no per-symbol loop) — separate fix shape.

**Memory entry**: `memory/project_mtds_parallelization_fix_2026_05_07.md` (Claude session-local auto-memory) captures
the full session for future agents.

**Afternoon shipments 2026-05-07** — writegate threading + governance + cross-tab parallel work (Agent 1 / Agent 2 /
Agent 5):

- **Writegate Phase 4.A typed-error rendering** — UTL classifier → deployment-api `error_reason` API field →
  deployment-ui typed badge end-to-end. deployment-ui@`a7384a0` (TypedReasonBadges + FailurePillarStack components + 24
  unit tests + client.ts TurboSubDimension extension) + deployment-ui@`621f0b3` (wire both into DataStatusTab venue
  summary line). Closed-set drift guard test fails CI if deployment-api `_FAILURE_PILLAR_KEYS` or `_EMPTY_REASON_KEYS`
  drift from UTL. Phase 4.B.1 + 4.B.2 checkboxes flipped per PM@`0c2a0cca` + PM@`21f8a277` (re-apply after foot-gun #3).
- **Writegate Phase 3.D.4 `--apply-write` complete** — 1,455,901 rows landed in per-VM manifest shards across all 5
  asset_groups (PM@`79e47874`): tradfi 35,033 / sports 13,176 / cefi 119,152 / prediction 2,280 / defi 1,286,260. CeFi
  - Prediction now real impl (UAC@`ac218dc` + instruments-service@`d1c9928`), no longer stubs. **Canonical-merge
    blocked** for tradfi / defi / prediction on consolidator P0 (`ArrowTypeError` on `instrument_count`); RESOLVED
    PM@`341bb285` via instruments-service@`a936a28` + 4 in-place shard fixes (cast string → Int64/boolean per canonical
    dtypes).
- **Writegate Phase 3.D.5 Wave 1+2.M migration COMPLETE** — 3,114,843 rows flipped across all 5 asset_groups
  (PM@`a541f51e` + PM@`937df64b`): UAC@`e855051` (typed errors) + UTL@`68b3804a` (4-state capture_status:
  `EXPECTED_UNATTEMPTED` 4th value) + UTL@`7eca2c20` + UTL@`7276cca1` + instruments-service@`86804c7` +
  deployment-service@`f72686b` + deployment-service@`327acf4`.
- **UAC `AlertCode` taxonomy Phase 1 shipped** — UAC@`d00326d` (Agent 1 tab) per PM@`7624ab21`. Closed-set alert-code
  StrEnum + threshold dataclass + severity-vs-alert-code separation. Phase 2-9 of
  `alerting_service_live_rules_2026_05_07` pending.
- **CLAUDE.md 4-state capture_status SSOT codified** — PM@`28e975b0` records `EXPECTED_UNATTEMPTED` as the 4th
  capture_status value alongside `captured` / `empty_confirmed` / `attempted_failed`; 4-category empty-output decision
  (A/B/C + new D for write-time-skip) documented for adapter authors.
- **Agent-5 Item 1 — umbrella + master Group F+G phase-ordering audit shipped** (Agent-5 Item 1, work_split P1) —
  ml_and_features_master gained explicit upstream sibling-blocker callout naming writegate Phase 2.D `available_at`
  stamping; strategy_and_dart_master gained Phase-numbering note + fixed ambiguous "Phase 1.9 service-split fold-in"
  descriptor → "Phase 3-11 fold-in residuals" + new Coordination-with-sibling-plans § naming hand-offs. Master Group F+G
  fold-in (operational-validation extends items 17-22 inline) verified structurally coherent. Edits absorbed by
  PM@`21f8a277` (writegate Phase 4.B re-apply commit, foot-gun #1 — semver-rollout bot's `git add` swept up Agent-5's
  unstaged work). Service-readiness matrix staleness (10 rows) refreshed in this commit.
- **Agent-5 Item 2 — `data_status_audit_findings` triage = STANDALONE** (Agent-5 Item 2, work_split P2) — PM@`2bd62a90`.
  Tracker stays standalone (NOT folded into `infrastructure_master`); cross-master rollup spans 5 owner plans;
  lifecycle-bounded — self-archives when all referenced master-plan todos go green.

---

## Critical-path DAG (May 6 → May 23)

### Top 3 risks for May-23 cutover (synthesised 2026-05-07 from 6-asset-group deep audit)

| #   | Risk                                                                  | Confidence | Impact | Mitigation                                                                                                                                                                                                                                                                                                                                                                        |
| --- | --------------------------------------------------------------------- | ---------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Lending-indices silent-zero cascade** on AAVE V3 ETHEREUM           | HIGH       | HIGH   | Day 1 (2026-05-08): root-cause + commit fix + re-launch `mtds-lending-indices` VM. Likely cause: instruments-store-defi metadata + subgraph URL mapping per chain. Validate Ethereum captures ≥1 row before declaring re-run complete. **Hard floor for carry_staked_basis batch e2e** (Week 2 item 1).                                                                           |
| 2   | **4-service QG + 9-connector testnet validation slip into Week 3**    | MEDIUM     | HIGH   | Days 2-5 (May 9-12): parallelize across 3 sub-agents — strategy-service Phase 6d (1 day), execution-service + features-onchain + R&E QG (3 agents × 2 days), deployment-api testnet runner for connector smoke (Day 2). EOD May 12 gate: all 4 services pass + 9 connectors validated. Owner: Agent 4. **Failure mode**: Group F checklist cannot close → Week 3 cutover at risk. |
| 3   | **PBM + R&E + pnl-attr live-mode wiring scope unspecified, no owner** | MEDIUM     | MEDIUM | Day 3 (May 10): assign owner (Agent 3 or 4); add explicit todos in defi_master Fork 1; validate Pub/Sub + intent-subscriber + `pnl-attribution --mode live` CLI in same 1-day sprint as 4-service QG. **Failure mode**: wiring stays implicit, slips into Week 3, or ships half-baked post-cutover.                                                                               |

**Sequencing recommendation for May 8-12 (5-day buffer to Week 2):**

1. **Day 1 (May 8)**: Lending-indices root-cause + fix + re-launch (Risk 1).
2. **Day 2 (May 9)**: Strategy-service Phase 6d QG → merge; execution-service QG start.
3. **Day 3 (May 10)**: Assign PBM/R&E/pnl-attr live-wiring owners (Risk 3); author 2-year config-grid backtest runner
   (deep-audit P0 follow-up).
4. **Days 4-5 (May 11-12)**: 9-connector testnet smoke (parallel); features-onchain + R&E + pnl-attr QG (parallel).
5. **EOD May 12 gate**: all 4-service QG passing; 9 connectors validated; lending-indices re-run complete; PBM/R&E
   live-wiring owners committed. **Do NOT defer any of these — losing May 8-12 leaves zero buffer for Week 3.**

### Week 1 (May 6–12) · foundations close + tier-1 services pass Groups A–E + AWS migration starts

> **Refreshed 2026-05-07 evening (Agent 5 deep-audit Item 3 follow-up)** — 6 parallel sub-agents audited cefi / defi /
> tradfi / sports / predictions / infrastructure umbrellas for shipped-vs-remaining. Bullets below now cite evidence per
> flip; remaining work routed to specific umbrella + risk-flagged where May-23 cutover is at stake.

- [x] Close shard-granularity propagation (designate one of the 3 plans as the SSOT). **DONE 2026-05-07** —
      `infrastructure_master_2026_05_07` is the SSOT umbrella (folds in `shard_granularity_propagation` +
      `data_status_multi_axis` + `deployment_service_build_infrastructure_repair`). Multi-axis correction shipped per
      deployment-service@`456acb9`; 4-state capture_status SSOT codified PM@`28e975b0`.
- [ ] Close TradFi MVP residuals (cluster-validation wiring at `record_captured`). **PARTIAL 2026-05-07** — Tier 2E
      tradfi adapters complete (MDPS@`e9520a0`); ES.OPT 11-cluster validation gate wired (MTDS@`260325c`); 35,033 tradfi
      EXPECTED_HOLIDAY/WEEKEND rows landed (PM@`79e47874`). **REMAINING**: market-hours + holiday SSOT integration
      across 12 affected repos (databento.py adapter, ml-training-service data_filters.py + mock_feature_generator.py,
      strategy base class config), 5 mdps-tradfi VMs draining ETA 2026-05-08.
- [ ] Close DeFi data-pipeline blockers (features-onchain LookaheadBiasError + lending_rates write-gate). **PARTIAL
      2026-05-07** — Pyth Hermes (Solana) + Chainlink EVM multi-chain oracle adapters shipped per `mtds-s3-5` +
      `mtds-s3-6`. **🚨 RISK 1 (HIGH/HIGH)**: Lending-indices silent-zero cascade on AAVE V3 ETHEREUM — VM
      `mtds-lending-indices-20260507-140418` ran + diagnosed 3 bugs (AAVE V3 ETH 0/343 captured / COMPOUND V3
      multi-chain subgraph schema error / instruments-store-defi metadata 404 for early-2022 dates); **MUST FIX BY
      2026-05-12** else carry_staked_basis batch e2e fails Week 2. Owner: Agent 4 / defi_master Fork 1.
- [ ] Close sports phantom recovery — frees VM-quota for DeFi + AWS work. **PARTIAL 2026-05-07** — Phase 1 + Phase 3
      pre-req shipped (instruments-service@`9f0e3f9` `dedup_phantom_after_recovery.py`; chain-runner architecture
      @`cbb50fa`/`e900769`/`7ce509e`); 4 sports recovery VMs in flight (af / fs / sfi / us) ETA 2026-05-08; LEAGUES
      daily-dump killed (instruments-service@`93efebf`); ODDS source confirmed footystats (codex doc updated). **POST
      2026-05-08 VM DRAIN**: run `dedup_phantom_after_recovery.py --apply` then `data_available_at` rename Phase 2.
- [x] **Open 1 alerting plan + extend 4 existing plans** (revised post-2026-05-06 audit; see work-stream E for details:
      PBMS / R&E / pnl-attribution extend `defi_master_2026_05_07` Fork 1 (folds `defi_e2e_pipeline_2026_04_30` per
      Stage 7 consolidation); batch-live-recon extends `consolidated_operational_validation_2026_04_15`). **DONE
      2026-05-07** — [`alerting_service_live_rules_2026_05_07`](alerting_service_live_rules_2026_05_07.md) opened; Phase
      1 UAC AlertCode taxonomy shipped (UAC@`d00326d` per PM@`7624ab21`); 4 plan extensions tracked under work-stream E.
- [x] **Plan hygiene sweep (Day 1 quick-win)** — archive 18 self-tagged superseded plans; backfill missing frontmatter
      (`last_updated` / `asset_group` / `locked_by` / 5 plans with no frontmatter at all); re-tag cluster children with
      `parent:` field — work-stream G. **DONE 2026-05-06** — Stage 1 archived 17 self-tagged superseded plans (one
      deferred per "Ready for [unlock-plan]" rule); per-plan checkboxes flipped under work-stream G § "Archive Stage 1".
- [ ] Ship deployment-api `/api/backfill/launch` + `/api/vm/events` (work-stream A). **IN FLIGHT 2026-05-07** — Phase 1
      UAC types shipped (UAC@`a70b3f6`: `BackfillLaunchRequest`, `BackfillLaunchResult`, `VMLifecycleEvent`,
      `VMEventListResult`, `BackfillLaunchTaskKind` 23-value StrEnum + 15 unit tests). Phase 2 (POST/GET handlers) +
      Phase 3 (QG) pending. Owner: Harsh Day 3 (Agent 1 work_stream_a tab).
- [ ] Decide research-service repo question (work-stream C). **PENDING** — fold into deployment-api default; no decision
      logged. Owner: operator + Agent 4.
- [x] AWS migration cost analysis (work-stream D.1) → user signs off scope. **DONE 2026-05-07** — research artefact
      shipped at `codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md`, then archived 2026-05-08 per
      codex_refactor F.4 to `plans/archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md` with per-resource cost
      snapshot extracted to `codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md`; recommendation
      SUPERSEDED by dual-cloud decision per `aws_migration_defi_first_2026_05_07.md` Phase 0 (≥$40k credit confirmed; no
      service / region / account locks). Phase 2 dual-bucket setup is Agent 4 Day 4.
- [ ] Sports / TradFi / CeFi ML pipelines reach "running on representative sample" milestone (parallel — tier 2 ladder).
      **BLOCKED ON VM DRAIN** — sports + tradfi VMs draining 2026-05-08; cefi VMs draining 2026-05-08/09 per cefi_master
      audit. Post-drain: ML smoke + backtest grid actionable for each.
- [ ] Hyperliquid + Aster perp DEX integration: instrument registry + market-data live (these don't have CEFFU
      equivalents — direct on-chain). **PARTIAL 2026-05-07** — Lighter zkSync + Pacifica Solana DEX onboarding shipped
      (MTDS@`10aa715` + `51fecd5` + UAC@`e890022` for ohlcv_1m); Hyperliquid + Aster live execution wiring pending.
      Owner: Agent 4 (defi_master Fork 1 hedging-leg).
- [ ] **Lending-indices silent-zero fix + re-launch** (Day 1 = today, 2026-05-08). **NEW 2026-05-07 deep-audit** — Risk
      1: AAVE V3 ETHEREUM 0/343 captured silently on `mtds-lending-indices-20260507-140418`; root-cause + commit fix +
      re-launch VM. Gates carry_staked_basis batch e2e (Week 2). Owner: Agent 4 (defi_master Fork 1).
- [ ] **4-service QG sweep** (strategy / execution / R&E / features-onchain; Days 2-5). **NEW 2026-05-07 deep-audit** —
      Risk 2: 37 unchecked defi_master items + 9 execution-service connectors untested on testnet. Parallelize across 3
      agents Days 2-3; testnet smoke Day 4-5. EOD May 12 gate: all 4 services pass + 9 connectors validated. Owner:
      Agent 4 (DeFi launch tab).
- [ ] **PBM + R&E + pnl-attr live-mode owner assignment** (Day 3). **NEW 2026-05-07 deep-audit** — Risk 3: defi_master
      Fork 1 folded `defi_e2e_pipeline` but did NOT explicitly scope "live-mode wiring" as separate todos — they sit as
      free-floating audit findings. Assign owner + add explicit todos in defi_master Fork 1 by 2026-05-10 else slips
      into Week 3 or ships half-baked post-cutover.

### Week 2 (May 13–19) · live wiring + cloud parity + Groups F/G

> **Refreshed 2026-05-07 evening (deep-audit Item 3)** — each Week 2 bullet now has its blocker chain explicit. Items at
> HIGH risk of slipping into Week 3 are flagged 🚨.

- [ ] `carry_staked_basis` runs end-to-end in batch with `always_fill` + matching-engine fills (Group F item 17).
      **Blockers**: 4-service QG (strategy / execution / R&E / features-onchain — none yet passing), execution-service
      Aave/Uniswap/Lido testnet validation (NOT yet started), vault-share-price + lst-rates MTDS VMs (NOT yet launched).
      Lending-indices silent-zero fix is the gate.
- [ ] `leveraged_funding_arb` runs end-to-end in batch — cross-venue funding spread across 6 perp venues. **Blockers**:
      funding_oi calculator backfill VMs in flight 2026-05-05; cross-venue funding spread feature; 4-service QG;
      Hyperliquid + Aster live execution wiring (Lighter + Pacifica shipped, but Hyperliquid + Aster pending).
- [ ] 2-year P&L variance batch run completed across config grid for both archetypes (Group F item 18). 🚨
      **AUTHOR-MISSING**: no `run_2yr_config_grid_backtest.py` exists yet — P0 follow-up filed in work-stream F §
      Deep-audit P0 follow-ups. Owner: Agent 4. Existing `trace_carry_staked_basis.py` + `trace_all_carry_archetypes.py`
      are tracing/simulation, NOT config-grid sweeps.
- [ ] Execution-service connectors validated on testnet (Group F item 20). 🚨 **9 connectors NOT YET validated** —
      master plan assumes testnet wiring exists; deep audit found 0 testnet branch paths in execution-service. Owner:
      Agent 4 (CeFi side) + Agent 4 (DeFi side). Tenderly fork fixtures shipped DeFi-side per
      `execution-service/tests/integration/conftest.py`; CeFi side fully unvalidated.
  - DeFi: Aave / Uniswap / Lido (carry_staked_basis); Hyperliquid + Aster (leveraged_funding_arb on-chain leg)
  - CeFi: Bybit perp + Deribit options/perp + Binance perp + OKX perp (the four CeFi venues)
- [ ] Position-balance-monitor + risk-and-exposure + pnl-attribution: live mode validated. 🚨 **OWNER UNASSIGNED** —
      Risk 3 from deep audit. defi_master Fork 1 folded `defi_e2e_pipeline` but live-mode wiring sits as free-floating
      audit findings. PBM Pub/Sub + R&E intent-subscriber + pnl-attribution `--mode live` CLI all pending.
- [ ] Alerting-service: live rules fired on synthetic violations. **Blocked**: alerting Phase 2 (Agent 1 tab) — consumer
      wiring (`grep AlertCode alerting-service/` returns 0 hits as of 2026-05-07 evening). UAC AlertCode taxonomy
      shipped UAC@`d00326d`; rules engine integration is the gap.
- [ ] Live Deployment UI tab shipped (work-stream B). **Blockers**: codex SSOT
      `codex/05-infrastructure/live-deployment-monitoring.md` (still missing), deployment-api `/api/vm/events` endpoint
      (work-stream A Phase 2), deployment-ui `/ops/live-deployments` route. Owner: Harsh Day 4-5 + Agent 4.
- [ ] **AWS data migration completed** (DeFi-only, work-stream D.1) — data status works on both clouds. **Blocked**:
      `aws_migration_defi_first_2026_05_07` Phase 2 dual-bucket setup (Agent 4 Day 4); Phase 1.5.A bucket-name string
      parity audit; Phase 1.5.D `cloud-providers.yaml` parity (10 missing DeFi raw-data buckets identified).
- [ ] **AWS batch backfill `--force`** runs on a small DeFi window (work-stream D.2). **Blocked on D.1**.
- [ ] **AWS backtest + ML examples** run via deployment-api (work-stream D.3). **Blocked on D.2**.
- [ ] DART terminal in UTS-UI: archetype visualization + manual trade entry (work-stream C). **Blocked**:
      research-service repo decision (Week 1 above); UTS-UI `/research/ml-experiments` +
      `/research/strategy-backtests` + `/research/execution-backtests` tabs; work-stream A endpoints.
- [ ] Treasury: Copper integration validated; CEFFU manual handoff documented. **Blocked on Copper sandbox integration
      test (pending) + CEFFU subsection body in custody-providers.md** (stub shipped 2026-05-07 + folded into
      [`codex/04-architecture/custody-providers.md § 2.4 CeffuCustodyProvider — PLANNED`](../../codex/04-architecture/custody-providers.md)
      2026-05-08; content owners pending).

### Week 3 (May 20–23) · cutover (live trading + AWS live deployment)

- [ ] Real wallet funded testnet → mainnet
- [ ] DART manual-trade window: 3 days operator-monitored on `carry_staked_basis`
- [ ] Automation flip on `carry_staked_basis` → 7-day continuous run begins (extends past May 23 into May 30)
- [ ] `leveraged_funding_arb` enters DART manual-trade window (lags carry_staked_basis by ~2 days)
- [ ] **AWS live archetype** running in parallel — one carry_staked_basis instance on smaller capital deployed to AWS
      (work-stream D.4)
- [ ] **Seamless-switch test** between GCP-live ↔ AWS-live (work-stream D.4)
- [ ] Build-history tab in deployment-ui shipped (work-stream D.5)
- [ ] Batch-vs-live reconciliation matches within tolerance per archetype config (Group F item 21)

---

## Tracking surface

- [x] Plan promoted to `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.plan.md` (this file)
- [x] Audit companion at `unified-trading-pm/codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md` (pointer + drift
      table mirror)
- [x] Referenced from `CLAUDE.md` so every agent session loads it
- [ ] Per-service yamls at `codex/10-audit/repos/<service>.yaml` extended with the 7-group / 23-item structure for
      tier-1 services
- [ ] Update cadence: Tier-1 readiness rollup refreshed by EOD daily; critical-path DAG checked at start of each week
- No duplication: sub-plans in `plans/active/` remain authoritative; this plan only references and orchestrates

---

## Verification (end-to-end, the 23-item checklist instantiated)

**DeFi live (the headline goal)**

- [ ] `carry_staked_basis` cycle on real wallet (testnet → mainnet) via DART manual-trade lane → backend execution →
      automation flip → ≥7-day continuous run; P&L matches batch sim within configured bps tolerance per Group F item 21
- [ ] `leveraged_funding_arb` running across ≥3 perp venues with cross-venue funding spread captured

**Perp venue coverage**

- [ ] All 6 venues live: Bybit, Deribit, Binance, OKX, Hyperliquid, Aster — one trade each verified via deployment-UI

**Observability + guardrails**

- [ ] Tail VM event logs from deployment-UI without SSH for 24h on a live forward-poll VM
- [ ] Live alerting fires on synthetic data-freshness, P&L deviation, and position-breach violations injected via test
      fixtures
- [ ] Kill switch fires on synthetic risk-breach trigger

**Cloud parity (work-stream D)**

- [ ] DeFi-relevant data migrated to AWS S3 (manifest + parquet) with same shard layout as GCS
- [ ] AWS data status query works in deployment-UI and matches GCS truth
- [ ] AWS batch backfill `--force` produces parquet end-to-end
- [ ] AWS strategy backtest + ML training + execution backtest examples run via deployment-api
- [ ] AWS live carry_staked_basis instance running on smaller capital
- [ ] Seamless-switch (GCP-live → AWS-live → back) preserves position state via custody / position-balance-monitor

**Readiness rollup**

- [ ] All Tier-1 services pass 23/23 readiness checklist (or have explicit n/a justified) — verified per
      `codex/10-audit/repos/<service>.yaml`
- [ ] All 9 drift-audit rows resolved (none remaining `⚠`)
- [ ] `codex/00-SSOT-INDEX.md` updated to reference all new SSOT docs (work-streams D.6 + F)
- [x] `CLAUDE.md` cross-references this master plan in a new "Master Plan" section (verified 2026-05-07:
      .claude/CLAUDE.md line 22 has `## Master Plan — Live DeFi Trading by 2026-05-23` section)

---

## Critical files (read first, in this order)

| Purpose                                           | File                                                                                                                                     |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Codex master index                                | `unified-trading-pm/codex/00-SSOT-INDEX.md`                                                                                              |
| Cross-cutting principles (read before any change) | `unified-trading-pm/codex/POST_PLAN_REALITY_2026_05_06.md`                                                                               |
| Existing service-readiness SSOT                   | `unified-trading-pm/codex/10-audit/REPO_READINESS_CHECKLIST.yaml`, `_checklist-template-enhanced.yaml`, `repos/<service>.yaml`           |
| Batch=live design SSOT                            | `unified-trading-pm/codex/04-architecture/batch-live-pipeline.md`, `batch-live-symmetry.md`, `backtest-groups.md`                        |
| Shard granularity per asset-group                 | `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md`                                                              |
| UI surface SSOT                                   | `unified-trading-pm/codex/05-infrastructure/UI-FUNCTIONALITY-REQUIREMENTS.md`                                                            |
| Tarball deployment SSOT                           | `unified-trading-pm/codex/05-infrastructure/vm-tarball-deployment.md`                                                                    |
| Cloud-agnostic SSOT                               | `unified-trading-pm/codex/04-architecture/cloud-agnostic-migration.md`                                                                   |
| Lifecycle events SSOT                             | `unified-trading-pm/codex/03-observability/lifecycle-events.md`                                                                          |
| Strategy archetypes SSOT                          | `unified-trading-pm/codex/09-strategy/strategy-summary.md`                                                                               |
| Strategy onboarding                               | `unified-trading-pm/codex/09-strategy/cross-cutting/onboarding-checklist.md`                                                             |
| Operational modes (manual / paper / automated)    | `unified-trading-pm/codex/09-strategy/cross-cutting/operational-modes-matrix.md`                                                         |
| P&L attribution                                   | `unified-trading-pm/codex/09-strategy/cross-cutting/pnl-attribution.md`                                                                  |
| Alerting (batch + live)                           | `unified-trading-pm/codex/04-architecture/alerting-batch-live.md`                                                                        |
| Auto-recovery / kill switches                     | `unified-trading-pm/codex/04-architecture/autonomous-recovery-matrix.md`                                                                 |
| Custody (Copper + CEFFU)                          | `unified-trading-pm/codex/04-architecture/custody-providers.md` (single SSOT — Copper + CEFFU + LocalKey + Mock), `wallet-hierarchy-and-capital-flow.md` |
| Service control surface                           | `unified-trading-pm/codex/04-architecture/service-control-surface.md`                                                                    |
| Existing deployment-API                           | `deployment-api/deployment_api/routes/`                                                                                                  |
| Existing deployment-UI                            | `deployment-ui/src/pages/`                                                                                                               |
| Existing UTS-UI admin                             | `unified-trading-system-ui/app/(ops)/admin/`                                                                                             |
| Cross-cloud partial AWS                           | `deployment-api/deployment_api/routes/_code_builds_aws.py`, `deployment-service/buildspec.aws.yaml`                                      |
