## Scenario `lrt_lending_meltdown_composite` — LRT bridge-exploit / oracle-staleness / Aave-freeze cascade

| Field | Value |
|---|---|
| `scenario_id` | `lrt_lending_meltdown_composite` |
| Category | `COMPOSITE_INCIDENT` (primary — multi-layer failure: issuer + bridge + oracle + lender) + `SYNTHETIC_SUPPLY_INFLATION` (specific to bridge-issued LRT exploit) + `LENDING_PROTOCOL_GUARDIAN_FREEZE` (Aave/Spark Guardian intervention path) |
| Layer | ALL — `RAW_TICK` (oracle + bridge-attestation + queue + market price) + `FEATURE` (cross-source divergence + backing-ratio attestation + lender-state) + `ORDER` (auto-deleverage execution) + `EVENT` (lender-Guardian-freeze + governance-forum signal) |
| Asset groups | `frozenset({MarketAssetGroup.DEFI})` |
| Applies-to | per-LRT × per-(lending-protocol × chain): primary closed-set rsETH × Aave-V3 × {Ethereum, Arbitrum, Mantle, Base, Linea}; secondary applicability ezETH / weETH / similar bridge-issued LRTs on Aave / Spark / Morpho on L2s. Mainnet-issued LSTs (Lido stETH, etherfi weETH-mainnet, Rocket Pool rETH) have lower exposure (no bridge-trust layer) but the secondary-market depeg mechanism still applies. |
| Targets archetype(s) | `CARRY_STAKED_BASIS` (HIGH severity — LRT-leg can become structurally impaired with no exit); `LEVERAGED_FUNDING_ARB` (CRITICAL severity — collateral structurally impaired AND lender freezes withdrawals → maximum-loss scenario). Cutover archetype (2026-05-23) MUST handle this case. |

### Real-world referent — rsETH/Aave April 2026 (composite of 13 + 14 + 15 + 16)

**Chronology (April 18, 2026)**:
- `17:35 UTC` — attacker exploits Kelp DAO LayerZero cross-chain bridge; mints ~116,500 rsETH (~$292M) on destination chains (Mantle, Arbitrum, Base, Linea) with **zero ETH backing on source chain**.
- `17:35 → 17:50 UTC` — attacker deposits unbacked rsETH to Aave V3 on L2s as collateral, borrows ~$190M WETH against it; Aave's rsETH oracle continues quoting **pre-exploit rate** (oracle doesn't know about the bridge exploit; price = primary-issuance rate).
- `17:50 → 19:00 UTC` — secondary-market peg cracks as on-chain detection bots flag the supply inflation; rsETH/ETH DEX prices on L2s drop ~5-15% within 90min; mainnet rsETH holds peg better (different bridge isolation).
- `19:00 UTC` — Aave Guardian freezes rsETH borrow on Arbitrum first; rsETH supply on Mantle backing ratio (real ETH locked vs circulating rsETH on Mantle) falls to **26.46%** = **73.54% haircut** on isolated Mantle balances; uniform-socialised loss would be ~15.12%.
- `19:00 → 05:00 UTC next day` — Guardian completes freezes on remaining chains + freezes adjacent WETH markets (to prevent further borrow-out); aggregate ETH withdrawal pressure on Aave hits **$5.4B in 24h**; Aave TVL drops $26.4B → ~$20B.
- **Bad debt**: $123.7M (socialised across chains) to $230.1M (L2-confined); resolution still in governance May 2026.

**Multi-week aftermath**: Aave Labs liquidates remaining attacker positions early May; $71M ETH in legal limbo via Arbitrum DAO restraining order; new "TEMP CHECK — Post-rsETH Collateral Framework" proposes tier-based LTV reductions + wrap-depth ineligibility limits. Governance forum: `governance.aave.com/t/temp-check-post-rseth-collateral-framework-...`

**Root cause** = synthetic-supply attack invisible to price oracles. Price-based monitoring (Chainlink rsETH/ETH, DEX TWAP) **stayed quiet for the first 75 minutes** while $292M of unbacked collateral entered Aave. Auto-response based on price alone was too late.

### Trigger condition (synthetic injection) — three composed sub-triggers

(a) **`bridge_backing_drift`** — at `T+0`, harness mutates `bridge_reserve_attestation` response (per-chain: ETH locked in source-chain vault vs LRT circulating on destination chain) such that `backing_ratio = locked_eth / circulating_lrt_on_chain` drops from `1.000` to `target_backing_ratio ∈ {0.99, 0.95, 0.50, 0.26}` over `drift_duration_seconds ∈ {30, 300, 1800}`. The drop happens BEFORE any oracle price moves and BEFORE any DEX-pool price moves. This is the early-detection signal — does the system see the supply inflation pre-price?

