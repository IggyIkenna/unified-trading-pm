---
name: consolidated-strategy-and-ui
overview: |
  Consolidated remaining strategy intelligence and UI work from 5 source plans.
  Covers: cross-domain alpha features, strategy lifecycle, composable strategies,
  client config E2E, UI walkthrough alignment, UI sync hardening.
type: mixed
epic: epic-code-completion
status: active

reconciliation_status: yaml_to_markdown_converted
reconciliation_date: 2026-04-25
reconciliation_evidence: _reconciliation_evidence_map_2026_04_25.md

completion_gates:
  code: C5
  deployment: D3
  business: B4

repo_gates:
  - repo: unified-api-contracts
    code: C0
  - repo: unified-trading-library
    code: C0
  - repo: strategy-service
    code: C0
  - repo: ml-inference-service
    code: C0
  - repo: execution-service
    code: C0
  - repo: features-delta-one-service
    code: C0
  - repo: features-onchain-service
    code: C0
  - repo: features-cross-instrument-service
    code: C0
  - repo: market-tick-data-service
    code: C0
  - repo: unified-trading-system-ui
    code: C0
  - repo: unified-trading-api
    code: C0

depends_on: []

source_plans:
  - cross_domain_alpha_execution_intelligence_2026_04_11
  - strategy_lifecycle_visibility_ui_2026_04_11
  - client_config_and_defi_risk_2026_04_01
  - ui_walkthrough_and_e2e_alignment_2026_04_01
  - ui_sync_hardening_2026_03_23

isProject: false
---

> **Reconciliation note (2026-04-25):** YAML `todos:` block converted to canonical Cursor markdown checkboxes per
> `PLAN_FORMAT.md`. 4 todos flipped to `[x]` with cited commit evidence; 32 remain open. Strategy lifecycle work has
> shipped under Plan A (UAC `bf407a2` + UTL `b1bd2adc` + strategy-service `f50d25c` + `07ac1f7`); cross-domain alpha
> work remains genuinely open. See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors
> (consolidated_strategy_and_ui block ~line 233). Note: this consolidator is a candidate for
> `superseded_by: dart_ui_strategy_filtering_and_onboarding_2026_04_24` per evidence-map duplication-cluster table.

# Consolidated Strategy & UI

Remaining work from 5 source plans. Cross-domain alpha is largely untouched. Strategy lifecycle Phase 1 shipped via Plan
A. Client config and UI alignment are nearly done (2 items each).

## Todos

### Group A — Cross-Domain Alpha: UAC + UTL Schemas & Engines

- [ ] [AGENT] P0. cda-p1-uac-schemas: Add cross-domain feature, SLA, and DQS schemas to UAC internal.
- [ ] [AGENT] P0. cda-p1-utl-sla-engine: Build FeatureFreshnessSLAEngine in UTL feature_service_base/sla_engine.py.
- [ ] [AGENT] P0. cda-p1-utl-crossdomain-calc: Build cross-domain feature calculators in UTL
      feature_calculator/crossdomain.py.
- [ ] [AGENT] P0. cda-p1-utl-dqs: Build DataQualityScorer in UTL feature_service_base/data_quality.py.
- [ ] [AGENT] P1. cda-p1-qg: Run quality-gates.sh on UAC, UTL — all pass.

### Group B — Cross-Domain Alpha: Feature Service Integration

- [ ] [AGENT] P0. cda-p2-microstructure: Add microstructure feature calculators to features-delta-one-service.
- [ ] [AGENT] P0. cda-p2-crossdomain-features: Wire cross-domain features into features-cross-instrument-service.
- [ ] [AGENT] P0. cda-p2-defi-alpha: Add DeFi-specific alpha features to features-onchain-service.
- [ ] [AGENT] P0. cda-p2-sla-integration: Integrate SLA engine into all feature services.
- [ ] [AGENT] P0. cda-p2-dqs-mtds: Integrate DataQualityScorer into market-tick-data-service.
- [ ] [AGENT] P1. cda-p2-qg: Run quality-gates.sh on all Phase 2 repos — pass.

### Group C — Cross-Domain Alpha: Execution Intelligence

