## Scenario `execution_slippage_spike` — Order fill price diverges from intended (DEX + CeFi)

| Field                | Value                                                                                                                                                                                                                                                                                                          |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario_id`        | `execution_slippage_spike`                                                                                                                                                                                                                                                                                     |
| Category             | `EXECUTION_QUALITY` (primary — realised fill bps off intended-mid blows past threshold) + `LIQUIDITY_DRAIN` (DEX variant — pool depth collapses) + `BOOK_THINNING` (CeFi variant — bid-ask spread widens AND top-N book depth falls)                                                                           |
| Layer                | `ORDER` primary (matching-engine / DEX-swap fill telemetry: realised fill price vs decision-time mid) + `RAW_TICK` secondary (mid-quote + book depth feed at the moment of fill) + `FEATURE` tertiary (rolling realised-slippage feature consumed by execution-quality monitor). Three taps.                   |
| Asset groups         | `frozenset({MarketAssetGroup.DEFI, MarketAssetGroup.CEFI})`                                                                                                                                                                                                                                                    |
| Applies-to           | **DEX variant** per-(chain, pool): Uniswap V3 / Curve / Balancer / Drift / Hyperliquid-spot (closed set per UAC `_defi.py` PROTOCOL_CAPABILITIES; GMX removed 2026-07-25, see `defi_gmx_venue_removal_2026_07_25.md`). **CeFi variant** per-venue: bybit / binance / deribit / okx / hyperliquid-perp / aster. |
| Targets archetype(s) | `CARRY_STAKED_BASIS` (LST→hedge-perp rebalance leg slips on either side); `ARBITRAGE_PRICE_DISPERSION` (perp-spot dispersion arb — if either leg slips, the captured edge collapses); `LEVERAGED_FUNDING_ARB` (entry/unwind leg of recursive borrow position)                                                  |

### Real-world referent

(1) **Uniswap V3 wstETH/ETH pool 2024-09 reorg-tail slippage** — a 4-block reorg flipped pool tick boundary mid-bundle;
a 500 wstETH swap executed at 240bps slippage vs decision mid (expected ~8bps). MEV bots ate the inter-block
dislocation. (2) **Curve crvUSD/USDC depeg-tail 2024-08** — pool drained one side during depeg-recovery; tail swaps
(last 10% of pool's USDC side) saw 80-300bps slippage; downstream PnL-attribution flagged the realised-vs-expected gap
but only after settlement. (3) **Binance BTCUSDT-perp 2024-04 CPI-print book thinning** — top-of-book spread widened
from 0.3bps to 35bps for ~12s; market orders sized at "normal depth" walked the book; realised-vs-expected slippage on
200 BTC of hedge-rebalance flow was ~28bps. (4) **Bybit 2024-12 ETHUSDT-perp halt-recovery** — when matching resumed
after the 20min outage, the first ~90s of fills saw 50-120bps slippage as the book re-formed; agents that submitted IOCs
in that window leaked. (5) **GMX V1 AVAX-spot 2025-02** — the GLP-AVAX leg's pool utilisation hit 95%; AMM curve's
borrow-fee adjustment pushed effective swap price 180bps off Chainlink reference; arbitrageurs took the dislocation.

### Trigger condition (synthetic injection)

Two variants run as separate sub-scenarios under `scenario_id`, parameterised via `variant`:

(a) **`dex_pool_drain`** — at wall-clock `T+0`, for chosen (chain, pool) `P`, the harness mutates the pool-state
response returned by `eth_call` / `getAccountInfo` to drain `drain_pct ∈ {25%, 50%, 75%, 95%}` of the same-side
liquidity. Effect: a swap sized at `swap_size_usd_baseline` (per-pool from historical p50) now incurs slippage of
`expected_slippage_bps × (1 / (1 − drain_pct))` per AMM curve. Mutation persists for
`drain_duration_seconds ∈ {30s, 300s, 1800s}`, then reverts to baseline. Sign matrix: ±1 (drain either token side
independently).

(b) **`cefi_book_thinning`** — at `T+0`, for chosen venue `V` and instrument `I`, harness publishes synthetic L2 book
updates that (i) widen top-of-book spread by factor `spread_blowout_ratio ∈ {5x, 20x, 100x}` baseline-spread-bps, AND
(ii) reduce top-5 level cumulative depth by `depth_collapse_pct ∈ {50%, 80%, 95%}`. Mutation persists for
`book_thinning_duration_seconds ∈ {10s, 60s, 600s}`. Then ramp-recovery over 30s (matrix variant: step-recovery for
halt-style cases).

Both variants emit `synthetic=true` correlation per Phase 1.B scenario contract; both layer-tap at ORDER + RAW_TICK
before features-cross-instrument reads realised-slippage feature.

### Observable signature (in event stream + dashboards)

- **execution-service ORDER manifest row** — `record_failed(error=ExcessiveSlippageError, attempted_at=<fill_time>)` on
  the (venue, instrument, order_id) shard when realised vs intended slippage crosses per-archetype `max_slippage_bps`
  threshold (from UAC `ARCHETYPE_RISK_LIMITS` per `defi_recursive_borrow_archetypes`).
- **AlertCode** — `EXECUTION_SLIPPAGE_EXCEEDED` (DeFi) / `CEFI_BOOK_THIN` (CeFi) emitted within 1 tick of the post-fill
  mid update.
- **Realised-slippage rolling feature** — `realised_slippage_bps_<venue>_<instrument>_60s` rolling-window time-series
  crosses 50bps threshold (CeFi) / 100bps threshold (DEX small) / 200bps threshold (DEX large).
- **Auto-response (Phase 2 of disaster_recovery_circuit_breakers)**: per-(venue, instrument)
  `MarketTradingMode.READ_ONLY` flip within 5s; in-flight orders cancelled; archetype enters `PAUSE_NEW_ENTRIES` state;
  existing position held until book re-forms OR explicit deleverage-trigger fires (composes with scenario 15).

### Auto-response policy (proposed for disaster_recovery_circuit_breakers)

```yaml
trigger: realised_slippage_bps_60s > archetype.max_slippage_bps for ≥ 3 consecutive fills
action: PAUSE_NEW_ENTRIES (per venue × instrument)
  + cancel_open_orders(scope=this_venue_this_instrument)
  + emit AlertCode.EXECUTION_SLIPPAGE_EXCEEDED
  + cooldown_seconds: 300 (re-arm after 5min book-stable window)
