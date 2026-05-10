---
name: strategy-lifecycle-visibility-ui
remaining_todos_consolidated_into: consolidated_strategy_and_ui_2026_04_15
superseded_by: [consolidated_strategy_and_ui_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview:
  Strategy lifecycle enforcement, paper trading comparison, ML dashboard, feature lineage, composable strategies,
  auto-retuning, research shell, risk attribution UI
type: code
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-11

completion_gates:
  code: C5
  deployment: none
  business: B3

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: ml-inference-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  # ── Phase 1: Foundation Schemas (PARALLEL) ─────────────────────────────
  - id: p1-uac-lifecycle-schemas
    content: |
      - [ ] [AGENT] P0. Add strategy lifecycle, paper comparison, and lineage schemas to UAC
      Add to `unified_api_contracts/internal/`:
      - `StrategyLifecycleStage` enum: `DRAFT`, `BACKTEST`, `VALIDATED`, `PAPER`, `SHADOW`, `LIVE`, `DEPRECATED`
      - `StrategyLifecycleTransition`: from_stage, to_stage, required_gates (list of gate conditions), auto_trigger (bool), human_approval_required (bool)
      - `LIFECYCLE_TRANSITIONS` dict: maps valid transitions with gate requirements:
        - DRAFT→BACKTEST: feature manifest complete
        - BACKTEST→VALIDATED: walk_forward_sharpe > 0.5, max_dd < 15%, auc > 0.55
        - VALIDATED→PAPER: human approval
        - PAPER→SHADOW: paper_sharpe within 20% of backtest for N days
        - SHADOW→LIVE: shadow performance within 10% of champion for M days
        - LIVE→DEPRECATED: 3 consecutive months negative alpha (auto-trigger)
      - `PaperTradeComparison`: strategy_id, paper_sharpe, backtest_sharpe, sharpe_ratio_pct, slippage_model_error, signal_decay_rate
      - `PredictionLineageRecord`: prediction_id, model_version, feature_versions (dict), raw_data_date, feature_timestamp, training_period, trade_id, pnl
      - `RiskAttribution`: strategy_id, alpha_pnl, beta_pnl, carry_pnl, residual_pnl, total_pnl
      - `ComposableStrategyConfig`: signal_generator (enum), position_sizer (enum), risk_filter (enum), execution_selector (enum)
      - `SignalGeneratorType` enum: `ML_DIRECTIONAL`, `ML_SWING`, `RULE_BASED`, `HYBRID`
      - `PositionSizerType` enum: `KELLY`, `FIXED`, `RISK_PARITY`, `VOLATILITY_TARGET`
      - `RiskFilterType` enum: `DRAWDOWN`, `CORRELATION`, `REGIME`, `COMPOSITE`
    status: todo
    note: "PARALLEL with p1-strategy-lifecycle-enforcement"

  - id: p1-strategy-lifecycle-enforcement
    content: |
      - [ ] [AGENT] P0. Build lifecycle state machine in strategy-service
      New module `strategy_service/engine/lifecycle/`:
      - `lifecycle_state_machine.py`:
        - `StrategyLifecycleManager`: validates transitions, checks gates, emits events
        - `can_transition(strategy_id, from_stage, to_stage) -> tuple[bool, list[str]]` — returns (allowed, unmet_gates)
        - `execute_transition(strategy_id, to_stage) -> StrategyLifecycleStage` — transitions if gates met
        - Gate checkers: `_check_backtest_gates()`, `_check_paper_gates()`, `_check_shadow_gates()`
      - `paper_comparison_tracker.py`:
        - `PaperComparisonTracker`: tracks paper vs backtest performance
        - `record_paper_trade(strategy_id, paper_result)` — accumulates paper P&L
        - `compare(strategy_id) -> PaperTradeComparison` — paper Sharpe vs backtest Sharpe
        - Emits PAPER_TRADE_COMPARISON events on each comparison
      - Wire into strategy engine: refuse to execute LIVE instructions for non-LIVE strategies
    status: todo
    note: "PARALLEL with p1-uac-lifecycle-schemas"

  # ── Phase 1 QG Gate ─────────────────────────────────────────────────────
  - id: p1-qg
    content: |
      - [ ] [AGENT] P0. Run quality-gates.sh on UAC, strategy-service — all pass
    status: todo
    note: "SEQUENTIAL — gate before Phase 2"

  # ── Phase 2: Composable Strategies + Auto-Retuning (PARALLEL) ──────────
  - id: p2-composable-strategies
    content: |
      - [ ] [AGENT] P1. Implement composable strategy building blocks in strategy-service
      New module `strategy_service/engine/composable/`:
      - `signal_generators/`: ML directional, ML swing, rule-based, hybrid — each implements `generate_signal(features) -> Signal`
      - `position_sizers/`: Kelly, fixed fractional, risk parity, vol targeting — each implements `size_position(signal, portfolio) -> PositionSize`
      - `risk_filters/`: Drawdown filter, correlation filter, regime filter, composite — each implements `filter(signal, portfolio) -> bool`
      - `ComposableStrategy(BaseStrategy)`: takes `ComposableStrategyConfig`, wires signal→sizer→filter→execution
      - Register as new strategy mode `composable` in strategy engine
      Benefit: new strategy = new config YAML, not new Python class. 44 factories → N composable blocks.
    status: todo
    note: "PARALLEL with p2-auto-retune, p2-lineage"

  - id: p2-auto-retune
    content: |
      - [ ] [AGENT] P1. Add auto-retuning trigger in ml-inference-service
      In drift monitoring:
      - If rolling accuracy drops >15% from validation baseline for 7+ days:
        - Emit MODEL_RETUNE_REQUESTED event with model_id, current_metrics, baseline_metrics
        - ml-training-service listens: triggers retrain with same config
        - If retrained model passes validation thresholds: auto-promote to shadow (not live)
        - If shadow beats champion after M days: emit PROMOTION_RECOMMENDED event for human approval
      - Config: `auto_retune_enabled: bool`, `retune_accuracy_drop_threshold: float = 0.15`, `retune_window_days: int = 7`
      - Add to TrainingPipelineConfig in UAC
    status: todo
    note: "PARALLEL with p2-composable-strategies"

  - id: p2-lineage
    content: |
      - [ ] [AGENT] P1. Add prediction lineage tracking
      In ml-inference-service:
      - For each prediction, record PredictionLineageRecord:
        - prediction_id, model_version, feature_versions (hash of each feature set), raw_data_date
      - Store to GCS: `gs://ml-lineage/{model_id}/{date}/lineage.parquet`
      In strategy-service:
      - When trade executes, link trade_id to prediction_id
      In pnl-attribution:
      - Link P&L to trade_id → prediction_id → model → features → raw data
      Full chain: raw tick → MTDS → feature service → training data → model → prediction → trade → P&L
    status: todo
    note: "PARALLEL with p2-auto-retune"

  # ── Phase 2 QG Gate ─────────────────────────────────────────────────────
  - id: p2-qg
    content: |
      - [ ] [AGENT] P0. Run quality-gates.sh on strategy-service, ml-inference-service — pass
    status: todo
    note: "SEQUENTIAL — gate before Phase 3"

  # ── Phase 3: UI Components (PARALLEL within) ──────────────────────────
  - id: p3-ml-performance-dashboard
    content: |
      - [ ] [AGENT] P0. Build ML model performance dashboard in unified-trading-system-ui
      New page or extension of existing `/services/research/ml/`:
      - **Accuracy Decay Curve**: per-model live accuracy vs validation accuracy (line chart, trailing 30 days)
      - **Feature Importance Drift Heatmap**: top 20 features, importance change over time (heatmap)
      - **Distribution Shift Monitor**: KL divergence of prediction distribution vs training (gauge + trend)
      - **Calibration Reliability Diagram**: predicted probability vs actual outcome rate (scatter + diagonal)
      - **P&L Attribution**: how much P&L from each model's signals (stacked bar chart)
      - Data source: existing ML mock data in `lib/mocks/fixtures/ml-data.ts` + new dashboard-specific mocks
      - Components: use existing chart primitives (recharts), add to research/ml page
    status: todo
    note: "PARALLEL with p3-strategy-research-shell, p3-risk-attribution"

  - id: p3-strategy-research-shell
    content: |
      - [ ] [AGENT] P1. Build strategy research shell in unified-trading-system-ui
      Extension of `/strategy-platform/`:
      - **Feature Importance Explorer**: select a model → SHAP waterfall for any prediction (uses explain=True inference)
      - **What-If Simulator**: adjust feature values → see prediction change in real-time (client-side inference mock)
      - **Backtest Parameter Sweep**: 3D surface plot (param1 x param2 → Sharpe) from grid search results
      - **Cross-Strategy Correlation**: matrix heatmap showing which strategies are crowded (correlation of returns)
      - **Lifecycle Pipeline**: visual Kanban of strategies by lifecycle stage (DRAFT→...→LIVE→DEPRECATED)
      - Mock data: extend strategy-platform fixtures with lifecycle, correlation, and sweep data
    status: todo
    note: "PARALLEL with p3-ml-performance-dashboard"

  - id: p3-risk-attribution
    content: |
      - [ ] [AGENT] P1. Build risk attribution dashboard in unified-trading-system-ui
      New widgets or extension of risk/exposure page:
      - **P&L Decomposition**: alpha (model signal), beta (market exposure), carry (funding/yield), residual (donut + time series)
      - **Risk Factor Exposure**: what-if scenarios: BTC -10%, rates +50bps, ETH/BTC spread widens (table + bar chart)
      - **Scenario Analysis**: preset scenarios (COVID crash, Terra/Luna, rate cuts) applied to current positions (impact table)
      - **Paper vs Live Comparison**: side-by-side Sharpe, returns, drawdown for paper vs live strategies (comparison table)
      - Mock data: extend risk page fixtures with attribution and scenario data
    status: todo
    note: "PARALLEL with p3-strategy-research-shell"

  # ── Phase 3 QG Gate ─────────────────────────────────────────────────────
  - id: p3-qg
    content: |
      - [ ] [AGENT] P0. Run quality-gates.sh / UI build on unified-trading-system-ui — pass
      `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build`
    status: todo
    note: "SEQUENTIAL — gate before Phase 4"

  # ── Phase 4: Final Validation ──────────────────────────────────────────
  - id: p4-final-qg
    content: |
      - [ ] [AGENT] P0. Final QG on all repos: UAC, strategy-service, ml-inference-service, unified-trading-system-ui
    status: todo
    note: "SEQUENTIAL — final validation"

isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_strategy_and_ui_2026_04_15.md](./consolidated_strategy_and_ui_2026_04_15.md).** ALSO superseded by
> archived strategy_lifecycle_maturity_model_2026_04_21 (Plan A — shipped + archived) Original scope retained for
> history. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

