---
title:
  "Consolidated CF-1…CF-12 data-state audit results — slot-3 surfaces (cefi/tradfi/sports/prediction + instruments +
  downstream)"
created: 2026-06-01
author: ikenna (slot-3)
source:
  - plans/audit/results/cf_manifest_audit_2026_06_01.py (the reusable tool that produced these)
  - canonical_form_cross_service_audit_checklist.md (CF-1…CF-12 SSOT)
master: defi_manifest_canonicalisation_2026_06_01.md
---

# Consolidated CF data-state audit — slot-3 surfaces (2026-06-01)

Read with `cf_manifest_audit_2026_06_01.py` against the **actual** prod `_index` rows (never the
`MANIFEST_SCHEMA_VERSION` constant — the manifest-v8 lesson). This is the audit-first P0 result for all six slot-3
plans. **defi = slot-2** (not audited here).

> ⚠️ **IRREVERSIBILITY — THE MIGRATION DELETES ALL LEGACY DATA PERMANENTLY (operator 2026-06-01).** The end-state is a
> SINGLE source of truth: every legacy bucket + every legacy/duplicate path is **deleted** so data-status/manifest shows
> exactly one canonical view and we can truly see what data is missing. Therefore there can be **NO confusion** about
> the canonical form before running: the schema (v9), the path layout
> (`day=/pipeline_mode=/asset_group=/venue=/chain=/instrument_type=/data_type=`), the `source`-column + `available_at`
> semantics, and which layout is the source-of-truth where copies overlap must be **KNOWN FOR SURE** and verified GREEN
> on real data-state BEFORE the delete. **Do it ONCE, correctly** — there is no rollback once legacy is gone. The
> Phase-0 layout audit + the CF verify step are the guards; the delete (L6) runs ONLY after `cf_manifest_audit` is
> CF-1…CF-12 GREEN on the canonical bucket. This is why the operator gated the whole programme on "only once we're on
> v9, because we keep missing things."

## The systemic finding (uniform across the ENTIRE non-defi corpus)

Every canonical MTDS-AG `_index` **and** every instruments-store `_index` audited shows the **same** canonical-form debt
— the v9 canonicalisation was only ever a **constant bump**, never applied to data:

| CF   | invariant                      | data-state across ALL surfaces                                                                                                                                                                                                              |
| ---- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CF-1 | schema_version = v9            | **RED — 100% v8** on every surface (0 rows v9)                                                                                                                                                                                              |
| CF-3 | pipeline_mode partition/column | **RED — column blank/absent**, no `pipeline_mode=` path segment anywhere                                                                                                                                                                    |
| CF-4 | `source` COLUMN                | **RED — column ABSENT** on every surface (prediction/sports also have `data_source=` in PATH)                                                                                                                                               |
| CF-8 | `available_at` per-row         | **RED — column ABSENT** on every surface (only `written_at` write-time proxy)                                                                                                                                                               |
| CF-2 | `asset_group=` not `category=` | rows: tradfi/pred/defi have `asset_group` col; cefi/sports vacuous (no col). PATHS: prediction still `category=`; cefi/tradfi/sports have no AG segment (flat / partial-hive) — **RED on paths**                                            |
| CF-5 | typed empty reason             | GREEN everywhere EXCEPT **sports = RED-by-mislabel** (584,177 empties blanket-labeled `SOURCE_RETURNED_ZERO` on a schedule-driven AG → must become typed fixture/season/window reasons)                                                     |
| CF-7 | canonical names                | mostly clean; drift to relabel: `UNKNOWN`+blank venues (tradfi/pred), `COINBASE`vs`COINBASE-SPOT` (cefi), ODDS case-drift (sports `ODDS`/`ODDS_SNAPSHOT` upper vs `odds_horizon_bucket` lower), blank `data_type` (instruments-store cells) |
| CF-9 | env-split bucket               | GREEN (all canonical buckets are `-prd-`)                                                                                                                                                                                                   |

So per the **"Audit scope is a PRIOR, not a ceiling"** HARD RULE every AG walk is a **whole-corpus content rewrite**
(download+transform+upload to add the source/asset_group/pipeline_mode/available_at columns + re-version v9 +
re-partition paths), not the headline cell-count gap-fill.

## Per-surface detail

### MTDS (raw tick + MDPS candles share one `_index`)

| AG         | canonical `_index` rows | capture_status split                              | legacy-only cells (headline → ACTUAL)                   | object-path scheme                                                                                                                        |
| ---------- | ----------------------- | ------------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| cefi       | 2,640,864               | failed 1,330,271 / captured 1,310,443 / empty 150 | **838 → 5,233** (2020-01 OKX-FUTURES book_snapshot_5 …) | `raw_tick_data/by_date/{SYMBOL}.parquet` (FLAT, no hive) + `processed_candles/by_date/day=/timeframe=/data_type=/venue=` (hive, no AG/pm) |
| tradfi     | 144,062                 | captured 100,536 / empty 37,490 / failed 6,036    | **4 → 71** (2023-05 NYSE tbbo …)                        | (probe hit `configs/`; raw needs targeted check — no AG/pm partition)                                                                     |
| sports     | 786,408                 | **empty 584,177** / captured 202,067 / failed 164 | **0** (data complete)                                   | `processed/by_date/day=/data_type=/league_id=/timeframe=` (hive, no AG/pm); `data_source=` elsewhere                                      |
| prediction | 16,812                  | captured 14,491 / empty 2,321                     | 2,039 (confirmed)                                       | `raw_tick_data/by_date/day=/category=prediction/data_source=POLYMARKET_CLOB/venue=` (has `category=` + `data_source=` in path)            |

