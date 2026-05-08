---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06 -->

> **POST-PLAN REALITY (2026-05-06)** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md)
> BEFORE making code or doc changes informed by this doc. This doc is partially stale: may describe shard atoms,
> manifest behaviour, available_at semantics, or partitioning that's evolving with the writegate-honest-coverage plan
> (per-fixture sports sharding, canonical_question_group for predictions, cluster validation mandatory, three-category
> empty-output decision, available_at per-row write-time). The post-plan-reality doc lists the 10 cross-cutting
> principles codified in workspace `CLAUDE.md` (live=batch, no double SSOT, three-category empty-output decision A/B/C,
> cluster validation mandatory at record_captured, per-row write-time `available_at`, prediction lifecycle timing,
> temporary state must have named successor, per-VM shard isolation, etc.) plus the active plans where the canonical
> post-plan reality is being implemented. If this doc and the active plans disagree, the plans win. If you find a
> contradiction the plans don't address, flag to user — don't decide unilaterally.

# Data-status drilldown — `/api/data-status/shard-detail`

**Status:** live as of 2026-04-25 — `deployment-api` commit `9d93236`, `deployment-ui` commit `f4a8e4e`,
`unified-api-contracts` commit `cf79d54`, `unified-trading-library` commit `f40481d7`.

## What it is

A unified shard-level drilldown surface accessible from any clickable date in the deployment-ui Data Status tab. For
every (`service`, `category`, `instrument_type`, `data_type`, `day`, `venue`) tuple a user clicks on, the endpoint
returns the canonical UAC schema, GCS metadata, sample rows, the relevant secondary axis (instruments / pools /
fixtures), and signed download URLs.

This replaces the older narrow `SchemaModal` flow (schema columns only) with a 4-tab `ShardDetailModal`: **Schema ·
Sample rows · Instruments-Pools-Fixtures · Download**.

## Endpoint

```
GET /api/data-status/shard-detail
  ?service=<str>           # market-tick-data-service | instruments-service | features-* | …
  &category=<str>          # CEFI | TRADFI | DEFI | SPORTS | PREDICTION | INSTRUMENTS
  &instrument_type=<str>   # lowercase UAC value: option | perpetual | spot_pair | pool | lending | spot_asset | …
  &data_type=<str>         # options_chain | trades | dex_pools | liquidation_events | oracle_prices | …
  &day=<YYYY-MM-DD>
  &venue=<str|null>        # DERIBIT | BINANCE-SPOT | AAVE_V3-ETHEREUM (composite for DeFi) | …
  &underlying=<str|null>   # BTC | ETH | … (for grouped bundles)
  &instrument_id=<str|null> # for per-symbol shards
```

A sister endpoint `GET /api/data-status/venue-detail?service=<>&category=<>&venue=<>` powers the inline "Instrument
breakdown" panel (DeFi-aware: chain-only returns protocols list, composite returns pools list).

## Response envelope

```python
{
  "coord":         { ... echo of request ... },
  "shard_class":   "grouped" | "per_symbol" | "reference" | "fixtures",
  "schema": {
    "registered":         bool,
    "source":             "CONTRACT_REGISTRY" | "VENUE_CONTRACT_OVERRIDES" | "none",
    "symbol_column":      str | None,
    "columns": [
      {
        "name":               str,
        "dtype":              str,
        "nullable":           bool,
        "required":           bool,                     # NEW (UAC cf79d54)
        "provided_by_venues": list[str] | None,         # NEW — None = all venues
        "description":        str,
      },
    ],
  },
  "gcs": {
    "path":             "gs://…/2026-04-18.parquet" | None,
    "file_size_bytes":  int | None,
    "row_count":        int | None,
    "captured_at":      iso8601 | None,
    "capture_status":   "captured" | "empty_confirmed" | "attempted_failed" | "expected_unattempted",
    "error_reason":     str | None,
  },
  "download_urls": {
    "parquet_signed_url": str | None,   # 1h TTL, only when shard exists
    "csv_projected":      str | None,   # always available when schema is registered
  },
  "sample_rows": [ {col: val, …}, … ],   # first 100 rows; empty for missing/empty shards
  "payload_grouped":    { "instrument_list": [ {key, type, …}, … ] }   | None,
  "payload_per_symbol": { "instrument_list": [coord.instrument_id], "..." } | None,
  "payload_reference":  { "instrument_definitions": [ {full row}, … ] } | None,
  "payload_fixtures":   { "fixtures": [ {home_team, away_team, kickoff_ts, markets}, … ] } | None,
}
```

