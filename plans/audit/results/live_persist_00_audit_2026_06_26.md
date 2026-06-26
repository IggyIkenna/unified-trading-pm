---
type: audit-result
title: Live-persist 00 — pre-audit live transport/persistence + SINK_MATRIX seed
epic: batch_live_symmetry_master
instructions_ref: plans/active/live_persist_00_audit_sink_matrix_2026_06_26.md
auditor: slot-0 [human-planning]
date: "2026-06-26"
status: complete
scope:
  8 repos — MTDS / UAC / UTL / MDPS / features-service / strategy-service / ml-service / execution-service (read-only)
method: direct file reads + parallel sub-agent grep per repo
---

# Live-persist 00 — Pre-Audit: Live Transport/Persistence + SINK_MATRIX Seed

## 1. Current Live Transport + Persistence — End-to-End Map

### 1.1 Transport Layer

**Current broker: Redis Streams** (NOT Pub/Sub) for the MTDS→MDPS→features cascade.

| Leg                      | Producer                                 | Consumer                               | Stream name                                                | Event type                           |
| ------------------------ | ---------------------------------------- | -------------------------------------- | ---------------------------------------------------------- | ------------------------------------ |
| MTDS → MDPS              | MTDS `websocket_runner.py:78-80`         | MDPS `live_aggregator.py`              | `streaming.{asset_group}.candle_boundary_crossed`          | `CandleBoundaryCrossedEvent`         |
| MTDS → consumers         | MTDS `websocket_runner.py:85`            | IS watchers                            | `streaming.{asset_group}.instrument_cache_refresh_trigger` | `InstrumentCacheRefreshTriggerEvent` |
| MDPS → features          | MDPS `live_aggregator.py`                | features `live_runner.py:134,156`      | `streaming.{asset_group}.candle_computed`                  | `CandleComputedEvent`                |
| features → cross-cutting | features `live_cross_cutting.py:132-137` | features cross-cutting                 | `streaming.{asset_group}.features_computed`                | `FeaturesComputedEvent`              |
| ml → strategy            | ml `cascade_prediction_publisher.py:25`  | strategy `cascade_subscriber.py:30`    | `cascade_predictions` (Pub/Sub, not Redis)                 | `CascadePredictionEvent`             |
| strategy marks           | MDPS/MTDS callback                       | strategy `colocated_engine.py:156-162` | shared memory (`/dev/shm`)                                 | `MarkSnapshot`                       |

**Key observation**: strategy-service and ml-service already use Pub/Sub natively; MTDS/MDPS/features-service use Redis
Streams. The plan unifies ALL on Pub/Sub.

### 1.2 Persistence Layer

**Per-window GCS overwrite (THE PROBLEM)**:

| Service                    | Write site                                                    | Path pattern                                                                                         | Notes                                                |
| -------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| MTDS                       | `websocket_runner.py:155-181` `LiveWebsocketTickSink.flush()` | `raw_tick_data/by_date/day={D}/pipeline_mode={live_mode}/asset_group={ag}/…/{instrument_id}.parquet` | **Overwrites on every window close** — 1-min windows |
| MTDS backfill              | `backfill_runner.py:223`                                      | Same path as live                                                                                    | Idempotent overwrite                                 |
| execution-service (live)   | `engine/modes/live/data_sink.py:74-115`                       | `results/{venue}/{date}/{instruction_id}_{timestamp}.json`                                           | JSON, async queue                                    |
| execution-service (report) | `results/save_operations.py:749`                              | `execution_fills/date={D}/mode={mode}/fills.parquet`                                                 | Parquet, canonical build_path                        |

**Hot-path GCS READ (THE RACE)**:

| Service | Read site                                       | What it reads                                 | Why it's a problem                                        |
| ------- | ----------------------------------------------- | --------------------------------------------- | --------------------------------------------------------- |
| MDPS    | `live_aggregator.py:316-352` `_MDPSTickFetcher` | `live_tick_blob_path(event)` → GCS per window | Reads from the same path MTDS overwrites → race condition |

