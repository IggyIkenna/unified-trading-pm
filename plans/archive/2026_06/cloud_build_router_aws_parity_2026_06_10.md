---
title:
  Cloud-build dual-cloud parity — AWS CodeBuild reaches GCP Cloud Build feature-parity (router + per-repo triggers + ECR
  + in-image QG)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: archived
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
created: 2026-06-10
locked_by: live-defi-rollout
related_plans:
  - plans/active/cicd_contract_hardening_2026_06_01.md
  - plans/active/issues/ci_incident_findings_2026_06_09.md
source:
  - chat/2026-06-10 operator:
      "what about code builds for aws do we have this workflow generally working identically e2e?"
---

> **🗄️ ARCHIVED 2026-06-18 — superseded by the cicd consolidation; any open items were migrated to the 4 themed plans
> (promotion-pipeline / quality-gates / sit-and-fleet / release-machinery). Disposition + provenance:
> `plans/active/cicd_docs_and_consolidation_2026_06_18.md`.**

# Cloud-build dual-cloud parity — AWS CodeBuild ≡ GCP Cloud Build

> **Premise (operator, 2026-06-10):** the firm runs **GCP primary / AWS secondary** (CLOUD_PROVIDER switches at
> runtime). Image builds must work **identically e2e on both clouds** — same trigger semantics, same in-image quality
> gates, same registry-push gating, same provenance dispatch — so a cloud failover does not silently lose CI coverage.
> Today GCP is the mature path (`cloud-build-router.yml` → per-repo `cloudbuild.yaml` → Artifact Registry) and AWS is a
> partial, drifted twin (per-repo `buildspec.aws.yaml` + a few CodeBuild projects, NO router, NO parity tests).

## What I found (audit 2026-06-10)

| Capability                    | GCP (mature)                                                                                                | AWS (today)                                                                                            | Gap                                                                                                      |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| Build orchestration / routing | `cloud-build-router.yml` (repository_dispatch → `gcloud builds triggers run`, manifest-derives `repo_type`) | **none** — each repo's CodeBuild project has its own GitHub PUSH webhook on `live-defi-rollout`        | No central AWS router; fan-out + repo_type derivation not mirrored                                       |
| Per-repo build config         | `cloudbuild.yaml` in every buildable repo                                                                   | `buildspec.aws.yaml` in **only a subset** (deployment-service, instruments-service confirmed)          | Missing buildspecs fleet-wide; no generator/template                                                     |
| In-image quality gates        | Step 4, **advisory** (`\|\| echo`) — base-service.sh not in docker context                                  | BUILD-phase QG, was **blocking → exit 127** (fixed to advisory 2026-06-10 @deployment-service 2077ecb) | Both clouds run QG ADVISORY only; neither actually gates on it (WORKSPACE_ROOT not honored in-container) |
| Registry push gating          | push `waitFor: [quality-gates]` (advisory step always green → always pushes)                                | `docker push` after advisory QG (always pushes)                                                        | Push is NOT gated on QG on EITHER cloud — shared latent gap                                              |
| Provenance dispatch           | `service-deployed` repository_dispatch on success                                                           | same dispatch present in buildspec post_build                                                          | OK (parity)                                                                                              |
| Registry                      | Artifact Registry `unified-trading-library`                                                                 | ECR per-repo (`create-repository` on demand)                                                           | OK functionally; no cross-cloud digest parity check                                                      |
| Parity tests                  | n/a                                                                                                         | **none**                                                                                               | No test asserts the two clouds build the same artifact / run the same gates                              |

**Root finding:** AWS is not "broken" so much as **incomplete + drifted**. The deployment-service exit-127 (fixed
separately — see Phase 0) was the visible symptom; the structural gap is (a) no AWS router, (b) buildspecs only in a
subset of repos with no generator, (c) **in-image QG is advisory on BOTH clouds** because `quality-gates.sh` re-derives
`WORKSPACE_ROOT` from `git rev-parse` which fails inside the image — so the "test the artifact you deploy" promise is
not actually kept on either cloud.

