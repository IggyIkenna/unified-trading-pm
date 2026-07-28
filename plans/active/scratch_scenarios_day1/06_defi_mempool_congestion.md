## Scenario `defi_mempool_congestion_inclusion_delay` — Mempool congestion → inclusion-delay → MEV sandwich risk

| Field                | Value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario_id`        | `defi_mempool_congestion_inclusion_delay`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Category             | `OPERATIONAL` (mempool dynamics — tx timing, not chain liveness) + `DATA_CORRUPTION` (sandwich variant — adversarial price-impact between sign-time and inclusion-time)                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Layer                | `ORDER` primary (tx submission + cancel-tx race in execution-service connectors) + `EVENT` secondary (synthetic `pending_tx` lifecycle events from the mempool watcher). `RAW_TICK` is NOT touched (oracles + chain state remain truthful — only **our own** in-flight transactions are affected).                                                                                                                                                                                                                                                                                        |
| Asset groups         | `frozenset({MarketAssetGroup.DEFI})`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Applies-to           | per-chain — closed set `{ethereum_mainnet, arbitrum, optimism, base}`. **Solana is NOT in scope** (Jito block-engine bundle inclusion is structurally different — no public mempool to congest; covered separately by a Jito-bundle-failure scenario in the post-cutover library). **L2s included with reduced severity** — Arbitrum / Optimism / Base sequencer is centralised so the "mempool" surface is the sequencer queue rather than a peer-to-peer mempool, but inclusion-latency spikes do occur during sequencer congestion (Arbitrum 2024-Q1 sequencer outage referent below). |
| Targets archetype(s) | `CARRY_STAKED_BASIS` (PRIMARY — every rebalance / deposit / withdraw against Aave / Uniswap V3 LST pool is a mainnet swap whose `available_at` is the inclusion timestamp; sandwich attack on a large rebalance burns slippage budget); `ARBITRAGE_PRICE_DISPERSION` (SECONDARY — any DeFi spot leg of a funding-arb pair whose underlying needs Uniswap / Curve fill; the perp-hedge leg lives on CeFi venues and is unaffected, so this is asymmetric leg-risk during the congestion window)                                                                                            |

### Real-world referent

Three categories of real-world incident shape this scenario. (1) **Ethereum mainnet 2023-Q3 / 2023-Q4 sandwich-bot
domination** — post-Merge, sandwich + back-running bots routinely captured 5-30 bps from un-protected swaps on Uniswap
V3; aggregate MEV extracted from public-mempool swaps tracked by `eigenphi.io` peaked at ~$5M / week during memecoin
frenzies. (2) **Flashbots Protect emergence (2022-Q4 onwards)** — `rpc.flashbots.net` became the default sandwich
mitigation for any swap ≥ $10k notional, but adoption is partial; transactions submitted via public
`eth_sendRawTransaction` remain sandwich-vulnerable. (3) **Arbitrum 2024-Q1 sequencer outage** (2024-01-15, ~78 min) +
the broader pattern of L2-sequencer queue backlogs during high-volume mint events — txs sit pending in sequencer queue
while the chain liveness probe still returns OK, so a chain-RPC-outage scenario would NOT catch this failure mode. (4)
**Continuous baseline**: Etherscan publishes `mean_inclusion_block_count` per hour; baseline ranges 1-2 blocks (12-24s)
on mainnet, spiking to 10-30 blocks (~120-360s) during NFT mints / airdrop claims / liquidation cascades. This scenario
captures the upper envelope of that distribution as the worst-case operational stress test for the May-23 archetypes'
tx-submission paths.

### Trigger condition (synthetic injection)

At wall-clock `T+N` seconds (`N` = scenario start offset, default 60), for the chosen chain
`C ∈ {ethereum_mainnet, arbitrum, optimism, base}`:

1. **Inclusion-latency injection (always-on)**: every transaction the execution-service signs and submits during the
   congestion window has its observed `confirmed_at - signed_at` artificially extended to `inclusion_delay_seconds`
   (default 180s = ~15 blocks on mainnet). Mechanism: matching-engine adversarial mode intercepts `submit_transaction()`
   calls on `_mev_provider`, holds the synthetic confirmation event for `inclusion_delay_seconds` before emitting
   `TX_CONFIRMED`.
2. **Synthetic `pending_tx` event stream**: a synthetic stream of `pending_tx` lifecycle events (`SIGNED` → `BROADCAST`
   → `PENDING(elapsed=Xs)` → `CONFIRMED` or `CANCEL_LOST_RACE`) is emitted on the EVENT layer per affected tx.
   `pending_count` saturates at `pending_tx_count_target` (default 100 simultaneous in-flight txs) as the strategy
   continues issuing rebalance instructions blind to the congestion.
3. **Optional sandwich variant** (`sandwich_variant=True`): for each Uniswap swap tx the strategy submits during the
   window, the harness injects a synthetic sandwich pair against it — a `BookSpoof` mutation on the Uniswap V3 pool's
   pre-tx state (front-run buy moves price `loss_target_bps`, default 50 bps = 0.5%, above the LP-pool-quoted mid) + a
   synthetic back-run sell that reverts the pool state post-our-tx but locks in the price impact for our fill. The
   strategy's signed `amountOutMinimum` (slippage guard) is honoured — if `slippage_tolerance_bps` < `loss_target_bps`,
   the tx reverts on-chain with `SLIPPAGE_EXCEEDED` (execution-service `DefiErrorCode`); if ≥, the tx fills at the worse
   price and the loss is realised.
4. **Cancel-tx race (always-on for affected txs)**: when the strategy's risk-and-exposure-service requests cancellation
   of an in-flight tx (e.g. because `inclusion_latency_seconds` breaches a fresh-quote threshold), the harness emits the
   cancel-tx with a synthetic `gas_price < original_tx_gas_price` (simulating the operator failing to bid up the cancel)
   so the original confirms first 80% of the time + cancel confirms first 20%. The cancellation-lag metric
   (`cancel_signed_to_cancel_confirmed_seconds`) tracks the full race.
5. **Recovery curve**: at `T + congestion_duration_seconds` (default 600s = 10min) the synthetic inclusion-delay decays
   linearly over `recovery_curve_seconds` (default 300s) back to the chain's baseline (12s on mainnet, 1s on Arbitrum).
   Sandwich injection terminates immediately at the same `T + congestion_duration_seconds` mark (not part of the ramp —
   sandwich bots are either active or not, no graceful decay).

The injection is correlation-id-tagged `synthetic=true` per UAC scenario contract Phase 1.B. Mempool watch + Flashbots
Protect submission paths are NOT short-circuited; the scenario tests the system's behaviour AS IF Flashbots Protect
failed for these specific txs (worst-case: private-mempool path unreachable, falls through to public mempool per
`codex/04-architecture/mev-protection.md` "Operational Run-Book" item 3) OR AS IF a non-Flashbots chain (Arbitrum / L2s
— `NoProtectionProvider` per the MEV codex doc § "Provider Selection" table).

### Observable signature (in event stream + dashboards)

- Mempool-depth metric spike: `mempool_pending_count` (per-chain) for `C` crosses `pending_tx_count_target` within 30s
  of trigger; emitter is execution-service mempool watcher.
- Inclusion-latency feature spike (per-chain): `mean_inclusion_latency_seconds` for `C` crosses 5× baseline within 60s
  (12s → 60s on mainnet; 1s → 5s on Arbitrum). Emitter is features-onchain `chain_mempool_latency` feature.
- `pending_tx` count > `inflight_tx_limit` threshold per archetype (default 5 simultaneous): autonomous-recovery state
  machine transitions to `mempool_congested` state in risk-and-exposure-service rule evaluator. **FOLLOW-UP** P2: no
  explicit `mempool_congested` named state in current `codex/04-architecture/autonomous-recovery-matrix.md`; closest
  analog is `chain_data_stale` (used by RPC-outage scenario). Suggested follow-up: extend the autonomous-recovery
  state-machine taxonomy to include `mempool_congested` distinct from `chain_data_stale` (chain is live + responsive,
  but our txs are stuck). Plan to capture: `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 4.
