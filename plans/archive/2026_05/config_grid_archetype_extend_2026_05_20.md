---
doc_type: plan
title: Extend run_2yr_config_grid_backtest.py to all 6 Tier-A archetype families
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-20
archived: 2026-05-23
priority: P1
parent_epic: strategy_master
assigned_vm: vm-trading-core
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

Missing families per `/codex/09-strategy/mvp-universe-per-asset-group.md`:

| Family                  | StrategyArchetype enum member  | Notes                                           |
| ----------------------- | ------------------------------ | ----------------------------------------------- |
| ml-continuous           | `ML_DIRECTIONAL_CONTINUOUS`    | ML model with rolling-retrain cadence           |
| ml-settled              | `ML_DIRECTIONAL_EVENT_SETTLED` | ML model for discrete event outcomes            |
| arbitrage-sportsbook    | `MARKET_MAKING_EVENT_SETTLED`  | Sports book vs prediction market spread         |
| arbitrage-event-markets | `ARBITRAGE_CROSS_DOMAIN_EVENT` | Polymarket vs CME (see cme_polymarket_arb plan) |

## Blocking design decision

Each new family needs a `_DIMENSIONS_BY_ARCHETYPE` dict entry with per-dimension `GridDimension(coarse, medium, fine)`
tuples, a `_dim_kwargs` branch, and a `_build_config_grid` branch in `run_2yr_config_grid_backtest.py`.

Dimension choices required per family:

| Family                  | Dimensions needed (operator/author to specify)                                                |
| ----------------------- | --------------------------------------------------------------------------------------------- |
| ml-continuous           | `regime_window_days`, `confidence_threshold`, `position_size_pct`, `max_drawdown_threshold`   |
| ml-settled              | `event_prob_threshold`, `side_size_factor`, `max_drawdown_threshold`, `slippage_cap_bps`      |
| arbitrage-sportsbook    | `edge_threshold_bps`, `round_trip_fee_cap_bps`, `position_size_pct`, `max_drawdown_threshold` |
| arbitrage-event-markets | `price_dispersion_threshold_bps`, `arb_window_seconds`, `hedge_ratio`, `slippage_cap_bps`     |

## Phased execution

- [x] **[BLOCKED-OPERATOR-DECISION 2026-05-20 slot-4]** [DESIGN] P0. Confirm per-archetype grid dimension names +
      coarse/medium/fine value tuples. **CRITICAL MISMATCH FOUND**: the plan's proposed dimension names do NOT match the
      actual engine params in `strategy_service/engine/strategies/v2/`:

      | Family | Plan's proposed dims | Actual engine params |
                                                                                                                      |---|---|---|
                                                                                                                      | ml-continuous (`MLDirectionalContinuousEngine`) | `regime_window_days`, `confidence_threshold`, `position_size_pct`, `max_drawdown_threshold` | `confidence_threshold`, `max_position_fraction`, `min_mid_price` (`regime_window_days` does NOT exist) |
                                                                                                                      | ml-settled (`MLDirectionalEventSettledEngine`) | `event_prob_threshold`, `side_size_factor`, `max_drawdown_threshold`, `slippage_cap_bps` | `min_confidence`, `min_edge`, `max_odds`, `kelly_fraction`, `max_stake_fraction` (none of the plan's names match) |
                                                                                                                      | arbitrage-sportsbook (`MarketMakingEventSettledEngine`) | `edge_threshold_bps`, `round_trip_fee_cap_bps`, `position_size_pct`, `max_drawdown_threshold` | `half_spread_bps`, `max_inventory_abs`, `refresh_cadence_ms`, `refresh_threshold_bps` (none match) |
                                                                                                                      | arbitrage-event-markets (`ARBITRAGE_CROSS_DOMAIN_EVENT`) | `price_dispersion_threshold_bps`, `arb_window_seconds`, `hedge_ratio`, `slippage_cap_bps` | **NO ENGINE IN FACTORY** — `ARCHETYPE_ENGINE_REGISTRY` has no entry for `ARBITRAGE_CROSS_DOMAIN_EVENT`. Grid sweep would crash at registration lookup. |

                                                                                                                      Operator must choose: (a) update the plan's proposed dimension names to match the actual engine params, OR
                                                                                                                      (b) add the proposed params to each engine first, THEN implement the grid dimensions.
                                                                                                                      Separate decision needed for `ARBITRAGE_CROSS_DOMAIN_EVENT`: either (i) implement the engine first, or
                                                                                                                      (ii) defer this archetype and extend the grid for 3 of 4.
                                                                                                                      Ping: `harsh_orchestrator/pings/slot_4.md` [2026-05-20 UTC].
                                                                                                                      **[DEFERRED-OPERATOR-DECISION 2026-05-23 slot 2]** No operator response since 2026-05-20. Plan is P1
                                                                                                                      (post-cutover). Requires strategy-service (not in worktree). Deferred to post-DeFi-cutover.

- [x] **[BLOCKED-OPERATOR-DECISION — depends on item 1]** [SCRIPT] P0. Add 4 `_DIMENSIONS_BY_ARCHETYPE` entries +
      `_dim_kwargs` branches + `_build_config_grid` branches in
      `strategy-service/scripts/run_2yr_config_grid_backtest.py`. Extend `SUPPORTED_ARCHETYPES` tuple. Run QG. Cannot
      implement without confirmed dimension names from item 1. `ARBITRAGE_CROSS_DOMAIN_EVENT` additionally requires
      engine factory registration before this item can close. **[DEFERRED-OPERATOR-DECISION 2026-05-23 slot 2]** Gated
      on item 1 + strategy-service repo.

- [x] **[BLOCKED-OPERATOR-DECISION — depends on item 2]** [SCRIPT] P0. Add `specs_for_archetype` smoke test per new
      family: 5-day synthetic window, coarse density, assert grid CSV non-empty + P&L delta within expected range.
      Target: QG passes in <5 min on c3-highcpu-44. **[DEFERRED-OPERATOR-DECISION 2026-05-23 slot 2]** Gated on items
      1+2 + strategy-service repo.

## Done definition

`SUPPORTED_ARCHETYPES` covers all 6 Tier-A families; 4 new integration tests pass; `quality-gates.sh` green; plan
flipped.

## Deferred work — migrated to:

All 3 items DEFERRED-OPERATOR-DECISION 2026-05-23 slot 2. No implementation. Migrated to `strategy_master` §
post-cutover backlog:

- **Confirm per-archetype grid dimension names (P0, BLOCKED-OPERATOR-DECISION)**: Migrated to: strategy_master §
  post-cutover backlog. Critical mismatch between plan's proposed dims and actual engine params (see plan body);
  operator must choose (a) update plan dims to match engine or (b) add params to engines first.
  `ARBITRAGE_CROSS_DOMAIN_EVENT` additionally needs engine factory registration.
- **Implement `_DIMENSIONS_BY_ARCHETYPE` entries + grid branches (P0)**: Gate: operator decision above.
- **Smoke test per new family (P0)**: Gate: implementation above + strategy-service repo.