(b) **`oracle_silent_inflation`** — concurrent with (a), harness keeps oracle (Chainlink rsETH/ETH on L2, primary-issuance-rate API) at pre-exploit rate for `oracle_lag_minutes ∈ {0, 15, 75}` before any update. This tests: does the strategy detect the divergence between bridge-attestation (true backing) and oracle-quoted-price (no-op)?

(c) **`lender_guardian_freeze`** — at `T + freeze_delay_minutes ∈ {30, 90, 360}` after (a), harness emits synthetic `aave.MarketStateChange(market=rsETH, action=freeze)` event + flips `getReserveData.isFrozen=true` for the rsETH market AND adjacent WETH market (the borrow leg). Post-freeze, `aave.repay()`, `aave.withdraw()`, `aave.deposit()` all revert; only `aave.repayWithATokens()` may still work (governance-dependent).

All three sub-triggers `synthetic=true` correlation per Phase 1.B; layer-tap at RAW_TICK + EVENT.

### Observable signature (in event stream + dashboards)

- **`bridge_backing_ratio_<lrt>_<chain>`** RAW_TICK feature (proposed UAC; lives in features-onchain):
  ```
  bridge_backing_ratio = locked_eth_source_chain / circulating_lrt_destination_chain
  ```
  - per-chain (mainnet, Arbitrum, Mantle, Base, Linea) + per-LRT (rsETH, ezETH, weETH-bridged)
  - **Threshold ladder**:
    - `< 0.995 sustained for ≥ 2 blocks` → AlertCode `LRT_BACKING_DRIFT_WARNING`
    - `< 0.990 sustained for ≥ 1 block` → AlertCode `LRT_BACKING_DRIFT_SEVERE` + `AUTO_WITHDRAW_COLLATERAL` (try to pull collateral before lender freezes)
    - `< 0.95` → AlertCode `LRT_BACKING_EXPLOIT_SUSPECTED` + `EMERGENCY_FULL_UNWIND` (deleverage + flatten regardless of slippage cost)
- **`oracle_vs_attestation_divergence_bps`** FEATURE — gap between Chainlink price and bridge-attestation-implied fair value. Crosses 50bps → composite alert.
- **`lender_state_change_event`** EVENT stream — subscription to Aave / Spark / Morpho governance contracts; any `MarketStateChange` / `isFrozen=true` / `LTV_change` / `reserveFactor_change` → emit `AlertCode.LENDER_STATE_CHANGE_DETECTED` within 1 block.
- **`governance_forum_watcher`** EVENT (proposed integration with `governance.aave.com` + `forum.makerdao.com` + Snapshot / Tally) — new thread tagged `incident` / `freeze` / `<lrt-name>` → operator-page alert.
- **Auto-response ladder** (composed from scenarios 13 + 14 + 15 + 16):
  1. Detection: backing_ratio drift OR oracle/attestation divergence
  2. PAUSE_NEW_ENTRIES across affected (lender, lrt, chain) tuple
  3. CLOSE_HEDGE_LEG first (perp short on ETH — cheap to close, no slippage from LRT side)
  4. ATTEMPT_AAVE_WITHDRAW of LRT collateral while withdrawals still open
  5. If withdraw succeeds: SWAP_LRT_TO_ETH via secondary market (accept depeg cost as voluntary slippage)
  6. If withdraw blocked (Guardian froze first): wait for governance resolution; flag position as `IMPAIRED`; remove from active P&L until resolved
  7. PAGE_OPERATOR with full incident chronology + executed actions

### Auto-response policy (proposed for disaster_recovery_circuit_breakers + defi_recursive_borrow_archetypes + carry_staked_basis archetype)

