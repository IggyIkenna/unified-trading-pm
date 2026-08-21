---
doc_type: plan
title: Safety and Risk Controls
summary: 'Verify and implement production-grade safety controls for live trading. risk-and-exposure-service

  has a PreTradeCheckEngine with position limit checks and risk_monitor. Gaps: no circuit breaker

  pattern, no kill switch mechanism, pre-trade wiring into execution-service not verified, preflight

  checks before live session start not confirmed. This plan wires PreTradeCheckEngine into the

  execution flow, adds circuit breakers and kill switch, verifies preflight checks, and achieves

  ≥70% test coverage on all risk modules. Covers audit S21.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-05'
todos:
- {id: risk-pretrade-wiring-verify, content: 'DONE 2026-03-08. Verified PreTradeCheckEngine wired via RiskChecker HTTP boundary in execution-service. kill_switch check runs BEFORE any order is submitted (503 when active). RiskChecker.check_instruction() delegates to check_pre_trade_risk() — the single HTTP boundary. Tests: tests/unit/engine/test_pretrade_wiring.py (10 tests): kill switch blocking, approved/rejected/error paths, payload construction.', status: completed}
- {id: risk-position-limits-verify, content: 'DONE 2026-03-08. Position limit enforcement verified and tested: position size breach (qty>100 rejected), position value breach (qty*price>max_position_value rejected), gross exposure breach, capital limit breach, VaR limit breach (PRE_TRADE_VAR_BREACH emitted). Limits loaded from service config (not hardcoded). Tests: tests/unit/test_position_limits_breach.py (11 tests, all assertions on checks dict keys).', status: completed}
- {id: risk-circuit-breaker, content: 'DONE 2026-03-07. Implemented execution-service/execution_service/engine/circuit_breaker.py — 3-state machine (CLOSED→OPEN→HALF_OPEN). Per-venue isolation via get_circuit_breaker(venue) singleton factory. 5 failures → OPEN; 300s cooldown → HALF_OPEN; 1 success → CLOSED. log_event on all transitions: CIRCUIT_BREAKER_OPEN, CIRCUIT_BREAKER_HALF_OPEN, CIRCUIT_BREAKER_CLOSED. Tests: tests/unit/engine/test_circuit_breaker.py. NOTE: alerting-service PubSub wiring owned by phase3_service_hardening_integration t4f-monitoring-pipeline.', status: completed}
- {id: risk-kill-switch, content: 'DONE 2026-03-07. Implemented execution-service/execution_service/engine/kill_switch.py — singleton Event, activate/deactivate/is_active. app.py imports from kill_switch module; emits KILL_SWITCH_ACTIVATED/DEACTIVATED via log_event(). manual_instruction_api.py gates all order submissions with kill_switch.is_active() → 503 if set. Tests: tests/unit/engine/test_kill_switch.py (11 tests).', status: completed}
- {id: risk-preflight-checks, content: 'DONE 2026-03-08. Implemented execution_service/engine/preflight.py: run_preflight_checks() with 5 checks: (1) Secret Manager accessible, (2) venue API keys present in SM, (3) risk service health reachable, (4) position state loadable (risk service /health), (5) risk limits config loaded. Emits PREFLIGHT_FAILED via log_event on any failure; raises PreflightCheckError. Tests: tests/unit/engine/test_preflight.py (10 tests).', status: completed}
- {id: risk-test-coverage, content: 'DONE 2026-03-08. Added 46 new unit tests across 4 new test files (test_pretrade_wiring.py, test_preflight.py, test_position_limits_breach.py, test_var_api_endpoint.py). pre_trade_check_engine.py at 92% coverage, var_calculator.py at 100% coverage — both exceed ≥70% gate. All tests unit-only with mocked externals.', status: completed}
isProject: false
---

# Safety and Risk Controls

**Day:** 6–8 (March 10–12) **Scope:** execution-service (circuit breaker, kill switch, preflight),
risk-and-exposure-service (pre-trade wiring verification, position limits, test coverage) **Blocks:**
trading_system_audit_prompt S21; live trading week (March 20) **Owner:** Person B

---

## Blockers

| Blocker                                                       | Type          | Specific Dependency                                                                                                                     | Resolution                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phase 3 T4 Batch E (execution-service hardening) not complete | `[PLAN_TODO]` | [phase3_service_hardening_integration.md](phase3_service_hardening_integration.md) § todos `t4e-execution-service` (Phase 3 T4 Batch E) | Execution-service must reach Phase 3 T4 Batch E green before circuit breaker wiring; does NOT require all of Phase 3 to complete — only execution-service's T4E batch. Circuit breaker is complementary: this plan owns the 3-state engine in execution-service/engine/; phase3 t4f owns alerting-service PubSub propagation of CIRCUIT_BREAKER_OPEN events. |
| Sports execution path (USEI v1) not implemented               | `[PLAN_TODO]` | [sports_migration_phase2_full.md](sports_migration_phase2_full.md) § todo `usei-adapters`                                               | Kill switch and circuit breaker for sports venue adapters (Betfair, Pinnacle) cannot be tested until USEI adapters exist; sports path risk controls are blocked until USEI v1                                                                                                                                                                                |
| execution-service sports routing not implemented              | `[STUB]`      | [unit_tests_and_test_failure_action.md](unit_tests_and_test_failure_action.md) § RC-3                                                   | route_instruction() returns category='trade' for sports venues; circuit breaker cannot be tested for sports path until routing is fixed                                                                                                                                                                                                                      |