- tradfi empty-reasons (already typed): `EXPECTED_WEEKEND` 35,050 · `EXPECTED_HOLIDAY` 2,427 ·
  `EXPECTED_OUT_OF_COVERAGE_WINDOW` 8 · `SOURCE_RETURNED_ZERO` 5.
- sports empty-reasons: **`SOURCE_RETURNED_ZERO` × 584,177** (the keystone mislabel — relabel via the UAC coverage
  oracle).
- cefi `attempted_failed` is **50%** of rows (1.33M) — a separate coverage/health concern (E1-class fetch failures),
  surfaced for the AG owners; not a canonicalisation blocker.

### instruments-store (input/reference surface)

| bucket                       | rows   | CF-1                      | legacy-only                               |
| ---------------------------- | ------ | ------------------------- | ----------------------------------------- |
| instruments-store-cefi-prd   | 30,803 | v8                        | 23 (2025-10, blank data_type)             |
| instruments-store-tradfi-prd | 20,264 | v8                        | 60 (2026-03, blank data_type)             |
| instruments-store-pred-prd   | 493    | v8 (no pipeline_mode col) | (legacy long-form name — re-diff in walk) |

All: no source col · blank/absent pipeline_mode · no available_at · flat paths · **blank `data_type`** on cells (keyed
date+venue — verify intent). cefi/defi/tradfi/pred/sports each have an AG-partitioned `_index`.

### downstream services (low-data — confirmed)

- **MDPS** candles ride the AG MTDS `_index` (same bucket `processed_candles/`) → covered by each AG walk, **no separate
  walk**.
- **features / strategy / execution** for cefi/tradfi/sports/prediction: **NO `_index`** (no data run —
  `features-delta-one/mtf/volatility/calendar`, `strategy-store-*`, `execution-store-*` all absent). Lever =
  **writer-fix-first** (born-canonical) + re-audit when input C-GREEN + first batch runs. (Only
  `features-onchain-defi-prd` has an index = slot-2.)

## What each AG walk must do (bundled, single-walk, per the perf contract)

1. **Whole-corpus column rewrite** on the canonical bucket: `schema_version→9`; add `source` (from path `data_source=` /
   UAC SOURCE_PRIORITY); add/populate `pipeline_mode`; add `available_at` (preserve from parquet where present, else
   day-EOD-UTC backfill — never migration-time); add `asset_group` column where absent (cefi/sports).
2. **Path re-partition**: emit `asset_group={ag}` + `pipeline_mode={mode}` hive segments; for prediction also drop
   `category=` + lift `data_source=` → `source` column; for cefi derive `day=`/`venue=` from columns (flat
   `by_date/{symbol}` source layout).
3. **Legacy-only gap copy**: cefi 5,233 · tradfi 71 · prediction 2,039 · instruments cefi 23 / tradfi 60 (sports 0).
4. **sports keystone**: relabel 584,177 `SOURCE_RETURNED_ZERO` → typed fixture/season/transfer-window/genesis via the
   UAC coverage oracle.
5. **CF-7 relabel**: `UNKNOWN`/blank venues, `COINBASE`↔`COINBASE-SPOT`, sports ODDS case-drift, instruments blank
   data_type.
6. Re-consolidate the `_index` from rewritten data (data-state v9 verified, not the constant) → verify → hand C-GREEN to
   `bucket_name_ssot…` L6.

## Execution constraint (why the walks are VM-only, not local)

Local gcsfs/aiodns DNS is flaky on this host (the audit tool works around it with `gcloud cp` for the single index
parquet + a time-boxed shallow object probe). A whole-corpus content rewrite (millions of objects per AG) **must run on
a VM in asia-northeast1** per `codex/05-infrastructure/gcs-object-operations.md` § Migration-script performance contract
(ThreadPoolExecutor parallel walk, wired `--workers`/`--start`/`--end` date-sharding, `gcs_copy_object` for path-only
moves, unbuffered progress, per-object isolation, idempotent). The `--apply` cutover is additionally gated on the
**fleet-wide pre-migration drain** (stop GCP+AWS writers → consolidate → snapshot each `_index`), which is shared with
slot-2's defi walk and coordinated at epic `mtds_mdps_master`. **Dry-run is read-only and needs no drain.**

## MECHANISM FINDING (system-first, 2026-06-01) — the `_index` columns come from the WRITER, not the data parquets

A direct probe of a cefi raw parquet (`raw_tick_data/by_date/AVAXUSDT.parquet`, 122,179 rows) shows it carries **pure
market data** (`exchange, symbol, timestamp, funding_rate, last_price, mark_price, …, data_type, instrument_id`) —
**NOT** the manifest columns. So `schema_version` / `source` / `pipeline_mode` / `asset_group` / `available_at` are
**MANIFEST `_index` columns**, produced by the UTL `ManifestWriter` + manifest-consolidator — they do not live in the
data parquets. Implications for the walk design (corrects the "rewrite every data parquet's columns" framing inherited
from the defi-dedicated-bucket tool, whose buckets store differently-shaped rows):

