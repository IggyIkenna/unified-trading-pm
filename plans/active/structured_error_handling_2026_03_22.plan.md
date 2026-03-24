---
title: "Structured Error Handling + Event Propagation"
status: active
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-03-22
owner: agent
---

# Structured Error Handling + Event Propagation

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

- [ ] [AGENT] P0. Create `unified_trading_library/service_framework/error_handling.py` with:
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

- [ ] [AGENT] P0. Add `SERVICE_ERROR` to UEI `LifecycleEventType` enum (if not already there)
- [ ] [AGENT] P0. Ensure `log_event("SERVICE_ERROR", details={...})` carries the full `EnhancedError.model_dump()`
      payload so downstream consumers (alerting-service) can parse it

### 1.3 Export + tests

- [ ] [AGENT] P1. Unit tests for `classify_error()` and `classify_and_emit_error()`
- [ ] [AGENT] P1. Export from UTL `__init__.py`

### QG Gate: `cd unified-trading-library && bash scripts/quality-gates.sh`

---

## Phase 2: P0 Service Fixes (PARALLEL)

### 2.1 execution-service

- [ ] [AGENT] P0. Replace `exceptions.py` raw exceptions with EnhancedError-based classification
- [ ] [AGENT] P0. Fix `cli/handlers/live_execution_handler.py` bare except — use `classify_and_emit_error()`
- [ ] [AGENT] P0. Fix `cli/exceptions.py` — BacktestConfigError/BacktestDataError → use ErrorCategory.CONFIGURATION/DATA

### 2.2 risk-and-exposure-service

- [ ] [AGENT] P0. Fix `api/main.py` 10 bare except blocks — wrap in `classify_and_emit_error()`
- [ ] [AGENT] P0. Ensure API error responses use EnhancedError schema (not raw stack traces)

### QG Gate: Both repos pass `bash scripts/quality-gates.sh`

---

## Phase 3: P1 Service Fixes (PARALLEL, grouped)

### 3A: Feature services — PARALLEL

- [ ] [AGENT] P1. features-delta-one-service: Fix 4 bare excepts in batch_handler.py
- [ ] [AGENT] P1. features-commodity-service: Fix 8+ bare excepts across data source adapters
- [ ] [AGENT] P1. All other feature services: audit and fix bare excepts

### 3B: ML services — PARALLEL

- [ ] [AGENT] P1. ml-training-service: Fix 8 bare excepts in model_registry.py
- [ ] [AGENT] P1. ml-inference-service: Fix fallback prediction path — fail with structured error

### 3C: Data services — PARALLEL

- [ ] [AGENT] P1. market-data-processing-service: Replace MarketDataProcessingError hierarchy with ErrorCategory mapping
- [ ] [AGENT] P1. market-tick-data-service: Fix async dependency checker + validated uploader bare excepts
- [ ] [AGENT] P1. instruments-service: Ensure consistent use of EnhancedError (40 files import but inconsistent)

### 3D: Other services — PARALLEL

- [ ] [AGENT] P1. strategy-service: Add EnhancedError to signal_generation module
- [ ] [AGENT] P1. pnl-attribution-service, position-balance-monitor-service: Fix bare excepts
- [ ] [AGENT] P1. batch-live-reconciliation-service: Fix stage handler bare excepts
- [ ] [AGENT] P1. trading-agent-service: Fix bare excepts in loop handlers

### 3E: Deduplicate custom exceptions

- [ ] [AGENT] P1. Delete DataNotFoundError from strategy-service (duplicate of execution-service)
- [ ] [AGENT] P1. Replace all custom exception classes with classify_and_emit_error() pattern

### QG Gate: All service repos pass `bash scripts/quality-gates.sh`

---

## Phase 4: Alerting Service — Error Event Consumption + Circuit Breaker (SEQUENTIAL)

### 4.1 Error event subscription

- [ ] [AGENT] P0. alerting-service: Subscribe to `SERVICE_ERROR` events from all services
- [ ] [AGENT] P0. Parse `EnhancedError` payload from event details
- [ ] [AGENT] P0. Route to appropriate alert channel based on ErrorSeverity:
  - CRITICAL → immediate Telegram + PagerDuty
  - HIGH → Telegram
  - MEDIUM → log + dashboard
  - LOW → log only

### 4.2 Circuit breaker for error events

- [ ] [AGENT] P0. Per-service/per-venue error rate tracking (sliding window)
- [ ] [AGENT] P0. Threshold: >5 errors/minute from same service+venue → CIRCUIT_OPEN event
- [ ] [AGENT] P0. Circuit breaker states: CLOSED → OPEN → HALF_OPEN
- [ ] [AGENT] P0. CIRCUIT_OPEN event triggers: stop sending work to that venue, alert operator
- [ ] [AGENT] P1. Dead letter queue: errors that exhaust retries → DeadLetterRecord (UIC schema)

### 4.3 Circuit breaker integration with execution-service

- [ ] [AGENT] P1. execution-service reads CIRCUIT_OPEN events from alerting-service
- [ ] [AGENT] P1. Venue circuit state affects order routing (skip venues with open circuits)

### QG Gate: alerting-service + execution-service pass QG

---

## Phase 5: Mock/Real Parity Fixes (PARALLEL)

### 5.1 Code path parity

- [ ] [AGENT] P1. features-cross-instrument-service: Use public `calculate()` not private `_calculate_features()`
- [ ] [AGENT] P1. features-multi-timeframe-service: Same — use public API
- [ ] [AGENT] P1. strategy-service: Pass real feature dict to strategy instead of None in mock
- [ ] [AGENT] P1. ml-inference-service: Remove fallback random predictions — fail structured if no model
- [ ] [AGENT] P1. alerting-service: Mock notification delivery (mock Slack/PagerDuty client)

### 5.2 Schema parity

- [ ] [AGENT] P1. features-calendar-service: Complete migration of DEPRECATED schemas to UIC
- [ ] [AGENT] P2. strategy-service types.py: Audit 30+ TypedDicts — move cross-service contracts to UIC

### 5.3 Missing **main**.py

- [ ] [AGENT] P2. Add **main**.py to: risk-and-exposure-service, position-balance-monitor-service,
      risk-management-service

### QG Gate: All affected repos pass QG

---

## Success Criteria

1. **Zero bare `except Exception` in service handler code** — all use `classify_and_emit_error()`
2. **Every error emits `SERVICE_ERROR` event** — parseable by alerting-service
3. **alerting-service consumes error events** — routes by severity to alert channels
4. **Circuit breaker operational** — per-venue error rate tracking, auto-opens on threshold
5. **Mock mode exercises same code paths as real** — no `if is_mock: return early` shortcuts
6. **No custom exception classes in services** — all use UIC ErrorCategory enum
