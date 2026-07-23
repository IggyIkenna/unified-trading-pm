---
doc_type: plan
title: Data Canonicalisation MVP — CeFi + TradFi + DeFi (schema, partitioning, migration)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    deployment-api,
    deployment-ui,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-17
locked_by: live-defi-rollout
locked_since: 2026-04-17
priority: P0
code_readiness: C0
deployment_readiness: D0
business_readiness: B0
---

# Data Canonicalisation MVP

## Context

MTDS writes market data to GCS across three categories (CeFi / DeFi / TradFi). During a sanity audit this session we
discovered:

| Category | Bug                                                                                                                                                                                                                                                                                                                                         |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CeFi     | Bybit `data_type=futures_chain` overloaded with instrument_type name (should be `data_type=trades` for dated futures). Mixed per-symbol and bundled `ticks.parquet` files from different sessions.                                                                                                                                          |
| TradFi   | Databento classifier falls back to `instrument_type=future` when `raw_symbol` missing — options (e.g. `E2AJ6 C6190`) end up mislabelled. Per-contract file naming (not per-underlying bundle as spec requires). Raw Databento symbols stored instead of canonical IDs. Continuous contracts fetched unnecessarily. Equity code path absent. |
| DeFi     | Non-canonical path: `day/venue=AAVE_V3-ETHEREUM/ticks.parquet` — chain embedded in venue, no `instrument_type` or `data_type` partitions, everything bundled.                                                                                                                                                                               |
| All      | No `instrument_id` column in rows. No per-day availability filter (can't know which strikes/contracts were tradeable on a given day). No schema/logic validation preventing future regressions.                                                                                                                                             |

Canonical format spec exists in UAC (`VENUE:INSTRUMENT_TYPE:SYMBOL`, 19 InstrumentType enums, generator code for
options/futures chains) but is not enforced at write time.

## Principles

1. **Every row has `instrument_id` column** containing canonical ID. File names are hive hints only; the column is
   queryable truth.
2. **Partition hierarchy**: `day/category/venue/instrument_type/data_type/{file}.parquet`. For DeFi also `chain`.
3. **Per-day availability filter** drives what we expect for each day — used for manifest zero-fill and data status
   denominators.
4. **Bundled per-underlying** for options_chain and futures_chain (all strikes × expiries of one underlying in one file
   per data_type per day).
5. **Fail loud, never silently default** — unknown instrument_types must raise, not fall back to `future`.
6. **Code first, test, then migrate, then fill, then validate**. No GCS writes before the code is proven.
7. **Manifest integrity**: zero-count entries for expected-empty days, no entries for truly-not-ingested days — data
   status distinguishes "zero by design" from "missing".
8. **Final truth is the Data Status page in deployment-ui** showing correct counts per (day, venue, instrument_type,
   data_type).

## Dependency DAG

```
Phase 0 (QG baseline)
  ↓
Phase 1 (code fixes, all in parallel)
  ├─ 1.1 UAC per-day availability filter
  ├─ 1.2 UAC canonical ID builder coverage
  ├─ 1.3 UAC schema validation framework
  ├─ 1.4 UTL DataSink logic validation hooks
  ├─ 1.5 instruments-service catalogue with available_from/to
  ├─ 1.6 MTDS Tardis (CeFi) data_type + instrument_id fix
  ├─ 1.7 MTDS Databento (TradFi) classifier + canonical symbols + equity code path
  ├─ 1.8 MTDS DeFi adapter refactor
  └─ 1.10 Manifest writer zero-fill
       ↓
Phase 2 (test) — local QG + per-category 1-day smoke tests to sandbox bucket
  ↓
Phase 3 (migrate existing data, 3 VMs in parallel)
  ├─ 3.1 CeFi migration v2
  ├─ 3.2 TradFi migration
  └─ 3.3 DeFi migration
       ↓
Phase 4 (fill gaps — new ingestion, non-overlapping periods)
  ↓
Phase 5 (manifest reconciliation)
  ↓
Phase 6 (validation via data status page)
  ↓
Phase 7 (docs sweep)
```

## Phase 0 — QG baseline [BLOCKING]

- [x] [SCRIPT] P0. Run `bash scripts/quality-gates.sh` on: unified-api-contracts, unified-trading-library,
      instruments-service, market-tick-data-service, deployment-api. Record baseline pass/fail state before any changes.
- [x] [AGENT] P0. Any pre-existing QG failures that would block this work must be fixed or explicitly waived here.

**Baseline (2026-04-17)**:

- unified-api-contracts — PASS (98s)
- unified-trading-library — PASS (109s)
- instruments-service — FAIL (codex compliance 7 violations, max 4) — PRE-EXISTING, WAIVED for Phase 1, tracked for
  later.
- market-tick-data-service — FAIL (codex compliance 4 violations, max 2) — PRE-EXISTING, WAIVED for Phase 1.
- deployment-api — FAIL (coverage 69.28% vs 70%; 1982 tests pass, 1 skipped) — PRE-EXISTING, WAIVED for Phase 1.

Waived failures are unrelated to canonicalisation scope. Phase 1 agents must not regress these further and should aim to
reduce violation counts where they touch affected areas.

## Phase 1 — Code fixes (parallel) [C1→C4]

### 1.1 UAC per-day availability filter

- [x] [AGENT] P0. Implement
      `get_instruments_available_on(ref_date, catalogue, category=None, venue=None, instrument_type=None, chain=None) -> list[InstrumentRecord]`.
      Filters by `available_from_datetime <= ref_date <= available_to_datetime` (None = open-ended). →
      `unified_api_contracts/internal/reference/availability.py` (24 tests).
- [x] [AGENT] P0. Unit tests: options chain (listing/expiry windows), futures chain (quarterly availability), perpetuals
      (listing only), equities (IPO→delisting). → 24/24 pass.

### 1.2 UAC canonical ID builder coverage

- [x] [AGENT] P0. Audit every InstrumentType enum value; ensure `build_instrument_id(...)` handles each. →
      `unified_api_contracts/internal/reference/canonical_id_builder.py` + top-level facade (42 tests).
- [x] [AGENT] P0. Fail loud on unknown instrument_type; missing kwargs raise.
- [x] [AGENT] P0. Canonical form confirmed for all 24 InstrumentType enum values (SPOT_PAIR, PERPETUAL, FUTURE, OPTION,
      POOL, LENDING, LST, YIELD_BEARING, A_TOKEN, DEBT_TOKEN, STAKING, SPOT_ASSET, EQUITY, ETF, COMMODITY, CURRENCY,
      INDEX, BOND, CDS, COMBO, PREDICTION_MARKET, EXCHANGE_ODDS, FIXED_ODDS, PROP).

### 1.3 UAC schema validation framework

- [x] [AGENT] P0. Define `SchemaContract`, `ColumnSpec`, `Violation` + 10 built-in contracts + `CONTRACT_REGISTRY`. →
      `unified_api_contracts/internal/schemas/contracts.py` (10 tests).
- [x] [AGENT] P0. `validate_dataframe(df, contract) -> list[Violation]` — missing_column, wrong_dtype,
      extra_required_null, null_rate_exceeded, row_count_too_low.
- [x] [AGENT] P0. Unit tests per contract.

### 1.4 UTL DataSink logic validation hooks

- [x] [AGENT] P0. Pre-write hook in `StreamingParquetWriter`. →
      `unified_trading_library/io/instrument_id_validator.py` + hook in `streaming_writer.py` (18 tests).
- [x] [AGENT] P0. Opt-out flag for legacy writers (`strict=False`) — default `True`. Existing streaming_writer tests
      opted into `strict=False`.

### 1.5 instruments-service catalogue

- [x] [AGENT] P0. `CatalogueBuilder` with `build_cefi/build_tradfi/build_defi/build_all/write_to_gcs`. →
      `instruments_service/reference_data/catalogue/catalogue_builder.py` (5 tests).
- [x] [AGENT] P0. Populates from existing URDI reference data per venue + canonicalises via UAC `build_instrument_id`.
- [x] [AGENT] P0. orchestrator hook `refresh_catalogue(categories, api_keys)`.

### 1.6 MTDS Tardis (CeFi)

- [x] [AGENT] P0. Helper `finalise_rows_and_path` in `cefi/tardis_shared.py` (12 tests). Rejects illegal
      `data_type=futures_chain`/`options_chain`. Per-underlying bundling for chain types.
- [x] [AGENT] P0. Helper attaches `instrument_id` column per row via UAC builder.
- [x] [AGENT] P0. Current CeFi adapters don't write parquet directly — write path currently in
      `tradfi/tardis_adapter.py` (Phase 1.7 / Phase 3.1 callers will adopt helper).

### 1.7 MTDS Databento (TradFi)

- [x] [AGENT] P0. Kill silent `instrument_type = "future"` fallback in cme_converter, opra_converter, databento_adapter.
      All three now raise `ValueError` on unparseable input.
- [x] [AGENT] P0. New `databento_classifier.py` — 16 tests covering continuous/dated/options/equity/unparseable.
- [x] [AGENT] P0. `databento_adapter._enrich_with_canonical_ids` attaches `instrument_id` column, drops continuous, sets
      partition-friendly instrument_type tokens (7 tests).
- [x] [AGENT] P1. `databento_equity.py` scaffold (list_symbols/fetch/canonical_instrument_id) — `fetch` raises
      NotImplementedError for MVP.

### 1.8 MTDS DeFi refactor

- [x] [AGENT] P0. Helper `write_defi_rows` + `build_defi_partition_path` in `defi/canonical_write.py` (17 tests).
      Partition `day/category=defi/venue={V}/chain={C}/instrument_type={IT}/data_type={DT}/{file}.parquet`.
- [x] [AGENT] P0. `venue` = protocol only, `chain` separate partition column, `instrument_id` composed via UAC builder.
- [x] [AGENT] P0. No DeFi adapter currently writes parquet directly — CLI handlers own write path (Phase 3.3 callers
      will adopt helper).
- [x] [AGENT] P0. data_type values: lending_indices, dex_pool_swaps, dex_pool_state, lst_rates, yield_snapshots.
- [x] [AGENT] P0. instrument_type values: LENDING, POOL, LST, YIELD_BEARING, A_TOKEN, DEBT_TOKEN, STAKING, SPOT_ASSET.

### 1.9 Manifest writer zero-fill

- [x] [AGENT] P0.
      `ManifestWriter.write_with_zero_fill(actual_records, *, expected_catalogue, ref_date, category, venue, instrument_type, chain, data_type) -> int`
      (5 tests).
- [x] [AGENT] P0. New fields on `AvailabilityRecord`: `instrument_id`, `expected=True`, `available=True`
      (backwards-compatible defaults).
- [x] [AGENT] P0. Data status consumer distinguishes: (a) `row_count>0`, (b) `row_count=0, expected=True`, (c) no entry.

### 1.10 Testing + QG

- [x] [AGENT] P0. Unit tests per change: 156 new tests total across 9 streams.
- [x] [AGENT] P0. QG final status (vs Phase 0 baseline):
  - unified-api-contracts: GREEN (80s) — was GREEN
  - unified-trading-library: GREEN (99s) — was GREEN
  - instruments-service: 7 codex violations (baseline 7) — unchanged
  - market-tick-data-service: 397 pass, 1 pre-existing fail, codex ≤ 4 (baseline) — no regression
- [x] [AGENT] P0. env_canon.py `all_canonical()` refactored into 4 helpers to stay under 50L limit (pre-existing
      uncommitted drift from prior Tier 2 work).

**Incidental fixes made during Phase 1:**

- `env_canon.py` — split `all_canonical()` into
  `_core_canonical/_protocol_canonical/_cloud_canonical/_service_canonical` helpers.
- `instruments-service/scripts/quality-gates.sh` — added `reference_data/catalogue/*.py` to `DEEP_IMPORT_EXCLUDE_GLOBS`
  (legitimate `unified_api_contracts.internal` usage, matches pattern for adapters).
- `reference_data/__init__.py` — removed `CatalogueBuilder` re-export to break circular import; consumers import from
  `reference_data.catalogue` directly. Eager top-level imports in `catalogue_builder.py`.
- `tests/unit/reference_data/test_catalogue.py` — patch path updated to
  `catalogue_builder.fetch_instruments_for_all_venues` (imported at top level now).

## Phase 2 — Per-category smoke tests (sandbox bucket)

- [ ] [AGENT] P0. CeFi: Binance-Futures BTCUSDT perp 2024-06-15 → verify partition path + `instrument_id` column.
- [ ] [AGENT] P0. CeFi chain: Bybit BTC dated futures → verify `instrument_type=futures_chain`, `data_type=trades` (not
      `futures_chain`), per-underlying bundle.
- [ ] [AGENT] P0. TradFi option: CME ES options → `instrument_type=options_chain/data_type=trades/ES.parquet` with all
      day's strikes, canonical `instrument_id` per row.
- [ ] [AGENT] P1. TradFi equity: 1 equity (AAPL) 1 day.
- [ ] [AGENT] P0. DeFi: Aave V3 Ethereum →
      `venue=AAVE_V3/chain=ETHEREUM/instrument_type=lending_position/data_type=lending_indices/aUSDC.parquet`.
- [ ] [AGENT] P0. Per-day availability: strike list for 2024-06-15 BTC options matches expected (ATM ± range, strikes
      listed between listing and expiry).
- [ ] [AGENT] P0. Manifest zero-fill: an expected-empty shard produces a `row_count=0, expected=true` manifest entry.
- [ ] [SCRIPT] P0. QG green on all repos.

## Phase 3 — Migration (3 VMs parallel)

### 3.1 CeFi migration v2 [VM: cefi-migration]

- [ ] [AGENT] P0. Extend `migrate_to_per_instrument.py`:
  1. Split bundled `ticks.parquet` by symbol (perpetual/spot) [existing]
  2. **NEW**: rename `data_type=futures_chain` → `data_type=trades` (preserving `instrument_type=futures_chain`)
  3. **NEW**: add `instrument_id` column to all rows if missing (use canonical ID builder)
  4. **NEW**: validate output against schema contract before upload
- [ ] [SCRIPT] P0. Dry-run on 1 date → confirm counts + structure → run full bucket.

### 3.2 TradFi migration [VM: tradfi-migration]

- [ ] [AGENT] P0. New script `migrate_tradfi_canonical.py`:
  1. Scan `day/category=tradfi/venue=CME/instrument_type=future/data_type=trades/*.parquet`
  2. For each file, classify by symbol (options_chain / futures_chain / equity / index)
  3. Group per (day, underlying) and bundle into `options_chain/data_type=trades/{UNDERLYING}.parquet` etc.
  4. Write canonical `instrument_id` column per row
  5. Keep old files as `_migrated_...` for rollback, delete only after validation

### 3.3 DeFi migration [VM: defi-migration]

- [ ] [AGENT] P0. New script `migrate_defi_canonical.py`:
  1. Scan `day=*/venue=*-*/ticks.parquet`
  2. Parse venue (`AAVE_V3-ETHEREUM` → venue=`AAVE_V3`, chain=`ETHEREUM`)
  3. Read rows, infer data_type + instrument_type per row (from content)
  4. Group by (data_type, instrument_type, instrument_id)
  5. Write to canonical paths with `instrument_id` column

### 3.4 Migration VMs

- [ ] [SCRIPT] P0. Launch 3 VMs (e2-standard-8) with migration scripts, in-region (asia-northeast1-c), 32 workers each.
- [ ] [SCRIPT] P0. Stream progress to GCS logs. Alert on errors.

## Phase 4 — Fill gaps (new ingestion)

- [ ] [SCRIPT] P0. Identify periods not covered by migration (2025-Q1 onward for most categories).
- [ ] [SCRIPT] P0. Launch ingestion VMs for those periods only (avoid write conflicts with migration).

## Phase 5 — Manifest reconciliation

- [ ] [AGENT] P0. Delete manifest entries that reference old paths (e.g. old TradFi `instrument_type=future/` entries).
- [ ] [SCRIPT] P0. Rerun `rebuild_mtds_manifest.py` over migrated paths.
- [ ] [SCRIPT] P0. Emit zero-count entries for expected-empty days using per-day availability filter.

## Phase 6 — Validation (Data Status page)

- [ ] [HUMAN] P0. Open deployment-ui Data Status page.
- [ ] [HUMAN] P0. Confirm counts per (day, venue, instrument_type, data_type) match expectations.
- [ ] [HUMAN] P0. Confirm no "missing" flags for days where instrument was not yet listed or already expired.
- [ ] [HUMAN] P0. Confirm per-category coverage % matches reality for MVP venues/instruments.
- [ ] [AGENT] P1. If any discrepancies: file bugs against specific phases and iterate.

## Phase 7 — Documentation sweep

- [ ] [AGENT] P1. MTDS docs (`market-tick-data-service/docs/`): adapter behaviour, canonical path convention,
      `instrument_id` column convention, per-underlying bundling rule.
- [ ] [AGENT] P1. UTL docs (`unified-trading-library/docs/`): DataSink validation hooks, SchemaContract usage, strict vs
      legacy mode.
- [ ] [AGENT] P1. UAC docs (`unified-api-contracts/docs/`): canonical ID spec (full format table), InstrumentType enum,
      `get_instruments_available_on` API, generator usage.
- [ ] [AGENT] P1. instruments-service docs: instrument catalogue schema, `available_from/to` population logic,
      per-category reference data refresh cadence.
- [ ] [AGENT] P1. PM codex: update `/codex/02-data/availability-manifest-and-data-status.md` (expected-empty vs missing
      distinction), `codex/06-coding-standards/` add `canonical-instrument-ids.md` if missing.

## Regression prevention (how this can't happen again)

- [ ] [AGENT] P0. UTL pre-write hook (Phase 1.4) is MANDATORY for all adapters — fail loud on missing `instrument_id` or
      partition mismatch.
- [ ] [AGENT] P0. SchemaContract validation (Phase 1.3) runs on every `write()` call.
- [ ] [AGENT] P0. CI integration: at least one smoke test per adapter in CI that writes a sandbox parquet and asserts
      canonical structure.
- [ ] [AGENT] P1. Nightly data status page audit job: compare actual GCS structure to expected shard dimensions — alert
      on drift.
- [ ] [AGENT] P1. Code review checklist in PM: any adapter change must confirm canonical partitioning + instrument_id
      column.

## Success criteria

- **Code readiness C4**: QG green on all repos after Phase 1.
- **Deployment readiness D3**: All 3 category migrations complete + new ingestion caught up + smoke tests pass in
  staging.
- **Business readiness B3**: Data Status page (deployment-ui) shows correct counts per (day, venue, instrument_type,
  data_type) with correct denominators from per-day availability filter; zero false-missing flags.
