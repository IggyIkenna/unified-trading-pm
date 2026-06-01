---
title: "Consolidated CF-1…CF-12 data-state audit results — slot-4 surfaces (cefi/tradfi/sports/prediction + instruments + downstream)"
created: 2026-06-01
author: ikenna (slot-4)
source:
  - plans/audit/results/cf_manifest_audit_2026_06_01.py (the reusable tool that produced these)
  - canonical_form_cross_service_audit_checklist.md (CF-1…CF-12 SSOT)
master: defi_manifest_canonicalisation_2026_06_01.md
---

# Consolidated CF data-state audit — slot-4 surfaces (2026-06-01)

Read with `cf_manifest_audit_2026_06_01.py` against the **actual** prod `_index` rows (never the
`MANIFEST_SCHEMA_VERSION` constant — the manifest-v8 lesson). This is the audit-first P0 result for
all six slot-4 plans. **defi = slot-2** (not audited here).

## The systemic finding (uniform across the ENTIRE non-defi corpus)

Every canonical MTDS-AG `_index` **and** every instruments-store `_index` audited shows the **same**
canonical-form debt — the v9 canonicalisation was only ever a **constant bump**, never applied to data:

| CF | invariant | data-state across ALL surfaces |
| -- | --------- | ------------------------------ |
| CF-1 | schema_version = v9 | **RED — 100% v8** on every surface (0 rows v9) |
| CF-3 | pipeline_mode partition/column | **RED — column blank/absent**, no `pipeline_mode=` path segment anywhere |
| CF-4 | `source` COLUMN | **RED — column ABSENT** on every surface (prediction/sports also have `data_source=` in PATH) |
| CF-8 | `available_at` per-row | **RED — column ABSENT** on every surface (only `written_at` write-time proxy) |
| CF-2 | `asset_group=` not `category=` | rows: tradfi/pred/defi have `asset_group` col; cefi/sports vacuous (no col). PATHS: prediction still `category=`; cefi/tradfi/sports have no AG segment (flat / partial-hive) — **RED on paths** |
| CF-5 | typed empty reason | GREEN everywhere EXCEPT **sports = RED-by-mislabel** (584,177 empties blanket-labeled `SOURCE_RETURNED_ZERO` on a schedule-driven AG → must become typed fixture/season/window reasons) |
| CF-7 | canonical names | mostly clean; drift to relabel: `UNKNOWN`+blank venues (tradfi/pred), `COINBASE`vs`COINBASE-SPOT` (cefi), ODDS case-drift (sports `ODDS`/`ODDS_SNAPSHOT` upper vs `odds_horizon_bucket` lower), blank `data_type` (instruments-store cells) |
| CF-9 | env-split bucket | GREEN (all canonical buckets are `-prd-`) |

So per the **"Audit scope is a PRIOR, not a ceiling"** HARD RULE every AG walk is a **whole-corpus
content rewrite** (download+transform+upload to add the source/asset_group/pipeline_mode/available_at
columns + re-version v9 + re-partition paths), not the headline cell-count gap-fill.

## Per-surface detail

### MTDS (raw tick + MDPS candles share one `_index`)

| AG | canonical `_index` rows | capture_status split | legacy-only cells (headline → ACTUAL) | object-path scheme |
| -- | ----------------------- | -------------------- | ------------------------------------- | ------------------ |
| cefi | 2,640,864 | failed 1,330,271 / captured 1,310,443 / empty 150 | **838 → 5,233** (2020-01 OKX-FUTURES book_snapshot_5 …) | `raw_tick_data/by_date/{SYMBOL}.parquet` (FLAT, no hive) + `processed_candles/by_date/day=/timeframe=/data_type=/venue=` (hive, no AG/pm) |
| tradfi | 144,062 | captured 100,536 / empty 37,490 / failed 6,036 | **4 → 71** (2023-05 NYSE tbbo …) | (probe hit `configs/`; raw needs targeted check — no AG/pm partition) |
| sports | 786,408 | **empty 584,177** / captured 202,067 / failed 164 | **0** (data complete) | `processed/by_date/day=/data_type=/league_id=/timeframe=` (hive, no AG/pm); `data_source=` elsewhere |
| prediction | 16,812 | captured 14,491 / empty 2,321 | 2,039 (confirmed) | `raw_tick_data/by_date/day=/category=prediction/data_source=POLYMARKET_CLOB/venue=` (has `category=` + `data_source=` in path) |

