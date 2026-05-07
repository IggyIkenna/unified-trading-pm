# Gap Classification: Service vs UI vs Mock — 2026-03-22

## Three Gap Categories

Every missing demo capability falls into exactly ONE of these categories. Agents MUST identify the category BEFORE
writing code, because the fix location differs:

| Category                             | Meaning                                                                                                    | Fix Location                                                                                                 |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Type 1: Service Missing**          | The service doesn't implement the functionality at all                                                     | Add to the real service repo (strategy-service, risk-and-exposure-service, etc.)                             |
| **Type 2: UI Visualization Missing** | Service has it, API may expose it, but UI doesn't show it                                                  | Add UI components + API hooks. If API doesn't proxy it, add gateway endpoint or MockDomainService simulation |
| **Type 3: Not Mockable**             | Service has it, but mock mode can't simulate it because it requires real upstream data or live connections | Add mock simulation in MockDomainService that replicates the service's output shape. Seed realistic data.    |

**Key principle:** Type 2 and Type 3 often co-occur. A feature can be "service has it" but BOTH "UI doesn't show it" AND
"mock mode doesn't simulate it." Fix both: mock the service output in MockDomainService, then wire the UI.

---

## Gap-by-Gap Classification

### GAP A: Pre-Trade Compliance Checks

**Category: Type 2 + Type 3** (Service has it. UI doesn't show it. Mock doesn't simulate it.)

**What exists at service level:**

- `execution-service/engine/live/risk.py` — `PreTradeRiskEngine.check_order()`: position limits, order caps, staleness
- `execution-service/engine/risk/pre_trade_client.py` — `check_pre_trade_risk()`: HTTP call to risk-and-exposure-service
- `risk-and-exposure-service/core/pre_trade_check_engine.py` — `PreTradeCheckEngine`: 6 checks (position limit, exposure
  limit, capital limit, leverage limit, VaR limit, stale price guard)
- `risk-and-exposure-service/api/main.py` — `POST /pre-trade-check` endpoint (LIVE, working)

**What's missing:**

1. **MockDomainService** (Agent 5): No pre-trade check simulation. Need `POST /compliance/pre-trade-check` on
   unified-trading-api that, in mock mode, validates the order against seeded risk_limits in MockStateStore. Check: does
   proposed position + existing positions exceed the strategy's max_position_size? Is leverage within limits? Return
   `{ approved: bool, checks: [{ name, status, limit, current, proposed }] }`.
2. **UI** (Agent 2): ManualTradingPanel must call pre-trade check BEFORE order submission. Show a compliance panel:
   green checkmarks for passing checks, red X for violations. Block submission if any check fails. This is the
   "institutional workflow" moment in the demo.
3. **Seed data** (Agent 6): Must seed `risk_limits` per strategy with realistic values (max_position_usd, max_leverage,
   max_var, max_exposure). Pre-trade check reads these.

**Service files (DO NOT modify — they work):**

- `risk-and-exposure-service/core/pre_trade_check_engine.py` (6 checks)
- `execution-service/engine/live/risk.py` (PreTradeRiskEngine)

---

### GAP B: Options Pricing & Greeks Visualization

**Category: Type 2 + Type 3** (Service has it. UI doesn't show it. Mock doesn't simulate it.)

**What exists at service level:**

- `features-volatility-service/app/calculators/second_order_greeks.py` — SecondOrderGreeksCalculator: vanna, volga,
  charm. Routes between Black-Scholes (equities) and Black-76 (futures/perps options).
- `features-volatility-service/app/calculators/gex_calculator.py` — GEX (gamma exposure) by strike
- `features-volatility-service/app/calculators/tradfi_vol_surface.py` — Full vol surface: ATM IV, 25-delta skew,
  risk-reversal, butterfly, term structure slope/curvature. Uses scipy CubicSpline.
- `features-volatility-service/app/calculators/vol_surface_term_structure.py` — Term structure across 5 expiry buckets
  (7d/30d/60d/90d/180d), delta pillars (10d/25d/ATM/25d/10d), vol regime, VRP
- `features-volatility-service/app/calculators/realized_vol_calculator.py` — Close-to-close, Parkinson, Yang-Zhang,
  vol-of-vol, regime z-score
- `position-balance-monitor-service/core/greeks_aggregator.py` — Portfolio Greeks aggregation
  (delta/gamma/theta/vega/rho by underlying and total)
