---
name: Coverage 70% Plan
overview: Achieve MIN_COVERAGE=70% across all Python repos (libraries, services, api-services). T0 first, then T1→T2→T3→services.
todos:
  - id: set-min-coverage
    content: Set MIN_COVERAGE=70 in scripts/quality-gates.sh per repo
    status: completed
  - id: run-pytest-coverage
    content: "Run pytest with coverage; identify gaps in core logic. PER-REPO BASELINE: results recorded in workspace-manifest.json coverage_pct field for each repo (from Phase 0 baseline run). Repos below 70% at baseline must add tests or document exceptions in QUALITY_GATE_BYPASS_AUDIT.md with: current_coverage, target_coverage, reason_for_exception, owner. GATE: all repos with quality-gates.sh have coverage_pct ≥ 70 in workspace-manifest.json, OR have a documented exception entry."
    status: pending
  - id: add-tests
    content: Add tests for core logic; document exceptions in QUALITY_GATE_BYPASS_AUDIT.md only when unavoidable
    status: pending
  - id: t0-t1-first
    content: T0 libraries first → T1 → T2 → T3 → services
    status: pending
isProject: false
---

# Coverage >70% Plan

**Order:** 3 (see master_pre_deployment_plan_chain.plan.md)
**SSOT:** unified-trading-codex/06-coding-standards/quality-gates.md
**Target:** All Python repos (libraries, services, api-services) at MIN_COVERAGE=70%

---

## Blockers

## Implementation Status (2026-03-05)

- **set-min-coverage:** DONE. quality-gates-template.sh updated MIN_COVERAGE 35→70. unified-trading-codex set to 50 (infrastructure). All Python libs/services already had MIN_COVERAGE=70.
- **run-pytest-coverage:** Unblocked. UTS→UTL regex fixes in unified-config-interface and metabet examples in unified-api-contracts applied. Run per-repo.
- **add-tests / t0-t1-first:** Phase 0 baseline recorded (coverage_pct in manifest). quality-gates (12 repos) and RC-1 UFCL aliases resolved.

| Blocker                                                             | Type          | Specific Dependency                                                                                                 | Resolution                                                                                                                                          |
| ------------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 baseline (coverage_pct in manifest) | `[DONE]` | [phase0_standards_enforcement.plan.md](phase0_standards_enforcement.plan.md) § todo `p0-gate-check`                 | Phase 0 records pass/fail + coverage % per repo into workspace-manifest.json; this plan uses that baseline to prioritise which repos need test work |
| quality-gates.sh (DONE — all 12 have it)                            | `[DONE]`      | [phase1_foundation_prep.plan.md](phase1_foundation_prep.plan.md) § todo `ci-add-missing-quality-gates`              | MIN_COVERAGE cannot be enforced in repos that have no quality-gates.sh; must be added first                                                         |
| RC-1: UFCL aliases (DONE — UFCL exports BaseFeatureCalculator etc.) | `[DONE]`      | [unit_tests_and_test_failure_action.plan.md](unit_tests_and_test_failure_action.plan.md) § todo `phase1-quick-wins` | features-calendar-service has 9 collection errors due to missing UFCL aliases; coverage cannot be measured until tests collect successfully         |

---

## Baseline Coverage Targets

| Repo type                  | MIN_COVERAGE | Notes                               |
| -------------------------- | ------------ | ----------------------------------- |
| library                    | 70           | MIN_COVERAGE=70 in quality-gates.sh |
| service                    | 70           | MIN_COVERAGE=70 in quality-gates.sh |
| api-service                | 70           | MIN_COVERAGE=70 in quality-gates.sh |
| infrastructure / docs-only | 50           | MIN_COVERAGE=50 in quality-gates.sh |

> **Phase 0 note:** Coverage targets are part of Phase 0 baseline verification (phase0_standards_enforcement.plan.md). Repos below 70% at Phase 0 must either add tests or document exceptions in QUALITY_GATE_BYPASS_AUDIT.md before Phase 1 begins.

## Current State

| Repo type      | Target | Exceptions             |
| -------------- | ------ | ---------------------- |
| library        | 70%    | Some at 35% (legacy)   |
| service        | 70%    | execution-service ~36% |
| api-service    | 70%    | —                      |
| infrastructure | 50%    | —                      |

---

## Per-Repo Actions

1. Set MIN_COVERAGE=70 in scripts/quality-gates.sh
2. Run pytest with coverage
3. Identify gaps; add tests for core logic
4. Document exceptions in QUALITY_GATE_BYPASS_AUDIT.md only when unavoidable

---

## Execution Order

T0 libraries first → T1 → T2 → T3 → services.
