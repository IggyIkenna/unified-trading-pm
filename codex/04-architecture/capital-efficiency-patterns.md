---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Capital Efficiency Patterns

> **What it is:** The recurring patterns that unlock capital efficiency when multiple strategies share a venue account
> or when a single strategy uses structural venue features (cross-margin, portfolio margin, LTV-based lending, greek
> netting, atomic composites). Each pattern names the venue features it requires and the coordination primitives it
> depends on.

## Why this matters

Running each strategy with dedicated capital on a dedicated account wastes:

- Margin (each strategy posts full margin independently)
- Bandwidth (redundant positions that could offset)
- Fees (VIP tiers require aggregate volume)
- Capital at rest (idle collateral)

Capital efficiency patterns reclaim that waste — sometimes 2–5× effective leverage on the same underlying equity.

## Pattern 1: Cross-margin basis + directional (CEX)

**Setup:**

- Strategy A: directional long BTC (perp)
- Strategy B: basis trade BTC (spot + perp)
- Same client, same Binance account, cross-margin enabled

**Benefit:** Strategy B's short perp leg contributes margin relief to Strategy A's long perp (opposite sign on perp
side). Effective margin use lower than sum-of-parts.

**Requirements:**

- Venue supports cross-margin
- Venue-account coordination primitives active (aggregation + pre-flight)
- Attribution rules defined for shared positions

**Trap:** Liquidation cascade — if cross-margin breaches, BOTH strategies' positions liquidate together. Risk gates must
model joint risk, not per-strategy.

## Pattern 2: Portfolio margin — greek netting (Deribit)

**Setup:**

- Multiple vol strategies on Deribit with different option positions
- Same client, same Deribit account, portfolio margin enabled

**Benefit:** Portfolio margin nets greeks across the book — long calls + short puts at same strike offset. Margin
requirement scales with net greek exposure, not sum of individual option positions.

**Requirements:**

- Deribit portfolio margin access (qualification-based)
- Execution-service computes joint greek state for pre-flight
- Risk-and-exposure-service sees joint greeks

**Trap:** Synthetic perp via long-call + short-put can become a perp-equivalent without "showing" as a perp position —
risk models must account for equivalent delta.

## Pattern 3: Reg-T netting (IBKR equities)

**Setup:**

- Long equity basket via IBKR
- Short-ETF hedge via IBKR
- Same IBKR account

**Benefit:** Reg-T margin rules net long and short positions in overlapping names. Effective margin lower.

**Requirements:**

- IBKR account with margin (not cash-only)
- Execution-service respects IBKR's position-level netting

## Pattern 4: LTV-based DeFi lending loop

**Setup:**

- Supply stETH as collateral on Aave (75% LTV for stETH)
- Borrow ETH against it
- Stake borrowed ETH via Lido → wstETH
- Supply wstETH back as collateral
- Borrow again
- Recursive loop

**Benefit:** Leverage ETH staking yield by ~3× (depending on LTV decay per recursion). See
[../09-strategy/architecture-v2/archetypes/carry-recursive-staked.md](../09-strategy/architecture-v2/archetypes/carry-recursive-staked.md).

**Requirements:**

- Protocol supports wstETH collateral (Aave V3 ETH)
- LST haircut model in execution-service pre-flight
- ATOMIC_ON_CHAIN for single-tx loop (else per-step rollback risk)
- Health factor monitor in live ops

**Trap:** stETH depeg (2022-06 / 2024-stress) liquidates the loop cascading. HF alerts + auto-deleveraging required.

## Pattern 5: Delta-hedged vol on same account

**Setup:**

- Long straddle on Deribit
- Delta hedge via Deribit perp

**Benefit:** Portfolio margin recognizes the delta-hedge offsets the option delta; margin scales with vega + gamma +
second-order, not notional.

**Requirements:**

- Deribit portfolio margin
- Delta-hedge executed on same account (not cross-venue)

## Pattern 6: LP + borrow on same chain

**Setup:**

- Supply USDC/WETH LP position on Uniswap V3
- Use LP NFT as collateral on some protocols (e.g., Gamma, Panoptic)
- Borrow against it
- Deploy borrowed into farming / yield

**Benefit:** LP earns fees; collateral serves dual purpose.

**Requirements:**

- Protocol accepts LP NFTs as collateral (limited set)
- Rebalancing LP range triggers reconciliation of LTV

**Trap:** Concentrated LP exit price differs from entry; collateral value shifts with price; LTV can blow up.

## Pattern 7: Unity pooled book with child arb

**Setup:**

- Single Unity wallet serves multiple sports strategies
- Strategy A: arb on 1X2
- Strategy B: ML directional on over/unders
- Strategy C: market making on totals

**Benefit:** One deposit serves all three strategies; Unity's internal SOR picks best child book per leg;
subscription-waiver turnover thresholds crossed faster via aggregate volume.

**Requirements:**

- Unity meta-broker adapter
- PBMS attribution per strategy (parsed from Unity fill reports with child-book tag)
- Per-strategy position accounting despite shared wallet

