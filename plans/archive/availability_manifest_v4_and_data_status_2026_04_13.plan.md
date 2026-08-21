---
doc_type: plan
title: availability-manifest-v4-and-data-status
summary: Universal availability manifest schema v4 — proper shard columns, atomic writes, UAC SSOT registry, data status
  page hierarchy, codex documentation
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, deployment-ui, execution-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-13"
type: mixed
epic: epic-code-completion
completion_gates: { code: C5, deployment: D3, business: B3 }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: instruments-service, code: C0, deployment: none, business: none }
  - { repo: market-tick-data-service, code: C0, deployment: none, business: none }
  - { repo: market-data-processing-service, code: C0, deployment: none, business: none }
  - { repo: features-delta-one-service, code: C0, deployment: none, business: none }
  - { repo: features-volatility-service, code: C0, deployment: none, business: none }
  - { repo: features-onchain-service, code: C0, deployment: none, business: none }
  - { repo: features-sports-service, code: C0, deployment: none, business: none }
  - { repo: features-calendar-service, code: C0, deployment: none, business: none }
  - { repo: features-multi-timeframe-service, code: C0, deployment: none, business: none }
  - { repo: features-cross-instrument-service, code: C0, deployment: none, business: none }
  - { repo: features-commodity-service, code: C0, deployment: none, business: none }
  - { repo: ml-training-service, code: C0, deployment: none, business: none }
  - { repo: ml-inference-service, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: risk-and-exposure-service, code: C0, deployment: none, business: none }
  - { repo: pnl-attribution-service, code: C0, deployment: none, business: none }
  - { repo: alerting-service, code: C0, deployment: none, business: none }
  - { repo: deployment-api, code: C0, deployment: none, business: none }
  - { repo: deployment-ui, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-04-13
todos: []
isProject: false
superseded_by:
  [
    manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md,
    data_status_institutional_drilldown_2026_04_24.plan.md,
    honest_coverage_metrics_2026_04_19.plan.md,
  ]
reconciliation_status: superseded
reconciliation_date: 2026-04-25
---

> **SUPERSEDED 2026-04-25 by
> [manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md](./manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md),
> [data_status_institutional_drilldown_2026_04_24.plan.md](./data_status_institutional_drilldown_2026_04_24.plan.md),
> [honest_coverage_metrics_2026_04_19.plan.md](./honest_coverage_metrics_2026_04_19.plan.md).** Schema progressed past
> v4 (now v6); data-status drilldown shipped via dedicated 2026-04-24 plan Original scope retained for history. See
> `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# Availability Manifest v4 & Data Status Overhaul

## Problem Statement

The availability manifest (`_index/availability_index.parquet`) is the SSOT for "what data exists" across the entire
pipeline. It is currently broken in 4 ways:

1. **Schema underspecified (v3)** — 9 columns. Services need 16. Result: 8 services stuff non-venue data into `venue`
   (feature_group:timeframe, model_id, client_id, commodity names, "alert_history"). The data status page can't build a
   proper hierarchy because the shard dimensions are invisible.

2. **No hierarchy** — the data status page shows a flat grid of venue cards. DEFI shows 57 protocol-chain combos. SPORTS
   shows "ODDS_API". No drill-down into chain, protocol, data_type, instrument_type, league, bookmaker, feature_group,
   timeframe, or any actual dimension.

3. **Scattered documentation** — sharding concepts spread across 6+ codex docs, 3 memory files, 2 active plans, and
   service READMEs. New sessions re-derive the shard matrix from scratch every time.

4. **Inconsistent denominators** — availability % uses different expected-date logic per service (calendar days vs
   fixture calendar vs trading days vs start dates). No uniform principle.

## Pre-Audit Manifest (Blast Radius)

### ManifestWriter.add() Call Sites — EVERY Consumer

| #   | Repo                        | File                                   | Line(s)                   | Current venue= value                             | Fix needed                                                           |
| --- | --------------------------- | -------------------------------------- | ------------------------- | ------------------------------------------------ | -------------------------------------------------------------------- |
| 1   | unified-trading-library     | manifest_writer.py                     | 93-106                    | SSOT AvailabilityRecord                          | Add 7 new columns, bump v3→v4                                        |
| 2   | market-tick-data-service    | scripts/rebuild_mtds_manifest.py       | 115                       | venue=raw venue, data_type=partition_key         | Add chain, instrument_type for DeFi; bookmaker names for SPORTS      |
| 3   | instruments-service         | engine/orchestrator.py                 | 843-862                   | venue=f"API*FOOTBALL*{entity}"                   | Write league_id properly; venue should be empty for sports reference |
| 4   | instruments-service         | scripts/patch_prediction_shards.py     | 50                        | venue=shard_name ("PREDICTION::EPL")             | Write proper venue+league_id                                         |
| 5   | instruments-service         | tests/unit/test_league_partitioning.py | 81,130                    | mock: venue="API_FOOTBALL_FIXTURES", league_id=x | Update test expectations                                             |
| 6   | features-sports-service     | cli/handlers/batch_handler.py          | 329-339                   | venue=base_table ("events","teams"), league_id=x | Write feature_group=base_table                                       |
| 7   | features-volatility-service | engine/orchestrator.py                 | 198-206, 269-277, 649-657 | venue=f"options_volatility:{tf}"                 | Write feature_group + timeframe separately                           |
| 8   | features-commodity-service  | cli/handlers/batch_handler.py          | 219-222                   | venue=commodity_name                             | Write feature_group=commodity_name                                   |
| 9   | features-calendar-service   | engine/calendar_orchestrator.py        | 256-260                   | venue=category ("economic_events")               | Write feature_group=category                                         |
| 10  | pnl-attribution-service     | cli/handlers/compute_handler.py        | 241                       | venue=client_id                                  | Write strategy_id properly                                           |
| 11  | risk-and-exposure-service   | core/risk_snapshot_sink.py             | 120-124                   | venue=client_id                                  | Write client_id properly                                             |
| 12  | alerting-service            | persistence/storage_store.py           | 102-106                   | venue="alert_history"                            | Write proper dimension                                               |
| 13  | execution-service           | engine/modes/live/data_sink.py         | 16+                       | Instantiates ManifestWriter                      | Add strategy_id, venue, instruction_type                             |
| 14  | execution-service           | results/save_operations.py             | 24+                       | Instantiates ManifestWriter                      | Same                                                                 |

**Read-only consumers** (no .add() call, only read_availability_index): deployment-api, deployment-service,
features-sports-service (check script), instruments-service (verify/rebuild scripts), UTL dependency_check.

### Existing Documentation to Consolidate

| #   | Path                                                              | Content                                   | Action                      |
| --- | ----------------------------------------------------------------- | ----------------------------------------- | --------------------------- |
| 1   | /codex/04-architecture/shard-level-failure-isolation.md           | Shard dims per service, failure isolation | Merge into new SSOT doc     |
| 2   | /codex/02-data/venue-availability.md                              | UAC VenueMapping as SSOT                  | Merge into new SSOT doc     |
| 3   | /codex/02-data/partitioning.md                                    | GCS path templates                        | Reference from new SSOT doc |
| 4   | /codex/02-data/data-catalogue-schema.md                           | Catalogue schema                          | Reference from new SSOT doc |
| 5   | memory/project_availability_manifest_v4_full_matrix_2026_04_13.md | Full L1-L8 matrix                         | Source for new codex doc    |
| 6   | memory/feedback_shard_integrity_principles.md                     | 3 non-negotiable principles               | Source for new codex doc    |
| 7   | memory/feedback_defi_chain_grouping.md                            | Chain as separate column                  | Source for new codex doc    |
| 8   | memory/feedback_sports_venues_are_bookmakers.md                   | Bookmakers not ODDS_API                   | Source for new codex doc    |
| 9   | memory/feedback_no_data_source_column.md                          | Data type not data source                 | Source for new codex doc    |
| 10  | MTDS docs/GCS_PATHS.md                                            | MTDS path conventions                     | Cross-reference             |

## Migration Strategy (No Re-Downloads)

**Key insight:** All data is already in GCS. The manifest is just an INDEX of what's there. Migration = re-scan existing
GCS paths to produce v4 index entries with proper columns. Zero data re-downloads.

1. **v3→v4 backward compat in read_availability_index()**: Missing columns backfilled with "" (same pattern as v2→v3).
   Existing v3 indexes continue to work immediately.
2. **Services deploy with v4 writes**: New runs write proper columns. Old v3 entries coexist.
3. **Re-scan existing data**: Run manifest rebuild scripts per service to regenerate v4 entries from existing GCS paths.
   The paths already contain the information (instrument_type from hive path, protocol/chain from folder names, etc.).
4. **Dedup on write**: ManifestWriter already deduplicates on (date, venue, data_type, service_name, league_id). v4
   extends this to include new columns. Old v3 entries with venue="" new columns get superseded by v4 entries.
5. **No GCS data changes**: Parquet files in GCS are untouched. Only `_index/availability_index.parquet` is regenerated.

## Principles (Non-Negotiable)

1. **Atomic shard failure** — if ANY item in a shard fails, the ENTIRE shard fails. ManifestWriter.add() only called
   after full shard write succeeds. No partial writes ever.
2. **Schema validation before write** — ParquetSchemaEnforcer runs before every GCS write. NaN/type/column checks.
   Schema failure = shard failure = no write = shows as missing on data status page.
3. **Single SSOT for registry** — UAC is the ONLY source for: what venues exist, what chains exist, what data_types
   exist, what feature_groups exist, when each became available. No hardcoded lists in services. Expected-date
   denominator ALWAYS comes from UAC.
4. **Sparseness is expected** — not all shards expected every day. Fixture calendar for SPORTS, trading calendar for
   TradFi, transfer window calendar for transfer data, per-chain start dates for DeFi. The denominator must account for
   sparseness — a day with no fixtures is not a missing shard.
5. **Data freshness** — `written_at` column enables point-in-time queries. "What data existed as of timestamp X?"

## Target Schema v4

```python
MANIFEST_SCHEMA_VERSION = 4

@dataclass
class AvailabilityRecord:
    # Universal
    date: str                       # YYYY-MM-DD
    service_name: str               # "instruments-service", "market-tick-data-service", etc.
    written_at: str                 # ISO timestamp
    schema_version: int = 4
    instrument_count: int = 0       # rows/instruments in the shard

    # Market data dimensions
    venue: str = ""                 # tradeable venue or protocol (BINANCE-SPOT, AAVE_V3, PINNACLE)
    chain: str = ""                 # DeFi only: ETHEREUM, ARBITRUM, BASE, SOLANA, etc.
    data_type: str = ""             # trades, book_snapshot_5, odds, swaps, liquidity, etc.
    instrument_type: str = ""       # spot, perpetuals, equity, pool, lending, prediction_market
    league_id: str = ""             # SPORTS only

    # Processing dimensions
    timeframe: str = ""             # MDPS: 15s-24h or T-24h..T-0. Features: 1m, 5m, 1h

    # Feature/ML dimensions
    feature_group: str = ""         # feature services: momentum, fixture_stats, macro_sentiment, etc.
    model_family: str = ""          # ML: pregame_xg, CEFI_BTC_swing-high_LIGHTGBM_1h_V1, etc.
    training_period: str = ""       # ML walk-forward: 2024-01 (month) or 2024 (season)

    # Downstream dimensions
    strategy_id: str = ""           # strategy/execution/PnL services
    client_id: str = ""             # risk service
    instruction_type: str = ""      # execution: TRADE, SWAP, LEND, BORROW, STAKE
```

## Execution DAG

```
Phase 0 (Documentation)
    ↓
Phase 1 (Foundation: UAC + UTL)
    ↓ QG gate
Phase 2 (Write-side: all 14 services — PARALLEL)
    ↓ QG gate
Phase 3 (GCS migration: re-scan existing data — PARALLEL per service)
    ↓
Phase 4 (Read-side: deployment-api)
    ↓ QG gate
Phase 5 (UI: deployment-ui)
    ↓ QG gate
Phase 6 (Validation: E2E + docs update + context propagation)
```

---

## Phase 0 — SSOT Documentation [BEFORE any code]

Create ONE codex reference document that is THE canonical source for sharding, availability, and data status. Every
other doc, CLAUDE.md, cursor rule, and memory file points to it.

- [ ] [AGENT] P0. Create `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md` — the SSOT
      document. Contents:
  - Schema v4 definition (all 16 columns, what each means, defaults)
  - Per-service shard dimension matrix (L1-L8, the full table from memory)
  - Data status page tree hierarchy per service × category
  - Availability % calculation: `found / expected × 100`, where expected comes from UAC
  - Sparseness rules: fixture calendar, trading calendar, transfer windows, per-chain start dates
  - Atomic shard failure principle
  - Schema validation principle
  - UAC SSOT principle (what functions to call, where start dates live)
  - Data freshness (written_at, point-in-time queries)
  - Migration: v3→v4 backward compatibility
  - DeFi chain grouping (venue=protocol, chain=chain)
  - Sports bookmaker venues (not ODDS_API)
  - No data_source column (track data type not source)

- [ ] [AGENT] P0. Update `/codex/04-architecture/shard-level-failure-isolation.md` — replace inline shard dimension
      tables with a cross-reference to the new SSOT doc. Keep the failure isolation rules, remove the per-service
      dimension lists (they now live in the SSOT doc).

- [ ] [AGENT] P0. Update `/codex/02-data/venue-availability.md` — add cross-reference to new SSOT doc for the complete
      picture. Keep UAC VenueMapping details.

- [ ] [AGENT] P0. Update root `.claude/CLAUDE.md` — add a section referencing the SSOT doc: "For sharding dimensions,
      availability manifest schema, data status page hierarchy, and missing data logic, see
      `/codex/02-data/availability-manifest-and-data-status.md`."

- [ ] [AGENT] P0. Create cursor rule `.cursor/rules/availability-manifest-ssot.mdc` — short rule that says: "When
      working on ManifestWriter, data status, availability index, or shard dimensions, read
      `/codex/02-data/availability-manifest-and-data-status.md` first. It is the SSOT."

- [ ] [AGENT] P0. QG pass for unified-trading-pm (docs fast-path — targets main directly).

## Phase 1 — Foundation (UAC + UTL) [SEQUENTIAL]

### 1A. UAC Registry Extensions

- [ ] [AGENT] P0. Add `Chain` enum or constants to UAC with all 11 chains (ETHEREUM, ARBITRUM, BASE, OPTIMISM, POLYGON,
      BSC, AVALANCHE, LINEA, SOLANA, HYPERLIQUID, ASTER) and per-chain data-availability start dates. Location:
      `registry/capability_declarations/_defi.py` or new `_chains.py`.

- [ ] [AGENT] P0. Add `get_venue_chain_start_date(venue: str, chain: str) -> str | None` to VenueMapping. Returns when a
      protocol became available on a specific chain. Source: existing SUBGRAPH_IDS + \_STATIC_VENUE_CHAINS in `_defi.py`
      already have this implicitly — make it queryable.

- [ ] [AGENT] P0. Add `get_expected_instrument_types_for_venue(venue: str) -> list[str]` to UAC. Returns instrument
      types a venue should produce (spot, perpetuals for BINANCE-FUTURES; pool, lending for AAVE_V3; etc.). Source:
      existing `venue_data_type_capabilities` mapping — extend to instrument_type.

- [ ] [AGENT] P0. Add sports bookmaker registry to UAC: `get_expected_bookmakers() -> list[str]` returning the ~23
      audited clean bookmakers with start dates and `is_execution_venue` boolean. Source: existing ODDS_API_KEY_MAP in
      `registry/_odds_api_maps.py` — add start dates and audit status.

- [ ] [AGENT] P0. Add `get_expected_feature_groups_for_service(service_name: str) -> list[str]` to UAC with start dates.
      Source: FeatureGroupRegistry in UTL has 39 groups — expose the list and start dates through UAC.

- [ ] [AGENT] P0. Add `get_expected_timeframes_for_service(service_name: str, category: str) -> list[str]` to UAC.
      Returns valid timeframes per service+category (15s-24h for MDPS CEFI; T-24h..T-0 for MDPS SPORTS; 1m for
      features-volatility; etc.).

- [ ] [AGENT] P1. Verify ALL existing start date functions are complete and consistent:
      `get_venue_data_type_start_date`, `get_expected_data_types_for_venue`, `get_league_fixture_calendar`,
      `get_expected_trading_dates`. Audit every venue for correct start dates — if a venue has data in GCS before its
      UAC start date, the start date is wrong.

- [ ] [AGENT] P1. QG pass for unified-api-contracts.

### 1B. UTL ManifestWriter v4

- [ ] [AGENT] P0. Add 7 new fields to `AvailabilityRecord`: `chain`, `instrument_type`, `feature_group`, `model_family`,
      `training_period`, `strategy_id`, `client_id`, `instruction_type`. All default "". Bump `MANIFEST_SCHEMA_VERSION`
      from 3 to 4. File: `manifest_writer.py:93`.

- [ ] [AGENT] P0. Update `ManifestWriter.add()` to accept new kwargs. File: `manifest_writer.py:165-178`. Add:
      `chain=""`, `instrument_type=""`, `feature_group=""`, `model_family=""`, `training_period=""`, `strategy_id=""`,
      `client_id=""`, `instruction_type=""`.

- [ ] [AGENT] P0. Update `read_availability_index()` backward compat (file: `manifest_writer.py:454-515`): if columns
      missing (v3 index), backfill with "". Same pattern as existing schema_version/data_type/league_id backfill at
      lines 498-503. Add: chain, instrument_type, feature_group, model_family, training_period, strategy_id, client_id,
      instruction_type.

- [ ] [AGENT] P0. Update empty DataFrame schema (returned when index doesn't exist) to include all 16 columns.

- [ ] [AGENT] P0. Update dedup key logic (file: `manifest_writer.py:420-430`): include new columns when non-empty.
      Current: `(date, venue, data_type, service_name)` + league_id if non-empty. v4: same pattern for all new columns.

- [ ] [AGENT] P1. Add unit tests for v4 schema: test new columns in .add(), test read v3 index with v4 code (backward
      compat), test dedup with new columns, test empty index schema.

- [ ] [AGENT] P1. QG pass for unified-trading-library.

### 1C. UTL Schema Enforcer

- [ ] [AGENT] P1. Verify `ParquetSchemaEnforcer` rejects: NaN values in required columns, wrong column types, missing
      required columns. If not, add checks. Schema failure must raise, not warn.

- [ ] [AGENT] P1. Add schema validation for availability_index.parquet itself — date is str YYYY-MM-DD format, venue is
      uppercase str, instrument_count is non-negative int, written_at is ISO format, etc.

**QG GATE:** Phase 1 complete when UAC + UTL both pass `bash scripts/quality-gates.sh`.

## Phase 2 — Write-Side (All Services) [PARALLEL within phase]

Each service updates its ManifestWriter.add() calls to use proper columns instead of overloading venue. **No behavioral
changes** — same shards written, same data, just proper column assignments.

### 2A. instruments-service (3 call sites)

- [ ] [AGENT] P0. `engine/orchestrator.py:843-862`: Sports reference — stop writing venue=f"API*FOOTBALL*{entity}".
      Write: `feature_group=entity_name` (or leave venue empty, write league_id). Sports reference tracks league×date
      coverage, not source×date.

- [ ] [AGENT] P0. `engine/orchestrator.py`: DeFi instruments — split venue (AAVE_V3-ETHEREUM) into venue=AAVE_V3 +
      chain=ETHEREUM. Add instrument_type (POOL, LENDING, LST, STAKING) from InstrumentType enum.

- [ ] [AGENT] P0. `engine/orchestrator.py`: CEFI/TRADFI — add instrument_type (SPOT_PAIR, PERPETUAL, FUTURE, OPTION,
      EQUITY, INDEX) from the instrument records being written.

- [ ] [AGENT] P0. `scripts/patch_prediction_shards.py:50`: Fix venue="PREDICTION::EPL" → proper venue+league_id.

- [ ] [AGENT] P0. `tests/unit/test_league_partitioning.py:81,130`: Update mock expectations for new column names.

- [ ] [AGENT] P1. QG pass.

### 2B. market-tick-data-service (1 call site + data_manifest_handler)

- [ ] [AGENT] P0. `scripts/rebuild_mtds_manifest.py:115`: Add chain, instrument_type extraction from GCS hive paths. For
      DeFi: parse protocol and chain from `{protocol}/{chain}/date=` path. For CEFI/TRADFI: parse instrument_type from
      `instrument_type={itype}/` in hive path.

- [ ] [AGENT] P0. `cli/handlers/data_manifest_handler.py`: All `_scan_*` functions — when building availability index
      rows, include chain (from path parsing) and instrument_type where applicable. For SPORTS: write individual
      bookmaker names as venue (extract from raw data) instead of "ODDS_API".

- [ ] [AGENT] P1. QG pass.

### 2C. market-data-processing-service

- [ ] [AGENT] P0. Stop stuffing data_type into venue. Write: venue=actual venue, data_type=actual data_type,
      timeframe=actual timeframe (15s/1m/5m/.../24h or T-24h/.../T-0), instrument_type where applicable, chain for DeFi,
      league_id for SPORTS.

- [ ] [AGENT] P1. QG pass.

### 2D. features-volatility-service (3 call sites)

- [ ] [AGENT] P0. `engine/orchestrator.py:198-206,269-277,649-657`: Replace venue=f"options_volatility:{tf}" with
      `feature_group="options_volatility", timeframe=tf`. Same for futures_term_structure, options_term_structure, etc.

- [ ] [AGENT] P1. QG pass.

### 2E. features-sports-service (1 call site)

- [ ] [AGENT] P0. `cli/handlers/batch_handler.py:329-339`: Replace venue=base_table with
      `feature_group=base_table, league_id=manifest_league`.

- [ ] [AGENT] P1. QG pass.

### 2F. features-commodity-service (1 call site)

- [ ] [AGENT] P0. `cli/handlers/batch_handler.py:219-222`: Replace venue=commodity_name with
      `feature_group=commodity_name`.

- [ ] [AGENT] P1. QG pass.

### 2G. features-calendar-service (1 call site)

- [ ] [AGENT] P0. `engine/calendar_orchestrator.py:256-260`: Replace venue=category with `feature_group=category`.

- [ ] [AGENT] P1. QG pass.

### 2H. features-onchain-service

- [ ] [AGENT] P0. Add timeframe to ManifestWriter calls (currently missing entirely). Add chain where applicable
      (lending_rates on ETHEREUM vs ARBITRUM).

- [ ] [AGENT] P1. QG pass.

### 2I. features-delta-one, features-multi-timeframe, features-cross-instrument

- [ ] [AGENT] P0. Each: verify ManifestWriter calls write feature_group and timeframe as proper columns. If overloading
      venue, fix.

- [ ] [AGENT] P1. QG pass for all three.

### 2J. pnl-attribution-service (1 call site)

- [ ] [AGENT] P0. `cli/handlers/compute_handler.py:241`: Replace venue=client_id with
      `strategy_id=<actual strategy>, client_id=<if needed>`.

- [ ] [AGENT] P1. QG pass.

### 2K. risk-and-exposure-service (1 call site)

- [ ] [AGENT] P0. `core/risk_snapshot_sink.py:120-124`: Replace venue=client_id with `client_id=client_id`.

- [ ] [AGENT] P1. QG pass.

### 2L. alerting-service (1 call site)

- [ ] [AGENT] P0. `persistence/storage_store.py:102-106`: Replace venue="alert_history" with proper dimension (or remove
      manifest write if alerting doesn't need data status tracking).

- [ ] [AGENT] P1. QG pass.

### 2M. execution-service (2 call sites)

- [ ] [AGENT] P0. `engine/modes/live/data_sink.py` and `results/save_operations.py`: Add strategy_id, instruction_type,
      venue (actual execution venue) to ManifestWriter calls.

- [ ] [AGENT] P1. QG pass.

### 2N. ml-training-service + ml-inference-service

- [ ] [AGENT] P0. ml-training: write model_family and training_period instead of stuffing model_id into venue.

- [ ] [AGENT] P0. ml-inference: write model_family instead of stuffing mode into venue.

- [ ] [AGENT] P1. QG pass for both.

### 2O. strategy-service

- [ ] [AGENT] P0. Verify ManifestWriter writes strategy_id properly. Fix if overloading venue.

- [ ] [AGENT] P1. QG pass.

**QG GATE:** Phase 2 complete when ALL 14 services pass `bash scripts/quality-gates.sh`.

## Phase 3 — GCS Index Migration (Re-Scan Existing Data) [PARALLEL per service]

No data re-downloads. Re-run manifest scanners to produce v4 index entries from existing GCS paths.

- [ ] [AGENT] P0. Write a `scripts/rebuild_v4_manifest.py` script in UTL (or per-service) that:
  1. Reads existing GCS paths for a given service+category+bucket
  2. Extracts new columns from the path structure (instrument_type from hive path, chain from folder, etc.)
  3. Writes v4 availability_index.parquet with all columns populated
  4. Validates: count of v4 entries >= count of v3 entries (no data loss)

- [ ] [SCRIPT] P0. Run rebuild for instruments-service (5 category buckets).

- [ ] [SCRIPT] P0. Run rebuild for MTDS (5 category buckets + 10 DeFi sub-dimension buckets).

- [ ] [SCRIPT] P0. Run rebuild for MDPS (4 category buckets).

- [ ] [SCRIPT] P1. Run rebuild for feature services (7 services × their buckets).

- [ ] [SCRIPT] P1. Run rebuild for ML services (2 services).

- [ ] [SCRIPT] P1. Run rebuild for strategy/execution/risk/PnL (4 services).

- [ ] [HUMAN] P0. Spot-check 3+ rebuilt indexes: verify new columns populated correctly, instrument_count matches, no
      entries lost vs v3.

**GATE:** Phase 3 complete when all rebuilt indexes verified.

## Phase 4 — Read-Side (deployment-api) [SEQUENTIAL after Phase 2+3]

- [ ] [AGENT] P0. Update `_build_manifest_category()` in data_status_service.py to read new columns from v4 index. Build
      tree breakdowns using actual populated columns.

- [ ] [AGENT] P0. Add `_build_chain_breakdown()`: group DeFi venues by chain→protocol. Support protocol→chain toggle via
      `?defi_grouping=chain|protocol` query param.

- [ ] [AGENT] P0. Update `_build_venue_breakdown()`: add instrument_type as a sub-level between venue and data_type for
      CEFI/TRADFI. Add bookmaker-level detail for SPORTS.

- [ ] [AGENT] P0. Add `_build_feature_group_breakdown()`: feature_group → timeframe → [chain|league] → dates.

- [ ] [AGENT] P0. Add `_build_model_breakdown()`: model_family → training_period → dates.

- [ ] [AGENT] P0. Add `_build_strategy_breakdown()`: strategy → [venue → instruction_type →] dates.

- [ ] [AGENT] P0. Add `_build_client_breakdown()`: client → dates.

- [ ] [AGENT] P0. Update expected-date denominator to use UAC for ALL dimensions uniformly:
  - `get_venue_chain_start_date()` for DeFi per-chain
  - `get_expected_bookmakers()` for SPORTS
  - `get_expected_feature_groups_for_service()` for features
  - `get_league_fixture_calendar()` for SPORTS sparseness
  - `get_expected_trading_dates()` for TradFi weekends
  - `get_expected_timeframes_for_service()` for MDPS/features Availability % = found / expected × 100 where expected
    comes ONLY from UAC.

- [ ] [AGENT] P0. Add `as_of_timestamp` query param for data freshness — filters by `written_at <= timestamp`.

- [ ] [AGENT] P0. Update `TurboDataStatusResponse` shape — add new sub-dimension types matching all hierarchies.

- [ ] [AGENT] P0. Update deployment-api tests — mock v4 indexes, verify correct tree structures for each
      service×category combo. Test backward compat (v3 index read by v4 code).

- [ ] [AGENT] P1. QG pass for deployment-api.

## Phase 5 — UI (deployment-ui) [SEQUENTIAL after Phase 4]

- [ ] [AGENT] P0. Update TypeScript types in client.ts: add interfaces for chain breakdown, feature_group breakdown,
      model breakdown, strategy breakdown, client breakdown. Extend TurboSubDimension with chain, instrument_type,
      leagues, feature_groups fields.

- [ ] [AGENT] P0. Implement hierarchical tree rendering in DataStatusTab.tsx — per service, per category:
  - **DEFI:** chain → protocol → data_type → [timeframe] → dates (with chain/protocol toggle dropdown)
  - **CEFI/TRADFI:** venue → instrument_type → data_type → [timeframe] → dates
  - **SPORTS:** league → [bookmaker|timeframe] → dates
  - **PREDICTION:** venue → data_type → dates
  - **Features:** feature_group → [timeframe] → [chain|league] → dates
  - **ML:** model_family → [training_period] → dates
  - **Strategy/Execution:** strategy → [venue → instruction_type] → dates
  - **Risk:** client → dates Each node: name, completion %, progress bar, found/expected count, expand to show children.

- [ ] [AGENT] P0. Add DeFi grouping toggle (chain-first vs protocol-first) as a dropdown above the DeFi tree.

- [ ] [AGENT] P0. Add data freshness timestamp picker — "show data as of [datetime]" that passes as_of_timestamp to the
      API.

- [ ] [AGENT] P1. Smoke build: `VITE_MOCK_API=true npx vite build`.

- [ ] [AGENT] P1. Start dev server, verify all trees render correctly against real deployment-api with real GCS data.
      Check: DEFI (chain grouping, protocol drill-down), CEFI (instrument_type level), SPORTS (league→bookmaker),
      features (feature_group→timeframe), ML (model_family). Screenshot each for review.

- [ ] [AGENT] P1. QG pass for deployment-ui.

## Phase 6 — Validation & Documentation Propagation [SEQUENTIAL after Phase 5]

### E2E Validation

- [ ] [HUMAN+AGENT] P0. Verify data status page for EVERY service × category combo with real GCS data. Confirm:
  - Correct tree hierarchy rendered
  - Availability % within 1% of manual spot-check
  - No false positives (shard marked present but partial/corrupt)
  - No false negatives from start date misconfiguration
  - Sparse categories (SPORTS fixtures, TradFi weekends) show correct expected counts

- [ ] [HUMAN+AGENT] P0. Test atomic shard failure: intentionally break one item in a shard, confirm entire shard shows
      as missing on data status page.

- [ ] [HUMAN+AGENT] P0. Test data freshness: pick a timestamp, confirm only shards with written_at <= timestamp appear.

- [ ] [HUMAN+AGENT] P0. Test backward compat: load a v3 index file, confirm it displays correctly (new columns show as
      empty, existing data intact).

### Documentation & Context Propagation

- [ ] [AGENT] P0. Update the SSOT codex doc (`/codex/02-data/availability-manifest-and-data-status.md`) with any changes
      made during implementation. Ensure it matches the final code exactly.

- [ ] [AGENT] P0. Update root `.claude/CLAUDE.md` — add to "Key Rules" section: "Availability manifest schema v4 — see
      `/codex/02-data/availability-manifest-and-data-status.md` for shard dimensions, data status hierarchy, and
      integrity principles. ManifestWriter writes proper columns (venue, chain, data_type, instrument_type, league_id,
      timeframe, feature_group, model_family, training_period, strategy_id, client_id, instruction_type). Never overload
      `venue` with non-venue data."

- [ ] [AGENT] P0. Update per-repo `.claude/CLAUDE.md` for deployment-api and deployment-ui — add reference to SSOT doc
      for data status page architecture.

- [ ] [AGENT] P0. Update memory files: mark old memory entries about shard confusion as superseded by the codex doc. Add
      a single memory entry pointing to the SSOT doc.

- [ ] [AGENT] P0. Verify cursor rule `.cursor/rules/availability-manifest-ssot.mdc` is created and active.

- [ ] [AGENT] P1. QG pass for unified-trading-pm (docs fast-path).

## Success Criteria

### Code (C5)

- All 22 repos pass quality-gates.sh
- ManifestWriter v4 writes correct columns for all 14 writing services
- read_availability_index handles v3→v4 transparently
- All 22+ .add() call sites migrated to proper columns

### Deployment (D3)

- Data status page renders correct hierarchical trees in staging with real GCS data
- All service × category combos verified visually
- v3→v4 backward compat verified in staging

### Business (B3)

- **Accuracy:** Availability % within 1% of manual audit for 5+ services
- **Freshness:** written_at filtering works correctly (verified with timestamp picker)
- **False positives:** 0% — no shard marked "present" that is partial or corrupt
- **False negatives:** < 1% — missing shards correctly attributed (start date or sparseness)
- **Documentation:** ONE reference doc, all other docs cross-reference it, new sessions don't re-derive the matrix
