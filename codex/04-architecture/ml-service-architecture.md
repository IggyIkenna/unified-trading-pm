---
scope: [engineer, ml-engineer, admin]
status: stub
last_reviewed: 2026-05-19
---

# ml-service architecture

> **🟡 STATUS: STUB (consolidation in-flight)** — this page describes the **target** post-consolidation architecture.
> Until [`ml_repo_consolidation_2026_05_19`](../../plans/active/ml_repo_consolidation_2026_05_19.md) Phase 9 lands,
> the `ml-service` repo **does not yet exist** — code still lives in the 2 source repos (`ml-training-service`,
> `ml-inference-service`). Promoted to `status: stable` by that plan's Phase 9 (a). Mirrors the
> `features-service-architecture.md` template.

## TL;DR

Two previously-separate workspace repos consolidated into a single new [`ml-service`](../../../ml-service/) repo
with sub-packages per surface. ONE Docker image (with conditional training-deps layer to keep the live-inference
build lean), ONE [`pyproject.toml`](../../../ml-service/pyproject.toml), ONE Health-API aggregator, ONE CLI
dispatcher parameterised by `--operation`. Subtree-merged with full per-repo git history preserved. Both
predecessor repos (`ml-training-service`, `ml-inference-service`) are archived post-merge; new code lands in
`ml-service` only.

This consolidation is pre-requisite for the 2026-05-23 live-DeFi cutover topology — training and inference are
colocated activities in deployment, share the model registry, share UAC feature contracts, and share
archetype/strategy mapping. Maintaining 2 separate image build + deploy pipelines + 2 cross-repo coordination
surfaces against that topology is operationally infeasible.

## Sub-package layout

```
ml-service/                              # NEW repo
├── ml_service/
│   ├── __init__.py
│   ├── __main__.py                     # python -m ml_service entry-point
│   ├── api/main.py                     # Health-API aggregator: /health/{training,inference}
│   ├── cli/main.py                     # dispatcher: parses --operation, forwards rest
│   ├── config_reloaders.py             # single typed MlServiceConfig root, sub-namespaces per surface
│   ├── common/                         # shared model registry client, feature provider, kill-switch subscriber
│   ├── training/                       # was ml-training-service/
│   │   ├── app/core/                   # config loader, feature selector, target generator, training orchestrator,
│   │   │                               # cloud feature provider, dependency checker, uniform pipeline,
│   │   │                               # cross-asset pipeline
│   │   ├── app/training/               # model_trainer, ensemble_trainer, regime_conditional_trainer,
│   │   │                               # sports_ensemble_trainer, hyperparameter_tuning
│   │   ├── backtest_v2/                # backtest runner
│   │   ├── engine/                     # orchestrator, mock_data_provider
│   │   └── ml/                         # model_registry, models
│   └── inference/                      # was ml-inference-service/
│       ├── app/core/                   # feature_subscriber, model_promotion_subscriber, mtf_feature_subscriber,
│       │                               # prediction_publisher, date_validation
│       ├── app/inference/              # batch_inference, cascade_inference, live_inference, meta_signal_inference,
│       │                               # sports_adapter
│       ├── engine/                     # model_loader, orchestrator, schemas
│       ├── io/                         # I/O handling
│       └── pre_crash_checkpoint.py     # recovery mechanism
├── pyproject.toml                      # ONE flat dependency list (conditional training deps via build flag)
├── Dockerfile                          # ONE image with build-arg INFERENCE_ONLY={true,false}
├── scripts/{training,inference}/
└── tests/{training,inference}/
```

## CLI dispatch

`--operation` is the discriminator; existing per-surface flags preserved verbatim post-merge:

| Operation | Mode | Previous repo | Notes |
|-----------|------|----------------|-------|
| `train` | batch | ml-training-service | final-training run per archetype × asset-group |
| `evaluate` | batch | ml-training-service | model evaluation against held-out fold |
| `hyperparam` | batch | ml-training-service | hyperparameter tuning (optuna sweep) |
| `batch-inference` | batch | ml-inference-service | offline predictions over a recorded feature stream |
| `live-inference` | live | ml-inference-service | real-time prediction publisher subscribed to feature stream |
| `cascade-inference` | live / batch | ml-inference-service | 2-stage meta-signal cascade |

All other CLI axes per `codex/06-coding-standards/cli-convention.md`: `--asset-group`, `--mode`,
domain-specific flags.

## Health-API aggregator

`api/main.py` exposes per-surface health under sub-paths:

- `/health/training` — last-train freshness per asset-group × archetype; last hyperparam-sweep freshness;
  cross-validation metric freshness
