---
doc_type: issue
title: Sports odds markets/outcomes/settlements/arbitrage_opportunity — expected since 2024-01-01, zero captured ever
summary:
  UAC's `VENUE_DATA_TYPE_CAPABILITIES` still declares `markets`/`outcomes`/`settlements`/`arbitrage_opportunity` as
  capabilities for ODDS_API/PINNACLE/BETFAIR starting 2024-01-01, so `_expected_sports()` in
  `instruments-service/scripts/expected_universe.py` includes them in the honest-coverage denominator today — but the
  manifest has ZERO rows for these 4 data_types on any date since 2020-06-05 (confirmed by a full manifest census
  immediately before purging the unrelated frozen 2018-2020 rows for the same 4 data_types). Either the capability
  declaration is stale (never actually re-enabled) or a real, silent, multi-year capture gap exists for whatever venues
  are supposed to be producing this data.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [sports, data-correctness, honest-coverage, expected-universe, capture-gap]
related:
  [
    /plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md,
    /plans/active/issues/sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md,
  ]
created: 2026-07-24
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
source:
  discovered live while purging the frozen 2018-2020 markets/outcomes/settlements/arbitrage_opportunity manifest rows
  (sports_closeout_batch1_ao_ready-018)
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Sports odds markets/outcomes/settlements/arbitrage_opportunity — live expected-vs-captured gap

## How this was found

While purging the frozen 2018-2020 `markets`/`outcomes`/`settlements`/`arbitrage_opportunity` manifest rows
(`sports_closeout_batch1_ao_ready-018`, see `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 18), a full-manifest
census of `instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` was run to confirm the
frozen population's true scope before deleting anything. That census found:

- All 26,352 rows for these 4 data_types (now purged) were dated 2018-01-01..2020-06-05, 100%
  `capture_status = empty_confirmed`.
- **Zero rows exist for these 4 data_types on ANY date after 2020-06-05** — confirmed on the full, unfiltered manifest
  (not a sample) both before and after the frozen-rows purge.

Separately, `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`'s
`VENUE_DATA_TYPE_CAPABILITIES` still lists, as live capabilities:

```python
"ODDS_API": {..., "arbitrage_opportunity": "2024-01-01", "markets": "2024-01-01",
             "outcomes": "2024-01-01", "settlements": "2024-01-01"},
"PINNACLE": {..., "markets": "2024-01-01", "outcomes": "2024-01-01", "settlements": "2024-01-01"},
"BETFAIR":  {..., "markets": "2024-01-01", "outcomes": "2024-01-01", "settlements": "2024-01-01"},
```

`instruments-service/scripts/expected_universe.py:228-253`'s `_expected_sports()` (the production
`build_expected("sports")` entry point) derives the sports expected universe directly from this capability table — for
every venue in scope, every declared capability becomes an expected `(venue, "odds", data_type)` tuple, from its
declared start date onward. This is independently locked in by the checked-in golden regression
`instruments-service/tests/unit/scripts/goldens/expected_universe/sports.json`, which enumerates exactly these tuples as
part of the current expected sports universe.

**Net: for ~19 months (2024-01-01 to today), these 12 (venue, data_type) tuples are counted as "expected" in the
honest-coverage denominator, with 0 rows ever captured against them.** `measure_honest_coverage.py`'s
`_compute_coverage()` groups the manifest generically by `["venue", "data_type"]` with no MVP read-time gate applied to
`"sports"` (that gate is `cefi`-only per `_MVP_READ_TIME_GATE_AGS`), so nothing filters these tuples out of the live
rollup either — they should be showing up as a coverage gap in the nightly `honest-coverage` output and the
`GET /distinct-values/{asset_group}` dashboard endpoint today, unless something else downstream is silently suppressing
them.

## Why this matters

This is exactly the class of finding CLAUDE.md's data-pipeline-correctness rule calls a "big finding" — a live,
multi-year gap between what the system declares it expects and what it has ever captured, hiding inside the honest-
coverage denominator rather than being visibly broken. Two very different root causes are both plausible and need to be
distinguished before any fix:

1. **Stale capability declaration** — these capabilities were added to UAC (dated 2024-01-01) speculatively or for a
   feature that was never actually wired up on the capture side; if so, the fix is to remove them from
   `VENUE_DATA_TYPE_CAPABILITIES` (or push the date out until they're genuinely live), which shrinks the sports
   expected-universe denominator to match reality.
2. **Real, silent capture failure** — the intent was genuine (build these products from ODDS_API/PINNACLE/BETFAIR), the
   capture path was supposed to run since 2024-01-01, and it never has (or stopped very early and was never caught). If
   so, this is a live, unaddressed data gap that needs its own backfill/fix, not a denominator edit.

Given the closely related, already-diagnosed finding for MDPS's separate `arbitrage_opportunity`/`odds_movement`/
`odds_snapshot` derived products (`sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md` — those are
registered in `CandleAdapterRegistry`/`SOURCE_PRIORITY` but never scheduled by any live Cloud Run job), option 2 looks
more likely: this may be the SAME underlying "declared but never scheduled" pattern recurring at the instruments-
service capture layer, not a coincidence — worth checking whether the same root cause (no live job ever wired to these
data_types) explains both findings at once.

## Recommended decision

1. Determine, per venue, whether any capture code path for `markets`/`outcomes`/`settlements`/`arbitrage_opportunity`
   against ODDS_API/PINNACLE/BETFAIR exists at all (adapter method, CLI operation, scheduled job) — if none exists, this
   settles toward root cause 1 (stale declaration, never implemented).
2. If a capture path exists but was never scheduled/enabled, settle toward root cause 2 and decide: schedule it for
   real, or formally retire the capability (with the operator's sign-off, since retiring changes what "100% coverage"
   means for sports going forward).
3. Whichever way it resolves, fix the mismatch — either implement + schedule real capture, or remove/adjust the UAC
   capability declaration so the expected-universe and the real world agree again.

## Todos

- [ ] [DIAG] P1. For each of ODDS_API/PINNACLE/BETFAIR, determine whether ANY capture code path exists for
      `markets`/`outcomes`/`settlements`/`arbitrage_opportunity` (repo: instruments-service, market-tick-data-service).
      **Done when**: a written conclusion states, per venue and data_type, whether a capture path exists and if so
      whether it is currently scheduled/enabled.
- [ ] [DECISION] P1. Based on the above, decide: implement + schedule real capture for these 12 (venue, data_type)
      tuples, or retire the capability declaration (operator sign-off required — changes the sports coverage
      denominator). **Done when**: an explicit decision is recorded with rationale.
- [ ] [CODE] P2. Execute the decided fix — either wire up + schedule real capture, or remove/adjust
      `VENUE_DATA_TYPE_CAPABILITIES` for these tuples (repo: unified-api-contracts and/or instruments-service /
      market-tick-data-service depending on the decision). **Done when**: the expected-universe golden regression
      (`tests/unit/scripts/goldens/expected_universe/sports.json`) is updated to match the new reality and the
      honest-coverage denominator reflects it.
