---
name: consolidated-ml-advanced-pipeline
overview: |
  Consolidated remaining ML work from ml_pipeline_revolution and domain_agnostic_ml_framework.
  Covers: calibration, P&L objectives, Bayesian tuning, incremental/transfer/multi-task training,
  hierarchical inference, strategy signal consumption, decision policy engine, sports feature adapter.
type: code
epic: epic-code-completion
status: active

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

todos:
  # ══════════════════════════════════════════════════════════════
  # PHASE 1 — UAC + UTL Foundations (partially done — see notes)
  # ══════════════════════════════════════════════════════════════
  - id: mlr-p1-uac-ml-schemas
    content:
      "Extend UAC internal ML schemas with calibration, training scope, cost-aware types (PARTIALLY_DONE — core schemas
      exist, missing tabnet/tft, InferenceRequest.explain)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p1-utl-calibration
    content:
      "Build calibration module in UTL ml/calibration.py (PARTIALLY_DONE — ProbabilityCalibrator exists, missing
      reliability_diagram, save/load, temperature scaling)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p1-utl-pnl-objective
    content:
      "Build P&L-aware training objectives in UTL ml/pnl_objectives.py (PARTIALLY_DONE — pnl_weighted + sharpe exist,
      missing asymmetric_mse)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p1-utl-bayesian
    content:
      "Build Bayesian optimization wrapper in UTL ml/bayesian_optimizer.py (PARTIALLY_DONE — BayesianHyperparamOptimizer
      exists, missing MedianPruner/RDBStorage)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p1-utl-feature-importance
    content:
      "Build feature importance monitor in UTL ml/feature_importance_monitor.py (PARTIALLY_DONE — basic monitor exists,
      missing SHAP + GCS history)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p1-qg
    content: "Run quality-gates.sh on UAC, UTL — all pass"
    status: todo
    source: ml_pipeline_revolution
  - id: daml-p2-decision-policy
    content: "Create unified_trading_library/ml/decision_policy_engine.py (plan [x] but file not found)"
    status: todo
    source: domain_agnostic_ml_framework

  # ══════════════════════════════════════════════════════════════
  # PHASE 2 — ML Training Service Integration
  # ══════════════════════════════════════════════════════════════
  - id: mlr-p2-calibration-integration
    content:
      "Wire calibration into uniform_training_pipeline.py Phase 3 (PARTIALLY_DONE — basic cal/ECE exists, missing
      cal/val split + joblib persist)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p2-pnl-training
    content:
      "Wire P&L-aware objectives into model_trainer_factory.py (PARTIALLY_DONE — LightGBM custom objective exists)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p2-bayesian-tuning
    content: "Replace grid search with Bayesian optimization in Phase 2 (PARTIALLY_DONE — basic Optuna exists)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p2-incremental
    content: "Add incremental training mode to uniform_training_pipeline.py (GENUINELY_PENDING)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p2-transfer-learning
    content: "Add global/cross-asset training scope to pipeline (GENUINELY_PENDING)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p2-multi-task
    content: "Add multi-target joint training option (GENUINELY_PENDING)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p2-feature-importance-feedback
    content: "Wire feature importance monitor into Phase 3 post-training (PARTIALLY_DONE — basic usage)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p2-qg
    content: "Run quality-gates.sh on ml-training-service — pass"
    status: todo
    source: ml_pipeline_revolution
  - id: daml-p4-feature-adapter
    content: "Add sports GCS feature loading to ML training service feature_data_adapter.py"
    status: todo
    source: domain_agnostic_ml_framework

  # ══════════════════════════════════════════════════════════════
  # PHASE 3 — ML Inference Service
  # ══════════════════════════════════════════════════════════════
  - id: mlr-p3-calibration-inference
    content: "Apply calibration at inference time (PARTIALLY_DONE — _apply_calibration exists, schema mismatch)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p3-shap-inference
    content:
      "Add optional SHAP explanation to inference responses (PARTIALLY_DONE — request.explain exists, no schema field)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p3-hierarchical
    content: "Support hierarchical model loading Level 0-2 (GENUINELY_PENDING)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p3-qg
    content: "Run quality-gates.sh on ml-inference-service — pass"
    status: todo
    source: ml_pipeline_revolution

  # ══════════════════════════════════════════════════════════════
  # PHASE 4 — Strategy Service Consumption
  # ══════════════════════════════════════════════════════════════
  - id: mlr-p4-strategy-calibrated-signals
    content: "Update strategy-service to consume calibrated confidences (GENUINELY_PENDING)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p4-cost-aware-strategy
    content: "Add cost-aware signal filtering in strategy-service (GENUINELY_PENDING)"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p4-qg
    content: "Run quality-gates.sh on strategy-service — pass"
    status: todo
    source: ml_pipeline_revolution
  - id: mlr-p5-final-qg
    content: "Final QG on all repos: UAC, UTL, ml-training-service, ml-inference-service, strategy-service"
    status: todo
    source: ml_pipeline_revolution

isProject: false
---

# Consolidated ML Advanced Pipeline

Remaining work from ml_pipeline_revolution and domain_agnostic_ml_framework. Many Phase 1-2 items are PARTIALLY_DONE
(code exists but gaps vs spec). Phase 2 incremental/transfer/multi-task and Phase 3 hierarchical are GENUINELY_PENDING.