- `risk-and-exposure-service/core/greeks_risk.py` — Delta-gamma VaR: PnL = delta*dS + 0.5*gamma\*dS^2
- `unified-api-contracts/canonical/domain/derivatives/` — Full schemas: CanonicalOptionsChainEntry,
  NormalizedStrikeCoordinate, VolSurface, VolSmilePoint, ComboQuote
- `strategy-service/engine/strategies/options_ml/options_ml_strategy.py` — 3 prediction types: STRIKE_SELECTION,
  DELTA_CONVERSION, VOLATILITY_COMBO
- `execution-service/engine/handlers/options_handler.py` — OptionsComboHandler for multi-leg execution
- `execution-service/instruments/strike_mapping.py` — StrikeMapper: delta -> real strike resolution

**What's missing:**

1. **MockDomainService** (Agent 5): Need to simulate options data. Add:
   - `GET /derivatives/options-chain?underlying=BTC&venue=deribit` — returns seeded options chain (strikes, expiries,
     bid/ask, Greeks per contract). Mock: generate chain from representative_sample Deribit specs using Black-Scholes
     formula.
   - `GET /derivatives/vol-surface?underlying=BTC` — returns vol surface slices. Mock: generate from realistic ATM IV +
     skew parameters.
   - `GET /derivatives/portfolio-greeks` — returns aggregated portfolio Greeks. Mock: sum from seeded options positions.
2. **Seed data** (Agent 6): Need seeded options positions with per-contract Greeks (delta, gamma, vega, theta). Need
   seeded vol surface data (ATM IV ~45% for BTC, skew ~-5%, term structure upward sloping). Use representative_sample.py
   Deribit options chain config.
3. **UI** (Agent 2 or Agent 7): Need options visualization:
   - Options chain table on Trading Terminal (grouped by expiry, calls left / puts right)
   - Vol surface chart (3D or heatmap: strike x expiry x IV)
   - Portfolio Greeks summary panel on Risk Dashboard (net delta, gamma, vega, theta)
   - Greeks P&L scenario: "if BTC moves +-X%, portfolio PnL = Y" (delta-gamma approximation — can be client-side math
     from the Greeks values the API returns)

**Service files (DO NOT modify):**

- `features-volatility-service/app/calculators/` (all calculators)
- `position-balance-monitor-service/core/greeks_aggregator.py`
- `unified-api-contracts/canonical/domain/derivatives/`

---

### GAP C: Risk Repricing / Stress Scenarios (Interactive)

**Category: Type 2 + Type 3** (Service has it. UI doesn't show it. Mock doesn't simulate it.)

**What exists at service level:**

- `risk-and-exposure-service/core/var_calculator.py` — 6 VaR methods: historical, parametric, Cornish-Fisher, CVaR,
  stress_var (GFC_2008/COVID_2020/CRYPTO_BLACK_THURSDAY), stressed_var with regime multiplier
- `risk-and-exposure-service/core/monte_carlo_var.py` — Monte Carlo VaR (10K simulations)
- `risk-and-exposure-service/core/regime_detector.py` — detect_regime(): normal/stressed/crisis based on volatility,
  correlation, drawdown velocity. suggest_multiplier(): 1.0/1.5/2.5
- `risk-and-exposure-service/core/correlation_matrix.py` — Pearson correlation matrix (pure stdlib)
- `risk-and-exposure-service/core/risk_dimensions/second_order_vol.py` — Volga, vanna, slide
- `risk-and-exposure-service/core/risk_dimensions/duration.py` — Duration, convexity, term structure buckets
- `risk-and-exposure-service/api/main.py` — `GET /risk/var` endpoint (takes returns[], confidence, horizon, scenario)
- `risk-and-exposure-service/scripts/seed_mock_data.py` — 548L deterministic seed with VaR, exposure, stress scenarios
  across CeFi/TradFi/DeFi venues

**What's missing:**

1. **MockDomainService** (Agent 5): Need to replicate risk calculation outputs. Add:
   - `GET /risk/var-summary` — returns pre-computed VaR (historical, parametric, CVaR) per strategy. Mock: seed
     realistic VaR values from risk-and-exposure-service's seed_mock_data.py output format.
   - `GET /risk/stress-test?scenario=GFC_2008` — returns portfolio impact under stress scenario. Mock: multiply current
     PnL by scenario multiplier (3.5x for GFC, 2.5x for COVID, 5.0x for Crypto crash).
   - `GET /risk/correlation-matrix` — returns NxN correlation between strategies. Mock: seed a realistic correlation
     matrix (crypto strategies correlated ~0.6, TradFi lower ~0.3, DeFi/Sports near 0).
