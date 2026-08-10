---
doc_type: plan
title: Data completion to 100% — TradFi manifest canonicalisation + backfill (split from M-1)
summary: >-
  TradFi slice of the data-completion-to-100% program, split out of data_completion_to_100_all_ag_2026_06_21 (M-1) on
  2026-07-15 per operator ruling (plan-reconcile §8) when M-1 breached the absolute 5000-line ceiling. Carries the
  tradfi scope M-1 absorbed in the 2026-07-13 consolidation, migrated VERBATIM — no scope added, dropped or reworded.
  M-1 remains the coordinator hub for cross-cutting work (bucket naming, source provenance, bar-edge) and owns the
  shared Progress Log.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [backfill, manifest, honest-coverage, data-completion, tradfi, data-correctness]
related: [/plans/active/data_completion_to_100_all_ag_2026_06_21.md]
created: 2026-07-15
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
last_updated: 2026-08-09 # (was: 2026-07-29 -- na-eligibility-audit 2026-08-09 fixed 3 citation gaps, see Progress Log)
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: [data_completion_to_100_all_ag_2026_06_21 (M-1) — split 2026-07-15, plan-reconcile §8 operator ruling A]
drift_direction: advance-code
context_scope:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/canonical-cutover-register.md,
    instruments-service/scripts/enumerate_expected_universe.py,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_tradfi_manifest.py,
  ]
---

# Data completion to 100% — TradFi

> **Split from M-1 on 2026-07-15** (`data_completion_to_100_all_ag_2026_06_21.md`, plan-reconcile §8, operator ruling
> A). M-1 had reached 5,366 lines — the only file in the corpus over the absolute 5,000-line ceiling — after absorbing
> 130 folded-in todos in the 2026-07-13 consolidation. This plan carries M-1's **tradfi** scope **verbatim**; M-1 stays
> the coordinator hub (measured snapshot, per-AG launch matrix, cross-cutting scope, shared Progress Log).
>
> **Read M-1 first** for the program-level snapshot + launch matrix. Cross-cutting items (bucket-name SSOT, data-source
> provenance, bar-edge) deliberately stayed there — they are not tradfi-specific.

### From `tradfi_manifest_canonicalisation_2026_06_01.md` (archived 2026-07-13 -- TradFi manifest + data canonicalisation (v9 + pipeline_mode partition single-walk, L3 owner for tradfi))

> **🔴 Massive removed/purged 2026-07-19→21, Barchart retired 2026-06-24** — every `massive`/`barchart` reference below
> (source lists, capture paths, `tradfi_massive_dual_source` cross-links) is STALE. Databento (batch SoT) + Yahoo
> (daily) are the only live tradfi sources; `batch_massive`/`batch_barchart` PipelineMode recognition is kept read-only
> for legacy GCS until the gated purge. Do not re-action any Massive/Barchart capture todo below without first
> re-reading it against this banner.

