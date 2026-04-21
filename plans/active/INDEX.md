# Active Plans Index

**Last Updated:** 2026-04-01

This is the canonical index of all active plans. Plans are organized by domain.

---

## DeFi Strategy Testing & Automation (NEW)

**⭐ START HERE:** [defi-strategy-testing-quickstart.md](defi-strategy-testing-quickstart.md) — Quick reference +
examples for testing any DeFi strategy

**Detailed Plans:**

- [defi-strategy-ui-verification.plan.md](defi-strategy-ui-verification.plan.md) — Phase 1: Verify UI widgets with
  mocked data
- [defi-strategy-e2e-automation.plan.md](defi-strategy-e2e-automation.plan.md) — Full pipeline: UI verification → test
  generation → execution → regression protection

---

## Currently Active Plans

### Infrastructure & Setup

- agent1_shell_navigation_2026_03_22.plan.md — Shell navigation framework
- agent2_trading_service_2026_03_22.plan.md — Trading service setup
- agent5_api_service_layer_2026_03_22.plan.md — API service layer

### DeFi Strategy Rollout

- defi_demo_e2e_workflow_2026_03_30.plan.md — End-to-end DeFi demo
- defi_ui_component_audit_2026_03_31.plan.md — UI component audit
- defi_phase3_infrastructure_2026_03_30.plan.md — Infrastructure completion
- defi_strategies_phase2_2026_03_29.plan.md — Phase 2 strategies

### Sports

- sports_live_streaming_viz_2026_04_15.plan.md — Sports live streaming, ML pipeline UI, promotion structure,
  frontend-backend parity

### Data & Testing

- agent6_mock_data_quality_2026_03_22.plan.md — Mock data quality
- agent8_e2e_tests_quality_2026_03_22.plan.md — E2E testing
- sports_e2e_validation_2026_03_27.plan.md — Sports E2E validation
- mtds_per_instrument_sentinels_2026_04_21.plan.md — Phase 8 honest-coverage: per-instrument Tier-3 sentinels for MTDS
  `trades` / `book_snapshot_5` / `derivative_ticker` / `options_chain` / `futures_chain`. UAC accessor + MTDS
  orchestrator + deployment-api aggregator + codex matrix. MVP cap=50 rollout. 4 repos.

### Service Remediation

- citadel_per_service_remediation_2026_03_24.plan.md — Per-service fixes
- instruments_service_reorganisation_2026_03_27.plan.md — Instruments service

### Library Consolidation

- fold_uei_into_utl_2026_04_17.plan.md — Fold unified-trading-library into `unified_trading_library.events` (aggregate
  of both), migrate 30+ consumers, archive UEI repo

### Deployment Topology & Client Isolation

- deployment_topology_and_client_isolation_2026_04_17.plan.md — Per-service isolation policy (shared vs isolated), SLA
  tiers (basic/standard/premium) with cost passthrough, runtime profiles (backtest/paper/mock-live/staging/prod)
  collapsing 5 mode env vars, chaos + kill-switch primitives. runtime-topology.yaml v6→v7, UAC schemas, UTL readers,
  deployment-service/api/ui materialisation, downstream service wiring. 13 repos. **Progress as of 2026-04-17
  live-defi-rollout:** Phases 1 (SSOT), 2a/2b (deployment-service/api), 3a/3b/3c (UTL ChaosController + KillSwitchBus +
  ServiceBootstrap wiring + strategy/exec/risk subscribers), 4a (deployment-api runtime_profile env var fanout), 5 (18
  archetype topology_requirements frontmatter + strategy-service enforcement module), 6 (PBM/R&E/PnL/execution isolation
  policy modules), 7 (8 e2e chaos scenarios), 4b (deployment-ui /client-subscriptions, /chaos pages, runtime_profile
  dropdown on DeployForm + 6 vitest cases) all committed locally. Phase 8 workspace QG sweep pending.

---

## How to Use This Index

1. **To find a plan:** Search this file for keywords or domain
2. **To run a plan:** Click the link and follow the plan's execution steps
3. **To create a new plan:** Add it to this INDEX with a one-line description, then update
   `[plan-placement.mdc](../../.cursor/rules/core/plan-placement.md)`

---

## Archive

For completed or superseded plans, see `archive/` directory.
