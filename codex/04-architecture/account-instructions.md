---
doc_type: codex-ssot
title: Account Instructions
summary: AccountInstruction — the operator-driven account-ops envelope parallel to StrategyInstruction (CLOSE_ALL,
  SET_MARGIN_MODE, EMERGENCY_LIQUIDATE, WITHDRAW, ROTATE_CREDENTIAL, PAUSE/RESUME); NOT strategy-attributed, skips
  Layer-1 self-check, per-action authorization + permanent audit.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [execution, account-ops, kill-switch, audit, defi, cefi]
related:
  [
    /codex/04-architecture/strategy-execution-protocol.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
  ]
created: 2026-04-17
authoritative_for: [AccountInstruction operator-driven account-ops envelope]
referenced_by: [/codex/04-architecture/strategy-execution-protocol.md]
owner:
last_reviewed: 2026-08-31
code_refs:
---

# Account Instructions

> **What it is:** The parallel envelope to `StrategyInstruction` for **operator-driven** account operations.
> `AccountInstruction` is NOT benchmarked, NOT attributed to strategy alpha, NOT emitted by strategy code — it's issued
> by operators, auto-recovery flows, or emergency systems. Examples: close-all, set-margin-mode, emergency-liquidate,
> transfer-subaccount.

## Why a separate envelope

If account ops flowed through StrategyInstruction:

- They'd be attributed to strategy P&L (wrong — they're operator-driven)
- They'd carry strategy_instance_id, config_hash, etc. that don't exist for ops actions
- They'd pass through Layer 1 strategy self-check (irrelevant for ops)
- They'd be benchmarked (nonsensical — no "intended alpha" to benchmark against)

Separating gives:

- Clean P&L attribution (ops moves ≠ strategy P&L)
- Different authority model (operator role, not strategy engine)
- Different audit trail (who initiated, why, with what approval)
- Different risk gates (some ops bypass strategy-layer checks by design)

## Common envelope

```python
class AccountInstruction:
    instruction_id: str                    # content hash
    emitted_at_utc: datetime
    client_id: str
    initiating_operator: str               # user id / system id for audit
    authorization_id: Optional[str]        # references operator approval record
    venue: VenueId
    account_id: str                        # venue-specific account identifier
    action: AccountActionEnum
    params: Dict                           # action-specific
    rationale: str                         # free text for audit
```

## Action catalog

### `CLOSE_ALL`

Unwind ALL positions on this account, regardless of owning strategy.

```python
action: CLOSE_ALL
params:
  close_mode: MARKET                      # or LIMIT_WITH_DEADLINE
  deadline_utc: "2026-04-17T15:00Z"
  skip_strategy_pnl_attribution: false   # attribute fills back to owning strategies
```

Used when: client offboarding, major incident, auditor demand, ops emergency.

### `CLOSE_ALL_FOR_STRATEGY`

Unwind positions attributed to a specific strategy instance on this account (other strategies on same account
preserved).

```python
action: CLOSE_ALL_FOR_STRATEGY
params:
  strategy_instance_id: "ML_DIRECTIONAL_CONTINUOUS@..."
  close_mode: MARKET
  deadline_utc: "..."
```

Used when: retiring a strategy, kill switch escalation, config rollback.

### `SET_MARGIN_MODE`

Change margin mode (ISOLATED, CROSS, PORTFOLIO).

```python
action: SET_MARGIN_MODE
params:
  mode: CROSS
  apply_to_all_instruments: true
```

Traps:

- Some venues require zero open positions to switch
- Some venues charge switch fees
- Switch while positions open can trigger margin recompute → liquidation risk

### `SET_LEVERAGE`

Set leverage per instrument.

```python
action: SET_LEVERAGE
params:
  instrument: "BINANCE:PERP:BTC-PERP"
  leverage: 10
```

Venue-specific rules apply. Some require no open position to change.

### `EMERGENCY_LIQUIDATE`

Hard liquidation — market-order all positions with maximum urgency. Bypasses some softer policies.

```python
action: EMERGENCY_LIQUIDATE
params:
  reason: KILL_SWITCH_TRIGGERED
  bypass_cost_cap: true
  bypass_slippage_tolerance: true
  escalate_to_alerts: true
```

Used rarely, for firm-wide emergency or failed-safe recovery (see
[autonomous-recovery-matrix.md](autonomous-recovery-matrix.md)).

### `TRANSFER_SUBACCOUNT`

Operator-initiated internal subaccount transfer.

```python
action: TRANSFER_SUBACCOUNT
params:
  subaccount_from: "binance-sub-hft"
  subaccount_to: "binance-main"
  asset: USDT
  amount: 1_000_000
```

