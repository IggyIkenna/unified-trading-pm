---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# ML Pipeline — Cross-Cutting Concern

## Hard Rules

### 1. ML models are signals, not decisions

ML models produce numeric signals (probabilities, scores, predicted values). Strategies consume these signals as one
input among many. The strategy — not the model — decides whether to trade. A model predicting "ETH +2% in 4H with 73%
confidence" is a feature. The strategy decides whether 73% is enough, whether cost and risk allow the trade, and what
size to use.

```
PROHIBITED:
  ml-inference-api  →  execution-service    (model cannot emit orders)
  ml-training-service  →  strategy configs  (training cannot change live configs)

ALLOWED:
  ml-inference-api  →  pub/sub  →  strategy-service  (signal as feature input)
  strategy-service  →  generate_signal(features + ml_signal + positions + risk)
```

### 2. Training and inference are separate services

- **ml-training-service:** Batch job. Reads features from GCS, trains models, writes model artifacts to model registry.
  Runs on schedule (daily/weekly) or on-demand. No live connectivity.
- **ml-inference-api:** Live service. Loads model from registry, receives feature vectors, returns predictions.
  Stateless — multiple instances behind load balancer.

These are separate deployments with separate scaling characteristics. Training is compute-intensive and bursty.
Inference is latency-sensitive and steady.

### 3. No model goes live without human approval

The promotion workflow is: batch train --> validation passes --> Telegram notification --> human approves --> model
promoted to live registry --> ml-inference-api hot-reloads. There is no automated promotion. A human reviews validation
metrics before any model serves live predictions.

## Feature Computation Pipeline

### Feature Services (7 Services)

| Service                         | Domain      | Features Computed                                   | Update Frequency   |
| ------------------------------- | ----------- | --------------------------------------------------- | ------------------ |
| features-delta-one-service      | CeFi/DeFi   | Funding rate, basis, carry, OI, volume profiles     | 1H candle close    |
| features-onchain-service        | DeFi        | Gas price, TVL, pool utilization, health factor     | Per block (12s L1) |
| features-options-service        | CeFi/TradFi | IV surface, greeks, skew, term structure            | 1H or on tick      |
| features-microstructure-service | CeFi        | Spread, depth, order flow imbalance, toxicity       | Per tick / 1min    |
| features-macro-service          | TradFi      | Rates, FX, CPI, GDP, sentiment indices              | Daily / on release |
| features-sports-service         | Sports      | Odds movement, sharp/soft diff, team form, injuries | Per odds update    |
| features-prediction-service     | Prediction  | Market sentiment, volume, resolution probability    | Per market update  |

### Feature Vector Schema

Features are published to pub/sub as typed feature vectors:

```python
# unified-features-interface
@dataclass
class FeatureVector:
    instrument_id: str           # canonical instrument ID
    feature_set: str             # "delta_one", "onchain", "microstructure", etc.
    timestamp: datetime          # feature computation timestamp
    values: dict[str, Decimal]   # feature_name → value
    metadata: FeatureMetadata    # version, source, freshness
```

### Feature Storage

```
Live path:
  features-*-service computes → pub/sub topic → strategy-service (real-time)
                               → GCS archive (historical record)

Batch path:
  GCS archive → ml-training-service reads for training
              → strategy-service reads for backtesting

GCS layout:
  gs://features/{feature_set}/{instrument_id}/{date}/features.parquet
```

## Model Families

The `model_trainer_factory.py` in ml-training-service supports 6 model families via `ModelType` enum and
`get_trainer()`:

| Model Family | Class             | Task Types                 | Key Characteristics                                                                    |
| ------------ | ----------------- | -------------------------- | -------------------------------------------------------------------------------------- |
| LightGBM     | `LightGBMTrainer` | Classification, Regression | Primary model. Multiclass (breakout/reversion/neither). Early stopping, class weights. |
| XGBoost      | `XGBoostTrainer`  | Classification, Regression | Alternative GBM. XGBClassifier / XGBRegressor.                                         |
| CatBoost     | `CatBoostTrainer` | Classification, Regression | Handles categorical features natively.                                                 |
| Huber        | `SklearnTrainer`  | Regression                 | Robust regression (outlier-resistant).                                                 |
| Ridge        | `SklearnTrainer`  | Regression                 | L2-regularized linear regression.                                                      |
| Poisson GLM  | `SklearnTrainer`  | Regression                 | Count data / rate modeling (PoissonRegressor).                                         |

**SSOT:** `ml-training-service/ml_training_service/app/training/model_trainer_factory.py` (`_TRAINER_MAP` dict)

All trainers implement the same interface: `train(x_train, y_train, x_val, y_val, hyperparams) -> TrainResult` and
`predict(model, x) -> np.ndarray`. The factory function `get_trainer(model_type, task_type)` returns the right trainer.

LightGBM and sklearn trainers use lazy imports (`import lightgbm as lgb` inside methods) to prevent ImportError cascade
in non-ML downstream repos.

## Inference Modes

The ml-inference-service implements 6 inference modes:

| Mode        | Handler / Engine              | Description                                                                                                                                                                                                                                              |
| ----------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------ |
| Batch       | `BatchInferenceHandler`       | Processes historical date ranges. Loads features from GCS, generates predictions in batch, writes results.                                                                                                                                               |
| Live        | `LiveInferenceHandler`        | Subscribes to live feature updates via `FeatureSubscriber`, runs inference per instrument/timeframe, publishes predictions to pub/sub. Polls at timeframe-specific intervals.                                                                            |
| Ensemble    | `EnsembleInferenceEngine`     | Runs multiple base models (LightGBM, XGBoost, CatBoost, sklearn) with weighted average combination. Supports optional meta-model for stacking.                                                                                                           |
| Cascade     | `CascadeInferenceMode`        | Multi-timeframe alignment. Trigger TF (e.g. 1h) fires, collects context TFs (4h, 1d), computes cascade confidence via weighted combination. Only publishes `CascadePredictionEvent` when confidence > threshold AND all TFs agree on direction.          |
| Meta-Signal | `MetaSignalInferenceEngine`   | Loads `SIGNAL_VECTOR_META` model from registry. Combines direction_signal (0.4), vol_signal (0.3), timing_signal (0.2), sizing_confidence (0.1) into single meta_signal [-1, 1]. Falls back to equal-weight combination when no trained model available. |
| SHAP        | `InferenceTimeSHAPCalculator` | Computes per-prediction feature attributions using cached `shap.TreeExplainer`. Top-N features by                                                                                                                                                        | shap_value | returned per inference call. ~2-10ms per row (explainer cached per model_key). |

**Cascade default profile** (`momentum_cascade`): trigger=1h, context=[4h, 1d], entry=[15m, 5m],
confidence_threshold=0.6, require_context_alignment=True.

**Meta-signal weight extraction:** For Logistic Regression models, weights come from `coef_` (normalized absolute
coefficients). For LightGBM/GBM models, weights come from `feature_importances_`.

## Training Pipeline

### Training Workflow

```
1. SCHEDULE: ml-training-service triggered (daily cron or manual)
2. LOAD: Read feature parquet files from GCS for training window
3. LABEL: Generate target labels (forward returns, binary outcomes)
4. SPLIT: Walk-forward split (see validation section below)
5. TRAIN: Fit model on training set
6. VALIDATE: Evaluate on out-of-sample set
7. ARTIFACT: Write model + metrics + config to model registry
8. NOTIFY: Telegram notification with validation metrics summary
9. APPROVE: Human reviews metrics, comments /approve on issue
10. PROMOTE: Model artifact promoted to live registry bucket
11. RELOAD: ml-inference-api detects new model, hot-reloads
```

### Model Training Configuration

