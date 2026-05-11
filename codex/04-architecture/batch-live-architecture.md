---
scope: [engineer, admin]
---

# Batch / Live Architecture — single SSOT

This is the single SSOT for the batch / live architecture. It folds in the previous separate docs
(`batch-live-pipeline.md` + `batch-live-symmetry.md`, both deleted 2026-05-08 per
[`../../plans/active/codex_refactor_2026_05_08.md`](../../plans/active/codex_refactor_2026_05_08.md) Phase D.6) so the
principle, the 4 seams, the anti-drift guards, the service audit matrix, the matching engine, alpha decomposition, the
sports-specific notes, anti-patterns, and the instruments-live exception all live in one file.

---

## §1 Principle

Batch and live use the **same code path, same component interactions, same risk checks**. There is no such thing as a
"live-only strategy" or a "batch-only strategy." 99% of the code is identical. The only seam that differs is the
execution fill source.

This applies to ALL categories: CeFi, DeFi, TradFi, sports, prediction markets.

### Component interaction diagram

```
Strategy-Service -----> Execution-Service -----> Position-Balance-Monitor -----> PnL-Attribution -----> Risk-and-Exposure
     ^                        |                          |                            |                         |
     |                        |                          |                            |                         |
     +--- risk limits --------+                          +--- positions --------------+                         |
     |                                                                                                          |
     +--- exposure limits ------------------------------------------------------------------------------------------+
```

In batch mode, all five services are co-located (same process or local network). In live mode, they communicate via
PubSub. The interaction contract is identical in both modes.

Data flow:

1. **Strategy-Service** generates execution instructions from features + ML predictions
2. **Execution-Service** fills the instruction (matching engine in batch, real venue in live)
3. **Position-Balance-Monitor** updates positions from fills
4. **PnL-Attribution** computes realized and unrealized P&L
5. **Risk-and-Exposure** enforces limits and feeds back to Strategy-Service

### TL;DR — what differs

|                     | Batch Mode                        | Live Mode                                                                |
| ------------------- | --------------------------------- | ------------------------------------------------------------------------ |
| Data transport      | GCS Parquet files                 | **Redis Stream (inner-loop) + PubSub (cross-service)**                   |
| Feature calculation | Loaded from GCS                   | Same code path as batch; trigger swapped from scheduler to Redis Stream  |
| ML inference        | Batch prediction via GCS          | Redis Stream subscription → prediction → Redis Stream / PubSub publish   |
| Latency target      | Minutes/hours                     | Sub-second                                                               |
| Network pattern     | GCS read/write                    | Redis Stream `XADD` / `XREADGROUP` (inner-loop) + PubSub (cross-service) |
| Forbidden pattern   | Synchronous REST between services | Synchronous REST between services                                        |

> **POST-2026-05-08 SSOT** — the inner-loop live cascade between MTDS → MDPS → features-service is **Redis Stream**
> (CANDLE_BOUNDARY_CROSSED + CANDLE_COMPUTED + FEATURES_COMPUTED), per
> [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md) § "Trigger
> cascade" + [`../03-observability/coordination-events.md`](../03-observability/coordination-events.md). PubSub remains
> the right transport for cross-service async fan-out (instruments-service catalogue refresh, strategy → execution,
> alerting). Where this doc says "PubSub" below, read it as "the live transport family — Redis Stream for the inner-loop
> cascade, PubSub for cross-service fan-out."

---

## §2 The 4 seams

The same pipeline business logic runs in both modes. The 4 seams that differ between modes are:

1. **Data source seam**: batch reads GCS Parquet; live subscribes to PubSub topic.
2. **Feature seam**: batch loads feature Parquet from GCS; live calls embedded library in-process.
3. **ML inference seam**: batch reads prediction Parquet from GCS; live subscribes to prediction PubSub topic.
4. **Output seam**: batch writes Parquet to GCS; live publishes to PubSub topic.

All other logic (signal generation, position sizing, risk checks) is shared and mode-agnostic.

### Data transport

#### Batch: GCS as message bus

Services communicate exclusively through GCS (or S3) Parquet files. Service A writes output to a well-known bucket path;
Service B reads from that path on its next scheduled run.

