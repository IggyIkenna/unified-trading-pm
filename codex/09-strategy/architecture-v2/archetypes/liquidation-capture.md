---
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `LIQUIDATION_CAPTURE`

> **Family:** [Arbitrage / Structural Edge](../families/arbitrage-structural.md) **Settlement model:** ATOMIC
> (flash-loan + multicall within single block). **Code module (target):**
> `strategy-service/engine/strategies/liquidation_capture_engine.py`

## What it does

Monitors under-collateralized lending positions on DeFi protocols and executes liquidation calls to capture the
protocol's paid bonus (typically 5-10% of seized collateral). Zero directional risk; alpha is the structural bonus paid
by the lending protocol for cleaning up unhealthy positions.

## Token / position flow

```
1. HEALTH FACTOR WATCHER:
   - Subscribe to on-chain state of all outstanding positions on target protocols
   - Compute health_factor = (collateral_value × liquidation_threshold) / debt_value
   - Trigger opportunity when health_factor drops below 1.0 (liquidatable)

2. OPPORTUNITY VALIDATION:
   - Compute expected profit = seized_collateral × (1 + liquidation_bonus) × current_price
                             − debt_repaid - gas_cost - dex_slippage
   - Skip if profit < threshold

3. ATOMIC EXECUTION (flash-loan pattern):
   multicall bundle {
     FLASH_LOAN (debt_asset, amount = position.debt)
     REPAY (protocol, on_behalf_of = underwater_address, amount = position.debt)
     SEIZE_COLLATERAL (protocol, underwater_address, collateral_asset)
     SWAP (collateral_asset → debt_asset, via DEX)
     REPAY_FLASH_LOAN (debt_asset, amount = borrowed + fee)
     # Net profit remains in executor wallet
   }

   Submitted via Flashbots bundle for MEV protection against front-runners.

4. POST-EXECUTION: net profit = surplus collateral_value after repaying all legs.
   Returned to treasury / strategy wallet.
```

## Supported protocols

| Protocol    | Chains                                                 | Liquidation bonus (typical) | Notes                           |
| ----------- | ------------------------------------------------------ | --------------------------- | ------------------------------- |
| Aave V3     | Ethereum, Arbitrum, Optimism, Polygon, Avalanche, Base | 5-10% per asset             | Primary target                  |
| Compound V3 | Ethereum                                               | 5-8%                        |                                 |
| Euler       | Ethereum                                               | Similar                     | Focus on risk-segmented markets |
| Morpho      | Ethereum                                               | Similar                     |                                 |
| Kamino      | Solana                                                 | 5-10%                       | Solana-native                   |

## Config schema

```yaml
protocols_eligible:
  - AAVE_V3_ETHEREUM
  - AAVE_V3_ARBITRUM
  - AAVE_V3_OPTIMISM
  - AAVE_V3_POLYGON
  - AAVE_V3_AVALANCHE
  - AAVE_V3_BASE
min_profit_usd: 50 # skip opps < $50 profit
max_debt_repay_usd: 1_000_000 # flash-loan cap per opp
priority_fee_strategy: AGGRESSIVE # win the gas auction
submission_mode: FLASHBOTS_BUNDLE # prevent front-run
dex_slippage_tolerance: 0.005 # 0.5%
execution_policy_ref: defi-liquidation-v3
share_class: USD
```

## Execution semantics

- Single `ATOMIC` instruction per opportunity
- Flash-loan embedded within the bundle
- Submission via Flashbots (Ethereum + Base) / equivalent bundlers (other chains)
- Reverts atomically if profit falls short mid-bundle

## P&L attribution

- **Gross liquidation profit**: seized_collateral_value − debt_repaid
- **Flash-loan fee**: minor (e.g., Aave 0.05%)
- **Gas**: deducted
- **DEX slippage on collateral sale**: deducted
- **Net P&L**: what's left after all above

## Risk profile

- Drawdowns: none from successful opps; only cost from failed attempts (wasted gas, failed bundle inclusion)
- Typical Sharpe: high on a per-opp basis; opp frequency is the constraint on annualized returns
- Kill switches: protocol incident (oracle failure, governance pause), abnormal bundle failure rate, gas price spike
  making opps unprofitable

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    self.max_debt_repay = new_equity * self.config.max_debt_repay_pct_of_equity
    return []    # no in-flight positions to resize
```

## Example instances

```
LIQUIDATION_CAPTURE@aave-ethereum-prod
LIQUIDATION_CAPTURE@aave-arbitrum-prod
LIQUIDATION_CAPTURE@aave-multichain-prod        (all chains)
LIQUIDATION_CAPTURE@compound-ethereum-prod
LIQUIDATION_CAPTURE@euler-ethereum-prod
LIQUIDATION_CAPTURE@morpho-ethereum-prod
LIQUIDATION_CAPTURE@kamino-solana-prod
```

## Migration from legacy

| Legacy                         | Notes                        |
| ------------------------------ | ---------------------------- |
| Code: `liquidation_capture.py` | → `LiquidationCaptureEngine` |

No dedicated legacy doc; v2 formalizes this as an archetype under Arbitrage / Structural Edge.

## See also

- Family: [arbitrage-structural.md](../families/arbitrage-structural.md)
- MEV protection: [../cross-cutting/mev-protection.md](../cross-cutting/mev-protection.md)
- Venue collateral rules (LTV, liquidation thresholds, bonus per asset):
  [../../../02-venues/venue-registry-reference.md](../../../02-venues/venue-registry-reference.md)
