---
doc_type: codex-ssot
title: Kill-Switch Event Bus — UTL `KillSwitchBus` + Audit-Log Persistence
summary:
  "The UTL KillSwitchBus arm/disarm event lifecycle: 3 event shapes (KillSwitchArmRequest / ArmedEvent / DisarmEvent)
  keyed by the 12-member KillSwitchId, 4-set KillSwitchProvenance gating, and append-only GCS audit-log persistence — an
  arm that can't be audited aborts with no fan-out."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: [kill-switch, execution, defi, uac, self-healing, audit, ssot]
related:
  [
    plans/active/disaster_recovery_circuit_breakers_2026_05_10.md,
    plans/active/alerting_service_live_rules_2026_05_07.md,
    plans/active/risk_simulations_limits_alerting_2026_05_10.md,
  ]
created: 2026-05-11
authoritative_for:
  [
    KillSwitchBus arm/disarm lifecycle,
    kill-switch audit-log persistence,
    KillSwitchId registry,
    KillSwitchProvenance taxonomy,
  ]
referenced_by:
  [
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/circuit-breaker-rule-taxonomy.md,
    /codex/04-architecture/client-lifecycle-event-bus.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/manual-trade-booking.md,
    /codex/04-architecture/mev-protection.md,
    /codex/15-runbooks/wallet-tier-kill-switch-operator.md,
  ]
owner: ikenna
last_reviewed: 2026-05-17
code_refs:
related_codex:
  [
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/circuit-breaker-rule-taxonomy.md,
    /codex/04-architecture/risk-breaker-seam.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/03-observability/alerting.md,
  ]
---

# Kill-Switch Event Bus — UTL `KillSwitchBus` + Audit-Log Persistence

> **What it is:** The canonical workspace SSOT for the kill-switch arm/disarm event lifecycle. The bus owns the
> `(switch_id, scope, applies_to) → armed/disarmed` state machine; every subscriber (execution-service matching engine,
> strategy-service signal generators, position-balance-monitor reconcilers, alerting-service notifiers) consumes the
> typed event and transitions its own state. UAC types ship at UAC@a7a99b5 (DR plan Phase 1.C-D); UTL `KillSwitchBus`
> singleton predates the plan (audited in Phase 0.C). Audit-log persistence ships in Phase 2.A. This doc is the codex
> SSOT companion (Phase 8.B).

## TL;DR

The kill-switch event bus is the **one-way fan-out path** from a breaker firing (or operator click) to every consumer
that needs to halt. It carries 3 event shapes (`KillSwitchArmRequest` inbound, `KillSwitchArmedEvent` +
`KillSwitchDisarmEvent` outbound) keyed by `KillSwitchId`, with provenance tagging via `KillSwitchProvenance` and
recovery semantics via `BreakerRecoveryMode`. Every arm/disarm transition is written to an append-only audit log
(GCS-backed in prod, local fallback for dev) so post-mortem reconstruction is durable beyond the in-process pub-sub
ring.

**Five axes per event** — all five are required:

| Axis                    | Type                   | What it captures                                                                                 |
| ----------------------- | ---------------------- | ------------------------------------------------------------------------------------------------ |
| `KillSwitchId`          | `StrEnum` (12 members) | What's being killed (`KILL_ALL_LIVE` / per-archetype / per-venue / per-asset_group / per-wallet) |
| `KillSwitchProvenance`  | `StrEnum` (4-set)      | Who armed (operator / breaker / scenario / scheduled drill)                                      |
| `KillSwitchArmRequest`  | `BaseModel` (6 fields) | Inbound request to `KillSwitchBus.arm()` (carries `target_wallet_id` for `KILL_PER_WALLET`)      |
| `KillSwitchArmedEvent`  | `BaseModel`            | Emitted to subscribers on successful arm                                                         |
| `KillSwitchDisarmEvent` | `BaseModel`            | Emitted on disarm with `BreakerRecoveryMode` + elapsed-cooldown telemetry                        |

