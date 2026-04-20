---
scope: [engineer, admin]
---

# Family: Arbitrage / Structural Edge

> **Alpha source:** Price dispersion between markets OR structural payment from protocol mechanics. Either way, the edge
> is largely risk-free (or near-risk-free) conditional on correct execution. This is NOT directional — we don't take a
> view on where prices go.
>
> **Primary edge method:** Spread > cost (for price dispersion) OR structural bonus > cost (for protocol-mechanic arb).
>
> **Typical hold policies:** ATOMIC (multi-leg simultaneous) or VERY_SHORT_HOLD (minutes to hours).
>
> **Archetype count:** 2 — distinguished by alpha mechanism (dispersion vs protocol bonus).

## Alpha thesis

Arbitrage / Structural Edge captures:

- **Price dispersion**: same/equivalent instrument priced differently on two venues → buy cheap, sell expensive, lock in
  spread
- **Structural payment**: a protocol or venue pays a bonus for a specific service (liquidating an underwater position,
  routing a bridge, providing stability, etc.)

Both share: the edge isn't a view on the future; it's a _present_ dislocation or payment. Risk is execution risk (can
you actually lock in the spread?), not directional risk.

**Not in this family:**

- Basis / funding capture (directional venue-pair that pays you) — goes to [Carry & Yield](carry-and-yield.md)
- Stat arb pairs (mean-reverting spread, NOT risk-free) — goes to [Stat Arb / Pairs](stat-arb-pairs.md)
- MM spread capture (you post liquidity; covers CLOB orderbook MM AND AMM LP, active + passive) — goes to
  [Market Making](market-making.md)
- LP provision of any kind — Uniswap V2 passive, V3 concentrated, Curve stablecoin pools, Balancer weighted — all go to
  [Market Making](market-making.md). The alpha is _fee earnings for providing liquidity_, not price dispersion
- Soft vol-surface residuals that aren't hard no-arb violations (statistical view that surface re-equilibrates) — goes
  to [Vol Trading](vol-trading.md)
- Pure directional ML/rules with incidental dispersion as P&L component — goes to [ML Directional](ml-directional.md) or
  [Rules Directional](rules-directional.md)

## 2 Archetypes

| Archetype                                                                   | Edge mechanism                                                                           | Examples                                                                                                                                                                                                                                                                                                                        |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`ARBITRAGE_PRICE_DISPERSION`](../archetypes/arbitrage-price-dispersion.md) | Price spread between venues on same/equivalent instrument                                | Cross-CEX arb, cross-DEX arb, flash-loan DEX arb, sports cross-book arb, cross-category (Polymarket-Betfair), **cross-venue vol arb (same option quoted at different IVs on Deribit vs OKX options)**, **hard no-arb violations within a single surface (butterfly / calendar / put-call parity)**, funding-rate-dispersion arb |
| [`LIQUIDATION_CAPTURE`](../archetypes/liquidation-capture.md)               | Protocol-paid bonus for repaying an underwater position + seizing collateral at discount | Aave liquidation bots, Compound liquidation, Euler, Morpho                                                                                                                                                                                                                                                                      |

## Shared primitives (both archetypes)

- **Dispersion/opportunity scanner**: continuous monitoring of prices, health factors, or dislocation signals; detect
  when edge exceeds cost threshold
- **Multi-leg execution orchestration**: coordinate execution across venues to lock in edge
- **Cost model**: explicit accounting for slippage, fees, gas, bridge cost, commission before declaring an opportunity
  viable
- **Atomic multi-leg support (where venue supports it)**: `ATOMIC` instruction type for flash-loan arb, multicall
  bundles, multi-leg on same CEX (e.g., Binance batch API)
- **Leg-and-hedge support (when atomic is impossible)**: for cross-venue arb where atomic is not supported, strategy
  specifies which leg is the "leader" (the side we want filled first) and which is the "hedge" (the side we chase
  immediately after leader fills). Which order types, slice sizes, and urgency are used on each leg are
  **execution-service decisions** driven by the execution_policy_ref — not strategy-level. Strategy just declares
  "leader = X, hedge = Y" and execution handles the rest.
- **Execution-risk monitoring**: mid-execution fail-safe checks (partial fill, venue outage, adverse move between leader
  fill and hedge completion)
- **Competition awareness**: for public arb (DEX, liquidation), priority-fee / gas-auction aware

### Atomic vs leg-and-hedge — when each applies

