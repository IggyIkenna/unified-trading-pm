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
  - plans/active/promote_workflow_may23_cli_path_2026_05_10.md
related_codex:
  - codex/04-architecture/kill-switch-circuit-breaker.md
  - codex/04-architecture/capital-efficiency-patterns.md
---

# Risk rule taxonomy + per-archetype/venue/account/client limits + pre-flight checks

> **🟢 § 7 SSOT RECONCILIATION CLOSED — Framing 1 (legitimate layered extension) picked by operator 2026-05-10.**
> `RiskRuleConsequence` is a new pre-flight rule-decision abstraction at Layer 2 of the existing 4-layer risk-gates
> model — distinct from + composing with the 5 canonical workspace risk SSOTs. Seam diagram codified in
> § "§ 7 SSOT reconciliation seam (Framing 1)" below. Phase 1 unblocked; Phase 1.A MUST cite the seam in every
> Pydantic docstring + Phase 7 codex doc must include the seam diagram verbatim. Reviewers reject Phase 1 PR if seam
> citations missing. Issue
> [`risk_rule_taxonomy_ssot_reconciliation_2026_05_10.md`](../archive/issues/risk_rule_taxonomy_ssot_reconciliation_2026_05_10.md)
> closed.

## Why this plan exists

May-23 cutover gates on Group F item 20 having every risk rule (limits, breakers, pre-flight checks) declared in a single
SSOT, scoped per archetype × per venue × per account × per asset_group × per client, with a closed-enum consequence
(BLOCK / SCALE_DOWN / MONITOR / TEST_ONLY). Today the rules live partially in risk-and-exposure-service code, partially
in alerting-service rules.py, partially in operator memory. This plan ships the unified UAC taxonomy, the per-axis limit
declarations for the 2 cutover archetypes, the pre-flight check API every order goes through before submission, and the
alerting wire on every rule fire. **Multi-strategy-family limit aggregation pulled into May-23 scope per operator
direction 2026-05-10** (Phase 2 extends with `StrategyFamilyId` registry + family-aggregate rules). Per-share-class
limits + multi-quarter risk-model calibration remain post-cutover.

## § 7 SSOT reconciliation seam (Framing 1 — picked 2026-05-10)

`RiskRuleConsequence` is a NEW abstraction at a NEW layer — **per-rule per-instruction pre-flight decision** evaluated
at Layer 2 of the 4-layer risk-gates model. It does NOT replace any existing canonical SSOT; it COMPOSES with all 5.
This section is the canonical seam diagram every Phase 1+ UAC contract docstring + Phase 7 codex doc must cite.

### Cross-product table — `RiskRuleConsequence` × 5 canonical SSOTs

| Consequence    | Risk-gates Layer (per [`risk-gates.md`](../../codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md)) | Event(s) emitted (per the 8-event lifecycle SSOT) | Composes with kill-switch trigger (5-set per [`kill-switch-circuit-breaker.md`](../../codex/04-architecture/kill-switch-circuit-breaker.md)) | Composes with circuit-breaker action (3-set per [`alerting_service_live_rules`](alerting_service_live_rules_2026_05_07.md)) | Composes with strategy kill-switch behaviour (4-set) | AlertCode mapping (UAC@d00326d) |
| -------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------- |
| `BLOCK`        | Layer 2 (risk-and-exposure-service)                                                                         | `INSTRUCTION_REJECTED_RISK` + `RiskRuleFiredEvent` (sev: HIGH or CRITICAL) | If rule has `triggers_kill_switch: true` AND fires per-rule threshold count → engages `DAILY_LOSS_BREACH` / `MAX_DRAWDOWN_BREACH` / `DATA_STALE` per `RiskRuleTrigger` type | Aggregated BLOCK rate ≥ 60% across N instructions → execution-service circuit-breaker may transition CLOSED→DEGRADED→OPEN per per-venue failure-rate threshold; on transition emits `stop_new_signals` (DEGRADED) / `force_exit_only` (OPEN) / `halt_strategy` (cascade per autonomous-recovery-matrix) | If kill-switch engaged: `STOP_NEW_ONLY` (default) / `FAST_UNWIND` (if MAX_DRAWDOWN_BREACH) / `SLOW_UNWIND` (operator override) / `DELTA_HEDGE` (if cross-venue still open) | Reuse existing `PREFLIGHT_FAILED` for generic case; new `RISK_RULE_BLOCKED` (proposed addition to closed set in Phase 1.E) if granular per-rule alerts needed |
| `SCALE_DOWN`   | Layer 2 (rule decision) → Layer 3 (execution-service applies size adjustment)                              | `INSTRUCTION_ACCEPTED_PREFLIGHT` (with `size_adjusted: true` annotation) → `RESIZED_EXECUTION` at Layer 3 + `RiskRuleFiredEvent` (sev: WARN) | Does NOT trigger kill-switch (size-adjusted instruction proceeds; no breach state)                                                          | Does NOT trigger circuit-breaker (instruction is approved, just smaller)                                                    | Strategy continues normally with reduced size        | New `RISK_RULE_SCALED_DOWN` (Phase 1.E proposed addition to UAC@d00326d closed set) |
| `MONITOR`      | Layer 2 (passthrough; advisory)                                                                            | `INSTRUCTION_ACCEPTED_PREFLIGHT` (no modification) + `RiskRuleFiredEvent` (sev: INFO or WARN) | Does NOT trigger kill-switch                                                                                                                | Does NOT trigger circuit-breaker                                                                                            | Strategy continues normally                          | New `RISK_RULE_MONITOR_FIRED` (Phase 1.E proposed addition) |
| `TEST_ONLY`    | Layer 2 (route-divert; tags instruction with `mode=TEST`) → Layer 3 routes to matching engine              | `INSTRUCTION_ACCEPTED_PREFLIGHT` (with `mode=TEST` annotation) → `ORDER_SUBMITTED` to matching engine instead of live venue + `RiskRuleFiredEvent` (sev: INFO) | Does NOT trigger kill-switch                                                                                                                | Does NOT trigger circuit-breaker (no live venue contact)                                                                    | Strategy continues; fills are simulated, not real    | New `RISK_RULE_TEST_ONLY_ROUTED` (Phase 1.E proposed addition) |

