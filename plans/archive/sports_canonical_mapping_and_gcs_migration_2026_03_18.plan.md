---
doc_type: plan
title: sports-canonical-mapping-and-gcs-migration
summary: "Consolidate all sports canonical ID mappings into UAC (their correct SSOT),\nremove duplicate implementations\
  \ scattered across instruments-service and\ndeployment-service, and write a GCS migration script for existing sports data.\n\
  \n## Problem\nSports mapping data (league registry, team aliases, stadium names, player name\nnormalisation) lives in\
  \ instruments-service/sports/ (17 files) and\ndeployment-service/scripts/sports/. Zero of it is in UAC where it belongs.\n\
  Downstream services that need the same data either re-implement or go without.\n\n## Solution\n1. Lift all type/data definitions\
  \ into UAC (canonical/ + external/api_football/ +\n   external/odds_api/) and export via the sports facade.\n2. instruments-service\
  \ deletes its local sports/ implementations and imports UAC.\n3. USRI exposes the new UAC sports symbols at the sports-reference\
  \ boundary (convenience imports). UCI does not own\n   or re-export UAC domain enums (uci-no-domain-schemas).\n4. GCS\
  \ migration script handles existing data path alignment.\n\n## Scope: 4 repos touched\n- unified-api-contracts (UAC) \
  \  — primary target\n- instruments-service           — delete local, import UAC\n- unified-sports-reference-interface\
  \ (USRI) — sports-facing exports from UAC\n- unified-trading-pm            — GCS migration script"
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-21'
locked_by: live-defi-rollout
locked_since: 2026-03-18
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-api-contracts, code: C3, deployment: none, business: none}
- {repo: instruments-service, code: C3, deployment: none, business: none}
- {repo: unified-sports-reference-interface, code: C3, deployment: none, business: none}
- {repo: unified-trading-pm, code: none, deployment: none, business: none, readiness_note: GCS migration script / PM configs.}
isProject: false
todos:
- {id: p1a-uac-league-registry-types, content: "- [x] [AGENT] P1. Add LeagueDefinition dataclass + LeagueClassification types to UAC.\n  Create unified_api_contracts/canonical/domain/sports/league_registry.py with:\n  - LeagueDefinition frozen dataclass (league_id, display_name, sport, country,\n    season_months, has_playoffs, data_sources, api_football_id, tier, classification)\n  - LeagueClassificationType enum (Prediction, Features, Reference, Other)\n  - LeagueClassification Pydantic model (api_football_id, type, tier, odds_api_key)\n  - Helper constants: PRED_FULL, PRED_NO_UNDERSTAT, PRED_NO_FOOTYSTATS, FEAT_STANDARD,\n    FEAT_NO_FOOTYSTATS, REF_API_ONLY, COUNTRY_MAP, SEASON_BY_COUNTRY frozensets\n  Export from unified_api_contracts/canonical/domain/sports/__init__.py\n  and from unified_api_contracts/sports.py facade.\n  Source: instruments-service/instruments_service/sports/league_definition.py\n          instruments-service/instruments_service/sports/league_classification.py\n",
  status: done}
