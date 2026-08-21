---
doc_type: plan
title: sports-integration-05-ml-training-pipeline
summary: 'Wire sports ML training end-to-end: features -> training -> model -> inference.

  Port Model 2A ensemble (CatBoost/XGBoost/LightGBM/Huber) from archived repo.

  Walk-forward validation across seasons. Multi-phase: CLV base -> meta, xG base -> meta.

  Sports metrics: Poisson NLL, RPS, Brier score.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-25'
remaining_todos_consolidated_into: consolidated_sports_prediction_pipeline_2026_04_15
superseded_by: [consolidated_sports_prediction_pipeline_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
type: code
epic: epic-code-completion
completion_gates: {code: C4, deployment: D2, business: B3}
repo_gates:
- {repo: ml-training-service, code: C0, notes: 'Sports training config, Model 2A ensemble, walk-forward validation'}
- {repo: ml-inference-service, code: C0, notes: Sports inference pipeline}
- {repo: unified-trading-library (ml/ sub-package), code: C0, notes: 'Verify/add Poisson NLL, RPS, Brier score metrics'}
depends_on: [sports-integration-04-feature-calculators-full]
isProject: false
todos:
- {id: p1-verify-metrics, content: "- [ ] [AGENT] P0. Check unified-trading-library (ml/ sub-package) for Poisson NLL, RPS, Brier score.\n  If missing, port from archived footballbets/ml/football_metrics.py (17,674L).\n", status: pending}
- {id: p2-training-config, content: "- [ ] [AGENT] P1. Add sports training config to ml-training-service.\n  Config: model_type=ENSEMBLE, target=PINNACLE_CLOSING_ODDS, features=SportsFeatureVector\n  Walk-forward: train 2020-2024, validate 2024-25, test 2025-26\n  Multi-phase: Phase 1 (CLV base @ T-24h), Phase 2 (CLV meta @ T-1h)\n", status: pending}
- {id: p3-model-2a, content: "- [ ] [AGENT] P1. Port Model 2A ensemble from archived model_2a.py (401L).\n  CatBoost (30%) + XGBoost (25%) + LightGBM (30%) + HuberRegressor (15%)\n  Input: SportsFeatureVector (1000+ features)\n  Output: home/draw/away probabilities\n  Follow UTS ML conventions (model registry, GCS, versioning)\n", status: pending, blocked_by: p2-training-config}
- {id: p4-walk-forward, content: "- [ ] [AGENT] P2. Port walk_forward.py workflow from archive (249L).\n  Expanding train window per season.\n  Metrics: Poisson NLL, RPS, Brier, calibration plot.\n", status: pending, blocked_by: p3-model-2a}
- {id: p5-validation, content: "- [ ] [AGENT] P0. Train model on historical features (2020-2025).\n  Verify probabilities for all 3 outcomes.\n  Verify metrics reasonable (RPS < 0.25, calibration < 5%).\n  QG: cd ml-training-service && bash scripts/quality-gates.sh\n", status: pending, blocked_by: p4-walk-forward}
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_sports_prediction_pipeline_2026_04_15.md](./consolidated_sports_prediction_pipeline_2026_04_15.md).**
> Original scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

# Sports Integration Plan 5: ML Training Pipeline

Part of the 6-plan sports integration series. Depends on Plan 4 (1000+ features available). Can run in PARALLEL with
Plan 4 once basic features exist.

## Success Criteria

- Model 2A trained and in GCS model registry
- Walk-forward validation per-season
- Sports metrics integrated
- Calibrated probabilities for home/draw/away
