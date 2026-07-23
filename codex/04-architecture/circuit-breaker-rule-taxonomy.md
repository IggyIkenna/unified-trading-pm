---
doc_type: codex-ssot
title: Circuit-Breaker Rule Taxonomy — Closed-Set Layer-3 Vocabulary
summary:
  "Canonical SSOT for the Layer-3 circuit-breaker vocabulary: CircuitBreakerId (20), BreakerScope (5), BreakerTrigger,
  BreakerAction (4), BreakerRecoveryMode (2) + BREAKER_RECOVERY_DEFAULTS; two 10-breaker per-archetype registry seeds."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [circuit-breaker, kill-switch, risk, execution, defi, taxonomy, recovery]
related:
  [
    plans/active/disaster_recovery_circuit_breakers_2026_05_10.md,
    plans/active/risk_simulations_limits_alerting_2026_05_10.md,
    plans/active/alerting_service_live_rules_2026_05_07.md,
  ]
created: 2026-05-11
authoritative_for:
  [Layer-3 circuit-breaker rule taxonomy, CircuitBreakerId/BreakerScope/BreakerAction/BreakerRecoveryMode closed sets]
referenced_by:
  [
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/kill-switch-event-bus.md,
    /codex/04-architecture/mev-protection.md,
    /codex/04-architecture/reconciliation-resolution.md,
  ]
owner: ikenna
last_reviewed: 2026-05-17
code_refs:
related_codex:
  [
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/kill-switch-event-bus.md,
    /codex/04-architecture/risk-breaker-seam.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/risk-rule-taxonomy.md,
    /codex/04-architecture/mev-protection.md,
  ]
---

# Circuit-Breaker Rule Taxonomy — Closed-Set Layer-3 Vocabulary

> **What it is:** The canonical workspace SSOT for the **Layer-3 circuit-breaker vocabulary** — what fires, where, with
> what action, and under what recovery semantics. Every `CircuitBreakerId` listed here lives in
> `unified_api_contracts.canonical.crosscutting.circuit_breaker` (UAC@a7a99b5); the per-archetype thresholds live under
> `unified_api_contracts/registry/circuit_breakers/<archetype>.py`. Shipped DR plan Phase 1.A; this doc is the codex
> SSOT companion (Phase 8.A).

## TL;DR

