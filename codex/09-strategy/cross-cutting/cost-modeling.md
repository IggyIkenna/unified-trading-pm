# Transaction Cost Modeling — Cross-Cutting Concern

## Hard Rules

### 1. Every strategy has a cost budget

No strategy runs without an explicit cost budget in its config. The cost budget defines the maximum acceptable cost as a
percentage of notional per trade. If expected cost exceeds the budget, the strategy must NOT emit a
`StrategyInstruction`.

```yaml
# strategy config excerpt
cost_budget:
  max_total_cost_bps: 15 # all-in cost ceiling (fees + slippage + gas)
  max_slippage_bps: 8 # slippage component ceiling
  warn_threshold_pct: 0.70 # alert at 70% of budget consumed
```

**Why:** A strategy that generates alpha of 5bps per trade but costs 8bps per trade is a losing strategy. Cost budgets
are the first filter — before risk limits, before position sizing.

### 2. Cost estimates are pre-trade, cost actuals are post-trade

```
PRE-TRADE (strategy-service):
  CostEstimator.estimate(instruction) → EstimatedCost
    → strategy checks: estimated_cost < cost_budget
      → YES: emit StrategyInstruction
      → NO: no-op (log reason: "cost budget exceeded")

POST-TRADE (execution-service):
  CostCalculator.calculate(fill) → ActualCost
    → written to PnL attribution as fee/slippage components
    → drift alert if actual > 1.5x estimated
```

### 3. Cost models are asset-class-specific

There is no universal cost model. Each asset class has fundamentally different cost structures:

| Asset Class | Primary Cost          | Secondary Cost      | Variable Cost         |
| ----------- | --------------------- | ------------------- | --------------------- |
| CeFi        | Exchange fees (bps)   | Withdrawal fees     | Slippage (order book) |
| DeFi        | Gas (ETH/gwei)        | Protocol fees (bps) | MEV / sandwich risk   |
| TradFi      | Commission (per unit) | Exchange fees       | Market impact         |
| Sports      | Overround / vig (%)   | None                | Line movement         |
| Prediction  | Platform fee (%)      | Settlement fee      | Spread cost           |

## CeFi Exchange Fee Model

### Fee Tiers

CeFi venues use maker/taker fee schedules based on 30-day trailing volume. The system tracks fee tiers per
`(venue, client_id)` pair.

| Venue       | Maker (bps) | Taker (bps) | Volume Tier    | Notes                       |
| ----------- | ----------- | ----------- | -------------- | --------------------------- |
| Binance     | 1.0–10.0    | 2.0–10.0    | 0–150M USD/30d | BNB discount: 25% off       |
| Deribit     | 0.0–2.0     | 3.0–5.0     | 0–100M USD/30d | Options: 3bps cap per lot   |
| Hyperliquid | 0.0–1.0     | 2.0–3.5     | 0–50M USD/30d  | Referral rebates applicable |
| OKX         | 0.8–8.0     | 1.0–10.0    | 0–100M USD/30d | Multi-tier VIP levels       |

**SSOT:** Fee schedules are stored in strategy config YAML per venue. The `CostEstimator` in strategy-service reads the
applicable tier for the client's volume level.

```yaml
# GCS: gs://config/{strategy_id}/clients/{client_id}.yaml
venue_fee_tiers:
  BINANCE:
    maker_bps: 2.0
    taker_bps: 4.0
    volume_tier: "VIP3"
  DERIBIT:
    maker_bps: 0.0
    taker_bps: 3.0
    volume_tier: "tier_2"
```

### Maker vs Taker Selection

Strategy controls whether to prefer maker or taker fills via `execution_style`:

| Style        | Fee Impact           | When Used                             |
| ------------ | -------------------- | ------------------------------------- |
| `passive`    | Maker fee (lower)    | No urgency, willing to wait for fill  |
| `aggressive` | Taker fee (higher)   | Urgent hedge, leader leg of multi-leg |
| `urgent`     | Taker fee + slippage | Stop-loss, liquidation avoidance      |

The cost estimator uses the `execution_style` hint from the strategy to select the correct fee tier for pre-trade
estimation.

## DeFi Gas Cost Model

### Gas Estimation Pipeline

```
1. features-onchain-service publishes gas_price_gwei as a feature
2. strategy-service CostEstimator reads gas feature
3. Estimate: gas_cost_usd = gas_units × gas_price_gwei × 1e-9 × eth_price_usd
4. Compare gas_cost_usd against trade notional → cost_bps
5. If cost_bps > budget: no-op (small trades on L1 are uneconomical)
```

### Gas Units by Operation Type

