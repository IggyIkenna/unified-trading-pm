---
name: Master Pre-Deployment Plan Chain
overview: |
  Full ordered plan sequence across all 49 active plans. Grouped into 7 phases.
  Gate rule: each phase must be fully green before the next phase starts.
  CI/CD sequence per repo: lint (ruff) → type check (basedpyright) → unit tests → coverage →
  arch checks → QG pass → quickmerge (feat/* → staging) → SIT validates → staging → main →
  cloud build. No cloud build until main is green. Data catalogue availability is a hard gate
  before live trading.
  Deadlines: all phases complete March 17 → live trading week March 20.
todos:
  - id: phase0-environment
    content: |
      PHASE 0 — Environment & Foundation (MUST COMPLETE FIRST, blocks everything)
      Gate: every repo collects pytest, QG passes, editable installs confirmed.

      Plans (run in parallel where possible):
        - pyrightconfig_venv_fix     : editable installs (uv pip install -e .) for all 60 repos; post-install verify uv pip show
        - pytest-collection-audit   : all 60 repos pass pytest --collect-only -q (DONE for core)
        - workspace_quickmerge_validation : validate-workspace-quickmerge.sh produces green matrix (DONE)
        - workspace_audit_remediation_2026_03_07 : all CRITICAL/HIGH findings resolved; force-push rewritten histories
        - foundational_repos_remediation : 15 agents fixing T0–T3 QG failures; re-run session 2 (usage reset Mar 11)

      GATE: zero repos with QG exit-code != 0 in quickmerge-matrix.json.
    status: in_progress

  - id: phase0b-audit-standards
    content: |
      PHASE 0B — Audit Standards (parallel with Phase 0, same gate)
      Plans:
        - phase0_audit_remediation  : streams 4-5 remediation (streams 1-3 DONE)
        - phase0_standards_enforcement : verify all tiers pass 5-check scan (T0-T3 DONE; confirm services tier)
        - quality_gate_hardening    : cloud-agnostic + protocol enforcement hard-fail (all P0/P1 DONE; verify P2)
        - dependency_governance     : workspace-constraints.toml, uv.lock aligned, no requirements.txt (DONE)

      GATE: phase0_standards_enforcement p0-gate-check exits 0.
    status: in_progress

  - id: phase1-foundation
    content: |
      PHASE 1 — Foundation & Architecture (after Phase 0+0B green, BLOCKS Phase 2)
      Plans (parallel within phase):
        - phase1_foundation_prep         : CI/CD infra live; all 55 repos have quickmerge + commit-msg hook; deployment split complete
        - uci_cloud_abstraction_complete : UCI StorageClient/SecretClient/QueueClient/AnalyticsClient/CacheClient complete; UTL parallel layer deleted
        - uac_schema_normalization_complete : 0 orphaned schemas; 70% UAC test coverage; interfaces own integration tests
        - schema_governance_full_audit   : canonical normalization quality; UIC utilization matrix; cross-contract dedup; STEP 5.12 gate
        - topology_dag_pm_ssot           : TOPOLOGY-DAG.md in PM; PROTOCOL-INJECTION.md in codex; CloudTarget deleted
        - version_cascade_rollout        : version-bump.yml + update-dependency-version.yml propagated to all 59 repos; cascade live
        - orphan-contracts-utilization   : all orphaned UIC/UAC schemas wired to at least one service consumer
        - documentation_standards_enforcement : codex doc standards enforced; all required docs present per service

      GATE: rg 'CloudTarget|os\.getenv|os\.environ' returns 0 hits in service source.
           version cascade e2e test passes (push feat: → verify dep-update dispatched).
    status: pending

  - id: phase2-tier-hardening
    content: |
      PHASE 2 — Library Tier Hardening T0→T1→T2→T3 (after Phase 1, BLOCKS Phase 3)
      INVARIANT: T0 fully green (D5) before T1 starts; T1 before T2; T2 before T3.
      Parallelism is within a tier only. D5 = all 6 QG steps pass + quickmerge --act simulation green.

      Plans (tier-ordered, each must reach D5 before next tier):
        - coverage_70_percent            : 70% coverage on all T0-T3 libs and services; MIN_COVERAGE auto-set per repo
        - strict_basedpyright_compliance : reportAny=error, reportUnknownMemberType=error on all repos; zero type: ignore
        - coding_standards_codex_audit   : ruff clean; no Any; no os.getenv; no try/except ImportError; all codex rules enforced
        - unit_tests_and_test_failure_action : all unit tests pass; no pytest.mark.skip without documented reason; QG fails on test failure
        - schema_contracts_full_audit    : all UIC/UAC import paths correct; no cross-service imports; placement violations = 0
        - schema_versioning_health_matrix_combos : version matrix for all schema×service combos; breaking changes gated

      Person A: T0-T2 (library-heavy)
      Person B: T2-T3 (interface-heavy)

      GATE: D5 for every tier. quickmerge-matrix.json all PASS for T0-T3 repos.
    status: pending

  - id: phase3-service-hardening
    content: |
      PHASE 3 — Service Hardening (after Phase 2 T0+T1 green, T2 and T3 can overlap)
      Plans (parallel within phase):
        - phase3_service_hardening_integration : service bundling ADR; SIT scope defined; all services pass integration smoke tests
        - observability_and_health_endpoints   : /health /ready /metrics on all services; OTel SDK rollout (ASGI middleware, PubSub spans, OTLP exporter); lifecycle event test mandate
        - api_keys_and_auth                    : VCR cassette matrix for all 7 interfaces; GCP auth integration tests; INTEGRATION_TEST_MODE convention documented
        - config_dynamic_injection             : ConfigStore audit trail (immutable log); config replay (get_at_time); deployment-ui Config timeline slider
        - service_protocol_abstraction         : GRPCEventBus in UCI; HivePartitionedSink for BigQuery external tables; get_cloud() factory
        - safety_and_risk_controls             : kill switch wired (DONE); circuit breaker per-venue (DONE); VaR/CVaR framework (DONE); preflight checks
        - var_risk_framework                   : historical_var, parametric_var, cvar, stress_var; Basel III scaling (DONE); risk-and-exposure-service wired
        - execution_service_package_hygiene    : execution-service QG clean; no dead adapters; package structure correct
        - execution_services_hygiene_refactor  : VWAP/sports/mock execution refactor; UI violation (visualizer embedded) fixed

      Plans parallel (sports + IBKR, start after T0+T1 green):
        - sports_migration_gap_fix     : bookmaker login scrapers (Betfair/Smarkets/Betdaq); Phase 1 SM credentials; Phase 2 Playwright scrapers; VCR cassettes scrubbing auth
        - sports_migration_phase2_full : sports arb full pipeline end-to-end
        - ibkr_gateway_rollout         : IBKR gateway infra live; version-bump.yml added; integration tests with VCR

      GATE: all services pass QG. SIT (system-integration-tests) green across T4-T5 services.
           Zero unhandled exceptions in 30-min smoke run.
    status: pending

  - id: phase4-features-strategy
    content: |
      PHASE 4 — Features & Strategy (after Phase 3 T0+T1+T2 green, parallel with Phase 3 T3)
      Plans:
        - citadel_grade_feature_architecture   : feature store design; feature versioning; citadel-grade latency targets
        - polynomial_trendline_wedge_features  : polynomial + trendline + wedge feature implementation; integrated into feature pipeline
        - multi_tf_cascade_signal_architecture : multi-timeframe cascade signal; ML inference pipeline end-to-end
        - strategy_expansion_five_themes       : 5 strategy themes implemented; backtest results per theme

      GATE: at least one strategy per category (Sports, CEFI, TradFi, DeFi) has a passing backtest.
    status: pending

  - id: phase5-pre-deployment-gates
    content: |
      PHASE 5 — Pre-Deployment Gates (after Phase 3 fully green, BLOCKS Phase 6)
      Plans:
        - data_catalogue_refresh          : GCP + AWS availability audit; MVP dataset split (CEFI/TradFi/DeFi/Sports); auto-update YAML on instrument writes; MetadataClient in UCI; canonical schema enforced
        - e2e_smoke_and_portable_backtests: local-service-play (each core service runs locally with mocked deps); portable backtests (all 4 categories); Layer 2 infra verify

      CI/CD SEQUENCE (per repo, in topological order T0→T1→T2→T3→services→APIs→UIs):
        1. ruff check <src>/ → must exit 0
        2. basedpyright <src>/ → zero errors (strict mode)
        3. pytest tests/unit/ → 100% pass, zero skips without bypass doc
        4. coverage >= MIN_COVERAGE (actual - 1%) → fail if drops
        5. arch checks (cloud-agnostic, no cross-service imports, no os.getenv)
        6. quickmerge --unit-only --no-push → QG exit 0
        7. quickmerge feat/* → staging (--to-staging)
        8. SIT validates staging (system-integration-tests green)
        9. staging → main (staging-to-main.yml dispatch)
       10. cloud build ONLY after main green (no speculative deploys)

      DATA GATE: data-catalogue-gcp-availability-report.yaml >= 80% PASS before any live data access.

      GATE: e2e smoke PASS for all 4 strategy categories. Layer 2 infra verify PASS.
           Data catalogue MVP split document complete and reviewed.
    status: pending

  - id: phase6-cloud-build
    content: |
      PHASE 6 — Cloud Build & Infrastructure (after Phase 5 green)
      Plans:
        - aws_migration : cloud-agnostic verification (CLOUD_PROVIDER switch works); buildspec.aws.yaml per service; S3 buckets provisioned; Terraform portable

      CI/CD: cloud build triggers automatically after main merge (cloudbuild.yaml per service).
      Image scan (vulnerability scanning) must pass before image is promoted to prod registry.
      No manual deploy — all deploys via cloud build pipeline.

      GATE: all service images build and pass vulnerability scan. At least one service deployed to staging environment end-to-end.
    status: pending

  - id: phase7-full-audit-live
    content: |
      PHASE 7 — Full Audit → Live Trading (after Phase 6 green)
      Plans:
        - trading_system_audit_prompt        : all sections PASS; grade A or better; <=3 WARN items; 0 FAIL
        - citadel_standard_production_readiness : citadel-grade production checklist complete
        - plans_to_deployable_unified_audit  : confirm all plans reflected in deployed state; no plan gap

      SUCCESS DEFINITION (live trading week, March 20):
        (1) PnL: breakeven or better across 5-day week (total net PnL >= 0)
        (2) Reliability: <=3 unhandled exceptions logged; zero circuit breaker trips
        (3) Execution: all orders placed within 500ms of signal emission (execution_alpha.json latency)
        (4) Coverage: at least one completed live trade per strategy category (sports arb, CEFI ML, TradFi ML, DeFi MVP)
        (5) Audit: trading_system_audit_prompt.plan.md achieves grade A (no FAIL, <=3 WARN)

      GATE: audit grade A. All 4 strategy categories live. Cloud build pipeline stable.
    status: pending

  - id: ongoing-parallel
    content: |
      ONGOING — Parallel / Non-blocking (run any time, do not block phase gates)
        - agent_ci_prototype           : Claude Code GHA prototype (manifest-updated → codex sync)
        - full_autonomous_agent_ci     : full autonomous agent CI with overnight orchestrator
        - documentation_standards_enforcement : enforce codex doc standards per service (non-blocking)
        - schema_versioning_health_matrix_combos : version health matrix (feeds into Phase 2 gate)
    status: pending

isProject: false
---

# Master Pre-Deployment Plan Chain

**Last updated:** 2026-03-07 **Plan inventory:** 49 active plans across 7 phases **Live trading target:** March 20, 2026

---

## Deadlines

| Milestone                    | Date               |
| ---------------------------- | ------------------ |
| Phase 0+0B complete          | **March 11, 2026** |
| Phase 1 complete             | **March 12, 2026** |
| Phase 2 T0+T1 green (D5)     | **March 13, 2026** |
| Phase 2 T2+T3 green (D5)     | **March 14, 2026** |
| Phase 3+4 complete           | **March 15, 2026** |
| Phase 5 pre-deployment gates | **March 16, 2026** |
| Phase 6 cloud build stable   | **March 17, 2026** |
| Phase 7 full audit PASS      | **March 19, 2026** |
| Live trading week begins     | **March 20, 2026** |

---

## Strategy Scope (by March 20)

At least one strategy per category:

| Category   | Strategy                                            | Plan                                 |
| ---------- | --------------------------------------------------- | ------------------------------------ |
| **Sports** | Arb                                                 | sports_migration_phase2_full         |
| **CEFI**   | ML signal                                           | multi_tf_cascade_signal_architecture |
| **TradFi** | ML signal                                           | strategy_expansion_five_themes       |
| **DeFi**   | Staking / lending / recursive staking / basis trade | strategy_expansion_five_themes       |

---

## Phase Map (all 49 plans)

### Phase 0 — Environment & Foundation

| Plan                                   | Status          |
| -------------------------------------- | --------------- |
| pyrightconfig_venv_fix                 | in_progress     |
| pytest-collection-audit                | complete (core) |
| workspace_quickmerge_validation        | complete        |
| workspace_audit_remediation_2026_03_07 | in_progress     |
| foundational_repos_remediation         | in_progress     |

### Phase 0B — Audit Standards (parallel with Phase 0)

| Plan                         | Status      |
| ---------------------------- | ----------- |
| phase0_audit_remediation     | in_progress |
| phase0_standards_enforcement | in_progress |
| quality_gate_hardening       | in_progress |
| dependency_governance        | complete    |

### Phase 1 — Foundation & Architecture

| Plan                                | Status      |
| ----------------------------------- | ----------- |
| phase1_foundation_prep              | in_progress |
| uci_cloud_abstraction_complete      | in_progress |
| uac_schema_normalization_complete   | in_progress |
| schema_governance_full_audit        | in_progress |
| topology_dag_pm_ssot                | in_progress |
| version_cascade_rollout             | in_progress |
| orphan-contracts-utilization        | pending     |
| documentation_standards_enforcement | pending     |

### Phase 2 — Tier Hardening (T0→T1→T2→T3)

| Plan                                   | Status  |
| -------------------------------------- | ------- |
| coverage_70_percent                    | pending |
| strict_basedpyright_compliance         | pending |
| coding_standards_codex_audit           | pending |
| unit_tests_and_test_failure_action     | pending |
| schema_contracts_full_audit            | pending |
| schema_versioning_health_matrix_combos | pending |

### Phase 3 — Service Hardening

| Plan                                 | Status  |
| ------------------------------------ | ------- |
| phase3_service_hardening_integration | pending |
| observability_and_health_endpoints   | pending |
| api_keys_and_auth                    | pending |
| config_dynamic_injection             | pending |
| service_protocol_abstraction         | pending |
| safety_and_risk_controls             | pending |
| var_risk_framework                   | pending |
| execution_service_package_hygiene    | pending |
| execution_services_hygiene_refactor  | pending |
| sports_migration_gap_fix             | pending |
| sports_migration_phase2_full         | pending |
| ibkr_gateway_rollout                 | pending |

### Phase 4 — Features & Strategy

| Plan                                 | Status  |
| ------------------------------------ | ------- |
| citadel_grade_feature_architecture   | pending |
| polynomial_trendline_wedge_features  | pending |
| multi_tf_cascade_signal_architecture | pending |
| strategy_expansion_five_themes       | pending |

### Phase 5 — Pre-Deployment Gates

| Plan                             | Status  |
| -------------------------------- | ------- |
| data_catalogue_refresh           | pending |
| e2e_smoke_and_portable_backtests | pending |

### Phase 6 — Cloud Build & Infrastructure

| Plan          | Status  |
| ------------- | ------- |
| aws_migration | pending |

### Phase 7 — Full Audit → Live Trading

| Plan                                  | Status  |
| ------------------------------------- | ------- |
| trading_system_audit_prompt           | pending |
| citadel_standard_production_readiness | pending |
| plans_to_deployable_unified_audit     | pending |

### Ongoing / Parallel (non-blocking)

| Plan                     | Status  |
| ------------------------ | ------- |
| agent_ci_prototype       | pending |
| full_autonomous_agent_ci | pending |

---

## CI/CD Sequence (per repo, canonical)

```
1. ruff check <src>/                         → exit 0 (lint)
2. basedpyright <src>/                       → 0 errors (strict)
3. pytest tests/unit/                        → 100% pass, 0 unexplained skips
4. coverage >= MIN_COVERAGE (actual - 1%)    → fail if drops
5. arch checks (cloud-agnostic, no os.getenv, no cross-service imports)
6. quickmerge --unit-only --no-push          → QG exit 0
7. quickmerge feat/* → staging               → --to-staging flag
8. SIT validates staging                     → system-integration-tests green
9. staging → main                            → staging-to-main.yml dispatch
10. cloud build                              → ONLY after main green
```

**Data catalogue availability (>= 80% PASS) is a hard gate before any live data access.**

**No cloud build until step 9 is complete. No live trading until Phase 7 audit passes.**

---

## Invariants

1. **Tier invariant:** T0 fully green (D5) before T1 starts; T1 before T2; T2 before T3
2. **Phase gate:** each phase must be fully green before the next phase starts
3. **QG bypass:** any `|| true` or `||true` in QG scripts fails the bypass check — use `|| :`
4. **Editable installs:** all internal packages installed via `uv pip install -e .` — never wheels
5. **No speculative deploys:** cloud build only after main is green
6. **Data gate:** data-catalogue-gcp-availability-report.yaml >= 80% before live trading

---

## Parallel-Work Split (2 People)

### Person A (Track 1)

- Phase 0: pyrightconfig_venv_fix, foundational_repos_remediation (T0-T2)
- Phase 2: T0-T2 tiers (coverage, basedpyright, coding standards)
- Phase 3: UCI/UAC plans, observability, config
- Phase 4: CEFI/TradFi/DeFi backtests
- Phase 6: cloud-agnostic verification

### Person B (Track 2)

- Phase 0: workspace_audit_remediation, foundational_repos_remediation (T3-services)
- Phase 2: T2-T3 tiers
- Phase 3: service hardening, sports, IBKR, execution refactor
- Phase 4: sports arb backtest
- Phase 6: buildspec.aws.yaml per service

---

## References

- `unified-trading-pm/scripts/quickmerge.sh` (--to-staging, --dep-branch, cascade)
- `unified-trading-pm/scripts/repo-management/run-all-setup.sh` (topological order setup)
- `unified-trading-pm/scripts/validate-workspace-quickmerge.sh` (quickmerge matrix)
- `unified-trading-pm/docs/repo-management/version-cascade-flow.md` (three-tier model SSOT)
- `unified-trading-codex/06-coding-standards/README.md` (coding standards)
- `system-integration-tests/` (SIT scope: T4-T5 services, alerting-service, deployment-api; excludes all UI repos)
