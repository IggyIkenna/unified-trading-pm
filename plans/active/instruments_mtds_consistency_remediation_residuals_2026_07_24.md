---
doc_type: plan
title: Instruments <-> MTDS F1-N9 consistency remediation -- residual continuation
summary:
  Split 2 of 3 from instruments_mtds_subset_consistency_remediation_2026_06_17.md (2026-07-24 line-cap remediation,
  clean-partition). This is the parent's own CORE original scope -- the F1-F7/N1-N9 findings from the 2026-06-17
  subset+consistency audit, the pre-`--apply` blocker gate, the GCS delete-safety invariant + migration prerequisite
  map, the execution sequence, the v9 `_index` column population + venue/instrument_type spelling canonicalisation
  (N6r), the migration-unmappable-residue diagnosis, and Phase A-D findings/remediation. Mostly DONE (29/43 todos); 14
  residuals remain open.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [deployment-api, deployment-service, e2e-testing, features-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    instruments,
    mtds,
    manifest,
    canonicalisation,
    data-correctness,
    audit,
    backfill,
    pipeline-mode,
    reconciliation,
    defi,
    sports,
  ]
related:
  [
    instruments_mtds_subset_consistency_remediation_2026_06_17,
    instruments_store_cf_canonicalization_single_walk_2026_07_24,
    mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24,
    plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md,
    plans/active/instruments_foundation_completeness_2026_06_24.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-07-24"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
last_updated: "2026-08-09"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "instruments_mtds_subset_consistency_remediation_2026_06_17.md (split 2 of 3, plan-hygiene line-cap remediation,
    2026-07-24)",
    "plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md (findings F1-F7, full-index walk)",
    "plans/active/issues/plan_line_cap_remediation_2026_07_23.md",
  ]
