---
type: analysis
title: Global Ledger Audit — client-reporting-api
epic: global_ledger_pnl_attribution_master
auditor: slot-7
date: "2026-05-23"
status: complete
source:
  - global_ledger_pnl_attribution_discovery_2026_05_21.md Phase 1 audit task
scope: client-reporting-api consumer-side audit
---

# Global Ledger Audit: client-reporting-api (2026-05-23)

**Audit type**: Read-only, consumer-side. client-reporting-api does NOT write SSOT ledgers — it is a downstream
consumer.

**Files read**: all Python source under `client_reporting_api/` (86 source files, ~3,500 lines).

---

## What it computes today

### NAV computation

Two separate NAV computation paths exist, served by different route families:

**Path A — Backfill-sourced NAV** (`/reporting/nav`, `/reporting/performance/*`):

- Position data: daily equity snapshots from `data/backfill/{client_id}/equity_curve.json` — a pre-loaded JSON file on
  disk, not a live GCS feed.
- Mark prices: not separated from equity — the equity_curve.json stores total equity_usd directly. No per-instrument
  mark price is exposed; unrealised P&L from open positions is embedded in the equity total.
- Transfer detection: `transfer_usd` flags embedded in equity_curve.json points; for BTC accounts, detected via BTC/USDT
  balance delta logic in `backfill_store.py`.
- Reporting periods: daily equity curve (full history); no explicit monthly/quarterly partitioning at read time — the
  caller controls period.

**Path B — Live-exchange NAV** (`/api/v1/performance/summary` via ExchangeDataCollector):

- Position data: live CCXT `fetch_balance()` + `fetch_positions()` on OKX/Binance.
- Mark prices: live `fetch_ticker()` per non-stablecoin asset; exchange-sourced mark price on each position (CCXT
  `markPrice` field).
- No independent pricing ledger — entirely dependent on exchange API responses.

**Path C — Attribution-ledger NAV** (`/api/v1/clients/{client_id}/nav`):

- Reads `pnl_attribution/strategy_id={S}/client_id={C}/date={D}/rows.parquet` from the `client-reports` GCS bucket via
  `attribution_reader.py`.
- NAV is computed by summing `amount` fields across all attribution rows per date — this is an approximate NAV, not a
  fund-accounting NAV.
- No marks, no positions — purely P&L amount aggregation.

### PnL metrics

**Realised PnL**:

- Bills ledger path: parsed from `data/backfill/{client_id}/bills_ledger.json` (OKX raw bill records) in
  `trade_analytics.py`. Sub-type 5 = realised P&L on close.
- Fills path: CCXT `fillPnl` field from trades in `reporting/trades.py`. Read from
  `data/backfill/{client_id}/trades.json`.
- Attribution ledger path: `attribution_reader.py` reads `PnLAttributionRow` parquets from GCS; realised P&L hardcoded
  to "0.00" in `_pnl_from_rows()` — only total attribution amount is exposed. **Realised vs unrealised split is NOT
  populated from parquet data.**

**Unrealised PnL**:

- Live path: CCXT `fetch_positions()` → `unrealizedPnl` per position.
- Backfill path: `positions.json` snapshot read in `reporting/performance.py` / `attribution.py`.
- Attribution path: all PnL shown as `unrealized_pnl` in `_pnl_from_rows()` because attribution rows do not carry a
  realised/unrealised flag.

**TWR (Time-Weighted Return)**: computed in `backfill_store.py` using
`unified_trading_library.performance_metrics.twr_equity_curve()` — this is the SSOT formula. Transfer-adjusted daily
returns chained; Sharpe/Sortino/Calmar also delegated to UTL.

**Funding P&L**: extracted from bills ledger sub-types 173/174 or bill type 8 in `trade_analytics.py`. Exposed on
`/performance/coin-breakdown` as `funding_pnl`.

### Attribution metrics

Attribution is present but shallow:

- **By factor × layer**: `PnLAttributionRow` parquets under `pnl_attribution/` partition. Factors are strings (e.g.
  `CARRY`, `SLIPPAGE`). Layers are `STRATEGY` / `EXECUTION`. Served at `GET /api/v1/clients/{client_id}/attribution`.
  Strategy-alpha vs execution-alpha totals computed per date.
