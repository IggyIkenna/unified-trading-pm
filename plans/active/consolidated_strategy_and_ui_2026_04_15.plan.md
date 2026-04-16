---
name: consolidated-strategy-and-ui
overview: |
  Consolidated remaining strategy intelligence and UI work from 5 source plans.
  Covers: cross-domain alpha features, strategy lifecycle, composable strategies,
  client config E2E, UI walkthrough alignment, UI sync hardening.
type: mixed
epic: epic-code-completion
status: active

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

todos:
  # ══════════════════════════════════════════════════════════════
  # GROUP A — Cross-Domain Alpha: UAC + UTL Schemas & Engines
  # ══════════════════════════════════════════════════════════════
  - id: cda-p1-uac-schemas
    content: "Add cross-domain feature, SLA, and DQS schemas to UAC internal"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p1-utl-sla-engine
    content: "Build FeatureFreshnessSLAEngine in UTL feature_service_base/sla_engine.py"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p1-utl-crossdomain-calc
    content: "Build cross-domain feature calculators in UTL feature_calculator/crossdomain.py"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p1-utl-dqs
    content: "Build DataQualityScorer in UTL feature_service_base/data_quality.py"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p1-qg
    content: "Run quality-gates.sh on UAC, UTL — all pass"
    status: todo
    source: cross_domain_alpha_execution_intelligence

  # ══════════════════════════════════════════════════════════════
  # GROUP B — Cross-Domain Alpha: Feature Service Integration
  # ══════════════════════════════════════════════════════════════
  - id: cda-p2-microstructure
    content: "Add microstructure feature calculators to features-delta-one-service"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p2-crossdomain-features
    content: "Wire cross-domain features into features-cross-instrument-service"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p2-defi-alpha
    content: "Add DeFi-specific alpha features to features-onchain-service"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p2-sla-integration
    content: "Integrate SLA engine into all feature services"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p2-dqs-mtds
    content: "Integrate DataQualityScorer into market-tick-data-service"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p2-qg
    content: "Run quality-gates.sh on all Phase 2 repos — pass"
    status: todo
    source: cross_domain_alpha_execution_intelligence

  # ══════════════════════════════════════════════════════════════
  # GROUP C — Cross-Domain Alpha: Execution Intelligence
  # ══════════════════════════════════════════════════════════════
  - id: cda-p3-cost-model
    content: "Build execution cost prediction model in execution-service"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p3-unified-sor
    content: "Build unified CeFi+DeFi SOR in execution-service"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p3-qg
    content: "Run quality-gates.sh on execution-service — pass"
    status: todo
    source: cross_domain_alpha_execution_intelligence
  - id: cda-p4-final-qg
    content: "Final QG on all cross-domain repos"
    status: todo
    source: cross_domain_alpha_execution_intelligence

  # ══════════════════════════════════════════════════════════════
  # GROUP D — Strategy Lifecycle Visibility
  # ══════════════════════════════════════════════════════════════
  - id: slv-p1-uac-lifecycle-schemas
    content: "Add strategy lifecycle, paper comparison, and lineage schemas to UAC"
    status: todo
    source: strategy_lifecycle_visibility_ui
  - id: slv-p1-lifecycle-enforcement
    content: "Build lifecycle state machine in strategy-service"
    status: todo
    source: strategy_lifecycle_visibility_ui
  - id: slv-p1-qg
    content: "Run quality-gates.sh on UAC, strategy-service — all pass"
    status: todo
    source: strategy_lifecycle_visibility_ui
  - id: slv-p2-composable
    content: "Implement composable strategy building blocks in strategy-service"
    status: todo
    source: strategy_lifecycle_visibility_ui
  - id: slv-p2-auto-retune
    content: "Add auto-retuning trigger in ml-inference-service"
    status: todo
    source: strategy_lifecycle_visibility_ui
  - id: slv-p2-lineage
    content: "Add prediction lineage tracking"
    status: todo
    source: strategy_lifecycle_visibility_ui
  - id: slv-p2-qg
    content: "Run quality-gates.sh on strategy-service, ml-inference-service — pass"
    status: todo
    source: strategy_lifecycle_visibility_ui

  # ══════════════════════════════════════════════════════════════
  # GROUP E — Strategy & ML UI Dashboards
  # ══════════════════════════════════════════════════════════════
  - id: slv-p3-ml-dashboard
    content: "Build ML model performance dashboard in unified-trading-system-ui"
    status: todo
    source: strategy_lifecycle_visibility_ui
  - id: slv-p3-research-shell
    content: "Build strategy research shell in unified-trading-system-ui"
    status: todo
    source: strategy_lifecycle_visibility_ui
  - id: slv-p3-risk-attribution
    content: "Build risk attribution dashboard in unified-trading-system-ui"
    status: todo
    source: strategy_lifecycle_visibility_ui
  - id: slv-p3-qg
    content: "Run quality-gates.sh / UI build on unified-trading-system-ui — pass"
    status: todo
    source: strategy_lifecycle_visibility_ui
  - id: slv-p4-final-qg
    content: "Final QG on all strategy lifecycle repos"
    status: todo
    source: strategy_lifecycle_visibility_ui

  # ══════════════════════════════════════════════════════════════
  # GROUP F — Client Config E2E & UI Alignment
  # ══════════════════════════════════════════════════════════════
  - id: cc-4a-e2e
    content: "Add client config + risk scenarios to e2e-testing"
    status: todo
    source: client_config_and_defi_risk
  - id: cc-5a-docs
    content: "Update codex docs for client config and DeFi risk"
    status: todo
    source: client_config_and_defi_risk
  - id: ui-1a-walkthrough-audit
    content: "Audit UI for every strategy walkthrough — can client manually execute each step?"
    status: todo
    source: ui_walkthrough_and_e2e_alignment
  - id: ui-2a-batch-live
    content: "Verify batch=live alignment across all services for all strategies"
    status: todo
    source: ui_walkthrough_and_e2e_alignment
  - id: ui-2b-e2e-all-strategies
    content: "Create E2E test suite covering all strategies in all modes"
    status: todo
    source: ui_walkthrough_and_e2e_alignment
  - id: ui-3a-demo-scripts
    content: "Create demo walkthrough scripts for client presentations"
    status: todo
    source: ui_walkthrough_and_e2e_alignment
  - id: ui-4a-docs
    content: "Update codex + handover docs"
    status: todo
    source: ui_walkthrough_and_e2e_alignment

  # ══════════════════════════════════════════════════════════════
  # GROUP G — UI Sync Hardening
  # ══════════════════════════════════════════════════════════════
  - id: ui-p9a-health-all-services
    content: "Health check all services from UI"
    status: todo
    source: ui_sync_hardening
  - id: ui-p9b-qg-validation
    content: "Run quality gates: vitest + vite build + playwright"
    status: todo
    source: ui_sync_hardening

isProject: false
---

# Consolidated Strategy & UI

Remaining work from 5 source plans. Cross-domain alpha and strategy lifecycle are entirely untouched. Client config and
UI alignment are nearly done (2 items each).
