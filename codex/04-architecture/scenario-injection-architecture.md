# Scenario injection architecture

> **Phase 8.A of `plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md`.**
> Codifies the synthetic-adversarial scenario harness — the closed-set scenario
> taxonomy + per-mutation applier + outcome checker + matrix runner. Stub doc
> shipped 2026-05-12 (slot 7 Day-3 / Day-4); full content updates as Harsh slot
> 5 implements Phase 3.E + 3.F service wire-ins.

## Reuse-prod-codepath principle

Scenarios ride the **same prod codepaths** as live + batch — per the workspace
"live = batch — same data, same fields, same timing semantics" HARD RULE
([batch-vs-live-architecture.md](../05-infrastructure/batch-vs-live-architecture.md)).
Only the overlay mutation differs. `synthetic=true` metadata on every emitted
event distinguishes scenario-fire from real-fire so alerting-service suppresses
paging while still recording the event for the operator dashboard.

The harness does **not** instantiate a parallel backtest engine. It configures
+ observes the unified pipeline (MTDS → MDPS → features-\* → strategy-service ↔
position-balance + risk + execution-service-in-matching-engine-mode) with one
well-bounded overlay layer.

## Six pipeline-tap layers (closed set)

Mutations inject at exactly one of six layers (`ScenarioOverlayLayer` enum,
UAC@`33630a6`):

| Layer | Pipeline boundary | Pre-cutover wire status (compressed scope) |
|---|---|---|
| `RAW_TICK` | MTDS adapter `_post_fetch` hook (tick / book / funding rows) | DEFERRED (Phase 3.A post-cutover) |
| `FEATURE` | features-service `_compute_*` exit OR mdps feature-layer hook | DEFERRED (Phase 3.B + 3.C post-cutover) |
| `SIGNAL` | strategy-service `signal_generator` emit boundary | DEFERRED (Phase 3.D post-cutover) |
| `ORDER` | execution-service order submit + matching-engine adversarial mode | **PRE-CUTOVER** (Phase 3.E, Harsh slot 5 wire-in) |
| `EVENT` | Cross-cutting event stream injection (chain-slot / venue-halt / tx-status) | DEFERRED (post-cutover) |
| `MANIFEST` | ManifestWriter `record_*` hook (phantom-row or honest-empty injection) | DEFERRED (Phase 3.G post-cutover) |

Pre-cutover compressed scope wires only `ORDER` layer + position-balance / risk
/ alerting consumers (Phase 3.F). Other layers are taped post-cutover per the
successor plan `simulation_scenarios_post_cutover_2026_06_01.md`.

## Eleven mutation types (closed-union)

`ScenarioMutationSpec` is a Pydantic discriminated union with 11 typed members
(UAC@`33630a6` `canonical/crosscutting/scenario_overlay.py`):

`PriceShift` · `StaleHold` · `LatencyInject` · `BookSpoof` · `RejectFills` ·
`OracleDeviate` · `GasSurge` · `DropRows` · `EventDrop` · `EventDuplicate` ·
`ManifestPhantom`

Adding a new mutation type requires:

1. Extend `_MutationBase` subclass + add discriminator literal in
   `scenario_overlay.py`.
2. Add a matching `apply_<mutation>()` method to UTL `ScenarioOverlayApplier`
   in the SAME logical unit (Citadel-Grade pre-audit; reviewers reject
   otherwise — see UTL@`3797fed5` `scenario/applier.py`).

## Nine outcome-assertion categories (closed-enum)

`OutcomeCategory` (UAC@`33630a6`): `STRATEGY_HALTED` · `STRATEGY_SCALED_DOWN` ·
`RISK_BREAKER_TRIPPED` · `ORDER_REJECTED` · `ORDER_CANCELLED_ON_STALE` ·
`KILL_SWITCH_ARMED` · `ALERT_FIRED` · `PNL_BOUNDED_BY` ·
`RECONCILIATION_FLAGGED`.

Each `ScenarioOutcomeAssertion` carries the 6-tuple-per-cell contract codified
in the handshake doc fragment 11
([`plans/active/scratch_scenarios_day1/11_handshake_integration.md`](../../plans/active/scratch_scenarios_day1/11_handshake_integration.md)):