| Operation     | Typical Gas Units | L1 Cost (30 gwei) | L2 Cost (0.01 gwei) |
| ------------- | ----------------- | ----------------- | ------------------- |
| ERC20 approve | 46,000            | ~$4.00            | ~$0.001             |
| Uniswap swap  | 150,000–185,000   | ~$14.00           | ~$0.004             |
| Aave supply   | 250,000           | ~$22.00           | ~$0.006             |
| Aave borrow   | 300,000           | ~$27.00           | ~$0.007             |
| Flash loan    | 500,000–800,000   | ~$50.00           | ~$0.015             |
| Atomic bundle | 800,000–1,500,000 | ~$90.00           | ~$0.030             |

**Rule:** L1 Ethereum operations are only cost-effective above ~$50,000 notional at 30 gwei. Below that, the strategy
must route to L2 or skip the trade.

### MEV Protection

DeFi swaps on public mempools are subject to sandwich attacks (front-running + back-running). Cost impact: 10–50bps
additional slippage on large trades.

**Mitigations in the system:**

- `max_slippage_bps` on every swap instruction — revert if price moves beyond tolerance
- Private transaction submission (Flashbots Protect) for L1 trades > $100K notional
- L2 execution preferred for most DeFi strategies (lower gas, reduced MEV surface)
- Atomic bundles (flash loans) are MEV-resistant by design — revert on any unfavorable state change

### Protocol Fees

| Protocol | Fee Type       | Rate      | Notes                                   |
| -------- | -------------- | --------- | --------------------------------------- |
| Uniswap  | Swap fee       | 1–100 bps | Pool-specific (0.01%, 0.05%, 0.30%, 1%) |
| Aave     | Flash loan fee | 5–9 bps   | Per flash loan amount                   |
| Curve    | Swap fee       | 1–4 bps   | Dynamic fee based on pool imbalance     |
| Lido     | Staking fee    | 1000 bps  | 10% of staking rewards (not principal)  |

## TradFi Commission Model

TradFi costs are commission-based (per contract or per share) rather than percentage-based:

| Instrument     | Commission     | Exchange Fee   | Clearing Fee   |
| -------------- | -------------- | -------------- | -------------- |
| Equity (US)    | $0.005/share   | $0.003/share   | $0.002/share   |
| Futures (CME)  | $1.25/contract | $1.00/contract | $0.50/contract |
| Options (CBOE) | $0.65/contract | $0.30/contract | $0.02/contract |
| FX Spot        | 0.5–2.0 bps    | N/A            | N/A            |

**Conversion to bps:** `cost_bps = (commission_per_unit / price_per_unit) × 10000`. For a $50 stock at $0.01/share
all-in: `(0.01 / 50) × 10000 = 2 bps`.

## Sports Overround / Vig Model

Sports betting costs are embedded in the odds via the overround (bookmaker margin):

```
Fair probability: Team A 60%, Team B 40%
Fair odds: Team A 1.667, Team B 2.500
Bookmaker odds: Team A 1.580, Team B 2.350

Overround = (1/1.580 + 1/2.350) - 1 = (0.633 + 0.426) - 1 = 5.9%
Effective cost per bet = overround / num_outcomes = ~2.95%
```

### Overround by Market Type

| Market Type    | Typical Overround | Equivalent Cost (bps) | Notes                        |
| -------------- | ----------------- | --------------------- | ---------------------------- |
| Match result   | 3–8%              | 150–400               | Most liquid                  |
| Asian handicap | 2–5%              | 100–250               | Tight spreads, high volume   |
| Over/under     | 4–8%              | 200–400               | Goals, points, corners       |
| Correct score  | 15–40%            | 750–2000              | Illiquid, wide margins       |
| In-play        | 5–15%             | 250–750               | Dynamic, widens with urgency |

**Rule:** Sports strategies must clear the overround hurdle before any trade is considered. A strategy needs
`edge_bps > overround_bps + execution_cost_bps` to be profitable.

## Prediction Market Fee Model

| Platform   | Trading Fee | Settlement Fee | Spread Cost (typical) |
| ---------- | ----------- | -------------- | --------------------- |
| Polymarket | 0 bps       | 0 bps          | 50–200 bps            |
| Kalshi     | 0–7%        | 0%             | 100–500 bps           |

The dominant cost in prediction markets is the bid-ask spread, not fees. Spread cost varies dramatically with market
liquidity and time to resolution.

## Slippage Estimation

### Order Book Slippage (CeFi / TradFi)

Slippage is estimated by walking the order book from the features pipeline:

```
Slippage estimation inputs:
  - order_size: Decimal (notional)
  - book_depth: list[PriceLevel] (from L2 features)
  - side: BUY | SELL

Algorithm:
  1. Walk the book from best bid/ask outward
  2. Accumulate filled quantity at each level
  3. VWAP of filled levels vs best bid/ask = slippage_bps
  4. If order_size > total book depth: slippage = INFINITY → reject
```

### Market Impact Model (Large Orders)

For orders exceeding 5% of average daily volume (ADV), temporary and permanent market impact must be estimated:

```
Temporary impact (bps) = sigma × sqrt(order_size / ADV) × participation_rate
Permanent impact (bps) = 0.5 × temporary_impact

Where:
  sigma = daily volatility (from features pipeline)
  ADV = 20-day average daily volume (from features pipeline)
  participation_rate = order_size / (ADV × execution_window_hours / 24)
```

This feeds into execution algorithm selection — large orders use TWAP/VWAP/Almgren-Chriss to minimize impact.

## Cost Budgets by Strategy Archetype

| Archetype             | Max Cost Budget (bps) | Typical Edge (bps) | Cost/Edge Ratio | Notes                          |
| --------------------- | --------------------- | ------------------ | --------------- | ------------------------------ |
| Delta-One Basis       | 15                    | 30–80              | 20–50%          | Low frequency, large notional  |
| DeFi Recursive Basis  | 25                    | 50–150             | 17–50%          | Gas-heavy, multi-step          |
| Statistical Arb       | 8                     | 15–30              | 27–53%          | High frequency, small edge     |
| Market Making         | 3                     | 5–15               | 20–60%          | Maker rebates offset costs     |
| Momentum              | 12                    | 20–60              | 20–60%          | Medium frequency               |
| Mean Reversion        | 10                    | 15–40              | 25–67%          | Passive entry, aggressive exit |
| Sports Arbitrage      | 200                   | 300–600            | 33–67%          | Overround is the cost          |
| Calendar Spread       | 10                    | 20–50              | 20–50%          | Two-leg execution              |
| Volatility Arb        | 15                    | 25–80              | 19–60%          | Options commissions            |
| Funding Rate Harvest  | 5                     | 10–30              | 17–50%          | Passive, long hold             |
| Liquidation Sniper    | 20                    | 50–200             | 10–40%          | Urgent, gas-competitive        |
| Cross-Exchange Arb    | 6                     | 10–25              | 24–60%          | Speed-dependent                |
| Prediction Contrarian | 150                   | 200–500            | 30–75%          | Spread-dominated               |
| Yield Optimization    | 20                    | 40–120             | 17–50%          | Gas + protocol fees            |

**Rule:** If `cost/edge > 0.67` (costs consume more than 2/3 of edge), the strategy is fragile and should not run live
without explicit risk approval.

## Cost Tracking in PnL Attribution

Post-trade costs feed into the PnL attribution pipeline (see [pnl-attribution.md](pnl-attribution.md)):

```
ActualCost breakdown:
  ├── exchange_fee_bps      → PnL factor: FEES
  ├── protocol_fee_bps      → PnL factor: FEES
  ├── gas_cost_bps          → PnL factor: FEES (DeFi only)
  ├── slippage_bps          → PnL factor: SLIPPAGE
  ├── market_impact_bps     → PnL factor: SLIPPAGE
  └── mev_cost_bps          → PnL factor: SLIPPAGE (DeFi only)
```

### Cost Drift Alerting

The alerting-service monitors cost drift: `actual_cost / estimated_cost`. Thresholds:

| Ratio       | Action                                         |
| ----------- | ---------------------------------------------- |
| `< 1.2`     | Normal — no action                             |
| `1.2 – 1.5` | WARN alert — cost model may need recalibration |
| `1.5 – 2.0` | ELEVATED alert — review cost estimates         |
| `> 2.0`     | CRITICAL alert — pause strategy, investigate   |

## SSOT References

| Concept             | SSOT                     | Location                                                    |
| ------------------- | ------------------------ | ----------------------------------------------------------- |
| Fee tier config     | Strategy config YAML     | `gs://config/{strategy_id}/clients/{client_id}.yaml`        |
| Gas price feature   | features-onchain-service | `features_onchain_service/calculators/gas_price_adapter.py` |
| Venue capabilities  | UAC registry             | `unified-api-contracts/registry/venue_constants.py`         |
| Cost attribution    | PnL attribution pipeline | `strategy-service/strategy_service/pnl_calculator.py`       |
| Slippage estimation | Order book features      | `features-delta-one-service/` (L2 book depth features)      |
| DeFi gas estimation | UDEI                     | `execution-service/`                                        |
| Cost drift alerts   | alerting-service         | `alerting-service/alerting_service/rules/`                  |
