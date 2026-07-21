---
doc_type: issue
title:
  ODDS_API adapter silently under-fetches — its league iteration scope (tier≤2 PREDICTION leagues with an odds_api_name
  mapping) is narrower than the IS catalog's real fixture set, so real game days can return credits_used=0/rows=0 with
  no error
summary:
  "Found 2026-07-12 while building a fixture-aware SPORTS re-verification for `data_pipeline_e2e_check_2026_07_10.md`
  (todo 26) — re-ran ODDS_API force-legs against a real, PROD-confirmed captured day (2026-06-24, 150,249 total captured
  days for this venue) and still got a clean `rows=0` with `credits_used=0`. Dispatched a focused investigation. Root
  cause, file:line-confirmed: `odds_api_adapter.py::_fetch_all_leagues` (lines 463-502) only iterates
  `DEFAULT_CLASSIFICATION_REGISTRY.get_prediction_leagues()` (`league_registry.py:315-321` — tier<=2 AND
  classification==PREDICTION only), and additionally skips any league missing an `odds_api_name` mapping
  (`odds_api_adapter.py:480-482`). A league with real fixtures in IS's own catalog that day but outside this narrow
  tier/classification/mapping intersection is silently skipped (`logger.debug` only) — the adapter never calls the
  vendor API for it, so there's no error, no partial-failure signal, just `credits_used=0`. This is DIFFERENT from the
  already-documented `sports_league_id_out_of_universe_overcapture_2026_06_24.md` (that doc is about API-Football
  numeric-vs-canonical league_id OVER-capture outside the canonical set; this is ODDS_API UNDER-capture of leagues
  genuinely INSIDE the catalog but outside the adapter's own narrower iteration scope) -- different provider, different
  mechanism, opposite direction."
status: resolved
nature: notes
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [sports, odds_api, intentional-scope, league-registry, smoke-test, data-correctness]
related:
  [
    ../data_pipeline_e2e_check_2026_07_10.md,
    sports_league_id_out_of_universe_overcapture_2026_06_24.md,
    mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
  ]
created: 2026-07-12
parent_epic: sports_master
priority: P2
source: [pipeline_e2e_check SPORTS re-verification, day=2026-06-24 (real PROD-captured day), real VM run.log evidence]
assigned_vm: NA
resolved_by: operator-decision-2026-07-12
locked_by:
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
---

# ODDS_API adapter under-fetches — league iteration scope narrower than the real catalog

## Context

`data_pipeline_e2e_check_2026_07_10.md` todo 26 built a fixture-aware SPORTS re-verification (a single sweep day has no
fixtures for most leagues most days, so a prior full 452-shard sweep's SPORTS results were honest-empty but
uninformative). Queried PROD's real SPORTS availability index directly and picked `2026-06-24` for ODDS_API — a day with
a real, confirmed `capture_status=captured` row (150,249 total captured days for this venue historically, so not a
fluke). Force-refetched `SPORTS:ODDS_API:odds_movement` (and the other 8 declared ODDS_API data_types) against this real
day — all 9 still returned `rows=0`.

## Two distinct findings from the investigation (this doc covers only #2)

**#1 — checker-side, not a production bug**: `download_batch()` (`odds_api_adapter.py:421-461`) accepts a `data_types`
parameter but never reads it — every declared data_type funnels through the identical `_fetch_all_leagues` →
`_discover_fixtures` path, so testing 9 "separate" data_types is testing the same code path 9 times. Several of the
declared data_types (`arbitrage_opportunity`, `odds_snapshot`, `odds_horizon_bucket`, `settlements`) have no independent
MTDS fetch code at all — `odds_horizon_bucket` is explicitly documented as an MDPS-downstream concern (adapter's own
docstring, line 12: "No time_bucket label in raw storage; bucket assignment is MDPS (L2.5) concern"). This is a
shard-enumeration mismatch in the checker's own SPORTS matrix, not a fetch bug — not filed separately, noted here for
completeness.

**#2 — real production bug (this doc)**: the actual fetch returning `rows=0`/`credits_used=0` on a day PROD itself
proves had real captured data.

## Root cause

`market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py:463-502` (`_fetch_all_leagues`):

```python
for league_cls in registry.get_prediction_leagues():
    if credits_exhausted:
        break
    odds_api_key = league_cls.odds_api_name
    if not odds_api_key:
        continue
    ...
    discovered = await self._discover_fixtures(api_key, odds_api_key, date_str)
    if not discovered:
        logger.debug("No fixtures for %s on %s -- skipping", odds_api_key, date_str)
        continue
```

`registry.get_prediction_leagues()`
(`unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_registry.py:315-321`):

```python
def get_prediction_leagues(self) -> list[LeagueClassification]:
    """Return tier 1 and 2 Prediction leagues."""
    return [
        league
        for league in self._leagues.values()
        if league.classification == LeagueClassificationType.PREDICTION and league.tier <= 2
    ]
```

The adapter's real fetch loop only ever considers leagues that are simultaneously (a) tier 1 or 2, (b)
`classification == PREDICTION`, and (c) carry a non-empty `odds_api_name` mapping. Any league with real fixtures that
day in IS's own broader catalog (the source the smoke check's day-picker and the manifest sentinel both read) but
outside this three-way intersection is silently `continue`d past at debug-log level — no warning, no error, no
partial-capture signal. `credits_used=0` in the run.log is the tell: **zero calls to the vendor API were even
attempted** for `2026-06-24`, meaning every fixture the catalog has for that day belongs to a league outside this narrow
scope (plausible for `2026-06-24` — mid-year, many major domestic leagues in their off-season window).

## Why this matters

This isn't a "picked an unlucky day" problem — it means ODDS_API's coverage is silently bounded by whichever leagues
happen to intersect `tier<=2 AND PREDICTION AND odds_api_name-mapped`, and any real, catalog-confirmed fixture outside
that intersection produces a clean, error-free empty result indistinguishable from "genuinely no games that day." The
distinction between "no games" and "games exist but this adapter's scope excludes them" is currently invisible in both
the manifest (sentinel rows look identical either way) and the logs (debug-level only).

## Resolution — operator confirmed intentional

Operator confirmed (2026-07-12): the `tier<=2 AND PREDICTION` scope is the INTENDED full ODDS_API league universe ("~30+
prediction-relevant leagues"), not an accidental narrowing. This is NOT a coverage bug — closing as
`resolved`/working-as-intended, not a fix-needed finding.

The one still-real, smaller observation from the original investigation stands as a minor, non-blocking observability
note (not re-opened as a P2 bug): the debug-level `"No fixtures for %s on %s -- skipping"` log
(`odds_api_adapter.py:89`) makes "no games that day" and "league outside intentional scope" indistinguishable from the
log/manifest alone. If this ever becomes confusing in practice, promoting it to a structured, classified skip reason
(rather than silent debug) would be a cheap follow-up — not tracked as a todo here since it's cosmetic, not a
correctness issue.

## Progress log

- 2026-07-12: Filed from the `data_pipeline_e2e_check_2026_07_10.md` SPORTS fixture-day re-verification. Root cause
  traced to file:line via a real re-fetch against a PROD-confirmed captured day, not guessed from the checker's
  abstracted reason string.
- 2026-07-12: Operator confirmed the league scope is intentional (~30+ prediction leagues) — closed as
  resolved/working-as-intended, no fix needed.
