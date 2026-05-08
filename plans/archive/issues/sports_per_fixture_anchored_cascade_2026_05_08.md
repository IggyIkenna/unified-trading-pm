---
title:
  "Sports orchestrator iterates per-LEAGUE-per-day for FIXTURE_STATS / EVENTS / LINEUPS / INJURIES instead of
  per-FIXTURE — silent missing-fixture downstream gaps"
created: 2026-05-08
author: ikenna
source:
  - instruments-service/instruments_service/engine/orchestrator.py:1222-1305 (per-day league enumeration)
  - instruments-service/instruments_service/engine/orchestrator.py:1245 (FIXTURES manifest read)
  - plans/active/sports_master_2026_05_07.md (Phase 3 fixture truthset 75% per master)
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md (Phase 3.D.5 expected-universe enumerator)
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Sports per-fixture-anchored cascade — orchestrator currently per-league not per-fixture

> **Severity**: P1 — silent missing-fixture downstream gaps; doesn't block May 23 cutover but compromises
> honest-coverage promise + per-fixture training set completeness. **Blast radius**: instruments-service
> (orchestrator) + manifest expected-universe enumerator + features-sports-service per-fixture aggregations. **Suggested
> owner**: `sports_master_2026_05_07.md` Phase 3 (fold in as a sub-todo of fixture truthset recovery).

## What I found

