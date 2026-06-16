---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Margin & Health Factor Monitoring — Cross-Cutting Concern

## Hard Rules

### 1. Margin monitoring is continuous, not on-demand

The `position-balance-monitor` (PBMS) polls venue margin state on a fixed interval (default: 30 seconds for CeFi, every
block for DeFi). Strategies do NOT query margin directly — they receive margin/health data as pre-computed inputs from
`RiskMonitor` in strategy-service.

```
position-balance-monitor:
  Every 30s (CeFi) / every block (DeFi):
    → fetch margin state from venue API (UTEI) or on-chain (UDEI)
      → normalize to CanonicalMarginState
        → publish to pub/sub topic: margin-state-updates
          → risk-monitoring-service consumes
          → strategy-service RiskMonitor consumes
```

### 2. Health factor is the universal risk metric

Regardless of asset class, every position has a health-equivalent metric that measures distance to liquidation. The
system normalizes all venue-specific margin representations into a single `health_factor` value:

```
health_factor = collateral_value / required_margin

health_factor > 2.0  → HEALTHY (green)
health_factor 1.5–2.0 → ELEVATED (yellow) — strategy reduces exposure
health_factor 1.2–1.5 → WARNING (orange) — strategy pauses new entries
health_factor 1.0–1.2 → CRITICAL (red) — auto-deleverage triggered
health_factor < 1.0   → LIQUIDATION IMMINENT — emergency close all
```

### 3. Strategies never manage margin directly

Strategy-service receives health factor and liquidation distance from `RiskMonitor`. Strategy config declares
thresholds. The strategy's only job is to reduce exposure when health deteriorates — it does NOT interact with venue
margin APIs.

```
PROHIBITED:
  strategy-service  ←✗→  venue margin API
  strategy-service  ←✗→  UTEI.get_margin()

ALLOWED:
  strategy-service  ←✓→  RiskMonitor.get_health_factor()
  strategy-service  ←✓→  ExposureMonitor.get_exposure()
  strategy-service  ←✓→  StrategyConfig.min_health_factor
```

## CeFi Margin Models

### Cross Margin

All positions in the account share a single margin pool. Profit on one position offsets loss on another.

```
Cross Margin State:
  total_equity = wallet_balance + unrealized_pnl_all_positions
  total_maintenance_margin = sum(position_maintenance_margin for all positions)
  health_factor = total_equity / total_maintenance_margin

Example (Binance Futures cross margin):
  wallet_balance: $100,000
  Position A (ETH-PERP long): unrealized PnL +$5,000, maint margin $8,000
  Position B (BTC-PERP short): unrealized PnL -$3,000, maint margin $12,000

  total_equity = 100,000 + 5,000 + (-3,000) = $102,000
  total_maintenance_margin = 8,000 + 12,000 = $20,000
  health_factor = 102,000 / 20,000 = 5.10 (HEALTHY)
```

### Isolated Margin

Each position has its own margin allocation. Losses on one position cannot drain margin from others.

```
Isolated Margin State (per position):
  position_equity = isolated_margin + unrealized_pnl
  maintenance_margin = position_notional × maintenance_margin_rate
  health_factor = position_equity / maintenance_margin

Example (Deribit isolated):
  isolated_margin: $10,000
  position_notional: $50,000
  unrealized_pnl: -$4,000
  maintenance_margin_rate: 5%

  position_equity = 10,000 + (-4,000) = $6,000
  maintenance_margin = 50,000 × 0.05 = $2,500
  health_factor = 6,000 / 2,500 = 2.40 (HEALTHY)
```

### Venue-Specific Margin Parameters

| Venue       | Margin Mode      | Max Leverage | Maint Margin Rate | Liquidation Engine      |
| ----------- | ---------------- | ------------ | ----------------- | ----------------------- |
| Binance     | Cross / Isolated | 125x (BTC)   | 0.4%–50%          | Insurance fund + ADL    |
| Deribit     | Cross / Isolated | 100x (BTC)   | 0.5%–30%          | Incremental liquidation |
| Hyperliquid | Cross            | 50x          | 1%–20%            | On-chain liquidation    |
| OKX         | Cross / Isolated | 125x (BTC)   | 0.4%–50%          | Insurance fund + ADL    |
| Bybit       | Cross / Isolated | 100x (BTC)   | 0.5%–50%          | Insurance fund + ADL    |

