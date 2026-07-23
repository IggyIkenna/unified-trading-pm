---
doc_type: codex-ssot
title: "Axis: Share Class"
summary:
  Share-class axis — the per-instance accounting currency (USDT/USDC/FDUSD, USD/GBP/EUR, ETH/BTC/SOL) that fixes the
  NAV/Sharpe/return denominator and whether FX/basis risk is inside strategy P&L. Structural per-instance (different
  share class = different instance); declares the cross_currency_policy (HEDGE_ON_ENTRY/EXIT/ACCEPT/REBALANCE) and Unity
  resolves to USD.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, share-class, reconciliation, cefi, defi]
related:
  [
    ../cross-cutting/portfolio-allocator.md,
    ../cross-cutting/transfer-rebalance.md,
    ../cross-cutting/capital-client-isolation.md,
    ../../../04-architecture/capital-structure-and-regulatory.md,
  ]
created: 2026-04-17
authoritative_for: [share-class axis (per-instance accounting currency)]
referenced_by:
  [
    /codex/04-architecture/defi-risk-monitoring.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/cross-cutting/capital-client-isolation.md,
    plans/epics/client_isolation_and_governance_master.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Axis: Share Class

> **What it is:** The _accounting currency_ for a strategy instance. All P&L, NAV, equity, allocations, and performance
> metrics for the instance are expressed in the share-class unit. Share class is a **structural per-instance** field —
> not a config knob that changes mid-life. Different share class = different strategy instance.
>
> **Why it matters:** Share class determines the denominator for Sharpe, return, and allocation decisions. It fixes
> whether FX/basis risk is inside or outside the strategy's own P&L. It controls what currency profits accrue in and
> dictates fund/transfer orchestration.

## Supported share classes

### Stablecoin share classes (primary for crypto/sports)

| Share class | Notes                                                                       |
| ----------- | --------------------------------------------------------------------------- |
| `USDT`      | Binance/OKX/Bybit/Hyperliquid primary; exchange-native margin on most perps |
| `USDC`      | Deribit margin, most DeFi protocols, Polymarket, most DEXes                 |
| `FDUSD`     | Rare; Binance promotional                                                   |

### Fiat share classes

| Share class | Notes                                                                            |
| ----------- | -------------------------------------------------------------------------------- |
| `USD`       | IBKR primary; Unity meta-broker pool; sports direct-book accounts in USD regions |
| `GBP`       | UK sports books, some TradFi mandates                                            |
| `EUR`       | EU sports books, some TradFi mandates                                            |

### Crypto-native share classes

| Share class | Notes                                                              |
| ----------- | ------------------------------------------------------------------ |
| `ETH`       | ETH-denominated strategies (staked basis ETH, ETH vol)             |
| `BTC`       | BTC-denominated strategies (coin-margined perps, BTC options-only) |
| `SOL`       | Solana-native strategies (Jito, Solana DeFi)                       |

## Share class selection rules

A strategy instance's share class is chosen based on:

1. **Margin/collateral unit of the venue(s)** — USDT-margined perps on Binance imply USDT share class unless the
   strategy explicitly holds the P&L swing in another currency
2. **Client mandate** — client wants P&L reported in USD → USD share class (may imply FX hedging)
3. **Fund structure** — fund reports in USDC → all instances in that fund are USDC share class
4. **Asset-native economics** — staked ETH yield + ETH perp short = ETH share class (yield is in ETH, P&L cleanest in
   ETH)
5. **Regulatory** — TradFi SMA in IBKR defaults to USD

## FX and basis risk

When a strategy trades instruments not natively in the share-class currency, there's implicit FX/basis exposure:

| Example                                                  | Implied cross-currency |
| -------------------------------------------------------- | ---------------------- |
| USD share class running a USDT-margined Binance strategy | USD↔USDT basis risk    |
| USDT share class holding ETH position                    | USDT↔ETH FX            |
| USDC share class trading Polymarket shares               | trivial (both USDC)    |

Strategy config declares how this is handled:

```yaml
share_class: USD
cross_currency_policy:
  mode: HEDGE_ON_ENTRY # or HEDGE_ON_EXIT, ACCEPT, REBALANCE_PERIODICALLY
  hedge_venue: IBKR # where FX hedge is placed
  hedge_threshold_abs_usd: 10_000
```

Or for stablecoin basis:

```yaml
share_class: USD
cross_currency_policy:
  mode: ACCEPT # we accept USDT↔USD basis as strategy P&L
  justification: "USDT basis is part of the opportunity set"
```

## Share class and Unity meta-broker

Unity currency units resolve to **USD share class** — Unity wallet is denominated in USD notionally; per-book child
wallets settle with Unity in USD. Strategies routing via Unity default to `share_class: USD`. See
[../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md).

## Share class × archetype independence

Any archetype can run in any share class (subject to venue margin compatibility). Examples:

```
ML_DIRECTIONAL_CONTINUOUS@binance-btc-5m-USDT-prod       # USDT share class
ML_DIRECTIONAL_CONTINUOUS@binance-btc-5m-USD-prod        # USD share class, requires FX policy
ML_DIRECTIONAL_CONTINUOUS@deribit-btc-1h-USDC-prod       # USDC share class
CARRY_BASIS_PERP@binance-okx-eth-USDT-prod               # USDT native
CARRY_STAKED_BASIS@lido-binance-eth-ETH-prod             # ETH share class, yield + P&L both in ETH
```

## Different share classes = different instances

These are **three separate instances** even though the underlying logic is identical:

```
ML_DIRECTIONAL_CONTINUOUS@binance-btc-5m-USDT-prod
ML_DIRECTIONAL_CONTINUOUS@binance-btc-5m-USD-prod
ML_DIRECTIONAL_CONTINUOUS@binance-btc-5m-BTC-prod
```

Each has its own:

- Config version chain
- Allocated equity
- P&L attribution
- Kill switch
- Position tracking
- Onboarded client linkage

This preserves **fungibility of reporting**: the allocator can directly compare Sharpe across instances that share a
denominator, and cannot accidentally compare instances with different denominators.

## NAV accounting

The strategy-service tracks **equity**, **realized P&L**, **unrealized P&L**, and **fees** per instance, always in the
share-class unit. Conversions from venue-native P&L to share-class unit use the FX/basis policy declared in config (see
above).

NAV roll-up to client/fund happens at the Portfolio Allocator layer — it knows how to convert instance NAV from each
share class to the fund's reporting currency (see
[../cross-cutting/portfolio-allocator.md](../cross-cutting/portfolio-allocator.md)).