- **The CF debt the audit reads is in the `_index` manifest + object PATHS** — fixing it means rebuilding the manifest
  through the **v9 `ManifestWriter`**, not rewriting tick parquets.
- **Sanctioned pattern = `rebuild_prediction_manifest.py`** (MTDS scripts): scan canonical object paths → derive shard
  keys → `ManifestWriter.add(...)` / `record_empty(reason=…, pipeline_mode=…)` with `per_vm_shards=True` → consolidator
  merges `_index/per_vm/*` into `availability_index.parquet`. The writer stamps the CURRENT (v9) schema + the canonical
  columns (`pipeline_mode`, `source`, `asset_group`, `available_at`). **Re-consolidation alone won't add columns absent
  from historical v8 per-shard fragments — the rebuild RE-DERIVES them from the canonical paths.**
- **`source` per-row provenance**: cefi = single-source (`tardis`) → stamp directly. sports/prediction carry
  `data_source=` IN the object path → the rebuild reads it from the path and stamps the `source` column (this is the
  CF-4 path→column lift). tradfi = per UAC `SOURCE_PRIORITY` / the BARCHART·YAHOO_FINANCE·DATABENTO·MASSIVE venue→source
  map. So `source` population REQUIRES the object-path scan (not derivable from the `_index` alone for multi-source
  AGs).

## CROSS-AG LESSON from slot-2's live DeFi migration (operator 2026-06-01) — audit ALL layouts before migrating

Slot-2's DeFi C0 run surfaced that a source bucket can hold **multiple overlapping legacy layouts** that a naive
day-prefix walk silently under-migrates. DeFi `dex-pools` had THREE: (1) `day=/category=defi/venue=…` flat-legacy
(~19K), (2) `raw_tick_data/by_date/day=/asset_group=defi/venue=/chain=/…/data_type=…` near-canonical (the bulk, missing
`pipeline_mode=`), (3) `dex_pools/{venue}/{chain}/date=…` older (bare segments, `date=` not `day=`, no asset_group → the
path parser skipped it). The day-prefix run migrated only #1 and would have left a **partial canonical set + data loss
on legacy delete** — the exact failure this programme exists to end.

**Operator directive (applies to EVERY slot-3 AG walk)**: the script must **audit all source layouts, determine overlap
vs complementary, pick the freshest/best schema where they overlap, land EVERYTHING on the one v9 manifest + data
schema, and only run the real migration once we're genuinely on v9 — "because we keep missing things."** Net end-state:
**old buckets + old paths all deleted → ONE source of truth** so data-status/manifest shows true missing-data. So
**Phase 0 (layout audit) is mandatory and blocking** before any AG walk — never assume a single layout from a sample.

## Grounded per-AG walk recipe (the build, system-first on existing MTDS tools)

**Phase 0 — layout audit per bucket (MANDATORY, blocking; the slot-2 DeFi lesson)**: enumerate ALL top-level trees +
nested layouts in each source/canonical bucket (`day=/category=`, `raw_tick_data/by_date/…`, bare
`{venue}/{chain}/date=`, `processed/`, `processed_candles/`, `sports_reference/`, …). For each: count objects, read a
sample schema, determine which layouts are **duplicates** (→ keep the freshest/most-canonical, discard the rest) vs
**complementary** (→ migrate all, mapping each to the canonical v9 form). Output a per-bucket layout manifest. The walk
must cover EVERY in-scope layout or it is incomplete — review-blocking.

Then, per AG, ONE bundled VM walk (single-walk discipline), built by generalising the proven tools:

1. **Object-path re-partition + legacy-gap copy** — extend the per-AG layout tool
   (`migrate_{sports,tradfi,polymarket}_canonical.py` exist; cefi needs one) to emit the canonical
   `…/day=/pipeline_mode={mode}/asset_group={ag}/…` layout and `gcs_copy_object` the legacy-only objects (cefi 5,233 ·
   tradfi 71 · prediction 2,039 · instruments cefi 23 / tradfi 60) into canonical paths. ThreadPoolExecutor + wired
   `--workers`/`--start`/`--end` + idempotent (perf contract).
2. **Manifest rebuild → v9** — generalise `rebuild_prediction_manifest.py` to `rebuild_{ag}_manifest_v9.py`: scan the
   canonical paths, `ManifestWriter.add/record_empty` with `pipeline_mode` + `source` (from path `data_source=` / UAC
   SOURCE_PRIORITY) → consolidator merge → `_index` becomes v9 + canonical columns + `available_at`.
3. **sports keystone (CF-5)** — relabel the 584,177 `SOURCE_RETURNED_ZERO` empties to typed
   fixture/season/transfer-window reasons via the UAC coverage oracle at rebuild time (`record_empty(reason=…)`), driven
   by `clip_dates_to_source_coverage` / `is_in_known_gap` / `league_data`.
4. **CF-7 relabel** — `UNKNOWN`/blank venue, `COINBASE`↔`COINBASE-SPOT`, sports ODDS case-drift, instruments blank
   data_type.
