# Active Plans Index

**Last updated:** 2026-03-21 (regenerated with Plans A-I + master plan) **Per-repo readiness checklist SSOT:**
`unified-trading-codex/10-audit/repos/{repo}.yaml` (codex v3.0 -- CR/DR/BR).

---

## Frontend-Backend Master Plan (Plans A-I)

### Master Plan

**File:** [frontend_backend_master_2026_03_21.plan.md](frontend_backend_master_2026_03_21.plan.md) **Type:** mixed |
**Status:** active (locked) | **Scope:** Master plan for frontend-backend integration: backend Plans A-D+H, then UI
Plans E-F, plus auth (G), API consolidation (H), client reporting (I).

### Plan A: Registry & Schema Sync

**File:** [plan_a_registry_schema_sync_2026_03_21.plan.md](plan_a_registry_schema_sync_2026_03_21.plan.md) **Type:**
code | **Status:** active | **Scope:** Registry schema sync between UAC, config-interface, and downstream consumers.

### Plan B: Config Hot-Reload & UI Wiring

**File:** [plan_b_config_hot_reload_2026_03_21.plan.md](plan_b_config_hot_reload_2026_03_21.plan.md) **Type:** code |
**Status:** active | **Scope:** Config hot-reload infrastructure and UI wiring for runtime config changes.

### Plan C: Domain Data API Backend Readiness

**File:** [plan_c_domain_data_api_2026_03_21.plan.md](plan_c_domain_data_api_2026_03_21.plan.md) **Type:** code |
**Status:** active | **Scope:** Domain data API backend readiness for UI consumption.

### Plan D: Testnet Stress Testing

**File:** [plan_d_testnet_stress_testing_2026_03_21.plan.md](plan_d_testnet_stress_testing_2026_03_21.plan.md) **Type:**
infra | **Status:** active | **Scope:** DeFi testnet stress testing and deployment mock validation.

### Plan E: UI Backend Integration

**File:** [plan_e_ui_backend_integration_2026_03_21.plan.md](plan_e_ui_backend_integration_2026_03_21.plan.md) **Type:**
code | **Status:** active | **Scope:** Wire UI components to real backend APIs, replace mock data.

### Plan F: UI Quality Gate Hardening

**File:** [plan_f_ui_quality_hardening_2026_03_21.plan.md](plan_f_ui_quality_hardening_2026_03_21.plan.md) **Type:**
infra | **Status:** active | **Scope:** UI quality gate hardening -- vitest, Playwright, lint, build validation.

### Plan G: Auth & Entitlement

**File:** [plan_g_auth_entitlement_2026_03_21.plan.md](plan_g_auth_entitlement_2026_03_21.plan.md) **Type:** code |
**Status:** active | **Scope:** Authentication and entitlement system for platform access control.

### Plan H: API Consolidation

**File:** [plan_h_api_consolidation_2026_03_21.plan.md](plan_h_api_consolidation_2026_03_21.plan.md) **Type:** code |
**Status:** active | **Scope:** API consolidation -- reduce API surface, unify endpoints, OpenAPI spec alignment.

### Plan I: Client Reporting & Docs

**File:** [plan_i_client_reporting_docs_2026_03_21.plan.md](plan_i_client_reporting_docs_2026_03_21.plan.md) **Type:**
business | **Status:** active | **Scope:** Client reporting infrastructure and documentation generation.

---

## Other Master Plans

### CI/CD & Code Rollout Master

**File:** [cicd_code_rollout_master_2026_03_13.plan.md](cicd_code_rollout_master_2026_03_13.plan.md) **Type:** mixed |
**Status:** active (76/92 done) | **Scope:** Pipeline bug fixes, citadel hardening, workflow rollout to 67 repos,
library tier completion (T0-T3), service/UI hardening, deployment infra, 1.0.0 stability gate.

### CI/CD E2E Testing & Validation

**File:** [cicd_e2e_testing_master_2026_03_13.plan.md](cicd_e2e_testing_master_2026_03_13.plan.md) **Type:** infra |
**Status:** active (blocked by CI/CD master Phase 3+) | **Scope:** Validate every CI/CD path. 8 phases from static
validation to golden path E2E.

### Strategy System Citadel Master

