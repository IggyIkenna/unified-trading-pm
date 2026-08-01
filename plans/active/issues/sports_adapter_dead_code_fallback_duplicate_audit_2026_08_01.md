---
doc_type: issue
title:
  "Sports adapter dead-code/fallback/duplicate audit (per adapter-dead-code-and-fallback-ban.md) — 14 findings across
  instruments-service, market-tick-data-service, execution-service"
summary: >-
  Read-only audit of every adapter/handler module under instruments-service's
  `reference_data/adapters/sports/adapters/`, market-tick-data-service's `market_interface/adapters/sports/`, and
  execution-service's `sports_execution/adapters/`, per
  `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md` (rule 1 dead code / rule 2 silent runtime fallback
  / rule 3 undocumented duplicate implementation). 14 findings total: 3 in instruments-service (2 are the SAME
  already-known bug class this codebase explicitly hardened against elsewhere — a swallowed fetch failure recorded as
  honest-absence instead of `attempted_failed` — left unfixed in `open_meteo.get_weather_match_window` and
  `api_football.get_standings`), 6 in market-tick-data-service (5 dead adapter classes reachable only through a
  secondary `sports/registry.py` dispatch table that itself has zero production callers, one of them — sports
  `PolymarketAdapter` — also an undocumented duplicate of the live-routed `prediction.PolymarketAdapter`; plus a silent
  schema-validation fallback in `FootystatsAdapter`), and 5 in execution-service (2 dead adapters, a repeated `except
  Exception: pass` swallow of the capability-preflight check immediately before 7 real-money order
  placement/cancellation call sites across 4 files, `OneXBetAdapter` advertised as a supported venue in
  `sports_handler.py` but never actually constructible, and a stale/factually-incorrect Kalshi stub contradicting the
  live `KalshiAdapter`'s real secret-naming convention).
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, execution-service, unified-trading-pm]
scope: [engineer]
tags: [sports, adapter-dead-code-and-fallback-ban, dead-code, silent-fallback, duplicate-adapter, audit, honest-absence]
related:
  [
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-08-01
last_updated: 2026-08-01
priority: P1
parent_epic: sports_master
source:
  "Track X audit todo, sports_consolidated_native_ao_extract_2026_07_25.md item 10 (source:
  sports_consolidated_closeout_2026_07_19.md:770-773) — worked by slot 6, backend_engineer, 2026-08-01"
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
locked_since:
depends_on: []
supersedes:
superseded_by:
context_scope:
  [
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
  ]
---

# Sports adapter dead-code/fallback/duplicate audit — 14 findings

## What I found

Per the source todo, this was a **read-only** audit (no code changes in this task) of every adapter/handler module under
the three named directories, checked against `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`'s three
rules (no dead code / no silent runtime fallback masking a real failure / no undocumented duplicate implementation).
Full per-file methodology and the compliant files already checked off (so a future worker doesn't re-check them) are
preserved in the Progress Log below; this section lists only the findings.

### instruments-service — `reference_data/adapters/sports/adapters/` (3 findings)

1. **`open_meteo.py::OpenMeteoAdapter.get_weather_match_window`** (lines 124-312, specifically the exception handlers at
   207-214, 235-273, and the outer catch-all at 284-286) — never re-raises on failure at any of its three nested
   exception layers; the outer catch-all logs via `_emit_fetch_failed` but then falls through and returns a
   partial/degraded result as if it were a normal one. The caller (`engine/orchestrator/weather.py:364-395`) is built to
   catch a raised failure and route it to `attempted_failed` via `_record_weather_failed`; because the adapter never
   raises, a genuine fetch failure is instead recorded as an honest `empty_confirmed` gap. This is the exact bug class
   (`false empty_confirmed` masking a real fetch failure) that `api_football.py`'s other per-entity methods were
   explicitly hardened against (see the file's own `api_football_injuries_silent_empty_swallow_2026_07_13` /
   `api_football_per_fixture_hard_failure_silently_recorded_empty_2026_07_25` fix-comments) — left unfixed here.
2. **`api_football.py::ApiFootballAdapter.get_standings`** (lines 714-728) — unlike every sibling per-entity fetch
   method in the same file (`get_fixtures`, `get_leagues`, `get_teams`, `get_injuries`, `get_fixture_statistics`,
   `get_fixture_events`, `get_fixture_lineups`, `get_fixture_player_stats`, all of which `raise` after
   `_emit_fetch_failed`), `get_standings` swallows the failure and `return []`. The caller
   (`engine/orchestrator/sports_reference_core.py::_fetch_and_cache_standings`, lines 584-604) expects a raise to route
   to `hooks.note_failed`; since it never fires, a failed league is silently recorded as an honest gap instead of
   `attempted_failed` — same bug class as finding 1.
3. **`open_meteo.py::OpenMeteoAdapter.get_weather`** (lines 71-122) — fully implemented, zero callers anywhere in the
   repo, not part of `BaseSportsReferenceAdapter`'s abstract interface. Production weather capture goes exclusively
   through `get_weather_match_window`. No "registered but intentionally unreached" note exists for it, unlike this
   codebase's own precedent for that pattern (e.g. `adapters/tradfi/ibkr.py`'s explicit unreached-note, or `router.py`'s
   inline `# unreached — see below` annotations).

