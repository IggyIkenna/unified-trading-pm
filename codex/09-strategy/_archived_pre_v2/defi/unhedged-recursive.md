---
scope: [engineer, admin]
---

# DeFi Unhedged Recursive Strategy

> **Asset class:** DeFi **Strategy type:** Leveraged Yield (flash loan amplified, directional coin exposure) **Strategy
> ID pattern:** `DEFI_ETH_RECURSIVE_UNHEDGED_ALL_HYPERLIQUID_HUF_1H`

## Overview

Directional variant of the Recursive Staked Basis strategy. Uses flash loans to create leveraged exposure to weETH
staking yield without a perp hedge. The investor retains full ETH price exposure (long bias) while amplifying staking
yield and EtherFi/EIGEN rewards via recursive Aave V3 borrowing. Flash borrow ETH, swap to weETH, deposit as Aave
collateral, borrow ETH against it, repay flash loan -- all atomic. No perp short means higher return in bull markets
(~38% APY in presentation) but full directional risk.

Use case: clients with an ETH/SOL/BTC share class who want coin + yield rather than delta-neutral yield harvesting.

**WARNING:** This strategy has liquidation risk AND directional market risk. If ETH drops significantly while leveraged,
health factor can deteriorate rapidly. Unlike the hedged variant, there is no perp hedge to offset spot price declines.

## Token / Position Flow

### Entry (Atomic Bundle)

```
Start:  WALLET:SPOT_ASSET:USDT  (100% USDT)

ATOMIC BUNDLE (all-or-nothing, single transaction):
Step 1 - FLASH_BORROW: Borrow WETH from Morpho    (amount = initial_eth * (leverage - 1))
Step 2 - SWAP:         USDT --> WETH               (90% of USDT capital)
Step 3 - SWAP:         WETH --> weETH              (initial_eth + flash_amount combined)
Step 4 - LEND:         Deposit weETH to AAVE       (total_weeth --> receive aweETH)
Step 5 - BORROW:       Borrow WETH from AAVE       (amount = flash_amount, against weETH collateral)
Step 6 - FLASH_REPAY:  Repay flash loan with WETH  (flash_amount + fee)

NO PERP HEDGE (unhedged mode):
Step 7 - (skipped)     No margin transfer
Step 8 - (skipped)     No perp short

Wallet after deploy:
  - AAVEV3-ETHEREUM:A_TOKEN:AWEETH@ETHEREUM              = total_weeth (collateral, positive)
  - AAVEV3-ETHEREUM:DEBT_TOKEN:DEBTWETH@ETHEREUM          = flash_amount (debt, negative)
  - No perp position
  - Net delta = leveraged LONG (fully directional)
```

### Concrete Example (2.5x leverage, $10,000)

```
initial_usdt     = $10,000
spot_allocation  = $9,000 (90%)
margin           = $1,000 (10% -- retained as reserve, not sent to perp venue)
eth_price        = $3,000
initial_eth      = $9,000 / $3,000 = 3 ETH
flash_amount     = 3 * (2.5 - 1) = 4.5 ETH  (from Morpho, 0% fee)
total_eth        = 3 + 4.5 = 7.5 ETH
weeth_rate       = 1.035
total_weeth      = 7.5 / 1.035 = 7.246 weETH

After atomic bundle:
  AAVE collateral (aweETH) = 7.246 weETH  (worth $22,500)
  AAVE debt (debtWETH)     = 4.5 ETH      (worth $13,500)
  Net AAVE equity          = $9,000

Net delta = +7.5 ETH (LONG, unhedged)
```

### Exit (Atomic Bundle)

```
ATOMIC BUNDLE:
Step 1 - FLASH_BORROW: Borrow WETH (= debt_balance * 1.001, slight buffer)
Step 2 - REPAY:        Repay AAVE debt with borrowed WETH
Step 3 - WITHDRAW:     Withdraw weETH collateral from AAVE (burn aweETH)
Step 4 - SWAP:         weETH --> WETH
Step 5 - FLASH_REPAY:  Repay flash loan with WETH from step 4

NON-ATOMIC:
Step 6 - SWAP:         Remaining WETH --> USDT (back to stablecoin)

No perp to close (unhedged mode).
```

## Data Architecture

