---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# DeFi Recursive Staked Basis

> **Asset class:** DeFi **Strategy type:** Leveraged Basis + LST Yield (flash loan amplified, atomic execution)
> **Strategy ID pattern:** `DEFI_ETH_RECURSIVE_BASIS_SCE_1H`

## Overview

The most complex DeFi strategy. Uses flash loans to create leveraged exposure to weETH staking yield while hedging delta
with a short perp. Flash borrow ETH, stake to weETH, deposit as Aave collateral, borrow ETH against it, repay flash loan
-- all in one atomic transaction. Net position: long leveraged weETH collateral, short ETH debt, short ETH perp.
Amplifies combined APY by leverage factor.

**WARNING:** This strategy involves liquidation risk. If health factor drops below 1.0, Aave liquidators will seize
collateral at a 5-10% penalty. Backtest liquidation enforcement is critical.

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

NON-ATOMIC (separate transactions):
Step 7 - TRANSFER:     USDC to Hyperliquid         (10% of USDT as margin)
Step 8 - TRADE:        Short ETH-USDC perp         (size = total_weeth * weeth_rate)
```

### Concrete Example (2.5x leverage, $10,000)

```
initial_usdt     = $10,000
spot_allocation  = $9,000 (90%)
margin           = $1,000 (10%)
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

After perp hedge:
  Perp short               = -7.5 ETH
  Margin                   = $1,000 USDC

