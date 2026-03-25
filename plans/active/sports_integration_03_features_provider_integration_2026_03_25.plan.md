---
name: sports-integration-03-features-provider-integration
locked_by: live-defi-rollout
locked_since: 2026-03-25
overview: |
  FSS reads reference data + cross-provider mappings from instruments-service GCS,
  odds data from MTDS GCS. Uses mappings to resolve provider-specific IDs (footystats_id,
  understat_name) and calls features-interface adapters for enrichment data.
  FSS never fetches reference data directly from APIs.
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C4
  deployment: D1
  business: B1

repo_gates:
  - repo: features-sports-service
    code: C0
    notes: "Replace direct API fetch with GCS reader + mapping-based enrichment"
  - repo: unified-features-interface
    code: C0
    notes: "Verify UnderstatAdapter, FootystatsAdapter work with provider-specific IDs"

depends_on:
  - sports-integration-01-reference-data-pipeline
  - sports-integration-02-odds-market-data-pipeline

isProject: false
todos:
  # ============================================================================
  # PHASE 1 — GCS reader for reference data  [SEQUENTIAL]
  # ============================================================================
  - id: p1-gcs-reader
    content: |
      - [ ] [AGENT] P0. Create gcs_reader.py in FSS data/ directory.
        File: features_sports_service/data/gcs_reader.py (NEW)
        Read from instruments-service GCS bucket:
          instruments-store-sports-{project}/sports_reference/by_date/day={date}/entity={type}/
          instruments-store-sports-{project}/sports_reference/mappings/team_mapping.parquet
          instruments-store-sports-{project}/sports_reference/mappings/fixture_mapping.parquet
        Read from MTDS GCS bucket:
          market-data-tick-sports-{project}/raw_tick_data/by_date/day={date}/venue=ODDS_API/
        Return: dict of DataFrames keyed by entity type.
        Use unified_cloud_interface.get_storage_client() for GCS reads.
    status: pending

  # ============================================================================
  # PHASE 2 — Mapping-based provider resolution  [SEQUENTIAL after Phase 1]
  # ============================================================================
  - id: p2-mapping-resolution
    content: |
      - [ ] [AGENT] P0. Update _fetch_runner.py to use mappings for enrichment.
        File: features_sports_service/cli/handlers/_fetch_runner.py
        Current: fetches directly from API-Football
        New flow:
          1. Read team_mapping.parquet and fixture_mapping.parquet from GCS
          2. For each fixture: look up footystats_match_id, understat_match_id
          3. Call FootystatsAdapter.fetch_match_details(footystats_match_id)
          4. Call UnderstatAdapter.fetch_match(understat_match_id) for xG
          5. Call SoccerFootballInfoAdapter for progressive/halftime stats
          6. Call OpenMeteoAdapter with stadium lat/lon for weather
        SM keys: footystats-api-key, soccer-football-info-api-key (both in SM)
        Rate limit: 1 req/sec per provider, shard-level failure isolation
    status: pending
    blocked_by: p1-gcs-reader

  # ============================================================================
  # PHASE 3 — Wire exporters  [PARALLEL]
  # ============================================================================
  - id: p3-wire-exporters
    content: |
      - [ ] [AGENT] P1. Replace stub exporters with GCS-backed + enrichment data.
        File: features_sports_service/exporters/exports.py
        Each export function reads from GCS-backed loader:
          export_fixtures() -> GCS reference data
          export_fixture_stats() -> enrichment from footystats
          export_venues() -> GCS reference data
        All non-stub, all producing real rows.
    status: pending
    blocked_by: p2-mapping-resolution

  # ============================================================================
  # PHASE 4 — Validation  [SEQUENTIAL]
  # ============================================================================
  - id: p4-validation
    content: |
      - [ ] [AGENT] P0. Run FSS for 2026-03-22 with all providers.
        Verify: reference data read from GCS (not fetched from API)
        Verify: enrichment data fetched via mappings
        Verify: all entity types exported with non-zero rows
        Verify: 4+ providers contributing data
        QG: cd features-sports-service && bash scripts/quality-gates.sh
    status: pending
    blocked_by: p3-wire-exporters
---

# Sports Integration Plan 3: Features Provider Integration

Part of the 6-plan sports integration series.
Depends on Plan 1 (reference data in GCS) and Plan 2 (odds in GCS).

## Success Criteria
- FSS reads reference data from instruments-service GCS (no direct API fetch)
- FSS uses TeamMapping/FixtureMapping to resolve provider IDs
- FootyStats, Understat, Soccer-Football-Info, Open-Meteo data flowing
- All exporters produce non-zero rows