## Phase 0 — deployment-service AWS red (DONE 2026-06-10, the trigger for this plan)

- [x] [CI] P0. Fix deployment-service `buildspec.aws.yaml` exit-127 — BUILD-phase QG guarded advisory (parity with
      cloudbuild.yaml step 4); POST_BUILD `uv pip install` → `python -m pip` gated under `CODEARTIFACT_DOMAIN` (uv not
      in CodeBuild env). — deployment-service@2077ecb | webhook re-triggered CodeBuild on the fixed sha.

> **🔎 Audit callout (CI/CD drift audit 2026-06-17 — D11 RESOLVED 2026-06-17 (drop, see Phase 1 below); D14 recorded):**
>
> - **D11 — reconcile Phase 1 against a since-shipped decision.** `gcp_cloudbuild_sibling_context_staging_2026_06_15`
>   (RESOLVED 2026-06-15) shipped `_RUN_INIMAGE_QG: false` to the sibling-COPY repos, deciding in-image QG is
>   **redundant** (the LDR→staging `quality-gates-v2` already gates before the build) **and impossible** (no
>   `unified-trading-pm` harness in the image → `exit 127`). That contradicts Phase 1's goal of making in-image QG
>   _run + gate_ on both clouds. **Decide before actioning Phase 1:** keep in-image QG (then Phase 1 must also solve the
>   harness-in-image problem the issue declared unsolvable) **or** treat the pre-build CI gate as sufficient (then
>   re-scope Phase 1 to drop in-image QG and assert the pre-build gate covers both clouds).
> - **D14 — the AR-publish gate already exists but is UNWIRED.** `scripts/cicd/assert_deps_published_to_ar.py` is
>   written (asserts internal deps are published to Artifact Registry at their declared floor) but its own STATUS
>   comment (2026-06-16) says it is **NOT wired into any workflow** — reserved for a production image-build dep-publish
>   gate that has not launched. If this plan's registry-push-gating work needs an AR-publish precondition, **wire this
>   script** rather than writing a new one.

## Phase 1 — in-image QG: DROPPED (DECISION 2026-06-17, operator) [RESOLVED]

> **DECISION 2026-06-17 (operator — D11 from the CI/CD drift audit
> `plans/audit/results/cicd_pipeline_vs_plans_drift_audit_2026_06_17.md`): drop in-image QG entirely.** Rationale: it
> re-runs gates the code already passed **twice** before the image is built (quickmerge Pass-1 locally + the LDR→staging
> `quality-gates-v2` PR gate), so it is **redundant**; and the harness isn't in the image (no `unified-trading-pm` →
> `exit 127`), so making it blocking would mean permanently mounting the PM harness + siblings into every build for
> ~zero gain. **`_RUN_INIMAGE_QG: false`** (shipped fleet-wide by `gcp_cloudbuild_sibling_context_staging_2026_06_15`)
> is now the **canonical** state. The **authoritative QG is the pre-build `quality-gates-v2` PR gate**; the image build
> just builds + pushes. The genuinely-valuable part of "test the artifact you deploy" — an **image-boot smoke** (does
> the container start + import / health-check, catching a bad `uv sync` / missing runtime dep / broken entrypoint that
> lint/type/test never would) — is owned by the **build-images workstream (separate agent)**, so it is intentionally NOT
> a todo here.

- [x] ✅ **DROPPED — in-image QG `WORKSPACE_ROOT`-honoring** (was: make `quality-gates.sh` resolve its harness
      in-container). Superseded by the drop decision; `_RUN_INIMAGE_QG: false` stands.
- [x] ✅ **DROPPED — flip in-image QG to blocking + gate `docker push`.** Superseded; the pre-build `quality-gates-v2`
      PR gate is the authoritative gate.