| Scenario                                       | Execution mode                              | Example                                                                             |
| ---------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------- |
| Flash-loan DEX arb on single chain             | ATOMIC (multicall + flash loan)             | Uniswap ↔ Balancer on Ethereum                                                     |
| Cross-CEX arb (fungible same instrument)       | Leg-and-hedge                               | Binance spot ↔ Bybit spot BTC-USDT — no venue supports simultaneous cross-CEX fill |
| Cross-DEX arb on same chain without flash loan | ATOMIC (multicall)                          | Uniswap ↔ Balancer ETH-USDC on Ethereum                                            |
| Cross-chain arb                                | Leg-and-hedge (bridge time kills atomicity) | Uniswap Ethereum ↔ Uniswap Arbitrum (same asset, different chain)                  |
| Sports cross-book via Unity                    | ATOMIC within Unity API                     | Back on Pinnacle-via-Unity + lay on Betfair-via-Unity, submitted near-atomic        |
| Sports cross-book direct (different accounts)  | Leg-and-hedge                               | Back on Pinnacle direct + lay on Betfair direct                                     |
| Cross-venue vol arb (Deribit ↔ OKX options)   | Leg-and-hedge                               | Two options venues, separate wallets                                                |

### Leader-hedge strategy choice

When leg-and-hedge is required, the strategy config declares:

```yaml
execution_ordering:
  mode: LEADER_HEDGE
  leader: venue_A # the leg that's executed first
  hedge: venue_B # the leg that chases once leader fills
  max_hedge_delay_ms: 500 # hard timeout; abort + unwind if exceeded
  abort_on_adverse_move_bps: 10 # unwind if reference price moves by this much between legs
```

**Strategy decides which side is leader based on:**

- Liquidity asymmetry — the more liquid venue is typically the hedge (easier to chase)
- Execution confidence — the less reliable venue is the leader (prove it fills first)
- Market impact — leader on the venue where our size creates less footprint
- Costs — leader on the venue with highest fee so hedge venue captures the lower-fee side

**Strategy does NOT decide:**

- Order type per leg (market vs passive vs iceberg vs hybrid) — that's execution_policy_ref
- Slice sizing across time — execution_policy_ref
- Dynamic algo selection based on microstructure conditions — execution_policy_ref

The strategy specifies **intent** (which leg is leader, max delay, abort conditions). The execution service picks the
**algo implementation** (what order types, slicing, etc. actually achieve that intent). This is exactly the "slow-path
vs fast-path routing split" principle — see
[../cross-cutting/venue-selection-split.md](../cross-cutting/venue-selection-split.md).

Later, once Group C (execution alpha) backtests validate which algo implementations produce the best execution against
each venue+condition combination, execution_policy_ref artifacts get updated. Strategy doesn't need to change;
execution_policy_ref version bump propagates new behavior (with consumer opt-in).

## Typical signal sources

| Signal                                  | Source                                                                                                           |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Cross-venue price dispersion            | Consolidated orderbook or aggregated feed                                                                        |
| Sports cross-book odds dispersion       | Unity (single-wallet access to 10 books) + aggregator feeds for remaining books                                  |
| Health factor monitor                   | On-chain read on lending protocol                                                                                |
| Oracle price vs market price            | Chainlink / Pyth oracle read + on-chain DEX price                                                                |
| DEX mempool pending swap                | Mempool watcher (for back-running)                                                                               |
| Funding rate dispersion                 | Aggregated per-venue funding-rate feeds                                                                          |
| Cross-venue vol dispersion              | Deribit vs OKX (or any two options venues) IVs on same (underlying, strike, expiry)                              |
| Hard no-arb violations within a surface | Butterfly convexity check, calendar carry-adjusted bound, put-call parity — all from single-venue fitted surface |

## Typical edge methods

- **Price-dispersion edge**: `best_bid_venue_A − best_ask_venue_B > total_costs`
- **Atomic cycle edge**: sequence of swaps/trades that net to positive after all legs complete atomically
- **Liquidation edge**: `liquidation_bonus − gas − slippage_on_collateral_sale > profit_threshold`
- **Funding-rate-dispersion edge**: `funding_rate_venue_A − funding_rate_venue_B > threshold` for same underlying
  (costly unless paired positions on both)

## Position structure

- **Price dispersion**: short-lived paired positions that net to (near-)zero directional exposure once both legs
  complete; ideally ATOMIC (simultaneous), otherwise sequenced with tight timing
- **Liquidation capture**: transient position (repay debt → seize collateral → sell collateral); net zero position
  post-completion, just cash profit

## Typical staking methods

