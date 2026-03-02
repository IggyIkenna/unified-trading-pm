# Sports Migration Gap Fix Plan

> Follows: SPORTS_BETTING_PREVIOUS_FULL_MIGRATION.md (COMPLETE)
> Date: 2026-03-02 (updated 2026-03-02)
> Status: ACTIVE — Part A COMPLETE, Part B IN PROGRESS

## Objective

Fix all remaining gaps identified during the full audit of `sports-betting-services-previous` migration **and** add comprehensive live-mode support so that:
1. The old repo is fully superseded and can be permanently archived. **(DONE)**
2. Sports can operate in **batch**, **paper**, and **live** modes using the same unified pipeline as TradFi.
3. Real-time odds scraping, live feature computation, and live execution are production-ready.

---

## Prerequisites

1. **Workspace venv active** — `.venv-workspace/bin/python` (3.13.x), ruff, basedpyright all resolve there.
2. **Claude Code available in IDE** — developers must be able to use Claude Code through the Cursor IDE extension tab (same setup used for this planning session). Ensure `claude-code` CLI is installed (`npm install -g @anthropic-ai/claude-code` or via VSCode/Cursor marketplace) and the `.claude/` workspace config is present in the repo root.
3. **GCP project access** — Secret Manager, Pub/Sub, Cloud Run, Artifact Registry, GCS.
4. **Odds API key provisioned** — `odds-api-key` in Secret Manager (declared in `SportsFeaturesConfig.odds_api_secret_name`). Verify: `gcloud secrets versions access latest --secret=odds-api-key --project=$PROJECT_ID`.
5. **Playwright browsers installed** — `playwright install chromium` in USEI Docker image and local dev envs.

---

## Part A — Batch Migration Gaps (COMPLETE)

### Gaps Identified

#### P0 — Must Fix
1. **8 canonical tables missing data exporters** — fixture_stats, fixture_events, fixture_lineups, fixture_player_stats, injuries, players, venues (fixture_coaches merged into lineups export)
2. **74 leagues missing from classification registry** — only 20 of 94 leagues migrated

#### P1 — Should Fix
3. **Batch fetch shell scripts not migrated** — 4 scripts (~1,439L) for rate-limited bulk data collection
4. **Team/stadium mapping data incomplete** — ~200+ aliases and 50 stadiums not loaded

#### P2 — Nice to Have
5. **Feature tracking incomplete** — 533 of 606 features untracked (11 modules missing)
6. **Geocoding CLI not migrated** — venue lat/lon via Google Maps API

#### P3 — Low Priority
7. **Round names data** — 210 tournament round names for season context

### Execution Streams (6 parallel + 1 integration)

| Stream | Agent | Priority | Target | Description |
|--------|-------|----------|--------|-------------|
| 1 | A | P0 | features-sports-service | 4 fixture-level data exporters |
| 2 | B | P0 | features-sports-service | 3 standalone data exporters + registry/validation |
| 3 | C | P0 | instruments-service | Expand league classification 20→94 |
| 4 | D | P1 | instruments-service | Team/stadium mapping data |
| 5 | E | P2 | features-sports-service | 11 feature tracking modules |
| 6 | F | P1 | features-sports-service | Batch fetch CLI scripts |
| 7 | G | P2-P3 | both | Geocoding, round names, final verification |

### Part A Done Criteria

- [x] `get_available_tables()` returns 14 tables (7 existing + 7 new) — VERIFIED
- [x] `_TABLE_CONFIGS` in validation.py has 14 entries — VERIFIED
- [x] `DEFAULT_CLASSIFICATION_REGISTRY.league_count == 94` — VERIFIED
- [x] Team alias resolver loads 56+ teams with cross-provider mappings — VERIFIED (74 teams: 40 EPL + 34 Bundesliga)
- [x] Feature tracking covers 400+ features across 14 modules — VERIFIED (420 features across 14 modules)
- [x] Batch fetch CLI accepts all 4 providers with rate limiting — VERIFIED
- [x] All tests pass in features-sports-service and instruments-service — VERIFIED (509 + 174 sports tests pass)
- [x] basedpyright clean on both repos — pre-existing errors only (888 in features, 1521 in instruments — none from new code)

