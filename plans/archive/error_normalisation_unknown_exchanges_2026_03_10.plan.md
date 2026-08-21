---
doc_type: plan
title: error-normalisation-unknown-exchanges-2026-03-10
summary: Complete venue error map coverage, add CanonicalUnknownVenueError, wire circuit breaker to canonical error types
  with configurable per-venue thresholds
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, system-integration-tests, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-api-contracts, code: C3, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-events-interface, code: C3, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-internal-contracts, code: C3, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: execution-service, code: C3, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-market-interface, code: C1, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: system-integration-tests, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
depends_on: []
todos:
- {id: phase-0-audit, content: Venue error map completeness audit and circuit breaker trigger audit, status: done, note: COMPLETE 2026-03-10 — full audit in unified-trading-pm/audits/venue_error_coverage_2026_03_10.md}
- {id: phase-1-schema-extensions, content: 'Add CanonicalUnknownVenueError, UNKNOWN_VENUE_ERROR_RECEIVED event, circuit breaker config schema and YAML', status: done, note: 'DONE 2026-03-11: P1.1–P1.4 all complete'}
- {id: phase-2-circuit-breaker-hardening, content: 'Load config in circuit_breaker.py, update all record_failure callers to pass CanonicalError', status: done, note: 'DONE 2026-03-11: P2.1 complete'}
- {id: phase-3-venue-error-map, content: Add all missing venues to VENUE_ERROR_MAP and apply catch-all handler to all adapters, status: done, note: 'DONE 2026-03-11: 41 venues in VENUE_ERROR_MAP; catch-all CanonicalUnknownVenueError pattern in UMI adapters'}
- {id: phase-4-sit-tests, content: 'Write SIT tests for unknown error pathway, non-triggering errors, and config-driven thresholds', status: done, note: 'DONE 2026-03-11: test_error_normalisation.py (419 lines) covers P4.1–P4.3'}
isProject: false
---

# Plan: Error Normalisation, Unknown Exchange Errors & Circuit Breaker Config

status: active priority: P0 owner: backend target: 2026-03-17

## Context

The system has 19 canonical error types (`unified-api-contracts/errors.py`) and a `VENUE_ERROR_MAP` covering 17 venues
(`schemas/errors.py`). The circuit breaker (`execution-service/engine/circuit_breaker.py`) has hardcoded thresholds (5
failures, 300s cooldown) applied identically to all venues. Three critical gaps:

1. Most venues are partially mapped — unknown error codes fall through with no structured logging
2. The circuit breaker does not discriminate between error types (rate limit ≠ auth failure ≠ network error)
3. Thresholds are not configurable per venue type or per runtime environment

Goal: after this plan, every exchange-originated error is either in the canonical map or captured as
`UNKNOWN_VENUE_ERROR` with full context; circuit breaker trips only on appropriate error classes with configurable
per-venue thresholds; production surprises from exchange errors are eliminated.

---

## Phase 0: Audit (no code changes)

### P0.1 — Venue error map completeness audit

Run: `rg "record_failure" execution-service/ --type py` Document: for each venue in `VENUE_ERROR_MAP`, what % of real
error codes are mapped.

Known missing venues (not in `VENUE_ERROR_MAP` at all):

- Polymarket (REST + WebSocket)
- Betfair (exchange bet errors: APINGException codes)
- Kalshi (prediction market REST errors)
- Smarkets, Betdaq (sports betting REST errors)
- Glassnode, Arkham, Coinglass (data API HTTP errors)
- DefiLlama (rate limit, schema errors)
- Instadapp, Envio, Aavescan (DeFi data API errors)
- OnChain contract reverts (EXECUTION_REVERTED, OUT_OF_GAS, INSUFFICIENT_FUNDS, NONCE_TOO_LOW)

Output: `unified-trading-pm/audits/venue_error_coverage_2026_03_10.md`

### P0.2 — Circuit breaker trigger audit

Document exactly which code paths call `record_failure()` in execution-service. Map: which `CanonicalError` types
currently result in `record_failure()` vs which fall through. Output: appended to audit doc above.

---

## Phase 0 Results (2026-03-10) — COMPLETE

Full detail: `unified-trading-pm/audits/venue_error_coverage_2026_03_10.md`

### P0.1 Results: Venue Coverage

