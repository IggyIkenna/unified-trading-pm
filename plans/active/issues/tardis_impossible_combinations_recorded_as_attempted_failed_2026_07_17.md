---
doc_type: issue
title:
  Tardis "impossible combinations" (symbol not archived / date outside listing) return HTTP 400 and are recorded as
  attempted_failed — they corrupt the coverage denominator AND are retried forever
summary:
  Tardis answers two structurally-impossible requests with HTTP 400 + a distinguishing JSON code - code=300 "Invalid
  'symbol' param" (the symbol is not in Tardis's archive at all) and code=140 "Requested dataset is not available for
  <date>" (the symbol IS archived but the date is outside its availableSince..availableTo). Neither is a fetch failure,
  but tardis_csv_transport only treats 404 as honest absence and RAISES everything else, so the per-shard runner routes
  both to record_failed -> attempted_failed. That is in the honest-coverage denominator (so phantom combos permanently
  depress measured coverage) and it reads as retryable (so every future run re-requests known-impossible shards). The
  live VM walks 2020->2026 across 17 venues while e.g. bybit AAVEUSDT only lists from 2021-05-13 and AAVEPERP from
  2025-04-30, making code=140 a large systematic multiplier. Tardis's own catalog supplies the exact 3-tuple to gate on
  (symbol x dataTypes x availableSince..availableTo) - the fix is a vendor-catalog intersection, NOT a symbol mapping
  change (the mapping is correct - AAVEUSDC is a genuine Bybit symbol Tardis simply never archived).
status: open
resolved_by:
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags:
  [cefi, tardis, honest-coverage, denominator, attempted-failed, impossible-combinations, data-correctness, big-finding]
related:
  [
    /plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    /plans/archive/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md,
  ]
