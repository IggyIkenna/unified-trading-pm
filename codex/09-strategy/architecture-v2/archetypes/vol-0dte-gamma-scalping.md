---
doc_type: codex-ssot
title: "Archetype: `VOL_0DTE_GAMMA_SCALPING`"
summary:
  "Archetype spec for `VOL_0DTE_GAMMA_SCALPING` — buys cheap 0DTE ATM straddles at session open and captures realized
  gamma via frequent delta-hedge scalps, hard-closing before daily expiry; Deribit BTC/ETH, 100ms premium SLA."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, gamma-scalping, 0dte, delta-hedge]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-pin-risk.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_0DTE_GAMMA_SCALPING archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-pin-risk.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-leaps-convexity.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_0DTE_GAMMA_SCALPING
family: VOL_TRADING
venue_universe: [DERIBIT]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 100
  min_sla_tier: premium
---

# Archetype: `VOL_0DTE_GAMMA_SCALPING`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Same-day expiry — 0DTE straddles bought
> and delta-hedged intraday; all positions close at or before daily expiry. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_0dte_gamma_scalping_engine.py`

## What it does

Buys 0DTE (zero days to expiry) straddles at the start of the trading session when their implied vol is cheap relative
to the expected intraday price range, then captures realized gamma by delta-hedging frequently as the underlying moves
throughout the day. The edge is that 0DTE straddles, despite their low absolute premium, can have high realized gamma
relative to their theta cost when intraday realized vol exceeds the IV priced in. Large gamma at 0DTE means the delta of
each option changes rapidly with spot price moves, allowing frequent profitable hedge trades. The strategy requires fast
delta-hedge execution and is sensitive to intraday vol versus the overnight theta that set the straddle price. Works
primarily on BTC and ETH on Deribit, which offers daily option expirations with sufficient liquidity.

## Token / position flow

```
1. SESSION ENTRY CHECK (at market open / start of 0DTE window):
   - Fetch 0DTE ATM straddle IV (current session's expiry)
   - Compute expected_intraday_rv from pre-market indicators:
       - Yesterday's intraday realized vol (rolling 20-session average)
       - Overnight futures price range as vol proxy
       - Perp funding spike as vol predictor
   - Entry signal: expected_intraday_rv > entry_rv_to_iv_ratio × straddle_iv
   - Check straddle ask <= max_straddle_cost_pct × spot (budget filter)

2. POSITION SIZING:
   - gamma_target_notional_usd: size straddle position to achieve target gamma exposure
   - n_contracts = gamma_target_notional / (option_gamma × spot² × contract_size)
   - Cap at max_contracts

3. ENTRY: ATOMIC TRADE — BUY ATM call + BUY ATM put (same strike, 0DTE expiry)
   - Must execute within entry_window_min of session open
   - If fill > max_fill_slip_bps above mid: abort (avoid adverse selection at open)

4. GAMMA SCALP LOOP (intraday):
   - Compute net_delta of straddle book (starts near 0 at ATM)
   - As underlying moves: |net_delta| grows (gamma effect)
   - When |net_delta| > scalp_delta_threshold:
       - TRADE underlying perp to flatten delta (buy if net_delta < 0, sell if > 0)
       - Scalp P&L ≈ 0.5 × gamma × (delta_move)² per scalp cycle
   - Scalp frequency: up to max_scalps_per_hour; rate-limited to control taker fees
   - Track cumulative_scalp_income vs cumulative_theta_cost in real time

5. INTRADAY MONITORING:
   - Stop: cumulative_theta_cost > theta_stop_multiple × current_scalp_income AND session
     < stop_latest_hour (i.e. early morning is unproductive — exit before theta erodes premium)
   - Target: cumulative_scalp_income > take_profit_multiple × initial_straddle_cost
   - Vol collapse: if 1h realized vol < vol_collapse_exit_threshold, exit early (no scalp opportunity)

6. SESSION CLOSE:
   - By close_before_expiry_min before expiry: EXIT ALL positions
   - Sell straddle (or let expire worthless if deep OTM)
   - Square all perp delta hedges
   - Log: session_pnl = scalp_income + straddle_exit_value − straddle_cost − fees
```

## Entry conditions + signal

- `expected_intraday_rv > entry_rv_to_iv_ratio × straddle_0dte_iv` (e.g. ratio = 1.15 — expect 15% more intraday vol
  than the straddle prices in)
- Straddle ask <= max_straddle_cost_pct × spot (e.g. 0.005 = 0.5% of spot price cap)
- Session opens within trading_session_start_utc ± entry_window_min
- Sufficient underlying liquidity for high-frequency delta hedging (perp bid-ask < max_perp_spread_bps)
- Not a known low-volatility day (holiday, post-event calm confirmed by overnight range < low_vol_threshold)

## Risk management

- Max loss = initial straddle premium paid (long vol, bounded loss)
- Theta stop: exit early if session looks unproductive (theta eroding faster than scalp income)
- Scalp fee discipline: each scalp must exceed 2× taker fee in expected gamma P&L; use wider scalp threshold if fees are
  high
- Vol collapse exit: if intraday vol collapses, the scalp opportunity is gone — cut losses early
- Expiry discipline: HARD close before expiry to avoid binary expiry P&L and pin risk
- Perp hedge slippage: large delta swings near strong support/resistance can cause hedge slippage; use limit orders when
  market is not fast-moving

## Config parameters

- `underlying`: BTC | ETH
- `venue`: DERIBIT (primary; only venue with daily 0DTE crypto options + liquid perp for hedging)
- `trading_session_start_utc`: session open time (e.g. "08:00")
- `entry_window_min`: minutes after open to permit entry (e.g. 30)
- `close_before_expiry_min`: mandatory exit before expiry (e.g. 15)
- `entry_rv_to_iv_ratio`: expected RV / straddle IV entry threshold (e.g. 1.15)
- `max_straddle_cost_pct`: max straddle ask as fraction of spot (e.g. 0.005)
- `gamma_target_notional_usd`: target gamma dollar exposure (e.g. 50_000)
- `max_contracts`: hard cap on straddle size
- `scalp_delta_threshold`: trigger delta-hedge scalp at this delta level (e.g. 0.05)
- `max_scalps_per_hour`: rate limit for hedge trades (e.g. 20)
- `max_perp_spread_bps`: max perp bid-ask to permit hedging (e.g. 3)
- `theta_stop_multiple`: exit if theta_cost > this × current_scalp_income (e.g. 2.0) by mid-session
- `stop_latest_hour`: latest hour (UTC) to apply theta stop (e.g. 12 — give morning session 4h)
- `take_profit_multiple`: exit if scalp_income > this × initial_straddle_cost (e.g. 2.0)
- `vol_collapse_exit_threshold`: exit if 1h realized vol < this fraction of entry IV (e.g. 0.50)

## When to use / market regime

- **Best regime**: high realized-vol days with frequent intraday price swings; particularly good during macro print
  days, token unlock events, or after overnight large moves that suggest continuation
- **Avoid**: post-event quiet days where overnight vol was high but intraday is expected to calm; also avoid
  Sundays/holidays with thin perp liquidity that makes delta hedging expensive
- **Latency requirement**: premium SLA tier — scalp hedge trades must execute within 100ms of trigger; deploy on
  low-latency infrastructure near Deribit matching engine
- **Asset fit**: BTC and ETH exclusively (Deribit 0DTE daily expirations; ETH also has fine liquidity)
- **Complements**: `VOL_CARRY` (0DTE scalping as active gamma collection; carry as passive theta harvest)

## Example instances

```
VOL_0DTE_GAMMA_SCALPING@deribit-btc-atm-straddle-0dte-usdt-prod
VOL_0DTE_GAMMA_SCALPING@deribit-eth-atm-straddle-0dte-usdt-prod
VOL_0DTE_GAMMA_SCALPING@deribit-btc-atm-straddle-0dte-usdt-paper
```

## Not in this archetype

- Pin risk management for short-gamma books near expiry strikes → [`VOL_0DTE_PIN_RISK`](vol-0dte-pin-risk.md)
- Passive theta harvest via short straddle / strangle held for days → [`VOL_CARRY`](vol-carry.md)
- Longer-tenor straddle positioning without intraday scalp loop → [`VOL_STRADDLE`](vol-straddle.md)
- Continuous two-sided quoting on an option book → [`VOL_MARKET_MAKING`](vol-market-making.md)

## See also

- Vol straddle (longer tenor): [vol-straddle.md](vol-straddle.md)
- Vol market making: [vol-market-making.md](vol-market-making.md)
- Vol carry: [vol-carry.md](vol-carry.md)
- Family: [vol-trading.md](../families/vol-trading.md)
