---
title: Ledger Event Taxonomy
type: data
status: active
created: 2026-05-21
last_reviewed: 2026-05-23
scope: [engineer, admin]
---

# Ledger Event Taxonomy

> **[DELTA 2026-05-23]** Phase 2 UAC schema shipped at `unified-api-contracts@008e59ce`. All enums below are canonical
> StrEnum values in `unified_api_contracts.canonical.crosscutting.ledger`. These are **closed sets** — extension
> requires a PR; removing or renaming any value is a breaking schema change.

**UAC module**: `unified_api_contracts.canonical.crosscutting.ledger` **Codex companion**:
`codex/04-architecture/global-ledger-architecture.md`

---

## EventOrigin

Discriminates instruction-driven vs passive (non-instruction) events. Routes rows to the correct SSOT ledger.

| Value         | String value  | Meaning                                                                                     | SSOT ledger       |
| ------------- | ------------- | ------------------------------------------------------------------------------------------- | ----------------- |
| `INSTRUCTION` | `instruction` | Event arose from an explicit agent action (order, transfer, stake, bridge, rebalance)       | InstructionLedger |
| `PASSIVE`     | `passive`     | Event arose without an explicit instruction (funding, dividend, staking reward, settlement) | PassiveLedger     |

---

## EventType

Routes rows to derived-ledger computation in strategy-service. Grouped by origin.

### Instruction-driven events (EventOrigin.INSTRUCTION)

| Value         | String value  | Meaning                                                                         |
| ------------- | ------------- | ------------------------------------------------------------------------------- |
| `TRADE`       | `trade`       | Fill on a CeFi / DeFi / TradFi / sports / prediction order                      |
| `TRANSFER`    | `transfer`    | On-chain or off-chain asset movement (deposit, withdrawal, bridge, sub-account) |
| `STAKE`       | `stake`       | LST mint / DeFi protocol deposit (asset locked, receipt token received)         |
| `UNSTAKE`     | `unstake`     | LST burn / DeFi protocol withdrawal                                             |
| `BORROW`      | `borrow`      | Collateralised borrow (Aave, Compound, Morpho)                                  |
| `REPAY`       | `repay`       | Repayment of a borrow position                                                  |
| `BRIDGE`      | `bridge`      | Cross-chain bridge movement (CCTP, Across, Stargate, Wormhole)                  |
| `LIQUIDATION` | `liquidation` | Forced liquidation by venue/protocol (partial or full)                          |

### Passive events (EventOrigin.PASSIVE)

| Value              | String value       | Meaning                                                                        | Typical cadence           |
| ------------------ | ------------------ | ------------------------------------------------------------------------------ | ------------------------- |
| `FUNDING_ACCRUAL`  | `funding_accrual`  | Perpetual funding payment received or paid                                     | 8h CeFi; block-level DeFi |
| `DIVIDEND`         | `dividend`         | Cash/stock dividend on equity or futures                                       | Ex-dividend date          |
| `STAKING_REWARD`   | `staking_reward`   | LST/validator staking reward (stETH rebase, JitoSOL yield)                     | Oracle report / epoch end |
| `LENDING_INTEREST` | `lending_interest` | Aave/Compound/Morpho interest accrual on supplied collateral                   | Block-level or daily      |
| `SETTLEMENT`       | `settlement`       | Futures/options settlement at expiry (cash or physical delivery)               | Expiry date               |
| `EXPIRY`           | `expiry`           | Options expiry — position zeroed at zero value (OTM)                           | Expiry date               |
| `MARK_UPDATE`      | `mark_update`      | Mark price / IV / greek snapshot update — **PricingLedger only** (MTDS writer) | Tick or per-minute        |

---

## AssetClass

Drives attribution bucketing, margin calculations, and passive-event synthesis rules.

