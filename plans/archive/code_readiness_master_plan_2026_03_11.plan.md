---
doc_type: plan
title: code-readiness-master-plan
summary: 'Per-repo Code Readiness (CR/DR/BR) stage tracker for all 65 manifest repos, grouped by tier.

  Defines the 5-stage CR progression (functionality → unit tests → integration tests → QG → quickmerge).

  Sub-plans own the implementation todos; this plan is the authoritative readiness state tracker.'
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-ui, execution-service, strategy-service, system-integration-tests, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-12'
type: mixed
epic: epic-code-completion
superseded_by: cicd_code_rollout_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C5, deployment: D4, business: B8}
repo_gates:
- {repo: unified-api-contracts, code: C4, deployment: none, business: none, readiness_note: CR4 reached (QG green locally). CR5 pending quickmerge. CR3 N/A (zero manifest deps). DR/BR pending.}
- {repo: unified-internal-contracts, code: C4, deployment: none, business: none, readiness_note: CR4 reached. CR3 N/A (zero manifest deps). DR/BR pending.}
- {repo: unified-events-interface, code: C4, deployment: none, business: none, readiness_note: CR4 reached (71/71 tests). CR3 N/A (zero manifest deps). DR/BR pending.}
- {repo: unified-cloud-interface, code: C4, deployment: none, business: none, readiness_note: 'CR4 reached. CR3 integration: GCS/PubSub/BigQuery emulators required. DR/BR pending.'}
- {repo: execution-algo-library, code: C4, deployment: none, business: none, readiness_note: CR4 reached (94/94 tests). CR3 N/A (zero manifest deps). DR/BR N/A (library). BR2 N/A.}
- {repo: matching-engine-library, code: C4, deployment: none, business: none, readiness_note: CR4 reached (83/83 tests). CR3 N/A (zero manifest deps). DR/BR N/A (library). BR2 N/A.}
- {repo: unified-trading-library, code: C4, deployment: none, business: none, readiness_note: 'CR4 reached (1000+ tests, QG --quick pass). CR3: UTL→UEI dep integration pending. DR/BR pending.'}
- {repo: unified-reference-data-interface, code: C4, deployment: none, business: none, readiness_note: 'CR4 reached (227/227 tests). CR3: URDI→UCI dep integration pending. DR/BR pending.'}
- {repo: unified-config-interface, code: C4, deployment: none, business: none, readiness_note: 'CR4 reached (608/608 tests). CR3: UCI→UEI dep integration pending. DR/BR pending.'}
- {repo: unified-sports-execution-interface, code: C1, deployment: none, business: none, readiness_note: Scaffolded status. CR1 in progress. Phase 3 plan tracks this repo.}
- {repo: unified-market-interface, code: C2, deployment: none, business: none, readiness_note: 'CR2 reached (2160/2160 tests). CR3: 12 URDI stubs pending (vcr-urdi-parse-raw-umi-stubs). D3 basedpyright partial (67 errors — extraPaths gap). CR4 blocked on basedpyright fix.'}
- {repo: unified-trade-execution-interface, code: C2, deployment: none, business: none, readiness_note: CR2 reached (203/203 tests). CR3 pending. CR4 blocked on basedpyright cleanup.}
- {repo: unified-ml-interface, code: C2, deployment: none, business: none, readiness_note: CR2 reached (413/413 tests). CR3 pending. CR4 reached (0 basedpyright errors after extraPaths fix).}
- {repo: unified-feature-calculator-library, code: C2, deployment: none, business: none, readiness_note: CR2 reached (203/203 tests). CR3 pending. CR4 status unknown — audit required.}
- {repo: unified-defi-execution-interface, code: C2, deployment: none, business: none, readiness_note: CR2 reached (94/94 tests). CR3 pending. CR4 blocked (78 basedpyright errors — pydantic/uniswap).}
- {repo: unified-position-interface, code: C0, deployment: none, business: none, readiness_note: Future status — repo absent from workspace. Skip all stages.}
- {repo: unified-domain-client, code: C2, deployment: none, business: none, readiness_note: 'CR2 reached (385/385 tests, 0 basedpyright errors). CR3: UDC deps are T0+T1+T2 — all integration tests pending. CR4 blocked on lib-phase1-udc-tier2-compliance (UTS→UCLI migration).'}
- {repo: instruments-service, code: C0, deployment: none, business: none, readiness_note: Phase 3 service hardening — blocked on Phase 2 T0–T3 all CR5.}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on instruments-service CR5.}
- {repo: market-data-processing-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on market-tick-data-service CR5.}
- {repo: features-calendar-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on MDPS CR5.}
- {repo: features-delta-one-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on MDPS CR5.}
- {repo: features-volatility-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on MDPS CR5.}
- {repo: features-onchain-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on MDPS CR5.}
- {repo: features-sports-service, code: C0, deployment: none, business: none, readiness_note: Scaffolded. Phase 3. Blocked on MDPS CR5.}
- {repo: features-multi-timeframe-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on MDPS CR5.}
- {repo: features-cross-instrument-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on MDPS CR5.}
- {repo: features-commodity-service, code: C0, deployment: none, business: none, readiness_note: Scaffolded. Phase 3. Blocked on MDPS CR5.}
- {repo: ml-training-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on features services CR5.}
- {repo: ml-inference-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on ML training CR5.}
- {repo: strategy-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on ML inference CR5.}
- {repo: execution-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on strategy-service CR5. QG script 59L (>50 stub threshold FAIL from audit).}
- {repo: alerting-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on execution-service CR5.}
- {repo: pnl-attribution-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on execution-service CR5.}
- {repo: position-balance-monitor-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on execution-service CR5.}
- {repo: risk-and-exposure-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on execution-service CR5.}
- {repo: strategy-validation-service, code: C0, deployment: none, business: none, readiness_note: Scaffolded. Phase 3.}
- {repo: batch-live-reconciliation-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on execution-service + pnl-attribution CR5.}
- {repo: trading-agent-service, code: C0, deployment: none, business: none, readiness_note: Scaffolded. Phase 3.}
- {repo: execution-results-api, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on execution-service CR5.}
- {repo: market-data-api, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on MDPS CR5.}
- {repo: client-reporting-api, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on pnl-attribution-service CR5.}
- {repo: ml-inference-api, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on ml-inference-service CR5.}
- {repo: ml-training-api, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on ml-training-service CR5.}
- {repo: trading-analytics-api, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on strategy-service + execution-service CR5.}
- {repo: batch-audit-api, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on batch-live-reconciliation-service CR5.}
- {repo: strategy-ui, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on T5 API CR5. BR2/BR5 N/A (UI). vitest required per audit.}
- {repo: deployment-ui, code: C1, deployment: none, business: none, readiness_note: Scaffolded. Vitest tests missing (audit §16 FAIL). BR2/BR5 N/A.}
- {repo: unified-admin-ui, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on API CR5.}
- {repo: batch-audit-ui, code: C0, deployment: none, business: none, readiness_note: Vitest missing (audit §16 FAIL). BR2/BR5 N/A.}
- {repo: trading-analytics-ui, code: C0, deployment: none, business: none, readiness_note: Vitest missing (audit §16 FAIL). BR2/BR5 N/A.}
- {repo: live-health-monitor-ui, code: C0, deployment: none, business: none, readiness_note: Phase 3. BR2/BR5 N/A.}
- {repo: client-reporting-ui, code: C0, deployment: none, business: none, readiness_note: Phase 3. BR2/BR5 N/A.}
- {repo: logs-dashboard-ui, code: C0, deployment: none, business: none, readiness_note: Phase 3. BR2/BR5 N/A.}
- {repo: onboarding-ui, code: C0, deployment: none, business: none, readiness_note: Phase 3. BR2/BR5 N/A.}
- {repo: settlement-ui, code: C0, deployment: none, business: none, readiness_note: Phase 3. BR2/BR5 N/A.}
- {repo: execution-analytics-ui, code: C0, deployment: none, business: none, readiness_note: Vitest missing (audit §16 FAIL). BR2/BR5 N/A.}
- {repo: ml-training-ui, code: C0, deployment: none, business: none, readiness_note: Phase 3. BR2/BR5 N/A.}
- {repo: unified-trading-ui-auth, code: C0, deployment: none, business: none, readiness_note: Library-type UI component. BR2/BR5 N/A.}
- {repo: ibkr-gateway-infra, code: C0, deployment: none, business: none, readiness_note: Infrastructure repo. DR gates primary. BR N/A mostly.}
- {repo: deployment-service, code: C0, deployment: none, business: none, readiness_note: Phase 3. QG 59L stub threshold (audit FAIL). DR gates primary.}
- {repo: deployment-api, code: C0, deployment: none, business: none, readiness_note: Phase 3. Blocked on deployment-service CR5.}
- {repo: system-integration-tests, code: C0, deployment: none, business: none, readiness_note: Scaffolded. SIT suite owns DR4 validation for all other repos.}
- {repo: unified-trading-codex, code: C0, deployment: none, business: none, readiness_note: Infrastructure. CR/DR/BR not applicable in same way — codex sync agent owns this.}
- {repo: unified-trading-pm, code: C5, deployment: none, business: none, readiness_note: PM repo — this plan lives here. CR5 reached. DR/BR N/A.}
depends_on: [plan-readiness-gates-overhaul]
todos:
---

 T0 Tier ---
  - id: cr-t0-cr5
    content:
      "T0 TIER: Push all 6 T0 repos (UEI, AC, UIC, UCI, EAL, MEL) to CR5 — quickmerge to feat/code-readiness-t0 branch
      per repo. Gate: CI passes. INVARIANT: T0 must be CR5 before T1 promoted to CR5."
    status: in_progress
    note:
      "CR4 reached on all 6 repos (D1/D2/D3 PASS per phase2 plan). D4/D5 quickmerge pending. Sub-plan:
      phase2_library_tier_hardening.md t0-progressive-validation."

  - id: cr-t0-cr3
    content:
      "T0 INTEGRATION: Verify CR3 for T0 repos with manifest deps (UCI→UEI, UCI→AC). All zero-dep repos (EAL, MEL, UEI,
      AC, UIC) satisfy CR3 automatically. Write tests/integration/test_uei_integration.py for UCI if not present."
    status: todo
    note:
      "Most T0 repos have zero manifest deps — CR3 auto-satisfied. UCI has deps: UEI, AC. Need integration test
      verification."

  # --- T1 Tier ---
  - id: cr-t1-cr5
    content:
      "T1 TIER: Push UTL and URDI to CR5. REQUIRES T0 all CR5. Sub-plan todos: t1-uts-code-rewrite (UTL rename),
      t1-uts-progressive-validation (D5). URDI: verify QG passes post URDI setup (t0-code-rewrite DONE)."
    status: todo
    note: "Blocked on T0 CR5. Sub-plan: phase2_library_tier_hardening.md t1-uts-progressive-validation."
    blocked_by: cr-t0-cr5

  - id: cr-t1-cr3
    content:
      "T1 INTEGRATION: Write integration tests for T1 repos against their manifest deps. UTL→UEI:
      test_uts_uei_integration.py. URDI→UCI: test_urdi_uci_integration.py. All tests credential-free."
    status: todo
    note: "Blocked on T0 CR5."
    blocked_by: cr-t0-cr5

  # --- T2 Tier ---
  - id: cr-t2-cr5
    content:
      "T2 TIER: Push UMI, UTEI, UML, UFC, UDEI, USEI to CR5. REQUIRES T0+T1 all CR5. Fix UMI basedpyright (67 errors —
      extraPaths). Fix UDEI basedpyright (78 errors). Sub-plan: phase2_library_tier_hardening.md t2-*."
    status: todo
    note: "Blocked on T1 CR5."
    blocked_by: cr-t1-cr5

  - id: cr-t2-cr3
    content:
      "T2 INTEGRATION: Write integration tests for each T2 repo against manifest deps. UMI→UEI+UCI+AC. UTEI→UEI+UCI.
      UML→UEI. UFC→UEI+UCI. UDEI→UEI+UCI. USEI→UEI+UCI."
    status: todo
    note: "Blocked on T1 CR5."
    blocked_by: cr-t1-cr5

  # --- T3 Tier ---
  - id: cr-t3-cr5
    content:
      "T3 TIER: Push UDC to CR5. REQUIRES T0+T1+T2 all CR5. Complete t3-udc-code-rewrite (UCLI migration),
      t3-udc-progressive-validation (D5). Sub-plan: phase2_library_tier_hardening.md t3-* todos."
    status: todo
    note: "Blocked on T2 CR5."
    blocked_by: cr-t2-cr5

  - id: cr-t3-cr3
    content:
      "T3 INTEGRATION: UDC→T0+T1+T2 integration tests. Key deps: UEI, UCI, UMI, UTEI, UML. Write
      test_udc_uei_integration.py, test_udc_uci_integration.py, test_udc_umi_integration.py at minimum."
    status: todo
    note: "Blocked on T2 CR5."
    blocked_by: cr-t2-cr5

  # --- Services ---
  - id: cr-services-cr1
    content:
      "SERVICES FUNCTIONALITY AUDIT: Run functionality audit (§2 of trading_system_audit_prompt) against all 22 service
      repos. Identify repos at CR0 vs CR1. Create sub-tasks for any CR0 repo with incomplete stubs or missing core
      logic. Sub-plan: phase3_service_hardening_integration.md."
    status: todo
    note: "Blocked on T3 CR5. Phase 3 plan owns individual service todos."
    blocked_by: cr-t3-cr5

  - id: cr-services-cr2
    content:
      "SERVICES UNIT TESTS: All 22 service repos reach CR2 (unit tests 100% passing, coverage ≥ 70%). Fix skipped tests.
      Re-run --cov-report=xml for audit reads. Sub-plan: phase3_service_hardening_integration.md."
    status: todo
    blocked_by: cr-services-cr1

  - id: cr-services-cr3
    content:
      "SERVICES INTEGRATION: Every service integration-tests against its direct manifest deps (not just mocked). For
      each service: list deps from manifest, verify tests/integration/ covers each dep. Credential-free emulators/mocks."
    status: todo
    blocked_by: cr-services-cr2

  - id: cr-services-cr4
    content:
      "SERVICES QG: All 22 service repos pass quality-gates.sh Pass 1 fully. Fix execution-service QG script (59L stub
      threshold FAIL). Fix any repos with basedpyright errors."
    status: todo
    blocked_by: cr-services-cr3

  - id: cr-services-cr5
    content:
      "SERVICES QUICKMERGE: All 22 service repos quickmerge to feat/code-readiness-<repo>. CI must pass. This unlocks
      API and UI tier."
    status: todo
    blocked_by: cr-services-cr4

  # --- APIs ---
  - id: cr-apis-cr5
    content:
      "APIS: All 7 API repos (ERA, MDA, CRA, MLIA, MLTA, TAA, BAA) reach CR5. Sub-plan:
      phase3_service_hardening_integration.md T5 section."
    status: todo
    blocked_by: cr-services-cr5

  # --- UIs ---
  - id: cr-uis-vitest
    content:
      "UIs VITEST: Fix vitest missing on deployment-ui, batch-audit-ui, trading-analytics-ui, execution-analytics-ui
      (audit §16 FAIL). Add vitest.config.ts, write component unit tests. Sub-plan: ui-audit-results.md action items."
    status: todo
    note: "Can run in parallel with T0–T3 service work."

  - id: cr-uis-cr5
    content: "UIs CR5: All 13 UI repos reach CR5 after vitest fixed and T5 API CR5 reached."
    status: todo
    blocked_by: cr-apis-cr5

  # --- Deployment Readiness ---
  - id: dr-t0-dr3
    content:
      "DR T0: Deploy all T0 library wheels to Artifact Registry from CI. Verify downstream install passes. DR3 N/A for
      pure libraries (not Cloud Run deployed) — declare explicitly in repo_gates readiness_note."
    status: todo
    note: "Libraries don't get Cloud Run DR3. AR publish is their DR equivalent. Update readiness_notes once confirmed."

  - id: dr-services-dr3
    content:
      "DR SERVICES: Deploy all service repos to feature Cloud Run environment. Verify GET /health and GET /readiness.
      Blocked on CR5 + cloud infra provisioned (api_keys_and_auth.md)."
    status: todo
    blocked_by: cr-services-cr5

  - id: dr-sit-dr4
    content:
      "DR ALL: Run system-integration-tests full suite with all services deployed to staging. Every service that fails
      SIT gets a bug filed immediately. DR4 gate for all service + API repos."
    status: todo
    blocked_by: dr-services-dr3

  # --- Business Readiness (Circuit Breaker + Events + PnL) ---
  - id: br-circuit-breaker
    content:
      "BR2 CIRCUIT BREAKER: For each revenue-path service (execution-service, strategy-service,
      risk-and-exposure-service, alerting-service, pnl-attribution-service): run FaultInjectionTransport tests; verify
      CLOSED→OPEN→HALF_OPEN transitions; PubSub propagation from alerting-service. BR2 declared N/A for libraries, UIs,
      infrastructure repos."
    status: todo
    blocked_by: dr-services-dr3

  - id: br-event-handling
    content:
      "BR3 EVENT HANDLING: For every repo that calls log_event() or setup_events(): run integration test that verifies
      event fires with correct schema, correct correlation_id, and correct UEI event type. Use PubSub emulator. Map
      every UEI event type per service."
    status: todo
    blocked_by: cr-services-cr5

  - id: br-pnl-targets
    content:
      "BR4/BR5 PNL: Declare domain KPIs per revenue-path repo. Run backtests (e2e_smoke_and_portable_backtests.md).
      Verify: strategy-service Sharpe ≥ target; execution-service alpha ≥ benchmark; pnl-attribution-service accuracy ≥
      threshold. Store backtest artifacts in GCS."
    status: todo
    blocked_by: dr-sit-dr4

  # --- v1.0.0 Gate ---
  - id: v100-readiness-check
    content:
      "v1.0.0 READINESS: After all CR/DR/BR stages complete for a given tier, run the per-repo v1.0.0 checklist (from
      semver-v1-hardening.mdc) against each repo. Present results to user. Do NOT set 1.0.0 — wait for user approval
      (BR8) per repo."
    status: todo
    note:
      "This is the only todo that requires user interaction to complete. Agent prepares the checklist; user approves."
    blocked_by: br-pnl-targets

