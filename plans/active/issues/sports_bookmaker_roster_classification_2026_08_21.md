---
doc_type: issue
title: >-
  Sports bookmaker roster classification — odds_api vs Unity vs legacy-leftover, 4 HIGH-confidence removal candidates
summary: >-
  Classified all 39 currently-kept sports venues (the plan's "27 kept books" is a stale 2026-08-08 snapshot; 12
  venues were added since) against odds_api fetch scope and Unity central-wallet coverage. 25 are actively fetched
  via odds_api, 9 are Unity-covered (1 dual-covered with odds_api), and 4 (BETOPENLY, NOVIG, ONEXBET, PROPHETX) carry
  a canonical venue token and an odds_api key that was never wired into the live fetch scope, with ZERO manifest
  presence of any kind — HIGH-confidence removal-proposal candidates, arbitrage-research vintage. 2 more (BETMGM,
  BETWAY) show the same unwired pattern but have some real captured rows, so are flagged LOW-MEDIUM confidence
  rather than proposed outright. Also surfaces 2 unresolved Unity-roster contradictions between
  `unity_child_books.py` (code SSOT) and `sports_master.md`'s historical 15-book vision doc.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [sports, bookmakers, odds-api, unity, venue-cleanup, classification]
related:
  [
    /plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md,
    /plans/epics/sports_master.md,
    /plans/active/mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14.md,
    /plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
  ]
created: 2026-08-21
author: T2 (general-purpose sub-agent investigation)
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend
drift_direction: advance-code
depends_on: []
source: ["code_readiness_t2_refdata_marketdata_2026_08_19.md's sports-bookmaker-roster-classification todo"]
resolved_by:
locked_by:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    unified-api-contracts/unified_api_contracts/registry/venue_constants.py,
    unified-api-contracts/unified_api_contracts/registry/_odds_api_maps.py,
    unified-api-contracts/unified_api_contracts/internal/unity_child_books.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py,
  ]
---

# Sports bookmaker roster classification — for operator removal-proposal review

## Why this ran

`code_readiness_t2_refdata_marketdata_2026_08_19.md`'s sports-bookmaker todo asked: for each "kept" sports
bookmaker, is it (a) an odds-api bookmaker, (b) covered by the Unity central-wallet integration, or (c) neither — a
legacy arbitrage-research leftover, proposed for removal (removal itself stays operator-gated, not done here). No
single clean roster existed across `sports_master.md` / the Unity plan doc / e2e docs, so this investigation built
one directly from the code + the live 2026-08-20 coverage.json.

## The "27 kept books" is stale

The literal "27" comes from a 2026-08-08 measurement (`sports_taxonomy_p1_capture_and_contracts_2026_08_08.md:103`,
operator ruling line 130: "keep all 27 books as venues"). The CURRENT `VENUES_BY_ASSET_GROUP["sports"]`
(`unified-api-contracts/.../market_data_categories.py:537-658`) holds **39** venues: the original 27 odds_api-fanout
books + 4 Betfair-family/Pinnacle venues (sourced via Betfair Stream / hybrid, outside the "bookmaker fan-out"
framing) + 8 Unity child books registered 2026-08-17 (`cross_cutting_satellite_ao_dispatch_batch14`, after the
27-count was taken). All 39 were classified, not just 27.

## Classification summary

- **(a) odds-api, live fetch scope**: 25 venues actively in `REQUESTED_ODDS_API_BOOKMAKERS`
  (`odds_api_adapter.py:115-157`) — all confirmed captured in coverage.json, real row counts.
- **(a)-key-only, never fetched**: 6 more carry an `ODDS_API_KEY_MAP` entry but are excluded from the live scope —
  BETMGM, BETOPENLY, BETWAY, NOVIG, ONEXBET, PROPHETX.
- **(b) Unity-covered**: 9 — MATCHBOOK (dual a+b, has its own execution-service adapter too) + 8 net-new Unity child
  books (3ET, BROKER5, CROWN, SBO, SHARPBET, VX, BETDEX, IBC), all currently zero-capture / Unity subscription
  pending (explicitly tracked forward-looking registrations, not legacy leftovers).
- **(c) neither — removal-proposal candidates**:
  - **HIGH confidence**: **BETOPENLY, NOVIG, ONEXBET, PROPHETX** — canonical venue token exists, odds_api key
    exists, but never in the live fetch scope; **zero `by_venue` presence of any kind** (no captured, no
    empty_confirmed, no attempted_failed) in the live 2026-08-20 coverage.json; no Unity coverage. All 4 sit in
    `SPORTS_PREDICTION_MARKET_VENUES`/`SPORTS_BOOKMAKER_API_VENUES` alongside Polymarket/Kalshi — read as
    arbitrage-research-vintage registrations kept as venue tokens under the 2026-08-08 "keep all books" ruling but
    never actually wired to a data source.
  - **LOW-MEDIUM confidence, flag only**: **BETMGM** (captured=1,591 / attempted_failed=4,964), **BETWAY**
    (captured=1,803 / attempted_failed=3,977) — same "key exists, not in live scope" pattern, but non-zero real
    captured rows, so not a clean removal case. Operator judgment call.
  - All other 33 venues are actively fetched and/or Unity-covered — **not** removal candidates.