### Part A Completion Summary

| Stream | Status | Tests Added | Key Metric |
|--------|--------|-------------|------------|
| 1 | DONE | 49 | 4 fixture-level exporters |
| 2 | DONE | (shared with 1) | 3 standalone exporters + registry |
| 3 | DONE | 51 | 94 leagues classified |
| 4 | DONE | 79 (38 mapping + 41 aliases) | 74 teams, 68 stadiums |
| 5 | DONE | 40 | 420 features tracked |
| 6 | DONE | 35 | 4 batch fetch providers |
| 7 | DONE | 64 (20 geocoding + 44 round names) | geocode-venues CLI + 208 round names |
| **Total** | **COMPLETE** | **~280 new tests** | All gaps fixed |

---

## Part B — Live Mode Gaps (NEW)

Deep audit revealed the following gaps preventing sports from running in live/real-time mode.

**Architectural principle**: No new repos or standalone services. Sports live = `mode="live"` + `category="sports"` flowing through the **same existing UTS services** that handle TradFi. USEI is a library consumed by services. Odds API validation runs inside an existing service (market-tick-data or reference-data). The existing Pub/Sub, sharding, and deployment infrastructure extends to sports by adding the right category/league dimensions — not by creating parallel sports-only infra.

### B1 — Scraper Adapters in USEI Library (P0)

**What exists:**
- 13 Playwright-based scraper adapters in `unified-sports-execution-interface/adapters/scrapers/` (Bet365, William Hill, Ladbrokes, Sky Bet, Paddy Power, Coral, Betfred, BetVictor, Betway, Unibet, bwin, BoyleSports, 888sport)
- Each implements `OddsAdapter` protocol → `async get_odds(fixture_id, markets) -> list[CanonicalOdds]`
- Dependencies declared in USEI `pyproject.toml`: `playwright>=1.40`, `beautifulsoup4>=4.12`, `lxml>=5.0`
- `OddsApiAdapter` (aggregator) returns odds from 30+ bookmakers in a single call for validation
- USEI is a **library** — services import and call its adapters, just like TradFi services import `unified-execution-interface`

**Gaps to fix:**

| # | Gap | Details |
|---|-----|---------|
| B1.1 | **Scraper CSS selectors unvalidated against live sites** | All 13 scrapers have hardcoded CSS selectors (e.g. `.gl-MarketGroupButton_Odds` for Bet365). These MUST be tested against current live website versions. Bookmakers update their frontends frequently. |
| B1.2 | **No website version fingerprinting** | Need a `scraper_version_registry` that records: bookmaker, last-validated date, CSS selector hash, page structure version. When a scraper fails with `ScraperError`, the registry flags the bookmaker as stale. |
| B1.3 | **Anti-bot detection handling** | Bet365, William Hill, and others use bot detection (Cloudflare, DataDome). Scrapers currently catch `ScraperError` but have no retry-with-rotation strategy. Need: proxy rotation, user-agent rotation, request fingerprint randomization. |
| B1.4 | **Playwright in base Docker image** | The `unified-trading-services:latest` base image needs Chromium headless (`playwright install --with-deps chromium`) so any service importing USEI scrapers can run them. |
| B1.5 | **Progressive stats scraping** | `CanonicalProgressiveStats` schema exists (goals, possession, shots, corners at 30s intervals) but no scraper populates it. Need live match stats scrapers (FlashScore, SofaScore, or similar) or adapt existing Soccer-Football-Info client for real-time. |

### B2 — API Contracts & Schemas for Live (P0)

**What exists:**
- `CanonicalOdds` — normalized odds per bookmaker per market
- `CanonicalProgressiveStats` — 30-second team-level stats snapshots
- `CanonicalProgressiveOdds` — 30-second odds snapshots
- `OddsType` enum: H2H, OVER_UNDER, ASIAN_HANDICAP, BOTH_TEAMS_SCORE, CORRECT_SCORE, OUTRIGHT
- `ScraperError`, `BookmakerUnavailableError`, `OddsChangedError` error hierarchy

