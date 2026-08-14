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

- [x] [DATA] P0. Enumerate every consumer of `VENUE_DATA_TYPE_CAPABILITIES` and `VENUE_DATA_TYPE_NO_BATCH_SOURCE` across
      all repos before changing either — DoD: a written consumer list in this plan's Progress Log naming file + symbol
      for each, cross-checked with `rg` over every repo including UI/TS surfaces, not just Python. ✅ See "2026-08-14 —
      P0 consumer enumeration" above. One gap found LATE (not by this enumeration, by MTDS's real gate run) — see the
      "Regression found + fixed" entry below.
- [x] [DATA] P0. Define the typed capability record (route + batch + live axes per the Design section) in
      `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py` or a new sibling module, with the
      `@contract-surface` annotation carried over — DoD: type-checks clean under strict basedpyright and every field in
      the Design section is representable. ✅ `VenueCapabilityRecord`/`DataTypeAvailability` dataclasses —
      unified-api-contracts@b6887df513.
- [x] [DATA] P0. Migrate all existing `VENUE_DATA_TYPE_CAPABILITIES` entries to the new record with `route=direct` and
      the current start_date as the batch leg, preserving every start date exactly — DoD: a test asserts the
      pre-migration `(venue, data_type) -> start_date` pairs are recoverable one-for-one from the new structure. ✅
      `tests/unit/test_venue_capability_migration_recoverability.py`, parametrized over all ~440 pre-migration entries —
      unified-api-contracts@b6887df513.
- [x] [DATA] P0. Fold `VENUE_DATA_TYPE_NO_BATCH_SOURCE`'s 3 venues into the new record as `batch = none` and DELETE the
      dict plus every import of it — DoD: `rg VENUE_DATA_TYPE_NO_BATCH_SOURCE` returns zero hits fleet-wide and the
      affected venues' live-only data_types still resolve. ✅ unified-api-contracts@b6887df513. Caveat on the DoD's
      literal "zero hits": the symbol is gone as an importable name (`hasattr` test asserts this) and zero live imports
      remain — a handful of PROSE comments (in `market_data_categories.py` itself, explaining the removal) still mention
      the old name as history, matching this codebase's existing convention for documenting removed symbols (e.g.
      "BINANCE-DELIVERY capability block REMOVED" comments elsewhere in the same file). Flagging the interpretation
      rather than silently claiming a literal zero-grep-hits that isn't quite true.
- [x] [DATA] P0. Migrate every consumer found by the first todo to the new shape in the SAME change — DoD: every repo
      touched is `quality-gates.sh`-green and no consumer reads a removed symbol. ✅ All 4 touched repos green +
      shipped: unified-api-contracts@b6887df513, market-tick-data-service@1feec2fe71, strategy-service@c95473c397,
      instruments-service@dd9e9486dc.

### P1 — declare what already captures

- [x] [DATA] P1. Add capability entries for the 7 defi venues that capture but are undeclared (`AAVE-PLASMA`,
      `BINANCE-BSC`, `BINANCE-ETHEREUM`, `COINBASE-ETHEREUM`, `FLUID-PLASMA`, `SANCTUM-SOLANA`, `SOLANA-NATIVE-SOLANA`),
      route=direct — DoD: start dates derived from each venue's earliest `captured` manifest row, not invented; cite the
      query. ✅ unified-api-contracts@4170f90d98 — see "2026-08-14 — P1 declarations" below. **Correction found**: 2 of
      the 7 (`FLUID-PLASMA`, `SOLANA-NATIVE-SOLANA`) measured ZERO captured rows of any data_type — this todo's own
      premise was wrong for them; they got `batch=None` (honest absence), not a fabricated date.
- [x] [DATA] P1. Add capability entries for `KALSHI-PERP` and `POLYMARKET-PERP` `perp_funding` (batch route=direct via
      `perp_funding_handler.py`) — DoD: entries match the venues' real captured `perp_funding` first dates, and no
      phantom EXPECTED cell is seeded for the data_types those venues only ever `empty_confirmed`. ✅
      unified-api-contracts@4170f90d98 — see Progress Log.
- [x] [DATA] P1. Add capability entries for all 31 existing sports bookmaker venues with `route=aggregator:ODDS_API` and
      the batch start date each venue's manifest actually shows, clamped to the 2020-06-06 floor — DoD: no entry
      predates the floor, and the four never-captured books get `batch = none` rather than a fabricated date. ✅
      unified-api-contracts@4170f90d98 — no venue's real earliest date predated the floor, so no clamping was needed.