## Contradictions found (not resolved here)

1. **Unity roster mismatch**: `sports_master.md:1607-1608`'s historical 15-book Unity vision (PS3838/Pinnacle,
   SingBet, BetISN, Penta88, GA288, Orbit, …) does not match the code SSOT `unity_child_books.py`'s 10 confirmed
   books (dated 2026-04-17) — PINNACLE and CROWN sit on opposite sides of the two lists.
2. **Betfair sub-venue ↔ Unity mapping unresolved**: Unity's "BETFAIR" child book is a reused token
   (`market_data_categories.py:635-641`) but never disambiguated against BETFAIR_SB_UK / BETFAIR_EX_UK /
   BETFAIR_EX_EU.
3. **Wire-spelling unfold artifacts** (data-quality observation, outside this task's scope): `LADBROKES`/
   `LADBROKES_UK` and `BET888SPORT`/`SPORT888` both appear as separate rollups in the live manifest despite
   `SPORTS_VENUE_FOLD` intending to fold them — flagged for whoever owns that fold logic next.

## Todos

- [x] [OPERATOR] P2. Rule on the 4 HIGH-confidence removal candidates (BETOPENLY, NOVIG, ONEXBET, PROPHETX) — remove
      the venue tokens, or keep them declared with an honest reason (e.g. future-planned direct-API integration)?
      — resolved by 2026-08-21 operator ruling in `code_readiness_t2_refdata_marketdata_2026_08_19.md`: REMOVE ALL 6.
- [x] [OPERATOR] P3. Judgment call on BETMGM/BETWAY — worth re-adding to the live odds_api fetch scope (both have
      real if weak historical capture), or also propose for removal? — resolved: removal, per same ruling.
- [x] [BACKEND] P1. **2026-08-21 removal shipped — wave-1a registry lane only, `unified-api-contracts@710db834`.**
      This doc's odds_api/manifest-only classification did not surface that the same 6 tokens also live in a
      SEPARATE registry family: `unified_api_contracts/canonical/domain/bookmaker_registry.py` +
      `canonical/domain/sports/{_registry_us,_registry_exchanges,_registry_intl_scrapers,odds_api_mapping}.py` +
      `registry/venue_manifest/betting_sports.py` + `registry/sports_bookmaker_league_coverage.py` +
      `unified_api_contracts/external/{onexbet,betway}/*` + `normalize_utils/sports.py` — none of these were in
      the T2 plan's enumerated surface list. Cross-repo grep found `execution-service` has a REAL import-time
      binding on ONEXBET specifically: `sports_execution/adapters/bookmaker_api/onexbet.py` does
      `BOOKMAKER = BOOKMAKER_REGISTRY["onexbet"]` at MODULE level (imported transitively via
      `sports_execution/adapters/__init__.py`) — removing the `"onexbet"` key from `bookmaker_registry.py` would
      raise `KeyError` at import time in execution-service, a cross-repo break. (The `OneXBetAdapter` class itself
      is confirmed dead/unrouted per `sports_adapter_dead_code_fallback_duplicate_audit_2026_08_01.md` finding 11 —
      `SportsHandler.BOOKMAKER_VENUES` is empty — but the import still executes.) Per this session's dispatch
      instructions ("if any live code binds them, STOP and report instead of shipping a break"), that second
      family was left untouched — only the originally-enumerated wave-1a lane
      (`venue_constants.py`/`_sports_venue_constants.py`/`market_data_categories.py`/`venue_adapter_keys.py`/
      `_odds_api_maps.py`/`registry/__init__.py`/`capability_declarations/_sports.py`/`venue_granularity_seed.py`
      + `tests/unit/test_venue_adapter_keys.py`/`tests/unit/test_data_status_registries.py`) was removed and
      shipped, confirmed genuinely removal-safe by a repo-wide grep across execution-service,
      market-tick-data-service, instruments-service that found zero consumers of those specific module/exported-set
      names. `quality-gates.sh --no-fix` green (13458 passed, 0 failed) before commit. Next-pass follow-up filed as
      new todos in the T2 plan (`code_readiness_t2_refdata_marketdata_2026_08_19.md`): (a) regenerate
      `openapi/capability-manifest.json` + `openapi/venue-coverage-report.md` (still list the 6 removed venues, no
      in-repo generator script found), (b) the coordinated two-repo removal of the `bookmaker_registry.py` family
      (execution-service's dead `OneXBetAdapter` retires first, then `"onexbet"` comes out of the registry).
- [ ] [BACKEND] P3. Resolve the Unity 15-book-vision vs `unity_child_books.py` contradiction (PINNACLE, CROWN) —
      update whichever source is stale, cite the resolution.
- [ ] [BACKEND] P3. Resolve the Betfair-family ↔ Unity "BETFAIR" child-book mapping ambiguity.
