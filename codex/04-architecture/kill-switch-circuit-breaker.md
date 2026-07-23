---
doc_type: codex-ssot
title: Kill Switch & Circuit Breaker
summary:
  "Two safety mechanisms: the kill switch (hard stop, composable scope down to KILL_PER_WALLET) enforced at the
  execution-service API 503 gate, and the per-venue circuit breaker (CLOSED / DEGRADED / OPEN / HALF_OPEN with
  exponential backoff). Three independent + idempotent breaker input axes; multi-venue cascade escalates to firm-wide
  STOP_NEW_ONLY / kill switch."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: [execution, kill-switch, circuit-breaker, defi, cefi, reconciliation, self-healing, ssot]
related:
  [
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/kill-switch-event-bus.md,
    /codex/04-architecture/circuit-breaker-rule-taxonomy.md,
    /codex/04-architecture/risk-breaker-seam.md,
    /codex/04-architecture/manual-trade-booking.md,
  ]
created: 2026-03-27
authoritative_for:
  [
    kill-switch state machine and scoping,
    circuit-breaker state machine and transitions,
    wallet-tier KILL_PER_WALLET semantics,
    multi-venue kill-switch hedged-position handling,
  ]
referenced_by:
  [
    /codex/04-architecture/account-instructions.md,
    /codex/04-architecture/alerting-batch-live.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/circuit-breaker-rule-taxonomy.md,
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/kill-switch-event-bus.md,
    /codex/04-architecture/manual-trade-booking.md,
    /codex/04-architecture/mev-protection.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
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
- [`risk-rule-taxonomy.md`](risk-rule-taxonomy.md) — closed-set vocabulary for Layer 2 pre-flight rules
- [`risk-preflight-flow.md`](risk-preflight-flow.md) — every-order pre-flight aggregation semantics
- [`risk-breaker-seam.md`](risk-breaker-seam.md) — risk-controller → breaker escalation event contract
- [`manual-trade-booking.md`](manual-trade-booking.md) § "Wallet-tier wiring (DeFi manual trades)" — wallet-tier
  kill-switch + spending-cap pre-trade audit-log invariant (every `KILL_PER_WALLET` fire produces a
  `WalletSpendingPreCheckResult` row, UAC@`1d8a059` slot 8 2026-05-12)

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

### Wallet-tier kill-switch (`KILL_PER_WALLET`)

**Added 2026-05-12** (slot 4 UAC@`d721b6a`) per `api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 5.

`KILL_PER_WALLET` is the **FINEST-grain switch** in the closed `KillSwitchId` set — sits _below_ per-venue and
per-archetype. The 5-axis kill-switch hierarchy is now:

```
KILL_ALL_LIVE  (GLOBAL)
   └─ KILL_PER_ASSET_GROUP_{CEFI,DEFI}  (asset-group filter)
       └─ KILL_PER_ARCHETYPE_{CARRY_STAKED_BASIS, ARBITRAGE_PRICE_DISPERSION}  (ARCHETYPE)
           └─ KILL_PER_VENUE_{BYBIT, DERIBIT, BINANCE, OKX, HYPERLIQUID, ASTER}  (VENUE)
               └─ KILL_PER_WALLET  (per-wallet — runtime-targeted via target_wallet_id)
```

**Runtime-targeting semantics.** Unlike per-archetype / per-venue (which dispatch on the `switch_id` enum alone),
`KILL_PER_WALLET` carries a `target_wallet_id` string field on `KillSwitchArmRequest` (UAC@`d721b6a`). The bus
validates: `target_wallet_id` MUST be non-empty when `switch_id == KILL_PER_WALLET`; MUST be empty otherwise. This
avoids an enum-per-wallet explosion (we provision many DeFi wallets per archetype) while preserving the closed-set
discipline at the switch-axis level.

**`KillSwitchScope` mapping.** `KillSwitchScope` (UAC `alerting/codes.py`) has **no `WALLET` member** today. The wallet
axis is runtime-targeted, parallel to the per-asset-group convention (where `KILL_PER_ASSET_GROUP_*` enum values exist
but there's no `KillSwitchScope.ASSET_GROUP` — at runtime the consumer maps to `GLOBAL` filtered by asset_group). The
`unified_api_contracts.canonical.crosscutting.kill_switch.KillSwitchId.KILL_PER_WALLET` docstring currently references
`KillSwitchScope.WALLET` — see audit findings R-5 / AL-1 for the slot 4 reconciliation (add `WALLET` enum member OR fix
docstring to "runtime-targeted, no enum equivalent").

**Halt semantics.** When armed:

- Engages **only the named wallet's signing surface** (the wallet's private-key Web3 / ECDSA / sequencer client).
- **Leaves sibling wallets** of the same archetype, venue, asset-group unaffected.
- Composes with `WalletProvisioningConfig.kill_switch_id` (UAC `internal/domain/defi/wallet_config.py`): set to
  `"KILL_PER_WALLET"` for wallet-level freezes; broader prefixes (`KILL_PER_VENUE_*` / `KILL_PER_ARCHETYPE_*` /
  `KILL_ALL_LIVE`) cascade through this wallet too.
- Composes with `SpendingCaps` (per-tx / per-hour / per-day / per-protocol — UAC `wallet_config.py:106-141`).
  Spending-cap exceedance fires `WALLET_CAP_EXCEEDED` AlertCode (see audit finding R-6 / AL-2 — missing today; slot 4
  follow-up).

**Audit-log invariant.** Every `KILL_PER_WALLET` arm / pre-trade check produces a `WalletSpendingPreCheckResult` row
(UAC `internal/execution.py:192-232`, slot 8 UAC@`1d8a059` 2026-05-12). See
[`manual-trade-booking.md`](manual-trade-booking.md) § "Wallet-tier wiring (DeFi manual trades)" for the validation
algorithm + the `ManualInstructionPrecheckResponse` consumer surface.

**Operator UX.** DART `ManualTradingPanel` "DeFi Action" tab ships a per-row kill-switch button for arming / unkilling
`KILL_PER_WALLET` per wallet_id (Phase 5 slot 8). See [`manual-trade-booking.md`](manual-trade-booking.md) § "DART
operator UI".

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
- **Cross-service propagation**: `alerting-service` subscribes to execution-service events and publishes `CIRCUIT_OPEN`
  (UAC `LifecycleEvent`) to `circuit-breaker-commands` topic.

> **Verified NON-finding (UTL/UAC reuse audit, 2026-07-13)**: this per-venue order circuit breaker is DISTINCT from
> `unified_trading_library.circuit_breaker` (UTL). UTL's package is the DR-plan `BreakerRecoveryEngine` — a pure
> disarm/auto-cooldown decision engine over the UAC `CircuitBreakerId`/`BreakerConfig` taxonomy, wired to the
> kill-switch bus (see `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 5). It does not observe per-venue order
> failure rates and cannot replace the CLOSED/DEGRADED/OPEN/HALF_OPEN state machine below. Do not re-flag this as a
> duplicate in a future reuse audit. SSOT: `plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md` line
> 176-179 (verified NON-findings list).

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

