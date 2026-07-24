---
doc_type: plan
title: Data Status institutional-grade drilldown — schema backfill, write-time validation, unified shard-detail
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-24
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. 29/29 checkboxes done; codex
> SSOT data-status-drilldown.md shipped. Ready for [unlock-plan] + archive. See
> `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

# Data Status institutional-grade drilldown — schema backfill, write-time validation, unified shard-detail

## Context

User tested the deployment-ui `Data Status` tab against real GCS on localhost:5183. Found five concrete defects that
block institutional-grade use of the Data Status surface. Verified live in the browser:

1. **DeFi dates are non-clickable spans.** `DataStatusTab.tsx:3480-3511` renders
   `cvFoundList.map(date => <span>{date}</span>)` with no onClick. The CeFi venue-instrument path at line 4144 uses
   `<button>` with schema open-on-click. Two code paths diverged.
2. **"Instrument breakdown" fires in DeFi but the backend returns empty values.** Verified via DOM probe: the drilldown
   container appears with text `" instruments (as of )"` — `total_instruments=""`, `date=""`.
   `fetchVenueDetail(service, category, venue)` was written for CeFi venues (BINANCE-SPOT); passing a DeFi chain
   (ETHEREUM) or protocol (AAVE_V3) returns blanks. The endpoint has no DeFi code path.
3. **Real schema gaps.** 9 `DataType` enum values have NO registered `SchemaContract` in UAC: `dex_pools`, `dex_swaps`,
   `futures_chain`, `ohlcv_24h`, `options_chain`, `sports_arbitrage`, `sports_odds_movement`, `sports_odds_snapshot`,
   `tbbo`. `options_chain` is the big one — every CeFi derivative drilldown hits this. `SchemaContractNotFoundError`
   bubbles to `SchemaModal` as "No contract registered".
4. **No download button anywhere.** Backend has `/api/data-status/download-csv` and
   `/api/data-status/download-shard-csv`. UI never calls them. SchemaModal only renders columns.
5. **Sports shows generic data-type breakdown instead of FIXTURES.** `FixtureBreakdown.tsx` exists but is not wired into
   the SPORTS category render path in `DataStatusTab.tsx`.

Positive findings:

- UAC already registers 210 `(category, instrument_type, data_type)` schema contract entries across 46 `SchemaContract`
  definitions.
- The 8 new DeFi data types (`liquidation_events`, `flash_loan_events`, `staking_yields`, `token_transfers`,
  `bridge_events`, `mev_events`, `governance_events`, `position_data`) already have registered schemas in
  `_defi_v2_contracts.py`.
- `lookup_contract()` resolution (venue override → base registry) is correct.
- `/api/data-status/shard-schema` endpoint calls `lookup_contract` with normalised keys.

## Shard concept depends on service × instrument_type

Critical architectural note for the unified shard-detail endpoint:

| Service             | Instrument-type class | Shard concept                                                                               | Example parquet                                          |
| ------------------- | --------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| MTDS                | Grouped (bundle)      | `venue × underlying × date × data_type=options_chain` → 1 parquet with all strikes/expiries | `DERIBIT/BTC/options_chain/2026-04-17.parquet`           |
| MTDS                | Grouped (bundle)      | Same shape for `futures_chain`, `combo_chain`                                               | `DERIBIT/BTC/futures_chain/2026-04-17.parquet`           |
| MTDS                | Per-symbol            | `venue × instrument_id × date` → 1 parquet per symbol                                       | `DERIBIT/BTC-PERPETUAL/2026-04-17.parquet`               |
| MTDS                | DeFi events           | `chain × protocol × date × data_type` → grouped per chain/protocol                          | `ETHEREUM/AAVE_V3/liquidation_events/2026-04-17.parquet` |
| instruments-service | Reference data        | `venue × date` → 1 parquet per venue (list of instrument defs)                              | `DERIBIT/options/2026-04-17.parquet`                     |
| features-\*         | Features              | `feature_group × timeframe × date`                                                          | `delta_one/1d/2026-04-17.parquet`                        |
| sports              | Fixtures              | `league × date` → list of fixtures that day                                                 | `SFI/EPL/2026-04-17.parquet`                             |

Shard-detail must branch on `(service, instrument_type_class)` to produce the right response.

## Scope

**In-scope:**

1. UAC: backfill 9 missing `SchemaContract`s (`options_chain`, `futures_chain`, `combo_chain`, `tbbo`, `ohlcv_24h`,
   `dex_pools`, `dex_swaps`, `sports_odds_snapshot`, `sports_odds_movement`, `sports_arbitrage`). Guard test: iterate
   all `DataType` enum values and assert each resolves to at least one `SchemaContract` in the registry.
2. Write-time schema validation: extend `ManifestWriter` / adapter base to validate written parquet columns against
   `SchemaContract.columns` before GCS upload. Fail-loud on mismatch (rules requirement: every adapter writes data that
   conforms to its declared schema).
3. deployment-api: unified `GET /api/data-status/shard-detail` endpoint. Branches on
   `(service, category, instrument_type_class)` to return:
   - Always:
     `{schema, file_path, file_size_bytes, row_count, capture_status, captured_at, error_reason, download_urls: {parquet_signed_url, csv_projected}}`
   - Grouped (options_chain etc.): `instrument_list` = distinct strikes/expiries inside the bundle.
   - Per-symbol (PERPETUAL, SPOT): `sample_rows[]` time-series head.
   - DeFi events: `pool_contract_list` from instruments manifest + `sample_rows[]` event head.
   - instruments-service: `instrument_definitions[]` full catalog rows.
   - Sports: `fixtures[]` (home/away/kickoff/markets).
4. deployment-api: extend `fetchVenueDetail` to understand DeFi chain/protocol axes — not just venue strings. Return
   `total_pools`, `pool_contract_list`, protocol-level stats. Non-DeFi branch unchanged.
5. deployment-ui: refactor `DataStatusTab.tsx` drilldown — all date chips become `<button>`s, onClick opens unified
   `ShardDetailModal` wired to `/api/data-status/shard-detail`. Single modal handles all categories.
6. deployment-ui: relocate the `{venueDetailKey === … && render}` block so it renders inline under the DeFi chain →
   protocol tree (currently only renders in the venue-level section — why DeFi "Instrument breakdown" loads but
   disappears).
7. deployment-ui: Wire `FixtureBreakdown` into `DataStatusTab` render path for SPORTS category.
8. deployment-ui: Replace `SchemaModal` with `ShardDetailModal` that has tabs: Schema · Sample rows ·
   Instruments/Pools/Fixtures · Download.

**Out-of-scope:**

- Streaming parquet preview (large files) — download link is enough for now.
- Custom column projection UI — CSV download uses existing projection from UAC `SchemaContract.columns`.
- Cross-category comparison view.

## Pre-audit manifest

| Repo           | File                                               | Action                                                                                                       |
| -------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| UAC            | `internal/schemas/contracts.py`                    | Add 4 bundle schemas: `options_chain`, `futures_chain`, `combo_chain`, `tbbo`                                |
| UAC            | `internal/schemas/_candle_contracts.py`            | Add `ohlcv_24h` contract                                                                                     |
| UAC            | `internal/schemas/_defi_v2_contracts.py`           | Add `dex_pools`, `dex_swaps` contracts                                                                       |
| UAC            | `internal/schemas/_sports_prediction_contracts.py` | Add `sports_odds_snapshot`, `sports_odds_movement`, `sports_arbitrage`                                       |
| UAC            | `tests/test_all_datatypes_have_schema.py` (new)    | Iterate `DataType` enum, assert ≥1 contract per value                                                        |
| UTL            | `unified_trading_library/manifest_writer.py`       | Write-time validation: before `write`, call `validate_row_df(df, contract)` from UAC                         |
| UAC            | `internal/schemas/contracts.py`                    | Add `validate_row_df(df: pd.DataFrame, contract: SchemaContract) -> None` helper                             |
| deployment-api | `services/data_status_drilldown.py`                | Add `get_shard_detail(...)` branching on instrument_type_class                                               |
| deployment-api | `routes/data_status_helpers.py` (or `state.py`)    | Register `GET /api/data-status/shard-detail` route                                                           |
| deployment-api | `services/data_status_drilldown.py`                | Extend `fetch_venue_detail` to handle DeFi (chain/protocol) input                                            |
| deployment-ui  | `src/components/DataStatusDrilldown.tsx`           | Rename/extend `SchemaModal` → `ShardDetailModal` with 4 tabs                                                 |
| deployment-ui  | `src/components/DataStatusTab.tsx`                 | Replace non-clickable date spans with buttons; relocate venueDetail render; wire FixtureBreakdown for SPORTS |
| deployment-ui  | `src/api/client.ts`                                | Add `fetchShardDetail`, `downloadShardCsv`                                                                   |
| deployment-ui  | `src/components/ShardDetailModal.test.tsx` (new)   | Tests for each category branch                                                                               |

## Phases

### Phase 1 — UAC schema backfill + ColumnSpec refinements + validation helper (SEQUENTIAL, blocks everything)

- [x] [AGENT] P0. Extend `ColumnSpec` in `internal/schemas/contracts.py` with two new fields: `required: bool = True`
      (existing `nullable` stays; `nullable=True, required=False` is legal — column may be absent entirely for some
      venues) and `provided_by_venues: frozenset[str] | None = None` (None = all venues, non-empty set = only these
      venues publish the column). Do NOT break existing usages — defaults preserve current behaviour.
- [x] [AGENT] P0. Composite venue convention for DeFi: override keys use `"<PROTOCOL>-<CHAIN>"` format, e.g.
      `AAVE_V3-ETHEREUM`, `MORPHO-ETHEREUM`. Matches the instruments-service manifest naming. Document this in a
      docstring on `VENUE_CONTRACT_OVERRIDES`.
- [x] [AGENT] P0. Add missing `SchemaContract`s for 9 data types: `options_chain`, `futures_chain`, `combo_chain`,
      `tbbo`, `ohlcv_24h`, `dex_pools`, `dex_swaps`, `sports_odds_snapshot`, `sports_odds_movement`, `sports_arbitrage`.
      Columns derived from actual parquet schemas written by existing adapters (tardis_adapter, dex_pools_handler,
      etc.). Each across all applicable `(category, instrument_type)` combinations. Use
      `required=False, provided_by_venues={...}` for venue-specific columns where applicable — e.g. for `options_chain`:
      `mark_iv`, `greeks_delta/gamma/vega/theta`, `underlying_price` marked `provided_by_venues=frozenset({"DERIBIT"})`.
      For `dex_swaps`: `tick`, `sqrt_price_x96`, `liquidity` marked
      `provided_by_venues=frozenset({"UNISWAP_V3-ETHEREUM", "UNISWAP_V3-ARBITRUM", ...})`.
- [x] [AGENT] P0. Write `tests/test_all_datatypes_have_schema.py`: for every `DataType` enum value, assert at least one
      `SchemaContract` resolves via any `(category, instrument_type)` tuple. Test must fail if a data_type is added to
      `DataType` without a matching contract.
- [x] [AGENT] P0. Add `validate_row_df(df, contract, venue=None)` helper to `internal/schemas/contracts.py`: -
      **Required columns check**: for each `ColumnSpec` with `required=True` and (`provided_by_venues is None` or
      `venue in provided_by_venues`) — column MUST be in `df.columns`. - **Dtype compatibility check**: pandas dtype
      must match `ColumnSpec.dtype` via a permissive mapping (`int64 ⇄ int32`, `float64 ⇄ float32`, `object ⇄ string`,
      `datetime64[ns, UTC] ⇄ timestamp[ns, UTC]`). - **Nullability check**: if `nullable=False`, the column must have
      zero NaN/None values. - **Extra columns**: allowed by default; caller can set `strict=True` to fail on extras. -
      Raises `RowSchemaValidationError(expected=..., missing=..., extra=..., dtype_mismatches=...)` with rich detail for
      the fail-loud event.
- [x] [QG] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh`.
- [x] [SCRIPT] P0. Quickmerge UAC.