## `KillSwitchId` registry — 12 closed-set members

Cutover-scope kill-switches (Phase 1.C UAC@a7a99b5 + wallet-tier slot 4 UAC@d721b6a 2026-05-12):

| ID                                              | Scope                                                                                | Halt semantics                                                                                                                                                                                                                                                                                                                        |
| ----------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `KILL_ALL_LIVE`                                 | `GLOBAL`                                                                             | Halt every live archetype across every venue. Operator-only arming.                                                                                                                                                                                                                                                                   |
| `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS`         | `ARCHETYPE`                                                                          | Halt the carry-staked-basis archetype across all its venues.                                                                                                                                                                                                                                                                          |
| `KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION` | `ARCHETYPE`                                                                          | Halt the funding-arb archetype.                                                                                                                                                                                                                                                                                                       |
| `KILL_PER_VENUE_BYBIT`                          | `VENUE`                                                                              | Halt every archetype touching Bybit.                                                                                                                                                                                                                                                                                                  |
| `KILL_PER_VENUE_DERIBIT`                        | `VENUE`                                                                              | Halt every archetype touching Deribit.                                                                                                                                                                                                                                                                                                |
| `KILL_PER_VENUE_BINANCE`                        | `VENUE`                                                                              | Halt every archetype touching Binance.                                                                                                                                                                                                                                                                                                |
| `KILL_PER_VENUE_OKX`                            | `VENUE`                                                                              | Halt every archetype touching OKX.                                                                                                                                                                                                                                                                                                    |
| `KILL_PER_VENUE_HYPERLIQUID`                    | `VENUE`                                                                              | Halt every archetype touching Hyperliquid.                                                                                                                                                                                                                                                                                            |
| `KILL_PER_VENUE_ASTER`                          | `VENUE`                                                                              | Halt every archetype touching Aster.                                                                                                                                                                                                                                                                                                  |
| `KILL_PER_ASSET_GROUP_CEFI`                     | (asset-group filter — no enum)                                                       | Halt every CeFi archetype.                                                                                                                                                                                                                                                                                                            |
| `KILL_PER_ASSET_GROUP_DEFI`                     | (asset-group filter — no enum)                                                       | Halt every DeFi archetype.                                                                                                                                                                                                                                                                                                            |
| `KILL_PER_WALLET`                               | (runtime-targeted via `target_wallet_id` — see `KillSwitchScope` mapping note below) | **FINEST-grain switch** (below per-venue + per-archetype). Engages only the named wallet's signing surface, leaving sibling wallets of the same archetype unaffected. Composes with `WalletProvisioningConfig.kill_switch_id`. Added 2026-05-12 (slot 4 UAC@d721b6a) per `api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 5. |

> **Wallet axis — `KillSwitchScope` mapping note (2026-05-12).** Unlike per-venue / per-archetype which map cleanly to
> `KillSwitchScope.{VENUE,ARCHETYPE}`, `KillSwitchScope` has **no `WALLET` member** today — the wallet axis is
> _runtime-targeted_ via `KillSwitchArmRequest.target_wallet_id` rather than enum-per-wallet (which would explode the
> closed set unbounded). The `kill_switch.py` § 7 SSOT reconciliation docstring references a `KillSwitchScope.WALLET`;
> see audit finding R-5 / AL-1 for the slot 4 reconciliation (add enum member OR fix docstring to "runtime-targeted").
> See full wallet-tier kill-switch section + audit-log invariant in
> [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md) § "Wallet-tier kill-switch (`KILL_PER_WALLET`)".

**Adding a new kill-switch** (review-blocking checklist):

1. Append the identifier to `KillSwitchId` (UAC `canonical/crosscutting/kill_switch.py`).
2. Add a matching entry to the master plan's Group F item 20 row + the operator's Kill-switch tab in the deployment-UI
   (DR plan Phase 7.B).