- Cancel-tx race outcome event: for each cancel issued during the window, exactly one of `CANCEL_WON_RACE` /
  `CANCEL_LOST_RACE` fires from execution-service `OrderRecoveryEngine`. Aggregate `cancel_lost_rate_bps` over the
  rolling 5min window crosses 8000 bps (80%) during the synthetic congestion.
- MEV-sandwich-loss feature spike (sandwich variant only): completed Uniswap swap fills emit a `realised_slippage_bps`
  per fill; the rolling distribution shifts from baseline (~5 bps p50, ~15 bps p99) to scenario distribution
  (~`loss_target_bps` p50 = 50 bps p50, ~100 bps p99). Emitter is execution-service `SwapHandler` post-fill measurement.
- `MEV_DETECTED` event (sandwich variant only): per `codex/04-architecture/mev-protection.md:376-389` (sandwich pattern
  detection — "tx pair with same `tx_recipient` flanking ours within ±2 blocks + opposite direction"), the mempool
  watcher emits a typed `MEV_DETECTED` event per detected sandwich; the breaker state machine consumes this event per
  the DR plan Phase 8 taxonomy.
- `DEFI_TX_SIMULATION_FAILED` fires for every Tenderly pre-flight whose simulated `amountOut` is now
  `< amountOutMinimum` because the synthetic front-run repriced the pool (sandwich variant only — inclusion-delay-only
  variant doesn't trip simulation since pool state isn't mutated).
