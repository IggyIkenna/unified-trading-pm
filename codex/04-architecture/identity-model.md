---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

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

| Type             | Example             | Identity                          |
| ---------------- | ------------------- | --------------------------------- |
| CeFi Exchange    | Binance sub-account | `client:BINANCE:sub-1`            |
| DeFi Wallet      | Aave on Ethereum    | `client:AAVEV3-ETHEREUM:0xABC...` |
| TradFi Broker    | IBKR                | `client:IBKR:DU1234567`           |
| Sports Bookmaker | Betfair             | `client:BETFAIR:main`             |

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
