---
scope: [engineer, admin]
---

# Family: Vol Trading

> **Alpha source:** Volatility-metric dislocation. The alpha is a view on _vol itself_ (IV vs RV, skew, term structure,
> cross-asset vol) — not a directional view on the underlying. Positions are typically delta-hedged so that P&L comes
> from vega, gamma, and theta, not delta.
>
> **Primary edge method:** Vol-metric dislocation vs fair (IV too rich/cheap vs realized; skew extreme vs historical;
> term structure bowed beyond no-arb bounds).
>
> **Typical hold policies:** CONTINUOUS (dynamic gamma scalping + vega exposure management) or HOLD_UNTIL_FLIP
> (event-bounded vol trades).
>
> **Archetype count:** 1 — `VOL_TRADING_OPTIONS`.

## Alpha thesis

Vol Trading captures alpha from volatility metrics dislocating from historical or model-implied norms. Key sub-patterns:

- **IV vs RV**: implied vol (market's forward expectation) diverges from realized vol (historical / recent) — long /
  short vol accordingly. Statistical view; not risk-free.
- **Skew dislocation** (soft): 25d put skew rich vs historical → sell puts / buy calls (risk reversal). Directional view
  on skew mean-reverting; not a no-arb violation.
- **Term structure** (soft): front-month IV richer than back-month vs typical carry-adjusted shape → calendar trades.
  Directional view; not a no-arb violation.
- **Soft surface residuals**: fitted IV surface (e.g., SVI) has residuals at specific strikes that suggest a strike is
  rich/cheap vs model-fair, but does NOT violate no-arb bounds. Directional view that the residual re-equilibrates.
- **Cross-asset vol (pair)**: BTC vol / ETH vol outside historical band → pair (but if this is the alpha source, this
  sits in Stat Arb / Pairs family as a vol-pair instance)

**Belongs in [`ARBITRAGE_PRICE_DISPERSION`](../archetypes/arbitrage-price-dispersion.md), NOT here:**

- Cross-venue vol arb (same option / same strike / same expiry quoted at different IVs on two venues, e.g., Deribit vs
  OKX options) — mechanical dispersion of the same instrument.
- Hard no-arb violations within a single venue's surface (butterfly convexity violation, calendar arbitrage where
  front > back beyond carry, put-call parity violations) — mechanical, near-risk-free.

**The distinguishing test:** is the edge _mechanical_ (guaranteed conditional on correct execution; cross-venue
same-option dispersion or a no-arb bound violation) or _statistical_ (profitable on average with spread risk; vol metric
expected to mean-revert)? Mechanical → Arbitrage. Statistical → Vol Trading.

Delta-hedged implementation is essential: the strategy takes a vol view, not a directional view. Delta hedging removes
directional exposure (or maintains a specific delta target).

**Not in this family:**

- Directional option trade (long call because bullish BTC) → ML Directional with options expression
- MM on options (earn spread, no vol view) → Market Making
- Options MM on vol mispricing (vol edge is primary alpha, spread capture secondary) → Vol Trading (this family)
- Cross-asset vol ratio mean-reversion → Stat Arb / Pairs (vol-pair variant)

## 1 Archetype

[`VOL_TRADING_OPTIONS`](../archetypes/vol-trading-options.md) — all vol-trading patterns within a single options venue
(Deribit BTC/ETH, CBOE SPY).

Why a single archetype: the code structure (vol surface fitter + dislocation detector + delta-hedge + greeks
management + risk bounds) is the same regardless of which specific vol dislocation you're capturing. Differences are
config: which vol edge method, which underlying, which strikes.

## Shared primitives

- **IV surface fitter**: fit SVI / SSVI / arbitrage-free surface to current market option prices; residuals =
  dislocations
