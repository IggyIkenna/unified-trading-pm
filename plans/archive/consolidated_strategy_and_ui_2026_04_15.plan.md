---
doc_type: plan
title: consolidated-strategy-and-ui
summary: 'Consolidated remaining strategy intelligence and UI work from 5 source plans.

  Covers: cross-domain alpha features, strategy lifecycle, composable strategies,

  client config E2E, UI walkthrough alignment, UI sync hardening.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    e2e-testing,
    execution-service,
    market-tick-data-service,
    strategy-service,
    unified-trading-pm,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-16"
type: mixed
epic: epic-code-completion
archived: 2026-05-07
superseded_by: plans/active/strategy_and_dart_master_2026_05_07.md
reconciliation_status: yaml_to_markdown_converted
reconciliation_date: 2026-04-25
reconciliation_evidence: _reconciliation_evidence_map_2026_04_25.md
completion_gates: { code: C5, deployment: D3, business: B4 }
repo_gates:
  - { repo: unified-api-contracts, code: C0 }
  - { repo: unified-trading-library, code: C0 }
  - { repo: strategy-service, code: C0 }
  - { repo: ml-inference-service, code: C0 }
  - { repo: execution-service, code: C0 }
  - { repo: features-delta-one-service, code: C0 }
  - { repo: features-onchain-service, code: C0 }
  - { repo: features-cross-instrument-service, code: C0 }
  - { repo: market-tick-data-service, code: C0 }
  - { repo: unified-trading-system-ui, code: C0 }
  - { repo: unified-trading-api, code: C0 }
depends_on: []
source_plans:
  [
    cross_domain_alpha_execution_intelligence_2026_04_11,
    strategy_lifecycle_visibility_ui_2026_04_11,
    client_config_and_defi_risk_2026_04_01,
    ui_walkthrough_and_e2e_alignment_2026_04_01,
    ui_sync_hardening_2026_03_23,
  ]
isProject: false
---

> **ARCHIVED 2026-05-07** — folded into
> [`strategy_and_dart_master_2026_05_07.md`](../active/strategy_and_dart_master_2026_05_07.md). All open todos preserved
> in the umbrella's Phase 1-3. This file is the historical SSOT.

> **Reconciliation note (2026-04-25):** YAML `todos:` block converted to canonical Cursor markdown checkboxes per
> `PLAN_FORMAT.md`. 4 todos flipped to `[x]` with cited commit evidence; 32 remain open. Strategy lifecycle work has
> shipped under Plan A (UAC `bf407a2` + UTL `b1bd2adc` + strategy-service `f50d25c` + `07ac1f7`); cross-domain alpha
> work remains genuinely open. See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors
> (consolidated_strategy_and_ui block ~line 233). Note: this consolidator is a candidate for
> `superseded_by: dart_ui_strategy_filtering_and_onboarding_2026_04_24` per evidence-map duplication-cluster table.

# Consolidated Strategy & UI

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 32 of 32 unchecked todos
- **Mis-marked DONE → flipped**: 1 — `cda-p2-microstructure` flipped to `[x]`. Verified: features-delta-one-service
  ships `app/calculators/microstructure.py` with `tests/unit/test_feature_groups/test_microstructure.py` covering it.
- **In-flight (running VMs)**: none directly — backfill VMs feed the features that strategy will consume.
- **Blocked by**:
  - `consolidated_ml_advanced_pipeline_2026_04_15` Phase 4 — Group D (auto-retune, lineage) and Group A SLA work
    overlap. ml-inference `engine/drift_monitor.py` ships `auto_retune_enabled` (so slv-p2-auto-retune is partially
    underway), but consumer-side strategy wiring is missing.
  - `feature_dag_uac_ssot_and_features_coverage_2026_05_06` — cross-domain feature SLA + DQS schemas can't be designed
    coherently until UAC FEATURE_REQUIRED_INPUTS lands (single-source-of-truth for what features are produced where).
  - `dart_ux_cockpit_refactor_2026_04_29` (sibling) — UI dashboards (Group E) and walkthrough audit (Group F) overlap
    heavily with DART surfaces; the per-strategy detail page already shipped at strategy-service `e4a0cdd` /
    unified-trading-system-ui `app/(platform)/services/strategy-catalogue/`.
- **Blocks**:
  - `master_to_live_defi_2026_05_23` Group F (Trading prereqs) — cost-aware filtering + calibrated signals are
    institutional-grade trading guardrails.
  - `master_to_live_defi_2026_05_23` Group G (Operator UX) — Strategy & ML dashboards.
