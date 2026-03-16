# Active Plans Index

**Last updated:** 2026-03-16 **Per-repo readiness checklist SSOT:** `unified-trading-codex/10-audit/repos/{repo}.yaml`
(codex v3.0 — CR/DR/BR).

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

### 8. Citadel-Grade UI/API Flow Validation

**File:**
[ui_api_flow_validation_citadel_grade_2026_03_14.plan.md](ui_api_flow_validation_citadel_grade_2026_03_14.plan.md)
**Type:** mixed | **Status:** active (~11/17 done after Wave 1-3) | **Scope:** Flow manifest (done), checker script
(done), CI wiring (done), MockStateStore (done). Remaining: enforcement gates.

### 9. Interfaces Capability Contract Unification

**File:**
[interfaces_capability_contract_unification_2026_03_14.plan.md](interfaces_capability_contract_unification_2026_03_14.plan.md)
**Type:** mixed | **Status:** active (~6/21 done after Wave 3) | **Scope:** Registry (done), error classes (done),
adapter guardrails (done in Wave 3). Remaining: mapping unification, service adoption, test matrix.

### 10. Sports Execution Venue Coverage

**File:** [sports_execution_venue_coverage_2026_03_15.plan.md](sports_execution_venue_coverage_2026_03_15.plan.md)
**Type:** mixed | **Status:** active (~15/23 done) | **Scope:** Venue profiles (done), browser base (done), health
monitor (done), concurrent executor (done). Remaining: adapter hardening (human), arb detection, advanced features.

### 11. Sports Hub — Residual Actions

**File:** [sports_hub_residual_actions_2026_03_15.plan.md](sports_hub_residual_actions_2026_03_15.plan.md) **Type:**
human | **Status:** active (2/12) | **Scope:** All human work: Secret Manager credentials, Playwright CSS selectors,
CAPTCHA, GeoComply. **Depends on:** Plan 10.

### 12. UI Trader Acceptance Testing

**File:** [ui_trader_acceptance_testing_2026_03_15.plan.md](ui_trader_acceptance_testing_2026_03_15.plan.md) **Type:**
human+agent | **Status:** active (0/36) | **Scope:** Smoke tests, visual audit, layout fixes, API mock validation,
stress scenarios, trader sign-off.

---

## Archived Plans (2026-03-16 cleanup)

17 plans archived in this session. See `plans/archive/` for full files.

| Plan                                        | Reason                                                             |
| ------------------------------------------- | ------------------------------------------------------------------ |
| ui_trading_desk_strategy_merge              | Complete (46/46)                                                   |
| uac_citadel_implementation_execution        | Complete (79/79)                                                   |
| liquidation_band_prediction                 | Complete (6/6)                                                     |
| sit_build_source_ci_rollout                 | Complete (10/10)                                                   |
| cross_venue_position_aggregation            | Complete (37/37)                                                   |
| registry_completeness_implementation_detail | Complete (31/31)                                                   |
| uac_citadel_architecture                    | Superseded by completed execution plan                             |
| uac_citadel_implementation                  | Spec doc; execution complete                                       |
| infrastructure_canonical_layer              | Design doc; todos:[]                                               |
| integration_tests_codex_compliance          | Done per completion summary                                        |
| uac_residual_refactors_expanded             | Research doc consumed by active plans                              |
| registry_completeness_refactor              | Superseded by implementation_detail                                |
| uac_residual_refactors_provider_manifest    | Phase 3 done; nesting deferred                                     |
| uac_canonical_normalization_master          | Deferred — current canonical/domain/ layout accepted as final      |
| mode_config_env_architecture                | Deferred — UDC stays separate; Phase 1 env_canon done              |
| uac_citadel_remediation                     | 21/24 done; remainder deferred or tracked in interfaces_capability |
| internal_contract_replay_and_drift_infra    | Deferred — all stubs, blocked by 7 plans                           |

### Architectural Decisions (codified)

- **UAC owns enums** (InstrumentType, Venue) — UCI will re-export
- **LogLevel lives in UIC** — operational config, not external API schema
- **UDC stays separate from UTL** — merge deferred indefinitely
- **Current `canonical/domain/` layout is final** — no restructuring
- **EventSeverity = LogLevel** — backward-compat alias in UIC
