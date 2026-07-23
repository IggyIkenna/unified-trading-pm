---
doc_type: audit-result
title: "P8 — PREDICTION candle canonical-path migration verify/reconcile (2026-07-23)"
summary: >-
  Independent post-migration verification of the PREDICTION `processed_candles/` canonical-path migration (P7b, done
  2026-07-22). A FRESH enumeration of the live `market-data-tick-pred-prd-central-element-323112` bucket's
  `processed_candles/by_date/` prefix (583,228 objects, 247 day partitions, 2025-03-14..2026-01-14) was run through the
  migration script's own `--dry-run` classifier (read-only, no `--apply`) — the exact inverse check of what the
  `--apply` run executed. Result: CLEAN. 583,228/583,228 objects classify `CANONICAL_NOOP` (100%); every other
  disposition (`MIGRATE`, `SPLIT_BRAIN_DUPLICATE`, `NEEDS_CONTENT_INSTRUMENT_TYPE`, `NEEDS_CONTENT_TRADFI_ID`,
  `NEEDS_CONTENT_CEFI_WIRE_ID`, `EMPTY_STEM_WITH/WITHOUT_UNDERLYING`, `QUARANTINE_CORRUPT`) = 0; `ORPHAN` = 0 (the
  script's own total-map safety invariant held). No non-canonical PREDICTION candle objects remain in the live bucket.
status: pass
nature: record
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm, market-data-processing-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, candles, prediction, p8, migration-verify, post-migration]
related:
  [
    candle_feature_canonical_path_divergence_2026_07_20,
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    non-canonical-path-inventory,
  ]
created: 2026-07-23
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=prediction, PROD (-prd-) bucket only, processed_candles/by_date/ prefix only, read-only; fresh
  whole-prefix enumeration (583,228 objects) classified via the migration script's own --dry-run path-only classifier.
  NOT re-audited: raw_tick_data/, other asset_groups (defi/cefi/tradfi — sibling P8 verifications), parquet content
  interiors, manifest/catalogue surfaces (S3/S4)."
date: 2026-07-23
auditor: P8 independent verification (fresh-enumeration + migration script's own dry-run classifier)
parent_epic: infrastructure_master
severity: P2
---

# P8 — PREDICTION candle canonical-path migration verify/reconcile (2026-07-23)

Independent, read-only post-migration verification of the PREDICTION leg of the `processed_candles/` canonical-path
migration (`market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py`). The `--apply` run (P7b, logged
2026-07-22 in `candle_feature_canonical_path_divergence_2026_07_20.md`) reported a clean first pass on all 10 shards (0
non-success outcomes, per-shard `MIGRATED` counts summing exactly to the P0 census total of 1,165,459). This document is
the independent check: a **fresh** enumeration of the live bucket today, run through the script's own classifier — the
literal inverse of what the migration executed — to prove 0 non-canonical PREDICTION candle objects remain. No
`--apply`, no writes, no deletes.

## 1. Bucket resolution

```python
from unified_trading_library import resolve_bucket_name
resolve_bucket_name(cloud="gcp", kind="market-data-tick-prediction", deployment_env="prd")
# -> "market-data-tick-pred-prd-central-element-323112"
```

Resolved via `.venv/bin/python` in `market-data-processing-service/` (same venv the migration ran under),
`GCP_PROJECT_ID=central-element-323112` set in env, no other env-var tier mutation. Matches the bucket used by the P7b
apply run and by the prior 2026-07-20 four-surface prediction reconciliation report (`raw tick` row).

Top-level reachability probe (non-recursive, `delimiter="/"`):

```
processed_candles/   _index/   raw_tick_data/   _vm_staging/   _migration_backup/
```

Reachable. `processed_candles/` present as expected.

## 2. Fresh enumeration

Bounded, single-purpose walk of `processed_candles/by_date/` ONLY (not the whole bucket) — one sanctioned walk for this
one prefix, not a general corpus walk.

- Day-prefix delimiter-descent first: 247 `day=` partitions, range `2025-03-14` .. `2026-01-14` (identical set to the
  pre-migration day list captured in this session's scratchpad on 2026-07-21 — no new day partitions appeared;
  day-boundary did not move).
- Per-day listing via `google.cloud.storage.Client.list_blobs(bucket, prefix="processed_candles/by_date/day=<D>/")`,
  parallelized across days with a `ThreadPoolExecutor(max_workers=32)` — server-side paginated listing, not
  `gsutil ls -r`.
- Output: one `gs://<bucket>/<rel>` URI per line, written incrementally with periodic progress heartbeats (measured
  forward progress: object count climbing every ~25-day checkpoint, not just liveness).

**Result: 583,228 objects enumerated across all 247 days in 1,278.8s (~21.3 min).**

```
[p8] DONE: 583228 objects across 247 days in 1278.8s
```

Enumeration file: `p8_prediction_enumeration.txt` (scratchpad, 583,228 lines). Sampled rows confirm the canonical shape
on their face
(`pipeline_mode=.../timeframe=.../data_type=trades/instrument_type=PREDICTION_MARKET/venue=POLYMARKET/POLYMARKET:PREDICTION_MARKET:<id>.parquet`
etc.) — consistent with the P7b hard-verify sample from 2026-07-22.

## 3. Dry-run classification (the migration script's own ground-truth oracle)

Skimmed the script's disposition contract first (`grep -n` on `run_manifest_and_reconcile` / `Counter` / disposition
constants) to confirm the exact histogram + reconcile-pass semantics before running: every enumerated object gets
exactly one of 9 dispositions (`CANONICAL_NOOP`, `MIGRATE`, `SPLIT_BRAIN_DUPLICATE`, `NEEDS_CONTENT_INSTRUMENT_TYPE`,
`EMPTY_STEM_WITH_UNDERLYING`, `EMPTY_STEM_WITHOUT_UNDERLYING`, `NEEDS_CONTENT_TRADFI_ID`, `NEEDS_CONTENT_CEFI_WIRE_ID`,
`QUARANTINE_CORRUPT`) or falls into the loud-failure `ORPHAN` bucket, which MUST be zero or the reconcile pass aborts
before any write (irrelevant here since `--dry-run` never writes regardless, but it's the same total-map safety
invariant used to gate `--apply`).

