## Scenario `defi_gas_surge_50x` — Ethereum gas price spike

| Field | Value |
|---|---|
| `scenario_id` | `defi_gas_surge_50x` |
| Category | `PRICE_SHOCK` (gas is a price — the on-chain compute commodity) + `OPERATIONAL` (tx-cost economics / mempool-priority dynamics) |
| Layer | `FEATURE` (gas-oracle feature in features-onchain) + `ORDER` (execution-service tx-submission cost gate) |
| Asset groups | `frozenset({MarketAssetGroup.DEFI})` |
| Applies-to | per-chain — PRIMARY `ethereum_mainnet`; SECONDARY L2s (`arbitrum`, `optimism`, `base`) with attenuated multiplier (~5-15× rather than 50×); TERTIARY `solana` as priority-fee-storm variant (different fee mechanic — `microlamports/CU` rather than gwei) |
| Targets archetype(s) | `carry_staked_basis` (PRIMARY — Solana LST rebalance economics + any Ethereum-LST extension; gas-budget rule already explicit per `registry/risk_rules/archetype.py:169-181`); `ARBITRAGE_PRICE_DISPERSION` (SECONDARY — cross-chain hedge leg expensive when CeFi-perp ↔ DeFi-spot arb requires DeFi-side tx submission); both archetype rules + DeFi asset-group rule fire concurrently |

### Real-world referent

Ethereum mainnet has shipped multiple high-gas episodes that directly compressed or inverted DeFi-strategy economics: **2021-05** NFT-mint gas wars (sustained 300-600 gwei across the Beeple / OpenSea boom; spot spikes to 1500+ gwei during specific drops); **2022-Q4 LUNA / FTX-collapse week** (300-400 gwei sustained as on-chain liquidation cascades + stablecoin de-pegs drove panic exits through Uniswap); **2024-Q1 memecoin / Friend.Tech storms** (200-400 gwei intermittent); plus **Solana 2024-Q1 mint-storm priority fees** (~0.01-0.05 SOL/tx — orders of magnitude above the baseline ~0.000005 SOL — driven by `pump.fun` token launches). For a strategy whose carry yield is ~3-8% APR, a 50× gas spike on a rebalance tx makes the rebalance unprofitable for hours; the worst case is rebalances queued during the spike landing post-spike with stale slippage assumptions. This scenario captures the worst envelope: instantaneous 50× spike, 10min sustained, then operator-chosen recovery curve.

### Trigger condition (synthetic injection)

At wall-clock `T+N` seconds (`N` = scenario start offset, default 60):

- features-onchain gas-oracle feature for the targeted chain (`eth_mainnet_gas_price_gwei` / `arbitrum_l2_gas_price_gwei` / `solana_priority_fee_microlamports`) jumps from operator-supplied `baseline_gwei` (default 30 gwei for Ethereum; 0.1 gwei for L2; 5000 microlamports/CU for Solana priority-fee variant) to `baseline_gwei * surge_multiplier` (default 50× → 1500 gwei for Ethereum).
- Spike sustained for `surge_duration_seconds` (default 600s = 10min).
- Recovery follows operator-selected curve: `step` (instant drop to baseline at `T + N + surge_duration_seconds`), `linear_300s` (linear ramp baseline-ward over 300s post-surge-end), or `exponential_decay_300s` (half-life ~75s).
- Derived features (`tx_cost_estimate_usd` per pending rebalance instruction, `gas_priority_percentile_rank`) recompute correspondingly — gas-budget rule consumes `tx_cost_estimate_usd` directly.
- Tenderly fork stays live throughout — tx-submission still works mechanically (the fork honours real gas pricing), but the **pre-flight gas-budget check should BLOCK before submission**. If the harness observes any tx land at 1500-gwei pricing, the breaker / risk-rule chain has failed and we have a regression.
- Mempool-side: synthetic gas-oracle ingestion is the only injection point; we do NOT synthesise pending-tx noise. The strategy reacts to the oracle, not to mempool inspection.

### Observable signature (in event stream + dashboards)

