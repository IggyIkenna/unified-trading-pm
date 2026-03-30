---
title: "Canonical Team Name Mapping — Propagation to Production"
priority: P1
status: active
owner: agent
created: 2026-03-30
locked_by: live-defi-rollout
locked_since: 2026-03-30
---

## Context

Team name resolution is fragmented: e2e-testing scripts use ad-hoc fuzzy matching, the arb backtest has its own
`_fuzzy_name()`/`_names_match()`, and UAC's `resolve_team_to_canonical()` has alias gaps for Odds API, OddsPapi, and
Betfair variants. This causes:

- **Silent mismatches**: "AC Milan" (Odds API) vs "AC Milan" (OddsPapi home_team) maps outcome to wrong side → 530%
  price diff reported as data quality issue
- **Duplicate canonical IDs**: "Feyenoord Rotterdam" → `FEYENOORD_ROTTERDAM` vs "Feyenoord" → `FEYENOORD` — same team,
  different IDs
- **No validation**: when a team name can't resolve, it silently falls back to slugification → undetected data
  corruption in ML features

### Data Sources and Their Team Name Formats

| Source          | Format                      | Example                             |
| --------------- | --------------------------- | ----------------------------------- |
| API-Football    | Display name                | "Manchester City"                   |
| Odds API        | Full name with suffix       | "Manchester City FC", "AC Milan"    |
| OddsPapi        | Mixed (varies by bookmaker) | "Man City", "AC Milan"              |
| Betfair         | Shortened                   | "Man City", "Newcastle", "The Draw" |
| Canonical (UAC) | SCREAMING_SNAKE             | `MAN_CITY`, `AC_MILAN`              |

### Blast Radius

- **UAC**: `team_mappings.py` (alias dicts), `canonical_ids.py`
- **instruments-service**: fixture resolution, `sports/` adapters
- **MTDS**: odds storage with canonical fixture IDs
- **features services**: ML feature computation per canonical fixture
- **strategy-service**: arb detection, signal generation
- **e2e-testing**: all sports scripts

## Phases

### Phase 1: UAC Alias Expansion [PARALLEL]

- [ ] [AGENT] P0. Audit all Odds API team names (64 bookmakers × 20 leagues) against UAC `resolve_team_to_canonical()`.
      Log every name that falls through to slugification (tier 3 fallback). Target: 0 fallbacks for prediction leagues.

- [ ] [AGENT] P0. Audit all OddsPapi team names (36 bookmakers × 20 leagues) — same check. Cross-reference with Odds API
      audit to find names that resolve differently.

- [ ] [AGENT] P0. Audit all Betfair runner names (4,837 events) — same check. Betfair uses shortened names ("Newcastle"
      vs "Newcastle United") that need explicit aliases.

- [ ] [AGENT] P1. Add missing aliases to UAC league-specific alias dicts (`EPL_TEAM_ALIASES`, `SERIE_A_TEAM_ALIASES`,
      etc.). Each alias dict entry: `"CANONICAL_ID": ["Variant 1", "Variant 2", "OddsAPI Name", "Betfair Name"]`.

- [ ] [AGENT] P1. Add Odds API-specific team name corrections to `API_FOOTBALL_TO_CANONICAL` dict (e.g.,
      "Internazionale" → "INTER_MILAN", "FSV Mainz 05" → "MAINZ").

- [ ] [AGENT] P1. Rebuild `_UNIVERSAL_REVERSE` and `BETFAIR_TO_CANONICAL` from expanded alias dicts. Verify zero
      collisions (two different teams mapping to same canonical ID).

**QG gate**: `cd unified-api-contracts && bash scripts/quality-gates.sh`

### Phase 2: Validation Framework [SEQUENTIAL after Phase 1]

- [ ] [AGENT] P0. Add `validate_team_resolution()` to UAC that takes a provider name
  - team name, resolves to canonical, and raises `TeamResolutionError` if it falls through to slugification. This is the
    "fail loud" requirement.

- [ ] [AGENT] P0. Add `validate_fixture_alignment()` to UAC that takes two fixtures (from different sources) matched by
      team names, and checks:
  1. Both home teams resolve to same canonical ID
  2. Both away teams resolve to same canonical ID
  3. Kickoff times are within ±30 min (UTC alignment check) Raises `FixtureAlignmentError` with details if any check
     fails.

- [ ] [AGENT] P1. Add UAC test: for every team in every alias dict, verify `resolve_team_to_canonical()` returns the
      expected canonical ID. This prevents regressions when new aliases are added.

- [ ] [AGENT] P1. Add UAC test: for every pair of alias dicts that share a canonical ID (e.g., EPL + Betfair both have
      "ARSENAL"), verify they resolve to the same ID.

