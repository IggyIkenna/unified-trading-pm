---
name: sports-batch-pipeline-end-to-end
locked_by: live-defi-rollout
locked_since: 2026-03-25
overview: |
  Wire the full sports batch pipeline end-to-end: instruments-service (API-Football reference data),
  market-tick-data-service (Odds API tick data with canonical instrument IDs), and features-sports-service
  (derived features from footystats, understat, etc.). Register all sports API keys in Secret Manager
  registry. Migrate existing GCS data from old bucket format to hive-partitioned format. Validate with
  1-day then 1-week runs across 20+ prediction leagues and all bookmakers Odds API covers.

  ## Problem
  Extensive sports schema infrastructure exists (UAC canonical types, USRI 8 adapters, league registry
  with 94 leagues, bookmaker registry with 22+ entries, 998 features in FSS) but the end-to-end batch
  pipeline has never been run. Key gaps:
  1. `odds_api` missing from UAC `DATA_SOURCE_TO_SECRET`
  2. MTDS SPORTS venue routing points to BETFAIR/API_FOOTBALL instead of ODDS_API
  3. 50GB+ GCS data in old bucket format (no hive partitioning)
  4. features-sports-service not tested against real providers

  ## Solution
  Phase 1: Register all sports API keys in UAC, fix venue routing
  Phase 2: Verify instruments-service SPORTS hook works (existing code, minimal changes)
  Phase 3: Wire MTDS to use ODDS_API venue for sports tick data
  Phase 4: Migrate GCS buckets to hive format
  Phase 5: Run features-sports-service batch against real providers
  Phase 6: Validate 1-day then 1-week across all prediction leagues

  ## Scope: 9 repos touched
  - unified-api-contracts (UAC) — DATA_SOURCE_TO_SECRET + canonical ID docstrings
  - instruments-service (URDI sports/ sub-package) (USRI) — quota tracking on OddsApi adapter
  - unified-reference-data-interface (URDI) — verify sports adapter routing
  - instruments-service — verify SPORTS hook (likely no code changes)
  - market-tick-data-service — wire ODDS_API venue
  - unified-market-interface (UMI) — verify OddsApiAdapter returns canonical IDs
  - features-sports-service — verify batch end-to-end
  - unified-trading-pm — plan + GCS migration script
  - unified-trading-pm/codex — update sports-schema-paths.md

  ## Archived repo reference (patterns only, no code copy)
  `archive/new-sports-batting-services` (branch: `week1-implementation`, 41 commits ahead of main)
  - Query cost tracking: `x-requests-remaining` header, `OUT_OF_USAGE_CREDITS` handling
  - League-based query grouping with ThreadPoolExecutor(50)
  - Connection pooling via HTTPAdapter(pool_connections=50)
  - Master mapping rules: `footballbets/utils/mapping.py` (807L)

type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: D1
  business: B4

repo_gates:
  - repo: unified-api-contracts
    code: C0
    notes: "DATA_SOURCE_TO_SECRET + canonical ID format docstrings"
  - repo: instruments-service (URDI sports/ sub-package)
    code: C0
    notes: "Quota tracking on OddsApi adapter"
  - repo: unified-reference-data-interface
    code: C0
    notes: "Verify sports adapter routing"
  - repo: instruments-service
    code: C0
    notes: "Verify SPORTS hook works (may need no changes)"
  - repo: market-tick-data-service
    code: C0
    notes: "Wire ODDS_API venue for sports tick data"
  - repo: unified-market-interface
    code: C0
    notes: "Verify OddsApiAdapter canonical IDs"
  - repo: features-sports-service
    code: C0
    notes: "Verify batch end-to-end with real providers"
  - repo: unified-trading-pm
    code: C0
    notes: "Plan + GCS migration script"
  - repo: unified-trading-pm/codex
    code: C0
    notes: "Update sports-schema-paths.md"

isProject: false