### Risk-Rule Fire → Breaker Arm Cross-Link

The circuit breaker has a SECOND transition cause beyond venue-rejection rates: the **risk-controller → breaker
escalation seam**. When `risk_preflight()` accumulates N consecutive `RiskRuleConsequence.SCALE_DOWN` fires on the same
`(venue, asset_group)` within a rolling window W, the risk-controller emits `BREAKER_ESCALATION_REQUESTED` to
`circuit-breaker-commands`. The breaker subscribes and transitions per the UAC-declared
`RISK_TO_BREAKER_ESCALATION_MAP: dict[(RiskRuleConsequence, int, timedelta), BreakerAction]`.

This is **distinct from venue-rejection-rate-driven transitions** and lives in a separate enum domain — see
[`risk-breaker-seam.md`](risk-breaker-seam.md) for the full layering contract. Key points:

- The risk-controller emits the event; the breaker subscribes. No direct invocation.
- Both transition causes are independent — a single SCALE_DOWN at Layer 2 does NOT engage the breaker (only N-in-W
  does).
- A breaker already in DEGRADED via venue-rejection-rate is unaffected by a fresh seam event for DEGRADED — the
  transition is idempotent.

### `BreakerRecoveryMode` — Manual vs Auto-Cooldown (UAC@a7a99b5)