| Value                 | String value          | Description                                                     |
| --------------------- | --------------------- | --------------------------------------------------------------- |
| `SPOT_TOKEN`          | `spot_token`          | CEX spot or plain ERC-20/SPL token                              |
| `ATOKEN`              | `atoken`              | Aave aToken (aUSDC, aWETH) — supplied collateral receipt        |
| `DEBT_TOKEN`          | `debt_token`          | Aave variableDebtToken — borrow position liability              |
| `LST`                 | `lst`                 | Liquid staking token (stETH, rETH, cbETH, JitoSOL, mSOL)        |
| `LRT`                 | `lrt`                 | Liquid restaking token (eETH, weETH, rsETH)                     |
| `VAULT_SHARE`         | `vault_share`         | Yield vault share (Yearn, ERC-4626, Morpho MetaMorpho)          |
| `FUTURE`              | `future`              | Exchange-traded or OTC futures contract                         |
| `PERP`                | `perp`                | Perpetual swap / inverse perp                                   |
| `OPTION`              | `option`              | Vanilla or exotic option                                        |
| `PREDICTION_CONTRACT` | `prediction_contract` | Binary prediction market contract (Polymarket CLOB, Kalshi)     |
| `SPORTS_OUTCOME`      | `sports_outcome`      | Sports betting outcome / odds contract                          |
| `CURRENCY`            | `currency`            | Fiat currency or stablecoin used as quote / margin              |
| `GAS_TOKEN`           | `gas_token`           | Native chain gas token (ETH, SOL, MATIC) — fees-only rows       |
| `UNKNOWN`             | `unknown`             | Unresolved — must be enriched before settlement; triggers alert |

---

## Direction

Maps to the natural language of each asset class. Not all values are valid for every `AssetClass`.

| Value      | String value | Applicable asset classes                          |
| ---------- | ------------ | ------------------------------------------------- |
| `BUY`      | `buy`        | SPOT_TOKEN, FUTURE, OPTION, CURRENCY              |
| `SELL`     | `sell`       | SPOT_TOKEN, FUTURE, OPTION, CURRENCY              |
| `BACK`     | `back`       | SPORTS_OUTCOME (back = bet for outcome)           |
| `LAY`      | `lay`        | SPORTS_OUTCOME (lay = bet against outcome)        |
| `YES`      | `yes`        | PREDICTION_CONTRACT (buy YES shares)              |
| `NO`       | `no`         | PREDICTION_CONTRACT (buy NO shares)               |
| `LONG`     | `long`       | PERP, FUTURE (opening long)                       |
| `SHORT`    | `short`      | PERP, FUTURE (opening short)                      |
| `SUPPLY`   | `supply`     | ATOKEN (Aave supply / deposit)                    |
| `WITHDRAW` | `withdraw`   | ATOKEN (Aave withdraw)                            |
| `EXERCISE` | `exercise`   | OPTION (holder exercises — American options only) |
| `ASSIGN`   | `assign`     | OPTION (writer assigned — American options only)  |

---

## OptionRight

Applies only when `asset_class=OPTION`.

| Value  | String value | Meaning     |
| ------ | ------------ | ----------- |
| `CALL` | `C`          | Call option |
| `PUT`  | `P`          | Put option  |

---

## Routing Summary

| Discriminant                                       | SSOT Ledger       | Writer                       |
| -------------------------------------------------- | ----------------- | ---------------------------- |
| `event_origin=INSTRUCTION`                         | InstructionLedger | execution-service            |
| `event_origin=PASSIVE, event_type != MARK_UPDATE`  | PassiveLedger     | strategy-service synthesiser |
| `event_type=MARK_UPDATE`                           | PricingLedger     | MTDS                         |
| `event_type=TRANSFER, counterparty_client_id=None` | TreasuryLedger    | TBD Phase 4 decision         |

---

## Cross-Client Transfer Invariant

`counterparty_client_id`, when set, MUST equal `client_id`. `CrossClientTransferForbiddenError` is raised at `LedgerRow`
construction time. See `codex/04-architecture/client-funds-isolation.md`.

Valid usages of "cross-client" in this codebase:

- Isolation enforcement contexts: `isolation_policy.assert_client_allowed()`, `CrossClientEventError` event-bus
  rejection
- Never: fund movement between different clients