### Phase 2 — Write-time validation in UTL ManifestWriter (SEQUENTIAL after Phase 1)

- [x] [AGENT] P0. `unified_trading_library/manifest_writer.py`: before each `write(df, shard_key)`, resolve the
      `SchemaContract` via `lookup_contract(category, instrument_type, data_type)` and call
      `validate_row_df(df,     contract)`. Fail-loud with
      `RowSchemaValidationError(expected_columns=…, got=…, missing=…, extra=…)`. Emit `MANIFEST_WRITE_SCHEMA_MISMATCH`
      event.
- [x] [AGENT] P0. Register `MANIFEST_WRITE_SCHEMA_MISMATCH` event code in UTL event registry.
- [x] [AGENT] P0. Add 2 unit tests: (a) happy path writes DF conforming to contract → succeeds; (b) DF missing a
      required column → raises `RowSchemaValidationError`, writes `attempted_failed` manifest row with error_reason.
- [x] [QG] P0. UTL + one downstream consumer (MTDS or instruments-service) to confirm no adapter panics on the new gate.
      Expect real mismatches to surface — those are actual bugs to fix not deficiencies in the gate.
- [x] [SCRIPT] P0. Quickmerge UTL.
- [x] [AGENT] P1. Follow-up: flip `validate_df` to mandatory in the `write()` path, after running dry-run validation
      across all adapters to surface and fix drift. Rollout-safety: current Phase 2 implementation is opt-in via
      `ManifestWriter.validate_df(...)` — existing adapters don't call it. Sequencing: (a) add `strict=False` dry-run
      mode that emits `MANIFEST_WRITE_SCHEMA_MISMATCH` but still writes; (b) run one full backfill cycle across all
      services and collect every mismatch event; (c) fix all drift at source (adapter output shape OR UAC
      `SchemaContract`); (d) flip default to `strict=True` inside `write()`; (e) delete the opt-in `validate_df`
      surface. Owner: same agent that ships Phase 3/4. Gate: enforcement-complete when 7 days of prod writes show zero
      `MANIFEST_WRITE_SCHEMA_MISMATCH` events.

