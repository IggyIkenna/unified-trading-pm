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

The system emits `MARGIN_CALL` events via unified-events-interface when TradFi margin drops below the house requirement.

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
