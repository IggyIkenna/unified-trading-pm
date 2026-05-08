---
title: "ODDS not FIXTURES-anchored — no NaN-fill for missing (fixture, bookmaker, market_type) triples"
created: 2026-05-08
author: ikenna
source:
  - instruments-service/instruments_service/engine/orchestrator.py:4768 (_fetch_footystats_odds day-level call)
  - unified-api-contracts/unified_api_contracts/canonical/domain/sports/_sports_prediction_contracts.py:198-287
    (SPORTS_ODDS_SNAPSHOT contract)
  - plans/active/sports_master_2026_05_07.md (sports_predictions_e2e folded in)
  - CLAUDE.md "Four-category empty-output decision" category D — zero-activity bars precedent for "tradeable but
    illiquid"
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# ODDS fixture-anchored NaN-fill — apply zero-volume-bar precedent to expected (fixture × bookmaker × market) triples

> **Severity**: P1 — silent missing-bookmaker / missing-market gaps in ODDS; doesn't block May 23 cutover but
> compromises arbitrage / odds-movement features that depend on full bookmaker coverage per fixture. **Blast radius**:
> instruments-service (orchestrator + odds_api adapter) + UAC (expected bookmaker × market sets per league tier) +
> features-sports-service odds calculators + market-tick-data-service `SportsBucketAssignmentAdapter`. **Suggested
> owner**: `sports_master_2026_05_07.md` Phase 3 (sports_predictions_e2e half) OR new sub-plan.

## What I found

