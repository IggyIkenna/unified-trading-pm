---
doc_type: plan
title: Venue capability matrix route/mode axis + cross-AG venue declarations
summary: |
  Cross-AG registry foundation. Adds a route axis (aggregator/broker/direct) and a mode axis (batch/live) to
  VENUE_DATA_TYPE_CAPABILITIES so an aggregator-served venue reads as a venue WITH an adapter, folds in the
  VENUE_DATA_TYPE_NO_BATCH_SOURCE one-way patch, declares the 40 venues across cefi/defi/sports that capture today but
  carry no capability entry, resolves the four-way bookmaker spelling drift, and expands the sports venue universe with
  Unity's 10 child books plus the priority-14 arb books that are absent from the data axis.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, deployment-api]
scope: [engineer]
tags: [sports, venue-registry, capability-matrix, batch-live, arb, odds, canonicalisation]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
    /codex/02-venues/unity-integration.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /plans/active/sports_taxonomy_p2_consumer_inventory_2026_08_12.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
assigned_role: data_engineering
effort: xhigh
drift_direction: advance-code
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py,
    unified-api-contracts/unified_api_contracts/registry/_odds_api_maps.py,
    unified-api-contracts/unified_api_contracts/registry/sports_bookmaker_league_coverage.py,
    unified-api-contracts/unified_api_contracts/internal/unity_child_books.py,
    /codex/02-venues/unity-integration.md,
    e2e-testing/docs/sports/LIVE_ODDS_PROVIDERS.md,
  ]
depends_on:
supersedes:
superseded_by:
locked_by:
locked_since:
source: Batch-vs-live venue parity audit, 2026-08-14 interactive session
---

# Venue capability matrix route/mode axis + cross-AG venue declarations

> **Track**: LOCAL / human plan (`assigned_vm: NA`). Intended to be handed to a Sonnet-5 worker and audited on
> completion. Not AO-ingested.

## Why this plan exists

A batch-vs-live venue parity audit (2026-08-14) measured the registries against prod manifest reality and found the
capability matrix cannot express what the system actually does.

**Measured facts this plan is built on** (re-verify before trusting; each was measured on 2026-08-14):

| Fact                                                                           | Measurement                                                    |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| Venues in `VENUES_BY_ASSET_GROUP` with NO `VENUE_DATA_TYPE_CAPABILITIES` entry | 40 — cefi 2, defi 7, sports 31                                 |
| Of those 40, how many have real prod manifest rows                             | 36 (only `BETOPENLY` / `NOVIG` / `ONEXBET` / `PROPHETX` empty) |
| Sports manifest rows for those "undeclared" venues                             | 5,587,089                                                      |
| Sports venues resolving a real adapter key in `VENUE_TO_ADAPTER_KEY`           | 0 of 31 — every one is `NO_ADAPTER_YET`                        |
| `VENUE_DATA_TYPE_CAPABILITIES` sports entries                                  | 0                                                              |
| Mode axis (batch vs live) anywhere in the capability matrix                    | none — only the 3-venue `VENUE_DATA_TYPE_NO_BATCH_SOURCE` list |

The consequence: a bookmaker priced through an aggregator reads as adapter-less and capability-less, so every consumer
that derives its expected universe from these dicts is blind to 5.6M captured rows. **Operator ruling 2026-08-14: a book
served through the Odds API, SharpAPI or Unity still counts as a venue WITH an adapter — the aggregator IS the
adapter.**

## Codex SSOTs this plan must not contradict

- `/codex/04-architecture/instrument-universe-registry-consolidation.md` — UAC owns which adapter key serves each venue;
  instruments-service owns key→class. `NO_ADAPTER_YET` means "declared adapterless", not "someone forgot".
- `/codex/02-data/availability-manifest-and-data-status.md` — shard atom must stay identical across
  writer/manifest/status/gate/UI.
- `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` — renaming a venue must migrate EVERY consumer in
  the same change; a token grep misses path-prefix / filename / registry-membership binders.
- `/codex/02-venues/unity-integration.md` — Unity is a META_BROKER with 10 child books, single TCP connection, Java Feed
  Connector sidecar.
- `/codex/02-data/sports-2020-06-data-floor.md` — odds start 2020-06-06; no capability start_date may precede it.

## Design — the route/mode axis

Today: `VENUE_DATA_TYPE_CAPABILITIES: dict[venue, dict[data_type, start_date_str]]`.

