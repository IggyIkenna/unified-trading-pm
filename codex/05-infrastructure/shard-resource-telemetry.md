---
doc_type: codex-ssot
title: Shard Resource/Cost Telemetry — the ShardRunTelemetry contract (SSOT)
summary: SSOT for the standardised per-shard resource/performance/cost telemetry record every VM, Cloud Run job, and
  pipeline_e2e_check driver emits — the UAC ShardRunTelemetry contract, the UTL ShardTelemetryRecorder emitter, the
  compute_price_table pricing SSOT, the sibling shard-run-telemetry BigQuery landing, the deployment-api query surface,
  and the deployment-ui "Shard capacity & cost" panel.
status: current
nature: ssot
asset_group: [cross-cutting]
stage: [data, meta]
repos: [unified-api-contracts, unified-trading-library, deployment-service, deployment-api, deployment-ui]
scope: [engineer, admin]
tags: [observability, telemetry, cost, capacity, monitoring, billing, benchmark]
related:
  [
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md,
  ]
created: 2026-08-22
owner:
last_reviewed:
code_refs: []
authoritative_for:
  [
    ShardRunTelemetry contract (per-shard resource/cost telemetry row),
    compute_price_table pricing SSOT (GCP/AWS machine types,
    Cloud Run Jobs,
    GCS ops),
    shard-run-telemetry Pub/Sub topic + BigQuery landing table ownership,
  ]
referenced_by: []
supersedes:
superseded_by:
---

# Shard Resource/Cost Telemetry

## What this closes

Before 2026-08-22, nothing recorded per-shard stage timings, bytes, objects, GCS ops or $ anywhere in the pipeline —
`pipeline_e2e_check/report.py` recorded `duration_sec` only, Cloud Run jobs emitted no samples at all, and every
`benchmark` leg's throughput number was hand-computed ad hoc per driver (features-service's `_run_benchmark_leg` even
fabricated a `~25s/shard-day` rate on a leg that exited `-1` with `objects=0` — see the T0 audit in
`/plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md`). This doc is the SSOT for the fix: one
standardised contract every compute unit emits the same way.

## The contract

`unified_api_contracts.internal.shard_run_telemetry.ShardRunTelemetry` — one row per (deployment target, shard,
leg/run). Fields: `target_kind` (VM | CLOUD_RUN_JOB), `target_name`, `service`, `mode` (batch/paper/live), `leg`
(force/skip/benchmark/canonical/pit/live), a `ShardAtom` (asset_group + whichever of venue/instrument_type/data_type/
feature_group+version/timeframe/model_family/slot_label/day apply — unused axes stay `None`), `machine_type` +
`pricing_class` (VM only), `accelerator_type`, `stage_timings` (list/fetch/process/write — the batch15 three-stage
benchmark harness's own vocabulary, plus `list` for manifest/read-set resolution), rows/bytes/objects in+out, GCS
Class A/B op counts, `peak_rss_bytes`, `cpu_pct_avg`/`p95`, `wall_clock_sec`, `usd_estimate`, and `expected_*` twins
(+ `wall_clock_variance_pct` / `usd_variance_pct` properties) for expected-vs-actual comparison.

**Emission**: `unified_trading_library.monitors.ShardTelemetryRecorder` — a context manager (mirrors
`core.performance_monitor.PerformanceContext`'s shape) that times the `with` block, samples RSS/CPU via psutil, counts
GCS ops via `wrap_storage_client()` (a thin counting proxy around a `StorageClient` instance — chosen over
monkeypatching the process-wide `get_storage_client()` cache, which would leak counters across unrelated concurrent
callers), computes `usd_estimate` from `compute_price_table`, and publishes on `__exit__` regardless of success or
failure (the exception, if any, still propagates — the recorder never swallows it).

## Pricing SSOT

`unified_api_contracts.internal.compute_price_table` — every priced compute unit resolves through
`resolve_machine_price()` / `resolve_accelerator_price()` / `resolve_cloud_run_price()` / `resolve_gcs_op_price()`;
an unregistered `machine_type` raises `UnknownMachineTypeError` rather than silently cost-estimating $0. Prices are
**approximate public list prices** (`us-central1` GCP / `us-east-1` AWS), dated by `PRICE_TABLE_VERSION` + each row's
`as_of_date` — a snapshot to make cost ESTIMABLE and STANDARDISED, not a live billing feed; refresh via the GCP Cloud
Billing Catalog API / AWS Price List API in a follow-up rather than trusting the constants indefinitely.
`deployment-service/scripts/quality_gates/check_machine_type_price_coverage.py` fails the gate if a
`launch-*.sh` `MACHINE_TYPE` has no registered price (no ratchet — the fleet is fully priced as of 2026-08-22, so a
new machine type must be priced in the same commit that adds it).

## Landing: a SIBLING of `resource_samples`, not the same topic

**Deviation from the original plan wording**: the plan text said this would publish "onto the existing
`resource-samples` topic ... as a new message kind." A native BigQuery Pub/Sub subscription binds ONE topic to
EXACTLY ONE destination table (`--use-table-schema --drop-unknown-fields`), so a differently-shaped row cannot fan out
of the `resource-samples` topic into a second table. `shard_run_telemetry` therefore gets its own sibling topic,
`shard-run-telemetry` (`deployment-service/scripts/setup-pubsub.sh`'s `TOPIC_REGISTRY` + `BQ_SUBSCRIPTION_REGISTRY`),
landing in `deployment_operational_data.shard_run_telemetry` (`deployment-service/scripts/migrations/self/
bootstrap_operational_data_bq.py` — **Python-bootstrapped, NOT terraform**: `deployment_operational_data` is a
deliberate exception to this repo's otherwise-terraform-managed BigQuery datasets, per `ARCHITECTURE.md`'s
runtime-driven deployment model; see that script's `TABLES` dict for the precedent every entry there follows).
Day-partitioned on `run_started_at`, clustered by `(service, shard_asset_group, mode)`, 90-day retention.

`ShardRunTelemetry.to_publish_dict()` is the ONE place the flattening happens (a native BQ subscription needs a flat
top-level JSON shape, no nested RECORD columns): `shard.<field>` → `shard_<field>`, each present `StageTiming` →
`stage_<stage>_sec`. Mirror this exactly if the BigQuery schema ever changes — the two must stay in lockstep.

## Reading it

`deployment_api/services/operational_data_queries.py::shard_run_telemetry_rolling_sql()` — p50/p95 wall-clock/peak-RSS/
bytes/ops/$ per `(service, shard_asset_group, mode)` over a rolling window, with expected-vs-actual variance computed
in SQL (`SAFE_DIVIDE`), the sibling of `resource_samples_rolling_sql()`. Routed at
`GET /api/vm-resources/shard-telemetry`, surfaced in deployment-ui's "Shard capacity & cost" panel beside the existing
`VmResourceComparison` view. `scripts/cost/shard_cost_model.py` (unified-trading-library) projects N-year totals from
the measured p50 $/shard-day × the honest-coverage expected-universe denominator.

## Reading the UI / rightsizing skill

`vm-resource-rightsizing-check` and `/honest-coverage-dump`-adjacent tooling should read this table (not just
`resource_samples`) once a shard has telemetry history — it is the only place `bytes`/`objects`/GCS-ops/$ per shard
exist; `resource_samples` stays host-level CPU/mem/disk only.
