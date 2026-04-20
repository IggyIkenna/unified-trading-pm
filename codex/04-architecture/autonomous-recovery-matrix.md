---
scope: [engineer, admin]
---

# Autonomous Recovery Matrix

## Principle

The system takes care of itself 99.9% of the time through retries, circuit breakers, compensation trades, and automatic
position management. Human intervention is only required when both reconciliation AND execution connectivity are lost
simultaneously — the 0.1% case.

**Live-mode only.** All recovery mechanisms are disabled in batch/backtest.

---

## Error Classification → Action Routing

Every error flows through UAC `classify_venue_error()` which maps to one of four actions:

| ErrorAction | Meaning                        | Example errors                           | System response                                      |
| ----------- | ------------------------------ | ---------------------------------------- | ---------------------------------------------------- |
| `RETRY`     | Transient, will likely succeed | 429 rate limit, 5xx, gas estimation fail | Exponential backoff (3 attempts), then circuit break |
| `RECONNECT` | Connection lost                | Timeout, connection reset, RPC error     | Rebuild connection, retry on new connection          |
| `SKIP`      | No-op, not an error            | No outstanding debt (trying to repay)    | Log as INFO, continue processing                     |
| `FAIL`      | Permanent, cannot recover      | Auth failure, insufficient balance       | Stop immediately, emit alert, escalate               |

Rate limits (429) explicitly do NOT trip circuit breakers — they're transient and handled via backoff.

---

## Decision Tree

```
ERROR DETECTED
|
+-- classify_venue_error(venue, error_code)
|   |
|   +-- RETRY ------> Exponential backoff (3 attempts)
|   |                  |
|   |                  +-- All retries fail --> Circuit breaker records failure
|   |                                          |
|   |                                          +-- failure_rate < 30% --> CLOSED (normal)
|   |                                          +-- failure_rate >= 30% --> DEGRADED (throttle)
|   |                                          +-- failure_rate >= 60% --> OPEN (blocked)
|   |
|   +-- RECONNECT --> Rebuild connection, retry once
|   |                  |
|   |                  +-- Reconnect fails --> Circuit breaker failure
|   |
|   +-- SKIP -------> Log INFO, continue
|   |
|   +-- FAIL -------> Stop operation, emit ADAPTER_FETCH_FAILED
|                      Alert via Telegram
|
+-- CIRCUIT BREAKER STATE
|   |
|   +-- Single venue OPEN
|   |   |
|   |   +-- Other venues available --> Queue orders, hedge elsewhere
|   |   +-- Strategy has positions on this venue only --> Alert WARNING
|   |   +-- Exponential backoff: 300s -> 600s -> 1200s -> 3600s
|   |   +-- HALF_OPEN probe after cooldown
|   |       +-- Probe succeeds --> CLOSED (recovery)
|   |       +-- Probe fails --> OPEN (backoff doubles)
|   |
|   +-- Multiple venues OPEN (>50% for a strategy)
|   |   |
|   |   +-- AUTO: STOP_NEW_ONLY on affected strategies  [G1]
|   |   +-- Alert Telegram + PagerDuty (CRITICAL)
|   |   +-- Strategy-service pauses target-tracking
|   |
|   +-- ALL venues OPEN
|       |
|       +-- AUTO: Firm-wide kill switch
|       +-- Alert PagerDuty (CRITICAL) + Telegram
|       +-- "No execution capability — all positions frozen"
|
+-- MULTI-LEG PARTIAL FILL
|   |
|   +-- Leader fills, follower fails after retries
|   |   |
|   |   +-- Emit UNHEDGED_POSITION_ALERT (CRITICAL)
|   |   +-- auto_unwind_enabled?
|   |       +-- YES --> Compensation trade (opposite side on leader venue)
|   |       |          +-- Compensation succeeds --> Done (leader UNWOUND)
|   |       |          +-- Compensation fails --> MULTI_LEG_COMPENSATION_FAILED
|   |       |                                     force_open(venue) circuit breaker
|   |       |                                     CRITICAL PagerDuty + Telegram
|   |       +-- NO --> Alert only, human must decide
|   |
|   +-- Both legs fail --> No exposure, retry from scratch
|
+-- HEALTH FACTOR BREACH (margin-health.md)
|   |
|   +-- HF > 2.0 -------> HEALTHY, no action
|   +-- HF 1.5-2.0 -----> ELEVATED: strategy reduces exposure
|   +-- HF 1.2-1.5 -----> WARNING: strategy pauses new entries
|   +-- HF 1.0-1.2 -----> CRITICAL: auto-deleverage triggered
|   +-- HF < 1.0 -------> EMERGENCY: close all positions on venue
|                          Kill switch on strategy
|                          CRITICAL PagerDuty + Telegram
|
+-- POSITION DRIFT DETECTED (new, from reconciliation work)
|   |
|   +-- deviation < 2% --> NORMAL, log only
|   +-- deviation 2-5% --> WARNING: Telegram alert, visible in Observe tab
|   +-- deviation > 5% --> CRITICAL:  [G4]
|       +-- AUTO: STOP_NEW_ONLY on affected strategy
|       +-- Telegram + PagerDuty alert
|       +-- Strategy-service pauses target-tracking for this strategy
|       +-- Human reviews in Observe tab, decides to close or wait
|
+-- RECONCILIATION FAILURE
    |
    +-- Check: can_reconcile? can_execute?
    |
    +-- YES / YES --> Normal operations
    |
    +-- YES / NO ---> Connectivity loss to exchange execution
    |                 Can verify positions but can't act
    |                 Alert CRITICAL: "Execution path down, positions verified"
    |                 Wait for circuit breaker recovery
    |
    +-- NO / YES ---> Reconciliation broken, execution works  [G2]
    |                 CAN close positions but flying blind
    |                 Emit RECON_DEGRADED flag on all operations
    |                 Post-close: force reconciliation check
    |                 Alert WARNING: "Closing without verified position state"
    |
    +-- NO / NO ----> DUAL FAILURE (the 0.1%)  [G3]
                      Positions frozen, no safe automatic action
                      Emit DUAL_FAILURE_DETECTED (CRITICAL)
                      PagerDuty P1 + Telegram with explicit message:
                      "Human intervention required -- cannot reconcile or execute
                       on [venue]. Positions may be stale. Verify on exchange
                       directly before taking any action."
                      Kill switch activated (prevent any automated attempts)
```

