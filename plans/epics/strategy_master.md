---
doc_type: epic
title: Strategy Master (L2)
summary: >-
  L2 everlasting epic owning strategy-service post-2026-05-19 consolidation (engine + portfolio_allocator + risk +
  position + pnl + 59 archetype engines (was: 53 — see 2026-07-12 count-drift note in "Scope inherited" below)),
  per-client subprocess isolation, and archetype lifecycle; inherits the strategy side of the split
  strategy_and_dart_master umbrella (v2 factory cutover, shadow deployment registry/ledger, capability gaps,
  cross-domain alpha). Also owns (folded 2026-08-18) the DART operator UX cockpit + promote workflow, and the
  global-ledger + PnL-attribution architecture, both formerly separate 0-reference epics.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    client-reporting-api,
    deployment-api,
    deployment-ui,
    execution-service,
    greeks-service,
    instruments-service,
    strategy-service,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags:
  [
    strategy,
    defi,
    execution,
    consolidation,
    reconciliation,
    ssot-audit,
    ui,
    live-trading,
    verification,
    observability,
    uac,
    data-correctness,
    client-isolation,
  ]
related:
  [
    ../active/capability_wizard_and_manifest_2026_06_11.md,
    ../active/compute_optimization_mock_data_2026_05_13.md,
    ../archive/2026_05/config_grid_archetype_extend_2026_05_20.md,
    ../active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md,
    ../active/defi_recursive_borrow_archetypes_2026_05_10.md,
    ../archive/2026_05/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md,
    ../archive/2026_05/strategy_archetype_taxonomy_2026_05_12.md,
    ../archive/2026_05/strategy_execution_contract_remediation_2026_05_20.md,
    ../archive/2026_05/strategy_repo_consolidation_2026_05_19.md,
    ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md,
    ../active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/epics/dart_and_promote_master.md,
    /plans/epics/global_ledger_pnl_attribution_master.md,
  ]
created: 2026-05-21
name: strategy_master
tier: L2
priority: P0
assigned_vm: vm-trading-core
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
  - ../active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md
  - ../active/carry_staked_basis_funding_scan_experiment_2026_06_16.md
  - ../active/carry_strategy_ensemble_productionization_2026_07_24.md
  - ../archive/2026_08/cefi_satellite_ao_dispatch_batch13_2026_08_09.md
  - ../archive/2026_08/cefi_satellite_ao_dispatch_batch13_2026_08_09_finalize.md
  - ../active/cross_venue_funding_reversion_research_2026_07_24.md
  - ../active/crypto_alpha_research_2026_07_24.md
  - ../active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md
  - ../archive/2026_08/family2_position_registry_unwind_consumption_2026_08_09.md
  - ../active/l2_book_microstructure_capture_2026_07_13.md
  - ../active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md
  - /plans/archive/2026_08/strategy_service_family2_close_unwind_emission_2026_08_09.md
  - ../active/v2_engine_venue_buildout_2026_06_15.md
last_updated: 2026-08-18 # was 2026-06-11 -- folded dart_and_promote_master + global_ledger_pnl_attribution_master in 2026-08-18, see body
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Strategy Master (L2)

> **🟡 IN-FLIGHT REFACTOR — UTL/UAC reuse consolidation** (guardrails phase:
> [`utl_reuse_phase0_guardrails_2026_07_13`](../archive/2026_07/utl_reuse_phase0_guardrails_2026_07_13.md); compose
> phases: `utl_reuse_phase1_strategy_risk_hwm_2026_07_13` (strategy risk/HWM),
> `utl_reuse_phase3_ml_model_registry_2026_07_13` (ml ModelRegistry),
> `utl_reuse_phase4_features_builder_registry_2026_07_13` (features builder_registry)). Concurrent slots: do not
> re-touch the strategy risk-eval, ml-registry, or features-builder-registry surfaces until those phase plans land —
> check them first.

