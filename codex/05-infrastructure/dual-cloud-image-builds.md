---
doc_type: codex-ssot
title: Dual-cloud image builds — SSOT
summary:
  SSOT for the dual-cloud Docker image build flow — a qg-passed dispatch fanning out to parallel GCP (Cloud Build →
  Artifact Registry) + AWS (CodeBuild → ECR) routers, per-repo buildspec.aws.yaml, the staging→main promote gate (both
  clouds must pass, soft-pass when a project is not-configured), the cross-cloud parity QG, and deployed_versions
  provenance in the workspace manifest.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, execution-service, unified-trading-library, unified-trading-pm, unified-trading-ci]
scope: [admin, engineer]
tags: [ci-cd, migration, aws-migration, infrastructure]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/05-infrastructure/cloud-agnostic-build-lineage.md,
  ]
created: 2026-06-27
authoritative_for:
  ["dual-cloud image build flow (GCP Cloud Build + AWS CodeBuild routers, buildspec, promote gate, provenance)"]
referenced_by: [/codex/05-infrastructure/cicd-setup.md]
owner:
last_reviewed: 2026-08-08
code_refs:
  [
    .github/workflows/cloud-build-router.yml,
    .github/workflows/cloud-build-router-aws.yml,
    execution-service/cloudbuild.yaml,
    market-tick-data-service/cloudbuild.yaml,
  ]
---

# Dual-cloud image builds — SSOT

> **Applies to**: every service repo that ships a Docker image (service and library repos). This document is the
> authoritative reference for the full build flow: push → router → buildspec → registry → promote gate → provenance.

## Overview

Image builds run on **both GCP (Cloud Build + Artifact Registry)** and **AWS (CodeBuild + ECR)** in parallel. The two
clouds fire from the same `repository_dispatch: qg-passed` event and produce equivalent images. Neither cloud's build
result blocks the other from triggering, but both must pass before a staging→main promote PR is merged.

```
LDR push
  └─ quality-gates-v2.yml passes
       └─ dispatches repository_dispatch {type: qg-passed, repo, branch, version, sha}
            ├─ cloud-build-router.yml (GCP)  →  Cloud Build <repo>-build/-main-deploy/-prod/-live-defi-rollout  →  Artifact Registry
            └─ cloud-build-router-aws.yml (AWS) →  CodeBuild <repo>  →  ECR (ap-northeast-1)
```