2. **Seed data** (Agent 6): Seed VaR metrics, stress test results, correlation matrix. Can import/adapt from
   `risk-and-exposure-service/scripts/seed_mock_data.py` which already generates all of this.
3. **UI** (Agent 7): Risk Dashboard needs:
   - VaR summary panel: historical VaR, parametric VaR, CVaR in a card grid
   - Stress scenario selector: dropdown (GFC/COVID/Crypto crash) → shows repriced portfolio impact
   - Correlation heatmap: NxN strategy correlation matrix (use lightweight heatmap component)
   - Interactive stress slider: "BTC price change: -30% to +30%" → recalculated PnL impact (client-side delta-gamma
     approximation from portfolio Greeks — this is presentation math, OK for UI)

**Service files (DO NOT modify):**

- `risk-and-exposure-service/core/var_calculator.py`
- `risk-and-exposure-service/core/regime_detector.py`
- `risk-and-exposure-service/core/correlation_matrix.py`
- `risk-and-exposure-service/scripts/seed_mock_data.py`

---

### GAP D: Circuit Breaker / Kill Switch / Drain Mode (Operational Actions)

**Category: Type 2 (primarily)** (Service has it. UI plans to show it but simplified. Mock plans exist.)

**What exists at service level:**

- `execution-service/engine/circuit_breaker.py` — 3-state machine (CLOSED -> OPEN -> HALF_OPEN -> CLOSED), per-venue,
  rolling failure window (20 samples), configurable cooldown (300s default), failure rate thresholds (30% = DEGRADED,
  60% = OPEN)
- `execution-service/engine/kill_switch.py` — Durable (persists to /tmp/execution_kill_switch.json), emergency halt with
  optional auto-deactivation timeout
- `execution-service/engine/drain_mode.py` — Graceful deployment pause: in-flight completes, new orders 503'd

**What Agent 5 already plans (a5-p1-operational-actions):**

- `POST /risk/circuit-breaker` — mock: updates strategies collection with circuit_breaker_status
- `POST /risk/kill-switch` — mock: sets kill_switch_active flag
- `POST /analytics/strategies/{id}/scale` — mock: updates position_scale field

**What's actually missing (amendment needed):**

1. The mock implementation is a REASONABLE simplification. The real service has per-venue circuit breakers with rolling
   windows — the mock just needs status toggle + visual state change. This is FINE for demo.
2. **UI gap** (Agent 7): The risk dashboard should show circuit breaker state VISUALLY:
   - Per-strategy status badge: ACTIVE (green) / DEGRADED (yellow) / HALTED (red)
   - Per-venue status: show which venues have open circuit breakers
   - Kill switch: prominent red banner when active ("EMERGENCY HALT — all execution stopped")
   - Drain mode indicator: "Deployment in progress — new orders paused"
   - All action buttons already planned in a7-p0-risk-dashboard — just ensure the visual states are rich

**Verdict:** Agent 5 plan is adequate. Agent 7 needs minor amendment to show per-venue CB state.

---

### GAP E: Execution Algorithm Visualization

**Category: Type 2** (Service has 7 algos. UI shows static comparison table.)

**What exists at service level:**

- `execution-service/algorithms/algorithms.py` — 7 algorithms: TWAP, VWAP, ADAPTIVE_TWAP, ALMGREN_CHRISS,
  HYBRID_OPTIMAL, PASSIVE_AGGRESSIVE_HYBRID, POV_DYNAMIC
- `execution-service/engine/execution/algorithms/twap.py` — Full TWAP: schedule() -> child orders, on_fill() hooks
- Each algo follows ExecutionAlgorithm Protocol: schedule() + on_fill()

**What's missing:**

1. **MockDomainService** (Agent 5): `GET /execution/algos` should return algo metadata with realistic performance
   metrics. Mock: seed algo records with: name, description, avg_slippage_bps, fill_rate, avg_latency_ms,
   supported_venues, supported_order_types. This data exists conceptually in the algo implementations.
2. **Seed data** (Agent 6): Seed 7 algo records matching the real algo names. Include historical performance metrics
   (mock but realistic: TWAP avg slippage 2.3bps, VWAP 1.8bps, etc.).