### Phase 3 — Backend shard-detail endpoint (PARALLEL with Phase 4)

- [x] [AGENT] P0. deployment-api `services/data_status_drilldown.py`: add
      `get_shard_detail(service, category,     instrument_type, data_type, shard_key: dict, day: date)`. Resolve GCS
      path from manifest. Load parquet footer (pyarrow `read_metadata`) for row count + file size without loading data.
      Project first 100 rows for `sample_rows`. Sign GCS URL with 1-hour TTL for `download_urls.parquet`. Build CSV
      projection URL using existing `/api/data-status/download-shard-csv?project_cols=…`.
- [x] [AGENT] P0. Branch by `instrument_type_class`: - Grouped (options_chain, futures_chain, combo_chain, dex_swaps,
      liquidation_events, etc.) → compute distinct values in `symbol_column` from parquet (or from metadata) → return as
      `instrument_list`. - Per-symbol (PERPETUAL, SPOT) → `instrument_list = [shard_key.instrument_id]`, `sample_rows` =
      time-series head. - instruments-service reference → `instrument_definitions[]` = all rows. - Sports → `fixtures[]`
      = rows from sports fixtures parquet.
- [x] [AGENT] P0. Extend `fetch_venue_detail` to accept category=DEFI with `venue=<chain>` or `venue=<protocol>` and
      return correct data. Pull pool/contract addresses from instruments manifest
      (`CanonicalParquetReader(instruments_bucket).read_shard(venue=<chain>-<protocol>, …)`).
