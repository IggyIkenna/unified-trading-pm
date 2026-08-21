---
doc_type: plan
title: consolidated-ml-advanced-pipeline
summary: 'Consolidated remaining ML work from ml_pipeline_revolution and domain_agnostic_ml_framework.

  Covers: calibration, P&L objectives, Bayesian tuning, incremental/transfer/multi-task training,

  hierarchical inference, strategy signal consumption, decision policy engine, sports feature adapter.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-16"
type: code
epic: epic-code-completion
reconciliation_status: yaml_to_markdown_converted
reconciliation_date: 2026-04-25
reconciliation_evidence: _reconciliation_evidence_map_2026_04_25.md
completion_gates: { code: C5, deployment: none, business: B4 }
repo_gates:
  - { repo: unified-api-contracts, code: C0 }
  - { repo: unified-trading-library, code: C0 }
  - { repo: ml-training-service, code: C0 }
  - { repo: ml-inference-service, code: C0 }
  - { repo: strategy-service, code: C0 }
depends_on: []
source_plans: [ml_pipeline_revolution_2026_04_11, domain_agnostic_ml_framework_2026_04_11]
isProject: false
---

> **ARCHIVED 2026-05-07** — folded into
> [`ml_and_features_master_2026_05_07.plan.md`](../active/ml_and_features_master_2026_05_07.plan.md). All open todos
> preserved in the umbrella's Phase 1-4. This file is the historical SSOT.