---

## Multi-Venue Hedged Position Kill Switch

### The Problem

Strategy has long 1 BTC on Binance + short 1 BTC on Bybit (delta-neutral basis trade). Bybit goes down.

### Resolution Options

| Option                         | Action                                | Delta After                                 | Cost                          | Risk                                  |
| ------------------------------ | ------------------------------------- | ------------------------------------------- | ----------------------------- | ------------------------------------- |
| **A. Wait**                    | Do nothing until Bybit recovers       | 0 (unchanged)                               | $0                            | Bybit margin call if price moves      |
| **B. Delta-neutral exit**      | Sell Binance long, orphan Bybit short | 0 → still 0 (net) but -1 BTC gross on Bybit | 1 trade slippage              | Bybit short margin if price drops     |
| **C. Full close on available** | Sell Binance long                     | +0 Binance, -1 Bybit = -1 BTC net           | 1 trade slippage              | Directional risk until Bybit recovers |
| **D. Hedge on 3rd venue**      | Short 1 BTC on OKX to cover Bybit     | 0 (3-venue flat)                            | 1 trade slippage + OKX margin | Complexity, 3 venues to unwind later  |

### Decision Logic

The strategy config declares `exit_mode` per strategy type:

```
exit_mode: delta_neutral   --> Option B: flatten delta on available venues, orphan rest
exit_mode: full_close      --> Option C: close everything possible, accept directional risk
exit_mode: wait            --> Option A: do nothing, rely on circuit breaker recovery
exit_mode: hedge_cross     --> Option D: hedge on a third venue
```

Default for most strategies: `delta_neutral` — cheapest and maintains risk neutrality.

### Who Decides What

| Component             | Decides                                                 | During kill switch                     |
| --------------------- | ------------------------------------------------------- | -------------------------------------- |
| **Strategy-service**  | Target position, exit_mode preference                   | PAUSED — does NOT fight back to target |
| **Execution-service** | Which orders to send, to which venues, in what sequence | ACTIVE — executes exit playbook        |
| **PBMS**              | Position verification, drift detection                  | ACTIVE — monitors post-exit state      |
| **Config (UAC)**      | Emergency exit playbook per strategy type               | Pre-declared, no runtime decision      |