```yaml
# GCS: gs://config/ml-training/{model_id}/training_config.yaml
model_id: defi_basis_v2
model_type: gradient_boosted_tree # xgboost
feature_sets:
  - delta_one
  - onchain
  - microstructure
target:
  type: forward_return # regression target
  horizon: 4H # predict 4-hour forward return
  swing_lookback_window: 24 # swing detection lookback
instruments:
  - "WALLET:SPOT_ASSET:ETH"
  - "WALLET:SPOT_ASSET:BTC"
training_window:
  start: "2024-01-01"
  end: "2025-12-31"
validation:
  method: walk_forward
  n_splits: 12
  test_size_days: 30
  embargo_days: 2 # gap between train/test to prevent leakage
hyperparameters:
  max_depth: 6
  learning_rate: 0.01
  n_estimators: 500
  early_stopping_rounds: 50
```

### Target Generation

Target variables are computed by `ml-training-service` from historical price data:

| Target Type        | Computation                                         | Use Case                                                                           |
| ------------------ | --------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Forward return     | `(price[t+h] - price[t]) / price[t]`                | Momentum, mean reversion                                                           |
| Binary direction   | `1 if price[t+h] > price[t] else 0`                 | Directional classification                                                         |
| Swing high         | `swing_high_outcome_N` column + shift(-1)           | Breakout/reversion after swing high (3-class: 1=breakout, -1=reversion, 0=neither) |
| Swing low          | `swing_low_outcome_N` column + shift(-1)            | Breakout/reversion after swing low (3-class: 1=breakout, -1=reversion, 0=neither)  |
| Cross-venue spread | `compute_cross_venue_spread_target(forward_bars=1)` | Binary (1=compress, 0=expand/flat). Fee-adjusted spread convergence.               |
| Spread change      | `spread[t+h] - spread[t]`                           | Basis / arb strategies                                                             |
| Volatility         | Realized vol over forward window                    | Options strategies                                                                 |
| Sports outcome     | Match result (1/X/2) or over/under                  | Sports prediction                                                                  |

**Swing targets:** Features-delta-one-service pre-computes `swing_high_outcome_N` / `swing_low_outcome_N` columns at
horizons [2, 3, 5, 10, 20, 50]. `TargetGenerator` selects the column matching `swing_lookback_window` from config and
applies shift(-1). Training is filtered to rows where swing events occurred (swing_high=1 or swing_low=1).

**Rule:** Target generation uses `shift(-1)` on computed labels, NOT `shift(-lookback_window)`. The lookback window
(`swing_lookback_window`) is for the label computation itself, not for the shift. This was a correctness fix applied
across 8 repos (2026-03-20).

## Validation Framework

### Walk-Forward Validation

The system uses expanding-window walk-forward validation, which is the only acceptable method for time-series financial
data:

```
Split 1: Train [Jan–Jun 2024]    | Embargo [Jul 1–2] | Test [Jul 2024]
Split 2: Train [Jan–Jul 2024]    | Embargo [Aug 1–2] | Test [Aug 2024]
Split 3: Train [Jan–Aug 2024]    | Embargo [Sep 1–2] | Test [Sep 2024]
...
Split 12: Train [Jan–May 2025]   | Embargo [Jun 1–2] | Test [Jun 2025]
```

**Embargo period:** 2-day gap between training and test windows to prevent information leakage from overlapping feature
windows.

**Prohibited validation methods:**

- Random train/test split (violates time ordering)
- K-fold cross-validation (future data leaks into training)
- Single holdout (insufficient for regime changes)

### Validation Metrics

| Metric                   | Threshold (Regression) | Threshold (Classification) | Action if Failed        |
| ------------------------ | ---------------------- | -------------------------- | ----------------------- |
| Out-of-sample R-squared  | > 0.02                 | N/A                        | Reject model            |
| Out-of-sample AUC        | N/A                    | > 0.55                     | Reject model            |
| Sharpe ratio (simulated) | > 0.5 annualized       | > 0.5 annualized           | Reject model            |
| Max drawdown             | < 15%                  | < 15%                      | Reject model            |
| Stability (std of perf)  | CV < 0.5               | CV < 0.5                   | Warn, manual review     |
| Feature importance drift | < 30% rank change      | < 30% rank change          | Warn, check for overfit |

