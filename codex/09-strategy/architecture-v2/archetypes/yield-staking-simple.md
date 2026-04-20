---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 500
  min_sla_tier: basic
---

# Archetype: `YIELD_STAKING_SIMPLE`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Continuous — stake assets, earn
> validator reward, passively held. **Code module (target):**
> `strategy-service/engine/strategies/yield_staking_simple_engine.py`

## What it does

Pure staking: deposit native PoS asset (ETH, SOL, etc.) into liquid staking protocol to earn validator rewards. No basis
leg, no leverage, no directional view. Just held-to-earn-yield.

## Token / position flow

```
1. DEPOSIT: stake share_class capital into selected LST protocol
   - ETH → Lido → receive stETH (rebasing or wrapped wstETH)
   - ETH → Rocket Pool → receive rETH
   - SOL → Jito → receive JitoSOL
   - SOL → Marinade → receive mSOL

2. HOLD: LST balance grows via rebase (stETH) or exchange rate increase (rETH, JitoSOL, mSOL)

3. EXIT: unstake
   - Lido: swap stETH → ETH on DEX OR use Lido withdrawal queue (slow)
   - Rocket Pool: swap rETH → ETH on DEX OR use Rocket withdrawal
   - Jito: instant unstake via Kamino or slow validator unbonding
   - Marinade: instant unstake (with ~0.3% fee) or delayed (free)
```

## Supported venues / instruments

**Coverage matrix:** See
[`../category-instrument-coverage.md § 10. YIELD_STAKING_SIMPLE`](../category-instrument-coverage.md#10-yield_staking_simple)
for the authoritative protocol × chain × LST table with APY anchors and unbonding times.

## Config schema

```yaml
staking_protocol: LIDO # or ROCKET_POOL, JITO, MARINADE
asset: ETH # or SOL
share_class: ETH # typically same as underlying
exit_preference: DEX_SWAP # or PROTOCOL_WITHDRAWAL
max_allocated_pct: 1.0 # can hold 100% staked for pure yield strategies
execution_policy_ref: defi-direct-v2
rebalance_cadence_days: 30 # e.g., claim rewards + restake monthly
```

## Execution semantics

- `STAKE` action type for deposits
- `UNSTAKE` action type for withdrawals (or SWAP via DEX if exit_preference = DEX_SWAP)
- Passive between events

## P&L attribution

- **Staking yield**: LST_balance_change × ETH_price (rebase model) OR LST_price × ETH_price (exchange rate model)
- **No execution alpha** (mostly passive deposit/withdrawal)

## Risk profile

- Drawdowns: LST depeg (stETH depegged to ~0.94 in 2022; rare but real)
- Typical Sharpe: very high in nominal terms (low vol); tail risk is depeg
- Kill switches: depeg > threshold (e.g., 1%), slashing events on validators, protocol incident

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    target_staked = new_equity * self.config.max_allocated_pct
    return [STAKE(protocol=self.proto, target_staked_amount=target_staked)]
```

## Example instances

```
YIELD_STAKING_SIMPLE@lido-eth-prod
YIELD_STAKING_SIMPLE@rocketpool-eth-prod
YIELD_STAKING_SIMPLE@jito-sol-prod
YIELD_STAKING_SIMPLE@marinade-sol-prod
```

## Migration from legacy

No dedicated legacy doc. Simple staking was implicit in staked-basis strategies (stake + use LST as collateral). v2
extracts pure staking as a first-class archetype for clients who want just the yield without the basis complexity.

## Not in this archetype

- **Recursive leverage loops** (flash-loan amplified) — `CARRY_RECURSIVE_STAKED`
- **Staking paired with perp hedge** — `CARRY_STAKED_BASIS`
- **Protocol rotation across lending venues** — `YIELD_ROTATION_LENDING`
- **LP market making / active range management** — `MARKET_MAKING_CONTINUOUS` (AMM LP variant)

## See also

- Family: [carry-and-yield.md](../families/carry-and-yield.md)
- Staked basis (stake + short perp): [carry-staked-basis.md](carry-staked-basis.md)
- Recursive (leveraged) variant: [carry-recursive-staked.md](carry-recursive-staked.md)
