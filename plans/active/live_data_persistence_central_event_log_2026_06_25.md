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
locked_by: live-defi-rollout
priority: P1
status: active
---

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

1. **SERVICE consumer (hot path)** — MDPS / features / strategy / execution react on the **event trigger** (sub-second),
   payload INLINE on the envelope (small bars/aggregates fit the 10 MB cap; a rare >10 MB raw-tick burst uses a fast
   hot-cache or chunking — **never a GCS read on the hot path**). Recent replay = Pub/Sub `seek`/snapshot within
   retention.
2. **TABLE sink** — native Pub/Sub **BigQuery subscription** (no consumer code) → a **warm** queryable BQ table for
   plotting / large tick queries. ~5-min freshness; retained ~7 days. (NOT per-event streaming inserts.)
3. **GCS sink — TWO tiers (operator 2026-06-25):**
   - **WARM (Tier 1, ~5-min):** native Pub/Sub **Cloud Storage subscription** batched by max-bytes / max-duration (~5
     min) → controlled big files, hive-prefixed. BQ queries off this; retained ~7 days. **No service holds data in
     memory for hours; the broker buffers.**
   - **COLD (Tier 2, long-term):** a **daily compaction job** that aggregates the warm 5-min files → few big daily
     hive-partitioned parquet files → long-term storage. "Grab the data twice" — once warm (5-min, BQ-queryable, ~7d),
     once cold (daily roll-up of the warm files). Easier than buffering: it just reads the warm tier, never per-tick.

**Transport facade (minimal blast radius):** services call ONE UTL facade — `publish(envelope)` (→ Pub/Sub when
distributed/live, in-memory bus when colocated paper/backtest) and `read(window|offset)` (→ Pub/Sub seek ≤retention → BQ
warm → cold GCS by recency). So `batch == paper == live` becomes **"which transport + which read offset," not different
code**. Persistence sinks (BQ + GCS) are **native Pub/Sub subscriptions = configuration, not code**.

**Retention classes (UAC `SINK_MATRIX[(asset_group, data_type)]`)** drive the lifecycle:

| Class                            | Definition                                                                          | Examples                                                                                                   | Lifecycle                                                                                                                                                                      |
| -------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **REPRODUCIBLE**                 | re-fetchable externally OR re-derivable from a _retained_ upstream + _pinned_ logic | Databento OHLCV; MDPS candles; features (formula_version); ML preds (model pinned)                         | Pub/Sub retention + warm ~7d → cold daily roll-up → cold TTL (re-derive/backfill beyond; longer TTL / `keep` flag for reproducible-but-charged-to-refetch e.g. deep Databento) |
| **STREAM_ONLY / IRREPRODUCIBLE** | no external backfill, OR our own emitted state                                      | prediction CLOB depth, live L2/L3, instantaneous funding, **execution fills/positions/PnL + paper ledger** | warm ~7d → cold **forever, no TTL** (system of record; execution/PnL already durable on the UAC global ledger — declares `stream_only` through the same matrix)                |

**Determinism guard (the whole point):** the cold flush is a **faithful copy** of what was streamed (never a recompute)
→ batch-replay reads the **identical bars** the live consumer saw → `paper(W) == batch-rerun(W)` holds
(`codex/09-strategy/operational/paper-batch-live-reconciliation.md`). For STREAM_ONLY data this long-term capture is a
**determinism requirement**, not a cost choice — you cannot re-run the week if the only copy was cleaned up.

## Open decisions (operator gates — resolve at the marked phase)

- **D1 (Phase 1):** Pub/Sub retention window — 7d vs longer — and the warm-GCS → cold-GCS hand-off point.
- **D2 (Phase 3):** BQ warm table = native BigQuery subscription vs external-table over the warm GCS (zero-load, slower
  scans) vs scheduled 5-min load.
- **D3 (Phase 3):** which `(asset_group, data_type)` shards enable the TABLE sink at all (raw high-volume L3 may be
  GCS-only to bound BQ cost — the sink matrix decides per shard).
- **D4 (Phase 2):** hot-cache for the rare >10 MB raw-tick burst — Redis vs chunked Pub/Sub.

## Pre-audit (Citadel standard — MUST precede code)

