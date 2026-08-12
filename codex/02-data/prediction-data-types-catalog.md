---
doc_type: codex-ssot
title: Prediction Data Types Catalog
summary: >-
  Prediction data-types catalog SSOT — the 4 MTDS prediction data_types (trades / book_snapshot_5 /
  prediction_canonical_question_group / market_lifecycle), their CLI ops, sources (polymarket_clob,
  polymarket_gamma_api, kalshi_*), shard keys and schemas; the venue-vs-source invariant (never collapse
  Polymarket-vs-Kalshi into a source merge), event_driven coverage semantics, and the MARKET_LIFECYCLE dual-casing.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: [prediction, mtds, data-pipeline, manifest, instruments, canonicalisation]
related:
  [
    /codex/02-data/prediction-schema-paths.md,
    /codex/02-data/mtds-data-source-coverage-matrix.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/contracts-scope-and-layout.md,
  ]
created: 2026-05-24
authoritative_for: [MTDS prediction data_type catalog, prediction venue-vs-source provenance invariant]
referenced_by:
  [/codex/02-data/README.md, /codex/02-data/prediction-perps-sourcing.md, /codex/02-data/prediction-schema-paths.md]
owner:
last_reviewed: 2026-08-12
code_refs:
---

# Prediction Data Types Catalog

> SSOT for all MTDS Prediction market data type definitions, sources, shard keys, and implementation status. Last
> updated: 2026-08-12 (book_snapshot_5 re-add corrected — see § "Legacy naming migration").

## Overview

MTDS collects Prediction market data in 4 distinct data types across trade execution, top-of-book depth, canonical
question grouping, and market lifecycle domains. Each data type maps to one or more MTDS CLI operations
(`--operation collect-<type>`), one or more venues (Polymarket, Kalshi), and a canonical GCS path under the Prediction
tick-data bucket.

> **Crypto perps (Kalshi-Perp / Polymarket-Perp)** are a SEPARATE `cefi` product (regulated crypto perpetual futures),
> NOT prediction YES/NO markets — sourcing SSOT: [`prediction-perps-sourcing.md`](./prediction-perps-sourcing.md).

The 4 data types are:

- `trades` — individual trade executions on prediction markets
- `book_snapshot_5` — top-5 order-book depth snapshot (instrument-day grain, same grain as `trades`); RE-ADDED
  2026-06-23 once both venues started emitting it (LIVE via `polymarket_clob_ws`/`kalshi_clob_ws`, BATCH via
  `polymarket_adapter` REST `/book`) — see § "Legacy data type retirement" below for the earlier RETIRED→re-added
  history, and `/plans/active/prediction_live_clob_depth_capture_2026_07_24.md` for the full capture-pipeline detail
- `prediction_canonical_question_group` — cluster-grain canonical question group (Plan A; primary current production
  type)
- `market_lifecycle` / `MARKET_LIFECYCLE` — lifecycle events (instruments-service writes `MARKET_LIFECYCLE` uppercase;
  MTDS/MDPS use `market_lifecycle` lowercase)

**Critical naming note**: `market_lifecycle` (lowercase) is the UAC canonical name for MTDS/MDPS use. `MARKET_LIFECYCLE`
(uppercase) is the instruments-service internal designation. Both refer to the same concept. The dual-casing is a known
asymmetry documented in `contracts-scope-and-layout.md` § "MARKET_LIFECYCLE dual-casing".

**Coverage semantics**: PREDICTION uses `event_driven` coverage (`COVERAGE_SEMANTICS["PREDICTION"] = "event_driven"`) —
shards-weighted `capture_coverage_pct` understates real coverage because the denominator assumes every (conditionId ×
day) combo should trade. Aggregator uses `attempt_coverage_pct` for the displayed %.