Each `BreakerConfig` carries a `recovery_mode: BreakerRecoveryMode` field with closed set
`{manual_unkill, auto_cooldown}` plus `cooldown_seconds: int | None` (None when manual). Per-action defaults from
`BREAKER_RECOVERY_DEFAULTS`:

| `BreakerAction` | Default recovery mode | Rationale                                                                |
| --------------- | --------------------- | ------------------------------------------------------------------------ |
| `BLOCK_NEW`     | `auto_cooldown`       | Least-restrictive; safe to auto-resume when metric clears.               |
| `SCALE_DOWN`    | `auto_cooldown`       | Partial unwind has a natural inverse — auto-resume on green guard reads. |
| `CANCEL_OPEN`   | `manual_unkill`       | Cancelled orders are gone; auto-recovery doesn't restore them.           |
| `KILL_ALL`      | `manual_unkill`       | Full unwind needs operator sign-off before any new sizing.               |

Recovery emits one of two AlertCodes:

- `KILL_SWITCH_AUTO_RECOVERED` — guard predicate green for the cooldown window; carries `recovered_after_seconds` +
  guard-evaluation trail.
- `KILL_SWITCH_MANUAL_UNKILLED` — operator action via deployment-UI or `kill-switch unkill` CLI; carries
  `unkilled_by_operator_id`.

The risk-controller does not observe recovery state — once the breaker auto-recovers or is operator-unkilled, subsequent
Layer 2 SCALE_DOWNs start a fresh rolling-window for the seam.

### Per-state-surface reconciler outputs feed breaker triggers

In addition to venue-rejection-rate sliding-windows (the classic state machine above) and risk-controller seam events
(per [`risk-breaker-seam.md`](risk-breaker-seam.md)), circuit breakers consume a third input axis: **per-state-surface
reconciler drift events**. The
[`disaster_recovery_circuit_breakers_2026_05_10.md`](../../plans/archive/disaster_recovery_circuit_breakers_2026_05_10.md)
Phase 3 ships 8 reconcilers, each emitting typed drift events that the matching `CircuitBreakerId` subscribes to.

| Reconciler                                             | What it diffs                                                                                      | Drift event feeds breaker                                                                            |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Position reconciler** (Phase 3.A)                    | `position-balance-monitor-service` internal state vs venue REST + custody endpoint per-instrument. | `POSITION_LIMIT_EXCEEDED` — position drift > tolerance fires breaker with `CANCEL_OPEN` action.      |
| **Balance reconciler** (Phase 3.B)                     | Per-account total balance: internal accumulator vs venue balance endpoint.                         | `HEDGE_GAP_NOTIONAL_USD` — balance drift > USD threshold fires breaker.                              |
| **Custody reconciler** (Phase 3.C)                     | Copper + CEFFU ping success + balance vs internal record.                                          | `CUSTODY_DISCONNECT_SECONDS` — failed ping over threshold seconds fires `BLOCK_NEW`.                 |
| **On-chain reconciler** (Phase 3.D)                    | Wallet on-chain balance vs `position-balance-monitor` per-chain accumulator.                       | `POSITION_LIMIT_EXCEEDED` (chain-scoped) — drift > tolerance fires breaker.                          |
| **Event reconciler** (Phase 3.E)                       | Event-stream count + sequence vs expected per service (gaps / out-of-order events).                | `CLOCK_SKEW_MS` (sequence proxy) + per-service health breakers — gap fires `BLOCK_NEW`.              |
| **Manifest reconciler** (Phase 3.F)                    | Phantom audit (per CLAUDE.md "Manifest phantom audit"); wired as nightly cron.                     | `MANIFEST_PHANTOM_RATE_BPS` — phantom rate > threshold bps fires breaker.                            |
| **Order-state reconciler** (Phase 3.G)                 | Internal order state vs venue order state per-instrument.                                          | `REJECT_RATE_BPS` (order-state drift proxy) — drift > bps fires `BLOCK_NEW`.                         |
| **PnL + clock + batch-vs-live reconciler** (Phase 3.H) | PnL invariant + clock-skew + UTL@908b1647 batch-vs-live divergence.                                | `BATCH_LIVE_DIVERGENCE_BPS` + `CLOCK_SKEW_MS` + `PNL_VARIANCE_SIGMA` — each subscribes to its slice. |

