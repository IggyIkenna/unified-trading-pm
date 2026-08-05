---
doc_type: issue
title: >-
  `dex_pools`/`dex_swaps`/`rate_indices` legacy data_type manifest residue (~4.0M rows) — scoping only, NOT executed;
  needs its own dedicated content-verified migration pass
summary: >-
  Confirmed via `/codex/02-data/defi-canonical-naming-ssot.md:88` (operator-locked 2026-06-01) that `dex_pool_state`/
  `dex_pool_swaps` are canonical at every layer and the legacy 2-layer split (manifest `dex_pools`/`dex_swaps`) is
  RETIRED. Confirmed via direct code read that no live writer emits these bare forms (MTDS handler consts already write
  canonical names; MDPS treats them as read-only legacy aliases). Real row counts are large — 2026-07-22 live census
  (cited in
  `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_progress_log_history_2026_08_03.md:105-107`):
  `dex_pools` 454,077 / `dex_swaps` 3,458,668 / `rate_indices` 49,096 rows (~4.0M total). This topic is nominally
  "owned" by `/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`, but that plan is at its
  1000-line hard cap (verified 2026-08-04) with no concrete scoped todo for this exact rename/fold — it references
  `dex_pools` only in a catalog-freshness probe context, not a migration todo. Filed as a standalone, properly-scoped
  issue doc (cannot add to the capped master doc) rather than executed inline — a migration at this row count needs its
  own dedicated dry-run + content-verification pass, per this exact workspace's own R5 precedent
  (`/plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`: a superficially-safe-looking `dex_pools/`
  delete order was overturned by a content-verify that found 32 legacy-only high-TVL pools NOT present in the
  "canonical" set — "the paths looked duplicated; the content was not"). Rushing a rename across 4M rows without
  per-shard content verification risks exactly that failure mode at much larger scale.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    defi,
    dex-pools,
    dex-swaps,
    rate-indices,
    canonicalisation,
    manifest,
    distinct-values,
    legacy-migration,
    data-correctness,
  ]
related:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-04"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
source: >-
  Sub-agent research dispatched from interactive session 2026-08-04, investigating the DEFI distinct-values
  non-canonical data_types panel under /autonomous dispatch (see
  defi_cefi_venue_chain_axis_contamination_2026_07_28.md's Progress Log for full session context)
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py,
  ]
---

# `dex_pools`/`dex_swaps`/`rate_indices` legacy data_type residue — scoping doc (2026-08-04)

## Why NOT executed this session

1. **Scale**: ~4.0M manifest rows spanning years — this is a genuine migration campaign, not a quick fix.
2. **The R5 precedent directly applies**: this exact workspace already had a near-miss on a superficially-identical
   "obviously safe" DeFi legacy-naming cleanup (`dex_pools/` GCS path fold, 2026-07-20/21) where a path/name-level
   "these look like duplicates" assumption was WRONG — content-verification found 32 legacy-only high-TVL pools
   (XMR/USDC $47M, BNB/USDC $18M, etc.) that a naive delete would have destroyed. A rename/fold of `dex_pools`→
   `dex_pool_state` (etc.) at the MANIFEST level carries the same risk class: is every `dex_pools`-labeled row's data
   actually IDENTICAL in shape/content to what a `dex_pool_state`-labeled row for the same cell would be, or did the
   legacy writer emit a different column set/grain that a blind rename would misrepresent? Not verified.
3. **Owning plan is capped**: `master_data_canonicalisation_migration_catalogue_2026_06_07.md` is at the 1000-line hard
   cap (`check_line_caps.sh`-enforced) — cannot append a new scoped todo there without first shrinking it (out of scope
   for this doc).
