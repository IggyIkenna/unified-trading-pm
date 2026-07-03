---
doc_type: plan
title: mtds-multi-dimensional-shard-architecture
summary:
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, instruments-service, market-tick-data-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-14'
overview: Multi-dimensional shard tracking, schema validation, smart caching, and UAC governance for MTDS
type: code
epic: epic-code-completion
archived_date: 2026-05-06
archived_reason: superseded by manifest_schema_v6_quote_margin_combo_2026_04_23 + manifest_429_per_vm_sharding_2026_04_25 per 2026-04-25 reconciliation
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
- {repo: deployment-api, code: C0, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
superseded_by: [manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md, manifest_429_per_vm_sharding_2026_04_25.plan.md]
reconciliation_status: superseded
reconciliation_date: 2026-04-25
---

> **SUPERSEDED 2026-04-25 by
> [manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md](./manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md),
> [manifest_429_per_vm_sharding_2026_04_25.plan.md](./manifest_429_per_vm_sharding_2026_04_25.plan.md).** Parent
> umbrella; the two newer plans carved out the actual work (UTL d8d5f22c, 7c6f155a, c95480de) Original scope retained
> for history. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# MTDS Multi-Dimensional Shard Architecture

## Context

Market-tick-data-service (MTDS) already has solid foundations — hive-partitioned GCS paths, PartitionedTickWriter
routing chunks by (instrument_type, data_type), and ManifestWriter integration. But the **skip logic, schema validation,
and deployment UI visibility** are still single-dimensional (date-level), creating a gap between how the service
actually writes data (multi-dimensional shards) and how it skips/displays data (flat date set).

**Goal**: Bring MTDS to instruments-service parity — same `check_shard_freshness()` smart caching, same tight schema
validation, same SSOT between service operation and deployment UI. Add UAC per-venue data type governance so the system
knows _which_ data types each venue should produce.

### What's Already Done (Path of Least Resistance)

| Capability                                                                | Status        | Where                              |
| ------------------------------------------------------------------------- | ------------- | ---------------------------------- |
| Hive-partitioned GCS paths with instrument_type + data_type               | DONE          | orchestrator.py L180-186           |
| PartitionedTickWriter (routes chunks by itype/dt)                         | DONE          | orchestrator.py L155-252           |
| ManifestWriter with data_type in availability index                       | DONE          | orchestrator.py L499-522           |
| `_MERGED_DATA_TYPE_MAP` (futures_chain → options_chain)                   | DONE          | orchestrator.py L60-62             |
| `_DATA_TYPE_TO_INSTRUMENT_TYPE` overrides                                 | DONE          | orchestrator.py L65-68             |
| Symbol-level classification for mixed venues                              | DONE          | orchestrator.py L100-139           |
| UAC `DATA_TYPES_BY_CATEGORY` + `VENUES_BY_CATEGORY`                       | DONE          | market_data_categories.py          |
| UAC `get_valid_data_types_for_venue()` + `validate_data_type_for_venue()` | DONE          | market_data_categories.py L318-336 |
| UTL `check_shard_freshness()` with cache TTL                              | DONE          | manifest_writer.py L454-529        |
| UTL `ManifestWriter` with generation-match locking                        | DONE          | manifest_writer.py L75-328         |
| DomainValidationService imported in MTDS                                  | DONE (unused) | orchestrator.py L56                |
| Deployment UI venue-level breakdown                                       | DONE          | data_status_service.py L551-597    |
| Deployment UI bucket category overrides                                   | DONE          | data_status_service.py L232-234    |

### Gaps to Fill

| Gap                                                                 | Impact                                                             | Fix Location                      |
| ------------------------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------- |
| Skip logic is date-level only (flat set of completed dates)         | Re-downloads entire date when only 1 venue failed                  | tick_data_handler.py L93-98, L108 |
| No `check_shard_freshness()` — uses raw `read_availability_index()` | No schema version check, no staleness detection                    | tick_data_handler.py L87-99       |
| DomainValidationService imported but never called                   | No schema validation on written data                               | orchestrator.py L56               |
| UAC lacks per-venue-per-data-type start dates                       | Can't tell deployment UI "DERIBIT options_chain starts 2022-01-01" | market_data_categories.py (new)   |
| Deployment UI doesn't show data_type dimension under venues         | Can't see which data types are missing per venue                   | data_status_service.py            |
| Manifest `data_type` is combined "itype/dt" string                  | Deployment UI can't parse instrument_type vs data_type             | orchestrator.py L506-511          |
| No adapter epoch versioning                                         | Can't invalidate stale manifest entries after adapter changes      | orchestrator.py (new)             |

## Dependency DAG

```
Phase 1 (UAC — SSOT additions)
    ├── 1A: Per-venue data type capabilities + start dates
    └── 1B: Manifest data_type field contract (split itype/dt)
            │
            ▼  ── QG gate: UAC ──
Phase 2 (MTDS — service-side, PARALLEL items)
    ├── 2A: Smart skip with check_shard_freshness()
    ├── 2B: Schema validation pre-write
    ├── 2C: Split manifest data_type field (itype separate from dt)
    └── 2D: Adapter epoch versioning
            │
            ▼  ── QG gate: MTDS ──
Phase 3 (Deployment UI + UTL — PARALLEL items)
    ├── 3A: Deployment UI data_type dimension display
    └── 3B: UTL check_shard_freshness data_type awareness (if needed)
            │
            ▼  ── QG gate: deployment-api, UTL ──
Phase 4 (Integration validation)
    └── 4A: Workspace-wide QG on all 4 repos
```

## Pre-Audit Manifest

### Symbols being added/modified

| Repo           | File                                 | Symbol                             | Action                                              |
| -------------- | ------------------------------------ | ---------------------------------- | --------------------------------------------------- |
| UAC            | `registry/market_data_categories.py` | `VENUE_DATA_TYPE_CAPABILITIES`     | ADD — per-venue dict of data_types with start dates |
| UAC            | `registry/market_data_categories.py` | `get_venue_data_type_start_date()` | ADD — lookup function                               |
| UAC            | `__init__.py`                        | re-export                          | ADD — expose new symbols                            |
| MTDS           | `engine/orchestrator.py`             | `_DOMAIN_VALIDATOR`                | MODIFY — activate validation calls                  |
| MTDS           | `engine/orchestrator.py`             | `shard_counts` / manifest write    | MODIFY — split data_type field                      |
| MTDS           | `engine/orchestrator.py`             | `_VENUE_ADAPTER_EPOCH`             | ADD — epoch versioning                              |
| MTDS           | `cli/handlers/tick_data_handler.py`  | `preflight()` / `process()`        | MODIFY — use check_shard_freshness                  |
| deployment-api | `services/data_status_service.py`    | `_build_venue_breakdown()`         | MODIFY — add data_type sub-dimension                |
| UTL            | `manifest_writer.py`                 | `check_shard_freshness()`          | AUDIT — may need data_type filter param             |

### Downstream consumers of modified symbols

- `market_data_categories.py` changes: MTDS (orchestrator.py), deployment-api (data_status_service.py), MDPS, features
  services — all read-only consumers; new symbols are additive (no breakage)
- ManifestWriter `data_type` field: deployment-api reads it, MTDS writes it — both updated in this plan
- `check_shard_freshness()`: instruments-service (current user), MTDS (new user) — signature unchanged

---

## Phase 1 — UAC SSOT Additions

### 1A. Per-venue data type capabilities with start dates

- [ ] [AGENT] P0. Add `VENUE_DATA_TYPE_CAPABILITIES` dict to `market_data_categories.py`

  Structure: `dict[str, dict[str, str]]` — `{venue: {data_type: start_date}}`. Governs which data types a venue can
  produce and when that capability started.

  Example entries:

  ```python
  VENUE_DATA_TYPE_CAPABILITIES: dict[str, dict[str, str]] = {
      # CeFi — Tardis historical availability
      "BINANCE-SPOT": {"trades": "2019-01-01", "book_snapshot_5": "2019-09-01"},
      "BINANCE-FUTURES": {"trades": "2019-09-08", "book_snapshot_5": "2019-09-08",
                          "derivative_ticker": "2019-09-08", "liquidations": "2019-09-08"},
      "DERIBIT": {"trades": "2019-01-01", "book_snapshot_5": "2019-01-01",
                  "derivative_ticker": "2019-01-01", "options_chain": "2019-01-01",
                  "futures_chain": "2019-01-01"},
      # TradFi
      "NASDAQ": {"trades": "2024-01-01", "ohlcv_1m": "2024-01-01", "tbbo": "2024-01-01"},
      "CBOE": {"ohlcv_15m": "2020-01-07"},  # VIX — Barchart CSV start
      "FX": {"ohlcv_24h": "2020-01-01"},
      # DeFi — normalized 10 data types (dex_swaps, dex_pools, lending_indices, etc.)
      "UNISWAP_V3-ETHEREUM": {"dex_swaps": "2021-05-05", "dex_pools": "2021-05-05"},
      "AAVE_V3-ETHEREUM": {"lending_indices": "2023-01-27", "oracle_prices": "2023-01-27",
                          "rewards": "2023-01-27", "risk_params": "2023-01-27"},
      # Sports
      "ODDS_API": {"odds": "2024-01-01", "odds_snapshot": "2024-01-01",
                   "odds_movement": "2024-01-01", "arbitrage_opportunity": "2024-01-01"},
      # Prediction
      "POLYMARKET": {"prediction_trades": "2024-06-01", "prediction_book_snapshot": "2024-06-01",
                     "prediction_market_metadata": "2024-06-01"},
  }
  ```

  Fill in ALL venues from `VENUES_BY_CATEGORY` with their data types from `DATA_TYPES_BY_CATEGORY`. Start dates come
  from `VenueMapping.venue_start_dates` as default — same date for all data types unless a data type started later (e.g.
  Deribit options_chain). Unknown = venue start date.

- [ ] [AGENT] P0. Add `get_venue_data_type_start_date(venue, data_type)` helper function

  Returns the start date for a specific (venue, data_type) pair. Falls back to `VenueMapping.venue_start_dates[venue]`
  if the data type isn't in capabilities. Returns `None` for unknown venue/data_type (permissive).

- [ ] [AGENT] P0. Add `get_expected_data_types_for_venue(venue)` helper function

  Returns `list[str]` of data types the venue is expected to produce. Uses `VENUE_DATA_TYPE_CAPABILITIES` if venue is
  present, else falls back to `get_valid_data_types_for_venue(venue)` (category-level).

- [ ] [AGENT] P1. Re-export new symbols from UAC `__init__.py`

  Add `VENUE_DATA_TYPE_CAPABILITIES`, `get_venue_data_type_start_date`, `get_expected_data_types_for_venue` to the
  public surface.

### 1B. Document manifest data_type field contract

- [ ] [AGENT] P1. Add docstring/comment in `manifest_writer.py` AvailabilityRecord

  Clarify that `data_type` field should contain the raw data type name (e.g. "trades", "options_chain") NOT a combined
  "instrument_type/data_type" path. Services that need instrument_type tracking should use a separate convention or
  embed it differently. This is documentation only — the schema already supports it.

**Success criteria Phase 1:**

- `cd unified-api-contracts && bash scripts/quality-gates.sh` passes
- New functions return correct data for all 5 categories
- No downstream breakage (additive only)

---

## Phase 2 — MTDS Service-Side (PARALLEL)

### 2A. Smart skip with check_shard_freshness

- [ ] [AGENT] P0. Replace date-level skip with `check_shard_freshness()` in TickDataHandler

  **Current** (tick_data_handler.py L87-98):

  ```python
  index = read_availability_index(bucket)
  if not index.empty:
      self._completed_dates = set(index["date"].unique())
  ```

  Then in `process()` (L108):

  ```python
  if not self._force and date in self._completed_dates:
      logger.info("Skipping already-complete date...")
      return {}
  ```

  **Target**: Port instruments-service pattern (orchestrator.py L750-763):

  ```python
  is_fresh, stale, missing = check_shard_freshness(
      bucket=bucket,
      date=date,
      service_name="market-tick-data-service",
      expected_venues=active_venues,
      max_age_hours=freshness_max_age,
  )
  if is_fresh:
      logger.info("SKIP date=%s: all venues fresh in manifest")
      return {}
  ```

  Changes needed:
  1. Remove `self._completed_dates` set from TickDataHandler
  2. Remove `read_availability_index()` from preflight (no longer needed for skip)
  3. Move skip check into `process()` — call `check_shard_freshness()` per date
  4. Add historical date optimization: `max_age_hours=0.0` for dates >7 days ago
  5. Pass `expected_venues` from `get_venues_for_categories()` filtered by availability
  6. When `stale` or `missing` venues returned, only process those venues (not all)
  7. Import `check_shard_freshness` from UTL

  This gives us: schema version checking, time-based staleness, per-venue completeness, and the 60s in-process cache TTL
  (skip without GCS call on consecutive dates).

- [ ] [AGENT] P1. Add partial-venue processing support to `process_ticks()`

  When `check_shard_freshness()` returns `stale` + `missing` venues, pass only those to `process_ticks()` via the
  `venues` parameter (already supported). This avoids re-downloading all venues when only 1-2 failed on a previous run.

### 2B. Schema validation pre-write

- [ ] [AGENT] P0. Activate DomainValidationService in PartitionedTickWriter or orchestrator

  `_DOMAIN_VALIDATOR = DomainValidationService("market_data")` is already instantiated at module level (orchestrator.py
  L56) but never called.

  Add validation in `PartitionedTickWriter.write_chunk()` before routing to writers:
  1. Validate required columns exist for the data_type (e.g. trades needs timestamp, price, amount, side;
     book_snapshot_5 needs bids, asks arrays)
  2. Validate data types (timestamp is datetime, price is numeric, etc.)
  3. Validate venue is in UAC VENUES_BY_CATEGORY
  4. Log validation failures as errors but don't block write (advisory first iteration)

  The validation schema per data_type should come from UAC. If UAC doesn't have tick data schemas yet, define the column
  requirements as a dict in the orchestrator (MTDS-internal, not in UAC — tick data schemas are MTDS's domain).

  **Minimal v1**: validate that the DataFrame is non-empty, has a `timestamp` column, and the data_type is valid for the
  venue per `validate_data_type_for_venue()`. Reject writes with wrong data_type for venue category (e.g.
  `options_chain` for a DeFi venue).

- [ ] [AGENT] P1. Add per-category tick data column schemas

  Define expected columns per data_type in MTDS (not UAC — these are internal):

  ```python
  _TICK_SCHEMA: dict[str, list[str]] = {
      "trades": ["timestamp", "price", "amount"],
      "book_snapshot_5": ["timestamp", "bids", "asks"],
      "derivative_ticker": ["timestamp", "funding_rate"],
      "liquidations": ["timestamp", "price", "amount", "side"],
      "options_chain": ["timestamp", "symbol"],
      "futures_chain": ["timestamp", "symbol"],
      "ohlcv_1m": ["timestamp", "open", "high", "low", "close"],
      "tbbo": ["timestamp", "bid_price", "ask_price"],
      "dex_swaps": ["timestamp", "price", "amount"],
      "odds": ["timestamp"],
      "prediction_trades": ["timestamp", "price", "amount"],
  }
  ```

  Validate before write. Missing columns → log error, still write (don't block pipeline).

### 2C. Split manifest data_type field

- [ ] [AGENT] P0. Write raw data_type (not combined "itype/dt") to manifest

  **Current** (orchestrator.py L504-511):

  ```python
  for (venue_name, partition_key), rows in shard_counts.items():
      writer_manifest.add(
          ...
          data_type=partition_key,  # "perpetual/trades" — combined string
      )
  ```

  **Target**: Write only the data_type portion:

  ```python
  for (venue_name, partition_key), rows in shard_counts.items():
      # partition_key = "instrument_type/data_type"
      parts = partition_key.split("/", 1)
      dt = parts[1] if len(parts) > 1 else partition_key
      writer_manifest.add(
          ...
          data_type=dt,  # "trades", "options_chain", etc.
      )
  ```

  Also update `shard_counts` tracking to use `(venue, instrument_type, data_type)` triple instead of
  `(venue, "itype/dt")` combined string. This makes the manifest parseable by deployment UI without string splitting.

  **Migration**: existing manifest entries with "itype/dt" format will coexist with new "dt-only" entries. The dedup key
  in ManifestWriter is (date, venue, data_type, service_name) — new entries will naturally replace old ones on next
  write.

### 2D. Adapter epoch versioning

- [ ] [AGENT] P2. Add `_VENUE_ADAPTER_EPOCH` dict to MTDS orchestrator

  Same pattern as instruments-service (orchestrator.py L192-230). Start with empty dict — bump epochs when adapter logic
  changes. Wire into skip logic: manifest entries before epoch are ignored by `check_shard_freshness()` (via
  schema_version bump or custom filter).

  For v1, just add the dict and the `_get_venue_epoch()` helper. Integration with check_shard_freshness comes when
  needed (adapter change).

**Success criteria Phase 2:**

- `cd market-tick-data-service && bash scripts/quality-gates.sh` passes
- `--force` still works (bypasses all skip logic)
- Default (no --force) skips dates that are fully fresh
- Partial failure on day X → next run only retries failed venues for day X
- Schema validation logs errors for malformed data (doesn't block writes)
- Manifest `data_type` field contains raw data type names

---

## Phase 3 — Deployment UI + UTL (PARALLEL)

### 3A. Deployment UI data_type dimension

- [ ] [AGENT] P0. Add data_type sub-breakdown under each venue in `_build_venue_breakdown()`

  **Current**: deployment-api shows `venue → {dates_found, dates_expected, completion_pct}`

  **Target**: deployment-api shows `venue → {data_types: {dt → {dates_found, dates_expected}}, ...}`

  In `data_status_service.py._build_venue_breakdown()`:
  1. Group filtered index by (venue, data_type)
  2. For each venue, build a `data_types` dict with per-data-type stats
  3. Use `get_expected_data_types_for_venue(venue)` from UAC to know which data types should exist — missing data types
     show as 0% complete
  4. Use `get_venue_data_type_start_date(venue, dt)` for per-data-type date ranges

  The venue-level stats remain (sum of data_type stats). The data_types dict is nested inside each venue entry for
  drill-down.

- [ ] [AGENT] P1. Update `_build_manifest_category()` to aggregate data_type dimension

  Category-level completion should account for data_type expectations. A venue that has trades but is missing
  book_snapshot_5 should not show 100%.

### 3B. UTL check_shard_freshness — audit for data_type awareness

- [ ] [AGENT] P1. Audit `check_shard_freshness()` for data_type filtering

  Current implementation filters by (date, service_name, venue) but NOT data_type. If MTDS writes separate manifest
  entries per data_type (from Phase 2C), the freshness check may need to also filter by data_type to avoid false-fresh
  when only some data types are present.

  Options: a) Add optional `expected_data_types` param to `check_shard_freshness()` b) Keep venue-level check but
  validate data_type completeness separately in MTDS c) No change needed if manifest dedup key handles it

  Instruments-service writes one manifest entry per (date, venue) — no data_type split. MTDS will write one entry per
  (date, venue, data_type). The freshness check counts venues — if MTDS writes 3 entries for BINANCE-SPOT (trades,
  book_snapshot_5, derivative_ticker), the venue still appears once in the unique set. So current
  `check_shard_freshness()` should still work for the "are all venues present" check.

  **Likely outcome**: Option (b) — MTDS checks venue-level freshness first (fast skip for fully complete dates), then
  does data_type completeness check internally for partial dates. No UTL change needed.

**Success criteria Phase 3:**

- `cd deployment-api && bash scripts/quality-gates.sh` passes
- Deployment UI data status page shows data_type breakdown under each venue
- Venues with missing data types show correct completion percentage
- Gas fees still display correctly (bucket override still works)

---

## Phase 4 — Integration Validation

- [ ] [AGENT] P0. Run QG on all 4 affected repos

  ```bash
  cd unified-api-contracts && bash scripts/quality-gates.sh
  cd market-tick-data-service && bash scripts/quality-gates.sh
  cd deployment-api && bash scripts/quality-gates.sh
  cd unified-trading-library && bash scripts/quality-gates.sh
  ```

- [ ] [AGENT] P1. Verify end-to-end: MTDS writes → manifest → deployment UI reads
  1. Run MTDS for a single date with `--force` to generate fresh manifest entries
  2. Check manifest parquet: `data_type` field should contain raw data type names
  3. Load deployment UI data status → should show data_type breakdown under venues
  4. Run MTDS again without `--force` → should skip (check_shard_freshness returns fresh)
  5. Delete one venue's data for a date → re-run → should only fetch that venue

**Success criteria Phase 4:**

- All 4 repos pass quality-gates.sh
- Manifest writes contain clean data_type values
- Deployment UI shows multi-dimensional data (category → venue → data_type)
- Smart skip works: fresh dates skip, partial dates retry only missing venues