3. Cross-link this codex doc + [`circuit-breaker-rule-taxonomy.md`](circuit-breaker-rule-taxonomy.md) (registry seed
   mapping).
4. If the kill-switch is breaker-engageable, register the `BreakerConfig.action == KILL_ALL` + scope-to-id mapping in
   the relevant per-archetype registry under `unified_api_contracts/registry/circuit_breakers/`.

## `KillSwitchProvenance` — 4-set closed enum

Drives downstream alert severity + recovery-mode policy:

| Provenance           | Source                                                                      | Severity                                    | Notes                                                                                       |
| -------------------- | --------------------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `OPERATOR_MANUAL`    | Operator click via deployment-UI kill-switch tab OR `kill-switch` CLI.      | HIGH (always)                               | `requested_by` carries operator ID; `KILL_ALL_LIVE` is operator-only.                       |
| `BREAKER_AUTO`       | Auto-armed by a `CircuitBreakerId` firing per its `BreakerAction.KILL_ALL`. | Inherits `BreakerConfig.alerting_severity`. | `requested_by` carries `f"{breaker_id}:{breaker_serial}"`.                                  |
| `SCENARIO_SYNTHETIC` | Chaos-drill cron / scenario runner.                                         | WARN                                        | Production-guarded: cron VM cannot arm on the live live-defi-rollout account; only testnet. |
| `SCHEDULED_DRILL`    | Nightly DR drill scheduler.                                                 | WARN                                        | Same severity as SCENARIO_SYNTHETIC; distinguishable in audit logs by source-VM tag.        |

Provenance gating rules:

- `KILL_ALL_LIVE` arming MUST have provenance `OPERATOR_MANUAL` or `SCHEDULED_DRILL`. Other provenances raise.
- `SCENARIO_SYNTHETIC` arming MUST happen on the testnet account, never the live account. Enforced at the bus
  construction site (testnet bus + live bus are separate singletons; the chaos-drill cron only has a handle to the
  testnet bus).

**Why `SCHEDULED_DRILL` is treated as operator-equivalent for `KILL_ALL_LIVE`**: A `SCHEDULED_DRILL` event is a nightly
disaster-recovery (DR) drill that runs on the live account with an operator present in the drill window. Unlike
`SCENARIO_SYNTHETIC` (fully unattended chaos-cron on testnet), every `SCHEDULED_DRILL` arm requires a human operator to
have pre-approved the drill time-window and to be monitoring the recovery sequence. The drill runner VM carries a
`source-vm-tag` in the audit log distinguishing it from a human click (`OPERATOR_MANUAL`), but the operator-attendance
requirement makes the risk profile equivalent. Both provenances satisfy the "human-in-the-loop" constraint for
`KILL_ALL_LIVE` arming.

## Event shapes

### `KillSwitchArmRequest` (inbound)

```python
class KillSwitchArmRequest(BaseModel):
    switch_id: KillSwitchId
    provenance: KillSwitchProvenance
    requested_by: str             # operator ID / breaker_id:serial / scenario_id / drill_id
    arm_timestamp: datetime       # when the arm was requested (UTC)
    target_wallet_id: str = ""    # required when switch_id == KILL_PER_WALLET (slot 4 UAC@d721b6a 2026-05-12); empty otherwise
    metadata: dict[str, str] = {} # breaker_serial / threshold_observed / correlation_id / etc.
```

Consumed by `KillSwitchBus.arm(request)`. The bus validates the provenance gates, then stamps the actual `armed_at` in
the outbound `KillSwitchArmedEvent` (may differ slightly from `arm_timestamp` if the bus queues the request).

### `KillSwitchArmedEvent` (outbound)

```python
class KillSwitchArmedEvent(BaseModel):
    switch_id: KillSwitchId
    provenance: KillSwitchProvenance
    armed_at: datetime
    requested_by: str
    metadata: dict[str, str] = {}
```