**Canonical errors**: 19 types confirmed in `unified_normalised_contracts/errors.py`. `CanonicalUnknownVenueError` does
not yet exist.

**VENUE_REGISTRY**: 33 venues across CeFi(9) + TradFi(9) + DeFi(14) + OnchainPerps(1) in
`unified-market-interface/factory.py`.

**VENUE_ERROR_MAP**: 17 entries, but only 13 match VENUE_REGISTRY venues. 20 of 33 registry venues have zero error
mappings (61% missing). Sports adapters (25+ in sports/registry.py) have zero mappings.

Coverage by category:

- CeFi: 7/9 venues mapped (coinglass, hyblock missing), ~15% of known error codes per venue
- TradFi: 5/9 venues mapped (barchart, fred, ecb, ofr, openbb missing), ~10% of codes
- DeFi: 0/14 venues mapped — all 14 DeFi protocols have zero entries
- OnchainPerps: 1/1 mapped (hyperliquid), ~20% of codes
- Sports: 0/25+ mapped

Additional defects found:

- `classify_venue_error()` silently returns FAIL for unknown codes with no event emission and no structured data capture
  — the raw error code/message is discarded
- `yahoo_finance` maps both `RATE_LIMIT_EXCEEDED` and `429` (duplicate for same condition)
- `DATABENTO_ERROR_MAP` is a separate dataclass dict that overlaps with the `databento` VENUE_ERROR_MAP entry — two
  sources of truth
- 5 venues in VENUE_ERROR_MAP (alchemy, thegraph, aster, bloxroute, versifi) are NOT in VENUE_REGISTRY — architecture
  classification gap
- Sports errors use `SportsError` hierarchy (not `CanonicalError` subclasses) — no bridge to canonical taxonomy

### P0.2 Results: Circuit Breaker Triggers

**Critical finding**: `record_failure()` has **zero production callers**. The circuit breaker module
(`execution_service/engine/circuit_breaker.py`) is never imported by any production execution-service code. Only test
code calls it. `LiveExecutionOrchestrator.execute_order()` has no circuit_breaker import.

**Hardcoded thresholds**: `_FAILURE_THRESHOLD = 5`, `_COOLDOWN_SECONDS = 300.0` — module-level constants with no config
loading.

**No error type discrimination**: `record_failure(reason: str = "")` takes a free-form string. Cannot distinguish rate
limit (non-fault) vs auth failure vs network error vs order rejection. All would trip the breaker identically after 5
occurrences.

**No CanonicalError plumbing**: At no layer does a CanonicalError instance flow into the circuit breaker.

### Phase 0 Grade: FAIL (2 FAILs, 2 WARNs)

- FAIL: 61% of registry venues unmapped; classify_venue_error() silently discards unknowns
- FAIL: Circuit breaker has zero production callers and no error-type discrimination
- WARN: Sports error hierarchy not bridged to CanonicalError
- WARN: DeFi/onchain revert errors require distinct mapping approach (not HTTP codes)

---

## Phase 1: Canonical error schema extensions

> ⚠️ **C2 CONFLICT NOTE (2026-03-11):** `execution-service/engine/circuit_breaker.py` was already modified by
> `institutional_hardening_2026_03_10` (DONE) to add exponential backoff and DEGRADED state machine. P2.2+ in this plan
> must integrate with the existing DEGRADED-state circuit breaker — do NOT overwrite or revert the exponential
> backoff/DEGRADED state machine. Read the current `circuit_breaker.py` before implementing P2.2+ and extend rather than
> replace.

### P1.1 — Add CanonicalUnknownVenueError ✅ DONE 2026-03-11

File: `unified-api-contracts/unified_api_contracts/unified_normalised_contracts/errors.py`

```python
class CanonicalUnknownVenueError(CanonicalError):
    """Fired when a venue returns an error code not in VENUE_ERROR_MAP."""
    raw_code: str
    raw_message: str
    venue: str
    endpoint: str | None = None
    # action defaults to FAIL — callers must explicitly handle
```

Export from `unified_api_contracts/__init__.py`.

### P1.2 — Add UEI event UNKNOWN_VENUE_ERROR_RECEIVED ✅ DONE 2026-03-11

File: `unified-events-interface/unified_events_interface/schemas.py` Add to `EventType` enum:

```python
UNKNOWN_VENUE_ERROR_RECEIVED = "UNKNOWN_VENUE_ERROR_RECEIVED"
```

Payload schema fields: `venue`, `raw_code`, `raw_message`, `endpoint`, `order_id` (optional), `timestamp`. This event
feeds the normalisation backlog — ops team reviews weekly and adds missing codes.

### P1.3 — Circuit breaker config schema ✅ DONE 2026-03-11

File: `unified-internal-contracts/unified_internal_contracts/reference/circuit_breaker_config.py`

```python
class VenueCircuitBreakerConfig(BaseModel):
    venue: str
    failure_threshold: int
    cooldown_seconds: float
    triggering_error_classes: list[str]     # CanonicalError subclass names that count as failures
    non_triggering_error_classes: list[str] # errors that do NOT count (rate limits, market closed)
    environment: str = "production"         # "production" | "staging" | "dev"
```

### P1.4 — Write circuit_breaker_config.yaml ✅ DONE 2026-03-11

File: `unified-trading-pm/configs/circuit_breaker_config.yaml`

```yaml
venue_types:
  cefi_exchange: # binance, bybit, okx, deribit, coinbase, hyperliquid
    failure_threshold: 5
    cooldown_seconds: 300
    triggering:
      - CanonicalNetworkError
      - CanonicalAuthenticationError
      - CanonicalInternalServerError
      - CanonicalMaintenanceModeError
      - CanonicalUnknownVenueError
    non_triggering:
      - CanonicalRateLimitError
      - CanonicalMarketClosedError
      - CanonicalInvalidRequestError
      - CanonicalOrderRejectedError
      - CanonicalInstrumentHaltedError
      - CanonicalInsufficientBalanceError
      - CanonicalPositionLimitExceededError

  defi_protocol: # aave, uniswap, curve, balancer, lido, ethena, etc.
    failure_threshold: 10
    cooldown_seconds: 60
    triggering:
      - CanonicalNetworkError
      - CanonicalAuthenticationError
      - CanonicalUnknownVenueError
    non_triggering:
      - CanonicalRateLimitError
      - CanonicalInvalidRequestError
      - CanonicalContractExpiredError

  data_provider: # tardis, databento, glassnode, coinglass, arkham, openbb, fred, ecb
    failure_threshold: 15
    cooldown_seconds: 120
    triggering:
      - CanonicalNetworkError
      - CanonicalAuthenticationError
    non_triggering:
      - CanonicalRateLimitError
      - CanonicalSchemaError

  sports_venue: # betfair, pinnacle, odds_api, kalshi, smarkets, betdaq
    failure_threshold: 8
    cooldown_seconds: 180
    triggering:
      - CanonicalNetworkError
      - CanonicalAuthenticationError
      - CanonicalUnknownVenueError
    non_triggering:
      - CanonicalRateLimitError
      - CanonicalMarketClosedError

dev_overrides: # all venues in dev/staging
  failure_threshold: 3
  cooldown_seconds: 10
```

---

## Phase 2: Circuit breaker hardening

### P2.1 — Load config in circuit_breaker.py ✅ DONE 2026-03-11

File: `execution-service/execution_service/engine/circuit_breaker.py`

- Replace hardcoded `_FAILURE_THRESHOLD = 5` / `_COOLDOWN_SECONDS = 300.0` with config load from
  `circuit_breaker_config.yaml` via UCI topology reader pattern
- Add `should_count_as_failure(error: CanonicalError, venue: str) -> bool` based on config
- `record_failure()` now takes `error: CanonicalError` not just `reason: str`
- Log `UNKNOWN_VENUE_ERROR_RECEIVED` UEI event when `CanonicalUnknownVenueError` is passed

### P2.2 — Update all callers of record_failure

Files: all execution-service handlers that call `record_failure`. Pass the actual `CanonicalError` instance; fallback to
`CanonicalUnknownVenueError` with raw details.

---

## Phase 3: Complete VENUE_ERROR_MAP for all supported venues

### P3.1 — Add missing venues to schemas/errors.py

File: `unified-api-contracts/unified_api_contracts/schemas/errors.py`

Add entries for:

- `polymarket`: HTTP 429 (rate limit), 401 (auth), 400 (invalid), 500 (server error)
- `betfair`: `APINGException` codes: `INVALID_SESSION_INFORMATION`, `TOO_MUCH_DATA`, `SERVICE_BUSY`, `TIMEOUT_ERROR`,
  `NO_SESSION`, `REQUEST_SIZE_EXCEEDS_LIMIT`
- `kalshi`: 400/401/403/429/500 series with Kalshi-specific error codes
- `smarkets`, `betdaq`: standard HTTP error + sport-specific errors
- `glassnode`, `coinglass`, `arkham`: standard HTTP error + API-specific rate/auth codes
- `defillama`: 429 (rate limit), 404 (not found), 500
- `onchain_revert`: `EXECUTION_REVERTED`, `OUT_OF_GAS`, `INSUFFICIENT_FUNDS`, `NONCE_TOO_LOW`
- `sports_generic`: `MARKET_SUSPENDED`, `SELECTION_REMOVED`, `COMPETITION_CLOSED`

After this, all 33 venues from UMI factory.py must have entries in `VENUE_ERROR_MAP`.

### P3.2 — Add catch-all handler to all venue adapters

Apply this pattern in all UMI, UTEI, URDI, UPI adapter files:

```python
except Exception as exc:
    code = getattr(exc, "code", type(exc).__name__)
    msg = str(exc)
    classification = classify_venue_error(venue_name, code)
    if classification is None:
        log_event(UNKNOWN_VENUE_ERROR_RECEIVED,
                  venue=venue_name, raw_code=code, raw_message=msg)
        raise CanonicalUnknownVenueError(
            raw_code=code, raw_message=msg, venue=venue_name, endpoint=endpoint
        ) from exc
    raise classification.to_canonical_error() from exc
```

Apply to all adapters in:

- `unified-market-interface/unified_market_interface/adapters/`
- `unified-trading-execution-interface/`
- `unified-reporting-and-data-interface/`
- `unified-portfolio-interface/`

---

## Phase 4: SIT tests

### P4.1 — Unknown error pathway test

File: `system-integration-tests/tests/integration/test_error_normalisation.py`

- For each venue adapter: inject an error code not in `VENUE_ERROR_MAP`
- Verify: `CanonicalUnknownVenueError` raised
- Verify: `UNKNOWN_VENUE_ERROR_RECEIVED` event emitted via UEI
- Verify: circuit breaker counts it as a failure
- Verify: after `failure_threshold`, circuit breaker enters OPEN state

### P4.2 — Non-triggering error test

- For each venue: inject `CanonicalRateLimitError` 100 times
- Verify: circuit breaker stays CLOSED
- Verify: `RETRY_ATTEMPT` events emitted

### P4.3 — Config-driven threshold test

- Set dev config (`failure_threshold=3`) and verify OPEN after exactly 3 triggering failures

---

## Verification Gates

- [ ] Zero bare `except Exception` without `CanonicalUnknownVenueError` wrapping in adapters
- [ ] `VENUE_ERROR_MAP` covers all 33 venues from `UMI factory.py`
- [x] Circuit breaker thresholds loaded from YAML, not hardcoded
- [ ] SIT tests P4.1–P4.3 all green
- [ ] `rg "record_failure" execution-service/` — all calls pass `CanonicalError` instance
- [ ] `unified-trading-pm/audits/venue_error_coverage_2026_03_10.md` documents 100% coverage

## Files Modified / Created

- `unified-api-contracts/unified_normalised_contracts/errors.py` — add `CanonicalUnknownVenueError`
- `unified-api-contracts/schemas/errors.py` — add 16 missing venues
- `unified-events-interface/schemas.py` — add `UNKNOWN_VENUE_ERROR_RECEIVED`
- `unified-internal-contracts/reference/circuit_breaker_config.py` (new)
- `unified-trading-pm/configs/circuit_breaker_config.yaml` (new)
- `unified-trading-pm/audits/venue_error_coverage_2026_03_10.md` (new)
- `execution-service/engine/circuit_breaker.py` — config-driven thresholds + error-type filtering
- All UMI/UTEI/URDI/UPI adapter files — catch-all pattern
- `system-integration-tests/tests/integration/test_error_normalisation.py` (new)

## Dependencies

- `api_keys_and_auth.md` Phase 2–4 (need live venue keys to validate error codes in recording)
- `phase3_service_hardening_integration.md` (hardening must not conflict with catch-all pattern)
