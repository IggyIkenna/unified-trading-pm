---
name: features-sports-honest-coverage
overview:
  Honest-coverage backfill for features-sports-service — distinguish NaN-expected (out-of-coverage) from
  genuinely-missing upstreams; phased per-source then cross-source then enriched
type: mixed
epic: data-pipeline-completion
status: active
owner: Iggy
created: 2026-05-05
locked_by: live-defi-rollout
locked_since: 2026-05-05
completion_gates:
  code: C5
  deployment: D2
  business: B2
repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: D0
    business: B0
  - repo: features-sports-service
    code: C0
    deployment: D0
    business: B0
  - repo: deployment-api
    code: C0
    deployment: D0
    business: B0
  - repo: instruments-service
    code: C0
    deployment: D0
    business: B0
depends_on:
  - instruments_and_market_tick_data_completion_2026_05_01
isProject: false
---

# features-sports-service — honest-coverage backfill

## Problem

The features-sports-service computes ~1,000+ feature columns over `(date, league)` shards. Each feature has a different
**upstream profile**: some need only one source (e.g. `xg_rolling_5g` ← understat XG only), some need a single source
across multiple entities (e.g. transfermarkt PLAYER_VALUES + transfermarkt mapping), some need cross-source joins (e.g.
fixture-features need api_football FIXTURES + footystats MATCHES + understat XG + odds_api odds), some are "enriched"
derivatives stacked on top (e.g. starting-lineup-prediction features that combine PLAYER_VALUES + INJURIES +
FIXTURE_LINEUPS + historical PLAYER_STATS).

Each upstream source has its own coverage matrix:

- **Date floor**: when the source first started serving (api_football=2018-01-01, understat=2015-01-16,
  transfermarkt=2019-01-01, footystats=2019-01-01, soccer_football_info=2024-03-15, odds_api=2020-06-06,
  openmeteo=2019-03-02).
- **Per-(source, data_type) override**: e.g. api_football per-fixture endpoints effectively start 2020-06-06 (matches
  odds_api downstream cutoff); SFI progressive-stats endpoint returns empty before 2020-01-01.
- **League coverage**: understat covers ~5 European leagues; transfermarkt covers ~47 (Prediction + Features); SFI ~33;
  api_football ~58; footystats ~46; openmeteo all-fixture-dates with coordinates.
- **Per-(source, data_type) known gaps**: documented provider outages / paused leagues that should not count as missing.

Today the features service collapses three distinct "feature shard is NaN" states into one outcome:

1. **NaN-expected** — upstream legitimately doesn't cover this (league, date) (e.g. understat XG for MLS). Feature
   should be NaN-by-design and the shard should count as `done` in coverage UI.
2. **NaN-empty-confirmed** — upstream is in-coverage but returned empty (e.g. league had no fixture that week). Should
   be `empty_confirmed`.
3. **Skipped (genuine gap)** — upstream `attempted_failed` or no manifest row. Computing the feature would silently emit
   a misleading NaN. Should be **skipped** (no parquet write) and manifest marked `attempted_failed` with reason
   `upstream_missing`, so it shows up in the UI as a real issue.

Until we distinguish these three states the data-status tab cannot tell us "is this feature genuinely incomplete" vs
"this feature is supposed to be NaN here". With ~1,000 features and ~60 leagues × ~365 days × 7 years, it's infeasible
to chase every cell manually.

## Goal

Build the honest-coverage model for features-sports-service so that:

- The data-status tab for features-sports-service shows accurate `captured + empty_confirmed` vs
  `attempted_failed/missing` per feature group (or per feature, depending on Phase 4 design choice).
- Backfill VMs only re-fetch features that genuinely failed (skip ones that are correctly NaN by design + ones that
  succeeded).
- Operators can target a specific feature group's gap without manual spreadsheet bookkeeping.

## Architecture (the three components we need to build)

### Component A — `FEATURE_UPSTREAM_REQUIREMENTS` registry (UAC)

Per-feature-group spec listing the required upstream entities + sources. ~10-15 entries, not 1k (most features in a
group share upstream profile).

