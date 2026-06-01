---
title: Data-source provenance enforced across all asset groups (source column + SOURCE_PRIORITY)
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
priority: P0
status: active
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
created: 2026-06-01
locked_by: live-defi-rollout
locked_since: 2026-06-01
completion_gates:
  code: C5
  deployment: D3
  business: B4
repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: features-service
    code: C0
    deployment: none
    business: none
related_plans:
  - plans/epics/mtds_mdps_master.md
  - plans/active/tradfi_massive_dual_source_2026_05_28.md
  - plans/epics/defi_master.md
  - plans/epics/sports_master.md
---

# Data-source provenance enforced across all asset groups

## Overview

TradFi shipped a dual-source provenance model (`tradfi_massive_dual_source_2026_05_28.md`): a shard
(`data_type × venue × time`) may be populated by more than one vendor over time, **co-mingled on the same hive drop**
and disambiguated by a **row-level `source` column** + a per-source manifest row, resolved downstream via UAC
`SOURCE_PRIORITY`. Operator decision 2026-06-01: **`source` stays a column, not a hive path key** — better for
batch/live symmetry and single-walk discipline.

**This concern is crosscutting, not TradFi-only.** Every asset group except prediction realistically gets the same
logical metric from >1 source over time. The crosscutting audit (2026-06-01, see § Audit findings) found the root
cause: **`SOURCE_PRIORITY` already declares multi-source lists for cefi / defi / sports, but the `source` field is only
*enforced* and only *wired downstream* for `category=="tradfi"`.** Everyone else writes `source=""` with no gate and no
read-time reconciliation — so two sources for one cell silently collapse (last-write-wins) or double-count.

## Design decision (SSOT for this plan)

