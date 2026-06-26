---
title: Live-persist 02 — UTL transport facade (publish/read; in-memory ↔ Pub/Sub; recency-routed read)
created: 2026-06-26
parent_epic: batch_live_symmetry_master
assigned_vm: human-planning
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3
locked_by: live-defi-rollout
priority: P1
status: active
---

# Live-persist 02 — UTL facade

Child #2. **Single repo: unified-trading-library.** Parent: `live_data_persistence_central_event_log_2026_06_25.md`.
Worker context = UTL only. PARALLEL with 03.

> Read `SUB_AGENT_MANDATORY_RULES.md`. Ship via `quickmerge --agent --files`; QG-green before commit. No `os.getenv`;
> cloud-agnostic clients only.

## Shared contract (recap)

Facade is the ONE I/O surface every service calls so `batch==paper==live` = "which transport + which read offset." The
envelope + `SINK_MATRIX` live in UAC (plan 01). Transports: in-memory bus (colocated paper/backtest) + Pub/Sub
(distributed live). Read tiers by recency: Pub/Sub `seek` (≤short retention) → warm GCS / BQ-view → cold GCS.

## Todos

- [ ] [UTL] P0. `publish(envelope)` facade in `unified_trading_library/streaming/` — impl-selected by runtime topology
      (mirror the existing `build_event_sink` / `runtime.messaging_protocol`): **in-memory bus** when colocated,
      **Pub/Sub** when distributed. Payload inline; chunk across ordered messages if >10 MB (D4 — no Redis).
- [ ] [UTL] P0. `read(shard, window|offset)` facade — recency-routed: Pub/Sub `seek` (≤retention) → warm GCS / BQ-view →
      cold GCS; returns the identical envelope/bar stream regardless of tier (the batch==live read primitive). GCS reads
      via `cloud_interface` + `resolve_bucket_name`.
- [ ] [UTL] P1. Re-point the existing `StreamPublisher`/`StreamConsumerGroup` call sites behind the facade (Redis stays
      a swappable impl, NOT the default). Keep public API stable for service call sites (those swap in plans 04–10).
- [ ] [UTL] P0. Unit tests: in-memory publish→read round-trip; **colocated-replay == live-stream byte-identical** on a
      fixture week (the determinism primitive); recency routing picks the right tier per offset.

## Success criteria

UTL `quality-gates.sh` exits 0; facade unit tests green incl. the byte-identical replay; no service-logic change (UTL
internals + shims only); shipped via quickmerge.

## Dependencies / unblocks

Deps: 01 (envelope). Unblocks: 04–10 (services call the facade). Pairs with 03 (infra provides the real Pub/Sub/GCS the
Pub/Sub impl targets).