```python
FEATURE_UPSTREAM_REQUIREMENTS: dict[str, list[UpstreamReq]] = {
    "xg_rolling_5g": [
        UpstreamReq(source="understat", entity="XG", required=True),
        UpstreamReq(source="api_football", entity="FIXTURES", required=True),
    ],
    "transfer_value_delta_30d": [
        UpstreamReq(source="transfermarkt", entity="PLAYER_VALUES", required=True),
    ],
    "lineup_prediction_v1": [
        UpstreamReq(source="api_football", entity="FIXTURE_LINEUPS", required=True),
        UpstreamReq(source="api_football", entity="PLAYER_STATS", required=True),
        UpstreamReq(source="api_football", entity="INJURIES", required=True),
        UpstreamReq(source="transfermarkt", entity="PLAYER_VALUES", required=False),
    ],
    ...
}
```

`UpstreamReq` carries `required: bool` (true = skip shard if missing; false = optional, NaN if missing).

### Component B — `in_coverage(source, entity, league, date)` helper (UAC)

Single function used by both the features compute and the data-status calc. Returns True iff the (source, entity,
league, date) is _expected_ to have a manifest row. Uses:

- `SOURCE_COVERAGE_START` / `DATA_TYPE_COVERAGE_START` (date floor)
- `SPORTS_ENTITY_LEAGUE_COVERAGE` (league filter)
- `KNOWN_COVERAGE_GAPS` (provider-outage windows)

### Component C — features compute logic (features-sports-service)

```python
def compute_feature_shard(date, league, feature_group):
    upstreams = FEATURE_UPSTREAM_REQUIREMENTS[feature_group]
    for u in upstreams:
        if not in_coverage(u.source, u.entity, league, date):
            # NaN-expected — upstream legitimately doesn't cover this combo.
            # Continue to compute; output will be NaN where this upstream feeds in.
            continue
        prev = manifest.lookup({source=u.source, entity=u.entity, league=league, date=date})
        if prev is None or prev.capture_status == "attempted_failed":
            if u.required:
                # Genuine gap — skip, mark attempted_failed.
                manifest.record_failed(
                    row_key={feature_group, league, date},
                    error="upstream_missing",
                    upstream=f"{u.source}/{u.entity}",
                )
                return Skipped
    # All required upstreams complete (or out-of-coverage which is fine).
    value = compute(...)
    if value is None or pd.isna(value):
        manifest.record_empty(...)  # empty_confirmed
    else:
        manifest.add(...)  # captured
```

### Component D — `axis: per_feature_per_league_per_fixture_date` calc (deployment-api)

Expected denominator = (clipped dates × in-coverage leagues) per feature group. Found = `captured + empty_confirmed`.
Missing = `attempted_failed`.

## Phased rollout

Stages are by **upstream-profile complexity**, not by feature count. A single Phase 4-7 stage typically covers ~200
features at once because they share upstream profile.

### Stage A — Single-source features

Features that depend on exactly one external source. Easiest because the in-coverage check is one-dimensional. Examples:
`xg_*` (understat only), `transfer_value_*` (transfermarkt only), `weather_*` (openmeteo only).

### Stage B — Per-source iteration

After Stage A passes for one source, iterate to the others. We do this so we can validate the model on one source before
scaling it. Order: understat (5 leagues, smallest scope) → openmeteo (no league filter) → transfermarkt → SFI →
footystats → api_football (largest, highest reuse).

### Stage C — Cross-source join features

Features that need multiple sources combined (e.g. fixture-feature joins api_football FIXTURES + footystats MATCHES +
understat XG + odds_api odds). The `required=True/False` flag matters more here — if odds is missing we still want the
fixture features computed.

### Stage D — Enriched / derived features

Features computed _on top of_ other features. Examples: starting-lineup prediction (depends on PLAYER_VALUES +
INJURIES + FIXTURE_LINEUPS + historical PLAYER_STATS + maybe other features as inputs). Recursive upstream-spec — a
feature can have other features as upstreams.

## Phase 0 — Inventory (PARALLEL)

