---
name: Coverage 70% Plan
overview:
  Achieve MIN_COVERAGE=70% across all Python repos (libraries, services, api-services). T0 first, then
  T1→T2→T3→services.
todos:
  - id: set-min-coverage
    content: Set MIN_COVERAGE=70 in scripts/quality-gates.sh per repo
    status: completed
  - id: run-pytest-coverage
    content:
      "PARTIALLY DONE (2026-03-06): T0 libs verified: unified-internal-contracts=99%, unified-events-interface=97%. 14
      UI/infra repos marked EXEMPT (N/A) in workspace-manifest.json. features-delta-one-service FIXED: 70.72% (commit
      4285483). Remaining below 70%: unified-market-interface=40% (BLOCKER: local venv has outdated
      unified_api_contracts missing CanonicalFundingRate), client-reporting-api=18% (BLOCKER: venv dep mismatch),
      features-volatility-service=35% (BLOCKER: unified_internal_contracts missing from repo .venv),
      features-cross-instrument-service=0% (PARTIAL QG — uv sync fails, unified-cloud-interface not in PyPI),
      ml-training-service=35% (not yet attempted)."
    status: pending
  - id: add-tests
    content:
      "PARTIALLY DONE (2026-03-06): T0 libs: unified-internal-contracts=99.73%, unified-events-interface=97%.
      features-delta-one-service: 70.72% (8 new test files — polars optimizations, timeframe resampler, numba kernels,
      output schemas, futures roll adjuster, multi-period features, trendline, weekly anchors, validate_args; also fixed
      Dict import bug in multi_period_features.py). Remaining: unified-market-interface, client-reporting-api,
      features-volatility-service, features-cross-instrument-service, ml-training-service all blocked by per-repo venv
      dep mismatches."
    status: pending
  - id: t0-t1-first
    content:
      "DONE T0 (2026-03-06): unified-internal-contracts=99%, unified-events-interface=97%. T1 (UTL, UCI, URDI) already
      above 70% per manifest. T2 unified-market-interface=40% BLOCKED. Services: features-delta-one-service=71% DONE.
      Others blocked by venv dep mismatches."
    status: pending
isProject: false
---

# Coverage >70% Plan

**Order:** 3 (see master_pre_deployment_plan_chain.plan.md) **SSOT:**
unified-trading-codex/06-coding-standards/quality-gates.md **Target:** All Python repos (libraries, services,
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

| Blocker                                                             | Type     | Specific Dependency                                                                                                 | Resolution                                                                                                                                          |
| ------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 baseline (coverage_pct in manifest)                         | `[DONE]` | [phase0_standards_enforcement.plan.md](phase0_standards_enforcement.plan.md) § todo `p0-gate-check`                 | Phase 0 records pass/fail + coverage % per repo into workspace-manifest.json; this plan uses that baseline to prioritise which repos need test work |
| quality-gates.sh (DONE — all 12 have it)                            | `[DONE]` | [phase1_foundation_prep.plan.md](phase1_foundation_prep.plan.md) § todo `ci-add-missing-quality-gates`              | MIN_COVERAGE cannot be enforced in repos that have no quality-gates.sh; must be added first                                                         |
| RC-1: UFCL aliases (DONE — UFCL exports BaseFeatureCalculator etc.) | `[DONE]` | [unit_tests_and_test_failure_action.plan.md](unit_tests_and_test_failure_action.plan.md) § todo `phase1-quick-wins` | features-calendar-service has 9 collection errors due to missing UFCL aliases; coverage cannot be measured until tests collect successfully         |

---

## Baseline Coverage Targets

| Repo type                  | MIN_COVERAGE | Notes                               |
| -------------------------- | ------------ | ----------------------------------- |
| library                    | 70           | MIN_COVERAGE=70 in quality-gates.sh |
| service                    | 70           | MIN_COVERAGE=70 in quality-gates.sh |
| api-service                | 70           | MIN_COVERAGE=70 in quality-gates.sh |
| infrastructure / docs-only | 50           | MIN_COVERAGE=50 in quality-gates.sh |

> **Phase 0 note:** Coverage targets are part of Phase 0 baseline verification (phase0_standards_enforcement.plan.md).
> Repos below 70% at Phase 0 must either add tests or document exceptions in QUALITY_GATE_BYPASS_AUDIT.md before Phase 1
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
