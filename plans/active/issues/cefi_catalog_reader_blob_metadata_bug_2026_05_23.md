---
title: CeFi backfill VMs silently capturing 0 records — BlobMetadata.endswith() crash in CeFiCatalogReader
created: 2026-05-23
source:
  - market-tick-data-service/market_tick_data_service/engine/cefi_catalog_reader.py
  - market-tick-data-service@09361718 # introducing commit (Phase 3.D.5 v2 enumerator)
  - plans/active/aws_cloud_toggle_and_backfill_parity_2026_05_22.md
  - plans/active/aws_migration_defi_first_2026_05_07.md
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

**17 CeFi backfill VMs** launched in two waves on 2026-05-23 (~14:21 UTC and ~16:15 UTC) recorded "0 venues ok, 0
failed, 0 skipped (no instruments), 0 total records" for every processing date attempted, and have produced **no log
output** for 45 min – 2.5 h (heartbeat uploader frozen; serial console silent past initial bootstrap).

Root cause is a type-mismatch crash in `CeFiCatalogReader._load_latest_catalog`:

```python
# market_tick_data_service/engine/cefi_catalog_reader.py (pre-fix)
raw_blobs = self._client.list_blobs(self._bucket, prefix=_CATALOG_PREFIX)
blobs: list[str] = list(raw_blobs)                              # ← actually list[BlobMetadata]
parquet_blobs = [b for b in blobs if b.endswith("all.parquet")]  # ← AttributeError
```

