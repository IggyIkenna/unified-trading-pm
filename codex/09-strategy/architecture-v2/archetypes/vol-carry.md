---
doc_type: codex-ssot
title: "Archetype: `VOL_CARRY`"
summary:
  "Archetype spec for `VOL_CARRY` — harvests the structural IV-over-RV premium by selling 7-21 DTE
  straddles/strangles/iron-condors for theta, delta-hedged; core carry_pnl=(IV²−RV²)×vega/2; Deribit/OKX/CBOE."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, carry, theta, delta-hedge]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-arb-rv-iv.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-term-structure-arb.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-trading-options.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-pin-risk.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_CARRY archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-gamma-scalping.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-pin-risk.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-arb-rv-iv.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-cross-asset-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-leaps-convexity.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-ml-lean.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_CARRY
family: VOL_TRADING
venue_universe: [DERIBIT, OKX_OPTIONS, CBOE]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `VOL_CARRY`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Continuous — short options positions
> managed with delta hedging; positions rolled at expiry. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_carry_engine.py`

## What it does

Harvests the persistent IV-over-RV premium at short tenors by selling options and collecting theta decay. The structural
alpha is that implied vol at 1-4 week tenors consistently prices in more realised-vol premium than materialises on
average. Delta-hedge the short-options book via the underlying perp/future to isolate the vega/theta P&L from
directional exposure.

**Core P&L equation (annualised, USDT):**

```
carry_pnl = (IV² − RV²) × vega_notional / 2   (variance-based vol carry)
theta_pnl = theta_daily × hold_days
delta_hedge_cost ≈ gamma × sigma² × dt / 2     (cost to hedge realised moves)
net ≈ carry_pnl + theta_pnl − delta_hedge_cost − fees
```

## Token / position flow

```
1. SURFACE FITTER: fit SVI / SSVI surface to current option chain

2. VOL CARRY SCANNER:
   - Compute rolling realised vol (RV_n: 5d, 10d, 20d)
   - Compute IV at target tenor (e.g. 14 DTE ATM IV)
   - Carry premium: (IV − RV_14d) in vol points
   - Entry condition: carry_premium > min_carry_threshold_vp AND NOT in high-vol regime

3. POSITION SIZING:
   - Target vega_notional_usd at entry
   - Prefer straddle or strangle depending on skew richness
     - Near-zero skew: straddle (sell ATM call + put)
     - Rich put skew:  strangle (sell OTM put + OTM call, collect put premium)
   - Max delta before hedge: configured delta_free_band_pct

4. ENTRY: ATOMIC multi-leg TRADE on options venue

5. HOLD + REHEDGE:
   - Delta-proxy rehedge: when |net_delta| > delta_hedge_band × vega_notional, emit hedge TRADE
   - Greeks monitor: theta (positive), vega (short, negative on regime), gamma (short, negative)
   - Monitor realised vol: if RV accelerates past iv_stop_rv_multiple × IV, exit

6. EXIT:
   - Theta target reached: theta_pnl_cumulative > take_profit_theta_pct × initial_premium
   - Stop loss: vega_pnl < -stop_loss_vega_pct × initial_premium (vol spike blowout)
   - Vol regime change: 5d RV > iv_stop_rv_multiple × entry_IV
   - Time: roll at roll_before_expiry_dte DTE to avoid pin / gamma risk
   - Expiry: ATOMIC roll (close expiring, open next-expiry chain)