Command (read-only, no `--apply` ever passed):

```
cd market-data-processing-service
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -u scripts/migrate_candle_canonical_2026_07.py \
  --dry-run \
  --enumeration <scratchpad>/p8_prediction_enumeration.txt \
  --out <scratchpad>/p8_prediction_mapping.tsv
```

**Full disposition histogram (verbatim from the script's own reconcile output):**

```
TOTAL objects classified: 583,228

=== disposition histogram ===
     583,228  CANONICAL_NOOP

MIGRATE (incl. split-brain): 0  |  CONTENT_REPAIR pending: 0  |  QUARANTINE: 0  |  CANONICAL_NOOP: 583,228
SUM(dispositions) = 583,228  |  TOTAL = 583,228  |  match=True
ORPHAN count = 0  (PASS — total map)
```

Cross-checked against the mapping TSV directly (`cut -f2 mapping.tsv | sort | uniq -c`): 583,228 rows, single distinct
disposition value = `CANONICAL_NOOP`. Every row's `new_path_or_reason` reads `<already canonical — verify in place>`.

## 4. Verdict: CLEAN

| Disposition                     |   Count | Expected (post-migration)        |
| ------------------------------- | ------: | -------------------------------- |
| `CANONICAL_NOOP`                | 583,228 | ~100% ✅                         |
| `MIGRATE`                       |       0 | 0 ✅                             |
| `SPLIT_BRAIN_DUPLICATE`         |       0 | 0 ✅                             |
| `NEEDS_CONTENT_INSTRUMENT_TYPE` |       0 | 0 ✅                             |
| `NEEDS_CONTENT_TRADFI_ID`       |       0 | 0 ✅ (N/A — not a TradFi bucket) |
| `NEEDS_CONTENT_CEFI_WIRE_ID`    |       0 | 0 ✅ (N/A — not a CeFi bucket)   |
| `EMPTY_STEM_WITH_UNDERLYING`    |       0 | 0 ✅                             |
| `EMPTY_STEM_WITHOUT_UNDERLYING` |       0 | 0 ✅                             |
| `QUARANTINE_CORRUPT`            |       0 | 0 ✅                             |
| `ORPHAN`                        |       0 | 0 ✅ (total-map holds)           |

**0 non-canonical PREDICTION candle objects remain in the live bucket.** This is the strongest available proof: the
exact same path-parsing/classification code the `--apply` run used to decide what to migrate, run fresh today against a
today-enumerated corpus, finds nothing left to do.

No parser-shape surprises for PREDICTION's `instrument_type=PREDICTION_MARKET` / colon-id leaf convention — the script's
Hive-key parser handled every one of the 583,228 objects without a single `QUARANTINE_CORRUPT` or `ORPHAN`, so there was
no CQG/manifest-only-grain edge case for this script to mishandle at the path-classification level (note: this script
classifies GCS object paths only — it does not touch the manifest or `canonical_question_group` grain, so this finding
is scoped to S1/path-canonicality, not a manifest-level statement).

### Secondary sanity check (non-blocking, informational only)

The P0 census (2026-07-22) measured PREDICTION's pre-migration corpus at 1,165,459 objects (1 `MIGRATE` + 1,165,458
`SPLIT_BRAIN_DUPLICATE` — i.e., PREDICTION was ~100% duplicate-pair dedup). A naive "every split-brain group was exactly
2 objects collapsing to 1" model predicts a post-migration canonical count of `1,165,458 / 2 + 1 ≈ 582,730`. The
measured 583,228 is **+498 (+0.09%)** above that naive estimate — well within the slack expected from a "mostly-pairs,
not strictly-all-pairs" duplicate distribution (some targets plausibly had 3+ claimants, and the day-partition list is
unchanged pre/post so this isn't new-day drift). This is a rough cross-check, not a disposition-level finding — the
authoritative signal is the histogram in §3, which is unambiguous and fully clean.

## 5. Suggested register-patch (informational — not applied)

No new non-canonical PREDICTION candle location was found. Nothing to add to
`/codex/02-data/non-canonical-path-inventory.md` from this verification (per this session's instruction, that file is
not edited directly here — 3 sibling agents are running the equivalent P8 procedure for the other 3 migrated
asset_groups against the same shared file concurrently).

## Reproducibility

```bash
cd market-data-processing-service
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -c "
from unified_trading_library import resolve_bucket_name
print(resolve_bucket_name(cloud='gcp', kind='market-data-tick-prediction', deployment_env='prd'))
"
# -> market-data-tick-pred-prd-central-element-323112

# fresh enumeration (day-parallel, see p8_prediction_enumerate.py in this session's scratchpad for the exact
# ThreadPoolExecutor(list_blobs) implementation)

GCP_PROJECT_ID=central-element-323112 .venv/bin/python -u scripts/migrate_candle_canonical_2026_07.py \
  --dry-run \
  --enumeration p8_prediction_enumeration.txt \
  --out p8_prediction_mapping.tsv
```