todos:
  # ============================================================================
  # PHASE 1 — UAC: Secret Manager Registry + Venue Routing  [PARALLEL]
  # ============================================================================
  - id: p1a-sm-keys-audit
    content: |
      - [ ] [AGENT] P0. Audit Secret Manager for sports API keys.
        Run: gcloud secrets list --filter="name:sports OR name:odds OR name:football OR name:betfair OR name:footy OR name:understat OR name:soccer"
        Document which keys exist and their exact names.
        Cross-reference with UAC DATA_SOURCE_TO_SECRET in canonical_mappings.py:454.
    status: pending

  - id: p1b-uac-data-source-to-secret
    content: |
      - [ ] [AGENT] P0. Add missing sports sources to UAC DATA_SOURCE_TO_SECRET.
        File: unified_api_contracts/canonical/canonical_mappings.py
        Add entries (verify key names from p1a):
          "odds_api": "odds-api-key",
          "footystats": "footystats-api-key" or None,
          "understat": None,
          "soccer_football_info": None,
          "open_meteo": None,
          "transfermarkt": None,
        QG: cd unified-api-contracts && bash scripts/quality-gates.sh
    status: pending
    blocked_by: p1a-sm-keys-audit

  - id: p1c-canonical-id-docstrings
    content: |
      - [ ] [AGENT] P1. Codify canonical ID format in UAC docstrings.
        File: unified_api_contracts/canonical/domain/sports/__init__.py
        Add format spec to each Canonical* class docstring:
        - CanonicalLeague: league_id = "{COUNTRY_CODE}_{LEAGUE_ABBR}" (e.g. EPL, BUN)
        - CanonicalTeam: team_id = SCREAMING_SNAKE_CASE (e.g. MAN_CITY)
        - CanonicalFixture: fixture_id = "{api_football_fixture_id}" (e.g. "1034567")
        - CanonicalPlayer: player_id = "{LASTNAME}_{INITIAL}" (e.g. PICKFORD_J)
        - CanonicalVenue: venue_id = SCREAMING_SNAKE_CASE (e.g. ANFIELD)
        - CanonicalReferee: referee_id = "{LASTNAME}_{INITIAL}" (e.g. ATKINSON_M)
        - CanonicalOdds: instrument_id = "{fixture_id}::{market_type}::{outcome}::{bookmaker_key}"
        Source: sports_canonical_mapping_and_gcs_migration_2026_03_18.plan.md § Canonical ID Table
    status: pending

  - id: p1d-mtds-sports-venue-routing
    content: |
      - [ ] [AGENT] P0. Fix MTDS SPORTS venue routing.
        File: market_tick_data_service/engine/orchestrator.py:59-62
        Current: SPORTS -> ["BETFAIR", "API_FOOTBALL"]
        Change to: SPORTS -> ["ODDS_API"]
        Rationale: API_FOOTBALL is reference data (instruments-service). BETFAIR is one bookmaker
        among 250+. ODDS_API is the aggregator that provides odds for all bookmakers.
        Also update VenueMapping in UAC if ODDS_API is not in venue lists.
    status: pending

  # ============================================================================
  # PHASE 1 gate: cd unified-api-contracts && bash scripts/quality-gates.sh
  # ============================================================================

  # ============================================================================
  # PHASE 2 — instruments-service: Verify SPORTS Reference Data  [SEQUENTIAL]
  # ============================================================================
  - id: p2a-verify-instruments-sports
    content: |
      - [ ] [AGENT] P1. Verify instruments-service SPORTS hook works end-to-end.
        File: instruments_service/engine/orchestrator.py:188-191
        Current code: get_venues_for_categories("SPORTS") -> ["API_FOOTBALL"]
        This calls URDI -> USRI api_football adapter -> InstrumentRecord[]
        Test: cd instruments-service && python -m instruments_service.service \
          --operation fetch --category SPORTS --date 2026-03-22
        Verify: InstrumentRecord[] written to GCS in hive format.
        If no code changes needed, just verify and mark done.
    status: pending
    blocked_by: p1b-uac-data-source-to-secret

  - id: p2b-urdi-capability-registry
    content: |
      - [ ] [AGENT] P1. Fix URDI capability registry for sports.
        AI plan noted: "venue=api_football not in capability registry" warning.
        Check unified_reference_data_interface/ for preflight capability checks.
        Add api_football + odds_api if missing.
    status: pending

  - id: p2c-season-definition-type
    content: |
      - [ ] [AGENT] P2. Add SeasonDefinition type to UAC if missing.
        Check unified_api_contracts/canonical/domain/sports/ for SeasonDefinition.
        If absent, add: frozen dataclass with sport, competition, year_start, year_end,
        start_date, end_date, has_playoffs.
        Needed for: season-scoped partitioning, data availability checks.
    status: pending

  # ============================================================================
  # PHASE 2 gate: cd instruments-service && bash scripts/quality-gates.sh
  # ============================================================================

  # ============================================================================
  # PHASE 3 — MTDS + UMI: Odds Tick Data Pipeline  [PARALLEL with Phase 2]
  # ============================================================================
  - id: p3a-umi-odds-adapter-verify
    content: |
      - [ ] [AGENT] P1. Verify UMI OddsApiAdapter for batch historical odds.
        File: unified-market-interface SPORTS_REGISTRY
        Check: Does OddsApiAdapter implement download_batch(date, data_types)?
        Check: Does it return DataFrame with canonical instrument IDs?
        Format: {fixture_id}::{market_type}::{outcome}::{bookmaker_key}
        If not, implement the batch download method using Odds API v4 historical endpoint:
          https://api.the-odds-api.com/v4/historical/sports/{sport}/odds
    status: pending
    blocked_by: p1d-mtds-sports-venue-routing

  - id: p3b-usri-quota-tracking
    content: |
      - [ ] [AGENT] P1. Add quota tracking to USRI OddsApi adapter.
        File: unified_sports_reference_interface/adapters/odds_api.py
        Pattern from archive: Track x-requests-remaining header on each response.
        Log remaining credits. Emit ADAPTER_QUOTA_WARNING event at <10% remaining.
        Raise on OUT_OF_USAGE_CREDITS instead of retrying.
        Group queries by league (from LEAGUE_REGISTRY prediction leagues) to minimize API calls.
        Do NOT copy archived code — implement using existing _get_with_retry() base pattern.
    status: pending

  - id: p3c-mtds-sports-integration-test
    content: |
      - [ ] [AGENT] P1. Test MTDS SPORTS pipeline end-to-end.
        Test: cd market-tick-data-service && python -m market_tick_data_service.service \
          --operation download --category SPORTS --date 2026-03-22
        Verify: Odds parquet written to:
          gs://market-data-tick-sports-{project}/raw_tick_data/by_date/day=2026-03-22/
            data_type=odds/venue=ODDS_API/odds.parquet
        Check: Data includes multiple leagues, multiple bookmakers per fixture.
    status: pending
    blocked_by: p3a-umi-odds-adapter-verify

  # ============================================================================
  # PHASE 3 gate: cd market-tick-data-service && bash scripts/quality-gates.sh
  # ============================================================================

  # ============================================================================
  # PHASE 4 — GCS Migration  [CAN START IMMEDIATELY, PARALLEL]
  # ============================================================================
  - id: p4a-gcs-bucket-audit
    content: |
      - [ ] [HUMAN] P1. Audit existing GCS sports data buckets.
        Run: gsutil ls -p {project_id} | grep -i "football\|sports\|odds\|betting"
        Document: bucket name, size (gsutil du -s), file count, path format.
        Known buckets from sports-data-migration.md:
          football-raw-data-all-sources-*
          market-data-tick-sports-*-v3
          football-mapped-consolidated-*
          football-ml-features-*
          football-ml-models-and-predictions-*
          football-backtest-results-*
    status: pending

  - id: p4b-migration-script
    content: |
      - [ ] [AGENT] P1. Write GCS migration script.
        File: unified-trading-pm/scripts/sports/migrate_sports_gcs_to_hive.sh
        Pattern: market-tick-data-service/scripts/migrate_gcs_path_to_hive.py
        Features: dry-run mode, server-side copy, date range filtering,
          day-YYYY-MM-DD -> day=YYYY-MM-DD, source category filtering.
        Target paths from codex sports-schema-paths.md:
          sports_features/by_date/day={date}/feature_group={group}/
          sports_odds/by_date/day={date}/venue={venue}/
    status: pending
    blocked_by: p4a-gcs-bucket-audit

  - id: p4c-execute-migration
    content: |
      - [ ] [HUMAN] P2. Execute GCS migration.
        1. Run dry-run: bash scripts/sports/migrate_sports_gcs_to_hive.sh --dry-run
        2. Review output, fix any path mapping issues
        3. Execute: bash scripts/sports/migrate_sports_gcs_to_hive.sh --execute
        4. Validate: compare file counts source vs target
        5. Keep old buckets for 30 days before archiving
    status: pending
    blocked_by: p4b-migration-script

  # ============================================================================
  # PHASE 5 — features-sports-service: Batch End-to-End  [AFTER P2 + P3]
  # ============================================================================
  - id: p5a-fss-batch-test
    content: |
      - [ ] [AGENT] P1. Test features-sports-service batch end-to-end.
        Test: cd features-sports-service && python -m features_sports_service.service \
          --mode batch --date 2026-03-22 --providers api_football,footystats,understat,odds_api
        Verify: Feature parquet files written to:
          gs://features-sports-{project}/by_date/day=2026-03-22/feature_group={group}/
        Check: All 4 providers fetched, features computed, no errors.
        Reference E2E plan: plans/active/end-to-end-testing/011_features_sports_service.md
    status: pending
    blocked_by: p2a-verify-instruments-sports, p3c-mtds-sports-integration-test

  - id: p5b-fss-hive-path-verification
    content: |
      - [ ] [AGENT] P2. Verify FSS output uses hive-partitioned paths.
        Check features_sports_service/data/ and engine/ for GCS write paths.
        Must use key=value format: by_date/day={date}/feature_group={group}/
        If using old format (day-YYYY-MM-DD), fix to hive format.
    status: pending

  # ============================================================================
  # PHASE 5 gate: cd features-sports-service && bash scripts/quality-gates.sh
  # ============================================================================

  # ============================================================================
  # PHASE 6 — Validation: 1-Day Then 1-Week  [SEQUENTIAL]
  # ============================================================================
  - id: p6a-one-day-validation
    content: |
      - [ ] [HUMAN+AGENT] P0. Run full 1-day pipeline validation.
        Date: 2026-03-22 (Saturday, full fixture slate)
        Steps:
          1. instruments-service --category SPORTS --date 2026-03-22
          2. market-tick-data-service --category SPORTS --date 2026-03-22
          3. features-sports-service --mode batch --date 2026-03-22
        Validate:
          - Fixtures for 20+ leagues in instruments output
          - Odds from all available bookmakers in MTDS output
          - Features computed for all fixtures with data
          - All GCS paths hive-partitioned
          - Canonical IDs consistent across all 3 services
    status: pending
    blocked_by: p5a-fss-batch-test

  - id: p6b-one-week-validation
    content: |
      - [ ] [HUMAN+AGENT] P1. Run 1-week pipeline validation.
        Date range: 2026-03-16 to 2026-03-22
        Run all 3 services for each date. Validate:
          - Data completeness >= 95% per provider per date
          - No duplicate fixtures across dates
          - Feature counts consistent day-over-day
          - Total data size reasonable (reference: 50-100MB/day for odds)
    status: pending
    blocked_by: p6a-one-day-validation

  # ============================================================================
  # PHASE 7 — QG Sweep + Codex Update  [PARALLEL]
  # ============================================================================
  - id: p7a-qg-sweep
    content: |
      - [ ] [AGENT] P0. Run quality gates across all touched repos.
        cd unified-api-contracts && bash scripts/quality-gates.sh
        cd instruments-service && bash scripts/quality-gates.sh  # includes URDI sports/ sub-package
        cd unified-reference-data-interface && bash scripts/quality-gates.sh
        cd instruments-service && bash scripts/quality-gates.sh
        cd market-tick-data-service && bash scripts/quality-gates.sh
        cd unified-market-interface && bash scripts/quality-gates.sh
        cd features-sports-service && bash scripts/quality-gates.sh
        All must pass.
    status: pending
    blocked_by: p6a-one-day-validation

  - id: p7b-codex-update
    content: |
      - [ ] [AGENT] P2. Update codex sports-schema-paths.md.
        Add: canonical ID format table, instrument ID format for odds markets,
        updated service path templates for SPORTS category.
    status: pending
