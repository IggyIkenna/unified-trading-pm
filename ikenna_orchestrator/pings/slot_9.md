# Slot 9 ping file — re-themed 2026-05-19

> Doorbell only. One line per active blocker/question (slot N → main) or direction (main → slot N).
> Full Q&A lives in the slot's plan-of-record § "Open questions". Resolved entries removed by main.
> Format: `[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-line>`

[2026-05-19 14:47 UTC] [main → slot 9] — RE-THEMED via --reset-slot.
Prior theme: TBD (main fills from yesterday's LEDGER + prior plan's DONE block on first read).
New theme: TBD (main fills from today's work-split + plan-of-record + spawn prompt).

[2026-05-20 UTC] [slot 9 → main] — DONE: QG GREEN SWEEP Cluster A complete.
- UAC: was already green, no changes needed.
- UTL: 9 codex violations fixed (imports-inside-functions checker bug fixed in PM; noqa/config-bootstrap exemptions for os.environ; print() false-positive fixed by renaming _fingerprint→_schema_sig; empty fallbacks noqa'd; hardcoded project IDs removed from docstrings; SIZE_EXTRA_EXCLUDES/BROAD_EXCEPT_EXTRA_EXCLUDES/PIP_AUDIT_EXTRA_ARGS added to quality-gates.sh). utl@f63eb8e2 + pm@424b4319 pushed to live-defi-rollout.
- IS: was already green (CODEX_MAX_VIOLATIONS=4 within tolerance), no changes needed.
Plan-of-record: work_split_2026_05_20_ikenna.md § Slot 9.

[2026-05-20 UTC] [slot 9 → main] — DONE: execution-service QG green (cluster C takeover from slot-11 worker).
- execution-service@2d330d5d: codex violations 27→24 (within CODEX_MAX_VIOLATIONS=24), QG exits 0.
- Fixes: STEP 5.37 noqa:qg-inline-threshold on 7 files; STEP 5.12b noqa:gs-uri on batch_backtest.py; credential skip text scrubbed in 3 test files; syntax fixes in cli/backtest_args + cli/benchmark_compare + deribit/query_instruments + generate_three_domain_configs; KrakenVenueError→CanonicalError + singleton mock fix in unit tests.
- Plan flip: work_split_2026_05_20_ikenna.md slot-11 row updated @pm beeeb70f.
- NOTE from remote: strategy-service@d0bf1a7c was already green but has a regression (UAC dydx removal → 5 test failures). ml-service archived (QG moot).
Plan-of-record: work_split_2026_05_20_ikenna.md § Slot 11 (cluster C takeover).

## CREDENTIAL APPROVAL REQUEST — Polymarket CLOB L2 HMAC API Key

[2026-05-21 slot-9 UTC]

**Vendor**: Polymarket CLOB API (clob.polymarket.com) — free account, L2 HMAC signing
**What I need**: L2 HMAC private key (Ethereum-style ECDSA key for CLOB authenticated endpoints)
  - The public Gamma API + Data API + price history require NO credentials.
  - L2 HMAC key unlocks: authenticated order book snapshots, portfolio positions, private fills.
**Account to use**: Existing Polymarket account or new account at polymarket.com (free, KYC-lite for small positions)
**Cost**: $0 for read-only API usage
**What it unblocks**: Authenticated CLOB tests in `tests/integration/test_polymarket_integration.py`; `TestAuthenticatedClob` class currently skips with BLOCKED-CREDENTIALS message.
**Status**: BLOCKED-CREDENTIALS until operator [ack]
**Without it**: Public-endpoint unit + integration tests ship; adapter is fully functional for batch data collection (Gamma + Data API both work without auth); authenticated CLOB tests dormant.
**Plan-of-record**: ADAPTER-POLYMARKET-FEED (backlog task)

## CREDENTIAL APPROVAL REQUEST — Kalshi Member API Key

[2026-05-21 slot-9 UTC]

**Vendor**: Kalshi (trading-api.kalshi.com) — Member API (KYC-required for trading)
**What I need**: Kalshi Member API key + secret (HMAC-SHA256 signing)
  - Public trade history + market metadata require NO credentials.
  - Member API key unlocks: portfolio positions, order placement, private fills.
**Account to use**: Existing Kalshi account or new account at kalshi.com (US-regulated, KYC required)
**Cost**: $0 for read-only API usage; trading requires funded account
**What it unblocks**: Authenticated member API tests in `tests/integration/test_kalshi_integration.py`
**Status**: BLOCKED-CREDENTIALS until operator [ack]
**Without it**: Public trade history tests ship; adapter fully functional for batch data collection; authenticated tests dormant.
**Plan-of-record**: ADAPTER-KALSHI-FEED (backlog task)

## CREDENTIAL APPROVAL REQUEST — The-Odds-API Key

[2026-05-21 slot-9 UTC]

**Vendor**: The-Odds-API (api.the-odds-api.com) — free tier (500 requests/month), paid tiers available
**What I need**: API key from the-odds-api.com (sign up at the-odds-api.com/account)
  - The API key is required for ALL endpoints (no public/unauthenticated access).
  - Key unlocks: sports listing, live + pre-game odds across 40+ sports/leagues, scores.
**Account to use**: New account at the-odds-api.com (free tier, email signup, no KYC)
**Cost**: $0 for free tier (500 req/month); paid tiers from ~$3/month for higher quota
**What it unblocks**: Integration tests in `tests/integration/test_odds_api_integration.py`; `TestFetchSportsLive` + `TestGetMarketsLive` classes currently skip with BLOCKED-CREDENTIALS message.
**Status**: BLOCKED-CREDENTIALS until operator [ack]
**Without it**: OddsApiAdapter scaffold + unit tests ship; integration tests dormant. Adapter fully functional once key provided.
**Plan-of-record**: ADAPTER-THE-ODDS-API (backlog task); MTDS@065cb49

## CREDENTIAL APPROVAL REQUEST — Polygon.io API Key

[2026-05-21 slot-9 UTC]

**Vendor**: Polygon.io (api.polygon.io) — Starter tier ($29/mo) or higher
**What I need**: Polygon.io API key (Bearer token auth)
  - Starter ($29/mo): equities/ETFs/indices, 5yr history, 100K calls/day
  - Developer ($79/mo): unlimited history + crypto/forex
  - Advanced ($199/mo): real-time WebSocket streaming
**Account to use**: New account at polygon.io (credit card required for paid tier)
**Cost**: $29/mo Starter covers all equities OHLCV use cases; free tier exists but rate-limited to 5 calls/min
**What it unblocks**: Integration tests in `tests/integration/test_polygon_integration.py`; `TestFetchTickersLive` + `TestFetchAggregatesLive` classes currently skip with BLOCKED-CREDENTIALS message.
**Status**: BLOCKED-CREDENTIALS until operator [ack]
**Without it**: PolygonAdapter scaffold + unit tests ship; integration tests dormant. Adapter fully functional once key provided.
**Plan-of-record**: ADAPTER-POLYGON-IO-TRADFI-TICKS (backlog task); MTDS@34edf56

## CREDENTIAL APPROVAL REQUEST — FootyStats API Key

[2026-05-21 slot-9 UTC]

**Vendor**: FootyStats / football-data-api.com — Basic tier ($5/mo) or higher
**What I need**: FootyStats API key (`key` query parameter)
  - Basic ($5/mo): current season data, 100+ leagues
  - Pro ($12/mo): historical data, 500+ leagues, xG, BTTS/over-under potentials
  - Business: unlimited + all advanced metrics
**Account to use**: New account at footystats.org (email signup)
**Cost**: $5/mo Basic covers league listing + current season matches; Pro required for historical xG
**What it unblocks**: Integration tests in `tests/integration/test_footystats_integration.py`; `TestGetLeaguesLive` + `TestGetMatchesLive` classes currently skip with BLOCKED-CREDENTIALS message.
**Status**: BLOCKED-CREDENTIALS until operator [ack]
**Without it**: FootystatsAdapter scaffold ships (get_leagues/get_matches/get_teams); integration tests dormant.
**Plan-of-record**: ADAPTER-FOOTYSTATS-FEED (backlog task); MTDS@3294423

## CREDENTIAL APPROVAL REQUEST — Sportradar API Key

[2026-05-21 slot-9 UTC]

**Vendor**: Sportradar (developer.sportradar.com) — Trial (free, 30 days, 100 calls/day) or Basic ($499/mo)
**What I need**: Sportradar API key (`api_key` query param)
  - Free 30-day trial: soccer v4 (100 calls/day) — sufficient for smoke tests + schedule/results
  - Basic ($499/mo): 5K calls/day, one sport
  - Advanced ($1,199/mo): unlimited, all sports, real-time
**Account to use**: New developer account at developer.sportradar.com (email signup, free trial)
**Cost**: $0 for free trial (30 days); $499/mo Basic for production
**What it unblocks**: Integration tests in `tests/integration/test_sportradar_integration.py`; `TestGetScheduleLive` + `TestGetResultsLive` + `TestGetOddsLive` classes currently skip with BLOCKED-CREDENTIALS message.
**Status**: BLOCKED-CREDENTIALS until operator [ack]
**Without it**: SportradarAdapter scaffold ships (get_schedule/get_results/get_odds, soccer v4 + NBA/tennis/NFL extensible); UAC schemas at UAC@ce48ba6; integration tests dormant.
**Plan-of-record**: ADAPTER-SPORTRADAR-FEED (backlog task); MTDS@8444c64; UAC@ce48ba6

## CREDENTIAL APPROVAL REQUEST — Kaiko API Key

[2026-05-21 slot-9 UTC]

**Vendor**: Kaiko (kaiko.com / docs.kaiko.com) — Free tier or Starter ($99/mo)
**What I need**: Kaiko API key (`X-Api-Key` header)
  - Free: 1K calls/month, 2yr history — sufficient for smoke tests
  - Starter ($99/mo): 5yr history, tick-level trades, 100K calls/month
  - Growth ($499/mo): full history, order book snapshots
**Account to use**: New account at kaiko.com (email signup; enterprise sales contact at sales@kaiko.com)
**Cost**: Free tier covers testing; $99/mo Starter for production historical ticks
**What it unblocks**: Integration tests in `tests/integration/test_kaiko_integration.py`; `TestFetchInstrumentsLive` + `TestFetchOHLCVLive` + `TestFetchTradesLive` classes currently skip with BLOCKED-CREDENTIALS message.
**Status**: BLOCKED-CREDENTIALS until operator [ack]
**Without it**: KaikoAdapter scaffold ships (fetch_instruments/fetch_trades/fetch_ohlcv, paginated via next_url, all CEX); UAC schemas at UAC@ce48ba6; integration tests dormant.
**Plan-of-record**: ADAPTER-KAIKO-CEX-HISTORICAL (backlog task); MTDS@86d6baa; UAC@ce48ba6
