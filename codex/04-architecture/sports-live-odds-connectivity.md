---
doc_type: codex-ssot
title: Sports Live Odds Connectivity
summary:
  The two LIVE odds connectivity paths for sports bookmakers — The Odds API (REST poll, no login) and exchange APIs
  (Betfair/Smarkets, keys only); latency/auth trade-offs, MDPS as producer. The former third path (login+scrape workers)
  was retired 2026-07-08 and is documented here only as history (§3).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, market-data-processing-service]
scope: [engineer, admin]
tags: [sports, odds, mdps, live-trading, footystats]
related: [sports-integration-plan.md, sports-batch-live.md]
created: 2026-03-27
authoritative_for:
  [sports live-odds connectivity paths (aggregator/exchange; scraper path retired 2026-07-08, historical only)]
referenced_by:
  [
    codex/02-data/sports-scheduling-and-sharding.md,
    codex/04-architecture/sports-batch-live.md,
    codex/04-architecture/sports-integration-plan.md,
  ]
owner:
last_reviewed: 2026-07-23
code_refs:
---

# Sports Live Odds Connectivity

> **✅ CORRECTED (2026-07-23) — §3 rewritten as historical, not just banner-flagged.** A 2026-07-19 pass first flagged
> that §3 described deleted code but never rewrote the section itself; this pass fixes the body. There are now only
> **two live** connectivity paths (§1 The Odds API, §2 Exchanges) — the third path (login+scrape workers, formerly §3)
> was **retired 2026-07-08** (execution-service@29a888a8d, "retire the 14 bookmaker scrapers" per operator decision) and
> §3 below now documents it in past tense, for history only. Separately: the in-play WebSocket connector
> (`odds_api_ws.py`) is effectively dark (14 rows in 6 years, measured), so HT-horizon starvation on the Odds API path
> is structural — not fixed by anything below.

How we connect to bookmakers in **live** mode: no batch files, real-time (or near real-time) odds. This doc is the SSOT
for the two live connectivity paths (Odds API, exchanges) plus, for history only, the retired scraper path.

---

## TL;DR

| Source                                               | Live path                 | Login/scrape?      | Latency                        |
| ---------------------------------------------------- | ------------------------- | ------------------ | ------------------------------ |
| **The Odds API**                                     | REST poll → Pub/Sub       | No                 | 40–60s (their update interval) |
| **Exchanges** (Betfair, Smarkets, Matchbook, Betdaq) | REST/stream API → Pub/Sub | No (API keys only) | 5–30s configurable             |

**Retired, historical only — not a live path:** Scrapers (SkyBet, Coral, etc.) — browser automation with login/geo, 14
bookmaker adapters, deleted 2026-07-08. See §3.

**Live “beef”:** `market-data-processing-service` (with `asset_group=SPORTS`, Batch B) is the producer: it polls the two
live adapter families above on a schedule and writes snapshots to GCS + publishes deltas to Pub/Sub.
`features-service (sports family)` consumes via **Pub/Sub** (live seam). So “connecting live” = that service calling
USEI adapters on an interval and pushing to Pub/Sub.

> **Note (2026-03-01):** `sports-odds-data-service` and `sports-odds-processing-service` have been consolidated into
> `market-data-processing-service` as part of the sports service consolidation. See `sports-integration-plan.md`
> Changelog 2026-03-01.

---

## 1. The Odds API (aggregator) — no login, no scrape

