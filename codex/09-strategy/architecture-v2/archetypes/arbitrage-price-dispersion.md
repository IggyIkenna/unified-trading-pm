---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `ARBITRAGE_PRICE_DISPERSION`

> **Family:** [Arbitrage / Structural Edge](../families/arbitrage-structural.md) **Settlement model:** ATOMIC (when
> venue supports) or LEADER_HEDGE (when atomic isn't possible). **Code module (target):**
> `strategy-service/engine/strategies/arbitrage_price_dispersion_engine.py`

## What it does

Detects price dispersion between venues on the same (or equivalent) instrument and executes a paired position that locks
in the spread net of costs. Covers:

- Cross-CEX spot / perp arb
- Cross-DEX arb (same chain, flash-loan optionally)
- Sports cross-book arb (via Unity prime broker — single wallet)
- Cross-category arb (Polymarket ↔ Betfair/Unity for correlated markets)
- Cross-venue vol arb (same option quoted at different IVs on Deribit vs OKX options)
- Within-venue no-arb violations (butterfly / calendar / put-call parity)
- Funding-rate dispersion arb (net position sized to capture funding differential)

## Token / position flow

```
1. DISPERSION SCANNER (continuous):
   - Per eligible (instrument, venue) pair: read prices / odds / IVs
   - Compute gross spread: best_bid_venue_A - best_ask_venue_B (or equivalent)
   - Deduct all costs: fees, slippage, gas, bridge, commission, execution spread
   - If net_spread > min_edge_threshold: opportunity found

2. OPPORTUNITY VALIDATION:
   - Verify liquidity on both legs: can we execute our target size?
   - Verify venue connectivity healthy
   - Verify we have pre-funded capital on both venues (or flash-loan available)
   - Pre-flight check against venue-account health

3. EXECUTION DISPATCH:
   Select mode based on venue support:
   - ATOMIC: if both legs on same chain, use multicall / batch API / flash-loan
   - LEADER_HEDGE: if cross-venue non-atomic, declare leader leg + hedge leg +
                   max_hedge_delay + abort_on_adverse_move

4. SUBMIT + RECONCILE:
   - ATOMIC: entire bundle succeeds or reverts; P&L realized atomically
   - LEADER_HEDGE: execution submits leader; on fill, submits hedge immediately;
                   monitors reference price move; aborts + unwinds if thresholds breached

5. POST-EXIT STATE: capital returns to idle (typically net-zero exposure + cash profit)
```

## Supported scenarios + execution modes

| Scenario                                                     | Execution mode                          | Notes                                                                  |
| ------------------------------------------------------------ | --------------------------------------- | ---------------------------------------------------------------------- |
| Flash-loan DEX arb (Uniswap ↔ Balancer) single chain        | ATOMIC (flash-loan + multicall)         | Risk-free if profitable after gas                                      |
| Cross-DEX arb same chain without flash loan                  | ATOMIC (multicall)                      | Profitable if price dispersion > gas + slippage                        |
| Cross-CEX arb (Binance ↔ Bybit on BTC-USDT)                 | LEADER_HEDGE                            | Different API endpoints; legs can't be atomic                          |
| Sports cross-book via Unity                                  | ATOMIC within Unity API                 | Unity single-wallet routes bets to chosen child books; near-atomic     |
| Sports cross-book direct (Betfair direct ↔ Smarkets direct) | LEADER_HEDGE                            | Different accounts; leg-then-hedge                                     |
| Cross-venue vol arb (Deribit ↔ OKX options)                 | LEADER_HEDGE                            | Two options venues, separate wallets                                   |
| Within-surface no-arb violation                              | ATOMIC (multi-leg bundle on same venue) | E.g., butterfly: buy wings, sell body — single Deribit multi-leg order |
| Funding-rate dispersion arb                                  | LEADER_HEDGE (usually)                  | Enter paired position; hold until funding normalizes                   |

## Config schema

```yaml
opportunity_type: CROSS_BOOK_SPORTS # or CROSS_DEX_SPOT, CROSS_CEX_SPOT, CROSS_VENUE_VOL, SURFACE_NOARB, FUNDING_DISPERSION
eligible_venues:
  - UNITY # with child_books preference list
  - BETFAIR_DIRECT
  - SMARKETS_DIRECT
eligible_markets:
  - league: EPL
    markets: ["1X2", "OVER_UNDER_2_5"]
min_edge_bps: 50 # 50 bps minimum after all costs
max_capital_per_opp_pct: 0.05 # 5% of equity per opp
max_concurrent_opps: 10
execution_ordering:
  mode: ATOMIC # or LEADER_HEDGE
  leader: UNITY # for LEADER_HEDGE
  hedge: BETFAIR_DIRECT
  max_hedge_delay_ms: 500
  abort_on_adverse_move_bps: 10
execution_policy_ref: arb-fast-v2
share_class: USD
```

## Execution semantics

- `ATOMIC` instruction type for bundled legs
- `TRADE` instructions sequenced for LEADER_HEDGE
- Execution-service enforces leader-hedge timing via execution_policy_ref
- Mid-execution abort if conditions breach (unwind whichever leg filled)

## P&L attribution

- **Arb edge captured**: (total_received - total_paid) on successful opp
- **Execution slippage**: difference between detected spread and realized spread
- **Gas / fees / commission**: per opp
- **Adverse-move losses** (leader-hedge aborts): unwind cost when hedge failed to fill in time

## Risk profile

- Drawdowns: rare but sharp when execution fails mid-sequence (partial fill, adverse move, gas auction loss)
- Typical Sharpe: 3+ when opportunities are found; limited by opportunity frequency
- Kill switches: abnormal dispersion (likely broken feed), consecutive execution failures, venue outage

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    self.max_capital_per_opp = new_equity * self.config.max_capital_per_opp_pct
    return []   # no in-flight positions to resize
```

## Example instances

```
Sports cross-book via Unity:
  ARBITRAGE_PRICE_DISPERSION@unity-epl-1x2-usd-prod
  ARBITRAGE_PRICE_DISPERSION@unity-nba-moneyline-usd-prod
  ARBITRAGE_PRICE_DISPERSION@unity-champions-league-1x2-usd-prod

DEX (single chain, flash-loan optional):
  ARBITRAGE_PRICE_DISPERSION@multi-dex-eth-usdc-ethereum-prod
  ARBITRAGE_PRICE_DISPERSION@multi-dex-eth-usdc-arbitrum-prod

Cross-CEX:
  ARBITRAGE_PRICE_DISPERSION@binance-bybit-btc-usdt-prod
  ARBITRAGE_PRICE_DISPERSION@cross-cex-eth-usdt-prod

Cross-venue vol:
  ARBITRAGE_PRICE_DISPERSION@deribit-okx-btc-vol-usdt-prod
  ARBITRAGE_PRICE_DISPERSION@deribit-okx-eth-vol-usdt-prod

Within-surface no-arb:
  ARBITRAGE_PRICE_DISPERSION@deribit-btc-surface-noarb-usdt-prod
  ARBITRAGE_PRICE_DISPERSION@deribit-eth-surface-noarb-usdt-prod

Cross-category:
  ARBITRAGE_PRICE_DISPERSION@polymarket-unity-elections-usdc-prod
  ARBITRAGE_PRICE_DISPERSION@polymarket-unity-sports-usdc-prod

Funding-rate dispersion:
  ARBITRAGE_PRICE_DISPERSION@multi-cex-btc-funding-usdt-prod
```

## Migration from legacy

| Legacy                                                                                                                   | Notes                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `sports/arbitrage.md`                                                                                                    | Primary migration target                                                              |
| `defi/cross-chain-sor-rebalancing.md`                                                                                    | Split: transient dispersion arb → here; pure rebalancing → Transfer/Rebalance service |
| `defi/cross-chain-yield-arb.md`                                                                                          | If transient dispersion → here; if sustained rate spread → YIELD_ROTATION_LENDING     |
| Code: `cross_exchange_btc.py`, `lending_protocol_arb.py`, `prediction_arb_btc.py`, `vol_surface_btc.py` (if hard no-arb) | → `ArbitragePriceDispersionEngine`                                                    |

## Not in this archetype

- **Funding-rate arbitrage between perp venues** (bidirectional funding capture) — `CARRY_BASIS_PERP` (cross-venue mode)
- **Liquidation snipe during cascades** — `LIQUIDATION_CAPTURE`
- **Cross-strategy capital rebalancing** (move capital to a better strategy) — portfolio-allocator service, not a
  strategy
- **ML-predicted momentum divergence** (model says A will outperform B) — `ML_DIRECTIONAL_CONTINUOUS` on one leg, not
  structural arb
- **Cointegrated pair trades** (z-score reversion) — `STAT_ARB_PAIRS_FIXED`

## See also

- Family: [arbitrage-structural.md](../families/arbitrage-structural.md)
- Liquidation variant: [liquidation-capture.md](liquidation-capture.md)
- Leader-hedge execution: [../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md)
- Unity integration (primary sports venue):
  [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
- MEV protection for DeFi arb: [../cross-cutting/mev-protection.md](../cross-cutting/mev-protection.md)