- **By strategy_id**: attribution rows carry `strategy_id`; the waterfall endpoint returns this field raw.
- **By venue**: attribution rows carry `venue` field; returned raw.
- **By archetype_id**: attribution rows carry `archetype_id`; returned raw.
- **By instrument**: attribution rows carry `instrument_id`; returned raw.
- **No aggregation** across strategies or archetypes — client is responsible for grouping.

**Sports attribution**: separate path via `sports_pnl_reader.py` reading
`pnl/sports/{period_month}/{client_id}/sports_pnl.parquet`. Breakdown by venue and strategy_id. CLV edge % included.
Completely separate from the CeFi/DeFi attribution flow.

### Reporting periods

- **On-demand**: most endpoints accept `date_from` / `date_to` query params.
- **Monthly**: `period_month` (YYYY-MM) used by `pnl_reader.py` and `sports_pnl_reader.py`.
- **HWM crystallization timeline**: quarterly events via `hwm_reader.py`.
- **No batch scheduled reports**: all computation is on-demand at API call time.

---

## API surface

| Endpoint                                       | What it returns                                                        | Data source                                                 |
| ---------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------- |
| `GET /pnl?client_id&period_month`              | PnL rows from GCS parquet                                              | `pnl/{YYYY-MM}/{client_id}/` GCS parquet via UCI DataSource |
| `GET /performance?client_id&period_month`      | Status only (live mode: empty metrics)                                 | Same GCS pnl parquet                                        |
| `GET /api/v1/performance/summary`              | Equity, balances, unrealised PnL, equity curve, monthly returns, stats | Live CCXT (OKX/Binance) + backfill JSON                     |
| `GET /api/v1/performance/positions`            | Open positions with unrealised P&L                                     | Live CCXT                                                   |
| `GET /api/v1/performance/balances`             | Per-asset balance breakdown                                            | Live CCXT                                                   |
| `GET /api/v1/performance/coin-breakdown`       | Realised PnL / fees / funding per coin                                 | bills_ledger.json + trades.json (disk)                      |
| `GET /api/v1/clients/{client_id}/nav`          | Daily NAV time-series                                                  | pnl_attribution GCS parquet (sum of amounts)                |
| `GET /api/v1/clients/{client_id}/pnl`          | Daily strategy_alpha + execution_alpha series                          | pnl_attribution GCS parquet                                 |
| `GET /api/v1/clients/{client_id}/positions`    | Current positions (MOCK only, Phase 8 pending)                         | Mock stub                                                   |
| `GET /api/v1/clients/{client_id}/attribution`  | PnLAttributionRow waterfall by factor × layer                          | pnl_attribution GCS parquet                                 |
| `GET /api/v1/clients/{client_id}/hwm-timeline` | HWM crystallization events                                             | fee_recognition GCS parquet (client-statements bucket)      |
| `GET /api/v1/trades`                           | Paginated fills with fees and realized P&L                             | Live CCXT → fallback to trades.json (disk)                  |
| `GET /reporting/nav`                           | Fund-level NAV aggregate + investor breakdown + capital flows          | equity_curve.json (disk) + invoice state                    |
| `GET /reporting/performance/summary`           | Per-client performance: TWR, Sharpe, HWM, etc.                         | equity_curve.json (disk)                                    |
| `GET /reporting/performance/coin-breakdown`    | Coin-level PnL                                                         | bills_ledger.json + trades.json (disk)                      |
| `GET /reporting/performance/positions`         | Open positions from snapshot                                           | positions.json (disk)                                       |
| `GET /reporting/performance/balances`          | Balance breakdown                                                      | balance.json (disk)                                         |
| `GET /reporting/trades`                        | Paginated trade history                                                | trades.json (disk)                                          |
| `GET /reporting/settlements`                   | Trade-derived settlement rows + invoice list                           | trades.json (disk) + invoice state                          |
| `GET /reporting/fund-operations`               | Investor register + capital accounts + distribution waterfall          | equity_curve.json (disk) + pnl_series compute               |
| `GET /reporting/reports`                       | Portfolio overview + generated HTML reports + invoices + transfers     | equity_curve.json + invoice state                           |
| `GET /api/v1/sports/*`                         | Sports P&L by venue/strategy, CLV, venue performance, positions        | pnl/sports/ GCS parquet                                     |