> **SUPERSEDED 2026-04-25 by
> [consolidated_strategy_and_ui_2026_04_15.md](./consolidated_strategy_and_ui_2026_04_15.md).** Original scope retained
> for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit formalises it as
> canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# Strategy Lifecycle, Visibility & UI

## Context

The system has sophisticated ML and execution pipelines but lacks operational controls, monitoring visibility, and
research tooling that institutional trading desks require. This plan addresses 8 deltas from the 2026-04-11 analysis
covering strategy lifecycle governance, model observability, and UI research tooling.

### Execution DAG

```
Phase 1 (PARALLEL) ─────────────────────────────────────────
  ├── [UAC] Lifecycle, lineage, composable, risk attribution schemas
  └── [strategy] Lifecycle state machine + paper comparison tracker
          │
       QG Gate (UAC + strategy-service)
          │
Phase 2 (PARALLEL within, SEQUENTIAL after P1) ─────────────
  ├── [strategy] Composable strategy building blocks
  ├── [ml-inference] Auto-retuning trigger
  └── [ml-inference + strategy] Prediction lineage tracking
          │
       QG Gate (strategy-service + ml-inference-service)
          │
Phase 3 (PARALLEL within, SEQUENTIAL after P2) ─────────────
  ├── [UI] ML model performance dashboard
  ├── [UI] Strategy research shell
  └── [UI] Risk attribution dashboard
          │
       QG Gate (UI build)
          │
Phase 4 (SEQUENTIAL) ───────────────────────────────────────
  └── Final QG on all 4 repos
```

### Success Criteria

- **Code:** quality-gates.sh passes on all repos, UI builds clean
- **Test:** Lifecycle transitions enforce gates correctly (reject invalid transitions); paper comparison tracker
  computes accurate Sharpe ratios; lineage records trace prediction→trade→P&L
- **Business (B3):** Lifecycle gates prevent untested models from going live; research shell enables faster strategy
  iteration; risk attribution visible for all active strategies in UI
