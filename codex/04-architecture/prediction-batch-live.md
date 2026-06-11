---
scope: [engineer, admin]
created: 2026-05-16
last_reviewed: 2026-06-11
plan:
  plans/active/prediction_manifest_canonicalisation_2026_06_01.md +
  pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md (R6-codex seam doc, replaces the 2026-05-16
  placeholder)
---

# Prediction Batch/Live Architecture

> Per-asset-group narrative for `asset_group=prediction`. Cross-cutting batch=live invariant lives in
> [`batch-live-architecture.md`](batch-live-architecture.md); the source-aware `pipeline_mode` contract lives in
> [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md) § "Ratified TARGET design". This doc
> covers the prediction-specific shape: the venue ≠ source rule, the canonical-question-group shard model, market
> lifecycle bounds, and the CLOB batch/live seam.

---

## §1 Prediction sources + venues in scope

**Venue ≠ source (HARD distinction for prediction).** `POLYMARKET` and `KALSHI` are VENUES; the registered sources are
the Polymarket APIs. Polymarket-vs-Kalshi price dispersion is a FEATURE-LAYER concern (cross-venue spread features),
NEVER a source merge — two venues' books are different markets, not two feeds of one logical series.

| Source                 | Role (data_types)                                                                    | `SOURCE_MODE_CAPABILITY` (UAC)                       |
| ---------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| `polymarket_clob`      | Tick series: `trades`, `book_snapshot`, `prediction_canonical_question_group`        | `{BATCH, LIVE, REPLAY}` — CLOB re-fetchable intraday |
| `polymarket_gamma_api` | `MARKET_LIFECYCLE` metadata (`/markets/{conditionId}` created/resolution/settlement) | `{BATCH}` — market metadata, not a tick series       |

Kalshi rides the same adapter family as a second VENUE (post-cutover dispersion target); its metadata source is a
deferred follow-up slot in `SOURCE_PRIORITY`.

Adapters live in `market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/`
(`base_prediction_adapter.py`, `polymarket_adapter.py`, `kalshi_adapter.py`); the live websocket connectors are
`live/connectors/polymarket_ws.py` + `kalshi_ws.py`. Market lifecycle capture
(`market_created_at`/`resolution_time`/`settlement_time`) is instruments-service (`MARKET_LIFECYCLE` via the gamma API).

**Source of truth**: UAC `SOURCE_PRIORITY[("prediction", <data_type>)]` + `SOURCE_MODE_CAPABILITY` +
`registry/capability_declarations/_prediction.py`.

---

## §2 Batch/live symmetry — prediction-specific shape

The core invariant from [`batch-live-architecture.md §1`](batch-live-architecture.md) applies: ONE prediction pipeline,
24/7 (no trading-calendar gating — prediction markets never close as a class; individual markets open/resolve per their
own lifecycle, §4).

| Seam            | Batch                                   | Live                                         |
| --------------- | --------------------------------------- | -------------------------------------------- |
| Data source     | CLOB REST polling → Parquet on GCS      | Polymarket/Kalshi WS (MTDS → Redis → MDPS)   |
| Feature compute | Load feature Parquet from GCS           | Embedded UTL `feature_calculator` in-process |
| ML inference    | Load prediction Parquet from GCS        | Subscribe to prediction Redis/PubSub topic   |
| Execution fills | `MatchingEngine` (CLOB book simulation) | Real venue CLOB order execution              |

**Replay/continuity (M6)**: `polymarket_clob` is live- AND replay-capable — the CLOB serves a recent window on demand,
so the M6 startup gate resolves prediction tick shards to "autostart `replay_polymarket_clob` over
`[batch-cutoff → now]`" (case 1). `polymarket_gamma_api` market metadata is batch-only reference data — cadence
`scheduled_recurring` per M8, with no live stream to reconcile against (M6 case 3 applies but lifecycle metadata
tolerates a configured gap).

**Candle path parity**: the processed-candles `pipeline_mode=` path segment is written identically by batch migrator and
live candle writers (mdps@5e7f075 fixed the batch≠live divergence) — a relaunched live MDPS reads/writes the same
canonical path the migration produces.

---

## §3 Matching engine + the canonical-question-group layer