created: 2026-07-17
source:
  - Operator questions 2026-07-17 ("is it doing data that doesnt exist or is it just skipping", "why you looking for
    wrong symbol dont we have a converter / mapping", "is it the date (available for and to?)") - all three proved
    correct against live measurement; the date hypothesis in particular surfaced a class I had missed.
assigned_vm: NA
assigned_role: data_engineering
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
drift_direction: advance-code
parent_epic: cefi_master
execution_scope: local-only
depends_on: []
last_updated: 2026-07-17
locked_by:
locked_since:
---

# Tardis impossible combinations are recorded as `attempted_failed`

## Measured (live, 2026-07-17, real key, on the VM)

| request                                     | Tardis response                                                        | our status          |
| ------------------------------------------- | ---------------------------------------------------------------------- | ------------------- |
| `bybit/book_snapshot_5/2026-02-02/AAVEUSDC` | `400` **`code=300`** — _"Invalid 'symbol' param provided: 'AAVEUSDC'"_ | `attempted_failed`  |
| `bybit/trades/2020-01-02/AAVEUSDT`          | `400` **`code=140`** — _"Requested dataset is not available for …"_    | `attempted_failed`  |
| `bybit/trades/2026-02-02/AAVEUSDT`          | `302` -> Wasabi -> data                                                | `captured` ✓        |
| `bybit/trades/…/<empty day>`                | `200` + 0 rows ("Empty CSV")                                           | `empty_confirmed` ✓ |

Both 400s are **permanent, structural absences**, not fetch failures.

## Why it happens

`tardis_csv_transport.py:514-524` (CF-11, 2026-06-10) treats **only 404** as honest absence and RAISEs everything else
so the runner routes `record_failed` — a design aimed at 5xx/429 outages (correct for those). HTTP 400 was never
distinguished, so it inherits the outage path. `tardis_batch_download.py:237` then records `attempted_failed`; only the
literal `"Empty CSV"` string escapes to `record_zero_rows(SOURCE_RETURNED_ZERO)`.

`_classify_tardis_error` does a code-token extract + `classify_venue_error(venue, token)` lookup, but **UAC registers no
Tardis error codes at all** — so 300/140 fall through as raw tokens and the status is `attempted_failed` regardless.

## Why it matters (two harms, the second is worse)

1. **Denominator corruption.** `attempted_failed` sits in the honest-coverage denominator
   (`captured/(captured+attempted_failed+expected_unattempted)`), so every impossible combo permanently depresses
   measured coverage. This is exactly the class the operator ruled out of scope: _"its the literally impossible
   combinations i dont even need in empty confirmed"_.
2. **Infinite retry.** `attempted_failed` reads as retryable, so **every future run re-requests known-impossible
   shards**. This is the engine behind the measured **87% dud rate** (25 successes vs 95 HTTP 400 + 69 Empty CSV + 7 404
   in one run) and it never decays.

**Systematic multiplier**: the live VM walks **2020 -> 2026** across 17 venues, while bybit `AAVEUSDT` lists from
**2021-05-13** and `AAVEPERP` from **2025-04-30**. Every (symbol x pre-listing date x data_type) is a guaranteed
`code=140`.

**NOT a throughput lever**: duds resolve in milliseconds (6 in the same second, measured) and transfer no bytes. Fixing
this improves coverage ACCURACY and cuts wasted requests; it does not move MB/s. The MB/s fix was the dedicated parse
executor (`market-tick-data-service@2e7c2b5d`).

**NOT a mapping bug**: `AAVEUSDC` is a genuine live Bybit symbol (bybit `/v5/market/instruments-info` returns it).
instruments-service is right; Tardis simply archives a **subset** (1712 bybit symbols, `AAVEUSDC` absent — it has
`AAVEPERP`/`AAVEUSD`/`AAVEUSDT`). The universes differ; no converter can bridge that.

## The fix — intersect with the vendor catalog

`GET https://api.tardis.dev/v1/exchanges/<venue>` -> `datasets.symbols[]`, each carrying exactly the 3-tuple needed:

```json
{ "id": "AAVEUSDT", "type": "spot",
  "dataTypes": ["trades", "book_snapshot_5", ...],
  "availableSince": "2021-05-13T00:00:00.000Z",
  "availableTo": "2026-07-17T00:00:00.000Z" }
```

Gate every request on **symbol ∈ catalog** AND **data_type ∈ symbol.dataTypes** AND **availableSince <= date <=
availableTo**. Anything failing that is an impossible combination: never request it, never record a row for it, keep it
out of the denominator. One cheap cacheable call per venue (the endpoint Tardis's own 400 message points at).

## Todos

- [ ] [CODE] P0. Gate the Tardis request universe on the vendor catalog (symbol x data_type x date-range). Cache the
      per-venue catalog; refresh daily. This is the operator's "impossible combinations" exclusion with the VENDOR as
      the authority — coordinate with the in-flight `coverage_exclusions` work in unified-api-contracts (another agent,
      live as of 2026-07-17).
- [x] ✅ [CODE] P0. Stop recording impossible combos as `attempted_failed`. Distinguish by Tardis JSON code: `140`/`300`
      -> honest absence / excluded (NOT the denominator); keep 5xx/429/`274` -> `attempted_failed` (genuinely
      transient). The body is ALREADY captured on `TardisHTTPError` (added for the 274 lock) — it is simply discarded on
      the 400 path. — **DONE**: `market-tick-data-service@a7569298` (2026-07-18).
- [x] ✅ [CODE] P1. **Log the Tardis error code.** `tardis_csv_transport.py:523` logs only `"Tardis HTTP %s error"`, so
      `code=300` and `code=140` are indistinguishable in the logs — the split is currently UNMEASURABLE. Log the code
      before anything tries to size this. — **VERIFIED DONE 2026-07-26**: the same commit `a7569298` already added
      `code=%s` to both 400-path log lines (streaming + non-streaming).
- [ ] [DATA] P1. Size the damage: count existing `attempted_failed` rows attributable to 400s, and purge/reclassify them
      (operator-gated, snapshot-first, like the 2026-07-17 eu purge). Expect a real coverage-% correction upward.
- [x] ✅ [CONTRACT] P2. Register Tardis error codes in UAC (`classify_venue_error` currently knows none), so the
      honest-absence-vs-fetch-failure decision is contract-driven rather than string-matched on `"Empty CSV"`. — **DONE
      2026-07-26**: `unified-api-contracts@c144f975` — `140`/`300` registered as `ErrorAction.SKIP`, 2 new unit tests,
      QG green.

## Progress Log (append-only)

- 2026-07-17: filed. Found by following three operator questions in sequence — "is it doing data that doesn't exist",
  "don't we have a converter/mapping", and decisively "is it the date (available for and to?)". The first two led to
  code=300; the third surfaced **code=140**, a separate class I had missed and the one with the large systematic
  multiplier given the 2020->2026 walk. All verified live against the real API with the production key, not inferred.
