---
title: Databento 402 / PAYG-exhaustion had no explicit classifier — would retry-thrash a billing wall
created: 2026-05-17
author: ikenna-main (slot-1 cycle audit)
resolved: 2026-05-17
resolution:
  SHIPPED — UAC@50f3939 added "402" + "DATABENTO_PAYMENT_REQUIRED" classifier entries (action=FAIL, retry=False).
  MTDS@f42d6c0 _classify_databento_exception now detects 402 via http_status + message-string fallback. 8/8 new unit
  tests pass.
source:
  - operator question 2026-05-17 ~12:30 UTC ("if we ran out of money with databento would that be attempted failed or
    empty confirmed?")
  - grep audit of unified_api_contracts/canonical/crosscutting/errors/tradfi.py § "databento" — no 402 entry; only
    401/429/400/500/RATE_LIMIT/AUTH_FAILURE/CONNECTION_RESET/VALIDATION_ERROR/NOT_FOUND/SERVER_ERROR
locked_by: live-defi-rollout
locked_since: 2026-05-17
severity:
  P2 — would not silently corrupt data (manifest correctly writes attempted_failed) but would burn unnecessary retry
  requests against a billing-wall, inflating bill + delaying operator alert
---

## What I found

The Databento adapter (`market-tick-data-service/.../databento_adapter.py:_classify_databento_exception`) maps SDK
exceptions to UAC classifier codes via `VENUE_ERRORS_TRADFI["databento"]` (`unified-api-contracts/.../tradfi.py`). The
canonical entries covered
401/429/400/500/RATE_LIMIT/AUTH_FAILURE/CONNECTION_RESET/VALIDATION_ERROR/NOT_FOUND/SERVER_ERROR but **NOT 402 (Payment
Required)**. The classifier function's string-match fallback also lacked any pattern for "insufficient credit" /
"payment required" / "quota exceeded" / "billing".

**Behaviour pre-fix**: a PAYG credit-exhaustion event would surface as `BentoHttpError(http_status=402)` → classifier
returns `"402"` (the digit, because `http_status` attribute is present) → UAC's `classify_venue_error()` finds no
matching entry → falls back to a default (likely `UNKNOWN` / retryable). Or if the SDK only surfaced the condition via
exception message text without http_status, the classifier would fall through to `"DATABENTO_FETCH_FAILED"` — also
either retried or wrong-classified. Net: the orchestrator's retry loop would burn additional Databento requests against
a billing wall before giving up, inflating cost + delaying the operator-visible failure signal.

**Manifest correctness was preserved** (attempted_failed would still be written eventually) — but the retry-thrash is
operationally bad.

## Why it matters

The Phase 8 PAYG-spend telemetry (`DATABENTO_PAYG_SPEND` event emission shipped 2026-05-17 at
`market-tick-data-service@1b0a207`) gives operator per-batch cost visibility AFTER a successful request. The
PAYMENT_REQUIRED classifier is the **other half** of that telemetry surface: it gives operator a clean halt signal the
moment a billing wall is hit, instead of:

1. PAYG-spend events keep emitting normally → operator can't distinguish "OK, just slow" from "billing wall".
2. Retry loop burns 15+ additional 402-getting requests per shard before giving up (Databento SDK default
   `max_retries=15`).
3. Eventually shard surfaces `attempted_failed` with `error_code="UNKNOWN"` or `"DATABENTO_FETCH_FAILED"` — operator has
   to grep run.log to identify the actual cause.

With the fix:

1. First 402 → classifier returns `"DATABENTO_PAYMENT_REQUIRED"` → UAC `classify_venue_error()` returns
   `action=FAIL, retry=False`.
2. Orchestrator writes `attempted_failed` with the typed code on the first attempt → no retry-thrash.
3. `ADAPTER_FETCH_FAILED` event carries `error_code="402"` or `"DATABENTO_PAYMENT_REQUIRED"` → operator alerting can
   route this specific code to a high-priority channel ("billing!").

## Recommended decision

SHIPPED — see resolution.

## What shipped

### UAC@50f3939 — canonical classifier entries

Added two entries to `VENUE_ERRORS_TRADFI["databento"]`:

```python
ve("databento", "402", retry=False, reconnect=False, action=ErrorAction.FAIL,
   desc="Payment Required — PAYG credit exhausted / billing failure (DO NOT retry)"),
ve("databento", "DATABENTO_PAYMENT_REQUIRED", retry=False, reconnect=False, action=ErrorAction.FAIL,
   desc="Payment Required from error message (insufficient credit / quota exceeded)"),
```

### MTDS@f42d6c0 — classifier function detection

`_classify_databento_exception()` now checks for the PAYMENT_REQUIRED condition BEFORE the existing 429/401/etc.
branches. Message-substring patterns covered: `"payment required"`, `"insufficient credit"`, `"insufficient funds"`,
`"quota exceeded"`, `"billing"`, `" 402"`. Test file:
`tests/market_interface/adapters/tradfi/test_databento_exception_classifier.py` — 8 tests (4 new + 4 regression-guards
on existing 401/429/fallback codes). All green.

## Cross-references

- Composes with Phase 8 `DATABENTO_PAYG_SPEND` emission at `market-tick-data-service@1b0a207` (PM commit cycle
  2026-05-17 ~10:00 UTC).
- Same operator question that triggered this audit confirmed the `attempted_failed` vs `empty_confirmed` boundary:
  `empty_confirmed` is reserved for "vendor said 0 rows" (HTTP 200 + empty result), `attempted_failed` is for "request
  itself failed" (any HTTP error / exception / timeout). The fix preserves that boundary.

execution: owner: ikenna-main cadence: one-shot verifier: 8/8 unit tests pass on MTDS QG last_executed: 2026-05-17

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED  
**Triaged by**: slot-8 triage sweep  
**Reason**: Resolved 2026-05-17; classifier entries added UAC@50f3939