- `CIRCUIT_BREAKER_DEGRADED` → `CIRCUIT_BREAKER_OPEN` cascade: `GAS_PRICE_SURGE_GWEI` may co-fire if the strategy raises
  gas to push pending txs through (composes with `defi_gas_surge_50x`); the mempool-congestion-specific breaker is
  **NEW** — see FOLLOW-UP gap callout below.
- Alert event payload includes `pending_count` + `mean_latency_s` provenance fields so operators can confirm the
  synthetic injection vs a real mempool spike at triage time.
- Autonomous-recovery transitions visible in deployment-UI `defi.execution` tile: `mempool_congested` state badge
  appears within ~60s; clears when inclusion-latency returns to baseline for 60s contiguous post-recovery.

### Mutation spec (UAC `ScenarioMutationSpec` discriminated-union member)

- **Mutation types (composite)**: `LatencyInject(target="tx_submission", delay_seconds=inclusion_delay_seconds)` on
  ORDER layer (existing closed-union member per Phase 1.B line 343-345) +
  `EventDuplicate(stream="pending_tx", count_target=pending_tx_count_target)` on EVENT layer (synthesises the pending-tx
  queue saturation; existing union member) + (sandwich variant only)
  `BookSpoof(pool="uniswap_v3_<pair>_<fee_tier>", front_run_bps=loss_target_bps, direction="adversarial")` on
  ORDER-adjacent quote-state mutation (existing union member). **No new mutation member needed** — the pre-cutover
  6-scenario subset uses only the existing 11-member closed union per Phase 1.B. Post-cutover plan should consider a
  dedicated `MempoolCongestion` composite mutation for cleaner semantics + parameter grouping.
- **Parameters**:
  - `chain: Literal["ethereum_mainnet", "arbitrum", "optimism", "base"]`
  - `inclusion_delay_seconds: int = 180` (matrix variants: 30 / 90 / 180 / 360 for mainnet — 90 = mild congestion, 180 =
    NFT-mint storm, 360 = sequencer outage envelope)
  - `congestion_duration_seconds: int = 600` (matrix variants: 120 / 600 / 1800)
  - `recovery_curve: Literal["step", "linear_300s", "linear_600s"] = "linear_300s"`
  - `pending_tx_count_target: int = 100`
  - `sandwich_variant: bool = False`
  - `loss_target_bps: int = 50` (sandwich variant only; matrix: 20 / 50 / 100 / 200 — 200 bps exceeds typical
    `slippage_tolerance_bps=30` so should always revert)
  - `cancel_lost_race_probability: float = 0.8` (cancel-tx race outcome; matrix: 0.5 / 0.8 / 1.0)
- **Pipeline tap layer**: primary `ScenarioOverlayLayer.ORDER` (tx submission + cancel race) + secondary
  `ScenarioOverlayLayer.EVENT` (pending-tx lifecycle stream). RAW_TICK explicitly **not** touched — chain state + oracle
  feeds remain truthful, distinguishing this scenario from `defi_chain_rpc_outage_solana` (which freezes chain data) and
  `defi_oracle_deviation_30sigma` (which corrupts oracle reads).
- **`available_at` discipline**: tx inclusion-time IS the legitimate `available_at` for downstream P&L attribution on
  swap fills — a 180s synthetic inclusion delay legitimately shifts `available_at` 180s forward for the affected fills,
  mirroring what would happen in a real congestion event. Per Phase 2.E (plan lines 397-401), the applier MUST stamp
  `_synthetic_available_at_shift: bool = True` on the affected `tx_confirmed` event rows + downstream fill rows so UTL
  `lookahead_bias_check(scenario_overlay_active=True)` downgrades to a structured warning rather than raising
  `LookaheadBiasError`. Strict mode stays ON for all non-overlay paths — this scenario does NOT introduce lookahead bias
  because the shift is forward (later confirmation), not backward (earlier knowledge).

### Expected outcomes (per archetype × per variant)

