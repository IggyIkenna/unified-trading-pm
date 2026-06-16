---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# P&L Attribution — Cross-Cutting Concern

## Hard Rules

### 1. P&L attribution uses canonical factors only

Every P&L component maps to one of the canonical attribution factors. No ad-hoc "other" or "unclassified" buckets. If a
P&L component does not fit an existing factor, a new factor must be formally added to the canonical list.

### 2. Attribution is identical in live and batch

The `PnLCalculator` in strategy-service runs the same code path for live and batch modes. Live mode processes real-time
fills; batch mode replays historical fills. The attribution logic, factor decomposition, and output schema are
identical.

```
Live:  CanonicalFill (from execution-service) → PnLCalculator → PnLAttribution
Batch: CanonicalFill (from CSV replay)        → PnLCalculator → PnLAttribution
```

### 3. T+1 reconciliation is mandatory

Every strategy instance runs a T+1 batch reconciliation that recomputes yesterday's P&L from settlement data. The batch
result is the official P&L. Live P&L is indicative only — it may differ due to delayed fills, funding settlements, or
price corrections.

```
Live P&L (indicative):
  Updated on every fill and funding event
  Used for: real-time dashboards, risk monitoring, position sizing

Batch P&L (official):
  Computed at T+1 from settled data
  Used for: reporting, performance measurement, fee calculation
  OVERRIDES live P&L where they differ
```

## Canonical Attribution Factors

### Factor Hierarchy

```
Total P&L
├── DELTA          — P&L from directional price movement
├── FUNDING        — P&L from perpetual funding rate payments
├── BASIS          — P&L from basis convergence/divergence
├── CARRY          — P&L from yield / interest rate differential
├── GREEKS         — P&L from options sensitivities (gamma, vega, theta)
├── FEES           — P&L impact from transaction fees (exchange, gas, protocol)
├── SLIPPAGE       — P&L impact from execution vs benchmark price
├── SETTLEMENT     — P&L from contract expiry / sports event settlement
├── LIQUIDATION    — P&L impact from liquidation events (penalty, bonus)
├── REBATE         — P&L from maker rebates, referral bonuses
├── FX             — P&L from currency conversion (non-USD denominated venues)
└── RESIDUAL       — Unexplained P&L (must be < 1% of total, else investigate)
```

### Factor Definitions

| Factor      | Computation                                                    | Sign Convention                 |
| ----------- | -------------------------------------------------------------- | ------------------------------- |
| DELTA       | `sum(position_qty × (price_now - price_prev))` per instrument  | Positive = profitable direction |
| FUNDING     | `sum(position_qty × funding_rate × funding_interval)` per perp | Positive = received funding     |
| BASIS       | `spot_pnl + perp_pnl` for basis trades (captures convergence)  | Positive = basis moved in favor |
| CARRY       | `sum(collateral × apy × time_fraction)` for lending/staking    | Positive = yield earned         |
| GREEKS      | `delta_pnl + gamma_pnl + vega_pnl + theta_pnl` for options     | Per-greek decomposition         |
| FEES        | `-sum(fee_amount)` for all trades in period                    | Always negative (cost)          |
| SLIPPAGE    | `sum(fill_price - benchmark_price) × quantity × side_sign`     | Negative = worse than benchmark |
| SETTLEMENT  | `settlement_value - mark_value` at expiry/event resolution     | Positive = favorable settlement |
| LIQUIDATION | `liquidation_penalty` or `liquidation_bonus`                   | Negative for penalized party    |
| REBATE      | `sum(rebate_amount)` for maker fills and referral credits      | Always positive (income)        |
| FX          | `pnl_local × (fx_rate_now - fx_rate_trade)` for non-USD venues | Positive = favorable FX move    |
| RESIDUAL    | `total_pnl - sum(all_attributed_factors)`                      | Should be near zero             |

## Strategy-Specific Factor Profiles

### Per-Archetype Factor Relevance