| Method                                                              | When used                                                                                       |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Fixed notional per opportunity                                      | Default — each arb sized to available capital / leg                                             |
| Opportunity-sized (max capital per leg × number of concurrent opps) | For DEX / sports arb where multiple opportunities fire simultaneously                           |
| Liquidation-specific sizing                                         | Cap by capital available to repay debt                                                          |
| Flash-loan sized                                                    | Unlimited capital available via flash loan; sizing limited by profit magnitude + gas + slippage |

## Venue patterns

- **Cross-CEX**: Binance ↔ Bybit ↔ OKX ↔ Hyperliquid
- **Cross-DEX (single chain)**: Uniswap V3 ↔ Balancer ↔ Curve on Ethereum / Arbitrum / Optimism / etc.
- **Cross-chain arb (rare)**: Not really arb — latency too high; treated as opportunistic rebalance
- **Sports cross-book**: Unity (primary, single wallet) + direct Betfair/Smarkets for books not on Unity
- **Cross-category**: Polymarket (prediction) ↔ Betfair/Unity (sports) for correlated markets
- **Within-venue vol surface arb**: Deribit BTC/ETH options only (surface fitter + mispricing detector)
- **Liquidation**: Aave V3 on 6 EVM chains, Compound on Ethereum, Euler on Ethereum, Morpho on Ethereum, Kamino on
  Solana

## Expression options

- **Price dispersion**: spot-spot, perp-perp, spot-perp (synthetic), cross-chain fungible token arb
- **Sports**: 2-way (back on book A + lay on exchange B) or 3-way (back all outcomes to cover)
- **Vol surface**: butterfly, calendar, skew, risk reversal
- **Liquidation**: liquidation call → collateral sale (single sequence)

## Risk profile

- **Drawdowns**: low in percentage terms; most losses are from execution failures (partial fill, slippage, adverse move
  between legs)
- **Tail risks**:
  - Partial fill on one leg, adverse move before completing other (cross-venue arb, non-atomic)
  - Flash loan revert mid-cycle (DEX arb)
  - Gas-auction loss (liquidation — someone else wins the priority fee race)
  - Protocol exploit / bug (liquidation edge cases, reentrancy)
- **Sharpe**: typically high when opportunities are found (3+), but opportunity frequency is finite — net annualised
  returns depend on capital allocation efficiency
- **Kill switches**: abnormal dispersion (may indicate broken feed rather than arb), multiple consecutive losses
  (execution quality degraded), venue outage

## UI dashboard (shared)

- Opportunity detection rate (opportunities found / hour / day)
- Opportunity fill rate (opportunities executed / opportunities detected)
- P&L per opportunity — distribution + rolling average
- Execution slippage vs detected spread
- Gas cost / fee attribution
- Latency distribution (detection → first leg filled → all legs filled)
- Competitor / priority-fee auction wins/losses (for DEX + liquidation)
- Per-venue / per-book contribution

## Required subscriptions

Config references:

- Multiple **venue_capability_refs** (eligible venues + current fees/slippage estimates)
- Multiple **feature_group_refs** (consolidated orderbook feeds, oracle prices, health factor feeds)
- One **execution_policy_ref** (with MEV protection config for DeFi arb)
- Optional **bridge_capability_refs** (for cross-chain variants)

## Typical instance examples

```
Price dispersion — sports:
  ARBITRAGE_PRICE_DISPERSION@unity-epl-1x2-usd-prod              (cross-book via Unity)
  ARBITRAGE_PRICE_DISPERSION@unity-nba-moneyline-usd-prod
  ARBITRAGE_PRICE_DISPERSION@unity-la-liga-1x2-usd-prod
  ARBITRAGE_PRICE_DISPERSION@unity-champions-league-1x2-usd-prod

Price dispersion — DEX (on-chain atomic):
  ARBITRAGE_PRICE_DISPERSION@multi-dex-eth-usdc-ethereum-prod
  ARBITRAGE_PRICE_DISPERSION@multi-dex-eth-usdc-arbitrum-prod

Price dispersion — CEX:
  ARBITRAGE_PRICE_DISPERSION@binance-bybit-btc-usdt-prod
  ARBITRAGE_PRICE_DISPERSION@cross-cex-eth-usdt-prod

Cross-category:
  ARBITRAGE_PRICE_DISPERSION@polymarket-unity-elections-usdc-prod
  ARBITRAGE_PRICE_DISPERSION@polymarket-unity-sports-usdc-prod

Vol arb (within-surface no-arb violations):
  ARBITRAGE_PRICE_DISPERSION@deribit-btc-surface-noarb-usdt-prod    (butterfly / calendar / parity violations)
  ARBITRAGE_PRICE_DISPERSION@deribit-eth-surface-noarb-usdt-prod

Cross-venue vol arb:
  ARBITRAGE_PRICE_DISPERSION@deribit-okx-btc-vol-usdt-prod          (same option, different IVs across venues)
  ARBITRAGE_PRICE_DISPERSION@deribit-okx-eth-vol-usdt-prod

Funding-rate dispersion:
  ARBITRAGE_PRICE_DISPERSION@multi-cex-btc-funding-usdt-prod

Liquidation capture:
  LIQUIDATION_CAPTURE@aave-ethereum-prod
  LIQUIDATION_CAPTURE@aave-arbitrum-prod
  LIQUIDATION_CAPTURE@aave-multichain-prod
  LIQUIDATION_CAPTURE@compound-ethereum-prod
  LIQUIDATION_CAPTURE@euler-ethereum-prod
  LIQUIDATION_CAPTURE@morpho-ethereum-prod
  LIQUIDATION_CAPTURE@kamino-solana-prod
```