- Coupling is through data contracts: Parquet schema + GCS path convention.
- No inter-service RPCs, no message queues, no PubSub in batch mode.
- Outputs are immutable: re-runs overwrite the entire shard, never append.
- Self-describing, schema-validated, BigQuery/Athena compatible.

#### Live: Redis Stream (inner-loop) + PubSub (cross-service) as message bus

Inter-service data flow in live mode uses two complementary async transports:

- **Redis Stream** — the inner-loop cascade between MTDS → MDPS → features-service. Consumer-group semantics (`XADD` /
  `XREADGROUP`) provide ordered per-shard delivery + replay-from-checkpoint when a consumer restarts. See
  [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md) for the
  full CANDLE_BOUNDARY_CROSSED → CANDLE_COMPUTED → FEATURES_COMPUTED cascade contract.
- **PubSub** — cross-service async broadcast (instruments-service catalogue refresh, strategy → execution signals,
  alerting fan-out to multiple subscribers). Fire-and-forget; downstream consumers are independent.

- Coupling is through async message contracts: Protobuf/Avro schema + topic/stream name convention.
- No inter-service synchronous HTTP/REST calls for data.
- PubSub is a message queue, not REST/RPC — see "No network hops clarification" below.
- Publishers and subscribers are independently deployable and restartable.

### Feature calculation

#### Batch: GCS-loaded features

Feature data is written to GCS Parquet by the relevant feature service, then read by the strategy/execution service as
part of its batch run. The feature values exist as files on object storage.

#### Live: embedded package (in-process)

The strategy process (and execution process) imports the feature calculator library directly as a Python package.
Feature computation happens in the same process, in memory, with no network call for the calculation itself.

- `unified-trading-library` (the `feature_calculator/` sub-package — formerly `unified-feature-calculator-library`,
  merged into UTL) is imported as a dependency, not called via HTTP.
- No RPC to a feature service during the hot path.
- Latency for the calculation is CPU-bound only — no serialization, no network round-trip.

This is the "embedded package model." It is distinct from the data transport layer (PubSub). The raw market tick data
that feeds into the in-process feature calculation arrives via PubSub subscription; the calculation itself is local.

### ML inference

#### Batch: GCS batch prediction

ML models are trained and artifacts written to GCS. Inference runs as a batch job: reads feature Parquet from GCS, runs
prediction, writes prediction Parquet back to GCS.

#### Live: PubSub subscription → in-process prediction → PubSub publish

The ML inference service subscribes to the feature PubSub topic, runs inference in-process on each message, and
publishes the prediction result to a downstream PubSub topic consumed by the strategy service.

### The "no network hops" rule — clarification

The rule "no network hops on the hot path" specifically prohibits **synchronous HTTP/REST calls between pipeline
services for data**. It does NOT prohibit PubSub.

| Pattern                                                            | Allowed?             | Reason                           |
| ------------------------------------------------------------------ | -------------------- | -------------------------------- |
| `GET http://features-service/api/v1/compute` from strategy-service | FORBIDDEN            | Synchronous RPC between services |
| `POST http://ml-service/api/v1/predict` from strategy-service      | FORBIDDEN            | Synchronous RPC between services |
| Subscribe to `topics/features-delta-one` and consume async         | ALLOWED              | Async message queue, not RPC     |
| Publish to `topics/strategy-signals` after computing               | ALLOWED              | Async message queue, not RPC     |
| Import `unified_feature_calculator_library` and call in-process    | ALLOWED              | Embedded package, no network     |
| Read `gs://features-bucket/day=2026-03-04/features.parquet`        | ALLOWED (batch only) | GCS object storage, not RPC      |

The distinction is synchronous vs asynchronous:

- **Synchronous RPC** (HTTP/REST, gRPC): caller blocks waiting for a response from another service. Forbidden for data
  flow.
- **Async messaging** (PubSub): publisher does not block; subscriber processes when ready. This is the standard live
  data transport.
- **In-process** (embedded library): no network at all for computation. Used for feature calculation and ML inference on
  the hot path.

---

## §3 Anti-drift guards

To prevent batch and live modes from drifting apart in business logic:

1. **Shared engine**: strategy and execution business logic lives in `unified-trading-library` (T1), imported by both
   batch and live service entrypoints. Logic is never duplicated per mode.