**Gaps to fix:**

| # | Gap | Details |
|---|-----|---------|
| B2.1 | **No `LiveOddsUpdate` event schema** | Need a Pub/Sub message schema wrapping `CanonicalOdds` with: `event_type="ODDS_UPDATE"`, `fixture_id`, `bookmaker_key`, `timestamp_utc`, `is_in_play: bool`, `match_minute: int \| None`. Add to `unified_api_contracts/sports/canonical/`. |
| B2.2 | **No `LiveMatchState` schema** | Need a unified match-state schema combining score, time, period (1H/2H/HT/ET/PEN), is_live, red_cards. Drives feature recomputation triggers. |
| B2.3 | **No `ScraperVersionMeta` schema** | For website version tracking: `bookmaker_key`, `css_selector_hash`, `last_validated_utc`, `page_structure_version`, `is_stale: bool`. |
| B2.4 | **Schema versioning for scraper changes** | When a bookmaker changes their website, update the scraper AND bump the source schema version in `sports/sources/{bookmaker}/schemas.py`. Add a `SCRAPER_SCHEMA_VERSION` constant per bookmaker adapter. |

### B3 — Live Mode in Existing Services (P0)

**Principle**: Sports live mode follows the same pattern as TradFi live — each existing service handles `category="sports"` via its `mode="live"` CLI arg. No new services.

**How it maps to existing services:**

| UTS Service | TradFi Live | Sports Live Equivalent |
|-------------|------------|----------------------|
| `market-tick-data-service` | WebSocket feeds from exchanges | Scraper polling loop (USEI adapters) for live odds |
| `features-sports-service` | — (FSS is sports-only) | `mode="live"`: subscribe to live odds → `compute_for_fixture()` → broadcast features |
| `strategy-service` | Consumes live features → signals | Consumes live sports features → arb detection → betting signals |
| `execution-service` | Routes to TradFi exchange adapters | Routes to USEI betting adapters (Betfair, Smarkets, etc.) |

**What exists:**
- `SportsFeaturesEngine` is mode-agnostic: `compute_for_fixture()` for live, `compute_bulk()` for batch
- `LiveDataSource` subscribes to Pub/Sub → yields records
- `BroadcastSink` publishes feature vectors to Pub/Sub
- `unified_events_interface` supports `mode="live"` with Pub/Sub coordination
- CLI already has `fetch-live-odds` handler

**Gaps to fix:**