isProject: true
---

# Code Readiness Master Plan

## Purpose

This plan is the **authoritative readiness state tracker** for all 65 repos in the workspace manifest. It tracks
per-repo progression through CR (Code Readiness), DR (Deployment Readiness), and BR (Business Readiness) stages.

**This plan does not own implementation todos** — those belong in the sub-plans listed below. This plan owns the
aggregate stage state and the tier-blocking invariants.

---

## Sub-Plans (Own the Implementation)

| Scope                            | Sub-Plan                                            | Status      |
| -------------------------------- | --------------------------------------------------- | ----------- |
| T0–T3 library hardening          | `phase2_library_tier_hardening.md`                  | IN_PROGRESS |
| T4–T6 service hardening          | `phase3_service_hardening_integration.md`           | PENDING     |
| UI vitest / component tests      | `ui-audit-results.md` action items                  | PENDING     |
| SIT deployment                   | `production_mock_e2e_plan_d90c8f20.md`              | IN_PROGRESS |
| Portable backtests / PnL         | `e2e_smoke_and_portable_backtests.md`               | IN_PROGRESS |
| Cloud infra / API keys           | `api_keys_and_auth.md`                              | ACTIVE      |
| Performance testing              | `performance_testing_load_benchmarks_2026_03_10.md` | PENDING     |
| Circuit breaker + event handling | `stub_completion_interfaces_and_infra.md`           | ACTIVE      |

