---
doc_type: plan
title: Build a ForexFactory economic-calendar adapter (consensus/actual/previous + release timing) in features-service
summary:
  Neither FRED nor any existing adapter captures economic-calendar consensus/forecast data or release timing — confirmed
  2026-07-30 that FRED's own API has no such concept at all, it's a pure historical-statistics archive. ForexFactory
  publishes this publicly (rolling-week JSON feed + historical calendar.php pages) with no official API; every viable
  free source for this data is an unofficial scrape. Operator-ruled 2026-07-30 — build our own scraper (not adapt a
  third-party GitHub project), targeting full historical depth (not just the rolling window), living in features-service
  (not a new repo — the UAC schemas this needs already exist and were designed for a "features-calendar-service" that
  pre-dates this workspace's repo consolidation).
status: draft
nature: design
asset_group: [cross-cutting]
stage: [data]
repos: [features-service, unified-api-contracts, deployment-service]
scope: [engineer]
tags: [tradfi, macro, economic-calendar, consensus, forexfactory, scraper, features-service]
related:
  [
    /plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /plans/archive/2026_07/macro_econ_adapter_scaffolds_2026_06_09.md,
    /plans/archive/issues/tradfi_manifest_consolidator_fred_widespan_stall_2026_07_30.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    "interactive session 2026-07-30 — arose while investigating the tradfi manifest consolidator FRED-widespan stall;
    operator asked whether FRED-style historical macro data extends to economic-calendar consensus/forecast/actual data
    too, confirmed it does not (FRED has no consensus concept at all), operator then ruled: build a ForexFactory scraper
    ourselves, full historical depth, in features-service.",
  ]
---

# Build a ForexFactory economic-calendar adapter in features-service

## Why this exists

Confirmed 2026-07-30 via direct code read of `market_tick_data_service/market_interface/adapters/tradfi/fred_adapter.py`
(+ `_umi_fred.py`): the FRED integration captures ONLY raw historical `series/observations` values (a bare
`value`/`date`/`series_id` triple). Neither release-timing metadata nor a consensus/forecast estimate is captured, and
**FRED's own API has no such concept** — FRED is a pure historical-statistics archive (the St. Louis Fed's own numbers,
published after the fact), not an economic-calendar/consensus provider. "Consensus estimate" (what economists expected
before a release) is fundamentally a different kind of data, produced by survey-aggregator vendors (Bloomberg,
TradingEconomics, Econoday), not government statistics agencies.

This gap was already anticipated in this workspace's schemas, just never built: `unified_api_contracts`'s
`EventCalendarSource` registry (`internal/architecture_v2/event_calendar_source.py`) has an
`EventSourceType.MACRO_CONSENSUS` entry literally documented as _"Bloomberg, TradingEconomics — consensus forecasts +
releases"_, and `internal/domain/trading_api/calendar.py`'s `EconomicResultItem` already carries `release_time_utc`
(release timing FRED never captures) — but has NO `consensus_value`/`forecast_value` field yet (its sibling
`CorporateActionItem` on the same file already has this exact pattern via `estimated_eps`, so extending
`EconomicResultItem` the same way is a precedented, not novel, schema change).
`unified_api_contracts/internal/reference/economic_calendar.py`'s `MacroResultRecord` docstring says _"Used by
features-calendar-service for macro result GCS output"_ — a service name that does not exist in this workspace today;
per operator direction, this is presumed pre-repo-consolidation naming and the real home is the current
`features-service` repo, not a new one.