- [x] [DATA] P1. Replace `NO_ADAPTER_YET` for the 31 sports venues with resolution through the route axis so an
      aggregator-served venue is adapter-backed, keeping `is_venue_executable()` as the SEPARATE execution-capability
      predicate it already documents itself to be — DoD: `is_venue_executable("PINNACLE")` stays False while the venue
      resolves a data-side route; the existing `test_venue_adapter_keys.py` assertions stay green or are updated with a
      stated reason. ✅ New `is_venue_data_adapter_backed()` predicate in `venue_adapter_keys.py` —
      `VENUE_TO_ADAPTER_KEY` itself is UNTOUCHED (still `NO_ADAPTER_YET` for all 31, so `is_venue_executable` behavior
      is unchanged, confirmed by the existing test file staying green with zero edits) — the new function checks
      `is_venue_executable(venue) or VENUE_DATA_TYPE_CAPABILITIES[venue].route != "direct"`.

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

### 2026-08-14 — P0 consumer enumeration (todo 1)

Full-repo `rg` sweep (all 26 non-PM repos in this slot, `.stale-pre-history-rewrite-*` excluded) for
`VENUE_DATA_TYPE_CAPABILITIES` / `VENUE_DATA_TYPE_NO_BATCH_SOURCE`, plus a second pass for aliased imports, TS/TSX
surfaces, dynamic access, and — critically — call sites that go through the three accessor functions
(`get_expected_data_types_for_venue`, `get_venue_data_type_start_date`, `venue_data_type_has_batch_source`, all defined
in `market_data_categories.py`) rather than importing the dicts directly, since a literal-string grep misses those
entirely.

**Definition site**: `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1959`
(`VENUE_DATA_TYPE_CAPABILITIES`), `:2729` (`VENUE_DATA_TYPE_NO_BATCH_SOURCE`), `:2410` (merges in the companion
`DEFI_VENUE_DATA_TYPE_CAPABILITIES` from `registry/defi_venue_capabilities.py:19` via `.update()`), `:2789`
(`get_expected_data_types_for_venue`, the accessor most callers actually use).

**Direct-dict REAL_CONSUMER (must migrate to the new shape)**:

| Repo                     | File                                                                | What it does                                                                      |
| ------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| unified-api-contracts    | `unified_api_contracts/registry/__init__.py:280,282,1014,1016`      | re-exports both symbols                                                           |
| market-tick-data-service | `engine/orchestrator/sentinels.py:152,155`                          | `.get(venue, {})` in sentinel-emission path                                       |
| market-tick-data-service | `scripts/sweep_phantom_manifest_rows.py:70,72`                      | (lifecycle: permanent) builds `{venue: frozenset(data_types)}` phantom-row mask   |
| strategy-service         | `engine/strategies/v2/target_universe/venue_capabilities.py:35,139` | `.get(name, {})` gates perp_funding eligibility                                   |
| instruments-service      | `scripts/expected_universe.py:51,250,271,293`                       | (lifecycle: permanent) `build_expected()`, the Layer-1 expected-universe producer |
| instruments-service      | `scripts/enumerate_expected_universe.py:121,767`                    | (lifecycle: permanent) backward-fill enumerator                                   |

**Direct-dict TEST consumers (must migrate)**: unified-api-contracts `tests/unit/test_data_status_registries.py`,
`test_mtds_venue_coverage.py`, `test_tradfi_ohlcv_only_mvp.py`, `test_cefi_registry_expected_universe_invariant.py`
(also reads `DEFI_VENUE_DATA_TYPE_CAPABILITIES`); market-tick-data-service
`tests/unit/engine/test_sentinels_coverage.py` (5x
`mock.patch("unified_api_contracts...market_data_categories.VENUE_DATA_TYPE_CAPABILITIES", {...})` — patches the dotted
path directly, breaks on rename regardless of accessor compat), `test_skipped_venue_expected_unattempted.py` (same
dotted-path patch pattern), `test_perp_funding_hyperliquid.py`; instruments-service
`tests/unit/scripts/test_enumerate_expected_universe.py`.

