---
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `CARRY_RECURSIVE_STAKED`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Continuous; multi-cycle leveraged
> loop. **Code module (target):** `strategy-service/engine/strategies/carry_recursive_staked_engine.py`

## What it does

Recursive leveraging of a liquid staking position: stake ETH → receive stETH → pledge on Aave → borrow ETH → stake again
→ receive more stETH → pledge → borrow → repeat. Each loop multiplies effective staking exposure by (1 / (1 − LTV ×
safety)). Typical effective leverage 3-4x on ETH. Captures leveraged staking yield, but with cascading liquidation risk.

## Token / position flow

```
Initial capital: 1 ETH

Loop 0 (initial stake):
  STAKE 1 ETH on Lido → 1 stETH
  PLEDGE 1 stETH on Aave (LTV 75%, safety buffer → effective LTV 0.60)
  BORROW 0.60 ETH

Loop 1:
  STAKE 0.60 ETH on Lido → 0.60 stETH (more)
  PLEDGE 0.60 stETH → BORROW 0.36 ETH

Loop 2:
  STAKE 0.36 → BORROW 0.216
  ...

After N loops, total stETH ≈ 1 / (1 − 0.60) = 2.5 (at effective LTV 0.6)
Total staking yield earned on 2.5 ETH vs 1 ETH of capital = 2.5x nominal
Net yield = 2.5 × staking_yield − 1.5 × borrow_rate − fees − depeg_risk_provision

Unwinding:
  Reverse loops. Each loop: REPAY → UNPLEDGE → UNSTAKE (respecting unbonding period on Lido).
```

## Supported venues / instruments

| Stake           | Lending              | Share class |
| --------------- | -------------------- | ----------- |
| Lido (Ethereum) | Aave V3 Ethereum     | ETH         |
| Lido (Ethereum) | Compound V3 Ethereum | ETH         |
| Jito (Solana)   | Kamino               | SOL         |

## Config schema

```yaml
staking_protocol: LIDO
lending_protocol: AAVE_V3_ETHEREUM
collateral_asset: stETH
borrow_asset: ETH
target_leverage: 2.5 # effective leverage after loops
max_leverage: 3.0 # max safety bound
safety_buffer_ltv: 0.15 # 75% - 15% = 60% effective LTV
max_stETH_depeg_bps: 50 # 0.5% — very tight; recursive amplifies depeg loss
health_factor_target: 1.6
health_factor_kill: 1.25
max_allocated_equity_pct: 0.25
rebalance_cadence: 1h
execution_policy_ref: defi-lending-default-v4
```

## Execution semantics

Entry: sequence of ATOMIC multicalls per loop. Each loop is one multicall (STAKE + TRANSFER + LEND + BORROW). Unwind is
the reverse.

## P&L attribution

- **Leveraged staking yield**: (1 / (1 − effective_LTV)) × staking_yield
- **Borrow cost**: leverage × borrow_rate (negative)
- **Execution alpha**: per-leg fills
- **Depeg loss (if realized)**: major tail loss if stETH depegs

## Risk profile

- Drawdowns: moderate in normal regimes; severe during stETH depeg (amplified by leverage)
- Typical Sharpe: 2.0-3.5 in normal; can be sharply negative during depeg
- Kill switches:
  - stETH depeg > max_bps
  - Aave health factor < kill threshold
  - Chain congestion preventing deleverage

## Reaction to equity change

Rescale initial stake; recursion depth preserved.

## Example instances

```
CARRY_RECURSIVE_STAKED@lido-aave-eth-prod              (ETH on Ethereum Aave)
CARRY_RECURSIVE_STAKED@lido-aave-arbitrum-eth-prod      (ETH on Arbitrum Aave)
CARRY_RECURSIVE_STAKED@jito-kamino-sol-prod            (SOL on Kamino)
```

## Migration from legacy

| Legacy                            | Notes                          |
| --------------------------------- | ------------------------------ |
| `defi/recursive-staked-basis.md`  | Direct match                   |
| Code: `recursive_staked_basis.py` | → `CarryRecursiveStakedEngine` |

## Not in this archetype

- **Simple LST hold** (no leverage) — `YIELD_STAKING_SIMPLE`
- **Non-recursive staked basis** (one stake + one perp hedge, no loops) — `CARRY_STAKED_BASIS`
- **Pure lending rotation** (no staking leg) — `YIELD_ROTATION_LENDING`
- **Liquidation snipe during cascade** — `LIQUIDATION_CAPTURE`

## See also

- Family: [carry-and-yield.md](../families/carry-and-yield.md)
- Non-recursive variant: [carry-staked-basis.md](carry-staked-basis.md)
- Venue collateral rules (LTV, haircut):
  [../../../02-venues/venue-registry-reference.md](../../../02-venues/venue-registry-reference.md)
