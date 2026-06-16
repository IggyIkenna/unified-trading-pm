---
scope: [engineer, admin]
status: stable
last_reviewed: 2026-05-20
---

# ml-service architecture

> **✅ STATUS: STABLE** — consolidation complete 2026-05-20 (Phases 1-9 of
> [`ml_repo_consolidation_2026_05_19`](../../plans/active/ml_repo_consolidation_2026_05_19.md)). `ml-service` is the
> canonical repo; both source repos (`ml-training-service`, `ml-inference-service`) are archived.

## TL;DR

Two previously-separate workspace repos consolidated into a single new [`ml-service`](../../../ml-service/) repo with
sub-packages per surface. ONE Docker image (single flat-deps build — see deployment topology section for rationale on
rejecting the inference-only split), ONE [`pyproject.toml`](../../../ml-service/pyproject.toml), ONE Health-API
aggregator, ONE CLI dispatcher parameterised by `--operation`. Subtree-merged with full per-repo git history preserved.
Both predecessor repos (`ml-training-service`, `ml-inference-service`) are archived post-merge; new code lands in
`ml-service` only.

This consolidation is pre-requisite for the 2026-05-23 live-DeFi cutover topology — training and inference are colocated
activities in deployment, share the model registry, share UAC feature contracts, and share archetype/strategy mapping.
Maintaining 2 separate image build + deploy pipelines + 2 cross-repo coordination surfaces against that topology is
operationally infeasible.

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
├── pyproject.toml                      # ONE flat [project.dependencies] list (~35 deps; no extras)
├── Dockerfile                          # ONE image (~1.2GB; flat-deps build; no conditional layers)
├── scripts/{training,inference}/
└── tests/{training,inference}/
```

## CLI dispatch

`--operation` is the discriminator; existing per-surface flags preserved verbatim post-merge:

| Operation           | Mode         | Previous repo        | Notes                                                       |
| ------------------- | ------------ | -------------------- | ----------------------------------------------------------- |
| `train`             | batch        | ml-training-service  | final-training run per archetype × asset-group              |
| `evaluate`          | batch        | ml-training-service  | model evaluation against held-out fold                      |
| `hyperparam`        | batch        | ml-training-service  | hyperparameter tuning (optuna sweep)                        |
| `batch-inference`   | batch        | ml-inference-service | offline predictions over a recorded feature stream          |
| `live-inference`    | live         | ml-inference-service | real-time prediction publisher subscribed to feature stream |
| `cascade-inference` | live / batch | ml-inference-service | 2-stage meta-signal cascade                                 |

All other CLI axes per `codex/06-coding-standards/cli-convention.md`: `--asset-group`, `--mode`, domain-specific flags.

## Health-API aggregator

`api/main.py` exposes per-surface health under sub-paths:

- `/health/training` — last-train freshness per asset-group × archetype; last hyperparam-sweep freshness;
  cross-validation metric freshness
- `/health/inference` — feature-subscriber lag; model-promotion subscriber state; prediction-publisher emit freshness;
  cascade-stage transition health

Each surface contributes a `data_freshness` callback merged into a single `make_health_router` call.

## ServiceBootstrap consolidation

ONE `ServiceBootstrap` at the consolidated-service top level (STARTED / STOPPED / FAILED at the ml-service level).
Per-surface sub-bootstraps available for granular kill-switch routing — kill-switch subscriber consolidates the 2 source
repos' patterns into a single dispatcher (model-promotion + training-complete + prediction-emitted event types).

## Deployment topology

ONE Docker image, ~1100-1200MB, identical regardless of `--operation`. Built from a single flat `[project.dependencies]`
list (~35 deps). NO conditional dep groups, NO `INFERENCE_ONLY` build-arg.

**Decision rationale (operator pick 2026-05-19, Option 2)**: a conditional training-deps split would have produced a
~400-500MB live-inference image (55-60% leaner) at the cost of carving an exception in the workspace flat-deps rule
(CLAUDE.md `### Dependencies + builds`). The size win was considered against the deployment topology — live-inference
runs on long-lived VMs (`launch-ml-vm.sh` per asset-group flavor), not scale-to-zero serverless. Cold-start is a
one-time cost per VM bringup, not per-prediction. The image-pull delta (~700MB extra at deploy time, multiplied across
the VM fleet × redeploy cadence) was deemed less operationally significant than preserving rule purity. **Result**:
flat-deps rule unchanged workspace-wide; ml-service carries training deps it doesn't import at inference time; no Phase
6 image-size regression gate.