- tradfi empty-reasons (already typed): `EXPECTED_WEEKEND` 35,050 · `EXPECTED_HOLIDAY` 2,427 · `EXPECTED_OUT_OF_COVERAGE_WINDOW` 8 · `SOURCE_RETURNED_ZERO` 5.
- sports empty-reasons: **`SOURCE_RETURNED_ZERO` × 584,177** (the keystone mislabel — relabel via the UAC coverage oracle).
- cefi `attempted_failed` is **50%** of rows (1.33M) — a separate coverage/health concern (E1-class fetch failures), surfaced for the AG owners; not a canonicalisation blocker.

### instruments-store (input/reference surface)

| bucket | rows | CF-1 | legacy-only |
| ------ | ---- | ---- | ----------- |
| instruments-store-cefi-prd | 30,803 | v8 | 23 (2025-10, blank data_type) |
| instruments-store-tradfi-prd | 20,264 | v8 | 60 (2026-03, blank data_type) |
| instruments-store-pred-prd | 493 | v8 (no pipeline_mode col) | (legacy long-form name — re-diff in walk) |

All: no source col · blank/absent pipeline_mode · no available_at · flat paths · **blank `data_type`**
on cells (keyed date+venue — verify intent). cefi/defi/tradfi/pred/sports each have an AG-partitioned `_index`.

### downstream services (low-data — confirmed)

- **MDPS** candles ride the AG MTDS `_index` (same bucket `processed_candles/`) → covered by each AG walk, **no separate walk**.
- **features / strategy / execution** for cefi/tradfi/sports/prediction: **NO `_index`** (no data run — `features-delta-one/mtf/volatility/calendar`, `strategy-store-*`, `execution-store-*` all absent). Lever = **writer-fix-first** (born-canonical) + re-audit when input C-GREEN + first batch runs. (Only `features-onchain-defi-prd` has an index = slot-2.)

## What each AG walk must do (bundled, single-walk, per the perf contract)

1. **Whole-corpus column rewrite** on the canonical bucket: `schema_version→9`; add `source` (from path `data_source=` / UAC SOURCE_PRIORITY); add/populate `pipeline_mode`; add `available_at` (preserve from parquet where present, else day-EOD-UTC backfill — never migration-time); add `asset_group` column where absent (cefi/sports).
2. **Path re-partition**: emit `asset_group={ag}` + `pipeline_mode={mode}` hive segments; for prediction also drop `category=` + lift `data_source=` → `source` column; for cefi derive `day=`/`venue=` from columns (flat `by_date/{symbol}` source layout).
3. **Legacy-only gap copy**: cefi 5,233 · tradfi 71 · prediction 2,039 · instruments cefi 23 / tradfi 60 (sports 0).
4. **sports keystone**: relabel 584,177 `SOURCE_RETURNED_ZERO` → typed fixture/season/transfer-window/genesis via the UAC coverage oracle.
5. **CF-7 relabel**: `UNKNOWN`/blank venues, `COINBASE`↔`COINBASE-SPOT`, sports ODDS case-drift, instruments blank data_type.
6. Re-consolidate the `_index` from rewritten data (data-state v9 verified, not the constant) → verify → hand C-GREEN to `bucket_name_ssot…` L6.

## Execution constraint (why the walks are VM-only, not local)

