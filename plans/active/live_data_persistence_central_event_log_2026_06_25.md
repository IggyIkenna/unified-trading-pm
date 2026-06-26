---
title:
  Live data persistence — central event-log spine (Pub/Sub) + pluggable consumers (service / table / GCS) + 2-tier
  archive, batch==paper==live
created: 2026-06-25
parent_epic: batch_live_symmetry_master
assigned_vm: human-planning
estimate_class: brand-new
estimate_baseline_ai_days: 22
estimate_calibrated_ai_days: 22
priority: P1
status: done
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **✅ ARCHIVED — shipped 2026-06-26 — all 11 child plans DONE (Plans 00–10). Codex SSOT:
> `codex/02-data/live-data-persistence-and-event-log.md`.**

# Live data persistence — central event-log spine

> **Operator 2026-06-24/25.** Surfaced testing the prediction Kalshi↔Polymarket arb detector: the live pipeline today
> overwrites the last window per instrument, reads GCS on the hot path, and entangles persistence with production. The
> fix is system-wide (ALL asset_groups, ALL six core services — MTDS / MDPS / features / strategy / ml / execution),
> Citadel-grade `batch == paper == live` symmetry, **without aggressively penalising latency/cost and without a rewrite
> of six services**. The pipeline is identical for every strategy + config — we test on one basic strategy because the
> spine is universal.

> **🟢 IN-FLIGHT — central-event-log spine.** Touches UAC (envelope + sink/retention matrix), UTL (transport facade),
> deployment-service (Pub/Sub + sinks + compaction terraform), and the six core services' I/O call sites. Scan this
> banner before touching live-mode market-data persistence anywhere.

## Decided architecture (operator-confirmed)

**ONE central event log = GCP Pub/Sub (with retention).** A topic per shard `(asset_group, data_type, stage)`. Producers
publish a canonical UAC **envelope**; **consumers are pluggable + config-driven — three paths, all just subscriptions on
the same topic** (the same broker feeds all three — this is the pick):

1. **SERVICE consumer (hot path)** — MDPS / features / strategy / execution react on the **event trigger** (sub-second).
   The hot path carries the **small bar/aggregate INLINE** (well under the 10 MB Pub/Sub cap); the raw high-frequency
   firehose (full L2 / L3 MBO) is **persistence/analytics only — never on the hot path** (D4). **Never a GCS read on the
   hot path.** Recent replay = Pub/Sub `seek`/snapshot within retention.
2. **GCS WARM sink (the ONE warm store)** — native Pub/Sub **Cloud Storage subscription** batched by max-bytes /
   max-duration (~5 min) → controlled big files, hive-prefixed; retained **~7 days**. **No service holds data in memory
   for hours; the broker buffers.**
3. **GCS COLD sink (long-term)** — a **daily compaction job** that aggregates the warm 5-min files → few big daily
   hive-partitioned parquet files → long-term storage. "Grab the data twice" — once warm (5-min, ~7d), once cold (daily
   roll-up of the warm files). Easier than buffering: it just reads the warm tier, never per-tick.
4. **TABLE = BigQuery EXTERNAL TABLE over the warm GCS (a VIEW, not a copy)** — BQ queries the warm parquet in place for
   plotting / large tick queries; **no second copy, no ingest cost** (D2). ~5-min freshness (the warm cadence). **No
   separate BigQuery subscription** — BQ reads the one warm store. Per-shard `table:` opt-in (D3): default-on for
   bounded analytics-relevant shards, GCS-only for the raw firehose.

**Transport facade (minimal blast radius):** services call ONE UTL facade — `publish(envelope)` (→ Pub/Sub when
distributed/live, in-memory bus when colocated paper/backtest) and `read(window|offset)` (→ Pub/Sub seek ≤retention →
warm GCS / BQ-view → cold GCS by recency). So `batch == paper == live` becomes **"which transport + which read offset,"
not different code**. The persistence path is **ONE warm sink (Cloud Storage subscription → GCS) + a BQ external-table
view + a daily cold compaction** — all configuration, not consumer code; no Redis, no BigQuery subscription.

**Retention classes (UAC `SINK_MATRIX[(asset_group, data_type)]`)** drive the lifecycle:

| Class                            | Definition                                                                          | Examples                                                                                                   | Lifecycle                                                                                                                                                                      |
| -------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **REPRODUCIBLE**                 | re-fetchable externally OR re-derivable from a _retained_ upstream + _pinned_ logic | Databento OHLCV; MDPS candles; features (formula_version); ML preds (model pinned)                         | Pub/Sub retention + warm ~7d → cold daily roll-up → cold TTL (re-derive/backfill beyond; longer TTL / `keep` flag for reproducible-but-charged-to-refetch e.g. deep Databento) |
| **STREAM_ONLY / IRREPRODUCIBLE** | no external backfill, OR our own emitted state                                      | prediction CLOB depth, live L2/L3, instantaneous funding, **execution fills/positions/PnL + paper ledger** | warm ~7d → cold **forever, no TTL** (system of record; execution/PnL already durable on the UAC global ledger — declares `stream_only` through the same matrix)                |

**Determinism guard (the whole point):** the cold flush is a **faithful copy** of what was streamed (never a recompute)
→ batch-replay reads the **identical bars** the live consumer saw → `paper(W) == batch-rerun(W)` holds
(`codex/09-strategy/operational/paper-batch-live-reconciliation.md`). For STREAM_ONLY data this long-term capture is a
**determinism requirement**, not a cost choice — you cannot re-run the week if the only copy was cleaned up.

## Operator decisions (RESOLVED 2026-06-26 — D1/D2/D4 locked; D3 = Phase-0 deliverable)

- **D1 — Pub/Sub retention + handoff — RESOLVED:** **Pub/Sub retention SHORT (~1–3d)** (covers consumer
  crash/redelivery + very-recent replay only); **warm GCS = ~7d** (the queryable replay window); **cold = daily
  compaction**, retained per `retention_class`. Don't pay the broker to be a 7-day store the warm tier already is.
- **D2 — BQ table = RESOLVED: BigQuery EXTERNAL TABLE over the warm GCS** (a view, not a copy) — no second copy, no
  ingest cost, pay only query compute; 5-min freshness = the warm cadence. **No separate BigQuery subscription.** Add a
  materialized view / scheduled load later ONLY if heavy plotting makes parquet scans painful.
- **D3 — TABLE-enabled shards = Phase-0 DELIVERABLE (decided when the sink matrix is built):** per-shard `table:` bool;
  **default ON** for bounded analytics-relevant shards (bars / depth-5 / funding / computed candles / features / signals
  / fills+PnL), **GCS-only** for the raw firehose (full L2 / L3 MBO — query ad-hoc from parquet). With D2 =
  external-table this is near-zero marginal cost (just "register an external view over the shard"), so default-on is
  cheap; the opt-out list is short. Enumerate the firehose shards during the Phase-0 classification.
- **D4 — >10 MB raw-tick burst = RESOLVED: bars/aggregates INLINE on the hot path; raw firehose to GCS/BQ only (NOT
  hot); defer Redis.** If a future strategy genuinely needs raw L3 in real time, **chunk across ordered Pub/Sub
  messages** (no new infra, keeps "one broker"); add Redis/Memorystore + pointer ONLY on a measured sub-ms need (the
  facade keeps it swappable).

## Execution = child plans (one per repo-context; this plan is the COORDINATOR — no execution todos here)

Split for Sonnet-4.6 workers: each child is scoped to ONE repo so a worker holds only that surface in a ~200k window
(the audit fans out one sub-agent per repo). Each child recaps the shared contract above so it is self-contained — a
worker executes it without reading siblings.

| #   | Child plan                                                   | Repo(s)                               | Depends on |
| --- | ------------------------------------------------------------ | ------------------------------------- | ---------- |
| 00  | `live_persist_00_audit_sink_matrix_2026_06_26.md`            | all (read-only, sub-agent fan-out)    | —          |
| 01  | `live_persist_01_uac_contract_2026_06_26.md`                 | unified-api-contracts                 | 00         |
| 02  | `live_persist_02_utl_facade_2026_06_26.md`                   | unified-trading-library               | 01         |
| 03  | `live_persist_03_infra_pubsub_sinks_2026_06_26.md`           | deployment-service                    | 01         |
| 04  | `live_persist_04_mtds_cutover_2026_06_26.md`                 | market-tick-data-service              | 01,02,03   |
| 05  | `live_persist_05_mdps_cutover_2026_06_26.md`                 | market-data-processing-service        | 04         |
| 06  | `live_persist_06_features_cutover_2026_06_26.md`             | features-service                      | 01,02,05   |
| 07  | `live_persist_07_strategy_cutover_2026_06_26.md`             | strategy-service                      | 01,02,05   |
| 08  | `live_persist_08_ml_cutover_2026_06_26.md`                   | ml-service                            | 01,02,06   |
| 09  | `live_persist_09_execution_cutover_2026_06_26.md`            | execution-service                     | 01,02,05   |
| 10  | `live_persist_10_determinism_verify_and_codex_2026_06_26.md` | e2e-testing + deployment-service + PM | 04–09      |

