# Phase 3 scenario-runner integration spec — execution-service adversarial mode + risk/alerting consumers

Per `simulation_scenarios_topology_price_shocks_2026_05_09.md` Phase 3.E + Phase 3.F (compressed-scope single
wire-in: execution-service matching-engine adversarial mode + position-balance / risk / alerting consumers). This
spec is the design substrate consumers integrate against — it concretizes the Day-1 handshake-shape (fragment 11)
in terms of the UTL primitives shipped Day-2 (UAC@`33630a6` + UTL@`3797fed5`).

Phase 3.A/B/C/D/G (MTDS / MDPS / features / strategy / manifest taps) DEFERRED to successor
`simulation_scenarios_post_cutover_2026_06_01.md` per compressed-scope plan body line 84-88. This document is
PRE-CUTOVER scope only.

## Shipped primitives (Day-2 2026-05-12)

| Repo | Symbol | Purpose |
|---|---|---|
| UAC | `ScenarioOverlay` (`scenario_overlay.py`) | Frozen Pydantic — the declarative scenario contract. |
| UAC | `ScenarioMutationSpec` (discriminated union) | 11 typed mutations (PriceShift / StaleHold / LatencyInject / BookSpoof / RejectFills / OracleDeviate / GasSurge / DropRows / EventDrop / EventDuplicate / ManifestPhantom). |
| UAC | `ScenarioOutcomeAssertion` | The 6-tuple-per-cell contract (consequence / breaker_id / breaker_action / kill_switch_id / alert_codes / expected_within). |
| UAC | `SCENARIO_REGISTRY` | Module-level dict; populated at import by `registry/scenarios/{cefi,defi,cross_asset}.py`. 10 scenarios shipped. |
| UAC | `ScenarioReport` / `ScenarioOutcomeResult` | Per-run report shape. |
| UTL | `ScenarioOverlayApplier` (`scenario/applier.py`) | Per-mutation typed dispatch; pure-functional; stamps `_synthetic_provenance`. |
| UTL | `ScenarioOutcomeChecker` (`scenario/checker.py`) | Per-OutcomeCategory match logic; consumes `ObservedEvent` stream + matches assertions. |
| UTL | `ScenarioRunner` (`scenario/runner.py`) | Orchestrator; takes `(scenario_id, archetype, observer_callback)` + emits `ScenarioReport`. |
| UTL | `ObserverCallback` typed alias | `Callable[[ScenarioOverlayApplier, ScenarioOutcomeChecker, ScenarioApplyContext], None]`. |

All primitives type-check + ruff-clean; 53 UAC unit tests + 51 UTL unit tests pass.

## Phase 3.E — execution-service matching-engine adversarial mode

### Scope

The matching engine already has slippage / latency / partial-fill hooks (per Day-1 audit fragment 01 cited
`execution-service/execution_service/matching_engine/{engine,trade_matcher}.py` slippage model). Phase 3.E extends
these hooks to accept `ScenarioMutationSpec`-driven mutations:

- **`LatencyInject`** mutations slip into the existing latency hook (already an integer-ms knob).
- **`RejectFills`** mutations slip into the existing partial-fill / reject hook.
- **`BookSpoof`** mutations slip into the existing book-spoof / liquidity-withdrawal hook.

Other mutation types (`PriceShift`, `StaleHold`, `GasSurge`, `OracleDeviate`, `DropRows`, `EventDrop`,
`EventDuplicate`, `ManifestPhantom`) are NOT execution-service-relevant pre-cutover — those tap at FEATURE /
RAW_TICK / EVENT / MANIFEST layers which are Phase 3.A/B/C/G (DEFERRED).

### Concrete wire-in (3-step recipe)

```python
# 1. Subscribe to scenario context at matching engine init.
from unified_api_contracts import SCENARIO_REGISTRY
from unified_trading_library.scenario import ScenarioOverlayApplier, ScenarioApplyContext

class MatchingEngineAdversarial:
    def __init__(self, *, scenario_id: str | None = None, ctx: ScenarioApplyContext | None = None) -> None:
        self._scenario_id = scenario_id
        self._ctx = ctx
        self._applier: ScenarioOverlayApplier | None = None
        if scenario_id is not None:
            self._applier = ScenarioOverlayApplier(scenario=SCENARIO_REGISTRY[scenario_id])

    # 2. At each fill-attempt boundary, route through applier if active.
    def _try_match(self, order: ExecutionOrder) -> FillResult:
        if self._applier is None or self._ctx is None:
            return self._real_match(order)
        # Apply the mutation to the fill-attempt payload.
        payload = self._applier.apply(
            input_payload={"order_id": order.order_id, "size": order.size, ...},
            context=self._ctx,
        )
        # Honor RejectFills / LatencyInject / BookSpoof per typed payload fields.
        if "reject_rate" in payload and self._sample_reject(payload["reject_rate"]):
            return FillResult.rejected(reason=payload["reject_reason"])
        if "latency_added_seconds" in payload:
            time.sleep(float(payload["latency_added_seconds"]))
        if "book_depth_scale" in payload:
            order = order.with_scaled_depth(payload["book_depth_scale"])
        return self._real_match(order)

    # 3. Emit ObservedEvent on every state transition so the checker can match assertions.
    def _emit_observed(self, event_type: str, **kwargs: object) -> ObservedEvent:
        return ObservedEvent(
            event_type=event_type,
            seconds_since_scenario_start=self._elapsed(),
            synthetic=True,  # MANDATORY for synthetic runs — checker rejects synthetic=False
            **kwargs,
        )
```

