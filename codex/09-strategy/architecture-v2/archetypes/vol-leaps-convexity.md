---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 300
  min_sla_tier: standard
---

# Archetype: `VOL_LEAPS_CONVEXITY`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Expiry-driven with long-dated quarterly
> roll — positions held 30-180 days; rolled at quarterly expiry or on vol spike trigger. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_leaps_convexity_engine.py`

## What it does

Buys long-dated options (180d+, referred to as LEAPS in traditional markets) when long-term implied volatility is cheap
relative to near-term realised volatility expectations. Long-dated options have high vega relative to theta, meaning
large realised volatility events pay off asymmetrically — a single large move can recoup months of theta decay. The
strategy holds through vol cycles, collecting asymmetric upside from vol regime changes while accepting slow theta
bleed in quiet periods. Exit is triggered when long-dated IV spikes (the vol the strategy was long becomes expensive —
take profit) or when time-to-expiry falls below the short-tenor threshold.

## Token / position flow

```
1. CHEAPNESS SCAN (weekly):
   - Extract far-dated ATM IV at target_tenor_dte (180d+)
   - Compare vs near-term IV expectations: rolling 5d RV × expansion_factor
   - LEAPS cheapness ratio: far_IV / (near_RV × expansion_factor)
   - Entry when ratio < entry_cheapness_ratio (long-vol is cheap)

2. CONVEXITY SCORE:
   - Compute vega / theta ratio at target tenor (high ratio = good convexity)
   - Compare vega_per_theta vs rolling 30d median
   - Prefer calls for bullish/neutral regime; puts for tail-risk hedge

3. POSITION SIZING:
   - Budget-based: size by theta_budget_daily_usd (max theta bleed per day)
   - theta_daily = option_theta × num_contracts × spot
   - max_contracts = theta_budget_daily_usd / (theta_daily_per_contract × spot)

4. ENTRY: TRADE (long option position at far expiry)
   - Prefer ATM or slight OTM (0.85-1.00 moneyness) for convexity
   - Single-leg (long call or long put or long straddle)

5. HOLD:
   - No delta hedging by default (preserve convexity / gamma optionality)
   - Optional: delta-hedge if net_delta > leaps_delta_hedge_threshold
   - Monitor IV daily: record rolling far-tenor IV for exit trigger

6. EXIT:
   - VOL SPIKE EXIT: far_IV > entry_IV × spike_exit_iv_multiple (take profit on vol)
   - EXPIRY ROLL: DTE < roll_at_dte → sell current + buy next quarterly expiry
   - STOP LOSS: position value < stop_loss_value_pct × initial_premium
   - TIME STOP: if theta accumulated > max_theta_bleed_pct × initial_premium
```

## Entry conditions + signal

- `far_IV / (near_RV × expansion_factor) < entry_cheapness_ratio` (default 0.85)
- `vega_per_theta > min_vega_theta_ratio` (default 20.0)
- `target_tenor_dte > min_leaps_dte` (default 90)
- Available expiry at target tenor with OI > min_leaps_oi
- Not already at max_leaps_positions_count

## Risk management

- Maximum total theta bleed per day: theta_budget_daily_usd (hard cap)
- Stop loss per position: stop_loss_value_pct of initial premium (default 60%)
- Vol spike exit is a PROFIT-TAKING trigger — do not suppress in fear of missing further upside
- Max position count: max_leaps_positions_count (default 3 concurrent LEAPS positions)
- Roll to quarterly — never let LEAPS decay into the short-gamma zone (< roll_at_dte DTE)

## Config parameters

- `underlying`: `BTC` | `ETH` (Deribit quarterly expiries)
- `target_tenor_dte`: minimum DTE at entry for LEAPS classification (default 90, prefer 180+)
- `option_type`: `call` | `put` | `straddle` — depends on regime view
- `target_moneyness`: moneyness at entry (default 0.95 = slight OTM call)
- `entry_cheapness_ratio`: far_IV / near_vol_expectation entry threshold (default 0.85)
- `expansion_factor`: multiplier on near-term RV for long-term vol expectation (default 1.2)
- `min_vega_theta_ratio`: convexity quality filter (default 20.0)
- `theta_budget_daily_usd`: maximum daily theta bleed across all LEAPS positions (default 200)
- `spike_exit_iv_multiple`: exit when far_IV > entry_IV × this multiple (default 1.5)
- `roll_at_dte`: roll to next quarterly when DTE drops below this (default 30)
- `stop_loss_value_pct`: stop loss as fraction of initial premium paid (default 0.60)
- `max_leaps_positions_count`: max concurrent LEAPS positions (default 3)
- `leaps_delta_hedge_threshold`: delta above which optional hedge is applied (default 0.70)
- `share_class`: USDT | USD
- `execution_policy_ref`: options-taker-v1

## When to use / market regime

- **Use when**: long-dated IV is historically cheap; near-term vol events expected over the next 1-6 months;
  theta budget allows slow bleed through a quiet period
- **Best regime**: post-crash recovery with low far-dated IV; pre-election / pre-halving periods where long-term event
  risk is not yet priced; equity market complacency with VIX < 15 (apply to SPX LEAPS)
- **Avoid**: very expensive long-dated vol (above historical 80th percentile); illiquid far-expiry option chains;
  when near-term vol is already elevated (theta carry cost too high relative to expected payoff)
- **Best instruments**: BTC/ETH quarterly expiries on Deribit; SPX LEAPS on CBOE via IBKR

## See also

- Family: [vol-trading.md](../families/vol-trading.md)
- Short-vol carry (opposite vol view): [vol-carry.md](vol-carry.md)
- Term structure (intermediate-tenor slope): [vol-term-structure-slope.md](vol-term-structure-slope.md)