A **circuit breaker** is a Layer-3 state machine that watches a typed `BreakerTrigger`, fires a `BreakerAction` when the
trigger threshold is crossed, and disarms via a `BreakerRecoveryMode`. Triggers feed in from risk-controller seam events
(Layer 2 → Layer 3, per [`risk-breaker-seam.md`](risk-breaker-seam.md)), venue-rejection-rate sliding-windows (the
classic CLOSED/DEGRADED/OPEN/HALF_OPEN state machine in
[`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md)), and per-state-surface reconciler outputs (DR plan
Phase 3 — positions / balances / custody / on-chain / events / manifest / order-state / PnL+clock+batch-live). When the
action escalates to `KILL_ALL`, the breaker engages a `KillSwitchId` via the bus
([`kill-switch-event-bus.md`](kill-switch-event-bus.md)).

**Five orthogonal axes per breaker** — collapse none of them:

| Axis                  | Type                   | What it captures                                                                  |
| --------------------- | ---------------------- | --------------------------------------------------------------------------------- |
| `CircuitBreakerId`    | `StrEnum` (20 members) | What's being watched (oracle / RPC / gas / position / etc.)                       |
| `BreakerScope`        | `StrEnum` (5-set)      | Blast radius (per-venue / per-archetype / per-account / per-asset_group / global) |
| `BreakerTrigger`      | `BaseModel`            | Threshold value + unit + optional window + consecutive count                      |
| `BreakerAction`       | `StrEnum` (4-set)      | Execution-side response (BLOCK_NEW / CANCEL_OPEN / SCALE_DOWN / KILL_ALL)         |
| `BreakerRecoveryMode` | `StrEnum` (2-set)      | How the breaker disarms (manual_unkill / auto_cooldown)                           |

Plus `BREAKER_RECOVERY_DEFAULTS: dict[BreakerAction, BreakerRecoveryMode]` is the per-action default mapping that drives
`BreakerConfig.recovery_mode` resolution at construction time.

## `CircuitBreakerId` — closed set (20 members)

Each member is **archetype-agnostic** at the enum level; per-archetype tuning happens in the registry seed. Members
group by which cutover archetype primarily uses them.

### `carry_staked_basis` family (LST leverage)

| ID                           | Description                                                                         |
| ---------------------------- | ----------------------------------------------------------------------------------- |
| `ORACLE_DEVIATION_BPS`       | Oracle price deviation from canonical mid (Chainlink/Pyth) ≥ threshold bps.         |
| `RPC_OUTAGE_SECONDS`         | Chain RPC endpoint unreachable ≥ threshold seconds.                                 |
| `GAS_PRICE_SURGE_GWEI`       | L1 gas price ≥ threshold gwei (renders tx-cost economics negative).                 |
| `POSITION_LIMIT_EXCEEDED`    | Per-archetype / per-venue gross position exceeds configured cap.                    |
| `DRAWDOWN_DAILY_BPS`         | Daily drawdown ≥ threshold bps of NAV.                                              |
| `LIQUIDATION_CASCADE_RISK`   | Aave/lending health-factor approaches liquidation across multiple positions.        |
| `VENUE_OUTAGE_SECONDS`       | Venue REST + WS both unreachable ≥ threshold seconds.                               |
| `CUSTODY_DISCONNECT_SECONDS` | Copper / CEFFU custody endpoint unreachable ≥ threshold seconds.                    |
| `MANIFEST_PHANTOM_RATE_BPS`  | Manifest phantom rate (captured-but-no-parquet) ≥ threshold bps of expected shards. |
| `BATCH_LIVE_DIVERGENCE_BPS`  | Batch-vs-live P&L divergence ≥ threshold bps (UTL@908b1647 batch_live_reconciler).  |

### `arbitrage_price_dispersion` family (funding-arb / cross-venue)

| ID                           | Description                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| `FUNDING_RATE_FLIP_BPS`      | Funding rate flips sign or moves ≥ threshold bps in one funding window.            |
| `BASIS_INVERSION_BPS`        | Cash-perp basis inverts or moves ≥ threshold bps adverse.                          |
| `SPREAD_BLOWOUT_BPS`         | Quoted bid-ask spread ≥ threshold bps (illiquidity / venue degradation).           |
| `CROSS_VENUE_DIVERGENCE_BPS` | Same-instrument mid-price across hedge venues diverges ≥ threshold bps.            |
| `INVENTORY_IMBALANCE_RATIO`  | Cross-venue inventory imbalance ≥ threshold ratio (hedge leg out of sync).         |
| `FILL_LATENCY_BREACH_MS`     | Order ack → fill latency p99 ≥ threshold ms (venue performance degradation).       |
| `REJECT_RATE_BPS`            | Order rejection rate over rolling window ≥ threshold bps.                          |
| `PNL_VARIANCE_SIGMA`         | Realised PnL variance ≥ threshold sigma vs expected (live-vs-backtest drift).      |
| `HEDGE_GAP_NOTIONAL_USD`     | Unhedged delta notional ≥ threshold USD.                                           |
| `CLOCK_SKEW_MS`              | Local clock vs venue ts skew ≥ threshold ms (timestamp-mismatch correctness risk). |

**Adding a new breaker** (review-blocking checklist per
[`disaster_recovery_circuit_breakers_2026_05_10.md`](../../plans/archive/disaster_recovery_circuit_breakers_2026_05_10.md)):

1. Append the identifier to `CircuitBreakerId` (UAC `canonical/crosscutting/circuit_breaker.py`).
2. Add a `BreakerConfig` entry to **each applicable** per-archetype registry seed
   (`unified_api_contracts/registry/circuit_breakers/<archetype>.py`).
3. Add a matching `BreakerRecoveryRule` for the same `CircuitBreakerId`.
4. If the trigger maps to an alert, append the corresponding `AlertCode` in `alerting/codes.py`.
5. Cross-link the codex doc list (this doc + [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md) +
   [`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md)).
6. If the trigger is reconciler-driven, update [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md) §
   "Per-state-surface reconciler outputs feed breaker triggers" with the consuming reconciler.

## `BreakerScope` — 5-set blast radius

