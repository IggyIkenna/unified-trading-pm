## Scenario `lst_unstake_queue_blowup` — LST/LRT withdrawal queue duration spikes

| Field                | Value                                                                                                                                                                                                                                                                                                                                                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `scenario_id`        | `lst_unstake_queue_blowup`                                                                                                                                                                                                                                                                                                                                                                 |
| Category             | `LIQUIDITY_LOCKUP` (primary — liquid-staked-token redemption window grows from hours/days to weeks/months, making the staked leg illiquid) + `WITHDRAWAL_QUEUE_CONGESTION` (mechanism — Ethereum exit queue, EigenLayer redelegation queue, Lido buffer drained) + `SECONDARY_MARKET_DEPEG` (consequence — if redemption is locked, secondary-market price decouples from primary peg)     |
| Layer                | `RAW_TICK` (per-LST withdrawal-queue depth + queue-duration from LST issuer API: Lido `bufferedEther` + `unfinalizedStETH`; etherfi `pendingWithdrawals`; Jito `validatorQueue`; EigenLayer `withdrawalRoots` + `withdrawalDelayBlocks`) + `FEATURE` (rolling `unstake_days_remaining` per-LST feature consumed by strategy + risk services)                                               |
| Asset groups         | `frozenset({MarketAssetGroup.DEFI})`                                                                                                                                                                                                                                                                                                                                                       |
| Applies-to           | per-LST/LRT closed set (UAC `LST_TOKEN_TO_PROTOCOL_ASSET` — 16 tokens per `unified_api_contracts.canonical.defi`): Lido stETH/wstETH, etherfi weETH, Rocket Pool rETH, Renzo ezETH, Kelp rsETH, Mantle mETH, Stader ETHx, Frax frxETH/sfrxETH, Coinbase cbETH, Stakewise osETH, Jito jitoSOL, Marinade mSOL, Sanctum LSTs, Lombard LBTC. (Solayer removed 2026-06-02 — operator decision.) |
| Targets archetype(s) | `CARRY_STAKED_BASIS` (primary — entire archetype is "long LST, short perp"; if LST can't be unwound for weeks, the position is involuntarily long beyond risk budget); `LEVERAGED_FUNDING_ARB` (secondary — if LST is the recursive-borrow collateral, can't exit position even if other legs go bad)                                                                                      |

### Real-world referent

(1) **Ethereum withdrawal queue 2024-07 mass-exit** — post-Shapella validator exits queued ~17 days at peak (vs
steady-state ~6 days); Lido stETH redemptions through native unstake queued 8-30 days; secondary market filled the
demand at -25-80bps below peg. (2) **EigenLayer withdrawal delay 2024-10** — initial delegated-withdrawal delay was 7
days; governance raised to 14 days for restaked-only positions due to slashing-domain concerns; impacted restakers had
no way to predict the change. (3) **Renzo ezETH depeg 2024-04** — ezETH had no native redemption (synthetic-only,
secondary-market exit only); a single DEX-pool drain pushed ezETH/ETH to -2% peg; positions levered on
Aave-borrowed-WETH-against-ezETH-collateral got force-deleveraged because price dropped before native redemption could
open. (4) **rsETH on Mantle 2026-04-18** (composes with scenario 17) — bridge exploit + Aave Guardian freeze trapped
rsETH on Mantle behind both a withdrawal halt AND a bridge halt; effective unstake_days_remaining = "indefinite" until
governance resolved. (5) **Solana withdrawal queue MEV-bundle 2024-Q1** — jitoSOL withdrawal queue grew from ~2 days to
~8 days during a high-priority-fee window; mSOL similarly stretched. (6) **Lombard LBTC native redemption 2025-02** —
BTC-bridge-back to native took 30+ days; secondary market for LBTC/BTC widened to 150bps; redemption discount stayed
elevated for 6 weeks.

### Trigger condition (synthetic injection)

Single variant with per-LST applies-to parameter:

**`unstake_queue_duration_spike`** — at `T+0`, for chosen LST/LRT `L`, harness mutates the issuer's queue-status API
response (`bufferedEther` / `pendingWithdrawals` / `validatorQueue` etc.) such that the derived `unstake_days_remaining`
feature jumps from `baseline_days ∈ {2, 6, 10}` to `spike_days ∈ {14, 30, 90}` within
`transition_duration_seconds ∈ {30, 300, 3600}`. The spike can be either a step (sudden change) or a ramp (queue slowly
grows). Mutation persists for `spike_duration_hours ∈ {6, 24, 168}` then ramps back to baseline over
`recovery_duration_hours ∈ {24, 168}`.

