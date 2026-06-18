---
title: Instruments ↔ MTDS subset + consistency remediation
created: 2026-06-17
parent_epic: instruments_master
assigned_vm: vm-operator-ops
status: active
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
locked_by: live-defi-rollout
locked_since: 2026-06-17
source:
  - plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md (findings F1–F7, full-index walk)
  - operator 2026-06-17 (deep-dive audit dispatch)
---

# Instruments ↔ MTDS subset + consistency remediation

> **🔴 PRE-`--apply` BLOCKER GATE (2026-06-17).** The dry-run projections that `--apply` will materialise STILL carry
> these defects, and a reconcile `--apply` over uncovered path shapes flips real `captured`→`attempted_failed`
> (CLAUDE.md hard rule). **Do NOT `--apply` until these are fixed + the projection regenerated + re-eyeballed:**
> (1) **prefix_tpls coverage** — prove `ASSET_GROUP_CONFIG[ag]["prefix_tpls"]` covers ALL coexisting shapes
> (`category=`/`asset_group=`/bare/`pipeline_mode=`, see N7) per AG BEFORE apply; (2) **N6** normalize defi
> chain/venue/instrument_type pollution (apply migrates BY these values); (3) **N1** confirm dedup keeps the captured
> row, not the empty shadow; (4) **N3** recover sports league_id into the manifest first (else null-league is permanent);
> (5) **N5** verify the phantom-reconcile targets only true 0-row pre-launch vault cells. NON-blocking (fix after/parallel):
> F1, F3, N2, N4, F6, N8. **Apply order: pred → tradfi (clean) → cefi → sports → defi; never all-AG at once.**

Findings of record + method: `plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md`.

> **🟢 SCRIPT-COVERAGE MAP (2026-06-17) — every blocker is a GAP in the existing rebuild scripts, not unscripted.** The
> rebuild scripts ARE the migration: fix the gap → regenerate the dry-run projection → improved beta → `--apply`
> (path-schema) → backfills. Per finding: **prefix_tpls** ✅ `canonical_path_templates(ag)` covers all shapes (sports
> `[""]` — verify only); **N3** ⚠️ `rebuild_sports_manifest_v9` never extracts `league_id`/`league` from the MTDS object
> path into the row_key (canonicalizer `_canonicalize_row_key_league_id` then gets null); **N1** ⚠️ `rebuild_cefi`
> CF-11 dedup key mismatches (empty re-emit has blank `instrument_type` vs captured populated → both survive); **N5** ❌
> `rebuild_defi` emits `captured`/row_count=0 on file PRESENCE without opening (0-row/pre-launch → false captured) →
> route via `record_zero_rows`; **N6** ⚠️ `rebuild_defi._split_legacy_venue_chain` lacks instrument_type case-norm +
> lets pairs leak into `chain` + incomplete venue-dedup; **F3** ❌ `rebuild_cefi` passes legacy
> `attempted_failed` reasons through un-reclassified; **N2** ❌ instruments enumerator marks CME weekend carry-forward
> as `SOURCE_RETURNED_ZERO`. **Each Phase-A/B/D todo below = a scoped fix to the named script → regen that AG's
> dry-run projection → re-audit the fixed dimension.**
Phase-1 (manifest-level, full v9-projected-index walk) is DONE; Phase-2 (file-level cross-year manifest-vs-reality
sampling) is IN PROGRESS via per-AG sub-agents — findings fold back into the audit doc + new todos here.