- {id: p1b-uac-league-data, content: "- [x] [AGENT] P1. Add league data to UAC external/api_football/league_data.py.\n  Create LEAGUE_REGISTRY dict[str, LeagueDefinition] with all ~94 leagues.\n  Split across prediction + other sub-modules mirroring instruments-service pattern.\n  Include get_league(), get_league_by_api_football_id(), get_prediction_leagues(),\n  get_leagues_by_classification(), get_leagues_by_country() query functions.\n  Source: instruments-service/instruments_service/sports/league_data_prediction.py\n          instruments-service/instruments_service/sports/league_data_other.py\n          instruments-service/instruments_service/sports/league_lookup.py\n  Add to external/api_football/__init__.py exports.\n", status: done}
- {id: p1c-uac-team-mappings, content: "- [x] [AGENT] P1. Add team mapping data to UAC external/api_football/team_mappings.py.\n  Contents:\n  - EPL_TEAM_MAPPINGS: list[dict] — 40+ EPL teams with canonical_team_id,\n    display_name, api_football_id, aliases list (Betfair/display variants)\n  - BUNDESLIGA_TEAM_MAPPINGS: list[dict] — 30+ Bundesliga teams\n  - API_FOOTBALL_TO_CANONICAL: dict[str, str] — API Football display name → canonical\n  - BETFAIR_TO_CANONICAL: dict[str, str] — Betfair variations → canonical (upper)\n  - get_canonical_team_name_from_api_football(name: str) -> str\n  - get_canonical_team_name_from_betfair(name: str) -> str\n  Source: instruments-service/instruments_service/sports/team_mapping_data.py\n          instruments-service/instruments_service/sports/team_mapping_data_bundesliga.py\n          /tmp/footballbets/footballbets/utils/mapping.py (EPL/BL mappings)\n  Add to external/api_football/__init__.py exports.\n", status: done}
- {id: p1d-uac-stadium-mappings, content: "- [x] [AGENT] P1. Add stadium/venue canonical name mappings to UAC.\n  Create external/api_football/stadium_mappings.py with:\n  - API_FOOTBALL_TO_CANONICAL_STADIUMS: dict[str, str] (~80 stadiums EPL + Bundesliga)\n  - get_canonical_stadium_name_from_api_football(name: str) -> str\n  Source: /tmp/footballbets/footballbets/utils/mapping.py lines 226–303\n  Add to external/api_football/__init__.py exports.\n", status: done}
- {id: p1e-uac-player-name, content: "- [x] [AGENT] P1. Add player name normalization to UAC external/api_football/player_name.py.\n  Contents:\n  - get_canonical_player_name_from_api_football(player_name: str, player_id: int) -> str\n    Format: LASTNAME_INITIAL (e.g. PICKFORD_J) or LASTNAME_FIRSTNAME for full names\n    Handles: diacritics (unicodedata.normalize NFKD), initials, compound names\n  Source: /tmp/footballbets/footballbets/utils/mapping.py lines 715–782\n  Add to external/api_football/__init__.py exports.\n", status: pending}
- {id: p1f-uac-odds-api-team-names, content: "- [x] [AGENT] P1. Add OddsAPI team name mappings to UAC external/odds_api/team_names.py.\n  Contents:\n  - CANONICAL_TO_ODDS_API_EPL: dict[str, str] — canonical → OddsAPI display (EPL)\n  - CANONICAL_TO_ODDS_API_BUNDESLIGA: dict[str, str] — canonical → OddsAPI display\n  - get_odds_api_team_name(canonical_name: str, api_football_league_id: int) -> str\n  - CANONICAL_TO_UNDERSTAT_EPL: dict[str, str] — canonical → Understat name\n  - CANONICAL_TO_UNDERSTAT_BUNDESLIGA: dict[str, str]\n  - get_understat_team_name(canonical_name: str, league_id: str) -> str\n  Source: /tmp/footballbets/footballbets/utils/mapping.py lines 513–695\n  Add to external/odds_api/__init__.py exports.\n", status: done}
- {id: p2a-instruments-delete-local, content: "- [x] [AGENT] P2. Delete instruments-service local sports implementations.\n  Delete (all in instruments_service/sports/):\n  - league_definition.py\n  - league_classification.py\n  - league_data_classification.py\n  - league_data_classification_a.py\n  - league_data_classification_b.py\n  - league_data_prediction.py\n  - league_data_other.py\n  - league_lookup.py\n  - team_mapping_data.py\n  - team_mapping_data_bundesliga.py\n  Note: Keep fixture_parser.py, team_aliases.py, team_normalizer.py, round_names.py\n        as they are instruments-service-specific logic (not raw data).\n        Update them to import data from UAC instead.\n", status: done}
- {id: p2b-instruments-update-imports, content: "- [x] [AGENT] P2. Update instruments-service to import from UAC.\n  Files to update (imports → from unified_api_contracts.sports import ...):\n  - instruments_service/sports/__init__.py\n  - instruments_service/sports/league_registry.py\n  - instruments_service/sports/fixture_parser.py\n  - instruments_service/sports/team_aliases.py\n  - instruments_service/sports/team_normalizer.py\n  - instruments_service/engine/.../sports_orchestration.py\n  - instruments_service/app/core/selective_validation.py\n  Also update all test files to import from UAC:\n  - tests/unit/test_sports_league_registry.py\n  - tests/unit/test_league_registry.py\n  - tests/unit/test_sports_service.py\n  - tests/unit/test_fixture_parser.py\n  - tests/unit/test_round_names.py\n  - tests/unit/test_team_aliases.py\n  - tests/unit/test_team_normalizer.py\n  - tests/unit/test_team_mapping_data.py\n", status: done}
- {id: p3a-usri-reexports, content: "- [x] [AGENT] P3. Update USRI to re-export new UAC sports symbols.\n  Add to unified_sports_reference_interface/__init__.py:\n  - LeagueDefinition\n  - LeagueClassificationType\n  - LeagueClassification\n  - LEAGUE_REGISTRY\n  - get_league, get_league_by_api_football_id, get_prediction_leagues\n  - get_canonical_team_name_from_api_football\n  - get_canonical_stadium_name_from_api_football\n  - get_canonical_player_name_from_api_football\n  - get_odds_api_team_name\n", status: done}
- {id: p3b-deployment-cleanup, content: "- [x] [AGENT] P3. Update deployment-service sports scripts to import from UAC.\n  Files: deployment-service/scripts/sports/league_config.py\n         deployment-service/scripts/sports/verify_league_config.py\n         deployment-service/scripts/sports/update_league_config.py\n  These reference LEAGUE_CLASSIFICATION from a local copy. Update to import\n  LEAGUE_REGISTRY from unified_api_contracts.sports.\n", status: done}
- {id: p3c-gcs-migration-script, content: "- [x] [AGENT] P3. Audit GCS sports data paths and write migration script.\n  Check features-sports-service for bucket names and path conventions.\n  Write unified-trading-pm/scripts/sports/migrate_sports_gcs_paths.sh that:\n  1. Lists current objects in the sports data bucket\n  2. Maps old path conventions to new canonical paths\n  3. Uses gsutil -m cp to migrate (preserving old paths until verified)\n  Note: /tmp/footballbets/data/ was empty (no GCS data from old system).\n  If GCS bucket is empty, the script just validates the path convention.\n", status: done}
- {id: p4-qg-sweep, content: "- [x] [AGENT] P4. Run quality gates across all 3 code repos:\n  cd unified-api-contracts && bash scripts/quality-gates.sh\n  cd instruments-service && bash scripts/quality-gates.sh\n  cd unified-sports-reference-interface && bash scripts/quality-gates.sh\n  All must pass. Fix any failures before marking done.\n", status: done}
---