Local gcsfs/aiodns DNS is flaky on this host (the audit tool works around it with `gcloud cp` for the single
index parquet + a time-boxed shallow object probe). A whole-corpus content rewrite (millions of objects per AG)
**must run on a VM in asia-northeast1** per `codex/05-infrastructure/gcs-object-operations.md` § Migration-script
performance contract (ThreadPoolExecutor parallel walk, wired `--workers`/`--start`/`--end` date-sharding,
`gcs_copy_object` for path-only moves, unbuffered progress, per-object isolation, idempotent). The `--apply`
cutover is additionally gated on the **fleet-wide pre-migration drain** (stop GCP+AWS writers → consolidate →
snapshot each `_index`), which is shared with slot-2's defi walk and coordinated at epic `mtds_mdps_master`.
**Dry-run is read-only and needs no drain.**

## MECHANISM FINDING (system-first, 2026-06-01) — the `_index` columns come from the WRITER, not the data parquets

A direct probe of a cefi raw parquet (`raw_tick_data/by_date/AVAXUSDT.parquet`, 122,179 rows) shows it carries
**pure market data** (`exchange, symbol, timestamp, funding_rate, last_price, mark_price, …, data_type, instrument_id`)
— **NOT** the manifest columns. So `schema_version` / `source` / `pipeline_mode` / `asset_group` / `available_at` are
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
  map. So `source` population REQUIRES the object-path scan (not derivable from the `_index` alone for multi-source AGs).

## CROSS-AG LESSON from slot-2's live DeFi migration (operator 2026-06-01) — audit ALL layouts before migrating

Slot-2's DeFi C0 run surfaced that a source bucket can hold **multiple overlapping legacy layouts** that a naive
day-prefix walk silently under-migrates. DeFi `dex-pools` had THREE: (1) `day=/category=defi/venue=…` flat-legacy
(~19K), (2) `raw_tick_data/by_date/day=/asset_group=defi/venue=/chain=/…/data_type=…` near-canonical (the bulk, missing
`pipeline_mode=`), (3) `dex_pools/{venue}/{chain}/date=…` older (bare segments, `date=` not `day=`, no asset_group →
the path parser skipped it). The day-prefix run migrated only #1 and would have left a **partial canonical set + data
loss on legacy delete** — the exact failure this programme exists to end.

**Operator directive (applies to EVERY slot-4 AG walk)**: the script must **audit all source layouts, determine overlap
vs complementary, pick the freshest/best schema where they overlap, land EVERYTHING on the one v9 manifest + data
schema, and only run the real migration once we're genuinely on v9 — "because we keep missing things."** Net end-state:
**old buckets + old paths all deleted → ONE source of truth** so data-status/manifest shows true missing-data. So
**Phase 0 (layout audit) is mandatory and blocking** before any AG walk — never assume a single layout from a sample.

## Grounded per-AG walk recipe (the build, system-first on existing MTDS tools)

**Phase 0 — layout audit per bucket (MANDATORY, blocking; the slot-2 DeFi lesson)**: enumerate ALL top-level trees +
nested layouts in each source/canonical bucket (`day=/category=`, `raw_tick_data/by_date/…`, bare `{venue}/{chain}/date=`,
`processed/`, `processed_candles/`, `sports_reference/`, …). For each: count objects, read a sample schema, determine
which layouts are **duplicates** (→ keep the freshest/most-canonical, discard the rest) vs **complementary** (→ migrate
all, mapping each to the canonical v9 form). Output a per-bucket layout manifest. The walk must cover EVERY in-scope
layout or it is incomplete — review-blocking.

Then, per AG, ONE bundled VM walk (single-walk discipline), built by generalising the proven tools:

1. **Object-path re-partition + legacy-gap copy** — extend the per-AG layout tool (`migrate_{sports,tradfi,polymarket}_canonical.py`
   exist; cefi needs one) to emit the canonical `…/day=/pipeline_mode={mode}/asset_group={ag}/…` layout and `gcs_copy_object`
   the legacy-only objects (cefi 5,233 · tradfi 71 · prediction 2,039 · instruments cefi 23 / tradfi 60) into canonical paths.
   ThreadPoolExecutor + wired `--workers`/`--start`/`--end` + idempotent (perf contract).