| Archetype                                                   | Variant                                                                      | `RiskRuleConsequence`                                                                                                                                                                                                                                                                                                                                                    | Breaker(s) tripped (cite by `breaker_id` from UAC registry)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `BreakerAction`                                                                                                                                                                                                                                                                                           | `KillSwitchId` armed (if any)                                                                                                                                                                                                                                                                                     | `AlertCode` fired                                                                                                                                                                                                                                      | `expected_within`                                         |
| ----------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| `CARRY_STAKED_BASIS`                                        | inclusion-delay only                                                         | `MONITOR` — LST rebalance is not safety-critical at intra-day cadence; a 600s congestion window is well within the strategy's natural rebalance frequency (typically hourly), so the rule engine emits advisory only.                                                                                                                                                    | **FOLLOW-UP** P1 (no dedicated mempool-congestion breaker in `registry/circuit_breakers/carry_staked_basis.py`). Closest analog: `BATCH_LIVE_DIVERGENCE_BPS` (`carry_staked_basis.py:168-180`, threshold 50bps) — IF the inclusion delay causes execution P&L to diverge from batch >50bps, this fires SCALE_DOWN as a side-effect. Suggested NEW breaker_id: `MEMPOOL_INCLUSION_LATENCY_SECONDS`, scope=PER_ASSET_GROUP, applies_to="defi", threshold=120s (= 10 blocks mainnet baseline-2σ), action=BLOCK_NEW, cooldown=120, AUTO_COOLDOWN. | `MONITOR` (advisory) at rule layer; no breaker action absent the FOLLOW-UP breaker                                                                                                                                                                                                                        | none                                                                                                                                                                                                                                                                                                              | `RISK_RULE_MONITOR_FIRED` (`codes.py:150`) + (post-FOLLOW-UP) `CIRCUIT_BREAKER_DEGRADED` (`codes.py:43`)                                                                                                                                               | 30s                                                       |
| `CARRY_STAKED_BASIS`                                        | sandwich variant, `loss_target_bps=50`                                       | `SCALE_DOWN` via `SLIPPAGE_BUDGET_PER_ARCHETYPE` (`registry/risk_rules/archetype.py:157-165`, budget=35bps for carry archetype) — projected slippage exceeds budget; rule cuts clip size proportionally. SCALE_DOWN reduces clip notional below the sandwich bot's profitable-extraction threshold (smaller fills attract less sandwich attention; bot economics break). | `BATCH_LIVE_DIVERGENCE_BPS` (`carry_staked_basis.py:168-180`) fires SCALE_DOWN once realised slippage breaches the 50bps batch-live divergence threshold; **FOLLOW-UP** P1 — same suggested NEW breaker as inclusion-delay row, plus a dedicated `MEV_SANDWICH_LOSS_BPS` breaker (suggested: scope=PER_ARCHETYPE, threshold=30bps, action=SCALE_DOWN, AUTO_COOLDOWN)                                                                                                                                                                          | `SCALE_DOWN` (smaller chunks)                                                                                                                                                                                                                                                                             | none                                                                                                                                                                                                                                                                                                              | `RISK_RULE_SCALED_DOWN` (`codes.py:144`) + `DEFI_TX_SIMULATION_FAILED` (`codes.py:55`) per failed Tenderly pre-flight + (post-FOLLOW-UP for `MEV_DETECTED`-driven alerts; today no literal `MEV_SANDWICH_DETECTED` AlertCode — see FOLLOW-UP P2 below) | 60s                                                       |
| `CARRY_STAKED_BASIS`                                        | sandwich variant, `loss_target_bps=200` (> default 30bps slippage tolerance) | `BLOCK` via `SLIPPAGE_BUDGET_PER_ARCHETYPE` (rejects pre-flight because projected impact > budget) + on-chain `TX_REVERTED` for any tx that slips through (slippage guard `amountOutMinimum` honoured)                                                                                                                                                                   | `BATCH_LIVE_DIVERGENCE_BPS` SCALE_DOWN — but irrelevant since BLOCK at rule layer prevents tx submission                                                                                                                                                                                                                                                                                                                                                                                                                                      | `BLOCK_NEW` at risk layer (no breaker escalation needed if pre-flight catches it; if pre-flight bypass occurs + on-chain reverts accumulate, escalates per `REJECT_RATE_BPS` — though that breaker is currently seeded for `ARBITRAGE_PRICE_DISPERSION` not `CARRY_STAKED_BASIS`, see FOLLOW-UP P3 below) | none initially; ESCALATES to `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` (`kill_switch.py:79`) only if every rebalance attempt reverts AND a position is approaching `LIQUIDATION_CASCADE_RISK` threshold (`carry_staked_basis.py:110-124`, HF<=1.10) without successful unwind                                       | `RISK_RULE_BLOCKED` (`codes.py:134`) + `DEFI_TX_SIMULATION_FAILED` per reverted simulation                                                                                                                                                             | 60s                                                       |
| `ARBITRAGE_PRICE_DISPERSION` (DeFi spot leg of funding-arb) | inclusion-delay only                                                         | `SCALE_DOWN` via `SLIPPAGE_BUDGET_PER_ARCHETYPE` (`archetype.py:327-336`, budget=15bps for arb archetype — tighter than carry because basis math is more slippage-sensitive). Delayed inclusion grows the strategy's exposure to mid-drift during the pending window, so projected slippage cap fires earlier.                                                           | **FOLLOW-UP** P1 same as carry rows + (suggested) cross-archetype seed of the new `MEMPOOL_INCLUSION_LATENCY_SECONDS` for `applies_to="ARBITRAGE_PRICE_DISPERSION"` with tighter threshold=60s (arb is more time-sensitive than carry)                                                                                                                                                                                                                                                                                                        | `SCALE_DOWN`                                                                                                                                                                                                                                                                                              | none                                                                                                                                                                                                                                                                                                              | `RISK_RULE_SCALED_DOWN` (`codes.py:144`) + `CIRCUIT_BREAKER_DEGRADED` (post-FOLLOW-UP)                                                                                                                                                                 | 30s                                                       |
| `ARBITRAGE_PRICE_DISPERSION` (DeFi spot leg of funding-arb) | sandwich variant                                                             | `BLOCK` — basis math is exquisitely slippage-sensitive; 15bps slippage budget is hit instantly at `loss_target_bps>=20`. Pre-flight rejects every DeFi leg attempt during the sandwich window. Hedge-leg perp continues trading (CeFi, unaffected) so existing positions accrue funding cost + delta drift.                                                              | `INVENTORY_IMBALANCE_RATIO` (`registry/circuit_breakers/arbitrage_price_dispersion.py:95-109`, threshold=20%) trips as DeFi leg can't be opened to balance the CeFi hedge → CANCEL_OPEN on the dangling CeFi hedge after `inventory_imbalance_window_seconds`; `HEDGE_GAP_NOTIONAL_USD` (`arbitrage_price_dispersion.py:158-172`, threshold=$100k) escalates if imbalance grows                                                                                                                                                               | `CANCEL_OPEN` (INVENTORY_IMBALANCE_RATIO) + `BLOCK_NEW` (HEDGE_GAP_NOTIONAL_USD) — INVENTORY_IMBALANCE_RATIO defaults to `MANUAL_UNKILL` per `BREAKER_RECOVERY_DEFAULTS` (CANCEL_OPEN → MANUAL_UNKILL)                                                                                                    | `KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION` (`kill_switch.py` analog of `:79`; **FOLLOW-UP** P3 — verify per-archetype kill-switch seed for arbitrage_price_dispersion is in the closed set) initially; ESCALATES to `KILL_PER_ASSET_GROUP_DEFI` (`kill_switch.py:92`) if hedge-gap accrues during the window | `RISK_RULE_BLOCKED` + `UNHEDGED_POSITION_ALERT` (`codes.py:84`) + `CIRCUIT_BREAKER_OPEN` (post-cancel-cascade) + `KILL_SWITCH_MANUAL_UNKILLED` on eventual operator action (`codes.py:178`)                                                            | 60s for first BLOCK; 180s for inventory-imbalance cascade |