### market-tick-data-service — `market_interface/adapters/sports/` (6 findings)

Scope note carried into the fix todos below: the live production sports dispatch path is
`umi_tick_provider.py::_route_sports()` → `factory.VENUE_REGISTRY`, which contains exactly one sports entry
(`"odds_api": OddsApiAdapter`). A second, parallel table (`market_interface/sports/registry.py::_ADAPTER_PATHS`,
resolved via `resolve_adapter_class()`/`adapter_for_bookmaker()`) has **zero non-test callers anywhere in the
workspace** — findings 4-6 below are all only "registered" through this dead secondary table.

4. **`betfair_adapter.py::BetfairAdapter`** (line 45) and **`matchbook_adapter.py::MatchbookAdapter`** (line 23) — both
   imported into `market_interface/__init__.py` but absent from `factory.VENUE_REGISTRY`; `sports/registry.py`'s
   `_ADAPTER_PATHS` resolves the same venue keys to the DIFFERENT, live-routed
   `execution_service.sports_execution.adapters.exchanges.{betfair,matchbook}` classes instead. `sports/registry.py`'s
   own module docstring already documents "active sports adapter classes live in
   `execution_service.sports_execution.adapters.*`" — so this is pure rule-1 dead code (the duplicate-vs-rule-3 question
   is already answered at the codebase level), reached only by `tests/market_interface/unit/test_sports_adapters.py`.
5. **`metabet_adapter.py::MetaBetAdapter`** (line 30), **`odds_engine_adapter.py::OddsEngineAdapter`** (line 31),
   **`opticodds_adapter.py::OpticOddsAdapter`** (line 28) — the resolved targets of `sports/registry.py`'s
   `_ADAPTER_PATHS`, but that registry's only entry points have zero production callers (see scope note above); the one
   real live sports dispatch path is hard-cast to `OddsApiAdapter` only. Each carries
   `ENDPOINT_STATUS = "PENDING_CASSETTE_AWAITING_AUTH"` (documents WIP-implementation status) but nowhere documents that
   the registry mechanism meant to reach them is itself unreachable.
6. **`footystats_adapter.py::FootystatsAdapter`** (line 90) and **`sportradar_adapter.py::SportradarAdapter`** (line 59)
   — both marked `ENDPOINT_STATUS = "IMPLEMENTED"` (not WIP) yet registered nowhere at all: absent from
   `VENUE_REGISTRY`/`PLANNED_VENUES`, absent from `sports/registry.py`, absent from `adapters/sports/__init__.py`'s
   `__all__`, absent from `market_interface/__init__.py`'s import list. Reached only by their own dedicated integration
   tests. The purest form of rule 1 — fully-built, "IMPLEMENTED" adapters with literally no route to production and no
   comment explaining the gap.
7. **`polymarket_adapter.py::PolymarketAdapter(BaseSportsAdapter)`** (line 56, the sports-package version) — exported
   via `adapters/sports/__init__.py`'s `__all__` but deliberately NOT imported by `market_interface/__init__.py`, which
   instead imports the structurally different `adapters.prediction.PolymarketAdapter` (extends `BasePredictionAdapter`,
   has CLOB fetch/retry/CF-11 machinery) for the same live symbol name (`VENUE_REGISTRY["polymarket"]`,
   `factory.py:188`). No comment anywhere in either file, or either package's `__init__.py`, addresses why two
   `PolymarketAdapter` classes coexist — a genuine **rule 3** violation (silence on which is live-routed) in addition to
   rule-1 dead code (reached only by `tests/market_interface/unit/test_sports_polymarket_adapter.py`).
