---
doc_type: codex-ssot
title: Scenario Outcome Assertions
summary:
  The scenario outcome-assertion contract (child of scenario-injection-architecture) — the 9-member OutcomeCategory
  closed-enum, the per-assertion 6-tuple (consequence / breaker_id / breaker_action / kill_switch_id / alert_codes /
  expected_within_seconds) checked by UTL ScenarioOutcomeChecker, per-archetype matrix cell shape, and PASS/FAIL/WARN
  semantics (any FAIL = cutover-block per master plan F-17.5); synthetic=true guards against real-fire masking.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, batch-live-reconciliation-service]
scope: [engineer, admin]
tags: [scenario-injection, simulation, validation, risk, kill-switch, uac]
related: [plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md Phase 8.B]
created: 2026-05-18
authoritative_for:
  [scenario outcome-assertion contract, OutcomeCategory closed-enum, scenario matrix PASS/FAIL/WARN semantics]
referenced_by: [/codex/02-data/scenario-overlay-semantics.md, /codex/04-architecture/scenario-injection-architecture.md]
owner:
last_reviewed: 2026-10-24
code_refs:
author: harsh-slot-3
---

# Scenario Outcome Assertions

> **Parent architecture**: [`scenario-injection-architecture.md`](scenario-injection-architecture.md) — tap-layer enum,
> mutation types, synthetic provenance. This doc covers the outcome-assertion contract: what a scenario is expected to
> cause, how assertions are verified, and what constitutes a PASS vs FAIL at matrix scale.

## Nine outcome categories (closed-enum)

`OutcomeCategory` (UAC `canonical/crosscutting/scenario_overlay.py` @`33630a6`) is a **closed-set enum** — new
categories require a PR to UAC + review sign-off before use:

| `OutcomeCategory`          | What it asserts                                                                                                     |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `STRATEGY_HALTED`          | Strategy instance stops emitting signals / orders for the duration of the scenario window                           |
| `STRATEGY_SCALED_DOWN`     | Strategy reduces position size or allocation by ≥X% (X in assertion config)                                         |
| `RISK_BREAKER_TRIPPED`     | A named `CircuitBreakerId` fires within `expected_within_seconds`                                                   |
| `ORDER_REJECTED`           | Execution-service adversarial-mode rejects the order at the matching-engine layer                                   |
| `ORDER_CANCELLED_ON_STALE` | An in-flight order is cancelled due to stale oracle / book feed within the scenario window                          |
| `KILL_SWITCH_ARMED`        | A named `KillSwitchId` arms within `expected_within_seconds`                                                        |
| `ALERT_FIRED`              | One or more `AlertCode`s are emitted by alerting-service (log-only path; PagerDuty suppressed for `synthetic=True`) |
| `PNL_BOUNDED_BY`           | Realised-PnL loss does not exceed the configured `max_loss_bps` within the scenario window                          |
| `RECONCILIATION_FLAGGED`   | batch-live-reconciliation-service flags a discrepancy within the scenario window                                    |

## Per-assertion 6-tuple contract

Each `ScenarioOutcomeAssertion` (UAC) carries a typed 6-tuple:

```python
consequence:             RiskRuleConsequence | None   # e.g. SCALE_DOWN, HALT, REJECT_ORDER
breaker_id:              CircuitBreakerId | None       # specific breaker that must trip
breaker_action:          BreakerAction | None          # OPEN / CLOSE / TRIP
kill_switch_id:          KillSwitchId | None           # specific kill-switch that must arm
alert_codes:             frozenset[AlertCode]          # one or more alert codes that must fire
expected_within_seconds: int                           # SLA from first mutation inject to observation
```

`UTL ScenarioOutcomeChecker` (`scenario/checker.py` @`3797fed5`) walks observed events after each scenario run and
matches against this 6-tuple. The `synthetic=True` safeguard rejects real-fire events from satisfying assertions —
prevents coincidence-masking when a real system event happens to match the expected outcome.

## Per-archetype matrix shape

The two-archetype pre-cutover matrix (`carry_staked_basis` × `ARBITRAGE_PRICE_DISPERSION`) is defined in
`unified_api_contracts/registry/scenario_archetype_matrix.py` (UAC @`556b96f`).

Each matrix cell is a `(archetype, scenario_id)` pair. Per cell:

- One `ScenarioOutcomeAssertion` list (one or more expected outcomes)
- One `ScenarioReport` result after the run

The matrix is **closed at design-ship time** — adding a new scenario to an archetype requires updating the registry PLUS
adding matching outcome assertions. Partial cells (scenario defined in registry but no assertion for an archetype) are
flagged as `ASSERTION_MISSING` and treated as FAIL at matrix review.

## PASS / FAIL / WARN semantics

| Result | Condition                                                                                                            |
| ------ | -------------------------------------------------------------------------------------------------------------------- |
| `PASS` | All assertions in the cell observed within their `expected_within_seconds` SLA                                       |
| `FAIL` | Any assertion not observed within SLA; OR observation arrived but wrong `consequence` / `breaker_id`                 |
| `WARN` | Assertion observed outside SLA but within a configured `warn_window_seconds` grace period; flagged for investigation |

**Matrix-red = cutover-block**: any `FAIL` in the per-archetype matrix is a **cutover-blocking finding** (Group F item
17.5 of `master_to_live_defi_2026_05_23.md`). `WARN` is not blocking but must be triaged within 24h.

## Scenario-fail vs real-fire event distinction

The `synthetic=true` guard is the only mechanism separating a scenario-driven outcome from a real-fire event:

- Every observable event emitted during a scenario run carries `ObservedEvent(synthetic=True)`.
- `ScenarioOutcomeChecker` calls `assert event.synthetic, "real-fire event matched scenario assertion"` — if this
  raises, the test infrastructure itself is broken (bug in scenario harness, not in the strategy).
- Real-fire events that arrive during a scenario window (e.g., a genuine oracle deviation coinciding with a
  `PRICE_SHIFT` injection) are ignored by the checker — they are logged with `SCENARIO_WINDOW_REAL_FIRE_COLLISION`
  marker for operator review but do not count as PASS for the assertion.

## Alerting wire pattern

`alerting-service` receives `AlertCode`s on both real and synthetic event paths. For scenario assertions on
`ALERT_FIRED`:

1. alerting-service fires the alert (same code path as live).
2. alerting-service checks `synthetic=True` on the triggering event → routes to log-only path.
3. PagerDuty + Telegram paging are **suppressed** for synthetic events.
4. Operator dashboard surface receives the alert entry (with `synthetic` badge) — unaffected.
5. `ScenarioOutcomeChecker` reads alerting-service event log and matches the `alert_codes` frozenset.

To verify alerting wire in tests: `assert AlertCode.MY_CODE in scenario_report.outcome_results[i].assertion.alert_codes`
where `i` is the `ALERT_FIRED` assertion index.

## Cross-references

- Parent: [`scenario-injection-architecture.md`](scenario-injection-architecture.md) — tap-layer enum + mutation types
- Kill-switch trips: [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md) — § "Scenario-driven trips"
- Recovery validation: [`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md) — § "Scenario-driven recovery
  validation"
- Backtest groups: [`backtest-groups.md`](backtest-groups.md) — § "Scenario-overlay mode" (fourth axis)
- Master plan gate: `plans/archive/2026_07/master_to_live_defi_2026_05_23.md` Group F item 17.5 (scenario regression
  matrix)
- Plan driving Phase 12: `plans/active/simulation_scenarios_post_cutover_2026_06_01.md`