- **Realized vol computer**: rolling RV estimators (close-to-close, Parkinson, Garman-Klass, Yang-Zhang)
- **Greeks computer**: delta, gamma, vega, theta, rho per position + portfolio-level
- **Delta-hedge engine**: dynamic hedging via underlying (spot, perp, future); configurable hedge band + frequency
- **Gamma-scalping engine**: long gamma strategies harvest realized vol by rehedging as underlying moves
- **Vol-trade constructors**: straddle, strangle, butterfly, calendar, risk reversal, skew trades — reusable payoff
  primitives
- **Expiry / time-decay manager**: close positions before ultra-short-expiry gamma spike; roll calendars at expiry
- **Cross-underlier correlation tracker** (for cross-asset vol)

## Typical signal sources

| Signal                                          | Source                                |
| ----------------------------------------------- | ------------------------------------- |
| IV surface grid                                 | Deribit mark IV per (strike, expiry)  |
| Realized vol                                    | Tick/minute history of underlying     |
| IV / RV ratio                                   | Computed continuously                 |
| Skew (25d put IV - 25d call IV)                 | Surface fitter output                 |
| Term structure (front vs back month)            | Surface fitter output                 |
| Put-call ratio                                  | Option flow feed                      |
| Historical vol percentiles                      | Rolling 90d / 1y histograms           |
| Event-upcoming indicator (for vol-event trades) | Event calendar + vol-surface reaction |

## Typical edge methods

- **IV/RV divergence**: `|IV - RV| > threshold` and persistent across observation window
- **Skew percentile extreme**: current skew < 5th or > 95th historical percentile
- **Term structure inversion**: front > back beyond no-arb + carry bounds
- **Soft surface residual**: per-strike IV residual from fitted surface > fit error threshold, but WITHIN no-arb bounds
  (statistical bet on residual re-equilibrating). Hard no-arb violations belong in `ARBITRAGE_PRICE_DISPERSION`.
- **Vol regime prediction**: ML-classified "vol expanding" or "vol contracting" state

## Position structure

- Option positions (long or short depending on vol view)
- Underlying hedge (delta-neutral by default; can target non-zero delta if strategy includes directional overlay)
- Multi-leg: straddles, strangles, butterflies, calendars, risk reversals
- Rolling: positions replaced before expiry, calendars rolled at front-month expiry

## Typical staking methods

| Method              | When used                                                                  |
| ------------------- | -------------------------------------------------------------------------- |
| Vega-notional cap   | Default — limit total vega exposure relative to equity                     |
| Gamma-notional cap  | Complementary — limit convexity exposure                                   |
| Notional-scaled     | Similar to cash-and-carry, scale with equity proportionally                |
| Scenario-PnL-capped | Limit worst-case P&L under scenario grid (e.g., ±10% move × ±20% IV shift) |

## Venue patterns

- **Deribit**: primary crypto options (BTC, ETH); portfolio margin available; tight spreads on ATM
- **CBOE**: SPY options (US equity index); via IBKR routing
- **CME**: options on futures (ES options, CL options, etc.); dated expiries
- **OKX options** (secondary): backup or for specific strikes

## Expression options

- Straddle (ATM long/short) — pure vol expression
- Strangle (OTM long/short) — cheaper pure vol with wider breakeven
- Butterfly — pure convexity view
- Calendar (buy back-month / sell front-month) — term structure view
- Risk reversal (sell put / buy call or vice versa) — skew view
- Iron condor / iron butterfly — spread combinations
- Delta-hedged single leg (e.g., long call, hedged) — gamma-scalping, vol-long

## Risk profile

- **Drawdowns**: can be sharp during vol explosions (short vol blown up); well-managed long vol is rarely catastrophic
- **Tail risks**:
  - Short vol regime change (VIX-style explosion)
  - Deribit settlement mechanics (perpetual vs dated)
  - Liquidity drying up on far OTM strikes
  - Cross-expiry roll timing (calendar P&L jumps on roll)
- **Sharpe**: wide range; well-executed vol strategies 1.5-3.0
- **Kill switches**: vol spike > N × regime, position greeks breach, IV > configured ceiling (indicates regime
  disruption)

