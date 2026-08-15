---
doc_type: issue
title: source column blank on 15 external-vendor manifest cells (cefi 14, tradfi 1) — post-backfill audit finding
status: open
nature: process
asset_group: [cefi, tradfi]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service]
scope: [engineer]
tags: [source-provenance, data-correctness, manifest, audit-finding]
related:
  [
    /plans/active/data_source_provenance_enforcement_2026_07_24.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md,
  ]
created: "2026-08-15"
author: slot-18 infra worker
assigned_vm: planning
execution_scope: orchestrator-agent
parent_epic: infrastructure_master
priority: P1
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
resolved_by:
source: >-
  Produced by cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md's [CODE] P2 todo: "Run
  scripts/quality_gates/audit_source_column_distribution.py against prod post-backfill and report the per-cell source
  histogram" (data_source_provenance_enforcement_2026_07_24.md).
summary: >-
  Post-backfill source-column audit across all 5 prod manifests found 15 external-vendor cells (14 cefi, 1 tradfi) with
  a residual blank-source tail (<9K rows out of ~213M audited) — narrows the still-open
  data_source_provenance_enforcement_2026_07_24.md backfill scope to these named cells.
drift_direction: advance-code
last_updated: "2026-08-15"
---

# source column blank on 15 external-vendor manifest cells — post-backfill audit finding

## What I found

Ran `scripts/quality_gates/audit_source_column_distribution.py` (read-only) against all 5 prod consolidated
`_index/availability_index.parquet` manifests
(`market-data-tick-{cefi,defi,pred,sports,tradfi}-prd-central-element-323112`). Before running it against the largest
manifest (DeFi, 6.7GB / ~160M rows) the script itself needed a fix — it materialized the entire manifest via a single
`pd.read_parquet()` call with no row-group streaming, which stalled indefinitely on this shared host even after
column-projection. Rewrote it to stream via `ParquetFile.iter_batches()` so peak memory stays bounded to the batch size
regardless of manifest size (`unified-trading-pm@13e98ea816` — shipped as part of this same todo).

Per-manifest results:

| asset_group | cells | rows        | RED cells | RED rows |
| ----------- | ----- | ----------- | --------- | -------- |
| cefi        | 172   | 29,804,891  | 14        | 8,841    |
| defi        | 2,027 | 159,832,617 | 0         | 0        |
| prediction  | 10    | 2,784,303   | 0         | 0        |
| sports      | 200   | 6,130,466   | 0         | 0        |
| tradfi      | 90    | 14,337,262  | 1         | 64       |

A cell is RED when it has a UAC `SOURCE_PRIORITY` entry with ≥1 external source (i.e.
`external_sources_for(asset_group, data_type)` is non-empty) yet has rows with a blank `source`. 15 such cells, all with
the overwhelming majority of rows correctly stamped and only a small residual blank-source tail:

**cefi (14 cells / 8,841 blank rows):**

- `ASTER/book_snapshot_5` — 509/76,202 blank
- `ASTER/liquidations` — 580/11,753 blank
- `BINANCE-FUTURES/book_snapshot_5` — 6/614,429 blank
- `BINANCE-FUTURES/trades` — 34/716,053 blank
- `DERIBIT/derivative_ticker` — 6,832/290,263 blank (largest single gap)
- `HYPERLIQUID/book_snapshot_5` — 97/391,690 blank
- `HYPERLIQUID/derivative_ticker` — 8/636,076 blank
- `HYPERLIQUID/trades` — 98/343,050 blank
- `KRAKEN-FUTURES/book_snapshot_5` — 28/636,804 blank
- `KRAKEN-FUTURES/derivative_ticker` — 23/1,049,996 blank
- `KRAKEN-FUTURES/trades` — 158/649,272 blank
- `OKX-FUTURES/book_snapshot_5` — 112/52,321 blank
- `OKX-FUTURES/derivative_ticker` — 214/106,520 blank
- `OKX-FUTURES/trades` — 142/158,465 blank

