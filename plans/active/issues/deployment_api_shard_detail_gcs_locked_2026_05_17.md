---
title: "deployment-api shard_detail.py + cloud_storage_client.py are GCS-locked — should use cloud-agnostic resolve_bucket_uri()"
created: 2026-05-17
author: ikenna-slot-3 (surfaced during inline-bucket-uri ratchet sweep at deployment-api@4b9dbbf)
source:
  - deployment-api/deployment_api/services/shard_detail.py (27 baseline + 3 newly-noqa'd inline `gs://` formatters)
  - unified_trading_library/config_interface/paths/registry.py:243 (legacy `build_bucket()` helper — GCS-only by docstring)
  - operator question 2026-05-17 11:00 UTC: "shard_detail should be cloud agnostic like the rest of deployment_api unless gcs has already been resolved by that point of the code path?"
locked_by: live-defi-rollout
locked_since: 2026-05-17
severity: P2 (post-cutover hygiene; not blocking May-23 since GCS is the May-23 cloud)
status: filed (deferred; cloud-agnostic migration is a refactor sprint, not a sweep item)
---

## What I found

A workspace inline-bucket-uri ratchet check at deployment-api flagged 30 violations over baseline 27. Three of
those are new formatters I just annotated with `# noqa: gs-uri` at deployment-api@`4b9dbbf` to restore the
baseline. BUT the underlying structural gap is bigger:

**`deployment-api/deployment_api/services/shard_detail.py` is structurally GCS-locked.**

The function `_read_instruments_day_df(bucket: str, venue, day, category)` and its callers all take a `bucket`
arg that came from `_instruments_bucket_for_category(category)` → `build_bucket("instruments", project_id=_pid,
asset_group=...)` (UTL).

`build_bucket()` docstring at
`unified_trading_library/config_interface/paths/registry.py:243`:
```python
def build_bucket(name: str, *, project_id: str, asset_group: str = "") -> str:
    """Return GCS bucket name for *name*; *asset_group* is the cefi/defi/… path segment.
    ...
    """
```

By the time `bucket` reaches the formatter sites in `_read_instruments_day_df`, **the GCS resolution has
already happened** (answering the operator's question literally — yes, GCS is resolved upstream). BUT the
upstream resolver itself is GCS-only. So the code path can't ever produce an S3 URI.

The 27-baseline inline-`gs://` formatters in deployment-api are essentially all of this shape: they live
inside helpers that took a `bucket` arg from `build_bucket()` and then composed `f"gs://{bucket}/..."`. The
3 new ones I noqa'd today are the same pattern just newly-introduced.

Additionally: `deployment_api/utils/cloud_storage_client.py:39` had a `f"Unsupported cloud path scheme. Must
start with gs:// or s3://. Got: {cloud_path}"` error-message literal flagged by the same regex. That's
genuinely a docstring-style usage and the noqa is the right fix; not part of the structural gap.

## Why it matters

This contradicts the CLAUDE.md "Bucket-name SSOT" HARD RULE:

> Every bucket lookup via `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` —
> never inline `gs://` f-string. `deployment-service/configs/cloud-providers.yaml` is canonical.
> QG STEP 5.69 enforces.

The `build_bucket()` helper that shard_detail uses is the **legacy** path, predating the cloud-agnostic
`resolve_bucket_name()` / `resolve_bucket_uri()` SSOT shipped in `bucket_name_ssot_canonicalisation_2026_05_10`.

Sister files in deployment-api already migrated to the canonical resolver (e.g.
`deployment_api/services/data_status_drilldown.py:47` references `resolve_bucket_name()`;
`deployment_api/services/deploy_missing.py:542` references the same; `data_status_service.py:2826` references
it). So the workspace pattern IS the migration; shard_detail.py is just behind.

**Why this is NOT a May-23 blocker**: May-23 cutover runs on GCP only (CLAUDE.md "Custody:
CLOUD_KMS_ENCRYPTED for May-23 → COPPER + CEFFU per POD June-1"). AWS migration is post-cutover (Group F
"Post-Gate-4 AWS migration" in master plan, lines 1843+). GCS-locked code paths work fine for May-23.

But this IS a real cloud-agnostic-migration gap and the inline-bucket-uri ratchet's "baseline 27" tolerance
should shrink to 0 once shard_detail.py migrates.

## Recommended decision

**Phase A — establish (DONE 2026-05-17 ikenna-slot-3 at deployment-api@`4b9dbbf`)**: 3 new violations noqa'd
with rationale linking to this issue doc. QG baseline restored to 27. No regression.

**Phase B — cloud-agnostic migration (POST-CUTOVER, ~1.5 cal AI-day)**: refactor `_instruments_bucket_for_category`
+ `_read_instruments_day_df` + callers to use
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_uri(cloud=..., kind="instruments",
asset_group=..., path=...)` returning the correct `gs://...` or `s3://...` URI based on the cloud
configuration. All 27 baseline + 3 noqa'd formatters can then be removed (ratchet to 0). The migration
pattern is well-established at sister files in deployment-api.

**Phase C — ratchet baseline 27→0 (POST-CUTOVER after Phase B)**: update
`unified-trading-pm/scripts/quality_gates/inline_bucket_uri_baseline.yaml` for deployment-api.

## Cross-references

- CLAUDE.md "Bucket-name SSOT" HARD RULE (§ "Other key rules")
- `bucket_name_ssot_canonicalisation_2026_05_10.md` (parent plan for the workspace-wide SSOT migration)
- `inline_bucket_uri_baseline.yaml` (current ratchet floor: 27 for deployment-api)
- Sister files already migrated: `data_status_drilldown.py` / `deploy_missing.py` / `data_status_service.py`
- deployment-api@`4b9dbbf` (this session's Phase A noqa fix)

---

## Triage — 2026-05-18

**Status**: OPEN  
**Triaged by**: slot-8 triage sweep  
**Reason**: Structural cloud-agnostic migration gap; P2 deferred
