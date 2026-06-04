---
title: "Prediction manifest + data canonicalisation (legacy→canonical, single-walk) — L3 owner for prediction"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-prediction
status: active
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-06-01
source:
  - bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md (L3 ordering — prediction had NO owner)
  - _index comparison 2026-06-01 (prediction canonical is the LEAST complete:
      2,039 legacy-only captured cells, only 783 overlap)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# Prediction manifest + data canonicalisation (L3 owner for prediction)

> **⏸️ E4 DRY-RUN DONE 2026-06-03 (VM auto-deleted) — full-run AWAITING OPERATOR REVIEW.** The dry migration planned
> **1,897,691** object moves (0 copied) cleanly (exit 0) — see the E4 todo for the per-phase breakdown + verified
> transforms. **The next step is the IRREVERSIBLE-DIRECTION FULL run (`… full`/`--apply`, the live 1.9M write) — do NOT
> fire it without operator sign-off on the dry plan.** E8 legacy-delete stays separately gated (post-E7-GREEN + shared
> fleet drain with slot-2).

## Slot-5 Prediction master orchestrator — owned + attached plans/issues

> **Slot↔asset-group split (operator 2026-06-03):** one asset group per slot (five slots). **Slot 5 = Prediction
> end-to-end** across every service — instruments-service → MTDS → MDPS → features → downstream → strategy/execution →
> bucket/data/manifest/UI. **THIS plan is the Prediction master orchestrator**: every prediction-related plan + issue
> cross-references here; orphaned prediction issues attach here. Sibling AG masters: **defi → slot 2**
> (`defi_manifest_canonicalisation_2026_06_01.md`), **cefi → slot 3** (`cefi_manifest_canonicalisation_2026_06_01.md`),
> **sports → slot 4** (`sports_manifest_canonicalisation_2026_06_01.md`), **tradfi → slot 6**
> (`tradfi_manifest_canonicalisation_2026_06_01.md`). Cross-cutting per-service plans keep their own `assigned_vm`
> (vm-ml / vm-cross-cutting) as PRIMARY owner — slot-5 tracks + drives only their **prediction slice**, not the whole
> plan.

**Cross-referenced prediction slices (primary owner keeps the plan; slot-5 drives the prediction portion):**