Fan-out to every subscriber. Subscribers MUST consume idempotently — re-emitting `KillSwitchArmedEvent` for an
already-armed switch is allowed (e.g. process restart replay) and consumers MUST not double-act.

### `KillSwitchDisarmEvent` (outbound)

```python
class KillSwitchDisarmEvent(BaseModel):
    switch_id: KillSwitchId
    disarmed_at: datetime
    disarmed_by: str              # operator ID OR literal "AUTO_COOLDOWN"
    recovery_mode: BreakerRecoveryMode  # MANUAL_UNKILL | AUTO_COOLDOWN
    cooldown_seconds_elapsed: int | None = None  # required for AUTO_COOLDOWN; None for MANUAL_UNKILL
    metadata: dict[str, str] = {}
```

Validator: `cooldown_seconds_elapsed` MUST be `None` when `recovery_mode=MANUAL_UNKILL`, and a positive int when
`recovery_mode=AUTO_COOLDOWN`. The actual elapsed time may be longer than the breaker's configured `cooldown_seconds` if
the guard predicate took multiple windows to read green.

## Audit-log persistence (Phase 2.A)

Every arm/disarm event is durably persisted to an append-only audit log, in addition to the in-process pub-sub fan-out.
The audit log is the SSOT for post-mortem reconstruction + operator-facing kill-switch history.

### Production path (GCS-backed)

```
gs://{pid}-kill-switch-audit/
└── audit/
    └── kill_switch/
        └── {YYYY-MM-DD}/
            └── {switch_id}/
                ├── armed_{timestamp}_{correlation_id}.jsonl
                └── disarmed_{timestamp}_{correlation_id}.jsonl
```

**Schema per JSONL line**:

```json
{
  "event_type": "armed | disarmed",
  "switch_id": "KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS",
  "provenance": "BREAKER_AUTO",
  "armed_at": "2026-05-15T12:34:56Z",
  "requested_by": "ORACLE_DEVIATION_BPS:00012",
  "metadata": {
    "breaker_serial": "00012",
    "threshold_observed": "125.4",
    "correlation_id": "abc-def-123"
  }
}
```

Writes are append-only via GCS `objects.create` with `If-Generation-Match: 0` semantics — no overwrite is ever
performed. The bus retries on transient failures (3 attempts, exponential backoff); permanent failure raises
`KillSwitchAuditLogPersistenceError` and the arm aborts with no in-process fan-out either. This is by design — an arm
that can't be audited is unsafe.

### Dev / testnet path (local fallback)

Local dev + testnet write the same JSONL schema to a workspace path:

```
${TMPDIR}/kill-switch-audit/{YYYY-MM-DD}/{switch_id}/{armed|disarmed}_{ts}_{cid}.jsonl
```

(Uses `tempfile.gettempdir()` per CLAUDE.md "Bandit B108" rule — no hardcoded `/tmp`.) The dev fallback is opt-in via
`KillSwitchBus(audit_log_mode="local")`; production must use GCS. The bus constructor refuses to start without one of
the two paths configured.

## Subscriber pattern

Subscribers register a callback at construction time and consume `KillSwitchArmedEvent` / `KillSwitchDisarmEvent` events
synchronously (in-process pub-sub; no asyncio queue). Multi-subscriber broadcast is a single fan-out call — if one
subscriber raises, the bus logs the failure but continues fan-out to the remaining subscribers (no subscriber can block
the others).

```python
from unified_trading_library.kill_switch import KillSwitchBus, KillSwitchSubscriber
from unified_api_contracts.canonical.crosscutting.kill_switch import (
    KillSwitchArmedEvent,
    KillSwitchDisarmEvent,
)

class ExecutionMatchingEngineSubscriber(KillSwitchSubscriber):
    def on_armed(self, event: KillSwitchArmedEvent) -> None:
        # Cancel open orders per scope; refuse new orders
        ...

    def on_disarmed(self, event: KillSwitchDisarmEvent) -> None:
        # Re-enable order acceptance per scope
        ...

bus = KillSwitchBus.get_instance()  # singleton per-process
bus.subscribe(ExecutionMatchingEngineSubscriber())
```