### Orthogonality declarations

- **vs ErrorAction taxonomy** (`RETRY` / `RECONNECT` / `SKIP` / `FAIL` per
  [`autonomous-recovery-matrix.md`](../../codex/04-architecture/autonomous-recovery-matrix.md)): `RiskRuleConsequence`
  is a **pre-flight rule decision at Layer 2** (before instruction reaches venue); ErrorAction is a **post-venue-error
  classification at Layer 4** (after venue rejects an attempt). They don't overlap; both can apply to the same
  instruction lifecycle:
  - Layer 2 may BLOCK → instruction never reaches venue → no ErrorAction ever fires.
  - Layer 2 may approve (any non-BLOCK) → Layer 4 venue may reject → ErrorAction classifies the venue rejection (and
    may transition the venue circuit-breaker per the failure-rate threshold).
- **vs AlertCode + AlertSeverity + AlertChannel SSOT** (UAC@d00326d, 39 closed codes per
  [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md)): every
  `RiskRuleFiredEvent` MUST cite an `AlertCode` from the closed set + an `AlertSeverity` + the `AlertRule` declares
  `AlertChannel` routing + `triggers_kill_switch: bool`. **Phase 1.E adds 4 new AlertCodes** (`RISK_RULE_BLOCKED`,
  `RISK_RULE_SCALED_DOWN`, `RISK_RULE_MONITOR_FIRED`, `RISK_RULE_TEST_ONLY_ROUTED`) to the closed set, growing it
  from 39 → 43. Reviewers MUST verify these additions extend the closed set + don't shadow existing codes (e.g.
  `PREFLIGHT_FAILED` continues to fire for generic pre-flight check failures NOT routed through the rule engine).
- **vs `RiskRuleScope` × `KillSwitchScope`**: `RiskRuleScope` (per-archetype / per-venue / per-account / per-client /
  per-asset_group / global) is the rule-applicability axis; `KillSwitchScope` (entity_type / strategy_type / venue /
  instrument_id) is the kill-switch-blast-radius axis. A rule fired at scope=per-venue with `triggers_kill_switch:
  true` engages a kill-switch with `KillSwitchScope=venue=<that_venue>`. Phase 1.D `RiskRule` Pydantic dataclass MUST
  declare the mapping function `RiskRule.kill_switch_scope() -> KillSwitchScope`.

### Phase 1.A discipline

Every Phase 1.A Pydantic class docstring MUST include a "§ 7 SSOT reconciliation" subsection that links to this seam
diagram + names the canonical SSOTs the type composes with. Phase 7 codex doc `kill-switch-circuit-breaker.md`
EXTENSION includes this seam diagram verbatim.

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

<!-- Multi-strategy-family limit aggregation pulled into May-23 scope per operator direction 2026-05-10. See Phase 2.G-I + § In-scope item updates. -->
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

