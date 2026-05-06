---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

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

**Coverage matrix:** See
[`../category-instrument-coverage.md § 12. LIQUIDATION_CAPTURE`](../category-instrument-coverage.md#12-liquidation_capture)
for the authoritative protocol × chain × liquidation-bonus table (Aave V3 on six chains, Compound V3, Euler, Morpho,
Kamino).

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

## Not in this archetype

- **Cross-venue price arbitrage** (no cascade, just venue spread) — `ARBITRAGE_PRICE_DISPERSION`
- **Lending-rate arbitrage** (long one protocol, short another) — `ARBITRAGE_PRICE_DISPERSION`
- **Directional mean-reversion after a dump** (buy the dip on a rule) — `RULES_DIRECTIONAL_CONTINUOUS`
- **Front-running MEV / sandwich attacks** — explicitly out of scope; MEV policies block this

## See also

- Family: [arbitrage-structural.md](../families/arbitrage-structural.md)
- MEV protection: [../cross-cutting/mev-protection.md](../cross-cutting/mev-protection.md)
- Venue collateral rules (LTV, liquidation thresholds, bonus per asset):
  [../../../02-venues/venue-registry-reference.md](../../../02-venues/venue-registry-reference.md)
