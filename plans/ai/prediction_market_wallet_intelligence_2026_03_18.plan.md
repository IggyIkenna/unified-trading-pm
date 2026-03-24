# AI-GENERATED — awaiting user review and promotion

---

name: prediction-market-wallet-intelligence overview: | Two-stream prediction market intelligence system. Stream 1:
ingest Polymarket + Kalshi wallet activity, filter by transaction threshold, build P&L profiles for every active wallet,
surface "smart money" wallets for ad hoc analysis. Stream 2: translate binary (YES/NO) prediction market prices into
ML-ingestible features and options-equivalent trading signals. type: mixed epic: epic-code-completion status: blocked
blocked_reason: | Waiting on Polymarket and Kalshi data access (API keys + historical wallet data). Plan is complete and
ready to promote once data feeds are confirmed. completion_gates: code: C5 deployment: D3 business: B6 repo_gates:

- repo: unified-api-contracts code: C0 deployment: none business: none
- repo: unified-market-interface code: C0 deployment: none business: none
- repo: unified-features-interface code: C0 deployment: none business: none
- repo: unified-internal-contracts code: C0 deployment: none business: none
- repo: unified-domain-client code: C0 deployment: none business: none

depends_on: []

todos:

# ── PHASE 0: SCHEMAS ──────────────────────────────────────────────────────

- id: p0-uac-prediction-market-schemas content: |
  - [ ] [AGENT] P0. Add Polymarket + Kalshi market schemas to UAC. `unified_api_contracts/external/polymarket/` and
        `external/kalshi/`. Polymarket models: `PredictionMarketTrade` (includes wallet_address — on-chain, public),
        `WalletPosition`, `MarketResolution`, `MarketSnapshot` (timestamp, yes_price, no_price, volume_24h,
        open_interest). Kalshi models: `KalshiMarketSnapshot`, `KalshiOrderBook`, `KalshiAggTrade` (NO wallet_address or
        user_id — Kalshi is a CFTC-regulated centralized exchange, individual trader activity is private; only aggregate
        market data is accessible). Both implement shared `PredictionMarketABC` protocol for market-level data only.
        Wallet profiling (Stream 1) is Polymarket-ONLY. status: pending note: ""

- id: p0-uic-wallet-pnl-types content: |
  - [ ] [AGENT] P0. Add wallet P&L internal types to UIC. `WalletPnLRecord`: wallet_address, market_id, entry_price,
        exit_price, shares, realized_pnl, unrealized_pnl, trade_count, first_seen_at, last_seen_at. `WalletProfile`:
        wallet_address, total_realized_pnl, total_volume, win_rate, avg_trade_size, active_markets, trailing_30d_pnl,
        trailing_7d_pnl, tier (NOISE/RETAIL/SMART/WHALE). `WalletTier` enum with configurable threshold: default >$10
        cumulative volume = RETAIL floor. `BinaryMarketFeatureVector`: market_id, resolution_time, yes_price,
        implied_prob, price_velocity_1h, price_velocity_6h, volume_spike_z, crowd_consensus_strength. status: pending
        blocked_by: p0-uac-prediction-market-schemas note: ""

# ── PHASE 1: DATA INGESTION ADAPTERS ────────────────────────────────────

- id: p1-umi-polymarket-adapter content: |
  - [ ] [AGENT] P1. Build Polymarket adapter in UMI. Endpoints: CLOB REST API for trade history, websocket feed for live
        prices. Methods: `get_wallet_trades(address, from_ts, to_ts)`, `get_market_trades(market_id, from_ts, to_ts)`,
        `stream_market_prices(market_ids)`. VCR cassettes required for all REST methods. Classify errors via UAC
        `classify_venue_error()`. Emit `ADAPTER_FETCH_FAILED` on failure. Register as `POLYMARKET` in UMI
        VENUE_REGISTRY. status: pending blocked_by: p0-uac-prediction-market-schemas note: "Blocked on Polymarket API
        access"

- id: p1-umi-kalshi-adapter content: |
  - [ ] [AGENT] P1. Build Kalshi adapter in UMI for MARKET-LEVEL data only. Kalshi is a CFTC-regulated centralized
        exchange — individual trader activity is private and not exposed via API. Only aggregate market data is
        available. Methods: `get_market_history(ticker, from_ts, to_ts)`, `get_orderbook(ticker)`,
        `stream_ticker(tickers)`. NO `get_user_trades()` — that only returns your own account data, useless for
        cross-wallet analysis. Kalshi contributes to Stream 2 (binary market features) only, not Stream 1 (wallet
        profiling). VCR cassettes required. Error classification via UAC. Register as `KALSHI` in UMI. status: pending
        blocked_by: p0-uac-prediction-market-schemas note: "Blocked on Kalshi API access. Market-level data only — no
        user profiling possible."

