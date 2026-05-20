---
title: Extend run_2yr_config_grid_backtest.py to all 6 Tier-A archetype families
type: plan
status: active
created: 2026-05-20
deadline: 2026-05-23
horizon: pre-cutover
companion_to: compute_optimization_mock_data_2026_05_13.md (Phase 1 EXTEND)
locked_by: live-defi-rollout
locked_since: 2026-05-20
priority: P1
parent_epic: strategy_and_dart_master_2026_05_07.md
spawned_from: |
  MIGRATED FROM compute_optimization_mock_data_2026_05_13.md Phase 1 EXTEND.
  Verification (slot 7, 2026-05-14) confirmed run_2yr_config_grid_backtest.py covers only
  2 of 6 Tier-A families. EXTEND blocked on per-archetype grid dimension design choices.
  Migrated to this successor plan 2026-05-20 slot 8.
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
---

**MIGRATED FROM:** `plans/active/compute_optimization_mock_data_2026_05_13.md` § Phase 1 EXTEND (slot 8, 2026-05-20)

# Extend config-grid backtest to all 6 Tier-A archetype families

## Context

`strategy-service/scripts/run_2yr_config_grid_backtest.py` currently supports 2 of 6 Tier-A archetype families:

- `CARRY_STAKED_BASIS` ✅ (defi-carry-family)
- `ARBITRAGE_PRICE_DISPERSION` ✅ (arbitrage-funding-rate)

Missing families per `codex/09-strategy/mvp-universe-per-asset-group.md`:

| Family              | StrategyArchetype enum member       | Notes                                          |
| ------------------- | ----------------------------------- | ---------------------------------------------- |
| ml-continuous       | `ML_DIRECTIONAL_CONTINUOUS`         | ML model with rolling-retrain cadence          |
| ml-settled          | `ML_DIRECTIONAL_EVENT_SETTLED`      | ML model for discrete event outcomes           |
| arbitrage-sportsbook | `MARKET_MAKING_EVENT_SETTLED`      | Sports book vs prediction market spread        |
| arbitrage-event-markets | `ARBITRAGE_CROSS_DOMAIN_EVENT`  | Polymarket vs CME (see cme_polymarket_arb plan) |

## Blocking design decision

Each new family needs a `_DIMENSIONS_BY_ARCHETYPE` dict entry with per-dimension
`GridDimension(coarse, medium, fine)` tuples, a `_dim_kwargs` branch, and a `_build_config_grid`
branch in `run_2yr_config_grid_backtest.py`.

Dimension choices required per family:

| Family              | Dimensions needed (operator/author to specify)                                                    |
| ------------------- | ------------------------------------------------------------------------------------------------- |
| ml-continuous       | `regime_window_days`, `confidence_threshold`, `position_size_pct`, `max_drawdown_threshold`      |
| ml-settled          | `event_prob_threshold`, `side_size_factor`, `max_drawdown_threshold`, `slippage_cap_bps`         |
| arbitrage-sportsbook | `edge_threshold_bps`, `round_trip_fee_cap_bps`, `position_size_pct`, `max_drawdown_threshold`   |
| arbitrage-event-markets | `price_dispersion_threshold_bps`, `arb_window_seconds`, `hedge_ratio`, `slippage_cap_bps`   |

## Phased execution

- [ ] [DESIGN] P0. **[BLOCKED-OPERATOR-DECISION]** Confirm per-archetype grid dimension names + coarse/medium/fine
      value tuples. Source: `codex/09-strategy/mvp-universe-per-asset-group.md` author or operator direction.
      Without this, `_DIMENSIONS_BY_ARCHETYPE` entries cannot be written without guessing.

- [ ] [SCRIPT] P0. Add 4 `_DIMENSIONS_BY_ARCHETYPE` entries + `_dim_kwargs` branches + `_build_config_grid` branches
      in `strategy-service/scripts/run_2yr_config_grid_backtest.py`. Extend `SUPPORTED_ARCHETYPES` tuple. Run QG.

- [ ] [SCRIPT] P0. Add `specs_for_archetype` smoke test per new family: 5-day synthetic window, coarse density,
      assert grid CSV non-empty + P&L delta within expected range. Target: QG passes in <5 min on c3-highcpu-44.

## Done definition

`SUPPORTED_ARCHETYPES` covers all 6 Tier-A families; 4 new integration tests pass; `quality-gates.sh` green;
plan flipped.