| Dimension              | Value                                                                                                                                                                                                    | SSOT                                |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)                                                                                                                                                | `strategy-service/config.py`        |
| **Processed data**     | `market_data` dict: `eth_price`, `weeth_eth_rate`, `aave_borrow_apy_eth`, `aave_ltv`, `morpho_flash_loan_liquidity`, `health_factor`, `weekly_rewards`, `aave_liquidation_threshold`                     | Features hydrated alongside candles |
| **Features**           | `features` dict: `lst_staking_apy`, `aave_borrow_apy_eth`, `weeth_eth_rate`, `health_factor`, `weekly_rewards`, `eigen_weekly_rewards`, `ethfi_weekly_rewards`, `aave_ltv`, `aave_liquidation_threshold` | `features-onchain-service`          |
| **Interval**           | Time-driven (candle-based), not event-driven                                                                                                                                                             | `timeframe` in strategy config      |
| **Lowest granularity** | 1H (currently hardcoded in factory)                                                                                                                                                                      | `defi_recursive_basis.py` factory   |
| **Execution mode**     | `hold_until_further` -- entry and exit can occur on same candle                                                                                                                                          | Strategy config                     |

## Instrument Selection

**Currently: STATIC (hardcoded per config, no dynamic selection)**

All instruments are fixed at strategy initialisation:

- Collateral: `AAVEV3-ETHEREUM:A_TOKEN:AWEETH@ETHEREUM` -- always weETH as collateral
- Debt: `AAVEV3-ETHEREUM:DEBT_TOKEN:DEBTWETH@ETHEREUM` -- always borrow WETH
- Flash loan: Morpho Blue (0% fee) preferred over Aave (0.05%)
- **No perp instrument** -- `hedged=False` means the perp venue config is set to HYPERLIQUID but never used for trading