| Archetype             | DELTA | FUNDING | BASIS | CARRY | GREEKS | FEES | SLIPPAGE | SETTLE | Notes                     |
| --------------------- | ----- | ------- | ----- | ----- | ------ | ---- | -------- | ------ | ------------------------- |
| Delta-One Basis       | Low   | High    | High  | Low   | --     | Med  | Med      | Low    | Funding is primary alpha  |
| DeFi Recursive Basis  | Low   | Med     | High  | High  | --     | High | Med      | --     | Gas fees dominate costs   |
| Statistical Arb       | High  | Low     | --    | --    | --     | High | High     | --     | Slippage is critical      |
| Market Making         | Low   | Low     | --    | --    | --     | Med  | High     | --     | Spread capture + rebates  |
| Momentum              | High  | Low     | --    | --    | --     | Med  | Med      | --     | Delta is the whole play   |
| Mean Reversion        | High  | Low     | --    | --    | --     | Med  | Med      | --     | Delta from mean return    |
| Sports Arbitrage      | --    | --      | --    | --    | --     | High | --       | High   | Settlement is binary      |
| Calendar Spread       | Low   | High    | High  | Low   | Low    | Med  | Med      | Med    | Basis term structure      |
| Volatility Arb        | Low   | --      | --    | --    | High   | Med  | Med      | Med    | Greeks are the whole play |
| Funding Rate Harvest  | Low   | High    | Low   | --    | --     | Low  | Low      | --     | Pure funding collection   |
| Liquidation Sniper    | High  | --      | --    | --    | --     | High | High     | --     | Gas-competitive entry     |
| Cross-Exchange Arb    | Low   | Low     | --    | --    | --     | Med  | High     | --     | Spread capture            |
| Prediction Contrarian | --    | --      | --    | --    | --     | Med  | Med      | High   | Binary settlement         |
| Yield Optimization    | Low   | --      | --    | High  | --     | Med  | Low      | --     | Carry is the whole play   |

`--` = not applicable for this archetype.

## Attribution Computation

### Per-Fill Attribution

Every `CanonicalFill` triggers an attribution update:

```python
# strategy-service/strategy_service/pnl_calculator.py (simplified)
def attribute_fill(fill: CanonicalFill, position: Position, config: StrategyConfig) -> PnLAttribution:
    factors = {}

    # DELTA: price movement since last mark
    factors["DELTA"] = position.quantity * (fill.price - position.avg_entry_price)

    # FEES: exchange fee on this fill
    factors["FEES"] = -fill.fee_amount

    # SLIPPAGE: fill vs benchmark
    if fill.benchmark_price:
        side_sign = Decimal("1") if fill.side == "BUY" else Decimal("-1")
        factors["SLIPPAGE"] = (fill.price - fill.benchmark_price) * fill.quantity * side_sign

    # REBATE: if maker fill and venue offers rebate
    if fill.is_maker and fill.rebate_amount:
        factors["REBATE"] = fill.rebate_amount

    return PnLAttribution(
        strategy_id=config.strategy_id,
        client_id=config.client_id,
        instrument_id=fill.instrument_id,
        timestamp=fill.timestamp,
        factors=factors,
        total_pnl=sum(factors.values()),
    )
```

### Periodic Attribution (Funding, Carry)

Some factors accrue over time, not on fills:

```python
# Funding rate attribution (every funding interval, typically 8H)
def attribute_funding(position: Position, funding_rate: Decimal, interval_hours: int) -> PnLAttribution:
    funding_pnl = position.quantity * position.notional * funding_rate
    # Long pays positive funding, short receives
    if position.side == "LONG":
        funding_pnl = -funding_pnl

    return PnLAttribution(
        factors={"FUNDING": funding_pnl},
        total_pnl=funding_pnl,
    )

# Carry attribution (daily for lending/staking)
def attribute_carry(collateral: Decimal, apy: Decimal, days: int = 1) -> PnLAttribution:
    carry_pnl = collateral * apy * Decimal(days) / Decimal("365")
    return PnLAttribution(
        factors={"CARRY": carry_pnl},
        total_pnl=carry_pnl,
    )
```

