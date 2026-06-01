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
