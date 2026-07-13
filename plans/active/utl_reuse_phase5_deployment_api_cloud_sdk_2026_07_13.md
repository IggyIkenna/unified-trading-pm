---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 5 deployment-api cloud-SDK-direct (routes half)
summary:
  Route deployment-api's remaining raw storage.Client() call-sites (builds routes + shard_detail) through UTL
  get_storage_client(); execution-service, agent-orchestrator, MTDS, and deployment-service already shipped.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [utl, uac, consolidation, refactor, cloud-sdk, split]
related: [plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
locked_by: live-defi-rollout
locked_since: "2026-07-13"
supersedes:
superseded_by:
depends_on:
source: [split from utl_uac_reuse_consolidation_remediation_2026_06_10 tracker, operator-approved 2026-07-13]
assigned_role: backend-engineer
drift_direction: advance-code
---

# UTL/UAC reuse consolidation — Phase 5 cloud-SDK-direct → UTL cloud_interface (deployment-api remainder)

> **Split provenance (2026-07-13):** Phase 5 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md)
> (findings #6, #7, #9, #12). execution-service, agent-orchestrator, market-tick-data-service, and deployment-service
> (scripts half) already shipped — reproduced below as done. Only deployment-api's routes half remains. Independent of
> every other split plan — no gate.

## Todos

- [x] ✅ [AGENT] P1. **execution-service** — DONE `execution-service@b7ea5e725` (116 custody + 24 AMM tests ✓, QG 0).
      `custody/cloud_kms.py` + `custody/withdrawal_signing.py` secret-fetch → UTL `get_secret_client()` (KMS Decrypt
      kept local); `providers/solana_amm_depth_provider.py` GCP-only `gcs.Client` blob loop → UTL `get_storage_client()`
      (now cloud-agnostic / AWS-safe). Tests updated to the `SecretClient` interface.
- [x] ✅ [AGENT] P1. **(SHIPPED `agent-orchestrator@62894565` 2026-06-22)** **agent-orchestrator**: `server/gcs_sync.py`
      raw `boto3`+`google.cloud.storage` → UTL `get_storage_client(provider="gcp"|"aws")` (GCS+S3 dual-mirror preserved
      via explicit per-provider clients; `upload_bytes`/`upload_file`). `server/auth.py` `_load_gcs_secret` gs:// blob →
      `get_storage_client(provider="gcp", project_id=…).download_bytes()`. HS256/ES256 JWT signing untouched. QG green.
- [x] ✅ [AGENT] P1. **market-tick-data-service** — DONE `market-tick-data-service@696249df` (988 handler tests ✓, QG
      0). Replaced the raw `secretmanager.SecretManagerServiceClient()` + bare-`except` across 9 CLI handlers (11 sites)
      with `from unified_trading_library import get_secret_client` → `.get_secret(name)` (cloud-agnostic, no swallow).
      Tests repointed to the UTL mock.
- [x] ✅ [AGENT] P2. **deployment-service** (scripts half) — DONE `deployment-service@6710f26` (QG 0).
      `scripts/vm/{vm_log_archival_cron,vm_serial_capture_cron,vm_zombie_watchdog,validate_vm_prefix_mapping}.py`
      `storage.Client()` → UTL `get_storage_client()`/`upload_to_storage`/`storage_exists`/`gcs_copy_object`;
      `compute_v1` control-plane kept.
- [x] ✅ [AGENT] P2. **deployment-api** (routes half) — DONE `deployment-api@cb16bc0`. `routes/builds_history.py`
      `_live_entries()` tarball-metadata lookup: `google.cloud.storage.Client()` → UTL
      `get_storage_client(provider="gcp").get_blob_metadata()`. `services/shard_detail/_shard_read.py`
      `_parquet_signed_url()` (post-split home of the former `shard_detail.py:828` site): raw
      `storage.Client().bucket().blob().generate_signed_url()` → UTL `generate_download_url()`. `builds.py` carries no
      `storage.Client()` site (only Artifact Registry + ECR, out of scope). `compute_v1` + pubsub/secretmanager liveness
      probes untouched.
- [x] ✅ [VERIFY] P1. `deployment-api@cb16bc0` — `quality-gates.sh` green (sentinel matches HEAD); 62 targeted unit
      tests (`test_builds_history.py` + `test_shard_detail_service.py`) pass; shipped via quickmerge.

## Success criteria

No `boto3`/`google.cloud`/raw `secretmanager` in service runtime of the 4 repos (scripts tail tracked separately in
Phase 7).

## Notes for the worker

- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
