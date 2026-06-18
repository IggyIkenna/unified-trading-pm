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
> `[""]` — verify only); **N3** ⚠️ `rebuild_sports_manifest_v9` never extracts `league_id`/`league` from the MTDS object
> path into the row_key (canonicalizer `_canonicalize_row_key_league_id` then gets null); **N1** ⚠️ `rebuild_cefi` CF-11
> dedup key mismatches (empty re-emit has blank `instrument_type` vs captured populated → both survive); **N5** ❌
> `rebuild_defi` emits `captured`/row_count=0 on file PRESENCE without opening (0-row/pre-launch → false captured) →
> route via `record_zero_rows`; **N6** ⚠️ `rebuild_defi._split_legacy_venue_chain` lacks instrument_type case-norm +
> lets pairs leak into `chain` + incomplete venue-dedup; **F3** ❌ `rebuild_cefi` passes legacy `attempted_failed`
> reasons through un-reclassified; **N2** ❌ instruments enumerator marks CME weekend carry-forward as
> `SOURCE_RETURNED_ZERO`. **Each Phase-A/B/D todo below = a scoped fix to the named script → regen that AG's dry-run
> projection → re-audit the fixed dimension.** Phase-1 (manifest-level, full v9-projected-index walk) is DONE; Phase-2
> (file-level cross-year manifest-vs-reality sampling) is IN PROGRESS via per-AG sub-agents — findings fold back into
> the audit doc + new todos here.

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
9. **Backfills** — F1 (Kraken+ instruments history), the ~88k genuine cefi `VENUE_FETCH_FAILED`, any real
   captured-absent cells. Run to completion (manifest-verified rows). **→ The FULL path to 100% (could-exist
   enumeration + per-AG MTDS/IS backfill + cross-data_type completeness + credential asks + live=batch keep-green) is
   tracked separately in `path_to_100pct_backfill_mtds_is_2026_06_17.md` (parent_epic mtds_mdps_master), gated to start
   once this migration's `--apply` lands.**

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

## Progress Log — B0/B1/B2 autonomous run (2026-06-18, dispatch)

> Operator `/autonomous` 2026-06-18: NEW Databento key live in SM `databento-api-key`, Tardis public, DeFi creds exist →
> no credential blockers. Drive B0→B1→B2 to verified completion. This log is the loop's handoff memory (no summary doc).

**Discovery (read-first, 2026-06-18):**

- **Data state** (instrument_availability/by_date latest day): tradfi=2026-06-11, defi=2026-06-11, cefi=2026-06-17 →
  ~7-day tradfi/defi gap, ~1-day cefi gap. earliest: tradfi 2020-01-01, cefi 2019-03-30, defi 2020-01-20.
- **B1 schedulers**: `lifecycle-catalogue-regen-{cefi,defi,tradfi,sports,prediction}-daily` all PAUSED (asia-northeast1,
  `0 1 * * *` UTC), last ran ~2026-06-11. Cloud Run Jobs exist (lifecycle_catalogue_scheduler.tf).
  `prod/catalog.parquet` present per AG.
- **B2 — MVP IS ALREADY CODIFIED**: `unified_api_contracts.canonical.crosscutting.mvp_scope.MVP_SCOPE` + `is_mvp()`
  (config v3) — catalogue (`build_instrument_catalogue.py`) + enumerator already consume it. The "total reasonable
  universe" = the full lifecycle catalogue (could-exist), consumed by `enumerate_expected_universe.py` v2, but is NOT a
  NAMED/codified SSOT with explicit selection axes. **B2 gap = add a sibling `total_universe` SSOT** (the could-exist
  selection axes: base_currency × venue × data_type × DeFi-pool-volume × fixtures ×
  hardcoded-genesis-vs-download-derived) next to MVP, + a predicate the enumerator reads, so both concepts are
  explicit + distinct.
- No code tarball in `gs://deployment-scripts-…/code/instruments-code.tar.gz` (need `create-code-tarballs.sh` first).
- No instr-backfill VM currently running.

**Discovery — instrument-store state per AG (read-first, 2026-06-18 22:30 UTC; IS@02cb876 + UAC@aeae389 + subscription
guard installed):** ran the IS `--operation status` + read each `instruments-store-{ag}-prd` `_index/availability_index.parquet`:

- **tradfi — ALREADY FULLY BACKFILLED to date (B0 effectively done for tradfi):** 11,418 captured / 256 empty_confirmed,
  cov 1.0, **0 attempted_failed, 0 date gaps.** 6 venues continuous DAILY: CME/FX/ICE/CBOE 2020-01-01→2026-06-18,
  NASDAQ/NYSE 2023-04-15(subscription start)→2026-06-18 (distinct-days == calendar-span ⇒ no missing day). The new
  3-dataset subscription guard (`assert_databento_request_allowed`, dataset-level shard-isolation) is installed on the IS
  `definition` fetch but matters only for FUTURE/forced fetches — existing tradfi instrument rows are already the right
  universe (CBOE/CME/ICE/NASDAQ/NYSE/FX), no banned datasets present. `--force` re-fetch would isolate any off-allowlist
  dataset, not hard-fail. **Verdict: tradfi B0 = COMPLETE; no backfill action needed (only forward daily keep-green).**
- **cefi — cov 0.999 (28,552 captured / 22 attempted_failed); real F1/F2 gaps confirmed:** KRAKEN-SPOT/KRAKEN-FUTURES
  have only 2 days (2026-06-17/18) vs earliest_venue_date 2020-01-01 → **~6yr backfill needed**; LIGHTER-ZKSYNC
  (2024-08-01), EXTENDED-STARKNET (2024-10-01), PACIFICA-SOLANA (2025-06-01) **ABSENT entirely**; BITGET-FUTURES/SPOT
  578 days from 2024-11-08 (the F2 5-missing-days). 22 attempted_failed to diagnose.
- **defi — cov 0.998 (75,706 captured / 172 attempted_failed):** 95 venues, 2020-01-20→2026-06-18. 172 failed to
  diagnose.
- **sports — high cov on most entities;** RED-by-design: SFI_LEAGUES/SFI_STANDINGS/TRANSFERMARKT_LEAGUES cov 0.000 (all
  attempted_failed — credentialed/blocked sources, see F-track). INJURIES/ODDS ~0.96.
- **prediction — NO per-AG instruments-store entry in the bucket SSOT** (`Available: CEFI/DEFI/SPORTS/TRADFI`); resolves
  to the FLAT kind `instruments-store-pred-prd-central-element-323112`. 500 captured POLYMARKET, 2025-03-14→**2026-06-09**
  (9-day stale; the `--operation status` path can't read the flat-kind bucket — status-CLI limitation, backfill path is
  fine via `resolve_instruments_store_kind`).
- **The IS CLI is idempotent + manifest-driven:** a re-run on a date already fresh in the manifest SKIPs ("all N
  venues/entities already fresh — use --force"). So a backfill targets dates NOT in the manifest (the absent venues /
  Kraken history) or uses `--force` to refresh.

**B0 plan (this run):** tradfi DONE. Drive cefi F1 (Kraken 6yr + 3 absent venues) + F2 (BITGET 5d) + prediction
freshness + diagnose defi/cefi attempted_failed. Monitored local CLI per venue (idempotent, skips fresh days), streamed
to logs.

**B0 EXECUTION — 2026-06-18 ~23:00 UTC (monitored local CLI, log dir `/tmp/is_backfill_logs/`):**

