---
doc_type: plan
title: Sports Migration Phase 2 Full
summary: Port all logic from sports-betting-services into UTS. All venues, features, arbitrage, ML practices. Strategy service
  arb + ML; execution via USEI. Unit tests only; strict quality gates.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-02'
todos:
- {id: feature-calculators, content: 'Feature calculators — season_context, goal_timing, venue_context, referee; team features (split team_form, team_goals, etc.)', status: pending}
- {id: data-loader, content: Data loader — in-memory DataFrames; optional DB later, status: done}
- {id: remaining-features, content: 'Remaining features — h2h, league, odds, halftime, player_lineup, poisson_xg, multisource_xg, advanced_stats', status: done}
- {id: usei-adapters, content: 'USEI — Betfair, Pinnacle adapters (unit tests with mocks)', status: pending}
- {id: strategy-execution, content: 'Strategy/execution — arb vs ML strategy types; consumers of FSS + USEI. ACCEPTANCE: (1) ArbitrageStrategy class reads vig + is_arbitrage from FSS output, emits TradeSignal with venue/odds/stake; unit tests mock FSS + USEI, verify signal emitted when arb margin > threshold; (2) MLSportsStrategy consumes FSS feature vectors + PredictionEvent (via unified-ml-interface), emits TradeSignal; unit tests mock FSS + UMI, verify signal at correct confidence threshold; (3) execution_service places/cancels via USEI Betfair/Pinnacle mocks; verify correct order type (back/lay) and stake calculation; (4) quality-gates.sh passes (ruff + basedpyright strict + MIN_COVERAGE=70); zero os.getenv; zero Any in public API.', status: pending}
isProject: false
---

# Sports Full Migration — Phase 2 (All Logic, UTS Standards)

Port **all** logic from `sports-betting-services` into UTS: all venues, all features, arbitrage, ML practices. Strategy
service: arb (no ML) + other strategy types with ML signals. Execution service: place/cancel via USEI. Unit tests only;
same quality gates (lint, line limits, types).

## Blockers

| Blocker                                                    | Type          | Specific Dependency                                                                                                                     | Resolution                                                                                                                            |
| ---------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| sports_migration_gap_fix Part B not substantially complete | `[PLAN_TODO]` | [sports_migration_gap_fix.plan.md](sports_migration_gap_fix.plan.md) § todos `b1-scraper-adapters` through `b5-b6-deployment`           | Phase 2 Full ports the remaining logic; Part B gap fix must establish USEI adapters + live mode seams first                           |
| USEI v1 (Betfair + Pinnacle adapters) not ready            | `[PLAN_TODO]` | [phase2_library_tier_hardening.plan.md](phase2_library_tier_hardening.plan.md) § todo `t2-tests-first` (usei-v1-betfair-pinnacle entry) | sports_migration_phase2_full todos `usei-adapters` + `strategy-execution` depend on USEI v1 being implemented                         |
| Betfair and Pinnacle API keys not in SM                    | `[EXTERNAL]`  | [api_keys_and_auth.plan.md](api_keys_and_auth.plan.md) § todo `phase-4-blockers` (betfair) and `phase-3-keys` (pinnacle)                | USEI adapter unit tests require cassettes; cassettes require the keys to record; betfair key not in SM, pinnacle key not obtained yet |

---

## Standards (strict)

- **Config:** `UnifiedCloudConfig` extension; no `os.getenv()`; secrets via
  `get_secret_client(secret_name=..., project_id=...)`.
- **Datetime:** `datetime.now(timezone.utc)` only.
- **Types:** No `Any`; use `TypedDict`, `Protocol`, `dict[str, X]`.
- **Files:** ≤900 lines (split team.py, models.py); functions ≤100; methods ≤50; classes ≤500.
- **Linting:** ruff (line-length 120), basedpyright; E501 enforced where not bypassed.
- **Tests:** Unit only for this migration; no external API auth in tests.

## Source inventory (sports-betting-services)

| Area      | Modules                                                                                                                                                                                                | Lines (approx)       | UTS destination                                                                    |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------- | ---------------------------------------------------------------------------------- |
| Core      | config, database, models, mapping, feature_models, logging_service                                                                                                                                     | 2308+320+259+462+127 | FSS config; schemas in FSS + UAC; data_loader in FSS                               |
| Features  | base, data_loader, team, team_oop, h2h, league, season_context, referee, goal_timing, weather, venue_context, odds, halftime, player_lineup, poisson_xg, multisource_xg, advanced_stats, pipeline_test | 250–1528 each        | FSS `features_sports_service/features/` (split team, base)                         |
| Arbitrage | analyze (script), analyze_bookmaker_vig, generate_report, odds (loader)                                                                                                                                | 260–552              | FSS `features_sports_service/arb/` (vig, arb_detection); strategy service consumes |
| Clients   | api_football, footystats, open_meteo, soccer_football, understat                                                                                                                                       | —                    | UAC schemas + UDC/URDI or FSS data adapters (unit-test with mocks)                 |
| Execution | —                                                                                                                                                                                                      | —                    | USEI: Betfair, Pinnacle adapters                                                   |

## Strategy vs execution

- **Arb strategy:** No ML; uses vig + arb detection (best odds across bookmakers). Strategy service emits signals;
  execution service places/cancels via USEI.
- **ML strategies:** Consume FSS feature vectors + model predictions; different strategy types in strategy service.

## Implementation order

1. **DONE** FSS config (UnifiedCloudConfig) + output schemas
2. **DONE** FSS engine (orchestrates calculators; batch/live seam)
3. **NOT DONE** Weather feature calculator (weather.py not found in features_sports_service/calculators/ — only
   ht_features.py and ml_predictions.py present); **NOT DONE** arb vig + is_arbitrage (features_sports_service/arb/
   contains only **init**.py — no implementation)
4. **UNVERIFIED** Unit tests: claimed "22 tests, 78% coverage" — tests/unit/ now has 57 test functions across 10 files
   (count may have grown with other additions); lint/type/coverage pass status unknown without running quality gates
5. **TODO** Feature calculators: season_context, goal_timing, venue_context, referee
6. **TODO** Data loader (in-memory DataFrames; optional DB later)
7. **TODO** Team features (split: team_form, team_goals, team_xg, team_derived; each file ≤900 lines)
8. **TODO** Remaining features: h2h, league, odds, halftime, player_lineup, poisson_xg, multisource_xg, advanced_stats
9. **TODO** USEI: Betfair, Pinnacle adapters (unit tests with mocks)
10. **TODO** Strategy/execution: arb vs ML strategy types (consumers of FSS + USEI)