Not the same as the strategy-emitted `TRANSFER` (which is within one strategy's context). This is an **account-level**
ops move that doesn't serve a specific strategy.

### `WITHDRAW`

Operator withdrawal to off-venue (client wallet, bank, cold storage).

```python
action: WITHDRAW
params:
  asset: USDT
  amount: 500_000
  destination: "0xclient_wallet..."
  destination_type: WALLET               # or BANK
  authorization_id: "ops_approval_123"
```

Requires additional authorization layer (compliance, 2-of-N sign-off per firm policy).

### `DEPOSIT_ACK`

Acknowledge a client deposit and allocate it to strategies.

```python
action: DEPOSIT_ACK
params:
  asset: USDT
  amount: 2_000_000
  source: CLIENT_WIRE
  allocate_via: portfolio_allocator       # or MANUAL
```

Triggers Portfolio Allocator re-run to distribute new capital across strategies.

### `ROTATE_CREDENTIAL`

Credential rotation trigger; revokes old API key, provisions new.

```python
action: ROTATE_CREDENTIAL
params:
  credential_type: API_KEY
  old_key_id: "..."
  new_key_id: "..."
  rollover_window_seconds: 60
```

Ops concern; strategy shouldn't see disruption if done right.

### `RESUME` / `PAUSE`

Toggle trading at account level.

```python
action: PAUSE
params:
  reason: SCHEDULED_MAINTENANCE
  resume_at_utc: "2026-04-17T18:00Z"
```

Strategies emitting during pause get `ACCOUNT_PAUSED` response; queue instructions. **(`ACCOUNT_PAUSED` is a
specified response code, not a shipped symbol — verified absent workspace-wide 2026-07-31. `AccountInstruction`
itself IS shipped: UAC `internal/architecture_v2/schemas.py`, driven by
`execution_service/v2/account_orchestrator.py::AccountInstructionOrchestrator`.)**

## Risk gate behavior

AccountInstructions skip Layer 1 (strategy self-check). They go through:

- **Layer 2 (risk pre-flight)**: limited — some ops (EMERGENCY_LIQUIDATE) intentionally bypass limits; others
  (SET_LEVERAGE) are subject to "not during market stress" checks
- **Layer 3 (execution pre-flight)**: modified — ops may require account lock acquisition first
- **Layer 4 (venue-side)**: venue applies its own rules

Each action declares its required bypasses explicitly in the handler; no silent bypass.

## Authorization

Critical AccountInstructions require operator authorization:

| Action                    | Authorization                           |
| ------------------------- | --------------------------------------- |
| CLOSE_ALL (non-emergency) | Ops lead                                |
| CLOSE_ALL_FOR_STRATEGY    | Strategy owner + ops                    |
| SET_MARGIN_MODE           | Ops lead                                |
| SET_LEVERAGE              | Ops lead                                |
| EMERGENCY_LIQUIDATE       | Automatic (kill switch) OR firm officer |
| WITHDRAW                  | Compliance + 2-of-N                     |
| DEPOSIT_ACK               | Ops lead                                |
| ROTATE_CREDENTIAL         | Ops (per rotation policy)               |
| PAUSE / RESUME            | Ops on-call                             |

Auto-recovery flows pre-authorize specific actions per the
[autonomous-recovery-matrix.md](autonomous-recovery-matrix.md).

**(This table is the DESIGN TARGET, not what ships today — verified 2026-08-20.**
`AccountInstructionOrchestrator.dispatch()` checks only that `authorization_id` is a non-empty string; it does not
look up who authorized it, what role they hold, or whether the action-specific requirement above (e.g. "Compliance

- 2-of-N" for `WITHDRAW`) was actually met. Per-action, role-based authorization is real remaining work, not built.)**

## Audit

Every AccountInstruction is audit-logged with:

- `initiating_operator`
- `authorization_id`
- `rationale`
- Full action + params
- Venue result (ack + fills + timing)
- Post-state snapshot

Retention: permanent per compliance.

**(DESIGN TARGET — verified 2026-08-20.** The shipped path logs two `log_event` calls
(`ACCOUNT_INSTRUCTION_RECEIVED`/`ACCOUNT_INSTRUCTION_RESULT`) carrying `instruction_id`/`org_id`/`action`/`venue`/
`account_id`/`accepted`/`reason` — no post-state snapshot, no dedicated permanent-audit-log store beyond whatever
the `log_event` sink itself retains. Only `CLOSE_ALL` has a real venue-facing runner today
(`execution_service/v2/account_orchestrator.py::AccountInstructionOrchestrator._execute_close_all`, reachable via
`POST /account/instruction` — `execution_service/api/account_instruction_api.py`); every other action in the table
above is still a log-only accept with no venue call, so "Venue result (ack + fills + timing)" has nothing to log
for them yet.)**

## Attribution handling

When an AccountInstruction generates fills (e.g., CLOSE_ALL):

- Fills attributed to the **originating strategy(s)** if identifiable
- If not identifiable, attributed to ops-pnl-account (firm treasury)
- P&L reporting shows: "strategy P&L = alpha; ops-driven P&L = operator impact"

## Coordination with venue-account

AccountInstructions interact with the coordination layer:

- May acquire account lock (see
  [/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md))
- May cause strategies on the account to receive `VENUE_ACCOUNT_LOCKED` responses
- PBMS updates on completion

## Kill switch integration

Kill switches that trigger account-level action emit `AccountInstruction.EMERGENCY_LIQUIDATE` (or `CLOSE_ALL`) — not via
strategy instruction path. This cleanly separates "strategy says close" from "operator/system says close."

See [kill-switch-circuit-breaker.md](kill-switch-circuit-breaker.md).

## UI / manual workflow

Operator UI provides forms for each AccountInstruction type. Submission requires:

- Rationale text
- Authorization approval (for elevated actions)
- Double-check on destination (for WITHDRAW)
- Dry-run preview where possible

## Cross-references

- Strategy-execution protocol: [strategy-execution-protocol.md](strategy-execution-protocol.md)
- Autonomous recovery: [autonomous-recovery-matrix.md](autonomous-recovery-matrix.md)
- Kill switch: [kill-switch-circuit-breaker.md](kill-switch-circuit-breaker.md)
- Venue-account coordination:
  [/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md)
- Capital-client isolation:
  [/codex/09-strategy/architecture-v2/cross-cutting/capital-client-isolation.md](/codex/09-strategy/architecture-v2/cross-cutting/capital-client-isolation.md)

## Not in this doc

- **Per-action implementation** — execution-service/account_ops_handlers/
- **Auto-recovery flows** — [autonomous-recovery-matrix.md](autonomous-recovery-matrix.md)
- **Operator UI** — admin UI repos
- **Authorization/approval system** — compliance / operator tooling
- **Per-venue specifics of margin mode, leverage** — venue adapter docs
