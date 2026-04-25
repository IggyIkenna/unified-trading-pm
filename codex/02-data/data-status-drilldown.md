---
scope: [engineer, ops]
---

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
    "capture_status":   "captured" | "empty_confirmed" | "attempted_failed" | "missing",
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

`unified_trading_library.ManifestWriter.validate_df(df, *, category, instrument_type, data_type, venue=None, row_key=None, strict=False)`
resolves the contract via UAC `lookup_contract` and calls `validate_row_df(df, contract, venue=venue)`:

- **Pass** → silent return.
- **`SchemaContractNotFoundError`** → `MANIFEST_WRITE_SCHEMA_MISSING` warn-level event; do not block.
- **`RowSchemaValidationError`** → `MANIFEST_WRITE_SCHEMA_MISMATCH` error event with full detail (expected / missing /
  extra / dtype_mismatches / null_violations / venue), records `attempted_failed` manifest row, re-raises.

The method is currently opt-in (callers must invoke it). Phase 2 follow-up flips it to mandatory in the `write()` path
after a 7-day dry-run window with zero `MANIFEST_WRITE_SCHEMA_MISMATCH` events.

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