### Done definition (Phase 3.E)

- Adversarial mode reads `(scenario_id, archetype)` from CLI flag `--scenario-id` + `--archetype` (operator-runtime
  override; production matching engine receives `None` by default).
- 3 existing hooks (slippage / latency / partial-fill) accept `ScenarioMutationSpec`-driven overrides.
- Engine emits `ObservedEvent` per fill-attempt transition with `synthetic=True` flag preserved.
- Per-archetype integration test (one per cutover archetype) drives the engine through a synthetic scenario + asserts
  the checker observes the expected event sequence.

## Phase 3.F — position-balance + risk + alerting consumers

### Scope

The 3 downstream consumers subscribe to the synthetic event stream + emit matching `ObservedEvent` records into the
checker. Per CLAUDE.md "Live = batch" rule, these consumers ride the SAME prod codepaths during synthetic runs —
ONLY the `synthetic=true` metadata distinguishes scenario-fire from real-fire.

### position-balance-monitor-service

```python
# Subscribe to synthetic events; emit per-scenario state snapshots.
class PositionBalanceConsumer:
    def on_kill_switch_armed(self, event: KillSwitchArmedEvent) -> None:
        if event.provenance == KillSwitchProvenance.SCENARIO_SYNTHETIC:
            # Snapshot per-scenario state but do NOT trigger real unwind paths.
            self._record_synthetic_kill_switch_state(event)
        else:
            self._real_unwind_path(event)
```

### risk-and-exposure-service

```python
# Outcome-checker hook fires on every breaker trip and emits ScenarioOutcomeResult.
class RiskOutcomeBridge:
    def on_breaker_armed(self, breaker_id: CircuitBreakerId, action: BreakerAction, synthetic: bool) -> None:
        observed = ObservedEvent(
            event_type="BREAKER_ARMED",
            seconds_since_scenario_start=self._elapsed(),
            synthetic=synthetic,
            breaker_id=breaker_id,
            breaker_action=action,
        )
        self._scenario_checker_handle.record(observed)  # the active run's checker, if any
```

### alerting-service

```python
# Rule-eval respects synthetic=true filter — alert fires + report records, paging suppressed.
class AlertingScenarioFilter:
    def evaluate_rule(self, rule: AlertRule, event_payload: AlertEvent) -> AlertDecision:
        if event_payload.synthetic:
            # Synthetic events go to dashboard only — no PagerDuty / Telegram pages.
            return AlertDecision.LOG_ONLY
        return self._real_alert_decision(rule, event_payload)
```

### Done definition (Phase 3.F)

- 3 consumers subscribe to synthetic-event stream + emit matching `ObservedEvent` records into the active
  `ScenarioOutcomeChecker` handle.
- Alerting-service log-only path tested end-to-end (no PagerDuty / Telegram paging fires during synthetic runs).
- Per-archetype integration test verifies: scenario fires breaker → BREAKER_ARMED ObservedEvent recorded →
  checker matches assertion → ScenarioOutcomeResult.passed == True.

## Operator-runtime invocation pattern

The matrix-runner (Phase 5) and the matching-engine adversarial mode share the same pattern:

```python
from unified_trading_library.scenario import ScenarioRunner, ObservedEvent

def _observer(applier, checker, ctx):
    # Drive the matching engine in adversarial mode using the applier.
    engine = MatchingEngineAdversarial(scenario_id=ctx.scenario_id, ctx=ctx)
    engine.run_session(...)  # this internally calls applier.apply() + emits ObservedEvent

    # Optionally inject extra observed events from external state surfaces.
    for event in engine.consumed_events():
        checker.record(event)

runner = ScenarioRunner(
    scenario_id="cefi_funding_spike_10x",
    archetype="ARBITRAGE_PRICE_DISPERSION",
    observer_callback=_observer,
)
result = runner.run(run_id="cefi_funding_spike_10x-20260512T2200Z")
report: ScenarioReport = result.report
print(f"passed={sum(1 for r in report.outcome_results if r.passed)}/{len(report.outcome_results)}")
```

## Integration tests — pre-cutover smoke

For each cutover archetype + each registered scenario applicable to it, ship a tagged smoke test under
`execution-service/tests/integration/scenarios/test_<scenario_id>.py` per Phase 3.E done-definition:

```python
@pytest.mark.scenario
def test_cefi_funding_spike_10x_apd_blocks_new_signals():
    runner = ScenarioRunner(
        scenario_id="cefi_funding_spike_10x",
        archetype="ARBITRAGE_PRICE_DISPERSION",
        observer_callback=_real_pipeline_observer,
    )
    result = runner.run()
    apd_outcomes = [r for r in result.report.outcome_results if r.assertion.archetype == "ARBITRAGE_PRICE_DISPERSION"]
    assert all(r.passed for r in apd_outcomes), [r.observed_summary for r in apd_outcomes if not r.passed]
```

Per-scenario smoke harness lives in execution-service repo (the only Phase 3 wire-in pre-cutover). Cross-archetype
matrix (Phase 5) runs all scenarios for both archetypes; that artefact emits the matrix.parquet (Phase 9 evidence).

## Open follow-ups (operator-triage Day-3 / Day-4)

| Follow-up | Owner | Pre-cutover vs successor |
|---|---|---|
| matching-engine adversarial mode wiring (the 3-step recipe above) | Harsh slot 5 per work-split row "Ikenna-7 ↔ Harsh-5 risk + DR + simulation" | Pre-cutover (Phase 3.E compressed scope) |
| position-balance / risk / alerting consumer subscriptions | Harsh slot 5 | Pre-cutover (Phase 3.F compressed scope) |
| per-scenario integration test fixtures (10 fixtures × 2 archetypes = up to 20 tests) | Ikenna slot 7 OR Harsh slot 5 | Pre-cutover; Day-3 / Day-4 |
| `ScenarioMatrixRunner` (Phase 5) | Ikenna slot 7 | Pre-cutover Day-3 |
| Phase 3.A/B/C/D/G (MTDS / MDPS / features / strategy / manifest taps) | — | DEFERRED `simulation_scenarios_post_cutover_2026_06_01.md` Phase 3 |
| `ScenarioReportEmitter` parquet sink (Phase 2.C) | — | DEFERRED post-cutover |
| `LookaheadBiasError` downgrade wiring (Phase 2.E) | UTL maintainer | Pre-cutover if scenarios that shift `available_at` land (Day-3+) |

## Cross-side handshake (Ikenna slot 7 → Harsh slot 5)

Per work-split `Ikenna-7 ↔ Harsh-5 (risk + DR + simulation)`: Ikenna designs + ships UAC + UTL primitives;
Harsh implements service-level wiring (Phase 3.E + 3.F). Concretely Harsh slot 5 picks up:

1. Read this spec + UAC@`33630a6` + UTL@`3797fed5`.
2. Wire matching-engine adversarial mode per the 3-step recipe in Phase 3.E.
3. Subscribe 3 consumers (position-balance / risk / alerting) per Phase 3.F shapes.
4. Ship per-archetype integration smoke test (1 test per archetype minimum; ideally 1 per archetype-applicable scenario
   pair for a ~16-cell matrix smoke).
5. Cross-side ping when Phase 3.E + 3.F done; Ikenna slot 7 picks up Phase 5 matrix-runner.

## Done definition (Phase 3 — `done` 2026-05-12 Harsh slot 5)

Phase 3.E + 3.F flipped to `done` 2026-05-12. Implementation shipped (each per shippable unit on `live-defi-rollout`):

- **Phase 3.E — matching-engine adversarial mode**:
  - `execution-service@d0ec76f1` — `AdversarialMatchingEngine` (RejectFills + LatencyInject + BookSpoof routing at
    fill-attempt boundary; `ObservedEvent` emission with `synthetic=True`).
  - `execution-service@6bdf6136` — 9 unit tests covering pass-through (scenario_id=None), `SCENARIO_REGISTRY`
    validation, all 3 mutation types, ObservedEvent discipline.
  - `execution-service@1c5923f3` — `python -m execution_service.cli.run_scenario --scenario-id X --archetype Y`
    operator-runtime CLI.
- **Phase 3.F — consumer subscriptions**:
  - `position-balance-monitor-service@8b6c06f` — `ScenarioKillSwitchSubscriber` (synthetic arm filter) + 7 unit tests.
  - `risk-and-exposure-service@0a8f024` — `ScenarioOutcomeBridge` + `arm_breaker(synthetic=...)` kwarg → BREAKER_ARMED
    ObservedEvent emission + 8 unit tests.
  - `alerting-service@3c0d675` — router `_is_synthetic()` + `_route_synthetic_log_only()` short-circuit + 8 unit tests.
  - `execution-service@92aa4af2` — per-archetype integration smoke (2 tests pass: APD × cefi_venue_circuit_breaker_trip
    + carry_staked_basis × defi_chain_rpc_outage_solana).

**Cross-side handshake closes**: Ikenna slot 7 (UAC@`33630a6` + UTL@`3797fed5` design primitives) ↔ Harsh slot 5
(implementation). Ikenna slot 7 picks up Phase 5 matrix-runner next.

Phase 3.A / 3.B / 3.C / 3.D / 3.G remain `deferred-after-simulation_scenarios_post_cutover_2026_06_01` per
compressed-scope plan body line 84-88 (MTDS / MDPS / features / strategy / manifest taps = post-cutover infra).