- features-onchain emits gas-oracle rows with `gas_price_gwei` jumping discontinuously at `T + N`; manifest writer captures successive `record_captured()` rows showing the surge envelope.
- Risk-rule evaluator fires `RISK_RULE_BLOCKED` (per archetype-level `GAS_BUDGET_PER_ARCHETYPE` rule, `consequence=BLOCK`) for `carry_staked_basis` within one rule-evaluation cycle (~10s) of any pending rebalance hitting the cost ceiling.
- Concurrently `RISK_RULE_SCALED_DOWN` fires at the DeFi-asset-group rule (`registry/risk_rules/asset_group.py:74-82`, `consequence=SCALE_DOWN`, USD 500 ceiling) — different scope, different consequence, both fire.
- Circuit-breaker `GAS_PRICE_SURGE_GWEI` trips at `T + N + ~10s` (per `registry/circuit_breakers/carry_staked_basis.py:65-78`, threshold 200 gwei, `action=BLOCK_NEW`) — alert `CIRCUIT_BREAKER_OPEN` follows.
- execution-service tx-submission queue accumulates `tx_submission_suppressed` events; rebalance-tx submission rate drops to zero for `carry_staked_basis` on the affected chain.
- position-balance-monitor-service reports "pending rebalance suppressed — gas budget exceeded" against open LST positions; existing positions held untouched (no liquidation pressure from this scenario alone).
- Autonomous-recovery transitions `carry_staked_basis` archetype state to `gas_high` (advisory state per DR plan recovery-state taxonomy); state clears when guard condition holds for 3min sustained.
- Alert provenance payload carries `gas_price_gwei` + `tx_cost_estimate_usd` + `baseline_gwei` + `surge_multiplier` per Phase 1.E alert-code provenance contract.

### Mutation spec (UAC `ScenarioMutationSpec`)

- **Mutation types**: `GasSurge` (existing closed-union member per simulation-scenarios Phase 1.B mutation taxonomy) + `PriceShift` (applied to the gas-oracle feature value series — gas IS a price-shaped feature and downstream `tx_cost_estimate_usd` consumes it as a price).
- **Parameters**:
  - `chain: "ethereum_mainnet" | "arbitrum" | "optimism" | "base" | "solana"`
  - `surge_multiplier: int` (default `50`)
  - `surge_duration_seconds: int` (default `600` = 10min)
  - `baseline_gwei: Decimal` (default `Decimal("30")` for Ethereum; chain-conditional default — operator override at sim-time to reflect real conditions when scenario runs)
  - `recovery_curve: "step" | "linear_300s" | "exponential_decay_300s"` (default `step`)
  - `affected_data_types: frozenset({"onchain_gas_oracle", "onchain_tx_cost_estimate"})` (closed-set keys must exist in UAC data_type registry)
