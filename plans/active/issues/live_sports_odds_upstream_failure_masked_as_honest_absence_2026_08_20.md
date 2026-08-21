---
doc_type: issue
title: >-
  Live sports odds shard (mtds-live-sports-odds-api-odds-20260816-145019) never captures — every
  poll failure (HTTP 401 from exhausted odds-api-key) recorded as empty_confirmed/SOURCE_RETURNED_ZERO
  because OddsApiWSFeedConnector lacks upstream_failure_reason (DP-LIVE-004)
summary: >-
  DP-LIVE-004 fired for vm=mtds-live-sports-odds-api-odds-20260816-145019 venue=MATCHBOOK
  data_type=odds: shard still attempting (last attempt 0.0h ago) but never captured (3d budget).
  Root cause has two layers. (1) CODE DEFECT — OddsApiWSFeedConnector does not implement
  upstream_failure_reason(), so every failed poll (HTTP 401/429/5xx/timeout) falls through the
  runner's _record_empty_window to record_zero_rows(SOURCE_RETURNED_ZERO) — a fabricated
  honest-absence (39,515 empty_confirmed rows in the per-VM shard) instead of record_failed.
  (2) OPERATOR-GATED — the shared odds-api-key is functionally exhausted (x-requests-remaining=2,
  used=14,999,998 of 15M); 80,394 HTTP 401s in the VM run.log since 2026-08-18 07:07. Fix ships
  in market-tick-data-service (upstream_failure_reason); credential top-up is operator-gated.
status: open
nature: process
asset_group: [sports]
stage: [live, meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-alerts, live-capture-stall, honest-absence, odds-api, misclassified-empty, dp-live-004]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md,
  ]
created: 2026-08-20
author: data-pipeline-fleet-monitor (escalation agt-f712d7, slot 31)
parent_epic: observability_master
priority: P1
assigned_vm: vm-cross-cutting
source: [DP-LIVE-004, DP_CRON_DID_NOT_FIRE]
locked_by:
resolved_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    market-tick-data-service/market_tick_data_service/live/connectors/odds_api_ws.py,
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
  ]
---

# Live sports odds shard: upstream failures masked as honest absence (DP-LIVE-004)

## What I found

DP-LIVE-004 fired for `vm=mtds-live-sports-odds-api-odds-20260816-145019` `venue=MATCHBOOK`
`data_type=odds`: the shard is **still attempting** (fresh `attempted_at`, 0.0h ago) but has
**never captured** within its 3-day staleness budget. Verified live (2026-08-20, slot 31):

### The per-VM manifest shard lies

`gs://market-data-tick-sports-prd-central-element-323112/_index/per_vm/mtds-live-sports-odds-api-odds-20260816-145019.parquet`:

- 39,515 rows, **ALL `capture_status=empty_confirmed`, `error_reason=SOURCE_RETURNED_ZERO`**.
- Zero `captured`, zero `attempted_failed`, across every venue (MATCHBOOK 660 rows, all empty).
- Fresh `attempted_at` every ~60s (the polling loop keeps running).

### The run.log shows the real cause

- **80,394 `OddsApi: HTTP 401` warning lines** — first at 2026-08-18 07:07, then continuous.
  Only 1× HTTP 429 and 0× HTTP 200 in the tail.
- Boot-time ticks DID flow at 08-16 14:54 (real bookmaker fixtures parsed) but the first window
  flush (08-16 14:55) hit **3268 × `404 Resource not found (resource=persist-sports-odds)`** — the
  Pub/Sub topic did not exist at boot (it exists now, verified live; fleet captures resumed
  there — 7,851 captured live-odds rows on 08-16, last capture 08-18 07:09:50 == first 401 07:07).
- Live key test (2026-08-20): `GET /v4/sports` → HTTP 200 but **`x-requests-remaining=2`,
  `x-requests-used=14999998`** (of 15M). The shared `odds-api-key` is functionally exhausted.

### Root cause (two layers)

**Layer 1 — CODE DEFECT (fixable):** `OddsApiWSFeedConnector`
(`market_tick_data_service/live/connectors/odds_api_ws.py`) does **not** implement
`upstream_failure_reason()`. The runner's `_record_empty_window`
(`market_tick_data_service/live/websocket_runner.py`) does:

```python
failure_reason = getattr(self._connector, "upstream_failure_reason", lambda: None)()
if self._in_connectivity_gap() or failure_reason is not None:
    ... record_failed(...) ; return
... record_zero_rows(..., SOURCE_RETURNED_ZERO, fetch_evidence=make_live_window_evidence(...))
```

