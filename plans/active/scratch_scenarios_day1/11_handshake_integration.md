# Handshake integration shape — `risk_simulations` × `disaster_recovery_circuit_breakers` × `simulation_scenarios`

This section codifies the THREE-PLAN integration seam — what each plan owns, how the contracts compose, and how a
scenario run drives the full lifecycle from `ScenarioOverlay` injection → `RiskRuleFiredEvent` → `BreakerArmedEvent` →
`KillSwitchArmedEvent` → `ScenarioOutcomeResult`.

## Plan-of-record ownership boundaries

| Concern                                                                                       | Owner plan                                                        | Canonical UAC contract                                                                                                   | Status (2026-05-12)                                                          |
| --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| **`ScenarioOverlay` + mutation_spec closed-union**                                            | `simulation_scenarios_topology_price_shocks_2026_05_09` Phase 1.B | `unified-api-contracts/canonical/crosscutting/scenario_overlay.py`                                                       | `todo` (compressed-scope subset: 5 mutations + 3 outcomes)                   |
| **`ScenarioOutcomeAssertion` closed-enum**                                                    | `simulation_scenarios_*` Phase 1.C                                | `unified-api-contracts/canonical/crosscutting/scenario_overlay.py`                                                       | `todo` (compressed-scope subset)                                             |
| **`ScenarioOverlayApplier` + `ScenarioRunner`**                                               | `simulation_scenarios_*` Phase 2                                  | `unified-trading-library/scenario/applier.py` + `runner.py`                                                              | `todo`                                                                       |
| **`RiskRule` + `RiskRuleConsequence` enum**                                                   | `risk_simulations_limits_alerting_2026_05_10` Phase 1.A-D         | `unified-api-contracts/canonical/crosscutting/risk_rule.py`                                                              | ✅ shipped UAC@`945ad5d`                                                     |
| **Per-axis risk-rule registry (≥30 archetype-scope + ≥12 family-scope rules)**                | `risk_simulations_*` Phase 2.A-I                                  | `unified-api-contracts/registry/risk_rules/{archetype,venue,account,client,asset_group,global_rules,strategy_family}.py` | ✅ shipped UAC@`86851ab` + `29d4fe4` + `301882f`                             |
| **`RiskRuleFiredEvent` Pydantic + alerting wire**                                             | `risk_simulations_*` Phase 5                                      | UAC `alerting/codes.py` (`RISK_RULE_BLOCKED` / `RISK_RULE_SCALED_DOWN` / etc)                                            | `todo` (Phase 5 not flipped)                                                 |
| **`risk_preflight(order, context)` API**                                                      | `risk_simulations_*` Phase 3                                      | `unified-trading-library/risk/preflight.py`                                                                              | ✅ shipped UTL@`9b4bcc09`                                                    |
| **`CircuitBreakerId` + `BreakerScope` + `BreakerTrigger` + `BreakerAction` enums**            | `disaster_recovery_circuit_breakers_2026_05_10` Phase 1.A         | `unified-api-contracts/canonical/crosscutting/circuit_breaker.py`                                                        | ✅ shipped UAC@`a7a99b5`                                                     |
| **Per-archetype `BreakerConfig` + `BreakerRecoveryRule` registry (10 + 10 per archetype)**    | `disaster_recovery_*` Phase 1.B                                   | `unified-api-contracts/registry/circuit_breakers/{carry_staked_basis,arbitrage_price_dispersion}.py`                     | ✅ shipped UAC@`a7a99b5`                                                     |
| **`BreakerRecoveryMode` + `BREAKER_RECOVERY_DEFAULTS` SSOT**                                  | `disaster_recovery_*` Phase 1.A                                   | `circuit_breaker.py` (in same file as enums)                                                                             | ✅ shipped UAC@`a7a99b5`                                                     |
| **`KillSwitchId` + `KillSwitchProvenance` + `KillSwitchArmRequest` / `KillSwitchArmedEvent`** | `disaster_recovery_*` Phase 1.C+1.D                               | `unified-api-contracts/canonical/crosscutting/kill_switch.py`                                                            | ✅ shipped UAC@`a7a99b5`                                                     |
| **`KillSwitchBus` (in-process + audit log)**                                                  | `disaster_recovery_*` Phase 2                                     | `unified-trading-library/kill_switch/bus.py`                                                                             | partial — bus exists at HEAD pre-plan; audit log + UAC-event-adoption `todo` |

