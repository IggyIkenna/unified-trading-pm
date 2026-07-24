---
doc_type: codex-ssot
title: CeFi Data Types Catalog
summary:
  Catalog of the CeFi MTDS data types — sources, per-venue genesis floors, shard keys, coverage axes, and
  NEEDS_CANDLE_PROCESSING routing. Stub created 2026-07-24 to close a gap `tradfi-data-types-catalog.md`'s own
  NEEDS_CANDLE_PROCESSING table has and cefi's equivalent lacked entirely — the table below needs to be filled in
  against UAC's live `market_data_categories.py` NEEDS_CANDLE_PROCESSING dict (see the todo below); do not treat the
  placeholder as authoritative until that todo is closed.
status: current
nature: ssot
asset_group: [cefi]
stage: [meta]
repos: [execution-service, features-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, mtds, data-status, catalogue, candle-processing]
related:
  [
    /codex/02-data/tradfi-data-types-catalog.md,
    /codex/02-data/mdps-candle-canonical-reconciliation.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: "2026-07-24"
authoritative_for: [CeFi MTDS data_type catalog]
referenced_by: [/codex/02-data/README.md]
owner:
last_reviewed: "2026-07-24"
code_refs:
---

# CeFi Data Types Catalog

## NEEDS_CANDLE_PROCESSING

Indicates whether MTDS passes a data type through the MDPS candle-processing pipeline before writing to GCS (same
convention as [`tradfi-data-types-catalog.md`](tradfi-data-types-catalog.md)'s table of the same name). CeFi's native
resolution floor is the `book_snapshot_5` interval — see
[`mdps-candle-canonical-reconciliation.md`](mdps-candle-canonical-reconciliation.md) §1a.

| data_type                                        | NEEDS_CANDLE_PROCESSING | Notes |
| ------------------------------------------------ | ----------------------- | ----- |
| `derivative_ticker`                              | _TBD_                   | _TBD_ |
| `trades`                                         | _TBD_                   | _TBD_ |
| `book_snapshot_5`                                | _TBD_                   | _TBD_ |
| _(3 more CeFi data types — TBD, see todo below)_ |                         |       |

## Todos

- [ ] [DATA] P2. Fill in the table above against UAC's live `market_data_categories.py` NEEDS_CANDLE_PROCESSING dict —
      enumerate all 6 CeFi data types (per `data_pipeline_e2e_milestones_gate_2026_07_24.md` §5) with their real
      `True`/`False` value + a one-line note per row, mirroring `tradfi-data-types-catalog.md`'s exact table structure.
      Definition-of-done: 0 `_TBD_` placeholders remain, each row cites the UAC dict entry it reflects.