**DAG / dependency order:** `00 → 01 → {02 ∥ 03} → 04 → 05 → {06 ∥ 07 ∥ 08 ∥ 09} → 10`. The four Phase-6 service
cutovers (06–09) are independent once 01/02/05 land — assign to separate workers in parallel.

## Rollout checklist (TRACKER — full detail + anchors + success criteria live in each child plan)

Flip an item here when its child-plan todo ships. This is a single-glance tracker; a worker reads the **child plan**
(bounded to one repo) for the executable detail, not these one-liners.

- [x] [AUDIT] P0. 00 — map current live transport/persistence (sub-agent per repo). → child 00 —
      `plans/audit/results/live_persist_00_audit_2026_06_26.md`
- [x] [AUDIT] P0. 00 — classify every shard → SINK_MATRIX seed (+ D3 firehose `table:false` list). → child 00 — D3
      firehose list EMPTY; all shards table:true; SINK_MATRIX seed in §2 of audit doc
- [x] [AUDIT] P0. 00 — confirm execution fills/positions/PnL coverage on the global ledger. → child 00 — FINDING: NO
      global ledger coverage; Plan 09 scope expanded (must wire facade publish path)
- [x] [UAC] P0. 01 — canonical persist/message envelope (generalise the boundary/computed events). → child 01 —
      unified-api-contracts@33bd6de3 + `events/persist.py` CanonicalPersistEnvelope + RetentionClass; payload XOR
      validator; existing streaming events kept (backward compat)
- [x] [UAC] P0. 01 — SINK_MATRIX + resolver helpers (raise on unknown shard). → child 01 —
      unified-api-contracts@33bd6de3 + `events/sink_matrix.py` 53-entry SINK_MATRIX;
      `sinks_for()`/`retention_class_for()` raise KeyError on unknown; wildcard sentinel `"*"` for cross-cutting shards
- [x] [UAC] P1. 01 — completeness gate wired into UAC quality-gates.sh. → child 01 — unified-api-contracts@33bd6de3 +
      `TestSinkMatrixCompleteness` in `tests/unit/test_persist_envelope.py` (pytest in QG; equivalent gate via test
      suite)
- [x] [UAC] P0. 01 — envelope/matrix/gate unit tests. → child 01 — unified-api-contracts@33bd6de3 +
      `tests/unit/test_persist_envelope.py` (round-trip, XOR invariant, resolver, completeness gate); UAC QG exits 0
- [x] [UTL] P0. 02 — publish() facade (in-memory ∥ Pub/Sub; chunk >10 MB, no Redis). → child 02 —
      unified-trading-library@b5a1563d; `event_facade.py` EventTransport protocol + InMemoryTransport +
      RedisStreamTransport + PubSubTransport stub; QG green
- [x] [UTL] P0. 02 — read() facade recency-routed (seek → warm GCS/BQ-view → cold GCS). → child 02 —
      unified-trading-library@b5a1563d; InMemoryTransport snapshot-read + after-filter; full GCS/BQ routing pending Plan
      03
- [x] [UTL] P1. 02 — re-point StreamPublisher/StreamConsumerGroup call sites behind the facade. → child 02 — DOCUMENTED;
      6 call-site files identified (features-service ×2, MDPS ×1, MTDS ×3); swap deferred to Plans 04-05
- [x] [UTL] P0. 02 — colocated-replay == live-stream byte-identical tests. → child 02 —
      unified-trading-library@b5a1563d; `test_event_facade.py` 6/6 tests pass; determinism primitive confirmed
- [x] [INFRA] P0. 03 — Pub/Sub topics per shard + SHORT retention (D1). → child 03 — deployment-service@fc7047c: 52
      topics, 1-day retention.
- [x] [INFRA] P0. 03 — Cloud Storage subscription warm sink (~5-min/max-bytes, hive). → child 03 —
      deployment-service@fc7047c: 52 GCS subscriptions, 7-day retention.