- [ ] [AGENT] P0. cda-p3-cost-model: Build execution cost prediction model in execution-service.
- [ ] [AGENT] P0. cda-p3-unified-sor: Build unified CeFi+DeFi SOR in execution-service.
- [ ] [AGENT] P1. cda-p3-qg: Run quality-gates.sh on execution-service — pass.
- [ ] [AGENT] P1. cda-p4-final-qg: Final QG on all cross-domain repos.

### Group D — Strategy Lifecycle Visibility

- [x] [AGENT] P0. slv-p1-uac-lifecycle-schemas: Add strategy lifecycle, paper comparison, and lineage schemas to UAC.
      Evidence: UAC `bf407a2` (Plan A 5-dim StrategyInstance + lifecycle phasing — see also session memory) + `1a08159`
      (Plan A catalogue with venue-set variants + lifecycle phasing).
- [x] [AGENT] P0. slv-p1-lifecycle-enforcement: Build lifecycle state machine in strategy-service. Evidence:
      strategy-service `f50d25c` (wire InstanceLifecycleService + SeedLifecycleHandler + seed-lifecycle CLI) + `07ac1f7`
      (wire Plan A maturity-phase gate into SignalEmitter.emit_signal).
- [x] [AGENT] P1. slv-p1-qg: Run quality-gates.sh on UAC, strategy-service — all pass. Evidence: Plan A archived per
      memory (PM `07efcb5d` `[unlock-plan]`); QG green at lifecycle-ship time.
- [ ] [AGENT] P0. slv-p2-composable: Implement composable strategy building blocks in strategy-service.
- [ ] [AGENT] P0. slv-p2-auto-retune: Add auto-retuning trigger in ml-inference-service.
- [ ] [AGENT] P0. slv-p2-lineage: Add prediction lineage tracking.
- [ ] [AGENT] P1. slv-p2-qg: Run quality-gates.sh on strategy-service, ml-inference-service — pass.

### Group E — Strategy & ML UI Dashboards

- [ ] [AGENT] P0. slv-p3-ml-dashboard: Build ML model performance dashboard in unified-trading-system-ui.
      <!-- needs human review: ml-pipeline UI integration partially shipped (see ml-training d53c2ea / ml-inference 7b9fefb) but dashboard surface scope unconfirmed -->
- [ ] [AGENT] P0. slv-p3-research-shell: Build strategy research shell in unified-trading-system-ui.
- [ ] [AGENT] P0. slv-p3-risk-attribution: Build risk attribution dashboard in unified-trading-system-ui.
- [ ] [AGENT] P1. slv-p3-qg: Run quality-gates.sh / UI build on unified-trading-system-ui — pass.
- [ ] [AGENT] P1. slv-p4-final-qg: Final QG on all strategy lifecycle repos.

### Group F — Client Config E2E & UI Alignment

- [ ] [AGENT] P1. cc-4a-e2e: Add client config + risk scenarios to e2e-testing.
- [ ] [AGENT] P1. cc-5a-docs: Update codex docs for client config and DeFi risk.
- [ ] [HUMAN+AGENT] P0. ui-1a-walkthrough-audit: Audit UI for every strategy walkthrough — can client manually execute
      each step?
- [ ] [HUMAN+AGENT] P0. ui-2a-batch-live: Verify batch=live alignment across all services for all strategies.
- [ ] [AGENT] P0. ui-2b-e2e-all-strategies: Create E2E test suite covering all strategies in all modes.
- [ ] [AGENT] P1. ui-3a-demo-scripts: Create demo walkthrough scripts for client presentations.
- [ ] [AGENT] P1. ui-4a-docs: Update codex + handover docs.

### Group G — UI Sync Hardening

- [x] [AGENT] P1. ui-p9a-health-all-services: Health check all services from UI. Evidence: per CLAUDE.md (Local
      Development), `http://localhost:3000/health` auto-detects tier and checks all connectors; runtime tiers in
      `codex/05-infrastructure/runtime-tiers-and-deployment.md`.
- [ ] [AGENT] P1. ui-p9b-qg-validation: Run quality gates: vitest + vite build + playwright.