## Launcher + Cloud Build

- ONE launcher: `launch-ml-vm.sh` parameterised by `--operation` + `--asset-group`. Predecessors
  (`launch-ml-training-vm.sh`, `launch-ml-inference-vm.sh`) deleted.
- Cloud Build refresh-tarballs: single `ml-service` entry (was 2).
- `VM_PREFIX_TO_BUCKET` updated to drop `ml-training-` / `ml-inference-` prefixes, add `ml-` prefix.
- DART UI service-list: single `ml-service` entry with 2 health sub-paths.

## Model registry + cross-surface coupling

Training writes model artifacts → GCS model-registry bucket → publishes `model-promoted` event. Inference's
`model_promotion_subscriber` consumes that event → loads model into runtime. **Post-merge** the publisher and subscriber
are in the same repo + can share types directly (no need for round-trip through UAC for the in-process case), but UAC
contracts remain the SSOT for the event schema since downstream strategy-service is also a consumer.

## Migration history

- 2026-05-19: plan filed ([`ml_repo_consolidation_2026_05_19`](../../plans/active/ml_repo_consolidation_2026_05_19.md))
  — 10-phase shape per features-service precedent.
- 2026-05-20: Phases 1-9 complete — ml-service repo live; source repos archived pending `gh repo archive` operator
  action (Phase 7 step 3). All downstream registries updated: deployment-service catalog, shard_builder, dependencies,
  manifest_reader, topology nodes, cli, seed_mock_data. Launcher: `launch-ml-vm.sh` unified. VM prefix: `ml-` (was
  `ml-train-`). All 3 parity gates GREEN (gate-1 boot, gate-2 QG, gate-3 functional).
- Source repo path mappings:
  - `ml-training-service/` (path `ml_training_service/`) → `ml-service/ml_service/training/`
  - `ml-inference-service/` (path `ml_inference_service/`) → `ml-service/ml_service/inference/`

## Cross-references

- [`features-service-architecture.md`](./features-service-architecture.md) — sibling consolidation precedent; same
  10-phase pattern, same template.
- [`promote-workflow-architecture.md`](./promote-workflow-architecture.md) — promote workflow pins `ml-service`
  inference-image + references model-promotion gate.
- [`codex/05-infrastructure/launcher-script-ssot.md`](../05-infrastructure/launcher-script-ssot.md) — 2-to-1 launcher
  collapse.
- [`codex/05-infrastructure/vm-tarball-deployment.md`](../05-infrastructure/vm-tarball-deployment.md) — single
  ml-service tarball replaces 2-source-repo matrix.
- [`codex/02-data/README.md`](../02-data/README.md) — ML data lineage post-merge.

## Anti-patterns (do NOT)

- Do NOT re-introduce per-surface repos (training / inference as separate services). The consolidation was driven by
  operational topology + shared model registry + shared UAC contracts.
- Do NOT add asset-group-specific training / inference variants. `--asset-group` is a CLI axis, not a package-layout
  axis.
- Do NOT introduce `[project.optional-dependencies]` to split training vs inference deps. Operator picked the flat-deps
  path 2026-05-19 (Option 2) — single image, no conditional layers. See deployment topology section for rationale. The
  55-60% inference-image-size win does NOT justify carving a workspace flat-deps exception given live-inference's
  long-lived VM topology (cold-start mostly N/A).
- Do NOT define event taxonomies locally in `ml_service/training/` etc. — all event types live in UAC under
  `unified_api_contracts.canonical.crosscutting.lifecycle` or `unified_api_contracts.domain.ml`.
- Do NOT couple training output rows directly to inference input rows in-process. Continue going through the GCS
  model-registry bucket — this preserves the deployment-topology flexibility (training VM ≠ inference VM) and the
  audit-trail.