Before any code changes, dump the existing feature registry and group by upstream profile. Output: a markdown table
mapping `feature_group → upstream sources/entities`. Goal: count distinct upstream profiles (target ~15 buckets, not 1k
feature-by-feature work).

- [x] [SCRIPT] P0.A. Locate the features-sports-service feature registry (likely `features_sports_service/registry/` or
      `features_sports_service/calculators/`). List all feature_group names + the raw entities each reads from. Tag each
      by upstream profile (single-source / per-source / cross-source / enriched).
- [x] [SCRIPT] P0.B. Group features by upstream profile. Produce a summary table: profile_count,
      feature_count_per_profile, example_features. Confirm ~15 buckets is realistic.
- [x] [DOC] P0.C. Append the inventory + bucket mapping to this plan as the "Inventory" section. Decide which Stage
      (A/B/C/D) each profile belongs to.

**Phase 0 success**: a single markdown table inside this plan listing ~15 upstream profiles, mapped to Stages A-D, with
feature counts per profile. This is the input to Phases 1+2.

## Phase 1 — UAC additions (SEQUENTIAL after P0)

- [ ] [AGENT] P1.A. Add `UpstreamReq` dataclass to UAC `unified_api_contracts.sports`.
- [ ] [AGENT] P1.B. Add `FEATURE_UPSTREAM_REQUIREMENTS` dict — initially populated with the buckets discovered in
      Phase 0.
- [ ] [AGENT] P1.C. Add `in_coverage(source, entity, league, date) -> bool` helper. Composes
      `clip_dates_to_source_coverage` + `get_entity_league_coverage` + `is_in_known_gap`.
- [ ] [AGENT] P1.D. Unit tests for `in_coverage` — coverage of each clip rule; edge cases (pre-launch dates,
      out-of-coverage leagues, gap windows).
- [ ] [AGENT] P1.E. UAC quickmerge.

**Phase 1 success**: UAC `in_coverage()` returns sane answers for ~10 spot-check (source, entity, league, date) combos
including the known-gap windows.

## Phase 2 — features-sports-service compute changes (SEQUENTIAL after P1)

- [ ] [AGENT] P2.A. Update the feature compute path to call `in_coverage` per upstream before fetching/joining; if
      `required=True` and missing, skip the shard and record_failed with `upstream_missing` reason.
- [ ] [AGENT] P2.B. NaN handling — explicitly distinguish NaN-by-design (write parquet, manifest `captured`) from
      NaN-error (no parquet write, manifest `attempted_failed`).
- [ ] [AGENT] P2.C. Backwards compat — features computed before this change have manifest rows that don't carry the
      `upstream_missing` reason. Decide: re-classify on next backfill, or one-shot reclassification script.
- [ ] [AGENT] P2.D. Unit tests covering all three NaN states.
- [ ] [AGENT] P2.E. features-sports-service quickmerge.

## Phase 3 — deployment-api data-status calc (SEQUENTIAL after P2)

- [ ] [AGENT] P3.A. Add `axis: per_feature_per_league_per_fixture_date` to `_sports_honest_coverage` in
      `deployment_api/services/data_status_service.py`.
- [ ] [AGENT] P3.B. Per-feature-group expected denominator = (clipped fixture dates) × (in-coverage leagues). Use UAC
      `in_coverage`.
- [ ] [AGENT] P3.C. Update SPORTS_DATA_TYPE_META (or a new FEATURES_SPORTS_DATA_TYPE_META) with one entry per feature
      group from Phase 0 inventory.
- [ ] [AGENT] P3.D. Unit tests for the new axis calculation.
- [ ] [AGENT] P3.E. deployment-api quickmerge.

**Phase 3 success**: hitting `/api/data-status/turbo?service=features-sports-service` returns honest per-feature-group
coverage with `found / expected` ratios that match operator expectation (not over-counting NaN-by-design).

## Phase 4 — Stage A backfill (SEQUENTIAL after P3)

Backfill the **single-source** features one source at a time. After each source completes, verify the data-status tab
shows expected coverage before moving to the next.