### Model Registry

```
GCS model registry layout:
  gs://models/{model_id}/
    ├── versions/
    │     ├── v1/
    │     │     ├── model.joblib          # serialized model artifact
    │     │     ├── metrics.json          # validation metrics
    │     │     ├── training_config.yaml  # reproducibility
    │     │     ├── feature_names.json    # ordered feature list
    │     │     └── metadata.json         # timestamp, git SHA, author
    │     ├── v2/
    │     └── v3/
    ├── live/
    │     └── model.joblib → symlink to promoted version
    └── champion_metadata.json           # which version is live
```

## Champion/Challenger Deployment

### Promotion Workflow

```
CHALLENGER (new model trained):
  1. ml-training-service writes to gs://models/{model_id}/versions/vN/
  2. Validation metrics computed and written to metrics.json
  3. Telegram notification: "Model {model_id} vN trained. Metrics: {summary}. Approve?"
  4. Human reviews metrics in Telegram or model registry UI
  5. Human comments /approve on GitHub Issue (or Telegram command)
  6. Promotion script copies vN/model.joblib to live/model.joblib
  7. Updates champion_metadata.json with new version

CHAMPION (currently live model):
  - ml-inference-api watches gs://models/{model_id}/live/model.joblib
  - On file change: hot-reload model into memory (< 5s)
  - Old model serves until new model is fully loaded (zero-downtime swap)
```

### Shadow Mode (Challenger Evaluation)

Before promoting a challenger, it can run in shadow mode alongside the champion:

```
ml-inference-api receives feature vector:
  → champion model predicts → published to pub/sub (strategy consumes)
  → challenger model predicts → logged to GCS (NOT consumed by strategy)
  → comparison metrics computed (champion vs challenger on live data)

Shadow duration: configurable, typically 1–2 weeks
Promotion criteria: challenger Sharpe > champion Sharpe by >10% on shadow period
```

## Live Monitoring

### Signal Freshness

```
strategy-service FreshnessMonitor:
  For each subscribed ML signal:
    last_signal_time = timestamp of most recent prediction
    staleness = now() - last_signal_time
    max_staleness = config.max_ml_signal_age_seconds (default: 300)

    if staleness > max_staleness:
      log_event(ML_SIGNAL_STALE, model_id, staleness)
      strategy returns no-op (refuses to trade on stale signal)
```

### Model Performance Drift

Continuous monitoring of live model performance against expectations:

| Metric                    | Window    | Alert Threshold               | Action                         |
| ------------------------- | --------- | ----------------------------- | ------------------------------ |
| Prediction accuracy       | 7-day     | Drop > 20% vs validation      | WARN — review model            |
| Signal distribution shift | Daily     | KS-test p < 0.01              | WARN — feature drift likely    |
| Feature value range       | Per-batch | Value outside training range  | WARN — extrapolation risk      |
| Prediction latency        | Per-call  | > 500ms (warm) or > 5s (cold) | WARN — scale inference service |
| Error rate                | Hourly    | > 1% of predictions fail      | CRITICAL — investigate         |

### Drift Detection Pipeline

```
1. ml-inference-api logs every prediction: (timestamp, features, prediction, model_version)
2. Nightly batch job compares:
   - Feature distribution (training vs last 24H) — KS test per feature
   - Prediction distribution (training vs last 24H)
   - Actual outcomes vs predictions (when outcomes are known)
3. If drift detected:
   - log_event(MODEL_DRIFT_DETECTED, model_id, drift_metrics)
   - alerting-service sends Telegram notification
   - No automatic action — human decides whether to retrain
```

