---
doc_type: issue
title: DeFi DEX-pool — a second, undecomposed writer path + 4 protocols with zero forward capture code
summary:
  Two real, distinct DEX-pool gaps found while landing the 2026-07-09 fee-tier/symbol-shape canonicalization, both
  pre-existing and outside that fix's scope — (1) a second real writer path (`pipeline_mode=batch_onchain_subgraph`,
  bare `0x<address>.parquet` files with no symbol/venue/chain columns, confirmed live for CURVE) whose historical
  backlog needs its own migration; (2) `uniswap_v2`/`uniswap_v4`/ `trader_joe_v2`/`velodrome_v2` have zero forward
  capture code at all in `dex_pools_handler.py`/ `dex_swaps_handler.py`, confirmed via repo-wide grep.
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [instrument-id, canonicalization, defi, dex-pool, writer-path, capture-gap]
related: [/plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md]
created: 2026-07-10
parent_epic: instruments_master
assigned_vm:
resolved_by:
source:
  "Real findings surfaced by the DEX-pool migrate-stage agent (wf_118d8268-18c, 2026-07-09) while landing the
  fee-tier/glued_pair_id symbol-shape fix (market-tick-data-service@0ce28623)."
priority: P2
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

### 1. A second, distinct real writer path (undecomposed, no symbol/venue/chain columns)

While migrating the primary DEX-pool symbol-shape writer path (357,164 real objects, ~$6-9 obj/s, ~20h real elapsed),
the migration surfaced a **second, structurally different real writer path already live in production**:
per-pool-address-named files (`0x<address>.parquet`) built directly from `instrument_id`, with **no `symbol`/
`venue`/`chain` columns at all** — confirmed under `pipeline_mode=batch_onchain_subgraph` for CURVE (this contradicts
the original discovery pass's guess that this path might be dormant — it is not).

- The **forward-going code for this path is already fixed** (same commit `0713c01a` that fixed
  `curve_defi_ws.py`/`dex_swap_uniswap_v3_ws.py` also covers this).
- The **historical backlog under this shape was correctly and safely skipped** (not mis-touched) by the primary
  migration script, since it has a different schema with nothing to key a resolver against.
- Documented in `market-tick-data-service/docs/DEFI_DOWNLOAD_STRATEGY.md`.

### 2. Four DEX protocols with zero forward capture code at all

Confirmed via a repo-wide grep across `dex_pools_handler.py`/`dex_swaps_handler.py`: `uniswap_v2`, `uniswap_v4`,
`trader_joe_v2`, `velodrome_v2` have **no forward capture code path at all** — a real, pre-existing gap unrelated to the
symbol-shape canonicalization work, discovered as a side effect of reading the capture handlers closely.

## Why it matters

- Item 1: a real, live-production data shape with zero canonical instrument identity today. Any downstream consumer
  keying off `symbol`/`venue`/`chain` for this shape gets nothing — it has to derive everything from the raw
  `0x<address>` alone.
- Item 2: 4 real DEX protocols are silently not being captured going forward at all — a data-completeness gap, not a
  naming/format gap. Worth confirming whether this is intentional (protocol descoped) or a real regression/gap in
  coverage.

## Recommended next step

1. **Item 1**: scope a dedicated historical migration for the `batch_onchain_subgraph` shape — needs a real resolver
   (the pool address → symbol/venue/chain lookup likely already exists in the reference-data catalog; join against it
   rather than re-deriving). Same backup-first, VM-eligible pattern as the rest of this effort.
2. **Item 2**: confirm with the operator whether `uniswap_v2`/`uniswap_v4`/`trader_joe_v2`/`velodrome_v2` are meant to
   be captured at all (check the current DeFi MVP scope decision) — if yes, this is a real coverage gap needing a fix
   plan; if these are intentionally out of MVP scope, downgrade/close this half of the issue.
