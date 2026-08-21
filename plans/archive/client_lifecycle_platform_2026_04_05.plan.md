---
doc_type: plan
title: client-lifecycle-platform
summary: 'Client lifecycle platform: exchange data collection, performance dashboards, invoice lifecycle, trade history,
  CSV exports'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, execution-service, unified-api-contracts, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-14'
type: mixed
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: B6}
repo_gates:
- {repo: unified-api-contracts, code: C1, deployment: none, business: none}
- {repo: client-reporting-api, code: C0, deployment: none, business: none}
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none}
- {repo: execution-service, code: C1, deployment: none, business: none}
depends_on: []
todos:
- {id: phase1-uac-schemas, content: '- [x] [AGENT] P0. Create UAC schemas for performance, trades, invoice, balance_snapshot in internal/domain/client_reporting/

    ', status: done}
- {id: phase2-exchange-collector, content: '- [x] [AGENT] P0. Build ExchangeDataCollector (CCXT-based) in client-reporting-api for Binance+OKX balance/position/trade/transfer fetching

    ', status: done}
- {id: phase2-credentials-registry, content: '- [x] [AGENT] P1. Add ODUM_PROP to credentials-registry.yaml, fix tranche_router path

    ', status: done}
- {id: phase3-api-performance, content: '- [x] [AGENT] P0. Create performance API routes (summary, equity-curve, monthly-returns, positions, balances) in client-reporting-api

    ', status: done}
- {id: phase3-api-trades, content: '- [x] [AGENT] P0. Create trades API routes (history, coin-breakdown) and clients list route in client-reporting-api

    ', status: done}
- {id: phase3-ui-dashboard, content: '- [x] [AGENT] P0. Build TradeLink-style performance dashboard page in unified-trading-system-ui with equity curve, monthly returns heatmap, stats grid, positions table, coin breakdown

    ', status: done}
- {id: phase3-ui-hooks, content: '- [x] [AGENT] P1. Create React Query hooks (use-performance.ts) and mock fixtures (performance-data.ts)

    ', status: done}
- {id: phase4-invoice-engine, content: '- [x] [AGENT] P0. Invoice state machine (DRAFT->ISSUED->ACCEPTED->PAID, DISPUTED->VOIDED) with dual HWM mock data in invoices.py

    ', status: done}
- {id: phase4-invoice-ui, content: '- [x] [AGENT] P1. Build invoice generation modal, detail drawer, status badges, action buttons in unified-trading-system-ui

    ', status: done}
- {id: phase4-trade-history-ui, content: '- [x] [AGENT] P1. Build trade history page with filters (client, symbol, side) and sortable columns

    ', status: done}
- {id: phase5-csv-exports, content: '- [x] [AGENT] P1. Create streaming CSV export endpoints (hourly snapshots, daily summary, trades, coin-breakdown)

    ', status: done}
- {id: phase5-fund-of-fund, content: '- [x] [AGENT] P2. Build manual entry routes for fund_of_fund clients (YOAV, GUY_ASRAF) — POST/GET snapshots and returns

    ', status: done}
- {id: phase5-portfolio-analytics, content: '- [x] [AGENT] P2. Build portfolio analytics page (allocation pie, correlation matrix, risk metrics)

    ', status: done}
- {id: phase5-tax-reporting, content: '- [x] [AGENT] P2. Build tax reporting endpoint (FIFO cost-basis, annual realized P&L summary) + CSV export

    ', status: done}
isProject: false
---

## Context

Build a complete client lifecycle platform that pulls live performance data from OKX and Binance exchanges using
read-only API keys stored in GCP Secret Manager. Provides TradeLink.pro-quality performance dashboards (equity curves,
monthly P&L, stats, coin breakdowns), full invoice lifecycle with dual high-water mark fee calculations (from mr_report
billing model), trade/order history, and CSV exports at hourly/daily/per-trade granularity. versa-client-reporting gets
merged into unified-trading-system-ui. Fund-of-fund clients (BTC Edge) supported via manual data entry.

## Dependency DAG

```
Phase 1 (UAC Schemas) ──DONE──> Phase 2 (Data Collection) ──QG──> Phase 3 (API + UI Dashboard)
                                                                         |
                                                                    ──QG──> Phase 4 (Invoice + Trade History)
                                                                                  |
                                                                             ──QG──> Phase 5 (Exports + Analytics)
```

## Pre-Audit Manifest

All changes are NET-NEW additions. No symbols moved, deleted, or renamed.

| Repo                      | Change Type                                      | Impact                           |
| ------------------------- | ------------------------------------------------ | -------------------------------- |
| unified-api-contracts     | New schemas in internal/domain/client_reporting/ | No downstream breaks -- additive |
| client-reporting-api      | New core modules + API routes                    | Self-contained                   |
| unified-trading-system-ui | New pages + components                           | Self-contained                   |
| execution-service         | credentials-registry.yaml update                 | Additive -- new ODUM_PROP entry  |

## Success Criteria

- Phase 1: UAC QG passes
- Phase 2: client-reporting-api QG passes, ExchangeDataCollector unit tests pass
- Phase 3: API endpoints return mock data, UI renders performance dashboard in mock mode
- Phase 4: Invoice lifecycle works end-to-end in mock mode, trade history page renders
- Phase 5: CSV downloads work, manual entry works, portfolio analytics renders
