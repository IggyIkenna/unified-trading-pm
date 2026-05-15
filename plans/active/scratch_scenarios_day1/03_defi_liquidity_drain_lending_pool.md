## Scenario `defi_liquidity_drain_lending_pool` — Aave/Morpho utilization spike → borrow cap → governance pause

| Field                | Value                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario_id`        | `defi_liquidity_drain_lending_pool`                                                                                                                                                                                                                                                                                                                                                                                        |
| Category             | `VENUE_OUTAGE` (per-protocol pause variant) + `TOPOLOGY_GAP` (utilization-driven borrow-cap variant). Modelled as a single scenario with two parameterised sub-shapes (`pause_mode="governance_paused"` vs `pause_mode="borrow_cap_reached"`) — both share the same observable signature on the deleverage path.                                                                                                           |
| Layer                | Primary `ScenarioOverlayLayer.FEATURE` (synthetic lending-indices feature row injects 99% utilization on `(protocol, chain, asset)`); secondary `ScenarioOverlayLayer.ORDER` (execution-service Tenderly-fork `borrow()` simulation reverts with `BorrowCapExceeded` / `PoolPaused`); tertiary `ScenarioOverlayLayer.MANIFEST` (`ManifestPhantom` injects high-utilization row at outage-time `available_at`). Three taps. |
| Asset groups         | `frozenset({MarketAssetGroup.DEFI})`                                                                                                                                                                                                                                                                                                                                                                                       |
| Applies-to           | per-protocol (closed-set: `aave_v3` / `morpho`) × per-chain (`ethereum` / `arbitrum`) × per-borrow-asset (`USDC` / `USDT`). Single `(protocol, chain, asset)` triple per run; matrix variants run all 8 combinations.                                                                                                                                                                                                      |
| Targets archetype(s) | `CARRY_STAKED_BASIS` (primary — deleverage path relies on USDC/USDT borrow availability on the LST-collateral pool; cannot rebalance leverage if borrow is blocked). `ARBITRAGE_PRICE_DISPERSION` is NOT directly affected (funding-arb does not hold lending positions).                                                                                                                                                  |

### Real-world referent

Models three recurring failure modes from 2023-2024: (1) **Aave V3 2023-11 BUSD utilization spike** during the Curve /
CRV-pool exploit — a whale borrowed against CRV collateral, drove BUSD-borrow utilization to ~98%, and downstream
borrowers faced 0.5%/day borrow APR for ~48h before governance intervened. (2) **Morpho 2024-03 Compound-fork governance
pause** — a community-vote `pause()` triggered after an oracle-attack vector was disclosed; the pool went `paused=true`
for ~6h with no new borrows + no liquidations, leaving leveraged-borrowers' deleverage paths broken. (3) **Aave V3
2024-Q4 ETH-borrow cap on Arbitrum** — pre-emptive governance cap reduction in anticipation of an oracle attack;
borrowAmount > availableCap returns `BORROW_CAP_REACHED` revert at the contract level, not a pool-pause. Sub-shapes
(1)+(3) share `borrow_cap_reached`; (2) shares `pool_paused`. All three break the `carry_staked_basis` deleverage
contract in the same way: cannot reduce leverage in response to oracle / depeg / drawdown shocks.

### Trigger condition (synthetic injection)

At wall-clock `T+0`, for the chosen tuple `(protocol, chain, asset)` ∈ {(`aave_v3`,`ethereum`,`USDC`),
(`aave_v3`,`arbitrum`,`USDC`), (`morpho`,`ethereum`,`USDC`), …} the harness simultaneously:

1. **FEATURE-layer tap (Phase 3.C)**: injects a synthetic lending-indices feature row via `features-onchain` adapter
   post-processing — `utilization=0.99`, `available_liquidity_usd=0`, `borrow_apr_bps=5000`,
   `paused=<bool depending on pause_mode>`, `available_at` set to outage-start (NOT read-time — preserves `Live = batch`
   discipline per CLAUDE.md and Phase 2.E `lookahead_bias_check(scenario_overlay_active=True)`).
2. **ORDER-layer tap (Phase 3.E)**: configures execution-service matching-engine adversarial-mode
   `RejectFills(reason="BORROW_CAP_REACHED" | "POOL_PAUSED", protocol=<protocol>, chain=<chain>)` for any borrow tx
   targeting `(protocol, chain, asset)`. Tenderly-fork simulation returns the revert deterministically per
   `codex/04-architecture/tenderly-execution-provider.md`.
3. **MANIFEST-layer tap (Phase 3.G)**: writes a `ManifestPhantom` row in the features-onchain availability manifest
   stamped `scenario_id=defi_liquidity_drain_lending_pool` so downstream consumers see the synthetic row's
   `available_at` semantics.
4. After `pause_duration_seconds` (parameterised, default 1800s; matrix variants 600 / 1800 / 21600), reverses:
   utilization decays linearly back to baseline over `recovery_curve_seconds` (default 300s for borrow-cap variant,
   instant for governance-unpause), borrow simulations resume.

The injection is correlation-id-tagged `synthetic=true` per UAC scenario contract. Both `pause_mode` sub-shapes run in
the matrix because they have DIFFERENT auto-recovery contracts (see § Auto-recovery below).

### Observable signature (in event stream + dashboards)

- `DEFI_AAVE_UTILIZATION_SPIKE` (`codes.py:50`) fires from features-onchain lending-indices monitor within ~15s of the
  synthetic utilization row crossing the 95% threshold. Severity HIGH.
- `DEFI_FEATURE_STALE` (`codes.py:52`) **does NOT** fire — the feature row is fresh, the utilization metric is just
  at-cap. Asserting absence is part of the scenario's correctness check.
- Borrow-tx simulation failure rate on the Tenderly fork: `DEFI_TX_SIMULATION_FAILED` (`codes.py:55`) fires after 3
  consecutive failed `borrow()` simulations targeting the affected `(protocol, chain, asset)`. Severity WARN.
- Strategy-service deleverage-path planner: emits a structured `deleverage_blocked` log + lifecycle event
  `INSTRUCTION_REJECTED_RISK` with `reject_reason="lending_pool_unavailable"`. Strategy's deleverage state machine
  transitions to `borrow_blocked` (autonomous-recovery state from
  `codex/04-architecture/autonomous-recovery-matrix.md`).
- features-onchain availability manifest: `record_failed(LendingPoolPausedError, attempted_at=...)` for the affected
  `(protocol, asset)` partition when `pause_mode="governance_paused"`; `record_captured()` with `paused=true` +
  `utilization=0.99` payload when `pause_mode="borrow_cap_reached"` (data IS captured, the pool just isn't usable). The
  asymmetry matters — the manifest contract for governance pause is different from utilization spike per honest-absence
  categories in CLAUDE.md.
- Pre-flight rejection: subsequent `carry_staked_basis` rebalance instructions hit `MAX_LEVERAGE_PER_ARCHETYPE`
  (`registry/risk_rules/archetype.py:115-126`, `SCALE_DOWN`, WARN) — because the deleverage path is blocked, the planner
  CANNOT scale down to fit the 3.5× cap. Sequential instructions accumulate; consecutive `RISK_RULE_SCALED_DOWN`
  (`codes.py:144`) emissions on the same archetype escalate via the breaker BLOCK-rate path (per `risk_rule.py` § 7 SSOT
  reconciliation seam).
- After `pause_duration_seconds > 600s`, `LIQUIDATION_CASCADE_RISK`
  (`registry/circuit_breakers/carry_staked_basis.py:109-124`) trips IF the LST oracle moves > 2% during the pause window
  (since deleverage was the planned response to any oracle move). Severity CRITICAL; action `KILL_ALL`; arms
  `KILL_SWITCH_DEFI_LIQUIDATION_RISK` (`codes.py:32`) per `kill_switch.py:74-93`.
- Provenance always includes `protocol_id` + `pool_address` (the Aave pool contract or Morpho market id) in the alert
  payload so dashboards can drill down per-pool.

### Mutation spec (UAC `ScenarioMutationSpec` discriminated-union composition)

- Mutation types (composite — three taps):
  `ManifestPhantom(scenario_id=defi_liquidity_drain_lending_pool, capture_status=captured|attempted_failed)` (MANIFEST
  layer) + custom `LendingFeatureSpike(utilization=0.99, paused=<bool>)` on FEATURE layer +
  `RejectFills(reason="BORROW_CAP_REACHED" | "POOL_PAUSED")` on ORDER layer. **Phase 4 follow-up
  (Capture-Discoveries)**: `LendingFeatureSpike` is NOT a member of the Phase 1.B closed-union
  (`DropRows | StaleHold | PriceShift | BookSpoof | LatencyInject | RejectFills | OracleDeviate | GasSurge | ManifestPhantom | EventDrop | EventDuplicate`
  per parent plan body lines 343-345). **Decision**: model as
  `PriceShift(field="utilization", target_value=0.99) + PriceShift(field="paused", target_value=1.0)` composed on the
  lending-indices feature row. Successor plan `simulation_scenarios_post_cutover_2026_06_01.md` Phase 1.B extension
  should add a first-class `LendingFeatureSpike` mutation for cleaner semantics.
- Parameters:
  - `protocol: Literal["aave_v3", "morpho"]`
  - `chain: Literal["ethereum", "arbitrum"]`
  - `asset: Literal["USDC", "USDT"]`
  - `pause_mode: Literal["governance_paused", "borrow_cap_reached"]` (both run in matrix)
  - `utilization_target: Decimal = Decimal("0.99")`
  - `pause_duration_seconds: int` (matrix: 600 / 1800 / 21600)
  - `recovery_curve: Literal["step", "linear_300s"]` (step = governance-unpause; linear = utilization decay)
  - `lst_oracle_concurrent_move_bps: int = 0` (default 0; matrix variant 200 to trigger LIQUIDATION_CASCADE_RISK
    escalation)
- Pipeline tap layer: primary `ScenarioOverlayLayer.FEATURE` (Phase 3.C) + secondary `ScenarioOverlayLayer.ORDER` (Phase
  3.E matching-engine adversarial) + tertiary `ScenarioOverlayLayer.MANIFEST` (Phase 3.G). Three-layer scenario.
- `available_at` discipline: the synthetic lending-indices row stamps `available_at` to outage-start (NOT read-time).
  Per parent plan Phase 2.E (lines 397-401) the applier MUST stamp `_synthetic_available_at_shift: bool = True` on the
  injected row so UTL `lookahead_bias_check(scenario_overlay_active=True)` downgrades to a structured warning rather
  than raising `LookaheadBiasError`. Strict mode stays ON for all non-overlay paths. The `record_captured` vs
  `record_failed` choice mirrors the honest-absence taxonomy per `codex/02-data/honest-absence-downstream-handling.md`.

### Expected outcomes (per archetype × per pause-mode)

| Archetype                                                               | `pause_mode`         | `RiskRuleConsequence`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Breaker(s) tripped (cite by `breaker_id`)                                                                                                                                                                                                                                                                                           | `BreakerAction`                                     | `KillSwitchId` armed                                                                                                                                                                                                                                                        | `AlertCode` fired                                                                                                                                                                                                                                  | `expected_within`                        |
| ----------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `CARRY_STAKED_BASIS` (entry path)                                       | both                 | `BLOCK` on new leverage entries via `MAX_LEVERAGE_PER_ARCHETYPE` (`registry/risk_rules/archetype.py:115-126`, `SCALE_DOWN` consequence — but the planner cannot satisfy the scaled-down target without a working borrow path → planner pre-empts and BLOCKs) + `MAX_POSITION_SIZE_PER_ARCHETYPE` (`archetype.py:88-100`, `BLOCK`) cross-checks. **FOLLOW-UP**: no `LENDING_POOL_PAUSED` breaker exists in `registry/circuit_breakers/carry_staked_basis.py:34-181` — add `LENDING_POOL_UNAVAILABLE_SECONDS` (PER_ARCHETYPE, applies_to="CARRY_STAKED_BASIS", action=BLOCK_NEW, cooldown_seconds=600) to closed-set `CircuitBreakerId` enum (`canonical/crosscutting/circuit_breaker.py:74-143`) and the registry. Owner: DR plan `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 4 or successor plan extension. | `BLOCK_NEW` (entry path)                                                                                                                                                                                                                                                                                                            | none (existing positions held; new entries refused) | `DEFI_AAVE_UTILIZATION_SPIKE` (≤15s; `codes.py:50`) + `RISK_RULE_BLOCKED` (≤30s; `codes.py:134`) + `DEFI_TX_SIMULATION_FAILED` (≤60s after 3 retries; `codes.py:55`) + `PREFLIGHT_FAILED` (`codes.py:92`) for any borrow-dependent pre-flight that bypasses the rule engine | 60s for full preflight-block timeline                                                                                                                                                                                                              |
| `CARRY_STAKED_BASIS` (deleverage path, oracle move == 0)                | `borrow_cap_reached` | `SCALE_DOWN` proportional unwind via Compound fallback OR partial deleverage from collateral-withdraw-only path; if Compound also paused (matrix sub-variant), escalates to MANUAL_UNKILL                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | **FOLLOW-UP**: no `DELEVERAGE_PATH_BLOCKED` breaker exists — same recommendation as entry-path row. Until shipped, the scenario asserts via the alerting cascade only (no breaker fire); post-FOLLOW-UP the breaker fires with `BreakerAction.SCALE_DOWN`, `recovery_mode=AUTO_COOLDOWN` per `circuit_breaker.py:235-240` defaults. | `SCALE_DOWN` (post-FOLLOW-UP)                       | none (deleverage proceeds at reduced capacity)                                                                                                                                                                                                                              | `DEFI_AAVE_UTILIZATION_SPIKE` + `RISK_RULE_SCALED_DOWN` (≤45s; `codes.py:144`) + `DEFI_TX_SIMULATION_FAILED`                                                                                                                                       | 120s                                     |
| `CARRY_STAKED_BASIS` (deleverage path, oracle move ≥ 200bps concurrent) | `governance_paused`  | `BLOCK` because oracle move triggered planned deleverage but pool is unreachable → cascade to `LIQUIDATION_CASCADE_RISK` if LST oracle deviation pairs with the pool pause                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | `LIQUIDATION_CASCADE_RISK` (`registry/circuit_breakers/carry_staked_basis.py:109-124`, scope=PER_ARCHETYPE, action=KILL_ALL) + `ORACLE_DEVIATION_BPS` (`carry_staked_basis.py:36-50`) on the LST oracle leg                                                                                                                         | `KILL_ALL` (LIQUIDATION_CASCADE_RISK)               | `KILL_SWITCH_DEFI_LIQUIDATION_RISK` (`codes.py:32`) + `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` (`kill_switch.py:79`); escalates to `KILL_ALL_LIVE` (`kill_switch.py:74`) only if the oracle move cascades into other archetypes' books                                       | `DEFI_AAVE_UTILIZATION_SPIKE` + `ORACLE_DEVIATION` + `CIRCUIT_BREAKER_OPEN` (`codes.py:42`) + `KILL_SWITCH_DEFI_LIQUIDATION_RISK` (`codes.py:32`) + `DEFI_HEALTH_FACTOR_CRITICAL` (`codes.py:48`) if any open position's HF approaches liquidation | 300s end-to-end for full kill-switch arm |