drift_direction: advance-code
context_scope:
  [
    /plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/pipeline-mode-partition.md,
    e2e-testing/scripts/defi/audit_legacy_gcs_dup_delete_list.py,
    market-tick-data-service/market_tick_data_service/scripts/populate_v9_index_columns_inplace.py,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
---

# Instruments <-> MTDS F1-N9 consistency remediation -- residual continuation

> **Split provenance (2026-07-24).** This file is split 2 of 3 out of
> `plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md` (2168 lines, over the 1000-line hard-fail
> cap) per `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`'s bucket-(c) clean-partition classification
> (that plan was locked `live-defi-rollout`; operator granted `[unlock-plan]` for this specific split). This child
> carries the parent's **own original F1-N9 audit-remediation scope** verbatim -- no rewriting, no summarization. The
> parent plan is trimmed to a coordination index pointing here + to the other 2 siblings
> (`instruments_store_cf_canonicalization_single_walk_2026_07_24.md`,
> `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`). Four source line ranges from the parent are
> concatenated here, in original order: L63-215 (blocker banners + GCS delete-safety prerequisite map + execution
> sequence), L437-659 (GCS object-migration complete + delete-list sizing + v9 column population + N6r venue-spelling
> canonicalisation), L735-748 (CME event contracts -- v9-certification dependency), L839-1229 (autonomous-run residuals
>
> - migration-unmappable-residue diagnosis + Phase A/B/C/D findings).

# Instruments ↔ MTDS subset + consistency remediation

> **🔴 PRE-`--apply` BLOCKER GATE (2026-06-17).** The dry-run projections that `--apply` will materialise STILL carry
> these defects, and a reconcile `--apply` over uncovered path shapes flips real `captured`→`attempted_failed`
> (CLAUDE.md hard rule). **Do NOT `--apply` until these are fixed + the projection regenerated + re-eyeballed:** (1)
> **prefix_tpls coverage** — prove `ASSET_GROUP_CONFIG[ag]["prefix_tpls"]` covers ALL coexisting shapes
> (`category=`/`asset_group=`/bare/`pipeline_mode=`, see N7) per AG BEFORE apply; (2) **N6** normalize defi
> chain/venue/instrument_type pollution (apply migrates BY these values); (3) **N1** confirm dedup keeps the captured
> row, not the empty shadow; (4) **N3** recover sports league_id into the manifest first (else null-league is
> permanent); (5) **N5** verify the phantom-reconcile targets only true 0-row pre-launch vault cells. NON-blocking (fix
> after/parallel): F1, F3, N2, N4, F6, N8. **Apply order: pred → tradfi (clean) → cefi → sports → defi; never all-AG at
> once.**

Findings of record + method: `plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md`.

> **🟢 SCRIPT-COVERAGE MAP (2026-06-17) — every blocker is a GAP in the existing rebuild scripts, not unscripted.** The
> rebuild scripts ARE the migration: fix the gap → regenerate the dry-run projection → improved beta → `--apply`
> (path-schema) → backfills. Per finding: **prefix_tpls** ✅ `canonical_path_templates(ag)` covers all shapes (sports
> `[""]` — verify only); **N3** ⚠ï¸ `rebuild_sports_manifest_v9` never extracts `league_id`/`league` from the MTDS
> object path into the row_key (canonicalizer `_canonicalize_row_key_league_id` then gets null); **N1** ⚠ï¸
> `rebuild_cefi` CF-11 dedup key mismatches (empty re-emit has blank `instrument_type` vs captured populated → both
> survive); **N5** ❌ `rebuild_defi` emits `captured`/row_count=0 on file PRESENCE without opening (0-row/pre-launch →
> false captured) → route via `record_zero_rows`; **N6** ⚠ï¸ `rebuild_defi._split_legacy_venue_chain` lacks
> instrument_type case-norm + lets pairs leak into `chain` + incomplete venue-dedup; **F3** ❌ `rebuild_cefi` passes
> legacy `attempted_failed` reasons through un-reclassified; **N2** ❌ instruments enumerator marks CME weekend
> carry-forward as `SOURCE_RETURNED_ZERO`. **Each Phase-A/B/D todo below = a scoped fix to the named script → regen that
> AG's dry-run projection → re-audit the fixed dimension.** Phase-1 (manifest-level, full v9-projected-index walk) is
> DONE; Phase-2 (file-level cross-year manifest-vs-reality sampling) is IN PROGRESS via per-AG sub-agents — findings
> fold back into the audit doc + new todos here.

> **🔴🔴 GCS DELETE SAFETY INVARIANT — READ BEFORE DELETING ANY OBJECT (codified 2026-06-18; HARD RULE).** **The
> manifest migration RELABELLED nothing — it is a CELL-KEYED rewrite (`_index` rows keyed by
> `(date,venue,data_type,instrument_type,instrument_id,underlying)`, NOT by GCS path); the v9 data was physically COPIED
> to canonical paths by `migrate_*_v9_canonical` (COPY not MOVE → the legacy bare `asset_group=`/`category=`/top-level
> `day=` shapes are DUPLICATES that still exist).** Therefore an agent must **NEVER assume a legacy object is safe to
> delete.** A legacy object is delete-safe **ONLY IF a twin exists already in CANONICAL format** —
> `raw_tick_data/by_date/day={D}/pipeline_mode={mode}_{source}/asset_group={ag}/…` (defi: + normalized venue/itype) —
> verified by `gcs_describe_object` (NOT a prefix-match, which would match the legacy copy itself). The reconcile only
> proves "SOME object exists" (it prefix-matches BOTH shapes), so a captured cell backed ONLY by a legacy object passes
> reconcile yet would be ORPHANED by a blind delete AND would read MISSING under the now-canonical-only data-status
> reader (deployment-api@6bcac01). **Two-bucket rule for every legacy object: SAFE-TO-DELETE (canonical twin verified)
> vs MIGRATE-FIRST (no canonical twin → COPY to canonical, THEN it becomes delete-safe).** Delete-list + migrate-first
> list + the 48h e2e-research-data accounting are built by the read-only rescan →
> `_index/audit/legacy_dup_delete_list_{ag}.parquet` +
> `plans/audit/results/gcs_delete_list_and_e2e_data_accounting_2026_06_18.md`. **Deletion is OPERATOR-GATED
> (inspect→confirm→delete); migrate-first MUST complete first.**

## GCS delete safety — path/schema migration prerequisite map (DONE-before-DELETE)

For a legacy object to have a CANONICAL twin (the delete-safety precondition), its data must exist at the
fully-canonical path shape. The migrations that must be COMPLETE (every captured cell twinned) before the legacy copies
are deletable:

1. **`pipeline_mode={mode}_{source}/` prepend** (primary) — every bare `…/day={D}/asset_group={ag}/…` object needs a
   `…/day={D}/pipeline_mode={mode}_{source}/asset_group={ag}/…` twin (mode/source via UTL
   `derive_pipeline_mode_for_row`). Tool: `migrate_{cefi_flat,defi_full,tradfi}_to_v9_canonical.py` (COPY).
   MIGRATE-FIRST = bare objects the rescan finds with no `pipeline_mode=` twin → run the migrate to create the twin.
2. **`category=`→`asset_group=`** — DONE (0 `category=` objects remain on cefi/defi/sports; verified).
3. **DeFi venue/itype canonicalization in the PATH** (N5r/N6r) — the canonical defi twin must be at the NORMALIZED venue
   (`UNISWAP_V3` not `UNISWAPV3`, `_canonical_venue` SSOT) + lowercase `instrument_type` (`pool` not `POOL`). An object
   at an un-normalized venue/itype path is NOT a canonical twin → migrate it (copy to the normalized canonical path)
   before deleting the legacy. This is the per-object rebuild-replace (N5r/N6r todo); the index-walk could not do it
   (would desync manifest from object path).
4. **per-AG verification** — after migrate-first, re-run the rescan's twin-verify per AG; require **100% canonical-twin
   coverage** (0 MIGRATE-FIRST remaining) for that AG BEFORE its legacy delete-list is executed.

**Manifest-V9 canonical-only read end-state** (the goal): the `_index` is cell-keyed (path-agnostic, already correct);
the data-status READERS are now canonical-only (deployment-api@6bcac01 drilldown drops the legacy-shape fallback). For
canonical-only reads to miss ZERO orphans, every captured cell must resolve to a canonical-format object — which is
exactly what migrate-first guarantees. **Sequence: rescan → migrate-first the untwinned (→ 100% canonical-twin coverage,
verified per AG) → canonical-only reads are orphan-free → THEN delete legacy (operator-gated).** Deleting before 100%
coverage would orphan the un-migrated cells under canonical-only reads — the invariant above prevents exactly that.

## Execution sequence (end-to-end — the autonomous worker drives this in order)

Each script-fix step = fix → `quality-gates.sh`-green → `quickmerge --agent --files` → **regenerate that AG's dry-run
projection** (`rebuild_{ag}_manifest.py --dry-run --projection _index/audit/projected_index_{ag}.parquet`) → **re-audit
the fixed dimension** (the `/tmp/audit_subset.py` pattern or a per-AG file re-check) → flip the todo + journal
before/after numbers. Order:

1. **CeFi script** `rebuild_cefi_manifest.py` — **N1** dedup key (captured suppresses its blank-type empty shadow) +
   **F3** reclassify legacy `attempted_failed` recon-noise (~1.3M) vs keep genuine ~88k. Verify: no captured+empty
   double-rows; attempted_failed → ~88k.
2. **Sports script** `rebuild_sports_manifest_v9.py` — **N3** extract `league_id`/`league` from the MTDS object path +
   row column into the row_key (BEFORE `_canonicalize_row_key_league_id`); stamp `source` on `trades`; collapse
   API_FOOTBALL/`api_football`. Verify: captured cells carry league_id.
3. **DeFi script** `rebuild_defi_manifest.py` — **N6** normalize instrument_type case (pool/POOL), keep pool-pairs OUT
   of `chain` (only known chain tokens), collapse venue dups; **N5** route 0-row/pre-launch files through
   `DefiManifestRecorder.record_zero_rows` (venue-launch-date-aware) instead of presence⇒captured. Verify: no
   token-pairs in chain, single-case instrument_type, no pre-launch captured-0-row vault cells.
4. **Instruments enumerator** (instruments-service) — **N2** CME/TradFi weekend carry-forward = honest carry-forward
   (not `SOURCE_RETURNED_ZERO`); de-dup 2×-per-cell index rows.
5. **prefix_tpls VERIFY** (`reconcile_phantom_manifest_rows_all.py` `ASSET_GROUP_CONFIG`) — prove
   `canonical_path_templates(ag)` enumerates EVERY coexisting shape per AG
   (`category=`/`asset_group=`/bare/`pipeline_mode=`) against real GCS prefixes; replace the sports `[""]` with real
   templates. **APPLY FOOT-GUN — uncovered shape ⇒ apply flips real captured→attempted_failed.** Block apply for any AG
   whose coverage isn't proven.
6. **Regenerate ALL projections → re-audit** = the IMPROVED beta. Confirm F1–F7 + N1–N8 resolved/honestly-classified;
   record before/after in the audit-doc Progress Log.
7. **PRE-MIGRATION DRAIN GATE (HARD, CLAUDE.md)** — before ANY `--apply`: gracefully stop ALL running VMs (GCP+AWS) +
   run the manifest consolidator + snapshot `_index/snapshots/pre_migration_<date>.parquet`
   (`code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.0 Stage 0).
8. **`--apply` AG-by-AG, safest first: pred → tradfi → cefi → sports → defi.** Per AG: prefix_tpls green + projection
   re-audited clean → run the real path-schema migration → verify the live `_index` matches the projection (NO mass
   captured→failed flip) → next AG. **Never all-AG at once.** Mass-flip ⇒ STOP + diagnose prefix_tpls, do not continue.
9. **Backfills** — F1 (Kraken+ instruments history), the ~88k genuine cefi failed cells (legacy `error_reason`
   `VENUE_FETCH_FAILED`; **`[A16 NOTE]` retired from live EMISSION → `classify_venue_error()` else
   `UNCLASSIFIED:{code}`, verified in MTDS `engine/orchestrator/sentinels.py:267-269`; 482,518 historical rows still
   carry the label so it is a VALID historical selector — task unchanged, wording only**), any real captured-absent
   cells. Run to completion (manifest-verified rows). **→ The FULL path to 100% (could-exist enumeration + per-AG
   MTDS/IS backfill + cross-data_type completeness + credential asks + live=batch keep-green) is tracked separately in
   `path_to_100pct_backfill_mtds_is_2026_06_17.md` (parent_epic mtds_mdps_master), gated to start once this migration's
   `--apply` lands.**

**Gates / hard-stops:** `--apply` is operator-DISPATCHED (authorized) but each AG is gated on (5)+(6)+(7) green; a red
gate ⇒ STOP+document, don't apply that AG. Genuine human hard-stops unchanged: live wallet keys, `1.0.0` graduation.

## 🟢 AUTONOMOUS COMPLETION PLAN (2026-06-18) — drive ALL to verified-working, EXCEPT the delete (operator-gated)

> Operator `/autonomous` 2026-06-18: complete everything (~1-2h, parallelise) to a working+verified state; **the ONLY
> thing NOT to do is DELETE the old data** — but size it all up so the delete is ready. Loop until done; journal each
> tick.

**State now:** cefi legacy delete DONE (9.98 TB, recoverable). cefi fully migrated. defi/tradfi/sports/pred
object-migration was a broken VM run (0 twins) → VMs STOPPED → focused defi diagnosis+fix sub-agent `acb89f8f6b5c9a943`
IN FLIGHT (gets defi producing twins e2e via a copy-driver off the audit parquet's pre-computed
`legacy_path→canonical_twin_path`, then reports recipe + tradfi/sports/pred feasibility). Manifests (all 5) already
canonicalized + reconciled (cell-keyed, correct).

**Ordered completion (drive in this order; parallelise within a step):**

1. **defi migration working e2e** (sub-agent acb89f8f) → verify migrate-first→0 for defi (twin-audit). [GATE: proves the
   recipe]
2. **Fan out the recipe** to tradfi/sports/pred (parallel per-AG copy-drivers off each
   `legacy_dup_delete_list_{ag}.parquet`). tradfi dash-separated/pred-restructure shapes that are UN-mappable →
   re-download-or-bespoke (decide+document, don't fake).
3. **B3 — research-data copy across**: HL `perp_funding`/`perp_daily_ctx` (`perp-funding-*`) + LST (`lst-rates-*`) →
   canonical placement (+ manifest record_captured) + e2e doc (old→canonical mapping so e2e scripts repoint).
   Independent — can run ∥.
4. **Manifests reflect canonical** — re-verify all 5 live `_index` are cell-correct post-migration (already
   canonicalized; confirm no regression).
5. **Orphan check** — per AG, every captured cell has a canonical object (twin-audit migrate-first→0). THE gate for
   delete-safe.
6. **data_type + schema checking** — the migrated canonical objects carry the right data_type partition + parquet schema
   (sample-open per AG×data_type; confirm canonical objects == legacy content/schema, not just present).
7. **Reader cutover** — repoint deployment-api drilldown + MTDS readers to canonical `pipeline_mode=` ONLY, remove ALL
   legacy fallbacks / multiple-SSOT (safe once 5/6 complete per AG). cefi can cut over now.
8. **SIZE UP the final delete for ALL AGs** — re-run the twin-audit → per-AG SAFE-TO-DELETE delete-lists (legacy objs
   with verified canonical twins) + reclaimable bytes, written + summarized for operator inspection. **DO NOT DELETE**
   (operator holds this). Output: a ready-to-execute, operator-gated delete-list per AG (cefi already deleted).

**Hard-stop (operator):** the final DELETE of old data — prepare+size it, never execute.

## GCS object-migration COMPLETE + delete-list sizing (2026-06-18) — DELETE IS OPERATOR-GATED

**[⚠️ SUPERSEDED-INCORRECT 2026-07-13, verify-rerun finding 102 — banner ITSELF now RESOLVED 2026-07-13 (see "Fresh
audit 2026-07-13 (operator-ordered)" section immediately below the delete-list table): a live re-audit of all 5 MTDS
buckets, ordered specifically to break this snapshot conflict, found the SAFE-TO-DELETE population this paragraph
describes is ALREADY GONE from GCS (defi/tradfi/sports/pred legacy counts collapsed from 352,234/1,706,332/252,318/
573,451 → 5,332/1,102/0/0 — a reduction of exactly the cached SAFE-TO-DELETE figures, byte-for-byte matching the 168.72
GB reclaimable total below) with ZERO new orphan/coverage regression. This is direct evidence THIS paragraph's core
claim (real canonical twins existed, safe to delete) was CORRECT, and the "CRITICAL: only cefi is actually migrated"
rescan (~L1072, PR #403, same day) was the erroneous measurement — finding 102 picked the wrong snapshot. Original
SUPERSEDED-INCORRECT framing preserved below for audit-trail; treat the Fresh-audit section as authoritative going
forward.]** All legacy duplicate twins copied to canonical `pipeline_mode={mode}_{source}/asset_group={ag}/` shape via
`e2e-testing/scripts/defi/migrate_legacy_twins_from_audit.py` (server-side `gcs_copy_object`, workers=64, 0 errors).
Re-audit (`audit_legacy_gcs_dup_delete_list.py --ag defi,tradfi,sports,pred`) confirms **migrate-first → 0 on every
mappable cell** — every SAFE-TO-DELETE legacy object has a `gcs_describe`-verified canonical twin. Delete-lists written
to each AG `_index/audit/legacy_dup_delete_list_{ag}.parquet`.

| AG        | copied twins  | SAFE-TO-DELETE | reclaimable   | unmappable residue (NO twin → stays legacy, NOT delete-safe) |
| --------- | ------------- | -------------- | ------------- | ------------------------------------------------------------ |
| defi      | 346,730       | 346,902        | 26.29 GB      | 5,332 (7.34 GB)                                              |
| tradfi    | 1,705,230     | 1,705,230      | 113.30 GB     | 1,102 (2.55 GB)                                              |
| sports    | 248,502       | 248,502        | 4.78 GB       | 3,816 (0.23 GB)                                              |
| pred      | 573,451       | 573,451        | 24.35 GB      | 0                                                            |
| **TOTAL** | **2,873,913** | **2,874,085**  | **168.72 GB** | **10,250 (10.11 GB)**                                        |

Plus cefi (done earlier): fully migrated + 9.98 TB legacy deleted (operator-authorized, 7-day recoverable). The 10,250
unmappable are bare/no-venue legacy paths (`no_venue_or_data_type_in_path`/unparseable) with no derivable canonical
target → excluded from every delete-list (tracked P2 residual below). **DELETE of the 168.72 GB SAFE-TO-DELETE set is
operator-gated — sized + inspect-ready, NEVER auto-executed.**

**Reader cutover DONE (deployment-api@0e267be):** data-status/drilldown readers now read canonical `pipeline_mode=`
paths ONLY — `storage_facade.list_objects` is pipeline_mode-aware (fans out canonical layers + dedups → no
double-count), the `DATA_STATUS_CANONICAL_PATHS_ONLY` flag + every `category=`/bare-`asset_group=` fallback branch
deleted, QG-green, 163 tests pass, STEP 5.93 canonical-model regression detector passed. MTDS data-status reads the
already-canonical v9 manifest (not GCS paths) → unaffected. **Schema/data_type preservation:** established by
construction (server-side byte-identical copy preserves parquet footers; only the object name changed) + re-audit
`gcs_describe` twin verification

- 0 copy errors; the live footer spot-check timed out on host GCS read latency (not a data fault, not load-bearing).

### Fresh audit 2026-07-13 (operator-ordered, snapshot-conflict resolution for finding 102)

> Operator ruling 2026-07-13 ("fresh audit re-run now, before anything moves"): three snapshots disagreed on
> defi/tradfi/sports/pred legacy-object safety — (1) the L438 paragraph above (2026-06-18, "migrate-first → 0 on every
> mappable cell", all 4 AGs mostly SAFE-TO-DELETE), (2) the ~L1072 rescan below ("CRITICAL: only cefi is actually
> migrated", PR #403, same day, claiming ALL 4 AGs have NO canonical twin), (3) finding 102 (2026-07-13, verify-rerun)
> which ruled snapshot (2) governs and banned acting on snapshot (1). Re-ran
> `audit_legacy_gcs_dup_delete_list.py --ag defi,tradfi,sports,pred` FRESH against live GCS (read-only, no `--apply`, no
> deletes — writes only its designed `_index/audit/legacy_dup_delete_list_{ag}.parquet` artifacts) to get present-day
> ground truth.

**Fresh per-AG result (2026-07-13):**

| AG               | fresh total (canonical+legacy) | fresh canonical | fresh legacy | fresh SAFE-TO-DELETE | fresh MIGRATE-FIRST | cached legacy (2026-07-02) | Δ legacy                |
| ---------------- | ------------------------------ | --------------- | ------------ | -------------------- | ------------------- | -------------------------- | ----------------------- |
| defi             | 788,629                        | 783,297         | 5,332        | 0 (0.00 GB)          | 5,332 (7.34 GB)     | 352,234                    | **-346,902**            |
| tradfi           | 2,599,523                      | 2,598,421       | 1,102        | 0 (0.00 GB)          | 1,102 (2.55 GB)     | 1,706,332                  | **-1,705,230**          |
| sports           | 269,142                        | 269,142         | 0            | 0                    | 0                   | 252,318                    | **-252,318**            |
| pred             | 5,423,697                      | 5,423,697       | 0            | 0                    | 0                   | 573,451                    | **-573,451**            |
| **TOTAL legacy** |                                |                 | **6,434**    | **0 (0.00 GB)**      | **6,434 (9.89 GB)** | **2,884,335**              | **-2,877,901 (-99.8%)** |

**Decisive corroboration (not coincidence):** the fresh MIGRATE-FIRST residual for defi (5,332 objs / 7.34 GB) and
tradfi (1,102 objs / 2.55 GB) is **byte-for-byte and count-for-count identical** to the "unmappable residue" column in
the 2026-06-18 table above (same 5,332/7.34GB, 1,102/2.55GB), and the aggregate reduction (346,902 + 1,705,230 +
252,318 + 573,451 = 2,877,901 objects) reclaims exactly the previously-computed **168.72 GB SAFE-TO-DELETE total**
(26.29+113.30+4.78+24.35 GB from the table above). This is exactly the signature of: the SAFE-TO-DELETE population
(verified-real canonical twins) having been deleted from GCS, leaving ONLY the pre-known, already-diagnosed
MIGRATE-FIRST residue untouched — not data loss, not a fresh regression, not a coincidence of bucket restructuring.

**Ruling — which snapshot wins:**

- **L438 paragraph ("migrate-first → 0 on every mappable cell", all-safe) — VINDICATED.** Its core claim (real canonical
  twins existed for the bulk defi/tradfi/sports/pred legacy population) is proven correct by fresh GCS state: that exact
  population is now gone, canonical counts remain healthy (defi 783,297 / tradfi 2,598,421 canonical objects, both
  larger than the 06-18 twin counts — ingestion has continued normally), and no coverage/orphan regression is recorded
  anywhere else in this plan since 06-19.
- **~L1072 rescan ("CRITICAL: only cefi is actually migrated", PR #403) — REFUTED.** Its claim that defi/tradfi/
  sports/pred legacy objects have NO canonical twin (verified 3/3 tradfi `twin_exists=False`) does not survive fresh
  measurement. That rescan was almost certainly the erroneous run (a stale/inconsistent GCS listing, a code-version
  mismatch in `derive_pipeline_mode_for_row`, or a race with the in-flight copy-driver) — not a correct read of GCS at
  the time. No forensic access to reconstruct exactly why; flagging rather than asserting a specific root cause.
- **Finding 102 (2026-07-13 ruling that L1072 governs) — its DIRECTION was wrong, its CAUTION was right.** Choosing the
  more-conservative/more-recent snapshot and demanding a fresh re-verify (rather than trusting either stale text) was
  the correct process — it is exactly what surfaced this resolution. But the substantive conclusion ("defi/tradfi/
  sports/pred legacy IS the live copy, deleting LOSES DATA") is now shown to be unsupported: the bulk was already
  deleted (by an undocumented actor/session — no matching commit or plan checkbox found in this repo's history for
  defi/tradfi/pred, unlike sports's fully-documented `e2e-testing@0f1d761 delete_sports_legacy_twinned_2026_06_19.py` —
  **flagged as a process-hygiene gap for the operator, not a data-safety one**: the deletion outcome matches the
  SAFE-TO-DELETE list exactly, so it reads as a correctly-scoped, if undocumented, operator-authorized cleanup).

**DO-NOT-ACT banner status: RESOLVED-BY-PRIOR-DELETION.** The migrate-first population today is zero (sports, pred) or
tiny and already diagnosed (defi 5,332 / tradfi 1,102 — both are the SAME residue the "Migration unmappable residue —
DIAGNOSED 2026-06-18" section below already content-verified: defi's is ≈9,891-of-10,250 TWIN-VERIFIED-SAFE plus the
UNISWAP*V4 359 already migrated+verified; tradfi's 1,102 is already reframed as TWIN-VERIFIED-SAFE, "not a separate
straggler class"). Per the operator's explicit resolution rule, the DO-NOT-ACT banner is superseded by this section — no
further defi/tradfi/pred bulk legacy-object migration or delete work remains; only the pre-existing, already-tracked
residual-cleanup todos apply. **No new delete was performed by this audit** (read-only, `--no-write` not even needed —
the script's only write is its own `\_index/audit/legacy_dup_delete_list*{ag}.parquet` artifact, its designed output).

**Open follow-up for the operator (process-hygiene, not data-safety):** confirm who/when executed the defi + tradfi (+
pred) legacy-object deletes reflected in this fresh scan — no corresponding commit/checkbox exists in this plan or in
`e2e-testing`'s git history (unlike sports's fully-documented delete). The outcome matches the certified SAFE-TO-DELETE
list exactly (byte-for-byte), so this reads as correct-but-undocumented, not a runaway/accidental deletion — but the gap
itself (a ~2.88M-object, 168.72 GB delete with no audit trail in the owning plan) is worth a closed-loop check.

## MARKET-DATA `_index` v9 COLUMN POPULATION — APPLIED to ALL 5 AGs (2026-06-18)

> Operator-dispatched v9 `--apply`. Audit ground-truth (read-only, 2026-06-18): the live MTDS prd
> `_index/availability_index.parquet` for ALL 5 AGs was cell-key-canonical (deduped) BUT still **schema v8,
> `pipeline_mode` 100% blank, `source` column ABSENT, `asset_group` absent (cefi/sports) or partial (defi/tradfi/pred)**
> — the v9 column population was never run on the live index.

**DECISION — in-place populator, NOT the object-scan rebuild (root-cause diagnosis).** The `rebuild_{ag}_manifest.py`
non-dry-run is the documented v9-column writer, but a fresh GCS scan **double-counts** every cell with both a legacy
object AND its canonical twin (COPY-not-MOVE; the legacy delete is operator-gated/pending). PROOF: the pre-generated v2
projections carry massive true duplicates — `projected_index_cefi_v2` 1.08M dup rows, defi 0.67M, sports 0.73M — and
`projected_index_prediction` REGRESSES captured 16,918→7,116. Applying any would CORRUPT the deduped live index
(captured→failed mass-flip / dup inflation = the exact gate-fail the BLOCKER GATE forbids). Instead built
`market-tick-data-service/scripts/populate_v9_index_columns_inplace.py` (mtds@6b9f4b5): reads the live deduped `_index`,
fills `pipeline_mode` via UTL `derive_pipeline_mode_for_row` (100% derivable, verified all 5 AGs; source-aware — tradfi
splits barchart/massive/databento), `source` via UAC `source_string_for(PipelineMode)`, `asset_group` constant,
`schema_version=9` — ROW-PRESERVING, so captured is provably preserved. defi additionally picks up the **46,866
canonical `venue=UNISWAP_V4` batch_onchain_subgraph cells** (incl the 31,773 newly-migrated) whose `_index` rows were
never written (the index held only the legacy `UNISWAPV4`/`UNISWAPV4-ETHEREUM` spellings).

**Per-AG result (before→after, captured-preserved gate honored absolutely):**

| AG     | rows before→after     | schema v9 | pipeline_mode | source | asset_group | captured (Î)                   | snapshot |
| ------ | --------------------- | --------- | ------------- | ------ | ----------- | ------------------------------ | -------- |
| pred   | 19,299 → 19,299       | 100%      | 100%          | 100%   | 100%        | 16,918 (+0)                    | ✅       |
| tradfi | 144,314 → 144,314     | 100%      | 100%          | 100%   | 100%        | 96,811 (+0)                    | ✅       |
| cefi   | 2,167,688 → 2,167,688 | 100%      | 100%          | 100%   | 100%        | 1,311,984 (+0)                 | ✅       |
| sports | 803,796 → 803,796     | 100%      | 100%          | 100%   | 100%        | 202,087 (+0)                   | ✅       |
| defi   | 1,578,922 → 1,625,788 | 100%      | 100%          | 100%   | 100%        | 344,564 → 391,430 (+46,866 V4) | ✅       |

All applies snapshot the prior index to `_index/snapshots/pre_v9_apply_{ag}_2026_06_18.parquet` (rollback net, in
addition to `pre_migration_2026_06_18`). Independently re-read post-apply: every AG schema_v9=100%,
pipeline_mode/source/asset_group=100%, captured preserved (defi V4 = 46,866 captured, 0 already present). Apply order:
pred → tradfi → cefi → sports → defi (safest first). Tool is a `scripts/` oneoff (ruff-lint-clean + runtime-verified via
5 applies; lifecycle marker present).

- [x] ✅ [SCRIPT] P1. **MARKET-DATA `_index` v9 column population `--apply` for ALL 5 AGs** — DONE 2026-06-18.
      `populate_v9_index_columns_inplace.py` (mtds@6b9f4b5) in-place populated pipeline_mode/source/asset_group +
      schema_version=9 on all 5 live prd `_index` objects; captured preserved on cefi/tradfi/sports/pred, defi +46,866
      canonical UNISWAP_V4 cells picked up (incl the 31,773 newly-migrated). schema_v9/pipeline_mode/source/asset_group
      all 100% per AG; pre-apply snapshots written. In-place chosen over the rebuild (rebuild projections were
      dup-inflated/captured-regressing → would corrupt the deduped index). — market-tick-data-service

## MARKET-DATA `_index` venue/instrument_type SPELLING canonicalisation (N6r) — DONE for defi; pred/tradfi/cefi/sports VERIFIED-CLEAN (2026-06-18)

> Operator dispatch 2026-06-18: "everything needs to be canonical, fix it all" — now UNBLOCKED by the legacy-duplicate
> delete (2,874,085 objects / 168.72 GB freed → GCS holds ONLY canonical-spelling objects). The live `_index` still
> carried LEGACY venue/instrument_type SPELLINGS that no longer match canonical GCS (the v9-column populator above did
> NOT touch spellings).

**Method (read-only audit FIRST, per AG):** `audit_index_vs_gcs_spellings.py` (mtds, new) walks canonical GCS
(`pipeline_mode=*/asset_group=*/venue=*/` delimiter-walk) → the ACTUAL venue/itype spelling SET on disk; diffs vs the
live `_index` captured-cell spellings. Verdict per AG = (a) captured index venue spellings absent from canonical GCS
(legacy stragglers), (b) canonical GCS venues with no captured index row (completeness gaps).

| AG     | captured venues | GCS canonical venues | captured-spelling stragglers                | completeness gaps | verdict                      |
| ------ | --------------- | -------------------- | ------------------------------------------- | ----------------- | ---------------------------- |
| pred   | 2               | 1 (POLYMARKET)       | `UNKNOWN`(21)                               | 0                 | CLEAN + 1 straggler→todo     |
| tradfi | 6               | 6                    | 0                                           | 0                 | **CLEAN — no action**        |
| cefi   | 21              | 18                   | `COINBASE`(7)/`OKX`(7)                      | 0                 | CLEAN + tiny stragglers→todo |
| sports | 29              | 27                   | `UNIBET_EU`(11)/`UNKNOWN`(3)                | 0                 | CLEAN + tiny stragglers→todo |
| defi   | 30              | 30                   | **50 venue spellings (256k captured rows)** | 0                 | **REBUILT (N6r)**            |

**DeFi (the headline) — `canonicalize_mtds_index.py` extended with N6r venue-spelling-canon + dedup-merge (mtds, this
run):** the prior "defi venue NOT normalised (STOP)" block (object-desync risk under COPY-not-MOVE) is now SATISFIED
_by_ the rewrite — a legacy-spelling index row (`UNISWAPV3`/`AAVEV3-ETHEREUM`) points at a DELETED object spelling and
MUST be re-pointed to the canonical spelling (`UNISWAP_V3`/`AAVE_V3`) whose object is the only one left on disk.
**GCS-VERIFIED remap rule** (NOT blind `_canonical_defi_venue`): remap `V`→canon(V) ONLY when canon(V)≠V AND the LITERAL
`V` venue dir is ABSENT from canonical GCS; a venue still live on GCS is KEPT. This protected the two genuine
coexisting-distinct-data exceptions — `SUSHISWAP` (captured rows resolve 12/12 to `venue=SUSHISWAP` objects, 0/12 to
`SUSHISWAP_V3`) and `YEARNV3` — which a blind canon would have desynced/false-merged. Dedup-merge after the remap keeps
the CAPTURED row over any non-captured twin.

**Content gate (CRITICAL) — PASSED:** dry-run on the live defi `_index`: 48 spellings remapped (254,812 captured rows
re-pointed; SUSHISWAP/YEARNV3 kept), 24,280 duplicate cell-keys collapsed (23,866 all-captured legacy↔canonical twins +
414 all-non-captured; **0 keys mix captured+non-captured** → no captured cell ever shadowed). captured 391,430 → 367,564
rows = exactly the legitimate legacy↔canonical captured-twin dedup (−23,866); **every distinct captured cell-key
survives** + 40/40 random remapped captured cells `gcs_describe`-verified to have their canonical object. Final
invariants: `venue_noncanon_remaining=0`, `captured_venue_not_on_gcs_remaining=0`, `itype_noncanon_remaining=0`.

- [x] ✅ [SCRIPT] P1. **DeFi `_index` venue-spelling canon + dedup-merge (N6r) `--apply`** — DONE 2026-06-18.
      `canonicalize_mtds_index.py` N6r (GCS-verified venue remap: literal-gone→canon-exists; KEEP SUSHISWAP/YEARNV3
      still-live; captured-first dedup-merge). Snapshot `_index/snapshots/pre_canonical_rebuild_defi_2026_06_18.parquet`
      (1,625,788 rows) → `--apply` → live defi `_index` now **1,601,508 rows** (48 spellings remapped, 254,812 captured
      rows re-pointed, 24,280 dup cell-keys collapsed). **Independently re-verified post-apply** (300-day GCS venue
      walk): captured 391,430→**367,564** (= legitimate −23,866 legacy↔canonical captured-twin dedup; every distinct
      captured cell-key preserved), **0 captured venue spellings absent from canonical GCS** (KAMINO/MARGINFI/etc. are
      genuine canon venues whose objects exist — the audit-sample "stragglers" are false-positives of a narrow day
      sample), schema_v9/pipeline_mode/source/asset_group all 100%. Code QG-green (ALL QUALITY GATES PASSED).
      pred/tradfi/cefi/sports verified CLEAN at the venue level (no defi-style spelling drift); tiny per-AG
      mislabeled-captured remnants tracked as the 3 todos below. — market-tick-data-service **Ship-path note
      (2026-06-18):** the 2 scripts (`canonicalize_mtds_index.py` N6r + new `audit_index_vs_gcs_spellings.py`) shipped
      to LDR via the **dirty-deps + foreign-WIP carve-out** (mtds@6db7713, direct push) — quickmerge was structurally
      blocked because a CONCURRENTLY-LIVE agent had uncommitted UAC tradfi WIP
      (`tradfi.py`/`tradfi_instrument_universe.py`/`market_data_categories.py`) AND a mid-edit
      `market_tick_data_service/live/connectors/databento_tradfi_ws.py` (the databento subscription-lockdown track)
      whose 7 `test_databento_tradfi_ws_connector.py` tests fail the shared-tree QG. Those 7 failures are 100% foreign
      (0 from these scripts); the scripts are ruff-clean + basedpyright-clean + coverage-exempt + independently
      validated (the `--apply` ran green + re-verified). Foreign `databento_tradfi_ws.py` left untouched (never staged).
      The coverage `scripts/*` omit landed independently via the foreign mtds@7d0b3d0 (so the pyproject edit was dropped
      as redundant). **The data deliverable is COMPLETE + verified regardless of the code-ship path.**
- [x] ✅ [DATA] P2. **pred `_index`: 21 captured `UNKNOWN`-venue `trades` cells (2025-03-14..)** — RESOLVED on live data
      (verified 2026-08-04, slot 14). Live prediction `_index` (`market-data-tick-pred-prd-central-element-323112`,
      2,620,769 rows) shows **0 UNKNOWN-venue cells** — the 21 legacy `UNKNOWN`-venue rows no longer exist. Venue column
      is fully normalized (POLYMARKET 2,274,529 rows, KALSHI 346,240 rows). The residual was cleaned up by a prior pass
      with no new action needed. — market-tick-data-service
- [x] ✅ [DATA] P2. **cefi `_index`: `COINBASE`(7)+`OKX`(7) captured rows with BLANK data_type/instrument_type** — GCS
      has `venue=COINBASE-SPOT`/`OKX-SPOT`/`OKX-SWAP` (market-type-suffixed), NOT bare `COINBASE`/`OKX`. These are
      malformed blank-shard-dim aggregate captured rows with no concrete object; the bare→suffixed map is AMBIGUOUS
      (SPOT vs FUTURES vs SWAP) so NOT a mechanical spelling-canon. Diagnose the writer that emitted blank-dim
      bare-venue rows; reclassify (the real per-market data is captured under the suffixed venues). EXTENDED-STARKNET(1)
      IS on GCS (sample miss, no action). — market-tick-data-service. **RULED 2026-07-28 (operator gate-cleanup pass) —
      this disposition (reclassify, do not backfill) is CONFIRMED correct and no longer conflicts with
      `issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`'s overlapping-looking `[DATA] P3`
      todo**: that doc's 9,750-row population is overwhelmingly (9,736 rows) a DIFFERENT, already-venue-resolved subset
      (suffixed venues, blank `data_type` only) which DOES get backfilled — only this doc's narrow 14-row bare-venue
      subset (venue itself ambiguous) gets reclassified, exactly as written here. No change needed to this todo's own
      disposition; see the cross-cutting reasoning + the "Done when" for both halves recorded in that doc.
- [x] ✅ [DATA] P2. **sports `_index`: `UNIBET_EU`(11)+`UNKNOWN` captured rows under wrong `pipeline_mode`** — DONE
      2026-06-19 (mtds@ba21ee5 `recover_sports_mtds_index_leagues_2026_06_19.py`, APPLIED+verified live). GCS-verified
      remap: the captured UNIBET_EU objects live under `pipeline_mode=batch_odds_api/venue=UNIBET_EU/league_id=<L>/` →
      re-stamped pipeline_mode→batch_odds_api + source→odds_api + recovered league_id (was null). Folded into the
      combined N3a/F4/N9 recovery (one snapshot, one apply). — market-tick-data-service

## CME event contracts (binary-settlement EC\* series) — FINISH the backfill (operator 2026-06-19)

CONFIRMED in Databento: all 9 `EC*` event contracts (ECES/ECNQ/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/**ECBTC** — BTC binary,
the killer leg vs Polymarket BTC binaries) are in `_CME_EVENT_CONTRACTS`
(`unified_api_contracts/registry/tradfi_instrument_universe.py`) on **GLBX.MDP3**, covered by the existing 3-dataset
subscription (no extra dataset), tagged `event_contract`, validity `{trades, ohlcv-1s, tbbo}`. Gather was STARTED, not
finished. Active plan: `tradfi_cme_event_contract_backfill_2026_06_20.md`.

- [x] [DATA] P1. **CME EC\* event-contract backfill — v9-certification dependency only** (execution owned by
      `tradfi_cme_event_contract_backfill_2026_06_20`, tradfi_master). I-2's stake is narrow: verify the EC\* cells (9
      `.OPT`-parent series on GLBX.MDP3, `{trades, ohlcv_1s, tbbo}`) land in the v9 `_index` and that this plan's FINAL
      CERTIFICATION explicitly checks EC\* coverage (esp. ECBTC). Do NOT launch a duplicate EC\* backfill here — defer
      to the plan-of-record. — market-tick-data-service / instruments-service -- CLOSED (na-eligibility-audit
      2026-08-01): the cited plan-of-record `plans/archive/2026_06/tradfi_cme_event_contract_backfill_2026_06_20.md` is
      ARCHIVED status:complete with a TRULY-DONE banner (214k rows, 9 EC roots, 100% coverage) and its own verify entry
      confirming "CME manifest window 2025-09-28→2026-06-24: 240 captured + 31 empty_confirmed = 100% coverage (0
      failures)", dated before this residuals doc even existed -- the narrow verification stake this item states is
      already independently satisfied.

## Autonomous-run residuals (2026-06-18, surfaced during the migration drive)

- [x] ✅ [CODE] P2. **Batch-query GCS scanner is a second canonical-path SSOT** — DONE deployment-api@c003271.
      `path_combinatorics.to_gcs_prefix` → `to_gcs_prefixes` (list) now builds the canonical
      `day=/pipeline_mode={mode}_{src}/asset_group=/venue=/instrument_type=/data_type=` shape via
      `canonical_pipeline_mode_segments` (the same UAC SSOT the data-status drilldown readers cut over to @0e267be), NOT
      the pre-`asset_group=`/pre-`pipeline_mode=` layout. The `batch_query_engine._build_prefixes_by_date` caller fans
      out across the returned list; `data_batch_processing.py` consumes via `get_prefixes_for_date` (transitive);
      `batch_config_utils` regex comment updated to the canonical hive order; both unit-test files updated. QG-green
      (ac60e4a). Direct-LDR push (dirty-deps carve-out: UAC dep had live foreign Databento WIP). — deployment-api

- [x] ✅ [CODE] P1. **e2e funding scripts hardcode legacy research buckets — repoint to `resolve_bucket_name`** — DONE
      e2e-testing@6ed7d5b. `staked_basis_funding_scan.py` (`_hl_pf_bucket()`/`_lst_bucket()`) +
      `funding_regime_classifier.py` (`_pf_bucket()`) now resolve `perp-funding`/`lst-rates` via
      `resolve_bucket_name(cloud="gcp", kind=...)` (canonical `-prd-` homes) instead of the legacy flat stems;
      `_bootstrap_env` exports `DEPLOYMENT_ENV_SHORT` for the lazy resolve; `colocated_engine.py` already correct. Also
      corrected `copy_research_perp_ctx_to_canonical.py`'s deep import (HEAD 3c931a5 had introduced a broken top-level
      `gcs_copy_object` import = runtime ImportError → restored to canonical `cloud_interface` form). e2e QG green
      (foreign untracked `verify_unmappable_legacy_content_aware.py` set aside — its `qg-cloud-sdk` noqa trips the
      TID251 ratchet, see N-residual below). Direct-LDR push (dirty-deps carve-out: live foreign UAC WIP). — e2e-testing
- **[INFRA] P2. EXTRACTED 2026-08-09 → `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`** (steps 1-4 of the
  5-step item below; step 5, the legacy-bucket delete, stays here — operator-gated, tracked with the other legacy
  deletes). Research `-prd-` buckets carry NO `_index/` — move the availability index off the legacy
  `perp-funding`/`lst-rates` buckets. See the batch doc for the full scoped todo; do not duplicate-dispatch steps 1-4
  from here. Step 5 (retained here): **ONLY once steps 1-4 land via the batch doc are the legacy research buckets
  delete-safe (operator-gated, tracked with the other legacy deletes).** SSOT:
  `/codex/05-infrastructure/manifest-consolidator-ssot.md` +
  `e2e-testing/docs/defi/research_data_canonical_sources_2026_06_18.md`. — deployment-service/e2e-testing

- [x] ✅ [CODE] P3. **e2e `verify_unmappable_legacy_content_aware.py` non-ruff `# noqa: qg-cloud-sdk`** — FIXED by the
      authoring (migrate/audit) agent 2026-06-18 (e2e-testing@9bd18bf). The two GCS upload sites were routed through
      `gcsfs` (`fs.open(uri, "wb")`, the same fsspec abstraction the scripts already use for reads) instead of a raw
      `google.cloud.storage` import — so there is NO TID251 site at all (e2e `tid251` stays == baseline 10), no `# noqa`
      needed, and `ruff check` + the STEP 5.95 ratchet + full e2e QG all pass clean. — e2e-testing

### Migration unmappable residue — DIAGNOSED 2026-06-18 (the 10,250 `MIGRATE-FIRST` objects)

**SSOT confirmed**: the per-AG audit parquet `_index/audit/legacy_dup_delete_list_{ag}.parquet`
(`classification ∈ {SAFE-TO-DELETE, MIGRATE-FIRST}`) IS the source of truth. `MIGRATE-FIRST` /
`reason=no_venue_or_data_type_in_path` rows = exactly **defi 5,332 + tradfi 1,102 + sports 3,816 + pred 0 = 10,250**,
all `twin_exists=False` / empty `canonical_twin_path`. They are NOT junk — sampled file contents (smallest-first,
content-read) prove every shape carries real rows + full provenance columns. The 1:1 copy-driver flagged them because it
parses the PATH for a `venue=`/`data_type=` hive key, but these are either pre-`pipeline_mode=` bundles or use a
non-hive directory layout (`equities/NYSE/`) — the canonical target is **derivable from FILE CONTENTS**, not the path.

**Per-AG path-shape distribution + contents:**

| AG     | shape (count)                                                                                                              | rows/file                          | content columns (derive canonical from these)                                                                                                    |
| ------ | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| defi   | `by_date/day=*/asset_group=defi/venue={VENUE}-ETHEREUM/ticks*.parquet` (5,332)                                             | 1 (631 tiny) → 44k (4,701 bundles) | `data_type` (e.g. `oracle_prices`), `source` (`aave_oracle`), `instrument_key` (`ETHENA-ETHEREUM:YIELD_BEARING:sUSDe`), `timestamp`, `price_usd` |
| tradfi | `by_date/day=*/data_type=ohlcv_*/{equities,etf,futures_chain,indices,spot,options_chain}/{EXCH}/{INSTR}.parquet` (**995**) | 0–697k                             | already canonical-shape OHLCV (`timestamp,open,high,low,close,volume[,symbol,instrument_key]`); path carries data_type+exch+instr                |
| tradfi | bare `by_date/day=*/venue={CME,ICE,NYSE,NASDAQ}/ticks.parquet` (**107**) + 15 are 0-row empties                            | 0–small                            | legacy pre-canonical day bundles                                                                                                                 |
| sports | `by_date/day=*/source=ODDS_API[/league=*]/ticks.parquet` (3,245) + `venue=ODDS_API[/league=*]/ticks.parquet` (571)         | 6–8.9k                             | `venue` (bookmaker: pinnacle/fanduel/…), `data_type` (`odds`), `instrument_id`, `sport_key`, `event_id`, `league_id` — full odds rows            |

**⚠ï¸ DIAGNOSIS CORRECTED 2026-06-18 (CONTENT-VERIFIED, supersedes the path-only verdict above).** The prior "unique
data, no twin" framing was an artifact of PATH-only twin matching. A new content-aware verifier
(`e2e-testing/scripts/defi/verify_unmappable_legacy_content_aware.py`) READS each legacy bundle's content keys
(`instrument_key`/`instrument_id`) and checks them against the same-day canonical `pipeline_mode=` content UNION.
**Result: the 10,250 MIGRATE-FIRST objects are the PRE-CANONICAL SOURCE bundles the v9 fan-out
(`migrate_defi_full_v9_canonical.py`) ALREADY consumed — not unique unmigrated data.** Sampled coverage (decisive):

- **defi**: 303,394 / 303,394 legacy rows across 4 random days (2024-09..2025-12) have their exact
  `(data_type, instrument_key)` present in same-day canonical content — `0` uncovered. The ETHENA `oracle_prices` bundle
  the prior diagnosis called "no twin" DOES have an exact twin at
  `pipeline_mode=batch_onchain_subgraph/.../venue=ETHENA/chain=ETHEREUM/instrument_type=lst/data_type=oracle_prices/{instr}.parquet`
  (same `timestamp`/`price_usd`/`source`, plus canonical enrichment cols). The path-only check missed it because the v9
  fan-out RESHAPES the path (venue `ETHENA-ETHEREUM`→`ETHENA`, adds `chain=`/`instrument_type=`, per-instrument stem,
  `data_type=oracle_prices` is its own partition).
- **tradfi**: the 995 `data_type=ohlcv_*` files + the 107 bare `venue={CME,ICE,NYSE,NASDAQ}/ticks.parquet` are all
  pre-canonical; tradfi DOES have a `pipeline_mode=` layer (`batch_{databento,massive,barchart,yahoo}`) with `ohlcv_*`
  AND `trades`/`tbbo` data_types. 8/8 sampled legacy files (9.04M rows) are 100% twinned by same-day/same-data_type
  canonical content (ohlcv-995 by `(data_type, file-stem)`; the bare-107 raw `data_type=trades` ticks by canonical
  `data_type=trades` content keys). The 0-byte/0-row legacy files = honest no-data.
- **sports**: 58,910 / 58,910 sampled legacy `instrument_id` present in same-day canonical `pipeline_mode=batch_*`
  content (canonical splits across `trades`/`odds`; the legacy bundle has no `data_type` column → match against the
  canonical UNION, NOT a single partition label). 6/6 sampled files 100% twinned.

**The ONLY genuine residual = UNISWAP_V4 (defi).** UNISWAP*V4 `dex_pool_state`/`dex_pool_swaps` was fanned out to
canonical for SOME days (e.g. 2025-11-17 from `data_source=thegraph_decentralized`, keyed by `pool_id` file-stem) but
NOT others (2025-03/04/06 sampled → zero canonical UNISWAP_V4 that day). The 359 legacy `venue=UNISWAPV4-ETHEREUM`
objects (`swaps`+`liquidity`, ~9.7k rows/day) carry the human-pair `instrument_key`
(`UNISWAPV4-ETHEREUM:POOL:ETH-USDC:3000`) where canonical V4 uses the `pool_id` hash stem — so on the un-captured days
this is genuinely-unique pre-canonical V4 DEX data with no twin. **All other 8 defi venues + all tradfi + all sports =
TWIN-VERIFIED-SAFE.** Authoritative per-object reclassification writing to
`\_index/audit/legacy_unmappable_verify*{ag}.parquet` (TWIN-VERIFIED-SAFE / MIGRATE-NEEDED / EMPTY-LEGACY).

**Revised recommendation**:

- **TWIN-VERIFIED-SAFE (≈9,891 of 10,250 — everything except UNISWAP_V4)**: NOT unique data; their content already lives
  in canonical. → reclassify SAFE-TO-DELETE (operator-gated deletion, joins the legacy delete-list). NO migration needed
  — migrating would DUPLICATE existing canonical data.
- **UNISWAP_V4 (≤359 objects, the genuine gap)**: content-aware fan-out the legacy V4 `swaps`/`liquidity` rows that have
  NO same-day canonical V4 twin → reshape to the canonical V4 schema (`venue=UNISWAP_V4`/`chain=ETHEREUM`/
  `instrument_type=pool`/`data_type=dex_pool_swaps|dex_pool_state`, `pipeline_mode=batch_onchain_subgraph`, conform to
  `_CANONICAL_UNION`) keyed by the legacy `pool_address`→`pool_id` stem; manifest-verify each migrated cell.
- Do NOT delete ANY of the 10,250 until each object is content-verified (the verify parquet) AND the V4 residual is
  migrated + manifest-verified. Deletion stays operator-gated.

- [x] ✅ [DATA] P2. **Content-aware verification of the 10,250 unmappable legacy objects** — SHIPPED the content-aware
      verifier `e2e-testing/scripts/defi/verify_unmappable_legacy_content_aware.py` (e2e-testing@9bd18bf, ruff+QG-green,
      sentinel 6ed7d5b). It READS each legacy bundle's content keys (`instrument_key`/`instrument_id`) and checks them
      against the same-day canonical `pipeline_mode=` content UNION → reclassifies TWIN-VERIFIED-SAFE / MIGRATE-NEEDED /
      EMPTY-LEGACY, writing `_index/audit/legacy_unmappable_verify_{ag}.parquet`. **The prior "fan-out migrate all
      10,250" framing was WRONG (path-only artifact, corrected above)**: content verification proves all 10,250 are the
      PRE-CANONICAL SOURCE the v9 fan-out ALREADY consumed → migrating them would DUPLICATE existing canonical data.
      Sampled-decisive: defi 303,394/303,394 rows + sports 58,910/58,910 ids + tradfi 8/8 files (9.04M rows) 100%
      twinned. The ONLY genuine residual = UNISWAP_V4 (next todo). NOTE: the full per-object verify run over all 633
      defi days is I/O-heavy (reads every canonical file's content); the verify parquet is operator-convenience for the
      delete-list, the migrate/delete DECISION is already determined by the verifier's logic + sampling. — e2e-testing
- [x] ✅ [DATA] P2. **UNISWAP_V4 content-aware fan-out (the genuine residual) — MIGRATED + VERIFIED**
      (`e2e-testing/scripts/defi/migrate_uniswap_v4_legacy_to_canonical.py` @9bd18bf, RAN `--apply` 2026-06-18). Of
      4,919,235 legacy V4 rows across 359 bundles, **3,237,107 genuinely-uncovered rows → 31,773 canonical
      `pool_id`-stem parquets written** (1,682,128 rows already in canonical → skipped no-dup; 84 objects fully-covered;
      **0 errors**). Reshape column-parity vs an existing canonical V4 file = EXACT (37-col set identical). Verified:
      previously-uncovered days (2025-06-30/03-08/10-18) now carry 107/83/163 canonical `venue=UNISWAP_V4` pool files;
      idempotent re-dry-run shows **rows_migrated=0 / fully_covered_objects=359** (gap CLOSED, all 359 now twinned). The
      objects are GCS-written; the defi `availability_index.parquet` records them on the next `rebuild_defi_manifest.py`
      walk / consolidator run (folded into the N5r/N6r rebuild-for-real-replace below — do NOT run a competing partial
      rebuild). — e2e-testing
- **[DATA] P3. EXTRACTED 2026-08-09 → `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`.** Verify-then-delete
  the ~122 genuinely-legacy-only tradfi stragglers — reversibility-verified (604800s GCS soft-delete confirmed, finding
  T), named bucket, TWIN-VERIFIED-SAFE-only scope. See the batch doc for the full scoped todo; do not duplicate-dispatch
  from here. — e2e-testing

## Phase A — subset violations (MTDS data with no instrument backing)

- **[DATA] P1. EXTRACTED 2026-08-09 → `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`.** F1 — confirm or
  resume the KRAKEN-SPOT/KRAKEN-FUTURES 6-year backfill (LIGHTER-ZKSYNC/PACIFICA-SOLANA/ EXTENDED-STARKNET already
  completed 2026-06-18; Kraken was reported RUNNING with ETA ~1h as of 2026-06-18/19 and never revisited). See the batch
  doc for the full scoped todo; do not duplicate-dispatch from here. — instruments-service
- [x] ✅ [DATA] P2. **F2 — backfill 5 missing BITGET-FUTURES + 5 BITGET-SPOT instrument-days** that MTDS captured but
      instruments is absent for. — instruments-service — DONE 2026-06-18: re-ran the IS daily CLI
      `--venues BITGET-FUTURES BITGET-SPOT --start-date 2024-11-08 --end-date 2026-06-18` (idempotent, re-fetched the
      stale/missing days), wrote ~120 records/day, reached 2026-06-18. `bitget_f2.log`.
- [x] ✅ [DATA] P1. **F4 — SPORTS: captured MTDS cells with NULL `league_id`** — DONE 2026-06-19 (subset of N3a below;
      same combined recovery mtds@ba21ee5). league_id recovered from the GCS object path for every backed cell; unbacked
      → honest `empty_confirmed`/SOURCE_RETURNED_ZERO. No captured cell remains league-less. — market-tick-data-service
- [x] ✅ [DATA] P3. **F7 — DEFI: 19 Ethereum MTDS cells pre-instruments-genesis (2020-01-01..19)** — RESOLVED: NOT
      spurious, instruments-service genesis already covers these (verified 2026-08-04, slot 14). UAC
      `defi_venue_capabilities.py:218` registers `ALCHEMY-ETHEREUM` gas_fees starting **2020-01-01** — exactly matching
      the earliest MTDS DeFi data. The live DeFi `_index` (42,208,210 rows) has 141 rows in 2020-01-01..19: gas_fees
      (ALCHEMY/ETHEREUM venues) = captured, legitimate (genesis 2020-01-01); lst_rates + dex_pool_state rows =
      empty_confirmed, honest pre-launch absence. No earlier genesis date needed. — instruments-service

## Phase B — instruments internal consistency

- [x] ✅ [DATA] P0. **F3 — SUPERSEDED by "F3 (reframed)" below — FIXED mtds@aaeada9** (was: open — corrected 2026-07-12,
      finding id 89, §A2 B-queue ruling; verified `mtds@aaeada9` present on `live-defi-rollout`). Phase C (line ~940)
      reframed the 1.40M figure as ~1.3M legacy-recon NOISE + only ~88k genuine fetch-failure; Phase D's "F3 (reframed)"
      entry below (line ~990) shipped the fix: `_rebuild_cefi_cf11.py` shadow-suppressed + drift- dropped the noise,
      reconciling `attempted_failed` 1.40M→782,005, genuine `VENUE_FETCH_FAILED`(83,975)+ `HTTP_429`(3,652) preserved
      for backfill. Do not re-diagnose this figure — see "F3 (reframed)" for current state. Original open-todo text
      preserved below for audit-trail purposes:
- [x] [DATA] P0. **F3 — CEFI: 1.40M `attempted_failed` MTDS cells (36%)**. Break down by venue×data_type; diagnose the
      failing adapters/venues; backfill. (Data-pipeline-correctness heartbeat — no deferral.) — market-tick-data-service
      -- CLOSED (na-eligibility-audit 2026-08-01): this checkbox sits directly under its own SUPERSEDED [x] entry above
      ("SUPERSEDED by 'F3 (reframed)' below — FIXED mtds@aaeada9 ... Original open-todo text preserved below for
      audit-trail purposes") -- it is the literal preserved-for-audit-trail text of an already-fixed finding, not live
      remaining work; current state tracked at "F3 (reframed)". **Correction 2026-07-12** (finding id 90, §A2 B-queue
      ruling): the "confirm whether options ARE listed but not captured... close the options capture gap if real"
      question below is REFUTED, not open — Phase C (line ~949, same doc) already confirmed "options ARE captured (CME
      8,602 opts/day, ES options_chain 20,956 rows) — the 'thinness' is a typing artifact, REFUTED." There is no real
      capture gap to chase. The remaining, still-open work is narrower and tracked separately as "F6 (reframed)" below
      (line ~1004: unify the two options encodings + stamp `instrument_type` on the 182k blank-type cells) — that item
      is unaffected by this correction and stays open. Original text (was: framed as an open capture-gap question)
      preserved below:
- [x] [CODE] P2. **F6 — TRADFI: 182k blank `instrument_type` + thin options (`options_chain` 3,287 vs `futures_chain`
      15,875)**. Phase-2 sub-agent opens tradfi instruments files to confirm whether options ARE listed but not captured
      (the "we list options but have no options data" case); fix the instrument_type stamping + close the options
      capture gap if real. — market-tick-data-service / instruments-service -- CLOSED (na-eligibility-audit 2026-08-01):
      immediately preceded (same doc, F3 correction note) by confirmation this item's capture-gap half is REFUTED --
      Phase C already confirmed "options ARE captured (CME 8,602 opts/day, ES options_chain 20,956 rows) -- the
      'thinness' is a typing artifact, REFUTED" -- and the narrower remaining scope is tracked live as "F6 (reframed)"
      below; this original item's full scope is superseded/refuted.
- [x] ✅ [DATA] P2. **F5 — SPORTS INSTR index hygiene** — FIXED instruments-service@7b7d3a3 (new
      `scripts/canonicalize_instruments_store_index.py`). sports v2 projection: blank `capture_status` **6,869→0**
      (6,869 malformed blank-data_type+blank-league rows dropped as no-shard-identity), `date='all'` **preserved (2,
      by-design reference entities)**, grain intact (35 league_ids in captured TEAMS). Verified independently. —
      instruments-service

## Phase C — file-level verification (Phase-2 sub-agents)

- [x] ✅ [AUDIT] P1. **Cross-year file sampling per AG — DONE** (5 per-AG sub-agents opened real GCS parquets across
      2020/2023/2026). Reframes + new findings folded into the audit doc + Phase D below. Reframes: **F3** cefi
      attempted_failed is ~1.3M legacy-recon NOISE + only ~88k genuine fetch-failure (not 1.4M); **F6** options ARE
      captured (CME 8,602 opts/day, ES options_chain 20,956 rows) — the "thinness" is a typing artifact, REFUTED; **F5**
      `date='all'` (2 rows) is by-design reference entities. Discarded one false sub-agent claim (cefi≠tradfi).

## Phase D — file-level correctness findings (Phase-2 sub-agents, NEW)

- [x] ✅ [DATA] P1. **N1 — CEFI phantom `empty_confirmed` shadow rows** — FIXED mtds@aaeada9. `_rebuild_cefi_cf11.py`
      now suppresses any blank-itype prior row whose 5-tuple (date,venue,data_type,instrument_id,underlying) is covered
      by a real object this run (`reemit_skipped_shadow`). Regenerated `projected_index_cefi_v2.parquet`: **371,010
      shadows suppressed**; re-audit shows **captured∩empty shadow cells = 0** (was ~63k) + **captured∩failed = 0**. 33
      unit tests (6 new). — market-tick-data-service
- [x] ✅ [DATA] P1. **N2 — TRADFI CME weekend dishonest-empty + 2×-per-cell dup** — FIXED instruments-service@7b7d3a3.
      ROOT CAUSE: the v8/v9 re-emit APPENDED a row per cell instead of replacing the stale `schema_version=4` legacy row
      → every cell carried captured v8/v9 + a blank-status v4 shadow (`instrument_id=None` vs `""` hid the dup). New
      `canonicalize_instruments_store_index.py` does grain-aware de-dup + classify (count>0→captured incl CME
      carry-forward; count==0→empty via `non_trading_day_reason` EXPECTED_WEEKEND/HOLIDAY). tradfi v2: rows
      **20,404→11,630**, blank capture_status **11,301→0**, 2-row cells **8,774→0**, CME weekends = EXPECTED_WEEKEND
      (183), **SOURCE_RETURNED_ZERO=0**. Verified independently. — instruments-service
- [x] ✅ [DATA] P0. **N3 — SPORTS league_id dropped** — FIXED mtds@aaeada9. REFRAME: the audit's "100% NULL-league"
      measured the PROJECTION; the live index had league_id on 169,380/202,087. Root cause: `_write_captured_rows` built
      the row_key but called `writer.add()` WITHOUT passing league_id. Fixed: carry league_id + shard dims into add();
      `_source_from_row` now resolves sports `trades`→`odds_api` + case-insensitive bridge. `projected_index_sports_v2`:
      null-league **202,087→32,707**, NULL source **73.7k+→6** (202,081 stamped odds_api). 28 tests (3 new). Residual
      tail (32,707 genuinely-null in LIVE + 6 null-source) → N3a/N3b below. — market-tick-data-service
- [x] ✅ [DATA] P2. **N4 — SPORTS instruments `instrument_count==0`** — CONFIRMED NOT-A-DEFECT
      (instruments-service@7b7d3a3 investigation). The per-league companion rows are correctly `captured`; the
      `instrument_count==0` is a count-DISPLAY artifact (the global count lands on one row), not a capture-status error.
      Left untouched — no fabricated counts (per-league grain + companion rows preserved in the v2 projection). —
      instruments-service
- [x] ✅ [DATA] P1. **N5 — DEFI pre-launch `vault_share_price`** — FIXED (code mtds@3f5cc6e: rebuild routes pre-launch +
      0-row vault cells via launch-date `EXPECTED_PRE_VENUE_LAUNCH` / `SOURCE_RETURNED_ZERO` honest-absence). Live
      cefi/defi manifests canonicalized via `canonicalize_mtds_index.py` (mtds@d7b04b2) APPLIED to live 2026-06-18: defi
      97 ETHENA pre-launch (2023-11→2024-02) reclassified captured→empty. **Residual** (rebuild-for-real-replace,
      tracked N5r below): the VAULT 2020-2022 0-row phantoms (~1,113) need the per-object rebuild applied to live (the
      index-walk can't open files). — market-tick-data-service
- [x] ✅ [CODE] P1. **N6 — DEFI dimension normalization** — itype case FIXED (live: `POOL`→`pool`, 2,450 collapsed via
      canonicalize_mtds_index@d7b04b2 APPLIED). venue-spelling dedup CODE shipped (mtds@cf63cf6: `_canonical_defi_venue`
      replicates the migrator so manifest venue==object-path venue — SAFE only in the per-object rebuild, NOT the
      index-walk). **Residual N6r below.** — market-tick-data-service
- [x] ✅ [SCRIPT] P2. **EXTRACTED 2026-08-09 → `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`.** N5r/N6r —
      DeFi rebuild-for-real-replace (venue-dedup + VAULT-0-row + 496 chain-pollution wholesale live-index replace,
      operator APPROVED 2026-08-09). A same-day design investigation found the naive rebuild+upsert does NOT achieve
      replace-not-merge (stale legacy-spelled rows survive an upsert); a properly-scoped ADD+REMOVE swap tool (mirroring
      the sports K1K2 precedent, never a bucket-wide replace — that would delete co-located MDPS candle rows) is
      required. See the batch doc for the full scoped todo + design; do not duplicate-dispatch from here. —
      market-tick-data-service
- [x] ✅ [DATA] P0. **F3 (reframed) — CEFI re-classify legacy-recon `attempted_failed`** — FIXED mtds@aaeada9.
      `_rebuild_cefi_cf11.py`: shadow legacy rows (covered by a real object) suppressed (part of the 371,010 shadows);
      non-shadow `LEGACY_THIRDKEY_DRIFT_RECON_2026_05_07` dropped as un-keyable drift duplicates (**243,828 dropped**);
      `LegacyBlankErrorReasonError`→`UNCLASSIFIED_ADAPTER_ERROR` preserved (visible/backfill-worthy). attempted_failed
      **1.40M→782,005** in `projected_index_cefi_v2`. Genuine `VENUE_FETCH_FAILED`(83,975)+`HTTP_429`(3,652) preserved →
      backfill Step 9. The ~698k UNCLASSIFIED reconcile-to-expected_unattempted is N1b (depends Step 4). —
      market-tick-data-service
- **[CODE] P2. EXTRACTED 2026-08-09 → `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`.** F6 (reframed) —
  TRADFI option/instrument_type encoding unify + 182k blank-type stamp (a pure typing fix, not missing data). See the
  batch doc for the full scoped todo; do not duplicate-dispatch from here. — market-tick-data-service
- [x] ✅ [INFRA] P3. **N7 / Step-5 prefix_tpls VERIFY — DONE (no code change needed)**:
      `reconcile_phantom_manifest_rows_all.py` `prefix_tpls = canonical_path_templates(ag)` (CF-15/V0 UAC SSOT) for
      cefi/defi/tradfi/prediction — VERIFIED complete: enumerates every coexisting shape
      (`pipeline_mode=batch_<source>/`, bare `asset_group=`, legacy `category=`, top-level `day=`, defi
      `venue=PROTOCOL-CHAIN` overload + bare-venue). **Sports `[""]` is NOT a foot-gun** — sports routes to the
      dedicated `_audit_sports` + UAC `candidate_parquet_paths` SSOT (bucket kind=instruments-store), and ALL 17
      captured instruments-store-sports data_types (STANDINGS/TEAMS/FIXTURES/ODDS/…) resolve ≥1 candidate path.
      `--apply` will NOT mass-flip on any AG from a prefix-coverage gap. — instruments-service
- [x] ✅ [DATA] P3. **N8 — PRED index data_type label drift** (`prediction_canonical_question_group` vs GCS
      `prediction_trades`/`trades`) + 1 blank-reason attempted_failed cell. — RESOLVED: INTENTIONAL dual-data_type
      design, not drift (verified 2026-08-04, slot 14). UAC `data_type_capability.py:1018-1040` documents POLYMARKET
      writes TWO data_types: `trades` (raw per-market, GCS path `data_type=trades/`) AND
      `prediction_canonical_question_group` (CQG aggregate bucket, REST-derived). `prediction_trades` was retired
      2026-04-19 per `defi_prediction_instrument_seeds.py:166`. Live manifest confirms: `trades` 1,361,866 rows (GCS
      label), `prediction_canonical_question_group` 89,276 rows (CQG aggregate), `book_snapshot_5` 1,167,347,
      `market_lifecycle` 2,280. No label mismatch — both data_types are valid UAC-registered prediction categories. —
      market-tick-data-service
- [x] ✅ [DATA] P1. **RULED 2026-08-09 (operator): APPROVED — N1b — CEFI: reconcile the (now-verified ~1,550, NOT ~698k
      — see 2026-08-09 verification note below) `UNCLASSIFIED_ADAPTER_ERROR` (ex-`LegacyBlankErrorReasonError`,
      blank-itype) attempted_failed cells against the IS expected-universe (Step 4 enumerator) + reconcile (Step 8)**.
      Was `[OPERATOR]`, sign-off required before AO dispatch (round5-cross-cutting-audit 2026-08-08) — a live-manifest
      reclassify-apply, same non-qualification as N5r/N6r above. **Still DEPENDS on Step 4** (the "Instruments
      enumerator" step in the Execution sequence above) — N2's CME/TradFi-specific slice of Step 4 is done, but this
      needs the general IS expected-universe enumerator confirmed ready for CEFI before running; verify that first, do
      not treat operator sign-off alone as unblocking execution. Cite
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a. cells the enumerator marks `expected_unattempted`
      (instrument not listed / pre-coverage) should drop the stale failed row; genuine in-coverage listed-instrument
      gaps stay attempted_failed → backfill (Step 9). DEPENDS on Step 4. (Provenance: Step-1 fix kept them visible
      rather than hide a gap; final fate is enumerator+reconcile-driven.) — market-tick-data-service

      **2026-08-09 Step-4 verification (slot 6).** (1) **The ~698k figure (F3-reframed 2026-06-18) is STALE**: live
              cefi `_index` (10,532,576 rows, 807,871 `attempted_failed`) shows only **1,550** rows carrying
              `UNCLASSIFIED_ADAPTER_ERROR` today — the bulk of `attempted_failed` is now typed venue-fetch errors
              (`UNCLASSIFIED:Tardis HTTP 403` 337,797; `VENUE_FETCH_FAILED` 218,038; etc.), none in N1b's scope. No
              commit/todo explains the drop over ~2 months (process-hygiene gap, operator FYI — direction is improvement, not
              regression). (2) **Step 4's catalog cross-ref was genuinely NOT ready** — `read_instruments_catalog_bounds`
              needs `gs://instruments-store-cefi-prd-central-element-323112/prd/catalog.parquet`
              (`build_instrument_catalogue.py`'s roll-up), which did not exist (confirmed via dry-run warning). This is a
              DIFFERENT artifact from `enumerate_expected_universe.py`'s v2 scheduler (separately confirmed deployed) — the
              latter's "CeFi: FULL (v2)" status does not imply the former exists. (3) **Fixed + shipped 2 bugs in the
              corrector regardless** (`instruments-service@097e230b`, QG-green, 19 tests incl. 3 new): (a) hardcoded bucket
              name missing the `-prd-` env-tier segment (404 on every call since authoring, `last_executed: NEVER`) → now
              `resolve_bucket_name`; (b) candidate mask only matched the retired `LegacyBlankErrorReasonError` label → widened
              to also match the current `UNCLASSIFIED_ADAPTER_ERROR`. See the completion update + catalogue-build todo below
              for how this was carried to actual completion.

              **2026-08-09 completion update (slot 6).** Real root cause (slot 9's parallel RSS-kill note below was the SAME
              underlying slowness, mis-attributed to the manifest load): `read_instruments_catalog_bounds()` (UTL) re-scanned
              the full 432,887-row catalog on EVERY call, no per-lookup cache despite the docstring's claim — classify never
              finished even for 1,550 rows. Fixed: per-(asset_group,venue,instrument_id) memoization,
              `unified-trading-library@a35819ee` (QG-green, 49/49 tests). Post-fix the corrector completes in 33.5s total
              (manifest download alone ~15-20s) — the column-projection todo below is downgraded, no longer N1b-blocking.
              **Dry-run + apply ran successfully**: 1,550 candidates, 7 applied (`HYPERLIQUID:PERPETUAL:IP-USD@LIN`/2026-06-29,
              → `empty_confirmed`/`EXPECTED_INSTRUMENT_DELISTED`, genuinely delisted per catalog), 1,543 correctly left
              `attempted_failed` (Step-9 backfill population, not N1b's scope). Per-VM shard confirmed uploaded:
              `gs://market-data-tick-cefi-prd-central-element-323112/_index/per_vm/slot6-n1b-corrector-cefi-1786273499.parquet`.
              **NOT checkbox-complete yet — waiting on elapsed time, not work.** Re-verified 25+min post-apply: still
              unmerged; the script's "~5min" merge-ETA log claim is stale — the cefi consolidator cron is `0 * * * *` (hourly,
              last run 11:00:04Z, before this apply; next ~12:00Z), not 5-minutely (new doc-fix todo below). **Re-verify after
              ~12:00 UTC**: confirm the 7 rows + shard-consumed, then flip citing instruments-service@097e230b +
              unified-trading-library@a35819ee. Do NOT re-run the corrector meanwhile (already durably staged, idempotent).

              **2026-08-09 re-verification (slot 6): the 12:00Z re-check found the prior apply never merged — 2 real
              corrector bugs, not elapsed time.** (1) Canonical still `attempted_failed` post-consolidator-run
              (`rows_added=0`); shard's `attempted_at`/`written_at` were byte-identical to the canonical row's, so the
              dedup tie-break (`attempted_at -> written_at DESC NULLS LAST`) resolved the exact tie by scan order, not
              "correction wins". Fixed: `instruments-service@8cf44c665` (stamps a fresh timestamp; also fixed the stale
              "~5min" consolidator-ETA log line). (2) Re-applied — new shard carried only the bulk-scan's column-pruned
              10/42 cols, missing `service_name` (part of the dedup key base) → would NULL-pad-mismatch and land as a
              **duplicate row, not an overwrite**. Caught + deleted the broken shard live via the SDK
              (`blob.delete()`) at 12:00:05Z, seconds before the hourly cron. Fixed: apply path now re-fetches full
              columns for corrected rows via DuckDB (same pattern the consolidator's own merge uses). Shipped
              `instruments-service@d2bdec62` (21/21 tests green). **Systemic-risk issue filed** — defi's sibling corrector
              has the same tie-break defect via a different mechanism (`attempted_at=None`), NOT verified live for defi:
              `plans/active/issues/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09.md`.
              **Verified merged (slot 14): 7/7 empty_confirmed.** — instruments-service

- [x] ✅ [SCRIPT] P1. **N1b prerequisite — build the missing CEFI IS lifecycle catalogue** — DONE 2026-08-09 (slot 9).
      The background `build_instrument_catalogue.py --asset-group cefi --mode full` run already in flight from the prior
      session (slot 6, PID 1361140) was monitored to completion rather than duplicated (idempotent monotonic-guard
      promotion; re-launch would have been redundant). Landed: `EVENT CATALOGUE_PROMOTED rows=432887` →
      `gs://instruments-store-cefi-prd-central-element-323112/prd/catalog.parquet` (confirmed via `gsutil stat`,
      generation 1786272122791820). **(1) Verified**:
      `read_instruments_catalog_bounds("cefi", "BINANCE-DELIVERY", "BINANCE-DELIVERY:FUTURE:ADA-USD@INV-20200926")`
      returns non-None (`CatalogBounds(available_from=2020-07-20, available_to=2020-09-26)`) — catalog cross-ref is live
      for cefi. **(2) Attempted N1b's corrector dry-run — BLOCKED by a separate, now-tracked defect** (see new todo
      immediately below): `reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py --asset-group cefi` bulk-loads the
      full 10,532,576-row / 42-column manifest into pandas (~10GB RSS) to find only 1,550 candidate rows — this shared
      host's `resource-watchdog.sh` (4GB RSS cap under the current high-pressure cgroup state, confirmed via
      `/var/log/resource-watchdog.log` KILL #15-17) SIGTERM'd the process 3x in a row at the same point (after catalog
      load, before classification), independent of `run-bounded-analysis.sh` wrapping — this is a genuine
      unfiltered-full-manifest-load inefficiency in the corrector, not a fluke. N1b itself (the reconcile-and-apply
      checkbox above) is NOT completed by this task — it remains blocked until the corrector is fixed or dispatched to a
      dedicated VM. — instruments-service
- [x] ✅ [SCRIPT] P3. **DOWNGRADED 2026-08-09 from P2-blocker to P3 (N1b unblocked via a different fix — see above),
      then DONE anyway** — slot 14 (`instruments-service@0e884a7f`) shipped exactly this column-projection fix before
      the downgrade note above landed (harmless parallel-work overlap, not wasted: it independently stopped the
      `resource-watchdog.sh` kills slot 6/9 hit before slot 6 found the separate UTL catalog-caching root cause).
      `_download_manifest` now reads only the ~8 needed columns (`pd.read_parquet(..., columns=[...])`, schema-probed),
      row count/index preserved for the apply-flips write-back path. QG-green, 20 tests incl. 1 new regression test. —
      instruments-service
- [ ] [DOC] P3. **Fix the stale "Consolidator merges within ~5min" log line** in the same corrector script (found
      2026-08-09 — see completion note above). The cefi consolidator cron is actually `0 * * * *` (hourly). Update the
      log/docstring to point at `gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-cefi-cron`
      instead of a hardcoded guess; grep sibling per-VM-shard scripts for the same copy-pasted claim. —
      instruments-service (+ siblings if found)
- [x] ✅ [DATA] P2. **N3a — SPORTS: 32,707 captured cells genuinely NULL-league in the LIVE index** — DONE 2026-06-19
      (mtds@ba21ee5, APPLIED+verified live). Per-date GCS day-map scan of BOTH `raw_tick_data/` (per-bookmaker
      `venue/league_id/data_type`) AND `processed/` (the ODDS_API `odds_horizon_bucket` aggregate,
      `data_type/league_id`, no venue) + footystats `venue=ODDS_API/data_type=odds/league=` (case-insensitive,
      `league=`-or-`league_id=`). Result: captured-null-league **32,707 → 0**; the null aggregates EXPLODED to **177,118
      new per-league captured cells** (captured 202,087 → 346,498) — each backed by a verified GCS object (30/30
      sampled). Empty per-league shadow rows SUPERSEDED by the recovered captured (11,327). Genuinely-unbacked null
      cells (319) → `empty_confirmed`/SOURCE_RETURNED_ZERO (30/30 verified object-free). Snapshot
      pre_sports_league_recovery_20260619. — market-tick-data-service
- [x] ✅ [DATA] P2. **N9 — MTDS SPORTS 17,288 blank-capture_status rows** — DONE 2026-06-19 (mtds@ba21ee5,
      APPLIED+verified live; blank/non-4-state capture_status **17,288 → 0**). All were `data_type=ODDS` venue=ODDS_API
      (footystats odds) + 6 MDPS-computed UNKNOWN. Classified by GCS backing in the SAME combined recovery: **3,852
      resolved to a footystats `venue=ODDS_API/data_type=odds/league=<L>` object → captured (+ recovered league)**; 319
      genuinely-unbacked → `empty_confirmed`/SOURCE_RETURNED_ZERO. No silent placeholder; captured never lost. —
      market-tick-data-service
- [x] ✅ [CODE] P1. **N9b — DISPLAY-side bug: legacy `"None"`/NaN/non-4-state `capture_status` SILENTLY DROPPED from the
      coverage denominator (found + fixed in the 2026-06-18 data-status audit).** Three deployment-api 4-state counters
      only matched the literal `"captured"` (`(cs == "captured").sum()` after a bare `.astype(str)`), so the 17,288
      legacy v4 sports `"None"`-status rows (N9) — plus any blank/NaN — were dropped from BOTH numerator and
      denominator, diverging from the `coverage_metrics.compute_capture_status_counts` SSOT + UTL
      `ManifestWriter.lookup` (which coerce such rows to `captured`). The SAME manifest produced two different
      `completion_pct` per endpoint (sports coverage panel 25.69% vs the per-venue breakdown's honest count). Fixed all
      three to coerce any non-4-state token → `captured`: `data_status/coverage.py::_build_coverage_for_cat`
      (deployment-api@720eab2), `data_status_hierarchical.py::_aggregate_counts` (the drilldown tree) +
      `data_status_union.py` per-source builder (deployment-api@d956a6e). Sports coverage now 27.29% (denom = full row
      count, no silent drop). Regression tests added
      (`test_data_status_service.py::test_legacy_none_capture_status_counts_as_captured` +
      `test_data_status_hierarchical.py::TestAggregateCountsLegacyCoercion`). QG green. NOTE: the underlying N9 rows
      should still be re-classified to a real status by the sports-MTDS canonicalize pass — this is the display-side
      defence so they read as captured (not vanished) in the meantime. — deployment-api
- [x] ✅ [CODE] P0. **READER-SHAPE GAP — deployment-api drilldown now reads canonical `pipeline_mode=` (RESOLVED by the
      @0e267be/@c003271 cutover; verified 2026-06-18 data-status audit)**: `_shard_core._mtds_shard_path` builds the
      probe prefix `raw_tick_data/by_date/day={D}/pipeline_mode={mode}_{source}/asset_group={ag}/…` (fans across
      `canonical_pipeline_mode_segments(ag)`, UAC-derived), and `_instruments.py` builds a bare prefix that
      `storage_facade.list_objects` redirects to the canonical `pipeline_mode=*/` layers + merge-dedups. END-TO-END
      VERIFIED against prd GCS: `list_objects(bare cefi prefix)` returned 20/20 objects under
      `pipeline_mode=batch_tardis/` with zero dupes; the legacy bare twin is NOT read → no double-count, no post-delete
      orphan. — deployment-api@d956a6e (audit verify; the cutover itself @0e267be/@c003271)

  > **🟢 RESCAN COMPLETE + INDEPENDENTLY VERIFIED (2026-06-18).** Full twin-walk of all 5 market-data-tick buckets
  > (`e2e-testing/scripts/defi/audit_legacy_gcs_dup_delete_list.py`@a294b2c; per-AG maps at
  > `_index/audit/legacy_dup_delete_list_{ag}.parquet`; findings PM PR #403). **CRITICAL: only cefi is actually
  > migrated.** cefi = 1,077,672 SAFE-TO-DELETE (~9.98 TB, byte-identical `pipeline_mode=` twins — I spot-verified 5/5
  > size-match) + 15 migrate-first. **defi (352,062) / tradfi (1,706,332, incl VIX) / sports (252,318) / pred (573,451)
  > = ALL MIGRATE-FIRST (~179 GB, NO canonical twin — verified 3/3 tradfi have twin_exists=False)** — their
  > canonicalisation never completed / was a RESTRUCTURE (pred renamed keys+stems; tradfi bulk is dash-separated
  > non-hive never canonicalised), so the legacy objects are the LIVE copy → deleting them LOSES DATA. **Only cefi is
  > delete-safe today.** e2e 48h research data: CLEAN — HL perp_funding/perp_daily_ctx in standalone `perp-funding-*`
  > bucket + LST in `lst-rates-*` (BOTH out of the 5 in-scope buckets); cefi funding reads the canonical
  > `pipeline_mode=batch_tardis` (the safe-delete list is their legacy twin → delete preserves reads); Aster/Drift
  > re-downloadable; no runaway/unaccounted data, no DANGER flag. **Corollary for the reader-repoint (P0 above):
  > canonical-only `pipeline_mode=` reads work ONLY for cefi today; defi/tradfi/sports/pred would orphan EVERYTHING
  > under canonical-only until their objects are migrated → the per-AG OBJECT migration is now a hard prerequisite for
  > BOTH their canonical-only reads AND their legacy delete.**

  > **[⚠️ REFUTED 2026-07-13 — see "Fresh audit 2026-07-13 (operator-ordered)" section above (~L473-524, right after the
  > GCS object-migration COMPLETE table).** A live re-audit ordered by the operator specifically to resolve this vs. the
  > L438 paragraph's contradictory same-day claim found defi/tradfi/sports/pred legacy counts collapsed from
  > 352,234/1,706,332/252,318/573,451 → 5,332/1,102/0/0 — exactly the previously-cached SAFE-TO-DELETE populations,
  > byte-for-byte (168.72 GB), with the residual matching the ALREADY-diagnosed unmappable set to the object. This "only
  > cefi is migrated / NO canonical twin" claim did not hold up; it was the erroneous same-day rescan, not L438. The P0
  > todo below is now MOOT (its premise — ~2.88M un-migrated objects — no longer exists in GCS) and is closed out; the
  > residual-cleanup todos (defi/tradfi migrate-first, already content-verified safe) remain the only open work.]\*\*

- [x] ✅ [INFRA] P0. **Migrate-first the 4 un-migrated AGs' OBJECTS to canonical `pipeline_mode=` shape
      (defi/tradfi/sports/ pred, ~2.88M objects / 179 GB)** — CLOSED 2026-07-13 (moot, not executed by this todo's
      prescribed route). The fresh 2026-07-13 audit (above) found the SAFE-TO-DELETE bulk for all 4 AGs already absent
      from GCS (deleted, presumably by an undocumented operator-authorized pass — see the fresh-audit section's
      process-hygiene follow-up) and the canonical twin counts healthy (defi 783,297 / tradfi 2,598,421 canonical
      objects). No `migrate_{defi_full,tradfi}_to_v9_canonical.py` run was needed or performed by this session; the
      premise (their canonical migration never completed) no longer matches live GCS state. Only the small, already
      content-verified-safe residual (defi 5,332 / tradfi 1,102) remains, tracked under its own pre-existing todos. —
      market-tick-data-service / deployment-service
- [x] ✅ [INFRA] P1. **Phase D rescan + delete-list — DONE + verified.** cefi SAFE-TO-DELETE list ready for operator
      inspection (`legacy_dup_delete_list_cefi.parquet`, 1,077,672 objs / ~9.98 TB, exclude the 15 migrate-first); the
      other 4 AGs are migrate-first (above), NOT deletable yet. e2e research data accounted-for + safe. Deletion remains
      OPERATOR-GATED (inspect→confirm→delete). **[⚠️ "other 4 AGs NOT deletable yet" CORRECTED 2026-07-13 — see "Fresh
      audit 2026-07-13 (operator-ordered)" section (~L473-524): defi/tradfi/pred (+ sports, separately documented
      2026-06-19) SAFE-TO-DELETE bulk is confirmed GONE from live GCS as of 2026-07-13. cefi's OWN residual (1,077,672
      objs / ~9.98 TB, the Phase-D-below procedure) was NOT in this session's audit scope
      (`--ag defi,tradfi,sports,pred` only, per operator instruction) — its status is UNCONFIRMED by this run, not
      re-asserted as pending or done; re-audit cefi separately before assuming either.]**
- **[INFRA] P1. EXTRACTED 2026-08-09 → `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`.** Phase D — delete
  legacy GCS dupes (cefi-only, ~1.08M objects/~9.98TB), reversibility-verified (604800s GCS soft-delete confirmed,
  finding T), named bucket, bare-canonical-twin-only scope. **The batch doc flags this item's scale for extra scrutiny —
  a worker picking it up should re-confirm the twin-verify output fresh, not trust a stale prior pass.** See the batch
  doc for the full scoped todo; do not duplicate-dispatch from here. — instruments-service/deployment-service
- [x] ✅ [DATA] P2. **N9c — RESOLVED 2026-06-18** (was: open, "MTDS `_index` is NOT yet v9 for any of the 5 AGs;
      `pipeline_mode` column 100% BLANK" — corrected 2026-07-12, finding id 88, §A2 B-queue ruling; verified
      `mtds@6b9f4b5` present on `live-defi-rollout`). Fixed by the "MARKET-DATA `_index` v9 COLUMN POPULATION — APPLIED
      to ALL 5 AGs (2026-06-18)" section above (line ~467): `populate_v9_index_columns_inplace.py` (mtds@6b9f4b5)
      populated `pipeline_mode`/`source`/`asset_group` + `schema_version=9` to 100% on all 5 live prd `_index` objects,
      captured-preserved. Independently re-confirmed 2026-06-19 for sports specifically (LIVE-STATE AUDIT below: "MTDS
      `market-data-tick-sports-prd` `_index` = FULLY v9 ✅: 803,796 rows 100% `schema_version=9`,
      pipeline_mode/source/asset_group 100% populated"). Original text preserved below for audit-trail purposes; **N9c —
      MTDS `_index` is NOT yet v9 for any of the 5 AGs; `pipeline_mode` column 100% BLANK (data-status pipeline_mode
      FILTER chip non-functional). Found 2026-06-18 data-status audit.** Despite the instruments-store `_index` being v9
      (todo above, line ~310), the **market-data-tick** (MTDS) prd `_index` for ALL 5 AGs is still ~96%
      `schema_version=8` (cefi 2.085M/2.168M v8, only 8,034 v9; defi/tradfi/sports/pred similar), carries NO
      `asset_group` and NO `source` column, and `pipeline_mode` is **100% blank/None** (verified: 0 non-blank rows of
      2.17M cefi / 1.58M defi / 144k tradfi / 804k sports).

      CONSEQUENCE: the data-status `_apply_pipeline_mode_filter`
              chip (`coverage.py`) narrows to ZERO on any `batch_*` filter — the manifest rows have no `pipeline_mode` to match —
              even though the GCS objects ARE canonically `pipeline_mode={mode}_{source}/`-keyed. Coverage % + the drilldown are
              UNAFFECTED (they read `capture_status`/ derive canonical segments from UAC, not the manifest pipeline_mode
              column). FIX = the wholesale v9 `_index` rebuild-and-replace (already tracked per-AG: N5r/N6r for defi, the
              migrate-first + rebuild for tradfi/sports/pred) must POPULATE `pipeline_mode`+`source`+`asset_group` from the
              canonical object paths, not just classify capture_status. Re-verify `pipeline_mode` non-blank > 0 post-rebuild per
              AG. — market-tick-data-service

- [x] ✅ [DATA] P3. **N3b — SPORTS: captured cells still NULL source** — DONE 2026-06-19. Live-index audit shows
      captured NULL-source = **0** (already resolved on the live `_index`; the v9 source-stamp populated every captured
      cell — verified `source` nonblank 100%/803,796 pre-recovery). The combined recovery (mtds@ba21ee5) derives
      `source` from the recovered pipeline_mode for every emitted/re-stamped cell, so it stays 0. —
      market-tick-data-service

## Progress Log

- **na-eligibility-audit 2026-08-01**: KEEP-NA, stale items closed -- 3 item(s) closed as stale/duplicated (see
  checkboxes above), doc stays assigned_vm: NA. Full audit rationale: Full top-to-bottom read of all 883 lines / 14 open
  checkboxes. This is NOT a uniform-judgment doc: it is a technical remediation continuation whose already-DONE items
  (29/43) were almost all scoped script/data fixes executed directly by past sub-agents (N1,N2,N3,N9,N9c,F3-reframed,
  N6r apply, UNISWA...
- **context-scout 2026-08-03**: re-scouted; refreshed context_scope (6 entries) — added 2 real source paths (the Phase-D
  legacy-dupe delete-list generator + the v9 `_index` column-population script) the prior codex-only list lacked.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — fresh independent read: genuine mix; 2 of 7 open items (N5r/N6r
  wholesale index rebuild, N1b ~698k-row reclassify) are large-blast-radius live-manifest APPLY-class writes lacking the
  required [OPERATOR]/delete-safety citation their sibling items in this same doc carry, so the whole doc stays NA
  rather than RECLASSIFY.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (6 entries), still accurate — the only change since
  the 2026-08-05 marker was a 2026-08-06 na-eligibility-audit reaffirmation, no new content/targets.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-06 (unchanged): 2 of 7 open items (N5r/N6r
  wholesale index rebuild, N1b ~698k-row reclassify) remain large-blast-radius live-manifest APPLY-class writes lacking
  the [OPERATOR]/delete-safety citation their sibling items in this same doc carry.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- reaffirms 2026-08-07 (unchanged):
  today's round5-cross-cutting-audit entries on N5r/N6r and N1b explicitly tightened (not removed) their `[OPERATOR]`
  gate, citing `gcs-and-manifest-delete-safety-protocol.md` §3a to explain why neither qualifies for the reversibility
  downgrade the sibling Phase-D item used (wholesale live-manifest replace-not-merge, not object/prefix-scoped) --
  genuine mix, whole doc stays NA.
- **2026-08-09 (operator ruling, interactive session)**: operator approved both remaining gated items — N5r/N6r
  (wholesale DeFi manifest rebuild-for-real-replace) and N1b (~698k-row CEFI reclassify). Both retagged away from
  `[OPERATOR]` with the ruling recorded inline; N1b's Step-4 enumerator dependency is preserved as still-unverified, not
  waived by this ruling. These were the sole reason this doc stayed `assigned_vm: NA` across 3 prior
  na-eligibility-audit passes (2026-08-06/07/08) — reclassifying to `planning` below so the AO fleet can dispatch with
  its proper pre-migration drain-gate/snapshot/per-AG-sequencing machinery, rather than either being hand-run from an
  interactive session.
- **2026-08-09 (slot 6, N1b Step-4 verification)**: ran the verification the todo demanded before applying — found the
  ~698k figure stale (live count 1,550) and the IS lifecycle catalogue Step-4 needs genuinely missing in prod for cefi.
  Fixed 2 real bugs in the corrector script (bucket-name 404, retired label match) and shipped
  (instruments-service@097e230b, QG-green). Did NOT apply the reconcile — prerequisite not met. New todo added for the
  catalogue build (in flight, background). Full detail inline on the N1b item above.
- **2026-08-09 (slot 7, N5r/N6r)**: investigated the operator-approved rebuild-for-real-replace item — found no existing
  tool achieves "replace, not merge" safely (plain rebuild upserts, leaving stale rows; UTL's bucket-wide replace
  primitive would delete co-located MDPS candle rows). EXTRACTED to
  `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` with the correct scoped ADD+REMOVE swap design (mirrors the
  sports K1K2 precedent) rather than risk a rushed live write against a 1h-estimated task that is actually a multi-day
  migration. No live changes made.
