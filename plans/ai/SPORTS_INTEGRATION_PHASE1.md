# Sports Integration — Phase 1 (Foundation)

Execute in order: Tier 0 → Tier 2 → Service. Unit tests only; no external API auth.
Follow AGENT_PROMPT_PHASE1.md, cursor rules, and codex.

## Scope

- **Source repo:** `sports-betting-services` (path: `other_repos/sports-betting-services` or workspace-equivalent). Logic (footballbets features, clients, core) to be ported in Phase 2+.
- **UTS venues:** Use canonical sports venues from `unified-api-contracts` (SPORTS_VENUES, VENUE_CATEGORY_MAP). Expand to include extra venues from sports-betting-services and existing UT venues.
- **Contracts:** All sports schemas live in T0 (unified-api-contracts). No inline schemas in services.

## Phase 1 Done (this session)

### Tier 0 — unified-api-contracts

- Added `SPORTS_VENUES` and sports entries in `VENUE_CATEGORY_MAP` (api_football, betfair, pinnacle, odds_api, footystats, soccer_football_info, open_meteo, understat, transfermarkt).
- Exported `SPORTS_VENUES` from package `__init__`.
- Added `tests/unit/test_sports_schemas.py`: schema validation for ApiFootball, Odds API, Betfair, Pinnacle, Open-Meteo, FootyStats, Soccer Football Info (no external API).

### Tier 2 — unified-sports-execution-interface

- Exported `BaseSportsAdapter` from `unified_sports_execution_interface.__init__`.
- Added `tests/unit/test_base_adapter.py`: mock adapter implements protocol; async get_markets/place_bet/cancel_bet (no network).
- Added pytest-asyncio and `unit` marker in pyproject.toml.

### features-sports-service

- Added `tests/unit/test_imports.py`: package import and adapters import (with Pub/Sub mocked).
- Existing `test_live_seams.py` retained. Registered `unit` marker in pyproject.toml.

## Next (Phase 2+)

- Port footballbets logic into features-sports-service (engine, feature calculators) using UAC schemas and USEI adapters.
- Add Betfair/Pinnacle adapter implementations in USEI (unit tests with mocks; integration later).
- Wire FSS into full pipeline (batch/live seams, Pub/Sub, GCS) per Phase 3.
- Add sports-betting-services repo to workspace or document as external source for porting.

## Key files

- `unified-trading-pm/workspace-manifest.json`: features-sports-service, unified-sports-execution-interface (completion_path: sports).
- `unified-trading-codex/04-architecture/TIER-ARCHITECTURE.md`: USEI T2, FSS service.
- `.cursor/plans/AGENT_PROMPT_PHASE1.md`, PHASE2.md, PHASE3.md: execution order and done criteria.
