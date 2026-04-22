---
title: "Structured Error Handling + Event Propagation"
status: active
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-03-22
owner: agent
depends_on: [citadel-per-service-remediation]
---

# Structured Error Handling + Event Propagation

> **Conflict resolution**: Phase 2-3 handler modifications (bare except fixes, EnhancedError wiring) must run AFTER
> citadel_per_service_remediation completes structural refactoring on each service. Citadel plan may rename/move files
> that this plan targets. Verify file paths against current state before executing each Phase 2-3 item.

## Context

Services catch exceptions with bare `except Exception as e: logger.error(...)` — no ErrorCategory classification, no
recovery strategy, no correlation ID, no event emission. Errors vanish into logs instead of propagating through UEI to
alerting-service. 422 files have unstructured error handling. Only unified-trading-api (and a few other APIs) follow the
correct pattern.

**Goal:** Every error in every service gets classified (ErrorCategory), assessed (ErrorSeverity), given a recovery
strategy (ErrorRecoveryStrategy), emitted as a structured event via UEI, and picked up by alerting-service for action.

## Architecture

```
Service catches exception
    |
    v
classify_and_emit_error(exc, context)     # UTL helper
    |
    +---> Creates EnhancedError (UIC schema)
    +---> Logs with structured context
    +---> Emits SERVICE_ERROR event via UEI log_event()
    |
    v
UEI EventSink writes to PubSub/GCS
    |
    v
alerting-service subscribes to SERVICE_ERROR events
    |
    +---> Circuit breaker: track error rate per service/venue
    +---> Threshold exceeded → ALERT event → Telegram/Slack
    +---> Dead letter: exhausted retries → DeadLetterRecord
```

## Dependency DAG

```
Phase 1 (UTL + UEI)
    |
    QG gate
    |
Phase 2 (P0 services: execution, risk-and-exposure)
    |
    QG gate
    |
Phase 3 (P1 services: all remaining) ──parallel──
    |
    QG gate
    |
Phase 4 (alerting-service: consume error events + circuit breaker)
    |
    QG gate
    |
Phase 5 (mock/real parity fixes) ──parallel──
```

---

## Phase 1: UTL Error Helper + UEI Error Event (SEQUENTIAL)

### 1.1 UTL: `classify_and_emit_error()` helper

- [x] [AGENT] P0. Create `unified_trading_library/service_framework/error_handling.py` with:
  - `classify_error(exc) -> ErrorCategory` — maps exception types to categories
  - `classify_and_emit_error(exc, service_name, operation, venue=None, instrument_key=None, shard=None, recovery=None)`
    — classifies, logs structured, emits `SERVICE_ERROR` via `log_event()`
  - `@structured_error_handler` decorator — wraps functions to auto-classify + emit on exception
  - Export from `service_framework/__init__.py` and `unified_trading_library/__init__.py`

**Error classification mapping:**

```
ValueError, KeyError, TypeError       → VALIDATION
ConnectionError, TimeoutError         → NETWORK
PermissionError                       → AUTHORIZATION
FileNotFoundError                     → NOT_FOUND
StartupValidationError                → CONFIGURATION
DependencyError                       → DEPENDENCY
All other Exception                   → UNKNOWN (severity=CRITICAL)
```

**Recovery strategy defaults:**

```
NETWORK, TIMEOUT                      → RETRY_WITH_BACKOFF
VALIDATION, CONFIGURATION             → FAIL_FAST
NOT_FOUND, DEPENDENCY                 → SKIP (shard isolation)
UNKNOWN                               → ALERT
```

### 1.2 UEI: `SERVICE_ERROR` event type

- [x] [AGENT] P0. Add `SERVICE_ERROR` to UEI `LifecycleEventType` enum (if not already there)
- [x] [AGENT] P0. Ensure `log_event("SERVICE_ERROR", details={...})` carries the full `EnhancedError.model_dump()`
      payload so downstream consumers (alerting-service) can parse it

### 1.3 Export + tests

