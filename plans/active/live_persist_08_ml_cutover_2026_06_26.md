---
title: Live-persist 08 — ml-service cutover to the facade (consume features / produce predictions via the envelope)
created: 2026-06-26
parent_epic: batch_live_symmetry_master
assigned_vm: human-planning
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
locked_by: live-defi-rollout
priority: P2
status: completed
---

# Live-persist 08 — ml-service cutover

Child #8 (PARALLEL with 06/07/09 once 01–05 land). **Single repo: ml-service.** Parent:
`live_data_persistence_central_event_log_2026_06_25.md`. Worker context = ml-service only.

> Read `SUB_AGENT_MANDATORY_RULES.md`. Ship via `quickmerge --agent --files`; QG-green before commit. Lazy-import heavy
> ML deps inside methods (never module-level). UAC types only; no service↔service imports.

## Shared contract (recap)

Consume/produce the canonical UAC envelope via the UTL facade (plan 02). ML predictions are **REPRODUCIBLE** with a
pinned model + pinned feature inputs → warm CS-subscription + cold compaction, TTL per matrix.

## Anchors (start here — grep, sub-agent if large)

The live feature-consume + prediction-emit call sites; `StreamConsumerGroup`/`build_event_sink`/`messaging_protocol`
usages; the `ml-predictions-store` bucket via `resolve_bucket`.

## Todos

- [x] [ML] P1. Replace live consume (features) + predict-emit call sites with the UTL facade (canonical envelope);
      declare ml-pred shards `REPRODUCIBLE` (model+feature pins recorded so re-derivation is exact). —
      ml-service@a6f5770; ml-service is batch-only (no live Redis/PubSub). Contract test proves the InMemoryTransport
      facade paths (consume + publish) work for both live and batch modes via the same code; SINK_MATRIX wired with
      REPRODUCIBLE + keep_flag=True.
- [x] [ML] P1. Batch + live read via the same facade `read()` (batch==live), same model path. — ml-service@a6f5770;
      `test_batch_equals_live_same_facade_path` proves byte-identical replay.
- [x] [ML] P0. Contract test: envelope round-trip + correct sink class; no GCS hot-path read; QG-green. —
      ml-service@a6f5770; 8/8 tests pass: `tests/inference/unit/test_facade_contract.py`; QG ALL QUALITY GATES PASSED;
      no GCS reads (InMemoryTransport only).

## Success criteria

ml `quality-gates.sh` exits 0; live + batch via the facade; contract test green; shipped via quickmerge.

## Dependencies / unblocks

Deps: 01, 02, 06 (consumes features). Unblocks: 10.
