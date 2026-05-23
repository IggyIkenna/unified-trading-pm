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

## EventType — 37 values

Routes rows to derived-ledger computation in strategy-service. Grouped by origin (19 instruction-driven + 18 passive).

### Instruction-driven events (EventOrigin.INSTRUCTION) — 19 values

| Value                | String value         | Meaning                                                                                                                                                                                              |
| -------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TRADE`              | `trade`              | Fill on a CeFi / DeFi / TradFi / sports / prediction order                                                                                                                                           |
| `SWAP`               | `swap`               | DEX swap (Uniswap, Curve, Balancer, Sushi, PancakeSwap, Phoenix, Orca, Raydium, Drift) — token-in / token-out atomic exchange. Distinct from TRADE because there is no order/fill semantics on-chain |
| `TRANSFER`           | `transfer`           | On-chain or off-chain asset movement (deposit, withdrawal, sub-account move)                                                                                                                         |
| `STAKE`              | `stake`              | LST mint / DeFi protocol deposit (asset locked, receipt token received)                                                                                                                              |
| `UNSTAKE`            | `unstake`            | LST burn / DeFi protocol withdrawal                                                                                                                                                                  |
| `BORROW`             | `borrow`             | Collateralised borrow (Aave, Compound, Morpho)                                                                                                                                                       |
| `REPAY`              | `repay`              | Repayment of a borrow position                                                                                                                                                                       |
| `BRIDGE`             | `bridge`             | Cross-chain bridge movement (CCTP, Across, Stargate, Wormhole)                                                                                                                                       |
| `SUPPLY`             | `supply`             | Lending-protocol supply / deposit of collateral (Aave aToken mint, Compound cToken mint, Morpho supply). Distinct from STAKE because the asset earns interest rather than staking rewards            |
| `WITHDRAW`           | `withdraw`           | Lending-protocol withdraw of supplied collateral (aToken / cToken burn). Distinct from UNSTAKE which closes a STAKE position                                                                         |
| `WRAP`               | `wrap`               | Wrap native asset into ERC-20 (ETH → WETH, SOL → wSOL) or wrap one receipt token into another (stETH → wstETH, eETH → weETH). 1:1 conversion with no price discovery                                 |
| `UNWRAP`             | `unwrap`             | Inverse of WRAP — burn wrapped token to redeem the underlying                                                                                                                                        |
| `EARLY_EXERCISE`     | `early_exercise`     | Holder-initiated early exercise of an American option before expiry. Distinct from SETTLEMENT/EXPIRY (passive at-expiry events) because this is an explicit agent instruction                        |
| `CASH_OUT`           | `cash_out`           | Prediction-market / sports-book cash-out of an open position before resolution (operator-initiated close at the book's current quote). Distinct from TRADE because it is a venue-mediated unwind     |
| `DEPOSIT`            | `deposit`            | Client funds inflow to a venue/account/wallet from an external source (bank wire, on-chain incoming transfer from a non-tracked address). Feeds TreasuryLedger when counterparty_client_id is None   |
| `WITHDRAWAL_TO_BANK` | `withdrawal_to_bank` | Client funds outflow from a venue/account/wallet to an off-platform destination (bank wire, on-chain outgoing transfer to a non-tracked address). Feeds TreasuryLedger                               |
| `CUSTODY_MOVE`       | `custody_move`       | Movement of assets between custody providers / sub-custodians for the same client (Copper ↔ CEFFU ↔ on-chain wallet ↔ KMS-encrypted hot wallet). HARD RULE: counterparty_client_id == client_id      |
| `FX_CONVERSION`      | `fx_conversion`      | Stablecoin / fiat / currency conversion that is not order-book mediated (e.g. on-chain stablecoin swap via 1:1 oracle, custodian-quoted FX fill, USDC ↔ USDT bridge-equivalent)                      |
| `LIQUIDATION`        | `liquidation`        | Forced liquidation by venue/protocol (partial or full). Counted as instruction-driven because the venue's keeper acts as the instructing agent on behalf of the protocol                             |

### Passive events (EventOrigin.PASSIVE) — 18 values

| Value                   | String value            | Meaning                                                                                                                                                                                            | Typical cadence           |
| ----------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `FUNDING_ACCRUAL`       | `funding_accrual`       | Perpetual funding payment received or paid                                                                                                                                                         | 8h CeFi; block-level DeFi |
| `DIVIDEND`              | `dividend`              | Cash/stock dividend on equity or futures                                                                                                                                                           | Ex-dividend date          |
| `STAKING_REWARD`        | `staking_reward`        | LST/validator staking reward (stETH rebase aggregate, JitoSOL yield)                                                                                                                               | Oracle report / epoch end |
| `LENDING_INTEREST`      | `lending_interest`      | Aave/Compound/Morpho interest accrual on supplied collateral                                                                                                                                       | Block-level or daily      |
| `REBASE`                | `rebase`                | Token-supply rebase event (stETH, ampleforth-style). Balance changes without a transfer — synthesised from liquidity-index / share-price delta. Distinct from STAKING_REWARD (per-block mechanism) | Block / oracle report     |
| `VALIDATOR_REWARD`      | `validator_reward`      | Direct validator block / attestation reward credited to a tracked validator (native ETH/SOL staking, NOT via an LST). Synthesised from consensus-layer events (beacon-chain) or SOL epoch credits  | Slot / epoch end          |
| `MEV_REWARD`            | `mev_reward`            | Maximal Extractable Value reward — proposer / searcher tip credited outside the staking reward stream (Flashbots block-builder payments). Distinct from VALIDATOR_REWARD (cash-flow path differs)  | Block                     |
| `AIRDROP`               | `airdrop`               | Token airdrop received without an explicit claim instruction (push airdrop) OR initial credit balance from a passive-eligibility snapshot. Pull-airdrop claims are TRADE/SWAP events               | Event-driven              |
| `COUPON`                | `coupon`                | Bond/note coupon payment received (TradFi fixed income). Periodic fixed cash flow tied to a bond holding                                                                                           | Coupon schedule           |
| `SPORTS_RESOLUTION`     | `sports_resolution`     | Sports-market settlement at event conclusion — winning / losing selection cash flow credited / debited. Distinct from SETTLEMENT because the resolution oracle and fee model are sports-specific   | Event conclusion          |
| `PREDICTION_RESOLUTION` | `prediction_resolution` | Prediction-market binary contract resolution (Polymarket CLOB, Kalshi). YES/NO shares settle to 1.00 / 0.00. Distinct from SETTLEMENT for the same reason as SPORTS_RESOLUTION                     | Resolution date           |
| `SLASHING`              | `slashing`              | Validator slashing penalty (native staking) or protocol-penalty debit (LST slashing-pass-through, lending bad-debt socialisation). Negative-cash-flow passive event                                | Event-driven              |
| `GAS_REFUND`            | `gas_refund`            | Gas refund event — EIP-3529 SSTORE-clear refund, L2 sequencer refund, or relayer rebate credited after the originating transaction. Linked via parent_event_id                                     | Per-tx                    |
| `AUTO_COMPOUND`         | `auto_compound`         | Vault / yield-aggregator auto-compound event — protocol re-stakes accrued rewards into the supplied position (Yearn harvest, ERC-4626 autocompound, Morpho MetaMorpho rebalance)                   | Vault harvest cadence     |
| `INTEREST_ACCRUAL`      | `interest_accrual`      | Generic interest accrual for non-lending-protocol contexts — CeFi margin-account interest, money-market-fund yield, custodian-paid cash interest. Distinct from LENDING_INTEREST (DeFi-specific)   | Daily / block             |
| `SETTLEMENT`            | `settlement`            | Futures/options settlement at expiry (cash or physical delivery). The ITM cash-flow counterpart to EXPIRY                                                                                          | Expiry date               |
| `EXPIRY`                | `expiry`                | Options expiry — position zeroed at zero value (OTM). The position-zeroing counterpart to SETTLEMENT; kept distinct because no cash flow occurs and premium decay realises fully                   | Expiry date               |
| `MARK_UPDATE`           | `mark_update`           | Mark price / IV / greek snapshot update — **PricingLedger only** (MTDS writer)                                                                                                                     | Tick or per-minute        |

---

## AssetClass — 17 values

Drives attribution bucketing, margin calculations, and passive-event synthesis rules.

| Value                 | String value          | Description                                                                                                                                                                          |
| --------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SPOT_TOKEN`          | `spot_token`          | CEX spot or plain ERC-20/SPL token (non-stablecoin)                                                                                                                                  |
| `STABLE`              | `stable`              | Stablecoin (USDC, USDT, DAI, USDe, PYUSD, FDUSD, USDS). Held distinct from SPOT_TOKEN because peg-deviation risk, attribution against quote currency, and treasury semantics differ  |
| `ATOKEN`              | `atoken`              | Aave aToken (aUSDC, aWETH) — supplied collateral receipt                                                                                                                             |
| `DEBT_TOKEN`          | `debt_token`          | Aave variableDebtToken — borrow position liability                                                                                                                                   |
| `LST`                 | `lst`                 | Liquid staking token (stETH, rETH, cbETH, JitoSOL, mSOL)                                                                                                                             |
| `LRT`                 | `lrt`                 | Liquid restaking token (eETH, weETH, rsETH)                                                                                                                                          |
| `VAULT_SHARE`         | `vault_share`         | Yield vault share (Yearn, ERC-4626, Morpho MetaMorpho)                                                                                                                               |
| `FUTURE`              | `future`              | Exchange-traded or OTC futures contract                                                                                                                                              |
| `PERP`                | `perp`                | Perpetual swap / inverse perp                                                                                                                                                        |
| `OPTION`              | `option`              | Vanilla or exotic option                                                                                                                                                             |
| `ETF`                 | `etf`                 | Exchange-traded fund share (TradFi: SPY, QQQ, IBIT etc.). Held distinct from SPOT_TOKEN because dividend handling, settlement venue, and regulatory treatment differ                 |
| `NFT`                 | `nft`                 | Non-fungible token (ERC-721 / ERC-1155). Held primarily for collateral and protocol-rewards positions; unit semantics (delta is always integer 1) differ from fungible asset classes |
| `PREDICTION_CONTRACT` | `prediction_contract` | Binary prediction market contract (Polymarket CLOB, Kalshi)                                                                                                                          |
| `SPORTS_OUTCOME`      | `sports_outcome`      | Sports betting outcome / odds contract                                                                                                                                               |
| `CURRENCY`            | `currency`            | Fiat currency used as quote / margin. **Stablecoins route to `STABLE`, not `CURRENCY`.**                                                                                             |
| `GAS_TOKEN`           | `gas_token`           | Native chain gas token (ETH, SOL, MATIC) — fees-only rows                                                                                                                            |
| `UNKNOWN`             | `unknown`             | Unresolved — must be enriched before settlement; triggers alert                                                                                                                      |

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