**Maintenance margin rate varies by position size tier.** Larger positions have higher maintenance requirements. The
`position-balance-monitor` fetches the applicable tier from the venue and applies it to the health calculation.

## DeFi Health Factor (Aave / Lending Protocols)

### Aave Health Factor

Aave defines health factor as:

```
health_factor = (total_collateral_eth × liquidation_threshold) / total_debt_eth

Where:
  total_collateral_eth = sum(collateral_amount × collateral_price × LTV_weight)
  total_debt_eth = sum(debt_amount × debt_price)
  liquidation_threshold = weighted average of per-asset thresholds
```

### Aave Asset Parameters

| Asset  | LTV (max borrow) | Liquidation Threshold | Liquidation Penalty |
| ------ | ---------------- | --------------------- | ------------------- |
| ETH    | 80%              | 82.5%                 | 5%                  |
| WBTC   | 70%              | 75%                   | 10%                 |
| USDC   | 80%              | 85%                   | 4%                  |
| USDT   | 75%              | 80%                   | 5%                  |
| DAI    | 75%              | 80%                   | 4%                  |
| WSTETH | 69%              | 80%                   | 7%                  |

### Aave V3 E-Mode (Efficiency Mode)

When collateral and debt are in the same asset category, Aave V3 enables E-Mode with significantly elevated risk
parameters. This dramatically changes leverage calculations for strategies like recursive staked basis.

**SSOT:** `unified_api_contracts.registry.defi_reserve_params.AAVE_V3_EMODE_CATEGORIES`

| E-Mode Category | Assets                     | LTV | Liq Threshold | Liq Bonus |
| --------------- | -------------------------- | --- | ------------- | --------- |
| ETH_CORRELATED  | WETH, weETH, wstETH, cbETH | 93% | 95%           | 1%        |
| STABLECOIN      | USDC, USDT, DAI            | 97% | 97.5%         | 1%        |

**Impact on recursive staked basis (weETH collateral + WETH debt = ETH_CORRELATED):**

```
Standard mode: LTV 72.5%, liq_threshold 77.5%
  max_leverage = 1/(1 - 0.725) = 3.6x (raw), ~3.16x (with 2% depeg tolerance)

E-Mode:       LTV 93%, liq_threshold 95%
  max_leverage = 1/(1 - 0.93) = 14.3x (raw), ~13.6x (with 2% depeg tolerance)
```

**Depeg tolerance sizing with E-Mode:** `max_lev = liq_threshold / (1 - liq_threshold + depeg_tolerance)`

| Depeg Tolerance | Standard (0.775 liq) | E-Mode (0.95 liq) |
| --------------- | -------------------- | ----------------- |
| 2%              | 3.16x                | 13.57x            |
| 3%              | 3.04x                | 11.88x            |
| 5%              | 2.82x                | 9.50x             |

**Detection:** `get_emode_params(collateral_asset, debt_asset)` returns `EModeCategory | None`. Strategy
`_resolve_emode_params()` auto-detects from instrument IDs. Dynamic features from risk-and-exposure-service override
base E-Mode values when present.

### DeFi Health Factor Monitoring

```
UDEI connector.get_health_factor(wallet_address):
  → call Aave Pool.getUserAccountData(wallet_address)
    → returns (totalCollateralBase, totalDebtBase, ..., healthFactor)
      → normalize to Decimal with 18 decimals
        → publish as CanonicalMarginState

Monitoring interval:
  - Every new block (12s on L1, 250ms on Arbitrum)
  - On every position change (borrow, repay, supply, withdraw)
```

### Recursive Leverage Health

DeFi recursive basis strategies (supply ETH → borrow USDT → swap to ETH → supply again) create amplified leverage. Each
loop degrades the health factor:

```
Loop 0: Supply 100 ETH ($350K), Borrow $280K USDT (80% LTV)
  HF = (350,000 × 0.825) / 280,000 = 1.031

Loop 1: Supply +80 ETH ($280K), Borrow +$224K USDT
  HF = ((350,000 + 280,000) × 0.825) / (280,000 + 224,000) = 1.031 (constant)

Effective leverage = 1 / (1 - LTV) = 1 / 0.20 = 5x
```

**Rule:** Recursive strategies MUST declare `max_recursion_depth` and `min_health_factor_at_max_depth` in config. The
strategy stops looping when health factor approaches the minimum.

## TradFi Portfolio Margin

### SPAN / Risk-Based Margin

TradFi uses scenario-based margin (SPAN for futures, portfolio margin for equities+options):