```yaml
trigger_a: bridge_backing_ratio_<lrt>_<chain> < 0.995 for ≥ 2 blocks
action_a: PAUSE_NEW_ENTRIES on this (lrt, chain) tuple across all archetypes
  + emit AlertCode.LRT_BACKING_DRIFT_WARNING
  + start exit-method-decision computation

trigger_b: bridge_backing_ratio < 0.99 OR oracle_vs_attestation_divergence_bps > 50
action_b: BEGIN_UNWIND (composite of scenarios 13 + 15 + 16)
  1. cancel_open_orders(scope=this_lrt_this_chain)
  2. close_perp_hedge_leg (smallest slippage path)
  3. attempt_aave_withdraw(lrt_collateral)
  4. if withdraw succeeds: swap_lrt_to_eth via secondary (accept slippage up to abs(secondary_premium_bps))
  5. if withdraw blocked: flag IMPAIRED; remove from PnL until governance resolves
  + emit AlertCode.LRT_BACKING_DRIFT_SEVERE
  + page_operator(severity=P0)

trigger_c: lender_state_change_event.action=freeze AND lrt_in_our_collateral
action_c: EMERGENCY_FULL_UNWIND
  + same as trigger_b but ALL positions, regardless of size
  + emit AlertCode.LENDER_GUARDIAN_FREEZE_DETECTED
  + page_operator(severity=P0)

trigger_d: governance_forum_watcher fires for active LRT
action_d: PAUSE_NEW_ENTRIES + page operator for human triage (≤ 5min response budget)
  + do NOT auto-unwind on forum signal alone (forum noise is high; require trigger_a/b/c to confirm)
```

### Composes with

- **Scenario 04 `defi_oracle_deviation_30sigma`** — oracle staleness was a critical part of the rsETH timeline. Stale oracle alone wouldn't trigger; needs cross-source divergence check (oracle vs DEX vs attestation).
- **Scenario 13 `execution_slippage_spike`** — secondary-market exit of LRT incurs slippage; this scenario must budget the slippage cost into the exit-method decision.
- **Scenario 14 `borrow_rate_spike`** — post-freeze, Aave raised WETH borrow rates to deter further draws; positions short of WETH bled while waiting for unwind path.
- **Scenario 15 `liquidation_proximity_auto_deleverage`** — primary unwind mechanism; this composite scenario calls scenario 15's auto-deleverage logic.
- **Scenario 16 `lst_unstake_queue_blowup`** — primary LST-side mechanism; backing-drift = structural impairment, often manifesting as secondary-market depeg + queue lockup.

### Key lessons (vs trading-system architecture)

1. **Price-based monitoring is insufficient for synthetic-supply attacks**. Need bridge-reserve-vs-supply attestation feed. Without it, you're blind for the first 60-90 minutes.
2. **Per-chain backing-ratio matters more than uniform-protocol-level metrics**. L2-isolated supply can take 73% haircut while mainnet takes 15%. Risk caps must be per-(lrt, chain), not per-lrt-global.
3. **Treat bridge-issued LRT as a 3-layer trust stack**: issuer (Kelp/Renzo/etherfi) + bridge (LayerZero/native/Wormhole) + lender (Aave/Spark/Morpho). Cap exposure per layer separately.
4. **Auto-response ladder must precede Guardian freeze**. By the time Aave Guardian froze (1.5h after exploit), withdrawals were already blocked. Pre-freeze unwind path is the only safe path.
5. **Governance-forum watching is a real signal** (operator-page only, not auto-action) — Aave Snapshot threads tagged `<lrt-name>` started 30-90 minutes before formal Guardian action.
6. **Mainnet-issued LRTs have lower exposure** than bridge-issued L2 variants. Materially different risk; treat as different assets in UAC `LRT_RISK_TIERS` registry.

### Open questions

- **Bridge-attestation feed source per (lrt, chain)** — does a reliable feed exist for rsETH source-chain locked ETH? For ezETH? For weETH? **DEFERRED-TO-PHASE-2-IMPL** — needs research + integration plan. Probable answer: build it in-house from on-chain reads of the bridge contracts; do NOT trust issuer-published metrics.
- **`LRT_RISK_TIERS` UAC registry** — propose tiered structure: Tier 1 (mainnet-issued, single-sig issuer) / Tier 2 (mainnet + multi-sig + audit) / Tier 3 (bridge-issued L2 + multi-sig) / Tier 4 (bridge-issued L2 + experimental). Per-tier caps + per-tier max-LTV. Defer to `defi_recursive_borrow_archetypes` Phase 2 follow-up.
- **`auto_deleverage` test harness** — does the test suite exercise the trigger_b unwind path in mock-mode? If not, propose adding a `tests/integration/test_lrt_meltdown_composite.py` under risk-and-exposure-service that simulates the rsETH timeline + asserts the trigger ladder fires at right thresholds.
- **Governance-forum-watcher integration** — Snapshot + Tally + Discord + X polling. Likely needs a dedicated service or extension of alerting-service. Defer to `disaster_recovery_circuit_breakers` Phase 3.
- **Re-entry policy post-incident** — what's the framework for re-onboarding an LRT after a freeze incident? Needs a separate operator-decision plan post-cutover (similar to Aave's "Post-rsETH Collateral Framework" governance discussion).
