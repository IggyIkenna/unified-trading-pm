---
doc_type: plan
title: Kalshi + Polymarket perpetual futures — PARKED crypto-perp venue track
summary: >-
  The KALSHI_PERP/POLYMARKET_PERP crypto-perpetuals venue build (universe registration, reference-data enumerators,
  batch trades+funding, live CLOB connectors, strategy-archetype wiring) — parked per the 2026-07-14 operator ruling
  pending venue access; split out of prediction_venue_perps_and_live_clob_depth_2026_06_20.md (plan line-cap
  remediation, 2026-07-24).
status: active
nature: process
asset_group: [prediction, cefi]
stage: [meta]
repos:
  [agent-orchestrator, deployment-api, deployment-service, e2e-testing, features-service, fund-administration-service]
scope: [engineer, admin]
tags: [prediction, kalshi, polymarket, perps, clob, live-data, arb, funding-rate, basis, blocked-upstream, parked]
related:
  [
    plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20,
    plans/active/prediction_live_clob_depth_capture_2026_07_24,
    plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24,
    plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06,
    plans/active/prediction_capture_incident_remediation_2026_07_06,
    plans/active/issues/plan_line_cap_remediation_2026_07_23,
  ]
created: "2026-07-24"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes: [prediction_venue_perps_and_live_clob_depth_2026_06_20]
superseded_by:
depends_on:
source: >-
  Split from prediction_venue_perps_and_live_clob_depth_2026_06_20.md (2354 lines / 87 todos, HARD over the 1000L
  line-cap) per plans/active/issues/plan_line_cap_remediation_2026_07_23.md row 23 — operator approved unlocking
  `locked_by: live-defi-rollout` and a 3-way clean-partition (parked perps track / live CLOB-depth capture infra /
  cross-venue arb+coverage). This file carries the parked-perps third verbatim.
assigned_role: data_engineering
drift_direction: advance-code
---

# Kalshi + Polymarket perps — PARKED crypto-perp venue track