Health Factor (standard) = ($22,500 * 0.775) / $13,500 = 1.29
Health Factor (E-Mode)   = ($22,500 * 0.95)  / $13,500 = 1.58  ← auto-detected for weETH/WETH
```

### Wallet After Deploy

```
AAVE_V3-ETHEREUM:A_TOKEN:AWEETH@ETHEREUM              = 7.246 weETH (collateral, positive)
AAVE_V3-ETHEREUM:DEBT_TOKEN:DEBTWETH@ETHEREUM          = 4.5 ETH    (debt, negative in equity)
HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID    = -7.5 ETH   (short)
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
Step 6 - TRADE:        Close perp short (buy to close)
Step 7 - SWAP:         Remaining WETH --> USDT (back to stablecoin)
```

## Data Architecture

| Dimension              | Value                                                                                                                                                                                                                        | SSOT                                                      |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)                                                                                                                                                                    | `strategy-service/config.py`                              |
| **Processed data**     | `market_data` dict: `eth_price`, `funding_rate`, `weeth_eth_rate`, `aave_borrow_apy_eth`, `aave_ltv`, `morpho_flash_loan_liquidity`, `health_factor`, `weekly_rewards`, `aave_liquidity_index`, `aave_liquidation_threshold` | Features hydrated alongside candles                       |
| **Features**           | `features` dict: all above keys                                                                                                                                                                                              | `features-onchain-service` + `features-delta-one-service` |
| **Interval**           | Time-driven (candle-based), not event-driven                                                                                                                                                                                 | `timeframe` in strategy config                            |
| **Lowest granularity** | 1H (currently hardcoded in factory, not configurable)                                                                                                                                                                        | `defi_recursive_basis.py` factory                         |
| **Execution mode**     | `same_candle_exit` — entry and exit can occur in same candle                                                                                                                                                                 | Strategy config                                           |

**Gap:** Timeframe is hardcoded to 1H. For health factor monitoring, sub-1H (15m or 5m) would be safer for detecting
rapid liquidation risk.

## Instrument Selection

**Currently: STATIC (hardcoded per config, no dynamic selection)**

All instruments are fixed at strategy initialisation:

- Collateral: `AAVE_V3-ETHEREUM:A_TOKEN:AWEETH@ETHEREUM` — always weETH as collateral
- Debt: `AAVE_V3-ETHEREUM:DEBT_TOKEN:DEBTWETH@ETHEREUM` — always borrow WETH
- Perp: `{perp_venue}:PERPETUAL:ETH-USDC@LIN@{perp_venue}` — venue configurable, instrument fixed
- Flash loan: Morpho Blue (0% fee) preferred over Aave (0.05%) or Balancer (0%)

There is **no dynamic collateral selection** — the strategy does NOT compare weETH vs wstETH as collateral, nor pick the
cheapest borrowing asset. This is a gap: a "recursive SOR" could optimise the leverage loop by selecting the best
collateral/debt pair across Aave markets.

**SSOT for instrument types per venue:** See
[`INSTRUMENT_TYPES_BY_VENUE`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**SOR is ON by default for the swap legs only.**

| Leg                               | SOR? | Allowed Venues                                          | SSOT                 |
| --------------------------------- | ---- | ------------------------------------------------------- | -------------------- |
| Step 3 (WETH→weETH swap)          | YES  | `CURVE-ETHEREUM`, `BALANCER-ETH`, `UNISWAP_V3-ETHEREUM` | `defi_base.py:84-86` |
| Step 1 (Flash borrow from Morpho) | NO   | Morpho Blue only (hardcoded)                            | —                    |
| Step 4 (Deposit to Aave)          | NO   | Aave V3 only                                            | —                    |
| Step 8 (Short perp)               | NO   | Hyperliquid only                                        | —                    |

SOR applies ONLY to the ETH→weETH swap within the atomic bundle. Flash loan provider, lending protocol, and perp venue
are all fixed.

**Same-wallet constraint:** All SOR venues must be on Ethereum mainnet (same ERC-20 wallet). SSOT:
[`SHARED_WALLET_GROUPS`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

**Execution boundary:** Strategy sends `StrategyInstruction` with `is_atomic=True` for the flash loan bundle.
Execution-service MUST execute all atomic steps in a single transaction — if any step fails, all revert. Non-atomic
steps (perp hedge) are separate instructions.

## Instruments

| Instrument Key                                   | Venue       | Type      | Role                              |
| ------------------------------------------------ | ----------- | --------- | --------------------------------- |
| `WALLET:SPOT_ASSET:USDT`                         | Wallet      | Spot      | Initial capital                   |
| `AAVE_V3-ETHEREUM:A_TOKEN:AWEETH@ETHEREUM`       | Aave V3     | aToken    | Collateral (long, leveraged)      |
| `AAVE_V3-ETHEREUM:DEBT_TOKEN:DEBTWETH@ETHEREUM`  | Aave V3     | debtToken | Debt (negative equity)            |
| `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID` | Hyperliquid | Perp      | Short leg (hedge, leveraged size) |

## Key Features Consumed

| Feature                       | Source Service     | SLA | Used For                          |
| ----------------------------- | ------------------ | --- | --------------------------------- |
| `lst_staking_apy`             | features-onchain   | 60s | Signal: staking yield component   |
| `funding_rate`                | features-delta-one | 10s | Signal: funding yield component   |
| `weeth_eth_rate`              | features-onchain   | 60s | Position sizing, rebalancing      |
| `aave_borrow_apy_eth`         | features-onchain   | 60s | Cost: leverage cost calculation   |
| `aave_ltv`                    | features-onchain   | 60s | Leverage cap: max safe LTV        |
| `morpho_flash_loan_liquidity` | features-onchain   | 60s | Pre-check: can we flash borrow?   |
| `health_factor`               | features-onchain   | 60s | Risk: liquidation proximity       |
| `weekly_rewards`              | features-onchain   | 24h | EtherFi/EIGEN reward distribution |
| `eth_price`                   | market-tick-data   | 1s  | PnL, sizing, HF calculation       |

## Hedged vs Unhedged Modes

The strategy supports two operating modes via `hedge_mode` config:

### Hedged (default, delta-neutral)

Full perp hedge: short perp sized at `total_weeth * weeth_rate`. Collects leveraged staking yield + leveraged funding
rate - borrow cost. This is the standard deployment -- delta-neutral with amplified yield.

### Unhedged (directional, long ETH)

No perp hedge: the strategy is long leveraged weETH and short ETH debt only. PnL is dominated by ETH price movement. Use
case: clients with a long-term bullish ETH view who want to amplify staking yield without funding rate dependency. Net
APY = `staking_apy * leverage - borrow_apy * (leverage - 1) + reward_yield * leverage`. Higher risk (no delta
neutrality), higher return in bull markets.

## Reward Mode (EIGEN / ETHFI Split)

The `reward_mode` config controls how EtherFi/EigenLayer reward distributions are handled:

| Mode    | Behavior                                    | Use Case                              |
| ------- | ------------------------------------------- | ------------------------------------- |
| `HOLD`  | Hold reward tokens (EIGEN, ETHFI) in wallet | Long-term accumulation                |
| `SELL`  | Immediately swap rewards to WETH via SOR    | Realize yield, compound into position |
| `SPLIT` | 50% hold / 50% sell (configurable ratio)    | Balanced approach                     |

Rewards are tracked as `SEASONAL_WEEKLY` settlement type. The `weekly_rewards` feature from features-onchain-service
provides the expected distribution amount for APY forecasting.

## Aave V3 E-Mode (Efficiency Mode)

When both collateral and debt are ETH-correlated (weETH collateral + WETH debt), the strategy auto-detects Aave V3
E-Mode via `get_emode_params()` from UAC. This provides dramatically higher LTV/liquidation parameters:

| Mode     | LTV   | Liq Threshold | Liq Bonus | Max Leverage (raw) |
| -------- | ----- | ------------- | --------- | ------------------ |
| Standard | 72.5% | 77.5%         | 7.5%      | 3.6x               |
| E-Mode   | 93%   | 95%           | 1%        | 14.3x              |

**Detection:** `_resolve_emode_params()` extracts asset symbols from instrument IDs, calls `get_emode_params()`. Dynamic
features from risk-and-exposure-service override E-Mode base values when present.

**Config max_leverage still caps:** Even with E-Mode allowing 14.3x, the strategy's `max_leverage` config (default 3.0)
and depeg tolerance cap apply. E-Mode means the protocol won't liquidate as aggressively, but the strategy stays
conservative by design.

## Depeg Tolerance as Leverage Cap

The weETH/ETH depeg tolerance functions as a **leverage cap** -- not an exit trigger (until emergency threshold). As
weETH depegs from its fair value (based on accumulated staking yield), the effective collateral value drops, reducing
health factor. The strategy uses depeg tolerance to dynamically cap leverage:

```
max_safe_leverage = liq_threshold / (1 - liq_threshold + depeg_tolerance)
```

**Three caps applied (most restrictive wins) in `_apply_ltv_leverage_cap()`:**

1. **LTV-based:** `1/(1 - LTV) * 0.85` safety buffer
2. **Depeg-based:** sizes leverage so `depeg_tolerance%` move won't trigger liquidation
3. **Config `max_leverage`** (hard cap, default 3.0)

| Depeg Tolerance | Standard Mode (liq=0.775) | E-Mode (liq=0.95) |
| --------------- | ------------------------- | ----------------- |
| 0%              | 3.44x                     | 20.0x             |
| 2% (default)    | 3.16x                     | 13.57x            |
| 3%              | 3.04x                     | 11.88x            |
| 5%              | 2.82x                     | 9.50x             |
| EMERGENCY EXIT  | ≥3% depeg                 | ≥3% depeg         |

This means depeg tolerance is a **sliding scale for leverage reduction**, not a binary exit signal. The strategy
gradually reduces leverage as depeg increases, maintaining HF > target. Only at the emergency threshold (default 3%)
does it trigger a full atomic unwind.

## Dual-Index Position Mechanics

aweETH has **two simultaneous yield sources**:

1. **weETH/ETH rate appreciation** (staking yield) -- the underlying weETH token appreciates
2. **Aave liquidity_index growth** (tiny supply interest) -- Aave pays interest on deposited collateral

The system tracks these via separate settlement types (`LST_YIELD` and `AAVE_INDEX`). They are orthogonal dimensions:

- LST_YIELD affects the **price** of the underlying (weETH rate)
- AAVE_INDEX affects the **quantity** of the aToken (scaled balance)

Composite value: `aweETH_value = weeth_amount * weeth_rate * eth_price * (current_liq_index / entry_liq_index)`

debtWETH grows independently via `variableBorrowIndex` -- this is the cost of leverage.

## PnL Attribution

| Component           | Settlement Type          | Mechanism                                                                         |
| ------------------- | ------------------------ | --------------------------------------------------------------------------------- |
| `staking_yield_pnl` | `LST_YIELD` (per candle) | `aweETH_amount * (weeth_rate_new - weeth_rate_old) / weeth_rate_old` -- LEVERAGED |
| `lending_yield_pnl` | `AAVE_INDEX` (supply)    | aweETH balance growth from liquidity_index (small)                                |
| `borrow_cost_pnl`   | `AAVE_INDEX` (borrow)    | debtWETH balance growth from borrow_index (NEGATIVE cost)                         |
| `funding_pnl`       | `FUNDING_8H`             | Short perp receives positive funding (LEVERAGED position)                         |
| `rewards_pnl`       | `SEASONAL_WEEKLY`        | EtherFi/EIGEN weekly distributions                                                |
| `trading_pnl`       | Entry/exit fills         | Realized from closing all legs                                                    |
| `transaction_costs` | Per-fill                 | Flash loan fee (Morpho=0%) + gas (~500k) + swap slippage                          |

**Source of truth:**

```
equity = aweETH_value - debtWETH_value + perp_pnl + margin - initial
```

The `_calculate_total_equity` function correctly subtracts debt tokens:

```
if ":DEBT_TOKEN:" in instrument_id:
    total -= abs(value)      # Debt is subtracted
