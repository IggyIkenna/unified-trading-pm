---
title: "UTL _touch_canonical_mtime: copy_blob-to-self silently fails in newer GCS SDK"
created: 2026-05-23
source:
  - plans/active/mdps_backfill_phase3_2026_05_22.md
  - unified-trading-library/unified_trading_library/manifest_consolidator.py
priority: P2
status: resolved
resolved_at: 2026-05-23
resolved_by: unified-trading-library@0ea6989c
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **✅ ARCHIVED 2026-05-27 `[unlock-plan]`** — RESOLVED (frontmatter status:resolved) — tier-2 re-upload fallback
> shipped UTL@0ea6989c (`manifest_consolidator.py` `_touch_canonical_mtime`).
>
> Operator-authorized archival 2026-05-27 (issue-doc lifecycle: work shipped or fully captured in a named plan). Lock
> `live-defi-rollout` removed via `[unlock-plan]` in the archival commit.

## What I found

`_touch_canonical_mtime` (UTL `manifest_consolidator.py:572`) is intended to refresh the GCS blob `Updated` timestamp on
`_index/availability_index.parquet` when the consolidator runs `no_op_unchanged` (all per-VM shards already merged into
canonical — nothing new to write, but mtime stays stale).

Implementation uses `Bucket.copy_blob(source_blob, bucket_ref, _CANONICAL_INDEX_PATH)` (server-side GCS copy to self).
This is supposed to create a new GCS generation with a fresh `Updated` timestamp.

**Observed failure**: For bucket `market-data-tick-defi-central-element-323112`, the method returns `True` (no
exception) but `blob.updated` does NOT advance. The `consolidator_run_at` custom metadata also stays unchanged.
Confirmed by:

- Cloud Run consolidator ran every minute for 2+ hours → `blob.updated` stayed at `17:35:17 GMT`
- Local bumtwjrt3 consolidation (exit 0, no_op_unchanged path) → `blob.updated` still `17:35:17`
- Manual `blob.upload_from_file()` re-upload → DID advance `blob.updated` and `consolidator_run_at`

**Impact**: After content-changing consolidation (real merge), future no-op cycles are supposed to keep the manifest
fresh via mtime touch. When touch fails silently, `blob.updated` ages past 120s, all MDPS VMs fall back to
`_read_and_merge_per_vm_shards` (reads ALL 59 per-VM shards = 30MB download). On DeFi bucket: tolerable. On larger
buckets with hundreds of VMs: OOM risk.

## Root cause hypothesis

`Bucket.copy_blob` was deprecated in `google-cloud-storage >= 2.0`. The method signature in newer SDK versions may
differ or the server-side copy to self may be silently rejected. The `copy_blob` call returns without raising but GCS
rejects the no-op copy (same source/dest/name = no new generation written). The caller has no way to detect this without
checking `blob.reload()` after.

Evidence: `getattr(bucket_ref, "copy_blob", None)` returns a callable (the method exists) → function proceeds →
`copy_blob(...)` returns None without raising → function returns True. But no new GCS generation was created.

## Why it matters

- Every bucket using `per_vm_shards=True` depends on this working correctly
- The 120s freshness window is tight; one failed touch = every subsequent VM reads 30-100MB of per-VM shards instead of
  the consolidated 2-3MB canonical
- VMs starting up during a staleness window do extra GCS work and memory allocation
- Larger CeFi/TradFi buckets with 100+ per-VM shards could OOM on startup

## Recommended fix

Replace the `copy_blob` touch with a reliable content-preserving re-upload:

```python
def _touch_canonical_mtime(client: object, bucket: str) -> bool:
    native = getattr(client, "_client", None)
    if native is None:
        return False
    try:
        bucket_ref = native.bucket(bucket)
        blob = bucket_ref.blob(_CANONICAL_INDEX_PATH)
        # Try server-side copy first (fast, no client-side bandwidth)
        copy_blob = getattr(bucket_ref, "copy_blob", None)
        if callable(copy_blob):
            blob.reload()
            updated_before = getattr(blob, "updated", None)
            copy_blob(blob, bucket_ref, _CANONICAL_INDEX_PATH)
            blob.reload()
            updated_after = getattr(blob, "updated", None)
            if updated_after != updated_before:
                return True
        # Fallback: download + re-upload (bumps Updated + preserves metadata)
        data = blob.download_as_bytes()
        meta = dict(blob.metadata or {})
        meta[_CONSOLIDATOR_RUN_AT_KEY] = datetime.now(UTC).isoformat()
        blob.metadata = meta
        blob.upload_from_string(data, content_type="application/octet-stream")
        return True
    except Exception as exc:
        logger.info(
            "ManifestConsolidator: canonical mtime touch failed for %s (%s) — "
            "reader may fall back this cycle",
            bucket, exc,
        )
        return False
```

Note: The fallback download+re-upload costs one GET + one PUT (~2.5MB per cycle). At 1-min cron cadence with 10 buckets,
this is ~25MB/min bandwidth cost — acceptable given the alternative (30MB per-VM shard merge per VM startup).

## Workaround (applied 2026-05-23)

Manual re-upload via Python SDK before DeFi VM launch:

```python
blob.upload_from_file(io.BytesIO(data), content_type='application/octet-stream')
```

This advances `blob.Updated` AND sets `consolidator_run_at` metadata. Applied at 18:52:55 UTC and again at 18:56:33 UTC
before launching `mdps-defi-{2022..2026}-20260523-195633`.

## Deployment path for fix

1. Fix UTL `manifest_consolidator.py:_touch_canonical_mtime` as above
2. Run `cd unified-trading-library && bash scripts/quality-gates.sh`
3. Push UTL to LDR → UTL semver bump
4. Rebuild Cloud Run consolidator Docker image (UTL dependency update)
5. Deploy new Cloud Run image to `uts-prod-manifest-consolidator-*` jobs

Tracking: `mdps_backfill_phase3_2026_05_22.md` SIXTH FIX section.
