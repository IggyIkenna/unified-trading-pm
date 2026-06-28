---
title: "NASDAQ/NYSE equity twins eu=828/1746 — backfill VM silently skipped in-window dates (delivery lag or manifest logic bug)"
created: 2026-06-28
author: "mvp_backfill_tradfi_ohlcv1m_v10 G2 verification (slot-3 data_engineering)"
parent_epic: tradfi_master
assigned_vm: planning
source:
  - mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27.md
locked_by: live-defi-rollout
---

# NASDAQ/NYSE equity twins: eu=828/1746 — silent skip in active listing window

## What I found

During G2 final verification of `mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27.md`, the tradfi manifest
shows `expected_unattempted` rows for NASDAQ (eu=828) and NYSE (eu=1746) equity twin instruments for
dates within their active listing window in `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`.

**Key evidence (NASDAQ/AAPL example):**

```
2026-05-01→2026-05-04:  empty_confirmed  EXPECTED_INSTRUMENT_NOT_LISTED   written_at=2026-06-28T01:31Z
2026-05-05→2026-06-09:  expected_unattempted                               written_at=2026-06-25T00:46Z ← UNCHANGED
2026-06-10→2026-06-15:  empty_confirmed  EXPECTED_INSTRUMENT_DELISTED     written_at=2026-06-28T01:31Z
```

The NASDAQ-2026 VM (tradfi-bf-nasdaq-ohlcv-1m-2026-20260627-210355) ran from 21:03 UTC to ~01:32 UTC
(4h29m) and correctly classified pre-listing and post-delisting dates. But the 36 in-window dates
(May 5 to Jun 9) remain as `expected_unattempted` with the OLD `written_at=2026-06-25` timestamp — 
the VM did NOT update these entries.

**Affected scope:**
- NASDAQ: 23 instruments × 36 trading days = 828 eu rows (2026-05-05 → 2026-06-09)
- NYSE: 21 instruments × ~83 trading days = 1,746 eu rows (2026-02-20 → 2026-06-28)
  - NYSE-2026 VM still running at time of filing (started 2026-06-27T21:04Z)

**Instruments affected (NASDAQ):** AAPL, ADBE, AMAT, AMD, AMZN, AVGO, COST, CSCO, GOOGL,
KLAC, LRCX, META, MSFT, MU, NFLX, NVDA, QCOM, TSLA, WMT, ETHA + 3 others

## Why it matters

This violates the **honest-absence HARD RULE**: `expected_unattempted` means "not yet attempted" —
if the VM attempted to download these dates but got no data, the entries MUST be updated to either:
- `captured` (got data)
- `empty_confirmed + EXPECTED_SOURCE_DELIVERY_LAG` (Databento doesn't have data yet — delivery lag)
- `attempted_failed + SCHEMA_VALIDATION_FAILED / rate_limited / etc.` (genuine failure)

Leaving them as `expected_unattempted` after the VM ran is a **silent placeholder** — it looks like
"not yet attempted" but the VM DID process 2026 and DID write entries for surrounding dates.

The G2 gate ("eu=0 for MVP universe") cannot be met until these are resolved.

## Root cause hypotheses

**Hypothesis A (most likely): Databento delivery lag**
- Databento XNAS.ITCH historical data has a delivery lag of 30-90 days
- Dates 2026-05-05 to 2026-06-09 are 19-54 days ago — within the lag window for some datasets
- The VM got 0 rows from Databento and should classify as `empty_confirmed + EXPECTED_SOURCE_DELIVERY_LAG`
- BUT instead of updating the manifest entry, the VM logic leaves it as `expected_unattempted`
- **Fix**: Update the manifest writer in MTDS/deployment-service to write
  `empty_confirmed + EXPECTED_SOURCE_DELIVERY_LAG` when Databento returns 0 rows for an in-window date

**Hypothesis B: Manifest logic skips existing eu entries**
- The VM only writes NEW manifest entries, not updates to existing `expected_unattempted` rows
- If the enumerator already wrote eu entries (Jun 25), the VM's "check-if-captured" logic might skip them
- **Fix**: Ensure VM's manifest writer UPDATES existing eu entries after processing each date

**Hypothesis C: Databento API error not recorded**
- The VM hit a rate limit or API error for these specific dates and silently skipped
- Should have been recorded as `attempted_failed` but wasn't
- **Fix**: Wrap Databento API calls with proper error handling that writes `attempted_failed`

## Recommended decision

1. **Check Databento coverage**: Does `databento.Client().timeseries.get_data_range()` for
   XNAS.ITCH for AAPL on 2026-05-05 return data? If not → Hypothesis A is correct.

2. **If Hypothesis A**: Update the MTDS/deployment-service backfill VM to write
   `empty_confirmed + EXPECTED_SOURCE_DELIVERY_LAG` when the Databento query succeeds but returns
   0 rows for a date that IS within the instrument's listing window. These will self-resolve when
   Databento delivers the historical data.

3. **For the G2 gate**: These 828+1746 rows cannot be made `captured` until Databento delivers
   the data. Once correctly classified as `empty_confirmed + EXPECTED_SOURCE_DELIVERY_LAG`, they
   are excluded from the G2 denominator and the gate can be met.

## Todos

- [ ] [DATA] P0. Verify Databento XNAS.ITCH coverage for AAPL 2026-05-05 in `market-tick-data-service`: run `databento.Client().metadata.get_dataset_range("XNAS.ITCH")` — check if 2026-05-05 is within the available range. If not → confirms delivery lag. (repo: market-tick-data-service)
- [ ] [CODE] P1. Fix MTDS backfill VM manifest writer to update `expected_unattempted` entries to `empty_confirmed + EXPECTED_SOURCE_DELIVERY_LAG` when Databento returns 0 rows for a date within the instrument's listing window (currently silently skipped). (repo: market-tick-data-service)
- [ ] [VERIFY] P1. After code fix: re-run `launch-tradfi-bf-nasdaq-ohlcv-1m.sh --year 2026 --force-recapture` for NASDAQ instruments and `launch-tradfi-bf-nyse-ohlcv-1m.sh --year 2026 --force-recapture` for NYSE, then confirm eu drops or transitions to honest-empty. (repo: deployment-service)
