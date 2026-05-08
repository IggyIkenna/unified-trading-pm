# Venue Error Coverage Audit — 2026-03-10

audit_date: 2026-03-10 phase: Phase 0 (read-only — no code changes) auditor: Claude Code (claude-sonnet-4-6) plan:
unified-trading-pm/plans/active/error_normalisation_unknown_exchanges_2026_03_10.md

---

## P0.1 — Venue Error Map Completeness

### Canonical Error Types (19 total)

Source: `unified-api-contracts/unified_api_contracts/unified_normalised_contracts/errors.py`

| #   | Class                               | Code                 | Action    |
| --- | ----------------------------------- | -------------------- | --------- |
| 1   | CanonicalRateLimitError             | RATE_LIMIT           | RETRY     |
| 2   | CanonicalAuthenticationError        | AUTH_FAILED          | FAIL      |
| 3   | CanonicalAuthorizationError         | UNAUTHORIZED         | FAIL      |
| 4   | CanonicalInternalServerError        | SERVER_ERROR         | RETRY     |
| 5   | CanonicalServiceUnavailableError    | SERVICE_UNAVAILABLE  | RETRY     |
| 6   | CanonicalNetworkError               | NETWORK_ERROR        | RETRY     |
| 7   | CanonicalInvalidRequestError        | INVALID_REQUEST      | FAIL      |
| 8   | CanonicalInsufficientBalanceError   | INSUFFICIENT_BALANCE | FAIL      |
| 9   | CanonicalInsufficientMarginError    | INSUFFICIENT_MARGIN  | FAIL      |
| 10  | CanonicalPriceBoundError            | PRICE_BOUND          | FAIL      |
| 11  | CanonicalOrderRejectedError         | ORDER_REJECTED       | FAIL      |
| 12  | CanonicalMarketClosedError          | MARKET_CLOSED        | FAIL      |
| 13  | CanonicalInstrumentHaltedError      | INSTRUMENT_HALTED    | FAIL      |
| 14  | CanonicalDuplicateOrderError        | DUPLICATE_ORDER      | FAIL      |
| 15  | CanonicalPositionLimitExceededError | POSITION_LIMIT       | FAIL      |
| 16  | CanonicalSizeLimitError             | SIZE_LIMIT           | FAIL      |
| 17  | CanonicalContractExpiredError       | CONTRACT_EXPIRED     | FAIL      |
| 18  | CanonicalMaintenanceModeError       | MAINTENANCE          | RECONNECT |
| 19  | CanonicalSchemaError                | SCHEMA_ERROR         | SKIP      |

NOTE: `CanonicalUnknownVenueError` does NOT yet exist — it is the primary deliverable of Phase 1.

---

### VENUE_REGISTRY vs VENUE_ERROR_MAP Coverage

Source for registry: `unified-market-interface/unified_market_interface/factory.py` (33 venues) Source for error map:
`unified-api-contracts/unified_api_contracts/schemas/errors.py` (17 venues mapped)

#### Venues IN VENUE_REGISTRY

**CeFi (9 venues)**