2. **Schema parity**: the Parquet schema (batch) and PubSub message schema (live) for each data type are derived from
   the same Pydantic/dataclass definitions in `unified-api-contracts` (T0).
3. **Determinism tests**: batch runs with known inputs produce known outputs. The same inputs fed through the live
   embedded feature calculation path must produce bit-identical outputs. This is validated in integration tests.
4. **No mode-specific business logic**: `if mode == "live": ... else: ...` branches inside business logic are forbidden.
   Mode differences belong only at the 4 seams above.

### Batch-only service exemptions

Not all services implement both modes. The following services are explicitly exempt from the batch/live symmetry
requirement because their workload is inherently offline and has no real-time streaming equivalent.

| Service             | Code | Mode       | Reason                                                                                                                                                                                  |
| ------------------- | ---- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ml-training-service | MLTR | Batch only | Model training is an offline optimization pass over historical data. There is no live training mode; training artifacts are consumed by ml-inference-service (which does support live). |

#### MLTR — ml-training-service

`ml-training-service` is **batch-only by design**. Model training requires full historical feature data loaded from GCS
Parquet, optimizer convergence over multiple epochs, and artifact serialization back to GCS. These properties are
fundamentally incompatible with a live streaming mode:

- Training consumes entire dataset partitions (not individual tick events).
- Gradient descent requires multiple passes over the data — not possible in a single-message PubSub handler.
- Trained model artifacts are written to GCS and consumed by `ml-inference-service`, which handles live prediction.

The `--mode live` CLI flag **must not** be added to `ml-training-service`. Any CI check validating batch/live symmetry
must exclude MLTR from its scope.

---

## §4 Service audit matrix

Current batch/live symmetry state across all pipeline services. Updated as part of
`live_batch_protocol_completeness_2026_03_10` plan + post-A.6 fix (execution-service is batch+live, not batch-only):

| Service                        | Code | Batch Handler           | Live Handler           | `--mode` CLI flag | Test Coverage       | Notes                                                                                                                                                                                                             |
| ------------------------------ | ---- | ----------------------- | ---------------------- | ----------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| features-commodity-service     | FCS  | `BatchHandler`          | `LiveHandler`          | batch / live      | unit: both modes    | Wired in `cli/main.py` (p1-todo-05)                                                                                                                                                                               |
| features-volatility-service    | FVS  | `BatchHandler`          | `LiveHandler`          | batch / live      | unit: both modes    | Pre-existing live handler                                                                                                                                                                                         |
| features-onchain-service       | FOS  | `BatchHandler`          | `LiveHandler`          | batch / live      | unit: both modes    | Pre-existing live handler                                                                                                                                                                                         |
| features-sports-service        | FSS  | `BatchHandler`          | n/a (batch-first)      | batch             | unit: batch handler | Live handler is future work (p1-todo-10)                                                                                                                                                                          |
| market-tick-data-service       | MTDS | `DownloadBatchHandler`  | n/a (download-only)    | batch             | unit: batch handler | Download service — no live streaming mode                                                                                                                                                                         |
| market-data-processing-service | MDPS | `process_candles`       | `LiveModeHandler`      | batch / live      | parser tests        | Lazy-imported; wired via `_mode_dispatch`                                                                                                                                                                         |
| instruments-service            | INS  | `InstrumentsBatchMode`  | n/a (catalogue-only)   | batch             | parser tests        | `--run-mode` renamed to `--mode` (p1-todo-09); see §9 instruments-live exception                                                                                                                                  |
| strategy-service               | STR  | `StrategyBatchHandler`  | `StrategyLiveHandler`  | batch / live      | unit: both modes    | `LiveHandler` facade added (p1-todo-13)                                                                                                                                                                           |
| ml-inference-service           | MLIN | `BatchInferenceHandler` | `LiveInferenceHandler` | batch / live      | unit: both modes    | Pre-existing                                                                                                                                                                                                      |
| ml-training-service            | MLTR | `TrainingHandler`       | **EXEMPT**             | batch only        | unit: batch handler | Batch-only by design (see exemption above)                                                                                                                                                                        |
| execution-service              | EXS  | `MatchingEngineHandler` | `ExecutionLiveHandler` | batch / live      | unit + integration  | Batch = matching engine fills (UAC `BatchExecutionMode`); live = real venue. Per CLAUDE.md "Batch = Live: Unified Pipeline Architecture" — execution alpha = live fills P&L − simulated fills P&L (see §6 below). |
| risk-service                   | RSK  | `RiskBatchHandler`      | `RiskLiveHandler`      | batch / live      | unit: both modes    | Pre-existing                                                                                                                                                                                                      |
| alerting-service               | ALS  | n/a                     | `AlertingHandler`      | live only         | integration         | Event-driven only; no batch mode                                                                                                                                                                                  |

