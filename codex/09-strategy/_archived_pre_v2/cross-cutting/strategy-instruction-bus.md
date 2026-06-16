---
scope: [engineer, admin]
---

# Strategy Instruction Bus

SSOT: `unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/instruction.py`

## Overview

Strategies emit typed `StrategyInstruction` objects with a `StrategyInstructionType` enum. Execution-service interprets
these instructions and decomposes them into atomic execution steps via the instruction adapter.

This decouples strategy logic from execution mechanics: strategies declare _what_ they want (SWAP, LEND, HEDGE*BASIS),
and execution-service decides \_how* to execute (approve, swap, multicall, etc.).

## Instruction Types

| Type                  | Domain    | Decomposition                                              |
| --------------------- | --------- | ---------------------------------------------------------- |
| `MARKET_ORDER`        | Trading   | Single TRADE step                                          |
| `LIMIT_ORDER`         | Trading   | Single TRADE step with limit price                         |
| `SWAP`                | DeFi      | [approve] -> [swap] (via IntentDecomposer)                 |
| `LEND`                | DeFi      | [approve] -> [supply] (via IntentDecomposer YIELD)         |
| `BORROW`              | DeFi      | [borrow] step                                              |
| `REPAY`               | DeFi      | [approve] -> [repay]                                       |
| `WITHDRAW`            | DeFi      | [withdraw] step                                            |
| `STAKE`               | DeFi      | [approve] -> [stake] (via IntentDecomposer YIELD)          |
| `UNSTAKE`             | DeFi      | [unstake] step                                             |
| `BRIDGE`              | DeFi      | [approve] -> [bridge] (via IntentDecomposer BRIDGE)        |
| `FLASH_LOAN`          | DeFi      | [flash_open] -> [ops] -> [flash_close] (atomic, single tx) |
| `HEDGE_BASIS`         | Composite | [spot trade] -> [perp hedge] (two-leg)                     |
| `REBALANCE_LP`        | Composite | [remove_liq] -> [swap] -> [add_liq]                        |
| `REBALANCE_PORTFOLIO` | Composite | Multiple [swap] steps (via IntentDecomposer REBALANCE)     |
| `BACK`                | Sports    | Single sports exchange order step                          |
| `LAY`                 | Sports    | Single sports exchange order step                          |

## Leg Roles

From `unified_api_contracts.internal.domain.execution_service.multi_leg.LegRole`:

| Role      | Meaning                                     | Execution Behaviour                              |
| --------- | ------------------------------------------- | ------------------------------------------------ |
| `PRIMARY` | Illiquid / initiating leg (the alpha trade) | Executes first (leader in LEADER_FOLLOWER mode)  |
| `HEDGE`   | Liquid / compensating leg                   | Executes after leader fills                      |
| `AUTO`    | Let execution-service decide                | Liquidity-aware routing picks thinnest as leader |

## Multi-Leg Grouping via group_id

Instructions sharing the same `group_id` are collected into a single `MultiLegInstruction` and routed through the
`MultiLegOrchestrator`. This enables:

- **Basis trades**: spot buy (PRIMARY) + perp short (HEDGE) grouped together.
- **Arb legs**: two venue legs that must execute atomically.
- **Options combos**: multi-leg options with coordinated execution.

```python
# Strategy emits two instructions with same group_id
spot_instr = StrategyInstruction(
    instruction_id="inst_001",
    strategy_id="BASIS_CARRY",
    instruction_type=StrategyInstructionType.MARKET_ORDER,
    operation=OperationType.TRADE,
    instrument_id="BINANCE-SPOT:SPOT:ETH-USDT",
    from_venue="BINANCE-SPOT",
    to_venue="BINANCE-SPOT",
    token_in="USDT",
    amount=Decimal("10000"),
    direction="LONG",
    leg_role=LegRole.PRIMARY,
    group_id="basis_001",
    # ...
)

perp_instr = StrategyInstruction(
    instruction_id="inst_002",
    strategy_id="BASIS_CARRY",
    instruction_type=StrategyInstructionType.MARKET_ORDER,
    operation=OperationType.TRADE,
    instrument_id="BINANCE-FUTURES:PERPETUAL:ETH-USDT@LIN",
    from_venue="BINANCE-FUTURES",
    to_venue="BINANCE-FUTURES",
    token_in="USDT",
    amount=Decimal("10000"),
    direction="SHORT",
    leg_role=LegRole.HEDGE,
    group_id="basis_001",
    # ...
)
```

`group_instructions_to_multi_leg([spot_instr, perp_instr])` produces a single `MultiLegInstruction` with
`LEADER_FOLLOWER` mode, PRIMARY leg leading.

## Urgency Levels

| Level       | Algorithm Default | Behaviour                                  |
| ----------- | ----------------- | ------------------------------------------ |
| `LOW`       | TWAP              | Passive, spread over time, minimize impact |
| `NORMAL`    | MARKET            | Standard market execution                  |
| `HIGH`      | MARKET            | Aggressive, taker-preferred                |
| `IMMEDIATE` | MARKET            | IOC/FOK, must fill now                     |

The `algo` field on `StrategyInstruction` overrides the urgency-derived default when set.

## Execution Flow

```
Strategy-Service                    Execution-Service
     |                                    |
     |  StrategyInstruction               |
     |  (instruction_type=SWAP,           |
     |   urgency=HIGH, group_id=...)      |
     |----------------------------------->|
     |                                    |
     |                    adapt_strategy_instruction()
     |                           |
     |                    ExecutionPlan (steps with deps)
     |                           |
     |                    group_instructions_to_multi_leg()
     |                           |
     |                    MultiLegOrchestrator.orchestrate()
     |                           |
     |                    MatchingEngine.submit_order()
     |                           |
     |  MultiLegExecutionResult   |
     |<---------------------------|
```

## Backwards Compatibility

When `instruction_type` is `None`, the adapter falls back to routing based on the `operation` field. This ensures
existing strategies that emit only `operation` continue to work without changes.

## SSOT Files

| Concern                      | File                                                                   |
| ---------------------------- | ---------------------------------------------------------------------- |
| StrategyInstructionType enum | `unified-api-contracts/.../strategy_service/instruction.py`            |
| LegRole enum                 | `unified-api-contracts/.../execution_service/multi_leg.py`             |
| OperationType enum           | `unified-api-contracts/.../execution_service/types.py`                 |
| Instruction adapter          | `execution-service/execution_service/engine/instruction_adapter.py`    |
| IntentDecomposer             | `execution-service/execution_service/algo_library/intent_engine.py`    |
| MultiLegOrchestrator         | `execution-service/execution_service/engine/multi_leg_orchestrator.py` |