### Auto-recovery contract (per DR plan `BreakerRecoveryRule`)

Per-pause-mode contract — both sub-shapes asserted in the matrix:

- **`borrow_cap_reached` (utilization decay):** if the (FOLLOW-UP) `LENDING_POOL_UNAVAILABLE_SECONDS` breaker is added
  with `action=BLOCK_NEW`, defaults give `recovery_mode=AUTO_COOLDOWN` per `circuit_breaker.py:235-240`. Recommended
  `BreakerRecoveryRule`:
  ```
  BreakerRecoveryRule(
      breaker_id=CircuitBreakerId.LENDING_POOL_UNAVAILABLE_SECONDS,
      guard_description="features-onchain utilization < 90% on (protocol, chain, asset) for >= 300s contiguous.",
      retry_policy="linear",
      auto_disarm_after_seconds=600,
  )
  ```
  Scenario asserts auto-disarm + `KILL_SWITCH_AUTO_RECOVERED` (`codes.py` recovery-emission code per
  `BreakerRecoveryMode.AUTO_COOLDOWN` docstring lines 215-220) fires within `recovery_curve_seconds + 600s`.
- **`governance_paused`:** the on-chain `paused=false` event is operator-visible (governance vote tx) but DOES NOT
  guarantee economic safety — the same vector that paused the pool may still be exploitable. Recommended
  `recovery_mode=MANUAL_UNKILL` (override the action-default) — operator must confirm `paused=false` AND verify the
  pause cause cleared before disarming. Per `circuit_breaker.py:254-256` reviewer-rejection rule, this override needs a
  written rationale in the registry seed description: "Governance-pause clear is not the same as economic-safety clear;
  operator must verify root cause."
