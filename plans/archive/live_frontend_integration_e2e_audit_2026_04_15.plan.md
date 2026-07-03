---
doc_type: plan
title: live-frontend-integration-e2e-audit
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, deployment-api, e2e-testing, execution-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-16'
overview: End-to-end audit of live data protocols per category, frontend mock modes, API gateway protocol support, and backend service readiness — with phased implementation to wire live data through all 7 layers
type: mixed
epic: epic-code-completion
completion_gates: {code: C5, deployment: D3, business: B4}
repo_gates:
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none}
- {repo: unified-trading-api, code: C0, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
- {repo: execution-service, code: C0, deployment: none, business: none}
- {repo: position-balance-monitor-service, code: C0, deployment: none, business: none}
- {repo: strategy-service, code: C0, deployment: none, business: none}
- {repo: risk-and-exposure-service, code: C0, deployment: none, business: none}
- {repo: client-reporting-api, code: C0, deployment: none, business: none}
- {repo: deployment-api, code: C0, deployment: none, business: none}
- {repo: features-sports-service, code: C0, deployment: none, business: none}
- {repo: ml-inference-service, code: C0, deployment: none, business: none}
- {repo: e2e-testing, code: C0, deployment: none, business: none}
- {repo: system-integration-tests, code: C0, deployment: none, business: none}
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p0-1, content: '- [x] [AGENT] P0. Add SSE helpers to unified-trading-library: `make_sse_router()` factory (mirrors `make_health_router()`), SSEChannel enum, SSEMessage Pydantic model, heartbeat wrapper with configurable interval. UTL already has FastAPI patterns — extend, don''t duplicate.

    ', status: done, note: All SSE-capable services will import from UTL — single implementation}
- {id: p0-2, content: '- [x] [AGENT] P0. Add protocol enum + event schemas to unified-api-contracts: `DataProtocol(REST, WEBSOCKET, SSE, PUBSUB)`, `LiveDataEvent` base model (channel, event_type, data, timestamp), `ProtocolCapability` per-service declaration. Services declare what they support.

    ', status: done, note: UAC is SSOT for schemas — protocol declarations belong here}
- {id: p0-3, content: '- [x] [AGENT] P0. Add `useSSE` React hook to unified-trading-system-ui: generic EventSource wrapper with auto-reconnect (exponential backoff), heartbeat monitoring, mock-mode interception (returns simulated events from fixture data). Mirrors existing useWebSocket pattern.

    ', status: done, note: UI currently has zero SSE hooks — this is the foundation}
- {id: p1-1, content: '- [x] [AGENT] P1. strategy-service: Add SSE endpoint `/stream/signals` using UTL SSE helpers. Publish strategy signals (instrument, direction, confidence, strategy_id) as SSE events when generate_signal() fires. Integrate with existing signal_publisher Pub/Sub — SSE is the external face of internal Pub/Sub signals.

    ', status: done, note: PARALLEL with p1-2..p1-5}
- {id: p1-2, content: '- [x] [AGENT] P1. risk-and-exposure-service: Add SSE endpoint `/stream/risk-alerts` using UTL SSE helpers. Push events on: threshold breach (VaR > limit, exposure > cap), circuit breaker trip, kill switch activation, regime change. Existing pre-trade-check logic already computes these — wire to SSE.

    ', status: done, note: PARALLEL}
- {id: p1-3, content: '- [x] [AGENT] P1. deployment-api: Activate SSE endpoint `/stream/deploy-events` (referenced in docstring but not implemented). Push deployment lifecycle events: started, building, deploying, health-checking, succeeded, failed. Background task already exists.

    ', status: done, note: PARALLEL}
- {id: p1-4, content: '- [x] [AGENT] P1. ml-inference-service: Add SSE endpoint `/stream/predictions` using UTL SSE helpers. Push new prediction events (model_family, instrument, prediction_score, confidence) when batch inference completes. Consumers subscribe by model_family.

    ', status: done, note: PARALLEL}
- {id: p1-5, content: '- [x] [AGENT] P1. features-sports-service: Add SSE endpoint `/stream/feature-ready` using UTL SSE helpers. Push DATA_READY events when feature computation completes for a fixture/league. Include fixture_id, league_id, feature_count, computed_at.

    ', status: done, note: PARALLEL}
- {id: p2-1, content: '- [x] [AGENT] P0. unified-trading-api: Add SSE pass-through endpoints. For each backend SSE source, create a corresponding gateway SSE route that proxies the upstream SSE stream with auth injection. Routes: `/stream/positions` (from position-balance-monitor), `/stream/signals` (from strategy-service), `/stream/risk-alerts` (from risk-service), `/stream/deploy-events` (from deployment-api), `/stream/predictions` (from ml-inference), `/stream/reports` (from client-reporting-api).

    ', status: done, note: ''}
- {id: p2-2, content: '- [x] [AGENT] P0. unified-trading-api: Upgrade WebSocket `/ws` to proxy real backend data in Tier 2 (real mode). Currently all 7 channels generate synthetic data. Wire: `market-data` channel to MTDS WebSocket, `execution` channel to execution-service WS, `sports-live` channel to MTDS sports feed. Keep Brownian motion for Tier 1 (mock mode).

    ', status: done, note: 'Tier 1 mock, Tier 2 real — same channel interface, different data source'}
- {id: p2-3, content: '- [x] [AGENT] P1. unified-trading-api: Add protocol capability discovery endpoint `GET /protocols` returning per-domain protocol support map. Response: `{ "market-data": ["REST", "WEBSOCKET"], "positions": ["REST", "SSE"], "risk": ["REST", "SSE"], ... }`. UI uses this to auto-select optimal protocol.

    ', status: done, note: ''}
- {id: p3-1, content: '- [x] [AGENT] P1. UI: Wire position updates via SSE. Replace REST polling in use-positions hook with useSSE(`/stream/positions`). Fallback to REST poll if SSE unavailable (mock mode or Tier 0). Position cards, portfolio view, balance summaries update in real-time.

    ', status: done, note: PARALLEL with p3-2..p3-8}
- {id: p3-2, content: '- [x] [AGENT] P1. UI: Wire risk alerts via SSE. Add useSSE(`/stream/risk-alerts`) to risk dashboard. Show toast notifications on threshold breach, circuit breaker trip, kill switch. Risk exposure charts update on push. Fallback to REST poll.

    ', status: done, note: PARALLEL}
- {id: p3-3, content: '- [x] [AGENT] P1. UI: Wire strategy signals via SSE. Add useSSE(`/stream/signals`) to strategy monitoring page. Show live signal stream: instrument, direction, confidence, timestamp. Enable filtering by strategy_id. Fallback to REST poll.

    ', status: done, note: PARALLEL}
- {id: p3-4, content: '- [x] [AGENT] P1. UI: Wire ML predictions via SSE. Add useSSE(`/stream/predictions`) to ML monitoring page. Show latest prediction scores, model confidence, drift alerts. Fallback to REST poll.

    ', status: done, note: PARALLEL}
- {id: p3-5, content: '- [x] [AGENT] P1. UI: Wire deployment events via SSE. Add useSSE(`/stream/deploy-events`) to deployment-ui. Show live deployment progress (building → deploying → health-checking → succeeded/failed). Remove manual refresh button.

    ', status: done, note: PARALLEL}
- {id: p3-6, content: '- [x] [AGENT] P1. UI: Enhance sports live mock. In mock mode, simulate minute-by-minute fixture progression: score changes, odds shifts, stat updates. Use existing sports-data.ts fixture but animate it through match timeline (0→90 min). WebSocket mock handler generates events on a 5s interval.

    ', status: done, note: PARALLEL}
- {id: p3-7, content: '- [x] [AGENT] P1. UI: Enhance market data mock. In mock mode, the WebSocket mock should generate realistic tick patterns per category: CeFi (geometric Brownian motion with volume spikes), DeFi (block-aligned price updates every ~12s), TradFi (session-aware with market open/close patterns). Currently uses basic Brownian.

    ', status: done, note: PARALLEL}
- {id: p3-8, content: '- [x] [AGENT] P1. UI: Add protocol indicator to all live-data pages. Small badge showing connection status: "WS Connected" (green), "SSE Streaming" (blue), "REST Polling" (yellow), "Mock" (gray). Helps developers verify which protocol is active. Configurable via dev tools, hidden in production.

    ', status: done, note: PARALLEL}
- {id: p4-1, content: '- [x] [AGENT] P0. e2e-testing: CeFi live data integration test. Start MTDS + unified-trading-api in Tier 2 mock mode. Verify: (a) WS market-data channel delivers ticks for BTC-USDT on Binance, (b) REST /market-data/candles returns OHLCV, (c) WS execution channel delivers fill events after POST /execution/orders, (d) SSE /stream/positions updates after fill. Assert data schema matches UAC types. Timeout: 60s.

    ', status: done, note: PARALLEL with p4-2..p4-6}
- {id: p4-2, content: '- [x] [AGENT] P0. e2e-testing: DeFi live data integration test. Start MTDS + unified-trading-api. Verify: (a) REST /defi/basis/funding-matrix returns per-venue rates, (b) REST /defi/lending/rates returns cross-protocol APYs, (c) POST /execution/defi/execute returns DeFiSwapResult with tx hash, (d) SSE /stream/positions updates with DeFi position. Use Tenderly fork fixtures for on-chain calls.

    ', status: done, note: PARALLEL}
- {id: p4-3, content: '- [x] [AGENT] P0. e2e-testing: Sports live data integration test. Start MTDS + unified-trading-api. Verify: (a) WS sports-live channel delivers fixture updates, (b) REST /api/sports/fixtures returns today''s fixtures, (c) REST /api/sports/fixtures/{id}/odds returns odds timeseries, (d) REST /api/sports/fixtures/{id}/predictions returns ML predictions, (e) POST /execution/sports/bets creates bet. Use mock fixtures with live progression simulation.

    ', status: done, note: PARALLEL}
- {id: p4-4, content: '- [x] [AGENT] P0. e2e-testing: TradFi live data integration test. Verify: (a) REST /market-data/candles for CME/NASDAQ instruments, (b) REST /derivatives/options-chain for Deribit underlyings, (c) REST /derivatives/vol-surface returns volatility surface, (d) SSE /stream/signals delivers TradFi ML directional signals. Use Databento cassettes for replay.

    ', status: done, note: PARALLEL}
- {id: p4-5, content: '- [x] [AGENT] P0. e2e-testing: Prediction Markets live data integration test. Verify: (a) REST /market-data/tickers for Polymarket CLOB markets, (b) instruments endpoint returns prediction market instruments, (c) cross-venue arb detection between Polymarket/Kalshi. Use mock CLOB data.

    ', status: done, note: PARALLEL}
- {id: p4-6, content: '- [x] [AGENT] P0. e2e-testing: Cross-cutting protocol tests. Verify: (a) WebSocket reconnection after server restart (< 5s reconnect), (b) SSE auto-reconnect with exponential backoff, (c) REST→SSE graceful degradation when SSE unavailable, (d) Protocol discovery endpoint returns correct capabilities, (e) Mock mode generates correct event shapes for all protocols. Timeout: 120s.

    ', status: done, note: PARALLEL}
- {id: p5-1, content: '- [x] [AGENT] P0. e2e-testing: Wire CeFi momentum strategy through all 7 layers. L1: instruments-service returns BTC-USDT. L2: MTDS delivers ticks. L3: MDPS produces 1H candles. L4: features-delta-one computes momentum signal. L5: ml-inference produces prediction. L6: strategy-service generates signal → execution-service places order. L7: position-balance updates, PnL attribution runs, risk checks pass. Validate each layer handoff schema.

    ', status: done, note: SEQUENTIAL — each layer depends on prior}
- {id: p5-2, content: '- [x] [AGENT] P0. e2e-testing: Wire DeFi basis strategy through all 7 layers. L1: instruments for Aave V3 ETH. L2: MTDS delivers funding rates + spot. L3: MDPS produces candles. L4: features-onchain computes basis_bps, funding_rate. L5: skip (rule-based). L6: strategy generates hedge signal → execution places spot+perp legs. L7: position tracks delta-neutral, PnL attributes funding yield.

    ', status: done, note: ''}
- {id: p5-3, content: '- [x] [AGENT] P0. e2e-testing: Wire Sports value betting strategy through all 7 layers. L1: instruments-service returns fixtures (3596). L2: MTDS delivers odds from bookmakers. L3: MDPS skipped (sports). L4: features-sports computes team_form, h2h, xG. L5: ml-inference produces match predictions. L6: strategy generates bet signal → execution places bet. L7: position tracks bet, PnL on settlement.

    ', status: done, note: ''}
- {id: p5-4, content: '- [x] [AGENT] P0. e2e-testing: Wire TradFi ML directional strategy through all 7 layers. L1: instruments for SPY/AAPL. L2: MTDS delivers equity ticks. L3: MDPS produces session-aware candles. L4: features-delta-one + features-volatility compute indicators. L5: ml-inference produces prediction_score. L6: strategy generates signal → execution places equity order. L7: position tracks, PnL attributes.

    ', status: done, note: ''}
- {id: p5-5, content: '- [x] [AGENT] P1. e2e-testing: Wire Prediction Markets arb strategy. L1: instruments for Polymarket CLOB markets. L2: MTDS delivers market prices. L4: features-cross-instrument computes cross-venue spread. L6: strategy detects arb → execution places CLOB orders. L7: position tracks, PnL on resolution.

    ', status: done, note: ''}
- {id: p6-1, content: '- [ ] [HUMAN+AGENT] P1. Browser test: Start Tier 2 (full stack) via `dev-tiers.sh --tier 2`. Navigate every category page (CeFi trading, DeFi staking, Sports, TradFi, Predictions, ML, Risk, Execution, PnL). Verify: (a) live data appears (not "Loading..." forever), (b) protocol badge shows correct connection type, (c) position updates stream via SSE, (d) risk alerts appear as toasts, (e) strategy signals stream on monitoring page.

    ', status: todo, note: ''}
- {id: p6-2, content: '- [ ] [HUMAN+AGENT] P1. Browser test: Mock mode validation. Start Tier 1 (mock). Navigate every page. Verify: (a) mock data renders correctly for all categories, (b) sports fixtures progress minute-by-minute, (c) market data shows category-appropriate tick patterns, (d) all actions (place order, place bet, execute DeFi) work with mock responses, (e) no console errors, (f) protocol badge shows "Mock" on all pages.

    ', status: todo, note: ''}
- {id: p6-3, content: '- [ ] [HUMAN+AGENT] P1. Browser test: Graceful degradation. Start Tier 2, then kill individual services. Verify: (a) SSE reconnects automatically, (b) WebSocket reconnects with backoff, (c) REST fallback activates when streaming unavailable, (d) error states show user-friendly messages, (e) no infinite spinners or blank pages.

    ', status: todo, note: ''}
- {id: p7-1, content: '- [ ] [AGENT] P2. e2e-testing: Update coverage-matrix.md with protocol column (REST/WS/SSE) per strategy per layer. Add protocol integration test results. Update per-strategy-acceptance.md with protocol-specific acceptance criteria.

    ', status: todo, note: PARALLEL with p7-2}
- {id: p7-2, content: '- [ ] [AGENT] P2. Run quality-gates.sh on ALL 15 affected repos. Fix any failures. All repos must reach C4 minimum.

    ', status: todo, note: PARALLEL}
isProject: true
---

## Architecture Context

### Protocol Decision Matrix

```
Data Type               │ Protocol  │ Direction     │ Latency    │ Mock Strategy
────────────────────────┼───────────┼───────────────┼────────────┼──────────────────
Market ticks (CeFi)     │ WebSocket │ Server→Client │ <50ms      │ Brownian motion
Market ticks (DeFi)     │ WebSocket │ Server→Client │ ~12s/block │ Block-aligned ticks
Market ticks (TradFi)   │ SSE       │ Server→Client │ <30s       │ Session-aware ticks
Sports live scores      │ WebSocket │ Bidirectional │ <1s        │ Fixture progression
Sports odds             │ WebSocket │ Server→Client │ <1s        │ Odds shift simulation
Order status/fills      │ WebSocket │ Bidirectional │ <100ms     │ Synthetic fills
Position updates        │ SSE       │ Server→Client │ 1-5s       │ Position snapshots
Risk alerts             │ SSE       │ Server→Client │ 5-30s      │ Threshold events
PnL/analytics           │ SSE       │ Server→Client │ 10-60s     │ P&L snapshots
Strategy signals        │ SSE       │ Server→Client │ <1s        │ Signal replay
Alerts/notifications    │ SSE       │ Server→Client │ <5s        │ Alert fixtures
ML predictions          │ REST      │ Request/Resp  │ Minutes    │ Static fixtures
Features                │ REST      │ Request/Resp  │ Minutes    │ Static fixtures
Service health          │ SSE       │ Server→Client │ 15-30s     │ Health snapshots
Deployment events       │ SSE       │ Server→Client │ 5-30s      │ Deploy lifecycle
Reports                 │ SSE       │ Server→Client │ N/A        │ Report snapshots
```

### Why SSE over WebSocket for server-push?

- SSE uses standard HTTP (works through all proxies, load balancers, CDNs)
- Auto-reconnect built into EventSource API (no custom reconnection logic)
- Simpler server implementation (no upgrade handshake, no frame protocol)
- WebSocket reserved for bidirectional needs: market data subscriptions (subscribe/unsubscribe), order management
  (place/cancel/amend), sports fixture subscriptions

### Dependency DAG

```
Phase 0 (Foundation)
  ├── UTL SSE helpers
  ├── UAC protocol schemas
  └── UI useSSE hook
       │
Phase 1 (Backend SSE) ──── all 5 services PARALLEL
       │
Phase 2 (API Gateway) ──── SEQUENTIAL (single repo)
       │
Phase 3 (Frontend Wiring) ── 8 tasks PARALLEL
       │
Phase 4 (Protocol E2E) ──── 6 tests PARALLEL
       │
Phase 5 (Strategy Pipeline) ── 5 strategies, each L1→L7 SEQUENTIAL
       │
Phase 6 (Browser E2E) ──── SEQUENTIAL (needs full stack)
       │
Phase 7 (Docs + QG) ──── PARALLEL
```

### Mock Mode Behavior by Tier

| Tier | VITE_MOCK_API | CLOUD_MOCK_MODE | WebSocket                 | SSE                       | Data Source          |
| ---- | ------------- | --------------- | ------------------------- | ------------------------- | -------------------- |
| 0    | true          | N/A             | Mock events from fixtures | Mock events from fixtures | Static fixtures only |
| 1    | false         | true            | Synthetic Brownian motion | Synthetic push events     | MockStateStore       |
| 2    | false         | false           | Real MTDS/execution feeds | Real service SSE streams  | GCS + live APIs      |

### Strategy Latency Budgets (from codex/09-strategy)

| Family         | Tick→Feature | Feature→Signal | Signal→Order | Total E2E           |
| -------------- | ------------ | -------------- | ------------ | ------------------- |
| CeFi MM        | <100ms       | <20ms          | <50ms        | <100ms (co-located) |
| CeFi Momentum  | N/A (candle) | <200ms         | <7s          | <7s                 |
| DeFi Basis     | N/A (1H)     | <200ms         | <37s         | <37s                |
| DeFi LP        | Per-block    | <500ms         | <60s         | <60s                |
| TradFi ML      | N/A (event)  | <200ms         | <720ms       | <720ms              |
| Sports Value   | <1s odds     | <5m model      | <3s          | <3s bet placement   |
| Sports HT ML   | <1s          | <200ms         | <7.7s        | <7.7s               |
| Prediction Arb | <200ms       | <200ms         | <75s         | <75s (CLOB)         |

### Pre-Audit: Affected Repos (15)

| Repo                             | Changes                                        | Protocol Added |
| -------------------------------- | ---------------------------------------------- | -------------- |
| unified-trading-library          | SSE helpers, SSEChannel enum                   | SSE foundation |
| unified-api-contracts            | DataProtocol enum, LiveDataEvent schema        | Schema SSOT    |
| unified-trading-system-ui        | useSSE hook, 8 page wirings, mock enhancements | SSE consumer   |
| unified-trading-api              | SSE pass-through, WS proxy upgrade, /protocols | Gateway        |
| market-tick-data-service         | No changes (WS already exists)                 | —              |
| execution-service                | No changes (WS already exists)                 | —              |
| position-balance-monitor-service | No changes (SSE already exists)                | —              |
| strategy-service                 | SSE /stream/signals                            | SSE producer   |
| risk-and-exposure-service        | SSE /stream/risk-alerts                        | SSE producer   |
| deployment-api                   | SSE /stream/deploy-events (activate stub)      | SSE producer   |
| ml-inference-service             | SSE /stream/predictions                        | SSE producer   |
| features-sports-service          | SSE /stream/feature-ready                      | SSE producer   |
| client-reporting-api             | No changes (SSE already exists)                | —              |
| e2e-testing                      | 11 new integration tests                       | Test coverage  |
| system-integration-tests         | Protocol smoke tests                           | SIT coverage   |