---

## Current State

| Component                  | Status              | Location                                                                             |
| -------------------------- | ------------------- | ------------------------------------------------------------------------------------ |
| PreTradeCheckEngine        | EXISTS              | `risk-and-exposure-service/risk_and_exposure_service/core/pre_trade_check_engine.py` |
| risk_monitor.py            | EXISTS              | `risk-and-exposure-service/risk_and_exposure_service/core/risk_monitor.py`           |
| alert_manager.py           | EXISTS              | `risk-and-exposure-service/risk_and_exposure_service/core/alert_manager.py`          |
| exposure_aggregator.py     | EXISTS              | `risk-and-exposure-service/risk_and_exposure_service/core/exposure_aggregator.py`    |
| Position limit checks      | EXISTS in pre_trade | needs wiring verification                                                            |
| Circuit breaker            | NOT IMPLEMENTED     | —                                                                                    |
| Kill switch                | NOT IMPLEMENTED     | —                                                                                    |
| Preflight checks           | NOT CONFIRMED       | needs verification in execution-service                                              |
| Test coverage risk modules | PARTIAL             | test_pre_trade_check_engine.py exists                                                |

---

## Audit Criteria (S21)

| #    | Criterion                                               | Blocking |
| ---- | ------------------------------------------------------- | -------- |
| 21.1 | Pre-trade check in critical path — no order bypasses it | YES      |
| 21.2 | Position limits enforced per venue per instrument       | YES      |
| 21.3 | Circuit breaker on repeated venue failures              | YES      |
| 21.4 | Kill switch halts all live orders immediately           | YES      |
| 21.5 | Preflight checks before live session start              | YES      |
| 21.6 | All risk events logged via log_event()                  | YES      |
| 21.7 | ≥70% test coverage on risk modules                      | YES      |

---

## Circuit Breaker Design

```
States: CLOSED → OPEN → HALF_OPEN → CLOSED

CLOSED:      Normal operation. Track failure count in rolling window.
OPEN:        Failure threshold exceeded. Reject all orders for venue. Emit CIRCUIT_BREAKER_OPEN.
HALF_OPEN:   After cooldown, allow 1 probe order. On success → CLOSED. On failure → OPEN.

Config (per venue, from UnifiedCloudConfig):
  circuit_breaker_failure_threshold: int = 5      # failures in window
  circuit_breaker_window_seconds: int = 60        # rolling window
  circuit_breaker_cooldown_seconds: int = 300     # time before HALF_OPEN
```

Implementation location: `execution_service/engine/circuit_breaker.py`

## Kill Switch Design

```
kill_switch_active: asyncio.Event  # shared in-process flag

# Trigger (CLI or admin endpoint):
kill_switch_active.set()
log_event(event_type="KILL_SWITCH_ACTIVATED", ...)
# All venue adapters check: if kill_switch_active.is_set(): raise KillSwitchError

# For venues that support cancel-all:
await venue_adapter.cancel_all_open_orders()

# Recovery (operator action required):
kill_switch_active.clear()
log_event(event_type="KILL_SWITCH_DEACTIVATED", ...)
```

Implementation location: `execution_service/engine/kill_switch.py`

## Preflight Check Pattern

```python
async def run_preflight_checks(config: ExecutionServiceConfig) -> None:
    """Fail fast before starting live session. Never start in degraded state."""
    checks = [
        _check_secret_manager(config),
        _check_venue_api_keys(config),
        _check_venue_health(config),
        _check_position_state_loaded(config),
        _check_risk_limits_loaded(config),
    ]
    results = await asyncio.gather(*checks, return_exceptions=True)
    failures = [r for r in results if isinstance(r, Exception)]
    if failures:
        log_event(event_type="PREFLIGHT_FAILED", metadata={"failures": [str(f) for f in failures]})
        raise PreflightCheckError(f"{len(failures)} preflight checks failed")
```

---

## Execution Order

1. Verify pre-trade wiring (trace route_instruction → venue adapter for non-sports path)
2. Write test_pretrade_wiring.py — assert no bypass
3. Verify position limit tests cover breach scenarios
4. Implement circuit_breaker.py in execution-service
5. Implement kill_switch.py in execution-service
6. Implement preflight checks (verify existing or add missing)
7. Add compliance events (CIRCUIT_BREAKER_OPEN, KILL_SWITCH_ACTIVATED, PREFLIGHT_FAILED)
8. Run coverage — verify ≥70% on risk modules
9. Commit per-repo via quickmerge

---

## Gate Criteria

- [ ] Pre-trade check verified in critical path (test_pretrade_wiring.py passes)
- [ ] Position limit breach test passes (order rejected with RISK_LIMIT_EXCEEDED)
- [ ] Circuit breaker transitions: CLOSED → OPEN → HALF_OPEN → CLOSED all tested
- [ ] Kill switch: after activation, zero orders submitted (test_kill_switch.py passes)
- [ ] Preflight checks: all 5 checks implemented; PREFLIGHT_FAILED emitted on any failure
- [ ] All risk events logged via log_event() with correct event_type
- [ ] ≥70% coverage on risk-and-exposure-service + execution-service/engine/ risk modules
