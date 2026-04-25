---
name: consolidated-ml-advanced-pipeline
overview: |
  Consolidated remaining ML work from ml_pipeline_revolution and domain_agnostic_ml_framework.
  Covers: calibration, P&L objectives, Bayesian tuning, incremental/transfer/multi-task training,
  hierarchical inference, strategy signal consumption, decision policy engine, sports feature adapter.
type: code
epic: epic-code-completion
status: active

reconciliation_status: yaml_to_markdown_converted
reconciliation_date: 2026-04-25
reconciliation_evidence: _reconciliation_evidence_map_2026_04_25.md

completion_gates:
  code: C5
  deployment: none
  business: B4

repo_gates:
  - repo: unified-api-contracts
    code: C0
  - repo: unified-trading-library
    code: C0
  - repo: ml-training-service
    code: C0
  - repo: ml-inference-service
    code: C0
  - repo: strategy-service
    code: C0

depends_on: []

source_plans:
  - ml_pipeline_revolution_2026_04_11
  - domain_agnostic_ml_framework_2026_04_11

isProject: false
---

> **Reconciliation note (2026-04-25):** YAML `todos:` block converted to canonical Cursor markdown checkboxes per
> `PLAN_FORMAT.md`. 6 todos flipped to `[x]` with cited commit evidence; 18 remain open. See
> `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors (ml_advanced_pipeline block ~line 201).

# Consolidated ML Advanced Pipeline

Remaining work from ml_pipeline_revolution and domain_agnostic_ml_framework. Many Phase 1-2 items are PARTIALLY_DONE
(code exists but gaps vs spec). Phase 2 incremental/transfer/multi-task and Phase 3 hierarchical are partially shipped
under architecture-v2 (ml-training `d53c2ea`, `f94f7db`, `df6caa4`; ml-inference `d6744d0`, `8b4fb8b`).

## Todos

### Phase 1 — UAC + UTL Foundations

- [ ] [AGENT] P0. mlr-p1-uac-ml-schemas: Extend UAC internal ML schemas with calibration, training scope, cost-aware
      types (PARTIALLY_DONE — core schemas exist, missing tabnet/tft, InferenceRequest.explain).
- [ ] [AGENT] P0. mlr-p1-utl-calibration: Build calibration module in UTL ml/calibration.py (PARTIALLY_DONE —
      ProbabilityCalibrator exists, missing reliability_diagram, save/load, temperature scaling).
- [ ] [AGENT] P0. mlr-p1-utl-pnl-objective: Build P&L-aware training objectives in UTL ml/pnl_objectives.py
      (PARTIALLY_DONE — pnl_weighted + sharpe exist, missing asymmetric_mse).
- [ ] [AGENT] P0. mlr-p1-utl-bayesian: Build Bayesian optimization wrapper in UTL ml/bayesian_optimizer.py
      (PARTIALLY_DONE — BayesianHyperparamOptimizer exists, missing MedianPruner/RDBStorage).
- [ ] [AGENT] P0. mlr-p1-utl-feature-importance: Build feature importance monitor in UTL
      ml/feature_importance_monitor.py (PARTIALLY_DONE — basic monitor exists, missing SHAP + GCS history).
- [ ] [AGENT] P1. mlr-p1-qg: Run quality-gates.sh on UAC, UTL — all pass.
- [ ] [AGENT] P1. daml-p2-decision-policy: Create unified_trading_library/ml/decision_policy_engine.py (plan [x] but
      file not found).

### Phase 2 — ML Training Service Integration

- [ ] [AGENT] P0. mlr-p2-calibration-integration: Wire calibration into uniform_training_pipeline.py Phase 3
      (PARTIALLY_DONE — basic cal/ECE exists, missing cal/val split + joblib persist).
- [ ] [AGENT] P0. mlr-p2-pnl-training: Wire P&L-aware objectives into model_trainer_factory.py (PARTIALLY_DONE —
      LightGBM custom objective exists).
- [ ] [AGENT] P0. mlr-p2-bayesian-tuning: Replace grid search with Bayesian optimization in Phase 2 (PARTIALLY_DONE —
      basic Optuna exists).
- [x] [AGENT] P0. mlr-p2-incremental: Add incremental training mode to uniform_training_pipeline.py. Evidence:
      ml-training `f94f7db` (incremental + cross-asset transfer learning).
- [x] [AGENT] P0. mlr-p2-transfer-learning: Add global/cross-asset training scope to pipeline. Evidence: ml-training
      `f94f7db` (incremental + cross-asset transfer learning).
- [ ] [AGENT] P0. mlr-p2-multi-task: Add multi-target joint training option (GENUINELY_PENDING).
- [ ] [AGENT] P1. mlr-p2-feature-importance-feedback: Wire feature importance monitor into Phase 3 post-training
      (PARTIALLY_DONE — basic usage).
- [ ] [AGENT] P1. mlr-p2-qg: Run quality-gates.sh on ml-training-service — pass.
- [x] [AGENT] P0. daml-p4-feature-adapter: Add sports GCS feature loading to ML training service
      feature_data_adapter.py. Evidence: ml-training `644ff22` (sports GCS reader uses correct path layout + handles
      NotFound) + `bcc8db0` (orchestrator uses variant.instrument_id for feature query scope) + `a5d3bbf` (sports ML
      training auto-populates instrument scope).

### Phase 3 — ML Inference Service

- [x] [AGENT] P0. mlr-p3-calibration-inference: Apply calibration at inference time. Evidence: ml-inference `d6744d0`
      (apply calibration at inference time).
- [ ] [AGENT] P1. mlr-p3-shap-inference: Add optional SHAP explanation to inference responses (PARTIALLY_DONE —
      request.explain exists, no schema field).
- [ ] [AGENT] P1. mlr-p3-hierarchical: Support hierarchical model loading Level 0-2 (GENUINELY_PENDING).
- [x] [AGENT] P1. mlr-p3-qg: Run quality-gates.sh on ml-inference-service — pass. Evidence: ml-inference `8b4fb8b`
      (Phase 13.3 strict-writer lint enforcement) + `bd05cbf` (CVE ignores accepted in QG).

### Phase 4 — Strategy Service Consumption

- [ ] [AGENT] P0. mlr-p4-strategy-calibrated-signals: Update strategy-service to consume calibrated confidences
      (GENUINELY_PENDING).
- [ ] [AGENT] P0. mlr-p4-cost-aware-strategy: Add cost-aware signal filtering in strategy-service (GENUINELY_PENDING).
- [ ] [AGENT] P1. mlr-p4-qg: Run quality-gates.sh on strategy-service — pass.
- [ ] [AGENT] P1. mlr-p5-final-qg: Final QG on all repos (UAC, UTL, ml-training-service, ml-inference-service,
      strategy-service).
