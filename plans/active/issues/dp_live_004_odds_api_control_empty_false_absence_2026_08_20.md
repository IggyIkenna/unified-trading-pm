---
doc_type: issue
title: DP-LIVE-004 — Odds API fan-out control buffers produced false empty-confirmed live shards
summary: >-
  The live MTDS Odds API poller used coarse `ODDS_API:SPORT:*` subscription ids to drive fan-out, but the websocket
  runner treated those control ids as data shards and recorded empty-confirmed rows when a poll produced no fixture
  ticks. HTTP/auth/rate-limit failures were therefore indistinguishable from an honest source empty, leaving the live
  sports odds shard attempting and unproductive beyond its staleness budget.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-live-004, sports, odds-api, honest-absence, fanout]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-08-20
last_updated: "2026-08-20"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P1
severity: P1
source: >-
  Escalation agt-a1445b, DP-LIVE-004: live shard vm=mtds-live-sports-odds-api-odds-20260816-145019,
  venue=ODDS_API, data_type=odds, remained attempting and unproductive with last attempt approximately 0.7h ago;
  no issue document had been filed by the originating alert.
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    market-tick-data-service/market_tick_data_service/live/connectors/odds_api_ws.py,
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
  ]
---

# DP-LIVE-004 — Odds API fan-out control empty false absence

## What I found

The live Odds API connector subscribes to coarse `ODDS_API:SPORT:<sport_key>` ids and emits richer
`ODDS_API:BOOKMAKER:<bookmaker>:LEAGUE:<league>:FIXTURE:<fixture>` ids. The runner still retained the coarse ids as
normal buffers. A healthy poll with no fixtures consequently reached the empty-window writer for a buffer that has no
data shard of its own. A failed poll also yielded no ticks, so without an explicit connector failure reason the same
path could record `SOURCE_RETURNED_ZERO` / `empty_confirmed` for an upstream error.

This violates the honest-absence contract: only a proven successful 2xx response with zero rows may become an honest
empty; authentication, rate-limit, timeout, and other fetch failures must be `attempted_failed`.

## Root-cause fix

`market-tick-data-service@59b85aa0` adds a connector fan-out capability marker and tracks control ids in the runner. A
healthy empty control buffer is skipped entirely, while any non-healthy upstream state is sent through the existing
failure recorder. The connector exposes `upstream_failure_reason()` and classifies HTTP and fetch failures so the
runner records `record_failed` instead of a false empty. Regression tests cover both healthy fan-out empties and an
HTTP/auth failure.

## Verification

- [x] [TEST] P1. Unit regression coverage added in `tests/unit/test_websocket_runner.py`.
- [ ] [VERIFY] P1. Run the target repository quality gates and verify the shipped commit is present on `origin/live-defi-rollout`.
- [ ] [VERIFY] P1. Re-run the DP-LIVE-004 candidate check against the live shard and confirm no new false empty-confirmed rows.

## Progress Log

**2026-08-20 — filed by escalation `agt-a1445b`.** No originating issue slug was supplied; this document records the
candidate payload before final verification and shipping.