**QG gate**: `cd unified-api-contracts && bash scripts/quality-gates.sh`

### Phase 3: Service Integration [SEQUENTIAL after Phase 2]

- [ ] [AGENT] P1. **instruments-service**: Update sports fixture resolution to use `validate_team_resolution()` when
      ingesting from any source. Log `TEAM_RESOLUTION_FAILED` event (not silent skip) when a team name can't resolve.

- [ ] [AGENT] P1. **MTDS**: When storing odds ticks, validate that the fixture's canonical team IDs match the
      instrument's team IDs. Reject rows where they don't match (emit `FIXTURE_MISMATCH` event).

- [ ] [AGENT] P1. **MTDS sports adapter** (Odds API + OddsPapi): Use `validate_team_resolution()` for outcome name →
      HOME/AWAY/DRAW mapping. Current logic uses string matching; replace with canonical resolution.

- [ ] [AGENT] P2. **features services**: When computing ML features, validate that the fixture has odds from at least N
      bookmakers with resolved team names. Skip fixture (with warning event) if resolution coverage < threshold.

- [ ] [AGENT] P2. **strategy-service**: ArbitrageStrategy validates that both legs of an arb have matching canonical
      fixture IDs before execution.

**QG gate**: Per-repo quality gates for all modified services.

### Phase 4: E2E Testing Scripts [PARALLEL with Phase 3]

- [ ] [AGENT] P1. Update `betfair_merge.py` to use `validate_team_resolution()` instead of ad-hoc
      `_canonical_fuzzy_match()`. Log unresolvable teams.

- [ ] [AGENT] P1. Update `arb_rolling_backtest.py` to use UAC `resolve_team_to_canonical()` instead of local
      `_fuzzy_name()`/`_names_match()`. Remove the duplicated team name logic.

- [ ] [AGENT] P1. Update `odds_api_freshness_audit.py` and `odds_api_betfair_audit.py` to use canonical resolution for
      outcome mapping (already done in this session).

- [ ] [AGENT] P2. Add a standalone `validate_data_sources.py` script that:
  1. Loads all three sources (Odds API, OddsPapi, Betfair) for a date range
  2. For each fixture, checks team name resolution across all sources
  3. Checks kickoff time alignment (±30 min)
  4. Reports: matched fixtures, unmatched fixtures, resolution failures This replaces ad-hoc validation scattered across
     scripts.

### Phase 5: Cross-Source Fixture Reconciliation [SEQUENTIAL after Phase 3]

The canonical fixture ID must be the single join key across ALL data sources. Every source's data must be tagged with a
canonical fixture ID at ingestion time, and that ID must be validated against the fixture registry before storage.

- [ ] [AGENT] P0. **MTDS fixture reconciliation** — When MTDS ingests odds from multiple providers (Odds API, OddsPapi,
      Betfair), it must reconcile them to a single canonical `fixture_id` using `validate_fixture_alignment()`. If a
      fixture from source A cannot be matched to the same fixture from source B (team names or kickoff time diverge),
      emit `FIXTURE_RECONCILIATION_FAILED` event and reject the data. Never store odds under an unreconciled fixture ID.

- [ ] [AGENT] P0. **Cross-source fixture ID join** — Add a `fixture_reconciliation` table/parquet that maps
      {odds_api_event_id, oddspapi_fixture_id, betfair_event_id, api_football_fixture_id} → canonical_fixture_id. Built
      at ingestion time by MTDS, validated by instruments-service. This is the SSOT for "these are the same match."

- [ ] [AGENT] P1. **All data sources use canonical fixture ID** — FootyStats, weather data, lineup data, xG data,
      referee data — every source that provides per-fixture data must be tagged with the canonical fixture ID at
      ingestion. Sources that use their own IDs (FootyStats match_id, weather station coords) must be joined to
      canonical via the reconciliation table.

### Phase 6: Feature Timestamp Validation [SEQUENTIAL after Phase 5]

ML features are computed at specific time buckets (T-24h, T-6h, T-1h, etc.). The feature value is only valid if the
underlying data actually falls within that time window. A T-1h odds_drift feature computed from a T-3h stale tick is a
data leak / incorrect feature.

- [ ] [AGENT] P0. **`validate_feature_timestamp()`** in UAC — Takes a feature bucket label (e.g. "T-1h"), a fixture
      kickoff time, and a data point's `bm_time` / timestamp. Returns True if the data point falls within the bucket's
      acceptable window (e.g. T-1h accepts data from T-70m to T-50m). Raises `FeatureTimestampError` if outside window.