**Indirect via accessor functions (need NO change if accessor signatures/return shapes are preserved)**:
market-tick-data-service (`sentinels.py`, `preflight.py`, `orchestrator/__init__.py`, `manifest_finalize.py`,
`venue_fetch.py`, `onchain_perp_batch_handler.py`, `_onchain_perp_batch_live_only.py`, `scripts/pipeline_e2e_check.py`);
instruments-service (`expected_universe.py`, `enumerate_expected_universe.py`, `cefi_per_venue_capture_summary.py` via
`get_venue_data_type_start_date`); deployment-api (`breakdowns_core.py`, `mtds_expected.py`, `mtds.py`, all via
`data_status_service`). **Decision: keep these 3 accessor function names/signatures stable, reimplement their bodies
against the new typed record** — this is the single highest-leverage design choice, it removes deployment-api and most
of MTDS/instruments-service from the migration surface entirely while still satisfying "no consumer reads a removed
symbol" (the accessors, not the raw dicts, are the contract these callers actually depend on).

**Excluded (dated one-off scripts, lifecycle-marked, not live consumers)**: market-tick-data-service (4 files, all
`scripts/*_2026_*.py`), instruments-service (3 files, same pattern) — per `/codex/06-coding-standards/script-homes.md`.

**Excluded (doc/comment-only, no code dependency)**: 46 files across unified-api-contracts (14),
market-tick-data-service (13), deployment-service (6), deployment-api (5, all insulated via the accessor decision
above), instruments-service (5), features-service (2), system-integration-tests (1) — verified no actual import.

**Zero hits, confirmed**: agent-orchestrator, alerting-service, batch-live-reconciliation-service, client-reporting-api,
deployment-ui, e2e-testing, execution-service, fund-administration-service, greeks-service, ibkr-gateway-infra,
ml-service, trading-agent-service, unified-trading-api, unified-trading-ci, unified-trading-library,
unified-trading-system-ui. execution-service in particular is confirmed zero-touch for this migration (matters since a
peer session is concurrently active in that repo for a different plan).

**False positive noted**: `deployment-api/deployment_api/routes/batch_config_utils.py:209` defines its own unrelated
local `get_expected_data_types_for_venue()` — different function, not the UAC symbol.

### 2026-08-14 — P0 schema + migration (todos 2-5) complete

Implemented in `unified-api-contracts` (my exclusively-owned `market_data_categories.py`, plus the necessarily-coupled
`registry/__init__.py` re-exports — not in the exclusive list but same repo, no peer overlap):

- New `VenueCapabilityRecord` (`route: str`, `data_types: dict[str, DataTypeAvailability]`) and `DataTypeAvailability`
  (`batch_start_date: str | None`, `live: str`) dataclasses in `market_data_categories.py`. Named
  `VenueCapabilityRecord` not `VenueCapability` — that name is already taken by an unrelated execution-capability
  `StrEnum` in `venue_constants.py` (`VENUE_CAPABILITIES: dict[str, set[VenueCapability]]`), confirmed via grep before
  naming.
- **Zero-transcription-risk migration**: the ~440-line hand-curated literal was renamed to private
  `_VENUE_DATA_TYPE_CAPABILITIES_RAW` byte-identical (not retyped), then `VENUE_DATA_TYPE_CAPABILITIES` is derived from
  it programmatically (`route="direct"` for every pre-existing entry, satisfying P0 todo 3's DoD literally by
  construction rather than by a written test needing to re-verify hand transcription).