### Auto-recovery contract (per DR plan `BreakerRecoveryRule`)

For the **inclusion-delay-only** variant on the suggested NEW `MEMPOOL_INCLUSION_LATENCY_SECONDS` breaker (FOLLOW-UP P1
below — design assumes the breaker ships per the disaster_recovery_circuit_breakers Phase 4 follow-up):

- `recovery_mode`: `AUTO_COOLDOWN` per `BREAKER_RECOVERY_DEFAULTS[BreakerAction.BLOCK_NEW]` (`circuit_breaker.py:236`)
- `guard_description`:
  `"mempool_pending_count < pending_tx_count_target/2 AND mean_inclusion_latency_seconds < baseline*2 sustained for 60s contiguous"`
- `retry_policy`: `"exponential"` (mempool clears in step-functions during NFT-mint exhaustion; exponential matches the
  empirical decay shape)
- `auto_disarm_after_seconds`: `120`

For the **sandwich variant** on the suggested NEW `MEV_SANDWICH_LOSS_BPS` breaker:

- `recovery_mode`: `AUTO_COOLDOWN` for typical sandwich-pattern firings (BLOCK_NEW → AUTO_COOLDOWN default)
- `guard_description`: `"realised_slippage_bps p95 < 10bps AND no MEV_DETECTED event for 120s contiguous"`
- `retry_policy`: `"exponential"`
- `auto_disarm_after_seconds`: `300`
- **OVERRIDE to `MANUAL_UNKILL`** if 3 consecutive `MEV_DETECTED` events fire within a rolling 1h window — repeat
  targeting by the same searcher cohort is a signal the wallet identity / pattern has leaked, and operator review
  (rotate wallet / change submission policy / increase MEV-protection threshold) is required before the auto-cooldown
  path is safe to honour. Per `BreakerConfig` validator, MANUAL_UNKILL requires `cooldown_seconds=None`.