**Owns**: strategy-service post-consolidation 2026-05-19 (engine + portfolio_allocator + risk + position + pnl + 59
(was: 53) archetype engines); per-client subprocess isolation; archetype lifecycle. Also owns (folded 2026-08-18,
see below): the DART operator UX cockpit + promote workflow, and the global-ledger + PnL-attribution architecture.

**Assigned VM**: `vm-trading-core` (co-located with `execution_master` + trading-agent-service scope, now under
`execution_master`).

## Scope inherited from `strategy_and_dart_master_SUPERSEDED_2026_05_21` (split 2026-05-21)

The pre-2026-05-21 `strategy_and_dart_master` umbrella was split into two everlasting epics. **This epic owns the
strategy side**:

- **Archetype engine v2 finalization** — factory cutover, shadow deployment registry + ledger, 18-archetype shadow
  observation, capability gaps (SOR, hold-policy mixin, transfer-rebalance integration, benchmark-fills, dated-future
  roll, IM/Trading allocator split).
- **Cross-domain alpha + strategy lifecycle visibility** — UAC schemas + UTL SLA engine + DataQualityScorer +
  cross-domain calc + DeFi alpha features + execution cost prediction.
- **59 archetypes** (was: 53) per `codex/09-strategy/architecture-v2/archetypes/` — NOT a fixed constant: the count is a
  live code figure that grew 53→55→57→58→59 between 2026-06-01 and 2026-06-22 as new archetypes landed (verified against
  `unified-api-contracts` `StrategyArchetype` enum on `live-defi-rollout` HEAD as of 2026-07-12 — 59 members, docstring
  self-declares "59 archetypes"; last addition `TSMOM_BTC_CTA` @61ac3ad2 2026-06-22). Only 28 engines are implemented
  for the May-23 rollout subset (F-34 below, operator decision 2026-06-01) — taxonomy-count and implemented-engine-count
  are different numbers, do not conflate. [Doc-reconciliation 2026-07-12, findings 287/290/294/333/295, §A2 B-queue
  ruling — `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`.]
- **Portfolio allocator** + risk_rules + position-balance-monitor + pnl-attribution (consolidated into strategy-service
  2026-05-19).

DART operator UX + promote workflow scope was originally split out to a separate `dart_and_promote_master.md` (L3)
epic — **folded back into this file 2026-08-18** (see "Folded-in epic: DART + Promote Workflow Master" below; that
epic had accrued 0 corpus references since its 2026-05-21 creation). Full archaeology:
[`strategy_and_dart_master_SUPERSEDED_2026_05_21.md`](strategy_and_dart_master_SUPERSEDED_2026_05_21.md).

## Codex SSOTs

