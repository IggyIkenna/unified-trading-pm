---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 3 ml-service ModelRegistry (EXTEND UTL FIRST)
summary:
  Carry ml-service's load-bearing writegate/manifest/allowlist controls into UTL ModelRegistry (MINOR bump), fix a
  latent manifest-match bug on the way, then delete the local registry + dead TypedDict.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [ml-service, unified-trading-library]
scope: [engineer, admin]
tags: [utl, uac, consolidation, refactor, ml, model-registry, split]
related:
  [
    plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md,
    plans/active/utl_reuse_phase0_guardrails_2026_07_13.md,
  ]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: "2026-07-13"
supersedes:
superseded_by:
depends_on: [utl_reuse_phase0_guardrails_2026_07_13]
gate_on_depends: true
source: [split from utl_uac_reuse_consolidation_remediation_2026_06_10 tracker, operator-approved 2026-07-13]
assigned_role: backend-engineer
drift_direction: advance-code
---

> **Phase 0 SPEC confirmation (2026-07-13, slot 7):** UTL/UAC targets verified accurate against live code
> (`unified_trading_library.ModelRegistry` exists; writegate/manifest/allowlist genuinely absent from UTL — matches
> "carry in" scope; local manifest-match bug at `training/ml/model_registry.py:531,646` confirmed real). One todo below
> was found stale and struck (dead TypedDict already deleted by prior work) — see inline note.

# UTL/UAC reuse consolidation — Phase 3 ml-service ModelRegistry — EXTEND UTL FIRST