- **Escalation paths that REQUIRE manual unkill regardless of pause-mode:** if `LIQUIDATION_CASCADE_RISK`
  (`carry_staked_basis.py:109-124`, recovery rule `:214-219`) trips during the pause window, it stays armed until
  operator confirms "positions unwound + health-factors > 1.5 across the book." The auto-disarm of the (FOLLOW-UP)
  lending-pool breaker does NOT cascade-disarm `LIQUIDATION_CASCADE_RISK` (orthogonal recovery per
  `circuit_breaker.py:395-400` `BreakerRecoveryRule` composition note). Scenario asserts `KILL_SWITCH_MANUAL_UNKILLED`
  is the ONLY exit path for the cascade-escalation variant.

### Cross-references / prior art

- UAC `BreakerConfig` for `LIQUIDATION_CASCADE_RISK` (cascade target):
  `unified-api-contracts/unified_api_contracts/registry/circuit_breakers/carry_staked_basis.py:109-124` (PER_ARCHETYPE,
  applies_to="CARRY_STAKED_BASIS", action=KILL_ALL, recovery=MANUAL_UNKILL).
- UAC `BreakerRecoveryRule` for the same: `carry_staked_basis.py:214-219`.
- UAC `BreakerConfig` for `RPC_OUTAGE_SECONDS` (composes when chain RPC also fails during pause):
  `carry_staked_basis.py:51-64`.