escalation: if 3+ venues thin simultaneously within 60s → archetype-wide PAUSE
  (composes with scenario 08 cross_asset_flash_crash; treated as cross-venue contagion)
```

### Composes with

- **Scenario 03 `defi_liquidity_drain_lending_pool`** — same shape, different layer (lending vs DEX-swap); shared
  `LiquidityDrainError` taxonomy in UAC.
- **Scenario 04 `defi_oracle_deviation_30sigma`** — wild-print oracle can trigger AMM rebalance flow that itself drains
  pool; cascade.
- **Scenario 17 `lrt_lending_meltdown_composite`** — slippage on LRT-pair pools is the first observable signal of
  LRT-side stress.

### Open questions

- Per-archetype `max_slippage_bps` thresholds — values needed in UAC `ARCHETYPE_RISK_LIMITS`. Suggest:
  `CARRY_STAKED_BASIS=80bps`, `ARBITRAGE_PRICE_DISPERSION=15bps` (must be tight or edge vanishes),
  `LEVERAGED_FUNDING_ARB=120bps` (entry only; unwind 200bps).
- DEX-swap pre-trade slippage prediction (Uniswap quoter / Curve `get_dy`) vs realised — should the scenario also test
  the predicted-vs-realised gap, or only realised-vs-intended-mid? Recommend: both, predicted-vs-realised as a separate
  `quoter_accuracy` sub-variant.