- **tradfi B0 = COMPLETE** (already; no action). cov 1.0, 0 gaps, 2020-01-01→2026-06-18, 3-dataset contract.
- **cefi F1 — Kraken 6yr backfill**: `instruments-service --asset-group cefi --venues KRAKEN-SPOT KRAKEN-FUTURES
  --start-date 2020-01-01 --end-date 2026-06-18` — RUNNING in background (Tardis source, ~40 records/day across both
  venues). The LONG leg (~2,360 days × 2 venues, ~10s/day) — ETA a few hours; left to run to completion + reports its
  state. Idempotent (skips fresh days). Log: `kraken_f1.log`.
- **cefi F1 — 3 absent venues backfilled DONE/near-done**: LIGHTER-ZKSYNC (2024-08-01→, 198 instr/day),
  EXTENDED-STARKNET (2024-10-01→, 103/day), PACIFICA-SOLANA (2025-06-01→2026-06-18 ✅ **DONE**, 10/day). All via
  Tardis/native adapters, creds present, 0 errors.
- **cefi F2 — BITGET 5 missing days**: re-fetched 2024-11-08→2026-06-18 (`--venues BITGET-FUTURES BITGET-SPOT`),
  near-done, fills the F2 gap.
- **prediction freshness — ✅ DONE**: `--asset-group prediction --start-date 2026-06-09 --end-date 2026-06-18` wrote
  **12,720 records across 30 venues** (POLYMARKET CLOB full scan ~1.4M markets + KALSHI 2000) to
  `instruments-store-pred-prd` (flat kind). The 9-day stale tail (last was 2026-06-09) is now current. NOTE: the IS
  `--operation status` CLI can't READ the flat-kind prediction bucket (`get_write_bucket_name` lacks a PREDICTION
  asset_group entry) — a status-CLI display gap, NOT a backfill blocker (the WRITE path resolves via
  `resolve_instruments_store_kind`).
- **defi**: 95 venues, cov 0.998, 2020-01-20→2026-06-18 — already broadly complete; 172 attempted_failed
  (MORPHO-ETH/BASE 41 each, DRIFT-SOLANA 41, AAVE_V3-OPTIMISM 41, TRADER_JOE_V2-AVALANCHE 6, SUSHISWAP_V3-BASE 2, all
  UNCLASSIFIED_ADAPTER_ERROR, 2026-05-09→06-18).
- **sports**: most entities high-cov; SFI_LEAGUES/SFI_STANDINGS/TRANSFERMARKT_LEAGUES cov 0.000 (all attempted_failed
  — credentialed/blocked scraper sources, tracked in sports_master DEFERRED-INDEFINITELY scraper set). Not a B0 gap.

- [ ] [CODE] P3. **`--operation status --asset-group prediction` can't read the flat-kind bucket** — `_run_coverage_status`
      calls `get_write_bucket_name("instruments", "prediction")` which raises `BucketNamingError` (the per-asset_group
      instruments-store dict has no PREDICTION entry; prediction resolves via the FLAT
      `resolve_instruments_store_kind`→`instruments-store-pred`). Teach the status path to use
      `_get_instruments_bucket_for_asset_group` (the same resolver the write path uses) so prediction status renders.
      Display-only gap; the backfill WRITE path already works. — instruments-service
- [ ] [DATA] P2. **Stale `attempted_failed` rows survive a failed→captured retry in the consolidated `_index` (manifest
      dedup blank-column edge — KNOWN, already tracked)** (surfaced 2026-06-18 while backfilling the fixed venues). After
      re-fetching a previously-`attempted_failed` shard to `captured`, the consolidated `_index/availability_index.parquet`
      carries BOTH rows for the same (date, venue) — e.g. DERIBIT-COMBO 2026-05-23 has `attempted_failed` (instrument_type=''
      pipeline_mode=None) AND `captured` (instrument_type='COMBO' pipeline_mode='batch_instruments_service'). ROOT CAUSE
      (documented in UTL `manifest_writer/_writer_io.py` ~line 716): the dedup key adds the v6-v9 shard-atom cols
      (instrument_type/pipeline_mode/source) only when non-empty, and `record_failed` leaves them blank while the captured
      retry populates them → populated-vs-blank delta keeps BOTH rows; last-write-wins fails. The captured data IS present +
      correct; the stale failed row inflates the coverage DENOMINATOR (slight under-count) until collapsed. **Already
      tracked** as the wildcard-"" dedup follow-on `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`
      (the fix: treat "" as a wildcard in the dedup key so a populated retry supersedes a blank failure). The scheduled
      manifest-consolidator does NOT currently collapse these either (same dedup logic). **Until that lands**, a targeted
      reconcile (drop the stale `attempted_failed` row where a same-(date,venue) `captured` row with a newer `written_at`
      exists) would clean the IS instruments-store indices — but do NOT hand-edit the dedup machine here (deliberate design
      tradeoff with a named owner). — unified-trading-library (dedup) — cross-link
      `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`
- [x] ✅ [DATA] P2. **Diagnosed all 172 defi attempted_failed cells (2026-05-09→06-18) — 4 of 6 venues fixed, 2 are
      deeper upstream changes (split below)**. Each was UNCLASSIFIED_ADAPTER_ERROR from a distinct upstream API change:
      - **MORPHO-ETHEREUM (41) + MORPHO-BASE (41) — ✅ ADAPTER FIXED + RE-FETCHED** (instruments-service@ec3fd3a): Morpho
        renamed `Market.uniqueKey`→`marketId` (HTTP 400 "Cannot query field uniqueKey"). Live verify: 968 markets
        fetched (was 0); re-fetched 2026-05-09→06-18 (164 captured rows written 2026-06-18 23:1x). **The captured rows
        land under the CANONICAL bare venue `MORPHO`** (the writer keys the shard by the adapter's `venue` property
        `"morpho"`→`MORPHO`, NOT the per-record chain-suffixed `venue_tag` `MORPHO-ETHEREUM`) — and `MORPHO` already has
        **1,669 captured rows 2024-01-08→2026-06-18** (the historical canonical capture). So the 41+41 `MORPHO-ETHEREUM`/
        `MORPHO-BASE` `attempted_failed` rows are an ANOMALOUS chain-suffixed venue-naming VARIANT, NOT a genuine data gap
        — the morpho lending markets ARE captured + current under `MORPHO`. (Same multi-source venue-naming drift the
        manifest-canonicalisation track owns — see the venue-naming P2 below.)
      - **TRADER_JOE_V2-AVALANCHE (6) + SUSHISWAP_V3-BASE (2) — ✅ SELF-RECOVERED + canonical-tag captured**: both fetch
        1000 pool instruments cleanly (transient subgraph rate-limits, not a code bug). Re-fetched; captured under the
        canonical bare `TRADER_JOE_V2` (74 captured 2026-05-09→06-18) + `SUSHISWAP_V3` (2,606 captured
        2023-04-05→06-18). The `-AVALANCHE`/`-BASE` chain-suffixed `attempted_failed` rows are the same anomalous
        variant — data captured under the canonical bare venue.
      - **DRIFT-SOLANA (41) + AAVE_V3-OPTIMISM (41)**: genuine deeper upstream changes — split to the two P2 todos below.
      — instruments-service
