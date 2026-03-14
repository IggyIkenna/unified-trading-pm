# Active Plans Index

**Last updated:** 2026-03-14 **Per-repo readiness checklist SSOT:** `unified-trading-codex/10-audit/repos/{repo}.yaml`
(codex v3.0 — CR/DR/BR).

---

## Master Plans (5 Active)

All previous plans have been consolidated into these 5 focused plans with inter-plan blockers. Milestone-gated: each
phase has exit criteria, no dates. Next phase starts only when current passes.

### 1. CI/CD & Code Rollout Master

**File:** [cicd_code_rollout_master_2026_03_13.plan.md](cicd_code_rollout_master_2026_03_13.plan.md) **Type:** mixed |
**Status:** active | **Gates:** C5/D5 **Scope:** Pipeline bug fixes (7 bugs), citadel hardening, workflow rollout to 67
repos, library tier completion (T0->T3), service/UI hardening, deployment infra, features, 1.0.0 stability gate.
**Phases:** 0-Cleanup → 1-CI/CD Hardening → 2-Workflow Rollout → 3-Library Tiers → 4-Service Hardening → 5-Deploy Infra
→ 6-Features & Stability Gate **Supersedes:** 16 plans (see supersession map below)

### 2. CI/CD E2E Testing & Validation

**File:** [cicd_e2e_testing_master_2026_03_13.plan.md](cicd_e2e_testing_master_2026_03_13.plan.md) **Type:** infra |
**Status:** active | **Gates:** C4 **Scope:** Validate every CI/CD path using instruments-service + UEI as guinea pigs.
8 phases from static validation to golden path E2E. **Phases:** 1-Static Validation → 2-Repo Flow → 3-Cascade →
4-Staging/SIT → 5-Agent Validation → 6-Failure Modes → 7-Codex/Docs → 8-Golden Path **Blocker:** Plan 1 Phase 1 (bugs
fixed first) **Supersedes:** 1 plan

### 3. DeFi Keys & Data Integration

**File:** [defi_keys_data_integration_2026_03_13.plan.md](defi_keys_data_integration_2026_03_13.plan.md) **Type:** mixed
| **Status:** active | **Gates:** C4/D3 **Scope:** 30 vendor API keys, VCR cassettes, data freshness SLAs for 33 venues,
production backfill pipeline. **Phases:** 1-Secret Provisioning → 2-VCR Cassettes → 3-Freshness SLAs → 4-Production
Backfill **Blocker:** Plan 1 Phase 3 (interfaces hardened for cassette recording) **Supersedes:** 4 plans

### 4. Presentations

**File:** [presentations_2026_03_13.plan.md](presentations_2026_03_13.plan.md) **Type:** business | **Status:** active |
**Gates:** B6 **Scope:** 13 board presentations, Elysium DeFi presentation, GCP credits application. **Deadlines:**
Rehearsal 2: March 18 | Board meeting: March 31 **Blocker:** Plan 1 Phase 4 (demo data) **Supersedes:** 3 plans

### 5. Website Master

**File:** [website_master_2026_03_13.plan.md](website_master_2026_03_13.plan.md) **Type:** business | **Status:** active
| **Gates:** C3/D3/B4 **Scope:** odum-research-website repo integration, content refresh, domain migration, presentation
hosting, admin portal. **Blocker:** Plan 4 (presentations complete) **Supersedes:** 4 plans

---

## Supporting Plans (Data / Contracts)

### 6. UAC Residual Refactors and Provider Manifest

**File:**
[uac_residual_refactors_provider_manifest_2026_03_14.plan.md](uac_residual_refactors_provider_manifest_2026_03_14.plan.md)
**Type:** mixed | **Status:** active | **Gates:** C4 **Scope:** Sports/DeFi nesting under canonical domains, reference
data consolidation, provider manifest expansion (testnet, data_type, API keys checklist). Single SSOT for provider
metadata. **Phases:** 1-Sports/DeFi Nesting → 2-Reference Data → 3-Provider Manifest **Depends on:** Plan 3 (defi_keys)
**Supersedes:** uac_nested_domain_deviations, uac_package_reorganization_c1c0734e

### 7. UI / API / Alerting / Observability