8. **`footystats_adapter.py::FootystatsAdapter`** — `get_leagues` (lines 137-138), `get_matches` (172-173), `get_teams`
   (196-197) each catch a pydantic/schema `model_validate()` failure
   (`except (ValueError, KeyError, TypeError): results.append(dict(item))`) and silently substitute the raw, unvalidated
   dict for the caller with **no logging at all** — inconsistent with every other exception handler in the same file
   (including this adapter's own `_footystats_get()`, lines 74-87, which correctly logs+reraises on transport failure).

### execution-service — `sports_execution/adapters/` (5 findings)

9. **`aggregator/odds_api.py::OddsApiAdapter`** (line 90) — registered in `routing.py`'s
   `SportsExecutionRouter._build_adapter()` dispatch table (`data_source == "odds_api_aggregator"`, a declared
   `SupportedDataSource` literal) but the only production caller that builds a `SportsExecutionRouter`
   (`adapters/sports_factory.py::_create_live_sports_adapter`) hardcodes `_LIVE_VENUE_CONFIGS` to only
   `{betfair, matchbook, kalshi, polymarket}` — no live config ever sets `data_source="odds_api_aggregator"`. Reached
   only by `tests/sports_execution/unit/test_routing.py`.
10. **`bookmaker_api/api_football.py::ApiFootballAdapter`** (line 140) — re-exported through the adapters package's
    public `__all__` but never constructed anywhere outside its own docstring usage example (a comment, not executable
    code); absent from `routing.py`, `sports_factory.py`, and `sports_handler.py`'s `BOOKMAKER_VENUES`. No note stating
    intentional unwired status (contrast the `unity/__init__.py` package, which DOES document its stub status — see
    Progress Log for the compliant precedent).
11. **`bookmaker_api/onexbet.py::OneXBetAdapter`** (line 49) — re-exported publicly, and `sports_handler.py` explicitly
    lists `"ONEXBET"` in `BOOKMAKER_VENUES`/`SUPPORTED_VENUES`/`DEFAULT_FEES` (implying live support), but zero
    production construction sites exist anywhere. The handler's only live-execution path delegates to
    `config["sports_router"]`, whose only concrete `SportsRouter` class (`adapters/sports_router.py`) has an empty
    `_BOOKMAKER_VENUES` default and no `.execute()` method — it cannot place a 1xBet bet. The venue is advertised as
    supported but nothing can actually service it.
12. **Capability-preflight failures silently swallowed before 7 real-money order-placement/cancellation call sites, 4
    files** — identical `except Exception: pass  # Graceful degradation — registry may not be bootstrapped` pattern
    wrapping `validate_operation(...)` (only `UnsupportedOperationError` is re-raised; every OTHER exception from
    `unified_api_contracts.registry.capability.validate_operation()` — e.g. `CapabilityResolutionError`,
    `UnsupportedModeError`, `UnsupportedEnvironmentError` — is swallowed with **zero logging**):
    - `exchanges/betfair.py:493-498` (`BetfairAdapter.place_bet`)
    - `exchanges/betfair_order_mapping.py:128-133` (`_BetfairCanonicalOrderMixin.place_order`)
    - `exchanges/betfair_order_mapping.py:212-217` (`_BetfairCanonicalOrderMixin.cancel_order`)
    - `exchanges/kalshi.py:223-228` (`KalshiAdapter.place_bet`)
    - `exchanges/kalshi.py:305-310` (`KalshiAdapter.cancel_bet`)
    - `exchanges/kalshi.py:415-420` (`KalshiAdapter.place_order`)
    - `exchanges/polymarket_clob.py:226-237` (`PolymarketCLOBAdapter._validate_create_order`)

    These are exactly the safety preflight checks meant to block an unsupported env/operation (e.g. a mainnet order in
    an env that shouldn't support it) before a real order is placed or cancelled — with no runtime observability if this
    path fires in production. The same textual pattern also appears outside the audited directory
    (`instruction_router.py`, `defi_execution/protocols/base.py`, MTDS `factory.py`), suggesting it may be a
    workspace-wide convention rather than a one-off — flagged as its own sub-finding below so it isn't silently
    generalized without a decision.

13. **`prediction_markets/kalshi.py::KalshiAdapterConfig`** (lines 19-24, docstring lines 1-9) — a stub whose docstring
    claims "Full implementation pending Kalshi API key provisioning" and "Kalshi does NOT split key/secret into two
    separate secrets... verified live 2026-07-23", with `secret_name: str = "kalshi-api-credentials"` (one combined
    secret). This directly contradicts the ACTUAL live `exchanges/kalshi.py::KalshiAdapter`, which is fully built, wired
    live via `sports_factory.py:39-44` (`_LIVE_VENUE_CONFIGS`), and uses **two** separate secrets (`kalshi-api-key-id`,
    `kalshi-private-key-pem`). Neither file references the other. Contrast the sibling
    `prediction_markets/polymarket.py` stub, which DOES correctly state its own not-yet-wired relationship to the live
    adapter — so the convention exists in the same package but wasn't applied/updated here after `KalshiAdapter` went
    live.

## Why it matters

Findings 1-2 (instruments-service) are silent-fallback bugs that directly corrupt data-pipeline correctness signal —
they make a real, unrecovered API/parse failure indistinguishable from a genuine "the source has zero rows for this
entity" honest absence, which is the exact class of bug this codebase has already spent real effort hardening
`api_football.py`'s OTHER methods against. Per CLAUDE.md, "data pipeline correctness is the heartbeat" and these are
exactly the kind of gap a RED data audit is meant to catch.

Finding 12 (execution-service capability-preflight swallow) sits directly in front of 7 real-money order
placement/cancellation call sites across `betfair.py`, `betfair_order_mapping.py`, `kalshi.py`, and `polymarket_clob.py`
— a capability-registry failure that should block an unsupported operation can instead silently let it through with zero
log signal.

Findings 3-11, 13 are dead-code / undocumented-duplicate findings per rule 1 and rule 3 — lower urgency but each is a
concrete instance of "nobody knows which of two things actually runs" (Findings 7, 13) or "fully-built code with no
route to production and no explanation" (Findings 3, 5, 6, 9, 10, 11), which is precisely what
`adapter-dead-code-and-fallback-ban.md` was written to close.

## Recommended decision

Per the source todo's own done-when ("a written per-repo finding list... exists"), this task is audit-only — no code
changes were made. Each finding below is filed as its own scoped, worker-determinable fix todo (repo named, symbol
named) rather than left as prose, per the findings-closure hard rule.

- [x] ✅ [BACKEND] P1. Fix `open_meteo.py::OpenMeteoAdapter.get_weather_match_window` (instruments-service) so every
      exception layer that currently only logs (lines 207-214, 235-273) either re-raises or is folded into the existing
      outer `_emit_fetch_failed` catch-all (lines 284-286), and make the outer catch-all itself `raise` after logging
      instead of falling through to return a partial result — matching the `raise`-after-`_emit_fetch_failed` pattern
      already used by every sibling method in `api_football.py`. (repo: instruments-service) —
      instruments-service@08e74647. Made all three nested exception handlers (Previous Runs API, actual-weather fetch,
      its 400-retry fallback) `raise` after logging instead of swallowing, and the outer catch-all `raise` after
      `_emit_fetch_failed` instead of falling through to return a partial result. Updated the 3 unit tests in
      `test_sports_open_meteo_boost.py` that asserted the old swallow-and-continue behavior to assert
      `pytest.raises(...)` + `_emit_fetch_failed` called instead. Full QG green (5133 passed).
- [x] ✅ [BACKEND] P1. Fix `api_football.py::ApiFootballAdapter.get_standings` (lines 714-728) to `raise` after
      `_emit_fetch_failed` instead of `return []`, matching every sibling per-entity fetch method in the same file
      (`get_fixtures`, `get_leagues`, `get_teams`, `get_injuries`, `get_fixture_statistics`, `get_fixture_events`,
      `get_fixture_lineups`, `get_fixture_player_stats`). Verify `_fetch_and_cache_standings`'s existing
      `except Exception` (`sports_reference_core.py:592-604`) then correctly routes to `hooks.note_failed`. (repo:
      instruments-service) — instruments-service@d182b503 (fix) + @64148070 (updated `test_get_standings_empty_on_error`
      → `test_get_standings_error_propagates`, the old test asserted the swallowed behavior). Verified
      `_fetch_and_cache_standings` (sports_reference_core.py:592-604) already catches `Exception` and calls
      `hooks.note_failed` — no caller change needed. Full QG green (5133 passed).
- [ ] [BACKEND] P3. `open_meteo.py::OpenMeteoAdapter.get_weather` (lines 71-122, instruments-service) — either delete
      (zero callers, not part of the abstract interface) or add an explicit "registered but intentionally unreached"
      note matching this codebase's own precedent (`adapters/tradfi/ibkr.py`'s unreached-note style). (repo:
      instruments-service)