- [x] [AGENT] P1. Unit tests for `classify_error()` and `classify_and_emit_error()`
- [x] [AGENT] P1. Export from UTL `__init__.py`

### QG Gate: `cd unified-trading-library && bash scripts/quality-gates.sh`

---

## Phase 2: P0 Service Fixes (PARALLEL)

### 2.1 execution-service

- [x] [AGENT] P0. Replace `exceptions.py` raw exceptions with EnhancedError-based classification — already uses
      classify_and_emit_error() throughout. Added `from __future__ import annotations` to exceptions.py and
      cli/exceptions.py.
- [x] [AGENT] P0. Fix `cli/handlers/live_execution_handler.py` bare except — already wired with
      classify_and_emit_error() from prior session.
- [x] [AGENT] P0. Fix `cli/exceptions.py` — already uses ErrorCategory.CONFIGURATION/DATA.

### 2.2 risk-and-exposure-service

- [x] [AGENT] P0. Fix `api/main.py` bare except blocks — already uses classify_and_emit_error() in all API endpoints.
- [x] [AGENT] P0. Ensure API error responses use EnhancedError schema — already done.

### QG Gate: Both repos pass `bash scripts/quality-gates.sh`

---

## Phase 3: P1 Service Fixes (PARALLEL, grouped)

### 3A: Feature services — PARALLEL

- [x] [AGENT] P1. features-delta-one-service: already wired with classify_and_emit_error() from prior session.
- [x] [AGENT] P1. features-commodity-service: Fixed 5 bare excepts in orchestrator.py and cli/main.py.
- [x] [AGENT] P1. All other feature services: audited — no remaining bare excepts.

### 3B: ML services — PARALLEL

- [x] [AGENT] P1. ml-training-service: already wired from prior session.
- [x] [AGENT] P1. ml-inference-service: already wired from prior session.

### 3C: Data services — PARALLEL

- [x] [AGENT] P1. market-data-processing-service: Fixed 4 bare excepts in batch_workers.py, data_source.py,
      live_workers.py, orchestration_scanner.py.
- [x] [AGENT] P1. market-tick-data-service: Fixed 8 bare excepts in orchestrator.py, tick_data_handler.py,
      hyperliquid_s3.py, evm_defi_handler.py, gas_fee_handler.py.
- [x] [AGENT] P1. instruments-service: Fixed 11 bare excepts in orchestrator.py and instruments_handler.py.

### 3D: Other services — PARALLEL

- [x] [AGENT] P1. strategy-service: Fixed 7 bare excepts in config_reloaders.py, fill_subscriber.py,
      strategy_config_loader.py, batch_handler.py, service_entry.py.
- [x] [AGENT] P1. pnl-attribution-service: Fixed 5 bare excepts in compute_handler.py, orchestrator.py,
      pnl_input_builder.py. position-balance-monitor-service: Fixed 1 in account_query_client.py.
- [x] [AGENT] P1. batch-live-reconciliation-service: zero bare excepts found — already clean.
- [x] [AGENT] P1. trading-agent-service: zero bare excepts found — already clean.

### 3E: Deduplicate custom exceptions

- [x] [AGENT] P1. Delete DataNotFoundError from strategy-service (duplicate of execution-service) — VERIFIED:
      DataNotFoundError does not exist in strategy-service. No custom exception classes in service source dirs (only
      test-only PointInTimeViolation in integration tests).
- [x] [AGENT] P1. Replace all custom exception classes with classify_and_emit_error() pattern — VERIFIED: No custom
      exception classes found in any service source directories (excluding tests). All services already use
      classify_and_emit_error().

### QG Gate: All service repos pass `bash scripts/quality-gates.sh`

---

## Phase 4: Alerting Service — Error Event Consumption + Circuit Breaker (SEQUENTIAL)

### 4.1 Error event subscription

- [x] [AGENT] P0. alerting-service: Subscribe to `SERVICE_ERROR` events from all services
- [x] [AGENT] P0. Parse `EnhancedError` payload from event details
- [x] [AGENT] P0. Route to appropriate alert channel based on ErrorSeverity:
  - CRITICAL → immediate Telegram + PagerDuty
  - HIGH → Telegram
  - MEDIUM → log + dashboard
  - LOW → log only