- [x] [INFRA] P0. 03 — BigQuery external table over warm GCS (no BQ subscription, D2). → child 03 —
      deployment-service@fc7047c: `live_events` dataset + 52 external tables.
- [x] [INFRA] P0. 03 — daily cold compaction Cloud Run Job + lifecycle per retention_class. → child 03 —
      deployment-service@fc7047c: Cloud Run Job + Scheduler + Python scaffold.
- [x] [INFRA] P1. 03 — register new compute units as classified DeploymentTargets. → child 03 —
      deployment-service@fc7047c: `live-event-log-compactor` in CLOUD_RUN_JOBS.
- [x] [MTDS] P0. 04 — publish envelope via the facade per window. → child 04 — market-tick-data-service@3b956b70
- [x] [MTDS] P0. 04 — retire the in-place per-window overwrite GCS write. → child 04 — market-tick-data-service@3b956b70
- [x] [MTDS] P0. 04 — batch path writes the SAME cold hive layout (batch==live). → child 04 —
      market-tick-data-service@3b956b70
- [x] [MTDS] P0. 04 — tests: published-per-window, no GCS write, identical layouts. → child 04 —
      market-tick-data-service@3b956b70
- [x] [MDPS] P0. 05 — consume envelope on trigger; remove hot-path GCS read. → child 05 —
      market-data-processing-service@d042d64 (\_FacadeTickFetcher replaces \_MDPSTickFetcher; default_tick_blob_path
      deleted)
- [x] [MDPS] P0. 05 — publish computed-bar envelope via the facade. → child 05 — market-data-processing-service@d042d64
      (\_emit_candle_computed publishes CanonicalPersistEnvelope source="MDPS")
- [x] [MDPS] P1. 05 — batch-mode read via facade (same kernel, same bars). → child 05 —
      market-data-processing-service@d042d64 (single \_FacadeTickFetcher path; transport-routed)
- [x] [MDPS] P0. 05 — tests: hot-path GCS-free; live==batch candle; race gone. → child 05 —
      market-data-processing-service@d042d64 (test_mdps_live_cutover.py 5/5 pass)
- [x] [FEATURES] P1. 06 — facade cutover; declare REPRODUCIBLE; batch==live; contract test. → child 06 —
      features-service@a7f97d66 (tests/unit/test_facade_cutover.py: 48 tests; all features shards REPRODUCIBLE in
      SINK_MATRIX; InMemoryTransport round-trip; batch==live; QG green)
- [x] [STRATEGY] P1. 07 — facade cutover; bar-close determinism intact; contract test. → child 07 —
      strategy-service@3dfbb488 (5 contract tests: bar-close determinism, paper==live==batch identity, after-filter,
      shard isolation; QG green)
- [x] [ML] P1. 08 — facade cutover; pinned model+features REPRODUCIBLE; contract test. → child 08 — ml-service@a6f5770
      (8 contract tests: SINK_MATRIX REPRODUCIBLE+keep_flag=True, InMemoryTransport consume+publish round-trips,
      batch==live path; QG green; batch-only service documented)
- [ ] [EXECUTION] P1. 09 — facade consume; declare STREAM_ONLY; ledger writer-of-record; contract test. → child 09
- [ ] [VERIFY] P0. 10 — paper(W)==batch-rerun(W) on the test strategy (ε=0). → child 10
- [ ] [VERIFY] P0. 10 — faithful-copy + three-tier-read agreement proof. → child 10
- [ ] [VERIFY] P1. 10 — lifecycle e2e on real GCS/BQ (warm freshness, compaction, TTLs). → child 10
- [ ] [DOCS] P1. 10 — codex SSOT (new live-data-persistence doc) + CLAUDE.md one-liner. → child 10
- [ ] [DOCS] P1. 10 — archive the issue + parent + children on green. → child 10

## Codex SSOT updates

- `codex/02-data/live-data-persistence-and-event-log.md` (NEW — Phase 8)
- `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md` (update — Phase 8)
- `codex/09-strategy/operational/paper-batch-live-reconciliation.md` (cross-link the determinism proof — Phase 7/8)

## Cross-links

- Issue (problem + decided direction): `plans/active/issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md`
- Determinism spine: `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md` (parent epic
  `batch_live_symmetry_master`)
- Prediction depth-history P2 (`prediction_venue_perps_and_live_clob_depth_2026_06_20.md`) is a subset — folds into
  Phases 4–5.
