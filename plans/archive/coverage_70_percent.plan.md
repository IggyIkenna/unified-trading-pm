---
doc_type: plan
title: Coverage 70% Plan
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-05"
overview:
  Achieve MIN_COVERAGE=70% across all Python repos (libraries, services, api-services). T0 first, then
  T1→T2→T3→services.
todos:
  - { id: set-min-coverage, content: Set MIN_COVERAGE=70 in scripts/quality-gates.sh per repo, status: completed }
  - {
      id: run-pytest-coverage,
      content:
        "DONE (2026-03-08): All T0-T2 library repos verified at or above their fail_under threshold.
        unified-events-interface=100% (was 89%, fail_under=99 — ComplianceEventPayload tests added).
        unified-internal-contracts=100% (was 97%, fail_under=99 — features_commodity + features_sports domain tests
        added). unified-api-contracts=80.35% (fail_under=80 — PASS). unified-trading-library=80.21% (fail_under=80 —
        PASS). unified-cloud-interface=84.15% (fail_under=70 — PASS). unified-market-interface=74.09% (fail_under=70 —
        PASS, was 40% blocked in prior session). unified-feature-calculator-library=94.99% (fail_under=93 — PASS). 14
        UI/infra repos marked EXEMPT (N/A). features-delta-one-service=70.72% DONE (commit 4285483).",
      status: completed,
    }
  - {
      id: add-tests,
      content:
        "DONE (2026-03-08): T0 libs at 100%: unified-internal-contracts (features_commodity/__init__.py +
        features_sports/__init__.py — test_coverage_gaps_features_domain.py, 26 tests) and unified-events-interface
        (ComplianceEventPayload — 18 tests added to test_schemas.py). Earlier sessions: features-delta-one-service
        70.72% (8 new test files). All T0-T2 library repos now at or above their configured fail_under threshold.",
      status: completed,
    }
  - {
      id: t0-t1-first,
      content:
        "DONE (2026-03-08): T0: unified-internal-contracts=100%, unified-events-interface=100%,
        unified-api-contracts=80.35%. T1: unified-trading-library=80.21%, unified-cloud-interface=84.15%. T2:
        unified-market-interface=74.09%, unified-feature-calculator-library=94.99%. Services:
        features-delta-one-service=71% DONE. All T0-T2 library repos pass fail_under.",
      status: completed,
    }
isProject: false
---

# Coverage >70% Plan

**Order:** 3 (see master_pre_deployment_plan_chain.md) **SSOT:**
unified-trading-/codex/06-coding-standards/quality-gates.md **Target:** All Python repos (libraries, services,
api-services) at MIN_COVERAGE=70%

---

## Blockers

## Implementation Status (2026-03-05)

- **set-min-coverage:** DONE. quality-gates-template.sh updated MIN_COVERAGE 35→70. unified-trading-codex set to 50
  (infrastructure). All Python libs/services already had MIN_COVERAGE=70.
- **run-pytest-coverage:** Unblocked. UTS→UTL regex fixes in unified-config-interface and metabet examples in
  unified-api-contracts applied. Run per-repo.
- **add-tests / t0-t1-first:** Phase 0 baseline recorded (coverage_pct in manifest). quality-gates (12 repos) and RC-1
  UFCL aliases resolved.

| Blocker                                                             | Type     | Specific Dependency                                                                                       | Resolution                                                                                                                                          |
| ------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 baseline (coverage_pct in manifest)                         | `[DONE]` | [phase0_standards_enforcement.md](phase0_standards_enforcement.md) § todo `p0-gate-check`                 | Phase 0 records pass/fail + coverage % per repo into workspace-manifest.json; this plan uses that baseline to prioritise which repos need test work |
| quality-gates.sh (DONE — all 12 have it)                            | `[DONE]` | [phase1_foundation_prep.md](phase1_foundation_prep.md) § todo `ci-add-missing-quality-gates`              | MIN_COVERAGE cannot be enforced in repos that have no quality-gates.sh; must be added first                                                         |
| RC-1: UFCL aliases (DONE — UFCL exports BaseFeatureCalculator etc.) | `[DONE]` | [unit_tests_and_test_failure_action.md](unit_tests_and_test_failure_action.md) § todo `phase1-quick-wins` | features-calendar-service has 9 collection errors due to missing UFCL aliases; coverage cannot be measured until tests collect successfully         |

---

## Baseline Coverage Targets

| Repo type                  | MIN_COVERAGE | Notes                               |
| -------------------------- | ------------ | ----------------------------------- |
| library                    | 70           | MIN_COVERAGE=70 in quality-gates.sh |
| service                    | 70           | MIN_COVERAGE=70 in quality-gates.sh |
| api-service                | 70           | MIN_COVERAGE=70 in quality-gates.sh |
| infrastructure / docs-only | 50           | MIN_COVERAGE=50 in quality-gates.sh |

> **Phase 0 note:** Coverage targets are part of Phase 0 baseline verification (phase0_standards_enforcement.md). Repos
> below 70% at Phase 0 must either add tests or document exceptions in QUALITY_GATE_BYPASS_AUDIT.md before Phase 1
> begins.

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
