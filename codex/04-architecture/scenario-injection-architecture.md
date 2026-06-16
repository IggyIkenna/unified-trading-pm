---
scope: [engineer, admin]
title: Scenario injection architecture
type: architecture
status: living
last_reviewed: 2026-05-17
owner: simulation-platform
---

# Scenario injection architecture

> **Phase 8.A of `plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md`.** Codifies the
> synthetic-adversarial scenario harness — the closed-set scenario taxonomy + per-mutation applier + outcome checker +
> matrix runner. Stub doc shipped 2026-05-12 (slot 7 Day-3 / Day-4); full content updates as Harsh slot 5 implements
> Phase 3.E + 3.F service wire-ins.

## Reuse-prod-codepath principle

Scenarios ride the **same prod codepaths** as live + batch — per the workspace "live = batch — same data, same fields,
same timing semantics" HARD RULE ([batch-vs-live-architecture.md](../05-infrastructure/batch-vs-live-architecture.md)).
Only the overlay mutation differs. `synthetic=true` metadata on every emitted event distinguishes scenario-fire from
real-fire so alerting-service suppresses paging while still recording the event for the operator dashboard.

The harness does **not** instantiate a parallel backtest engine. It configures

- observes the unified pipeline (MTDS → MDPS → features-\* → strategy-service ↔ position-balance + risk +
  execution-service-in-matching-engine-mode) with one well-bounded overlay layer.

## Six pipeline-tap layers (closed set)

Mutations inject at exactly one of six layers (`ScenarioOverlayLayer` enum, UAC@`33630a6`):

| Layer      | Pipeline boundary                                                          | Pre-cutover wire status (compressed scope)        |
| ---------- | -------------------------------------------------------------------------- | ------------------------------------------------- |
| `RAW_TICK` | MTDS adapter `_post_fetch` hook (tick / book / funding rows)               | DEFERRED (Phase 3.A post-cutover)                 |
| `FEATURE`  | features-service `_compute_*` exit OR mdps feature-layer hook              | DEFERRED (Phase 3.B + 3.C post-cutover)           |
| `SIGNAL`   | strategy-service `signal_generator` emit boundary                          | DEFERRED (Phase 3.D post-cutover)                 |
| `ORDER`    | execution-service order submit + matching-engine adversarial mode          | **PRE-CUTOVER** (Phase 3.E, Harsh slot 5 wire-in) |
| `EVENT`    | Cross-cutting event stream injection (chain-slot / venue-halt / tx-status) | DEFERRED (post-cutover)                           |
| `MANIFEST` | ManifestWriter `record_*` hook (phantom-row or honest-empty injection)     | DEFERRED (Phase 3.G post-cutover)                 |

Pre-cutover compressed scope wires only `ORDER` layer + position-balance / risk / alerting consumers (Phase 3.F). Other
layers are taped post-cutover per the successor plan `simulation_scenarios_post_cutover_2026_06_01.md`.

## Eleven mutation types (closed-union)

`ScenarioMutationSpec` is a Pydantic discriminated union with 11 typed members (UAC@`33630a6`
`canonical/crosscutting/scenario_overlay.py`):

`PriceShift` · `StaleHold` · `LatencyInject` · `BookSpoof` · `RejectFills` · `OracleDeviate` · `GasSurge` · `DropRows` ·
`EventDrop` · `EventDuplicate` · `ManifestPhantom`

Adding a new mutation type requires:

1. Extend `_MutationBase` subclass + add discriminator literal in `scenario_overlay.py`.
2. Add a matching `apply_<mutation>()` method to UTL `ScenarioOverlayApplier` in the SAME logical unit (Citadel-Grade
   pre-audit; reviewers reject otherwise — see UTL@`3797fed5` `scenario/applier.py`).

## Nine outcome-assertion categories (closed-enum)

`OutcomeCategory` (UAC@`33630a6`): `STRATEGY_HALTED` · `STRATEGY_SCALED_DOWN` · `RISK_BREAKER_TRIPPED` ·
`ORDER_REJECTED` · `ORDER_CANCELLED_ON_STALE` · `KILL_SWITCH_ARMED` · `ALERT_FIRED` · `PNL_BOUNDED_BY` ·
`RECONCILIATION_FLAGGED`.

