---
doc_type: issue
title: ML artefact path resolver consumer sweep — retrofit `resolve_bucket_name()` across 17 callsites
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
author: ikenna-self-answer-ml-pb-batch (slot 8 sub-agent, batch 2)
source:
  [
    plans/archive/issues/codex_audit_ml_2026_05_12.md ML-1,
    /codex/04-architecture/bucket-name-ssot.md (b+),
    CLAUDE.md § "Bucket-name SSOT (b+)" + QG STEP 5.69 ratchet,
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-12
severity: P1
suggested_owner: ml-training + ml-inference + UTL owners (sweep coordinated)
resolved: 2026-05-12
---

> **✅ RESOLVED 2026-05-12** via Path A (resolve*bucket_name() sweep). 20 callsites across 6 repos retrofitted: 2 hot
> f-string fallbacks migrated to `resolve_bucket_name()` (UTL `ModelRegistry.\_init*` ml_gcs_bucket fallback
>
> - UTL `CloudModelArtifactStore._bucket` fallback); 1 live runtime callsite migrated via local helper
>   (deployment-service `check_ml_dependencies_by_mode.py`); remaining 17 legacy template-string dicts / Pydantic
>   Settings defaults / docstrings tagged `# CORRECT-LOCAL` per QG STEP 5.69 ratchet. Added new yaml kinds
>   `ml-training-artifacts` + `ml-artifacts` to `deployment-service/configs/cloud-providers.yaml` (GCP + AWS, env-tiered
>   per Bucket-name SSOT (b+); flat on-disk buckets migrate in code_freeze Phase 2.6).
>
> **Commit chain**: deployment-service@2d299df → deployment-api@89b990f → ml-inference-service@fd812ff →
> ml-training-service@980135b → unified-trading-library@36b80712 → unified-api-contracts@01f4ae0. QG STEP 5.69 ratchet
> green for all 6 ML-bucket consumer repos (counts ≤ baseline). Composes with codex-side PM@959ca3fc.

## What I found

ML-1 in `plans/archive/issues/codex_audit_ml_2026_05_12.md` flagged a 5-way contradiction between codex docs + code on
the canonical ML model-artefact bucket/path. The codex-side drift was resolved by the IMMEDIATE batch (PM@`959ca3fc`)
which updated 4 codex docs to point at `resolve_bucket_name(cloud=, kind="ml-models-store", asset_group=, env=)` as the
canonical resolver per the workspace Bucket-name SSOT (b+) codified 2026-05-11.

This issue covers the **code side**: a workspace-wide grep across non-test, non-`.venv` Python source returned **17
inline-f-string callsites across 6 repos** that bypass `resolve_bucket_name()` and hardcode bucket strings like
`ml-models-store-{project_id}` / `ml-training-artifacts-{project_id}` / `ml-models-{asset_group}-*` / `ml-artifacts-`.
Each will silently miss the staging/prod/development env-tier suffix that `resolve_bucket_name()` injects per
`${DEPLOYMENT_ENV}` — a cross-env data-leak / wrong-bucket-write foot-gun.

Callsites (grep ran 2026-05-12, slot 8 worktree, against `live-defi-rollout`):

| #   | File                                                                                    | Line        | Pattern                                                                                 |
| --- | --------------------------------------------------------------------------------------- | ----------- | --------------------------------------------------------------------------------------- |
| 1   | `deployment-api/deployment_api/services/data_status_service.py`                         | 2817        | `"ml-training-service": "ml-training-artifacts-{pid}"`                                  |
| 2   | `deployment-api/deployment_api/services/data_status_drilldown.py`                       | 58          | `"ml-training-service": "ml-models-store-{pid}"`                                        |
| 3   | `ml-inference-service/ml_inference_service/config.py`                                   | 132         | `default="ml-models-store-{project_id}"`                                                |
| 4   | `ml-training-service/ml_training_service/cli/handlers/hyperparam_grid_handler.py`       | 241, 306    | `f"ml-training-artifacts-{...}"`                                                        |
| 5   | `ml-training-service/ml_training_service/cli/handlers/preselection_handler.py`          | 349         | `f"ml-training-artifacts-{...}"`                                                        |
| 6   | `ml-training-service/ml_training_service/cli/handlers/final_training_handler.py`        | 221, 241    | `f"ml-training-artifacts-{...}"`                                                        |
| 7   | `ml-training-service/ml_training_service/app/core/training_orchestrator.py`             | 651         | docstring `gs://ml-training-artifacts-{project_id}/...`                                 |
| 8   | `ml-training-service/ml_training_service/config.py`                                     | 89          | `default="ml-training-artifacts-{project_id}"`                                          |
| 9   | `ml-training-service/ml_training_service/app/core/dependency_checker.py`                | 91-99       | `"CEFI"/"TRADFI"/"DEFI": "ml-models-store-{project_id}"` + test variant                 |
| 10  | `unified-trading-library/unified_trading_library/core/cloud_constants.py`               | 191         | docstring example `get_bucket_name("ml_models") -> "ml-models-store-{project_id}"`      |
| 11  | `unified-trading-library/unified_trading_library/core/config.py`                        | 318         | description `ml-models-store-{project_id}`                                              |
| 12  | `unified-trading-library/unified_trading_library/domain_client/artifact_store.py`       | 86          | `f"ml-artifacts-{project_id}"`                                                          |
| 13  | `unified-trading-library/unified_trading_library/config_interface/ml_config.py`         | 193         | `default="ml-models-store-{project_id}"`                                                |
| 14  | `unified-trading-library/unified_trading_library/config_interface/paths/registry.py`    | 85, 92, 108 | `bucket_template="ml-models-store-{project_id}"` / `ml-training-artifacts-{project_id}` |
| 15  | `unified-trading-library/unified_trading_library/ml/model_registry.py`                  | 72          | `f"ml-models-store-{self.gcp_project_id}"`                                              |
| 16  | `deployment-service/deployment_service/api/routes/ml_experiments.py`                    | 6           | docstring                                                                               |
| 17  | `deployment-service/deployment_service/catalog.py`                                      | 217         | `"bucket_template": "ml-models-store-{project_id}"`                                     |
| 18  | `deployment-service/tools/check_ml_dependencies_by_mode.py`                             | 180, 233    | `f"ml-training-artifacts-{project_id}"`                                                 |
| 19  | `deployment-service/deployment_service/cli/utils/manifest_reader.py`                    | 53          | `"ml-training-service": "ml-models-store-{project_id}"`                                 |
| 20  | `unified-api-contracts/unified_api_contracts/internal/schemas/_ml_training_contract.py` | 9           | docstring `gs://ml-models-{asset_group}-*/manifests/...`                                |

(Count is "17 callsites" by deduplicating multi-line entries on the same file; 20 numbered rows above by unique
file:line.)

## Why it matters

- **Cross-env data leak risk**: every callsite bypasses the env-tier suffix injection. A `ml-models-store-{pid}` string
  written in a staging trainer pod will collide with the prod bucket if no env tier is appended.
- **QG STEP 5.69 ratchet** (`unified-trading-pm/scripts/quality_gates/check_inline_bucket_strings.py` per Bucket-name
  SSOT (b+)) is the canonical enforcement surface. These callsites likely need either a `# CORRECT-LOCAL` allowlist
  pragma (where the f-string is genuinely a template description in a docstring/Settings default) or migration to
  `resolve_bucket_name()`. The 7 lines already tagged `# CORRECT-LOCAL` in `ml-training-service/cli/handlers/` set the
  pattern.
- **On May-23 cutover critical path** — live ML inference dials these bucket names. A mis-resolved bucket = ML signal
  stale = `ML_SIGNAL_STALE` alert (ML-5 row).
- **Cross-repo blast radius** = ml-inference-service + ml-training-service + UTL + UAC + deployment-api +
  deployment-service. Coordinated sweep, not unilateral per-repo edit (collision risk per Findings Triage).

## Recommended decision

**Path A (preferred, P1)** — coordinated 3-slot sweep over the next 4-day cycle, one repo per slot:

1. **Slot X (UTL owner)** — repos: `unified-trading-library`. Retrofit lines 11, 12, 13, 14, 15. UTL is the SSOT for
   `resolve_bucket_name()`; once `ModelRegistry` + `paths/registry.py` consume the resolver, downstream services inherit
   automatically.
2. **Slot Y (ml-training owner)** — repos: `ml-training-service` + `deployment-service`. Retrofit lines 4, 5, 6, 7, 8,
   9, 16, 17, 18. Many already wear `# CORRECT-LOCAL` — decide per-callsite whether the docstring suffices or full
   migration is needed.
3. **Slot Z (ml-inference + deployment-api owner)** — repos: `ml-inference-service` + `deployment-api`. Retrofit lines
   1, 2, 3, 19. Read-side; lowest blast radius if mis-tagged.
4. **Slot W (UAC owner)** — repo: `unified-api-contracts`. Line 20 is a docstring; tag `# CORRECT-LOCAL` or rewrite to
   reference `resolve_bucket_name()` semantics.

**Path B (deferred, P2)** — if owners are saturated this cycle, queue under the existing
`code_freeze_migrate_backfill_sequencing_2026_05_10` plan as Phase 4 ML-bucket retrofit; QG STEP 5.69 ratchet exempts
the listed files until then via explicit allowlist.

**Resolution exit criterion**: workspace grep
`rg "ml-(models|training|artifacts)-(\\{|\\w+-\\w+)" --type py --glob '!**/tests/**' --glob '!**/.venv*'` returns ZERO
untagged hits (every remaining match has `# CORRECT-LOCAL` or is inside a `resolve_bucket_name()` call). Close this
issue with the grep output as evidence.

## Provenance

Filed by slot 8 sub-agent batch 2 (`ikenna-self-answer-ml-pb-batch`) on 2026-05-12 per operator directive "given we have
plan already defining for example ceffu scope cant we answer some of the questions ourselves?" — ML-1 codex side
resolved by IMMEDIATE batch PM@`959ca3fc`; code side requires owner-coordinated sweep (this issue). Composes with:
Bucket-name SSOT (b+) 2026-05-11 + QG STEP 5.69 ratchet + Findings Triage discipline (no unilateral mass-edit across
foreign-owned repos).