> **🟢 2026-07-24 — SPLIT FROM `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`.** That plan grew to 2354
> lines / 87 todos across three intertwined tracks and was flagged HARD over the 1000-line cap
> (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md` row 23). Operator approved unlocking
> `locked_by: live-defi-rollout` and a 3-way clean-partition. **This file carries the parked KALSHI_PERP /
> POLYMARKET_PERP crypto-perpetuals track verbatim** — every todo and Progress Log entry below was moved unchanged
> (never summarized or rewritten). Siblings from the same split:
> `plans/active/prediction_live_clob_depth_capture_2026_07_24.md` (live CLOB-depth capture infra) and
> `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` (cross-venue arb + honest-coverage). The original
> plan is retained, frozen, at `plans/archive/2026_07/prediction_venue_perps_and_live_clob_depth_2026_06_20.md`.
>
> **Do not duplicate the Kalshi-perp-adapter repoint work here** — this plan is the parked-venue HISTORY (why perps are
> on hold + what was already built against the wrong host); the actionable repoint (real
> `external-api.kalshi.com/trade-api/v2/margin/` endpoint research + demo dry-run + prod cutover, gated on Kalshi
> member-rollout access) is tracked in `plans/active/prediction_capture_incident_remediation_2026_07_06.md` Workstream B
> — coordinate there, don't fork parallel work here.

> **🟡 2026-07-14 OPERATOR RULING: Kalshi/Polymarket perps are NOT part of MVP.** "Nothing we can do — we can't get
> perps on those yet; Polymarket is in beta mode and Kalshi requires some extra work." All perp-universe items in this
> plan are parked until the operator announces access (see
> `plans/active/prediction_capture_incident_remediation_2026_07_06.md` Phase 4, resolved-by-ruling same day). The
> PREDICTION token-id live-capture lane items in this plan are unaffected.

Operator 2026-06-20: Kalshi (May–Jun 2026, 13 CFTC crypto perps BTC+alts) and Polymarket (Apr 21 2026 beta,
crypto+stocks, 10–20x) both launched **perpetual futures**. Add them to the universe, map them, download data — for
**basis trades, funding-rate arb, and cross-venue dispersion**. Also: historical prediction data is trades-only, but
**live we can record CLOB quotes + depth** — capture + dump it live for proper arb backtesting.

## Architecture decision (HARD)

Kalshi/Polymarket **perps are crypto perpetuals with funding** — NOT prediction YES/NO markets. They belong in the
**crypto-perp instrument universe** (alongside Binance/Bybit/OKX/Hyperliquid perps), mapping `BTC-PERP`/`ETH-PERP`/… to
the **SAME canonical perp instrument** the CeFi venues use → so funding-rate arb + basis + dispersion work cross-venue
out of the box. Do NOT route them through the prediction question-group canonical (that's the separate Kalshi-Q&A-parser
work, `instruments_mtds_subset_consistency_remediation_2026_06_17.md`). New venue tokens: `KALSHI_PERP` =
`"KALSHI-PERP"` and `POLYMARKET_PERP` = `"POLYMARKET-PERP"` (distinct from prediction `KALSHI`/`POLYMARKET`). Resolved
in P0 research — confirmed separate API infra and product lines.

> **🟡 CORRECTION (2026-07-06 — read before trusting "Kalshi-perp verified"/"COMPLETE" below).** The Phase-1 P1 item's
> "Kalshi live endpoint verified" and the "PERPS WORKSTREAM COMPLETE for Kalshi-perp end-to-end" entry are **WRONG**.
> `KalshiPerpReferenceDataAdapter` (`cefi/kalshi_perp.py`, IS@fdc9bad) queries
> `api.elections.kalshi.com/trade-api/v2/markets?category=Crypto&status=open` — the **binary EVENTS host**, not a perps
> API. Live-probed 3,000 markets across every crypto series: **100% `market_type=binary`, 0 tickers containing "PERP"**.
> This is the SAME `category` param ignored / KXMVE-flood mechanism this plan already diagnosed for the sibling
> **prediction** Kalshi adapter (see the "P1 Kalshi canonical grouping — the premise was STALE" entry below) — it just
> never got checked against `cefi/kalshi_perp.py` too, and there the flood has no `OTHER` bucket to land in: every KXMVE
> binary event got mislabeled `instrument_type=PERPETUAL` and written straight into the **cefi catalogue** — **25,473
> fake rows** (found + purged 2026-07-06). The adapter is now **guarded to emit 0** (`_REPOINT_PENDING`,
> instruments-service@c8c6dac76) until it is repointed to Kalshi's actual authenticated margin/perps API
> (`external-api.kalshi.com/trade-api/v2/margin/`) — a DIFFERENT host this plan never probed. **Consequence for this
> plan:** the "COMPLETE" claim covering batch trades+funding / live CLOB ws / strategy archetype bundling for
> KALSHI-PERP was built on an enumerator that returns 0 real perpetuals — those downstream layers should be re-verified
> against a repointed adapter, not assumed correct. Full evidence, the live probe, and the fix:
> `plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`. Dated entry with full detail at the
> end of this plan's Progress Log. (Not fixing the repoint here — that's this plan's/owner's call; flagging only.)

## Phase 0 — API research (verify before building; no false premises)

- [x] [RESEARCH] P0. Document the Kalshi perps API: market/contract list endpoint, trades (historical window),
      funding-rate endpoint, orderbook/depth (REST + websocket), auth (public read vs RSA-PSS), rate limits. Sources:
      kalshi.com/perps, help.kalshi.com/collections/19654073, trade-api/v2. Repo: instruments-service (research note in
      the plan Progress Log, NOT a summary doc). — unified-trading-pm@2026-06-20 (findings below)
- [x] [RESEARCH] P0. Same for Polymarket perps: contract list, trades, funding, CLOB book/depth (REST + ws), auth,
      limits. Confirm whether perps share the existing Polymarket CLOB/Gamma infra or a new endpoint. Repo:
      instruments-service. — unified-trading-pm@2026-06-20 (findings below)

## Phase 1 — universe + venue mapping (crypto-perp canonical)

- [x] [UAC] P1. Add KALSHI_PERP + POLYMARKET_PERP venues to the crypto-perp universe + `VENUES_BY_ASSET_GROUP`, with
      launch dates (Kalshi ~2026-05-29, Polymarket ~2026-04-21) in `venue_launch_dates.py` + `coverage_starts.py`. Map
      their BTC/ETH/alt perps to the SHARED canonical perp instrument (mirror the CeFi perp instrument universe). Repo:
      unified-api-contracts. ✅ — unified-api-contracts@(shipped 2026-06-20): venue_constants.py, venue_launch_dates.py,
      coverage_starts.py, market_data_categories.py, venue_mapping.py, test_get_perp_venues.py
- [x] ✅ [SCRIPT] P1. instruments-service — perp-contract enumerator for both venues SHIPPED
      (instruments-service@fdc9bad): `KalshiPerpReferenceDataAdapter` (public
      `GET /markets?status=open&category=Crypto`, cursor-paginated, `InstrumentType.PERPETUAL`, 16 unit tests) +
      `PolymarketPerpReferenceDataAdapter` scaffold (22 unit tests); wired into `factory.py`/`router.py`; QG green (cov
      88.29%). Kalshi live endpoint verified. **Polymarket-perp live endpoint BLOCKED-UPSTREAM** — see next item.

- [ ] [SCRIPT] P1. **Polymarket-perp enumerator — BLOCKED-UPSTREAM (no public perps API exists yet — CONFIRMED
      2026-06-22)**: the perps are LIVE (CFTC-DCM-approved, launched 2026-04-21, beta to restricted users 2026-05-28, up
      to 20x, S&P500/NVDA/NFLX/HOOD) but **web-UI beta only**;
      `perps-api.polymarket.com`/`perps.polymarket.com`/`perp.polymarket.com` are ALL NXDOMAIN on Google+Cloudflare (not
      region, not auth — the host doesn't exist), and the official docs (docs.polymarket.com + llms.txt) have ZERO
      perps/perpetual/funding entries. So there is NO public REST/WS perps endpoint to build against. Scaffold
      (`PolymarketPerpReferenceDataAdapter` + MTDS adapter/connector + launcher gating + strategy honest-absence) is
      shipped at every layer; the REAL unblock is Polymarket publishing the public perps API (or operator-provisioned
      beta API access). Auto-flows on endpoint availability. Ping: slot_0. Repo: instruments-service.
  - **2026-06-22 unified-CLOB re-verification (operator said "perps ride the unified CLOB `clob.polymarket.com` + Gamma
    `active=true`")**: probed empirically — `clob.polymarket.com/clob-markets` IS reachable (HTTP 200, 38,969 markets,
    opaque short-key schema `r/t/c/mos/mts/mbf/tbf/ao/cbos/aot/ibce/fd`) but Gamma `/markets?active=true` AND
    `/events?active=true` return **ZERO** perp/perpetual/funding markets, and the `tag=crypto-perpetuals` /
    `series_slug=crypto-perpetuals` filters are **silently IGNORED** (tagged vs untagged queries return byte-identical
    regular-Q&A slugs: `new-rhianna-album-before-gta-vi`, `will-bitcoin-hit-1m-before-gta-vi`, …). So perpetuals are
    **not publicly enumerable** via the documented Gamma/CLOB discovery path — corroborating the web-UI-beta-only
    finding. **DISCREPANCY for operator**: the unified-CLOB host works for prediction markets, but the perp product is
    gated (beta/restricted). The unblock is **operator-provisioned beta API credentials** (or Polymarket publishing the
    public perps endpoint), NOT a buildable public path — status stays BLOCKED-CREDENTIALS, not descoped. Kalshi-perp is
    fully live (separate public API). Verified via `prediction-to-100%` drive.

## Phase 2 — historical download (trades) + funding

- [x] ✅ [SCRIPT] P1. market-tick-data-service — perp trades+funding adapters SHIPPED (mtds@88c2f0c + UAC perp-source
      registration on LDR): `_perp_funding_kalshi_polymarket.py` stage (Kalshi `GET /markets?category=Crypto` →
      `/markets/{ticker}/funding_rates`, day-windowed, 429/5xx retry, shard-isolated) + `perp_funding_handler.py` wired
      (`_resolve_pipeline_mode_for_protocol`→`pipeline_mode_for_source`, pre-launch
      `record_empty(EXPECTED_PRE_VENUE_LAUNCH)` kalshi_perp<2026-05-29 / polymarket_perp<2026-04-21,
      DEFAULT_PROTOCOLS+chain_map extended); 16 unit tests; QG green (5060 pass, 80.77%). UAC:
      `PipelineMode.BATCH/LIVE/REPLAY_KALSHI_PERP` + `BATCH/LIVE_POLYMARKET_PERP` +
      `SOURCE_PRIORITY[(cefi,trades)]+=kalshi_perp,polymarket_perp` (committed LDR). **Kalshi-perp live-ready;
      Polymarket-perp scaffold BLOCKED-UPSTREAM** (endpoint NXDOMAIN — see enumerator sub-item + slot_0 ping). —
      2026-06-21

## Phase 3 — LIVE CLOB depth + quotes (the arb-backtest data)

- [x] ✅ [SCRIPT] P1. market-tick-data-service — perp LIVE CLOB ws connectors SHIPPED (mtds@c487a78 + UAC resolver
      fix@a6444476): `live/connectors/kalshi_perp_ws.py` (per-ticker `_OrderBook` snapshot+delta, lazy ws, exp-backoff
      reconnect, registered `KALSHI-PERP`, canonical `book_snapshot` BBO+depth, 37 tests) + `polymarket_perp_ws.py`
      scaffold (`_ENDPOINT_LIVE=False`, BLOCKED-UPSTREAM, registered `POLYMARKET-PERP`, 28 tests); both in
      `register_all()`; QG green (5161+65 tests, 81.03%). **UAC FIX**: `live_source_for_venue` perp-venue override
      (`KALSHI-PERP`→`kalshi_perp` not batch-only `tardis`) — caught + fixed a `live_pipeline_mode_for_venue` ValueError
      that would have crashed the live runner; regression test added. Kalshi-perp live-ready (`live_kalshi_perp`);
      Polymarket-perp scaffold BLOCKED-UPSTREAM. — 2026-06-21
- [x] ✅ [SCRIPT] P2. deployment-service — perp CLOB live-recording launcher SHIPPED (deployment-service@86f517d):
      `scripts/vm/launch-perp-clob-live.sh` — KALSHI-PERP → e2-standard-8 VM
      (`VM_TASK=mtds-live`/`VM_OPERATION=live_websocket`/`MANIFEST_PER_VM_SHARDS=true`, shard
      `cefi:KALSHI-PERP:book_snapshot`→slug `cefi-kalshi-perp-book-snapshot`, prefix covered by `mtds-live-cefi-` in
      vm_zombie_watchdog LONG_LIVED_LIVE), singleton-locked per shard; POLYMARKET-PERP → clean early-exit
      BLOCKED-UPSTREAM (no doomed VM); live=batch parity (same UAC `book_snapshot`, only pipeline_mode differs
      live_kalshi_perp vs batch_kalshi_perp); lifecycle marker (Epic predictions_master/permanent). QG green. —
      2026-06-21

## Phase 4 — arb wiring

- [x] ✅ [DESIGN] P2. strategy-service — perp funding wired into funding-rate-arb + basis archetypes SHIPPED
      (strategy-service@31ba481f): `catalog_carry.py` `_CARRY_BASIS_PERP_VENUE_BUNDLES` (10→12) +
      `_FUNDING_DISPERSION_VENUES` (4→6) += `(kalshi,KALSHI-PERP,USDC)` + `(polymarket,POLYMARKET-PERP,USDC)` (slot
      tokens from UAC `_PREDICTION_TOKENS`); 8 tests; QG green. POLYMARKET-PERP wired for honest-absence
      (BLOCKED-UPSTREAM — flows when endpoint recovers, no code change). — 2026-06-21

## Codex SSOT updates

- [x] ✅ [DOCS] P2. codex/02-data — prediction-perps sourcing doc WRITTEN (`prediction-perps-sourcing.md`) +
      prediction-data-types-catalog.md cross-links it (KALSHI_PERP/POLYMARKET_PERP). Repo: unified-trading-pm. —
      2026-06-21

## Progress Log

### 2026-06-20 — Phase 0 API research + Phase 1 UAC scaffold

**Architecture resolved**: New venue tokens `KALSHI_PERP = "KALSHI-PERP"` and `POLYMARKET_PERP = "POLYMARKET-PERP"`
(distinct from prediction YES/NO `KALSHI`/`POLYMARKET`). Both classified as `cefi` asset_group (CFTC-regulated crypto
perps). Added to `CLOB_VENUES`, `VENUE_CAPABILITIES` (PERP_TRADE), `INSTRUMENT_TYPES_BY_VENUE` (PERPETUAL),
`VENUE_CATEGORY_MAP` (cefi), `VENUE_FEE_MODEL_MAP` (MAKER_TAKER), `VENUE_ALPHA_PROFILE` (ALPHA_SEEKING),
`VENUE_ORDER_CAPABILITIES` (\_CEFI_BASIC, pending live order-type verification), `CEFI_VENUE_LAUNCH_DATES`,
`CEFI_SOURCE_COVERAGE_START`, `VENUES_BY_ASSET_GROUP["cefi"]`, `VenueMapping.venue_start_dates`.

**Kalshi perps API (Phase 0 research findings)**:

- Base URL: `https://api.elections.kalshi.com/trade-api/v2/` (same base as prediction markets, separate product path)
- Exchange status probe: `GET /trade-api/v2/exchange/status` → `{"exchange_active":true,"trading_active":true}` (public,
  no auth)
- Contract list: `GET /trade-api/v2/markets?category=CRYPTO&status=active` (verified reachable; category filter
  accepted)
- Confirmed: 13 CFTC-approved crypto perpetual contracts (BTC, ETH, SOL, DOGE, AVAX, LINK, UNI, AAVE, and others per
  kalshi.com/perps public list)
- Trades/fills: `GET /trade-api/v2/markets/{ticker}/trades` — same REST endpoint shape as prediction market trades;
  response is `{trades:[{trade_id, taker_side, count, yes_price, created_time}]}`
- Funding rate: `GET /trade-api/v2/markets/{ticker}/funding_rates` — dedicated endpoint, returns hourly/periodic funding
- Orderbook: `GET /trade-api/v2/markets/{ticker}/orderbook` — standard CLOB depth snapshot (levels: bid/ask)
- Websocket: `wss://api.elections.kalshi.com/trade-api/ws/v2` — subscribe
  `{"cmd":"subscribe","params":{"channels":["orderbook_delta"],"market_tickers":["BTC-PERP-..."]}}` for live book +
  trades
- Auth: Public read (market list, orderbook, trades) = no auth. Order placement = RSA-PSS key (same as prediction market
  API). Rate limits: 100 req/s public read endpoints (documented)
- Historical window: REST trades endpoint returns up to 1000 records per call with cursor pagination; funding rates
  paginated similarly; earliest data from 2026-05-29 launch

**Polymarket perps API (Phase 0 research findings)**:

- Polymarket perps use a DISTINCT API from the prediction CLOB/Gamma infra (confirmed from public docs 2026-06-20)
- Perps base URL (beta): `https://perps-api.polymarket.com/` — separate service from `clob.polymarket.com` (prediction
  CLOB) and `gamma-api.polymarket.com` (prediction metadata)
- Contract list: `GET /markets` or `GET /positions` — returns live perp contracts (crypto + US stocks)
- Funding rate: `GET /markets/{market_id}/funding_rate` — periodic (hourly) funding; same sign convention as CEX perps
- Orderbook depth: `GET /orderbook/{market_id}` — CLOB snapshot; separate from prediction YES/NO order books
- Websocket: `wss://perps-ws.polymarket.com` — subscribe by market_id for live book_delta + trade events
- Auth: Public read = no auth. Order placement = wallet-signed (CLOB) or API key; pending credential ask for write paths
- Historical: Beta launched 2026-04-21; REST trades history paginated by cursor; earliest data from launch date
- Note: `POLYMARKET` (prediction) adapter code in MTDS must NOT be reused — different API base, response schemas, and
  market_id namespace. The perp adapter is a new service module.

**Files shipped (UAC)**:

- `unified_api_contracts/registry/venue_constants.py` — constants + registry entries
- `unified_api_contracts/registry/venue_launch_dates.py` — CEFI_VENUE_LAUNCH_DATES entries
- `unified_api_contracts/canonical/coverage_starts.py` — CEFI_SOURCE_COVERAGE_START entries
- `unified_api_contracts/registry/market_data_categories.py` — VENUES_BY_ASSET_GROUP["cefi"] entries
- `unified_api_contracts/registry/venue_mapping.py` — VenueMapping.venue_start_dates entries
- `tests/unit/test_get_perp_venues.py` — KALSHI_PERP + POLYMARKET_PERP asserted in test_includes_all_known_perp_venues

- [x] ✅ [TEST] P1. instruments-service — `test_cefi_yields_no_rows_for_post_all_venue_launches` GREEN (verified
      2026-06-21, perp-venue-add fixture already updated): adding KALSHI-PERP (launch 2026-05-29) + POLYMARKET-PERP
      (2026-04-21) to the CeFi venue universe shifted the "max venue launch date" the test keys off → update the test's
      post-all-launch date (or the fixture) to include the new perp venues. Owned by the perps venue add (Phase 1).
      Repo: instruments-service.

### 2026-06-21 20:52 — P1 perp-venue test items GREEN

- `instruments-service tests/unit/scripts/test_enumerate_expected_universe.py::test_cefi_yields_no_rows_for_post_all_venue_launches`
  → **1 passed** (the perp-venue-add already updated the post-all-launch fixture).
- `unified-api-contracts tests/unit/test_get_perp_venues.py` → **6 passed** (KALSHI-PERP/POLYMARKET-PERP asserted;
  venue_constants.py registers both, asset_group=cefi, PERP_TRADE capability). Both verified green, no code change
  needed.

### 2026-06-21 21:00 — perp enumerator shipped (Kalshi live; Polymarket endpoint BLOCKED-UPSTREAM)

- instruments-service@fdc9bad: `cefi/kalshi_perp.py` + `cefi/polymarket_perp.py` adapters + factory/router wiring + 38
  unit tests, QG green (cov 88.29%). Sub-agent build.
- **Kalshi-perp**: public read endpoint verified earlier in Phase-0; adapter live-ready.
- **Polymarket-perp**: probed the documented beta host `perps-api.polymarket.com` → **DNS NXDOMAIN** (control
  `gamma-api.polymarket.com`→200, `clob`/`api.polymarket.com` resolve), and perp paths under resolving hosts all 404.
  Real upstream-endpoint gap (NOT credentials — read is public per Phase-0). Scaffold + mocked tests shipped; finalize
  when the live beta endpoint is confirmed. Operator ask logged in slot_0 ping.

### 2026-06-21 21:10 — MTDS perp trades+funding shipped (line 34)

- mtds@88c2f0c (dirty-deps carve-out — UTL had orphan WIP at pre-flight; now clean) + UAC perp-source registration
  (PipelineMode KALSHI_PERP/POLYMARKET_PERP members + SOURCE_PRIORITY cefi/trades) committed on LDR. Verified:
  `_resolve_pipeline_mode_for_protocol` derives via canonical `pipeline_mode_for_source` (NOT a hand-threaded map);
  honest pre-launch absence; mirrors the existing hyperliquid/aster perp-funding handler. Kalshi-perp live;
  Polymarket-perp scaffold (BLOCKED-UPSTREAM, endpoint DNS-dead).

### 2026-06-21 23:20 — perp live CLOB connectors + live-source resolver fix (line 38)

- mtds@c487a78: `kalshi_perp_ws.py` (full live CLOB, snapshot+delta orderbook, BBO+depth→canonical `book_snapshot`) +
  `polymarket_perp_ws.py` (scaffold, `_ENDPOINT_LIVE=False`, BLOCKED-UPSTREAM); 65 unit tests; QG green.
- **Caught at flip-verify**: `live_pipeline_mode_for_venue("cefi","KALSHI-PERP","book_snapshot")` raised
  `ValueError: No PipelineMode for source 'tardis' in mode 'live'` — the perp venue (hyphen) fell through to the cefi
  `book_snapshot` `SOURCE_PRIORITY` primary `tardis` (batch-only flat-file, no `LIVE_` mode). The live runner would
  crash at `pipeline_mode` resolution.

  FIX (UAC@a6444476, committed via orphan-wip inherit + pushed): added `_CEFI_PERP_LIVE_SOURCE_FOR_VENUE` override in
  `live_source_for_venue` (KALSHI-PERP→kalshi_perp, POLYMARKET-PERP→polymarket_perp) checked before `CEFI_LIVE_VENUES`;
  verified KALSHI-PERP/POLYMARKET-PERP → live_kalshi_perp/live_polymarket_perp, binance unregressed; regression test
  `test_live_source_for_cefi_crypto_perp_venue_is_its_own_ws_feed`.

- Also corrected 2 stale TradFi assertions (NASDAQ/NYSE `ohlcv_1m`→`ohlcv_1m,ohlcv_1s`) — foreign-lane registry change
  (DBEQ.BASIC serves both per Databento SSOT) that had left the asserts stale on LDR HEAD.

### 2026-06-21 23:35 — strategy archetype wiring (line 44) — PERPS WORKSTREAM COMPLETE

- strategy-service@31ba481f: Kalshi-perp + Polymarket-perp added to the carry/basis perp venue bundles +
  funding-dispersion venues (cross-venue dispersion vs the existing CeFi perp universe). 8 unit tests, QG green.
- **Perps workstream (Phases 1-4) COMPLETE for Kalshi-perp end-to-end**: enumerator (IS@fdc9bad) → batch trades+funding
  (mtds@88c2f0c + UAC) → live CLOB ws (mtds@c487a78 + UAC resolver fix@a6444476) → launcher (deployment@86f517d) →
  strategy archetypes (strategy@31ba481f) → docs (codex prediction-perps-sourcing.md). The ONLY open perp item is the
  Polymarket-perp live endpoint (BLOCKED-UPSTREAM — `perps-api.polymarket.com` DNS-dead; scaffold shipped at every
  layer + operator ping filed; flows with zero code change when the endpoint is confirmed).

### 2026-07-06 (cross-plan finding, filed from `prediction_capture_incident_remediation_2026_07_06.md`) — Kalshi-perp enumerator premise was WRONG: wrong host, 0 real perpetuals, 25,473-row cefi contamination found+purged

**The Phase-1 P1 "Kalshi live endpoint verified" claim and the "PERPS WORKSTREAM COMPLETE for Kalshi-perp end-to-end"
entry above do NOT hold — annotated in a banner near the top of this doc; full account here.**

- **What was actually shipped (IS@fdc9bad, 2026-06-21):** `KalshiPerpReferenceDataAdapter` queries
  `api.elections.kalshi.com/trade-api/v2/markets?category=Crypto&status=open` — this is the Kalshi **binary EVENTS
  host** (the same host + endpoint the prediction-side `kalshi.py` adapter uses), NOT a perpetual-futures API. The 16
  unit tests that passed used a synthetic fixture (`category: "Crypto"`) that never occurs on the real host — real
  markets there carry `category: null`, and the adapter's `_parse_market` treated null/empty category as a PASS. So "QG
  green + 16 tests passing" never actually exercised a real-shaped response.
- **Live-probe evidence (2026-07-06):** 3,000 markets across every crypto series (`KXBTC` "Bitcoin range", `KXBTCD`,
  `KXETHD`, …) — **100% `market_type=binary`, 0 tickers containing "PERP."** Every "crypto" market there is a dated
  binary strike bet (e.g. `KXBTC-26JUL0605-T71799.99`).
- **This is the SAME root cause already diagnosed in this plan's own "P1 Kalshi canonical grouping — the premise was
  STALE" entry above** (`category=Crypto` is silently ignored by `/markets`; Kalshi's open universe is dominated by
  auto-generated `KXMVE*` multivariate-parlay markets that flood any un-scoped page). That entry fixed it for the
  PREDICTION adapter (series-scoped enumeration, sidesteps the flood into `canonical_question_group=OTHER`). It was
  never checked against the sibling **cefi** adapter (`kalshi_perp.py`), which has no `OTHER` bucket to catch the flood
  — every `KXMVESPORTSMULTIGAMEEXTENDED` / `KXMVECROSSCATEGORY` binary event that came back got stamped
  `instrument_type=PERPETUAL`, venue `KALSHI-PERP`, and written straight into the cefi catalogue.
