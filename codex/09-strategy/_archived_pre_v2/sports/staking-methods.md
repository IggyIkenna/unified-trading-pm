---
scope: [engineer, admin]
---

# Sports Staking Methods

> Cross-cutting concern for all sports strategies. Staking methods determine **bet size**, not which bets to place.
> Signal generation (which bets) comes from strategy code. Staking (how much) comes from here.

## Overview

Every sports strategy produces signals with an edge estimate. The staking method converts that edge into a dollar stake.
The system provides six staking methods across two code paths: `kelly.py` for live signal sizing (used by
`KellyCriterionStrategy`, `MLSportsStrategy`, and `HalftimeMLStrategy`) and `betting_strategies.py` for backtest
research (used by `backtest_engine.py`). Both paths share the same Kelly formula.

## Available Methods

### Kelly Criterion (Fractional)

The core formula for bankroll-optimal growth under uncertainty:

```
f* = (p * b - q) / b
```

Where `f*` = fraction of bankroll to wager, `p` = model probability of winning, `q` = 1 - p, and `b` = net odds
(decimal_odds - 1). Raw Kelly is aggressive (maximises long-run geometric growth but with high variance), so production
always uses fractional Kelly: multiply `f*` by a fraction (typically 0.25-0.5) and clamp to a maximum fraction (default
5%).

- **Parameters:** `fractional_kelly` (0.25-0.5 typical), `max_bet_fraction` (default 0.05), `min_edge` (default 0.02)
- **When to use:** ML strategies where model probability estimates are well-calibrated
- **Code:** `kelly.py::compute_kelly_fraction()` (standalone function, lines 31-52)

### Portfolio Kelly

Adjusts individual Kelly fractions when multiple bets are placed simultaneously from a shared bankroll. Computes
individual Kelly fractions for each bet, then if total exposure exceeds 100% of bankroll, scales all fractions
proportionally so they sum to 1.0.

- **When to use:** Slate days with many concurrent qualifying bets (e.g. Saturday football fixtures)
- **Code:** `kelly.py::KellyCriterionStrategy.portfolio_kelly()` (lines 181-206)

### Venue-Constrained Kelly

Returns an absolute stake amount (not a fraction) that respects venue-imposed limits. Takes the minimum of: Kelly
optimal stake, venue maximum bet size, and account maximum observed accepted stake. This handles the real-world
constraint that bookmakers restrict stakes for profitable accounts.

- **When to use:** Any live execution where venue limits are known
- **Code:** `kelly.py::KellyCriterionStrategy.venue_constrained_kelly()` (lines 231-255)

### Simultaneous Kelly

Adjusts Kelly sizing for bankroll already committed to open bets. If 30% of bankroll is in open bets, the calculation
uses the remaining 70% as the effective bankroll. Current exposure is capped at 95% to prevent division-by-zero edge
cases.

- **When to use:** Live betting with multiple open positions across concurrent events
- **Code:** `kelly.py::KellyCriterionStrategy.simultaneous_kelly()` (lines 208-229)

### Fixed Dollar (FixedDollarV2)

Every qualifying bet gets the same stake regardless of edge or odds. Default $10,000 per bet. Returns zero if current
capital is below the fixed amount.

- **Parameters:** `stake_amount` (default $10,000)
- **When to use:** Baseline strategy for backtesting; isolates signal quality from position sizing
- **Code:** `betting_strategies.py::FixedDollarV2` (lines 107-129)

### Fixed Percentage (FixedPercentageV2)

Bets a fixed percentage of **initial** capital (not current) to avoid compounding risk. Safety cap: never bets more than
`max_pct_of_current` of current capital. Returns zero if computed stake is below minimum.

- **Parameters:** `stake_pct` (default 2%), `max_pct_of_current` (default 5%), `min_stake` (default $100)
- **When to use:** Conservative staking for strategies with uncertain calibration
- **Code:** `betting_strategies.py::FixedPercentageV2` (lines 132-165)

### Adaptive Daily (AdaptiveDailyV2)

Daily budget = `daily_budget_pct` of initial capital, divided across expected daily bets. As bets are placed throughout
the day, remaining slots shrink and per-bet allocation grows. An edge multiplier (`1.0 + edge_pct / 10`, capped at 2x)
scales higher-edge bets up. Final stake is clamped to min/max bounds and a 10% of current capital safety cap.

- **Parameters:** `daily_budget_pct` (default 5%), `min_stake` ($500), `max_stake` ($50,000), `expected_daily_bets`
  (default 10)