- [ ] [SCRIPT] P4.A. Stage A — understat (XG features only). Smallest scope (5 leagues, ~10 years), validates the model
      end-to-end.
- [ ] [SCRIPT] P4.B. Stage A — openmeteo (weather features). All-fixture-dates, no league filter; tests the
      no-league-coverage path.
- [ ] [SCRIPT] P4.C. Stage A — transfermarkt (transfer-value features). Quarterly cadence; tests the per-feature
      periodic axis.
- [ ] [SCRIPT] P4.D. Stage A — soccer-football-info (progressive-stats features). Recent launch (2024-03-15); tests the
      post-launch clip.
- [ ] [SCRIPT] P4.E. Stage A — footystats (matches/predictions/odds features). Largest single-source group.
- [ ] [SCRIPT] P4.F. Stage A — api_football (fixture / events / lineups / stats / injuries features). Largest source;
      per-(data_type) coverage windows apply.
- [ ] [SCRIPT] P4.G. Stage A — odds_api (MTDS odds_horizon_bucket features).

**Phase 4 success**: each single-source feature group shows ≥95% coverage on the data-status tab where the source itself
is ≥95% (the gap should track the upstream gap, not exceed it).

## Phase 5 — Stage B (cross-source-but-no-join) iteration

Some features compute over a single source's data + a fixture calendar from api_football (the universal pulse). These
aren't true cross-source joins — they just need fixtures as a clock. Treat as a separate stage so we can catch
fixture-coverage as a single shared gating dimension.

- [ ] [SCRIPT] P5.A. Iterate the per-source features that anchor on api_football FIXTURES as the calendar. Verify each
      one's coverage tracks the intersection of the source AND fixtures.
- [ ] [SCRIPT] P5.B. Identify any per-source feature whose coverage diverges from the upstream gap — that means the
      bucket-coverage logic isn't handling that profile. Fix before Stage C.

## Phase 6 — Stage C cross-source join features

Features that genuinely combine multiple sources (e.g. fixture-features joining api_football + footystats + understat +
odds_api).

- [ ] [AGENT] P6.A. Audit each cross-source feature group and classify each upstream as `required` or `optional`.
      Required = if missing, skip the shard. Optional = if missing, NaN that column but compute the rest.
- [ ] [SCRIPT] P6.B. Backfill cross-source features. Verify coverage = the intersection of (required upstreams'
      coverage) — not less.
- [ ] [AGENT] P6.C. Add tests that check the optional-upstream path: missing odds shouldn't skip the whole feature
      shard.

## Phase 7 — Stage D enriched / derived features

Features computed on top of other features (lineup-prediction, ensemble features, etc.). Recursive upstream-spec — a
feature can have other features as upstreams.

- [ ] [AGENT] P7.A. Extend `UpstreamReq` to allow `kind="feature"` (vs `kind="raw_entity"`). Recursive coverage check.
- [ ] [AGENT] P7.B. Topological-sort feature DAG so we backfill leaves first. Cycle detection (must be a DAG).
- [ ] [SCRIPT] P7.C. Backfill enriched features in dependency order. Check that lineup-prediction features show the
      union-of-required-upstreams coverage gap pattern, not stand-alone.

## Phase 8 — UI polish + drift monitoring

- [ ] [AGENT] P8.A. UI: deployment-ui data-status tab for features-sports-service. Show per-feature-group coverage +
      per-upstream gap attribution (when a feature is at 50%, show which upstream is dragging it down).
- [ ] [AGENT] P8.B. Drift alert: if a feature group's coverage drops > X% since last hour, page the operator. Catches
      runtime regressions.
- [ ] [DOC] P8.C. Codex/playbook: how to add a new feature to the registry, tag its upstream profile, and verify it
      lands in data-status correctly.

## Out of scope for this plan

- Data quality of upstream raw data (PLAYER_VALUES adapter, fs-backfill rate limits, etc. — those are separate plans).
- Strategy-level feature consumption (this is purely about features-service honest-coverage; downstream strategy
  backtests are tracked by their own plans).