Each `ScenarioOutcomeAssertion` carries the 6-tuple-per-cell contract codified in the handshake doc fragment 11
([`plans/active/scratch_scenarios_day1/11_handshake_integration.md`](../../plans/active/scratch_scenarios_day1/11_handshake_integration.md)):

1. `consequence: RiskRuleConsequence | None`
2. `breaker_id: CircuitBreakerId | None`
3. `breaker_action: BreakerAction | None`
4. `kill_switch_id: KillSwitchId | None`
5. `alert_codes: frozenset[AlertCode]`
6. `expected_within_seconds: int`

UTL `ScenarioOutcomeChecker` (UTL@`3797fed5` `scenario/checker.py`) walks observed events + matches against this 6-tuple
per assertion. The `synthetic=True` safeguard rejects real-fire events from satisfying scenario assertions (avoids
coincidence-masking).

## `synthetic=true` event-stream provenance

Every observable event emitted during a scenario run carries `synthetic=True` metadata. Consumer behaviours:

- **risk-and-exposure-service** fires its breakers normally (same code path as live); attaches `synthetic=True` to
  `BREAKER_ARMED` events.
- **execution-service** matching engine adversarial mode routes the fill-attempt through
  `ScenarioOverlayApplier.apply()` when an active `ScenarioApplyContext` is bound; emits
  `ObservedEvent(synthetic=True)`.
- **position-balance-monitor-service** filters `KillSwitchProvenance.SCENARIO_SYNTHETIC` to snapshot state WITHOUT
  triggering real unwind paths.
- **alerting-service** `synthetic=True` log-only path — alert fires + is recorded; PagerDuty + Telegram paging
  suppressed; dashboard surface unaffected.

## LookaheadBias compatibility (Phase 2.E)

ScenarioOverlay mutations that legitimately shift `available_at` (`StaleHold` / `EventDrop` / `OracleDeviate` stale
variants) MUST NOT trigger `LookaheadBiasError` downstream. Mechanism: UTL
`assert_no_lookahead_for_feature_group(..., scenario_overlay_active=True)` downgrades violations to a structured warning
logged with the `SCENARIO_OVERLAY_LOOKAHEAD_DOWNGRADE` marker (UTL@`9e84ee44`).

Strict mode stays on for every non-overlay path. Only the overlay-active path skips. This protects against accidental
scenario-driven masking of real lookahead bugs in non-scenario runs.

## Two-archetype regression matrix (Phase 5)

Per-cutover-archetype matrix is built at module-load from the registry
([`unified_api_contracts/registry/scenario_archetype_matrix.py`](../../../unified-api-contracts/unified_api_contracts/registry/scenario_archetype_matrix.py)
UAC@`556b96f`):

- `MATRIX["carry_staked_basis"]` — every scenario with at least one declared
  `expected_outcome.archetype="carry_staked_basis"`.
- `MATRIX["ARBITRAGE_PRICE_DISPERSION"]` — same for funding-arb.

Pre-cutover ship: 16 cells (10 scenarios × 2 archetypes filtered to applicable — over-delivered vs the 12-cell
compressed-scope target on plan body line 73-74).

Phase 5.C green-matrix invariant: a matrix run is GREEN iff every cell PASSES every declared expected outcome within its
`expected_within_seconds` SLA. Any FAIL = matrix red. RED matrix = cutover blocker (Phase 10).

UTL `ScenarioMatrixRunner` (UTL@`66904fe0` `scenario/matrix_runner.py`) synchronously iterates the matrix; emits
`ScenarioMatrixReport` with `all_passed` / `cell_count` / `passed_cell_count` / `failure_summary()` surfaces.

## Cross-plan composition

- **`risk_simulations_limits_alerting_2026_05_10.md`** — provides the `RiskRuleConsequence` + `RiskRule` +
  risk-rule-fire taxonomy that `ScenarioOutcomeAssertion` references. Scenarios CONSUME the rule names; they don't
  extend the taxonomy.
- **`disaster_recovery_circuit_breakers_2026_05_10.md`** — provides the `CircuitBreakerId` + `BreakerAction` +
  `KillSwitchId` taxonomies. Scenarios CONSUME these for outcome-assertion references.
