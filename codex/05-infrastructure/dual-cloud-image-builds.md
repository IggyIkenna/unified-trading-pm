---
scope: [infra, admin]
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
            ├─ cloud-build-router.yml (GCP)  →  Cloud Build <repo>-<env>  →  Artifact Registry
            └─ cloud-build-router-aws.yml (AWS) →  CodeBuild <repo>-<env>  →  ECR (ap-northeast-1)
```

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
- Routes to trigger `<repo>-<env>` for service repos, `<repo>-wheel-<env>` for library repos.
- Freeze-check via `change-freeze-check.yml` reusable; defers on freeze instead of running.
- On success: updates `deployed_versions[<repo>]` in `workspace-manifest.json`.
- `CLOUD_BUILD_PROD_DEPLOY_EXPECTED` repo variable gates `notify-build-not-configured` alerts (avoids pre-cutover
  noise).

### Registry

- **Artifact Registry host**: `asia-northeast1-docker.pkg.dev`
- **Project**: `central-element-323112`
- **Repository**: `unified-trading`
- **Image URI format**: `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading/<repo>:<version>`
- **Region**: `asia-northeast1`

### Build project naming

- Service repos: `<repo>-<env>` (e.g. `execution-service-staging`, `execution-service-prod`)
- Library repos (wheel builds): `<repo>-wheel-<env>`

---

## AWS side

### Router

`unified-trading-pm/.github/workflows/cloud-build-router-aws.yml` — fires from the same `qg-passed` dispatch event as
the GCP router.

- Auth: OIDC via `aws-actions/configure-aws-credentials@v4`; role ARN from `secrets.AWS_BUILD_ROLE_ARN`.
- Routes to CodeBuild project `<repo>-<env>` (library repos: `<repo>-wheel-<env>`).
- Polls build status via `aws codebuild batch-get-builds` (60×30s = 30 min max).
- `ResourceNotFoundException` → detected as "not configured" → soft notification (same gating as GCP side).
- On success: updates `deployed_versions_aws[<repo>]` in `workspace-manifest.json`.

### Registry

- **ECR host**: `427895769566.dkr.ecr.ap-northeast-1.amazonaws.com`
- **AWS account**: `427895769566`
- **Region**: `ap-northeast-1`
- **Image URI format**: `427895769566.dkr.ecr.ap-northeast-1.amazonaws.com/<repo>:<version>`

**ECR target decision (2026-06-27)**: ECR target matches the AWS account `427895769566` in `buildspec.aws.yaml` files
and the live AWS account constant in workspace configs. No TF divergence identified; this is the live target. Decision:
use as-is, no reconciliation or retirement required.

### Build project naming

Same convention as GCP: `<repo>-<env>` for services, `<repo>-wheel-<env>` for libraries.

### Build trigger model

**Router-driven (primary)**: the GHA router triggers CodeBuild via `aws codebuild start-build`. This is the canonical
path. CodeBuild webhook triggers (PUSH events from GitHub) are a secondary/legacy model.

**Webhook model decision (2026-06-27)**: the GHA router is the canonical build-trigger path, consistent with GCP's
router pattern. CodeBuild PUSH webhooks, if configured on any project, fire in addition to the router call — this is
redundant but not harmful (idempotent image builds). The canonical source of truth for build provenance is the router
(it records `deployed_versions_aws` in the workspace manifest). Do not add new PUSH webhooks; migrate existing
webhook-only projects to router-driven if/when they need provenance tracking.

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
- Image push target: `427895769566.dkr.ecr.ap-northeast-1.amazonaws.com/<repo>:<version>`.

---

## Staging→main promote gate

### Per-service template

`unified-trading-pm/scripts/workflow-templates/image-build-gate.yml` — rolled out to every repo via the template
mechanism. Creates `.github/workflows/image-build-gate.yml` in each service repo.

Trigger: `pull_request: branches: [main]` — fires on every staging→main promote PR.

Calls: `IggyIkenna/unified-trading-pm/.github/workflows/image-build-validate.yml@live-defi-rollout`.

### Reusable validate workflow

`unified-trading-pm/.github/workflows/image-build-validate.yml`

Runs GCP Cloud Build and AWS CodeBuild **in parallel** for the PR head commit, then gates:

- Both clouds must exit 0.
- If either cloud's build project is `not-configured` (trigger/project not found) → **soft-pass** (exit 0). This
  prevents the gate from blocking promote PRs for repos that have not yet had their Cloud Build / CodeBuild projects
  provisioned (pre-cutover safe).
- Outputs: `gcp_build_id`, `gcp_build_exit_code`, `aws_build_id`, `aws_build_exit_code`, `both_passed`.
- GCP auth: WIF preferred, SA key fallback.
- AWS auth: OIDC.

---

## GCP `live-defi-rollout` branch trigger

**Decision (2026-06-27)**: GCP opt-in for `live-defi-rollout` branch builds is an operator decision (cost vs. coverage).
Currently, GCP Cloud Build triggers fire on `staging` and `prod` branches. Adding a `live-defi-rollout` trigger would
provide earlier build feedback before promotion but increases build cost. **Status: no change to current setup** —
operator should explicitly request this if coverage justifies cost. Implementation would require adding
`live-defi-rollout` as a trigger branch to each `<repo>-ldr` Cloud Build trigger.

---

## Cross-cloud parity test

`deployment-service/scripts/quality_gates/check_dual_cloud_parity.py` — checks that for every service registered in
`workspace-manifest.json`, both `buildspec.aws.yaml` (AWS) and `cloudbuild.yaml` (GCP) exist in the repo, confirming
dual-cloud build coverage.

Run via deployment-service `quality-gates.sh`. A missing buildspec for a registered service fails the gate.

---

## Provenance

- GCP success: `deployed_versions[<repo>]` key in `workspace-manifest.json` (updated by `cloud-build-router.yml`).
- AWS success: `deployed_versions_aws[<repo>]` key in `workspace-manifest.json` (updated by
  `cloud-build-router-aws.yml`).

Manifest state is the build-provenance audit trail; read Firestore (`ci_status`) for live CI status.

---

## Adding a new service to dual-cloud builds

1. Add `buildspec.aws.yaml` to the service repo (use the template as base).
2. Provision `<service>-<env>` Cloud Build triggers in GCP (project `central-element-323112`, region `asia-northeast1`).
3. Provision `<service>-<env>` CodeBuild projects in AWS (account `427895769566`, region `ap-northeast-1`).
4. Set `CLOUD_BUILD_PROD_DEPLOY_EXPECTED=true` repo variable in GitHub to activate not-configured alerts.
5. The `image-build-gate.yml` is already rolled out (soft-passes until projects are provisioned).

## Related

- `codex/08-workflows/ci-cd-flow.md` — overall CI/CD pipeline, LDR-is-SSOT, quickmerge, promotion flow
- `codex/05-infrastructure/vm-tarball-deployment.md` — VM (non-Cloud Run) deployment
- `unified-trading-pm/.github/workflows/cloud-build-router.yml` — GCP router (canonical ref)
- `unified-trading-pm/.github/workflows/cloud-build-router-aws.yml` — AWS router (canonical ref)
- `deployment-service/templates/buildspec.aws.yaml` — buildspec template