### 1.3 Existing Event Shapes in UAC (to be generalised)

`unified_api_contracts/events/streaming.py`:

- `CandleBoundaryCrossedEvent` — MTDS window close signal
- `CandleComputedEvent` — MDPS computed-bar signal
- `FeaturesComputedEvent` — features-service output signal
- `InstrumentCacheRefreshTriggerEvent` — IS catalog refresh

All are Redis-stream-native; none carry `retention_class`, `schema_version`, or a `payload|pointer` discriminator. Plan
01 generalises these into the canonical persist envelope.

### 1.4 UTL Streaming Primitives

`unified_trading_library/streaming/`:

- `StreamPublisher` / `StreamConsumerGroup` — Redis Streams XADD/XREADGROUP
- `MDPSStreamingAggregator` / `_MDPSTickFetcher` / `TickFetcher` protocol — the hot-path GCS read abstraction
- `ReplayPublisher` / `ReplayWatermarkKV` — replay helpers (smooth handoff live→replay, not batch-equivalence)

No Pub/Sub adapter exists yet in UTL streaming. Plan 02 adds the `publish()`/`read()` facade.

---

## 2. SINK_MATRIX Seed (Full Per-Shard Classification)

**Notation**: `R` = REPRODUCIBLE, `SO` = STREAM_ONLY; `hot` = hot-path sub subscriptions; `warm` = Cloud Storage
subscription; `table` = BQ external table.

### 2.1 MTDS Shards (raw ticks — windowed, NOT raw L2/L3/MBO firehose)

> **Finding D3**: MTDS does NOT produce a true L2/L3/MBO firehose. All ticks are windowed (1-min UTCAlignedScheduler).
> `book_snapshot_5` = 5-level depth snapshot (not raw order flow). No firehose shards → `table: true` for all MTDS
> data_types by default.

| asset_group | data_type                  | retention_class | hot | warm | table | cold_lifecycle | Notes                        |
| ----------- | -------------------------- | --------------- | --- | ---- | ----- | -------------- | ---------------------------- |
| cefi        | trades                     | R               | ✓   | ✓    | true  | 90d TTL        | Databento backfill available |
| cefi        | book_snapshot_5            | R               | ✓   | ✓    | true  | 30d TTL        | 5-level depth, re-fetchable  |
| cefi        | derivative_ticker          | R               | ✓   | ✓    | true  | 90d TTL        | Pricing data                 |
| cefi        | liquidations               | R               | ✓   | ✓    | true  | 180d TTL       | Exchange events              |
| defi        | trades                     | R               | ✓   | ✓    | true  | 90d TTL        | Re-fetchable on-chain        |
| defi        | book_snapshot_5            | R               | ✓   | ✓    | true  | 30d TTL        | 5-level depth                |
| defi        | liquidations               | R               | ✓   | ✓    | true  | 180d TTL       | On-chain events              |
| defi        | lst_rates                  | R               | ✓   | ✓    | true  | 365d TTL       | Re-fetchable on-chain        |
| defi        | lending_indices            | R               | ✓   | ✓    | true  | 365d TTL       | Re-fetchable                 |
| defi        | dex_pools                  | R               | ✓   | ✓    | true  | 365d TTL       | On-chain                     |
| defi        | dex_swaps                  | R               | ✓   | ✓    | true  | 90d TTL        | On-chain                     |
| defi        | arbitrage_price_dispersion | R               | ✓   | ✓    | true  | 30d TTL        | Derived                      |
| tradfi      | trades                     | R               | ✓   | ✓    | true  | 90d TTL        | Databento backfill           |
| sports      | trades                     | R               | ✓   | ✓    | true  | 30d TTL        | Exchange data                |
| prediction  | trades                     | R               | ✓   | ✓    | true  | 30d TTL        | Exchange data                |
| prediction  | book_snapshot              | R               | ✓   | ✓    | true  | 14d TTL        | Depth data                   |
| prediction  | book_snapshot_5            | R               | ✓   | ✓    | true  | 14d TTL        | 5-level depth                |

### 2.2 MDPS Shards (computed candles)

