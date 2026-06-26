---
title: Live-persist 00 — pre-audit live transport/persistence + seed the SINK_MATRIX classification
created: 2026-06-26
parent_epic: batch_live_symmetry_master
assigned_vm: human-planning
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2
locked_by: live-defi-rollout
priority: P1
status: active
---

# Live-persist 00 — pre-audit + SINK_MATRIX seed

Child #0 of the central-event-log spine. **Foundation — must land before plans 01–10.** Parent (architecture + DAG):
`live_data_persistence_central_event_log_2026_06_25.md`; problem record:
`issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md`.

> **Sonnet-safety (large codebase):** this is READ-ONLY across 9 repos → **fan out one sub-agent per repo** (paste
> `SUB_AGENT_MANDATORY_RULES.md` at the top of each; each returns ≤400 tokens of findings). Do NOT load all repos into
> one context. Output is a doc, no code.

## Shared contract (recap — keep self-contained)

- Central log = GCP Pub/Sub, topic per shard `(asset_group, data_type, stage)`, SHORT retention (~1–3d).
- Canonical UAC envelope (`unified_api_contracts.events`):
  `schema_version, asset_group, data_type, pipeline_mode, period_start, period_end, source, available_at, retention_class, payload|pointer`
  (generalises the existing `CandleBoundaryCrossedEvent`/`CandleComputedEvent`).
- `SINK_MATRIX[(asset_group,data_type)]` →
  `{retention_class: REPRODUCIBLE|STREAM_ONLY, sinks{hot,gcs_warm,table}, warm_ttl_days≈7, cold_lifecycle}`. Persistence
  = ONE warm Cloud-Storage-subscription sink + BQ external-table view + daily cold compaction (no Redis, no BQ
  subscription).

## Todos

- [x] [AUDIT] P0. Map the CURRENT live transport + persistence end-to-end (one sub-agent per repo): MTDS
      `LiveWebsocketRunner` + `LiveWebsocketTickSink.flush` (per-window overwrite, `websocket_runner.py:155-181`) +
      `live_tick_blob_path`; UAC `events/streaming.py` (`CandleBoundaryCrossedEvent`/`CandleComputedEvent`); UTL
      `streaming/` (`StreamPublisher`/`StreamConsumerGroup`/`build_event_sink`/`messaging_protocol`); MDPS
      `live_aggregator.py` `_MDPSTickFetcher` (hot-path GCS read) + `orchestration_scanner`; and every live-mode
      produce/consume call site in features / strategy / ml / execution. Repo: unified-trading-pm (audit doc) +
      read-only across the 9 repos. — unified-trading-pm@pending
      `plans/audit/results/live_persist_00_audit_2026_06_26.md`
- [x] [AUDIT] P0. Classify EVERY live `(asset_group, data_type)` shard → `{retention_class, sinks{hot,gcs_warm,table}}`.
      **REPRODUCIBLE** = re-fetchable externally or re-derivable from a retained+pinned upstream (Databento OHLCV, MDPS
      candles, features, ML preds); **STREAM_ONLY** = no external backfill or our own emitted state (prediction CLOB
      depth, live L2/L3, instantaneous funding, execution fills/positions/PnL + paper ledger). Mark `table:` default-on
      EXCEPT the raw firehose (full L2 / L3 MBO → GCS-only) — this resolves **D3**. State sampled-vs-walked. Repo:
      unified-trading-pm. — D3 firehose list = EMPTY (MTDS produces windowed ticks only, no L2/L3 MBO); all shards
      `table: true`
- [x] [AUDIT] P0. Confirm how much of the STREAM_ONLY irreproducible class (execution fills/positions/PnL + paper
      ledger) ALREADY lands durably on the UAC global ledger (`canonical.crosscutting.ledger`), so plan 09's scope is
      "declare `stream_only` + reconcile," not "re-persist." Repo: execution-service + unified-api-contracts (read). —
      FINDING: 0 hits on canonical.crosscutting.ledger in execution-service; fills go to direct GCS only; Plan 09 scope
      = facade consume + declare SO + wire publish() path (not just ledger annotation)

## Success criteria

Audit doc in `plans/audit/results/` with: the transport/persistence manifest, the full per-shard classification table
(the SINK_MATRIX seed plan 01 encodes), the firehose opt-out list (D3), and the execution-ledger coverage finding.
States where it sampled vs walked.

## Dependencies / unblocks

Deps: none (foundation). Unblocks: 01 (UAC matrix), 03 (infra topic list), 09 (execution scope).
