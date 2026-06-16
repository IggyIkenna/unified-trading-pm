---
type: analysis
title: pipeline_mode backfill verification — pre-backfill state (2026-05-28)
epic: mtds_mdps_master
auditor: claude + operator
date: "2026-05-28"
status: complete
---

# pipeline_mode backfill verification — pre-backfill state (2026-05-28)

**Verification date**: 2026-05-28  
**Verifier**: Worker Slot 10 (sub-a-ikenna)  
**Plan**: `pipeline_mode_implementation_2026_05_28.md` Phase 3.3  
**Status**: PRE-BACKFILL — backfill (Phase 3.2) NOT YET RUN on prd buckets

GCS project: `central-element-323112`

---

## Summary

| Metric                               | Count                          |
| ------------------------------------ | ------------------------------ |
| Total rows checked                   | 49,372,930                     |
| Rows with valid `pipeline_mode`      | 41,301,411 (83.7%)             |
| Rows with NULL/empty `pipeline_mode` | 8,071,519 (16.3%)              |
| Buckets PASS                         | 8                              |
| Buckets NEEDS_BACKFILL               | 11                             |
| Buckets NO_INDEX (no manifest)       | 12 features-delta-one-\*       |
| Buckets NO_COLUMN                    | 1 (instruments-store-pred-prd) |

**Verdict**: FAIL — pre-backfill. 8M rows across 11 prd buckets need backfill.

---

## Per-bucket results

| Bucket (short)                     | Status         | Total      | NULL      | Valid      |
| ---------------------------------- | -------------- | ---------- | --------- | ---------- |
| market-data-tick-cefi              | PASS           | 35,829,048 | 0         | 35,829,048 |
| market-data-tick-cefi-prd          | NEEDS_BACKFILL | 2,632,931  | 2,632,931 | 0          |
| market-data-tick-defi              | NEEDS_BACKFILL | 1,787,797  | 287       | 1,787,510  |
| market-data-tick-defi-prd          | NEEDS_BACKFILL | 1,633,780  | 1,633,780 | 0          |
| market-data-tick-tradfi            | PASS           | 355,566    | 0         | 355,566    |
| market-data-tick-tradfi-prd        | NEEDS_BACKFILL | 144,062    | 144,062   | 0          |
| market-data-tick-sports            | PASS           | 164,597    | 0         | 164,597    |
| market-data-tick-sports-prd        | NEEDS_BACKFILL | 786,408    | 786,408   | 0          |
| market-data-tick-pred-prd          | NEEDS_BACKFILL | 16,812     | 16,812    | 0          |
| market-data-tick-prediction        | NEEDS_BACKFILL | 357,463    | 128       | 357,335    |
| instruments-store-cefi             | PASS           | 30,449     | 0         | 30,449     |
| instruments-store-cefi-prd         | NEEDS_BACKFILL | 30,803     | 30,803    | 0          |
| instruments-store-defi             | PASS           | 68,885     | 0         | 68,885     |
| instruments-store-defi-prd         | NEEDS_BACKFILL | 125,242    | 125,242   | 0          |
| instruments-store-sports           | PASS           | 2,694,638  | 0         | 2,694,638  |
| instruments-store-sports-prd       | NEEDS_BACKFILL | 2,680,309  | 2,680,309 | 0          |
| instruments-store-tradfi           | PASS           | 11,439     | 0         | 11,439     |
| instruments-store-tradfi-prd       | NEEDS_BACKFILL | 20,264     | 20,264    | 0          |
| instruments-store-pred-prd         | NO_COLUMN      | 493        | 493       | 0          |
| instruments-store-prediction       | PASS           | 1,944      | 0         | 1,944      |
| features-delta-one-\* (12 buckets) | NO_INDEX       | 0          | —         | —          |

---

## Findings

### 1. Bucket naming bug in backfill script (FIXED)

The original `backfill_pipeline_mode.py` used `raw-tick-data-*` templates, but production buckets use
`market-data-tick-*`. Script updated in this commit to fix the templates (adds both prd and legacy variants).

### 2. Legacy buckets already PASS

All 8 legacy (non-`-prd-`) buckets have `pipeline_mode` fully populated — already `batch_tardis` or
`batch_hyperliquid_rest`. The Phase 1B rollout that wrote pipeline_mode was apparently applied to legacy buckets but NOT
to the env-tiered prd buckets.

### 3. Prd buckets all NEEDS_BACKFILL

All `-prd-` suffixed buckets have 100% NULL rows. The env-tiered buckets were created after the Phase 1B rollout
completed on legacy, so they received rows without `pipeline_mode` populated.

### 4. instruments-store-pred-prd: NO_COLUMN

493 rows in the prediction instruments-store-prd bucket have no `pipeline_mode` column at all (pre-v8 schema). The
backfill script will add the column and derive values.

### 5. market-data-tick-defi and prediction: small residual NULLs

- `market-data-tick-defi`: 287/1,787,797 NULL (0.016%)
- `market-data-tick-prediction`: 128/357,463 NULL (0.036%) These are minor residuals from pre-backfill row writes;
  already covered by the backfill pass.

---

## Operator action required (Phase 3.2)

The backfill has NOT been run. Run the now-corrected script against prd buckets:

```bash
# Dry-run first for a bucket:
python scripts/migration/backfill_pipeline_mode.py \
  --verify --bucket market-data-tick-cefi-prd-central-element-323112 --asset-group cefi

# Apply to all prd buckets (needs write credentials):
python scripts/migration/backfill_pipeline_mode.py \
  --apply --all --project-id central-element-323112
```

After the backfill run, re-run this verification. Target: all buckets PASS (0 NULL rows).

---

## Per-VM shards note

Verification above covers only `_index/availability_index.parquet`. Per-VM shards under `_index/per_vm/` also need
verification — not checked here. The backfill script's `--all` mode does NOT currently handle per-VM shards (only the
consolidated index). A per-VM shard pass should be added as a follow-up OR included in the main backfill run when
`--apply` is used.