## Pattern 8: IBKR basket netting

**Setup:**

- Stat arb cross-sectional: 100 longs, 100 shorts
- Portfolio margin IBKR

**Benefit:** IBKR portfolio margin recognizes factor-neutral basket as lower-risk; margin requirement scales with
residual beta/vol, not gross.

**Requirements:**

- IBKR portfolio margin eligibility (qualification)
- Basket-level margin model in pre-flight

## Pattern 9: Binance cross-margin netting with ~5% headroom

**Setup:**

- Hedged basis: long spot + short perp at Binance
- Same Binance account, cross-margin

**Benefit:** Binance cross-margin recognizes the hedge; practical requirement ~5% of total notional (vs ~20% on isolated
margin per leg).

**Requirements:**

- Cross-margin enabled at Binance
- Pre-flight recognizes hedge; doesn't double-count margin

**Trap:** Funding-rate fluctuations still require margin buffer for variation; 5% is minimum-at-rest, not total need.

## Pattern 10: Same-chain atomic composites

**Setup:**

- Flash loan → liquidate underwater position → sell collateral → repay flash loan → keep spread
- Single Ethereum tx

**Benefit:** Zero capital required for the flash-loan loop; only gas.

**Requirements:**

- Flash loan receiver contract deployed (per CLAUDE.md, `FlashLoanReceiver.sol`)
- Error classification for flash-loan reverts (per `DefiErrorCode`)
- Gas budget + MEV-aware submission

## Pattern 11: Unity deposit leverage (commercial)

**Setup:**

- Deposit $10.8k (refundable at $5.3M volume)
- Trade via Unity
- Deposit acts as bond, not margin — doesn't consume buying power

**Benefit:** Unity extends credit-against-deposit; capital-efficient relative to per-book deposits.

**Requirements:**

- Unity relationship established
- Subscription: $2.6k/mo (waived at $260k/mo turnover)

## Pattern 12: Options spread vs outright

**Setup:**

- Instead of outright long call, deploy call spread (long K1 + short K2)

**Benefit:** Portfolio margin requirement scales with max loss = K2 - K1 - premium, not notional.

**Requirements:**

- Portfolio margin account

**Tradeoff:** Capped upside; pick when upside capping is acceptable.

## Cross-pattern interactions

Multiple patterns compose:

- Pattern 2 (portfolio margin) + Pattern 5 (delta-hedge) on Deribit
- Pattern 4 (LTV loop) + Pattern 10 (atomic composite) on Aave
- Pattern 1 (cross-margin) + Pattern 9 (basis) on Binance
- Pattern 7 (Unity pool) + Pattern 11 (deposit leverage) on Unity

Venue-account coordination primitives
([../09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](../09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md))
make composition safe.

## Risk scaling

Capital efficiency is NOT free — risk concentration grows with efficiency:

- Higher leverage → tighter liquidation triggers
- Shared account → joint liquidation
- Greek netting → correlated blow-ups in regime shifts
- LP-as-collateral → dual price dependency

Risk-and-exposure-service must model joint risk, not per-strategy. Family-level limits + correlation caps handle this.

## Venue-feature requirements summary

| Pattern               | Venue feature required         |
| --------------------- | ------------------------------ |
| Cross-margin basis    | Binance/OKX/Bybit cross-margin |
| Portfolio margin vol  | Deribit portfolio margin       |
| Reg-T netting         | IBKR margin                    |
| LTV loop              | Aave V3 (wstETH 75%)           |
| Delta-hedged same acc | Deribit portfolio margin       |
| LP + borrow           | Gamma / Panoptic / etc.        |
| Unity pool            | Unity agreement                |
| IBKR basket           | IBKR portfolio margin          |
| Binance basis ~5%     | Binance cross-margin           |
| Atomic composites     | EVM chain                      |
| Unity deposit         | Unity commercial terms         |
| Spread vs outright    | Portfolio margin account       |

## Cross-references

- Venue-account coordination:
  [../09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](../09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md)
- Venue registry: [../02-venues/venue-registry-reference.md](../02-venues/venue-registry-reference.md)
- Unity: [../02-venues/unity-integration.md](../02-venues/unity-integration.md)
- Recursive staked:
  [../09-strategy/architecture-v2/archetypes/carry-recursive-staked.md](../09-strategy/architecture-v2/archetypes/carry-recursive-staked.md)
- Liquidation archetype:
  [../09-strategy/architecture-v2/archetypes/liquidation-capture.md](../09-strategy/architecture-v2/archetypes/liquidation-capture.md)
- Risk gates:
  [../09-strategy/architecture-v2/cross-cutting/risk-gates.md](../09-strategy/architecture-v2/cross-cutting/risk-gates.md)

## Not in this doc

- **Per-venue margin formula implementations** — venue registry + execution-service pre-flight
- **LTV haircut tables** — venue capability registry
- **Greek calculator** — pricing engine / options service
- **Liquidation thresholds** — per-venue capability registry
- **Flash-loan receiver internals** — `deployment-service/contracts/FlashLoanReceiver.sol`