## Reaction to capital flow events

```python
def react_to_equity_change(self, new_equity_usd: Decimal) -> list[StrategyInstruction]:
    self.equity_usd = new_equity_usd
    # Arbitrage doesn't have a "current position" to resize — edges fire when detected
    # Just update max_capital_per_opportunity + max_concurrent_opportunities
    self.max_capital_per_opp = new_equity_usd * self.config.max_pct_per_opp
    return []  # no pending reconciliation needed
```

## Rebalancing triggers

- Opportunity detected → evaluate cost-adjusted edge → submit ATOMIC bundle or sequenced legs
- Post-fill: reconcile → return capital to idle state
- Equity change: update max-opp sizing; no in-flight positions to resize

## Migration from legacy docs

| Legacy                                               | Mapping                                                                                                                                                                                                                       | Notes                                                                                                                       |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `sports/arbitrage.md`                                | `ARBITRAGE_PRICE_DISPERSION`                                                                                                                                                                                                  | Unity-first routing; much simpler ops                                                                                       |
| `defi/cross-chain-sor-rebalancing.md`                | Split: SOR arb → this family; pure rebalancing → Transfer/Rebalance service                                                                                                                                                   | SOR execution primitive is cross-cutting; SOR _arbitrage_ is a strategy                                                     |
| `defi/cross-chain-yield-arb.md`                      | `ARBITRAGE_PRICE_DISPERSION` (if transient dispersion) or `YIELD_ROTATION_LENDING` (if sustained rate spread)                                                                                                                 | Alpha thesis decides                                                                                                        |
| Code: `strategy-service/.../lending_protocol_arb.py` | `ArbitragePriceDispersionEngine`                                                                                                                                                                                              |                                                                                                                             |
| Code: `strategy-service/.../liquidation_capture.py`  | `LiquidationCaptureEngine`                                                                                                                                                                                                    |                                                                                                                             |
| Code: `strategy-service/.../prediction_arb_btc.py`   | `ArbitragePriceDispersionEngine`                                                                                                                                                                                              | Cross-category (Polymarket + CEX)                                                                                           |
| Code: `strategy-service/.../cross_exchange_btc.py`   | `ArbitragePriceDispersionEngine`                                                                                                                                                                                              | Cross-CEX                                                                                                                   |
| Code: `strategy-service/.../vol_surface_btc.py`      | `ArbitragePriceDispersionEngine` if the alpha is hard no-arb violations (butterfly/calendar/parity) OR cross-venue IV dispersion; `VolTradingOptionsEngine` if the alpha is soft surface residuals expected to re-equilibrate | Test: is the edge mechanical (~risk-free conditional on execution) or statistical (profitable on average with spread risk)? |

## Cross-references

- Archetypes: [arbitrage-price-dispersion](../archetypes/arbitrage-price-dispersion.md),
  [liquidation-capture](../archetypes/liquidation-capture.md)
- ATOMIC multi-leg:
  [../../../04-architecture/strategy-execution-protocol.md](../../../04-architecture/strategy-execution-protocol.md)
- MEV protection: [../cross-cutting/mev-protection.md](../cross-cutting/mev-protection.md)
- Venue-account coordination (for cross-CEX simultaneous execution):
  [../cross-cutting/venue-account-coordination.md](../cross-cutting/venue-account-coordination.md)
- Unity for sports cross-book: [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