- **`alerting_service_live_rules_2026_05_07.md`** — provides the `AlertCode` closed-set + alerting wire. Scenarios
  CONSUME `AlertCode` for `ALERT_FIRED` assertions; the `synthetic=true` filter is enforced alerting-side per the
  consumer-shape in Phase 3 integration spec.
- **`writegate_honest_coverage_endtoend_2026_05_06.md`** — `EmptyConfirmedReason` taxonomy is the upstream SSOT for
  topology-gap scenarios; this harness does NOT extend that taxonomy.

## Cross-references

- [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md) — kill-switch trigger 5-set + circuit-breaker
  action 3-set.
- [`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md) — every recovery row gets a paired `scenario_id`
  post-cutover (Phase 8.E DEFERRED).
- [`backtest-groups.md`](backtest-groups.md) — scenario-overlay mode is a new axis (Phase 8.F DEFERRED).
- [`../02-data/honest-absence-downstream-handling.md`](../02-data/honest-absence-downstream-handling.md) —
  scenario-driven gap injection cross-references.
- [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md) —
  7-layer-tap point map (Phase 8.G DEFERRED until other layers wire).
- [`../05-infrastructure/replay-subsystem.md`](../05-infrastructure/replay-subsystem.md) — scenario-overlay-on-replay
  extension (Phase 8.H DEFERRED).

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

The `_real_pipeline_observer` + `_per_scenario_observer_factory` are service-side (execution-service Phase 3.E wire-in;
Harsh slot 5 implementation target). UTL primitives ship the runner shells; the pipeline driver is caller-supplied per
the Phase 3 integration spec
([`plans/active/scratch_scenarios_day1/12_phase3_integration_spec.md`](../../plans/active/scratch_scenarios_day1/12_phase3_integration_spec.md)).

## Pre-cutover vs post-cutover scope (compressed-scope)

| Surface                            | Pre-cutover (compressed)        | Post-cutover (successor `simulation_scenarios_post_cutover_2026_06_01.md`)           |
| ---------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------ |
| Mutation types                     | 11 (all)                        | Plus `LendingFeatureSpike` / `VenueOutage` / `MempoolCongestion` first-class members |
| Pipeline-tap layers                | `ORDER` only                    | All 6 layers wired                                                                   |
| Scenarios                          | 10 (6 topology + 4 price-shock) | ≥34 (full per-asset_group library)                                                   |
| Archetypes in matrix               | 2 (cutover)                     | Per asset_group expansion                                                            |
| ScenarioReportEmitter parquet sink | DEFERRED                        | Phase 2.C                                                                            |
| deployment-ui Scenarios tab        | DEFERRED                        | Phase 7                                                                              |
| Real-VM matrix runs                | DEFERRED                        | Phase 9 (per-archetype matrix.parquet on GCS)                                        |
| Cron VM nightly matrix             | DEFERRED                        | Phase 10.D                                                                           |

## Provenance

- Day-1 design: 10 scenario fragments + handshake-shape at `plans/active/scratch_scenarios_day1/{01..11}.md` (~995
  lines, PM@`bea269b1`).
- Day-2 UAC code: UAC@`33630a6` scenario_overlay.py + 10 registry instances + 53 unit tests.
- Day-2 UTL code: UTL@`3797fed5` scenario/{applier,checker,runner}.py + 51 unit tests.
- Day-2 Phase 3 integration spec: `scratch_scenarios_day1/12_phase3_integration_spec.md`.
- Day-3 UAC matrix: UAC@`556b96f` `registry/scenario_archetype_matrix.py` + 11 tests.
- Day-3 UTL matrix-runner: UTL@`66904fe0` `scenario/matrix_runner.py` + 10 tests.
- Day-4 Phase 2.E LookaheadBias downgrade: UTL@`9e84ee44` + 2 tests.

This codex doc itself is the Phase 8.A NEW deliverable. Phase 8.B + 8.C (scenario-outcome-assertions +
scenario-overlay-semantics) DEFERRED — content folded into the per-scenario fragment files + this doc until consumers
grow enough to need separate codex pages.

## Scenario authoring guide (Phase 8.B)

> **Phase 8.B of `simulation_scenarios_topology_price_shocks_2026_05_09.md`.** Shipped 2026-05-13 slot 7 Day-2-4 scope
> extension.

A scenario is a `ScenarioOverlay` Pydantic instance in UAC `unified_api_contracts/registry/scenarios/<asset_group>.py`.
Every new scenario MUST follow this 5-step authoring recipe:

1. **Choose a `scenario_id`**: lowercase snake*case, starts with the primary asset_group or `cross_asset`. Regex:
   `^[a-z]a-z0-9*]+$`. Must be globally unique across all 6 asset_group modules.

2. **Select `ScenarioCategory`**: closed 7-member enum (`TOPOLOGY_GAP` / `STALENESS` / `PRICE_SHOCK` / `VENUE_OUTAGE` /
   `DATA_CORRUPTION` / `CROSS_ASSET` / `OPERATIONAL`). One primary; secondary is implicit in description.

3. **Pick the `ScenarioOverlayLayer`**: one of the 6 closed-set layers. For multi-layer scenarios, declare the FIRST
   injection point as the primary layer; add `description` cross-references for secondary layers.

4. **Define `mutation_spec`**: one member of the 11-member `ScenarioMutationSpec` discriminated union. Adding a new
   member requires BOTH a UAC union extension AND a matching `apply_<mutation>()` in UTL `ScenarioOverlayApplier` in the
   SAME logical unit.

5. **Declare `expected_outcomes`**: ≥1 `ScenarioOutcomeAssertion` per archetype the scenario targets. Each assertion
   carries the 6-tuple-per-cell contract (consequence / breaker_id / breaker_action / kill_switch_id / alert_codes /
   expected_within_seconds). Nil fields are `None`; do NOT fabricate values.

**Anti-patterns to avoid**:

- `expected_outcomes=()` — a scenario with zero outcome assertions has no regression value and blocks the matrix from
  covering it.
- Hardcoding `expected_within_seconds=0` — use realistic SLA from the historical reference or circuit-breaker rule
  timeout.
- Using `asset_groups=frozenset({"all"})` — wrong; use the exact set of asset_groups the scenario injects into.
- Declaring `archetype` in `applies_to` but not in any `ScenarioOutcomeAssertion` — the matrix builder uses assertion
  archetype, not applicability filter.

**CI gate**: `pytest tests/internal/unit/test_scenario_overlay.py` covers schema validation + registry completeness +
per-asset_group counts. Add a test row when adding a new scenario.

---

## Per-archetype scenario selection (Phase 8.C)

> **Phase 8.C of `simulation_scenarios_topology_price_shocks_2026_05_09.md`.** Shipped 2026-05-13 slot 7 Day-2-4 scope
> extension.

Different archetypes are exposed to different failure surfaces. This section provides the selection rules for which
scenarios belong in each archetype's regression matrix.

### `carry_staked_basis` selection rules

**Primary exposure**: Solana LST yield + Ethereum/Arbitrum lending (Aave/Morpho)

- CeFi perp hedge (Bybit UTA/stETH, Deribit, OKX/wstETH, DRIFT).

Mandatory scenario families:

- All `defi` scenarios (RPC outage, oracle deviation, gas surge, liquidity drain, stablecoin depeg, mempool congestion)
  — CSB DeFi leg is the primary strategy.
- All `cross_asset` scenarios — hybrid DeFi-CeFi position is structurally exposed to correlated shocks.
- `cefi_venue_circuit_breaker_trip` + `cefi_funding_spike_10x` — hedge-leg exposure on Bybit/Deribit/OKX.

Exclusion rules:

- Pure CeFi funding-arb scenarios that only affect perp-vs-perp basis (no DeFi leg) — these belong exclusively to APD
  unless they affect CSB hedge leg.

### `ARBITRAGE_PRICE_DISPERSION` selection rules

**Primary exposure**: cross-venue USDC-margined perp funding-rate arbitrage across Binance / Bybit / OKX / Deribit /
Hyperliquid / Aster.

Mandatory scenario families:

- All `cefi` scenarios — APD primary exposure is CeFi perp venues.
- `cross_asset` scenarios — flash crash + basis blowout both degenerate APD's basis arithmetic.
- `defi` scenarios that affect APD DeFi-spot leg in hybrid implementations: `defi_chain_rpc_outage_solana` (secondary),
  `defi_oracle_deviation_30sigma` (secondary), `defi_gas_surge_50x` (secondary).

Exclusion rules:

- DeFi-only scenarios that do not touch CeFi perp legs — `defi_liquidity_drain` in isolation (CSB only),
  `defi_mempool_congestion` unless DeFi-spot leg used.

### Adding a new archetype to the matrix

The matrix builder at `unified_api_contracts/registry/scenario_archetype_matrix.py` auto-discovers archetypes from the
`CUTOVER_ARCHETYPES` frozenset. To add a post-cutover archetype:

1. Add the archetype id string to `CUTOVER_ARCHETYPES`.
2. Declare at least one `ScenarioOutcomeAssertion` with that archetype in a registry scenario instance.
3. Run `pytest tests/internal/unit/test_scenario_archetype_matrix.py` — tests assert non-empty matrix per archetype.
4. Add a codex pointer here under "Archetype-specific selection rules".

---

## Matrix runner usage (Phase 8.D)

> **Phase 8.D of `simulation_scenarios_topology_price_shocks_2026_05_09.md`.** Shipped 2026-05-13 slot 7 Day-2-4 scope
> extension.

`ScenarioMatrixRunner` (UTL@`66904fe0` `unified_trading_library/scenario/matrix_runner.py`) drives the per-archetype
regression matrix. Usage:

```python
from unified_api_contracts import SCENARIO_REGISTRY, SCENARIO_ARCHETYPE_MATRIX
from unified_trading_library.scenario import ScenarioMatrixRunner

