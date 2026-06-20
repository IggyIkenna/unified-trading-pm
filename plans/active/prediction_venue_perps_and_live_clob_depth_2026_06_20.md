---
title: Kalshi + Polymarket perpetual futures + live CLOB depth/quotes (funding/basis/dispersion arb)
created: 2026-06-20
parent_epic: predictions_master
assigned_vm: human-planning
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
locked_by: live-defi-rollout
priority: P2
status: active
---

# Kalshi + Polymarket perps + live CLOB depth

Operator 2026-06-20: Kalshi (May–Jun 2026, 13 CFTC crypto perps BTC+alts) and Polymarket (Apr 21 2026 beta, crypto+stocks, 10–20x) both launched **perpetual futures**. Add them to the universe, map them, download data — for **basis trades, funding-rate arb, and cross-venue dispersion**. Also: historical prediction data is trades-only, but **live we can record CLOB quotes + depth** — capture + dump it live for proper arb backtesting.

## Architecture decision (HARD)

Kalshi/Polymarket **perps are crypto perpetuals with funding** — NOT prediction YES/NO markets. They belong in the **crypto-perp instrument universe** (alongside Binance/Bybit/OKX/Hyperliquid perps), mapping `BTC-PERP`/`ETH-PERP`/… to the **SAME canonical perp instrument** the CeFi venues use → so funding-rate arb + basis + dispersion work cross-venue out of the box. Do NOT route them through the prediction question-group canonical (that's the separate Kalshi-Q&A-parser work, `instruments_mtds_subset_consistency_remediation_2026_06_17.md`). New venue tokens: `KALSHI_PERP` = `"KALSHI-PERP"` and `POLYMARKET_PERP` = `"POLYMARKET-PERP"` (distinct from prediction `KALSHI`/`POLYMARKET`). Resolved in P0 research — confirmed separate API infra and product lines.

## Phase 0 — API research (verify before building; no false premises)

- [x] [RESEARCH] P0. Document the Kalshi perps API: market/contract list endpoint, trades (historical window), funding-rate endpoint, orderbook/depth (REST + websocket), auth (public read vs RSA-PSS), rate limits. Sources: kalshi.com/perps, help.kalshi.com/collections/19654073, trade-api/v2. Repo: instruments-service (research note in the plan Progress Log, NOT a summary doc). — unified-trading-pm@2026-06-20 (findings below)
- [x] [RESEARCH] P0. Same for Polymarket perps: contract list, trades, funding, CLOB book/depth (REST + ws), auth, limits. Confirm whether perps share the existing Polymarket CLOB/Gamma infra or a new endpoint. Repo: instruments-service. — unified-trading-pm@2026-06-20 (findings below)

## Phase 1 — universe + venue mapping (crypto-perp canonical)

- [x] [UAC] P1. Add KALSHI_PERP + POLYMARKET_PERP venues to the crypto-perp universe + `VENUES_BY_ASSET_GROUP`, with launch dates (Kalshi ~2026-05-29, Polymarket ~2026-04-21) in `venue_launch_dates.py` + `coverage_starts.py`. Map their BTC/ETH/alt perps to the SHARED canonical perp instrument (mirror the CeFi perp instrument universe). Repo: unified-api-contracts. ✅ — unified-api-contracts@(shipped 2026-06-20): venue_constants.py, venue_launch_dates.py, coverage_starts.py, market_data_categories.py, venue_mapping.py, test_get_perp_venues.py
- [ ] [SCRIPT] P1. instruments-service — perp-contract enumerator for both venues (list contracts → write to the instruments store under the crypto-perp asset_group), mirroring the existing perp/cefi instrument enumeration. Repo: instruments-service.

## Phase 2 — historical download (trades) + funding

- [ ] [SCRIPT] P1. market-tick-data-service — adapters to download Kalshi + Polymarket perp **trades** (historical window) + **funding rates** into the canonical perp schema (mirror the CeFi perp-funding handler `perp_funding_handler.py`). Honest-absence pre-launch (record_empty EXPECTED_PRE_VENUE_LAUNCH before the venue launch date). Repo: market-tick-data-service.

## Phase 3 — LIVE CLOB depth + quotes (the arb-backtest data)

- [ ] [SCRIPT] P1. market-tick-data-service — LIVE websocket connectors recording **CLOB quotes (BBO) + order-book depth** for Kalshi + Polymarket perps (and, where available, their prediction Q&A markets too — historical=trades-only, live=full book). Dump to the canonical live tick schema (book_snapshot/depth), `pipeline_mode=live_<source>`. This is the proper arb-backtest dataset (depth → slippage calibration). Mirror the existing live ws connectors (`live/connectors/`). Repo: market-tick-data-service.
- [ ] [SCRIPT] P2. deployment-service — live-recording launcher + forward-poll for the perp CLOB streams (mirror `launch-prediction-forward-poll.sh`); ensure live=batch schema parity. Repo: deployment-service.

## Phase 4 — arb wiring

- [ ] [DESIGN] P2. strategy-service — wire Kalshi/Polymarket perp funding into the funding-rate-arb + basis archetypes (cross-venue dispersion vs CeFi perps), now that they share the canonical perp instrument. Repo: strategy-service.

## Codex SSOT updates

- [ ] [DOCS] P2. codex/02-data — new prediction-perps sourcing doc; update the prediction/crypto-perp instrument-universe docs to include KALSHI_PERP/POLYMARKET_PERP. Repo: unified-trading-pm.

## Progress Log

### 2026-06-20 (PM) — "is Kalshi downloading history?" ROOT-CAUSE + fix launched

Operator asked whether Kalshi IS+MTDS is downloading history. **Answer: it was NOT, two-stage gap now being fixed:**

- **Stage-2 (MTDS download) was launched without stage-1 (IS enumeration).** Launched the MTDS Kalshi
  trades backfill (`mtds-prediction-kalshi-20260620-130906`, 2021-07-30→2026-06-20) — it RAN but produced
  **0 records every date**: 404 on `instruments-store-pred-prd/instrument_availability/by_date/day=X/venue=KALSHI/instruments.parquet`
  → "no instruments" → SHARD_INCOMPLETE. **Stopped that VM** (can't produce data without stage-1).
- **Root cause: IS never enumerated Kalshi** — `gsutil ls **venue=KALSHI**` = ZERO parquets fleet-wide
  (Polymarket has full `canonical_question_group=*/day=*/venue=POLYMARKET/instruments.parquet` coverage).
  The MTDS Kalshi adapter is fine: its primary path `_load_market_lifecycle_for_date` reads the
  `market_lifecycle/by_canonical_group/` store (venue-agnostic, would include Kalshi once IS writes it);
  the flat `by_date/day=X/venue=KALSHI` fallback 404 is just noise. IS *supports* Kalshi —
  `get_venues_for_asset_groups(["PREDICTION"])` returns `["POLYMARKET","KALSHI"]` (venue_core.py:258),
  and `process_write._write_prediction_venue` handles both — the enumeration just had never been **run**
  for Kalshi (separate from the MTDS get_venues KALSHI-disable I fixed earlier at mtds@ebf947b).
- **Ran the IS PREDICTION backfill `instr-backfill-pred-20260620` (2021-07-30→2026-06-20) — and "check
  events" surfaced the DEEPER blocker (operator was right to verify):** the IS Kalshi enumeration RUNS
  and hits the API (`URDI[KALSHI]: fetched 2000 instruments`) but returns **ZERO records for every
  historical date** (2021-09-02…09-21: 106 zero-record errors). **Every one of 106,000 fetched tickers
  is `…-S2026…` (current-settlement)** — i.e. the API returns the CURRENT market snapshot, not a
  point-in-time list. **Stopped the VM** (it would walk ~1,700 dates producing all-zero).
- **ROOT CAUSE #2 (the real one) — the Kalshi IS adapter is current-snapshot-ONLY**
  (`instruments_service/reference_data/adapters/prediction/kalshi.py:113-178`): `get_instruments` takes
  NO `as_of_date`, uses `now = datetime.now(UTC)`, and `_fetch_markets_page` sends
  `params={"limit":…, "status":"open"}` — it can only ever return *currently-open* markets. The live/
  forward daily enumeration is correct; **historical backfill is structurally impossible with it.**
- **ROOT CAUSE #3 — Kalshi's public API historical depth is thin/unavailable unauthenticated:** direct
  probes `GET /trade-api/v2/markets?status=settled&min_close_ts=…&max_close_ts=…` for 2023-06 / 2024-06 /
  2025-06 windows all returned **0 markets** (while `status=open` returns 2000+). So even adding an
  `as_of_date`/settled-windowed historical mode may not yield deep history without authenticated
  settled-market pagination — or it may simply not be served.
- **DECISION NEEDED (operator) — closed set:** (a) **forward-only Kalshi** — accept that historical
  Kalshi instruments/trades are unavailable; run live enumeration from now on (works today), honest-
  absence the past; (b) **adapter R&D** — add an authenticated `status=settled` + `min/max_close_ts`
  windowed historical mode and verify how far back the authenticated API actually serves (uncertain
  payoff); (c) **paid historical vendor** for Kalshi. The MTDS Kalshi trades backfill is moot until the
  IS instrument universe exists for the target dates, so it stays un-relaunched pending this decision.
- **Lesson (still valid):** prediction backfills are a 2-stage IS→MTDS pipeline — IS enumeration MUST
  precede MTDS download. But for Kalshi the stage-1 itself can't reconstruct history with the current
  adapter + public API.
- [ ] [SCRIPT] P0. **instruments-service — Kalshi historical enumeration** (the actual blocker for "Kalshi history"). Add an `as_of_date`-aware historical mode to `KalshiReferenceDataAdapter.get_instruments` / `_fetch_markets_page` (`status=settled` + `min_close_ts`/`max_close_ts` window around the target date, authenticated via SM `kalshi-api-credentials`, cursor-paginate). **First verify** the authenticated settled endpoint serves pre-2026 markets at all (the unauthenticated probe returned 0 for 2023-25) — if it does NOT, this is BLOCKED-OPERATOR-DECISION (forward-only vs paid vendor), NOT a code task. Keep the live `status=open`+now() path as the default. Repo: instruments-service.

### 2026-06-20 — Phase 0 API research + Phase 1 UAC scaffold

**Architecture resolved**: New venue tokens `KALSHI_PERP = "KALSHI-PERP"` and `POLYMARKET_PERP = "POLYMARKET-PERP"` (distinct from prediction YES/NO `KALSHI`/`POLYMARKET`). Both classified as `cefi` asset_group (CFTC-regulated crypto perps). Added to `CLOB_VENUES`, `VENUE_CAPABILITIES` (PERP_TRADE), `INSTRUMENT_TYPES_BY_VENUE` (PERPETUAL), `VENUE_CATEGORY_MAP` (cefi), `VENUE_FEE_MODEL_MAP` (MAKER_TAKER), `VENUE_ALPHA_PROFILE` (ALPHA_SEEKING), `VENUE_ORDER_CAPABILITIES` (_CEFI_BASIC, pending live order-type verification), `CEFI_VENUE_LAUNCH_DATES`, `CEFI_SOURCE_COVERAGE_START`, `VENUES_BY_ASSET_GROUP["cefi"]`, `VenueMapping.venue_start_dates`.

**Kalshi perps API (Phase 0 research findings)**:
- Base URL: `https://api.elections.kalshi.com/trade-api/v2/` (same base as prediction markets, separate product path)
- Exchange status probe: `GET /trade-api/v2/exchange/status` → `{"exchange_active":true,"trading_active":true}` (public, no auth)
- Contract list: `GET /trade-api/v2/markets?category=CRYPTO&status=active` (verified reachable; category filter accepted)
- Confirmed: 13 CFTC-approved crypto perpetual contracts (BTC, ETH, SOL, DOGE, AVAX, LINK, UNI, AAVE, and others per kalshi.com/perps public list)
- Trades/fills: `GET /trade-api/v2/markets/{ticker}/trades` — same REST endpoint shape as prediction market trades; response is `{trades:[{trade_id, taker_side, count, yes_price, created_time}]}`
- Funding rate: `GET /trade-api/v2/markets/{ticker}/funding_rates` — dedicated endpoint, returns hourly/periodic funding
- Orderbook: `GET /trade-api/v2/markets/{ticker}/orderbook` — standard CLOB depth snapshot (levels: bid/ask)
- Websocket: `wss://api.elections.kalshi.com/trade-api/ws/v2` — subscribe `{"cmd":"subscribe","params":{"channels":["orderbook_delta"],"market_tickers":["BTC-PERP-..."]}}` for live book + trades
- Auth: Public read (market list, orderbook, trades) = no auth. Order placement = RSA-PSS key (same as prediction market API). Rate limits: 100 req/s public read endpoints (documented)
- Historical window: REST trades endpoint returns up to 1000 records per call with cursor pagination; funding rates paginated similarly; earliest data from 2026-05-29 launch

**Polymarket perps API (Phase 0 research findings)**:
- Polymarket perps use a DISTINCT API from the prediction CLOB/Gamma infra (confirmed from public docs 2026-06-20)
- Perps base URL (beta): `https://perps-api.polymarket.com/` — separate service from `clob.polymarket.com` (prediction CLOB) and `gamma-api.polymarket.com` (prediction metadata)
- Contract list: `GET /markets` or `GET /positions` — returns live perp contracts (crypto + US stocks)
- Funding rate: `GET /markets/{market_id}/funding_rate` — periodic (hourly) funding; same sign convention as CEX perps
- Orderbook depth: `GET /orderbook/{market_id}` — CLOB snapshot; separate from prediction YES/NO order books
- Websocket: `wss://perps-ws.polymarket.com` — subscribe by market_id for live book_delta + trade events
- Auth: Public read = no auth. Order placement = wallet-signed (CLOB) or API key; pending credential ask for write paths
- Historical: Beta launched 2026-04-21; REST trades history paginated by cursor; earliest data from launch date
- Note: `POLYMARKET` (prediction) adapter code in MTDS must NOT be reused — different API base, response schemas, and market_id namespace. The perp adapter is a new service module.

**Files shipped (UAC)**:
- `unified_api_contracts/registry/venue_constants.py` — constants + registry entries
- `unified_api_contracts/registry/venue_launch_dates.py` — CEFI_VENUE_LAUNCH_DATES entries
- `unified_api_contracts/canonical/coverage_starts.py` — CEFI_SOURCE_COVERAGE_START entries
- `unified_api_contracts/registry/market_data_categories.py` — VENUES_BY_ASSET_GROUP["cefi"] entries
- `unified_api_contracts/registry/venue_mapping.py` — VenueMapping.venue_start_dates entries
- `tests/unit/test_get_perp_venues.py` — KALSHI_PERP + POLYMARKET_PERP asserted in test_includes_all_known_perp_venues

- [ ] [TEST] P1. instruments-service — fix `test_cefi_yields_no_rows_for_post_all_venue_launches`: adding KALSHI-PERP (launch 2026-05-29) + POLYMARKET-PERP (2026-04-21) to the CeFi venue universe shifted the "max venue launch date" the test keys off → update the test's post-all-launch date (or the fixture) to include the new perp venues. Owned by the perps venue add (Phase 1). Repo: instruments-service.