---

# Sports Batch Pipeline End-to-End

## Problem Statement

The sports domain has extensive schema infrastructure but the batch pipeline has never been run end-to-end. Three
services need to work in sequence: instruments-service (fixtures from API-Football), market-tick-data-service (odds from
Odds API), and features-sports-service (derived features from multiple providers).

## Canonical ID Table (SSOT)

| Entity     | Format                                                    | Example                               | Source                  |
| ---------- | --------------------------------------------------------- | ------------------------------------- | ----------------------- |
| League     | `{COUNTRY_CODE}_{LEAGUE_ABBR}`                            | `EPL`, `BUN`                          | UAC league_data.py      |
| Team       | `SCREAMING_SNAKE_CASE`                                    | `MAN_CITY`, `TOTTENHAM`               | UAC team_mappings.py    |
| Fixture    | `{api_football_fixture_id}`                               | `"1034567"`                           | API Football            |
| Player     | `{LASTNAME}_{INITIAL}`                                    | `PICKFORD_J`                          | UAC player_name.py      |
| Stadium    | `SCREAMING_SNAKE_CASE`                                    | `ANFIELD`                             | UAC stadium_mappings.py |
| Referee    | `{LASTNAME}_{INITIAL}`                                    | `ATKINSON_M`                          | Same pattern as player  |
| Season     | `{YYYY}/{YY}`                                             | `2024/25`                             | String convention       |
| Instrument | `{fixture_id}::{market_type}::{outcome}::{bookmaker_key}` | `"1034567::h2h::home::betfair_ex_uk"` | UAC CanonicalOdds       |