The three input axes are **independent + idempotent**. A single root cause that fires from multiple inputs (e.g. venue
outage tripping rejection-rate AND custody reconciler) results in idempotent state transitions — CLOSED → DEGRADED is a
no-op if already DEGRADED. The breaker state machine is the deduplication boundary; reconcilers don't coordinate among
themselves.

Per [`circuit-breaker-rule-taxonomy.md`](circuit-breaker-rule-taxonomy.md) § "Trigger sources — three input axes", every
`CircuitBreakerId` declares which axis or axes it subscribes to in the per-archetype registry seed. Reconciler-driven
breakers (manifest / batch-live / position-drift / balance / custody / clock) are explicit in their `description` field.

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

| Event                           | Published by      | Severity | Subscribers               |
| ------------------------------- | ----------------- | -------- | ------------------------- |
| `KILL_SWITCH_ACTIVATED`         | execution-service | CRITICAL | All services, alerting    |
| `KILL_SWITCH_DEACTIVATED`       | execution-service | INFO     | All services, alerting    |
| `KILL_SWITCH_AUTO_DEACTIVATED`  | execution-service | WARNING  | All services, alerting    |
| `KILL_SWITCH_BLOCKED_STARTUP`   | execution-service | CRITICAL | Alerting                  |
| `KILL_SWITCH_AUTO_RECOVERED`    | execution-service | INFO     | Alerting                  |
| `KILL_SWITCH_MANUAL_UNKILLED`   | execution-service | INFO     | Alerting                  |
| `BREAKER_ESCALATION_REQUESTED`  | risk-and-exposure | WARNING  | Execution circuit breaker |
| `CIRCUIT_OPEN`                  | execution-service | ERROR    | Alerting, all services    |
| `CIRCUIT_HALF_OPEN`             | execution-service | WARNING  | Alerting                  |
| `CIRCUIT_CLOSED`                | execution-service | INFO     | Alerting, all services    |
| `POSITION_DRIFT_DETECTED`       | PBMS              | HIGH     | Alerting, UI              |
| `UNHEDGED_POSITION_ALERT`       | execution-service | CRITICAL | Alerting                  |
| `MULTI_LEG_COMPENSATION_FAILED` | execution-service | CRITICAL | Alerting                  |

> **Lifecycle vs Alert taxonomy.** The events above are UAC `LifecycleEvent` enum members emitted via `log_event()`. The
> alerting-service derives UAC `AlertCode` taxonomy from these (`CIRCUIT_BREAKER_OPEN`, `CIRCUIT_BREAKER_DEGRADED`,
> `CIRCUIT_BREAKER_CLOSED`, `CIRCUIT_BREAKER_BACKOFF_ESCALATING`) for routing rules — see
> `03-observability/alerting.md`. The two enums have different naming on purpose: lifecycle events are short-form
> (`CIRCUIT_OPEN`); AlertCodes prefix with the subsystem (`CIRCUIT_BREAKER_*`) for pattern-routing in
> `alerting-service/notifiers/router.py`.

> **Wallet-tier kill-switch ↔ manual-trade audit-log invariant (2026-05-12).** Every `KILL_PER_WALLET` arm AND every
> wallet-tier pre-trade check produces a `WalletSpendingPreCheckResult` audit-log row (UAC
> `internal/execution.py:192-232`, slot 8 UAC@`1d8a059`). See [`manual-trade-booking.md`](manual-trade-booking.md) §
> "Wallet-tier wiring (DeFi manual trades)" for the validation algorithm + DART operator-UI integration. The audit log
> is the SSOT for "did the wallet-tier kill-switch / spending-cap actually engage on this manual trade attempt?" —
> distinct from the PubSub `KILL_SWITCH_*` event fanout (which is the runtime-halt signal, not the per-attempt audit
> trail).

---

## Scenario-driven trips