- DeFi / CeFi / TradFi features (this plan is sports-only; the model generalises but we ship sports first).

## Success Criteria

- **C5 + D2 + B2** per repo gates above.
- Data-status tab for features-sports-service shows honest `captured + empty_confirmed` vs `attempted_failed` per
  feature group.
- A simulated upstream failure (delete one (date, league) raw shard) causes the dependent feature shards to flip to
  `attempted_failed`, NOT silently emit NaN.
- A simulated out-of-coverage feature compute (understat XG for MLS) writes a NaN parquet AND marks manifest `captured`,
  NOT `attempted_failed`.
- Backfill VMs picking up failed-only shards don't waste cycles re-fetching in-coverage successful shards.

## Phase 0 inventory output (2026-05-05) — CORRECTED

> **Initial pass via the YAML registry (`feature_definitions.yaml`) found only 142 features and was misleading.** The
> YAML is stale operator documentation, not the runtime source of truth. Re-doing Phase 0 against the actual runtime
> pipeline (`feature_catalog.py` column constants + `derived_features_exporter._run_new_calculators` dispatch) gives the
> correct picture.

### Headline numbers (corrected)

- **1,104 features** total across 34 calculators (`DERIVED_FEATURE_COUNT=912 + ODDS_FEATURE_COUNT=156`, plus a few
  pipeline-stage outputs).
- **11 raw entity keys** read by the pipeline via `ref_data` dict (assembled by `read_all_reference_data(date)` in
  `data/gcs_reader.py`):
  `fixtures, fixture_stats, fixture_events, fixture_lineups, ht_stats,  footystats_matches, understat_xg, coaches, injuries, player_values,  transfer_records`.
- **+ 5 standalone reads**: `read_pre_match_standings`, `read_venues`, `read_odds_data` (footystats),
  `compute_weather_for_fixtures` (openmeteo), `read_bucketed_odds` (MTDS odds_horizon_bucket).

### YAML drift — Phase 1 input must come from code, not YAML

`feature_definitions.yaml` declares 142 features. Runtime catalog is 1,104. Cannot use the YAML as the input to
`FEATURE_UPSTREAM_REQUIREMENTS`.

Phase 1 must reverse-engineer per-calculator upstream requirements from the runtime dispatcher + each calculator's
compute signature.

### Per-calculator inventory (1,104 features, 34 calculators)

| Calculator                    | Cols | Real upstream (from dispatcher)                            | Stage |
| ----------------------------- | ---: | ---------------------------------------------------------- | ----- |
| `team_form`                   |   82 | api_football FIXTURES (history)                            | A     |
| `team_goals`                  |   96 | api_football FIXTURES (history)                            | A     |
| `team_xg`                     |    8 | understat XG + api_football FIXTURES                       | C     |
| `multisource_xg`              |   28 | understat XG + footystats MATCHES + (synthetic xG)         | C/D   |
| `team_derived`                |   26 | derived from team_form/team_goals                          | D     |
| `season_context`              |   20 | api_football FIXTURES + STANDINGS                          | A     |
| `goal_timing`                 |   20 | api_football FIXTURE_EVENTS                                | A     |
| `halftime_calculator`         |   97 | footystats `ht_stats` + fixture_stats                      | C     |
| `ht_features`                 |   13 | footystats `ht_stats`                                      | A     |
| `relative_context`            |   60 | FIXTURES + STANDINGS + league aggregates                   | A/D   |
| `xg_decomposition`            |   20 | api_football FIXTURE_STATS + understat XG + (synthetic xG) | C/D   |
| `meta_features`               |   12 | derived (other features)                                   | D     |
| `ml_predictions`              |   10 | derived (other features)                                   | D     |
| `replacement_model`           |    8 | transfermarkt PLAYER_VALUES + (player_quality model)       | C/D   |
| `bucketed_features`           |   16 | derived (bucketed expansions)                              | D     |
| `odds_calculator`             |  153 | footystats ODDS + MTDS odds_horizon_bucket                 | C     |
| `weather_calculator`          |   10 | openmeteo (compute_weather_for_fixtures)                   | A     |
| `transfer_window_calculator`  |   38 | transfermarkt PLAYER_VALUES + transfer_records + lineups   | C     |
| `squad_value_calculator`      |   14 | transfermarkt PLAYER_VALUES + transfer_records             | A     |
| `manager_calculator`          |   40 | api_football coaches + FIXTURES history                    | A     |
| `formation_calculator`        |   15 | api_football FIXTURE_LINEUPS + FIXTURES history            | A     |
| `injury_impact_calculator`    |   10 | api_football INJURIES                                      | A     |
| `travel_calculator`           |   10 | api_football FIXTURES + venues + history                   | A     |
| `european_fatigue_calculator` |    8 | api_football FIXTURES (UEFA history)                       | A     |
| `elo_calculator`              |   10 | api_football FIXTURES (history)                            | A     |
| `h2h_calculator`              |   42 | api_football FIXTURES (history)                            | A     |
| `poisson_xg_calculator`       |   16 | xG features (derived)                                      | D     |
| `player_lineup_calculator`    |   74 | api_football FIXTURE_LINEUPS + transfermarkt PLAYER_VALUES | C     |
| `advanced_stats_calculator`   |   62 | api_football FIXTURE_STATS + FIXTURES                      | A     |
| `venue_context`               |   20 | api_football FIXTURES + venues                             | A     |
| `league_calculator`           |   30 | api_football FIXTURES + STANDINGS                          | A     |
| `referee_features`            |   20 | api_football FIXTURES (referee field)                      | A     |
| `bench_sub_calculator`        |   16 | api_football FIXTURE_EVENTS + FIXTURE_LINEUPS              | A     |

