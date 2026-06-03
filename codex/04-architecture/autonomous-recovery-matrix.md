---
scope: [engineer, admin]
last_reviewed: 2026-05-23
---

# Autonomous Recovery Matrix

> **2026-05-23 SCOPE NOTE**: this doc owns the per-failure-scenario decision tree (what action fires for which error
> class). The **5-layer defence-in-depth model** that surrounds these actions lives in
> [`recovery-defence-in-depth-layers.md`](recovery-defence-in-depth-layers.md). The Layer-0 deterministic recovery
> scripts each action maps to live in `deployment-service/scripts/recovery/` (per
> `plans/active/agent_recovery_controller_layer0_deterministic_2026_05_23.md`). The Layer-1 LLM audit-signoff agent (per
> `plans/active/ai_recovery_audit_signoff_agent_2026_05_23.md`) audits every action emitted from this decision tree.

## Principle

The system takes care of itself 99.9% of the time through retries, circuit breakers, compensation trades, and automatic
position management. Human intervention is only required when both reconciliation AND execution connectivity are lost
simultaneously — the 0.1% case.

**Live-mode only.** All recovery mechanisms are disabled in batch/backtest.

**Every action in this decision tree** is wrapped by Layer-0 deterministic scripts emitting structured
`AgentActionEvent` to the Incident Gateway. The operator gets a human audit ack within 6h (per
`codex/15-runbooks/alerting/audit-acknowledgement-flow.md`).

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
+-- LIQUIDATION RISK (pre-detection — 6 triggers, fires BEFORE actual liquidation)
|   |   (LiquidationRiskPredetector in strategy-service — emits LIQUIDATION_RISK_IMMINENT SEV0)
|   +-- margin_ratio_breach (closed set per venue — CeFi perp, DeFi lending, DeFi perp)
|   +-- liquidation_distance_below_threshold
|   +-- collateral_transfer_fail
|   +-- ADL_or_insurance_fund_risk_signal
|   +-- venue_API_cannot_confirm_margin_state
|   +-- price_gap_exceeds_model_assumptions
|   --> SEV0 → Layer-0 deleverage + Layer-2 PagerDuty + Layer-3 Twilio voice
|
+-- LIQUIDATION EVENT (actual liquidation — closed-set predicates per venue family)
|   |   (LiquidationEventDetector in strategy-service — emits LIQUIDATION_EVENT_DETECTED SEV1)
|   +-- SEV0 escalation if any of 7 overrides true:
|       material_liquidation | more_risk_remains | cause_unknown | strategy_still_trading |
|       margin_collateral_uncertain | cross_account_may_be_affected | internal_state_did_not_predict
|   --> LiquidationInvestigationReport written to GCS audit-store
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
    +-- Age-band escalation (per codex/04-architecture/reconciliation-age-tracking.md):
    |   +-- 0-5 min   --> Internal warning only
    |   +-- 5-15 min  --> Slack/Telegram warning + agent investigation (SEV3)
    |   +-- >15 min   --> SEV1 (human investigation; RECONCILIATION_AGE_WARN AlertCode)
    |   +-- >30 min   --> SEV0 + recon-freeze armed (RECONCILIATION_AGE_CRITICAL AlertCode)
    |
    +-- 7 immediate-SEV0 overrides (bypass age band — any true → SEV0 + freeze):
    |   UNKNOWN_NET_EXPOSURE | OPEN_ORDERS_UNCONFIRMABLE | KILL_SWITCH_CANNOT_CONFIRM_CANCEL |
    |   VENUE_INTERNAL_BALANCE_MISMATCH | POSITION_EXISTS_EXTERNALLY_UNKNOWN_INTERNALLY |
    |   MATERIAL_BALANCE_MOVEMENT_UNEXPLAINED | MARGIN_COLLATERAL_SAFETY_UNCERTAIN
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

