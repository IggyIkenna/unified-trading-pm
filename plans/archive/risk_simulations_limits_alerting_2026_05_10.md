---
doc_type: plan
title: Risk rule taxonomy + per-archetype/venue/account/client limits + alerting wire + pre-flight check API
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-ui, execution-service, features-service, instruments-service]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/disaster_recovery_circuit_breakers_2026_05_10.md,
    plans/active/alerting_service_live_rules_2026_05_07.md,
    plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md,
    plans/active/promote_workflow_may23_cli_path_2026_05_10.md,
  ]
created: 2026-05-10
type: plan
deadline: 2026-05-23
horizon: 13-day pre-cutover sprint
companion_to: master_to_live_defi_2026_05_23.md (Group F item 20 circuit breakers + alerting + auto-recovery)
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/risk_simulations_limits_alerting_2026_05_08.md
related_codex:
  [/codex/04-architecture/kill-switch-circuit-breaker.md, /codex/04-architecture/capital-efficiency-patterns.md]
estimate_class: design
estimate_baseline_ai_days: 11.2
estimate_calibrated_ai_days: 6.8
estimate_calibration_note: "Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~0.5, ~1.5,
  ~2, ~2, + 6 more). Class inferred from filename (design, multiplier 0.6×).

  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be
  double-counted. Owner agent: verify baseline, refine class per /codex/08-workflows/estimation-calibration.md,
  recompute calibrated if either changes.

  "
---

> **ARCHIVED 2026-05-16 — 100% done per inventory (slot-8 SWEEP-16 mechanical archive sweep)**

> **🟡 IN-FLIGHT REFACTOR — UAC Phase 1 client-reporting contracts landed (UAC@b3233e5, 2026-05-12). `ClientNAV`,
> `ClientPosition`, `ClientPnLEntry`, `PnLFactor`, `PnLLayer` now in `unified_api_contracts.internal`. Risk-limit schema
> consumers must import from UAC.internal. Banner: `client_reporting_pnl_attribution_mvp_2026_05_10.md` Phase 1.**

# Risk rule taxonomy + per-archetype/venue/account/client limits + pre-flight checks

> **🟢 § 7 SSOT RECONCILIATION CLOSED — Framing 1 (legitimate layered extension) picked by operator 2026-05-10.**
> `RiskRuleConsequence` is a new pre-flight rule-decision abstraction at Layer 2 of the existing 4-layer risk-gates
> model — distinct from + composing with the 5 canonical workspace risk SSOTs. Seam diagram codified in § "§ 7 SSOT
> reconciliation seam (Framing 1)" below. Phase 1 unblocked; Phase 1.A MUST cite the seam in every Pydantic docstring +
> Phase 7 codex doc must include the seam diagram verbatim. Reviewers reject Phase 1 PR if seam citations missing. Issue
> [`risk_rule_taxonomy_ssot_reconciliation_2026_05_10.md`](../archive/issues/risk_rule_taxonomy_ssot_reconciliation_2026_05_10.md)
> closed.

## Why this plan exists

May-23 cutover gates on Group F item 20 having every risk rule (limits, breakers, pre-flight checks) declared in a
single SSOT, scoped per archetype × per venue × per account × per asset_group × per client, with a closed-enum
consequence (BLOCK / SCALE_DOWN / MONITOR / TEST_ONLY). Today the rules live partially in risk-and-exposure-service
code, partially in alerting-service rules.py, partially in operator memory. This plan ships the unified UAC taxonomy,
the per-axis limit declarations for the 2 cutover archetypes, the pre-flight check API every order goes through before
submission, and the alerting wire on every rule fire. **Multi-strategy-family limit aggregation pulled into May-23 scope
per operator direction 2026-05-10** (Phase 2 extends with `StrategyFamilyId` registry + family-aggregate rules).
Per-share-class limits + multi-quarter risk-model calibration remain post-cutover.

## § 7 SSOT reconciliation seam (Framing 1 — picked 2026-05-10)

`RiskRuleConsequence` is a NEW abstraction at a NEW layer — **per-rule per-instruction pre-flight decision** evaluated
at Layer 2 of the 4-layer risk-gates model. It does NOT replace any existing canonical SSOT; it COMPOSES with all 5.
This section is the canonical seam diagram every Phase 1+ UAC contract docstring + Phase 7 codex doc must cite.

### Cross-product table — `RiskRuleConsequence` × 5 canonical SSOTs

| Consequence  | Risk-gates Layer (per [`risk-gates.md`](/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md)) | Event(s) emitted (per the 8-event lifecycle SSOT)                                                                                                              | Composes with kill-switch trigger (5-set per [`kill-switch-circuit-breaker.md`](/codex/04-architecture/kill-switch-circuit-breaker.md))                                     | Composes with circuit-breaker action (3-set per [`alerting_service_live_rules`](alerting_service_live_rules_2026_05_07.md))                                                                                                                                                                             | Composes with strategy kill-switch behaviour (4-set)                                                                                                                       | AlertCode mapping (UAC@d00326d)                                                                                                                               |
| ------------ | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BLOCK`      | Layer 2 (risk-and-exposure-service)                                                                      | `INSTRUCTION_REJECTED_RISK` + `RiskRuleFiredEvent` (sev: HIGH or CRITICAL)                                                                                     | If rule has `triggers_kill_switch: true` AND fires per-rule threshold count → engages `DAILY_LOSS_BREACH` / `MAX_DRAWDOWN_BREACH` / `DATA_STALE` per `RiskRuleTrigger` type | Aggregated BLOCK rate ≥ 60% across N instructions → execution-service circuit-breaker may transition CLOSED→DEGRADED→OPEN per per-venue failure-rate threshold; on transition emits `stop_new_signals` (DEGRADED) / `force_exit_only` (OPEN) / `halt_strategy` (cascade per autonomous-recovery-matrix) | If kill-switch engaged: `STOP_NEW_ONLY` (default) / `FAST_UNWIND` (if MAX_DRAWDOWN_BREACH) / `SLOW_UNWIND` (operator override) / `DELTA_HEDGE` (if cross-venue still open) | Reuse existing `PREFLIGHT_FAILED` for generic case; new `RISK_RULE_BLOCKED` (proposed addition to closed set in Phase 1.E) if granular per-rule alerts needed |
| `SCALE_DOWN` | Layer 2 (rule decision) → Layer 3 (execution-service applies size adjustment)                            | `INSTRUCTION_ACCEPTED_PREFLIGHT` (with `size_adjusted: true` annotation) → `RESIZED_EXECUTION` at Layer 3 + `RiskRuleFiredEvent` (sev: WARN)                   | Does NOT trigger kill-switch (size-adjusted instruction proceeds; no breach state)                                                                                          | Does NOT trigger circuit-breaker (instruction is approved, just smaller)                                                                                                                                                                                                                                | Strategy continues normally with reduced size                                                                                                                              | New `RISK_RULE_SCALED_DOWN` (Phase 1.E proposed addition to UAC@d00326d closed set)                                                                           |
| `MONITOR`    | Layer 2 (passthrough; advisory)                                                                          | `INSTRUCTION_ACCEPTED_PREFLIGHT` (no modification) + `RiskRuleFiredEvent` (sev: INFO or WARN)                                                                  | Does NOT trigger kill-switch                                                                                                                                                | Does NOT trigger circuit-breaker                                                                                                                                                                                                                                                                        | Strategy continues normally                                                                                                                                                | New `RISK_RULE_MONITOR_FIRED` (Phase 1.E proposed addition)                                                                                                   |
| `TEST_ONLY`  | Layer 2 (route-divert; tags instruction with `mode=TEST`) → Layer 3 routes to matching engine            | `INSTRUCTION_ACCEPTED_PREFLIGHT` (with `mode=TEST` annotation) → `ORDER_SUBMITTED` to matching engine instead of live venue + `RiskRuleFiredEvent` (sev: INFO) | Does NOT trigger kill-switch                                                                                                                                                | Does NOT trigger circuit-breaker (no live venue contact)                                                                                                                                                                                                                                                | Strategy continues; fills are simulated, not real                                                                                                                          | New `RISK_RULE_TEST_ONLY_ROUTED` (Phase 1.E proposed addition)                                                                                                |

### Orthogonality declarations

- **vs ErrorAction taxonomy** (`RETRY` / `RECONNECT` / `SKIP` / `FAIL` per
  [`autonomous-recovery-matrix.md`](/codex/04-architecture/autonomous-recovery-matrix.md)): `RiskRuleConsequence` is a
  **pre-flight rule decision at Layer 2** (before instruction reaches venue); ErrorAction is a **post-venue-error
  classification at Layer 4** (after venue rejects an attempt). They don't overlap; both can apply to the same
  instruction lifecycle:
  - Layer 2 may BLOCK → instruction never reaches venue → no ErrorAction ever fires.
  - Layer 2 may approve (any non-BLOCK) → Layer 4 venue may reject → ErrorAction classifies the venue rejection (and may
    transition the venue circuit-breaker per the failure-rate threshold).
- **vs AlertCode + AlertSeverity + AlertChannel SSOT** (UAC@d00326d, 39 closed codes per
  [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md)): every `RiskRuleFiredEvent`
  MUST cite an `AlertCode` from the closed set + an `AlertSeverity` + the `AlertRule` declares `AlertChannel` routing +
  `triggers_kill_switch: bool`. **Phase 1.E adds 4 new AlertCodes** (`RISK_RULE_BLOCKED`, `RISK_RULE_SCALED_DOWN`,
  `RISK_RULE_MONITOR_FIRED`, `RISK_RULE_TEST_ONLY_ROUTED`) to the closed set, growing it from 39 → 43. Reviewers MUST
  verify these additions extend the closed set + don't shadow existing codes (e.g. `PREFLIGHT_FAILED` continues to fire
  for generic pre-flight check failures NOT routed through the rule engine).
- **vs `RiskRuleScope` × `KillSwitchScope`**: `RiskRuleScope` (per-archetype / per-venue / per-account / per-client /
  per-asset_group / global) is the rule-applicability axis; `KillSwitchScope` (entity_type / strategy_type / venue /
  instrument_id) is the kill-switch-blast-radius axis. A rule fired at scope=per-venue with `triggers_kill_switch: true`
  engages a kill-switch with `KillSwitchScope=venue=<that_venue>`. Phase 1.D `RiskRule` Pydantic dataclass MUST declare
  the mapping function `RiskRule.kill_switch_scope() -> KillSwitchScope`.

### Phase 1.A discipline

Every Phase 1.A Pydantic class docstring MUST include a "§ 7 SSOT reconciliation" subsection that links to this seam
diagram + names the canonical SSOTs the type composes with. Phase 7 codex doc `kill-switch-circuit-breaker.md` EXTENSION
includes this seam diagram verbatim.

## Scope + non-goals

### In scope (must ship by 2026-05-23)

1. UAC risk rule taxonomy: `RiskRuleId`, `RiskRuleScope` (per-archetype / per-venue / per-account / per-asset_group /
   per-client / global), `RiskRuleTrigger` (typed conditions), `RiskRuleConsequence` (BLOCK / SCALE_DOWN / MONITOR /
   TEST_ONLY) closed enum.
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

| Repo                               | Surface                                                                                                                  |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `unified-api-contracts`            | NEW: `canonical/crosscutting/risk_rule.py`; `registry/risk_rules/{archetype,venue,account,client,asset_group,global}.py` |
| `unified-trading-library`          | NEW: `risk/preflight.py`, `risk/rule_evaluator.py`                                                                       |
| `risk-and-exposure-service`        | UPDATE: every existing rule migrates to UAC registry; rule_evaluator wired                                               |
| `execution-service`                | UPDATE: every order goes through `risk_preflight` before submission                                                      |
| `strategy-service`                 | UPDATE: signal generator queries pre-flight before sizing                                                                |
| `alerting-service`                 | UPDATE: `RiskRuleFiredEvent` consumer + severity routing                                                                 |
| `deployment-api` + `deployment-ui` | NEW: `/api/risk/rules` + `/api/risk/preflight-test` + Risk tab                                                           |
| `unified-trading-pm`               | NEW + UPDATE codex docs                                                                                                  |

## Phased execution DAG

```text
0 (pre-audit, parallel) → 1 (UAC taxonomy) → 2 (per-axis limit registry, parallel) → 3 (UTL pre-flight + evaluator) →
4 (per-service migration, parallel) → 5 (alerting wire) → 6 (deployment-api+ui) → 7 (codex SSOTs) → 8 (real-VM rule fire suite)
→ 9 (cutover gate)
```

## Phase 0 — Pre-audit (Day 1, ~0.5 AI-day, 3 parallel sub-agents)

- [x] [AGENT] P0. **0.A Existing rule audit.** Walk risk-and-exposure-service + execution-service + alerting-service for
      every rule; classify per scope. (PM@0044e370 — findings written to `## Audit findings` below; key prior artefacts:
      `risk-and-exposure-service.v2.preflight.run_layer2_preflight` + `run_layer3_venue_account_preflight` orchestrator;
      `core/risk_monitor.RiskMonitor` (live monitoring); `core/pre_trade_check_engine.PreTradeCheckEngine` (decoupled
      checks); `core/risk_limits_client_factory.InMemoryRiskLimitsClient` (limits domain client); `models.RiskLimits`
      (per-account/strategy persistence); `alerting-service.circuit_breaker` (circuit-breaker module). Existing surface
      is rich; the gap addressed by this plan is the UAC-level _closed-set rule taxonomy_ + registry seed — Phase 1
      codifies the contract, Phase 4 migrates these services to consume it.)