- **Pipeline tap layer**: `FEATURE` (gas-oracle feature in features-onchain — the value injection point) + `ORDER` (execution-service pre-flight gas-budget check on tx-submission path).
- **`available_at` discipline**: synthetic gas-oracle rows use real-time `available_at` (gas-price feeds ARE live in production; we're synthesising the VALUE not the arrival timing). No `lookahead_bias_check` downgrade needed — distinct from the RPC-outage scenario where data-arrival is the synthetic axis.

### Expected outcomes (per archetype × per chain)

| Archetype | Chain | `RiskRuleConsequence` | Breaker(s) tripped | `BreakerAction` | `KillSwitchId` armed | `AlertCode` fired | `expected_within` |
|---|---|---|---|---|---|---|---|
| `carry_staked_basis` | `ethereum_mainnet` (rebalance tx — Ethereum LST extension) | `BLOCK` (archetype-level `GAS_BUDGET_PER_ARCHETYPE`, `registry/risk_rules/archetype.py:169-181`, USD 50 ceiling) **+** `SCALE_DOWN` (asset-group-level, `registry/risk_rules/asset_group.py:74-82`, USD 500 ceiling — fires concurrently at coarser grain) | `GAS_PRICE_SURGE_GWEI` (`registry/circuit_breakers/carry_staked_basis.py:65-78`, threshold 200 gwei, `applies_to="CARRY_STAKED_BASIS"`) — **FOLLOW-UP**: breaker is **chain-agnostic** (no per-chain discriminator) so an Ethereum spike + simultaneous Arbitrum spike cross-fire on the same breaker_id | `BLOCK_NEW` (cooldown 180s; recovery via `AUTO_COOLDOWN` per recovery rule at `:196-201`) | none at breaker level (operational, not safety-critical; existing positions unaffected). Escalates to `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` (`kill_switch.py:79`) ONLY if gas-high coincides with `LIQUIDATION_CASCADE_RISK` (HF approaching 1.10) AND rebalance is required to top up collateral — chained-scenario interaction, not solo trip | `RISK_RULE_BLOCKED` (archetype rule) + `RISK_RULE_SCALED_DOWN` (asset-group rule) + `CIRCUIT_BREAKER_OPEN` (`alerting/codes.py:42`) — **FOLLOW-UP**: no gas-specific literal alert code in the 45-member set (no `GAS_PRICE_SPIKE` / `GAS_BUDGET_EXCEEDED`); scenario uses `RISK_RULE_BLOCKED` + breaker `CIRCUIT_BREAKER_OPEN` with `breaker_id=GAS_PRICE_SURGE_GWEI` in provenance as the semantic substitute | 10s (pre-flight check is synchronous; breaker eval cadence ≤ 10s) |
| `carry_staked_basis` | `solana` (LST rebalance via Marinade / Jito) | `BLOCK` (archetype rule fires on Solana priority-fee variant — USD 50 ceiling translates roughly to priority-fee `>10,000,000` microlamports/CU at SOL = $150). Note: Solana base fees are trivially small (~$0.0001/tx); only the priority-fee-storm variant approaches the budget ceiling | `GAS_PRICE_SURGE_GWEI` (same breaker_id; chain-agnostic registry — Solana priority-fee normalised to gwei-equivalent USD-cost for the trip check) — **FOLLOW-UP**: per-chain breaker disambiguation needed for Solana priority-fee specifically; current registry conflates gwei + microlamports under the gwei label | `BLOCK_NEW` (cooldown 180s) | none | `RISK_RULE_BLOCKED` + `CIRCUIT_BREAKER_OPEN` | 10s |
| `ARBITRAGE_PRICE_DISPERSION` | `ethereum_mainnet` (cross-chain hedge leg requiring DeFi-side tx) | `SCALE_DOWN` (DeFi asset-group rule, USD 500 ceiling). Note: the archetype's own gas-budget rule applies only to `CARRY_STAKED_BASIS` in current registry seed — **FOLLOW-UP**: `ARBITRAGE_PRICE_DISPERSION` needs its own `GAS_BUDGET_PER_ARCHETYPE` seed once cross-chain DeFi legs come online | `GAS_PRICE_SURGE_GWEI` — **FOLLOW-UP**: same chain-agnostic gap as above; ALSO no `applies_to="ARBITRAGE_PRICE_DISPERSION"` seed in the breaker registry, so cross-archetype escalation is currently implicit not coded | `BLOCK_NEW` (when seeded) | none | `RISK_RULE_SCALED_DOWN` + `CIRCUIT_BREAKER_OPEN` | 10s |

### Auto-recovery contract (per DR plan `BreakerRecoveryRule`)

Per `registry/circuit_breakers/carry_staked_basis.py:196-201` for `GAS_PRICE_SURGE_GWEI`:

- `guard_description`: `"L1 gas < 150 gwei sustained for 3min."` (existing registry value — guard is roughly 5× the baseline-30-gwei case; for the scenario's 30-gwei baseline this means "back within 5× of baseline").
- `retry_policy`: `"linear"` (steady cadence; gas-price is mean-reverting on minutes-timescale so linear retry is appropriate — no need for exponential backoff).
- `auto_disarm_after_seconds`: `180` (hard cap on armed state).
- `recovery_mode`: `auto_cooldown` (operational class; no manual-unkill required — DR plan policy reserves `MANUAL_UNKILL` for safety-critical breakers like `LIQUIDATION_CASCADE_RISK` and `POSITION_LIMIT_EXCEEDED`).

`KILL_ALL` never escalates from this scenario in isolation — gas-spike is operational, not safety-critical, and existing positions are not in danger from gas alone. Operator override path: if elevated-but-survivable gas persists past the auto-disarm cap (e.g. multi-hour congestion) and a rebalance is required for collateral health, operator can route the rebalance through `RISK_RULE_TEST_ONLY_ROUTED` (per `alerting/codes.py:156`) — the rule's test-only route bypasses BLOCK while preserving audit trail.

### Cross-references / prior art

- UAC `BreakerConfig` entry: `unified-api-contracts/unified_api_contracts/registry/circuit_breakers/carry_staked_basis.py:65-78` (`GAS_PRICE_SURGE_GWEI` config) + `:196-201` (recovery rule).
- UAC `CircuitBreakerId` definition: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/circuit_breaker.py:106` (`GAS_PRICE_SURGE_GWEI`).
- UAC archetype-level gas-budget `RiskRule`: `unified-api-contracts/unified_api_contracts/registry/risk_rules/archetype.py:169-181` (`carry_staked_basis`, `GasBudgetTrigger(budget_usd=Decimal("50"))`, `BLOCK`).
- UAC asset-group-level gas-budget `RiskRule`: `unified-api-contracts/unified_api_contracts/registry/risk_rules/asset_group.py:74-82` (`defi`, `GasBudgetTrigger(budget_usd=Decimal("500"))`, `SCALE_DOWN`).
- UAC `AlertCode` closed set: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/codes.py:42` (`CIRCUIT_BREAKER_OPEN`) + `:134` (`RISK_RULE_BLOCKED`) + `:144` (`RISK_RULE_SCALED_DOWN`) + `:156` (`RISK_RULE_TEST_ONLY_ROUTED`).
- UAC `KillSwitchId`: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/kill_switch.py:79` (`KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS`).
- DR plan § Phase 1.A + 1.B: `disaster_recovery_circuit_breakers_2026_05_10.md` (BreakerConfig / BreakerRecoveryRule SSOT + `GasSurge` mutation taxonomy).
- Risk plan § Phase 2.E: `risk_simulations_limits_alerting_2026_05_10.md` (DeFi-asset-group gas-budget rule wiring + `GasBudgetTrigger` shape).
- DeFi simulation-realism plan: `defi_simulation_realism_2026_05_10.md` (gas-modelling SSOT — baseline-gwei distribution per chain + percentile-rank methodology).
- Parent plan slot: `simulation_scenarios_topology_price_shocks_2026_05_09.md:69` (compressed-scope listing) + `:466` (Phase 4.B DeFi scenario enumeration).
- CLAUDE.md SSOT pointer: "DeFi pipeline flow: instruments-service → MTDS → features-onchain → strategy → execution" — gas-oracle lives in features-onchain step.
- Historical incidents: Ethereum 2021-05 NFT-mint gas wars (300-600 gwei sustained); 2022-Q4 LUNA-collapse cascade; 2024-Q1 memecoin storms; Solana 2024-Q1 `pump.fun` priority-fee storms.

### Follow-up gaps (for parent-agent reconciliation)

- **FOLLOW-UP** P1: UAC `GAS_PRICE_SURGE_GWEI` breaker is **chain-agnostic** (`applies_to="CARRY_STAKED_BASIS"` only, no `chain` discriminator). Ethereum + Arbitrum + Solana priority-fee storms all trip the same breaker_id. Scenario harness cannot assert chain-specific firing without registry extension. Suggested: add `chain` key to `BreakerConfig.applies_to` (structured like `archetype:CARRY_STAKED_BASIS,chain:ethereum_mainnet`) once Phase 4 audit confirms granularity needs. Plan to capture: `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 4 follow-up.
- **FOLLOW-UP** P1: No `applies_to="ARBITRAGE_PRICE_DISPERSION"` seed for `GAS_PRICE_SURGE_GWEI` breaker AND no archetype-level `GAS_BUDGET_PER_ARCHETYPE` rule for `ARBITRAGE_PRICE_DISPERSION` — cross-archetype gas economics is currently DeFi-asset-group-rule-only. Plan to capture: `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 1.A + `risk_simulations_limits_alerting_2026_05_10.md` Phase 2.E.
- **FOLLOW-UP** P2: `AlertCode` closed set has no literal `GAS_PRICE_SPIKE` / `GAS_BUDGET_EXCEEDED` (verified — 45-member grep). Scenario uses `RISK_RULE_BLOCKED` + `CIRCUIT_BREAKER_OPEN` with `breaker_id=GAS_PRICE_SURGE_GWEI` in provenance as the semantic substitute. If gas-specific routing matters (e.g. dedicated gas-spike PagerDuty channel), propose `GAS_PRICE_SPIKE` as a new alert code on the next `alerting/codes.py` ratchet. Plan to capture: `risk_simulations_limits_alerting_2026_05_10.md` Phase 1.E.
- **FOLLOW-UP** P2: Solana priority-fee storm normalisation to gwei-equivalent USD-cost for the gas-budget trip check is currently implicit — features-onchain must compute `tx_cost_estimate_usd` uniformly across chains so the USD-50 archetype ceiling fires consistently. Confirm `tx_cost_estimate_usd` data_type contract handles microlamports → USD conversion. Plan to capture: `defi_simulation_realism_2026_05_10.md` gas-modelling phase.