### Options Greeks Attribution

For options strategies, P&L is decomposed into greek components:

```
Delta P&L    = delta × underlying_price_change
Gamma P&L    = 0.5 × gamma × underlying_price_change^2
Vega P&L     = vega × implied_vol_change
Theta P&L    = theta × time_decay_days
Rho P&L      = rho × interest_rate_change

Total Greeks P&L = sum(delta_pnl, gamma_pnl, vega_pnl, theta_pnl, rho_pnl)
```

### Settlement Attribution (Sports / Prediction)

Sports and prediction markets settle as binary outcomes:

```python
def attribute_settlement(position: Position, outcome: str, settlement_price: Decimal) -> PnLAttribution:
    # settlement_price: 1.0 if outcome matches bet, 0.0 if not
    settlement_pnl = position.quantity * (settlement_price - position.avg_entry_price)

    return PnLAttribution(
        factors={"SETTLEMENT": settlement_pnl},
        total_pnl=settlement_pnl,
    )
```

## T+1 Attribution Pipeline

### Batch Reconciliation Flow

```
T+1 Batch (runs daily at 02:00):
  1. LOAD: Read all fills for T from execution-service GCS archive
  2. LOAD: Read all funding payments for T from venue APIs (UTEI)
  3. LOAD: Read all settlements for T (expired contracts, sports results)
  4. LOAD: Read opening positions for T from PBMS snapshot
  5. LOAD: Read closing positions for T from PBMS snapshot
  6. COMPUTE: Per-fill attribution (DELTA, FEES, SLIPPAGE, REBATE)
  7. COMPUTE: Periodic attribution (FUNDING, CARRY)
  8. COMPUTE: Settlement attribution (SETTLEMENT, LIQUIDATION)
  9. COMPUTE: FX attribution (for non-USD denominated venues)
  10. COMPUTE: Residual = total_pnl - sum(all_factors)
  11. VALIDATE: |RESIDUAL| < 0.01 × |total_pnl| (1% tolerance)
  12. WRITE: Attribution breakdown to GCS
  13. WRITE: Summary to BigQuery for reporting
```

### Reconciliation Checks

| Check                         | Tolerance | Action if Failed                   |
| ----------------------------- | --------- | ---------------------------------- |
| Residual < 1% of total        | 1%        | WARN — investigate unexplained P&L |
| Residual < 5% of total        | 5%        | CRITICAL — manual reconciliation   |
| Position balance matches PBMS | Exact     | CRITICAL — position break          |
| Fill count matches venue      | Exact     | CRITICAL — missing fills           |
| Funding payments match venue  | 0.01%     | WARN — rounding differences        |

### GCS Attribution Output

```
gs://pnl/{strategy_id}/{client_id}/{date}/
  ├── attribution_summary.json       # factor totals for the day
  ├── attribution_detail.parquet     # per-fill and per-event attribution
  ├── positions_opening.json         # SOD positions
  ├── positions_closing.json         # EOD positions
  └── reconciliation_report.json     # checks passed/failed
```

## Reporting Dimensions

### Attribution Rollups

P&L attribution can be sliced across multiple dimensions:

```
DIMENSION HIERARCHY:

By Organization:
  org_total
    └── client_1
          ├── strategy_A (instance 1)
          ├── strategy_A (instance 2, different config)
          └── strategy_B
    └── client_2
          └── strategy_A

By Strategy:
  strategy_A_total
    ├── client_1 (config v1)
    └── client_2 (config v2)

By Venue:
  binance_total
    ├── client_1 / strategy_A
    └── client_2 / strategy_A

By Asset Class:
  cefi_total
    ├── all CeFi strategies
  defi_total
    ├── all DeFi strategies
  tradfi_total / sports_total / prediction_total

By Factor:
  funding_total (across all strategies, clients, venues)
  delta_total
  fees_total
  ...
```