def _make_observer(scenario_id: str, archetype: str):
    # Return an ObserverCallback that watches the real pipeline (execution-service
    # adversarial mode + position-balance + risk + alerting). See Phase 3
    # integration spec: scratch_scenarios_day1/12_phase3_integration_spec.md.
    ...

matrix_runner = ScenarioMatrixRunner(
    archetype="carry_staked_basis",
    observer_factory=_make_observer,
    scenario_registry=SCENARIO_REGISTRY,
    matrix=SCENARIO_ARCHETYPE_MATRIX,
)
matrix_report = matrix_runner.run()
if not matrix_report.all_passed:
    print(matrix_report.failure_summary())
```

**Key properties on `ScenarioMatrixReport`**:

- `all_passed: bool` — True iff every cell PASSES every assertion within SLA.
- `cell_count: int` — total (archetype, scenario_id) cells.
- `passed_cell_count: int` — cells with PASS.
- `failed_cell_count: int` — cells with any FAIL.
- `failure_summary() -> str` — formatted text listing failed cells + per-assertion observed_summary for each failed
  cell.

**Failure triage flow** (per Phase 9 triage discipline):

1. `matrix_report.all_passed` is False → print `failure_summary()`.
2. For each failed cell: was the assertion wrong (fix UAC + re-run) OR is the prod code wrong (file issue doc in plan)
   OR is the assertion over-strict (document + fix)?
3. Re-run matrix after each fix until `all_passed`.

**Pre-cutover green-matrix gate**: `matrix_report.all_passed` returning True for both `carry_staked_basis` +
`ARBITRAGE_PRICE_DISPERSION` is required before cutover per Phase 10 (master plan Group F item 17.5).

---

## Post-run report shape (Phase 8.E)

> **Phase 8.E of `simulation_scenarios_topology_price_shocks_2026_05_09.md`.** Shipped 2026-05-13 slot 7 Day-2-4 scope
> extension.

`ScenarioReport` and `ScenarioMatrixReport` (UAC@`33630a6` `canonical/crosscutting/scenario_overlay.py`) are the output
contracts for single-scenario and matrix runs respectively.

### `ScenarioReport` fields

| Field                  | Type                                | Description                                                           |
| ---------------------- | ----------------------------------- | --------------------------------------------------------------------- |
| `scenario_id`          | `str`                               | Scenario identifier (matches UAC registry)                            |
| `archetype`            | `str`                               | Archetype the run was scoped to                                       |
| `run_id`               | `str`                               | UUID for this run; used to correlate event stream + parquet           |
| `started_at_iso`       | `str`                               | ISO-8601 run start timestamp                                          |
| `finished_at_iso`      | `str`                               | ISO-8601 run finish timestamp                                         |
| `outcome_results`      | `tuple[ScenarioOutcomeResult, ...]` | Per-assertion PASS/FAIL with observed evidence                        |
| `synthetic`            | `bool`                              | Always `True`; guards against accidental use in non-synthetic context |
| `parquet_artifacts`    | `frozenset[str]`                    | GCS URIs for per-stage parquet snapshots (post-cutover Phase 2.C)     |
| `event_correlation_id` | `str`                               | Matches `correlation_id` in the event stream for this run             |

### `ScenarioOutcomeResult` fields

| Field              | Type                       | Description                                                            |
| ------------------ | -------------------------- | ---------------------------------------------------------------------- |
| `assertion`        | `ScenarioOutcomeAssertion` | The expected outcome this result evaluates                             |
| `passed`           | `bool`                     | True iff assertion PASSED within SLA                                   |
| `observed_summary` | `str`                      | Human-readable evidence (e.g. "ORACLE_DEVIATION_BPS tripped at T+28s") |
| `observed_at`      | `float \| None`            | Epoch seconds at which the outcome was observed (None if not observed) |
| `sla_seconds`      | `int`                      | From `assertion.expected_within_seconds`                               |

### Parquet sink (post-cutover Phase 2.C)

Pre-cutover: reports emitted in-memory; consumer JSONL-serializes per matrix-runner spec. Post-cutover Phase 2.C adds
`ScenarioReportEmitter` writing to:

```
gs://{pid}-scenario-reports/{archetype}/{YYYY-MM-DD}/{scenario_id}/{run_id}/report.parquet
gs://{pid}-scenario-reports/matrix/{archetype}/{YYYY-MM-DD}/{run_id}/matrix.parquet
```

Both use the workspace bucket-naming SSOT via
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)`.

