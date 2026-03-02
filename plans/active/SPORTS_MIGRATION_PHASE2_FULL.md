# Sports Full Migration — Phase 2 (All Logic, UTS Standards)

Port **all** logic from `sports-betting-services` into UTS: all venues, all features, arbitrage, ML practices. Strategy service: arb (no ML) + other strategy types with ML signals. Execution service: place/cancel via USEI. Unit tests only; same quality gates (lint, line limits, types).

## Standards (strict)

- **Config:** `UnifiedCloudConfig` extension; no `os.getenv()`; secrets via `get_secret_client(secret_name=..., project_id=...)`.
- **Datetime:** `datetime.now(timezone.utc)` only.
- **Types:** No `Any`; use `TypedDict`, `Protocol`, `dict[str, X]`.
- **Files:** ≤900 lines (split team.py, models.py); functions ≤100; methods ≤50; classes ≤500.
- **Linting:** ruff (line-length 120), basedpyright; E501 enforced where not bypassed.
- **Tests:** Unit only for this migration; no external API auth in tests.

## Source inventory (sports-betting-services)

| Area | Modules | Lines (approx) | UTS destination |
|------|---------|----------------|-----------------|
| Core | config, database, models, mapping, feature_models, logging_service | 2308+320+259+462+127 | FSS config; schemas in FSS + UAC; data_loader in FSS |
| Features | base, data_loader, team, team_oop, h2h, league, season_context, referee, goal_timing, weather, venue_context, odds, halftime, player_lineup, poisson_xg, multisource_xg, advanced_stats, pipeline_test | 250–1528 each | FSS `features_sports_service/features/` (split team, base) |
| Arbitrage | analyze (script), analyze_bookmaker_vig, generate_report, odds (loader) | 260–552 | FSS `features_sports_service/arb/` (vig, arb_detection); strategy service consumes |
| Clients | api_football, footystats, open_meteo, soccer_football, understat | — | UAC schemas + UDC/URDI or FSS data adapters (unit-test with mocks) |
| Execution | — | — | USEI: Betfair, Pinnacle adapters |

## Strategy vs execution

- **Arb strategy:** No ML; uses vig + arb detection (best odds across bookmakers). Strategy service emits signals; execution service places/cancels via USEI.
- **ML strategies:** Consume FSS feature vectors + model predictions; different strategy types in strategy service.

## Implementation order

1. **DONE** FSS config (UnifiedCloudConfig) + output schemas
2. **DONE** FSS engine (orchestrates calculators; batch/live seam)
3. **DONE** Weather feature calculator; **DONE** arb vig + is_arbitrage (for strategy service)
4. **DONE** Unit tests: config, weather, arb, engine, schemas (22 tests, 78% coverage); lint/type/coverage pass
5. **TODO** Feature calculators: season_context, goal_timing, venue_context, referee
6. **TODO** Data loader (in-memory DataFrames; optional DB later)
7. **TODO** Team features (split: team_form, team_goals, team_xg, team_derived; each file ≤900 lines)
8. **TODO** Remaining features: h2h, league, odds, halftime, player_lineup, poisson_xg, multisource_xg, advanced_stats
9. **TODO** USEI: Betfair, Pinnacle adapters (unit tests with mocks)
10. **TODO** Strategy/execution: arb vs ML strategy types (consumers of FSS + USEI)