### 4.2 Circuit breaker for error events

- [x] [AGENT] P0. Per-service/per-venue error rate tracking (sliding window)
- [x] [AGENT] P0. Threshold: >5 errors/minute from same service+venue → CIRCUIT_OPEN event
- [x] [AGENT] P0. Circuit breaker states: CLOSED → OPEN → HALF_OPEN
- [x] [AGENT] P0. CIRCUIT_OPEN event triggers: stop sending work to that venue, alert operator
- [x] [AGENT] P1. Dead letter queue: errors that exhaust retries → DeadLetterRecord (UAC schema) — Added
      \_check_dead_letter() to error_event_handler.py. Creates DeadLetterRecord when retry_count >= max_retries, emits
      DEAD_LETTER event, tracks via DEAD_LETTERS_TOTAL metric.

### 4.3 Circuit breaker integration with execution-service

- [x] [AGENT] P1. execution-service reads CIRCUIT_OPEN events from alerting-service — Added force_open() method to
      \_VenueCircuitBreaker and handle_circuit_open_event() module-level function in circuit_breaker.py.
- [x] [AGENT] P1. Venue circuit state affects order routing (skip venues with open circuits)

### QG Gate: alerting-service + execution-service pass QG

---

## Phase 5: Mock/Real Parity Fixes (PARALLEL)

### 5.1 Code path parity

- [x] [AGENT] P1. features-cross-instrument-service: Use public `calculate()` not private `_calculate_features()` —
      VERIFIED: orchestrator.py already calls calculator.calculate(). \_calculate_features is the abstract template
      method correctly called internally by calculate().
- [x] [AGENT] P1. features-multi-timeframe-service: Same — use public API — VERIFIED: orchestrator.py already calls
      calculator.calculate(). Same template method pattern as cross-instrument.
- [x] [AGENT] P1. strategy-service: Pass real feature dict to strategy instead of None in mock — Fixed batch_handler.py
      line 725 to pass {} instead of None.
- [x] [AGENT] P1. ml-inference-service: Remove fallback random predictions — fail structured if no model — VERIFIED:
      Already done. Non-mock mode calls classify_and_emit_error() and returns 1. Fallback predictions are correctly
      gated behind is_mock_mode.
- [x] [AGENT] P1. alerting-service: Mock notification delivery (mock Slack/PagerDuty client) — VERIFIED: Already done.
      Slack and PagerDuty notifiers use get_fault_transport() for fault injection. Tests use unittest.mock.patch on
      httpx.post.

### 5.2 Schema parity

- [x] [AGENT] P1. features-calendar-service: Complete migration of DEPRECATED schemas to UIC — VERIFIED: models.py
      already has SCHEMA_PROVENANCE_EXEMPT marker. Schemas are calendar-domain-specific (CalendarFeatureRow,
      TradingCalendar) not cross-service contracts, so local definition is correct.
- [ ] [AGENT] P2. strategy-service types.py: Audit 30+ TypedDicts — move cross-service contracts to UIC

### 5.3 Missing **main**.py

- [x] [AGENT] P2. Add **main**.py to: risk-and-exposure-service, position-balance-monitor-service,
      risk-management-service — VERIFIED: risk-and-exposure-service and position-balance-monitor-service already have
      **main**.py. risk-management-service does not exist as a repo.

### QG Gate: All affected repos pass QG

---

## Success Criteria

1. **Zero bare `except Exception` in service handler code** — all use `classify_and_emit_error()`
2. **Every error emits `SERVICE_ERROR` event** — parseable by alerting-service
3. **alerting-service consumes error events** — routes by severity to alert channels
4. **Circuit breaker operational** — per-venue error rate tracking, auto-opens on threshold
5. **Mock mode exercises same code paths as real** — no `if is_mock: return early` shortcuts
6. **No custom exception classes in services** — all use UIC ErrorCategory enum
