## Scenario `liquidation_proximity_auto_deleverage` — Margin call / LTV approaching liquidation threshold

| Field                | Value                                                                                                                                                                                                                                                                                                                                                                                                           |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario_id`        | `liquidation_proximity_auto_deleverage`                                                                                                                                                                                                                                                                                                                                                                         |
| Category             | `RISK_LIMIT_APPROACH` (primary — health-factor / margin-ratio approaches the protocol's liquidation threshold) + `AUTO_DELEVERAGE` (action — system unwinds before the protocol does, accepting voluntary slippage to avoid involuntary liquidation penalty)                                                                                                                                                    |
| Layer                | `RAW_TICK` (Aave `getUserAccountData.healthFactor` per block; CeFi venue `getMarginAccountInfo.maintenanceMarginRatio` per second) + `FEATURE` (rolling time-to-liquidation feature derived from healthFactor velocity + current collateral price volatility) + `ORDER` (the auto-deleverage trigger that submits unwind orders)                                                                                |
| Asset groups         | `frozenset({MarketAssetGroup.DEFI, MarketAssetGroup.CEFI})`                                                                                                                                                                                                                                                                                                                                                     |
| Applies-to           | **DeFi variant** per-(chain, protocol, position): Aave V3 / Spark / Morpho / Compound V3 — any open borrow position with `healthFactor < 1.5`. **CeFi variant** per-(venue, account): bybit / binance / okx / deribit cross-margin or isolated-margin accounts — any with `maintenance_margin_ratio < 1.5x_initial`.                                                                                            |
| Targets archetype(s) | `LEVERAGED_FUNDING_ARB` (primary — recursive-borrow position by definition runs near LTV ceiling for capital efficiency; any collateral price drop or borrow-asset price rise pushes towards liquidation); `CARRY_STAKED_BASIS` (secondary — LST collateral can lose value vs ETH peg → health factor drops); also `ARBITRAGE_PRICE_DISPERSION` if perp-leg uses isolated margin near the venue's mmr threshold |

### Real-world referent

(1) **Aave V3 stETH-looper cascade 2024-08-05 "Yen carry" unwind** — stETH/ETH peg widened to 1.5% (vs typical 0.05%) on
a Tuesday; recursive stETH-loopers on Aave saw healthFactor drop from ~1.4 to ~1.05 in 90 minutes; ~$120M of positions
self-deleveraged via Aave repay-with-collateral; ~$25M waited too long and got liquidated at the 5% Aave penalty;
reference example of "auto-deleverage saved 5% gross" vs "involuntary liquidation cost 5% gross". (2) **CeFi BTC margin
cascade 2024-12-09** — BTC dropped 8% in 30min; cross-margin Binance accounts at 1.1x mmr were force-liquidated by the
venue's adv-liquidation engine, often at unfavorable prices because the liquidation engine sweeps at market; pre-emptive
deleverage from 1.1x→1.5x mmr would have saved ~80bps on the unwind. (3) **Aave rsETH 2026-04-18 (scenario 17
composes)** — once rsETH price began to crack, healthFactor on rsETH-collateralised positions dropped sharply; positions
that auto-de-levered before Aave Guardian froze withdrawals saved themselves; positions that waited were trapped behind
the freeze. (4) **Curve crvUSD soft-liquidation 2024-06** — Curve's LLAMMA mechanism does continuous partial liquidation
rather than discrete; the analogous trigger is "soft-liquidation band entry" (the position starts losing collateral to
LLAMMA but isn't fully closed); deleverage should fire BEFORE entering soft-liq band.

### Trigger condition (synthetic injection)

Two variants:

(a) **`defi_health_factor_drift`** — at `T+0`, harness mutates `getUserAccountData.healthFactor` response to drift from
baseline `health_factor_baseline ∈ {1.8, 2.0, 2.5}` towards `health_factor_target ∈ {1.5, 1.2, 1.05}` linearly over
`drift_duration_minutes ∈ {5, 30, 180}`. Mutation also adjusts `totalCollateralBase` + `totalDebtBase` consistently so
the math holds. Sign matrix: collateral-price-drop variant (collateral value falls) + borrow-asset-price-rise variant
(debt value rises) — both trigger same drift but different upstream cause.

(b) **`cefi_margin_ratio_drift`** — at `T+0`, harness mutates venue `getMarginAccountInfo.maintenanceMarginRatio`
response to drift from `mmr_baseline ∈ {1.8x, 2.0x, 2.5x}` towards `mmr_target ∈ {1.5x, 1.2x, 1.1x}` over
`drift_duration_minutes ∈ {1, 10, 60}` (CeFi typically faster than DeFi due to tighter mark-price updates). Additionally
for venues that send margin-call-notice signals (deribit / okx), harness emits synthetic margin-call event at the 1.3x
threshold.

Both variants `synthetic=true` correlation per Phase 1.B; both layer-tap at RAW_TICK before risk-and-exposure-service
consumes healthFactor + features-cross-instrument computes time-to-liquidation feature.

### Observable signature (in event stream + dashboards)

- **`time_to_liquidation_minutes`** rolling feature (proposed UAC; lives in features-service (cross-instrument family)):
  ```
  time_to_liquidation_minutes = (current_health_factor - 1.0) / health_factor_velocity_per_minute
  ```
  where `health_factor_velocity` is computed via 60s rolling regression. Threshold ladder:
  - `<60` → AlertCode `LIQUIDATION_60MIN_WARNING`
  - `<30` → AlertCode `LIQUIDATION_30MIN_WARNING` + `PAUSE_NEW_ENTRIES`
  - `<15` → AlertCode `LIQUIDATION_AUTO_DELEVERAGE_TRIGGERED` + actual unwind
- **`auto_deleverage_action_log`** event stream — per-trigger record of (position_id, trigger_time,
  target_health_factor, unwind_method, executed_slippage_bps, final_health_factor).
- **Auto-response (Phase 2 disaster_recovery_circuit_breakers + defi_recursive_borrow_archetypes)**:
  - `time_to_liquidation_minutes < 15` → `AUTO_DELEVERAGE` immediately
    - DeFi: use `aave.repayWithATokens()` to repay debt using collateral aTokens (single tx, low slippage). If pool is
      illiquid, fall back to DEX swap of collateral → borrow-asset → `repay()`.
    - CeFi: reduce position size by `target_leverage_reduction_pct ∈ {25%, 50%}` via market orders on the venue's
      matching engine.
  - `time_to_liquidation_minutes < 30 AND oracle_deviation_check OK` → `PAUSE_NEW_ENTRIES` + recompute every block
  - `time_to_liquidation_minutes < 30 AND oracle_deviation_check FAIL` → ASSUME oracle wild-print; treat conservatively,
    deleverage anyway

### Auto-response policy (proposed for disaster_recovery_circuit_breakers + defi_recursive_borrow_archetypes)

```yaml
trigger_a: time_to_liquidation_minutes < 30 (per position)
action_a: PAUSE_NEW_ENTRIES on archetype
  + emit AlertCode.LIQUIDATION_30MIN_WARNING
  + start computing deleverage plan (which leg to unwind first, target health_factor)