---

## Data sources today

### 1. GCS parquets (canonical paths)

| Path pattern                                                          | Content                                               | Read by                                   |
| --------------------------------------------------------------------- | ----------------------------------------------------- | ----------------------------------------- |
| `pnl/{YYYY-MM}/{client_id}/`                                          | Generic PnL rows (schema unknown)                     | `pnl_reader.py` via UCI DataSource        |
| `pnl/sports/{YYYY-MM}/{client_id}/`                                   | Sports PnL rows with profit_loss, stake, clv_edge_pct | `sports_pnl_reader.py` via UCI DataSource |
| `pnl_attribution/strategy_id={S}/client_id={C}/date={D}/rows.parquet` | PnLAttributionRow records                             | `attribution_reader.py` direct GCS        |
| `{client_id}/fee_recognition/{date}/*.parquet`                        | FeeRecognitionRow records                             | `hwm_reader.py` direct GCS                |
| `positions/latest/{client_id}/sports/`                                | Sports position snapshots                             | `sports_pnl_reader.py` via UCI DataSource |

### 2. Local disk JSON (backfill data, NOT GCS)

Location: `data/backfill/{client_id}/` relative to repo root. Loaded from disk at runtime.

| File                | Content                                                        | Used by                                   |
| ------------------- | -------------------------------------------------------------- | ----------------------------------------- |
| `equity_curve.json` | Daily equity_usd snapshots with transfer_usd flags             | backfill_store.py, pnl_chart_generator.py |
| `bills_ledger.json` | OKX raw bill records (realised P&L, fees, funding by sub-type) | trade_analytics.py                        |
| `trades.json`       | CCXT trade records                                             | backfill_store.py, reporting/trades.py    |
| `transfers.json`    | CCXT deposit/withdrawal records                                | transfer_collector.py                     |
| `positions.json`    | Position snapshot                                              | reporting/performance.py                  |
| `balance.json`      | Asset balance snapshot                                         | reporting/performance.py                  |
| `summary.json`      | Backfill metadata (venue, equity_source)                       | backfill_store.py                         |

**Known clients in hardcoded CLIENT_IDS list**: `PR`, `NN`, `ET`, `STD`, `GP`, `SL`, `SL2`, `ANU`, `IK`, `ODUM_PROP`.
This is a static constant in `trade_analytics.py` — not driven by the canonical client registry.

### 3. Live exchange API (CCXT, read-only)

- OKX and Binance via CCXT.
- Credentials from GCP Secret Manager: `exec-{client_lower}-{venue}-api-key` + `-api-secret` + `-passphrase`.
- Fetches: balance, positions, trades, deposits/withdrawals.
- Used only by `/api/v1/performance/*` and `/api/v1/trades` endpoints in live mode.

### 4. Invoice state (in-memory, Firestore-backed)

- Invoice CRUD managed by `invoice_state.py` and `InvoiceStateManager`.
- Consumed by `/reporting/settlements`, `/reporting/reports`, `/reporting/fund-operations`, `/reporting/nav`.

### 5. NOT consumed

- **No calls to strategy-service API.** Zero HTTP calls to strategy-service.
- **No calls to execution-service API.**
- **No calls to instruments-service API.**
- **No reads from MTDS parquets.**
- **No reads from features-service parquets.**

---

## Target model alignment

In the target model, client-reporting-api joins from:

1. **InstructionLedger** — fills/transfers as the instruction-level atomic record.
2. **PassiveLedger** — funding payments, dividends, staking rewards.
3. **PricingLedger** — per-instrument mark prices for unrealised P&L computation.
4. **PositionLedger** (strategy-service derived) — aggregated positions per client.
5. **PnLLedger** (strategy-service derived) — realised/unrealised P&L per client.

### Per-join assessment

