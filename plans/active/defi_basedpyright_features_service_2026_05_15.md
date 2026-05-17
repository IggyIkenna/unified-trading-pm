---
title: "basedpyright reportAny cleanup — features-service"
created: 2026-05-15
author: ikenna
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
locked_by: live-defi-rollout
locked_since: 2026-05-15
---

**MIGRATED FROM:** `defi_master_2026_05_07.md` line 292 deferral **Status:** DEFERRED — 825 reportAny errors remain in
features-service

## Context

features-service has 825 `reportAny` errors blocking basedpyright clean. The other 3 DeFi service repos
(strategy-service, risk-and-exposure-service, execution-service) are at 0 errors.

This plan tracks the remaining work to bring features-service to 0 reportAny errors.

## Error profile (2026-05-15 snapshot)

825 errors, primarily in:

- `features_service/calculators/` — numpy array operations + pandas row access
- `features_service/adapters/` — external API resp.json() calls
- `features_service/onchain/` — driftpy / web3 untyped attributes

## Approach

Same patterns as execution-service fix:

- `cast(dict[str, object], resp.json())` for HTTP response bodies
- `cast(list[float], arr.tolist())` for numpy arrays
- `cast(object, getattr(obj, "attr", default))` for untyped library objects
- `cast(int, df["col"].iloc[0])` for pandas scalar extraction

## Tasks

- [ ] [AGENT] P0. Run basedpyright on features-service and triage top 10 error locations.
- [ ] [AGENT] P0. Fix cast() wrappers in features_service/calculators/ (expected ~300 errors).
  - [x] ✅ transfer_window_calculator.py 32→0 errors — features-service@9183f81f (slot-8 2026-05-17)
  - [x] ✅ season_context.py 28→0 errors — features-service@5199db4d (slot-8 2026-05-17)
  - [x] ✅ team_form.py 28→0 errors — features-service@62e460cf (slot-8 2026-05-17)
  - [x] ✅ sports_validity_engine.py 26→0 errors (engine/ surface) — features-service@d2013034 (slot-8 2026-05-17)
  - [x] ✅ poisson_xg_calculator.py 17→0 errors — features-service@5aa6079f (slot-8 2026-05-17)
  - [x] ✅ elo_calculator.py 17→0 errors — features-service@5aa6079f (slot-8 2026-05-17)
  - [x] ✅ delta_one/app/calculators/returns.py 23→0 errors — features-service@e14fdae8 (slot-8 wave 2 2026-05-17)
  - [x] ✅ delta_one/app/calculators/trendline.py 19→0 errors — features-service@e14fdae8 (slot-8 wave 2 2026-05-17)
  - [x] ✅ delta_one/app/utils/numba_kernels.py 37→0 errors — features-service@be6f01a5 (slot-8 wave 2 2026-05-17)
  - [x] ✅ delta_one/app/calculators/streaks.py 18→0 errors — features-service@8828900b (slot-8 wave 2 2026-05-17)
  - [x] ✅ delta_one/app/calculators/market_structure_sequence.py 14→0 errors — features-service@8828900b (slot-8 wave 2
        2026-05-17)
  - [x] ✅ sports/calculators/travel_calculator.py 14→0 errors — features-service@360a804d (slot-8 wave 2 2026-05-17)
  - [x] ✅ sports/calculators/referee_features.py 14→0 errors — features-service@360a804d (slot-8 wave 2 2026-05-17)
  - [x] ✅ sports/calculators/halftime_calculator.py 14→0 errors — features-service@360a804d (slot-8 wave 2 2026-05-17)
  - [x] ✅ sports/calculators/advanced_stats_calculator.py 14→0 errors — features-service@360a804d (slot-8 wave 2
        2026-05-17)
  - [x] ✅ sports/smoke.py 11→0 errors — features-service@f64cb47a (slot-8 wave 3 2026-05-17)
  - [x] ✅ delta_one/smoke.py 11→0 errors — features-service@f64cb47a (slot-8 wave 3 2026-05-17)
  - [x] ✅ multi_timeframe/smoke.py 11→0 errors — features-service@f64cb47a (slot-8 wave 3 2026-05-17)
  - [x] ✅ commodity/smoke.py 11→0 errors — features-service@f64cb47a (slot-8 wave 3 2026-05-17)
  - [x] ✅ calendar/smoke.py 11→0 errors — features-service@f64cb47a (slot-8 wave 3 2026-05-17)
  - [x] ✅ delta_one/engine/delta_one_validity_engine.py 23→0 errors — features-service@6d402524 (slot-8 wave 3
        2026-05-17)
  - [x] ✅ delta_one/app/core/multi_period_features.py 15→0 errors — features-service@6d402524 (slot-8 wave 3
        2026-05-17)
  - [x] ✅ sports/exporters/derived_features_helpers.py 13→0 errors — features-service@8444039c (slot-8 wave 3)
  - [x] ✅ sports/calculators/h2h_calculator.py 13→0 errors — features-service@8444039c (slot-8 wave 3)
  - [x] ✅ sports/calculators/european_fatigue_calculator.py 13→0 errors — features-service@8444039c (slot-8 wave 3)
  - [x] ✅ sports/calculators/sfi_progressive_calculator.py 12→0 errors — features-service@8444039c (slot-8 wave 3)
  - [x] ✅ delta_one/app/calculators/volume.py 11→0 errors — features-service@b3e72d41 (slot-8 wave 4 2026-05-17)
  - [x] ✅ delta_one/app/core/futures_roll_adjuster.py 9→0 errors — features-service@b3e72d41 (slot-8 wave 4 2026-05-17)
  - [x] ✅ delta_one/app/calculators/supply_demand_zones.py 8→0 errors — features-service@b3e72d41 (slot-8 wave 4
        2026-05-17)
  - [x] ✅ delta_one/app/calculators/fibonacci.py 8→0 errors — features-service@b3e72d41 (slot-8 wave 4 2026-05-17)
  - [x] ✅ sports/calculators/replacement_model_calculator.py 10→0 errors — features-service@d7a4574b (slot-8 wave 4
        2026-05-17)
  - [x] ✅ sports/calculators/goal_timing.py 9→0 errors — features-service@d7a4574b (slot-8 wave 4 2026-05-17)
  - [x] ✅ sports/calculators/team_goals.py 7→0 errors — features-service@d7a4574b (slot-8 wave 4 2026-05-17)
  - [x] ✅ sports/calculators/manager_calculator.py 7→0 errors — features-service@d7a4574b (slot-8 wave 4 2026-05-17)
  - [x] ✅ sports/calculators/league_calculator.py 7→0 errors — features-service@d7a4574b (slot-8 wave 4 2026-05-17)
  - [x] ✅ sports/exporters/odds_features_exporter.py 7→0 errors — features-service@d7a4574b (slot-8 wave 4 2026-05-17)
  - [x] ✅ features_service/sports/ FULL CLEAN — bench_sub_calculator, footystats_predictions_calculator, formation_calculator, halftime_multi_source, ht_features, injury_impact_calculator, meta_features_calculator, odds_prob_space, squad_value_calculator, _fetch_runner, batch_handler, live_handler, cli/main, config_reloaders, gcs_normalizers, feature_builder_registry (46→0) — features-service@5f4e0112 (slot-8 wave 5 2026-05-17)
  - [x] ✅ features_service/delta_one/ FULL CLEAN — 23 files, 53→0 errors: anomaly, base, base_calculator, candlestick, kurtosis, liquidation_levels, market_structure, momentum, order_flow_inference, oscillators, polynomial_trendline, round_numbers, volatility, wedge_detector, dependency_checker, feature_writer, batch_handler, live_handler, target_handler, cli/main, cli/parser, config_reloaders, orchestrator — features-service@c0b7415c (slot-8 wave 5 2026-05-17)
