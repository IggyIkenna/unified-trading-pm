---
type: analysis
title: Global Ledger Architecture Audit — strategy-service
epic: global_ledger_pnl_attribution_master
auditor: slot-7 (ikenna)
date: "2026-05-23"
status: in-progress
source:
  - plans/active/global_ledger_pnl_attribution_discovery_2026_05_21.md
  - strategy-service source (read-only)
scope: Phase 1 audit — derived ledger state in strategy-service
---

# Global Ledger Audit — strategy-service (2026-05-23)

## Audit scope + method

Exhaustive read-only source walk of:

- `strategy_service/position/` (all submodules)
- `strategy_service/pnl/` (all submodules)
- `strategy_service/risk/` (all submodules)
- `strategy_service/portfolio_allocator/emitter.py`
- `strategy_service/supervisor/mark_price_aggregator.py`

No code was modified. All findings are observational.

---

## Position tracking — current state

### Core state machine: `PositionTracker`

**File**: `strategy_service/position/core/position_tracker.py`

State maintained:

- `_cache: dict[tuple[client_id, strategy_id, venue, account_id, instrument], Position]` — write-through in-memory cache
- `PositionStore` (SQLAlchemy + SQLite via `position/storage/database.py`) — durable persistence per (client_id,
  strategy_id, venue, account_id, instrument)

`Position` model fields (from `position/models.py`):

- `quantity` (signed Decimal, net long/short)
- `avg_price` (VWAP of contributing fills)
- `realized_pnl` (closed P&L from SELL fills only)
- `unrealized_pnl` (STORED as Decimal, but set to 0 at fill time — requires mark price update to be meaningful)
- `position_value` (quantity × current_price; stored but not continuously updated)
- `fill_count` (audit counter)
- `archetype_id`, `strategy_leg_id`, `trade_id` (attribution lineage)
- `share_class` (USDT/ETH/BTC denomination)
- `lst_ratio` (weETH/ETH ratio for LST positions)
- `base_asset_equivalent_qty` (ETH-equivalent quantity for LST positions)

**Reconstruction on restart**: Positions are reloaded from SQLite via `_get_or_create_position()` which queries
`PositionStore.get_position()` on cache miss. The `StartupOrchestrator` + `StartupReconciler` runs a full position
reconciliation pass before emitting `STARTED`, comparing internal fill-derived state against exchange REST API. Critical
discrepancies are logged but do NOT block startup (soft-fail).

**Event drivers (what triggers position updates)**:

- `FillEventConsumer` subscribes to PubSub topic `{fill_events_pubsub_topic}-sub`
- Pulls in batches of up to 10 messages, 5s timeout, 100ms sleep between batches
- Cross-client isolation: `assert_client_allowed()` enforced at ingress before any state mutation
- Sports fills routed to `SportsPositionTracker` (back/lay semantics); all other fills to `PositionTracker`

**Fill application logic** (`apply_fill_to_position`):

- BUY: quantity += fill_qty; avg_price = VWAP update
- SELL: realized_pnl += (fill_price − avg_price) × fill_qty; quantity −= fill_qty
- Fee tracking: stored in `FillDB` but NOT deducted from `realized_pnl` in `PositionTracker.apply_fill_to_position()` —
  fees are separate audit trail only

### Cross-venue aggregation: `CrossVenueAggregator`

**File**: `strategy_service/position/core/cross_venue_aggregator.py`

- Maintains `_state: dict[instrument_id, _InstrumentState]` where `_InstrumentState.venues` is `dict[venue, VenueData]`
- On each `update_venue_position()`: rebuilds `AggregatedPosition` with:
  - `net_quantity` = signed sum across all venues
  - `gross_quantity` = absolute sum across all venues
  - `weighted_avg_entry_price` = gross-weighted VWAP
  - `total_unrealized_pnl` = sum of per-venue `unrealized_pnl`
  - `per_venue: list[VenuePositionBreakdown]`
- Delegates gross/net exposure math to `CrossAssetPortfolioAggregator` (from UAC internal)
- `build_portfolio_view()` constructs a `PortfolioView` with:
  - `total_equity_usd` = sum of balance totals
  - `total_unrealized_pnl` / `total_realized_pnl` from positions
  - `gross_exposure` / `net_exposure` from portfolio aggregator
  - `asset_group_exposures`, `strategy_exposures` breakdowns
  - Attaches `PortfolioGreeksSnapshot` and `PortfolioPnLAttribution` if passed by caller