**File:** [ui_api_alerting_observability_2026_03_14.plan.md](ui_api_alerting_observability_2026_03_14.plan.md) **Type:**
mixed | **Status:** active | **Gates:** C5/D3 **Scope:** UI↔API mapping fixes (2 new APIs: settlement-api, config-api),
alerting system hardening (Telegram + GCS persistence, Slack deprecated), observability (LOG_LEVEL wiring,
logs-dashboard-ui backend, event warehouse via external tables), CI/CD alerting centralization (notify-telegram.yml +
persist-cicd-event.yml), OTel cleanup, UI branding standardization. **Phases:** 0-Foundation → 1-Alert Hardening →
2-CI/CD Alerting → 3-Observability → 4-UI/API Mapping → 5-Cross-Cutting **Depends on:** Plan 6 (UAC residual refactors)

### 8. UAC Package Reorganization (Archived — Complete)

**File:**
[../archive/uac_package_reorganization_f1bc790f.plan.md](../archive/uac_package_reorganization_f1bc790f.plan.md)
**Status:** archived **Completed:** external rename, config/registry moves, provider modes, **all** fix, SIT orphan
test. Remaining work in Plan 6 (residual plan).

### 9. Citadel-Grade UI/API Flow Validation

**File:**
[ui_api_flow_validation_citadel_grade_2026_03_14.plan.md](ui_api_flow_validation_citadel_grade_2026_03_14.plan.md)
**Type:** mixed | **Status:** active | **Gates:** C4/D2 **Scope:** 3-layer testing framework (UI mock / API mock /
real-flow). Critical journey mapping, interaction-level assertions, no-op control detection, fixture drift prevention,
scoring model (90+ = citadel-grade). **Depends on:** Plan 7 (UI/API/Alerting/Observability)

### 10. Interfaces Capability Contract Unification

**File:**
[interfaces_capability_contract_unification_2026_03_14.plan.md](interfaces_capability_contract_unification_2026_03_14.plan.md)
**Type:** mixed | **Status:** active | **Gates:** C5/D3 **Scope:** Unify architecture, import policy, capability
registry, and runtime guardrails across all interface repos (UAC, UMI, URD, UTEI, USEI, UDEI, UPI, UFCL, UIC, UDC, UTL)
and consuming services. Standardize raw→validated→canonical flows, endpoint selection by mode/env/auth scope, fail-fast
errors for unsupported combinations. **Supersedes:** uac-uic-umi-contract-surface-refactor-2026-03-14

---

### 11. Internal Contract Replay and Drift Infrastructure

**File:**
[internal_contract_replay_and_drift_infra_2026_03_14.plan.md](internal_contract_replay_and_drift_infra_2026_03_14.plan.md)
**Type:** infra | **Status:** active | **Gates:** C5/D3 **Scope:** Citadel-grade internal/external contract assurance.
Strict UAC (external) vs UIC (internal) boundaries, deterministic replay gates, live SIT compatibility checks, scheduled
drift recording with approval-only promotion. **Depends on:** Plans 1, 2, 3, 4, 6, 7 (cicd_rollout, cicd_e2e,
integration_tests, sit_build_source, uac_canonical, defi_keys, ui_api_alerting)

---

## Inter-Plan Blocker Diagram

```
Plan 1 (Rollout) Phase 1 ──blocks──> Plan 2 (Testing) Phase 1
Plan 1 (Rollout) Phase 3 ──blocks──> Plan 3 (DeFi) Phase 2
Plan 3 (DeFi) Phase 1   ──blocks──> Plan 1 (Rollout) Phase 5
Plan 1 (Rollout) Phase 4 ──blocks──> Plan 4 (Presentations) demo data
Plan 4 (Presentations)   ──blocks──> Plan 5 (Website) hosting
Plan 6 (UAC Residual)    ──blocks──> Plan 7 (UI/API/Alerting) P0.1 (LogLevel in UAC)
Plan 1 (Rollout)         ──blocks──> Plan 7 (UI/API/Alerting) P3.2 (batch-audit-api BASELINE_PENDING)
Plan 7 (UI/API/Alerting) ──blocks──> Plan 9 (Flow Validation) Phase 1 (createApiClient + smoke tests)
```

