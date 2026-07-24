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

- [x] [DIAG] P1. For each of ODDS_API/PINNACLE/BETFAIR, determine whether ANY capture code path exists for
      `markets`/`outcomes`/`settlements`/`arbitrage_opportunity` (repo: instruments-service, market-tick-data-service).
      **Done when**: a written conclusion states, per venue and data_type, whether a capture path exists and if so
      whether it is currently scheduled/enabled. — **RESOLVED, corroborated by TWO independent investigations (slot 12
      then slot 5, 2026-07-24): root cause is (1), stale declaration — no capture code exists for any of the 12 (venue,
      data_type) tuples.** | Venue | data_type | Verdict | |---|---|---| | ODDS_API |
      markets/outcomes/settlements/arbitrage_opportunity | NO capture code, ever — UAC `venue_adapter_keys.py:195`
      `"ODDS_API": NO_ADAPTER_YET`; MTDS's only sports write path (`venue_fetch.py::_process_sports_venue_with_leagues`)
      hardcodes `data_type=TRADES`; the manifest-facing adapter (`odds_api_adapter.py:761`) only ever stamps
      `data_type="ODDS"` — structurally cannot emit these 4 | | PINNACLE |
      markets/outcomes/settlements/arbitrage_opportunity | NO capture code, ever — **no dedicated Pinnacle adapter file
      exists anywhere in market-tick-data-service** (Pinnacle is one bookmaker string inside ODDS_API's fan-out,
      `REQUESTED_ODDS_API_BOOKMAKERS`); UAC doesn't even declare `arbitrage_opportunity` for PINNACLE | | BETFAIR |
      markets/outcomes/settlements/arbitrage_opportunity | NO writer ever stamps these — a real
      `BetfairReferenceDataAdapter` (instruments-service) exists but is `BLOCKED-CREDENTIALS`, zero prod rows ever, and
      even if unblocked produces instrument-catalogue data (`InstrumentRecord`s), not a `data_type=` manifest stamp for
      these 4; `venue_fetch.py:85`'s `_VENUE_TO_DATA_SOURCE` doesn't recognize bare `BETFAIR` at all — real Betfair
      capture happens under sub-venue names `BETFAIR_SB_UK`/`BETFAIR_EX_UK`/`BETFAIR_EX_EU`, none of which are declared
      either | Full evidence chain: adapter registries, the hardcoded `TRADES` write path, git history showing a real
      Pinnacle/OddsApi adapter existed 2026-03-27→2026-04-11 and was deleted as dead code with no
      `get_outcomes`/`get_settlements`/`get_arbitrage` method ever written even then, the disconnected
      `configs/venue_data_types.yaml` aspirational declaration with zero runtime readers, a SECOND authoritative
      registry (`expected_coverage.py`'s `_SPORTS` table) that never declared these 4 data_types either, the UAC
      capability entries' own git provenance (`unified-api-contracts@7511207a`, a broad mechanical cross-asset-group
      registry sweep with zero corresponding adapter changes), and the matching MDPS-side "declared but never scheduled"
      pattern in `sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md`. Start points for a fresh
      re-derivation: `unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py:189-201`
      (`NO_ADAPTER_YET` for ODDS_API/PINNACLE),
      `market-tick-data-service/.../venue_fetch.py::_process_sports_venue_with_leagues` (hardcoded `data_type=TRADES`),
      and `unified_api_contracts/registry/expected_coverage.py:458-466` (`_SPORTS`).
- [x] [DECISION] P1. Based on the above, decide: implement + schedule real capture for these 12 (venue, data_type)
      tuples, or retire the capability declaration (operator sign-off required — changes the sports coverage
      denominator). **Done when**: an explicit decision is recorded with rationale. ✅ — recommendation recorded below;
      operator sign-off requested via /blocked (slot 5, 2026-07-24).
- [ ] [CODE] P2. Execute the decided fix — either wire up + schedule real capture, or retire/adjust
      `VENUE_DATA_TYPE_CAPABILITIES` for these tuples (repo: unified-api-contracts and/or instruments-service /
      market-tick-data-service depending on the decision). **Done when**: the expected-universe golden regression
      (`tests/unit/scripts/goldens/expected_universe/sports.json`) is updated to match the new reality and the
      honest-coverage denominator reflects it. **Gated on operator sign-off of the recommended decision below.**

### DIAG findings (2026-07-24, slot 5) — corroborating a second, independent investigation

Followed up on slot 12's open question — grepped both repos specifically for `markets`/`outcomes`/`settlements`/
`arbitrage_opportunity` as `data_type=`/`DataType.` enum-member usages (not JSON-key usages). **No real capture code
path exists for any of the 12 tuples** — this settles root cause 1 (stale/never-implemented declaration), not root cause
2 (built-but-unscheduled):

- **Adapters only ever stamp `data_type="ODDS"`.** Confirmed: `odds_api_adapter.py:761` and the Betfair adapter's
  equivalent write site are the ONLY manifest `record_captured(data_type=...)` calls in either repo for these venues.
  The `markets`/`outcomes` string hits are exclusively raw-API-response JSON keys (`market.outcomes`, `bm.markets`),
  never a `data_type=` literal — settling slot 12's open question directly.