### DeFi-specific position aggregators

**`DeFiLPAggregator`** (`position/core/defi_lp_aggregator.py`):

- Input: `list[DeFiLPPosition]` (from UAC internal)
- Output: `DeFiLPAggregatedMetrics` with `total_lp_value_usd`, `total_fees_earned_usd`, `total_impermanent_loss_usd`,
  per-protocol breakdown
- Groups by protocol (Uniswap, Curve, Balancer, etc.)

**`GreeksAggregator`** (`position/core/greeks_aggregator.py`):

- Input: `list[tuple[instrument_id, underlying, delta, gamma, theta, vega, rho]]`
- Output: `PortfolioGreeksSnapshot` with per-underlying breakdowns
- Groups by `underlying`, sums within-group (correlation=1 assumption within underlying)

**`PnLAttributionAggregator`** (`position/core/pnl_attribution_aggregator.py`):

- Input: `list[dict[str, Decimal]]` (per-position attribution dicts), `list[AggregatedPosition]`
- Output: `PortfolioPnLAttribution` summing 11 dimensions: delta, gamma, theta, vega, rho, funding, basis,
  interest_rate, carry, fx, residual
- Groups `total_unrealized_pnl` by `asset_group` and by `strategy_id` (composite `client_id:account_id:strategy_id` key)

**`SportsPositionTracker`** (`position/core/sports_position_tracker.py`):

- Separate in-memory state for sports positions: `dict[fixture_id:market_type:selection, SportsPosition]`
- Tracks `total_backed`, `total_laid`, `avg_back_odds`, `avg_lay_odds`
- Derives `potential_pnl_if_wins`, `potential_pnl_if_loses` from current position
- NOT persisted to SQLite (in-memory only — gap vs canonical fill-based tracker)

**`TransferReconciler`** (`position/core/transfer_reconciler.py`):

- Reconciles execution-service transfer records against Alchemy on-chain data
- Tracks `_known_tx_hashes`, detects unexpected inflows/outflows
- Emits `TRANSFER_RECONCILIATION_MISMATCH`, `BALANCE_DISCREPANCY_DETECTED`

### Mark prices: `MarkPriceAggregator`

**File**: `strategy_service/supervisor/mark_price_aggregator.py`

- Lives in the **supervisor** process (one per archetype/shard), not in client workers
- Subscribes to MTDS/MDPS mark-price stream and writes into named shared memory
- ClientWorker subprocesses open shared memory read-only (zero-copy)
- Layout: 32 bytes/slot — price (float64), mtm_value_per_unit (float64), timestamp (int64 ms), stale_after_ms (int32),
  valid flag (uint8)
- **Mark prices are NOT integrated back into `PositionTracker.unrealized_pnl`** — this is a critical gap (see below)

### v2 rework: position/v2/

**Files**: `records.py`, `attribution.py`, `projections.py`, `invariants.py`, `recon_freshness.py`

Status: In-progress v2 engine, not yet the operational path for live fills.

- `V2Fill` / `AttributedFill` records — richer than v1; carries `instruction_id`, `fees_asset/amount`, `child_venue_id`
  (for meta-broker sports venues), `chain`
- `FillAttributor` — indexes `instruction_id → StrategyInstanceIdentity` (from UAC internal); matches fills back to
  archetype, family, config_hash, share_class
- `DualProjection` — maintains two consistent views simultaneously:
  - `StrategyProjection`: keyed by `strategy_instance_id`, shows net position per (instrument, asset) + running fees
  - `VenueAccountProjection`: keyed by `(venue, account_id)`, aggregates positions across strategies
- `SumEqualityInvariantChecker` — validates strategy-sum == venue-account-sum per (venue, account, instrument, asset),
  tolerance 1e-9; emits `DriftEvent` on breach
- `ReconFreshnessFeed` — in-memory publish/subscribe feed broadcasting recon completion timestamps to risk-service Layer
  2 preflight (staleness gate)

**v2 is not wired to production fill ingestion yet.** The operational path is v1 (`FillEventConsumer` →
`PositionTracker`).

---

## PnL computation — current state

