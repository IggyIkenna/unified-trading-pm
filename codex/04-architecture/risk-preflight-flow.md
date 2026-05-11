---
scope: [engineer, admin]
---

# Risk Pre-Flight Flow

> **What it is:** The order-submission path that every instruction takes from strategy emission to venue submission.
> The UTL helper `risk_preflight(order, context) -> RiskPreflightResult` is the single integration point — every order
> goes through it BEFORE reaching execution-service. Returns one aggregate decision: pass / scale-down (with
> min-aggregated factor) / block (with reason set) / test-only (with route-divert annotation). Companion to
> [`risk-rule-taxonomy.md`](risk-rule-taxonomy.md).

## TL;DR

`risk_preflight()` lives at **Layer 2** of the [4-layer risk-gates model](../09-strategy/architecture-v2/cross-cutting/risk-gates.md).
Strategy-service calls it BEFORE sizing the order; execution-service calls it BEFORE submitting to the venue. (Both
calls happen — defense in depth — but strategy-side caching is forbidden because portfolio state changes per tick.) The
helper iterates every `RiskRule` whose scope matches `(archetype_id, venue, account_id, asset_group, client_id)` from
the registry, evaluates each via `evaluate_rule(rule, context)`, and aggregates the per-rule consequences into a single
`RiskPreflightResult`. Block aggregates as "any BLOCK wins"; scale-down aggregates as "min of all scale_factors";
monitor and test-only are passthrough annotations.

## Flow diagram

```
┌────────────────────────────────────────────────────────────────┐
│  STRATEGY GENERATOR                                             │
│  - Produces target position delta + signal direction            │
│  - Calls risk_preflight(intended_order, ctx) BEFORE sizing      │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│  Layer 1 — STRATEGY SELF-CHECK (intra-service)                  │
│  Local checks; cheap; catches bugs early.                       │
│  Fails → drop instruction, emit REJECTED_SELF_CHECK.            │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│  Layer 2 — RISK PRE-FLIGHT (risk-and-exposure-service)          │
│  risk_preflight(order, context) →                               │
│    for rule in applicable_rules(scope_axes):                    │
│        result = evaluate_rule(rule, context)                    │
│    aggregate(results) → RiskPreflightResult                     │
└────────────────────────────────────────────────────────────────┘
                          │
              ┌───────────┼───────────┬───────────┐
              ▼           ▼           ▼           ▼
           BLOCK     SCALE_DOWN    MONITOR    TEST_ONLY
              │           │           │           │
              ▼           ▼           ▼           ▼
        INSTRUCTION_  RESIZED     instruction   route-divert
        REJECTED_     EXECUTION   passes        to matching
        RISK          (scale_     unchanged     engine (no
        (alert+halt)  factor=min) + advisory    live venue)
              │           │           │           │
              ▼           ▼           ▼           ▼
           — END —    Layer 3     Layer 3     matching engine
                      execution   execution   simulated fill
                      pre-trade   pre-trade
                          │           │
                          ▼           ▼
                      Layer 4 — VENUE-SIDE RISK
                      (external; venue may reject)
                          │
                          ▼
                      ORDER_FILLED / ORDER_REJECTED_VENUE
                      (Layer 4 → ErrorAction classification)
```

## Aggregation semantics

`risk_preflight()` returns a single `RiskPreflightResult`:

```python
@dataclass(frozen=True)
class RiskPreflightResult:
    decision: Literal["pass", "scale_down", "block", "test_only"]
    scale_factor: Decimal | None  # None unless decision == "scale_down"; else min of all SCALE_DOWN fires
    blocked_by: list[RiskRuleFiredEvent]  # non-empty iff decision == "block"
    scaled_by: list[RiskRuleFiredEvent]  # SCALE_DOWN fires that contributed to scale_factor
    monitored: list[RiskRuleFiredEvent]  # passthrough advisory fires (decision unchanged)
    test_only_routed_by: RiskRuleFiredEvent | None  # at most one rule can route to TEST mode
    decision_layer: Literal["LAYER_2"]
```

### `BLOCK` semantics

Any `BLOCK` rule fire causes `decision = "block"`. ALL blocking rules are surfaced in `blocked_by` (not just the first
one) — operator dashboards show every reason simultaneously. The instruction never reaches Layer 3. Emits
`INSTRUCTION_REJECTED_RISK` + one `RiskRuleFiredEvent` per blocking rule + per-rule `RISK_RULE_BLOCKED` AlertCode (or
generic `PREFLIGHT_FAILED` if the rule predates the per-rule code addition).

Aggregation of multiple blocks:

- All block reasons surfaced (no first-wins).
- Severity = `max(rule.alerting_severity for rule in blocked_by)`.
- Kill-switch engagement: if any `blocked_by` rule has `triggers_kill_switch: true` AND per-rule threshold count met,
  the corresponding kill-switch trigger fires per the cross-product table in [risk-rule-taxonomy.md](risk-rule-taxonomy.md).

### `SCALE_DOWN` semantics

Multiple `SCALE_DOWN` rules can fire on the same instruction. Aggregation is **min of all scale_factors** — the
most-restrictive rule wins.

```python
# Three rules fire on the same instruction:
# rule_A: scale_factor = 0.80 (concentration cap suggests 20% reduction)
# rule_B: scale_factor = 0.50 (correlation cap suggests 50% reduction)
# rule_C: scale_factor = 0.90 (slippage budget suggests 10% reduction)
# Aggregate: 0.50 — rule_B wins.
```

