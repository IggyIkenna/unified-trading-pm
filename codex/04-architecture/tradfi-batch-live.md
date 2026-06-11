---
scope: [engineer, admin]
created: 2026-05-16
last_reviewed: 2026-06-11
plan:
  plans/active/tradfi_manifest_canonicalisation_2026_06_01.md +
  pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md (R6-codex seam doc, replaces the 2026-05-16
  placeholder)
---

# TradFi Batch/Live Architecture

> Per-asset-group narrative for `asset_group=tradfi`. Cross-cutting batch=live invariant lives in
> [`batch-live-architecture.md`](batch-live-architecture.md); the source-aware `pipeline_mode` contract lives in
> [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md) § "Ratified TARGET design". This doc
> covers the TradFi-specific shape: source list, calendar gating, matcher pattern, shard atomicity, and the dual-source
> (databento + massive) seam.

---

## §1 TradFi sources + venues in scope

TradFi is the canonical MULTI-SOURCE asset group — the same logical metric arrives from more than one vendor, so the
row-level `source` column + per-source manifest rows (crosscutting `source=` provenance rule) were proven here first.

| Source      | Role                                                                | `SOURCE_MODE_CAPABILITY` (UAC)                                                        |
| ----------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `databento` | Primary: CME futures/options (GLBX.MDP3), equities/ETF trades+OHLCV | `{BATCH, LIVE, REPLAY}` — Live-API 24h intraday replay                                |
| `massive`   | Secondary (= Polygon.io): equities/ETF ticks, REST time-range fetch | `{BATCH, LIVE, REPLAY}` — REST tick-within-range; Starter tier live is 15-min delayed |
| `yahoo`     | VIX 15m rolling window (last 60d) + tradfi ETFs                     | `{BATCH}`                                                                             |
| `barchart`  | VIX 15m historical preload (2020-01-02 → 2025-11-12)                | `{BATCH}`                                                                             |
| `eia`       | Energy weekly series                                                | `{BATCH, REPLAY}` — weekly series re-fetchable by date                                |

Adapters live in `market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/`
(`databento_adapter.py` + `databento_equity.py` + the CME/OPRA converters, `massive_tradfi_rest_connector.py`,
`yahoo_finance_adapter.py`, `eia_adapter.py`, plus macro adapters — FRED/ECB/CFTC-COT/OFR/Baker-Hughes). The live
websocket connector is `live/connectors/databento_tradfi_ws.py`. Post-cutover expansion: **IBKR** (`ibkr_adapter.py` via
`ibkr-gateway-infra`).

**Source of truth**: UAC `registry/capability_declarations/_tradfi.py` (venue/instrument capability) +
`SOURCE_MODE_CAPABILITY` (mode capability) + `SOURCE_PRIORITY[("tradfi", <data_type>)]` (per-data_type source order).
Massive does NOT cover VIX/VX futures — the VIX 15m gap remains Barchart (preload) + Yahoo (rolling) with honest gap
semantics (UAC `registry/data_source_continuity.py`).

---

## §2 Batch/live symmetry — TradFi-specific shape

The core invariant from [`batch-live-architecture.md §1`](batch-live-architecture.md) applies: 99% of the code path is
identical. The seams for TradFi:

| Seam            | Batch                                        | Live                                               |
| --------------- | -------------------------------------------- | -------------------------------------------------- |
| Data source     | Databento bulk / Massive REST Parquet on GCS | Databento Live-API websocket (MTDS → Redis → MDPS) |
| Feature compute | Load feature Parquet from GCS                | Embedded UTL `feature_calculator` in-process       |
| ML inference    | Load prediction Parquet from GCS             | Subscribe to prediction Redis/PubSub topic         |
| Execution fills | `MatchingEngine` (L2Matcher)                 | Real venue execution (IBKR post-cutover)           |

TradFi adds ONE seam-adjacent rule the 24/7 groups don't have: **the venue trading calendar gates the live path's
expected-cadence checks.** Live-mode emission policy MUST consult UAC
`registry/venue_trading_calendar.is_non_trading_day(venue, iso_date)` before flagging staleness — else half the trading
week (weekends/holidays) shows as STALE. NYSE/NASDAQ/CME calendars differ; the check is per-venue.

