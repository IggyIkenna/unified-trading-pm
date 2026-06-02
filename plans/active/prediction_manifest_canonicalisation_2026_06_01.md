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

- [ ] [DATA] P0. **Phase 0 — layout audit (MANDATORY, blocking — slot-2 DeFi lesson 2026-06-01)**: enumerate ALL
      top-level trees + nested layouts in the prediction source + canonical buckets before the walk (`raw_tick_data/`,
      `processed_candles/`, the 6-dimension `day=/category=/data_source=/venue=/…/market_category=/…` polymarket
      layout); classify duplicate (keep freshest) vs complementary (migrate all → canonical v9). The existing
      `rebuild_prediction_manifest.py` (ManifestWriter rebuild) is the manifest-side template. Cover every in-scope
      layout or the walk is incomplete (review-blocking). SSOT:
      `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § grounded recipe Phase 0.

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
      addition AND its cells stamp `kalshi*\*` as source. Do NOT open a separate prediction source walk.

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
      now invokes `migrate_prediction_to_pred_prd_v9` (dry-by-default + `--apply`) — run
      `bash deployment-service/scripts/vm/launch-canonical-migration-vm.sh prediction 2025-03-14 2026-06-01 dry` then
      review planned moves/timing in the VM log → optimise workers if >1h → re-fire `full` (no fire-and-forget:
      STARTED<60s + progress/hr + STOPPED; T+10min `gcloud instances describe`). **PENDING: VM launch + monitor (next
      session — VM-only per local-DNS constraint).**

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
- [ ] [DATA] P0. E6b CODEX-ALIGNMENT VERIFY-ITEM (operator final-gate 2026-06-01): a codex-alignment audit confirmed
      paths/columns/buckets/vocab are ALIGNED across codex + IS/MTDS/MDPS (all use UAC builders + `resolve_bucket_name`;
      no inline divergence) — see `cf_data_state_audit_slot3_2026_06_01.md`. **ONE prediction nuance to confirm before
      apply**: `codex/02-data/prediction-schema-paths.md` describes a `canonical_question_group={cqg}/` PATH SEGMENT for
      `data_type=prediction_canonical_question_group` (post-Plan-A target). The migrator's `candidate_parquet_paths`
      builds `.../data_type={DT}/{filename}.parquet` (cqg-as-filename, NO segment). For the 289 legacy question_group
      cells: list an ACTUAL legacy question_group object, confirm whether the canonical layout uses the SEGMENT vs the
      filename, and confirm the canonical READER resolves whichever my migrator produces. If the segment is required,
      extend the migrator's prediction path build for that data_type. (raw_tick/trades/ohlcv = unaffected.)
- [ ] [DATA] P0. E7 Verify: `cf_manifest_audit_2026_06_01.py market-data-tick-pred-prd-…` → CF-1…CF-12 GREEN on
      data-state (v9, source populated, pipeline_mode, asset_group, available_at, 0 legacy-only). Flip the CF-coverage
      rows in `predictions_master_audit_instructions.md`.
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

- [ ] [DATA] P0. **E5 rebuild classifier (`rebuild_prediction_manifest.py`): within-bounds empty → `attempted_failed`.**
      For every empty cell: if the market/condition exists + is within its active window + data_type
      guaranteed-when-listed (trades / prices on a live market) + not pre-launch → `attempted_failed` (`record_failed`),
      NOT `SOURCE_RETURNED_ZERO`/`empty_confirmed`. Audit the 41 existing `SOURCE_RETURNED_ZERO` rows — genuine
      source-zero vs masked fetch failure. Preserve the legit `EXPECTED_PRE_VENUE_LAUNCH` typed empties.
- [ ] [DATA] P0. **E5 rebuild: re-emit existing `attempted_failed` rows v9, status PRESERVED** — never silently relabel
      a failure to `empty_confirmed`; they stay flagged for backfill.
- [x] ✅ [CODE] P1. **Batch=live classifier-None divergence — DONE (mtds@5744ba61, 2026-06-02).** The live Polymarket
      adapter now emits `None` (NaN), NOT `"OTHER"`, for a sub-threshold classifier result (polymarket_adapter.py ~735);
      the orchestrator `write_chunk` splits null cqg rows BEFORE the captured groupby (`_prediction_unclassified` keyed
      by market_id) and the finalize loop emits one `record_failed(error="ClassifierConfidenceLow")` per market —
      byte-identical to `rebuild_prediction_manifest.emit_manifest_rows`. The REAL `CanonicalQuestionGroup.OTHER` group
      (value `"OTHER"`) stays a CAPTURED bundle, distinct from the `None` sentinel (they were indistinguishable before).
      3 regression tests in `test_polymarket_bundling_finalize.py` + updated `test_polymarket_adapter_lifecycle_gating`
      (now asserts sub-threshold → `None`, NOT `"OTHER"`). mtds QG green.
- [ ] [CODE] P1. **Kalshi classifier-None divergence (DISCOVERY slot-3 2026-06-02, mtds — follow-up to the Polymarket
      fix above)**: the Kalshi adapter still maps an unclassified result → `canonical_question_group="OTHER"`
      (`test_kalshi_adapter_lifecycle_gating.py:246` asserts it). The orchestrator finalize (shared across all
      prediction venues) treats a non-null `"OTHER"` as a REAL captured group, so Kalshi unclassified markets are
      bundled CAPTURED while Polymarket now routes them to `attempted_failed` — a venue-inconsistency + batch≠live for
      Kalshi. Fix the Kalshi adapter the same way (emit `None` for sub-threshold so the shared orchestrator routes it to
      `attempted_failed[ClassifierConfidenceLow]`); update the Kalshi lifecycle-gating test to assert `None` not
      `"OTHER"`. Target: `market-tick-data-service` Kalshi prediction adapter +
      `test_kalshi_adapter_lifecycle_gating.py`. Low live urgency today (prediction live corpus is Polymarket CLOB), but
      required for venue parity before Kalshi goes live.
- [ ] [CODE] P0. **Write-path CF-11 audit + fix (IS + MTDS prediction Polymarket adapters)**: on a genuine API error
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

## Success criteria

- 0 legacy-only prediction cells (canonical holds all historical POLYMARKET data + question-groups).
- Canonical `pred-prd` `_index` = v9 + `pipeline_mode=` partition present + **`source` stamped on every cell (zero blank
  — HARD; the API source per venue, swap-resilient)**.
- `mdps-prediction-2025` relaunch unblocked (writes canonical-only).
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-prediction-…` deletable.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — prediction canonical form.