[orchestrator.py:1222-1305](../../../instruments-service/instruments_service/engine/orchestrator.py#L1222-L1305) —
sports orchestrator determines expected `(league, date)` pairs by reading the FIXTURES manifest index once per date:

```python
# orchestrator.py:1245 — read manifest once to get leagues with FIXTURES on this date
_fix_mask = (_index_df["date"] == date) & (_index_df["data_type"] == "FIXTURES")
captured_leagues = _index_df[_fix_mask]["league_id"].unique()
```

Then it cascades downstream data_types (FIXTURE_STATS, FIXTURE_EVENTS, FIXTURE_LINEUPS, INJURIES, ODDS) **by iterating
per-league-per-day** rather than per-fixture-id. This is correct for league-level data (ODDS day-aggregate, INJURIES
league-roster) but WRONG for fixture-grain data:

- FIXTURE_STATS is PER-FIXTURE (one row of stats per fixture, ~18 columns once flattened).
- FIXTURE_EVENTS is PER-FIXTURE-PER-EVENT.
- FIXTURE_LINEUPS is PER-FIXTURE-PER-PLAYER.
- INJURIES is PER-PLAYER but reported at FIXTURE grain.

Today: on a day where FIXTURES has 12 captured matches in EPL, the orchestrator's FIXTURE_STATS attempt is effectively
"fetch stats for `league=EPL, date=X`" — api_football returns whatever fixtures it has stats for. If it returns 11 of
12, **the missing 12th fixture's missing stats does not produce a manifest row at all**. Coverage % shows "FIXTURE_STATS
captured for league=EPL, date=X" with no indication that 1/12 fixtures were silently dropped.

The expected universe at FIXTURE_STATS grain should be: `(captured FIXTURES rows) × (FIXTURE_STATS data_type)` — not
`(captured leagues × dates)`. Per-fixture missingness is the correctness signal, not per-league missingness.

## Why it matters

- **Silent ML training set bias**: features-sports-service per-fixture aggregations skip fixtures where stats are
  silently missing. Models learn from biased subset.
- **Expected-universe denominator wrong**: writegate Phase 3.D.5 Wave 3 v2 enumerator (which derives expected universe
  from instruments-service catalog × dates × data_types) needs FIXTURES as the per-fixture truthset for downstream
  data_types. If we don't anchor FIXTURE_STATS to FIXTURES at fixture grain, the v2 enumerator can't honestly compute
  coverage %.
- **Cross-instrument analyses break**: e.g. league-level xG aggregations weighted by expected-fixture-count silently
  undercount when FIXTURE_STATS is missing for some fixtures.
- **Reference-source verification**: the `fixtures_postponed_cancelled_lifecycle_2026_05_08.md` issue cross-checks
  fixture STATUS but not fixture-level downstream data presence. Per-fixture cascade is the natural place to catch
  reference-missing-outcome-data (Failure 2 of that issue).

## Recommended decision

Refactor orchestrator's FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES attempt loop to iterate
per-fixture-id, not per-league-per-day:

### Phase 1 — Per-fixture iteration in orchestrator

For each `(league, date)` after FIXTURES capture:

```python
captured_fixtures = read_fixtures_parquet(league, date)  # returns list of fixture_id rows

for fixture_id in captured_fixtures:
    if not should_skip(fixture_id, "FIXTURE_STATS"):
        try:
            stats = adapter.fetch_fixture_stats(fixture_id)
            if stats:
                manifest.record_captured(row_key={..., fixture_id: fixture_id, ...}, parquet=stats_parquet)
            else:
                manifest.record_empty(row_key={..., fixture_id: fixture_id, ...}, reason="SOURCE_RETURNED_ZERO")
        except Exception as exc:
            error = classify_venue_error(exc)
            manifest.record_failed(row_key={..., fixture_id: fixture_id, ...}, error=error)
```

Manifest row_key for FIXTURE_STATS / EVENTS / LINEUPS / INJURIES becomes
`(asset_group, source, data_type, league_id, fixture_id, date)` — fixture_id is a first-class shard axis (not just a
column inside the parquet).

### Phase 2 — Manifest schema migration

- v5 manifest schema already supports `fixture_id` as a column (per CLAUDE.md "Sports per-fixture-bundle data_types
  ODDS_SNAPSHOT / ODDS_MOVEMENT / ARBITRAGE" cluster validation precedent).
- Migrate existing manifest rows: read FIXTURES parquet for each captured `(league, date)`, expand existing
  FIXTURE_STATS rows into per-fixture rows (mark all as `expected_unattempted` since we don't know which specific
  fixtures had stats inside the bundled parquet). Future re-fetch via forward-poll fills them in correctly.

### Phase 3 — Reader-side cluster validation

Add `expected_root_clusters` + `cluster_extractor` kwargs at `record_captured` for bundled FIXTURE_STATS / EVENTS /
LINEUPS bundles per the CLAUDE.md "Cluster validation MANDATORY" rule. The expected cluster set is
`(captured FIXTURES rows for the league/date)`; the extractor reads `fixture_id` from each row. Under-coverage triggers
`ClusterCoverageError` instead of silent partial-bundle.

### Phase 4 — Cross-cut: writegate v2 enumerator integration

- Coordinate with writegate Phase 3.D.5 Wave 3 v2 enumerator: when it walks
  `instruments-service catalog × dates × data_types` to pre-populate `expected_unattempted` rows, sports FIXTURE_STATS /
  EVENTS / LINEUPS / INJURIES expected-universe is `(captured FIXTURES rows) × (data_type)` — not catalog-driven
  (catalog has leagues, not specific fixtures).
- This means the FIXTURES capture itself is the catalog input for downstream sports per-fixture data_types. Document
  this dependency in the Wave 3 plan.

## Acceptance criteria

- [ ] Orchestrator iterates per-fixture-id for FIXTURE_STATS / EVENTS / LINEUPS / INJURIES.
- [ ] Manifest row_key includes `fixture_id` for the four data_types.
- [ ] `record_captured` for bundled fixture-day parquets passes `expected_root_clusters` + `cluster_extractor` per
      cluster validation rule.
- [ ] Migration of existing manifest rows + parquet shape complete; no fallback reader.
- [ ] writegate Phase 3.D.5 Wave 3 v2 enumerator wires sports FIXTURE_STATS / EVENTS / LINEUPS / INJURIES
      expected-universe = captured FIXTURES.
- [ ] Per-fixture coverage % displayed in deployment-ui drilldown for sports per-fixture data_types.

## Open questions

- Does api_football's `/fixtures/statistics?fixture={id}` endpoint exist as a per-fixture lookup, or only as a
  date+league bulk endpoint? If only bulk, per-fixture iteration costs API quota proportional to fixture count — need to
  verify quota budget.
- For ODDS at per-fixture-anchored grain — covered separately in `odds_fixture_anchored_nan_fill_2026_05_08.md`. This
  issue is FIXTURE_STATS / EVENTS / LINEUPS / INJURIES only.
