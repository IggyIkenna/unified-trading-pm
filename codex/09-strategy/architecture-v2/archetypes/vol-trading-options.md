---
doc_type: codex-ssot
title: "Archetype: `VOL_TRADING_OPTIONS`"
summary:
  "Archetype spec for `VOL_TRADING_OPTIONS` (legacy general vol-view engine) — delta-hedged options expressing IV/RV,
  skew, term, or soft-surface-residual dislocations via straddle/strangle/butterfly/calendar/risk-reversal; the granular
  VOL_* archetypes carve out its specific expressions."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, iv-rv, skew, delta-hedge]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/stat-arb-pairs-fixed.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-arb-rv-iv.md,
    ../families/vol-trading.md,
  ]
created: 2026-04-17
authoritative_for: ["VOL_TRADING_OPTIONS archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_TRADING_OPTIONS
family: VOL_TRADING
venue_universe: [DERIBIT, CBOE, OKX_OPTIONS]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `VOL_TRADING_OPTIONS`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Continuous — options positions actively
> managed with delta hedging, rebalancing on greeks drift, and roll at expiry. **Code module (target):**
> `strategy-service/engine/strategies/vol_trading_options_engine.py`

## What it does

Expresses a directional view on a vol metric (IV/RV divergence, skew, term structure, soft surface residuals) through a
delta-hedged options position. P&L comes from vega, gamma, and theta — not delta. Statistical, not risk-free.

## Token / position flow

```
1. SURFACE FITTER: continuously fit IV surface (SVI or SSVI) to current option prices

2. VOL DISLOCATION SCANNER:
   - IV vs RV: compute (IV - realized_vol) at each tenor; persistent divergence?
   - Skew extreme: 25d put skew vs historical percentile
   - Term bowed: front-month vs back-month richness beyond carry norm
   - Soft surface residual: strike IV residual within no-arb bounds but rich/cheap vs fair
   (Hard no-arb violations → `ARBITRAGE_PRICE_DISPERSION`, not here)

3. TRADE CONSTRUCTOR:
   - Straddle (ATM long/short) for IV/RV bet
   - Strangle (OTM long/short) for IV/RV cheaper-wider
   - Butterfly (convexity bet) for central-strike dislocation
   - Calendar (buy back, sell front) for term structure
   - Risk reversal (sell put, buy call or vice versa) for skew
   - Single leg + delta hedge (gamma scalping)

4. ENTRY: emit ATOMIC multi-leg + delta-hedge TRADE
   options leg(s) on Deribit/CBOE + underlying hedge on Deribit perp / IBKR equity

5. HOLD:
   - Delta-proxy rehedge: when underlying move breaches hedge band, emit hedge TRADE
   - Greeks monitor: portfolio vega, gamma, theta, vanna, vomma tracked continuously
   - Vol P&L realized continuously; theta decay continuously negative for long-vol, positive for short-vol

6. EXIT:
   - Take profit: vega_pnl > target
   - Stop loss: vega_pnl < -stop
   - Time decay: dte < exit_dte (roll to next expiry if still holding vol view)
```

## Supported venues / instruments

**Coverage matrix:** See
[`../category-instrument-coverage.md § 16. VOL_TRADING_OPTIONS`](../category-instrument-coverage.md#16-vol_trading_options)
for the authoritative venue × underlying × expiry-chain coverage (Deribit BTC/ETH, CBOE via IBKR, CME options-on-
futures, OKX alternate, NSE India — Oct 2026 go-live).

## Expression options

- **Straddle**: long/short ATM call + put (pure vol)
- **Strangle**: long/short OTM call + put (cheaper vol with wider breakeven)
- **Butterfly**: convexity trade
- **Iron condor**: short strangle + long further-out strangle (capped risk vol-short)
- **Calendar**: sell front / buy back (term structure)
- **Diagonal**: calendar with different strikes
- **Risk reversal**: long call / short put or vice versa (skew)
- **Delta-hedged single leg**: long call hedged with short underlying (gamma scalp)

## Hold policies

- CONTINUOUS (rebalance greeks)
- HOLD_UNTIL_FLIP if vol metric reverts before expiry
- Roll at pre-expiry if view persists

## Config schema

```yaml
underlying: BTC
venue: DERIBIT
surface_model_ref: svi-btc-v3 # versioned surface model
vol_edge_method: IV_RV_DIVERGENCE # or SKEW, TERM, SOFT_RESIDUAL
iv_rv_divergence_threshold: 0.10 # 10% (IV 50%, RV 40% → trade)
min_days_to_expiry: 7
max_days_to_expiry: 45
max_vega_notional_usd: 75_000
max_gamma_notional_usd: 15_000
delta_hedge_band_pct: 0.05 # rehedge when |delta| > 5% of vega
hedge_venue: DERIBIT # hedge on same venue usually
hedge_instrument: "DERIBIT:PERPETUAL:BTC-PERPETUAL"
time_decay_exit_dte: 3
take_profit_vega_pct: 0.25 # realize at 25% vega-P&L gain
stop_loss_vega_pct: 0.40 # stop at 40% vega-P&L loss
share_class: USDT
execution_policy_ref: options-mm-v2 # use MM-aware algo for tight spreads

# Leverage + net-delta controls (universal per StrategyInstanceDefinition; Stream D 2026-05-07):
target_leverage: 1.0 # [1, 10]; options notional vs equity; delta-hedge via perp leg
target_net_delta: 0.0 # net directional delta (0 = delta-hedged; vega-only exposure)
max_underlying_move_pct: 3.0 # vol-cap clamp: skip entry if realized move > X% in 1h window
instrument_volatility_registry_lookup: true # use realized_vol_20 (1h candles) from FSS
```

## Execution semantics

- `ATOMIC` multi-leg orders on options venue (Deribit supports multi-leg structures)
- `TRADE` for delta hedge on underlying
- Roll at expiry: ATOMIC (close expiring + open next-expiry)

## P&L attribution

- **Vega P&L**: vol movement × vega × days held
- **Gamma P&L**: realized vol captured via delta rehedges (gamma scalping positive for long-vol)
- **Theta P&L**: time decay (negative for long-vol, positive for short-vol)
- **Delta-hedge slippage**: cost of rehedging (ideally zero at true vol; >0 in practice)
- **Execution alpha**: per leg

## Risk profile

- Drawdowns: can be sharp on vol regime change (short-vol blown up on VIX spike)
- Typical Sharpe: 1.0-2.5; short-vol regimes 2+ but tail-risky
- Kill switches: vol spike > N × regime, greeks breach, IV > configured ceiling (regime disruption)

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    self.max_vega_usd = new_equity * self.config.max_vega_pct
    return self._rescale_positions_to_vega_bound()
```

## Example instances

```
VOL_TRADING_OPTIONS@deribit-btc-iv-rv-usdt-prod               (IV/RV divergence trades)
VOL_TRADING_OPTIONS@deribit-btc-skew-usdt-prod                 (skew percentile)
VOL_TRADING_OPTIONS@deribit-btc-calendar-usdt-prod             (term structure)
VOL_TRADING_OPTIONS@deribit-btc-gamma-scalp-usdt-prod           (delta-hedged long-vol)
VOL_TRADING_OPTIONS@deribit-eth-iv-rv-usdt-prod
VOL_TRADING_OPTIONS@deribit-eth-skew-usdt-prod
VOL_TRADING_OPTIONS@cboe-spy-vol-usd-prod                      (CBOE SPY options)
VOL_TRADING_OPTIONS@cboe-spy-gamma-scalp-usd-prod
```

## Not in this archetype

- **Cross-venue IV arb** (same option different IV on Deribit vs OKX) — that's mechanical dispersion, goes to
  `ARBITRAGE_PRICE_DISPERSION`
- **Hard no-arb violations** (butterfly convexity violated, put-call parity violated, calendar carry-violated) —
  mechanical, also `ARBITRAGE_PRICE_DISPERSION`
- **Cross-asset vol ratio mean-reversion** (BTC-vol / ETH-vol pair) — spread risk exists, goes to `STAT_ARB_PAIRS_FIXED`
  with vol instruments
- **Directional options trades** where the alpha is the underlying direction (not vol) — goes to
  `ML_DIRECTIONAL_CONTINUOUS` with options expression
- **Options MM** where the alpha is spread capture (not vol view) — goes to `MARKET_MAKING_CONTINUOUS`
- **Event-driven vol** where the alpha is IV crush around FOMC — borderline; if alpha is pure vol reaction to event,
  could be VOL_TRADING_OPTIONS with event-aware config, but if alpha is directional reaction, it's EVENT_DRIVEN

## Migration from legacy

| Legacy                                | Notes                                                                                 |
| ------------------------------------- | ------------------------------------------------------------------------------------- |
| `tradfi/options-ml.md`                | If alpha is vol → this archetype; if alpha is delta → `ML_DIRECTIONAL_CONTINUOUS`     |
| `tradfi/market-making-options.md`     | If spread capture primary → `MARKET_MAKING_CONTINUOUS`; if vol alpha → this archetype |
| Code: `vol_surface_btc.py`            | Soft residuals → this; hard no-arb → `ArbitragePriceDispersionEngine`                 |
| Code: `options_ml_vol_eth_deribit.py` | → `VolTradingOptionsEngine`                                                           |
| Code: `options_ml_delta_*.py`         | → `MLDirectionalContinuousEngine` (delta-direction, not vol)                          |

## See also

- Family: [vol-trading.md](../families/vol-trading.md)
- Arbitrage variant for hard dispersion: [arbitrage-price-dispersion.md](arbitrage-price-dispersion.md)
- Stat arb for cross-asset vol pair: [stat-arb-pairs-fixed.md](stat-arb-pairs-fixed.md)