### Primary orchestrator: `compute_pnl()`

**File**: `strategy_service/pnl/engine/orchestrator.py`

Entry point: `async compute_pnl(date, fills, categories, ...)` → `list[PnLBreakdown]`

**Data sources**:

1. **Fills**: passed as `list[dict]` by the adapter layer (from execution-service fills stored in GCS:
   `execution/by_date/day={date}/fills.parquet`)
2. **Aave liquidity index**: read from features-onchain GCS:
   `by_date/day={date}/feature_group=lending_rates/features.parquet` — columns `instrument_id`, `aave_liquidity_index`
3. **Aave rate impact (projected APYs)**: read from features-onchain GCS:
   `by_date/day={date}/feature_group=aave_rate_impact/features.parquet` — columns `symbol`, `projected_supply_apy`,
   `apy_base_supply`

**Routing logic**:

- Empty fills → `_compute_hold_day_pnl()` — searches backwards up to 7 days for last fill from
  `execution/by_date/day={prev}/fills.parquet`, computes daily interest = position × (index_eod/index_sod − 1)
- `categories=["sports"]` → `process_sports_settlements()` → `SportsPnLEngine`
- Otherwise → `aggregate_fills_to_pnl_inputs()` → per-instrument `compute_pnl_breakdown()`

**Per-instrument failure isolation**: `ValueError, TypeError, KeyError, AttributeError` caught per instrument; loop
continues. `RuntimeError` propagates (fails shard).

### Breakdown computation: `compute_pnl_breakdown()`

**File**: `strategy_service/pnl/engine/breakdown.py`

Output: `PnLBreakdown` with:

- `realized_pnl` (from fill aggregation: SELL fills × (fill_price − avg_entry))
- `unrealized_pnl` (mark-to-market; caller-provided; not computed here)
- `delta_pnl` (optional; caller-provided)
- `basis_pnl` (optional; caller-provided)
- `funding_rate_pnl` (from fill records)
- `interest_rate_pnl` (from Aave liquidity index growth × deployed capital)
- `greeks_delta_pnl`, `greeks_gamma_pnl`, `greeks_theta_pnl`, `greeks_vega_pnl` (from `GreeksExposure` if provided)
- `gas_cost_usd` (from execution fill records)
- `slippage_bps` (from execution fill records)
- `residual_pnl` = mark_to_market − attributed_components (designed to approach zero)
- `share_class_pnl`, `fx_attribution_pnl`, `lst_yield_pnl` (for LST/cross-currency positions)
- DeFi reward factors: `STAKING_YIELD`, `RESTAKING_REWARD`, `SEASONAL_REWARD`, `REWARD_UNREALISED`, `LST_RATIO_YIELD`

**Client isolation**: `assert_client_allowed(client_id)` enforced at function ingress before any computation.

### Archetype-level aggregation: `archetype_aggregator`

**File**: `strategy_service/pnl/engine/archetype_aggregator.py`

- Parses `strategy_id` (or `slot_label`) using slot-label-prefix convention `<ARCHETYPE>@<descriptor>`
- Groups per-strategy PnL DataFrame by `(archetype, config_variant)`
- Writes one parquet per archetype to GCS:
  `by_strategy/{archetype}/config_variant={cv}/year={Y}/month={M}/{date}.parquet`
- Required output columns: `timestamp`, `archetype`, `config_variant`, `strategy_id`, `simulated_pnl_usd`
- **Temporary state**: archetype/config_variant columns parsed from slot labels until execution-service emits them
  natively

### PnL reconciliation: `PnLReconciliationEngine`

**File**: `strategy_service/position/core/pnl_reconciliation_engine.py`

- Compares attributed PnL component sum vs exchange-reported unrealized PnL
- `unexplained_pnl = exchange_pnl − sum(components)` — goal is to drive this to zero
- Currently: `_get_components()` returns `{}` by default (no component provider wired) → ALL PnL is unexplained
- Thresholds: configurable `critical_discrepancy_pct/value` and `discrepancy_threshold_pct/value`
- Emits `UNEXPLAINED_PNL_RESIDUAL` at WARNING or CRITICAL severity

---

## Risk computation — current state

### `RiskCalculator`

**File**: `strategy_service/risk/core/risk_calculator.py`

Metrics computed:

- `leverage` = total_position_value / account_equity
- `margin_usage` = total_position_value / account_equity (same formula as leverage)
- `concentration` = max_instrument_position_value / account_equity
- `drawdown` = (peak_equity − current_equity) / peak_equity (per-client, in-memory peak tracking)
- `cash_balance` = account_equity − total_position_value
- `leverage_status`, `concentration_status`, `drawdown_status` (OK/WARNING/CRITICAL per config thresholds)

**Account equity estimation**: `total_position_value / max_leverage + unrealized_pnl` (estimated from positions — actual
margin balance NOT read from exchange here).

Data source: `PositionMonitorClient` → queries position-balance-monitor's REST API → returns `list[RiskPosition]` (from
UAC internal).

### `ExposureAggregator`

**File**: `strategy_service/risk/core/exposure_aggregator.py`

- Fetches active positions from `PositionMonitorClient`
- Computes: `gross_exposure`, `net_exposure`, `long_exposure`, `short_exposure`, `by_venue`, `by_instrument`
- Optional `SnapshotSink`: writes `ExposureSummary` to GCS for batch mode
- Emits `EXPOSURE_CALCULATED` event

### `VarCalculator` + `VarAttribution`

**Files**: `strategy_service/risk/core/var_calculator.py`, `var_attribution.py`

VaR methods implemented (pure stdlib, no I/O):

- `historical_var()` — empirical, requires ≥10 observations
- `parametric_var()` — normal distribution, requires ≥30 observations; raises `InsufficientDataError` if insufficient
- `parametric_var_cornish_fisher()` — fat-tail adjusted via skewness/excess kurtosis; requires ≥30 observations
- `cvar()` — historical CVaR (Expected Shortfall)
- `stress_var()` — scenario multiplier × historical VaR (GFC_2008=3.5×, COVID_2020=2.5×,
  CRYPTO_BLACK_THURSDAY_2020=5.0×)
- `stressed_var()` — Cornish-Fisher base × scenario multiplier × regime multiplier (hot-reloadable via
  `set_regime_multiplier()`)

VaR attribution (`var_attribution.py`):

- `compute_component_var()` — marginal VaR per position via covariance-based beta: Component_VaR_i = weight_i × beta_i ×
  portfolio_VaR
- Returns `dict[instrument, Decimal]` (contribution in portfolio VaR units)

**Data sources for VaR**: Returns series are passed IN by the caller. The `VarCalculator` itself has no I/O. The caller
(risk monitor loop) must supply historical returns; how those are sourced from GCS/BQ is not wired in this module.

### Risk v2: `FourLayerGateOrchestrator`

**File**: `strategy_service/risk/v2/orchestrator.py`

- Composes Layer 2 (portfolio risk preflight) + Layer 3 (venue account preflight)
- Layer 2 (`run_layer2_preflight`): checks portfolio context including `recon_last_success_utc` (from
  `ReconFreshnessFeed`)
- Layer 3 (`run_layer3_venue_account_preflight`): checks `VenueCapabilityV2` collateral/margin requirements
- Decision: `REJECTED > DEFERRED > RESIZED > APPROVED` (most restrictive wins)
- Short-circuit: REJECTED at Layer 2 → skip Layer 3 entirely

### Additional risk modules

**`GreeksRisk`** (`risk/core/greeks_risk.py`): Greeks-based risk limits (delta limits, vega limits, etc.)

**`LeverageBreachDetector`** (`risk/core/leverage_breach_detector.py`): Real-time leverage breach detection.

**`CorrelationMatrix`** (`risk/core/correlation_matrix.py`): Portfolio-level correlation computation.

**`MonteCarlVar`** (`risk/core/monte_carlo_var.py`): Monte Carlo VaR (supplements the analytical VaR calculator).

**`RegimeDetector`** (`risk/core/regime_detector.py`): Market regime classification for VaR multiplier selection.

**`PreTradeCheckEngine`** (`risk/core/pre_trade_check_engine.py`): Pre-trade risk checks before order routing.

**`RiskDimensions`** (`risk/core/risk_dimensions/`): Duration, second-order vol, spread, venue-protocol risk dimensions.

**`ReturnsStore`** (`risk/core/returns_store.py`): Historical returns persistence (feeds VaR calculator).

---

## Portfolio allocation — current state