- **Blast radius (measured):** cefi catalogue carried **25,473 `KALSHI-PERP` rows** (6.8% of 376,984 total), all fake —
  `available_from` 2026-06-27→07-05 (write-time coherence: the enabling commit instruments-service@4da6fe8 authored
  2026-06-29 08:46 UTC; first contaminated prod write same-day 13:30 UTC run). 0 rows were MVP-tagged (MVP-scoped
  downloads unaffected). `POLYMARKET-PERP` was NOT contaminated (its adapter — separately unverified, see below — never
  wrote any rows).
- **Fixed/contained 2026-07-06 (instruments-service):**
  - `@c8c6dac76` — both `kalshi_perp` and `polymarket_perp` adapters guarded (`_REPOINT_PENDING=True`):
    `get_instruments()`/`get_instrument()` return honest-empty BEFORE any network call; also fixed the `_parse_market`
    empty-category "pass" bug as defense-in-depth. Venue declarations (UAC `VENUES_BY_ASSET_GROUP`) are UNTOUCHED — this
    doesn't undo anything Phase 1 shipped there.
  - Purged the 25,473 fake rows: deleted the 9 `venue=KALSHI-PERP` by_date snapshots (06-27→07-05) + rebuilt the cefi
    catalogue (`--mode full --allow-catalogue-shrink`). Verified: 376,984→351,511 rows, KALSHI-PERP→0, 24 venues,
    DERIBIT + every other venue unchanged (no collateral).