**Replay/continuity (M6)**: both `databento` and `massive` are intraday-replay-capable (vendor-doc-confirmed,
UAC@8079b884) — Databento's Historical API is 24h-embargoed, so a today-since-start backfill rides the **Live-API
intraday replay**, not historical. The M6 startup gate therefore resolves TradFi shards to "autostart `replay_databento`
/ `replay_massive` over `[batch-cutoff → now]`" — TradFi never has to pre-run live just to cover the tail.

---

## §3 Matching engine — L2Matcher (TradFi)

TradFi fills in batch mode route through the SAME `L2Matcher` as CeFi
(`execution-service/execution_service/matching_engine/`) — matcher dispatch is on
`unified_api_contracts.internal.execution.BatchExecutionMode`, never on asset_group:

- **`BENCHMARK`**: fills at requested price, zero commission/slippage (strategy alpha isolation).
- **`SIMULATED`**: routes through L2Matcher depth simulation (execution alpha measurement).

TradFi-specific matcher considerations:

- **Session boundaries**: fills cannot occur on non-trading days / outside the venue session (`is_non_trading_day` +
  `EXPECTED_OUTSIDE_TRADING_HOURS` semantics) — the batch engine must not synthesize fills in a closed session.
- **Futures roll**: contract expiry is a hard instrument boundary — instrument definitions are re-fetched per date from
  instruments-service (never copied between dates; CME futures/options list/expire daily). The only static exception is
  the CBOE VIX index.
- **Options/futures chain bundles**: chain data_types are BUNDLED at the `underlying=` grain (see §4) — the matcher
  consumes per-instrument legs, the data layer validates the bundle cluster.

---

## §4 Shard atomicity — TradFi

TradFi shard atom is `(asset_group=tradfi, source, data_type, instrument_id, date)` — note **`source` is part of the
atom**: the same `(data_type, instrument_id, date)` legitimately exists once per source (`batch_databento` AND
`batch_massive` rows coexist; the M5 union view collapses them for data-status).

**Bundled chain data_types**: `options_chain` / `futures_chain` (+ `combo`) are captured at the `underlying=` bundle
grain — one shard covers the whole chain for an underlying; cluster validation at `record_captured()` is MANDATORY (else
`MissingClusterValidationError`). NOTE the name collision: `options_chain`/`futures_chain` are BOTH an instrument_type
AND a genuine snapshot data_type (`*_OPTIONS_CHAIN_SNAPSHOT`) — do not "fix" one into the other.

**Empty-record rules (closed set, UAC `EmptyConfirmedReason`)**:

- `EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND` — whole-day venue closure (the calendar-driven workhorse reasons).
- `EXPECTED_OUTSIDE_TRADING_HOURS` — intraday slot outside the published session.
- `EXPECTED_PARTIAL_HALF_DAY` — shortened session (e.g. day after Thanksgiving).
- `EXPECTED_INSTRUMENT_NOT_LISTED` / `EXPECTED_INSTRUMENT_DELISTED` — outside the instrument's listing window
  (pre-request filter against `InstrumentRecord.available_from/available_to_datetime`, same contract as CeFi §9).
- `EXPECTED_PRE_SOURCE_COVERAGE_START` / `EXPECTED_PAST_SOURCE_COVERAGE_END` — per-source archive bounds (e.g. Barchart
  VIX preload ends 2025-11-12; Yahoo only covers the rolling 60d).
- `EXPECTED_LEGACY_MIGRATION_MISSING_EXPIRY` — migration-only: pre-2026-05-13 futures/options rows whose expiration
  cannot be backfilled from Databento reference data.
- Any other absence MUST be `record_failed(error=classify_venue_error(...))` — NOT `record_empty`. A 401/auth failure is
  `attempted_failed` (retryable), never honest absence.