### Stage rollup (corrected)

| Stage                      | Calculators |   Features | Notes                                                                                                                                                                                                                                            |
| -------------------------- | ----------: | ---------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **A — Single-source**      |         ~17 |       ~620 | api_football-only families (team_form 82, team_goals 96, h2h 42, manager 40, advanced_stats 62, season_context 20, league 30, etc.) + weather (openmeteo 10) + ht_features (footystats 13) + squad_value (transfermarkt 14) + injury_impact (10) |
| **C — Cross-source join**  |          ~9 |       ~414 | xg (multisource), odds (footystats + MTDS), halftime (footystats + api_football), transfer_window (api_football + transfermarkt), player_lineup (api_football + transfermarkt), team_xg (understat + api_football), xg_decomposition             |
| **D — Enriched / derived** |          ~6 |        ~70 | meta_features, ml_predictions, bucketed_features, team_derived, poisson_xg, relative_context                                                                                                                                                     |
| **Total**                  |      **34** | **~1,104** |                                                                                                                                                                                                                                                  |

### Genuinely missing wiring (decision needed before Phase 4)

1. **SFI_PROGRESSIVE_STATS not consumed** — captured at 96.5% but no calculator reads it. Either (a) add a calculator
   family for per-match progressive xG / dominance / 30-second-snapshot features, or (b) declare the data as
   captured-but-unused and remove the manifest pressure to keep capturing it.
2. **`footystats_predictions` is read by `gcs_reader` but no calculator consumes it.** Same decision: add features or
   retire from capture.

### Phase 0 follow-ups (BEFORE Phase 1 starts)

- [ ] [DOC] P0.D. Phase 1 must reverse-engineer FEATURE_UPSTREAM_REQUIREMENTS from the dispatcher + per-calculator code,
      NOT from the YAML.
- [ ] [DOC] P0.E. Update `feature_definitions.yaml` to actually reflect the 1,104 features the runtime computes — OR
      delete it and put operator-facing documentation in a different format. The current drift is misleading.
- [ ] [AGENT] P0.F. Decision on SFI_PROGRESSIVE_STATS — wire features that consume it OR retire from capture. Same for
      `footystats_predictions`.

---

### LEGACY (incorrect) Phase 0 output below — kept for traceability

> The text below was the first pass against the stale YAML. Numbers are wrong (142 features, 33 profiles) but the
> bucketing approach is sound. See "corrected" section above for real numbers.