- [ ] [AUDIT] P0. Map the CURRENT live transport + persistence end-to-end and embed the manifest in this plan: MTDS
      `LiveWebsocketRunner` + `LiveWebsocketTickSink.flush` (the per-window overwrite, `websocket_runner.py:155-181`),
      `live_tick_blob_path` (day+instrument key), `StreamPublisher`/Redis + `CandleBoundaryCrossedEvent` /
      `CandleComputedEvent` (UAC `events/streaming.py`), MDPS `live_aggregator.py` `_MDPSTickFetcher` (hot-path GCS
      read) + `orchestration_scanner` (batch poll). Grep every producer/consumer of these across all 6 services. Repo:
      unified-trading-pm (audit doc) + read-only across services.
- [ ] [AUDIT] P0. Classify EVERY `(asset_group, data_type)` shard into REPRODUCIBLE vs STREAM_ONLY + enabled sinks {hot,
      table, gcs_warm} → the seed for the UAC `SINK_MATRIX`. State where sampled vs walked. Repo: unified-trading-pm.
- [ ] [AUDIT] P0. Confirm exactly how much of the STREAM_ONLY irreproducible class (execution fills/positions/PnL +
      paper ledger) ALREADY lands durably on the UAC global ledger (`canonical.crosscutting.ledger`) — so Phase-0 scope
      is "declare `stream_only` + reconcile," not "re-persist." Repo: execution-service + unified-api-contracts (read).

## Phase 1 — UAC contract (envelope + sink/retention matrix) — no service-logic change

- [ ] [UAC] P0. Canonical persist/message **envelope** in `unified_api_contracts.events` (or `internal`):
      schema_version, asset_group, data_type, pipeline_mode, period_start/end, source, available_at, retention_class,
      payload-or-pointer. Generalises `CandleBoundaryCrossedEvent`/`CandleComputedEvent` (do not fork; extend/replace
      cleanly, delete the old shape per delete-deprecated rule). Repo: unified-api-contracts.
- [ ] [UAC] P0. `SINK_MATRIX[(asset_group, data_type)]` →
      `{retention_class, sinks{hot,table,gcs_warm}, warm_ttl_days,     cold_lifecycle}` from the Phase-0 classification.
      Repo: unified-api-contracts.
- [ ] [UAC] P1. **Completeness gate** — a QG check that every live `(asset_group, data_type)` shard has a `SINK_MATRIX`
      entry (no silent default); wire into UAC `quality-gates.sh`. Resolve **D1**. Repo: unified-api-contracts.
- **Success:** UAC QG green; envelope round-trip + matrix-completeness unit tests pass; no service code changed yet.

## Phase 2 — UTL transport facade (publish / read; in-memory ↔ Pub/Sub) — PARALLEL with Phase 3

- [ ] [UTL] P0. `publish(envelope)` facade — in-memory bus impl (colocated paper/backtest) + Pub/Sub impl (distributed
      live), selected by runtime topology (mirror existing `build_event_sink`/`messaging_protocol`). Resolve **D4**.
      Repo: unified-trading-library.
- [ ] [UTL] P0. `read(shard, window|offset)` facade — recency-routed: Pub/Sub `seek` (≤retention) → warm BQ → cold GCS;
      returns the identical envelope/bar stream regardless of tier (the batch==live read primitive). Repo:
      unified-trading-library.
- [ ] [UTL] P1. Replace the `StreamPublisher`/Redis call sites behind the facade (Redis stays a swappable impl; not the
      default). Unit tests: colocated-replay == live-stream byte-identical on a fixture week. Repo:
      unified-trading-library.
- **Success:** UTL QG green; facade unit tests prove transport-agnostic read; zero service-logic change (only the UTL
  internals + call-site shims).

## Phase 3 — Infra: Pub/Sub topics + native sinks + daily compaction (deployment-service / terraform)

- [ ] [INFRA] P0. Terraform Pub/Sub topics per shard `(asset_group, data_type, stage)` + retention config (per D1).
      Repo: deployment-service.
