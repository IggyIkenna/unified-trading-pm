# Live data persistence and central event log

## Problem solved

Before this system: MTDS wrote ticks to GCS on the hot path (in-place overwrite per window per instrument); MDPS read
from that GCS path on every candle boundary. This coupled persistence to the live pipeline and broke `paper==batch`
determinism (GCS contents could change between write and read).

## Architecture

```
MTDS live tick → CanonicalPersistEnvelope(source=MTDS) → UTL facade publish()
MDPS → UTL facade read() → tick payload_inline → OHLCV aggregate → CanonicalPersistEnvelope(source=MDPS) → UTL facade publish()
features/strategy/ml/execution → UTL facade read() → process → UTL facade publish()
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

Execution fills/positions/PnL/paper_ledger are `STREAM_ONLY`. All market-data and derived-feature shards are
`REPRODUCIBLE`.

### SINK_MATRIX

`unified_api_contracts.events.sink_matrix.SINK_MATRIX` — 52 entries keyed by `(asset_group, data_type)`. Wildcard `"*"`
in asset_group matches any. `sinks_for()` raises `KeyError` on unknown shard (no silent default).

### EventTransport (UTL facade)

`unified_trading_library.streaming.event_facade`:

- `InMemoryTransport` — paper/colocated (same code path → determinism)
- `RedisStreamTransport` — existing Redis Streams wrapper
- `PubSubTransport` — live Pub/Sub (stub pending full provisioning)
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
4. `test_sink_matrix_covers_all_52_shards` — SINK_MATRIX completeness gate

## Topic naming

One Pub/Sub topic per shard `(asset_group, data_type)`. Wildcard shards use topic `persist-all-{data_type}`. Retention
1d (REPRODUCIBLE) to 3d (STREAM_ONLY cold seeding); warm GCS subscription is the durable copy.

## Terraform provisioning

52 Pub/Sub topics + Cloud Storage subscriptions (warm GCS) + BigQuery external tables + daily compaction Cloud Run Job
deployed in `deployment-service/terraform/gcp/live_event_log/`.

## Cross-references

- SINK_MATRIX definition: `unified_api_contracts/events/sink_matrix.py`
- UTL facade: `unified_trading_library/streaming/event_facade.py`
- Terraform infra: `deployment-service/terraform/gcp/live_event_log/`
- Batch==live reconciliation: `codex/09-strategy/operational/paper-batch-live-reconciliation.md`
- Pipeline mode partition: `codex/02-data/pipeline-mode-partition.md`
- Pipeline mode + batch/live reconciliation: `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`
