---
doc_type: codex-ssot
title: Share Class Architecture
summary:
  Share class = the base currency (USDT/ETH/BTC) a client portfolio is denominated in; defines per-class delta-neutral
  targets, margin-currency-mismatch + base-currency-drift risk checks, and FX-component PnL decomposition.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [e2e-testing, execution-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, defi, cefi, execution, reconciliation]
related: [/codex/04-architecture/strategy-execution-protocol.md, /codex/04-architecture/capital-flow-model.md]
created: 2026-04-03
authoritative_for:
  [share-class base-currency architecture (USDT/ETH/BTC denomination + per-class delta-neutral targets)]
referenced_by:
  [
    /codex/04-architecture/client-config-and-risk-dimensions.md,
    /codex/14-customer-journeys/glossary.md,
    /codex/14-customer-journeys/playbook-concepts/client-reporting.md,
    /codex/14-customer-journeys/playbook-concepts/fund-org-hierarchy.md,
    /codex/14-customer-journeys/playbook-concepts/sma-vs-pooled.md,
    /codex/14-customer-journeys/playbooks/02a-research-im.md,
    /codex/14-customer-journeys/roadmap/plan-references.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Share Class Architecture

## Definition

A **share class** is the base currency in which a client's portfolio is denominated. All P&L, risk metrics, and
rebalancing thresholds are expressed in the share class currency rather than USD.

Three share classes are supported (matching `UAC ShareClass` enum):

| Share Class | Base Currency              | Target Clients                        |
| ----------- | -------------------------- | ------------------------------------- |
| `USDT`      | Stablecoin (USDT/USDC/USD) | Capital-preservation / market-neutral |
| `ETH`       | Ethereum                   | ETH-native DeFi strategies            |
| `BTC`       | Bitcoin                    | BTC-denominated strategies            |

## CeFi vs DeFi Application

### CeFi (margin futures/perpetuals)

CeFi positions are margined in a quote currency (e.g. BTC-USDT → margin in USDT). When the client's share class is
`ETH`, having all positions margined in USDT creates FX exposure that is not captured by the strategy's delta hedging.

The `evaluate_margin_currency_mismatch()` function in `risk-and-exposure-service` detects this:

- `USDT` share class accepts USDT, USDC, USD, BUSD, FDUSD as quote currency — no mismatch.
- `ETH` share class expects ETH/WETH margined positions. Any USDT-margined CeFi position triggers a `MARGIN_WARNING`
  alert with metric `MARGIN_CURRENCY_MISMATCH`.
- `BTC` share class expects BTC/WBTC/XBT margined positions.

### DeFi

DeFi positions (aTokens, LP positions, staking receipts) do not have a margin currency in the same sense. The relevant
risk check for DeFi is `evaluate_base_currency_drift()` which measures whether the portfolio delta is aligned with the
share class target.

## Delta Neutrality Per Share Class

Each share class defines a different "neutral" target:

- **USDT share class**: Total portfolio should be market-neutral — net non-stablecoin delta ≈ 0. The strategy earns
  yield on USD-denominated capital without directional exposure.

- **ETH share class**: Portfolio should maintain net delta in ETH equal to total equity / ETH price. An ETH-denominated
  investor wants to grow their ETH stack, not just USD. Basis strategies provide yield while being long ETH via
  collateral.

- **BTC share class**: Same as ETH but denominated in BTC. BTC basis strategies deposit WBTC on Aave and short BTC
  perps. The portfolio is net long BTC in collateral terms.

Drift from target is monitored by `evaluate_base_currency_drift()` in the risk engine:

```
drift_warning:  >2% deviation from target
drift_critical: >5% deviation from target
```

## Rebalancing Logic (Threshold-Based)

Rebalancing is triggered when delta drift exceeds the configured warning threshold. The flow:

1. `risk-and-exposure-service` emits `BASE_CURRENCY_DRIFT` alert via Pub/Sub.
2. `strategy-service` consumes the alert and generates a `REBALANCE` instruction.
3. `execution-service` routes the rebalance instruction through the appropriate algo (e.g. `AMM_CONCENTRATED` for LP
   range adjustment, `SOR_DEX` for spot swap).

Rebalancing is always instruction-based — no position management happens inside the risk service. The risk service
detects and alerts; strategy and execution services act.

## P&L Attribution with FX Component

When share class != USD, P&L is decomposed into two components:

```
total_pnl_share_class = strategy_pnl_usd / fx_rate + fx_pnl
```

Where:

- `strategy_pnl_usd`: P&L from yield, funding rates, fees (computed in USD by execution-service).
- `fx_pnl`: Change in `account_equity_share_class` due to share class price movement. For ETH share class with ETH at
  $3,500 → $3,800: fx_pnl = equity_eth \* 300/3500.

`RiskMetrics.account_equity_share_class` = `account_equity_usd / share_class_fx_rate` is computed by
`compute_risk_metrics()` and stored for P&L decomposition downstream.

## Cross-Service Data Flow

```
UAC (ShareClass enum)
    |
    +--> strategy-service
    |       - StrategyConfig.share_class field
    |       - Generates instructions aligned to base currency
    |
    +--> execution-service
    |       - Fills include share_class from instruction context
    |       - P&L computed in USD, stored with share_class tag
    |
    +--> position-balance-monitor-service
    |       - Tracks account_equity per share class
    |       - Publishes RiskPosition with venue + instrument
    |
    +--> risk-and-exposure-service
    |       - compute_risk_metrics(): account_equity_share_class
    |       - evaluate_margin_currency_mismatch(): CeFi margin alignment
    |       - evaluate_base_currency_drift(): DeFi delta alignment
    |       - Emits AlertMessage to Pub/Sub
    |
    +--> UI (lib/types/defi.ts ShareClass type)
            - ShareClass selector component
            - Risk widgets filter/group by share class
            - P&L displayed in base currency
```

### UAC Type Location

`ShareClass` enum is defined in `unified_api_contracts` and consumed by all services. The UI type in `lib/types/defi.ts`
mirrors it for TypeScript type safety (`USDT | ETH | BTC`).

### E2E Config

All strategy configs in `e2e-testing/configs/defi/strategies/` declare `share_class: "USDT"` as the default. Override
per-strategy for ETH/BTC scenarios.
