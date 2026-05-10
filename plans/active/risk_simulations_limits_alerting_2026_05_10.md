---
title: Risk rule taxonomy + per-archetype/venue/account/client limits + alerting wire + pre-flight check API
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: 13-day pre-cutover sprint
companion_to: master_to_live_defi_2026_05_23.md (Group F item 20 circuit breakers + alerting + auto-recovery)
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/risk_simulations_limits_alerting_2026_05_08.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/disaster_recovery_circuit_breakers_2026_05_10.md
  - plans/active/alerting_service_live_rules_2026_05_07.md
  - plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md
  - plans/active/promote_workflow_backtest_to_live_2026_05_10.md
related_codex:
  - codex/04-architecture/kill-switch-circuit-breaker.md
  - codex/04-architecture/capital-efficiency-patterns.md
---

# Risk rule taxonomy + per-archetype/venue/account/client limits + pre-flight checks

> **🟡 IN-FLIGHT REFACTOR — § 7 SSOT RECONCILIATION REQUIRED BEFORE PHASE 1 (2026-05-10).** Phase 1 ships UAC contracts
> introducing a new `RiskRuleConsequence` (BLOCK / SCALE_DOWN / MONITOR / TEST_ONLY) enum without reconciling against
> 5 existing canonical workspace risk SSOTs (4-layer risk-gates / 3 circuit-breaker actions / 5 kill-switch trigger
> types / ErrorAction / 39-code AlertCode). See
> [`plans/active/issues/risk_rule_taxonomy_ssot_reconciliation_2026_05_10.md`](issues/risk_rule_taxonomy_ssot_reconciliation_2026_05_10.md)
> — operator must pick Framing 1 (legitimate layered extension; declare seam diagram) or Framing 2 (retire
> `RiskRuleConsequence` as contamination from question-doc first-pass reconstruction). Pre-Phase-1 reconciliation is
> doc-edit cost; post-Phase-1 reconciliation is multi-repo refactor cost. Do not start Phase 1 UAC contract design
> until this finding closes.

## Why this plan exists

May-23 cutover gates on Group F item 20 having every risk rule (limits, breakers, pre-flight checks) declared in a single
SSOT, scoped per archetype × per venue × per account × per asset_group × per client, with a closed-enum consequence
(BLOCK / SCALE_DOWN / MONITOR / TEST_ONLY). Today the rules live partially in risk-and-exposure-service code, partially
in alerting-service rules.py, partially in operator memory. This plan ships the unified UAC taxonomy, the per-axis limit
declarations for the 2 cutover archetypes, the pre-flight check API every order goes through before submission, and the
alerting wire on every rule fire. Multi-strategy-family limits + per-share-class limits + multi-quarter risk-model
calibration deferred post-cutover.

## Scope + non-goals

### In scope (must ship by 2026-05-23)

1. UAC risk rule taxonomy: `RiskRuleId`, `RiskRuleScope` (per-archetype / per-venue / per-account / per-asset_group /
   per-client / global), `RiskRuleTrigger` (typed conditions), `RiskRuleConsequence` (BLOCK / SCALE_DOWN / MONITOR / TEST_ONLY) closed enum.
2. Per-archetype limit declarations: position size, drawdown, leverage, concentration, correlation, slippage budget,
   funding-cost ceiling, gas budget, capital-at-risk ceiling.
3. Per-venue limit declarations: max OI, max single-instrument size, max cross-instrument size.
4. Per-account limit declarations: max gross exposure, max net exposure, max daily loss.
5. Per-client limit declarations (cutover demo client only): per-archetype subscription size + drawdown.
6. Per-asset_group + global limit declarations.
7. Pre-flight check API: every order request goes through `risk_preflight(order, context) -> RiskPreflightResult` BEFORE
   reaching execution-service. Returns pass / scale-down / block.
8. Alerting wire: every rule fire emits `RiskRuleFiredEvent` with severity routing.
9. Codex SSOTs: 2 NEW + 2 UPDATE.
10. Real-VM cutover-archetype simulation suite: every rule has at least one synthetic-scenario fire test.

### Non-goals (post-cutover)

- Multi-strategy-family limit aggregation across 50+ archetypes — post-cutover; cutover scopes 2 archetypes.
- Per-share-class limit decomposition (multi-fund accounting) — post-cutover.
- Multi-quarter risk-model calibration (Bayesian / GARCH / VaR sims) — post-cutover; cutover uses static thresholds.
- Per-counterparty credit risk modeling — post-cutover.

## Pre-audit / blast radius

