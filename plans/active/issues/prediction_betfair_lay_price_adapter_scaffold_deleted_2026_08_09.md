---
doc_type: issue
title:
  Betfair back+lay persistence todo's premise invalidated — scaffold adapter deleted as dead code 2026-08-01; real
  remaining scope is a multi-part adapter+routing+fixture-mapping build, not a "wiring" task
summary: >-
  The batch6 plan's Betfair back+lay todo assumed a scaffolded market-data adapter still existed; it was deleted
  2026-08-01 as unreached dead code. Restoring it alone isn't enough either — the live sports batch-routing path is
  hardcoded to a different adapter's interface, and Betfair's market_id has no resolver to this repo's canonical
  fixture_id. Re-scopes the remaining work into concrete, worker-determinable todos.
status: open
nature: issue
asset_group: [prediction, sports]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [betfair, sports-odds, prediction, dead-code, scope-correction]
related: [prediction_satellite_ao_dispatch_batch6_2026_07_29]
created: 2026-08-09
author: slot-17 (backend_engineer)
parent_epic: predictions_master
assigned_vm: planning
priority: P2
resolved_by:
locked_by:
source: [prediction_satellite_ao_dispatch_batch6_2026_07_29.md item under "Two-sided Betfair odds"]
---

# What I found

`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s open P2 todo ("Two-sided Betfair odds — persist back+lay") was
dispatched to slot-17 with a described remaining scope of "only the `factory.py` `VENUE_REGISTRY` wiring + `lay_price`
persistence + live-verification re-run" — based on a 2026-07-31 (slot-7) research note claiming a Betfair market-data
adapter was "already scaffolded, unused, in
`market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/betfair_adapter.py` (confirmed via
research to already parse both sides)".

**That file no longer exists.** It was deleted 2026-08-01 by `market-tick-data-service@6bc85e13` ("fix(sports): delete
dead BetfairAdapter/MatchbookAdapter market_interface classes") — correctly, per `adapter-dead-code-and-fallback-ban.md`
rule 1: the class was imported/exported but never reached by any live code path (`factory.VENUE_REGISTRY` didn't include
it; the actual live sports dispatch is `umi_tick_provider.py::_route_sports()` → `factory.VENUE_REGISTRY`, which has
exactly one sports entry, `"odds_api"`). The dead-code sweep ran one day after the partial-progress note was written and
had no way to know this todo was mid-flight depending on that exact file.

I recovered the deleted content via `git show 6bc85e13~1:.../betfair_adapter.py` (313 lines) — it's real, not a stub:
`BetfairAdapter(BaseSportsAdapter)` with `authenticate()` (interactive session-token login), `get_markets()`
(`listMarketCatalogue`), `get_prices()` (`listMarketBook`, `EX_BEST_OFFERS`), and `_normalize_runner()` which DOES
already parse both `availableToBack` and `availableToLay` price levels into `backs`/`lays` lists per runner. The
UAC-side pydantic models it depends on (`unified_api_contracts.external.betfair.{schemas,normalize}` —
`BetfairMarketBook`/`BetfairMarketCatalogue`/ `BetfairRunner`/`BetfairAuthResponse`) are still live and unchanged. So
the 2026-07-31 research was accurate — the artifact just got swept in the interim.

**Restoring the file is NOT sufficient to close this todo**, though — two further gaps surfaced during this session's
research that the original todo text didn't anticipate:

1. **`_route_sports()` is hardcoded to `OddsApiAdapter`, not generic dispatch.**
   `market_tick_data_service/adapters/umi_tick_provider.py:190-201` does
   `cast(OddsApiAdapter, get_adapter(venue.lower(), category="sports"))` then calls
   `sports_adapter.download_batch(date=..., data_types=..., leagues=...)` unconditionally. The deleted `BetfairAdapter`
   never implemented `download_batch()` (its interface is `get_markets()`/`get_prices()`, modeled on Betfair's two-call
   discovery+book pattern, not odds_api's single-call-per-day batch pull). Simply adding
   `"betfair": ("sports", BetfairAdapter)` to `VENUE_REGISTRY` would make `get_adapter("betfair")` resolve, but the
   automated batch-capture scheduler would still break on the `.download_batch()` call — this needs either a
   `download_batch()` method added to `BetfairAdapter` (mapping the two-call Betfair flow into the same per-day-batch
   cadence/shape odds_api uses) or a venue-branch in `_route_sports()` — an actual design decision, not mechanical
   wiring.
2. **Betfair market_id → the workspace's canonical `fixture_id` is unresolved.** The odds_api row shape is built around
   `fixture_id` (see `market_tick_data_service/market_interface/adapters/sports/fixture_id_resolver.py`); Betfair's own
   `market_id`/`selection_id` are exchange-native identifiers with no established resolver mapping to canonical fixtures
   in this repo today. Emitting a Betfair-sourced row that downstream consumers can actually key against (rather than a
   parallel, unresolved identifier space) needs that mapping worked out — cross-venue entity-resolution, not "add a
   column."

Given both gaps require actual engineering/architecture judgment (not a checkable fact or a small scoped change), and
per `backend_engineer.md`'s craft rule ("If you surface an unknown the plan didn't anticipate... file an issue doc +
escalate — do not absorb unplanned scope"), I'm stopping here rather than open-endedly expanding this P2/
1-estimated-hour todo into what is realistically a multi-hour, multi-file build touching schema-adjacent code in a
domain CLAUDE.md flags as high-stakes ("data pipeline correctness is the heartbeat").

# Why it matters

The parent plan's todo is currently unchecked and will keep re-dispatching as scoped ("just wire it in") to whichever
worker picks it up next, who will hit the same deleted-file surprise and re-do this same research unless the todo is
re-scoped here first.

# Recommended decision

Re-scope the parent todo into the concrete steps below (this issue doc's `## Todos`) rather than leave it as one
under-scoped item. All are AO-eligible (bounded, worker-determinable) except the design choice in item 2, which should
be resolved as part of doing item 2 (pick the `download_batch()`-shim approach — it's the smaller, more
consistent-with-existing-pattern option — rather than branching `_route_sports()`, unless whoever picks it up finds a
concrete reason not to).

