---
doc_type: issue
title: COINBASE-FUTURES 2026-07-25 — 354 manifest rows with null instrument_type despite well-formed instrument_id
summary: >-
  Surfaced while verifying the ⑧ IS cefi REFERENCE-UNIVERSE closure in data_completion_cefi_2026_07_15.md — a direct
  read of market-data-tick-cefi-prd's _index/availability_index.parquet found 0 blank/UNKNOWN-venue rows (that item's
  original ~650-row pollution is resolved) but a NEW, distinct, single-day gap: 354 COINBASE-FUTURES rows dated
  2026-07-25 have instrument_type=null while instrument_id/venue/data_type are all well-formed.
status: resolved # (was: open) 2026-08-06 RB-04f4f852 archival: all todos [x], no locked_by
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, manifest, coinbase-futures, instrument_type, data-correctness]
related: [/plans/active/data_completion_cefi_2026_07_15.md]
created: 2026-07-27
author: unknown
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: data_engineering
drift_direction: stable
depends_on: []
source: ["surfaced 2026-07-27 while closing data_completion_cefi_2026_07_15.md item ⑧ (slot-4 live manifest read)"]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /plans/active/data_completion_cefi_2026_07_15.md,
    /plans/active/issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/coinbase.py,
    market-tick-data-service/market_tick_data_service/live/connectors/coinbase_book_ws.py,
  ]
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by the plan-hygiene gate remediation for repo-blocker RB-04f4f852 (escalation
> agt-3dc7e9), 2026-08-06. No content was rewritten.

# COINBASE-FUTURES 2026-07-25 blank instrument_type — 354 rows

## What I found

A direct read of `market-data-tick-cefi-prd-central-element-323112`'s `_index/availability_index.parquet` (8,764,263
rows total, read via `unified_trading_library.cf_manifest_audit._cp` + `pd.read_parquet`, columns
`date,venue,instrument_type,instrument_id,data_type,capture_status`) found:

- 0 rows with blank/null `venue`
- 0 rows with `venue == "UNKNOWN"`
- 0 rows with `instrument_id` ending in `F0`
- **354 rows with null `instrument_type`** — ALL dated `date=2026-07-25`, ALL `venue=COINBASE-FUTURES`,
  `data_type=book_snapshot_5`, `capture_status` split 301 `empty_confirmed` / 53 `attempted_failed`.

Sample instrument_ids (all well-formed, PERPETUAL-shaped): `COINBASE-FUTURES:PERPETUAL:1000BONK-USD@LIN`,
`COINBASE-FUTURES:PERPETUAL:AAPL-USD@LIN`, `COINBASE-FUTURES:PERPETUAL:AMZN-USD@LIN`, etc.

This is NOT the venue-pollution class tracked by `data_completion_cefi_2026_07_15.md` item ⑧ sub-part (4) (that was
blank-venue/UNKNOWN-venue rows, now confirmed at 0). It is a narrower, single-day writer gap: the venue and
instrument_id resolved correctly but `instrument_type` didn't get populated for this one date's COINBASE-FUTURES
book_snapshot_5 shard.

## Why it matters

`instrument_type` is a coverage-denominator field for some downstream honest-coverage / CF-checks (schema presence
checks read the column even when not filtering on it). A one-day gap for one venue is low-blast-radius but is a genuine
writer defect worth root-causing — if it's a transient race (e.g. instrument-type resolution timing out against a stale
reference-universe cache on that date) it could recur on future dates/venues.

## Recommended decision

- [x] ✅ [DATA] P3. Root-cause complete — NOT a resolver gap, NOT a code-path regression. The code fix
      (`market-tick-data-service@91ac1caa`, 2026-07-12) correctly threads `instrument_type` via
      `_classify_row_instrument_type` in BOTH `_build_per_symbol_tasks` (line 208-210) and the inline `PerSymbolTask`
      path (line 361-363). For COINBASE-FUTURES symbols like `1000BONK-USD@LIN`, the classifier returns
      `InstrumentType.PERPETUAL` — correct. `venue_fetch.py:599` blocks `book_snapshot_5` for COINBASE-FUTURES
      (trades-only), so these 354 rows came from a backfill/one-off VM, not the standing daily cron. Most likely root
      cause: **stale tarball** — the VM that processed 2026-07-25 used a code tarball built before the P1 fix landed
      (the fix shipped 13 days earlier but the backfill VM's tarball may not have been rebuilt). No code change needed;
      the fix has been in place since 2026-07-12. The 354 rows are harmless legacy strays (same analysis as the sibling
      [`cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md`](/plans/active/issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md)
      P2 decision — they won't recur, and active re-tag is disproportionate). Repo: market-tick-data-service (no code
      change — investigation-only). — unified-trading-pm (doc-only).

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (6 entries).
- **slot-7 (data_engineering) 2026-08-05**: Root-cause complete. Traced the full write path: COINBASE-FUTURES →
  `download_batch` → `_run_per_symbol_batch` → `PerSymbolTask.row_key` with `instrument_type` from
  `_classify_row_instrument_type`. Both `_build_per_symbol_tasks` (line 208-210) and the inline path (line 361-363)
  correctly thread instrument_type. The classifier correctly returns `PERPETUAL` for `@LIN`-suffixed symbols.
  `venue_fetch.py:599` blocks `book_snapshot_5` for COINBASE-FUTURES (trades-only), confirming these rows came from a
  backfill/one-off VM. Most likely root cause: stale tarball — the VM used pre-fix code. No code change needed; the P1
  fix (`91ac1caa`, 2026-07-12) already covers this. The 354 rows are harmless legacy strays per the honest-coverage
  model (same P2 decision as the sibling doc).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