- [ ] [BACKEND] P2. Delete `betfair_adapter.py::BetfairAdapter` and `matchbook_adapter.py::MatchbookAdapter`
      (market-tick-data-service `market_interface/adapters/sports/`) — both are dead code superseded by the live-routed
      `execution_service.sports_execution.adapters.exchanges.{betfair,matchbook}` classes per `sports/registry.py`'s own
      docstring; remove their imports from `market_interface/__init__.py` and their exports from
      `adapters/sports/__init__.py`, and update/delete `tests/market_interface/unit/test_sports_adapters.py`'s
      references accordingly. (repo: market-tick-data-service)
- [x] ✅ [BACKEND] P2. Decide + document the fate of `market_interface/sports/registry.py`'s `_ADAPTER_PATHS` dispatch
      table (market-tick-data-service) — it has zero production callers, making `metabet_adapter.py::MetaBetAdapter`,
      `odds_engine_adapter.py::OddsEngineAdapter`, and `opticodds_adapter.py::OpticOddsAdapter` unreachable dead code.
      Either wire the registry into a real live dispatch path with a stated activation plan, or delete the registry +
      its three orphaned adapter classes (or add an explicit "kept behind an unreached registry, activation path is X"
      note to each). (repo: market-tick-data-service) — market-tick-data-service@a900ecb4. Chose the document-in-place
      option (not delete/not wire) since `ENDPOINT_STATUS=PENDING_CASSETTE_AWAITING_AUTH` shows genuine WIP scaffolding
      gated on unprovisioned API credentials, not abandoned code; added a STATUS note (matching
      `instruments-service/adapters/tradfi/ibkr.py`'s precedent) to the registry module + all 3 adapters naming the
      unreached path and the activation condition. Full QG green.
- [ ] [BACKEND] P2. Decide + document the fate of `footystats_adapter.py::FootystatsAdapter` and
      `sportradar_adapter.py::SportradarAdapter` (market-tick-data-service) — both marked
      `ENDPOINT_STATUS =     "IMPLEMENTED"` but registered nowhere (absent from `VENUE_REGISTRY`, `sports/registry.py`,
      and both `__init__.py` export lists). Either wire them into `factory.VENUE_REGISTRY` with a stated venue key, or
      add an explicit unreached-and-why note. (repo: market-tick-data-service)
- [ ] [BACKEND] P2. Resolve the undocumented duplicate `PolymarketAdapter` classes —
      `market_interface/adapters/sports/     polymarket_adapter.py::PolymarketAdapter(BaseSportsAdapter)` vs the
      live-routed `market_interface/adapters/prediction/polymarket_adapter.py::PolymarketAdapter(BasePredictionAdapter)`
      (market-tick-data-service). Add an explicit comment in the sports-package version stating it is NOT live-routed
      (the prediction-package version is), or delete it if it's fully superseded — per rule 3, silence on which is live
      is itself the violation. (repo: market-tick-data-service)
- [ ] [BACKEND] P2. Add logging to `footystats_adapter.py::FootystatsAdapter`'s schema-validation-failure fallback
      (market-tick-data-service, `get_leagues:137-138`, `get_matches:172-173`, `get_teams:196-197`) — each currently
      silently substitutes the raw unvalidated dict with no log call; add a `logger.warning`/`log_event` naming the
      validation failure before falling back, matching the rest of this file's discipline. (repo:
      market-tick-data-service)