| Repo                                  | Surface                                                                                                          |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts`               | NEW: `canonical/crosscutting/risk_rule.py`; `registry/risk_rules/{archetype,venue,account,client,asset_group,global}.py` |
| `unified-trading-library`             | NEW: `risk/preflight.py`, `risk/rule_evaluator.py`                                                               |
| `risk-and-exposure-service`           | UPDATE: every existing rule migrates to UAC registry; rule_evaluator wired                                       |
| `execution-service`                   | UPDATE: every order goes through `risk_preflight` before submission                                              |
| `strategy-service`                    | UPDATE: signal generator queries pre-flight before sizing                                                        |
| `alerting-service`                    | UPDATE: `RiskRuleFiredEvent` consumer + severity routing                                                         |
| `deployment-api` + `deployment-ui`    | NEW: `/api/risk/rules` + `/api/risk/preflight-test` + Risk tab                                                   |
| `unified-trading-pm`                  | NEW + UPDATE codex docs                                                                                          |

## Phased execution DAG

```text
0 (pre-audit, parallel) → 1 (UAC taxonomy) → 2 (per-axis limit registry, parallel) → 3 (UTL pre-flight + evaluator) →
4 (per-service migration, parallel) → 5 (alerting wire) → 6 (deployment-api+ui) → 7 (codex SSOTs) → 8 (real-VM rule fire suite)
→ 9 (cutover gate)
```

## Phase 0 — Pre-audit (Day 1, ~0.5 AI-day, 3 parallel sub-agents)

- [ ] [AGENT] P0. **0.A Existing rule audit.** Walk risk-and-exposure-service + execution-service + alerting-service for every rule; classify per scope.
- [ ] [AGENT] P0. **0.B Per-cutover-archetype rule requirements.** Operator + plan author co-author the per-archetype rule list (≥10 per archetype).
- [ ] [SCRIPT] P0. **0.C Banners on cross-plan files.**

**Full-execution criterion**: § Audit findings; banners on 4 plans.

## Phase 1 — UAC risk rule taxonomy (Days 2-3, ~1.5 AI-days)

- [ ] [AGENT] P0. **1.A `RiskRuleId` + `RiskRuleScope` + `RiskRuleConsequence` enums.** Closed sets.
- [ ] [AGENT] P0. **1.B `RiskRuleTrigger` typed conditions.** Closed-union: `MaxPositionSize`, `MaxDrawdown`, `MaxLeverage`, `MaxConcentration`, `MaxCorrelation`, `SlippageBudgetExceeded`, `FundingCostCeiling`, `GasBudgetExceeded`, `CapitalAtRiskCeiling`, `MaxOI`, `MaxGrossExposure`, `MaxDailyLoss`, plus extension closed-enum for unique-archetype rules.
- [ ] [AGENT] P0. **1.C `RiskRule` Pydantic dataclass.** `(rule_id, scope, applies_to, trigger, consequence, alerting_severity)`.
- [ ] [AGENT] P0. **1.D Tests.** ≥30 unit tests.

**Full-execution criterion**: UAC PR pushed; QG green.

## Phase 2 — Per-axis limit registry (Days 3-5, ~2 AI-days, 6 parallel sub-agents)

- [ ] [AGENT] P0. **2.A Per-archetype rules.** `registry/risk_rules/archetype.py` — ≥10 rules per cutover archetype.
- [ ] [AGENT] P0. **2.B Per-venue rules.** `registry/risk_rules/venue.py` — for cutover-archetype venues.
- [ ] [AGENT] P0. **2.C Per-account rules.** `registry/risk_rules/account.py` — paper + live accounts.
- [ ] [AGENT] P0. **2.D Per-client rules.** `registry/risk_rules/client.py` — cutover demo client.
- [ ] [AGENT] P0. **2.E Per-asset_group rules.** `registry/risk_rules/asset_group.py` — DeFi + CeFi cutover-relevant.
- [ ] [AGENT] P0. **2.F Global rules.** `registry/risk_rules/global.py` — workspace-wide kill conditions.

**Full-execution criterion**: registry has ≥30 total rules; per-archetype helper returns full rule set; tests pass.

## Phase 3 — UTL pre-flight + rule evaluator (Days 5-7, ~2 AI-days)

- [ ] [AGENT] P0. **3.A `risk/rule_evaluator.py`.** `evaluate_rule(rule, context) -> RuleEvalResult`. Per-trigger evaluator function.
- [ ] [AGENT] P0. **3.B `risk/preflight.py`.** `risk_preflight(order, context) -> RiskPreflightResult`. Iterates applicable rules per scope; returns aggregate (pass / scale-down with multiplier / block with reason). Reuses rule_evaluator.
- [ ] [AGENT] P0. **3.C Tests.** ≥40 unit tests; per-rule evaluator behaviour; pre-flight aggregation.

**Full-execution criterion**: UTL PR pushed; QG green; integration test runs pre-flight on stub orders.

## Phase 4 — Per-service migration (Days 7-9, ~2 AI-days, 4 parallel sub-agents)

- [ ] [AGENT] P0. **4.A risk-and-exposure-service.** Existing rules migrate to UAC registry; rule_evaluator wired; no code-side rule logic remains in service.
- [ ] [AGENT] P0. **4.B execution-service.** Order submission path inserts `risk_preflight` BEFORE venue submission. Block / scale-down behaviour wired.
- [ ] [AGENT] P0. **4.C strategy-service.** Signal generator queries pre-flight before sizing; if pre-flight returns scale-down, signal scaled.
- [ ] [AGENT] P0. **4.D position-balance.** Per-rule state-tracking (current draw-down, current leverage, current OI) emitted to rule_evaluator-readable format.

**Full-execution criterion**: per-repo QG green; integration test verifies block behaviour at execution-service.

## Phase 5 — Alerting wire (Day 10, ~0.5 AI-day)

- [ ] [AGENT] P0. **5.A `RiskRuleFiredEvent` emit on every rule fire.** Severity per UAC `alerting_severity` field.
- [ ] [AGENT] P0. **5.B Alerting-service consumer.** Routes to severity tier (CRITICAL → page, WARNING → dashboard, INFO → log).

**Full-execution criterion**: integration test fires a rule → alert routes per severity.

## Phase 6 — deployment-api + ui (Day 11, ~0.5 AI-day)

- [ ] [AGENT] P0. **6.A `/api/risk/rules` endpoint.** Per-axis listing.
- [ ] [AGENT] P0. **6.B `/api/risk/preflight-test` endpoint.** POST a hypothetical order; returns pre-flight result.
- [ ] [AGENT] P0. **6.C deployment-ui Risk tab.** Per-axis rule browser + pre-flight playground.

**Full-execution criterion**: UI renders rules + playground works against real API.

## Phase 7 — Codex SSOTs (Day 12, ~0.5 AI-day)

- [ ] [AGENT] P0. **7.A NEW `codex/04-architecture/risk-rule-taxonomy.md`.** Taxonomy, scope axis, consequence closed enum.
- [ ] [AGENT] P0. **7.B NEW `codex/04-architecture/risk-preflight-flow.md`.** Order-submission flow, scale-down semantics, block semantics.
- [ ] [AGENT] P0. **7.C UPDATE `kill-switch-circuit-breaker.md`** — risk-rule fire → breaker arm cross-link.
- [ ] [AGENT] P0. **7.D UPDATE `capital-efficiency-patterns.md`** — per-archetype capital-at-risk ceiling cross-link.

**Full-execution criterion**: 2 NEW + 2 UPDATE; cross-references resolve.

## Phase 8 — Real-VM rule fire suite (Days 12-13, ~1.5 AI-days)

- [ ] [SCRIPT] P0. **8.A Per-rule synthetic-fire test.** Uses `simulation_scenarios_topology_price_shocks_2026_05_09` injection primitives. Each rule has at least one scenario that fires it.
- [ ] [AGENT] P0. **8.B Per-archetype suite green.** All ≥10 rules per archetype fire on schedule + alert routes per severity + pre-flight blocks downstream order.
- [ ] [AGENT] P0. **8.C Evidence capture.**

**Full-execution criterion**: per-archetype suite log green; ≥10 fire-events per archetype with alert routing.

## Phase 9 — Cutover gate (Day 13, ~0.25 AI-day)

- [ ] [AGENT] P0. **9.A Master plan row.** Group F item 20 row gains "risk rule taxonomy + pre-flight + alerting wire green per archetype."
- [ ] [AGENT] P0. **9.B Banners removed.**

**Full-execution criterion**: master plan row green; banners gone.

## Cross-plan coordination

- `disaster_recovery_circuit_breakers_2026_05_10` — risk rule fire → breaker arm path; banner reciprocal.
- `simulation_scenarios_topology_price_shocks_2026_05_09` — Phase 8 consumes those primitives; banner reciprocal.
- `alerting_service_live_rules_2026_05_07` — `RiskRuleFiredEvent` is alerting consumer.
- `promote_workflow_backtest_to_live_2026_05_10` — gate evaluator reads pre-flight pass/fail.

## Deferred work after 2026-05-10 plan-creation session

| Item                                                | Status              | Successor / blocker                                                       |
| --------------------------------------------------- | ------------------- | ------------------------------------------------------------------------- |
| Multi-strategy-family limit aggregation             | DEFERRED-PER-USER   | Post-cutover                                                              |
| Per-share-class limit decomposition                 | DEFERRED-PER-USER   | Post-cutover                                                              |
| Multi-quarter risk-model calibration (VaR / GARCH)  | DEFERRED-PER-USER   | Post-cutover                                                              |
| Per-counterparty credit risk modeling               | DEFERRED-PER-USER   | Post-cutover                                                              |

## Done definition

1. ✅ Phases 0-9 every checkbox flipped with evidence.
2. ✅ UAC + UTL + 5 service repos + UI + PM green.
3. ✅ ≥30 risk rules in registry; per-archetype suite green; alerting wire green.
4. ✅ Master plan Group F item 20 row gains the taxonomy + pre-flight assertion.

## Audit findings

(Phase 0 sub-agents fill.)

## DONE block

(Filled at completion.)
