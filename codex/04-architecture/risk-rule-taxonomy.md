---
doc_type: codex-ssot
title: Risk Rule Taxonomy
summary:
  The closed-set UAC vocabulary for every Layer-2 pre-flight risk decision — RiskRule = RiskRuleId (28 members) ×
  RiskRuleScope (7 axes) × RiskRuleTrigger (13 typed subtypes) × RiskRuleConsequence (BLOCK / SCALE_DOWN / MONITOR /
  TEST_ONLY); rules live in a UAC registry (never inline in service code), consumed via risk_preflight(); includes the
  RiskRuleConsequence × 5-canonical-SSOT event-emission cross-product (§7 seam diagram).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [risk, execution, strategy, uac, kill-switch]
related:
  [
    /codex/04-architecture/risk-preflight-flow.md,
    /codex/04-architecture/risk-breaker-seam.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: 2026-05-11
authoritative_for: [RiskRule taxonomy (RiskRuleId/Scope/Trigger/Consequence closed enums)]
referenced_by:
  [
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/04-architecture/circuit-breaker-rule-taxonomy.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/risk-breaker-seam.md,
    /codex/04-architecture/risk-preflight-flow.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Risk Rule Taxonomy

> **What it is:** The closed-set vocabulary that describes every pre-flight risk decision in the system. `RiskRule` is
> the single UAC SSOT for "what does the risk-and-exposure-service check before an instruction reaches a venue"; it
> combines an identifier (`RiskRuleId`), a scope axis (`RiskRuleScope`), a typed trigger condition (`RiskRuleTrigger`),
> and a consequence (`RiskRuleConsequence`). Every rule fire emits a `RiskRuleFiredEvent` that routes through the
> alerting taxonomy. Composes with — does not replace — the 5 canonical risk SSOTs (4-layer risk gates, kill-switch,
> circuit-breaker, autonomous-recovery ErrorAction, AlertCode).

## TL;DR

`RiskRule` lives at **Layer 2** of the
[4-layer risk-gates model](/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md) — between strategy self-check
(Layer 1) and execution-service pre-trade checks (Layer 3). Each rule answers one question: _given this instruction and
current portfolio state, what should happen?_ The closed-set answer is one of `BLOCK` / `SCALE_DOWN` / `MONITOR` /
`TEST_ONLY`. Rules are declared in a UAC registry
(`registry/risk_rules/{archetype,venue, account,client,asset_group,global,strategy_family}.py`); the UTL
`risk_preflight(order, context)` helper iterates applicable rules per scope and returns the aggregate decision. No rule
logic lives in service code — services consume the registry.

## Closed enums

### `RiskRuleId` (UAC `canonical/crosscutting/risk_rule.py`)

The closed-enum identifier for every rule shape. **Twenty-eight members shipped at UAC@`risk_rule.py:53-130`** (counted
2026-05-12 per slot 8 audit R-7 PRE*CUTOVER refresh; baseline was 22 at UAC@945ad5d, plus 6 `FAMILY*\*` members added
Phase 2.H — see § "Family-aggregate rules" below). Extension closed-enum allowed for archetype-unique additions (Phase
2.A onward).

| `RiskRuleId`                           | One-line description                                                                                                                              |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MAX_POSITION_SIZE_PER_ARCHETYPE`      | Per-archetype notional ceiling. Breach → BLOCK new sizing.                                                                                        |
| `MAX_DRAWDOWN_PER_ARCHETYPE`           | Trailing peak-NAV drawdown. Tiered SCALE_DOWN → BLOCK at deeper levels.                                                                           |
| `MAX_LEVERAGE_PER_ARCHETYPE`           | Gross-notional / equity cap. Breach → BLOCK.                                                                                                      |
| `MAX_CONCENTRATION_PER_INSTRUMENT`     | Max % of archetype NAV in a single instrument. Breach → BLOCK (single-name risk).                                                                 |
| `MAX_CORRELATION_PER_ARCHETYPE`        | Pearson ρ across hedge legs. Breach → SCALE_DOWN (de-correlation incomplete).                                                                     |
| `SLIPPAGE_BUDGET_PER_ARCHETYPE`        | Cumulative bps slipped per period. Breach → BLOCK until reset.                                                                                    |
| `FUNDING_COST_CEILING_PER_ARCHETYPE`   | Funding-cost APR ceiling on borrow legs. Breach → BLOCK new sizing.                                                                               |
| `GAS_BUDGET_PER_ARCHETYPE`             | Daily on-chain gas spend ceiling. Breach → BLOCK new on-chain instructions.                                                                       |
| `CAPITAL_AT_RISK_CEILING`              | 95% VaR ceiling per archetype (oracle-depeg / liquidation-cascade scenario). Breach → BLOCK.                                                      |
| `ORACLE_STALENESS_BLOCK`               | Oracle price age > threshold → BLOCK new positions. (DeFi-specific.)                                                                              |
| `LST_TRACKING_ERROR_MONITOR`           | LST/SOL ratio Δ vs 24h-EMA → MONITOR (advisory dashboard event, no instruction effect).                                                           |
| `MAX_OI_PER_VENUE`                     | Open-interest cap per venue (avoid tape-imprint). Breach → BLOCK.                                                                                 |
| `MAX_SINGLE_INSTRUMENT_SIZE_PER_VENUE` | Per-instrument per-venue notional cap. Breach → BLOCK.                                                                                            |
| `MAX_CROSS_INSTRUMENT_SIZE_PER_VENUE`  | Aggregate per-venue notional cap across instruments. Breach → BLOCK.                                                                              |
| `MAX_GROSS_EXPOSURE`                   | Per-account gross-notional cap across all archetypes. Breach → BLOCK.                                                                             |
| `MAX_NET_EXPOSURE`                     | Per-account net-delta cap (delta-neutral invariant). Breach → BLOCK + alert (legs de-syncing).                                                    |
| `MAX_DAILY_LOSS`                       | Per-account daily P&L floor. Breach → BLOCK + engages `DAILY_LOSS_BREACH` kill-switch.                                                            |
| `PER_CLIENT_SUBSCRIPTION_SIZE`         | Per-client per-archetype subscription size ceiling. Breach → BLOCK.                                                                               |
| `PER_CLIENT_DRAWDOWN`                  | Per-client drawdown from peak NAV. Tiered SCALE_DOWN → BLOCK.                                                                                     |
| `FAMILY_GROSS_EXPOSURE_CAP`            | Strategy-family aggregate gross-notional cap (e.g. all LST-leverage archetypes combined). Breach → BLOCK.                                         |
| `FAMILY_CORRELATION_WITH_OTHER_FAMILY` | Cross-family correlation surveillance (e.g. LST + funding-arb both share Solana oracle risk). Breach → MONITOR → SCALE_DOWN at higher thresholds. |
| `GLOBAL_KILL_CONDITION`                | Workspace-wide kill condition (regulatory halt, exchange outage cascade). Breach → BLOCK firmwide + engages `KILL_ALL_LIVE`.                      |

Extension axis: archetype-unique rules (e.g. LST validator-set concentration for `carry_staked_basis`) extend the enum
via the closed-enum extension pattern in Phase 2.A, not by wildcard `Any`.

### `RiskRuleScope` (UAC `canonical/crosscutting/risk_rule.py`)

The closed-set axis on which a rule applies. **Seven axes** (slot 8 audit R-8 PRE_CUTOVER refresh 2026-05-12 — was 6 at
original ship, `PER_STRATEGY_FAMILY` added Phase 2.H for family-aggregate caps); every rule declares exactly one scope.

| Scope                 | Applies when …                                                                                                                                                  |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PER_ARCHETYPE`       | Rule is keyed by `ArchetypeId` (`carry_staked_basis`, `ARBITRAGE_PRICE_DISPERSION`, etc.).                                                                      |
| `PER_VENUE`           | Rule is keyed by venue (Binance, Aave, Polymarket, ...). Caps per-venue concentration / OI / size.                                                              |
| `PER_ACCOUNT`         | Rule is keyed by trading account (Bybit-live-account-1, paper-account-2). Caps exposure / loss / margin.                                                        |
| `PER_ASSET_GROUP`     | Rule is keyed by asset_group (cefi / defi / tradfi / sports / prediction). Caps domain-level concentration.                                                     |
| `PER_CLIENT`          | Rule is keyed by client_id. Caps per-subscription size / drawdown / withdrawal pressure.                                                                        |
| `PER_STRATEGY_FAMILY` | Rule is keyed by strategy family (e.g. LST-leverage family, funding-arb family). Caps family-aggregate exposure / correlation surveillance. Phase 2.H addition. |
| `GLOBAL`              | Workspace-wide kill conditions. Single instance per rule_id.                                                                                                    |

The `RiskRule.kill_switch_scope()` method maps scopes to `KillSwitchScope` per the seam-diagram orthogonality
declaration (`PER_VENUE → VENUE`, `PER_ARCHETYPE → ARCHETYPE`, `PER_CLIENT → CLIENT`, `GLOBAL → GLOBAL`; `PER_ACCOUNT`
and `PER_ASSET_GROUP` return None — they engage no kill-switch directly).

### `RiskRuleConsequence` (UAC `canonical/crosscutting/risk_rule.py`)

The closed-set decision a rule's evaluator returns. Four values; each maps to a deterministic set of downstream events.

| Consequence  | Semantics                                                                                                                                             | Event(s) emitted                                                                                                          |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `BLOCK`      | Instruction rejected at Layer 2; never reaches venue.                                                                                                 | `INSTRUCTION_REJECTED_RISK` + `RiskRuleFiredEvent` (sev HIGH or CRITICAL) + `RISK_RULE_BLOCKED` AlertCode                 |
| `SCALE_DOWN` | Instruction approved at reduced size. The rule's `scale_factor` is min-aggregated against every other SCALE_DOWN consequence on the same instruction. | `INSTRUCTION_ACCEPTED_PREFLIGHT` (with `size_adjusted: true`) + `RESIZED_EXECUTION` at Layer 3 + `RISK_RULE_SCALED_DOWN`  |
| `MONITOR`    | Instruction approved unchanged; rule fire is advisory (dashboard event).                                                                              | `INSTRUCTION_ACCEPTED_PREFLIGHT` + `RiskRuleFiredEvent` (sev INFO or WARN) + `RISK_RULE_MONITOR_FIRED`                    |
| `TEST_ONLY`  | Instruction route-diverted to matching engine instead of live venue; live fill simulated.                                                             | `INSTRUCTION_ACCEPTED_PREFLIGHT` (with `mode=TEST`) → `ORDER_SUBMITTED` to matching engine + `RISK_RULE_TEST_ONLY_ROUTED` |

The full event-emission cross-product is codified in the [§ 7 SSOT seam diagram](#§-7-ssot-seam-diagram-verbatim) below
and at the
[risk plan body](../../plans/archive/risk_simulations_limits_alerting_2026_05_10.md#-7-ssot-reconciliation-seam-framing-1--picked-2026-05-10);
reviewers must reject changes that drift the two.

### `RiskRuleTrigger` (UAC `canonical/crosscutting/risk_rule.py`)

Closed-union over typed trigger conditions. Each subtype carries the field set required to evaluate the trigger. The
Pydantic discriminator is `trigger_type: Literal["..."]`. Thirteen subtypes shipped at UAC@945ad5d.

| `trigger_type` literal     | Required fields                                                                                   | Threshold semantics                                                                                             |
| -------------------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `max_position_size`        | `max_notional_usd: Decimal`                                                                       | Instruction + current_position_notional > max → fire.                                                           |
| `max_drawdown`             | `max_drawdown_bps: int`, `tier_thresholds: dict[int, RiskRuleConsequence]`                        | Trailing peak-NAV drawdown ≥ threshold → tier-mapped consequence (e.g. 500 bps → SCALE_DOWN, 1000 bps → BLOCK). |
| `max_leverage`             | `max_leverage_ratio: Decimal`                                                                     | Gross-notional / equity > ratio → fire.                                                                         |
| `max_concentration`        | `max_pct_of_nav: Decimal`, `aggregation_key: Literal["instrument", "venue", "chain"]`             | Concentration in keyed axis > pct → fire.                                                                       |
| `max_correlation`          | `max_pearson_rho: Decimal`, `pair_axis: Literal["hedge_legs", "cross_archetype", "cross_family"]` | ρ of returns over rolling window > threshold → fire.                                                            |
| `slippage_budget_exceeded` | `budget_bps_per_period: int`, `period: Literal["per_swap", "daily", "rolling_24h"]`               | Cumulative slipped bps in period > budget → fire.                                                               |
| `funding_cost_ceiling`     | `max_apr: Decimal`                                                                                | Funding APR on borrow leg > ceiling → fire.                                                                     |
| `gas_budget_exceeded`      | `max_gas_usd_per_period: Decimal`, `period: Literal["per_tx", "daily"]`                           | Gas spend in period > budget → fire.                                                                            |
| `capital_at_risk_ceiling`  | `max_var_usd: Decimal`, `confidence: Decimal`, `scenario_id: str`                                 | 95% VaR under named scenario > ceiling → fire.                                                                  |
| `max_oi`                   | `max_pct_of_24h_volume: Decimal`                                                                  | Open-interest at venue > pct of 24h volume → fire.                                                              |
| `max_gross_exposure`       | `max_gross_usd: Decimal`                                                                          | Sum of \|notional\| across archetypes/account > max → fire.                                                     |
| `max_daily_loss`           | `max_loss_usd: Decimal`, `triggers_kill_switch: bool = True`                                      | Realized + unrealized loss today > max → fire.                                                                  |
| `oracle_staleness`         | `max_age_seconds: int`, `oracle_source: Literal["pyth_hermes", "chainlink", "pyth_solana", ...]`  | Oracle price age > threshold → fire.                                                                            |

Adding a new trigger requires a UAC PR. Adding archetype-unique rules within an existing trigger family is a Phase 2.A
registry-only change (no new trigger type needed).

## Anti-patterns

- **Don't define rules outside the registry.** Any inline rule in service code is a drift hazard. Migrate to
  `registry/risk_rules/...` and consume via `risk_preflight()`.
- **Don't add new trigger types without a UAC PR.** The closed-union is the contract; widening it via `Any` /
  `dict[str, Any]` defeats Pydantic discrimination + the preflight evaluator.
- **Don't shadow `AlertCode` members.** Each new rule*id MUST map to one of the existing closed-set codes
  (`RISK_RULE*\*` family added at UAC@945ad5d) or extend the closed set via a co-coordinated UAC+alerting PR.
- **Don't conflate `RiskRuleConsequence.SCALE_DOWN` with `BreakerAction.SCALE_DOWN`.** They live at different layers
  (Layer 2 risk vs Layer 3 breaker) by design. See [risk-breaker-seam.md](risk-breaker-seam.md) for the escalation
  contract.
- **Don't evaluate rules at strategy-service Layer 1.** Layer 1 is local self-check; cross-strategy / cross-account
  rules live at Layer 2. Strategy-service queries `risk_preflight()` BEFORE sizing, but does not own the rule evaluator.
- **Don't cache `risk_preflight()` results.** Portfolio state changes per-tick — every order goes through fresh
  evaluation.

## § 7 SSOT seam diagram (verbatim)

The `RiskRuleConsequence` × 5-canonical-SSOT cross-product table is mirrored from
[`risk_simulations_limits_alerting_2026_05_10.md` § "§ 7 SSOT reconciliation seam (Framing 1)"](../../plans/archive/risk_simulations_limits_alerting_2026_05_10.md#-7-ssot-reconciliation-seam-framing-1--picked-2026-05-10).
Reviewers reject any PR that drifts this table from the plan-body source-of-truth.

| Consequence  | Risk-gates Layer       | Event(s) emitted                                                                                       | Composes with kill-switch trigger (5-set per [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md))                                       | Composes with circuit-breaker action (3-set per [`alerting_service_live_rules`](../../plans/active/alerting_service_live_rules_2026_05_07.md))                                                                                                                                                      | Composes with strategy kill-switch behaviour (4-set)                                                                                                                 | AlertCode mapping (UAC@d00326d)                                                            |
| ------------ | ---------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `BLOCK`      | Layer 2                | `INSTRUCTION_REJECTED_RISK` + `RiskRuleFiredEvent` (sev: HIGH/CRITICAL)                                | If `triggers_kill_switch: true` AND per-rule threshold count met → engages `DAILY_LOSS_BREACH` / `MAX_DRAWDOWN_BREACH` / `DATA_STALE` per trigger type | Aggregated BLOCK rate ≥ 60% across N instructions → execution-service breaker may transition CLOSED→DEGRADED→OPEN per per-venue failure-rate threshold; emits `stop_new_signals` / `force_exit_only` / `halt_strategy` cascade per [`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md) | If kill-switch engaged: `STOP_NEW_ONLY` (default) / `FAST_UNWIND` (MAX_DRAWDOWN_BREACH) / `SLOW_UNWIND` (operator override) / `DELTA_HEDGE` (cross-venue still open) | `PREFLIGHT_FAILED` (generic) or `RISK_RULE_BLOCKED` (per-rule granular, added UAC@945ad5d) |
| `SCALE_DOWN` | Layer 2 → Layer 3      | `INSTRUCTION_ACCEPTED_PREFLIGHT` (with `size_adjusted: true`) → `RESIZED_EXECUTION` + sev: WARN        | Does NOT trigger kill-switch (sized-down instruction proceeds; no breach)                                                                              | Does NOT trigger breaker (instruction approved, just smaller)                                                                                                                                                                                                                                       | Strategy continues normally with reduced size                                                                                                                        | `RISK_RULE_SCALED_DOWN` (UAC@945ad5d)                                                      |
| `MONITOR`    | Layer 2 (passthrough)  | `INSTRUCTION_ACCEPTED_PREFLIGHT` + `RiskRuleFiredEvent` (sev: INFO/WARN)                               | Does NOT trigger kill-switch                                                                                                                           | Does NOT trigger breaker                                                                                                                                                                                                                                                                            | Strategy continues normally                                                                                                                                          | `RISK_RULE_MONITOR_FIRED` (UAC@945ad5d)                                                    |
| `TEST_ONLY`  | Layer 2 (route-divert) | `INSTRUCTION_ACCEPTED_PREFLIGHT` (with `mode=TEST`) → `ORDER_SUBMITTED` to matching engine + sev: INFO | Does NOT trigger kill-switch                                                                                                                           | Does NOT trigger breaker (no live venue contact)                                                                                                                                                                                                                                                    | Strategy continues; fills are simulated                                                                                                                              | `RISK_RULE_TEST_ONLY_ROUTED` (UAC@945ad5d)                                                 |

### Orthogonality declarations

- **vs ErrorAction taxonomy** (per [`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md)):
  `RiskRuleConsequence` is a **pre-flight decision at Layer 2**; ErrorAction is a **post-venue-error classification at
  Layer 4**. They don't overlap; both can apply to the same instruction lifecycle: Layer 2 BLOCK → no venue contact, no
  ErrorAction; Layer 2 non-BLOCK → venue may reject → ErrorAction fires + may transition the breaker.
- **vs `RiskRuleScope` × `KillSwitchScope`**: `RiskRuleScope` is the rule-applicability axis; `KillSwitchScope` is the
  kill-switch blast-radius axis. Mapping in `RiskRule.kill_switch_scope()`.
- **vs `AlertCode` SSOT**: every `RiskRuleFiredEvent` cites an `AlertCode` from the closed set (UAC@d00326d →
  UAC@945ad5d growth: 39 → 45 with `RISK_RULE_*` + `KILL_SWITCH_AUTO_RECOVERED` + `KILL_SWITCH_MANUAL_UNKILLED`).
  Severity routing per `LIVE_ALERT_RULES` (UAC@c96447b).

## Cross-references

- Pre-flight flow (every-order path): [risk-preflight-flow.md](risk-preflight-flow.md)
- Risk-breaker escalation seam (distinct enums, coupled by event): [risk-breaker-seam.md](risk-breaker-seam.md)
- Kill switch + circuit breaker mechanics: [kill-switch-circuit-breaker.md](kill-switch-circuit-breaker.md)
- Capital-at-risk ceiling composition: [capital-efficiency-patterns.md](capital-efficiency-patterns.md)
- 4-layer risk-gates model (Layer 1-4 separation):
  [/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md](/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md)
- Autonomous recovery (Layer 4 ErrorAction): [autonomous-recovery-matrix.md](autonomous-recovery-matrix.md)
- Plan-of-record:
  [plans/active/risk_simulations_limits_alerting_2026_05_10.md](../../plans/archive/risk_simulations_limits_alerting_2026_05_10.md)
- Alerting-service rule registry:
  [plans/active/alerting_service_live_rules_2026_05_07.md](../../plans/active/alerting_service_live_rules_2026_05_07.md)