### Reporting Periods

| Period    | Computation                   | Storage                                |
| --------- | ----------------------------- | -------------------------------------- |
| Daily     | T+1 batch attribution         | `gs://pnl/{strategy}/{client}/{date}/` |
| Weekly    | Sum of daily attributions     | Computed on-demand from daily data     |
| Monthly   | Sum of daily attributions     | Computed on-demand from daily data     |
| YTD       | Sum of daily attributions     | Computed on-demand from daily data     |
| Inception | Sum of all daily attributions | Computed on-demand from daily data     |

### Key Performance Metrics (Derived from Attribution)

| Metric               | Computation                                            | Granularity           |
| -------------------- | ------------------------------------------------------ | --------------------- |
| Gross P&L            | `sum(all factors)`                                     | Daily, per strategy   |
| Net P&L              | `gross_pnl + FEES + SLIPPAGE`                          | Daily, per strategy   |
| Sharpe Ratio         | `mean(daily_returns) / std(daily_returns) × sqrt(365)` | Rolling 30/90/365 day |
| Max Drawdown         | `max peak-to-trough decline`                           | Since inception       |
| Win Rate             | `count(profitable_days) / count(all_days)`             | Rolling 30 day        |
| Avg Win / Avg Loss   | `mean(positive_days) / abs(mean(negative_days))`       | Rolling 30 day        |
| Cost Ratio           | `abs(FEES + SLIPPAGE) / abs(gross_pnl)`                | Daily, per strategy   |
| Funding Contribution | `FUNDING / gross_pnl`                                  | Per funding strategy  |
| Alpha vs Benchmark   | `strategy_return - benchmark_return`                   | Daily                 |

## Live vs Batch Reconciliation

### Discrepancy Sources

| Source                 | Live P&L Impact    | Batch P&L Impact    | Resolution                  |
| ---------------------- | ------------------ | ------------------- | --------------------------- |
| Delayed fill report    | Missing fill       | Included            | Batch is correct            |
| Venue price correction | Original price     | Corrected price     | Batch is correct            |
| Funding rate revision  | Estimated rate     | Actual settled rate | Batch is correct            |
| Gas price fluctuation  | Estimated gas      | Actual gas used     | Batch is correct            |
| FX rate timing         | Spot rate at fill  | Settlement rate     | Batch is correct            |
| Position break         | Incorrect position | Reconciled position | CRITICAL — investigate root |

### Reconciliation Alert

```
If |live_pnl - batch_pnl| > threshold:
  log_event(PNL_RECONCILIATION_BREAK, {
    strategy_id, client_id, date,
    live_pnl, batch_pnl,
    difference, difference_pct,
    largest_discrepancy_factor
  })
  → alerting-service → Telegram + email
  → manual investigation required
```

Threshold: 1% of gross P&L or $1,000, whichever is larger.

## PnLAttribution Schema

```python
# unified_api_contracts.internal (simplified)
@dataclass
class PnLAttribution:
    strategy_id: str
    client_id: str
    instrument_id: str
    timestamp: datetime
    period: str                        # "fill", "funding_8h", "daily", "settlement"
    factors: dict[str, Decimal]        # factor_name → P&L amount
    total_pnl: Decimal                 # sum of all factors
    metadata: PnLMetadata              # fill_id, venue, benchmark_price, etc.
```

## Share Class P&L

P&L is converted from USD to the client's share class base currency. The FX attribution factor tracks the conversion
difference, keeping trading P&L separate from currency exposure.

```
# ETH share class example
pnl_eth = pnl_usd / eth_price_at_settlement

# FX attribution
fx_factor = pnl_usd * (1/eth_price_settlement - 1/eth_price_trade)
trading_factor = pnl_usd / eth_price_trade
total_pnl_eth = trading_factor + fx_factor  # = pnl_usd / eth_price_settlement
```

For `USDT` share class, no FX conversion applies (P&L is already in USD). For `ETH` and `BTC` share classes, every
attribution factor is converted to the base currency at settlement time, and the FX component is separated as its own
factor for transparency.

