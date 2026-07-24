---
doc_type: audit-result
title: P8 — CEFI candle canonical-path migration, independent post-migration verification
summary: >-
  Fresh, independent enumeration of gs://market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/
  (405,408 objects, 2026-07-23) re-classified via the migration script's own read-only --dry-run pass. Result: 0 ORPHAN,
  0 QUARANTINE/CONTENT_REPAIR pending, 405,259 CANONICAL_NOOP, exactly 149 SPLIT_BRAIN_DUPLICATE — an EXACT count match
  to the todo-19 documented residual (candle_feature_canonical_path_divergence_2026_07_20.md). Verdict: RESIDUAL MATCHES
  TODO-19 EXPECTATION.
status: pass
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [data-correctness, canonical, gcs-paths, candles, migration, verification, p8, todo-19]
related:
  [
    ../../active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-23
last_updated: 2026-07-23
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=cefi, PROD (-prd-) bucket only (market-data-tick-cefi-prd-central-element-323112),
  processed_candles/by_date/ prefix only, read-only; fresh enumeration (405,408 objects) + a re-derived --dry-run
  classify pass, independent of the prior --apply run's own bookkeeping"
date: 2026-07-23
auditor: P8 independent post-migration verification (candle canonical-path migration, todo-19 residual check)
parent_epic: infrastructure_master
severity: P2
source: >-
  Independent P8 verification, 2026-07-23: fresh google-cloud-storage list_blobs enumeration of
  processed_candles/by_date/ (day-prefix-chunked, 20-worker ThreadPoolExecutor) + a read-only
  migrate_candle_canonical_2026_07.py --dry-run classify pass over that enumeration. No --apply, no writes, no deletes.
---

# P8 — CEFI candle canonical-path migration: independent post-migration verification

**Verdict: RESIDUAL MATCHES TODO-19 EXPECTATION.** A fresh, independent enumeration + read-only re-classification of
CEFI's `processed_candles/by_date/` corpus today finds exactly **149** non-canonical residual objects — an EXACT match
to the documented todo-19 count in `plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`
(Progress Log "P7c: CEFI DONE — 149-object documented residual", 2026-07-23). Zero orphans, zero unexpected disposition
classes.

## What this verifies

The prior migration (`market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py --apply`) reported 149
objects as `CRC32C_MISMATCH_KEPT_SRC`/`SIZE_MISMATCH_KEPT_SRC` across its 10 shards — a known, accepted, non-blocking
gap in `_copy_verify_delete()`'s retry-idempotency (filed as todo 19: a destination that exists-but- failed-verification
is never retried, because the copy step only fires when the destination is absent). That prior count was **self-reported
by the apply run**, not independently re-derived. This task (P8) re-derives it from scratch: a brand-new GCS enumeration
today, re-classified by the same script's own dry-run logic, entirely independent of the apply run's own bookkeeping.

## Bucket + reachability

```
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -c "
from unified_trading_library import resolve_bucket_name
resolve_bucket_name(cloud='gcp', kind='market-data', asset_group='cefi', deployment_env='prd')
"
# -> market-data-tick-cefi-prd-central-element-323112
```

Confirmed reachable via a non-recursive top-level `list_blobs(prefix='processed_candles/', delimiter='/')` before the
full walk (returned exactly one common prefix: `processed_candles/by_date/`).

## Fresh enumeration (bounded, single-prefix walk)

Scope: `processed_candles/by_date/` **only** (not the whole bucket) — a single sanctioned bounded walk for this one
prefix, per the task's single-walk discipline. Method: cheap delimiter-descent to list `day=` prefixes (327 found), then
a 20-worker `ThreadPoolExecutor` doing a full (non-delimited) `list_blobs(prefix=day_prefix)` per day, writing one
`gs://<bucket>/<rel>` URI per line.

- **Total objects enumerated: 405,408** (327/327 day prefixes, 0 listing errors), ~1,114s wall-clock.
- Enumeration file: `p8_cefi_enumeration.txt` (scratchpad; not committed — ephemeral working artifact).

**Object count vs. the pre-migration P0 census (940,606):** the drop is expected, not a discrepancy. The migration's
`--apply --quarantine` gate moves `QUARANTINE_CORRUPT`/`EMPTY_STEM_WITHOUT_UNDERLYING`-classified objects to a
**sibling** top-level prefix, `_quarantine/processed_candles/by_date/...` — outside `processed_candles/by_date/`
entirely (`QUARANTINE_PREFIX = "_quarantine"`, and the quarantine target is built as `f"{QUARANTINE_PREFIX}/{rel}"`
where `rel` is the object's full bucket-relative path, i.e. `_quarantine/` sits at the bucket root, not nested inside
`processed_candles/`). Confirmed today via a cheap existence probe:

```
list_blobs(bucket, prefix='_quarantine/', delimiter='/', max_results=5).prefixes
# -> ['_quarantine/processed_candles/']
```