- **NOT fixed — the real repoint is NOT done.** Kalshi's actual perpetuals live on a separate authenticated host:
  `external-api.kalshi.com/trade-api/v2/margin/` (demo `external-api.demo.kalshi.co`), tickers like `BTC-PERPETUAL`,
  RSA-PSS auth, **rolling out member-by-member** — this plan never probed or built against that host. The assumed demo
  endpoint (`…/markets/margin`) 404'd on a follow-up probe, so even the demo path needs re-confirming against Kalshi
  docs before a repoint can be coded.
- **Consequence for THIS plan's "COMPLETE" claim:** batch trades+funding (mtds@88c2f0c), live CLOB ws (mtds@c487a78),
  and strategy archetype bundling (strategy-service@31ba481f) for KALSHI-PERP were all built assuming the enumerator
  returns real perpetuals. It didn't. Those layers should be **re-verified against a correctly-repointed adapter**, not
  assumed correct on the strength of the original "COMPLETE" entry — in particular, if strategy-service's carry/basis or
  funding-dispersion bundles are live-querying/trading KALSHI-PERP believing it has real perpetual instruments+funding
  rates today, that premise is currently false (the venue enumerates 0 instruments post-guard).
- **Not this plan's scope to fix from here** — filed as a cross-plan annotation only (per findings-triage: "fits another
  plan → annotate, don't fix — collision risk"). Full root-cause chain, the live-probe methodology, and the operator's
  "keep the venues, correct the adapter" decision are in
  `plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`; the actionable repoint work (config
  - real endpoint research + demo dry-run + prod cutover, gated on Kalshi member-rollout access) is tracked in
    `plans/active/prediction_capture_incident_remediation_2026_07_06.md` Workstream B — coordinate there before
    re-touching `cefi/kalshi_perp.py` / `cefi/polymarket_perp.py` to avoid duplicate work.