Exactly one `payload_*` key is populated per response, aligned with `shard_class`.

## Shard class — service × instrument_type matrix

The `shard_class` field tells the UI which payload tab title and renderer to use. It branches on the actual parquet
shape, not just the category:

| `shard_class` | Examples                                                                                                                                                                                                                            | What's in the parquet                            | Payload tab                                                            |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------- |
| `grouped`     | MTDS `options_chain`, `futures_chain`, `combo_chain`, `dex_pools`, `dex_swaps`, `liquidation_events`, `flash_loan_events`, `staking_yields`, `token_transfers`, `bridge_events`, `mev_events`, `governance_events`, `position_data` | One parquet, many distinct symbols/strikes/pools | "Instruments in this shard" — list of distinct `symbol_column` values  |
| `per_symbol`  | MTDS `PERPETUAL` trades, `SPOT_PAIR` book, `oracle_prices` per asset                                                                                                                                                                | One parquet per symbol; rows are time series     | "Instrument" — single instrument echo + sample_rows is the time series |
| `reference`   | instruments-service `OPTIONS`, `FUTURES`, `LENDING_POOLS` catalogs                                                                                                                                                                  | Reference data — full instrument definitions     | "Instrument definitions" — full table, capped at 500 rows with footer  |
| `fixtures`    | sports `FIXTURE_*` data types, prediction `EVENT_DEFINITIONS`                                                                                                                                                                       | Fixture/event-keyed data                         | "Fixtures" — `home_team / away_team / kickoff_ts / markets`            |

## DeFi composite venue convention

DeFi shards live at the `chain × protocol` axis. The endpoint accepts the composite form `<PROTOCOL>-<CHAIN>` matching
the instruments-service manifest naming:

- `AAVE_V3-ETHEREUM` (lending)
- `MORPHO-ETHEREUM` (lending)
- `UNISWAP_V3-ETHEREUM`, `UNISWAP_V3-ARBITRUM`, … (pools)
- `CHAINLINK-ETHEREUM` (oracle)

When `venue` matches `<PROTOCOL>-<CHAIN>` the endpoint resolves through `VENUE_CONTRACT_OVERRIDES` first (per-pool
variants), then falls back to `CONTRACT_REGISTRY` for the base contract.

## Schema column variation across venues

UAC `ColumnSpec` carries two structural fields the modal renders explicitly:

- **`required: bool`** — `False` columns are absent entirely on some venues (not just nullable).
- **`provided_by_venues: frozenset[str] | None`** — `None` means all venues; a set marks the column as venue-specific
  (e.g. `{DERIBIT}` for `mark_iv` / `greeks_*`, the UNISWAP_V3 family for `tick` / `sqrt_price_x96` / `liquidity`).

The Schema tab splits the column list into **Core columns** (always present) and **Venue-specific columns** (badge
listing the venues that publish them). This lets a desk read "does this venue ship `mark_iv`, or do I have to compute
it?" directly from the modal.

## Write-time validation

`unified_trading_library.ManifestWriter.record_captured(...)` automatically resolves the contract via UAC
`lookup_contract` and calls `validate_row_df(df, contract, venue=venue)` **before** staging the manifest row. Adapters
do NOT need to call validation explicitly — it runs every time. Behaviour:

- **Pass** → manifest row staged with `capture_status=captured`.
- **`SchemaContractNotFoundError`** (no contract registered for the shard's tuple) → `MANIFEST_WRITE_SCHEMA_MISSING`
  warn-level event; the write proceeds (this is a temporary state during contract rollout — every `DataType` enum value
  has a contract as of UAC `cf79d54`, so this branch should be rare).
- **`RowSchemaValidationError`** (contract registered + DF violates) →
  - **Strict mode (production default)**: `MANIFEST_WRITE_SCHEMA_MISMATCH` error event with full detail (expected /
    missing / extra / dtype_mismatches / null_violations / venue), `attempted_failed` manifest row written carrying
    `error_reason`, parquet does **not** upload, exception re-raised so the adapter's shard-level failure-isolation loop
    catches it. The bad data never reaches GCS.
  - **Warn-only mode (opt-out)**: same event emitted but no exception; manifest row stays `captured` and parquet
    uploads. Used when an operator needs to push a backfill through known drift while the adapter is being fixed.

**Default is strict** as of `unified-config-interface` 2026-04-25 —
`UnifiedCloudConfig.manifest_strict_schema_validation` defaults to `True`. To opt out at the boundary, set
`MANIFEST_STRICT_SCHEMA_VALIDATION=false` for that VM / Cloud Run service / local dev. Test fixtures that need warn-only
behaviour pass `strict_validation=False` to the `ManifestWriter` constructor explicitly.

**Where failures surface for ops:**

1. **Events bucket** — `gs://central-element-323112-events/events/<service>/<date>/<vm>/events.jsonl` carries one
   `MANIFEST_WRITE_SCHEMA_MISMATCH` event per failed write. Each event's `metadata.details` block contains the full diff
   (`expected`, `missing_required`, `extra_columns`, `dtype_mismatches`, `null_violations`, `venue`) so the root cause
   is in the event itself — no log archeology required.
2. **Availability manifest** — `_index/availability_index.parquet` row for the shard has
   `capture_status=attempted_failed` and `error_reason=<RowSchemaValidationError message>` so the data-status UI
   surfaces the failure on the same chip the user clicks.
3. **Deployment-ui Data Status modal** — `ShardDetailModal` → `gcs.error_reason` is rendered as a red panel above the
   tabs.

## UI flow per category

```
DEFI     →  CHAIN  →  PROTOCOL (composite venue) →  Date button  →  ShardDetailModal
                                                 →  "Instrument breakdown" link  →  inline VenueDetailPanel
                                                                                    (chain → protocols list,
                                                                                     composite → pools list)

CEFI     →  VENUE  →  INSTRUMENT_TYPE  →  DATA_TYPE  →  Date button  →  ShardDetailModal
TRADFI   →  same as CEFI

SPORTS   →  LEAGUE  →  Fixture date button (FixtureBreakdown for FIXTURE_*)
                   →  Other-data-type date button  →  ShardDetailModal (shard_class=fixtures)

INSTRUMENTS → VENUE  →  Date button  →  ShardDetailModal (shard_class=reference)
```

All date chips — both **available** (green) and **missing** (red) — are clickable. Clicking a missing date still opens
the modal: the schema and CSV-projection URL are populated (the contract is known); only the parquet signed URL and
sample rows are empty. This is intentional — operators need to see the expected schema while planning a backfill.

## Download semantics

- **Parquet signed URL** — direct GCS download, 1-hour TTL, only present when the shard exists.
- **CSV (projected)** — `GET /api/data-status/download-shard-csv?...` returns CSV containing exactly the columns
  declared in the contract. Venue-specific columns absent on this venue are dropped from the projection. Always
  available when schema is registered.

## Schema coverage gate

`unified_api_contracts/tests/test_all_datatypes_have_schema.py` enforces the invariant: **every** `DataType` enum value
resolves to at least one `SchemaContract` in `CONTRACT_REGISTRY`. As of UAC `cf79d54`, 30 / 30 enum values have coverage
(was 21 / 30 before the backfill).

If a future engineer adds a new `DataType` without a matching contract, this test fails — preventing "No contract
registered" from ever reaching the modal again.

## Known follow-ups

1. **DeFi date click context inference** — DataStatusTab passes `instrument_type=<first_data_type>` /
   `data_type=<first_data_type>` for DeFi protocol date clicks because the click site does not have the axis split in
   scope. Fix: pre-compute a `data_type → instrument_type` mapping per protocol from the manifest response, OR add a
   backend `instrument_type=AUTO` mode that resolves from the data_type's registered contracts. Tracked in plan
   `data_status_institutional_drilldown_2026_04_24` Phase 5 follow-ups.

2. **ManifestWriter validation flip to mandatory** — currently opt-in via `validate_df(...)`. After 7 days of zero
   `MANIFEST_WRITE_SCHEMA_MISMATCH` events in prod, flip to default-on inside `write()` and remove the opt-in surface.
   Same plan, Phase 2 follow-up.

3. **TypedDicts for `ShardDetailResponse`** — currently in `deployment-api/deployment_api/types/`. Migrate to
   `unified_api_contracts.internal.architecture_v2.deployment_api` once a deployment-api domain facade exists in UAC.
