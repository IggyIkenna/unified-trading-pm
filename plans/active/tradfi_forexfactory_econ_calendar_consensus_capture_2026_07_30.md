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
asset_group: [tradfi] # corrected 2026-08-02 ag-closeout-audit tradfi tranche -- was [cross-cutting], a genuine mistag (content is 100% tradfi-specific: ForexFactory economic-calendar scraper for tradfi macro data, tags already say tradfi)
stage: [data]
repos: [features-service, unified-api-contracts, deployment-service]
scope: [engineer]
tags: [tradfi, macro, economic-calendar, consensus, forexfactory, scraper, features-service]
related:
  [
    /plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /plans/archive/2026_07/macro_econ_adapter_scaffolds_2026_06_09.md,
    /plans/archive/issues/tradfi_manifest_consolidator_fred_widespan_stall_2026_07_30.md,
    /plans/archive/corporate_actions_+_earnings_to_calendar_56d63c2c.plan.md,
    /plans/archive/issues/features_calendar_pipeline_mode_gap_2026_05_12.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
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
effort: xhigh
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
- [x] ✅ [DATA] P1. **SHIPPED 2026-08-09 — `unified-api-contracts@cbb3e2b33`.** `consensus_value: Decimal | None` added
      to `MacroResultRecord` + `to_dict()`; new `forexfactory_scrape` `EventCalendarSource` entry registered
      (`source_type=MACRO_CONSENSUS`), distinct from the zero-client-code `bloomberg_macro`/`trading_economics_macro`
      placeholders. `economic_results_calculator.py`'s empty-DataFrame column list updated to match (FRED records always
      carry `consensus_value=None`, since FRED has no consensus concept). QG green. **CORRECTED SCOPE 2026-07-30 (see
      Progress Log) — target `MacroResultRecord`, not `EconomicResultItem`, as the primary schema change.** A dedicated
      investigation found `features_service/calendar/` IS the real, already-built "features-calendar-service"
      `MacroResultRecord`'s docstring refers to — and `MacroResultRecord`
      (`unified_api_contracts/internal/reference/economic_calendar.py`, fields: `event_type`, `series_id`,
      `release_date`, `actual_value`, `previous_value`, `revision`, `unit`, `source`, `fetched_at`) is the schema its
      REAL, GCS-writing production path (`economic_results_calculator.py`/`economic_results_handler.py`) actually uses
      today for real FRED actuals — `EconomicResultItem`
      (`unified_api_contracts/internal/domain/trading_api/calendar.py`) is only a mock-serving API-gateway DTO with no
      live writer behind it yet (`unified-trading-api`'s `/calendar/economic-results` route is explicitly mock-only,
      docstring states "Live mode (future)"). Add `consensus_value: Decimal | None` + update `to_dict()` on
      `MacroResultRecord` (primary target — this is what actually lands in GCS); extending `EconomicResultItem` the same
      way is a reasonable secondary/later step for eventual UI-serving, not the main target. Also register a new
      `EventCalendarSource` entry (`source_id="forexfactory_scrape"`, `source_type=EventSourceType.MACRO_CONSENSUS`) in
      `event_calendar_source.py`'s registry, distinct from the existing `bloomberg_macro`/`trading_economics_macro`
      placeholder entries (both confirmed to have ZERO client code anywhere in the workspace — pure unused placeholders;
      this is a genuinely different, free source and should be labeled as such, not folded into them).
      `quality-gates.sh` green in unified-api-contracts. Done when: `MacroResultRecord` carries the new field and
      round-trips in `to_dict()`, covered by a schema test, with no breaking change to its existing 8 fields.