## Outcome-assertion → expected-state cross-product

For each `ScenarioOutcomeAssertion` category (per `simulation_scenarios_*` Phase 1.C), the scenario harness asserts the
named event was emitted AND the named state transition occurred within `expected_within: timedelta`. This table is the
contract the `ScenarioOutcomeChecker` (UTL Phase 2.B) implements.

| `ScenarioOutcomeAssertion` category | What it asserts                                                           | Cross-plan dependency                                                                                        | Verification surface                                                                                                           |
| ----------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `STRATEGY_HALTED`                   | Signal generator stops emitting on `(archetype, instrument)` within SLA   | risk plan Phase 3.A `risk_preflight` returns BLOCK → strategy-service signal-emit boundary suppresses signal | event stream: absence of new `STRATEGY_SIGNAL_EMITTED` events on the affected axis within `expected_within`                    |
| `STRATEGY_SCALED_DOWN`              | Signal generator emits reduced-size signal on `(archetype, instrument)`   | risk plan Phase 3.A returns SCALE_DOWN with `scale_factor`                                                   | event stream: `STRATEGY_SIGNAL_EMITTED` payload `size_target` ≤ baseline × `scale_factor` within SLA                           |
| `RISK_BREAKER_TRIPPED`              | Named `BreakerConfig` transitions to OPEN or DEGRADED                     | DR plan Phase 1.B registry; specific `breaker_id` cited in scenario expected-outcome                         | event stream: `BREAKER_ARMED` event with matching `breaker_id` within SLA                                                      |
| `ORDER_REJECTED`                    | execution-service refuses order at pre-flight                             | risk plan Phase 4.B `risk_preflight` wire-in OR DR plan Phase 4.B KillSwitchBus subscribe                    | event stream: `ORDER_REJECTED` with `reason` matching expected `RiskRuleConsequence.BLOCK` source                              |
| `ORDER_CANCELLED_ON_STALE`          | Cancellation tx submitted within SLA after staleness signal               | DR plan Phase 3.G order-state reconciler + Phase 4.B KillSwitchBus arm                                       | event stream: `ORDER_CANCELLATION_SUBMITTED` within SLA of the staleness event                                                 |
| `KILL_SWITCH_ARMED`                 | Named `KillSwitchId` armed by named provenance                            | DR plan Phase 1.C+1.D + KillSwitchBus.arm                                                                    | event stream: `KILL_SWITCH_ARMED` event with matching `switch_id` + `provenance=SCENARIO_SYNTHETIC` within SLA                 |
| `ALERT_FIRED`                       | Named `AlertCode` rule evaluates true with `synthetic=true` metadata      | risk plan Phase 1.E AlertCode extensions + alerting-service consumer rule eval                               | event stream: `ALERT_FIRED` event matching code; alerting-service log shows rule eval'd; paging suppressed if `synthetic=true` |
| `PNL_BOUNDED_BY`                    | Per-archetype P&L stays within `[lower_bound, upper_bound]` post-scenario | strategy P&L attribution + position-balance-monitor                                                          | post-run `ScenarioReport.outcome_results`: archetype P&L from execution-service matching engine output within bound            |
| `RECONCILIATION_FLAGGED`            | Named reconciler emits `RECONCILIATION_DRIFT_DETECTED` event              | DR plan Phase 3.A-H reconcilers                                                                              | event stream: reconciler-specific drift event within SLA                                                                       |

## Per-scenario expected-outcome shape (every scenario fragment uses this)

Each of the 10 scenarios authored on Day-1 declares expected outcomes per `(archetype, scenario_variant)` cell. The
harness reads these from the `ScenarioOverlay.expected_outcomes` field (per UAC Phase 1.B) and feeds them to the
`ScenarioOutcomeChecker`. Below the canonical 5-tuple every cell carries:

1. `consequence: RiskRuleConsequence` — what the rule engine should decide for new signals/orders
2. `breaker_id: CircuitBreakerId | None` — which named breaker should trip (None = no breaker expected, e.g. for
   MONITOR/TEST_ONLY consequences)