---

## Adversarial mode flag wiring (Phase 8.F)

> **Phase 8.F of `simulation_scenarios_topology_price_shocks_2026_05_09.md`.** Shipped 2026-05-13 slot 7 Day-2-4 scope
> extension.

The execution-service `AdversarialMatchingEngine` (Harsh slot 5, `execution-service@d0ec76f1`) accepts a scenario
context at runtime. The wiring path:

### Wire-in contract (Phase 3.E implementation reference)

```python
# execution-service matching_engine/engine.py (simplified)
from unified_api_contracts import ScenarioOverlay, ScenarioOverlayLayer

class AdversarialMatchingEngine:
    def __init__(self, scenario_id: str | None = None):
        self._overlay: ScenarioOverlay | None = None
        if scenario_id is not None:
            from unified_api_contracts import SCENARIO_REGISTRY
            self._overlay = SCENARIO_REGISTRY[scenario_id]

    def simulate_fill(self, order, ...):
        if self._overlay is not None:
            from unified_trading_library.scenario import ScenarioOverlayApplier
            order_frame = _to_frame(order)
            mutated = ScenarioOverlayApplier.apply(
                order_frame, self._overlay,
                context=ScenarioContext(layer=ScenarioOverlayLayer.ORDER),
            )
            order = _from_frame(mutated)
        return self._real_simulate_fill(order, ...)
```