```
Portfolio margin calculation:
  1. Generate 16 theoretical scenarios (price ±up/down × volatility ±up/down)
  2. Calculate portfolio P&L under each scenario
  3. Margin requirement = worst-case loss across all scenarios + concentration charge

Normalized health_factor:
  health_factor = net_liquidating_value / portfolio_margin_requirement
```

### Margin Call Workflow

TradFi margin calls follow a formal timeline:

| Event              | Timeline     | Action                                   |
| ------------------ | ------------ | ---------------------------------------- |
| Margin warning     | Intraday     | Alert — deposit cash or reduce positions |
| Margin call issued | T+0 close    | Must meet by T+1 open                    |
| Forced liquidation | T+1 if unmet | Broker liquidates sufficient positions   |

The system emits `MARGIN_CALL` events via unified-trading-library when TradFi margin drops below the house requirement.

## Position-Balance-Monitor Integration

### PBMS Architecture

```
position-balance-monitor:
  ├── BalancePoller
  │     └── per-venue balance polling (UTEI.get_balances())
  ├── PositionPoller
  │     └── per-venue position polling (UTEI.get_positions())
  ├── MarginPoller
  │     └── per-venue margin polling (UTEI.get_margin_state())
  ├── DeFiHealthPoller
  │     └── per-chain health factor polling (UDEI.get_health_factor())
  └── Publisher
        └── normalizes all to CanonicalMarginState → pub/sub
```

### CanonicalMarginState Schema

```python
# unified_api_contracts.internal
@dataclass
class CanonicalMarginState:
    venue: str
    client_id: str
    margin_mode: str                    # "CROSS" | "ISOLATED" | "PORTFOLIO"
    total_equity: Decimal
    total_maintenance_margin: Decimal
    health_factor: Decimal
    liquidation_distance_pct: Decimal   # (equity - maint) / equity × 100
    free_margin: Decimal                # equity - used_margin
    positions: list[PositionMargin]     # per-position breakdown
    timestamp: datetime
```

## Risk-Monitoring-Service Alerts

### Alert Thresholds (Configurable per Client)

```yaml
# GCS: gs://config/risk/{client_id}/margin_thresholds.yaml
margin_alerts:
  healthy:
    health_factor_min: 2.0
    action: none
  elevated:
    health_factor_min: 1.5
    action: warn
    channels: [telegram, email]
  warning:
    health_factor_min: 1.2
    action: reduce_exposure
    channels: [telegram, email, pager]
    auto_deleverage: false
  critical:
    health_factor_min: 1.05
    action: auto_deleverage
    channels: [telegram, email, pager]
    auto_deleverage: true
    target_health_factor: 2.0
```

### Alert Event Flow

```
position-balance-monitor publishes CanonicalMarginState
  → risk-monitoring-service evaluates against thresholds
    → if threshold breached:
        1. log_event(MARGIN_THRESHOLD_BREACHED, severity, details)
        2. alerting-service picks up event → sends to configured channels
        3. if auto_deleverage=true:
             → emit DELEVERAGE_REQUIRED event
               → strategy-service RiskMonitor receives
                 → strategy generates deleverage StrategyInstruction
                   → execution-service closes positions to restore health
```

## Auto-Deleverage Triggers

### Deleverage Decision Logic

```python
# strategy-service RiskMonitor (simplified)
def check_margin_health(margin_state: CanonicalMarginState, config: StrategyConfig) -> StrategyInstruction | None:
    if margin_state.health_factor >= config.min_health_factor:
        return None  # healthy, no action

    # Calculate how much exposure to reduce
    target_hf = config.target_health_factor_on_deleverage  # e.g., 2.0
    current_hf = margin_state.health_factor

    # Reduce positions proportionally until target HF reached
    reduction_pct = Decimal("1") - (current_hf / target_hf)
    reduction_pct = min(reduction_pct, Decimal("1"))  # cap at 100%

    return StrategyInstruction(
        operation=OperationType.DELEVERAGE,
        reduction_pct=reduction_pct,
        urgency="critical",
        reason=f"health_factor={current_hf}, target={target_hf}",
    )
```

### Deleverage Priority Order

When multiple positions exist, deleverage in this order:

1. **Largest loss position first** — stop the bleeding
2. **Most leveraged position** — highest margin consumption
3. **Most liquid position** — easiest to close without market impact
4. **Newest position** — least conviction (entered most recently)