(The placeholder's `EXPECTED_NON_TRADING_DAY` reason never existed in UAC — the real closed set is above.)

**Shard identity propagation**: writer atomicity → manifest row key → data-status display → downstream preflight gate →
deployment-UI drilldown must carry the identical atom. SSOT:
[`../../plans/epics/infrastructure_master.md`](../../plans/epics/infrastructure_master.md).

---

## §5 Dual-source provenance — databento + massive

TradFi is the reference implementation of the crosscutting `source=` provenance rule
(`plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`):

- Every captured cell carries a row-level `source` column + a per-source manifest row; `record_captured(source=...)` is
  REQUIRED; blank/unregistered → `MissingSourceError`.
- `pipeline_mode` is source-aware (`batch_databento`, `batch_massive`, `batch_yahoo`, `batch_barchart`, `batch_eia`) via
  UTL `derive_pipeline_mode_for_row(venue, "tradfi", data_type)`; the write-time cross-check
  `source_string_for(pipeline_mode) == source` raises `PipelineModeSourceMismatchError` on disagreement.
- Downstream resolves via `SOURCE_PRIORITY` / `select_primary_available_source()` — a cell is `captured` when ≥1 source
  has it (M5 union); the drilldown shows the per-(pipeline_mode × source) breakdown.
- `transport` is a COLUMN (`rest` for databento/massive/yahoo/barchart/eia batch), never glued into the source name.

The migrator reference implementation for the whole workspace is `migrate_tradfi_to_v9_canonical.py`
(`_pipeline_mode → batch_databento` — the pattern every other AG copies).

---

## §6 Live pipeline timing — TradFi

TradFi ticks follow the same MTDS → Redis Stream → MDPS → features-service cascade
([`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md)):

- **MTDS** subscribes to the Databento live gateway (`databento_tradfi_ws.py`) + emits
  `streaming.tradfi.candle_boundary_crossed` at UTC-aligned boundaries. The UTC-alignment rule (§10.1 of
  `batch-live-architecture.md`) applies — no partial windows at startup.
- **Calendar-aware staleness**: the expected-cadence alert tier consults `is_non_trading_day` — a silent feed on
  Saturday is NOT an incident; a silent feed at 15:00 ET on a Tuesday is.
- **Live=batch path parity**: live writes land on the canonical hive path with `pipeline_mode=` LEFT of
  `asset_group=tradfi` — currently the transitional `live_websocket` alias; `live_databento` under the gated
  `M1-BREAKING` tranche.

---

## §7 Anti-patterns

- Don't build a TradFi-only backtest engine — route through execution-service MatchingEngine (`BatchExecutionMode`
  dispatch, same as CeFi).
- Don't stamp coarse `pipeline_mode=batch`/`live` — TradFi is source-aware (`batch_databento` / `batch_massive` / …);
  readers prefix-match `batch_*`/`live_*`/`replay_*`, never an exact coarse literal.
- Don't glue transport into the source (`databento_rest` etc.) — `transport` is a separate manifest COLUMN (R4).
- Don't flag live staleness without consulting `is_non_trading_day` — half the week is legitimately silent.
- Don't copy instrument definitions between dates — CME futures/options expire/list daily; re-run the
  instruments-service CLI per missing date (VIX index is the only static exception).
- Don't record a 401/auth failure as `record_empty` — `attempted_failed` keeps the cell retryable (CeFi §9 contract).
- Don't treat `options_chain`-the-instrument_type and `options_chain`-the-snapshot-data_type as a bug to "unify" — it is
  a known name collision, both are real.

---

## §8 Cross-references

- **Batch/live invariant (global)**: [`batch-live-architecture.md`](batch-live-architecture.md) §1-§4
- **Source-aware pipeline_mode + M1–M8 target**:
  [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md) § "Ratified TARGET design"
- **Reconciliation column + precedence**:
  [`../02-data/pipeline-mode-and-batch-live-reconciliation.md`](../02-data/pipeline-mode-and-batch-live-reconciliation.md)
- **Sibling per-AG docs**: [`cefi-batch-live.md`](cefi-batch-live.md) · [`sports-batch-live.md`](sports-batch-live.md) ·
  [`prediction-batch-live.md`](prediction-batch-live.md)
- **Matching engine + L2Matcher**: [`batch-live-architecture.md §5`](batch-live-architecture.md)
- **Live pipeline cascade**:
  [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md)
- **Replay subsystem**: [`../05-infrastructure/replay-subsystem.md`](../05-infrastructure/replay-subsystem.md)
- **Mode-axis discipline**:
  [`../06-coding-standards/mode-axis-discipline.md`](../06-coding-standards/mode-axis-discipline.md)
- **Empty-record taxonomy**:
  [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) +
  [`../02-data/honest-absence-downstream-handling.md`](../02-data/honest-absence-downstream-handling.md)
- **Source provenance plan**: `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`
- **TradFi canonicalisation walk**: `plans/active/tradfi_manifest_canonicalisation_2026_06_01.md`