### `AllocationDirectiveEmitter`

**File**: `strategy_service/portfolio_allocator/emitter.py`

- `build_allocation_directive()` produces `AllocationDirective` (UAC internal type)
- Inputs: `client_id`, `allocator_id`, `allocator_archetype`, `total_client_equity`,
  `target_weights: dict[strategy_id, Decimal]`, `share_class_by_strategy`, optional `fx_matrix`
- Per-strategy: computes `target_equity_reporting = total_client_equity × weight`, converts to native share class via
  `fx_matrix.convert_nav()`
- Contains `delta_vs_previous_pct` for each strategy directive
- `AllocationDirectiveEmitter` wraps a `list[AllocationDirective]` with `emit()` / `history()` / `reset()`
- Publish to event bus is caller-owned (the emitter constructs the typed event; it does not write to PubSub itself)

**Guard rails**: `strategy_service/portfolio_allocator/guard_rails.py` — enforces position size limits, concentration
limits before emitting directives.

---

## Gap to derived ledger target

### PositionLedger gap

**Target**: `holdings(t, asset) = Σ delta` — a time-indexed, asset-keyed holdings ledger with complete fill history.

**Current state**:

- `PositionTracker` computes point-in-time net position per `(client_id, strategy_id, venue, account_id, instrument)` —
  this IS the delta summation logic, but stored in SQLite as a running aggregate, NOT as a queryable time series.
- **Time dimension missing**: no `holdings_at(t)` API. SQLite stores only the CURRENT state; fill history is in `FillDB`
  but not indexed as a time-series ledger.
- **Mark price NOT integrated**: `unrealized_pnl` is initialised to 0 at fill time and never updated by
  `PositionTracker`; `MarkPriceAggregator` writes into shared memory but the bridge back to position state is not
  implemented. `CrossVenueAggregator` carries `unrealized_pnl` from caller-provided `VenueData.unrealized_pnl` which is
  passed in as 0 from `PositionTracker._notify_aggregator()`.
- **Fee deduction gap**: fees are stored in `FillDB` but not deducted from `realized_pnl` in `apply_fill_to_position()`.
  Realized PnL in the position store = gross of fees.
- **Sports positions not persisted**: `SportsPositionTracker` is in-memory only; not reconstructable from SQLite on
  restart.
- **Cross-venue rollup exists** via `CrossVenueAggregator` but is produced on-demand, not stored as a ledger.
- **v2 DualProjection** (`position/v2/projections.py`) is closer to the ledger concept: it maintains both strategy-view
  and venue-account-view with invariant checking, but is NOT yet wired to the live fill pipeline.

**Gap summary**: Position state exists as a running aggregate; the global ledger needs it as a queryable, time-indexed,
mark-price-inclusive holdings table. The infrastructure (SQLite store + `FillDB`) is present but not surfaced as a
ledger API.

### PnLLedger gap

**Target**: `realised_pnl = Σ cash_out − Σ fees` — fee-net realized P&L, time-series.

**Current state**:

- `PositionTracker.apply_fill_to_position()` computes `realized_pnl` = (fill_price − avg_price) × sell_qty — gross of
  fees.
- Fees in `FillDB`: stored as `fee` (Decimal) + `fee_currency` per fill — NOT deducted from the position's
  `realized_pnl`.
- `compute_pnl_breakdown()` in the PnL engine computes `gas_cost_usd` and `slippage_bps` but these are attributed
  components, not subtracted from `realized_pnl` stored in the position store.
- `PnLReconciliationEngine`: designed to surface `unexplained_pnl = exchange_pnl − component_sum`, but
  `_get_components()` defaults to `{}` (no component provider wired in production) → all PnL unexplained at present.
- Time series: the PnL engine produces `list[PnLBreakdown]` per date, written to GCS as archetype-bucketed parquets via
  `archetype_aggregator`. This IS a time-series ledger of batch PnL — but it's GCS parquets, not a queryable ledger API.
- The `/api/v1/accounts/{account_id}/pnl-series` endpoint exists but delegates to
  `PositionStore.list_pnl_series_points()` which is not yet implemented (`getattr` check with empty-list fallback →
  always 404 in current code).

**Gap summary**: Gross realized PnL tracked per position. Fee-net P&L not computed. Time-series API (`pnl-series`
endpoint) unimplemented. PnL reconciliation component provider not wired. Batch PnL exists as GCS parquets.