| Plan / issue                                                   | Primary VM       | Prediction slice                                                                            |
| -------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------- |
| `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` | vm-cross-cutting | L3 prediction ordering + L6 legacy `market-data-tick-prediction` delete                     |
| `data_source_provenance_all_asset_groups_2026_06_01.md`        | vm-ml            | prediction `source=API` column (this plan's C-source RIDER)                                 |
| `pipeline_mode_partition_migration_2026_06_01.md`              | vm-cross-cutting | prediction `pipeline_mode=` partition (this plan's C-pipeline_mode RIDER)                   |
| `instruments_manifest_canonicalisation_2026_06_01.md`          | vm-cross-cutting | `instruments-store-prediction` reference slice                                              |
| `downstream_services_manifest_canonicalisation_2026_06_01.md`  | vm-ml            | prediction MDPS/features/execution canonical-form slice + Kalshi classifier-None divergence |

> **🔎 CROSS-AG FINDING from defi (2026-06-01) — CHECK THE SAME HERE**: defi's CF data-state audit found the legacy
> `_index` **100% NOT v9** (v4/5/6/8 spread), with **no `source`/`asset_group`/`pipeline_mode` COLUMNS** — a FULL
> re-canonicalisation, not the headline cell-count (same shape as the cefi reference incident). **CF-2 gotcha**: the
> migrate tool emitted `asset_group=` to the object PATH but did NOT stamp it as a parquet COLUMN → the rebuilt `_index`
> lacked the column. Fix = stamp `asset_group` (+ `schema_version`/`source`/`pipeline_mode`) as COLUMNS, never rely on
> the consolidator deriving them from the path. **Action**: run a CF data-state audit on prediction's `_index` as
> pre-flight + verify (reusable: `market-tick-data-service/market_tick_data_service/scripts/audit_canonical_form.py` or
> `plans/audit/results/cf_manifest_audit_2026_06_01.py`) — trust the real data-state, never the v9 constant. If the same
> debt shows → fix fully in-walk (scope is a prior, not a ceiling). SSOT:
> `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`.

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, prediction lane). This plan is the prediction
> analogue of `defi_manifest`'s §C single-walk. **Single-walk discipline (HARD RULE)**: one bundled walk on the
> prediction `_index` — bundle every transform (env-split, `asset_group=`, `pipeline_mode=` partition, v9, **`source`
> stamp** = the data-source API, typed empty-reason). Do NOT open a second walk; `pipeline_mode_partition_migration` +
> `data_source_provenance` ride THIS walk.

## Why this exists — prediction is the LEAST-complete canonical (decommission data-loss risk)

The 2026-06-01 `_index` comparison (legacy `market-data-tick-prediction-…` vs canonical `market-data-tick-pred-prd-…`):

| metric                                         | value                                                                                 |
| ---------------------------------------------- | ------------------------------------------------------------------------------------- |
| captured legacy CELLS `(date,venue,data_type)` | 2,822                                                                                 |
| canonical CELLS                                | 3,086                                                                                 |
| overlap                                        | **783**                                                                               |
| legacy-only CELLS (canonical MISSING)          | **2,039**                                                                             |
| legacy-only by data_type                       | `prediction_canonical_question_group` 289 · `ohlcv_15m`/`15s`/`1d`/`1h`/`1m` 247 each |

So **most historical POLYMARKET prediction data is in legacy ONLY** — deleting the legacy bucket now = data loss. This
plan migrates it into the canonical `market-data-tick-pred-prd-central-element-323112` SSOT before L6 decommission.
Legacy layout (per 2026-06-01 audit): `raw_tick_data/` + `processed_candles/` (NO defi-style per-type prefixes).

## Sequencing — canonical migration is a GATE before any prediction backfill (inherits the master HARD RULE)

No prediction backfill / relaunch of `mdps-prediction-2025` until this walk is C-GREEN (per `bucket_name_ssot…` Phase
4 + master L3-gates-L5). L0 tarball-prune blocker (`issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`) must
be fixed first if run on a VM.

## Canonical target form (prediction)

| Dimension       | Legacy                                                      | Canonical                                                                                                                                                                                                                                                                                                                      |
| --------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Bucket          | `market-data-tick-prediction-{project}` (long-form, no env) | `market-data-tick-pred-prd-{project}` (short token `pred` + env)                                                                                                                                                                                                                                                               |
| asset-group key | `category=prediction`                                       | `asset_group=prediction`                                                                                                                                                                                                                                                                                                       |
| pipeline_mode   | absent in path                                              | `pipeline_mode=` hive partition (`batch_polymarket_clob`/`batch_polymarket_gamma_api`)                                                                                                                                                                                                                                         |
| schema_version  | legacy spread                                               | v9                                                                                                                                                                                                                                                                                                                             |
| source          | blank `""` today                                            | `source` COLUMN stamped = the data-source API (`polymarket_clob`/`polymarket_gamma_api`/`kalshi_*`) on every cell — HARD, swap-resilient per `data_source_provenance` Phase 6. **Venue ≠ source**: Polymarket/Kalshi stay VENUES (cross-venue dispersion is feature-layer); each venue's cell still stamps its own API source. |

## Phased execution

### P0 — pre-walk audit + scope

> **Scope is a prior, not a ceiling — fix-fully-autonomously (HARD RULE)**: the headline ("2,039 legacy-only") is a
> coarse prior. Read DATA-STATE. If the audit finds MORE form debt than implied (e.g. cefi turned out 100% v8 / no
> source / no asset_group / blank pipeline_mode — a full re-canonicalisation), fix ALL of it in this one walk — NOT
> descoped, deferred, post-cutover, or `BLOCKED-OPERATOR-DECISION` (a data-state gap is not a design fork). SSOT:
> `canonical_form_cross_service_audit_checklist.md` § "Audit scope is a PRIOR, not a ceiling".

- [x] ✅ [DATA] P0. Legacy→canonical diff (slot-3 tool, 2026-06-01): **2,039 legacy-only cells confirmed** (legacy 2,822
      · canonical 805 · overlap 783) — matches the headline; mostly `POLYMARKET ohlcv_*` +
      `prediction_canonical_question_group` from 2025-03-14 on. Per-data_type object counts resolved in the C0 copy walk
      (idempotent). Data-loss risk on delete → these MUST land in canonical before L6.
- [x] ✅ [DATA] P0. Canonical `pred-prd` `_index` DATA-STATE: **100% v8** (0/16,812 v9 — CF-1 RED); **`asset_group` col
      present** (CF-2 rows GREEN) but **object PATHS still `category=prediction`** + **`data_source=POLYMARKET_CLOB` in
      path** (CF-2 paths RED, CF-4 source-in-path); **`pipeline_mode` blank 0/16,812 + no path segment** (CF-3 RED);
      **no `source` column** (CF-4 RED); **no `available_at` column** (CF-8 RED — only `written_at`); CF-5 typed GREEN
      (`EXPECTED_PRE_VENUE_LAUNCH` 2,280 / `SOURCE_RETURNED_ZERO` 41). **CF-7 drift**: venue includes `UNKNOWN` + blank
      `''`; data_type includes blank `''` + `prediction_trades`/`trades` — diagnose/relabel in the walk. Path sample:
      `raw_tick_data/by_date/day=2025-03-14/category=prediction/data_source=POLYMARKET_CLOB/venue=POLYMARKET`.

### C — single-walk migration (legacy `prediction` → canonical `pred-prd`)

> **🔎 BUILD-GAP FINDING (slot-3, 2026-06-01) — the existing tools do NOT achieve the v9 single-SSOT target; this is the
> bespoke build spec.** `migrate_polymarket_canonical.py` rewrites the **legacy** `market-data-tick-prediction` bucket
> **IN-PLACE** (`category=`→`asset_group=`, `DEFAULT_BUCKET_PREFIX="market-data-tick-prediction"`) — which is why legacy
> raw is near-canonical (`day=/asset_group=/venue=/instrument_type=/data_type=`) but the SEPARATE canonical
> `market-data-tick-pred-prd` bucket holds **older, less-complete** data (`category=/data_source=` paths, 805 captured
> cells vs legacy's 2,822, v8). `rebuild_prediction_manifest.py` rebuilds the manifest via `ManifestWriter` (→v9) but
> ALSO targets the legacy long-form bucket and its `CANONICAL_PATH_RE` expects `category=…/market_category=…`. **Neither
> consolidates legacy's richer data ONTO `pred-prd` in v9-canonical form.** Required build (single bundled walk):
>
> 1. **Reconcile source-of-truth**: legacy (2,822 cells, asset_group= hive) is the FRESHER/more-complete copy; pred-prd
>    (805 cells, category=) is stale. Migrate legacy → `pred-prd` at canonical
>    `day=/pipeline_mode=batch_polymarket_clob/ asset_group=prediction/venue=/chain=/instrument_type=/data_type=`
>    (gcs_copy_object server-side; the 2,039 legacy-only cells are the data-loss gap). Drop the stale pred-prd
>    `category=` objects after the copy.
> 2. **Manifest rebuild on `pred-prd`**: generalise `rebuild_prediction_manifest.py` to target `pred-prd` + scan the
>    canonical `asset_group=` paths + stamp `source=polymarket_clob` (from the `data_source` path/col) + `pipeline_mode`
>    - `available_at` → `ManifestWriter` auto-stamps v9.
> 3. **CF-7 relabel**: `UNKNOWN`/blank venue + blank/`prediction_trades` data_type → canonical.
> 4. Verify with `cf_manifest_audit_2026_06_01.py` (CF-1…CF-12 GREEN on pred-prd data-state) → delete legacy bucket.
>    VM-run (object scan + consolidator); prediction-writer (`mdps-prediction-2025`) confirmed drained before `--apply`.

- [x] ✅ [DATA] P0. **Phase 0 — layout audit DONE (slot-5 2026-06-03, read-only GCS metadata scoping — no data
      download).** Enumerated both buckets. **Layouts found**: `_index/` (+ `per_vm/`,
      `snapshots/pre_migration_2026-05-22`), `_vm_staging/` (prediction_backfill/features/pipeline),
      `raw_tick_data/by_date/day=…` + `processed_candles/by_date/day=…`. The CANONICAL `pred-prd` raw objects STILL
      carry the OLD 6-dim
      `day=/category=prediction/data_source=POLYMARKET_CLOB/     venue=/chain=/market_category=/underlying=/market_type=/resolution_period=/data_type=/{cid}.parquet`
      shape (NOT yet `pipeline_mode=/asset_group=` — **EXPECTED**: the migration that rewrites the shape is E4
      `--apply`, operator-gated + not yet run; the dry run is clean). LEGACY raw uses
      `asset_group=prediction/venue=/instrument_type=/data_type=`. Candles (both buckets):
      `processed_candles/by_date/day=/timeframe=/data_type=/venue=/{id}.parquet` (no `pipeline_mode=` yet — what item
      228's fix + the migrator now add). **Sharding/perf scope**: ~44–200 raw parquets/day (healthy, activity-driven),
      parquet sizes 16–38 KB avg ~27 KB (**no tiny-file explosion, no hot-spot shard**), canonical 352 days
      (2025-03-14→2026-04-29) vs legacy 422 days (→2026-05-22; legacy ~2 mo ahead). Migrator's ~1,897,691 planned moves
      reconcile as raw+candles (×timeframes) + stale `category=` subtree + staging across both buckets. **Full-run
      wall-clock estimate**: 1.9M ÷ (32–64 workers × server-side `gcs_copy_object` ~100 ms) ≈ **1.6–4 h** (schedule a 4
      h window; re-snapshot `_index` pre-cutover — the snapshot is 2026-05-22, stale). No layout anomaly beyond the
      expected pre-migration old-shape. SSOT: `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § grounded
      recipe Phase 0.

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: the walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. SSOT:
> `codex/05-infrastructure/gcs-object-operations.md` § "Migration-script performance contract".

- [ ] [DATA] P0. C0 ONE bundled walk: copy legacy `raw_tick_data/` + `processed_candles/` objects → canonical `pred-prd`
      at the canonical path (env-tier + `asset_group=` + `pipeline_mode=` partition); rewrite manifest rows to v9; typed
      empty-reasons. **`category=`→`asset_group=` lands on BOTH the object PATHS and the manifest `_index` ROWS in this
      walk** (CODE side — writers emit `asset_group=` — already shipped via archived
      `venue_axis_asset_group_vocabulary_2026_04_25`; this is historical data+manifest only). Server-side
      `gcs_copy_object` (layout-aware: prediction = `raw_tick_data/`/`processed_candles/`). RUN ON A VM via
      `VM_TASK=canonical-migration` (gated on L0 tarball-prune fix) OR locally if object count is small (P0 audit
      decides).
- [ ] [DATA] P0. C-pipeline_mode RIDER: the `pipeline_mode=` partition for prediction lands in THIS walk (satisfies
      `pipeline_mode_partition_migration_2026_06_01.md` for prediction — do NOT run it separately).
- [ ] [DATA] P1. C-source RIDER: stamp `source` = the data-source API (`polymarket_clob` / `polymarket_gamma_api` /
      `kalshi_*`) on every prediction cell in THIS walk (path/pipeline*mode → `source` column), re-consolidate into the
      `_index` — HARD, swap-resilient (a future Polymarket data-provider change stays distinguishable). Closes
      `data_source_provenance` Phase 6 prediction. **Venue ≠ source invariant preserved**: Polymarket/Kalshi remain
      VENUES (cross-venue dispersion is a feature-layer concern, not a source merge); when Kalshi lands it is a venue
      addition AND its cells stamp
      `kalshi*\*`as source. Do NOT open a separate prediction source walk.     **[CODE-WIRED — slot-5 confirmed 2026-06-03; operator picked source-column over N/A]** The CODE foundation is     already in place: UAC`SOURCE*PRIORITY`carries`("prediction","trades")=["polymarket_clob"]`,     `("prediction","book_snapshot")`, `("prediction","prediction_canonical_question_group")`, and     `("prediction","MARKET_LIFECYCLE")=["polymarket_gamma_api"]`(+`EMISSION_LATENCY_MS_BY_SOURCE`entries), and the     UTL`manifest_writer.add()/record_captured\*`AUTO-STAMP the sole external source via`default_source`for     single-source cells (no`MissingSourceError`—`source_required`is False). So **live/new writes already stamp    `source`**; this rider is now just the HISTORICAL `\_index`backfill — ensure the rebuild's`record*\*`calls flow     the parquet's own`data_source`(or let`default_source`auto-stamp`polymarket_clob`), no writer code change     needed. The stale "prediction N/A" line was corrected in CLAUDE.md + `data_source_provenance`
      row (slot-5 2026-06-03).

### Verify + handoff to decommission

- [ ] [DATA] P0. Post-walk: re-run the `(date,venue,data_type)` comparison → **legacy-only CELLS = 0**; canonical
      `_index` all v9; `pipeline_mode` non-null; **`source` populated on every cell (HARD — zero blank; the API source
      per venue) — closes `data_source_provenance` Phase 6 prediction**. This is the C-GREEN signal `bucket_name_ssot…`
      Phase 6/7 waits on for the prediction legacy bucket decommission.

## Execution checklist (grounded — next session, finish in full)

> Supersedes the old "rewrite every parquet's columns" framing: the CF debt is in the `_index` MANIFEST (rebuilt via the
> UTL `ManifestWriter`, which auto-stamps v9) + object PATHS — NOT the raw tick parquets. See
> `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § MECHANISM + the BUILD-GAP block above.
>
> ⚠️ **IRREVERSIBLE — E8 DELETES legacy `market-data-tick-prediction` + stale pred-prd `category=` paths permanently.**
> Do not run E2–E8 until the canonical target (v9, `day=/pipeline_mode=/asset_group=prediction/…`, source=API) is
> CONFIRMED CORRECT at the verify step. One pass, no confusion — once legacy is deleted it is gone.

- [x] ✅ [DATA] P0. E1 Phase-0 layout audit on legacy `market-data-tick-prediction` + canonical `pred-prd` (ran
      `cf_layout_audit_2026_06_01.py` 2026-06-01): legacy raw = **near-canonical**
      `raw_tick_data/by_date/day=/     asset_group=prediction/venue=/instrument_type=/data_type=` (fresher
      source-of-truth) + `processed_candles/by_date/     day=/timeframe=/data_type=/venue=`; pred-prd raw tree is
      sparse/stale (no leaf shallowly — the stale `category=` copy). **Legacy = source-of-truth confirmed.** — slot-3
      2026-06-01.
- [x] ✅ [DATA] P0. E2 Built `migrate_prediction_to_pred_prd_v9.py` (perf-contract: ThreadPoolExecutor + wired
      `--workers`/`--start-date`/`--end-date` + `gcs_copy_object` server-side + `python -u` progress + per-object
      try/except + idempotent `gcs_describe_object` skip): copies legacy `raw_tick_data/` + `processed_candles/` →
      `pred-prd` at canonical `day=/pipeline_mode=/asset_group=prediction/…` via the **UAC `candidate_parquet_paths`
      SSOT** (byte-exact batch=live; pipeline_mode LEFT of asset_group= per writer+reader+UAC). **DUAL-SOURCE
      RECONCILIATION (operator catch 2026-06-01)**: real data-state = legacy 2,822 captured cells / pred-prd **805**
      (NOT the stale 3,086 prior in the header table) / overlap 783 → **2,039 legacy-only AND 22 CANON-only** (neither
      bucket is a subset). Migrator canonicalises BOTH sources: Source A legacy (fresher, wins overlap, first) + Source
      B pred-prd's own `category=` objects (preserves the 22 unique cells, dedup-to-freshest). `--drop-stale` (E8)
      deletes `category=` originals ONLY after Source B canonicalises them → final pred-prd = UNION, fully canonical,
      single SSOT, ZERO loss (IRREVERSIBLE). Path transforms unit-validated. — market-tick-data-service@74077c39, slot-3
      2026-06-01.
- [ ] [DATA] P0. E3 Confirm `mdps-prediction-2025` writer drained; snapshot `pred-prd/_index` →
      `_index/snapshots/pre_v9_canonical_2026_06_01.parquet`.
- [ ] [DATA] P0. E4 Dry-VM run + full-VM run. **Launcher WIRED 2026-06-01** (deployment-service@f8866b6): `prediction`
      now invokes `migrate_prediction_to_pred_prd_v9` (dry-by-default + `--apply`). **DRY-RUN DONE + CLEAN (slot-5
      2026-06-03, VM `canonical-migration-prediction-20260603-190322`, sha-pinned mtds@90aeb7dd, exit_code=0,
      auto-deleted).** Planned moves (`copied=0`, dry): `raw_tick_data/by_date` **751,723** +
      `processed_candles/by_date` **582,730** + stale pred-prd `category=` **563,238** = **TOTAL 1,897,691** objects.
      Transforms verified correct vs canonical target: `category=prediction`→`asset_group=prediction`,
      `pipeline_mode=batch_polymarket_clob` inserted (LEFT of `asset_group=`), env-tier `prediction`→`pred-prd`, the
      6-dim `data_source=/market_category=/underlying=/     market_type=/resolution_period=` segments dropped→parquet
      columns. NO errors/exceptions/skips. NB: had to rebuild the code tarball first — the prior GCS tarball (db6d947d)
      predated `eb5eaad2` (`gcs_copy_object` deep-import fix) and would have ImportError'd. **REMAINING
      (operator-gated): the FULL run (`… full`/`--apply`) is the live 1.9M object write** — fire only after operator
      reviews this dry plan (no fire-and-forget: STARTED<60s + progress/hr + STOPPED; T+10min
      `gcloud instances describe`). Dry run took ~3 min (1.9M plan @ workers=64) so the full copy (server-side
      `gcs_copy_object`) is well within budget — no worker re-tune needed.
- [x] ✅ [CODE] P0. **BATCH≠LIVE for processed_candles `pipeline_mode=` — FIXED (option a) — mdps@5e7f075 | QG ✅ ALL
      QUALITY GATES PASSED (1550s) | basedpyright 0 err | 8 regression tests
      `tests/unit/test_pipeline_mode_in_candle_paths.py`.** `get_processed_path` (config.py) + both live candle writers
      (`CandleWriteMixin._write_candles`, `GCSDataSink.write_candles`) + the prior-day-seed READ now thread
      `pipeline_mode.value` into the object path, inserting `pipeline_mode={pm}/` after `day={D}/` — matching the
      migrator `_canon_candle_rel` + the raw-writer `orchestrator.py:994` (path==manifest invariant). Cross-AG (all
      asset_groups' candles). On LDR; staging promotion dep-tier-blocked behind UTL/MTDS/UAC (FEATURE_GREEN) — drains
      when they promote. ORIGINAL GAP: The migrator inserts a `pipeline_mode=` segment into candle paths
      (`migrate_prediction_to_pred_prd_v9.py:176-188` `_insert_pipeline_mode_for_candle`, "no UAC candle builder"; dry
      run wrote `processed_candles/by_date/day=/pipeline_mode=batch_polymarket_clob/     timeframe=/data_type=/…` —
      582,730 candle objects), but the LIVE MDPS candle writer
      (`market-data-processing-service config.py:46 get_processed_path`) returns
      `processed_candles/by_date/day={d}/timeframe={tf}/data_type={dt}` with **NO `pipeline_mode=` segment**. So
      post-migration the migrated candles sit at a `pipeline_mode=` path that a relaunched `mdps-prediction-2025` would
      NOT write to → two candle forms in the bucket + a batch≠live drift (the raw_tick writer is fine —
      `orchestrator.py:994` DOES insert `pipeline_mode=` for raw, the path==manifest invariant; only the CANDLE path
      lacks it). **Reconcile BEFORE the full run touches candles:** either (a) wire `pipeline_mode=` into
      `get_processed_path` (+ the candle manifest), making MDPS candles batch=live with the migrator (preferred —
      matches the raw-writer precedent + the `pipeline_mode_partition_migration` intent), OR (b) if the canonical candle
      form should NOT carry `pipeline_mode=`, drop the migrator's `_insert_pipeline_mode_for_candle` so it copies
      candles path-only. Also confirm the candle READER (features-service / MDPS scan) dual-probes both forms during the
      window. Repos: market-data-processing-service (+ migrate_prediction_to_pred_prd_v9 if option b). parent_epic:
      mtds_mdps_master.

  > **✅ GRANULARITY RESOLVED (slot-3 2026-06-02 — the atom is the live-writer atom, batch=live SSOT).** A sub-agent
  > draft was REVERTED for collapsing the row key to `(date,venue,instrument_type,data_type)` (dropped `{cid}` +
  > `underlying` → massive undercount → G6 FAIL). The CORRECT canonical shard atom = the LIVE prediction writer's atom
  > (orchestrator.py ~1370-1420 + CLAUDE.md per-AG shard-key matrix):
  > **`(asset_group, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)`** — ONE
  > bundled manifest row per `canonical_question_group` per day, emitted via **`record_captured_from_counts`** (NOT
  > per-cid `add()`), with `observed_clusters = {market_id(conditionId): row_count}`, `expected_root_clusters` (UAC
  > group-expected clusters or = observed when unknown), `available_at_envelope = max(available_at)`, `pipeline_mode`
  > (path-or-derive),
  > `row_key = {asset_group, venue, data_type, canonical_question_group, processing_date, pipeline_mode}`. The raw
  > canonical OBJECTS stay per-cid (`…/data_type={DT}/{cid}.parquet`);
  > `canonical_question_group`/`market_id`/`available_at` are PARQUET COLUMNS → the rebuild MUST READ them per object
  > (set by the Polymarket/Kalshi adapter via UAC `classify_polymarket_to_canonical_group`). **VM cross-check**
  > (confirmation, not a blocker): on the migration VM where the `_index` parquet reads cleanly (local gcsfs/cp flaky
  > 2026-06-02), confirm the rebuilt row count ≈ the live canon `_index` (~16,812 rows) granularity. **BUILD = mirror
  > the live writer's `record_captured_from_counts` call exactly** (find it in the prediction finalize loop
  > ~orchestrator.py:1450+). The post-migration REGEX (optional `pipeline_mode=` +
  > `asset_group=prediction/venue=/instrument_type=/data_type=/{cid}.parquet`) from the reverted draft IS correct +
  > reusable; the row-key/cluster-bundling + column-read is the build.
  >
  > **VERBATIM BUILD SPEC — mirror this exact live-writer call (orchestrator.py:~3068, prediction emit loop):**
  >
  > ```python
  > writer.record_captured_from_counts(
  >     row_key={"date": str(processing_date), "venue": pred_venue,
  >              "data_type": "prediction_canonical_question_group",
  >              "instrument_type": "prediction", "instrument_id": cqg_str},   # cqg = canonical_question_group
  >     total_rows=total_rows,                       # sum of market_counts.values()
  >     expected_root_clusters=expected_clusters,    # _load_expected_clusters_for_cqg(cqg, date, fallback=dict.fromkeys(market_counts,1))
  >     observed_clusters=market_counts,             # {market_id(conditionId): row_count}
  >     available_at_envelope=envelope,              # max(available_at) per cqg (rebuild: read from parquet, NO live-latency add)
  >     pipeline_mode=PipelineMode.BATCH_POLYMARKET_CLOB,  # or derive_pipeline_mode_for_row(venue,"prediction",dt)
  > )
  > ```
  >
  > **Rebuild from objects**: scan canonical per-cid objects → for each, read parquet COLUMNS
  > `canonical_question_group`, `market_id`(/`condition_id`), `available_at` + num_rows (pyarrow column projection +
  > metadata) → group by `(date, venue, canonical_question_group)` building `observed_clusters={market_id: rows}` +
  > `envelope=max(available_at)` → one `record_captured_from_counts` per group. Missing-envelope (no parseable
  > available_at) → `record_failed` (mirror the live writer's NaT guard). expected_root_clusters: reuse
  > `_load_expected_clusters_for_cqg` if importable, else `dict.fromkeys(market_counts, 1)`. This is per-AG-canonical +
  > batch=live identical → G6 completeness checkable against the live `_index`.
  >
  > **⚠️ CORRECTION (slot-3 2026-06-02 — disk-verified a real pred-prd object; a 2nd build draft was REVERTED for
  > this).** The raw canonical prediction parquet does **NOT carry `canonical_question_group`, `market_id`, or
  > `available_at` columns** — those are WRITE-TIME-COMPUTED MANIFEST values, NOT persisted in the tick parquet (and the
  > path-only migrator does not add columns). A real object's columns are:
  > `side, asset, conditionId, size, price, timestamp, title, slug, eventSlug, outcome, outcomeIndex, transactionHash, condition_id, data_type, instrument_type, underlying, market_category, market_type, resolution_period, data_source, venue, chain, ts_event, symbol`.
  > So a rebuild that reads a `canonical_question_group` column gets `""` for EVERY row (→ catastrophic collapse to one
  > `(venue,"")` bundle) and a `available_at` column that's absent (→ EVERY cell routed to `record_failed`). **The E5
  > rebuild MUST RE-COMPUTE the atom** (mirrors the live writer's in-memory computation → batch=live):
  >
  > - read columns `[title, slug, eventSlug, outcome, conditionId|condition_id, ts_event, timestamp]` + num_rows;
  > - `cqg = classify_polymarket_to_canonical_group(title=, slug=, event_slug=eventSlug, outcome=outcome, condition_id=conditionId)`
  >   (UAC `unified_api_contracts.canonical.domain.predictions.classifiers`, sig verified 2026-06-02). **`None` → route
  >   that cid to `record_failed`/`attempted_failed[reason=ClassifierConfidenceLow]`** (per the classifier contract),
  >   NOT into a bundle;
  > - `market_id = conditionId` (the `condition_id`/`conditionId` column); `available_at_envelope = max(ts_event)`
  >   (derive from ts_event/timestamp — the rebuild's batch envelope, no live-latency add);
  > - then group by `(date, venue, cqg)` → `observed_clusters={conditionId: rows}` → the verbatim
  >   `record_captured_from_counts` call above. This is the genuinely-correct build; it needs the UAC Polymarket
  >   classifier (re-classification per object, heavier but correct). Kalshi: the equivalent
  >   `classify_kalshi_to_canonical_group`.

- [x] ✅ [DATA] P0. E5 Manifest rebuild → v9 — **CAPTURED-ATOM REBUILD DONE (mtds@d1f1317d, 2026-06-02).**
      `rebuild_prediction_manifest.py` REWRITTEN to the CORRECTION spec: scans the post-migration canonical layout at
      DAY-level prefix (optional `pipeline_mode=` segment parsed), and for each per-cid object RE-COMPUTES the
      `canonical_question_group` via UAC
      `classify_polymarket_to_canonical_group(title,slug,event_slug=eventSlug,     outcome,condition_id=conditionId)`
      (the raw parquet has NO cqg/market_id/available_at columns — verified), groups by `(date,venue,cqg)` with
      `observed_clusters={conditionId:rows}` + `available_at_envelope=max(ts_event)`, and emits one
      `record_captured_from_counts` per bundle — the EXACT live-writer atom (orchestrator.py:3071), batch=live.
      None-classifier → `record_failed[ClassifierConfidenceLow]`; 0-row + missing-envelope → `record_failed` (CF-11
      universal 0-row guard). Perf-contract: `ThreadPoolExecutor`(--workers) + `--start-date`/`--end-date` date-shard +
      per-object isolation + `python -u`. 14 unit tests (parse/atom/bundle/emit). **STILL OPEN (the CF-11 sub-todos
      below):** re-emit of the EXISTING `_index`'s `empty_confirmed`/`attempted_failed` rows that have NO backing object
      (a pure object-scan loses them) + within-bounds-empty classification + the IS/MTDS write-path audit — at parity
      with cefi E5's deferred CF-11 enhancements. Build-spec reference retained below.
- [ ] [DATA] P2. E5 build-spec reference (superseded by the DONE item above): **REFERENCE: cefi E5 DONE
      (mtds@2c3a479b) + tradfi E5 DONE (mtds@e6250b99)** — copy their pattern (optional `pipeline_mode=` regex segment,
      DAY-level list prefix, canonical `-prd` bucket, stamp `pipeline_mode` via path-or-
      `derive_pipeline_mode_for_row`). Prediction differs: its CANONICAL*PATH_RE must be **REWRITTEN** to the
      post-migrator form (verified 2026-06-02 via `candidate_parquet_paths`):
      `raw_tick_data/by_date/day={D}/pipeline_mode={mode}/asset_group=prediction/venue={V}/instrument_type={IT}/data_type={DT}/{cid}.parquet`
      — the CURRENT regex matches the PRE-migration `category=/data_source=/market_category=/…` form (which the migrator
      DROPS) so it would scan ZERO post-apply shards. **BUILD SPEC (refined slot-3 2026-06-01)**: generalise
      `rebuild_prediction_manifest.py` to target `pred-prd` scanning the NEW canonical
      `day=/pipeline_mode=/asset_group=prediction/venue=/instrument_type=/data_type=/{cid}.parquet` layout.
      **Granularity reconciliation (the one open correctness point)**: the canonical path no longer carries
      `underlying=`/`chain=`/ `data_source=` segments (they are PARQUET COLUMNS now, per
      `build_prediction_partition_path`), but the proven manifest
      `ShardKey=(date,venue,chain,instrument_type,data_type,underlying)` needs them → the rebuild MUST READ each
      parquet's `chain`/`underlying`/`data_source` columns (the existing tool read them from the path). Stamp `source =
      pipeline_mode.removeprefix("batch*")`(use UAC`source_string_for`/`pipeline_mode_for_source`) +     `pipeline_mode`(path-derivable: question_group→gamma_api else clob) +`available_at`→`ManifestWriter`    auto-stamps v9. Confirm row-key granularity against the EXISTING pred-prd`\_index`
      (16,812 rows) so the rebuild dedups, not double-counts. Then consolidator merge.
- [ ] [DATA] P1. E6 CF-7 relabel. **CF-7 NOW BAKED INTO THE MIGRATOR (mtds@4b311c93)** — `_cf7_normalise` runs in BOTH
      path transforms BEFORE dedup: `venue UNKNOWN/blank → POLYMARKET` (prediction is single-venue today; Kalshi lands
      born-canonical), `data_type prediction_trades → trades` (verified the same markets). Grounded by the
      operator-requested overlap verification (2026-06-01): clean `(POLYMARKET,trades)` overlap is **byte-identical**
      between legacy + canon (401 common dates; sampled days had identical condition*id sets + identical per-object row
      counts) → legacy-wins + relabel loses nothing; canon's apparent 22 'canon-only' cells are venue=UNKNOWN/blank
      DRIFT (not unique data — canon has NO ohlcv*\*/question_group that legacy has). **Residual (object-level,
      small):** blank `data_type` (17 rows, both buckets) is skip+logged by the migrator → diagnose at rebuild from the
      parquet's own `data_type` column; confirm the ~21 UNKNOWN-venue cells are object-backed (relabel) vs phantom
      (honest drop).
- [x] ✅ [DATA] P0. E6b CODEX-ALIGNMENT VERIFY — DONE (slot-5 2026-06-03). **Resolved: NO migrator change needed + codex
      reconciled.** Confirmed against (1) UAC `build_prediction_partition_path` — `{conditionId}.parquet` is the
      per-instrument FILENAME, explicitly "NOT a partition segment"; (2) legacy data — **0**
      `data_type=prediction_canonical_question_group` raw objects across sampled days (only `data_type=trades` per-cid).
      `prediction_canonical_question_group` is a MANIFEST-ONLY bundled data_type (rebuild re-computes cqg per-cid → one
      `record_captured_from_counts` row), so there is no `canonical_question_group={cqg}/` object segment to build — the
      migrator's cqg-as-filename output is correct and the canonical reader resolves it. The codex
      `prediction-schema-paths.md` "Target (post-Plan A)" object-bundle layout was STALE/aspirational → added a
      SHIPPED-DESIGN CORRECTION banner (per-cid objects + manifest-only bundle). Original verify text below.
      <br>**Original:** a codex-alignment audit confirmed paths/columns/buckets/vocab are ALIGNED across codex +
      IS/MTDS/MDPS (all use UAC builders + `resolve_bucket_name`; no inline divergence) — see
      `cf_data_state_audit_slot3_2026_06_01.md`. **ONE prediction nuance to confirm before apply**:
      `codex/02-data/prediction-schema-paths.md` describes a `canonical_question_group={cqg}/` PATH SEGMENT for
      `data_type=prediction_canonical_question_group` (post-Plan-A target). The migrator's `candidate_parquet_paths`
      builds `.../data_type={DT}/{filename}.parquet` (cqg-as-filename, NO segment). For the 289 legacy question_group
      cells: list an ACTUAL legacy question_group object, confirm whether the canonical layout uses the SEGMENT vs the
      filename, and confirm the canonical READER resolves whichever my migrator produces. If the segment is required,
      extend the migrator's prediction path build for that data_type. (raw_tick/trades/ohlcv = unaffected.)
- [ ] [DATA] P0. E7 Verify: `cf_manifest_audit_2026_06_01.py market-data-tick-pred-prd-…` → CF-1…CF-12 GREEN on
      data-state (v9, source populated, pipeline_mode, asset_group, available_at, 0 legacy-only). Flip the CF-coverage
      rows in `predictions_master_audit_instructions.md`. **[PRE-RUN BASELINE — slot-5 ran the audit 2026-06-03 on the
      current (un-migrated) `_index`: 16,812 rows / 31 cols / 14,491 captured / 2,321 empty_confirmed].** GREEN now:
      CF-2-rows (`asset_group` col present, no `category` col), CF-5 (typed empty — `EXPECTED_PRE_VENUE_LAUNCH` 2,280 /
      `SOURCE_RETURNED_ZERO` 41, 0 blank), CF-9 (env `-prd-` bucket). RED now — **all "RED because not-yet-migrated",
      NOT code regressions** (each is produced by the rebuild/migrate step that is operator-gated + hasn't run): CF-1
      (100% v8 — rebuild stamps v9), CF-3 (`pipeline_mode` blank — rebuild stamps), CF-4 (`source` col absent — C-source
      rider stamps; live writes already auto-stamp per item 170), CF-7 (blank/`UNKNOWN` venue +
      blank/`prediction_trades` data_type — `_cf7_normalise` in the migrator fixes), CF-8 (`available_at` absent, only
      `written_at` — rebuild writes it). **2,039 legacy-only cells** (canonical 805 captured vs legacy 2,822,
      overlap 783) = the data-loss risk that keeps **E8 legacy-delete HARD-gated until the migration runs**. So E7 is
      GREEN-able only AFTER the gated E4 full-run + rebuild; the code side is ready (verified no defect introduced by
      E2/E5).
- [ ] [DATA] P0. E8 Hand C-GREEN to `bucket_name_ssot…` L6 → delete legacy `market-data-tick-prediction` + stale
      pred-prd `category=` paths (single source of truth).

## Deferred work after 2026-06-01 slot-3 session

| Item                                | State                                 | Next action                                                                                                                                                      |
| ----------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E1 layout audit                     | ✅ done                               | —                                                                                                                                                                |
| E2 path-migrator built              | ✅ done (mtds@456ae08a)               | —                                                                                                                                                                |
| E4 launcher wired                   | ✅ done (deployment-service@f8866b6)  | VM dry-run + full run still PENDING (VM-only)                                                                                                                    |
| E3 writer-drain + `_index` snapshot | ⏳ pending                            | confirm `mdps-prediction-2025` stopped (most self-terminated) + snapshot pred-prd `_index` before `--apply`                                                      |
| E5 manifest rebuild → v9            | ✅ captured-atom DONE (mtds@d1f1317d) | object-scan re-computes cqg atom + record_captured_from_counts (batch=live). OPEN: existing-`_index` empty/failed re-emit (CF-11) + within-bounds classification |
| E6 CF-7 relabel                     | ⏳ pending                            | runs at rebuild time                                                                                                                                             |
| E7 CF verify                        | ⏳ pending                            | `cf_manifest_audit` CF-1…CF-12 GREEN on pred-prd real data-state                                                                                                 |
| E8 IRREVERSIBLE delete              | ⏳ pending — GATED                    | only after E7 GREEN + fleet drain (shared w/ slot-2) → `--drop-stale` + L6                                                                                       |

**Pipeline proven on prediction (smallest/most-scaffolded first, per mission).** The path-migrator is
correct-by-construction (UAC `candidate_parquet_paths` SSOT, unit-validated). Remaining = run on VM + manifest rebuild +
verify + the gated delete.

### CF-11 completeness — fetch-failure must be `attempted_failed`, NOT `empty_confirmed` (operator directive 2026-06-02)

> Operator: "when there is an API issue somewhere in IS or MTDS, is it correctly doing `attempted_failed` where the
> attempt makes sense by instrument / UAC bounds — RATHER THAN `empty_confirmed` which would not be complete?"
> Prediction twist: legitimate typed empties exist for `EXPECTED_PRE_VENUE_LAUNCH` (2,280 — market not yet listed) which
> stay `empty_confirmed`. The risk is a Polymarket CLOB/Gamma API error for an EXISTING market (condition_id live,
> within the market's active window) being mislabeled `SOURCE_RETURNED_ZERO` (41 such today — verify each) instead of
> `attempted_failed`. Expected-attempt set = Polymarket market/condition universe × market-active window × UAC
> SOURCE_PRIORITY data_type registration.
>
> **The manifest must EXPLAIN every zero (3-way decision tree — the E5 rebuild contract):** (1) attempt errored on a
> live-market in-window cell → `attempted_failed`; (2) a UAC guard explains the zero → typed `empty_confirmed`
> (`EXPECTED_PRE_VENUE_LAUNCH` "not started yet" / post-resolution / out-of-coverage); (3) only if the market was live +
> fetch succeeded + genuinely no trades/prices → `SOURCE_RETURNED_ZERO`. A blanket/blank `SOURCE_RETURNED_ZERO` = "we
> don't know why" masquerading as complete.

- [x] ✅ [DATA] P0. **E5 rebuild classifier: within-bounds empty → `attempted_failed` — DONE (mtds@62b7ff74, slot-5
      2026-06-03).** The 41 `SOURCE_RETURNED_ZERO` (per-condition_id) are now reclassified: lifecycle bounds loaded per
      date from the FIXED reader (`start_date`/`end_date_iso`), and a row live in-window
      (`start_date<=day<end_date_iso`) → `record_failed(WithinBoundsSourceZero)` (attempted_failed); out-of-window /
      no-bounds preserved as typed empty. `EXPECTED_PRE_VENUE_LAUNCH` preserved. Tests: within-vs-out-of-bounds +
      no-bounds; QG exit 0. Superseded-PARTIAL note: (mtds@59d25967, slot-5 2026-06-03): the rebuild now AUDITS the
      `SOURCE_RETURNED_ZERO` rows (per-row WARN log `(date,venue,instrument_id)` via `reemit_honest_absence_rows` + a
      `source_returned_zero_preserved` counter) and PRESERVES the legit `EXPECTED_PRE_VENUE_LAUNCH` typed empties.
      **RESIDUAL NOW CLOSED (slot-5 2026-06-03, verified — supersedes the stale "deferred" note):** the within-bounds
      RECLASSIFICATION IS wired + tested (it was completed in the same @62b7ff74 work — see the "robust `_index` read +
      within-bounds reclassification DONE" item below). Verified by reading the shipped code, not re-implementing:
      `reemit_honest_absence_rows` (rebuild_prediction_manifest.py:648-706) loads per-date lifecycle bounds via
      `_load_market_lifecycle_for_date` (cached), and for each `SOURCE_RETURNED_ZERO` row whose `condition_id` is live
      in-window (`created_at <= day < settlement`) emits `record_failed(error="WithinBoundsSourceZero")`
      (attempted_failed), else preserves the typed empty + logs. The lookup it depends on returns real bounds:
      `_load_market_lifecycle_for_date` (base_prediction_adapter.py:89-121) falls back from the empty
      `market_lifecycle/by_canonical_group/` to `instrument_availability/…/instruments.parquet` keyed by `condition_id`
      (`start_date`→created, `end_date_iso`→settlement). Tests:
      `test_reemit_source_returned_zero_within_bounds_reclassified` (FIX 3a) +
      `test_load_market_lifecycle_fallback_parses_start_end_columns` (FIX 1) + the 15-test
      `test_market_lifecycle_loader` suite. **Real-data verification** (does the bounds lookup actually fire for the 41
      rows) is the post-migration rebuild VM run — the E4 DRY run (2026-06-03) confirmed the migrator + tarball + code
      chain runs correctly on a VM. No code change needed.
- [x] ✅ [DATA] P0. **E5 rebuild: re-emit existing `attempted_failed` rows v9, status PRESERVED — DONE (mtds@59d25967,
      slot-5 2026-06-03).** `reemit_honest_absence_rows` reads the existing pred-prd `_index`
      (`read_availability_index`), and for every `attempted_failed`/`empty_confirmed` row whose
      `(date,venue,data_type,instrument_type,instrument_id)` key is NOT covered by the fresh object-scan, re-emits it
      with status PRESERVED (`record_failed` error preserved / `record_empty` reason validated vs
      `EMPTY_CONFIRMED_REASONS`) — fixing the pure-object-scan false-complete (honest-absence rows were being lost).
      Fresh captured/failed always wins the dedup; never silently relabels a failure to `empty_confirmed`. 3 new tests
      (re-emit / dedup-skip / status-preserved), 17/17 green; mtds QG `--no-fix` exit 0.
- [x] ✅ [CODE] P1. **Batch=live classifier-None divergence — DONE (mtds@5744ba61, 2026-06-02).** The live Polymarket
      adapter now emits `None` (NaN), NOT `"OTHER"`, for a sub-threshold classifier result (polymarket_adapter.py ~735);
      the orchestrator `write_chunk` splits null cqg rows BEFORE the captured groupby (`_prediction_unclassified` keyed
      by market_id) and the finalize loop emits one `record_failed(error="ClassifierConfidenceLow")` per market —
      byte-identical to `rebuild_prediction_manifest.emit_manifest_rows`. The REAL `CanonicalQuestionGroup.OTHER` group
      (value `"OTHER"`) stays a CAPTURED bundle, distinct from the `None` sentinel (they were indistinguishable before).
      3 regression tests in `test_polymarket_bundling_finalize.py` + updated `test_polymarket_adapter_lifecycle_gating`
      (now asserts sub-threshold → `None`, NOT `"OTHER"`). mtds QG green.
- [x] ✅ [CODE] P1. **Kalshi classifier-None divergence — DONE (mtds@584871e9, slot-6 2026-06-03).** The Kalshi adapter
      (`kalshi_adapter.py`) now stamps `None` (NaN) for a sub-threshold `classify_kalshi_to_canonical_group` result
      instead of collapsing to `CanonicalQuestionGroup.OTHER`; the venue-agnostic orchestrator finalize (the shared
      `_prediction_unclassified` split shipped with the Polymarket fix mtds@5744ba61) routes it to
      `record_failed[ClassifierConfidenceLow]` — byte-identical to the batch `rebuild_prediction_manifest`. Real
      `CanonicalQuestionGroup.OTHER` stays a captured bundle. Removed the now-unused enum import;
      `test_kalshi_adapter_lifecycle_gating.py::test_unclassified_canonical_group_is_none_not_other` flipped to assert
      `isna().all()` + `"OTHER" not in …` (9/9 green); mtds `quality-gates.sh --no-fix` exit 0, sentinel==HEAD. On LDR
      via the tab→LDR mirror; staging-promotion gated on the workspace dep-tier drain (UTL+UAC LDR-ahead-of-staging).
      Original finding below for reference. ~~the Kalshi adapter still maps an unclassified result →
      `canonical_question_group="OTHER"`~~ (`test_kalshi_adapter_lifecycle_gating.py:246` asserts it). The orchestrator
      finalize (shared across all prediction venues) treats a non-null `"OTHER"` as a REAL captured group, so Kalshi
      unclassified markets are bundled CAPTURED while Polymarket now routes them to `attempted_failed` — a
      venue-inconsistency + batch≠live for Kalshi. Fix the Kalshi adapter the same way (emit `None` for sub-threshold so
      the shared orchestrator routes it to `attempted_failed[ClassifierConfidenceLow]`); update the Kalshi
      lifecycle-gating test to assert `None` not `"OTHER"`. Target: `market-tick-data-service` Kalshi prediction
      adapter + `test_kalshi_adapter_lifecycle_gating.py`. Low live urgency today (prediction live corpus is Polymarket
      CLOB), but required for venue parity before Kalshi goes live.
- [x] ✅ [CODE] P0. **Write-path CF-11 audit + fix (IS + MTDS prediction Polymarket adapters) — DONE (IS fix
      instruments-service@65e1f8f0, slot-6 2026-06-03).** MTDS side already VERIFIED COMPLIANT (diagnosis retained
      below). IS-side residual verify COMPLETE + found-and-fixed a concrete gap: the Polymarket CLOB universe scan
      (`polymarket.py::_fetch_all_raw_clob_markets`) caught a mid-pagination `aiohttp.ClientError` with only
      `logger.warning` + `break` → returned the PARTIAL `all_markets` accumulated so far, which is cached 24 h
      (`_get_raw_clob_markets_cached`) and read by every per-date filter as a COMPLETE (but smaller) universe →
      false-complete coverage with ZERO failure signal (A8/CF-11 class). Fix: classify + emit `ADAPTER_FETCH_FAILED`
      (mirrors `_fetch_clob_history`/`_fetch_page`) then RAISE so the per-venue handler records the cell
      `attempted_failed` rather than caching a truncated universe (single-venue pagination loop → respects
      shard-isolation). Regression test `test_clob_scan_midscan_failure_raises_not_truncates` (5/5 green); IS
      `quality-gates.sh --no-fix` exit 0, sentinel==HEAD. On LDR via tab→LDR mirror; staging-promotion gated on the
      workspace dep-tier drain (UTL+UAC). **Original audit + MTDS diagnosis:** on a genuine API error
      (timeout/5xx/429/auth) for a live market/condition within its active window, the handler MUST `record_failed` (→
      `attempted_failed`) via `classify_venue_error()`/`ADAPTER_FETCH_FAILED`, NOT `record_empty`. Grep the prediction
      Polymarket CLOB/Gamma fetch paths for `except … record_empty` / bare `return []` swallows; gate empty-vs-failed on
      market-exists + active-window + UAC coverage. Cross-ref the sports CF-11 model
      (`sports_manifest_canonicalisation_2026_06_01.md` § CF-11). **DIAGNOSIS (slot-3 2026-06-02): MTDS side VERIFIED
      COMPLIANT** — same finding as the cefi CF-11 todo (shared MTDS orchestrator finalize): the polymarket adapter
      classifies+emits+re-raises on a genuine API error (no swallow), and `orchestrator.py:3818`/`:3766` gate
      `record_failed` vs `record_empty(SOURCE_RETURNED_ZERO)` on a recorded fetch-failure. (Distinct from the now-fixed
      None-classifier divergence above, which was about UNCLASSIFIABLE markets, not fetch errors.) RESIDUAL = focused
      instruments-service write-path verify. See cefi plan § CF-11 for the full diagnosis.

## Deployment-API/UI prediction v9 data-status alignment (CODE — E2E readiness; slot-5 audit 2026-06-03)

> **Why (operator 2026-06-03):** "code e2e ready" = the deployment-api data-status summary + the deployment-ui drilldown
> must render the prediction v9 canonical form (the manifest-only `prediction_canonical_question_group` bundle atom +
> `pipeline_mode`/`source`/`schema_version`/`available_at`) BEFORE the migration runs, so post-migration backfills,
> code, and the data-status display all agree. Findings from a read-only deployment-api/ui audit (slot-5 2026-06-03).
> The manifest atom is the MANIFEST-ONLY bundle (per E5/E6b): one row per
> `(asset_group, venue, data_type=prediction_canonical_question_group, canonical_question_group, day, pipeline_mode)`
> with `observed_clusters={conditionId: rows}`; raw objects stay per-cid `data_type=trades/{conditionId}.parquet`.

- [x] ✅ [CODE] P0. **deployment-api `_prediction_venue_detail` reads the bundled atom — DONE (deployment-api@2ac1dfa,
      slot-5 2026-06-03).** Now reads `data_type=prediction_canonical_question_group` rows, takes cqg from
      `instrument_id` (v9; falls back to `underlying` for the migration window), expands `observed_clusters` for the
      per-market drilldown, surfaces `source`+`pipeline_mode` per leaf. ruff+basedpyright clean; QG `--no-fix` exit 0.
      ~~reads the bundled atom, not `underlying`~~\*\* — repo `deployment-api`,
      `deployment_api/services/shard_detail.py:1364-1372` groups by the `underlying` column and emits it AS
      `canonical_question_group`. Post-v9 the manifest carries an explicit `canonical_question_group` column on the
      bundled `data_type=prediction_canonical_question_group` rows + per-market `observed_clusters` JSON. Fix: read
      `canonical_question_group` from the bundled row + expand `observed_clusters` (`{conditionId: rows}`) for the
      per-market drilldown leaf; stop assuming `underlying==cqg`. parent_epic: mtds_mdps_master.
- [x] ✅ [CODE] P0. **deployment-api turbo aggregation handles the bundled data_type — DONE (deployment-api@2ac1dfa).**
      `data_status_service._read_defi_merged_index` + `data_status_hierarchical.get_hierarchical_drilldown` promote
      `canonical_question_group` from `instrument_id` for prediction so the turbo breakdown + SHARD_AXIS_MATRIX axis +
      filters resolve against v9 rows. ~~aggregation handles the prediction bundled data_type~~\*\* — repo
      `deployment-api`, `deployment_api/services/data_status_service.py:2022` (+ `data_status_hierarchical.py:369`):
      aggregation assumes flat per-venue rows; add the `prediction_canonical_question_group` bundled-row path so the
      summary counts per-`(venue, canonical_question_group, day)` (not per-flat-venue) and rolls up `observed_clusters`.
      parent_epic: mtds_mdps_master.
- [x] ✅ [CODE] P1. **deployment-api surfaces `source`+`pipeline_mode` for prediction — DONE (deployment-api@2ac1dfa).**
      `_prediction_venue_detail` emits `source`/`pipeline_mode` per leaf; `routes/data_status.py` filters already wired
      through `_apply_row_filters`/`_apply_pipeline_mode_filter` (now resolve correctly post-promotion). ~~surfaces
      `source` (+ `pipeline_mode`) for prediction~~\** — repo `deployment-api`, `deployment_api/routes/data_status.py`
      prediction handlers accept `pipeline_mode` but never surface the v9 row-level `source`
      (polymarket*clob/gamma_api/kalshi\*\*) as a column/filter. Add `source` to the prediction data-status response +
      filter, mirroring the cross-AG source-provenance display. parent_epic: mtds_mdps_master.
- [x] ✅ [CODE] P1. **deployment-ui renders the cqg bundle — DONE (deployment-ui@4a358ec, slot-5 2026-06-03) | pw:L2 ✓ |
      regression: tests/smoke/prediction_v9_breakdown.spec.ts**. `[UI]` data-status-helpers
      prediction→`canonical_question_group` breakdown + `DataStatusTab` source badge + `observed_clusters`
      per-conditionId drilldown + v9 mock. tsc clean; vitest 273 pass (17 new); playwright 97 pass. ~~renders the cqg
      bundle, not flat venues~~\*\* — repo `deployment-ui`, `src/lib/data-status-helpers.ts:24` hardwires prediction to
      a `venues` breakdown; post-v9 the shard axis is `(venue, canonical_question_group, day)` with per-market clusters.
      Add a prediction breakdown branch (`breakdown_axis` → canonical_question_group → market_id cluster drilldown).
      `[UI]` — needs `pw:L2 ✓` + regression spec per the playwright gate. parent_epic: mtds_mdps_master.

- [x] ✅ [CODE] P0. **Shared prediction lifecycle reader FIXED (mtds@62b7ff74, slot-5 2026-06-03) — derive bounds from
      `start_date`/`end_date_iso` (batch=live; repairs live gating too)** (slot-5 discovery 2026-06-03).
      `base_prediction_adapter._load_market_lifecycle_for_date` reads `market_lifecycle/by_canonical_group/` which has
      **0 objects** (IS never populated MARKET_LIFECYCLE), and `polymarket_adapter._load_lifecycles_from_gcs`'s
      `instrument_availability/` fallback checks for `available_from_datetime`/`available_to_datetime` columns that **DO
      NOT EXIST** — the real `instruments.parquet` has `start_date`/`end_date_iso`/`active`/`closed` (verified
      day=2025-03-14, 157 rows). Net: the reader returns `{}` for every date, so the **LIVE** MTDS writer's lifecycle
      gating (no-ticks-before-created / after-settlement) is a SILENT NO-OP, and batch within-bounds reclassification
      has no source. Fix the shared reader to derive `(market_created_at=start_date, settlement_time=end_date_iso)`
      keyed by `condition_id` from `instrument_availability` (graceful: prefer MARKET_LIFECYCLE when it lands). Repo:
      market-tick-data-service. parent_epic: mtds_mdps_master.
- [x] ✅ [CODE] P0. **E5 rebuild: robust `_index` read DONE (mtds@62b7ff74) — direct parquet fallback + within-bounds
      reclassification** (slot-5 2026-06-03). `reemit_honest_absence_rows` uses `read_availability_index(bucket)` which
      returns **0 rows on this host** (gcsfs/aiodns DNS flakiness — the audit reads `_index/availability_index.parquet`
      directly via download+`pd.read_parquet` for exactly this reason) → the re-emit can SILENTLY no-op. Fix: read the
      `_index/availability_index.parquet` object directly (fallback when `read_availability_index` yields 0). THEN wire
      the within-bounds reclassification: the 41 `SOURCE_RETURNED_ZERO` rows are per-`condition_id` (`data_type=trades`,
      `instrument_id=0x…`), so for each, load lifecycle bounds (fixed reader above) for its date and if
      `start_date ≤ day < end_date_iso` (live + in-window) → `record_failed` (attempted_failed); else preserve typed
      empty. Repo: market-tick-data-service. parent_epic: mtds_mdps_master.
- [x] ✅ [CODE] P1. **instruments-service MARKET_LIFECYCLE for prediction — ROOT-CAUSED + FIXED (slot-5 IS@4105bba3) +
      writer VERIFIED (slot-6 IS@e3360f05); two complementary findings reconciled 2026-06-03.** BOTH were true. **(1)
      slot-5 found + fixed the upstream BUCKET-RESOLUTION CRASH**: `_get_instruments_bucket("prediction")` called
      `resolve_bucket_name(kind="instruments-store", asset_group="prediction")`, but `cloud-providers.yaml`'s
      per-asset_group `instruments-store:` dict has only CEFI/DEFI/TRADFI/SPORTS (prediction is the FLAT kind
      `instruments-store-prediction`) → it raised `BucketNamingError` at `orchestrator.py:2263` BEFORE the per-venue
      write loop, so the ENTIRE prediction write (`instruments.parquet` AND `market_lifecycle.parquet`) aborted → 0
      objects. Fix = new `resolve_instruments_store_kind()` routes prediction → flat kind (used by engine
      `_get_instruments_bucket` + CLI `_get_instruments_bucket_for_asset_group`), resolving to
      `instruments-store-pred-prd-…` identical to the MTDS reader; 106 tests (the old
      `test_bucket_name_prediction_uses_category_prefix` ENCODED the bug — corrected). **(2) slot-6 independently
      VERIFIED the writer LOGIC is correct**: `orchestrator._write_market_lifecycle` (from
      `save_instrument_data_to_gcs`) emits
      `market_lifecycle/by_canonical_group/group={g}/day={d}/market_lifecycle.parquet` with
      `market_id`/`market_created_at`/`settlement_time` (round-trip with the MTDS reader); +8 contract tests.
      **RECONCILED**: slot-6's "writer correct → residual is a backfill" was right about the writer but tested it in
      ISOLATION (mocked bucket) so it MISSED the upstream crash — in the real pipeline the writer was never reached.
      Net: the bucket fix makes the writes RUN, the (verified) writer emits the correct path/columns, and the PRIMARY
      `market_lifecycle/` objects populate on the next IS prediction run (operator-gated backfill —
      `--asset-group     prediction` for the range; the MTDS `instrument_availability` bridge mtds@62b7ff74 covers the
      interim). Column-contract verified both ways (no drift). NOTE: local QG `uv.lock` pre-gate is a foreign host-uv
      false-positive (committed lock correct `pyjwt>=2.13.0`; server `quality-gates-v2` passes). ORIGINAL (superseded —
      never reached classify_lifecycle): the writer is wired — `orchestrator.py:2418 _write_market_lifecycle(...)` is
      called per-canonical-group inside the prediction branch; `_build_market_lifecycle_df` (orchestrator.py:3324)
      builds from `venue_df` which is `InstrumentRecord.model_dump()` (orchestrator.py:2238) → it HAS
      `instrument_key`/`available_from_datetime`/`available_to_datetime` (NOT `start_date`/`end_date_iso` — those are
      raw Polymarket fields used to BUILD the record, and the slot-5 `start_date`/`end_date_iso` parquet was the
      DIFFERENT `instrument_availability/` write, not this one). So `_build_market_lifecycle_df` is structurally
      correct; it drops every row whose `available_from_datetime` OR `available_to_datetime` is null (line 3344), and
      BOTH are null when `polymarket.py classify_lifecycle()` returns `None` (line 882-883). **So 0 objects = either (a)
      `classify_lifecycle` returns None for most/all markets** (then the fix is in `classify_lifecycle` / its
      created_at/closed_time/end_date_iso parse — line 1116/1120 — make it resolve bounds robustly, mirroring the
      @62b7ff74 MTDS-reader fix that derives from start_date/end_date_iso), **or (b) no recent IS prediction enumerate
      run has executed** (operational — the write only fires on a fresh run). **VM-VERIFY REQUIRED (can't verify locally
      — GCS reads flaky from the Mac slot host):** on a VM, run the IS prediction enumerate for a sample date + (1) log
      how many markets get a non-None `classify_lifecycle`, (2) check whether `market_lifecycle/by_canonical_group/`
      objects appear. If (a), fix `classify_lifecycle`; if (b), it self- resolves on the next run. Repo:
      instruments-service. parent_epic: mtds_mdps_master.
- [ ] [CODE] P2. **instruments-service QG STEP 5.64 — preflight short-circuits emit NO `PREFLIGHT_SKIPPED`**
      (cross-cutting finding surfaced by slot-5 during the 552 fix 2026-06-03; NOT prediction-scoped — for the
      instruments epic). `instruments-service` has preflight-guard patterns (`_check_dependencies` / `should_skip_date`
      / `check_shard_freshness`) in `engine/orchestrator.py`, `engine/validation_utils.py`, `cli/instruments_handler.py`
      but emits no `emit_preflight_skip` / `PREFLIGHT_SKIPPED` anywhere → silent preflight skips are invisible in the
      event stream (the same observability gap STEP 5.64 enforces for service repos). Wire `emit_preflight_skip` (UTL)
      at each short-circuit. Repo: instruments-service. parent_epic: mtds_mdps_master (or the instruments epic).

## Slot-4 ready-to-run audit 2026-06-04 (operator-requested: migrator dry-run · manifest-rebuild dry-run · preflight IS→execution empty/partial batch=live · read/write path post-migration parity)

> Cross-service code audit (5 services × 4 dimensions, read-only). VERDICT: the prediction vertical is **~90%
> code-ready** — most of the operator's 4 readiness items are CONFIRMED-WIRED by slot-5's prior work; 3 gaps remain (1
> latent SSOT-drift, 1 real preflight gap, 1 known observability todo). The actual full migration WALK stays
> operator-gated (C0/E4-full).

**CONFIRMED (verified against shipped code, not annotations):**

- [x] ✅ **(1) Migrator dry-run** — `migrate_prediction_to_pred_prd_v9.py` is dry-by-default + `--apply`; idempotent
      (`gcs_describe_object` skip); server-side `gcs_copy_object`; no import-time risk; launcher dry-by-default
      (`deployment-service/scripts/vm/launch-canonical-migration-vm.sh:94-98`). E4 dry-VM run already DONE clean (slot-5
      2026-06-03, 1.9M-object plan, exit 0). **READY.**
- [x] ✅ **(2) Manifest-rebuild dry-run MODE** — `rebuild_prediction_manifest.py` has `--dry-run` (`_DryWriter` no-op,
      lines ~847-899); previews per-`capture_status` counts (captured*bundles / failed_envelope / failed_unclassified /
      failed_zero_row / reemit*\*) WITHOUT mutating `_index`. The rebuild meaningfully runs POST-migration (scans the
      migrated canonical objects), so its dry-run is the post-walk step — mode is READY now.
- [x] ✅ **(3a) Empty/partial CF-11 3-way decision tree (batch=live)** — within-bounds zero → `attempted_failed`
      (lifecycle bounds); typed empties (`EXPECTED_PRE_VENUE_LAUNCH`) preserved; classifier-None → CLOB NaN (not
      "OTHER", batch=live `polymarket_adapter.py`); zero-row → `record_failed`; untyped empty reason → demoted to
      `record_failed` (never blank). prediction is trade-based (no zero-vol OHLCV). CONFIRMED-WIRED.
- [x] ✅ **(4) Read/write path post-migration parity (downstream readers)** — MDPS / features-service / strategy /
      execution all resolve prediction via `resolve_bucket_name` + canonical `asset_group=prediction` paths (features
      keeps a legacy `category=` dual-probe fallback for the migration window — correct). No downstream reader stuck on
      a legacy-only path. CONFIRMED.

**GAPS — both readiness-blocking P1s now CLOSED 2026-06-04 (slot-4); residual = 2 latent P2s (observability + a UAC
venue-override question) + the operator-gated migration walk:**

- [x] ✅ [CODE] P1. **MTDS keystone: migrator+rebuild pipeline_mode unified through the UAC SSOT — DONE 2026-06-04
      (slot-4, operator cqg=clob decision)** — market-tick-data-service@ea2c2d50. The migrator's local
      `_GAMMA_DATA_TYPES={prediction_canonical_question_group}` (cqg→`batch_polymarket_gamma_api`) drifted from the
      authoritative UAC SSOT — `source_priority.py:271`
      `("prediction","prediction_canonical_question_group") =     ["polymarket_clob"]` — while the live writer
      (`derive_pipeline_mode_for_row`) + the rebuild (hardcoded CLOB) already used CLOB → migrated object PATH could
      disagree with the manifest ROW (path==manifest risk; sports-keystone class). **Fix:** routed BOTH
      `_pipeline_mode_for_data_type` (migrator) AND `bundle_pm` (rebuild) through the SAME UTL
      `derive_pipeline_mode_for_row("POLYMARKET","prediction",data_type)` SSOT the live writer uses → all three derive
      IDENTICALLY, local map deleted. cqg/trades/candles → `batch_polymarket_clob`. 3 regression tests lock
      migrator==SSOT parity; 22 existing rebuild tests unchanged; QG green (225s). **SSOT nuance found + recorded:**
      `derive_pipeline_mode_for_row` resolves ALL Polymarket data_types to CLOB because a **venue override**
      (`POLYMARKET → BATCH_POLYMARKET_CLOB` in `pipeline_mode_resolver.py:_VENUE_OVERRIDES`) short-circuits BEFORE the
      per-data_type SOURCE_PRIORITY lookup — so `MARKET_LIFECYCLE` resolves CLOB too (despite `source_priority.py:278`
      data = gamma). That keeps all four consumers consistent at CLOB (good for path==manifest) but is a separate latent
      UAC question → see the new handoff todo below. parent_epic: mtds_mdps_master.
- [ ] [CODE] P2. **HANDOFF→UAC/prediction: POLYMARKET venue override masks the per-data_type gamma source** — repo:
      `unified-api-contracts` (+ `unified-trading-library`). `derive_pipeline_mode_for_row`'s
      `_VENUE_OVERRIDES["POLYMARKET"]     = BATCH_POLYMARKET_CLOB` fires before the SOURCE_PRIORITY lookup, so
      `("prediction","MARKET_LIFECYCLE") =     ["polymarket_gamma_api"]` (`source_priority.py:278`) is NEVER realised —
      every Polymarket row (incl. gamma-sourced MARKET_LIFECYCLE) resolves CLOB. Latent (all consumers use the resolver
      → all consistent at CLOB; no live MARKET_LIFECYCLE pipeline_mode-sensitive divergence today). Decide: is the broad
      venue override correct (all Polymarket = clob — then `batch_polymarket_gamma_api` is effectively dead +
      SOURCE_PRIORITY:278 is misleading), or should the override yield to the per-data_type source so MARKET_LIFECYCLE =
      gamma? Surfaced 2026-06-04 while unifying the migrator. **DEFERRED** to the prediction/UAC track. parent_epic:
      mtds_mdps_master.
- [x] ✅ [CODE] P1. **MDPS prediction consolidator preflight — DONE 2026-06-04 (slot-4, parity with sports)** —
      market-data-processing-service@eb8d00a. `dependency_checker.validate_can_run` gated
      `assert_consolidator_healthy()` (market-data + instruments-store) on `asset_group==SPORTS` ONLY → prediction MDPS
      read the pred-prd `_index` with no consolidator health gate (stale/missing read silently on live). Extended the
      gate to PREDICTION. Key correctness detail: prediction resolves the **dedicated flat kinds**
      `market-data-tick-prediction` / `instruments-store-prediction` (→ `*-pred-prd`), NOT the per-AG map (kind=
      `market-data`, asset_group=`prediction`) which RAISES `BucketNamingError` (prediction not in the map — the same
      map-vs-flat asymmetry as the execution-store). 2 new tests (both flat kinds gated + stale raises) + 4 existing
      sports tests green; QG green (156s). parent_epic: mtds_mdps_master.
- [ ] [CODE] P2. **instruments-service preflight short-circuits emit no `PREFLIGHT_SKIPPED`** (observability parity) —
      DUPLICATE of the existing IS STEP 5.64 todo above; 5 `_should_skip_date_for_per_league` sites in `orchestrator.py`
      (5398/5673/5894/6518/6821) return silently; `emit_preflight_skip` (UTL) is not imported. Not a run-blocker
      (observability only). repo: instruments-service.

## Readiness gate — operator's 7 criteria (slot-5 audit 2026-06-04 — extends slot-4's 4-item audit above)

> The operator's 2026-06-04 list is **7** criteria; slot-4's audit above covered the TradFi-style first ~5. This extends
> with **⑥ (IS+UAC guardrails)** + **⑦ (coverage denominator)** and **corrects ③** per slot-4's MDPS-consolidator
> finding. Slot-5 verified every contested claim (one fan-out agent's "critical gaps" on `candidate_parquet_paths` /
> phantom-auditor / candle-handling were grep-then-conclude noise — all refuted). Net verdict: ①④⑤⑥ verified; **③ has a
> real gap (slot-4 Gap 2)**; ② coupled to the gated migration; **⑦ is a genuine CROSS-AG gap**.
>
> - **① migrator dry-run ✅ DONE** (1,897,691 planned, exit 0); **⑤ paths-match ✅** (raw orchestrator insert + candle
>   fix mdps@5e7f075 on LDR + dual-probe readers).
> - **③ pre-flight 4-state — ✅ NOW FIXED (slot-4 found the gap, slot-5 fixed it — mdps@b8b515d):** the MDPS
>   `assert_consolidator_healthy` gate was **SPORTS-ONLY** (`dependency_checker.py` `if asset_group=="SPORTS"`) →
>   prediction (+ cefi/tradfi/defi) got no consolidator-health gate. **GENERALIZED to EVERY asset_group** (operator
>   2026-06-04: it's the SAME gate — a stale upstream consolidator is a silent-correctness risk for any AG with upstream
>   data, not just sports; no-op on fresh buckets so it only fires on a genuinely-stale consolidator). Prediction
>   resolves the FLAT bucket kinds (`market-data-tick-prediction`/`instruments-store-prediction`), others the per-AG
>   dict kinds. 7 tests (parametrized cefi/tradfi/defi + prediction flat-kinds regression; flipped the old
>   non-sports-skips test). features-delta_one / strategy (`manifest_allocation_guard`) / execution already had their
>   4-state preflight. **(This subsumes slot-4 Gap 2 — done.)**
> - **④ empty/partial honest + downstream batch+live ✅** (within-bounds `reemit_honest_absence_rows`; lifecycle
>   pre-creation/post-settlement reject in adapters → typed-empty/expected not failure; the no-trade CANDLE uses the
>   SHARED MDPS `candle_write_mixin` finalize = NaN-vol + prior-day last-price carry, deterministic batch==live; UAC
>   `EmptyConfirmedReason`/`CanonicalQuestionGroup`/`MarketLifecycle` shared).
> - **⑥ IS+UAC guardrail vs impossible instruments ✅** (universe from IS `instrument_availability`; lifecycle reject;
>   UAC cqg+lifecycle contracts; phantom auditor HAS prediction — `reconcile_phantom_manifest_rows_all.py`
>   ASSET_GROUP_CONFIG["prediction"], refutes the "sports-only" noise — see the P2 bucket-name nit below).

- [x] ✅ [DATA] P0. **② Manifest-rebuild dry-run — DEMONSTRATED on a 1-day canonical sample (slot-5 2026-06-04).** The
      live `pred-prd` bucket was still pre-migration (old `category=/data_source=` shape → the rebuild's full-range
      `--dry-run` reported every object "unparseable"). So (per operator "create the paths so we can dry-run") I
      migrated **1 day** (`migrate_prediction_to_pred_prd_v9.py --start-date 2025-03-14 --end-date 2025-03-14 --apply` →
      **537 objects copied** = raw 96 + candles 441, additive — old-shape preserved, idempotent vs the full run), then
      ran `rebuild_prediction_manifest.py --dry-run` on it: **Listed 85 canonical objects** (vs 0 pre-sample),
      classified **1 captured cqg-bundle**, ran the **CF-11 honest-absence re-emit (2,321 empties, 41
      SOURCE_RETURNED_ZERO preserved)** — proving the rebuild parses + classifies the canonical shape end-to-end. ENV
      gotcha: both the migrator's `gcs_copy_object` AND the rebuild's CF-11 `_index` read need `GCP_PROJECT_ID` set
      (else copy/read fail). **Residual to check (NOT a blocker):** 84/85 sample objects were `failed_unclassified` (no
      cqg mapping for those condition_ids on day 1 — likely the same `classify_polymarket_to_canonical_group` coverage
      slot-4's migrator-cqg-drift gap touches). The full-range scoping number (tradfi-equivalent) rides the gated E4
      full run; the 1-day sample is the proof-of-capability. Repo: market-tick-data-service.
- [ ] [CODE] P1. **⑦ Coverage denominator does NOT use the could-exist universe — genuine CROSS-AG gap (slot-5 audit
      2026-06-04; affects ALL asset_groups' raw-tick coverage, prediction included).** deployment-api
      `data_status_hierarchical.py` computes the raw-tick coverage denominator from the MANIFEST ONLY
      (`read_availability_index`; the 4-state total is correct for ROWS THAT EXIST) — it NEVER intersects the
      instruments-service could-exist universe (confirmed: zero IS/catalogue refs). So a market that EXISTS in IS (a
      `condition_id` active on day D) whose **tick backfill has NOT run** produces **no manifest row** → invisible: the
      denominator silently shrinks to only-attempted and coverage% inflates. **No tick-layer rebuild seeds
      `expected_unattempted` from the IS universe** (prediction rebuild has none; sports:921/cefi:552 only PRESERVE
      existing rows — "record_expected_unattempted doesn't exist in this writer pattern"). Only the FEATURES delta-one
      layer seeds it (`record_out_of_scope_instruments`, per-AG — so FEATURE coverage is correct; RAW-TICK is not).
      **FIX (design call — likely BLOCKED-OPERATOR-DECISION on WHERE):** (a) a tick-manifest pre-flight seeds
      `expected_unattempted` for the IS could-exist universe (condition_ids active per `market_lifecycle`
      not-yet-captured) so the denominator == could-exist universe; OR (b) deployment-api intersects the IS catalogue at
      read-time. + regression test (IS-universe ⊃ manifest ⇒ denominator doesn't shrink). Repos:
      market-tick-data-service + deployment-api + instruments-service. parent_epic: mtds_mdps_master. **Operator: this
      is the exact "instruments exist but backfill hasn't run" visibility gap you named — cross-AG, so it likely wants
      ONE shared fix.** **PATTERN FOUND (the rollout the operator remembered "we did for some stuff") — slot-5
      2026-06-04:** the MTDS orchestrator ALREADY seeds expected_unattempted at the tick layer —
      `engine/orchestrator.py:3496` `record_expected_unattempted` (the
      `expected_unattempted_propagation_chain_2026_05_12` work): for venues in `skipped_shards` (venues IS supplied NO
      instruments for on (venue,date)), it writes `record_expected_unattempted` per expected data_type "so the manifest
      denominator accounts for these shards instead of leaving them invisible" — gated by
      `get_expected_data_types_for_venue` + `VENUE_DATA_TYPE_CAPABILITIES`. **So the pattern + the helper exist; the gap
      is GRANULARITY**: it fires at the VENUE level (whole venue had no instruments), NOT the per-market level
      prediction needs (a `condition_id` that IS HAS but whose tick backfill hasn't run, when the venue POLYMARKET
      otherwise has data). ROLLOUT = extend this same `record_expected_unattempted` propagation to seed
      per-`condition_id` from the IS lifecycle universe (active-on-day-D minus captured `observed_clusters`) — reuse the
      existing helper + `_load_market_lifecycle_for_date`, don't invent a new mechanism.
- [ ] [CODE] P2. **⑥ minor — phantom auditor prediction bucket is the LEGACY long-form name** (slot-5 2026-06-04):
      `reconcile_phantom_manifest_rows_all.py:85` maps `"prediction": ("market-data-tick-prediction", None)` (the
      L6-delete legacy bucket), not env-tiered `market-data-tick-pred-prd`. Resolve via `resolve_bucket_name` so the
      phantom audit runs against the canonical bucket post-migration. Repo: instruments-service.

## Success criteria

- [x] ✅ [CODE][UI] P1. **deployment-api turbo response ↔ deployment-ui contract — VERIFIED + FIXED a real mismatch
      (slot-5 2026-06-03).** Cross-repo audit (both sides read): the **turbo summary** path matches (UI
      `TurboSubDimension` consumes `observed_clusters`/`source`/`capture_status_counts` 4-state +
      `breakdown_axis="canonical_question_group"` — no drift; covered by `prediction_v9_breakdown.spec.ts`). But the
      **venue-detail drilldown** had a real contract mismatch: deployment-api emitted `category="PREDICTION"` while the
      UI `VenueDetailResult` expected `asset_group` → it was always `undefined` client-side and every prediction
      venue-detail fell back to the CeFi v1 render branch; the prediction instrument fields
      (`canonical_question_group`/`instrument_count`/`pipeline_mode`/`source`) were silently discarded by the TS type.
      **FIX (both sides):** deployment-api@f1dd7d5 — `VenueDetailResponse` now emits `asset_group` (computed mirror of
      `category`; basedpyright 0-err, NO `type: ignore`; 50 shard_detail tests pass). deployment-ui@f242055 —
      `VenueDetailResult` carries `asset_group` + `category?` + optional `base`/`quote` + the 4 prediction fields.
      **playwright gate satisfied** — repo@f242055 | pw:L2 ✓ (`npx playwright test --project=chromium     tests/smoke/`
      exit 0, 5 passed) | tsc 0 | regression: `tests/smoke/venue_detail_prediction_asset_group.spec.ts`. The END-TO-END
      real-data confirmation (turbo emits the shape on live v9 `_index` rows) still rides the operator-gated migration
      run — but the contract is now correct + regression-locked on both sides. Repos: deployment-api + deployment-ui.
- [x] ✅ [CODE] P2. **deployment-api `fetch_venue_detail` bucket routing for prediction v9 — FIXED + CONFIRMED-BUG
      (deployment-api@318db9b, slot-5 2026-06-03).** It WAS a real bug, not just uncertainty: `_prediction_venue_detail`
      read `build_bucket_name("instruments-service","prediction")` = `instruments-store-pred-prd-{pid}`, but the v9
      cqg-bundle manifest (`data_type=prediction_canonical_question_group` + `observed_clusters`) is MTDS-written into
      `market-data-tick-pred-prd-{pid}` → the prediction v9 drilldown read an empty/wrong bucket. `fetch_venue_detail`
      also IGNORES its `service` arg (`_ = service`), so the fix hardcodes the MTDS bucket
      (`build_bucket_name("market-tick-data-service","prediction")`) — correct because prediction venue-detail is
      definitionally MTDS-manifest-based (shard axis `("market-tick-data-service","prediction")`). Regression test
      `test_prediction_reads_mtds_bucket_not_instruments_store` asserts the MTDS bucket regardless of the caller's
      service arg (4/4 prediction tests green; QG `--no-fix` exit 0). On LDR FEATURE_GREEN; staging-promotion gated on
      the workspace dep-tier drain (UTL/UAC/deployment-service/strategy-service). Repo: deployment-api.

- 0 legacy-only prediction cells (canonical holds all historical POLYMARKET data + question-groups).
- **Deployment-api/UI render the prediction v9 bundled atom + `source`/`pipeline_mode` (data-status summary + drilldown
  agree with the canonical manifest) — the 4 CODE items above GREEN.**
- Canonical `pred-prd` `_index` = v9 + `pipeline_mode=` partition present + **`source` stamped on every cell (zero blank
  — HARD; the API source per venue, swap-resilient)**.
- `mdps-prediction-2025` relaunch unblocked (writes canonical-only).
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-prediction-…` deletable.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — prediction canonical form.
