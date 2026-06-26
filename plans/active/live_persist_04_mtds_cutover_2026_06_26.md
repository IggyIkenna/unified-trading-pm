---
title: Live-persist 04 — MTDS producer cutover (publish envelope via facade; retire the per-window overwrite write)
created: 2026-06-26
parent_epic: batch_live_symmetry_master
assigned_vm: human-planning
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2
locked_by: live-defi-rollout
priority: P1
status: active
---

# Live-persist 04 — MTDS cutover

Child #4. **Single repo: market-tick-data-service.** Parent: `live_data_persistence_central_event_log_2026_06_25.md`.
Worker context = MTDS only.

> Read `SUB_AGENT_MANDATORY_RULES.md`. Ship via `quickmerge --agent --files`; QG-green before commit. UAC types only; no
> service↔service imports.

## Shared contract (recap)

Publish the canonical UAC envelope via the UTL facade (plan 02). Warm GCS now comes from the Cloud Storage subscription
(plan 03), cold from daily compaction — so the producer **stops writing GCS in-place**. Hot path carries the small
bar/aggregate inline; raw firehose persists via the sink only.

## Anchors (start here — don't scan the whole repo)

`market_tick_data_service/live/websocket_runner.py` — `LiveWebsocketRunner`, `LiveWebsocketTickSink.flush` (`:155-181`,
the per-window overwrite), `live_tick_blob_path`, `StreamPublisher` usage. `live/backfill_runner.py`
(`_tick_sink.flush`). Batch writer path (for the batch==live same-store assertion).

## Todos

- [ ] [MTDS] P0. On each closed window boundary, **publish the canonical envelope via the UTL facade** (payload inline)
      instead of the bespoke `StreamPublisher` signal. Pipeline_mode/source/period from the existing window.
- [ ] [MTDS] P0. **Retire `LiveWebsocketTickSink`'s in-place GCS write** (the `{instrument_id}.parquet` overwrite) —
      warm GCS is now the Cloud Storage subscription; delete the dead path (no parallel old+new). Confirm the manifest
      honest-coverage still records correctly off the new flow.
- [ ] [MTDS] P0. Assert the **batch path writes the SAME cold hive-parquet shape** the compaction produces (batch==live
      one store) — adjust the batch writer's path/layout if it diverges.
- [ ] [MTDS] P0. Tests: envelope published per window (mocked facade); no GCS write remains in the live producer;
      batch + live write identical hive layout.

## Success criteria

MTDS `quality-gates.sh` exits 0; live ticks flow to the topic → warm GCS via subscription; **no per-window overwrite
remains**; batch/live layouts identical; shipped via quickmerge.

## Dependencies / unblocks

Deps: 01 (envelope), 02 (facade), 03 (topics+sink). Unblocks: 05 (MDPS consumes the MTDS envelope).
