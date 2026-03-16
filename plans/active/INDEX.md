# Active Plans Index

**Last updated:** 2026-03-16 (resumed 12 plans from archive) **Per-repo readiness checklist SSOT:**
`unified-trading-codex/10-audit/repos/{repo}.yaml` (codex v3.0 — CR/DR/BR).

---

## Master Plans (5 Active)

### 1. CI/CD & Code Rollout Master

**File:** [cicd_code_rollout_master_2026_03_13.plan.md](cicd_code_rollout_master_2026_03_13.plan.md) **Type:** mixed |
**Status:** active (76/92 done) | **Scope:** Pipeline bug fixes, citadel hardening, workflow rollout to 67 repos,
library tier completion (T0→T3), service/UI hardening, deployment infra, 1.0.0 stability gate.

### 2. CI/CD E2E Testing & Validation

**File:** [cicd_e2e_testing_master_2026_03_13.plan.md](cicd_e2e_testing_master_2026_03_13.plan.md) **Type:** infra |
**Status:** active (0/54, blocked by Plan 1 Phase 3+) | **Scope:** Validate every CI/CD path. 8 phases from static
validation to golden path E2E.

### 3. DeFi Keys & Data Integration

**File:** [defi_keys_data_integration_2026_03_13.plan.md](defi_keys_data_integration_2026_03_13.plan.md) **Type:** mixed
| **Status:** active (0/21, mostly human) | **Scope:** 30 vendor API keys, VCR cassettes, data freshness SLAs for 33
venues, production backfill pipeline.

### 4. Presentations

**File:** [presentations_2026_03_13.plan.md](presentations_2026_03_13.plan.md) **Type:** business | **Status:** active
(0/6, human) | **Deadlines:** Rehearsal 2: March 18 | Board meeting: March 31

### 5. Website Master

**File:** [website_master_2026_03_13.plan.md](website_master_2026_03_13.plan.md) **Type:** business | **Status:** active
(0/5) | **Blocked by:** Plan 4 (presentations)

---

## Supporting Plans

### 6. Strategy System Citadel Master

**File:** [strategy_system_citadel_master_2026_03_15.plan.md](strategy_system_citadel_master_2026_03_15.plan.md)
**Type:** mixed | **Status:** active (~22/44 done after Wave 2-3) | **Scope:** Strategy universe expansion, config
system N10, events canonicalization, UI/API completeness, testing framework, dependency tracking.

### 7. UI / API / Alerting / Observability

**File:** [ui_api_alerting_observability_2026_03_14.plan.md](ui_api_alerting_observability_2026_03_14.plan.md) **Type:**
mixed | **Status:** active (~28/41 done after Wave 1-3) | **Scope:** LogLevel (done), alerting hardening (done), CI/CD
alerting (done), observability (done), UI/API mapping, auth standardization (done), cross-cutting.

### 8. Sports Hub — Residual Actions

**File:** [sports_hub_residual_actions_2026_03_15.plan.md](sports_hub_residual_actions_2026_03_15.plan.md) **Type:**
human | **Status:** active (2/12) | **Scope:** All human work: Secret Manager credentials, Playwright CSS selectors,
CAPTCHA, GeoComply.

### 9. UI Trader Acceptance Testing

**File:** [ui_trader_acceptance_testing_2026_03_15.plan.md](ui_trader_acceptance_testing_2026_03_15.plan.md) **Type:**
human+agent | **Status:** active (0/36) | **Scope:** Smoke tests, visual audit, layout fixes, API mock validation,
stress scenarios, trader sign-off.

---

## Resumed Plans (active — resumed from archive, incomplete todos)

### 10. Quality Gates Full Fix

**File:** [quality_gates_full_fix_2026_03_10.plan.md](quality_gates_full_fix_2026_03_10.plan.md) **Type:** infra |
**Status:** active — resumed from archive (incomplete todos) (~11/22 done) | **Scope:** Systematically fix all failing
tests and coverage gaps across all repos; no bypasses; T0–T3 libs ≥80%, services/APIs ≥70%.

### 11. UAC Citadel Remediation

**File:** [uac_citadel_remediation.plan.md](uac_citadel_remediation.plan.md) **Type:** code | **Status:** active —
resumed from archive (incomplete todos) (~5/27 done) | **Scope:** Clean up remaining UAC Citadel Architecture items
across facades, domain sub-packages, and capability registry that were marked done prematurely.

### 12. Registry Completeness — Implementation Detail

**File:** [registry_completeness_implementation_detail.plan.md](registry_completeness_implementation_detail.plan.md)
**Type:** code | **Status:** active — resumed from archive (incomplete todos) (~1/30 done) | **Scope:** Add missing
instrument types, sports market granularity (BTTS end-to-end), BetSide/CommissionModel enums, and consumer adoption
across 11 repos; enum consolidation with UCI re-exports from UAC.

### 13. Full Autonomous Agent CI

**File:** [full_autonomous_agent_ci.plan.md](full_autonomous_agent_ci.plan.md) **Type:** infra | **Status:** active —
resumed from archive (incomplete todos); superseded by Plan 1 for remaining scope | **Scope:** Multi-repo autonomous
agent CI suite with four specialized agent types, overnight tier-ordered execution, and Telegram morning summary.

### 14. Cross-Venue Position Aggregation (2026-03-15)

**File:** [cross_venue_position_aggregation_2026_03_15.plan.md](cross_venue_position_aggregation_2026_03_15.plan.md)
**Type:** mixed | **Status:** active — resumed from archive (incomplete todos) (~1/36 done) | **Scope:**
Institutional-grade cross-venue position aggregation engine covering all 5 asset classes, 16+ instrument types, 4
strategy types, and 33 venues; adds AggregatedPosition, PortfolioView, Greeks, PnL attribution to UAC/UIC/PBMS.