## Model Governance

### Model Approval Workflow

```
1. Training completes → GitHub Issue auto-created
   Title: "Model Promotion: {model_id} v{N}"
   Body: validation metrics, feature importance, sample predictions

2. Required reviewers: model owner + risk officer
   - Model owner reviews: feature engineering, overfitting, data quality
   - Risk officer reviews: max drawdown, tail risk, correlation to existing models

3. Approval: comment /approve on Issue
   - Triggers promotion script via GitHub Actions
   - Model copied to live registry
   - Audit log entry created

4. Rejection: comment /reject with reason
   - Model stays in versions/ but NOT promoted
   - Reason logged for future reference
```

### Audit Trail

Every model version maintains a complete audit trail:

```json
{
  "model_id": "defi_basis_v2",
  "version": 3,
  "trained_at": "2026-03-15T08:00:00Z",
  "trained_by": "ml-training-service (cron)",
  "git_sha": "abc123",
  "training_config_hash": "sha256:def456",
  "feature_set_versions": {
    "delta_one": "2026-03-15",
    "onchain": "2026-03-15"
  },
  "validation_metrics": {
    "oos_sharpe": 0.82,
    "oos_max_drawdown": -0.08,
    "oos_auc": 0.61
  },
  "approved_by": "ikenna",
  "approved_at": "2026-03-15T10:30:00Z",
  "promoted_at": "2026-03-15T10:31:00Z"
}
```

## Uniform Training Pipeline (All Asset Classes)

### Global Model Architecture

The system supports a single global model trained across all leagues/instruments (Star Lizard approach for sports):

```
Global model (sports example):
  - Training data: ALL leagues (Premier League, La Liga, NBA, NFL, etc.)
  - Features: normalized per-league (relative strength, form, odds movement)
  - Target: unified outcome (win/loss/draw or over/under)
  - League identity: encoded as categorical feature, NOT as separate models

Why global:
  - More training data → better generalization
  - Cross-league patterns (e.g., home advantage is universal)
  - Simpler deployment — one model, not N models per league
```

### Pooled Horizons

For financial models, multiple prediction horizons are pooled into a single training dataset:

```
Pooled horizon training:
  Row 1: features(ETH, t=100), target=return_1H(ETH, t=100), horizon_label="1H"
  Row 2: features(ETH, t=100), target=return_4H(ETH, t=100), horizon_label="4H"
  Row 3: features(ETH, t=100), target=return_1D(ETH, t=100), horizon_label="1D"
  Row 4: features(BTC, t=100), target=return_1H(BTC, t=100), horizon_label="1H"
  ...

Model predicts: P(return > 0 | features, horizon_label)
Strategy queries: model.predict(features, horizon="4H")
```

This reduces the number of models to maintain and allows cross-horizon learning.

## SSOT References

| Concept               | SSOT                              | Location                                                  |
| --------------------- | --------------------------------- | --------------------------------------------------------- |
| Feature vector schema | unified-features-interface        | `unified-features-interface/`                             |
| Training config       | ml-training-service config YAML   | `gs://config/ml-training/{model_id}/training_config.yaml` |
| Model registry        | GCS model artifacts               | `gs://models/{model_id}/`                                 |
| Inference API         | ml-inference-api                  | `ml-inference-api/`                                       |
| Training service      | ml-training-service               | `ml-training-service/`                                    |
| Target generation     | ml-training-service targets       | `ml-training-service/.../target_generation.py`            |
| Feature freshness     | strategy-service FreshnessMonitor | `strategy-service/strategy_service/monitors/`             |
| Model promotion       | GitHub Actions + Telegram         | `.github/workflows/` in ml-training-service               |
| Drift detection       | ml-inference-api monitoring       | `ml-inference-api/.../drift_monitor.py`                   |
| Uniform pipeline      | ml-training-service               | `ml-training-service/.../uniform_pipeline.py`             |