[orchestrator.py:4768](../../../instruments-service/instruments_service/engine/orchestrator.py#L4768) —
`_fetch_footystats_odds(date)` is a day-level endpoint:

```python
odds_rows = await adapter.get_fixture_odds_snapshot(date)  # returns odds for ALL fixtures on date
```

It calls a day-level endpoint that returns whatever odds the source has for the day; the adapter internally handles
per-fixture bucketing. There is **no logic that says**: "for each captured FIXTURES row × each expected bookmaker × each
expected market_type, ensure we have a row; NaN-fill the odds if the source returned nothing for that triple."

[\_sports_prediction_contracts.py:198-287](../../../unified-api-contracts/unified_api_contracts/canonical/domain/sports/_sports_prediction_contracts.py#L198-L287)
— SPORTS_ODDS_SNAPSHOT contract has
`instrument_id, venue, ts_event, league_id, fixture_id, market_type, outcome, odds_decimal, bookmaker, traded_volume, max_bet`.
Contract supports per-(fixture, bookmaker, market) row but write path is whatever the source returns, not what we
expect.

The MDPS `SportsBucketAssignmentAdapter` (referenced in `sports_predictions_e2e` plan, currently 75% per
`sports_master`) handles downstream bucketing but doesn't write back into the manifest at instruments-service grain. So
a fixture × bookmaker × market triple that was expected but not returned by odds_api → no row at all, no manifest entry,
no signal to downstream.

This contradicts the CLAUDE.md "Four-category empty-output decision" category D precedent: when an instrument is alive
(here: fixture is captured + bookmaker offers this market for this league tier) and source returned zero (here: odds_api
didn't return the triple), we should write a NaN-odds row with `record_captured`, NOT skip. Same way zero-volume bars
are written for tradeable-but-illiquid instrument-periods.

## Why it matters

- **Arbitrage detection breaks**: `SPORTS_ODDS_ARBITRAGE` (cross-bookmaker mispricings,
  [\_sports_prediction_contracts.py:262-287](../../../unified-api-contracts/unified_api_contracts/canonical/domain/sports/_sports_prediction_contracts.py#L262-L287))
  needs full bookmaker coverage per fixture-market. Silent missing rows mean we can't compute the leg_a / leg_b spread
  when one leg is silently absent.
- **Odds-movement tracking breaks**: `SPORTS_ODDS_MOVEMENT` requires `odds_before` and `odds_after` snapshots. If a
  snapshot is silently missing (bookmaker offered odds at T1 but odds_api didn't return at T2), we miss the movement.
- **Features bias**: ML features that aggregate across bookmakers (consensus odds, dispersion, market efficiency)
  silently undercount.
- **Coverage % wrong**: deployment-ui shows ODDS at 92% (93807/101618) but the 92% is at fixture-day grain, not (fixture
  × bookmaker × market) grain. True coverage at the trading-relevant grain is unknown.
- **`Live = batch` violation**: live mode would naturally see "bookmaker X stopped offering market Y for fixture Z" as a
  real signal (their market closed); batch silently drops it.

## Recommended decision

Apply the FIXTURES-anchored + zero-volume-bar precedent to ODDS:

### Phase 1 — Per-league expected bookmaker × market_type SSOT

New UAC SSOT: `unified_api_contracts.canonical.domain.sports.expected_bookmaker_market_sets`

```python
# Per-league-tier expected sets — what bookmakers are expected to offer what market_types
EXPECTED_BOOKMAKER_MARKET_SETS: dict[str, dict[str, list[MarketType]]] = {
    "tier_1_premier_leagues": {  # EPL, La Liga, Bundesliga, Serie A, Ligue 1
        "pinnacle": [MATCH_RESULT, OVER_UNDER, BTTS, ASIAN_HANDICAP, ...],
        "bet365": [MATCH_RESULT, OVER_UNDER, BTTS, ASIAN_HANDICAP, ...],
        "betfair": [MATCH_RESULT, OVER_UNDER, ...],  # exchange — different market shape
        ...
    },
    "tier_2_european_leagues": {...},
    "tier_3_lower_leagues": {...},
}
```

Empirical input: 30-day rolling audit of "which bookmakers actually returned odds for which market_types per league
tier." Floor below median frequency = expected; above = optional (don't NaN-fill).

### Phase 2 — Per-fixture × bookmaker × market enumeration at orchestrator commit

After odds_api capture for `(date)`:

```python
captured_fixtures = read_fixtures_parquet(date)  # all leagues
for fixture in captured_fixtures:
    league_tier = get_league_tier(fixture.league_id)
    expected = EXPECTED_BOOKMAKER_MARKET_SETS[league_tier]
    for bookmaker, market_types in expected.items():
        for market_type in market_types:
            row = lookup_in_returned_odds(fixture.fixture_id, bookmaker, market_type)
            if row:
                write_odds_row(row)  # captured normally
            else:
                write_odds_row(
                    fixture_id=fixture.fixture_id,
                    bookmaker=bookmaker,
                    market_type=market_type,
                    odds_decimal=NaN,  # NaN means "expected but source returned nothing"
                    ts_event=fixture.kickoff_utc,
                    available_at=odds_api_poll_completed_at,
                )
```

### Phase 3 — Cluster validation at write-gate

Apply CLAUDE.md "Cluster validation MANDATORY at `record_captured` for bundled shards" rule. ODDS becomes a bundled
data_type with cluster_extractor = `f"{bookmaker}:{market_type}"`. `expected_root_clusters` per league tier from Phase 1
SSOT. Under-coverage triggers `ClusterCoverageError` and `record_failed(reason=ODDS_CLUSTER_UNDER_COVERAGE)` instead of
silent partial-bundle.

### Phase 4 — Downstream consumer guidance

- Arbitrage / odds-movement calculators read NaN-odds rows as "expected-but-missing" signal (skip the leg in arbitrage
  spread computation; skip the movement delta).
- features-sports-service odds-aggregation calculators distinguish NaN (expected-but-missing) from row-not-present
  (truly outside expected universe).
- deployment-ui ODDS coverage panel rolls up at (fixture × bookmaker × market) grain, not just fixture-day.

## Acceptance criteria

- [ ] `EXPECTED_BOOKMAKER_MARKET_SETS` SSOT shipped in UAC with empirical audit for tier-1 leagues at minimum.
- [ ] Orchestrator enumerates expected (fixture × bookmaker × market) triples post-FIXTURES-capture.
- [ ] Missing triples written with `odds_decimal=NaN` + `available_at=poll_completed_at`.
- [ ] Cluster validation kwargs passed at `record_captured` for ODDS_SNAPSHOT bundled writes.
- [ ] Coverage % at (fixture × bookmaker × market) grain rendered in deployment-ui.
- [ ] Arbitrage + odds-movement calculators handle NaN-odds rows correctly.
- [ ] `Live = batch` invariant: live ODDS capture produces same NaN-fill shape for missing triples.

## Open questions

- Does odds_api's API expose "this bookmaker stopped offering this market for this fixture" as a typed signal, or just
  "no row returned"? If typed: differentiate market-closed (legitimate) from API-miss (data quality).
- Is the EXPECTED_BOOKMAKER_MARKET_SETS audit better done from MDPS bucketed parquets (where every odds row is grouped)
  than from instruments-service raw odds_api response? Operator decision — likely both (instruments-service for "what
  odds_api returns," MDPS for "what bucketing yields").
- For Betfair (exchange) vs traditional bookmakers (Pinnacle / bet365), the market shape is different — `traded_volume`
  only on Betfair, `max_bet` only on Pinnacle. Does NaN-fill use the per-bookmaker contract subset, or one unified shape
  with NULLs for non-applicable columns?