### 15. Feature Enrichment — Reversal Dynamics

**File:** [feature_enrichment_reversal_dynamics.plan.md](feature_enrichment_reversal_dynamics.plan.md) **Type:** code |
**Status:** active — resumed from archive (incomplete todos) (all 10 todos in_progress) | **Scope:** Enrich the feature
engineering pipeline with ~4,000–5,000 new derived features (streak reversals, cross-candle morphology, N-bar
confirmation, multi-signal confluence, volatility regimes, and more); 70% unit test coverage target.

### 16. Stub Completion — Interfaces and Infra

**File:** [stub_completion_interfaces_and_infra.plan.md](stub_completion_interfaces_and_infra.plan.md) **Type:** code |
**Status:** active — resumed from archive (incomplete todos) (blocked items remain: UPI adapters, UMI onchain) |
**Scope:** Complete all `raise NotImplementedError` stubs and unimplemented TODOs across URDI, UMI, UTEI, UPI, UCI, and
deployment-api not tracked by other active plans.

### 17. Strategy Visibility — Grafana Dashboards

**File:** [strategy_visibility_grafana_2026_03_10.plan.md](strategy_visibility_grafana_2026_03_10.plan.md) **Type:**
code | **Status:** active — resumed from archive (incomplete todos); superseded by Plan 1 for delivery | **Scope:**
Deploy Grafana on Cloud Run, add Prometheus metrics to strategy/execution/PnL services, create 5 dashboards, and embed
panels into unified-admin-ui.

### 18. User Management Platform

**File:** [user_management_platform_2026_03_13.plan.md](user_management_platform_2026_03_13.plan.md) **Type:** code |
**Status:** active — resumed from archive (incomplete todos); superseded by Plan 1 for delivery; human blocker pending |
**Scope:** New `user-management-ui` repo — full lifecycle user management (onboard/modify/off-board) with provisioning
for GitHub, Slack, M365, GCP IAM, and website portal per role.

### 19. Production Mock E2E

**File:** [production_mock_e2e_plan_d90c8f20.plan.md](production_mock_e2e_plan_d90c8f20.plan.md) **Type:** infra |
**Status:** active — resumed from archive (incomplete todos) (~13/26 done) | **Scope:** Bring all 60+ repos to
production-standard mock E2E testability — libraries via UAC/UIC validation and VCR cassettes; services/APIs via mock
data replay and load checks; UIs via mock API and smoke tests.

### 20. Data Availability — Live Expectations

**File:**
[data_availability_live_expectations_2026_03_10.plan.md](data_availability_live_expectations_2026_03_10.plan.md)
**Type:** code | **Status:** active — resumed from archive (incomplete todos) (~21/33 done); superseded by Plan 3
(defi_keys_data_integration) for remaining scope | **Scope:** Add per-source freshness contracts, FreshnessMonitor base
class in UTL, per-service freshness gates in strategy/execution, and alerting integration for stale-data detection
within 60 seconds in live mode.

### 21. Live/Batch Protocol Completeness

**File:** [live_batch_protocol_completeness_2026_03_10.plan.md](live_batch_protocol_completeness_2026_03_10.plan.md)
**Type:** code | **Status:** active — resumed from archive (incomplete todos) (~11/22 done, 8 blocked) | **Scope:**
Audit and remediate all 14 T4 services to ensure both batch and live mode handlers, CLI flags, transport switching, and
tests are present and functional.

---

## Archived Plans (2026-03-16 cleanup)

17 plans archived in this session. See `plans/archive/` for full files.

| Plan                                        | Reason                                                           |
| ------------------------------------------- | ---------------------------------------------------------------- |
| ui_trading_desk_strategy_merge              | Complete (46/46)                                                 |
| uac_citadel_implementation_execution        | Complete (79/79)                                                 |
| liquidation_band_prediction                 | Complete (6/6)                                                   |
| sit_build_source_ci_rollout                 | Complete (10/10)                                                 |
| cross_venue_position_aggregation            | Complete (37/37)                                                 |
| registry_completeness_implementation_detail | Moved to active (resumed — incomplete todos remain)              |
| uac_citadel_architecture                    | Superseded by completed execution plan                           |
| uac_citadel_implementation                  | Spec doc; execution complete                                     |
| infrastructure_canonical_layer              | Design doc; todos:[]                                             |
| integration_tests_codex_compliance          | Done per completion summary                                      |
| uac_residual_refactors_expanded             | Research doc consumed by active plans                            |
| registry_completeness_refactor              | Superseded by implementation_detail                              |
| uac_residual_refactors_provider_manifest    | Phase 3 done; nesting deferred                                   |
| uac_canonical_normalization_master          | Deferred — current canonical/domain/ layout accepted as final    |
| mode_config_env_architecture                | Deferred — UDC stays separate; Phase 1 env_canon done            |
| uac_citadel_remediation                     | Moved to active (resumed — incomplete todos remain)              |
| internal_contract_replay_and_drift_infra    | Deferred — all stubs, blocked by 7 plans                         |
| ui_api_flow_validation_citadel_grade        | Phases 1-2 done; enforcement gates deferred                      |
| interfaces_capability_contract_unification  | Core items done (registry, errors, guardrails); mapping deferred |
| sports_execution_venue_coverage             | ~15/23 done; remaining human work tracked in sports_hub          |

### Architectural Decisions (codified)

- **UAC owns enums** (InstrumentType, Venue) — UCI will re-export
- **LogLevel lives in UIC** — operational config, not external API schema
- **UDC stays separate from UTL** — merge deferred indefinitely
- **Current `canonical/domain/` layout is final** — no restructuring
- **EventSeverity = LogLevel** — backward-compat alias in UIC
