---
scope: [engineer, admin]
---

# Replay Subsystem

> **STATUS** — covers the replay process that fills gap windows when the live pipeline loses data (intraday VM restart,
> websocket disconnect exceeding reconnect grace, cluster bounce). Designed alongside the live-pipeline activation for
> 2026-05-23. Full work plan in
> [`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md)
> Phase 7. If this doc disagrees with the active plan, the plan wins.

## TL;DR

Separate process replays gap windows by reading historical batch sources (Databento / Tardis / exchange REST snapshot)
and emitting events through the SAME Redis Streams the live pipeline uses. Downstream MDPS / features-service consumers
don't know or care whether an event is replay or live — only the timestamps differ. Smooth handoff to live via per-shard
`replay_watermark.{asset_group}.{shard_key}` Redis KV.

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
- **`pipeline_mode=live_websocket`** on the parquet output (NOT a `replay_*` mode). The output is indistinguishable from
  a true live capture, which is the point — replay is filling a gap that should have been live.
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

## Anti-patterns

- Don't introduce `pipeline_mode=replay`. Output goes to `pipeline_mode=live_websocket`. Replay vs live is operational,
  not data-shape.
- Don't auto-recover from `REPLAY_BACKSTOP_REACHED` for May-23 cutover — manual gate. Auto-recovery is post-cutover.
- Don't run replay at the same time as MTDS-live for the same shard without watermark KV — race condition produces
  double-publish. Always go through `ReplayPublisher` which checks the KV.
- Don't stamp `available_at` to replay-execution-time. Original-time only.

## Cross-references

- Plan:
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md)
  Phase 7 (replay subsystem) + Phase 2C (UTL replay-cascade helpers).
- Sibling: [`live-pipeline-architecture.md`](./live-pipeline-architecture.md).
- Foundation: [`../04-architecture/autonomous-recovery-matrix.md`](../04-architecture/autonomous-recovery-matrix.md).
