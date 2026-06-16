---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# SOL Staked Basis Trade (Marinade mSOL + Drift)

> **Asset class:** DeFi **Strategy type:** Basis + LST Yield (delta-neutral with staking enhancement) **Strategy ID
> pattern:** `DEFI_SOL_STAKED_BASIS_DRIFT_1H`

## Overview

Enhanced SOL basis trade: stake SOL via Marinade Finance to receive mSOL (liquid staking token, ~7% APY from Solana
validator rewards), then short SOL-PERP on Drift. Collects staking yield (~7%) on top of Drift funding rate (~15-30%),
for a combined target of 22-37% APY. Delta-neutral with higher combined APY than plain SOL basis.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDC  (100% USDC)

Step 1 - SWAP:     USDC --> SOL          (85% of capital, via Jupiter aggregator)
Step 2 - STAKE:    SOL --> mSOL          (Marinade liquid staking, instant via stake pool)
Step 3 - DEPOSIT:  USDC --> Drift margin (15% to Drift as perp margin)
Step 4 - TRADE:    Short SOL-PERP        (size = sol_amount from step 1, on Drift)

Wallet after deploy:
  - MARINADE-SOLANA:LST:MSOL             = msol_amount  (long, appreciating ~7% APY)
  - DRIFT-SOLANA:PERPETUAL:SOL-PERP      = -sol_amount  (short)
  - Drift margin                         = 15% USDC