`getattr` on a connector with no such attribute returns the `None` default, so every failed poll
(HTTP 401/429/5xx/timeout) is recorded as **`record_zero_rows(SOURCE_RETURNED_ZERO)`** — a proven
honest-absence stamped with a **fabricated `FetchEvidence(http_status=200, error_signal="")`**
(`make_live_window_evidence` hardcodes 200) even though the poll actually 401'd. This is exactly the
DP-FETCH-002/004 misclassified-empty class: "adapter hit a disqualifying signal (401/403/429/5xx)
but did not `record_failed`". `DatabentoTradfiWSFeedConnector` implements the hook; the Odds API
connector was missing it.

**Layer 2 — OPERATOR-GATED credential:** the shared `odds-api-key` is exhausted (2 remaining).
A live producer cannot self-stop (it must keep running), so every poll 401s. Top-up / rotate the key
is an operator decision (same class as `odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02.md`,
resolved 2026-08-03). Even with credits restored, the Layer-1 defect would still record a dead feed as
`empty_confirmed` instead of `attempted_failed`.

## Why it matters

The manifest currently records **false honest-absence** for a feed that is actually failing. Downstream
honest-coverage / empty-re-probe logic reads `empty_confirmed` as "source proven 200+empty" and will
never re-attempt or surface the failure. DP-LIVE-004 (a productivity gap) is the only signal — and it
fires only because no row was ever captured, not because the manifest is honest. The data-pipeline
correctness hard rule ("only a genuine 200+empty stays honest-absence; an error path routes to
`record_failed`") is violated by construction.

## Recommended decision

1. **Ship the code fix** (`market-tick-data-service`): implement `upstream_failure_reason()` on
   `OddsApiWSFeedConnector` — set a failure reason on HTTP non-200 / exception / missing key, clear
   on HTTP 200 — so failed-poll windows route to `record_failed` instead of fake `record_zero_rows`.
   Mirrors the Databento connector + is covered by a new `TestOddsApiUpstreamFailureReason` class.
2. **Operator: top-up / rotate the shared `odds-api-key`** (BLOCKED-CREDENTIALS) so the live shard
   can capture again. The VM is healthy and the sink/topic path is proven working (fleet captured
   live odds through 08-18 07:09:50).
3. After both, the shard should show `attempted_failed` (honest) while the key is down and
   `captured` once the key returns — DP-LIVE-004 clears on the first captured row.

## Todos

- [x] ✅ [CODE] P1. Ship `OddsApiWSFeedConnector.upstream_failure_reason()` in
      `market-tick-data-service` — `market-tick-data-service@40b9b624` (landed on
      `live-defi-rollout` 2026-08-20; QG green; 85 unit tests pass incl. new
      `TestOddsApiUpstreamFailureReason`). Verified ancestor of `origin/live-defi-rollout`.
- [ ] [OPERATOR] P1. Top-up / rotate the shared `odds-api-key` (15M exhausted, 2 remaining) so
      `mtds-live-sports-odds-api-odds-*` can capture. BLOCKED-CREDENTIALS until operator action.
- [ ] [BACKEND] P2. Verify after the key is restored: the shard shows `captured` rows again and
      DP-LIVE-004 stops firing for this VM.

## Progress Log

- 2026-08-20 — Escalation `agt-f712d7` (slot 31, data_pipeline_failure). Filed from the DP-LIVE-004
  finding payload (no pre-filed doc). Diagnosed both layers live (per-VM shard read, run.log scan,
  live key test). Shipped the connector fix in `market-tick-data-service@40b9b624`
  (`OddsApiWSFeedConnector.upstream_failure_reason()`, QG green, landed on `live-defi-rollout`).
  Operator-gated `odds-api-key` top-up remains open (BLOCKED-CREDENTIALS).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **ag-closeout-audit 2026-08-21 (sports tranche, Phase 2 sweep)**: found this doc and
  `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md` document the SAME incident
  (same VM `mtds-live-sports-odds-api-odds-20260816-145019`, same root-cause chain: shared `odds-api-key`
  exhaustion + the connector's missing `upstream_failure_reason()`) filed hours apart with no cross-reference
  either direction — added the sibling doc to `related:` above. This doc's own `upstream_failure_reason()` fix
  (`market-tick-data-service@40b9b624`) is the SAME commit the sibling doc cites as already-shipped — no
  duplicate/competing code work exists between the two; the sibling doc additionally tracks 2 more bounded
  follow-ups (a batch-path quota-stop fix, extracted to `sports_satellite_ao_dispatch_batch17_2026_08_21.md`) not
  named here. The `[OPERATOR]` top-up ask in both docs is the same real-world action — resolving one resolves
  both; not merging the docs (each carries its own independent evidence trail), just cross-referencing per the
  ag-closeout-audit parked-findings mechanical-hygiene flag.
