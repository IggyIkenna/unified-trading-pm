## Scenario `defi_chain_rpc_outage_solana` — Solana chain RPC outage (DeFi)

| Field | Value |
|---|---|
| `scenario_id` | `defi_chain_rpc_outage_solana` |
| Category | `VENUE_OUTAGE` (chain-level — Solana RPC blanket fail) |
| Layer | `RAW_TICK` + `EVENT` |
| Asset groups | `frozenset({MarketAssetGroup.DEFI})` |
| Applies-to | per-chain (`solana`) — every Solana protocol + LST simultaneously dark |
| Targets archetype(s) | `carry_staked_basis` (PRIMARY — Solana LST yield base case via Marinade / Jito / Sanctum); `ARBITRAGE_PRICE_DISPERSION` (SECONDARY — any cross-chain perp-hedge leg whose underlying lives on Solana) |

### Real-world referent

Solana mainnet beta has shipped multiple full-chain consensus stalls / RPC blackouts: **2022-09-30** (~4h consensus-stall after bot-driven transaction flood; validators unable to agree on fork choice), **2024-02-06** (~5h outage from a regression in the BPF loader during epoch boundary), plus chronic pre-v2-validator-client cascading RPC overloads where public endpoints returned 429/503 for tens of minutes while consensus continued. Symptom shape varies (consensus-stall vs RPC-overload vs validator-client crash) but downstream effect is identical for our pipeline: **no fresh slot height observable, on-chain price-getter calls timeout, Pyth Solana feeds freeze, lending indices halt**. This scenario captures the worst-case envelope — total RPC unavailability across all configured Solana endpoints in `SOLANA_RPC_TEMPLATES` (UAC `registry/capability_declarations/_defi.py:14`).

### Trigger condition (synthetic injection)

At wall-clock `T+N` seconds (`N` = scenario start offset, default 60):

- All Solana RPC endpoints enumerated in `SOLANA_RPC_TEMPLATES` return `HTTP 503` / `connection-refused` for the entire `outage_duration_seconds` window.
- WebSocket subscription connections (program-account / log subscriptions for Marinade / Jito / Sanctum / Drift) close with `reason='chain-stalled'`; reconnect attempts also fail.
- Slot-height progression freezes at slot `S` for the duration — no new blocks observable; the chain-slot event stream stops emitting `BLOCK_ADVANCED` events.
- Pyth Hermes batch endpoints continue returning data BUT the on-chain Pyth (PythNet → Solana mirror) freezes; freshness checks against on-chain Pyth fail.
- On-chain swap quote calls (Jupiter aggregator / direct Raydium / Orca) timeout. On-chain lending-index reads (Kamino / MarginFi) timeout. Pure REST staking-yield endpoints (Marinade off-chain APR endpoint) keep returning stale-cached values — distinct from the chain truth.

### Observable signature (in event stream + dashboards)

- `BLOCK_ADVANCED` event flatline for Solana — last-slot timestamp gap exceeds `tick_staleness_seconds` (default 300s; tighter 60s for high-frequency LST-rebalance archetype).
- MTDS `LiveConnectivityWatchdog` fires `CONNECTIVITY_GAP_DETECTED` against `(venue="solana-rpc-*", instrument="*")` within 30s of trigger.
- features-onchain stops emitting `onchain_lst_yields` rows; manifest writer records `attempted_failed(error=<rpc-timeout>, attempted_at=...)` per Solana protocol shard (per Honest Absence Category 2 — unexpected upstream-pipeline gap).
- MDPS write-gate fires `TICK_STALENESS` against Pyth Solana feeds for `(SOL, MSOL, JITOSOL, BSOL)`.
- DeFi-specific `DEFI_FEATURE_STALE` fires once features-onchain crosses freshness window without emission.
- Lending-indices manifest gap visible in deployment-UI `defi.onchain` coverage tile.
- On-chain swap execution attempts during outage emit `DEFI_TX_SIMULATION_FAILED` (simulate step times out before submission).
- `CIRCUIT_BREAKER_OPEN` fires for `RPC_OUTAGE_SECONDS` breaker at `T + 60s` (per registry threshold).
- Autonomous-recovery transitions to `chain_data_stale` state in risk-and-exposure-service rule evaluator.

### Mutation spec (UAC `ScenarioMutationSpec`)