Polymarket/Kalshi are CLOBs — prediction fills in batch mode route through the execution-service matching engine's
order-book simulation (dispatch on `unified_api_contracts.internal.execution.BatchExecutionMode`, never on asset_group;
`BENCHMARK` fills at requested price, `SIMULATED` walks the book).

The prediction-specific layer sits ABOVE matching: the **`prediction_canonical_question_group` axis** groups synonymous
markets (e.g. recurring hourly/daily "will-X-by-Y" series, and the same question listed on Polymarket vs Kalshi) for
feature/strategy consumption. The grouping registry lives in UAC `canonical/domain/prediction/`
(`classify_polymarket_to_canonical_group`); cross-venue mapping rollout per
`plans/archive/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`. Matching never crosses
venues — only features do.

---

## §4 Shard atomicity + market lifecycle — prediction

Prediction shard atom is
**`(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)`** —
the LIVE writer's atom is the canonical atom (batch=live SSOT).

- **`market_id` (`conditionId`) is a row-level parquet column, NOT a shard axis** — HOURLY (24/day) + DAILY + ELECTION
  groups all roll up to ONE manifest row per `(canonical_question_group, day)`; per-market detail at drilldown comes
  from reading the parquet. Raw canonical OBJECTS stay per-cid (`…/data_type={DT}/{cid}.parquet`);
  `canonical_question_group`/`market_id`/`available_at` are parquet COLUMNS.
- **Bundled capture**: the manifest row is emitted via `record_captured_from_counts` with
  `observed_clusters = {market_id: row_count}` + `expected_root_clusters` (UAC `PREDICTION_GROUPS`) — per-market_id
  cluster validation lives INSIDE the per-`(cqg, day)` row (`MissingClusterValidationError` on a missing expected
  cluster), never as per-cid manifest rows.
- **Market lifecycle bounds the could-exist window**: instruments-service `MARKET_LIFECYCLE`
  (`market_created_at`/`resolution_time`/`settlement_time`) is the SSOT for when a market CAN have data. MTDS respects
  lifecycle bounds at fetch time (pre-creation / post-resolution slots are never attempted for that market);
  `LookaheadBiasError` checks are per-market-aware.

**Empty-record rules (closed set, UAC `EmptyConfirmedReason`)**:

- Open-but-quiet markets → `SOURCE_RETURNED_ZERO` (the market traded nothing in the window — honest zero, not absence).
  Guarded: a zero-claim is rejected when the IS catalog says the cell should have data.
- Pre-creation / post-resolution windows are handled by the LIFECYCLE FILTER (not a reason): markets outside their
  lifecycle window are excluded from the expected universe per the IS `MARKET_LIFECYCLE` could-exist roll-up — the
  listing-window family (`EXPECTED_INSTRUMENT_NOT_LISTED`/`EXPECTED_INSTRUMENT_DELISTED`) covers per-instrument windows
  where a seeded cell needs a typed reason.
- Auth/fetch/empty-response failures → `record_failed(error=classify_venue_error(...))` (`attempted_failed`, retryable)
  — an empty CLOB response on an open market is a failure to capture, never `record_empty(SOURCE_RETURNED_ZERO)` (CF-11
  contract; both adapters enforce).

(The 2026-05-16 placeholder's `EXPECTED_PRE_MARKET_GENESIS` / `EXPECTED_MARKET_RESOLVED` reasons never existed in UAC —
the real mechanism is the lifecycle filter + the closed set above.)

**Shard identity propagation**: writer atomicity → manifest row key → data-status → preflight gate → deployment-UI
drilldown carry the identical atom. SSOT:
[`../../plans/epics/infrastructure_master.md`](../../plans/epics/infrastructure_master.md).

---

## §5 Source provenance + `pipeline_mode` — prediction

- `pipeline_mode` is source-aware: `batch_polymarket_clob` / `batch_polymarket_gamma_api`; `live_polymarket_clob` /
  `replay_polymarket_clob` exist per the capability matrix (live writes ride the transitional `live_websocket` alias
  until the gated `M1-BREAKING` tranche). NEVER coarse `batch`/`live`, never an asset_group-glued value.
- Prediction is **single-source per data_type today** → the writer AUTO-STAMPS `source` via `default_source`
  (`SOURCE_PRIORITY` carries the prediction pairs; `record_captured(source=...)` still REQUIRED semantics — blank →
  `MissingSourceError`). Swap-resilience is the point: when a second source lands, rows are already disambiguated.