- `/health/inference` — feature-subscriber lag; model-promotion subscriber state; prediction-publisher emit
  freshness; cascade-stage transition health

Each surface contributes a `data_freshness` callback merged into a single `make_health_router` call.

## ServiceBootstrap consolidation

ONE `ServiceBootstrap` at the consolidated-service top level (STARTED / STOPPED / FAILED at the ml-service
level). Per-surface sub-bootstraps available for granular kill-switch routing — kill-switch subscriber
consolidates the 2 source repos' patterns into a single dispatcher (model-promotion + training-complete +
prediction-emitted event types).

## Deployment topology + Docker layer separation

Live-inference Docker image must NOT carry the full training deps (sklearn / xgboost / lightgbm / optuna /
shap). Approach:

- `pyproject.toml`: `[project.optional-dependencies] training = [...]` (closed set of heavy deps);
  `[project.dependencies]` carries only inference + shared deps
- `Dockerfile`: `ARG INFERENCE_ONLY=false`; conditional `RUN uv pip install ml-service[training]` when false
- Build matrix: `ml-service:<sha>` (training-capable) + `ml-service-inference:<sha>` (inference-only)
- Image-size gate: live-inference image regression vs ml-inference-service pre-merge baseline must be <30%
  (Phase 4 (h) gate in the consolidation plan)

## Launcher + Cloud Build

- ONE launcher: `launch-ml-vm.sh` parameterised by `--operation` + `--asset-group`. Predecessors
  (`launch-ml-training-vm.sh`, `launch-ml-inference-vm.sh`) deleted.
- Cloud Build refresh-tarballs: single `ml-service` entry (was 2).
- `VM_PREFIX_TO_BUCKET` updated to drop `ml-training-` / `ml-inference-` prefixes, add `ml-` prefix.
- DART UI service-list: single `ml-service` entry with 2 health sub-paths.

## Model registry + cross-surface coupling

Training writes model artifacts → GCS model-registry bucket → publishes `model-promoted` event.
Inference's `model_promotion_subscriber` consumes that event → loads model into runtime. **Post-merge** the
publisher and subscriber are in the same repo + can share types directly (no need for round-trip through UAC
for the in-process case), but UAC contracts remain the SSOT for the event schema since downstream
strategy-service is also a consumer.

## Migration history

- 2026-05-19: plan filed
  ([`ml_repo_consolidation_2026_05_19`](../../plans/active/ml_repo_consolidation_2026_05_19.md)) — 10-phase
  shape per features-service precedent.
- Pre-cutover race for 2026-05-23 live-DeFi launch; auto-flips to `BLOCKED-CUTOVER` if Phase 6 parity fails.
- Source repos archived via `gh repo archive` post-Phase 6 parity validation:
  - `ml-training-service` → `ml_service/training/`
  - `ml-inference-service` → `ml_service/inference/`

## Cross-references

- [`features-service-architecture.md`](./features-service-architecture.md) — sibling consolidation precedent;
  same 10-phase pattern, same template.
- [`promote-workflow-architecture.md`](./promote-workflow-architecture.md) — promote workflow pins
  `ml-service` inference-image + references model-promotion gate.
- [`codex/05-infrastructure/launcher-script-ssot.md`](../05-infrastructure/launcher-script-ssot.md) — 2-to-1
  launcher collapse.
- [`codex/05-infrastructure/vm-tarball-deployment.md`](../05-infrastructure/vm-tarball-deployment.md) — single
  ml-service tarball replaces 2-source-repo matrix.
- [`codex/02-data/README.md`](../02-data/README.md) — ML data lineage post-merge.

## Anti-patterns (do NOT)

- Do NOT re-introduce per-surface repos (training / inference as separate services). The consolidation was
  driven by operational topology + shared model registry + shared UAC contracts.
- Do NOT add asset-group-specific training / inference variants. `--asset-group` is a CLI axis, not a
  package-layout axis.
- Do NOT bloat the live-inference Docker image with training deps. Use the `INFERENCE_ONLY` build-arg path;
  Phase 4 (h) gate enforces this.
- Do NOT define event taxonomies locally in `ml_service/training/` etc. — all event types live in UAC under
  `unified_api_contracts.canonical.crosscutting.lifecycle` or `unified_api_contracts.domain.ml`.
- Do NOT couple training output rows directly to inference input rows in-process. Continue going through the
  GCS model-registry bucket — this preserves the deployment-topology flexibility (training VM ≠ inference VM)
  and the audit-trail.