- **Mutation types**: `LatencyInject` (∞ — all Solana RPC calls hang past timeout) + `DropRows` (`block_height_progression` event stream stops) + `StaleHold` (on-chain Pyth Solana feed pinned at slot `S` price).
- **Parameters**:
  - `chain: "solana"`
  - `outage_duration_seconds`: scenario-author-overridable; defaults `1800` (30min, worst-case batch backfill window). Secondary curve `step_then_ramp_300s` (instant fail + linear RPC-success-rate recovery from 0 → 100% over 300s) for testing partial-recovery paths.
  - `affected_data_types: frozenset({"onchain_lst_yields", "onchain_pyth_prices", "onchain_swap_quotes", "onchain_lending_indices"})`
  - `affected_protocols: frozenset({"marinade", "jito", "sanctum", "kamino", "drift", "raydium", "orca"})` (per `_defi.py:769-774`)
- **Pipeline tap layer**: `RAW_TICK` (chain price + lending-index feeds) + `EVENT` (chain-slot advancement event).
- **`available_at` discipline**: per Phase 2.E, every Solana-derived row's `available_at` shifts to the outage-recovery wall-clock. UTL `lookahead_bias_check` downgrades to **warning** during the outage window (not error) since data-honesty model treats this as a legitimate upstream gap, not a backtest cheat.

### Expected outcomes (per archetype × per layer)