`StorageClient.list_blobs()` returns `Iterator[BlobMetadata]`, not strings. `BlobMetadata` is a `@dataclass` with a
`.name: str` field
([unified-trading-library abstractions.py:38](../../../unified-trading-library/unified_trading_library/cloud_interface/abstractions.py#L38)).
Calling `.endswith()` on the dataclass itself raises
`AttributeError: 'BlobMetadata' object has no attribute 'endswith'`. The orchestrator's broad `except Exception` at
[orchestrator.py:3163](../../../market-tick-data-service/market_tick_data_service/engine/orchestrator.py#L3163) catches
it and falls back to UAC seed instruments — which then produces 0 records for the venues the VMs were launched to
backfill.

Repro from any VM run.log:

```
WARNING CeFi catalog read failed for date=2024-01-04: 'BlobMetadata' object has no attribute 'endswith'
        — falling back to UAC seed instruments
INFO    Manifest updated: date=2024-01-04 venues=0 shards=0 total_records=0 complete=False
INFO    Processed date=2024-01-04: 0 venues ok, 0 failed, 0 skipped (no instruments), 0 total records
```

Introduced by `market-tick-data-service@09361718` ("feat: add CeFi v2 catalog enumerator (Phase 3.D.5)").
`SportsCatalogReader` uses direct per-league path templates and is unaffected. All other workspace `list_blobs()`
callers correctly extract `.name` (verified workspace-wide grep — client-reporting-api, MDPS scripts, deployment-service
monitor all use `blob.name` or `getattr(b, "name", "")`).

## Why it matters

- **Data-pipeline correctness HARD RULE violation**: 17 VMs burned ~3h compute producing 0 records; the entire current
  CeFi backfill wave is wasted.
- **Silent failure pattern**: orchestrator's `except Exception` swallows the type error, so this only surfaces by
  reading run.log line-by-line. Manifest "captured" counter freezes; no alert fires.
- **Compounds with VM hang**: even after catalog falls back, processes go SILENT (no log output, no STOPPED/FAILED) for
  45min-2.5h with `gcloud instances list` still reporting RUNNING. The `STALL_TIMEOUT_SEC=1800s` watchdog from
  `deployment-service@88c53ad` did NOT trigger — suggests either the watchdog isn't deployed in these VM tarballs OR a
  separate hang occurs in the fallback path that the watchdog can't detect (e.g. heartbeat daemon dies but process holds
  CPU).
- **Blocks AWS smoke + ECS deployment**: AWS Phase 5 smoke + Phase 6 ECS Fargate deploy (both tracked in
  `plans/epics/infrastructure_master.md` § P3 — the source plans `aws_cloud_toggle_and_backfill_parity_2026_05_22.md`
  and `aws_migration_defi_first_2026_05_07.md` were archived 2026-05-23; deferred work migrated to epic) are gated on
  GCP CeFi backfill 100% complete.

## Recommended decision

**P0 — fix shipped, VM relaunch required**:

1. **Fix shipped**: `market-tick-data-service@9c91a176`
   (`fix(catalog): CeFiCatalogReader.endswith() crash — BlobMetadata not str`) pushed to `live-defi-rollout`. One-line
   change: `blobs: list[str] = [b.name for b in raw_blobs]`. Pushed with `--no-verify` per operator authorisation
   (pre-existing MTDS QG failure on `unified_trading_library.risk.rule_evaluator` BinaryEventTrigger import — foreign,
   not introduced by this change).
2. **Operator action needed**: stop the 17 in-flight CeFi backfill VMs (`gcloud compute instances delete ...`), rebuild
   VM tarballs via `bash deployment-service/scripts/vm/create-code-tarballs.sh` to pick up @9c91a176, relaunch the
   waves. Without rebuild + relaunch the running VMs continue producing 0 records.
3. **P1 follow-up — investigate VM hang** (likely separate bug): heartbeat daemon stops uploading logs after the
   catalog-read failure cascade. STALL_TIMEOUT_SEC watchdog should have caught the silence but didn't. Suspected: either
   watchdog code not in the tarball, or the python process is genuinely deadlocked (e.g. in pre-flight) and the
   heartbeat thread died with the main thread alive. Needs SSH into a hung VM before delete + thread dump
   (`py-spy dump --pid <pid>`).
4. **P2 follow-up — orchestrator should NOT swallow `AttributeError` in catalog fallback path**: the broad
   `except Exception` at `orchestrator.py:3163` masks type-mismatch bugs. Consider tightening to
   `except (KeyError, IOError, GCSError)` so genuine code bugs raise loud per the "schema-drift bug → RAISE LOUD"
   Manifest+Honest Absence HARD RULE.

## Composes with

- `Data Pipeline Correctness Is The Heartbeat` (HARD RULE) — every cell either `captured` or
  `empty_confirmed[reason=<typed>]`; silently emitting 0 records is neither.
- `Manifest + Honest Absence` HARD RULE — "schema-drift bug → RAISE LOUD" applies here; the broad exception catch in
  orchestrator.py:3163 violates this.
- `External Data Is Always Available` — root cause is code bug, NOT data absence; current 17 VMs do NOT qualify for
  BLOCKED-CREDENTIALS or BLOCKED-OPERATOR-DECISION.

## Status

- 2026-05-23 ~17:30 UTC — Fix shipped at MTDS@9c91a176. Awaiting operator: VM kill + tarball rebuild
  - relaunch. P1+P2 follow-ups deferred to post-relaunch.
- 2026-05-23 ~18:30 UTC — Two additional critical findings expand scope (see slot_3.md ping):
  - **969,349 bait sentinels** (`captured count=0`, no parquet in GCS, 14/15 sample probe confirmed missing) are
    poisoning pre-flight skip — `_filter_data_types_by_atom_coverage` treats them as captured atoms → 817K orphan cells
    get false-skipped. 99.2% of bait sentinels were written in one 2h burst on 2026-05-04 (single event, schema_v6, all
    enumerator_run_id=None).
  - **MTDS@020442bf catastrophic regression**: commit "feat(mtds): add mbp_10 to CME tick_window + fix G201 lint in
    orchestrator" actually **deleted 3,557 lines** of orchestrator.py — including the pre-flight skip logic, per-venue
    async fan-out, Tier-3 sentinel fan-out, all catalog reader registrations, and the `process_ticks` signature went
    from 11 params to 5. CLI handler at `tick_data_handler.py:242` now TypeError's on every call (passes
    `asset_groups=`, `instrument_ids=`, `force=` etc. to an orchestrator that no longer accepts them). MTDS is
    functionally down on live-defi-rollout.
- Bait-sentinel guard prepared (stash@{0} in slot-3 MTDS worktree) but unpushable until 020442bf is reverted by operator
  (the code being patched no longer exists in HEAD).
- 2026-05-23 ~20:15 UTC — All operator-approved actions executed:
  - **17 in-flight CeFi backfill VMs deleted** (`gcloud compute instances delete` via xargs).
  - **MTDS@020442bf reverted** at `MTDS@ed0ab31c` — restores 3,557 lines of orchestrator including pre-flight skip
    logic, per-venue async fan-out, Tier-3 sentinel fan-out, all catalog reader registrations.
  - **CME mbp_10 yaml change cherry-picked cleanly** at `MTDS@325beaa7` (only useful payload of 020442bf; does NOT
    re-add the stale `tick_windows:` section that 020442bf snuck back in).
  - **Bait-sentinel pre-flight guard shipped** at `MTDS@e032b186` — defensive backstop. Excludes captured-with-count-0
    rows from the pre-flight skip set unconditionally.
  - **Targeted cleanup script shipped** at `MTDS@623ce2c8` (`scripts/cleanup_may4_bait_sentinels.py`). Avoids the
    110-min full GCS walk of `reconcile_phantom_manifest_rows_all.py` since the bait class is already characterised.
  - **960,447 bait sentinels flipped** in consolidated manifest to
    `attempted_failed error_reason=bait_sentinel_may4_burst_no_parquet attempted_at=<now>`. Pre-flip snapshot preserved
    at
    `gs://market-data-tick-cefi-central-element-323112/_index/snapshots/pre_bait_cleanup_2026-05-23T19-09-35Z.parquet`.
  - **Bait source shard quarantined**: per-VM shard `_index/per_vm/local-99178-edc2.parquet` (983,904 rows, 100%
    captured + count==0, all written 2026-05-04 11:06-13:15 UTC) was the single source of the bait burst. Snapshotted to
    `_index/snapshots/bait_source_local-99178-edc2_quarantined_2026-05-23.parquet` then deleted. Without this deletion
    the consolidator (10 Cloud Run jobs `*/1 * * * *`) would re-introduce the bait rows on the next merge cycle —
    `legacy_seed` predates May-4 and the consolidator merges legacy_seed + per_vm/\*.parquet from scratch each cycle
    (`_merge_shard_frames`, last-write-wins on `attempted_at`). With the source shard gone, the next merge produces a
    bait-free consolidated.
- **Awaiting operator** (the actual relaunch path now unblocked):
  1. Rebuild VM tarballs: `bash deployment-service/scripts/vm/create-code-tarballs.sh`. New tarball will include
     MTDS@ed0ab31c (revert) + MTDS@9c91a176 (BlobMetadata fix) + MTDS@e032b186 (bait guard) + MTDS@325beaa7 (CME
     mbp_10) + MTDS@623ce2c8 (cleanup script).
  2. Relaunch CeFi backfill waves (heavy + light) — the launcher (`deployment-service@38902bf` with e2-highmem-8
     default) is unchanged; relaunch resumes where the deleted VMs left off (pre-flight will properly retry the 817K
     orphan cells that were previously false-skipped).
  3. Decide on broader phantom audit: optional follow-up. The full
     `reconcile_phantom_manifest_rows_all.py --asset-group cefi --apply` (~110 min on the current 35M-row CeFi manifest)
     would catch any OTHER phantom-captured rows beyond the May-4 bait window. Not required for the May-23 backfill
     gate.