- UAC `BreakerConfig` for `GAS_PRICE_SURGE_GWEI` (composes if alt-deleverage path requires high-priority tx):
  `carry_staked_basis.py:65-78`.
- UAC `BreakerConfig` for `MANIFEST_PHANTOM_RATE_BPS` (composes via MANIFEST-layer tap): `carry_staked_basis.py:153-166`
  (scope=PER_ASSET_GROUP, applies_to="defi", action=BLOCK_NEW, cooldown_seconds=3600).
- **FOLLOW-UP (Capture-Discoveries P1)**: add `LENDING_POOL_UNAVAILABLE_SECONDS` to `CircuitBreakerId` closed-set enum
  (`canonical/crosscutting/circuit_breaker.py:74-143`) + `BreakerConfig` + `BreakerRecoveryRule` entries in
  `registry/circuit_breakers/carry_staked_basis.py:34-244`. Owner: DR plan
  `disaster_recovery_circuit_breakers_2026_05_10.md` Phase 4 (preferred) or successor plan
  `simulation_scenarios_post_cutover_2026_06_01.md` Phase 1.E extension if DR plan is locked.
- **FOLLOW-UP (Capture-Discoveries P2)**: add `LENDING_POOL_PAUSED` + `LENDING_BORROW_CAP_REACHED` to `AlertCode`
  closed-set (`canonical/crosscutting/alerting/codes.py:47-55` DeFi-specific section). Current closest match is
  `DEFI_AAVE_UTILIZATION_SPIKE` (`codes.py:50`) which conflates utilization-spike + cap-reached. Per `codes.py:25-29`
  adding a new code requires (1) enum append, (2) `AlertRule` in `LIVE_ALERT_RULES`, (3) operator playbook in
  `codex/15-runbooks/alerting/`, (4) inclusion in next quarterly rehearsal. Owner:
  `alerting_service_live_rules_2026_05_07.md` extension.
