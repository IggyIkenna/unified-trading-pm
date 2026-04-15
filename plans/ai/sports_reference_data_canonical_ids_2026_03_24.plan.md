# AI-GENERATED — awaiting user review and promotion

---

type: code epic: epic-code-completion completion_gates: code: C5 deployment: D1 business: B1

repo_gates:

- repo: unified-api-contracts code: C0 notes: "Schema additions and ID format standardisation"
- repo: instruments-service (reference_data/ sub-package) code: C0 notes: "Canonical ID mapping across adapters"
- repo: instruments-service (reference_data/ sub-package) code: C0 notes: "Sports adapters must use canonical IDs from
  UAC"
- repo: instruments-service code: C0 notes: "Sports instruments use canonical fixture/team IDs"

---

## Context

**Instruments-service SPORTS category** fetches reference data — team names, player names, referees, stadiums, fixtures,
seasons, country codes — not derived data. When running `--category SPORTS --date 2026-03-22`, the orchestrator asks
instruments-service reference_data for instruments. It calls `api_football` and `betfair` adapters. The output should be
`InstrumentRecord[]` where each record represents a betting market / fixture available to trade.

**What already exists (do not recreate):**

| What                                                                                                            | Where                                                                               |
| --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `CanonicalTeam`, `CanonicalFixture`, `CanonicalVenue`, `CanonicalReferee`, `CanonicalPlayer`, `CanonicalLeague` | `unified_api_contracts.canonical.domain.sports.__init__`                            |
| Team name → canonical mapping (EPL, Bundesliga)                                                                 | `unified_api_contracts.canonical.domain.sports.team_mapping_data_epl/bundesliga.py` |
| `LEAGUE_REGISTRY` (all leagues by canonical `league_id`)                                                        | `unified_api_contracts.canonical.domain.sports.league_data`                         |
| Sports data adapters (api_football, odds_api, footystats, transfermarkt, understat)                             | `instruments_service.reference_data.adapters.*`                                     |
| `TeamNormalizer` (raw name → canonical)                                                                         | `instruments_service.reference_data.adapters._sports_normalizer`                    |

## Problems to Solve

### 1. Canonical ID Format is Undefined

The `CanonicalTeam.team_id`, `CanonicalFixture.fixture_id`, `CanonicalVenue.venue_id`, `CanonicalReferee.referee_id`,
`CanonicalPlayer.player_id` fields exist but have **no documented format**. Different adapters likely produce different
ID formats:

- api_football: numeric IDs (`42` for Arsenal)
- odds_api: string names (`"Arsenal"`)
- footystats: own numeric IDs
- betfair: own numeric market IDs

**Without a canonical ID format, the same team/fixture has different IDs in different data sources.** Features/ML can't
join across sources.

**Proposed canonical ID format:**

```
team:    {sport}:{competition}:{normalised_name}  e.g. football:EPL:arsenal
fixture: {sport}:{competition}:{home_slug}+{away_slug}@{date}  e.g. football:EPL:arsenal+chelsea@20260315
player:  {sport}:{nationality}:{normalised_name}  e.g. football:ENG:bukayo-saka
venue:   {sport}:{country}:{normalised_name}  e.g. football:ENG:emirates-stadium
referee: {sport}:{nationality}:{normalised_name}  e.g. football:ENG:michael-oliver
season:  {sport}:{competition}:{year_start}/{year_end}  e.g. football:EPL:2025/2026
```

**Where this goes:** The format definition belongs in the docstring/comment of each `Canonical*` class in
`unified_api_contracts.canonical.domain.sports.__init__`. Each adapter must produce IDs in this format.

### 2. Historical Odds Data Source for SPORTS

User clarified: historical odds come from **Odds API** (`odds-api-key` in Secret Manager). instruments-service
reference_data already has `instruments_service.reference_data.adapters.odds_api`. The question is: **which data source
does instruments-service use for SPORTS historical reference data?**

For **instruments-service SPORTS**, reference data is:

- Fixtures (upcoming + historical for the date) from api_football
- Historical odds availability indicators from Odds API

This is NOT derived data. The odds values themselves are tick data (market-tick-data-service). The instruments are the
markets/fixtures that exist.

**Action needed:**

- instruments-service reference_data `CANONICAL_VENUE_TO_ADAPTER` currently maps `BETFAIR` → `betfair` and
  `API_FOOTBALL` → `api_football`
- `betfair` adapter needs the `betfair-session-token` and `betfair-app-key` secrets
- `api_football` adapter needs `api-football-api-key`
- For historical data: check if Odds API key (`odds-api-key`) should be added as a third SPORTS data source

### 3. Missing `SeasonDefinition` Type

There is no `SeasonDefinition` canonical type in UAC for representing a sports season (start date, end date,
competition, rounds). This is needed for:

- Data availability checks: "was 2026-03-22 in the EPL 2025/2026 season?"
- Partitioning: instruments are season-scoped, not just date-scoped

**Where it goes:** `unified_api_contracts.canonical.domain.sports.__init__` alongside the existing canonical types.

### 4. instruments-service reference_data Capability Registry Not Updated for Sports

The `refdata_preflight_skip` warning fires for all sports venues: `"venue=api_football not in capability registry"`.
instruments-service reference_data's preflight check has a capability registry that needs to include sports adapters.

**Where:** `instruments_service/reference_data/` capability registry (whichever file controls which adapters are
"live").

### 5. Country Codes

The `CanonicalTeam.country` and `CanonicalLeague.country` fields are freeform strings. There is no canonical country
code type. **This is acceptable short-term** since UAC has `LEAGUE_REGISTRY` which uses ISO country codes consistently.
Document this in the schema docstring.

## What Does NOT Need to Change

- The canonical schema structure in UAC — the Pydantic models are already correct
- The LEAGUE_REGISTRY — it's already comprehensive and uses canonical `league_id`
- The `TeamNormalizer` in instruments-service reference_data — it works and maps to canonical names
- The api_football adapter in instruments-service reference_data — it already produces canonical fixture keys

## Recommended Action Order

1. **Define canonical ID format** in UAC docstrings (no code changes — documentation only)
2. **Audit adapters** in instruments-service reference_data to verify they produce IDs in that format
3. **Add `SeasonDefinition`** to UAC
4. **Fix instruments-service reference_data capability registry** to include sports adapters
5. **Add Odds API** as a secondary SPORTS data source to `ADAPTER_DATA_SOURCES` if needed
6. **Provision secrets**: `betfair-session-token`, `betfair-app-key`, `api-football-api-key` in Secret Manager (betfair
   secrets already exist as `BETFAIR_APP_KEY`, `betfair-api-key`, `betfair-app-key` — names need alignment)

## API Key / Data Source Registry

For SPORTS, the data source → Secret Manager mapping in UAC `DATA_SOURCE_TO_SECRET`:

```python
'betfair': 'betfair-api-key',       # already defined
'api_football': 'api-football-api-key',  # already defined
'odds_api': 'odds-api-key',         # NOT YET defined in DATA_SOURCE_TO_SECRET
```

`odds-api-key` exists in Secret Manager but is not in `DATA_SOURCE_TO_SECRET`. Add it.