- **Last meaningful commit**: strategy-service `e4a0cdd` (CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION specs Phase 9
  Phase 3); `f50d25c` + `07ac1f7` (Plan A lifecycle + maturity-phase gate); UAC `bf407a2` + `1a08159` (5-dim catalogue);
  features-delta-one microstructure (date pre-2026-04-15 in archive); features-cross-instrument paired-dispersion
  pipeline (`190bea1`/`2804f47`/`071604f`/`d1da107`).
- **Recommendation**: KEEP active, RESCOPE. Reconciliation note already flags this as a candidate for
  `superseded_by: dart_ui_strategy_filtering_and_onboarding_2026_04_24` per evidence-map duplication-cluster table —
  promote that supersession formally. Group A-C "cross-domain alpha" is genuinely-pending net-new work; do NOT roll into
  the asset-group umbrellas (it's by-definition cross-asset-group). Consider consolidating Group A+B+C into a successor
  plan `cross_domain_alpha_2026_05_<date>`. Group D is partially superseded by lifecycle Plan A. Group E+F+G largely
  subsumed by `dart_ux_cockpit_refactor_2026_04_29`. Net: this plan can shed about 18 of 32 todos to its successors and
  leave 14 cross-domain-alpha core open in a smaller successor.

Remaining work from 5 source plans. Cross-domain alpha is largely untouched. Strategy lifecycle Phase 1 shipped via Plan
A. Client config and UI alignment are nearly done (2 items each).

## Todos

### Group A — Cross-Domain Alpha: UAC + UTL Schemas & Engines

- [ ] [AGENT] P0. cda-p1-uac-schemas: Add cross-domain feature, SLA, and DQS schemas to UAC internal. [AUDIT 2026-05-07:
      FRESH — UAC grep `FeatureFreshnessSLA|DataQualityScorer|CrossDomainFeature` → 0 hits.]
- [ ] [AGENT] P0. cda-p1-utl-sla-engine: Build FeatureFreshnessSLAEngine in UTL feature_service_base/sla_engine.py.
      [AUDIT 2026-05-07: FRESH — UTL grep `FeatureFreshnessSLAEngine|sla_engine` → 0 hits.]
- [ ] [AGENT] P0. cda-p1-utl-crossdomain-calc: Build cross-domain feature calculators in UTL
      feature_calculator/crossdomain.py. [AUDIT 2026-05-07: FRESH — `unified_trading_library/feature_calculator/` has
      time_series, transformations, onchain, liquidation_bands, validations, base, registry — no `crossdomain.py`.]
- [ ] [AGENT] P0. cda-p1-utl-dqs: Build DataQualityScorer in UTL feature_service_base/data_quality.py. [AUDIT
      2026-05-07: FRESH — UTL grep `DataQualityScorer` → 0 hits in production code (only one stray
      `enable_data_quality_validation` config flag at `unified_trading_library/models/schemas.py:22`).]
- [ ] [AGENT] P1. cda-p1-qg: Run quality-gates.sh on UAC, UTL — all pass. [AUDIT 2026-05-07: FRESH — final QG gate,
      depends on the four preceding net-new builds.]

### Group B — Cross-Domain Alpha: Feature Service Integration

- [x] [AGENT] P0. cda-p2-microstructure: Add microstructure feature calculators to features-delta-one-service. [AUDIT
      2026-05-07: DONE — verified
      `features-delta-one-service/features_delta_one_service/app/calculators/microstructure.py` shipped with
      `tests/unit/test_feature_groups/test_microstructure.py` covering it.]
- [ ] [AGENT] P0. cda-p2-crossdomain-features: Wire cross-domain features into features-cross-instrument-service. [AUDIT
      2026-05-07: PARTIALLY-FRESH — features-cross-instrument-service ships paired_price_dispersion +
      paired_spec_resolver + catalog_pair_builder + paired_dispatch (UAC@0e7ba95 + features-cross-instrument
      `190bea1`/`2804f47`/`071604f`/`d1da107`) — that's a cross-instrument family, not the SLA-driven cross-domain
      wiring this todo names. Net-new SLA-driven wiring still pending.]
- [ ] [AGENT] P0. cda-p2-defi-alpha: Add DeFi-specific alpha features to features-onchain-service. [AUDIT 2026-05-07:
      PARTIALLY-FRESH — features-onchain has aave_*, block_priority_gas_distribution,
      concentrated_liquidity_il_realised, cryptoquant_exchange_flow calculators shipped; the named "alpha features"
      catalogue is unspecified. Likely overlap with `defi_master_2026_05_07` umbrella scope; consider migrating.]
- [ ] [AGENT] P0. cda-p2-sla-integration: Integrate SLA engine into all feature services. [AUDIT 2026-05-07: BLOCKED-ON
      cda-p1-utl-sla-engine.]
- [ ] [AGENT] P0. cda-p2-dqs-mtds: Integrate DataQualityScorer into market-tick-data-service. [AUDIT 2026-05-07:
      BLOCKED-ON cda-p1-utl-dqs. Note: writegate-honest-coverage's record_captured 4-pillar gate (NaN ratio + cluster
      coverage) is a partial overlap — verify scope before re-scoping this item.]