1. `consequence: RiskRuleConsequence | None`
2. `breaker_id: CircuitBreakerId | None`
3. `breaker_action: BreakerAction | None`
4. `kill_switch_id: KillSwitchId | None`
5. `alert_codes: frozenset[AlertCode]`
6. `expected_within_seconds: int`

UTL `ScenarioOutcomeChecker` (UTL@`3797fed5` `scenario/checker.py`) walks
observed events + matches against this 6-tuple per assertion. The
`synthetic=True` safeguard rejects real-fire events from satisfying scenario
assertions (avoids coincidence-masking).

## `synthetic=true` event-stream provenance

Every observable event emitted during a scenario run carries `synthetic=True`
metadata. Consumer behaviours:

- **risk-and-exposure-service** fires its breakers normally (same code path as
  live); attaches `synthetic=True` to `BREAKER_ARMED` events.
- **execution-service** matching engine adversarial mode routes the
  fill-attempt through `ScenarioOverlayApplier.apply()` when an active
  `ScenarioApplyContext` is bound; emits `ObservedEvent(synthetic=True)`.
- **position-balance-monitor-service** filters `KillSwitchProvenance.SCENARIO_SYNTHETIC`
  to snapshot state WITHOUT triggering real unwind paths.
- **alerting-service** `synthetic=True` log-only path — alert fires + is
  recorded; PagerDuty + Telegram paging suppressed; dashboard surface
  unaffected.

## LookaheadBias compatibility (Phase 2.E)

ScenarioOverlay mutations that legitimately shift `available_at`
(`StaleHold` / `EventDrop` / `OracleDeviate` stale variants) MUST NOT trigger
`LookaheadBiasError` downstream. Mechanism: UTL
`assert_no_lookahead_for_feature_group(..., scenario_overlay_active=True)`
downgrades violations to a structured warning logged with the
`SCENARIO_OVERLAY_LOOKAHEAD_DOWNGRADE` marker (UTL@`9e84ee44`).

Strict mode stays on for every non-overlay path. Only the overlay-active path
skips. This protects against accidental scenario-driven masking of real lookahead
bugs in non-scenario runs.

## Two-archetype regression matrix (Phase 5)

Per-cutover-archetype matrix is built at module-load from the registry
([`unified_api_contracts/registry/scenario_archetype_matrix.py`](../../../unified-api-contracts/unified_api_contracts/registry/scenario_archetype_matrix.py)
UAC@`556b96f`):

- `MATRIX["carry_staked_basis"]` — every scenario with at least one declared
  `expected_outcome.archetype="carry_staked_basis"`.
- `MATRIX["ARBITRAGE_PRICE_DISPERSION"]` — same for funding-arb.

Pre-cutover ship: 16 cells (10 scenarios × 2 archetypes filtered to applicable
— over-delivered vs the 12-cell compressed-scope target on plan body line
73-74).

Phase 5.C green-matrix invariant: a matrix run is GREEN iff every cell PASSES
every declared expected outcome within its `expected_within_seconds` SLA. Any
FAIL = matrix red. RED matrix = cutover blocker (Phase 10).

UTL `ScenarioMatrixRunner` (UTL@`66904fe0` `scenario/matrix_runner.py`)
synchronously iterates the matrix; emits `ScenarioMatrixReport` with
`all_passed` / `cell_count` / `passed_cell_count` / `failure_summary()`
surfaces.

## Cross-plan composition

- **`risk_simulations_limits_alerting_2026_05_10.md`** — provides the
  `RiskRuleConsequence` + `RiskRule` + risk-rule-fire taxonomy that
  `ScenarioOutcomeAssertion` references. Scenarios CONSUME the rule names;
  they don't extend the taxonomy.
- **`disaster_recovery_circuit_breakers_2026_05_10.md`** — provides the
  `CircuitBreakerId` + `BreakerAction` + `KillSwitchId` taxonomies. Scenarios
  CONSUME these for outcome-assertion references.
- **`alerting_service_live_rules_2026_05_07.md`** — provides the `AlertCode`
  closed-set + alerting wire. Scenarios CONSUME `AlertCode` for
  `ALERT_FIRED` assertions; the `synthetic=true` filter is enforced
  alerting-side per the consumer-shape in Phase 3 integration spec.