| asset_group | data_type | retention_class | hot | warm | table | cold_lifecycle | Notes                                  |
| ----------- | --------- | --------------- | --- | ---- | ----- | -------------- | -------------------------------------- |
| all         | candle    | R               | ✓   | ✓    | true  | 365d TTL       | Re-derivable from MTDS ticks + formula |

(all = cefi, defi, tradfi, sports, prediction, commodity)

### 2.3 Features-Service Shards

All features shards are REPRODUCIBLE (pinned `formula_version` per CLAUDE.md features rule).

| asset_group | data_type               | retention_class | hot | warm | table | cold_lifecycle |
| ----------- | ----------------------- | --------------- | --- | ---- | ----- | -------------- |
| all         | tf_momentum_alignment   | R               | ✓   | ✓    | true  | 180d TTL       |
| all         | tf_structure_context    | R               | ✓   | ✓    | true  | 180d TTL       |
| all         | tf_vol_compression      | R               | ✓   | ✓    | true  | 180d TTL       |
| defi/cefi   | regime_detection        | R               | ✓   | ✓    | true  | 180d TTL       |
| defi/cefi   | cross_venue_spreads     | R               | ✓   | ✓    | true  | 180d TTL       |
| defi/cefi   | realized_implied_vol    | R               | ✓   | ✓    | true  | 180d TTL       |
| defi/cefi   | cross_asset_correlation | R               | ✓   | ✓    | true  | 180d TTL       |
| defi/cefi   | cme_gap                 | R               | ✓   | ✓    | true  | 180d TTL       |
| defi/cefi   | book_depth_bands        | R               | ✓   | ✓    | true  | 90d TTL        |
| defi/cefi   | liquidity_walls         | R               | ✓   | ✓    | true  | 90d TTL        |
| defi/cefi   | liquidation_clusters    | R               | ✓   | ✓    | true  | 90d TTL        |
| defi/cefi   | flow_interaction        | R               | ✓   | ✓    | true  | 90d TTL        |
| defi/cefi   | composite_sr            | R               | ✓   | ✓    | true  | 180d TTL       |
| cefi/defi   | technical_indicators    | R               | ✓   | ✓    | true  | 180d TTL       |
| cefi/defi   | moving_averages         | R               | ✓   | ✓    | true  | 180d TTL       |
| cefi/defi   | microstructure          | R               | ✓   | ✓    | true  | 90d TTL        |
| defi        | options_iv              | R               | ✓   | ✓    | true  | 180d TTL       |
| defi        | options_term_structure  | R               | ✓   | ✓    | true  | 180d TTL       |
| defi        | futures_basis           | R               | ✓   | ✓    | true  | 180d TTL       |
| defi        | futures_term_structure  | R               | ✓   | ✓    | true  | 180d TTL       |
| all         | time_features           | R               | ✓   | ✓    | true  | 365d TTL       |
| all         | economic_events         | R               | ✓   | ✓    | true  | 365d TTL       |
| sports      | fixture_features        | R               | ✓   | ✓    | true  | 90d TTL        |
| sports      | odds_features           | R               | ✓   | ✓    | true  | 30d TTL        |
| sports      | derived_features        | R               | ✓   | ✓    | true  | 90d TTL        |
| commodity   | storage_alpha           | R               | ✓   | ✓    | true  | 180d TTL       |
| commodity   | weather_delta           | R               | ✓   | ✓    | true  | 180d TTL       |
| defi        | lst_yields              | R               | ✓   | ✓    | true  | 365d TTL       |
| defi        | lst_native_rates        | R               | ✓   | ✓    | true  | 365d TTL       |

### 2.4 ML-Service Shards

ML predictions are REPRODUCIBLE with pinned model_id + model_version (propagated into prediction event fields, confirmed
`live_handler.py:80-96` + `schemas.py:150-192`).

| asset_group | data_type           | retention_class | hot | warm | table | cold_lifecycle                             |
| ----------- | ------------------- | --------------- | --- | ---- | ----- | ------------------------------------------ |
| all         | per_strategy_signal | R               | ✓   | ✓    | true  | 180d TTL + keep flag (costly to recompute) |