- **Provider:** [The Odds API](https://the-odds-api.com/) (the-odds-api.com). We use v4 REST only.
- **Live mechanism:** They do **not** offer WebSocket. Odds update on **fixed intervals**
  ([update-intervals](https://the-odds-api.com/sports-odds-data/update-intervals.html)):
  - Pre-match: 60s (featured markets), 5 min (outrights).
  - In-play: 40s (featured), 60s (additional).
  - Exchanges (when requested via Odds API): 30s pre-match, 20s in-play.
- **How we connect live:** A job in `market-data-processing-service` (asset_group=SPORTS) polls the Odds API at or just
  above their interval (e.g. every 45–60s). Each response is written to GCS (snapshots) and/or published to Pub/Sub
  (`market-data-updated` with asset_group=SPORTS). No login, no browser; just REST + API key (Secret Manager).
- **Bookmakers covered:** All keys in our `ODDS_API_KEY_MAP` (UK/EU/US/AU). One REST call can return many bookmakers; we
  map their keys to our canonical registry and emit `CanonicalOdds` per bookmaker.

---

## 2. Exchanges — API-only, no scrape

- **Adapters:** Betfair, Smarkets, Matchbook, Betdaq (USEI exchange adapters).
- **Live mechanism:** Each has a **REST API** (and some have streaming). We call `get_odds(fixture_id, markets)` (and
  optionally `get_fixtures_with_odds`) on a schedule. No browser, no login UI; credentials are API keys / client certs
  in Secret Manager.
- **How we connect live:** `market-data-processing-service` (asset_group=SPORTS) runs a loop (e.g. every 5s for
  exchanges) and calls each exchange adapter; results are written to GCS and published to Pub/Sub. Concurrency: asyncio
  gather across exchanges; rate limits per exchange (Betfair, Smarkets, etc.) are respected in each adapter.
- **Latency:** Typically 5–30s poll interval; sub-second if an exchange offers streaming and we add a stream client
  later.

---

## 3. Scrapers — RETIRED 2026-07-08 (historical only, not a live path)

**This section is history, not current architecture.** Do not build against it; there is no scraper code to call.

- **What existed:** 14 per-bookmaker Playwright-based scraper adapters that loaded each bookmaker's **public** page
  (e.g. `skybet.com/football/match/{fixture_id}`), parsed HTML, and for sites that gated full odds behind login/geo ran
  a logged-in browser session (cookies, optional residential proxy) instead. Adapters covered: Bet365, 888sport,
  Betfred, BetVictor, Betway, BoyleSports, Bwin, Coral, Ladbrokes, PaddyPower, SBOBet, SkyBet, Unibet, William Hill. (An
  earlier version of this doc listed only 13 of these — SkyBet, Coral, Paddy Power, Ladbrokes, Bet365, Betway, Unibet,
  888sport, William Hill, Betfred, BetVictor, BoyleSports, Bwin — omitting SBOBet; corrected here against the retirement
  commit's own docstring.)
- **What happened:** **Deleted 2026-07-08** (`execution-service@29a888a8d`, operator decision verbatim "retire the 14
  bookmaker scrapers"). Verified in the current repo: `execution_service/sports_execution/adapters/scrapers/` holds no
  source files, and `execution_service/sports_execution/adapters/__init__.py` now carries only the retirement note and
  imports the surviving Odds API / bookmaker-API / exchange / paper adapters. Rationale: 0 rows were ever captured in
  production via this path — it never earned its login/geo/session maintenance cost. This superseded an earlier
  (2026-05-12) "keep as dormant scaffolding, retire indefinitely" call. Provenance:
  `unified-trading-pm/plans/epics/sports_master.md` § "Scrapers retired 2026-07-08 per operator".
- **What replaced it:** Nothing runs in its place — there is no scraper fallback anymore. The Odds API aggregator (§1)
  already covers most of the same brands under its own keys (`sport888`, `betvictor`, `betway`, `boylesports`, `coral`,
  `ladbrokes_uk`, `paddypower`, `skybet`, `unibet_uk`, `williamhill`, …); that remains the only live path for them. A
  bookmaker that was scraper-only and is **not** covered by the Odds API today has **no live odds path** in this system
  — that is an accepted coverage gap (operator-accepted cost of retirement), not an open TODO tracked elsewhere in this
  doc.

---

## Where the “live beef” lives

- **Producer:** `market-data-processing-service` (asset_group=SPORTS, Batch B). It holds the list of **live** adapters
  (Odds API, exchanges — scraper adapters were retired 2026-07-08, see §3), runs `run_live_polling()` (or equivalent),
  and for each cycle:
  - Calls each adapter’s `get_odds` (and optionally `get_fixtures_with_odds`).
  - Writes snapshots to GCS.
  - Publishes delta events to Pub/Sub topic `market-data-updated` (with asset_group=SPORTS attribute).
  - Performs arbitrage detection and normalization inline (previously in separate `sports-odds-processing-service`).
- **Consumers:**
  - `features-service (sports family)` in live mode uses `LiveDataSource` (Pub/Sub subscription) to receive records
    (fixture + odds or derived data) and runs the feature pipeline per fixture.
- So **connecting to bookmakers live** = ensuring `market-data-processing-service` is running with SPORTS category, the
  right adapters and config (Odds API key, exchange keys) and that it publishes to the topic the downstream services
  subscribe to. There is no scraper credential/session path anymore.

> **Note (2026-03-01):** The previous architecture had a separate `sports-odds-processing-service` consuming from
> `sports-odds-data-service`. Both are now consolidated into `market-data-processing-service` with `asset_group=SPORTS`.
> Arbitrage detection and odds normalization happen within the same service.

---

## Summary table

| Connectivity                                  | Auth           | Live implementation                              | Maintenance |
| --------------------------------------------- | -------------- | ------------------------------------------------ | ----------- |
| Odds API                                      | API key only   | Poll REST every 40–60s → GCS + Pub/Sub           | Low         |
| Exchanges                                     | API key / cert | Poll (or stream) API every 5–30s → GCS + Pub/Sub | Low         |
| ~~Scrapers~~ (RETIRED 2026-07-08, historical) | n/a — deleted  | n/a — deleted; see §3                            | n/a         |

Use **The Odds API for live** wherever it covers the bookmaker and 40–60s latency is acceptable; use **exchanges** for
low-latency API. Scrapers are retired and not an available option — there is no code to run, and building a new one
would require an explicit operator decision to reverse the 2026-07-08 retirement.