> **Split provenance (2026-07-13):** Phase 3 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md)
> (findings #4, #13) — **fully unstarted**, the biggest untouched phase. **Machine-held** until
> [`utl_reuse_phase0_guardrails_2026_07_13.md`](utl_reuse_phase0_guardrails_2026_07_13.md) lands its golden
> inference-date-selection fixture (`depends_on` + `gate_on_depends: true`).

> **Verified reality:** walk-forward selection (`get_model_for_inference_date`) and the GCS storage layout /
> MANIFEST_PATH are **byte-identical** between local and UTL — zero reconciliation needed there. BUT local carries
> load-bearing controls UTL lacks, and local has a latent bug UTL does not.

## Todos

- [x] ✅ [AGENT] P0. **Carry into UTL `ModelRegistry` (ship UTL MINOR bump first):** — DONE
      `unified-trading-library@7e4f9a23`.
  - [x] ✅ `store_model` writegate — `training_completeness_fraction` param +
        `_check_emission_policy`/`publish_with_policy` BLOCK_CRITICAL gate (suppresses partial-coverage model writes +
        P0 alert). Data-correctness invariant. Extracted into `_emission_gate()` to stay under the 50-line method limit.
  - [x] ✅ `store_model` availability-manifest emission — `ManifestWriter.add(...).write()` with `job_id`, via
        `_emit_availability_record()` (best-effort, non-fatal on failure).
  - [x] ✅ `load_model` joblib **trusted-prefix allowlist** (`_ALLOWED_JOBLIB_PREFIXES`) — kept UTL's `expected_sha256`
        integrity param too (strongest combination = both), enforced in `_deserialize_model`.
- [x] ✅ [AGENT] P0. **Adopt UTL's correct manifest-match — DONE.** `ml-service@3d6fe656` — fixed both bug sites
      (`_get_metadata_from_manifest:531`, `_upsert_version:646`) from `... or training_period == ""` (never actually
      compares the two values — returns/matches the first truthy entry regardless of the requested training_period) to
      UTL's correct `== training_period`. Added 2 regression tests: a multi-entry manifest lookup that returns the entry
      matching the requested period, and an upsert that inserts a new entry for an unseen period instead of overwriting
      an unrelated one (verified fail-before/pass-after via a deliberate temporary revert). Full `tests/training/`
      suite: 1666 passed, 2 skipped. `quality-gates.sh` green, quickmerge landed on `live-defi-rollout`.
- [x] ✅ [AGENT] P0. **Audit the local-only escape hatches before deleting:** `CLOUD_PROVIDER=local` no-bucket guard +
      AWS S3 bucket fallback (`ml_models_s3_bucket`) + `None`-on-miss error contract. If any ml-service test or AWS
      deployment depends on them, add the equivalent local/S3 path to UTL first; else confirm `config.ml_source_bucket`
      is always set on the training path. — AUDITED (2026-07-13, slot-3), all 3 resolved, no UTL extension needed:
  - **`CLOUD_PROVIDER=local` no-bucket guard** — MOOT for UTL. The guard exists because ml-service's `__init__` calls
    UCI's `get_data_sink`/`get_data_source` factories, which auto-upgrade local→gcp whenever a bucket name is supplied.
    UTL's `ModelRegistry` doesn't use those factories at all — it calls `get_storage_client()` / `download_from_storage`
    / `upload_to_storage` directly (`unified_trading_library/cloud_interface/factory.py`), which resolves the provider
    via `get_cloud_provider()` cleanly regardless of whether a bucket is passed. No action needed.
  - **AWS S3 bucket fallback** — test-covered but NOT production-live. 3 ml-service test files
    (`tests/training/unit/test_model_registry_utils.py::test_uses_aws_bucket_when_cloud_provider_is_aws`,
    `tests/training/unit/test_model_registry_coverage.py::test_uses_aws_s3_bucket_when_configured`,
    `tests/training/test_model_registry_full.py`) exercise `cloud_provider="aws"` + `ml_models_s3_bucket`, but
    `deployment-service/configs/aws/` has NO `ml-service.yaml` (unlike strategy-service/execution-service/
    features-service/alerting-service/risk-and-exposure-service, which do) — ml-service has never actually been deployed
    to AWS. UTL's `ModelRegistry` resolves its bucket via `resolve_bucket_name(cloud="gcp", ...)` (GCP-only). Decision:
    do NOT carry AWS support into UTL for a capability with zero live deployment — delete the 3 AWS-path tests as part
    of the local-registry deletion (todo below) instead of blocking on unneeded UTL work. If ml-service is ever deployed
    to AWS, extend `resolve_bucket_name` with an AWS kind mapping then (same pattern other AWS-deployed services already
    use), not before.
  - **`None`-on-miss error contract** — ALREADY equivalent. UTL's `load_model`/`get_model_metadata`/
    `get_model_for_inference_date` all `return None` on miss (never raise), matching the local registry's contract
    exactly. No action needed.
  - **`config.ml_source_bucket` always set on the training path** — confirmed: UTL resolves
    `ml_gcs_bucket or unified_config.ml_gcs_bucket or resolve_bucket_name(cloud="gcp", kind="ml-models-store")`, so the
    training path always has a concrete bucket with no local-only special-casing required.
- [ ] [AGENT] P0. Delete `ml_service/training/ml/model_registry.py`; repoint `training_orchestrator.py`,
      `final_training_handler.py`, `model_loader.py` (loader already uses UTL) to
      `from unified_trading_library import ModelRegistry`. Also delete the 3 AWS-path tests identified in the audit
      above (`test_uses_aws_bucket_when_cloud_provider_is_aws`, `test_uses_aws_s3_bucket_when_configured`, and the AWS
      case in `test_model_registry_full.py`) — they test a capability with no live UTL equivalent and no live AWS
      deployment; do not carry them forward as skipped/xfail (CLAUDE.md "delete deprecated code", no shims).
- [x] ✅ [AGENT] P1. ~~Delete the **dead** `inference/types.py:ModelMetadata` TypedDict~~ — **already done**, verified
      stale during Phase 0 SPEC confirmation (2026-07-13): `ml-service@00855f6` ("schema-provenance class cleared
      honestly … 4 dead TypedDicts deleted") already removed this TypedDict;
      `grep -rn "class ModelMetadata"     ml_service/` returns no hits. No action needed at Phase 3 execution time.
- [ ] [VERIFY] P0. Golden inference-date selection fixture reproduces; writegate still blocks a partial-coverage write;
      `quality-gates.sh` green for UTL + ml-service; quickmerge.

## Success criteria

UTL `ModelRegistry` carries writegate+manifest+allowlist; local registry + dead TypedDict deleted; manifest-match bug
gone.

## Notes for the worker

- **MINOR-bump-first ordering:** this phase adds to UTL — ship the lib bump, let the range-pin pull carry it, then
  migrate ml-service. Don't edit consumer + lib in a way that needs a coordinated MAJOR.
- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