2. **Manifest rebuild → v9** — generalise `rebuild_prediction_manifest.py` to `rebuild_{ag}_manifest_v9.py`: scan the
   canonical paths, `ManifestWriter.add/record_empty` with `pipeline_mode` + `source` (from path `data_source=` / UAC
   SOURCE_PRIORITY) → consolidator merge → `_index` becomes v9 + canonical columns + `available_at`.
3. **sports keystone (CF-5)** — relabel the 584,177 `SOURCE_RETURNED_ZERO` empties to typed fixture/season/transfer-window
   reasons via the UAC coverage oracle at rebuild time (`record_empty(reason=…)`), driven by `clip_dates_to_source_coverage`
   / `is_in_known_gap` / `league_data`.
4. **CF-7 relabel** — `UNKNOWN`/blank venue, `COINBASE`↔`COINBASE-SPOT`, sports ODDS case-drift, instruments blank data_type.
5. **Verify** — re-run `cf_manifest_audit_2026_06_01.py` → all CF GREEN on data-state → hand C-GREEN to `bucket_name_ssot…` L6.

Execution: VM in asia-northeast1 (object scan is ~25 min/AG for prediction-scale, more for cefi), `--apply` gated on the
fleet drain. DeFi is slot-2's lane (the defi v9 tool + its dedicated-bucket shape) — not in slot-4 scope.

## Phase-0 LAYOUT audit results (tool `cf_layout_audit_2026_06_01.py`, 2026-06-01)

Confirms the multi-layout reality — each AG bucket has ≥2 distinct layouts that the migrator MUST all handle/reconcile:

- **cefi** (prd AND legacy, identical layout set):
  - `raw_tick_data/by_date/{SYMBOL}.parquet` — **FULLY FLAT**, no hive at all. day/venue/data_type live ONLY in the
    parquet columns (`exchange, symbol, timestamp[epoch-micros], data_type, instrument_id, funding_rate, …`). The
    migrator must derive day (from epoch-micros `timestamp`), venue (from `exchange`/`symbol`), data_type (column) per
    row and re-partition to canonical hive — possibly **fanning out one flat symbol-file into many day= partitions**
    (122,179 rows × 94,048 distinct timestamps in one AVAXUSDT file). Hardest AG.
  - `processed_candles/by_date/day=/timeframe=/data_type=/venue=` (MDPS candles) — has `day=` but no `asset_group=`/`pipeline_mode=`.
- **prediction** — **legacy and canonical layouts are INVERTED** (needs reconciliation, not blind copy):
  - legacy raw: `raw_tick_data/by_date/day=/asset_group=/venue=/instrument_type=/data_type=` (near-canonical — already
    has `asset_group=`; rich parquet cols incl `asset_group, data_source, chain, underlying`).
  - canonical pred-prd raw (from the CF audit): `…/day=/category=/data_source=/venue=/…` (has `category=` + `data_source=`
    — LESS canonical than legacy on the AG key). So "pick the freshest schema" here = the **legacy** asset_group= layout
    is closer to target; the migrator must converge both onto `day=/asset_group=/pipeline_mode=/…`.
  - `processed_candles/by_date/day=/timeframe=/data_type=/venue=` (candles).
- **(tradfi / sports / instruments)**: run `cf_layout_audit_2026_06_01.py` on each before its walk (Phase 0). Expect the
  same shape — a raw tree (flat or partial-hive) + processed_candles + possibly an older bare-segment tree.

**Design consequence**: the migrator is genuinely **layout-dispatching** — per object it must detect its source layout
and map to the single canonical `day=/pipeline_mode=/asset_group=/venue=/chain=/instrument_type=/data_type=` target,
deriving missing dims from parquet columns (cefi flat), reconciling inverted schemes (prediction), and deduping any
overlap to the freshest. Then the `ManifestWriter` rebuild stamps v9 + source + pipeline_mode + available_at. This is
why the operator gated it on "only once we're on v9, no more missing things" — the Phase-0 audit per AG is the guard.
