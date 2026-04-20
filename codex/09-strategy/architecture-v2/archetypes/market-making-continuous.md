---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
    strategy-service: isolated
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 40
  min_sla_tier: premium
---

# Archetype: `MARKET_MAKING_CONTINUOUS`

> **Family:** [Market Making](../families/market-making.md) **Settlement model:** Continuous — quote lifecycle is
> long-running; inventory oscillates around a target; P&L is realized continuously. **Code module (target):**
> `strategy-service/engine/strategies/market_making_continuous_engine.py`

## What it does

Posts two-sided quotes around a theoretical fair price. Earns the bid-ask spread on fills. Covers CEX orderbook MM
(spot, perp, options) AND DeFi concentrated-liquidity LP on AMMs (Uniswap V3, V4, Orca, Aerodrome, etc.). Though the
venue mechanics differ (CLOB vs AMM), the alpha source is the same: providing liquidity and earning spread.

## Two sub-modes

This archetype covers two distinct venue mechanics with shared engine primitives:

### Sub-mode A: CLOB market making

```
Venues: Binance, OKX, Bybit, Hyperliquid, Deribit, Betfair-direct, Unity child books
  - Post bid + ask at theo ± half_spread
  - Inventory skew: widen the side you're long on; tighten the side you want filled
  - Delta-proxy repricer: auto-adjust quotes on underlying move (sub-ms)
  - Kill switch: rapid price move, spread blow-out, inventory breach
```

### Sub-mode B: AMM concentrated-liquidity LP ("active LP")

```
Venues: Uniswap V3/V4, Orca (Solana), Aerodrome V3 (Base), Raydium CLMM (Solana), Joe V2 (Avalanche)
  - Provide liquidity to a SPECIFIC PRICE RANGE (concentrated)
  - Earn swap fees only when price is WITHIN your range
  - When price leaves range: no fee earning, but also no more IL accrual (locked)
  - Subject to amplified impermanent loss (IL) when price moves within range
  - Manage IL via range adjustment, asymmetric ranges, or hedging on CEX
  - Requires active rebalancing — hence "active LP"
```

### Sub-mode C: AMM full-curve LP ("passive LP")

```
Venues: Uniswap V2, Curve StableSwap, Balancer weighted pools, Aerodrome V2 stable
  - Provide liquidity across ALL POSSIBLE PRICES (there is no range — liquidity spread over the full xy=k or stable curve)
  - Fees proportional to your share of pool TVL × pool volume
  - IL is smoother (no amplification vs concentrated) but also unbounded on one-directional moves (only bounded by total LP value collapsing to zero asymptotically)
  - Minimal active management — deposit and hold
  - Best for: highly correlated pairs (stablecoin-stablecoin via Curve, ETH-stETH on Balancer) where IL is structurally low
```

### Passive LP vs active LP — when each is appropriate

| Factor                     | Passive LP (V2, Curve, Balancer) | Active LP (V3, V4, Orca, Raydium)                     |
| -------------------------- | -------------------------------- | ----------------------------------------------------- |
| Management overhead        | None — deposit + hold            | High — range rebalancing, hedging                     |
| Capital efficiency         | Low (spread across all prices)   | High (concentrated where price actually trades)       |
| Fee earnings per $ capital | Lower                            | Much higher when in range                             |
| IL magnitude               | Smoother, lower amplification    | Amplified within range                                |
| Gas cost                   | One-time deposit                 | Per-rebalance (significant on Ethereum)               |
| Best for                   | Correlated pairs, stable pairs   | Volatile pairs where active management's fees beat IL |
| Typical Sharpe             | 0.3-1.0                          | 1.0-2.5 (with hedging)                                |

### IL in a nutshell

Impermanent loss is the opportunity cost of providing liquidity vs just holding. When price moves:

- If you had held the two assets, your value = holding value
- Because you provided liquidity, the AMM rebalances — you end up with more of the losing asset and less of the winning
  asset
- IL = |holding value − LP value|
- Called "impermanent" because if price returns to entry, IL disappears; but if you close the position mid-move, the
  loss is realized

Key realities:

- IL is **not guaranteed to be offset by fees**. You can absolutely lose money net-of-fees in directional markets
- Magnitude scales with price move magnitude + with concentration (V3 concentrated LP has amplified IL vs V2 full-range)
- Protocols with higher volume per TVL tend to have better fee / IL ratios