> **CORRECTED 2026-08-08** (`ui_satellite_ao_dispatch_batch1-003`, source:
> `artifact_pipeline_observability_2026_07_17.md` Phase 5) — 5 named drifts fixed below, each with fresh 2026-08-08
> evidence re-measured against live GCP/AWS state (not just re-trusting the 2026-07-17 finding): registry name, tag
> convention, trigger/project naming, the canonical-trigger claim, and empty-manifest provenance. A standard post-phase
> codex audit of the rest of this doc while touching it turned up 2 more stale sections (the `live-defi-rollout`
> branch-trigger claim, and the reusable validate workflow's repo location) — also corrected below.

```
staging→main promote PR
  └─ image-build-gate.yml (per-service, template)
       └─ image-build-validate.yml (PM reusable)
            ├─ build-gcp job  →  Cloud Build (GCP)
            └─ build-aws job  →  CodeBuild (AWS)
                 └─ gate job  →  fails PR if either cloud fails
```

---

## GCP side

### Router

`unified-trading-pm/.github/workflows/cloud-build-router.yml` — triggered by `repository_dispatch: qg-passed`.

- Derives `repo_type` from `workspace-manifest.json` when absent from payload.
- Routes to trigger `<repo>-<env>` where `env` is derived from branch (`main`→`prod`, `staging`→`staging`, else→`dev`) —
  but see "Build trigger naming" below: the trigger this ATTEMPTS to run and the trigger that ACTUALLY EXISTS in GCP
  often differ, because the fleet is pre-live-cutover and most repos only have a build-only trigger provisioned, not a
  full `<repo>-<env>` matrix. No separate `-wheel-<env>` naming exists for library repos (CORRECTED 2026-08-08 — see
  below).
- Freeze-check via `change-freeze-check.yml` reusable; defers on freeze instead of running.
- ~~On success: updates `deployed_versions[<repo>]` in `workspace-manifest.json`.~~ **REMOVED 2026-08-10** — the
  provenance write was dead code (write step never fired; `permissions: contents: read` blocked the push; manifest field
  never populated). Retired per `infra_satellite_ao_dispatch_batch9_2026_08_09.md` todo 4. Read Firestore `ci_status`
  for live deploy state.
- `CLOUD_BUILD_PROD_DEPLOY_EXPECTED` repo variable gates `notify-build-not-configured` alerts (avoids pre-cutover
  noise).

### Registry

- **Artifact Registry host**: `asia-northeast1-docker.pkg.dev`
- **Project**: `central-element-323112`
- **Repository**: **`unified-trading-system`** (CORRECTED 2026-08-08 — was wrongly documented as `unified-trading`,
  which returns `NOT_FOUND`; re-verified live:
  `gcloud artifacts repositories describe unified-trading-system --project=central-element-323112 --location=asia-northeast1`
  → exists, ~145 GB as of 2026-08-08. Every per-repo `cloudbuild.yaml`'s `_REGISTRY_REPO` substitution defaults to
  `unified-trading-system` — confirmed fleet-wide, e.g. `execution-service/cloudbuild.yaml:41`,
  `market-tick-data-service/cloudbuild.yaml:41`. The PM's own `scripts/propagation/templates/cloudbuild.yaml` template
  still hardcodes the stale `unified-trading` name in its `_AR_REPO` substitution default — that template drift is
  tracked as a follow-up, see `codex_drift_followups_dual_cloud_image_builds_2026_08_08.md`.)
- **Image URI format**: `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/<repo>:<tag>` —
  see "Image tag convention" below for what `<tag>` actually is.
- **Region**: `asia-northeast1`

### Image tag convention (CORRECTED 2026-08-08 — was: "images tagged `:<version>`")

Every GCP build **always** pushes two tags: `:$SHORT_SHA` (Cloud Build's built-in short commit SHA) and `:latest`. It
**additionally** pushes a `:<version>` tag (e.g. `0.47.0`) derived at build time from `git describe --tags --match 'v*'`
(falling back to the latest `v[0-9]*` tag, then `pyproject.toml`'s `version`, then `0.0.0.dev0`) — this is a DIFFERENT
mechanism than the router's own `client_payload.version` field, which the semver-agent no longer populates (confirmed
dead 2026-07-24, SHA-only tagging from that path is intentional). Verified live 2026-08-08:
`gcloud artifacts docker images list .../unified-trading-system/execution-service --include-tags` shows recent images
tagged both `0.47.0,7949f58,latest` (a version-bump build) and bare SHA-only (e.g. `8d1ff65`) for builds where the
derived version didn't change. Confirmed fleet-consistent via `execution-service/cloudbuild.yaml` and
`market-tick-data-service/cloudbuild.yaml`.

### Build trigger naming (CORRECTED 2026-08-08 — was: "`<repo>-<env>`" for both GCP triggers and AWS projects)

Live GCP trigger names (`gcloud builds triggers list --project=central-element-323112 --region=asia-northeast1`,
re-verified 2026-08-08) do NOT follow a uniform `<repo>-<env>` pattern. Actual naming observed across the fleet:

- `<repo>-build` — the default pre-cutover build-only trigger (most repos, e.g. `execution-service-build`,
  `instruments-service-build`).
- `<repo>-feature-build` — `feat/*` branches (created by `scripts/create-cloud-build-feature-triggers.sh`, e.g.
  `execution-service-feature-build`).
- `<repo>-main-deploy` — a prod-deploy trigger naming variant used by some repos (e.g. `deployment-api-main-deploy`,
  `deployment-ui-main-deploy`).
- `<repo>-prod` — the prod-deploy naming variant used by other repos (e.g. `instruments-service-prod`,
  `unified-trading-library-prod`) — see `notify-build-not-configured`'s own comment in `cloud-build-router.yml` for the
  pre-cutover build-only rationale.
- `<repo>-live-defi-rollout` — an LDR-specific trigger provisioned for a subset of repos (e.g.
  `market-tick-data-service-live-defi-rollout`, `unified-api-contracts-live-defi-rollout`,
  `unified-trading-library-live-defi-rollout`) — see "GCP `live-defi-rollout` branch trigger", also corrected below.
- No separate `-wheel-<env>` naming exists for library repos — `unified-trading-library` and `unified-api-contracts` use
  the same trigger-name families as service repos.

**AWS CodeBuild project naming**: the 2026-07-17 finding states AWS projects are bare `<repo>` (not `<repo>-<env>`).
**Not independently re-verifiable from this worker's identity** (`ikenna-worker` lacks `codebuild:ListProjects`, and IAM
introspection/self-grant on that identity is out of scope — the documented AO self-service identity is the separate
`uts-orchestrator-epic-role`, see `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`); retained on
the strength of the original dated measurement, flagged as unverified-this-pass in the follow-up issue doc.

---

## AWS side

### Router

`unified-trading-pm/.github/workflows/cloud-build-router-aws.yml` — fires from the same `qg-passed` dispatch event as
the GCP router.

- Auth: OIDC via `aws-actions/configure-aws-credentials@v4`; role ARN from `secrets.AWS_BUILD_ROLE_ARN`.
- Routes to CodeBuild project `<repo>-<env>` per the router's own code — but per the 2026-07-17 finding the live project
  names are bare `<repo>` with no `-<env>` suffix (unverified this pass, see "Build trigger naming" above).
- Polls build status via `aws codebuild batch-get-builds` (60×30s = 30 min max).
- `ResourceNotFoundException` → detected as "not configured" → soft notification (same gating as GCP side).
- ~~On success: updates `deployed_versions_aws[<repo>]` in `workspace-manifest.json`.~~ **REMOVED 2026-08-10** — same
  dead-code retirement as the GCP side (see the GCP bullet above; `infra_satellite_ao_dispatch_batch9_2026_08_09.md`
  todo 4).

### Registry

- **ECR host**: `427895769566.dkr.ecr.ap-northeast-1.amazonaws.com`
- **AWS account**: `427895769566`
- **Region**: `ap-northeast-1`
- **Image URI format**: `427895769566.dkr.ecr.ap-northeast-1.amazonaws.com/<repo>:<version>` — per
  `deployment-service/templates/buildspec.aws.yaml`, the AWS build tags `:$VERSION` and `:latest` (no `:$SHORT_SHA` tag
  on the AWS side — that convention is GCP-only, see "Image tag convention" above).

**ECR target decision (2026-06-27)**: ECR target matches the AWS account `427895769566` in `buildspec.aws.yaml` files
and the live AWS account constant in workspace configs. No TF divergence identified; this is the live target. Decision:
use as-is, no reconciliation or retirement required.

### Build project naming

Documented as `<repo>-<env>` for services, `<repo>-wheel-<env>` for libraries — but per the 2026-07-17 finding, live AWS
project names are bare `<repo>` with no env/wheel suffix (see "Build trigger naming" above; not independently
re-verifiable this pass).

### Build trigger model (CORRECTED 2026-08-08 — was: "router is the canonical AWS trigger", unqualified)

**Router-driven (primary, by decision)**: the GHA router triggers CodeBuild via `aws codebuild start-build`. CodeBuild
webhook triggers (PUSH events from GitHub) are a secondary/legacy model that should be migrated away from — but the
2026-07-17 finding measured a REAL build whose `initiator` field read `GitHub-Hookshot`, i.e. a webhook fired that build
directly, not the router. So "canonical" here describes the operator's decision (2026-06-27) about which path SHOULD be
used, not a live guarantee that only the router ever fires a build — webhook-triggered builds do occur in practice on
any project where a PUSH webhook is still configured alongside the router.

**Webhook model decision (2026-06-27)**: the GHA router is the intended canonical build-trigger path, consistent with
GCP's router pattern. CodeBuild PUSH webhooks, if configured on any project, fire in addition to (or instead of, per the
finding above) the router call — redundant-when-both-fire, not harmful (idempotent image builds), but NOT "canonical
source of truth for build provenance via the router" today: the router's own provenance-recording
(`deployed_versions_aws`) is not actually happening — see "Provenance" below, corrected 2026-08-08. Do not add new PUSH
webhooks; migrate existing webhook-only projects to router-driven if/when they need provenance tracking.