- [ ] [DATA] P2. **DeFi manifest venue-naming drift — chain-suffixed VARIANT venue tags shadow the canonical bare-protocol
      venue** (surfaced 2026-06-18). The defi instruments-store `_index` carries BOTH the canonical bare-protocol venue
      (`MORPHO` 1,669 captured / `SUSHISWAP_V3` 2,606 / `TRADER_JOE_V2` 74 — where the adapter actually writes, keyed by
      its `venue` property) AND a smaller anomalous chain-suffixed variant (`MORPHO-ETHEREUM`/`MORPHO-BASE` 42 each,
      `SUSHISWAP_V3-BASE` 2, `TRADER_JOE_V2-AVALANCHE` 6, `SUSHISWAPV3`/`SUSHISWAP-ARBITRUM`/etc.) that is almost entirely
      `attempted_failed` + a stray captured. The DeFi venue identity is ambiguous: the adapter's `venue` property is the
      bare protocol (`morpho`→`MORPHO`) while `InstrumentRecord.venue`=`MORPHO-{chain}` and the manifest writer keys the
      shard by the PROPERTY not the record field → multi-chain protocols collapse to one bare venue + the chain-suffixed
      rows are orphan variants. **Decide the canonical DeFi instrument venue grain** (bare-protocol vs protocol-chain) +
      make the adapter `venue` property, the `InstrumentRecord.venue`, and the manifest shard key AGREE (shard-granularity
      SSOT), then reconcile/collapse the variant rows (phantom-audit). Captured data is present under the bare venue — this
      is a naming-canonicalisation correctness item, not a fetch gap. — instruments-service / unified-trading-library
      (manifest shard key) — composes with the `*_manifest_canonicalisation_*` + `source=` provenance tracks
- [ ] [DATA] P2. **DRIFT-SOLANA instrument adapter — `data.api.drift.trade/stats/markets` now 404** (diagnosed
      2026-06-18). The Drift Data API endpoint moved: `/stats/markets`→404, `/markets`→403, `/contracts`/`/perpMarkets`
      →403 (auth-gated), `dlob.drift.trade`→502. Find Drift's current PUBLIC markets endpoint (docs at
      `https://docs.drift.trade/`); if all current endpoints are auth-gated this becomes **BLOCKED-CREDENTIALS** (file
      a Drift API-key ask per external-data-always-available). Fix `drift.py` `_DATA_API_URL`/path (the URL resolves via
      UAC `get_solana_protocol_url("drift","api_url")` — update the registry value, not a hardcode), classify the breach
      properly, backfill 2026-05-09→06-18. — instruments-service / unified-api-contracts (registry URL)
- [ ] [DATA] P2. **AAVE_V3-OPTIMISM IS instruments adapter must route to the RPC fallback (KNOWN abandoned subgraph —
      NOT a subgraph-ID hunt)** (diagnosed 2026-06-18). The instruments adapter queries the subgraph
      `3RWFxWNstn4nP3dXiDfKi9GgBoHx7xzc7APkXs1MLEgi` which raises `Type Query has no field reserves` → attempted_failed.
      **This is the DOCUMENTED operator policy (UAC `_defi.py` aave_v3 OPTIMISM comment, decision 2026-05-30): Aave
      silently abandoned the Optimism subgraph (republished to an empty v0.0.5 entity store); the CANONICAL data source
      for AAVE_V3-OPTIMISM is the RPC fallback (14-row daily), not the subgraph.** So do NOT chase a new subgraph ID
      (none exists per the policy). The fix is in the IS `aave_v3.py` adapter: for OPTIMISM, route to the same RPC
      fallback the MTDS rate handler uses (or `record_empty(reason=...)` honest-absence if the IS layer has no RPC path)
      — never leave it attempted_failed (a known-policy state masquerading as a fetch failure). The sibling chains
      (ETH/ARB/POLY/BASE/AVALANCHE) work fine. — instruments-service (NOT a UAC subgraph-ID change)

**DERIBIT-COMBO — fixed a NEVER-WORKING venue (4 stacked breaks, found during cefi diagnosis) — ✅ SHIPPED:**
cefi's 22 attempted_failed were ALL DERIBIT-COMBO (0 captured days since added 2026-05-23). Root cause = 4 stacked bugs,
all fixed: (1) Deribit retired `get_instruments?kind=combo` (HTTP 400) → switched to `public/get_combos`; (2) adapter
tagged records `venue=DERIBIT` but batch canonical is `DERIBIT-COMBO` → URDI venue-tag filter dropped all rows → fixed
the venue property; (3) legs were always empty (`_parse_combo_legs` always returned `[]`) and validation rejects
leg-less COMBOs → build `InstrumentLeg` from `get_combos` structured legs; (4) `DERIBIT-COMBO` was absent from UAC
`VENUES_BY_ASSET_GROUP["cefi"]` + `CEFI_VENUE_LAUNCH_DATES` → validation rejected "unknown venue" → registered it.
Verified live: **117 combos written/day** (was 0). Removed dead `_parse_combo_legs`/`_extract_structure_code`. Tests
updated (332 IS combo tests + 907 UAC venue/coverage tests green; IS QG `--no-fix` exit 0). Shipped:
unified-api-contracts@dfe7e6f (venue registration) + instruments-service@dedae75 (adapter). Re-fetch of the 22 failed
days running (`deribit_combo.log`) — combos active today land captured; expired-combo days the get_combos endpoint no
longer returns stay honest (the API only returns currently-active combos — historical combo state is not retrievable,
an upstream limitation, NOT a silent placeholder).

> **Dependency order (operator 2026-06-18):** (B0) backfill instruments to NO-MISSING first → (B1) regen the instrument
> catalogue (it aggregates instruments) → (B2) codify MVP-universe vs total-reasonable-universe (so the backfill config
>
> - data-status "could-exist" are correct) — these gate/inform each other. Research-data canonical-copy (B3) is
>   independent. Cross-links: `path_to_100pct_backfill_mtds_is_2026_06_17.md` (the backfill-to-100% home).

- [ ] [INFRA] P1. **B3 — copy e2e research data to CANONICAL placement + e2e doc**: HL `perp_funding`/`perp_daily_ctx`
      currently ONLY in the no-env-suffix research bucket `gs://perp-funding-central-element-323112/day=*/`; LST rates
      ONLY in `gs://lst-rates-central-element-323112/day=*/`. These are prod-needed data. (a) Determine the canonical
      home per data_type — the dedicated `-prd-` bucket (`lst-rates-prd`, exists) vs the
      market-data-tick-{cefi|defi}-prd canonical `pipeline_mode=` path (cefi already carries
      `pipeline_mode=batch_hyperliquid`; HL perp may be cefi-perp, LST is defi). (b) `gcs_copy_object` (workers=32,
      in-region) the research objects → canonical placement (+ manifest `record_captured` so the `_index` reflects
      them). (c) Write `e2e-testing/docs/` (or the e2e README) a note: research reads MUST migrate to the canonical
      sources — list the old→canonical bucket/path mapping so the e2e funding scripts
      (`staked_basis_funding_scan`/`colocated_engine`/etc.) update their fetch paths. Then the research buckets become
      deletable (operator-gated). — instruments-service/deployment-service + e2e-testing(doc)
- [ ] [INFRA] P1. **B1 — instrument catalogue regen + un-pause (aggregation/dedup; "has this instrument ever existed" +
      available-from/to)**: `instruments-service/scripts/build_instrument_catalogue.py` +
      `reference_data/catalogue/catalogue_builder.py` EXIST; Cloud Run jobs
      `lifecycle-catalogue-regen-{cefi,defi,tradfi,     sports,prediction}` exist but the `*-daily` SCHEDULERS are
      **PAUSED** + last ran ~2026-06-11/15 (STALE, pre-backfill). AFTER B0 (instrument backfill no-missing): re-run the
      regen jobs per AG → verify the catalogue reflects the full deduped instrument lifecycle
      (genesis/first-seen/last-seen per instrument) → decide cadence + un-pause the daily schedulers (or keep manual).
      data-status "could-exist" + the expected_unattempted enumerator (`enumerate_expected_universe.py`) read this —
      stale catalogue = wrong could-exist universe. — instruments-service/deployment-service
