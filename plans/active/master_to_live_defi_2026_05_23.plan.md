---
plan_type: meta
asset_group: cross-cutting
owner: ikenna
created: 2026-05-06
last_updated: 2026-05-06
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

# Master Plan — Live DeFi Trading by 2026-05-23

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
2. **`leveraged_funding_arb`** — cross-venue funding-rate spread trade. Locked plan:
   `defi_pipeline_extension_2026_05_01` (leveraged_leg_controller_2026_05_01 archived 2026-05-06; folded into
   `defi_e2e_pipeline_2026_04_30` — full plan shipped per memory project_leveraged_leg_controller_2026_05_01.md).

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
| **Custody / treasury wiring** (Copper, CEFFU)                                           | `codex/04-architecture/copper-custody-integration.md` · `custody-providers.md` · `wallet-hierarchy-and-capital-flow.md` · CEFFU doc (new, work-stream F) · `unified-config-interface/testnet_contracts.py` PROTOCOL_SCHEMAS                                                                                                                                                                                    |
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

| Area                                                            | Codex SSOT                                                                                                                                  | Sub-plans                                                                                                                                                              | Drift status                                                                                              | Resolve via                                                                                                                                                               |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Manifest schema (v6)                                            | `02-data/availability-manifest-and-data-status.md` (current)                                                                                | `manifest_schema_v6_quote_margin_combo_2026_04_23`, `availability_manifest_v4_and_data_status_2026_04_13`                                                              | ⚠ Confirmed — `availability_manifest_v4_…` is the only stale active plan; self-tagged superseded         | Archive the v4 plan via work-stream G; doc already canonical v6 with v4/v5 hive-key fallback                                                                              |
| Shard granularity propagation                                   | `02-data/availability-manifest-and-data-status.md` (multi-axis correction post-2026-05-06)                                                  | `shard_granularity_ssot_propagation_2026_05_06.HANDOVER`, `writegate_honest_coverage_endtoend_2026_05_06`, `data_status_multi_axis_shard_propagation_2026_05_06`       | ⚠ Confirmed — `writegate_…` declared umbrella; other two are children but not yet `parent:`-tagged       | Re-tag children with `parent: writegate_honest_coverage_endtoend_2026_05_06` (work-stream G); surface only umbrella                                                       |
| Cloud-agnostic VM/build                                         | `04-architecture/cloud-agnostic-migration.md`                                                                                               | (no active plan — work-stream D is the new one)                                                                                                                        | ⚠ Doc partially describes target; VM launchers GCP-only in code                                          | Add VM-launcher parity appendix to the doc; new plan for AWS launchers                                                                                                    |
| Live-mode services (PBM, R&E, P&L attr, alerting, B-vs-L recon) | Mostly covered by `04-architecture/alerting-batch-live.md`, `autonomous-recovery-matrix.md`, `09-strategy/cross-cutting/pnl-attribution.md` | ✓ REVISED — PBM/R&E/P&L attr in `defi_e2e_pipeline_2026_04_30` Fork 1; B-vs-L recon in `consolidated_operational_validation_2026_04_15`; only **alerting** has no plan | ⚠ Only alerting genuinely missing a plan                                                                 | Open `alerting-service-live-rules_2026_05_07.plan.md`; extend the 4 existing plans with explicit live-mode todos (work-stream E REVISED)                                  |
| Custody (Copper + CEFFU)                                        | `04-architecture/copper-custody-integration.md`, `custody-providers.md`, `wallet-hierarchy-and-capital-flow.md`                             | (no active plan; CEFFU not in codex)                                                                                                                                   | ⚠ CEFFU has no codex doc; integration unwritten                                                          | Add CEFFU codex doc + plan as part of work-stream F + E                                                                                                                   |
| Strategy v2 finalization                                        | `09-strategy/strategy-summary.md`, `architecture-v2/`                                                                                       | `strategy_architecture_v2_finalization_2026_04_19`, `strategy_architecture_v2_phase3_11_handoff_2026_04_17`                                                            | ⚠ Confirmed — finalization is live; handoff is historical (Phase 2 done)                                 | Mark handoff `parent_of: finalization`; verify residuals; archive once absorbed (work-stream G)                                                                           |
| DART / research-service                                         | `09-strategy/cross-cutting/operational-modes-matrix.md` (operational modes)                                                                 | `dart_ui_strategy_filtering_and_onboarding_2026_04_24` (self-tagged superseded), `dart_ux_cockpit_refactor_2026_04_29` (active superset)                               | ⚠ research-service has 0 repo, only PNG mockups; manual-trade lane not in codex                          | Archive DART UI plan; add `04-architecture/research-service-and-dart-integration.md`; extend operational-modes-matrix                                                     |
| ML experiment lifecycle                                         | `02-data/data-lineage-MTDS-features-ml.md` (partial)                                                                                        | `ml_pipeline_revolution_2026_04_11` (self-tagged superseded), `consolidated_ml_advanced_pipeline_2026_04_15` (active), `sp500_ml_readiness_master_2026_05_05`          | ⚠ No dedicated SSOT for ML job_id lifecycle; `ml_pipeline_revolution` should archive                     | Archive `ml_pipeline_revolution_2026_04_11` + `domain_agnostic_ml_framework_2026_04_11` (work-stream G); add `04-architecture/ml-experiment-lifecycle.md` (work-stream F) |
| Live observability / log streaming                              | `03-observability/lifecycle-events.md`, `coordination-events.md`                                                                            | (no active plan for GCS event-tail endpoint)                                                                                                                           | ⚠ Doc defines events; deployment-api endpoint doesn't exist                                              | Build endpoint as part of work-stream A; doc stays current                                                                                                                |
| **NEW (audit-discovered):** Plan frontmatter discipline         | `plans/PLAN_FORMAT.md`                                                                                                                      | n/a (workspace-wide systemic gap)                                                                                                                                      | ⚠ 95% missing `last_updated`, 96% missing `asset_group`, 21% missing `locked_by`, 5 plans no frontmatter | Workspace-wide one-shot backfill script (work-stream G)                                                                                                                   |
| **NEW (audit-discovered):** Service-overlap concentration       | n/a (master-plan tracking concern)                                                                                                          | 35 plans on instruments-service; 16 each on deployment-service / strategy-service / deployment-api; 12+ on UTS-UI / execution-service / deployment-ui                  | ⚠ Real overlap risk; consolidation candidate post-cutover                                                | Post-May-23 cleanup; not blocking. Document on master plan; address in next cycle                                                                                         |