- [x] ✅ [DATA] P1. **SHIPPED 2026-08-09 — `features-service@b6809756`.** The Cloudflare blocker is RESOLVED, not just
      worked around: tested live against the actual site, Playwright AND `patchright` (a purpose-built anti-detection
      fork) are BOTH blocked (403 "Just a moment...", confirmed from a residential dev IP AND the real GCP backfill
      region `asia-northeast1-c`). The combination that passes: `nodriver` + a real Google Chrome binary (not a
      CI/testing Chromium build) + headed mode + a residential IP — Cloudflare weighs IP reputation as a distinct signal
      from browser fingerprint quality, so a GCP datacenter IP fails regardless of tooling. New
      `calendar/adapters/forexfactory_adapter.py` (nodriver-based) +
      `calendar/engine/calculators/     forexfactory_calculator.py` + `calendar/cli/handlers/forexfactory_handler.py`
      (`--operation forexfactory`, registered in `ServiceBootstrap` in the SAME commit — the orphan-registration mistake
      this todo warned about was NOT repeated). **Premise correction vs. this todo's own text below**: the page does NOT
      need HTML-table parsing at all — it embeds a clean, structured JSON state (`window.calendarComponentStates`) with
      `ebaseId` (stable cross-week event-type id), `dateline` (epoch), and `actual`/`forecast`/`previous`/`revision` as
      direct fields — far more robust than the HTML-table approach this todo originally scoped. Verified end-to-end
      against the live site: 55 real records for the 2007-01-01 week, including the correct historical NFP release
      (`actual=167K forecast=115K previous=132K`) and 2 bond-auction events with a compound `"yield|bid-to-cover"` value
      format the parser explicitly handles. **NOT yet done**: production runs need
      `CalendarFeaturesConfig.forexfactory_proxy_url` (Secret Manager, a residential-proxy egress) — BLOCKED-CREDENTIALS
      pending operator provisioning (recommended: a pay-as-you-go residential proxy like IPRoyal, ~$7/1GB, no
      subscription — the full 2007-2026 historical backfill is ~330MB, comfortably under 1GB). Without it the adapter
      works today only from a residential-IP dev machine. **CORRECTED ARCHITECTURE 2026-07-30 (see Progress Log) — this
      is a new SIBLING data source inside the EXISTING `features_service/calendar/` module, not new standalone
      orchestration.** A dedicated investigation found this module already has a working, precedented pattern for adding
      exactly this kind of external source: the archived plan
      `plans/archive/corporate_actions_+_earnings_to_calendar_56d63c2c.plan.md` (2026-03-24) built
      `corporate_actions_handler.py`/`polygon_corporate_actions_adapter.py` and `yfinance_earnings_adapter.py` as
      siblings within this same module — new adapter in `calendar/adapters/`, new calculator in
      `calendar/engine/calculators/`, new `--operation <name>` CLI handler, GCS path
      `calendar/<name>/by_date/day={date}/*.parquet`. Follow that shape: a new
      `calendar/adapters/forexfactory_adapter.py` + a new calculator + a new CLI handler (or a `source` discriminator
      added to the existing `economic_results` handler), reusing
      `CalendarOrchestrationService`/`CalendarFeaturesConfig`/`GCSCalendarStorage` (`ManifestWriter` wiring, dry-run/GCS
      split, bucket resolution) rather than building parallel plumbing. **CRITICAL — do not repeat this module's own
      most relevant cautionary precedent**: `economic_results_handler.py` was built the same way ~4 months ago and
      captures REAL FRED actuals correctly, but was NEVER registered in `cli/main.py`'s
      `ServiceBootstrap(operations={...})` dict, so nothing has ever actually run it in production (tracked as its own
      todo now in `macro_micro_econ_data_capture_audit_2026_06_05.md`) — this plan's new operation MUST be registered
      there in the SAME commit that builds it, not left as a second orphan. Own HTTP client with a real User-Agent
      string (not a browser-spoofing one — `robots.txt` itself is permissive, no Disallow anywhere), bounded
      retry-with-backoff that honors `Retry-After` on 429 (measured 2026-07-30: the JSON host returned HTTP 429 +
      `retry-after: 300` on a follow-up request only ~30s after a clean 200 — throttle to well under that, e.g. one pull
      per several minutes, not per-few-seconds), and do not parallelize the historical walk across multiple concurrent
      connections. Parses the JSON feed (rolling window — `forecast`/`previous`/`impact` only, no `actual`) and the HTML
      calendar page (`calendar?week=<mon><day>.<year>`, historical — carries Actual too), normalizes both into
      `MacroResultRecord` (per the corrected schema todo above). **Premise CORRECTED per todo 1's finding**: the
      underlying HTML does NOT require JS rendering to parse (confirmed via a non-JS Wayback crawl showing full
      server-rendered markup) — but the LIVE site sits behind a Cloudflare Managed Challenge blocking every plain-HTTP
      path (curl/`requests`/WebFetch all hit a 403 JS-challenge shell on every path tried), so a
      `requests`+`BeautifulSoup`-only client as originally scoped will fail at the FIRST request regardless of
      JS-rendering being a non-issue; budget for a stealth/anti-detection headless browser (e.g. Playwright) OR a paid
      unblocking proxy to get past the challenge, then parse the resulting HTML with a plain parser (no JS execution
      needed once past the gate). Before marking this todo done, explicitly resolve how `actual_value` gets captured
      given the JSON feed never carries it (HTML-only, and HTML is challenge-gated), confirm/replace the 404ing
      `ff_calendar_{next,last}week.json` names (see the dedicated follow-up todo above), and check
      `features_calendar_pipeline_mode_gap_2026_05_12.md` for the still-open `pipeline_mode` tagging decision any new
      calendar-family write needs. Done when: a real invocation against ForexFactory returns correctly typed, non-empty
      `MacroResultRecord` results — including a real `actual_value` — for both a rolling-window and a historical-week
      request, AND the new `--operation` is confirmed registered + reachable via `python -m features_service.calendar`.