- DR plan `disaster_recovery_circuit_breakers_2026_05_10.md` § Phase 1.B (BreakerAction closed-set) + Phase 1.C-D
  (KillSwitchId 4-set per `kill_switch.py:74-92`) — all shipped.
- Risk plan `risk_simulations_limits_alerting_2026_05_10.md` § Phase 2.A ArchetypeRules:
  `registry/risk_rules/archetype.py:87-250` (12 rules for `CARRY_STAKED_BASIS`; this scenario exercises
  `MAX_LEVERAGE_PER_ARCHETYPE` SCALE_DOWN + `MAX_POSITION_SIZE_PER_ARCHETYPE` BLOCK + `GAS_BUDGET_PER_ARCHETYPE` BLOCK
  when high-priority deleverage tx is attempted at `:170-181`).
- defi_recursive_borrow plan `defi_recursive_borrow_archetypes_2026_05_10.md` — Family 1 (LST-leverage) + Family 2
  (stablecoin-leverage) both depend on lending-pool borrow availability for deleverage; protocol governance pause is a
  documented Family-1 + Family-2 shared shock mode (per plan body — paused / utilization / borrow_cap vocabulary). This
  scenario is the synthetic-simulation analogue of the live shock those archetypes were designed to survive.
- defi_master plan `defi_master_2026_05_07.md` — sources `lending_indices` data_type from features-onchain; this
  scenario's FEATURE-layer tap injects into that exact emission path.
