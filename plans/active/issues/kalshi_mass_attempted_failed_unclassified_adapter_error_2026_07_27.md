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
status: open
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
  ]
created: 2026-07-27
parent_epic: predictions_master
priority: P1
source: ["read-only manifest measurement, prediction_satellite_ao_dispatch_batch1-004, slot 15, 2026-07-27"]
assigned_vm: NA
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md,
    /plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
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

- [ ] [DIAG] P1. Check whether `date=2026-07-27`'s (today's) KALSHI backfill run also shows mass `attempted_failed` — if
      yes, this is an ongoing regression, not a one-off; if the run is clean, it strengthens the transient-incident
      read. Repo: market-tick-data-service (read-only manifest read, no new GCS walk — the same
      `read_capture_status_counts` call for a 1-day window).
- [ ] [DIAG] P1. Pull the actual HTTP/adapter exception this run logged for a sample of the 2,010 failed instrument_ids
      (Cloud Logging or the run's own log artifact) to reclassify `UNCLASSIFIED_ADAPTER_ERROR` into a typed
      `classify_venue_error()` bucket (rate-limit vs 5xx vs timeout vs auth). Repo: market-tick-data-service.
- [ ] [CODE] P2. Contingent on todo 2's verdict: if rate-limit-shaped, add/tighten a KALSHI-side backoff or concurrency
      cap sized for the widened daily attempt volume (mirrors the Tardis single-VM-queue precedent for a different
      venue). Repo: market-tick-data-service.

## Progress log

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — all 3 open todos are CONFLICT:
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 6 claims the entire 3-step chain (recurrence check ->
  exception reclassification -> contingent backoff fix) verbatim as one internally-sequential todo. Flipping this doc
  would dispatch a duplicate.

- 2026-07-27: Filed from `prediction_satellite_ao_dispatch_batch1-004`'s read-only re-measurement pass (slot 15). No
  code changed; no root cause investigated yet.