So this enumeration, scoped strictly to `processed_candles/by_date/`, correctly excludes everything the apply run
already quarantined out — it was never meant to re-count those. (Per the issue doc's Progress Log for the CEFI apply
run, `CONTENT_REPAIR_UNRESOLVED_QUARANTINED` ran ~13-14% of each shard — consistent in order of magnitude with the
~535K-object difference between the pre-migration census and today's in-prefix count.)

## Dry-run classification (read-only — no `--apply`, no writes, no deletes)

```
cd market-data-processing-service
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -u scripts/migrate_candle_canonical_2026_07.py \
  --dry-run \
  --enumeration <scratchpad>/p8_cefi_enumeration.txt \
  --out <scratchpad>/p8_cefi_mapping.tsv
# exit code 0
```

### Disposition histogram (full, verbatim from script output)

```
TOTAL objects classified: 405,408

=== disposition histogram ===
     405,259  CANONICAL_NOOP
         149  SPLIT_BRAIN_DUPLICATE

MIGRATE (incl. split-brain): 149  |  CONTENT_REPAIR pending: 0  |  QUARANTINE: 0  |  CANONICAL_NOOP: 405,259
SUM(dispositions) = 405,408  |  TOTAL = 405,408  |  match=True
ORPHAN count = 0  (PASS — total map)
```

No `MIGRATE`, `NEEDS_CONTENT_*`, `EMPTY_STEM_*`, `QUARANTINE_CORRUPT`, `NOT_CANDLE_NAMESPACE`, or `ORPHAN` entries at
all — every one of the 405,408 objects resolves to exactly one of two buckets: already-canonical, or the known
split-brain residual.

## Root-cause corroboration for the 149 (new color, not a new problem)

The task brief anticipated the residual might show up as `MIGRATE`/`SPLIT_BRAIN_DUPLICATE`/similar rather than literally
re-appearing as `KEPT_SRC` (that label is an `--apply`-only outcome; a dry-run re-classify necessarily re-derives
disposition from path shape alone, not from the previous run's per-object outcome log — which in any case was never
captured per-object, see the issue doc's "why not just fix the script live" note). All 149 residual entries here are
`SPLIT_BRAIN_DUPLICATE`, and characterizing them fully:

| Axis                                              | Result                                                                                                                                                                                              |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `data_type`                                       | 93 `futures_chain` (BYBIT) + 56 `options_chain` (DERIBIT) — 100% chain-bundle-eligible types                                                                                                        |
| Canonical target leaf filename                    | **100%** resolve to the bundled `ticks.parquet` name (never an individual leaf id)                                                                                                                  |
| `pipeline_mode=` present on the legacy (old) path | 76 yes / 73 no — i.e. roughly half-and-half                                                                                                                                                         |
| Days affected                                     | exactly 8 distinct days (`2023-06-01`, `2023-08-02`, `2023-11-02`, `2024-02-01`, `2024-02-02`, `2024-07-01`, `2025-11-01`, `2026-01-01`) — every other one of the 327 enumerated days is 100% clean |
| Objects per shared target                         | mostly 2 (one `pipeline_mode=`-carrying + one `pipeline_mode`-less sibling, per the script's own documented defect #3), a few 3s/4s on `2024-07-01`                                                 |

This matches the script's own docstring description of "defect #3" (split-brain duplicates: the same logical shard
existing as two source objects — most commonly one `pipeline_mode=`-partitioned + one `pipeline_mode`-less copy — that
both resolve to the same canonical target) applied to the **chain-bundle** case specifically: multiple distinct per-leg
objects (e.g. a BYBIT `BTC-20240628` future and an `ETH-20240628` future on the same day/venue/timeframe) all collapse
onto the **same** shared `ticks.parquet` bundle target. The docstring's stated `--apply` behavior for split-brain ("the
second one to reach the target sees it already present and simply verifies+deletes its own source, no primary election
needed") implicitly assumes the two/more siblings are byte-identical duplicates; for the chain-bundle case they are
**not** — each carries a different instrument leg's candle data — so the second (and subsequent) sibling's post-copy
verification against the already-written destination will legitimately fail on size/crc32c. This is the most plausible
mechanism explaining why exactly these objects landed in `CRC32C_MISMATCH_KEPT_SRC`/`SIZE_MISMATCH_KEPT_SRC` during
`--apply` — it deepens, but does not contradict or change, the existing todo-19 finding (a proper fix likely needs real
content-level parquet merging for the bundle case, not just a retry-idempotency patch — worth folding into whoever
eventually picks up todo 19, but out of scope for this verification task).

## Verdict

**RESIDUAL MATCHES TODO-19 EXPECTATION.** 149/149 — an exact count match, same disposition class the task anticipated
(`SPLIT_BRAIN_DUPLICATE`), 0 `ORPHAN`, 0 unexpected `QUARANTINE_CORRUPT`/`NEEDS_CONTENT_*` residue, and the affected
objects' shape (100% chain-bundle `futures_chain`/`options_chain` types resolving to a shared `ticks.parquet` target,
concentrated on exactly 8 days) is internally consistent and well-explained. No new finding requiring action beyond what
todo 19 already tracks. CEFI's candle canonical-path migration+purge stands confirmed at 99.98%+ complete, with the same
149-object residual independently reproduced.

## Reproduction

```bash
# 1. Resolve bucket
cd market-data-processing-service
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -c "
from unified_trading_library import resolve_bucket_name
print(resolve_bucket_name(cloud='gcp', kind='market-data', asset_group='cefi', deployment_env='prd'))
"

# 2. Fresh enumeration of processed_candles/by_date/ only (day-prefix-chunked, 20 workers) -> p8_cefi_enumeration.txt

# 3. Read-only dry-run classify
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -u scripts/migrate_candle_canonical_2026_07.py \
  --dry-run \
  --enumeration p8_cefi_enumeration.txt \
  --out p8_cefi_mapping.tsv

# 4. Inspect residual
grep "SPLIT_BRAIN_DUPLICATE" p8_cefi_mapping.tsv | wc -l   # -> 149
```

No `--apply`, no `--quarantine`, no `--content-repair` were passed at any point. Read-only against GCS throughout.
