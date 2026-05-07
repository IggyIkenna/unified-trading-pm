---
title: "Manifest consolidator failing on defi/tradfi/prediction buckets — ArrowTypeError on instrument_count column"
created: 2026-05-07
author: claude-session
source:
  - manifest-consolidator-20260507-175639 VM run.log (2026-05-07 17:24 UTC + 17:28 + 17:32 UTC consolidator cycles)
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md § Phase 3.D.5 Wave 2.M (migration that surfaced the bug)
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# Manifest consolidator failing on 3-of-5 market-data-tick buckets

> **Severity**: P0 — blocks the writegate Wave 2.M migration's per-VM shards from merging into canonical
> manifests for defi / tradfi / prediction. cefi merge already succeeded; sports is lock-contended (sibling
> cron running, status unclear).
>
> **Blast radius**: 3 asset_groups (defi / tradfi / prediction). Migration data for those 3 sits in
> `_index/per_vm/blank-reason-recon-{ag}-*.parquet` waiting for the consolidator to merge. Data-status
> panel + downstream consumers reading the canonical manifest will NOT see the migration's effect on
> those 3 buckets until the consolidator schema-conflict is fixed.
>
> **Suggested owner**: manifest-consolidator service maintainer (operator triage).

## What I found

Consolidator log (`gs://deployment-scripts-central-element-323112/vm-logs/manifest-consolidator-20260507-175639/run.log`)
shows repeated failures on three `market-data-tick-*` buckets:

```
2026-05-07T17:24:54Z  bucket=market-data-tick-prediction-central-element-323112  success=False
   error=ArrowTypeError: ("Expected bytes, got a 'int' object",
                          'Conversion failed for column instrument_count with type object')

2026-05-07T17:28:24Z  bucket=market-data-tick-defi-central-element-323112        success=False
   error=ArrowTypeError: ("Expected bytes, got a 'int' object",
                          'Conversion failed for column instrument_count with type object')

2026-05-07T17:28:36Z  bucket=market-data-tick-tradfi-central-element-323112      success=False
   error=ArrowTypeError: ("Expected bytes, got a 'int' object",
                          'Conversion failed for column instrument_count with type object')
```

The same error repeats every cycle (every ~5min). cefi succeeds (`shards=1482 rows_in=0 rows_out=0`), so
the bug is not workspace-wide — only the 3 listed buckets are affected.

## Why it matters

Today's writegate Phase 3.D.5 Wave 2.M migration ran successfully and uploaded per-VM shards for all 5
asset_groups:

```
gs://market-data-tick-cefi-central-element-323112/_index/per_vm/blank-reason-recon-cefi-20260507-173136.parquet  (1.24M rows)
gs://market-data-tick-defi-central-element-323112/_index/per_vm/blank-reason-recon-defi-20260507-175522.parquet  (685 rows)
gs://market-data-tick-tradfi-central-element-323112/_index/per_vm/blank-reason-recon-tradfi-20260507-175606.parquet  (7,603 rows)
gs://instruments-store-sports-central-element-323112/_index/per_vm/blank-reason-recon-sports-20260507-175543.parquet  (1.87M rows)
gs://market-data-tick-prediction-central-element-323112/_index/per_vm/blank-reason-recon-prediction-20260507-175636.parquet  (41 rows)
```

**cefi**: canonical `_index/availability_index.parquet` mtime = 2026-05-07T17:33:40Z (post-migration; merge
landed). 1.24M rows now classified per the discriminated taxonomy (1.24M `attempted_failed` + 150
`EXPECTED_PRE_VENUE_LAUNCH`).

**defi / tradfi / prediction**: canonical mtimes still at 14:48-14:56 UTC (pre-migration). The
consolidator can't merge until the schema conflict is resolved. Per-VM shards persist (consolidator only
deletes after successful merge).

**sports**: consolidator log shows skipped cycles ("fresh lock present (sibling cron still running)")
— another consolidator process holds the lock. Status of that sibling unknown from this VM's log.

## Root cause hypothesis

The `instrument_count` column has inconsistent types across per-VM shards in defi/tradfi/prediction. One
or more shards has it as `int` (or pandas `object`), while the canonical / other shards have it as
`bytes`. When pyarrow tries to concatenate, it raises.

Candidates:

* `_legacy_seed.parquet` (defi 2026-05-03, prediction 2026-04-29) — pre-canonical-schema seed, may have
  a different `instrument_count` type than current writes.
* Older mtds-vault-share-price / mdps-prediction shards — may predate a schema migration that bytes-ed
  the column.
* My own writes (instruments-service@86804c7) — though these reuse the canonical's df schema verbatim
  via `df.loc[mask].to_parquet(out_path, index=False)`, so should match. **2026-05-07 verification**:
  the cefi merge SUCCEEDED with my shard, suggesting our writes are not the cause.

The schema-conflict predates today's migration writes (first error 17:24 UTC; our writes 16:58-17:02 UTC,
but the same pattern likely exists in pre-2026-05-07 shards too).

## Recommended decision

1. **Inspect the per-VM shards** for the offending column-type rows. Run
   `for shard in $(gcloud storage ls gs://market-data-tick-defi.../_index/per_vm/*.parquet); do
        gcloud storage cat $shard | python -c "import pyarrow.parquet as pq, sys; t=pq.read_table(sys.stdin.buffer); print(shard, t.schema.field('instrument_count').type)"
   done`
   or similar, to identify which shard has the wrong type.
2. **Re-write the offending shard(s)** with the correct type (bytes — matching the canonical). Or
   **delete the offending shard(s)** if they're stale (e.g. `_legacy_seed.parquet` if its purpose was
   one-time seeding and it's been merged already).
3. **Restart the consolidator** to pick up the fixed/deleted shards.
4. **Verify migration merge**: defi/tradfi/prediction canonical mtimes should bump after the next
   consolidator cycle; data-status panel should reflect the migration outcome (defi 685 attempted_failed,
   tradfi 7,603 split, prediction 41 SOURCE_RETURNED_ZERO).

Out of scope for this issue doc: the writegate Phase 3.D.5 work shipped today is correct end-to-end; the
manifests just need this consolidator bug resolved before the canonical reflects them.

## Cross-references

* Migration plan: `plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md` § Phase 3.D.5 Wave 2.M
* Migration script: `instruments-service/scripts/reconcile_blank_error_reason_rows.py`
* Migration commits today: UAC@e855051, UTL@68b3804a, UTL@7eca2c20, UTL@7276cca1,
  instruments-service@86804c7, deployment-service@f72686b, deployment-service@327acf4