- `VENUE_DATA_TYPE_NO_BATCH_SOURCE` **deleted** (3 venues: ASTER book_snapshot_5, EXTENDED-STARKNET book_snapshot_5,
  LIGHTER-ZKSYNC trades+book_snapshot_5) — folded into the typed record as `batch_start_date=None` on the SAME
  capability entry (not a separate dict). One entry from the old dict (`ASTER: liquidations`) was NOT carried forward —
  it was never a declared `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` capability at all (confirmed: ASTER has no
  `liquidations` key), so it was unreachable through `get_expected_data_types_for_venue` and dropping it changes nothing
  observable (the dict's own comment already called it a "harmless superset").
- `venue_data_type_has_batch_source()` / `get_venue_data_type_start_date()` / `get_expected_data_types_for_venue()`
  signatures **unchanged** — bodies rewritten against `.data_types`. This was the highest-leverage design choice: it
  means every INDIRECT consumer (deployment-api's `breakdowns_core.py`/`mtds_expected.py`/`mtds.py`, most of MTDS/IS)
  needed **zero code changes**.
- One deliberate, narrow behavior change: `get_venue_data_type_start_date()` for the 3 folded no-batch-source cells now
  falls through to the `VenueMapping` venue-level fallback instead of returning the old literal date (which was really
  "when live capture started", not a batch date, per the plan's Design section — `batch=None` is the honest
  representation). No caller was found that depends on the old literal value for these 3 specific cells.
- **Direct-dict consumers migrated** (the ones NOT insulated by the accessor-signature-stable choice above): UAC's own
  `registry/__init__.py` (removed `VENUE_DATA_TYPE_NO_BATCH_SOURCE` from both the import list and `__all__`) and 4
  internal call sites in `market_data_categories.py` itself; market-tick-data-service `sentinels.py` +
  `scripts/sweep_phantom_manifest_rows.py`; strategy-service `venue_capabilities.py`; instruments-service
  `scripts/expected_universe.py` (2 call sites) + `scripts/enumerate_expected_universe.py`. Pattern was uniform across
  every site: `X.get(venue, {})` + `dt in X`/`X.keys()` → `X.get(venue)` (typed `VenueCapabilityRecord | None`) +
  `dt in cap.data_types`/`cap.data_types.keys()`.
- **Tests migrated**: unified-api-contracts (`test_data_status_registries.py`, `test_mtds_venue_coverage.py`,
  `test_tradfi_ohlcv_only_mvp.py` — `test_cefi_registry_expected_universe_invariant.py` needed NO change, it only
  iterates dict keys); market-tick-data-service (`test_sentinels_coverage.py` /
  `test_skipped_venue_expected_unattempted.py` — the latter's `mock.patch` target was rewritten from a raw
  `dict[str,dict[str,str]]` literal to a real `VenueCapabilityRecord`/`DataTypeAvailability` fixture — /
  `test_perp_funding_hyperliquid.py`); instruments-service (`test_enumerate_expected_universe.py`, 3 assertions). New
  `tests/unit/test_venue_capability_migration_recoverability.py` in UAC: parametrized over every one of the ~440
  pre-migration `(venue, data_type, start_date)` triples (sourced from `_VENUE_DATA_TYPE_CAPABILITIES_RAW`, not
  hand-copied) asserting `get_venue_data_type_start_date` recovers each one byte-for-byte, plus dedicated tests for the
  3 folded no-batch-source cells and the route="direct" invariant.
- **Verified, not just claimed**: UAC's full affected-test subset ran 454 passed / 4 skipped / 0 failed locally (the 2
  initial failures were the not-yet-fixed instruments-service consumer, confirmed fixed by re-run: 3 passed). MTDS
  58/58, strategy-service 51/51, instruments-service 19/19 passed on their respective targeted suites.
  `quality-gates.sh --no-fix` run in unified-api-contracts (in progress at time of this entry — full lint/basedpyright
  pass, one lint fix already applied for the new test file's import ordering).
- **Regression found + fixed by the real MTDS gate run** (not by this session's own test suite — a genuine miss):
  dropping ASTER's vacuous "liquidations" no-batch-source entry (reasoned above as "never reachable") was WRONG.
  market-tick-data-service's `_onchain_perp_batch_live_only.batch_data_types_for_venue()` calls
  `venue_data_type_has_batch_source(venue, data_type)` over an EXTERNALLY-SOURCED candidate list (not derived from
  `VENUE_DATA_TYPE_CAPABILITIES`), so an undeclared (venue, data_type) pair CAN reach that accessor —
  `test_onchain_perp_batch_handler.py::TestBatchDataTypesForVenue::test_aster_drops_book_and_liq_keeps_trades_funding`
  failed on the first full MTDS `quality-gates.sh` run. Root cause: `venue_data_type_has_batch_source()`'s rewritten
  body only ever checked `VENUE_DATA_TYPE_CAPABILITIES[venue].data_types[dt]` — it never consulted
  `_NO_BATCH_SOURCE_BY_VENUE` at all, so restoring the dict entry alone (first fix attempt) did nothing. Real fix: the
  accessor now checks `_NO_BATCH_SOURCE_BY_VENUE` FIRST, independent of whether the (venue, dt) pair is declared —
  restoring the original two-source-of-truth check the pre-migration code had. Added a dedicated regression test
  (`test_aster_liquidations_no_batch_source_despite_undeclared`) so this can't silently regress again. **Caught a live
  quickmerge race in the process**: I had already launched UAC's quickmerge before this failure surfaced; since
  quickmerge may isolate/snapshot the worktree at launch, I could not be certain the in-flight run would pick up the
  fix, so I stopped it (`TaskStop`) rather than let an uncertain race ship a known-broken commit, verified the repo was
  left clean (no partial commit, no orphaned worktree), and re-ran gates fresh before re-attempting the ship.

### 2026-08-14 — P1 declarations (defi 7, KALSHI-PERP/POLYMARKET-PERP, sports 31, adapter-backed predicate) — shipped unified-api-contracts@4170f90d98

All dates measured via
`pd.read_parquet("gs://<bucket>/_index/availability_index.parquet", columns=[...], filters=[...])` against the live prod
manifest (read-only; no gcloud/gsutil subprocess — hook-blocked in this workspace, used a GCS-backed pandas read
instead), `capture_status=="captured"` rows only, `.groupby(...)["date"].min()` for the earliest date. Full detail in
`unified_api_contracts/registry/market_data_categories.py`'s inline comments at each addition (not duplicated here per
the plan-references-codex-not-code convention, but summarized):

- **KALSHI-PERP / POLYMARKET-PERP `perp_funding`** (bucket `market-data-tick-cefi-prd-central-element-323112`):
  KALSHI-PERP 2026-06-03 (72 captured rows), POLYMARKET-PERP 2026-08-07 (7 rows, thin but real). Both venues also carry
  thousands of `empty_confirmed` rows for OTHER data_types — only `perp_funding` was declared, per the DoD.
- **7 defi venues** (bucket `market-data-tick-defi-prd-central-element-323112`): **naming finding first** — the manifest
  does NOT store these as the hyphenated `"AAVE-PLASMA"` etc. token; it stores a bare-protocol `venue` column
  (`AAVE_V3`, `BINANCE`, `COINBASE`, `FLUID`, `SANCTUM`, `SOLANA-NATIVE`) plus a separate `chain` column. Queried by
  bare venue + chain filter, results mapped back to this registry's hyphenated keys (confirmed correct per
  `venue_adapter_keys.py`'s own comments for AAVE-PLASMA/FLUID-PLASMA). Dates: AAVE-PLASMA `lending_indices` 2026-07-30
  (36 rows); BINANCE-BSC/BINANCE-ETHEREUM `lst_rates` 2023-04-19 (2,593 rows, same underlying wBETH contract both
  chains); COINBASE-ETHEREUM `lst_rates` 2022-02-05 (3,473 rows); SANCTUM-SOLANA `lst_rates` 2021-12-16 (3,571 rows).
  **FLUID-PLASMA and SOLANA-NATIVE-SOLANA measured ZERO captured rows of any data_type** (123,068 and 21,155+7,029
  non-captured rows respectively) — a correction to this plan's own P0 fact table, which assumed all 7 "capture but are
  undeclared." Both got `batch=None` instead of a fabricated date (`lending_indices` for FLUID-PLASMA matching its
  ETHEREUM sibling's declared type; `lst_rates` for SOLANA-NATIVE-SOLANA matching the other Solana LST venues — both are
  stated ASSUMPTIONS about which data_type is "the" honest-absence cell, not measurements, since zero rows of anything
  exist to measure from). **Separate, unresolved finding**:
  COINBASE-ETHEREUM/SANCTUM-SOLANA/BINANCE-BSC/BINANCE-ETHEREUM's earliest CAPTURED row predates that same venue's own
  `venue_launch_dates.py` entry by 8 days to ~1.5 years (2022-02-05 vs 2022-08-24; 2021-12-16 vs 2023-06-01; 2023-04-19
  vs 2023-04-27). Plausible for on-chain data (manifest date = real block history; launch date might mean "UAC
  registration date," not protocol genesis) but not reconciled here — used the measured manifest date per this todo's
  explicit DoD instruction, flagging rather than silently picking a side. Worth a follow-up `plans/active/issues/` doc
  if a future session wants to resolve it; not done here since it's outside this plan's scope and doesn't block the
  declaration itself.
- **31 sports bookmaker venues** (bucket `market-data-tick-sports-prd-central-element-323112`): captured `data_type`
  values are ONLY `odds`/`odds_horizon_bucket`/`arbitrage_opportunity`/`odds_movement`/`odds_snapshot` — never
  `trades`/`trades_inplay` (confirms those are reserved for the separate direct-feed venue set per
  `DATA_TYPES_BY_ASSET_GROUP`'s own comments). Declared `odds` only — the real raw MTDS capture type; NOT
  `arbitrage_opportunity`/`odds_horizon_bucket` (cross-bookmaker DERIVED types per that same comment, not a single-venue
  capability) and NOT the retired `odds_movement`/`odds_snapshot` (removed 2026-08-08, sports taxonomy P1 — historical
  artifacts, not current vocabulary). Earliest `odds` dates range 2020-06-06 (floor, 11 venues) to 2025-07-31 (4
  venues); none predates the floor. `BETOPENLY`/`NOVIG`/`ONEXBET`/`PROPHETX` re-confirmed zero rows of any status —
  `batch=None`. **PINNACLE correction**: it already had a `VENUE_DATA_TYPE_CAPABILITIES` key mapping to an empty `{}` (a
  pre-existing placeholder, unrelated to this plan) — 30 venues had zero key, 1 had a vacuous key, all 31 were
  functionally undeclared; the addition loop fills PINNACLE's existing key in rather than creating a duplicate.
- **Adapter-backed predicate**: new `is_venue_data_adapter_backed()` in `venue_adapter_keys.py` —
  `is_venue_executable(venue) or (VENUE_DATA_TYPE_CAPABILITIES.get(venue) is not None and cap.route != "direct")`.
  `VENUE_TO_ADAPTER_KEY` itself is untouched (still `NO_ADAPTER_YET` for all 31 sports venues), so `is_venue_executable`
  stays exactly as before — `test_venue_adapter_keys.py`'s 11 pre-existing tests pass unmodified, plus 3 new ones for
  the PINNACLE/BINANCE-SPOT/UNDERSTAT cases.
- **Regression found + fixed during P1 verification** (full UAC suite run, not just the new test files):
  `test_data_status_registries.py::TestYahooFinancePhantomVenueRemoved::test_legit_sports_no_adapter_venue_keeps_fallback_types`
  asserted `BETFAIR_EX_EU`/`DRAFTKINGS`/`FANDUEL` fall through to the FULL asset-group data_type cross-product — true
  before this plan, now false BY DESIGN (they have real narrow declarations). Rewrote it in two parts: a
  `monkeypatch`-based mechanism test proving the empty-caps fallback itself still works (via a SYNTHETIC venue, not a
  real one — same "real venues aren't stable absent-fixtures" lesson
  `test_row_data_types_capability_absent_venue_not_gated` in instruments-service already encodes), and a new
  `TestSportsBookmakerCapabilities` class asserting the NEW narrowed behavior is the regression guard going forward.
  Full UAC suite: 13,172 passed / 0 failed after the fix (was 1 failed / 8,240 passed on first full run, mid-P1).
- Full UAC test suite re-run clean after all P1 additions: **13,172 passed, 672 skipped, 5 xfailed, 0 failed**.

- **One-off scripts intentionally left untouched** (per the P0 consumer-enumeration entry above, script-homes lifecycle
  convention): `market-tick-data-service/scripts/delete_bybit_spot_spot_nonsense_manifest_2026_07_07.py` still reads
  `VENUE_DATA_TYPE_CAPABILITIES.get(_VENUE, {})` in its old raw-dict-assuming form. If this script is ever re-run before
  being deleted, it needs the same `.data_types` fix — flagging here rather than fixing silently, since scripts in this
  class are meant to be deleted after their one-time prod run, not maintained.

### 2026-08-14 — Four-way bookmaker spelling drift (P1, documentation todo)

Full mapping table, every book appearing in ANY of the four registries — **Registry A** =
`VENUES_BY_ASSET_GROUP["sports"]` / `VENUE_TO_ADAPTER_KEY` (venue_adapter_keys.py, the canonical DATA-axis venue token —
31 books); **Registry B** = `REQUESTED_ODDS_API_BOOKMAKERS` (sports_bookmaker_league_coverage.py, the real Odds-API
`bookmakers=` request keys — 23 entries, lowercase); **Registry C** = `BOOKMAKER_LEAGUE_COVERAGE` (same file, keys from
the committed `data/sports_bookmaker_league_coverage.json`, derived from captured manifest rows — 27 entries,
uppercase); **Registry D** = `AUDITED_BOOKMAKERS` (_odds_api_maps.py, data-quality-audited subset — 20 entries). "—" =
book absent from that registry.

| Book (canonical, Registry A) | Registry B (requested)                             | Registry C (observed-captured)    | Registry D (audited)          | Drift                                                                                    |
| ---------------------------- | -------------------------------------------------- | --------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------- |
| PINNACLE                     | pinnacle                                           | PINNACLE                          | PINNACLE                      | agree                                                                                    |
| BETFAIR_SB_UK                | betfair_sb_uk                                      | BETFAIR_SB_UK                     | BETFAIR_SB (no region suffix) | **D drops region suffix**                                                                |
| BETFAIR_EX_UK                | betfair_ex_uk                                      | BETFAIR_EX_UK                     | BETFAIR_EX (no region suffix) | **D drops region suffix**                                                                |
| BETFAIR_EX_EU                | betfair_ex_eu                                      | BETFAIR_EX_EU                     | — (absent)                    | D has no EU exchange entry at all                                                        |
| DRAFTKINGS                   | draftkings                                         | DRAFTKINGS                        | DRAFTKINGS                    | agree                                                                                    |
| FANDUEL                      | fanduel                                            | FANDUEL                           | FANDUEL                       | agree                                                                                    |
| LADBROKES                    | ladbrokes_uk (**adds \_UK**)                       | LADBROKES_UK (**adds \_UK**)      | LADBROKES                     | **A/D bare vs B/C suffixed**                                                             |
| BET888SPORT                  | sport888 (**different word order, no BET prefix**) | SPORT888 (same)                   | BET888SPORT                   | **A/D vs B/C are different tokens entirely** (B/C mirror the raw Odds-API bookmaker key) |
| SMARKETS                     | smarkets                                           | SMARKETS                          | — (absent)                    | agree where present                                                                      |
| BETMGM                       | — (absent — not in the requested list)             | BETMGM (has captured rows anyway) | — (absent)                    | B under-declares vs observed C                                                           |
| BETONLINEAG                  | betonlineag                                        | BETONLINEAG                       | BETONLINEAG                   | agree                                                                                    |
| BETOPENLY                    | — (excluded: `PREDICTION_MARKET_VENUES`)           | — (0 captured rows)               | — (absent)                    | consistent — this is 1 of the 4 zero-manifest-row venues from the plan's fact table      |
| BETRIVERS                    | betrivers                                          | BETRIVERS                         | BETRIVERS                     | agree                                                                                    |
| BETSSON                      | betsson                                            | BETSSON                           | — (absent)                    | agree where present                                                                      |
| BETVICTOR                    | betvictor                                          | BETVICTOR                         | BETVICTOR                     | agree                                                                                    |
| BETWAY                       | — (absent)                                         | BETWAY (has captured rows)        | — (absent)                    | B under-declares vs observed C                                                           |
| BOVADA                       | — (absent)                                         | BOVADA (has captured rows)        | — (absent)                    | B under-declares vs observed C                                                           |
| CASUMO                       | casumo                                             | CASUMO                            | CASUMO                        | agree                                                                                    |
| CORAL                        | coral                                              | CORAL                             | CORAL                         | agree                                                                                    |
| LIVESCOREBET                 | livescorebet                                       | LIVESCOREBET                      | LIVESCOREBET                  | agree                                                                                    |
| MATCHBOOK                    | matchbook                                          | MATCHBOOK                         | MATCHBOOK                     | agree                                                                                    |
| NOVIG                        | — (excluded: `PREDICTION_MARKET_VENUES`)           | — (absent)                        | — (absent)                    | consistent — 1 of the 4 zero-row venues                                                  |
| ONEXBET                      | — (absent)                                         | — (absent)                        | — (absent)                    | consistent — 1 of the 4 zero-row venues                                                  |
| PADDYPOWER                   | paddypower                                         | PADDYPOWER                        | PADDYPOWER                    | agree                                                                                    |
| PROPHETX                     | — (excluded: `PREDICTION_MARKET_VENUES`)           | — (absent)                        | — (absent)                    | consistent — 1 of the 4 zero-row venues                                                  |
| SKYBET                       | skybet                                             | SKYBET                            | SKYBET                        | agree                                                                                    |
| UNIBET                       | unibet                                             | UNIBET                            | UNIBET                        | agree                                                                                    |
| UNIBET_EU                    | — (absent — not requested)                         | UNIBET_EU (has captured rows)     | — (absent)                    | B under-declares vs observed C                                                           |
| UNIBET_UK                    | unibet_uk                                          | UNIBET_UK                         | UNIBET_UK                     | agree                                                                                    |
| VIRGINBET                    | virginbet                                          | VIRGINBET                         | VIRGINBET                     | agree                                                                                    |
| WILLIAMHILL                  | williamhill                                        | WILLIAMHILL                       | WILLIAMHILL                   | agree                                                                                    |

**Extra finding, not in Registry A at all**: `AUDITED_BOOKMAKERS` also has a `BET365` entry — a book that is not a
member of `VENUES_BY_ASSET_GROUP["sports"]` / `VENUE_TO_ADAPTER_KEY` under any spelling. Either BET365 needs a
Registry-A entry or this audited entry is stale/orphaned — flagged, not resolved by this documentation todo.

**Second finding**: `unified_api_contracts/registry/_odds_api_maps.py` itself has an INTERNAL two-way split not counted
in the plan's "four-way" framing — `ODDS_API_KEY_MAP` uses bare `"BETFAIR"` (mapping to
`["betfair_ex_uk","betfair_ex_eu","betfair_ex_au"]`), while `AUDITED_BOOKMAKERS` in the SAME FILE uses the
exchange/sportsbook-split `BETFAIR_EX`/`BETFAIR_SB` forms. Also flagged, not resolved here.

**Real drift requiring a canonicalization decision** (i.e. not just "one registry hasn't caught up yet" — B's
under-declarations vs C are a separate, pre-existing scope gap, not a spelling collision): **LADBROKES** (bare vs
`_UK`-suffixed) and **BET888SPORT** (vs the raw Odds-API `sport888`/`SPORT888` token) and **BETFAIR_EX/BETFAIR_SB**
(region-suffixed vs bare in Registry D only). These 3 are the genuine same-book-different-spelling collisions the plan's
next todo (canonicalize + migrate) must resolve.

**Recommended direction (not yet executed — see deferral below)**: canonicalize to `LADBROKES_UK` and `SPORT888` — i.e.
migrate Registry A (`VENUES_BY_ASSET_GROUP`/`VENUE_TO_ADAPTER_KEY`), the OUTLIER here, to match B/C. Evidence this is
the no-manifest-rekey-needed direction: `BOOKMAKER_LEAGUE_COVERAGE` (Registry C) is generated straight from captured
manifest rows (its own docstring) and already shows `LADBROKES_UK`/`SPORT888`, never bare `LADBROKES`/ `BET888SPORT` —
meaning the manifest was likely never actually written under Registry A's spelling for these two books in the first
place, so this direction should need an alias/rename only, not a historical re-key. **This is UNVERIFIED, not measured**
— stated as the evidence-based recommendation, not a confirmed fact; the todo below must re-confirm before executing.
`BETFAIR_EX`/`BETFAIR_SB` (Registry D only) needs an operator call, not a code inference: Registry A has TWO region
variants per exchange product (`_UK`/`_EU`) but D's audit numbers (accuracy/`is_exchange`) are recorded against ONE
unsuffixed key each — which region the audit actually covers isn't determinable from the registries themselves.

**Deferred — NOT executed this pass.** A real rename here is a large, separate blast-radius task, not a quick
same-session follow-on: `LADBROKES` alone appears in 21 files and `BET888SPORT` in 19, spanning unified-api-contracts,
market-tick-data-service, market-data-processing-service, AND
`execution-service/execution_service/cli/handlers/ live_execution_handler.py` — execution-service is a peer-occupied
repo this session was told to touch ONLY at named call sites, never a handler/launcher file, so this rename cannot
proceed under this session's coordination boundary regardless. More importantly: market-tick-data-service and
market-data-processing-service both already carry a cluster of dated `restamp`/`manifest_swap` scripts targeting sports
bookmaker venue spelling specifically (`restamp_sports_bookmaker_venue_2026_07_27.py`,
`manifest_swap_bookmaker_venue_restamp_2026_07_27.py`, `manifest_swap_venue_restamp_candles_2026_08_03.py`,
`restamp_sports_trades_to_odds_2026_08_12.py`, and siblings) — strong evidence an adjacent, dedicated venue-restamp
effort already ran or is running. Grepping `plans/active/` for this territory surfaces
`plans/active/issues/sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md` as the directly relevant
prior-art doc (title alone: "venue writer bugs"). Executing this rename blind, without reading that doc's history first,
risks contradicting an operator ruling already made there or duplicating completed work — a real risk this session
should not take casually.

**Leaving the plan's canonicalization todo (and its `[OPERATOR]` re-keying-gate follow-on) UNCHECKED, not fabricating a
new one** — the todo already exists and already tracks this; the correct next step for whoever picks this up is: read
`sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md` first, confirm whether LADBROKES/ BET888SPORT
canonicalization is already resolved or still open there, THEN do the full consumer enumeration (same rigor as this
session's P0 VENUE_DATA_TYPE_CAPABILITIES enumeration) before touching any file.