**Audit guideline going forward.** Whenever an agent touches a row in this table, the PR includes a one-line "drift
status: resolved / unchanged / new-drift" note in the description. New drift = a new row gets added here.

---

## Audit — sub-plan conflicts, overlaps, stale references (VERIFIED 2026-05-06)

Two parallel agents (mechanical frontmatter + topic-map sweep ; content-overlap pass) audited the **148 active
sub-plans** on 2026-05-06. **Headline corrections to the earlier suspicion list:** 3 of the 5 "NO-PLAN" live-mode
services are actually already in scope of `defi_e2e_pipeline_2026_04_30` Fork 1 — only **alerting** genuinely needs a
new dedicated plan. **18 self-tagged superseded plans** should be archived. Frontmatter discipline is systemically
broken (95% missing `last_updated`, 96% missing `asset_group`, 21% missing `locked_by`) — needs a one-shot backfill
script.

### Plan clusters → surface ONE per cluster on the master plan

| Cluster                          | Lead / umbrella plan                                                                                                                         | Children (reference, not duplicate)                                                                                                                                                                                                                 | Action                                                                                                                          |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **DeFi end-to-end pipeline**     | `defi_e2e_pipeline_2026_04_30`                                                                                                               | `defi_pipeline_extension_2026_05_01` · `leveraged_leg_controller_2026_05_01` · `carry_staked_basis_structure_axis_2026_05_04` · `consolidated_defi_data_pipeline_2026_04_15` (residuals) · `defi_data_types_completeness_2026_04_24` (residuals)    | Surface only the lead on master plan; track children as sub-bullets. Archive `defi_full_coverage_expansion_2026_04_09`.         |
| **Write-gate / honest-coverage** | `writegate_honest_coverage_endtoend_2026_05_06` (umbrella; declares `supersedes_phases:` on shard-granularity Tier 1 #1 + Tier 2 raw-tables) | `shard_granularity_ssot_propagation_2026_05_06.HANDOVER` · `data_status_multi_axis_shard_propagation_2026_05_06` · `feature_dag_uac_ssot_and_features_coverage_2026_05_06` · `predictions_canonical_question_group_polymarket_migration_2026_05_06` | Re-tag children with `role: child` / `parent: writegate_…`; surface only the umbrella.                                          |
| **Sports phantom recovery**      | `sports_fixtures_truthset_recovery_2026_05_06` (active executor; declares `supersedes_phases:` on phantom-recovery relaunch + audit-flip)    | `sports_phantom_fixtures_recovery_2026_05_06` · `sports_phantom_recon_and_failure_triage_2026_05_01` (diagnostic context)                                                                                                                           | Surface only truthset; the others are background.                                                                               |
| **Strategy v2 finalization**     | `strategy_architecture_v2_finalization_2026_04_19` (live, supersedes `strategy_architecture_v2_2026_04_17`)                                  | `strategy_architecture_v2_phase3_11_handoff_2026_04_17` (historical, Phase 2 done)                                                                                                                                                                  | Surface only finalization; mark handoff `parent_of: finalization`.                                                              |
| **DART terminal / cockpit**      | `dart_ux_cockpit_refactor_2026_04_29` (active superset; supersedes codex `14-playbooks/dart/dart-terminal-vs-research.md`)                   | `dart_terminal_research_split_2026_04_28` (mechanics shipped)                                                                                                                                                                                       | Archive terminal-research-split.                                                                                                |
| **Marketing site**               | `marketing_site_three_route_consolidation_2026_04_26`                                                                                        | `marketing_homepage_old_hero_migration_2026_04_22` (homepage scope within route-consolidation) · `dart_ui_strategy_filtering_and_onboarding_2026_04_24` (self-tagged superseded)                                                                    | Archive DART UI plan; reference homepage as scope-of route-consolidation.                                                       |
| **Sports roadmap**               | `sports_roadmap_master_execution_2026_04_21` (10-plan parallel-execution master)                                                             | 4 explicit children (apifootball_enrichment_historical_backfill · non_apifootball_provider_backfill_launchers · features_sports_pipeline_deployment · sports_scheduler_cron_activation, all 2026-04-21)                                             | Surface master only; reconcile overlap with `sports_predictions_e2e_2026_05_05` + `features_sports_honest_coverage_2026_05_05`. |
| **Playbook SSOT**                | `playbook_ssot_stage_3_infra_spec_2026_04_19`                                                                                                | `_stage_2_doc_rewrite_2026_04_19` · `_stage_1_rules_2026_04_19` (correctly modeled with `depends_on` / `blocks`)                                                                                                                                    | Surface as one playbook-SSOT cluster.                                                                                           |
| **Asset-group vocabulary**       | `venue_axis_asset_group_vocabulary_2026_04_25` (parent)                                                                                      | `shard_dimension_naming_asset_group_ssot_2026_04_25` (declares "complements")                                                                                                                                                                       | **Merge** or formal child link.                                                                                                 |

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
   `carry_staked_basis_structure_axis_2026_05_04`, `defi_pipeline_extension_2026_05_01`,
   `leveraged_leg_controller_2026_05_01`.
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
5. ? **Manual-trade gating duration.** How many days of DART-driven manual trades before flipping to automation?
   Default: **3 days manual → 7 days automated**, with kill-switch monitoring throughout. Resolve before May 18.
6. ? **research-service repo decision.** Separate repo or fold into deployment-api? Default: **fold into
   deployment-api** unless scope grows. Resolve in Week 1.
7. ? **ML ladder targets per asset group by May 23.** Prediction → features-only, sports → ML, TradFi → ML, CeFi → ML,
   DeFi → no ML (rules-based). Default for May 23: prediction features done; sports/TradFi/CeFi ML pipelines _running_
   on representative sample (not necessarily _deployed_ in production). Confirm "running" vs "ready-to-run".
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
    pipeline hard-fails on every record_captured call.
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
| 5 NO-PLAN live-mode services to write + ship            | Medium                                 | Live trading without circuit breakers / live alerting / batch-vs-live recon = unsafe to flip    | RESOLVED post-2026-05-06 audit: only `alerting-service` is genuinely NO-PLAN; PBM / R&E / pnl-attribution extend `defi_e2e_pipeline_2026_04_30` Fork 1; B-vs-L recon extends `consolidated_operational_validation_2026_04_15` (work-stream E REVISED).                                                                                                                            |
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

17. **Backtest fidelity** — real gas, real market impact, realistic matching engine for AMM pools / perpetuals / spots /
    transfers / atomic transfers / flash loans; cost+yield to smallest precision (codex
    `04-architecture/backtest-groups.md`, `batch-live-symmetry.md`)
18. **2-year batch backtest run** — completed across config grid; P&L variance per archetype configuration captured so
    the live-trading config is informed, not guessed
19. **Treasury / custody integration** — Copper for DeFi side (codex `04-architecture/copper-custody-integration.md`);
    CEFFU for Binance institutional flow; cross-wallet transfer paths verified
20. **Live testnet replicates prod** — Tenderly fork / forked-mainnet for DeFi; Binance testnet / Bybit testnet for
    CeFi; same config code path, no faked data
21. **Reconciliation suite** — batch-vs-live reconciliation working (codex
    `09-strategy/cross-cutting/pnl-attribution.md` + `batch-live-reconciliation-service`); P&L attribution decomposed
    per source; per-trade reconciliation
22. **Trading guardrails** — circuit breakers configured per archetype; kill switches wired (codex
    `04-architecture/autonomous-recovery-matrix.md`); alerting-service rules cover live data-freshness + P&L deviation +
    position breaches (codex `04-architecture/alerting-batch-live.md`); auto-recovery for known transient failure
    classes

### Group G — Operator UX (live-only)

23. **DART manual-trade gate** — DART terminal in UTS-UI visualizes the strategy archetype end-to-end; operator first
    puts trades on manually → backend executes through the same path as automation → monitor for the gate window → flip
    switch to automation (codex `09-strategy/cross-cutting/operational-modes-matrix.md`)

> Per-service yamls in `codex/10-audit/repos/<service>.yaml` get extended to track items 4–23. Items 1–3 already in the
> existing repo readiness yaml are inherited.

---

## Service readiness matrix — current snapshot

Tier-1 services — every item must be ✓ by May 23. Group-level rollup (full 23-item detail in per-service yamls).

| Service                           | A·Code | B·Data | C·Runtime | D·Coverage | E·Ops | F·Trading | G·UX | Linked plans                                                                                                                                                     |
| --------------------------------- | ------ | ------ | --------- | ---------- | ----- | --------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| instruments-service               | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | instruments_and_market_tick_data_completion_2026_05_01 (instruments_service_orchestrator_reliability_fixes_2026_04_21 archived 2026-05-06)                       |
| market-tick-data-service          | ✓      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | market_tick_data_to_100pct_2026_05_05, instruments_and_market_tick_data_completion_2026_05_01 (mtds_canonical_sharding_alignment_2026_03_31 archived 2026-05-06) |
| market-data-processing-service    | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | instruments_and_market_tick_data_completion_2026_05_01 (data_pipeline_completion_2026_04_18 archived 2026-05-06; same epic, newer audit, strict superset)        |
| features-onchain-service          | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | consolidated_defi_data_pipeline_2026_04_15, defi_e2e_pipeline_2026_04_30                                                                                         |
| features-volatility-service       | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | feature_dag_uac_ssot_and_features_coverage_2026_05_06                                                                                                            |
| features-cross-instrument-service | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | features_consolidation_and_drilldown_2026_05_06                                                                                                                  |
| ml-training-service               | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | consolidated_ml_advanced_pipeline_2026_04_15, ml_training_feature_read_perf_2026_05_06 (ml_pipeline_revolution_2026_04_11 archived 2026-05-06)                   |
| ml-inference-service              | ◐      | ◐      | ◐         | n/a        | ◐     | n/a       | n/a  | consolidated_ml_advanced_pipeline_2026_04_15                                                                                                                     |
| strategy-service                  | ◐      | ◐      | ◐         | n/a        | ◐     | ✗         | ✗    | strategy_architecture_v2_finalization_2026_04_19, carry_staked_basis_structure_axis_2026_05_04                                                                   |
| execution-service                 | ◐      | ◐      | ◐         | n/a        | ◐     | ✗         | ✗    | defi_phase3_infrastructure_2026_03_30, leveraged_leg_controller_2026_05_01                                                                                       |
| position-balance-monitor-service  | ◐      | ◐      | ◐         | n/a        | ◐     | ◐         | n/a  | defi_e2e_pipeline_2026_04_30 Fork 1 (PBMS dual projection / fill attributor / child-venue attribution)                                                           |
| risk-and-exposure-service         | ◐      | ◐      | ◐         | n/a        | ◐     | ◐         | n/a  | defi_e2e_pipeline_2026_04_30 Fork 1 (R&E intent subscriber — extend with explicit live-wiring todo)                                                              |
| pnl-attribution-service           | ◐      | ◐      | ◐         | n/a        | ◐     | ◐         | n/a  | defi_e2e_pipeline_2026_04_30 Fork 1 (compute --mode batch CLI; extend with live-mode wiring todo)                                                                |
| alerting-service                  | ✗      | n/a    | ◐         | n/a        | ◐     | ✗         | n/a  | **(NO PLAN — only genuine gap; new plan needed)**                                                                                                                |
| batch-live-reconciliation-service | ✗      | n/a    | ◐         | n/a        | ◐     | ◐         | n/a  | consolidated_operational_validation_2026_04_15 (extend with live-cutover items)                                                                                  |
| deployment-api                    | ✓      | n/a    | ◐         | n/a        | ◐     | n/a       | n/a  | deployment_ui_e2e_uat_2026_04_01                                                                                                                                 |
| deployment-service                | ✓      | n/a    | ◐         | n/a        | ◐     | n/a       | n/a  | deployment_service_build_infrastructure_repair_2026_04_22                                                                                                        |
| deployment-ui                     | ✓      | n/a    | n/a       | n/a        | n/a   | n/a       | n/a  | data_status_offline_rollup_2026_05_06, data_status_ui_fixes_2026_05_06                                                                                           |
| unified-trading-system-ui         | ✓      | n/a    | n/a       | n/a        | n/a   | n/a       | n/a  | consolidated_strategy_and_ui_2026_04_15, dart_ui_strategy_filtering_and_onboarding_2026_04_24                                                                    |

> **Action:** Cell values seeded from session memory + sub-plan inventory + 2026-05-06 plan-vs-plan audit. Verify via
> per-service yamls in `codex/10-audit/repos/` before relying. Plan-vs-plan audit corrected the earlier "5 NO-PLAN"
> claim: PBMS / R&E / pnl-attribution are already in `defi_e2e_pipeline_2026_04_30` Fork 1 (extend, don't open new);
> batch-live-reconciliation folds into `consolidated_operational_validation_2026_04_15` (extend); only
> **alerting-service** genuinely needs a new plan.

### Tier 2 — backfill catch-up + ML readiness ladder (NOT live by May 23)

`features-sports-service` (→ ML), `features-calendar-service` (TradFi → ML), `features-delta-one-service` (TradFi → ML),
`features-commodity-service` (TradFi → ML). Group A–E required by May 23; Group F/G n/a until next archetype lands.

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

- [ ] [PLAN] Open `alerting-service-live-rules_2026_05_07.plan.md` — the only genuine NO-PLAN gap. Lock to
      `live-defi-rollout`. References checklist Groups F + G.
- [ ] [EXTEND] `defi_e2e_pipeline_2026_04_30` Fork 1 — add explicit todos for **position-balance-monitor live-mode
      wiring** (PBMS Pub/Sub + GCS contract; dual projection + fill attributor + child-venue attribution already shipped
      per plan body).
- [ ] [EXTEND] `defi_e2e_pipeline_2026_04_30` Fork 1 — add explicit **risk-and-exposure intent-subscriber live-wiring
      todo** (currently flagged as one of 5 wiring holes blocking live closure).
- [ ] [EXTEND] `defi_e2e_pipeline_2026_04_30` Fork 1 — add explicit **pnl-attribution `--operation compute --mode live`
      todo** alongside the existing batch CLI.
- [ ] [EXTEND] `consolidated_operational_validation_2026_04_15` — add explicit **batch-live-reconciliation live-cutover
      items** (matches plan's existing operational-validation surface; archive
      `manual_trade_booking_reconciliation_2026_03_22` which is self-tagged superseded by it).

### F · Codex SSOT gaps to fill alongside the work

- [ ] [DOC] `codex/05-infrastructure/live-deployment-monitoring.md` (work-stream B)
- [ ] [DOC] `codex/04-architecture/research-service-and-dart-integration.md` (work-stream C)
- [ ] [DOC] `codex/05-infrastructure/cloud-agnostic-build-lineage.md` (work-stream D)
- [ ] [DOC] `codex/04-architecture/ml-experiment-lifecycle.md` — ML job_id manifest separate from data manifest
- [ ] [DOC] `codex/04-architecture/live-strategy-config-hot-reload.md` — strategy config hot-reload end-to-end for live
      mode
- [ ] [DOC] CEFFU integration page in `codex/04-architecture/` (peer to `copper-custody-integration.md`)

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

- [ ] [SCRIPT] Workspace-wide script to populate missing `last_updated` from `git log` mtime (140 plans affected)
- [ ] [SCRIPT] Same script populates `asset_group` inferred from filename + body (142 plans affected)
- [ ] [SCRIPT] Same script populates `locked_by: live-defi-rollout` for the 31 plans missing it (verify each is actually
      mid-flight first; otherwise leave unset)
- [ ] [SCRIPT] Add YAML frontmatter to 5 plans that have none (`_sports_phantom_fixtures_recovery_handover_2026_05_06`,
      `dashboard_services_grid_collapse_2026_04_21`, `defi-strategy-ui-verification`, `tiered_help_chatbot_2026_03_22`,
      `universe_ssot_fix_2026_04_20`)
- [ ] [SCRIPT] Fix the 1 filename↔name mismatch (`path_to_100m_finalization_2026_04_20`)
- [ ] [SCRIPT] Fix the 2 YAML errors

**Re-tag children of cluster umbrellas:**

- [ ] [SCRIPT] Add `parent: writegate_honest_coverage_endtoend_2026_05_06` to the 4 child plans
- [ ] [SCRIPT] Add `parent: defi_e2e_pipeline_2026_04_30` to defi_pipeline_extension / leveraged_leg_controller /
      carry_staked_basis where appropriate
- [ ] [SCRIPT] Add `parent: sports_fixtures_truthset_recovery_2026_05_06` to phantom-recovery + recon plans
- [ ] [SCRIPT] Merge or formal child-link `shard_dimension_naming_asset_group_ssot_2026_04_25` under
      `venue_axis_asset_group_vocabulary_2026_04_25`

---

## Critical-path DAG (May 6 → May 23)

### Week 1 (May 6–12) · foundations close + tier-1 services pass Groups A–E + AWS migration starts

- [ ] Close shard-granularity propagation (designate one of the 3 plans as the SSOT)
- [ ] Close TradFi MVP residuals (cluster-validation wiring at `record_captured`)
- [ ] Close DeFi data-pipeline blockers (features-onchain LookaheadBiasError + lending_rates write-gate)
- [ ] Close sports phantom recovery — frees VM-quota for DeFi + AWS work
- [ ] **Open 1 alerting plan + extend 4 existing plans** (revised post-2026-05-06 audit; see work-stream E for details:
      PBMS / R&E / pnl-attribution extend `defi_e2e_pipeline_2026_04_30`; batch-live-recon extends
      `consolidated_operational_validation_2026_04_15`)
- [ ] **Plan hygiene sweep (Day 1 quick-win)** — archive 18 self-tagged superseded plans; backfill missing frontmatter
      (`last_updated` / `asset_group` / `locked_by` / 5 plans with no frontmatter at all); re-tag cluster children with
      `parent:` field — work-stream G
- [ ] Ship deployment-api `/api/backfill/launch` + `/api/vm/events` (work-stream A)
- [ ] Decide research-service repo question (work-stream C)
- [ ] AWS migration cost analysis (work-stream D.1) → user signs off scope
- [ ] Sports / TradFi / CeFi ML pipelines reach "running on representative sample" milestone (parallel — tier 2 ladder)
- [ ] Hyperliquid + Aster perp DEX integration: instrument registry + market-data live (these don't have CEFFU
      equivalents — direct on-chain)

### Week 2 (May 13–19) · live wiring + cloud parity + Groups F/G

- [ ] `carry_staked_basis` runs end-to-end in batch with `always_fill` + matching-engine fills (Group F item 17)
- [ ] `leveraged_funding_arb` runs end-to-end in batch — cross-venue funding spread across 6 perp venues
- [ ] 2-year P&L variance batch run completed across config grid for both archetypes (Group F item 18)
- [ ] Execution-service connectors validated on testnet:
  - DeFi: Aave / Uniswap / Lido (carry_staked_basis); Hyperliquid + Aster (leveraged_funding_arb on-chain leg)
  - CeFi: Bybit perp + Deribit options/perp + Binance perp + OKX perp (the four CeFi venues)
- [ ] Position-balance-monitor + risk-and-exposure + pnl-attribution: live mode validated
- [ ] Alerting-service: live rules fired on synthetic violations
- [ ] Live Deployment UI tab shipped (work-stream B)
- [ ] **AWS data migration completed** (DeFi-only, work-stream D.1) — data status works on both clouds
- [ ] **AWS batch backfill `--force`** runs on a small DeFi window (work-stream D.2)
- [ ] **AWS backtest + ML examples** run via deployment-api (work-stream D.3)
- [ ] DART terminal in UTS-UI: archetype visualization + manual trade entry (work-stream C)
- [ ] Treasury: Copper integration validated; CEFFU manual handoff documented

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
- [ ] `CLAUDE.md` cross-references this master plan in a new "Master Plan" section

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
| Custody (Copper)                                  | `unified-trading-pm/codex/04-architecture/copper-custody-integration.md`, `custody-providers.md`, `wallet-hierarchy-and-capital-flow.md` |
| Service control surface                           | `unified-trading-pm/codex/04-architecture/service-control-surface.md`                                                                    |
| Existing deployment-API                           | `deployment-api/deployment_api/routes/`                                                                                                  |
| Existing deployment-UI                            | `deployment-ui/src/pages/`                                                                                                               |
| Existing UTS-UI admin                             | `unified-trading-system-ui/app/(ops)/admin/`                                                                                             |
| Cross-cloud partial AWS                           | `deployment-api/deployment_api/routes/_code_builds_aws.py`, `deployment-service/buildspec.aws.yaml`                                      |
