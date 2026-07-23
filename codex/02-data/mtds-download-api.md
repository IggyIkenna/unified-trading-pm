---
doc_type: codex-ssot
title: MTDS Download API — CanonicalParquetReader
summary: >-
  CanonicalParquetReader — the canonical GCS reader for MTDS parquet shards; validates against the availability manifest
  (raises ShardNotFoundError before any GCS read), supports full-bundle vs per-instrument pyarrow predicate-pushdown
  reads (162M-row Deribit options_chain: per-instrument peak RSS 1.3GB vs >7GB bundle) plus column projection and
  list_instruments.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [mtds, manifest, parquet, data-pipeline, features]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /codex/02-data/mtds-data-source-coverage-matrix.md,
  ]
created: 2026-04-24
authoritative_for: [CanonicalParquetReader MTDS shard read API]
referenced_by:
owner:
last_reviewed: 2026-05-17
code_refs: [market-tick-data-service/market_tick_data_service/reader.py]
---

# MTDS Download API — CanonicalParquetReader

**Status:** live — `market-tick-data-service` commit `2095d1b` on `live-defi-rollout`.

## What it is

`CanonicalParquetReader` is the canonical way to read MTDS parquet shards from GCS. It handles:

1. **Bundle reads** — load the entire shard (e.g., all 162M rows of an options_chain)
2. **Per-instrument reads** — load only the rows for a specific symbol via pyarrow predicate pushdown, keeping RSS
   bounded even on > 1 GB files

Before this API, consumers called `pd.read_parquet(gcs_path)` directly, which loaded entire bulk parquets into memory
and had no manifest validation.

## When to use which mode

| Mode                                  | When                                                           | Memory                                                   |
| ------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------- |
| `instrument_id=None` (full bundle)    | Backfills, analytics over all strikes, bulk feature generation | O(full parquet)                                          |
| `instrument_id="BTC-25MAR26-50000-C"` | Per-symbol feature calc, smoke tests, per-contract inspection  | O(matching rows) — pyarrow skips non-matching row groups |
| `list_instruments(...)`               | Enumerate available symbols before deciding which to load      | O(symbol column only)                                    |

## API

```python
from market_tick_data_service import CanonicalParquetReader, ShardNotFoundError

reader = CanonicalParquetReader()  # uses default catalogue bucket

# Full bundle
df = reader.read_shard(
    venue="DERIBIT",
    target_date=date(2026, 4, 17),
    data_type="options_chain",
    instrument_type="option",
)

# Per-instrument (predicate pushdown — O(matching rows))
df = reader.read_shard(
    venue="DERIBIT",
    target_date=date(2026, 4, 17),
    data_type="options_chain",
    instrument_type="option",
    instrument_id="BTC-25MAR26-50000-C",
)

# Column projection + filter (combine for minimal I/O)
df = reader.read_shard(
    venue="DERIBIT",
    target_date=date(2026, 4, 17),
    data_type="options_chain",
    instrument_type="option",
    instrument_id="BTC-25MAR26-50000-C",
    columns=["timestamp", "bid", "ask", "mark_price"],
)

# List available symbols without loading data
symbols = reader.list_instruments(
    venue="DERIBIT",
    target_date=date(2026, 4, 17),
    data_type="options_chain",
    instrument_type="option",
    underlying="BTC",  # optional filter
)
# → ["BTC-25MAR26-50000-C", "BTC-25MAR26-50000-P", ...]

# Missing shard raises ShardNotFoundError
try:
    df = reader.read_shard(venue="DERIBIT", target_date=..., ...)
except ShardNotFoundError as e:
    logger.warning("Shard not in manifest: %s %s %s", e.venue, e.target_date, e.data_type)
```

## Manifest dependency

`CanonicalParquetReader` validates against the availability manifest before hitting GCS. If no manifest row matches
`(venue, date, data_type, instrument_type)`, it raises `ShardNotFoundError` immediately — without making any GCS read.

This is intentional: a missing manifest row means the upstream pipeline didn't capture that shard (instruments-service
or MTDS fetch failed). The correct response is to surface the gap, not to try a blind GCS read that would return a 404.

## Memory characteristics

For per-instrument reads, pyarrow's predicate pushdown reads row group statistics from the parquet footer, then skips
any row group whose min/max values for the `symbol` column cannot match the filter. On a sorted (or roughly sorted)
parquet with good row group statistics, this is effectively O(1) row groups scanned.

**Smoke VM result (2026-04-23):** DERIBIT `options_chain` for `btc` (162M rows, 7+ GB parquet): per-instrument read peak
RSS = 1,329 MB; full bundle peak RSS would be > 7 GB.

## Shard granularity stays at bundle level

The manifest tracks shards at bundle granularity (`venue × underlying × date × data_type=options_chain`), not at
per-strike level. This is correct: if an options_chain fetch fails, the whole strike surface for that underlying is
unavailable — you can't partially backfill individual strikes.

`CanonicalParquetReader` is the layer that enables per-symbol access on top of bundle-level shards. The manifest
granularity stays coarse; the download is what's fine-grained.

## Works for all shard types

| Shard type                    | Example                                        | instrument_id behavior       |
| ----------------------------- | ---------------------------------------------- | ---------------------------- |
| Per-symbol (perpetuals, spot) | `DERIBIT/BTC-PERPETUAL/2026-04-17.parquet`     | Must match the single symbol |
| Bulk (options_chain)          | `DERIBIT/BTC/options_chain/2026-04-17.parquet` | Filters within the bulk file |
| Bulk (futures_chain)          | `DERIBIT/BTC/futures_chain/2026-04-17.parquet` | Same                         |
| Bulk (combo_chain)            | `DERIBIT/BTC/combo_chain/2026-04-17.parquet`   | Same                         |

## Consumer wiring

Existing consumers that call `pd.read_parquet(path)` directly should migrate to `CanonicalParquetReader.read_shard()`.
This gives them:

- Manifest validation (early `ShardNotFoundError` instead of silent empty DataFrame)
- Automatic predicate pushdown when `instrument_id` is set
- Column projection via `columns=` parameter
- Consistent GCS path resolution from manifest metadata

Search for direct calls to migrate: `rg "pd\.read_parquet" market-tick-data-service/market_tick_data_service --type py`

## Import path

```python
from market_tick_data_service import CanonicalParquetReader, ShardNotFoundError
# or
from market_tick_data_service.reader import CanonicalParquetReader, ShardNotFoundError
```