- features-onchain lending-indices source: `features-service/features_service/onchain/lending_indices/` (per
  `defi_master` references; scenario harness must register `ScenarioOverlayApplier` for the `FEATURE` layer at the
  lending-indices adapter exit per parent plan Phase 3.C).
- Tenderly-fork execution provider: `codex/04-architecture/tenderly-execution-provider.md` — the ORDER-layer tap (Phase
  3.E) uses the existing Tenderly-fork integration to return `BORROW_CAP_REACHED` / `POOL_PAUSED` reverts
  deterministically.
- Autonomous-recovery matrix: `codex/04-architecture/autonomous-recovery-matrix.md` — `borrow_blocked` is the
  strategy-service state transition triggered by 3 consecutive `DEFI_TX_SIMULATION_FAILED` events on `borrow()` calls;
  documented as a Layer-4 (post-venue-error) classification distinct from this scenario's Layer-2 (pre-flight)
  `RISK_RULE_BLOCKED` consequence per `risk_rule.py:181-219` § 7 SSOT reconciliation.
- Historical incidents modelled: Aave 2023-11 BUSD utilization spike during CRV exploit, Morpho 2024-03 Compound-fork
  governance pause, Aave V3 2024-Q4 ETH-borrow cap reduction on Arbitrum (citations in § Real-world referent above).

**Phase 4 follow-ups (deferred — captured per Capture-Discoveries HARD RULE)**:

- Add `LENDING_POOL_UNAVAILABLE_SECONDS` to `CircuitBreakerId` closed-set + carry_staked_basis registry (owner: DR plan
  Phase 4 or successor).
- Add `LENDING_POOL_PAUSED` + `LENDING_BORROW_CAP_REACHED` AlertCodes (owner:
  `alerting_service_live_rules_2026_05_07.md` extension).
- Add first-class `LendingFeatureSpike` mutation to `ScenarioMutationSpec` closed-union (owner: successor plan
  `simulation_scenarios_post_cutover_2026_06_01.md` Phase 1.B extension).
- Confirm features-onchain lending-indices adapter exposes a `record_failed(LendingPoolPausedError)` path distinct from
  `record_captured(paused=true)` — current honest-absence taxonomy in
  `codex/02-data/honest-absence-downstream-handling.md` § "Reason taxonomy" does not enumerate `LENDING_POOL_PAUSED` as
  an `EMPTY_CONFIRMED_REASONS` member (it's a failure mode, not an honest gap). No change needed if the adapter raises a
  typed exception via `classify_venue_error()`; verification owned by `defi_master_2026_05_07.md` features-onchain
  phase.
