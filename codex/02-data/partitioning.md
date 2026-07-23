---
doc_type: codex-ssot
title: Data Partitioning Conventions
summary: >-
  Data partitioning conventions SSOT — the universal by_date/day={date} hive axis, bucket naming
  {domain}-{asset_group}-{project_id} (canonical asset_group= vs legacy category=), per-service extra dims
  (data_type/instrument_type/timeframe/feature_group), the BigQuery external-table hive requirement, and live/ vs
  by_date/ micro-batch routing with end-of-day GCS compose.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, market-data-processing-service, market-tick-data-service]
scope: [engineer, admin]
tags: [partitioning, manifest, data-pipeline, mtds, mdps, features]
related: [/codex/02-data/per-asset-group-bucket-layouts.md, /codex/02-data/availability-manifest-and-data-status.md]
created: 2026-03-27
authoritative_for:
  [GCS hive-partitioning conventions, BigQuery external-table partition requirement, live-vs-batch GCS path routing]
referenced_by:
  [
    /codex/02-data/README.md,
    /codex/02-data/chart-candle-delivery-flow.md,
    /codex/02-data/data-lineage-MTDS-features-ml.md,
    /codex/02-data/instrument-pipeline-defi.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /codex/02-data/schema-governance.md,
    /codex/02-data/shard-granularity-cefi.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Data Partitioning Conventions

<!-- MULTI_AXIS_CORRECTION_2026_05_06 -->

> **Multi-axis correction (2026-05-06)** — shard atoms vs display axes (row-level columns) per asset_group are the SSOT
> in
> [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md#multi-axis-correction-banner-canonical).
> See that doc for the full per-asset-group shard-atom matrix (sports / prediction / cefi options-futures / DeFi chain /
> ML+strategy+execution job_id / TradFi EVENT_CONTRACT).

## TL;DR

- **Universal partition key**: `by_date/day={date}/` — every service partitions by date. **Daily granularity is the
  universal axis** across all tiers (data, decision, ML, execution) so any backtest or backfill can pick `start_date` +
  `end_date`.
- **Bucket naming**: `{domain}-{asset_group_lower}-{project_id}` for asset-group–scoped data; `{domain}-{project_id}`
  for shared buckets.
- **Core venue asset groups**: CEFI, TRADFI, DEFI, SPORTS, PREDICTION — each gets its own bucket where data is
  partitioned by that axis. Legacy term: "category". **Canonical hive vocab (post-2026-04 rename)**: `asset_group=` for
  new writes; `category=` is legacy-preserved on disk (do NOT rekey existing data per workspace CLAUDE.md
  `§ Asset-group vocabulary`). Readers try canonical `asset_group=` first then fall back to legacy `category=`.
- **Sports per-fixture row-level shape** (writegate Phase 2.B, post-2026-05-06; Q1 resolution): per-fixture `data_types`
  (ODDS\*\_, FIXTURE\_\_, INJURIES) shard at `(asset_group=sports, source, data_type, league_id, day)` — `fixture_id` is
  a row-level column NOT a shard axis. Cluster validation (`cluster_extractor=bookmaker`) enforces per-fixture coverage
  within the parquet. Avoids ~10× manifest-row inflation.
- **Predictions canonical_question_group** (predictions Plan A, post-2026-05-06; Q1 resolution): Polymarket / Kalshi
  shards at
  `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)` —
  `market_id` is a row-level column NOT a shard axis. Cluster validation (`cluster_extractor=market_id`) enforces
  per-canonical-question coverage. Per-market lifecycle bounds enforced via row-level `market_created_at` /
  `settlement_time` columns.
- **Additional dimensions** vary by service: timeframe, data_type, instrument_type, feature_group, fixture_id,
  canonical_question_group, etc.
- **Hive-style partitioning**: `key=value/` directory structure for partition pushdown in queries.
- **`available_at` column required per row** (post-2026-05-06): every shard's parquet has an `available_at` column
  populated per row at write time (per workspace CLAUDE.md
  `§ available_at is per-row, write-time, equal to live-pipeline-arrival`). UTL `record_captured` calls
  `assert_available_at_present` internally.
- Path templates are defined in `dependencies.yaml` and are the single source of truth.
- Instrument files are named by instrument ID; feature files are named by feature group.

---

## GCS Path Conventions

### Universal Structure

Every GCS path follows this pattern:

```
gs://{bucket}/{prefix}/by_date/day={date}/{additional_dimensions}/{filename}.parquet
```

### Path Templates by Service

> **SSOT pointer**: per-service path templates + per-asset-group divergences live in
> [`per-asset-group-bucket-layouts.md`](./per-asset-group-bucket-layouts.md). That doc is the canonical SSOT for bucket
> templates (cefi / tradfi / defi / sports / prediction / instruments / features / ml / strategy / execution), shard
> atom shapes per asset_group, hive-vocab compatibility (`category=` legacy vs `asset_group=` canonical), and reader
> fallback discipline. Consult it before adding or modifying any path-template assumption in code.

---

## Bucket Naming Convention

### Asset-group–scoped buckets

For data that is inherently tied to a **venue asset group** (CeFi / TradFi / DeFi / Sports / Prediction):

```
{domain}-{asset_group_lower}-{project_id}

Examples:
  instruments-store-cefi-test-project
  instruments-store-tradfi-test-project
  instruments-store-defi-test-project
  market-data-tick-cefi-test-project
  features-delta-one-tradfi-test-project
```

### Shared buckets (not sharded by venue asset group)

For data that applies across categories:

```
{domain}-{project_id}

Examples:
  features-calendar-test-project       # Calendar features are domain-independent
  features-onchain-test-project         # On-chain metrics apply across CeFi/DeFi
  ml-models-store-test-project          # Models are not category-scoped
  ml-predictions-store-test-project
  strategy-store-test-project
  execution-store-test-project
```

### Why Some Buckets Are Shared

| Domain            | Shared? | Reason                                                          |
| ----------------- | ------- | --------------------------------------------------------------- |
| features-calendar | Yes     | Calendar/temporal features are identical regardless of category |
| features-onchain  | Yes     | On-chain metrics (TVL, sentiment) apply to both CeFi and DeFi   |
| ml-models-store   | Yes     | Models can train on cross-category features                     |
| ml-predictions    | Yes     | Predictions reference specific instruments, not categories      |
| strategy-store    | Yes     | Strategies may span categories                                  |
| execution-store   | Yes     | Execution results reference specific strategy runs              |

---

## Venue asset group dimension

These labels partition the trading **venue axis** (older terminology: “market category”):

| Asset group | Path / bucket token | Description                                                      |
| ----------- | ------------------- | ---------------------------------------------------------------- |
| CEFI        | `cefi`              | Centralized crypto exchanges + on-chain CLOBs                    |
| TRADFI      | `tradfi`            | Traditional finance (equities, futures, FX)                      |
| DEFI        | `defi`              | Decentralized protocols (AMM, lending, LST)                      |
| SPORTS      | `sports`            | Betting exchanges and bookmakers (Betfair, Pinnacle, Polymarket) |

Mapping is defined in `dependencies.yaml` (keys may still say `category` in legacy YAML — values are venue asset
groups):

```yaml
category_domain_mapping:
  CEFI: cefi
  TRADFI: tradfi
  DEFI: defi
  SPORTS: sports
```

---

## Venue Dimension

Venues are defined in `venues.yaml` and are the canonical list:

### CEFI Venues

`BINANCE-SPOT`, `BINANCE-FUTURES`, `DERIBIT`, `BYBIT`, `OKX`, `UPBIT`, `COINBASE`, `HYPERLIQUID`, `ASTER`

### TRADFI Venues

`CME`, `CBOE`, `NASDAQ`, `NYSE`, `ICE`, `FX`

### DEFI Venues

`UNISWAP_V2-ETHEREUM`, `UNISWAP_V3-ETHEREUM`, `UNISWAP_V4-ETHEREUM`, `CURVE-ETHEREUM`, `AAVE_V3-ETHEREUM`,
`MORPHO-ETHEREUM`, `LIDO-ETHEREUM`, `ETHERFI`, `ETHENA-ETHEREUM`

---

## Date Dimension

- **Granularity**: daily (`day=YYYY-MM-DD`)
- **Format**: ISO 8601 date string
- **Timezone**: all dates are UTC
- **Non-trading days**: no data files created for weekends/holidays (TradFi); CeFi/DeFi have data every day

---

## Service-Specific Extra Dimensions

### data_type

Used by market-tick-data-service and market-data-processing-service:

| Asset group | Data Types                                                                                                                                                                                                                                                                                             |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| CEFI        | `trades`, `book_snapshot_5`, `derivative_ticker`, `liquidations`, `options_chain` (bundled, cluster-validation MANDATORY), `futures_chain` (bundled, cluster-validation MANDATORY)                                                                                                                     |
| TRADFI      | `trades`, `ohlcv_1m`, `ohlcv_15m`, `ohlcv_24h`, `tbbo`, `options_chain` (ES.OPT 11-cluster, MANDATORY), `futures_chain` (ES + MES seeds, MANDATORY)                                                                                                                                                    |
| DEFI        | `dex_swaps`, `lending_indices`, `oracle_prices`, `utilization`, `dex_pools`, `risk_params`, `flash_loan_availability`, `rewards`                                                                                                                                                                       |
| SPORTS      | Per-fixture: `ODDS_SNAPSHOT`, `ODDS_MOVEMENT`, `ARBITRAGE` (bundled, cluster_extractor=bookmaker, MANDATORY), `FIXTURE_STATS`, `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`, `PLAYER_STATS`, `INJURIES` (when fixture-scoped). Day-aggregate: `STANDINGS`, `LEAGUES`, `TEAMS`, `REFEREES`, `COACHES`, `ROUNDS`. |
| PREDICTION  | `prediction_canonical_question_group` (post-Plan A; bundled by canonical_question_group; cluster_extractor=market_id; MANDATORY). Pre-Plan A: per-base_asset legacy data_types `BTC` / `ETH` / `SPX` / `FOOTBALL` / `OTHER`.                                                                           |

**Bundled data_types require cluster validation** at `ManifestWriter.record_captured` per writegate plan Phase 1A
(`expected_root_clusters` + `cluster_extractor` kwargs MANDATORY; UTL guard raises `MissingClusterValidationError` if
absent; QG STEP 5.64 statically checks). See
[`06-coding-standards/validation-and-errors.md`](/codex/06-coding-standards/validation-and-errors.md)
`§2 Write-gate quartet at record_captured`.

### instrument_type

Determined by venue (from `venues.yaml`):

| Venue                  | Instrument Types                                                                                                                  |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| BINANCE-SPOT           | SPOT_PAIR                                                                                                                         |
| BINANCE-FUTURES        | PERPETUAL, FUTURE                                                                                                                 |
| DERIBIT                | PERPETUAL, FUTURE, OPTION (with v6 disambiguation: `quote_asset` + `margin_type` for inverse vs linear)                           |
| CME                    | FUTURE, OPTION (with v6 `combo_type` + `leg_weights` for spreads / butterflies / iron condors)                                    |
| NASDAQ, NYSE           | EQUITY, ETF (IBIT, ETHA on NASDAQ post-2026-05-05 MVP scope)                                                                      |
| UNISWAP_V3-ETHEREUM    | POOL                                                                                                                              |
| AAVE_V3-ETHEREUM       | POOL                                                                                                                              |
| LIDO-ETHEREUM, ETHERFI | LST                                                                                                                               |
| HYPERLIQUID, ASTER     | PERPETUAL only (UnsupportedCapabilityError raised on OPTION / FUTURE)                                                             |
| POLYMARKET, KALSHI     | PREDICTION_MARKET (with per-market lifecycle: `market_created_at` / `resolution_time` / `settlement_time` per predictions Plan A) |

### timeframe

Used by market-data-processing-service and features-service (delta-one family):

```
15s, 1m, 5m, 15m, 1h, 4h, 24h
```

### feature_group

Used by features-service (delta-one family) (~20 groups):

```
technical_indicators, moving_averages, oscillators, volatility_realized,
momentum, volume_analysis, vwap, candlestick_patterns, market_structure,
returns, round_numbers, streaks, microstructure, funding_oi, liquidations,
futures_basis, volume_flow, temporal, economic_events, targets,
swing_outcome_targets
```

---

## Path Construction Example

To construct the full GCS path for a specific data file:

```python
# Features delta-one for BTC on Binance Futures, momentum group, 5m timeframe, Jan 15 2024
bucket = f"features-delta-one-cefi-{project_id}"
path = (
    f"by_date/day=2024-01-15/"
    f"feature_group=momentum/"
    f"timeframe=5m/"
    f"BINANCE-FUTURES_PERPETUAL_BTC-USDT@LIN.parquet"
)
full_path = f"gs://{bucket}/{path}"

# Result:
# gs://features-delta-one-cefi-test-project/
#   by_date/day=2024-01-15/feature_group=momentum/timeframe=5m/
#   BINANCE-FUTURES_PERPETUAL_BTC-USDT@LIN.parquet
```

In practice, domain clients handle path construction automatically. Services never need to build paths manually.

---

## BigQuery External Tables: Why Hive Partitioning Matters

### The Cost Optimization

All GCS paths use `key=value` folder naming (Hive-style partitioning) to enable **BigQuery external tables**. External
tables query GCS Parquet files in-place without loading them into BigQuery storage, eliminating data duplication and
storage costs.

```sql
-- Create external table pointing to GCS
CREATE EXTERNAL TABLE `project.features_delta_one.features_5m`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://features-delta-one-cefi-{project_id}/by_date/day=*/feature_group=*/timeframe=5m/*.parquet'],
  hive_partition_uri_prefix = 'gs://features-delta-one-cefi-{project_id}/by_date',
  require_hive_partition_filter = true
);

-- Query partitions directly (BigQuery scans only matching folders)
SELECT * FROM `project.features_delta_one.features_5m`
WHERE day = '2024-01-15'
  AND feature_group = 'momentum';
```

**Cost comparison**:

| Approach           | Storage Cost                     | Query Cost       | Total (1 year, 100 TB) |
| ------------------ | -------------------------------- | ---------------- | ---------------------- |
| Load into BigQuery | $20/TB active + $10/TB long-term | $6.25/TB scanned | $3,000 + $625/query    |
| External tables    | $20/TB (GCS only)                | $6.25/TB scanned | $2,000 + $625/query    |

Savings: $1,000/year by avoiding BigQuery storage duplication. External tables are the primary cost optimization for
analytics.

### Primary vs Optional Query Path

**Primary (production ML training):**

- GCS Parallel Reader -- reads Parquet directly via `pandas.read_parquet()`
- Speed: 20-30 seconds for typical queries
- Cost: $0 (GCS storage only, no query cost)
- Use case: batch ML training, feature generation

**Optional (development/analysis):**

- BigQuery external tables -- SQL queries over GCS data
- Speed: 2 seconds for typical queries (10-20x faster)
- Cost: $6.25/TB scanned
- Use case: ad-hoc exploration, debugging, quality checks, dashboard queries

### Schema Compatibility Requirements

For BigQuery external tables to work, GCS paths MUST use `key=value` format:

| Valid (Hive)              | Invalid           | BigQuery Result                     |
| ------------------------- | ----------------- | ----------------------------------- |
| `day=2024-01-15/`         | `day-2024-01-15/` | Partition not recognized, full scan |
| `feature_group=momentum/` | `group-momentum/` | Partition not recognized            |
| `timeframe=5m/`           | `5m/`             | Partition not recognized            |

All 12 services already use the `key=value` format [IMPLEMENTED]. Legacy data with `prefix-value` format is
automatically ignored by external tables (no data corruption risk).

### When External Tables Auto-Refresh

External tables do NOT cache data. Every query reads directly from GCS. This means:

- **Automatic freshness**: as soon as a service writes a new Parquet file to GCS, it is immediately queryable via the
  external table (no refresh command needed)
- **No ETL lag**: traditional BigQuery tables require ETL pipelines with delays; external tables are real-time with
  respect to GCS writes
- **Partition discovery**: BigQuery scans the URI pattern on every query; new partitions are discovered automatically

This is why Hive partitioning is critical for live operations -- monitoring dashboards can query the latest data without
any refresh or ETL step.

---

## Live vs Batch Data Routing

### Convention

Same bucket, different top-level prefix:

```
gs://{bucket}/
  live/                                         ← streaming micro-batches
    venue={venue}/instrument={instrument}/
      window=2026-03-18T01:00Z.parquet          ← 1-5 minute windows
      window=2026-03-18T01:05Z.parquet
      ...
  by_date/                                      ← daily accumulated batch
    day=2026-03-18/
      data_type={data_type}/
        venue={venue}/
          {instrument}.parquet
```

- **Batch** (default): daily Hive-partitioned files under `by_date/`. Written once per day by batch jobs.
- **Live**: micro-batch window files under `live/`. Written every 1-5 minutes by streaming subscribers.

Both use Hive `key=value/` partitioning. Both are queryable by BigQuery external tables.

### Micro-Batch Strategy (Live Mode)

Services in live mode (`SERVICE_MODE=live`) buffer data in-memory and flush to GCS on a window interval:

1. PubSub subscriber receives events
2. Accumulates in a buffer (1-5 minutes, configurable per service)
3. Writes a single Parquet file per window per instrument to `live/venue=X/instrument=Y/window={ISO_timestamp}.parquet`
4. At end-of-day, a compaction job composes window files into the daily `by_date/` partition via GCS object compose

**Why micro-batch, not per-event:**

- GCS charges per write operation ($0.005 per 1,000 ops)
- Tiny objects (<1 KB) waste storage overhead and slow list operations
- 1-minute windows at 100 instruments = 144,000 files/day — manageable
- Per-event at 1000 events/sec = 86M files/day — unmanageable

### End-of-Day Compaction

```python
# GCS compose merges up to 32 source objects into one destination
# For >32 windows, chain compose calls (compose first 32, then compose result with next batch)
storage_client.compose(
    bucket="market-data-tick-defi-prd-{project_id}",
    sources=["live/venue=HYPERLIQUID/instrument=BTC-USD/window=2026-03-18T00:00Z.parquet", ...],
    destination="by_date/day=2026-03-18/data_type=trades/venue=HYPERLIQUID/BTC-USD.parquet",
)
# After successful compose, delete the live window files
```

### UCI Integration

`get_data_source()` accepts `mode="live"` or `mode="batch"` (default):

```python
from unified_cloud_interface import get_data_source

# Batch (default) — reads from by_date/ prefix
source = get_data_source(routing_key="defi", prefix="by_date")

# Live — reads from live/ prefix (auto-prepended)
source = get_data_source(routing_key="defi", prefix="venue=HYPERLIQUID", mode="live")
```

`StorageDataSource` prepends `live/` to the prefix when `mode="live"`.

### AWS S3 Compatibility

The `live/` and `by_date/` prefixes work identically on S3. S3 uses the same `key=value/` convention for Hive-compatible
partitioning (Athena, Glue, Redshift Spectrum all support it).
