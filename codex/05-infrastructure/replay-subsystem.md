---
scope: [engineer, admin]
last_reviewed: 2026-06-11
---

# Replay Subsystem

> **STATUS** — covers the replay process that fills gap windows when the live pipeline loses data (intraday VM restart,
> websocket disconnect exceeding reconnect grace, cluster bounce). Designed alongside the live-pipeline activation for
> 2026-05-23. Full work plan in
> [`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)
> Phase 7. If this doc disagrees with the active plan, the plan wins.
>
> **⚠️ PARTIALLY SUPERSEDED on `pipeline_mode` (M1, operator-ratified; annotated 2026-06-11 R6-codex)**: this doc's
> "replay output writes `pipeline_mode=live_websocket`, never `replay_*`" rule was the PRE-M1 design. Under the ratified
> source-aware standard, **`replay_<source>` is a REAL pipeline_mode** (the intraday gap-fill tier, always the middle of
> mode-contextual precedence), and `live_websocket` is only the TRANSITIONAL alias until the gated `M1-BREAKING` tranche
> migrates live/replay writers + objects + readers. The `live_websocket` stamping described below is the CURRENT
> (transitional) implementation, not the target. SSOT:
> [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md) § "Ratified TARGET design —
> live/replay (M1–M8 settled contract)".

## TL;DR

Separate process replays gap windows by reading historical batch sources (Databento / Tardis / exchange REST snapshot)
and emitting events through the SAME Redis Streams the live pipeline uses. Downstream MDPS / features-service consumers
don't know or care whether an event is replay or live — only the timestamps differ. Smooth handoff to live via per-shard
`replay_watermark.{asset_group}.{shard_key}` Redis KV.

## Implementation status (2026-05-20)

### UTL layer (upstream helpers)

| Component                                                       | Status     | Location                                              |
| --------------------------------------------------------------- | ---------- | ----------------------------------------------------- |
| `ReplayWatermarkKV` — per-shard KV                              | ✅ SHIPPED | `unified_trading_library/streaming/replay.py:61-108`  |
| `ReplayPublisher` — event publisher with watermark coordination | ✅ SHIPPED | `unified_trading_library/streaming/replay.py:113-204` |

### MTDS layer (shipped MTDS@9358c54, 2026-05-14)

| Component                                                      | Status     | Location                                                                   |
| -------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------- |
| `InstrumentWindowData` — per-instrument window dataclass       | ✅ SHIPPED | `market_tick_data_service/replay/runner.py`                                |
| `HistoricalWindowFetcher` Protocol — venue-agnostic source API | ✅ SHIPPED | `market_tick_data_service/replay/runner.py`                                |
| `ReplayRunner` — boundary iteration + publish loop             | ✅ SHIPPED | `market_tick_data_service/replay/runner.py`                                |
| `ReplayHandler` — `--mode replay` CLI handler                  | ✅ SHIPPED | `market_tick_data_service/cli/handlers/replay_handler.py`                  |
| `HISTORICAL_WINDOW_FETCHER_FACTORIES` registry                 | ✅ SHIPPED | `market_tick_data_service/cli/handlers/replay_handler.py` (empty at Ph 7)  |
| Per-venue `HistoricalWindowFetcher` implementations            | ⏳ PENDING | Phase 3.5 rollout (defi → cefi → tradfi → sports → prediction)             |
| Phase 7 deployment — launch replay VMs in production           | ⏳ PENDING | `plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 7      |
| `REPLAY_BACKSTOP_REACHED` alerting hook                        | ⏳ PENDING | alerting-service `alerting_service_live_rules_2026_05_07.md` Phase 7 scope |

**`REPLAY_BACKSTOP_REACHED` wiring**: the event is emitted by `ReplayRunner.run()` (via `log_event`) when
`coverage_limit` is set and `end > coverage_limit`. `ReplayPublisher.finalize()` is called immediately after to stamp
the watermark KV — it does NOT emit the event. alerting-service must route `REPLAY_BACKSTOP_REACHED` to a `CRITICAL`
alert + strategy-service manual-resume gate. This wiring is in Phase 7 scope but has not yet run in production. Until
Phase 7 deploys, the event is emitted into the stream but no alerting consumer is hooked up. **Do NOT treat this as a
silent production gap** — Phase 7 was on the pre-cutover critical path.

> **[DELTA 2026-05-22]** **Current state:** `REPLAY_BACKSTOP_REACHED` event emission is shipped (UTL layer).
> Alerting-service consumer and per-venue `HistoricalWindowFetcher` implementations are PENDING (Phase 7 scope).
> Production replay VM deployment is PENDING. **Planned delta:** Phase 7 delivery tracked under
> `plans/epics/batch_live_symmetry_master.md`. **Target architecture:** Full alerting routing for
> `REPLAY_BACKSTOP_REACHED` + all per-venue fetchers + production replay VM fleet.

---

## MTDS implementation layer

### ReplayRunner

`ReplayRunner` (MTDS@9358c54) is scoped to one `(asset_group, venue, data_type, timeframe)` shard. It owns the
boundary-iteration loop; the UTL `ReplayPublisher` owns watermark coordination and Redis XADD.

Constructor parameters:

| Parameter          | Type                      | Notes                                                                  |
| ------------------ | ------------------------- | ---------------------------------------------------------------------- |
| `asset_group`      | `str`                     | Canonical asset-group key (`defi`/`cefi`/`tradfi`/…)                   |
| `venue`            | `str`                     | Canonical venue name                                                   |
| `data_type`        | `str`                     | UAC data-type key                                                      |
| `start` / `end`    | `datetime` (TZ-aware)     | Replay window; must be UTC-aware (enforced at construction)            |
| `timeframe`        | `str`                     | Boundary step string (`"1m"`, `"5m"`, …); parsed via `parse_timeframe` |
| `shard_key`        | `str`                     | Passed through to `ReplayPublisher`; also watermark KV key             |
| `fetcher`          | `HistoricalWindowFetcher` | Venue-specific historical source; injected by `ReplayHandler`          |
| `replay_publisher` | `ReplayPublisher`         | UTL publisher with watermark KV wired in                               |
| `vm_name`          | `str`                     | Stamped on emitted lifecycle events for traceability                   |
| `correlation_id`   | `str`                     | UUID4 per replay run; threads through every published event            |
| `coverage_limit`   | `datetime \| None`        | If set and `end > coverage_limit`, backstop halts the loop             |

`run()` is synchronous; `ReplayHandler` invokes it via `asyncio.to_thread` to avoid blocking the event loop.

**Lifecycle events** emitted by `ReplayRunner.run()`:

- `MTDS_REPLAY_STARTED` — INFO at loop entry, includes `start`, `end`, `backstop_truncated`
- `REPLAY_BACKSTOP_REACHED` — WARNING when coverage limit hit (before finalize call)
- `MTDS_REPLAY_COMPLETED` — INFO at loop exit, includes `windows_processed`, `backstop_reached`

### HistoricalWindowFetcher Protocol + InstrumentWindowData

```python
@runtime_checkable
class HistoricalWindowFetcher(Protocol):
    def fetch_window(
        self,
        *,
        asset_group: str,
        venue: str,
        data_type: str,
        period_start: datetime,
        period_end: datetime,
    ) -> Sequence[InstrumentWindowData]: ...

@dataclass(frozen=True)
class InstrumentWindowData:
    instrument_id: str
    instrument_type: str | None
    chain: str | None
    tick_count: int   # 0 is valid — source returned zero for the window
```

Empty return from `fetch_window` means no instruments have data for the boundary — NOT an error. `tick_count=0` is also
valid: the runner publishes a `CandleBoundaryCrossedEvent` with `tick_count=0` so MDPS can emit a zero-activity bar per
the writegate Cat A/D split. The protocol is `runtime_checkable` so the runner can assert the fetcher at construction.

### Per-venue factory registry

`HISTORICAL_WINDOW_FETCHER_FACTORIES` in `replay_handler.py` is a
`dict[str, Callable[[str, str, str], HistoricalWindowFetcher]]` keyed by canonical venue name. It is **empty at Phase
7** (the registry scaffolding shipped but no implementations yet). Per-venue implementations ship with Phase 3.5 in the
same rollout order as `WS_FEED_CONNECTOR_FACTORIES`: DeFi → CeFi spot/perp → CeFi options/futures → TradFi → Sports →
Prediction.

If a venue is requested that is not registered, `_resolve_fetcher()` raises `NotImplementedError` with the rollout-stage
hint rather than silently skipping — consistent with the honest-absence workspace rule.

### CLI integration (ReplayHandler)

`ReplayHandler` extends UTL `BaseModeHandler` and is invoked via `--mode replay`. Accepted args:

| Flag                      | Default                         | Notes                                            |
| ------------------------- | ------------------------------- | ------------------------------------------------ |
| `--shard-spec ag:v:dt`    | required                        | Same format as `--operation websocket-streaming` |
| `--start <ISO>`           | required                        | UTC-aware ISO-8601 replay window start           |
| `--end <ISO>`             | required                        | UTC-aware ISO-8601 replay window end             |
| `--shard-key <key>`       | `ag.venue.data_type`            | Watermark KV key; caller can override            |
| `--base-timeframe <tf>`   | `1m`                            | Aligned boundary step                            |
| `--coverage-limit <ISO>`  | unset (no backstop)             | Emits `REPLAY_BACKSTOP_REACHED` if `end` exceeds |
| `--correlation-id <uuid>` | `uuid.uuid4()` (auto-generated) | Threads through all emitted events               |

`validate_config()` enforces that `streaming_redis_url` is set — replay cannot run without a Redis Stream endpoint.

### Throughput benchmarks

⏳ **PENDING production run** — benchmarks will be added after Phase 7 deploys. Tracked in
`live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 14 item 2. Placeholder targets (to be validated):

| Scenario                      | Estimated wall-clock     | Bottleneck                     |
| ----------------------------- | ------------------------ | ------------------------------ |
| 1h gap, DeFi, single shard    | TBD (pending production) | `fetch_window` (REST throttle) |
| 6h gap, CeFi spot, 10 shards  | TBD (pending production) | Redis XADD throughput          |
| 24h backstop (coverage limit) | TBD (pending production) | Historical-source rate limit   |

---

## Why a separate process

Three reasons:

1. **MTDS is busy with live websockets** — bolting replay onto the same process means a heavy historical fetch (e.g. 24h
   Databento backfill) competes with the websocket reader's tick-buffering deadline.
2. **Replay shard atom matches batch backfill** — the per-asset_group v5 SSOT shard atom; convenient to launch one
   replay VM per shard slice without coupling to the live VM's connection-pool concerns.
3. **Operator visibility** — replay VMs have a distinct VM-name prefix (`replay-`), distinct event correlation, and
   distinct Health-API readouts. Conflating them with live VMs would make the data-status tab less interpretable.

## Contract — what replay must preserve

- **Same Redis Stream contract** as live: `streaming.{asset_group}.candle_boundary_crossed` +
  `streaming.{asset_group}.candle_computed`.
- **Original-time `available_at`** stamped per row (NOT replay-execution time). The live pipeline's `available_at`
  semantic is "when MTDS would have actually had the row in live mode, given the source priority entry's emission
  delay." Replay must reproduce that — otherwise downstream `LookaheadBiasError` checks fail and reconciliation diverges
  from batch.
- **`pipeline_mode=live_websocket`** on the parquet output — the CURRENT transitional behavior (see the SUPERSEDED
  banner above): the M1 target stamps `replay_<source>` (a REAL mode, distinguishable for the audit trail while still
  unioned by readers per M4 precedence); the writer flip rides the gated `M1-BREAKING` tranche.
- **Same shard atomicity contract** — one parquet per shard, one `record_captured` per shard, cluster validation
  preserved for bundled shards.

## Smooth handoff

```
Replay producer (per shard):
  publish_window(t0)
  publish_window(t1)
  ...
  publish_window(t_n)         # t_n = now - epsilon
  finalize(target_period_end=t_n)
       └─ ReplayWatermarkKV.set("replay_watermark.{ag}.{shard_key}", t_n)

Live producer (same shard):
  on every aligned boundary, before publishing:
    if period_end <= ReplayWatermarkKV.get(shard_key):
        skip   # replay owns this window
    else:
        publish_window(period_end)
```

Result: consumer sees a continuous stream from `t-N` (replay) through `t_n` to `t_n+timeframe` (live) with no gap and no
duplicate. The watermark KV is the only coordination point.

## Multi-hour-outage backstop

Replay can't always catch up. If the gap window exceeds the historical-source coverage limit (e.g. exchange REST
snapshot only retains 24h, Databento has a fetch-throttle ceiling), the replay finalizer halts at the coverage limit +
emits `REPLAY_BACKSTOP_REACHED{shard_key, attempted_window, coverage_limit}`. alerting-service routes this to a CRITICAL
alert + a manual-intervention gate on strategy-service: operator must explicitly resume after batch backfill catches up.
Auto-recovery is intentionally NOT in scope for the May-23 cutover (per
[`../04-architecture/autonomous-recovery-matrix.md`](../04-architecture/autonomous-recovery-matrix.md) — auto-recovery
ships post-cutover for known transient failure classes).

## Watermark KV semantics

- One key per shard: `replay_watermark.{asset_group}.{shard_key}`.
- Value: ISO timestamp of the last `period_end` replay finalized.
- TTL: optional 7d (auto-expire prevents stale watermarks blocking live indefinitely if the replay process crashes
  mid-finalize without resetting the key).
- Live publisher reads the key on every aligned boundary check; if missing or expired, no replay in flight, live
  publishes normally.

## Operational pattern

- Replay launchers: `deployment-service/scripts/vm/launch-replay-cascade.sh` parameterised by
  `--asset-group <ag> --shard-key <key> --start <ISO> --end <ISO>`.
- VM naming: `replay-{asset_group}-{shard_key_short_hash}-{ts}` per workspace VM-naming convention.
- VM_PREFIX_TO_BUCKET: register `replay-` prefix so zombie watchdog covers replay VMs.
- Singleton-lock pattern OPTIONAL — replay VMs may run concurrently for different shards; same-shard replay is
  idempotent via the watermark KV (a duplicate replay of an already-finalized window is a no-op).
- Dry-run mode: `--dry-run` lets operator verify the replay window + estimated wall-clock without publishing events.

## Scenario overlay on replay

Scenario overlays compose with the replay subsystem for batch backtest runs: replay re-drives historical windows through
the prod pipeline; a `ScenarioOverlay` is applied at the selected tap layer on top of the replayed events.

**Composition contract:**

1. `ReplayPublisher` writes events with `pipeline_mode=live_websocket` (transitional — `replay_<source>` under the M1
   target, see the banner above) and the original-time `available_at`.
2. `ScenarioOverlayApplier` intercepts events at the configured `ScenarioOverlayLayer` (e.g., `ORDER` pre-cutover;
   `RAW_TICK` / `FEATURE` post-cutover) _after_ replay has emitted the canonical row — same hook location as in a live
   run.
3. `synthetic=true` is stamped on every mutated row so the alerting-service suppresses paging and the operator dashboard
   can distinguish scenario-fire from historical-real rows.
4. `scenario_id` is threaded through the scenario run's `ScenarioReport` parquet (per-row `scenario_id` column) —
   attribution is unambiguous even when a replay window covers multiple scenarios sequentially.

**Ordering invariant**: replay watermark KV check runs before the scenario overlay hook. A scenario mutation never
affects the watermark write; `REPLAY_BACKSTOP_REACHED` halts the replay before any overlay is applied, preserving the
honest-absence guarantee.

**Batch-backtest pattern** (`ScenarioMatrixRunner`):

```
launch replay VM (shard, start, end)
    ↓
ReplayPublisher re-drives events at original-time available_at
    ↓
ScenarioOverlayApplier.apply() at ORDER tap layer (pre-cutover)
    ↓
execution-service matching-engine-mode processes mutated order book
    ↓
ScenarioReport parquet emitted per cell (archetype × scenario_id)
```

Post-cutover: additional tap layers (RAW_TICK, FEATURE) compose the same way — replay precedes overlay; watermark KV is
unaffected. Full post-cutover scope tracked in
[`simulation_scenarios_post_cutover_2026_06_01.md`](../../plans/active/simulation_scenarios_post_cutover_2026_06_01.md).

## Anti-patterns

- Don't stamp a COARSE `pipeline_mode=replay` (no source). The M1 target is the source-aware `replay_<source>`; until
  the gated `M1-BREAKING` tranche flips the writers, output rides the transitional `pipeline_mode=live_websocket` alias.
  (SUPERSEDES the prior "don't introduce `pipeline_mode=replay_*` at all" rule — that contradicted M1; see the banner
  above.)
- Don't auto-recover from `REPLAY_BACKSTOP_REACHED` for May-23 cutover — manual gate. Auto-recovery is post-cutover.
- Don't run replay at the same time as MTDS-live for the same shard without watermark KV — race condition produces
  double-publish. Always go through `ReplayPublisher` which checks the KV.
- Don't stamp `available_at` to replay-execution-time. Original-time only.

## Cross-references

- Plan:
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)
  Phase 7 (replay subsystem) + Phase 2C (UTL replay-cascade helpers).
- Sibling: [`live-pipeline-architecture.md`](./live-pipeline-architecture.md).
- Scenario injection:
  [`../04-architecture/scenario-injection-architecture.md`](../04-architecture/scenario-injection-architecture.md) —
  overlay layer enum + composition contract.
- Foundation: [`../04-architecture/autonomous-recovery-matrix.md`](../04-architecture/autonomous-recovery-matrix.md).