- [ ] [AGENT] P0. Fix cast() wrappers in features_service/adapters/ (expected ~200 errors).
- [ ] [AGENT] P0. Fix cast() wrappers in features_service/onchain/ (expected ~200 errors).
- [x] ✅ [AGENT] P0. Fix remaining errors in other modules. — features-service@dad0b74a (slot-8 wave 4 2026-05-17)
  - [x] ✅ calendar/ family (15 errors): yfinance_earnings_adapter, batch_handler, corporate_actions_handler,
        config_reloaders, economic_calendar_loader, calendar_orchestrator, mock_data_provider, feature_builder_registry
        — features-service@dad0b74a
  - [x] ✅ volatility/ family (11 errors): batch_handler, live_handler, service_entry, config_reloaders, feature_writer,
        orchestration_service, mock_data_provider — features-service@dad0b74a
  - [x] ✅ multi_timeframe/ family (11 errors): cli/main, mock_data_provider, orchestrator — features-service@dad0b74a
  - [x] ✅ commodity/ family (7 errors): cli/main, config_reloaders, mock_data_provider — features-service@dad0b74a
  - [x] ✅ basedpyright: 0 errors, 0 warnings, 0 notes on all 4 family dirs — confirmed 2026-05-17
- [ ] [AGENT] P0. Verify basedpyright 0 errors, run quality-gates.sh, commit+push.
- [ ] [AGENT] P0. Flip checkbox in defi_master_2026_05_07.md.

## Temporary states + their canonical follow-up plans

None.
