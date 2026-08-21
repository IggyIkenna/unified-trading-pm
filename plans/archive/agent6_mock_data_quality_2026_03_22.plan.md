---
doc_type: plan
title: agent6-mock-data-quality
summary: Enhance seed data realism, add org-scoped filtering, persona-based entitlement filtering, deterministic seeding
  for CI
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, unified-trading-api, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-22"
todos:
  - {
      id: a6-p0-persona-ssot,
      content:
        "- [x] [AGENT] P0. VERIFY existing personas.py (121 lines, already exists at
        unified_trading_api/mock_data/personas.py with 4 orgs, 5 personas). Ensure it matches auth-api mock_data.py
        EXACTLY (org IDs, persona names, entitlements). If any misalignment: fix personas.py to match. Add any missing
        entitlement keys needed by the UI (check hooks/use-auth.ts).\n  - 4 organizations: Odum Internal
        (odum-internal), Alpha Capital (acme), Beta Fund (beta), Vertex Partners (vertex)\n  - 5 personas: admin,
        internal-trader, client-full (acme), client-premium (vertex), client-data-only (beta)\n  - Entitlements per
        persona matching the UI's entitlement checks\n  Export these as constants. auth-api should import from here (or
        duplicate with same IDs). UI persona definitions must use the same org IDs and entitlement keys.\n",
      status: done,
    }
  - {
      id: a6-p0-org-scoped-seed,
      content:
        "- [x] [AGENT] P0. Update ALL seed data in `seed.py` to include `org_id` field on every record.
        Distribution:\n  - odum-internal: 60% of data (internal strategies, positions, orders)\n  - acme (Alpha
        Capital): 20% of data\n  - vertex (Vertex Partners): 12% of data\n  - beta (Beta Fund): 8% of data (data-only,
        minimal trading)\n  When a client persona queries, they only see their org's data. Admin/internal sees all.\n",
      status: done,
    }
  - { id: a6-p1-strategies-alignment, content: "- [x] [AGENT] P0. Expand seed strategies from 18 to 50+ using the
        config-driven approach. Strategies are CONFIG, not code — the EventDrivenStrategyEngine in strategy-service is
        parameterised by subscription config (see /codex/09-strategy/_archived_pre_v2/cross-cutting/config-architecture.md). No new
        engine code paths needed.\n  Step 1: Keep the existing 18 strategies from `lib/trading-data.ts` with SAME IDs,
        names, asset classes (for Dashboard visual parity during migration).\n  Step 2: Add 32+ new strategies by
        combining codex archetypes x UAC asset classes:\n  - 13 code-complete archetypes: momentum, mean-reversion,
        ML-directional, options-ML, basis-trade, staked-basis, recursive-basis, AAVE-lending, AMM-LP, arbitrage,
        value-betting, ML-sports, market-making\n  - 5 asset classes from UAC representative_sample.py: CeFi, TradFi,
        DeFi, Sports, Prediction\n  - Naming convention: `{ASSET}_{ARCHETYPE}_{MODE}_{TIMEFRAME}` e.g.
        `CEFI_MOMENTUM_LIVE_1H`\n  Each strategy\
        \ config includes: id, name, archetype, asset_group, instruments[] (referencing UAC registry symbols),
        execution_mode (live/paper), timeframe, risk_limits, org_id, inception_date.\n  Instruments in each strategy
        MUST reference symbols that exist in UAC representative_sample.py — no invented instruments.\n  Store in
        MockStateStore `strategies` and `strategy_configs` collections.\n  The UI reads strategy lists from `GET
        /analytics/strategies` and `GET /analytics/strategy-configs` — NOT from `trading-data.ts` or
        `strategy-registry.ts`.\n", status: done }
  - { id: a6-p1-positions-realistic, content: "- [x] [AGENT] P0. Seed realistic positions: 15-20 positions across 5
        venues (Binance, Deribit, Hyperliquid, Uniswap V3, Aave V3). Each position should have: instrument (matching
        real instrument symbols), side (long/short), quantity, entry_price, current_price (slightly different from entry
        for realistic PnL), unrealized_pnl, margin_used, venue, org_id, strategy_id.

        ", status: done }
  - { id: a6-p1-orders-realistic, content: "- [x] [AGENT] P0. Enhance orders seed from 4 to 20+. Include orders across
        all venues, with status distribution: 40% filled, 20% partially_filled, 20% open, 10% cancelled, 10% rejected.
        Each order should reference a valid strategy_id and org_id.

        ", status: done }
  - { id: a6-p1-fills-realistic, content: "- [x] [AGENT] P1. Enhance fills seed from 3 to 30+. Each fill should
        reference a valid order_id. Include realistic slippage (0.01-0.05% from order price), realistic fees
        (venue-specific fee rates).

        ", status: done }
  - {
      id: a6-p1-alerts-realistic,
      content:
        "- [x] [AGENT] P0. Seed 15-20 alerts with realistic scenarios:\n  - 2-3 critical: \"Position limit breached on
        BTC-USDT\", \"Margin call warning on Deribit\"\n  - 4-5 high: \"Strategy drawdown exceeds threshold\", \"Venue
        latency spike on Hyperliquid\"\n  - 5-6 medium: \"Batch/live PnL drift > 5%\", \"Feature staleness
        detected\"\n  - 3-4 low: \"Strategy rebalance scheduled\", \"Model retrain due\"\n  Each alert should have:
        severity, message, source (service name), strategy_id, org_id, timestamp, acknowledged (bool).\n",
      status: done,
    }
  - {
      id: a6-p1-ml-data,
      content:
        "- [x] [AGENT] P1. Seed ML data:\n  - 8 models: mean-reversion-btc, momentum-multi-asset, vol-surface-eth, etc.
        With versions (v1.0, v1.1, v2.0), status (production/staging/deprecated), metrics (sharpe, accuracy,
        precision)\n  - 12 experiments: linked to models, with hyperparameters, training metrics (loss curve data
        points), duration\n  - 20 features: with importance scores, drift metrics, categories\n  - 5 training jobs:
        queued/running/completed/failed\n",
      status: done,
    }
  - {
      id: a6-p1-settlements-invoices,
      content:
        "- [x] [AGENT] P1. Seed settlement and invoicing data:\n  - 8 settlements: various status
        (pending/matched/disputed/settled), with trade references\n  - 5 invoices: management fee invoices with
        calculation breakdown (AUM * fee_rate / 365 * days)\n  - 3 fee schedules: tier-based (basic: 0.5% mgmt, premium:
        1% mgmt + 10% perf, full: 1.5% mgmt + 15% perf)\n",
      status: done,
    }
  - { id: a6-p1-services-health, content: "- [x] [AGENT] P0. Seed service health data matching actual 21 services. Each
        record: name (matching real service names from workspace-manifest.json), status (healthy/degraded/down),
        latency_ms, last_check, version, uptime_pct. Most services healthy, 1-2 degraded for realism.

        ", status: done }
  - { id: a6-p1c-timeseries-pnl, content: "- [x] [AGENT] P0. Seed PnL time-series data for ALL 50+ strategies: 180 daily
        data points per strategy. Each point: `{ strategy_id, date, cumulative_pnl, daily_pnl, drawdown, nav }`.
        Generate with archetype-appropriate equity curves:\n  - Momentum: trending with sharp reversals, positive drift,
        10-20% max drawdown\n  - Mean-reversion: oscillating around baseline, tight range, 5-10% drawdown\n  -
        Market-making: steady low-vol income (0.01-0.05% daily), occasional spikes (spread blow-out)\n  - DeFi yield:
        steady positive accrual, protocol-risk drawdowns (5-15% on DeFi event days)\n  - Basis trade: low-vol positive
        carry, convergence risk at expiry\n  - Sports/prediction: step-function PnL (bet resolves to discrete gain/loss,
        flat between events)\n  - ML-directional: trending with model-driven entry/exit, higher vol than momentum\n  For
        the ORIGINAL 18 strategies (from trading-data.ts): PnL curves must match closely enough for visual parity during
        Dashboard\
        \ migration.\n  For NEW 32+ strategies: generate fresh curves per archetype.\n  - Start from strategy inception
        date (stagger across last 12 months)\n  - Trend: 60% of strategies profitable overall\n  - Correlation: crypto
        strategies correlated to BTC candle data (seed BTC series first, derive others)\n  - Include YTD, MTD, QTD
        breakpoints for reporting\n  Store in MockStateStore `pnl_timeseries_live` and `pnl_timeseries_batch`
        collections.\n", status: done }
  - { id: a6-p1c-ohlcv-candles, content: "- [x] [AGENT] P0. Seed OHLCV candle data for ALL instruments from UAC
        representative_sample.py across 4 intervals.\n  DO NOT hardcode an instrument list. Import the registry
        programmatically:\n  `from unified_api_contracts.registry.representative_sample import CEFI_SPOT_SPECS,
        CEFI_PERPETUAL_SPECS, TRADFI_EQUITY_SPECS, TRADFI_FUTURES_SPECS, DEFI_INSTRUMENT_SPECS,
        SPORTS_INSTRUMENT_SPECS`\n  Build the full instrument list from all spec lists. This means if UAC registry
        expands, `POST /admin/reset` regenerates candles for new instruments automatically.\n  - Intervals: 1m (200
        candles), 5m (200), 1h (200), 1d (200) per instrument\n  - Generate with Brownian motion per asset class: CeFi
        crypto high vol (1-3% daily), TradFi equities low vol (0.3-1%), DeFi medium, Sports step-function prices\n  -
        Volume profile: higher at opens/closes for TradFi/CeFi, flatter for DeFi\n  - Store in MockStateStore
        `candles_1m`, `candles_5m`, `candles_1h`, `candles_1d` collections\n\
        \  - The candle generator is a function(instrument_specs, base_prices) not a hardcoded array\n", status: done }
  - {
      id: a6-p1c-tickers-seed,
      content:
        "- [x] [AGENT] P0. Seed initial ticker prices in `tickers_live` collection for ALL instruments from UAC
        representative_sample.py. Import the registry (same as candles). Each ticker: `{ instrument, venue, price, bid,
        ask, volume_24h, change_24h_pct, asset_group, timestamp }`. Prices realistic as of today: BTC ~$67K, ETH ~$3.5K,
        AAPL ~$195, QQQ ~$490, ES ~$5300, VIX ~$15, aTokens at protocol rates, sports at probability-based pricing
        (0.30-0.70).\n  These serve as the starting point for the WebSocket mock tick generator (Agent 5). Also seed
        `tickers_batch` with yesterday's close prices (slightly different from live).\n",
      status: done,
    }
  - { id: a6-p2-batch-live-data, content: "- [x] [AGENT] P0. Seed separate batch and live data collections in
        MockStateStore. ALL domains must have both `_live` and `_batch` variants. Live collections persist to
        `.local-dev-cache/unified-trading-api/` as JSONL (survive restarts, get updated by WebSocket ticks and manual
        actions). Batch collections are seeded once and immutable until reset.\n\n  Collection naming convention (ALL
        time-varying domains get both variants):\n  - `positions_live` / `positions_batch`\n  - `orders_live` /
        `orders_batch`\n  - `fills_live` / `fills_batch`\n  - `pnl_live` / `pnl_batch`\n  - `tickers_live` /
        `tickers_batch`\n  - `pnl_timeseries_live` / `pnl_timeseries_batch`\n  - `alerts_live` / `alerts_batch`\n  -
        `risk_live` / `risk_batch`\n\n  When API receives `mode=batch&as_of=2026-03-21`, it reads from `*_batch`
        collections.\n  When API receives `mode=live` (or no mode param), it reads from `*_live` collections.\n\n  Batch
        vs live differences (to make the switch visually\
        \ meaningful):\n  - Batch PnL includes reconciliation adjustments (+/- 0.1-0.5% from live)\n  - Batch positions
        may have 1-2 fewer positions (unreconciled fills not yet in batch)\n  - Batch uses official close prices; live
        uses last tick prices\n  - Batch has exact fee breakdowns; live has estimated fees\n  - Batch orders all have
        final status (filled/cancelled); live has open/partial orders\n  - Batch alerts all have final status
        (acknowledged/escalated/resolved); live has unacknowledged alerts\n  - Batch risk is end-of-day snapshot; live
        risk updates as positions/prices change\n  The data SHAPE is >90% identical. Same fields, same schema. Only the
        values differ slightly to reflect the T+1 reconciliation process. The service layer code (filtering, pagination,
        org-scoping) is identical — the only branching is the collection name suffix.\n\n  This architecture means: in
        production, the same directory is populated by real services.\n  In mock, it's populated by seed data +
        WebSocket tick\
        \ generator. The API code is identical.\n", status: done }
  - { id: a6-p3-deterministic, content: '- [x] [AGENT] P1. Add seed versioning: `SEED_VERSION = "1.0.0"` in seed.py.
        MockStateStore checks cached seed version against current — if mismatch, clears cache and re-seeds. This ensures
        developers always get fresh data after code pulls.

        ', status: done }
  - { id: a6-p3-ci-mode, content: "- [x] [AGENT] P1. When `MOCK_STATE_MODE=deterministic` (CI mode): skip JSONL
        persistence, use pure in-memory store, seed on every startup. When `MOCK_STATE_MODE=interactive` (dev mode):
        persist mutations to `.local-dev-cache/unified-trading-api/`, survive restarts.

        ", status: done }
  - { id: a6-p4-remove-msw, content: "- [x] [AGENT] P1. In unified-trading-system-ui: remove `lib/mocks/` directory
        (browser.ts, server.ts, handlers/, fixtures/, utils.ts — 1,411 lines total). Remove MSW from package.json
        dependencies. Remove `startMockWorker()` call from app initialization. The UI now always calls the real API at
        port 8030 (which handles mock/real internally).

        ", status: done }
  - { id: a6-p4-migrate-trading-data, content: "- [x] [AGENT] P1. Migrate the Dashboard page from client-side
        `lib/trading-data.ts` data to API calls. Currently the Dashboard imports ORGANIZATIONS, CLIENTS, STRATEGIES,
        getFilteredStrategies, getAggregatedPnL, etc. from trading-data.ts. Replace these with API hook calls:
        `useTradingOrgs()`, `useTradingPnl()`, `useTradingTimeseries()`, `useTradingPerformance()` (these hooks already
        exist in `hooks/api/use-trading.ts`). The seed data in the API must match the trading-data.ts output closely
        enough that the Dashboard looks the same.

        ", status: done }
  - {
      id: a6-p5-seed-tests,
      content:
        "- [x] [AGENT] P0. Add tests verifying seed data quality:\n  1. Every record has org_id field\n  2. All
        strategy_ids in positions/orders reference valid strategies\n  3. All order_ids in fills reference valid
        orders\n  4. Org filtering works (client-full sees only acme data)\n  5. Batch vs live data returns different
        results\n  6. Reset clears mutations but preserves seed\n",
      status: done,
    }
  - { id: a6-p6-data-consistency, content: "- [x] [AGENT] P0. Add cross-domain data consistency validation to seed.py.
        After seed_all_domains(), run validate_consistency() that checks:\n  1. Price consistency: OHLCV candle close
        prices for a given date match the price used to calculate that day's strategy PnL (for strategies trading that
        instrument)\n  2. Reference integrity: every strategy_id in positions/orders exists in strategies collection.
        Every order_id in fills exists in orders. Every org_id exists in organizations.\n  3. Temporal consistency: no
        position opened_at before strategy inception_date. PnL time-series starts at strategy inception.\n  4.
        Aggregation consistency: sum of position-level PnL per strategy approximately equals strategy's reported PnL
        (within 5% tolerance)\n  5. Batch/live consistency: batch data is a slightly stale version of live — not
        completely different random data. Batch positions = live positions minus 1-2 unreconciled fills.\n  6.
        validate_consistency() raises\
        \ ValueError with descriptive message on any violation. It runs automatically in seed_all_domains() — no manual
        invocation needed.\n", status: done }
  - {
      id: a6-p6-client-reporting-alignment,
      content:
        "- [x] [AGENT] P1. Ensure client-reporting-api mock data aligns with unified-trading-api seed data.
        unified-trading-api proxies /reporting/* to client-reporting-api in real mode. In mock mode, unified-trading-api
        serves from its own MockStateStore. For demo consistency:\n  1. Read client-reporting-api's mock_data if it
        exists\n  2. Ensure the same org IDs, client names, and report types are used\n  3. If client-reporting-api has
        its own seed data, verify no conflicts with unified-trading-api's reporting seed data\n  4. Document any
        alignment issues as TODOs for follow-up\n",
      status: done,
    }
  - {
      id: a6-p6-sample-pdfs,
      content:
        "- [x] [AGENT] P1. Create sample PDF reports in `unified_trading_api/mock_data/sample_reports/`:\n  1.
        `executive_report.pdf` — 1-2 pages: title \"Executive Summary — March 2026\", AUM table, top strategies, risk
        summary\n  2. `pnl_attribution.pdf` — 1-2 pages: title \"P&L Attribution Report\", attribution table by
        strategy\n  3. These are served by Agent 5's `GET /reporting/download/{report_id}` endpoint\n  4. Can be
        generated programmatically using reportlab or fpdf2, or be static hand-crafted PDFs\n",
      status: done,
    }
  - {
      id: a6-p6-news-seed,
      content:
        "- [x] [AGENT] P1. Seed 15-20 mock news items for the Observe > News page (currently a 24-line stub):\n  1. Each
        item: title, source (Reuters, Bloomberg, CoinDesk, etc.), timestamp (last 48 hours), category (market,
        regulatory, macro, crypto), relevance_score, linked_instruments[]\n  2. Mix of: market moves (\"BTC breaks $70K
        resistance\"), regulatory (\"SEC approves spot ETH ETF\"), macro (\"Fed signals rate pause\"), crypto-specific
        (\"Uniswap V4 launch\")\n  3. Store in MockStateStore \"news\" collection. API serves via GET
        /market-data/news.\n",
      status: done,
    }
  - { id: a6-p7-full-instrument-seed, content: "- [x] [AGENT] P0. Expand seed data to cover ALL instruments from UAC
        representative_sample.py — not a hardcoded 10:\n  1. Import `from
        unified_api_contracts.registry.representative_sample import ...` to get the full instrument list (~40 specs:
        CeFi spot, CeFi perps, TradFi, DeFi pools, sports leagues)\n  2. Seed OHLCV candles for ALL instruments: 4
        intervals × 200 candles each. Use Brownian motion generator (~50 lines, not hardcoded). Total: ~32,000 candle
        records.\n  3. Seed tickers_live and tickers_batch for ALL instruments with realistic prices\n  4. Seed order
        books (generated on-the-fly by Agent 5, not pre-seeded — but tickers must exist)\n  5. The Brownian motion
        generator must accept a base price per instrument — use realistic prices from the registry\n  6. Group
        instruments by category for the candle generation: crypto uses 24/7 timestamps, tradfi uses market hours, sports
        uses match schedules\n  DEPENDENCY: UAC representative_sample.py\
        \ is the SSOT. No upstream changes needed.\n", status: done }
  - { id: a6-p7-strategy-expansion, content: "- [x] [AGENT] P0. Expand strategies from 18 to 50+ using the combinatorial
        matrix from CITADEL_VISION:\n  1. Read `unified-trading-pm/codex/09-strategy/` for all documented archetypes (10
        types across 5 asset classes)\n  2. Generate 50+ strategies following the naming convention:
        `{CATEGORY}_{INSTRUMENT}_{ARCHETYPE}_{MODE}_{TIMEFRAME}`\n  3. Distribution: CeFi 16, TradFi 11, DeFi 11, Sports
        9, Prediction 3 (as per CITADEL_VISION matrix)\n  4. Each strategy gets: org_id (distributed across 4 orgs), PnL
        time-series (180 daily points), 2-5 positions, 3-8 orders, realistic metrics (sharpe, drawdown, etc.)\n  5.
        Strategy types that map to config, not code: market making for all asset classes, ML directional for all,
        momentum/mean reversion for CeFi/TradFi, value betting for sports, arbitrage across all\n  6. Update
        `strategy-registry.ts` (1,863 lines) in the UI to include all 50+ strategies with proper archetype/category
        metadata\n  7. Ensure all strategy\
        \ archetypes documented in codex 09-strategy/ are represented\n  DEPENDENCY: None — seed generation is
        procedural. But strategy-registry.ts update requires understanding the UI's type system.\n", status: done }
  - {
      id: a6-p7-run-sync-pipeline,
      content:
        "- [x] [AGENT] P0. Run the full SSOT sync pipeline AFTER completing all seed data expansion:\n  1. Run `python
        unified-trading-pm/scripts/openapi/generate_ui_reference_data.py` to sync UAC registries →
        ui-reference-data.json\n  2. Verify ui-reference-data.json includes ALL instruments from
        representative_sample.py\n  3. Verify strategy-manifest.json in PM is updated with the 50+ strategies\n  4. Run
        `python unified-trading-pm/scripts/validation/validate-strategy-manifest.py` to validate\n  5. Run `python
        unified-trading-pm/scripts/manifest/check-strategy-instruments.py` to verify instrument refs\n  6. Document
        which sync scripts were run and their output in a commit message\n  DEPENDENCY: All seed data expansion
        (a6-p7-full-instrument-seed, a6-p7-strategy-expansion) must be complete.\n",
      status: done,
    }
  - {
      id: a6-p7-strategy-registry-alignment,
      content:
        "- [x] [AGENT] P0. Ensure strategy definitions are aligned across all layers:\n  1.
        `unified-trading-pm/codex/09-strategy/` — documented archetypes (SSOT for what strategies exist)\n  2.
        `unified-api-contracts` — strategy type enums must include all 10 archetypes\n  3. `unified-api-contracts
        (internal contracts)` — strategy schemas must support all 4 execution modes\n  4.
        `unified-trading-api/mock_data/seed.py` — 50+ strategies seeded\n  5.
        `unified-trading-system-ui/lib/strategy-registry.ts` — 50+ strategies with UI metadata\n  6.
        `unified-trading-pm/strategy-manifest.json` — 50+ strategies registered\n  7. If any layer is missing archetypes
        or execution modes, ADD them. The codex is the SSOT — everything else derives from it.\n  DEPENDENCY: Strategy
        expansion (a6-p7-strategy-expansion) must be complete first.\n",
      status: done,
    }
  - {
      id: a6-p8-risk-limits,
      content:
        "- [x] [AGENT] P0. Seed `risk_limits` collection for pre-trade compliance checks. GAP CATEGORY: Type 3
        (risk-and-exposure-service has pre-trade engine — mock needs seed data to simulate it).\n  The REAL service
        reads limits from `RiskLimitsDomainClient` (GCS backend per client_id). For mock, seed static limits.\n  Per
        strategy, seed: max_position_size_usd, max_leverage, max_var_99, max_exposure_pct, max_open_orders.\n  Realistic
        values: momentum strategies get tighter limits (max_leverage 3x, max_position 500K), market-making gets wider
        (max_leverage 10x, max_position 2M), DeFi yield gets conservative (max_leverage 1.5x).\n  Store in `risk_limits`
        collection, keyed by strategy_id.\n  Make at least 2-3 limits intentionally CLOSE to current positions (so
        pre-trade check demo can show a \"fail\" scenario with a slightly-too-large order).\n",
      status: done,
    }
  - { id: a6-p8-options-chain-seed, content: "- [x] [AGENT] P0. Seed `options_chain` collection. GAP CATEGORY: Type 3
        (features-volatility-service computes Greeks — mock needs seeded chain).\n  The REAL data comes from Deribit
        (via UMI) and features-volatility-service computes second-order Greeks.\n  Import Deribit options config from
        `representative_sample.py` (generates strikes/expiries from ref_date).\n  For BTC options (primary), seed a
        realistic chain:\n  1. 5 expiry buckets: 7d, 14d, 30d, 60d, 90d from today\n  2. Per expiry: 10 strikes (0.8x to
        1.2x of current BTC price in 5% increments)\n  3. Per strike+expiry: call AND put entry with realistic
        Greeks\n  4. Greeks generation: use Black-Scholes formula (it's ~20 lines of Python):\n     d1 = (ln(S/K) + (r +
        sigma^2/2)*T) / (sigma*sqrt(T))\n     delta_call = N(d1), gamma = N'(d1)/(S*sigma*sqrt(T)), theta,
        vega\n     ATM IV ~45% for BTC, skew: lower strikes higher IV (smile)\n  5. For ETH: similar but ATM IV ~55%,
        fewer strikes\n  6. For\
        \ SPY: ATM IV ~15%, tighter strikes (1% increments)\n  Store in `options_chain` collection grouped by
        underlying+venue.\n", status: done }
  - {
      id: a6-p8-vol-surface-seed,
      content:
        "- [x] [AGENT] P0. Seed `vol_surfaces` collection. GAP CATEGORY: Type 3 (features-volatility-service computes
        full surfaces).\n  Import format from `features-volatility-service/app/calculators/tradfi_vol_surface.py` output
        shape.\n  Per underlying (BTC, ETH, SPY):\n  1. Slices: one per expiry bucket (7d, 30d, 60d, 90d). Each slice: {
        expiry_days, smile: [{ strike, iv }] }\n  2. Term structure: [{ expiry_days, atm_iv }] — upward sloping
        (short-term IV < long-term IV)\n  3. Key metrics: atm_iv, skew_25d (negative for equities, more negative for
        crypto), butterfly_25d, risk_reversal_25d\n  4. Vol regime: { iv_percentile: 45, vrp: 3.2 (vol risk premium),
        regime: \"normal\" }\n  BTC realistic values: ATM IV 45%, 25d skew -5%, term structure slope +2% per 30d\n  SPY:
        ATM IV 15%, 25d skew -3%, flatter term structure\n",
      status: done,
    }
  - { id: a6-p8-var-metrics-seed, content: "- [x] [AGENT] P0. Seed `var_metrics`, `stress_test_results`, and
        `correlation_matrix` collections. GAP CATEGORY: Type 3 (risk-and-exposure-service computes all of this — mock
        needs seed data).\n  IMPORT FORMAT from `risk-and-exposure-service/scripts/seed_mock_data.py` (548L) which
        already generates realistic VaR and stress data. Adapt its output format.\n  1. `var_metrics` collection:
        per-strategy VaR. Fields: strategy_id, historical_var_99, parametric_var_99, cvar_99, cornish_fisher_var_99.
        Realistic: momentum strategies VaR 2-5%, mean-reversion 1-3%, DeFi yield 0.5-2%.\n  2. `stress_test_results`
        collection: per-scenario portfolio impact. 3 scenarios: GFC_2008 (portfolio -15%), COVID_2020 (-10%),
        CRYPTO_BLACK_THURSDAY (-25%). Per scenario: portfolio_impact_pct, expected_loss_usd, worst_strategy_id.\n  3.
        `correlation_matrix` collection: single record with NxN matrix. Crypto strategies correlated ~0.5-0.7. TradFi
        ~0.2-0.4. DeFi/Sports near 0 (uncorrelated).\
        \ Use strategy_ids as row/column labels.\n  4. `regime` collection: single record { regime: \"normal\",
        multiplier: 1.0, vol_signal: 0.02, correlation_signal: 0.3, drawdown_velocity: -0.005 }.\n", status: done }
  - {
      id: a6-p8-fx-rates-seed,
      content:
        "- [x] [AGENT] P0. Seed `fx_rates` collection and add `denomination_currency` + `fx_rate_to_usd` to positions.
        GAP CATEGORY: Type 1+3 (NO service has FX — genuinely missing, trivial to mock).\n  1. `fx_rates` collection: {
        \"BTC/USD\": 67000, \"ETH/USD\": 3500, \"USDT/USD\": 1.0001, \"EUR/USD\": 1.08, \"GBP/USD\": 1.27 }\n  2. Add to
        EVERY position record: `denomination_currency` (USDT for Binance, BTC for Deribit, USD for CME/NYSE, ETH for
        Uniswap/Aave) and `fx_rate_to_usd` (e.g., 1.0 for USD, 67000 for BTC-denominated).\n  3. This enables Agent 5's
        PnL aggregation to show correct USD-converted totals.\n",
      status: done,
    }
  - {
      id: a6-p8-regulatory-seed,
      content:
        "- [x] [AGENT] P1. Seed `regulatory_reports` collection. GAP CATEGORY: Type 2+3 (execution-service has MiFID
        II/FCA reporter — mock needs seed data).\n  Seed 8-10 regulatory report records matching the events
        execution-service would emit:\n  - 3 MiFID II best execution reports (status: submitted)\n  - 2 FCA transaction
        reports (status: submitted)\n  - 2 EMIR derivative reports (status: pending)\n  - 1 overdue report (status:
        overdue, demonstrates alerting)\n  Fields: report_id, report_type, jurisdiction, status, filing_date,
        next_due_date, instruments_covered[], filing_reference.\n",
      status: done,
    }
  - {
      id: a6-p8-market-hours,
      content:
        "- [x] [AGENT] P1. Amend OHLCV candle generator to respect market hours per asset class. GAP CATEGORY: Type 3
        (real market data respects trading sessions — mock generator ignores them).\n  1. CeFi/DeFi: 24/7 candles (no
        change needed)\n  2. TradFi equities (AAPL, QQQ, GLD, VIX): NYSE hours only (09:30-16:00 ET, Mon-Fri). Skip
        overnight and weekends for intraday candles (1m, 5m, 1h). Daily candles OK for all trading days.\n  3. TradFi
        futures (ES, ZB, ZN): Near-24hr (Sun 18:00 - Fri 17:00 ET) with 1hr daily break. Weekday only.\n  4. Sports:
        Event-based (candle timestamps correspond to match times, not continuous)\n  Add `market_hours: { start_hour,
        end_hour, timezone, weekdays_only }` config per asset class to the Brownian motion generator.\n",
      status: done,
    }
  - {
      id: a6-p8-defi-health-positions,
      content:
        "- [x] [AGENT] P1. Add DeFi-specific fields to DeFi positions. GAP CATEGORY: Type 2 (strategy-service
        RiskMonitor + risk-service DefiReconciliation compute these — positions don't include them).\n  For positions
        where venue is a DeFi protocol (AAVE_V3, COMPOUND_V3, UNISWAP_V3, LIDO):\n  1. Lending positions: add
        health_factor (1.2-3.0), ltv_ratio (0.3-0.7), liquidation_price, collateral_value_usd, borrow_value_usd\n  2. LP
        positions: add il_pct (impermanent loss 0-5%), pool_share_pct, fee_accrued_usd\n  3. Staking positions: add
        staking_apy (3-8%), rewards_accrued\n  Make 1-2 positions with health_factor close to 1.5 (yellow warning) for
        demo visual impact.\n",
      status: done,
    }
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-pm/plans/archive/CITADEL_VISION_2026_03_22.md` — system-wide vision
2. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — see exact per-page API hooks and what data each page
   expects
3. Read `unified-trading-system-ui/lib/trading-data.ts` (770L) — the client-side data you're replacing. Seed data MUST
   match this closely.

## KEY CONSTRAINT: Registry-Driven, Not Hardcoded

ALL seed data generators must import from UAC `representative_sample.py` for instruments and from codex strategy
archetypes for strategies. If a new instrument or strategy archetype is added to the registry, `POST /admin/reset` must
pick it up automatically — no seed.py code change required.

**Instrument SSOT:** `unified_api_contracts.registry.representative_sample` — import all spec lists **Strategy
archetypes SSOT:** `unified-trading-pm/codex/09-strategy/` — 13 code-complete + 4 documented **Strategy configs:**
Generated by combining archetypes x asset classes x modes. Config, not code.

## KEY CONSTRAINT: Visual Parity for Original 18 Strategies

The Dashboard currently uses `lib/trading-data.ts` which generates 18 strategies. The ORIGINAL 18 must be preserved with
the same IDs, names, asset classes, and similar PnL ranges — so the Dashboard migration (Phase 4) is invisible. The NEW
32+ strategies are additions that expand coverage. Cross-reference `lib/strategy-registry.ts` and `lib/taxonomy.ts`.

## KEY CONSTRAINT: No Two Sources of Truth

After this agent's work, `lib/trading-data.ts` (770L), `lib/strategy-registry.ts`, `lib/ml-mock-data.ts`,
`lib/execution-platform-mock-data.ts`, `lib/data-service-mock-data.ts`, `lib/strategy-platform-mock-data.ts` — ALL of
these client-side data sources become dead code. The UI calls the API. The API reads from MockStateStore. The seed data
is the single source. Phase 4 (MSW removal + trading-data.ts migration) deletes the client-side copies.

## Absorbed from prior plans

- mock_data_rollout_2026_03_18: Mock data enhancement (46% done)
- plan_c_domain_data_api: Mock provider completeness
- plan_d_testnet_stress_testing: Seed hardening, scenario infrastructure
- production_mock_e2e_plan_d90c8f20: Mock E2E testing

## Risk Factors & Mitigations

**RISK 1 (HIGHEST): Visual parity is subjective and hard to verify automatically.** trading-data.ts generates data with
seeded random. Seed data in the API will have different values. The Dashboard may look "different enough" that
stakeholders notice. MITIGATION: Read trading-data.ts FIRST. Extract the EXACT strategy names, org names, and
approximate PnL ranges. Hardcode these in seed.py (not random). For time-series, use similar growth patterns. After
seeding, manually compare Dashboard screenshots (old vs new) before marking done.

**RISK 2: seed.py becomes enormous (8,000 candles + 3,240 PnL points + all domains).** Startup will be slow. File will
be unreadable. MITIGATION: Split seed.py into domain-specific modules:

- `seed_strategies.py`, `seed_positions.py`, `seed_candles.py`, `seed_timeseries.py`
- `seed.py` orchestrates: `seed_all_domains()` calls each module
- Candle generation should be PROCEDURAL (Brownian motion function, not hardcoded arrays)
- A Brownian motion generator for 8,000 candles is ~50 lines, not 8,000 lines

**RISK 3: Collection naming mismatch with Agent 5.** If Agent 6 seeds into `positions` but Agent 5 reads from
`positions_live`, data is invisible. MITIGATION: Use EXACT names from CITADEL_VISION § Interface Contracts. Seed into
`positions_live` and `positions_batch`, NOT just `positions`.

**RISK 4: MSW removal breaks UI build — scattered import references.** Removing lib/mocks/ is not just deleting files.
Other files import from it:

- app initialization calls `startMockWorker()`
- Test files may import MSW handlers
- Components may conditionally import MSW MITIGATION: After deleting lib/mocks/, run
  `grep -r "mocks" --include="*.ts" --include="*.tsx" app/ lib/ hooks/ components/` to find all remaining references.
  Fix each one. Then run `npx next build` to verify.

**RISK 5: Dashboard migration (trading-data.ts → API) is a high-visibility change.** The Dashboard is the first thing
users see after login. If it breaks or looks different, the entire demo is compromised. MITIGATION: Do this LAST (after
all other seed data is solid). Keep trading-data.ts imports as fallback until API hooks return equivalent data. Remove
trading-data.ts only after visual verification.

## Current seed data (what exists)

- orders: 4 records (need 20+)
- fills: 3 records (need 30+)
- execution_venues: 5 records (good)
- algos: 4 records (good)
- backtests: partial (need 8+)

## UI client-side data to replace

- `lib/trading-data.ts` (770 lines) — generates 18 strategies, org/client hierarchy, PnL time series
- `lib/strategy-registry.ts` — canonical strategy definitions
- `lib/ml-mock-data.ts` — ML mock data
- `lib/execution-platform-mock-data.ts` — execution mock data
- `lib/data-service-mock-data.ts` — data service mock data
- `lib/strategy-platform-mock-data.ts` — strategy mock data

## Key constraint

- Seed data MUST match the UI's current client-side data closely enough that the Dashboard looks the same after
  migration. Same strategy names, similar PnL ranges, same org names.

## Tier 0 (UI offline mock) alignment

- SSOT: `CITADEL_VISION_2026_03_22.md` § **Runtime convergence tiers**. When the UI runs **without**
  `unified-trading-api`, it still needs **the same shapes** the gateway would return. Where practical, export
  **versioned JSON** (or reuse `generate_ui_reference_data.py` outputs) from the same seed definitions this plan owns,
  so Tier 0 in-memory state can hydrate from artifacts that stay in lockstep with `MockStateStore` / `seed.py`.

## Cross-domain consistency rules (added 2026-03-22)

These rules ensure the demo doesn't have embarrassing data inconsistencies:

- If BTC candles show a 5% rally on March 15, the BTC-momentum strategy PnL must show a corresponding positive day
- If a position references strategy "alpha-btc-momentum", that strategy must exist in strategies collection
- If an order shows as "filled", there must be corresponding fill records
- Batch data must look like "yesterday's version" of live data, not completely unrelated numbers
- validate_consistency() function enforces all of this automatically

## New scope (added 2026-03-22 gap analysis)

- PnL time-series: 180 daily data points per strategy — now 50+ strategies = 9,000+ data points
- OHLCV candles: ALL instruments from representative_sample.py (~40) × 4 intervals × 200 candles = ~32,000 records
- Ticker seeds: ALL instruments with realistic prices — starting point for WebSocket ticks
- Batch/live collection separation with JSONL persistence to .local-dev-cache/
- All collections need both `_live` and `_batch` variants

## Phase 7 scope (full registry coverage — gap-closing)

- **Full instrument coverage** (P0): Use ALL instruments from UAC representative_sample.py. Import programmatically.
- **50+ strategy expansion** (P0): Combinatorial matrix from CITADEL_VISION. Config-driven, not code-path-driven.
- **Run sync pipeline** (P0): generate_ui_reference_data.py, validate-strategy-manifest.py,
  check-strategy-instruments.py
- **Cross-layer alignment** (P0): Codex → UAC → UIC → API seed → UI registry → PM manifest all consistent.

## Phase 8: Service-Capability Seed Data (READ GAP_CLASSIFICATION_2026_03_22.md)

These seed collections replicate what real services would produce:

- **risk_limits** — from risk-and-exposure-service RiskLimitsDomainClient. Per-strategy limits for pre-trade checks.
- **options_chain** — from features-volatility-service Greeks computation + Deribit data. Black-Scholes Greeks per
  contract.
- **vol_surfaces** — from features-volatility-service vol surface calculators. ATM IV, skew, term structure.
- **var_metrics / stress_test_results / correlation_matrix** — from risk-and-exposure-service VaR/stress/correlation
  calculators. IMPORT FORMAT from `risk-and-exposure-service/scripts/seed_mock_data.py`.
- **fx_rates** — genuinely missing (Type 1). Simple static rates. Also add denomination_currency to positions.
- **regulatory_reports** — from execution-service MiFID II/FCA compliance reporter. Seeded report records.
- **Market hours** — TradFi candles must respect NYSE/CME trading sessions.
- **DeFi health** — health_factor, ltv_ratio on DeFi positions from strategy-service RiskMonitor.

Key principle: seed data shapes MUST match the real service output shapes. When in doubt, read the real service's
seed_mock_data.py or mock_data_provider.py to understand the expected format.

## Sync pipeline scripts (MUST run after expansion)

- `python unified-trading-pm/scripts/openapi/generate_ui_reference_data.py` — sync UAC → UI reference data
- `python unified-trading-pm/scripts/validation/validate-strategy-manifest.py` — validate strategy manifest
- `python unified-trading-pm/scripts/manifest/check-strategy-instruments.py` — verify instrument refs
- `python unified-trading-pm/scripts/checkers/check_ui_api_flow_coverage.py` — verify UI→API coverage
