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
related: [data_completion_to_100_all_ag_2026_06_21.md]
created: 2026-07-15
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
last_updated: 2026-07-15
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: [data_completion_to_100_all_ag_2026_06_21 (M-1) — split 2026-07-15, plan-reconcile §8 operator ruling A]
drift_direction: advance-code
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

- [ ] [DATA] P1. Verify the corpus venue / data_type strings are underscore-canonical: data-state shows venues
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
> `codex/05-infrastructure/gcs-object-operations.md` § "Migration-script performance contract". **(MIGRATED FROM:
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
      `codex/02-data/canonical-cutover-register.md`). **(MIGRATED FROM:
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

- [ ] [DATA] P1. E6 CF-7 relabel: `UNKNOWN`/blank venue + blank data_type → canonical (diagnose, don't bulk-rename).
      **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. E7 Verify: `cf_manifest_audit_2026_06_01.py market-data-tick-tradfi-prd-…` → CF-1…CF-12 GREEN
      data-state (esp. v9 confirmed on real rows — CONFLICT-2); flip CF-coverage in
      `tradfi_master_audit_instructions.md`. ⚠️ IRREVERSIBLE — only after GREEN: hand C-GREEN to L6 → **delete legacy
      `market-data-tick-tradfi` permanently** + **bulk-delete the 12 `day-*` hyphen 0-row-placeholder prefixes** in
      `tradfi-prd` (~110k objects — the issue-doc **Pattern-1 cleanup, now executed here**; pre-delete guard: re-assert
      0-row per object before deleting, abort the prefix on any non-empty object). This SUPERSEDES the
      `gcs_hive_partition_malformed_paths_remediation` Pattern-1 todo. **DONE — apply 2026-07-06 exit_code=0/fatal=0; E5
      rebuild ran 2026-07-07; orphan_class_E=0 corpus-wide 2026-07-10; schema_version=9=100% (5,553,198 rows, 0 blank
      pipeline_mode/source) confirmed 2026-07-16** (`tradfi_v9_stage1_finish_2026_07_06.md`). **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. **COVERAGE GAP → IN PROGRESS (was: surfaced by the 0-row-placeholder finding, 2026-06-02).** tradfi
      **equities/ETF (NYSE/NASDAQ)** were originally never genuinely ingested — only the 0-row Massive dry-run
      placeholders existed; the `day=` hive corpus was CME databento only. **UPDATE 2026-07-21**: the Databento
      equity/ETF backfill is RUNNING (SPOT) — NASDAQ g01-g05 + NYSE g01-g05, `ohlcv_1m`+`ohlcv_1s`, window 2023-2026
      (XNAS/XNYS Databento discovery floor 2023-04-15); launched-and-healthy tranche measured 449M+ records, 0 real
      errors, 0 quarantine (`tradfi_consolidated_closeout_2026_07_18.md`). Equities/ETF are being ingested via Databento
      — Massive is NOT the ingest path (removed/purged); drop the `tradfi_massive_dual_source` cross-link. Track
      remaining coverage against this running backfill's completion + manifest verification, not as a never-ingested
      gap. Until fully backfilled, the manifest must still show not-yet-covered cells as
      MISSING/`attempted_unattempted`, never `empty_confirmed` (CF-11). **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [CODE] P1. ⑦ tradfi could-exist denominator seed — build the `--catalog-path` parquet from the tradfi IS catalog
      (per-instrument lifecycle: `instrument_id`/`instrument_type`/`venue`/`available_from`/`available_to`) and run
      `enumerate_expected_universe.py --asset-group tradfi --catalog-path <catalog> --apply-write` against the canonical
      `_index` so the raw-tick denominator == could-exist universe (active-but-uncaptured instruments seeded
      `expected_unattempted`). Verify on a VM (GCS flaky locally); confirm `_enumerate_v2_tradfi` row-key/data_types
      match the tradfi captured atom; add a regression (IS-universe ⊃ manifest ⇒ denominator doesn't shrink). The
      mechanism + bucket fix are done; this is the per-AG catalog build + run + verify. parent_epic: mtds_mdps_master.
      **SLOT-6 G1 DRY-RUN PROVEN (2026-06-07) — see the `## G1` section below for full evidence; `--apply-write` stays
      GATED (gate-b catalogue liveness + gate-c v9 indices).** **SLOT-6 NOTE (2026-06-04, atom-alignment VERIFIED):**
      read `instruments-service/scripts/enumerate_expected_universe.py::_enumerate_v2_tradfi` — it respects
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
    current.
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

- [ ] [INFRA] P1. **Wire the tradfi `build_instrument_catalogue.py` daily rollup scheduler (GATED on gate-b capture
      restore).** FINDING (slot-6 2026-06-07): the G1 lifecycle producer `build_instrument_catalogue.py` has **NO
      terraform scheduler for ANY asset group** (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04` [INFRA] P1
      "Trigger on every instruments update" is still `[ ]`, owner vm-cross-cutting). The two TFs that DO exist —
      `deployment-service/terraform/gcp/{catalogue_regen_scheduler,instrument_catalogue_scheduler}.tf` — run a DIFFERENT
      artefact (`generate_instrument_catalogue.py`, the availability-matrix), and their instruments-store `for_each`
      **OMITS tradfi** (only cefi/defi/sports/prediction) AND uses legacy no-env bucket names (`-central-element-…` not
      `-prd-`). So even the matrix regen never reads tradfi. **Gated** behind gate-b (a scheduler over a frozen
      `by_date/` self-perpetuates a stale catalogue) — wire once IS reference-capture (Databento-based; the Massive
      capture path is removed/purged) restores `by_date/`. Owner: vm-cross-cutting (shared producer scheduler) + slot-6
      (confirm tradfi inclusion). Repo: deployment-service (terraform). parent_epic: mtds_mdps_master. **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [SCRIPT] P2. **⑫ FOLLOW — re-run `reconcile_phantom_manifest_rows_all.py --asset-group tradfi --dry-run` AFTER the
      tradfi v9 object `--apply`** to confirm 0 false phantoms across all 5 source pipeline_modes
      (batch_databento/massive/barchart/yahoo/eia). The prefix_tpls fix (is@5e8d192d) is verified by inspection +
      `batch_massive` presence; the live re-run is gated on the apply. Repo: instruments-service. parent_epic:
      manifest_master. **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [DATA] P1. **R1 RUNBOOK — the tradfi `migrate_tradfi_to_v9_canonical --apply` MUST include `--also-legacy`** to
      cover the 2,008-day no-env `market-data-tick-tradfi` corpus, then decommission that legacy bucket after the
      canonical copy is G7-verified. Without the flag, 2,008 legacy days orphan. Repo: market-tick-data-service.
      parent_epic: mtds_mdps_master. Provenance: orphan-coverage drill-down, slot-6 2026-06-08. **(MIGRATED FROM:
      `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. **R2 DELETE-AFTER sweep — after the tradfi v9 `--apply` + G7 byte-verify, run the gated delete of the
      old-format source paths** (every **DELETE-AFTER=YES** row in the drill-down: bare `day=*/asset_group=tradfi/`
      without `pipeline_mode=`, the 12 `day-*` hyphen dirs, old processed_candles, the whole legacy bucket, the
      instruments-store E6 bare paths). Capture the migrator dry-run's planned-copy counts per source/branch into a G7
      ledger so the delete set == the verified copy set (no orphan, no premature delete). Repos:
      market-tick-data-service + instruments-service. parent_epic: mtds_mdps_master. Provenance: orphan-coverage
      drill-down, slot-6 2026-06-08.

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

- [ ] ❌ [DATA] P1. ~~NEXT — run Massive tradfi reference capture → regenerate catalogue → unblock gate-b (VM, requires
      live `MASSIVE_API_KEY`). With the adapter shipped (above), run IS instrument capture with `--source massive` to
      refill `instrument_availability/by_date/` to today.~~ **SUPERSEDED 2026-07-21** — Massive removed as a tradfi
      source (operator ruling 2026-07-19, `uac@a2beed46`) and subscription terminated + data purged (operator Option C
      2026-07-21). No `--source massive` capture; a `source='massive'` write now hard-rejects (`MissingSourceError`,
      2026-07-20 ruling). **Replacement path**: run IS instrument capture with `--source     databento`
      (`DatabentoReferenceDataAdapter`, `instruments_service/reference_data/router.py`) to refill
      `instrument_availability/by_date/` → regenerate the catalogue
      (`build_instrument_catalogue --asset-group tradfi --apply`) → THEN re-check whether liveness still marks ~651K
      instruments delisted → unblocks gate-b → then G1.run `--apply-write` (Step 3) becomes runnable. Not yet run under
      this replacement path (do not assume gate-b is unblocked). Repo: instruments-service. parent_epic:
      mtds_mdps_master. **(MIGRATED FROM: `tradfi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

### From `macro_econ_adapter_scaffolds_2026_06_09.md` (archived 2026-07-13 -- Macro/alt-data free adapter scaffolds (fear_greed / CFTC COT / Baker Hughes / EIA))

- [ ] [BLOCKED-CREDENTIALS] P1. EIA live fetch + cassette recording — needs the free EIA API key. CREDENTIAL APPROVAL
      REQUEST filed in `ikenna_orchestrator/pings/slot_3.md` (vendor=EIA, free tier). Unblocks the live integration test
      (`tests/integration/test_macro_adapters_integration.py::test_eia_live`) + EIA backfill RUN. **(MIGRATED FROM:
      `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [OPERATOR-DECISION] P1. `altdata` home — revive `altdata` as a real `asset_group` vs model macro as a SHARED
      cross-asset axis. **DEFERRED** — gates the GCS-shard write + manifest `record_captured` + bucket
      (`resolve_bucket_name`) wiring for all four sources (adapters today return `CanonicalOnChainMetric` lists; they do
      NOT yet write GCS shards because the asset_group/bucket/data_type is undecided). Provenance: audit Open Question
      #1. **(MIGRATED FROM: `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [OPERATOR-DECISION] P2. Honest-coverage-gate registration — add the macro key to `expected_coverage.py` +
      `coverage_start` dates so macro can no longer be silently empty. **DEFERRED** — audit Phase 5. Depends on the
      asset-group decision above. **(MIGRATED FROM: `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [SCRIPT] P2. Wire the macro adapters into an MTDS handler + CLI operation + manifest emission once the asset-group
      home lands (the GCS shard-write path). **DEFERRED** — audit Phase 5/6, gated on OPERATOR-DECISION #1. **(MIGRATED
      FROM: `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DOC] P2. After the asset-group decision lands, document the macro/alt-data capture path in `codex/02-data/` (no
      new contract was introduced by the scaffolds themselves — they reuse `CanonicalOnChainMetric` + the existing
      adapter/`classify_venue_error`/`ADAPTER_FETCH_FAILED` patterns). **DEFERRED** until Phase 5 wiring. **(MIGRATED
      FROM: `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [SCRIPT] P2. **DEFERRED — PM-template gap: `base-library.sh` QG writes `.qg_content_sentinel` but `quickmerge.sh`
      `--agent` fast-path (STAGE 3) verifies `.qg_last_passed_sha`** — so the agent quickmerge fast-path is structurally
      unsatisfiable for **library** repos (UAC), whereas `base-service.sh` writes the sha sentinel. Worked around here
      by writing `.qg_last_passed_sha` after a verified-green UAC QG. Fix: have `base-library.sh` also write
      `.qg_last_passed_sha` on a complete green run (mirror base-service), then roll out via
      `rollout-workflow-templates`/the QG-base propagation. Provenance: UAC quickmerge 2026-06-09 STAGE 3 block. Target
      repo: `unified-trading-pm` (`scripts/quality-gates-base/base-library.sh`). **(MIGRATED FROM:
      `macro_econ_adapter_scaffolds_2026_06_09.md`, 2026-07-13 per MTDS consolidation ruling.)**
