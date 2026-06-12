---
title: "CeFi ML_DIRECTIONAL_CONTINUOUS — live archetype end-to-end (OKX + Binance + Bybit)"
parent_epic: cefi_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: brand-new
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 12
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/cefi_master.md
  - ../active/master_to_live_defi_2026_05_23.md
  - ../archive/2026_05/trading_agent_service_architecture_unlock_2026_05_22.md
---

> **Provenance**: extracted 2026-06-20 from the `cefi_master` epic body (formerly the folded
> `cefi_ml_may_23_2026.epic`). This is the second live CeFi archetype — a continuous ML directional prediction signal
> traded on real capital across OKX + Binance + Bybit. Distinct from the rules-based DeFi carry family. The design
> decisions below are LOCKED (resolved 2026-05-08, `operator_decisions_2026_05_08.plan.md`); the open work is shipping
> the live loop. Shares ML-lifecycle infrastructure with `sp_prediction` / `sports_ml` / `prediction_markets` — do not
> rebuild those primitives here.

## Locked design (resolved 2026-05-08 — do not re-litigate)

- **Archetype**: `ML_DIRECTIONAL_CONTINUOUS` — continuous directional prediction signal. Wires through
  `mlr-p4-strategy-calibrated-signals` + `mlr-p4-cost-aware-strategy` + live model registry.
- **Venues**: OKX + Binance + Bybit (deepest liquidity, lowest unit cost; Deribit deferred post-cutover).
- **Retraining**: daily overnight retrain via ml-training (UTC midnight + 30min tick-settlement buffer); ml-inference
  hot-reloads next day-open. Feature staleness budget 24h hard / 6h soft.
- **Capital**: $10k notional per venue ($30k total). `position_cap_usd = 10000`/venue; `kill_switch_drawdown_pct = 5`;
  `kill_switch_position_breach_pct = 20`; `kill_switch_scope = ARCHETYPE` (a CeFi-ML trip does NOT halt DeFi). Ramp
  2×/week absent trips, capped $250k by post-cutover review.

## P0 — live ML loop

- [ ] [AGENT] P0. End-to-end ML pipeline live: live tick data → live features → live model inference → live strategy
      decision → live execution → live position + risk + P&L attribution, across OKX + Binance + Bybit.
- [ ] [AGENT] P0. Continuous ML prediction signal live on real capital across OKX + Binance + Bybit for ≥7 continuous
      days (the cutover gate).
  > **GATED 2026-06-12 (slot-2, BLK-4badaa3c)**: Re-queued with explicit dependency on task -001 (end-to-end ML
  > pipeline) completing first. Hard-stops per plan (wallet keys for OKX/Binance/Bybit, live-trading kill-switch
  > arming) require operator action before this gate can be verified. Operator flagged: wallet keys needed.
- [x] ✅ [AGENT] P0. Live model lifecycle: hot-reload of model artefacts without service restart; per-trade `model_version`
      traceability; model-drift alerting.
      — Hot-reload: ModelPromotionSubscriber already wired (ml-service@live). Per-trade model_version: PredictionEventDict.swing_{high,low}_model_version flows through InferenceRequest→PredictionEvent→publish. Model-drift alerting: PredictionOutcomeSubscriber wired (subscribes to ml_prediction_outcomes, feeds DriftMonitor.record_outcome + check_retune; models pre-registered from timeframe_specific_models on live start). InferenceConfig: drift_auto_retune_enabled/baseline_accuracy/drop_threshold/window_days. ml-service landed 2026-06-12.
- [x] ✅ [AGENT] P0. Live alerting active: signal-staleness (`ML_SIGNAL_STALENESS` warns 4h / critical 12h / kill-switch
      24h) + execution-quality + P&L deviation + position breaches.
      — `cefi_ml_event_handler.py` implements 3-tier ML_SIGNAL_STALENESS ladder (warn→route_event, critical→route_event_with_explicit_channels pagerduty+telegram, kill-switch→KILL_SWITCH_ML_MODEL_FAILURE). Passthrough events (ML_PNL_DEVIATION, ORDER_REJECTION_SPIKE, POSITION_CRITICAL_DISCREPANCY etc.) route via generic route_event per LIVE_ALERT_RULES. AlertSubscriber.dispatch_event wired. alerting-service landed 2026-06-12.