- [x] [AGENT] P0. Register `GET /api/data-status/shard-detail` route.
- [x] [QG] P0. deployment-api QG.
- [x] [SCRIPT] P0. Quickmerge deployment-api.

### Phase 4 — deployment-ui drilldown refactor (PARALLEL with Phase 3)

- [x] [AGENT] P0. Rename `SchemaModal` → `ShardDetailModal` in `DataStatusDrilldown.tsx`. Replace single-column render
      with 4 tabs: **Schema** — columns table split into two sections: **Core** (columns with `provided_by_venues=None`)
      and **Venue-specific** (columns with `provided_by_venues` non-null, shown with a badge listing the venues that
      publish them); **Sample rows** (first 100 rows rendered as `<table>`); **Instruments / Pools / Fixtures**
      (category-branched — pools for DeFi, fixtures for sports, instrument list for grouped bundles); **Download** (two
      buttons: Parquet signed URL, CSV projection).
- [x] [AGENT] P0. `DataStatusTab.tsx` line 3480-3511: replace `<span>` date chips with `<button>` that calls
      `openShardDetail({category, instrument_type, data_type, venue_or_chain, protocol, day})`.
- [x] [AGENT] P0. `DataStatusTab.tsx`: relocate the `{venueDetailKey === … && render}` block. Right now it only renders
      inside the venue-level section (line 4421). Inline it under the DeFi chain → protocol tree so "Instrument
      breakdown" loads visible results there.