### CLI invocation (Phase 3.E, `execution-service@1c5923f3`)

```bash
python -m execution_service.cli.run_scenario \
    --scenario-id defi_oracle_deviation_30sigma \
    --archetype carry_staked_basis \
    --time-window 2024-01-15/2024-01-15
```

### Production default behaviour

When `scenario_id=None` (default in all non-scenario paths), the adversarial engine adds zero overhead — the overlay
branch is never entered. This guarantees the adversarial mode has no performance impact on live trading.

### `synthetic=true` propagation path

Every `ObservedEvent` emitted by the adversarial engine carries `synthetic=True`. Consumer chain:

1. `position-balance-monitor-service` `ScenarioKillSwitchSubscriber`: filters `KillSwitchProvenance.SCENARIO_SYNTHETIC`
   to snapshot WITHOUT triggering real unwind paths (`execution-service@8b6c06f` Phase 3.F).
2. `risk-and-exposure-service` `ScenarioOutcomeBridge`: emits `BREAKER_ARMED ObservedEvent(synthetic=True)` per arm
   (`risk-and-exposure-service@0a8f024`).
3. `alerting-service` router: `_is_synthetic()` short-circuits to `_route_synthetic_log_only()` — PagerDuty + Telegram
   suppressed; dashboard surface unaffected (`alerting-service@3c0d675`).