---

## Per-Repo Stage Definitions

Full definition: `unified-trading-pm/docs/REPO_READINESS_CHECKLIST.md`

### Code Readiness (CR) — 5 Stages

1. **CR1 — Functionality 100%**: Zero stubs, zero `NotImplementedError`, zero `TODO`/`FIXME` in prod paths. Audit §2
   passes.
2. **CR2 — Unit tests 100%**: QG unit stage green, coverage ≥ floor, zero unexplained skips, `--cov-report=xml` current.
3. **CR3 — Integration tests 100%**: Every direct manifest dep exercised in `tests/integration/` with emulators/mocks.
   Zero-dep repos auto-satisfy.
4. **CR4 — Quality gate locally green**: `bash scripts/quality-gates.sh` Pass 1 fully green. No bypass shortcuts.
5. **CR5 — Quickmerge to feature branch**: CI passes on `feat/code-readiness-<repo>`. PR created.

### Tier Blocking Invariant (Readiness Promotion)

```
T0 all CR5 → T1 CR5 unblocked
T0+T1 all CR5 → T2 CR5 unblocked
T0+T1+T2 all CR5 → T3 CR5 unblocked
T3 CR5 → Services (T4) CR5 unblocked
T4 CR5 → APIs (T5) CR5 unblocked
T5 CR5 → UIs (T6) CR5 unblocked
```