---

## Per-repo buildspec

### `buildspec.aws.yaml`

Every service repo must have a `buildspec.aws.yaml` at root. The canonical template lives at:

```
deployment-service/templates/buildspec.aws.yaml
```

Generate/update fleet buildspecs by editing the template, then running:

```bash
# Rollout is idempotent — safe to re-run.
bash scripts/workflow-templates/rollout-workflow-templates.sh --template buildspec.aws.yaml
```

**Key conventions**:

- Python installs use `python -m pip install`, NOT `uv pip install` — `uv` is not available in the CodeBuild default
  Python 3.13 runtime. Repos that explicitly install uv first (e.g. `unified-trading-library`) are an explicit
  exception; they install uv via pip before using it.
- The CODEARTIFACT block authenticates to AWS CodeArtifact for private packages; uses
  `python -m pip install build twine` for wheel builds.
- Image push target: `427895769566.dkr.ecr.ap-northeast-1.amazonaws.com/<repo>:<version>` (`:latest` also pushed — see
  "Image tag convention" above).

---

## Staging→main promote gate

### Per-service template

`unified-trading-pm/scripts/workflow-templates/image-build-gate.yml` — rolled out to every repo via the template
mechanism. Creates `.github/workflows/image-build-gate.yml` in each service repo.

Trigger: `pull_request: branches: [main]` — fires on every staging→main promote PR.