The priority is configurable per client in the risk config.

### DeFi Auto-Deleverage (Recursive Unwind)

For recursive basis strategies, deleverage is the reverse of the entry loop:

```
Deleverage loop (reverse of entry):
  1. Withdraw partial collateral from Aave
  2. Swap collateral to debt asset
  3. Repay partial debt
  4. Repeat until health_factor >= target

Each loop:
  - Monitor health factor after each step
  - If health factor drops below 1.05 during unwind: emergency full close
  - Gas cost of unwind is a factor — multiple small unwinds cost more gas
```

## Liquidation Distance Tracking

### Liquidation Distance Metric

```
liquidation_distance_pct = (current_price - liquidation_price) / current_price × 100

Example:
  ETH-PERP long at $3,500, liquidation at $3,150
  distance = (3,500 - 3,150) / 3,500 × 100 = 10%
```

### Distance Dashboard

The `risk-monitoring-ui` displays liquidation distance for all active positions:

| Position        | Entry Price | Liquidation Price | Current Price | Distance | Health Factor |
| --------------- | ----------- | ----------------- | ------------- | -------- | ------------- |
| ETH-PERP Long   | $3,500      | $3,150            | $3,450        | 8.7%     | 1.87          |
| BTC-PERP Short  | $95,000     | $102,000          | $96,500       | 5.4%     | 1.54          |
| Aave ETH Supply | $3,500      | $3,030            | $3,450        | 12.2%    | 2.22          |

### Liquidation Price Calculation

```
CeFi (isolated):
  liq_price_long = entry_price × (1 - (initial_margin - maintenance_margin) / position_size)
  liq_price_short = entry_price × (1 + (initial_margin - maintenance_margin) / position_size)

DeFi (Aave):
  liq_price = (total_debt × 1.0) / (collateral_amount × liquidation_threshold)
  (simplified — actual calculation includes multiple collateral/debt assets)
```

## Cross-Asset Margin Interactions

### Correlation Risk

When a client holds positions across multiple asset classes, margin health on one venue can affect the entire portfolio:

```
Scenario:
  CeFi: ETH-PERP long on Binance (cross margin)
  DeFi: ETH supplied as collateral on Aave
  Both positions are long ETH exposure

If ETH drops 20%:
  Binance: margin equity drops, health_factor decreases
  Aave: collateral value drops, health_factor decreases
  BOTH positions deteriorate simultaneously — correlated drawdown
```

**Rule:** `risk-monitoring-service` aggregates health factors across ALL venues for a client and calculates a
`portfolio_health_factor` that accounts for correlated risk. A client can be HEALTHY on each individual venue but
ELEVATED at the portfolio level due to concentrated directional exposure.

### Portfolio Health Factor

```
portfolio_health_factor = sum(venue_equity) / sum(venue_maintenance_margin)

Adjusted for correlation:
  correlation_adjusted_margin = base_margin × (1 + correlation_surcharge)
  correlation_surcharge = 0.10 × count_of_same_direction_positions_across_venues
```

## DeFi Risk Dimensions

The risk-and-exposure-service tracks 4 DeFi-specific risk dimensions. Each dimension has tiered severity thresholds and
corresponding automated actions.

### 1. Health Factor

On-chain health factor from Aave V3 (`Pool.getUserAccountData`). Applies to any strategy with Aave debt positions
(recursive staked basis, leveraged lending).

| Health Factor | Severity  | Action                                                          |
| ------------- | --------- | --------------------------------------------------------------- |
| HF > 1.5      | NORMAL    | No action. Strategy operates normally.                          |
| HF 1.3 - 1.5  | WARNING   | Log alert. Increase monitoring frequency. Reduce new entries.   |
| HF 1.1 - 1.3  | CRITICAL  | Deleverage 20% via atomic bundle. Alert sent to client.         |
| HF < 1.1      | EMERGENCY | Full emergency deleverage. Atomic unwind of all Aave positions. |

### 2. Oracle Depeg

Protocol oracle price (Chainlink via Aave) vs market price (aggregated CEX from market-tick-data-service). Applies to
all DeFi strategies with on-chain positions.

| Divergence (oracle vs market) | Severity  | Action                                                       |
| ----------------------------- | --------- | ------------------------------------------------------------ |
| < 1%                          | NORMAL    | No action. Expected noise.                                   |
| 1% - 2%                       | WARNING   | Log alert. Increase monitoring frequency to every 5 minutes. |
| 2% - 3%                       | CRITICAL  | Reduce position by 50%. Alert sent to client.                |
| > 3%                          | EMERGENCY | Full withdrawal. Oracle may be stale or manipulated.         |