- [`codex/09-strategy/architecture-v2/`](../../codex/09-strategy/architecture-v2/) — strategy v2 SSOT (archetype count
  is a live code figure, see the "59 archetypes (was: 53)" note above — 7 axes + 11 cross-cutting + 2 architecture docs;
  corrected 2026-08-10 to drop the stale hardcoded "53" this same section's own remedy warns against restating)
- [`/codex/04-architecture/shadow-deployment-pattern.md`](/codex/04-architecture/shadow-deployment-pattern.md) — shadow
  window contract for archetype builds
- [`/codex/11-project-management/epic-execution-with-sub-agents.md`](/codex/11-project-management/epic-execution-with-sub-agents.md)
  — epic-flow SSOT (pointer to [`README.md`](README.md))

## Composition with other epics

- **Upstream**: `mtds_mdps_master` (raw market data) + `features_and_ml_master` (features + ML inference) +
  `instruments_master` (universe SSOT) + `manifest_master` (data completeness gate)
- **Downstream**: `execution_master` (handlers + transfers + the closed-loop allocator/directive scope folded there
  from `trading_agent_master`)
- **Operator surfaces**: this epic's own DART + promote workflow scope (folded 2026-08-18, below) consumes strategy
  maturity phases directly
- **Cross-cutting**: `client_isolation_and_governance_master` (per-client isolation + share-class registry +
  jurisdiction restrictions affect strategy emit)

## Assigned active plans

_13 active plans declare `parent_epic: strategy_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

_(no plans currently assigned at this priority)_

## P1 — important; post-current-gate

### [`capability_wizard_client_lite_and_ci_regen_followup_2026_07_24`](../active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md)

**status**: active · **estimate**: 1.0 cal AI-days (class: brand-new) **title**: Capability wizard — client-lite
successor + CI-runner openapi regen follow-up

### [`carry_staked_basis_funding_scan_experiment_2026_06_16`](../active/carry_staked_basis_funding_scan_experiment_2026_06_16.md)

**status**: active · **estimate**: 3.6 cal AI-days (class: research) **title**: carry_staked_basis funding-carry scan —
exploratory analysis harness + journal

### [`carry_strategy_ensemble_productionization_2026_07_24`](../active/carry_strategy_ensemble_productionization_2026_07_24.md)

**status**: active · **estimate**: 3.6 cal AI-days (class: research) **title**: carry_staked_basis — ensemble
orchestrator engine + strategy-service productionization

### [`crypto_alpha_research_2026_07_24`](../active/crypto_alpha_research_2026_07_24.md)

**status**: active · **estimate**: 18 cal AI-days (class: research) **title**: Crypto Alpha Research — Book
Construction, Signal Research & Paper-Trading POC

### [`recursive_loop_orchestrator_wiring_finalize_2026_08_09`](../active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md)

**status**: active · **estimate**: 0.2 cal AI-days (class: refactor) **title**: Finalize — RecursiveLoopOrchestrator
wiring plan reconciliation + archival

## P2 — useful; opportunistic

### [`cefi_satellite_ao_dispatch_batch13_2026_08_09`](../archive/2026_08/cefi_satellite_ao_dispatch_batch13_2026_08_09.md)

**status**: complete · **estimate**: 0.48 cal AI-days (class: infra) **title**: CeFi satellite AO batch 13 — item-level
extraction from 19 non-qualifying NA docs (strategy_master group)

### [`cefi_satellite_ao_dispatch_batch13_2026_08_09_finalize`](../archive/2026_08/cefi_satellite_ao_dispatch_batch13_2026_08_09_finalize.md)

**status**: complete · **estimate**: 0.24 cal AI-days (class: infra) **title**: CeFi satellite AO batch 13 — finalize
(reconcile source docs + archive)

### [`cross_venue_funding_reversion_research_2026_07_24`](../active/cross_venue_funding_reversion_research_2026_07_24.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: research) **title**: carry_staked_basis — cross-venue
funding-reversion research (Pass-B reconciliation + deployable book)

### [`defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17`](../active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md)

**status**: active · **estimate**: 18.0 cal AI-days (class: brand-new) **title**: Collateral-aware sizing +
opportunity-checker + wizard full-parameterization

### [`l2_book_microstructure_capture_2026_07_13`](../active/l2_book_microstructure_capture_2026_07_13.md)

**status**: active · **estimate**: 5.0 cal AI-days (class: brand-new) **title**: Deeper-Than-L5 Order Book Capture —
populate queue_position_* for MARKET_MAKING_QUEUE_MICROSTRUCTURE

### [`strategy_service_family2_close_unwind_emission_2026_08_09`](/plans/archive/2026_08/strategy_service_family2_close_unwind_emission_2026_08_09.md)

**status**: complete · **estimate**: 0.6 cal AI-days (class: design) **title**: Family-2 (CARRY_BASIS_PERP_INV)
close/unwind instruction emission — strategy-service

### [`v2_engine_venue_buildout_2026_06_15`](../active/v2_engine_venue_buildout_2026_06_15.md)

**status**: active · **estimate**: 66.0 cal AI-days (class: research) **title**: v2 Engine + Venue Build-Out — 22
engineless archetypes + 9 unwired venues

## P3 — backlog; revisit quarterly

### [`family2_position_registry_unwind_consumption_2026_08_09`](../archive/2026_08/family2_position_registry_unwind_consumption_2026_08_09.md)

**status**: active · **estimate**: 0.2 cal AI-days (class: refactor) **title**: Family2PositionRegistry — consume the
Family-2 close/unwind event once it exists

## Folded-in epic: DART + Promote Workflow Master (folded 2026-08-18)

**Source**: [`dart_and_promote_master.md`](dart_and_promote_master.md) (0 corpus references) — folded into this
epic per
[`/codex/11-project-management/epic-taxonomy-2026-08-18.md`](/codex/11-project-management/epic-taxonomy-2026-08-18.md)
(domain 3, Strategy service). The source file is kept as archaeology, `status: superseded`, with a banner pointing
here — do not add new work there.

**Owns**: DART operator UX cockpit + `ManualTradeGateDialog` + promote workflow (CLI primary + UI secondary) +
strategy lifecycle state machine + `MinimalCandidateManifest` (UAC) + Firebase `execution-full` enforcement.

**Assigned VM**: `vm-operator-ops` (co-located with `deployment_and_user_management_master`).

**Repos**: alerting-service, deployment-api, deployment-ui, unified-trading-system-ui.

### Scope inherited from `strategy_and_dart_master_SUPERSEDED_2026_05_21` (split 2026-05-21) — the DART/promote side

The pre-2026-05-21 `strategy_and_dart_master` umbrella was split into two everlasting epics. This section carries
the **DART + promote side** (the strategy-archetype side lives above, in "Scope inherited from
`strategy_and_dart_master_SUPERSEDED_2026_05_21`" — both halves of the original split now live in this one file):

- **DART operator UX cockpit** (was `dart_ux_cockpit_refactor`) — 9-phase programme collapsing DART from a route tree
  into a guided cross-asset trading cockpit. 9 phases + Configuration lifecycle UI surfaces + persona walkthrough
  Playwright matrix + Phase 1A/1B foundational primitives shipped. 7 open polish items: widget vocabulary SSOT,
  cross-cutting widget conventions, Layer-2 minimum proof signals, v2 archetype-expansion roadmap, doc alignment, IR
  copy alignment, public website copy alignment.
- **Promote workflow May-23 dual-track** — CLI primary (`run-paper.sh` → `colocated_engine.py` → `run-live.sh`) + UI
  secondary (Promote button → `MinimalCandidateManifest` in Firestore → paper/live VM auto-launch → DART
  `ManualTradeGateDialog` first 3 trading days). Valid May-23 transitions: `CANDIDATE → PAPER_1D → LIVE_EARLY`.
- **Promote workflow post-cutover UI pipeline** — full state-machine consolidation + candidate manifest enrichment
  (pinned shas, model refs, features manifest version) + Firebase backend integration.
- **UI walkthrough audit + persona walkthrough matrix** — every live action replicable as manual operator action.

Full archaeology:
[`strategy_and_dart_master_SUPERSEDED_2026_05_21.md`](strategy_and_dart_master_SUPERSEDED_2026_05_21.md).

### DART UI Verification Contract (HARD RULE — codified 2026-05-23)

All active plans under this epic that touch any UI repo (`unified-trading-system-ui`, `deployment-ui` — was: also
`user-management-ui`; ARCHIVED 2026-05, folded into `unified-trading-system-ui` per
`/codex/04-architecture/runtime-deployment-topology.md` + CLAUDE.md's system map) MUST pass the playwright
verification gate before any todo is ticked done. Per `plans/PLAN_FORMAT.md` § 9 and
`/codex/06-coding-standards/ui-testing-layers.md` § "Plan-Level Enforcement":

- **`[UI]` tag**: every UI-touching todo MUST use `[AGENT][UI]` or `[HUMAN][UI]` (not bare `[AGENT]`).
- **pw:L2 ✓**: `npx playwright test --project=chromium tests/smoke/` exits 0 before tick.
- **regression guard**: spec written/updated in `tests/e2e/`, `tests/playbooks/`, `tests/widgets/`, or `tests/smoke/`
  matched to the change layer (widget→L1.5, route→L2, playbook flow→L3a, strategy execute→L3b, visual→L4).
- **Evidence format**: `— repo@sha | pw:L2 ✓ | regression: tests/path/spec.ts` appended to tick line.
- **Reviewer rejects** ticks missing `pw:` or `regression:` — same weight as a missing `docs(plans):` flip.

Key DART/promote surfaces and their required layers:

| Surface                        | Layer | Regression guard path                            |
| ------------------------------- | ----- | -------------------------------------------------- |
| ManualTradeGateDialog          | L3a   | `tests/playbooks/promote_workflow.spec.ts`       |
| Promote button → API call      | L3a   | `tests/playbooks/promote_workflow.spec.ts`       |
| DART cockpit route loads       | L2    | `tests/smoke/routes.spec.ts`                     |
| Strategy lifecycle state chip  | L1.5  | `tests/widgets/strategy-lifecycle-chip.test.tsx` |

### DART/promote Codex SSOTs

- [`/codex/04-architecture/promote-workflow-architecture.md`](/codex/04-architecture/promote-workflow-architecture.md) —
  CLI + UI promote tracks + state machine + candidate manifest
- [`/codex/09-strategy/operational/cli-promote-paths.md`](/codex/09-strategy/operational/cli-promote-paths.md) — CLI
  dispatch pattern
- [`codex/14-customer-journeys/dart/`](../../codex/14-customer-journeys/dart/) — DART terminal vs research playbook

### DART/promote composition with other epics

- **Upstream**: this epic's own strategy-archetype scope (strategy lifecycle phases drive promote eligibility) +
  the closed-loop allocator scope folded into `execution_master` from `trading_agent_master` (emits
  `AllocationDirective` consumed by promote)
- **Downstream**: `execution_master` (promote-acked instructions flow to execution)
- **Co-located VM**: `deployment_and_user_management_master` (deployment-api Promote button + Firebase auth)
- **Cross-cutting**: `client_isolation_and_governance_master` (manual-trade gate enforces per-client +
  per-jurisdiction)

### DART/promote assigned active plans

None declared `parent_epic: dart_and_promote_master` at fold time — new work in this area now declares
`parent_epic: strategy_master`.

### DART/promote archived plans

#### [`promote_workflow_may23_cli_path_2026_05_10`](../archive/2026_05/promote_workflow_may23_cli_path_2026_05_10.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phase 1 complete; Phases 3-10 and Phase 2 VM smoke deferred.

**Deferred (migrated):**

- **Phases 3-10 (DEFERRED-POST-CUTOVER)**: Full promote-workflow pipeline (Firestore MinimalCandidateManifest write,
  paper VM auto-launch, ManualTradeGateDialog integration, live VM auto-launch, LIVE_EARLY→LIVE graduation,
  multi-tenant flow H4) — all gated on DeFi 7-day soak.
- **Phase 2 smoke VM verification (DEFERRED-OPERATOR)**: Requires `vm-operator-ops` launch to validate CLI promote
  path end-to-end.
- **MinimalCandidateManifest enrichment (DEFERRED-POST-CUTOVER)**: Pinned shas, model refs, features manifest
  version fields.
- **LifecycleEventType UAC enum (DEFERRED-POST-CUTOVER)**: Extend once this epic's strategy lifecycle state machine
  settled.

#### [`promote_workflow_post_cutover_ui_pipeline_2026_05_10`](../archive/2026_05/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)

**status**: ✅ ARCHIVED 2026-05-23 — Entire plan DEFERRED-POST-CUTOVER (gated on DeFi 7-day live soak).

**Deferred (migrated):**

- **All 12 phases (DEFERRED-POST-CUTOVER)**: Firebase `execution-full` enforcement, Promote button UI pipeline,
  state-machine consolidation, candidate manifest enrichment, Firestore backend integration, Playwright e2e matrix —
  all blocked until DeFi goes live and completes 7-day soak.

## Folded-in epic: Global Ledger + PnL Attribution Master (folded 2026-08-18)

**Source**: [`global_ledger_pnl_attribution_master.md`](global_ledger_pnl_attribution_master.md) (0 corpus
references) — folded into this epic per
[`/codex/11-project-management/epic-taxonomy-2026-08-18.md`](/codex/11-project-management/epic-taxonomy-2026-08-18.md)
(domain 3, Strategy service). The source file is kept as archaeology, `status: superseded`, with a banner pointing
here — do not add new work there.

**Owns**: the canonical ledger architecture from which position, exposure, PnL, and PnL-attribution are all derived.
Four SSOT ledgers (Instruction / Passive / Treasury / Pricing) authored by execution-service + strategy-service +
MTDS + instruments-service; four derived materialised views (Position / Exposure / PnL / PnLAttribution) computed in
strategy-service `position/` + `risk/` + `pnl/` + `portfolio_allocator/`; one RiskView consumed by alerting-service.

**Repos**: alerting-service, client-reporting-api, execution-service, greeks-service, instruments-service,
strategy-service.

**Status (2026-05-23, corrected 2026-07-12)**: UAC schemas SHIPPED — `LedgerRow` + 5 enums (`EventOrigin`,
`EventType` 39 values, `AssetClass` 17 values, `Direction`, `OptionRight`) + `CrossClientTransferForbiddenError`
validator landed in `unified_api_contracts.canonical.crosscutting.ledger/`. Discovery plan 36/38 BACKED + 2/38
PARTIAL (Phase 2 enum expansion + Phase 6 TreasuryLedger split — closed by enum expansion + recorded decision;
operator [ack] landed 2026-05-23, `unified-trading-pm@351a47b61`). Migration plan itself stayed 0/27 (all items
DEFERRED-OPERATOR-DECISION at archival), but the SAME Phase 7/8 scope (InstructionLedger/PricingLedger/TransferLedger
writers + paper-mode PassiveLedger synthesiser) SHIPPED via a separate, operator-commissioned plan
([`citadel_paper_batch_live_reconciliation_2026_06_19`](../active/citadel_paper_batch_live_reconciliation_2026_06_19.md),
`parent_epic: batch_live_symmetry_master`):

- **Phase 7 (InstructionLedger writer)**: `unified-trading-library@41d50461`
  `unified_trading_library/ledger/run_writer.py` (`write_run_ledger` / `write_run_pricing_ledger` /
  `write_run_transfer_ledger` / `write_run_passive_ledger`, all four `ledger_type=` GCS writers) wired live via
  `strategy-service/strategy_service/engine/backtest/ledger_emit.py::write_paper_run`. A related but distinct
  artifact, `execution-service/execution_service/pnl_attribution/rows.py::build_attribution_rows`
  (`execution-service@a4145838`→`49f42f77`, tested `tests/unit/pnl_attribution/test_build_attribution_rows.py`)
  builds the derived `PnLAttributionRow` factor×layer decomposition — real and shipped, though it is the
  PnLAttribution DERIVED view, not the InstructionLedger SSOT write path itself.
- **Phase 8 (PassiveLedger synthesiser), paper/backtest leg**: shipped
  (`strategy-service/strategy_service/engine/backtest/paper_run_passive.py`, `build_paper_run_passive` /
  `emit_paper_run_passive`, tested `tests/unit/engine/backtest/test_paper_run_passive.py`) — constructs real
  `event_origin=PASSIVE` canonical `LedgerRow`s (STAKING_REWARD / LENDING_INTEREST / FUNDING_ACCRUAL). **Genuine
  residual gap, carried forward as open scope**: the LIVE (non-paper) per-event divergence-check listener (the
  PassiveLedger synthesiser running inside `StrategySupervisor` per-client subprocess) is NOT shipped — no live
  on-chain/venue-emission listener found in strategy-service as of the 2026-07-12 re-audit.
- **Residual gap — `ledger_type=treasury` partition**: the acked separate-partition decision (writer =
  fund-administration-service) is still UNIMPLEMENTED at HEAD (zero code hits for `ledger_type=treasury` across UTL
  / strategy-service / execution-service / fund-administration-service / client-reporting-api); the
  `ledger_type=transfer` run tape that DID ship (`write_run_transfer_ledger`) is an adjacent, run-scoped paper-run
  construct, not that treasury SSOT.
- **Phase 9 (DART / client-reporting-api / alerting-service reader refactor)**: consumes PnL + PnLAttribution;
  DEFERRED-POST-CUTOVER (gate: Phase 7/8), plausible as genuinely still-deferred given Phase 7/8's partial state —
  not independently re-verified in the 2026-07-12 re-audit.

### Global-ledger codex SSOTs

| Doc                                                                    | Owns                                                                                                                                                                       |
| ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/codex/04-architecture/global-ledger-architecture.md`                 | 4-SSOT-+-4-derived ledger model; universal PnL recipe; ownership table; per-service writer/reader gap status                                                             |
| `/codex/02-data/ledger-event-taxonomy.md`                              | `EventOrigin` / `EventType` (39) / `AssetClass` (17) / `Direction` / `OptionRight` enum SSOT + routing summary + invariant tables                                        |
| `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`  | Carry-as-theta-family attribution framing; ledger→factor decomposition (delta/gamma/theta/vega/carry/funding/settlement/residual)                                        |
| `/codex/04-architecture/client-funds-isolation.md`                     | Cross-client transfer HARD RULE — `client_id == counterparty_client_id` on every transfer/bridge row                                                                     |

All 4 docs verified present at HEAD, `status: current`, non-stub, as of the 2026-07-12 re-audit.

### Global-ledger cross-epic handshakes

| Partner epic                                               | Handshake                                                                                                          |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| `execution_master`                                          | InstructionLedger + PassiveLedger writers (`attribution_builder.build_attribution_rows`); emits via writegate path |
| this epic (`strategy_master`)                                | Derived-ledger compute (`strategy_service/{position,pnl,risk,portfolio_allocator}/`); PassiveLedger synthesiser    |
| `mtds_mdps_master`                                           | PricingLedger writes (`MARK_UPDATE` rows with mid/bid/ask/IV/greeks); carry-rate emission                          |
| `instruments_master`                                         | Instrument metadata for passive-event synthesis (expiry / funding interval / rebase schedule / `exercise_style`)  |
| `client_isolation_and_governance_master`                     | UAC schema governance + cross-client funds isolation HARD RULE validator                                           |
| `observability_master`                                       | RiskView consumes PassiveLedger LIQUIDATION/SLASHING rows for alerting                                             |
| this epic (`dart_and_promote_master` scope, folded above)    | DART consumes PnL + PnLAttribution for promote workflow decisions                                                  |

### Global-ledger assigned active plans

None declared `parent_epic: global_ledger_pnl_attribution_master` at fold time — new work in this area now declares
`parent_epic: strategy_master`.

### Global-ledger archived plans

#### [`global_ledger_pnl_attribution_discovery_2026_05_21`](../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md)

**status**: ✅ ARCHIVED 2026-05-23 — 36/38 BACKED + 2/38 PARTIAL; UAC schemas shipped; operator [ack] landed
2026-05-23 (`unified-trading-pm@351a47b61`) on Phase 3 (late-arriving-data → Option A event-sourced append-only),
Phase 5 (greeks home → new `greeks-service/` repo), Phase 6 (TreasuryLedger split → separate
`ledger_type=treasury/client_id={cid}/` partition, writer = fund-administration-service — still unimplemented, see
Status above). Codex SSOT docs (`global-ledger-architecture.md` + `ledger-event-taxonomy.md` + `pnl-attribution.md`)
all exist, `status: current`, non-stub.

#### [`global_ledger_pnl_attribution_migration_2026_06_01`](../archive/2026_05/global_ledger_pnl_attribution_migration_2026_06_01.md)

**status**: ✅ ARCHIVED 2026-05-23 — Stub plan; 0/27 items implemented through this plan's own gate (all
DEFERRED-OPERATOR-DECISION at archival time). The Phase 7/8 scope it deferred shipped anyway via the separate
Citadel plan (see Status above) — see that plan's own record for the ack + shipped-evidence detail; not re-derived
here.