**Subscriber contract**:

- Subscribers MUST be idempotent. Re-emitted events are valid (process restart replay; bus reconstructs from audit log).
- Subscribers MUST NOT raise on event consumption. Failures are logged + counted in `KillSwitchBus.fan_out_failures` but
  never propagate to the publisher.
- Subscribers SHOULD acknowledge state via a lifecycle event (`KILL_SWITCH_ACKED` per
  [`alerting.md`](/codex/03-observability/alerting.md)) so the operator-facing UI can render per-subscriber state.

## Multi-subscriber broadcast — execution / strategy / PBMS / alerting

The cutover wiring fans out every arm to four subscribers:

| Subscriber                           | Behaviour on `KillSwitchArmedEvent`                                                                                                             | Behaviour on `KillSwitchDisarmEvent`                                          |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `execution-service` matching engine  | Per scope: cancel open orders, refuse new orders.                                                                                               | Re-enable order acceptance.                                                   |
| `strategy-service` signal generators | Per scope: pause target-tracking, halt signal emission.                                                                                         | Resume target-tracking.                                                       |
| `position-balance-monitor-service`   | Mark reconcilers as "during kill switch" — non-blocking state queries continue, but reconciler-driven breaker arms are suppressed (no cascade). | Clear the suppression flag.                                                   |
| `alerting-service` notifier          | Emit `KILL_SWITCH_*` AlertCode with severity per provenance; route to PagerDuty + Telegram.                                                     | Emit `KILL_SWITCH_AUTO_RECOVERED` or `KILL_SWITCH_MANUAL_UNKILLED` AlertCode. |

Fan-out is **single-message-multi-subscriber** — all four callbacks invoked within the same `KillSwitchBus.arm()` call.
Subscribers ordering is deterministic (registration order) but no consumer depends on it; idempotent state machines
absorb any reordering.

## Wire from breaker → bus → subscriber

The end-to-end shape of a breaker-driven arm:

```
BreakerConfig fires (action=KILL_ALL)
    │
    ▼
breaker maps (scope, applies_to) → KillSwitchId per the per-archetype registry
    │
    ▼
KillSwitchBus.arm(KillSwitchArmRequest(
    switch_id=...,
    provenance=KillSwitchProvenance.BREAKER_AUTO,
    requested_by=f"{breaker_id}:{breaker_serial}",
    metadata={"correlation_id": ..., "threshold_observed": ...},
))
    │
    ▼
bus validates provenance gating; writes audit-log entry (GCS / local)
    │
    ▼
bus emits KillSwitchArmedEvent to every subscriber (synchronous fan-out)
    │
    ├── execution-service: cancel open orders + refuse new
    ├── strategy-service: pause target-tracking
    ├── position-balance-monitor: suppress reconciler-driven arms
    └── alerting-service: emit KILL_SWITCH_* AlertCode (severity per provenance)
    │
    ▼
breaker recovery loop runs per BreakerRecoveryMode:
    AUTO_COOLDOWN → re-evaluate guard every cooldown_seconds; on N green reads, call KillSwitchBus.disarm(...)
    MANUAL_UNKILL → wait for operator action via deployment-UI / CLI; operator call invokes KillSwitchBus.disarm(...)
    │
    ▼
bus writes disarm audit-log entry + emits KillSwitchDisarmEvent to every subscriber
```

For operator-initiated arms (`provenance=OPERATOR_MANUAL`), the flow starts at the deployment-UI kill-switch tab; the DR
plan Phase 7.A wires `/api/kill-switch/{id}/arm` + `/disarm` endpoints that construct the `KillSwitchArmRequest` + call
`KillSwitchBus.arm()`.