### Handler pattern reference

All services that support both modes follow the `BaseModeHandler` pattern from `unified-trading-library`:

```
cli/handlers/
  batch_handler.py  — BatchHandler (or service-specific name)
  live_handler.py   — LiveHandler wrapping the domain BaseModeHandler
  __init__.py       — exports both + get_handler_for_mode()
```

The CLI entry point (`cli/main.py` or `cli/parser.py`) dispatches on `--mode batch|live` and constructs the appropriate
handler. Business logic lives in the service engine, shared by both modes — only the 4 seams differ.

### UX surface — how the symmetry shows up to the operator

The batch=live engineering invariant has a direct UX consequence in deployment-UI: the operator-facing surface for batch
and live mode is structurally identical, never two parallel UIs. Reinforces the engineering invariant via the
operator-facing UX so an operator inferring the system shape from the UI lands on the same model the code enforces.

What is identical:

- **Same Data-Status tab** — single tab, one widget tree.
- **Same drilldown depth** — per-shard staleness + per-day coverage + leaf parquet schema-view, identical hierarchy in
  both modes.
- **Same parquet schema-view** — same `LeafSchemaModal` mounting, same column inspector, same per-row preview.
- **Same event-tail** — per-shard event stream surface; mode does not branch the event-source path.

What is different — exactly one operator-visible thing:

- **Data-Status mode-toggle position** — `Batch` / `Scheduled-Today` / `Live` (per
  [`deployment_ui_lifecycle_tabs_2026_05_08`](../../plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md) Phase B.5).
  Mode=Batch answers "is the historical backfill complete?"; mode=Live answers "is the live pipeline writing fresh
  data?". **Same SHAPE, different TIME-SLICE** — the toggle invalidates the `/api/data-status` query key and refetches;
  no widget tree branch, no new bucket convention, no parallel component.

Concrete consequences for implementers:

- Phase B.5 implementation **must not** branch the widget tree by mode. Only the query-key changes. If you find yourself
  introducing a `<BatchDataStatus />` and a `<LiveDataStatus />` peer pair, you've broken the invariant — refactor back
  to a single component with a mode prop.
- A new `LiveFreshnessPanel` (Phase B.6) is added when `mode=Live`, but it is a **peer panel**, not a replacement — both
  render together when mode=Live, layered above the same drilldown. The freshness math reads the existing `available_at`
  per-row column; no new write path.
- "Strategy / execution / ML signals + metrics in live mode" do **not** belong in Data-Status — those live in Monitor →
  Experiments / Live per the
  [`../05-infrastructure/deployment-ui-architecture.md`](../05-infrastructure/deployment-ui-architecture.md) scope
  split. Data-Status is data + pricing correctness only, regardless of mode.
- Operator inferring the system shape from the UI: "live mode is a different time-slice of the same data path" — never
  "live mode is a different system."

Plan provenance:
[`deployment_ui_lifecycle_tabs_2026_05_08`](../../plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md) Phase A.4
added this section.

---

## §5 Matching engine + book matchers

Defined in UAC as `BatchExecutionMode` (`unified_api_contracts.internal.BatchExecutionMode`):

### BENCHMARK (strategy alpha isolation)

- Always fills at the **requested price** (exact odds for sports, exact limit price for CeFi/DeFi).
- Zero execution alpha by definition.
- Zero commission, zero slippage, zero latency impact.
- Purpose: isolate **strategy P&L** from execution quality.
- This is the default for strategy development and backtesting.

### SIMULATED (execution alpha measurement)