### Headline numbers (LEGACY — yaml-only)

- **142 features** declared in the YAML registry (real column count is higher — ~635+ for derived_features per
  `feature_catalog.py` — because bucketed variants expand at runtime).
- **33 distinct upstream profiles** (the `sources: [...]` tuple).
- **37 distinct source tokens** in the YAML; ~half map to RAW external sources (api_football / footystats / odds_api /
  transfermarkt), the rest to DERIVED feature outputs (Stage D inputs).

### Stage breakdown

| Stage                      | Profiles | Features | Description                                                                                                                                                                                                                                                                                          |
| -------------------------- | -------: | -------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A — Single-source**      |       16 |       64 | Depend on exactly one external source; iterate one source at a time                                                                                                                                                                                                                                  |
| **C — Cross-source join**  |        3 |       11 | api_football + transfermarkt joins (no understat / footystats / SFI joins yet)                                                                                                                                                                                                                       |
| **D — Enriched / derived** |       12 |       61 | Depend on derived feature outputs (synthetic*xg, lineup_predictions, replacement_model, base_model_predictions, season_context, fatigue_model, league_season_aggregates, etc.) — includes the 33 `bucketed*\*`features which have empty`sources:` because they expand from other features at runtime |
| **X — Config-only**        |        2 |        6 | transfer_window_calendar / position_grouping (UAC config, not captured data)                                                                                                                                                                                                                         |
| **Total**                  |   **33** |  **142** |                                                                                                                                                                                                                                                                                                      |

### Stage A profiles (do these FIRST, one source at a time)

| Profile (YAML tokens)             | Real upstream                             | Calculators                                                         | Features |
| --------------------------------- | ----------------------------------------- | ------------------------------------------------------------------- | -------: |
| `fixtures+stats`                  | api_football FIXTURES + FIXTURE_STATS     | season_context, sports_validity_engine, xg_decomposition_calculator |       11 |
| `manager_timeline`                | api_football TEAMS (manager fields)       | manager_calculator                                                  |        6 |
| `lineups_history`                 | api_football FIXTURE_LINEUPS              | player_lineup_calculator, transfer_window_calculator                |        5 |
| `player_stats`                    | api_football PLAYER_STATS                 | player_lineup_calculator, xg_decomposition_calculator               |        3 |
| `event_substitutions`             | api_football FIXTURE_EVENTS               | bench_sub_calculator                                                |        3 |
| `fixtures+standings`              | api_football FIXTURES + STANDINGS         | season_context                                                      |        2 |
| `fixtures+manager_timeline`       | api_football FIXTURES + TEAMS             | manager_calculator                                                  |        2 |
| `formations+historical_lineups`   | api_football FIXTURE_LINEUPS              | manager_calculator                                                  |        2 |
| `xi_overlap_history`              | api_football FIXTURE_LINEUPS              | manager_calculator                                                  |        2 |
| `player_data`                     | api_football PLAYER_STATS                 | player_lineup_calculator                                            |        1 |
| `odds_snapshots`                  | footystats ODDS                           | odds_calculator, sports_validity_engine                             |       10 |
| `odds_time_series`                | odds_api ODDS_HORIZON_BUCKET (via MTDS)   | odds_calculator                                                     |        7 |
| `transfermarkt_values`            | transfermarkt PLAYER_VALUES               | transfer_window_calculator                                          |        4 |
| `player_values+position_tags`     | transfermarkt PLAYER_VALUES (+UAC config) | player_lineup_calculator                                            |        2 |
| `player_values`                   | transfermarkt PLAYER_VALUES               | player_lineup_calculator                                            |        2 |
| `player_values+position_grouping` | transfermarkt PLAYER_VALUES (+UAC config) | bench_sub_calculator                                                |        2 |

**Stage A iteration order**: footystats (10f, ODDS — already at 92% upstream) → odds_api (7f) → transfermarkt (10f,
PLAYER_VALUES is the active gap) → api_football (37f, biggest scope, depends on
FIXTURES/STATS/LINEUPS/EVENTS/PLAYER_STATS/TEAMS).