A secondary sub-variant: **`secondary_market_depeg`** — concurrent with the queue spike, harness mutates the DEX-pool
spot price of `L/ETH` (or `L/SOL`, `L/BTC` per chain) to `peg_target ∈ {-0.5%, -2%, -8%}` below 1.0. This composes with
scenario 13's `dex_pool_drain` mechanism but in this scenario the depeg is driven by queue-stress demand, not synthetic
pool drain.

Both layers (queue + depeg) emit `synthetic=true` correlation per Phase 1.B; both layer-tap at RAW_TICK before
features-onchain reads.

### Observable signature (in event stream + dashboards)

- **`unstake_days_remaining_<lst>`** rolling feature (proposed UAC; lives in features-onchain or
  features-cross-instrument):
  ```
  unstake_days_remaining = withdrawal_queue_depth_eth / withdrawal_throughput_eth_per_day
  ```
  Per-LST baseline + threshold ladder:
  - `> 2x baseline` → AlertCode `LST_UNSTAKE_QUEUE_EXTENDED`
  - `> 14 days` → AlertCode `LST_UNSTAKE_QUEUE_LOCKED` + `PAUSE_NEW_ENTRIES` on LST-leg
  - `> 30 days` → AlertCode `LST_UNSTAKE_QUEUE_CRITICAL` + `BEGIN_SECONDARY_MARKET_EXIT`
- **`lst_secondary_market_premium_bps_<lst>`** feature — DEX-pool spot price vs primary-issuance rate. Threshold ladder:
  - `< -50bps for > 30min` → `LST_SECONDARY_DEPEG_WARNING`
  - `< -200bps for > 60min` → `LST_SECONDARY_DEPEG_SEVERE` + forced exit-mode-decision (queue vs secondary vs hold)
- **Composite exit-method-decision logic** (proposed feature):
  ```
  optimal_exit_method = argmin over {wait_for_queue, secondary_market_sell}
  cost(wait_for_queue) = unstake_days × daily_carry_cost + opportunity_cost
  cost(secondary_market_sell) = abs(secondary_premium_bps) + slippage_bps
  ```
  Strategy/execution-service picks the cheaper option dynamically.

### Auto-response policy (proposed for disaster_recovery_circuit_breakers + carry_staked_basis archetype)

```yaml
trigger_a: unstake_days_remaining > 14 days
action_a: PAUSE_NEW_ENTRIES on LST-leg of all carry_staked_basis positions on this LST
  + emit AlertCode.LST_UNSTAKE_QUEUE_LOCKED
  + compute secondary-market exit cost vs hold cost
  + if hold-cost < secondary-cost: HOLD + extend perp-hedge if expiring
  + if secondary-cost < hold-cost: BEGIN_SECONDARY_MARKET_EXIT

trigger_b: unstake_days_remaining > 30 days OR secondary_market_depeg > 200bps for > 60min
action_b: EXIT_REGIME — assume this LST is structurally impaired
  + FLATTEN positions via the cheaper of (queue / secondary)
  + emit AlertCode.LST_REGIME_CHANGE
  + page operator with regime assessment

trigger_c: rsETH-like exploit signal (composes with scenario 17 trigger_a)
  → AUTO_DELEVERAGE supersedes (scenario 15 takes priority over wait-for-queue)
```

### Composes with

- **Scenario 15 `liquidation_proximity_auto_deleverage`** — if LST is locked AND collateral health drops,
  auto-deleverage cannot use the LST as repayment-collateral; must swap LST→ETH via secondary market (accepting depeg
  cost) OR swap ETH→borrow-asset via DEX. Decision logic gets harder.
- **Scenario 17 `lrt_lending_meltdown_composite`** — primary triggering signal: LRT bridge exploit → secondary-market
  depeg → queue stress → meltdown cascade.
- **Scenario 10 `defi_stablecoin_depeg`** — same shape, different asset; shared `peg_deviation_bps` taxonomy.

### Open questions

- **Per-LST `withdrawal_throughput_eth_per_day` baseline** — needs UAC `LST_WITHDRAWAL_THROUGHPUT_BASELINES` registry.
  Computed from on-chain history; needs 30d / 90d / 1y windows. **DEFERRED-TO-PHASE-2-IMPL**.
- **Secondary-market peg-restore mechanism per LST** — Lido stETH has arb-bot-driven peg; rsETH has
  bridge-validator-driven; ezETH has neither (synthetic). The "peg-restore time-constant" per LST drives the
  hold-vs-exit decision. Recommend filing as small UAC sub-plan.
- **LRT-on-L2 = bridge-trust + issuer-trust + lender-trust (3-layer)** — per-L2 backing-ratio attestation feed needed
  before exposure cap calibration (lessons from rsETH 2026-04-18; see scenario 17).
