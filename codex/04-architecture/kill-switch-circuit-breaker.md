---
scope: [engineer, admin]
---

# Kill Switch & Circuit Breaker

## Overview

Two distinct safety mechanisms at different scopes. The kill switch is a hard stop (system-wide or scoped to
client/strategy/venue). The circuit breaker is a per-venue adaptive protection layer. Together with the position drift
monitor and reconciliation health check, they form the autonomous recovery stack.

**Related docs:**

- `autonomous-recovery-matrix.md` — decision tree for every failure scenario
- `09-strategy/architecture-v2/cross-cutting/risk-gates.md` — health factor thresholds trigger progressive responses
- `04-architecture/execution-policy.md` — unwind cost estimation used by exit playbooks
- `03-observability/alerting.md` — alert routing (Telegram, PagerDuty) for safety events

---

## Kill Switch

### Ownership

- **State machine**: `execution-service` owns the kill switch state, persisted to disk
  (`/tmp/execution_kill_switch.json`) — survives process restarts.
- **PubSub propagation**: `alerting-service` publishes `KILL_SWITCH_ACTIVATED` to the `circuit-breaker-commands` PubSub
  topic, consumed by all services.
- **Scoping**: `KillSwitchScope` (UAC `risk_service`) supports composable scope: entity_type (company/client/account),
  strategy_type, venue, instrument_id.

### Activation

**Manual (human-triggered):**

```
POST /kill-switch/activate
{
  "reason": "Manual halt — suspected fat-finger order",
  "activated_by": "operator",
  "auto_deactivate_after_minutes": 30
}
```

**Automatic (system-triggered) — see `autonomous-recovery-matrix.md` for full decision tree:**

- Health factor < 1.0 → emergency close all (margin-health.md)
- Multi-leg compensation failure → circuit breaker force-open + kill switch on that venue
- Multi-venue circuit breaker cascade (>50% venues OPEN) → firm-wide STOP_NEW_ONLY
- Position drift CRITICAL (>5%) → STOP_NEW_ONLY on affected strategy
- Reconciliation + connectivity dual failure → firm-wide kill switch + CRITICAL PagerDuty

### Auto-Deactivation

Kill switch supports optional `auto_deactivate_after_minutes`. Checked on every `is_active()` call. When deadline
elapses, emits `KILL_SWITCH_AUTO_DEACTIVATED` and resumes normal operation. Use for temporary halts where you want
automatic recovery.

### Startup Behaviour

If kill switch is active when service starts, emits `KILL_SWITCH_BLOCKED_STARTUP` (CRITICAL severity). Service enters
503 mode — rejects all order submissions. Requires manual deactivation before trading resumes.

### Enforcement Point

```python
# execution_service/api/manual_instruction_api.py
if kill_switch.is_active():
    raise HTTPException(status_code=503, detail="Kill switch is active")
```

ALL order submission is blocked at the API gateway level. No orders reach the execution engine.

### Strategy-Service Behaviour During Kill Switch

When `KILL_SWITCH_ACTIVATED` event is received by strategy-service:

- **STOP_NEW_ONLY**: Strategy stops emitting new signals but does NOT attempt to close existing positions. Existing
  positions stay as-is. Strategy does NOT fight back to target position.
- **FAST_UNWIND / SLOW_UNWIND**: Strategy emits close instructions for all positions, then halts. Execution-service
  processes closes but rejects any new-position instructions.
- **DELTA_HEDGE**: Strategy emits hedge-only instructions to flatten delta. No new directional exposure.

**Critical rule:** During kill switch, strategy-service MUST NOT attempt to re-enter target positions. The kill switch
overrides strategy target state. Strategy pauses its target-tracking loop and only processes exit playbook instructions.

### Propagation Path

```
Kill Switch Activated (manual or automatic)
    |
    +---> execution-service (HALTED state, rejects all new orders, processes exit-only)
    |
    +---> strategy-service (stops signal emission, pauses target-tracking)
    |
    +---> alerting-service --> PagerDuty + Telegram
    |
    +---> circuit-breaker-commands PubSub --> all subscribing services halt
```

---

## Circuit Breaker

### Ownership

- **Per-venue state machine**: `execution-service/engine/circuit_breaker.py`
- **Cross-service propagation**: `alerting-service` subscribes to execution-service events and publishes
  `CIRCUIT_OPEN` (UAC `LifecycleEvent`) to `circuit-breaker-commands` topic.

### States

| State       | Description                                       | Behaviour                                  |
| ----------- | ------------------------------------------------- | ------------------------------------------ |
| `CLOSED`    | Normal operation.                                 | All orders proceed.                        |
| `DEGRADED`  | Failure rate >= 30%. Probabilistic throttling.    | Some orders dropped; alerts emitted.       |
| `OPEN`      | Failure rate >= 60% or consecutive threshold hit. | All orders blocked. Cooldown with backoff. |
| `HALF_OPEN` | Cooldown elapsed. Testing recovery.               | One probe order allowed; others blocked.   |

