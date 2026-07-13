---
doc_type: issue
title:
  "agent-orchestrator Artifact Registry image
  (asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/agent-orchestrator:latest) is NOT a
  deploy surface — nothing consumes it; staleness (37 commits behind main) is harmless; do not rebuild"
summary:
  "Deployment-sync leg, 2026-07-13. The AO image in the asia-northeast1 `unified-trading-system` AR repo (:latest =
  :0.0.0.dev0 = :4539201d, digest sha256:6236b0d8…, built 2026-06-28) was flagged as 37 commits / 136 files behind
  main@e04875c9 with no Cloud Build trigger. Determination: it is a NON-SURFACE. The live AO runtime is the EC2 central
  VM systemd `orchestrator.service` (tmux + uvicorn :8765) with git self-pull deploy (runtime-deployment-topology.md §
  agent-orchestrator self-pull, added 2026-07-12) — it never pulls a container. The only orchestrator Cloud Run service
  (`agent-orchestrator-staging`, europe-west4, HISTORICAL per agent-orchestrator-deploy.md) runs a DIFFERENT image
  (europe-west4 cloud-run-source-deploy/agent-orchestrator:uat). No Cloud Run job, no VM launcher, and zero workspace
  code references consume the asia-northeast1 path. The image exists only as the output of a one-off MANUAL Cloud Build
  (e11ef7c7-ab7c-4559-8289-9658f8fa8dd7, 2026-06-28T05:31:16Z, empty buildTriggerId) of
  agent-orchestrator/cloudbuild.yaml, whose ongoing purpose is PR-time buildability validation via image-build-gate.yml
  → PM image-build-validate.yml (which soft-passes for AO because the `agent-orchestrator-staging` Cloud Build trigger
  is not configured — verified absent in both global and asia-northeast1). No rebuild performed; no runtime touched."
status: resolved
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, deployment-service]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    artifact-registry,
    deploy-surface,
    cloud-build,
    dual-cloud-image-builds,
    deployment-sync,
    non-surface,
  ]
related:
  [
    ../../../codex/04-architecture/runtime-deployment-topology.md,
    ../../../codex/05-infrastructure/agent-orchestrator-deploy.md,
    ../../../codex/05-infrastructure/dual-cloud-image-builds.md,
    ../../../codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-13
parent_epic: orchestrator_master
priority: P3
source:
  "Operator deployment-sync sweep 2026-07-13 ('fix the rest'): AO image 37 commits / 136 files behind main@e04875c9, no
  Cloud Build trigger, tag 0.0.0.dev0; pin+crypto bump shipped to AO LDR @6cb82b9. Leg instruction: determine whether
  the image is a real deploy surface before rebuilding anything."
assigned_vm: NA
resolved_by:
  "determination 2026-07-13 (this doc) — image verified non-surface via live GCP reads + workspace grep; no code change
  and no rebuild required"
locked_by:
---

# agent-orchestrator AR image is a non-surface — determination + evidence

## Question

Is `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/agent-orchestrator:latest` a real
deploy surface that must be kept current with `main` (it is 37 commits / 136 files behind `main@e04875c9`, tag
`0.0.0.dev0`, no Cloud Build trigger)?

## Determination: NO — nothing consumes this image. Do not rebuild it to "fix" staleness.

The live agent-orchestrator runtime is **not container-based**. Rebuilding the image from `main` would change nothing in
production; its staleness is harmless.

## Evidence (all verified 2026-07-13)

1. **Live runtime is git-self-pull systemd on EC2, not a container.**
   `codex/04-architecture/runtime-deployment-topology.md` § "agent-orchestrator — self-pull deploy (added 2026-07-12)":
   central + epic VMs are long-lived systemd services (`orchestrator.service`, tmux + uvicorn :8765 on EC2
   `13.113.200.22`), "not container-redeployed on push"; currency comes from git self-pull (shipped
   `agent-orchestrator@589b711`, hardened `@d16d737` + `@5462959`). Deploy reference:
   `codex/05-infrastructure/agent-orchestrator-deploy.md` (systemd install script; Cloud Run shape explicitly marked
   "HISTORICAL — superseded 2026-05-20 by EC2 … Not running today").
2. **The one existing orchestrator Cloud Run service runs a DIFFERENT image.** `gcloud run services list` (project
   `central-element-323112`) shows only `agent-orchestrator-staging` (europe-west4, created 2026-05-19, latestReady
   `agent-orchestrator-staging-00014-hdn`), whose container image is
   `europe-west4-docker.pkg.dev/central-element-323112/cloud-run-source-deploy/agent-orchestrator:uat` — the historical
   registry, NOT the asia-northeast1 image. No prod service; `gcloud run jobs list` has no orchestrator match.
3. **Zero workspace consumers of the AR path.** `rg "unified-trading-system/agent-orchestrator"` across all repos
   (excluding .venv/build/node_modules) returns 0 hits. The deployment-api `builds_history.py` route lists AR builds for
   observability only. The packer AMI (`deployment-service/packer/agent-orchestrator/`) warm-caches via **git clone +
   venv build**, no docker pull. No VM launcher references the image.
4. **The image is the output of a one-off MANUAL build, not a pipeline.** Build `e11ef7c7-ab7c-4559-8289-9658f8fa8dd7`
   (asia-northeast1, SUCCESS, 2026-06-28T05:31:16Z) produced `:4539201d` + `:latest` (digest
   `sha256:6236b0d8dd204fe5d6907b263125841f3f3a6e1cee15a2dc39c25eb11fd382ca`, also tagged `0.0.0.dev0` — the
   cloudbuild.yaml PEP440 fallback when no v-tag is reachable) with an **empty buildTriggerId** (manual
   `gcloud builds submit`). `gcloud builds triggers list` in both `global` and `asia-northeast1` has NO
   agent-orchestrator trigger.
5. **The cloudbuild.yaml's ongoing role is PR-gate buildability validation, not deployment.**
   `agent-orchestrator/.github/workflows/image-build-gate.yml` (PRs → main) calls PM `image-build-validate.yml`, which
   runs Cloud Build trigger `agent-orchestrator-staging` — not configured, so the GCP side **soft-passes**
   ("pre-cutover" branch of the workflow). SSOT: `codex/05-infrastructure/dual-cloud-image-builds.md`.

## Resolution

Documentation-only (per the leg's instruction: if nothing consumes it, do NOT build anything). No rebuild, no LDR→main
promote forced, no runtime or Cloud Run service touched. The pin+crypto bump already shipped to AO LDR (`@6cb82b9`)
flows to `main` via the standing fleet promote; the image needs no action.

## Follow-up candidates (operator decision, non-blocking — none executed)

- [ ] P3. Delete the stale `unified-trading-system/agent-orchestrator` AR package (3 tags, 1 digest) — pure cost/
      hygiene; nothing breaks if kept.
- [ ] P3. Decide whether AO should get a real `agent-orchestrator-staging` Cloud Build trigger so the dual-cloud
      image-build gate stops soft-passing on the GCP side (only worth it if the operator wants image-buildability
      enforced for AO PRs; the AWS/ECR side has `buildspec.aws.yaml`).
- [ ] P3. Tear down the HISTORICAL europe-west4 Cloud Run service `agent-orchestrator-staging` (min-instances 0, runs
      the superseded `cloud-run-source-deploy:uat` image) + its registry — codex already marks it "not running today";
      keep only if the cloud-agnostic re-spin optionality is still wanted.