This ensures clients see P&L in their chosen denomination while the system maintains USD as the internal accounting
currency. The FX factor appears in attribution reports alongside DELTA, FUNDING, CARRY, etc.

### Supported Share Classes

| Share Class | Base Asset | FX Rate Feature (MDPS) | Delta Target             |
| ----------- | ---------- | ---------------------- | ------------------------ |
| `USDT`      | USD / USDT | n/a (rate = 1.0)       | 0 (market neutral)       |
| `ETH`       | ETH        | `fx_rate_eth_usd`      | equity_in_eth (NOT zero) |
| `BTC`       | BTC        | `fx_rate_btc_usd`      | equity_in_btc (NOT zero) |

### FX Rate Source

FX rates (`fx_rate_eth_usd`, `fx_rate_btc_usd`) are produced by `DefiFxRateAdapter` in MDPS. The adapter reads spot tick
data from CeFi venues, aggregates to candle close, and applies LOCF. These features are consumed by strategy-service,
pnl-attribution-service, and risk-and-exposure-service.

### P&L Conversion in Settlement Service

`strategy-service/strategy_service/engine/core/settlement_service.py`
`convert_settlement_to_share_class(pnl, share_class, fx_rates)` converts a USD P&L dict.

For `USDT`: returns all values unchanged with `_share_class` suffixed keys equal to USD values. For `ETH/BTC`: divides
each value by the FX rate (ETH at $3500 → 1 ETH = 1/3500 USD → divide).

Output keys:

- `{factor}_usd` — original USD P&L (unchanged)
- `{factor}_share_class` — same P&L in share class denomination
- `total_pnl_usd`, `total_pnl_share_class`
- `fx_rate_used` — the FX rate applied at settlement

### ETH/BTC Share Class: Delta Target is NOT Zero

For ETH share class, the risk target is NOT zero ETH delta. A portfolio targeting ETH denomination must hold
equity_in_eth worth of ETH exposure. Zero ETH delta would mean underperforming ETH appreciation.

`evaluate_base_currency_drift()` in risk_metrics.py enforces this:

- Target ETH delta = account_equity / fx_rate_eth_usd
- Drift = |actual - target| / target × 100%
- WARNING at >2%, CRITICAL at >5%

When drift exceeds threshold, strategy emits a SWAP instruction to buy ETH back toward target.

See [cross-cutting/share-classes.md](../cross-cutting/share-classes.md) for the full share class specification and
[codex/04-architecture/defi-risk-monitoring.md](../../04-architecture/defi-risk-monitoring.md) for monitoring
thresholds.

## Implementation: pnl-attribution-service `compute_pnl_breakdown()`

The `breakdown.py` function `compute_pnl_breakdown()` is the core computation. It accepts all 12 canonical factors as
parameters and produces a `PnLBreakdown` result:

**Implemented factor parameters:**

| Parameter                 | Maps to Factor | Notes                                                                                                                            |
| ------------------------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `realized_pnl`            | REALIZED       | Closed position P&L                                                                                                              |
| `unrealized_pnl`          | UNREALIZED     | Open position mark-to-market                                                                                                     |
| `delta_pnl`               | DELTA          | Directional price movement                                                                                                       |
| `basis_pnl`               | BASIS          | Basis convergence/divergence                                                                                                     |
| `funding_rate_pnl`        | FUNDING        | Perpetual funding rate payments                                                                                                  |
| `interest_rate_pnl`       | INTEREST       | Lending/borrowing interest differential                                                                                          |
| `greeks_exposure`         | GREEKS         | Options decomposition: delta/gamma/theta/vega computed from `GreeksExposure` (delta x price, 0.5 x gamma x price^2, theta, vega) |
| `gas_cost_usd`            | GAS            | DeFi transaction gas costs (subtracted from attributed total)                                                                    |
| `slippage_bps`            | SLIPPAGE       | Execution vs benchmark price difference                                                                                          |
| `residual_pnl`            | RESIDUAL       | `mark_to_market - attributed` (computed automatically)                                                                           |
| `share_class` + `fx_rate` | FX             | Share class conversion via `compute_share_class_pnl()`                                                                           |
| (via rewards)             | LST_YIELD      | LST ratio appreciation (weETH/ETH, stETH/ETH)                                                                                    |

