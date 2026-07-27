---
doc_type: issue
title: >-
  deployment-api's Cloud Build hits its 600s timeout on the `deploy` step ~5% of the time — the deploy itself still
  succeeds, but the build status misleadingly reads TIMEOUT
summary: >
  While verifying `deployment-api@e8fc64a`'s promote-to-main deploy (build `34593227-e79e-41e8-a1ca-c5bfb5917a4c`,
  2026-07-27T02:04:19Z), the build's overall `status` came back `TIMEOUT` — but `gcloud run revisions describe`
  confirmed the new revision (`uts-shared-deployment-api-00302-xv5`, correct image digest
  `sha256:4effcfbd579f6e9e3cadea02615df55f03391a7eb45a1123c2239a5352d48b2`) was created at `02:14:03Z`, BEFORE the
  build's `finishTime` of `02:15:39Z` — the deploy genuinely succeeded. Per-step inspection (`gcloud builds describe ...
  --format='value(steps[].id,steps[].status)'`) shows all 12 steps (`fetch-ui`...`push`/`scan-check`) SUCCESS; only the
  FINAL `deploy` step itself shows `CANCELLED` — the deploy step evidently completed its actual `gcloud run deploy` call
  (hence the live revision existing) but then got cut off mid-step (a post-deploy wait/poll sub-step, most likely) when
  the build's total `timeout: 600s` budget ran out.

  **Not a one-off**: `gcloud builds list --filter="substitutions.REPO_NAME=deployment-api AND status=TIMEOUT"` shows 8
  TIMEOUT builds total (unbounded query, earliest 2026-07-13: 07-13, 07-14, 07-21×3, 07-23×2, 07-27), spread across 6
  distinct days — a low-rate, non-worsening chronic flake (the most recent 20 builds specifically show 19 SUCCESS / 1
  TIMEOUT, ~5% in that window).

  **Impact today**: none observed — this specific deploy succeeded regardless of the misleading build status. The real
  risk is downstream: any automation gating on Cloud Build's own `status` field (rather than directly checking the live
  Cloud Run revision) could incorrectly treat a genuinely-successful deploy as failed and either alert falsely or retry
  unnecessarily.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service]
scope: [engineer, admin]
tags: [ci-cd, cloud-build, timeout, deployment-api, flake, cloud-run]
related: [/codex/08-workflows/ci-cd-flow.md]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P3
source: >-
  /autonomous fleet CI health sweep, 2026-07-27 -- discovered while verifying deployment-api@e8fc64a's live deploy (a
  fix shipped earlier this session). Root-caused via direct gcloud builds/run inspection, not inferred.
assigned_vm: NA
execution_scope: local-only
assigned_role: devops
drift_direction: advance-code
last_updated: 2026-07-27
locked_by:
resolved_by:
depends_on: []
---

# deployment-api Cloud Build 600s timeout flake (deploy step CANCELLED, deploy itself succeeds)

## Recommended fix (not implemented here — low priority, non-blocking)

- Raise `deployment-api/cloudbuild.yaml`'s build `timeout:` (currently 600s) modestly, OR investigate why the final
  `deploy` step occasionally runs long (likely a `gcloud run deploy` readiness-wait polling loop against a cold or
  slow-starting revision) and tighten that specific wait instead of the whole-build budget.
- Lower-effort alternative: whatever DOES gate/report on this build's status (if anything currently does) should verify
  the live Cloud Run revision directly rather than trusting the Cloud Build `status` field alone — this session's own
  verification recipe (`gcloud run services describe ... latestReadyRevisionName` + compare image digest/creation time
  against the build's start time) is a reasonable model.

## Evidence

- Build: `34593227-e79e-41e8-a1ca-c5bfb5917a4c`, `createTime=2026-07-27T02:04:19Z`, `finishTime=2026-07-27T02:15:39Z`,
  `status=TIMEOUT`, `timeout=600s`.
- Steps:
  `fetch-ui, vendor-deps, auth-precheck, configure-docker, ensure-repo, pull-base-image, build, quality-gates, operability-probe, sha-tag-guard, push, scan-check`
  all `SUCCESS`; `deploy` alone `CANCELLED`.
- Live revision: `uts-shared-deployment-api-00302-xv5`, `creationTimestamp=2026-07-27T02:14:03Z`, image
  `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/deployment-api@sha256:4effcfbd579f6e9e3cadea02615df55f03391a7eb45a1123c2239a5352d48b2`
  — confirms the deploy that the build "failed" on actually landed.
- Historical rate: `gcloud builds list --filter="...AND status=TIMEOUT"` (unbounded, no date range) returns 8 TIMEOUT
  builds total for this repo, earliest 2026-07-13, spread across 6 distinct days (not concentrated/worsening). In the
  most RECENT 20 builds specifically, 19 are `SUCCESS` and 1 is `TIMEOUT` (~5% in that recent window) — the two numbers
  aren't the same sample size, both cited for completeness rather than a single precise rate.