- **`writegate_honest_coverage_endtoend_2026_05_06.md`** — `EmptyConfirmedReason`
  taxonomy is the upstream SSOT for topology-gap scenarios; this harness does
  NOT extend that taxonomy.

## Cross-references

- [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md) — kill-switch
  trigger 5-set + circuit-breaker action 3-set.
- [`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md) — every
  recovery row gets a paired `scenario_id` post-cutover (Phase 8.E DEFERRED).
- [`backtest-groups.md`](backtest-groups.md) — scenario-overlay mode is a new
  axis (Phase 8.F DEFERRED).
- [`../02-data/honest-absence-downstream-handling.md`](../02-data/honest-absence-downstream-handling.md)
  — scenario-driven gap injection cross-references.
- [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md)
  — 7-layer-tap point map (Phase 8.G DEFERRED until other layers wire).
- [`../05-infrastructure/replay-subsystem.md`](../05-infrastructure/replay-subsystem.md)
  — scenario-overlay-on-replay extension (Phase 8.H DEFERRED).

## Operator-runtime invocation

```python
from unified_api_contracts import SCENARIO_REGISTRY
from unified_trading_library.scenario import ScenarioRunner, ScenarioMatrixRunner

# Single-scenario run.
runner = ScenarioRunner(
    scenario_id="cefi_funding_spike_10x",
    archetype="ARBITRAGE_PRICE_DISPERSION",
    observer_callback=_real_pipeline_observer,
)
report = runner.run().report

# Full-archetype matrix run.
matrix_runner = ScenarioMatrixRunner(
    archetype="ARBITRAGE_PRICE_DISPERSION",
    observer_factory=_per_scenario_observer_factory,
)
matrix_report = matrix_runner.run()
assert matrix_report.all_passed, matrix_report.failure_summary()
```

The `_real_pipeline_observer` + `_per_scenario_observer_factory` are
service-side (execution-service Phase 3.E wire-in; Harsh slot 5 implementation
target). UTL primitives ship the runner shells; the pipeline driver is
caller-supplied per the Phase 3 integration spec
([`plans/active/scratch_scenarios_day1/12_phase3_integration_spec.md`](../../plans/active/scratch_scenarios_day1/12_phase3_integration_spec.md)).

## Pre-cutover vs post-cutover scope (compressed-scope)

| Surface | Pre-cutover (compressed) | Post-cutover (successor `simulation_scenarios_post_cutover_2026_06_01.md`) |
|---|---|---|
| Mutation types | 11 (all) | Plus `LendingFeatureSpike` / `VenueOutage` / `MempoolCongestion` first-class members |
| Pipeline-tap layers | `ORDER` only | All 6 layers wired |
| Scenarios | 10 (6 topology + 4 price-shock) | ≥34 (full per-asset_group library) |
| Archetypes in matrix | 2 (cutover) | Per asset_group expansion |
| ScenarioReportEmitter parquet sink | DEFERRED | Phase 2.C |
| deployment-ui Scenarios tab | DEFERRED | Phase 7 |
| Real-VM matrix runs | DEFERRED | Phase 9 (per-archetype matrix.parquet on GCS) |
| Cron VM nightly matrix | DEFERRED | Phase 10.D |

## Provenance

- Day-1 design: 10 scenario fragments + handshake-shape at
  `plans/active/scratch_scenarios_day1/{01..11}.md` (~995 lines, PM@`bea269b1`).
- Day-2 UAC code: UAC@`33630a6` scenario_overlay.py + 10 registry instances + 53 unit tests.
- Day-2 UTL code: UTL@`3797fed5` scenario/{applier,checker,runner}.py + 51 unit tests.
- Day-2 Phase 3 integration spec: `scratch_scenarios_day1/12_phase3_integration_spec.md`.
- Day-3 UAC matrix: UAC@`556b96f` `registry/scenario_archetype_matrix.py` + 11 tests.
- Day-3 UTL matrix-runner: UTL@`66904fe0` `scenario/matrix_runner.py` + 10 tests.
- Day-4 Phase 2.E LookaheadBias downgrade: UTL@`9e84ee44` + 2 tests.

This codex doc itself is the Phase 8.A NEW deliverable. Phase 8.B + 8.C
(scenario-outcome-assertions + scenario-overlay-semantics) DEFERRED — content
folded into the per-scenario fragment files + this doc until consumers grow
enough to need separate codex pages.