- `transport` is a COLUMN: `rest` for the CLOB poll + gamma API; the WS connectors stamp `websocket` when the gated
  `live_<source>` writers land. Never glue transport into the source name.
- The historical `_index` source-stamp + the `pipeline_mode=` path partition ride the prediction canonicalisation walk
  (`prediction_manifest_canonicalisation_2026_06_01.md` single-walk riders); live/new writes already auto-stamp.

---

## §6 Live pipeline timing — prediction

Prediction ticks follow the same MTDS → Redis Stream → MDPS → features-service cascade
([`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md)):

- **MTDS** runs `polymarket_ws.py` / `kalshi_ws.py` (+ the 200ms CLOB poll for book snapshots) and emits
  `candle_boundary_crossed` at UTC-aligned boundaries — no partial windows at startup
  ([`batch-live-architecture.md §10.1`](batch-live-architecture.md)).
- **24/7, lifecycle-gated**: there is no venue trading calendar; staleness expectations are bounded per market by the IS
  lifecycle (a resolved market going silent is expected; an open market going silent is an incident).
- **Live=batch path parity**: live writes land on the canonical hive path with `pipeline_mode=` LEFT of
  `asset_group=prediction` — currently the transitional `live_websocket` alias; `live_polymarket_clob` under the gated
  `M1-BREAKING` tranche.

---

## §7 Anti-patterns

- Don't merge Polymarket + Kalshi as two SOURCES of one series — they are VENUES; dispersion is a feature-layer concern
  (venue ≠ source).
- Don't stamp coarse `pipeline_mode=batch`/`live` — prediction is source-aware (`batch_polymarket_clob` / …); readers
  prefix-match `batch_*`/`live_*`/`replay_*`, never an exact coarse literal.
- Don't make `market_id` a shard axis — it is a row-level column inside the per-`(cqg, day)` bundle; promoting it
  inflates the manifest ~10× for zero isolation gain (a sub-agent draft that collapsed the atom the OTHER way — dropping
  `canonical_question_group` — was equally wrong and reverted; the LIVE writer's atom is canonical).
- Don't skip cluster validation on the bundled row — `record_captured_from_counts` with
  `observed_clusters`/`expected_root_clusters` is mandatory (`MissingClusterValidationError`).
- Don't fetch outside lifecycle bounds or derive lifecycle at read time — IS `MARKET_LIFECYCLE` is the could-exist SSOT;
  copying lifecycle between dates is the instruments-copy anti-pattern.
- Don't record an empty CLOB response on an open market as `record_empty(SOURCE_RETURNED_ZERO)` — that is
  `record_failed` (CF-11); zero-volume on an open market IS `SOURCE_RETURNED_ZERO`.
- Don't reference the phantom `EXPECTED_PRE_MARKET_GENESIS`/`EXPECTED_MARKET_RESOLVED` reasons — they never existed.

---

## §8 Cross-references

- **Batch/live invariant (global)**: [`batch-live-architecture.md`](batch-live-architecture.md) §1–§4
- **Source-aware pipeline_mode + M1–M8 target**:
  [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md) § "Ratified TARGET design"
- **Reconciliation column + precedence**:
  [`../02-data/pipeline-mode-and-batch-live-reconciliation.md`](../02-data/pipeline-mode-and-batch-live-reconciliation.md)
- **Sibling per-AG docs**: [`cefi-batch-live.md`](cefi-batch-live.md) · [`tradfi-batch-live.md`](tradfi-batch-live.md) ·
  [`sports-batch-live.md`](sports-batch-live.md)
- **Shard-atom + empty-reason SSOT**:
  [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) +
  [`../02-data/honest-absence-downstream-handling.md`](../02-data/honest-absence-downstream-handling.md)
- **Live pipeline cascade**:
  [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md)
- **Mode-axis discipline**:
  [`../06-coding-standards/mode-axis-discipline.md`](../06-coding-standards/mode-axis-discipline.md)
- **Source provenance plan**: `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`
- **Prediction canonicalisation walk**: `plans/active/prediction_manifest_canonicalisation_2026_06_01.md`
- **CQG migration**: `plans/archive/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`
- **Predictions epic**: `plans/epics/predictions_master.md`