- [ ] [BACKEND] P2. Decide + document the fate of `aggregator/odds_api.py::OddsApiAdapter` and
      `bookmaker_api/api_football.py::ApiFootballAdapter` (execution-service `sports_execution/adapters/`) — both
      registered/exported but never constructed by any live path (`sports_factory.py::_LIVE_VENUE_CONFIGS` never sets
      `data_source="odds_api_aggregator"`; `ApiFootballAdapter` has no construction site outside its own docstring
      example). Either wire each into a live venue config with a stated activation path, or add an explicit unreached
      note (matching `unity/__init__.py`'s existing precedent in the same repo). (repo: execution-service)
- [x] ✅ [BACKEND] P1. **DONE 2026-08-01 (slot 9), `execution-service@63f099b2`.**
      `bookmaker_api/onexbet.py::OneXBetAdapter` is a read-only odds adapter (module/class docstrings say so explicitly,
      no place-bet method exists) and nothing wires it into a live dispatch path (`config["sports_router"]` is never
      populated in production, so `SportsHandler._try_live_router` always returns `None` and falls through to simulation
      for every sports venue — not ONEXBET-specific). Chose the removal option: dropped `"ONEXBET"` from
      `SportsHandler.BOOKMAKER_VENUES` (now an empty set, same pattern already used by `adapters/sports_router.py`'s
      `_BOOKMAKER_VENUES`) and from `SUPPORTED_VENUES`/`DEFAULT_FEES`; updated the class docstring's Supported-Venues
      line. Updated the one test that depended on the false-positive path
      (`tests/unit/test_instruction_handlers.py::test_sports_bet_execute_success` → renamed
      `test_sports_bet_rejects_unwired_bookmaker_venue`, now asserts the correct validation-rejection).
      `quality-gates.sh` green, verified on origin. (repo: execution-service)
- [x] ✅ [BACKEND] P1. Fix the `except Exception: pass` capability-preflight swallow at the 7 call sites listed in
      Finding 12 above (`exchanges/betfair.py:493-498`, `exchanges/betfair_order_mapping.py:128-133,212-217`,
      `exchanges/kalshi.py:223-228,305-310,415-420`, `exchanges/polymarket_clob.py:226-237`, all execution-service) —
      add a `logger.warning`/`log_event` call naming the swallowed exception type before proceeding, so a
      `CapabilityResolutionError`/`UnsupportedModeError`/`UnsupportedEnvironmentError` firing in production is at least
      observable instead of silent, ahead of a real order placement/cancellation. (repo: execution-service) —
      execution-service@7bba972a. Added `logger.warning` naming `type(exc).__name__` + the exception message at all 7
      sites; control flow (graceful degradation, still not re-raising) unchanged. Full QG green.
- [ ] [OPERATOR] P3. Decide whether the `except Exception: pass  # Graceful degradation` capability-preflight pattern
      found at the 7 sports_execution sites (Finding 12) should be treated as a workspace-wide anti-pattern — the same
      textual pattern was also seen outside the audited directory (`instruction_router.py`,
      `defi_execution/protocols/base.py`, MTDS `factory.py`) during this audit but auditing those call sites was out of
      this task's scope. If confirmed workspace-wide, file a follow-up cross-cutting audit todo. (repo: cross-cutting —
      scoping decision only)