Target: the value becomes a typed record carrying route and per-mode availability. Shape to implement (exact field names
are the implementer's call, but every one of these facts must be expressible):

- `route` — how the price reaches us: `direct` (we hold the venue's own socket/REST), `aggregator:<SOURCE>` (ODDS_API,
  SHARPAPI, ODDS_API_IO), or `broker:<SOURCE>` (UNITY). This is the field that makes an aggregator-served book resolve
  as adapter-backed.
- `batch` — the historical leg: a start date, or an explicit "no batch source" marker. The 3 entries currently in
  `VENUE_DATA_TYPE_NO_BATCH_SOURCE` (`ASTER`, `EXTENDED-STARKNET`, `LIGHTER-ZKSYNC`) become `batch = none` and that dict
  is deleted, not left as a parallel truth.
- `live` — the realtime leg: `none` / `wired` (a connector exists) / `deployed` (a live capture process is actually
  running for it). The audit needed three separate sources plus a prod manifest read to answer this; it must become one
  lookup.

Backwards compatibility is NOT a goal — delete the old shape, migrate every consumer in the same change per the
entity-rename rule. `@contract-surface` annotations on both dicts mean the AST breaking-change differ will flag this;
that is expected and correct, not something to work around.

## Todos

### P0 — schema

- [ ] [DATA] P0. Enumerate every consumer of `VENUE_DATA_TYPE_CAPABILITIES` and `VENUE_DATA_TYPE_NO_BATCH_SOURCE` across
      all repos before changing either — DoD: a written consumer list in this plan's Progress Log naming file + symbol
      for each, cross-checked with `rg` over every repo including UI/TS surfaces, not just Python.
- [ ] [DATA] P0. Define the typed capability record (route + batch + live axes per the Design section) in
      `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py` or a new sibling module, with the
      `@contract-surface` annotation carried over — DoD: type-checks clean under strict basedpyright and every field in
      the Design section is representable.
- [ ] [DATA] P0. Migrate all existing `VENUE_DATA_TYPE_CAPABILITIES` entries to the new record with `route=direct` and
      the current start_date as the batch leg, preserving every start date exactly — DoD: a test asserts the
      pre-migration `(venue, data_type) -> start_date` pairs are recoverable one-for-one from the new structure.
- [ ] [DATA] P0. Fold `VENUE_DATA_TYPE_NO_BATCH_SOURCE`'s 3 venues into the new record as `batch = none` and DELETE the
      dict plus every import of it — DoD: `rg VENUE_DATA_TYPE_NO_BATCH_SOURCE` returns zero hits fleet-wide and the
      affected venues' live-only data_types still resolve.
- [ ] [DATA] P0. Migrate every consumer found by the first todo to the new shape in the SAME change — DoD: every repo
      touched is `quality-gates.sh`-green and no consumer reads a removed symbol.

### P1 — declare what already captures

- [ ] [DATA] P1. Add capability entries for the 7 defi venues that capture but are undeclared (`AAVE-PLASMA`,
      `BINANCE-BSC`, `BINANCE-ETHEREUM`, `COINBASE-ETHEREUM`, `FLUID-PLASMA`, `SANCTUM-SOLANA`, `SOLANA-NATIVE-SOLANA`),
      route=direct — DoD: start dates derived from each venue's earliest `captured` manifest row, not invented; cite the
      query.
- [ ] [DATA] P1. Add capability entries for `KALSHI-PERP` and `POLYMARKET-PERP` `perp_funding` (batch route=direct via
      `perp_funding_handler.py`) — DoD: entries match the venues' real captured `perp_funding` first dates, and no
      phantom EXPECTED cell is seeded for the data_types those venues only ever `empty_confirmed`.
- [ ] [DATA] P1. Add capability entries for all 31 existing sports bookmaker venues with `route=aggregator:ODDS_API` and
      the batch start date each venue's manifest actually shows, clamped to the 2020-06-06 floor — DoD: no entry
      predates the floor, and the four never-captured books get `batch = none` rather than a fabricated date.
- [ ] [DATA] P1. Replace `NO_ADAPTER_YET` for the 31 sports venues with resolution through the route axis so an
      aggregator-served venue is adapter-backed, keeping `is_venue_executable()` as the SEPARATE execution-capability
      predicate it already documents itself to be — DoD: `is_venue_executable("PINNACLE")` stays False while the venue
      resolves a data-side route; the existing `test_venue_adapter_keys.py` assertions stay green or are updated with a
      stated reason.

### P1 — resolve the bookmaker spelling drift

- [ ] [DATA] P1. Document the current four-way bookmaker spelling split before changing anything —
      `VENUES_BY_ASSET_GROUP` uses `LADBROKES`/`BET888SPORT`, `REQUESTED_ODDS_API_BOOKMAKERS` +
      `BOOKMAKER_LEAGUE_COVERAGE` use `ladbrokes_uk`/`sport888`, `AUDITED_BOOKMAKERS` uses unsuffixed
      `BETFAIR_EX`/`BETFAIR_SB` — DoD: a mapping table in the Progress Log covering every book in any of the four lists.
- [ ] [DATA] P1. Pick ONE canonical spelling per book and migrate the other three registries plus every consumer to it,
      per the entity-rename-and-split rule — DoD: manifest venue values, request keys, coverage-JSON keys and
      audited-bookmaker keys all resolve through a single canonical token; state explicitly whether historical manifest
      rows are being re-keyed or an alias map is retained, and why.
- [ ] [OPERATOR] P1. If the chosen canonicalisation implies re-keying historical sports manifest rows, gate that on the
      delete-safety protocol — cite `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` and get explicit
      approval before any manifest mutation. An alias-map-only resolution needs no gate; state which path was taken.

### P2 — expand the universe

- [ ] [DATA] P2. Register Unity's 10 child books as canonical sports venues from the UAC SSOT
      `unified_api_contracts/internal/unity_child_books.py` (`3ET`, `BETFAIR`, `BROKER5`, `CROWN`, `MATCHBOOK`, `SBO`,
      `SHARPBET`, `VX`, `BETDEX`, `IBC`), reusing the existing `BETFAIR`/`MATCHBOOK` venue tokens rather than minting
      Unity-specific duplicates — DoD: 8 net-new venues registered, and a test asserts the venue set is derived FROM
      `UNITY_CHILD_BOOKS` so adding a child book is a data change, not a code change.
- [ ] [DATA] P2. Give the Unity books capability entries with `route=broker:UNITY`, `batch = none`, `live = none` (flips
      to `wired` in the MTDS plan) — DoD: no batch backfill is implied for any Unity book; operator ruling 2026-08-14 is
      that no history is needed beyond what Odds API already captures.
- [ ] [DATA] P2. Register the priority-14 arb books absent from the data axis, sourced from
      `e2e-testing/docs/sports/LIVE_ODDS_PROVIDERS.md`'s coverage matrix — KTO, Betano, SharpBet, Dafabet, BetPlay,
      Cloudbet, Bet365, SingBet, Stake — with `route=aggregator:SHARPAPI` or `aggregator:ODDS_API_IO` per that doc's
      per-book availability column — DoD: each registered book cites which provider serves it; a book no provider serves
      is NOT registered.
- [ ] [DATA] P2. Re-confirm the provider availability columns in `LIVE_ODDS_PROVIDERS.md` before relying on them — that
      doc's status column is stale (it cites an odds-api.io trial expiring 2026-04-03 and a results section dated
      2026-04-01) — DoD: each provider's current subscription state is verified against the live account or Secret
      Manager entry and the doc is corrected in the same change.