- Fills through the **matching engine** with realistic assumptions.
- For CeFi: order book depth simulation (L1/L2), latency modelling, maker/taker fees.
- For DeFi: AMM constant-product math (`x*y=k`), gas costs, MEV impact.
- For sports: commission rates per venue, slight odds spread (+/-0.5%) simulating market impact.
- Purpose: measure **execution alpha** = live fills P&L minus benchmark fills P&L.

The matching engine lives in `execution-service/execution_service/matching_engine/`. Book type matchers:

| Matcher            | Category | Model                                           |
| ------------------ | -------- | ----------------------------------------------- |
| `L0Matcher`        | Sports   | Top-of-book (scraped bookmaker odds)            |
| `L1Matcher`        | TradFi   | Trades with aggressor side                      |
| `L2Matcher`        | CeFi     | Order book depth with 5 levels                  |
| `AMMMatcher`       | DeFi     | Constant product swaps                          |
| `BenchmarkMatcher` | All      | Always fill at requested price (benchmark mode) |

---

## §6 Strategy alpha vs execution alpha

**Strategy alpha** is the P&L attributable to the strategy's signal quality. Measured using BENCHMARK mode fills (always
fill at requested price). If a strategy generates good signals, it will show positive P&L even with zero execution
optimisation.

**Execution alpha** is the P&L difference between live fills and benchmark fills. It measures how much the execution
layer adds (or loses) relative to the idealised fill. Computed as:

```
execution_alpha = live_fills_pnl - benchmark_fills_pnl
```

This separation is critical because:

- Strategy developers optimise signal quality without worrying about execution mechanics.
- Execution engineers optimise fill quality without conflating it with signal quality.
- A strategy with positive strategy alpha but negative execution alpha needs execution improvement, not signal rework.
- A strategy with negative strategy alpha is fundamentally unprofitable regardless of execution quality.

---

## §7 Sports-specific notes

### SportsMatchingEngine

Located at `execution_service/matching_engine/sports_matching.py`. Handles the full bet lifecycle:

1. `place_bet(BetOrder)` -- returns `CanonicalFill` (fill_id = bet_id, price = odds, quantity = stake)
2. `settle(bet_id, outcome)` -- settles individual bet (WON/LOST/VOID)
3. `settle_fixture(fixture_id, winning_selection)` -- settles all bets for a fixture
4. `settle_all(results)` -- batch settle by fixture results dict
5. `get_portfolio_summary()` -- returns `PortfolioSummary` with total_bets, wins, losses, ROI, bankroll

### Bets as positions

Sports bets are positions: open on placement, closed on settlement. A bet on "HOME @ 2.50" is a position with
`instrument_id=fixture_id`, `side=BUY`, `price=2.50`, `quantity=stake`. It stays open until the fixture settles. This
maps directly to the position-balance-monitor's position lifecycle.

### CanonicalFill mapping

`SportsMatchingEngine.place_bet()` returns a standard `CanonicalFill` from UAC:

- `fill_id` = bet UUID
- `instrument_id` = fixture_id
- `side` = BUY (backing a selection)
- `price` = odds (benchmark) or adjusted odds (simulated)
- `quantity` = stake
- `fee` = 0 (benchmark) or stake \* venue commission rate (simulated)

This ensures sports fills flow through the same position-tracking and PnL-attribution pipeline as CeFi/DeFi fills.

### Walk-forward capital carryover

`run_walk_forward()` in strategy-service passes season N's `final_capital` (from the engine's `PortfolioSummary`) as
season N+1's `initial_capital`. Capital compounds across seasons through the engine, not through a separate tracking
variable.

---

## §8 Anti-patterns fixed

These violations of the batch=live principle were identified and corrected:

1. **Inline settlement** — Computing `returned = stake * odds` directly in the backtest loop instead of routing through
   `SportsMatchingEngine.settle_all()`. Fixed: all settlement goes through the engine.
2. **Custom P&L calculation** — Backtest engines that computed their own P&L instead of reading from
   `PortfolioSummary.total_pnl`. Fixed: `BacktestResult` reads P&L from the engine summary.