**Legacy naming migration (2026-04-19)**: Prior to Plan A, MTDS used per-conditionId shards with data_type ∈
{`prediction_trades`, `prediction_book_snapshot`, `prediction_market_metadata`}. These were RETIRED —
`prediction_book_snapshot` and `prediction_market_metadata` removed from `_PER_INSTRUMENT_SHARD_DATA_TYPES`
(UAC@7511207a). `prediction_trades` folded into canonical `trades`. **`book_snapshot_5` (the canonical-named
successor to the retired `prediction_book_snapshot`) was RE-ADDED 2026-06-23** once both venues started emitting it
(`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:357-372`) — UAC now: `trades` +
`book_snapshot_5` + `prediction_canonical_question_group` + `market_lifecycle`/`MARKET_LIFECYCLE`.

### Source vs Venue invariant (HARD — both are true, never collapsed)

> Codifies the prediction `source`-provenance invariant (`data_source_provenance_all_asset_groups_2026_06_01.md` CODEX
> P2, slot-5 2026-06-04). Two distinct axes that are routinely confused:

- **`venue`** = WHERE the market trades — `POLYMARKET`, `KALSHI`. Cross-venue **price dispersion** (Polymarket-vs-Kalshi
  on the same canonical question) is a **feature-layer** concern, computed downstream from two captured venue cells. It
  is **NOT** a manifest `source` merge — each venue stays its own `(asset_group=prediction, venue, …)` shard. When
  Kalshi goes live it is a **venue addition** (a new shard-axis value), not a new source for Polymarket's cells.
- **`source`** = the DATA-PROVIDER API a cell's bytes came from — `polymarket_clob` (trades / book / the
  `prediction_canonical_question_group` bundle), `polymarket_gamma_api` (`MARKET_LIFECYCLE`), `kalshi_*` (Kalshi cells).
  Every captured prediction cell stamps its own `source` (swap-resilience: a future Polymarket data-provider change
  stays distinguishable). Single-source today → the UTL writer auto-stamps via `default_source`
  (`source_required=False`, no `MissingSourceError`); UAC `SOURCE_PRIORITY` carries the prediction pairs.

So a Polymarket `MARKET_LIFECYCLE` cell is `venue=POLYMARKET, source=polymarket_gamma_api`, while a Polymarket `trades`
cell is `venue=POLYMARKET, source=polymarket_clob` — **same venue, different source**. `derive_pipeline_mode_for_row`
honors this per-data_type (the blanket `POLYMARKET → CLOB` venue override was removed — UTL@01ca49ea, slot-4 2026-06-04
— so gamma-sourced lifecycle resolves gamma, not CLOB). Do NOT treat Kalshi-vs-Polymarket as a
`select_primary_available_source()` union (that resolver is for the SAME logical cell arriving from >1 provider, e.g.
tradfi databento/massive — not two venues).

### GCS Path Convention

Canonical (v9, post-`prediction_manifest_canonicalisation` migration) — `pipeline_mode=` is a hive partition LEFT of
`asset_group=` (path==manifest invariant; inserted by the live raw writer `orchestrator.py:~1005`, the migrator, and the
manifest rebuild via the SAME `derive_pipeline_mode_for_row` SSOT):

```
{resolved-prediction-tick-bucket}/raw_tick_data/by_date/day={date}/pipeline_mode={mode}/
  asset_group=prediction/venue={VENUE}/instrument_type={IT}/data_type={data_type}/{shard_key}.parquet
```

`{mode}` = `batch_polymarket_clob` (trades / book / the `prediction_canonical_question_group` bundle) or
`batch_polymarket_gamma_api` (`MARKET_LIFECYCLE`) — derived per-data_type, never venue-blanket. The migration-window
readers dual-probe BOTH the legacy (no-`pipeline_mode=`) and canonical shapes until the global Phase-8 cutover removes
the fallback (~2026-06-15, per `/codex/02-data/pipeline-mode-partition.md`).

For `prediction_canonical_question_group` (cluster-grain): shard is per `canonical_question_group`, not per
`conditionId`. `conditionId` is a row-level column + cluster validation key. The raw OBJECTS stay per-cid
(`…/data_type=trades/{conditionId}.parquet`); the cqg bundle is a **manifest-only** row (`record_captured_from_counts`
with `observed_clusters={conditionId: rows}`) — there is no `canonical_question_group=` object path segment (verified
E6b, prediction plan).