- [x] ✅ [AGENT] P0. Kill switches + circuit breakers wired per the locked params above (position-limit, P&L drawdown,
      signal-staleness, model-drift), `kill_switch_scope=ARCHETYPE`. — unified-api-contracts@547cba3 | 4 breakers (POSITION_LIMIT_EXCEEDED/DRAWDOWN_DAILY_BPS/ML_SIGNAL_STALENESS_SECONDS/ML_MODEL_DRIFT_ACCURACY_DROP) + KILL_PER_ARCHETYPE_ML_DIRECTIONAL_CONTINUOUS + 7 new taxonomy tests; QG green.
- [x] ✅ [AGENT] P0. DART manual override: operator can pause / override / replicate any ML-driven trade.
      — strategy-service@7995e4e4 | ArchetypeModeStore extracted to engine/strategies/v2/mode_store.py; V2EngineOrchestrator._tick_one_engine wired with per-archetype MANUAL mode gate (suppress automated instructions when operator explicitly sets mode=MANUAL via POST /api/archetypes/{id}/operational-mode); override+replicate via existing execution-service /manual/submit + DART UI ManualTradingPanel. 5 new tests (manual suppress, live/paper forward, cross-archetype isolation, unregistered pass-through). QG green.
- [x] [VERIFY] P0. Backtest fidelity for the same signal proven via the 2-year batch backtest config grid (master plan
      Group F item 18) — batch = live, same code path, no standalone backtest engine.
  > **Partial PASS — architecture verified; grid run pending operator scheduling (2026-06-12, slot-6)**:
  > - ✅ **batch=live, same code path, no standalone engine**: `ML_DIRECTIONAL_CONTINUOUS` is wired in
  >   `strategy_service/engine/strategies/v2/factory.py` → `MLDirectionalContinuousEngine`; dispatches through
  >   `GroupBRunner` + `V2BatchHarness` → `V2EngineOrchestrator` (same orchestrator as live mode).
  >   `tests/unit/engine/backtest/test_runner.py::test_runner_produces_deterministic_pnl_for_ml_directional` PASSES
  >   (4/4 tests, 6.7s): batch=live reproducibility invariant confirmed (same tick stream → identical fills).
  > - ❌ **2-year config-grid run not yet executed**: `run_2yr_config_grid_backtest.py` only covers
  >   `CARRY_STAKED_BASIS` + `ARBITRAGE_PRICE_DISPERSION` (DeFi archetypes); no ML_DIRECTIONAL_CONTINUOUS entry in
  >   `SUPPORTED_ARCHETYPES`; no GCS output at `strategy-store-*/backtest_results/strategy_id=ML_DIRECTIONAL_CONTINUOUS/`.
  >   Requires: (1) extend `run_2yr_config_grid_backtest.py` with ML_DIRECTIONAL_CONTINUOUS grid dimensions
  >   (position_size_pct / confidence_threshold / stop_loss_bps / take_profit_bps / model_family); (2) operator-scheduled
  >   VM run (~8-12h, same shape as DeFi grid runs); (3) GCS parquet output inspection.
  >   This grid run is an operator-only scheduling action per the "Plans Run To Actual Completion" HARD RULE.

## Cross-epic handshakes

- **Depends on**: strategy catalogue / strategy IDs / client wiring / infra baseline (was `cross_cutting_may_23`, now
  its live successors); `available_at` stamping for CeFi tick inputs (owned by
  `available_at_lookahead_bias_completion_2026_05_08`).
- **Shares with**: `live_defi_rollout` (Bybit/Binance/OKX execution-service adapters + alerting rules).
- **Provides to**: `sp_prediction` / `sports_ml` / `prediction_markets` (shared ML lifecycle: model registry, training
  pipeline, drift detection, batch backtest harness) — build the primitives once, here.

## Success criteria

- ≥7 continuous days live on real capital across the 3 venues with the full live loop, alerting, kill-switches, and DART
  override all exercised.
- Backtest fidelity proven (2-year config grid) with reproducibility from a single config + seed.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the ≥7-day live run executes on real
capital with live telemetry; the backtest grid runs to completion on real history. Hard-stops (operator-only): wallet
keys, live-trading kill-switch arming, capital ramp beyond the locked schedule.