| Discriminant                                                                                      | SSOT Ledger       | Writer                       |
| ------------------------------------------------------------------------------------------------- | ----------------- | ---------------------------- |
| `event_origin=INSTRUCTION`                                                                        | InstructionLedger | execution-service            |
| `event_origin=PASSIVE, event_type != MARK_UPDATE`                                                 | PassiveLedger     | strategy-service synthesiser |
| `event_type=MARK_UPDATE`                                                                          | PricingLedger     | MTDS                         |
| `event_type ∈ {TRANSFER, DEPOSIT, WITHDRAWAL_TO_BANK, CUSTODY_MOVE}, counterparty_client_id=None` | TreasuryLedger    | TBD Phase 4 decision         |

Notes:

- `DEPOSIT` and `WITHDRAWAL_TO_BANK` always feed TreasuryLedger when the counterparty is external (no
  `counterparty_client_id`).
- `CUSTODY_MOVE` is intra-client by HARD RULE (`counterparty_client_id == client_id`) but still feeds TreasuryLedger for
  custody-provider attribution.
- `SWAP`, `SUPPLY`, `WITHDRAW`, `WRAP`, `UNWRAP`, `EARLY_EXERCISE`, `CASH_OUT`, `FX_CONVERSION` route to
  InstructionLedger like other agent-instructed events.