Calls: `IggyIkenna/unified-trading-ci/.github/workflows/image-build-validate.yml@main` (CORRECTED 2026-08-08 — found
during this doc's post-phase audit, not one of the 5 named drifts. The doc previously said
`IggyIkenna/unified-trading-pm/.github/workflows/image-build-validate.yml@live-defi-rollout` — the reusable workflow was
extracted out of `unified-trading-pm` into the dedicated `unified-trading-ci` repo on 2026-08-06, per
`scripts/workflow-templates/image-build-gate.yml`'s own comment: "extracted from unified-trading-pm 2026-08-06 so this
workflow keeps resolving even if PM's own visibility changes." Verified live: the file no longer exists at the old PM
path and is present at `unified-trading-ci/.github/workflows/image-build-validate.yml`.)

### Reusable validate workflow

`unified-trading-ci/.github/workflows/image-build-validate.yml` (moved from `unified-trading-pm` 2026-08-06 — see above)

Runs GCP Cloud Build and AWS CodeBuild **in parallel** for the PR head commit, then gates:

- Both clouds must exit 0.
- If either cloud's build project is `not-configured` (trigger/project not found) → **soft-pass** (exit 0). This
  prevents the gate from blocking promote PRs for repos that have not yet had their Cloud Build / CodeBuild projects
  provisioned (pre-cutover safe).
- Outputs: `gcp_build_id`, `gcp_build_exit_code`, `aws_build_id`, `aws_build_exit_code`, `both_passed`.
- GCP auth: WIF preferred, SA key fallback.
- AWS auth: OIDC.

---

## GCP `live-defi-rollout` branch trigger (CORRECTED 2026-08-08 — found during post-phase audit)

