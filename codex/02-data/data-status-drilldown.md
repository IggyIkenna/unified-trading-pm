---
doc_type: codex-ssot
title: Data-status drilldown — single SSOT for `/api/data-status/*`
summary:
  Single SSOT for the /api/data-status/* surface — the per-shard ShardDetailModal endpoint (shard_class
  grouped/per_symbol/reference/fixtures, schema + signed-URL payload, write-time strict schema validation) and the
  hierarchical drilldown endpoint, plus Deploy-Missing preview/auto-launch modes with IAM/rate-limit/audit gating.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-ui,
    features-service,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [data-status, ui, manifest, mtds, instruments, defi]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/data-status-drilldown-hierarchy.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: 2026-04-25
authoritative_for: [data-status drilldown API contract (/api/data-status/* endpoints)]
referenced_by:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/data-status-drilldown-hierarchy.md,
    /codex/04-architecture/e2e-pipeline-manifest-wiring.md,
    /codex/04-architecture/features-service-architecture.md,
    /codex/05-infrastructure/deployment-ui-architecture.md,
    /codex/06-coding-standards/cli-convention.md,
    /codex/06-coding-standards/data-status-endpoint-contract.md,
    /codex/06-coding-standards/feature-service-pattern.md,
  ]
owner:
last_reviewed: 2026-10-28
code_refs:
---

# Data-status drilldown — single SSOT for `/api/data-status/*`

**Status:** live as of 2026-04-25 (`ShardDetailModal`); hierarchical drill-down GA 2026-05-07
(`HierarchicalShardDrilldown`).

**Source commits:** `deployment-api` `9d93236`, `deployment-ui` `f4a8e4e`, `unified-api-contracts` `cf79d54`,
`unified-trading-library` `f40481d7`.

This doc is the SSOT for both:

- the **per-shard drilldown surface** (`ShardDetailModal` powered by `GET /api/data-status/shard-detail`), and
- the **hierarchical drilldown surface** (`HierarchicalShardDrilldown` powered by
  `GET /api/data-status/drilldown/{service}/{asset_group}`).

The two endpoints share the codex shard-axis matrix. The hierarchical endpoint enumerates roll-up nodes; the per-shard
endpoint returns the leaf payload (schema, sample rows, signed URLs).

---

## §1 — Overview / API surface

### Per-shard endpoint (`ShardDetailModal`)

```
GET /api/data-status/shard-detail
  ?service=<str>           # market-tick-data-service | instruments-service | features-* | …
  &category=<str>          # CEFI | TRADFI | DEFI | SPORTS | PREDICTION | INSTRUMENTS
                           #   ^ LEGACY query-param name (preserved for backwards-compat on per-shard endpoint until
                           #     deprecation cutoff ~2026-06-15); canonical workspace vocabulary is `asset_group=`
                           #     (lowercase keys) per CLAUDE.md § "Asset-group vocabulary". Hierarchical endpoint
                           #     below already uses the canonical `{asset_group}` path segment.
  &instrument_type=<str>   # lowercase UAC value: option | perpetual | spot_pair | pool | lending | spot_asset | …
  &data_type=<str>         # options_chain | trades | dex_pools | liquidation_events | oracle_prices | …
  &day=<YYYY-MM-DD>
  &venue=<str|null>        # DERIBIT | BINANCE-SPOT | AAVE_V3-ETHEREUM (composite for DeFi) | …
  &underlying=<str|null>   # BTC | ETH | … (for grouped bundles)
  &instrument_id=<str|null> # for per-symbol shards
```

> **Vocab reconciliation (codex audit D-16 2026-05-12)**: the per-shard endpoint accepts the legacy `category=` query
> param (uppercase asset-group enum names) while the hierarchical endpoint uses the canonical `{asset_group}` path
> segment (lowercase dict-key form). Both endpoints accept the same set of asset-groups; the spelling difference is
> preserved through the deprecation window. After 2026-06-15 the per-shard endpoint accepts `asset_group=` as primary
>
> - `category=` as a deprecated alias that logs a `DEPRECATED_QUERY_PARAM` event.

Sister endpoint `GET /api/data-status/venue-detail?service=<>&category=<>&venue=<>` powers the inline "Instrument
breakdown" panel (DeFi-aware: chain-only returns protocols list, composite returns pools list).

### Hierarchical endpoint (`HierarchicalShardDrilldown`)

```
GET /api/data-status/drilldown/{service}/{asset_group}
  ?start_date=<YYYY-MM-DD>             # required
  &end_date=<YYYY-MM-DD>               # required
  &chain=<str|null>
  &venue=<str|null>
  &data_type=<str|null>
  &instrument_type=<str|null>
  &instrument_id=<str|null>
  &league_id=<str|null>
  &feature_group=<str|null>
  &timeframe=<str|null>
  &canonical_question_group=<str|null>
  &expand_to_depth=<int>               # default 2
```

Pairs the SSOT covers: enumerate via `GET /api/data-status/drilldown-pairs`.

Both endpoints branch on the codex per-asset_group shard-axis matrix declared in
[`unified_api_contracts.registry.data_status_axis_matrix.SHARD_AXIS_MATRIX`](../../../unified-api-contracts/unified_api_contracts/registry/data_status_axis_matrix.py).

---

## §2 — Per-asset_group depth table

Matches the workspace SSOT in CLAUDE.md "Per-asset-group shard-key matrix".

| Service / asset_group               | Drill-down (top → leaf)                                                                                                                                       |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruments-service`               | `venue → date` (cefi/tradfi); `venue → chain → date` (defi)                                                                                                   |
| MTDS CeFi spot/perp                 | `venue → data_type → instrument_type → instrument_id → date`                                                                                                  |
| MTDS CeFi options/futures           | `venue → data_type → instrument_type → root → date` (bundled)                                                                                                 |
| MTDS TradFi futures                 | `venue → data_type → instrument_type → root → date` (bundled)                                                                                                 |
| MTDS TradFi options                 | `venue → data_type → instrument_type → root → date` (11-cluster ES.OPT)                                                                                       |
| MTDS DeFi                           | `venue → chain → instrument_id → data_type → date`                                                                                                            |
| MTDS sports                         | `data_type → league_id → date`                                                                                                                                |
| MTDS prediction                     | `venue → canonical_question_group → data_type → date`                                                                                                         |
| `features-service` (consolidated)   | `feature_family → <per-family axes below>` (the 8 family rows below collapse to sub-package paths inside ONE service; `feature_family` is the outermost axis) |
| ↳ `feature_family=delta_one`        | `feature_family → venue [→ chain] → feature_group → timeframe → instrument_id → date`                                                                         |
| ↳ `feature_family=onchain`          | `feature_family → venue → chain → feature_group → protocol_id → timeframe → date` (DeFi only)                                                                 |
| ↳ `feature_family=sports`           | `feature_family → feature_group → league_id → date`                                                                                                           |
| ↳ `feature_family=calendar`         | `feature_family → feature_group → timeframe → date` (asset-group=shared)                                                                                      |
| ↳ `feature_family=cross_instrument` | `feature_family → venue [→ chain] → feature_group → timeframe → date`                                                                                         |
| ↳ `feature_family=volatility`       | `feature_family → venue → feature_group → timeframe → instrument_id → date`                                                                                   |
| ↳ `feature_family=commodity`        | `feature_family → venue → feature_group → root → timeframe → date` (futures-bundled)                                                                          |
| ↳ `feature_family=multi_timeframe`  | `feature_family → venue [→ chain] → feature_group → timeframe → instrument_id → date`                                                                         |

> **`feature_family` is the outermost axis for features-service drilldowns** (added 2026-05-08 per
> [`features_repo_consolidation_2026_05_08`](../../plans/archive/features_repo_consolidation_2026_05_08.plan.md) Phase
> 1A). The 8 previously-separate `features-*-service` repos are sub-packages of the consolidated
> [`features-service`](../../../features-service/); the data-status drilldown surfaces `feature_family` (the UAC
> `FeatureFamily` StrEnum: `onchain` / `volatility` / `cross_instrument` / `sports` / `calendar` / `commodity` /
> `delta_one` / `multi_timeframe`) as the top-level shard axis so operators see the consolidated repo's coverage
> per-family without mixing families. Architecture SSOT:
> [`/codex/04-architecture/features-service-architecture.md`](/codex/04-architecture/features-service-architecture.md).

> **`pipeline_mode` is the outermost partition column** above every tree shown above (added 2026-05-08 per
> [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../../plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md)).
> Every drilldown tree implicitly stratifies by `pipeline_mode={batch_*, live_websocket, ...}` first, then by the
> per-asset_group axes listed in the table above. Operators querying the data-status drilldown UI without an explicit
> `pipeline_mode` filter see the **batch-vs-live merged** view (live wins for dates where live exists, batch otherwise,
> per the SOURCE_PRIORITY fan-in semantics in [`pipeline-mode-partition.md`](./pipeline-mode-partition.md)). Querying
> with explicit `pipeline_mode={value}` returns only that stratum — required for the `live_pipeline` Phase 12
> batch-vs-live reconciliation gate. SSOT for the `PipelineMode` closed-set values:
> `unified_api_contracts.canonical.crosscutting.pipeline_mode.PipelineMode`.

---

## §3 — Shard class — service × instrument_type matrix

The `shard_class` field on the per-shard endpoint response tells the UI which payload tab title and renderer to use. It
branches on the actual parquet shape, not just the category:

| `shard_class` | Examples                                                                                                                                                                                                                            | What's in the parquet                            | Payload tab                                                            |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------- |
| `grouped`     | MTDS `options_chain`, `futures_chain`, `combo_chain`, `dex_pools`, `dex_swaps`, `liquidation_events`, `flash_loan_events`, `staking_yields`, `token_transfers`, `bridge_events`, `mev_events`, `governance_events`, `position_data` | One parquet, many distinct symbols/strikes/pools | "Instruments in this shard" — list of distinct `symbol_column` values  |
| `per_symbol`  | MTDS `PERPETUAL` trades, `SPOT_PAIR` book, `oracle_prices` per asset                                                                                                                                                                | One parquet per symbol; rows are time series     | "Instrument" — single instrument echo + sample_rows is the time series |
| `reference`   | instruments-service `OPTIONS`, `FUTURES`, `LENDING_POOLS` catalogs                                                                                                                                                                  | Reference data — full instrument definitions     | "Instrument definitions" — full table, capped at 500 rows with footer  |
| `fixtures`    | sports `FIXTURE_*` data types, prediction `EVENT_DEFINITIONS`                                                                                                                                                                       | Fixture/event-keyed data                         | "Fixtures" — `home_team / away_team / kickoff_ts / markets`            |

### DeFi composite venue convention

DeFi shards live at the `chain × protocol` axis. The endpoint accepts the composite form `<PROTOCOL>-<CHAIN>` matching
the instruments-service manifest naming:

- `AAVE_V3-ETHEREUM` (lending)
- `MORPHO-ETHEREUM` (lending)
- `UNISWAP_V3-ETHEREUM`, `UNISWAP_V3-ARBITRUM`, … (pools)
- `CHAINLINK-ETHEREUM` (oracle)

When `venue` matches `<PROTOCOL>-<CHAIN>` the endpoint resolves through `VENUE_CONTRACT_OVERRIDES` first (per-pool
variants), then falls back to `CONTRACT_REGISTRY` for the base contract.

### Schema column variation across venues

UAC `ColumnSpec` carries two structural fields the modal renders explicitly:

- **`required: bool`** — `False` columns are absent entirely on some venues (not just nullable).
- **`provided_by_venues: frozenset[str] | None`** — `None` means all venues; a set marks the column as venue-specific
  (e.g. `{DERIBIT}` for `mark_iv` / `greeks_*`, the UNISWAP_V3 family for `tick` / `sqrt_price_x96` / `liquidity`).

The Schema tab splits the column list into **Core columns** (always present) and **Venue-specific columns** (badge
listing the venues that publish them). This lets a desk read "does this venue ship `mark_iv`, or do I have to compute
it?" directly from the modal.

---

## §4 — `ShardDetailModal` endpoint contract

### Response envelope

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

### Write-time validation

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

### UI flow per category

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

### Download semantics

- **Parquet signed URL** — direct GCS download, 1-hour TTL, only present when the shard exists.
- **CSV (projected)** — `GET /api/data-status/download-shard-csv?...` returns CSV containing exactly the columns
  declared in the contract. Venue-specific columns absent on this venue are dropped from the projection. Always
  available when schema is registered.

### Schema coverage gate

`unified_api_contracts/tests/test_all_datatypes_have_schema.py` enforces the invariant: **every** `DataType` enum value
resolves to at least one `SchemaContract` in `CONTRACT_REGISTRY`. As of UAC `cf79d54`, 30 / 30 enum values have coverage
(was 21 / 30 before the backfill).

If a future engineer adds a new `DataType` without a matching contract, this test fails — preventing "No contract
registered" from ever reaching the modal again.

---

## §5 — Hierarchical drill endpoint

### Backend

Endpoint: `GET /api/data-status/drilldown/{service}/{asset_group}`.

- Query params: `start_date` / `end_date` (required); per-axis filters `chain` / `venue` / `data_type` /
  `instrument_type` / `instrument_id` / `league_id` / `feature_group` / `timeframe` / `canonical_question_group`;
  `expand_to_depth` (default 2).
- Response: `{ service, asset_group, axes, tree, totals, filtered_by, manifest_uri }`. Each tree node has `axis`,
  `value`, `captured`, `empty_confirmed`, `attempted_failed`, `total`, `completion_pct`, `row_key` (the structured shard
  atom for the leaf, consumed by the per-leaf SmartDownloadButton + the Deploy-Missing surgical CLI), `children`,
  `is_leaf`.
- Implementation:
  [`deployment_api/services/data_status_hierarchical.py`](../../../deployment-api/deployment_api/services/data_status_hierarchical.py).
- Pairs the SSOT covers: enumerate via `GET /api/data-status/drilldown-pairs`.

Aggregate counts at every non-leaf node reflect the FULL subtree below it (so the operator sees the rolled-up
`captured / total` ratio at any depth without expanding). Lazy-load: deeper levels only materialise on expand.

### Frontend

Component: [`HierarchicalShardDrilldown.tsx`](../../../deployment-ui/src/components/HierarchicalShardDrilldown.tsx).

- Top-level fetch on mount with `expand_to_depth=1`.
- Each non-leaf row lazy-loads its children on first expand by re-calling the endpoint with the parent's `row_key` as
  filter query params.
- Each row renders `axis=value | captured/total | completion_pct | empty badge | failed badge`. Leaf rows are
  un-clickable.
- `AbortController` on every fetch cleanly cancels in-flight requests on unmount or filter-change.

Phase 2 ships the component drop-in-ready;
[`DataStatusTab.tsx`](../../../deployment-ui/src/components/DataStatusTab.tsx) wire-in (insertion below the existing
`BreakdownsAccordion`) is the follow-up.

### Per-leaf download + surgical recovery

Every leaf carries a `row_key` dict. Two operator actions consume it:

1. **Per-leaf SmartDownloadButton** — passes the full `row_key` to `/data-status/download-shard-csv` so bundled shards
   (options_chain ES.OPT) download the per-root bundle parquet and per-instrument shards (CeFi spot BTCUSDT 2024-03-04)
   download the per-instrument parquet. Capture-status branching (200 + CSV / empty_confirmed header / attempted_failed
   header / 404 / 502) is per the existing `_capture_status_response` contract.
2. **Deploy-Missing button** — emits a structured `--shard-key=...` pipe-delimited form
   (`asset_group|venue|data_type|instrument_type|instrument_id_or_root|day`) that the MTDS CLI decomposes into
   individual filter flags. The resulting backfill VM scopes to ONE leaf shard rather than re-running the whole
   asset_group. SSOT for the format:
   [`market_tick_data_service/cli/shard_key.py`](../../../market-tick-data-service/market_tick_data_service/cli/shard_key.py).

   **Two launch modes** (operator-selectable per Phase 0 IAM/audit/rate-limit ratification 2026-05-08; tracked in
   [`plans/active/deploy_missing_auto_launch_2026_05_07.md`](../../plans/archive/deploy_missing_auto_launch_2026_05_07.md)):
   - **Preview mode (shipped)** — `POST /api/data-status/deploy-missing-preview` returns the bash invocation
     (`bash <launcher-script> --shard-key=<quoted>`) for the operator to copy + run from their authenticated terminal.
     No service-account IAM grant required on the deployment-api side; the operator's user creds are the auth boundary.
     Mode is opt-in via `DeployMissingButton` "Copy command" action.
   - **Auto-launch mode (Phase 2/3 — in-flight; gated on IAM custom-role + Firestore rate-limit + audit-log infra
     landing)** — `POST /api/data-status/deploy-missing-launch` invokes `gcloud compute instances create` from the
     deployment-api Cloud Run pod via the `roles/customDeployMissingLauncher` service-account binding. The endpoint:
     - Enforces per-shard idempotency via GCE `compute.instances.list` with label filter
       `shard_key_hash=<sha1(shard_key)>` — duplicate calls return the running VM rather than launching a new one.
     - Emits `DEPLOY_MISSING_VM_LAUNCHED` event keyed on `shard_key` as `correlation_id`; blocks the HTTP response until
       the per-VM `STARTED` event lands within 90s (no-fire-and-forget rule).
     - Routes through the Firestore-backed rate limiter enforcing Phase 0 Decision 3 ceilings: 30 launches/operator/hr,
       200/operator/day, 100/project/hr, **1 active per `shard_key` for 6h**. Returns HTTP 429 + `Retry-After` when
       tripped; alerts to `#uts-prod-alerts`.
     - Writes a synchronous audit-log row to BigQuery primary + Cloud Logging mirror per Phase 0 Decision 2 (90d hot /
       5y cold; sync-blocking write). The launch fails-closed if the audit write fails.

   **IAM scope** (Phase 0 Decision 1 approved 2026-05-08, Option B): the auto-launch path uses a custom project-level
   role `roles/customDeployMissingLauncher` with minimum permissions:
   `compute.instances.{create,get,list,delete, setMetadata,setLabels}`, `compute.disks.{create,get}`,
   `compute.subnetworks.{use,useExternalIp}`, `compute.networks.get`, `compute.machineTypes.get`, `compute.zones.get`,
   `compute.images.useReadOnly`, `iam.serviceAccounts.actAs`, and `cloudbuild.builds.{create,get,list}` for
   tarball-staleness paired refresh. IAM-condition-scoped to the specific zone + image family. Blanket
   `roles/compute.instanceAdmin.v1` is REJECTED (insufficient scoping).

   **Tarball-staleness paired refresh** — before the launch endpoint creates the GCE VM, it calls
   `TarballStalenessChecker.ensure_fresh()` (`deployment-api@faac20a` — `deployment_api/services/tarball_staleness.py`)
   which compares the GCS tarball mtime against `git rev-parse HEAD` of `live-defi-rollout`; if stale, triggers the
   Cloud Build refresh + polls `cloudbuild.builds.get` until complete before launching. This guarantees the recovery VM
   picks up the latest code, not a stale tarball.

### Failure modes that the drill-down catches

- Misleading roll-up headlines — the pre-2026-05-07 chain rollup reported `ARBITRUM 32/54 shards` (date-count math
  collapsed across 3 protocols × 5 data_types × ~1700 days ≈ 25k true shards). The new hierarchical drill-down
  materialises the true leaf shard count at every level.
- Partial bundles — the codex shard atom for options_chain bundles all 11 ES.OPT clusters under one parquet; if the
  writer captured 1 of 11 the leaf shows `empty_confirmed=10 attempted_failed=0 captured=1` rather than the
  pre-2026-05-07 `captured=1` that masked the gap.
- Per-protocol launch dates — `_mtds_expected_dates_cached` clips pre-`max(chain_genesis, protocol_launch)` days so
  AAVE_V3-ARBITRUM drilldown 2021-08-31 → 2022-03-15 returns empty subtrees rather than inflating the denominator with
  always-empty days.

---

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

---

## §6 — Cross-references

- Plan: `plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.md`.
- Sibling SSOTs:
  - [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md) — manifest schema,
    rollup-vs-drilldown denominator divergence.
  - [`per-asset-group-bucket-layouts.md`](./per-asset-group-bucket-layouts.md) — canonical parquet paths.
  - [`honest-absence-downstream-handling.md`](./honest-absence-downstream-handling.md) — NaN-handling tolerances.
  - [`pipeline-mode-partition.md`](./pipeline-mode-partition.md) — `pipeline_mode` outermost partition column.
- Reference incident 2026-05-07: operator DEFI screenshot showing ARBITRUM 32/54 misleading headline; root cause the
  date-count rollup math + missing protocol launch SSOT.