Bucket name is resolved via
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud=..., kind="market-data-tick-prediction", env=...)`
(the FLAT prediction kind → `market-data-tick-pred-{env_short}-{pid}`; NOT the per-AG
`kind="market-data", asset_group="prediction"` map, which raises `BucketNamingError`) per CLAUDE.md § "Bucket-name SSOT"
— never inline `gs://...` / `s3://...` (QG STEP 5.69 ratchet enforces).

### Instrument Type Mapping

| instrument_type     | Data types                                                    |
| ------------------- | ------------------------------------------------------------- |
| `prediction_market` | trades, book_snapshot_5, prediction_canonical_question_group, market_lifecycle |

---

## Data Type Catalog

### 1. trades

| Field               | Value                                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-trades` (prediction_trades_handler)                                                            |
| **Sources**         | Polymarket CLOB API (`clob.polymarket.com`); Kalshi REST API (`api.elections.kalshi.com/trade-api/v2/`) |
| **Shard key**       | venue × conditionId × date (per-instrument shard)                                                       |
| **Instrument type** | `prediction_market`                                                                                     |
| **Status**          | Production                                                                                              |
| **Schema fields**   | symbol, ts_event, venue, condition_id, trade_id, price, size, side, maker_order_id, taker_order_id      |
| **Requires**        | Polymarket: no auth for public CLOB; Kalshi: `kalshi-api-key` (Secret Manager)                          |

Individual trade executions on prediction markets. One row per matched trade. `price` ∈ [0, 1] representing implied
probability (Polymarket) or [0, 100] (Kalshi cents). `side` ∈ {`YES`, `NO`}. Shard is per-conditionId per day
(per-instrument semantics — `is_per_instrument_shard_data_type("trades") = True`). Coverage is `event_driven` —
zero-trade days on inactive conditions emit `record_empty(reason=SOURCE_RETURNED_ZERO)`.

---

### 2. prediction_canonical_question_group

| Field               | Value                                                                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-canonical-questions` (prediction_canonical_question_handler)                                                                       |
| **Sources**         | Polymarket CLOB API (all markets aggregated); Kalshi REST API (all markets)                                                                 |
| **Shard key**       | venue × canonical_question_group × date (cluster-grain shard)                                                                               |
| **Instrument type** | `prediction_market`                                                                                                                         |
| **Status**          | Production (Plan A — 2026-04-19)                                                                                                            |
| **Schema fields**   | symbol, ts_event, venue, canonical_question_group, condition_id, question, price, volume_24h, open_interest, resolution_date, market_status |
| **NEEDS_CANDLE**    | False (pass-through — cluster-validated snapshot, no MDPS candle processing)                                                                |

Cluster-grain canonical question group snapshot. One row per (canonical_question_group, conditionId, day). Multiple
conditionIds sharing the same canonical question (e.g., "Will ETH reach $5,000 in 2026?" on Polymarket and Kalshi) are
grouped under one canonical_question_group shard. Cluster validation MANDATORY: `cluster_extractor=market_id`
(conditionId) — ensures all markets within a canonical_question_group are present in the shard.

**Grain rationale**: Per-conditionId shards would create ~10,000+ shards/day (one per active Polymarket market).
Canonical question grouping reduces to ~50–200 canonical groups/day covering meaningful question families. Avoids
manifest-row explosion while preserving full per-market_id data as row-level columns.

**Canonical question group taxonomy** (registered in instruments-service):

- Asset price targets (e.g., `BTC_2026_100K`, `ETH_2026_5K`)
- Election/political outcomes (`US_ELECTION_2026_MIDTERMS`, `FED_RATE_DECISION_YYYY_MM`)
- Macro events (`NFP_YYYY_MM`, `CPI_YYYY_MM`)
- Sports outcomes mapped to Prediction (cross-domain canonical groups)

---

### 3. market_lifecycle

| Field               | Value                                                                                                                                   |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI operation**   | `collect-market-lifecycle` (market_lifecycle_handler)                                                                                   |
| **Sources**         | Polymarket CLOB API (`/markets`); Kalshi REST API (`/markets` + `/series`); instruments-service internal                                |
| **Shard key**       | venue × date (venue-level snapshot — all markets per day)                                                                               |
| **Instrument type** | `prediction_market`                                                                                                                     |
| **Status**          | Production                                                                                                                              |
| **NEEDS_CANDLE**    | False (pass-through — lifecycle events; no MDPS processing)                                                                             |
| **Schema fields**   | symbol, ts_event, venue, condition_id, canonical_question_group, event_type, question, resolution_date, resolution_value, market_status |