### 2.5 Execution-Service Shards (STREAM_ONLY — forever)

| asset_group | data_type           | retention_class | hot | warm | table | cold_lifecycle      |
| ----------- | ------------------- | --------------- | --- | ---- | ----- | ------------------- |
| all         | execution_fills     | SO              | ✓   | ✓    | true  | **forever, no TTL** |
| all         | execution_positions | SO              | ✓   | ✓    | true  | **forever, no TTL** |
| all         | execution_pnl       | SO              | ✓   | ✓    | true  | **forever, no TTL** |
| all         | paper_ledger        | SO              | ✓   | ✓    | true  | **forever, no TTL** |

---

## 3. D3 Firehose Opt-Out List

**Result: EMPTY.** MTDS does not produce raw L2/L3/MBO. All shards are windowed aggregates (1-min UTCAlignedScheduler +
`book_snapshot_5` = 5-level depth). No shard gets `table: false`.

> **Note for Plan 01**: If a future connector adds raw tick-by-tick L2/L3 (e.g., full order book depth), add it to
> `SINK_MATRIX` with `table: false` at that time. The matrix's `raise-on-unknown` gate ensures new shards get classified
> before going live.

---

## 4. Execution Ledger Coverage Finding (Plan 00 Todo 3)

**Finding: Execution fills/positions/PnL do NOT land on the UAC global ledger (`canonical.crosscutting.ledger`).**

Evidence (verified Jun 2026 code state):

- `engine/modes/live/data_sink.py`: Direct async GCS writes → `results/{venue}/{date}/{instruction_id}_{timestamp}.json`
- `results/save_operations.py`: Dual-write to canonical `build_path("execution_fills")` parquet (new Jun 16 via
  `feat(pipeline-mode)`) AND untyped JSON
- `ManifestWriter.record_captured()` called but wrapped in bare `except Exception` (silent swallow — P0 from May 2026
  audit; unresolved)
- `grep canonical.crosscutting.ledger execution_service/` → **0 hits**

**Plan 09 scope implication**: The cutover is NOT just "declare `stream_only`" — it must also wire fills/positions/PnL
through the UTL facade `publish()` path so the Pub/Sub warm sink captures them durably (cold GCS forever, no TTL). The
global ledger (`canonical.crosscutting.ledger`) remains the typed-schema target but is NOT the STREAM_ONLY buffer; the
Pub/Sub warm→cold sink IS.

**Note on paper ledger**: `PaperMatchingEngine` (`engine/modes/live/matching_engine.py`) gets mark prices from
caller-provided `MarketData` (no live feed integration); paper fills follow the same direct-GCS write path.

---

## 5. Sampling vs Walked

| Repo              | Method                                                                                                                                      |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| MTDS              | Direct file read `websocket_runner.py:140-250` + connector audit                                                                            |
| UAC               | Full file read `events/streaming.py`                                                                                                        |
| UTL               | Full `streaming/__init__.py` + agent grep                                                                                                   |
| MDPS              | grep `live_aggregator.py` confirmed `_MDPSTickFetcher`                                                                                      |
| features-service  | Sub-agent exhaustive grep across all families                                                                                               |
| strategy-service  | Sub-agent full audit (`colocated_engine.py`, `cascade_subscriber.py`, signal pipeline)                                                      |
| ml-service        | Sub-agent exhaustive grep across inference path                                                                                             |
| execution-service | Sub-agent audit + existing `global_ledger_audit_execution_service_2026_05_23.md` (verified still current as of Jun 16 pipeline-mode commit) |

---

## 6. What This Unblocks

- **Plan 01** (UAC): SINK_MATRIX seed (§2) + generalise 4 event shapes into envelope
- **Plan 03** (infra): Topic list = all `(asset_group, data_type)` rows in §2 × stage; D3 opt-out list = empty
- **Plan 09** (execution): Scope is facade consume + declare SO + fix the GCS write path (not just ledger annotation)