| Scope             | Applies to                                                                   | Mapping to `KillSwitchScope` (alerting)                      |
| ----------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `PER_VENUE`       | Single venue (e.g. `bybit`, `aave_arbitrum`).                                | `KillSwitchScope.VENUE`                                      |
| `PER_ARCHETYPE`   | One trading archetype (`carry_staked_basis` / `arbitrage_price_dispersion`). | `KillSwitchScope.ARCHETYPE`                                  |
| `PER_ACCOUNT`     | One operator account / sub-fund.                                             | `KillSwitchScope.ACCOUNT`                                    |
| `PER_ASSET_GROUP` | One asset_group (`cefi` / `defi`).                                           | No 1:1 enum; runtime maps to GLOBAL filtered by asset_group. |
| `GLOBAL`          | Every archetype × every venue.                                               | `KillSwitchScope.GLOBAL`                                     |

`BreakerConfig.applies_to: str` carries the scope-key (venue name when `scope=PER_VENUE`, archetype string when
`scope=PER_ARCHETYPE`, etc.). The literal `"*"` means scope-wide (every member of the scope).

## `BreakerAction` — 4-set execution response

Severity escalates **left-to-right**:

| Action        | Behaviour                                                         | Default `BreakerRecoveryMode` (per `BREAKER_RECOVERY_DEFAULTS`) |
| ------------- | ----------------------------------------------------------------- | --------------------------------------------------------------- |
| `BLOCK_NEW`   | Least restrictive. New orders refused; in-flight kept.            | `AUTO_COOLDOWN`                                                 |
| `SCALE_DOWN`  | Proportional unwind (e.g. halve position).                        | `AUTO_COOLDOWN`                                                 |
| `CANCEL_OPEN` | Open orders cancelled; existing positions held.                   | `MANUAL_UNKILL`                                                 |
| `KILL_ALL`    | Full unwind / delta-neutral exit; engages `KillSwitchId` via bus. | `MANUAL_UNKILL`                                                 |

**Rationale for the per-action recovery default**:

- `BLOCK_NEW` + `SCALE_DOWN` → `AUTO_COOLDOWN`. Both have a natural inverse (resume when metric clears; re-scale up when
  conditions improve). Safe to auto-recover.
- `CANCEL_OPEN` → `MANUAL_UNKILL`. Cancelled orders don't come back. Auto-recovery would silently re-engage trading
  without operator awareness that the in-flight book was wiped.
- `KILL_ALL` → `MANUAL_UNKILL`. Full unwind needs operator sign-off before any new sizing.

Per-breaker override via `BreakerConfig.recovery_mode` is supported but **review-blocking** — overriding away from
defaults requires a written rationale in the registry seed's `description` field. Reviewers reject silent overrides.

## `BreakerRecoveryMode` — 2-set recovery semantics

Codified per **Q8 ratification 2026-05-10** (cross-plan audit between DR Phase 1.A + risk-plan Phase 1.F).

| Mode            | When the breaker disarms                                                                           | Recovery event                                                                               |
| --------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `MANUAL_UNKILL` | Operator action via deployment-UI kill-switch tab or `kill-switch unkill` CLI.                     | `KILL_SWITCH_MANUAL_UNKILLED` AlertCode + `unkilled_by_operator_id` metadata.                |
| `AUTO_COOLDOWN` | Guard predicate re-evaluated every `cooldown_seconds`; N consecutive green readings → auto-disarm. | `KILL_SWITCH_AUTO_RECOVERED` AlertCode + `recovered_after_seconds` + guard-evaluation trail. |

`BreakerConfig` validator semantics:

- `recovery_mode == AUTO_COOLDOWN` → `cooldown_seconds` MUST be a positive int.
- `recovery_mode == MANUAL_UNKILL` → `cooldown_seconds` MUST be `None`.
- If `recovery_mode is None` at construction, the default from `BREAKER_RECOVERY_DEFAULTS[action]` is filled in via a
  Pydantic `model_validator`.

## `BreakerTrigger` — closed-union typed condition

`BreakerTrigger` is a frozen Pydantic model with four fields:

```python
class BreakerTrigger(BaseModel):
    trigger_type: CircuitBreakerId        # which id this trigger evaluates
    threshold_value: Decimal              # numeric threshold to cross
    threshold_unit: ThresholdUnit         # bps / ratio / USD / seconds / etc.
    window_seconds: int | None = None     # optional rolling-window length
    consecutive_count: int | None = None  # optional N-consecutive guard
```