### Global-ledger VM assignment notes

Ran on `vm-trading-core` co-located with `execution_master` + this epic + (formerly) `trading_agent_master` (now
folded into `execution_master`) under the legacy per-epic VM-topology model — superseded by single-VM role-based
dispatch since 2026-06-27; retained only to name the co-located service trio. Bulk of implementation lands in
execution-service + strategy-service code. UAC schema PRs route through `client_isolation_and_governance_master`
review per its UAC-schema ownership. No net-new VM prefixes were added to `VM_PREFIX_TO_BUCKET`
(`ledger-reconcile-` absorbed into existing `batch-live-recon-`; `passive-listener-` will absorb into existing
`strategy-live-*` once the live PassiveLedger listener above ships; derived ledgers use existing
`strategy-paper-*` / `strategy-live-*` / `client-reporting-cutover-*` cohorts).

### Global-ledger continuous-verification path (post-migration)

| Surface                                                | Verification                       | Cadence      |
| --------------------------------------------------------- | ------------------------------------ | -------------- |
| InstructionLedger ⟷ venue execution reports            | Daily reconciliation cron          | T+1 daily    |
| PassiveLedger synthesiser ⟷ on-chain/venue emissions   | Per-event divergence check         | Per emission |
| PricingLedger ⟷ MTDS canonical prices                  | Snapshot cross-check               | Hourly       |
| Derived ledgers ⟷ SSOT replay                          | Backfill replay = production view  | Pre-deploy   |
| RiskView liquidation rows ⟷ alerting-service pages     | End-to-end smoke                   | Per event    |