Order size = `intended_size × aggregate_scale_factor`. Emits `INSTRUCTION_ACCEPTED_PREFLIGHT` with `size_adjusted: true`
annotation + one `RiskRuleFiredEvent` per SCALE_DOWN rule + `RISK_RULE_SCALED_DOWN` AlertCode per rule + Layer 3 emits
`RESIZED_EXECUTION` on actual venue submission.

A `BLOCK` rule firing alongside any number of `SCALE_DOWN` rules always wins (decision = "block"; scale_factor
discarded).

### `MONITOR` semantics

Passthrough decision; instruction is approved unchanged. Each MONITOR rule fire emits `RiskRuleFiredEvent` with the
declared severity (INFO or WARN) and `RISK_RULE_MONITOR_FIRED` AlertCode. Operator dashboards aggregate MONITOR events
for trend visibility; no instruction-level effect.

MONITOR can coexist with any other decision — multiple MONITOR fires alongside a BLOCK, SCALE_DOWN, or pure pass are
fine. All MONITOR events surfaced via `monitored` list.

### `TEST_ONLY` semantics

At most one rule can route an instruction to TEST_ONLY mode (the registry enforces uniqueness — multiple TEST_ONLY
rules on the same instruction is a registry-validation error caught at UAC PR time). When a TEST_ONLY rule fires,
`decision = "test_only"`, the instruction is tagged `mode=TEST`, and Layer 3 routes it to the matching engine instead
of the live venue. Fills are simulated — no real venue contact, no real capital movement.

Use cases: shadow-trading a new archetype against a paper account before live; A/B testing two model versions in
parallel without risking capital on the challenger; smoke-testing a venue integration end-to-end with synthetic fills.

A TEST_ONLY route is incompatible with BLOCK (block wins; TEST_ONLY discarded) but composable with SCALE_DOWN (the
TEST-routed instruction is sized down before going to the matching engine) and MONITOR (advisory events still emit on
the TEST-routed instruction).

## Integration points

### Strategy-service call site

Strategy-service queries `risk_preflight()` BEFORE sizing the order. If the result is `block`, the strategy drops the
intended order and emits `INSTRUCTION_REJECTED_RISK`. If `scale_down`, the strategy sizes the order at `intended_size ×
scale_factor` and continues. If `monitor` or `test_only`, the strategy proceeds normally; downstream side-effects
(route divert, advisory events) are handled by the helper + Layer 3 wiring.

### Execution-service call site

Execution-service ALSO calls `risk_preflight()` immediately before venue submission (defense in depth — portfolio state
may have changed between strategy sizing and execution submission, and a different agent's instruction may have
breached the same scope). This is the authoritative check; strategy-side caching is forbidden. If the second
preflight returns `block`, execution-service emits `INSTRUCTION_REJECTED_RISK` from its own service and the order never
reaches the venue.

### Kill-switch bus integration

`BLOCK` aggregates with `triggers_kill_switch: true` may engage the kill-switch bus. The engagement is one-directional:
risk preflight emits the trigger event (e.g. `MAX_DRAWDOWN_BREACH` per `RiskRuleTrigger` type); the kill-switch state
machine in execution-service consumes the event and transitions per its own rules — see
[`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md). `SCALE_DOWN`, `MONITOR`, and `TEST_ONLY` consequences
do not engage kill-switch.

For the related (but distinct) **risk-rule-fire → breaker-arm escalation seam**, see
[`risk-breaker-seam.md`](risk-breaker-seam.md). The seam fires only on N-consecutive-SCALE_DOWN-in-window-W aggregates,
not on individual SCALE_DOWN events.

## Anti-patterns

- **Don't skip preflight for "fast path" orders.** Every order goes through preflight — no exceptions. Aggregated rate
  is a few µs per rule; an entire preflight pass is sub-millisecond even with 30+ applicable rules.
- **Don't cache `RiskPreflightResult`.** Portfolio state changes per tick. A cached result is stale within
  milliseconds for actively-traded instruments. Re-evaluate per order.
- **Don't combine `SCALE_DOWN` factors as a product.** Min-aggregation is correct (most-restrictive wins); product
  aggregation would over-shrink instructions when many advisory rules fire simultaneously.
- **Don't surface only the first `BLOCK` reason.** Operators need every reason at once to triage. The `blocked_by`
  list is the contract.
- **Don't evaluate Layer 2 rules inside strategy-service.** Strategy queries the helper but does not own the
  evaluator. Cross-strategy / cross-account rules require the risk-and-exposure-service vantage point.
- **Don't add new aggregation semantics without UAC PR.** The decision-aggregation rules above are part of the helper
  contract; widening them silently changes behaviour across every consumer.

## Cross-references

- Risk rule vocabulary: [risk-rule-taxonomy.md](risk-rule-taxonomy.md)
- Risk-breaker escalation seam: [risk-breaker-seam.md](risk-breaker-seam.md)
- Kill switch + circuit breaker mechanics: [kill-switch-circuit-breaker.md](kill-switch-circuit-breaker.md)
- 4-layer risk-gates separation: [../09-strategy/architecture-v2/cross-cutting/risk-gates.md](../09-strategy/architecture-v2/cross-cutting/risk-gates.md)
- Layer 4 venue-side ErrorAction: [autonomous-recovery-matrix.md](autonomous-recovery-matrix.md)
- Capital-at-risk ceiling composition: [capital-efficiency-patterns.md](capital-efficiency-patterns.md)
- Plan-of-record:
  [plans/active/risk_simulations_limits_alerting_2026_05_10.md](../../plans/active/risk_simulations_limits_alerting_2026_05_10.md)
