## Scenario `borrow_rate_spike` — Borrow APR explodes (CeFi margin OR DeFi lending pool)

| Field                | Value                                                                                                                                                                                                                                                                                                                                                           |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario_id`        | `borrow_rate_spike`                                                                                                                                                                                                                                                                                                                                             |
| Category             | `FUNDING_COST_SHOCK` (primary — per-block / per-interval borrow APR jumps multi-x baseline) + `UTILIZATION_KINK_CROSSING` (DeFi variant — pool crosses optimal-utilization kink and slope-2 borrow rate kicks in) + `LENDER_RECALL` (CeFi variant — venue raises tiered margin rate or recalls open margin loans)                                               |
| Layer                | `RAW_TICK` primary (Aave / Compound / Spark `getReserveData.currentVariableBorrowRate` per block on DeFi side; CeFi venue tiered-margin-rate API endpoint per minute) + `FEATURE` secondary (rolling carry-PnL feature — funding-arb's expected-carry feature reverses sign when borrow rate exceeds receive-rate)                                              |
| Asset groups         | `frozenset({MarketAssetGroup.DEFI, MarketAssetGroup.CEFI})`                                                                                                                                                                                                                                                                                                     |
| Applies-to           | **DeFi variant** per-(chain, protocol, asset): Aave V3 / Spark / Morpho / Compound V3 on Ethereum + Arbitrum + Base + OP; assets `WETH / USDC / USDT / DAI / WSTETH / WEETH / RETH / rsETH`. **CeFi variant** per-(venue, asset): bybit / binance / okx / deribit margin-borrow on USDT / USDC / BTC / ETH; closed-set per UAC `_cefi.py` + `_margin_rates.py`. |
| Targets archetype(s) | `LEVERAGED_FUNDING_ARB` (primary — entire archetype is "borrow cheap, receive expensive"; if borrow rate exceeds receive-rate the carry inverts and the position bleeds); `CARRY_STAKED_BASIS` (secondary — if LST yield is collateralised via Aave-borrow USDC to short perp, the USDC borrow leg is exposed)                                                  |

### Real-world referent

(1) **Aave V3 ETH borrow APR spike 2024-03-15** — leveraged stETH-loopers crossed Aave's WETH utilization-kink (90%
optimal) en masse during a Merge-anniversary deposit-stake flow; WETH borrow APR jumped from ~3% to ~22% over 45
minutes; loopers either de-levered (selling stETH into thin pools → cascading wstETH/ETH peg break) or held and bled.
(2) **Aave USDC borrow APR spike 2023-03 SVB depeg** — USDC depeg trapped USDC borrowers (longs of USDC short of USDT);
borrow APR went from 4% to 75% as utilization spiked. (3) **Binance tiered-margin-rate 2024-05 BTC** — venue raised
top-tier USDT borrow rate from 5%→18% APR mid-session in response to liquidation cascade; many positions inverted carry
inside 4h. (4) **Spark DAI borrow APR 2024-11** — DSR-driven rate hike pushed Spark DAI borrow APR from 5%→13% in a
single governance vote; recursive-borrow positions on sDAI-as-collateral / DAI-as-borrow inverted overnight. (5)
**rsETH-on-Aave 2026-04-18** (composes with scenario 17) — post-exploit, Aave Guardian froze rsETH markets BUT first
raised borrow rates on adjacent WETH markets ~2x to discourage further draws; positions short of WETH bled while waiting
for the freeze.

### Trigger condition (synthetic injection)

Two variants:

(a) **`defi_kink_crossing`** — at `T+0`, for chosen (chain, protocol, asset) tuple, harness mutates
`getReserveData.currentVariableBorrowRate` response to `baseline_apr × spike_multiplier ∈ {3x, 10x, 30x, 100x}` for
`spike_duration_blocks ∈ {1, 10, 100, 1000}` blocks. Mutation also bumps `getReserveData.utilizationRate` past
`optimalUtilizationRate` (kink) so the slope-2 path is what the rate-strategy contract returns naturally. Recovery: ramp
back to baseline over `recovery_blocks` (matrix: step / 100-block ramp).

(b) **`cefi_margin_rate_recall`** — at `T+0`, venue API returns synthetic `tieredMarginRate` response with rate hiked by
`spike_multiplier ∈ {2x, 5x, 10x}` baseline; additionally, harness emits a synthetic `margin_loan_recall_notice` event
(for venues that support it: bybit / binance) signalling open margin loans must be repaid within
`recall_window_hours ∈ {1h, 4h, 24h}`. Recall is a separate signal from the rate hike — both variants run.

Both variants `synthetic=true` correlation per Phase 1.B; both layer-tap at RAW_TICK before features-onchain /
features-cross-instrument computes carry-PnL feature.

### Observable signature (in event stream + dashboards)

- **AlertCode** — `BORROW_RATE_SPIKE_DEFI` / `CEFI_MARGIN_RATE_HIKE` / `CEFI_MARGIN_RECALL` (all three new — add to UAC
  `LIVE_ALERT_RULES`).
- **features-onchain manifest** — for DeFi variant: `record_captured` continues on the borrow-rate feature (data is
  real, not absent), but the rolling `carry_pnl_bps_<protocol>_<asset>_60s` feature flips sign within 1 block of the
  spike. The scenario tests downstream consumption: does the strategy-service unwind-trigger fire on sign-flip?
- **Cross-feature derivative** — `funding_arb_breakeven_minutes_remaining` (proposed UAC feature) =
  `position_pnl_now / current_burn_rate`. Crosses zero → unwind trigger.
- **Auto-response (Phase 2 disaster_recovery_circuit_breakers)**:
  - `borrow_rate_apr_spike_3x_baseline_for_5min` → `PAUSE_NEW_ENTRIES` on this protocol/asset
  - `borrow_rate_apr_spike_10x_baseline_for_1min` → `UNWIND_POSITIONS` on funding_arb archetype for this asset
  - `cefi_margin_loan_recall_received` → `IMMEDIATE_UNWIND` regardless of rate (recall is non-negotiable)

### Auto-response policy (proposed for disaster_recovery_circuit_breakers)

```yaml
trigger_a: defi_borrow_rate_apr > 3 × baseline_24h_median for ≥ 300s
action_a:
  PAUSE_NEW_ENTRIES (per protocol × asset) + emit AlertCode.BORROW_RATE_SPIKE_DEFI + recompute carry_pnl_bps +
  funding_arb_breakeven_minutes_remaining