## Sub-mode B detail: LP dynamics by protocol

The user's question: _"when you lend to a pool, it's not guaranteed, right? if you take money out and it moves one way
in a straight line without collecting enough fees, don't you get fucked?"_ — Yes. This is **impermanent loss** (IL), and
the severity + mechanics differ per protocol.

### IL in a nutshell

Impermanent loss is the opportunity cost of providing liquidity vs just holding. When price moves:

- If you had held the two assets, your value = holding value
- Because you provided liquidity, the AMM rebalances — you end up with more of the losing asset and less of the winning
  asset
- IL = |holding value − LP value|
- Called "impermanent" because if price returns to entry, IL disappears; but if you close the position mid-move, the
  loss is realized

Key realities:

- IL is **not guaranteed to be offset by fees**. You can absolutely lose money net-of-fees in directional markets
- Magnitude scales with price move magnitude + with concentration (V3 concentrated LP has amplified IL vs V2 full-range)
- Protocols with higher volume per TVL tend to have better fee / IL ratios

### Per-protocol dynamics

| Protocol               | Version                     | Liquidity model                                     | IL behavior                                                                                | Fee tiers                 | Active management needed                                                                    |
| ---------------------- | --------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------- | ------------------------------------------------------------------------------------------- |
| **Uniswap V2**         | V2                          | Full-range (xy=k)                                   | Smooth IL; symmetric around entry; capped by total LP value                                | 0.3% (single tier)        | No active management; passive LP                                                            |
| **Uniswap V3**         | V3                          | Concentrated in a price range                       | Amplified IL within range (leveraged-like); zero IL once out of range (but also zero fees) | 0.01% / 0.05% / 0.3% / 1% | **Heavy active management** — range rebalancing as price moves                              |
| **Uniswap V4**         | V4                          | Same as V3 + hooks (custom logic)                   | Same as V3 + hook-specific behavior                                                        | Flexible via hooks        | Heavy (same as V3) + hook awareness                                                         |
| **Orca** (Solana)      | Whirlpools                  | V3-style concentrated liquidity                     | Same as Uniswap V3                                                                         | 0.01% / 0.05% / 0.3% / 1% | Heavy active management                                                                     |
| **Raydium** (Solana)   | CLMM                        | V3-style concentrated                               | Same as Uniswap V3                                                                         | Tiered                    | Heavy                                                                                       |
| **Aerodrome** (Base)   | V2 stable + V3 concentrated | V2 stable (for stablecoin pairs) or V3 concentrated | V2 stable: near-zero IL for pegged pairs; V3: same as Uniswap V3                           | Tiered                    | V2 stable: minimal; V3: heavy                                                               |
| **Joe V2** (Avalanche) | Liquidity Book (bin-based)  | Discrete bins vs continuous range                   | Similar to V3 but with bin granularity                                                     | Dynamic                   | Heavy (bin rebalancing)                                                                     |
| **Balancer**           | V2/V3                       | Weighted pools (e.g., 80/20)                        | Asymmetric IL based on weights                                                             | Pool-specific             | Passive or active; weighted pools have structurally lower IL than 50/50 for one-sided moves |
| **Curve**              | StableSwap                  | Specialized for pegged pairs                        | Near-zero IL for pegged pairs; significant IL if pairs de-peg                              | 0.04% typical             | Passive (pool creator tunes amplification)                                                  |

### IL mitigation strategies (per protocol)

**Uniswap V3 / Orca / Raydium / Aerodrome V3 (concentrated liquidity):**

1. **Range width**: wider ranges = lower IL but lower fees; narrower = more fees but more IL. Optimal width depends on
   vol regime.
2. **Active rebalancing**: periodically close + re-open range around current price (realizes IL; re-enters with fresh
   range)
3. **Asymmetric ranges**: if we have a view, skew the range (e.g., narrow on the side we expect resistance)
4. **Hedging**: short perp on CEX to hedge the directional exposure from LP rebalancing (transforms LP from
   directional+fees into fees-only)

**Uniswap V2 / Balancer:**

1. **Weighted pools** (Balancer): 80/20 pools have ~4x less IL than 50/50 for one-sided moves
2. **Pair selection**: correlated pairs (ETH-stETH, ETH-rETH, USDC-USDT) have structurally low IL
3. **Passive hold**: accept IL as cost of steady fees on volatile pairs