- **No PINNACLE adapter file exists anywhere in market-tick-data-service** (`find -iname '*pinnacle*'` empty). Confirms
  slot 12's suspicion: PINNACLE is not a separate venue integration, just a bookmaker key nested inside ODDS_API's
  response — so a standalone `"PINNACLE"` capability entry is itself part of the stale declaration.
- **Venue dispatch tables don't recognize bare `BETFAIR`/`PINNACLE`.** `venue_fetch.py:85` (`_VENUE_TO_DATA_SOURCE`) has
  only `"ODDS_API": "odds_api"`; real Betfair capture happens under sub-venue names
  `BETFAIR_SB_UK`/`BETFAIR_EX_UK`/`BETFAIR_EX_EU`, which `VENUE_DATA_TYPE_CAPABILITIES` doesn't declare either.
  `settlements`/`arbitrage_opportunity` have zero adapter methods, zero dispatch wiring, zero CLI operations anywhere in
  either repo.
- **A second, authoritative registry already disagrees with `VENUE_DATA_TYPE_CAPABILITIES` and excludes these 4
  data_types.** `unified_api_contracts/registry/expected_coverage.py:458-466` (`_SPORTS`, feeds
  `EXPECTED_COVERAGE_BY_ASSET_GROUP`) declares only `ODDS_API: ["ODDS"]`, `PINNACLE: ["trades"]`,
  `BETFAIR_SB_UK/EX_UK/EX_EU: ["trades"]` — none of the 4 data_types in question. `VENUE_DATA_TYPE_CAPABILITIES` is a
  separate, broader table that `expected_universe.py`'s `_expected_sports()` reads from directly (bypassing
  `expected_coverage.py`), which is exactly why this gap wasn't caught by the other registry.
- **Git provenance confirms mechanical, non-deliberate origin.** `markets`/`outcomes`/`settlements` for all 3 venues
  were added in `unified-api-contracts@7511207a` (2026-05-23, `semver-rollout[bot]`, "canonicalize DeFi/prediction/
  tradfi data type names + add missing types") — a broad cross-asset-group registry sweep with generic placeholder
  comments ("Market metadata", "Outcome results", "Settlement records — pass-through") and zero corresponding
  adapter/CLI changes in the same commit. `arbitrage_opportunity` for ODDS_API predates that (`@1a05a8724`, 2026-04-12,
  "add league fixture calendar and prediction league ID helpers") — also unrelated to any adapter work.
- **Not a silent-empty-dispatch bug**: when an adapter is called for an unsupported data_type it raises
  `NotImplementedError`, which `orchestrator/__init__.py:875-880` explicitly treats as "a capability signal, not a
  failure" — never becomes `attempted_failed`. Consistent with zero manifest rows AND zero error rows, i.e. these
  capture paths are never invoked at all, not invoked-and-failing.

### DECISION (recommended, pending operator sign-off — 2026-07-24, slot 5)

**Recommendation: retire the capability declaration** — remove the `markets`/`outcomes`/`settlements`/
`arbitrage_opportunity` entries for ODDS_API/PINNACLE/BETFAIR from `VENUE_DATA_TYPE_CAPABILITIES`
(`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`) rather than building real capture.

**Rationale**:

1. This is a stale/mechanical declaration (DIAG finding above), not a deliberately-built-then-abandoned feature — there
   is no adapter code, no CLI path, no dispatch wiring, and (for PINNACLE) no adapter file at all to "re-enable."
   Implementing real capture from scratch means net-new PINNACLE adapter work, new markets/results/ settlement endpoint
   integrations on 3 venues, and — for `arbitrage_opportunity` specifically — building a cross-bookmaker
   margin-comparison engine that doesn't exist anywhere in the codebase today (`brand-new` estimate class, likely
   multi-day, not a P2-sized fix).
2. `expected_coverage.py`'s `_SPORTS` table — the OTHER, arguably more-authoritative expected-coverage registry — was
   never updated to include these tuples, meaning even the workspace's own registries disagree about whether this
   capability is real. Retiring `VENUE_DATA_TYPE_CAPABILITIES` brings the two registries back into agreement rather than
   requiring `expected_coverage.py` to be extended to match a declaration nothing implements.
3. This directly parallels the sibling MDPS finding
   (`sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md`, RESOLVED) — `odds_movement`/`odds_snapshot`/
   `arbitrage_opportunity` candle adapters were registered but never scheduled, root-caused as dead/aspirational
   registration rather than a live bug. Same pattern here, one layer up the stack (raw capture vs. derived candles).
4. Retiring is the lower-risk fix: it makes the honest-coverage denominator match the system's actual current
   capabilities immediately, with no new capture surface to build, test, and operate. If real sports markets/outcomes/
   settlements/arbitrage products become a genuine product priority later, that is a fresh, deliberately-scoped
   `brand-new` feature effort (new plan), not a "restore what was there" fix — because nothing usable was ever there.
5. Confidence is high: slot 12 and slot 5 investigated independently (different starting points —
   `venue_adapter_keys.py` +git-history vs. `expected_coverage.py`+`data_type=` literal grep) and converged on the
   identical root cause and the identical retire recommendation.

**Why sign-off is still required before execution** (per this issue's own todo 2 note): retiring shrinks the sports
honest-coverage denominator, which changes what "100% coverage" reports for sports going forward — an operator-visible
metric change, not a pure implementation detail. Posted as a `/blocked` question (slot 5, 2026-07-24) requesting
confirmation to proceed with retirement; todo 3 (CODE) is gated on that answer.