**No official free API exists for consensus/forecast data** (researched 2026-07-30) — Bloomberg/TradingEconomics/
Econoday-class stable APIs are paid; the free options (Apify's ForexFactory-JSON wrapper, Pineify, Investing.com's
public page) are all third-party scrapers of public calendar websites, not sanctioned vendor APIs. Operator ruled to
proceed anyway via our own ForexFactory scraper (not an adopted third-party GitHub project), covering full historical
depth (ForexFactory's `calendar.php` archive), not just its rolling this/last/next-week JSON feed.

## Scope

**In scope**: a new adapter (features-service) that captures, per economic-calendar event: `event_type`, `country`/
`currency`, `release_date`, `release_time_utc`, `actual_value`, `consensus_value` (new field), `previous_value`,
`impact`/`importance` (ForexFactory's own low/medium/high tagging). Both a one-time historical backfill (as far back as
ForexFactory's calendar actually goes — confirm the real floor, do not assume) and a going-forward daily/weekly poll.

**Out of scope**: any change to FRED's own adapter/data (already fixed separately, `deployment-service@fee8860b`); a
paid-vendor integration (Bloomberg/TradingEconomics) — this plan is the free-source path specifically; UI/dashboard
surfacing of this data (a separate, later consumer-side concern).

## Todos

- [ ] [DATA] P0. **Research ForexFactory's real request shape before writing any scraper code.** Confirm: (a) the
      rolling-week JSON feed's exact URL(s) (`nfs.faireconomy.media/ff_calendar_*week.json` or current equivalent —
      verify it's still live and unauthenticated, sites change), (b) the historical `calendar.php?week=<date>`-style URL
      scheme for past weeks and how far back it actually resolves to real data (do not assume "since ForexFactory
      existed" — measure the real floor by walking backward from today until a request returns empty/errors), (c) the
      exact per-event fields present in each format (does the JSON feed already carry `previous`/`forecast`/`actual` the
      same way the HTML does?), (d) whether the site's `robots.txt` disallows `calendar.php` (if so, this is a real
      go/no-go input for the "build our own" decision, not just an implementation detail — surface it, don't silently
      ignore it). Done when: a short written finding (this plan's Progress Log) states the confirmed URL scheme(s), the
      measured historical floor date, and the `robots.txt` status, with real HTTP responses shown, not assumed. Repo:
      features-service (research only, no code yet).
- [ ] [DATA] P1. **Extend the UAC schema with a consensus/forecast field, matching the precedented pattern.** Add
      `consensus_value: float | None` to `EconomicResultItem`
      (`unified_api_contracts/internal/domain/trading_api/calendar.py`) — mirroring `CorporateActionItem.estimated_eps`
      on the same file. Register a new `EventCalendarSource` entry (`source_id="forexfactory_scrape"`,
      `source_type=EventSourceType.MACRO_CONSENSUS`) in `event_calendar_source.py`'s registry, distinct from the
      existing `bloomberg_macro`/`trading_economics_macro` placeholder entries (those name vendors this workspace does
      not integrate; this is a genuinely different, free source and should be honestly labeled as such, not silently
      folded into the Bloomberg/TradingEconomics entries). `quality-gates.sh` green in unified-api-contracts. Done when:
      the new field + registry entry exist, are covered by a schema test, and every existing consumer of
      `EconomicResultItem` still round-trips (no breaking change to the existing 6 fields).
- [ ] [DATA] P1. **Build the scraper/adapter in features-service, mirroring fred_adapter.py's conventions.** Own HTTP
      client with a real User-Agent string (not a browser-spoofing one — identify honestly per the `robots.txt` finding
      above), bounded retry-with-backoff, rate-limited requests (this is someone else's public web server, not an API
      meant for bulk historical scraping — pace requests conservatively, e.g. no more than 1 request per few seconds,
      and do not parallelize the historical walk across multiple concurrent connections). Parses either the JSON feed
      (rolling window) or the HTML calendar page (historical), normalizes both into the same `EconomicResultItem` shape.
      No Selenium/headless-browser dependency unless the research todo above proves the HTML truly requires JS rendering
      (several of the researched open-source projects manage without it — confirm before adding that dependency weight).
      Done when: a real invocation against ForexFactory returns correctly typed, non-empty results for both a
      rolling-window and a historical-week request.
- [ ] [DATA] P2. **Wire the historical backfill launcher + forward-poll cron.** Mirror
      `deployment-service/scripts/vm/launch-tradfi-bf-fred.sh`'s single-VM, non-sharded pattern (rationale: a shared
      rate-limited external source, not a per-IP-scalable one — fanning out multiple VMs would just multiply request
      pressure against ForexFactory's server, the same reasoning FRED's launcher already documents for its own
      shared-API-key limit). Explicitly clamp the backfill start floor to the REAL measured floor from the research todo
      above (never default to "as far back as possible" without that confirmed number — this plan exists partly because
      FRED's launcher got exactly this wrong). Done when: `--dry-run` shows the correct floor..today window, and a real
      `--year <first-available-year>` smoke-test capture returns real events with `quality-gates.sh` green.
- [ ] [DATA] P2. **Tests: HTML/JSON fixtures, no live network in CI.** Regression tests for the parser(s) using saved
      real response fixtures (captured once during the research todo, not re-fetched on every test run) — asserts the
      new `consensus_value` field parses correctly, `release_time_utc` is present and correctly timezone-normalized
      (ForexFactory's calendar is ET-based; verify the conversion), and a malformed/missing-field event fails closed
      (recorded as `empty_confirmed`/error, never silently dropped). Done when: `quality-gates.sh` is green in
      features-service and the new tests pass with zero live HTTP calls.
- [ ] [DATA] P3. Once the above ships and a real backfill has run, do a first honest-coverage check: what fraction of
      expected calendar events (per ForexFactory's own historical week count) actually landed with a real
      `consensus_value`, vs. how many are `actual`-only (older weeks where ForexFactory itself may not have retained the
      original forecast) — report this rather than assuming 100% consensus coverage back to the historical floor. Repo:
      features-service.

## Codex SSOTs

No existing codex doc covers economic-calendar/consensus data specifically — if this plan ships a real pattern worth
generalizing (e.g. "how to safely integrate a scraped, rate-limited third-party source"), stub one under
`codex/02-data/` in the post-phase audit rather than leaving the pattern undocumented for the next such integration.

## Progress Log

- **2026-07-30 (plan authored, this session)**: drafted per direct operator ruling (build our own ForexFactory scraper,
  full historical depth, lives in features-service) following confirmation that no free-and-stable consensus/calendar
  API exists. `status: draft`, `assigned_vm: NA` per the operator's explicit choice (human plan, not AO-dispatched) — no
  code written yet, this is the scoping document.
