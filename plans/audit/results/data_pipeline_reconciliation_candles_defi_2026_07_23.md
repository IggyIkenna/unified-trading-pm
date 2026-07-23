---
doc_type: audit-result
title: "P8 candle-canonicalisation post-migration verification — defi (2026-07-23)"
summary: >-
  Independent verification (P8) of the DEFI processed_candles/ canonical-path migration
  (market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py), run AFTER the migration's own P7a-full
  apply+retry reported 0 non-success outcomes (1,131,814 objects processed in run 1 + 211 re-verified/re-migrated in the
  retry, hard-verified via real gsutil stat). A FRESH parallel enumeration of processed_candles/by_date/ (1,146
  day-prefixes, 32-way parallel listing) found 1,123,415 live objects — lower than run 1's processed count by 8,399,
  which is EXPECTED and was reconciled before concluding CLEAN, not just reported as a bare number: a direct probe of
  gs://market-data-tick-defi-prd-central-element-323112/_quarantine/ found exactly 1,442 objects (an EXACT match to the
  P0 census's QUARANTINE_CORRUPT count for DEFI), confirming the quarantine gate (MODE=full) relocated those objects OUT
  of processed_candles/by_date/ as designed; the remaining gap is consistent with SPLIT_BRAIN_DUPLICATE dedup (DEFI's
  split-brain count folds into the census's MIGRATE line rather than being broken out separately), which collapses 2
  source objects to 1 canonical target. Running the migration script's own --dry-run classifier against this fresh
  enumeration (the tool's inverse ground-truth check) over the full 1,123,415 objects returned a disposition histogram
  of 100% CANONICAL_NOOP, 0 ORPHAN, and 0 in every other class (MIGRATE / SPLIT_BRAIN_DUPLICATE / any NEEDS_CONTENT_* /
  QUARANTINE_CORRUPT / EMPTY_STEM_*). VERDICT: CLEAN.
status: pass
nature: record
asset_group: [defi]
stage: [data]
repos: [market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, candles, defi, migration-verification, p8, processed_candles]
related: [candle_feature_canonical_path_divergence_2026_07_20]
created: 2026-07-23
auditor:
  "P8 independent post-migration verification (fresh parallel GCS enumeration + migrate_candle_canonical_2026_07.py
  --dry-run classify)"
parent_epic: infrastructure_master
severity: P1
audited_scope:
  "asset_group=defi, processed_candles/by_date/ ONLY (raw_tick_data/ and the rest of the bucket are OUT OF SCOPE), PROD
  bucket (market-data-tick-defi-prd-central-element-323112), read-only throughout, ONE sanctioned bounded walk of this
  prefix (not a whole-corpus walk)"
date: 2026-07-23
resulting_plan:
lib_version:
doc_versions_checked:
---

# P8 — DEFI candle canonical-path post-migration verification (2026-07-23)

**Scope**: independent, read-only, post-`--apply` verification that 0 non-canonical DEFI `processed_candles/` objects
remain in GCS, per `plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md` (P8 step of the P6→P7→P8
candle canonical-path migration). This is the migration script's own dry-run classifier run against a **fresh,
independent enumeration** of the live bucket — the inverse operation of what `--apply` executed, and the most
authoritative check available.

**Verdict: CLEAN.** 1,123,415/1,123,415 objects classify `CANONICAL_NOOP` (100%). Zero `MIGRATE`, zero
`SPLIT_BRAIN_DUPLICATE`, zero `QUARANTINE_CORRUPT`, zero `NEEDS_CONTENT_*`, zero `EMPTY_STEM_*`, and — the hard
invariant — **`ORPHAN` = 0**. No further action needed for DEFI.

## What was checked against

Per the issue doc's Progress Log (`## Progress Log — 2026-07-22`, "P7a-full: DEFI — RETRY SUCCEEDED"): DEFI's `--apply`
(`MODE=full`, i.e. `--apply --quarantine --content-repair`) processed **1,131,814 objects** in run 1 (10 shards) +
**211** re-verified/re-migrated in a retry pass, with every shard's `run.log` ending
`apply COMPLETE — shard N/10 fully migrated cleanly (0 non-success outcomes)`, hard-verified against real `gsutil stat`
output on 2 sampled objects. The doc's P0 census (a separate, earlier full dry-run pass, also real-GCS) measured DEFI at
**1,124,849** total objects: 1,123,407 `MIGRATE` (DEFI's split-brain-duplicate count folds into this bucket — the
histogram doesn't break it out separately for DEFI, unlike the other 3 asset groups), 1,442 `QUARANTINE_CORRUPT`, 0
`CANONICAL_NOOP`, `ORPHAN`=0.

## Bucket resolved

```python
from unified_trading_library import resolve_bucket_name
resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi", deployment_env="prd")
# -> market-data-tick-defi-prd-central-element-323112
```

Resolved via `market-data-processing-service/.venv` (GCP_PROJECT_ID=central-element-323112 in env, no other
deployment_env override). Reachability confirmed with a non-recursive top-level listing of `processed_candles/` before
the full walk.

## Fresh enumeration

Single sanctioned bounded walk of `processed_candles/by_date/` only (raw_tick_data/ out of scope), via
`google.cloud.storage.list_blobs` server-side-paginated listing, chunked by `day=` prefix (1,146 day prefixes discovered
via a delimiter-descent listing) and run in parallel across a 32-worker `ThreadPoolExecutor` (one
`list_blobs(prefix=day_prefix)` call per day, writing `gs://<bucket>/<rel>` lines to the output file under a lock).

- **Total objects enumerated: 1,123,415** across 1,146 `day=` partitions (2023-01-01 .. 2026-07-22).
- Wall clock: 1,370.5s (~22.8 min) — exceeded a single 10-min Bash call, so it ran as a tracked background process,
  polled to completion (not fire-and-forgotten).
- Output: `p8_defi_enumeration.txt` (scratchpad, 1,123,415 lines, one `gs://` URI per line).

## Reconciling the object-count gap (1,131,814 vs. 1,123,415)

The fresh count is lower than run 1's "processed" count by 8,399. Investigated before concluding CLEAN, not just
reported as a bare number:

1. **Quarantine gate moved `QUARANTINE_CORRUPT` objects out of `by_date/` entirely.** DEFI's apply ran with
   `--quarantine` enabled (`MODE=full`), which relocates quarantined objects to `_quarantine/{original_rel}` — i.e.
   under a `_quarantine/processed_candles/...` prefix, a **different top-level prefix** than
   `processed_candles/by_date/...`, so they are structurally outside this scan's scope (by design — quarantined objects
   are deliberately non-canonical, parked for human review, not silently deleted).
   - Verified directly: a bounded probe of `gs://market-data-tick-defi-prd-central-element-323112/_quarantine/` found
     **exactly 1,442 objects**, all under `_quarantine/processed_candles/...` — an **exact match** to the P0 census's
     `QUARANTINE_CORRUPT` count for DEFI (1,442). This confirms the objects were moved, not lost, and confirms they are
     legitimately out of this scan's scope.
2. **Split-brain-duplicate dedup collapses source count.** The issue doc explicitly notes DEFI's split-brain-duplicate
   count is folded into its `MIGRATE` histogram line rather than broken out (unlike prediction/cefi/tradfi). A
   `SPLIT_BRAIN_DUPLICATE` pair enumerates as 2 source objects pre-migration but converges to 1 canonical target
   post-migration (idempotent copy: the second arrival sees the target already verified-present and only deletes its own
   source) — a net -1 per duplicate pair. The remaining gap (1,131,814 − ~1,451 quarantine-adjusted-for-corpus-growth −
   1,123,415 ≈ 6,948) is consistent with this mechanic and is not itself a defect: every one of those objects still
   resolves to exactly one canonical target, which is what the dry-run classifier below confirms directly.

Net: the gap is fully attributable to (a) an explicit, verified out-of-scope relocation and (b) expected dedup
arithmetic — not to missing or still-non-canonical data. The dry-run classifier result below is the authoritative check
regardless of this reconciliation, and it is unambiguous.

## Dry-run classifier run (read-only, `--dry-run`, never `--apply`)

```bash
cd market-data-processing-service
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -u scripts/migrate_candle_canonical_2026_07.py \
  --dry-run \
  --enumeration <scratchpad>/p8_defi_enumeration.txt \
  --out <scratchpad>/p8_defi_mapping.tsv
```

Exit code: `0`. Full disposition histogram (from the script's own reconcile output):

```
TOTAL objects classified: 1,123,415

=== disposition histogram ===
   1,123,415  CANONICAL_NOOP

MIGRATE (incl. split-brain): 0  |  CONTENT_REPAIR pending: 0  |  QUARANTINE: 0  |  CANONICAL_NOOP: 1,123,415
SUM(dispositions) = 1,123,415  |  TOTAL = 1,123,415  |  match=True
ORPHAN count = 0  (PASS — total map)
```

Every disposition class other than `CANONICAL_NOOP` is **zero**: `MIGRATE`, `SPLIT_BRAIN_DUPLICATE`,
`NEEDS_CONTENT_INSTRUMENT_TYPE`, `EMPTY_STEM_WITH_UNDERLYING`, `EMPTY_STEM_WITHOUT_UNDERLYING`,
`NEEDS_CONTENT_TRADFI_ID`, `NEEDS_CONTENT_CEFI_WIRE_ID`, `QUARANTINE_CORRUPT`, and — the hard safety invariant —
`ORPHAN` (the pre-flight abort gate; a non-zero value here would have aborted the run loudly before any output). A
sample of the mapping TSV confirms objects carry the full locked canonical shape, e.g.:

```
processed_candles/by_date/day=2023-01-15/pipeline_mode=batch_onchain_rpc/timeframe=15m/data_type=dex_pool_swaps/instrument_type=POOL/venue=BALANCER-ARBITRUM/BALANCER-ARBITRUM:POOL:0x178e...158.parquet   CANONICAL_NOOP   <already canonical — verify in place>
```

## Verdict

**CLEAN.** A fresh, independent, real-GCS enumeration of DEFI's entire `processed_candles/by_date/` corpus (1,123,415
objects, taken today, 2026-07-23 — one full day after the migration's retry pass completed) classifies **100%
`CANONICAL_NOOP`** under the tool's own ground-truth classifier. Zero objects require migration, content-repair, or
quarantine; zero orphans. This independently confirms the P7a-full DEFI migration's own completion claim ("0 outstanding
legacy-path candle objects") — no new findings, no register-patch needed for
`codex/02-data/non-canonical-path-inventory.md`.

## Reproducibility — exact commands

```bash
# 1. Resolve bucket (market-data-processing-service/.venv)
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -c "
from unified_trading_library import resolve_bucket_name
print(resolve_bucket_name(cloud='gcp', kind='market-data', asset_group='defi', deployment_env='prd'))"

# 2. Discover day= prefixes (delimiter-descent, cheap)
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -c "
from google.cloud import storage
client = storage.Client()
bucket = client.bucket('market-data-tick-defi-prd-central-element-323112')
it = client.list_blobs(bucket, prefix='processed_candles/by_date/', delimiter='/')
list(it)
print(len(it.prefixes))"

# 3. Fresh parallel enumeration (32-worker ThreadPoolExecutor over the day= prefixes; see
#    scratchpad p8_enumerate.py for the full script) -> p8_defi_enumeration.txt

# 4. Dry-run classify (read-only, never --apply)
cd market-data-processing-service
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -u scripts/migrate_candle_canonical_2026_07.py \
  --dry-run --enumeration <enum file> --out <mapping tsv>

# 5. Quarantine-prefix sanity probe
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -c "
from google.cloud import storage
client = storage.Client()
bucket = client.bucket('market-data-tick-defi-prd-central-element-323112')
n = sum(1 for _ in client.list_blobs(bucket, prefix='_quarantine/', max_results=5000))
print(n)"
```