**SSOT for instrument types per venue:** See
[`INSTRUMENT_TYPES_BY_VENUE`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**SOR is ON by default for the swap legs only.**

| Leg                               | SOR? | Allowed Venues                                              | SSOT                 |
| --------------------------------- | ---- | ----------------------------------------------------------- | -------------------- |
| Step 3 (WETH to weETH swap)       | YES  | `CURVE-ETHEREUM`, `BALANCER-ETHEREUM`, `UNISWAPV3-ETHEREUM` | `defi_base.py:84-86` |
| Step 1 (Flash borrow from Morpho) | NO   | Morpho Blue only (hardcoded)                                | --                   |
| Step 4 (Deposit to Aave)          | NO   | Aave V3 only                                                | --                   |

No perp SOR needed -- there is no perp leg.

## Instruments

| Instrument Key                                 | Venue   | Type      | Role                         |
| ---------------------------------------------- | ------- | --------- | ---------------------------- |
| `WALLET:SPOT_ASSET:USDT`                       | Wallet  | Spot      | Initial capital              |
| `AAVEV3-ETHEREUM:A_TOKEN:AWEETH@ETHEREUM`      | Aave V3 | aToken    | Collateral (long, leveraged) |
| `AAVEV3-ETHEREUM:DEBT_TOKEN:DEBTWETH@ETHEREUM` | Aave V3 | debtToken | Debt (negative equity)       |

Note: no perp instrument -- the strategy is fully directional.

## Key Features Consumed

| Feature                       | Source Service   | SLA | Used For                        |
| ----------------------------- | ---------------- | --- | ------------------------------- |
| `lst_staking_apy`             | features-onchain | 60s | Signal: staking yield component |
| `weeth_eth_rate`              | features-onchain | 60s | Position sizing, HF tracking    |
| `aave_borrow_apy_eth`         | features-onchain | 60s | Cost: leverage cost calculation |
| `aave_ltv`                    | features-onchain | 60s | Leverage cap: max safe LTV      |
| `aave_liquidation_threshold`  | features-onchain | 60s | Dynamic HF and leverage cap     |
| `morpho_flash_loan_liquidity` | features-onchain | 60s | Pre-check: can we flash borrow? |
| `health_factor`               | features-onchain | 60s | Risk: liquidation proximity     |
| `weekly_rewards`              | features-onchain | 24h | EtherFi/EIGEN reward yield      |
| `eigen_weekly_rewards`        | features-onchain | 24h | EIGEN-only reward attribution   |
| `ethfi_weekly_rewards`        | features-onchain | 24h | ETHFI-only reward attribution   |
| `eth_price`                   | market-tick-data | 1s  | PnL, sizing, HF calculation     |

**Difference from hedged variant:** `funding_rate` is NOT consumed. Since there is no perp hedge, funding rate is
irrelevant. The `_resolve_signal_rates()` method sets `funding_rate = 0` when `self.hedged is False`.

## Signal Generation

```python
# Net APY = (staking_apy + reward_yield) * leverage - borrow_apy * (leverage - 1)
# Note: funding_apy = 0 (no perp hedge)
net_apy = calculate_net_apy(staking_apy, funding_apy=0, borrow_apy, target_leverage, reward_yield)

# Entry: deploy when net APY exceeds minimum threshold (default 5%)
if not self.is_deployed and net_apy >= self.min_net_apy:
    return {"action": "DEPLOY", ...}

# Exit: net APY turns negative or health factor critical
if self.is_deployed:
    if net_apy < 0:
        return {"action": "EXIT", "reason": "Net APY negative"}
    if health_factor < effective_min_health:
        return {"action": "EXIT", "reason": "Health factor critical"}
```

The `min_net_apy` default for the unhedged variant is 5% (vs 8% for hedged), reflecting the additional ETH price
appreciation expected by directional investors.

## Reward Mode (EIGEN / ETHFI Split)

The `reward_mode` config controls how EtherFi/EigenLayer reward distributions are attributed:

| Mode         | Behavior                               | Use Case                          |
| ------------ | -------------------------------------- | --------------------------------- |
| `all`        | EIGEN + ETHFI combined (default)       | Maximum yield attribution         |
| `eigen_only` | Only EIGEN rewards included in net APY | Conservative (exclude ETHFI risk) |
| `ethfi_only` | Only ETHFI rewards included            | ETHFI-focused clients             |

Rewards are annualized from weekly distributions: `reward_yield = weekly_rewards * 52`. The factory function
`create_unhedged_recursive_strategy()` defaults to `reward_mode="all"`.

## Aave V3 E-Mode

Same E-Mode detection as the hedged variant. When collateral (weETH) and debt (WETH) are ETH-correlated, Aave V3 E-Mode
provides significantly higher LTV:

| Mode     | LTV   | Liq Threshold | Max Leverage (raw) |
| -------- | ----- | ------------- | ------------------ |
| Standard | 72.5% | 77.5%         | 3.6x               |
| E-Mode   | 93%   | 95%           | 14.3x              |

Config `max_leverage` (default 3.0) still caps actual leverage well below the protocol maximum.

## Leverage Cap (Four Caps)

Four caps applied in `_apply_ltv_leverage_cap()` -- most restrictive wins:

1. **LTV-based:** `1/(1 - LTV) * 0.85` safety buffer
2. **Spread-move-based (depeg tolerance):** `liq_threshold / (1 - liq_threshold + max_depeg_tolerance)`
   - Defaults from UAC `MAX_UNDERLYING_MOVES[base_currency].max_spread_move` (ETH = 3%)
3. **Outright-move-based:** `(1 - 0.05) / max_outright_move`
   - For unhedged, this cap is less relevant (no perp to liquidate) but still applied
4. **Config `max_leverage`** (hard cap, default 3.0)

**SSOT:** `unified_api_contracts.registry.max_underlying_moves.MAX_UNDERLYING_MOVES`

## PnL Attribution

| Component           | Settlement Type          | Mechanism                                                                      |
| ------------------- | ------------------------ | ------------------------------------------------------------------------------ |
| `staking_yield_pnl` | `LST_YIELD` (per candle) | `aweETH_amount * (weeth_rate_new - weeth_rate_old) / weeth_rate_old` LEVERAGED |
| `lending_yield_pnl` | `AAVE_INDEX` (supply)    | aweETH balance growth from liquidity_index (small)                             |
| `borrow_cost_pnl`   | `AAVE_INDEX` (borrow)    | debtWETH balance growth from borrow_index (NEGATIVE cost)                      |
| `rewards_pnl`       | `SEASONAL_WEEKLY`        | EtherFi/EIGEN weekly distributions (LEVERAGED amount)                          |
| `spot_pnl`          | Mark-to-market           | ETH price change \* leveraged exposure (DOMINANT component)                    |
| `transaction_costs` | Per-fill                 | Flash loan fee (Morpho=0%) + gas (~500k) + swap slippage                       |

**Key difference from hedged variant:** `funding_pnl` is absent (no perp), and `spot_pnl` is the dominant P&L driver. In
the hedged variant, spot exposure is neutralized by the perp hedge, so P&L comes primarily from yield. In the unhedged
variant, P&L is dominated by directional ETH price movement, with yield as a secondary component.

**Source of truth:**

```
equity = aweETH_value - debtWETH_value - initial
```

**Net APY formula (signal generation):**

```
net_apy = (staking_apy + 0 + reward_yield) * leverage - borrow_apy * (leverage - 1)

Example: (3.5% + 0% + 3.0%) * 2.5 - 2% * 1.5 = 16.25% - 3% = 13.25% net yield
Plus: ETH price appreciation (directional, not in APY formula)
```

The 38% headline figure from the presentation includes both yield (~13%) and assumed ETH price appreciation (~25%).

## Risk Profile

| Metric               | Target  | Notes                                                         |
| -------------------- | ------- | ------------------------------------------------------------- |
| Target annual return | 25-38%  | Leveraged staking yield + directional ETH appreciation        |
| Target Sharpe ratio  | 0.8-1.5 | Lower than hedged due to directional volatility               |
| Max drawdown         | 30%     | Directional ETH risk + leveraged position amplifies losses    |
| Max leverage         | 3.0x    | Capped by strategy; Aave allows up to ~5x in E-Mode           |
| Capital scalability  | $5M     | Constrained by Morpho flash loan liquidity + Aave utilization |

**Key risk difference:** Sharpe ratio is significantly lower than the hedged variant (~2.0) because the dominant P&L
component is directional ETH price movement, not stable yield harvesting.

## Latency Profile

| Segment                             | p50 Target | p99 Target | Co-location Needed?                    |
| ----------------------------------- | ---------- | ---------- | -------------------------------------- |
| Market data -> feature              | 50ms       | 200ms      | No                                     |
| Feature -> signal                   | 10ms       | 50ms       | No                                     |
| Signal -> instruction               | 5ms        | 20ms       | No                                     |
| Instruction -> fill (atomic bundle) | 5s         | 60s        | No (gas-dependent, may need gas boost) |
| **End-to-end**                      | **~6s**    | **~61s**   | **No**                                 |

Lower latency than hedged variant because there is no perp leg to execute after the atomic bundle. The entire strategy
is a single on-chain atomic transaction plus one swap to exit.

## Execution Details

- **Venues:** Morpho (flash loan), Aave V3 (collateral + borrow), Uniswap/Curve (swaps via SOR)
- **Order types:** Atomic bundle (flash loan sequence), Market (swaps via SOR)
- **Atomic execution required?** YES -- Steps 1-6 MUST be atomic. If any step fails, all revert.
- **No perp venue needed** -- Hyperliquid is configured but never receives instructions
- **Gas budget:** ~500k gas for atomic bundle (entry), ~500k for exit (fewer steps than hedged)

### Rebalancing

**Trigger type:** Event-driven (NOT periodic). No rebalance without new market data.

| Level    | Position Deviation | Health Factor | Action                               |
| -------- | ------------------ | ------------- | ------------------------------------ |
| Minor    | >2% drift          | HF > 1.5      | LOG_ONLY                             |
| Major    | >5% drift          | HF < 1.4      | REBALANCE -- deleverage 20%          |
| Critical | >10% drift         | HF < 1.25     | EMERGENCY_EXIT -- full atomic unwind |

Since there is no perp to rebalance, "position deviation" refers to the collateral-to-debt ratio drifting from target.
Deleverage is an atomic bundle: flash borrow -> partial repay debt -> partial withdraw collateral -> swap weETH to WETH
-> flash repay. Leverage decreases by 20% per deleverage event.

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern     | Exposure Type                      | Used For               |
| ---------------------- | ---------------------------------- | ---------------------- |
| `AAVE_V3:A_TOKEN:*`    | Collateral value (leveraged weETH) | HF numerator           |
| `AAVE_V3:DEBT_TOKEN:*` | Debt value (borrowed WETH)         | HF denominator         |
| `WALLET:LST:*`         | Underlying LST appreciation        | Staking yield tracking |

No perp exposure subscriptions (unhedged).

### Risk Type Subscriptions

| Risk Type          | Subscribed?        | Threshold                                    | Action on Breach                 |
| ------------------ | ------------------ | -------------------------------------------- | -------------------------------- |
| `aave_liquidation` | **YES (CRITICAL)** | HF < 1.5 deleverage, HF < 1.2 emergency exit | Atomic deleverage bundle         |
| `delta`            | NO                 | --                                           | No hedge to adjust               |
| `funding`          | NO                 | --                                           | No perp position                 |
| `staking_yield`    | YES (signal)       | Net APY below threshold                      | Exit decision                    |
| `borrow_cost`      | YES                | Borrow rate spike erodes net APY             | Deleverage or exit               |
| `protocol_risk`    | YES                | weETH depeg > 2%, Morpho liquidity dry-up    | Emergency exit                   |
| `directional`      | YES                | ETH price drop amplified by leverage         | HF-based deleverage              |
| `liquidity`        | YES                | Flash loan liquidity < required amount       | Cannot rebalance/exit atomically |
| `basis`            | NO                 | --                                           | --                               |

**Key difference from hedged:** `delta` and `funding` are not subscribed (no perp). `directional` risk is implicit
through health factor monitoring -- as ETH price drops, HF degrades, triggering deleverage.

### Custom Strategy Risk Types

| Custom Risk                        | What It Measures                                               | Evaluation Method  |
| ---------------------------------- | -------------------------------------------------------------- | ------------------ |
| ETH borrow rate sensitivity        | PnL impact of +100bp borrow rate on leveraged position         | `rate_sensitivity` |
| Health factor degradation velocity | Rate of HF decline from ETH price drops -> time-to-liquidation | `threshold_breach` |
| Flash loan liquidity risk          | Morpho pool liquidity vs required flash amount                 | `threshold_breach` |
| Directional leverage amplification | How leverage multiplies losses in ETH downturn                 | `scenario_pnl`     |
| weETH depeg cascade                | weETH depeg -> HF drop -> forced deleverage -> more selling    | `scenario_pnl`     |

## Margin & Liquidation

- **Margin model:** Aave V3 health factor ONLY (no CeFi margin -- no perp)
- **Health factor:** `HF = (collateral_value * liquidation_threshold) / debt_value`
- **Liquidation penalty:** 5-10% of collateral (asset-dependent)
- **Liquidation trigger:** HF < 1.0
- **Strategy thresholds:** HF < 1.5 deleverage 20%, HF < 1.2 emergency exit
- **Monitoring:** Health factor checked EVERY candle; interval tightens as HF degrades
- **No perp margin risk** -- unlike the hedged variant, there is no Hyperliquid margin to monitor

### What Causes Health Factor to Drop

1. **ETH price drops** -- collateral (weETH) and debt (WETH) both denominated in ETH, so raw ETH price moves have
   minimal direct HF impact. BUT if weETH/ETH rate depegs simultaneously, HF drops.
2. **weETH depegs** -- collateral drops relative to debt (most dangerous scenario, same as hedged)
3. **Borrow rate spikes** -- debt grows faster than expected
4. **Aave parameter changes** -- governance reduces LTV or liquidation threshold

## Authentication & Credentials

| Venue                     | Secret Name                   | Testnet Available? | Notes                                  |
| ------------------------- | ----------------------------- | ------------------ | -------------------------------------- |
| Morpho (flash loan)       | `alchemy-api-key` (RPC)       | Yes (Sepolia)      | No API key needed; interact via wallet |
| Aave V3 (collateral/debt) | `alchemy-api-key` (RPC)       | Yes (Sepolia)      | Permissionless via wallet              |
| Uniswap/Curve (swaps)     | `alchemy-api-key` (RPC)       | Yes (Sepolia)      | Permissionless via wallet              |
| Wallet                    | `wallet-{client}-private-key` | Yes (dev wallet)   | Signs ALL on-chain transactions        |

No Hyperliquid credentials needed (no perp trading).

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Factory Function

```python
from strategy_service.engine.strategies.defi_recursive_basis import (
    create_unhedged_recursive_strategy,
)

# Create default unhedged recursive strategy
strategy = create_unhedged_recursive_strategy(
    target_leverage=2.5,
    flash_loan_provider="MORPHO",
    min_net_apy=0.05,
    reward_mode="all",
)

# Strategy ID: DEFI_ETH_RECURSIVE_UNHEDGED_ALL_HYPERLIQUID_HUF_1H
```

### Config Parameters

| Parameter              | Type  | Default  | Description                                                       |
| ---------------------- | ----- | -------- | ----------------------------------------------------------------- |
| `target_leverage`      | float | 2.5      | Target recursive leverage multiplier                              |
| `max_leverage`         | float | 3.0      | Hard cap on leverage                                              |
| `flash_loan_provider`  | str   | `MORPHO` | Flash loan source (Morpho=0% fee, Aave=0.05%)                     |
| `min_net_apy`          | float | 0.05     | Minimum net APY for entry (5% -- lower than hedged's 8%)          |
| `min_health_factor`    | float | 1.2      | Emergency exit threshold                                          |
| `target_health_factor` | float | 1.5      | Deleverage trigger                                                |
| `reward_mode`          | str   | `all`    | EIGEN/ETHFI reward attribution: `all`, `eigen_only`, `ethfi_only` |
| `max_depeg_tolerance`  | float | (UAC)    | Defaults from UAC MAX_UNDERLYING_MOVES (ETH = 3% spread move)     |
| `base_currency`        | str   | `ETH`    | Base currency for move assumptions                                |
| `hedged`               | bool  | `False`  | Always False for this variant (set by factory)                    |

## Client Onboarding

See [cross-cutting/client-onboarding.md](../cross-cutting/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Wallet per client (signs atomic bundles -- MUST have sufficient ETH for gas)
2. **No Hyperliquid account needed** (no perp trading)
3. Config: `initial_capital`, `max_leverage` (default 2.5x), `min_health_factor`
4. **Restart required?** No -- hot-reload via GCS config
5. **Gas funding:** Client wallet needs ~0.1 ETH pre-funded for gas on atomic bundles

### Higher Risk -- Additional Onboarding Steps

- Client must acknowledge both liquidation risk AND directional market risk
- Client should understand that losses are amplified by leverage in ETH downturns
- Initial capital minimum: $50,000 (gas costs make smaller amounts unprofitable)
- Leverage cap agreed per client (default 2.5x, max 3.0x with approval)
- Health factor alert thresholds configured per client risk tolerance

## UI Visualisation

### Standard views

- PnL waterfall, margin health, position breakdown (from monitoring UI plans)

### Strategy-specific views

- **Health factor time series** -- with 1.5 (deleverage), 1.2 (emergency), 1.0 (liquidation) threshold lines
- **Leverage gauge** -- current leverage vs max, with colour zones (green/yellow/red)
- **Collateral vs debt chart** -- stacked: aweETH value (green) vs debtWETH value (red), net equity line
- **Directional P&L decomposition** -- spot_pnl (dominant, blue) vs yield_pnl (staking + rewards, green) vs costs (red)
- **ETH price overlay with leverage amplification** -- shows how 10% ETH move translates to 25% portfolio move at 2.5x
- **Net APY waterfall** -- staking + rewards - borrow_cost = net yield APY (excluding directional component)

## E2E Manual Trading Workflow

Step-by-step manual recreation of the unhedged recursive strategy. Simpler than hedged (no perp leg).

### Prerequisites

- Treasury wallet funded with USDC/ETH on Ethereum
- FlashLoanReceiver contract deployed (or use Instadapp DSA)
- Alchemy RPC for Ethereum
- No CeFi venue accounts needed

### Step-by-Step (Atomic Deploy Sequence)

| Step                    | Action                                       | Instruction Type | Service                           | Instant P&L            |
| ----------------------- | -------------------------------------------- | ---------------- | --------------------------------- | ---------------------- |
| 1                       | Observe treasury balance                     | --               | position-balance-monitor          | --                     |
| 2                       | Transfer ETH from treasury to trading wallet | TRANSFER         | execution-service                 | Gas: ~$2               |
| **Atomic Bundle Start** |                                              |                  |                                   |                        |
| 3                       | Flash borrow ETH from Morpho (0% fee)        | FLASH_BORROW     | execution-service                 | $0 (no fee)            |
| 4                       | Swap USDC to ETH (90% of wallet)             | SWAP             | execution-service (SOR)           | Slippage: ~5 bps       |
| 5                       | Swap ETH to weETH (EtherFi staking)          | SWAP             | execution-service                 | Slippage: ~20-35 bps   |
| 6                       | Deposit weETH as collateral in AAVE V3       | LEND             | execution-service (AaveConnector) | Gas included in bundle |
| 7                       | Borrow ETH from AAVE against weETH           | BORROW           | execution-service (AaveConnector) | Gas included           |
| 8                       | Repay flash loan with borrowed ETH           | FLASH_REPAY      | execution-service                 | $0                     |
| **Atomic Bundle End**   |                                              |                  | Total bundle gas: ~$50-80         |                        |

### Position State After Deployment

- AAVE collateral: ~7.25 aWEETH ($22,500 at 2.5x leverage)
- AAVE debt: ~4.5 ETH ($13,500 borrowed)
- No perp position
- Health Factor: ~1.29 (standard) or ~1.58 (E-Mode)
- Net delta: +7.5 ETH LONG (fully directional)

### Instant P&L

- Flash loan: $0 (Morpho 0% fee)
- Swap slippage (USDC to ETH): ~$4.50 (5 bps on $9K)
- Swap slippage (ETH to weETH): ~$23 (25 bps on $9K leveraged to $22.5K)
- Atomic bundle gas: ~$65
- Total entry cost: ~$92.50 (cheaper than hedged -- no perp leg)

### Ongoing P&L (Daily)

- Staking yield (weETH): 3.5% APY x 2.5x = 8.75%
- EtherFi rewards (EIGEN + ETHFI): 3.0% APY x 2.5x = 7.5%
- Borrow cost (AAVE ETH): -2.0% APY x 1.5x = -3.0%
- **Net yield APY: ~13.25%** on $9K base capital
- Daily yield: ~$3.27/day
- Directional P&L: ETH price change x 7.5 ETH (dominant)
- Cost recovery (yield only): ~28 days

### Risk Metrics

- Health Factor: monitored every candle. Deleverage at HF < 1.4. Emergency exit at HF < 1.25.
- Net delta: +7.5 ETH LONG (no hedge)
- Directional risk: 10% ETH drop = ~25% portfolio loss at 2.5x leverage
- Liquidation price: where HF hits 1.0 (depends on weETH/ETH depeg more than raw ETH price)

### Exit Workflow (Atomic Unwind)

| Step | Action                    | Instruction Type |
| ---- | ------------------------- | ---------------- |
| 1    | Flash borrow ETH          | FLASH_BORROW     |
| 2    | Repay AAVE debt           | REPAY            |
| 3    | Withdraw weETH collateral | WITHDRAW         |
| 4    | Swap weETH to ETH         | SWAP             |
| 5    | Repay flash loan          | FLASH_REPAY      |
| 6    | Swap ETH to USDC          | SWAP             |
| 7    | Transfer USDC to treasury | TRANSFER         |

### Trade History (Expected Output)

| #   | Time  | Type         | Instrument  | Amount     | Gas | Slippage | Running P&L |
| --- | ----- | ------------ | ----------- | ---------- | --- | -------- | ----------- |
| 1   | 10:01 | TRANSFER     | ETH         | $10K       | $2  | $0       | -$2         |
| 2   | 10:02 | FLASH_BORROW | ETH         | 4.5 ETH    | $0  | $0       | -$2         |
| 3   | 10:02 | SWAP         | ETH/USDC    | 3 ETH      | --  | -$4.50   | -$6.50      |
| 4   | 10:02 | SWAP         | weETH/ETH   | 7.25 weETH | --  | -$23     | -$29.50     |
| 5   | 10:02 | LEND         | aWEETH      | 7.25       | --  | $0       | -$29.50     |
| 6   | 10:02 | BORROW       | ETH         | 4.5        | --  | $0       | -$29.50     |
| 7   | 10:02 | FLASH_REPAY  | ETH         | 4.5        | $65 | $0       | -$94.50     |
| EOD | --    | STAKING      | weETH       | +$2.16     | $0  | $0       | -$92.34     |
| EOD | --    | BORROW       | ETH debt    | -$0.74     | $0  | $0       | -$93.08     |
| EOD | --    | REWARDS      | EIGEN+ETHFI | +$1.85     | $0  | $0       | -$91.23     |
| EOD | --    | SPOT         | ETH         | +/-varies  | $0  | $0       | directional |

## Testing Stage Status

| Stage        | Status  | Notes                                                                  |
| ------------ | ------- | ---------------------------------------------------------------------- |
| MOCK         | Pending | Need MockDeFiDynamics with HF degradation + ETH price scenarios        |
| HISTORICAL   | Pending | Need 365 days data (must see bear market to validate directional risk) |
| LIVE_MOCK    | Pending | Blocked by features-onchain health_factor + aave_borrow_apy            |
| LIVE_TESTNET | Pending | Blocked by AAVEConnector live execution + testnet contracts            |
| BATCH_REAL   | Pending | Blocked by historical APY storage + liquidation enforcement            |
| STAGING      | Pending | Tenderly fork (atomic bundles execute against fork)                    |
| LIVE_REAL    | Pending | All above + real capital approval + client risk acknowledgment         |

## Wallet & Capital Flow

| Component        | Value                                       |
| ---------------- | ------------------------------------------- |
| Treasury reserve | 20% of AUM                                  |
| Hot wallet       | Per-chain, per-strategy isolated            |
| CeFi sub-account | No (no perp trading)                        |
| Bridge required  | No (single-chain -- Ethereum mainnet)       |
| Flash loan       | Morpho Blue (0% fee) -- atomic borrow/repay |
| Custody          | Copper MPC                                  |

Capital flow: Client deposit --> treasury --> hot wallet --> SWAP to WETH + FLASH BORROW (atomic bundle: flash borrow,
swap to weETH, deposit to Aave, borrow WETH, repay flash). No margin transfer to CeFi venues. Simpler capital flow than
hedged variant.

See [wallet-hierarchy-and-capital-flow.md](../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked via Alchemy RPC using `eth_feeHistory` (Ethereum mainnet). Atomic bundles are gas-intensive: ~500k
gas for entry (~$45 at 30 gwei), ~500k for exit. Slightly cheaper than hedged variant (no perp margin transfer or perp
trade). Gas hits P&L immediately as a realized transaction cost.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../cross-cutting/instrument-filtering.md). DEX
pools (swap leg) require BOTH sides to be in `DEFI_MAJOR_ASSET_SYMBOLS`. Both WETH and weETH are in the whitelist.
Lending markets (Aave V3) require the base asset to be major.

## Share Class

The unhedged recursive strategy is designed primarily for coin-denominated share classes:

| Share Class | Target Delta        | P&L Currency | Notes                                                               |
| ----------- | ------------------- | ------------ | ------------------------------------------------------------------- |
| `ETH`       | total_equity_in_eth | ETH          | Primary use case. Investor wants ETH + amplified yield.             |
| `BTC`       | total_equity_in_btc | BTC          | Cross-asset. weETH appreciation + BTC-denominated returns.          |
| `USDT`      | leveraged_long_eth  | USD          | Less common. Exposes to full leveraged ETH price risk in USD terms. |

For `ETH` share class, the investor measures performance in ETH. The leveraged weETH position means: if weETH staking
yield is 3.5% and leverage is 2.5x, the strategy adds ~8.75% ETH-denominated return per year beyond holding ETH.

For `USDT` share class, the strategy has significant directional risk. A 30% ETH drop with 2.5x leverage results in ~75%
portfolio drawdown (before HF-triggered deleverage). This share class should be offered only to clients who explicitly
want leveraged long ETH exposure.

See [cross-cutting/share-classes.md](../cross-cutting/share-classes.md) for the full cross-strategy specification.

## Comparison: Hedged vs Unhedged

| Dimension          | Hedged (default)                   | Unhedged (this strategy)        |
| ------------------ | ---------------------------------- | ------------------------------- |
| Net delta          | ~0 (market neutral)                | +leveraged ETH (directional)    |
| Perp venue         | Hyperliquid (SHORT)                | None                            |
| Funding income     | Yes (from perp hedge)              | No                              |
| Dominant P&L       | Yield (staking + funding - borrow) | Spot price movement             |
| Target APY         | 25-35% (yield only)                | 25-38% (yield + directional)    |
| Sharpe ratio       | ~2.0 (stable yield)                | ~0.8-1.5 (volatile directional) |
| Max drawdown       | ~15%                               | ~30%                            |
| Credentials needed | Wallet + Hyperliquid API           | Wallet only                     |
| Gas per entry      | ~$65 (bundle) + ~$17 (perp)        | ~$65 (bundle only)              |
| Ideal share class  | USDT (market neutral)              | ETH/BTC (coin + yield)          |

Both variants use the same `RecursiveStakedBasisStrategy` class. The `hedged` config parameter controls whether perp
instructions are emitted. Factory functions: `create_recursive_staked_basis_strategy()` (hedged=True) vs
`create_unhedged_recursive_strategy()` (hedged=False).

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_recursive_basis.py`
- **Factory:** `create_unhedged_recursive_strategy()`
- **Mixins:** `strategy-service/strategy_service/engine/strategies/_defi_recursive_basis_mixins.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md`
- **Aave connector:** `execution-service/protocols/aave.py`
- **EtherFi connector:** `execution-service/protocols/etherfi.py`
- **Morpho connector:** `execution-service/protocols/morpho.py`
- **Flash loan simulator:** `strategy-service/strategy_service/engine/backtest/flash_loan_simulator.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
- **Hedged variant doc:** [recursive-staked-basis.md](recursive-staked-basis.md)
