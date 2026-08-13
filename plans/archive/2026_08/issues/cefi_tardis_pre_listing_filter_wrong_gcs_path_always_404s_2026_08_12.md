---
doc_type: issue
title: >-
  CeFi Tardis pre-listing symbol filter always 404s (wrong GCS blob path — missing pipeline_mode/asset_group hive
  segments) and fails open, silently attempting every instrument on every date regardless of real listing date
summary: >-
  `market_tick_data_service/market_interface/adapters/tradfi/tardis_symbol_resolution.py::_resolve_symbols` reads
  `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet` to filter pre-listing symbols before
  requesting them from Tardis (avoids a known HTTP 400). The real path instruments-service writes (confirmed in
  `instruments_service/engine/orchestrator/writers.py:176-182`) is
  `instrument_availability/by_date/day={date}/pipeline_mode={pipeline_mode}/asset_group={asset_group}/venue={venue}/...`
  — two extra hive segments (`pipeline_mode`, `asset_group`) the reader never includes. Every read at the reader's path
  therefore 404s, and the function's own except-block fails open on NotFound ("proceeding with all instrument_ids") — so
  the pre-listing filter has likely never actually filtered anything for CeFi Tardis venues since it was written; every
  `--instrument-ids`-scoped or catalogue-mvp-driven fetch attempts every symbol on every date in range, regardless of
  whether that symbol existed yet, relying entirely on Tardis's own HTTP 400 + this workspace's downstream
  `classify_venue_error()` to turn that into `empty_confirmed` rather than `attempted_failed` (NOT verified in this pass
  — see open todo below).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [cefi, tardis, honest-coverage, data-pipeline, gcs-path, pre-listing]
related:
  - /codex/02-data/availability-manifest-and-data-status.md
  - /codex/02-data/honest-absence-downstream-handling.md
  - /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md
  - /plans/active/issues/cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md
created: "2026-08-12"
author: main (Claude Code, interactive session)
parent_epic: cefi_master
resolved_by:
locked_by:
locked_since:
source: >-
  Found while researching the correct START_DATE strategy for launching the CeFi Tardis equity-perp backfill
  (cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md Phase 2 todo 4) — planned to rely on this filter to
  safely use one shared conservative START_DATE across a wide per-symbol listing-date spread (esp. the 139-base Binance
  equity-perp universe, listing dates spanning 2025-12-11..2026-07-22), then discovered via direct code read that the
  filter's GCS path never matches what instruments-service actually writes.
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
drift_direction: fix
depends_on: []
---

# CeFi Tardis pre-listing filter reads the wrong GCS path (always 404s, fails open)

## What I found

`_resolve_symbols` (`market_tick_data_service/market_interface/adapters/tradfi/tardis_symbol_resolution.py:800-802`):

```python
_blob = f"instrument_availability/by_date/day={date_str}/venue={_canonical}/instruments.parquet"
```

The actual writer (`instruments_service/engine/orchestrator/writers.py:176-182`, `_instrument_availability_sink_for` or
equivalent) builds:

```python
f"instrument_availability/by_date/day={date}/pipeline_mode={pipeline_mode}/asset_group={asset_group}/venue={venue}"
```

Confirmed live: a `list_blobs` probe (via UTL `get_storage_client`, not a raw `gcloud`/`gsutil` call, per this
workspace's storage-code rule) against
`gs://instruments-store-cefi-prd-central-element-323112/instrument_availability/by_date/` with a `day=2026-08` prefix
returned **zero blobs and zero sub-prefixes** at the exact 3-segment shape the reader expects — the object the reader
wants literally cannot exist at that path. The reader's own except-block (`tardis_symbol_resolution.py:827-845`)
explicitly duck-types GCS `NotFound`/404 and **fails open**: "proceeding with all instrument_ids" — a deliberate,
documented fallback, but one that (given the path never resolves) has likely been live 100% of the time for every CeFi
Tardis fetch that reaches this function, not just an occasional-missing-snapshot edge case the comment seems to assume.

## Why it matters

- The filter's entire purpose is to avoid requesting Tardis for a symbol before its real listing date (the docstring:
  "Pre-listing symbols... cause HTTP 400 from Tardis — filter proactively"). If it never actually filters, every
  pre-listing (symbol, date) pair still gets requested from Tardis and presumably 400s at the vendor instead of being
  skipped locally — real wasted API calls against the single shared Tardis IP (this workspace's Tardis N=1 concurrency
  model already treats vendor-side call volume as a scarce, contended resource), and one API round-trip per pre-listing
  symbol-day.
- **Unconfirmed downstream classification**: it's possible the resulting Tardis 400 is still correctly turned into
  `empty_confirmed(EXPECTED_INSTRUMENT_NOT_LISTED)` further down the pipeline via `classify_venue_error()` (the general
  shard-level-failure-isolation mechanism), in which case the manifest itself may not actually be polluted with false
  `attempted_failed` rows — only the wasted vendor call remains as the concrete cost. This was NOT verified in this pass
  (would need either a live capture sample over a known pre-listing date or a read of `classify_venue_error()`'s
  Tardis-400-for-missing-symbol branch) — flagging as the key open question, not asserting the worse outcome.