| Target ledger                            | Already happening (partially)                                                                                                                                                                                                                                              | Status                                                      |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **InstructionLedger** (fills)            | Yes — fills read from CCXT live + trades.json backfill. Attribution rows carry `fill_id`. But the data is not joined FROM a canonical InstructionLedger — it is sourced directly from exchanges or disk JSON.                                                              | PARTIAL — shape exists, SSOT not connected                  |
| **InstructionLedger** (transfers)        | Yes — `transfer_collector.py` + `transfer_store.py` collect TransferRecord from CCXT + equity curve flags. Conforms to `unified_api_contracts.internal.TransferRecord`.                                                                                                    | PARTIAL — UAC type used, but source is ad-hoc               |
| **PassiveLedger** (funding)              | Yes — funding extracted from bills ledger sub-types 173/174. Exposed on `coin-breakdown` endpoint. NOT read from a canonical PassiveLedger parquet.                                                                                                                        | PARTIAL — data exists, no canonical join                    |
| **PricingLedger** (marks for unrealised) | Partially — live mode fetches mark prices from exchange via CCXT. No PricingLedger parquet read anywhere. Unrealised from attribution rows is inferred from total attribution amount, not priced positions.                                                                | MISSING for canonical mark prices; live exchange marks only |
| **PositionLedger** (positions)           | Partially — positions read from CCXT live or `positions.json` snapshot. Attribution route `/api/v1/clients/{client_id}/positions` is MOCK ONLY (comment: "Phase 8 demo run").                                                                                              | MISSING canonical join; live exchange + disk snapshot only  |
| **PnLLedger** (strategy-service)         | Not connected. The service reads `PnLAttributionRow` parquets from the `client-reports` GCS bucket (writer: UTL `emit_attribution_parquet`). Whether these rows originate from strategy-service's PnLLedger is unclear — the writer is UTL, not strategy-service directly. | UNCLEAR lineage; no explicit strategy-service join          |

---

## Gap to target model

### G1. No canonical InstructionLedger join

Current state: fills come from CCXT live or disk JSON. The canonical InstructionLedger (if it exists in strategy-service
or execution-service as a parquet/GCS asset) is not read.

Required change: `attribution_reader.py` (or a new `instruction_ledger_reader.py`) should join fills from
`InstructionLedger` canonical path. `fill_id` field is already present on `PnLAttributionRow` — the FK exists, the join
does not.

### G2. No PricingLedger join — unrealised P&L is ad-hoc

Current state: unrealised P&L sourced from:

- Live: CCXT exchange mark prices (correct for live view, not auditable).
- Attribution: total `amount` from `PnLAttributionRow`, no mark price applied.
- Backfill: `equity_usd` total from equity_curve.json (no per-instrument breakdown).

Required change: read per-instrument marks from `PricingLedger` canonical parquet and multiply against open positions
from PositionLedger to compute auditable unrealised P&L.

### G3. Position data is not canonical