**Share class conversion** (`compute_share_class_pnl()`): Converts USD P&L to share class base currency (ETH, BTC).
Returns `(share_class_pnl, fx_pnl, lst_yield_factor)`. The FX attribution isolates P&L from base currency movement. The
LST yield factor isolates P&L from LST ratio appreciation (e.g., weETH/ETH went from 1.050 to 1.055).

**Aave liquidity index:** For DeFi lending positions, P&L accrues via the Aave liquidity index (which tracks cumulative
interest). The `compute_share_class_pnl()` function handles the `lst_ratio` / `lst_ratio_start` parameters to attribute
yield from LST ratio changes separately from price movement.

## Reward P&L Factors

Four additional attribution factors for DeFi staking reward streams. These extend the canonical factor hierarchy for
strategies that involve liquid staking tokens (weETH, wstETH) and their associated reward protocols.

| Factor                         | What It Captures                                         | Settlement Type   |
| ------------------------------ | -------------------------------------------------------- | ----------------- |
| `PNL_FACTOR_STAKING_YIELD`     | Base staking APY contribution (weETH/wstETH rate growth) | `LST_YIELD`       |
| `PNL_FACTOR_RESTAKING_REWARD`  | EIGEN restaking rewards (weekly from EigenLayer)         | `SEASONAL_WEEKLY` |
| `PNL_FACTOR_SEASONAL_REWARD`   | ETHFI quarterly airdrops (from EtherFi protocol)         | `SEASONAL_WEEKLY` |
| `PNL_FACTOR_REWARD_UNREALISED` | Accrued but unclaimed rewards (mark-to-market estimate)  | `MARK_TO_MARKET`  |

**Lifecycle:**

1. Rewards accrue in the protocol. Tracked as `PNL_FACTOR_REWARD_UNREALISED` (unrealized, estimated from expected
   distribution schedule).
2. On-chain claim transaction converts unrealized to realized. `PNL_FACTOR_REWARD_UNREALISED` decreases,
   `PNL_FACTOR_RESTAKING_REWARD` or `PNL_FACTOR_SEASONAL_REWARD` increases by the claimed amount.
3. If reward tokens are sold (via `SELL_REWARD` operation), the realized proceeds replace the token-denominated value
   with a USD-denominated value in the factor.

These factors are only active for strategies that use EtherFi or Lido staking. For Lido (`staking_protocol="LIDO"`),
only `PNL_FACTOR_STAKING_YIELD` applies -- there are no separate reward tokens.

## SSOT References

| Concept                | SSOT                       | Location                                                  |
| ---------------------- | -------------------------- | --------------------------------------------------------- |
| PnL calculator         | PnLCalculator              | `strategy-service/strategy_service/pnl_calculator.py`     |
| Settlement service     | SettlementService          | `strategy-service/strategy_service/settlement_service.py` |
| PnL attribution schema | UIC                        | `unified-api-contracts (internal/)/`                      |
| Fill schema            | CanonicalFill (UIC)        | `unified-api-contracts (internal/)/`                      |
| Funding rate features  | features-delta-one-service | `features-delta-one-service/`                             |
| Options greeks         | features-options-service   | `features-options-service/`                               |
| Cost factors           | See cost-modeling.md       | `codex/09-strategy/cross-cutting/cost-modeling.md`        |
| PnL storage            | GCS archives               | `gs://pnl/{strategy_id}/{client_id}/{date}/`              |
| Reporting UI           | trading-analytics-ui       | `trading-analytics-ui/`                                   |
| BigQuery reporting     | UCI DataSink               | `unified-cloud-interface/`                                |