# Sports Canonical Mapping & GCS Migration

## Problem Statement

Sports reference mapping data (league registry, team alias tables, stadium names, player name normalisation, OddsAPI
team names) is scattered across:

- `instruments-service/instruments_service/sports/` — 17 files, built correctly but in wrong layer
- `deployment-service/scripts/sports/` — a stale copy of league config
- `/tmp/footballbets/` — original source (EPL + Bundesliga only, 2 leagues)

None of it is in UAC where external-data normalization schemas belong. This means:

1. `features-sports-service` and all future sports consumers must re-implement or go without
2. The instruments-service leaks a service-internal dependency on raw mapping tables
3. No SSOT for "what is the canonical name for X entity from source Y"

## Canonical ID Table (definitive reference)

| Entity     | Canonical ID format                                       | Example                               | Source                                               |
| ---------- | --------------------------------------------------------- | ------------------------------------- | ---------------------------------------------------- |
| League     | `{COUNTRY_CODE}_{LEAGUE_ABBR}`                            | `EPL`, `BUN`, `ENG_CHAMPIONSHIP`      | instruments-service/sports/league_data_prediction.py |
| Team       | SCREAMING_SNAKE_CASE                                      | `MAN_CITY`, `TOTTENHAM`, `DORTMUND`   | /tmp/footballbets/utils/mapping.py                   |
| Fixture    | `{api_football_fixture_id}` (int as str)                  | `"1034567"`                           | API Football                                         |
| Player     | `{LASTNAME}_{INITIAL}` or `{LASTNAME}_{FIRSTNAME}`        | `PICKFORD_J`, `FERNANDES_BRUNO`       | player_name.py normalization                         |
| Stadium    | SCREAMING_SNAKE_CASE                                      | `ANFIELD`, `ALLIANZ_ARENA`            | stadium_mappings.py                                  |
| Referee    | `{LASTNAME}_{INITIAL}`                                    | `ATKINSON_M`                          | Same pattern as player                               |
| Season     | `{YYYY}/{YY}`                                             | `2024/25`                             | String convention                                    |
| Instrument | `{fixture_id}::{market_type}::{outcome}::{bookmaker_key}` | `"1034567::h2h::home::betfair_ex_uk"` | UAC CanonicalOdds                                    |

## Architecture Decision

```
UAC external/api_football/
├── team_mappings.py          ← EPL + Bundesliga alias tables + API Football → canonical
├── stadium_mappings.py       ← API Football stadium name → canonical
├── player_name.py            ← get_canonical_player_name_from_api_football()
└── league_data.py            ← LEAGUE_REGISTRY dict + query functions

UAC external/odds_api/
└── team_names.py             ← canonical → OddsAPI/Understat display names

UAC canonical/domain/sports/
└── league_registry.py        ← LeagueDefinition dataclass, LeagueClassificationType enum

instruments-service/sports/
├── DELETED: league_definition.py, league_classification.py, league_data_*.py, league_lookup.py
├── DELETED: team_mapping_data.py, team_mapping_data_bundesliga.py
└── KEPT + UPDATED: fixture_parser.py, team_aliases.py, team_normalizer.py, round_names.py
```

## Pre-Audit Manifest

### Symbols being MOVED from instruments-service to UAC