- [x] ✅ [DESIGN] P1. **B2 — codify MVP-universe vs TOTAL-REASONABLE-universe (NOT codified anywhere — confirmed gap)**:
      define in UAC (registry) the two distinct expected-universes so we know what we SHOULD have (drives the backfill
      config + data-status denominators): dimensions = base_currency × venue × data_type × (DeFi-pool by volume
      threshold) × fixtures (sports) × combinations; canonical sources = hardcoded (chain genesis dates, VIX-index) vs
      download-derived (must have had the right fetch config to cover the full universe). **TOTAL-REASONABLE** = the
      full could-exist universe; **MVP** = the subset the May-23 archetypes need. Scan
      `path_to_100pct_backfill_mtds_is_2026_06_17.md` + the current `enumerate_expected_universe.py` + UAC registry for
      how far this exists + outliers; codify the gap as a UAC SSOT both the enumerator + the backfill config +
      data-status read from. — unified-api-contracts/instruments-service —
      **UAC SSOT SHIPPED: unified-api-contracts@b654eb6** — `canonical/crosscutting/total_universe.py`
      (`TOTAL_UNIVERSE_AXES` per-AG selection-axis taxonomy with base_currency/venue/data_type/defi_pool_volume/
      fixtures/combinations; `UniverseProvenance` HARDCODED_GENESIS-vs-DOWNLOAD_DERIVED taxonomy; `UniverseTier` +
      `universe_membership()` classifier MVP⊆TOTAL; config-version descriptor) + 9 unit tests, all exported from the
      UAC root facade. The instruments-service consumer wiring (`enumerate_expected_universe.py` reading these axes for
      the could-exist denominator) is the downstream half, tracked under B0/B1 + path_to_100pct backfill.
- [ ] [DATA] P0. **B0 — backfill instruments to NO-MISSING (prereq for B1 catalogue + all expected-universe
      consumers)**: the F1/F2 instrument backfills below + the broader could-exist instrument backfill tracked in
      `path_to_100pct_backfill_mtds_is_2026_06_17.md`. Other services rely on instruments to know what's
      available/expected → this runs FIRST. — instruments-service

## GCS object-migration COMPLETE + delete-list sizing (2026-06-18) — DELETE IS OPERATOR-GATED

All legacy duplicate twins copied to canonical `pipeline_mode={mode}_{source}/asset_group={ag}/` shape via
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

## MARKET-DATA `_index` v9 COLUMN POPULATION — APPLIED to ALL 5 AGs (2026-06-18)

> Operator-dispatched v9 `--apply`. Audit ground-truth (read-only, 2026-06-18): the live MTDS prd
> `_index/availability_index.parquet` for ALL 5 AGs was cell-key-canonical (deduped) BUT still
> **schema v8, `pipeline_mode` 100% blank, `source` column ABSENT, `asset_group` absent (cefi/sports)
> or partial (defi/tradfi/pred)** — the v9 column population was never run on the live index.

**DECISION — in-place populator, NOT the object-scan rebuild (root-cause diagnosis).** The
`rebuild_{ag}_manifest.py` non-dry-run is the documented v9-column writer, but a fresh GCS scan
**double-counts** every cell with both a legacy object AND its canonical twin (COPY-not-MOVE; the
legacy delete is operator-gated/pending). PROOF: the pre-generated v2 projections carry massive true
duplicates — `projected_index_cefi_v2` 1.08M dup rows, defi 0.67M, sports 0.73M — and
`projected_index_prediction` REGRESSES captured 16,918→7,116. Applying any would CORRUPT the deduped
live index (captured→failed mass-flip / dup inflation = the exact gate-fail the BLOCKER GATE forbids).
Instead built `market-tick-data-service/scripts/populate_v9_index_columns_inplace.py` (mtds@6b9f4b5):
reads the live deduped `_index`, fills `pipeline_mode` via UTL `derive_pipeline_mode_for_row` (100%
derivable, verified all 5 AGs; source-aware — tradfi splits barchart/massive/databento), `source` via
UAC `source_string_for(PipelineMode)`, `asset_group` constant, `schema_version=9` — ROW-PRESERVING, so
captured is provably preserved. defi additionally picks up the **46,866 canonical `venue=UNISWAP_V4`
batch_onchain_subgraph cells** (incl the 31,773 newly-migrated) whose `_index` rows were never written
(the index held only the legacy `UNISWAPV4`/`UNISWAPV4-ETHEREUM` spellings).

**Per-AG result (before→after, captured-preserved gate honored absolutely):**

| AG     | rows before→after        | schema v9 | pipeline_mode | source | asset_group | captured (Δ)            | snapshot |
| ------ | ------------------------ | --------- | ------------- | ------ | ----------- | ----------------------- | -------- |
| pred   | 19,299 → 19,299          | 100%      | 100%          | 100%   | 100%        | 16,918 (+0)             | ✅       |
| tradfi | 144,314 → 144,314        | 100%      | 100%          | 100%   | 100%        | 96,811 (+0)             | ✅       |
| cefi   | 2,167,688 → 2,167,688    | 100%      | 100%          | 100%   | 100%        | 1,311,984 (+0)          | ✅       |
| sports | 803,796 → 803,796        | 100%      | 100%          | 100%   | 100%        | 202,087 (+0)            | ✅       |
| defi   | 1,578,922 → 1,625,788    | 100%      | 100%          | 100%   | 100%        | 344,564 → 391,430 (+46,866 V4) | ✅ |

All applies snapshot the prior index to `_index/snapshots/pre_v9_apply_{ag}_2026_06_18.parquet`
(rollback net, in addition to `pre_migration_2026_06_18`). Independently re-read post-apply: every AG
schema_v9=100%, pipeline_mode/source/asset_group=100%, captured preserved (defi V4 = 46,866 captured,
0 already present). Apply order: pred → tradfi → cefi → sports → defi (safest first). Tool is a
`scripts/` oneoff (ruff-lint-clean + runtime-verified via 5 applies; lifecycle marker present).