**Critical rule:** During kill switch, strategy-service's target-tracking loop is PAUSED. It does NOT attempt to
re-enter its target position. This prevents the strategy from fighting the exit (e.g., strategy wants to maintain basis
trade, but kill switch is closing it).

### What If Strategy-Service Is Down?

Execution-service has the emergency exit playbooks from UAC. Each strategy type has a pre-declared playbook with ordered
steps. Execution-service can execute the playbook autonomously. The playbook is the "system takes care of itself" path
that doesn't require strategy-service to be running.

---

## Recovery Timeline

```
T+0s    Error detected, classify_venue_error()
T+0-5s  Retry with backoff (if RETRY action)
T+5-15s Circuit breaker evaluates failure rate
T+15s   If DEGRADED: throttle orders, emit alert
T+30s   If OPEN: block venue, start cooldown, emit CRITICAL alert
T+30s   Telegram + PagerDuty notification delivered
T+300s  HALF_OPEN probe (first attempt)
T+300s  If probe succeeds: CLOSED, resume normal
T+600s  If probe fails: backoff doubles (next probe at T+900s)
...
T+3600s Maximum backoff cap reached
```

For multi-venue cascade:

```
T+0s    First venue OPEN
T+30s   Alert: "Venue X circuit breaker OPEN"
T+300s  Second venue OPEN (>50% threshold)
T+300s  AUTO: STOP_NEW_ONLY on affected strategies
T+300s  PagerDuty CRITICAL: "Multiple venues down"
```

---

## Alerting Channels by Severity

| Scenario                    | Telegram | PagerDuty      | UI (Observe) | Auto-Action             |
| --------------------------- | -------- | -------------- | ------------ | ----------------------- |
| Single venue DEGRADED       | Yes      | No             | Yes          | Throttle orders         |
| Single venue OPEN           | Yes      | No             | Yes          | Block venue, backoff    |
| Multi-venue OPEN (>50%)     | Yes      | Yes (CRITICAL) | Yes          | STOP_NEW_ONLY           |
| All venues OPEN             | Yes      | Yes (P1)       | Yes          | Firm-wide kill switch   |
| Multi-leg compensation fail | Yes      | Yes (CRITICAL) | Yes          | force_open(venue)       |
| Health factor < 1.0         | Yes      | Yes (CRITICAL) | Yes          | Emergency close all     |
| Position drift CRITICAL     | Yes      | Yes            | Yes          | STOP_NEW_ONLY           |
| Recon degraded close        | Yes      | No             | Yes          | Close with CAUTION flag |
| Dual failure (recon + exec) | Yes      | Yes (P1)       | Yes          | Kill switch + freeze    |
| Kill switch activated       | Yes      | Yes (CRITICAL) | Yes          | Block all orders        |

---

## Gap Implementation Status

| ID  | Gap                                                            | Status  | Implementation                                                              |
| --- | -------------------------------------------------------------- | ------- | --------------------------------------------------------------------------- |
| G1  | Circuit breaker → kill switch escalation (multi-venue cascade) | PLANNED | execution-service: monitor venue breaker states, auto STOP_NEW_ONLY at >50% |
| G2  | Reconciliation as pre-close gate                               | PLANNED | execution-service: check PBMS recon health before exit playbook             |
| G3  | Dual failure event (recon + exec both down)                    | PLANNED | PBMS: detect when both are broken, emit DUAL_FAILURE_DETECTED               |
| G4  | Position drift → auto STOP_NEW_ONLY                            | PLANNED | PBMS: on CRITICAL drift, call execution-service kill switch API             |
| G5  | Connectivity loss → mark recon as stale                        | PLANNED | PBMS: subscribe to CIRCUIT_BREAKER_OPEN, mark venue recon as unreliable     |
| G6  | Playbook-to-scenario mapping                                   | PLANNED | UAC: map EmergencyExitType to trigger scenarios in config                   |

---

## Related

- `kill-switch-circuit-breaker.md` — detailed kill switch and circuit breaker mechanics
- `09-strategy/architecture-v2/cross-cutting/risk-gates.md` — health factor thresholds
- `04-architecture/execution-policy.md` — unwind cost estimation
- `05-infrastructure/disaster-recovery.md` — infrastructure DR (RTO/RPO, rollback)
- `03-observability/alerting.md` — alert routing rules
- `reconciliation-resolution.md` — reconciliation break resolution workflow