**File:** [strategy_system_citadel_master_2026_03_15.plan.md](strategy_system_citadel_master_2026_03_15.plan.md)
**Type:** mixed | **Status:** active (~22/44 done) | **Scope:** Strategy universe expansion, config system N10, events
canonicalization, UI/API completeness, testing framework, dependency tracking.

---

## DeFi Plans

### DeFi Keys & Data Integration

**File:** [defi_keys_data_integration_2026_03_13.plan.md](defi_keys_data_integration_2026_03_13.plan.md) **Type:** mixed
| **Epic:** epic-infra | **Status:** active (0/21, mostly human) | **Scope:** 30 vendor API keys, VCR cassettes, data
freshness SLAs for 33 venues, production backfill pipeline.

### DeFi Operation Capability & Pipeline

**File:**
[defi_operation_capability_and_pipeline_2026_03_17.plan.md](defi_operation_capability_and_pipeline_2026_03_17.plan.md)
**Type:** code | **Status:** active | **Scope:** Wire operation-level capability validation into all interfaces, resolve
SSOT flags, complete DeFi end-to-end MVP pipeline.

---

## Infrastructure & Quality Plans

### Quality Gates Full Fix

**File:** [quality_gates_full_fix_2026_03_10.plan.md](quality_gates_full_fix_2026_03_10.plan.md) **Type:** infra |
**Status:** paused -- superseded by systemic remediation for execution; coverage targets remain reference (~11/22 todos)
| **Scope:** Fix all failing tests and coverage gaps across all repos; T0-T3 libs >=80%, services/APIs >=70%.

### Quality Gates Systemic Remediation

**File:** [quality_gates_systemic_remediation_2026_03_16.plan.md](quality_gates_systemic_remediation_2026_03_16.plan.md)
**Type:** infra | **Status:** active | **Supersedes:** QG Full Fix (execution) | **Scope:** Systemic remediation of QG
failures -- type errors, coverage, lint, codex compliance; strict registry/UCI alignment.

### Full System Audit Resolution

**File:** [full_system_audit_resolution_2026_03_18.plan.md](full_system_audit_resolution_2026_03_18.plan.md) **Type:**
infra | **Status:** active | **Scope:** Resolution of all findings from the 2026-03-18 full system audit.

### Production Mock E2E

**File:** [production_mock_e2e_plan_d90c8f20.plan.md](production_mock_e2e_plan_d90c8f20.plan.md) **Type:** infra |
**Status:** active (~13/26 done) | **Scope:** Bring all 60+ repos to production-standard mock E2E testability.

### Mock Data Rollout

**File:** [mock_data_rollout_2026_03_18.plan.md](mock_data_rollout_2026_03_18.plan.md) **Type:** infra | **Status:**
active | **Scope:** Mock data architecture rollout across all services and UIs.

### Instruments Service Batch Validation

**File:**
[instruments_service_batch_validation_2026_03_17.plan.md](instruments_service_batch_validation_2026_03_17.plan.md)
**Type:** infra | **Status:** active | **Scope:** End-to-end instruments-service architecture fix + batch validation.
Template for all services.

### Live/Batch Alignment Audit

**File:** [live_batch_alignment_audit_2026_03_18.plan.md](live_batch_alignment_audit_2026_03_18.plan.md) **Type:** code
| **Status:** active | **Scope:** Full audit + 27-item remediation across 30 repos for live/batch alignment.

---

## Config & Architecture Plans

### Fixed vs Grid Config Refactor

**File:** [fixed_grid_config_refactor_2026_03_21.plan.md](fixed_grid_config_refactor_2026_03_21.plan.md) **Type:** code
| **Status:** active | **Scope:** Fixed vs Grid config refactor -- mass backtesting architecture.

### Config Lifecycle Flows

**File:** [config_lifecycle_flows_6b1b961d.plan.md](config_lifecycle_flows_6b1b961d.plan.md) **Type:** code |
**Status:** active | **Scope:** Config lifecycle flows -- grid deploy and promote best.

### Registry Completeness -- Implementation Detail

**File:** [registry_completeness_implementation_detail.plan.md](registry_completeness_implementation_detail.plan.md)
**Type:** code | **Status:** active (~1/30 done) | **Scope:** Add missing instrument types, sports market granularity,
BetSide/CommissionModel enums, and consumer adoption across 11 repos.

### Backtest Config UI

**File:** [backtest_config_ui_2026_03_21.plan.md](backtest_config_ui_2026_03_21.plan.md) **Type:** code | **Status:**
active | **Scope:** Backtest configuration UI plan.