5. **Verify** — re-run `cf_manifest_audit_2026_06_01.py` → all CF GREEN on data-state → hand C-GREEN to
   `bucket_name_ssot…` L6.

Execution: VM in asia-northeast1 (object scan is ~25 min/AG for prediction-scale, more for cefi), `--apply` gated on the
fleet drain. DeFi is slot-2's lane (the defi v9 tool + its dedicated-bucket shape) — not in slot-3 scope.

## Phase-0 LAYOUT audit results (tool `cf_layout_audit_2026_06_01.py`, 2026-06-01)

Confirms the multi-layout reality — each AG bucket has ≥2 distinct layouts that the migrator MUST all handle/reconcile:

- **cefi** (prd AND legacy, identical layout set):
  - `raw_tick_data/by_date/{SYMBOL}.parquet` — **FULLY FLAT**, no hive at all. day/venue/data_type live ONLY in the
    parquet columns (`exchange, symbol, timestamp[epoch-micros], data_type, instrument_id, funding_rate, …`). The
    migrator must derive day (from epoch-micros `timestamp`), venue (from `exchange`/`symbol`), data_type (column) per
    row and re-partition to canonical hive — possibly **fanning out one flat symbol-file into many day= partitions**
    (122,179 rows × 94,048 distinct timestamps in one AVAXUSDT file). Hardest AG.
  - `processed_candles/by_date/day=/timeframe=/data_type=/venue=` (MDPS candles) — has `day=` but no
    `asset_group=`/`pipeline_mode=`.
- **prediction** — **legacy and canonical layouts are INVERTED** (needs reconciliation, not blind copy):
  - legacy raw: `raw_tick_data/by_date/day=/asset_group=/venue=/instrument_type=/data_type=` (near-canonical — already
    has `asset_group=`; rich parquet cols incl `asset_group, data_source, chain, underlying`).
  - canonical pred-prd raw (from the CF audit): `…/day=/category=/data_source=/venue=/…` (has `category=` +
    `data_source=` — LESS canonical than legacy on the AG key). So "pick the freshest schema" here = the **legacy**
    asset_group= layout is closer to target; the migrator must converge both onto `day=/asset_group=/pipeline_mode=/…`.
  - `processed_candles/by_date/day=/timeframe=/data_type=/venue=` (candles).
- **(tradfi / sports / instruments)**: run `cf_layout_audit_2026_06_01.py` on each before its walk (Phase 0). Expect the
  same shape — a raw tree (flat or partial-hive) + processed_candles + possibly an older bare-segment tree.

### Complete Phase-0 layout map (all 4 MTDS AGs, 2026-06-01) — each AG needs a BESPOKE migrator

| AG         | raw_tick_data layout (the hard tree)                                                                                                                                                     | processed(\_candles)                                                                             | notes                                                                                                                          |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| cefi       | **FLAT** `raw_tick_data/by_date/{SYMBOL}.parquet` — NO path dims; day/venue/data_type only in parquet cols (`exchange,symbol,timestamp[epoch-µs],data_type`)                             | `processed_candles/by_date/day=/timeframe=/data_type=/venue=`                                    | flat → derive dims + fan-out to day= partitions                                                                                |
| tradfi     | **HYPHEN pseudo-hive** `raw_tick_data/by_date/day-2025-11-02/data_type-ohlcv_1m/equities/NYSE/{id}.parquet` (`-` not `=`, bare `equities`/`NYSE`) + a `databento-batch-registry/` tree   | same candle layout                                                                               | hyphen-delim parse; sample raw file had **0 rows** (verify not-empty); cols `timestamp,symbol,ohlcv,instrument_key,underlying` |
| sports     | full hive `raw_tick_data/by_date/day=/category=/data_source=/venue=/league_id=/instrument_type=/data_type=` (parquet already has `source` + `data_source` cols)                          | `processed/by_date/day=/data_type=/league_id=/timeframe=` (also has `source`/`data_source` cols) | category=→asset_group=, data_source= path→source col (already in col too), keystone reason relabel                             |
| prediction | legacy `raw_tick_data/by_date/day=/asset_group=/venue=/instrument_type=/data_type=` (near-canon) vs canonical pred-prd `…/category=/data_source=/venue=/…market_category=/underlying=/…` | candle layout                                                                                    | INVERTED legacy↔canonical; `rebuild_prediction_manifest.py` exists                                                            |

**Conclusion**: per-AG bespoke migrators (matching the existing `migrate_{sports,tradfi,polymarket}_canonical.py`
structure), NOT one generalized tool. cefi needs a NEW flat→hive fan-out migrator (none exists). Each converges its
source layout(s) onto the single canonical `day=/pipeline_mode=/asset_group=/venue=/chain=/instrument_type=/data_type=`
target + a `ManifestWriter` v9 rebuild (auto-stamps `schema_version=9` + `source`/`pipeline_mode`/`available_at`).

**Design consequence**: the migrator is genuinely **layout-dispatching** — per object it must detect its source layout
and map to the single canonical `day=/pipeline_mode=/asset_group=/venue=/chain=/instrument_type=/data_type=` target,
deriving missing dims from parquet columns (cefi flat), reconciling inverted schemes (prediction), and deduping any
overlap to the freshest. Then the `ManifestWriter` rebuild stamps v9 + source + pipeline_mode + available_at. This is
why the operator gated it on "only once we're on v9, no more missing things" — the Phase-0 audit per AG is the guard.