The `ScenarioRunner` (UTL `unified_trading_library.scenario.runner`) validates breaker and kill-switch rules by
injecting synthetic `ScenarioOverlay` conditions at the features layer. Each overlay carries `synthetic=true` in its
event payload; downstream consumers (strategy-service, execution-service) handle it identically to real data, so the
full kill-switch propagation path exercises.

**How a scenario trip works:**

1. `ScenarioRunner.run(scenario_id, archetype)` applies the overlay via `ScenarioOverlayApplier` — e.g., forces
   `HEALTH_FACTOR < 1.0` or `failure_rate >= 0.60` on a venue.
2. The modified tick propagates through the normal pipeline (features → strategy → execution).
3. `ScenarioOutcomeAssertion` checker verifies the expected breaker / kill-switch event fires within the assertion
   window.
4. `ScenarioReport.all_passed` is the pass/fail gate. `synthetic=true` events are excluded from P&L attribution.

**Per-rule expected-trip mapping (selected):**

| Scenario ID (`UAC registry/scenarios/`)     | Breaker / switch that MUST fire             | Kill-switch scope    |
| ------------------------------------------- | ------------------------------------------- | -------------------- |
| `DEFI_AAVE_HEALTH_FACTOR_BREACH_1_05`       | `KILL_PER_ARCHETYPE_CARRY_RECURSIVE_STAKED` | `KILL_PER_ARCHETYPE` |
| `DEFI_LST_DEPEG_STETH_5PCT`                 | `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS`     | `KILL_PER_ARCHETYPE` |
| `DEFI_LIQUIDATION_CASCADE_CASCADE_SCENARIO` | `KILL_ALL_LIVE` (>50% venues OPEN)          | `KILL_ALL_LIVE`      |
| `CEFI_MULTI_VENUE_REJECTION_RATE_SPIKE`     | `CIRCUIT_OPEN` on target venue              | circuit breaker      |
| `CEFI_POSITION_DRIFT_CRITICAL_5PCT`         | `STOP_NEW_ONLY` on affected strategy        | `KILL_PER_ARCHETYPE` |
| `DEFI_RECURSIVE_LOOP_SAFETY_ABORT_HF_LOW`   | `LOOP_ABORTED_HF_LOW` + `BLOCK_NEW`         | circuit breaker      |

**Assertion timing:** by default the checker expects the event within `assertion_window_seconds=30`. Scenarios that
exercise exponential backoff (cascade → multi-venue OPEN) may need a longer window declared in the scenario seed.

**Reference:** `UAC registry/scenarios/defi.py` + `cefi.py` (UAC@`33630a6`); `UTL scenario/runner.py` (UTL@`3797fed5`);
full outcome taxonomy in `/codex/04-architecture/scenario-outcome-assertions.md` (item 8.B, pending).

---

## Related

- `autonomous-recovery-matrix.md` — full decision tree for every failure scenario
- `09-strategy/architecture-v2/cross-cutting/risk-gates.md` — health factor thresholds and progressive responses
- `04-architecture/execution-policy.md` — unwind cost estimation for exit playbooks
- `05-infrastructure/disaster-recovery.md` — infrastructure-level DR (RTO/RPO, rollback procedures)
- `03-observability/alerting.md` — alert routing rules (Telegram, PagerDuty)
- `03-observability/lifecycle-events.md` — mandatory event sequences during failures
- [`risk-rule-taxonomy.md`](risk-rule-taxonomy.md) — Layer 2 vocabulary that feeds the escalation seam
- [`risk-preflight-flow.md`](risk-preflight-flow.md) — every-order pre-flight aggregation that emits seam events
- [`risk-breaker-seam.md`](risk-breaker-seam.md) — distinct-enums-with-escalation contract; Q9 ratification 2026-05-10
- [`circuit-breaker-rule-taxonomy.md`](circuit-breaker-rule-taxonomy.md) — closed-set `CircuitBreakerId` +
  `BreakerAction` + `BreakerRecoveryMode` SSOT (DR plan Phase 8.A)
- [`kill-switch-event-bus.md`](kill-switch-event-bus.md) — UTL `KillSwitchBus` arm/disarm/subscribe API + audit-log
  persistence + typed UAC event shapes (DR plan Phase 8.B)