3. `breaker_action: BreakerAction | None` — what action the tripped breaker emits
4. `kill_switch_id: KillSwitchId | None` — which kill-switch arms (None = no kill-switch escalation)
5. `alert_codes: frozenset[AlertCode]` — closed set of alerts that should fire with `synthetic=true`
6. `expected_within: timedelta` — SLA from injection time to observed state

This 6-tuple is the per-cell payload of the per-archetype regression matrix (Phase 5 of `simulation_scenarios_*`).
Matrix-green = every cell's tuple matches observed events; matrix-red = any cell deviates.

## Per-axis registry handshake (concrete example — `cefi_funding_spike_10x` × `ARBITRAGE_PRICE_DISPERSION`)

Trace the integration through all three plans:

1. **`simulation_scenarios_*` Phase 1.D registry** declares scenario:

   ```python
   CEFI_FUNDING_SPIKE_10X = ScenarioOverlay(
       scenario_id="cefi_funding_spike_10x",
       category=ScenarioCategory.PRICE_SHOCK,
       layer=ScenarioOverlayLayer.FEATURE,
       asset_groups=frozenset({MarketAssetGroup.CEFI}),
       mutation_spec=PriceShift(data_type="funding_rate", target_value_bps=100, baseline_bps=10, duration_seconds=28800),
       expected_outcomes=[
           ScenarioOutcomeAssertion(
               archetype=ArchetypeId.ARBITRAGE_PRICE_DISPERSION,
               consequence=RiskRuleConsequence.BLOCK,
               breaker_id=CircuitBreakerId.ARBITRAGE_PRICE_DISPERSION_FUNDING_COST_BLOWOUT,  # FOLLOW-UP if not in registry
               breaker_action=BreakerAction.BLOCK_NEW,
               kill_switch_id=None,
               alert_codes=frozenset({AlertCode.RISK_RULE_BLOCKED, AlertCode.RISK_RULE_SCALED_DOWN}),
               expected_within=timedelta(seconds=60),
           ),
       ],
   )
   ```

2. **`risk_simulations_*` Phase 2.A registry** declares the matching rule (already shipped UAC@`86851ab`):

   ```python
   FUNDING_COST_CEILING_ARBITRAGE_PRICE_DISPERSION = RiskRule(
       rule_id=RiskRuleId.FUNDING_COST_CEILING,
       scope=RiskRuleScope.PER_ARCHETYPE,
       applies_to=ArchetypeId.ARBITRAGE_PRICE_DISPERSION,
       trigger=FundingCostCeiling(max_funding_rate_bps_per_8h=50),
       consequence=RiskRuleConsequence.BLOCK,
       alerting_severity=AlertSeverity.HIGH,
   )
   ```

3. **`disaster_recovery_*` Phase 1.B registry** declares the matching breaker — **FOLLOW-UP if missing**. The 10 + 10
   breakers per archetype shipped at UAC@`a7a99b5` cover drawdown / leverage / inventory / venue-outage / data-stale
   etc.; whether funding-cost-blowout has dedicated breaker_id needs verification at reconcile time.

4. **Scenario harness flow** (`ScenarioRunner` per UTL Phase 2.D):
   - Step 1: `ScenarioOverlayApplier.apply()` injects 10× funding-rate at FEATURE layer.
   - Step 2: features-service `_compute_funding_features()` emits spiked rate (via Phase 3.C tap of
     `simulation_scenarios_*` — DEFERRED to post-cutover in compressed scope; pre-cutover harness mocks at
     execution-service ingestion).
   - Step 3: strategy-service signal generator queries `risk_preflight(new_signal, context)` per risk plan Phase 3.B.
     The `rule_evaluator` per Phase 3.A iterates applicable rules; `FUNDING_COST_CEILING_ARBITRAGE_PRICE_DISPERSION`
     evaluates `funding_rate_bps > 50` → fires → consequence=BLOCK.
   - Step 4: pre-flight aggregator returns
     `RiskPreflightResult(decision="BLOCK", blocked_by=["FUNDING_COST_CEILING_ARBITRAGE_PRICE_DISPERSION"], composite_reason=...)`.
   - Step 5: strategy-service suppresses signal (no `STRATEGY_SIGNAL_EMITTED` event).
   - Step 6: risk-and-exposure-service emits `RiskRuleFiredEvent` (per risk plan Phase 5.A — DEFERRED pre-cutover;
     ScenarioOutcomeChecker observes pre-flight result directly instead).
   - Step 7: alerting-service consumer rule-eval fires `RISK_RULE_BLOCKED` alert with `synthetic=true` (paging
     suppressed).
   - Step 8: if `FUNDING_COST_CEILING` was wired to escalate via the risk-breaker seam (per `risk-breaker-seam.md` codex
     doc — N consecutive BLOCK consequences within W window), the execution-service circuit-breaker transitions OPEN;
     `BREAKER_ARMED` event emitted. In the compressed-scope dry run, single-firing is the assertion target, not the
     N-consecutive escalation.
   - Step 9: `ScenarioOutcomeChecker.check()` reads event stream + pre-flight result; matches against
     `expected_outcomes` tuple; emits `ScenarioOutcomeResult(pass=true|false, observed=..., expected=...)`.
   - Step 10: `ScenarioReportEmitter` writes per-run report parquet.

