---
scope: [engineer, admin]
---

# Multi-Leg Execution

> **Scope:** All spread, basis, arb, and composite strategies that submit 2+ legs as a single trade. **SSOT:**
> `execution-service/execution_service/engine/multi_leg_orchestrator.py`

## Overview

Multi-leg execution coordinates the submission of related order legs (e.g., buy spot + short perp for basis trade) with
safety guarantees. The system handles leg ordering, partial fill thresholds, retry on transient errors, and automatic
compensation/unwind when a hedge leg fails after the primary leg has already filled.

## Execution Modes

| Mode                | Behaviour                                                                  | Use case                                    |
| ------------------- | -------------------------------------------------------------------------- | ------------------------------------------- |
| **SEQUENTIAL**      | Legs execute in order; first failure cancels remaining                     | Simple multi-step, low urgency              |
| **LEADER_FOLLOWER** | Leader fills first; followers dispatch only if leader meets fill threshold | Spread/basis trades with known leg ordering |
| **PARALLEL**        | All legs submitted simultaneously; partial failure allowed                 | Independent legs, latency-sensitive         |
| **LIQUIDITY_AWARE** | Queries book depth per leg; thinner side leads, deeper side hedges         | Arb/spread where liquidity varies by venue  |

### LIQUIDITY_AWARE Mode (New)

Automatically resolves leg ordering without the strategy needing to specify `leader_leg_index`:

1. Queries `LiquidityProvider.get_available_liquidity()` for each leg's venue + instrument
2. The leg with the **thinnest** available liquidity becomes the leader (fills first before it moves)
3. The leg with the **deepest** liquidity becomes the follower (hedge, more likely to fill at target price)
4. Explicit `leg_role = PRIMARY` overrides automatic detection
5. Falls back to SEQUENTIAL if liquidity data is unavailable

After leader selection, delegates to LEADER_FOLLOWER mode with the computed leader index.

## Leg Roles

Strategies can tag legs with roles to hint at execution ordering:

| Role      | Meaning                                                                 |
| --------- | ----------------------------------------------------------------------- |
| `PRIMARY` | Illiquid, initiating leg. Always executes first in LIQUIDITY_AWARE mode |
| `HEDGE`   | Liquid, compensating leg. Executes after PRIMARY fills                  |
| `AUTO`    | Let execution-service decide based on liquidity data (default)          |

Roles are set via `LegInstruction.leg_role` (type: `LegRole` enum from UAC).

## Retry Policy

When a leg fails, the error is classified through UAC's `classify_venue_error()`:

| ErrorAction | Behaviour                                                                             |
| ----------- | ------------------------------------------------------------------------------------- |
| **RETRY**   | Retry with exponential backoff (configurable `retry_backoff_ms`, doubled per attempt) |
| **SKIP**    | Mark leg as SKIPPED, continue to next leg                                             |
| **FAIL**    | Return failure immediately; triggers compensation if leader already filled            |

**Network errors are always retryable** — `ConnectionError`, `TimeoutError`, `OSError` bypass venue classification and
go straight to RETRY.

Configuration on `MultiLegInstruction`:

- `max_retry_attempts`: Maximum retries per leg (default: 3)
- `retry_backoff_ms`: Initial backoff in milliseconds (default: 500, doubles each attempt)

## Compensation / Unwind

**Problem:** In non-atomic (CeFi/cross-venue) multi-leg trades, if the leader fills but the follower fails, you're left
with an unhedged position.

**Solution:** Automatic compensation trade fires when:

1. Leader leg is FILLED
2. Follower leg fails AFTER all retries are exhausted
3. `auto_unwind_enabled` is True (default)

**Compensation flow:**

```
Leader fills (BUY 0.1 BTC on Binance)
  → Follower fails (SELL 0.1 BTC perp on Bybit) after 3 retries
    → Emit UNHEDGED_POSITION_ALERT (CRITICAL severity)
    → Fire compensation: SELL 0.1 BTC MARKET IOC on Binance (opposite side, same venue)
      → Success: leader marked UNWOUND with compensation_order_id
      → Failure: emit MULTI_LEG_COMPENSATION_FAILED (CRITICAL) + trigger circuit breaker
```

**Configuration on `MultiLegInstruction`:**

- `auto_unwind_enabled`: Enable automatic compensation (default: True)
- `max_unwind_slippage_bps`: Maximum acceptable slippage for compensation trade (default: 50 bps)
- `timeout_seconds`: Per-leg submission timeout

**Flash loan atomicity:** DeFi flash loan legs are already atomic on-chain (Solidity tx reverts entirely). Compensation
logic only applies to non-atomic CeFi/cross-venue multi-leg trades.

## Leg Statuses

| Status    | Meaning                                                     |
| --------- | ----------------------------------------------------------- |
| PENDING   | Not yet submitted                                           |
| FILLED    | Successfully filled                                         |
| FAILED    | Failed after retries exhausted                              |
| CANCELLED | Cancelled due to prior leg failure                          |
| SKIPPED   | Skipped (ErrorAction.SKIP classification)                   |
| UNWOUND   | Originally filled, then compensation trade fired to reverse |

## Data Structures

```python
MultiLegInstruction(
    instruction_id: str
    strategy_id: str
    legs: list[LegInstruction]
    execution_mode: MultiLegExecutionMode  # SEQUENTIAL | LEADER_FOLLOWER | PARALLEL | LIQUIDITY_AWARE
    leader_leg_index: int = 0              # For LEADER_FOLLOWER mode
    max_partial_fill_ratio: Decimal = Decimal("0.8")
    auto_unwind_enabled: bool = True
    max_unwind_slippage_bps: int = 50
    max_retry_attempts: int = 3
    retry_backoff_ms: int = 500
    timeout_seconds: int = 30
)

LegInstruction(
    leg_id: str
    instrument_id: str
    venue: str
    side: str           # BUY or SELL
    quantity: Decimal
    order_type: str      # MARKET, LIMIT, etc.
    time_in_force: str   # GTC, IOC, FOK
    price: Decimal | None = None
    leg_role: LegRole = LegRole.AUTO    # PRIMARY, HEDGE, or AUTO
    priority: int = 0
)

LegExecutionResult(
    leg_id: str
    status: LegStatus
    filled_quantity: Decimal | None = None
    average_price: Decimal | None = None
    order_id: str | None = None
    compensation_order_id: str | None = None  # Set when UNWOUND
    error_message: str | None = None
    retry_count: int = 0
)
```

## Strategy Integration

Strategies emit multi-leg trades via the Strategy Instruction Bus (see `strategy-instruction-bus.md`):

1. Strategy groups related instructions with the same `group_id`
2. `group_instructions_to_multi_leg()` in the instruction adapter converts grouped instructions into
   `MultiLegInstruction`
3. If any instruction has `leg_role = PRIMARY`, the adapter chooses LEADER_FOLLOWER mode
4. If all legs have `leg_role = AUTO`, the adapter chooses LIQUIDITY_AWARE mode
5. The multi-leg orchestrator handles execution, retry, and compensation

## Events Emitted

| Event                              | Severity | When                                                      |
| ---------------------------------- | -------- | --------------------------------------------------------- |
| `UNHEDGED_POSITION_ALERT`          | CRITICAL | Leader filled, follower failed, compensation initiated    |
| `MULTI_LEG_COMPENSATION_COMPLETED` | INFO     | Compensation trade succeeded                              |
| `MULTI_LEG_COMPENSATION_FAILED`    | CRITICAL | Compensation trade also failed; circuit breaker triggered |
| `ADAPTER_FETCH_FAILED`             | WARNING  | Individual leg submission error (classified via UAC)      |