# ── PHASE 2: WALLET P&L PIPELINE ─────────────────────────────────────────

- id: p2-wallet-activity-ingestion content: |
  - [ ] [AGENT] P1. Build wallet activity ingestion job. New service or feature in `unified-features-interface`:
        `prediction_market_wallet_ingestion`. Two modes: BACKFILL: paginate full trade history for all discovered
        wallets (wallet graph seeding) LIVE: subscribe to Polymarket CLOB websocket, extract wallet addresses from each
        trade Filter: discard any wallet with cumulative volume < configurable threshold (default $10 USDC). Store raw
        trades to BigQuery `prediction_markets.wallet_trades` (partitioned by date, clustered by wallet_address). Emit
        `PREDICTION_MARKET_WALLET_TRADE` UEI event on each ingested trade. status: pending blocked_by:
        p1-umi-polymarket-adapter, p1-umi-kalshi-adapter note: ""

- id: p2-wallet-pnl-calculator content: |
  - [ ] [AGENT] P1. Build wallet P&L calculator. Consumes `prediction_markets.wallet_trades`, computes `WalletPnLRecord`
        per market per wallet. P&L accounting: FIFO for partial fills; realized on YES/NO resolution; mark-to-market for
        open positions. Materialized to `prediction_markets.wallet_pnl_daily` (daily snapshot per wallet). Handles:
        splits, resolution payouts ($1.00 YES = win), $0.00 YES = loss. Edge cases: wallets that hold through resolution
        vs those that exit early (alpha signal). status: pending blocked_by: p2-wallet-activity-ingestion note: ""

- id: p2-wallet-profiler content: |
  - [ ] [AGENT] P1. Build wallet profiler that generates `WalletProfile` records. Rolling windows: 7d, 30d, 90d,
        all-time. Scoring dimensions: - Total realized P&L (USD) - Win rate (% of markets resolved profitably) -
        Calibration score (how well their entry prices predicted resolution) - Alpha over naive market (entry price vs
        final market price at T-24h) - Market category specialization (political, sports, crypto, macro) Tier
        assignment: NOISE (<$10 volume), RETAIL ($10–$1k), SMART ($1k–$100k and win_rate > 55%), WHALE (>$100k). Tiers
        are data-driven not hardcoded — recalibrate quarterly. Output: `prediction_markets.wallet_profiles` BigQuery
        table. UEI event: `SMART_WALLET_TIER_CHANGE` when a wallet crosses tier boundaries. status: pending blocked_by:
        p2-wallet-pnl-calculator note: ""

# ── PHASE 3: SMART MONEY DISCOVERY ─────────────────────────────────────

- id: p3-trending-wallet-detector content: |
  - [ ] [AGENT] P1. Build trending wallet detector. "Trending" definition (configurable, all must be true): 1.
        trailing_7d_pnl > $500 2. win_rate_30d > 0.58 3. calibration_score_30d > median + 1 stdev 4. trade_count_30d >=
        10 (not a one-hit wonder) Runs nightly, writes results to `prediction_markets.trending_wallets`. Publishes
        Telegram alert when new wallet enters SMART or WHALE tier. Exposes REST endpoint via `unified-trading-api`
        (/analytics and related routes) for ad hoc querying: GET
        /prediction-markets/wallets?tier=SMART&sort=trailing_7d_pnl&limit=50 status: pending blocked_by:
        p2-wallet-profiler note: ""

- id: p3-wallet-adhoc-analysis-tooling content: |
  - [ ] [HUMAN+AGENT] P2. Build ad hoc wallet analysis tooling. A Jupyter notebook template (not ad hoc script —
        parameterized for reuse): `unified-trading-pm/notebooks/prediction_market_wallet_deep_dive.ipynb` Sections: 1.
        Load wallet profile + full trade history 2. P&L attribution by market category 3. Entry timing analysis (does
        this wallet enter early or late?) 4. Market selection alpha (do markets they enter outperform?) 5. Correlation
        with other tracked smart wallets (cluster analysis) 6. Current open positions with unrealized P&L Pulls from
        BigQuery via UCI DataSource. No hardcoded credentials. status: pending blocked_by: p3-trending-wallet-detector
        note: ""

