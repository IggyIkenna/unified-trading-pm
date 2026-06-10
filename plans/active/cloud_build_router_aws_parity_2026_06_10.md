---
title:
  Cloud-build dual-cloud parity — AWS CodeBuild reaches GCP Cloud Build feature-parity (router + per-repo triggers + ECR
  + in-image QG)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
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

## Phase 1 — make in-image QG ACTUALLY run on both clouds (the shared latent gap) [P1]

> This is the real parity win: today QG is advisory-only on GCP **and** AWS because the script can't find
> `base-service.sh` in the image. The buildspec already mounts PM at `/workspace/unified-trading-pm` and passes
> `-e WORKSPACE_ROOT=/workspace` — the script just ignores it.

- [ ] [SCRIPT] P1. In the `quality-gates.sh` **template** (`scripts/quality-gates-base/` header generator / the
      templated per-repo header), honor a pre-set `WORKSPACE_ROOT`:
      `WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." && pwd)}"`. Harmless locally (env
      unset → git fallback unchanged); in-container the buildspec's `-e WORKSPACE_ROOT=/workspace` is honored →
      `source /workspace/unified-trading-pm/...base-service.sh` resolves → QG RUNS. Target repo: **unified-trading-pm**
      (template) + roll out fleet-wide via the standard template rollout.
- [ ] [SCRIPT] P1. Once QG runs in-container, flip the in-image QG step from advisory (`|| echo`) to **blocking** on
      BOTH `cloudbuild.yaml` (GCP) and `buildspec.aws.yaml` (AWS), and gate `docker push` on it — restoring the "test
      the artifact you deploy, push only if green" contract the file headers claim. Target repos: deployment-service +
      every repo with a build config.
- [ ] [TEST] P1. Add a parity smoke that runs the same image's `quality-gates.sh --no-fix --quick` with
      `WORKSPACE_ROOT=/workspace` + PM mounted, asserting exit 0 (catches the WORKSPACE_ROOT regression on either
      cloud). Target repo: deployment-service (wired into its QG per the peripheral-script rule).

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

- In-image QG **runs and gates** (not advisory) on both clouds; `docker push` blocked on a real QG failure.
- Every buildable repo has both a `cloudbuild.yaml` and a `buildspec.aws.yaml` (or is explicitly marked GCP-only).
- A cross-cloud parity test is green and wired into deployment-service QG.
- `codex/08-workflows/ci-cd-flow.md` documents the dual-cloud flow.

## Temporary states + their canonical follow-up plans

- **In-image QG advisory on both clouds** — TEMPORARY; canonical fix = Phase 1 of THIS plan (honor `WORKSPACE_ROOT` →
  blocking QG + push-gating).