> **Reconciliation note (2026-04-25):** YAML `todos:` block converted to canonical Cursor markdown checkboxes per
> `PLAN_FORMAT.md`. 6 todos flipped to `[x]` with cited commit evidence; 18 remain open. See
> `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors (ml_advanced_pipeline block ~line 201).

# Consolidated ML Advanced Pipeline

## Codex SSOTs

This plan implements / extends the following codex documents (read these BEFORE making code changes; drift between code
and these docs is a review-blocking failure per `doc → plan → code`):

- [`/codex/02-data/data-lineage-MTDS-features-ml.md`](/codex/02-data/data-lineage-MTDS-features-ml.md) — MTDS → features
  → ml-training/ml-inference lineage; calibration / Bayesian tuning / hierarchical inference all sit on this chain
- [`/codex/04-architecture/batch-live-pipeline.md`](/codex/04-architecture/batch-live-pipeline.md) — batch=live
  symmetry; ml-training (batch) and ml-inference (live) MUST share the same feature-read path + same calibration
- [`/codex/04-architecture/batch-live-symmetry.md`](/codex/04-architecture/batch-live-symmetry.md) — code-path symmetry
  contract; strategy signal consumption + decision policy engine cannot diverge between modes

If any of the docs above is missing, this plan creates a stub for it (see [`codex/`](../../codex/) tree).

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 17 of 18 unchecked todos (mlr-p3-shap-inference re-evaluated → flippable to DONE)
- **Mis-marked DONE → flipped**: 1 — `mlr-p3-shap-inference` flipped to `[x]`. Verified: full SHAP wiring present at
  `ml-inference-service/ml_inference_service/app/inference/inference_shap.py` (TreeExplainer cache + bag) and
  `engine/orchestrator.py:180` (`if request.explain: ...`); UAC `InferenceRequest.explain: bool = Field(...)` shipped at
  `unified_api_contracts/internal/domain/ml/schemas.py:605`. The plan's note "request.explain exists, no schema field"
  is stale.
- **In-flight (running VMs)**: none.
- **Blocked by**:
  - `feature_dag_uac_ssot_and_features_coverage_2026_05_06` — multi-task / strategy calibrated-signals consumption all
    operate on features that need honest manifest semantics; soft-blocked, not hard.
  - For Phase 4 strategy-service consumption: `strategy_architecture_v2_finalization_2026_04_19` provides the lifecycle
    backbone that calibrated-signals plug into.
- **Blocks**:
  - `consolidated_strategy_and_ui_2026_04_15` Group D — calibrated signal consumption depends on the calibration
    integration here.
  - `master_to_live_defi_2026_05_23` Group F — cost-aware filtering on signals is one of the trading guardrails.
- **Last meaningful commit**: ml-inference `d6744d0` (calibration at inference), `8b4fb8b` (strict-writer lint),
  `bd05cbf` (CVE ignores); ml-training `f94f7db` (incremental + cross-asset transfer learning), `d53c2ea` (Group A
  backtest runner), `644ff22` / `bcc8db0` / `a5d3bbf` (sports feature adapter trio).
- **Recommendation**: KEEP active but RESCOPE. About 70% of original-scope items are PARTIALLY*DONE (skeletons exist,
  spec items missing). Recommended path: (a) flip the 1 mis-marked DONE; (b) split the remaining 17 into "spec-gap
  PARTIALLY_DONE polish" (low-priority) and "GENUINELY_PENDING net-new" (multi-task, hierarchical inference, calibrated
  signal consumption, cost-aware strategy). Net-new items are the May-23-or-later live trading prereqs. Do NOT archive
  this plan into one of the 5 asset-group umbrellas — it's cross-asset-group ML scaffolding. Consider folding into a
  successor plan `ml_advanced_pipeline_v2_2026_05*<date>` once writegate Phase 5 + feature_dag plan land.

Remaining work from ml_pipeline_revolution and domain_agnostic_ml_framework. Many Phase 1-2 items are PARTIALLY_DONE
(code exists but gaps vs spec). Phase 2 incremental/transfer/multi-task and Phase 3 hierarchical are partially shipped
under architecture-v2 (ml-training `d53c2ea`, `f94f7db`, `df6caa4`; ml-inference `d6744d0`, `8b4fb8b`).

## Todos

### Phase 1 — UAC + UTL Foundations

- [ ] [AGENT] P0. mlr-p1-uac-ml-schemas: Extend UAC internal ML schemas with calibration, training scope, cost-aware
      types (PARTIALLY_DONE — core schemas exist, missing tabnet/tft, InferenceRequest.explain). [AUDIT 2026-05-07:
      PARTIALLY-FRESH — `InferenceRequest.explain: bool` shipped (UAC `internal/domain/ml/schemas.py:605`). Remaining
      genuine gap: tabnet/tft schemas (UAC grep `TabNet|tabnet|TFT|tft` → 0 hits) — only meaningful if the model factory
      supports them, which is itself architecture-v2 dependent.]
- [ ] [AGENT] P0. mlr-p1-utl-calibration: Build calibration module in UTL ml/calibration.py (PARTIALLY_DONE —
      ProbabilityCalibrator exists, missing reliability_diagram, save/load, temperature scaling). [AUDIT 2026-05-07:
      PARTIALLY-FRESH — `ProbabilityCalibrator` confirmed in `unified_trading_library/ml/ml_training_utils.py:16`; no
      separate `ml/calibration.py` module, no reliability_diagram / temperature_scaling helpers; consider lifting into a
      dedicated module per spec.]
- [ ] [AGENT] P0. mlr-p1-utl-pnl-objective: Build P&L-aware training objectives in UTL ml/pnl_objectives.py
      (PARTIALLY_DONE — pnl_weighted + sharpe exist, missing asymmetric_mse). [AUDIT 2026-05-07: PARTIALLY-FRESH —
      confirmed pnl_weighted + sharpe at `ml_training_utils.py:199-206`; no separate `ml/pnl_objectives.py`;
      asymmetric_mse not implemented.]
- [ ] [AGENT] P0. mlr-p1-utl-bayesian: Build Bayesian optimization wrapper in UTL ml/bayesian_optimizer.py
      (PARTIALLY_DONE — BayesianHyperparamOptimizer exists, missing MedianPruner/RDBStorage). [AUDIT 2026-05-07:
      PARTIALLY-FRESH — `BayesianHyperparamOptimizer` at `ml_training_utils.py:70`; consumed in ml-training
      `uniform_training_pipeline.py:592-599`; no MedianPruner/RDBStorage; lifting to dedicated
      `ml/bayesian_optimizer.py` is cosmetic.]
- [ ] [AGENT] P0. mlr-p1-utl-feature-importance: Build feature importance monitor in UTL
      ml/feature_importance_monitor.py (PARTIALLY_DONE — basic monitor exists, missing SHAP + GCS history). [AUDIT
      2026-05-07: STALE-ish — SHAP shipped end-to-end (UAC `InferenceRequest.explain` + ml-inference `inference_shap.py`
      TreeExplainer cache + orchestrator wiring). GCS history persistence still pending. Consider flipping to DONE if
      "feature importance" was scoped narrowly to SHAP at inference time.]
- [ ] [AGENT] P1. mlr-p1-qg: Run quality-gates.sh on UAC, UTL — all pass. [AUDIT 2026-05-07: FRESH — final QG sweep
      gate; will trip on any not-yet-merged code from siblings.]
- [ ] [AGENT] P1. daml-p2-decision-policy: Create unified_trading_library/ml/decision_policy_engine.py (plan [x] but
      file not found). [AUDIT 2026-05-07: PARTIALLY-FRESH — `DecisionPolicyConfig` exists in
      `unified_trading_library/config_interface/sports_ml_config.py:26` (sports-only); the cross-asset-group "engine"
      module path `unified_trading_library/ml/decision_policy_engine.py` is still absent. Likely scoped narrower than
      original plan envisioned.]

### Phase 2 — ML Training Service Integration

- [ ] [AGENT] P0. mlr-p2-calibration-integration: Wire calibration into uniform_training_pipeline.py Phase 3
      (PARTIALLY_DONE — basic cal/ECE exists, missing cal/val split + joblib persist). [AUDIT 2026-05-07:
      PARTIALLY-FRESH — cal/val split + joblib persist still missing per ml-training grep.]
- [ ] [AGENT] P0. mlr-p2-pnl-training: Wire P&L-aware objectives into model_trainer_factory.py (PARTIALLY_DONE —
      LightGBM custom objective exists). [AUDIT 2026-05-07: PARTIALLY-FRESH — extension to other model families
      pending.]
- [ ] [AGENT] P0. mlr-p2-bayesian-tuning: Replace grid search with Bayesian optimization in Phase 2 (PARTIALLY_DONE —
      basic Optuna exists). [AUDIT 2026-05-07: PARTIALLY-FRESH — Optuna confirmed wired at
      `uniform_training_pipeline.py:594` `if self.config.tuning_method == "optuna"`; the genuinely-missing piece is
      grid-search removal + MedianPruner/RDBStorage.]
- [x] [AGENT] P0. mlr-p2-incremental: Add incremental training mode to uniform_training_pipeline.py. Evidence:
      ml-training `f94f7db` (incremental + cross-asset transfer learning).
- [x] [AGENT] P0. mlr-p2-transfer-learning: Add global/cross-asset training scope to pipeline. Evidence: ml-training
      `f94f7db` (incremental + cross-asset transfer learning).
- [ ] [AGENT] P0. mlr-p2-multi-task: Add multi-target joint training option (GENUINELY_PENDING). [AUDIT 2026-05-07:
      FRESH — confirmed absent: ml-training grep `multi_target|multi.task` → 0 production hits.]
- [ ] [AGENT] P1. mlr-p2-feature-importance-feedback: Wire feature importance monitor into Phase 3 post-training
      (PARTIALLY_DONE — basic usage). [AUDIT 2026-05-07: PARTIALLY-FRESH — same scope as mlr-p1-utl-feature-importance.]
- [ ] [AGENT] P1. mlr-p2-qg: Run quality-gates.sh on ml-training-service — pass. [AUDIT 2026-05-07: FRESH — final QG
      gate.]
- [x] [AGENT] P0. daml-p4-feature-adapter: Add sports GCS feature loading to ML training service
      feature_data_adapter.py. Evidence: ml-training `644ff22` (sports GCS reader uses correct path layout + handles
      NotFound) + `bcc8db0` (orchestrator uses variant.instrument_id for feature query scope) + `a5d3bbf` (sports ML
      training auto-populates instrument scope).

### Phase 3 — ML Inference Service

- [x] [AGENT] P0. mlr-p3-calibration-inference: Apply calibration at inference time. Evidence: ml-inference `d6744d0`
      (apply calibration at inference time).
- [x] [AGENT] P1. mlr-p3-shap-inference: Add optional SHAP explanation to inference responses (PARTIALLY_DONE —
      request.explain exists, no schema field). [AUDIT 2026-05-07: DONE — verified UAC
      `InferenceRequest.explain: bool = Field(...)` shipped at `internal/domain/ml/schemas.py:605`;
      `inference_shap.py` (TreeExplainer cache + bag) shipped at
      `ml-inference-service/ml_inference_service/app/inference/inference_shap.py`; orchestrator wires `request.explain`
      at `engine/orchestrator.py:180`. The "no schema field" note in plan body is stale.]
- [ ] [AGENT] P1. mlr-p3-hierarchical: Support hierarchical model loading Level 0-2 (GENUINELY_PENDING). [AUDIT
      2026-05-07: FRESH — ml-inference grep `level_0|level_1|level_2|hierarchical` in `ml_inference_service/` source → 0
      hits.]
- [x] [AGENT] P1. mlr-p3-qg: Run quality-gates.sh on ml-inference-service — pass. Evidence: ml-inference `8b4fb8b`
      (Phase 13.3 strict-writer lint enforcement) + `bd05cbf` (CVE ignores accepted in QG).

### Phase 4 — Strategy Service Consumption

- [ ] [AGENT] P0. mlr-p4-strategy-calibrated-signals: Update strategy-service to consume calibrated confidences
      (GENUINELY_PENDING). [AUDIT 2026-05-07: FRESH — strategy-service grep
      `calibrated.*confidence|consume.*calibrated|calibration.*signal` → 0 hits. Ownership overlaps with
      `consolidated_strategy_and_ui:Group D`. Live trading prereq.]
- [ ] [AGENT] P0. mlr-p4-cost-aware-strategy: Add cost-aware signal filtering in strategy-service (GENUINELY_PENDING).
      [AUDIT 2026-05-07: FRESH — execution-service has `services/execution_cost_estimator.py` and `v2/cost_models.py`
      (the producer side); strategy-service has no consumer wiring. Live trading prereq.]
- [ ] [AGENT] P1. mlr-p4-qg: Run quality-gates.sh on strategy-service — pass. [AUDIT 2026-05-07: FRESH — final QG gate;
      depends on the two preceding consumer wirings.]
- [ ] [AGENT] P1. mlr-p5-final-qg: Final QG on all repos (UAC, UTL, ml-training-service, ml-inference-service,
      strategy-service). [AUDIT 2026-05-07: FRESH — final acceptance.]