**Original decision (2026-06-27)**: GCP opt-in for `live-defi-rollout` branch builds was an operator decision (cost vs.
coverage), stated at the time as "no change to current setup." **That is now stale**: live `gcloud builds triggers list`
(2026-08-08) shows a `<repo>-live-defi-rollout` trigger already provisioned for at least 3 repos —
`market-tick-data-service`, `unified-api-contracts`, `unified-trading-library` — so the opt-in has since happened for a
subset of the fleet, just not fleet-wide. Most repos still only have a `<repo>-build` (pre-cutover build-only) trigger
and no LDR-specific trigger. Treat "which repos have LDR coverage" as a live `gcloud builds triggers list` question, not
this doc's static claim.

---

## Cross-cloud parity test

`deployment-service/scripts/quality_gates/check_dual_cloud_parity.py` — checks that for every service registered in
`workspace-manifest.json`, both `buildspec.aws.yaml` (AWS) and `cloudbuild.yaml` (GCP) exist in the repo, confirming
dual-cloud build coverage.

Run via deployment-service `quality-gates.sh`. A missing buildspec for a registered service fails the gate.

---

## Provenance (RETIRED 2026-08-10 — was: "manifest state is the build-provenance audit trail"; CORRECTED 2026-08-08 to "not functioning")

- ~~GCP: `cloud-build-router.yml` updates `deployed_versions[<repo>]` in `workspace-manifest.json` on success.~~
  **REMOVED 2026-08-10**: the write step was dead code — it never fired (`build_triggered` gate), and even when it would
  fire the workflow's `permissions: contents: read` blocked the `git push origin main` (silently swallowed by
  `|| true`); the manifest field was never populated in 5 months. The step is deleted and the `deployed_versions`
  manifest field is removed.
- ~~AWS: `cloud-build-router-aws.yml` updates `deployed_versions_aws[<repo>]`.~~ **REMOVED 2026-08-10**: same dead-code
  retirement, step + field removed.
- `reconcile_manifest_backmerge.py`'s `_TOPLEVEL_CI_FIELDS` no longer lists `deployed_versions`.

**The manifest is NOT a build-provenance audit trail** (field removed). Do not rely on `workspace-manifest.json` to
answer "what's deployed" — read Firestore (`ci_status`) for live CI status instead, per the workspace's
`ci_status`-is-SSOT rule. Retirement tracked: `infra_satellite_ao_dispatch_batch9_2026_08_09.md` todo 4.

---

## Adding a new service to dual-cloud builds

1. Add `buildspec.aws.yaml` to the service repo (use the template as base).
2. Provision a `<service>-build` Cloud Build trigger in GCP (project `central-element-323112`, region `asia-northeast1`)
   — see "Build trigger naming" above for the real naming families; `<service>-<env>` is the router's own aspiration,
   not the live convention.
3. Provision a CodeBuild project in AWS (account `427895769566`, region `ap-northeast-1`) — naming per "Build trigger
   naming" above.
4. Set `CLOUD_BUILD_PROD_DEPLOY_EXPECTED=true` repo variable in GitHub to activate not-configured alerts.
5. The `image-build-gate.yml` is already rolled out (soft-passes until projects are provisioned).

## Related

- `/codex/08-workflows/ci-cd-flow.md` — overall CI/CD pipeline, LDR-is-SSOT, quickmerge, promotion flow
- `/codex/05-infrastructure/vm-tarball-deployment.md` — VM (non-Cloud Run) deployment
- `unified-trading-pm/.github/workflows/cloud-build-router.yml` — GCP router (canonical ref)
- `unified-trading-pm/.github/workflows/cloud-build-router-aws.yml` — AWS router (canonical ref)
- `unified-trading-ci/.github/workflows/image-build-validate.yml` — reusable promote-gate validator (moved from
  `unified-trading-pm` 2026-08-06)
- `deployment-service/templates/buildspec.aws.yaml` — buildspec template