- [ ] [DATA] P2. Wire `NOVIG` / `PROPHETX` / `ONEXBET` to `route=aggregator:SHARPAPI` — all three are on SharpAPI's
      active 31-book list yet have zero manifest rows, so this is a routing fix, not a build — DoD: each resolves a
      route; actual capture is proven by the MTDS plan, not this one.
- [ ] [DATA] P2. Leave `BETOPENLY` explicitly `batch = none, live = none` with an inline reason if no provider serves it
      — DoD: the venue is honestly declared rather than silently absent, per the honest-absence rule.

### P2 — guard the invariant

- [ ] [DATA] P2. Add a drift-guard test asserting every venue in `VENUES_BY_ASSET_GROUP` has a capability record, and
      every capability record's venue is declared — DoD: the test fails if either side gains an unmatched entry; the
      four genuinely-unserved books pass via an explicit `none` route, not an allowlist.
- [ ] [DATA] P2. Extend the UAC parity gate `tests/unit/test_venue_source_adapter_parity.py` to cover the route axis so
      a venue whose route names a provider we do not actually subscribe to fails — DoD: a deliberately-broken fixture (a
      venue routed to an unsubscribed provider) RED-fails, proving the gate bites.
- [ ] [REVIEW] P2. Re-run the parity measurement that produced this plan's fact table and confirm the 40-undeclared
      count is now 0 — DoD: cite the re-run output in the Progress Log.

## Definition of done for the whole plan

Every venue in `VENUES_BY_ASSET_GROUP` resolves a capability record naming its route and its batch/live availability;
`VENUE_DATA_TYPE_NO_BATCH_SOURCE` is gone; the four bookmaker spelling registries agree; Unity's child books and the
priority-14 absentees are on the data axis; and the drift guards fail if any of that regresses.

## Progress Log

_(append dated entries here; extract fully-closed sections once this file passes ~500 lines)_
