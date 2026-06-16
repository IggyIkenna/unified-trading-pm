---
scope: [engineer, admin]
title: ML Lifecycle — Model Registry, Inference, and Deployment
updated: 2026-05-15
owner: topology_qgroup_gap_closure_2026_05_09 Phase 2
closes: GAP-7, GAP-8
last_reviewed: 2026-05-17
---

# ML Lifecycle — Canonical Decisions

## 1. Model Registry SSOT

`ModelArtifactRegistry` (UAC `unified_api_contracts.internal`) is the canonical record for every deployed model
artifact. Fields: `model_id`, `model_family`, `asset_group`, `version`, `gcs_uri`, `trained_at`, `is_active`,
`archetype`, `paper_snapshot_version`, `live_hot_reload_cadence_days`.

ml-inference-service MUST read from this registry at startup + on the hot-reload cadence to resolve the active artifact
GCS URI. Direct GCS path lookup without registry is banned.

## 2. Paper-Snapshot Semantics

When a paper trading run starts, the orchestrator calls `freeze_model_artifact(strategy_id, model_id)` which writes
`paper_snapshot_version = <current version>` to the registry record. The paper run uses this frozen version for its
entire lifetime — no hot-reloads during a paper run. This preserves reproducibility: replay of the same paper run
re-loads the same artifact version.

## 3. Live Hot-Reload Cadence

Default: weekly (`live_hot_reload_cadence_days = 7`). Per-archetype override in `StrategyConfig.ml_reload_cadence_days`.
Hot-reload is atomic: new model loaded + validated on shadow traffic before the primary pointer is swapped. On
validation failure the old model stays active and an alert is emitted.

## 4. Monolithic ML Cluster — May-23 Decision

**Decision (2026-05-15)**: The ML cluster ships May-23 as a single monolithic service instance (one ml-inference-service
process, all asset_groups served by the same process). Per-asset-group sharding (separate inference processes per
cefi/defi/tradfi/sports/prediction) is explicitly deferred to post-cutover. Rationale: latency SLA (p99 ≤ 200ms) is
achievable with a single process at May-23 traffic volumes; sharding adds operational complexity that risks the May-23
date.

This decision is locked until the post-cutover sharding plan is written and approved.

> **[DELTA 2026-05-22]** **Current state:** Monolithic ml-inference-service instance ships for the May-23 cutover (all
> asset_groups in one process). Per-asset-group sharding is not implemented. **Planned delta:** Post-cutover sharding
> plan to be written and approved; tracked in `plans/epics/features_and_ml_master.md`. **Target architecture:** Separate
> ml-inference-service processes per asset_group (cefi/defi/tradfi/sports/prediction) with per-asset-group model
> registries and hot-reload isolation.

## 5. Batch Inference Cadence — per-bar Replay

Batch inference MUST use per-bar replay — `predict()` is called exactly once per bar at the bar's `available_at`
timestamp. Vectorized daily pass (compute all predictions at once) is banned because it violates the "Batch = Live, only
fill source differs" invariant: live inference is per-tick, not vectorized.

The `available_at` timestamp on the feature record is the authoritative clock for when inference is permitted. Inference
for bar T must not use features with `available_at > T`.

## 6. Latency SLA

p99 inference latency ≤ 200ms per signal, measured at the strategy-service boundary (time from feature-vector assembly
to `MLPrediction` available). Enforced by:

1. pytest in `strategy-service/tests/integration/test_ml_inference_latency_sla.py`
2. Grafana alert: `ml_inference_latency_p99_ms > 200` fires `ML_INFERENCE_LATENCY_BREACH`

Alert code `ML_INFERENCE_LATENCY_BREACH` is declared in UAC `canonical/crosscutting/alerting/codes.py` (existing).
