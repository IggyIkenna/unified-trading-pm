---
doc_type: issue
title: CME options_chain legacy flat layout — ~187.5M rows outside the TradFi single-leg @LIN canonicalization
summary:
  The TradFi single-leg FUTURE/OPTION `@LIN`/`@INV`-`YYYYMMDD` migration (2026-07-09) deliberately excluded 120,946 real
  CME `data_type=options_chain` manifest entries (~187.5M rows) that sit under a different, unverified legacy
  per-contract/spread flat layout — no `underlying=X/` subdirectory, raw per-contract filenames
  (`CC__FMH0025!.parquet`), manifest `underlying` values are per-contract keys (`ESU4_C5675`). Real, confirmed via live
  GCS listing; correctly excluded rather than risked at this scale, but the historical instrument-id canonicalization
  for this population remains open.
status: open
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [instrument-id, canonicalization, tradfi, cme, options-chain, legacy-layout]
related:
  [
    instrument_id_format_canonicalization_2026_07_08.md,
    ../canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
  ]
created: 2026-07-10
parent_epic: instruments_master
assigned_vm:
resolved_by:
source:
  "Real finding surfaced by the TradFi single-leg migrate-stage agent (wf_118d8268-18c, 2026-07-09) while scoping the
  @LIN/@INV historical migration against the real availability_index.parquet manifest (single-walk discipline, not a
  fresh corpus walk)."
priority: P2
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

The 2026-07-09 TradFi single-leg canonicalization
(`market-tick-data-service/scripts/ migrate_tradfi_single_leg_product_root_lin_2026_07_09.py`) real-scoped its target
population from the existing `availability_index.parquet` manifest and found **158,812 real shard objects (~1.19B
rows)** in the bundled-chain layout it targets (CME `futures_chain` 147,807 + `options_chain` 8,419 + CBOE
`futures_chain` 2,586). That migration ran to completion on a VM (`canonical-migration-tradfi-20260709-160919`,
7,500.6s, `error=4` out of ~158,812).

Separately, real GCS listing found **120,946 CME `data_type=options_chain` manifest entries (~187.5M rows)** — an order
of magnitude larger than the migrated population — sitting under a structurally different, unverified legacy layout:

- Real filenames like `CC__FMH0025!.parquet` — no `underlying=X/` subdirectory grouping contracts by underlying.
- Manifest `underlying` values are per-contract keys (e.g. `ESU4_C5675`), not the human-readable product root (`SP500`)
  the rest of this canonicalization effort targets.

This population was **correctly excluded from the 2026-07-09 migration** rather than risked at ~187M-row scale without
first verifying the real layout's semantics — this doc tracks that exclusion as open work, not a decision to never do
it.

## Why it matters

This is a real, large population of CME options-chain historical data that does not yet carry the canonical
`@LIN`/`@INV`-`YYYYMMDD` instrument-id format or the human-readable product-root convention (`ES→SP500`, `VX→VIX`) the
rest of TradFi now has. It represents a meaningful fraction of the total TradFi historical corpus by row count.

## Recommended next step

1. Real investigation first: confirm the actual real-world meaning of this flat per-contract layout (is it a legacy
   pre-bundling write path, a different real data product, or a partial/abandoned migration from an earlier session?) —
   do not assume it mirrors the bundled-chain semantics.
2. Once understood, scope a dedicated migration (same backup-first, idempotent, VM-eligible pattern already proven for
   the rest of this effort) to bring this population's `instrument_id`/`underlying` values in line with the canonical
   target.
3. Given the real scale (~187.5M rows), this is a strong candidate for VM-based execution from the start (per the
   operator's standing durability preference), not a laptop-session migration.