### State Transitions

```
CLOSED ----(failure_rate >= 30%)----> DEGRADED
DEGRADED --(failure_rate >= 60%)----> OPEN
OPEN ------(cooldown_elapsed)-------> HALF_OPEN
HALF_OPEN -(probe succeeds)---------> CLOSED  (consecutive_open_cycles reset)
HALF_OPEN -(probe fails)------------> OPEN    (cooldown doubles, exponential backoff)
```

### Thresholds (actual, from code)

| Parameter                         | Default | Notes                                            |
| --------------------------------- | ------- | ------------------------------------------------ |
| `failure_threshold`               | 5       | Consecutive failures before CLOSED -> OPEN       |
| `cooldown_seconds`                | 300     | Base cooldown in OPEN before HALF_OPEN probe     |
| `max_cooldown_seconds`            | 3600    | Cap on exponential backoff                       |
| `degraded_failure_rate_threshold` | 0.30    | 30% failure rate triggers DEGRADED               |
| `open_failure_rate_threshold`     | 0.60    | 60% failure rate triggers OPEN                   |
| `failure_rate_window`             | 20      | Sliding window size for failure rate calculation |
| `failure_rate_min_samples`        | 5       | Minimum samples before rate-based transitions    |

### Exponential Backoff

Each consecutive OPEN cycle doubles the cooldown: `base * 2^(cycles-1)`, capped at 3600s.

- Cycle 1: 300s
- Cycle 2: 600s
- Cycle 3: 1200s
- Cycle 4+: 3600s (cap)

Triggers `CIRCUIT_BREAKER_BACKOFF_ESCALATING` alert (UAC `AlertCode`) when cycle > 1. The underlying lifecycle event
remains `CIRCUIT_OPEN` (re-emitted on each cycle); the alerting-service applies the BACKOFF_ESCALATING AlertCode based
on the cycle counter in the event metadata.

### What Counts as a Failure

- Raw exceptions (timeout, connection error, OSError) → **YES**
- Authentication errors (401) → **YES**
- Server errors (5xx) → **YES**
- Rate limits (429) → **NO** (handled via separate backoff, not a venue health issue)
- `CanonicalRateLimitError` explicitly excluded from failure counting.

### External Force-Open

```python
# Other services can force a venue's circuit breaker open
from execution_service.engine.circuit_breaker import force_open
force_open(venue="binance", reason="Multi-leg compensation failed")
```

Also triggered via `CIRCUIT_OPEN` PubSub event from alerting-service.

### Multi-Venue Cascade → Kill Switch Escalation

When multiple venues for a strategy are simultaneously OPEN, the system cannot maintain its intended hedging. This
requires automatic escalation (see `autonomous-recovery-matrix.md` for implementation):

| Venues OPEN    | Action                                                             |
| -------------- | ------------------------------------------------------------------ |
| 1 venue        | Queue orders for that venue, hedge on other venues if possible     |
| >50% of venues | Auto-activate STOP_NEW_ONLY for affected strategies                |
| All venues     | Auto-activate firm-wide kill switch, CRITICAL PagerDuty + Telegram |

---

## Multi-Venue Kill Switch — Hedged Position Handling

### The Problem

Long on Binance + Short on Bybit. Lose Bybit connectivity. Can't buy back shorts on Bybit, but CAN sell longs on
Binance. What do you do?

### Decision Framework

The kill switch exit playbook must consider **net delta** across venues, not just positions on each venue:

1. **Delta-neutral goal**: Get to flat delta using whichever venues are still connected.
   - If strategy is long 1 BTC on Binance, short 1 BTC on Bybit, and Bybit is down:
     - Sell the 1 BTC on Binance → now flat (0 delta) with 1 BTC short orphaned on Bybit
     - When Bybit recovers → buy back the short
   - This costs 1 round-trip transaction instead of 2 (vs waiting for both venues)