3. **UI** (Agent 2): The `/services/execution/algos` page should show:
   - Algo comparison table: name, avg slippage, fill rate, latency, supported venues
   - Per-algo detail: description, parameter configuration, venue compatibility
   - NOT interactive algo execution (that's Tier 2 — real service fleet)

**Verdict:** Mostly a data richness gap. Plans are directionally correct, just need richer seed data.

---

### GAP F: MiFID II / FCA Compliance Reporting

**Category: Type 2 + Type 3** (Service has it. UI is a stub. Mock doesn't simulate it.)

**What exists at service level:**

- `execution-service/compliance/mifid_reporter.py` — MiFIDReporter: log_order_submitted_mifid(),
  log_trade_reported_mifid(), best execution checks. Emits structured events.
- `execution-service/compliance/compliance_reporter.py` — ComplianceReporter: jurisdiction-aware (EU_MIFID_II, UK_FCA)

**What's missing:**

1. **MockDomainService** (Agent 5): Need `GET /reporting/regulatory` endpoint that returns seeded regulatory report
   records. Seed: 5-10 sample MiFID II best execution reports, FCA transaction reports. Each record: report_type,
   jurisdiction, status (submitted/pending/overdue), filing_date, instruments_covered.
2. **Seed data** (Agent 6): Seed regulatory report records. Also seed compliance events that mirror the events
   execution-service would emit (ORDER_SUBMITTED_MIFID, TRADE_REPORTED_MIFID).
3. **UI** (Agent 4): `/services/reports/regulatory` is a 24-line stub. Build it with:
   - Regulatory report list table: type (MiFID II / FCA / EMIR), status, filing date, next due
   - Report detail: instruments covered, best execution metrics, filing reference
   - NOT interactive filing (that's real-service only) — just display and export

---

### GAP G: DeFi Position Health & Liquidation Risk

**Category: Type 2** (Service has it. UI doesn't show it.)

**What exists at service level:**

- `strategy-service/engine/core/components/risk_monitor.py` — Aave liquidation checks: health_factor = ltv_max /
  ltv_ratio. Thresholds: hf_min=1.2, ltv_max=0.85
- `risk-and-exposure-service/core/defi_reconciliation.py` — Aave aToken/debt token reconciliation using on-chain
  liquidity index formula
- `unified-defi-execution-interface` — DeFi position management (connect, swap, lend, borrow)

**What's missing:**

1. **Seed data** (Agent 6): DeFi positions should include health_factor, ltv_ratio, liquidation_distance_pct fields. For
   Aave lending positions: collateral_value, borrow_value, health_factor.
2. **UI** (Agent 7 or Agent 2): Positions table (when viewing DeFi positions) should show:
   - Health factor column with color coding (>2.0 green, 1.5-2.0 yellow, <1.5 red)
   - Liquidation price column
   - "Liquidation distance" badge (e.g., "32% to liquidation")
   - This is a column addition to the Positions DataTable, not a new page

---

### GAP H: FX Conversion / Multi-Currency

**Category: Type 1 (Service Missing) + Type 3 (Not Mockable)**

**What exists:** NOTHING. risk-and-exposure-service assumes USD denomination. No FX rate service.

**What's needed:**

1. **Seed data** (Agent 6): Add `fx_rates` collection to MockStateStore with static rates:
   `{ BTC/USD: 67000, ETH/USD: 3500, USDT/USD: 1.0001, EUR/USD: 1.08, GBP/USD: 1.27 }`. Add `denomination_currency`
   field to positions (USDT for Binance, BTC for Deribit, USD for CME/NYSE). Add `fx_rate_to_usd` to each position
   record (so PnL aggregation is correct).
2. **MockDomainService** (Agent 5): When aggregating PnL across positions, apply FX conversion:
   `usd_pnl = position.unrealized_pnl * fx_rate_to_usd`. This is ~5 lines in the PnL aggregation function.
3. **API**: `GET /market-data/fx-rates` — returns current mock FX rates. Simple.
4. **UI**: No new UI needed — PnL values are already displayed in USD. The fix is server-side.

**This is the only Type 1 gap.** The service genuinely doesn't have FX conversion. But the fix is trivial (static FX
rates in mock seed, 5-line conversion in PnL aggregation).

---

### GAP I: Market Hours & Time Zone Awareness

**Category: Type 3** (Service has market-hours-aware logic. Mock candle generator ignores it.)

**What exists at service level:**

- TradFi instruments have market hours (NYSE 09:30-16:00 ET, CME near-24hr with breaks)
- The real market data pipeline respects trading sessions
- features-volatility-service computes vol using market-hours-appropriate windows

**What's missing:**

1. **Seed data** (Agent 6): OHLCV candle generator must respect market hours per asset class:
   - CeFi/DeFi: 24/7 candles (correct as-is)
   - TradFi equities (AAPL, QQQ, GLD, VIX): NYSE hours only (09:30-16:00 ET, Mon-Fri). No candles on weekends or
     overnight. Daily candles OK for all days.
   - TradFi futures (ES, ZB, ZN): Near-24hr with 1hr break (17:00-18:00 ET). Weekday only.
   - Sports: Event-based (candle = match), not continuous Add `market_hours` config per asset class to the Brownian
     motion generator.

---

### GAP J: Signal Vector / Strategy Internals Visualization

**Category: Type 2** (Service has rich signal decomposition. UI shows none of it.)

**What exists at service level:**

- `strategy-service/engine/core/signal_vector/assembler.py` — 5-dimensional signal vector: direction, vol, timing, + 2
  more. Each dimension computed independently.
- Every strategy generates signals with confidence scores, regime awareness, etc.

**What's missing:**

1. **Seed data** (Agent 6): For each strategy, seed recent signal history (last 20 signals with direction, confidence,
   regime, timestamp). Store in `signal_history` collection.
2. **UI** (Agent 3): On strategy detail page (`/services/trading/strategies/[id]`), add:
   - Signal history chart: direction signal over time with confidence bands
   - Current regime indicator: normal/stressed/crisis badge
   - NOT real-time signal generation (Tier 2) — just display seeded signal history

**Verdict:** Nice-to-have for demo. Lower priority than gaps A-C.

---

## Priority Matrix

| Gap                       | Category | Demo Impact                         | Effort | Priority |
| ------------------------- | -------- | ----------------------------------- | ------ | -------- |
| A: Pre-Trade Checks       | Type 2+3 | HIGH — institutional workflow       | 3-4h   | P0       |
| B: Options/Greeks         | Type 2+3 | HIGH — shows derivatives capability | 6-8h   | P0       |
| C: Stress Scenarios       | Type 2+3 | HIGH — BlackRock showstopper        | 4-5h   | P0       |
| H: FX Conversion          | Type 1+3 | HIGH — PnL correctness              | 1-2h   | P0       |
| D: Circuit Breaker Visual | Type 2   | MEDIUM — ops richness               | 1h     | P1       |
| G: DeFi Health Factor     | Type 2   | MEDIUM — DeFi depth                 | 2h     | P1       |
| F: Regulatory Reporting   | Type 2+3 | MEDIUM — compliance story           | 3h     | P1       |
| I: Market Hours           | Type 3   | MEDIUM — TradFi realism             | 1h     | P1       |
| E: Algo Metrics           | Type 2   | LOW — data richness                 | 1h     | P2       |
| J: Signal History         | Type 2   | LOW — strategy depth                | 2h     | P2       |

---

## Which Agent Fixes What

| Gap             | Agent 5 (API)                                                | Agent 6 (Seed)                            | Agent 2 (Trading UI)      | Agent 7 (Risk/Observe UI)                                           | Agent 4 (Reports UI)  |
| --------------- | ------------------------------------------------------------ | ----------------------------------------- | ------------------------- | ------------------------------------------------------------------- | --------------------- |
| A: Pre-Trade    | Add POST /compliance/pre-trade-check                         | Seed risk_limits                          | Wire ManualTradingPanel   | —                                                                   | —                     |
| B: Options      | Add GET /derivatives/\* endpoints                            | Seed options chain + vol surface + Greeks | Options chain on Terminal | Portfolio Greeks on Risk Dashboard                                  | —                     |
| C: Stress       | Add GET /risk/var-summary, /stress-test, /correlation-matrix | Seed VaR + correlation data               | —                         | VaR panel + stress selector + correlation heatmap + scenario slider | —                     |
| D: CB Visual    | Already planned                                              | —                                         | —                         | Amend: per-venue CB state, kill switch banner                       | —                     |
| E: Algo Metrics | Enrich GET /execution/algos response                         | Seed algo performance metrics             | —                         | —                                                                   | —                     |
| F: Regulatory   | Add GET /reporting/regulatory with mock data                 | Seed regulatory report records            | —                         | —                                                                   | Build regulatory page |
| G: DeFi Health  | —                                                            | Add health_factor to DeFi positions       | Show health factor column | —                                                                   | —                     |
| H: FX           | Add GET /market-data/fx-rates, apply in PnL aggregation      | Seed fx_rates + denomination_currency     | —                         | —                                                                   | —                     |
| I: Market Hours | —                                                            | Amend candle generator                    | —                         | —                                                                   | —                     |
| J: Signals      | Add GET /analytics/signal-history                            | Seed signal history                       | —                         | —                                                                   | —                     |