else:
    total += value           # Everything else added
```

**Net APY formula (signal generation only):**

```
net_apy = (staking_apy + funding_apy + reward_yield) * leverage
        - borrow_apy * (leverage - 1)

Example: (3.5% + 8% + 2%) * 2.5 - 2% * 1.5 = 33.75% - 3% = 30.75% net
```

**Double-counting prevention:**

- aweETH collateral: weETH rate change (staking) and liquidity_index change (Aave supply) are tracked by separate
  settlement types and are orthogonal
- debtWETH: grows independently via borrow_index -- always negative (cost)
- Perp: sized at full leveraged ETH exposure, receives amplified funding
- Reconciliation: composite index check verifies expected vs actual value each candle

## Risk Profile

| Metric               | Target | Notes                                                         |
| -------------------- | ------ | ------------------------------------------------------------- |
| Target annual return | 25-35% | Leveraged staking + funding - borrow cost                     |
| Target Sharpe ratio  | 2.0+   | Higher absolute return but higher vol than unleveraged        |
| Max drawdown         | 15%    | Liquidation cascade is the tail risk                          |
| Max leverage         | 3.0x   | Capped by strategy; Aave allows up to ~5x in E-Mode           |
| Capital scalability  | $5M    | Constrained by Morpho flash loan liquidity + Aave utilization |

## Latency Profile

| Segment                             | p50 Target | p99 Target | Co-location Needed?                    |
| ----------------------------------- | ---------- | ---------- | -------------------------------------- |
| Market data -> feature              | 50ms       | 200ms      | No                                     |
| Feature -> signal                   | 10ms       | 50ms       | No                                     |
| Signal -> instruction               | 5ms        | 20ms       | No                                     |
| Instruction -> fill (atomic bundle) | 5s         | 60s        | No (gas-dependent, may need gas boost) |
| Instruction -> fill (perp)          | 100ms      | 500ms      | No (Hyperliquid CLOB)                  |
| **End-to-end**                      | **~6s**    | **~61s**   | **No**                                 |

Low-frequency (1h candles). Atomic bundle may need priority gas in congested conditions.

## Execution Details

- **Venues:** Morpho (flash loan), Aave V3 (collateral + borrow), Uniswap/Curve (swaps), Hyperliquid (perp)
- **Order types:** Atomic bundle (flash loan sequence), Market (swaps), Limit (perp)
- **Atomic execution required?** YES -- Steps 1-6 MUST be atomic. If any step fails, all revert.
- **Rebalancing triggers:**
  - Delta drift > 2%: adjust perp size
  - Health factor < 1.5: deleverage 20% (partial atomic unwind)
  - Health factor < 1.2: emergency full exit
  - weETH depeg > 2%: emergency full exit
- **Deleverage sequence:** Flash borrow WETH -> partial repay debt -> partial withdraw collateral -> swap weETH to WETH
  -> flash repay. Leverage decreases: `current_leverage *= (1 - 0.20)`
- **Gas budget:** ~500k gas for atomic bundle (entry), ~600k for exit (more steps)

### Rebalancing

**Trigger type:** Event-driven (NOT periodic). No rebalance without new market data.

| Level    | Position Deviation | Health Factor | Action                                   |
| -------- | ------------------ | ------------- | ---------------------------------------- |
| Minor    | >2% delta drift    | HF > 1.5      | LOG_ONLY                                 |
| Major    | >5% delta drift    | HF < 1.4      | REBALANCE — deleverage 20% + adjust perp |
| Critical | >10% delta drift   | HF < 1.25     | EMERGENCY_EXIT — full atomic unwind      |

**Additional rebalance triggers (unique to this strategy):**

- Dynamic LTV change: If Aave governance reduces weETH LTV, cap leverage accordingly
- Flash loan liquidity dry-up: If Morpho pool liquidity < required flash amount, deleverage
- weETH depeg >2%: Emergency exit regardless of HF

**Deleverage is itself an atomic bundle:** Flash borrow → partial repay debt → partial withdraw collateral → swap →
flash repay. This is expensive (~500k gas) so minor drifts are logged only.

Thresholds from `defi_base.py:_parse_thresholds()` + `defi_recursive_basis.py` health factor overrides. SSOT:
[`rebalancing_config.yaml`](../../../strategy-service/strategy_service/configs/rebalancing_config.yaml)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions → exposures) → RiskMonitor (exposures → risk assessment) → Strategy (risk
assessment → rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern        | Exposure Type                      | Used For               |
| ------------------------- | ---------------------------------- | ---------------------- |
| `AAVE_V3:A_TOKEN:*`       | Collateral value (leveraged weETH) | HF numerator           |
| `AAVE_V3:DEBT_TOKEN:*`    | Debt value (borrowed WETH)         | HF denominator         |
| `HYPERLIQUID:PERPETUAL:*` | Perp notional (short, leveraged)   | Delta calculation      |
| `WALLET:LST:*`            | Underlying LST appreciation        | Staking yield tracking |

Config: `defi_mode.enabled=True`, `defi_mode.track_aave_positions=True`, `defi_mode.track_staking_positions=True`,
`ml_mode.track_perp_positions=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type          | Subscribed?        | Threshold                                           | Action on Breach                 |
| ------------------ | ------------------ | --------------------------------------------------- | -------------------------------- |
| `aave_liquidation` | **YES (CRITICAL)** | HF < 1.5 deleverage, HF < 1.2 emergency exit        | Atomic deleverage bundle         |
| `delta`            | YES                | 2% net delta drift                                  | Adjust perp size                 |
| `funding`          | YES (signal)       | Net APY below threshold                             | Exit decision                    |
| `staking_yield`    | YES (signal)       | `min_staking_apy` config param                      | Exit decision                    |
| `borrow_cost`      | YES                | Borrow rate spike erodes net APY                    | Deleverage or exit               |
| `protocol_risk`    | YES                | weETH depeg > 2%, Morpho liquidity dry-up           | Emergency exit                   |
| `venue_protocol`   | YES                | Hyperliquid circuit breaker, Aave governance change | Pause/exit                       |
| `liquidity`        | YES                | Flash loan liquidity < required amount              | Cannot rebalance/exit atomically |
| `basis`            | NO                 | —                                                   | —                                |

