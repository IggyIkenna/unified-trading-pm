---
title: Live-persist 05 — MDPS hot-path cutover (consume envelope on trigger; drop the hot-path GCS read; kill the race)
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

# Live-persist 05 — MDPS cutover

Child #5. **Single repo: market-data-processing-service.** Parent:
`live_data_persistence_central_event_log_2026_06_25.md`. Worker context = MDPS only.

> Read `SUB_AGENT_MANDATORY_RULES.md`. Ship via `quickmerge --agent --files`; QG-green before commit.

## Shared contract (recap)

MDPS consumes the MTDS envelope **on the Pub/Sub trigger with payload inline** — NO GCS read on the hot path (that read
is what created the per-window overwrite race). Batch-mode MDPS reads via the facade `read()` (cold GCS). Same
aggregation kernel both modes.

## Anchors (start here)

`market_data_processing_service/app/core/live_aggregator.py` — the boundary-event consumer, `_MDPSTickFetcher` (the
hot-path GCS read via `default_tick_blob_path(event)`), `MDPSStreamingAggregator`, the `candle_computed` publish.
`app/core/orchestration_scanner.py` — the batch poll path.

## Todos

- [ ] [MDPS] P0. Consume the MTDS envelope via the UTL facade on the **event trigger**; aggregate from the **inline
      payload**. **Remove `_MDPSTickFetcher`'s hot-path GCS read** entirely.
- [ ] [MDPS] P0. Publish the computed-bar envelope to the MDPS output topic via the facade (replacing the bespoke
      `CandleComputedEvent` publish — use the canonical envelope).
- [ ] [MDPS] P1. Batch-mode MDPS reads via the facade `read()` (cold GCS) — same `MDPSStreamingAggregator` kernel, same
      bars (batch==live).
- [ ] [MDPS] P0. Tests: hot path touches NO GCS (mock facade, assert no `cloud_interface` read); live candle == batch
      candle for the same window window (determinism probe); a lagged consumer no longer mis-reads (race gone).

## Success criteria

MDPS `quality-gates.sh` exits 0; hot path GCS-free; live==batch candle for a sample window; the overwrite race is
structurally impossible (no shared mutable blob); shipped via quickmerge.

## Dependencies / unblocks

Deps: 04 (MTDS publishes the envelope). Unblocks: 06 (features), 07 (strategy) — they consume MDPS output.
