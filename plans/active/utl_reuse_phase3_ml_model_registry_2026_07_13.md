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

- [ ] [AGENT] P0. **Carry into UTL `ModelRegistry` (ship UTL MINOR bump first):**
  - [ ] `store_model` writegate — `training_completeness_fraction` param +
        `_check_emission_policy`/`publish_with_policy` BLOCK_CRITICAL gate (suppresses partial-coverage model writes +
        P0 alert). Data-correctness invariant.
  - [ ] `store_model` availability-manifest emission — `ManifestWriter.add(...).write()` with `job_id`.
  - [ ] `load_model` joblib **trusted-prefix allowlist** (`_ALLOWED_JOBLIB_PREFIXES`) — keep UTL's `expected_sha256`
        integrity param too (strongest combination = both).
- [ ] [AGENT] P0. **Adopt UTL's correct manifest-match** — local `get_model_metadata`/`_upsert_version` test
      `... or training_period == ""` (`:531`,`:646`) returns the WRONG version from cache; UTL's `== training_period` is
      correct. Consolidating onto UTL **fixes** this for ml-service.
- [ ] [AGENT] P0. **Audit the local-only escape hatches before deleting:** `CLOUD_PROVIDER=local` no-bucket guard + AWS
      S3 bucket fallback (`ml_models_s3_bucket`) + `None`-on-miss error contract. If any ml-service test or AWS
      deployment depends on them, add the equivalent local/S3 path to UTL first; else confirm `config.ml_source_bucket`
      is always set on the training path.
- [ ] [AGENT] P0. Delete `ml_service/training/ml/model_registry.py`; repoint `training_orchestrator.py`,
      `final_training_handler.py`, `model_loader.py` (loader already uses UTL) to
      `from unified_trading_library import ModelRegistry`.
- [ ] [AGENT] P1. Delete the **dead** `inference/types.py:ModelMetadata` TypedDict (no importers; the live
      `ModelMetadata` everywhere is the UTL dataclass).
- [ ] [VERIFY] P0. Golden inference-date selection fixture reproduces; writegate still blocks a partial-coverage write;
      `quality-gates.sh` green for UTL + ml-service; quickmerge.

## Success criteria

UTL `ModelRegistry` carries writegate+manifest+allowlist; local registry + dead TypedDict deleted; manifest-match bug
gone.

## Notes for the worker

- **MINOR-bump-first ordering:** this phase adds to UTL — ship the lib bump, let the range-pin pull carry it, then
  migrate ml-service. Don't edit consumer + lib in a way that needs a coordinated MAJOR.
- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