trigger_b: time_to_liquidation_minutes < 15
action_b: AUTO_DELEVERAGE per position-specific plan:
  + DeFi: prefer repayWithATokens; fall back to swap-then-repay
  + CeFi: reduce position size by 50% via market orders
  + accept slippage up to (liquidation_penalty_bps - target_buffer_bps) — voluntary < forced
  + emit AlertCode.LIQUIDATION_AUTO_DELEVERAGE_TRIGGERED
  + page operator with deleverage plan + execution status

trigger_c: deleverage executed AND health_factor_post < 1.3
action_c: ESCALATE — deleverage didn't restore safe margin; either oracle is wrong,
  liquidity is too thin, OR position size was wrong for the regime
  + FULL_FLATTEN (close all related positions across archetype)
  + page operator with regime-change incident report
```

### Composes with

- **Scenario 04 `defi_oracle_deviation_30sigma`** — wild-print oracle can falsely show healthFactor < 1; the deleverage
  trigger must cross-check oracle-deviation before acting on healthFactor (else gets baited into unnecessary unwinds).
- **Scenario 14 `borrow_rate_spike`** — borrow rate spike accelerates debt growth → healthFactor decline;
  auto-deleverage trigger may fire from borrow-rate-spike before any collateral price drop.
- **Scenario 17 `lrt_lending_meltdown_composite`** — primary unwind mechanism in the meltdown is auto-deleverage.

### Open questions

- **`health_factor_velocity` rolling window** — 60s vs 5min vs 30min? 60s catches fast-moving Aave-mark cascades but
  produces noise during routine price chop. Recommend 60s with 5min smoothing fallback; per-protocol override if needed.
- **`liquidation_penalty_bps` per protocol** — Aave V3 = 5% (500bps) default but varies per asset; values needed in UAC
  `LIQUIDATION_PENALTIES` registry. Suggest filing as small UAC sub-plan if not already covered.
- **Cross-position priority** — if 3 positions all hit `time_to_liquidation_minutes < 15` simultaneously, which one
  deleverages first? Recommend: largest absolute exposure first; per-archetype daily_PnL_budget defines the cap.
