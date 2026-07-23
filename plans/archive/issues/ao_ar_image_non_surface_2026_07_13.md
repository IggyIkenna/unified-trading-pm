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
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    /codex/05-infrastructure/dual-cloud-image-builds.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
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
  and no rebuild required. Addendum 2026-07-13: per explicit operator ruling, the stale asia-northeast1 AR package was
  deleted and the zero-traffic europe-west4 agent-orchestrator-staging Cloud Run service torn down (both verified
  NOT_FOUND — see teardown checklist)."
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
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
   `/codex/04-architecture/runtime-deployment-topology.md` § "agent-orchestrator — self-pull deploy (added 2026-07-12)":
   central + epic VMs are long-lived systemd services (`orchestrator.service`, tmux + uvicorn :8765 on EC2
   `13.113.200.22`), "not container-redeployed on push"; currency comes from git self-pull (shipped
   `agent-orchestrator@589b711`, hardened `@d16d737` + `@5462959`). Deploy reference:
   `/codex/05-infrastructure/agent-orchestrator-deploy.md` (systemd install script; Cloud Run shape explicitly marked
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
   ("pre-cutover" branch of the workflow). SSOT: `/codex/05-infrastructure/dual-cloud-image-builds.md`.

## Resolution

Documentation-only (per the leg's instruction: if nothing consumes it, do NOT build anything). No rebuild, no LDR→main
promote forced, no runtime or Cloud Run service touched. The pin+crypto bump already shipped to AO LDR (`@6cb82b9`)
flows to `main` via the standing fleet promote; the image needs no action.

## Follow-up candidates (operator decision, non-blocking — none executed)

- [x] P3. ✅ Delete the stale `unified-trading-system/agent-orchestrator` AR package (3 tags, 1 digest) — pure cost/
      hygiene; nothing breaks if kept. **EXECUTED 2026-07-13 per operator ruling — see teardown checklist below
      (Evidence: cloudbuild=d571bed5-a3d8-4828-86ed-954ff2f3308e SUCCESS, verify NOT_FOUND).**
- [x] P3. ✅ **DECIDED 2026-07-16 — WON'T DO (operator ruling).** _"We don't need a cloud run image for this right now,
      we have deployed this service and it is running since 2 months without it, so no need for image building for this
      one for now."_ Consistent with the determination above: AO is **not container-deployed** (EC2 systemd
      `orchestrator.service` + git self-pull, live ~2 months with no image), so an `agent-orchestrator-staging` Cloud
      Build trigger would only buy GCP-side image-buildability enforcement on AO PRs for an artifact **nothing
      consumes**. The dual-cloud image-build gate continues to **soft-pass on the GCP side by design** (not a defect —
      see `/codex/05-infrastructure/dual-cloud-image-builds.md`); the AWS/ECR side retains `buildspec.aws.yaml`. Revisit
      ONLY if AO ever becomes container-deployed.
- [x] P3. ✅ Tear down the HISTORICAL europe-west4 Cloud Run service `agent-orchestrator-staging` (min-instances 0, runs
      the superseded `cloud-run-source-deploy:uat` image) — codex already marks it "not running today". **SERVICE
      DELETED 2026-07-13 per operator ruling after a verified zero-traffic-in-30d gate — see teardown checklist below.
      The europe-west4 registry/image itself was NOT in the ruling and remains.**

## Operator ruling 2026-07-13 (explicit, interactive Q&A): execute items 1 + 3 — pre-delete state capture

Ruling: delete the stale asia-northeast1 AR package `unified-trading-system/agent-orchestrator` AND tear down the
europe-west4 Cloud Run service `agent-orchestrator-staging` — the latter conditional on verified zero traffic over the
last 30 days. Do NOT touch the central-VM AO runtime (tmux/systemd) or any europe-west4 'production'-tagged
image/service. Item 2 (Cloud Build trigger decision) remains open — not part of this ruling.

### Traffic verification for `agent-orchestrator-staging` (gate PASSED — zero traffic)

- Cloud Logging `run.googleapis.com/requests` for
  `resource.labels.service_name="agent-orchestrator-staging" AND resource.labels.location="europe-west4"`,
  `--freshness=30d`: **0 entries**.
- Cloud Monitoring `run.googleapis.com/request_count` (unaffected by logging-sink exclusions), 30-day window aligned
  `ALIGN_SUM`: **empty timeSeries — no data points**, i.e. genuinely zero requests.
- Service status corroborates: latestReadyRevision `agent-orchestrator-staging-00014-hdn`, last transition
  2026-05-22T03:50Z (untouched for ~7 weeks).

### 1. AR package `unified-trading-system/agent-orchestrator` (asia-northeast1) — pre-delete state

```text
IMAGE:  asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/agent-orchestrator
DIGEST: sha256:6236b0d8dd204fe5d6907b263125841f3f3a6e1cee15a2dc39c25eb11fd382ca   (single digest)
TAGS:   0.0.0.dev0, 4539201d, latest
CREATED: 2026-06-28T05:34:30 (package createTime 2026-06-28T05:34:30.866415Z)
Provenance: manual Cloud Build e11ef7c7-ab7c-4559-8289-9658f8fa8dd7 (2026-06-28T05:31:16Z, empty buildTriggerId)
            of agent-orchestrator/cloudbuild.yaml @ 4539201d — re-creatable via `gcloud builds submit` from the repo.
```

### 2. Cloud Run service `agent-orchestrator-staging` (europe-west4) — pre-delete spec

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/urls: '["https://agent-orchestrator-staging-1060025368044.europe-west4.run.app","https://agent-orchestrator-staging-cldtjniqvq-ez.a.run.app"]'
    serving.knative.dev/creator: ikenna@odum-research.com
  creationTimestamp: "2026-05-19T11:27:18.862776Z"
  generation: 14
  labels: { cloud.googleapis.com/location: europe-west4 }
  name: agent-orchestrator-staging
  namespace: "1060025368044"
  uid: d11385ae-95e6-4d89-8c51-6575df5b471a
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "3"
        run.googleapis.com/startup-cpu-boost: "true"
    spec:
      containerConcurrency: 80
      containers:
        - command: [sh]
          args: ["-c", "uvicorn server.server:app --host 0.0.0.0 --port 8080"]
          env:
            - name: ORCHESTRATOR_JWT_SECRET
              valueFrom: { secretKeyRef: { key: latest, name: ORCHESTRATOR_JWT_SECRET } }
            - name: AGENT_ORCHESTRATOR_SLACK_WEBHOOK
              valueFrom: { secretKeyRef: { key: latest, name: AGENT_ORCHESTRATOR_SLACK_WEBHOOK } }
            - name: AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET
              valueFrom: { secretKeyRef: { key: latest, name: AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET } }
            - { name: ORCHESTRATOR_MODE, value: live }
            - { name: ORCHESTRATOR_ALLOW_ANONYMOUS, value: "false" }
            - { name: ORCHESTRATOR_USERS_JSON, value: /secrets/users.json }
          image: europe-west4-docker.pkg.dev/central-element-323112/cloud-run-source-deploy/agent-orchestrator:uat
          ports: [{ containerPort: 8080, name: http1 }]
          resources: { limits: { cpu: "1", memory: 1Gi } }
          startupProbe: { failureThreshold: 1, periodSeconds: 240, tcpSocket: { port: 8080 }, timeoutSeconds: 240 }
          volumeMounts: [{ mountPath: /secrets, name: ORCHESTRATOR_USERS_JSON-tuk-fih }]
      serviceAccountName: 1060025368044-compute@developer.gserviceaccount.com
      timeoutSeconds: 300
      volumes:
        - name: ORCHESTRATOR_USERS_JSON-tuk-fih
          secret: { items: [{ key: latest, path: users.json }], secretName: ORCHESTRATOR_USERS_JSON }
  traffic: [{ latestRevision: true, percent: 100 }]
# status at capture: Ready=True since 2026-05-22T03:50:19Z; latestReadyRevision agent-orchestrator-staging-00014-hdn;
# url https://agent-orchestrator-staging-cldtjniqvq-ez.a.run.app
# NOTE: the referenced image europe-west4 cloud-run-source-deploy/agent-orchestrator:uat is NOT deleted by this ruling.
```

### Teardown checklist (execute after this capture is committed)

- [x] P1. ✅ Delete AR package `unified-trading-system/agent-orchestrator` (asia-northeast1) + verify NOT_FOUND — direct
      delete PERMISSION_DENIED for `unified-trading-sa`, executed via Cloud Build executor (Evidence:
      cloudbuild=d571bed5-a3d8-4828-86ed-954ff2f3308e SUCCESS): "Deleted package [agent-orchestrator]", in-build
      `artifacts packages describe` → NOT_FOUND
- [x] P1. ✅ Delete Cloud Run service `agent-orchestrator-staging` (europe-west4) + verify NOT_FOUND — zero-traffic gate
      PASSED (0 request-log entries in 30d + empty `run.googleapis.com/request_count` timeSeries); deleted
      2026-07-13T23:33Z; `gcloud run services describe` → "Cannot find service [agent-orchestrator-staging]". The
      europe-west4 `cloud-run-source-deploy/agent-orchestrator:uat` image and the central-VM AO runtime were NOT
      touched.

Teardown COMPLETE 2026-07-13. **ALL ITEMS NOW CLOSED** — the last open item (the P3 `agent-orchestrator-staging` Cloud
Build trigger decision) was ruled **WON'T DO** by the operator on 2026-07-16 (see Follow-up candidates item 2). This doc
has **no remaining open surface**.

## Reconciliation 2026-07-16

Re-verified independently (operator-requested one-by-one issue reconciliation — not agent-relayed). All five
load-bearing claims re-checked against live GCP + the workspace on 2026-07-16 and every one holds:

| Claim                              | Check                                            | Result                                 |
| ---------------------------------- | ------------------------------------------------ | -------------------------------------- |
| AR package deleted                 | `gcloud artifacts packages describe`             | NOT_FOUND ✅                           |
| europe-west4 Cloud Run torn down   | `gcloud run services describe`                   | "Cannot find service" ✅               |
| No orchestrator Cloud Run anywhere | `gcloud run services list`                       | none ✅                                |
| Deletion build SUCCESS             | `gcloud builds describe d571bed5…`               | SUCCESS, 2026-07-13T23:26:55Z ✅       |
| Zero workspace consumers           | `rg 'unified-trading-system/agent-orchestrator'` | 0 code hits (only this doc matches) ✅ |

Archival CONFIRMED correct. The one previously-dangling P3 todo is now decided (WON'T DO), so nothing from this doc is
carried anywhere else.