The trigger axis is **closed** at the type level — every breaker watches exactly one `CircuitBreakerId`, against exactly
one threshold value, with at most one rolling-window length. Compound triggers (e.g. "oracle deviation > 100bps AND gas
price > 200 gwei") are decomposed into two separate breakers that share a `BreakerScope`. The execution-service's
matching-engine subscribes to the union; when both fire, the higher-severity action wins.

**Window semantics**:

- `window_seconds=None, consecutive_count=None` → instantaneous evaluation; one threshold breach fires.
- `window_seconds=60, consecutive_count=None` → rolling-window aggregate (e.g. failure-rate over the last 60s).
- `window_seconds=60, consecutive_count=3` → 3 consecutive 60s windows above threshold (oracle deviation `BreakerConfig`
  uses this shape).

## `BreakerConfig` + `BreakerRecoveryRule` semantics

A complete per-archetype breaker is the pair of `(BreakerConfig, BreakerRecoveryRule)` keyed by `breaker_id`:

```python
BreakerConfig(
    breaker_id=CircuitBreakerId.ORACLE_DEVIATION_BPS,
    scope=BreakerScope.PER_ARCHETYPE,
    applies_to="CARRY_STAKED_BASIS",
    trigger=BreakerTrigger(
        trigger_type=CircuitBreakerId.ORACLE_DEVIATION_BPS,
        threshold_value=Decimal("100"),
        threshold_unit=ThresholdUnit.BPS_OF_ONE,
        window_seconds=60,
        consecutive_count=3,
    ),
    action=BreakerAction.BLOCK_NEW,
    cooldown_seconds=300,          # required when recovery_mode=AUTO_COOLDOWN
    alerting_severity=AlertSeverity.HIGH,
    description="Chainlink/Pyth oracle deviation > 100bps for 3 consecutive 60s windows.",
)

BreakerRecoveryRule(
    breaker_id=CircuitBreakerId.ORACLE_DEVIATION_BPS,
    guard_description="oracle deviation < 5 sigma for 5min",
    retry_policy="exponential",   # exponential | linear | none
    auto_disarm_after_seconds=300, # matches BreakerConfig.cooldown_seconds for AUTO_COOLDOWN
)
```

**`BreakerRecoveryRule` validator semantics**:

- `MANUAL_UNKILL` rules MUST have `auto_disarm_after_seconds=None` (operator drives disarm; no hard timeout).
- `AUTO_COOLDOWN` rules MUST have `auto_disarm_after_seconds` set to a positive int matching
  `BreakerConfig.cooldown_seconds`.

Reviewers cross-check that every `CircuitBreakerId` listed for an archetype has BOTH a `BreakerConfig` AND a matching
`BreakerRecoveryRule` in the same registry seed file. Missing either is review-blocking.

## Per-archetype registry seed (≥10 breakers per cutover archetype)

The DR plan Phase 1.B ships two seed files (UAC@a7a99b5):

### `unified_api_contracts/registry/circuit_breakers/carry_staked_basis.py`

10 breakers covering the LST-leverage archetype:

1. `ORACLE_DEVIATION_BPS` — `BLOCK_NEW`, 300s cooldown, HIGH severity.
2. `RPC_OUTAGE_SECONDS` — `BLOCK_NEW`, 120s cooldown, HIGH severity.
3. `GAS_PRICE_SURGE_GWEI` — `BLOCK_NEW`, 180s cooldown, WARN severity.
4. `POSITION_LIMIT_EXCEEDED` — `CANCEL_OPEN`, manual_unkill, CRITICAL severity.
5. `DRAWDOWN_DAILY_BPS` — `SCALE_DOWN`, 600s cooldown, HIGH severity.
6. `LIQUIDATION_CASCADE_RISK` — `KILL_ALL`, manual_unkill, CRITICAL severity.
7. `VENUE_OUTAGE_SECONDS` — `BLOCK_NEW`, 600s cooldown, HIGH severity.
8. `CUSTODY_DISCONNECT_SECONDS` — `BLOCK_NEW`, 300s cooldown, CRITICAL severity.
9. `MANIFEST_PHANTOM_RATE_BPS` — `BLOCK_NEW`, 600s cooldown, WARN severity (feeds from manifest reconciler).
10. `BATCH_LIVE_DIVERGENCE_BPS` — `SCALE_DOWN`, 900s cooldown, HIGH severity (feeds from batch-live reconciler).

### `unified_api_contracts/registry/circuit_breakers/arbitrage_price_dispersion.py`

10 breakers covering the funding-arb archetype:

1. `FUNDING_RATE_FLIP_BPS` — `SCALE_DOWN`, 300s cooldown, HIGH severity.
2. `BASIS_INVERSION_BPS` — `SCALE_DOWN`, 300s cooldown, HIGH severity.
3. `SPREAD_BLOWOUT_BPS` — `BLOCK_NEW`, 180s cooldown, WARN severity.
4. `CROSS_VENUE_DIVERGENCE_BPS` — `BLOCK_NEW`, 120s cooldown, HIGH severity.
5. `INVENTORY_IMBALANCE_RATIO` — `CANCEL_OPEN`, manual_unkill, CRITICAL severity.
6. `FILL_LATENCY_BREACH_MS` — `BLOCK_NEW`, 60s cooldown, WARN severity.
7. `REJECT_RATE_BPS` — `BLOCK_NEW`, 120s cooldown, WARN severity (composes with the venue-rejection-rate state machine).
8. `PNL_VARIANCE_SIGMA` — `SCALE_DOWN`, 1800s cooldown, HIGH severity.
9. `HEDGE_GAP_NOTIONAL_USD` — `KILL_ALL`, manual_unkill, CRITICAL severity.
10. `CLOCK_SKEW_MS` — `BLOCK_NEW`, 60s cooldown, HIGH severity (feeds from clock reconciler).

Concrete thresholds per breaker live in the registry seed; this codex doc enumerates the IDs + actions + recovery
defaults only. Per-archetype tuning is reviewed in the DR plan, not here.

## Trigger sources — three input axes

A breaker fires from any of three independent input streams; the breaker subscribes to all three and acts on the first
to cross threshold:

1. **Venue-rejection-rate sliding-window** — the classic
   [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md) state machine (CLOSED → DEGRADED at 30% failure
   rate; DEGRADED → OPEN at 60%; exponential backoff in HALF_OPEN). Lives in
   `execution-service/engine/circuit_breaker.py`. Feeds the `REJECT_RATE_BPS` + `FILL_LATENCY_BREACH_MS` breakers
   natively.
2. **Risk-controller seam events** — `BREAKER_ESCALATION_REQUESTED` emitted by the risk-controller when N consecutive
   `RiskRuleConsequence.SCALE_DOWN` fires accumulate on the same `(venue, asset_group)` within window W. See
   [`risk-breaker-seam.md`](risk-breaker-seam.md) for the full layering contract + `RISK_TO_BREAKER_ESCALATION_MAP`
   threshold table.
3. **Per-state-surface reconciler outputs** — DR plan Phase 3 ships 8 reconcilers (positions / balances / custody /
   on-chain / events / manifest / order-state / PnL+clock+batch-live). Each reconciler emits typed drift events that
   feed the matching breaker. See
   [`kill-switch-circuit-breaker.md` § "Per-state-surface reconciler outputs"](kill-switch-circuit-breaker.md).

These three input streams are **independent + idempotent**. A single root cause that fires from multiple streams (e.g.
venue outage tripping both rejection-rate AND custody reconciler) results in idempotent state transitions (CLOSED →
DEGRADED is a no-op if already DEGRADED).

## Compose with the kill-switch event bus

When a breaker's action escalates to `BreakerAction.KILL_ALL`, the breaker engages a `KillSwitchId` via the
[`kill-switch-event-bus.md`](kill-switch-event-bus.md). The wire is:

```
BreakerConfig.action == KILL_ALL fires
    │
    ▼
breaker maps (scope, applies_to) → KillSwitchId per the registry:
    PER_ARCHETYPE / CARRY_STAKED_BASIS → KillSwitchId.KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS
    PER_VENUE / bybit                  → KillSwitchId.KILL_PER_VENUE_BYBIT
    GLOBAL                              → KillSwitchId.KILL_ALL_LIVE
    │
    ▼
KillSwitchBus.arm(KillSwitchArmRequest(
    switch_id=...,
    provenance=KillSwitchProvenance.BREAKER_AUTO,
    requested_by=f"{breaker_id}:{breaker_serial}",
    metadata={"breaker_id": ..., "threshold_observed": ..., "correlation_id": ...},
))
    │
    ▼
KillSwitchArmedEvent emitted to subscribers (execution-service, strategy-service, PBMS)
```

Disarm follows the breaker's `BreakerRecoveryMode`:

- `AUTO_COOLDOWN` → bus auto-emits `KillSwitchDisarmEvent(recovery_mode=AUTO_COOLDOWN, cooldown_seconds_elapsed=N)` once
  the guard reads green for `cooldown_seconds`.
- `MANUAL_UNKILL` → bus waits for operator action; emits
  `KillSwitchDisarmEvent(recovery_mode=MANUAL_UNKILL, disarmed_by=operator_id, cooldown_seconds_elapsed=None)`.

## Layer-3 boundary (what's NOT a breaker)

To keep the taxonomy clean, three adjacent concepts are **explicitly NOT** circuit breakers:

- **Layer-2 risk-rule consequences** (`RiskRuleConsequence`) — per-instruction; stateless; live in
  [`risk-rule-taxonomy.md`](risk-rule-taxonomy.md). Compose with breakers ONLY via the seam event
  ([`risk-breaker-seam.md`](risk-breaker-seam.md)).
- **Layer-4 error-action classification** (`ErrorAction` in
  [`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md)) — post-venue-error routing (RETRY / RECONNECT / SKIP
  / FAIL). Orthogonal to breaker firing.
- **Strategy-side kill-switch behaviour** (`STOP_NEW_ONLY` / `FAST_UNWIND` / `SLOW_UNWIND` / `DELTA_HEDGE`) — what the
  strategy does WHILE the kill-switch is armed. See
  [`kill-switch-circuit-breaker.md` § "Strategy-Service Behaviour During Kill Switch"](kill-switch-circuit-breaker.md).

The 4-set strategy behaviours are service-side decisions on top of the bus event; they don't change the breaker enum.

## Anti-patterns

- **Don't add a `CircuitBreakerId` without a registry seed entry.** Per-archetype tuning lives in the registry; adding
  the enum without populating the registry leaves the breaker invisible at runtime.
- **Don't override `BreakerRecoveryMode` without a written rationale.** The `BREAKER_RECOVERY_DEFAULTS` are operator-
  ratified (Q8 2026-05-10). Reviewers reject silent overrides — every `BreakerConfig(recovery_mode=...)` that diverges
  from the default MUST cite the rationale in `description`.
- **Don't compound triggers in a single `BreakerConfig`.** "Oracle deviation > 100bps AND gas > 200 gwei" is TWO
  breakers, not one. The matching engine subscribes to the union; the highest-severity firing action wins.
- **Don't subscribe directly to `BreakerArmed` events from the risk-controller.** Layer 2 → Layer 3 is one-way via the
  seam event; the risk-controller doesn't observe breaker state. See [`risk-breaker-seam.md`](risk-breaker-seam.md).
- **Don't expand `BreakerAction` beyond the 4-set.** Operator-facing vocab is closed at 4. New behaviours go into the
  strategy-side kill-switch 4-set, not into `BreakerAction`.
- **Don't conflate `BreakerAction.SCALE_DOWN` with `RiskRuleConsequence.SCALE_DOWN`.** Same word, different layers,
  different state machines. See
  [`risk-breaker-seam.md` § "Why the naming collision is intentional"](risk-breaker-seam.md).

## Cross-references

- Risk-controller seam contract: [`risk-breaker-seam.md`](risk-breaker-seam.md) (Q9 ratification 2026-05-10).
- Kill-switch event bus: [`kill-switch-event-bus.md`](kill-switch-event-bus.md).
- Circuit-breaker state machine: [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md).
- Autonomous recovery matrix (Layer-4 ErrorAction): [`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md).
- Risk rule vocabulary (Layer 2): [`risk-rule-taxonomy.md`](risk-rule-taxonomy.md).
- MEV-driven breakers: [`mev-protection.md`](mev-protection.md).
- Reconciler-driven breakers (DR Phase 3): [`reconciliation-resolution.md`](reconciliation-resolution.md).
- UAC SSOT: `unified_api_contracts.canonical.crosscutting.circuit_breaker` (UAC@a7a99b5).
- Per-archetype registries:
  `unified_api_contracts/registry/circuit_breakers/{carry_staked_basis,arbitrage_price_dispersion}.py`.
- Plan:
  [`disaster_recovery_circuit_breakers_2026_05_10.md`](../../plans/archive/disaster_recovery_circuit_breakers_2026_05_10.md).