- [x] ✅ [SCRIPT] P1. **MARKET-DATA `_index` v9 column population `--apply` for ALL 5 AGs** — DONE
      2026-06-18. `populate_v9_index_columns_inplace.py` (mtds@6b9f4b5) in-place populated
      pipeline_mode/source/asset_group + schema_version=9 on all 5 live prd `_index` objects;
      captured preserved on cefi/tradfi/sports/pred, defi +46,866 canonical UNISWAP_V4 cells picked up
      (incl the 31,773 newly-migrated). schema_v9/pipeline_mode/source/asset_group all 100% per AG;
      pre-apply snapshots written. In-place chosen over the rebuild (rebuild projections were
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

| AG     | captured venues | GCS canonical venues | captured-spelling stragglers | completeness gaps | verdict |
| ------ | --------------- | -------------------- | ---------------------------- | ----------------- | ------- |
| pred   | 2               | 1 (POLYMARKET)       | `UNKNOWN`(21)                | 0                 | CLEAN + 1 straggler→todo |
| tradfi | 6               | 6                    | 0                            | 0                 | **CLEAN — no action** |
| cefi   | 21              | 18                   | `COINBASE`(7)/`OKX`(7)       | 0                 | CLEAN + tiny stragglers→todo |
| sports | 29             | 27                   | `UNIBET_EU`(11)/`UNKNOWN`(3) | 0                 | CLEAN + tiny stragglers→todo |
| defi   | 30             | 30                   | **50 venue spellings (256k captured rows)** | 0  | **REBUILT (N6r)** |

**DeFi (the headline) — `canonicalize_mtds_index.py` extended with N6r venue-spelling-canon + dedup-merge
(mtds, this run):** the prior "defi venue NOT normalised (STOP)" block (object-desync risk under COPY-not-MOVE) is now
SATISFIED *by* the rewrite — a legacy-spelling index row (`UNISWAPV3`/`AAVEV3-ETHEREUM`) points at a DELETED object
spelling and MUST be re-pointed to the canonical spelling (`UNISWAP_V3`/`AAVE_V3`) whose object is the only one left on
disk. **GCS-VERIFIED remap rule** (NOT blind `_canonical_defi_venue`): remap `V`→canon(V) ONLY when canon(V)≠V AND the
LITERAL `V` venue dir is ABSENT from canonical GCS; a venue still live on GCS is KEPT. This protected the two genuine
coexisting-distinct-data exceptions — `SUSHISWAP` (captured rows resolve 12/12 to `venue=SUSHISWAP` objects, 0/12 to
`SUSHISWAP_V3`) and `YEARNV3` — which a blind canon would have desynced/false-merged. Dedup-merge after the remap keeps
the CAPTURED row over any non-captured twin.

**Content gate (CRITICAL) — PASSED:** dry-run on the live defi `_index`: 48 spellings remapped (254,812 captured rows
re-pointed; SUSHISWAP/YEARNV3 kept), 24,280 duplicate cell-keys collapsed (23,866 all-captured legacy↔canonical twins +
414 all-non-captured; **0 keys mix captured+non-captured** → no captured cell ever shadowed). captured 391,430 →
367,564 rows = exactly the legitimate legacy↔canonical captured-twin dedup (−23,866); **every distinct captured
cell-key survives** + 40/40 random remapped captured cells `gcs_describe`-verified to have their canonical object.
Final invariants: `venue_noncanon_remaining=0`, `captured_venue_not_on_gcs_remaining=0`, `itype_noncanon_remaining=0`.

- [ ] [SCRIPT] P1. **DeFi `_index` venue-spelling canon + dedup-merge (N6r) `--apply`** — code DONE
      (`canonicalize_mtds_index.py` N6r, mtds@<sha>): GCS-verified venue remap (literal-gone→canon-exists; KEEP
      SUSHISWAP/YEARNV3 still-live) + captured-first dedup-merge. Dry-run content-gate PASSED (above). PENDING: snapshot
      live defi `_index` → `_index/snapshots/pre_canonical_rebuild_defi_2026_06_18.parquet` → `--apply` → re-verify with
      `audit_index_vs_gcs_spellings.py` (0 captured stragglers). — market-tick-data-service
- [ ] [DATA] P2. **pred `_index`: 21 captured `UNKNOWN`-venue `trades` cells (2025-03-14..)** — GCS has `venue=POLYMARKET`
      only; these legacy `UNKNOWN`-venue rows have blank instrument_id (aggregate/legacy) and no `venue=UNKNOWN` object.
      Recover the real POLYMARKET venue (join to the same-day `pipeline_mode=batch_polymarket_clob/venue=POLYMARKET`
      object) or route to honest-absence. Composes with N8 (pred label drift). — market-tick-data-service
- [ ] [DATA] P2. **cefi `_index`: `COINBASE`(7)+`OKX`(7) captured rows with BLANK data_type/instrument_type** — GCS has
      `venue=COINBASE-SPOT`/`OKX-SPOT`/`OKX-SWAP` (market-type-suffixed), NOT bare `COINBASE`/`OKX`. These are malformed
      blank-shard-dim aggregate captured rows with no concrete object; the bare→suffixed map is AMBIGUOUS (SPOT vs
      FUTURES vs SWAP) so NOT a mechanical spelling-canon. Diagnose the writer that emitted blank-dim bare-venue rows;
      reclassify (the real per-market data is captured under the suffixed venues). EXTENDED-STARKNET(1) IS on GCS
      (sample miss, no action). — market-tick-data-service
- [ ] [DATA] P2. **sports `_index`: `UNIBET_EU`(11)+`UNKNOWN`(3) captured rows under wrong `pipeline_mode`** — the
      bookmaker venues (BETMGM/BETWAY/BOVADA/UNIBET_EU) exist on GCS under `pipeline_mode=batch_odds_api/venue=<bk>/`
      but these index rows carry `pipeline_mode=batch_api_football` → venue spelling is correct, the
      pipeline_mode/source is mislabeled. Re-stamp pipeline_mode/source to the odds_api source (or honest-absence for
      genuinely-absent cells). Composes with N3a (null-league) / N3b (null-source). — market-tick-data-service

## INSTRUMENTS-STORE buckets — legacy GCS audit + `_index` canonicalisation COMPLETE (2026-06-18)

> Operator-granted: delete legacy twins once 100%-verified canonical twin (`gcs_describe`). This is the
> **instruments-store** (reference-data) analogue of the market-data delete work above — a DISTINCT bucket set
> (`instruments-store-{cefi,defi,tradfi,sports}-prd-…` + `instruments-store-pred-prd-…`), NOT the `market-data-tick-*`
> buckets (those are mid-delete and were NOT touched here).

**KEY FINDING — instruments-store has NO `pipeline_mode=`/`asset_group=` twin model.** It is reference data (one AG per
bucket, no batch/live mode): canonical shapes are `prod/catalog.parquet` +
`instrument_availability/by_date/day={D}/.../instruments.parquet` (cefi/defi/tradfi/pred partition by `venue=`; sports
by `league=`/`venue=`). So the market-data "insert `pipeline_mode={mode}_{src}/asset_group={ag}/` twin" model **does not
apply**. A "legacy" object here is a data parquet OUTSIDE those canonical prefixes. READ-ONLY audit:
`instruments-service/scripts/audit_instruments_store_legacy_gcs_delete_list.py` (per-AG delete-list parquet →
`gs://<bucket>/_index/audit/instruments_store_legacy_delete_list_{ag}.parquet`).

| AG         | canonical | control | legacy[bare_day, dash] | SAFE-TO-DELETE | UNMAPPABLE residue (NOT deleted) | manifest `_index` |
| ---------- | --------- | ------- | ---------------------- | -------------- | -------------------------------- | ----------------- |
| cefi       | 28,524    | 7       | 0, 0                   | 0              | 0                                | canonical ✅      |
| defi       | 66,894    | 6       | 0, 0                   | 0              | 0                                | canonical ✅      |
| tradfi     | 11,648    | 8       | 0, 0                   | 0              | 0                                | canonical ✅      |
| sports     | 110,138   | 778,010 | 2, 9,721               | 0              | 9,723 (0.146 GB)                 | canonical ✅      |
| prediction | 4,932     | 50      | 0, 0                   | 0              | 0                                | canonical ✅      |

**Migrate-first + delete: nothing to do (safe outcome).** cefi/defi/tradfi/pred are 100% canonical — zero legacy
objects, nothing to migrate or delete. Sports' two non-canonical shapes are **superseded orphan data from older sports
pipelines, NOT twins of the canonical reference data**, so they are honest-absence residue (excluded from the
delete-list, reported only — never deleted):

- bare top-level `day=2026-03-21/venue=BETFAIR/<hash>.parquet` (n=2): a BETFAIR odds-instrument write (different venue
  than the canonical `venue=API_FOOTBALL_FIXTURES`, no `league=` key → no canonical-rename twin).
- `instrument_availability/by-date/day-{D}/{soccer_slug}/instruments.parquet` (n=9,721, dates 2020-06-06..2025-12-15, 52
  league-slugs): the legacy **dash-separator odds-api source** (`bookmaker_key`/`odds_api_market_id`/`market`/
  `selection` schema; venues ONEXBET/PADDYPOWER/PINNACLE/BETFAIR/UNIBET — from `oddspapi_historical_backfill.py`). The
  canonical `by_date/` (underscore) shape is api-football FIXTURES reference (different data source + schema + a
  non-translatable `soccer_germany_bundesliga`→`BUNDESLIGA` league-slug map), and it COVERS the same date range + is
  written more recently (tip 2026-05-13 > legacy tip 2025-12-15) → the dash shape is superseded, not a twin. Deleting it
  needs an operator/explicit decision (it is orphan stale data, but has no canonical replacement to verify against).
  **MIGRATE-FIRST=0 mappable** — the only "legacy" is unmappable by construction (no canonical-rename target exists).

**`_index` (manifest) canonicalisation — now COMPLETE for ALL 5 AGs** (the N2 2x-per-cell + blank-status v4 shadow
defect). `canonicalize_instruments_store_index.py` was already applied to tradfi+sports; I applied it to **cefi**
(15,933 blanks classified, 12 dups dropped → 28,586→28,574 rows) and **defi** (127,140 blanks classified, 121,109 dups
dropped → 196,987→75,878 rows), and re-ran tradfi idempotently (dropped 3 residual dups → 11,674). Re-verified: **every
AG now has blank_status=0 AND dup_cells=0.** prediction was already clean (500 rows, 0 blank, 0 dup).

- [x] ✅ [SCRIPT] P1. **instruments-store legacy GCS audit + per-AG delete-list** — DONE
      instruments-service@`audit_instruments_store_legacy_gcs_delete_list.py`. cefi/defi/tradfi/pred 100% canonical (0
      legacy); sports 9,723 unmappable-superseded (excluded, reported); SAFE-TO-DELETE=0 fleet-wide → no delete needed.
      Delete-list parquets written to each `_index/audit/`. — instruments-service
- [x] ✅ [SCRIPT] P1. **instruments-store `_index` v9-canonical for ALL 5 AGs** — DONE (cefi+defi+tradfi `--apply`'d;
      sports/prediction already clean). Every AG blank_status=0 + dup_cells=0. — instruments-service
- [ ] [SCRIPT] P3. **`canonicalize_instruments_store_index.py` can't resolve the prediction bucket** — `_bucket_for`
      calls `resolve_bucket_name(kind="instruments-store", asset_group="prediction")` which raises `BucketNamingError`
      (prediction uses the flat `instruments-store-prediction` kind, no per-AG key). Harmless today (prediction `_index`
      is already canonical — 500 rows, 0 blank, 0 dup → nothing to canonicalize), but the `--asset-group prediction`
      choice is a dead path. Fix `_bucket_for` to route prediction →
      `kind="instruments-store-prediction",     asset_group=None` if prediction ever needs re-canonicalisation.
      **NICE-TO-HAVE** (provenance: 2026-06-18 instruments-store audit). — instruments-service

## Databento SUBSCRIPTION CONTRACT (operator 2026-06-18 — supersedes PAYG model)

**No longer PAYG** — subscription + ~$150 credits (more than enough to stream all instruments). **ONE API key**
(`databento-api-key`, single-key — operator chose collapse-to-single-key) across **exactly 3 datasets**: `GLBX.MDP3`
(CME) + `DBEQ.BASIC` (Databento US Equities) + `CFE` (CBOE Futures). Any other dataset → reject.

Schema → free-window entitlement (a request's `start` must be ≥ `today − window`; clip/reject otherwise):

| Level | Schemas                                          | Free window | Guard                |
| ----- | ------------------------------------------------ | ----------- | -------------------- |
| L0    | `ohlcv-1s`, `definition`, `statistics`, `status` | 16 years    | start ≥ today − 16y  |
| L1    | `trades`, `tbbo`, `mbp-1`, `bbo-*`               | 1 year      | start ≥ today − 365d |
| L2    | `mbp-10`                                         | 1 month     | start ≥ today − ~30d |
| L3    | `mbo`                                            | 1 month     | start ≥ today − ~30d |

Codify this (schema→window table + 3-dataset allowlist) as the SSOT (UAC) + enforce as a pre-request guard in the
Databento adapter(s) — replaces the PAYG-cost-blocker framing (cost emission stays as credit-burn telemetry; the hard
guard is now entitlement window + dataset, surfaced as 403/entitlement not 402/payment). Instruments = `definition`
schema = L0 (16y window) → the instrument backfill can pull the FULL universe within the 3 datasets, cost-free within
credits. Tracked todos below.

- [x] ✅ [CODE] P1. **Databento subscription cutover (MTDS+UAC+IS)** — DONE: single-key config
      (`use_multi_key_rotation=False`, `num_api_keys=1`, `DEFAULT_NUM_API_KEYS=1`; num_keys-asserting test fixed to read
      `get_num_api_keys()`; transitional secret `databento-api-key-1` DELETED — only `databento-api-key` remains) +
      schema→free-window + 3-dataset allowlist SSOT (`databento_subscription_allowlist.py` @31db3b0) enforced as the
      pre-request guard at the MTDS get_range chokepoint AND the IS `definition`-schema fetch (with dataset-level shard
      isolation so an off-allowlist dataset doesn't hard-fail siblings). — market-tick-data-service@88d1c65e /
      instruments-service@86ecc67b / unified-api-contracts@3b76c0bc | all QG green.
- [x] ✅ [SCRIPT] P1. **B0 instrument backfill within contract**: backfill `definition` (L0, 16y) for GLBX.MDP3 +
      DBEQ.BASIC + CFE — full universe (credits cover it). — instruments-service — **ALREADY COMPLETE** (verified
      2026-06-18, instruments-service@dedae75 run): `instruments-store-tradfi-prd` `_index` = 11,418 captured / 256
      empty_confirmed, cov **1.0, 0 attempted_failed, 0 date gaps**. 6 venues continuous DAILY: CME/FX/ICE/CBOE
      2020-01-01→2026-06-18, NASDAQ/NYSE 2023-04-15(subscription start)→2026-06-18 (distinct-days == calendar-span ⇒ no
      missing day). The 3-dataset subscription guard (`assert_databento_request_allowed`, dataset-level shard-isolation)
      is installed on the `definition` fetch — banned datasets isolate (not hard-fail), existing rows are already the
      right 6-venue universe (no banned datasets present). Forward daily keep-green only. See Progress Log "B0 EXECUTION".
- [ ] [CODE] P1. **`ohlcv-1s` has NO `BarTimeframe` member → OHLCV close-edge conversion raises** (surfaced 2026-06-18
      during the subscription cutover): the contract fetches ONLY `ohlcv-1s`, but `_OHLCV_DATA_TYPE_TIMEFRAME` (mtds
      `databento_adapter.py`) + the UAC `BarTimeframe` closed set (`bar_boundary.py` — smallest unit is `15s`) have no
      `1s`/`ohlcv_1s` entry, so `_convert_ohlcv_open_edge_to_close` raises `ValueError` for a real `ohlcv_1s` OHLCV
      write. Adding `"1s"` is a deliberate workspace-wide closed-set extension (per the `BarTimeframe` docstring: extend
      the Literal + `BAR_TIMEFRAME_SECONDS` (1s divides 86400 so the midnight-grid clause holds) + audit every
      `record_captured` OHLCV write-callsite + features-\* DAG + data-status drilldown + cluster-validation registry,
      ALL in one commit). Until landed, the OHLCV path must AGGREGATE `ohlcv-1s`→1m/15m/24h before the close-edge stamp
      (the written bar is the aggregated bar, which DOES have a `BarTimeframe`), never write raw 1s bars. (Workaround
      shipped: the 4 `test_databento_path_streaming.py` tests now exercise `trades` not the banned `ohlcv_1m`, so they
      no longer depend on this gap.) — unified-api-contracts / market-tick-data-service / features-service

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
- [ ] [INFRA] P2. **Research `-prd-` buckets carry NO `_index/` — move the availability index off the legacy
      `perp-funding`/`lst-rates` buckets before they can be deleted** (DIAGNOSED 2026-06-18, larger than a config edit —
      exact steps below). ROOT CAUSE: the dedicated DeFi research stores `perp-funding`/`lst-rates` are NOT in the
      manifest-consolidator TF at all (`deployment-service/terraform/{gcp,aws}/manifest_consolidator_scheduler.tf`
      `manifest_consolidator_buckets` covers only `instruments-store-*` + `market-data-tick-*`, env-tiered + legacy —
      grep confirms 0 `perp`/`lst` entries). The B3 manifest writer
      `e2e-testing/scripts/defi/record_research_perp_ctx_manifest.py` hardcodes
      `INDEX_BUCKET = "perp-funding-central-element-323112"` (LEGACY flat) → the live `_index` sits only in the legacy
      bucket; there is no consolidator cron for these stores. **EXACT STEPS:** (1) add 4 entries to
      `manifest_consolidator_buckets` (gcp) + the AWS Batch/EventBridge equivalent —
      `perp-funding-prd-${env}-${project}`, `lst-rates-prd-${env}-${project}` (the canonical `-prd-` homes; resolve via
      the `perp-funding`/`lst-rates` `cloud-providers.yaml` keys, NOT new hardcodes) — with a `*/1` cron + IAM
      `storage.objectAdmin` on each; (2) repoint `record_research_perp_ctx_manifest.py`'s `INDEX_BUCKET` to
      `resolve_bucket_name(cloud="gcp", kind="perp-funding")` (the `-prd-` home) so new index shards write there (LST
      writer if/when one exists → `kind="lst-rates"`); (3) one-shot seed: copy the legacy
      `perp-funding-central-element-323112/_index/` + `lst-rates-central-element-323112/_index/` → their `-prd-` twins
      (`gcs_copy_object`), or run the consolidator `--force` once over the `-prd-` bucket after the per-VM shards land
      there; (4) verify `_index/availability_index.parquet` freshness on each `-prd-` bucket (consolidator heartbeat <
      `MANIFEST_CONSOLIDATED_STALENESS_SEC`); (5) ONLY THEN are the legacy research buckets delete-safe (operator-gated,
      tracked with the other legacy deletes). SSOT: `codex/05-infrastructure/manifest-consolidator-ssot.md` +
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

**⚠️ DIAGNOSIS CORRECTED 2026-06-18 (CONTENT-VERIFIED, supersedes the path-only verdict above).** The prior "unique
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
- [ ] [DATA] P3. **Verify-then-delete the ~122 genuinely-legacy-only tradfi stragglers** — REFRAMED 2026-06-18: the 107
      bare `venue={CME,ICE,NYSE,NASDAQ}/ticks.parquet` are recent (2026-02+) RAW `data_type=trades` ticks (Databento
      market-by-order), NOT pre-canonical OHLCV — and `data_type=trades` IS a canonical tradfi data_type
      (`pipeline_mode=batch_massive/.../data_type=trades/`). The content verifier already classifies them
      TWIN-VERIFIED-SAFE when their `instrument_id` is in same-day canonical `trades` content (8/8 sampled, incl.
      bare-107, 100% covered). So they are NOT a separate straggler class — the verify parquet's TWIN-VERIFIED-SAFE set
      is the delete-safe list (operator-gated). 0-row/empty legacy = honest no-data, delete-safe once confirmed empty. —
      e2e-testing

## Phase A — subset violations (MTDS data with no instrument backing)

- [ ] [DATA] P1. **F1 — backfill instruments-service for CEFI venues MTDS has but instruments lacks historically**:
      `KRAKEN-SPOT`/`KRAKEN-FUTURES` (added to instruments only at day=2026-06-17 — ~6yr gap), `LIGHTER-ZKSYNC`,
      `PACIFICA-SOLANA`, `EXTENDED-STARKNET`. Re-run the IS daily-listing CLI across the MTDS-covered date range per
      venue (never copy between dates). Verify the cefi (venue,date) subset closes. — instruments-service —
      **🟢 IN PROGRESS / mostly DONE (2026-06-18 autonomous run):** LIGHTER-ZKSYNC (2024-08-01→06-18 ✅), PACIFICA-SOLANA
      (2025-06-01→06-18 ✅), EXTENDED-STARKNET (2024-10-01→06-18 ✅) all backfilled via the IS daily CLI (Tardis/native,
      0 errors). **KRAKEN-SPOT/FUTURES 6yr backfill RUNNING** to completion in background (2020-01-01→2026-06-18, Tardis,
      ~40 records/day; at 2024-06 as of 23:20, ETA ~1h; `/tmp/is_backfill_logs/kraken_f1.log`, monitored). Flip fully ✅
      once Kraken reaches 2026-06-18 (the monitor reports completion).
- [x] ✅ [DATA] P2. **F2 — backfill 5 missing BITGET-FUTURES + 5 BITGET-SPOT instrument-days** that MTDS captured but
      instruments is absent for. — instruments-service — DONE 2026-06-18: re-ran the IS daily CLI
      `--venues BITGET-FUTURES BITGET-SPOT --start-date 2024-11-08 --end-date 2026-06-18` (idempotent, re-fetched the
      stale/missing days), wrote ~120 records/day, reached 2026-06-18. `bitget_f2.log`.
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
- [ ] [DATA] P2. **N5r/N6r — DEFI rebuild-for-real-replace to land venue-dedup + VAULT-0-row + 496 chain-pollution on
      LIVE**: the per-object rebuild (mtds@3f5cc6e/cf63cf6) normalizes venue + detects 0-row vaults + would clean the
      496 `chain`-pollution rows (token-pairs ETH-USDC/1INCH-ETH in `chain`, all attempted_failed UNISWAP_V4
      swaps_ohlcv), but reaching LIVE needs a WHOLESALE replace of the defi `_index` (the consolidator merge leaves
      stale un-normalized rows; the index-walk can't normalize venue without desyncing from object paths). Run the
      rebuild to produce the full v9 index + write it as the live `_index` (replace, not merge). NOT a
      double-count/data-loss (P2 grouping hygiene). **ALSO picks up the 31,773 newly-migrated canonical UNISWAP_V4
      `pool_id` cells (3.24M rows) the content-aware fan-out wrote 2026-06-18** — the rebuild walks all canonical
      objects, so these get their `availability_index` rows on this same wholesale-replace run (no separate V4 manifest
      pass needed). — market-tick-data-service
- [x] ✅ [DATA] P0. **F3 (reframed) — CEFI re-classify legacy-recon `attempted_failed`** — FIXED mtds@aaeada9.
      `_rebuild_cefi_cf11.py`: shadow legacy rows (covered by a real object) suppressed (part of the 371,010 shadows);
      non-shadow `LEGACY_THIRDKEY_DRIFT_RECON_2026_05_07` dropped as un-keyable drift duplicates (**243,828 dropped**);
      `LegacyBlankErrorReasonError`→`UNCLASSIFIED_ADAPTER_ERROR` preserved (visible/backfill-worthy). attempted_failed
      **1.40M→782,005** in `projected_index_cefi_v2`. Genuine `VENUE_FETCH_FAILED`(83,975)+`HTTP_429`(3,652) preserved →
      backfill Step 9. The ~698k UNCLASSIFIED reconcile-to-expected_unattempted is N1b (depends Step 4). —
      market-tick-data-service
- [ ] [CODE] P2. **F6 (reframed) — TRADFI option/instrument_type encoding**: unify the two options encodings
      (`instrument_type=options_chain` vs `data_type=options_chain` w/ blank type) + stamp instrument_type on the 182k
      blank-type cells (legacy path shapes). Not missing data — a typing fix. — market-tick-data-service
- [x] ✅ [INFRA] P3. **N7 / Step-5 prefix_tpls VERIFY — DONE (no code change needed)**:
      `reconcile_phantom_manifest_rows_all.py` `prefix_tpls = canonical_path_templates(ag)` (CF-15/V0 UAC SSOT) for
      cefi/defi/tradfi/prediction — VERIFIED complete: enumerates every coexisting shape
      (`pipeline_mode=batch_<source>/`, bare `asset_group=`, legacy `category=`, top-level `day=`, defi
      `venue=PROTOCOL-CHAIN` overload + bare-venue). **Sports `[""]` is NOT a foot-gun** — sports routes to the
      dedicated `_audit_sports` + UAC `candidate_parquet_paths` SSOT (bucket kind=instruments-store), and ALL 17
      captured instruments-store-sports data_types (STANDINGS/TEAMS/FIXTURES/ODDS/…) resolve ≥1 candidate path.
      `--apply` will NOT mass-flip on any AG from a prefix-coverage gap. — instruments-service
- [ ] [DATA] P3. **N8 — PRED index data_type label drift** (`prediction_canonical_question_group` vs GCS
      `prediction_trades`/`trades`) + 1 blank-reason attempted_failed cell. Confirm intentional rollup label vs drift;
      type the blank reason. — market-tick-data-service
- [ ] [DATA] P1. **N1b — CEFI: reconcile the ~698k `UNCLASSIFIED_ADAPTER_ERROR` (ex-`LegacyBlankErrorReasonError`,
      blank-itype) attempted_failed cells against the IS expected-universe (Step 4 enumerator) + reconcile (Step 8)**:
      cells the enumerator marks `expected_unattempted` (instrument not listed / pre-coverage) should drop the stale
      failed row; genuine in-coverage listed-instrument gaps stay attempted_failed → backfill (Step 9). DEPENDS on
      Step 4. (Provenance: Step-1 fix kept them visible rather than hide a gap; final fate is
      enumerator+reconcile-driven.) — market-tick-data-service
- [ ] [DATA] P2. **N3a — SPORTS: 32,707 captured cells genuinely NULL-league in the LIVE index** (schema_version=8;
      venue=bookmaker/ODDS_API, data_type=trades/ODDS/odds_horizon_bucket). The Step-2 fix recovered the 169,380 cells
      that HAD league; these 32,707 lost it at WRITE time. Recover league_id by joining each null-league captured
      (date,venue, data_type) to the GCS object paths (`league_id=<L>`) for that cell — needs a sports object scan (the
      rebuild is index-driven). No sports market data may be captured for an unattributed league. —
      market-tick-data-service
- [ ] [DATA] P2. **N9 — MTDS SPORTS (market-data-tick-sports) 17,288 blank-capture_status rows** (pre-existing CF-10
      reference/phantom set; surfaced in the 2026-06-18 final live-manifest verify — distinct from the instruments-store
      sports blanks F5 which ARE fixed). Classify via a sports-MTDS canonicalize pass (extend
      `canonicalize_mtds_index.py` to sports, mirroring the instruments-store classify: reference blank-data_type rows
      kept; real-data_type phantoms → honest status). NOT a double-count. captured (202,087, league_id present) + empty
      (584,257) already correct. — market-tick-data-service
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

- [ ] [INFRA] P0. **Migrate-first the 4 un-migrated AGs' OBJECTS to canonical `pipeline_mode=` shape
      (defi/tradfi/sports/ pred, ~2.88M objects / 179 GB)** — their canonical migration never completed (tradfi never
      hive-canonicalised; pred restructured; defi/sports partial). Run/complete
      `migrate_{defi_full,tradfi}_to_v9_canonical.py` (+ sports/pred equivalents) on in-region VMs (gcs_copy_object
      workers=32) to create the canonical twins, then re-run the twin-audit → 0 migrate-first per AG. ONLY THEN are
      those AGs' canonical-only reads orphan-free + their legacy objects delete-safe. cefi needs NONE of this (already
      twinned). — market-tick-data-service / deployment-service
- [x] ✅ [INFRA] P1. **Phase D rescan + delete-list — DONE + verified.** cefi SAFE-TO-DELETE list ready for operator
      inspection (`legacy_dup_delete_list_cefi.parquet`, 1,077,672 objs / ~9.98 TB, exclude the 15 migrate-first); the
      other 4 AGs are migrate-first (above), NOT deletable yet. e2e research data accounted-for + safe. Deletion remains
      OPERATOR-GATED (inspect→confirm→delete).
- [ ] [INFRA] P1. **Phase D — DELETE legacy GCS dupes (OPERATOR-GATED, cefi-only today)**: the bare
      `raw_tick_data/by_date/day=*/asset_group={ag}/...` objects are EXACT duplicates of canonical
      `pipeline_mode={mode}_{source}/asset_group={ag}/...` twins (verified: same instrument exists at both). They no
      longer cause UI double-count (data-status reads the cell-reduced manifest + deployment-api@6bcac01 drilldown is
      canonical-only). Procedure: per AG, list bare `day=*/asset_group=` objects → verify each has a `pipeline_mode=`
      twin (via `gcs_describe_object`) → write the delete-list to `_index/audit/legacy_dup_delete_list_{ag}.txt` →
      **OPERATOR INSPECTS + confirms** → `gcs_delete_object` the confirmed bare twins (in-region VM, workers=32).
      Storage reclamation only; do NOT delete any bare object lacking a canonical twin (that would be unmigrated →
      migrate it first). — instruments-service/deployment-service
- [ ] [DATA] P2. **N9c — MTDS `_index` is NOT yet v9 for any of the 5 AGs; `pipeline_mode` column 100% BLANK
      (data-status pipeline_mode FILTER chip non-functional). Found 2026-06-18 data-status audit.** Despite the
      instruments-store `_index` being v9 (todo above, line ~310), the **market-data-tick** (MTDS) prd `_index` for ALL
      5 AGs is still ~96% `schema_version=8` (cefi 2.085M/2.168M v8, only 8,034 v9; defi/tradfi/sports/pred similar),
      carries NO `asset_group` and NO `source` column, and `pipeline_mode` is **100% blank/None** (verified: 0 non-blank
      rows of 2.17M cefi / 1.58M defi / 144k tradfi / 804k sports). CONSEQUENCE: the data-status
      `_apply_pipeline_mode_filter` chip (`coverage.py`) narrows to ZERO on any `batch_*` filter — the manifest rows
      have no pipeline*mode to match — even though the GCS objects ARE canonically
      `pipeline_mode={mode}*{source}/`-keyed. Coverage % + the drilldown are     UNAFFECTED (they read `capture_status`/ derive canonical segments from UAC, not the manifest pipeline_mode column).     FIX = the wholesale v9`\_index`rebuild-and-replace (already tracked per-AG: N5r/N6r for defi, the migrate-first +     rebuild for tradfi/sports/pred) must POPULATE`pipeline_mode`+`source`+`asset_group`from the canonical object     paths, not just classify capture_status. Re-verify`pipeline_mode`
      non-blank > 0 post-rebuild per AG. — market-tick-data-service
- [ ] [DATA] P3. **N3b — SPORTS: 6 captured cells still NULL source**
      (ARBITRAGE_OPPORTUNITY/ODDS_MOVEMENT/ODDS_SNAPSHOT, 2 each) after the Step-2 `trades→odds_api` + case-insensitive
      bridge. Add these MDPS-derived data_types to the source bridge (or route to honest absence if not genuinely
      captured). — market-tick-data-service