- [ ] [BACKEND] P2. Fix `prediction_markets/kalshi.py::KalshiAdapterConfig`'s stale/incorrect docstring
      (execution-service, lines 1-9, 19-24) — it claims Kalshi uses one combined secret (`kalshi-api-credentials`) and
      is "pending provisioning", which is now false: the live `exchanges/kalshi.py::KalshiAdapter` is fully wired via
      TWO separate secrets (`kalshi-api-key-id`, `kalshi-private-key-pem`, see `sports_factory.py:39-44`). Either delete
      the stub (if fully superseded by the live adapter) or correct its docstring to state the real live/stub
      relationship, matching the sibling `prediction_markets/polymarket.py` stub's correct precedent. (repo:
      execution-service)

## Progress Log

**2026-08-01, slot 6 (backend_engineer)**: Ran the audit via 3 parallel read-only sub-agents (one per repo), each given
the full rule text from `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md` and instructed to trace
reachability through the real dispatch/factory/registry layers, not just the target directory. Files checked and found
COMPLIANT (documented, logged fallbacks; documented wrapper relationships; genuine shard-level-failure-isolation
catch-and-continue patterns) are preserved in each sub-agent's full report rather than re-pasted here — see the source
sub-agent transcripts referenced by this session if a future worker needs the negative-result detail; the summary is:
`base_sports_adapter.py`, `betfair_adapter.py` (MTDS), `sportradar_adapter.py` (MTDS), `polymarket_adapter.py` (MTDS
prediction dispatch path), `odds_api_adapter.py`, `fixture_id_resolver.py`, `matchbook_adapter.py`/
`metabet_adapter.py`/`opticodds_adapter.py`/`odds_engine_adapter.py` (no try/except at all), `api_football.py` (IS, ~25
except blocks, disciplined pattern), `understat.py`, `transfermarkt.py`, `footystats.py`/`soccerfootball_info.py` (IS),
`base.py` (IS), `betfair.py` (IS), `api_football_reference.py`, `unity/*` (execution-service, explicitly documented stub
status), `betfair.py`/`betfair_order_mapping.py` split (execution-service, documented reason),
`trade_execution/adapters/{polymarket_adapter,sports_adapter}.py` (documented USEI wrapper layer),
`paper/paper_betting.py`.