---

## Supersession Map (26 old plans → 5 new plans)

| Archived Plan                                   | → New Plan | Phase                |
| ----------------------------------------------- | ---------- | -------------------- |
| master_pre_deployment_plan_chain                | Plan 1     | All                  |
| code_readiness_master_plan_2026_03_11           | Plan 1     | Phase 3-4            |
| phase2_library_tier_hardening                   | Plan 1     | Phase 3              |
| phase3_service_hardening_integration            | Plan 1     | Phase 4              |
| cicd_audit_remediation_2026_03_13               | Plan 1     | Phase 0-1            |
| full_autonomous_agent_ci                        | Plan 1     | Phase 0-2            |
| conflict_resolution_agent_2026_03_13            | Plan 1     | Phase 1-2            |
| composite_action_qg_inheritance_2026_03_12      | Plan 1     | Phase 1-2            |
| aws_migration                                   | Plan 1     | Phase 5              |
| dev_environment_automated_onboarding_2026_03_10 | Plan 1     | Phase 5              |
| ibkr_gateway_rollout                            | Plan 1     | Phase 5              |
| user_management_platform_2026_03_13             | Plan 1     | Phase 6              |
| ui_cloud_mode_indicator_2026_03_12              | Plan 1     | Phase 6              |
| strategy_visibility_grafana_2026_03_10          | Plan 1     | Phase 6              |
| elysium_defi_system_fork_2026_03_10             | Plan 1     | Phase 6              |
| cicd_e2e_test_plan_2026_03_13                   | Plan 2     | All                  |
| api_keys_and_auth                               | Plan 3     | Phase 1-2            |
| data_availability_live_expectations_2026_03_10  | Plan 3     | Phase 3              |
| defi_dev_testnet_data_rollout_2026_03_13        | Plan 3     | Phase 1              |
| production_backfill_step_by_step_2026_03_10     | Plan 3     | Phase 4              |
| board_presentations_update_2026_03_10           | Plan 4     | All                  |
| elysium_defi_presentation_2026_03_10            | Plan 4     | Item 3               |
| gcp_credits_elysium_application_2026_03_10      | Plan 4     | Item 4               |
| website_repo_integration_2026_03_13             | Plan 5     | Item 1               |
| website_content_refresh_2026_03_13              | Plan 5     | Item 2               |
| website_domain_migration_2026_03_13             | Plan 5     | Item 3               |
| website_admin_presentations_2026_03_13          | Plan 5     | Items 4-5            |
| uac_nested_domain_deviations_9a5e89ee           | Plan 6     | Phase 1              |
| uac_package_reorganization_c1c0734e             | Plan 6     | All                  |
| uac_package_reorganization_f1bc790f             | Plan 6     | Archived (complete)  |
| uac_residual_plan_expansion_d27fddf7            | Plan 6     | Executed (meta-plan) |

---

## Phase Progress (2026-03-13)

| Phase   | Name                                                                   | Status                              |
| ------- | ---------------------------------------------------------------------- | ----------------------------------- |
| Phase 0 | Cleanup & Archive Superseded Plans                                     | In Progress (actioned 2026-03-13)   |
| Phase 1 | CI/CD Hardening (7 pipeline bugs + composite QG action + SIT debounce) | In Progress (parallel with Phase 0) |
| Phase 2 | Workflow Rollout (67 repos)                                            | Pending                             |
| Phase 3 | Library Tiers (T0→T3 completion)                                       | Pending                             |
| Phase 4 | Service & UI Hardening                                                 | Pending                             |
| Phase 5 | Deployment Infrastructure                                              | Pending                             |
| Phase 6 | Features & 1.0.0 Stability Gate                                        | Pending                             |

---

## Archived Phase References

**Phase 0:** [phase0_audit_remediation](../archive/phase0_audit_remediation.plan.md) — DONE (2026-03-08) **Phase 0b:**
[phase0_standards_enforcement](../archive/phase0_standards_enforcement.plan.md) — DONE (2026-03-08) **Phase 1:**
[phase1_foundation_prep](../archive/phase1_foundation_prep.plan.md) — DONE (2026-03-08)