- Affects every CeFi Tardis venue's pre-listing handling generally (not equity-perp-specific) — anywhere
  `_resolve_symbols` is reached with a `date` before a real symbol's listing, which includes ordinary MVP crypto
  perps/spot with delayed listings, not just the equity-perp universe that surfaced it.

## Action items

- [x] ✅ [SCRIPT] P2. **Fix the reader's blob path** to match the writer's actual hive shape
      (`day=.../pipeline_mode=.../     asset_group=.../venue=...`) — needs `pipeline_mode` and `asset_group` values
      threaded into `_resolve_symbols` (asset_group is always "cefi" for this call site; pipeline_mode needs sourcing
      from the caller's own context, likely `batch_tardis` for this code path — confirm against a live writer call
      before hardcoding). Add a regression test asserting the constructed blob path matches `writers.py`'s real shape
      (string-level parity, not just "the read doesn't throw"). Repo: market-tick-data-service. —
      market-tick-data-service@b4ca5d7bdf
- [x] ✅ [DATA] P2. **Verify the downstream classification question above** — confirm whether a live Tardis 400 for an
      actual pre-listing symbol currently lands as `empty_confirmed` or `attempted_failed` in the manifest (read
      `classify_venue_error()`'s Tardis-error-code branch, or check a real manifest sample for a known pre-listing
      symbol/date). If it lands as `attempted_failed`, this becomes a manifest-correctness finding, not just an
      efficiency one, and should be escalated per the workspace's data-pipeline-correctness hard rule. Repo:
      market-tick-data-service. — **VERIFIED (code-read, 2026-08-13): lands as `empty_confirmed`, NOT
      `attempted_failed`** — a pre-listing symbol's Tardis 400 carries JSON `code=140` ("dataset not available for
      <date>" — symbol archived but date before `availableSince`) or `code=300` (symbol not in archive at all), both in
      `TardisHTTPError.STRUCTURAL_ABSENCE_400_CODES={140,300}` (`market_interface/clients/tardis_base_client.py:152`),
      so `is_structural_absence` is True and `tardis_csv_transport.py` (streaming `:448` + non-streaming `:541`) returns
      the honest-absence skip sentinel (same as 404) → `empty_confirmed`, never `record_failed`/`attempted_failed`. The
      reactive classification backstop is live and correct (UAC `classify_venue_error` registers `140`/`300` as
      `ErrorAction.SKIP`, per the 2026-07-17 structural-absence SSOT), and the vendor-catalog gate is a second proactive
      layer. Conclusion: efficiency-only (wasted vendor call while the filter was broken); manifest NOT polluted — no
      data-pipeline-correctness escalation required. No code change (verification todo).

## Progress Log

- 2026-08-12: found while pre-flighting the CeFi equity-perp Tardis backfill launch
  (`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Phase 2 todo 4) — not fixed in this pass (out of that
  task's scope; that task instead worked around it by supplying an accurate, cohorted START_DATE per venue/symbol-group
  rather than relying on this filter). No code changed by this doc.
- 2026-08-13: fixed todo 1 — added `instruments_availability_blob_path()` (threads
  `PipelineMode.BATCH_INSTRUMENTS_SERVICE`
  - `asset_group="cefi"` into the hive-shaped blob path) and switched `_resolve_symbols_from_by_date_snapshot`'s
    pre-listing read to it; added string-level parity regression tests confirming the constructed path matches the
    writer's real hive shape. QG green on `market-tick-data-service`, shipped via quickmerge, verified on
    origin/live-defi-rollout — market-tick-data-service@b4ca5d7bdf. Todo 2 (downstream `classify_venue_error()`
    manifest-correctness question) is still open.
- 2026-08-13: closed todo 2 (downstream classification verification) — confirmed via code-read (the more definitive
  oracle than a manifest sample, which would only show pre-fix historical rows): a pre-listing symbol's Tardis 400
  carries JSON `code=140`/`code=300`, both in `TardisHTTPError.STRUCTURAL_ABSENCE_400_CODES`
  (`tardis_base_client.py:152`), so `is_structural_absence` is True and `tardis_csv_transport.py`'s 400 handlers
  (streaming + non-streaming) return the honest-absence skip sentinel → `empty_confirmed`, never `attempted_failed`.
  Reactive backstop is backed by UAC `classify_venue_error` registering `140`/`300` as `ErrorAction.SKIP`, and the
  vendor-catalog gate (`tardis_vendor_catalog.py`, `availableSince<=date<=availableTo`) is a second proactive layer.
  Conclusion: efficiency-only (wasted vendor call while the GCS-path filter was broken); the manifest is NOT polluted
  with `attempted_failed` — no data-pipeline-correctness escalation required. No code change (verification todo).
