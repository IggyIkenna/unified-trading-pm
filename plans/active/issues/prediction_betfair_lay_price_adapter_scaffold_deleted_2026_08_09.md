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
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
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
- [x] ✅ [BACKEND] P2. **DONE 2026-08-09 (slot-5, backend_engineer) — `market-tick-data-service@85872cab`.** Add a
      `download_batch(date, data_types, leagues)` method to the restored `BetfairAdapter` that calls `get_markets()`
      then `get_prices()` per discovered market and returns a `pd.DataFrame` shaped compatibly with
      `OddsApiAdapter.download_batch`'s output (same column set odds_api emits, e.g. fixture linkage / bookmaker / price
      / side / timestamp columns — read `odds_api_adapter.py`'s row-construction before `pd.DataFrame(all_rows)` at line
      ~520 for the exact target shape), PLUS a `lay_price` column (scalar per row, e.g. best/lowest `availableToLay`
      price) populated ONLY when a complete lay book exists for that outcome (mirrors the honest-absence contract
      `features-service@d792f421`'s read side already expects — a partial book must NOT populate a distorted
      `lay_price`). Add `"betfair": ("sports", BetfairAdapter)` to `factory.py`'s `VENUE_REGISTRY` (removing it from
      `PLANNED_VENUES`). (repo: market-tick-data-service)

      Implemented via `get_markets()`+`get_prices()` (catalogue's `RUNNER_DESCRIPTION` projection extended to surface
          `runner_name`/`selection_id`; `get_markets` gained an optional `market_start_time` window since Betfair's
          catalogue has no historical endpoint). `lay_price` gated at MARKET level (every runner with a back price must
          also have a lay price, else the whole market's `lay_price` stays unset) — exactly the completeness contract
          `_row_for_runner`/`_rows_for_market` implement. `fixture_id`/`af_fixture_id` are honestly left unresolved
          (`NO_FIXTURE_DATA`, falling back to Betfair's own `event_id`/`market_id`) — real fixture resolution is todo 3
          below, confirmed genuinely hard (a real Betfair catalogue response shows match-odds runners are generic
          "Home"/"Draw"/"Away" labels, not team names). Also fixed the ACTUAL dispatch blocker this todo's own text didn't
          anticipate: `umi_tick_provider.py`'s `_SPORTS_VENUES` was hardcoded to `{"ODDS_API"}` — without adding
          `"BETFAIR"` there, the factory wiring alone would never have been reached by a live `--venue betfair` capture
          call. 9 new unit tests (`tests/unit/test_betfair_adapter.py`); 1 pre-existing test fixed
          (`test_prediction_market_venue_wiring.py::test_remaining_planned_venues` asserted the old
          `betfair in PLANNED_VENUES` state). Full `quality-gates.sh` green (`ALL QUALITY GATES PASSED`, sentinel matched
          `06387b04` before the ship rebase).

          **Open caveat for todo 4 (live-verify), NOT resolved this session**: UAC's registries
          (`_sports_venue_constants.py`, `_odds_api_maps.py`, `data_availability.py`) reference `BETFAIR_EX_UK`/
          `BETFAIR_EX_EU` as the canonical per-region data-axis venue names for the exchange (bare `BETFAIR` described
          elsewhere as "operator-group parent, not data-axis"). This todo's own instruction said literally `"betfair"`
          for the `VENUE_REGISTRY` key, which is what's implemented — but the live-verify pass should confirm whether the
          manifest/asset-group/bucket routing expects bare `BETFAIR` or the region-qualified forms before trusting a live
          capture's shard path is correct, not just that the HTTP calls succeed.

- [x] ✅ [BACKEND] P2. **DONE 2026-08-09 (slot-26, backend_engineer) — `market-tick-data-service@766e776d`.** Resolve
      Betfair `market_id`/`selection_id` → canonical `fixture_id` — check whether `fixture_id_resolver.py`'s existing
      resolver can accept a Betfair market/event name lookup, or whether a new resolution path is needed; do NOT emit
      unresolved Betfair rows under a parallel identifier space. (repo: market-tick-data-service)

      **Answer: the existing `FixtureIdResolver.resolve(af_league_id, home_id, away_id, day)` needed no changes at
          all** — wired `BetfairAdapter` into the SAME resolver instance `OddsApiAdapter` uses (added a lazy
          `fixture_resolver` property, identical `resolve_bucket_name(kind="instruments-store", asset_group="sports")`
          pattern), fed by a new Betfair-specific projection: `_parse_market_teams()` splits `event_name`'s free-text
          "Team A v Team B" via UAC's already-shipped-but-unused `parse_betfair_event_teams()` (found during this
          session — no caller existed anywhere in the codebase before this); `_canonical_team_ids()` runs both names
          through the SAME `validate_team_resolution()` alias index `OddsApiAdapter._build_fixture_rows()` uses (`provider=`
          is informational-only, confirmed by reading `team_mappings.py`); a new `_resolve_af_league_id()` matches
          `competition_name` against UAC's `LEAGUE_REGISTRY.display_name` (exact match first, substring fallback,
          `event_country`-disambiguated when the bare name collides — confirmed live: bare "Premier League" alone
          substring-matches ~40 leagues worldwide (English/Russian/Ukrainian/Egyptian/Kazakhstan/...), so without a
          country hint it honestly returns `None` rather than risking a wrong join; "English Premier League" or
          "Premier League"+`event_country="GB"` both resolve cleanly to af_league_id=39). One resolution per MARKET (not
          per runner, since every runner in a match-odds market shares one fixture) via new
          `_resolve_fixture_for_market()`, called once in `download_batch`'s loop before `_rows_for_market`.
          `fixture_id` now prefers the resolved `af_fixture_id`, falling back to Betfair's own `event_id`/`market_id`
          only when honestly unresolved — the exact same pattern `OddsApiAdapter` already uses, no parallel identifier
          space. `home_team`/`away_team`/`league_id` columns (previously always `None`) now populate from the same
          resolution. 9 new/updated unit tests (6 new + existing 15 kept green) — the existing tests' `_MARKET` fixture
          uses the deliberately-ambiguous bare "Premier League" competition_name (no `event_country`), so they stay
          `NO_FIXTURE_DATA` unchanged AND never touch `fixture_resolver` (no live GCS I/O in the pre-existing suite);
          new tests inject a `_FakeFixtureResolver` via `adapter._fixture_resolver` (mirrors
          `test_odds_api_fixture_id_join.py`'s DI pattern) to prove the matched path, the unresolved-team-name path
          (confirms `fixture_resolver.resolve()` is never called when team resolution fails — no wasted GCS read), and
          `_resolve_af_league_id`'s exact/ambiguous/country-disambiguation/non-football-gate behavior directly.
          Full `quality-gates.sh` PASSED (267s, 10409 passed/0 failed; sentinel matched HEAD `651156eb`). Shipped
          `market-tick-data-service@766e776d`, verified ancestor of `origin/live-defi-rollout`.

          **Open for todo 4 (live-verify)**: this resolution has only been exercised against a synthetic test fixture
          (`"Man Utd v Liverpool"` / `"Premier League"` + `event_country="GB"`) — a real Betfair catalogue response's
          actual `competition.name`/`event.countryCode` values (does Betfair send bare "Premier League" or already
          country-qualified names? is `countryCode` reliably populated for every competition?) are UNVERIFIED against
          the live API. Todo 4's live-verify pass should confirm the resolver actually matches real captured markets,
          not just that the wiring compiles.

- [ ] [INFRA] P2. **RETAGGED 2026-08-11 (slot-20, backend_engineer) — was `[BACKEND]`.** Provisioning a new
      `europe-west2` network egress (VM/proxy) is `infra` craft's domain per `backend_engineer.md`'s `does_not` ("Infra
      provisioning, VM launches, CI/CD, cloud (→ infra)") — retagged so dispatch routes correctly; see the matching
      retag note in the parent plan's mirrored item for the full rationale. **OPERATOR-DECIDED 2026-08-11: provision
      egress from `europe-west2` (London), not `europe-west4`.** Reversing the 2026-08-10 "permanently parked"
      disposition: asked again, the operator declined to re-approve `europe-west4` but asked for whichever
      Betfair-accepted region matches the credential's actual jurisdiction. Confirmed the adapter authenticates against
      `api.betfair.com`/`identitysso.betfair.com` (the UK & Ireland-licensed Exchange API) and this workspace's account
      is a direct UK Exchange account (`BETFAIR_EX_UK` primary venue, `capital-structure-and-regulatory.md`) —
      `europe-west2` is the only GCP EU region with UK IP geolocation, which is the actual mismatch that got both Tokyo
      and `europe-west4` (Netherlands) 403'd; `europe-west1` (Belgium, cheaper) carries the same jurisdiction-mismatch
      risk already vetoed once, so not used. **Next step (not done this session)**: provision an egress path from
      `europe-west2`, re-run `refresh_betfair_session_token.py` against it, confirm the `betfair-session-token` GSM
      secret populates, then live-verify per the original done-when below. Prior context preserved: the
      `betfair-session-token` secret was NOT actually live (execution-service@7e03bf7b shipped only the refresh
      mechanism, never ran it) and, once provisioned, Betfair's interactive-login endpoint hard-rejects this workspace's
      ONLY current network egress (the single orchestrator VM's Tokyo/`asia-northeast1` IP) as geo/traffic-restricted.
      Live-verify: using a working `betfair-session-token` GSM secret, call the restored adapter's
      `get_markets()`/`get_prices()` (or the new `download_batch()`) against a real sampled in-play Betfair market,
      confirm both `backs` and a populated `lay_price` persist through the normal MTDS capture write path (not a
      standalone script bypassing it), and flip this satellite plan's original P2 item +
      `prediction_arb_live_execution_bridge_2026_07_20.md` item [5] to done citing the commit SHA + the sampled market's
      evidence. (repo: market-tick-data-service)

- [x] ✅ [INFRA] P2. **DONE 2026-08-11 (slot-18, data_engineering adopting infra craft).** Provision the
      `europe-west2` egress path the operator decided on 2026-08-11, and MEASURE whether it actually clears
      Betfair's block (the open question todo 4 could not answer from Tokyo). **Answer: it clears it.**
      Reserved regional static address `betfair-egress-ip` = **34.39.85.36** (`europe-west2`) and launched a
      probe VM + a real egress VM there. Measured, same two endpoints, same day:

      | endpoint | Tokyo `13.113.200.22` | europe-west2 |
      | --- | --- | --- |
      | `identitysso.betfair.com/api/login` | 403 + Betfair "Restricted" page | **405** (real Betfair app HTML) |
      | `api.betfair.com/exchange/betting/json-rpc/v1` | 403 + "Restricted" page | **400 `{"code":-32700,"message":"DSC-0008"}`** |

      A 405-on-GET and a real JSON-RPC parse error are Betfair's OWN API responses — the geo/traffic block that has
      held this todo since 2026-08-09 is NOT present from europe-west2. Shipped
      `deployment-service/scripts/vm/launch-betfair-egress-vm.sh`: attaches the reserved static IP (Betfair fraud
      heuristics key on IP STABILITY for a real-money account, so an ephemeral IP re-rolls that dice every launch),
      `lc_singleton_check` so two concurrent logins can never race, self-deletes after the refresh unless `--keep`
      (billing-waste rule), and carries a `# non-relaunchable:` marker since it writes no manifest shard.
      (repo: deployment-service)

- [ ] [OPERATOR] P1. **BLOCKED-OPERATOR — the Betfair credentials in GSM are INVALID; this now blocks todo 4, and
      no further egress work can fix it.** With the europe-west2 path proven above, `refresh_betfair_session_token.py`
      was re-run there against the REAL shipped code and got past the network entirely — reaching Betfair's
      authentication layer and returning a genuine API error:
      `betfairlightweight.exceptions.LoginError: API login: INVALID_USERNAME_OR_PASSWORD` (`REFRESH_RC=1`). All three
      source secrets read fine (`betfair-username` 23 chars, `betfair-password` 9 chars, `betfair-app-key` 33 chars),
      so this is NOT a GSM/IAM gap — the stored username/password simply do not authenticate.
      **`betfair-session-token` therefore still has ZERO versions.** Operator action needed: verify / reset the
      account password and update the `betfair-password` (and `betfair-username` if it changed) secret, OR confirm
      whether this account requires Betfair's CERTIFICATE (non-interactive) login rather than `login_interactive()`
      — an account with 2FA enabled cannot use the interactive flow at all.
      **HARD — do NOT retry the login to "check" it.** Betfair locks an account after a small number of consecutive
      failed logins, and unlocking a real-money account is operator/account-holder-only. Exactly ONE attempt has been
      made (2026-08-11, slot-18); treat that budget as spent until the credentials are actually changed.
      (repo: none — operator / account-holder action)

## Progress Log

- 2026-08-09 (slot-17, backend_engineer): filed this issue doc after discovering the dispatched todo's premise (existing
  scaffold) was invalidated by an intervening dead-code deletion; recovered the deleted file's content via git history
  for the next worker's use (embedded above); did not implement anything in market-tick-data-service this session — see
  the parent plan's Progress Log for the pointer back here.
- 2026-08-09 (slot-3, backend_engineer): completed todo 1 — restored `betfair_adapter.py` verbatim + re-added its
  `BetfairAdapter` imports/exports to both `__init__.py` files (Matchbook left deleted, out of scope). QG green, shipped
  `market-tick-data-service@fc9e36cd`. Todos 2-4 (download_batch shim, fixture_id resolution, live-verify) remain open
  for the next worker.
- 2026-08-09 (slot-5, backend_engineer): **todo 2 implemented, NOT YET SHIPPED** — checkpointing at context-limit before
  a forced `/compact`. Chose the `download_batch()`-shim approach per this doc's own recommendation. Work is UNCOMMITTED
  in this slot's own dedicated worktree (`.tabs/5/market-tick-data-service`, not shared — safe from cross-slot loss) — a
  fresh session picking up this todo should read the working-tree diff there before re-doing the research below.
  - `betfair_adapter.py`: `_convert_catalogue_to_market` now also returns `runners` (selection_id + runner_name from the
    `RUNNER_DESCRIPTION` projection already requested) + `event_type_name`/`competition_name`; `get_markets` gained an
    optional `market_start_time: (from_iso, to_iso)` window param (Betfair's `listMarketCatalogue` has no historical
    endpoint — always reflects the live catalogue, so a batch call needs a start-time window, not a date param, to scope
    to one day). New `download_batch(date, data_types, leagues)`: joins `get_markets()` catalogue+runners against
    per-market `get_prices()` back/lay levels; `lay_price` populated ONLY when the market's lay book is COMPLETE (every
    runner with a back price also has a lay price) — a partial book leaves `lay_price` unset for the WHOLE market, per
    `features-service@d792f421`'s read-side contract. `fixture_id`/`af_fixture_id` are honestly left unresolved
    (`FixtureMatchStatus.NO_FIXTURE_DATA`, falling back to Betfair's own `event_id`/`market_id` — the same "attempted,
    unresolved" pattern `OddsApiAdapter` itself uses) — real fixture resolution stays todo 3's scope, confirmed
    genuinely hard: a VCR-cassette-recorded real catalogue response shows Betfair match-odds runners are generic
    "Home"/"Draw"/"Away" labels, not team names — team names only exist as free text in `event.name` ("Man Utd v
    Liverpool"), no established parser.
  - `factory.py`: added `"betfair": ("sports", BetfairAdapter)` to `VENUE_REGISTRY`, removed the old
    `"betfair": "prediction_market"` entry from `PLANNED_VENUES`.
  - `umi_tick_provider.py`: fixed the ACTUAL dispatch blocker todo 2's own text didn't anticipate — `_route_sports()`'s
    `cast(OddsApiAdapter, ...)` was a type-hint only (no runtime effect, widened to `OddsApiAdapter | BetfairAdapter`),
    but `_SPORTS_VENUES = frozenset({"ODDS_API"})` (a hardcoded gate BEFORE `_route_sports` is ever called) would have
    silently dropped every `--venue betfair` capture call even with the factory wired — added `"BETFAIR"` to that set.
    Without this fix the factory wiring alone would NOT have made Betfair capture actually dispatchable.
  - **New open question for todo 4 (live-verify), NOT resolved this session**: UAC's registries
    (`_sports_venue_constants.py`, `_odds_api_maps.py`, `data_availability.py`) already reference
    `BETFAIR_EX_UK`/`BETFAIR_EX_EU` as the canonical per-region data-axis venue names for the exchange (bare `BETFAIR`
    described elsewhere as "operator-group parent, not data-axis" — `representative_sample.py`), separate from
    Odds-API's own aggregated view of Betfair prices (different pipeline). This todo's own instruction said literally
    `"betfair"` for the `VENUE_REGISTRY` key, which is what's implemented — but todo 4's live-verify pass should confirm
    whether the manifest/asset-group/bucket routing expects bare `BETFAIR` or the region-qualified
    `BETFAIR_EX_UK`/`EX_EU` forms before trusting a live capture's shard path is correct, not just that the HTTP calls
    succeed.
  - Tests: `tests/unit/test_betfair_adapter.py` (9 tests, all passing via a direct `.venv` pytest run — complete/partial
    lay-book gating, no-back-price skip, leagues filter, shard-level isolation on a `get_prices` exception, honest
    fixture_id fallback, factory registration). NOT yet verified via the canonical `quality-gates.sh` gate — the full
    run hit the SAME shared-host contention (load avg 20-28, many concurrent slots' QG runs) that repeatedly killed
    background QG processes on this host earlier today; one full run DID complete and caught one real lint fix (a bare
    `# noqa` ruff flagged as unused — fixed), but the re-run after that fix was killed mid-run before completion.
  - **Next step for whoever resumes**: re-run `bash scripts/quality-gates.sh --no-fix` from
    `.tabs/5/market-tick-data-service` (retry if killed again — this is host contention, not a code defect signal); on
    green, commit + quickmerge + flip this doc's todo 2 + `/done` the dispatched task
    (`prediction_satellite_ao_dispatch_batch6-a878572ff8da`,
    `plan_ref: plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md` — per slot-17's scope-correction
    note, the PARENT plan's todo stays unchecked; only this issue doc's todo 2 flips).
- 2026-08-09 (slot-5, backend_engineer, continued after resume — the worktree WIP above was lost when the session died
  mid-checkpoint; reconstructed verbatim from this Progress Log entry, re-verified via the same 9 local tests, no
  content drift): full `quality-gates.sh` PASSED on commit `06387b04` (310s). One real pre-existing test failure caught
  (not host-contention) — `test_prediction_market_venue_wiring.py::test_remaining_planned_venues` asserted the old
  `"betfair" in PLANNED_VENUES` state; fixed. A second real gate failure caught: `download_batch` (128L) and
  `get_markets` (59L) exceeded `MAX_METHOD_LINES=50` — refactored (extracted `_post_rpc` shared JSON-RPC helper,
  `_market_matches_leagues`, `_row_for_runner`, `_rows_for_market`); pure refactor, all 9 tests still passing. **Shipped
  `market-tick-data-service@85872cab`, verified ancestor of `origin/live-defi-rollout`.** Todo 2 flipped above. Todos 3
  (fixture_id resolution) and 4 (live-verify, incl. the `BETFAIR_EX_UK`/`EX_EU` venue-naming question) remain open for
  the next worker.
- 2026-08-09 (slot-26, backend_engineer): **todo 3 implemented + shipped** — `market-tick-data-service@766e776d`
  (details embedded in the flipped todo 3 above). Wired `BetfairAdapter` into the existing `FixtureIdResolver` (no new
  resolution path needed, confirming the todo's own open question) via a new team-name/league-name projection off
  `event_name`/`competition_name`; found + used a previously-unwired UAC helper (`parse_betfair_event_teams`, shipped
  earlier but never called from anywhere) that already does exactly the "Team A v Team B" free-text parse the prior
  progress-log entries (slot-17, slot-5) had flagged as "no established parser" — it existed, it just hadn't been wired
  to a caller yet. Full `quality-gates.sh` green (267s, 10409/0 failed). Todo 4 (live-verify against a real Betfair
  catalogue response) remains open — this session's resolution logic is unverified against real API data (only a
  synthetic test fixture), see the caveat on todo 3 above.
- 2026-08-09 (slot-15, backend_engineer): dispatched to this issue doc's todo 3 via the parent plan's original P2 item.
  Implemented it independently (team-name split from `event.name` on " v ", a `resolve_af_league_id_from_betfair_names`
  competition-name matcher in `fixture_id_resolver.py` with a country-code disambiguation table, `FixtureIdResolver`
  wiring into `download_batch`) — but on the fresh-pull before shipping, discovered **slot-26 had landed the identical
  scope moments earlier AND already flipped this todo's checkbox above with a full writeup**:
  `market-tick-data-service@766e776d`, using UAC's own shared
  `unified_api_contracts.external.betfair.normalize.parse_betfair_event_teams` for the team split (cleaner than my local
  regex — no Betfair-specific parsing reinvented) plus an equivalent exact-then-substring `_resolve_af_league_id` league
  matcher with the same country-disambiguation approach. Per RULES.md's "never delete another agent's already-landed
  content" rule, discarded my own conflicting stash entirely (`git restore --source=HEAD` on the three touched files)
  rather than force my version over theirs — genuine duplicate-work collision, not a content dispute; their commit is
  git-verified ancestor of `origin/live-defi-rollout` and the full `tests/unit/test_betfair_adapter.py` suite (15 tests)
  passes clean at that HEAD. No further action needed on todo 3. Todo 4 (live-verify, incl. the `BETFAIR_EX_UK`/`EX_EU`
  venue-naming question) remains the sole open item.
- 2026-08-09 (slot-8, backend_engineer): dispatched to todo 4 (live-verify). **Premise invalidated, same pattern as
  slot-17's original scope-correction** — the dispatched task text asserted `betfair-session-token` was "now-live"
  citing `execution-service@7e03bf7b`, but that commit only shipped the refresh SCRIPT
  (`execution-service/scripts/refresh_betfair_session_token.py`); nobody had ever actually run it, and the
  `betfair-session-token` secret did not exist in GSM at all (confirmed via both
  `gcloud secrets list --project central-element-323112` and the codebase's own
  `unified_trading_library.cloud_interface.get_secret` — "Secret 'betfair-session-token' not found"). Also found the
  script's `_PROJECT` default was wrong (`unified-trading-prd`, a project this workspace has no access to / that may not
  exist) — the real project is `central-element-323112` (confirmed against
  `unified_trading_library/instruments_catalog_reader.py::PROJECT_ID` and every other GSM-reading script in the
  workspace). Fixed that default and shipped it (`execution-service@b97abbd9`, full `quality-gates.sh` green, verified
  ancestor of origin) — a real, if small, bug: without it the script silently targets an inaccessible project unless the
  operator remembers to set `GCP_PROJECT`.

  With the default fixed, self-serviced the actual provisioning gap per RULES.md's IAM-self-service pattern (had
  `roles/secretmanager.admin` on the ambient `unified-trading-sa` identity already) — created the empty
  `betfair-session-token` secret container
  (`gcloud secrets create betfair-session-token --project central-element-323112`), then ran the refresh script. **It
  failed — not on credentials, on network.** Betfair's `identitysso.betfair.com/api/loginInteractive` (and `/api/login`)
  endpoints returned HTTP 403 with an explicit Betfair-authored "Restricted" page: _"Our Software detects that you may
  be accessing the Betfair website from a country that Betfair does not accept bets from or the traffic from your
  network was detected as being unusual."_ Verified this is not a `betfairlightweight`-wrapper artifact by hitting the
  raw endpoint directly with `requests` — identical 403 + body. The egress IP is `13.113.200.22` — per
  `runtime-deployment-topology.md` this is literally the single orchestrator VM's EIP (`asia-northeast1`/Tokyo), i.e.
  this workspace's ONLY current live network egress path for ANY worker session, not something scoped to this slot.
  `betfair-username`/`betfair-password`/`betfair-app-key` all load fine (so this is not a credential problem) — the
  account itself may simply never have logged in from a non-UK/EU IP before and Betfair's fraud/geo heuristic is
  rejecting the whole request before credentials are even checked.

  **Why this is BLOCKED-OPERATOR-DECISION, not a worker judgment call**: fixing this means either (a) provisioning new
  network egress in a Betfair-accepted jurisdiction — the workspace already has GCP infra in `europe-west4`
  (`/codex/05-infrastructure/launcher-script-ssot.md`, `/codex/05-infrastructure/agent-orchestrator-deploy.md`) that's a
  plausible candidate, but standing up a new egress path (proxy/relay/VM) for a real gambling-account login is a cost +
  compliance decision (accessing a betting account from a jurisdiction/IP it's never used before risks the account's OWN
  fraud/ToS triggers on Betfair's side, separate from this workspace's infra) — not something a worker should decide
  unilaterally per `/codex/04-architecture/capital-structure-and-regulatory.md`'s jurisdiction-sensitivity around this
  exact account; or (b) contacting Betfair support to whitelist/confirm the account for this access pattern, which is an
  operator/account-holder action by definition. Neither is a checkable-fact/small-scoped-change a worker can resolve
  alone.

  **Left the created `betfair-session-token` secret container in place** (empty, zero versions — harmless, and it's the
  correct provisioning step regardless of how the network question resolves; the source-credential secrets it depends on
  were unaffected). Did NOT touch factory.py/adapter code (todos 1-3's shipped work is unaffected and correct — this is
  purely a network-reachability blocker on the verification step, not a defect in the adapter itself). Filed `/blocked`
  for the operator's network-routing decision. Todo 4 stays unchecked; the satellite plan's original P2 item and
  `prediction_arb_live_execution_bridge_2026_07_20.md` item [5] stay untouched pending its resolution.
  - 2026-08-10 (slot-25, backend_engineer): **Independent verification of the 2026-08-09 geo-restriction finding.**
    Dispatched to the parent plan's original P2 item [5]; confirmed todos 1-3 all shipped + green at current
    `origin/live-defi-rollout` HEAD. The `betfair-session-token` secret container exists (empty, zero versions). Re-ran
    `uv run python scripts/refresh_betfair_session_token.py` — same HTTP 403 from
    `identitysso.betfair.com/api/loginInteractive` (via `betfairlightweight.APIClient.login_interactive()`), same
    Betfair-authored "Restricted" page body slot-8 documented. Credentials load fine (username/password/app-key all
    resolved from GSM); this is purely geo/traffic restriction on the orchestrator VM's Tokyo EIP `13.113.200.22`.
    Option A (provision europe-west4 egress) was explicitly NOT granted by the operator on main-agent review —
    jurisdiction/compliance risk to the real gambling account. Todo 4 stays BLOCKED-OPERATOR-DECISION; the two real
    paths are (A) operator-provisioned egress/relay in a Betfair-accepted jurisdiction, or (B) contact Betfair
    support/account holder to whitelist the Tokyo IP. Code is ready — the adapter, routing, fixture resolution, and
    session-token refresh mechanism are all shipped and green. Skipping this task; the parent plan's item [5] stays
    unchecked until the operator resolves the network question.
  - 2026-08-10 (slot-19, backend_engineer): **dispatch #7 of the parent plan's original P2 item [5].** Fresh
    verification — all 3 shipped SHAs (`market-tick-data-service@fc9e36cd`/`@85872cab`/`@766e776d`) still ancestors of
    `origin/live-defi-rollout`, `tests/unit/test_betfair_adapter.py` present, and `betfair-session-token` still **0
    versions** (empty). No change since slot-25/slot-11's findings: same Tokyo-egress geo-block (403 Restricted), same
    empty token. Rather than skip (which re-arms immediate re-dispatch to the next slot — the mechanism behind 6+
    dispatches of this same item across slots 17/5/15/8/25/11), posted **`/blocked` (BLK-2c74f86d)** to HOLD the task
    and stop the re-dispatch churn until the operator makes the disposition call: **A)** re-scope/descope the
    live-verify (accept the shipped code + synthetic persistence verification as done), **B)** provision
    Betfair-accepted egress (not europe-west4), or **C)** park the todo open. Recommended A. Task held in
    `status: blocked` — no `/done`, no skip, no false completion.
  - 2026-08-10 (main, BLK-2c74f86d): **ruling — option C, disposition=partial.** Todo 4 stays OPEN + BLOCKED-OPERATOR-
    DECISION (flipping it `[x]` now would be false-progress while the operator decision is pending); accept todos 1-3 as
    complete shipped work. Egress stays operator-owned: europe-west4 NOT granted (cost + compliance + Betfair ToS/fraud
    risk to the real gambling account per `capital-structure-and-regulatory.md`); Betfair-support whitelist of Tokyo EIP
    13.113.200.22 is an operator/account-holder action. **Churn permanently stopped**: parent batch6 item [5] is tagged
    `[BLOCKED-OPERATOR-DECISION]` (slot-11 `7f1ad66ffd`) → `_is_non_dispatchable` = True; the stale derived task
    `prediction_satellite_ao_dispatch_batch6-a878572ff8da` is cancelled + orphaned (regen re-derives 0 open todos from
    the batch6 plan); future dispatches will not land here. Re-open only if/when the operator resolves the
    network/egress question.
  - **2026-08-11** (operator decision, via main, part of an AO-dispatch-visibility gate unblocking pass): re-opened the
    network/egress question. Operator declined to reverse the `europe-west4` decline but delegated picking a
    Betfair-accepted region; researched via sub-agent and determined `europe-west2` (London) is the correct choice —
    it's the only GCP EU region whose IP geolocation matches the credential's actual UK jurisdiction, which is the
    mismatch that got both Tokyo and `europe-west4` 403'd (Belgium/`europe-west1` carries the same mismatch risk despite
    being cheaper). Retagged todo 4 from `BLOCKED-OPERATOR-DECISION` to `OPERATOR-DECIDED`, now AO-dispatchable.
    Provisioning the actual `europe-west2` egress path is not done in this session.
  - **2026-08-11** (slot-20, backend_engineer): dispatched to the parent plan's original P2 item. Retagged todo 4 above
    from `[BACKEND]` to `[INFRA]` — provisioning a new network egress (VM/proxy in `europe-west2`) is `infra` craft's
    domain per `backend_engineer.md`'s `does_not` list ("Infra provisioning, VM launches, CI/CD, cloud (→ infra)"), not
    something a backend_engineer worker should do itself per the craft-scoping rule. Mirror retag applied to the parent
    plan's item. No egress provisioned this session; skipping the dispatched task so it redispatches to an `infra`-craft
    worker.
  - **2026-08-11** (slot-18, data_engineering adopting the `[INFRA]` craft per `worker.md`'s craft-adopt rule):
    **egress provisioned + PROVEN; the blocker has MOVED from network to credentials.** Two new todos above capture
    it. Sequence: (1) launched a throwaway probe VM in `europe-west2-a` and curled both Betfair endpoints — got
    **405** and **400 `DSC-0008`** where Tokyo gets 403 + "Restricted", so the region choice the operator delegated
    on 2026-08-11 is measurably correct, not just plausible; (2) reserved the regional static address
    `betfair-egress-ip` = `34.39.85.36` and launched a real egress VM on it running execution-service's OWN shipped
    `refresh_betfair_session_token.py` (passed in by metadata, not a reimplementation, so the verification is of the
    real path); (3) it read all three GSM credential secrets successfully, called `login_interactive()`, and Betfair
    answered `INVALID_USERNAME_OR_PASSWORD`. **That error is the good news and the bad news**: it can only be
    produced by a request that reached Betfair's auth layer, which is the proof the geo-block is gone — and it means
    the credentials themselves are wrong, so `betfair-session-token` still has 0 versions and todo 4's live-verify
    remains genuinely undone. I did NOT retry (Betfair locks accounts on consecutive failures; real-money account).
    Both throwaway VMs were deleted after their evidence was captured; only the reserved static IP persists
    (~$7/mo unattached — kept deliberately, since a stable IP is the property Betfair's fraud heuristics care about
    and re-rolling it would invalidate this session's measurement).
    **Concurrency note — a peer effort exists, left untouched**: `lc_singleton_check` in my new launcher refused
    its own first dry-run because `betfair-egress-proxy-20260811-211046` (e2-micro, `tier: daemon`,
    `purpose: betfair-egress-proxy`, ephemeral IP `35.230.151.99`, created 21:10 UTC — ~50 min before this session)
    was already RUNNING in `europe-west2-a`. That is another agent's in-flight PROXY-design egress, not mine; per
    RULES.md I did not delete, modify, or reuse it, and my launcher deliberately singleton-guards against it so the
    two designs can never issue concurrent Betfair logins. **Whoever owns that proxy should read the credential
    finding above before investing further in proxy plumbing — a working proxy still returns
    `INVALID_USERNAME_OR_PASSWORD`.** If the proxy design is the one kept, attach `betfair-egress-ip` to it rather
    than leaving it on an ephemeral IP.