**tradfi (1 cell / 64 blank rows):**

- `CME/ohlcv_15m` — 64/6,527 blank

## Why it matters

`data_source_provenance_enforcement_2026_07_24.md`'s P0 write-path/backfill/manifest todos are all still `- [ ]` open as
of this audit (confirmed via the plan's own Progress Log, last dated 2026-08-09: "13 open items"). So this is NOT the
"confirm zero blank on every cell, all asset groups" post-backfill sign-off state that plan's [AUDIT] todo ultimately
wants — the corpus-wide backfill hasn't landed yet. This audit run is honest, real data-state (not the pre-backfill
~100%-blank baseline either): the overwhelming majority of rows already carry `source` correctly (DeFi's 159.8M rows are
100% clean; sports/prediction are 100% clean), and the residual gap is narrow and concentrated (14 cefi cells + 1 tradfi
cell, <9K total blank rows out of ~213M rows audited). This narrows the remaining backfill scope precisely instead of
leaving it as an unscoped "run a corpus backfill" todo.

## Recommended decision

- [ ] [DATA] P1. Backfill the `source` column for the 14 named cefi cells above (repo: market-tick-data-service or
      market-data-processing-service, whichever owns manifest consolidation for these shards) — target rows are
      `capture_status=captured` with `source=""`/blank; the correct value per cell is inferable from the cell's own
      dominant non-blank source (e.g. `ASTER/book_snapshot_5` → `aster`; `BINANCE-FUTURES/*` → `tardis` given the 600K+
      tardis-attributed rows dwarf the 13K `binance`-direct rows — confirm the correct per-row attribution against the
      write-path code before backfilling, don't just impute the majority value blindly).
- [ ] [DATA] P1. Backfill the `source` column for the 1 named tradfi cell (`CME/ohlcv_15m`, 64 rows, repo:
      market-tick-data-service) — all 6,463 non-blank rows are `databento`; verify the 64 blank rows are also genuinely
      databento-sourced (not a different vendor silently uncaptured) before backfilling.
- [ ] [SCRIPT] P2. Re-run `scripts/quality_gates/audit_source_column_distribution.py --strict` against
      `market-data-tick-cefi-prd-central-element-323112` and `market-data-tick-tradfi-prd-central-element-323112` after
      the two backfills above land — confirm 0 RED cells (exit 0).
- [ ] [CODE] P2. Once confirmed zero-blank on cefi + tradfi, flip the `[DATA]` P0 **"Data parquets"** todo in
      `data_source_provenance_enforcement_2026_07_24.md` (line ~184) — **correction (2026-08-15, slot-32): that item is
      ONE combined checkbox spanning all 5 asset groups ("populated on every ingested cell across all five asset
      groups"), not five separable per-group checkboxes** — despite defi/prediction/sports already being 0-blank per
      this audit's own table, there is nothing to flip for them individually; the single checkbox can only flip once
      cefi + tradfi ALSO reach zero-blank. Verified live 2026-08-15: still `- [ ]`, correctly unflipped.

## Progress Log

- **2026-08-15 (slot-18·infra)**: filed after running the full-corpus post-enforcement `source`-column audit across all
  5 prod manifests per `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md`'s dispatched todo.
- **2026-08-15 (slot-32, data_engineering)**: Dispatched the P2 "flip the P0 checkbox" todo above. Found its premise
  imprecise: `data_source_provenance_enforcement_2026_07_24.md`'s "Data parquets" P0 item (line ~184) is a single
  checkbox covering all 5 asset groups jointly, not per-group — so "flip defi/prediction/sports individually" isn't a
  real action available in the target plan; corrected the todo's wording in place (see above) rather than leaving a
  future worker to rediscover this. Both P1 backfill todos above (cefi 14 cells, tradfi 1 cell) are still unchecked with
  no Progress Log entry showing work started — genuinely nothing to flip yet. GATED-skipping (~120 min), same root
  blocker as the P2 audit-rerun todo (already GATED this session).