4. This session already made and caught one "assumed safe, wasn't" mistake on a much smaller delete candidate this same
   session (`defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s P2(b)) — proceeding to execute a 4M-row migration
   on the same day, on the same class of assumption, without a dedicated verification pass would repeat that exact
   failure mode at far larger scale.

## What's confirmed (safe to rely on)

- Canonical target: `dex_pool_state`/`dex_pool_swaps` (operator-locked 2026-06-01,
  `/codex/02-data/defi-canonical-naming-ssot.md:88`). No ambiguity on the TARGET naming.
- No live writer emits the bare legacy forms today (`dex_pools_handler.py`/`dex_swaps_handler.py` handler consts already
  write canonical names — this is a pure historical-residue migration, not a live-writer bug to fix first).
- `rate_indices` — NOT yet investigated this session; same "legacy vs current" question needs answering before assuming
  it's the same shape of fix as `dex_pools`/`dex_swaps` (do not assume; check the naming SSOT + writer code for
  `rate_indices`'s own canonical target before scoping the fix).

## Todos

- [ ] [DIAG] P2. Confirm `rate_indices`'s canonical target name/relationship (not yet checked this session — do not
      assume it mirrors `dex_pools`/`dex_swaps`; may be a different mechanism entirely, e.g. `lending_indices` with a
      typo/drift, or a genuinely separate legacy data_type).
- [x] ✅ [DIAG] P2. **RESOLVED 2026-08-04 (interactive session) — the R5 concern is CONFIRMED REAL for `dex_swaps`,
      REFUTED for `dex_pools`. Two genuinely different cases, not one.** Bounded, per-(venue,chain) date-set +
      instrument_id-set comparison (live `pyarrow.dataset` reads against `_index/availability_index.parquet`,
      columns-projected, filtered to the 4 data_types in question — not a full-corpus walk): - **`dex_pools` vs
      `dex_pool_state` — CLEAN 1:1, safe.** Only 2 (venue,chain) pairs carry `dex_pools` data (`ORCA/SOLANA`,
      `RAYDIUM/SOLANA`). At BOTH the date grain AND the finest instrument_id grain: **zero legacy-only entries** —
      canonical dates (1327/1326) and instrument_ids (28328/554) strictly SUPERSET the legacy population (32/31 dates,
      14093/109 instrument_ids) in both cases. This is a true 1:1 rename candidate. - **`dex_swaps` vs `dex_pool_swaps`
      — NOT clean, real content gap confirmed, same failure class as R5.** Date-grain comparison across all 24
      `dex_swaps` (venue,chain) pairs: **22 of 24 show a real legacy-only date gap** (only `UNISWAP_V2/ETHEREUM` and a
      near-zero 1-date case on `UNISWAP_V3/ETHEREUM` are clean). Gaps range from small (`PANCAKESWAP_V3/BSC`: 15
      legacy-only dates) to severe (`SUSHISWAP_V3/ARBITRUM`: **1,049 of 1,243 legacy dates (84%) have NO canonical twin
      at all**; `BALANCER`/`SUSHISWAP`/`CURVE` pairs show 400-620 legacy-only dates each). Two distinct gap shapes
      observed, both real: (a) OLD historical gaps (2023 dates, e.g. `BALANCER/ARBITRUM` starting 2023-03-08) — genuine
      historical legacy-only captures never re-backfilled under the canonical name; (b) a RECENT, consistent
      ~130-140-day gap clustered around 2025-07-27→2025-08-06+ across MANY venues simultaneously (`AERODROME_V3/BASE`,
      `CAMELOT_V3/ARBITRUM`, `PANCAKESWAP_V3/{BASE,ETHEREUM}`, `SUSHISWAP_V3/{AVALANCHE,ETHEREUM}`,
      `UNISWAP_V3/{ARBITRUM,BASE,OPTIMISM}` all show ~130-140 legacy-only dates in this exact window) — this shape
      suggests either a canonical writer that stopped/lagged recently for many venues at once, or a legacy writer that
      (surprisingly) kept running past its supposed retirement — NOT yet root-caused, flagging as a genuinely new
      sub-finding for whoever picks up the DATA migration below. Instrument_id-grain comparison NOT run for `dex_swaps`
      (3.46M legacy rows — the date-grain result alone is already decisive; an instrument_id pass would only refine
      severity, not the safe/unsafe verdict). **Verdict: `dex_pools` is DIAG-cleared for a simple rename; `dex_swaps` is
      NOT — it needs a real content migration (copy the legacy-only rows forward under the canonical name, verify, THEN
      retire), never a blind rename/delete.** This directly validates the caution this doc was filed under and the R5
      precedent it cited — the fear was not hypothetical.
- [ ] [DATA] P2. **`dex_pools` → `dex_pool_state`**: DIAG cleared above — safe to design + dry-run + execute as a pure
      manifest-only re-key (or a bounded 2-venue GCS relabel if the raw objects also carry the legacy data_type in their
      path) once someone picks this up. Small population (454K rows, 2 venue/chain pairs) — low risk, low effort.
- [ ] [DATA] P2. **`dex_swaps` → `dex_pool_swaps`**: DIAG above proves this is NOT a rename — it is a real content
      migration. Recipe: for each of the 22 gapped (venue,chain) pairs, copy the legacy-only-dated `dex_swaps` rows
      forward to canonical `dex_pool_swaps` form (mirroring the R5 fold precedent — copy, verify, THEN retire the legacy
      label), never delete first. **Before designing the migration, first root-cause the recent ~2025-07-27→2025-08-06+
      multi-venue gap cluster** (is a live writer currently still emitting `dex_swaps` for some venues today, or did the
      canonical writer silently stop for a window?) — migrating a STILL-ACTIVE legacy writer's output without first
      stopping/redirecting it would just regenerate the gap. Full five-part delete-safety proof required before any
      GCS-level change; this is now a genuinely large, multi-week-scale migration given severity (up to 84% legacy-only
      on some pairs), not a same-session task.
- [x] ✅ [REVIEW] P3. Fixed independently of the DATA migration below (no data risk, as this todo itself notes) —
      `unified-api-contracts@ab4693de` ("docs: correct stale _schema_spec_defi.py docstring — dex_pools/dex_swaps are
      RETIRED, not current writers"). Live-verified: the docstring now reads "RETIRED legacy manifest data_type names
      (corrected 2026-08-04: this docstring previously and incorrectly described these bare forms as 'current'
      writers...)" and cites this exact issue doc. — interactive session, 2026-08-04.

## Progress Log

- **interactive session 2026-08-04 (autonomous, `/autonomous`)**: filed as a scoping-only doc after confirming (a) the
  row counts are large enough to warrant dedicated care, (b) the owning master plan is at its hard line cap, and (c)
  this exact session already caught one "looked safe, wasn't" mistake on a smaller, related delete candidate this same
  day — proceeding to a 4M-row migration on an unverified content-equivalence assumption would repeat that failure mode.
  Not executed.
- **interactive session 2026-08-04 (separate session, `/autonomous`)**: independently arrived at this same doc while
  investigating an operator report of `dex_pools`/`dex_swaps` showing as non-canonical in a Data Status panel — cross-
  checked live writers (two running `mtds-dex-swaps-backfill-*` VMs' own per-VM manifest shards read directly from GCS:
  4527 + 400 rows, 100% `data_type=dex_pool_swaps`, zero legacy `dex_swaps` rows), confirming this doc's "no live writer
  emits the bare legacy forms" finding independently. Did not duplicate the DIAG/DATA todos above (correctly scoped,
  already gated on real content-verification per the R5 precedent this doc cites) — flipped only the REVIEW P3 todo,
  which was already shipped (`unified-api-contracts@ab4693de`) but left unchecked.
- **interactive session 2026-08-04 (continuation, operator directive: "batch/live symmetry — bad names shouldn't
  exist")**: ran the DIAG P2 content-comparison this doc had left open, per-(venue,chain) date-set + instrument_id-set
  bounded live reads (not a corpus walk). **Result is a genuine split verdict, not the single-outcome the todo
  anticipated**: `dex_pools` cleared clean (zero legacy-only content at any grain, safe rename); `dex_swaps` confirmed
  UNSAFE for a blind rename — 22 of 24 (venue,chain) pairs have real legacy-only date coverage, up to 84% on
  `SUSHISWAP_V3/ARBITRUM`. Rewrote the DIAG/DATA todos above to reflect the split (P2a rename-safe, P2b real-migration-
  required) and flagged an unexplained recent multi-venue gap cluster (~2025-07-27→2025-08-06+) for the next DATA
  picker-upper to root-cause before designing the P2b migration. This is exactly the R5 failure mode this doc was filed
  to guard against — confirmed real this time, not just a theoretical risk.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid — the 3 open items are a
  diagnostic pair (rate_indices canonical-target check, sample-based content-equivalence comparison) feeding a
  DATA-migration item gated on their outcome and likely needing delete-safety/[OPERATOR] handling; the
  content-equivalence judgment call is the exact risk class this doc's own cited R5 precedent shows can be wrong, so it
  stays genuine-caution NA rather than a clean mechanical RECLASSIFY. Doc stays `assigned_vm: NA`.