## UI dashboard

- IV surface grid (with overlaid fitted surface)
- IV percentile rank per strike
- Realized vol rolling
- Current greeks + portfolio scenario P&L grid
- Delta-hedge event log (when + why hedged)
- Vol P&L attribution (vega, gamma, theta, delta-hedge-slippage)
- Surface residuals heatmap (for surface arb)

## Required subscriptions

Config references:

- **venue_capability_ref** (Deribit typically)
- **feature_group_refs** — IV surface, RV, historical vol percentiles
- **surface_model_ref** — fitted surface model artifact (SVI, SSVI)
- **vol_edge_model_ref** (optional) — ML model predicting IV/RV divergence
- **execution_policy_ref** — options-specific execution policy (iceberg for size, mid-price for tight spreads)

## Typical instance examples

```
Deribit BTC vol trading:
  VOL_TRADING_OPTIONS@deribit-btc-straddle-usdt-prod       (IV vs RV divergence)
  VOL_TRADING_OPTIONS@deribit-btc-skew-usdt-prod           (skew extreme)
  VOL_TRADING_OPTIONS@deribit-btc-surface-usdt-prod        (surface residuals)
  VOL_TRADING_OPTIONS@deribit-btc-calendar-usdt-prod       (term structure)

Deribit ETH vol trading:
  VOL_TRADING_OPTIONS@deribit-eth-straddle-usdt-prod
  VOL_TRADING_OPTIONS@deribit-eth-skew-usdt-prod
  VOL_TRADING_OPTIONS@deribit-eth-surface-usdt-prod

CBOE SPY vol:
  VOL_TRADING_OPTIONS@cboe-spy-vol-ml-usd-prod
  VOL_TRADING_OPTIONS@cboe-spy-gamma-scalping-usd-prod
```

## Reaction to capital flow events

```python
def react_to_equity_change(self, new_equity_usd: Decimal) -> list[StrategyInstruction]:
    self.equity_usd = new_equity_usd
    self.max_vega_notional = new_equity_usd * self.config.max_vega_pct
    self.max_gamma_notional = new_equity_usd * self.config.max_gamma_pct
    return self._rescale_positions_to_vega_bound()
```

## Rebalancing triggers

- Delta drift > band → emit hedge TRADE on underlying
- IV surface changes → re-evaluate entries/exits
- New vol dislocation detected → enter new position
- Vol dislocation closes → exit position
- Expiry approaching → roll / close
- Equity change → rescale vega / gamma bounds

## Migration from legacy docs

| Legacy                                          | Mapping                                                                                                             | Notes                          |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| `tradfi/options-ml.md`                          | `VOL_TRADING_OPTIONS` (if vol alpha) OR `ML_DIRECTIONAL_CONTINUOUS` (if delta alpha)                                | Config disambiguates           |
| `tradfi/market-making-options.md`               | `MARKET_MAKING_CONTINUOUS` (if spread-capture primary) OR `VOL_TRADING_OPTIONS` (if vol alpha primary)              | Config disambiguates           |
| Code: `strategy-service/.../options_ml_*.py`    | Split: delta-ML → `MLDirectionalContinuousEngine`, vol-ML → `VolTradingOptionsEngine`, strike-ML → depends on alpha | Per strategy                   |
| Code: `strategy-service/.../vol_surface_btc.py` | `VolTradingOptionsEngine`                                                                                           | Surface arb as vol edge method |

## Cross-references

- Archetype: [vol-trading-options](../archetypes/vol-trading-options.md)
- Options MM distinction: [market-making.md](market-making.md) (spread capture as primary alpha)
- Cross-asset vol pair: [stat-arb-pairs.md](stat-arb-pairs.md) (if alpha is ratio mean-reversion)
- Greeks / risk: [../cross-cutting/risk-gates.md](../cross-cutting/risk-gates.md)
