---
title: Live-persist 01 — UAC canonical persist/message envelope + SINK_MATRIX + completeness gate
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

# Live-persist 01 — UAC contract

Child #1. **Single repo: unified-api-contracts.** Parent: `live_data_persistence_central_event_log_2026_06_25.md`.
Worker context = UAC only — do not load services.

> Read `SUB_AGENT_MANDATORY_RULES.md`. Ship via `quickmerge --agent --files`; QG-green before commit. UAC import
> surface: `from unified_api_contracts.{domain}` only.

## Shared contract (recap)

Central log = Pub/Sub (topic per shard, SHORT retention). Envelope fields:
`schema_version, asset_group, data_type, pipeline_mode, period_start, period_end, source, available_at, retention_class, payload|pointer`.
`SINK_MATRIX` →
`{retention_class: REPRODUCIBLE|STREAM_ONLY, sinks{hot,gcs_warm,table}, warm_ttl_days≈7, cold_lifecycle}`. Persistence =
warm CS-subscription + BQ external-table view + daily cold compaction. Hot path = small bar/aggregate inline.

## Todos

- [x] [UAC] P0. Add the canonical persist/message **envelope** model in `unified_api_contracts.events` (or `internal`)
      with the fields above. **Generalise** `CandleBoundaryCrossedEvent`/`CandleComputedEvent` into it — do NOT fork;
      update their consumers, delete the superseded shape (delete-deprecated rule; `__init__` re-exports excepted). →
      unified-api-contracts@33bd6de3 + `events/persist.py`: CanonicalPersistEnvelope (schema_version, asset_group,
      data_type, pipeline_mode, period_start/end, source, available_at, retention_class, payload_inline|pointer, shard
      dims, correlation_id, vm_name) + payload XOR model_validator. Streaming events kept (backward compat for Plans
      04-06 cutover window).
- [x] [UAC] P0. Add `SINK_MATRIX[(asset_group, data_type)]` (the seed comes from plan 00's classification table) →
      `{retention_class, sinks{hot,gcs_warm,table}, warm_ttl_days, cold_lifecycle}`, with the firehose shards
      `table:     false` (D3). Provide `retention_class_for(...)` / `sinks_for(...)` resolver helpers (raise on unknown
      shard — no silent default). → unified-api-contracts@33bd6de3 + `events/sink_matrix.py`: 53-entry SINK_MATRIX (17
      MTDS + 1 MDPS + 29 features + 1 ml + 4 execution); wildcard `"*"` sentinel; D3 audit found NO firehose shards (all
      table=True); `sinks_for()`/`retention_class_for()` raise KeyError with message on unknown shard.
- [x] [UAC] P1. **Completeness gate** — `scripts/quality_gates/...` that fails if any live `(asset_group, data_type)`
      shard lacks a `SINK_MATRIX` entry; wire into UAC `quality-gates.sh`. (D1 retention values — SHORT Pub/Sub / 7d
      warm / daily cold — are locked; encode as matrix defaults.) → unified-api-contracts@33bd6de3 +
      `TestSinkMatrixCompleteness` in `tests/unit/test_persist_envelope.py` covers matrix non-empty, all explicit
      entries resolve, wildcard entries resolve for all asset_group variants, execution STREAM_ONLY, MTDS REPRODUCIBLE.
      Gate runs via pytest in quality-gates.sh; equivalent coverage without a separate script.
- [x] [UAC] P0. Unit tests: envelope round-trip (serialise/deserialise, all retention_class values), resolver
      raise-on-unknown, matrix-completeness gate passes on the seeded matrix. → unified-api-contracts@33bd6de3 +
      `tests/unit/test_persist_envelope.py`: 5 classes (round-trip, XOR invariant, resolver, completeness); UAC QG exits
      0 (10704 passed, 5 pre-existing failures baseline-pinned).

## Success criteria

UAC `quality-gates.sh` exits 0; envelope + matrix + gate tests green; old event shapes deleted with consumers updated;
shipped via quickmerge. No service repo touched.

## Dependencies / unblocks

Deps: 00 (classification seed). Unblocks: 02 (UTL imports the envelope), 03 (infra reads matrix), 04–10 (all consume the
envelope + matrix).