## Config schema

```yaml
share_class: USD # one of the enum values above
share_class_precision: 2 # decimals for P&L display
cross_currency_policy:
  mode: HEDGE_ON_ENTRY # HEDGE_ON_ENTRY / HEDGE_ON_EXIT / ACCEPT / REBALANCE_PERIODICALLY
  hedge_venue: IBKR # optional
  hedge_instrument: "IBKR:FX:USDUSDT" # optional
  hedge_threshold_abs_usd: 10_000 # optional
cost_reporting_currency: USD # how costs are aggregated for reporting (defaults to share_class)
```

## Not in this axis

- **FX hedging execution** — cross-cutting (transfer/rebalance + execution policy)
- **Fund-level currency consolidation** — Portfolio Allocator concern
- **Cross-class rebalancing** — transfer/rebalance service + Portfolio Allocator
- **Onboarded-client reporting currency** — may differ from share class; client-reporting layer converts

## Cross-references

- Capital structure:
  [../../../04-architecture/capital-structure-and-regulatory.md](../../../04-architecture/capital-structure-and-regulatory.md)
- Portfolio allocator: [../cross-cutting/portfolio-allocator.md](../cross-cutting/portfolio-allocator.md)
- Transfer/rebalance: [../cross-cutting/transfer-rebalance.md](../cross-cutting/transfer-rebalance.md)
- Unity integration: [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