Market lifecycle events. One row per lifecycle transition per market. `event_type` ∈ {`MARKET_CREATED`,
`MARKET_RESOLVED`, `MARKET_CLOSED`, `MARKET_CANCELLED`, `TRADING_RESUMED`}. `resolution_value` ∈ {`YES`, `NO`, `VOID`,
null (unresolved)}.

For instruments-service internal designation: uses `MARKET_LIFECYCLE` (uppercase) as the data_type string — this is the
known dual-casing asymmetry; MTDS/MDPS always use lowercase `market_lifecycle`. Both write to the same GCS data_type
path segment `data_type=market_lifecycle` (lowercase, hive-canonical). Code that reads instruments-service output should
normalize to lowercase before comparison.

Used by instruments-service to maintain the canonical prediction-market universe (active conditions, resolution dates,
outcomes). The downstream consumer is instruments-service's prediction_market aggregator, which builds the UAC
`canonical_question_group` registry from these events.

---

## Venue Coverage Matrix

| Venue      | Data Types                                                    | Status     | Notes                                                                               |
| ---------- | ------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------- |
| POLYMARKET | trades, book_snapshot_5, prediction_canonical_question_group, market_lifecycle | Production | Binary markets (YES/NO outcomes); CLOB; prices ∈ [0, 1]                             |
| KALSHI     | trades, book_snapshot_5, prediction_canonical_question_group, market_lifecycle | Production | Binary + categorical; REST API; prices in cents [0, 100]; requires `kalshi-api-key` |

---

## Coverage Axes

| data_type                             | Coverage axis                                    | Expected shards (per day)                               | record_empty expected                                                          |
| ------------------------------------- | ------------------------------------------------ | ------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `trades`                              | per-venue × per-conditionId × daily              | venue × active conditions                               | Yes — zero-trade day on inactive condition = `SOURCE_RETURNED_ZERO`            |
| `book_snapshot_5`                     | per-venue × per-conditionId × daily              | venue × active conditions                                | Yes — same instrument-day grain as `trades`                                    |
| `prediction_canonical_question_group` | per-venue × per-canonical_question_group × daily | venue × canonical groups (instruments-service registry) | Yes — no markets in group = `empty_confirmed`                                  |
| `market_lifecycle`                    | per-venue × daily                                | venue × 1 shard/day                                     | Yes — no lifecycle events = `empty_confirmed` (markets stable, no transitions) |

---

## Implementation Notes

### Legacy data type retirement (2026-04-19)

| Old (retired)                | New canonical      | Notes                                                  |
| ---------------------------- | ------------------ | ------------------------------------------------------ |
| `prediction_trades`          | `trades`           | Folded into unified trades type                        |
| `prediction_book_snapshot`   | `book_snapshot_5`  | RETIRED 2026-04-19, then **RE-ADDED 2026-06-23** as canonical `book_snapshot_5` once both venues started emitting depth (see § "Legacy naming migration" above) — no longer "no replacement" |
| `prediction_market_metadata` | `market_lifecycle` | Superseded by lifecycle-event model                    |

Retired types removed from `_PER_INSTRUMENT_SHARD_DATA_TYPES` at UAC@7511207a. Any manifest rows with old data_type
strings are re-classified by phantom-reconcile script
(`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`).

### MARKET_LIFECYCLE dual-casing

`market_lifecycle` (lowercase) is the UAC canonical for `DATA_TYPES_BY_ASSET_GROUP["prediction"]` and for all MTDS/MDPS
code paths. `MARKET_LIFECYCLE` (uppercase) appears as an internal instruments-service designator, inherited from early
instruments-service code before the vocabulary standardization. Both write to the same GCS data_type path segment
`data_type=market_lifecycle` (lowercase, hive-canonical). Code that reads instruments-service output should normalize to
lowercase before comparison. The asymmetry is documented in `contracts-scope-and-layout.md` § "MARKET_LIFECYCLE
dual-casing".