| Venue     | In VENUE_ERROR_MAP | Codes Mapped                                                                  | Coverage Assessment                                                                                                                                                                                                                                                                                                                                                                                  |
| --------- | ------------------ | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| binance   | YES                | 6 codes: -1003, -1021, -1000, -1006, -2011, -1013                             | PARTIAL — Binance has 100+ documented error codes. Missing: -1001 (disconnected), -1002 (unauthorized), -1010 (bad recv window), -1015 (too many new orders), -1016 (no trading day), -1020 (unsupported operation), -2010 (new order rejected), -2013 (no such order), -2014 (API key format invalid), -2015 (invalid API key), -2018 (balance locked), -2019 (margin insufficient) and dozens more |
| bybit     | YES                | 5 codes: 10006, 10000, 10001, 10019, 33004                                    | PARTIAL — Bybit v5 has 50+ error codes. Missing: 10002 (request expired), 10003 (API key invalid), 10004 (sign check error), 10005 (perm denied), 10007 (unmatched IP), 10010 (unmatched perm), 10014 (readonly key), 10016 (internal error), 10020 (cloudflare ban), 30034-30049 (order-specific), 110001-110085 (unified account errors)                                                           |
| okx       | YES                | 4 codes: 50004, 50011, 50026, 51008                                           | PARTIAL — OKX has 200+ error codes. Missing: 50000 (body can't be empty), 50001 (svc unavailable), 50002 (json error), 50003 (svc closed), 50005 (api deprecated), 50010 (duplicate clientId), 50012 (system busy), 50013 (parameter error), 50014-50039 (auth/param errors), 51001-51007 (order errors), 51100-51163 (position errors), 58000-58400 (funding errors)                                |
| deribit   | YES                | 5 codes: 10028, 10040, 11044, 13009, 13010                                    | PARTIAL — Deribit has 30+ error codes. Missing: 10001 (auth required), 10003 (auth failed), 10029 (connection limit), 11008 (not enough funds variant), 11029 (invalid action), 11030 (invalid arguments), 11031 (too many requests), 11032 (not authorized), 11033 (method not found)                                                                                                               |
| coinbase  | YES                | 3 codes: RATE_LIMIT_EXCEEDED, INTERNAL_SERVICE_ERROR, TEMPORARILY_UNAVAILABLE | PARTIAL — Coinbase Advanced Trade has 20+ error codes. Missing: INVALID_ARGUMENT, NOT_FOUND, ALREADY_EXISTS, RESOURCE_EXHAUSTED, FAILED_PRECONDITION, ABORTED, OUT_OF_RANGE, UNIMPLEMENTED, UNAVAILABLE, DATA_LOSS, UNAUTHENTICATED                                                                                                                                                                  |
| ccxt      | YES                | 3 codes: RateLimitExceeded, ExchangeNotAvailable, ExchangeError               | PARTIAL — CCXT has 15+ exception classes. Missing: AuthenticationError, PermissionDenied, InsufficientFunds, InvalidOrder, OrderNotFound, NetworkError, DDoSProtection, ExchangeNotAvailable, OnMaintenance, BadSymbol, BadRequest, RequestTimeout, NotSupported                                                                                                                                     |
| coinglass | NO                 | 0                                                                             | MISSING — No entry in VENUE_ERROR_MAP                                                                                                                                                                                                                                                                                                                                                                |
| hyblock   | NO                 | 0                                                                             | MISSING — No entry in VENUE_ERROR_MAP                                                                                                                                                                                                                                                                                                                                                                |
| upbit     | YES                | 3 codes: invalid_access_key, invalid_query_payload, too_many_requests         | PARTIAL — Upbit has 10+ error codes. Missing: jwt_verification, expired_access_key, nonce_used, no_authorization_i_p, out_of_one_minute, under_min_tot_krw                                                                                                                                                                                                                                           |

**TradFi (9 venues)**

| Venue         | In VENUE_ERROR_MAP | Codes Mapped                                        | Coverage Assessment                                                                                                                                                                                                                                                                                                          |
| ------------- | ------------------ | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| databento     | YES                | 3 codes: RATE_LIMIT, AUTH_FAILURE, CONNECTION_RESET | PARTIAL — Missing: SUBSCRIPTION_ERROR (in DATABENTO_ERROR_MAP but not VENUE_ERROR_MAP — duplicate map exists), SCHEMA_CHANGE, DATASET_NOT_FOUND, PERMISSION_DENIED, INVALID_SCHEMA                                                                                                                                           |
| tardis        | YES                | 3 codes: 401, 429, 500                              | PARTIAL — HTTP only. Missing: 400 (bad request), 403 (forbidden), 404 (not found), specific tardis error body codes                                                                                                                                                                                                          |
| yahoo_finance | YES                | 2 codes: RATE_LIMIT_EXCEEDED, 429                   | PARTIAL (DUPLICATE) — RATE_LIMIT_EXCEEDED and 429 are likely the same condition mapped twice. Missing: 401, 404, 503, yf-specific "No price data found", "Data doesn't exist"                                                                                                                                                |
| barchart      | NO                 | 0                                                   | MISSING — No entry in VENUE_ERROR_MAP                                                                                                                                                                                                                                                                                        |
| fred          | NO                 | 0                                                   | MISSING — No entry in VENUE_ERROR_MAP                                                                                                                                                                                                                                                                                        |
| ecb           | NO                 | 0                                                   | MISSING — No entry in VENUE_ERROR_MAP                                                                                                                                                                                                                                                                                        |
| ofr           | NO                 | 0                                                   | MISSING — No entry in VENUE_ERROR_MAP                                                                                                                                                                                                                                                                                        |
| openbb        | NO                 | 0                                                   | MISSING — No entry in VENUE_ERROR_MAP                                                                                                                                                                                                                                                                                        |
| ibkr          | YES                | 3 codes: 100, 1100, 1300                            | PARTIAL — IBKR has 2000+ error codes. Missing: 101-162 (connection), 200 (no security def found), 201 (order rejected), 202 (order cancelled), 300-399 (order/account errors), 400-449 (algo errors), 500 (socket port reset), 1100-1102 (connectivity), 2100-2158 (user security errors), 2161 (no market data permissions) |

**DeFi (14 protocols)**

| Venue      | In VENUE_ERROR_MAP | Codes Mapped | Coverage Assessment                                                                                                                           |
| ---------- | ------------------ | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| aave_v3    | NO                 | 0            | MISSING — Aave V3 has 100+ on-chain error codes (1-95 numeric) plus RPC/provider errors                                                       |
| balancer   | NO                 | 0            | MISSING — Balancer has BAL#000-BAL#999 error codes (numeric)                                                                                  |
| curve      | NO                 | 0            | MISSING — Curve has revert reason strings (not standardized)                                                                                  |
| ethena     | NO                 | 0            | MISSING                                                                                                                                       |
| euler      | NO                 | 0            | MISSING                                                                                                                                       |
| fluid      | NO                 | 0            | MISSING                                                                                                                                       |
| etherfi    | NO                 | 0            | MISSING                                                                                                                                       |
| lido       | NO                 | 0            | MISSING — Lido uses named revert errors e.g. APP_AUTH_FAILED, NO_NODE_OPERATOR_IN_QUEUE                                                       |
| morpho     | NO                 | 0            | MISSING                                                                                                                                       |
| uniswap_v2 | NO                 | 0            | MISSING — Uniswap V2: UniswapV2: INSUFFICIENT_OUTPUT_AMOUNT, INSUFFICIENT_LIQUIDITY, INSUFFICIENT_INPUT_AMOUNT, K, LOCKED, EXPIRED, FORBIDDEN |
| uniswap_v3 | NO                 | 0            | MISSING — Uniswap V3: named custom errors via ABI                                                                                             |
| uniswap_v4 | NO                 | 0            | MISSING — Uniswap V4: custom errors via PoolManager                                                                                           |
| instadapp  | NO                 | 0            | MISSING                                                                                                                                       |
| defillama  | NO                 | 0            | MISSING                                                                                                                                       |

**Onchain Perps (1 venue)**

| Venue       | In VENUE_ERROR_MAP | Codes Mapped                                       | Coverage Assessment                                                                                                                  |
| ----------- | ------------------ | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| hyperliquid | YES                | 4 codes: 500, 503, RATE_LIMIT, INSUFFICIENT_MARGIN | PARTIAL — Missing: 400 (bad request), 401 (auth), 403, specific HL error codes for order rejection, position limits, leverage errors |

**Venues in VENUE_ERROR_MAP but NOT in VENUE_REGISTRY**

| Venue     | Notes                                                                                                                                          |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| alchemy   | In error map but NOT in UMI VENUE_REGISTRY — used as RPC provider for DeFi adapters; should be under an "rpc_providers" category               |
| thegraph  | In error map but NOT in UMI VENUE_REGISTRY — used as DeFi data source; architecture classification unclear                                     |
| aster     | In error map but NOT in UMI VENUE_REGISTRY — referenced as incomplete onchain perps; likely the "Aster incomplete" noted in factory.py comment |
| bloxroute | In error map but NOT in UMI VENUE_REGISTRY — MEV/transaction relay; architecture classification unclear                                        |
| versifi   | In error map but NOT in UMI VENUE_REGISTRY — institutional DeFi execution; should be in VENUE_REGISTRY                                         |

---

### Sports Venues (separately tracked via UMI sports/registry.py)

These are managed by `unified-sports-execution-interface` adapters, not UMI VENUE_REGISTRY. They have zero
VENUE_ERROR_MAP entries.

**Sports Exchange Adapters (4 venues — highest priority for error mapping)**

| Venue     | In VENUE_ERROR_MAP | Notes                                                                                                                                                                                                     |
| --------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| betfair   | NO                 | APINGException codes: INVALID_SESSION_INFORMATION, TOO_MUCH_DATA, SERVICE_BUSY, TIMEOUT_ERROR, NO_SESSION, REQUEST_SIZE_EXCEEDS_LIMIT, INVALID_APP_TOKEN, TOO_MANY_REQUESTS, ACCESS_DENIED — all unmapped |
| smarkets  | NO                 | REST API HTTP errors + sports-specific codes — all unmapped                                                                                                                                               |
| matchbook | NO                 | REST API HTTP errors — all unmapped                                                                                                                                                                       |
| betdaq    | NO                 | REST API errors — all unmapped                                                                                                                                                                            |

**Sports Bookmaker API Adapters (2 venues)**

| Venue    | In VENUE_ERROR_MAP | Notes                                                 |
| -------- | ------------------ | ----------------------------------------------------- |
| pinnacle | NO                 | REST API errors + line-not-found codes — all unmapped |
| onexbet  | NO                 | REST API errors — all unmapped                        |

**Sports Aggregator APIs (5 venues)**

| Venue     | In VENUE_ERROR_MAP | Notes                                                |
| --------- | ------------------ | ---------------------------------------------------- |
| odds_api  | NO                 | HTTP 401/422/429/500 + quota exceeded — all unmapped |
| opticodds | NO                 | — all unmapped                                       |
| oddsjam   | NO                 | — all unmapped                                       |
| sharpapi  | NO                 | — all unmapped                                       |
| metabet   | NO                 | — all unmapped                                       |

**Sports Scraper Adapters (14 venues: skybet, coral, paddypower, betfred, betvictor, boylesports, bwin, ladbrokes,
williamhill, betway, unibet, bet888sport, bet365, sbo)**

All 14 have zero VENUE_ERROR_MAP entries. Scrapers typically raise ScraperError (from sports/errors.py) which is NOT a
CanonicalError subclass and is not routed through the circuit breaker.

---

### Summary: Coverage by Category

| Category                                    | Venues in Registry/Registry | Venues in VENUE_ERROR_MAP                        | % Covered                        |
| ------------------------------------------- | --------------------------- | ------------------------------------------------ | -------------------------------- |
| CeFi (VENUE_REGISTRY)                       | 9                           | 7 (coinglass, hyblock missing)                   | 78% venues, ~15% codes           |
| TradFi (VENUE_REGISTRY)                     | 9                           | 5 (barchart, fred, ecb, ofr, openbb missing)     | 56% venues, ~10% codes           |
| DeFi (VENUE_REGISTRY)                       | 14                          | 0                                                | 0%                               |
| Onchain Perps (VENUE_REGISTRY)              | 1                           | 1 (hyperliquid)                                  | 100% venues, ~20% codes          |
| Sports exchanges                            | 4                           | 0                                                | 0%                               |
| Sports bookmakers/aggregators               | 24                          | 0                                                | 0%                               |
| Extra (in error map, not in VENUE_REGISTRY) | N/A                         | 5 (alchemy, thegraph, aster, bloxroute, versifi) | —                                |
| **TOTAL**                                   | **61**                      | **13 of 33 registry venues**                     | **39% venues, <10% error codes** |

### Critical Architecture Gap: classify_venue_error() Silent Fallthrough

`classify_venue_error()` in `schemas/errors.py` (line 596-615) currently returns a default `VenueErrorClassification`
with `action=FAIL, retry_safe=False, description="Unknown error"` for any unrecognized code — including for venues not
in the map at all.

This means unknown errors are silently treated as permanent failures with no structured logging of the raw code/message.
There is no `UNKNOWN_VENUE_ERROR_RECEIVED` event emission and no `CanonicalUnknownVenueError` to carry the raw data.

---

## P0.2 — Circuit Breaker Trigger Audit

### Hardcoded Thresholds

Source: `execution-service/execution_service/engine/circuit_breaker.py`

```
_FAILURE_THRESHOLD: int = 5       # module-level constant, line 33
_COOLDOWN_SECONDS: float = 300.0  # module-level constant, line 34
```

Both values are module-level constants. There is no config loading, no YAML parsing, no per-venue override, and no
per-environment override. All 33 VENUE_REGISTRY venues (and all sports venues) share identical thresholds.

### record_failure() Signature

```python
def record_failure(self, reason: str = "") -> None:
```

The `reason` parameter is a free-form string. There is no `CanonicalError` parameter. The circuit breaker has no
knowledge of error type — it cannot distinguish:

- Rate limit (should NOT trip breaker — venue is healthy, we are being throttled)
- Auth failure (SHOULD trip breaker — credentials invalid)
- Network error (SHOULD trip breaker — venue unreachable)
- Market closed (should NOT trip breaker — normal market condition)
- Order rejected (should NOT trip breaker — our order was bad, venue is fine)

### Production Callers of record_failure()

**rg result (production code, excluding tests and venv):**

Output was empty — meaning `record_failure()` is called ONLY in:

1. The circuit breaker module itself (docstring example and the definition)
2. Tests in `tests/unit/engine/test_circuit_breaker.py`

**The circuit breaker has zero production callers.** It is an isolated module that is never imported or used anywhere in
the execution-service production code path.

Specifically confirmed:

- `execution_service/engine/live/orchestrator.py` — does NOT import circuit_breaker
- `execution_service/engine/live/factory.py` — not checked but no import found
- No execution, routing, or handler module imports `circuit_breaker`

This is a **critical gap**: the 3-state machine exists and has been tested in isolation, but it is never invoked during
actual order execution.

### What Error Types Currently Result in record_failure()?

**None** — because the circuit breaker has no production callers. In the test suite, `record_failure()` is called with
raw string reasons (`"test-failure"`, `"probe failed"`, `"exchange error"`) with no CanonicalError type discrimination.

### Circuit Breaker State Transitions (as implemented)

```
CLOSED  → OPEN:       when consecutive_failures >= 5 (any failure, any type)
OPEN    → HALF_OPEN:  after 300 seconds elapsed
HALF_OPEN → CLOSED:   on record_success()
HALF_OPEN → OPEN:     on any record_failure() (resets 300s cooldown)
```

The HALF_OPEN → OPEN re-trip is particularly aggressive: any single failure in HALF_OPEN restarts the full 300s
cooldown, even for a rate limit error.

### UEI Events Emitted by Circuit Breaker

| Event                     | Emitted When            | Missing                                    |
| ------------------------- | ----------------------- | ------------------------------------------ |
| CIRCUIT_BREAKER_OPEN      | CLOSED/HALF_OPEN → OPEN | No CIRCUIT_BREAKER_TRIPPED with error type |
| CIRCUIT_BREAKER_HALF_OPEN | cooldown elapsed        | —                                          |
| CIRCUIT_BREAKER_CLOSED    | HALF_OPEN → CLOSED      | —                                          |

`UNKNOWN_VENUE_ERROR_RECEIVED` does NOT exist in UEI — must be added in Phase 1.

---

## Findings Summary

### FAIL — Venue Error Coverage

- 20 of 33 VENUE_REGISTRY venues have zero VENUE_ERROR_MAP entries (61% missing)
- 57+ sports venues (sports/registry.py) have zero VENUE_ERROR_MAP entries
- Mapped venues cover only ~10% of documented real-world error codes
- `classify_venue_error()` silently returns a default FAIL classification for unknowns with no event emission
- Duplicate: `yahoo_finance` maps both `RATE_LIMIT_EXCEEDED` and `429` — same condition
- Orphan: `DATABENTO_ERROR_MAP` is a separate dataclass map that overlaps with the `databento` entry in
  `VENUE_ERROR_MAP` — two sources of truth for the same venue
- Architecture orphans: alchemy, thegraph, aster, bloxroute, versifi are in VENUE_ERROR_MAP but not VENUE_REGISTRY

### FAIL — Circuit Breaker Integration

- Circuit breaker has **zero production callers** — it is entirely unwired from the execution path
- Thresholds hardcoded: `_FAILURE_THRESHOLD=5`, `_COOLDOWN_SECONDS=300.0` — not configurable
- `record_failure(reason: str)` cannot discriminate error types
- Rate limit errors (non-venue-fault) would trip the breaker identically to auth failures
- No `CanonicalError` plumbing at any layer

### WARN — Sports Error Isolation

- Sports errors use `SportsError` hierarchy (sports/errors.py) — NOT `CanonicalError` subclasses
- `BookmakerUnavailableError`, `BetRejectedError`, `OddsChangedError`, `MarketClosedError`, `ScraperError`,
  `FixtureNotFoundError` are unrelated to the canonical error taxonomy
- These will require bridging (sports canonical → CanonicalError) in Phase 3

### WARN — OnChain/DeFi Error Gap

- All 14 DeFi protocols have zero error mappings
- DeFi errors are contract revert strings (not HTTP codes) — need a distinct mapping approach
- On-chain errors: `EXECUTION_REVERTED`, `OUT_OF_GAS`, `INSUFFICIENT_FUNDS`, `NONCE_TOO_LOW` are not represented in
  canonical types
- No `CanonicalContractRevertError` class exists (distinct from `CanonicalInvalidRequestError`)

---

## Recommended Phase 1–3 Priorities (informed by audit)

1. **P1 (immediate)**: Add `CanonicalUnknownVenueError` and `UNKNOWN_VENUE_ERROR_RECEIVED` UEI event
2. **P1 (immediate)**: Wire circuit breaker into `LiveExecutionOrchestrator.execute_order()` — it has zero callers today
3. **P2 (sprint)**: Make thresholds config-driven; add `should_count_as_failure()` discriminator
4. **P2 (sprint)**: Complete CeFi + TradFi error maps (binance, bybit, okx, deribit, coinbase, ibkr are highest
   priority)
5. **P3 (next sprint)**: DeFi error maps — requires separate `ONCHAIN_ERROR_MAP` for revert codes
6. **P3 (next sprint)**: Sports error bridge — map SportsError subclasses to CanonicalError equivalents
7. **Cleanup**: Remove DATABENTO_ERROR_MAP (or unify with VENUE_ERROR_MAP databento entry)
8. **Cleanup**: Register alchemy, thegraph, bloxroute, versifi in VENUE_REGISTRY or move them to a separate
   RPC_PROVIDER_ERROR_MAP

---

## Files Audited

- `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-api-contracts/unified_api_contracts/unified_normalised_contracts/errors.py`
  — 19 canonical types confirmed
- `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-api-contracts/unified_api_contracts/schemas/errors.py`
  — 17-venue VENUE_ERROR_MAP, classify_venue_error() fallthrough confirmed
- `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-api-contracts/unified_api_contracts/unified_api_contracts_external/sports/errors.py`
  — sports error hierarchy (not CanonicalError subclasses)
- `/Users/ikennaigboaka/Code/unified-trading-system-repos/execution-service/execution_service/engine/circuit_breaker.py`
  — hardcoded thresholds, no production callers
- `/Users/ikennaigboaka/Code/unified-trading-system-repos/execution-service/execution_service/engine/live/orchestrator.py`
  — confirmed: no circuit_breaker import
- `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-market-interface/unified_market_interface/factory.py`
  — 33-venue VENUE_REGISTRY (source of truth)
- `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-market-interface/unified_market_interface/sports/registry.py`
  — 25-entry sports adapter registry
