---
doc_type: issue
title:
  Mutable git-sha image tags — every Cloud Build config re-stamps :$SHORT_SHA on rebuilds of the same commit, silently
  re-pointing sha-tag consumers (observed on deployment-api, tag 7da9baf moved fb364cd9 → f33b346a)
summary:
  "Found 2026-07-13: the deployment-api AR tag 7da9baf moved from digest fb364cd9… to f33b346a… — a git-sha tag is
  supposed to be an immutable pointer, but every cloudbuild config in the fleet tags :$SHORT_SHA unconditionally, pushes
  with `docker push --all-tags`, AND lists the sha tag in `images:` (unconditional post-steps push). Any second build of
  the same commit (trigger retry, double-fire — 2×2df7c55 within 15s on 2026-07-13, 2×c62c8ac / 2×b862a3b / 2×ee90570 in
  the last 3 days; manual deploy-shared.sh `gcloud builds submit` which passes SHORT_SHA=local HEAD) re-stamps the tag.
  Rebuilds are NOT bit-reproducible (deployment-api's fetch-ui/vendor-deps clone deployment-ui + 3 sibling repos +
  unified-trading-pm at live-defi-rollout HEAD at BUILD time; all repos seed layer cache off the moving :latest), so the
  re-stamp genuinely changes content. Cloud Run SERVICES pin per-revision digests and are safe; humans/scripts/plans
  that resolve a sha tag get silent drift. Confirmed re-stamp event: build 2d9e658f-a843-49c3-94eb-c71d7b70bc14
  (deployment-api-main-deploy, 2026-07-13T17:24Z, overall FAILURE at the deploy step but push step SUCCESS) pushed
  f33b346a onto the pre-existing 7da9baf tag. FIXED (first-push-wins sha-tag-guard): PM templates
  cloudbuild-api/service/ui-template.yaml + deployment-api/cloudbuild.yaml. PROPOSED (not yet rolled out): per-repo
  copies of the other 15 docker repos + cloudbuild-infra-template.yaml (ibkr-gateway-infra terraform image)."
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-api]
scope: [engineer, admin]
tags: [cicd, cloud-build, artifact-registry, image-tags, immutability, deployment-drift, template-rollout]
related: []
created: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source:
  [
    deployment-api AR tag observation (7da9baf fb364cd9→f33b346a),
    gcloud builds list/describe + AR tags list evidence 2026-07-13,
  ]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
depends_on: []
---

# Mutable git-sha tag re-stamping in Cloud Build (fleet class) — 2026-07-13

## Observation

`asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/deployment-api:7da9baf` moved from digest
`sha256:fb364cd9…` to `sha256:f33b346a…`. A git-sha tag is expected to be an immutable commit→image pointer; when it
moves, anything that resolves the tag (humans, scripts, plan evidence, `gcloud run deploy --image …:<sha>`) silently
gets different content. Cloud Run SERVICES themselves are safe (revisions pin the digest at deploy time — verified
earlier today that Cloud Run JOBS resolve `:latest` at execution-creation time, a separate precedent).

## Root cause (confirmed)

1. **Every fleet cloudbuild config stamps `:$SHORT_SHA` unconditionally on EVERY build** and pushes it twice: the
   explicit `docker push --all-tags` step AND the `images:` list (which Cloud Build pushes after all steps succeed).
2. **Rebuilds of the same commit happen routinely**: trigger double-fires/retries — build history shows same-SHA double
   builds on 2026-07-13 alone (`2df7c55` at 10:35:02 AND 10:35:17, `b862a3b` 11:47 + 14:35) plus `c62c8ac` ×2 (Jul-10)
   and `ee90570` ×2 (Jul-10); and the manual path `deployment-service/scripts/cloud-run/deploy-shared.sh` runs
   `gcloud builds submit --substitutions=SHORT_SHA=$(git rev-parse --short HEAD)` — same tag, new build.
3. **Rebuilds are NOT reproducible**, so a re-push moves the digest: deployment-api's `fetch-ui` + `vendor-deps` steps
   clone deployment-ui, unified-api-contracts, deployment-service, strategy-service and unified-trading-pm at
   `live-defi-rollout` HEAD **at build time**; every repo additionally seeds `--cache-from :latest` (moving target) and
   floats on the UTL base `:latest` where not digest-pinned.
4. **Confirmed re-stamp event** for the observed tag: build `2d9e658f-a843-49c3-94eb-c71d7b70bc14`
   (`deployment-api-main-deploy`, 2026-07-13T17:24Z, SHORT_SHA=7da9baf) — overall status FAILURE (deploy step), but its
   `push` step SUCCEEDED at ~17:28:52Z, creating digest `f33b346a` and re-pointing the tag. The prior pointer
   `fb364cd9…` is the digest created by the Jul-12 `8cf78c4` build (a full-cache-hit rebuild of 7da9baf reproduced the
   8cf78c4 layers exactly, so AR had attached the 7da9baf tag to that digest — tag-attach event itself not in audit
   logs; AR data-access audit logging is not enabled).

