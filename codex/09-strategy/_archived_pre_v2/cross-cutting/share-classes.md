---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Share Classes -- Cross-Cutting Concern

## Overview

Share classes define the base currency denomination for a strategy instance. The share class affects delta neutrality
targets, P&L attribution, treasury management, and rebalancing logic. Every strategy config includes a `share_class`
parameter (default: `USDT`).

## Share Class Definitions

### USDT (USD-denominated)

- **Target delta:** 0 (fully market neutral)
- **P&L currency:** USD
- **Delta neutrality:** Long spot + short perp (or equivalent hedge) cancel completely. The strategy has zero net market
  exposure.
- **Use case:** Clients who want pure yield harvesting with no crypto price risk.
- **CeFi equivalent:** USDT-margined futures have zero natural delta. A USDT share class basis trade is fully
  market-neutral by default.

### ETH (Ether-denominated)

- **Target delta:** total_equity_in_eth
- **P&L currency:** ETH
- **Delta neutrality:** The portfolio's ETH-denominated value is stable. The perp hedge removes basis risk and funding
  rate directionality, but the portfolio retains full ETH exposure. Returns accrue in ETH terms.
- **Use case:** Clients with a long-term ETH allocation who want to earn yield on their ETH position without converting
  to USD.
- **CeFi equivalent:** Coin-margined (inverse) futures have natural delta equal to the margin amount in ETH. An ETH
  share class aligns with this natural delta.

### BTC (Bitcoin-denominated)

- **Target delta:** total_equity_in_btc
- **P&L currency:** BTC
- **Delta neutrality:** Same pattern as ETH but for BTC-denominated positions. The portfolio retains full BTC exposure.
  Returns accrue in BTC terms.
- **Use case:** Clients with a BTC allocation who want yield without currency conversion.
- **CeFi equivalent:** BTC coin-margined futures. The natural delta matches the BTC margin.

## Delta Neutrality by Share Class

The delta target varies by share class. The rebalancing system computes deviation from the share-class-specific target,
not from zero.

```
delta_deviation = |current_delta - target_delta| / notional

For USDT:  target_delta = 0
For ETH:   target_delta = total_equity / eth_price
For BTC:   target_delta = total_equity / btc_price
```

Rebalancing triggers when `delta_deviation > threshold` (default 2%). The rebalance action adjusts the perp hedge to
bring delta back to the share-class target.

## CeFi Margin Interaction

CeFi venues offer both linear (USDT-margined) and inverse (coin-margined) perpetuals. The share class interacts with the
margin type:

| Share Class | Preferred Margin Type | Natural Delta   | Notes                                                |
| ----------- | --------------------- | --------------- | ---------------------------------------------------- |
| `USDT`      | Linear (USDT)         | 0               | Default. No additional delta management needed.      |
| `ETH`       | Inverse (ETH)         | = margin in ETH | Natural delta from coin margin matches target delta. |
| `BTC`       | Inverse (BTC)         | = margin in BTC | Same pattern.                                        |

When using linear (USDT-margined) futures with an ETH share class, the strategy must manage the additional delta from
the ETH spot position explicitly. Inverse futures automatically provide the correct delta alignment.

## P&L Attribution

The P&L attribution system separates base-currency conversion from trading P&L using the FX factor:

| Factor               | What It Captures                                                  |
| -------------------- | ----------------------------------------------------------------- |
| `PNL_FACTOR_TRADING` | Realized and unrealized trading gains in base currency.           |
| `PNL_FACTOR_FX`      | Gains/losses from base-currency to reporting-currency conversion. |
| `PNL_FACTOR_FUNDING` | Funding rate income (in base currency).                           |
| `PNL_FACTOR_STAKING` | Staking yield (in base currency).                                 |

For `USDT` share class, the FX factor is zero (no conversion needed). For `ETH` share class, the FX factor captures the
USD/ETH price movement between P&L snapshots. This ensures that a strategy's trading performance is evaluated in the
client's base currency without being contaminated by FX movements.

## Rebalancing

Rebalancing is only triggered when `|delta_deviation| > threshold`:

- Default threshold: 2% of notional
- Cost-benefit gate applies: only rebalance if expected benefit > cost x 1.5
- For `USDT` share class: rebalance means adjusting perp size to restore zero delta
- For `ETH`/`BTC` share class: rebalance means adjusting perp size to restore delta = equity-in-base-currency

## Implementation

- **Enum:** `ShareClass` in UAC (`unified_api_contracts.internal.enums`)
- **Mixin:** `ShareClassMixin` in `strategy-service/strategy_service/engine/strategies/defi_enhancements.py`
- **Config:** `share_class: str` in strategy config (values: `"USDT"`, `"ETH"`, `"BTC"`)
- **P&L integration:** `PnLCalculator` reads `share_class` from strategy config and applies the FX factor accordingly

## Strategy Applicability

| Strategy               | USDT | ETH | BTC | Notes                                             |
| ---------------------- | ---- | --- | --- | ------------------------------------------------- |
| Basis Trade            | Yes  | Yes | Yes | Most common use of share classes.                 |
| Staked Basis           | Yes  | Yes | Yes | ETH share class is natural fit for staking yield. |
| Recursive Staked Basis | Yes  | Yes | No  | BTC not supported (no BTC LST on Aave).           |
| AAVE Lending           | Yes  | Yes | No  | ETH variant uses ETH share class by default.      |
| CeFi strategies        | Yes  | Yes | Yes | Coin-margined futures align with ETH/BTC classes. |