> **🔴🔴 GCS DELETE SAFETY INVARIANT — READ BEFORE DELETING ANY OBJECT (codified 2026-06-18; HARD RULE).**
> **The manifest migration RELABELLED nothing — it is a CELL-KEYED rewrite (`_index` rows keyed by
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
> `_index/audit/legacy_dup_delete_list_{ag}.parquet` + `plans/audit/results/gcs_delete_list_and_e2e_data_accounting_2026_06_18.md`.
> **Deletion is OPERATOR-GATED (inspect→confirm→delete); migrate-first MUST complete first.**

## GCS delete safety — path/schema migration prerequisite map (DONE-before-DELETE)

For a legacy object to have a CANONICAL twin (the delete-safety precondition), its data must exist at the fully-canonical
path shape. The migrations that must be COMPLETE (every captured cell twinned) before the legacy copies are deletable:

1. **`pipeline_mode={mode}_{source}/` prepend** (primary) — every bare `…/day={D}/asset_group={ag}/…` object needs a
   `…/day={D}/pipeline_mode={mode}_{source}/asset_group={ag}/…` twin (mode/source via UTL `derive_pipeline_mode_for_row`).
   Tool: `migrate_{cefi_flat,defi_full,tradfi}_to_v9_canonical.py` (COPY). MIGRATE-FIRST = bare objects the rescan finds
   with no `pipeline_mode=` twin → run the migrate to create the twin.
2. **`category=`→`asset_group=`** — DONE (0 `category=` objects remain on cefi/defi/sports; verified).
3. **DeFi venue/itype canonicalization in the PATH** (N5r/N6r) — the canonical defi twin must be at the NORMALIZED venue
   (`UNISWAP_V3` not `UNISWAPV3`, `_canonical_venue` SSOT) + lowercase `instrument_type` (`pool` not `POOL`). An object at
   an un-normalized venue/itype path is NOT a canonical twin → migrate it (copy to the normalized canonical path) before
   deleting the legacy. This is the per-object rebuild-replace (N5r/N6r todo); the index-walk could not do it (would
   desync manifest from object path).
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
the fixed dimension** (the `/tmp/audit_subset.py` pattern or a per-AG file re-check) → flip the todo + journal before/after
numbers. Order:

1. **CeFi script** `rebuild_cefi_manifest.py` — **N1** dedup key (captured suppresses its blank-type empty shadow) + **F3**
   reclassify legacy `attempted_failed` recon-noise (~1.3M) vs keep genuine ~88k. Verify: no captured+empty double-rows;
   attempted_failed → ~88k.
2. **Sports script** `rebuild_sports_manifest_v9.py` — **N3** extract `league_id`/`league` from the MTDS object path +
   row column into the row_key (BEFORE `_canonicalize_row_key_league_id`); stamp `source` on `trades`; collapse
   API_FOOTBALL/`api_football`. Verify: captured cells carry league_id.
3. **DeFi script** `rebuild_defi_manifest.py` — **N6** normalize instrument_type case (pool/POOL), keep pool-pairs OUT of
   `chain` (only known chain tokens), collapse venue dups; **N5** route 0-row/pre-launch files through
   `DefiManifestRecorder.record_zero_rows` (venue-launch-date-aware) instead of presence⇒captured. Verify: no token-pairs
   in chain, single-case instrument_type, no pre-launch captured-0-row vault cells.
4. **Instruments enumerator** (instruments-service) — **N2** CME/TradFi weekend carry-forward = honest carry-forward (not
   `SOURCE_RETURNED_ZERO`); de-dup 2×-per-cell index rows.
5. **prefix_tpls VERIFY** (`reconcile_phantom_manifest_rows_all.py` `ASSET_GROUP_CONFIG`) — prove
   `canonical_path_templates(ag)` enumerates EVERY coexisting shape per AG (`category=`/`asset_group=`/bare/`pipeline_mode=`)
   against real GCS prefixes; replace the sports `[""]` with real templates. **APPLY FOOT-GUN — uncovered shape ⇒ apply
   flips real captured→attempted_failed.** Block apply for any AG whose coverage isn't proven.
6. **Regenerate ALL projections → re-audit** = the IMPROVED beta. Confirm F1–F7 + N1–N8 resolved/honestly-classified;
   record before/after in the audit-doc Progress Log.
7. **PRE-MIGRATION DRAIN GATE (HARD, CLAUDE.md)** — before ANY `--apply`: gracefully stop ALL running VMs (GCP+AWS) + run
   the manifest consolidator + snapshot `_index/snapshots/pre_migration_<date>.parquet`
   (`code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.0 Stage 0).
8. **`--apply` AG-by-AG, safest first: pred → tradfi → cefi → sports → defi.** Per AG: prefix_tpls green + projection
   re-audited clean → run the real path-schema migration → verify the live `_index` matches the projection (NO mass
   captured→failed flip) → next AG. **Never all-AG at once.** Mass-flip ⇒ STOP + diagnose prefix_tpls, do not continue.
9. **Backfills** — F1 (Kraken+ instruments history), the ~88k genuine cefi `VENUE_FETCH_FAILED`, any real captured-absent
   cells. Run to completion (manifest-verified rows). **→ The FULL path to 100% (could-exist enumeration + per-AG
   MTDS/IS backfill + cross-data_type completeness + credential asks + live=batch keep-green) is tracked separately in
   `path_to_100pct_backfill_mtds_is_2026_06_17.md` (parent_epic mtds_mdps_master), gated to start once this migration's
   `--apply` lands.**

**Gates / hard-stops:** `--apply` is operator-DISPATCHED (authorized) but each AG is gated on (5)+(6)+(7) green; a red
gate ⇒ STOP+document, don't apply that AG. Genuine human hard-stops unchanged: live wallet keys, `1.0.0` graduation.

## 🟢 AUTONOMOUS COMPLETION PLAN (2026-06-18) — drive ALL to verified-working, EXCEPT the delete (operator-gated)

> Operator `/autonomous` 2026-06-18: complete everything (~1-2h, parallelise) to a working+verified state; **the ONLY
> thing NOT to do is DELETE the old data** — but size it all up so the delete is ready. Loop until done; journal each tick.

**State now:** cefi legacy delete DONE (9.98 TB, recoverable). cefi fully migrated. defi/tradfi/sports/pred object-migration
was a broken VM run (0 twins) → VMs STOPPED → focused defi diagnosis+fix sub-agent `acb89f8f6b5c9a943` IN FLIGHT (gets defi
producing twins e2e via a copy-driver off the audit parquet's pre-computed `legacy_path→canonical_twin_path`, then reports
recipe + tradfi/sports/pred feasibility). Manifests (all 5) already canonicalized + reconciled (cell-keyed, correct).

**Ordered completion (drive in this order; parallelise within a step):**
1. **defi migration working e2e** (sub-agent acb89f8f) → verify migrate-first→0 for defi (twin-audit). [GATE: proves the recipe]
2. **Fan out the recipe** to tradfi/sports/pred (parallel per-AG copy-drivers off each `legacy_dup_delete_list_{ag}.parquet`).
   tradfi dash-separated/pred-restructure shapes that are UN-mappable → re-download-or-bespoke (decide+document, don't fake).
3. **B3 — research-data copy across**: HL `perp_funding`/`perp_daily_ctx` (`perp-funding-*`) + LST (`lst-rates-*`) → canonical
   placement (+ manifest record_captured) + e2e doc (old→canonical mapping so e2e scripts repoint). Independent — can run ∥.
4. **Manifests reflect canonical** — re-verify all 5 live `_index` are cell-correct post-migration (already canonicalized;
   confirm no regression).
5. **Orphan check** — per AG, every captured cell has a canonical object (twin-audit migrate-first→0). THE gate for delete-safe.
6. **data_type + schema checking** — the migrated canonical objects carry the right data_type partition + parquet schema
   (sample-open per AG×data_type; confirm canonical objects == legacy content/schema, not just present).
7. **Reader cutover** — repoint deployment-api drilldown + MTDS readers to canonical `pipeline_mode=` ONLY, remove ALL
   legacy fallbacks / multiple-SSOT (safe once 5/6 complete per AG). cefi can cut over now.
8. **SIZE UP the final delete for ALL AGs** — re-run the twin-audit → per-AG SAFE-TO-DELETE delete-lists (legacy objs with
   verified canonical twins) + reclaimable bytes, written + summarized for operator inspection. **DO NOT DELETE** (operator
   holds this). Output: a ready-to-execute, operator-gated delete-list per AG (cefi already deleted).

**Hard-stop (operator):** the final DELETE of old data — prepare+size it, never execute.

## Operator follow-ups 2026-06-18 — research-data canonical-copy + instrument catalogue + MVP/total universe

> **Dependency order (operator 2026-06-18):** (B0) backfill instruments to NO-MISSING first → (B1) regen the instrument
> catalogue (it aggregates instruments) → (B2) codify MVP-universe vs total-reasonable-universe (so the backfill config
> + data-status "could-exist" are correct) — these gate/inform each other. Research-data canonical-copy (B3) is
> independent. Cross-links: `path_to_100pct_backfill_mtds_is_2026_06_17.md` (the backfill-to-100% home).

- [ ] [INFRA] P1. **B3 — copy e2e research data to CANONICAL placement + e2e doc**: HL `perp_funding`/`perp_daily_ctx`
      currently ONLY in the no-env-suffix research bucket `gs://perp-funding-central-element-323112/day=*/`; LST rates ONLY
      in `gs://lst-rates-central-element-323112/day=*/`. These are prod-needed data. (a) Determine the canonical home per
      data_type — the dedicated `-prd-` bucket (`lst-rates-prd`, exists) vs the market-data-tick-{cefi|defi}-prd canonical
      `pipeline_mode=` path (cefi already carries `pipeline_mode=batch_hyperliquid`; HL perp may be cefi-perp, LST is
      defi). (b) `gcs_copy_object` (workers=32, in-region) the research objects → canonical placement (+ manifest
      `record_captured` so the `_index` reflects them). (c) Write `e2e-testing/docs/` (or the e2e README) a note: research
      reads MUST migrate to the canonical sources — list the old→canonical bucket/path mapping so the e2e funding scripts
      (`staked_basis_funding_scan`/`colocated_engine`/etc.) update their fetch paths. Then the research buckets become
      deletable (operator-gated). — instruments-service/deployment-service + e2e-testing(doc)
- [ ] [INFRA] P1. **B1 — instrument catalogue regen + un-pause (aggregation/dedup; "has this instrument ever existed" +
      available-from/to)**: `instruments-service/scripts/build_instrument_catalogue.py` +
      `reference_data/catalogue/catalogue_builder.py` EXIST; Cloud Run jobs `lifecycle-catalogue-regen-{cefi,defi,tradfi,
      sports,prediction}` exist but the `*-daily` SCHEDULERS are **PAUSED** + last ran ~2026-06-11/15 (STALE, pre-backfill).
      AFTER B0 (instrument backfill no-missing): re-run the regen jobs per AG → verify the catalogue reflects the full
      deduped instrument lifecycle (genesis/first-seen/last-seen per instrument) → decide cadence + un-pause the daily
      schedulers (or keep manual). data-status "could-exist" + the expected_unattempted enumerator
      (`enumerate_expected_universe.py`) read this — stale catalogue = wrong could-exist universe. — instruments-service/deployment-service
- [ ] [DESIGN] P1. **B2 — codify MVP-universe vs TOTAL-REASONABLE-universe (NOT codified anywhere — confirmed gap)**: define
      in UAC (registry) the two distinct expected-universes so we know what we SHOULD have (drives the backfill config +
      data-status denominators): dimensions = base_currency × venue × data_type × (DeFi-pool by volume threshold) ×
      fixtures (sports) × combinations; canonical sources = hardcoded (chain genesis dates, VIX-index) vs
      download-derived (must have had the right fetch config to cover the full universe). **TOTAL-REASONABLE** = the full
      could-exist universe; **MVP** = the subset the May-23 archetypes need. Scan `path_to_100pct_backfill_mtds_is_2026_06_17.md`
      + the current `enumerate_expected_universe.py` + UAC registry for how far this exists + outliers; codify the gap as a
      UAC SSOT both the enumerator + the backfill config + data-status read from. — unified-api-contracts/instruments-service
- [ ] [DATA] P0. **B0 — backfill instruments to NO-MISSING (prereq for B1 catalogue + all expected-universe consumers)**:
      the F1/F2 instrument backfills below + the broader could-exist instrument backfill tracked in
      `path_to_100pct_backfill_mtds_is_2026_06_17.md`. Other services rely on instruments to know what's
      available/expected → this runs FIRST. — instruments-service

## GCS object-migration COMPLETE + delete-list sizing (2026-06-18) — DELETE IS OPERATOR-GATED

All legacy duplicate twins copied to canonical `pipeline_mode={mode}_{source}/asset_group={ag}/` shape via
`e2e-testing/scripts/defi/migrate_legacy_twins_from_audit.py` (server-side `gcs_copy_object`, workers=64, 0 errors).
Re-audit (`audit_legacy_gcs_dup_delete_list.py --ag defi,tradfi,sports,pred`) confirms **migrate-first → 0 on every
mappable cell** — every SAFE-TO-DELETE legacy object has a `gcs_describe`-verified canonical twin. Delete-lists written
to each AG `_index/audit/legacy_dup_delete_list_{ag}.parquet`.

| AG | copied twins | SAFE-TO-DELETE | reclaimable | unmappable residue (NO twin → stays legacy, NOT delete-safe) |
| --- | --- | --- | --- | --- |
| defi | 346,730 | 346,902 | 26.29 GB | 5,332 (7.34 GB) |
| tradfi | 1,705,230 | 1,705,230 | 113.30 GB | 1,102 (2.55 GB) |
| sports | 248,502 | 248,502 | 4.78 GB | 3,816 (0.23 GB) |
| pred | 573,451 | 573,451 | 24.35 GB | 0 |
| **TOTAL** | **2,873,913** | **2,874,085** | **168.72 GB** | **10,250 (10.11 GB)** |

Plus cefi (done earlier): fully migrated + 9.98 TB legacy deleted (operator-authorized, 7-day recoverable). The 10,250
unmappable are bare/no-venue legacy paths (`no_venue_or_data_type_in_path`/unparseable) with no derivable canonical
target → excluded from every delete-list (tracked P2 residual below). **DELETE of the 168.72 GB SAFE-TO-DELETE set is
operator-gated — sized + inspect-ready, NEVER auto-executed.**

## Autonomous-run residuals (2026-06-18, surfaced during the migration drive)

- [ ] [CODE] P1. **e2e funding scripts hardcode legacy research buckets — repoint to `resolve_bucket_name`**: B3 copied
      HL perp_daily_ctx/perp_mark_price → `perp-funding-prd` (e2e-testing@af084af) + shipped
      `docs/defi/research_data_canonical_sources_2026_06_18.md`. Repoint: `staked_basis_funding_scan.py:164-165`
      (`_HL_PF_BUCKET`/`_LST_BUCKET`), `funding_regime_classifier.py:46` (`PF_BUCKET`) → `resolve_bucket_name(...)`
      (`colocated_engine.py` already correct). Touches the live funding-arb path → strategy-service QG. — e2e-testing
- [ ] [INFRA] P2. **Research `-prd-` buckets carry NO `_index/`** — the live availability index still lives in the legacy
      `perp-funding`/`lst-rates` buckets; point the consolidator/readers at the `-prd-` index before the legacy research
      buckets are deleted (consolidator-runtime concern; B3 doc notes it). — deployment-service/instruments-service
- [ ] [DATA] P2. **Migration unmappable residue (bare/no-venue legacy paths, no canonical twin computable)**: defi 5,332 /
      tradfi 1,102 / sports 3,816 / pred 0 legacy objects have `no_venue_or_data_type_in_path` → the 1:1 copy-driver can't
      derive a canonical target. Decide per-shape: re-derive venue/data_type from file contents, or re-download, or accept
      as legacy-only (NOT delete-safe — exclude from every delete-list). — market-tick-data-service

## Phase A — subset violations (MTDS data with no instrument backing)

- [ ] [DATA] P1. **F1 — backfill instruments-service for CEFI venues MTDS has but instruments lacks historically**:
      `KRAKEN-SPOT`/`KRAKEN-FUTURES` (added to instruments only at day=2026-06-17 — ~6yr gap), `LIGHTER-ZKSYNC`,
      `PACIFICA-SOLANA`, `EXTENDED-STARKNET`. Re-run the IS daily-listing CLI across the MTDS-covered date range per
      venue (never copy between dates). Verify the cefi (venue,date) subset closes. — instruments-service
- [ ] [DATA] P2. **F2 — backfill 5 missing BITGET-FUTURES + 5 BITGET-SPOT instrument-days** that MTDS captured but
      instruments is absent for. — instruments-service
- [ ] [DATA] P1. **F4 — SPORTS: 2,107 captured MTDS cells with NULL `league_id`** (odds_horizon_bucket/trades/ODDS).
      Diagnose whether the league mapping drops on write or we capture non-canonised leagues; stamp league_id or route
      to honest-absence. No sports market data may be captured for a non-canonised league. — market-tick-data-service
- [ ] [DATA] P3. **F7 — DEFI: 19 Ethereum MTDS cells pre-instruments-genesis (2020-01-01..19)**. Confirm instruments
      defi genesis should start earlier, or mark those MTDS cells spurious. — instruments-service

## Phase B — instruments internal consistency

- [ ] [DATA] P0. **F3 — CEFI: 1.40M `attempted_failed` MTDS cells (36%)**. Break down by venue×data_type; diagnose the
      failing adapters/venues; backfill. (Data-pipeline-correctness heartbeat — no deferral.) — market-tick-data-service
- [ ] [CODE] P2. **F6 — TRADFI: 182k blank `instrument_type` + thin options (`options_chain` 3,287 vs `futures_chain`
      15,875)**. Phase-2 sub-agent opens tradfi instruments files to confirm whether options ARE listed but not captured
      (the "we list options but have no options data" case); fix the instrument_type stamping + close the options
      capture gap if real. — market-tick-data-service / instruments-service
- [x] ✅ [DATA] P2. **F5 — SPORTS INSTR index hygiene** — FIXED instruments-service@7b7d3a3 (new
      `scripts/canonicalize_instruments_store_index.py`). sports v2 projection: blank `capture_status` **6,869→0** (6,869
      malformed blank-data_type+blank-league rows dropped as no-shard-identity), `date='all'` **preserved (2, by-design
      reference entities)**, grain intact (35 league_ids in captured TEAMS). Verified independently. — instruments-service

## Phase C — file-level verification (Phase-2 sub-agents)

- [x] ✅ [AUDIT] P1. **Cross-year file sampling per AG — DONE** (5 per-AG sub-agents opened real GCS parquets across
      2020/2023/2026). Reframes + new findings folded into the audit doc + Phase D below. Reframes: **F3** cefi
      attempted_failed is ~1.3M legacy-recon NOISE + only ~88k genuine fetch-failure (not 1.4M); **F6** options ARE
      captured (CME 8,602 opts/day, ES options_chain 20,956 rows) — the "thinness" is a typing artifact, REFUTED;
      **F5** `date='all'` (2 rows) is by-design reference entities. Discarded one false sub-agent claim (cefi≠tradfi).

## Phase D — file-level correctness findings (Phase-2 sub-agents, NEW)

- [x] ✅ [DATA] P1. **N1 — CEFI phantom `empty_confirmed` shadow rows** — FIXED mtds@aaeada9. `_rebuild_cefi_cf11.py`
      now suppresses any blank-itype prior row whose 5-tuple (date,venue,data_type,instrument_id,underlying) is covered by
      a real object this run (`reemit_skipped_shadow`). Regenerated `projected_index_cefi_v2.parquet`: **371,010 shadows
      suppressed**; re-audit shows **captured∩empty shadow cells = 0** (was ~63k) + **captured∩failed = 0**. 33 unit tests
      (6 new). — market-tick-data-service
- [x] ✅ [DATA] P1. **N2 — TRADFI CME weekend dishonest-empty + 2×-per-cell dup** — FIXED instruments-service@7b7d3a3.
      ROOT CAUSE: the v8/v9 re-emit APPENDED a row per cell instead of replacing the stale `schema_version=4` legacy row →
      every cell carried captured v8/v9 + a blank-status v4 shadow (`instrument_id=None` vs `""` hid the dup). New
      `canonicalize_instruments_store_index.py` does grain-aware de-dup + classify (count>0→captured incl CME carry-forward;
      count==0→empty via `non_trading_day_reason` EXPECTED_WEEKEND/HOLIDAY). tradfi v2: rows **20,404→11,630**, blank
      capture_status **11,301→0**, 2-row cells **8,774→0**, CME weekends = EXPECTED_WEEKEND (183), **SOURCE_RETURNED_ZERO=0**.
      Verified independently. — instruments-service
- [x] ✅ [DATA] P0. **N3 — SPORTS league_id dropped** — FIXED mtds@aaeada9. REFRAME: the audit's "100% NULL-league"
      measured the PROJECTION; the live index had league_id on 169,380/202,087. Root cause: `_write_captured_rows` built
      the row_key but called `writer.add()` WITHOUT passing league_id. Fixed: carry league_id + shard dims into add();
      `_source_from_row` now resolves sports `trades`→`odds_api` + case-insensitive bridge. `projected_index_sports_v2`:
      null-league **202,087→32,707**, NULL source **73.7k+→6** (202,081 stamped odds_api). 28 tests (3 new). Residual
      tail (32,707 genuinely-null in LIVE + 6 null-source) → N3a/N3b below. — market-tick-data-service
- [x] ✅ [DATA] P2. **N4 — SPORTS instruments `instrument_count==0`** — CONFIRMED NOT-A-DEFECT (instruments-service@7b7d3a3
      investigation). The per-league companion rows are correctly `captured`; the `instrument_count==0` is a count-DISPLAY
      artifact (the global count lands on one row), not a capture-status error. Left untouched — no fabricated counts
      (per-league grain + companion rows preserved in the v2 projection). — instruments-service
- [x] ✅ [DATA] P1. **N5 — DEFI pre-launch `vault_share_price`** — FIXED (code mtds@3f5cc6e: rebuild routes pre-launch +
      0-row vault cells via launch-date `EXPECTED_PRE_VENUE_LAUNCH` / `SOURCE_RETURNED_ZERO` honest-absence). Live cefi/defi
      manifests canonicalized via `canonicalize_mtds_index.py` (mtds@d7b04b2) APPLIED to live 2026-06-18: defi 97 ETHENA
      pre-launch (2023-11→2024-02) reclassified captured→empty. **Residual** (rebuild-for-real-replace, tracked N5r below):
      the VAULT 2020-2022 0-row phantoms (~1,113) need the per-object rebuild applied to live (the index-walk can't open
      files). — market-tick-data-service
- [x] ✅ [CODE] P1. **N6 — DEFI dimension normalization** — itype case FIXED (live: `POOL`→`pool`, 2,450 collapsed via
      canonicalize_mtds_index@d7b04b2 APPLIED). venue-spelling dedup CODE shipped (mtds@cf63cf6: `_canonical_defi_venue`
      replicates the migrator so manifest venue==object-path venue — SAFE only in the per-object rebuild, NOT the
      index-walk). **Residual N6r below.** — market-tick-data-service
- [ ] [DATA] P2. **N5r/N6r — DEFI rebuild-for-real-replace to land venue-dedup + VAULT-0-row + 496 chain-pollution on
      LIVE**: the per-object rebuild (mtds@3f5cc6e/cf63cf6) normalizes venue + detects 0-row vaults + would clean the 496
      `chain`-pollution rows (token-pairs ETH-USDC/1INCH-ETH in `chain`, all attempted_failed UNISWAP_V4 swaps_ohlcv), but
      reaching LIVE needs a WHOLESALE replace of the defi `_index` (the consolidator merge leaves stale un-normalized rows;
      the index-walk can't normalize venue without desyncing from object paths). Run the rebuild to produce the full v9
      index + write it as the live `_index` (replace, not merge). NOT a double-count/data-loss (P2 grouping hygiene). — market-tick-data-service
- [x] ✅ [DATA] P0. **F3 (reframed) — CEFI re-classify legacy-recon `attempted_failed`** — FIXED mtds@aaeada9.
      `_rebuild_cefi_cf11.py`: shadow legacy rows (covered by a real object) suppressed (part of the 371,010 shadows);
      non-shadow `LEGACY_THIRDKEY_DRIFT_RECON_2026_05_07` dropped as un-keyable drift duplicates (**243,828 dropped**);
      `LegacyBlankErrorReasonError`→`UNCLASSIFIED_ADAPTER_ERROR` preserved (visible/backfill-worthy). attempted_failed
      **1.40M→782,005** in `projected_index_cefi_v2`. Genuine `VENUE_FETCH_FAILED`(83,975)+`HTTP_429`(3,652) preserved →
      backfill Step 9. The ~698k UNCLASSIFIED reconcile-to-expected_unattempted is N1b (depends Step 4). — market-tick-data-service
- [ ] [CODE] P2. **F6 (reframed) — TRADFI option/instrument_type encoding**: unify the two options encodings
      (`instrument_type=options_chain` vs `data_type=options_chain` w/ blank type) + stamp instrument_type on the 182k
      blank-type cells (legacy path shapes). Not missing data — a typing fix. — market-tick-data-service
- [x] ✅ [INFRA] P3. **N7 / Step-5 prefix_tpls VERIFY — DONE (no code change needed)**: `reconcile_phantom_manifest_rows_all.py`
      `prefix_tpls = canonical_path_templates(ag)` (CF-15/V0 UAC SSOT) for cefi/defi/tradfi/prediction — VERIFIED complete:
      enumerates every coexisting shape (`pipeline_mode=batch_<source>/`, bare `asset_group=`, legacy `category=`,
      top-level `day=`, defi `venue=PROTOCOL-CHAIN` overload + bare-venue). **Sports `[""]` is NOT a foot-gun** — sports
      routes to the dedicated `_audit_sports` + UAC `candidate_parquet_paths` SSOT (bucket kind=instruments-store), and
      ALL 17 captured instruments-store-sports data_types (STANDINGS/TEAMS/FIXTURES/ODDS/…) resolve ≥1 candidate path.
      `--apply` will NOT mass-flip on any AG from a prefix-coverage gap. — instruments-service
- [ ] [DATA] P3. **N8 — PRED index data_type label drift** (`prediction_canonical_question_group` vs GCS
      `prediction_trades`/`trades`) + 1 blank-reason attempted_failed cell. Confirm intentional rollup label vs drift;
      type the blank reason. — market-tick-data-service
- [ ] [DATA] P1. **N1b — CEFI: reconcile the ~698k `UNCLASSIFIED_ADAPTER_ERROR` (ex-`LegacyBlankErrorReasonError`,
      blank-itype) attempted_failed cells against the IS expected-universe (Step 4 enumerator) + reconcile (Step 8)**:
      cells the enumerator marks `expected_unattempted` (instrument not listed / pre-coverage) should drop the stale
      failed row; genuine in-coverage listed-instrument gaps stay attempted_failed → backfill (Step 9). DEPENDS on Step 4.
      (Provenance: Step-1 fix kept them visible rather than hide a gap; final fate is enumerator+reconcile-driven.) — market-tick-data-service
- [ ] [DATA] P2. **N3a — SPORTS: 32,707 captured cells genuinely NULL-league in the LIVE index** (schema_version=8;
      venue=bookmaker/ODDS_API, data_type=trades/ODDS/odds_horizon_bucket). The Step-2 fix recovered the 169,380 cells that
      HAD league; these 32,707 lost it at WRITE time. Recover league_id by joining each null-league captured (date,venue,
      data_type) to the GCS object paths (`league_id=<L>`) for that cell — needs a sports object scan (the rebuild is
      index-driven). No sports market data may be captured for an unattributed league. — market-tick-data-service
- [ ] [DATA] P2. **N9 — MTDS SPORTS (market-data-tick-sports) 17,288 blank-capture_status rows** (pre-existing CF-10
      reference/phantom set; surfaced in the 2026-06-18 final live-manifest verify — distinct from the instruments-store
      sports blanks F5 which ARE fixed). Classify via a sports-MTDS canonicalize pass (extend `canonicalize_mtds_index.py`
      to sports, mirroring the instruments-store classify: reference blank-data_type rows kept; real-data_type phantoms →
      honest status). NOT a double-count. captured (202,087, league_id present) + empty (584,257) already correct. — market-tick-data-service
- [ ] [CODE] P0. **READER-SHAPE GAP — deployment-api drilldown reads the BARE (legacy) shape, NOT canonical
      `pipeline_mode=` (DELETE-PREREQUISITE, found 2026-06-18)**: `deployment_api/services/shard_detail/_shard_core.py`
      (the `DATA_STATUS_CANONICAL_PATHS_ONLY` cutover @6bcac01) builds the probe prefix
      `raw_tick_data/by_date/day={D}/asset_group={ag}/…` — NO `pipeline_mode=` segment → it matches ONLY the legacy bare
      objects we are about to DELETE, not the canonical `…/pipeline_mode={mode}_{source}/asset_group={ag}/…` twin. The
      headline data-status COUNTS are unaffected (manifest cell-keyed), but the file-detail DRILLDOWN would orphan/blank
      post-delete. **Repoint the probe to the canonical `pipeline_mode=` shape** (list `day={D}/` + match
      `pipeline_mode=*/asset_group={ag}/`, or prepend the derived `pipeline_mode={mode}_{source}/`) BEFORE any legacy
      delete. Same check the deployment-api drilldown `_instruments.py` + any other GCS-listing reader. — deployment-api
> **🟢 RESCAN COMPLETE + INDEPENDENTLY VERIFIED (2026-06-18).** Full twin-walk of all 5 market-data-tick buckets
> (`e2e-testing/scripts/defi/audit_legacy_gcs_dup_delete_list.py`@a294b2c; per-AG maps at
> `_index/audit/legacy_dup_delete_list_{ag}.parquet`; findings PM PR #403). **CRITICAL: only cefi is actually migrated.**
> cefi = 1,077,672 SAFE-TO-DELETE (~9.98 TB, byte-identical `pipeline_mode=` twins — I spot-verified 5/5 size-match) +
> 15 migrate-first. **defi (352,062) / tradfi (1,706,332, incl VIX) / sports (252,318) / pred (573,451) = ALL MIGRATE-FIRST
> (~179 GB, NO canonical twin — verified 3/3 tradfi have twin_exists=False)** — their canonicalisation never completed /
> was a RESTRUCTURE (pred renamed keys+stems; tradfi bulk is dash-separated non-hive never canonicalised), so the legacy
> objects are the LIVE copy → deleting them LOSES DATA. **Only cefi is delete-safe today.** e2e 48h research data: CLEAN —
> HL perp_funding/perp_daily_ctx in standalone `perp-funding-*` bucket + LST in `lst-rates-*` (BOTH out of the 5 in-scope
> buckets); cefi funding reads the canonical `pipeline_mode=batch_tardis` (the safe-delete list is their legacy twin →
> delete preserves reads); Aster/Drift re-downloadable; no runaway/unaccounted data, no DANGER flag. **Corollary for the
> reader-repoint (P0 above): canonical-only `pipeline_mode=` reads work ONLY for cefi today; defi/tradfi/sports/pred would
> orphan EVERYTHING under canonical-only until their objects are migrated → the per-AG OBJECT migration is now a hard
> prerequisite for BOTH their canonical-only reads AND their legacy delete.**

- [ ] [INFRA] P0. **Migrate-first the 4 un-migrated AGs' OBJECTS to canonical `pipeline_mode=` shape (defi/tradfi/sports/
      pred, ~2.88M objects / 179 GB)** — their canonical migration never completed (tradfi never hive-canonicalised; pred
      restructured; defi/sports partial). Run/complete `migrate_{defi_full,tradfi}_to_v9_canonical.py` (+ sports/pred
      equivalents) on in-region VMs (gcs_copy_object workers=32) to create the canonical twins, then re-run the twin-audit
      → 0 migrate-first per AG. ONLY THEN are those AGs' canonical-only reads orphan-free + their legacy objects
      delete-safe. cefi needs NONE of this (already twinned). — market-tick-data-service / deployment-service
- [x] ✅ [INFRA] P1. **Phase D rescan + delete-list — DONE + verified.** cefi SAFE-TO-DELETE list ready for operator
      inspection (`legacy_dup_delete_list_cefi.parquet`, 1,077,672 objs / ~9.98 TB, exclude the 15 migrate-first); the
      other 4 AGs are migrate-first (above), NOT deletable yet. e2e research data accounted-for + safe. Deletion remains
      OPERATOR-GATED (inspect→confirm→delete).
- [ ] [INFRA] P1. **Phase D — DELETE legacy GCS dupes (OPERATOR-GATED, cefi-only today)**: the bare
      `raw_tick_data/by_date/day=*/asset_group={ag}/...` objects are EXACT duplicates of canonical
      `pipeline_mode={mode}_{source}/asset_group={ag}/...` twins (verified: same instrument exists at both). They no longer
      cause UI double-count (data-status reads the cell-reduced manifest + deployment-api@6bcac01 drilldown is
      canonical-only). Procedure: per AG, list bare `day=*/asset_group=` objects → verify each has a `pipeline_mode=` twin
      (via `gcs_describe_object`) → write the delete-list to `_index/audit/legacy_dup_delete_list_{ag}.txt` → **OPERATOR
      INSPECTS + confirms** → `gcs_delete_object` the confirmed bare twins (in-region VM, workers=32). Storage reclamation
      only; do NOT delete any bare object lacking a canonical twin (that would be unmigrated → migrate it first). — instruments-service/deployment-service
- [ ] [DATA] P3. **N3b — SPORTS: 6 captured cells still NULL source** (ARBITRAGE_OPPORTUNITY/ODDS_MOVEMENT/ODDS_SNAPSHOT,
      2 each) after the Step-2 `trades→odds_api` + case-insensitive bridge. Add these MDPS-derived data_types to the
      source bridge (or route to honest absence if not genuinely captured). — market-tick-data-service