- id: p3-wallet-position-mirroring-scaffold content: |
  - [ ] [HUMAN+AGENT] P2. Scaffold wallet position mirroring signal generator. NOT an execution system yet — generates
        SIGNAL events only. When a SMART/WHALE wallet opens a new position: - Emit `SMART_WALLET_POSITION_OPENED` event
        with: wallet_tier, market_id, direction (YES/NO), entry_price, wallet_trailing_alpha, market_category Consumer
        (future): strategy-service can subscribe and decide whether to mirror. This keeps mirroring logic decoupled from
        wallet intelligence layer. status: pending blocked_by: p3-trending-wallet-detector note: ""

# ── PHASE 4: BINARY MARKET → ML + OPTIONS TRANSLATION ──────────────────

- id: p4-binary-market-feature-engineering content: |
  - [ ] [AGENT] P0. Build binary market feature engineering for ML. The core translation challenge: YES/NO price ∈ [0,
        1] is an implied probability. Features to extract per market per timestamp: - `implied_prob`: raw YES price
        (market's crowd probability estimate) - `prob_velocity_1h/6h/24h`: dp/dt — how fast is consensus shifting? -
        `prob_momentum`: is velocity accelerating or decelerating? - `volume_weighted_prob`: VWAP of YES trades (vs last
        traded price) - `order_imbalance`: (YES_bid_volume - NO_bid_volume) / total - `time_to_resolution_pct`: elapsed
        time / total market duration (0→1) - `liquidity_depth`: $-depth within 2% of mid for YES and NO -
        `crowd_consensus_strength`: how clustered is the orderbook around current price? -
        `resolution_category_encoding`: one-hot (political/crypto/sports/macro/weather) - `binary_entropy`: -p*log(p) -
        (1-p)*log(1-p) — uncertainty measure Output: `BinaryMarketFeatureVector` → UFI feature store. These features are
        domain-agnostic — any downstream ML model can consume them. status: pending blocked_by:
        p1-umi-polymarket-adapter, p0-uic-wallet-pnl-types note: ""

- id: p4-options-translation-framework content: |
  - [ ] [AGENT] P1. Build binary-market-to-options translation framework. Mathematical foundation: Binary YES contract =
        digital call option (pays $1 if event occurs, $0 otherwise). YES price P_yes = risk-neutral probability
        Q(event). Therefore: P_yes maps directly to delta of a deep-in/out digital option.

        Translations to implement:
          1. `binary_to_digital_option_params(market)` → `DigitalOptionParams`:
               - strike = resolution condition (e.g. "BTC > $100k by Dec 31")
               - current_delta = P_yes (already the risk-neutral prob)
               - implied_vol = derived from time-to-resolution + price uncertainty
               - theta = -∂P_yes/∂t (time decay of probability — markets converge)
          2. `implied_probability_to_bs_delta(p, T, r)` → equivalent BS delta
               for a vanilla option with similar payoff profile
          3. `binary_spread_to_vertical_spread(yes_price, no_price)` →
               equivalent debit/credit spread levels in options terms
          4. `prob_path_to_vol_surface(market_history)` → reconstructed
               implied vol surface from historical binary price paths

        Key insight for ML: binary market prices give you a FORWARD-LOOKING
        crowd probability estimate, which is a strong feature for any model
        predicting the underlying outcome (e.g. BTC price, election winner).
        This is fundamentally different from historical price data.

    status: pending blocked_by: p4-binary-market-feature-engineering note: ""

- id: p4-prediction-market-ml-signal-generator content: |
  - [ ] [AGENT] P1. Build prediction market ML signal generator. Three signal types:

        A. CROWD WISDOM SIGNAL:
           When prediction market implied_prob diverges significantly from
           underlying asset model price (e.g. "BTC > $100k" market at 72% but
           quant model says 45%), flag as CROWD_MODEL_DIVERGENCE signal.
           Actionable: if crowd has historically been right in this category,
           adjust model or enter a position betting on convergence.

        B. LATE-RESOLUTION MOMENTUM SIGNAL:
           In the last 20% of a market's life, prob_velocity typically
           accelerates toward resolution. Detect abnormal early acceleration
           as a leading indicator of information leakage or insider activity.
           Signal: EARLY_RESOLUTION_MOMENTUM.

        C. CROSS-MARKET CORRELATION SIGNAL:
           When two markets that should be correlated (e.g. "BTC > $80k by
           Jan 1" and "ETH > $4k by Jan 1") have diverging implied probs,
           flag as CROSS_MARKET_ARBITRAGE opportunity.

        Each signal → UEI event type, consumed by strategy-service.

    status: pending blocked_by: p4-options-translation-framework note: ""

# ── PHASE 5: VALIDATION & QG ─────────────────────────────────────────────

- id: p5-backtesting-wallet-signals content: |
  - [ ] [HUMAN+AGENT] P2. Backtest wallet mirroring and binary market signals. Use historical Polymarket data (available
        via API back to 2020). Metrics to validate: - Smart wallet signal: does mirroring SMART/WHALE wallets beat
        market? - Calibration: do our ranked wallets actually outperform going forward? - Options translation: do
        reconstructed vol surfaces predict realized vol? - ML signals: are CROWD_MODEL_DIVERGENCE signals profitable
        within 24h? Output: backtesting report in `unified-trading-pm/docs/prediction_markets/`. Must meet B3 gate:
        Sharpe ≥ 0.8 on backtest for at least one signal type. status: pending blocked_by:
        p4-prediction-market-ml-signal-generator, p3-trending-wallet-detector note: ""

- id: p5-quality-gates-sweep content: |
  - [ ] [AGENT] P0. Run quality gates across all modified repos. cd unified-api-contracts && bash
        scripts/quality-gates.sh cd unified-market-interface && bash scripts/quality-gates.sh cd
        unified-features-interface && bash scripts/quality-gates.sh cd unified-internal-contracts && bash
        scripts/quality-gates.sh cd unified-domain-client && bash scripts/quality-gates.sh All must pass before
        promotion to active plan. status: pending blocked_by: p4-prediction-market-ml-signal-generator note: ""

isProject: false

---

# Prediction Market Wallet Intelligence

**Status: BLOCKED** — Waiting on Polymarket + Kalshi data access. Promote to `plans/active/` when API keys confirmed.

## Overview

Two independent but synergistic streams:

**Stream 1 — Smart Wallet Profiler:** Ingest every wallet transaction from Polymarket (on-chain CLOB) and Kalshi
(regulated US exchange). Filter out noise (<$10 cumulative volume threshold, configurable). Build rolling P&L, win-rate,
and calibration scores per wallet. Identify "smart money" wallets. Surface them for ad hoc deep-dive analysis and
eventually as mirroring signals into the strategy layer.

**Stream 2 — Binary Market → ML + Options:** Prediction market YES/NO prices are risk-neutral probabilities. This stream
extracts rich feature vectors from binary markets (velocity, entropy, imbalance, time decay) and provides the
mathematical translation layer to options-equivalent constructs — enabling both ML model enrichment and options position
sizing based on crowd-derived probability estimates.

---

## Architecture

```
Polymarket CLOB API          Kalshi REST v2
       │                           │
       ▼                           ▼
  UMI Polymarket Adapter    UMI Kalshi Adapter
       │                           │
       └──────────┬────────────────┘
                  ▼
     Wallet Activity Ingestion Job
     (filter: volume > $10 threshold)
                  │
          BigQuery: wallet_trades
                  │
         ┌────────┴────────┐
         ▼                 ▼
   Wallet P&L         Binary Market
   Calculator         Feature Extractor
         │                 │
   wallet_pnl_daily   UFI Feature Store
         │                 │
   Wallet Profiler    Options Translation
   (tier: NOISE→      Framework
    RETAIL→SMART→          │
    WHALE)            ML Signal Generator
         │                 │
   Trending Wallet    CROWD_WISDOM_SIGNAL
   Detector           EARLY_MOMENTUM_SIGNAL
         │             CROSS_MARKET_ARB
         │                 │
         └────────┬─────────┘
                  ▼
           strategy-service
           (UEI event consumers)
```

---

## Stream 1: Wallet P&L Profiling — Key Design Decisions

### Threshold Design

The `>$10` filter is a starting default. The real filter is multi-dimensional:

- **Minimum cumulative volume**: $10 (avoids one-cent test wallets)
- **Minimum trade count**: 3 (avoids lucky single-trade wallets)
- **Recency**: active within last 90 days (wallets that stopped trading 2 years ago aren't useful)

These are all configurable constants in UCI/UnifiedCloudConfig — not hardcoded.

### P&L Accounting Model

Polymarket uses USDC. Every YES contract purchased = cost basis. If market resolves YES, payout = $1.00 per share. P&L =
(1.00 − entry_price) × shares. If exits early, P&L = (exit_price − entry_price) × shares.

Edge case: wallets that consistently buy when P < 0.20 and hold to resolution have a fundamentally different risk
profile than wallets that scalp momentum. The profiler distinguishes these via a `trading_style` field (CONTRARIAN /
MOMENTUM / VALUE / LIQUIDITY_PROVIDER).

### "Good Trending Wallet" Criteria (from user requirement)

Not just highest total P&L (whales can brute-force size). Quality criteria:

1. Alpha over naive buy-and-hold the market (did they call it earlier than the crowd?)
2. Consistency across multiple markets, not one big win
3. Category specialization score (are they systematically good at crypto markets? political?)
4. Non-correlation with other smart wallets (diversified signal, not a pack)

---

## Stream 2: Binary → ML + Options — Key Design Decisions

### Why Binary Markets are Unusual ML Features

Traditional ML features are backward-looking (price at T-1, volume at T-7, etc.). Prediction market prices are
**forward-looking crowd consensus** — they aggregate dispersed private information. A `implied_prob = 0.73` for "BTC >
$100k by Dec 31" represents what a diverse group of financially-motivated participants collectively believes, updated in
real-time.

This is qualitatively different from a model price. The combination of model price vs market-implied price (the "wedge")
is where the alpha lives.

### Binary Market as Digital Option

```
YES contract = Binary Call Option
  Underlying: event occurrence (0 or 1)
  Strike: resolution condition
  Expiry: resolution date
  Price: P_yes ∈ [0, 1] = risk-neutral Q(event)
  Payoff: $1 if event, $0 otherwise

Relationship to vanilla options:
  For "Asset X > K at time T":
    P_yes ≈ N(d2) in Black-Scholes
    where d2 = (ln(S/K) + (r - σ²/2)T) / (σ√T)

  This means: given P_yes, T, r, and S — we can BACK-SOLVE for implied σ.
  This is the crowd's implied volatility for the underlying.
```

### Options Trading Application

When a prediction market gives `P("BTC > $100k by Dec 31") = 0.72`:

1. Back-solve to implied vol σ_crowd
2. Compare σ_crowd to options market IV for same strike/expiry
3. If σ_crowd > σ_options: market underpricing the probability → buy calls
4. If σ_crowd < σ_options: market overpricing the probability → sell calls / buy puts

This is a **cross-market arbitrage** between prediction markets and derivatives markets. The signal generator (Phase 4)
automates this detection.

---

## Data Sources & Access Requirements

| Source                     | Type             | What's accessible                                         | Blocker                          |
| -------------------------- | ---------------- | --------------------------------------------------------- | -------------------------------- |
| Polymarket CLOB            | REST + WebSocket | All trades with wallet addresses (on-chain, fully public) | None                             |
| Polymarket wallet history  | REST             | Any wallet's full trade history                           | None — on-chain                  |
| Kalshi market data         | REST v2          | Prices, order books, aggregate volume only                | Account (for higher rate limits) |
| Kalshi user trades         | REST v2          | **Your account only** — no other users visible            | N/A — not useful for profiling   |
| Historical Polymarket data | REST paginated   | Full history back to 2020                                 | Rate limits only                 |

**Key asymmetry:**

- **Polymarket** = on-chain (Polygon). Every trade, every wallet, every position is a public blockchain transaction.
  Full wallet profiling is possible with zero special access.
- **Kalshi** = centralized regulated exchange (like a brokerage). User data is private. You can see market prices and
  aggregate liquidity but never who is on the other side of a trade.

Stream 1 (wallet profiling) is **Polymarket-only**. Kalshi is useful only for Stream 2 (binary market ML features).

---

## Success Criteria

| Gate | Criterion                                                          |
| ---- | ------------------------------------------------------------------ |
| C4   | All repos pass quality-gates.sh                                    |
| C5   | All merged to staging/main                                         |
| D3   | Live Polymarket + Kalshi data flowing to BigQuery in staging       |
| B3   | ≥1 signal type achieves Sharpe ≥ 0.8 in backtesting                |
| B6   | User confirms smart wallet shortlist is useful for ad hoc analysis |

---

## Related Plans

- `strategy_system_citadel_master_2026_03_15.plan.md` — strategy-service that will consume signals
- `elysium_defi_presentation_2026_03_10.plan.md` — DeFi pipeline (Polymarket is on-chain, shares infra)
- Future: dedicated ML training plan for binary market → asset price prediction model