| Symbol                               | From                                             | To                                          |
| ------------------------------------ | ------------------------------------------------ | ------------------------------------------- |
| `LeagueDefinition`                   | instruments_service.sports.league_definition     | unified_api_contracts.sports                |
| `LeagueClassificationType`           | instruments_service.sports.league_classification | unified_api_contracts.sports                |
| `LeagueClassification`               | instruments_service.sports.league_classification | unified_api_contracts.sports                |
| `LEAGUE_REGISTRY`                    | instruments_service.sports.league_lookup         | unified_api_contracts.sports                |
| `get_league()`                       | instruments_service.sports.league_lookup         | unified_api_contracts.sports                |
| `get_league_by_api_football_id()`    | instruments_service.sports.league_lookup         | unified_api_contracts.sports                |
| `get_prediction_leagues()`           | instruments_service.sports.league_lookup         | unified_api_contracts.sports                |
| `get_leagues_by_classification()`    | instruments_service.sports.league_lookup         | unified_api_contracts.sports                |
| `get_leagues_by_country()`           | instruments_service.sports.league_lookup         | unified_api_contracts.sports                |
| `EPL_TEAM_MAPPINGS`                  | instruments_service.sports.team_mapping_data     | unified_api_contracts.external.api_football |
| `BUNDESLIGA_TEAM_MAPPINGS`           | instruments_service.sports.team_mapping_data     | unified_api_contracts.external.api_football |
| `API_FOOTBALL_TO_CANONICAL`          | (new)                                            | unified_api_contracts.external.api_football |
| `BETFAIR_TO_CANONICAL`               | (new)                                            | unified_api_contracts.external.api_football |
| `API_FOOTBALL_TO_CANONICAL_STADIUMS` | (new)                                            | unified_api_contracts.external.api_football |
| `CANONICAL_TO_ODDS_API_EPL/BL`       | (new)                                            | unified_api_contracts.external.odds_api     |
| `CANONICAL_TO_UNDERSTAT_EPL/BL`      | (new)                                            | unified_api_contracts.external.odds_api     |

### Files that import from instruments_service.sports (pre-audit)

| File                                                   | Symbols used                          | Action              |
| ------------------------------------------------------ | ------------------------------------- | ------------------- |
| instruments_service/sports/**init**.py                 | all                                   | Re-export from UAC  |
| instruments_service/sports/league_registry.py          | LeagueClassification, league_lookup   | Re-export from UAC  |
| instruments_service/sports/fixture_parser.py           | LeagueDefinition                      | Update import       |
| instruments_service/sports/team_aliases.py             | EPL_TEAM_MAPPINGS, BUND_TEAM_MAPPINGS | Update import       |
| instruments_service/sports/team_normalizer.py          | team_aliases                          | Stays local (logic) |
| instruments_service/engine/.../sports_orchestration.py | league_registry, team_aliases         | Update import       |
| instruments_service/app/core/selective_validation.py   | league_classification                 | Update import       |
| deployment-service/scripts/sports/league_config.py     | LEAGUE_CLASSIFICATION                 | Update import       |
| tests (8 files)                                        | various                               | Update imports      |

## Dependency DAG

```
Phase 1 (UAC additions) ─┬─ p1a: league_registry types (canonical/)
  [PARALLEL]              ├─ p1b: league_data (external/api_football/)
                          ├─ p1c: team_mappings (external/api_football/)
                          ├─ p1d: stadium_mappings (external/api_football/)
                          ├─ p1e: player_name (external/api_football/)
                          └─ p1f: odds_api team_names (external/odds_api/)
                                       │
                               UAC QG gate
                                       │
Phase 2 (instruments-service) ─┬─ p2a: delete local files
  [SEQUENTIAL]                  └─ p2b: update imports + tests
                                       │
                           instruments-service QG gate
                                       │
Phase 3 ─────────────────┬─ p3a: USRI re-exports
  [PARALLEL]              ├─ p3b: deployment-service cleanup
                          └─ p3c: GCS migration script
                                       │
                               USRI QG gate
                                       │
Phase 4 ─────────────────── p4: Full QG sweep (UAC + instruments + USRI)
```

## Success Criteria

### Phase 1

- C4: `cd unified-api-contracts && bash scripts/quality-gates.sh` → green
- All 6 new modules pass basedpyright strict mode
- LEAGUE_REGISTRY has ≥28 Prediction leagues matching league_classification_config.py

### Phase 2

- C4: `cd instruments-service && bash scripts/quality-gates.sh` → green
- 0 references to `instruments_service.sports.league_data_*` or `team_mapping_data*` remain
- All 9 test files updated and passing

### Phase 3

- USRI exports ≥10 new symbols via `from unified_api_contracts.sports import`
- GCS migration script either runs successfully or documents empty-bucket state

### Phase 4

- All 3 repos pass quality gates simultaneously
- B1: Canonical ID table in plan is accurate and serves as reference for all future development