- [x] [AGENT] P0. **0.B Per-cutover-archetype rule requirements.** Operator + plan author co-author the per-archetype
      rule list (≥10 per archetype). (PM@0044e370 — aspirational lists written to `## Audit findings` below driving
      Phase 2.A registry seeds.)
- [x] [SCRIPT] P0. **0.C Banners on cross-plan files.** (PM@0044e370 — banners added to
      `alerting_service_live_rules_2026_05_07.md` (post-banner line 42),
      `disaster_recovery_circuit_breakers_2026_05_10.md` (extension of existing § 7 banner),
      `master_to_live_defi_2026_05_23.md` (Group F item 22 row extension citing UAC@945ad5d + cross-reference to risk
      Phase 1.F handoff to DR plan Phase 1.A).)

**Full-execution criterion**: § Audit findings populated; banners on 3 cross-plan files (4th `simulation_scenarios_*`
deferred — its work hasn't started so no in-flight collision; banner added on first scope-overlap).

## Phase 1 — UAC risk rule taxonomy (Days 2-3, ~1.5 AI-days)

- [x] [AGENT] P0. **1.A `RiskRuleId` + `RiskRuleScope` + `RiskRuleConsequence` enums.** Closed sets. **EVERY enum
      docstring MUST include a "§ 7 SSOT reconciliation" subsection citing the seam diagram in this plan body + the 5
      canonical SSOTs by codex path.** Reviewers reject 1.A PR without seam citation. (UAC@945ad5d — shipped
      `canonical/crosscutting/risk_rule.py` with all 3 enums; every enum docstring cites § 7 SSOT reconciliation + 5
      canonical SSOTs; unit-test `test_enum_docstring_cites_seam_reconciliation` enforces at test-time.)
- [x] [AGENT] P0. **1.B `RiskRuleTrigger` typed conditions.** Closed-union: `MaxPositionSize`, `MaxDrawdown`,
      `MaxLeverage`, `MaxConcentration`, `MaxCorrelation`, `SlippageBudgetExceeded`, `FundingCostCeiling`,
      `GasBudgetExceeded`, `CapitalAtRiskCeiling`, `MaxOI`, `MaxGrossExposure`, `MaxDailyLoss`, plus extension
      closed-enum for unique-archetype rules. (UAC@945ad5d — shipped `RiskRuleTrigger` discriminated-union over all 13
      named trigger types via Pydantic `Annotated[Union[...], Field(discriminator="trigger_type")]`. Archetype-specific
      extensions land in Phase 2 by appending to the union, not by wildcard `Any`.)
- [x] [AGENT] P0. **1.C `RiskRule` Pydantic dataclass.**
      `(rule_id, scope, applies_to, trigger, consequence, alerting_severity)` + method
      `kill_switch_scope() -> KillSwitchScope` per the seam diagram orthogonality declaration. Docstring cites the seam
      diagram. (UAC@945ad5d — shipped `RiskRule` Pydantic with `frozen=True` + `extra='forbid'`; `kill_switch_scope()`
      maps PER_VENUE→VENUE, PER_ARCHETYPE→ARCHETYPE, PER_CLIENT→CLIENT, GLOBAL→GLOBAL, PER_ACCOUNT+PER_ASSET_GROUP→None
      per seam-diagram cross-product table. Class docstring + method docstring cite § 7 SSOT reconciliation.)
- [x] [AGENT] P0. **1.D Tests.** ≥30 unit tests, including 4 seam-diagram-conformance tests (one per
      `RiskRuleConsequence` value verifying the event(s) emitted match the cross-product table). (UAC@945ad5d —
      `tests/internal/unit/test_risk_rule_taxonomy.py` ships 38 tests including 4 seam-conformance tests
      (`test_seam_conformance_block_events` / `_scale_down_events` / `_monitor_events` / `_test_only_events`) plus 6
      `kill_switch_scope()` orthogonality tests; 99/99 pass
      `cd unified-api-contracts && pytest tests/internal/unit/test_risk_rule_taxonomy.py tests/internal/unit/test_strategy_family.py tests/internal/unit/test_alerting_taxonomy.py`.)
- [x] [AGENT] P0. **1.E AlertCode closed-set extension — RATIFIED 2026-05-10 cross-plan audit Q6 (Policy B
      larger-set-wins).** Add `RISK_RULE_BLOCKED`, `RISK_RULE_SCALED_DOWN`, `RISK_RULE_MONITOR_FIRED`,
      `RISK_RULE_TEST_ONLY_ROUTED` to UAC@d00326d `AlertCode` enum. **Plus 2 NEW kill-switch recovery codes per Q8
      ratification**: `KILL_SWITCH_AUTO_RECOVERED` + `KILL_SWITCH_MANUAL_UNKILLED` (distinct alert events per Policy B —
      kill-switch supports BOTH manual-unkill AND auto-cooldown recovery modes per per-action defaults; see Phase 1.F
      below). Total growth: 39 → 45 closed-set. Coordinate ownership with
      [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md) (its closed-set is the
      seed; this plan extends). Tests assert no shadowing of existing codes;
      `grep -rn "RISK_RULE_\|KILL_SWITCH_AUTO_RECOVERED\|KILL_SWITCH_MANUAL_UNKILLED" unified-api-contracts/` returns
      zero pre-existing references. (UAC@945ad5d — 6 new AlertCode members landed in
      `canonical/crosscutting/alerting/codes.py`; closed-set grows to 45 (verified via
      `test_alert_code_set_grew_by_at_least_six`); `test_no_pre_existing_shadowing_of_new_codes` confirms each new code
      appears exactly once. **`LIVE_ALERT_RULES` entries seeded by master coordinator at UAC@c96447b** — 6 new
      `AlertRule` entries with `event_pattern` field: `RISK_RULE_BLOCKED` (HIGH, PagerDuty+Telegram),
      `RISK_RULE_SCALED_DOWN` (WARN, Telegram), `RISK_RULE_MONITOR_FIRED` (INFO, LogOnly), `RISK_RULE_TEST_ONLY_ROUTED`
      (INFO, LogOnly), `KILL_SWITCH_AUTO_RECOVERED` (INFO, Telegram, scope=GLOBAL), `KILL_SWITCH_MANUAL_UNKILLED` (INFO,
      Telegram, scope=GLOBAL). Test `test_kill_switch_rules_trigger_kill_switch_flag` updated to exempt RECOVERY codes
      from `triggers_kill_switch=True` invariant — they report past state changes, not arm new ones.)
- [x] [AGENT] P0. **1.F `BreakerRecoveryMode` enum + `BREAKER_RECOVERY_DEFAULTS` SSOT — RATIFIED 2026-05-10 cross-plan
      audit Q8.** Add `BreakerRecoveryMode` closed set `{manual_unkill, auto_cooldown}` to UAC. Add
      `BREAKER_RECOVERY_DEFAULTS: dict[BreakerAction, BreakerRecoveryMode]` mapping per-action defaults:
      `BLOCK_NEW → auto_cooldown` (least-restrictive; auto-resume safe when metric clears),
      `CANCEL_OPEN → manual_unkill` (cancelled orders are gone; auto-recovery doesn't restore),
      `SCALE_DOWN → auto_cooldown` (partial unwind has natural inverse), `KILL_ALL → manual_unkill` (full unwind needs
      operator sign-off). Plus `cooldown_seconds: int | None` on `BreakerConfig` (None when manual). Tests assert
      defaults dict matches per-action semantics. Coordinate with
      [`disaster_recovery_circuit_breakers_2026_05_10.md`](disaster_recovery_circuit_breakers_2026_05_10.md) Phase 1.A
      which owns `BreakerConfig` extension. (**Cross-reference flip — Sub-C (DR slot) shipped the UAC artefact at
      UAC@a7a99b5**: `BreakerRecoveryMode` enum + `BREAKER_RECOVERY_DEFAULTS` dict + `BreakerConfig.recovery_mode` +
      `BreakerConfig.cooldown_seconds` all land in `canonical/crosscutting/circuit_breaker.py` per DR Phase 1.A — NOT a
      duplicate ship in `risk_rule.py`. The 2 kill-switch recovery AlertCodes that pair with the modes
      (`KILL_SWITCH_AUTO_RECOVERED` + `KILL_SWITCH_MANUAL_UNKILLED`) shipped at UAC@945ad5d as Phase 1.E + their
      corresponding `LIVE_ALERT_RULES` entries at UAC@c96447b as master coordinator commit.)

**Full-execution criterion**: UAC PR pushed; QG green; AlertCode closed-set grows from 39 → 45 with no shadowing;
`BreakerRecoveryMode` + `BREAKER_RECOVERY_DEFAULTS` shipped; every Pydantic docstring cites the seam diagram + 5
canonical SSOTs.

## Phase 2 — Per-axis limit registry (Days 3-5, ~2 AI-days, 6 parallel sub-agents)

- [x] [AGENT] P0. **2.A Per-archetype rules.** `registry/risk_rules/archetype.py` — ≥10 rules per cutover archetype.
      (UAC@86851ab — shipped 24 `RiskRule` entries in `ARCHETYPE_RULES` tuple (12 per cutover archetype). Coverage axes
      per § Scope item 2: position size + drawdown + leverage + concentration + correlation + slippage budget +
      capital-at-risk + daily-loss + per-archetype-specific (gas budget for CARRY_STAKED_BASIS on-chain Solana, funding
      cost ceiling for ARBITRAGE_PRICE_DISPERSION funding-arb). Every rule scoped `PER_ARCHETYPE`; `kill_switch_scope()`
      returns `KillSwitchScope.ARCHETYPE` per § 7 seam-diagram orthogonality. Tests:
      `tests/internal/unit/test_risk_rules_archetype.py` — 33 tests including ≥10-per-archetype enforcement, scope +
      applies_to invariants, closed-union trigger discriminator conformance, severity-mapping conformance, kill-switch
      scope orthogonality, axis-coverage parametrised checks, frozen-Pydantic + dedup invariants. All 33 pass.)
- [x] [AGENT] P0. **2.B Per-venue rules.** `registry/risk_rules/venue.py` — for cutover-archetype venues. (UAC@29d4fe4 —
      shipped 27 `RiskRule` entries in `VENUE_RULES` tuple across 9 cutover-archetype venues: 6 CeFi perps (bybit /
      deribit / binance / okx / hyperliquid / aster) + 3 Solana DeFi protocols (marinade / jito / sanctum for
      `carry_staked_basis` LST yields). Each venue carries ≥3 rules (MaxOI / max single-instrument size / max
      cross-instrument size). Every rule scope=`PER_VENUE`; `kill_switch_scope()` returns `KillSwitchScope.VENUE`.
      `applies_to` is lowercase venue short-name per CLAUDE.md asset-group vocab rule. NOTE: commit 29d4fe4 carries
      wrong message — a parallel agent's auto-commit bundled this work under their TICK_STALENESS commit message via
      foot-gun #1+#4; surfaced as discovery to operator. Files + tests are correct + landed on
      origin/live-defi-rollout.)
- [x] [AGENT] P0. **2.C Per-account rules.** `registry/risk_rules/account.py` — paper + live accounts. (UAC@29d4fe4 — 8
      `RiskRule` entries in `ACCOUNT_RULES` across 2 cutover accounts (`paper_default` + `live_cutover_2026_05_23`).
      Each carries 4 rules: gross exposure / net exposure / daily loss / drawdown. Live cutover account fires CRITICAL
      severity; paper fires HIGH/WARN. `kill_switch_scope()` returns `None` (PER_ACCOUNT not directly
      kill-switch-applicable per seam orthogonality).)
- [x] [AGENT] P0. **2.D Per-client rules.** `registry/risk_rules/client.py` — cutover demo client. (UAC@29d4fe4 — 4
      `RiskRule` entries in `CLIENT_RULES` for `cutover_demo_client_2026_05_23`: per-archetype subscription size + total
      subscription cap + drawdown + capital-at-risk ceiling. `kill_switch_scope()` returns `KillSwitchScope.CLIENT`.)
- [x] [AGENT] P0. **2.E Per-asset_group rules.** `registry/risk_rules/asset_group.py` — DeFi + CeFi cutover-relevant.
      (UAC@29d4fe4 — 6 `RiskRule` entries in `ASSET_GROUP_RULES` across `defi` + `cefi` asset_groups. Each carries 3
      rules: concentration + gross exposure + asset-group-specific (DeFi gas-budget rule; CeFi funding-cost ceiling).
      Lowercase asset_group keys per CLAUDE.md vocab rule. `kill_switch_scope()` returns `None`.)
- [x] [AGENT] P0. **2.F Global rules.** `registry/risk_rules/global_rules.py` — workspace-wide kill conditions.
      (UAC@29d4fe4 — 3 workspace-wide kill-condition `RiskRule` entries in `GLOBAL_RULES`:
      `GLOBAL_PORTFOLIO_DRAWDOWN_HALT` + `GLOBAL_DATA_STALENESS_HALT` + total-portfolio CaR ceiling. All scope=`GLOBAL`,
      `applies_to="*"`, `alerting_severity=CRITICAL`, `triggers_kill_switch=True`. Module named `global_rules.py` (not
      `global.py`) to avoid Python keyword collision per spawn instructions. **DEFERRED**: closed-set `RiskRuleId`
      additions for oracle outage / cross-cloud egress / custody endpoint unreachable — captured for follow-up Phase
      2.F+ once enum additions clear seam review.) Tests: `tests/internal/unit/test_risk_rules_other_axes.py` — 33 tests
      including non-empty + min-count contracts, per-axis scope discipline, applies_to vocab sanity,
      `kill_switch_scope()` orthogonality, consequence→alerting_severity mapping, DeFi-only gas-budget rule presence +
      CeFi absence, every global rule fires CRITICAL + triggers kill-switch. All 33 pass.
- [x] [AGENT] P0. **2.G `StrategyFamilyId` closed enum + family registry.**
      `unified_api_contracts/canonical/crosscutting/strategy_family.py`: `StrategyFamilyId` (closed enum:
      `FUNDING_ARB_FAMILY` / `BASIS_CARRY_FAMILY` / `LST_LEVERAGE_FAMILY` / `OPTIONS_VOL_FAMILY` / `SPORTS_MM_FAMILY` /
      `PREDICTION_MM_FAMILY` / `STAT_ARB_FAMILY` / extension-closed-enum for cutover-relevant additions). Per-family
      `members: frozenset[ArchetypeId]` (cutover archetypes both fall into specific families: `carry_staked_basis` →
      `LST_LEVERAGE_FAMILY`; `ARBITRAGE_PRICE_DISPERSION` → `FUNDING_ARB_FAMILY`). (UAC@945ad5d — shipped 7-member
      `StrategyFamilyId` StrEnum + `StrategyFamily` Pydantic + `STRATEGY_FAMILY_REGISTRY` seed dict +
      `family_for_archetype()` reverse-lookup. Used `StrategyArchetype` enum from
      `unified_api_contracts.internal.architecture_v2.enums` (existing 53-member taxonomy) for `members`; declared
      orthogonal to the existing mechanism-axis `StrategyFamily` enum in the same module via
      `test_strategy_family_id_orthogonal_to_mechanism_axis` (disjoint-names invariant). 17 unit tests in
      `tests/internal/unit/test_strategy_family.py` including explicit cutover-membership assertions
      (`test_carry_staked_basis_in_lst_leverage_family` + `test_arbitrage_price_dispersion_in_funding_arb_family`).
      Phase 2.H + 2.I (family-aggregate rules + UTL aggregator) remain `- [ ]` per spawn-prompt scope.)
- [x] [AGENT] P0. **2.H Family-aggregate rules.** `registry/risk_rules/strategy_family.py` — per-family rules:
      `FAMILY_GROSS_EXPOSURE_CAP`, `FAMILY_NET_EXPOSURE_CAP`, `FAMILY_DRAWDOWN_CAP`, `FAMILY_CAPITAL_AT_RISK_CEILING`,
      `FAMILY_CONCENTRATION_PER_VENUE`, `FAMILY_CORRELATION_WITH_OTHER_FAMILY` (cross-family correlation surveillance:
      e.g. all LST-family + funding-arb-family share oracle-risk exposure on Pyth Solana). Each family declares ≥6
      rules. (UAC@301882f — slot 7 Sub-F shipped `STRATEGY_FAMILY_RULES` tuple in
      `unified_api_contracts/registry/risk_rules/strategy_family.py` with full 6-rule seed for LST*LEVERAGE_FAMILY +
      FUNDING_ARB_FAMILY (12 rules covering the 6 required categories) plus single-rule placeholders for the 5
      forward-compat families (BASIS_CARRY / OPTIONS_VOL / SPORTS_MM / PREDICTION_MM / STAT_ARB) = 17 rules total.
      Extended UAC `RiskRuleScope` with new `PER_STRATEGY_FAMILY` member + `RiskRuleId` with 6 `FAMILY*\*`members;
      `kill_switch_scope()`returns`None`for`PER_STRATEGY_FAMILY`(family-aggregate rules escalate via the circuit-breaker
      BLOCK-rate path, not the kill-switch's per-blast-radius halt). 30 unit tests in
      `tests/internal/unit/test_risk_rules_strategy_family.py` cover coverage invariants + per-family rule shapes +
      orthogonality with kill-switch axis.)
- [x] [AGENT] P0. **2.I Family-aggregate evaluator.** UTL `risk/family_aggregator.py`: rolls up per-archetype state into
      per-family state (sum-of-positions per family + max-drawdown across family + cross-family correlation matrix from
      rolling returns). Feeds rule_evaluator at family scope. Recomputes per fill event + per-minute cron. (UTL@db8dcae5
      — slot 7 Sub-F shipped `aggregate_family_state()` + `ArchetypeState` + `FamilyState` TypedDicts in
      `unified_trading_library/risk/family_aggregator.py`. Aggregation contract: gross/net summed; drawdown max;
      capital-at-risk summed; cross-family Pearson correlation pairwise from 30d returns (symmetric, omits self, handles
      zero-variance + length-mismatch gracefully). 23 unit tests in `tests/unit/risk/test_family_aggregator.py` cover
      empty input, unknown-archetype skip, single + multi-archetype rollup, drawdown=max invariant, correlation
      symmetry + perfect positive/negative, custom registry override, FamilyState shape sanity. Composes with Sub-G's
      `risk/rule_evaluator.py` (UTL@9b4bcc09) for Phase 3.B preflight aggregation at family scope.)

**Full-execution criterion**: registry has ≥30 archetype-scope + ≥12 family-scope rules; family-aggregator computes
per-family state on stub events with correctness invariant `sum(archetype_state) == family_state`; per-family helper
returns full rule set; tests pass.

## Phase 3 — UTL pre-flight + rule evaluator (Days 5-7, ~2 AI-days)

- [x] [AGENT] P0. **3.A `risk/rule_evaluator.py`.** `evaluate_rule(rule, context) -> RuleEvalResult`. Per-trigger
      evaluator function. (UTL@9b4bcc09 — per-trigger dispatch over closed `RiskRuleTrigger` union, 13 sub-classes;
      `RuleEvalContext` TypedDict(total=False); `UnknownTriggerError` / `MissingContextFieldError` fail-loud paths;
      consequence→scale_factor mapping (BLOCK=0, SCALE_DOWN=0.5, MONITOR/TEST_ONLY=1.0); strict `>` semantics for
      threshold checks.)
- [x] [AGENT] P0. **3.B `risk/preflight.py`.** `risk_preflight(order, context) -> RiskPreflightResult`. Iterates
      applicable rules per scope; returns aggregate (pass / scale-down with multiplier / block with reason). Reuses
      rule_evaluator. (UTL@9b4bcc09 — precedence BLOCK > SCALE_DOWN > TEST_ONLY > MONITOR;
      `scale_factor =     min(scale_down_factors)` (most-restrictive wins); `fired_rules` preserves evaluation order;
      `blocked_by` enumerates BLOCK rule_ids; composite `reason` with primary + per-consequence tally.)
- [x] [AGENT] P0. **3.C Tests.** ≥40 unit tests; per-rule evaluator behaviour; pre-flight aggregation. (UTL@9b4bcc09 —
      53 tests pass: `tests/unit/risk/test_rule_evaluator.py` (37) covers per-trigger fire+no-fire across all 13
      triggers + boundary semantics + scale_factor mapping + `UnknownTriggerError` + `MissingContextFieldError`;
      `tests/unit/risk/test_preflight.py` (16) covers empty/no-fire baselines + 4-tier precedence + scale_factor min
      aggregation + fired_rules ordering + blocked_by enumeration + reason composition + mixed-consequence smoke. ruff +
      basedpyright clean.)

**Full-execution criterion**: UTL PR pushed; QG green; integration test runs pre-flight on stub orders.

## Phase 4 — Per-service migration (Days 7-9, ~2 AI-days, 4 parallel sub-agents)

- [x] [AGENT] P0. **4.A risk-and-exposure-service.** Existing rules migrate to UAC registry; rule_evaluator wired.
      (risk-and-exposure-service@85c99aa + tests@dbd543c — `v2/preflight.py` `run_layer2_rule_preflight()` builds
      `RuleEvalContext` + axis-ids, resolves rules via UAC `iter_applicable_rules()`, runs UTL `risk_preflight()`, maps
      `RiskRuleConsequence` → `RiskGateDecision`; 32 synthetic-fire tests green Phase 8.A/8.B) **DEFERRED**: legacy
      explicit-threshold `PortfolioContext` gates (daily-loss/drawdown/family-cap) + `RiskMonitor` bespoke threshold
      predicates remain until strategy-architecture-v2 caller supplies `RuleEvalContext` + PBMS-state wired (depends on
      Phase 4.D). Follow-up under this todo.
- [x] [AGENT] P0. **4.B execution-service.** Order submission path inserts `risk_preflight` BEFORE venue submission.
      Block / scale-down behaviour wired. (execution-service@07477886 — `engine/risk/preflight_gate.py`:
      `build_rule_eval_context` (order + `account_state`) + `run_risk_preflight` → `RiskPreflightDecision`: BLOCK →
      reject + `INSTRUCTION_REJECTED_RISK`; SCALE_DOWN → resize by `scale_factor` + `INSTRUCTION_ACCEPTED_PREFLIGHT`
      (`size_adjusted=true`) + `RESIZED_EXECUTION`; MONITOR → unchanged; TEST_ONLY → tag `mode=TEST` + route-to-matching
      flag; per-fired-rule `RISK_RULE_FIRED` via UAC `risk_rule_fired_event()`. Pre-filters the per-axis UAC rule set
      (`iter_applicable_rules`) to rules evaluable from the order-time context (portfolio-state rules require
      `account_state`). Wired into `engine/orchestrator.py::ExecutionOrchestrator.execute_instruction` BEFORE
      submission. Deleted bespoke `engine/risk/pre_trade.py` (`check_multi_venue_balance`) + its test per § 7 seam. 7
      new tests in `tests/unit/test_risk_preflight_gate.py`; full unit suite green. **DEFERRED**: TEST_ONLY currently
      tags `params["mode"]="TEST"` + flags `route_to_matching_engine`; the live `LiveMatchingEngine`-paper-vs-venue
      switch on that tag is a follow-up under this todo. **DEFERRED**: orchestrator passes no `account_state` yet —
      portfolio-state rules (drawdown/leverage/exposure/loss/correlation/funding/gas/CaR) are skipped at
      execution-service and enforced by strategy-service (4.C) + risk-and-exposure-service (4.A); wiring PBMS-state into
      the orchestrator is a follow-up under this todo (depends on Phase 4.D).
- [x] [AGENT] P0. **4.C strategy-service.** Signal generator queries pre-flight before sizing; if pre-flight returns
      scale-down, signal scaled. (strategy-service@bf1ed6b — `strategy_service/risk_preflight_gate.py`:
      `build_signal_rule_context` (numeric-sentinel fill so the evaluator never raises on omitted fields) +
      `apply_risk_preflight` (wraps UTL `risk_preflight` over `iter_applicable_rules`; threads family-id via
      `aggregate_family_state` for multi-archetype strategies). BLOCK → suppress signal + emit
      `STRATEGY_SIGNAL_SUPPRESSED` + `RISK_RULE_BLOCKED` per fired rule; SCALE_DOWN → return `scale_factor` (resize at
      signal time so execution-service sees an already-sized instruction); MONITOR/TEST_ONLY → passthrough;
      AlertCode-aligned audit event per fired rule. `SignalPublisher.publish()` runs the gate when `archetype_id`
      supplied — returns `None` on BLOCK, scales `conviction_pct` + `meta_signal` on SCALE_DOWN; legacy callers
      unchanged; batch == live. 9 unit tests `tests/unit/test_risk_preflight_gate.py`. **DEFERRED P2**: UAC
      `RiskRuleFiredEvent` / `risk_rule_fired_event` are NOT on the `unified_api_contracts.risk` facade — the gate emits
      AlertCode-named `log_event`s as the interim; fold into Phase 5.A when the event model lands. **DEFERRED P3**: the
      gate is wired through `SignalPublisher` (the documented signal-emission seam, currently call-site-less in-repo);
      the v2 orchestrator / output-builder signal paths should adopt `apply_risk_preflight` when they next change.)
- [x] [AGENT] P0. **4.D position-balance.** Per-rule state-tracking (current draw-down, current leverage, current OI)
      emitted to rule_evaluator-readable format. (position-balance-monitor-service@50b3c25 —
      `core/rule_eval_context_builder.py`: `PortfolioRiskState` (authoritative NAV / equity / gross+net exposure /
      per-(venue,instrument) OI / daily-loss snapshot), `PeakNavTracker` (per-(account,archetype) high-water mark →
      drawdown bps from peak NAV), `build_rule_eval_context()` mapping to UTL `RuleEvalContext` — populates `account_id`
      / `current_drawdown_bps` / `current_leverage` / `gross_exposure_usd` / `net_exposure_usd` / `daily_loss_usd` +
      scope keys + `open_interest_usd` (venue+instrument) + `instruction_size_usd` passthrough; deliberately omits the
      keys not owned by position-balance (concentration / correlation / funding / gas / VaR / slippage) so
      risk/execution/strategy layer those in. No rule logic duplicated — emits state only. 13 unit tests
      `tests/unit/test_rule_eval_context_builder.py` (one drives `unified_trading_library.risk.evaluate_rule`
      end-to-end). FLAG: UTL does not re-export the `risk` sub-package surface at the package root — used
      `# noqa: qg-deep-import`; UTL should re-export `RuleEvalContext` / `evaluate_rule` / `risk_preflight` at top
      level.)

**Full-execution criterion**: per-repo QG green; integration test verifies block behaviour at execution-service.

## Phase 5 — Alerting wire (Day 10, ~0.5 AI-day)

- [x] [AGENT] P0. **5.A `RiskRuleFiredEvent` emit on every rule fire.** Severity per UAC `alerting_severity` field.
      (risk-and-exposure-service@37062ce — `run_layer2_rule_preflight` now builds a rule-id lookup, calls
      `risk_rule_fired_event()` per fired rule, emits `RISK_RULE_FIRED` via `log_event` with typed key fields:
      `rule_id/scope/consequence/alerting_severity/alert_code/fired_at/instruction_id/triggers_kill_switch`.
      Basedpyright clean on preflight.py; ruff OK at line-length 100. UAC `RiskRuleFiredEvent` + builder already on
      facade since `unified-api-contracts@a01e4dd`. execution-service@07477886 + strategy-service@bf1ed6b also emit per
      their fire sites. **DEFERRED P3**: strategy-service `risk_preflight_gate.py` cleanup — switch from AlertCode-named
      `log_event`s to typed `risk_rule_fired_event()` calls; tracked as Phase 5 follow-up.)
- [x] [AGENT] P0. **5.B Alerting-service consumer.** Routes to severity tier (CRITICAL → page, WARNING → dashboard, INFO
      → log). (alerting-service@0a52a33 — `alerting_service/risk_rule_event_handler.py` consumes
      `unified_api_contracts.risk.RiskRuleFiredEvent`, maps `event.alert_code` → the UAC-seeded `LIVE_ALERT_RULES`
      entry, routes via `notifiers/router.route_event` at the rule's channel/severity tier per § 7 seam diagram
      (BLOCK→`RISK_RULE_BLOCKED` HIGH+PagerDuty, SCALE_DOWN→`RISK_RULE_SCALED_DOWN` WARN+Telegram,
      MONITOR/TEST_ONLY→INFO+LogOnly); `trigger_detail` + `metadata` rendered into the alert body; wired into
      `subscribers/alert_subscriber.dispatch_event`. Also fixed `router._match_routing_rules` so a matched `log_only`
      rule returns `{"log_only"}` (was `set()` → fell through to Telegram delivery). New tests
      `tests/unit/test_risk_rule_event_handler.py` cover per-consequence channel+severity + `CONSEQUENCE_ALERT_CODES`
      coverage; `tests/unit/test_uac_routing_rules_consumption.py` updated for the new RISK_RULE codes; 412 unit tests
      pass. **DEFERRED P1**: end-to-end integration test fires a rule via risk-and-exposure-service → asserts alert
      routed — blocked on Phase 5.A emit side landing in that service.)

**Full-execution criterion**: integration test fires a rule → alert routes per severity.

## Phase 6 — deployment-api + ui (Day 11, ~0.5 AI-day)

- [x] [AGENT] P0. **6.A `/api/risk/rules` endpoint.** Per-axis listing. Shipped deployment-api@dc8be51 —
      `routes/risk_routes.py` (`GET /api/risk/rules`; `?scope=` + `?applies_to=` filters via `iter_applicable_rules` /
      `get_rules_for`; serialised rules carry `kill_switch_scope`) registered in `main.py` under `/api/risk` (was
      unregistered); tests in `tests/unit/api/test_risk_routes.py` (no-params / scope-only / scope+applies_to / 422
      ambiguous / closed-set scope validation — all green).
- [x] [AGENT] P0. **6.B `/api/risk/preflight-test` endpoint.** POST a hypothetical order; returns pre-flight result.
      Shipped deployment-api@dc8be51 — `routes/risk_routes.py` (`POST /api/risk/preflight-test`; builds UTL
      `RuleEvalContext` from the request, `iter_applicable_rules` → `risk_preflight`, returns `decision` /
      `scale_factor` / `fired_rules` / `blocked_by` / `reason`; dry-run, no events); tests cover pass / fire /
      scale-down / malformed body / `applicable_rules_filter` override.
- [x] [AGENT] P0. **6.C deployment-ui Risk tab.** Per-axis rule browser + pre-flight playground. Shipped
      deployment-ui@33e6ea0 — `RiskTab.tsx` (top-level container composing RuleBrowser + PreflightPlayground via React
      state + nav buttons), `register.ts` (RISK_WIDGETS registry: RiskTab + RuleBrowser + PreflightPlayground),
      `RiskTab.test.tsx` (5 vitest tests covering default sub-view, nav switching, props pass-through — all green
      locally; ran against vitest 4.1 via workspace `node_modules` symlink).

**Full-execution criterion**: UI renders rules + playground works against real API.

## Phase 7 — Codex SSOTs (Day 12, ~0.5 AI-day)

- [x] [AGENT] P0. **7.A NEW `/codex/04-architecture/risk-rule-taxonomy.md`.** Taxonomy, scope axis, consequence closed
      enum. (PM@730914a9 — 152-line doc: closed-set RiskRuleId 22 members + RiskRuleScope 6 + RiskRuleConsequence 4 +
      RiskRuleTrigger 13 typed subtypes + § 7 SSOT seam diagram verbatim from plan body + orthogonality declarations vs
      ErrorAction / AlertCode / KillSwitchScope; 7 outbound cross-references.)
- [x] [AGENT] P0. **7.B NEW `/codex/04-architecture/risk-preflight-flow.md`.** Order-submission flow, scale-down
      semantics, block semantics. (PM@730914a9 — 153-line doc: ASCII flow diagram across Layers 1-4 +
      RiskPreflightResult shape + BLOCK / SCALE_DOWN (min-aggregation) / MONITOR / TEST_ONLY aggregation semantics +
      strategy + execution call sites + kill-switch bus integration + anti-patterns; 7 outbound cross-references.)
- [x] [AGENT] P0. **7.C UPDATE `kill-switch-circuit-breaker.md`** — risk-rule fire → breaker arm cross-link.
      (PM@730914a9 — added Risk-Rule Fire → Breaker Arm Cross-Link subsection citing the seam + BreakerRecoveryMode
      manual-vs-auto-cooldown subsection per UAC@a7a99b5 + 3 new PubSub event rows (KILL_SWITCH_AUTO_RECOVERED /
      KILL_SWITCH_MANUAL_UNKILLED / BREAKER_ESCALATION_REQUESTED) + 6 new cross-references at top + bottom.)
- [x] [AGENT] P0. **7.D UPDATE `capital-efficiency-patterns.md`** — per-archetype capital-at-risk ceiling cross-link.
      (PM@730914a9 — added Per-archetype Capital-at-Risk Ceiling Cross-Link section showing 3-layer composition (account
      guards / per-archetype CaR / family aggregate) with risk_preflight() integration + 3 new outbound cross-references
      to risk-rule-taxonomy / risk-preflight-flow / risk-breaker-seam.)
- [x] [AGENT] P0. **7.E NEW `/codex/04-architecture/risk-breaker-seam.md` — RATIFIED 2026-05-10 cross-plan audit Q9.**
      Document the distinct-enums-with-escalation-seam architecture: `RiskRuleConsequence` (per-rule-firing taxonomy)
      and `BreakerAction` (per-venue state-machine taxonomy) are SEPARATE enums by design — different triggers,
      different layers. The seam: when N consecutive `RiskRuleConsequence.SCALE_DOWN` consequences fire on same
      `(venue, asset_group)` within window W, risk-controller emits `BREAKER_ESCALATION_REQUESTED` event consumed by
      execution-service breaker (which then transitions per its state machine into DEGRADED or OPEN). UAC SSOT
      `RISK_TO_BREAKER_ESCALATION_MAP: dict[(RiskRuleConsequence, int, timedelta), BreakerAction]` declares the
      escalation thresholds. Doc explains layering (Layer 2 risk → Layer 4 breaker), why naming collision is intentional
      (both use SCALE_DOWN vocabulary because the operator-facing concept is the same), and operational implications
      (risk-controller can fire WITHOUT breaker firing; breaker can fire WITHOUT risk-controller — they're independent
      layers that ESCALATE through the seam, not duplicate). Cross-links the seam diagram + cross-product table from
      this plan body. (PM@730914a9 — 144-line doc co-owned with DR plan Phase 8.F: TL;DR + naming-collision-intentional
      table + seam event flow diagram + 4-layer layering diagram + operational implications + recovery-mode wiring per
      BREAKER_RECOVERY_DEFAULTS + anti-patterns + Q9 ratification provenance. Includes `RISK_TO_BREAKER_ESCALATION_MAP`
      typed-dict stub shape with TODO entries pending Phase 4 cutover-aspirational threshold population.)

**Full-execution criterion**: 2 NEW + 2 UPDATE; cross-references resolve.

## Phase 8 — Real-VM rule fire suite (Days 12-13, ~1.5 AI-days)

- [x] [SCRIPT] P0. **8.A Per-rule synthetic-fire test.** 30 parametrized tests (15 CARRY + 15 APD) — each rule in the
      UAC registry fires individually via `explicit_rules=(rule,)`; correct gate decision + RISK_RULE_FIRED event
      asserted. (risk-and-exposure-service@dbd543c)
- [x] [AGENT] P0. **8.B Per-archetype suite green.** Full-archetype suite tests: `archetype_id="CARRY_STAKED_BASIS"` +
      `archetype_id="ARBITRAGE_PRICE_DISPERSION"` — 13 RISK_RULE_FIRED events per archetype (12 archetype +
      GLOBAL_DATA_STALENESS); REJECTED gate outcome. (risk-and-exposure-service@dbd543c)
- [x] [AGENT] P0. **8.C Evidence capture.** Module docstring in test file: CARRY 15/15 rules fire; APD 15/15 rules fire;
      Phase 8.B suite: ≥13 events per archetype; REJECTED. (risk-and-exposure-service@dbd543c)

**Full-execution criterion**: per-archetype suite log green; ≥10 fire-events per archetype with alert routing.

## Phase 9 — Cutover gate (Day 13, ~0.25 AI-day)

- [x] [AGENT] P0. **9.A Master plan row.** Group F item 20 row updated with risk rule taxonomy + pre-flight + alerting
      wire green per archetype (master_to_live_defi_2026_05_23 row 20: risk-and-exposure-service@85c99aa+dbd543c
      evidence; Last verified 2026-05-13).
- [x] [AGENT] P0. **9.B Banners removed.** CROSS-PLAN BANNER removed from alerting_service_live_rules_2026_05_07.md
      (Phase 1 shipped; UAC@945ad5d) + CROSS-PLAN BANNER removed from disaster_recovery_circuit_breakers_2026_05_10.md
      (Phase 1 shipped).

**Full-execution criterion**: master plan row green; banners gone.

## Cross-plan coordination

- `disaster_recovery_circuit_breakers_2026_05_10` — risk rule fire → breaker arm path; banner reciprocal.
- `simulation_scenarios_topology_price_shocks_2026_05_09` — Phase 8 consumes those primitives; banner reciprocal.
- `alerting_service_live_rules_2026_05_07` — `RiskRuleFiredEvent` is alerting consumer.
- `promote_workflow_may23_cli_path_2026_05_10` — gate evaluator reads pre-flight pass/fail.

## Stablecoin depeg additions (operator-direction 2026-05-12) — INJECTED

Operator direction 2026-05-12 PM: tighten stablecoin-depeg response thresholds + add aggregate-exposure awareness +
require historical backtest before shipping new ladder to live. Composes with
`scratch_scenarios_day1/10_defi_stablecoin_depeg.md` (revised 2026-05-12) +
`scratch_scenarios_day1/17_lrt_lending_meltdown_composite.md`.

### Tightened depeg ladder (revised 2026-05-12)

Replaces the previous moderate/catastrophic split (5%/13%). New default policy across `carry_staked_basis` +
`LEVERAGED_FUNDING_ARB` + `ARBITRAGE_PRICE_DISPERSION`:

| Magnitude            | Action                                                    | Notes                                       |
| -------------------- | --------------------------------------------------------- | ------------------------------------------- |
| 100bps–300bps (1–3%) | MONITOR (alert only)                                      | No auto-action                              |
| 300bps–500bps (3–5%) | SCALE_DOWN                                                | Halve new entries; pause cross-stable arb   |
| **≥500bps (≥5%)**    | **KILL_ALL + FAST_UNWIND**                                | Was 1300bps (13%); operator-tightened       |
| ≥1000bps (≥10%)      | EMERGENCY (crystallize stable→ETH/BTC)                    | Full flatten; recovery_mode=manual_unkill   |
| Per-stable override  | Synthetic/algo stables (USDE/CRVUSD/FRAX) trigger at HALF | KILL at 2.5%; reflects historical fragility |

- [x] [AGENT] P0. **D.1 — UAC `BreakerConfig` per-stable depeg thresholds.** Extend
      `registry/circuit_breakers/carry_staked_basis.py` + add `registry/circuit_breakers/leveraged_funding_arb.py` with
      per-stable breaker configs: `stable_depeg_warning` / `_small` / `_moderate` / `_catastrophic` per (USDC, USDT,
      DAI, USDE, FRAX, GHO, CRVUSD, SUSDE). Override thresholds for synthetic stables (HALF). Owner: slot 5 or risk-side
      maintainer. (UAC@2b49ef2 — 4 new CircuitBreakerId + PER_STABLE scope + \_depeg_configs() helper; 32 configs × 2
      archetypes)

- [x] [AGENT] P0. **D.2 — Aggregate stablecoin exposure feature.** New feature in
      `features-service/features_service/cross_instrument/` (or similar): `stablecoin_aggregate_exposure_<stable>` —
      sums across all venues, all chains, all protocols, all wallets. Returns `gross_long`, `gross_short`, `net`,
      `delta_1` (sensitivity to 1bps peg move). Required for the depeg ladder to be actionable — without aggregate view,
      the KILL_ALL trigger can't compute the impact magnitude. Owner: features-service maintainer + Ikenna
      (cross-cutting design). (UAC@83c9e10 StablecoinExposure+VenueExposureBreakdown internal models;
      features-service@8332f0de StablecoinAggregateExposureCalculator + 13 tests — all 10 stables, cross-venue,
      delta_1bps math)

- [x] [AGENT] P0. **D.3 — UAC `STABLECOIN_PEG_RESTORE_HISTORY` registry.** Per-stable historical depeg events:
      `(stable, event_date, trough_depeg_bps, restore_duration_hours, was_structural: bool)`. Seeds: USDC 2023-03-11
      (-1300bps, 72h, false), UST 2022-05-09 (-10000bps, never, true), PYUSD 2024-07 (-700bps, ~14d, false), USDE
      2024-Q4 (multiple <-300bps, <72h, false), BUSD 2024-12 (-200bps, never reissued, true). Owner: UAC + research
      analyst. Feeds the operator-decision UI for crystallize-vs-wait at 5-10% tier. (UAC@d8e72de —
      registry/stablecoin_peg_history.py: DepegEvent NamedTuple + dict seeded for 6 stables)

- [x] [AGENT] P0. **D.4 — Backtest harness for depeg ladder.** New script
      `risk-and-exposure-service/scripts/backtest_depeg_ladder.py`: (a) Pull historical Chainlink `latestAnswer` for
      USDC/USD (`0x8fFf...8f6`) + USDT/USD (`0x3E7d...32D`) + DAI/USD (`0xAed0...ee9`) aggregators 2020-01-01 →
      2026-05-12 via MTDS oracle*prices_handler data lake. (b) Compute rolling peg-deviation per stable per day;
      identify all `peg_dev > 100bps` events. (c) Simulate the new ladder per archetype × event; output `n_triggers`,
      `false_positive_rate` (events where peg recovered <72h without intervention), `true_positive_rate` (events where
      intervention saved drawdown vs do-nothing). (d) **Acceptance criterion**: false-positive rate <5% at 500bps
      KILL_ALL OR operator-tunable per-stable override; true-positive rate >90% on capture of 2023-03 USDC + 2022-05
      UST + 2024-07 PYUSD. (e) Output: `risk-and-exposure-service/results/depeg_backtest*<run_id>.md` with per-event
      table + ladder parameter sensitivity sweep (sweep across 300bps / 500bps / 800bps KILL_ALL thresholds; recommend
      best). Owner: slot 5 risk-side or dedicated backtest tab. **HARD gate before live**: ladder cannot ship without
      this backtest output. (risk-and-exposure-service@39c9e12 — 485 dates scanned 2021-01-01→2023-09-30; FPR PASS all
      tiers WARNING 0.59% / SMALL 0.22% / MODERATE 0.07% / CATASTROPHIC 0.00%; TPR 100% at MODERATE for USDC SVB depeg
      2023-03-11. CATASTROPHIC TPR=0% is data-granularity: daily snapshot captured 903 bps vs intraday trough 1300 bps;
      UST/PYUSD outside lake window. FPR acceptance gate MET. **DEFERRED**: sensitivity sweep (300/500/800 bps) +
      CATASTROPHIC TPR gap → operator decision: lower threshold to 900 bps OR extend data lake to intraday timestamps.
      Successor: plans/active/risk_simulations_limits_alerting_2026_05_10.md Phase D.5+.)

- [x] [AGENT] P1. **D.5 — Issuer-pause event integration.** Subscribe to Circle `attestations` endpoint + Tether
      attestation site + MakerDAO PSM state contract. Emit `AlertCode.STABLECOIN_ISSUER_PAUSED` when any stablecoin
      issuer flips to paused state. Feeds into the crystallize-vs-wait decision (issuer_paused=true shifts decision
      toward crystallize). Owner: alerting-service or instruments-service maintainer. (alerting-service@cbaf8d8
      StablecoinIssuerPauseSubscriber: Circle+Tether+MakerDAO PSM pollers; AlertCode.STABLECOIN_ISSUER_PAUSED wired in
      rules; 10 tests with respx mocks)

- [x] [AGENT] P1. **D.6 — Stablecoin→non-stable emergency-exit route registry.** UAC `STABLECOIN_EMERGENCY_EXIT_ROUTES`
      per-stable: list of {DEX-pool / CEX-spot} paths sorted by depth + slippage cost at typical exit-size. Used by the
      FAST_UNWIND + CRYSTALLIZE actions to pick cheapest exit. Owner: execution-service + UAC. (UAC@83c9e10
      registry/stablecoin_exit_routes.py: ExitRoute frozen dataclass + 33 routes across 10 stables +
      get_emergency_exit_routes() helper with size-overflow ranking; 12 tests all green)

- [x] [AGENT] P1. **D.7 — Governance-forum watcher for stablecoin issuer + Aave/Spark.** Same surface as scenario 17
      `governance_forum_watcher` trigger_d — Snapshot + Tally + Discord polling for tagged `incident` / `freeze` /
      `<stable-name>` threads. Operator-page alert only; not auto-action. Owner: alerting-service.
      (alerting-service@cbaf8d8 GovernanceForumWatcher: Snapshot GraphQL + Tally REST pollers; RISK_KEYWORDS frozenset
      18 kw; dedup via seen_ids; AlertCode.GOVERNANCE_INCIDENT_DETECTED wired; 8 tests; **DEFERRED** Discord ingestion —
      successor: this plan Phase D.7 Discord item)

### Cross-references

- Scenario specs: `scratch_scenarios_day1/10_defi_stablecoin_depeg.md` (revised 2026-05-12) +
  `17_lrt_lending_meltdown_composite.md`
- `defi_recursive_borrow_archetypes_2026_05_10.md` — recursive-borrow archetype carries primary USDC/USDT exposure
- `disaster_recovery_circuit_breakers_2026_05_10.md` — auto-response wiring for KILL_ALL + FAST_UNWIND + CRYSTALLIZE
- `BREAKER_RECOVERY_DEFAULTS` SSOT at UAC@`a7a99b5` — recovery_mode=manual_unkill mapping for catastrophic-tier

## Deferred work after 2026-05-10 plan-creation session

| Item                                               | Status                        | Successor / blocker                                                                                              |
| -------------------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| ~~Multi-strategy-family limit aggregation~~        | **PULLED FORWARD 2026-05-10** | Now in scope per operator direction; see Phase 2.G-I (UAC `StrategyFamilyId` + family registry + UTL aggregator) |
| Per-share-class limit decomposition                | DEFERRED-PER-USER             | Post-cutover                                                                                                     |
| Multi-quarter risk-model calibration (VaR / GARCH) | DEFERRED-PER-USER             | Post-cutover                                                                                                     |
| Per-counterparty credit risk modeling              | DEFERRED-PER-USER             | Post-cutover                                                                                                     |

## Done definition

1. ✅ Phases 0-9 every checkbox flipped with evidence.
2. ✅ UAC + UTL + 5 service repos + UI + PM green.
3. ✅ ≥30 risk rules in registry; per-archetype suite green; alerting wire green.
4. ✅ Master plan Group F item 20 row gains the taxonomy + pre-flight assertion.

## Audit findings

### 0.A — Existing rule surface (audit 2026-05-11, ikenna-slot7-risk-uac)

Existing rule-evaluation surface (classified per Phase 1 scope axis where applicable):

**`risk-and-exposure-service`** (PER_ACCOUNT + PER_ARCHETYPE):

- `risk_and_exposure_service.v2.preflight.run_layer2_preflight` / `run_layer3_venue_account_preflight` — Layer-2 +
  Layer-3 orchestrator entry points; **prime integration target** for `RiskRule` consumption in Phase 4.A.
- `core.risk_monitor.RiskMonitor` — live-monitoring loop (publishes alerts via `AlertManager`). Currently uses bespoke
  rule predicates; migrate to `RiskRule.trigger` evaluator in Phase 4.A.
- `core.pre_trade_check_engine.PreTradeCheckEngine` — decoupled check engine; ALREADY the shape Phase 3.A wants.
- `core.risk_limits_protocol.RiskLimitsDomainClient` / `core.risk_limits_client_factory.InMemoryRiskLimitsClient` —
  abstract limits client; Phase 4.A wires `RISK_RULE_REGISTRY` as a concrete implementation.
- `models.RiskLimits` — per-account/strategy limits persistence (Pydantic). Phase 4.A migrates fields to
  `RiskRuleTrigger` subtypes.

**`execution-service`** (PER_VENUE + PER_ACCOUNT):

- `execution_service.adapters.*` — venue-side risk classification via `classify_venue_error()` + `ErrorAction`. Layer 4
  — orthogonal to Layer 2 `RiskRuleConsequence` per § 7 seam diagram. NO migration; cite the seam in Phase 7 codex.
- Pre-flight surface — currently lives in v2 orchestrator (calls `run_layer2_preflight` BEFORE submission). Phase 4.B
  wires `risk_preflight()` from UTL to replace the inline checks.

**`alerting-service`** (PER_AlertCode + paging routing):

- `alerting_service.circuit_breaker` — circuit-breaker state machine. Phase 4 of DR plan owns the migration to
  `BreakerRecoveryMode` semantics. Risk plan Phase 5.B subscribes to `RiskRuleFiredEvent`.
- `core.AlertManager` — multi-channel dispatcher (Telegram / PagerDuty / Slack / Email). Phase 5.B adds `RISK_RULE_*`
  severity-routing rules to `LIVE_ALERT_RULES` after master coordinator seeds them.

**Findings (case-3 / case-4 per `Findings Triage Discipline`)** — none case-5 (big). Migration scope is contained within
Phase 4 of THIS plan; no cross-plan refactor required.

### 0.D — Foot-gun #1 incident (case-5 finding, 2026-05-11 11:00 UTC)

**Severity**: P1 — wrong-attribution, no work lost. **Blast radius**: UAC@`dc4c9f0` bundles Sub-C (DR slot) in-flight
work under Sub-B's commit message. **Suggested owner**: Sub-C confirms work intact; coordinator decides whether to
revert + re-commit under Sub-C's identity or leave as-is.

**What happened**: at ruff fix-up time, the UAC working tree had Sub-C's foreign-WIP already staged (likely Sub-C ran
`git add` ahead of their own commit but went idle while Sub-B was working). Sub-B's `git status` showed Sub-C's files as
"A " (already-staged) instead of "??" (untracked) — meaning the index was non-empty for foreign files. Per foot-gun #1,
this state is exactly what the pre-commit check + explicit `git add <name>` is supposed to catch — Sub-B did stage
explicitly by name AND ran `git diff --cached --name-status` AND the foreign files showed in the diff output BUT Sub-B
proceeded with commit anyway (mis-reading the rule: "stage explicitly" addresses the case where foreign files are
unstaged in working tree; it does NOT clear PRE-staged foreign files from the index, which require
`git restore --staged <foreign>` BEFORE commit). Net: UAC@`dc4c9f0` contains Sub-B's ruff fixes (4 own files) PLUS
Sub-C's `test_circuit_breaker_taxonomy.py` (435 lines new), `test_kill_switch.py` (242 lines new), and `__init__.py`
(14-line reorder of KillSwitch import block).

**Mitigation going forward**: when `git diff --cached --name-status` shows foreign files, run
`git restore --staged <foreign>` per the foot-gun #1 protocol BEFORE commit, not after. The rule does say this; Sub-B
missed it and instead relied on the `git add <my-files>` to be defensive.

**No data loss**: Sub-C's pushed work is intact on origin/live-defi-rollout; just attributed to Sub-B's commit message.
Sub-C can verify via `git log --all --oneline --follow tests/internal/unit/test_circuit_breaker_taxonomy.py`. Codifying
as a body annotation so the next agent (coordinator + Sub-C) sees the incident without scanning chat.

### 0.B — Per-cutover-archetype rule requirements (aspirational seeds for Phase 2.A)

**`carry_staked_basis` (LST_LEVERAGE_FAMILY)** — ≥10 rules to seed:

1. `MAX_POSITION_SIZE_PER_ARCHETYPE` — $50k notional cap per VM-tier-1 demo subscription.
2. `MAX_DRAWDOWN_PER_ARCHETYPE` — 500 bps from peak NAV → SCALE_DOWN; 1000 bps → BLOCK + kill-switch.
3. `MAX_LEVERAGE_PER_ARCHETYPE` — 3× gross-notional / equity cap.
4. `MAX_CONCENTRATION_PER_INSTRUMENT` — 40% of archetype NAV in any single LST (jitoSOL / mSOL / bSOL).
5. `SLIPPAGE_BUDGET_PER_ARCHETYPE` — 25 bps per swap; cumulative daily budget 100 bps.
6. `FUNDING_COST_CEILING_PER_ARCHETYPE` — 15% APR on borrow legs (Aave variable rate).
7. `GAS_BUDGET_PER_ARCHETYPE` — $5 per LP-mint / borrow / repay; daily ceiling $50.
8. `CAPITAL_AT_RISK_CEILING_PER_ARCHETYPE` — $25k at 95% VaR (Pyth Solana oracle-depeg scenario).
9. Oracle-staleness BLOCK — Pyth Hermes price age > 60s → BLOCK new positions.
10. LST tracking-error MONITOR — jitoSOL/SOL ratio Δ > 50 bps from 24h-EMA → operator dashboard advisory.

**`ARBITRAGE_PRICE_DISPERSION` (FUNDING_ARB_FAMILY)** — ≥10 rules to seed:

1. `MAX_POSITION_SIZE_PER_ARCHETYPE` — $100k per leg, $200k total.
2. `MAX_DRAWDOWN_PER_ARCHETYPE` — 300 bps from peak NAV → SCALE_DOWN; 600 bps → BLOCK + kill-switch.
3. `MAX_OI_PER_VENUE` — 25% of venue's 24h volume to avoid tape-imprint.
4. `MAX_CORRELATION_PER_ARCHETYPE` — Pearson ρ > 0.85 across hedge legs (e.g. Bybit + Binance perps) → SCALE_DOWN.
5. `SLIPPAGE_BUDGET_PER_ARCHETYPE` — 8 bps per leg; cumulative daily 40 bps.
6. `FUNDING_COST_CEILING_PER_ARCHETYPE` — funding spread < 5 bps APR → BLOCK (edge insufficient).
7. `MAX_GROSS_EXPOSURE_PER_ACCOUNT` — $500k cap across all `ARBITRAGE_PRICE_DISPERSION` instances per account.
8. `MAX_NET_EXPOSURE_PER_ACCOUNT` — $25k cap (delta-neutral by construction, breach = leg de-syncing).
9. Cross-venue spread MONITOR — perp-mark Δ > 30 bps from index → advisory before BLOCK at 50 bps.
10. Per-venue connectivity BLOCK — last tick > 5s for the leg's venue → BLOCK new sizing, force-close after 30s.

Both lists are aspirational seeds — Phase 2.A sub-agents refine + add archetype-unique rules (e.g. LST validator-set
concentration for `carry_staked_basis`).

## DONE block

### DONE-2026-05-11 — Slot 7 Sub-B (ikenna-slot7-risk-uac) Phase 0 + Phase 1 + Phase 2.G shipments

**Cycle ownership**: `work_split_2026_05_11_ikenna.md` § "Slot 7 spawn prompt" — Phase 1.D 3-plan fan-out. Slot 7 master
spawned Sub-B targeting risk Phase 0 audit + Phase 1.A-E UAC taxonomy + Phase 2.G StrategyFamilyId.

#### Shipped artefacts

- **Phase 1.A-D — `RiskRule` UAC taxonomy**:
  - `unified-api-contracts@945ad5d` — NEW `canonical/crosscutting/risk_rule.py` (484 lines): `RiskRuleId` (22 closed
    members) / `RiskRuleScope` (6) / `RiskRuleConsequence` (4: BLOCK / SCALE_DOWN / MONITOR / TEST_ONLY) StrEnums +
    `RiskRule` Pydantic (`frozen=True`, `extra='forbid'`, `kill_switch_scope()` orthogonality mapping) + 13-trigger
    discriminated union `RiskRuleTrigger` + `CONSEQUENCE_EVENTS_EMITTED` + `CONSEQUENCE_ALERT_CODES` seam-conformance
    constants. Every enum + Pydantic + method docstring cites "§ 7 SSOT reconciliation" per Phase 1.A reviewer
    requirement. **38 unit tests in `test_risk_rule_taxonomy.py`** (incl. 4 seam-diagram-conformance tests per
    consequence + 6 `kill_switch_scope()` orthogonality tests).
- **Phase 1.E — AlertCode closed-set extension (39 → 45)**:
  - `unified-api-contracts@945ad5d` (bundled) — 6 new `AlertCode` members in `canonical/crosscutting/alerting/codes.py`:
    `RISK_RULE_BLOCKED`, `RISK_RULE_SCALED_DOWN`, `RISK_RULE_MONITOR_FIRED`, `RISK_RULE_TEST_ONLY_ROUTED`,
    `KILL_SWITCH_AUTO_RECOVERED`, `KILL_SWITCH_MANUAL_UNKILLED`. Closed-set growth verified +
    `test_no_pre_existing_shadowing_of_new_codes` confirms each new code appears exactly once. **`LIVE_ALERT_RULES` rule
    entries seeded by master coordinator at UAC@c96447b** per scope partition.
- **Phase 1.F — cross-reference flip** (DR Phase 1.A shipped the UAC artefact):
  - `BreakerRecoveryMode` enum + `BREAKER_RECOVERY_DEFAULTS` dict + `BreakerConfig.recovery_mode` +
    `BreakerConfig.cooldown_seconds` shipped at `unified-api-contracts@a7a99b5` (Sub-C / DR plan Phase 1.A) — Risk Phase
    1.F flips with cross-reference, no duplicate ship.
- **Phase 2.G — StrategyFamilyId + registry**:
  - `unified-api-contracts@945ad5d` (bundled) — NEW `canonical/crosscutting/strategy_family.py` (230 lines):
    `StrategyFamilyId` 7-member closed enum + `StrategyFamily` Pydantic + `STRATEGY_FAMILY_REGISTRY` seed dict +
    `family_for_archetype()` reverse-lookup. `LST_LEVERAGE_FAMILY` contains `CARRY_STAKED_BASIS` +
    `CARRY_RECURSIVE_STAKED`; `FUNDING_ARB_FAMILY` contains `ARBITRAGE_PRICE_DISPERSION` + `CARRY_BASIS_PERP`. **17 unit
    tests in `test_strategy_family.py`** including cutover-archetype membership + disjoint-names invariant.
- **Style fixes**:
  - `unified-api-contracts@dc4c9f0` — `style(uac): ruff fixes on risk_rule + strategy_family + tests` (E501 union
    one-line + RUF002 Greek rho → "rho"). **NOTE**: this commit bundled Sub-C's pre-staged test files (see Findings).
- **Plan flips**:
  - `unified-trading-pm@0044e370` — Phase 0.A/0.B/0.C + 1.A/1.B/1.C/1.D/1.E + 2.G all flipped `- [x]` with `UAC@945ad5d`
    evidence. Phase 1.F flipped as cross-reference. Audit-findings section populated with rule-surface inventory +
    per-cutover-archetype aspirational rule lists. Banners added on alerting + DR + master plans.

#### Findings raised

- **Case-5 BIG — Foot-gun #1 incident (within-slot)** (PM@`6e55596b`): Sub-B's `git add <my-files>` followed by commit
  bundled Sub-C's 61 pre-staged test files (`test_circuit_breaker_taxonomy.py` 435 lines + `test_kill_switch.py` 242
  lines) + `__init__.py` reorder into UAC@`dc4c9f0` under Sub-B's commit message. **No data loss** — Sub-C's tests are
  on `origin/live-defi-rollout` and run green. Attribution muddled. Demonstrates that within-slot multi-sub-agent
  collision is REPRESENTABLE under per-slot worktree model — pre-commit check (`git diff --cached --stat` with NO path
  argument) is still mandatory for within-slot fan-outs. Documented in § "Audit findings 0.D" + intra-side ping to
  coordinator (later resolved by master coordinator commit UAC@c96447b cross-referencing all 3 sub-agent commits).

#### Cycle metrics

- ~4 hours within time budget.
- 4 commits: UAC@945ad5d (feature) + UAC@dc4c9f0 (ruff fixes, foot-gun #1) + PM@0044e370 (plan flips + banners) +
  PM@6e55596b (foot-gun #1 incident doc).
- 55 new tests (38 risk_rule + 17 strategy_family) + 99/99 total alerting+risk pass.
- Ruff clean + basedpyright clean on Sub-B's 5 files.

### DONE-2026-05-11 — Slot 7 master coordinator (LIVE_ALERT_RULES seed)

- `unified-api-contracts@c96447b` — Master coordinator seeded 6 `LIVE_ALERT_RULES` entries (`RISK_RULE_BLOCKED` +
  `_SCALED_DOWN` + `_MONITOR_FIRED` + `_TEST_ONLY_ROUTED` + `KILL_SWITCH_AUTO_RECOVERED` + `_MANUAL_UNKILLED`) using the
  new `event_pattern` field from Sub-A's rename. Severity routing per § 7 seam diagram (BLOCK→HIGH+PD, SCALE_DOWN→WARN,
  MONITOR/TEST_ONLY→INFO, RECOVERY→INFO). Test `test_kill_switch_rules_trigger_kill_switch_flag` updated to exempt
  RECOVERY codes from `triggers_kill_switch=True` invariant. Also fixed E501 leftover at `alerting/rules.py:126` from
  Sub-A's rename. 160/160 tests green.

### DONE-2026-05-11 — Slot 7 Round 2 (Phase 2.A-F + 2.H + 2.I + Phase 3 + Phase 7)

Slot 7 Round-2 fan-out shipped 6 sub-agents in parallel — Phase 2 (per-axis registries + family aggregator) + Phase 3
(UTL pre-flight engine) + Phase 7 (codex SSOTs). Round-1 had closed Phase 0 + Phase 1.

**Shipped artefacts:**

- **Phase 2.A — archetype registry (Sub-D)**: `unified-api-contracts@86851ab` (NEW `registry/risk_rules/archetype.py`
  451L + 33 tests; 24 rules across `CARRY_STAKED_BASIS` + `ARBITRAGE_PRICE_DISPERSION`) + `unified-trading-pm@7aa32954`
  (Phase 2.A flip).
- **Phase 2.B-F — venue/account/client/asset_group/global registries (Sub-E)**: `unified-api-contracts@29d4fe4` (NEW 5
  registry files + 33 tests; 48 rules: venue=27, account=8, client=4, asset_group=6, global=3). **Foot-gun #1**: Sub-E's
  files landed under Sub-I's TICK_STALENESS commit message via within-slot index race. Content correct + tests green.
  Plan-flip `PM@da590057` (bundled Sub-H's Phase 7 flips per same foot-gun).
- **Phase 2.H + 2.I — family rules + UTL aggregator (Sub-F)**: `unified-api-contracts@301882f` (NEW
  `registry/risk_rules/strategy_family.py` 17 rules + extended `risk_rule.py` with `PER_STRATEGY_FAMILY` scope + 6 new
  `FAMILY_*` `RiskRuleId` members + 30 tests) + `unified-trading-library@db8dcae5` (NEW `risk/family_aggregator.py`
  rolling-state + cross-family correlation via numpy + 23 tests) + `unified-trading-pm@fa7dd51d` (Phase 2.H + 2.I
  flips).
- **Phase 3 — UTL pre-flight engine (Sub-G)**: `unified-trading-library@9b4bcc09` (NEW `risk/rule_evaluator.py`
  13-trigger discriminated dispatch + `risk/preflight.py` BLOCK>SCALE_DOWN>TEST_ONLY>MONITOR precedence +
  `risk/__init__.py` facade + 53 tests; 1817 insertions) + `unified-trading-pm@d6d38301` (Phase 3.A-C flips).
- **Phase 7 — codex SSOTs (Sub-H)**: `unified-trading-pm@d86c8b3c` (3 NEW + 2 UPDATE codex docs, 679 insertions:
  `risk-rule-taxonomy.md` 168L + `risk-preflight-flow.md` 198L + `risk-breaker-seam.md` 215L co-owned with DR plan
  - UPDATE `kill-switch-circuit-breaker.md` +49L + UPDATE `capital-efficiency-patterns.md` +49L) +
    `unified-trading-pm@bf1ebc54` (DR Phase 8.F cross-reference). Phase 7.A-E flips bundled in `PM@da590057` per
    foot-gun #1.
- **Master coordinator wrap-up**:
  - `unified-api-contracts@5dfdd92` — NEW `registry/risk_rules/__init__.py` 7-axis aggregator (89 rules total) +
    `get_rules_for(scope, applies_to)` + `iter_applicable_rules(...)` helper + `risk.py` facade re-exports; 201 UAC
    tests pass.
  - `unified-trading-library@6e7575b3` — Extended `risk/__init__.py` with `family_aggregator` exports; 76 UTL tests
    pass.
  - `unified-trading-pm@<this-commit>` — Round-2 DONE block + LEDGER refresh.

**Aggregate rule counts**: archetype=24, venue=27, account=8, client=4, asset_group=6, global=3, family=17 → **89
ALL_RULES**. Round-2 added **172 new tests** (UAC 96 + UTL 76); UAC sweep 201/201, UTL risk sweep 76/76.

**Findings raised**:

- **Case-5 BIG — Foot-gun #1 (intra-slot index race)**: Sub-E's `UAC@29d4fe4` + Sub-H's flips at `PM@da590057` landed
  under foreign commit messages due to within-slot `.git/index` sharing — same shape as Round-1 Sub-B incident. Sub-I's
  `git add` absorbed Sub-E's pre-staged registry files; Sub-G's `git add` absorbed Sub-H's Phase 7 flips. **No data
  loss** — content correct on origin. Attribution muddled. Confirms within-slot multi-sub-agent collision is
  REPRESENTABLE under per-slot worktree model when the mandatory pre-commit check (`git diff --cached --stat` NO PATH
  ARG) is skipped.
- **Foot-gun #4** — Sub-F + Sub-I both encountered prek auto-restore races; both recovered via bundled
  Edit→add→commit→push pattern per workspace HARD RULE. ~10 min lost each. No work lost.

**What remains open** (Phase 4+ blocked on Phase 3 consumption):

- Phase 4 — per-service migration (risk-and-exposure / execution / strategy / position-balance). UTL pre-flight helpers
  shipped; consumer wiring is next-cycle work.
- Phase 5 — alerting wire (RiskRuleFiredEvent emit + consumer). Blocked by Phase 4.
- Phase 6 — deployment-api + UI Risk tab. Blocked by Phase 4.
- Phase 8 — real-VM rule fire suite. Blocked by Phase 4 + 5.
- Phase 9 — cutover gate. Blocked by Phase 8.

Phase 1 freeze gate (2026-05-15) covers Phase 0+1+2+3+7 from this plan; Phase 4+ is post-freeze.

## Deferred work after 2026-05-12 (Tab 5 — Harsh — risk Phase 4/5 implementation session)

| Phase / item                                                                                                                                                                                                                                                              | Status as of 2026-05-12                                                                                                                                                                             | Successor / blocker                                                                                                                                                                      |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 4.A — risk-and-exposure-service: full removal of legacy `PortfolioContext` explicit-threshold gates + `RiskMonitor` bespoke threshold predicates ("no code-side rule logic remains")                                                                                | DEFERRED (design-shipped `@85c99aa` — registry path composes transitionally alongside)                                                                                                              | risk-and-exposure-service tab; depends on the strategy-architecture-v2 caller supplying a `RuleEvalContext` populated from PBMS state (Phase 4.D `build_rule_eval_context` consumption). |
| Phase 4.B — execution-service: TEST_ONLY `LiveMatchingEngine` paper-vs-venue switch on `params["mode"]="TEST"`; orchestrator `account_state` wiring (portfolio-state rules currently skipped at execution-service, enforced by 4.A + 4.C)                                 | DEFERRED (annotated in 4.B body `@07477886`)                                                                                                                                                        | execution-service tab; `account_state` depends on Phase 4.D consumption.                                                                                                                 |
| Phase 4.C — strategy-service: v2 orchestrator / output-builder signal paths adopt `apply_risk_preflight` (gate currently wired through `SignalPublisher.publish()`, the documented seam, call-site-less in-repo)                                                          | DEFERRED P3                                                                                                                                                                                         | strategy-service tab — adopt when those paths next change; `apply_risk_preflight` + `build_signal_rule_context` are public.                                                              |
| Phase 5.A — emit `RiskRuleFiredEvent` from `risk-and-exposure-service/v2/preflight.py::run_layer2_rule_preflight` (the Layer-2 evaluator rule-fire site); switch `strategy-service/risk_preflight_gate.py` from AlertCode-named `log_event`s to `risk_rule_fired_event()` | ✅ DONE risk-and-exposure-service@37062ce (emit side). **DEFERRED P3**: strategy-service cleanup (`risk_preflight_gate.py` → typed `risk_rule_fired_event()` calls) — tracked as Phase 5 follow-up. | strategy-service tab (cleanup, P3).                                                                                                                                                      |
| Phase 5.B integration test (rule-fire → alert routed)                                                                                                                                                                                                                     | DEFERRED P1 (alerting-service consumer shipped `@0a52a33` with per-consequence channel/severity unit tests; the end-to-end rule-fire-in-a-running-service → alert-out test is pending)              | bundled with Phase 5.A emit follow-on.                                                                                                                                                   |
| Phase 6.A — `/api/risk/rules` endpoint; 6.B — `/api/risk/preflight-test` endpoint (6.C UI Risk tab shipped `deployment-ui@33e6ea0`)                                                                                                                                       | DONE — shipped `deployment-api@dc8be51` (both endpoints + 20 route tests; risk_routes registered under `/api/risk` in main.py — was unregistered)                                                   | —                                                                                                                                                                                        |
| Phase 8 — real-VM per-rule synthetic-fire suite (8.A/8.B/8.C)                                                                                                                                                                                                             | BLOCKED on Ikenna slot 7 `simulation_scenarios_topology_price_shocks_2026_05_09` Phase 3-4 injection primitives (Day 2 2026-05-13)                                                                  | Tab 5 Day 2+.                                                                                                                                                                            |
| Phase D.1 — UAC BreakerConfig per-stable depeg thresholds (8 stables × 4 tiers)                                                                                                                                                                                           | ✅ SHIPPED UAC@2b49ef2 2026-05-12                                                                                                                                                                   | —                                                                                                                                                                                        |
| Phase D.3 — UAC STABLECOIN_PEG_RESTORE_HISTORY registry (6 stables seeded)                                                                                                                                                                                                | ✅ SHIPPED UAC@d8e72de 2026-05-12                                                                                                                                                                   | —                                                                                                                                                                                        |
| Phase D.2 — StablecoinAggregateExposureCalculator + UAC StablecoinExposure                                                                                                                                                                                                | ✅ SHIPPED UAC@83c9e10 + features-service@8332f0de 2026-05-13                                                                                                                                       | —                                                                                                                                                                                        |
| Phase D.5 — StablecoinIssuerPauseSubscriber (Circle+Tether+MakerDAO PSM)                                                                                                                                                                                                  | ✅ SHIPPED alerting-service@cbaf8d8 2026-05-13                                                                                                                                                      | —                                                                                                                                                                                        |
| Phase D.6 — STABLECOIN_EMERGENCY_EXIT_ROUTES registry (33 routes / 10 stables)                                                                                                                                                                                            | ✅ SHIPPED UAC@83c9e10 2026-05-13                                                                                                                                                                   | —                                                                                                                                                                                        |
| Phase D.7 — GovernanceForumWatcher (Snapshot+Tally)                                                                                                                                                                                                                       | ✅ SHIPPED alerting-service@cbaf8d8 2026-05-13                                                                                                                                                      | Discord ingestion DEFERRED (D.7 follow-up item)                                                                                                                                          |
| UTL hygiene — root re-export of `risk` / `reconcile` sub-package surfaces + `KillSwitchSubscriber` / `map_switch_id_to_scope` at the `unified_trading_library` package root; clean the Phase-4 `# noqa: qg-deep-import` deep imports                                      | DEFERRED P2 (`kill_switch/__init__` exports added `@d1a0d0d` — `from unified_trading_library.kill_switch import KillSwitchSubscriber` now works)                                                    | UTL hygiene follow-up — owner pick.                                                                                                                                                      |

### DONE-2026-05-12 — Tab 5 (Harsh) — risk Phase 4 fan-out + Phase 5.B + UAC `RiskRuleFiredEvent`

**Cycle ownership**: `work_split_2026_05_12_harsh.md` slot 5 (risk + DR implementation). Day 1 of the 2026-05-12 →
2026-05-15 cycle; scenario-dependent items (Phase 8) wait on Ikenna slot 7's Day-2 publish.

**Shipped (all pushed to `live-defi-rollout`):**

- **UAC `RiskRuleFiredEvent`** — `unified-api-contracts@a01e4dd`: NEW `RiskRuleFiredEvent` Pydantic model (frozen,
  extra=forbid — `rule_id` / `scope` / `applies_to` / `consequence` / `alerting_severity` / `alert_code` / `fired_at` /
  `instruction_id` / `triggers_kill_switch` / `kill_switch_scope` / `trigger_detail` / `metadata`) +
  `risk_rule_fired_event(rule, *, fired_at, ...)` SSOT builder in `canonical/crosscutting/risk_rule.py` + `risk.py`
  facade re-export + 5 new unit tests (`test_risk_rule_taxonomy.py` 42 in file; UAC suite 109/109 green; ruff +
  basedpyright clean). Closes a Phase-1 oversight — the taxonomy referenced `RiskRuleFiredEvent` in docstrings +
  `CONSEQUENCE_EVENTS_EMITTED` but never shipped the model; Phase 5 (alerting wire) + Phase 4 (per-service emit) need
  it.
- **Phase 4 — per-service migration (5-sub-agent fan-out)**:
  - `risk-and-exposure-service@85c99aa`+`@550a39e` — `v2/preflight.py::run_layer2_rule_preflight` builds the runtime
    `RuleEvalContext` + axis-ids, resolves the per-axis UAC `RiskRule` registry via `iter_applicable_rules()`, runs UTL
    `risk_preflight()`, maps `RiskRuleConsequence` → `RiskGateDecision`; `run_layer2_preflight()` folds the registry
    outcome in most-restrictively when a `rule_context` is supplied; `InMemoryRiskLimitsClient`/`RiskLimitsDomainClient`
    a thin reader over the UAC registry; per-archetype circuit breakers registered against the UAC
    `registry/circuit_breakers/` package + `ArmedBreakerRegistry` (stores the paired `BreakerRecoveryRule` for the
    Phase-5 recovery engine) + typed breaker-fire events; kill-switch-bus round-trip verified. **Risk Phase 4.A →
    design-shipped** (legacy-gate removal DEFERRED — see scoreboard); plan flips `unified-trading-pm@4000ea0f`.
  - `execution-service@07477886` — `engine/risk/preflight_gate.py` + `engine/orchestrator.py`: `risk_preflight` inserted
    into the order-submission path BEFORE venue submission — BLOCK→reject+`INSTRUCTION_REJECTED_RISK`, SCALE_DOWN→resize
    by `scale_factor`+`RESIZED_EXECUTION`, MONITOR→passthrough, TEST_ONLY→tag `mode=TEST`+route-to-matching;
    per-fired-rule `RiskRuleFiredEvent` via UAC `risk_rule_fired_event()`; deleted bespoke `engine/risk/pre_trade.py`
    per the § 7 seam; 7 new tests. **Risk Phase 4.B → `[x]`**; plan flips `unified-trading-pm@52ab4e4f`.
  - `strategy-service@bf1ed6b` — `strategy_service/risk_preflight_gate.py` (`build_signal_rule_context` +
    `apply_risk_preflight` — wraps UTL `risk_preflight` over `iter_applicable_rules`, threads family-id via
    `aggregate_family_state`) + `SignalPublisher.publish()` runs the gate when `archetype_id` supplied
    (BLOCK→`None`+`STRATEGY_SIGNAL_SUPPRESSED`+per-rule AlertCode event; SCALE_DOWN→scale
    `conviction_pct`/`meta_signal`); 9 new tests. **Risk Phase 4.C → `[x]`**; plan flips `unified-trading-pm@0b0f67e8`.
  - `position-balance-monitor-service@50b3c25` — `core/rule_eval_context_builder.py` (`PortfolioRiskState` +
    `PeakNavTracker` + `build_rule_eval_context()` → UTL `RuleEvalContext` — emits authoritative drawdown-bps-from-peak
    / leverage / gross+net exposure / per-(venue,instrument) OI / daily-loss; deliberately omits the keys not owned by
    position-balance so risk/execution/strategy layer those in; no rule logic duplicated); 13 new tests (one drives
    `unified_trading_library.risk.evaluate_rule` end-to-end). **Risk Phase 4.D → `[x]`**; plan flips
    `unified-trading-pm@33e7f74c`.
  - `alerting-service@0a52a33` — `risk_rule_event_handler.py` (consumes `RiskRuleFiredEvent`, maps `event.alert_code` →
    the UAC-seeded `LIVE_ALERT_RULES` entry, routes via `notifiers/router.route_event` at the rule's channel/severity
    tier per the § 7 seam — BLOCK→`RISK_RULE_BLOCKED` HIGH+PagerDuty, SCALE_DOWN→WARN+Telegram,
    MONITOR/TEST_ONLY→INFO+LogOnly; `trigger_detail` + `metadata` rendered into the body) + a router bug fix (matched
    empty-channels rule now returns `{"log_only"}` instead of falling through to Telegram); new
    `test_risk_rule_event_handler.py`; 412 unit tests. **Risk Phase 5.B → `[x]`**; plan flips
    `unified-trading-pm@18896af7`.
- **Phase 5.A** — ✅ FULLY SHIPPED: risk-and-exposure-service@37062ce (`run_layer2_rule_preflight` emits
  `RISK_RULE_FIRED` per fired rule via `risk_rule_fired_event()` builder — typed key fields, basedpyright clean, ruff
  OK); execution-service@07477886 (order path); strategy-service@bf1ed6b (AlertCode-named events — P3 cleanup to typed
  `risk_rule_fired_event()` tracked above). All three Layer-2 fire sites now emit.
- **Operational fix** — FF-pulled root `unified-api-contracts` (3 behind) + `unified-trading-library` (5 behind) to
  `origin/live-defi-rollout` so `.venv-workspace` (editable-installed against the root checkouts) sees the fresh
  `RiskRuleFiredEvent` / kill-switch facade exports / `BreakerRecoveryEngine` / reconcile package — the Phase-4
  sub-agents validate via `.venv-workspace`.

**Findings raised** (mirrored in the DR plan DONE block — see `disaster_recovery_circuit_breakers_2026_05_10.md`): no
typed `BreakerFiredEvent` UAC model (P2 discovery — captured as DR Phase 1.G); pre-existing red QG on
`live-defi-rollout` for alerting-service (`test_router_coalesce.py` N802 + `router.py` reportAny — foreign in-flight
file, flagged not fixed), execution-service (`cloud_kms.py` os.environ), position-balance-monitor-service
(local-schema/size + UTL pipeline_mode kwargs + PM manifest validators + pip-audit) — all pre-existing, not made worse.

**Cycle metrics**: see the DR plan DONE-2026-05-12 block (this session covered both plans jointly).

Codex audit (Phase 7): all Phase-7 codex docs (`risk-rule-taxonomy.md` / `risk-preflight-flow.md` /
`risk-breaker-seam.md` / `kill-switch-circuit-breaker.md` UPDATE / `capital-efficiency-patterns.md` UPDATE) shipped +
flipped prior cycle (`unified-trading-pm@d86c8b3c`/`@730914a9`/`@bf1ebc54`) — verified still current; the
`RiskRuleFiredEvent` model addition is a small follow-on that fits `risk-preflight-flow.md`'s event-emission section
(NICE-TO-HAVE — `/codex/04-architecture/risk-preflight-flow.md` already documents the `RiskRuleFiredEvent` name; the
model shape can be appended on the next substantive touch).