- **When to use:** High-volume strategies (10+ bets/day) where daily risk budget matters
- **Code:** `betting_strategies.py::AdaptiveDailyV2` (lines 168-213)

### Fractional Kelly V2 (FractionalKellyV2)

Backtest-oriented Kelly implementation in `betting_strategies.py`. Uses the same `f* = (p*b - q) / b` formula but
operates on `BankrollState` (tracking initial/current capital, daily counts, drawdown). Default fraction is 0.25
(quarter-Kelly) with a 5% max cap.

- **Parameters:** `kelly_fraction` (default 0.25), `max_pct` (default 5%), `min_stake` ($100)
- **When to use:** Backtest research with Kelly sizing; mirrors live Kelly but within the backtest framework
- **Code:** `betting_strategies.py::FractionalKellyV2` (lines 216-261)

## Which Strategy Uses Which Method

| Strategy               | Staking Method             | Code Path                          | Context      |
| ---------------------- | -------------------------- | ---------------------------------- | ------------ |
| MLSportsStrategy       | Fractional Kelly           | `kelly.py::compute_kelly_fraction` | Live signals |
| HalftimeMLStrategy     | Fractional Kelly           | `kelly.py::compute_kelly_fraction` | Live in-play |
| KellyCriterionStrategy | All Kelly variants         | `kelly.py` (class methods)         | Live signals |
| Value Betting          | Edge-scaled proportional   | Inline in strategy                 | Live signals |
| Arbitrage              | Fixed margin-scaled        | Inline in strategy                 | Live signals |
| Backtest research      | Any of the four V2 stakers | `betting_strategies.py`            | Backtesting  |

Typical production fractions: ML strategies use 0.35-0.5 fractional Kelly; backtest defaults to 0.25.

## Implementation Notes

- All monetary calculations use `Decimal` to avoid floating-point rounding errors in stake computation.
- `compute_kelly_fraction()` returns zero (not negative) when expected value is negative -- the formula naturally
  produces f* <= 0 when `p * b < q`, and the function clamps to zero.
- `net_odds <= 0` (decimal odds <= 1.0) is rejected immediately -- these represent guaranteed losses.
- The `BankrollState` dataclass in `betting_strategies.py` tracks peak capital and max drawdown for backtest analytics.
  True ROI is computed as `(total_returned - total_staked) / total_staked * 100`, not equity-based.
- Venue-constrained Kelly uses `account_max_observed_stake` (the largest stake the venue has historically accepted for
  this account) as a practical ceiling, since many bookmakers silently reduce limits for winning accounts.

## Code Overlap and Architecture

Two code paths exist for historical reasons (the V2 stakers were ported from the archived `new-sports-batting-services`
repo):

1. **`kelly.py`** -- the live production path. `compute_kelly_fraction()` is the shared utility function (line 37:
   "Standalone function used by both KellyCriterionStrategy and MLSportsStrategy to avoid duplicating the Kelly
   formula"). `KellyCriterionStrategy` wraps it as a full strategy class for external model probabilities, adding
   portfolio, simultaneous, and venue-constrained variants.

2. **`betting_strategies.py`** -- the backtest research path. Four staking allocators (`FixedDollarV2`,
   `FixedPercentageV2`, `AdaptiveDailyV2`, `FractionalKellyV2`) all implement `BaseBettingStrategy.compute_stake()`.
   These are consumed by `backtest_engine.py` for strategy research and historical simulation.

The two paths are intentionally separate: live strategies need `SportsMarketDict` integration, venue constraints, and
signal metadata, while backtest stakers need `BankrollState` tracking and daily budget management. `FractionalKellyV2`
in `betting_strategies.py` re-implements the Kelly formula locally rather than calling `compute_kelly_fraction()`
because it operates on different input types (`edge_pct` + `odds` + `BankrollState` vs `model_prob` + `decimal_odds`).

## References

- **Kelly utility (shared):** `strategy-service/strategy_service/engine/strategies/sports/kelly.py`
- **Kelly strategy (standalone):** `kelly.py::KellyCriterionStrategy`
- **Backtest stakers:** `strategy-service/strategy_service/engine/strategies/sports/betting_strategies.py`
- **Backtest engine (consumer):** `strategy-service/strategy_service/engine/strategies/sports/backtest_engine.py`
- **ML sports (consumer):** `strategy-service/strategy_service/engine/strategies/sports/ml_sports_strategy.py`
- **Halftime ML (consumer):** `strategy-service/strategy_service/engine/strategies/sports/halftime_ml.py`
- **Value betting doc:** `codex/09-strategy/sports/value-betting.md`
