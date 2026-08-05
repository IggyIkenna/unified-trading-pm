---
doc_type: issue
title:
  C0-RD5/C0-RD5b legacy-orphan-sweep todos stranded unchecked inside an archived plan, unreachable from any active doc
summary: >-
  Byproduct discovery from a 2026-07-31 na-eligibility-audit checkbox-citation fix (closing
  defi_dedicated_bucket_shared_migration_2026_07_13.md's last open todo, now archived). That todo's own text cited an
  "ambiguous Delete-when — a different, still-open C0-RD5b sweep exists in the archived governing plan" as the reason ~9
  dead-code campaign scripts were left in place rather than deleted (confirmed independently by
  defi_satellite_ao_dispatch_batch2_2026_07_26.md's 2026-07-26 audit AND defi_satellite_ao_dispatch_batch6_2026_07_30's
  2026-07-30 triage, both reaching the same conclusion). Tracing the citation: `plans/archive/2026_07/
  defi_manifest_canonicalisation_2026_06_01.md` (archived 2026-07-13) still carries two UNCHECKED `- [ ]` todos — C0-RD5
  ("delete ALL legacy... after C0-RD4 GREEN") and C0-RD5b ("orphan sweep of pre-existing legacy-FORM objects already in
  -prd") — that never migrated forward into any live plan when that doc archived, per
  /codex/12-agent-workflow/plan-completion-and-archival-discipline.md step 1 ("migrate any DEFERRED item into a real
  tracked todo"). They are the ONLY remaining evidence this specific legacy-orphan question was ever open; nothing in
  the active corpus currently tracks it.
status: open
nature: notes
asset_group: [defi]
stage: [data, meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [defi, archival, orphan-sweep, legacy-bucket, plan-hygiene, stranded-todo]
related:
  [
    /plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-07-31"
author: unknown
last_updated: "2026-07-31"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  na-eligibility-audit 2026-07-31 (tranche=defi, autonomous) — surfaced while fixing a stale checkbox citation on
  defi_dedicated_bucket_shared_migration_2026_07_13.md's P3 housekeeping todo; filed per the findings-triage HARD RULE
  ("outside every plan → plans/active/issues/<slug>_<date>.md") rather than chased to full resolution, since resolving
  it requires a live-GCS orphan sweep this audit's scope doesn't cover.
context_scope:
  [
    /plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    instruments-service/scripts/migration_orphan_sweep.py,
  ]
---

# C0-RD5/C0-RD5b legacy-orphan-sweep todos stranded in an archived plan

## What's actually open here (likely little-to-nothing — needs a quick live check, not a design call)

Two `- [ ]` todos in the archived `defi_manifest_canonicalisation_2026_06_01.md` (lines ~1230-1237 there):

- **C0-RD5** — delete ALL legacy DeFi buckets/paths, gated on C0-RD4 GREEN.
- **C0-RD5b** — orphan sweep of legacy-FORM objects pre-seeded in the `-prd` buckets before the v9 canonical migration
  wrote its own paths there (risk: double-counting in the C0e consolidator rebuild, or a non-`pipeline_mode`-aware
  reader reading stale rows).

Both are dated 2026-06-02/06-07 in origin. Substantial DeFi bucket work has landed since then that plausibly already
subsumes them:

- `gcs_bucket_estate_cleanup_2026_07_10.md` deleted 12 of 14 legacy kind-dedicated DeFi buckets.
- `defi_dedicated_bucket_shared_migration_2026_07_13.md` (archived today) migrated + deleted the remaining 3
  (`dex-pools-prd`/`lst-rates-prd`/`perp-funding-prd`).
- `defi_dex_pools_delete_order_stale_2026_07_20.md` + the 2026-07-21 dex_pools/lending_indices fold (per workspace
  CLAUDE.md: "FOLDED + DELETED 2026-07-21 — legacy prefixes now 0 objects") directly addressed the "legacy-form objects
  still present" risk class C0-RD5b describes, for at least those two data_types.

**Hypothesis, not verified**: C0-RD5/RD5b are most likely stale/superseded by this later, more specific work — but this
was not confirmed against live GCS state (that would require the kind of bucket-sweep this audit's scope doesn't cover)
and the archived host doc's own text never got a closing note when the later work landed, so the hypothesis should be
checked, not assumed.

## Todos

- [x] ✅ [SCRIPT] P3. Live-check whether any of the 8 legacy DeFi bucket-stems still hold pre-canonical legacy-FORM
      objects (`day=/category=defi/venue=...` or bare `date=` shapes, no `pipeline_mode=`) in the surviving `-prd`
      buckets today — **FOUND: 1,042 legacy-FORM objects + ongoing migration artifacts. See Progress Log for full
      characterization and scoped follow-up todos below.** — instruments-service@<SHA>

- [x] ✅ [DATA] P2. Backfill `record_captured` for the 1,042 CURVE dex_pool_state orphans (repo:
      market-tick-data-service) — market-tick-data-service@2b436caf — 205 true orphans registered in manifest via
      additive per-VM-shard ManifestWriter.add(); 837 already had canonical twins on GCS; verified post-apply: 0 orphan
      candidates remain.
- [x] ✅ [DATA] P2. Audit the `ticks_migrated` writer for canonical v9 path compliance — **FINDINGS: NOT a current
      writer defect; the fold already ran + manifest coverage is complete. See Progress Log for full audit.** —
      market-tick-data-service@13f14b78 (fold script, the canonical resolution)
- [x] ✅ [DATA] P3. Close C0-RD5/C0-RD5b checkboxes on the archived `defi_manifest_canonicalisation_2026_06_01.md` — per
      the corpus's existing precedent, edit the two `- [ ]` checkboxes (lines ~1230 and ~1232) directly in the archived
      doc to note their resolution: C0-RD5 (legacy bucket deletion) was subsumed by
      `gcs_bucket_estate_cleanup_2026_07_10.md` + `defi_dedicated_bucket_shared_migration_     2026_07_13.md`; C0-RD5b
      (orphan sweep) is now tracked by the two P2 todos above in this issue doc.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — swapped the archival-discipline codex doc for the
  actual live-check tool (`migration_orphan_sweep.py`, GCS→manifest orphan sweep) + the corroborating
  already-resolved-precedent plan the doc's own "Why" section cites.
- **na-eligibility-audit 2026-08-03 (reclassify pass)**: RECLASSIFY -> planning, the sole remaining todo is a bounded,
  worker-determinable live GCS check (grep 8 named legacy bucket-stems for a specific object-shape pattern, then
  close-as-moot-with-evidence or draft a scoped follow-up) — no design/judgment call left. Conflict-check: grepped
  `plans/active/*.md` + `plans/active/issues/*.md` for "C0-RD5" — the only other hit
  (`defi_satellite_ao_dispatch_batch2_2026_07_26.md`) is a corroborating citation on an already-closed, unrelated todo
  (deleting a specific script + auditing 8 campaign scripts for dead bucket templates), not a live claim on this doc's
  live-check work. CLEAR, no conflict.
- **slot-11 worker 2026-08-05 (live GCS check)**: Bounded, streaming scan of
  `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/` (121,655 parquet objects scanned, capped at
  200K). **FOUND two distinct classes of legacy-FORM objects**:

  **Class 1 — Pre-canonical dex_pool_state (1,042 objects)**: Exactly the shape C0-RD5b described.
  - Path:
    `raw_tick_data/by_date/day=2021-01-{17..31},{02-01..02-23}/asset_group=defi/venue=CURVE/chain=ETHEREUM/ instrument_type=pool/data_type=dex_pool_state/0x{address}.parquet`
    — NO `pipeline_mode=` segment.
  - All CURVE/ETHEREUM/pool, 38 unique days, 1 row each, ~11.7KB avg (real data, not zero-row shells).
  - These are true orphans: no canonical twin exists at the corresponding `pipeline_mode=batch_onchain_subgraph/` path.
  - Per `migration_orphan_sweep.py` taxonomy: class (E) ORPHAN_REAL — valid shape, rows>0, NO manifest row → needs
    `record_captured` backfill, never delete.

  **Class 2 — Migration artifacts (ticks_migrated\_, ongoing)**: A DIFFERENT, more concerning finding.
  - Path:
    `raw_tick_data/by_date/day=2026-01-{01..NN}/asset_group=defi/venue={AAVEV3,CURVE,ETHENA,ETHERFI,LIDO, MORPHO,UNISWAPV2,UNISWAPV3,UNISWAPV4}-ETHEREUM/ticks_migrated_20260418T{HHMMSS}Z.parquet`
    — NO `pipeline_mode=`, NO `data_type=`/`chain=`/`instrument_type=` hive keys, just bare venue with `-ETHEREUM`
    suffix.
  - Written by a migration on 2026-04-18 (filename timestamp), 9 files/day across 9 venues, real row counts
    (UNISWAPV3=40-70K rows, UNISWAPV4=10-23K rows). Scan only covered Jan 1-20; actual date range likely extends
    further. These are NOT pre-canonical — they're RECENT migration output not following canonical v9 path conventions.
  - This is a CURRENT writer defect, not just stale data to clean up.

  **What was NOT found**: The 8 legacy kind-dedicated buckets (dex-swaps, oracle-prices, gas-fees, dex-pools, lst-rates,
  perp-funding, lending-indices, eigenlayer-rewards) are all confirmed deleted per the earlier cleanup/migration work.
  The legacy top-level `dex_pools/` and `lending_indices/` trees are zero-objects (per the 2026-07-21 fold). No `day=`
  top-level objects exist. No `category=defi` objects exist. The surviving legacy-FORM objects are all in the shared
  `-prd` bucket under `raw_tick_data/` — exactly the pre-seeded-in-`-prd` scenario C0-RD5b predicted.

- **slot-10 worker 2026-08-05 (`ticks_migrated` writer audit — this todo)**: Traced the full provenance of the
  `ticks_migrated_20260418T*.parquet` objects through code and plan corpus. **FOUR FINDINGS, correcting the "current
  writer defect" framing above**:

  **(a) Origin**: The objects were produced by a one-time migration batch — the instruments-store v9 migration
  (`build_instrument_catalogue.py` / `migrate_instruments_store_v9.py`) — that ran on 2026-04-18 (the filename
  timestamp). All 5,332 objects share a single GCS `Creation time=2026-05-12` and `Storage class=COLDLINE`. The
  `ticks_migrated_<ts>.parquet` naming convention was the legacy batch's output-stamp for objects written at the
  composite-venue path (`venue=PROTOCOL-CHAIN`) without hive keys.

  **(b) Still running**: **NO — definitively not.** Verified in the issue doc
  `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` (lines 148-154): a bounded probe of near-present
  dates (2026-07-20/25/27) for `venue=UNISWAPV4-ETHEREUM/` under the non-canonical prefix found ZERO new objects. This
  is a frozen, one-time migration artifact, NOT an active writer producing new non-canonical output.

  **(c) Canonical re-path needed**: **ALREADY DONE.** The script `fold_legacy_composite_venue_objects_2026_07_31.py`
  (`market-tick-data-service@13f14b78`, applied 2026-08-01 via `defi_satellite_ao_dispatch_batch6_2026_07_30.md`)
  processed all 5,332 legacy shards → 324,867 canonical objects written with proper
  `pipeline_mode=batch_onchain_subgraph/`, fully decomposed hive keys
  (`chain=ETHEREUM/instrument_type=<type>/data_type=<dt>`), canonicalized venues (UNISWAPV2→UNISWAP_V2, AAVEV3→AAVE_V3,
  etc.), and remapped data_types (liquidity→dex_pool_state, swaps→dex_pool_swaps,
  rate_indices/utilization→lending_indices). The legacy objects remain as intentionally un-deleted residuals — deletion
  is the separate, delete-safety-gated `[PM] P2` todo in
  `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`.

  **(d) Manifest rows**: **YES for the canonical twins** — 324,867 `record_captured` rows registered during the fold.
  **NO for the legacy objects** (by design — the fold deliberately leaves them unregistered; they were never parseable
  by `parse_hive_path()` which returns `None` for the bare-venue `ticks_migrated_*.parquet` shape). This is correct: the
  canonical twins now carry the manifest coverage; the legacy residual objects await the separate deletion step. **No
  backfill needed** — the fold already handled it.

  **Conclusion**: No code changes required for this todo. The `ticks_migrated` writer is a frozen historical artifact,
  not a current defect; the fold has already restored canonical path compliance and manifest coverage. The ONLY
  remaining action is deleting the residual legacy objects, tracked separately by the `delete-the-legacy-copies` phase
  in `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`'s `[PM] P2` todo (requires operator +
  delete-safety protocol).

- **slot-8 worker 2026-08-05 (CURVE dex_pool_state orphan manifest backfill — this todo)**: Created
  `scripts/one_offs/backfill_curve_dex_pool_state_orphan_manifest_2026_08_05.py` in MTDS (modelled on the existing
  `register_extended_starknet_batch_extended_manifest_gap_2026_08_05.py` pattern). **Key finding correcting the slot-11
  scan above**: of the 1,042 legacy-FORM CURVE objects, **only 205 are true orphans** — the other 837 already have
  canonical `pipeline_mode=batch_onchain_subgraph/` twins on GCS. The slot-11 scan's "no canonical twin" claim was
  incorrect. Ran per-object twin-existence checks across all 1,042 (targeted per-object GCS prefix probes, never a
  corpus walk).

  **Orphan registration**: Registered the 205 true orphans in the production availability manifest via additive
  `ManifestWriter(per_vm_shards=True).add()` writes with `pipeline_mode=batch_onchain_subgraph`,
  `source=onchain_subgraph`, `instrument_type=POOL`, `chain=ETHEREUM`. Verified post-registration: 0 orphan candidates
  remain across all 38 days — every GCS object now has a manifest `capture_status=captured` row.

  **837 with twins**: No action needed — the canonical writer already registered them. The legacy copies are redundant
  but harmless (same instrument_id, same row_count=1, same data).