- [ ] [INFRA] P0. Native **BigQuery subscription** (warm table) for TABLE-enabled shards; resolve **D2**/**D3**. Repo:
      deployment-service.
- [ ] [INFRA] P0. Native **Cloud Storage subscription** (warm GCS, ~5-min / max-bytes batched, hive prefix via per-shard
      topic) for gcs_warm-enabled shards. Repo: deployment-service.
- [ ] [INFRA] P0. **Daily compaction** Cloud Run Job + Scheduler: read warm 5-min files → write cold long-term hive
      parquet (few big files); apply warm TTL (GCS lifecycle) + cold lifecycle per `retention_class` (TTL for
      REPRODUCIBLE, none for STREAM_ONLY); export precedes warm-TTL. GCS ops via UTL `cloud_interface` (no gsutil),
      `resolve_bucket_name`, env-short buckets, UTC. Repo: deployment-service.
- [ ] [INFRA] P1. Register every new compute unit (compaction job + subscriptions) as a classified `DeploymentTarget`
      (`classify_deployment_target` + `cloud_run_job_registry`) so deployment-observability + Slack cover it. Repo:
      deployment-service.
- **Success:** topics + subscriptions live in prod; a synthetic publish lands in warm BQ + warm GCS; daily compaction
  produces cold parquet + applies lifecycle; deployment-ui `/deployments` shows the new targets.

## Phase 4 — MTDS producer cutover (publish envelope; retire the overwrite write)

- [ ] [MTDS] P0. MTDS live producer publishes the canonical envelope via the UTL facade (payload inline). Repo:
      market-tick-data-service.
- [ ] [MTDS] P0. **Retire the in-place per-window overwrite GCS write** — warm GCS now comes from the Cloud Storage
      subscription; cold from compaction. The batch path writes the SAME cold hive parquet shape (batch==live one
      store). Delete the dead `LiveWebsocketTickSink` GCS path (no parallel old+new). Repo: market-tick-data-service.
- **Success:** MTDS QG green; live ticks flow to the topic; warm GCS/BQ populate via subscriptions; NO per-window
  overwrite remains; manifest honest-coverage intact.

## Phase 5 — MDPS hot-path cutover (consume envelope on trigger; drop hot-path GCS read)

- [ ] [MDPS] P0. MDPS consumes the MTDS envelope on the Pub/Sub trigger (payload inline) — **remove the
      `_MDPSTickFetcher` hot-path GCS read**; publish the computed-bar envelope to its output topic via the facade.
      Repo: market-data-processing-service.
- [ ] [MDPS] P1. Batch-mode MDPS reads via the facade `read()` (cold GCS) — same aggregation kernel, same bars. Repo:
      market-data-processing-service.
- **Success:** MDPS QG green; hot path touches no GCS; live candle == batch candle for the same window (determinism
  probe); the overwrite RACE is gone.

## Phase 6 — features / strategy / ml / execution cutover (PARALLEL per service after Phases 1–3)

- [ ] [FEATURES] P1. features consumes/produces envelopes via the facade (REPRODUCIBLE class). Repo: features-service.
- [ ] [STRATEGY] P1. strategy consumes via the facade; signals are bar-close deterministic (benchmark-fill spine
      intact). Repo: strategy-service.
- [ ] [ML] P1. ml preds via the facade (REPRODUCIBLE w/ pinned model+features). Repo: ml-service.
- [ ] [EXECUTION] P1. execution fills/positions/PnL via the facade declaring **STREAM_ONLY**; ledger stays
      writer-of-record (declare, don't re-persist). Repo: execution-service.
- **Success:** each service QG green; per-service contract test asserts envelope round-trip + correct sink class; no
  service↔service Python imports introduced (UAC/UTL only).

## Phase 7 — Determinism verification + analytics + lifecycle (run to completion, real infra)

- [ ] [VERIFY] P0. On the basic test strategy: run a paper week on the live spine, then batch-rerun the SAME week from
      cold GCS — assert `paper(W) == batch-rerun(W)` trade-for-trade (ε=0). Repo: e2e-testing (strategy-service
      QG-wired).
- [ ] [VERIFY] P0. Replay-from-cold == live-streamed bars (faithful-copy proof); recent replay via Pub/Sub seek == warm
      BQ == warm GCS for an overlapping window. Repo: e2e-testing.
- [ ] [VERIFY] P1. Lifecycle end-to-end: warm 5-min freshness in BQ; daily compaction produces cold parquet; warm TTL
      fires AFTER compaction; STREAM_ONLY cold never TTLs; REPRODUCIBLE cold TTLs per matrix. Repo: deployment-service.
- **Success:** determinism proof green on the test strategy; lifecycle verified on real GCS/BQ with sampled parquet.

## Phase 8 — Codex SSOT + CLAUDE.md (HARD RULE — Post-Plan-Phase Codex Audit)

- [ ] [DOCS] P1. New codex SSOT `codex/02-data/live-data-persistence-and-event-log.md` (the spine: central log,
      pluggable consumers, 2-tier GCS, retention classes, determinism). Repo: unified-trading-pm.
- [ ] [DOCS] P1. Update `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md` + the "Live = Batch" /
      determinism-spine references; add a one-liner to CLAUDE.md `§ Live = batch` pointing at the new SSOT. Repo:
      unified-trading-pm.

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
