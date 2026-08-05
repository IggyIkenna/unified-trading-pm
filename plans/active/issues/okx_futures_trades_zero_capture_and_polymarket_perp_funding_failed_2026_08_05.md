---
doc_type: issue
title: >-
  OKX-FUTURES trades chronic zero-capture + POLYMARKET-PERP perp_funding permanent attempted_failed — two pre-existing
  pipeline issues surfaced incidentally by cefi tarball-staleness audit
summary: >-
  Two unrelated chronic pipeline issues discovered during the cefi tarball-staleness manifest check (2026-08-01). Both
  predate the 2026-07-30–2026-08-01 tarball outage and are NOT caused by it. (1) OKX-FUTURES trades (live_okx pipeline):
  intermittent zero-capture going back to at least 2026-07-20. (2) POLYMARKET-PERP perp_funding (batch_polymarket_perp
  pipeline): permanently attempted_failed since at least 2026-07-28. Each needs its own root-cause investigation and
  fix.
status: open
nature: issue
asset_group: [cefi]
stage: [live]
repos: [market-tick-data-service]
scope: [engineer]
tags: [data-correctness, cefi, live-capture, batch-pipeline, manifest, okx-futures, polymarket-perp]
related:
  [
    /plans/active/issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: "2026-08-05"
author: slot-16
parent_epic: infrastructure_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [/plans/active/issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md]
context_scope:
  [
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    market-tick-data-service/market_tick_data_service/live/connectors/,
  ]
depends_on: []
resolved_by:
locked_by:
locked_since:
---

# OKX-FUTURES trades zero-capture + POLYMARKET-PERP perp_funding failed — two chronic pipeline issues (2026-08-05)

## What I found

These two findings were surfaced incidentally by the `2026-07-30`–`2026-08-01` cefi tarball-staleness manifest check
(todo #2 of the parent issue doc). Both predate the tarball outage window and are NOT caused by it — they are
independent, pre-existing pipeline issues that need their own investigation and fix.

**Source data**: single `market-data-tick-cefi-prd-{project}/_index/availability_index.parquet` object read, filtered
(row-group pushdown, `columns=`+`filters=`) to relevant `(venue, data_type, pipeline_mode)` combinations. No
whole-corpus walk.

### Finding 1: OKX-FUTURES trades — chronic intermittent zero-capture (`live_okx` pipeline)

- **Observed**: 100% `empty_confirmed`/`expected_unattempted` (zero `captured` rows) on every day `2026-07-30` through
  `2026-08-01`.
- **Chronic**: zero-or-near-zero on most days back to at least `2026-07-20` — intermittent, not a clean unbroken
  zero-stretch, but consistently far below healthy capture rates.
- **Pipeline**: `live_okx` — the live WebSocket path on the `mtds-live-cefi-consolidated-*` VM, same infrastructure as
  the recently-fixed `OKX-FUTURES book_snapshot_5`/`derivative_ticker` shards. Those sibling shards recovered (at least
  partially) after the tarball fixes landed; `trades` did not.
- **Not caused by**: the tarball-staleness incident (predates it) or the ASTER/DERIBIT fixes shipped 2026-08-02 (those
  targeted different venues/data_types). This is a separate, pre-existing issue specific to the OKX-FUTURES trades
  connector or its WS subscription.

### Finding 2: POLYMARKET-PERP perp_funding — permanent `attempted_failed` (`batch_polymarket_perp` pipeline)

- **Observed**: `attempted_failed` every day `2026-07-28` through `2026-07-31` (the window checked). Zero `captured`
  rows ever in this window.
- **Pipeline**: `batch_polymarket_perp` — a BATCH path, NOT the live-capture VM/tarball mechanism. Completely different
  infrastructure from the live-WebSocket shards that were the focus of the parent tarball-staleness incident.
- **Chronic**: predates the tarball-staleness window; the failure pattern was already established before `2026-07-30`.
- **Not caused by**: the tarball-staleness incident or any of the live-capture fixes. This is a batch-pipeline failure
  requiring its own root-cause investigation (likely a sourcing/API-key/endpoint issue specific to Polymarket's
  perp_funding data feed).

## Why it matters

- Per the data-pipeline-correctness HARD RULE, these cannot be silently ignored just because they were "found
  incidentally." Both represent real data gaps — zero-capture for an entire venue×data_type combination over multi-day
  windows.
- `OKX-FUTURES trades` is a core CeFi data type on a major exchange; the sibling OKX-FUTURES shards
  (`book_snapshot_5`/`derivative_ticker`) are now healthy after the tarball-staleness fixes, leaving `trades` as the
  sole remaining gap on this venue's live pipeline.
- `POLYMARKET-PERP perp_funding` is a batch path — `attempted_failed` (not `empty_confirmed`) means the pipeline itself
  is erroring, not just producing zero results. This is a hard failure, not a data-availability question.

## Recommended decision

Each finding needs its own root-cause investigation. They are unrelated (different venues, different pipelines,
different failure modes) — treat them as independent work items, not a single fix.

## Todos

- [x] ✅ [DATA] P3. Root-cause + fix `OKX-FUTURES trades` chronic zero-capture on the `live_okx` pipeline —
      market-tick-data-service@bf69e612. Root cause: `OKXFuturesDatedWSFeedConnector` inherited
      `_send_sub_batch`/`_send_unsub_batch` from `OKXFuturesWSFeedConnector` (okx_ws.py), which called
      `_instrument_to_okx_inst_id` — a function that only handles `OKX-SWAP:PERPETUAL:` IDs. For
      `OKX-FUTURES:FUTURE:BTC-USD@INV-20260710`, it returned bare `BTC-USD@INV-20260710` (marker + canonical date
      intact) — a malformed instId OKX silently ignores. Fix: overrode both methods to use
      `_instrument_to_okx_futures_inst_id` instead, correctly mapping `@LIN`→`_UM`, `@INV`→bare, `YYYYMMDD`→`YYMMDD`.
      Sibling book/ticker connectors never had this bug (they inherit from `_OKXFuturesBaseConnector` which already uses
      the correct mapper). (repo: market-tick-data-service)
- [x] ✅ [DATA] P3. Root-cause + fix `POLYMARKET-PERP perp_funding` permanent `attempted_failed` on the
      `batch_polymarket_perp` pipeline — market-tick-data-service@b2497b73, unified-api-contracts@845f7ce5. Root cause:
      `CEFI_PERP_VENUE_API_ENDPOINTS["POLYMARKET_PERP"]` was set to `https://perps-api.polymarket.com` which was DNS
      NXDOMAIN (2026-06-21). The Polymarket perps API is now live at `https://api.perpetuals.polymarket.com` (verified
      HTTP 200, 2026-08-05). Fix: updated the UAC registry endpoint URL + replaced the hardcoded
      `raise ClientConnectionError` in `_collect_polymarket_perp` with a working collector that fetches instruments via
      `GET /v1/info/instruments` and funding rates via `GET /v1/info/funding?instrument_id=<id>&limit=100`.

## Codex SSOTs

`/codex/02-data/data-pipeline-correctness-hard-rule.md`, `/codex/02-data/availability-manifest-and-data-status.md`.