---

## Synthetic provenance auditing (Phase 8.G)

> **Phase 8.G of `simulation_scenarios_topology_price_shocks_2026_05_09.md`.** Shipped 2026-05-13 slot 7 Day-2-4 scope
> extension.

Ensuring that scenario-generated events never pollute real production state requires a complete provenance trail. The
`_synthetic_provenance` column is the primary audit artefact.

### `_synthetic_provenance` column

`ScenarioOverlayApplier.apply()` appends a `_synthetic_provenance: list[str]` column to every output frame. The list
contains the ordered chain of `scenario_id` values that transformed this row (chain-aware — supports composed scenarios
where two overlays apply in sequence).

**Downstream consumers that MUST NOT strip this column**:

- Features calculators: must pass `_synthetic_provenance` through `_compute_<group>()` output (post-cutover Phase 3.C
  wire-in).
- Strategy signal generator: must include in signal output (Phase 3.D).
- Manifest writer: must carry in the `scenario_id` column when Phase 3.G ships.
- Parquet writer: must NOT filter out `_synthetic_provenance` rows as "garbage data" — this is the audit trail.

### Audit probe (operator runbook)

To verify no synthetic rows leaked into production parquets:

```bash
# GCS probe — should return 0 rows
python3 - << 'EOF'
import polars as pl
from google.cloud import storage

bucket = "central-element-323112-unified-trading-captured"
# Sample last 7 days of OHLCV parquets and check for _synthetic_provenance col
# Expected: column absent (pre-Phase 3.G) OR present but always null
...
EOF
```

Pre-Phase 3.G: `_synthetic_provenance` column does NOT appear in production parquets (applier only runs in scenario
context). Post-Phase 3.G (manifest wire-in): column present but always `null` for non-scenario runs; non-null only when
scenario_id was active for that pipeline run.

### Event stream audit

Every `ObservedEvent(synthetic=True)` is persisted to the event stream at:

```
gs://{pid}-events/scenarios/{archetype}/{YYYY-MM-DD}/{scenario_id}/{run_id}/hour={H}/*.jsonl
```

Operator can diff real event stream vs scenario event stream by filtering on `synthetic: true` in the JSONL payload.
Alerting-service records all synthetic events in `ALERT_SUPPRESSED_SYNTHETIC` audit log with full payload.

---

## Scenario archive and version history (Phase 8.H)

> **Phase 8.H of `simulation_scenarios_topology_price_shocks_2026_05_09.md`.** Shipped 2026-05-13 slot 7 Day-2-4 scope
> extension.

### Scenario registry versioning

Scenario definitions live in UAC `registry/scenarios/<asset_group>.py`. The UAC follows standard semver. Each scenario
is immutable once its `scenario_id` is declared in the registry: only additive changes (new `expected_outcomes`, updated
`description`, extended `applies_to`) are backwards-compatible.

**Non-backwards-compatible changes** (require new `scenario_id`):

- Changing `mutation_spec` type or magnitude beyond ±20% of original.
- Removing a declared `expected_outcomes` assertion.
- Changing `category` or `layer`.

When a new variant is needed, add a new `scenario_id` with `_v2` suffix (e.g. `defi_oracle_deviation_30sigma_v2`) and
annotate the original with:

```python
# DEPRECATED 2026-06-01: replaced by defi_oracle_deviation_30sigma_v2.
# Keep for historical matrix runs until successors succeed in ≥5 consecutive nightly runs.
```

### Historical run archive

Pre-cutover: reports in-memory only. Post-cutover Phase 2.C ships the parquet sink. Once the parquet sink is live, every
matrix run is persisted for:

- Regression trend analysis (did a recent code change degrade a formerly-passing cell?).
- Audit evidence for Group F item 17.5 ("scenario regression matrix green ≥7 days before cutover"
  continuous-verification requirement).

**Retention policy**: scenario run parquets retained 365 days. Matrix-level summary parquets (one row per cell) retained
indefinitely (small).

