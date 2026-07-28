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
assigned_vm: planning
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

## Update 2026-07-25 (re-check for `defi_satellite_ao_dispatch_batch2` — per `ag-closeout-audit` batchN methodology)

This doc was excluded whole from `defi_satellite_ao_dispatch_batch1_2026_07_25.md` (`doc_too_large_or_risky_for_batch`).
Re-checked fresh per that plan's own finalize-plan todo 2 (`defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md`)
to see whether either item has settled enough for a batch2 candidate.

- **Item 2 (4 zero-capture protocols) — SUPERSEDED, no batch2 action needed.** `uniswap_v2`/`uniswap_v4`/
  `trader_joe_v2`/`velodrome_v2` were wired + smoke-tested 2026-07-14 (`defi_consolidated_closeout_2026_07_18.md` Track
  4), and real ground-truth coverage was verified 2026-07-24
  (`issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`, 160 venue×data_type×date combos probed against
  live GCS). That verification found real substantive historical data for all 4 protocols but 2 residual gaps
  (TRADER_JOE_V2 `dex_pool_swaps` 0% ever captured — TheGraph schema-cascade bug; VELODROME_V2 `dex_pool_swaps`
  near-zero) — **both already dispatched** as part of `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s combined
  `dex_swaps_handler.py` todo (Source: `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`). This half of
  the doc is closed by that coverage — nothing new to extract.
- **Item 1 (second writer path historical migration) — STILL genuinely too-large/risky, unchanged since 2026-07-10.** No
  new information found (no citing doc, commit, or plan addresses the `batch_onchain_subgraph`
  bare-`0x<address>.parquet` shape or its resolver question). "Scope a dedicated historical migration ... needs a real
  resolver ... same backup-first, VM-eligible pattern as the rest of this effort" is still a real, open-ended
  design-plus-migration effort (confirm/build a pool-address→symbol/venue/chain resolver, then a VM-eligible historical
  backfill/transform over a genuinely-live production data shape) — not a bounded, single-worker-checkable batchN todo.
  Per the `ag-closeout-audit` skill's non-batchable taxonomy, this stays in the "too-large-or-risky-for-a-batch-todo"
  category: it needs its own dedicated triage/design pass as a standalone plan when picked up, not a `batchN` slot.

**Net effect**: no `defi_satellite_ao_dispatch_batch2` item drafted from this doc. Re-check again at the next batch
cycle only if item 1's resolver/scope question gets independently investigated elsewhere first.

## Update 2026-07-28 — Item 1 SUPERSEDED (root cause + fix landed under a different plan)

Item 1's own resolver question ("pool address → symbol/venue/chain lookup ... join against it rather than re-deriving")
got independently investigated exactly as the 2026-07-25 update anticipated, but not from this doc —
`plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` (opened the same day as this doc's last re-check,
for an unrelated FLAGGED-marker investigation) found and fixed the actual root cause first, making the resolver-build
unnecessary.

**Verified by code read (this task, 2026-07-28)**: `_dex_pools_subgraph.py`'s protocol table maps exactly
`curve`/`sushiswap`/`velodrome_v2`/`trader_joe_v2` to the `messari_basic` entry (`_dex_pools_subgraph.py:300-308`) — no
other protocol uses it. Before the fix, `messari_basic` parsed responses via `_parse_curve`
(`_dex_pools_parsers.py:164-194`), which never reads `inputTokens` at all — genuinely **zero** symbol/venue/chain
columns, confirming this doc's original Item 1 description was accurate, not a description of a degraded-value case.
This is the exact same bare-`0x<address>.parquet` shape Item 1 described, for the exact same protocol set.

**The fix (shipped under the sibling plan, not this one)**: rather than building a pool-address→catalogue resolver to
backfill identity onto the old address-keyed leaves, the sibling plan fixed the query/parser at the source
(`_CURVE_QUERY` now requests `inputTokens { symbol }`/`fees`, and `messari_basic` now routes through
`_parse_messari_dex` instead of `_parse_curve` — `market-tick-data-service@63199601`) and re-backfilled the full
historical range directly from the subgraph with real symbols attached, no resolver needed:

- Query/parser fix: `market-tick-data-service@63199601` (2026-07-27).
- Per-subgraph 2022-indexing feasibility live-test: `market-tick-data-service@0f40a69f` (2026-07-27) — curve (ETHEREUM,
  AVALANCHE), sushiswap (ARBITRUM), trader_joe_v2 (AVALANCHE) fully recoverable; curve/OPTIMISM confirmed deindexed (no
  replacement possible, excluded); velodrome_v2/OPTIMISM recoverable from ~2023-06/07 (genuine protocol launch window,
  not a gap).
- Historical re-backfill with the fixed query: completed 2026-07-28 (`mtds-dex-pools-symbolfix-batch1c` +
  `mtds-dex-pools-symbolfix-batch2`), manifest spot-checked (creation-timestamp-verified) for every in-scope
  protocol/chain.
- Purge of the now-superseded old address-keyed leaves: script shipped `market-tick-data-service@249dc019`; category-2
  (address-keyed leaf) `--apply` run confirmed complete + independently re-verified 2026-07-28 (190,955 leaves deleted,
  5/5 spot-checked genuinely absent from GCS); category-1 (`_migrated_*` marker) purge in progress as of this edit (not
  blocking — a cleanup of redundant backup copies, not the identity gap this item was about).

**Disposition**: Item 1 is closed by this superseding work — no separate resolver or historical-migration build is
needed, and starting one now would duplicate/conflict with the sibling plan's in-flight purge todo. Full detail:
`plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` todos 2-5 + Progress Log.

## Todos

- [x] ✅ [BACKEND] P2. **Scope + build the `batch_onchain_subgraph` second-writer-path historical migration** — Item 1.
      **SUPERSEDED, no build needed** — root-caused + fixed at the source (subgraph query/parser, not a resolver) and
      historically re-backfilled under `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`
      (`market-tick-data-service@63199601`, `@0f40a69f`, `@249dc019`; backfill VMs completed + spot-verified
      2026-07-28). See "Update 2026-07-28" above for full evidence.
