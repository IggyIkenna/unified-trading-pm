---
doc_type: codex-ssot
title: Live data persistence and central event log
summary: >-
  SSOT for the live=batch event-log persistence spine — MTDS/MDPS/features/strategy/ml/execution all publish/read via
  the UTL EventTransport facade (InMemoryTransport for paper, Pub/Sub for live), three automatic persistence tiers
  (hot/warm/cold) classified by SINK_MATRIX + RetentionClass, giving paper(W)==batch-rerun(W) trade-for-trade
  determinism (epsilon=0); Pub/Sub topics, pull readers, warm-GCS subscriptions, and daily compaction are provisioned
  in Terraform.
  Shard/topic counts drift as connectors are added — verify against the live SINK_MATRIX/Terraform before citing an
  exact number (see § SINK_MATRIX below).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [deployment-service, e2e-testing, execution-service, strategy-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: [live-trading, event-log, pipeline-mode, reconciliation, data-pipeline, mtds, mdps]
related:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/04-architecture/batch-live-architecture.md,
  ]
created: 2026-06-26
authoritative_for:
  [
    live=batch event-log persistence spine (hot/warm/cold tiers + SINK_MATRIX + EventTransport facade),
    paper==batch-rerun determinism proof,
  ]
referenced_by:
  [
    /codex/05-infrastructure/pubsub-topic-inventory.md,
    /plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md,
    /plans/audit/results/vm_deployment_events_audit_2026_05_15.md,
    plans/archive/2026_08/issues/live_mode_event_sink_topic_missing_2026_06_21.md,
    plans/archive/issues/mtds_plan_reconciliation_2026_06_29.md,
  ]
owner:
last_reviewed: 2026-08-21
code_refs:
---

# Live data persistence and central event log

## Problem solved

Before this system: MTDS wrote ticks to GCS on the hot path (in-place overwrite per window per instrument); MDPS read
from that GCS path on every candle boundary. This coupled persistence to the live pipeline and broke `paper==batch`
determinism (GCS contents could change between write and read).

## Architecture

```
MTDS live tick → CanonicalPersistEnvelope(source=MTDS) → UTL facade publish()
MDPS → UTL facade read() → tick payload_inline → OHLCV aggregate → CanonicalPersistEnvelope(source=MDPS) → UTL facade publish()
features → UTL facade read() → execution FeatureTickSubscriber → QuoteMaintainer
strategy AtomicInstruction → UTL facade publish() → execution StrategyInstructionSubscriber → Instruction → ExecutionOrchestrator
strategy/ml/execution → UTL facade read() → process → UTL facade publish()
```

### Three persistence tiers (automatic via SINK_MATRIX)

| Tier | Mechanism                                    | Freshness | Use                        |
| ---- | -------------------------------------------- | --------- | -------------------------- |
| Hot  | InMemoryTransport (paper) / Pub/Sub (live)   | ~ms       | Real-time signal           |
| Warm | Cloud Storage subscription → GCS (hive)      | ~5min     | Recent replay, BQ query    |
| Cold | Daily compaction Cloud Run Job → GCS parquet | ~1d       | Long-term replay, archival |

BQ external table = view over warm GCS (no BQ subscription, no second copy, no ingest cost).

### RetentionClass

- `REPRODUCIBLE` — data can be re-derived from upstream; finite cold TTL (per SINK_MATRIX)
- `STREAM_ONLY` — system of record; cold GCS forever, `cold_ttl_days=None`

Execution fills/positions/PnL/paper_ledger and strategy-emitted `atomic_instruction` envelopes are `STREAM_ONLY`.
All market-data and derived-feature shards are `REPRODUCIBLE` unless their SINK_MATRIX entry says otherwise.

### SINK_MATRIX

`unified_api_contracts.events.sink_matrix.SINK_MATRIX` — keyed by `(asset_group, data_type)`. Wildcard `"*"` in
asset_group matches any. `sinks_for()` raises `KeyError` on unknown shard (no silent default). The matrix is the machine-readable source of truth; its entry set grows as new connectors go live, so verify the live
file rather than copying a fixed count into this document.

### EventTransport (UTL facade)

`unified_trading_library.streaming.event_facade`:

- `InMemoryTransport` — paper/colocated (same code path → determinism)
- `RedisStreamTransport` — existing Redis Streams wrapper
- `PubSubTransport` — live Pub/Sub via the UTL `MessageBus` abstraction; publishes to the shard topic and pulls from
  the corresponding `-reader` subscription
- `publish(envelope, transport?)` / `read(asset_group, data_type, after?, transport?)` — module-level API

## Determinism guarantee

`paper(W) == batch-rerun(W)` trade-for-trade (epsilon=0):

- Paper: `InMemoryTransport` filled by live MTDS→MDPS writes
- Batch-rerun: same facade `read()` against cold GCS (via transport swap)
- Same `CanonicalPersistEnvelope` schema → no format drift

Proven in `e2e-testing/tests/unit/test_live_persist_determinism.py` (4 tests):

1. `test_paper_equals_batch_rerun_trade_for_trade` — 7-window candle spine, epsilon=0
2. `test_faithful_copy_three_tier_read_agreement` — Pub/Sub seek == warm GCS == cold GCS
3. `test_lifecycle_reproducible_vs_stream_only` — REPRODUCIBLE finite TTL; STREAM_ONLY none
4. `TestSinkMatrixCompleteness` (`test_matrix_is_non_empty`/`test_all_explicit_entries_resolve`/
   `test_wildcard_entries_resolve_for_sample_asset_groups`) — SINK_MATRIX completeness gate (test name corrected
   2026-08-12; the doc previously cited a `test_sink_matrix_covers_all_52_shards` name that no longer exists in
   `unified-api-contracts/tests/unit/test_persist_envelope.py`)

The strategy/execution seam is also proven in
`e2e-testing/tests/unit/test_atomic_instruction_live_routing_seam.py`: the publish-side
`publish_atomic_instruction()` writes a real envelope to `InMemoryTransport`, and the execution-side
`route_atomic_instructions()` reads it and drives `AtomicLegExecutor` to a settlement report. The deployed
`execution-service` entrypoint additionally starts `StrategyInstructionSubscriber` and `FeatureTickSubscriber` in
its `api.main` lifespan; both retain per-shard cursors and are cancelled during shutdown.

## Topic naming

One Pub/Sub topic per shard `(asset_group, data_type)`. Wildcard shards use topic `persist-all-{data_type}`; the
atomic-instruction execution reader uses concrete topics `persist-{asset_group}-atomic-instruction` with the matching
`-reader` subscription for `cefi`, `defi`, and `prediction`. Retention is 1d for REPRODUCIBLE and 3d for STREAM_ONLY
cold seeding; the warm GCS subscription is the durable copy.

## Terraform provisioning

The `deployment-service/terraform/gcp/live_event_log/` module provisions the wildcard/declared Pub/Sub sink topics and
their Cloud Storage subscriptions (warm GCS). `strategy_atomic_instruction.tf` additionally provisions concrete
asset-group atomic-instruction topics, execution-reader subscriptions, warm-GCS subscriptions, and matching BigQuery
external tables because `PubSubTransport` publishes and reads `persist-{asset_group}-*` names.

- BigQuery external tables + daily compaction Cloud Run Job deployed in
  `deployment-service/terraform/gcp/live_event_log/`.

## Live transport selection boundary

The Pub/Sub transport implementation and production resources are real, but `get_transport()` with no topology argument
intentionally returns `InMemoryTransport`. The strategy publish helpers and `execution_service.api.main` currently rely
on that default unless a caller explicitly injects `get_transport("pubsub")` or a `PubSubTransport`. The landed subscriber
and startup work therefore proves the shared contract and the in-memory round trip; it does not by itself prove that the
deployed strategy and execution entrypoints exchange instructions over Pub/Sub. Verify topology selection/injection
separately before claiming production inter-service delivery.

## Cross-references

- SINK_MATRIX definition: `unified_api_contracts/events/sink_matrix.py`
- UTL facade: `unified_trading_library/streaming/event_facade.py`
- Terraform infra: `deployment-service/terraform/gcp/live_event_log/`
- Batch==live reconciliation: `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`
- Pipeline mode partition: `/codex/02-data/pipeline-mode-partition.md`
- Pipeline mode + batch/live reconciliation: `/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`
- Durable operational-data tables (BigQuery, not the event log itself) + their DuckDB-over-`bq extract` analysis path:
  `/codex/05-infrastructure/deployment-observability.md`