### 3. Borrow-Staking Spread

Net spread between staking APY and borrow APY, multiplied by leverage. Applies to recursive staked basis and any
strategy combining staking with borrowing.

```
effective_spread = (staking_apy - borrow_apy) * leverage
```

| Condition                  | Severity | Action                                                                            |
| -------------------------- | -------- | --------------------------------------------------------------------------------- |
| `effective_spread > 0`     | NORMAL   | Strategy is profitable. Continue.                                                 |
| `effective_spread < 0`     | WARNING  | Leverage cost exceeds spread. Consider deleveraging.                              |
| `effective_spread < -0.5%` | CRITICAL | Borrow rate significantly exceeds staking yield. Exit staking or reduce leverage. |

### 4. Stablecoin Depeg

Peg deviation for stablecoin positions (USDC, USDT, DAI). Applies to lending strategies with stablecoin exposure.

| Depeg (vs $1.00) | Severity  | Action                                                               |
| ---------------- | --------- | -------------------------------------------------------------------- |
| < 0.5%           | NORMAL    | No action. Normal fluctuation.                                       |
| 0.5% - 1.0%      | WARNING   | Log alert. Prepare withdrawal instructions.                          |
| 1.0% - 5.0%      | CRITICAL  | Withdraw 50% of position. Monitor utilization for bank-run dynamics. |
| > 5.0%           | EMERGENCY | Full withdrawal. Accept slippage to exit before utilization cap.     |

## VaR Suite (risk-and-exposure-service)

The `var_calculator.py` implements a pure-function VaR suite with no I/O dependencies. All functions operate on
`list[float]` return series and produce negative floats representing loss thresholds.

### VaR Methods

| Method                    | Function                          | Min Observations | Description                                                                                                                                                                       |
| ------------------------- | --------------------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Historical VaR            | `historical_var()`                | 10               | Empirical percentile. Sorts returns, picks the (1-confidence) quantile.                                                                                                           |
| Parametric VaR            | `parametric_var()`                | 30               | Variance-covariance method assuming normal distribution. Uses sample mean + stdev + z-score.                                                                                      |
| Cornish-Fisher VaR        | `parametric_var_cornish_fisher()` | 30               | Adjusts normal quantile for observed skewness and excess kurtosis. More accurate for fat-tailed crypto/equity distributions. Based on JP Morgan RiskMetrics / Basel III guidance. |
| CVaR (Expected Shortfall) | `cvar()`                          | 10               | Expected loss given that loss exceeds VaR. Mean of returns in the (1-confidence) worst tail. Always >= VaR in absolute value.                                                     |
| Stress VaR                | `stress_var()`                    | 10               | Historical VaR multiplied by crisis-period multiplier.                                                                                                                            |
| Regime-Adjusted VaR       | `stressed_var()`                  | 30               | Cornish-Fisher VaR x scenario multiplier x regime multiplier.                                                                                                                     |

### Stress Scenario Multipliers

| Scenario                   | Multiplier | Basis                                     |
| -------------------------- | ---------- | ----------------------------------------- |
| GFC_2008                   | 3.5x       | S&P 500 peak-to-trough ~57% drawdown      |
| COVID_2020                 | 2.5x       | March 2020 30-day ~34% drawdown           |
| CRYPTO_BLACK_THURSDAY_2020 | 5.0x       | BTC/ETH single-day ~50% drop (2020-03-12) |

**Regime multiplier:** `set_regime_multiplier(factor, set_by)` allows risk managers to amplify all VaR figures during
known stress periods without redeployment. Factor must be >= 1.0 (never reduces VaR). Emits
`REGIME_STRESS_FACTOR_CHANGED` event for audit trail.

All VaR figures are scaled to the holding period via the square-root-of-time rule (Basel III):
`var_n_day = var_1_day * sqrt(n)`.

**SSOT:** `risk-and-exposure-service/risk_and_exposure_service/core/var_calculator.py`

## Pre-Trade Check Engine

The `PreTradeCheckEngine` is the last line of defense before order submission. All checks must pass for a trade to be
approved. The engine runs 7 checks in parallel:

| Check          | What It Validates                                                                                                                                    |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Market Hours   | TradFi venues: rejects orders on weekends and outside RTH (13:30-20:00 UTC). CeFi/DeFi: 24/7, always passes.                                         |
| Stale Price    | Rejects if any position's `last_updated` exceeds `stale_price_threshold_seconds`. Prevents executing against outdated mark prices.                   |
| Position Limit | `abs(new_qty) <= max_position_size` AND `new_position_value <= max_position_value`.                                                                  |
| Exposure Limit | Gross exposure, net exposure, single-instrument exposure, and venue exposure all within limits.                                                      |
| Capital Limit  | `new_capital <= max_capital_deployed` AND remaining capacity >= `min_cash_reserve`. Fail-safe: rejects if `max_capital_deployed` is not configured.  |
| Leverage Limit | Estimated leverage <= `max_leverage` AND margin ratio >= `min_margin_ratio`.                                                                         |
| VaR Limit      | Estimated parametric VaR (notional x volatility x z-score) <= `max_var_loss_pct` of gross exposure. Emits `PRE_TRADE_VAR_BREACH` event on rejection. |

Risk limits are loaded per-client from GCS via `RiskLimitsDomainClient`, falling back to service-level config defaults.

**Circuit Breaker + Kill Switch:** The execution-service owns the 3-state circuit breaker (CLOSED / OPEN / HALF-OPEN).
See [latency-profiles.md](latency-profiles.md) for circuit breaker thresholds per venue and DeFi-specific conditions
(gas price, RPC latency, tx reverts, block reorgs).

**SSOT:** `risk-and-exposure-service/risk_and_exposure_service/core/pre_trade_check_engine.py`

## Venue Collateral Matrix

The UAC registry is the SSOT for venue collateral acceptance. Each venue accepts specific tokens as margin or
collateral, which determines pre-processing requirements (wrapping, swapping) before position entry.

### DeFi Venues (Aave V3)

| Collateral | LTV   | Liquidation Threshold | Max Leverage | Notes                               |
| ---------- | ----- | --------------------- | ------------ | ----------------------------------- |
| weETH      | 72.5% | 75%                   | 3.6x         | EtherFi. Highest combined yield.    |
| wstETH     | 79.5% | 82%                   | 4.9x         | Lido. Higher LTV, no reward tokens. |
| WETH       | 82.5% | 85%                   | 5.7x         | No staking yield. Highest leverage. |
| USDC       | 80%   | 85%                   | 5.0x         | Stablecoin lending.                 |
| USDT       | 75%   | 80%                   | 4.0x         | Stablecoin lending.                 |

### CeFi Venues

| Venue       | Accepted Margin                        | Notes                                         |
| ----------- | -------------------------------------- | --------------------------------------------- |
| Hyperliquid | USDC only                              | USDT must be swapped to USDC before transfer. |
| Binance     | USDT (linear), BTC/ETH (coin-margined) | No swap needed for USDT linear perps.         |
| OKX         | USDT (linear), BTC/ETH (coin-margined) | No swap needed for USDT linear perps.         |
| Bybit       | USDT (linear), BTC/ETH (coin-margined) | No swap needed for USDT linear perps.         |
| Aster       | USDT (linear), BTC/ETH (coin-margined) | No swap needed for USDT linear perps.         |

The `CollateralValidationMixin` in strategy-service checks venue collateral requirements before instruction emission and
auto-emits SWAP or WRAP instructions when the current token form is incompatible.

## SSOT References

| Concept              | SSOT                       | Location                                                     |
| -------------------- | -------------------------- | ------------------------------------------------------------ |
| Margin state schema  | CanonicalMarginState (UIC) | `unified-api-contracts (internal/)/`                         |
| Position polling     | position-balance-monitor   | `position-balance-monitor/`                                  |
| Risk thresholds      | Risk config YAML           | `gs://config/risk/{client_id}/margin_thresholds.yaml`        |
| DeFi health factor   | UDEI connector             | `execution-service/`                                         |
| Aave asset params    | UAC testnet contracts      | `unified-config-interface/testnet_contracts.py`              |
| Risk monitoring      | risk-monitoring-service    | `risk-and-exposure-service/`                                 |
| Margin alerts        | alerting-service rules     | `alerting-service/alerting_service/rules/`                   |
| Strategy risk checks | RiskMonitor                | `strategy-service/strategy_service/monitors/risk_monitor.py` |
| Venue margin params  | UAC venue capabilities     | `unified-api-contracts/registry/venue_constants.py`          |