Net delta = 0 (long mSOL SOL-equivalent exposure + short perp cancel)
```

## Instruments

| Instrument Key                    | Venue    | Type | Role                    |
| --------------------------------- | -------- | ---- | ----------------------- |
| `WALLET:SPOT_ASSET:USDC`          | Wallet   | Spot | Initial capital         |
| `MARINADE-SOLANA:LST:MSOL`        | Marinade | LST  | Long leg (appreciating) |
| `DRIFT-SOLANA:PERPETUAL:SOL-PERP` | Drift    | Perp | Short leg (hedge)       |

## Key Features Consumed

| Feature              | Source Service     | SLA | Used For                             |
| -------------------- | ------------------ | --- | ------------------------------------ |
| `msol_staking_apy`   | features-onchain   | 60s | Signal: entry if staking APY >= 5%   |
| `drift_funding_rate` | features-delta-one | 30s | Signal: entry if combined APY >= 15% |
| `msol_sol_rate`      | features-onchain   | 60s | Position sizing, rebalancing trigger |
| `sol_price`          | market-tick-data   | 1s  | PnL, sizing                          |

## Data Architecture

| Dimension              | Value                                                                      | SSOT                                                      |
| ---------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)                  | `strategy-service/config.py`                              |
| **Processed data**     | `market_data` dict: `sol_price`, `drift_funding_rate`, `msol_sol_rate`     | Features hydrated alongside candles                       |
| **Features**           | `features` dict: `msol_staking_apy`, `drift_funding_rate`, `msol_sol_rate` | `features-onchain-service` + `features-delta-one-service` |
| **Interval**           | Time-driven (candle-based), not event-driven                               | `timeframe` in strategy config                            |
| **Lowest granularity** | 1H (configurable via strategy config)                                      | `defi_sol_staked_basis.py` factory                        |
| **Execution mode**     | `same_candle_exit` -- entry and exit can occur in same candle              | Strategy config                                           |

## Instrument Selection

**Currently: STATIC (hardcoded per config, no dynamic selection)**

Instruments are set at strategy initialisation and never change:

- LST: `MARINADE-SOLANA:LST:MSOL` -- always mSOL (not jitoSOL, not bSOL, not stSOL)
- Perp: `DRIFT-SOLANA:PERPETUAL:SOL-PERP` -- always SOL-PERP on Drift

There is **no dynamic LST selection** -- the strategy does NOT compare mSOL vs jitoSOL vs bSOL staking yields and pick
the best one. This is a gap: an "LST SOR" could select the highest-yielding Solana LST that meets liquidity and depeg
risk thresholds.

**SSOT for instrument types per venue:** See
[`INSTRUMENT_TYPES_BY_VENUE`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**SOR is ON by default for the swap leg only.**

| Leg                      | SOR? | Allowed Venues                 | SSOT                              |
| ------------------------ | ---- | ------------------------------ | --------------------------------- |
| Step 1 (USDC->SOL swap)  | YES  | `JUPITER-SOLANA` (aggregator)  | `defi_sol_staked_basis.py:swap()` |
| Step 2 (SOL->mSOL stake) | NO   | Marinade only (direct staking) | --                                |
| Step 4 (Short perp)      | NO   | Drift only (on-chain CLOB)     | --                                |

Jupiter handles multi-venue routing natively across Raydium, Orca, and other Solana DEXes. Marinade staking is direct
(no SOR needed -- it is a stake pool, not a swap).

**Same-wallet constraint:** All Solana operations use the same wallet. SSOT:
[`SHARED_WALLET_GROUPS`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## mSOL Mechanics

mSOL is a **non-rebasing** liquid staking token from Marinade Finance. Your token count stays fixed after staking. The
mSOL/SOL exchange rate increases over time as Solana validator rewards accrue (~0.019% per day, ~7% APY).

- **Rate tracking:** `msol_sol_rate` starts at ~1.18 (as of early 2026) and grows monotonically
- **Yield source:** Solana validator staking rewards (consensus layer) distributed across Marinade's 400+ validator set
- **Instant stake/unstake:** Marinade offers instant liquid staking via the stake pool (no unbonding period for liquid
  staking)
- **Delayed unstake:** 1-2 epoch wait (~2-4 days) for native unstaking at exact rate (no slippage)

This means delta drift: as mSOL appreciates vs SOL, the SOL-equivalent exposure grows, creating a mismatch against the
fixed-size perp short. Strategy rebalances by adjusting perp size:
`target_perp_size = -(msol_balance * current_msol_rate)`.

## PnL Attribution

| Component           | Settlement Type                | Mechanism                                                                 |
| ------------------- | ------------------------------ | ------------------------------------------------------------------------- |
| `staking_yield_pnl` | `LST_YIELD` (per candle)       | `position_size * (msol_rate_new - msol_rate_old) / msol_rate_old`         |
| `funding_pnl`       | `FUNDING_1H` (hourly on Drift) | Short perp receives positive funding                                      |
| `trading_pnl`       | Entry/exit fills               | Price difference on swaps                                                 |
| `transaction_costs` | Per-fill                       | Jupiter swap fee + Marinade stake fee (0%) + Solana gas + Drift taker fee |

**Source of truth:** `total_pnl = msol_amount * msol_rate * sol_price - perp_loss + margin - initial`

**Combined APY calculation (signal generation only, NOT used for PnL):**

```
combined_apy = msol_staking_apy + (drift_funding_rate * 24 * 365)
Entry: combined_apy >= 15% AND msol_staking_apy >= 5%
Exit:  combined_apy drops 60% OR mSOL depegs > 3%
```

**Double-counting prevention:** LST_YIELD settlement does NOT adjust position size -- it only records yield for
attribution. The actual value change comes through mSOL rate (price) updates. Balance-based equity is the reconciliation
anchor.

## Risk Profile

| Metric               | Target | Notes                                                            |
| -------------------- | ------ | ---------------------------------------------------------------- |
| Target annual return | 22-37% | Staking ~7% + funding ~15-30%                                    |
| Target Sharpe ratio  | 2.5+   | Higher than plain SOL basis due to staking floor                 |
| Max drawdown         | 5%     | mSOL depeg is primary risk (historically stable, max 1.5% depeg) |
| Max leverage         | 1x     | No leverage (spot LST + perp hedge)                              |
| Capital scalability  | $5M    | mSOL liquidity is deep (~$1.5B TVL in Marinade)                  |

## Latency Profile

| Segment                     | p50 Target | p99 Target | Co-location Needed?   |
| --------------------------- | ---------- | ---------- | --------------------- |
| Market data -> feature      | 30ms       | 150ms      | No                    |
| Feature -> signal           | 10ms       | 50ms       | No                    |
| Signal -> instruction       | 5ms        | 20ms       | No                    |
| Instruction -> fill (swap)  | 500ms      | 3s         | No (Solana on-chain)  |
| Instruction -> fill (stake) | 500ms      | 2s         | No (Marinade instant) |
| Instruction -> fill (perp)  | 500ms      | 3s         | No (Drift on-chain)   |
| **End-to-end**              | **~2s**    | **~8s**    | **No**                |

Low-frequency (1H candles). Solana's 400ms block time makes all operations fast. Co-location provides no benefit.

## Execution Details

- **Venues:** Jupiter (spot swap aggregator), Marinade (liquid staking), Drift (perp)
- **Order types:** Market (swap via Jupiter), Direct (Marinade stake pool), Limit (perp on Drift CLOB)
- **Atomic execution required?** No -- legs are independent (swap, stake, and perp are separate Solana programs)
- **Gas budget:** ~0.001 SOL per transaction (~$0.15), ~0.004 SOL per full deploy (swap + stake + deposit + perp)

### Rebalancing

**Trigger type:** Event-driven (NOT periodic). No rebalance without new market data.

| Level    | Position Deviation | Action         | Notes                                |
| -------- | ------------------ | -------------- | ------------------------------------ |
| Minor    | >2% delta drift    | LOG_ONLY       | Log deviation, no action             |
| Major    | >5% delta drift    | REBALANCE      | Adjust perp size via Drift order     |
| Critical | >10% delta drift   | EMERGENCY_EXIT | Full exit: unstake mSOL + close perp |

**Delta drift source:** mSOL appreciation causes SOL-equivalent exposure to grow while perp size stays fixed. Target
perp size = `-(msol_balance * current_msol_rate)`.

**Rebalance action:** Minor rebalance adjusts perp size only (cheap, Drift order ~0.001 SOL gas). Major rebalance may
partial unwind + re-enter if mSOL depegs.

Thresholds from `defi_base.py:_parse_thresholds()`. SSOT:
[`rebalancing_config.yaml`](../../../strategy-service/strategy_service/configs/rebalancing_config.yaml)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern                | Exposure Type                  | Used For                                  |
| --------------------------------- | ------------------------------ | ----------------------------------------- |
| `MARINADE-SOLANA:LST:MSOL`        | LST value (long, appreciating) | Delta calculation, staking yield tracking |
| `DRIFT-SOLANA:PERPETUAL:SOL-PERP` | Perp notional (short)          | Delta calculation                         |

Config: `defi_mode.enabled=True`, `solana_mode.enabled=True`, `defi_mode.track_staking_positions=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type        | Subscribed?       | Threshold                                     | Action on Breach        |
| ---------------- | ----------------- | --------------------------------------------- | ----------------------- |
| `delta`          | YES               | 2% net delta drift (from mSOL appreciation)   | Adjust perp size        |
| `funding`        | YES (signal only) | `min_combined_apy` config param (default 15%) | Entry/exit decision     |
| `staking_yield`  | YES               | `min_staking_apy` config param (default 5%)   | Exit if yield collapses |
| `protocol_risk`  | YES               | mSOL depeg > 3% OR Marinade exploit           | Emergency exit          |
| `venue_protocol` | YES               | Drift program halt / Solana outage            | Pause trading           |
| `liquidity`      | NO                | --                                            | --                      |
| `borrow_cost`    | NO                | --                                            | No borrowing            |