## Archived plans

### [`defi_recursive_borrow_archetypes_post_cutover_2026_06_01`](../archive/2026_05/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 4/5/7/8/9/11/12/13 all DEFERRED-SERVICE-REPOS or DEFERRED-POST-CUTOVER (slot
6 sweep). Phase 6 (Hyperliquid LIVE) missed by slot 6, deferred here.

**Deferred (migrated):**

- **Phase 6 — Hyperliquid LIVE perp connector (7 items, DEFERRED-SERVICE-REPOS)**: execution-service work — DELETE
  `venues/hyperliquid.py` + replace simulation logic + NEW `_hyperliquid_signing.py` (EIP-712) + `ApiKeyReloader` + 8 HL
  `VENUE_ERRORS_DEFI` error codes + `hyperliquid_bridge.py` helpers + available-margin placeholder fix.
- **Phase 13 — Live deploy (BLOCKED-OPERATOR)**: Treasury allocation + 7-day live VM + plan archival, all gated on
  operator DeFi live deployment authorization.

### [`strategy_execution_contract_remediation_2026_05_20`](../archive/2026_05/strategy_execution_contract_remediation_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-5+Q done: strategy manifest emission (`record_captured`/`record_failed`),
`resolve_bucket_name(kind="strategy-store")` bucket SSOT, preflight gate via `validate_config_can_run()`, error
classification (`ADAPTER_FETCH_FAILED`), QG ratchet, codex SSOT updated. · **estimate**: 3.0 cal AI-days

**Deferred (MIGRATED FROM archived plan)** — P0 operator-decision:

- **4c. Per-AG → unified bucket migration**: CeFi bucket has 237 files (~19MB) dev backtest data (2025-01-01). All prod
  per-AG buckets are 0-byte. Operator choose: (a) abandon old dev data + delete per-AG buckets, OR (b) write migration
  script (old `strategy_instructions/<id>/<date>.parquet` → new `strategy_instructions/client_id=/.../`).
  BLOCKED-OPERATOR-DECISION. Ping filed slot-6 2026-05-23.
