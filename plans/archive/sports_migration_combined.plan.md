---
doc_type: plan
title: sports-migration-combined
summary: Consolidates sports_migration_gap_fix and sports_migration_phase2_full — all actionable todos complete; live VCR
  cassettes blocked on api_keys_and_auth phase-4.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-09'
todos:
- {id: b1-scraper-adapters, content: 'B1 — Scraper adapters in USEI; validate CSS selectors; website version fingerprinting; Playwright in base image. DONE 2026-03-09: Added _CSS_H2H/_CSS_OVER_UNDER constants + validate_css_selectors() at module-import to all 13 full scraper adapters (bet365, betway, coral, williamhill, ladbrokes, bwin, paddypower, skybet, unibet, betvictor, betfred, bet888sport, boylesports). register_scraper_version() seeds ScraperVersionRegistry at import. get_odds() delegates to wrap_get_odds_with_stale_tracking() + _get_odds_inner() for auto stale-flagging. sbobet stub: register_scraper_version with css_selector_hash="stub". Added 39 new unit tests (3 per adapter). All 426 unit tests pass; coverage 80.44%. Commits: 32c5513.', status: done}
- {id: b5-b6-deployment, content: 'B5–B6 — Odds API validation; sports sharding; Dockerfile base image; deployment configs. DONE 2026-03-10: B5: odds_api_validator.py added to market-tick-data-service/adapters/sports/ (OddsValidationResult, validate_odds_payload, validate_canonical_odds_dict; 29 unit tests pass; basedpyright 0 errors). B6: Dockerfile + pip.conf added to features-sports-service (uses unified-trading-library base image — no Playwright; FSS is batch/API only). deployment-service configs updated: dependencies.yaml (features-sports-service entry + SPORTS category_domain_mapping), expected_start_dates.yaml (SPORTS category_start 2020-08-01, 8 leagues), checklist.features-sports-service.yaml (items 6,11,14,15 marked done). Commits: market-tick-data-service d5ebecc, deployment-service 406199d, features-sports-service ba62fa3.', status: done}
- {id: feature-calculators, content: 'FSS feature calculators — season_context, goal_timing, venue_context, referee; team features (split team_form, team_goals, team_xg, team_derived; each ≤900L). Pure Python, no external deps. Also: arb vig + is_arbitrage in features_sports_service/arb/ (currently only __init__.py).', status: done}
- {id: usei-adapters, content: 'USEI — Betfair and Pinnacle adapters (unit tests with VCR mocks). DONE 2026-03-09 (code + mock-tests): Betfair adapter fully implemented (exchanges/betfair.py: get_odds, place_order, cancel_order, list_orders, CanonicalSportsOrder). Pinnacle adapter fully implemented (bookmaker_api/pinnacle.py: get_odds, place_order, cancel_bet, place_bet). 28 unit tests (betfair_adapter: 18, pinnacle_adapter: 10) using mock objects/aioresponses. Added local cassettes betfair_list_market_catalogue.yaml + pinnacle_get_odds.yaml + 14 integration schema tests in test_vcr_betting_exchange_schemas.py. All 465 tests pass. Commits: 57a5b4b. NOTE: Live VCR cassette recording remains blocked pending API keys in SM (api_keys_and_auth.md phase-3-keys + phase-4-blockers) — cassettes are manually crafted mock data.', status: done}
- {id: strategy-execution, content: 'Strategy/execution — ArbitrageStrategy (reads vig + is_arbitrage from FSS, emits TradeSignal); MLSportsStrategy (consumes FSS features + PredictionEvent via UMI); execution_service places/cancels via USEI Betfair/Pinnacle mocks. Acceptance: quality-gates.sh passes; zero os.getenv; zero Any. DONE 2026-03-09: ArbitrageStrategy fully implemented with 86 tests (arbitrage detection, HT arb, bookmaker liquidity ranking, market liquidity ranking, odds comparison). MLSportsStrategy implemented in strategy_service/engine/strategies/sports/ml_sports_strategy.py — ML model probability predictions + fractional Kelly sizing, confidence gate, max-odds gate, model_id metadata annotation; 28 new unit tests all passing. MLSportsConfigDict TypedDict added to types.py. Exported from sports/__init__.py + strategies/__init__.py. Execution-service USEI routing: SportsAdapter, SportsRouter, _route_instruction, _execute_sports_instruction fully implemented with 55 tests (BET/CANCEL_BET
    -> USEI routing for BETFAIR/SMARKETS/MATCHBOOK/BETDAQ/PINNACLE). basedpyright: 0 errors on all new files. strategy-service unit tests: 969 passed, 1 skipped.', status: done}
isProject: false
---

# Sports Migration — Combined Plan

**Merged 2026-03-09** from:

- `sports_migration_gap_fix.md` (Part A complete; Part B in progress)
- `sports_migration_phase2_full.md`

## Completed Work (before merge)

### Gap Fix — Part A (DONE)

- Batch pipeline fully migrated from sports-betting-services-previous
- API contracts (CanonicalOdds, OddsType, progressive stats schemas)
- Live feature subset, feature cache, strategy-service sports arb
- Execution-service USEI routing
- PaperBettingAdapter + operation mode routing

### Phase 2 — Completed

- FSS config (UnifiedCloudConfig) + output schemas
- FSS engine (batch/live seam)
- Remaining features: h2h, league, odds, halftime, player_lineup, poisson_xg, multisource_xg, advanced_stats
- Data loader (in-memory DataFrames)

## Remaining Work

### Actionable Now (no external blockers)

1. **b1-scraper-adapters** — validate CSS selectors, add fingerprinting, finish Playwright adapter
2. **b5-b6-deployment** — update base image Dockerfile, instruments sports namespace
3. **feature-calculators** — season_context, goal_timing, venue_context, referee + arb/vig in FSS

### Blocked by API Keys (phase-4-blockers + phase-3-keys)

1. **usei-adapters** — Betfair + Pinnacle (need keys in SM to record VCR cassettes)
2. **strategy-execution** — depends on usei-adapters

## Blockers

| Blocker                | Type          | Specific Dependency                     | Resolution                           |
| ---------------------- | ------------- | --------------------------------------- | ------------------------------------ |
| Betfair key not in SM  | `[EXTERNAL]`  | api_keys_and_auth.md § phase-4-blockers | Obtain via betfair developer program |
| Pinnacle key not in SM | `[EXTERNAL]`  | api_keys_and_auth.md § phase-3-keys     | Obtain via pinnacle.com/affiliates   |
| USEI v1 not ready      | `[PLAN_TODO]` | usei-adapters (this plan)               | Unblocked once API keys in SM        |

## Standards

- `UnifiedCloudConfig` extension; no `os.getenv()`; secrets via `get_secret_client()`
- No `Any` in public API; `TypedDict`/`Protocol`/`dict[str, X]`
- Files ≤900L; functions ≤100L; methods ≤50L; classes ≤500L
- ruff (line-length 120) + basedpyright strict; MIN_COVERAGE=70