**Curve (StableSwap):**

1. Mostly passive; IL exists only during de-peg events
2. Monitor peg; exit if de-peg > threshold

### When LP is a good strategy

- High volume relative to TVL (fee generation > IL over typical vol window)
- Pairs with stable correlation / low vol (stablecoin-stablecoin, ETH-stETH)
- Hedged LP (short perp to offset directional exposure)
- Passive structural allocations (Curve stables, Balancer stables)

### When LP loses money

- One-directional price moves (classic "picked off" scenario — strategy out of range, no fee collection)
- Low volume relative to TVL (fees don't compensate IL)
- Extreme vol spikes (IL outpaces fees)
- De-peg events on supposedly-correlated pairs (Curve stablecoin depegs)

## Token / position flow (LP sub-mode, Uniswap V3 example)

```
1. RANGE SELECTION: config or strategy computes target range (e.g., ±2% around mid, or based on ATR)

2. SPLIT CAPITAL: convert share_class capital into (token0, token1) ratio required by range
   - If at current price: 50/50 between tokens
   - If range skewed: asymmetric split

3. DEPOSIT: PROVIDE_LIQUIDITY on Uniswap V3 with range bounds + deposit amounts
   (ATOMIC multicall: approve + mint position)

4. HOLD: earn fees on swaps within range
   Monitor:
   - Price vs range bounds (if out of range, no fees earning)
   - IL accruing (vs holding benchmark)
   - Fees collected
   - Hedge leg (if CEX short perp for hedge)

5. REBALANCE triggers:
   - Price near range boundary → reposition range
   - IL > threshold without fee compensation → exit
   - Volatility regime shift → widen/narrow range
   - Equity change → rescale

6. EXIT: close position (withdraw liquidity + collect unclaimed fees)
```

## Supported venues / instruments (both sub-modes)

**CLOB:**

- Binance (spot, perp, options futures)
- OKX (spot, perp)
- Bybit (spot, perp)
- Hyperliquid (spot, perp)
- Deribit (perp, options)
- Betfair direct, Unity child books, Smarkets, Matchbook (sports — see EVENT_SETTLED variant)

**AMM LP:**

- Uniswap V2 (Ethereum) — passive
- Uniswap V3 (Ethereum, Arbitrum, Optimism, Polygon, Base, Avalanche) — active
- Uniswap V4 (Ethereum + L2s as deployed) — active + hooks
- Orca Whirlpools (Solana) — active
- Raydium CLMM (Solana) — active
- Aerodrome (Base) — V2 stable + V3 concentrated
- Joe V2 (Avalanche) — bin-based
- Balancer (Ethereum, Arbitrum) — weighted pools
- Curve (Ethereum, Arbitrum, Optimism, Polygon) — stable pairs

## Expression options

- **CLOB spot quotes**: standard two-sided
- **CLOB perp quotes**: with funding exposure; may hedge via spot
- **CLOB options quotes**: vega/gamma-bounded (see VOL_TRADING_OPTIONS if alpha is vol)
- **AMM concentrated LP**: range + tick spacing
- **AMM passive LP**: full range (V2-style)

## Hold policies

- CONTINUOUS (both sub-modes — quote lifecycle is long-running)

## Config schema (CLOB example)

```yaml
venue: BINANCE
instrument: "BINANCE:SPOT:BTC-USDT"
theo_source: consensus_mid
half_spread_bps: 3
min_spread_edge_bps: 1
vol_spread_multiplier: 1.5 # widen when vol high
max_inventory_usd: 100000
max_inventory_pct_equity: 0.20
skew_per_unit_bps: 0.5
refresh_interval_seconds: 2
kill_switch_movement_pct: 5.0
funding_bias_weight: 0.3 # perp specific
execution_policy_ref: cefi-mm-v3
share_class: USDT
```

## Config schema (LP example, Uniswap V3)

```yaml
venue: UNISWAP_V3_ETHEREUM
pool_instrument: "UNISWAP_V3:ETH-USDC:500" # 0.05% fee tier
lp_mode: concentrated
range_selection: atr_based # or fixed_percent or volatility_adaptive
range_width_atr_multiple: 2.0
rebalance_trigger_distance_pct: 0.8 # rebalance at 80% of range width from center
il_exit_threshold_pct: 1.0 # close if IL > 1% of position
hedge_on_cex: true # short ETH perp on Hyperliquid for directional hedge
hedge_venue: HYPERLIQUID
hedge_instrument: "HYPERLIQUID:PERPETUAL:ETH-USD"
share_class: USDC
execution_policy_ref: defi-lp-v2
```

## Execution semantics

- **CLOB**: QUOTE action type; execution-service maintains quote lifecycle via delta-proxy repricer
- **LP**: ATOMIC multicalls for deposit/withdraw; TRADE for hedge leg on CEX

## P&L attribution

**CLOB:**

- Spread captured per fill
- Funding P&L (perp MM)
- Inventory P&L (directional P&L from carrying inventory)
- Fees
- Execution alpha (vs benchmark)

**LP:**

- Fees collected per swap event
- IL (impermanent loss) — realized on close or at each rebalance
- Hedge P&L (if hedging on CEX)
- Gas cost per rebalance (significant on Ethereum mainnet)

## Risk profile

**CLOB:**

- Drawdowns: modest + frequent (inventory on wrong side during adverse moves)
- Typical Sharpe: 2-5 in normal regimes
- Kill switches: price move > 5× ATR, inventory limit, venue outage

**LP:**

- Drawdowns: IL-driven; can be sharp during trending markets
- Typical Sharpe: 1.0-2.5 for concentrated LP with hedge; lower for passive
- Kill switches: IL > threshold, price out of range for > N hours, de-peg (stable pairs)

## Example instances

```
CLOB MM:
  MARKET_MAKING_CONTINUOUS@binance-btc-usdt-mm-prod
  MARKET_MAKING_CONTINUOUS@hyperliquid-eth-usdt-perp-mm-prod
  MARKET_MAKING_CONTINUOUS@deribit-btc-options-mm-usdt-prod

AMM LP (concentrated):
  MARKET_MAKING_CONTINUOUS@uniswap-v3-eth-usdc-500-ethereum-prod
  MARKET_MAKING_CONTINUOUS@uniswap-v3-wbtc-eth-3000-arbitrum-prod
  MARKET_MAKING_CONTINUOUS@orca-sol-usdc-active-lp-prod
  MARKET_MAKING_CONTINUOUS@aerodrome-eth-usdc-v3-base-prod

AMM LP (passive / stable):
  MARKET_MAKING_CONTINUOUS@curve-3pool-stables-ethereum-prod
  MARKET_MAKING_CONTINUOUS@balancer-80wbtc-20eth-arbitrum-prod

Hedged LP:
  MARKET_MAKING_CONTINUOUS@uniswap-v3-eth-usdc-hedged-hyperliquid-prod
  (LP on Uniswap + short ETH perp on Hyperliquid to hedge delta)
```

## Migration from legacy

| Legacy                        | Notes                                          |
| ----------------------------- | ---------------------------------------------- |
| `cefi/market-making.md`       | CLOB sub-mode                                  |
| `defi/market-making-lp.md`    | AMM sub-mode                                   |
| `defi/sol-concentrated-lp.md` | AMM sub-mode (Solana)                          |
| Code: `cefi_market_making.py` | → `MarketMakingContinuousEngine` (CLOB path)   |
| Code: `active_defi_mm.py`     | → `MarketMakingContinuousEngine` (AMM LP path) |

## Not in this archetype

- **Event-settled market making** (sports exchanges, prediction markets) — `MARKET_MAKING_EVENT_SETTLED`
- **Directional quoting with strong skew on signal** (if inventory management serves alpha, not the other way) —
  `ML_DIRECTIONAL_CONTINUOUS` with quote expression
- **Spread arbitrage / cross-venue SOR** — `ARBITRAGE_PRICE_DISPERSION`
- **Pair-z-score trades around a reference spread** — `STAT_ARB_PAIRS_FIXED`
- **Passive LP without active range management** (set-and-forget Uniswap V2) — `YIELD_STAKING_SIMPLE` (closer to passive
  yield than MM)

## See also

- Family: [market-making.md](../families/market-making.md)
- Event-settled variant: [market-making-event-settled.md](market-making-event-settled.md)
- Capital efficiency (e.g., running MM alongside directional on same Binance account):
  [../../../04-architecture/capital-efficiency-patterns.md](../../../04-architecture/capital-efficiency-patterns.md)
