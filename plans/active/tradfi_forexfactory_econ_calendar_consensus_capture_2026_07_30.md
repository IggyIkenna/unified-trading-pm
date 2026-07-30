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
depth (ForexFactory's historical `calendar?week=` archive — confirmed 2026-07-30 as the CURRENT scheme; `calendar.php`
was the 2007-2012 legacy name, see todo 1's Progress Log evidence), not just its rolling this/last/next-week JSON feed.

## Scope

**In scope**: a new adapter (features-service) that captures, per economic-calendar event: `event_type`, `country`/
`currency`, `release_date`, `release_time_utc`, `actual_value`, `consensus_value` (new field), `previous_value`,
`impact`/`importance` (ForexFactory's own low/medium/high tagging). Both a one-time historical backfill (as far back as
ForexFactory's calendar actually goes — confirm the real floor, do not assume) and a going-forward daily/weekly poll.

**Out of scope**: any change to FRED's own adapter/data (already fixed separately, `deployment-service@fee8860b`); a
paid-vendor integration (Bloomberg/TradingEconomics) — this plan is the free-source path specifically; UI/dashboard
surfacing of this data (a separate, later consumer-side concern).

## Todos

- [x] 1. ✅ [DATA] P0. **Research ForexFactory's real request shape before writing any scraper code.** Confirm: (a) the
      rolling-week JSON feed's exact URL(s), (b) the historical URL scheme for past weeks + the real floor, (c) exact
      per-event fields per format, (d) `robots.txt` status. **Done 2026-07-30 — full evidence in the Progress Log
      below.** Concise summary: (a) `nfs.faireconomy.media/ff_calendar_thisweek.json` is LIVE (HTTP 200, 92 real events)
      but the sibling `ff_calendar_{next,last}week.json` both 404 at those exact names — see new follow-up todo below;
      (b) the CURRENT scheme is `forexfactory.com/calendar?week=<mon><day>.<year>` (e.g. `week=jan1.2007`), **not**
      `calendar.php?week=<date>` as this todo originally assumed — `calendar.php` was the 2007-2012 legacy scheme, now
      presumed (Wayback CDX shows 301s, unconfirmed live) to redirect to the modern one; measured real floor =
      **2007-01-01** (every earlier week silently clamps to a byte-identical 13,904/13,896-byte "No results found."
      empty state at HTTP 200 — a scraper must detect this signature as "before floor," never "zero events"); (c) the
      JSON feed carries only 6 fields (title/country/date/impact/forecast/previous) and **never** an `actual` value
      (confirmed absent even 4 days post-release) — `actual_value` capture requires the HTML page (which does carry
      Actual) or another source; (d) `robots.txt` is a bare 2-line Sitemap-only file with NO Disallow of any kind on one
      probe, but a LATER same-day probe hit a Cloudflare challenge 403 on the identical URL — reconciled in the Progress
      Log as adaptive Cloudflare bot-protection, not a robots.txt content change. **Unplanned but material finding**:
      the live site sits behind a Cloudflare Managed Challenge blocking every plain-HTTP path — this is NOT a
      JS-DOM-rendering requirement (the underlying HTML is server-rendered, confirmed via a non-JS Wayback crawl), but
      it does mean a plain `requests`/curl/WebFetch client cannot reach any page reliably; this corrects the
      build-scraper todo's premise below. Repo: features-service (research only, no code shipped this todo).
- [ ] [DATA] P1. **Confirm the correct rolling next-week/last-week JSON access pattern.** `ff_calendar_nextweek.json`
      and `ff_calendar_lastweek.json` both 404'd at those literal names during the 2026-07-30 research pass — only
      `ff_calendar_thisweek.json` is confirmed live. Check for an offset/query-param variant or a differently-named file
      before assuming the rolling JSON feed only ever covers the current week. Done when: either a working
      next/last-week JSON URL is found and cited with a real HTTP 200, or the negative is confirmed (only `thisweek`
      exists) and the build-scraper todo's forward-poll design accounts for that (e.g. poll `thisweek` daily and diff
      against the prior capture, rather than relying on a `nextweek` pre-announcement). Repo: features-service.
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
      client with a real User-Agent string (not a browser-spoofing one — `robots.txt` itself is permissive, no Disallow
      anywhere), bounded retry-with-backoff that honors `Retry-After` on 429 (measured 2026-07-30: the JSON host
      returned HTTP 429 + `retry-after: 300` on a follow-up request only ~30s after a clean 200 — throttle to well under
      that, e.g. one pull per several minutes, not per-few-seconds), and do not parallelize the historical walk across
      multiple concurrent connections. Parses the JSON feed (rolling window — `forecast`/`previous`/`impact` only, no
      `actual`) and the HTML calendar page (`calendar?week=<mon><day>.<year>`, historical — carries Actual too),
      normalizes both into the same `EconomicResultItem` shape. **Premise CORRECTED per todo 1's finding**: the
      underlying HTML does NOT require JS rendering to parse (confirmed via a non-JS Wayback crawl showing full
      server-rendered markup) — but the LIVE site sits behind a Cloudflare Managed Challenge blocking every plain-HTTP
      path (curl/`requests`/WebFetch all hit a 403 JS-challenge shell on every path tried), so a
      `requests`+`BeautifulSoup`-only client as originally scoped will fail at the FIRST request regardless of
      JS-rendering being a non-issue; budget for a stealth/ anti-detection headless browser (e.g. Playwright) OR a paid
      unblocking proxy to get past the challenge, then parse the resulting HTML with a plain parser (no JS execution
      needed once past the gate). Before marking this todo done, explicitly resolve how `actual_value` gets captured
      given the JSON feed never carries it (HTML-only, and HTML is challenge-gated) and confirm/replace the 404ing
      `ff_calendar_{next,last}week.json` names (see the dedicated follow-up todo above). Done when: a real invocation
      against ForexFactory returns correctly typed, non-empty results — including a real `actual_value` — for both a
      rolling-window and a historical-week request.
- [ ] [DATA] P2. **Wire the historical backfill launcher + forward-poll cron.** Mirror
      `deployment-service/scripts/vm/launch-tradfi-bf-fred.sh`'s single-VM, non-sharded pattern (rationale: a shared
      rate-limited external source, not a per-IP-scalable one — fanning out multiple VMs would just multiply request
      pressure against ForexFactory's server, the same reasoning FRED's launcher already documents for its own
      shared-API-key limit). Explicitly clamp the backfill start floor to the REAL measured floor confirmed by todo 1 —
      **2007-01-01** (never default to "as far back as possible" without that confirmed number — this plan exists partly
      because FRED's launcher got exactly this wrong); the launcher's HTTP client needs the same Cloudflare-bypass
      tooling as the build-scraper todo above, since the historical walk hits the identical challenge-gated HTML path.
      Done when: `--dry-run` shows the correct 2007-01-01..today window, and a real `--year 2007` smoke-test capture
      returns real events with `quality-gates.sh` green.
- [ ] [DATA] P2. **Tests: HTML/JSON fixtures, no live network in CI.** Regression tests for the parser(s) using saved
      real response fixtures (captured once during the research todo, not re-fetched on every test run) — asserts the
      new `consensus_value` field parses correctly, `release_time_utc` is present and correctly timezone-normalized
      (ForexFactory's calendar is ET-based; verify the conversion), and a malformed/missing-field event fails closed
      (recorded as `empty_confirmed`/error, never silently dropped). Also fixture the pre-floor empty-state response
      (the byte-identical ~13,904-byte "No results found." page confirmed 2026-07-30) so the floor-detection logic has
      its own regression test, not just the happy-path parser. Done when: `quality-gates.sh` is green in
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
- **2026-07-30 (research pass, this session)**: completed todo 1 with real HTTP evidence for all four sub-findings;
  flipped it `[x]`, corrected a false premise the plan carried since authoring, and added one new follow-up todo.
  - **JSON feed**: `https://nfs.faireconomy.media/ff_calendar_thisweek.json` — HTTP 200, verified via both WebFetch and
    a direct `curl` (byte-identical), 92-event JSON array. Union of fields across all 92 objects is exactly 6: `title`,
    `country`, `date`, `impact`, `forecast`, `previous` — **no `actual` field at all, ever**, confirmed absent even for
    an event already 4 days in the past relative to the fetch, and no `url`/`id` field either. `date` is ISO-8601 with a
    fixed `-04:00` (US/Eastern) offset. `ff_calendar_nextweek.json` and `ff_calendar_lastweek.json` both returned a real
    nginx 404 at those exact filenames — not yet resolved, see the new follow-up todo. A plain HEAD to the same host
    ~30s after the successful 200 got HTTP 429 (Cloudflare) with `retry-after: 300` — the JSON host is
    Cloudflare-fronted and enforces a real cooldown even though the first request needed no special handling.
  - **Historical URL scheme — corrects this plan's own premise.** The CURRENT (confirmed live 2026-07-30) scheme is
    `https://www.forexfactory.com/calendar?week=<mon><day>.<year>` (3-letter lowercase month, e.g. `week=jan1.2007`;
    keywords `week=this/last/next` also work; companion `day=`/`month=` params exist). This plan's "Why this exists"
    prose and todo 1's own original text both assumed `calendar.php?week=<date>`; that is the LEGACY 2007-2012 scheme (a
    session-hashed PHP endpoint keyed on a raw Unix timestamp) — confirmed via contemporaneous Wayback Machine captures
    from those years, plus CDX records showing 301 redirects on `calendar.php` in 2021-2025 crawls (consistent with it
    now forwarding to the modern scheme; NOT independently confirmed live today since `calendar.php` sits behind the
    same Cloudflare gate as everything else on the domain). Both references corrected in this edit.
  - **Measured historical floor: 2007-01-01.** Direct A/B test (via a JS-capable retrieval path — plain curl/WebFetch
    are blocked by Cloudflare for every path today, see below): `calendar?week=jan1.2007` returns real,
    internally-consistent 2007 events (e.g. Fri Jan 5 2007: USD Non-Farm Employment Change actual 167K forecast 115K
    previous 132K, matching the well-documented real release). `calendar?week=dec31.2006` returns HTTP 200 but silently
    clamps the displayed range forward to "Jan 1, 2007 - Jan 6, 2007." Every week requested further back
    (`dec25.2006`/`dec18.2006`/`jun1.2006`/`jan1.2006`/`jan1.2005`/`jan1.2003`/`jan1.2000`/`jan1.1999`) returns an
    IDENTICAL generic empty-state page — byte size pinned at exactly 13,904 bytes (13,896 for 1999) vs 27-34KB for a
    real week, literal "No results found." text, nav pinned to "Jan 2007," permalink rewritten to `week=jan1.2007`, zero
    data rows in the event table. This is a detectable, reproducible floor signature a scraper must treat as "before the
    archive's floor," never "a genuine zero-event week" — a naive HTTP-200-only check would misread it.
  - **`robots.txt` — two contradictory results in the same day, reconciled as adaptive bot-protection, not a content
    change.** An early, isolated probe of `https://www.forexfactory.com/robots.txt` returned HTTP 200 with the ENTIRE
    file being one 55-byte line — `Sitemap: https://www.forexfactory.com/sitemap-index.xml` — no `User-agent:` line at
    all, so zero `Disallow`/`Allow` directives of any kind; confirmed byte-identical via both WebFetch and a direct
    `curl`. From robots.txt alone, nothing on the domain (including `/calendar`) is disallowed. A LATER same-day probe
    of the identical URL — made after many additional historical-floor requests against `forexfactory.com` earlier in
    the same research pass — returned HTTP 403 with a Cloudflare `cf-mitigated: challenge` header (a "Just a moment..."
    JS-challenge shell, not the real file). Most consistent read: Cloudflare's bot heuristics are
    request-volume/pattern-adaptive per session, not a fixed allow/deny stamped on a given path — the SAME URL went from
    freely-servable to challenge-gated within one research session once enough requests had been made against the
    domain. **Practical conclusion**: `robots.txt` itself does not disallow calendar scraping (permissive), but that
    permission is not the real access gate — Cloudflare's Managed Challenge in front of the origin is, and it can trip
    even on a previously-clean path mid-session. A production scraper must assume challenge state can flip at any time
    and handle 403/429 gracefully, never trust one successful probe as proof of continued reachability.
  - **JS rendering: NOT required to parse the HTML once fetched.** Confirmed via a Wayback Machine capture of
    `calendar?week=sep28.2008`, crawled 2021-06-25 by archive.org's non-JS Heritrix crawler — the captured HTML contains
    complete real multi-day event rows with actual/forecast/previous values as static markup (217 `calendar__row` + 144
    `calendar__event-title` instances; `<th>` headers Date/Currency/Impact/Alerts/Detail/
    Actual/Forecast/Previous/Graph). **But this is a materially different question from whether the LIVE site is
    reachable at all**: every plain-HTTP probe today (`curl`/WebFetch) against `/`, `/calendar`, `/calendar?week=...`,
    `/calendar.php`, and (on the later probe) `/robots.txt`, hit the identical Cloudflare Managed Challenge 403 — a
    `requests`+`BeautifulSoup`-only scraper as the build-scraper todo originally scoped it will fail at the FIRST
    request regardless of JS-rendering being a non-issue. Getting past Cloudflare (a stealth/anti-detection headless
    browser, e.g. Playwright, or a paid unblocking proxy) is the real engineering problem, not DOM rendering.
  - **HTML field set** (for once the Cloudflare gate is solved): Date, Time, Currency, Impact (color-coded icon), Event
    name/title, Detail (expandable description), Alerts, **Actual**, Forecast, Previous (carries a "revised"
    sub-indicator + tooltip when restated), Graph (historical chart link) — richer than the JSON feed's 6 fields,
    critically including Actual, which the JSON feed never carries.
  - **Edits made to this plan in this same session**: research todo 1 flipped `[x]` with the evidence above; a new P1
    todo added to resolve the next/last-week JSON naming gap; the build-scraper todo corrected to remove the false "no
    headless browser unless JS-rendering is proven necessary" premise and state the real Cloudflare-bypass +
    rate-limiting + `actual_value`-sourcing requirements instead; the launcher todo now cites the confirmed 2007-01-01
    floor explicitly; the tests todo now also calls for a pre-floor empty-state fixture; the "Why this exists" prose's
    `calendar.php` reference corrected to the confirmed-current `calendar?week=` scheme. **Net effect on later todos**:
    still viable as a plan, but NOT as cheaply as originally scoped — the "no Selenium/headless-browser unless proven
    necessary" cost-saving premise in the build-scraper todo does not survive contact with the live site (Cloudflare
    gates every path regardless of JS-rendering need), so that todo should be estimated with that dependency weight
    included, not treated as a stretch fallback.