**Source is stamped on EVERY cell, ALL asset groups — even when only one source is currently declared.** (Operator
2026-06-01: "I don't care if there are two data sources yet — I may find an alternative for Tardis, so it's the same
issue.") The source a cell uses can change over time — a Tardis replacement, a second vendor added, a provider swapped.
If you only start stamping `source` at the moment a 2nd source appears, the entire pre-existing single-source corpus is
left unlabelled and cannot be distinguished from the new source after the swap. So stamping is **universal**, not gated
on cardinality.

Generalize the existing TradFi gate (`manifest_writer.py` `if category == "tradfi" and not source`) to:

> **Raise `MissingSourceError` when `source` is blank OR not a member of `SOURCE_PRIORITY[(asset_group, data_type)]`, for
> every captured cell.**

`SOURCE_PRIORITY` validates *which* source is allowed (closed set) and drives *resolution* when >1 exists — it does NOT
decide *whether* to stamp. Cardinality (>1) governs resolution only. No asset_group is exempt; no hardcoded list; the
registry is the SSOT for the allowed source strings (it already enumerates the current source for every cell, e.g.
`("cefi", …)=["tardis"]`, `("prediction", "trades")=["polymarket_clob"]`).

## Audit findings (2026-06-01 crosscutting sweep — the exposed gaps)

Verdict basis: **every cell must stamp `source` now** (swap-resilience) — so a single-source cell with a blank `source`
column is RED, not exempt.

| Asset group | Current source(s) | `source` stamped today | Status |
| ----------- | ----------------- | ---------------------- | ------ |
| TradFi      | databento (+massive / yahoo / barchart) | ✅ v9 column + gate (`manifest_writer.py:2430`) | 🟡 code GREEN; **backfill now RUNNABLE** — `MASSIVE_API_KEY` provided (use S3 flat-files for bulk history; stamp `source=databento` on legacy rows) |
| DeFi        | `onchain_subgraph`/`onchain_rpc` (most), `oracle_prices`=pyth+chainlink, `native_staking_rates`=solana_rpc+helius_rpc | ❌ writers route via `add()`, never pass source (`_defi_manifest.py:174`, docstring L144) | **🔴 RED** — no cell stamps source; the 2 multi-source cells additionally collapse last-write-wins **today** |
| CeFi        | `tardis` (single, but **operator may swap for an alternative** → stamp now) | ❌ source `""` | **🔴 RED** — stamp `source=tardis` on every cefi cell NOW so a future Tardis-swap/2nd-source is distinguishable |
| Sports      | `api_football`/`footystats`/`odds_api`/… (`FIXTURES` already 2-source) | ❌ source in PATH not column | **🔴 RED** — path→column migration + stamp every cell |
| Prediction  | `polymarket_clob`/`polymarket_gamma_api`/… (single per venue) | ❌ source `""` | **🔴 RED** — stamp source now (swap-resilience). *Venue ≠ source still holds*: cross-venue dispersion (Polymarket vs Kalshi) stays a feature-layer concern, NOT a source merge |

> **Audit run 2026-06-01 (code write-path).** Full result + per-item evidence:
> [`plans/audit/results/data_source_provenance_audit_2026_06_01.md`](../audit/results/data_source_provenance_audit_2026_06_01.md).
> Correction (operator 2026-06-01): **provenance is universal** — every cell stamps `source` now, even single-source,
> because any source may later be swapped/supplemented. So **all five asset groups are RED/owed** for stamping (defi is
> additionally the one LIVE multi-source collapse). TradFi backfill is **unblocked** (`MASSIVE_API_KEY` provided).

## Phased execution

### Phase 1 — UAC + UTL: universal source gate (P0, foundation)

- [ ] [UAC] P0. Expose `validate_source(asset_group, data_type, source) -> None` (raises) in
      `unified-api-contracts/.../canonical/crosscutting/source_priority.py`: a non-blank `source` is REQUIRED for every
      cell that has a `SOURCE_PRIORITY` entry, and it must be a **member** of that entry's list (closed set). Cardinality
      (>1) is NOT the trigger — single-source cells require source too. (A cell with no `SOURCE_PRIORITY` entry at all is
      the only exemption; treat that as a registry gap to fix, not a pass.)
- [ ] [UTL] P0. Replace the hardcoded `if category == "tradfi" and not source` gate with the universal rule: raise
      `MissingSourceError` when `source` is blank OR not in `SOURCE_PRIORITY[(category, data_type)]`, for **all** asset
      groups. `unified-trading-library/.../manifest_writer.py:2426`. No single-source / prediction exemption.
- [ ] [TEST] P0. Extend `unified-trading-library/tests/unit/test_manifest_writer_source.py`: a cell from ANY asset group
      (incl. single-source cefi `tardis`, prediction `polymarket_clob`) without `source=` MUST raise; a `source` not in
      the cell's SOURCE_PRIORITY list MUST raise; two valid sources on one cell produce two manifest rows.

### Phase 2 — DeFi writer rewiring (P0, biggest gap)

- [ ] [UTL] P0. `DefiManifestRecorder.record_captured()` must accept `source: str` and route through
      `ManifestWriter.record_captured()` (currently routes through legacy `add()` which drops source).
      `market-tick-data-service/.../cli/handlers/_defi_manifest.py`.
- [ ] [MTDS] P0. Thread `source=` through every DeFi handler call site (oracle_prices, native_staking_rates,
      lending_indices, dex_swaps, dex_pools, evm_defi, solana_defi, +others). Source string = the actual provider used
      for that fetch, from the SOURCE_PRIORITY closed set. `market-tick-data-service/.../cli/handlers/*.py`.
- [ ] [MTDS] P0. Oracle + staking handlers already resolve per-row pipeline_mode at the callsite — stamp the matching
      `source` (`pyth_hermes`/`chainlink`, `solana_rpc`/`helius_rpc`) on each row in the same place.
- [ ] [AUDIT] P1. Features-service DeFi onchain calculators — audit every emit that touches a DeFi data_type and confirm
      source is stamped. `features-service/.../onchain/`.

### Phase 3 — CeFi writer source (P1 — stamp `source=tardis` NOW for swap-resilience)

> Operator 2026-06-01: "I may find an alternative for Tardis, so it's the same issue." cefi has one source today
> (`tardis`) but it MUST be stamped on every cefi cell **now** — so that when Tardis is replaced or a 2nd source is
> added, the existing corpus is already labelled `source=tardis` and downstream can distinguish/resolve. This is NOT
> latent; a blank `source` on cefi today is a real gap (the universal Phase 1 gate requires it).

- [ ] [MTDS] P1. Thread `source="tardis"` through every CeFi adapter write + extend
      `record_empty_for_shard`/`record_failed_for_shard` to accept + forward `source`.
      `market-data-processing-service/.../core/canonical_writer.py`. (No `SOURCE_PRIORITY` change needed yet — `tardis`
      is already the declared source; expand the list only when the alternative actually lands.)
- [ ] [TEST] P1. CeFi unit test: a cefi cell without `source=` raises; `source="tardis"` persists; a future
      `["<alt>", "tardis"]` registry expansion resolves two sources by priority.
- [ ] [DATA] P2. Backfill `source="tardis"` onto the existing cefi corpus — **two steps** (see § Migration scope):
      (1) data-parquet column backfill (walk+rewrite every cefi parquet, stamp `source=tardis`; template
      `backfill_tradfi_source_column.py`) — **bundle into a pending cefi-bucket migration window, NOT a standalone walk**
      (single-walk discipline); (2) manifest re-consolidation after. So the historical corpus is labelled before any
      Tardis swap.

### Phase 4 — Sports writer source (P1)

- [ ] [MTDS] P1. Thread `source=` through Sports adapter writes (api_football / footystats / odds_api / understat).
      `market-tick-data-service/.../market_interface/adapters/sports/`.
- [ ] [TEST] P1. Sports multi-source unit test (same fixture from api_football + footystats → two rows, primary resolved).

### Phase 5 — Downstream reconciliation wired for all multi-source asset groups (P0 correctness)

- [ ] [TEST] P0. Prove the consumer read path resolves source priority for **cefi/defi/sports** (not just tradfi):
      2-source fixture (same instrument+ts from two providers, co-mingled in one folder) → consumer emits exactly ONE
      resolved row via `select_primary_available_source()`. No silent double-count. Cover features-service consumers.
- [ ] [UAC] P1. Confirm `detect_dual_source_conflicts()` is invoked at consolidation/audit time for every multi-source
      asset group; `DUAL_SOURCE_DUPLICATE`/`VALUE_DIVERGENCE`/`COVERAGE_DIVERGENCE` surfaced, never swallowed.

### Phase 6 — QG + audit instructions + codex (P1)

- [ ] [QG] P1. Generalise QG STEP 5.64 (currently tradfi-only `source` kwarg check) to fire for any multi-source
      `(asset_group, data_type)` per `source_required()`. Wire into MTDS + MDPS `quality-gates.sh`.
- [x] ✅ [AUDIT] P1. Add a **Dual-source provenance** section to ALL per-epic audit instruction files: `tradfi_master`
      (items h–o), `cefi_master` (i–l), `sports_master` (h–j, incl. path→column migration finding), `predictions_master`
      (h–j, N/A-by-design invariant), `defi_master` (n1–n4, strongest multi-source case), `mtds_mdps_master` (Mode 1 item
      j, write-time stamping), `manifest_master` (item i, the `source`-column schema home + registry-driven gate). The
      defi/mtds_mdps/manifest edits were layered on top of an in-flight "zero-rows = silent lie" sweep (operator-acked
      2026-06-01 as ready-to-ship → bundled).
- [ ] [CODEX] P1. Generalise `codex/02-data/contracts-scope-and-layout.md` § "TradFi canonical schema — dual-source
      source column" + `honest-absence-downstream-handling.md` multi-source consumer policy to all multi-source asset
      groups (currently scoped to tradfi).
- [ ] [MTDS] P1. **Prediction — stamp `source` on every cell NOW** (`polymarket_clob` / `polymarket_gamma_api` /
      `kalshi_*`): single-source today but stamp for swap-resilience (a future Polymarket data-provider change). Required
      by the universal Phase 1 gate. `market-tick-data-service/.../engine/orchestrator.py` (`record_captured_from_counts`).
- [ ] [CODEX] P2. Document the prediction invariant precisely: stamping `source` ≠ treating venues as sources —
      Polymarket/Kalshi stay separate **venues**, cross-venue dispersion is a feature-layer concern, and when Kalshi lands
      it is a venue addition; AND each venue's cell still stamps its own source. Both are true.

### Phase 7 — Prod data-state verification (P1, post-enforcement)

- [ ] [DATA] P1. **TradFi backfill UNBLOCKED** (`MASSIVE_API_KEY` provided by operator 2026-06-01) — run the dual-source
      backfill per `tradfi_massive_dual_source_2026_05_28.md` Phase 5: stamp `source=databento` on legacy tradfi rows +
      ingest MASSIVE via **S3 flat-files** for bulk history (flat-files are independent of the REST tier — the bulk path;
      REST for incremental/live). Unblock the dual-source plan's deferred table accordingly.
- [ ] [AUDIT] P1. After enforcement lands, read ACTUAL `source` column distribution per (asset_group, venue, data_type)
      in prod manifests/parquets — confirm **zero blank source on EVERY cell, all asset groups** (not just multi-source).
      Data-state, NOT constant (manifest-v8 lesson: constant said 8 while 0% of rows were v8). Report per-cell histogram.

## Migration scope — `source` lives in TWO places (do not conflate)

`source` is recorded **both** as a per-row column inside the GCS **data parquets** AND as a field on the **manifest**
row (confirmed: UTL writegate v9 adds the column; `backfill_tradfi_source_column.py` "single-walk pass over every TradFi
parquet … stamps `source` on every row … rewrites the file in-place"; manifest `source` is populated by
re-consolidation). Backfilling the existing corpus is therefore **two distinct steps, per asset group**:

1. **Data-parquet column backfill (the data itself)** — walk every parquet under that asset group's canonical prefix,
   stamp the known historical `source` on every row, rewrite in place. Template:
   `market-tick-data-service/.../scripts/backfill_tradfi_source_column.py` (one per asset group: cefi→`tardis`,
   defi→`onchain_subgraph`/per-handler, sports→its source, prediction→`polymarket_clob`). Idempotent (skip files already
   carrying a non-blank `source`).
2. **Manifest re-consolidation** — runs **after** step 1; the consolidator re-derives the manifest `source` from the
   rewritten parquets. Index-level, cheap. (TradFi precedent: drain → consolidate → snapshot → backfill → re-consolidate
   → resume.)

> **SINGLE-WALK DISCIPLINE (HARD RULE — review-blocking).** Step 1 is a whole-corpus walk. Per CLAUDE.md +
> `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`, a standalone new whole-corpus walk to add the column
> is review-blocking. The source-column add MUST be **bundled into a pending/scheduled migration window for each bucket**
> (e.g. the defi canonicalisation migration `defi_manifest_canonicalisation_2026_06_01.md`, or a v9 schema migration) —
> not a dedicated walk. Check the MTDS migration registry first; if a walk is already open for that bucket, fold the
> column-add into it. **New writes going forward stamp both places at write time → no migration for new data.**

## Out of scope (deferred — named successors required)

- A **standalone, dedicated whole-corpus walk** purely to add `source` (it must instead bundle into a scheduled
  migration window — see § Migration scope). File a `<asset_group>_source_backfill_<date>.md` successor only to track the
  bundling of step-1 into the chosen migration window per bucket.

## Codex SSOTs

- `codex/02-data/contracts-scope-and-layout.md` — generalise dual-source `source` column section beyond tradfi
- `codex/02-data/honest-absence-downstream-handling.md` — generalise multi-source consumer policy
- `codex/02-data/availability-manifest-and-data-status.md` — `source` field semantics across asset groups

## Provenance

Crosscutting data-source provenance audit run 2026-06-01 (slot 1, operator-directed). Four parallel read-only audits
(cefi/defi/sports/prediction) + the prior tradfi exploration. Operator directive: provenance must be auditable across
**all** asset groups, gaps exposed, PM active todos created.