- [ ] [AGENT] P0. **1.A `RiskRuleId` + `RiskRuleScope` + `RiskRuleConsequence` enums.** Closed sets. **EVERY enum docstring MUST include a "§ 7 SSOT reconciliation" subsection citing the seam diagram in this plan body + the 5 canonical SSOTs by codex path.** Reviewers reject 1.A PR without seam citation.
- [ ] [AGENT] P0. **1.B `RiskRuleTrigger` typed conditions.** Closed-union: `MaxPositionSize`, `MaxDrawdown`, `MaxLeverage`, `MaxConcentration`, `MaxCorrelation`, `SlippageBudgetExceeded`, `FundingCostCeiling`, `GasBudgetExceeded`, `CapitalAtRiskCeiling`, `MaxOI`, `MaxGrossExposure`, `MaxDailyLoss`, plus extension closed-enum for unique-archetype rules.
- [ ] [AGENT] P0. **1.C `RiskRule` Pydantic dataclass.** `(rule_id, scope, applies_to, trigger, consequence, alerting_severity)` + method `kill_switch_scope() -> KillSwitchScope` per the seam diagram orthogonality declaration. Docstring cites the seam diagram.
- [ ] [AGENT] P0. **1.D Tests.** ≥30 unit tests, including 4 seam-diagram-conformance tests (one per `RiskRuleConsequence` value verifying the event(s) emitted match the cross-product table).
- [ ] [AGENT] P0. **1.E AlertCode closed-set extension — RATIFIED 2026-05-10 cross-plan audit Q6 (Policy B larger-set-wins).** Add `RISK_RULE_BLOCKED`, `RISK_RULE_SCALED_DOWN`, `RISK_RULE_MONITOR_FIRED`, `RISK_RULE_TEST_ONLY_ROUTED` to UAC@d00326d `AlertCode` enum. **Plus 2 NEW kill-switch recovery codes per Q8 ratification**: `KILL_SWITCH_AUTO_RECOVERED` + `KILL_SWITCH_MANUAL_UNKILLED` (distinct alert events per Policy B — kill-switch supports BOTH manual-unkill AND auto-cooldown recovery modes per per-action defaults; see Phase 1.F below). Total growth: 39 → 45 closed-set. Coordinate ownership with [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md) (its closed-set is the seed; this plan extends). Tests assert no shadowing of existing codes; `grep -rn "RISK_RULE_\|KILL_SWITCH_AUTO_RECOVERED\|KILL_SWITCH_MANUAL_UNKILLED" unified-api-contracts/` returns zero pre-existing references.
- [ ] [AGENT] P0. **1.F `BreakerRecoveryMode` enum + `BREAKER_RECOVERY_DEFAULTS` SSOT — RATIFIED 2026-05-10 cross-plan audit Q8.** Add `BreakerRecoveryMode` closed set `{manual_unkill, auto_cooldown}` to UAC. Add `BREAKER_RECOVERY_DEFAULTS: dict[BreakerAction, BreakerRecoveryMode]` mapping per-action defaults: `BLOCK_NEW → auto_cooldown` (least-restrictive; auto-resume safe when metric clears), `CANCEL_OPEN → manual_unkill` (cancelled orders are gone; auto-recovery doesn't restore), `SCALE_DOWN → auto_cooldown` (partial unwind has natural inverse), `KILL_ALL → manual_unkill` (full unwind needs operator sign-off). Plus `cooldown_seconds: int | None` on `BreakerConfig` (None when manual). Tests assert defaults dict matches per-action semantics. Coordinate with [`disaster_recovery_circuit_breakers_2026_05_10.md`](disaster_recovery_circuit_breakers_2026_05_10.md) Phase 1.A which owns `BreakerConfig` extension.

**Full-execution criterion**: UAC PR pushed; QG green; AlertCode closed-set grows from 39 → 45 with no shadowing; `BreakerRecoveryMode` + `BREAKER_RECOVERY_DEFAULTS` shipped; every Pydantic docstring cites the seam diagram + 5 canonical SSOTs.

## Phase 2 — Per-axis limit registry (Days 3-5, ~2 AI-days, 6 parallel sub-agents)

- [ ] [AGENT] P0. **2.A Per-archetype rules.** `registry/risk_rules/archetype.py` — ≥10 rules per cutover archetype.
- [ ] [AGENT] P0. **2.B Per-venue rules.** `registry/risk_rules/venue.py` — for cutover-archetype venues.
- [ ] [AGENT] P0. **2.C Per-account rules.** `registry/risk_rules/account.py` — paper + live accounts.
- [ ] [AGENT] P0. **2.D Per-client rules.** `registry/risk_rules/client.py` — cutover demo client.
- [ ] [AGENT] P0. **2.E Per-asset_group rules.** `registry/risk_rules/asset_group.py` — DeFi + CeFi cutover-relevant.
- [ ] [AGENT] P0. **2.F Global rules.** `registry/risk_rules/global.py` — workspace-wide kill conditions.
- [ ] [AGENT] P0. **2.G `StrategyFamilyId` closed enum + family registry.** `unified_api_contracts/canonical/crosscutting/strategy_family.py`: `StrategyFamilyId` (closed enum: `FUNDING_ARB_FAMILY` / `BASIS_CARRY_FAMILY` / `LST_LEVERAGE_FAMILY` / `OPTIONS_VOL_FAMILY` / `SPORTS_MM_FAMILY` / `PREDICTION_MM_FAMILY` / `STAT_ARB_FAMILY` / extension-closed-enum for cutover-relevant additions). Per-family `members: frozenset[ArchetypeId]` (cutover archetypes both fall into specific families: `carry_staked_basis` → `LST_LEVERAGE_FAMILY`; `ARBITRAGE_PRICE_DISPERSION` → `FUNDING_ARB_FAMILY`).
- [ ] [AGENT] P0. **2.H Family-aggregate rules.** `registry/risk_rules/strategy_family.py` — per-family rules: `FAMILY_GROSS_EXPOSURE_CAP`, `FAMILY_NET_EXPOSURE_CAP`, `FAMILY_DRAWDOWN_CAP`, `FAMILY_CAPITAL_AT_RISK_CEILING`, `FAMILY_CONCENTRATION_PER_VENUE`, `FAMILY_CORRELATION_WITH_OTHER_FAMILY` (cross-family correlation surveillance: e.g. all LST-family + funding-arb-family share oracle-risk exposure on Pyth Solana). Each family declares ≥6 rules.
- [ ] [AGENT] P0. **2.I Family-aggregate evaluator.** UTL `risk/family_aggregator.py`: rolls up per-archetype state into per-family state (sum-of-positions per family + max-drawdown across family + cross-family correlation matrix from rolling returns). Feeds rule_evaluator at family scope. Recomputes per fill event + per-minute cron.

**Full-execution criterion**: registry has ≥30 archetype-scope + ≥12 family-scope rules; family-aggregator computes per-family state on stub events with correctness invariant `sum(archetype_state) == family_state`; per-family helper returns full rule set; tests pass.

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
- [ ] [AGENT] P0. **7.E NEW `codex/04-architecture/risk-breaker-seam.md` — RATIFIED 2026-05-10 cross-plan audit Q9.**
      Document the distinct-enums-with-escalation-seam architecture: `RiskRuleConsequence` (per-rule-firing taxonomy)
      and `BreakerAction` (per-venue state-machine taxonomy) are SEPARATE enums by design — different triggers, different
      layers. The seam: when N consecutive `RiskRuleConsequence.SCALE_DOWN` consequences fire on same
      `(venue, asset_group)` within window W, risk-controller emits `BREAKER_ESCALATION_REQUESTED` event consumed by
      execution-service breaker (which then transitions per its state machine into DEGRADED or OPEN). UAC SSOT
      `RISK_TO_BREAKER_ESCALATION_MAP: dict[(RiskRuleConsequence, int, timedelta), BreakerAction]` declares the
      escalation thresholds. Doc explains layering (Layer 2 risk → Layer 4 breaker), why naming collision is intentional
      (both use SCALE_DOWN vocabulary because the operator-facing concept is the same), and operational implications
      (risk-controller can fire WITHOUT breaker firing; breaker can fire WITHOUT risk-controller — they're independent
      layers that ESCALATE through the seam, not duplicate). Cross-links the seam diagram + cross-product table from
      this plan body.
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
- `promote_workflow_may23_cli_path_2026_05_10` — gate evaluator reads pre-flight pass/fail.

## Deferred work after 2026-05-10 plan-creation session

| Item                                                | Status              | Successor / blocker                                                       |
| --------------------------------------------------- | ------------------- | ------------------------------------------------------------------------- |
| ~~Multi-strategy-family limit aggregation~~         | **PULLED FORWARD 2026-05-10** | Now in scope per operator direction; see Phase 2.G-I (UAC `StrategyFamilyId` + family registry + UTL aggregator) |
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