- [ ] [AGENT] P0. **Features-service integration** — Every time-sensitive feature calculator (odds_drift, CLV,
      sharp_money_flow, market_efficiency) must call `validate_feature_timestamp()` before computing. If the underlying
      tick is outside the bucket window, the feature is set to NULL (not computed from stale data). Log
      `FEATURE_STALE_DATA` event with details.

- [ ] [AGENT] P1. **Feature provenance metadata** — Each computed feature row includes: `feature_bm_time` (actual
      bookmaker timestamp used), `feature_staleness_s` (seconds between bm_time and bucket target), `feature_bookmaker`
      (which bookmaker's price was used). This lets downstream consumers (strategy, ML training) filter by data quality.

- [ ] [AGENT] P1. **Multi-source feature fallback** — If pinnacle's price is stale at T-1h but betsson's is fresh, use
      betsson. Feature calculator ranks bookmakers by reliability (pinnacle > betsson > coral > unibet) and picks the
      freshest available within the bucket window. Log which source was used.

- [ ] [AGENT] P2. **Training data validation** — ML training pipeline validates that every feature row has
      `feature_staleness_s` within acceptable bounds. Reject training samples where >30% of features are NULL (too much
      stale data). Report per-fixture, per-bucket data completeness.

### Phase 7: Non-Odds Data Source Alignment [PARALLEL with Phase 6]

All data sources used for ML features must align to the canonical fixture ID and pass timestamp validation. This
includes non-odds sources.

- [ ] [AGENT] P1. **FootyStats** — Match IDs → canonical fixture ID mapping. FootyStats uses its own match_id. Map via
      team names + date using `validate_fixture_alignment()`. Store mapping in reconciliation table. Data: xG, shots,
      possession, corners, cards per fixture.

- [ ] [AGENT] P1. **Weather data** — Stadium coordinates → canonical fixture ID. Weather is fetched per-stadium
      per-kickoff-time. Validate that weather timestamp is within ±2h of kickoff. Tag with canonical fixture ID via
      stadium → home_team → fixture mapping.

- [ ] [AGENT] P1. **Lineup data** (API-Football) — Uses API-Football fixture_id which is already in the reconciliation
      table. Validate that lineup confirmation timestamp is before kickoff (T-1h lineup features must use confirmed
      lineups, not predicted).

- [ ] [AGENT] P1. **Referee data** (API-Football) — Same fixture ID mapping as lineups. Validate referee assignment is
      confirmed (not "TBD").

- [ ] [AGENT] P2. **TV schedule / attendance data** — Maps via team + date. Less critical for ML but should still use
      canonical fixture IDs for consistency.

- [ ] [AGENT] P2. **Historical results** (settlement) — API-Football match results must map to canonical fixture ID. The
      arb backtest's `_match_results()` already uses canonical resolution (fixed in this session). Production settlement
      service must do the same.

### Phase 8: Monitoring [AFTER Phase 6]

- [ ] [AGENT] P2. Add events to UAC: `TEAM_RESOLUTION_FAILED`, `FIXTURE_MISMATCH`, `FIXTURE_RECONCILIATION_FAILED`,
      `FEATURE_STALE_DATA`, `FEATURE_TIMESTAMP_ERROR`. Wire into alerting service for Telegram notifications.

- [ ] [AGENT] P2. Add GCS metrics: per-day count of resolution failures per source, per-day feature staleness
      distribution, per-day reconciliation success rate. Dashboard in Grafana.

- [ ] [AGENT] P2. Weekly automated validation job: run `validate_data_sources.py` across all sources for the past week,
      report any new team names that fall through to slugification, any fixture mismatches, any stale features.

## Success Criteria

1. **Zero silent fallbacks**: Every team name from all sources (Odds API, OddsPapi, Betfair, FootyStats, API-Football,
   weather) resolves to a known canonical ID for all 20 prediction leagues.
2. **Fail loud**: Any unresolvable team name raises an error/event, never silently proceeds with a bad canonical ID.
3. **Cross-source alignment**: For every fixture, all sources agree on canonical team IDs and kickoff times (within ±30
   min).
4. **Single join key**: Every data point (odds tick, xG stat, weather reading, lineup, result) is tagged with the same
   canonical fixture ID.
5. **Feature timestamp integrity**: No ML feature is computed from data outside its bucket window. Stale data → NULL
   feature, not wrong feature.
6. **Feature provenance**: Every feature row records which source's data was used and how stale it was.
7. **Single implementation**: All team name resolution goes through UAC `resolve_team_to_canonical()` — no local fuzzy
   matching in scripts or services.
8. **All QG pass**: UAC + all modified services pass quality gates.