- [ ] [DATA] P1. **BLOCKED-CREDENTIALS — provision a residential-proxy account, then wire it into
      `CalendarFeaturesConfig.forexfactory_proxy_url` (Secret Manager, `forexfactory-residential-proxy-url` by
      default).** The code path is ready (`ForexFactoryAdapter.__init__(proxy_url=...)` passes it straight through to
      `--proxy-server=` on the launched Chrome); nothing to build here, just an operator account signup. Recommended
      2026-08-09: a pay-as-you-go residential proxy (e.g. IPRoyal, ~$7/1GB, no subscription/expiry) — the full backfill
      (~1030 weeks × ~330KB) is ~330MB, comfortably under a single 1GB pack.
- [ ] [DATA] P2. **Wire the historical backfill launcher + forward-poll cron.** Mirror
      `deployment-service/scripts/vm/launch-tradfi-bf-fred.sh`'s single-VM, non-sharded pattern (rationale: a shared
      rate-limited external source, not a per-IP-scalable one — fanning out multiple VMs would just multiply request
      pressure against ForexFactory's server, the same reasoning FRED's launcher already documents for its own
      shared-API-key limit); check whether `runtime-topology.yaml`'s existing `calendar` family Cloud Scheduler cadence
      (the corporate-actions/earnings precedent runs `time_throttled_medium`, ~15min) is the right cadence to extend,
      rather than building a wholly separate cron. Explicitly clamp the backfill start floor to the REAL measured floor
      confirmed by todo 1 — **2007-01-01** (never default to "as far back as possible" without that confirmed number —
      this plan exists partly because FRED's launcher got exactly this wrong); NEEDS the residential-proxy todo above
      first (a VM launch runs on GCP, so it needs the proxy to clear Cloudflare). The CLI handler
      (`--operation forexfactory --mode batch --start-date 2007-01-01 --end-date <today>`) already iterates the full
      week range via `iter_historical_weeks` — this todo is specifically about the VM launcher wrapper + Cloud Scheduler
      wiring, the actual fetch/write logic is done. Done when: `--dry-run` shows the correct 2007-01-01..today window,
      and a real `--year 2007` smoke-test capture returns real events with `quality-gates.sh` green.
- [x] ✅ [DATA] P2. **SHIPPED 2026-08-09 — `features-service@b6809756`, 28 tests, `quality-gates.sh` green, zero live
      HTTP calls.** The 2026-07-30 fixtures (`json_feed_thisweek_sample_2026_07_30.json`,
      `html_calendar_2007_01_01_floor_real_data.html`, etc.) turned out NOT to be the shape the shipped adapter consumes
      — it reads the embedded JSON state directly (`window.calendarComponentStates`), not HTML tables, so new fixtures
      were captured and promoted instead: `calendar_component_state_2007_01_01_real_data.json` (the real state for the
      NFP week, 72 events) and `calendar_component_state_2006_01_01_pre_floor_empty.json` (the real pre-floor state,
      `days=[]`). **`release_time_utc` was NOT added** — out of the corrected schema scope (only `consensus_value` per
      the todo above); `dateline` (unix epoch) is used internally to derive `release_date` but is not exposed on
      `MacroResultRecord`. **Empty-state detection redesigned from what this todo assumed**: a text-marker check ("No
      results found.") was tried and REJECTED — that string is generic search-select-widget boilerplate present on EVERY
      page (a dropdown's own empty-search placeholder), confirmed via a live test that it false-positived on the real
      2007-01-01 week. The correct signal, now what's actually implemented: the parsed JSON state's own `days` array is
      genuinely empty for a pre-floor week vs. populated for a real week — no HTML/byte-length heuristics needed at all.
      The old sibling HTML fixtures remain in the repo as reference material (they establish the real historical floor +
      boundary-clamp behavior) but are no longer what the shipped code's tests assert against.
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

- **2026-08-08 (draft-flip conflict-check session)**: Reviewed against today's operator authorization to flip draft AO
  plans to active where genuinely gate-clear. This doc is NOT that class of draft — `depends_on: []` so there is no
  dependency gate to clear, but the absence of a dependency gate doesn't make this an approval-pending draft either:
  `nature: design`, and this doc's OWN 2026-07-30 authoring Progress Log entry (below) states
  `status: draft`/`assigned_vm: NA` was the operator's EXPLICIT choice — "human plan, not AO-dispatched" — not a
  default. The remaining open todos still carry genuine unresolved engineering/design judgment calls (todo 4: how to get
  past ForexFactory's Cloudflare Managed Challenge — a stealth/anti-detection headless browser vs. a paid unblocking
  proxy — and how `actual_value` gets sourced at all given the JSON feed never carries it, HTML-only and
  challenge-gated), not a checkable/bounded outcome a dispatched worker could resolve alone (task_template.md §4
  "bounded outcome only"). **Not flipped** — stays `assigned_vm: NA` / `status: draft` pending an operator/human design
  decision on the scraping approach.
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
- **2026-07-30 (architecture correction, this session)** — a dedicated investigation of `features_service/calendar/`
  (triggered by noticing `economic_events` in a routine `quality-gates.sh` formula-hash-drift dump — not something this
  plan's original authoring pass had looked for) found this module already IS the real, substantially-built
  "features-calendar-service" `MacroResultRecord`'s docstring refers to, with a working precedent (the archived
  `corporate_actions_+_earnings_to_calendar` plan) for adding exactly this kind of new external source as a sibling.
  This significantly changes the shape of todos 3-5 above (now corrected in place, not left stale): the schema target
  moves from the mock-only `EconomicResultItem` to the real, GCS-writing `MacroResultRecord`; the adapter/handler build
  becomes "add a sibling within `features_service/calendar/`" rather than new standalone orchestration; the launcher
  todo now cross-checks the existing `calendar` family's Cloud Scheduler cadence before assuming a new cron is needed.
  Also found (and separately fixed, outside this plan's own scope) that `economic_results_handler.py` — this module's
  closest existing sibling, already capturing real FRED actuals — was built ~4 months ago and never registered in the
  CLI's dispatch table, so it has never actually run in production; added a real tracked todo for that gap to
  `macro_micro_econ_data_capture_audit_2026_06_05.md` (it had only ever been prose in that doc's own "Recommended
  decision" section, never a `- [ ]` item) rather than duplicating it here. Promoted the research fixtures from
  scratchpad into `features-service/tests/fixtures/forexfactory/` in the same pass (real HTTP evidence is otherwise
  session-ephemeral and expensive to re-capture given Cloudflare's rate limiting).
- **2026-08-09 (Cloudflare blocker resolved + adapter shipped)**: operator asked to actually tackle the Cloudflare
  blocker rather than leave it parked. Tested empirically, not assumed: plain Playwright and `patchright` (a
  purpose-built anti-detection fork) are BOTH blocked by the site's Managed Challenge, from both a residential dev IP
  and the real GCP backfill region (`asia-northeast1-c`) — ruling out "it's just this sandbox's IP." The working
  combination: `nodriver` + a real Google Chrome binary + headed mode + a residential IP (this machine's genuine UK
  residential ISP). Verified end-to-end against the live site with real historical data (2007-01-01 week, 55 records
  including the correct NFP release). Shipped: `unified-api-contracts@cbb3e2b33` (schema + registry),
  `features-service@b6809756` (adapter + calculator + CLI handler + 28 tests). Also fixed 3 unrelated pre-existing
  empty-string-fallback ratchet violations that were blocking the push (confirmed via git-stash to predate this change)
  — `unified-trading-pm@533c2fa3fc` ratchets the baseline down. Remaining: a residential-proxy account
  (BLOCKED-CREDENTIALS, recommended IPRoyal PAYG ~$7 total) for the actual GCP-hosted historical backfill + the VM
  launcher wrapper itself — both now separately tracked todos above, not re-blocked on any open design question.