### Change log convention

Each `ScenarioOverlay` instance in the registry module carries a `changelog:` field in its `description` string for
material changes:

```
description="...; Changelog: 2026-05-12 initial ship UAC@33630a6; 2026-06-01 extended applies_to with Solana devnet."
```

---

## Operator runbook — triggering scenarios on demand (Phase 8.I)

> **Phase 8.I of `simulation_scenarios_topology_price_shocks_2026_05_09.md`.** Shipped 2026-05-13 slot 7 Day-2-4 scope
> extension.

```yaml
execution:
  owner: Ikenna slot 7 (pre-cutover) → mtds-scenario-matrix- cron VM (post-Phase 10.D)
  cadence: on-demand (pre-cutover); nightly (post-Phase 10.D)
  verifier: matrix_report.all_passed == True; event stream SCENARIO_RUN_STARTED + SCENARIO_RUN_FINISHED per cell
  last_executed: NEVER (pending Phase 9 real-VM runs)
```

### Pre-requisites

1. Phase 3.E wire-in live in execution-service (`execution-service@d0ec76f1` `AdversarialMatchingEngine`).
2. Phase 3.F consumers live (position-balance-monitor `ScenarioKillSwitchSubscriber`
   - risk-and-exposure `ScenarioOutcomeBridge` + alerting `_is_synthetic()`).
3. Both archetype registries populated in UAC (`SCENARIO_REGISTRY` contains ≥8 carry_staked_basis-applicable scenarios +
   ≥8 APD-applicable scenarios).

### Single-scenario on-demand trigger

```bash
# Step 1: identify scenario_id + archetype
python3 - << 'EOF'
from unified_api_contracts import SCENARIO_REGISTRY, scenarios_for_archetype
print("carry_staked_basis matrix:", sorted(scenarios_for_archetype("carry_staked_basis")))
print("APD matrix:", sorted(scenarios_for_archetype("ARBITRAGE_PRICE_DISPERSION")))
EOF

# Step 2: launch via execution-service CLI (Phase 3.E)
python -m execution_service.cli.run_scenario \
    --scenario-id cefi_venue_circuit_breaker_trip \
    --archetype ARBITRAGE_PRICE_DISPERSION \
    --time-window 2024-06-15/2024-06-15

# Step 3: verify event stream (within 90s of launch)
# Events at gs://{pid}-events/scenarios/ARBITRAGE_PRICE_DISPERSION/.../
# Expect: SCENARIO_RUN_STARTED → SCENARIO_RUN_FINISHED per scenario
```

### Full-archetype matrix trigger

```bash
# Launch matrix runner for one archetype (parallel per-scenario)
python3 - << 'EOF'
from unified_api_contracts import SCENARIO_REGISTRY, SCENARIO_ARCHETYPE_MATRIX
from unified_trading_library.scenario import ScenarioMatrixRunner

def observer_factory(scenario_id, archetype):
    # Wire to real execution-service adversarial pipeline
    from execution_service.scenario_observer import make_observer
    return make_observer(scenario_id, archetype)

runner = ScenarioMatrixRunner(
    archetype="carry_staked_basis",
    observer_factory=observer_factory,
)
report = runner.run()
print(f"Matrix result: {'GREEN' if report.all_passed else 'RED'}")
if not report.all_passed:
    print(report.failure_summary())
EOF
```

### Alerting on matrix failure

Post-Phase 10.D cron VM: if `matrix_report.all_passed` is False for >24h consecutive, alerting-service rule fires
`SCENARIO_MATRIX_RED` alert to the operator dashboard (NOT to PagerDuty — synthetic events are dashboard-only per Phase
3.F routing). The alert carries the `failure_summary()` payload.

### Recovery from matrix-red

1. Read `failure_summary()` — identifies which cells failed + per-assertion observed_summary.
2. Triage each failed cell per Phase 9 triage discipline (§ Phase 9.C):
   - Assertion wrong → fix UAC + re-run.
   - Prod code defect → file issue doc in plan + fix in appropriate plan.
   - Assertion over-strict → document + fix.
3. Re-run targeted cell(s) to verify green before re-running full matrix.
4. Once full matrix green, update `continuous_verification.last_verified` in master plan Group F item 17.5.