### Stage C profiles (cross-source — after all Stage A iterations land)

| Profile (YAML tokens)             | Real upstreams                                             | Calculators                                          | Features |
| --------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------- | -------: |
| `player_minutes+transfer_history` | api_football PLAYER_STATS + transfermarkt PLAYER_VALUES    | transfer_window_calculator                           |        4 |
| `lineups+transfer_tags`           | api_football FIXTURE_LINEUPS + transfermarkt PLAYER_VALUES | transfer_window_calculator                           |        4 |
| `transfer_window_data+xi`         | transfermarkt PLAYER_VALUES + api_football FIXTURE_LINEUPS | player_lineup_calculator, transfer_window_calculator |        3 |

**Stage C is just api_football × transfermarkt today.** No understat/SFI/footystats joins surface in the YAML.

### Stage D profiles (depend on derived/feature outputs — after Stages A+C)

| Profile (YAML tokens)                         | Derived dependencies                  | Features |
| --------------------------------------------- | ------------------------------------- | -------: |
| `(empty)` (bucketed)                          | bucketed expansions of other features |       33 |
| `synthetic_xg_model`                          | derived xG model                      |        5 |
| `manager_change_date+rolling_xg`              | derived xG rolling + raw TEAMS        |        4 |
| `lineup_predictions`                          | derived lineup model                  |        4 |
| `replacement_model`                           | derived replacement model             |        4 |
| `base_model_predictions`                      | derived base predictions              |        3 |
| `prior_starter_definition+projected_xi`       | derived                               |        2 |
| `season_context`                              | derived                               |        2 |
| `fixtures+league_season_aggregates+standings` | api_football raws + derived           |        1 |
| `fatigue_model`                               | derived                               |        1 |
| `player_quality_ratings`                      | derived                               |        1 |
| `player_embeddings`                           | derived                               |        1 |

Stage D is a topo-sort problem (Phase 7) — the derived models themselves sit somewhere in this DAG and need to be
computed before their consumers.

### Stage X — config-only (no GCS coverage tracking needed)

| Profile                    | Real upstream       | Features |
| -------------------------- | ------------------- | -------: |
| `position_grouping`        | UAC (static config) |        4 |
| `transfer_window_calendar` | UAC (static config) |        2 |

These don't need data-status tracking at all — output of these features should never be NaN unless the UAC config is
broken.

### Cross-cutting findings

1. **No understat (XG) features in the YAML.** The xg_decomposition features use `synthetic_xg_model` (a derived
   feature) rather than raw understat. The YAML may be out-of-date (the 100% XG entity coverage suggests we DO capture
   understat data we're not using yet).
2. **No openmeteo (WEATHER) features in the YAML.** `weather_calculator.py` exists in the calculators dir but has no
   entry in `feature_definitions.yaml`. Either yaml is incomplete or the weather features got retired.
3. **No SFI / SFI_PROGRESSIVE_STATS features in the YAML.** Despite the recent SFI ingest work and 96.5%
   SFI_PROGRESSIVE_STATS coverage. Likely in-progress feature work not yet declared in the registry.
4. **No PREDICTIONS / MATCHES (footystats)-direct features** beyond ODDS. Match info comes through `fixtures`
   (api_football) only.
5. The `sources:` field in the YAML is documentation, not the runtime contract. Phase 1 must verify each profile's real
   GCS reads against the calculator code before writing FEATURE_UPSTREAM_REQUIREMENTS.

### Phase 0 follow-up before Phase 1

- [ ] [DOC] Reconcile YAML vs calculator code — open question: which is the SSOT? The YAML `sources:` field looks
      human-maintained; the calculator reads via gcs_reader are the runtime contract. Phase 1's first step should be to
      grep each calculator for actual `read_entity(...)` calls and reconcile against the YAML.
- [ ] [DOC] Add weather + understat + SFI + predictions features to the YAML (or confirm they shouldn't be there). The
      100% XG / 96.5% SFI_PROGRESSIVE_STATS / 100% WEATHER captures suggest features SHOULD exist on top of these.