- [ ] [AGENT] P1. cda-p2-qg: Run quality-gates.sh on all Phase 2 repos — pass. [AUDIT 2026-05-07: FRESH — final QG
      gate.]

### Group C — Cross-Domain Alpha: Execution Intelligence

- [ ] [AGENT] P0. cda-p3-cost-model: Build execution cost prediction model in execution-service. [AUDIT 2026-05-07:
      PARTIALLY-FRESH — execution-service ships `execution_service/services/execution_cost_estimator.py` +
      `v2/cost_models.py` + a unit test. Whether the "prediction model" is a learned model or a deterministic estimator
      is the design gap; the deterministic estimator is shipped.]
- [ ] [AGENT] P0. cda-p3-unified-sor: Build unified CeFi+DeFi SOR in execution-service. [AUDIT 2026-05-07:
      PARTIALLY-FRESH — execution-service ships `algo_library/sor_cross_chain.py` (DeFi cross-chain SOR); the
      unified-CeFi+DeFi facade across both venue types is a separate piece. Live trading prereq.]
- [ ] [AGENT] P1. cda-p3-qg: Run quality-gates.sh on execution-service — pass. [AUDIT 2026-05-07: FRESH — final QG
      gate.]
- [ ] [AGENT] P1. cda-p4-final-qg: Final QG on all cross-domain repos. [AUDIT 2026-05-07: FRESH — final acceptance.]

### Group D — Strategy Lifecycle Visibility

- [x] [AGENT] P0. slv-p1-uac-lifecycle-schemas: Add strategy lifecycle, paper comparison, and lineage schemas to UAC.
      Evidence: UAC `bf407a2` (Plan A 5-dim StrategyInstance + lifecycle phasing — see also session memory) + `1a08159`
      (Plan A catalogue with venue-set variants + lifecycle phasing).
- [x] [AGENT] P0. slv-p1-lifecycle-enforcement: Build lifecycle state machine in strategy-service. Evidence:
      strategy-service `f50d25c` (wire InstanceLifecycleService + SeedLifecycleHandler + seed-lifecycle CLI) + `07ac1f7`
      (wire Plan A maturity-phase gate into SignalEmitter.emit_signal).
- [x] [AGENT] P1. slv-p1-qg: Run quality-gates.sh on UAC, strategy-service — all pass. Evidence: Plan A archived per
      memory (PM `07efcb5d` `[unlock-plan]`); QG green at lifecycle-ship time.
- [ ] [AGENT] P0. slv-p2-composable: Implement composable strategy building blocks in strategy-service. [AUDIT
      2026-05-07: FRESH — strategy-service grep `ComposableStrategy|composable_strategy` → 0 hits. Likely lower priority
      post-Plan A 5-dim catalogue; archetype variants already provide composition surface.]
- [ ] [AGENT] P0. slv-p2-auto-retune: Add auto-retuning trigger in ml-inference-service. [AUDIT 2026-05-07:
      PARTIALLY-FRESH — `ml-inference-service/ml_inference_service/engine/drift_monitor.py` ships
      `auto_retune_enabled: bool` + monitor pipeline (lines 8 + 110); needs the actual retune-trigger publish wiring
      to ml-training-service.]
- [ ] [AGENT] P0. slv-p2-lineage: Add prediction lineage tracking. [AUDIT 2026-05-07: PARTIALLY-FRESH — ml-inference
      `69d6313` threads service-run job_id + model_family into manifest writes; ml-training `f7369f2` companion. That's
      the manifest-side lineage; the strategy-side consumer (strategy reads back which model produced which signal) is
      the remaining gap.]
- [ ] [AGENT] P1. slv-p2-qg: Run quality-gates.sh on strategy-service, ml-inference-service — pass. [AUDIT 2026-05-07:
      FRESH — final QG gate.]

### Group E — Strategy & ML UI Dashboards