### PnLAttributionLedger gap

**Target**: Decompose Δ(unrealised) into Greeks components per position per period.

**Current state**:

- `compute_pnl_breakdown()` accepts `greeks_exposure: GreeksExposure | None` and computes `greeks_delta_pnl`,
  `greeks_gamma_pnl`, `greeks_theta_pnl`, `greeks_vega_pnl` — BUT this requires the caller to provide the Greeks. In
  `compute_pnl()` (orchestrator), `greeks_exposure=None` is always passed → Greeks PnL components are never computed in
  production batch runs.
- `GreeksAggregator` (`position/core/greeks_aggregator.py`): aggregates per-position Greeks into
  `PortfolioGreeksSnapshot` — but requires caller to provide per-position Greek tuples; no source of these is wired.
- `PnLAttributionAggregator` (`position/core/pnl_attribution_aggregator.py`): aggregates 11 PnL dimensions across
  positions for portfolio-level view — but all inputs come from caller; dimensions default to 0 if caller doesn't
  provide.
- Attribution dimensions with live data paths:
  - `interest_rate_pnl`: LIVE — Aave liquidity index from features-onchain GCS
  - `funding_rate_pnl`: LIVE — from fill records if present
  - `gas_cost_usd`: LIVE — from fill records
  - `slippage_bps`: LIVE — from fill records
- Attribution dimensions not yet sourced:
  - `delta_pnl`: caller passes `None` in orchestrator
  - `basis_pnl`: caller passes `None` in orchestrator
  - `greeks_delta_pnl` through `greeks_vega_pnl`: requires `GreeksExposure` input not yet wired
  - `carry_pnl`, `rho_pnl`: no live data path

**Gap summary**: Attribution framework is built and schema is complete, but most components (delta, basis, Greeks) have
no live data source. Only interest (via Aave index), funding, gas, and slippage are production-grade. Decomposition of
Δ(unrealised) into Greeks requires option model integration not yet present.

### RiskLedger gap

**Target**: Time-indexed risk metrics — VaR, CVaR, exposure, Greeks — per client.

**Current state**:

- `RiskCalculator`: computes leverage, concentration, drawdown, margin_usage — but uses estimated equity (position_value
  / max_leverage) rather than actual exchange-reported margin balance
- `ExposureAggregator`: computes gross/net/long/short exposure with `by_venue` and `by_instrument` breakdowns — can
  persist to GCS via `SnapshotSink` in batch mode
- `VarCalculator`: full suite of VaR methods (historical, parametric, Cornish-Fisher, CVaR, stress VaR) — all
  implemented as pure functions
- `VarAttribution`: component VaR per position implemented
- **Returns series not sourced**: `VarCalculator` requires historical returns series as input; `ReturnsStore`
  (`risk/core/returns_store.py`) exists but how it's populated is not directly audited
- **Time series persistence**: `ExposureAggregator` can write to GCS via sink in batch mode; live-mode writes are not
  persisted
- **Greeks risk**: `GreeksRisk` module exists for Greeks-based limits but inputs require option model
- **Leverage metric gap**: uses estimated account equity rather than actual exchange-reported balance; account_equity =
  total_position_value / max_leverage + unrealized_pnl (circular approximation)

**Gap summary**: VaR math is complete and well-implemented. Exposure aggregation works. The gap is (a) returns series
sourcing for VaR, (b) actual margin balance for leverage, (c) persistent time-series ledger API for risk snapshots, (d)
Greeks-based risk limits requiring option model.

---

## v2/ rework status

### position/v2/

| Module               | Status      | Purpose                                                                         |
| -------------------- | ----------- | ------------------------------------------------------------------------------- |
| `records.py`         | In-progress | `V2Fill` + `AttributedFill` — richer fill schema with instruction_id linkage    |
| `attribution.py`     | In-progress | `FillAttributor` — fill → strategy attribution via instruction_id index         |
| `projections.py`     | In-progress | `DualProjection` — strategy-view + venue-account-view maintained simultaneously |
| `invariants.py`      | In-progress | `SumEqualityInvariantChecker` — validates dual projection consistency           |
| `recon_freshness.py` | In-progress | `ReconFreshnessFeed` — pub/sub feed for Layer 2 preflight staleness gate        |