---

## Sports Plans

### Sports Hub -- Residual Actions

**File:** [sports_hub_residual_actions_2026_03_15.plan.md](sports_hub_residual_actions_2026_03_15.plan.md) **Type:**
human | **Status:** active (2/12) | **Scope:** All human work: Secret Manager credentials, Playwright CSS selectors,
CAPTCHA, GeoComply.

### Sports Canonical Mapping & GCS Migration

**File:**
[sports_canonical_mapping_and_gcs_migration_2026_03_18.plan.md](sports_canonical_mapping_and_gcs_migration_2026_03_18.plan.md)
**Type:** code | **Status:** active | **Scope:** Sports canonical mapping and GCS path migration.

### Sports Schema Allocation Restructuring

**File:**
[sports_schema_allocation_restructuring_2026_03_20.plan.md](sports_schema_allocation_restructuring_2026_03_20.plan.md)
**Type:** code | **Status:** active | **Scope:** Sports schema allocation restructuring.

### Uniform ML Pipeline + Sports Migration

**File:**
[uniform_ml_pipeline_sports_migration_2026_03_20.plan.md](uniform_ml_pipeline_sports_migration_2026_03_20.plan.md)
**Type:** code | **Status:** active | **Scope:** Uniform ML training pipeline + CosmicTrader sports migration. Global
model, pooled horizons, SportsMatchingEngine.

---

## UI Plans

### UI Platform Redesign

**File:** [ui_platform_redesign_2026_03_17.plan.md](ui_platform_redesign_2026_03_17.plan.md) **Type:** code |
**Status:** active | **Scope:** Unified Trading Platform UI/UX redesign vision.

### UI Consolidation & UX Hardening

**File:** [ui_consolidation_ux_hardening_7571b4f8.plan.md](ui_consolidation_ux_hardening_7571b4f8.plan.md) **Type:**
code | **Status:** active | **Scope:** UI consolidation and UX hardening.

### UI Navigation & UX Model

**File:** [ui_navigation_ux_model_6fda92d7.plan.md](ui_navigation_ux_model_6fda92d7.plan.md) **Type:** code |
**Status:** active | **Scope:** UI navigation and UX model (addendum to data-driven consolidation plan).

### UI Trader Acceptance Testing

**File:** [ui_trader_acceptance_testing_2026_03_15.plan.md](ui_trader_acceptance_testing_2026_03_15.plan.md) **Type:**
human+agent | **Status:** active (0/36) | **Scope:** Smoke tests, visual audit, layout fixes, API mock validation,
stress scenarios, trader sign-off.

### Backend-Frontend Alignment & Enhancements

**File:** [backend_frontend_alignment.plan.md](backend_frontend_alignment.plan.md) **Type:** code | **Status:** active |
**Scope:** Backend-frontend alignment and enhancements.

---

## Business Plans

### Presentations

**File:** [presentations_2026_03_13.plan.md](presentations_2026_03_13.plan.md) **Type:** business | **Status:** active
(0/6, human) | **Deadlines:** Rehearsal 2: March 18 | Board meeting: March 31

### Website Master

**File:** [website_master_2026_03_13.plan.md](website_master_2026_03_13.plan.md) **Type:** business | **Status:** active
(0/5) | **Blocked by:** Presentations plan

### User Management Platform

**File:** [user_management_platform_2026_03_13.plan.md](user_management_platform_2026_03_13.plan.md) **Type:** code |
**Status:** active | **Scope:** New `user-management-ui` repo -- full lifecycle user management
(onboard/modify/off-board) with provisioning for GitHub, Slack, M365, GCP IAM, and website portal per role.

---

## Archived Plans

26+ plans archived across all sessions. See `plans/archive/` for full files.

### Architectural Decisions (codified)

- **UAC owns domain enums** (InstrumentType, Venue, etc.) -- **UCI does not re-export UAC**; consumers use
  `from unified_api_contracts import ...` (see `uci-no-domain-schemas.mdc`).
- **LogLevel lives in UIC** -- operational config, not external API schema
- **UDC stays separate from UTL** -- merge deferred indefinitely
- **Current `canonical/domain/` layout is final** -- no restructuring
- **EventSeverity** -- aligned with operational severity naming in UIC; no silent dual-path "compat" aliases for domain
  enums
