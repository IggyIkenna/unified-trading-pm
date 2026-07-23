---
doc_type: codex-ssot
title: Risk-Breaker Seam — Distinct Enums With Escalation Event
summary:
  The architectural contract between Layer-2 risk-controller (RiskRuleConsequence) and Layer-3 circuit-breaker
  (BreakerAction) — two distinct closed enums that share a SCALE_DOWN member by design and never invoke each other,
  composing only through the single UAC BREAKER_ESCALATION_REQUESTED event fired on N-consecutive SCALE_DOWN in window W
  (RISK_TO_BREAKER_ESCALATION_MAP). Ratified Q9 2026-05-10 (distinct-enums-with-escalation-seam over unified-enum).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [risk, kill-switch, execution, escalation, uac]
related:
  [
    /codex/04-architecture/risk-rule-taxonomy.md,
    /codex/04-architecture/risk-preflight-flow.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: 2026-05-11
authoritative_for: [risk-controller ↔ circuit-breaker escalation seam (BREAKER_ESCALATION_REQUESTED)]
referenced_by:
  [
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/04-architecture/circuit-breaker-rule-taxonomy.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/kill-switch-event-bus.md,
    /codex/04-architecture/risk-preflight-flow.md,
    /codex/04-architecture/risk-rule-taxonomy.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Risk-Breaker Seam — Distinct Enums With Escalation Event

> **What it is:** The architectural contract between **Layer 2 risk-controller** (per-rule pre-flight decisions) and
> **Layer 3 circuit-breaker state machine** (per-venue rejection-rate-driven state transitions). The two layers publish
> **distinct closed enums** (`RiskRuleConsequence` ≠ `BreakerAction`) and never directly invoke each other. They compose
> only through a **single UAC-defined escalation event** — `BREAKER_ESCALATION_REQUESTED` — fired when N-consecutive
> `RiskRuleConsequence.SCALE_DOWN` consequences accumulate on the same `(venue, asset_group)` within a rolling window W.
> The breaker subscribes to the event and transitions per its own rules; the risk-controller never reads breaker state.
> This doc ratifies the design (Q9 2026-05-10) and codifies the seam.

## TL;DR

`RiskRuleConsequence` and `BreakerAction` are SEPARATE enums by design. Both contain a `SCALE_DOWN` member — that naming
collision is **intentional** because the operator-facing concept ("reduce activity") is the same, but the **triggers,
layers, and consequences are different**.

- **`RiskRuleConsequence.SCALE_DOWN`** at Layer 2 → applies to a SINGLE pre-flight instruction; shrinks its size; does
  NOT change breaker state; emits `RISK_RULE_SCALED_DOWN` AlertCode.
- **`BreakerAction.SCALE_DOWN`** at Layer 3 → applies to ALL future instructions on a `(venue, asset_group)`; the
  breaker enters a degraded state for some cooldown window; emits `CIRCUIT_BREAKER_DEGRADED` AlertCode.

The two layers compose through one well-defined seam — `BREAKER_ESCALATION_REQUESTED` — and nothing else. The
risk-controller can fire SCALE_DOWN consequences indefinitely without ever engaging the breaker; the breaker can
transition CLOSED → DEGRADED → OPEN purely from venue-rejection rates without any risk-controller fire. They are
**independent layers ESCALATING through the seam**, not duplicating each other.

## Why the naming collision is intentional

Collapsing the two enums into a single set would be a category error. Consider the same operator-facing concept, "scale
down", at two layers:

| Question                        | Layer 2 answer (RiskRuleConsequence.SCALE_DOWN)                   | Layer 3 answer (BreakerAction.SCALE_DOWN)                              |
| ------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------- |
| What triggered it?              | A rule fired on THIS instruction's context                        | N venue rejections within rolling-window threshold                     |
| What does it affect?            | THIS instruction's size                                           | ALL future instructions on `(venue, asset_group)`                      |
| How long does the effect last?  | One instruction (next instruction re-evaluates)                   | A cooldown window (per `BreakerConfig.cooldown_seconds`)               |
| What state machine owns it?     | Stateless per-instruction evaluator                               | Stateful per-venue circuit breaker                                     |
| What event(s) emit?             | `RISK_RULE_SCALED_DOWN` AlertCode                                 | `CIRCUIT_BREAKER_DEGRADED` AlertCode                                   |
| How does the operator un-do it? | Wait for the rule's input state to clear (e.g. drawdown recovers) | Manual `kill-switch unkill` OR auto-cooldown per `BreakerRecoveryMode` |

Same operator vocabulary; entirely different semantics. The seam keeps the vocabulary aligned (the operator dashboard
shows "scale down" for both) while keeping the implementations decoupled.

## The seam: `BREAKER_ESCALATION_REQUESTED`

A `BREAKER_ESCALATION_REQUESTED` event fires when the risk-controller observes a pattern of N consecutive
`RiskRuleConsequence.SCALE_DOWN` fires on the same `(venue, asset_group)` within a rolling time window W. The threshold
table is declared in UAC:

```python
# unified_api_contracts/canonical/crosscutting/risk_rule.py (planned addition, scope: cutover sprint)
RISK_TO_BREAKER_ESCALATION_MAP: dict[
    tuple[RiskRuleConsequence, int, timedelta],  # (consequence, N_fires, window_W)
    BreakerAction,                                # → escalation action
] = {
    (RiskRuleConsequence.SCALE_DOWN, 5, timedelta(minutes=15)): BreakerAction.SCALE_DOWN,
    (RiskRuleConsequence.SCALE_DOWN, 10, timedelta(minutes=30)): BreakerAction.BLOCK_NEW,
    (RiskRuleConsequence.SCALE_DOWN, 20, timedelta(hours=1)): BreakerAction.CANCEL_OPEN,
    # ...
}
```

**Status (2026-05-11)**: shape declared; concrete thresholds populated as part of risk plan Phase 4 (per-service
migration) when the per-archetype rule registries shape the cutover-aspirational N + W values. Until populated, the seam
ships as a typed-dict stub with TODO entries — readers should consult the risk plan body for the in-flight thresholds.

### Event flow

```
RiskRule fires SCALE_DOWN on instruction I_k for (venue=V, asset_group=G)
        │
        ▼
risk_preflight() records the fire in the rolling-window log keyed by (V, G)
        │
        ▼
Sliding-window check: are there ≥ N fires within window W?
        │
        ├── NO  → instruction I_k proceeds at reduced size; no further escalation
        │
        └── YES → emit BREAKER_ESCALATION_REQUESTED:
                   {
                     "venue": V,
                     "asset_group": G,
                     "consequence_observed": SCALE_DOWN,
                     "n_fires": N,
                     "window": W,
                     "escalation_action": <looked up in RISK_TO_BREAKER_ESCALATION_MAP>,
                   }
                   → published to circuit-breaker-commands PubSub
                   │
                   ▼
                   execution-service circuit_breaker subscribes,
                   consumes the event, transitions (V, G) breaker per
                   its own rules:
                     CLOSED → DEGRADED   (action=SCALE_DOWN)
                     DEGRADED → OPEN     (action=BLOCK_NEW)
                     OPEN → CANCEL_OPEN  (action=CANCEL_OPEN; cooldown extended)
```

Note: the breaker's existing CLOSED → DEGRADED → OPEN transitions driven by venue-rejection rates continue to operate
independently. The seam adds an ADDITIONAL transition cause — risk-controller-driven escalation — without removing the
existing venue-rejection-rate-driven cause.

## Layering diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1 — STRATEGY SELF-CHECK                                    │
│   Local; per-instance; cheap.                                    │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2 — RISK PRE-FLIGHT (RiskRuleConsequence: per-rule)        │
│   Decisions: BLOCK / SCALE_DOWN / MONITOR / TEST_ONLY            │
│   Per-instruction; stateless evaluator.                          │
│   Side effect: rolling-window log per (venue, asset_group).      │
│                                                                  │
│   Emits BREAKER_ESCALATION_REQUESTED when N-in-W threshold met.  │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼ (escalation seam — published event)
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3 — CIRCUIT BREAKER (BreakerAction: per-venue state machine)│
│   States: CLOSED / DEGRADED / OPEN / HALF_OPEN                   │
│   Transition causes:                                             │
│     (a) venue-rejection-rate threshold (existing)                │
│     (b) BREAKER_ESCALATION_REQUESTED (NEW: risk-controller seam) │
│   Actions: SCALE_DOWN / BLOCK_NEW / CANCEL_OPEN / KILL_ALL        │
│   Per-action recovery mode: manual_unkill / auto_cooldown        │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 4 — VENUE-SIDE (ErrorAction post-rejection classification) │
│   RETRY / RECONNECT / SKIP / FAIL                                │
│   Orthogonal to Layers 2-3; only relevant after venue contact.    │
└─────────────────────────────────────────────────────────────────┘
```

## Operational implications

- **Risk-controller can fire WITHOUT breaker firing.** A drawdown-based SCALE_DOWN on a small archetype shrinks one
  instruction; if the rule clears next tick (drawdown recovers), no second fire, no breaker engagement.
- **Breaker can fire WITHOUT risk-controller firing.** A venue's API starts returning 5xx on 60% of orders → the
  failure-rate threshold trips the breaker OPEN regardless of any risk-rule state.
- **Both can fire on the same root cause.** A correlated-positions blowup triggers per-instruction SCALE_DOWN from the
  correlation rule AND a flood of venue rejections that trips the rejection-rate threshold. Both Layer 2 and Layer 3
  respond; events emit from both layers; the seam ALSO fires (N SCALE_DOWNs in W). The breaker transitions twice (once
  from rejection-rate, once from seam) — both transitions are idempotent (CLOSED → DEGRADED is a no-op if already
  DEGRADED).
- **Risk-controller doesn't read breaker state.** The risk-controller has no `breaker.is_open(venue)` check. The Layer 2
  evaluator is stateless w.r.t. breaker state. If the breaker is OPEN, Layer 3 will reject the instruction AFTER Layer 2
  passes — that's the correct layering; Layer 2 doesn't need to anticipate.
- **Breaker doesn't read risk-controller state.** The breaker has no `risk.last_scaled_down(venue)` check. The breaker
  subscribes only to the `BREAKER_ESCALATION_REQUESTED` event + venue rejection-rate updates from execution-service.

This independence is what makes the layers composable. Each can evolve (new rules, new actions, new recovery modes)
without touching the other, as long as the event-seam contract holds.

## Recovery mode wiring

When the breaker transitions to OPEN or BLOCK_NEW via the seam, the recovery mode comes from
[`BreakerConfig.recovery_mode`](kill-switch-circuit-breaker.md) (UAC@a7a99b5). Per-action defaults from
`BREAKER_RECOVERY_DEFAULTS`:

- `BLOCK_NEW` → `auto_cooldown` (after `cooldown_seconds` of green guard reads, auto-disarm; emit
  `KILL_SWITCH_AUTO_RECOVERED`).
- `CANCEL_OPEN` → `manual_unkill` (cancelled orders are gone; operator decides when to re-enable).
- `SCALE_DOWN` → `auto_cooldown`.
- `KILL_ALL` → `manual_unkill`.

The risk-controller is not aware of recovery — it sees only the seam-emission side. Once the breaker auto-recovers or is
operator-unkilled, subsequent Layer 2 SCALE_DOWNs start a fresh window.

## Anti-patterns

- **Don't collapse the enums.** `RiskRuleConsequence.SCALE_DOWN` and `BreakerAction.SCALE_DOWN` MUST stay distinct.
  Operator dashboards may display them with the same word, but the type system enforces the layering.
- **Don't treat Layer 2 SCALE_DOWN as Layer 3 SCALE_DOWN directly.** A single Layer 2 fire does NOT change breaker
  state. The seam threshold (N-in-W) is the gating contract.
- **Don't bypass the event for "performance reasons".** Direct invocation of `breaker.set_state()` from the
  risk-controller defeats the layering. The PubSub event is the contract — events emit; the breaker subscribes.
- **Don't add a `BreakerAction` member to `RiskRuleConsequence` (or vice versa).** Different vocabularies for different
  layers. Extension goes via the seam map, not via union enum membership.
- **Don't read breaker state from the risk-controller.** Layer 2 evaluators are stateless w.r.t. Layer 3 state. If you
  find yourself wanting `breaker.is_open(venue)` in a rule evaluator, the rule belongs at Layer 3 instead.
- **Don't widen the seam contract silently.** Adding a new escalation pattern (e.g. "N BLOCKs in W" → breaker arm)
  requires a UAC PR extending `RISK_TO_BREAKER_ESCALATION_MAP`. Reviewers reject inline patterns in service code.

## Q9 ratification (2026-05-10)

The operator ratified Framing 2 ("distinct enums with escalation seam") over Framing 1 ("unified single enum") on
2026-05-10. The decision is recorded in
[`risk_simulations_limits_alerting_2026_05_10.md` Phase 7.E](../../plans/archive/risk_simulations_limits_alerting_2026_05_10.md#phase-7--codex-ssots-day-12-05-ai-day)
and
[`disaster_recovery_circuit_breakers_2026_05_10.md` Phase 8.F](../../plans/archive/disaster_recovery_circuit_breakers_2026_05_10.md#phase-8--codex-ssots-day-12-05-ai-day).
This doc is co-owned by both plans — risk plan Phase 7.E ships the doc; DR plan Phase 8.F cross-references it; both
plans cite the seam in their `## Cross-plan coordination` sections.

## Cross-references

- Risk rule vocabulary: [risk-rule-taxonomy.md](risk-rule-taxonomy.md)
- Pre-flight flow + aggregation semantics: [risk-preflight-flow.md](risk-preflight-flow.md)
- Kill switch + circuit breaker mechanics: [kill-switch-circuit-breaker.md](kill-switch-circuit-breaker.md)
- 4-layer risk-gates separation:
  [/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md](/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md)
- Layer 4 ErrorAction taxonomy: [autonomous-recovery-matrix.md](autonomous-recovery-matrix.md)
- Co-owned plans:
  [plans/active/risk_simulations_limits_alerting_2026_05_10.md](../../plans/archive/risk_simulations_limits_alerting_2026_05_10.md) +
  [plans/active/disaster_recovery_circuit_breakers_2026_05_10.md](../../plans/archive/disaster_recovery_circuit_breakers_2026_05_10.md)
