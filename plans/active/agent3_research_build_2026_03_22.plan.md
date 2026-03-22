---
name: agent3-research-build
overview:
  Ensure Research/Build and Promote services have real content, absorb strategy-ui wizard and ml-training-ui experiment
  tracking
todos:
  - id: a3-p0-research-overview
    content: |
      - [ ] [AGENT] P0. Verify `/services/research/overview` has real content (not placeholder). It should show: active experiments count, model registry status, backtest queue, recent results. Wire to API hooks: `GET /ml/models` (model count), `GET /execution/backtests` (recent backtests). If placeholder, build a dashboard with KPI cards for each research domain (ML, Strategy, Execution).
    status: todo
  - id: a3-p0-ml-overview
    content: |
      - [ ] [AGENT] P0. Verify `/services/research/ml/overview` has real content. Should show: model registry summary, training status, recent experiments, feature drift. Wire to `GET /ml/models`, `GET /ml/experiments`, `GET /ml/training-status` API endpoints.
    status: todo
  - id: a3-p0-ml-experiments
    content: |
      - [ ] [AGENT] P0. Verify `/services/research/ml/experiments` has a real experiments table: experiment_id, model_type, status (running/completed/failed), metrics (sharpe, accuracy), created_at. Wire to `GET /ml/experiments` API. Verify `/services/research/ml/experiments/[id]` shows experiment detail with training curves (loss over epochs), hyperparameters, comparison to baseline.
    status: todo
  - id: a3-p0-ml-training
    content: |
      - [ ] [AGENT] P1. Verify `/services/research/ml/training` has: trigger training button, training queue, active jobs with progress. Wire to `GET /ml/training-jobs` and `POST /ml/training-jobs` APIs. In mock mode, POST should add a job to MockStateStore with status "queued".
    status: todo
  - id: a3-p0-ml-features
    content: |
      - [ ] [AGENT] P1. Verify `/services/research/ml/features` has: feature list with importance scores, correlation matrix, drift monitoring. Wire to `GET /ml/features` API.
    status: todo
  - id: a3-p0-ml-validation
    content: |
      - [ ] [AGENT] P1. Verify `/services/research/ml/validation` has: out-of-sample test results, signal quality metrics, walk-forward analysis. Wire to `GET /ml/validation-results` API.
    status: todo
  - id: a3-p0-ml-registry
    content: |
      - [ ] [AGENT] P1. Verify `/services/research/ml/registry` has: model version list with promote/deprecate actions, model comparison, A/B test setup. Wire to `GET /ml/models` and `POST /ml/models/{id}/promote` APIs.
    status: todo
  - id: a3-p0-ml-remaining
    content: |
      - [ ] [AGENT] P2. Verify remaining ML sub-tabs have content: `/services/research/ml/monitoring` (live model performance), `/services/research/ml/deploy` (deployment status), `/services/research/ml/governance` (model governance, approval workflows), `/services/research/ml/config` (ML pipeline configuration).
    status: todo
  - id: a3-p1-strategy-backtests
    content: |
      - [ ] [AGENT] P0. Verify `/services/research/strategy/backtests` has: backtest runs table with status, sharpe, drawdown, total return, trades count. Wire to `GET /execution/backtests` API. Add "New Backtest" button that opens a configuration modal/drawer.
    status: todo
  - id: a3-p1-strategy-compare
    content: |
      - [ ] [AGENT] P1. Verify `/services/research/strategy/compare` has: side-by-side comparison of 2+ backtests, equity curves overlay, risk metrics comparison. Wire to API.
    status: todo
  - id: a3-p1-strategy-results
    content: |
      - [ ] [AGENT] P1. Verify `/services/research/strategy/results` has: detailed backtest results with trade log, equity curve, drawdown chart, monthly returns heatmap.
    status: todo
  - id: a3-p1-strategy-heatmap
    content: |
      - [ ] [AGENT] P1. Verify `/services/research/strategy/heatmap` has: parameter sweep heatmap showing sharpe/return across parameter combinations.
    status: todo
  - id: a3-p2-absorb-strategy-wizard
    content: |
      - [ ] [AGENT] P1. Extract the multi-step strategy creation wizard from `strategy-ui/src/components/wizard/` (WizardShell, BasicConfigStep, StrategySelectionStep, InstitutionalShareClassStep, ReviewStep) and adapt it as a modal/drawer in the main UI. Trigger from "New Strategy" button on the backtests page. Adapt to use unified-trading-api endpoints and the main UI's component library (shadcn/ui, not whatever strategy-ui uses). Key features to preserve: CSV parameter upload (via papaparse), multi-step flow with validation.
    status: todo
  - id: a3-p3-absorb-ml-training
    content: |
      - [ ] [AGENT] P1. Review `ml-training-ui/src/` for any experiment tracking UI patterns not already in the main UI's ML sub-tabs. Key things to look for: training curve visualization (loss/metrics over epochs), hyperparameter display, model artifact download links, experiment comparison views. Absorb any missing patterns into the corresponding ML sub-tab pages.
    status: todo
  - id: a3-p4-promote-candidates
    content: |
      - [ ] [AGENT] P0. Verify `/services/research/strategy/candidates` shows a review queue of strategies pending promotion. Each candidate should show: name, backtest metrics, risk assessment, approval status. Add approve/reject buttons that call `POST /analytics/strategies/{id}/promote` and `POST /analytics/strategies/{id}/reject` APIs. In mock mode, these update MockStateStore.
    status: todo
  - id: a3-p4-promote-handoff
    content: |
      - [ ] [AGENT] P1. Verify `/services/research/strategy/handoff` shows the handoff tracking page: which strategies have been promoted from research to live, when, by whom, with what risk limits.
    status: todo
  - id: a3-p5-execution-research
    content: |
      - [ ] [AGENT] P1. Verify execution research pages have content: `/services/execution/algos` (algo comparison: TWAP, VWAP, IS, Sniper), `/services/execution/venues` (venue connectivity, latency, fill rates), `/services/execution/benchmarks` (benchmark definitions and results), `/services/execution/tca` (transaction cost analysis). Wire all to API.
    status: todo
  - id: a3-p6-tests
    content: |
      - [ ] [AGENT] P1. Add Playwright tests: 1) Navigate to Research Hub → verify KPI cards render. 2) Navigate to ML Models → verify model list renders. 3) Navigate to Backtests → verify backtest table renders. 4) Click "New Strategy" → verify wizard modal opens. 5) Navigate to Promote > Review Queue → verify candidate list renders.
    status: todo
isProject: false
---

# Notes & Context

## Key source repos for absorption

- `strategy-ui/src/components/wizard/` — multi-step wizard (BasicConfigStep, StrategySelectionStep, etc.)
- `strategy-ui/src/components/results/` — equity curve chart, backtest results
- `ml-training-ui/src/` — experiment tracking UI
- `_reference/versa-execution-analytics-ui/` — execution analytics patterns

## Absorbed from prior plans

- strategy_system_citadel_master_2026_03_15: Strategy lifecycle, promote flow
- uniform_ml_pipeline_sports_migration_2026_03_20: ML pipeline standardization
- fixed_grid_config_refactor_2026_03_21: Grid config for strategy parameters

## API endpoints needed

- GET /ml/models, GET /ml/experiments, GET /ml/training-jobs, GET /ml/features
- GET /ml/validation-results, POST /ml/training-jobs, POST /ml/models/{id}/promote
- GET /execution/backtests, POST /execution/backtests
- POST /analytics/strategies/{id}/promote, POST /analytics/strategies/{id}/reject
