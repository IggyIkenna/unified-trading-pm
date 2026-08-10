---
doc_type: codex-ssot
title: "Family: Arbitrage / Structural Edge"
summary:
  The Arbitrage / Structural Edge strategy family — 7 archetypes (price-dispersion, liquidation-capture, 4 MEV variants,
  cross-domain-event) capturing near-risk-free spread or protocol-paid structural bonus; edge is spread/bonus > cost,
  executed ATOMIC or leg-and-hedge, NOT directional.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, arbitrage, mev, liquidation, defi, execution, funding]
related:
  [
    /codex/09-strategy/architecture-v2/families/carry-and-yield.md,
    /codex/09-strategy/architecture-v2/families/stat-arb-pairs.md,
    market-making.md,
    ../archetypes/arbitrage-price-dispersion.md,
    ../cross-cutting/mev-protection.md,
  ]
created: 2026-04-17
authoritative_for: [Arbitrage / Structural Edge strategy family spec (alpha thesis + 7 archetypes)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-cross-domain-event.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-backrun.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-jit-liquidity.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-liquidation-bundle.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-sandwich.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/liquidation-capture.md,
  ]
owner:
last_reviewed:
code_refs:
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
> **Archetype count:** 7 — distinguished by alpha mechanism and execution model. (2 original + 5 added: 4 MEV variants +
> `ARBITRAGE_CROSS_DOMAIN_EVENT` per taxonomy V-1, uac@0196842.)

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

## 7 Archetypes

| Archetype                                                                               | Edge mechanism                                                                                                 | Execution model                  | When to use                                                                                                    |
| --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| [`ARBITRAGE_PRICE_DISPERSION`](../archetypes/arbitrage-price-dispersion.md)             | Price spread between venues on same/equivalent instrument                                                      | Atomic or leg-and-hedge          | Cross-CEX, cross-DEX, sports cross-book, cross-category (Polymarket-Betfair), vol arb, funding-rate dispersion |
| [`LIQUIDATION_CAPTURE`](../archetypes/liquidation-capture.md)                           | Protocol-paid bonus for repaying an underwater position + seizing collateral at discount                       | Leg-and-hedge (capital required) | Aave / Compound / Euler / Morpho / Kamino liquidation bots                                                     |
| [`ARBITRAGE_MEV_BACKRUN`](../archetypes/arbitrage-mev-backrun.md)                       | Large swap left DEX pools momentarily out-of-sync; arb in next-tx slot                                         | ATOMIC single tx                 | Post-swap DEX price recovery; Ethereum / L2                                                                    |
| [`ARBITRAGE_MEV_SANDWICH`](../archetypes/arbitrage-mev-sandwich.md)                     | Bracket a victim's large swap with front-run + back-run; capture adverse price movement                        | ATOMIC 3-tx bundle               | **Theoretical only — no live engine.** Regulatory risk; retained for completeness.                             |
| [`ARBITRAGE_MEV_JIT_LIQUIDITY`](../archetypes/arbitrage-mev-jit-liquidity.md)           | Mint concentrated-LP position before imminent large swap; collect fees; burn next block                        | ATOMIC 2-block                   | Uniswap V3 / Algebra concentrated-liquidity pools; low-capital, near-zero inventory                            |
| [`ARBITRAGE_MEV_LIQUIDATION_BUNDLE`](../archetypes/arbitrage-mev-liquidation-bundle.md) | Flash-loan funded liquidation in a single atomic bundle; zero capital required                                 | ATOMIC single tx                 | Aave / Compound / Euler on 6 EVM chains + Kamino on Solana; extends LIQUIDATION_CAPTURE                        |
| [`ARBITRAGE_CROSS_DOMAIN_EVENT`](../archetypes/arbitrage-cross-domain-event.md)         | Same real-world event priced in ≥2 venue domains (sports book / prediction CLOB / CME binary); arb across them | Leg-and-hedge                    | Sports book ↔ Polymarket ↔ Kalshi; CME binary options; added 2026-05-18 per taxonomy V-1                       |

## Shared primitives (all archetypes)

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

