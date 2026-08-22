---
doc_type: issue
title: "DP-LIVE-004: BYBIT-FUTURES book_snapshot_5 remains unproductive on the live VM"
created: 2026-08-21
author: data-pipeline-failure
parent_epic: observability_master
assigned_vm: vm-cross-cutting
source:
  - DP-LIVE-004
locked_by: live-defi-rollout
summary: "The live CEFI VM still reports attempts but no BYBIT-FUTURES book_snapshot_5 captures; the running VM predates the shipped linear-instrument filter and requires a fresh runtime cycle for verification."
status: superseded
superseded_by: [dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20]
nature: process
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-alerts, dp-live-004, cefi, bybit-futures, book-snapshot-5]
related:
  - /plans/active/cross_ag_live_capture_parity_2026_08_14.md
priority: P1
resolved_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - /codex/02-data/honest-absence-downstream-handling.md
  - market-tick-data-service/market_tick_data_service/live/connectors/bybit_ws.py
  - market-tick-data-service/market_tick_data_service/live/connectors/bybit_futures_book_ticker_ws.py
  - market-tick-data-service/tests/unit/test_bybit_futures_book_ticker_ws_coverage.py
---

# DP-LIVE-004: BYBIT-FUTURES book_snapshot_5 remains unproductive on the live VM

> **SUPERSEDED 2026-08-21 (ag-closeout-audit cefi tranche, Phase 3 sweep)**: consolidated into
> `/plans/active/issues/dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md` — same VM
> (`mtds-live-cefi-consolidated-20260817-025031`), same root cause (`5f88715e4b`), same recommended action. This
> doc's own evidence/detail is kept for provenance; the tracked `- [ ]` todos live on the canonical doc now.

## What I found

The escalation payload reports live VM `mtds-live-cefi-consolidated-20260817-025031`, venue `BYBIT-FUTURES`, data type `book_snapshot_5`, still attempting but with no captured row inside the three-day productivity budget. The per-VM manifest evidence recorded in the live-capture parity plan shows 10,258 BYBIT-FUTURES rows all `empty_confirmed`/`SOURCE_RETURNED_ZERO`, with 737 `PERPETUAL`, 44 `FUTURE`, and 501 `SPOT_PAIR` instrument IDs attempted. That exact 1,282-instrument count matches the unfiltered BYBIT instruments catalog.

The root cause is the stale runtime, not an honest absence: the Bybit linear endpoint was being given the full venue catalog, including spot instruments, and the subscription could exceed the endpoint's topic-size limit. The required `_is_linear_derivative()` filter is present in the MTDS checkout and is applied to the book connector before topic construction; the shipped code also applies the same filter to trades, ticker, and depth connectors. The existing parity record identifies this fix as `market-tick-data-service@5f88715e4b`, but captured-row verification after a fresh VM cycle was explicitly still open.

## Why it matters

The live process is active enough to produce attempts, but the shard's all-empty manifest state would hide a broken live feed from downstream consumers unless the productivity alert remains active. No placeholder parquet or fabricated capture must be written. A runtime cycle using the shipped tarball is required before this alert can be considered resolved.

## Recommended decision

Use the normal registered CEFI live launcher to cycle the stale VM onto the shipped MTDS artifact, then verify the new per-VM manifest shard contains at least one real `captured` `BYBIT-FUTURES`/`book_snapshot_5` row and that the subscription universe contains only linear derivative instruments. If the fresh runtime still produces zero captures, inspect its subscribe acknowledgements and file a follow-up code issue; do not mute DP-LIVE-004 or reclassify the rows as `empty_confirmed` without HTTP/WS proof.

## Todos

- [ ] [OPERATOR] P1. Cycle the registered `mtds-live-cefi-consolidated-*` VM using the shipped `market-tick-data-service@5f88715e4b` artifact and verify a post-relaunch captured `BYBIT-FUTURES`/`book_snapshot_5` row in the new per-VM manifest shard; record the VM name and measured manifest evidence.
- [ ] [DATA] P1. If the fresh runtime remains unproductive, inspect Bybit subscribe acknowledgements/rejections and diagnose the remaining root cause before changing any manifest status.

## Progress Log

- 2026-08-21 — Filed by escalation `agt-9bcd90` because no issue slug was supplied. Confirmed the alert is DP-LIVE-004 productivity-gap semantics, not a proven honest absence. Existing parity evidence ties the exact 1,282-universe attempt pattern to the unshipped linear-instrument filter; the filter is now present in MTDS at `5f88715e4b`, while post-relaunch captured-row evidence remains absent. No data or placeholder rows were written.