## Cross-link with alerting recovery events

The bus + alerting-service emit complementary events. Per the
[`alerting_service_live_rules_2026_05_07.md`](../../plans/active/alerting_service_live_rules_2026_05_07.md) plan (Round
1 UAC@a7a99b5 added two recovery AlertCodes):

| AlertCode                     | Emitted by                                                                             | Severity | Carried by `KillSwitchDisarmEvent`                               |
| ----------------------------- | -------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------- |
| `KILL_SWITCH_AUTO_RECOVERED`  | alerting-service consuming `KillSwitchDisarmEvent` with `recovery_mode=AUTO_COOLDOWN`. | INFO     | `cooldown_seconds_elapsed` + guard-evaluation trail in metadata. |
| `KILL_SWITCH_MANUAL_UNKILLED` | alerting-service consuming `KillSwitchDisarmEvent` with `recovery_mode=MANUAL_UNKILL`. | INFO     | `disarmed_by` (operator ID) in metadata.                         |

The bus is the source of the disarm event; the alerting AlertCode is the source of the operator-facing notification.
Both ship in the same logical cycle — operator sees the recovery notification via Telegram + UI simultaneously.

## Anti-patterns

- **Don't bypass the bus and call subscribers directly.** Every arm/disarm MUST go through `KillSwitchBus.arm()` /
  `KillSwitchBus.disarm()` so the audit log captures the event. Direct subscriber invocation skips the log and breaks
  post-mortem reconstruction.
- **Don't write to the audit log out-of-band.** The bus is the only writer. Out-of-band writes break the append-only
  invariant + the operator-facing event-ordering guarantee.
- **Don't subscribe asynchronously and assume order.** The bus is synchronous fan-out; subscribers run in registration
  order within the publisher's call stack. Asyncio queue + worker pool inside a subscriber is fine but doesn't change
  the bus contract.
- **Don't make subscribers raise.** Subscriber callbacks MUST swallow errors + log internally. A raising subscriber
  silently blocks fan-out to later subscribers (logged but not visible without inspecting
  `KillSwitchBus.fan_out_failures`).
- **Don't arm `KILL_ALL_LIVE` via `BREAKER_AUTO`.** Provenance gating refuses the request — `KILL_ALL_LIVE` is
  operator-only or scheduled-drill-only. Breaker cascades top out at per-archetype halts; full-platform halt is an
  operator decision.
- **Don't arm on the live bus from a chaos-drill / scenario runner.** Production-guarded by separate bus singletons
  (testnet + live); the chaos-drill cron only has a handle to testnet.
- **Don't emit `KillSwitchArmedEvent` for an already-armed switch as a "refresh".** Re-emission is allowed for replay
  but is NOT a refresh — subscribers consume idempotently. If you want to update metadata mid-arm, emit a separate
  custom event; don't re-arm.

## Cross-references

- Breaker taxonomy + per-archetype registry: [`circuit-breaker-rule-taxonomy.md`](circuit-breaker-rule-taxonomy.md).
- Breaker state machine + kill-switch propagation: [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md).
- Risk-controller seam: [`risk-breaker-seam.md`](risk-breaker-seam.md).
- Layer-4 ErrorAction routing: [`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md).
- Alerting AlertCode taxonomy: [`/codex/03-observability/alerting.md`](/codex/03-observability/alerting.md).
- UAC SSOT: `unified_api_contracts.canonical.crosscutting.kill_switch` (UAC@a7a99b5).
- UTL SSOT: `unified_trading_library.kill_switch.bus` (predates DR plan; audited in Phase 0.C).
- Plan:
  [`disaster_recovery_circuit_breakers_2026_05_10.md`](../../plans/archive/disaster_recovery_circuit_breakers_2026_05_10.md)
  Phase 2 (bus + audit-log) + Phase 7 (UI surface).