### NEEDS_CANDLE_PROCESSING

**CORRECTED 2026-07-27** (`mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Update 6 + the KALSHI-mapping todo,
operator-ruled): this section previously claimed a prediction-specific `False` override for `trades` — that claim was
**stale/wrong**, not a description of real running code.
`unified_api_contracts.registry.market_data_categories. NEEDS_CANDLE_PROCESSING` is a **flat, data_type-keyed dict with
no asset_group axis at all**; `"trades": True` applies uniformly to every asset_group, and the dict's own adjacent
comment reads "Prediction — uses canonical 'trades' / 'book_snapshot_5' (same keys as CeFi)" — i.e. the code's intent
has always been to share CeFi's `True` value, not override it. `needs_candle_processing()` is called with `data_type`
only (never `asset_group`), so no code path could apply a prediction-specific exception even if one were intended.

- **True**: `trades` — uniform across every asset_group (CeFi/TradFi/DeFi/prediction), including prediction. MDPS DOES
  attempt candle derivation for prediction `trades` (Polymarket has worked in production since 2026-01; the KALSHI
  schema mapping was the gap — see `PredictionTradesAdapter`).
- **False (unchanged, not part of the corrected claim)**: `market_lifecycle` — pass-through lifecycle events, no MDPS
  candle adapter registered for it.

Residual, NOT independently re-verified in this correction pass: `prediction_canonical_question_group` is likewise
absent from the flat `NEEDS_CANDLE_PROCESSING` dict, which means `needs_candle_processing()`'s documented "unknown data
types default to `True`" fallback applies to it too (same mechanism that was silently wrong for `trades`) — but MDPS has
no `CandleAdapterRegistry` entry for `(PREDICTION, "prediction_canonical_question_group")` either, so this doc no longer
asserts `False` for it. Whether that live behavior is correct (harmlessly no-adapter-found / skipped) or a second,
smaller instance of the same class of drift was not investigated here — flagging rather than guessing.

### API Key Requirements

| Handler                                            | Secret Manager key | Notes                             |
| -------------------------------------------------- | ------------------ | --------------------------------- |
| prediction_trades — Polymarket                     | None               | Public CLOB API; no auth required |
| prediction_trades — Kalshi                         | `kalshi-api-key`   | Required for trade history access |
| prediction_canonical_question_handler — Polymarket | None               | Public                            |
| prediction_canonical_question_handler — Kalshi     | `kalshi-api-key`   | Required                          |
| market_lifecycle_handler — Polymarket              | None               | Public                            |
| market_lifecycle_handler — Kalshi                  | `kalshi-api-key`   | Required                          |

### event_driven Coverage Semantics

Prediction uses `event_driven` coverage rather than the time-series `continuous` semantics used by CeFi/TradFi. The core
issue is the denominator: not every conditionId trades every day. A market for "Will BTC reach $150K before 2027-01-01?"
may have no trades on quiet days — this is expected behavior, not a data failure. Using `capture_coverage_pct` (which
divides captured shards by all (conditionId × day) combos in the expected set) would systematically understate real
coverage because thousands of inactive conditions contribute to the denominator without any obligation to produce data.

The aggregator therefore uses `attempt_coverage_pct` as the displayed metric for prediction: the ratio of
`(captured + empty_confirmed)` over `(captured + empty_confirmed + attempted_failed)`. Zero-trade days on inactive
conditions emit `record_empty(reason=SOURCE_RETURNED_ZERO)` and count as successful attempts, not failures.

---

## Related Documents

- `/codex/02-data/prediction-schema-paths.md` — GCS path conventions, shard atom definition, canonical question group
  taxonomy
- `/codex/02-data/mtds-data-source-coverage-matrix.md` — full MTDS source coverage
- `/codex/02-data/per-asset-group-bucket-layouts.md` — GCS bucket layout
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest v5+ honest-absence semantics
- `/codex/02-data/contracts-scope-and-layout.md` — UAC layout + MARKET_LIFECYCLE dual-casing note