- [x] ✅ [DATA] P1. **DONE 2026-07-27 (slot-6, data_engineering, tradfi_satellite_ao_dispatch_batch2)** — Verify the
      corpus venue / data_type strings are underscore-canonical: data-state shows venues
      `BARCHART/CBOE/CME/FX/ICE/NASDAQ/NYSE/YAHOO_FINANCE` (canonical) BUT also `UNKNOWN` + blank `''` (drift to
      diagnose); data_types `ohlcv_15m/ohlcv_1m/ohlcv_24h/options_chain/tbbo/trades` + blank `''`. Relabel/diagnose the
      `UNKNOWN`/blank rows in the walk (do NOT bulk-rename ambiguous strings). **✅ DIAGNOSIS DONE (slot-6 2026-06-04,
      live `-prd` `_index` read, 144,062 rows — pre-migration de-risk so the E5/E6 walk is ready):** the drift is
      **6,602 rows / 4.6%** — **DRIFT-VENUE 4,130** (3,540 blank + 590 `UNKNOWN`; spread across tbbo/trades/ohlcv real
      data_types; **blank `instrument_type` + `asset_group=None`**; 3,955 captured + 175 attempted_failed; dates
      2020→2026) + **DRIFT-DATA_TYPE 2,472** (all blank; real venues CBOE/ICE/CME/NASDAQ/NYSE/FX; blank instrument_type;
      all captured). These are NOT ambiguous strings to rename — they are **under-populated older-schema manifest rows**
      (the writer left venue/data_type/instrument_type/asset_group blank). **Resolution = PATH RE-DERIVATION, not a
      string-rename table**: E5 `rebuild_tradfi_manifest.py` scans the canonical object paths
      (`venue=/data_type=/asset_group=/instrument_type=` segments) and re-stamps these fields → captured drift rows are
      FIXED in-walk by the object scan (consistent with "do NOT bulk-rename"). **⚠️ RISK to verify in the walk (why this
      stays open):** (1) any drift row whose OBJECT is NOT at a canonical `venue=`-bearing path (e.g. an L-hyphen 0-row
      placeholder, which the migrator SKIPS) will NOT be re-derived → its captured status must be re-evaluated, not
      silently dropped (a blank-venue "captured" backed only by a placeholder is a false-capture → should become
      honest-absence, not coverage). (2) the 175 blank-venue `attempted_failed` rows pass through
      `reemit_honest_absence_rows`, whose `row_key` includes venue — a blank venue can mis-dedup; confirm they re-emit
      under their PATH-derived venue. **Post-walk verify hook (add to E7):** re-run this audit on the rebuilt `_index` →
      assert **0 blank/`UNKNOWN` venue + 0 blank data_type + 0 `asset_group=None`**, and assert total captured-cell
      count does not silently shrink by ~6,602 (coverage-regression guard). Audit script:
      `/tmp/tradfi_index_drift_audit.py` (read-only, reproducible). **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

      **✅ POST-WALK VERIFY HOOK RE-RUN (slot-6, 2026-07-27)**: fresh live read of
                                                                                                                                                                                                                                                          `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` (5,873,616 rows, up
                                                                                                                                                                                                                                                          from the 5,553,198-row count confirmed 2026-07-16 in E7 below — a +320,418 GROWTH from continued backfills, no
                                                                                                                                                                                                                                                          unexplained ~6,602-row shrink). Result: **0 blank venue, 0 `UNKNOWN` venue, 0 blank data_type, 0
                                                                                                                                                                                                                                                          `asset_group=None`** — the 2026-06-04 diagnosis's 6,602-row drift (4,130 venue + 2,472 data_type) is FULLY
                                                                                                                                                                                                                                                          RESOLVED by the E5 path-re-derivation walk; venue sample is exactly the canonical set
                                                                                                                                                                                                                                                          `{BARCHART,CBOE,CME,FX,ICE,KRX,NASDAQ,NYSE,YAHOO_FINANCE}`, data_type sample fully populated (12 real values, 0
                                                                                                                                                                                                                                                          blank). **Residual finding (different axis, NOT part of this candidate's tracked drift)**: `instrument_type` is
                                                                                                                                                                                                                                                          blank on 310,386 rows (202,221 `attempted_failed` / 105,936 `empty_confirmed` / 2,229 `captured`), spread across
                                                                                                                                                                                                                                                          ALL real venues (CME 219,095 / CBOE 18,032 / NASDAQ 14,805 / NYSE 13,095 / KRX 12,497 / FX 12,102 / ICE 11,641 /
                                                                                                                                                                                                                                                          BARCHART 9,119) and real data_types — 85% (262,649) are the aggregated `ohlcv_1s/1m/24h/15m` data_types, matching
                                                                                                                                                                                                                                                          the canonical_writer's own by-design omission of per-instrument fields on aggregated (non-per-instrument) shards
                                                                                                                                                                                                                                                          (see the E6/line-629 candle-writer fix below); the remainder (`tbbo/trades/macro_result/mbp_10/
                                                                                                                                                                                                                                                          corporate_action_confirmed/earnings_result/options_chain`) is not root-caused here — out of this candidate's
                                                                                                                                                                                                                                                          scope (blank/`UNKNOWN` venue + blank data_type only), flagged for a future dedicated pass, not a re-open of this
                                                                                                                                                                                                                                                          checkbox.

- [ ] [DATA] P0. **Phase 0 — layout audit (MANDATORY, blocking — slot-2 DeFi lesson 2026-06-01)**: enumerate ALL
      top-level trees + nested layouts in the tradfi source + canonical buckets before the walk; classify duplicate
      (keep freshest schema) vs complementary (migrate all → canonical v9). Cover every in-scope layout or the walk is
      incomplete (review-blocking). SSOT: `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § grounded
      recipe Phase 0.

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: the walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. SSOT:
> `/codex/05-infrastructure/gcs-object-operations.md` § "Migration-script performance contract". **(MIGRATED FROM:
> `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. C0 ONE bundled walk on the tradfi `_index` + objects: (a) `pipeline_mode=` hive partition added to
      object paths (`pipeline_mode_partition_migration` RIDER — satisfied here, do NOT run separately); (b) re-version
      manifest rows to **v9** (data-state — assert the rewritten rows actually carry 9, not just the constant); (c)
      **`category=`→`asset_group=` across BOTH object PATHS and manifest `_index` ROWS** + env-split bucket for any
      legacy-form rows that remain (CODE side — writers emit `asset_group=` — already shipped via archived
      `venue_axis_asset_group_vocabulary_2026_04_25`; this is historical data+manifest only); (d) venue/data_type
      canonical relabel for any drift found in P0; (e) `available_at` preserve-or-backfill (never migration-time).
      **DONE — executed by `tradfi_v9_stage1_finish_2026_07_06.md`**: apply completed 2026-07-06 (2020-2026, all years,
      exit_code=0, fatal=0); manifest is 100% `schema_version=9` corpus-wide, 0 blank `pipeline_mode`, 0 blank `source`
      (verified 2026-07-16, `market-tick-data-service@38cf5dfa`+`@ba866544`, `total=5,553,198 rows`). NOTE: this is the
      manifest schema-version/partition/relabel migration only — it does NOT by itself canonicalize the
      raw-tick-parquet/manifest `instrument_id` COLUMN content (a separate, still-in-progress surface — see
      `/codex/02-data/canonical-cutover-register.md`). **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. C-source RIDER: re-consolidate the already-stamped parquet `source` into the `_index` — every tradfi
      `_index` row carries `source` stamped from the live sources only (Databento = batch SoT; Yahoo = daily). DONE
      alongside C0 (2026-07-16 verification, 0 blank `source` corpus-wide). Dropped the "absorbs `tradfi_massive` Task
      -031" / "databento+massive/yahoo/barchart cells emit two rows" premise — Massive is removed + purged, Barchart is
      retired, so there is no live dual-source cell to coordinate a re-consolidation walk for. Legacy
      `batch_massive`/`batch_barchart` rows already on disk are read-only until the gated GCS purge; re-consolidation
      must NOT re-stamp `source='massive'` (the UTL writer now hard-rejects it). **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. C-pipeline_mode RIDER: confirm the `pipeline_mode=` partition for tradfi lands in THIS walk
      (satisfies `pipeline_mode_partition_migration_2026_06_01.md` for tradfi). DONE alongside C0 — see
      `tradfi_v9_stage1_finish_2026_07_06.md`. **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. Post-walk: fresh `_index` read — `schema_version=9` for 100% of rows (data-state), `pipeline_mode=`
      partition present + non-null, venue/data_type canonical only, `source` populated, `available_at` non-null. **0
      legacy-only cells.** DONE — `tradfi_v9_stage1_finish_2026_07_06.md` (2026-07-16):
      `total=5,553,198 rows ·     schema_version=9=5,553,198 (100%) · blank pipeline_mode=0 · blank source=0`,
      independently verified. This is the C-GREEN signal `bucket_name_ssot…` Phase 6/7 waits on for the legacy
      `market-data-tick-tradfi-…` decommission. **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. **Orphan sweep + bucket-state evidence (slot/Harsh bucket-state verification 2026-06-02).** Measured
      (Cloud Monitoring `storage/v2/total_count`, live-object): `market-data-tick-tradfi-prd` 5,299,037 (~93% of legacy
      5,696,400), current to `day=2026-05-18` (= legacy). Sample `-prd` parquet
      `day=2026-05-18/asset_group=tradfi/venue=CME/instrument_type=combo/data_type=ohlcv_1m/underlying=SP500/ticks.parquet`
      (244 rows): columns LACK `schema_version`/`source`/`pipeline_mode`/`asset_group` (it has `available_at`) → `-prd`
      is INTERMEDIATE FORM (`asset_group=` in PATH only, NO `pipeline_mode=`). So the E4 walk writes NEW
      `pipeline_mode=` paths → the pre-existing legacy-FORM `-prd` objects become ORPHANS; E5/E7 MUST delete the
      legacy-FORM `-prd` objects too (not only the legacy SOURCE bucket). Legacy carries 3.52M noncurrent objects → E7's
      bulk-delete (incl. the 12 hyphen 0-row-placeholder prefixes) must also purge noncurrent versions; count
      comparisons use Monitoring `type=live-object`. **DONE — orphan_class_E=0, unknown_prefixes=0** corpus-wide,
      confirmed 2026-07-10 17:17:22 UTC (`tradfi_v9_stage1_finish_2026_07_06.md`, fresh full corpus-wide re-sweep).
      **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P1. ~~Notify `tradfi_massive_dual_source` to flip its Task -031 (manifest re-consolidation) — executed
      here as the C-source rider; cross-link both ways.~~ **DONE-MOOT 2026-07-21** — `tradfi_massive_dual_source`'s
      dual-source premise is dead (Massive removed 2026-07-19, purged 2026-07-21; that plan is now
      `status: superseded`). No separate re-consolidation walk exists to coordinate; the C-source rider above already
      covers the live-source case. **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per
      MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. E4 Dry-VM → timing → optimise → full-VM run (144k index rows — modest; no fire-and-forget). **DONE —
      full-VM apply completed 2026-07-06** (`tradfi_v9_stage1_finish_2026_07_06.md`, 7 VMs, exit_code=0, fatal=0, all
      years 2020-2026).
  - **DRY-RUN SCOPING DONE (slot-6 2026-06-03 — sharding/perf scoped, NO apply; full-VM run stays operator-gated):**
    - **Migrator** `migrate_tradfi_to_v9_canonical.py --dry-run` (real GCS `tradfi-prd`): **5,305,520 objects** planned,
      **moved=0 (dry)**, **100,698 L-hyphen placeholders correctly skipped** (0-row guard), **0 errors** → clean,
      date-shardable corpus; placeholder-skip is honest-absence-safe.
    - **Rebuild** `rebuild_tradfi_manifest.py --dry-run`: **704,641 shards / 6 venues**, distribution **CME 486,189
      (69%)** · NYSE 162,519 · NASDAQ 44,203 · ICE 9,452 · CBOE 1,607 · FX 671; **1,984 distinct dates**; CF-11 re-emit
      path exercised (no-op in mock = no local `_index`, works against real GCS).
    - **Sharding/perf recommendation**: shard the full run **by `day=`** (1,984 dates) across VMs; **CME is the heavy
      partition** (69%) → give it dedicated shards; use **workers=32 REST-API** (GCS-object-ops rule, ~250× vs CLI).
      Migrator is `--apply`-gated + dry-by-default; E3 drain + snapshot still precede the real run. **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P2. E5 build-spec reference (superseded by the DONE item above): NEW `rebuild_tradfi_manifest.py`.
      REFERENCE: cefi E5 DONE (mtds@2c3a479b) — copy its structure (optional `pipeline_mode=` regex segment, DAY-level
      list prefix, canonical `-prd` bucket, stamp `pipeline_mode` via
      path-or-`derive_pipeline_mode_for_row(venue,"tradfi",dt)`). The post-migrator tradfi canonical form (the L-hive
      shape + inserted pipeline_mode) is
      `raw_tick_data/by_date/day={D}/pipeline_mode={mode}/asset_group=tradfi/venue={V}/instrument_type={IT}/data_type={DT}/[underlying={U}/]{file}`
      (chain bundles keep `underlying=`). Stamp `source` via `source_string_for(pipeline_mode)` — **live set only:
      databento/yahoo (+ eia where in scope)**; `massive`/`barchart` are legacy-only (removed/retired) and MUST NOT be
      stamped on new writes (`MissingSourceError` gate hard-rejects `source='massive'`). NO hyphen-tree rows (those are
      0-row placeholders excluded by the migrator + deleted at E7). DONE — ran 2026-07-07
      (`tradfi_v9_stage1_finish_2026_07_06.md`, `market-tick-data-service@4ccf52c6`). **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P1. **DONE 2026-07-27 (slot-6, data_engineering)** — E6 CF-7 relabel: `UNKNOWN`/blank venue + blank
      data_type → canonical (diagnose, don't bulk-rename). Re-verified live against the current `-prd` `_index`
      (5,873,616 rows): 0 blank/`UNKNOWN` venue, 0 blank data_type remain — the E5 path-re-derivation walk already
      relabeled every row via object-path re-stamping (per line-54's post-walk verify hook, same evidence). No further
      relabeling action needed; nothing left to diagnose on this axis. **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. E7 Verify: `cf_manifest_audit_2026_06_01.py market-data-tick-tradfi-prd-…` → CF-1…CF-12 GREEN
      data-state (esp. v9 confirmed on real rows — CONFLICT-2); flip CF-coverage in
      `tradfi_master_audit_instructions.md`. ⚠️ IRREVERSIBLE — only after GREEN: hand C-GREEN to L6 → **delete legacy
      `market-data-tick-tradfi` permanently** + **bulk-delete the 12 `day-*` hyphen 0-row-placeholder prefixes** in
      `tradfi-prd` (~110k objects — the issue-doc **Pattern-1 cleanup, now executed here**; pre-delete guard: re-assert
      0-row per object before deleting, abort the prefix on any non-empty object). This SUPERSEDES the
      `gcs_hive_partition_malformed_paths_remediation` Pattern-1 todo. **RE-OPENED 2026-08-02 (operator ruling on
      `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 1c, option A): complete for the MIGRATED corpus only —
      ~2,008 legacy-only tradfi days destroyed without migration (see R1 below) are irrecoverable and NOT part of the
      "100%" claim. Un-checked so no downstream reader treats tradfi as fully complete.** Migrated-corpus apply
      2026-07-06 exit_code=0/fatal=0; E5 rebuild ran 2026-07-07; orphan_class_E=0 corpus-wide 2026-07-10;
      schema_version=9=100% (of the migrated corpus, 5,553,198 rows, 0 blank pipeline_mode/source) confirmed
      2026-07-16** (`tradfi_v9_stage1_finish_2026_07_06.md`). **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. **COVERAGE GAP → IN PROGRESS (was: surfaced by the 0-row-placeholder finding, 2026-06-02).** tradfi
      **equities/ETF (NYSE/NASDAQ)** were originally never genuinely ingested — only the 0-row Massive dry-run
      placeholders existed; the `day=` hive corpus was CME databento only. **UPDATE 2026-07-21**: the Databento
      equity/ETF backfill is RUNNING (SPOT) — NASDAQ g01-g05 + NYSE g01-g05, `ohlcv_1m`+`ohlcv_1s`, window 2023-2026
      (XNAS/XNYS Databento discovery floor 2023-04-15); launched-and-healthy tranche measured 449M+ records, 0 real
      errors, 0 quarantine (`tradfi_consolidated_closeout_2026_07_18.md`). Equities/ETF are being ingested via Databento
      — Massive is NOT the ingest path (removed/purged); drop the `tradfi_massive_dual_source` cross-link. **UPDATE
      2026-07-26 (plan-reconcile, MEASURED)**: that equity/ETF fleet is no longer running —
      `gcloud compute operations list` on project `central-element-323112`, filtered
      `targetLink~tradfi-bf-nasdaq OR targetLink~tradfi-bf-nyse`, shows the last `tradfi-bf-{nasdaq,nyse}-ohlcv-1m-g0*`
      shard deleted 2026-07-21T17:34:04Z, and zero `tradfi-bf-*` instances exist in `central-element-323112` in ANY
      state as of 2026-07-26T02:20Z. So this item is no longer "track against a running backfill" — it is now purely
      **manifest-verify the 2023-2026 NASDAQ/NYSE window** (VM completion is not row-capture proof). Track remaining
      coverage against that manifest verification, not as a never-ingested gap. Until fully backfilled, the manifest
      must still show not-yet-covered cells as MISSING/`attempted_unattempted`, never `empty_confirmed` (CF-11).
      **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**
      **UPDATE 2026-07-27 (MEASURED, `tradfi_satellite_ao_dispatch_batch4-007`, slot-5/data_engineering) — pure
      manifest-count verify, NOT a fresh pipeline-check run** (that different, heavier method is
      `tradfi_consolidated_closeout_2026_07_18.md`'s own open P2 todo — not conflated here). Single-object read of the
      live `-prd` `_index` (`market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`,
      5,876,351 total rows, no bucket walk), scoped to venue∈{NASDAQ,NYSE} × data_type∈{ohlcv_1m,ohlcv_1s} ×
      date≥2023-04-15 (2,087,240 scoped cells). Per-year `capture_status` breakdown:

      | venue | data_type | year | captured | empty_confirmed | expected_unattempted | attempted_failed |
                                                                                                                                                                                                                                              |---|---|---|---|---|---|---|
                                                                                                                                                                                                                                              | NASDAQ | ohlcv_1m | 2023 | 10,062 | 79,989 | 8,378 | 0 |
                                                                                                                                                                                                                                              | NASDAQ | ohlcv_1m | 2024 | 15,703 | 136,411 | 11,337 | 0 |
                                                                                                                                                                                                                                              | NASDAQ | ohlcv_1m | 2025 | 15,784 | 139,699 | 11,176 | 0 |
                                                                                                                                                                                                                                              | NASDAQ | ohlcv_1m | 2026 | 7,303 | 41,772 | 21,851 | 0 |
                                                                                                                                                                                                                                              | NASDAQ | ohlcv_1s | 2023 | 9,838 | 78,871 | 0 | 0 |
                                                                                                                                                                                                                                              | NASDAQ | ohlcv_1s | 2024 | 14,461 | 135,757 | 0 | 0 |
                                                                                                                                                                                                                                              | NASDAQ | ohlcv_1s | 2025 | 14,813 | 171,646 | 0 | 0 |
                                                                                                                                                                                                                                              | NASDAQ | ohlcv_1s | 2026 | 7,087 | 58,629 | 18,441 | 0 |
                                                                                                                                                                                                                                              | NYSE | ohlcv_1m | 2023 | 88,242 | 19,099 | 7,479 | 0 |
                                                                                                                                                                                                                                              | NYSE | ohlcv_1m | 2024 | 129,385 | 22,686 | 10,470 | 0 |
                                                                                                                                                                                                                                              | NYSE | ohlcv_1m | 2025 | 113,015 | 19,185 | 10,838 | 0 |
                                                                                                                                                                                                                                              | NYSE | ohlcv_1m | 2026 | 70,143 | 17,032 | 18,028 | 85 |
                                                                                                                                                                                                                                              | NYSE | ohlcv_1s | 2023 | 88,010 | 17,859 | 0 | 0 |
                                                                                                                                                                                                                                              | NYSE | ohlcv_1s | 2024 | 128,330 | 21,223 | 0 | 0 |
                                                                                                                                                                                                                                              | NYSE | ohlcv_1s | 2025 | 112,506 | 52,137 | 0 | 0 |
                                                                                                                                                                                                                                              | NYSE | ohlcv_1s | 2026 | 70,019 | 46,864 | 15,512 | 0 |

                                                                                                                                                                                                                                              **Totals**: NASDAQ ohlcv_1m 48,852 captured / 397,871 empty_confirmed / 52,742 expected_unattempted (0 failed);
                                                                                                                                                                                                                                              NASDAQ ohlcv_1s 46,199 / 444,903 / 18,441 (0); NYSE ohlcv_1m 400,785 / 78,002 / 46,815 (85); NYSE ohlcv_1s
                                                                                                                                                                                                                                              398,865 / 138,083 / 15,512 (85). **Verdict: PARTIALLY FILLED, asymmetric by venue** — NYSE is well-covered
                                                                                                                                                                                                                                              (72-76% `captured`), NASDAQ is mostly `empty_confirmed` (79-87%) with only ~9-10% `captured`; both venues still
                                                                                                                                                                                                                                              carry a real not-yet-attempted remainder (`expected_unattempted`: NASDAQ 71,183 combined, NYSE 62,327 combined)
                                                                                                                                                                                                                                              that needs an actual fetch attempt before this axis can close — this is NOT the 2026-06-02 never-ingested state
                                                                                                                                                                                                                                              (real Databento data now exists at volume for both venues), but it is also not fully filled.
                                                                                                                                                                                                                                              `attempted_failed` is negligible (170 rows total, all NYSE 2026). **Restating the remainder, not flipping the
                                                                                                                                                                                                                                              checkbox** — the NASDAQ `empty_confirmed`/`captured` skew reads as plausible honest-absence (lower-liquidity
                                                                                                                                                                                                                                              names genuinely not printing every 1m/1s bar vs NYSE blue-chip volume), not an obvious write-path defect, but is
                                                                                                                                                                                                                                              flagged here rather than silently absorbed for whoever re-triages this axis next.
                                                                                                                                                                                                                                              **NOTE (na-eligibility-audit 2026-07-27, now executed — see above)**: this manifest-verify item was claimed in
                                                                                                                                                                                                                                              `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` (todo 8); see that plan's checkbox for shipped evidence.

**SCOPE GATE (round-9 combined RECLASSIFY + satellite-extraction sweep, 2026-08-09)**: the remaining "needs an actual
fetch attempt" work this item describes — filling the NASDAQ/NYSE `expected_unattempted` remainder for years OTHER than
2026 — is now explicitly `BLOCKED-OPERATOR-DECISION` per
`/plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`'s same-day ruling: immediate equities
backfill work is narrowed to **year 2026 only**, with "completing the full historical equities corpus to 100%" (this
item's 2023-2025 remainder) explicitly gated until November 2026. Do not dispatch further NASDAQ/NYSE multi-year
backfill off this item before then — cite that ruling doc, not this checkbox, as the current gate.

- [ ] [CODE] P1. ⑦ tradfi could-exist denominator seed — build the `--catalog-path` parquet from the tradfi IS catalog
      (per-instrument lifecycle: `instrument_id`/`instrument_type`/`venue`/`available_from`/`available_to`) and run
      `enumerate_expected_universe.py --asset-group tradfi --catalog-path <catalog> --apply-write` against the canonical
      `_index` so the raw-tick denominator == could-exist universe (active-but-uncaptured instruments seeded
      `expected_unattempted`). Verify on a VM (GCS flaky locally); confirm `_enumerate_v2_tradfi` row-key/data_types
      match the tradfi captured atom; add a regression (IS-universe ⊃ manifest ⇒ denominator doesn't shrink). The
      mechanism + bucket fix are done; this is the per-AG catalog build + run + verify. parent_epic: mtds_mdps_master.
      **SLOT-6 G1 DRY-RUN PROVEN (2026-06-07) — see the `## G1` section below for full evidence; `--apply-write` stays
      GATED (gate-b catalogue liveness + gate-c v9 indices).** **CITATION ADDED (na-eligibility-audit 2026-08-09,
      dispatch agt-3df41f):** gate-b's "re-feed by_date via the Databento IS reference-data adapter" is the same
      live-Databento-fetch dependency items 6/9 below already cite as BLOCKED-OPERATOR-DECISION — see
      `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md` (status: blocked, filed today).
      This item was missing that citation despite sharing the identical gate; added here for consistency, not a new
      blocker. **UNBLOCKED 2026-08-10** — the cited doc's account-level Databento suspension is confirmed resolved (live
      `metadata.list_datasets()` verification, see that doc's Progress Log); gate-b's re-feed is now genuinely runnable,
      not just theoretically so. **SLOT-6 NOTE (2026-06-04, atom-alignment VERIFIED):** read
      `instruments-service/scripts/enumerate_expected_universe.py::_enumerate_v2_tradfi` — it respects
      available_from/available_to lifecycle (date<af → EXPECTED_INSTRUMENT_NOT_LISTED; date>at →
      EXPECTED_INSTRUMENT_DELISTED; alive + no manifest row → `expected_unattempted`) and builds the row_key from
      `(venue, chain="", data_type, instrument_type, instrument_id, league_id="", date)` = the tradfi per-instrument
      captured atom. Logic CONFIRMED correct. **Remaining is genuinely VM + POST-MIGRATION gated**: `--apply-write`
      hard-requires `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<tag>` (per-VM shard isolation, refuses locally) AND must
      seed the v9 `_index` AFTER the canonical `--apply` migration (seeding the pre-migration v8 corpus would be
      rewritten by the walk). So this rides post-migration on a VM — not a local task. Open work = catalog-parquet
      build + VM `--apply-write` run + the IS-universe⊃manifest regression test. **✅ CODE PIECE DONE (slot-6
      2026-06-08, is@7ac22635):** the IS-universe⊇manifest regression
      `test_tradfi_v2_denominator_is_could_exist_universe_not_just_manifest` is shipped (mixed captured/uncaptured
      tradfi catalog → enumerator seeds `expected_unattempted` for the un-captured instrument + SKIPS (does not drop)
      the captured one → seeded universe ∪ manifest ⊇ manifest, denominator never shrinks; the tradfi mirror of the
      proven defi `test_defi_v2_denominator_is_could_exist_universe_not_just_manifest`). IS `quality-gates.sh --no-fix`
      exit 0 (268s, sentinel 7ac22635). **Item stays `- [ ]` — the catalog-parquet build + the gated VM `--apply-write`
      seed are OPERATIONAL/apply-time (bucket-B), not code.** **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **G1.run `--apply-write` for tradfi — GATED, NOT runnable this wave.** Per-gate readiness:
  - **(a) Slot-7 PART C G1-foundation code: 🟢 GREEN (RESOLVED 2026-06-08, slot-6).** Era-B bundle rollup LANDED
    (uac@ae70338d options_chain/futures_chain are instrument_types→{trades} + is@74df991d/687d1443 per-underlying
    rollup) + my tradfi `future`/`spot_pair` validity rows (uac@576f8fa8). Enumerate re-run (scan-only, 2026-06-04..05):
    **587,990 → 24,914 (Era-B bundle) → 17,928 (matrix fix)** — the ~563K false per-contract OPTION/COMBO candidates are
    GONE; report verified 0 per-contract OPTION/COMBO, 0 data_type=options_chain (Era-B trades model), 0 impossible
    pairs, FUTURE now 6 data_types; 17,928 = exact Σ(alive × valid-dts × 2 days). Original RED ↓ retained for context.
  - **(a-orig) Slot-7 PART C G1-foundation code: 🔴 RED (re-validated 2026-06-07)** — the G1-ENUM shape-aware producer
    LANDED (@6ea46565) and I RE-RAN tradfi enumerate on it, but the count barely moved (588,798→587,990) because
    tradfi's dominant types (OPTION/COMBO/FUTURE/SPOT_PAIR) are UNMAPPED in the validity matrix AND — the real blocker —
    **tradfi options/combos are captured at BUNDLE grain (options_chain/combo/futures_chain) while the catalogue +
    enumerate are per-contract → ~563K false candidates (grain mismatch).** Gate-(a) needs the **G1-ENUM bundle-grain
    rollup for tradfi** (catalogue emits options_chain/futures_chain bundles + the matrix entries) — see the 🔴
    ROOT-CAUSE FINDING todo above. Not green until that lands and the re-run drops to a sane count.
    - **RE-VERIFIED slot-6 2026-06-07 session-2 — gate-(a) STILL RED, PART A still the blocker.** (1) Live UAC accessor
      confirms the matrix gap: `valid_data_types_for_instrument_type("tradfi", X)` returns **None** for `option` /
      `combo` / `options_chain` / `futures_chain` / `future`
      (equity/etf/index/bond/cds/event_contract/commodity/currency ARE mapped). (2) The catalogue instrument_type
      distribution (sampled day=2026-06-07, 33,258 rows) is **OPTION 31,282 (94%)** · FUTURE 1,163 · EQUITY 197 · ETF 67
      · INDEX 1 · SPOT_PAIR 1 → the over-fan is per-contract OPTION. (3) `build_instrument_catalogue.py` STILL emits NO
      `options_chain`/`futures_chain` bundle rows (only prediction multi-grain) and the master coordinator confirms
      "PART A NOT shipped" — slot-7's `dd7fa100 grain_for_instrument_type SSOT` is progress, not the catalogue emission.
      The matrix fix (above) MUST co-land with PART A (a lone `option→frozenset()` makes options vanish =
      false-absence). **Per the operator gate, the enumerate re-validation stays HELD until slot-7 confirms PART A
      green.** The MTDS migrator + instruments-store v9 prep are GREEN (below).
  - **(b) tradfi IS instrument backfill complete: ❌ UNMET** — IS `by_date` capture **degraded 16-18K→~2/day after
    2026-05-04, stopped after 2026-05-22** (freeze FINDING in
    `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`); the catalogue marks **651,661/684,372 (95%) delisted** →
    liveness PROVISIONAL. Seeding `expected_unattempted` against a frozen catalogue would write a WRONG could-exist
    denominator. **Unblock (re-scoped 2026-07-21 — Massive removed/purged, its adapter is dead): re-feed `by_date/` via
    the Databento IS reference-data adapter (`instruments_service/reference_data/router.py::_route_databento`,
    `DatabentoReferenceDataAdapter`, `--source databento`) → regenerate the catalogue → THEN seed.** Not yet run under
    this replacement path — do not assume gate-b is unblocked until a fresh liveness read confirms `by_date/` is
    current. **CITATION ADDED (na-eligibility-audit 2026-08-09, dispatch agt-3df41f):** this Databento IS
    reference-capture re-feed is now ALSO BLOCKED-OPERATOR-DECISION per
    `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md` (status: blocked, filed today) —
    same citation items 6/9 below already carry; added here for consistency since this is the identical gate-b
    dependency. **UNBLOCKED 2026-08-10** — Databento account access confirmed live-restored (see that doc); this re-feed
    is now dispatchable, just not yet run.
  - **(c) accurate UAC + v9 indices: ⏳ TOOL-READY (UPDATED slot-6 2026-06-07 session-2) — the G1-V8 migrator is now
    BUILT (is@febb899e) + tradfi dry-run GREEN (20,388 `_index` rows → v9 100%, all CF stamps; see Step-1 UPDATE).** The
    `instruments-store-tradfi` `_index` is still v8 ON DISK (the dry-run only PROJECTS v9) AND the
    `market-data-tick-tradfi-prd` `_index` the seed writes is still v8 (CONFLICT-2). So gate-c is no longer "blocked on
    a migrator that doesn't exist" — the tool is ready; what remains is the gated `--apply` RUN. Once G0 is green, run
    `migrate_instruments_store_v9 --asset-group tradfi --apply` on `instruments-store-tradfi-prd` (pre-migration drain +
    snapshot first). `--apply-write` must seed the **post-migration v9 `_index`** (seeding the v8 corpus would be
    rewritten by the walk) — so G1.run rides AFTER that v9 walk. It also hard-requires a VM
    (`MANIFEST_PER_VM_SHARDS=true` + `VM_NAME`).
  - **Disposition**: dry-run PROVEN (Step 2); the irreversible seed waits on (b)+(c). NOT `DEFERRED` — gated with named
    unblocks (Databento IS reference-capture restore + the v9 walks; Massive capture is dead — removed/purged
    2026-07-19/21). parent_epic: mtds_mdps_master. **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`,
    2026-07-13 per MTDS consolidation ruling.)**

- [ ] [INFRA] P1. **UNGATED 2026-08-10** — the billing-suspension gate is resolved (live-reverified that day, 3 real
      Databento calls across all 3 core datasets, see tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md).
      **UNBLOCKED 2026-08-10** — the databento account-level billing-suspension gate is lifted (live
      `metadata.list_datasets()` verification succeeded, no auth/suspended error; see
      `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`'s Progress Log). Prior gate
      (superseded, kept for history): ~~BLOCKED-OPERATOR-DECISION (databento account billing-suspended 2026-08-09, see
      /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md)~~ — this todo is itself still gated
      on the Databento IS reference-capture restore below (gate-b re-feed): that re-feed is now dispatchable (Databento
      is reachable again) but has NOT yet been RUN, so this scheduler item stays open, not newly unblocked in practice.
      **Wire the tradfi `build_instrument_catalogue.py` daily rollup scheduler (GATED on gate-b capture restore).**
      FINDING (slot-6 2026-06-07): the G1 lifecycle producer `build_instrument_catalogue.py` has **NO terraform
      scheduler for ANY asset group** (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04` [INFRA] P1 "Trigger on
      every instruments update" is still `[ ]`, owner vm-cross-cutting). The two TFs that DO exist —
      `deployment-service/terraform/gcp/{catalogue_regen_scheduler,instrument_catalogue_scheduler}.tf` — run a DIFFERENT
      artefact (`generate_instrument_catalogue.py`, the availability-matrix), and their instruments-store `for_each`
      **OMITS tradfi** (only cefi/defi/sports/prediction) AND uses legacy no-env bucket names (`-central-element-…` not
      `-prd-`). So even the matrix regen never reads tradfi. **Gated** behind gate-b (a scheduler over a frozen
      `by_date/` self-perpetuates a stale catalogue) — wire once IS reference-capture (Databento-based; the Massive
      capture path is removed/purged) restores `by_date/`. Owner: vm-cross-cutting (shared producer scheduler) + slot-6
      (confirm tradfi inclusion). Repo: deployment-service (terraform). parent_epic: mtds_mdps_master. **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [SCRIPT] P2. **Operator-ruled 2026-07-29 (interactive decision session): run the dry-run now, feed result into
      Phase C.** Resolved by adding a new `[DATA]` todo to `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s
      Phase C "Denominator / catalogue-completeness" todo to actually execute
      `reconcile_phantom_manifest_rows_all.py --asset-group tradfi --dry-run` and record the result there — **explicitly
      distinct from `phantom_captures_tradfi_2026_06_28.md`** (an archived, already-closed, unrelated
      phantom-manifest-rows finding doc). **⑫ FOLLOW — re-run
      `reconcile_phantom_manifest_rows_all.py --asset-group tradfi --dry-run` AFTER the tradfi v9 object `--apply`** to
      confirm 0 false phantoms across all 5 source pipeline_modes (batch_databento/massive/barchart/yahoo/eia). The
      prefix_tpls fix (is@5e8d192d) is verified by inspection + `batch_massive` presence; the live re-run is gated on
      the apply. Repo: instruments-service. parent_epic: manifest_master. **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

      **ATTEMPTED 2026-07-30 — could NOT complete on the shared planning host, aborted for host-safety; needs a
                                                                                                                                                                                                                          dedicated VM instead.** Ran `GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV=prod .venv/bin/python
                                                                                                                                                                                                                          scripts/reconcile_phantom_manifest_rows_all.py --asset-group tradfi --dry-run` live. The manifest load
                                                                                                                                                                                                                          (`merge_canonical_with_outstanding_shards` over the 5,894,011-row `-prd` `_index` + its outstanding
                                                                                                                                                                                                                          `_index/per_vm/` shards — tradfi has an extensive VM-launch history in this plan family) drove the process to
                                                                                                                                                                                                                          ~13GB RSS and growing swap (5.9Gi→9.3Gi) on a host with only 15Gi total memory and other concurrent sessions
                                                                                                                                                                                                                          active, with zero log progress past "Loading manifest" for 6+ minutes (flat progress = stall per
                                                                                                                                                                                                                          async-wait-discipline). Killed it (`kill -9`) before it either OOM-crashed or started thrashing badly enough to
                                                                                                                                                                                                                          harm other concurrent work on the shared host — this is the same "heavy I/O/heavy-compute-on-shared-host" class
                                                                                                                                                                                                                          the infra codex SSOT gates to a dedicated VM, not the interactive/planning host, and the ⑫ FOLLOW todo's "the
                                                                                                                                                                                                                          dry-run is runnable now" framing undersold the actual resource cost for tradfi's corpus size. **Not completed
                                                                                                                                                                                                                          this session** — re-run via a proper VM launch (or `--start-date`/`--end-date`/`--venues` scoping to shrink the
                                                                                                                                                                                                                          per-VM-shard merge) rather than the shared host. No mutation attempted (never got to `--apply`, and this was
                                                                                                                                                                                                                          `--dry-run` throughout).

- [ ] [DATA] P0. **R1 RUNBOOK — the tradfi `migrate_tradfi_to_v9_canonical --apply` MUST include `--also-legacy`** to
      cover the 2,008-day no-env `market-data-tick-tradfi` corpus, then decommission that legacy bucket after the
      canonical copy is G7-verified. Without the flag, 2,008 legacy days orphan. Repo: market-tick-data-service.
      parent_epic: mtds_mdps_master. Provenance: orphan-coverage drill-down, slot-6 2026-06-08. **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)** — **AUDITED
      2026-07-26, VIOLATION CONFIRMED, DATA-LOSS FINDING FILED.** **RULED 2026-08-02 (operator ruling on
      `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 1c, option A): the E7/R1 contradiction is resolved — E7
      now reads "complete for the migrated corpus only," these ~2,008 legacy-only days are acknowledged irrecoverable
      (the legacy bucket is confirmed permanently deleted, so `--also-legacy` cannot be re-run against it). Checkbox
      stays OPEN as a tracked data-loss record, not as a pending contradiction** — see
      `/plans/archive/issues/tradfi_legacy_bucket_deleted_without_also_legacy_migration_2026_07_26.md` for the full
      evidence (path corrected 2026-08-07, na-eligibility-audit — the issue doc has since been archived:
      `status:     resolved`, operator decision 2026-07-26 was to accept the loss). Code-verified
      (`deployment-service/scripts/vm/launch-canonical-migration-vm.sh`@`77cfcda`, the commit live at apply time) that
      the 2026-07-06 completing apply's launcher NEVER passes `--also-legacy`. The one attempt that did use the flag
      (`canonical-migration-tradfi-20260629-053023`) OOM-crashed after copying only ~1% (37k/3.8M processed_candles) and
      was never resumed with the flag. The legacy bucket (`market-data-tick-tradfi-central-element-323112`) is confirmed
      permanently deleted (ADC `bucket.exists() ==     False`). Full evidence + final decision (accept the loss,
      resolved 2026-07-26):
      `/plans/archive/issues/tradfi_legacy_bucket_deleted_without_also_legacy_migration_2026_07_26.md`.

- [x] ✅ [DATA] P1. **R2 DELETE-AFTER sweep — after the tradfi v9 `--apply` + G7 byte-verify, run the gated delete of
      the old-format source paths** (every **DELETE-AFTER=YES** row in the drill-down: bare `day=*/asset_group=tradfi/`
      without `pipeline_mode=`, the 12 `day-*` hyphen dirs, old processed_candles, the whole legacy bucket, the
      instruments-store E6 bare paths). Capture the migrator dry-run's planned-copy counts per source/branch into a G7
      ledger so the delete set == the verified copy set (no orphan, no premature delete). Repos:
      market-tick-data-service + instruments-service. parent_epic: mtds_mdps_master. Provenance: orphan-coverage
      drill-down, slot-6 2026-06-08. — **AUDITED 2026-07-26**: read-only GCS listing (ADC) of the 3 still-open targets —
      bare `day=*` without `pipeline_mode=` (0 objects), old-shape `processed_candles/` (0 non-canonical in a
      50,000-object sample), instruments-store E6 bare `day=` paths (0 objects) — all CLEAN, nothing further to delete.
      The 4th target ("the whole legacy bucket") was already destroyed via E7, separately audited above as the R1
      violation — not a clean R2 outcome, tracked there instead. Full evidence:
      `issues/tradfi_legacy_bucket_deleted_without_also_legacy_migration_2026_07_26.md`.

**Chain data_types beyond `trades` (operator's tardis/implied-vol question, 2026-06-08):** the migrator is **path-only —
it copies EVERY object under a day regardless of `data_type`** (`_list_day` lists all `.parquet`; `_canon_rel` preserves
`instrument_type`+`data_type`), so **NO `data_type` is ever dropped by the migration** — whatever a chain bundle carries
survives byte-for-byte. **tradfi (Databento) chains carry only `{trades, ohlcv_1m}`** (probed
`instrument_type=options_chain` → trades 19 / ohlcv_1m 3; `futures_chain` → trades 9 / ohlcv_1m 13; Databento does NOT
compute implied vols) — so there is no IV data at risk in tradfi. The ONLY place a chain's non-`trades` data_types
matter is the **validity matrix could-exist SEED** (`options_chain/futures_chain → {trades}`), which is exactly the ⑥/⑦
G1.run-seed finding (the matrix is too narrow for chain bundles that also hold `ohlcv_1m`/`tbbo`) — a denominator
concern, NOT data loss. **Tardis/cefi caveat flagged to slot-3 + the matrix owner**: if tardis options_chain bundles
carry `derivative_ticker` (mark IV / greeks) or `book_snapshot_5` as distinct data_types, the SAME matrix-too-narrow gap
applies there with first-class IV data — folded into the coordinator ⑥/⑦ finding for cefi verification (migration still
preserves it; the seed must admit it). **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13
per MTDS consolidation ruling.)**

- [ ] [INFRA] P2. **PRE-EXISTING UAC QG RED (not tradfi; flagged slot-6 2026-06-08) — blocks the UAC `--no-fix` sentinel
      → no clean UAC quickmerge fleet-wide.** `tests/unit/test_schema_version_matrix.py` 3 failing
      (`test_green_status_when_versions_match` / `test_na_schema_version_does_not_trigger_red` /
      `test_load_providers_green_when_versions_match`): assert `binance.computed_status == "green"` but it is `"yellow"`
      (schema_version provider-status drift). **Proven PRE-EXISTING** (stash-test: fails identically on clean LDR
      without my matrix change) + **unrelated** to the G1-ENUM data_type validity matrix + **outside the tradfi AG**
      (the schema_version provider subsystem is cefi/cross-cutting). My `uac@576f8fa8` adds ZERO net-new failures (8,617
      pass, ruff clean). Owner: the schema_version-provider/cefi AG or vm-cross-cutting — align the provider
      schema_version registry so binance reads green. Repo: unified-api-contracts. parent_epic: manifest_master.
      **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] ❌ [DATA] P1. **UNGATED 2026-08-10** — the billing-suspension gate is resolved (live-reverified that day, 3 real
      Databento calls across all 3 core datasets, see tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md).
      **UNBLOCKED 2026-08-10** — Databento account access confirmed live-restored (`metadata.list_datasets()` succeeded,
      no auth/suspended error; see `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`'s
      Progress Log). Prior gate (superseded, kept for history): ~~BLOCKED-OPERATOR-DECISION (databento account
      billing-suspended 2026-08-09, see /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md)~~
      — the live "Replacement path" below needs a real Databento fetch, now genuinely runnable (not yet run — see
      `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s citation below for where this is tracked live). ~~NEXT
      — run Massive tradfi reference capture → regenerate catalogue → unblock gate-b (VM, requires live
      `MASSIVE_API_KEY`). With the adapter shipped (above), run IS instrument capture with `--source massive` to refill
      `instrument_availability/by_date/` to today.~~ **SUPERSEDED 2026-07-21** — Massive removed as a tradfi source
      (operator ruling 2026-07-19, `uac@a2beed46`) and subscription terminated + data purged (operator Option C
      2026-07-21). No `--source massive` capture; a `source='massive'` write now hard-rejects (`MissingSourceError`,
      2026-07-20 ruling). **Replacement path**: run IS instrument capture with `--source     databento`
      (`DatabentoReferenceDataAdapter`, `instruments_service/reference_data/router.py`) to refill
      `instrument_availability/by_date/` → regenerate the catalogue
      (`build_instrument_catalogue --asset-group tradfi --apply`) → THEN re-check whether liveness still marks ~651K
      instruments delisted → unblocks gate-b → then G1.run `--apply-write` (Step 3) becomes runnable. Not yet run under
      this replacement path (do not assume gate-b is unblocked). Repo: instruments-service. parent_epic:
      mtds_mdps_master. **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)** **CITATION (na-eligibility-audit 2026-08-02, tradfi tranche)**: this exact replacement
      path is now tracked live as `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s 2026-07-29 operator-ruled
      "run the full Databento re-feed chain to completion" todo — cite/track there going forward. That doc is itself
      `status: draft`/`assigned_vm: NA` (not yet an active dispatched plan), so this is dedup within the NA corpus, not
      a duplicate-of-an-AO-plan citation fix.

### From `macro_econ_adapter_scaffolds_2026_06_09.md` (archived 2026-07-13 -- Macro/alt-data free adapter scaffolds (fear_greed / CFTC COT / Baker Hughes / EIA))

- [ ] [BACKEND] P1. **UNBLOCKED 2026-08-07 (operator, via consolidated NA-blocker-digest audit) — key provisioned.**
      Operator supplied the free EIA API key directly; provisioned into GCP Secret Manager as `eia-api-key` (project
      `central-element-323112`) — the exact name `eia_adapter.py::get_api_key("eia-api-key")` expects. Verified live:
      `gcloud secrets versions list eia-api-key` shows version 1 enabled; byte-length check confirms the value landed
      uncorrupted (no truncation/extra newline). **Value never written to any git-tracked file or this doc — GSM is the
      sole store.** Remaining work: run the live integration test
      (`tests/integration/test_macro_adapters_integration.py::test_eia_live`) + the EIA backfill, now unblocked. Old
      credential-request pointer (`ikenna_orchestrator/pings/slot_3.md`) is superseded — key already in hand.
      **(MIGRATED FROM: `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [OPERATOR-DECISION] P1. **RULED 2026-08-07 (operator, via consolidated NA-blocker-digest audit) — THIRD option,
      neither of the two originally posed.** Do NOT revive `altdata` as a standalone `asset_group`; do NOT model macro
      as a shared cross-asset axis either. Instead: **wrap each source into whichever existing AG is topically closest
      to it** — general macro/econ data (EIA, FRED-shaped sources) → `tradfi`; crypto-native alt-data → `defi`;
      per-source AG assignment to be finalized when wiring the GCS-shard write path below (each of the 4 adapters picks
      its own `asset_group`/bucket individually, not one shared decision). Unblocks the GCS-shard write + manifest
      `record_captured` + bucket (`resolve_bucket_name`) wiring for all four sources (adapters today return
      `CanonicalOnChainMetric` lists; they do NOT yet write GCS shards). Provenance: audit Open Question #1. **(MIGRATED
      FROM: `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS consolidation ruling.)**
      **(na-eligibility-audit 2026-08-10, tradfi tranche, dispatch agt-a70469): closing — the decision itself is fully
      answered in-place above (THIRD option ruled 2026-08-07), and every downstream action it unblocks is already
      separately tracked in this doc's own dependent todos (honest-coverage-gate registration, sequenced behind the MTDS
      wiring todo). This checkbox was tracking "make the decision," not "do the wiring" — it was a missed flip, not open
      work.**

- [ ] [DATA] P2. **(RETAGGED 2026-08-08, na-eligibility-audit — was `[OPERATOR-DECISION]`; the P1 asset-group ruling
      above landed 2026-08-07, this item is no longer gated on an undecided operator call.)** Honest-coverage-gate
      registration — add the macro key to `expected_coverage.py` + `coverage_start` dates so macro can no longer be
      silently empty. Now sequenced behind the MTDS wiring todo directly below (needs the GCS-shard write path to exist
      before there's anything to register coverage against). **(MIGRATED FROM:
      `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [SCRIPT] P2. **(2026-08-08 na-eligibility-audit: no longer gated on OPERATOR-DECISION #1 — that ruling landed
      2026-08-07, see P1 above.)** Wire the macro adapters into an MTDS handler + CLI operation + manifest emission,
      routing each of the 4 sources to its ruled asset-group home (general macro/econ → tradfi; crypto-native → defi) —
      the GCS shard-write path adapters don't yet have. This is genuine, non-trivial multi-integration design/build work
      (4 sources × handler + CLI + manifest wiring), not yet cleanly scoped as a single bounded AO todo; recommend a
      follow-up pass properly scopes it into a dedicated plan or a decomposed todo set before dispatch. **(MIGRATED
      FROM: `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS consolidation ruling.)** **CITATION ADDED
      (na-eligibility-audit 2026-08-09, dispatch agt-3df41f):** this item's scope directly governs whether/how the 4
      macro adapters (incl. EIA) get registered — cross-reference the 2026-08-03 operator ruling in the archived
      `tradfi_adapter_dead_code_fallback_audit_2026_07_25.md` Finding M-2 ("document, don't register or delete") before
      wiring any of them into `factory.py`'s `VENUE_REGISTRY`/`PLANNED_VENUES`; this doc's 2026-08-07 asset-group ruling
      above authorizes wiring the write path but does not by itself supersede M-2's standing "don't register" text —
      confirm the two are reconciled before dispatch, not assumed.

- [ ] [DOC] P2. Now that the asset-group decision has landed (2026-08-07 ruling, see P1 above), document the
      macro/alt-data capture path in `codex/02-data/` once the MTDS wiring todo above lands (no new contract was
      introduced by the scaffolds themselves — they reuse `CanonicalOnChainMetric` + the existing
      adapter/`classify_venue_error`/`ADAPTER_FETCH_FAILED` patterns). **(MIGRATED FROM:
      `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [SCRIPT] P2. **CLOSED 2026-07-27 (na-eligibility-audit) — checkbox was stale, this doc's OWN "Deferred work —
      migrated to:" section below already confirmed it resolved.** PM-template gap: `base-library.sh` QG writes
      `.qg_content_sentinel` but `quickmerge.sh` `--agent` fast-path (STAGE 3) verifies `.qg_last_passed_sha` — so the
      agent quickmerge fast-path was structurally unsatisfiable for **library** repos (UAC), whereas `base-service.sh`
      writes the sha sentinel. Fix landed separately: `scripts/quality-gates-base/base-library.sh` now writes
      `.qg_last_passed_sha` on a complete green run too (see the "SENTINEL CONTRACT (parity with base-service.sh, WS-L
      #1014)" block, ~line 1467-1484, this file). No further code action required. **(MIGRATED FROM:
      `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS consolidation ruling.)**

## Deferred work — migrated to:

This plan carries 5 bare `DEFERRED` mentions, all in the `macro_econ_adapter_scaffolds_2026_06_09.md` migrated-in block.
Re-audited 2026-07-21:

- **4 items** (`altdata` asset_group home decision; honest-coverage-gate registration; MTDS handler/CLI wiring; codex
  doc update) originally formed one dependency chain, all gated on the `[OPERATOR-DECISION] P1` item directly above them
  ("`altdata` home — revive `altdata` as a real `asset_group` vs model macro as a SHARED cross-asset axis"). **UPDATE
  2026-08-08 (na-eligibility-audit):** that P1 ruling landed 2026-08-07 (THIRD option — per-source AG assignment,
  general macro/econ → tradfi, crypto-native → defi; see P1's own text above). The chain is no longer operator-blocked:
  the honest-coverage-gate and codex-doc items are now sequenced behind the MTDS handler/CLI/manifest wiring item
  (retagged `[DATA]`/confirmed `[SCRIPT]` above), which is itself real, non-trivial multi-integration design/build work
  — this plan (post-migration from the archived `macro_econ_adapter_scaffolds_2026_06_09.md`) remains the current owner.
- **1 item** ("PM-template gap: `base-library.sh` QG writes `.qg_content_sentinel` but `quickmerge.sh --agent` verifies
  `.qg_last_passed_sha`") — investigated the live file: `scripts/quality-gates-base/base-library.sh` (this repo)
  **already writes `.qg_last_passed_sha` on a full green run** (see the "SENTINEL CONTRACT (parity with base-service.sh,
  WS-L #1014)" block, ~line 1467-1484) — the exact fix this item describes has landed separately. **Already resolved** —
  the checklist item text is stale (left un-flipped by whoever shipped the sentinel-parity fix); no successor plan
  needed, no further code action required.

## Progress Log

> **Folded in 2026-07-24** from the M-1 coordinator's (`data_completion_to_100_all_ag_2026_06_21.md`) shared Progress
> Log (plan line-cap remediation, `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` bucket-(d) split,
> operator-approved) — every TradFi-lane-tagged dated entry, moved verbatim, in original chronological order. M-1
> retains the cross-cutting/multi-AG entries; read M-1's Progress Log too for the full program-level narrative.

### 2026-06-21 ~23:00 — DEPLOYED + VERIFIED: live_databento (prod-confirmed) + equity ohlcv_1s (capturing) + MDPS batching

Operator said "do both" (live_databento deploy + MDPS batching) + fetch equity 1s. Executed all three end-to-end with
clean tarball rebuilds (from origin/LDR worktrees, NOT the peer-WIP workspace) + VM relaunches:

1. **live_databento — DEPLOYED + PROD-CONFIRMED.** Rebuilt UAC tarball (UAC@1205ae44) + relaunched the live producer
   (`mtds-live-tradfi-cme-trades-20260621-224032`). Verified the actual per-VM manifest rows:
   `pipeline_mode = {'live_databento': 4}` (was live_massive). ✅

2. **equity ohlcv_1s — DEPLOYED + CAPTURING.** Added ohlcv_1s to `VENUE_DATA_TYPE_CAPABILITIES`+`expected_coverage`
   NASDAQ/NYSE (UAC@87c60b50) → pre-flight now fetches it. Launched NASDAQ+NYSE 1s year-shard backfill (8 VMs).
   Verified: `dt=ohlcv_1s … captured=45` (NASDAQ), `captured=158` (NYSE). ✅

3. **MDPS 429 batching — 2 fixes shipped, residual deeper issue diagnosed.** UTL per-VM write-debounce (UTL@94d9de30) +
   MTDS finalize batch_size 1→500 (MTDS@d0f42ba), both deployed via fresh tarballs + MDPS relaunch
   (`mdps-backfill-tradfi-20260621-225740`). 429s PERSIST — root cause refined: CONCURRENT per-unit finalize threads
   race-write the shared per-VM shard with `final=True` (non-monotonic counts 54→65→56), which `batch_size`
   (per-instance) can't fix. NOT a correctness blocker (retries succeed, consolidator still merges 15m/24h). Deeper fix
   (serialize per-VM shard write + coalesce final=True) captured as a todo. The UTL debounce DID fix the live producer's
   `final=False` writes (fleet-wide benefit).

All shipped via isolated-worktree promotion (UAC/MTDS had concurrent live peer WIP — preserved, never bundled).

### 2026-06-21 ~22:00 — tradfi `live_databento` source-stamp FIXED + 2 manifest cleanups actioned

**`live_massive` -> `live_databento` (root cause FIXED, UAC@1205ae44).** The relaunched live producer
`mtds-live-tradfi-cme-trades-20260621-213416` CONNECTS + authenticates (`session_id` issued) + streams real databento
ticks - but stamped `pipeline_mode=live_massive`. Root cause (corrected after reading both sides):
`live_source_for_venue` resolved tradfi live via the BATCH `SOURCE_PRIORITY[0]=massive`. First instinct (remove
massive's `Mode.LIVE`) was WRONG - `test_massive_and_databento_are_live_and_replay_capable` documents an explicit
**operator 2026-06-05** decision that massive (Polygon.io 15-min REST) IS live-capable; reverted that. Real fix: the
SOLE tradfi live **WS producer** is `databento_tradfi_ws`, so a `tradfi` branch in `live_source_for_venue` returns
`databento` (mirrors `_PREDICTION_LIVE_SOURCE_FOR_VENUE`); batch path unchanged. Verified
`live_pipeline_mode_for_venue(tradfi,*)=live_databento`

- 48/48 tests green. Shipped via **isolated-worktree promotion** (UAC had a concurrent LIVE peer editing
  `_source_priority_data.py`/cefi-perp venues; preserved their WIP, never bundled it). Codex SSOT + CLAUDE.md corrected
  (my earlier bug-#1/#2 framing was inaccurate: the key resolves fine - verified 32-char secret; massive is not
  "batch-only"). **Deploy pending:** live VM bakes UAC from a GCS tarball -> running producer keeps `live_massive` until
  a `create-code-tarballs.sh` rebuild from clean LDR + relaunch (tracked todo added; daily cron reuses the old tarball).

**2 manifest cleanups (operator "DO THAT too"):** (1) **MDPS 15m/24h** - LAUNCHED `mdps-backfill-tradfi-20260621-213646`
(RUNNING) re-aggregating the 1m corpus -> ohlcv_15m/24h. (2) **equity `ohlcv_1s`** - investigated: NOT a clean phantom.
DBEQ ALLOWS ohlcv-1s (allowlist) + the validity matrix lists it, but `expected_coverage` deliberately excludes it ->
genuine opposite-direction OPERATOR DECISION (fetch-it vs deliberate-exclude); reframed `[DATA-OPERATOR]` rather than
blindly dropping or backfilling. honest-cov now **14.3%** (323,836 captured, up from 5.3% baseline).

### 2026-06-21 — TRADFI lane: launcher bugs diagnosed + fixed; CME-2026 canary verifying

Measured (consolidated v9 `_index`, `market-data-tick-tradfi-prd-…`): **1.94M rows, 99.7% v9** (only 6444 at v4). The
dispatch's "v9 46.6%" is the **instruments-store (IS)** index, NOT the MTDS market-data index — MTDS tradfi is already
v9. Capture: 102936 captured / 1.007M empty / 10013 failed / **818k expected_unattempted** (5.3% honest-cov).
**Fillable-gap reality (3-dataset subscription):** only `ohlcv_1s`/`ohlcv_1m` on GLBX.MDP3(CME) /
DBEQ.BASIC(NASDAQ,NYSE) / XCBF.PITCH(CBOE) are batch-fillable; the unattempted ohlcv_1s/1m is **ALL 2026-YTD** (CME
160767, NYSE 48270, NASDAQ 14184, CBOE 212; pre-2026 already attempted=empty/captured). The remaining ~595k unattempted
is genuine honest absence under the subscription: `trades`/`tbbo` (L1, >1yr free window), `mbp_10` (L2, >1mo),
`ohlcv_15m`/`24h` (DERIVED, aggregated not fetched), and `ICE`/`BARCHART`/`YAHOO`/`FX` venues (off the 3-dataset
allowlist; ICE→IFUS.IMPACT not subscribed). Adapter `_get_dataset_for_exchange` correctly maps NASDAQ/NYSE→DBEQ.BASIC,
CBOE→XCBF.PITCH (launcher header comments mentioning XNAS.ITCH are stale; routing is on-allowlist). **Two launcher bugs
(root-caused via T+10min run.log verify — both rc=0/1 with 0 rows = SILENT FAILURE):**

1. Wrapper bare-`python3` UAC enumeration (ModuleNotFoundError) — **already fixed by peer @e31817b** (uses
   `${WORKSPACE_ROOT}/.venv-workspace/bin/python3`; verified UAC-importable). No action.
2. **`VM_TASK=cefi-backfill` (copy-paste) + no `--source`** → routed AWAY from the chunked MTDS-download branch; handler
   raised `--source databento|massive is REQUIRED` on every payload. FIX (deployment-service): lib
   `_tradfi-ohlcv-launcher-lib.sh` → `VM_TASK=mtds-backfill` + `VM_SOURCE=${OHLCV_SOURCE:-databento}`;
   `setup-data-pipeline-vm.sh` reads `VM_SOURCE` + adds `--source $VM_SOURCE` in the mtds-backfill BASE_CLI. (UAC
   `_VENUE_SOURCE_EXCLUSIONS` excludes only `massive` for CBOE → `databento` is capable for every tradfi OHLCV venue.)
   Plus end-date clipped to **yesterday** (Databento T+1). GCS startup re-uploaded with the fix (reset/collision-proof).
   **CME-2026 canary `tradfi-bf-cme-ohlcv-1m-es-2026-145146` relaunched + watcher armed.** ⚠️ Peer concurrently adding
   the `mtds-live` branch to the SAME `setup-data-pipeline-vm.sh` (live, dispatch item 3) — non-overlapping hunks.

- [x] ✅ [DATA] P0. **tradfi fan-out after canary-green**: NASDAQ + NYSE full DBEQ year-shards (2023-04-15→2026,
      force-window re-attempts wrongly-empty equity history) + CBOE/XCBF (needs a CBOE wrapper — VX-futures universe) +
      CME 2026. Repo: deployment-service. — deployment-service@f243eb4 | CBOE wrapper created
      (`launch-tradfi-bf-cboe-ohlcv-1m.sh`, XCBF.PITCH/VX.FUT, 2026-01-01 floor) + forward-poll fixed
      (VM_TASK=mtds-backfill + VM_SOURCE=databento + VM_NAME + MANIFEST_PER_VM_SHARDS). All 17 VMs RUNNING.
- [x] ✅ [SCRIPT] P1. **deployment-service: launcher fix committed durably** — deployment-service@9aca3a5 (lib
      `VM_TASK=mtds-backfill` + `VM_SOURCE=databento` + yesterday-end; startup `--source $VM_SOURCE` in mtds-backfill
      BASE_CLI). Shipped via isolated-worktree promotion (peer's relentless reset of the shared tree + the dirty-deps
      carve-out blocked normal quickmerge); QG-green 51s; GCS startup re-uploaded with the fix. CME-2026 canary PROVEN
      capturing (`GLBX.MDP3/ohlcv_1m → batch_databento` parquets + per-VM manifest shard).

### 2026-06-21 15:18 — TRADFI batch fan-out LIVE + PROVEN (15 VMs capturing)

Launcher fix committed ds@9aca3a5 (isolated-worktree promotion past peer collision). **15 tradfi-bf VMs all confirmed
capturing** `→ batch_databento` parquets + per-VM manifest shards: CME-2026 (7 roots, GLBX.MDP3), NASDAQ full-history
2023-26 (4, DBEQ.BASIC), NYSE full-history 2023-26 (4, DBEQ). NASDAQ-2024 proven writing REAL equity data (SNPS/INTU/…
613/529/… rows) → the prior equity `empty_confirmed` history WAS wrongly-empty; the force-window DBEQ re-run fills it
(big honest-cov lever). Monitoring the drain (VMs self-delete on completion); will re-measure honest-cov + relaunch any
failure on wave completion. REMAINING tradfi: CBOE/XCBF (VX-futures wrapper — small gap), IS v9 canonicalisation
(instruments-store index 46.6%→100%; the `canonicalize_instruments_store_index.py` N2/F5/N4 dedup + asset_group/source/
pipeline_mode bump — overlaps peer's UAC source_priority work), LIVE forward-poll (peer building `mtds-live` branch).

### 2026-06-21 15:42 — TRADFI lane: ALL 3 dispatch items launched/done

- ✅ [IS] **IS tradfi v9 canonicalisation DONE** (sub-agent, verified on live blob): `instruments-store-tradfi-prd`
  `_index` now **schema_version 100% v9** (was 46.6%), **asset_group 100% `tradfi`** (was absent), **source 0% blank**
  (`instruments_service`), **pipeline_mode 0% blank** (`batch_instruments_service`), capture_status 14045/581 unchanged
  (no fabrication). Mechanism = `instruments-service/scripts/populate_is_index_v9_2026_06_19.py --apply` (the
  column-bump walk; the named `canonicalize_instruments_store_index.py` is dedup-only). Pre-apply snapshot written.
- ✅ [DATA] **LIVE forward-poll wired** — fixed `launch-tradfi-forward-poll.sh` (same cefi-backfill/no-`--source` bug):
  ds-commit (VM_TASK=mtds-backfill + VM_SOURCE=databento + VM_DATA_TYPES=ohlcv_1m). Launched the **daily-cron host VM**
  `tradfi-fwd-daily-cron-20260621-154132` (RUNNING, fires 06:00 UTC daily → `launch-tradfi-forward-poll.sh` T-1) + an
  immediate T-1 forward-poll. Fixed launcher uploaded to the cron's GCS path. This is the tradfi LIVE/recurring
  mechanism (markets are T+1; daily forward-poll = the live keep-current path).
- ✅ [DATA] **CBOE/XCBF launched** (3rd subscribed dataset) — peer had committed a `launch-tradfi-bf-cboe-ohlcv-1m.sh`
  (better 2026-floor scope); I accidentally clobbered it then **restored their version + fixed a real venue bug**
  (`XCBF`→`CBOE`: the adapter maps CBOE→XCBF.PITCH; `XCBF` is unmapped→GLBX default). Launched CBOE-2026 (VX.FUT). Keep-
  both-sides reconcile (ds@f43f50a restore + @3bed824 venue fix).
- Batch fan-out (15 VMs CME/NASDAQ/NYSE) still draining + capturing `batch_databento`. CBOE + forward-poll capture
  verification in flight. The 3-dataset tradfi batch (GLBX+DBEQ+XCBF) is now ALL launched.

### 2026-06-21 16:25 — ohlcv_1s added (CME+CBOE only; equities don't support it)

Operator: grab ohlcv_1s. Shipped ds@47c56d7 — lib + forward-poll default VM_DATA_TYPES now `ohlcv_1m;ohlcv_1s`
(OHLCV_DATA_TYPES env override). **Key correction:** ohlcv_1s is expected ONLY for **CME + CBOE (futures)** per UAC
`expected_coverage` (`CME:[trades,ohlcv_1s,ohlcv_1m,tbbo]`, `CBOE:[ohlcv_15m,ohlcv_1s,ohlcv_1m]`); **NASDAQ/NYSE list
`[ohlcv_1m]` only** — equities (DBEQ.BASIC) have NO 1s, and the MTDS pre-flight correctly drops it
(`dropping data_types not supported per UAC: ['ohlcv_1s']`). So equity-1s is NOT a gap. Deleted the 8 no-op equity-1s
VMs; launched **CME-1s full-history** (7 roots × 2019-2026) + CBOE-1s. The default-both is harmless for equities
(pre-flight drops 1s, fetches 1m). Operational health verified: 0 real rate-limit events fleet-wide, 0 code failures,
liquid tickers captured.

### 2026-06-21 16:40 — CME event contracts (binary/event markets) — IS + MTDS

Operator: capture CME event markets. The 9 CME event-contract roots (ECES/ECBTC/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECNQ,
GLBX.MDP3 .OPT parents, Databento coverage from 2025-09-28, classified EVENT_CONTRACT). On-allowlist (GLBX subscribed);
UAC has `CME:{...,EVENT_CONTRACT}`. Findings:

- **IS index had ZERO event-contract instruments** — `launch-tradfi-event-contract-backfill.sh` (VM_TASK=instruments-
  backfill, `--operation instruments`, no `--source` needed) had **never run**. Launched it
  (`tradfi-event-contract-backfill-20260621-163633`); verifying EC instrument definitions land in
  `instruments-store-tradfi-prd` `_index`.
- **MTDS had 1438 captured EC\* cells** (all 9 roots, 2025-09-28→2026-06-17: trades 1296, ohlcv_1m 124, ohlcv_1s 18) —
  ohlcv sparse because the EC roots weren't in the CME OHLCV backfill. Launched a dedicated **MTDS EC\* OHLCV backfill**
  (9 EC roots, 2025-09-28→yesterday, ohlcv_1m+1s) to complete it.
- ohlcv_1s health re-confirmed: CME-1s capturing (es-2024 `data_type=ohlcv_1s`); **0 rate-limit events across 38 VMs**
  (no self-cap needed). CME-1s full-history wave was timeout-killed partway → relaunched the remaining roots
  (CL/GC/ES_OPT + MNQ tail) in background.

### 2026-06-21 17:49 — TRADFI LIVE producer launched (live_databento; live==batch)

Operator probe: the forward-poll = `batch_databento` (T-1 download), NOT real-time `live_databento` → tradfi LIVE rows
still 0. Launched the genuine live producer: `mtds-live-tradfi-cme-trades-20260621-174904` (e2-standard-8,
LONG*LIVED_LIVE) via
`launch-mtds-live.sh --asset-group tradfi --shard-spec tradfi:CME:trades --instrument-ids "ES;NQ;CL;GC"`. The
`databento_tradfi_ws` connector subscribes `schema=trades`, `SType.PARENT`, aggregates → live candles stamped
`live_databento` (live==batch: same schema/data_types, pipeline_mode=`live*<source>`). Uses the existing
`databento-api-key` (in Secret Manager). US markets OPEN (17:49 UTC). Verifying it connects to Databento **Live**
streaming (the one open question = whether the account's subscription includes Real-Time/Live; if not → genuine
BLOCKED-CREDENTIALS, the only acceptable non-completion). Watcher armed.

- [x] ✅ [SCRIPT] P2. **deployment-service: harden the VM log-uploader thread** — on the CME-1s VMs the GCS run.log
      uploader froze ~16:35 (large 1s logs) while the run + heartbeat + shard-writes continued fine (heartbeat fresh, no
      premature watchdog kill). Cosmetic (can't tail those logs) but worth a try/except + re-arm in the uploader loop.
      Repo: deployment-service (setup-data-pipeline-vm.sh uploader daemon). — unified-trading-library@5ed6824c
      (lifecycle/uploader.py: daemon-thread + 90s join timeout caps blocking upload_bytes();
      test_blocking_upload_does_not_freeze_loop added)

### 2026-06-21 17:55 — TRADFI live_databento: diagnosed (3 bugs + subscription unknown) — FLAGGED not stomped

Launched a real tradfi live producer (`mtds-live-tradfi-cme-trades`) to test live==batch. It FAILED — 3 precisely
root-caused bugs in the (peer's, in-flight) `mtds-live` / `databento_tradfi_ws` live scaffold + 1 vendor unknown.
**Deleted the broken VM** (it wrote 4 wrong `live_massive` empty rows). Bugs (filed for the live-pipeline lane; NOT
fixed here — the UAC file is actively peer-edited + needs a tarball rebuild + the subscription is unconfirmable):

- [x] ✅ [SCRIPT] P1. **mtds: `databento_tradfi_ws._get_api_key()` reads the raw Pydantic field
      `cfg.databento_api_key`** (None unless `DATABENTO_API_KEY` env set) → logs
      `no API key — connection skipped (BLOCKED-CREDENTIALS)`. The BATCH path resolves the key from the
      `databento-api-key` **secret** via the secret client (works). Fix: `_get_api_key` fallback-resolves
      `databento_secret_name` via `get_secret_client()` like batch. Repo: market-tick-data-service. —
      market-tick-data-service@e532105
- [x] ✅ [SCRIPT] P1. **UAC: `live_source_for_venue(tradfi,…)` mis-stamped live rows `live_massive`** — resolved tradfi
      live/replay via the BATCH `SOURCE_PRIORITY[0]=massive`. **CORRECTION** to the original framing: `massive` IS
      live-capable (operator 2026-06-05, Polygon.io 15-min REST — NOT batch-only; do NOT remove its `Mode.LIVE`). Real
      root cause: the SOLE tradfi live **WS producer** is `databento_tradfi_ws` (massive/yahoo/barchart have no live WS
      connector). Fix = a `tradfi` branch in `live_source_for_venue` → `databento` (mirrors
      `_PREDICTION_LIVE_SOURCE_FOR_VENUE`); batch path unchanged (`get_primary_source(tradfi,*)=massive`). —
      unified-api-contracts@1205ae44 | verified `live_pipeline_mode_for_venue(tradfi,*)=live_databento` + 48/48
      `test_source_priority_pipeline_mode.py` green | isolated-worktree promotion (concurrent peer WIP on
      `_source_priority_data.py` preserved, not bundled).
- [x] ✅ [DATA] P1. **launch-mtds-live.sh tradfi instrument-ids format** —
      `CME:FUTURES:ES;CME:FUTURES:NQ;CME:FUTURES:CL;CME:FUTURES:GC` (`_parse_instrument_id` needs
      `venue:type:underlying`). — relaunched `mtds-live-tradfi-cme-trades-20260621-213416` → CONNECTED + authenticated
      (`session_id` issued) + streaming live ticks.
- [x] ✅ [DATA-OPERATOR] P0. **Databento Real-Time/Live subscription CONFIRMED** (operator 2026-06-21: the usage-based
      plan includes Live data + 1yr L1 / 1mo L2-L3 history — the live WS is NOT subscription-blocked). The producer
      connects + authenticates against `wss://live.databento.com`.
- [x] ✅ [DATA] P1. **Deploy the `live_databento` stamp fix (UAC@1205ae44) to the running live producer** — the live VM
      bakes UAC from a GCS **tarball** (working-tree tar), so `mtds-live-tradfi-cme-trades-*` keeps `live_massive` until
      a `create-code-tarballs.sh` rebuild **from a clean LDR checkout** (NOT this peer-WIP dev workspace) + relaunch.
      The daily forward-poll cron relaunches but REUSES the existing tarball — a tarball rebuild is the gating step.
      Repo: deployment-service. Provenance: this Progress Log. NOTE: the dispatch's tradfi LIVE item (forward-poll T-1 +
      daily-cron host) IS done (`batch_databento`); `live_databento` websocket is beyond-dispatch peer-domain work, now
      fully diagnosed for them. — slot-4@vm-planning | tarball rebuilt from UAC@04ca4647 (incl 1205ae44 fix) | old VM
      deleted | new VM `mtds-live-tradfi-cme-trades-20260621-223242` RUNNING | T+5min manifest:
      pipeline_mode=live_databento ✓

### 2026-06-21 19:40 — TRADFI honest-cov re-measured: 5.3% → 13.8% (captured TRIPLED), still climbing

Consolidated `_index`: captured **102,936 → 310,180** (3×), `ohlcv_1s` **3,187 → 48,656** (15×), schema 99.7% v9.
Landed: NYSE ohlcv_1m **125,915** (full DBEQ equity history — was ~0/wrongly-empty), CME ohlcv_1m 68,729 + ohlcv_1s
49,171, NASDAQ 36,295, CBOE 135. **0 failures from this backfill** (the 9,998 `attempted_failed` are STALE 2026-04-30→
05-26 pre-existing runs). 12 CME-1s VMs still finishing (re-armed finalizer). The flat 818k `expected_unattempted` is
**structural honest-absence**, not a gap: trades/tbbo/mbp_10 (L1/L2 window-bound, un-backfillable historically),
ohlcv_15m/24h (MDPS-DERIVED not MTDS-fetched), ICE (off-allowlist). Two real manifest items found:

- [x] ✅ [DATA] P2. **NYSE/NASDAQ `ohlcv_1s` — OPERATOR CHOSE FETCH (option A), DEPLOYED + CAPTURING (2026-06-21).**
      Investigated: DBEQ.BASIC serves equity 1s (allowlist allows) but
      `expected_coverage`+`VENUE_DATA_TYPE_CAPABILITIES` had NASDAQ/NYSE=[ohlcv_1m] only → pre-flight dropped 1s.
      Operator confirmed equity 1s is in-scope. Fix: added `ohlcv_1s` (start 2023-04-15) to BOTH
      `VENUE_DATA_TYPE_CAPABILITIES[NASDAQ/NYSE]` (pre-flight fetches it) AND `expected_coverage[tradfi][NASDAQ/NYSE]`
      (denominator) — unified-api-contracts@87c60b50. Rebuilt UAC tarball from clean LDR + launched NASDAQ+NYSE
      `ohlcv_1s` year-shard backfill (`OHLCV_DATA_TYPES=ohlcv_1s`, 2023→2026, 8 VMs). VERIFIED CAPTURING in prod:
      `tradfi-bf-nasdaq-ohlcv-1m-2025` log `dt=ohlcv_1s … captured=45`, NYSE `captured=158`.
- [ ] [DATA] P2. **ohlcv_15m/24h conversion — 429 FIXED but NOT done; 4-part diagnosis (corrected 2026-06-22, I had
      prematurely flipped this ✅).** The 429 storm IS fixed (UTL per-VM shard lock+coalesce @6b6d53bd + MTDS batch_size
      @d0f42ba: 429 1060→64, monotonic counts) — but that only UNMASKED that MDPS's manifest writes FAIL VALIDATION, so
      0 CME/NASDAQ/NYSE 15m/24h convert. Four parts: (1) ✅ MDPS row_key passed `instrument_id=''` for aggregated
      candles → MalformedRowKeyError — FIXED (omit instrument_id for non-per-instrument shards,
      market-data-processing-service); (2) ✅ MDPS missing `source=` for multi-source tradfi → manifest write rejected —
      FIXED (thread source from the input `pipeline_mode`); both in canonical_writer, tests green. **✅ DEPLOYED +
      LIVE-VERIFIED (slot-6, 2026-07-27, tradfi_satellite_ao_dispatch_batch2):** rebuilt the market-data-processing-
      service tarball from a clean LDR checkout (`market-data-processing-service@3328ffd0`) and relaunched
      `mdps-backfill-tradfi-*` twice (`--force`, 2026-07-13..19 then 2026-07-20..24, ~5,400+ instrument-day attempts
      combined) — ZERO occurrences of `MalformedRowKeyError` or a missing-source rejection in either run, confirming
      parts (1)+(2) are correctly fixed and deployed. **However, BOTH verification runs still show `Candles: 0` for
      every date processed** (confirmed via the post-run manifest-consolidator pass:
      `rows_added: 0, verdict:     "empty", no_op: true`) — two NEW, orthogonal blockers were found live, filed as
      `issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`: (a) NASDAQ/NYSE equity writes are REJECTED
      at the manifest validation gate (`record_empty(reason=SOURCE_RETURNED_ZERO)` called without the required
      `FetchEvidence` — 6,650 rejections across both runs, on regular trading Mondays, not weekends); (b) CME
      combo/chain-bundle candles silently produce ZERO output despite confirmed real raw-tick input being read (no
      WARNING, no ERROR, no candle file — a genuine silent-failure gap, worse than (a)). **CITATION
      (na-eligibility-audit 2026-08-02, tradfi tranche)**: part (b)'s root-cause instrumentation is already an open todo
      in `tradfi_satellite_ao_dispatch_batch5_2026_07_29.md` (`status: active`, `assigned_vm: planning`), citing
      `issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md` as Source — track there going forward.
      **CITATION CORRECTION (na-eligibility-audit 2026-08-06, tradfi tranche)**: the batch5 tracker above is since
      `status: complete` (archived, 0 open todos — its extraction todo landed); the live tracker for the 15m/24h work is
      now the issue doc itself, `issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`
      (`assigned_vm:     planning` + `status: open`, self-dispatched, 2 open todos) — cite there going forward. Parts
      (a), (3), and (4) remain untracked by any active batch (genuine open, judgment-laden diagnosis work). Neither
      blocker is caused by, or fixable within, the row_key/source fix deployed here — both are new root-cause targets
      tracked in the new issue doc. (3) ❌ ~64k of the 1m corpus is OLD migrated data with malformed
      `instrument_id='ticks_migrated_20260418T143552Z'` → StreamingParquet partition_mismatch on the aggregated DATA
      write (the 167k databento 1m are clean + aggregate fine; only the 64k massive-migrated fail) — needs the migrated
      1m re-keyed/re-backfilled. (4) ❌ the 15m/24h `expected_unattempted` is seeded `source=massive`/blank (legacy —
      massive used to serve aggregated bars) but the real path is now databento→MDPS (`source=databento`), so databento
      15m/24h captures land as NEW rows and the massive-keyed unattempted (103,651 cells) never converts — PHANTOM seeds
      needing reconcile to databento (IS enumerator); confirmed live 2026-07-27 that CME has ZERO enumerated
      ohlcv_15m/24h rows (any status) for 2026-07-13 through 07-15, consistent with this gap. Repo:
      market-data-processing-service + unified-api-contracts/instruments-service (seeding). Provenance: this Progress
      Log.

- **na-eligibility-audit 2026-07-30** (tradfi tranche): **KEEP-NA, valid.** All 14 open todos read end-to-end. The doc
  is a genuine mix and cannot flip as a whole: 5 are explicitly operator- or credential-gated (the `altdata`
  asset_group-home `[OPERATOR-DECISION]` plus its 3 dependents, and the `[BLOCKED-CREDENTIALS]` EIA API key); the R1
  `--also-legacy` item is self-marked "checkbox stays OPEN pending operator decision" with a data-loss issue doc already
  filed; and G1.run `--apply-write` is gated on named, still-unmet prerequisites (gate-b Databento IS reference re-feed,
  gate-c the v9 instruments-store walk). Bounded AO-eligible content does exist here (the pre- existing UAC
  `test_schema_version_matrix` QG-RED item; the `--source databento` IS reference-capture re-run), but a whole-doc
  `assigned_vm` flip would dispatch the operator-gated majority alongside it — that content belongs in an
  `/ag-closeout-audit` carve-out, not a reclassification. No content found stale on this pass.
- **na-eligibility-audit 2026-08-02** (tradfi tranche, dispatch agt-6397c9): **KEEP-NA, MIXED — 2 citation touch-ups
  applied, 1 orphan flagged out-of-tranche.** All 14 open todos re-read end-to-end via an independent sub-agent
  classification; count reconciled (14/14). 11 items remain genuinely operator/credential/design-gated (corroborated by
  the fresh 2026-08-01 `/ag-closeout-audit tradfi` batch6 pass, which independently classifies the Phase 0 layout
  audit + ~133K-cell NASDAQ/NYSE backfill + G1.run/gate-b/gate-c chain + catalogue-scheduler wiring as real but
  "too-large-or-risky" for a batch todo). 2 items were KEEP-NA-STALE-duplicated and got citation fixes applied above:
  the Massive→Databento re-feed item (line ~444, now pointing to
  `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s 2026-07-29 todo) and the ohlcv_15m/24h item's part (b)
  (line ~740, now pointing to `tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`'s open, active todo). **1 item (line
  ~433, `test_schema_version_matrix` QG-RED) is a genuine bounded RECLASSIFY-shaped fix but is self-declared out of
  tradfi's own scope** ("outside the tradfi AG... Owner: the schema_version-provider/cefi AG or vm-cross-cutting") — NOT
  reclassified here (this tranche has no authority to flip a cefi/cross-cutting-owned item's dispatch), flagging for the
  next cefi or cross-cutting na-eligibility-audit/ag-closeout-audit pass to pick up; it will not surface under tradfi's
  own scope again since tradfi's own `/ag-closeout-audit` correctly excludes it as cross-AG. `assigned_vm` unchanged.

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: refreshed context_scope (6 entries) -- dropped
  gcs-object-operations.md (generic), added the two live tradfi scripts the open todos actually name
  (`enumerate_expected_universe.py`, `rebuild_tradfi_manifest.py`).
- **na-eligibility-audit 2026-08-06** (tradfi tranche, dispatch agt-e38653): **KEEP-NA, valid — re-verified, unchanged,
  1 citation correction applied.** All 15 open todos re-read end-to-end; count reconciled (15/15). The doc remains a
  genuine mix that cannot flip as a whole: the operator/credential-gated majority is unchanged (the `altdata`
  asset_group-home `[OPERATOR-DECISION]` plus its 3 dependents, the `[BLOCKED-CREDENTIALS]` EIA key, the
  self-flagged-out-of-tradfi-scope UAC `test_schema_version_matrix` QG-RED item), the R1 `--also-legacy` item stays open
  as a tracked data-loss record per the 2026-08-02 ruling, G1.run stays gated on the unmet gate-b (Databento IS
  reference re-feed) / gate-c (v9 instruments-store walk) prerequisites, and the ⑫ FOLLOW phantom dry-run re-run needs a
  dedicated VM (attempted + aborted on the shared host 2026-07-30). Citation correction (line ~768): the ohlcv_15m/24h
  part-(b) tracker citation is stale — `tradfi_satellite_ao_dispatch_batch5_2026_07_29.md` is now `status: complete`
  (archived, 0 open todos); the live tracker is the issue doc itself,
  `issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`, now `assigned_vm: planning` + `status: open`
  (self-dispatched, 2 open todos). `assigned_vm` unchanged.
- **context-scout 2026-08-07**: re-verified context_scope, no change needed (6 entries) -- M-1 coordinator, 3
  tradfi/manifest/cutover codex SSOTs, and the 2 live tradfi scripts remain accurate.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, stale items -- 15 open todos read end-to-end, count reconciled (15/15).
  Fixed 2 broken citations (R1 item, line ~397) pointing at the now-archived
  `issues/tradfi_legacy_bucket_deleted_without_also_legacy_migration_2026_07_26.md` (status: resolved, operator accepted
  the loss 2026-07-26) -- repointed to `/plans/archive/issues/...`; R1 checkbox stays open per the existing 2026-08-02
  ruling (permanent data-loss record, not re-litigated). No fresh RECLASSIFY/ARCHIVE candidates; doc remains a genuine
  operator/credential/design-gated mix.
- **na-eligibility-audit 2026-08-08** (tradfi tranche, dispatch agt-29c933): **KEEP-NA, stale items -- 4 items had stale
  `[OPERATOR-DECISION]`-gated framing, fixed.** 15 open todos read end-to-end, count reconciled (15/15). Found that the
  `altdata`/macro asset-group-home P1 decision (line 486) WAS ruled 2026-08-07 (THIRD option: per-source AG assignment,
  general macro/econ -> tradfi, crypto-native -> defi) -- but its 3 dependents (honest-coverage-gate registration, MTDS
  handler/CLI/manifest wiring, codex doc update) still read "DEFERRED ... gated on OPERATOR-DECISION #1" / "Depends on
  the asset-group decision above," which was stale per CLAUDE.md's "the moment an [OPERATOR] tag resolves, retag in the
  SAME edit" hard rule -- the immediately-prior 2026-08-07 same-day pass had this ruling already in the file and still
  reported "no fresh candidates," missing this. Fixed: retagged the coverage-gate item `[OPERATOR-DECISION]` -> `[DATA]`
  (line 496) and updated all 3 dependents' framing to reflect the ruling landed, now sequenced behind the MTDS wiring
  item (itself confirmed still genuine, non-trivial, multi-integration design/build work across 4 sources -- NOT
  reclassified, too large for a single bounded AO todo as currently scoped). Also updated the "Deferred work -- migrated
  to:" section's stale "blocked on the operator ruling... until that ruling lands" framing. Doc remains a genuine mix,
  stays NA. Other 11 items independently re-verified unchanged (operator/credential/ design-gated majority, R1
  permanent-record, G1.run gate-b/gate-c, cefi/cross-cutting-owned QG-RED item still flagged out of tradfi's scope per
  the 2026-08-02 note).
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate -- the 2026-08-08
  stale-tag retagging + framing fixes were prose edits, no new source/codex reference introduced.
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:ad62eda8ab583aaa]: **KEEP-NA,
  stale items -- 3 citation gaps fixed.** 15 open todos read end-to-end via a dedicated sub-agent hunter; count
  reconciled (15/15), no DECOMMISSIONED/RE-TRIAGE traps found. Fixed: (1) items 4 and 5 (the catalog-seed + G1.run
  todos) share the exact same gate-b "re-feed by_date via Databento IS reference-data adapter" dependency that items 6/9
  already cited as BLOCKED-OPERATOR-DECISION against today's `tradfi_databento_account_billing_suspended_2026_08_09.md`
  -- added the same citation to items 4/5 for consistency (was inconsistently applied, not a new blocker); (2) item 13
  (macro-adapter MTDS wiring) now cross-references the archived `tradfi_adapter_dead_code_fallback_audit_2026_07_25.md`
  Finding M-2 operator ruling ("document, don't register or delete") so a future dispatch doesn't wire the 4 adapters
  into `factory.py` without checking that ruling first. Two softer findings NOT acted on this pass, flagged for a
  follow-up read instead of forcing a change on secondhand evidence: item 1 (Phase-0 layout audit) may be satisfied in
  substance by already-completed work (the 2026-07-06 C0 walk + 2026-07-10 orphan sweep) but no prior pass has confirmed
  this, and item 11 (altdata AG-home decision) may be stale-open now that its ruling landed 2026-08-07 and its 3
  dependents were retagged -- both need a direct read before acting, not inferred from this pass's summary alone. No
  RECLASSIFY candidates (majority remains genuine operator/credential/design-gated mix); item 10's "run the live
  integration test" sub-part is a MISCLASSIFIED_LIKELY_AO_ELIGIBLE candidate (low confidence -- the backfill half is not
  actually runnable, per `eia_adapter.py`'s own "not yet registered" docstring / Finding M-2 above) but not promoted
  this pass. Doc stays NA.
- **round-9 combined RECLASSIFY + satellite-extraction sweep (2026-08-09)**: re-read all 15 open items. No new
  RECLASSIFY or satellite-extraction candidates found (the majority remains genuine operator/credential/design-gated,
  consistent with 8 prior na-eligibility-audit passes). One conflict-check finding applied: the NASDAQ/NYSE equities
  COVERAGE GAP item's remaining fetch-attempt work is now scope-gated to November 2026 for years other than 2026, per
  the same-day `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` ruling — citation added above. The `⑫ FOLLOW`
  phantom-reconcile item (already `[x]`, delegated) was re-checked and confirmed its real open tracker lives in
  `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (a different, out-of-candidate-list doc this round) — not
  re-extracted here to avoid a double-dispatch. Doc stays NA.
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:33bbd8e9af9db9c7]: **KEEP-NA,
  stale-items fixed.** Fresh full read, 15 open items. Closed 1 stale checkbox this pass (the `[OPERATOR-DECISION]`
  "altdata home" item — the decision text itself is fully answered in-place, RULED 2026-08-07 THIRD option, and every
  downstream action it unblocks is already separately tracked in this doc's own dependent todos; was a missed flip, not
  open work). Remaining 14 items independently re-verified: the Databento gate-b citations (items 4/5/6/9) confirmed
  still-current by reading `tradfi_databento_account_billing_suspended_2026_08_09.md` directly, which explicitly names
  this doc's catalogue-scheduler and `--source databento` replacement-path todos as still genuinely gated. Doc stays NA
  (still a genuine, multi-part gated mix).
- **2026-08-10 (live-verification session, same-day follow-up)**: the Databento gate-b citations this doc's own prior
  entry just re-confirmed as "still genuinely gated" are now stale — independently live-verified Databento account
  access is restored (`DatabentoBaseClient.warmup()` → `metadata.list_datasets()` succeeded, no auth/suspended error;
  full evidence in `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`'s Progress Log).
  Lifted the BLOCKED-OPERATOR-DECISION citations on items 4/5 (consistency notes) and 6/9 (the catalogue-scheduler +
  `--source databento` replacement-path todos themselves) — see each item's own `UNBLOCKED 2026-08-10` note. None of
  these are flipped `[x]` — the gate-b re-feed is now dispatchable, not yet actually run. Doc stays NA.