## Architecture Decision

```
instruments-service (SPORTS category)
  └─ URDI → USRI api_football adapter → InstrumentRecord[] (fixtures/teams/leagues)
       └─ Writes to: instruments-store-sports-{project}/by_date/day={date}/

market-tick-data-service (SPORTS category)
  └─ UMI → OddsApiAdapter → DataFrame (historical odds per fixture per bookmaker)
       └─ Writes to: market-data-tick-sports-{project}/raw_tick_data/by_date/day={date}/

features-sports-service (batch mode)
  └─ Reads instruments + odds from GCS
  └─ Calls USRI adapters directly for: footystats, understat, soccer_football_info
  └─ Computes 998+ features per fixture
       └─ Writes to: features-sports-{project}/by_date/day={date}/feature_group={group}/
```

## Key Pattern: Borrowing from Archived Repo

The `archive/new-sports-batting-services` (branch `week1-implementation`) has patterns to borrow:

1. **Query cost tracking**: `x-requests-remaining` header → log + emit event on depletion
2. **League grouping**: Process fixtures by league to minimize API calls
3. **Connection pooling**: `HTTPAdapter(pool_connections=50)` for efficient batch fetching
4. **Graceful credit exhaustion**: Stop fetching when `OUT_OF_USAGE_CREDITS`, don't retry