| Scenario                                       | Execution mode                              | Example                                                                            |
| ---------------------------------------------- | ------------------------------------------- | ---------------------------------------------------------------------------------- |
| Flash-loan DEX arb on single chain             | ATOMIC (multicall + flash loan)             | Uniswap ↔ Balancer on Ethereum                                                     |
| Cross-CEX arb (fungible same instrument)       | Leg-and-hedge                               | Binance spot ↔ Bybit spot BTC-USDT — no venue supports simultaneous cross-CEX fill |
| Cross-DEX arb on same chain without flash loan | ATOMIC (multicall)                          | Uniswap ↔ Balancer ETH-USDC on Ethereum                                            |
| Cross-chain arb                                | Leg-and-hedge (bridge time kills atomicity) | Uniswap Ethereum ↔ Uniswap Arbitrum (same asset, different chain)                  |
| Sports cross-book via Unity                    | ATOMIC within Unity API                     | Back on Smarkets-via-Unity + lay on Betfair-via-Unity, submitted near-atomic       |
| Sports cross-book direct (different accounts)  | Leg-and-hedge                               | Back on Smarkets direct + lay on Betfair direct                                    |
| Cross-venue vol arb (Deribit ↔ OKX options)    | Leg-and-hedge                               | Two options venues, separate wallets                                               |

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
- **Sharpe (per opportunity)**: 3+. Opportunity frequency is finite; net annualised returns depend on capital-
  allocation efficiency and how often the scanner fires.
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

## Active catalog slots (2026-05-20, from `catalog.py _build_arbitrage_price_dispersion`)

```
Lending protocol arb (same chain, different protocols):
  ARBITRAGE_PRICE_DISPERSION@aave-compound-ethereum-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-morpho-ethereum-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-compound-arbitrum-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-morpho-arbitrum-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-compound-optimism-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-morpho-optimism-usdc-1h-usdc-v2-prod

Cross-chain yield arb (same protocol, different chains):
  ARBITRAGE_PRICE_DISPERSION@aave-ethereum-arbitrum-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-ethereum-optimism-usdc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@aave-arbitrum-base-usdc-1h-usdc-v2-prod

CEX-CEX spot/perp spread arb:
  ARBITRAGE_PRICE_DISPERSION@binance-okx-btc-1m-usdt-v2-prod
  ARBITRAGE_PRICE_DISPERSION@binance-bybit-eth-1m-usdt-v2-prod
  ARBITRAGE_PRICE_DISPERSION@okx-hyperliquid-sol-1m-usdt-v2-prod

Sports cross-book arb:
  ARBITRAGE_PRICE_DISPERSION@unity-betfair-matchbook-epl-gbp-v2-prod
  ARBITRAGE_PRICE_DISPERSION@unity-betfair-matchbook-nba-gbp-v2-prod

Prediction market arb:
  ARBITRAGE_PRICE_DISPERSION@polymarket-betfair-sports-gbp-v2-prod

CME-Deribit dated futures arb:
  ARBITRAGE_PRICE_DISPERSION@cme-deribit-mbt-btc-1h-usdc-v2-prod
  ARBITRAGE_PRICE_DISPERSION@cme-deribit-met-eth-1h-usdc-v2-prod

Funding-rate dispersion (bridge slots, not in TARGET_UNIVERSE catalog):
  ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-btc-usdt-v5-prod
  ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-eth-usdt-v5-prod

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
  [liquidation-capture](../archetypes/liquidation-capture.md),
  [arbitrage-mev-backrun](../archetypes/arbitrage-mev-backrun.md),
  [arbitrage-mev-sandwich](../archetypes/arbitrage-mev-sandwich.md),
  [arbitrage-mev-jit-liquidity](../archetypes/arbitrage-mev-jit-liquidity.md),
  [arbitrage-mev-liquidation-bundle](../archetypes/arbitrage-mev-liquidation-bundle.md),
  [arbitrage-cross-domain-event](../archetypes/arbitrage-cross-domain-event.md)
- ATOMIC multi-leg:
  [../../../04-architecture/strategy-execution-protocol.md](../../../04-architecture/strategy-execution-protocol.md)
- MEV protection: [../cross-cutting/mev-protection.md](../cross-cutting/mev-protection.md)
- Venue-account coordination (for cross-CEX simultaneous execution):
  [../cross-cutting/venue-account-coordination.md](../cross-cutting/venue-account-coordination.md)
- Unity for sports cross-book: [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
- **Subdir → family enforcement**: `strategy-service/strategy_service/engine/strategies/v2/mev/` archetypes map to
  `ARBITRAGE_STRUCTURAL`; enforced by `tests/unit/engine/strategies/v2/test_subdir_family_alignment.py`
  (strategy-service@f01d12d).