## Todos

- [x] ✅ [BACKEND] P2. Restore `market_tick_data_service/market_interface/adapters/sports/betfair_adapter.py` from
      `market-tick-data-service@6bc85e13~1` (content already recovered and verified against current UAC in this issue
      doc's research — the UAC `external.betfair` models are unchanged) and re-add its `__init__.py` imports/exports
      (reverse of `6bc85e13`'s diff). (repo: market-tick-data-service) — market-tick-data-service@fc9e36cd. Restored the
      313-line file verbatim via `git show 6bc85e13~1:...betfair_adapter.py`; re-added `BetfairAdapter` to
      `market_interface/adapters/sports/__init__.py` and `market_interface/__init__.py` (imports + `__all__`),
      MatchbookAdapter intentionally left deleted (out of scope for this todo). Verified UAC deps
      (`unified_api_contracts.external.betfair.{BetfairAuthResponse,BetfairMarketBook,BetfairMarketCatalogue,BetfairRunner}`)
      and `BaseSportsAdapter` unchanged;
      `python3 -c "import market_tick_data_service.market_interface as mi; mi.BetfairAdapter"` resolves cleanly. QG
      green (sentinel matched HEAD `fea84ecd`); shipped via quickmerge (rebased to `fc9e36cd` on push), verified
      ancestor of `origin/live-defi-rollout`.
- [ ] [BACKEND] P2. Add a `download_batch(date, data_types, leagues)` method to the restored `BetfairAdapter` that calls
      `get_markets()` then `get_prices()` per discovered market and returns a `pd.DataFrame` shaped compatibly with
      `OddsApiAdapter.download_batch`'s output (same column set odds_api emits, e.g. fixture linkage / bookmaker / price
      / side / timestamp columns — read `odds_api_adapter.py`'s row-construction before `pd.DataFrame(all_rows)` at line
      ~520 for the exact target shape), PLUS a `lay_price` column (scalar per row, e.g. best/lowest `availableToLay`
      price) populated ONLY when a complete lay book exists for that outcome (mirrors the honest-absence contract
      `features-service@d792f421`'s read side already expects — a partial book must NOT populate a distorted
      `lay_price`). Add `"betfair": ("sports", BetfairAdapter)` to `factory.py`'s `VENUE_REGISTRY` (removing it from
      `PLANNED_VENUES`). (repo: market-tick-data-service)
- [ ] [BACKEND] P2. Resolve Betfair `market_id`/`selection_id` → canonical `fixture_id` — check whether
      `fixture_id_resolver.py`'s existing resolver can accept a Betfair market/event name lookup, or whether a new
      resolution path is needed; do NOT emit unresolved Betfair rows under a parallel identifier space. (repo:
      market-tick-data-service)
- [ ] [BACKEND] P2. Live-verify: using the now-live `betfair-session-token` GSM secret (`execution-service@7e03bf7b`),
      call the restored adapter's `get_markets()`/`get_prices()` (or the new `download_batch()`) against a real sampled
      in-play Betfair market, confirm both `backs` and a populated `lay_price` persist through the normal MTDS capture
      write path (not a standalone script bypassing it), and flip this satellite plan's original P2 item +
      `prediction_arb_live_execution_bridge_2026_07_20.md` item [5] to done citing the commit SHA + the sampled market's
      evidence. (repo: market-tick-data-service)

## Progress Log

- 2026-08-09 (slot-17, backend_engineer): filed this issue doc after discovering the dispatched todo's premise (existing
  scaffold) was invalidated by an intervening dead-code deletion; recovered the deleted file's content via git history
  for the next worker's use (embedded above); did not implement anything in market-tick-data-service this session — see
  the parent plan's Progress Log for the pointer back here.
- 2026-08-09 (slot-3, backend_engineer): completed todo 1 — restored `betfair_adapter.py` verbatim + re-added its
  `BetfairAdapter` imports/exports to both `__init__.py` files (Matchbook left deleted, out of scope). QG green, shipped
  `market-tick-data-service@fc9e36cd`. Todos 2-4 (download_batch shim, fixture_id resolution, live-verify) remain open
  for the next worker.