## CROSS-AG EXECUTION LESSONS (slot-3 prediction build, 2026-06-01) — EVERY AG migrator MUST apply these

> These are the concrete mistakes/findings surfaced executing the prediction migrator first (the proving ground). cefi /
> tradfi / sports / instruments inherit ALL of them. Each is a "we keep missing things" trap.

0. **EXHAUSTIVE layout enumeration is MANDATORY — the shallow first-leaf probe LIES (operator "3 versions like defi"
   check, 2026-06-01).** `cf_layout_audit`'s shallow descent reported cefi raw as "FULLY FLAT" because it hit the 9
   orphan root files first; the REAL state is **2,613 `day=` dirs + 9 flat orphans + some already-`pipeline_mode=`
   canonical = THREE layouts**. The first cefi migrator handled ONLY the 9 orphans → it would have **silently lost 2,613
   day-partitions** on legacy delete. Before any migrator runs, for EACH bucket: (a) list top-level prefixes, (b) for
   the raw tree **COUNT children by kind** — `gcloud storage ls .../by_date/` then count `*.parquet` (flat) vs `day=`
   dirs vs other; a mix = ≥2 layouts; (c) descend one `day=` to read the sub-layout (`asset_group=`? `category=`?
   `pipeline_mode=`? bare?); (d) sample MULTIPLE days, not one. A migrator MUST handle every layout found (defi had 3,
   cefi has 3, prediction legacy has 2 sub-layouts under `day=`). The dry-run's `TOTAL planned` count MUST be
   sanity-checked against the full corpus object count — if it's way under, a layout was missed. **Never trust a single
   shallow probe before an irreversible delete.**

1. **Canonical path order is UNANIMOUS + load-bearing — use the UAC builder, never hand-roll.** The shared
   `market-data-tick-{ag}-{pid}` canonical layout is
   `raw_tick_data/by_date/day={D}/pipeline_mode={MODE}/asset_group={ag}/ venue={V}/[chain={C}/]instrument_type={IT}/data_type={DT}/{file}`
   — `pipeline_mode` LEFT of `asset_group=`, day FIRST. Confirmed by THREE authorities: UAC
   `candidate_parquet_paths(ag, dt, day, pipeline_mode=mode)[0]` (`unified_api_contracts.canonical.partition_paths`) +
   the UTL writer (UTL@87134364) + the reader Level-0 probe (`manifest_reader_fallback.py`). **Every migrator MUST build
   dest paths via `candidate_parquet_paths(..., pipeline_mode=...)[0]`** → byte-identical to a live write (batch=live),
   correct-by-construction. (The DeFi v9 tool uses a DIFFERENT shape because it migrates DEDICATED per-type buckets
   `dex-pools-prd-…`, not the shared market-tick buckets — slot-2's lane, do not copy its path order for shared-bucket
   AGs.)

2. **Multi-source completeness — NEVER "copy the bigger bucket into the smaller" (operator catch).** A source bucket can
   have cells the target lacks AND vice-versa. Compute BOTH directions: legacy-only AND canon-only. Prediction: legacy
   2,822 captured cells, canon 805, overlap 783 → 2,039 legacy-only AND **22 canon-only**. Blindly dropping the stale
   target objects would have lost the 22. The migrator must canonicalise EVERY source layout into the target, dedup to
   freshest, and only delete originals AFTER the union is canonicalised.

3. **The headline cell-count is a PRIOR, usually wrong — read DATA-STATE.** The prediction plan header said canon =
   3,086 cells; the real data-state was **805**. (Same lesson as the cefi "838-cell" → full-re-canon incident.) Re-run
   the CF + layout audits on the actual `_index`/objects before sizing or designing.

4. **"Overlap" by `(date,venue,data_type)` is CONTAMINATED by CF-7 drift — normalise BEFORE comparing/deduping.** Legacy
   and target often label the SAME data differently: prediction had `data_type=prediction_trades` (target) ≡ `trades`
   (legacy) for the identical markets, plus `venue=UNKNOWN`/blank. Computing overlap on raw labels yields phantom
   legacy-only/canon-only counts AND, if path-preserved, **duplicate vocab in the survivor**. Bake CF-7 normalisation
   (`_cf7_normalise`) INTO the path transform, BEFORE dedup — not as a separate post-step.

5. **Verify the overlap is the SAME DATA — sample object content, not just cell keys.** For prediction the clean
   `(POLYMARKET,trades)` overlap was byte-identical (same condition_ids, identical per-object row counts across sampled
   days) → "X-wins-the-overlap" was proven safe. Do this sample per AG before trusting any dedup-to-freshest; if the
   "winner" has FEWER rows than the loser for a shared object, switch dedup to keep-the-larger / merge.

6. **"canon-only / unique" cells are often DRIFT, not precious data — diagnose, don't blind-preserve OR blind-drop.**
   Prediction's 22 canon-only were `venue=UNKNOWN`/blank degenerate rows (single-venue AG → POLYMARKET), not unique data
   (canon had NO `ohlcv_*`/`question_group` legacy has). Decide per-object: object-backed real-but-mislabeled → relabel
   (CF-7); no backing object → phantom → honest drop (never migrate a manifest row with no object).