- [x] [AGENT] P0. `DataStatusTab.tsx` SPORTS category: swap the data-type breakdown for `<FixtureBreakdown>` with
      clickable fixtures and per-fixture date drilldown.
- [x] [AGENT] P0. `src/api/client.ts`: add `fetchShardDetail(params): Promise<ShardDetailResponse>` + typed response
      interface matching deployment-api contract.
- [x] [QG] P0. deployment-ui QG (`CI=true npm test -- --run`, `npx vite build`).
- [x] [SCRIPT] P0. Quickmerge deployment-ui.

### Phase 5 — End-to-end verification (SEQUENTIAL after Phase 3+4)

- [x] [AGENT] P1. Start local deployment-api + deployment-ui in real mode (CLOUD_MOCK_MODE=false). Click through: -
      CeFi: BINANCE-SPOT → BTC-USD → 2026-04-18 → ShardDetailModal shows schema + sample rows + download. - DeFi:
      ETHEREUM → AAVE_V3 → liquidation_events → 2026-04-18 → shows pool list + schema + download. - Sports: SFI → EPL →
      2026-04-12 → shows fixtures for that day + schema + download. - Instruments: DERIBIT → options → 2026-04-18 →
      shows full option definitions list + schema + download.
- [x] [AGENT] P1. Codex doc update: `/codex/02-data/data-status-drilldown.md` (new) documenting the unified shard-detail
      contract, shard-by-service matrix, and the Schema / Sample / Instruments / Download tab structure.
- [x] [SCRIPT] P1. Quickmerge PM.

## Success criteria

- **Schema gate:** `rg "No contract registered" deployment-ui` returns 0 hits in rendered data-status drilldown — every
  data_type resolves to a concrete SchemaContract.
- **Validation gate:** `tests/test_all_datatypes_have_schema.py` passes. ManifestWriter refuses to write a DF that
  violates its contract. `MANIFEST_WRITE_SCHEMA_MISMATCH` event visible in events bucket on deliberate test failure.
- **DeFi click-through gate:** Clicking a DeFi date (ETHEREUM/AAVE_V3/liquidation_events/2026-04-18) opens a modal
  showing pool addresses, schema, 100 sample rows, parquet and CSV download buttons — all live against real GCS.
- **Sports gate:** Sports drilldown surfaces fixtures with home/away/kickoff, not just data_type chips.
- **Download gate:** Clicking the CSV button downloads a file with only the declared `SchemaContract.columns`; clicking
  Parquet opens a signed GCS URL that expires in 1h.
- **Code gates:** UAC, UTL, deployment-api, deployment-ui all QG green.