- [ ] [AGENT] P0. slv-p3-ml-dashboard: Build ML model performance dashboard in unified-trading-system-ui.
      <!-- needs human review: ml-pipeline UI integration partially shipped (see ml-training d53c2ea / ml-inference 7b9fefb) but dashboard surface scope unconfirmed -->
      [AUDIT 2026-05-07: PARTIALLY-FRESH — `app/(platform)/services/research/ml/training/page.tsx` +
      `monitoring/page.tsx` shipped, with `components/grid-config-editor.tsx` + `training-run-detail.tsx`. Surface
      exists; "model performance dashboard" depth unclear (e.g. drift charts, P&L attribution to model_family). Likely
      partially folded into `dart_ux_cockpit_refactor_2026_04_29`.]
- [ ] [AGENT] P0. slv-p3-research-shell: Build strategy research shell in unified-trading-system-ui. [AUDIT 2026-05-07:
      PARTIALLY-FRESH — `app/(platform)/services/research/` shipped with sub-routes: strategies, signals, features, ml,
      execution, allocate, quant, overview, strategy. Looks substantively shipped modulo UX polish; consider flipping to
      DONE after a Playwright walk.]
- [ ] [AGENT] P0. slv-p3-risk-attribution: Build risk attribution dashboard in unified-trading-system-ui. [AUDIT
      2026-05-07: FRESH — workspace grep `RiskAttribution` returns only schema definitions in `context/` (not a UI
      surface) + plan files. No risk-attribution route shipped. Live trading prereq for Group F.]
- [ ] [AGENT] P1. slv-p3-qg: Run quality-gates.sh / UI build on unified-trading-system-ui — pass. [AUDIT 2026-05-07:
      FRESH — final QG gate; depends on the three preceding dashboards.]
- [ ] [AGENT] P1. slv-p4-final-qg: Final QG on all strategy lifecycle repos. [AUDIT 2026-05-07: FRESH — final
      acceptance.]

### Group F — Client Config E2E & UI Alignment

- [ ] [AGENT] P1. cc-4a-e2e: Add client config + risk scenarios to e2e-testing. [AUDIT 2026-05-07: FRESH — e2e-testing/
      folder under unified-trading-pm has 23 service stubs but no client-config cross-cutting scenario file. Overlaps
      with Group B of `consolidated_operational_validation`.]
- [ ] [AGENT] P1. cc-5a-docs: Update codex docs for client config and DeFi risk. [AUDIT 2026-05-07: FRESH — codex
      04-architecture has `flash-loan-receiver.md`, `interface-credential-convention.md` shipped; "client config" scope
      unverified. Doc-only follow-up.]
- [ ] [HUMAN+AGENT] P0. ui-1a-walkthrough-audit: Audit UI for every strategy walkthrough — can client manually execute
      each step? [AUDIT 2026-05-07: BLOCKED-ON dart_ux_cockpit_refactor_2026_04_29 (DART surface owns the walkthrough
      flow); also partial-overlap with strategy-catalogue UI shipped at unified-trading-system-ui
      `app/(platform)/services/strategy-catalogue/`.]
- [ ] [HUMAN+AGENT] P0. ui-2a-batch-live: Verify batch=live alignment across all services for all strategies. [AUDIT
      2026-05-07: BLOCKED-ON master_to_live_defi_2026_05_23 Group F batch-vs-live reconciliation deliverable. The
      CLAUDE.md "Batch = Live" architectural rule is the principle; the verification is the deliverable here.]
- [ ] [AGENT] P0. ui-2b-e2e-all-strategies: Create E2E test suite covering all strategies in all modes. [AUDIT
      2026-05-07: BLOCKED-ON consolidated_operational_validation Group B cluster e2e completion + Plan A 228 strategy
      instances catalogue (UAC@bf407a2 + 1a08159 shipped).]
- [ ] [AGENT] P1. ui-3a-demo-scripts: Create demo walkthrough scripts for client presentations. [AUDIT 2026-05-07: FRESH
      — narrowly demo-only; not on May-23 critical path.]
- [ ] [AGENT] P1. ui-4a-docs: Update codex + handover docs. [AUDIT 2026-05-07: FRESH — doc-only acceptance gate.]

### Group G — UI Sync Hardening

- [x] [AGENT] P1. ui-p9a-health-all-services: Health check all services from UI. Evidence: per CLAUDE.md (Local
      Development), `http://localhost:3000/health` auto-detects tier and checks all connectors; runtime tiers in
      `/codex/05-infrastructure/runtime-tiers-and-deployment.md`.
- [ ] [AGENT] P1. ui-p9b-qg-validation: Run quality gates: vitest + vite build + playwright. [AUDIT 2026-05-07: FRESH —
      final QG gate. Note: `unified-trading-system-ui` is Next.js (not Vite for dev/test); command names should be
      `npm test` (vitest) + `npm build` + `npx playwright test` per `package.json` standard across the workspace.]