## Risk-breaker escalation seam (UAC@`a7a99b5` × per UAC `RISK_TO_BREAKER_ESCALATION_MAP`)

Per `risk_simulations_*` § 7 SSOT reconciliation (Framing 1): `RiskRuleConsequence` ≠ `BreakerAction`; they're
orthogonal layers. The seam:

- Layer 2 (risk-and-exposure-service) — pre-flight rule fires `RiskRuleConsequence` per instruction.
- Layer 4 (execution-service circuit-breaker) — per-venue state-machine tracks failure rate.
- Seam — when N consecutive `RiskRuleConsequence.BLOCK` consequences fire on same `(venue, asset_group, archetype)`
  within window W, risk-controller emits `BREAKER_ESCALATION_REQUESTED` event; execution-service breaker consumes it +
  transitions state per its own state machine.

`RISK_TO_BREAKER_ESCALATION_MAP: dict[(RiskRuleConsequence, int, timedelta), BreakerAction]` is the SSOT for these
thresholds. Risk plan Phase 7.E `codex/04-architecture/risk-breaker-seam.md` documents it; populating the actual
threshold values is Phase 4 of risk plan (cutover-aspirational).

For scenario design (this plan): scenarios assert against BOTH layers when applicable. Per-rule firing assertions are
`RiskRuleFiredEvent` checks; cascade-into-breaker assertions are `BREAKER_ARMED` checks. The harness MUST tolerate
either layer firing alone if the other is not expected; only matrix-cell failures are when BOTH ARE expected and only
one fires.

## Recovery integration (UAC@`a7a99b5` `BREAKER_RECOVERY_DEFAULTS`)

Every scenario's expected `BreakerAction` carries an implicit recovery mode per `BREAKER_RECOVERY_DEFAULTS`:

| `BreakerAction` | Default recovery_mode | Default cooldown_seconds                                           | Implication for scenario assertion                                                         |
| --------------- | --------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| `BLOCK_NEW`     | `auto_cooldown`       | per `BreakerConfig` (varies — e.g. 90s for `VENUE_OUTAGE_SECONDS`) | Assert `BREAKER_RECOVERED` event within cooldown + guard satisfied                         |
| `CANCEL_OPEN`   | `manual_unkill`       | None                                                               | Assert `KILL_SWITCH_MANUAL_UNKILLED` event when scenario harness simulates operator-unkill |
| `SCALE_DOWN`    | `auto_cooldown`       | per `BreakerConfig`                                                | Assert position-resize back to normal within cooldown + guard                              |
| `KILL_ALL`      | `manual_unkill`       | None                                                               | Assert `KILL_SWITCH_MANUAL_UNKILLED` event when harness simulates operator-unkill          |

For scenarios that fire `KILL_ALL`-action breakers (e.g. `cross_asset_flash_crash`, `defi_stablecoin_depeg`
catastrophic-tier), the matrix assertion ENDS when the kill-switch arms; recovery is operator-initiated, not auto.
Matrix-cell PASS requires kill-switch fires correctly; recovery validation is separate (Phase 9 of
`simulation_scenarios_*` covers this on real VMs).

## Open follow-ups discovered across the 10 scenarios

Aggregated `**FOLLOW-UP**` annotations from per-scenario fragments. Resolved in risk plan Phase 2.A/Phase 4 OR DR plan
Phase 1.B OR successor plan `simulation_scenarios_post_cutover_2026_06_01.md`:

| Follow-up                                                                                                                                                         | Owner plan                                                                       | Severity                  |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------------------------- |
| `VENUE_HALTED` AlertCode missing — operators can't distinguish venue-halt from generic data-stale on dashboards                                                   | `alerting_service_live_rules_2026_05_07` Phase 1.E extension                     | P1                        |
| `LENDING_POOL_PAUSED` + `LENDING_BORROW_CAP_REACHED` + `LENDING_UTILIZATION_HIGH` AlertCodes missing                                                              | `alerting_service_live_rules` Phase 1.E                                          | P1                        |
| `MARKET_DATA_STALE` AlertCode literally missing from 45-set — semantic substitute is `TICK_STALENESS` + `DEFI_FEATURE_STALE`                                      | `alerting_service_live_rules` Phase 1.E                                          | P2 (cleanup)              |
| `GAS_PRICE_SPIKE` / `GAS_BUDGET_EXCEEDED` dedicated AlertCodes missing                                                                                            | `alerting_service_live_rules` Phase 1.E                                          | P2                        |
| `KILL_SWITCH_ORACLE_DIVERGENCE` AlertCode missing (parity gap vs `KILL_SWITCH_VENUE_DISCONNECT`)                                                                  | `alerting_service_live_rules` Phase 1.E                                          | P2                        |
| `ORACLE_STALENESS_SECONDS` `CircuitBreakerId` member missing — staleness conflated with deviation under `ORACLE_DEVIATION_BPS`                                    | `disaster_recovery_circuit_breakers` Phase 4 OR successor                        | P1                        |
| `RPC_OUTAGE_SECONDS` breaker is chain-agnostic — no per-chain disambiguation                                                                                      | `disaster_recovery_circuit_breakers` Phase 4                                     | P2                        |
| `ARBITRAGE_PRICE_DISPERSION` `applies_to` seed for `RPC_OUTAGE_SECONDS` missing                                                                                   | `disaster_recovery_circuit_breakers` Phase 1.A extension                         | P2                        |
| `LENDING_POOL_UNAVAILABLE_SECONDS` breaker missing from `CircuitBreakerId` closed-set                                                                             | `disaster_recovery_circuit_breakers` Phase 4 OR successor                        | P1                        |
| `OracleStaleError` / `OracleDeviationError` exception classes likely missing from UTL honest-coverage taxonomy                                                    | `writegate_honest_coverage_endtoend_2026_05_06` Phase 2.A extension OR successor | P1                        |
| First-class `LendingFeatureSpike` + `VenueOutage` mutation members missing from `ScenarioMutationSpec` closed-union (composed via primitives in compressed scope) | successor `simulation_scenarios_post_cutover_2026_06_01.md` Phase 1.B            | P3 (post-cutover cleanup) |
| Solana microlamports → USD normalisation for `GAS_BUDGET_PER_ARCHETYPE`'s USD-50 ceiling needs `tx_cost_estimate_usd` contract confirmation                       | `defi_master_2026_05_07.md` Phase 1.E or features-onchain                        | P2                        |

## Day-2 handshake checkpoint (operator review)

Day-2 noon checkpoint: parent agent slots 7 + 5 cross-side sync:

- Operator confirms which P1 follow-ups land in pre-cutover scope vs successor plan.
- DR slot (Harsh slot 5 candidate or Ikenna successor) commits to closing the missing `CircuitBreakerId` members +
  `BreakerConfig` seeds within Day 2-3 of this cycle.
- alerting slot commits to AlertCode extension by Day 2 EOD.
- This plan body Day-2 PM extends to Phase 5 matrix-runner spec (per CONTINUE prompt "If Phases 1-2 + handshakes close,
  pick up Phase 3 (scenario-runner integration spec) or Phase 4 (per-scenario test fixture set)").

**✅ RESOLVED 2026-05-13 (UAC@adcfcf5 + UAC@479432c, slot 7 Ikenna)**: 10 of 12 P1/P2 follow-up gaps shipped to
`live-defi-rollout`. Rows 1-10 in table above: all AlertCode extensions (rows 1-5), CircuitBreakerId/BreakerConfig
extensions (rows 6-9), OracleStaleError/OracleDeviationError (row 10) — shipped. Remaining: row 11
(LendingFeatureSpike/VenueOutage post-cutover, P3) + row 12 (microlamports→USD P2, defi_master) unchanged.