For the **inventory-imbalance escalation** (arbitrage variant on `INVENTORY_IMBALANCE_RATIO`):

- `recovery_mode`: `MANUAL_UNKILL` per `BREAKER_RECOVERY_DEFAULTS[BreakerAction.CANCEL_OPEN]` (cancelled hedge orders
  are gone; auto-recovery doesn't restore them)
- `guard_description`: `"operator confirms hedge position rebalanced + DeFi leg gateway green"`
- `retry_policy`: `"none"`
- `auto_disarm_after_seconds`: `None`

**Composes with `codex/04-architecture/mev-protection.md`** § "MEV-driven breaker trigger" (lines 376-394): the existing
`MEV_DETECTED` event already feeds the breaker state machine with `BreakerAction.BLOCK_NEW` +
`BreakerRecoveryMode.AUTO_COOLDOWN`. The suggested NEW `MEV_SANDWICH_LOSS_BPS` breaker is the **threshold-based
codification** of that event-driven trigger so the breaker can also fire on **passive observation of realised loss**
(post-fill measurement) not only on **mempool-watch pattern detection** (pre-confirmation). Operationally — if Flashbots
Protect is misconfigured / falls back to public mempool, the realised-loss path catches what the mempool-watch path
missed. Operator escape valve during the scenario: increase `MEV_PROTECTION_THRESHOLD_USD` down from $10k to $1k (forces
more swaps through Flashbots Protect), or tighten `slippage_tolerance_bps` to 10 bps (more reverts but no realised
sandwich loss).

### Cross-references / prior art

- UAC `CircuitBreakerId` closed set:
  `unified-api-contracts/unified_api_contracts/canonical/crosscutting/circuit_breaker.py:74-143`. No dedicated mempool /
  MEV identifier today — see FOLLOW-UP P1 below.
- UAC `BreakerConfig` carry archetype registry:
  `unified-api-contracts/unified_api_contracts/registry/circuit_breakers/carry_staked_basis.py:34-181` (10 breakers;
  closest analogs `GAS_PRICE_SURGE_GWEI:65-78` + `BATCH_LIVE_DIVERGENCE_BPS:167-180`).
- UAC `BreakerConfig` arbitrage archetype registry:
  `unified-api-contracts/unified_api_contracts/registry/circuit_breakers/arbitrage_price_dispersion.py:80-172`
  (INVENTORY_IMBALANCE_RATIO + HEDGE_GAP_NOTIONAL_USD + REJECT_RATE_BPS + CROSS_VENUE_DIVERGENCE_BPS).
- UAC `RiskRule` archetype seeds: `unified-api-contracts/unified_api_contracts/registry/risk_rules/archetype.py:157-165`
  (carry SLIPPAGE_BUDGET=35bps) + `:327-336` (arb SLIPPAGE_BUDGET=15bps); `SlippageBudgetTrigger` import at line 79.
- UAC `AlertCode` closed set:
  `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/codes.py:42-45` (CB lifecycle) + `:55`
  (`DEFI_TX_SIMULATION_FAILED`) + `:84` (`UNHEDGED_POSITION_ALERT`) + `:134-156` (RISK_RULE_BLOCKED / SCALED_DOWN /
  MONITOR_FIRED / TEST_ONLY_ROUTED) + `:171-184` (KILL_SWITCH_AUTO_RECOVERED / MANUAL_UNKILLED). No literal
  `MEV_SANDWICH_DETECTED` or `MEMPOOL_CONGESTED` — see FOLLOW-UP P2.
- UAC `MevSubmissionMode` internal type: `unified-api-contracts/unified_api_contracts/internal/__init__.py:64` +
  `:1308`; closed set per `mev-protection.md:186-198` (PUBLIC_MEMPOOL / FLASHBOTS_PROTECT / MEV_BLOCKER / MANIFOLD /
  JITO_BUNDLE).
- UAC normalize helpers for MEV bundle results:
  `unified-api-contracts/unified_api_contracts/normalize_utils/onchain.py:58-101` (`normalize_flashbots_bundle_result`,
  `normalize_mev_share_bundle_result`).
- UAC availability semantics for MEV data type:
  `unified-api-contracts/unified_api_contracts/canonical/crosscutting/availability_semantics.py:132`
  (`("defi", "mev_events"): "tick_timestamp"`).
- MEV protection codex SSOT: `unified-trading-pm/codex/04-architecture/mev-protection.md` (full doc — threat model lines
  14-23, MEV-driven breaker trigger lines 376-394, slippage-tolerance lines 42-63, Flashbots Protect lines 65-95,
  per-strategy MEV policy lines 251-292, error codes lines 305-313).
- Execution-service Uniswap live-swap path: `execution-service/execution_service/defi_execution/protocols/uniswap.py`
  `UniswapConnector.swap_exact_input()` (per CLAUDE.md SSOT pointer); SwapRouter02 address
  `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45`.
- Execution-service DeFi error codes: `execution-service/execution_service/defi_execution/protocols/aave.py`
  `DefiErrorCode` (13-code enum); relevant codes for this scenario per `mev-protection.md:305-313`: `SLIPPAGE_EXCEEDED`
  / `TX_REVERTED` / `GAS_PRICE_SPIKE`.
- Execution-service MEV provider factory: `execution-service/execution_service/defi_execution/mev/protection.py`
  `get_mev_provider()`; `private_mempool.py` `PrivateMempoolProvider`; `v2/mev_router.py` `_DEFAULT_POLICIES`.
- DR plan § Phase 1.A + Phase 4 follow-up: `disaster_recovery_circuit_breakers_2026_05_10.md` (NEW breaker registration
  process per `circuit_breaker.py:50-59` + Phase 4 placeholder for non-carry / non-arb breaker additions).
- Risk plan § Phase 1.E + 1.F: `risk_simulations_limits_alerting_2026_05_10.md` (new AlertCode additions + recovery
  wiring).
- DeFi master plan MEV section: `unified-trading-pm/plans/epics/defi_master.md` line 1018 (MEV-leakage as
  audit-followup).
- This plan body (parent scope): `simulation_scenarios_topology_price_shocks_2026_05_09.md` lines 51-103 (compressed
  scope frame — 6 critical-path scenarios; line 73 lists `defi_gas_surge_50x` as the cousin scenario covering gas PRICE,
  this scenario covers gas TIMING) + lines 334-373 (Phase 1 UAC scenario contracts the scenario consumes —
  `ScenarioCategory.OPERATIONAL` + `.DATA_CORRUPTION`, `ScenarioOverlayLayer.ORDER` + `.EVENT`, `ScenarioMutationSpec`
  discriminated-union members `LatencyInject` + `EventDuplicate` + `BookSpoof`, `ScenarioOutcomeAssertion` closed set).
- Historical incidents: Ethereum 2023-Q3/Q4 sandwich-bot domination (eigenphi.io public dataset); Arbitrum 2024-01-15
  sequencer outage (~78 min — public Arbitrum status page record); chronic NFT-mint mempool spikes 2022-2024 (Etherscan
  public mempool charts).

### Composition with `defi_gas_surge_50x`

These two scenarios target **orthogonal axes of the same family of events**: `defi_gas_surge_50x` exercises gas
**price** economics (rebalance becomes uneconomic at 200+ gwei; `GAS_PRICE_SURGE_GWEI` breaker per
`carry_staked_basis.py:65-78`); this scenario exercises gas **timing** (txs sit pending regardless of bid; sandwich risk
grows; cancel-tx race; inventory imbalance on the arb leg). In real adversarial conditions — NFT-mint storms, post-CPI
liquidation cascades, large memecoin launches — gas-price-surge AND mempool-congestion frequently **co-occur** (the
surge is the SYMPTOM of the congestion + the operator response). The post-cutover Phase 5 matrix (per
`simulation_scenarios_post_cutover_2026_06_01.md` successor plan) SHOULD include a composite scenario
`defi_gas_surge_50x + defi_mempool_congestion_inclusion_delay` exercising both simultaneously to verify (a) breaker
non-double-firing (the operator sees ONE alert per logical event, not two competing per-symptom alerts), (b)
recovery-curve interaction (gas decays faster than mempool clears, or vice versa, depending on the trigger), (c)
`MEV_PROTECTION_THRESHOLD_USD` policy interaction with cancel-tx race economics. **Pre-cutover compressed scope** keeps
this scenario standalone — the composite is captured as a Phase 4 follow-up todo in the post-cutover successor plan.

### Follow-up gaps (for parent-agent reconciliation)

- **FOLLOW-UP** P1: UAC `CircuitBreakerId` closed set (`circuit_breaker.py:74-143`) has NO dedicated mempool /
  inclusion-delay / MEV / sandwich breaker today. The scenario relies on `BATCH_LIVE_DIVERGENCE_BPS` +
  `SLIPPAGE_BUDGET_PER_ARCHETYPE` (risk-rule layer) as semantic substitutes, plus `INVENTORY_IMBALANCE_RATIO` for the
  arb-leg cascade. Suggested additions to UAC `CircuitBreakerId` enum (per the canonical "adding a new breaker" recipe
  at `circuit_breaker.py:50-59`): (a) `MEMPOOL_INCLUSION_LATENCY_SECONDS` (scope=PER_ASSET_GROUP, applies_to="defi",
  threshold=120s mainnet / 60s arb-specific, action=BLOCK_NEW, AUTO_COOLDOWN, cooldown=120s); (b)
  `MEV_SANDWICH_LOSS_BPS` (scope=PER_ARCHETYPE, applies_to per-archetype, threshold=30bps, action=SCALE_DOWN,
  AUTO_COOLDOWN, cooldown=300s) WITH an override condition for MANUAL_UNKILL after 3 consecutive MEV_DETECTED events in
  1h (repeat-targeting signal). Plan to capture: `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 4 follow-up
  todo.
- **FOLLOW-UP** P2: UAC `AlertCode` closed set (`alerting/codes.py:21-227`) has NO literal `MEV_SANDWICH_DETECTED` /
  `MEMPOOL_CONGESTED` / `TX_PENDING_TIMEOUT` / `INCLUSION_DELAY_BREACH` codes. Scenario uses `RISK_RULE_BLOCKED` /
  `RISK_RULE_SCALED_DOWN` / `RISK_RULE_MONITOR_FIRED` + `DEFI_TX_SIMULATION_FAILED` + (post-FOLLOW-UP P1)
  `CIRCUIT_BREAKER_OPEN` as semantic substitutes. The `MEV_DETECTED` typed event is documented in
  `mev-protection.md:376-389` but is an **internal event** consumed by the breaker state machine, not an emitted
  `AlertCode` for operator-facing alerting. If operator-facing MEV alerts are required (separate from generic
  CIRCUIT_BREAKER_OPEN), propose `MEV_SANDWICH_DETECTED` + `MEMPOOL_CONGESTION_DETECTED` as new alert codes on the next
  `alerting/codes.py` ratchet. Plan to capture: `risk_simulations_limits_alerting_2026_05_10.md` Phase 1.E (alert-code
  closed-set extension).
- **FOLLOW-UP** P2: `codex/04-architecture/autonomous-recovery-matrix.md` named-state taxonomy does NOT include
  `mempool_congested` distinct from `chain_data_stale`. Suggested addition (`mempool_congested` — chain is live +
  responsive but our submitted txs are stuck) since the operator response is materially different (chain-RPC-outage →
  wait + monitor RPC health; mempool-congestion → bid up gas / route to Flashbots / scale down clip size). Plan to
  capture: `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 4 follow-up.
- **FOLLOW-UP** P3: `REJECT_RATE_BPS` breaker (`arbitrage_price_dispersion.py:127-140`) is currently seeded ONLY for
  `ARBITRAGE_PRICE_DISPERSION` archetype, not `CARRY_STAKED_BASIS`. The high-sandwich-loss carry-archetype row in the
  expected-outcomes table assumes pre-flight catches every reverted tx and BLOCK is sufficient; if a pre-flight bypass
  occurs (e.g. simulation fork drift) and on-chain reverts accumulate, there is NO breaker to catch the cascade for
  carry. Suggested follow-up: add `REJECT_RATE_BPS` seed for `applies_to="CARRY_STAKED_BASIS"` with carry-specific
  threshold. Plan to capture: `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 1.A registry-seed expansion.
- **FOLLOW-UP** P3: Verify per-archetype `KillSwitchId` for `KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION` exists in
  `kill_switch.py` closed set — the inventory-imbalance escalation in the arbitrage variant row depends on the named ID.
  If absent, suggested addition. Plan to capture: `risk_simulations_limits_alerting_2026_05_10.md` Phase 1.F kill-switch
  ID registry sweep.
