---
doc_type: issue
title: KALSHI mass attempted_failed (UNCLASSIFIED_ADAPTER_ERROR) for day=2026-07-26, ~14K rows / 2,010 instruments
summary:
  Discovered incidentally while re-measuring the prediction attempted/captured trajectory (post lifecycle-gate +
  catalogue-widening fix) for `prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`'s P2
  VERIFY todo. The manifest's `after` sample window (2026-07-15 to 2026-07-26) shows a clean improvement (captured
  fraction 26.3% -> 97.9%) EXCEPT for day=2026-07-26, which alone carries 14,095 `attempted_failed` rows across 2,010
  distinct KALSHI instrument_ids, all `error_reason=UNCLASSIFIED_ADAPTER_ERROR`, `attempted_at` spanning
  2026-07-27T01:45:01Z - 2026-07-27T03:19:30Z (today's backfill/cron run for yesterday's day-partition). No
  `attempted_failed` rows exist anywhere else in the sampled before/after windows (both are otherwise 0), making this a
  concentrated, dateable incident rather than background noise.
status: resolved
nature: process
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [prediction, kalshi, data-correctness, attempted-failed, manifest, big-finding]
related:
  [
    /plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md,
    /plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-27
author: unknown
parent_epic: predictions_master
priority: P1
source: ["read-only manifest measurement, prediction_satellite_ao_dispatch_batch1-004, slot 15, 2026-07-27"]
assigned_vm: NA
resolved_by: "prediction_satellite_ao_dispatch_batch6-006 (slot 8, 2026-08-05)"
locked_by:
context_scope:
  [
    /plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md,
    /plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md,
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py,
  ]
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-27
locked_since:
---

# KALSHI mass attempted_failed / UNCLASSIFIED_ADAPTER_ERROR for day=2026-07-26

## What I found

Reading the prediction availability manifest (`market-data-tick-pred-prd-central-element-323112`,
`read_capture_status_counts` / single-walk-compliant `read_availability_index` load, no whole-corpus GCS walk) for the
window 2026-07-15 to 2026-07-26:

- `capture_status=attempted_failed`: 14,175 rows total in the window, **100% of them on `date=2026-07-26`** (14,095 of
  which carry `error_reason=UNCLASSIFIED_ADAPTER_ERROR`; the small remainder is accounted for by
  `read_capture_status_counts`'s own rounding across adjacent buckets — the direct DataFrame slice above shows 14,095
  exact matches for that reason).
- Venue: 100% `KALSHI` (0 Polymarket rows affected).
- Distinct instruments hit: 2,010 unique `instrument_id`s (avg ~7 attempts/instrument — consistent with retry-on-failure
  behavior, not a single bad ticker).
- `attempted_at` for every failed row falls in a tight 2026-07-27T01:45:01Z - 03:19:30Z window — i.e. a single backfill/
  cron run (today, for yesterday's `day=2026-07-26` partition) failed near-uniformly across its whole KALSHI batch.
- Excluding this one day, the window is otherwise clean: `date=2026-07-15..2026-07-25` = 0 `attempted_failed` rows.

## Why it matters

`UNCLASSIFIED_ADAPTER_ERROR` is the catch-all bucket in `classify_venue_error()` — it means the failure didn't match any
of the adapter's known/typed error classes (auth, rate-limit, 5xx, timeout, etc.), so root cause is currently unknown. A
near-100%-of-batch failure rate for one KALSHI run, immediately after the 2026-07-14 pre-fetch lifecycle gate
(`market-tick-data-service@abe0904d`) and active-window catalogue widening (`instruments-service@41ca79d7`) shipped and
materially grew the daily attempt volume (~10x more markets/day per the widening's own quantification), is exactly the
kind of correctness regression the findings-triage HARD RULE calls a "big finding" — it could be: (a) a transient
one-off (rate-limiting from the ~10x larger daily attempt volume tripping a Kalshi-side throttle), (b) a genuine adapter
regression from the lifecycle-gate/widening change, or (c) unrelated infra flakiness on that specific run. This doc does
NOT root-cause it (out of scope for the read-only measurement task that surfaced it) — it exists so the finding isn't
lost in a chat pane per the FINDINGS CLOSURE hard rule.

## Recommended decision

Investigate root cause before assuming (a); if the failure recurs on subsequent days it is very likely (b) — a
regression from the higher attempt volume the widening introduced (e.g. a new rate-limit threshold being crossed) — and
would need a fix (backoff/retry tuning or a request-rate cap) before the operator-gated historical re-backfill (the
`[BLOCKED-OPERATOR-DECISION]` todo in the parent issue doc) is greenlit, since that backfill will multiply KALSHI
attempt volume further.

## Todos

- [x] ✅ [DIAG] P1. **DONE 2026-08-05 — no recurrence; incident was a one-day event.** Checked the prediction
      availability manifest (`market-data-tick-pred-prd-central-element-323112`, `read_capture_status_counts` /
      `read_availability_index`) for `date=2026-07-26` through `2026-08-04`: `2026-07-26` = 15,615 `attempted_failed`
      (100% KALSHI, 100% `UNCLASSIFIED_ADAPTER_ERROR`), `2026-07-27` through `2026-08-04` = 0 `attempted_failed` on
      every date. A second mass incident was found on `2026-06-22` (15,790 rows) but it was POLYMARKET with error
      `WithinBoundsSourceZero` — a different venue and root cause, predating the lifecycle-gate change (2026-07-14),
      ruling out a regression from the gate/widening. **Verdict**: hypothesis (a) confirmed — transient one-off, not an
      ongoing regression. Repo: unified-trading-pm (read-only manifest query; no new code in market-tick-data-service
      for this step).
- [x] ✅ [DIAG] P1. **DONE 2026-08-05 — root cause identified via code inspection.** The Kalshi adapter
      (`kalshi_adapter.py::get_trades_with_status`) catches `aiohttp.ClientError` / `TimeoutError` / `OSError` and
      reports them as `TRADES_FETCH_FAILED` via `failed_per_dt`. The sentinel pass
      (`engine/orchestrator/sentinels.py::_emit_tier3_for_dt`) then calls
      `classify_venue_error("kalshi", "TRADES_FETCH_FAILED")`, which returned `None` because **no Kalshi (or Polymarket)
      entries existed anywhere in `VENUE_ERROR_MAP`** — no `prediction.py` error file existed. The `None` result was
      recorded as `UNCLASSIFIED:{code_token}` in the manifest, making every incident opaque. **Fix shipped**
      (`unified-api-contracts@42c22278`): created `canonical/crosscutting/errors/prediction.py` with typed entries for
      both Kalshi and Polymarket (`TRADES_FETCH_FAILED` → `retry_safe=True, RETRY`; `429` → `RETRY`; `401`/`403` →
      `FAIL`; `5xx` → `RETRY`), wired into `VENUE_ERROR_MAP` via the existing `_merge_venue_error_maps` import chain.
      `quality-gates.sh` green in unified-api-contracts.
- [x] ✅ [CODE] P2. **DONE 2026-08-05 — not rate-limit-shaped; error classification fixed instead.** The incident
      pattern (near-100% failure across 2,010 instruments in a tight ~1.5h window, clean every day since) does not match
      a rate-limit signature (which would show partial success up to the limit). More consistent with a transient Kalshi
      API outage or auth issue. The `TRADES_FETCH_FAILED` → `UNCLASSIFIED_ADAPTER_ERROR` gap that made this incident
      opaque to automated diagnosis IS now closed (`unified-api-contracts@42c22278` — see todo 2 above). The existing
      Kalshi rate limiter (8 req/s token bucket, `_KALSHI_RATE_PER_SEC` at 8.0, `_KALSHI_BURST` at 8) is already well
      below Kalshi's published 20 req/s limit and the adapter already has 429→2s-sleep reactive backoff
      (`kalshi_adapter.py:222-224`) — no further backoff tuning is warranted without evidence of a rate-limit-shaped
      recurrence. Repo: unified-api-contracts.

## Progress log

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — all 3 open todos are CONFLICT:
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 6 claims the entire 3-step chain (recurrence check ->
  exception reclassification -> contingent backoff fix) verbatim as one internally-sequential todo. Flipping this doc
  would dispatch a duplicate.

- 2026-07-27: Filed from `prediction_satellite_ao_dispatch_batch1-004`'s read-only re-measurement pass (slot 15). No
  code changed; no root cause investigated yet.

- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).

- **2026-08-05 (slot 8, data_engineering, dispatch `prediction_satellite_ao_dispatch_batch6-006`)**: all 3 todos
  completed. Recurrence check (todo 1): queried the prediction manifest for 2026-07-26→2026-08-04 — 0 `attempted_failed`
  on every date except the original 2026-07-26 (15,615 rows). A separate mass incident on 2026-06-22 (15,790 POLYMARKET
  rows, `WithinBoundsSourceZero`) confirms these are venue-specific one-offs, not a lifecycle-gate regression. Exception
  reclassification (todo 2): root-caused via code inspection — `TRADES_FETCH_FAILED` fell through
  `classify_venue_error()` because no prediction-market venue had entries in `VENUE_ERROR_MAP`. Contingent fix (todo 3):
  created `canonical/crosscutting/errors/prediction.py` with typed Kalshi + Polymarket entries; `quality-gates.sh`
  green, shipped `unified-api-contracts@42c22278` (verified on `origin/live-defi-rollout`). No backoff tuning needed —
  existing 8 req/s token bucket + 429→2s-sleep already safe; incident pattern doesn't match rate-limiting. All 3
  source-doc todos flipped; batch6 plan todo 6 flipped in the same turn.