### Deployment Readiness (DR) — 6 Stages

DR1 (infra) → DR2 (CI smoke) → DR3 (feature env deployed) → DR4 (staging SIT) → DR5 (load/perf) → DR6 (prod-ready)

Libraries: DR3–DR6 declared N/A (libraries are AR packages, not Cloud Run services). DR equivalent is AR publish passing
CI.

### Business Readiness (BR) — 8 Stages

BR1 (acceptance criteria) → BR2 (circuit breaker) → BR3 (event handling) → BR4 (PnL targets) → BR5 (PnL optimization) →
BR6 (batch vs live) → BR7 (staging parity) → BR8 (user approved)

---

## Current Readiness Snapshot (2026-03-11)

| Tier           | Repos    | Best CR | CR3 Status                          | Notes                           |
| -------------- | -------- | ------- | ----------------------------------- | ------------------------------- |
| T0             | 6 repos  | CR4     | Auto-satisfied (zero deps for most) | D4/D5 quickmerge pending        |
| T1             | 3 repos  | CR4     | Integration tests pending           | UTL rename pending              |
| T2             | 6 repos  | CR2     | Integration tests pending           | Basedpyright errors in UMI/UDEI |
| T3             | 1 repo   | CR2     | Integration tests pending           | UTS migration pending           |
| T4 services    | 22 repos | CR0     | Blocked on T3 CR5                   | Phase 3 not started             |
| T5 APIs        | 7 repos  | CR0     | Blocked on T4 CR5                   | Phase 3 not started             |
| T6 UIs         | 13 repos | CR0–CR1 | Blocked on T5 CR5                   | Vitest missing on 4 repos       |
| Infrastructure | 6 repos  | CR0–CR5 | N/A                                 | PM at CR5                       |

**All repos at 0.x.x** — no repo has reached v1.0.0 (audit §7 FAIL, 2026-03-11).

---

## v1.0.0 Promotion Policy

1. Agent runs the per-repo checklist from `docs/REPO_READINESS_CHECKLIST.md § v1.0.0 Gate`
2. Agent presents results to user: which gates are met, which are N/A with reason, which are unmet
3. Every unmet item must be in an active plan with a completion timeline
4. User reviews and gives explicit approval (BR8)
5. After BR8: agent updates this plan's `repo_gates` for that repo, then creates the version PR

**No agent may autonomously promote any repo to 1.0.0.** Rule: `cursor-rules/core/semver-v1-hardening.mdc`

---

## References

- SSOT checklist: `unified-trading-pm/docs/REPO_READINESS_CHECKLIST.md`
- Semver rule: `unified-trading-pm/cursor-rules/core/semver-v1-hardening.mdc`
- Readiness cursor rule: `unified-trading-pm/cursor-rules/core/repo-readiness-checklist.mdc`
- Plan format: `unified-trading-pm/plans/PLAN_FORMAT.md`
- Phase gate (deployment-oriented): `unified-trading-pm/docs/phase-gate-checklist.md`
