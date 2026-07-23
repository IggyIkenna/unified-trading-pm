---
doc_type: issue
title:
  "Post-purge tradfi manifest cleanup: a force-rebuild does NOT drop the 686k stale massive + 16k phantom rows
  (deletion-resurrection gap)"
summary:
  After the authorized massive purge removed 1,701,422 batch_massive OBJECTS, the tradfi availability manifest still
  carries 686,005 stale batch_massive rows + 16,389 phantom batch_databento trades/tbbo captured rows (zero backing
  objects) + 35.5% blank instrument_id + 0% derivative -USD@LIN. A `consolidate(force=True)` will NOT drop the stale
  rows — the consolidator re-scans 100% of the canonical on a full rebuild and a pure DELETION correction survives
  trivially (the documented deletion-resurrection gap). rebuild_tradfi_manifest.py (additive per-VM shards, merged) also
  does not drop them. Fixing (a)+(b) needs surgical index removal; fixing (c)+(d) needs the object-walk id
  re-derivation. Both target a live _index a peer is already rebuilding — coordinate before any cutover.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [manifest, consolidator, deletion-resurrection, phantom-rows, data-correctness, tradfi, coordinate]
related:
  [
    massive_purge_blocked_databento_l1_entitlement_2026_07_20,
    reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-20
priority: P0
parent_epic: tradfi_master
source: "Post-purge manifest analysis (slot-1, 2026-07-20, RUN_TS=20260720-193849)"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# Post-purge tradfi manifest cleanup — the naive force-rebuild won't drop the stale rows

## ✅ RESOLVED (a)+(b) — surgical drop applied under paused consolidator (slot-1, 2026-07-20T20:09Z)

**(a) phantom + (b) massive are DONE via a CAS surgical drop.** (c)/(d) are SCOPED FOLLOW-UP (see below). The apply was
done directly, NOT handed off — the field turned out to be CLEAR for the tick `_index` (the only peer rebuild in flight,
`rebuild_gated.py`, writes the **instruments-store catalogue**, not this tick bucket; the only per-VM shard is the
frozen `_legacy_seed`).

**CRITICAL CORRECTION — the "16,389 phantom" count was CONTAMINATED; blind-dropping it would have destroyed real data.**
The phantom set was defined from a heuristic shard list (`phantom_db_l1_shards.json`, 3,488 CME/NYSE/NASDAQ tbbo+trades
shard-keys). A mandatory on-disk re-verification of every candidate shard (2,393 `(venue,day)` prefixes, delimiter walk)
found that **79 of the candidate shards actually HAVE `batch_databento` objects on disk** — CME is a databento-native
venue (GLBX) and genuinely holds historical tbbo/trades. Those 79 shards carry **12,790 real `captured` manifest rows**.
Only **3,413 shards (3,615 rows) are TRUE phantoms** (zero object on disk). Reconciliation is exact:
`16,405 candidate db-captured L1 rows = 12,790 KEPT (real data) + 3,615 TRUE phantom`. **Dropping the stale 16,389 would
have deleted ~12,790 rows of real captured coverage.** This is exactly why the task mandated on-disk re-verification
before dropping.

| step                     | value                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| consolidator PAUSED      | `gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-tradfi-cron --location asia-northeast1` (verified PAUSED)                                                                                                                                                                                                                                                                                                                                     |
| consolidator RESUMED     | `gcloud scheduler jobs resume …` (verified ENABLED `*/1`)                                                                                                                                                                                                                                                                                                                                                                                                             |
| snapshot                 | `_index/snapshots/pre_manifest_surgical_cleanup_20260720T200716Z.parquet` (gen `1784578000150929`, 5,209,585 rows)                                                                                                                                                                                                                                                                                                                                                    |
| (b) massive dropped      | **686,005** (`pipeline_mode==batch_massive`; GCS re-verified 0 objects across 12 sampled days 2020→2026)                                                                                                                                                                                                                                                                                                                                                              |
| (a) TRUE phantom dropped | **3,615** (db-captured L1 rows in the 3,413 disk-verified zero-object shards; NOT the contaminated 16,389)                                                                                                                                                                                                                                                                                                                                                            |
| rows                     | 5,209,585 → **4,519,965** (−689,620)                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| CAS write                | `if_generation_match=1784578000150929` → new gen `1784578157569319`; `schema_version` preserved **int64** (unique=[9])                                                                                                                                                                                                                                                                                                                                                |
| markers                  | `consolidator_content_write_at` PRESERVED (18:41:37 → next cycle no-op), `consolidator_run_at` refreshed (20:09:00)                                                                                                                                                                                                                                                                                                                                                   |
| durability               | `_legacy_seed` is EXCLUDED from every merge path when a canonical exists (`manifest_consolidator.py:783,873-875`); watched **2 post-resume cycles** (20:11:43Z + 20:12:37Z) — both `verdict=empty, shards_changed=0, rows_added=0, error_reason=""`; post-cycle index re-verified **4,519,965 rows, residual batch_massive=0, schema_version int64**, stall_state `streak=0`, only `_legacy_seed` in `per_vm/` — NO resurrection, NO `ManifestConsolidatorStaleError` |

capture_status deltas reconcile exactly: `captured −679,609` (675,994 massive + 3,615 phantom), `empty_confirmed −9,541`
(massive), `attempted_failed −470` (massive), `expected_unattempted` unchanged.

**(c)/(d) SCOPED FOLLOW-UP (not forced — provably entangled, and largely already resolved):**

- **(d) is ~91% `-USD@LIN` ALREADY** (the "0.0%" baseline below was measured pre-migration; the canonical-path migration
  has since landed canonical ids). Post-drop derivatives are **91.08% `-USD@LIN`**; the residual ~9% is `instrument_id`
  in `'ticks'`/blank form.
- **(c)'s real defect is small.** Of the 35.5% blank `instrument_id`, **1,765,757 are legitimate Option-A bundle/chain
  atoms keyed by `underlying`** (NOT defects, per contract). The genuine blank-no-underlying defect is **~82,032 rows
  (1.8%)**.
- **Why not forced now:** `instrument_id` is in `_OPTIONAL_DEDUP_COLS` (`manifest_consolidator.py:522-536`), so the
  object-walk re-derivation (`rebuild_tradfi_manifest.py`) writes rows with a DIFFERENT dedup key than the
  blank/`'ticks'` rows — a merge would ADD canonical rows ALONGSIDE the defective ones (or double-count), NOT flip them.
  Fixing (c)/(d) therefore requires the object-walk rebuild PLUS a second surgical drop of the superseded
  blank/`'ticks'` rows — a separate, heavier operation partly already covered by the in-flight catalogue rebuild + the
  expected-universe-v2 enumerator. Tracked as the follow-up todo below.

## ✅ RESOLVED (c)/(d) — MOOTED, evidence-backed consumer trace (2026-07-21, operator-authorised close)

**Verdict: the residual non-canonical manifest `instrument_id` is COSMETIC/UNUSED — no correctness-critical consumer
keys off its VALUE. The (c)/(d) object-walk re-derivation + 2nd surgical drop is NOT worth the risk and is closed
resolved-as-mooted.** A standalone index surgery here is exactly the risky op the SSOT warns against, and it buys
nothing no consumer reads.

### Consumer trace — who reads the manifest `instrument_id`, and whether its canonical form matters

| Consumer                                                                     | Reads manifest `instrument_id`?                                                                                               | Does the canonical form of the id STRING matter? | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **deployment-api served honest-coverage** (`mtds_honest_coverage_for_venue`) | Yes, to form coverage cells                                                                                                   | **NO**                                           | Every tradfi per-instrument data_type is **SEEDED** (`expected_unattempted` materialised — measured live: ohlcv_1m=307,512, plus ohlcv_1s/15m/24h, tbbo, trades, mbp_10, corporate_action, earnings), so `_seeded_expected_unattempted_dts` routes them to `_mtds_seeded_4state_dt_entry` (`data_status/mtds.py:500-576`) where cells are built from the manifest's OWN rows — **both numerator and denominator** — so the ratio is internally consistent regardless of the id string. Never matched against an external canonical set. |
| deployment-api Tier-3 `per_instrument_coverage` (`instrument_coverage.py`)   | Only for NON-seeded per-instrument dts                                                                                        | **NO (dead for tradfi)**                         | Inactive for tradfi because its per-instrument dts are seeded (above). Even if reached: blank ids hit the legacy→venue-level fallback (`:241-258`); populated ids are normalised (`_normalize_instrument_id_for_match` strips `@LIN`/`@INV` + whitespace) and matched against a **terse UAC MVP seed** — canonicalising to `VENUE:TYPE:ROOT-USD@LIN-…` would make matching WORSE, not better.                                                                                                                                           |
| **deployment-api catalogue / identity render** (`catalogue_lifecycle.py`)    | **No** — reads `prod/catalog.parquet`                                                                                         | n/a                                              | "The catalogue is the ONLY identity-level source" (`catalogue_lifecycle.py:6`). The canonical-id RENDER comes from the CATALOGUE, not the manifest. Catalogue canonicalisation is separately tracked (Phase B).                                                                                                                                                                                                                                                                                                                         |
| **instruments-service `measure_honest_coverage.py`** (offline audit)         | Yes, as a cross-bucket **dedup-key** component only                                                                           | **NO**                                           | `_SHARD_KEY_WITH_IID=[date,venue,instrument_id,data_type]` with a `(date,venue,data_type)` fallback; coverage % is from `capture_status` counts, not id values. Canonicalising the prd bucket alone would HURT cross-bucket dedup vs the legacy `market-data-tick-tradfi-{pid}` bucket, not help.                                                                                                                                                                                                                                       |
| **MTDS `reader.py`** (runtime data read)                                     | Reads the manifest, but resolves by `(venue,data_type,instrument_type,date,capture_status=="captured")` (`reader.py:851-855`) | **NO**                                           | Does NOT filter the manifest by `instrument_id`. Data is read by GCS path (`underlying=`/`symbol`); per-contract identity lives in parquet CONTENT. `'ticks'` is just the derivative bundle filename stem (`underlying={U}/ticks.parquet`).                                                                                                                                                                                                                                                                                             |
| runtime guards **ml / strategy / execution**                                 | Read FEATURES/STRATEGY manifests                                                                                              | **NO**                                           | `manifest_inference_guard`/`manifest_gap_handler` (features_bucket), `strategy manifest_allocation_guard` (features, keyed `asset_group×date`), `execution canonical_paths` (keyed `asset_group×date`) — none read the tradfi TICK manifest instrument_id.                                                                                                                                                                                                                                                                              |
| CSV / drilldown DISPLAY (`_csv_export.py`, `_instruments.py`)                | Yes, renders it                                                                                                               | cosmetic only                                    | Renders the shard/file-stem id; canonical identity display is the catalogue's job.                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **Operator-ruled corroboration**                                             | —                                                                                                                             | —                                                | The 2026-07-20 databento shard-atom ruling (`databento_future_option_blank_instrument_id_shard_atom_2026_07_19.md`) records a **repo-wide sweep that found NO honest-coverage / UI / gate code re-keying a tradfi chain atom on `instrument_id`** — the per-root blank-id atom keyed by `underlying` IS canonical.                                                                                                                                                                                                                      |

### Live re-measurement (post-cleanup `_index`, 2026-07-21) — the defect is smaller than feared and self-converging

Read of the live `market-data-tick-tradfi-prd` `_index/availability_index.parquet` (**4,519,965 rows; `schema_version`
int64=9; source = databento 4,473,311 + yahoo 41,999 + barchart 4,655 → `batch_massive`=0**, i.e. exactly the
post-(a)+(b) index):

- **The feared "~9% `ticks`/blank derivative" defect does NOT exist.** Literal `'ticks'` = **983 rows (0.02%)**.
  Derivative rows (850,240) = **52.2% legitimate blank chain-atoms** (keyed by `underlying`) + **42.6% canonical
  `@LIN`/`@INV`** + ~44k real Databento terse root codes (`6E.FUT`, `6A.OPT`). Non-blank derivative ids are **89.1%
  `@LIN`** (confirms the ~91% prior figure).
- **The genuine blank-no-underlying set = 104,440, but 95,658 are `empty_confirmed`** (legitimate absence — no data, so
  no id is expected) + 1,304 `attempted_failed`; **only 7,478 are `captured` (0.17%)** — and even those degrade
  gracefully via the seeded/legacy fallback above.
- **Self-converging:** the manifest `instrument_id` is DERIVED from the parquet-content id, the forward-writer already
  emits `-USD@LIN` (Phase A DONE), so the manifest converges passively as the separately-tracked Phase-B tick-content
  migration lands and the consolidator re-absorbs — **no standalone index surgery needed**. Attempting it now is
  strictly worse: `instrument_id ∈ _OPTIONAL_DEDUP_COLS` (`manifest_consolidator.py:522`) means a re-derive lands
  new-keyed rows ALONGSIDE the defective ones, requiring a rebuild PLUS a second paused-consolidator surgical drop — a
  data-loss-grade operation for a column no consumer reads canonically.

**Measurement script (read-only):** `scratchpad/measure_tradfi_manifest.py` (local copy of the `_index`; no writes to
prod).

## Measured post-purge manifest baseline (live `_index/availability_index.parquet`, 2026-07-20)

Total rows **5,209,585**:

> ⚠️ This baseline is the ORIGINAL first-pass measurement. See the ✅ RESOLVED section above for the CORRECTED numbers:
> (a) the real phantom count is **3,615**, not 16,389 (the 16,389 was contaminated with 12,790 real-data rows — proven
> by on-disk re-verification); (d) is already **~91% `-USD@LIN`** (this "0.0%" was a pre-migration measurement).

| defect                                                                      | measured (first pass)          | corrected (disk-verified) | target |
| --------------------------------------------------------------------------- | ------------------------------ | ------------------------- | ------ |
| (a) phantom `batch_databento` trades/tbbo `captured` (zero backing objects) | ~~16,389~~                     | **3,615** (dropped)       | 0      |
| (b) `pipeline_mode=batch_massive` rows (objects now purged)                 | **686,005**                    | 686,005 (dropped)         | 0      |
| (c) blank `instrument_id` share                                             | **35.5%**                      | 82,032 real (1.76M legit) | ↓      |
| (d) derivative rows in canonical `-USD@LIN` form                            | ~~0.0%~~ (stale pre-migration) | **91.08%**                | ↑      |

## The gap — a force-rebuild does NOT drop (a) or (b)

`unified_trading_library/manifest_consolidator.py:844-875` (`consolidate(force=True)`): a full rebuild window-dedups the
canonical + every per-VM shard, and `canon_read` re-scans **100% of the canonical's CURRENT state**. The code comment
(`:850-862`, `legacy_seed_captured_outranks_resurrection_risk_2026_07_15`) is explicit:

> a DELETION correction — when a row is removed from the canonical entirely (not flipped to a different status) … there
> is no competing row left for any tie-break to apply to: … the row is simply the ONLY row for that key on the next full
> rebuild, so it survives trivially.

So the 686,005 massive rows and 16,389 phantom `captured` rows — which must be DROPPED (massive) or DEMOTED (phantom
captured → empty_confirmed) — are NOT removed by `consolidate(force=True)`. `rebuild_tradfi_manifest.py` also does not
drop them: it writes ADDITIVE per-VM shards (captured-from-disk + CF-11 honest-absence re-emit of empty/failed rows
only), which the consolidator MERGES with the stale canonical.

## What actually fixes each defect

- **(a) phantom captured → empty_confirmed**: a STATE-FLIP (captured → non-captured) IS honored by the consolidator's
  captured-outranks demotion (a newer non-captured row for the same key beats a stale captured claim). So writing
  competing `empty_confirmed` rows for the 16,389 phantom keys via a per-VM shard works — OR surgical in-place re-stamp.
- **(b) drop 686,005 massive rows**: a DELETION, which the consolidator resurrects. Requires **surgical removal from the
  canonical parquet** (drop `pipeline_mode=batch_massive` rows) with the consolidator PAUSED (the 2026-07-15 Part-2 fix
  excludes `_legacy_seed` on force when a canonical exists, so once removed they stay removed across cycles — provided
  no shard re-adds them).
- **(c)/(d) id canonicalization**: the surgical drop/re-stamp does NOT touch ids — a projection confirms (c) actually
  rises to 37.3% after dropping massive. Lowering blank-id and producing `-USD@LIN` requires the **object-walk
  re-derivation** (`rebuild_tradfi_manifest.py` over the post-migration canonical disk paths, which carry the `-USD@LIN`
  ids), then a consolidation that lets those rows win their shard atoms.

## VERIFIED non-destructively (projection)

A local projection over the downloaded canonical (drop `batch_massive`; re-stamp the 16,389 phantom captured →
`empty_confirmed`) yields **(a) 0, (b) 0**, rows 5,209,585 → 4,523,580. Artifact:
`/tmp/tradfi_index_corrected_projection.parquet` (local, not applied). (c)/(d) unchanged by this projection — they need
the object-walk rebuild.

## Why this is coordinate-before-cutover (not a blind run)

- The live `_index` is rewritten by the **manifest consolidator every minute** (Cloud Scheduler `*/1`), and a **peer is
  actively rebuilding the tradfi manifest** (`unified-trading-pm@384f0345a` — "/data-pipeline-check-mtds … blocked only
  on a fresh consolidator run; 2025d rebuild HANGING on the redundant re-emit"; `mtds@ac051bfe` — "stamp tradfi
  schema_version int64 not string"). Concurrent writes to the same `_index` are the exact
  `reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12` incident class.
- The correct live procedure (SSOT `manifest-consolidator-ssot.md` § "Full / --force rebuild"): pause the tradfi tick
  consolidator Cloud Scheduler cron → snapshot the canonical → apply (surgical drop/re-stamp for a/b + object-walk
  rebuild for c/d) → verify → resume. Pausing a shared prod cron + colliding with an in-flight peer rebuild is a
  coordinate-and-announce action, per the operator's Phase-3 instruction.

## Follow-up todos

- [x] [BACKEND] P0. ✅ Applied the surgical drop(batch_massive)+drop(TRUE-phantom) for (a)+(b) with the consolidator
      PAUSED + canonical snapshotted + CAS write (`if_generation_match`), disk-verifying every candidate phantom shard
      first (caught 12,790 contaminated rows). Watched 2 clean no-op cycles post-resume; index 5,209,585→4,519,965,
      massive=0, schema_version int64. — `market-data-tick-tradfi` `_index` gen `1784578157569319`, 2026-07-20T20:09Z
      (slot-1).
- [x] [BACKEND] P1. ✅ **RESOLVED-AS-MOOTED 2026-07-21** (operator-authorised close). (c)/(d) object-walk id
      re-derivation is CLOSED without surgery — see the "✅ RESOLVED (c)/(d) — MOOTED" section above for the full
      consumer trace + live re-measurement. Verdict: **no correctness-critical consumer keys off the manifest
      `instrument_id` VALUE** (served coverage takes the seeded 4-state internally-consistent path; the identity render
      reads the catalogue `prod/catalog.parquet`, not the manifest; MTDS `reader.py` resolves shards by
      `(venue,data_type,instrument_type,date,captured)` not the id; ml/strategy/execution guards read features/strategy
      manifests keyed `asset_group×date`). The feared "~9% `ticks`" defect does NOT exist (983 rows, 0.02%); the real
      blank-no-underlying defect is only 7,478 `captured` rows (0.17%), and the manifest id self-converges (it is
      DERIVED from the already-canonical `-USD@LIN` parquet content) as the separately-tracked Phase-B tick-content
      migration lands. A standalone rebuild + 2nd surgical drop (id ∈ `_OPTIONAL_DEDUP_COLS`) is a data-loss-grade op
      for a column no consumer reads canonically — not worth the risk. (repo: market-tick-data-service — NO code change
      required)
- [ ] [BACKEND] P1. Add a manifest-vs-disk consistency check so a `captured` row with no object on disk fails loudly
      (prevents the phantom-row class recurring — this exact class produced BOTH the 3,615 real phantoms AND the
      contaminated 16,389 list). (repo: market-tick-data-service)
- [x] [DOCS] P1. ✅ The deletion-resurrection gap is intended behaviour; dropping rows requires surgical removal under a
      paused consolidator (force-rebuild is insufficient) — the `_legacy_seed` merge-exclusion
      (`manifest_consolidator.py:783,873-875`) makes a surgical drop durable. Documented here + in the codex SSOT §
      "Surgical row removal". (/codex/05-infrastructure/manifest-consolidator-ssot.md)