3. **Manual position tracking** — Maintaining a separate list of open/closed bets outside the engine. Fixed: engine owns
   the bet lifecycle (`_open_bets` / `_settled_bets`). The `BankrollState` in strategy-service is retained only for
   staking context (compute_stake needs it) and max drawdown tracking, not for settlement.
4. **Category-specific backtest engines** — Building a standalone sports backtest that bypasses execution-service.
   Fixed: `strategy_service.engine.strategies.sports.backtest_engine` imports and uses
   `execution_service.matching_engine.sports_matching.SportsMatchingEngine`.
5. **Batch-only or live-only strategies** — Treating batch and live as fundamentally different code paths. Fixed: the
   same strategy code runs in both modes; only the execution fill source changes.

---

## §9 Instruments-live exception

Instruments-service runs live but does NOT use a `pipeline_mode=live` partition — instruments are reference data, not
ticks. Live-mode writes to the **same GCS path** as batch; T+1 is a retrospective audit, not a parallel backfill.
Detail: [`instruments-live-architecture.md`](instruments-live-architecture.md) +
[`instruments-preflight-chain.md`](instruments-preflight-chain.md). Live = batch invariant for instruments is mechanical
(same schema, same `available_at`, same code path; only source adapter swapped).

---

## §10 Live-pipeline timing semantics (UTC alignment + cascade rule)

The MTDS → MDPS → features-service cascade preserves batch=live by three timing invariants. The full design contract
lives in [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md); the
rules below are the architectural commitments every live consumer + reader must honour.

### §10.1 UTC midnight alignment

All timeframe boundaries are **UTC-aligned by construction**. Live consumers never emit partial windows on startup; they
wait for the next aligned boundary and start there. A 15s timeframe service booting at `14:23:07.4Z` emits its first
candle at `14:23:16.0Z` covering window `[14:23:00, 14:23:15)`. A 1m service booting at `14:23:07.4Z` emits its first
candle at `14:24:01.0Z` covering window `[14:23:00, 14:24:00)`. The window definition is identical to batch — batch jobs
over the same minute compute the same `[14:23:00, 14:24:00)` window from the same ticks. Live = batch by construction.

The UTL primitive `unified_trading_library.streaming.UTCAlignedScheduler` (+ `BoundaryTick` event) is the SSOT for the
alignment rule + grace-window NTP tolerance (default 500ms).

### §10.2 Service-start-order independence

Any service can boot in any order; they all sync at the next aligned boundary. MTDS booting at `14:23:07Z` + MDPS
booting at `14:23:30Z` + features-service booting at `14:23:55Z` all emit their first events at the next aligned
boundary for their respective timeframes — no startup handshake, no synchronization barrier. Mid-day restart of any
single service loses some live data; the replay subsystem
([`../05-infrastructure/replay-subsystem.md`](../05-infrastructure/replay-subsystem.md)) fills the gap. The downstream
service sees a stable `period_end` watermark on every event regardless of which upstream service booted first.

### §10.3 Multi-timeframe cascade rule (4×15s → 1m, never tick-replay)

The 1m candle MUST derive from 4× 15s candles emitted by the cascade, NOT from raw ticks re-aggregated. The same rule
applies recursively up the timeframe DAG:

| Parent timeframe | Child timeframe | Fanout (children per parent) |
| ---------------- | --------------- | ---------------------------- |
| 1m               | 15s             | 4                            |
| 5m               | 1m              | 5                            |
| 15m              | 5m              | 3                            |
| 1h               | 15m             | 4                            |
| 1d               | 1h              | 24                           |

`MDPSStreamingAggregator._feed_cascade_buffer` (UTL@`58bfbbeb`, integrated UTL@`5d3eddd`) buffers child candles per
`(asset_group, venue, instrument_id, parent_timeframe)` key + waits for `parent_fanout` child events before computing
the parent candle. Bypassing the cascade (e.g. tick-replay for the 1m candle while 15s is also derived from ticks)
diverges live from batch (batch uses cascade) and produces silent OHLCV drift across the timeframe DAG.