Config: `enabled_risk_types: ["aave_liquidation"]`, `defi_risk.enabled=True`, `defi_risk.aave_liquidation=True`,
`cex_risk.enabled=True` Strategy-specific: `min_health_factor=1.2`, `target_health_factor=1.5` (lines 81-82 in
`defi_recursive_basis.py`) SSOT: [`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

**Gap:** Risk subscriptions are implicit in code defaults. Plan item `p5-risk-strategy-subscription` will create
`StrategyRiskProfile` per strategy type. This strategy has the MOST subscriptions of all 4 DeFi strategies.

### Custom Strategy Risk Types

| Custom Risk                        | What It Measures                                                        | Evaluation Method  |
| ---------------------------------- | ----------------------------------------------------------------------- | ------------------ |
| ETH borrow rate sensitivity        | PnL impact of +100bp borrow rate on leveraged position                  | `rate_sensitivity` |
| Health factor degradation velocity | Rate of HF decline → time-to-liquidation estimate                       | `threshold_breach` |
| Flash loan liquidity risk          | Morpho pool liquidity vs required flash amount                          | `threshold_breach` |
| Recursive leverage amplification   | How leverage multiplies losses in stress scenario                       | `scenario_pnl`     |
| weETH depeg cascade                | weETH depeg → HF drop → forced deleverage → more selling → deeper depeg | `scenario_pnl`     |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented. This strategy has the most
custom risk needs of all 4 DeFi strategies due to leverage.

## Margin & Liquidation

- **Margin model:** Aave V3 health factor (DeFi side) + Hyperliquid cross-margin (perp side)
- **Health factor:** `HF = (collateral_value * liquidation_threshold) / debt_value`
  - Default liquidation_threshold for weETH: 0.825 (82.5%)
  - Default LTV: 0.50 (50%)
  - E-Mode (ETH-correlated): LTV up to ~90%, liq threshold ~93%
- **Liquidation penalty:** 5-10% of collateral (asset-dependent)
- **Liquidation trigger:** HF < 1.0
- **Strategy thresholds:**
  - HF < 1.5: deleverage 20%
  - HF < 1.2: emergency full exit
- **Monitoring:** Health factor checked EVERY candle (critical for this strategy)
- **Backtest enforcement:** If HF < 1.0 in backtest, forced exit with penalty applied (plan item
  p5-backtest-liquidation-enforcement)

### What Causes Health Factor to Drop

1. **ETH price drops** -- collateral (weETH) loses value faster than debt (in ETH terms, net effect is the weETH/ETH
   rate component only)
2. **weETH depegs** -- collateral drops relative to debt (most dangerous scenario)
3. **Borrow rate spikes** -- debt grows faster than expected
4. **Aave parameter changes** -- governance reduces LTV or liquidation threshold

## Authentication & Credentials

| Venue                     | Secret Name                   | Testnet Available? | Notes                                  |
| ------------------------- | ----------------------------- | ------------------ | -------------------------------------- |
| Morpho (flash loan)       | `alchemy-api-key` (RPC)       | Yes (Sepolia)      | No API key needed; interact via wallet |
| Aave V3 (collateral/debt) | `alchemy-api-key` (RPC)       | Yes (Sepolia)      | Permissionless via wallet              |
| Uniswap (swaps)           | `alchemy-api-key` (RPC)       | Yes (Sepolia)      | Permissionless via wallet              |
| Hyperliquid               | `hyperliquid-api-credentials` | Yes (testnet)      | API key + secret                       |
| Wallet                    | `wallet-{client}-private-key` | Yes (dev wallet)   | Signs ALL on-chain transactions        |

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Client Onboarding

See [cross-cutting/client-onboarding.md](../../../08-workflows/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Wallet per client (signs atomic bundles -- MUST have sufficient ETH for gas)
2. Hyperliquid account per client (separate margin)
3. Config: `initial_capital`, `max_leverage` (default 2.5x), `min_health_factor` (default 1.5)
4. **Restart required?** No -- hot-reload via GCS config
5. **Gas funding:** Client wallet needs ~0.1 ETH pre-funded for gas on atomic bundles

### Higher Risk -- Additional Onboarding Steps

- Client must acknowledge liquidation risk
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
- **Dual-index decomposition** -- weETH rate growth vs Aave liquidity_index growth (shows which yield source dominates)
- **Net APY waterfall** -- staking + funding + rewards - borrow_cost = net APY (per candle)
- **Flash loan execution log** -- entry/exit bundle success/failure, gas used, Morpho liquidity at time
- **Deleverage history** -- when and why deleverage events fired, HF before/after

## Testing Stage Status

| Stage        | Status  | Notes                                                                 |
| ------------ | ------- | --------------------------------------------------------------------- |
| MOCK         | Pending | Need MockDeFiDynamics with HF degradation scenarios                   |
| HISTORICAL   | Pending | Need 365 days data (must see at least one market stress event)        |
| LIVE_MOCK    | Pending | Blocked by features-onchain health_factor + aave_borrow_apy (#6)      |
| LIVE_TESTNET | Pending | Blocked by AAVEConnector live execution (#1) + testnet contracts (#3) |
| BATCH_REAL   | Pending | Blocked by historical APY storage (#4) + liquidation enforcement (p5) |
| STAGING      | Pending | Tenderly fork (atomic bundles execute against fork)                   |
| LIVE_REAL    | Pending | All above + real capital approval + client risk acknowledgment        |

## Wallet & Capital Flow

| Component        | Value                                                                              |
| ---------------- | ---------------------------------------------------------------------------------- |
| Treasury reserve | 20% of AUM                                                                         |
| Hot wallet       | Per-chain, per-strategy isolated                                                   |
| CeFi sub-account | Yes (Hyperliquid -- perp margin)                                                   |
| Bridge required  | No (single-chain -- Ethereum mainnet)                                              |
| Flash loan       | Morpho Blue (0% fee) / AAVE (0.05% fee) -- protocol provides and repays atomically |
| Custody          | Copper MPC                                                                         |

Capital flow: Client deposit --> treasury --> hot wallet --> SWAP to WETH + FLASH BORROW (atomic bundle: flash borrow,
swap to weETH, deposit to Aave, borrow WETH, repay flash) + TRANSFER USDC to Hyperliquid (margin). Flash loan amount is
NOT from wallet -- protocol provides and repays within a single atomic transaction. Rebalance: treasury < 10% -->
strategy reduces position --> atomic deleverage bundle + close perp --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked via Alchemy RPC using `eth_feeHistory` (Ethereum mainnet). The MTDS `gas_fee_handler` fetches
real-time gas prices and writes them as features. Gas hits P&L immediately as a realized transaction cost -- not
estimated. Atomic bundles are gas-intensive: ~500k gas for entry (~$45 at 30 gwei), ~600k for exit. Gas is a significant
cost component that must be recovered by the leveraged yield within the first few hours of deployment.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). DEX
pools (swap leg) require BOTH sides to be in `DEFI_MAJOR_ASSET_SYMBOLS`. Both WETH and weETH are in the whitelist.
Lending markets (Aave V3) require the base asset to be major. Perps use the CeFi base asset universe.

## E2E Manual Trading Workflow

Step-by-step manual recreation of the recursive staked basis strategy. Uses atomic flash loan for leveraged entry.

### Prerequisites

- Treasury wallet funded with USDC/ETH on Ethereum
- Hyperliquid account for perp hedge
- FlashLoanReceiver contract deployed (or use Instadapp DSA)
- Alchemy RPC for Ethereum

### Step-by-Step (Atomic Deploy Sequence)

All steps 3-8 execute atomically in a single transaction via flash loan:

| Step                    | Action                                      | Instruction Type | Service                           | Instant P&L            |
| ----------------------- | ------------------------------------------- | ---------------- | --------------------------------- | ---------------------- |
| 1                       | Observe treasury balance                    | —                | position-balance-monitor          | —                      |
| 2                       | Transfer ETH from treasury → trading wallet | TRANSFER         | execution-service                 | Gas: ~$2               |
| **Atomic Bundle Start** |                                             |                  |                                   |                        |
| 3                       | Flash borrow ETH from Morpho (0% fee)       | FLASH_BORROW     | execution-service                 | $0 (no fee)            |
| 4                       | Swap USDC → ETH (90% of wallet)             | SWAP             | execution-service (SOR)           | Slippage: ~5 bps       |
| 5                       | Swap ETH → weETH (EtherFi staking)          | SWAP             | execution-service                 | Slippage: ~20-35 bps   |
| 6                       | Deposit weETH as collateral in AAVE V3      | LEND             | execution-service (AaveConnector) | Gas included in bundle |
| 7                       | Borrow ETH from AAVE against weETH          | BORROW           | execution-service (AaveConnector) | Gas included           |
| 8                       | Repay flash loan with borrowed ETH          | FLASH_REPAY      | execution-service                 | $0                     |
| **Atomic Bundle End**   |                                             |                  | Total bundle gas: ~$50-80         |                        |
| 9                       | Transfer margin USDC → Hyperliquid          | TRANSFER         | execution-service                 | $0                     |
| 10                      | Short ETH perp on Hyperliquid (delta hedge) | TRADE            | execution-service                 | Fee: ~3-8 bps          |

### Position State After Deployment

- AAVE collateral: ~120 aWEETH ($360K at 2.5x leverage)
- AAVE debt: ~96 ETH ($288K borrowed)
- Hyperliquid: -96 ETH SHORT (delta hedge)
- Health Factor: ~1.52
- LTV: 80% (target, capped by depeg tolerance)
- Net delta: ~0 (hedged mode) or +120 ETH (unhedged mode)

### Instant P&L

- Flash loan: $0 (Morpho 0% fee)
- Swap slippage (USDC→ETH): ~$18 (5 bps on $360K)
- Swap slippage (ETH→weETH): ~$90 (25 bps on $360K)
- Atomic bundle gas: ~$65
- Perp trade fee: ~$17 (6 bps on $288K)
- Total entry cost: ~$190

### Leverage Cap (Depeg Tolerance + E-Mode)

**Four caps applied in `_apply_ltv_leverage_cap()` (most restrictive wins):**

1. **LTV cap:** `1/(1-LTV) * 0.85` safety buffer
2. **Spread-move cap:** `liq_threshold / (1 - liq_threshold + max_spread_move)`
   - Defaults from UAC `MAX_UNDERLYING_MOVES[base_currency].max_spread_move` (ETH=3%, SOL=5%)
   - Override via `max_depeg_tolerance` config
3. **Outright-move cap:** `(1 - maint_margin) / max_outright_move`
   - Caps the perp hedge leg: if ETH can crash 30%, max leverage ~3.17x
   - Defaults from UAC `MAX_UNDERLYING_MOVES[base_currency].max_outright_move`
   - Override via `max_outright_move` config
4. **Config `max_leverage`** (hard cap, default 3.0)

| Move Type | ETH Default          | BTC Default | SOL Default        |
| --------- | -------------------- | ----------- | ------------------ |
| Outright  | 30% → 3.17x          | 25% → 3.8x  | 40% → 2.38x        |
| Spread    | 3% → 11.88x (E-Mode) | 2% → —      | 5% → 9.5x (E-Mode) |

**SSOT:** `unified_api_contracts.registry.max_underlying_moves.MAX_UNDERLYING_MOVES`

### Ongoing P&L (Daily)

- Staking yield (weETH): 3.5% APY × 2.5x = 8.75%
- Funding income (perp hedge): 5.0% APY
- EtherFi rewards (EIGEN + ETHFI): 3.0% APY × 2.5x = 7.5%
- Borrow cost (AAVE ETH): -3.0% APY × 1.5x = -4.5%
- **Net APY: ~21.75%** on $144K base capital
- Daily: ~$85.89
- Cost recovery: ~2.2 days

### Reward Mode (P&L Attribution)

- `reward_mode="all"`: EIGEN + ETHFI rewards included
- `reward_mode="eigen_only"`: only EIGEN (lower but more conservative)
- `reward_mode="ethfi_only"`: only ETHFI

### Risk Metrics

- Health Factor: monitored every candle. Deleverage at HF < 1.4. Emergency exit at HF < 1.25.
- LTV: 80% target. Max safe = `1/(1-ltv) * 0.85`
- weETH/ETH depeg: 2% tolerance → sizes leverage to survive 2% move
- Liquidation price: where HF hits 1.0 (computed from collateral/debt/liq_threshold)

### Exit Workflow (Atomic Unwind)

| Step | Action                          | Instruction Type |
| ---- | ------------------------------- | ---------------- |
| 1    | Flash borrow ETH                | FLASH_BORROW     |
| 2    | Repay AAVE debt                 | REPAY            |
| 3    | Withdraw weETH collateral       | WITHDRAW         |
| 4    | Swap weETH → ETH                | SWAP             |
| 5    | Repay flash loan                | FLASH_REPAY      |
| 6    | Close perp SHORT (buy to close) | TRADE            |
| 7    | Swap ETH → USDC                 | SWAP             |
| 8    | Transfer USDC → treasury        | TRANSFER         |

### Trade History (Expected Output)

| #   | Time  | Type         | Instrument  | Amount    | Gas | Slippage | Running P&L |
| --- | ----- | ------------ | ----------- | --------- | --- | -------- | ----------- |
| 1   | 10:01 | TRANSFER     | ETH         | $144K     | $2  | $0       | -$2         |
| 2   | 10:02 | FLASH_BORROW | ETH         | 96 ETH    | $0  | $0       | -$2         |
| 3   | 10:02 | SWAP         | ETH/USDC    | 120 ETH   | —   | -$18     | -$20        |
| 4   | 10:02 | SWAP         | weETH/ETH   | 120 weETH | —   | -$90     | -$110       |
| 5   | 10:02 | LEND         | aWEETH      | 120       | —   | $0       | -$110       |
| 6   | 10:02 | BORROW       | ETH         | 96        | —   | $0       | -$110       |
| 7   | 10:02 | FLASH_REPAY  | ETH         | 96        | $65 | $0       | -$175       |
| 8   | 10:03 | TRANSFER     | USDC        | $10K      | $0  | $0       | -$175       |
| 9   | 10:03 | TRADE        | ETH-PERP    | -96 SHORT | $0  | —        | -$192       |
| EOD | —     | STAKING      | weETH       | +$34.52   | $0  | $0       | -$157.48    |
| EOD | —     | FUNDING      | Perp        | +$39.45   | $0  | $0       | -$118.03    |
| EOD | —     | BORROW       | ETH debt    | -$23.67   | $0  | $0       | -$141.70    |
| EOD | —     | REWARDS      | EIGEN+ETHFI | +$29.59   | $0  | $0       | -$112.11    |

## Collateral Haircuts

Aave V3 applies different loan-to-value (LTV) ratios and liquidation thresholds per collateral asset. These determine
the maximum leverage achievable for each collateral type.

| Collateral | LTV   | Liquidation Threshold | Max Leverage (theoretical) | Notes                                        |
| ---------- | ----- | --------------------- | -------------------------- | -------------------------------------------- |
| weETH      | 72.5% | 75%                   | 3.636x                     | Default for EtherFi staking.                 |
| wstETH     | 79.5% | 82%                   | 4.88x                      | Higher LTV due to deeper Lido liquidity.     |
| WETH       | 82.5% | 85%                   | 5.71x                      | Highest LTV. No staking yield on collateral. |

Formula: `max_leverage = 1 / (1 - LTV)`. In practice, the strategy caps leverage below the theoretical maximum to
maintain a health factor buffer. With the default `target_health_factor=1.5`, effective leverage is significantly lower
than the theoretical max.

The collateral choice (weETH vs wstETH vs WETH) trades off between staking yield and leverage capacity. weETH earns the
highest combined yield (staking + EtherFi rewards) but has the lowest LTV. WETH has no staking yield but allows the
highest leverage -- useful when funding rate alone justifies the strategy.

## Health Factor Monitoring

Health factor monitoring runs on a sub-5-minute cycle for this strategy, tighter than the standard 1H candle interval.
This is critical because leveraged positions can approach liquidation rapidly during volatile markets.

| Health Factor | Severity  | Action                                                                |
| ------------- | --------- | --------------------------------------------------------------------- |
| HF > 2.0      | HEALTHY   | No action. Strategy operates normally.                                |
| HF 1.5 - 2.0  | WARNING   | Log alert. Reduce new entries. Monitor every 2 minutes.               |
| HF 1.3 - 1.5  | CRITICAL  | Deleverage 20% via atomic bundle. Alert sent to client.               |
| HF 1.1 - 1.3  | EMERGENCY | Full emergency deleverage. Atomic unwind of all Aave positions.       |
| HF < 1.1      | IMMINENT  | Emergency exit all legs (Aave + perp). Accept slippage, priority gas. |

The monitoring interval tightens as health factor degrades:

- HF > 2.0: check every candle (1H)
- HF 1.5-2.0: check every 2 minutes
- HF < 1.5: check every 30 seconds (block-level for DeFi)

Health factor is computed from on-chain data: `HF = (collateral_value * liquidation_threshold) / total_debt_value`. The
`features-onchain-service` provides `health_factor` as a pre-computed feature. The strategy also computes a local
estimate between feature updates using cached collateral and debt values with live price feeds.

## MEV Protection

Atomic bundles (flash loan entry/exit) are vulnerable to MEV extraction -- sandwich attacks can front-run the swap legs
within the bundle. The strategy uses tiered MEV protection based on the execution environment.

| Environment     | MEV Protection Method | Notes                                                         |
| --------------- | --------------------- | ------------------------------------------------------------- |
| Mainnet (live)  | Flashbots relay       | Bundles submitted via `eth_sendBundle` to Flashbots builders. |
| L2 (Arbitrum)   | Private mempool       | MEV Blocker RPC endpoint for sequencer-level protection.      |
| Testnet / Paper | NoProtection          | No MEV on testnets. Paper mode uses Tenderly fork.            |

Flashbots relay ensures atomic bundles are not visible in the public mempool. The strategy's execution-service
integration submits the bundle directly to block builders, who include it atomically or not at all. This eliminates
sandwich risk on the swap legs.

For L2 deployments (future), private mempool via MEV Blocker (`rpc.mevblocker.io`) routes transactions through a
protected sequencer path. The protection method is configurable via `mev_protection` in strategy config.

## Emergency Exit Cost Estimation

Before deploying capital, the strategy estimates the cost of an emergency exit. Deployment is blocked if:

```
expected_annual_yield < emergency_close_cost * annualization_factor
```

Where `annualization_factor` defaults to 4 (meaning: the strategy must earn back emergency exit cost within 3 months).

Emergency exit cost components:

- Flash loan fee: $0 for Morpho, 0.05% of flash amount for Aave fallback
- Gas for atomic unwind bundle: estimated from current gas price and ~600k gas units
- Swap slippage on weETH to WETH: estimated from current pool depth and position size
- Perp close slippage: estimated from Hyperliquid orderbook depth
- Priority gas premium: 2x base gas for time-critical exits

The estimation runs at signal time (before `DEPLOY` instruction emission). If the estimated emergency cost exceeds the
threshold, the strategy logs a `DEPLOYMENT_BLOCKED_HIGH_EXIT_COST` event and waits for conditions to improve (typically:
lower gas prices or deeper liquidity).

## Share Class

The recursive staked basis supports the same share classes as the other basis strategies. Note that recursive leverage
amplifies the share class delta -- rebalance thresholds may need to be tighter for leveraged positions.

| Share Class | Target Delta             | P&L Currency | Notes                                                                               |
| ----------- | ------------------------ | ------------ | ----------------------------------------------------------------------------------- |
| `USDT`      | 0 (fully market neutral) | USD          | Default. Leveraged weETH long + perp short cancel. Pure leveraged yield harvesting. |
| `ETH`       | total_equity_in_eth      | ETH          | Perp hedge removes basis risk but preserves leveraged ETH exposure.                 |
| `BTC`       | total_equity_in_btc      | BTC          | Same pattern. Less common for recursive strategies.                                 |

For `USDT` share class, the leveraged position is delta-neutral in USD terms. For `ETH` share class, the perp hedge
removes basis risk but the amplified staking yield accrues as ETH-denominated return. The FX factor separates
base-currency conversion from the leveraged staking + funding P&L in attribution.

Because leverage amplifies delta drift from weETH rate changes, the rebalance deviation threshold should be tighter than
unleveraged strategies (e.g., 1.5% instead of 2% for a 2.5x leveraged position).

See [cross-cutting/share-classes.md](../cross-cutting/share-classes.md) for the full cross-strategy specification.

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_recursive_basis.py`
- **Mixins:** `strategy-service/strategy_service/engine/strategies/_defi_recursive_basis_mixins.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md`
- **Aave connector:** `execution-service/protocols/aave.py`
- **EtherFi connector:** `execution-service/protocols/etherfi.py`
- **Morpho connector:** `execution-service/protocols/morpho.py`
- **Flash loan simulator:** `strategy-service/strategy_service/engine/backtest/flash_loan_simulator.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
- **Yield reconciliation:** `execution-service/execution_service/services/yield_recon_engine.py`