Config: `enabled_risk_types: ["solana_defi"]`, `defi_risk.enabled=True`, `defi_risk.track_staking_positions=True` SSOT:
[`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

**Gap:** Risk subscriptions are implicit in code defaults, not in a machine-readable YAML registry. Plan item
`p5-risk-strategy-subscription` will create `StrategyRiskProfile` per strategy type.

### Custom Strategy Risk Types

| Custom Risk                 | What It Measures                                         | Evaluation Method  | SSOT          |
| --------------------------- | -------------------------------------------------------- | ------------------ | ------------- |
| mSOL depeg risk             | mSOL/SOL rate drops below fair value (loss of peg)       | `threshold_breach` | Strategy YAML |
| Combined APY collapse       | Staking + funding falls below min_combined_apy           | `rate_sensitivity` | Strategy YAML |
| Marinade validator slashing | Validator penalties reduce staking yield below threshold | `threshold_breach` | Strategy YAML |
| Solana network congestion   | Tx landing rate drops below 80% (degraded execution)     | `threshold_breach` | Strategy YAML |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** Drift cross-margin on perp side only
- **Health factor threshold:** N/A (no lending positions -- mSOL is held in wallet, not as collateral)
- **Liquidation risk:** Drift margin liquidation if basis widens beyond margin buffer (15% USDC)
- **mSOL depeg risk:** If mSOL/SOL rate drops > 3% from fair value, strategy exits immediately
- **Liquidation penalty:** ~5% of position value on Drift
- **Monitoring:** mSOL rate + Drift margin usage checked per candle, alert at >75% utilisation

## Authentication & Credentials

| Venue    | Secret Name                      | Testnet Available? | Notes                                      |
| -------- | -------------------------------- | ------------------ | ------------------------------------------ |
| Jupiter  | `solana-rpc-url` (Helius/Triton) | Yes (devnet)       | Read: public RPC. Write: wallet signs tx   |
| Marinade | `solana-rpc-url` (same)          | Yes (devnet)       | Uses same RPC -- Marinade program on-chain |
| Drift    | `drift-authority-keypair`        | Yes (devnet)       | Solana keypair for Drift program calls     |
| Wallet   | `wallet-{client}-solana-keypair` | Yes (dev wallet)   | Signs all Solana transactions              |

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Client Onboarding

See [cross-cutting/client-onboarding.md](../../../08-workflows/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Solana wallet per client (separate SOL, mSOL, USDC token accounts)
2. Drift sub-account per client (separate margin and positions)
3. Config: `initial_capital`, `min_staking_apy` (default 5%), `min_combined_apy` (default 15%)
4. **Restart required?** No -- hot-reload via GCS config

### Services requiring per-client configuration

| Service           | What Changes                   | Restart?        |
| ----------------- | ------------------------------ | --------------- |
| strategy-service  | New config entry in GCS        | No (hot-reload) |
| execution-service | New Solana wallet routing rule | No (hot-reload) |

## UI Visualisation

### Standard views

- PnL waterfall, margin health, position breakdown (from monitoring UI plans)

### Strategy-specific views

- **Combined APY decomposition** -- stacked bar: mSOL staking (~7%) + Drift funding (~15-30%) = combined
- **mSOL/SOL rate chart** -- with appreciation trend line and depeg alert threshold (3%)
- **Drift funding rate overlay** -- funding rate vs combined APY threshold line
- **Delta drift indicator** -- shows current delta mismatch and next rebalance trigger
- **Marinade validator health** -- aggregate validator performance and slashing events

## Testing Stage Status

| Stage        | Status  | Notes                                                                   |
| ------------ | ------- | ----------------------------------------------------------------------- |
| MOCK         | Pending | Need MockSolanaDeFiDynamics with mSOL rate appreciation + Drift funding |
| HISTORICAL   | Pending | Need mSOL rate history (Marinade launched 2021, ~5yr available)         |
| LIVE_MOCK    | Pending | Blocked by features-onchain msol_staking_apy calculator                 |
| LIVE_TESTNET | Pending | Blocked by Marinade devnet + Drift devnet integration                   |
| BATCH_REAL   | Pending | Blocked by historical APY storage                                       |
| STAGING      | Pending | Drift devnet + Marinade devnet + funded devnet wallet                   |
| LIVE_REAL    | Pending | All above + real capital approval                                       |

## Wallet & Capital Flow

| Component        | Value                                                       |
| ---------------- | ----------------------------------------------------------- |
| Treasury reserve | 20% of AUM                                                  |
| Hot wallet       | Solana wallet, per-strategy isolated                        |
| CeFi sub-account | Yes (Drift sub-account -- perp margin)                      |
| Bridge required  | Yes (if capital originates on EVM; No if already on Solana) |
| Custody          | Copper MPC                                                  |

Capital flow: Client deposit --> treasury --> hot wallet (Solana) --> SWAP to SOL --> STAKE to mSOL (spot LST leg) +
DEPOSIT USDC to Drift (margin). Rebalance: treasury < 10% --> strategy reduces position --> close perp + unstake mSOL +
SWAP SOL back --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked via Alchemy RPC using `getRecentPrioritizationFees` (Solana). The MTDS `gas_fee_handler` fetches
real-time priority fees and writes them as features. Gas hits P&L immediately as a realized transaction cost -- not
estimated. Full deploy costs ~0.004 SOL (~$0.60 total for swap + stake + deposit + perp). Solana gas is negligible
relative to position size.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md).
Jupiter swap routing uses SOL and USDC which are both in `DEFI_MAJOR_ASSET_SYMBOLS`. mSOL is in the Solana LST category
(WSOL, MSOL, STSOL, JITOSOL, BSOL, JSOL -- 35+ Solana tokens in `SOLANA_TOKEN_ADDRESSES`). LST/yield protocols have no
additional filtering needed -- the adapter returns all instruments.

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_sol_staked_basis.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md`
- **Execution adapter (Jupiter):** `execution-service/protocols/jupiter.py`
- **Execution adapter (Drift):** `execution-service/protocols/drift.py`
- **Execution adapter (Marinade):** `execution-service/protocols/marinade.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
