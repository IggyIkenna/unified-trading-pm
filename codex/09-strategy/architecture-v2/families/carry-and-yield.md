---
doc_type: codex-ssot
title: "Family: Carry & Yield"
summary:
  The Carry & Yield strategy family — 10 archetypes capturing a paid rate/yield differential (perp funding, dated basis,
  staked basis, recursive borrow, lending-APY rotation, simple staking); edge is rate-differential sustained above a
  cost threshold, rebalanced periodically.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, carry, basis, staking, yield, funding, defi]
related:
  [
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
    /codex/09-strategy/architecture-v2/families/market-making.md,
    ../archetypes/carry-basis-perp.md,
    ../archetypes/yield-rotation-lending.md,
  ]
created: 2026-04-17
authoritative_for: [Carry & Yield strategy family spec (alpha thesis + 10 archetypes)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-dated-inv.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-dated.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis-dated.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Family: Carry & Yield

> **Alpha source:** Rate / yield differential capture. Whether the rate is funding on a perp, lending APY on a protocol,
> staking reward on a PoS chain, or basis spread on a dated future, the common thesis is: capture a paid rate that
> compensates for holding a position.
>
> **Primary edge method:** Rate-differential sustained above a cost threshold.
>
> **Typical hold policies:** CONTINUOUS (with periodic rebalance triggers) or HOLD_UNTIL_FLIP.
>
> **Archetype count:** 10 — distinguished by position structure and capital utilization pattern. (6 original + 4 added
> 2026-05-18: `CARRY_BASIS_DATED_INV`, `CARRY_BASIS_PERP_INV`, `CARRY_RECURSIVE_BORROW_LENDING_ONLY`,
> `CARRY_STAKED_BASIS_DATED` per taxonomy V-1, uac@0196842.)

## Alpha thesis

The Carry & Yield family captures the family of alpha sources that pay you for holding something (or pay differentially
between venues):

- **Basis (dated)**: long spot + short dated future locks in the futures-spot premium/discount, captured at futures
  expiry
- **Basis (dated, inverse)**: short spot + long dated future captures backwardation premium (negative funding regime)
- **Basis (perp)**: long spot + short perp captures funding rate while staying delta-neutral
- **Basis (perp, inverse)**: short spot + long perp captures negative funding rate (CeFi-margin-funded, USD\* only)
- **Staked basis (perp)**: stake ETH → LST → pledge on perp venue → short perp; earn staking yield + funding
- **Staked basis (dated)**: stake ETH → LST → pledge on dated-futures venue → short dated future; locks in basis at
  entry, staking yield accrues during hold
- **Recursive staked basis**: leverage the staked basis via borrow-against-LST-restake loop (ETH/SOL share class)
- **Recursive borrow lending only**: pure cross-venue lending/borrow APY arb with no staking leg (USD\* or single-token)
- **Yield rotation**: supply stable / BTC / ETH to the best-APY lending protocol per chain, rebalance as APYs shift
- **Simple staking**: stake a PoS asset for validator yield, no basis/leverage

All have a shared structural property: **the alpha is a rate/yield that is observable, persistent over short windows,
and rebalanced periodically** as rates shift.

**Not in this family:**

- Unhedged funding carry (you'd be directional — that's ML or Rules Directional)
- Pure capital appreciation with incidental yield (directional families)
- Yield farming with impermanent loss as primary risk (that's MARKET_MAKING — active LP)

## 10 Archetypes

| Archetype                                                                                     | Position structure                                    | Primary rate captured                        | When to use                                                                  |
| --------------------------------------------------------------------------------------------- | ----------------------------------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------- |
| [`CARRY_BASIS_DATED`](../archetypes/carry-basis-dated.md)                                     | Long spot + short dated future                        | Basis convergence (futures − spot at expiry) | TradFi commodities/equity index basis; Deribit dated futures                 |
| [`CARRY_BASIS_DATED_INV`](../archetypes/carry-basis-dated-inv.md)                             | Short spot + long dated future                        | Backwardation premium (inverse basis)        | Backwardation regime; negative dated basis; added 2026-05-18                 |
| [`CARRY_BASIS_PERP`](../archetypes/carry-basis-perp.md)                                       | Long spot + short perp                                | Funding rate (positive)                      | Crypto basis: Uniswap/CEX spot + CEX/DEX perp                                |
| [`CARRY_BASIS_PERP_INV`](../archetypes/carry-basis-perp-inv.md)                               | CeFi margin → borrow + sell spot → long perp          | Negative funding rate (inverse carry)        | Negative funding regime; was `CARRY_RECURSIVE_BORROW_PERP_HEDGED`            |
| [`CARRY_STAKED_BASIS`](../archetypes/carry-staked-basis.md)                                   | Stake → LST → perp venue collateral → short perp      | Staking yield + funding                      | ETH on Lido + perp; SOL on Jito + Drift                                      |
| [`CARRY_STAKED_BASIS_DATED`](../archetypes/carry-staked-basis-dated.md)                       | Stake → LST → perp venue collateral → short dated fut | Staking yield + locked dated basis at entry  | Higher carry than perp when dated basis > expected funding; added 2026-05-18 |
| [`CARRY_RECURSIVE_STAKED`](../archetypes/carry-recursive-staked.md)                           | Recursive loop: stake → borrow → stake → borrow → ... | Leveraged staking yield                      | ETH/SOL leveraged staking; carries liquidation cascade risk                  |
| [`CARRY_RECURSIVE_BORROW_LENDING_ONLY`](../archetypes/carry-recursive-borrow-lending-only.md) | Lend + borrow same token cross-venue; no staking leg  | Cross-venue lending/borrow APY spread        | USDT/ETH cross-protocol rate spread; flash-loan or sequential unwind         |
| [`YIELD_ROTATION_LENDING`](../archetypes/yield-rotation-lending.md)                           | Supply asset to best-APY protocol/chain               | Lending APY differential                     | USDC/USDT/wBTC/ETH lending rotation across Aave, Compound, Euler, Kamino     |
| [`YIELD_STAKING_SIMPLE`](../archetypes/yield-staking-simple.md)                               | Stake asset, earn validator reward                    | Pure staking reward                          | Standalone staking without basis leg; ETH on Lido, SOL on Jito/Marinade      |

## Shared primitives (all archetypes)

- **Rate / yield monitor**: continuous polling of funding rates, APYs, staking rewards, basis spreads per eligible venue
- **Rate differential computer**: compute spreads between venues/protocols; detect rotation opportunities
- **Delta-neutral position tracker** (for basis archetypes): track spot position vs hedge position; maintain delta
  within band
- **Rebalance scheduler**: time-based (e.g., every N hours) and event-based (e.g., funding tick, APY threshold crossed,
  basis widened)
- **Collateral utilization policy**: what to do with unused collateral (idle, lent, staked)
- **Liquidation monitor** (for leveraged variants): track health factor, auto-deleverage before breach
- **Gas-aware rebalancer** (DeFi): don't rotate for small differentials that don't cover gas; threshold configurable

## Typical signal sources

| Signal               | Source                                                                |
| -------------------- | --------------------------------------------------------------------- |
| Funding rate (perp)  | CEX/DEX funding-rate API; updated per 4h / 1h / 8h depending on venue |
| Staking reward rate  | Staking protocol APY feed (on-chain)                                  |
| Lending supply APY   | Aave/Compound/Euler on-chain reads                                    |
| Basis spread (dated) | Futures price - spot price from exchange feed                         |
| Health factor        | Lending protocol on-chain read                                        |
| Gas price            | Chain RPC                                                             |

## Typical edge methods

- **Rate differential sustained**: `rate_a > rate_b + threshold_over_minimum_duration`
- **Net carry > cost**: after fees, slippage, gas, liquidation buffer, the net carry is positive
- **Spread convergence** (dated): future - spot > cost_of_trade, reliable convergence at expiry
- **Threshold crossing** (rotation): APY differential between venues > gas+bridge cost to rotate

## Position structure

Each archetype has distinct position structure — see individual archetype docs. Common patterns:

- **Delta-neutral paired**: equal notional long + short (basis archetypes)
- **Leveraged paired**: larger short leg than spot leg, using lending collateral (recursive)
- **Single-sided**: supply-only for yield rotation and simple staking

## Typical staking methods

| Method                      | When used                                                                      |
| --------------------------- | ------------------------------------------------------------------------------ |
| Fixed % equity              | Default — allocate a configured fraction of equity to the strategy             |
| Per-venue allocation policy | For yield rotation: split across venues by weight                              |
| Delta-neutral paired        | For basis: equal notional on both legs, computed from equity + target leverage |
| Leverage-capped             | For recursive: max leverage from venue LTV + safety buffer                     |

## Venue patterns

- **Basis dated**: TradFi venues (CME futures + underlying spot); Deribit dated
- **Basis perp**: CEX spot + CEX perp (single venue netted, e.g., Binance) OR DEX spot + CEX/DEX perp (cross-venue)
- **Staked basis**: Lido/Rocket/Jito + Aave/Compound/Kamino + Hyperliquid/Binance/Drift
- **Recursive staked**: Same as staked basis, with recursive leveraging on lending protocol
- **Yield rotation**: Aave multichain (primary) + Compound/Euler/Morpho/Kamino (multi-protocol variant)
- **Simple staking**: Lido, Rocket Pool, Jito, Marinade

## Expression options

- **Basis**: spot instrument + perp/future instrument
- **Staked basis**: LST + perp instrument
- **Yield rotation**: asset (USDC, USDT, wBTC, ETH, stETH)
- **Simple staking**: native token (ETH, SOL)

## Risk profile

- **Drawdowns**: lower than directional strategies in normal regimes (basis is delta-neutral; yield is directionally
  neutral). Tail-risk drawdowns — funding flip, LST depeg, cascading liquidation — are severe and warrant kill switches.
- **Tail risks**:
  - Funding rate reversal (basis)
  - LST depeg (staked basis)
  - Cascading liquidation (recursive staked)
  - Smart-contract risk (all DeFi variants)
  - Chain halt / bridge delay (multi-chain)
- **Sharpe (well-run basis + yield, normal regime)**: 1.5–3.5. Sharpe collapses on tail events; kill switches enforce
  the ceiling loss.
- **Kill switches**: LST depeg > threshold, health factor breach, funding reversal, rapid APY change indicating
  disruption

## Latency Requirements

**Category: `Low`** — sub-second inter-leg execution gap, live mode only (batch mode has no latency requirements; it
replays historical data at compute speed). Baseline: the archived
[`/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md`](/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md)
table — SUPERSEDED as a doc, but its **Delta-One Basis** row (Tick-to-Signal <5 s / Signal-to-Order <2 s / Order-to-Fill
<30 s / Total E2E <37 s, Category **Medium**) is the operative baseline and is **corrected, not confirmed**, here. The
archived doc classified basis as Medium because the decision cycle (rate monitor → signal → decide) tolerates seconds —
funding rates and basis spreads are slow-moving signals that don't flip sub-second. But the 2026-08-10 operator ruling
corrects this: for a multi-leg carry position, the **inter-leg execution gap** (the time between the lead-leg fill and
the lag hedge-leg fill) must be ms-realm, regardless of how slow the decision cycle is. The decision is slow; the
execution of the paired legs, once the decision to enter (or exit) is made, is not.

| Segment                              | Budget                                                        | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------------------------------------ | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Tick-to-Signal                       | < 5 s                                                         | Rate/yield monitor → funding-rate / APY / basis-spread tick → feature → signal. Rates are slow-moving (funding updates per 1h/4h/8h; APYs shift gradually; basis spreads widen/narrow over minutes-to-hours). The decision cycle tolerates seconds; this is the one segment the archived doc's Medium categorization was correct about.                                                                                                                                                                                                                                  |
| Signal-to-Order (lead leg)           | < 2 s                                                         | StrategyInstruction → routing → venue adapter → lead-leg order submitted (spot buy, LST mint, collateral deposit). Seconds are acceptable because the basis spread hasn't moved materially in this window; the lead leg is just acquiring the position, not capturing the spread yet.                                                                                                                                                                                                                                                                                    |
| Order-to-Fill (lead leg)             | Venue-dep. (CeFi: <50 ms; DeFi: block-time-bound)             | CeFi spot venues: 20–50 ms order submission + matching (archived venue-baselines table: Binance 20–50 ms, Coinbase, Deribit 15–40 ms). DeFi staking legs: Ethereum L1 ~12 s block time, Arbitrum ~250 ms, Solana ~400 ms — block time, not network latency, dominates. The staking-leg fill is NOT the gap constraint (see below).                                                                                                                                                                                                                                       |
| **Inter-leg execution gap**          | **ms-realm** (< 500 ms operating target; < 100 ms achievable) | **The binding constraint — this is why the category is `Low`.** Lead-leg fill confirmed → hedge-leg order submitted → hedge-leg fill. For single-venue netted basis (Binance spot + Binance perp): achievable <100 ms. For cross-venue basis (Coinbase spot → Deribit perp): the budget allows cross-venue order routing within ms timing. For staked-basis: the staking-leg fill confirmation is DeFi-block-time-bound, but the hedge-leg submits to a CeFi perp venue — the gap from hedge-submit to hedge-fill IS ms-realm regardless of how long the stake leg took. |
| Order-to-Fill (hedge leg)            | Venue-dep. (CeFi perp: 20–50 ms)                              | CeFi perp/futures matching engine: Binance 20–50 ms, Deribit 15–40 ms, Hyperliquid 20–60 ms, Bybit 25–70 ms (archived venue-baselines table). The hedge leg lands on the same or a nearby venue; matching-engine latency is the floor.                                                                                                                                                                                                                                                                                                                                   |
| **Total E2E (decision + execution)** | **< 40 s** (CeFi basis); **block-time + <5 s** (DeFi staked)  | Sum of all segments. This number is NOT what drives the deployment profile — the inter-leg gap does. A 40 s total E2E with a <100 ms inter-leg gap is a Low-latency strategy because the spread-capture happens inside that gap; the slow decision cycle is just when you start the clock.                                                                                                                                                                                                                                                                               |

`Inter-leg execution gap (lead fill → hedge fill)` in the UI dashboard is the monitor for the binding constraint;
`Total E2E` is informative but not the number that gates the deployment profile.

**Deployment implication:** `Low` ⇒ the `co_located_vm` deployment profile per the `/configs/runtime-topology.yaml`
`deployment_profiles` category mapping, referencing
[`/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md`](/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md)
§ 6. The current `topology_requirements` rows for `CARRY_BASIS_PERP` and `CARRY_STAKED_BASIS` (execution `isolated`,
strategy `shared OK`, co-location `no`, min SLA `standard`) are a **discrepancy** the paired deployment-profile
derivation todo resolves
([`/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md`](/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md)
todo 8): `Low` latency requires execution + strategy co-located on the same VM at min SLA `premium`, matching the
`MARKET_MAKING_CONTINUOUS` row. The basis/staking-basis archetypes join market-making and arbitrage-structural as
`co_located_vm` families.

### Decision latency vs. inter-leg execution gap

The archived doc's Medium category for Delta-One Basis was correct about the decision cycle (seconds are fine for
rate/yield monitoring) but missed the multi-leg execution constraint (seconds are NOT fine for the gap between legs).
The 2026-08-10 operator ruling is explicit: "we are executing two legs of a trade... how are we ensuring the lag leg
followed by the lead leg is ms timing." For this family, the binding latency constraint is the **inter-leg execution
gap**, not the decision latency:

- **Basis perp** (`CARRY_BASIS_PERP`): long spot → short perp. The spot fill is the lead leg; the perp-hedge short is
  the lag leg. If the perp order lands seconds after the spot fill, the funding rate or basis spread can move, and the
  entry spread measured pre-trade is no longer the spread captured. The gap must be ms-realm: spot fills, perp order
  submits immediately, perp fills at the same (or near-same) basis. Single-venue netted (Binance spot + Binance perp,
  same account): the hedge can be a single order on the same matching engine — gap <100 ms achievable without
  cross-venue routing.
- **Basis perp inverse** (`CARRY_BASIS_PERP_INV`): short spot → long perp. Same structure inverted; same gap constraint.
- **Basis dated** (`CARRY_BASIS_DATED`): long spot → short dated future. CME Globex / Deribit dated futures support
  sub-100ms order submission; the gap is enforceable on TradFi venues with co-location. The futures-spot basis at entry
  is the alpha; a lagged hedge captures a different basis.
- **Basis dated inverse** (`CARRY_BASIS_DATED_INV`): short spot → long dated future. Same gap constraint.
- **Staked basis perp** (`CARRY_STAKED_BASIS`): stake ETH/SOL → LST received → pledge LST as collateral on perp venue →
  short perp. The staking leg (L1 smart-contract interaction) is DeFi-block-time-bound and is NOT the gap constraint —
  the gap is between perp-collateral-pledge confirmation and perp-short order fill, both on the same CeFi venue, and
  must be ms-realm. Live instances (JitoSOL×Drift, mSOL×Drift, stETH×Deribit, stETH×Bybit UTA) all hedge on CeFi perp
  venues where ms timing is achievable.
- **Staked basis dated** (`CARRY_STAKED_BASIS_DATED`): same as staked-basis-perp but the hedge is a dated future; the
  gap is still CeFi-venue-bound at ms timing.
- **Recursive staked basis** (`CARRY_RECURSIVE_STAKED`): the initial stake leg is DeFi-block-time-bound; each recursive
  borrow+stake iteration adds another block-time window. The gap constraint applies at the perp-hedge step after the
  loop completes — same ms-realm requirement as non-recursive staked basis.
- **Recursive borrow lending only** (`CARRY_RECURSIVE_BORROW_LENDING_ONLY`): cross-venue lend+borrow with no staking
  leg. The borrow leg is the hedge; the lend leg is the lead. Same inter-leg gap constraint — the APY spread can move
  against the position if the borrow lags the lend.

### Single-sided sub-families (yield rotation, simple staking)

The two single-sided archetypes in this family — `YIELD_ROTATION_LENDING` and `YIELD_STAKING_SIMPLE` — have no paired
legs, so the inter-leg gap concept does not apply. These inherit the **Medium** category from the archived doc's closest
analogs (Funding Rate Harvest / Yield Optimization rows) per the audit plan's
[rubric table](/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md). Decision latency alone
governs; the P3 population todo for `vol-trading.md` / `event-driven.md` / `portfolio.md` will apply the same derivation
pattern and state the reasoning explicitly in each doc.

## UI dashboard (shared)

- Rate / APY curves over time per venue
- Current spreads + rebalance history
- Delta exposure tracker (for basis archetypes)
- Health factor gauge (for leveraged variants)
- Per-venue P&L attribution
- Carry yield accrued vs paid
- Gas cost per rebalance
- Liquidation distance (leveraged variants)

## Required subscriptions

Config references:

- One or more **venue_capability_refs** (to read current rates, fees, haircuts)
- One or more **feature_group_refs** (for derived signals like vol-adjusted carry)
- Optional **model_id** (e.g., if using ML to predict funding-rate regime shifts)
- One **execution_policy_ref**

## Typical instance examples

```
Basis perp:
  CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod
  CARRY_BASIS_PERP@binance-binance-btc-usdt-prod       (single-venue netted)
  CARRY_BASIS_PERP@coinbase-deribit-btc-usd-prod
  CARRY_BASIS_PERP@binance-binance-multicoin-usdt-prod (multi-coin rotating)

Basis dated:
  CARRY_BASIS_DATED@cme-cl-front-curve-usd-prod      (oil front vs second month)
  CARRY_BASIS_DATED@deribit-btc-quarterly-usdt-prod

Staked basis (active 2026-05-20, from catalog.py _build_carry_staked_basis):
  CARRY_STAKED_BASIS@jito-drift-f100-usdc-1h-usdc-v2-prod     # JitoSOL × DRIFT (Solana)
  CARRY_STAKED_BASIS@marinade-drift-f100-usdc-1h-usdc-v2-prod # mSOL × DRIFT (Solana)
  CARRY_STAKED_BASIS@lido-deribit-f100-usdc-1h-usdc-v2-prod   # stETH × DERIBIT (ETH, USDC)
  CARRY_STAKED_BASIS@lido-bybit-f100-usdt-1h-usdt-v2-prod     # stETH × BYBIT UTA (ETH, USDT)

Recursive staked:
  CARRY_RECURSIVE_STAKED@lido-aave-eth-prod          (ETH on Ethereum)
  CARRY_RECURSIVE_STAKED@jito-kamino-sol-prod         (SOL on Solana)

Yield rotation:
  YIELD_ROTATION_LENDING@aave-multichain-usdc-prod
  YIELD_ROTATION_LENDING@aave-compound-ethereum-usdc-prod
  YIELD_ROTATION_LENDING@aave-multichain-wbtc-prod
  YIELD_ROTATION_LENDING@kamino-sol-usdc-prod

Simple staking:
  YIELD_STAKING_SIMPLE@lido-eth-prod
  YIELD_STAKING_SIMPLE@jito-sol-prod
```

## Reaction to capital flow events

```python
def react_to_equity_change(self, new_equity_usd: Decimal) -> list[StrategyInstruction]:
    self.equity_usd = new_equity_usd
    # For basis: scale both legs proportionally, maintain delta-neutral
    # For yield rotation: recompute per-venue target supplied
    target_state = self._compute_target_state()
    return self._emit_reconciliation(self.current_state, target_state)
```

Per-archetype reaction:

- **Basis**: both legs scale together → ATOMIC reconciliation to avoid delta breach
- **Recursive**: scale initial stake; recursion depth preserved; no additional leverage change
- **Yield rotation**: scale per-venue targets proportionally
- **Simple staking**: scale staked amount

## Migration from legacy docs

| Legacy                                                                         | Mapping                                                  | Notes                                                                  |
| ------------------------------------------------------------------------------ | -------------------------------------------------------- | ---------------------------------------------------------------------- |
| `defi/basis-trade.md`                                                          | `CARRY_BASIS_PERP`                                       | Generic archetype                                                      |
| `defi/btc-basis-trade.md`                                                      | `CARRY_BASIS_PERP`                                       | BTC instance of same archetype                                         |
| `defi/l2-basis-trade.md`                                                       | `CARRY_BASIS_PERP`                                       | L2 spot + CEX/DEX perp                                                 |
| `defi/sol-basis-trade.md`                                                      | `CARRY_BASIS_PERP`                                       | SOL instance                                                           |
| `defi/staked-basis.md`                                                         | `CARRY_STAKED_BASIS`                                     | Generic                                                                |
| `defi/sol-staked-basis.md`                                                     | `CARRY_STAKED_BASIS`                                     | SOL instance                                                           |
| `defi/recursive-staked-basis.md`                                               | `CARRY_RECURSIVE_STAKED`                                 | Generic                                                                |
| `defi/aave-lending.md`                                                         | `YIELD_ROTATION_LENDING`                                 | Multi-chain via config                                                 |
| `defi/btc-lending-yield.md`                                                    | `YIELD_ROTATION_LENDING`                                 | wBTC variant                                                           |
| `defi/multi-chain-lending-yield.md`                                            | `YIELD_ROTATION_LENDING`                                 | Consolidates with aave-lending                                         |
| `defi/sol-lending-yield.md`                                                    | `YIELD_ROTATION_LENDING`                                 | Kamino SOL                                                             |
| `defi/cross-chain-yield-arb.md`                                                | `YIELD_ROTATION_LENDING` or `ARBITRAGE_PRICE_DISPERSION` | Depends whether alpha is sustained rate spread or transient dispersion |
| `defi/ethena-benchmark.md`                                                     | Reference section in `CARRY_BASIS_PERP`                  | Benchmark strategy; not deployed                                       |
| Code: `strategy-service/.../basis_trade.py` (+ btc, l2, sol variants)          | `CarryBasisPerpEngine`                                   | Shared engine, per-instance configs                                    |
| Code: `strategy-service/.../staked_basis.py` (+ sol variant)                   | `CarryStakedBasisEngine`                                 | Shared engine                                                          |
| Code: `strategy-service/.../recursive_staked_basis.py`                         | `CarryRecursiveStakedEngine`                             |                                                                        |
| Code: `strategy-service/.../aave_lending.py` (+ btc, sol, multichain variants) | `YieldRotationLendingEngine`                             | Shared engine                                                          |

## Cross-references

- Archetypes: [carry-basis-dated](../archetypes/carry-basis-dated.md),
  [carry-basis-dated-inv](../archetypes/carry-basis-dated-inv.md),
  [carry-basis-perp](../archetypes/carry-basis-perp.md), [carry-basis-perp-inv](../archetypes/carry-basis-perp-inv.md),
  [carry-staked-basis](../archetypes/carry-staked-basis.md),
  [carry-staked-basis-dated](../archetypes/carry-staked-basis-dated.md),
  [carry-recursive-staked](../archetypes/carry-recursive-staked.md),
  [carry-recursive-borrow-lending-only](../archetypes/carry-recursive-borrow-lending-only.md),
  [yield-rotation-lending](../archetypes/yield-rotation-lending.md),
  [yield-staking-simple](../archetypes/yield-staking-simple.md)
- Venue collateral rules:
  [../../../02-venues/venue-registry-reference.md](../../../02-venues/venue-registry-reference.md) (LTV, haircuts,
  liquidation thresholds)
- Capital efficiency patterns (e.g., single-venue netted basis):
  [../../../04-architecture/capital-efficiency-patterns.md](../../../04-architecture/capital-efficiency-patterns.md)
- Reward lifecycle (claim, compound, harvest):
  [../../cross-cutting/reward-lifecycle.md](../cross-cutting/reward-lifecycle.md) (legacy, preserved)
- Rate impact modeling: [../../cross-cutting/rate-impact-model.md](../cross-cutting/rate-impact-model.md) (legacy,
  preserved)