- [x] ✅ **DROPPED — in-image-QG parity smoke** (re-running `quality-gates.sh` in-image). Replaced by the image-boot
      smoke owned by the build-images workstream — a boot/import check, NOT a QG re-run.

## Phase 2 — AWS build router (mirror cloud-build-router) [P2]

- [ ] [SCRIPT] P2. Author an AWS build router equivalent of `cloud-build-router.yml`: a `repository_dispatch`-driven GHA
      job (or a single CodeBuild "router" project) that, given `{repo, repo_type}`, starts the per-repo CodeBuild
      project — deriving `repo_type` from `workspace-manifest.json` when the payload omits it (same jq logic already
      added to cloud-build-router.yml). Decide router-in-GHA vs router-as-CodeBuild (BLOCKED-OPERATOR-DECISION if
      cost/latency trade-off is unclear). Target repo: **unified-trading-pm** (`.github/workflows/`).
- [ ] [SCRIPT] P2. Mirror the GCP `notify-build-not-configured` gating (prod-only) into the AWS router so non-prod /
      unconfigured repos no-op quietly instead of paging. Target repo: unified-trading-pm.

## Phase 3 — buildspec generator + fleet coverage [P2]

- [ ] [SCRIPT] P2. Add a `buildspec.aws.yaml` generator/template (parallel to however `cloudbuild.yaml` is templated) so
      every buildable repo gets a consistent AWS buildspec; generate the missing ones. Inventory: grep repos with
      `cloudbuild.yaml` but no `buildspec.aws.yaml`. Target repo: unified-trading-pm template + per-repo rollout.
- [ ] [SCRIPT] P3. Replace the per-repo CodeBuild GitHub PUSH webhook with router-driven starts (Phase 2) for
      consistency with the GCP dispatch model, OR document the webhook model as the intentional AWS-side trigger. Target
      repo: deployment-service/terraform/aws + unified-trading-pm.

## Phase 4 — cross-cloud parity tests [P2]

- [ ] [TEST] P2. A parity test asserting: (a) both clouds build from the same Dockerfile + `PROJECT_ID` arg, (b) both
      run the same `quality-gates.sh` invocation, (c) both push a tag derivable from `pyproject.version`, (d) both fire
      the `service-deployed` provenance dispatch. Lives in deployment-service QG (primary consumer). Target repo:
      deployment-service.
- [ ] [DOC] P2. Codex SSOT: write/extend `codex/08-workflows/ci-cd-flow.md` § "Dual-cloud image builds" documenting the
      router → buildspec → in-image-QG → registry-push → provenance flow for BOTH clouds, with the GCP/AWS parity table.

## Codex SSOT updates (HARD RULE — enumerated)

- `codex/08-workflows/ci-cd-flow.md` — new § "Dual-cloud image builds (GCP Cloud Build ≡ AWS CodeBuild)".
- `codex/05-infrastructure/` — if an AWS router project is added, document its identity + trigger semantics.

## Success criteria

- In-image QG is **dropped** (`_RUN_INIMAGE_QG: false` canonical on both clouds, DECISION 2026-06-17); the pre-build
  `quality-gates-v2` PR gate is the authoritative QG. Deploy-artifact safety is covered by the image-boot smoke (owned
  by the build-images workstream), NOT by re-running QG in-image.
- Every buildable repo has both a `cloudbuild.yaml` and a `buildspec.aws.yaml` (or is explicitly marked GCP-only).
- A cross-cloud parity test is green and wired into deployment-service QG.
- `codex/08-workflows/ci-cd-flow.md` documents the dual-cloud flow.

## Temporary states + their canonical follow-up plans

- ~~In-image QG advisory on both clouds~~ — **RESOLVED 2026-06-17: dropped** (`_RUN_INIMAGE_QG: false` canonical; the
  pre-build `quality-gates-v2` PR gate is authoritative). No longer a temporary state. See Phase 1.