Current state: positions from CCXT `fetch_positions()` (live) or `positions.json` snapshot (disk). The
`/api/v1/clients/{client_id}/positions` endpoint is **MOCK only** — no live data feed connected (comment: "Phase 8 demo
run").

Required change: connect to PositionLedger parquet written by strategy-service or a position-balance-monitor service.
The positions.json disk file is a one-time backfill snapshot, not a continuous pipeline.

### G4. Realised vs unrealised split broken in attribution path

Current state: `_pnl_from_rows()` hardcodes `realized_pnl: "0.00"` and puts all PnL into `unrealized_pnl`. Attribution
rows do not carry a realized/unrealized flag.

Required change: PnLAttributionRow schema needs a `pnl_type: realized | unrealized` field, or client-reporting-api must
join against InstructionLedger to determine which attribution rows correspond to closed fills (realised).

### G5. Bills ledger is not a canonical ledger — it is raw exchange data

Current state: coin-level PnL breakdown reads OKX raw bill records (bills_ledger.json). Sub-type parsing
(`sub_type == "5"` for realised, `sub_type in ("173", "174")` for funding) is hard-coded OKX semantics.

Required change: the PassiveLedger should carry funding records in a venue-agnostic schema. The InstructionLedger should
carry fee records. client-reporting-api should join canonical ledgers, not parse raw OKX bill records.

### G6. Hardcoded client list in trade_analytics.py

`CLIENT_IDS = ["PR", "NN", "ET", "STD", "GP", "SL", "SL2", "ANU", "IK", "ODUM_PROP"]`

This static constant controls which clients are processed in `compute_all_clients()`. In the target model, the client
list should be derived from the InstructionLedger / canonical client registry. New clients are not picked up until this
constant is updated.

### G7. Equity curve is a disk JSON, not a GCS ledger

The primary data source for NAV, TWR, HWM, drawdown, monthly returns, capital flows — the `equity_curve.json` disk file
— is a pre-computed, manually-backfilled artifact.

In the target model, NAV snapshots should come from the PnLLedger (or a dedicated BalanceLedger) written continuously by
strategy-service or execution-service as GCS parquets with manifest tracking. The disk backfill is not monitored by the
manifest system.

### G8. Transfer detection is heuristic, not ledger-derived

Current state: transfers inferred from equity curve `transfer_usd` flags and BTC balance delta heuristics. "Large USDT
jumps > $500" threshold hard-coded in multiple places.

Required change: transfers should be read directly from InstructionLedger transfer records where
`instruction_type = DEPOSIT | WITHDRAWAL`. The `TransferRecord` UAC type is already used — the source needs to be the
canonical ledger, not equity curve inference.

### G9. Treasury / fund-flow visibility is incomplete

Current state: `/reporting/nav` and `/reporting/fund-operations` show deposits/withdrawals derived from the equity curve
heuristics above. No connection to execution-service transfer events or bridge operations.

Required change: treasury visibility should join InstructionLedger transfer records across all execution-service venues,
including DeFi bridging (CCTP) and on-chain staking inflows.

### G10. Attribution ledger path is valid — lineage needs verification

The `pnl_attribution/` GCS parquet join is the most canonical data feed today. However, the writer (UTL
`emit_attribution_parquet`) is not clearly traced to a strategy-service PnLLedger. If attribution rows are emitted by
strategy-service's ledger output, this is the correct join. If they are emitted by a separate batch computation, the
lineage is incomplete.

**Recommended action**: trace the writer of `pnl_attribution/` parquets and confirm it is driven by the canonical
PositionLedger + InstructionLedger, not a parallel computation.

---

## Summary: current vs target

| Dimension                    | Current                       | Target                       | Gap severity |
| ---------------------------- | ----------------------------- | ---------------------------- | ------------ |
| Fill data                    | CCXT live + disk JSON         | InstructionLedger parquet    | HIGH         |
| Transfer data                | Equity curve heuristic + CCXT | InstructionLedger transfers  | HIGH         |
| Mark prices (unrealised PnL) | CCXT live ticker              | PricingLedger parquet        | HIGH         |
| Open positions               | CCXT live + disk JSON + MOCK  | PositionLedger parquet       | HIGH         |
| Realised/unrealised split    | Broken in attribution path    | InstructionLedger join       | HIGH         |
| Funding P&L                  | OKX-specific bill parsing     | PassiveLedger parquet        | MEDIUM       |
| NAV snapshots                | Disk equity_curve.json        | PnLLedger / BalanceLedger    | HIGH         |
| Attribution waterfall        | PnLAttributionRow GCS parquet | Same (lineage needs tracing) | LOW-MEDIUM   |
| HWM crystallization          | FeeRecognitionRow GCS parquet | Same                         | LOW          |
| Sports P&L                   | Sports GCS parquet            | Same                         | LOW          |
| Client list                  | Hardcoded constant            | Canonical client registry    | MEDIUM       |
| Strategy-service coupling    | NONE                          | Must read derived ledgers    | HIGH         |

**Overall readiness for canonical ledger model: LOW.** The attribution and HWM paths are the only GCS-parquet-based
joins. All performance/NAV/trade data flows through either CCXT live or pre-loaded disk JSON that has no manifest
tracking and no honest-absence enforcement.