```

## Supported venues / instruments

- **Crypto options**: Deribit (BTC, ETH — primary; deepest options liquidity), OKX options (alternate)
- **TradFi options**: CBOE via IBKR (SPX, SPY weeklies), CME options-on-futures
- **Preferred tenors**: 7-21 DTE at entry (IV carry premium strongest in 1-3 week range)

## Expression options

- **Short straddle**: short ATM call + short ATM put (symmetric, max theta at ATM)
- **Short strangle**: short OTM put + short OTM call (cheaper, wider wings, directional safety zone)
- **Short iron condor**: strangle + long wings (capped loss; reduces required margin)
- **Short put spread**: for when put-skew richness makes pure put premium the carry source

## Hold policies

- CONTINUOUS (delta-hedge loop running)
- Roll at `roll_before_expiry_dte` (default 3 DTE) to avoid expiry gamma and pin risk

## Config schema

```yaml
underlying: BTC
venue: DERIBIT
surface_model_ref: svi-btc-v3
target_dte_entry: 14 # target DTE at entry (7-21 range)
roll_before_expiry_dte: 3 # roll to next expiry at ≤3 DTE
min_carry_threshold_vp: 3.0 # minimum (IV − RV_14d) in vol points to enter
expression: straddle # straddle | strangle | iron_condor | short_put_spread
strangle_delta_target: 0.20 # for strangle: target option delta per wing (20d)
max_vega_notional_usd: 50_000
delta_hedge_band_pct: 0.05 # rehedge when |portfolio_delta| > 5% of vega_notional
hedge_venue: DERIBIT
hedge_instrument: "DERIBIT:PERPETUAL:BTC-PERPETUAL"
take_profit_theta_pct: 0.50 # realize at 50% of initial premium collected
stop_loss_vega_pct: 0.75 # exit if vega loss > 75% of premium collected
iv_stop_rv_multiple: 1.5 # exit if 5d RV > 1.5× entry IV (vol regime change)
high_vol_regime_iv_threshold: 0.80 # skip entry if ATM IV > 80% (BTC; tune per asset)
share_class: USDT
execution_policy_ref: options-taker-v1 # taker algo — priority on fill to avoid leg risk

# Leverage + net-delta controls:
target_leverage: 1.0 # [1, 10]; short options notional vs equity
target_net_delta: 0.0 # net directional delta (0 = delta-hedged)
max_underlying_move_pct: 3.0 # vol-cap clamp: pause new entries if 1h move > X%
instrument_volatility_registry_lookup: true # use realized_vol_20 (1h candles) from FSS
```

## Execution semantics

- `ATOMIC` multi-leg TRADE for option entry (straddle / strangle / iron condor)
- `TRADE` for delta hedge on underlying (perp or future)
- `ATOMIC` roll at expiry: close expiring legs + open next-expiry legs in one instruction
- Never enter with only one leg open when the other fill fails — abort ATOMIC on partial fill

## P&L attribution

- **Theta P&L**: time decay collected per day (positive for short-vol); largest component in stable regimes
- **Vega P&L**: loss when vol rises post-entry, gain when vol falls (short-vol is short-vega)
- **Gamma P&L**: cost of delta-hedging realised moves (negative for short-gamma)
- **Delta-hedge slippage**: taker spread on hedge TRADE
- **Execution alpha**: vs mid on option fills

## Risk profile

- Primary risk: short-gamma blowout on vol spike (BTC ±20%+ in hours can exceed stop)
- Typical Sharpe: 1.5-2.5 in low-IV regimes; negative tail on sudden vol events
- Kill switches: RV > iv_stop_rv_multiple × IV; vega loss > stop_loss_vega_pct; venue outage
- Regime sensitivity: do NOT run during known high-vol events (FOMC, major protocol hacks, ETF approvals)

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    self.max_vega_usd = new_equity * self.config.max_vega_pct_of_equity
    return self._rescale_positions_to_vega_bound()
```

## Example instances

```
VOL_CARRY@deribit-btc-straddle-14dte-usdt-prod
VOL_CARRY@deribit-eth-strangle-14dte-usdt-prod
VOL_CARRY@deribit-btc-iron-condor-14dte-usdt-prod
VOL_CARRY@cboe-spy-straddle-weekly-usd-prod
VOL_CARRY@cboe-spx-iron-condor-weekly-usd-prod
```

## Not in this archetype

- **Directional vol view** (IV/RV divergence trade with a specific expectation) — `VOL_TRADING_OPTIONS` (legacy) or the
  specific view-expressing archetype (`VOL_ARB_RV_IV`)
- **Long vol** (straddle buyer) — also `VOL_ARB_RV_IV` if paired with a view; this archetype is short-vol carry only
- **Term structure expression** (sell expensive front / buy cheap back) — `VOL_TERM_STRUCTURE_ARB`
- **Skew expression** (risk reversal) — `VOL_SPREAD_STRUCTURES`
- **Delta-hedged single-leg gamma scalp** — `VOL_0DTE_GAMMA_SCALPING`
- **Options MM** (two-sided quoting on spread) — `VOL_MARKET_MAKING`

## See also

- Family: [vol-trading.md](../families/vol-trading.md)
- Realised-vs-implied divergence view: [vol-arb-rv-iv.md](vol-arb-rv-iv.md)
- Term structure carry arb: [vol-term-structure-arb.md](vol-term-structure-arb.md)
- Legacy options archetype: [vol-trading-options.md](vol-trading-options.md)
