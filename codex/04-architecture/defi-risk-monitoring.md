---
doc_type: codex-ssot
title: DeFi Risk Monitoring
summary:
  DeFi risk-type taxonomy + alert thresholds — health-factor, oracle-depeg, borrow/staking spread, stablecoin depeg,
  withdrawal-delay, base-currency drift, margin-currency mismatch — plus per-check monitoring cadence.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service]
scope: [engineer, admin]
tags: [defi, risk, monitoring, health-factor, oracle, alerting]
related:
  [
    /codex/04-architecture/defi-phase3-infrastructure.md,
    /codex/09-strategy/architecture-v2/axes/share-class.md,
    /codex/04-architecture/alerting-batch-live.md,
  ]
created: 2026-04-03
authoritative_for: [DeFi risk-type taxonomy and alert thresholds]
referenced_by:
  [
    /codex/04-architecture/client-config-and-risk-dimensions.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# DeFi Risk Monitoring

## Overview

DeFi strategies operate with fundamentally different risk profiles from CeFi:

- **Health factor** can collapse in minutes during ETH price crashes (not hours)
- **Oracle lag** causes liquidations before market participants can react
- **Staking withdrawals** can be locked for days to weeks in stress scenarios
- **Borrow rate spikes** can flip leveraged positions from profitable to loss-making

This document covers all DeFi-specific risk types, monitoring thresholds, and alerting logic implemented in
`risk_and_exposure_service/engine/risk_metrics.py`.

## Risk Types

All DeFi risk type constants are in `unified_api_contracts.canonical.crosscutting.risk_taxonomy.RiskType`.

| RiskType constant          | Metric constant in risk_metrics.py   | Description                                 |
| -------------------------- | ------------------------------------ | ------------------------------------------- |
| `HEALTH_FACTOR`            | `DEFI_RISK_HEALTH_FACTOR`            | Aave/Compound HF for leveraged positions    |
| `ORACLE_DEPEG`             | `DEFI_RISK_ORACLE_DEPEG`             | Oracle price vs market price divergence     |
| `BORROW_RATE_SPREAD`       | `DEFI_RISK_BORROW_STAKING_SPREAD`    | Borrow APY vs staking/lending APY spread    |
| `STABLECOIN_DEPEG`         | `DEFI_RISK_STABLECOIN_DEPEG`         | USDT/USDC peg deviation                     |
| `WITHDRAWAL_DELAY`         | `DEFI_RISK_WITHDRAWAL_DELAY`         | LST/staking venue withdrawal queue exposure |
| `BASE_CURRENCY_DRIFT`      | `DEFI_RISK_BASE_CURRENCY_DRIFT`      | Delta drift from share class target         |
| `MARGIN_CURRENCY_MISMATCH` | `CEFI_RISK_MARGIN_CURRENCY_MISMATCH` | CeFi margin currency vs share class         |

## Sub-1H Health Factor Monitoring

`evaluate_health_factor_risk(health_factor, leverage, client_id)` — called on every position update, not just hourly
candles.

**Why sub-1H matters**: Recursive staking at 2.5x leverage can be liquidated within minutes during ETH crashes. The June
2024 Aave near-liquidation event happened in ~8 minutes.

**Thresholds**:

| Threshold | Alert type       | Severity | Action                      |
| --------- | ---------------- | -------- | --------------------------- |
| HF < 1.5  | RISK_WARNING     | WARNING  | Monitor, reduce exposure    |
| HF < 1.3  | RISK_CRITICAL    | CRITICAL | Urgent deleveraging         |
| HF < 1.1  | LIQUIDATION_RISK | CRITICAL | Emergency: immediate action |

**Matching convention**: Thresholds match Aave's own tiered safety model. alerting-service `defi_rules.py` uses the same
thresholds to avoid duplicate firing.

## Oracle Depeg Detection

`check_oracle_depeg(oracle_price, market_price, token, client_id)` — called when both oracle and spot price feeds are
available for the same token.

**Why it matters**: The June 2024 weETH event showed Aave oracle staying at peg while market price dropped 3%. Positions
calculated healthy by oracle were underwater in market terms.

**Thresholds**:

| Divergence | Alert type    | Severity                                   |
| ---------- | ------------- | ------------------------------------------ |
| > 1%       | RISK_WARNING  | WARNING                                    |
| > 2%       | RISK_CRITICAL | CRITICAL                                   |
| > 3%       | RISK_CRITICAL | CRITICAL (oracle may be stale/compromised) |

## Borrow Rate vs Staking Rate Spread

`check_borrow_staking_spread(borrow_apy, staking_apy, leverage, client_id)` — monitors whether leveraged staking
positions remain profitable.

**Formula**: `net_spread = staking_apy - (borrow_apy × leverage)`

A negative spread means the strategy is losing money at the current leverage level.

**Thresholds**:

| Net spread | Alert type    | Severity                              |
| ---------- | ------------- | ------------------------------------- |
| < 0%       | RISK_WARNING  | WARNING                               |
| < -0.5%    | RISK_CRITICAL | CRITICAL (significant negative carry) |

**Example**: ETH staking at 4% APY, WETH borrow at 3% APY, leverage 2.0x. Net spread = 4% - (3% × 2) = -2% → CRITICAL.

## Stablecoin Depeg

`check_stablecoin_depeg(price, peg, token, client_id)` — monitors USDT/USDC/DAI peg.

Relevant because lending collateral is often stablecoin-denominated.

**Thresholds** (deviation from peg):

| Deviation | Alert type    | Severity                     |
| --------- | ------------- | ---------------------------- |
| > 0.5%    | RISK_WARNING  | WARNING                      |
| > 1%      | RISK_CRITICAL | CRITICAL                     |
| > 5%      | RISK_CRITICAL | CRITICAL (major depeg event) |

## Withdrawal Delay Risk

`_assess_withdrawal_delay_risk(positions, account_equity, client_id)` — quantifies illiquidity risk from staking/LST
positions with multi-day withdrawal queues.

**Why it matters**: EtherFi can take up to 14 days to process withdrawals in stress scenarios (2023: Lido withdrawal
queue backed up 7+ days). If >50% of a portfolio is in staking venues, effective emergency liquidity is severely
constrained.

**Venue delay model**:

| Venue prefix | Typical delay | Notes                             |
| ------------ | ------------- | --------------------------------- |
| ETHERFI      | 14 days       | 1-14 days, queue-dependent        |
| LIDO         | 4 days        | 1-4 days (stETH withdrawal queue) |
| ROCKETPOOL   | 7 days        | Up to 7 days                      |
| MARINADE     | 3 days        | Marinade Finance (SOL)            |
| KAMINO       | 2 days        | Kamino (SOL)                      |
| DRIFT        | 1 day         | Drift (SOL)                       |

**Thresholds** (illiquid % of total equity):

| Illiquid % | Alert type    | Severity |
| ---------- | ------------- | -------- |
| > 20%      | RISK_WARNING  | WARNING  |
| > 50%      | RISK_CRITICAL | CRITICAL |

## Base Currency Drift (Share Class)

`evaluate_base_currency_drift(delta_composite, share_class, account_equity, fx_rate)` — monitors portfolio delta vs
share class target.

**USDT share class**: Target delta in all non-stablecoin assets = 0 (market neutral). **ETH/BTC share class**: Target
delta in base asset = account_equity / fx_rate (NOT zero).

Drift > 2% triggers WARNING, > 5% triggers CRITICAL.

See `/codex/09-strategy/architecture-v2/axes/share-class.md` for full share class architecture.

## Margin Currency Mismatch

`evaluate_margin_currency_mismatch(positions, share_class, client_id)` — detects CeFi positions whose margin currency
differs from the portfolio share class.

**Example**: ETH share class portfolio with BTC-USDT perp (USDT margin) → WARNING.

This matters for P&L accuracy: if ETH rallies and your perp gains are in USDT, you've underperformed your share class
target.

## Rebalance and Emergency Close Cost Estimation

Cost estimation lives in:

- Strategy-service: `defi_enhancements.py` — `_estimate_rebalance_cost()`, `_estimate_emergency_close_cost()`
- Execution-service: `unwind_cost.py` — `estimate_full_unwind_cost(positions)`

**`estimate_full_unwind_cost(positions)` inputs**:

```python
class PositionSummary(TypedDict):
    instrument_id: str
    size_usd: Decimal
    venue_type: str  # "DEX", "CEFI", "LENDING", "STAKING"
```

**Output** (`UnwindCostEstimate`):

- `total_cost_usd`, `gas_cost_usd`, `exchange_fees_usd`, `slippage_usd`, `bridge_fees_usd`
- `estimated_time_minutes`: time to fully unwind
- `notes`: human-readable explanations for unusual costs

Strategy uses cost estimates in the rebalance decision:

```python
if not self._rebalance_passes_cost_benefit(current_weights, target_weights):
    # Rebalance cost exceeds expected yield gain — skip
    return []
```

## Monitoring Frequency

| Risk check               | Frequency             | Trigger                       |
| ------------------------ | --------------------- | ----------------------------- |
| Health factor            | Every position update | Redis position update event   |
| Oracle depeg             | Every candle          | Feature pipeline candle event |
| Borrow rate spread       | Every candle          | Feature pipeline candle event |
| Stablecoin depeg         | Every candle          | Feature pipeline candle event |
| Withdrawal delay         | Every risk cycle      | Hourly (config-driven)        |
| Base currency drift      | Every risk cycle      | Hourly or position update     |
| Margin currency mismatch | Every risk cycle      | Position update               |