**Not yet wired to production fill pipeline** (`FillEventConsumer` still routes to v1 `PositionTracker`). v2 is
architecturally superior for the global ledger because:

- `AttributedFill` carries full `StrategyInstanceIdentity` (archetype, family, config_hash, slot_version)
- `DualProjection` provides native strategy-view + venue-account-view with invariant checking
- `SumEqualityInvariantChecker` catches attribution drift at 1e-9 tolerance

### risk/v2/

| Module                 | Status      | Purpose                                                      |
| ---------------------- | ----------- | ------------------------------------------------------------ |
| `orchestrator.py`      | In-progress | `FourLayerGateOrchestrator` — Layer 2 + Layer 3 composition  |
| `preflight.py`         | In-progress | `run_layer2_preflight`, `run_layer3_venue_account_preflight` |
| `greek_model.py`       | In-progress | Greeks model for options risk                                |
| `margin_sim.py`        | In-progress | Margin simulation for Layer 3                                |
| `correlation_cap.py`   | In-progress | Correlation-capped position sizing                           |
| `kill_switch_rules.py` | In-progress | Kill switch rule evaluation                                  |

---

## Key findings summary

| Finding                                                                                                                  | Severity | Location                                                                        |
| ------------------------------------------------------------------------------------------------------------------------ | -------- | ------------------------------------------------------------------------------- |
| `unrealized_pnl` always 0 in `PositionTracker`; mark price from `MarkPriceAggregator` not bridged back to position store | HIGH     | `position/core/position_tracker.py:320` + `supervisor/mark_price_aggregator.py` |
| Fees stored in `FillDB` but NOT deducted from `realized_pnl` in `apply_fill_to_position()` — realized PnL is gross       | HIGH     | `position/core/position_tracker.py:200-211`                                     |
| `PnLReconciliationEngine._get_components()` returns `{}` by default — all exchange PnL is "unexplained"                  | HIGH     | `position/core/pnl_reconciliation_engine.py:163-166`                            |
| `pnl-series` endpoint always returns 404 — `list_pnl_series_points` method not on `PositionStore`                        | HIGH     | `position/api/routes/pnl_series.py:83-86`                                       |
| Greeks exposure (`delta_pnl`, `basis_pnl`) always `None` in production `compute_pnl()` calls                             | MEDIUM   | `pnl/engine/orchestrator.py:514-515`                                            |
| `SportsPositionTracker` in-memory only — not persisted, not reconstructable on restart                                   | MEDIUM   | `position/core/sports_position_tracker.py`                                      |
| Account equity in `RiskCalculator` is an approximation (`position_value/max_leverage`) not actual margin balance         | MEDIUM   | `risk/core/risk_calculator.py:34-43`                                            |
| v2 `DualProjection` + `FillAttributor` not wired to production fill pipeline                                             | INFO     | `position/v2/`                                                                  |
| `margin_usage` == `leverage` in `RiskCalculator` (same formula) — appears to be a placeholder                            | LOW      | `risk/core/risk_calculator.py:129-130`                                          |

---

## Data source map

| Ledger layer            | Source system               | Transport                          | Gap                               |
| ----------------------- | --------------------------- | ---------------------------------- | --------------------------------- |
| Position state          | execution-service fills     | PubSub `fill_events-sub`           | Mark price not integrated         |
| Realized PnL            | Fill accumulation in SQLite | In-process                         | Fee deduction missing             |
| Interest PnL            | features-onchain GCS        | GCS read at `compute_pnl()`        | None (working)                    |
| Funding PnL             | Fill records (fill field)   | Via fills                          | None (working)                    |
| Greeks PnL              | Option model input          | Caller-provided                    | Not sourced                       |
| Delta/basis PnL         | Signal model output         | Caller-provided                    | Not sourced                       |
| VaR                     | Historical returns          | Caller-provided to `VarCalculator` | Returns sourcing path not audited |
| Allocation directives   | Portfolio allocator cadence | PubSub (caller emits)              | None (working)                    |
| Exchange position recon | Exchange REST APIs          | `AccountQueryClient`               | Soft-fail on startup              |
| DeFi LP metrics         | `DeFiLPPosition` inputs     | Caller-provided                    | Not audited here                  |
