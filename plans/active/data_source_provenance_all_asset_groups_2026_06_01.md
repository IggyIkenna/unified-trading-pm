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

> **🟡 SEQUENCING DEPENDENCY — `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` is RUNNING (2026-06-01).**
> That plan drained the tick-data writers and is migrating legacy→canonical tick buckets via **server-side copy**
> (`migrate_legacy_tick_buckets_to_canonical.py` — moves objects, does NOT add columns). It touches the **same tick-data
> objects** + owns the drain/relaunch cadence. **Do NOT launch the `source`-column backfill now — it would race the
> in-flight copy** (and it needs the Phase 1/2 write-path fix first anyway). Sequence: (1) let the remediation finish;
> (2) **bundle this plan's source-stamping write-path fix (Phase 1+2) into the remediation's code-fix → tarball →
> relaunch** so relaunched writers stamp `source`; (3) run the source-column **data backfill after, on the CANONICAL
> buckets** (the server-side copy doesn't add `source`, so backfill is still required — not redundant). Net: each object
> is content-rewritten once. See § Migration scope.

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

## Scope boundary — what stamps `source` (so "all asset groups in full" is unambiguous)

- **IN SCOPE — every ingested raw market-data cell** that has a `SOURCE_PRIORITY` entry: all five asset groups, every
  venue × data_type. These carry an external vendor/source and MUST stamp it (write-path + backfill).
- **MDPS processed candles inherit/propagate the upstream source.** A candle is derived from a raw cell with a known
  `source`; the candle pipeline must carry that `source` through so a tardis-derived vs venue-derived candle stays
  distinguishable (Phase 4-MDPS todo). Same swap-resilience rationale.
- **EXEMPT (computed, no external vendor)** — features-service outputs, `strategy_output`, `execution_record`, `pnl`, and
  any data_type with **no** `SOURCE_PRIORITY` entry. The gate does not fire for these; their lineage is the upstream
  cell, not a vendor. (If such a cell unexpectedly has a `SOURCE_PRIORITY` entry, that's a registry bug to fix.)

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
- [ ] [SCRIPT] P1. Write `backfill_defi_source_column.py` (copy tradfi template) — stamps the known historical source
      **per data_type** (most defi → `onchain_subgraph`; `oracle_prices` → resolve pyth vs chainlink from the existing
      `pipeline_mode`/path; `native_staking_rates` → solana_rpc vs helius_rpc). Idempotent.
- [ ] [DATA] P1. Backfill the existing DeFi corpus — run now, parallel in-region VMs sharded by `day=` (see § Migration
      scope); fold into the defi canonicalisation migration (`defi_manifest_canonicalisation_2026_06_01.md`) if open, else
      run direct; manifest re-consolidation after.

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
- [ ] [DATA] P1. Backfill `source="tardis"` onto the existing cefi corpus — **run now, parallel in-region VMs** (see
      § Migration scope, two steps): (1) data-parquet column backfill — **write `backfill_cefi_source_column.py`** (copy
      tradfi template) then fan it across many same-region VMs, sharded by `day=` (no egress, idempotent); fold into the cefi-bucket migration
      if one is already pending, else run direct; (2) manifest re-consolidation after. Labels the corpus before any
      Tardis swap.

### Phase 4 — Sports writer source (P1)

- [ ] [MTDS] P1. Thread `source=` through Sports adapter writes (api_football / footystats / odds_api / understat).
      `market-tick-data-service/.../market_interface/adapters/sports/`.
- [ ] [TEST] P1. Sports multi-source unit test (same fixture from api_football + footystats → two rows, primary resolved).
- [ ] [SCRIPT] P1. Write `backfill_sports_source_column.py` (copy tradfi template) — **path→column migration**: read the
      source from the existing path segment (`data_source=ODDS_API/` legacy, `pipeline_mode=batch_api_football/` newer),
      write it into the `source` column on every row, and emit on the canonical column layout. Map each path token →
      closed-set source string. Idempotent.
- [ ] [DATA] P1. Backfill the existing sports corpus — run now, parallel in-region VMs sharded by `day=` (see § Migration
      scope); manifest re-consolidation after. Confirms sports source moves path→column for the whole corpus.

### Phase 5 — Downstream reconciliation wired for all multi-source asset groups (P0 correctness)

- [ ] [TEST] P0. Prove the consumer read path resolves source priority for **cefi/defi/sports** (not just tradfi):
      2-source fixture (same instrument+ts from two providers, co-mingled in one folder) → consumer emits exactly ONE
      resolved row via `select_primary_available_source()`. No silent double-count. Cover features-service consumers.
- [ ] [UAC] P1. Confirm `detect_dual_source_conflicts()` is invoked at consolidation/audit time for every multi-source
      asset group; `DUAL_SOURCE_DUPLICATE`/`VALUE_DIVERGENCE`/`COVERAGE_DIVERGENCE` surfaced, never swallowed.
- [ ] [TEST] P1. **`available_at` parity across sources (batch = live)**: rows from any source for a cell are timestamped
      with the live-mode `available_at` of the `SOURCE_PRIORITY` top entry — NOT each vendor's slower archive time. A
      2-source fixture asserts identical `available_at` derivation per cell, so swapping/adding a source never shifts the
      lookahead. (Covers the tradfi audit item (n) generalised to all asset groups.)
- [ ] [UAC] P1. **FINDING (2026-06-01 read-path audit)**: `select_primary_available_source()` /
      `detect_dual_source_conflicts()` are generic + unit-tested across cefi/defi/sports (UAC@559dc81b proves
      resolution is NOT tradfi-gated) but **are not called by ANY non-test consumer** — they are dead code at the read
      layer. Wire the resolver into the actual consumer read path (features-service loaders + any manifest/parquet
      reader that merges co-mingled multi-source folders) so reads emit one resolved row per cell. Until wired, multi-
      source resolution depends entirely on the consolidator's last-write-wins (see next item).
- [ ] [UTL] P1. **FINDING (2026-06-01 read-path audit)**: `manifest_consolidator.py` dedup key (`_BASE_DEDUP_COLS` +
      `_OPTIONAL_DEDUP_COLS`) **omits `source`** — two source rows for one `(date, venue, data_type, …)` cell collapse
      to ONE row by last-write-wins on `(attempted_at, written_at)`, NOT by `SOURCE_PRIORITY`. This matches the shipped
      tradfi **union** model (per-source provenance lives in the parquet `source` column, manifest is captured-if-any),
      so it is not currently a data-loss bug. **Decision needed (sequence with the data-side backfill behind the bucket
      remediation)**: if per-source *manifest* rows must be preserved, add `source` to `_OPTIONAL_DEDUP_COLS` — but that
      changes consolidation cardinality for all asset groups and naive (non-resolving) consumers would then see N rows
      per cell, so it must land together with the read-path resolver wiring above. Do NOT change unilaterally.

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

> **EXECUTE — parallel in-region VMs (operator decision 2026-06-01), but SEQUENCE behind the running tick-bucket
> remediation.** This is just read+write; on VMs in the same region there is **no egress cost** and it fans across many
> VMs, so it is **fast — do not defer to a future window.** Single-walk discipline's real constraint is *"touch each
> object once,"* NOT *"wait."* Decide per bucket:
> - **A tick-bucket migration is RUNNING right now** — `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`
>   (legacy→canonical **server-side copy**, writers already drained). Its copy does NOT add `source`. **Do not run a
>   concurrent `source` walk on those objects** (race). Sequence behind it: run the `source` backfill on the **canonical**
>   buckets **after** the copy completes. The copy is metadata-cheap (server-side), so the only content rewrite is this
>   backfill → still "touch once" for the expensive op.
> - **If a CONTENT-rewriting whole-corpus pass is pending** for a bucket (e.g. the defi canonicalisation migration
>   `defi_manifest_canonicalisation_2026_06_01.md`, or a v9 schema migration), **fold the `source`-column add into that
>   pass** — read+written once with both changes.
> - **If nothing is pending/running** for a bucket, the `source` backfill **is** that bucket's walk — run it directly.
>
> Check the MTDS migration registry to pick run-direct / fold-in / sequence-behind per bucket (never to defer). **New
> writes stamp both places at write time → no migration for new data.**

### Execution sequencing (per asset group, parallelised across VMs)

1. **Write-path fix first (Phase 1 + 2)** — land the universal source gate + writer stamping so new writes carry
   `source`; otherwise the backfill races fresh blank rows.
2. **Pre-migration drain (HARD RULE)** — stop that bucket's writer VMs (GCP Cloud Run + AWS batch), consolidate the
   manifest, snapshot `_index` to `_index/snapshots/pre_source_backfill_<date>.parquet`.
3. **Parallel data-parquet backfill** — fan the per-asset-group `backfill_<ag>_source_column.py` (template = the tradfi
   one) across many same-region VMs, sharded by `day=`/partition (idempotent; skip non-blank). No egress (in-region).
4. **Manifest re-consolidation** → verify zero blank `source` (data-state read) → **resume writers**.

## Out of scope (deferred — named successors required)

- (none for the source backfill — operator authorised running it now, parallelised; see § Migration scope.) Per-bucket
  execution is tracked by the Phase-3/4/7 backfill todos + a `<asset_group>_source_backfill_<date>.md` runbook if a
  bucket's fold-in/run-direct needs its own ledger.

## Completion criteria — "closed in full" across all asset groups

This plan is closeable only when ALL of the following are GREEN (no asset_group, no step skipped):

- [ ] **Write-path** — universal gate live (`source` blank OR not-in-`SOURCE_PRIORITY` → raise) for every asset group;
      every MTDS/MDPS writer (cefi/defi/sports/prediction/tradfi) stamps `source`; QG STEP 5.64 generalised + green.
- [ ] **Data parquets** — `source` column populated on every ingested cell across all five asset groups, read from
      ACTUAL prod rows (data-state, not the constant): **zero blank `source`**. Sports migrated path→column. MDPS candles
      carry the inherited upstream source.
- [ ] **Manifest** — re-consolidated; manifest `source` populated for every cell; multi-source cells = two rows.
- [ ] **Downstream** — consumer read path resolves source priority for every multi-source asset group (one row per
      instrument+ts, no double-count); `detect_dual_source_conflicts()` surfaces divergence; `available_at` parity holds.
- [ ] **Sequencing honoured** — source backfill ran behind / folded into the running tick-bucket remediation, on
      canonical buckets, no race.
- [ ] **Codex + audit instructions** updated to the universal rule; audit result archived when every todo above is `[x]`.

Scope exemptions (by design, not gaps): features-service / strategy / execution outputs (computed — no vendor source).

## Codex SSOTs

- `codex/02-data/contracts-scope-and-layout.md` — generalise dual-source `source` column section beyond tradfi
- `codex/02-data/honest-absence-downstream-handling.md` — generalise multi-source consumer policy
- `codex/02-data/availability-manifest-and-data-status.md` — `source` field semantics across asset groups

## Provenance

Crosscutting data-source provenance audit run 2026-06-01 (slot 1, operator-directed). Four parallel read-only audits
(cefi/defi/sports/prediction) + the prior tradfi exploration. Operator directive: provenance must be auditable across
**all** asset groups, gaps exposed, PM active todos created.