2. **Gross vs net consideration**: Getting to delta-neutral (net) is cheaper than closing everything (gross).
   - Closing everything: sell Binance long ($X slippage) + wait for Bybit to buy back short ($Y slippage)
   - Getting to delta-neutral: sell Binance long only ($X slippage), orphan the short
   - The orphaned short is risk-free in delta terms (it's hedged by being flat everywhere else)
   - BUT: the orphaned short still has venue risk (Bybit liquidation, margin call)

3. **Who decides?**
   - **Execution-service** decides the mechanics: which orders to send, to which venues
   - **Strategy-service** decides the intent: "get to delta-neutral" vs "close everything"
   - **Config per strategy** declares the exit preference: `exit_mode: delta_neutral | full_close`
   - During kill switch, strategy's target-tracking is PAUSED — it does NOT fight the exit

4. **What if strategy-service is also down?**
   - Execution-service has the emergency exit playbooks (UAC `EmergencyExitPlaybook`)
   - Each strategy type has a pre-declared playbook with ordered steps
   - Execution-service can execute the playbook autonomously without strategy-service
   - This is the "system takes care of itself" path

### Configuration Per Strategy

```python
# UAC EmergencyExitPlaybook
EmergencyExitPlaybook(
    strategy_type="basis_trade",
    exit_type=EmergencyExitType.DELTA_HEDGE,  # get to delta-neutral, not full close
    steps=[
        EmergencyExitStep(order=1, action="flatten_delta", urgency="immediate", max_slippage_bps=50),
        EmergencyExitStep(order=2, action="close_orphaned", urgency="queued", max_slippage_bps=20),
    ],
    description="Flatten delta on available venues; queue orphan close for venue recovery",
)
```

Step 1 runs immediately on available venues. Step 2 is queued — executes when the disconnected venue recovers.

---

## Reconciliation as a Pre-Close Gate

### The Rule

Before executing any exit playbook, the system MUST verify reconciliation health:

```
Can reconcile?  Can execute?  Action
─────────────  ────────────  ──────
    YES            YES        Execute exit playbook normally
    YES            NO         Alert CRITICAL (connectivity loss) — positions verified but can't act
    NO             YES        Execute with CAUTION flag — verify post-close, alert WARNING
    NO             NO         DUAL_FAILURE — CRITICAL PagerDuty, human required
```

**Reconciliation healthy** means: PBMS successfully queried venue balances within the last 60s and position counts match
between internal state and venue state.

**When reconciliation is broken but execution works**: You can close positions, but you should verify the close went
through by checking venue state after execution. Emit `RECON_DEGRADED_CLOSE` event for audit trail.

**When both are broken (the 0.1%)**: Positions are frozen. No automatic action is safe. Emit `DUAL_FAILURE_DETECTED`
(CRITICAL, PagerDuty + Telegram) with explicit message: "Positions may be stale — human verification required on [venue]
before any action."

---

## PubSub Events

| Event                               | Published by      | Severity | Subscribers                    |
| ----------------------------------- | ----------------- | -------- | ------------------------------ |
| `KILL_SWITCH_ACTIVATED`             | execution-service | CRITICAL | All services, alerting         |
| `KILL_SWITCH_DEACTIVATED`           | execution-service | INFO     | All services, alerting         |
| `KILL_SWITCH_AUTO_DEACTIVATED`      | execution-service | WARNING  | All services, alerting         |
| `KILL_SWITCH_BLOCKED_STARTUP`       | execution-service | CRITICAL | Alerting                       |
| `CIRCUIT_OPEN`                      | execution-service | ERROR    | Alerting, all services         |
| `CIRCUIT_HALF_OPEN`                 | execution-service | WARNING  | Alerting                       |
| `CIRCUIT_CLOSED`                    | execution-service | INFO     | Alerting, all services         |
| `POSITION_DRIFT_DETECTED`           | PBMS              | HIGH     | Alerting, UI                   |
| `UNHEDGED_POSITION_ALERT`           | execution-service | CRITICAL | Alerting                       |
| `MULTI_LEG_COMPENSATION_FAILED`     | execution-service | CRITICAL | Alerting                       |

> **Lifecycle vs Alert taxonomy.** The events above are UAC `LifecycleEvent` enum members emitted via `log_event()`. The
> alerting-service derives UAC `AlertCode` taxonomy from these (`CIRCUIT_BREAKER_OPEN`, `CIRCUIT_BREAKER_DEGRADED`,
> `CIRCUIT_BREAKER_CLOSED`, `CIRCUIT_BREAKER_BACKOFF_ESCALATING`) for routing rules — see `03-observability/alerting.md`.
> The two enums have different naming on purpose: lifecycle events are short-form (`CIRCUIT_OPEN`); AlertCodes prefix
> with the subsystem (`CIRCUIT_BREAKER_*`) for pattern-routing in `alerting-service/notifiers/router.py`.

---

## Related

- `autonomous-recovery-matrix.md` — full decision tree for every failure scenario
- `09-strategy/architecture-v2/cross-cutting/risk-gates.md` — health factor thresholds and progressive responses
- `04-architecture/execution-policy.md` — unwind cost estimation for exit playbooks
- `05-infrastructure/disaster-recovery.md` — infrastructure-level DR (RTO/RPO, rollback procedures)
- `03-observability/alerting.md` — alert routing rules (Telegram, PagerDuty)
- `03-observability/lifecycle-events.md` — mandatory event sequences during failures
