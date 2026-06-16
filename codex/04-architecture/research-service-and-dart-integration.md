---
scope: [engineer, admin]
last_reviewed: 2026-05-17
---

# Research-service ↔ DART integration

## What this doc covers

DART (Decision And Risk Terminal) is the operator-facing manual-trade gate for live-mode trading. Research-service is
the offline strategy / signal authoring surface. They share the strategy + execution code path but expose two distinct
operator workflows. This doc names the boundary.

## DART manual-trade lane (operational mode "manual")

In manual mode, every trade requires explicit operator confirmation in DART before execution-service places the order.
Five lanes are first-class:

| Surface             | Action                                            | Approval surface                            |
| ------------------- | ------------------------------------------------- | ------------------------------------------- |
| DeFi swap           | Uniswap / Curve / Balancer swap                   | DART → execution-service `UniswapConnector` |
| DeFi lend / stake   | Aave deposit, Lido stake, jitoSOL/mSOL/bSOL stake | DART → execution-service DeFi connectors    |
| CeFi orders         | Spot / perp limit / market on Bybit/Binance/etc.  | DART → execution-service order adapters     |
| ML training trigger | Manual retrain a model                            | DART → ml-training-service                  |
| Sports bet          | Pre-match outright / in-play tick                 | DART → execution-service sports adapter     |
| Prediction-market   | Polymarket / Kalshi market take                   | DART → execution-service prediction adapter |

Each lane:

- Renders the proposed order pre-confirmation (size, side, venue, price-with-bands, expected slippage).
- Requires explicit operator click-to-confirm; no implicit approval, no batch approval.
- Logs the manual decision via `unified-trading-library` lifecycle events with the operator's identity from DART auth.
- Routes through the **same** execution-service code path as automated mode — only the approval gate differs.

Full lane spec:
[`../09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md`](../09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md).

## Research-service surface

Research-service serves three functions:

1. **Strategy authoring** — register a strategy archetype config for backtest. Live = batch (CLAUDE.md "Batch = Live") —
   once authored, the same config drives batch (matching engine fills) and live (real fills) without divergence.
2. **Signal exploration** — read MDPS / features-service outputs, run ad-hoc analyses, draft a signal definition. The
   signal definition graduates to a strategy archetype when the operator promotes it.
3. **Backtest review** — read batch P&L attribution + execution alpha measurement.

Research-service does NOT execute live orders. Live execution always flows through DART → execution-service.

## Boundary

| Concern              | Research-service | DART               | execution-service                  |
| -------------------- | ---------------- | ------------------ | ---------------------------------- |
| Backtest             | ✓                | ✗                  | matching engine (always-fill mode) |
| Live order placement | ✗                | approval gate      | order adapter / DeFi connector     |
| Strategy config      | author           | display + override | consume                            |
| Operator audit log   | per-strategy     | per-trade          | per-fill                           |

## Cross-references

- DART manual-trade spec:
  [`../09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md`](../09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md)
- Operational modes matrix:
  [`../09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md`](../09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md)
- Strategy summary: [`../09-strategy/strategy-summary.md`](../09-strategy/strategy-summary.md)
- Live = batch: [`batch-live-architecture.md`](batch-live-architecture.md) (single SSOT)
- Execution architecture: [`defi-execution-overview.md`](defi-execution-overview.md) +
  [`interface-credential-convention.md`](interface-credential-convention.md)
