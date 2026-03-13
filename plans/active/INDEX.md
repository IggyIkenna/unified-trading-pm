# Active Plans Index

**Last updated:** 2026-03-13 **Per-repo readiness checklist SSOT:** `unified-trading-codex/10-audit/repos/{repo}.yaml`
(codex v3.0 — CR/DR/BR).

---

## Master Plans (5 Active)

All previous plans have been consolidated into these 5 focused plans with inter-plan blockers. Milestone-gated: each
phase has exit criteria, no dates. Next phase starts only when current passes.

### 1. CI/CD & Code Rollout Master

**File:** [cicd_code_rollout_master_2026_03_13.plan.md](cicd_code_rollout_master_2026_03_13.plan.md) **Type:** mixed |
**Status:** active | **Gates:** C5/D5 **Scope:** Pipeline bug fixes (7 bugs), citadel hardening, workflow rollout to 65
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

## Inter-Plan Blocker Diagram

```
Plan 1 (Rollout) Phase 1 ──blocks──> Plan 2 (Testing) Phase 1
Plan 1 (Rollout) Phase 3 ──blocks──> Plan 3 (DeFi) Phase 2
Plan 3 (DeFi) Phase 1   ──blocks──> Plan 1 (Rollout) Phase 5
Plan 1 (Rollout) Phase 4 ──blocks──> Plan 4 (Presentations) demo data
Plan 4 (Presentations)   ──blocks──> Plan 5 (Website) hosting
```

---

## Supersession Map (26 old plans → 5 new plans)

| Archived Plan                                   | → New Plan | Phase     |
| ----------------------------------------------- | ---------- | --------- |
| master_pre_deployment_plan_chain                | Plan 1     | All       |
| code_readiness_master_plan_2026_03_11           | Plan 1     | Phase 3-4 |
| phase2_library_tier_hardening                   | Plan 1     | Phase 3   |
| phase3_service_hardening_integration            | Plan 1     | Phase 4   |
| cicd_audit_remediation_2026_03_13               | Plan 1     | Phase 0-1 |
| full_autonomous_agent_ci                        | Plan 1     | Phase 0-2 |
| conflict_resolution_agent_2026_03_13            | Plan 1     | Phase 1-2 |
| composite_action_qg_inheritance_2026_03_12      | Plan 1     | Phase 1-2 |
| aws_migration                                   | Plan 1     | Phase 5   |
| dev_environment_automated_onboarding_2026_03_10 | Plan 1     | Phase 5   |
| ibkr_gateway_rollout                            | Plan 1     | Phase 5   |
| user_management_platform_2026_03_13             | Plan 1     | Phase 6   |
| ui_cloud_mode_indicator_2026_03_12              | Plan 1     | Phase 6   |
| strategy_visibility_grafana_2026_03_10          | Plan 1     | Phase 6   |
| elysium_defi_system_fork_2026_03_10             | Plan 1     | Phase 6   |
| cicd_e2e_test_plan_2026_03_13                   | Plan 2     | All       |
| api_keys_and_auth                               | Plan 3     | Phase 1-2 |
| data_availability_live_expectations_2026_03_10  | Plan 3     | Phase 3   |
| defi_dev_testnet_data_rollout_2026_03_13        | Plan 3     | Phase 1   |
| production_backfill_step_by_step_2026_03_10     | Plan 3     | Phase 4   |
| board_presentations_update_2026_03_10           | Plan 4     | All       |
| elysium_defi_presentation_2026_03_10            | Plan 4     | Item 3    |
| gcp_credits_elysium_application_2026_03_10      | Plan 4     | Item 4    |
| website_repo_integration_2026_03_13             | Plan 5     | Item 1    |
| website_content_refresh_2026_03_13              | Plan 5     | Item 2    |
| website_domain_migration_2026_03_13             | Plan 5     | Item 3    |
| website_admin_presentations_2026_03_13          | Plan 5     | Items 4-5 |

---

## Phase Progress (2026-03-13)

| Phase   | Name                                                                   | Status                              |
| ------- | ---------------------------------------------------------------------- | ----------------------------------- |
| Phase 0 | Cleanup & Archive Superseded Plans                                     | In Progress (actioned 2026-03-13)   |
| Phase 1 | CI/CD Hardening (7 pipeline bugs + composite QG action + SIT debounce) | In Progress (parallel with Phase 0) |
| Phase 2 | Workflow Rollout (65 repos)                                            | Pending                             |
| Phase 3 | Library Tiers (T0→T3 completion)                                       | Pending                             |
| Phase 4 | Service & UI Hardening                                                 | Pending                             |
| Phase 5 | Deployment Infrastructure                                              | Pending                             |
| Phase 6 | Features & 1.0.0 Stability Gate                                        | Pending                             |

---

## Archived Phase References

**Phase 0:** [phase0_audit_remediation](../archive/phase0_audit_remediation.plan.md) — DONE (2026-03-08) **Phase 0b:**
[phase0_standards_enforcement](../archive/phase0_standards_enforcement.plan.md) — DONE (2026-03-08) **Phase 1:**
[phase1_foundation_prep](../archive/phase1_foundation_prep.plan.md) — DONE (2026-03-08)
