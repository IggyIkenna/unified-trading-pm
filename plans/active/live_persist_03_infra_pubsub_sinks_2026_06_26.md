---
title:
  Live-persist 03 — infra — Pub/Sub topics + Cloud Storage subscription (warm) + BQ external table + daily cold
  compaction
created: 2026-06-26
parent_epic: batch_live_symmetry_master
assigned_vm: human-planning
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3
locked_by: live-defi-rollout
priority: P1
status: active
---

# Live-persist 03 — infra (Pub/Sub + sinks + compaction)

Child #3. **Single repo: deployment-service** (terraform + a Cloud Run Job). Parent:
`live_data_persistence_central_event_log_2026_06_25.md`. Worker context = deployment-service only. PARALLEL with 02.

> Read `SUB_AGENT_MANDATORY_RULES.md`. VM/job launchers + terraform live in deployment-service. GCS ops via UTL
> `cloud_interface` (no gsutil/`google.cloud` direct); `resolve_bucket_name`; env-short buckets; UTC. Every compute unit
> = a classified `DeploymentTarget`.

## Shared contract (recap)

ONE warm sink = Pub/Sub **Cloud Storage subscription** → GCS (~5-min / max-bytes batched, hive-prefixed); **BQ external
table** is a view over that warm GCS (NO BigQuery subscription, D2); **daily compaction** rolls warm 5-min files → cold
long-term parquet. Pub/Sub message retention SHORT ~1–3d (D1); warm GCS TTL ~7d; cold lifecycle per `retention_class`
(TTL for REPRODUCIBLE, none for STREAM_ONLY).

## Todos

- [ ] [INFRA] P0. Terraform Pub/Sub topics per shard `(asset_group, data_type, stage)` (topic list derived from the UAC
      `SINK_MATRIX`) + **SHORT message retention (~1–3d, D1)**.
- [ ] [INFRA] P0. Terraform native **Cloud Storage subscription** (the warm sink) for `gcs_warm`-enabled shards: ~5-min
      / max-bytes batching, parquet, hive prefix `…/pipeline_mode=…/asset_group=…/venue=…/data_type=…/day=…/` via the
      per-shard topic; GCS lifecycle TTL ~7d on the warm prefix.
- [ ] [INFRA] P0. **BigQuery external table** over the warm GCS for `table:`-enabled shards (D2 — view, not a copy; no
      BQ subscription).
- [ ] [INFRA] P0. **Daily compaction** Cloud Run Job + Scheduler: read the warm 5-min files → write cold long-term hive
      parquet (few big files) → run BEFORE the warm-TTL expiry; apply cold lifecycle per `retention_class` (TTL
      REPRODUCIBLE, none STREAM_ONLY). GCS ops via UTL `cloud_interface`.
- [ ] [INFRA] P1. Register the compaction job (+ the subscriptions if surfaced) as classified `DeploymentTarget`s
      (`classify_deployment_target` + `cloud_run_job_registry`) so deployment-observability + Slack cover them.

## Success criteria

`terraform plan/apply` clean; a synthetic publish to a test topic lands in warm GCS (right hive path) + is queryable via
the BQ external table; the daily compaction produces cold parquet + applies lifecycle; deployment-ui `/deployments`
shows the new targets; QG-green; shipped via quickmerge.

## Dependencies / unblocks

Deps: 01 (matrix → topic/sink list). Unblocks: 04 (MTDS publishes to real topics), 10 (lifecycle verify).