| Archetype | `RiskRuleConsequence` | Breaker(s) tripped | `BreakerAction` | `KillSwitchId` armed | `AlertCode` fired | `expected_within` |
|---|---|---|---|---|---|---|
| `carry_staked_basis` | `BLOCK` (no Solana RPC ⇒ no new LST-rebalance entries; existing positions held but un-rebalanceable) | `RPC_OUTAGE_SECONDS` (UAC `registry/circuit_breakers/carry_staked_basis.py:51-64`, threshold 60s, `applies_to="CARRY_STAKED_BASIS"`) — **FOLLOW-UP**: no per-chain disambiguation in current registry (single breaker covers any chain the archetype touches). See gap callout below. | `BLOCK_NEW` (cooldown 120s; auto-recover via `AUTO_COOLDOWN` per `BREAKER_RECOVERY_DEFAULTS`) | `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` (kill_switch.py:79) at `T + 60s`; escalates to `KILL_PER_ASSET_GROUP_DEFI` (kill_switch.py:92) if outage > `T + 300s` AND any open LST leverage position has health-factor approaching `LIQUIDATION_CASCADE_RISK` threshold (1.10, per registry:115) without observable refresh path | `CONNECTIVITY_GAP_DETECTED` + `TICK_STALENESS` + `DEFI_FEATURE_STALE` + `CIRCUIT_BREAKER_OPEN` + `KILL_SWITCH_VENUE_DISCONNECT` (semantic match — chain-as-venue from the alerting taxonomy's perspective; no `CHAIN_RPC_FAILED` literal in `AlertCode` closed set) | 60s (Solana data-freshness expectation tighter than CeFi REST polling cadence) |
| `ARBITRAGE_PRICE_DISPERSION` (any DeFi leg whose underlying is Solana-anchored) | `SCALE_DOWN` (reduce position; CeFi perp hedge leg remains tradeable on Bybit / Binance / OKX) | `RPC_OUTAGE_SECONDS` PER_ARCHETYPE (same breaker, different `applies_to` rationale — chain-data dependence) — **FOLLOW-UP**: registry only seeds the breaker for `CARRY_STAKED_BASIS`; cross-archetype escalation matrix needs explicit `applies_to="ARBITRAGE_PRICE_DISPERSION"` seed | `SCALE_DOWN` (cooldown 300s, `AUTO_COOLDOWN`) | none at breaker level (CeFi leg still tradeable; archetype kill-switch withheld until cross-leg divergence widens) | `CONNECTIVITY_GAP_DETECTED` + `TICK_STALENESS` + `CIRCUIT_BREAKER_DEGRADED` | 60s |

### Auto-recovery contract (per DR plan `BreakerRecoveryRule`)

Per `unified_api_contracts/registry/circuit_breakers/carry_staked_basis.py:190-195` for `RPC_OUTAGE_SECONDS`:

- `guard_description`: `"RPC endpoint returns 200 for >= 5 consecutive health checks."`
- `retry_policy`: `"exponential"` (escalating retry delay; standard exponential backoff per UTL `RetryPolicy`).
- `auto_disarm_after_seconds`: `120` (hard cap on armed state for this breaker — if guard goes green within 120s post-outage-clear, breaker auto-disarms and emits `KILL_SWITCH_AUTO_RECOVERED`).

Scenario-specific extension for Solana: validator confirms **chain slot progression resumed at ≥ 2 slots/second AND Pyth on-chain feeds fresh within 30s AND lending-indices manifest captured at least one fresh row** before the auto-disarm is honoured. The first two conditions are the underlying-truth checks; the third is the pipeline-arrival check (data made it through our infra, not just the chain restarted). If outage exceeds `auto_disarm_after_seconds` cap, breaker stays armed past auto-cooldown; operator manual-unkill required.

### Cross-references / prior art

- UAC `BreakerConfig` entry: `unified-api-contracts/unified_api_contracts/registry/circuit_breakers/carry_staked_basis.py:51-64` (RPC_OUTAGE_SECONDS config) + `:190-195` (recovery rule).
- UAC `CircuitBreakerId` definition: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/circuit_breaker.py:104-105` (`RPC_OUTAGE_SECONDS`).
- UAC `KillSwitchId` registry: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/kill_switch.py:79` (per-archetype) + `:92` (per-asset-group DeFi).
- UAC `AlertCode` closed set: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/codes.py:34` (`KILL_SWITCH_VENUE_DISCONNECT`) + `:42-45` (CB lifecycle) + `:52` (`DEFI_FEATURE_STALE`) + `:196-211` (`TICK_STALENESS` + `CONNECTIVITY_GAP_DETECTED`).
- UAC Solana RPC SSOT: `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:14` (`SOLANA_RPC_TEMPLATES`) + `:769-774` (Solana-anchored protocols).
- DR plan § Phase 1.A: `disaster_recovery_circuit_breakers_2026_05_10.md` (BreakerConfig / BreakerRecoveryRule SSOT).
- Risk plan § Phase 1.F: `risk_simulations_limits_alerting_2026_05_10.md` (kill-switch recovery wiring + `GLOBAL_DATA_STALENESS_HALT` rule pattern).
- DeFi master plan: `defi_master_2026_05_07.md` (Pyth-unbanned-for-Solana note + CHAIN_RPC_TEMPLATES SSOT location + Solana outage history).
- CLAUDE.md SSOT pointer: "DeFi pipeline flow: instruments-service → MTDS → features-onchain → strategy → execution".
- Historical incidents: Solana 2022-09-30 (~4h consensus stall) + 2024-02-06 (~5h BPF loader regression) — operator-known dates; both pre-date our pipeline so we have no captured manifest rows from those windows but the failure-mode envelope is well-documented public record.

### Follow-up gaps (for parent-agent reconciliation)

- **FOLLOW-UP** P1: UAC `RPC_OUTAGE_SECONDS` breaker config is **chain-agnostic** (`applies_to="CARRY_STAKED_BASIS"`, no per-chain key). A Solana-specific outage shares the same breaker_id as an Ethereum or Arbitrum outage. If the scenario harness needs to assert Solana-specific firing without cross-firing on a simultaneous Ethereum RPC dip, the breaker registry needs a `chain` discriminator OR a per-chain breaker_id variant. Suggested follow-up: extend `BreakerConfig.applies_to` to a structured key like `archetype:CARRY_STAKED_BASIS,chain:solana` once Phase 4 audit confirms whether the assertion granularity matters for the 12-cell matrix. Plan to capture: `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 4 follow-up todo.
- **FOLLOW-UP** P2: No `applies_to="ARBITRAGE_PRICE_DISPERSION"` seed for `RPC_OUTAGE_SECONDS` in the registry — cross-archetype escalation for the secondary archetype is currently implicit, not coded. Plan to capture: `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 1.A.
- **FOLLOW-UP** P2: `AlertCode` closed set has no literal `CHAIN_RPC_FAILED` / `MARKET_DATA_STALE`. Scenario uses `KILL_SWITCH_VENUE_DISCONNECT` + `TICK_STALENESS` + `DEFI_FEATURE_STALE` as semantic substitutes. If chain-vs-venue distinction matters for routing, propose `CHAIN_RPC_FAILED` as a new alert code on the next `alerting/codes.py` ratchet. Plan to capture: `risk_simulations_limits_alerting_2026_05_10.md` Phase 1.E (alert-code closed-set extension).
