---
doc_type: plan
title: "NASDAQ/NYSE equity twins eu=828/1746 — backfill VM silently skipped in-window dates (delivery lag or manifest logic bug)"
created: 2026-06-28
parent_epic: tradfi_master
assigned_vm: planning
source:
  - mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27.md
locked_by: live-defi-rollout
summary: "During G2 final verification of `mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27.md`, the tradfi manifest shows `expected_unattempted` rows for NASDAQ (eu=828) and NYSE (eu=1746) equity twin instruments..."
status: active
nature: process
asset_group: tradfi
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
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

**Hypothesis A (DISPROVED 2026-06-28): Databento delivery lag**
- `databento.Historical().metadata.get_dataset_range("XNAS.ITCH")` confirmed on 2026-06-28:
  - ohlcv-1m inclusive range: **2018-05-01 to 2026-06-26** (end `2026-06-27T00:00Z` is exclusive)
  - 2026-05-05 is within range → data IS available → delivery lag DOES NOT explain the skip
- All 36 NASDAQ in-window dates (2026-05-05 → 2026-06-09) fall within the Databento coverage window.
- Hypothesis A is **RULED OUT** as the root cause.

**Hypothesis B (most likely — promoted): Manifest logic skips existing eu entries**
- The VM only writes NEW manifest entries; existing `expected_unattempted` rows from the Jun-25 enumerator
  run are NOT updated by the VM's "check-if-captured" / writer logic.
- Evidence: surrounding dates (pre-listing, post-delisting) received fresh `written_at=2026-06-28T01:31Z`
  entries, but in-window dates still carry `written_at=2026-06-25T00:46Z` (enumerator timestamp) —
  consistent with the writer skipping rows that already have an eu entry.
- **Fix**: The MTDS backfill VM manifest writer must UPDATE (not skip) existing `expected_unattempted`
  rows after each date is processed, writing the correct terminal state (`captured`, `empty_confirmed`,
  or `attempted_failed`).

**Hypothesis C: Databento API error not recorded**
- The VM may have hit a silent error for these dates without writing `attempted_failed`.
- Secondary to B; may co-occur. Fix B first, then verify no residual `attempted_failed` gap.

## Recommended decision

1. **CONFIRMED (2026-06-28)**: Databento XNAS.ITCH ohlcv-1m coverage is 2018-05-01 to 2026-06-26
   (inclusive). 2026-05-05 is within range — Hypothesis A (delivery lag) is RULED OUT.

2. **Root cause is Hypothesis B** (manifest writer skips existing eu rows). Fix the backfill VM
   manifest writer to UPDATE `expected_unattempted` rows with the correct terminal state after
   processing each date. Do NOT write `EXPECTED_SOURCE_DELIVERY_LAG` — data IS available.

3. **For the G2 gate**: After the code fix and re-run, in-window dates should transition to
   `captured` (Databento returned data) or `attempted_failed` (API error occurred). The eu count
   should drop to 0 for these instruments.

## Todos

- [x] ✅ [DATA] P0. Verify Databento XNAS.ITCH coverage for AAPL 2026-05-05 — `metadata.get_dataset_range("XNAS.ITCH")` confirms ohlcv-1m range 2018-05-01→2026-06-26. 2026-05-05 IS in range → delivery lag DISPROVED. Root cause = Hypothesis B (manifest writer skips existing eu entries). — unified-trading-pm@2026-06-28 (slot-10 data_engineering)
- [ ] [CODE] P1. Fix MTDS backfill VM manifest writer to UPDATE (not skip) existing `expected_unattempted` entries with the correct terminal state (`captured`/`empty_confirmed`/`attempted_failed`) after processing each date — delivery lag is NOT the cause, data IS available. (repo: market-tick-data-service)
- [ ] [VERIFY] P1. After code fix: re-run `launch-tradfi-bf-nasdaq-ohlcv-1m.sh --year 2026 --force-recapture` for NASDAQ instruments and `launch-tradfi-bf-nyse-ohlcv-1m.sh --year 2026 --force-recapture` for NYSE, then confirm eu drops to 0 or all entries transition to `captured`/`attempted_failed`. (repo: deployment-service)