### Why not AR immutable tags

The AR repo `unified-trading-system` is `mode: STANDARD_REPOSITORY` with immutable tags DISABLED. Enabling
`--immutable-tags` is repo-wide and would break the `:latest` flow (every build re-pushes `:latest`; Cloud Run deploy
scripts, `--cache-from :latest` seeding, and Cloud Run Jobs' `:latest` resolution all depend on it). NOT viable — do not
enable.

## Fix shipped (first-push-wins sha-tag-guard)

Minimal mechanism, uniform across templates:

- New `sha-tag-guard` step (gcloud builder, parallel after `configure-docker`): if `:$SHORT_SHA` already exists in AR,
  write its digest to `/workspace/.sha_tag_preexists`.
- `push` step becomes conditional: marker present → push `:latest` only (service template: `:latest` + `:$VERSION`),
  never re-stamping the sha tag; marker absent → `docker push --all-tags` exactly as before (first build of a commit is
  unchanged).
- `images:` list drops the `:$SHORT_SHA` entry (it is pushed unconditionally after all steps and would defeat the
  guard); `:latest` stays listed.
- Semantics: the sha tag now permanently pins the FIRST successful push for that commit; `:latest` remains the mutable
  rolling pointer; deployment-api's gated `deploy` step still deploys `:$SHORT_SHA` (resolves to the preserved first
  digest — deterministic on retries).

### Fixed (committed)

| File                                       | Repo               | Status                                             |
| ------------------------------------------ | ------------------ | -------------------------------------------------- |
| `configs/cloudbuild-api-template.yaml`     | unified-trading-pm | FIXED                                              |
| `configs/cloudbuild-service-template.yaml` | unified-trading-pm | FIXED                                              |
| `configs/cloudbuild-ui-template.yaml`      | unified-trading-pm | FIXED                                              |
| `cloudbuild.yaml`                          | deployment-api     | FIXED — deployment-api@4be663f (surgical: the copy |
|                                            |                    | has intentional drift vs the template —            |
|                                            |                    | vendor-deps/deploy/rollup steps exist ONLY in the  |
|                                            |                    | repo copy; a blind rollout would clobber them,     |
|                                            |                    | repeating the 2026-06-14 fetch-ui incident)        |

Validation: YAML parse OK ×4; `scripts/validation/validate-cloudbuild.py` OK ×4 (SchemaStore schema);
`scripts/quality_gates/check_cloudbuild_substitutions.py` clean ×4; prettier clean.

## Class analysis — affected repos (share the pattern via per-repo copies)

Per-repo `cloudbuild.yaml` copies still carrying the mutable-sha pattern (sha tag in build/push/`images:`):
market-tick-data-service, instruments-service, execution-service, strategy-service, features-service, ml-service,
alerting-service, greeks-service, market-data-processing-service, fund-administration-service, trading-agent-service,
batch-live-reconciliation-service, agent-orchestrator, client-reporting-api, deployment-ui, unified-trading-system-ui,
ibkr-gateway-infra (terraform image; `images:` has no sha but `push --all-tags` re-stamps). Not affected:
deployment-service, e2e-testing, unified-api-contracts (no sha tagging), unified-trading-api (no cloudbuild.yaml).
Exposure is lower than deployment-api (no build-time sibling-repo vendoring) but real: `--cache-from :latest` + UTL base
drift means a same-commit rebuild can still produce a different digest, and same-SHA double-builds are observed in
trigger history.

## Proposed (NOT yet done)

- [ ] [INFRA] P2. Roll the guarded push out to the 16 per-repo `cloudbuild.yaml` copies +
      `configs/cloudbuild-infra-template.yaml` via `scripts/propagation/rollout-cloudbuild.py` — but FIRST diff each
      copy against its rendered template (deployment-api-style drift would be clobbered; the rollout script overwrites
      wholesale). One quickmerge per repo.
- [ ] [INFRA] P3. Consider `scan-check` semantics on a pre-existing sha tag: it scans the preserved (old) image, not the
      just-built one — acceptable (the preserved image is what the tag serves) but worth a deliberate ruling at rollout
      time.
- [ ] [INFRA] P3. deploy-shared.sh manual path: passes `SHORT_SHA=$(git rev-parse --short HEAD)` — now safe (guard keeps
      the first digest); no change needed, noted for awareness.
- [ ] [INFRA] P3. deployment-api's secondary configs `cloudbuild-tier3.yaml` (writes the SAME
      `${_REGISTRY_REPO}/${_SERVICE_NAME}:$SHORT_SHA` image path) and `cloudbuild-dashboard.yaml` still carry the
      unguarded pattern — no live trigger uses them (all 3 deployment-api triggers point at `cloudbuild.yaml`;
      `deployment-api-build` is disabled), manual-submit-only vectors; guard them at next touch.