7. **`row_count` can be NaN across an ENTIRE `_index`** (canon prediction had it 0/14,491 populated) → NaN is NOT a
   phantom signal by itself. Confirm against the clean rows / object existence before concluding phantom.

8. **Manifest GRANULARITY can differ between legacy and target `_index`** (prediction: legacy 449k rows vs canon 16.8k
   for the same AG). The rebuild must reconcile to ONE granularity (the canonical shard atom). The canonical path often
   DROPS dims the legacy path carried (prediction lost `underlying=`/`chain=`/`data_source=` → now PARQUET COLUMNS) →
   the rebuild MUST READ those columns from the parquet, not the path, to populate the manifest row + `source`. Confirm
   the rebuilt row-key granularity matches the existing `_index` so verify is apples-to-apples and dedups (not
   double-counts).

9. **`source` column is authoritative from the parquet/path data_source, not guessable** — stamp it at rebuild via UAC
   `source_string_for`/`pipeline_mode_for_source`. `pipeline_mode` is path-derivable (data_type/data_source) and must be
   the SAME value in the path segment AND the manifest column.

10. **Additive copy (`--apply`) is non-destructive; only the DELETE is irreversible + drain-gated.** Run dry →
    apply-copy → rebuild → CF verify freely (copies write NEW canonical paths). Gate ONLY the legacy/stale DELETE on
    CF-1…CF-12 GREEN on real data-state + the fleet drain (shared w/ slot-2). Verify-before-delete is the HARD guard.