trigger_b: carry_pnl_bps < 0 AND |carry_pnl_bps| × position_notional > 0.5 × daily_PnL_budget
action_b:
  UNWIND_POSITION (escalate from PAUSE to active unwind) + accept slippage up to archetype.max_slippage_bps × 2
  (emergency override) + emit AlertCode.FUNDING_ARB_CARRY_INVERTED

trigger_c: cefi_margin_loan_recall_received
action_c:
  IMMEDIATE_UNWIND (≤ recall_window_hours / 2 deadline) + parallelize unwind across all venues holding the recalled
  asset + emit AlertCode.CEFI_MARGIN_RECALL + page operator
```

### Composes with

- **Scenario 03 `defi_liquidity_drain_lending_pool`** — pool drain → utilization spike → kink crossing → borrow APR
  spike. Causal chain.
- **Scenario 15 `liquidation_proximity_auto_deleverage`** — borrow rate spike accelerates LTV drift up; the rate-spike
  scenario can trigger the liquidation-proximity scenario within minutes.
- **Scenario 17 `lrt_lending_meltdown_composite`** — borrow rate spike on WETH-against-rsETH is one of the early signals
  in the LRT meltdown timeline.

### Open questions

- **Baseline window for "spike" definition** — 24h median vs 7d median vs 30d. Recommend 7d (smooths weekly cyclicality
  but catches regime shift). Per-asset override needed for stablecoins (different volatility profile).
- **`funding_arb_breakeven_minutes_remaining` feature** — does this exist in features-cross-instrument? If not, propose
  adding under `features-service (cross-instrument family)/scripts/derived_features/`. **DEFERRED-TO-PHASE-2-IMPL**.
- **CeFi recall-notice schema** — Bybit + Binance margin-loan-recall API formats differ; need adapter normalization in
  MTDS `market_interface/cefi/margin_rates_adapter/` (or wherever per-venue margin-rate fetch lives). Worth a separate
  small plan if not already covered.
