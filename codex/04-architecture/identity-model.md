---
doc_type: codex-ssot
title: Identity Model — Client, Account, Strategy
summary:
  Composite-key identity model for client / account / strategy — key formats, (client_id, strategy_id) override key,
  credential routing to Secret Manager, and write-time record enrichment via UTL RecordEnricher.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [strategy, execution, cefi, defi, registry]
related:
  [
    /codex/04-architecture/client-funds-isolation.md,
    /codex/04-architecture/per-client-isolation-architecture.md,
    /codex/04-architecture/execution-service-per-client-isolation.md,
  ]
created: 2026-04-16
authoritative_for: [client/account/strategy composite-key identity model]
referenced_by:
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Identity Model — Client, Account, Strategy

## Composite Keys

| Entity   | Key Format                                          | Example                            |
| -------- | --------------------------------------------------- | ---------------------------------- |
| Client   | `client_id` (string)                                | `patrick-elysium`                  |
| Account  | `{client_id}:{venue}:{account_label}`               | `patrick-elysium:BINANCE:main`     |
| Strategy | `{CATEGORY}_{ASSET}_{desc}_{MODE}_{TIMEFRAME}_V{N}` | `CEFI_BTC_momentum-macd_HUF_5M_V1` |

## Client-Strategy Relationship

- `(client_id, strategy_id)` is the composite key for strategy overrides
- Strategy instructions are keyed by `(client_id, strategy_id)` in GCS
- Positions are keyed by `(client_id, strategy_id, venue, account_id, instrument)`

## Account Types

| Type             | Example             | Identity                           |
| ---------------- | ------------------- | ---------------------------------- |
| CeFi Exchange    | Binance sub-account | `client:BINANCE:sub-1`             |
| DeFi Wallet      | Aave on Ethereum    | `client:AAVE_V3-ETHEREUM:0xABC...` |
| TradFi Broker    | IBKR                | `client:IBKR:DU1234567`            |
| Sports Bookmaker | Betfair             | `client:BETFAIR:main`              |

## Credential Routing

Execution-service resolves credentials via `(client_id, venue, account_label)` → Secret Manager lookup.

## Record Enrichment (Write-Time)

All records (orders, fills, positions) carry shard dimensions resolved at write time:

- `strategy_name` — from StrategyRegistry
- `client_name` — from ClientRegistry
- `category` — CEFI/DEFI/TRADFI/SPORTS/PREDICTION
- `strategy_family` — from StrategyRegistry
- `chain` — for DeFi
- `account_id` — composite key

Never resolve these at display time. UTL `RecordEnricher` handles enrichment.