- `REBASE`, `VALIDATOR_REWARD`, `MEV_REWARD`, `AIRDROP`, `COUPON`, `SPORTS_RESOLUTION`, `PREDICTION_RESOLUTION`,
  `SLASHING`, `GAS_REFUND`, `AUTO_COMPOUND`, `INTEREST_ACCRUAL` route to PassiveLedger.

---

## Cross-Client Transfer Invariant

`counterparty_client_id`, when set, MUST equal `client_id`. `CrossClientTransferForbiddenError` is raised at `LedgerRow`
construction time. See `codex/04-architecture/client-funds-isolation.md`.

Valid usages of "cross-client" in this codebase:

- Isolation enforcement contexts: `isolation_policy.assert_client_allowed()`, `CrossClientEventError` event-bus
  rejection
- Never: fund movement between different clients

---

## Changelog

- 2026-05-23: expanded to 37 EventTypes + 17 AssetClasses per
  `plans/active/global_ledger_pnl_attribution_discovery_2026_05_21.md` Phase 2. Added 11 instruction events (SWAP,
  SUPPLY, WITHDRAW, WRAP, UNWRAP, EARLY_EXERCISE, CASH_OUT, DEPOSIT, WITHDRAWAL_TO_BANK, CUSTODY_MOVE, FX_CONVERSION) +
  11 passive events (REBASE, VALIDATOR_REWARD, MEV_REWARD, AIRDROP, COUPON, SPORTS_RESOLUTION, PREDICTION_RESOLUTION,
  SLASHING, GAS_REFUND, AUTO_COMPOUND, INTEREST_ACCRUAL) + 3 asset classes (STABLE, ETF, NFT). CURRENCY redirected
  stablecoins → STABLE. Routing summary updated for TreasuryLedger-feeding events.
- 2026-05-23: initial codex publication for Phase 2 UAC ledger schema.