The 4-category gap semantics (FRESH / ZERO_ACTIVITY_BAR / no-emit / STALE / WS-dead-cascade) attach per-child; the
cascade buffer aggregates the per-child flags into the parent according to the `data_freshness` propagation table in
[`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md) § "Live gap
semantics — stale-not-missing." `PUBLISHED_DEGRADED` on any child → `PUBLISHED_DEGRADED` on parent (degraded propagates
up); pure carry-forward across all 4 children → `data_freshness=STALE` on parent.

### §10.4 Cross-cutting features fan-in

The cross-cutting features-service consumer (`CrossCuttingFeaturesRunner`, UTL@`58bfbbeb`) subscribes to MULTIPLE
asset_groups' `streaming.{ag}.features_computed` streams + uses `WatermarkAlignmentFanin` (UTL@`858f3c84`) to align
events at a common `period_end` boundary with a default 500ms intra-zone grace window. Tier-2 + Tier-3 alerting
thresholds (per [`alerting-batch-live.md`](alerting-batch-live.md) § "Live-Pipeline Alert Tier Table") fire if grace
expires without all expected streams contributing — degraded propagation (per-stream STALE) propagates without blocking,
clock-skew falls back to conservative latest-watermark (never emit beyond the slowest stream's watermark).

---

## §11 References + cross-refs

- **Live pipeline architecture**:
  [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md) (MTDS
  standalone + MDPS+features-asset-scoped colocated topology, Redis Stream cascade)
- **Replay subsystem**: [`../05-infrastructure/replay-subsystem.md`](../05-infrastructure/replay-subsystem.md) (smooth
  handoff replay → live)
- **Pipeline-mode partition (data, not instruments)**:
  [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md)
- **Instruments live = batch**: [`instruments-live-architecture.md`](instruments-live-architecture.md)
- **Auto-recovery + kill-switches**: [`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md)
- **Alerting parity**: [`alerting-batch-live.md`](alerting-batch-live.md)
- **Strategy hot-reload**: [`live-strategy-config-hot-reload.md`](live-strategy-config-hot-reload.md)
- **Cloud switch**: [`seamless-cloud-switch.md`](seamless-cloud-switch.md)
- **ML experiment lifecycle**: [`ml-experiment-lifecycle.md`](ml-experiment-lifecycle.md)
- **Research-service / DART integration**:
  [`research-service-and-dart-integration.md`](research-service-and-dart-integration.md)
- **Features-service architecture**: [`features-service-architecture.md`](features-service-architecture.md)
- **Feature-service pattern**:
  [`../06-coding-standards/feature-service-pattern.md`](../06-coding-standards/feature-service-pattern.md)
- **Integration-testing layers**:
  [`../06-coding-standards/integration-testing-layers.md`](../06-coding-standards/integration-testing-layers.md)
- **Honest absence downstream handling**:
  [`../02-data/honest-absence-downstream-handling.md`](../02-data/honest-absence-downstream-handling.md)
- **Instrument-lifecycle cache delta hot-reload**:
  [`instrument-lifecycle-cache-delta-hot-reload.md`](instrument-lifecycle-cache-delta-hot-reload.md)
- **Strategy config architecture**: see
  [`../06-coding-standards/strategy-identity-versioning.md`](../06-coding-standards/strategy-identity-versioning.md)
- **Data flow map**: see [`data-flow-map.md`](data-flow-map.md)
- **Communication patterns**: see [`communication-patterns.md`](communication-patterns.md)
- **Deployment topology diagrams**: see [`runtime-deployment-topology.md`](runtime-deployment-topology.md)
- **Benchmark fills cross-cutting**:
  [`../09-strategy/architecture-v2/cross-cutting/benchmark-fills.md`](../09-strategy/architecture-v2/cross-cutting/benchmark-fills.md)
- **Matching engine**: `execution-service/execution_service/matching_engine/`
  - Sports: `sports_matching.py` (`SportsMatchingEngine`, `BetOrder`, `PortfolioSummary`)
  - Unified: `engine.py` (`MatchingEngine`, `BookType`, matchers)
- **Backtest engine**: `strategy-service/strategy_service/engine/strategies/sports/backtest_engine.py`
- **BatchExecutionMode**: `unified-api-contracts/unified_api_contracts/internal/execution.py` (`BENCHMARK` and
  `SIMULATED` enum values)
- **E2E validation**: `e2e-testing/tests/integration/test_unified_sports_backtest.py`