> **🟡 OPERATOR-UX NOTE (R-13 PRE_CUTOVER 2026-05-12, slot 8 audit)** — the timeline below shows the breaker state-
> machine timing. **WHO recovers each step is a `BreakerRecoveryMode` decision** (§ "Layer-3 BreakerRecoveryMode
> composes with Layer-4 ErrorAction" below): `auto_cooldown` actions self-recover on the timeline shown, but
> `manual_unkill` actions (notably `KILL_ALL` + first-engagement of `STOP_NEW_ONLY` per-archetype) **stop at the
> CRITICAL emit + require operator click to resume** — no `T+300s HALF_OPEN probe` for those, no `T+3600s backoff cap`
> ever applies because they never auto-attempt. The `BREAKER_RECOVERY_DEFAULTS` mapping (shipped UAC@a7a99b5) is the
> per-action lookup; operator-runbook reading this should consult it before assuming auto-recovery on any line.

```
T+0s    Error detected, classify_venue_error()
T+0-5s  Retry with backoff (if RETRY action)
T+5-15s Circuit breaker evaluates failure rate
T+15s   If DEGRADED: throttle orders, emit alert
T+30s   If OPEN: block venue, start cooldown, emit CRITICAL alert
T+30s   Telegram + PagerDuty notification delivered
T+300s  HALF_OPEN probe (first attempt) — auto_cooldown actions only; manual_unkill stops at T+30s
T+300s  If probe succeeds: CLOSED, resume normal
T+600s  If probe fails: backoff doubles (next probe at T+900s)
...
T+3600s Maximum backoff cap reached — auto_cooldown only
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

> **🟡 STATUS REFRESH (R-14 PRE_CUTOVER 2026-05-12, slot 8 audit)** — table refreshed against DR plan Phase 3 ship at
> `kill-switch-circuit-breaker.md:218-244` (8 reconcilers shipped). Reviewers reading the PLANNED-when-shipped state
> below before 2026-05-12 should treat the SHIPPED-status entries as authoritative; full implementation provenance
> belongs to `plans/active/disaster_recovery_circuit_breakers_2026_05_10.md` Phase 3.

| ID  | Gap                                                            | Status                    | Implementation                                                                                                                    |
| --- | -------------------------------------------------------------- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| G1  | Circuit breaker → kill switch escalation (multi-venue cascade) | SHIPPED (DR Plan Phase 3) | execution-service: monitor venue breaker states, auto STOP_NEW_ONLY at >50% — wired per `kill-switch-circuit-breaker.md:218-244`  |
| G2  | Reconciliation as pre-close gate                               | PLANNED                   | execution-service: check PBMS recon health before exit playbook                                                                   |
| G3  | Dual failure event (recon + exec both down)                    | SHIPPED (DR Plan Phase 3) | PBMS: detect when both are broken, emit DUAL_FAILURE_DETECTED — reconciler shipped per `kill-switch-circuit-breaker.md:218-244`   |
| G4  | Position drift → auto STOP_NEW_ONLY                            | SHIPPED (DR Plan Phase 3) | PBMS: on CRITICAL drift, call execution-service kill switch API — reconciler shipped per `kill-switch-circuit-breaker.md:218-244` |
| G5  | Connectivity loss → mark recon as stale                        | PLANNED                   | PBMS: subscribe to CIRCUIT_OPEN, mark venue recon as unreliable                                                                   |
| G6  | Playbook-to-scenario mapping                                   | PLANNED                   | UAC: map EmergencyExitType to trigger scenarios in config                                                                         |

---

## Layer-3 BreakerRecoveryMode composes with Layer-4 ErrorAction

The 4-set `ErrorAction` taxonomy (RETRY / RECONNECT / SKIP / FAIL) classifies **post-venue-error responses** at Layer 4
— after a venue rejects an attempt, the adapter routes via `classify_venue_error()`. This composes with — but is
distinct from — Layer 3's `BreakerRecoveryMode` 2-set (`manual_unkill` / `auto_cooldown`), which classifies the
**breaker state machine's exit** from DEGRADED / OPEN / HALF_OPEN. Per-action defaults in `BREAKER_RECOVERY_DEFAULTS`
(shipped UAC@a7a99b5 per Q8 ratification 2026-05-10):

| BreakerAction | Default recovery mode | Why                                                              |
| ------------- | --------------------- | ---------------------------------------------------------------- |
| `BLOCK_NEW`   | `auto_cooldown`       | Least-restrictive; auto-resume safe once metric clears.          |
| `CANCEL_OPEN` | `manual_unkill`       | Cancelled orders are gone; auto-recovery can't restore them.     |
| `SCALE_DOWN`  | `auto_cooldown`       | Partial unwind has a natural inverse — full-size resumes safely. |
| `KILL_ALL`    | `manual_unkill`       | Full unwind requires operator sign-off before re-enable.         |

**How they compose**: a venue rejection at Layer 4 maps to an ErrorAction; that ErrorAction may transition the breaker
state machine (e.g. repeated `FAIL` classifications open the breaker). Once open, the breaker's
`BreakerConfig.recovery_mode` (defaulted via `BREAKER_RECOVERY_DEFAULTS[action]`, or explicitly overridden) governs exit
semantics. Layer 4 `ErrorAction` is per-attempt; Layer 3 `BreakerRecoveryMode` is per-state-transition.

**Cross-references**: [`circuit-breaker-rule-taxonomy.md`](circuit-breaker-rule-taxonomy.md) — `BreakerAction` +
`BreakerRecoveryMode` taxonomy. [`kill-switch-event-bus.md`](kill-switch-event-bus.md) — arm/disarm event flow consuming
recovery decisions. [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md) — integrated state-machine
narrative.

### Runtime: `BreakerRecoveryEngine` (UTL, DR plan Phase 5.A)

The taxonomy declares _what_ recovery mode each breaker uses;
`unified_trading_library.circuit_breaker.BreakerRecoveryEngine` (shipped UTL@d5161fd) is the _runtime_ state machine
that drives it. One engine per process holds the armed-breaker registry:

- `arm(config, recovery_rule, *, armed_at=...)` — record that a `CircuitBreakerId` fired; stores its `BreakerConfig`
  (carrying `recovery_mode` + `cooldown_seconds`) + the matching `BreakerRecoveryRule` (carrying `guard_description`,
  `retry_policy`, `auto_disarm_after_seconds`).
- `register_guard(breaker_id, guard_fn)` — register the green-condition predicate (`Callable[[CircuitBreakerId], bool]`)
  for an `auto_cooldown` breaker. **Fail-loud**: `evaluate()` on an `auto_cooldown` breaker with no registered guard
  raises `MissingRecoveryGuardError` — no silent stuck state.
- `evaluate(breaker_id, *, now=...) -> RecoveryDecision` — one recovery tick. `manual_unkill` mode → always `HOLD`.
  `auto_cooldown` mode → run the guard; N consecutive `True` readings (default N=2) → `AUTO_DISARM`; if
  `auto_disarm_after_seconds` has elapsed regardless of guard state → `TIMEOUT_DISARM` (a hard ceiling so a
  permanently-red guard can't pin a least-restrictive breaker forever).
- `manual_unkill(breaker_id, *, operator_id, now=...) -> RecoveryDecision` — operator-driven disarm (`MANUAL_DISARM`);
  works for both modes (operators always override; the reverse — auto-disarming a `manual_unkill` breaker — is
  forbidden); `operator_id` is mandatory for the `KILL_SWITCH_MANUAL_UNKILLED` audit trail.
- `tick_all(*, now=...)` — `evaluate()` every armed `auto_cooldown` breaker (skips `manual_unkill`), deterministic
  `CircuitBreakerId` order; for a cron / per-fill recovery sweep.

The engine is **pure** — it never touches the `KillSwitchBus` or the alerting channels. The caller (DR Phase 5 service
wiring) maps a disarming `RecoveryDecision` to `KillSwitchBus.disarm(...)` + emits `KILL_SWITCH_AUTO_RECOVERED` (for
`AUTO_DISARM` / `TIMEOUT_DISARM`) or `KILL_SWITCH_MANUAL_UNKILLED` (for `MANUAL_DISARM`). `RecoveryDecision` carries
`recovered_after_seconds` + the boolean `guard_trail` so the alert body can show the evaluation history.

## Scenario-driven recovery validation

Every decision tree gate in this doc has a paired UAC scenario that exercises it. The `ScenarioRunner` applies a
synthetic overlay, forces the condition, and asserts the expected recovery action fires within
`assertion_window_seconds`.

**Recovery row → scenario pairing:**

| Gate label | Decision tree node  | Paired scenario ID                              | Assertion checked                                   |
| ---------- | ------------------- | ----------------------------------------------- | --------------------------------------------------- |
| G1         | >50% venues OPEN    | `CEFI_MULTI_VENUE_REJECTION_RATE_SPIKE`         | `STOP_NEW_ONLY` fires; strategy pauses target-track |
| G2         | NO/YES recon        | `CEFI_POSITION_DRIFT_CRITICAL_5PCT` (recon leg) | `RECON_DEGRADED_CLOSE` emitted; post-close recon    |
| G3         | DUAL_FAILURE        | `CEFI_POSITION_DRIFT_CRITICAL_5PCT` + network   | `DUAL_FAILURE_DETECTED` CRITICAL PD fires           |
| G4         | Drift > 5% CRITICAL | `CEFI_POSITION_DRIFT_CRITICAL_5PCT`             | `STOP_NEW_ONLY` + strategy pause; Telegram + PD     |

**DeFi-specific recovery pairings:**

| Gate label | Condition                            | Paired scenario ID                          | Assertion checked                                |
| ---------- | ------------------------------------ | ------------------------------------------- | ------------------------------------------------ |
| HF1        | HF < 1.0 emergency close             | `DEFI_AAVE_HEALTH_FACTOR_BREACH_1_05`       | All positions closed; `KILL_PER_ARCHETYPE` fired |
| HF2        | LST depeg kill                       | `DEFI_LST_DEPEG_STETH_5PCT`                 | `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` fired    |
| CAS1       | Liquidation cascade → all-venue OPEN | `DEFI_LIQUIDATION_CASCADE_CASCADE_SCENARIO` | `KILL_ALL_LIVE` + firm-wide halt                 |

**Running the matrix:**

```bash
# UTL ScenarioMatrixRunner — per-archetype all-scenarios sweep
from unified_trading_library.scenario.runner import ScenarioMatrixRunner
report = ScenarioMatrixRunner.run(archetype="carry_staked_basis")
assert report.all_passed, report.failed_scenario_ids
```

Scenarios with `synthetic=true` are excluded from P&L attribution. The `ScenarioReport` carries per-gate
`assertion_passed` booleans + the event that was (or wasn't) emitted within the assertion window.

**Reference:** `UAC registry/scenarios/defi.py` + `cefi.py` (UAC@`33630a6`); `UTL scenario/runner.py` +
`scenario/checker.py` (UTL@`3797fed5`); injection architecture:
`codex/04-architecture/scenario-injection-architecture.md` (8.A, SHIPPED UTL@`66904fe0` slot 7 Day-4 2026-05-12).

## Hard-stop scope: agent vs human (codified 2026-06-02)

The CLAUDE.md "Hard-stop list" defers to this matrix for _which kill-switch / trading-halt actions an autonomous agent
may take vs which require a human._ The rule is **direction- + scope-aware, not a blanket "kill-switch = human" gate** —
because a fail-safe halt left waiting 8 h on a human is worse than the halt itself:

| Action                                                                                                                                                             | Who                                     | Why                                                                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Arm** kill-switch / `STOP_NEW_ONLY` / firm-wide halt (protective)                                                                                                | **Agent + runtime — always autonomous** | Fail toward safety; the runtime already auto-arms (G1/G4 SHIPPED). An agent that spots a novel failure overnight halts-to-safety without waiting.                                                                  |
| **Relaunch** crashed safety/monitoring VMs (alerting / watchdog / consolidator)                                                                                    | **Agent — autonomous**                  | Infra op (CLAUDE.md "do NOT pause for operator approval on infra ops"); keeps the autonomous risk system alive so it _can_ auto-halt.                                                                              |
| **Resume / un-kill / disarm — within DR + auto-recovery scope** (`auto_cooldown` breakers: `BLOCK_NEW`, `SCALE_DOWN`; self-recover on the Recovery-Timeline above) | **Agent + runtime — autonomous**        | Reversible, least-restrictive; the engine's `AUTO_DISARM` / `TIMEOUT_DISARM` paths already do this without an operator.                                                                                            |
| **Resume / un-kill / disarm — OUTSIDE scope**                                                                                                                      | **Human only**                          | Two cases: (1) a `manual_unkill` destructive breaker (`KILL_ALL`, `CANCEL_OPEN` — operator sign-off by design, `manual_unkill(operator_id=…)`); (2) a novel situation this matrix / the DR runbook does NOT cover. |
| Wallet keys / move capital / force-push `main` / 1.0.0 graduation                                                                                                  | **Human only**                          | Unchanged hard-stops — risk-increasing + irreversible, unrelated to recovery.                                                                                                                                      |

**One-line invariant:** the gate is on the **risk-increasing** direction _and only when it falls outside the defined
DR/auto-recovery scope_ — never on the protective direction, and never on in-scope reversible resume. SSOT mirror:
CLAUDE.md § "Plans Run To Actual Completion → Hard-stop list".

## Related

- `kill-switch-circuit-breaker.md` — detailed kill switch and circuit breaker mechanics
- `circuit-breaker-rule-taxonomy.md` — `CircuitBreakerId` / `BreakerScope` / `BreakerAction` / `BreakerRecoveryMode`
  closed sets (DR plan Phase 8.A)
- `kill-switch-event-bus.md` — `KillSwitchBus` + audit-log + typed event vocab (DR plan Phase 8.B)
- `09-strategy/architecture-v2/cross-cutting/risk-gates.md` — health factor thresholds
- `04-architecture/execution-policy.md` — unwind cost estimation
- `05-infrastructure/disaster-recovery.md` — infrastructure DR (RTO/RPO, rollback)
- `03-observability/alerting.md` — alert routing rules
- `reconciliation-resolution.md` — reconciliation break resolution workflow
