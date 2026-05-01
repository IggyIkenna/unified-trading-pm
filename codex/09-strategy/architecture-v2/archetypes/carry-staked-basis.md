---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `CARRY_STAKED_BASIS`

> **Family:** [Carry & Yield](../families/carry-and-yield.md) **Settlement model:** Continuous; multi-step paired
> position with collateral utilization. **Code module (target):**
> `strategy-service/engine/strategies/carry_staked_basis_engine.py`

## What it does

Three-leg strategy: stake native asset → receive liquid staking token (LST) → pledge LST as collateral on lending
protocol → borrow base currency → short perp on CEX/DEX. Earn staking yield + funding rate simultaneously on the same
capital.

## Token / position flow

```
1. STAKE: deposit ETH → Lido → receive stETH (or deposit SOL → Jito → JitoSOL)
   Earning staking reward (e.g., ~3.5% APY ETH, ~7% APY SOL).

2. PLEDGE: deposit stETH as collateral on Aave (LTV 75%, haircut implied)
   Now can borrow against it.

3. BORROW: borrow USDC (or USDT) up to (LTV × buffer) of pledged stETH.
   Lending cost: typically 5-8% APY on stablecoin borrows.

4. SHORT PERP: short ETH perp on CEX with the borrowed USDC as margin.
   Position sized to match the stETH notional (delta-neutral).
   Earning funding rate.

5. NET CARRY: total_lst_yield + funding rate − borrow cost − fees.
   Breakeven when carry > costs + haircut risk provision.

   For restaking-eligible LSTs (weETH, pufETH, ankrETH, ETHx) `total_lst_yield` is the sum of THREE
   on-chain-discoverable layers (see
   [restaking-reward-economics.md](../../cross-cutting/restaking-reward-economics.md)):
     - CARRY_BASE              (exchange_rate appreciation)
     - CARRY_AVS_CONTINUOUS    (EigenLayer/Karak per-token rewards, dust-converted to ETH via simulated swap)
     - CARRY_ISSUER_SEASONAL   (Ether.fi quarterly / Puffer / Ankr / Stader episodic, dust-converted to ETH)

   Each layer has its own pnl-attribution row + a paired REWARD_REALISATION_SLIPPAGE row capturing the dust-conversion
   cost. Strategy may choose to HOLD vesting tokens (e.g. EIGEN with 4-yr cliff) via the
   `ConvertDustInstruction.hold_until_vested_tokens` field rather than realise immediately.

   Both legs (LST stake + perp short) carry their own target_leverage and target_net_delta; the LeveragedLegController
   maintains them across PnL drift via cash-sweep auto-rebalancing. Standard configuration is target_net_delta=0
   (delta-neutral) with each leg at the same target_leverage (e.g. 4x4x → gross 8x exposure, zero net ETH delta).

6. REBALANCE triggers:
   - Health factor drift → either add collateral or reduce borrow
   - Funding collapses → unwind short perp + repay borrow (keep stETH for staking)
   - stETH depeg > threshold → KILL SWITCH (unwind everything)
```

## Supported venues / instruments

**Coverage matrix:** See
[`../category-instrument-coverage.md § 7. CARRY_STAKED_BASIS`](../category-instrument-coverage.md#7-carry_staked_basis)
for the authoritative staking × lending × perp combinations and share-class mapping.

## Config schema

```yaml
staking_protocol: LIDO
staking_instrument: "LIDO:ETH-stETH"
lending_protocol: AAVE_V3_ETHEREUM
collateral_asset: stETH
borrow_asset: USDC
perp_venue: HYPERLIQUID
perp_instrument: "HYPERLIQUID:PERPETUAL:ETH-USD"
share_class: ETH # denominated in ETH
target_health_factor: 1.5
max_health_factor_breach: 1.2 # auto-deleverage if breach
target_funding_rate_bps: 80
exit_funding_rate_bps: 20
max_stETH_depeg_bps: 100 # kill switch at 1% depeg
max_allocated_equity_pct: 0.40
execution_policy_ref: defi-cefi-combined-v5
```

## Execution semantics

Entry is a sequence of ATOMIC bundles + cross-venue legs:

1. ATOMIC: `STAKE` on Lido → receive stETH (single tx)
2. ATOMIC: `TRANSFER` stETH to Aave + `LEND` as collateral + `BORROW` USDC (multicall)
3. CROSS-VENUE: `TRANSFER` USDC from Aave → perp venue; `TRADE` short perp (leader-hedge)

Exit is the reverse. ATOMIC within single chain, sequential cross-venue.

## P&L attribution

- **Staking yield**: stETH rebase × holding period
- **Funding yield**: funding_rate × perp_notional × holding period
- **Borrow cost**: lending_rate × borrowed_amount × holding period (negative)
- **Execution alpha**: vs benchmark per leg

## Risk profile

- Drawdowns: low to moderate (delta-neutral on price, exposure to stETH depeg + lending liquidation)
- Typical Sharpe: 2.0-3.5 in normal regimes (excellent for a delta-neutral DeFi strategy)
- Kill switches:
  - stETH / rETH / JitoSOL depeg > configured threshold
  - Aave health factor breach
  - Funding flip persistent beyond threshold
  - Aave liquidity crunch (can't withdraw)
  - Chain congestion (can't rebalance in time)

## Reaction to equity change

Scales all three legs proportionally. Health-factor-aware reconciliation.

## Example instances

```
CARRY_STAKED_BASIS@lido-aave-hyperliquid-eth-prod
CARRY_STAKED_BASIS@rocketpool-aave-binance-eth-prod
CARRY_STAKED_BASIS@jito-kamino-drift-sol-prod
CARRY_STAKED_BASIS@marinade-kamino-drift-sol-prod
```

## Migration from legacy

| Legacy                                         | Notes                                  |
| ---------------------------------------------- | -------------------------------------- |
| `defi/staked-basis.md`                         | Generic ETH staked basis               |
| `defi/sol-staked-basis.md`                     | SOL variant                            |
| Code: `staked_basis.py`, `sol_staked_basis.py` | Collapse into `CarryStakedBasisEngine` |

## Not in this archetype

- **Single LST passive hold** (no perp hedge) — `YIELD_STAKING_SIMPLE`
- **Flash-loan amplified staked basis** (recursive leverage loops) — `CARRY_RECURSIVE_STAKED`
- **Perp funding capture without LST collateral** (spot = raw asset) — `CARRY_BASIS_PERP`
- **Lending the LST for extra yield without the perp hedge** — `YIELD_ROTATION_LENDING`

## See also

- Family: [carry-and-yield.md](../families/carry-and-yield.md)
- Recursive variant: [carry-recursive-staked.md](carry-recursive-staked.md) (adds borrow-and-restake loop)
- Venue collateral rules:
  [../../../02-venues/venue-registry-reference.md](../../../02-venues/venue-registry-reference.md)