These patterns go into USRI adapters (interface layer), NOT into services.

## Pre-Audit Manifest

### Symbols being ADDED

| Symbol                       | Where                                   | Consumers            |
| ---------------------------- | --------------------------------------- | -------------------- |
| `"odds_api": "odds-api-key"` | UAC canonical_mappings.py               | MTDS, USRI           |
| Canonical ID docstrings      | UAC canonical/domain/sports/**init**.py | All sports consumers |
| ODDS_API venue routing       | MTDS orchestrator.py                    | MTDS                 |
| Quota tracking               | USRI odds_api.py                        | FSS, MTDS            |

### Files that need changes

| File                                                              | Change                                | Action                  |
| ----------------------------------------------------------------- | ------------------------------------- | ----------------------- |
| `unified_api_contracts/canonical/canonical_mappings.py`           | Add odds_api to DATA_SOURCE_TO_SECRET | Add entry               |
| `unified_api_contracts/canonical/domain/sports/__init__.py`       | Add ID format docstrings              | Edit docstrings         |
| `market_tick_data_service/engine/orchestrator.py`                 | Change SPORTS venues to ["ODDS_API"]  | Edit list               |
| `unified_sports_reference_interface/adapters/odds_api.py`         | Add quota tracking                    | Extend \_get_with_retry |
| `unified-trading-pm/scripts/sports/migrate_sports_gcs_to_hive.sh` | New migration script                  | Create                  |
| `unified-trading-pm/codex/02-data/sports-schema-paths.md`         | Add canonical ID format table         | Edit                    |

## Dependency DAG

```
P1 (UAC + SM keys) ──┬── P1a: SM audit
  [PARALLEL]          ├── P1b: DATA_SOURCE_TO_SECRET
                      ├── P1c: Canonical ID docstrings
                      └── P1d: MTDS venue routing
                                │
                       UAC QG gate
                                │
P2 (instruments) ────── P2a: Verify SPORTS hook ──── instruments QG gate
  [SEQUENTIAL]          P2b: URDI capability            │
                        P2c: SeasonDefinition           │
                                                        │
P3 (MTDS + UMI) ─────── P3a: UMI adapter ──── MTDS QG gate
  [PARALLEL w/ P2]       P3b: Quota tracking         │
                         P3c: Integration test       │
                                                     │
P4 (GCS migration) ──── P4a: Audit buckets    (PARALLEL - can start immediately)
                         P4b: Migration script
                         P4c: Execute migration
                                                     │
P5 (features) ──────── P5a: Batch test ──── FSS QG gate
  [AFTER P2+P3]         P5b: Hive path verify        │
                                                     │
P6 (validation) ─────── P6a: 1-day
  [SEQUENTIAL]           P6b: 1-week
                                                     │
P7 (cleanup) ──────── P7a: QG sweep all repos
                       P7b: Codex update
```

## Success Criteria

### Phase 1

- C4: `cd unified-api-contracts && bash scripts/quality-gates.sh` green
- All sports data sources registered in DATA_SOURCE_TO_SECRET

### Phase 2

- instruments-service --category SPORTS produces InstrumentRecord[] for 20+ leagues
- Canonical fixture IDs match API Football format

### Phase 3

- MTDS --category SPORTS writes odds parquet with canonical instrument IDs
- Quota tracking logs x-requests-remaining on each Odds API call

### Phase 4

- Migration script passes dry-run
- Old data accessible via new hive paths

### Phase 5

- FSS batch mode computes features from all 4 providers
- Output in hive-partitioned GCS paths

### Phase 6

- B4: 1-day pipeline end-to-end with zero errors
- Data completeness >= 95% per provider
- 1-week run covers all prediction leagues
