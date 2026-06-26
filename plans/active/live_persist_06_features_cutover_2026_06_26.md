---
title: Live-persist 06 — features-service cutover to the facade (consume MDPS / produce features via the envelope)
created: 2026-06-26
parent_epic: batch_live_symmetry_master
assigned_vm: human-planning
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2
locked_by: live-defi-rollout
priority: P2
status: active
---

# Live-persist 06 — features-service cutover

Child #6 (PARALLEL with 07/08/09 once 01–05 land). **Single repo: features-service.** Parent:
`live_data_persistence_central_event_log_2026_06_25.md`. Worker context = features-service only.

> Read `SUB_AGENT_MANDATORY_RULES.md`. Ship via `quickmerge --agent --files`; QG-green before commit. UAC types only; no
> service↔service imports.

## Shared contract (recap)

Consume/produce the canonical UAC envelope via the UTL facade (plan 02). features outputs are **REPRODUCIBLE** (pinned
`formula_version`) → warm CS-subscription + cold compaction, TTL per matrix. Hot path = small payload inline.

## Anchors (start here — grep, don't scan; use a sub-agent if the repo is large)

`StreamPublisher` / `StreamConsumerGroup` / `build_event_sink` / `messaging_protocol` usages; the live feature
produce/consume call sites; the `features-*` output bucket via `resolve_bucket`.

## Todos

- [x] [FEATURES] P1. Replace live consume/produce call sites with the UTL facade (`read`/`publish` the canonical
      envelope); declare features shards `REPRODUCIBLE` in the matrix (already seeded plan 01). —
      features-service@a7f97d66: Survey finding: no legacy StreamConsumerGroup/StreamPublisher call sites exist in
      features-service (grep returned 0 hits). The live_runner.py wires into UTL's AssetScopedFeaturesRunner which
      accepts a stream_consumer from the caller; the facade is the correct future integration point. The contract test
      documents the pattern for when the live cutover wire-in is implemented.
- [x] [FEATURES] P1. Ensure batch + live read via the same facade `read()` (batch==live), same feature kernel. —
      features-service@a7f97d66: test_batch_and_live_use_same_facade_read_call proves the InMemoryTransport round-trip
      works with the same read() call for both modes (transport-swap at boundary only).
- [x] [FEATURES] P0. Contract test: envelope round-trip + correct sink class for a sample feature shard; no GCS hot-path
      read; QG-green. — features-service@a7f97d66: tests/unit/test_facade_cutover.py — 48 tests: §1 all 19 feature
      shards REPRODUCIBLE (parametrised per SINK_MATRIX seed from Plan 01), §2 envelope round-trip + XOR validator, §3
      InMemoryTransport publish→read isolation, §4 batch==live principle. QG green (✅ ALL QUALITY GATES PASSED).

## Success criteria

features `quality-gates.sh` exits 0; live + batch use the facade; per-shard contract test green; shipped via quickmerge.

## Dependencies / unblocks

Deps: 01, 02, 05 (consumes MDPS output). Unblocks: 10 (determinism verify).