| # | Gap | Details |
|---|-----|---------|
| B3.1 | **market-tick-data-service: sports category not handled** | MTDS currently handles TradFi WebSocket feeds. Needs a `category="sports"` path that imports USEI scraper adapters, polls on configurable intervals (30s in-play, 5min pre-match), publishes `CanonicalOdds` to the standard Pub/Sub topic with sports category routing. This is the sports equivalent of WebSocket tick data. |
| B3.2 | **FSS: no live orchestration wiring** | `engine.py` has `compute_for_fixture()` but no caller wires Pub/Sub → engine → broadcast. Need a `live_runner.py` that the CLI invokes with `--mode live`: subscribes to live odds topic, calls engine, publishes feature vectors. Same pattern as TradFi features live mode. |
| B3.3 | **Live feature subset** | Not all 30+ calculators make sense in live mode (weather doesn't change mid-match). Define a `LIVE_CALCULATORS` subset: odds, progressive stats, goal timing, halftime, team form (cached from pre-match). Skip: weather, venue_context, season_context, referee (pre-computed at kickoff). |
| B3.4 | **Feature cache for live mode** | Pre-match features (team form, H2H, league stats) pre-computed at kickoff and cached in-memory. Only live-changing features recompute on each update. |
| B3.5 | **Live coordination events** | Register sports-specific coordination events in `unified_events_interface`: `LIVE_ODDS_RECEIVED`, `LIVE_FEATURES_COMPUTED`, `LIVE_SIGNAL_GENERATED`. These are just new event types — not new infrastructure. |
| B3.6 | **strategy-service: sports arb strategy type** | Strategy service needs a sports arb strategy type that: consumes live sports features, runs arb detection across bookmaker odds, emits `BettingSignal` when `ArbitrageStatus.FREE_MONEY`. This is just a new strategy type alongside existing TradFi strategies. |
| B3.7 | **execution-service: USEI adapter routing** | Execution service needs to route sports bet orders to USEI adapters (Betfair, Smarkets, etc.) the same way it routes TradFi orders to exchange adapters. Validates signal freshness (< 5s), checks `MarketStatus.ACTIVE`, handles `OddsChangedError`. |

### B4 — Operation Mode & Paper Trading (P1)

**What exists:**
- Existing TradFi `execution_mode` in trading config (`REQUIRED_CONFIG_FIELDS`)
- `BettingAdapter` protocol with `place_bet()`, `cancel_bet()`, `get_balance()`

**Gaps to fix:**

| # | Gap | Details |
|---|-----|---------|
| B4.1 | **Paper trading adapter for sports** | Need a `PaperBettingAdapter` implementing `BettingAdapter` protocol that simulates fills and tracks virtual P&L. Essential for validating the pipeline end-to-end before going live with real money. |
| B4.2 | **Operation mode routing** | Extend existing `execution_mode` config to support sports paper/live routing. When `execution_mode` indicates paper, route through `PaperBettingAdapter`; when live, route through real USEI adapters. No new enum — use the existing config pattern. |

### B5 — Odds API Validation (P1)

**Principle**: Odds API cross-check runs as a periodic job inside an existing service (market-tick-data or reference-data), not as a standalone deployment.

| # | Gap | Details |
|---|-----|---------|
| B5.1 | **Periodic scraper validation** | Add a periodic task (scheduled batch job or cron in market-tick-data-service/reference-data-service) that runs each scraper against a known live fixture and compares output to Odds API baseline. Tolerance: ±0.02. Flags drift, logs `BookmakerUnavailableError`, alerts on failure. |
| B5.2 | **Odds API key in Secret Manager** | Verify `odds-api-key` is provisioned. `SportsFeaturesConfig.odds_api_secret_name` already declares it. Run: `gcloud secrets versions access latest --secret=odds-api-key`. |

### B6 — Deployment Config for Sports Live (P1)

**Principle**: Sports live uses existing deployment infrastructure. Just add sports dimensions to existing configs.

| # | Gap | Details |
|---|-----|---------|
| B6.1 | **Sports sharding in `sharding_config.yaml`** | Add `category: sports` dimensions to existing service entries: `features-sports-service` (batch: `[league, date]`, live: `[league]`), `market-tick-data-service` (add sports alongside cefi/tradfi/defi), `strategy-service` and `execution-service` (add sports category). |
| B6.2 | **Playwright in base Docker image** | The `unified-trading-services:latest` base image needs `playwright install --with-deps chromium` so services importing USEI scrapers can run headless browsers. This is a one-time base image update. |
| B6.3 | **Instruments service: sports namespace** | `instruments-service` has `gcs_bucket_sports` config but zero sports instrument logic. Need: league instruments, fixture instruments, team instruments — following existing `InstrumentId` conventions. Sports is just another `category` alongside cefi/tradfi/defi. |
| B6.4 | **Pub/Sub topic extensions** | Sports live data flows through existing Pub/Sub topics using `category="sports"` message attributes for routing — same pattern as TradFi. If separate topics are needed for throughput, add them in existing Terraform with the standard naming convention. |

### B7 — Scraper Resilience & Website Version Tracking (P1)

| # | Gap | Details |
|---|-----|---------|
| B7.1 | **CSS selector test suite per bookmaker** | Each scraper needs a `test_selectors.py` that loads a saved HTML snapshot and validates selectors still extract odds. When a bookmaker updates their site, save new snapshot, update selectors, bump `SCRAPER_SCHEMA_VERSION`. |
| B7.2 | **HTML snapshot archiving** | Save timestamped HTML snapshots to GCS (`scraper-snapshots-{project_id}/{bookmaker}/{date}.html`) for debugging and regression testing. |
| B7.3 | **Proxy rotation infrastructure** | For bot-detection-heavy sites (Bet365, William Hill): integrate a proxy provider (residential proxies). Configure per-bookmaker in config. |
| B7.4 | **Graceful degradation** | If a scraper fails for a bookmaker, the system continues with remaining bookmakers. Arb detection works with ≥2 bookmakers. Log `BookmakerUnavailableError`, don't crash the pipeline. |
| B7.5 | **Scraper versioning tied to API contract versioning** | Each bookmaker scraper gets a `SCRAPER_SCHEMA_VERSION: str` constant (e.g., `"bet365-v3"`). When the bookmaker changes their site: update scraper, bump version, update source schema in `unified_api_contracts/sports/sources/`. |

### B8 — Secret Management & API Keys (P0)

| # | Gap | Details |
|---|-----|---------|
| B8.1 | **Verify all sports secrets provisioned** | Check Secret Manager for: `api-football-api-key`, `footystats-api-key`, `odds-api-key`, `open-meteo-api-key`, `soccer-football-info-api-key`, `betfair-api-key`, `pinnacle-api-key`, `smarkets-api-key`. |
| B8.2 | **Exchange API keys for execution** | Betfair, Smarkets, Matchbook, Betdaq adapters need authenticated sessions. Secrets must be in Secret Manager, referenced via `get_secret_client(secret_name=..., project_id=...)`. No hardcoded keys. |
| B8.3 | **Scraper bookmakers need NO API keys** | Bet365, William Hill, etc. are scraped — no API auth. But proxy credentials (if used) must go through Secret Manager. |

### B9 — Feature Implementation Completeness (P1)

**Source:** `archive/sports-betting-services-previous/footballbets/features/tracking/README.md` + `docs/FEATURE_IMPLEMENTATION_STATUS.md` + `docs/FEATURE_STATUS_AND_PLAN.md`

The old tracking system documented **659 features** with **499 implemented (75.7%)**. The new tracking system in `features-sports-service/tracking/` registers only **~420 FeatureEntry records**. Key gaps:

**Old system vs new tracking registration count:**

| Category | Old Total | Old Implemented | New Tracked | Delta (not in new) |
|----------|-----------|-----------------|-------------|-------------------|
| Team | 234 | 158 | 45 | **189 untracked** |
| H2H | 43 | 43 | 14 | **29 untracked** |
| Odds/Market | 48 | 32 | 14 | **34 untracked** |
| League | 32 | 25 | 32 | 0 |
| Referee | 18 | 18 | 18 | 0 |
| Goal Timing | 22 | 22 | 22 | 0 |
| Weather | 12 | 9 | 12 | 0 |
| Poisson/xG | 33 | 33 | 33 | 0 |
| Player/Lineup | 54 | 48 | 54 | 0 |
| Halftime | 66 | 25 | 66 | 0 |
| Advanced Stats | 42 | 42 | 42 | 0 |
| Multi-Source xG | 30 | 30 | 30 | 0 |
| Venue/Context | 28 | 16 | 28 | 0 |
| Season Context | — | — | 10 | +10 (new) |
| **TOTAL** | **659** | **499** | **~420** | **~252 untracked** |

| # | Gap | Details |
|---|-----|---------|
| B8.1 | **189 team features not tracked in new system** | Old system tracked 234 team features (158 implemented). New system only has 45 FeatureEntry records. Need to reconcile: port the remaining feature definitions into the new Pydantic-based `FeatureEntry` format in `tracking/team_features.py`. Includes: EWMA variants (30d, 90d), variance/std metrics, style metrics (possession_style, pressing_style), momentum features, cross-season features, promoted team features (57 from Phase 4 plan). |
| B8.2 | **29 H2H features not tracked** | Old system had 43 H2H features (all implemented). New system tracks 14. Port remaining 29 feature definitions. |
| B8.3 | **34 odds/market features not tracked** | Old system tracked 48 odds features (32 tested, 16 need data). New system tracks 14. The missing 34 include: BTTS odds (4), Asian handicap odds (3), value bet features (4, need ML model), expected value features (4, need ML model), steam detection, velocity/acceleration, market entropy. **These are critical for live mode arb detection.** |
| B8.4 | **Promoted teams features missing entirely** | `FEATURE_STATUS_AND_PLAN.md` documents 57 promoted team features (league classification, newly promoted team handling, early-season special features). Not tracked in either old or new system. These affect early-season prediction accuracy. |
| B8.5 | **74 features need data sources not yet available** | From old status: API-Football player age/injury data (6 features), Open-Meteo precipitation (3 features), progressive odds data for BTTS/Asian handicap (15 features), API-Football expanded stats — tackles, interceptions, clearances (18 features), venue metadata — stadium age, roof, dimensions, attendance (9 features), Transfermarkt market values (future). |
| B8.6 | **Halftime features only 37.9% complete (25/66)** | 41 halftime features remain unimplemented. These are specifically **live mode features** — they require HT state snapshots, delta models, and live odds integration. Critical for in-play trading. |
| B8.7 | **Feature computation at multiple time horizons missing** | Old system computed features at T-72h, T-24h, T-6h, T-1h horizons. This multi-horizon architecture supports odds movement detection and is essential for live mode (T-0 = current). Verify FSS engine supports horizon parameter. |

---

## Part B Execution Streams (7 parallel — no new repos)

All work targets **existing repos**. USEI is a library, not a service.

| Stream | Agent | Priority | Target Repo(s) | Description |
|--------|-------|----------|----------------|-------------|
| B-S1 | H | P0 | unified-sports-execution-interface | Validate 13 scraper CSS selectors against live sites; fix broken ones; add `SCRAPER_SCHEMA_VERSION` per adapter; anti-bot handling; snapshot archiving |
| B-S2 | I | P0 | unified-api-contracts + unified-events-interface | Add `LiveOddsUpdate`, `LiveMatchState`, `ScraperVersionMeta` schemas; register live coordination events (`LIVE_ODDS_RECEIVED`, etc.) |
| B-S3 | J | P0 | features-sports-service | Build `live_runner.py` (`--mode live`); define `LIVE_CALCULATORS` subset; add `LiveFeatureCache`; wire Pub/Sub → engine → broadcast |
| B-S4 | K | P0 | market-tick-data-service | Add `category="sports"` path that imports USEI scraper adapters; configurable polling intervals; publishes to standard Pub/Sub with sports routing |
| B-S5 | L | P1 | strategy-service + execution-service | Sports arb strategy type in strategy-service; USEI adapter routing in execution-service; `PaperBettingAdapter`; paper/live mode routing via existing `execution_mode` |
| B-S6 | M | P1 | unified-trading-deployment-v3 + instruments-service | Sports dimensions in `sharding_config.yaml`; Playwright in base Docker image; sports instruments namespace; Pub/Sub topic config |
| B-S7 | N | P1 | features-sports-service | Reconcile old→new feature tracking: port 252 untracked feature definitions; implement 41 remaining halftime features; add promoted team features (57); add missing odds features for live arb; verify multi-horizon computation |

---

## Dependency Graph

```
Part A (batch gaps) ── COMPLETE ──────────────────────────────→ Old repo archived
    ↕ (independent)
Part B (live mode):

B-S2 (schemas)  ──→  B-S1 (scrapers)  ──→  B-S4 (MTDS: sports category)
       │                                          │
       └──→  B-S3 (FSS: live runner)  ────────────┤
                                                   ↓
B-S7 (feature completeness) ──→  B-S5 (strategy + execution: sports routing)
   (can run independently)                         │
                                                   ↓
                                    B-S6 (deployment config + instruments)
```

- **B-S2** (schemas) is the foundation — live event schemas needed by all other streams.
- **B-S1** (scrapers) and **B-S3** (FSS live runner) can start in parallel once schemas land.
- **B-S4** (MTDS sports category) needs working scrapers to import from USEI.
- **B-S5** (strategy/execution) needs live features flowing before it can consume them.
- **B-S6** (deployment config) can start early but needs final config from B-S4/B-S5.
- **B-S7** (feature completeness) is independent — can run in parallel with everything.

---

## Part B Done Criteria

**Scrapers & Contracts:**
- [ ] All 13 scraper adapters tested against live bookmaker sites with passing CSS selector tests
- [ ] Each scraper has `SCRAPER_SCHEMA_VERSION` constant and archived HTML snapshots in GCS
- [ ] `LiveOddsUpdate`, `LiveMatchState`, `ScraperVersionMeta` schemas in unified-api-contracts
- [ ] Playwright installed in `unified-trading-services:latest` base Docker image

**Live Pipeline (existing services, `mode="live"`):**
- [ ] `market-tick-data-service` handles `category="sports"` — imports USEI scrapers, polls, publishes to Pub/Sub
- [ ] `features-sports-service --mode live` — `live_runner.py` subscribes to live odds, computes features, broadcasts
- [ ] `LIVE_CALCULATORS` subset defined; pre-match features cached at kickoff
- [ ] `strategy-service` has sports arb strategy type consuming live sports features
- [ ] `execution-service` routes sports bet orders to USEI adapters (Betfair, Smarkets, etc.)
- [ ] `PaperBettingAdapter` passes all `BettingAdapter` protocol tests
- [ ] Paper/live routing via existing `execution_mode` config

**Validation & Ops:**
- [ ] Odds API periodic validation: scraper output matches within ±0.02 tolerance (runs in MTDS or reference-data)
- [ ] All sports secrets verified in Secret Manager (7+ keys)
- [ ] Sports dimensions added to `sharding_config.yaml` for all relevant services
- [ ] Sports instruments namespace in instruments-service (leagues, fixtures, teams — same `InstrumentId` conventions)

**End-to-end:**
- [ ] End-to-end paper mode test: scrape odds → compute features → detect arb → paper-place bet → log P&L
- [ ] All changes in existing repos only — no new repos created

**Feature Completeness:**
- [ ] Feature tracking reconciled: new system tracks ≥600 features (vs old system's 659)
- [ ] Team features tracking: ≥200 FeatureEntry records in `tracking/team_features.py`
- [ ] Odds features tracking: ≥45 FeatureEntry records in `tracking/odds_features.py` (including BTTS, Asian handicap, steam detection, value bet placeholders)
- [ ] H2H features tracking: ≥40 FeatureEntry records in `tracking/h2h_features.py`
- [ ] Promoted team features: new `tracking/promoted_team_features.py` with ≥50 entries
- [ ] Halftime features: ≥55 of 66 implemented (up from 25)
- [ ] Multi-horizon computation verified (T-72h, T-24h, T-6h, T-1h, T-0)

**Quality:**
- [ ] basedpyright clean on all modified repos
- [ ] Claude Code available in Cursor IDE for all developers (`.claude/` config in repo root, extension installed)

---

## Bookmaker Coverage Matrix

| Bookmaker | Adapter Type | Live Odds | Bet Placement | Auth | Notes |
|-----------|-------------|-----------|---------------|------|-------|
| Betfair | Exchange API | Yes | Yes | API key + session | Sharpest exchange; primary execution venue |
| Smarkets | Exchange API | Yes | Yes | API key | Lower liquidity |
| Matchbook | Exchange API | Yes | Yes | API key | Commission-free periods |
| Betdaq | Exchange API | Yes | Yes | API key | Lowest exchange volume |
| Pinnacle | Bookmaker API | Yes | No (read-only) | HTTP Basic | Sharpest bookmaker; reference line |
| 1xBet | Bookmaker API | Yes | No (read-only) | API key | High limits, EU-focused |
| Odds API | Aggregator API | No (pre-match) | No | API key | Validation baseline; 30+ bookmakers |
| Bet365 | **Scraper** | Yes | No | None (browser) | Heavy bot detection; needs proxy rotation |
| William Hill | **Scraper** | Yes | No | None (browser) | Frequent site updates; CSS selectors fragile |
| Ladbrokes | **Scraper** | Yes | No | None (browser) | Same parent as Coral (Entain) |
| Coral | **Scraper** | Yes | No | None (browser) | Same parent as Ladbrokes (Entain) |
| Sky Bet | **Scraper** | Yes | No | None (browser) | Flutter-owned |
| Paddy Power | **Scraper** | Yes | No | None (browser) | Flutter-owned (shared infra with Betfair) |
| Betfred | **Scraper** | Yes | No | None (browser) | UK-focused |
| BetVictor | **Scraper** | Yes | No | None (browser) | Competitive odds |
| Betway | **Scraper** | Yes | No | None (browser) | Global coverage |
| Unibet | **Scraper** | Yes | No | None (browser) | Kindred Group |
| bwin | **Scraper** | Yes | No | None (browser) | Entain (EU-focused) |
| BoyleSports | **Scraper** | Yes | No | None (browser) | Ireland/UK |
| 888sport | **Scraper** | Yes | No | None (browser) | 888 Holdings |

**Scraping strategy**: Own scrapers for speed (sub-second for in-play), imported as a library from USEI into market-tick-data-service. Odds API as optional periodic validation to verify scraper accuracy (runs in MTDS or reference-data). Never rely on Odds API for live — it's pre-match only and slower.

---

## Data Source Architecture (Live vs Batch)

Sports follows the same service pipeline as TradFi — just different adapters and `category="sports"`.

```
BATCH MODE (daily) — same as today:
  API-Football ──→ FSS batch fetch ──→ compute_bulk() ──→ GCS Parquet
  FootyStats   ──→ FSS batch fetch ──→     ↑
  Understat    ──→ FSS batch fetch ──→     ↑
  Open-Meteo   ──→ FSS batch fetch ──→     ↑

LIVE MODE (real-time) — existing services, category="sports":
  13 Scrapers ─┐
  Exchanges   ─┤──→ MTDS (category=sports) ──→ Pub/Sub ──→ FSS (mode=live)
  Pinnacle    ─┘    imports USEI adapters       │            compute_for_fixture()
                                                │                    │
  FlashScore/ ──→ MTDS (stats category)  ───────┘                   ↓
  SofaScore                                              Pub/Sub: features
                                                                     │
                                                                     ↓
                                                strategy-service (sports arb strategy type)
                                                                     │
                                                                     ↓
                                                execution-service → USEI adapters (paper/live)

VALIDATION (periodic, in MTDS or reference-data):
  Odds API ──→ compare vs scraper output ──→ alert on drift > ±0.02
```

---

## Scraper Versioning & Website Change Protocol

When a bookmaker changes their website:

1. **Detection**: Scraper health-check fails (CSS selectors return empty / `ScraperError`).
2. **Alert**: Cloud Monitoring alert fires → PagerDuty / Slack.
3. **Diagnosis**: Load latest HTML snapshot from GCS, diff against archived version.
4. **Fix**: Update CSS selectors in the scraper adapter.
5. **Version bump**: Increment `SCRAPER_SCHEMA_VERSION` (e.g., `"bet365-v3"` → `"bet365-v4"`).
6. **Schema update**: If the data structure changed (new fields, removed fields), update `unified_api_contracts/sports/sources/{bookmaker}/schemas.py`.
7. **Test**: Run selector test suite against new HTML snapshot.
8. **Archive**: Save new HTML snapshot to GCS.
9. **Deploy**: `bash scripts/quickmerge.sh "fix: update bet365 scraper for site v4"`.

This leverages the existing API contract versioning — scraper schema versions are parallel to source schemas.