11. **DELETE ALL AT THE END, after a final strategically-sampled-across-shards verify — NEVER inline (operator
    2026-06-01).** Migrators MUST be additive-only (`--apply` copies; deletion is a SEPARATE explicit end-stage flag,
    never inside the copy loop). Reason: inline delete destroys the source BEFORE a migrator bug is found — the cefi
    3-layout miss this session would have permanently deleted 2,613 day-dirs under inline delete. Mandatory end-delete
    protocol (every AG): (a) `--apply` additive copy; (b) E5 manifest rebuild → v9 via `record_captured_from_counts` (it
    takes `pipeline_mode`+`source`; `add()` does NOT persist pipeline_mode → that's why CF-3 reads blank); (c) CF-1…
    CF-12 GREEN; (d) **completeness COUNT gate** — canonical distinct-cells ≥ UNION of every source layout's distinct
    cells (a shortfall = a missed layout → STOP); (e) **strategically-sampled cross-shard verify** — sample across
    (date-range × venue × data_type × EACH layout × AG); per sample confirm canonical object exists + content matches
    legacy + manifest row v9-correct; (f) ONLY THEN bulk-delete legacy buckets + superseded in-bucket paths (prediction
    `category=`, cefi `day=/asset_group=` lacking `pipeline_mode=`) at once; (g) fleet-drain (w/ slot-2) precedes it.

12. **0-ROW OBJECT CONTAMINATION is per-AG — audit EACH, never assume tradfi-only (operator cross-check 2026-06-02).** A
    clean pipeline records empties manifest-only (`record_empty`, NO object), so a 0-row PARQUET OBJECT on disk = a
    bad-write bug, and a path-only migrator would COPY it into canonical → phantom canonical cell (false-complete at the
    G6 count). Row-count (footer) audit of all three slot-3 AGs (2026-06-02): **tradfi = CONTAMINATED** (the ~110k
    hyphen `day-` Massive dry-run placeholders, uniform 3070/4251-byte header-only → migrator 0-row guard + E7 delete);
    **cefi = CLEAN** (day= smallest objects are real low-volume cells, e.g. 3-row 6.3KB liquidations — no header-only
    cluster; only the 9 root files are malformed, and they are REAL data fanned out by the L-flat branch which already
    `df.empty`-skips); **prediction = CLEAN** (smallest ~16KB real Polymarket trades, no 0-row signature). **The
    UNIVERSAL guard is the E5 rebuild**: any object that reads 0 rows → `record_empty`/`attempted_failed`, NEVER
    `record_captured` (UTL 4-pillar rejects row_count=0 anyway) — bake this into all three rebuilds so a stray 0-row
    object anywhere can never become a captured cell. A migrator-level footer guard is added ONLY where contamination is
    known (tradfi hyphen) — NOT on the cefi/prediction bulk path-copy (would kill the server-side-copy perf for no
    benefit on an audited-clean corpus; the E5 + G6 + G7 gates are the backstop). **GOTCHA caught here: the prediction
    canonical bucket is `market-data-tick-pred-prd-…` (`pred` short-token), NOT `…-prediction-prd-…`.** A first probe
    used the wrong name → returned empty → would have FALSELY scored "prediction clean" without inspecting any object.
    Always resolve the bucket via `resolve_bucket_name`/the `pred` token + confirm the probe actually hit objects before
    concluding clean (a near-miss of the exact "we keep missing things" failure).

## CANONICAL DECISIONS (operator-ratified 2026-06-01) + doc/plan supersession sweep

These are the ratified canonical conventions for the whole tick corpus. **Every plan + codex doc must reflect them; any
doc describing an older form must be UPDATED or banner-SUPERSEDED pointing to the superseding plan + why.** Recorded so
no agent "hacks fake buckets/paths/columns to fit stale docs and regresses."

### Ratified canonical form

1. **PATH**
   `raw_tick_data/by_date/day={D}/pipeline_mode={MODE}/asset_group={ag}/venue={V}/[chain={C}/]instrument_type={IT}/data_type={DT}/{file}`.
   `pipeline_mode=` is **canonical IN the path** (operator decision 2026-06-01: "stick to pipeline*mode since it's
   canonical and fix the readers/writers" — lead the convention, do not retreat). **Known gap to close (cross-AG):** the
   BASE
   `build*{defi,cefi,tradfi,prediction}\_partition_path`does NOT include`pipeline_mode=`— only`candidate_parquet_paths(...,
   pipeline_mode=…)[0]`prepends it (slot-2 primary-source finding). So readers/writers that call the BASE builder directly would miss pipeline_mode= data → they MUST be migrated to the pipeline_mode-aware path as PRIMARY (this is`pipeline_mode_partition_migration`/`pipeline_mode_implementation`intent). Migrators already emit it via`candidate_parquet_paths[0]`
   — correct.
2. **COLUMNS (v9)** schema_version=9 + asset_group + pipeline_mode + source + available_at. `ManifestWriter.add()` now
   persists `pipeline_mode` (utl@b872bdf1; was dropped → CF-3 blank); `record_captured*` already did.
3. **data_type = ON-DISK form, not the logical/manifest key** (the `dex_pool_state` / `_resolve_partition_data_type`
   lesson): dex_pools→`dex_pool_state`, dex_swaps→`dex_pool_swaps`, rate_indices→`lending_indices`,
   futures_chain→`options_chain` (data_type only; instrument_type kept). Migrators MUST mirror the live writer's merge.
4. **BUCKETS** `market-data-tick-{ag}-prd` via `resolve_bucket_name` (pred short token). **venue** = data-state form
   (cefi HYPHENATED BINANCE-FUTURES/COINBASE-SPOT; COINBASE→COINBASE-SPOT). **DELETE at END only, after sampled verify**
   (lesson #11).

### Supersession mapping (mark these in the named files)

| Superseded plan/section                                                | Superseded BY                                     | Why                                                        |
| ---------------------------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------- |
| `tradfi_massive_dual_source` — source re-consolidation task            | `tradfi_manifest_canonicalisation` C-source rider | source col rides the L3 single-walk; no separate walk      |
| `data_source_provenance_all_asset_groups` — per-AG source-col backfill | each AG's L3 `*_manifest_canonicalisation` rider  | rides the single walk (HARD RULE); never a standalone walk |
| `pipeline_mode_partition_migration` — per-AG partition write           | each AG's L3 walk (emits `pipeline_mode=`)        | partition lands in the L3 walk                             |
| `bucket_name_ssot…` Phase-5 `--manifest-only` seed (NON-DeFi)          | each AG's L3 `_index` rebuild                     | guarded out 2026-06-01; L3 owns the rebuild                |

### Codex/plan doc-update TODOs (tracked dispatch — an agent must action these before independent execution)

- [ ] [DOCS] P1. Codex sweep: grep `codex/02-data` + `codex/04-architecture` + repo `docs/GCS_PATHS.md` for any path
      example WITHOUT `pipeline_mode=` shown as canonical, OR `category=` as canonical, OR data_type=dex_pools/dex_swaps
      as the on-disk form → update to the ratified form above OR add `SUPERSEDED → <canonicalisation plan>` banner. (The
      2026-06-01 codex-alignment audit found docs MOSTLY aligned; this closes the residuals + the
      pipeline_mode-base-builder gap.)
- [ ] [DOCS] P1. Banner the four superseded plan sections in the table above with `SUPERSEDED BY <plan> — <why>`.
- [ ] [CODE] P0. pipeline*mode reader/writer alignment (cross-AG, coordinate w/ slot-2): make the pipeline_mode-aware
      path the PRIMARY in
      `build*_*partition_path`consumers (not just a`candidate_parquet_paths`fallback) so live     reads find migrated data. Targets: MTDS reader, MDPS cloud_data_provider, features-onchain data_loader, any direct    `build*_\_partition_path`
      caller. (manifest_reader_fallback Level-0 already probes pipeline_mode= → readers using it are safe; this closes
      base-builder callers.)

## 🎬 NEXT-AGENT EXECUTION HANDOFF — non-DeFi migration + deletion (slot-3 → next, 2026-06-02)

> Paste-ready dispatch. You finish the remaining PREP, then run the REAL migration + the IRREVERSIBLE delete for
> **cefi + tradfi + prediction** (sports = its own slot via that plan's pickup prompt; defi = slot-2). FIRST read
> `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`; read THIS whole doc (esp. "CROSS-AG EXECUTION LESSONS" #0–#11 +
> "CANONICAL DECISIONS"); `git pull --ff-only origin live-defi-rollout`. Commit+Push+Flip each unit same-turn.

### STATE — DONE + verified (do not redo)

- **Migrators built + validated**: `migrate_prediction_to_pred_prd_v9.py` (dual-source A+B reconciliation + CF-7) and
  `migrate_cefi_flat_to_v9_canonical.py` (3 layouts: day= bulk pipeline_mode-insert + v6 chain-bundle preserve + 9 flat
  orphans fan-out; CF-7 venue/data_type; on-disk data_type merge futures_chain→options_chain). cefi **completeness
  SAMPLE ✅** (7 days 2020→2026, src==planned==3847, bundle 30/30, 0 skips). Prediction overlap content byte-identical
  (verified). **FOUR completeness-gate-caught bugs already fixed** (3-layout, chain-bundle, chain-instrument-type,
  data_type-merge) — proof the gates below are mandatory, not optional.
- **UTL**: `ManifestWriter.add()` now persists `pipeline_mode` (utl@b872bdf1, QG-green) — unblocks E5 on the
  per-instrument path. `add()` already auto-resolves `source` from SOURCE_PRIORITY.
- **Decisions locked** (this doc): pipeline_mode= IS canonical-in-path; data_type = on-disk form (the merge map); delete
  END-only after sampled verify; #7 coordinator fixed (non-DeFi seed guard + filed-plan refs).
- **Launcher wired**: `deployment-service/scripts/vm/launch-canonical-migration-vm.sh {cefi,prediction}` → the v9 tools
  (dry-by-default + `--apply`). Re-tarball at current HEAD (`create-code-tarballs.sh`) + pin MTDS/UAC/UTL SHAs per
  launch.

### REMAINING PREP (HARD gate before any --apply)

1. **BUILD tradfi migrator** (not built). Layout (audit): HYPHEN pseudo-hive
   `day-2025-11-02/data_type-ohlcv_1m/equities/ NYSE/{id}.parquet` (`-` not `=`, bare segments) +
   `databento-batch-registry/` tree. Reuse `migrate_tradfi_canonical.py`
   - `_migrate_tradfi_hyphen_rewriter.py` + `_migrate_tradfi_classifier.py`; emit canonical via
     `candidate_parquet_paths`; tradfi `source` is REQUIRED (databento/massive) per v9. Run the SAME completeness sample
     for tradfi before apply.
2. **BUILD E5 manifest rebuilds** (cefi/tradfi/prediction): adapt `rebuild_{cefi,prediction}_manifest.py` — (a) extend
   the path regex for the new `pipeline_mode=` segment, (b) stamp `pipeline_mode` + `source` via
   `record_captured_from_counts` (NOT add()-counts; add() lacks counts+pipeline together — or use the new add() kwarg +
   record_captured_from_counts for bundles). Row key = live-writer 10-field (orchestrator.py:2937). available_at =
   parquet col else day-EOD-UTC.
3. **Reader/writer pipeline_mode-PRIMARY** (cross-AG, coord slot-2): base `build_*_partition_path` lacks pipeline_mode;
   make the pipeline_mode-aware path PRIMARY in direct base-builder callers (MTDS reader, MDPS cloud_data_provider,
   features-onchain data_loader). manifest_reader_fallback Level-0 already probes it → fallback-using readers are safe.
4. **Codex/plans doc sweep + supersession banners** — execute the "doc-update TODOs" + "supersession mapping" in the
   CANONICAL DECISIONS section above.

### THE GATES (run IN ORDER, per AG — never skip; the sample ≠ exhaustive)

G1. **Full-corpus VM dry-run** in asia-northeast1 (re-tarball+pin first):
`launch-canonical-migration-vm.sh <ag> <start>     <end> dry`. Confirm `TOTAL planned` ≈ full-corpus source object count
(cefi = millions across 2,613 day-dirs + bundles + 9 orphans, NOT 9). A shortfall = a missed layout → STOP + fix. This
is the DEFINITIVE completeness gate. G2. Per-AG writer drained + snapshot `_index` →
`_index/snapshots/pre_v9_canonical_2026_06_0X.parquet`. G3. `--apply` (additive copy only — non-destructive, safe to
re-run; idempotent). G4. E5 manifest rebuild → v9 `_index`. G5. **CF-1…CF-12 GREEN** on real data-state:
`cf_manifest_audit_2026_06_01.py <canonical-bucket>`. G6. **Completeness COUNT gate**: canonical distinct-cells ≥ UNION
of every source layout's distinct cells. G7. **Strategically-sampled cross-shard verify**: sample (date × venue ×
data_type × EACH layout); per sample confirm canonical object exists + content matches legacy + manifest row v9-correct.
G8. **Fleet drain** (GCP+AWS, shared w/ slot-2; epic mtds_mdps_master coordinates).

### THE REAL MIGRATION + DELETION (only after G1–G8 GREEN per AG)

- Perf: I/O-bound (not CPU). `--workers 96`; **date-shard cefi across ~4–6 VMs** via `--start-date`/`--end-date`
  (sub-hour); prediction 1–2 VMs; tradfi after build. Server-side `gcs_copy_object` for path-only (bulk) = no egress.
- **DELETE = END-ONLY, NEVER inline** (lesson #11): after G5–G8 GREEN, bulk-delete legacy buckets + superseded in-bucket
  paths (prediction `category=`, cefi `day=/asset_group=` lacking `pipeline_mode=`) → hand to `bucket_name_ssot…` L6.
  Prediction `--drop-stale` only after Source B verified. ONE pass, no rollback.
- DONE = every (cefi/tradfi/prediction × CF-1…CF-12) GREEN on real data-state + legacy deleted = single SSOT.
