---
scope: [engineer, admin]
last_reviewed: 2026-05-28
---

# `pipeline_mode` Column — Batch/Live Reconciliation

> **STATUS** — Documents the `pipeline_mode` manifest column. On-disk partition is IN PROGRESS as a named rider per AG
> L3 walk (see § "On-disk partition" below). Implementation plan:
> [`plans/active/pipeline_mode_implementation_2026_05_28.md`](../../plans/active/pipeline_mode_implementation_2026_05_28.md).

## What `pipeline_mode` is

`pipeline_mode` is a `StrEnum` column on every availability manifest row that identifies **which pipeline wrote it** — a
batch source (Tardis archive, Databento, onchain RPC, etc.) or the live websocket feed. It enables batch ↔ live
reconciliation via `GROUP BY pipeline_mode` over the same manifest without a separate table.

The canonical enum is `unified_api_contracts.canonical.crosscutting.pipeline_mode.PipelineMode`:

| Value                                  | Source                           |
| -------------------------------------- | -------------------------------- |
| `batch_tardis`                         | Tardis archive (default CeFi)    |
| `batch_databento`                      | Databento (default TradFi)       |
| `batch_hyperliquid_rest`               | Hyperliquid REST API             |
| `batch_onchain_rpc`                    | EVM / Solana native RPC          |
| `batch_onchain_subgraph`               | DeFi subgraph (Uniswap etc.)     |
| `batch_polymarket_clob`                | Polymarket CLOB + Kalshi         |
| `batch_polymarket_gamma_api`           | Polymarket Gamma API             |
| `batch_api_football`                   | API-Football (sports)            |
| `batch_barchart`                       | Barchart (TradFi VIX historical) |
| `batch_yahoo`                          | Yahoo Finance                    |
| `batch_eia`                            | EIA energy/commodity             |
| `batch_chainlink`                      | Chainlink oracle                 |
| `batch_pyth_hermes`                    | Pyth Hermes (Solana)             |
| `batch_solana_rpc`                     | Solana native RPC                |
| `batch_helius_rpc`                     | Helius enriched RPC              |
| `batch_instruments_service`            | Instruments service internal     |
| `batch_strategy_service`               | Strategy service internal        |
| `batch_execution_service`              | Execution service internal       |
| `batch_mdps_odds_horizon_bucket`       | MDPS odds/horizon bucket         |
| `batch_features_onchain_service`       | Features onchain service         |
| `batch_cross_instrument`               | Cross-instrument features        |
| _(…more batch values in PipelineMode)_ |                                  |
| `live_websocket`                       | Real-time WebSocket feed (MTDS)  |

## How to resolve `pipeline_mode` at write time

Use the UTL SSOT helper — never hardcode string literals:

```python
from unified_trading_library import resolve_pipeline_mode

pm = resolve_pipeline_mode(
    service="market-tick-data-service",
    mode="batch",          # or "live"
    venue="BINANCE",       # optional — venue override wins
    asset_group="cefi",    # optional — consulted via SOURCE_PRIORITY
    data_type="trades",    # optional — paired with asset_group
)
# → PipelineMode.BATCH_TARDIS
```

Resolution order:

1. `mode="live"` → always `LIVE_WEBSOCKET`
2. Venue override (e.g. `HYPERLIQUID` → `BATCH_HYPERLIQUID_REST`)
3. UAC `read_with_source_priority(asset_group, data_type)` → primary source's mode
4. Per-service fallback (`instruments-service` → `BATCH_INSTRUMENTS_SERVICE`, etc.)
5. `ValueError` if nothing matches — add to `_VENUE_OVERRIDES` or UAC SOURCE_PRIORITY

## How to derive `pipeline_mode` for backfill

For existing rows (NULL `pipeline_mode`), use `derive_pipeline_mode_for_row()`:

```python
from unified_trading_library import derive_pipeline_mode_for_row

pm = derive_pipeline_mode_for_row(
    venue="BINANCE",
    asset_group="cefi",
    data_type="trades",
    pipeline_mode_col=existing_row_value,  # idempotent: returned as-is if valid
)
# → PipelineMode.BATCH_TARDIS, or None if undecidable
```

The one-shot backfill script lives at `unified-trading-pm/scripts/migration/backfill_pipeline_mode.py`.

## Batch ↔ live reconciliation pattern

Stage 0 of `batch-live-reconciliation-service` compares the batch vs live sides of the manifest for each date by
filtering on `pipeline_mode`:

- **Batch side**: any row where `pipeline_mode.startswith("batch_")`
- **Live side**: any row where `pipeline_mode == "live_websocket"`

```
manifest rows (same bucket, same date)
├── batch_tardis rows  → batch_status, batch_reason
└── live_websocket rows → live_status, live_reason

Agreement rules:
  both captured                           → OK
  both empty_confirmed, same reason       → OK (agreed expected gap)
  both empty_confirmed, different reasons → FLAG (reason disagreement)
  one captured, other attempted_failed    → FLAG (asymmetric failure)
  one or both absent from manifest        → skip (fail-open)
  unknown combination                     → log warning, no flag
```

## NOT NULL constraint status

As of 2026-05-28, `pipeline_mode` allows NULL in the schema — ~38M legacy rows written before Phase 4.MTDS (2026-05)
have NULL. The NOT NULL constraint will be enforced after the backfill verifies clean
(`SELECT count(*) WHERE pipeline_mode IS NULL = 0` per bucket).

## On-disk partition (IN PROGRESS as named rider per AG L3 walk)

Adding `pipeline_mode=` as a hive partition key on disk is **IN PROGRESS** — re-scoped from "Phase 5 DEFERRED" to a
named **rider** inside each asset-group's L3 single-walk per
`plans/active/pipeline_mode_partition_migration_2026_06_01.md`. Reads continue to filter via column-scan (low
cardinality, ~10 values) until each per-bucket rider completes.

**Per-bucket rider coverage** (as of 2026-06-01):

| Bucket / asset-group      | Rider status                   | Notes                                      |
| ------------------------- | ------------------------------ | ------------------------------------------ |
| `market-data-tick-cefi`   | In L3 walk plan                | Rider confirmed in AG cefi L3 walk scope   |
| `market-data-tick-defi`   | In L3 walk plan                | Rider confirmed in AG defi L3 walk scope   |
| `market-data-tick-tradfi` | In L3 walk plan                | Rider confirmed in AG tradfi L3 walk scope |
| `market-data-tick-sports` | In L3 walk plan                | Rider confirmed in AG sports L3 walk scope |
| `instruments-store-*`     | **Pending** — not yet in scope | instruments bucket rider not yet scheduled |

See: [`pipeline-mode-partition.md`](pipeline-mode-partition.md) for the Phase 3 migration history (2026-05-19
hive-partition walk).

## Cross-links

- [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md)
- [`contracts-scope-and-layout.md`](contracts-scope-and-layout.md)
- [`pipeline-mode-partition.md`](pipeline-mode-partition.md) — on-disk partition history
