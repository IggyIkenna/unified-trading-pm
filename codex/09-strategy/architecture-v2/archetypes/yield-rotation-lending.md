---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 500
  min_sla_tier: basic
---

# Archetype: `YIELD_ROTATION_LENDING`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Continuous — supply positions held
> while APY competitive; rotated as rates shift. **Code module (target):**
> `strategy-service/engine/strategies/yield_rotation_lending_engine.py`

## What it does

Supply assets (USDC, USDT, wBTC, ETH, stETH, etc.) to lending protocols and rotate across chains / protocols based on
APY differentials. Single-sided supply (no leverage) — just the best place for your stablecoin / asset to sit.

## Token / position flow

```
1. APY MONITOR: continuously poll supply APY across eligible (protocol, chain) pairs

2. TARGET ALLOCATION: compute per-venue target allocation based on APY + capacity + gas
   e.g., {ETHEREUM: 40%, ARBITRUM: 30%, POLYGON: 30%} at $1M equity

3. ENTRY / REBALANCE triggers:
   - APY differential > min_rebalance_threshold → emit LEND targets per chain
   - BRIDGE instructions if capital needs to move across chains
   - Gas-aware: skip rebalance if gas > expected uplift over rebalance interval

4. HOLD: earn APY; claim rewards (if any); compound per config

5. EXIT: close all positions (withdraw from all chains, bridge back to base)
```

## Supported venues / instruments

**Coverage matrix:** See
[`../category-instrument-coverage.md § 9. YIELD_ROTATION_LENDING`](../category-instrument-coverage.md#9-yield_rotation_lending)
for the authoritative protocol × chain × asset matrix (Aave V3 on six chains, Compound V3, Euler, Morpho, Kamino).

## Config schema

```yaml
protocol_eligible: [AAVE_V3, COMPOUND_V3] # multi-protocol variant
chains_eligible: [ETHEREUM, ARBITRUM, OPTIMISM, POLYGON, AVALANCHE, BASE]
asset: USDC
share_class: USDC
min_apy_differential_bps: 30 # 0.3% — don't rebalance for less
min_rebalance_notional_usd: 10000 # don't move < $10k
gas_budget_pct_of_rotation: 0.1 # gas can't exceed 10% of rotation expected yield gain
rebalance_cadence_minutes: 60 # re-evaluate hourly
max_pct_per_chain: 0.50 # no more than 50% in one chain
execution_policy_ref: defi-lending-default-v4
```

## Execution semantics

- `LEND` action for each target supplied_amount per (protocol, chain, asset)
- `BRIDGE` when rebalancing across chains (Circle CCTP for USDC, LayerZero for others)
- Execution sequences: withdraw from lower-APY venue → bridge → deposit to higher-APY venue

## P&L attribution

- **Supply APY accrued**: tracked per position; realized on withdraw or at reporting interval
- **Reward tokens** (e.g., Aave rewards): tracked separately; optionally claimed + swapped to base asset
- **Gas + bridge fees**: deducted from net yield
- **Execution alpha**: minimal — lending is mostly deterministic execution

## Risk profile

- Drawdowns: very low (no leverage, no directional exposure)
- Tail risks: smart-contract risk, stablecoin depeg (if asset = stable), chain halt, bridge exploit
- Typical Sharpe: 2.0-4.0 (excellent given it's effectively a higher-yielding cash strategy)
- Kill switches: protocol incident (exploit, pause, oracle failure), asset depeg > threshold, chain congestion
  preventing withdrawal
- Chainlink oracle divergence tiering (applied per supplied asset):
  - **1-2% warn** — log + alert, no position change
  - **2-3% reduce** — halve allocation on the affected chain
  - **>3% exit** — withdraw fully from the affected chain pending oracle recovery

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    # Recompute per-chain targets proportionally
    target_per_chain = {chain: new_equity * weight for chain, weight in self.weights.items()}
    return [LEND(protocol=self.proto, chain=c, asset=self.asset, target=t)
            for c, t in target_per_chain.items()]
```

## Example instances

```
YIELD_ROTATION_LENDING@aave-multichain-usdc-prod
YIELD_ROTATION_LENDING@aave-multichain-usdt-prod
YIELD_ROTATION_LENDING@aave-multichain-wbtc-prod
YIELD_ROTATION_LENDING@aave-multichain-eth-prod
YIELD_ROTATION_LENDING@aave-compound-ethereum-usdc-prod      (multi-protocol single-chain)
YIELD_ROTATION_LENDING@kamino-sol-usdc-prod                   (Solana only)
YIELD_ROTATION_LENDING@aave-ethereum-steth-prod               (stETH supply)
```

## Migration from legacy

| Legacy                                                                                                  | Notes                                                                         |
| ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `defi/aave-lending.md`                                                                                  | Generic lending rotation                                                      |
| `defi/btc-lending-yield.md`                                                                             | wBTC variant                                                                  |
| `defi/multi-chain-lending-yield.md`                                                                     | Consolidates                                                                  |
| `defi/sol-lending-yield.md`                                                                             | Kamino variant                                                                |
| `defi/cross-chain-yield-arb.md`                                                                         | If alpha is sustained rate spread (not transient dispersion) → this archetype |
| Code: `aave_lending.py`, `multi_chain_lending_yield.py`, `sol_lending_yield.py`, `btc_lending_yield.py` | All → `YieldRotationLendingEngine`                                            |

## Not in this archetype

- **Staking-only yields** (LST hold, no lending) — `YIELD_STAKING_SIMPLE`
- **LST collateral used as basis** (staked token + perp hedge) — `CARRY_STAKED_BASIS`
- **Flash-loan recursion** (borrow to amplify staked basis) — `CARRY_RECURSIVE_STAKED`
- **Cross-protocol lending-rate arbitrage** (long one protocol, short another) — `ARBITRAGE_PRICE_DISPERSION`

## See also

- Family: [carry-and-yield.md](../families/carry-and-yield.md)
- Simple staking: [yield-staking-simple.md](yield-staking-simple.md)
- Venue collateral rules (for supply-only, liquidation risk is N/A but interest rate model matters):
  [../../../02-venues/venue-registry-reference.md](../../../02-venues/venue-registry-reference.md)
