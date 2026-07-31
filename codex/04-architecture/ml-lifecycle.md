---
doc_type: codex-ssot
title: ML Lifecycle — Model Registry, Inference, and Deployment
summary:
  "Canonical ML lifecycle decisions — ModelArtifactRegistry (UAC) as the model-artifact SSOT read by ml-inference at
  startup / hot-reload, paper-snapshot version freeze for reproducibility, weekly live hot-reload cadence, per-bar batch
  inference replay (vectorized daily pass banned). Latency SLO is owned by the UAC threshold
  ml_inference_latency_p99_ms (500ms), not by this doc."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [ml, strategy, model-tier, features, live-trading, ssot]
related:
  [
    /codex/04-architecture/ml-experiment-lifecycle.md,
    /codex/04-architecture/ml-service-architecture.md,
    /codex/04-architecture/promote-workflow-architecture.md,
    /codex/04-architecture/live-strategy-config-hot-reload.md,
  ]
created: 2026-05-15
authoritative_for:
  [
    ML model-artifact registry SSOT,
    paper-snapshot model freeze semantics,
    live ML hot-reload cadence,
    per-bar batch inference replay rule,
  ]
referenced_by: [/codex/04-architecture/ml-experiment-lifecycle.md, /codex/04-architecture/ml-service-architecture.md]
owner: topology_qgroup_gap_closure_2026_05_09 Phase 2
last_reviewed: 2026-10-09
code_refs:
updated: 2026-05-15
closes: GAP-7, GAP-8
---

# ML Lifecycle — Canonical Decisions

## 1. Model Registry SSOT

`ModelArtifactRegistry` (UAC `unified_api_contracts.internal`) is the canonical record for every deployed model
artifact. Fields: `model_id`, `model_family`, `asset_group`, `version`, `gcs_uri`, `trained_at`, `is_active`,
`archetype`, `paper_snapshot_version`, `live_hot_reload_cadence_days`.

ml-inference-service MUST read from this registry at startup + on the hot-reload cadence to resolve the active artifact
GCS URI. Direct GCS path lookup without registry is banned.

## 2. Paper-Snapshot Semantics

When a paper trading run starts, the orchestrator freezes the artifact by writing
`paper_snapshot_version = <current version>` to the registry record. The paper run uses this frozen version for its
entire lifetime — no hot-reloads during a paper run. This preserves reproducibility: replay of the same paper run
re-loads the same artifact version.

> **Implementation status (verified 2026-07-31):** the `paper_snapshot_version` **field** exists on
> `ModelArtifactRegistry`, but the `freeze_model_artifact(strategy_id, model_id)` helper this section originally named
> is **not implemented** anywhere in the workspace — the freeze is a declared contract, not shipped code. Treat the
> semantics above as the target; do not import a `freeze_model_artifact` symbol.

## 3. Live Hot-Reload Cadence

Default: weekly (`live_hot_reload_cadence_days = 7`, a real field on `ModelArtifactRegistry`). Hot-reload is atomic: new
model loaded + validated on shadow traffic before the primary pointer is swapped. On validation failure the old model
stays active and an alert is emitted.

> **Implementation status (verified 2026-07-31):** the per-archetype override this section originally cited as
> `StrategyConfig.ml_reload_cadence_days` does **not** exist — no such field is defined anywhere in the workspace. The
> registry-level `live_hot_reload_cadence_days` is the only cadence knob that actually exists today.

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

Inference p99 latency is measured at the strategy-service boundary (time from feature-vector assembly to `MLPrediction`
available).

> **Corrected 2026-07-31 — the shipped SLO is 500ms, not 200ms.** The machine SSOT is the UAC threshold
> `ml_inference_latency_p99_ms`, whose `default_value` is **500** (`canonical/crosscutting/alerting/thresholds.py`),
> with the stated rationale that CeFi ML archetypes run on a 1-min bar cadence so 500ms p99 leaves ample headroom, and
> that sub-100ms HFT archetypes (not shipped pre-May-23) would override per-archetype. This doc previously asserted
> ≤200ms; that figure was never the enforced threshold. This doc is **not** `authoritative_for` the latency SLA — the
> UAC threshold is. Read the threshold, don't copy a number from here.

Enforcement that actually exists:

- An `AlertRule` for `AlertCode.ML_INFERENCE_LATENCY_BREACH` in UAC `canonical/crosscutting/alerting/rules.py` — it
  binds the threshold named `ml_inference_latency_p99_ms`, at severity `WARN`, on the `SLACK` channel. The alert code
  itself is declared in UAC `canonical/crosscutting/alerting/codes.py`. Routing is **Slack**, not Grafana.
- **No pytest gate.** This section previously cited
  `strategy-service/tests/integration/test_ml_inference_latency_sla.py`; no such test exists anywhere in the workspace.
  The SLA is alert-enforced at runtime only.
